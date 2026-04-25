#!/usr/bin/env python3
"""Local web console for the Shenzhen fixed-protocol Mira Light demo."""

from __future__ import annotations

import argparse
import errno
import json
import mimetypes
import os
from pathlib import Path
import pty
import select
import shlex
import subprocess
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from threading import Lock
from urllib.parse import unquote, urlparse


CONSOLE_DIR = Path(__file__).resolve().parent
DEMO_ROOT = CONSOLE_DIR.parent
SCRIPTS_DIR = DEMO_ROOT / "scripts"
WEB_ROOT = CONSOLE_DIR / "web"
REGISTRY_PATH = CONSOLE_DIR / "scene_registry.json"
DEFAULT_HOST = "82.157.174.100"
DEFAULT_PORT = 6000
DEFAULT_USER = "root"
DEFAULT_TIMEOUT_SECONDS = 180.0
PASSWORD_ENV = "MIRA_SHENZHEN_BOARD_PASSWORD"


def load_registry(path: Path = REGISTRY_PATH) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def render_remote_script(steps: list[dict]) -> str:
    lines = ["set -euo pipefail"]
    for step in steps:
        label = str(step["label"])
        command = str(step["command"])
        lines.append(f"echo '== {label} =='")
        lines.append(command)
    return "\n".join(lines) + "\n"


def parse_extra_args(raw: object) -> list[str]:
    if raw in (None, "", False):
        return []
    if isinstance(raw, list):
        return [str(item) for item in raw if str(item).strip()]
    if isinstance(raw, str):
        return shlex.split(raw)
    raise ValueError("extraArgs must be a string or list")


def redact_password(text: str, password: str) -> str:
    if not password:
        return text
    return text.replace(password, "***")


def run_local_command(command: list[str], timeout_seconds: float) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        check=False,
        text=True,
        capture_output=True,
        timeout=timeout_seconds,
    )


def run_ssh_with_pty(command: list[str], password: str, timeout_seconds: float) -> dict:
    master_fd, slave_fd = pty.openpty()
    started = time.monotonic()
    output_chunks: list[str] = []
    process = subprocess.Popen(
        command,
        stdin=slave_fd,
        stdout=slave_fd,
        stderr=slave_fd,
        text=False,
        close_fds=True,
    )
    os.close(slave_fd)
    password_sent = False
    try:
        while True:
            if time.monotonic() - started > timeout_seconds:
                process.kill()
                return {
                    "returnCode": -1,
                    "stdout": redact_password("".join(output_chunks), password),
                    "stderr": f"Timed out after {timeout_seconds:.1f}s",
                }

            ready, _, _ = select.select([master_fd], [], [], 0.1)
            if master_fd in ready:
                try:
                    chunk = os.read(master_fd, 4096)
                except OSError as exc:
                    if exc.errno != errno.EIO:
                        raise
                    chunk = b""
                if chunk:
                    text = chunk.decode("utf-8", errors="replace")
                    output_chunks.append(text)
                    if not password_sent and "password:" in text.lower():
                        os.write(master_fd, (password + "\n").encode("utf-8"))
                        password_sent = True
                elif process.poll() is not None:
                    break

            if process.poll() is not None and not ready:
                break
    finally:
        os.close(master_fd)

    stdout = redact_password("".join(output_chunks), password)
    return {"returnCode": process.returncode, "stdout": stdout, "stderr": ""}


def run_remote_script(
    *,
    script: str,
    host: str,
    port: int,
    user: str,
    password: str,
    timeout_seconds: float,
) -> dict:
    remote = f"bash -lc {shlex.quote(script)}"
    base = ["ssh", "-o", "StrictHostKeyChecking=no", "-p", str(port), f"{user}@{host}", remote]
    if password:
        return run_ssh_with_pty(base, password=password, timeout_seconds=timeout_seconds)

    command = [
        "ssh",
        "-o",
        "StrictHostKeyChecking=no",
        "-o",
        "BatchMode=yes",
        "-p",
        str(port),
        f"{user}@{host}",
        remote,
    ]
    try:
        result = run_local_command(command, timeout_seconds=timeout_seconds)
    except subprocess.TimeoutExpired:
        return {"returnCode": -1, "stdout": "", "stderr": f"Timed out after {timeout_seconds:.1f}s"}
    return {"returnCode": result.returncode, "stdout": result.stdout, "stderr": result.stderr}


