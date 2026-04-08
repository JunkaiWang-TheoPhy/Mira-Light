import json
import threading
import unittest
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
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
from embodied_memory_client import EmbodiedMemoryClient
from mira_light_runtime import MiraLightRuntime


def request_json(url: str, *, method: str = "GET", payload: dict | None = None) -> tuple[int, dict]:
    data = None if payload is None else json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json"},
        method=method,
    )
    with urllib.request.urlopen(req, timeout=3) as response:
        return response.status, json.loads(response.read().decode("utf-8"))


class MemoryWriteCaptureServer(ThreadingHTTPServer):
    def __init__(self, address):
        self.requests: list[dict] = []
        self.session_notes: dict[tuple[str, str], dict] = {}
        super().__init__(address, MemoryWriteCaptureHandler)


class MemoryWriteCaptureHandler(BaseHTTPRequestHandler):
    server: MemoryWriteCaptureServer

    def log_message(self, format: str, *args) -> None:  # noqa: A003
        return

    def do_POST(self) -> None:  # noqa: N802
        length = int(self.headers.get("Content-Length", "0") or 0)
        raw = self.rfile.read(length).decode("utf-8") if length > 0 else "{}"
        body = json.loads(raw)
        self.server.requests.append({"path": self.path, "body": body})

        if self.path == "/v1/session-memory/current":
            key = (body.get("userId", ""), body.get("sessionId", ""))
            encoded = json.dumps({"ok": True, "note": self.server.session_notes.get(key)}).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(encoded)))
            self.end_headers()
            self.wfile.write(encoded)
            return

        if self.path == "/v1/session-memory/update":
            key = (body.get("userId", ""), body.get("sessionId", ""))
            note = {
                "sessionId": body.get("sessionId"),
                "userId": body.get("userId"),
                "sourceMessageId": body.get("sourceMessageId"),
                **body.get("note", {}),
                "createdAt": "2026-04-09T00:00:00+08:00",
                "updatedAt": "2026-04-09T00:00:00+08:00",
            }
            self.server.session_notes[key] = note
            encoded = json.dumps({"ok": True, "created": True, "updatedAt": note["updatedAt"], "note": note}).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(encoded)))
            self.end_headers()
            self.wfile.write(encoded)
            return

        encoded = json.dumps({"ok": True, "written": len(body.get("items", []))}).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)


class FakeMemoryClient:
    def __init__(self) -> None:
        self.scene_outcomes: list[dict] = []
        self.device_reports: list[dict] = []
        self.scene_session_states: list[dict] = []
        self.enabled = True

    def record_scene_outcome(self, **payload) -> None:
        self.scene_outcomes.append(payload)

    def record_device_report(self, **payload) -> None:
        self.device_reports.append(payload)

    def record_scene_session_state(self, **payload) -> None:
        self.scene_session_states.append(payload)


class EmbodiedMemoryTest(unittest.TestCase):
    def test_embodied_memory_client_posts_scene_failure_as_memory_items(self) -> None:
        server = MemoryWriteCaptureServer(("127.0.0.1", 0))
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            client = EmbodiedMemoryClient(
                base_url=f"http://127.0.0.1:{server.server_address[1]}",
                enabled=True,
                user_id="mira-light-test",
            )
            result = client.record_scene_outcome(
                scene_name="celebrate",
                status="failed",
                runtime_state={"running": False, "lastError": "servo3 timed out"},
                error="servo3 timed out",
            )

            self.assertTrue(result["ok"])
            self.assertEqual(len(server.requests), 1)
            self.assertEqual(server.requests[0]["path"], "/v1/memory/write")
            items = server.requests[0]["body"]["items"]
            self.assertEqual(len(items), 2)
            self.assertEqual(items[0]["layer"], "episodic")
            self.assertEqual(items[1]["layer"], "working")
            self.assertEqual(items[0]["namespace"], "home")
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=3)

    def test_bridge_records_scene_and_device_outcomes_when_memory_client_is_attached(self) -> None:
        runtime = MiraLightRuntime(base_url="http://127.0.0.1:9", dry_run=True)
        fake_memory = FakeMemoryClient()
        runtime.set_embodied_memory_client(fake_memory)

        with TemporaryDirectory() as tmpdir:
            server = BridgeHTTPServer(
                ("127.0.0.1", 0),
                BridgeHandler,
                runtime=runtime,
                token="",
                ingest_root=Path(tmpdir),
                memory_client=fake_memory,
            )
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            base_url = f"http://127.0.0.1:{server.server_address[1]}"
            try:
                status, ran = request_json(
                    f"{base_url}/v1/mira-light/run-scene",
                    method="POST",
                    payload={"scene": "farewell", "async": False},
                )
                self.assertEqual(status, 200)
                self.assertTrue(ran["ok"])
                self.assertEqual(len(fake_memory.scene_outcomes), 1)
                self.assertEqual(fake_memory.scene_outcomes[0]["scene_name"], "farewell")
                self.assertEqual(fake_memory.scene_outcomes[0]["status"], "completed")

                status, stored = request_json(
                    f"{base_url}/v1/mira-light/device/status",
                    method="POST",
                    payload={
                        "deviceId": "mira-light-001",
                        "scene": "farewell",
                        "playing": False,
                        "ledMode": "warm",
                    },
                )
                self.assertEqual(status, 200)
                self.assertTrue(stored["ok"])
                self.assertEqual(len(fake_memory.device_reports), 1)
                self.assertEqual(fake_memory.device_reports[0]["report_type"], "status")
                self.assertEqual([item["phase"] for item in fake_memory.scene_session_states], ["started", "completed"])
            finally:
                server.shutdown()
                server.server_close()
                thread.join(timeout=3)

    def test_embodied_memory_client_updates_session_memory(self) -> None:
        server = MemoryWriteCaptureServer(("127.0.0.1", 0))
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            client = EmbodiedMemoryClient(
                base_url=f"http://127.0.0.1:{server.server_address[1]}",
                enabled=True,
                user_id="mira-light-bridge",
            )
            result = client.record_scene_session_state(
                scene_name="track_target",
                phase="started",
                runtime_state={"running": True, "runningScene": "track_target"},
                session_id="mira-light-runtime",
            )

            self.assertTrue(result["ok"])
            current = client.get_current_session_note(session_id="mira-light-runtime")
            self.assertTrue(current["ok"])
            self.assertIsNotNone(current["note"])
            self.assertEqual(current["note"]["sessionId"], "mira-light-runtime")
            self.assertIn("track_target", current["note"]["currentState"])
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=3)


if __name__ == "__main__":
    unittest.main()
