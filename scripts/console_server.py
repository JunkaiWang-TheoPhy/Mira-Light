#!/usr/bin/env python3
"""Simple local web console server for Mira Light booth control."""

from __future__ import annotations

import argparse
import json
import mimetypes
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlparse

from mira_light_runtime import DEFAULT_TIMEOUT_SECONDS, MiraLightRuntime


WEB_ROOT = Path(__file__).resolve().parent.parent / "web"


class ConsoleHTTPServer(ThreadingHTTPServer):
    def __init__(self, server_address, handler_class, runtime: MiraLightRuntime, web_root: Path):
        super().__init__(server_address, handler_class)
        self.runtime = runtime
        self.web_root = web_root


class ConsoleHandler(BaseHTTPRequestHandler):
    server: ConsoleHTTPServer

    def log_message(self, format: str, *args) -> None:  # noqa: A003
        self.server.runtime.log(f"[http] {self.address_string()} - {format % args}")

    def _send_json(self, status_code: int, payload: dict) -> None:
        body = json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _read_json_body(self) -> dict:
        length = int(self.headers.get("Content-Length", "0") or 0)
        if length <= 0:
            return {}
        raw = self.rfile.read(length).decode("utf-8")
        if not raw.strip():
            return {}
        return json.loads(raw)

    def _serve_static(self, raw_path: str) -> None:
        path = raw_path or "/"
        if path == "/":
            path = "/index.html"

        target = (self.server.web_root / path.lstrip("/")).resolve()
        try:
            target.relative_to(self.server.web_root.resolve())
        except ValueError:
            self._send_json(403, {"ok": False, "error": "Forbidden"})
            return

        if not target.is_file():
            self._send_json(404, {"ok": False, "error": "Not found"})
            return

        content = target.read_bytes()
        content_type = mimetypes.guess_type(str(target))[0] or "application/octet-stream"
        self.send_response(200)
        self.send_header("Content-Type", f"{content_type}; charset=utf-8")
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)

    def do_GET(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        path = parsed.path

        try:
            if path == "/api/scenes":
                self._send_json(200, {"ok": True, "items": self.server.runtime.list_scenes()})
                return

            if path == "/api/runtime":
                self._send_json(200, {"ok": True, "runtime": self.server.runtime.get_runtime_state()})
                return

            if path == "/api/logs":
                self._send_json(200, {"ok": True, "items": self.server.runtime.get_logs()})
                return

            if path == "/api/status":
                self._send_json(200, {"ok": True, "data": self.server.runtime.get_status()})
                return

            if path == "/api/led":
                self._send_json(200, {"ok": True, "data": self.server.runtime.get_led()})
                return

            if path == "/api/actions":
                self._send_json(200, {"ok": True, "data": self.server.runtime.get_actions()})
                return

            if path == "/api/profile":
                self._send_json(200, {"ok": True, "profile": self.server.runtime.get_profile()})
                return

            if path == "/api/config":
                self._send_json(200, {"ok": True, "runtime": self.server.runtime.get_runtime_state()})
                return

            self._serve_static(path)
        except Exception as exc:  # noqa: BLE001
            self._send_json(500, {"ok": False, "error": str(exc)})

    def do_POST(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        path = parsed.path

        try:
            if path.startswith("/api/run/"):
                scene_name = unquote(path.removeprefix("/api/run/"))
                runtime_state = self.server.runtime.start_scene(scene_name)
                self._send_json(200, {"ok": True, "runtime": runtime_state})
                return

            if path == "/api/reset":
                result = self.server.runtime.reset_lamp()
                self._send_json(200, {"ok": True, "data": result})
                return

            if path == "/api/operator/stop-to-neutral":
                runtime_state = self.server.runtime.stop_to_pose("neutral")
                self._send_json(200, {"ok": True, "runtime": runtime_state})
                return

            if path == "/api/operator/stop-to-sleep":
                runtime_state = self.server.runtime.stop_to_pose("sleep")
                self._send_json(200, {"ok": True, "runtime": runtime_state})
                return

            if path == "/api/apply-pose":
                body = self._read_json_body()
                pose_name = body.get("pose")
                if not isinstance(pose_name, str) or not pose_name:
                    self._send_json(400, {"ok": False, "error": "pose is required"})
                    return
                result = self.server.runtime.apply_pose(pose_name)
                self._send_json(200, {"ok": True, "data": result})
                return

            if path == "/api/stop":
                runtime_state = self.server.runtime.stop_scene()
                self._send_json(200, {"ok": True, "runtime": runtime_state})
                return

            if path == "/api/config":
                body = self._read_json_body()
                runtime_state = self.server.runtime.update_config(
                    base_url=body.get("baseUrl"),
                    dry_run=body.get("dryRun"),
                )
                self._send_json(200, {"ok": True, "runtime": runtime_state})
                return

            self._send_json(404, {"ok": False, "error": "Unknown endpoint"})
        except KeyError as exc:
            self._send_json(404, {"ok": False, "error": str(exc)})
        except RuntimeError as exc:
            message = str(exc)
            status_code = 409 if "already running" in message else 400
            self._send_json(status_code, {"ok": False, "error": message})
        except Exception as exc:  # noqa: BLE001
            self._send_json(500, {"ok": False, "error": str(exc)})


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run the Mira Light local web console.")
    parser.add_argument("--host", default="127.0.0.1", help="HTTP bind host")
    parser.add_argument("--port", default=8765, type=int, help="HTTP bind port")
    parser.add_argument("--base-url", default="http://172.20.10.3", help="Lamp base URL")
    parser.add_argument("--dry-run", action="store_true", help="Do not send real device requests")
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    runtime = MiraLightRuntime(
        base_url=args.base_url,
        timeout_seconds=DEFAULT_TIMEOUT_SECONDS,
        dry_run=args.dry_run,
    )
    runtime.log(f"[server] starting at http://{args.host}:{args.port}")

    server = ConsoleHTTPServer((args.host, args.port), ConsoleHandler, runtime=runtime, web_root=WEB_ROOT)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        runtime.log("[server] shutdown requested")
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
