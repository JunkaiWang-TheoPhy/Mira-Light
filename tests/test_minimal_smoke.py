import json
import threading
import unittest
import urllib.error
import urllib.request
from pathlib import Path
from tempfile import TemporaryDirectory

import sys


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = ROOT / "scripts"
BRIDGE_DIR = ROOT / "tools" / "mira_light_bridge"

if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))
if str(BRIDGE_DIR) not in sys.path:
    sys.path.insert(0, str(BRIDGE_DIR))

from bridge_server import BridgeHTTPServer, BridgeHandler
from mira_light_runtime import MiraLightRuntime


def request_json(url: str, *, method: str = "GET", payload: dict | None = None) -> tuple[int, dict]:
    data = None if payload is None else json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json"},
        method=method,
    )
    try:
        with urllib.request.urlopen(req, timeout=3) as response:
            return response.status, json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        try:
            return exc.code, json.loads(exc.read().decode("utf-8"))
        finally:
            exc.close()


class MinimalSmokeTest(unittest.TestCase):
    def test_runtime_lists_ready_scenes_only_by_default(self) -> None:
        runtime = MiraLightRuntime(base_url="http://127.0.0.1:9", dry_run=True)
        scenes = runtime.list_scenes()
        self.assertTrue(scenes)
        self.assertEqual({item["id"] for item in scenes}, {"cute_probe", "daydream", "farewell"})
        self.assertTrue(all(item["readiness"] == "ready" for item in scenes))

    def test_bridge_supports_minimal_mode(self) -> None:
        runtime = MiraLightRuntime(base_url="http://127.0.0.1:9", dry_run=True)
        with TemporaryDirectory() as tmpdir:
            server = BridgeHTTPServer(
                ("127.0.0.1", 0),
                BridgeHandler,
                runtime=runtime,
                token="",
                ingest_root=Path(tmpdir),
            )
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            base_url = f"http://127.0.0.1:{server.server_address[1]}"
            try:
                status, health = request_json(f"{base_url}/health")
                self.assertEqual(status, 200)
                self.assertTrue(health["ok"])

                status, scenes = request_json(f"{base_url}/v1/mira-light/scenes")
                self.assertEqual(status, 200)
                self.assertEqual({item["id"] for item in scenes["items"]}, {"cute_probe", "daydream", "farewell"})

                status, blocked = request_json(
                    f"{base_url}/v1/mira-light/run-scene",
                    method="POST",
                    payload={"scene": "celebrate", "async": False},
                )
                self.assertEqual(status, 400)
                self.assertIn("minimal mode", blocked["error"])

                status, ran = request_json(
                    f"{base_url}/v1/mira-light/run-scene",
                    method="POST",
                    payload={"scene": "farewell", "async": False},
                )
                self.assertEqual(status, 200)
                self.assertTrue(ran["ok"])

                status, logs = request_json(f"{base_url}/v1/mira-light/logs")
                self.assertEqual(status, 200)
                self.assertTrue(logs["items"])
            finally:
                server.shutdown()
                server.server_close()
                thread.join(timeout=3)


if __name__ == "__main__":
    unittest.main()
