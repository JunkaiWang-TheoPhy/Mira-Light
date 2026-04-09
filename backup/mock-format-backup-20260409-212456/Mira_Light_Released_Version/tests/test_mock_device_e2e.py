from __future__ import annotations

import json
import threading
import time
import unittest
import urllib.error
import urllib.request
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import mock

import sys


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = ROOT / "scripts"
BRIDGE_DIR = ROOT / "tools" / "mira_light_bridge"

if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))
if str(BRIDGE_DIR) not in sys.path:
    sys.path.insert(0, str(BRIDGE_DIR))

from bridge_server import BridgeHTTPServer, BridgeHandler
from mira_light_runtime import BoothController, MiraLightRuntime
from mock_mira_light_device import create_server


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


class MockDeviceE2ETest(unittest.TestCase):
    def _start_server(self, server):
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        return thread

    def _wait_until_not_running(self, bridge_base_url: str, *, attempts: int = 20) -> None:
        for _ in range(attempts):
            status, runtime_state = request_json(f"{bridge_base_url}/v1/mira-light/runtime")
            self.assertEqual(status, 200)
            if not runtime_state["runtime"]["running"]:
                return
            time.sleep(0.02)
        self.fail("runtime did not settle before the next trigger")

    def test_bridge_scene_and_manual_controls_hit_mock_device(self) -> None:
        with TemporaryDirectory() as tmpdir:
            tmp_root = Path(tmpdir)
            mock_server = create_server(
                "127.0.0.1",
                0,
                request_log_path=tmp_root / "mock.requests.jsonl",
                state_dump_path=tmp_root / "mock.state.json",
            )
            mock_thread = self._start_server(mock_server)
            mock_base_url = f"http://127.0.0.1:{mock_server.server_address[1]}"

            runtime = MiraLightRuntime(base_url=mock_base_url, dry_run=False, timeout_seconds=1.0)
            runtime.audio_player.dry_run = True
            bridge_server = BridgeHTTPServer(
                ("127.0.0.1", 0),
                BridgeHandler,
                runtime=runtime,
                token="",
                ingest_root=tmp_root / "ingest",
            )
            bridge_thread = self._start_server(bridge_server)
            bridge_base_url = f"http://127.0.0.1:{bridge_server.server_address[1]}"

            with mock.patch.object(BoothController, "_sleep_ms", autospec=True, return_value=None):
                try:
                    status, ran = request_json(
                        f"{bridge_base_url}/v1/mira-light/run-scene",
                        method="POST",
                        payload={"scene": "farewell", "async": False},
                    )
                    self.assertEqual(status, 200)
                    self.assertTrue(ran["ok"])
                    self.assertEqual(ran["runtime"]["lastFinishedScene"], "farewell")

                    status, led = request_json(
                        f"{bridge_base_url}/v1/mira-light/led",
                        method="POST",
                        payload={"mode": "solid", "brightness": 144, "color": {"r": 200, "g": 160, "b": 120}},
                    )
                    self.assertEqual(status, 200)
                    self.assertEqual(led["data"]["led"]["brightness"], 144)

                    status, reset = request_json(f"{bridge_base_url}/v1/mira-light/reset", method="POST", payload={})
                    self.assertEqual(status, 200)
                    self.assertTrue(reset["data"]["ok"])

                    status, device_status = request_json(f"{bridge_base_url}/v1/mira-light/status")
                    self.assertEqual(status, 200)
                    self.assertTrue(device_status["data"]["ok"])
                    self.assertEqual(device_status["data"]["sensors"]["headCapacitive"], 0)
                    self.assertEqual(len(device_status["data"]["led"]["pixelSignals"]), 40)

                    status, admin_state = request_json(f"{mock_base_url}/__admin/state")
                    self.assertEqual(status, 200)
                    request_paths = [item["path"] for item in admin_state["recentRequests"]]
                    self.assertIn("/control", request_paths)
                    self.assertIn("/led", request_paths)
                    self.assertIn("/reset", request_paths)
                    self.assertEqual(admin_state["led"]["mode"], "off")
                    self.assertEqual(admin_state["sensors"]["headCapacitive"], 0)
                finally:
                    bridge_server.shutdown()
                    bridge_server.server_close()
                    bridge_thread.join(timeout=3)
                    mock_server.shutdown()
                    mock_server.server_close()
                    mock_thread.join(timeout=3)

    def test_dynamic_farewell_context_reaches_mock_device(self) -> None:
        with TemporaryDirectory() as tmpdir:
            tmp_root = Path(tmpdir)
            mock_server = create_server("127.0.0.1", 0)
            mock_thread = self._start_server(mock_server)
            mock_base_url = f"http://127.0.0.1:{mock_server.server_address[1]}"

            runtime = MiraLightRuntime(base_url=mock_base_url, dry_run=False, timeout_seconds=1.0)
            runtime.audio_player.dry_run = True
            bridge_server = BridgeHTTPServer(
                ("127.0.0.1", 0),
                BridgeHandler,
                runtime=runtime,
                token="",
                ingest_root=tmp_root / "ingest",
            )
            bridge_thread = self._start_server(bridge_server)
            bridge_base_url = f"http://127.0.0.1:{bridge_server.server_address[1]}"

            with mock.patch.object(BoothController, "_sleep_ms", autospec=True, return_value=None):
                try:
                    status, ran = request_json(
                        f"{bridge_base_url}/v1/mira-light/run-scene",
                        method="POST",
                        payload={
                            "scene": "farewell",
                            "async": False,
                            "context": {"departureDirection": "left"},
                        },
                    )
                    self.assertEqual(status, 200)
                    self.assertTrue(ran["ok"])

                    status, admin_state = request_json(f"{mock_base_url}/__admin/state")
                    self.assertEqual(status, 200)
                    control_payloads = [
                        item["payload"]
                        for item in admin_state["recentRequests"]
                        if item["path"] == "/control" and isinstance(item.get("payload"), dict)
                    ]
                    self.assertTrue(any(payload.get("servo1") == 78 for payload in control_payloads))
                finally:
                    bridge_server.shutdown()
                    bridge_server.server_close()
                    bridge_thread.join(timeout=3)
                    mock_server.shutdown()
                    mock_server.server_close()
                    mock_thread.join(timeout=3)

    def test_trigger_endpoint_routes_farewell_and_multi_person_contexts(self) -> None:
        with TemporaryDirectory() as tmpdir:
            tmp_root = Path(tmpdir)
            mock_server = create_server("127.0.0.1", 0)
            mock_thread = self._start_server(mock_server)
            mock_base_url = f"http://127.0.0.1:{mock_server.server_address[1]}"

            runtime = MiraLightRuntime(base_url=mock_base_url, dry_run=False, timeout_seconds=1.0)
            runtime.audio_player.dry_run = True
            bridge_server = BridgeHTTPServer(
                ("127.0.0.1", 0),
                BridgeHandler,
                runtime=runtime,
                token="",
                ingest_root=tmp_root / "ingest",
            )
            bridge_thread = self._start_server(bridge_server)
            bridge_base_url = f"http://127.0.0.1:{bridge_server.server_address[1]}"

            with mock.patch.object(BoothController, "_sleep_ms", autospec=True, return_value=None):
                try:
                    status, farewell = request_json(
                        f"{bridge_base_url}/v1/mira-light/trigger",
                        method="POST",
                        payload={"event": "farewell_detected", "payload": {"direction": "left"}},
                    )
                    self.assertEqual(status, 200)
                    self.assertTrue(farewell["ok"])
                    self._wait_until_not_running(bridge_base_url)

                    status, multi = request_json(
                        f"{bridge_base_url}/v1/mira-light/trigger",
                        method="POST",
                        payload={
                            "event": "multi_person_detected",
                            "payload": {"primaryDirection": "left", "secondaryDirection": "right"},
                        },
                    )
                    self.assertEqual(status, 200)
                    self.assertTrue(multi["ok"])
                    self._wait_until_not_running(bridge_base_url)

                    status, admin_state = request_json(f"{mock_base_url}/__admin/state")
                    self.assertEqual(status, 200)
                    control_payloads = [
                        item["payload"]
                        for item in admin_state["recentRequests"]
                        if item["path"] == "/control" and isinstance(item.get("payload"), dict)
                    ]
                    self.assertTrue(any(payload.get("servo1") == 78 for payload in control_payloads))
                    self.assertTrue(any(payload.get("servo1") == 106 for payload in control_payloads))
                finally:
                    bridge_server.shutdown()
                    bridge_server.server_close()
                    bridge_thread.join(timeout=3)
                    mock_server.shutdown()
                    mock_server.server_close()
                    mock_thread.join(timeout=3)

    def test_fault_injection_surfaces_bridge_errors(self) -> None:
        with TemporaryDirectory() as tmpdir:
            tmp_root = Path(tmpdir)
            mock_server = create_server("127.0.0.1", 0)
            mock_thread = self._start_server(mock_server)
            mock_base_url = f"http://127.0.0.1:{mock_server.server_address[1]}"

            runtime = MiraLightRuntime(base_url=mock_base_url, dry_run=False, timeout_seconds=0.2)
            runtime.audio_player.dry_run = True
            bridge_server = BridgeHTTPServer(
                ("127.0.0.1", 0),
                BridgeHandler,
                runtime=runtime,
                token="",
                ingest_root=tmp_root / "ingest",
            )
            bridge_thread = self._start_server(bridge_server)
            bridge_base_url = f"http://127.0.0.1:{bridge_server.server_address[1]}"

            try:
                status, injected = request_json(
                    f"{mock_base_url}/__admin/faults",
                    method="POST",
                    payload={
                        "replace": True,
                        "rules": [
                            {"method": "GET", "path": "/status", "mode": "http_error", "status": 503, "times": 1},
                            {"method": "POST", "path": "/led", "mode": "invalid_json", "times": 1},
                            {"method": "POST", "path": "/control", "mode": "timeout", "delayMs": 400, "times": 1},
                        ],
                    },
                )
                self.assertEqual(status, 200)
                self.assertEqual(len(injected["rules"]), 3)

                status, status_error = request_json(f"{bridge_base_url}/v1/mira-light/status")
                self.assertEqual(status, 500)
                self.assertIn("HTTP 503", status_error["error"])

                status, led_error = request_json(
                    f"{bridge_base_url}/v1/mira-light/led",
                    method="POST",
                    payload={"mode": "solid", "color": {"r": 255, "g": 210, "b": 180}},
                )
                self.assertEqual(status, 200)
                self.assertEqual(led_error["data"], "{invalid-json")

                status, control_error = request_json(
                    f"{bridge_base_url}/v1/mira-light/control",
                    method="POST",
                    payload={"mode": "absolute", "servo1": 90},
                )
                self.assertEqual(status, 500)
                self.assertIn("timed out", control_error["error"])
            finally:
                bridge_server.shutdown()
                bridge_server.server_close()
                bridge_thread.join(timeout=3)
                mock_server.shutdown()
                mock_server.server_close()
                mock_thread.join(timeout=3)

    def test_mock_device_supports_sensor_updates_and_device_state_injection(self) -> None:
        with TemporaryDirectory() as tmpdir:
            tmp_root = Path(tmpdir)
            mock_server = create_server("127.0.0.1", 0)
            mock_thread = self._start_server(mock_server)
            mock_base_url = f"http://127.0.0.1:{mock_server.server_address[1]}"

            runtime = MiraLightRuntime(base_url=mock_base_url, dry_run=False, timeout_seconds=1.0)
            runtime.audio_player.dry_run = True
            bridge_server = BridgeHTTPServer(
                ("127.0.0.1", 0),
                BridgeHandler,
                runtime=runtime,
                token="",
                ingest_root=tmp_root / "ingest",
            )
            bridge_thread = self._start_server(bridge_server)
            bridge_base_url = f"http://127.0.0.1:{bridge_server.server_address[1]}"

            try:
                status, sensors = request_json(
                    f"{bridge_base_url}/v1/mira-light/sensors",
                    method="POST",
                    payload={"headCapacitive": 1},
                )
                self.assertEqual(status, 200)
                self.assertEqual(sensors["data"]["sensors"]["headCapacitive"], 1)

                status, injected = request_json(
                    f"{mock_base_url}/__admin/device-state",
                    method="POST",
                    payload={
                        "led": {
                            "mode": "vector",
                            "pixelSignals": [[10, 20, 30, 40] for _ in range(40)],
                        }
                    },
                )
                self.assertEqual(status, 200)
                self.assertEqual(injected["state"]["led"]["pixelSignals"][0], [10, 20, 30, 40])

                status, bridge_status = request_json(f"{bridge_base_url}/v1/mira-light/status")
                self.assertEqual(status, 200)
                self.assertEqual(bridge_status["data"]["sensors"]["headCapacitive"], 1)
                self.assertEqual(bridge_status["data"]["led"]["pixelSignals"][0], [10, 20, 30, 40])

                status, bridge_sensors = request_json(f"{bridge_base_url}/v1/mira-light/sensors")
                self.assertEqual(status, 200)
                self.assertEqual(bridge_sensors["data"]["headCapacitive"], 1)
            finally:
                bridge_server.shutdown()
                bridge_server.server_close()
                bridge_thread.join(timeout=3)
                mock_server.shutdown()
                mock_server.server_close()
                mock_thread.join(timeout=3)


if __name__ == "__main__":
    unittest.main()
