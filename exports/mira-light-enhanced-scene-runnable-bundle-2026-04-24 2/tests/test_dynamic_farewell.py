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


def first_absolute_servo1(scene: dict) -> int:
    for step in scene["steps"]:
        payload = step.get("payload", {})
        if step.get("type") == "control" and payload.get("mode") == "absolute":
            return payload["servo1"]
    raise AssertionError("No absolute control step found")


class DynamicFarewellTest(unittest.TestCase):
    def test_preview_scene_resolves_departure_direction(self) -> None:
        runtime = MiraLightRuntime(base_url="http://127.0.0.1:9", dry_run=True)

        left_scene = runtime.preview_scene("farewell", {"departureDirection": "left"})
        center_scene = runtime.preview_scene("farewell", {"departureDirection": "center"})
        default_scene = runtime.preview_scene("farewell", {"departureDirection": "unknown"})

        self.assertEqual(first_absolute_servo1(left_scene), 78)
        self.assertEqual(first_absolute_servo1(center_scene), 92)
        self.assertEqual(first_absolute_servo1(default_scene), 106)
        self.assertIn("左侧", left_scene["notes"][0])
        self.assertIn("正前方", center_scene["notes"][0])
        self.assertIn("右侧", default_scene["notes"][0])

    def test_run_scene_blocking_records_scene_context_and_dynamic_logs(self) -> None:
        runtime = MiraLightRuntime(base_url="http://127.0.0.1:9", dry_run=True)
        state = runtime.run_scene_blocking("farewell", scene_context={"departureDirection": "left"})

        self.assertEqual(state["lastSceneContext"]["departureDirection"], "left")
        log_lines = [item["text"] for item in runtime.get_logs()]
        self.assertTrue(any("先目送评委离开的左侧" in line for line in log_lines))
        self.assertTrue(any('"servo1": 78' in line for line in log_lines))

    def test_bridge_run_scene_accepts_context_alias(self) -> None:
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
                status, ran = request_json(
                    f"{base_url}/v1/mira-light/run-scene",
                    method="POST",
                    payload={
                        "scene": "farewell",
                        "async": False,
                        "context": {"departureDirection": "left"},
                    },
                )
                self.assertEqual(status, 200)
                self.assertTrue(ran["ok"])
                self.assertEqual(ran["runtime"]["lastSceneContext"]["departureDirection"], "left")
            finally:
                server.shutdown()
                server.server_close()
                thread.join(timeout=3)


if __name__ == "__main__":
    unittest.main()
