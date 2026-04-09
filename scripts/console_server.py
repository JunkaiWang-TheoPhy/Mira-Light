#!/usr/bin/env python3
"""Simple static web console that proxies all control requests to the bridge."""

from __future__ import annotations

import argparse
import json
import mimetypes
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import unquote, urlparse
from urllib.request import Request, urlopen


WEB_ROOT = Path(__file__).resolve().parent.parent / "web"
DEFAULT_LIVE_VISION_DIR = Path(__file__).resolve().parent.parent / "runtime" / "live-vision"
DEFAULT_BRIDGE_URL = "http://127.0.0.1:9783"
DEFAULT_BRIDGE_TIMEOUT_SECONDS = 5.0
DEFAULT_OPENCLAW_CONFIG_PATH = Path.home() / ".openclaw" / "openclaw.json"
DEFAULT_VISION_OPERATOR_STATE_PATH = DEFAULT_LIVE_VISION_DIR / "vision.operator.json"
DEFAULT_VISION_EVENT_PATH = DEFAULT_LIVE_VISION_DIR / "vision.latest.json"
DEFAULT_VISION_BRIDGE_STATE_PATH = DEFAULT_LIVE_VISION_DIR / "vision.bridge.state.json"


class ConsoleHTTPServer(ThreadingHTTPServer):
    def __init__(
        self,
        server_address,
        handler_class,
        web_root: Path,
        bridge_base_url: str,
        bridge_token: str,
        bridge_timeout_seconds: float,
        vision_operator_state_path: Path,
        vision_event_path: Path,
        vision_bridge_state_path: Path,
    ):
        super().__init__(server_address, handler_class)
        self.web_root = web_root
        self.bridge_base_url = bridge_base_url.rstrip("/")
        self.bridge_token = bridge_token
        self.bridge_timeout_seconds = bridge_timeout_seconds
        self.vision_operator_state_path = vision_operator_state_path
        self.vision_event_path = vision_event_path
        self.vision_bridge_state_path = vision_bridge_state_path


