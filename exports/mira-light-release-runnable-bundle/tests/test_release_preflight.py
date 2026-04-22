import json
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

import sys


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = ROOT / "scripts"

if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import preflight_release


class JsonFixtureServer(ThreadingHTTPServer):
    def __init__(self, address, *, routes: dict[str, tuple[int, object]], required_auth: dict[str, str] | None = None):
        self.routes = routes
        self.required_auth = required_auth or {}
        super().__init__(address, JsonFixtureHandler)


class JsonFixtureHandler(BaseHTTPRequestHandler):
    server: JsonFixtureServer

    def log_message(self, format: str, *args) -> None:  # noqa: A003
        return

    def do_GET(self) -> None:  # noqa: N802
        if self.path not in self.server.routes:
            self.send_error(404)
            return

        expected_auth = self.server.required_auth.get(self.path)
        if expected_auth and self.headers.get("Authorization") != expected_auth:
            body = json.dumps({"ok": False, "error": "unauthorized"}).encode("utf-8")
            self.send_response(401)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return

        status, payload = self.server.routes[self.path]
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def start_json_server(
    routes: dict[str, tuple[int, object]],
    *,
    required_auth: dict[str, str] | None = None,
) -> tuple[JsonFixtureServer, threading.Thread, str]:
    server = JsonFixtureServer(("127.0.0.1", 0), routes=routes, required_auth=required_auth)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    base_url = f"http://127.0.0.1:{server.server_address[1]}"
    return server, thread, base_url


class ReleasePreflightTest(unittest.TestCase):
    def test_parser_defaults_to_offline_mode(self) -> None:
        parser = preflight_release.build_parser()
        args = parser.parse_args([])
        self.assertEqual(args.mode, "offline")

    def test_parser_uses_bridge_host_and_port_when_url_is_not_set(self) -> None:
        with patch.dict(
            preflight_release.os.environ,
            {
                "MIRA_LIGHT_BRIDGE_HOST": "0.0.0.0",
                "MIRA_LIGHT_BRIDGE_PORT": "19783",
            },
            clear=True,
        ):
            parser = preflight_release.build_parser()
            args = parser.parse_args([])
            self.assertEqual(args.bridge_url, "http://127.0.0.1:19783")

    def test_offline_preflight_flags_missing_release_venv(self) -> None:
        with TemporaryDirectory() as tmpdir:
            config = preflight_release.PreflightConfig(
                release_root=Path(tmpdir),
                bridge_base_url="http://127.0.0.1:9783",
                receiver_base_url="http://127.0.0.1:9784",
                lamp_base_url="",
                bridge_token="",
                timeout_seconds=1.0,
                strict_online=False,
            )
            results = preflight_release.run_offline_checks(config)
            by_name = {result.name: result for result in results}
            self.assertEqual(by_name["release venv"].status, "FAIL")

    def test_online_preflight_passes_against_mock_endpoints(self) -> None:
        bridge_server, bridge_thread, bridge_url = start_json_server(
            {
                "/health": (200, {"ok": True}),
                "/v1/mira-light/scenes": (200, {"ok": True, "items": [{"id": "farewell"}]}),
            },
            required_auth={"/v1/mira-light/scenes": "Bearer token-123"},
        )
        receiver_server, receiver_thread, receiver_url = start_json_server(
            {"/health": (200, {"ok": True})}
        )
        lamp_server, lamp_thread, lamp_url = start_json_server(
            {"/status": (200, {"servos": []})}
        )
        try:
            config = preflight_release.PreflightConfig(
                release_root=ROOT,
                bridge_base_url=bridge_url,
                receiver_base_url=receiver_url,
                lamp_base_url=lamp_url,
                bridge_token="token-123",
                timeout_seconds=1.0,
                strict_online=True,
            )
            results = preflight_release.run_online_checks(config)
            self.assertTrue(all(result.status == "PASS" for result in results))
        finally:
            for server, thread in (
                (bridge_server, bridge_thread),
                (receiver_server, receiver_thread),
                (lamp_server, lamp_thread),
            ):
                server.shutdown()
                server.server_close()
                thread.join(timeout=3)

    def test_online_preflight_uses_warning_when_relaxed(self) -> None:
        config = preflight_release.PreflightConfig(
            release_root=ROOT,
            bridge_base_url="http://127.0.0.1:9",
            receiver_base_url="http://127.0.0.1:9",
            lamp_base_url="",
            bridge_token="",
            timeout_seconds=0.2,
            strict_online=False,
        )
        results = preflight_release.run_online_checks(config)
        by_name = {result.name: result for result in results}
        self.assertEqual(by_name["bridge health"].status, "WARN")
        self.assertEqual(by_name["receiver health"].status, "WARN")
        self.assertEqual(by_name["lamp status"].status, "WARN")


if __name__ == "__main__":
    unittest.main()
