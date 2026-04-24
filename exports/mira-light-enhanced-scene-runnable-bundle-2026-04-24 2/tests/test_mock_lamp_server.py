from __future__ import annotations

import json
import threading
import unittest
import urllib.error
import urllib.request
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = ROOT / "scripts"

if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from mock_lamp_server import MockLampController, MockLampHandler, MockLampHTTPServer


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


class MockLampServerTest(unittest.TestCase):
    def setUp(self) -> None:
        self.server = MockLampHTTPServer(
            ("127.0.0.1", 0),
            MockLampHandler,
            controller=MockLampController(led_count=40),
        )
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.base_url = f"http://127.0.0.1:{self.server.server_address[1]}"

    def tearDown(self) -> None:
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=3)

    def test_mock_server_exposes_stateful_device_surface(self) -> None:
        status, health = request_json(f"{self.base_url}/health")
        self.assertEqual(status, 200)
        self.assertTrue(health["ok"])
        self.assertEqual(health["snapshot"]["led"]["led_count"], 40)
        self.assertEqual(len(health["snapshot"]["led"]["pixelSignals"]), 40)
        self.assertNotIn("ledCount", health["snapshot"]["led"])
        self.assertEqual(health["snapshot"]["status"]["sensors"]["headCapacitive"], 0)

        status, controlled = request_json(
            f"{self.base_url}/control",
            method="POST",
            payload={"mode": "absolute", "servo1": 120, "servo4": 70},
        )
        self.assertEqual(status, 200)
        servo_angles = {item["name"]: item["angle"] for item in controlled["servos"]}
        self.assertEqual(servo_angles["servo1"], 120)
        self.assertEqual(servo_angles["servo4"], 70)

        pixels = [{"r": 8, "g": 16, "b": 24} for _ in range(40)]
        status, led = request_json(
            f"{self.base_url}/led",
            method="POST",
            payload={"mode": "vector", "brightness": 180, "pixels": pixels},
        )
        self.assertEqual(status, 200)
        self.assertEqual(led["mode"], "vector")
        self.assertEqual(led["brightness"], 180)
        self.assertEqual(led["led_count"], 40)
        self.assertNotIn("ledCount", led)
        self.assertEqual(len(led["pixels"]), 40)
        self.assertEqual(len(led["pixelSignals"]), 40)
        self.assertEqual(led["pixelSignals"][0], [8, 16, 24, 180])

        status, sensors = request_json(
            f"{self.base_url}/sensors",
            method="POST",
            payload={"headCapacitive": 1},
        )
        self.assertEqual(status, 200)
        self.assertEqual(sensors["headCapacitive"], 1)

        status, current_sensors = request_json(f"{self.base_url}/sensors")
        self.assertEqual(status, 200)
        self.assertEqual(current_sensors["headCapacitive"], 1)

        status, action = request_json(
            f"{self.base_url}/action",
            method="POST",
            payload={"name": "wave", "loops": 2},
        )
        self.assertEqual(status, 200)
        self.assertTrue(action["playing"])
        self.assertEqual(action["currentAction"]["name"], "wave")

        status, stopped = request_json(f"{self.base_url}/action/stop", method="POST", payload={})
        self.assertEqual(status, 200)
        self.assertTrue(stopped["stopped"])
        self.assertFalse(stopped["playing"])

    def test_mock_server_accepts_rgba_vector_payloads(self) -> None:
        status, led = request_json(
            f"{self.base_url}/led",
            method="POST",
            payload={"mode": "vector", "pixelSignals": [[12, 24, 36, 90] for _ in range(40)]},
        )
        self.assertEqual(status, 200)
        self.assertEqual(led["pixelSignals"][0], [12, 24, 36, 90])
        self.assertEqual(led["pixels"][0], {"r": 12, "g": 24, "b": 36})

    def test_mock_server_rejects_bad_vector_payloads(self) -> None:
        status, blocked = request_json(
            f"{self.base_url}/led",
            method="POST",
            payload={"mode": "vector", "pixels": [[255, 0, 0]] * 10},
        )
        self.assertEqual(status, 400)
        self.assertIn("exactly 40", blocked["error"])

        status, blocked = request_json(
            f"{self.base_url}/led",
            method="POST",
            payload={"mode": "vector", "pixelSignals": [[255, 0, 0, 128]] * 39 + [[300, 0, 0, 128]]},
        )
        self.assertEqual(status, 400)
        self.assertIn("between 0 and 255", blocked["error"])

        status, blocked = request_json(
            f"{self.base_url}/sensors",
            method="POST",
            payload={"headCapacitive": 2},
        )
        self.assertEqual(status, 400)
        self.assertIn("must be 0 or 1", blocked["error"])


if __name__ == "__main__":
    unittest.main()