class ConsoleHandler(BaseHTTPRequestHandler):
    server: ConsoleHTTPServer

    def log_message(self, format: str, *args) -> None:  # noqa: A003
        print(f"[console] {self.address_string()} - {format % args}")

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

    def _load_vision_operator_state(self) -> dict:
        path = self.server.vision_operator_state_path
        if not path.is_file():
            return {"lockSelectedTrackId": None}
        try:
            raw = path.read_text(encoding="utf-8").strip()
            if not raw:
                return {"lockSelectedTrackId": None}
            parsed = json.loads(raw)
            return parsed if isinstance(parsed, dict) else {"lockSelectedTrackId": None}
        except Exception:
            return {"lockSelectedTrackId": None}

    def _load_json_file(self, path: Path) -> dict | None:
        if not path.is_file():
            return None
        try:
            raw = path.read_text(encoding="utf-8").strip()
            if not raw:
                return None
            parsed = json.loads(raw)
            return parsed if isinstance(parsed, dict) else None
        except Exception:
            return None

    def _save_vision_operator_state(self, payload: dict) -> dict:
        path = self.server.vision_operator_state_path
        path.parent.mkdir(parents=True, exist_ok=True)
        current = self._load_vision_operator_state()
        current.update(payload)
        normalized = {
            "lockSelectedTrackId": None,
            "updatedAt": current.get("updatedAt"),
            "note": current.get("note"),
        }
        raw_track_id = current.get("lockSelectedTrackId")
        if raw_track_id not in {None, "", False}:
            try:
                value = int(raw_track_id)
                normalized["lockSelectedTrackId"] = value if value > 0 else None
            except (TypeError, ValueError):
                normalized["lockSelectedTrackId"] = None
        path.write_text(json.dumps(normalized, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        return normalized

    def _proxy_json(self, method: str, bridge_path: str, payload: dict | None = None) -> None:
        data = None if payload is None else json.dumps(payload).encode("utf-8")
        headers = {"Content-Type": "application/json"}
        if self.server.bridge_token:
            headers["Authorization"] = f"Bearer {self.server.bridge_token}"

        req = Request(
            f"{self.server.bridge_base_url}{bridge_path}",
            data=data,
            headers=headers,
            method=method,
        )

        try:
            with urlopen(req, timeout=self.server.bridge_timeout_seconds) as response:
                status_code = response.status
                raw = response.read().decode("utf-8")
        except HTTPError as exc:
            status_code = exc.code
            raw = exc.read().decode("utf-8", errors="replace")
        except URLError as exc:
            self._send_json(502, {"ok": False, "error": f"Bridge unavailable: {exc.reason}"})
            return

        try:
            parsed = json.loads(raw) if raw.strip() else {}
        except json.JSONDecodeError:
            self._send_json(502, {"ok": False, "error": "Bridge returned invalid JSON"})
            return

        self._send_json(status_code, parsed)

    def do_GET(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        path = parsed.path

        if path == "/api/scenes":
            self._proxy_json("GET", "/v1/mira-light/scenes")
            return

        if path == "/api/runtime":
            self._proxy_json("GET", "/v1/mira-light/runtime")
            return

        if path == "/api/logs":
            self._proxy_json("GET", "/v1/mira-light/logs")
            return

        if path == "/api/status":
            self._proxy_json("GET", "/v1/mira-light/status")
            return

        if path == "/api/led":
            self._proxy_json("GET", "/v1/mira-light/led")
            return

        if path == "/api/actions":
            self._proxy_json("GET", "/v1/mira-light/actions")
            return

        if path == "/api/profile":
            self._proxy_json("GET", "/v1/mira-light/profile")
            return

        if path == "/api/config":
            self._proxy_json("GET", "/v1/mira-light/runtime")
            return

        if path == "/api/vision-operator":
            self._send_json(200, {"ok": True, "state": self._load_vision_operator_state()})
            return

        if path == "/api/vision":
            self._send_json(
                200,
                {
                    "ok": True,
                    "operator": self._load_vision_operator_state(),
                    "latestEvent": self._load_json_file(self.server.vision_event_path),
                    "bridgeState": self._load_json_file(self.server.vision_bridge_state_path),
                },
            )
            return

        self._serve_static(path)

    def do_POST(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        path = parsed.path

        if path.startswith("/api/run/"):
            scene_name = unquote(path.removeprefix("/api/run/"))
            body = self._read_json_body()
            payload = {"scene": scene_name, "async": True}
            if isinstance(body, dict):
                payload.update(body)
            self._proxy_json("POST", "/v1/mira-light/run-scene", payload)
            return

        if path == "/api/trigger":
            self._proxy_json("POST", "/v1/mira-light/trigger", self._read_json_body())
            return

        if path == "/api/reset":
            self._proxy_json("POST", "/v1/mira-light/reset")
            return

        if path == "/api/operator/stop-to-neutral":
            self._proxy_json("POST", "/v1/mira-light/operator/stop-to-neutral")
            return

        if path == "/api/operator/stop-to-sleep":
            self._proxy_json("POST", "/v1/mira-light/operator/stop-to-sleep")
            return

        if path == "/api/apply-pose":
            self._proxy_json("POST", "/v1/mira-light/apply-pose", self._read_json_body())
            return

        if path == "/api/stop":
            self._proxy_json("POST", "/v1/mira-light/stop")
            return

        if path == "/api/config":
            self._proxy_json("POST", "/v1/mira-light/config", self._read_json_body())
            return

        if path == "/api/profile/capture-pose":
            self._proxy_json("POST", "/v1/mira-light/profile/capture-pose", self._read_json_body())
            return

        if path == "/api/profile/set-servo-meta":
            self._proxy_json("POST", "/v1/mira-light/profile/set-servo-meta", self._read_json_body())
            return

        if path == "/api/vision-operator":
            body = self._read_json_body()
            state = self._save_vision_operator_state(body if isinstance(body, dict) else {})
            self._send_json(200, {"ok": True, "state": state})
            return

        self._send_json(404, {"ok": False, "error": "Unknown endpoint"})


def resolve_bridge_token(env_name: str) -> str:
    token = os.environ.get(env_name, "").strip()
    if token:
        return token

    if DEFAULT_OPENCLAW_CONFIG_PATH.is_file():
        try:
            raw = json.loads(DEFAULT_OPENCLAW_CONFIG_PATH.read_text(encoding="utf-8"))
            plugins = raw.get("plugins", {})
            entries = plugins.get("entries", {})
            mira_entry = entries.get("mira-light-bridge", {})
            config = mira_entry.get("config", {})
            token = str(config.get("bridgeToken") or "").strip()
            if token:
                return token
        except Exception:
            pass

    return ""


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run the Mira Light local web console.")
    parser.add_argument("--host", default="127.0.0.1", help="HTTP bind host")
    parser.add_argument("--port", default=8765, type=int, help="HTTP bind port")
    parser.add_argument(
        "--bridge-base-url",
        default=os.environ.get("MIRA_LIGHT_CONSOLE_BRIDGE_URL", DEFAULT_BRIDGE_URL),
        help="Bridge base URL",
    )
    parser.add_argument("--bridge-token-env", default="MIRA_LIGHT_BRIDGE_TOKEN", help="Bridge token env name")
    parser.add_argument(
        "--bridge-timeout",
        default=DEFAULT_BRIDGE_TIMEOUT_SECONDS,
        type=float,
        help="Bridge proxy timeout in seconds",
    )
    parser.add_argument(
        "--vision-operator-state-path",
        default=str(os.environ.get("MIRA_LIGHT_VISION_OPERATOR_STATE_PATH", DEFAULT_VISION_OPERATOR_STATE_PATH)),
        help="Local JSON file used for director-console target lock state.",
    )
    parser.add_argument(
        "--vision-event-path",
        default=str(os.environ.get("MIRA_LIGHT_VISION_EVENT_PATH", DEFAULT_VISION_EVENT_PATH)),
        help="Path to the latest vision event JSON.",
    )
    parser.add_argument(
        "--vision-bridge-state-path",
        default=str(os.environ.get("MIRA_LIGHT_VISION_BRIDGE_STATE_PATH", DEFAULT_VISION_BRIDGE_STATE_PATH)),
        help="Path to the vision bridge state JSON.",
    )
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    bridge_token = resolve_bridge_token(args.bridge_token_env)
    print(f"[console] starting at http://{args.host}:{args.port}")
    print(f"[console] proxying bridge {args.bridge_base_url}")
    print(f"[console] bridge token env {args.bridge_token_env} present={bool(bridge_token)}")

    server = ConsoleHTTPServer(
        (args.host, args.port),
        ConsoleHandler,
        web_root=WEB_ROOT,
        bridge_base_url=args.bridge_base_url,
        bridge_token=bridge_token,
        bridge_timeout_seconds=args.bridge_timeout,
        vision_operator_state_path=Path(args.vision_operator_state_path).expanduser().resolve(),
        vision_event_path=Path(args.vision_event_path).expanduser().resolve(),
        vision_bridge_state_path=Path(args.vision_bridge_state_path).expanduser().resolve(),
    )
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("[console] shutdown requested")
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