class ShenzhenConsoleServer(ThreadingHTTPServer):
    def __init__(
        self,
        server_address,
        handler_class,
        *,
        registry: dict,
        host: str,
        board_port: int,
        user: str,
        timeout_seconds: float,
        password: str,
    ):
        super().__init__(server_address, handler_class)
        self.registry = registry
        self.board_host = host
        self.board_port = board_port
        self.board_user = user
        self.timeout_seconds = timeout_seconds
        self.password = password
        self.lock = Lock()
        self.state = {
            "running": False,
            "current": None,
            "lastResult": None,
            "history": [],
        }


class ShenzhenConsoleHandler(BaseHTTPRequestHandler):
    server: ShenzhenConsoleServer

    def log_message(self, format: str, *args) -> None:  # noqa: A003
        print(f"[shenzhen-console] {self.address_string()} - {format % args}")

    def _send_json(self, status_code: int, payload: dict) -> None:
        body = json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _read_json(self) -> dict:
        length = int(self.headers.get("Content-Length", "0") or 0)
        if length <= 0:
            return {}
        raw = self.rfile.read(length).decode("utf-8")
        return json.loads(raw) if raw.strip() else {}

    def _serve_static(self, raw_path: str) -> None:
        path = raw_path or "/"
        if path == "/":
            path = "/index.html"
        target = (WEB_ROOT / path.lstrip("/")).resolve()
        try:
            target.relative_to(WEB_ROOT.resolve())
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

    def _scene_by_id(self, scene_id: str) -> dict | None:
        return next((scene for scene in self.server.registry["scenes"] if scene["id"] == scene_id), None)

    def _quick_action_by_id(self, action_id: str) -> dict | None:
        return next((action for action in self.server.registry["quickActions"] if action["id"] == action_id), None)

    def _scene_script_path(self, scene: dict) -> Path:
        target = (SCRIPTS_DIR / scene["script"]).resolve()
        target.relative_to(SCRIPTS_DIR.resolve())
        if not target.is_file():
            raise FileNotFoundError(f"Scene script not found: {scene['script']}")
        return target

    def _build_scene_script(self, scene: dict, body: dict) -> str:
        script_path = self._scene_script_path(scene)
        command = [
            os.environ.get("PYTHON", "python3"),
            str(script_path),
            *[str(item) for item in scene.get("defaultArgs", [])],
            *parse_extra_args(body.get("extraArgs")),
        ]
        try:
            result = run_local_command(command, timeout_seconds=20.0)
        except subprocess.TimeoutExpired as exc:
            raise RuntimeError(f"Timed out while rendering scene script: {exc}") from exc
        if result.returncode != 0:
            raise RuntimeError(result.stderr.strip() or result.stdout.strip() or "Scene script failed")
        return result.stdout

    def _connection_from_body(self, body: dict) -> tuple[str, int, str, str, float]:
        host = str(body.get("host") or self.server.board_host)
        port = int(body.get("port") or self.server.board_port)
        user = str(body.get("user") or self.server.board_user)
        password = str(body.get("password") or self.server.password or "")
        timeout = float(body.get("timeoutSeconds") or self.server.timeout_seconds)
        return host, port, user, password, timeout

    def _record_result(self, *, kind: str, item_id: str, title: str, result: dict) -> None:
        entry = {
            "at": time.strftime("%Y-%m-%d %H:%M:%S"),
            "kind": kind,
            "id": item_id,
            "title": title,
            "returnCode": result.get("returnCode"),
        }
        with self.server.lock:
            self.server.state["running"] = False
            self.server.state["current"] = None
            self.server.state["lastResult"] = {**entry, **result}
            self.server.state["history"] = [entry, *self.server.state["history"][:19]]

    def _execute_script(self, *, kind: str, item_id: str, title: str, script: str, body: dict) -> dict:
        host, port, user, password, timeout = self._connection_from_body(body)
        with self.server.lock:
            self.server.state["running"] = True
            self.server.state["current"] = {"kind": kind, "id": item_id, "title": title, "host": host, "port": port}
        started = time.monotonic()
        result = run_remote_script(
            script=script,
            host=host,
            port=port,
            user=user,
            password=password,
            timeout_seconds=timeout,
        )
        result["durationSeconds"] = round(time.monotonic() - started, 3)
        result["script"] = script
        result["host"] = host
        result["port"] = port
        result["user"] = user
        self._record_result(kind=kind, item_id=item_id, title=title, result=result)
        return result

    def do_GET(self) -> None:  # noqa: N802
        path = urlparse(self.path).path
        if path == "/api/scenes":
            self._send_json(
                200,
                {
                    "ok": True,
                    "registry": self.server.registry,
                    "defaults": {
                        "host": self.server.board_host,
                        "port": self.server.board_port,
                        "user": self.server.board_user,
                    },
                    "passwordConfigured": bool(self.server.password),
                },
            )
            return
        if path == "/api/state":
            with self.server.lock:
                state = dict(self.server.state)
            self._send_json(200, {"ok": True, "state": state})
            return
        self._serve_static(path)

    def do_POST(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        path = parsed.path
        try:
            body = self._read_json()
        except json.JSONDecodeError as exc:
            self._send_json(400, {"ok": False, "error": f"Invalid JSON: {exc}"})
            return

        try:
            if path.startswith("/api/preview/"):
                scene_id = unquote(path.removeprefix("/api/preview/"))
                scene = self._scene_by_id(scene_id)
                if scene is None:
                    self._send_json(404, {"ok": False, "error": "Unknown scene"})
                    return
                script = self._build_scene_script(scene, body)
                self._send_json(200, {"ok": True, "scene": scene, "script": script})
                return

            if path.startswith("/api/run/"):
                scene_id = unquote(path.removeprefix("/api/run/"))
                scene = self._scene_by_id(scene_id)
                if scene is None:
                    self._send_json(404, {"ok": False, "error": "Unknown scene"})
                    return
                script = self._build_scene_script(scene, body)
                result = self._execute_script(kind="scene", item_id=scene_id, title=scene["title"], script=script, body=body)
                self._send_json(200 if result["returnCode"] == 0 else 502, {"ok": result["returnCode"] == 0, "result": result})
                return

            if path.startswith("/api/quick-action/"):
                action_id = unquote(path.removeprefix("/api/quick-action/"))
                action = self._quick_action_by_id(action_id)
                if action is None:
                    self._send_json(404, {"ok": False, "error": "Unknown quick action"})
                    return
                script = render_remote_script(action["commands"])
                if body.get("preview", False):
                    self._send_json(200, {"ok": True, "action": action, "script": script})
                    return
                result = self._execute_script(
                    kind="quick-action",
                    item_id=action_id,
                    title=action["title"],
                    script=script,
                    body=body,
                )
                self._send_json(200 if result["returnCode"] == 0 else 502, {"ok": result["returnCode"] == 0, "result": result})
                return
        except Exception as exc:
            with self.server.lock:
                self.server.state["running"] = False
                self.server.state["current"] = None
            self._send_json(500, {"ok": False, "error": str(exc)})
            return

        self._send_json(404, {"ok": False, "error": "Unknown endpoint"})


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run the Shenzhen fixed-protocol Mira Light demo console.")
    parser.add_argument("--host", default="127.0.0.1", help="HTTP bind host")
    parser.add_argument("--port", default=8777, type=int, help="HTTP bind port")
    parser.add_argument("--board-host", default=os.environ.get("MIRA_SHENZHEN_BOARD_HOST", DEFAULT_HOST))
    parser.add_argument("--board-port", default=int(os.environ.get("MIRA_SHENZHEN_BOARD_PORT", DEFAULT_PORT)), type=int)
    parser.add_argument("--board-user", default=os.environ.get("MIRA_SHENZHEN_BOARD_USER", DEFAULT_USER))
    parser.add_argument("--timeout-seconds", default=DEFAULT_TIMEOUT_SECONDS, type=float)
    parser.add_argument("--password-env", default=PASSWORD_ENV)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    password = os.environ.get(args.password_env, "")
    registry = load_registry()
    defaults = registry.get("boardDefaults", {})
    board_host = args.board_host or defaults.get("host", DEFAULT_HOST)
    board_port = args.board_port or defaults.get("port", DEFAULT_PORT)
    board_user = args.board_user or defaults.get("user", DEFAULT_USER)
    print(f"[shenzhen-console] open http://{args.host}:{args.port}")
    print(f"[shenzhen-console] board ssh {board_user}@{board_host}:{board_port}")
    print(f"[shenzhen-console] password env {args.password_env} configured={bool(password)}")
    server = ShenzhenConsoleServer(
        (args.host, args.port),
        ShenzhenConsoleHandler,
        registry=registry,
        host=board_host,
        board_port=board_port,
        user=board_user,
        timeout_seconds=args.timeout_seconds,
        password=password,
    )
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("[shenzhen-console] shutdown requested")
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
