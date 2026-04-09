from __future__ import annotations

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
from console_server import ConsoleHTTPServer, ConsoleHandler
from mira_light_runtime import MiraLightRuntime
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


def request_text(url: str) -> tuple[int, str]:
    with urllib.request.urlopen(url, timeout=3) as response:
        return response.status, response.read().decode("utf-8")


class ConsoleServerTest(unittest.TestCase):
    def _start_server(self, server):
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        return thread

    def test_console_proxies_sensor_mock_controls(self) -> None:
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

            console_server = ConsoleHTTPServer(
                ("127.0.0.1", 0),
                ConsoleHandler,
                web_root=ROOT / "web",
                bridge_base_url=bridge_base_url,
                bridge_token="",
                bridge_timeout_seconds=1.0,
                vision_operator_state_path=tmp_root / "vision.operator.json",
                vision_event_path=tmp_root / "vision.latest.json",
                vision_bridge_state_path=tmp_root / "vision.bridge.state.json",
                capture_memory_latest_observation_path=tmp_root / "capture.latest.json",
                capture_memory_status_path=tmp_root / "capture.status.json",
            )
            console_thread = self._start_server(console_server)
            console_base_url = f"http://127.0.0.1:{console_server.server_address[1]}"

            try:
                status, updated = request_json(
                    f"{console_base_url}/api/sensors",
                    method="POST",
                    payload={"headCapacitive": 1},
                )
                self.assertEqual(status, 200)
                self.assertEqual(updated["data"]["sensors"]["headCapacitive"], 1)

                status, sensors = request_json(f"{console_base_url}/api/sensors")
                self.assertEqual(status, 200)
                self.assertEqual(sensors["data"]["headCapacitive"], 1)

                status, device_status = request_json(f"{console_base_url}/api/status")
                self.assertEqual(status, 200)
                self.assertEqual(device_status["data"]["sensors"]["headCapacitive"], 1)
            finally:
                console_server.shutdown()
                console_server.server_close()
                console_thread.join(timeout=3)
                bridge_server.shutdown()
                bridge_server.server_close()
                bridge_thread.join(timeout=3)
                mock_server.shutdown()
                mock_server.server_close()
                mock_thread.join(timeout=3)

    def test_console_persists_vision_operator_target_mode(self) -> None:
        with TemporaryDirectory() as tmpdir:
            tmp_root = Path(tmpdir)
            console_server = ConsoleHTTPServer(
                ("127.0.0.1", 0),
                ConsoleHandler,
                web_root=ROOT / "web",
                bridge_base_url="http://127.0.0.1:9",
                bridge_token="",
                bridge_timeout_seconds=1.0,
                vision_operator_state_path=tmp_root / "vision.operator.json",
                vision_event_path=tmp_root / "vision.latest.json",
                vision_bridge_state_path=tmp_root / "vision.bridge.state.json",
                capture_memory_latest_observation_path=tmp_root / "capture.latest.json",
                capture_memory_status_path=tmp_root / "capture.status.json",
            )
            console_thread = self._start_server(console_server)
            console_base_url = f"http://127.0.0.1:{console_server.server_address[1]}"

            try:
                status, saved = request_json(
                    f"{console_base_url}/api/vision-operator",
                    method="POST",
                    payload={"targetMode": "tabletop_follow", "note": "switch to tabletop", "updatedAt": "2026-04-09T00:00:00Z"},
                )
                self.assertEqual(status, 200)
                self.assertEqual(saved["state"]["targetMode"], "tabletop_follow")

                status, loaded = request_json(f"{console_base_url}/api/vision-operator")
                self.assertEqual(status, 200)
                self.assertEqual(loaded["state"]["targetMode"], "tabletop_follow")
                self.assertEqual(loaded["state"]["note"], "switch to tabletop")
            finally:
                console_server.shutdown()
                console_server.server_close()
                console_thread.join(timeout=3)

    def test_console_serves_silent_page(self) -> None:
        with TemporaryDirectory() as tmpdir:
            tmp_root = Path(tmpdir)
            console_server = ConsoleHTTPServer(
                ("127.0.0.1", 0),
                ConsoleHandler,
                web_root=ROOT / "web",
                bridge_base_url="http://127.0.0.1:9",
                bridge_token="",
                bridge_timeout_seconds=1.0,
                vision_operator_state_path=tmp_root / "vision.operator.json",
                vision_event_path=tmp_root / "vision.latest.json",
                vision_bridge_state_path=tmp_root / "vision.bridge.state.json",
                capture_memory_latest_observation_path=tmp_root / "capture.latest.json",
                capture_memory_status_path=tmp_root / "capture.status.json",
            )
            console_thread = self._start_server(console_server)
            console_base_url = f"http://127.0.0.1:{console_server.server_address[1]}"

            try:
                status, html = request_text(f"{console_base_url}/silent.html")
                self.assertEqual(status, 200)
                self.assertIn("Mira Light 无声版导演台", html)
                self.assertIn('data-console-variant="silent"', html)
            finally:
                console_server.shutdown()
                console_server.server_close()
                console_thread.join(timeout=3)

    def test_console_proxies_signal_delivery_contract(self) -> None:
        with TemporaryDirectory() as tmpdir:
            tmp_root = Path(tmpdir)
            runtime = MiraLightRuntime(base_url="http://127.0.0.1:9", dry_run=True, timeout_seconds=1.0)
            bridge_server = BridgeHTTPServer(
                ("127.0.0.1", 0),
                BridgeHandler,
                runtime=runtime,
                token="",
                ingest_root=tmp_root / "ingest",
            )
            bridge_thread = self._start_server(bridge_server)
            bridge_base_url = f"http://127.0.0.1:{bridge_server.server_address[1]}"

            console_server = ConsoleHTTPServer(
                ("127.0.0.1", 0),
                ConsoleHandler,
                web_root=ROOT / "web",
                bridge_base_url=bridge_base_url,
                bridge_token="",
                bridge_timeout_seconds=1.0,
                vision_operator_state_path=tmp_root / "vision.operator.json",
                vision_event_path=tmp_root / "vision.latest.json",
                vision_bridge_state_path=tmp_root / "vision.bridge.state.json",
                capture_memory_latest_observation_path=tmp_root / "capture.latest.json",
                capture_memory_status_path=tmp_root / "capture.status.json",
            )
            console_thread = self._start_server(console_server)
            console_base_url = f"http://127.0.0.1:{console_server.server_address[1]}"

            try:
                status, contract = request_json(f"{console_base_url}/api/signal-delivery")
                self.assertEqual(status, 200)
                self.assertEqual(contract["data"]["docPath"], "docs/Guide/09-Mira Light统一信号交付格式说明.md")
                self.assertEqual(contract["data"]["schemaPath"], "config/mira_light_signal_delivery.schema.json")
                self.assertEqual(contract["data"]["contracts"][2]["payload"]["field"], "headCapacitive")

                status, schema = request_json(f"{console_base_url}/api/signal-delivery/schema")
                self.assertEqual(status, 200)
                self.assertEqual(schema["data"]["$defs"]["led_state"]["properties"]["led_count"]["const"], 40)
            finally:
                console_server.shutdown()
                console_server.server_close()
                console_thread.join(timeout=3)
                bridge_server.shutdown()
                bridge_server.server_close()
                bridge_thread.join(timeout=3)

    def test_motion_script_catalog_includes_signal_delivery_contract(self) -> None:
        with TemporaryDirectory() as tmpdir:
            tmp_root = Path(tmpdir)
            console_server = ConsoleHTTPServer(
                ("127.0.0.1", 0),
                ConsoleHandler,
                web_root=ROOT / "web",
                bridge_base_url="http://127.0.0.1:9",
                bridge_token="",
                bridge_timeout_seconds=1.0,
                vision_operator_state_path=tmp_root / "vision.operator.json",
                vision_event_path=tmp_root / "vision.latest.json",
                vision_bridge_state_path=tmp_root / "vision.bridge.state.json",
                capture_memory_latest_observation_path=tmp_root / "capture.latest.json",
                capture_memory_status_path=tmp_root / "capture.status.json",
            )
            console_thread = self._start_server(console_server)
            console_base_url = f"http://127.0.0.1:{console_server.server_address[1]}"

            try:
                status, payload = request_json(f"{console_base_url}/api/motion-scripts")
                self.assertEqual(status, 200)
                items = payload["items"]
                curious = next(item for item in items if item.get("sceneId") == "curious_observe")
                delivery = curious["signalDelivery"]
                self.assertEqual(delivery["docPath"], "docs/Guide/09-Mira Light统一信号交付格式说明.md")
                self.assertEqual(delivery["recommendedCallerPath"], "/api/run-motion-script/curious_observe")
                self.assertEqual(delivery["signalDomains"], ["jointControl", "led"])
                self.assertEqual(delivery["contracts"][0]["writePath"], "/v1/mira-light/control")
                self.assertEqual(delivery["contracts"][1]["payload"]["readPixelsField"], "pixelSignals")
            finally:
                console_server.shutdown()
                console_server.server_close()
                console_thread.join(timeout=3)


if __name__ == "__main__":
    unittest.main()
