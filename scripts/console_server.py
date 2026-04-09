#!/usr/bin/env python3
"""Simple static web console that proxies all control requests to the bridge."""

from __future__ import annotations

import argparse
import importlib.util
import json
import mimetypes
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import unquote, urlparse
from urllib.request import Request, urlopen


WEB_ROOT = Path(__file__).resolve().parent.parent / "web"
MOTIONS_ROOT = Path(__file__).resolve().parent.parent / "Motions"
DEFAULT_LIVE_VISION_DIR = Path(__file__).resolve().parent.parent / "runtime" / "live-vision"
DEFAULT_BRIDGE_URL = "http://127.0.0.1:9783"
DEFAULT_BRIDGE_TIMEOUT_SECONDS = 5.0
FIXED_LAMP_BASE_URL = "tcp://192.168.31.10:9527"
DEFAULT_OPENCLAW_CONFIG_PATH = Path.home() / ".openclaw" / "openclaw.json"
DEFAULT_VISION_OPERATOR_STATE_PATH = DEFAULT_LIVE_VISION_DIR / "vision.operator.json"
DEFAULT_VISION_EVENT_PATH = DEFAULT_LIVE_VISION_DIR / "vision.latest.json"
DEFAULT_VISION_BRIDGE_STATE_PATH = DEFAULT_LIVE_VISION_DIR / "vision.bridge.state.json"


def _coerce_bool(value, default: bool) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in {"1", "true", "yes", "on"}:
            return True
        if normalized in {"0", "false", "no", "off", ""}:
            return False
    return default


def _iter_motion_script_paths(root: Path) -> list[Path]:
    if not root.is_dir():
        return []
    return sorted(path for path in root.glob("*/scene_script.py") if path.is_file())


def _load_motion_script_module(path: Path):
    module_name = f"mira_light_motion_{path.parent.name}"
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Unable to load module spec from {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _motion_script_info_from_module(root: Path, path: Path, module) -> dict:
    raw_info = getattr(module, "SCENE_SCRIPT", {})
    info = dict(raw_info) if isinstance(raw_info, dict) else {}
    scene_id = str(info.get("sceneId") or getattr(module, "SCENE_ID", "")).strip()
    if not scene_id:
        raise ValueError(f"Motion script {path} does not declare sceneId")

    repo_root = root.parent
    info["sceneId"] = scene_id
    info.setdefault("folderName", path.parent.name)
    info.setdefault("folderPath", str(path.parent.relative_to(repo_root)))
    info.setdefault("scriptPath", str(path.relative_to(repo_root)))
    info.setdefault("apiRunPath", f"/api/run-motion-script/{scene_id}")
    return info


def _load_motion_script_catalog(root: Path) -> list[dict]:
    items: list[dict] = []
    for path in _iter_motion_script_paths(root):
        try:
            module = _load_motion_script_module(path)
            info = _motion_script_info_from_module(root, path, module)
            info["ok"] = True
            items.append(info)
        except Exception as exc:  # pragma: no cover - surfaced in API output
            repo_root = root.parent
            items.append(
                {
                    "ok": False,
                    "folderName": path.parent.name,
                    "folderPath": str(path.parent.relative_to(repo_root)),
                    "scriptPath": str(path.relative_to(repo_root)),
                    "error": str(exc),
                }
            )
    return items


def _load_motion_script_by_scene_id(root: Path, scene_id: str) -> dict | None:
    normalized_scene_id = scene_id.strip()
    if not normalized_scene_id:
        return None

    for path in _iter_motion_script_paths(root):
        try:
            module = _load_motion_script_module(path)
            info = _motion_script_info_from_module(root, path, module)
            if info["sceneId"] != normalized_scene_id:
                continue
            builder = getattr(module, "build_request_body", None)
            return {
                "info": info,
                "build_request_body": builder if callable(builder) else None,
            }
        except Exception:
            continue

    return None


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

        if path == "/api/motion-scripts":
            self._send_json(200, {"ok": True, "items": _load_motion_script_catalog(MOTIONS_ROOT)})
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

        if path == "/api/sensors":
            self._proxy_json("GET", "/v1/mira-light/sensors")
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

        if path.startswith("/api/run-motion-script/"):
            scene_name = unquote(path.removeprefix("/api/run-motion-script/"))
            body = self._read_json_body()
            motion_script = _load_motion_script_by_scene_id(MOTIONS_ROOT, scene_name)
            if motion_script is None:
                self._send_json(404, {"ok": False, "error": f"Motion script not found: {scene_name}"})
                return

            payload: dict
            build_request_body = motion_script.get("build_request_body")
            if build_request_body is not None:
                cue_mode = "director"
                context = None
                async_run = True
                allow_unavailable = None
                if isinstance(body, dict):
                    cue_mode = str(body.get("cueMode") or cue_mode)
                    context = body.get("context")
                    async_run = _coerce_bool(body.get("async"), True)
                    if "allowUnavailable" in body:
                        allow_unavailable = _coerce_bool(body.get("allowUnavailable"), False)
                payload = build_request_body(
                    cue_mode=cue_mode,
                    context=context,
                    async_run=async_run,
                    allow_unavailable=allow_unavailable,
                )
            else:
                payload = {
                    "scene": scene_name,
                    "async": True,
                    "cueMode": "director",
                }

            if not isinstance(payload, dict):
                self._send_json(500, {"ok": False, "error": f"Motion script payload must be a JSON object: {scene_name}"})
                return

            payload.setdefault("scene", scene_name)
            if isinstance(body, dict):
                for key, value in body.items():
                    if key == "scene":
                        continue
                    payload.setdefault(key, value)

            self._proxy_json("POST", "/v1/mira-light/run-scene", payload)
            return

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
            body = self._read_json_body()
            payload = body if isinstance(body, dict) else {}
            payload["baseUrl"] = FIXED_LAMP_BASE_URL
            self._proxy_json("POST", "/v1/mira-light/config", payload)
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

        if path == "/api/sensors":
            self._proxy_json("POST", "/v1/mira-light/sensors", self._read_json_body())
            return

        self._send_json(404, {"ok": False, "error": "Unknown endpoint"})


def resolve_bridge_token(env_name: str) -> str:
    if env_name.strip().lower() in {"disabled", "none", "off", "false", "0"}:
        return ""

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
        "--base-url",
        dest="bridge_base_url",
        default=(
            os.environ.get("MIRA_LIGHT_CONSOLE_BRIDGE_URL")
            or os.environ.get("MIRA_LIGHT_BRIDGE_URL")
            or DEFAULT_BRIDGE_URL
        ),
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
    print(f"[console] motion scripts root {MOTIONS_ROOT}")
    print(f"[console] vision bridge state path {args.vision_bridge_state_path}")
    print(f"[console] vision event path {args.vision_event_path}")
    print(f"[console] vision operator state path {args.vision_operator_state_path}")

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
