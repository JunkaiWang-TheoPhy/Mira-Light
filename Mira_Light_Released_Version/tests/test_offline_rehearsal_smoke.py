from __future__ import annotations

import json
import threading
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


class OfflineRehearsalSmokeTest(unittest.TestCase):
    def _start_server(self, server):
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        return thread

    def test_scene_flow_reaches_mock_device(self) -> None:
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
                        payload={"scene": "farewell", "async": False, "cueMode": "scene"},
                    )
                    self.assertEqual(status, 200)
                    self.assertTrue(ran["ok"])
                    self.assertEqual(ran["runtime"]["lastFinishedScene"], "farewell")

                    status, admin_state = request_json(f"{mock_base_url}/__admin/state")
                    self.assertEqual(status, 200)
                    request_paths = [item["path"] for item in admin_state["recentRequests"]]
                    self.assertIn("/control", request_paths)
                    self.assertIn("/led", request_paths)
                finally:
                    bridge_server.shutdown()
                    bridge_server.server_close()
                    bridge_thread.join(timeout=3)
                    mock_server.shutdown()
                    mock_server.server_close()
                    mock_thread.join(timeout=3)

    def test_faults_surface_as_bridge_errors(self) -> None:
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
                            {"method": "POST", "path": "/control", "mode": "timeout", "delayMs": 400, "times": 1},
                        ],
                    },
                )
                self.assertEqual(status, 200)
                self.assertEqual(len(injected["rules"]), 2)

                status, status_error = request_json(f"{bridge_base_url}/v1/mira-light/status")
                self.assertEqual(status, 500)
                self.assertIn("HTTP 503", status_error["error"])

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


if __name__ == "__main__":
    unittest.main()
