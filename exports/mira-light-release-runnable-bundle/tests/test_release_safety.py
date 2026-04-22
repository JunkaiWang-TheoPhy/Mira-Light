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
from mira_light_safety import SafetyViolation


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


class ReleaseSafetyTest(unittest.TestCase):
    def test_safe_pose_passes_without_clamp(self) -> None:
        runtime = MiraLightRuntime(base_url="http://127.0.0.1:9", dry_run=True)
        applied = runtime.apply_pose_with_safety("neutral", source="test.pose")

        self.assertEqual(applied["safety"]["status"], "passed")
        self.assertEqual(applied["data"]["payload"]["servo1"], 90)
        self.assertEqual(runtime.get_runtime_state()["estimatedServoState"]["servo1"], 90)

    def test_absolute_control_is_clamped_to_rehearsal_range(self) -> None:
        runtime = MiraLightRuntime(base_url="http://127.0.0.1:9", dry_run=True)
        controlled = runtime.control_lamp({"mode": "absolute", "servo1": 140}, source="test.absolute")

        self.assertEqual(controlled["safety"]["status"], "clamped")
        self.assertEqual(controlled["data"]["payload"]["servo1"], 110)
        self.assertTrue(any("[safety-clamp]" in entry["text"] for entry in runtime.get_logs()))

    def test_dangerous_relative_nudge_is_rejected(self) -> None:
        runtime = MiraLightRuntime(base_url="http://127.0.0.1:9", dry_run=True)
        runtime.apply_pose("neutral")

        with self.assertRaises(SafetyViolation):
            runtime.control_lamp({"mode": "relative", "servo4": 100}, source="test.relative.reject")

        self.assertTrue(any("[safety-reject]" in entry["text"] for entry in runtime.get_logs()))

    def test_bridge_control_reports_clamp_and_reject(self) -> None:
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
                status, clamped = request_json(
                    f"{base_url}/v1/mira-light/control",
                    method="POST",
                    payload={"mode": "absolute", "servo1": 140},
                )
                self.assertEqual(status, 200)
                self.assertEqual(clamped["safety"]["status"], "clamped")
                self.assertEqual(clamped["data"]["payload"]["servo1"], 110)

                status, applied_pose = request_json(
                    f"{base_url}/v1/mira-light/apply-pose",
                    method="POST",
                    payload={"pose": "neutral"},
                )
                self.assertEqual(status, 200)
                self.assertEqual(applied_pose["safety"]["status"], "passed")

                status, rejected = request_json(
                    f"{base_url}/v1/mira-light/control",
                    method="POST",
                    payload={"mode": "relative", "servo4": 100},
                )
                self.assertEqual(status, 400)
                self.assertEqual(rejected["safety"]["status"], "rejected")
            finally:
                server.shutdown()
                server.server_close()
                thread.join(timeout=3)


if __name__ == "__main__":
    unittest.main()
