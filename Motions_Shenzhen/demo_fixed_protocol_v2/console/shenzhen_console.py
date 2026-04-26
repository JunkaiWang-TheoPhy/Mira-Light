#!/usr/bin/env python3
"""Local web console for the Shenzhen fixed-protocol Mira Light demo."""

from __future__ import annotations

import argparse
import hashlib
import copy
import errno
import json
import mimetypes
import os
from pathlib import Path
import pty
import re
import select
import shlex
import shutil
import subprocess
import tempfile
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from threading import Lock, Thread
from urllib.parse import unquote, urlparse
from uuid import uuid4


CONSOLE_DIR = Path(__file__).resolve().parent
DEMO_ROOT = CONSOLE_DIR.parent
SCRIPTS_DIR = DEMO_ROOT / "scripts"
WEB_ROOT = CONSOLE_DIR / "web"
REGISTRY_PATH = CONSOLE_DIR / "scene_registry.json"
DEFAULT_HOST = "192.168.0.183"
DEFAULT_PORT = 22
DEFAULT_USER = "root"
DEFAULT_TIMEOUT_SECONDS = 180.0
PASSWORD_ENV = "MIRA_SHENZHEN_BOARD_PASSWORD"
SSH_CONTROL_DIR = Path(os.environ.get("MIRA_SHENZHEN_SSH_CONTROL_DIR", "/tmp/mira-ssh"))
SSH_CONTROL_PERSIST_SECONDS = int(os.environ.get("MIRA_SHENZHEN_SSH_CONTROL_PERSIST_SECONDS", "600"))
SSH_CONNECT_RETRIES = int(os.environ.get("MIRA_SHENZHEN_SSH_CONNECT_RETRIES", "2"))
SSH_RETRY_DELAY_SECONDS = float(os.environ.get("MIRA_SHENZHEN_SSH_RETRY_DELAY_SECONDS", "0.15"))
SSH_LOCK = Lock()
SERVO_MIN = 0
SERVO_MAX = 4095
MANUAL_SERVO_SPEEDS = (440, 320, 320, 440)
SERVO_POSITION_SCRIPT = """set -euo pipefail
echo '== read all servo positions =='
python3 /home/sunrise/Desktop/four_servo_control.py read-pos-all
"""


def parse_servo_positions(stdout: str) -> dict[str, int]:
    positions: dict[str, int] = {}
    pattern = re.compile(r"Read ID\s*:\s*(\d+).*?Position\s*:\s*(\d+)", re.DOTALL)
    for servo_id, position in pattern.findall(stdout.replace("\r", "")):
        positions[servo_id] = int(position)
    return positions


def compact_remote_warning(result: dict) -> str | None:
    return_code = result.get("returnCode")
    if return_code == 0:
        return None
    text = str(result.get("stderr") or result.get("stdout") or f"Remote command exited {return_code}")
    for needle in (
        "timed out waiting for servo response header",
        "Timed out waiting for SSH response",
        "Timed out after",
    ):
        if needle in text:
            return needle
    first_line = next((line.strip() for line in text.replace("\r", "").splitlines() if line.strip()), "")
    if not first_line:
        return f"Remote command exited {return_code}"
    return first_line[:180]


def validate_servo_positions(raw_positions: object) -> dict[str, int]:
    if not isinstance(raw_positions, dict):
        raise ValueError("positions must be an object with keys 0, 1, 2, and 3")
    positions: dict[str, int] = {}
    for servo_id in ("0", "1", "2", "3"):
        if servo_id not in raw_positions:
            raise ValueError(f"missing servo position: {servo_id}")
        value = int(raw_positions[servo_id])
        if value < SERVO_MIN or value > SERVO_MAX:
            raise ValueError(f"servo {servo_id} position out of range: {value}")
        positions[servo_id] = value
    return positions


def render_servo_pose_script(positions: dict[str, int], speeds: tuple[int, int, int, int] = MANUAL_SERVO_SPEEDS) -> str:
    p0, p1, p2, p3 = (positions[str(index)] for index in range(4))
    s0, s1, s2, s3 = speeds
    return (
        "set -euo pipefail\n"
        "echo '== manual servo pose =='\n"
        f"python3 /home/sunrise/Desktop/four_servo_control.py pose {p0} {p1} {p2} {p3} "
        f"--speeds {s0} {s1} {s2} {s3}\n"
    )


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


def timestamp() -> str:
    return time.strftime("%Y-%m-%d %H:%M:%S")


def ssh_control_path(*, host: str, port: int, user: str) -> Path:
    digest = hashlib.sha256(f"{user}@{host}:{port}".encode("utf-8")).hexdigest()[:16]
    return SSH_CONTROL_DIR / f"cm-{digest}"


def ssh_control_options(*, host: str, port: int, user: str) -> list[str]:
    SSH_CONTROL_DIR.mkdir(mode=0o700, parents=True, exist_ok=True)
    control_path = ssh_control_path(host=host, port=port, user=user)
    return [
        "-o",
        "ControlMaster=auto",
        "-o",
        f"ControlPersist={SSH_CONTROL_PERSIST_SECONDS}s",
        "-o",
        f"ControlPath={control_path}",
    ]


def is_transient_ssh_failure(result: dict) -> bool:
    if result.get("returnCode") != 255:
        return False
    text = f"{result.get('stdout', '')}\n{result.get('stderr', '')}"
    if "Permission denied" in text or "Authentication failed" in text:
        return False
    transient_markers = (
        "Connection reset",
        "Connection closed",
        "kex_exchange_identification",
        "mux_client_request_session",
    )
    return not text.strip() or any(marker in text for marker in transient_markers)


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


def run_ssh_with_expect(command: list[str], password: str, timeout_seconds: float) -> dict:
    expect_bin = shutil.which("expect")
    if not expect_bin:
        return run_ssh_with_pty(command, password=password, timeout_seconds=timeout_seconds)

    expect_program = r"""
set timeout $env(MIRA_EXPECT_TIMEOUT)
spawn {*}$argv
expect {
  -re "(?i)are you sure you want to continue connecting" {
    send "yes\r"
    exp_continue
  }
  -re "(?i)password:" {
    send "$env(MIRA_EXPECT_PASSWORD)\r"
    exp_continue
  }
  timeout {
    puts "\nTimed out waiting for SSH response"
    exit 124
  }
  eof
}
catch wait result
exit [lindex $result 3]
"""
    env = {
        **os.environ,
        "MIRA_EXPECT_PASSWORD": password,
        "MIRA_EXPECT_TIMEOUT": str(max(1, int(timeout_seconds))),
    }
    try:
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", suffix=".expect", delete=False) as handle:
            handle.write(expect_program)
            expect_script = handle.name
        try:
            result = subprocess.run(
                [expect_bin, expect_script, *command],
                check=False,
                text=True,
                capture_output=True,
                timeout=timeout_seconds + 5.0,
                env=env,
            )
        finally:
            Path(expect_script).unlink(missing_ok=True)
    except subprocess.TimeoutExpired:
        return {"returnCode": -1, "stdout": "", "stderr": f"Timed out after {timeout_seconds:.1f}s"}

    return {
        "returnCode": result.returncode,
        "stdout": redact_password(result.stdout, password),
        "stderr": redact_password(result.stderr, password),
    }


def run_remote_script(
    *,
    script: str,
    host: str,
    port: int,
    user: str,
    password: str,
    timeout_seconds: float,
) -> dict:
    with SSH_LOCK:
        return _run_remote_script_unlocked(
            script=script,
            host=host,
            port=port,
            user=user,
            password=password,
            timeout_seconds=timeout_seconds,
        )


def _run_remote_script_unlocked(
    *,
    script: str,
    host: str,
    port: int,
    user: str,
    password: str,
    timeout_seconds: float,
) -> dict:
    remote = f"bash -lc {shlex.quote(script)}"
    control_options = ssh_control_options(host=host, port=port, user=user)
    base = [
        "ssh",
        "-o",
        "StrictHostKeyChecking=no",
        "-o",
        "ConnectTimeout=8",
        "-o",
        "NumberOfPasswordPrompts=1",
        *control_options,
        "-p",
        str(port),
        f"{user}@{host}",
        remote,
    ]
    if password:
        if ssh_control_path(host=host, port=port, user=user).exists():
            warm_command = [
                "ssh",
                "-o",
                "StrictHostKeyChecking=no",
                "-o",
                "BatchMode=yes",
                "-o",
                "ConnectTimeout=8",
                "-o",
                "NumberOfPasswordPrompts=0",
                *control_options,
                "-p",
                str(port),
                f"{user}@{host}",
                remote,
            ]
            try:
                result = run_local_command(warm_command, timeout_seconds=timeout_seconds)
            except subprocess.TimeoutExpired:
                return {"returnCode": -1, "stdout": "", "stderr": f"Timed out after {timeout_seconds:.1f}s"}
            if result.returncode != 255:
                return {
                    "returnCode": result.returncode,
                    "stdout": redact_password(result.stdout, password),
                    "stderr": redact_password(result.stderr, password),
                }
        for attempt in range(max(0, SSH_CONNECT_RETRIES) + 1):
            result = run_ssh_with_expect(base, password=password, timeout_seconds=timeout_seconds)
            if not is_transient_ssh_failure(result) or attempt >= SSH_CONNECT_RETRIES:
                return result
            time.sleep(SSH_RETRY_DELAY_SECONDS)

    command = [
        "ssh",
        "-o",
        "StrictHostKeyChecking=no",
        "-o",
        "BatchMode=yes",
        "-o",
        "ConnectTimeout=8",
        *control_options,
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
        self.queue: list[dict] = []
        self.current_job: dict | None = None
        self.worker_active = False
        self.position_refresh_running = False
        self.servo_control_running = False
        self.state = {
            "running": False,
            "current": None,
            "lastResult": None,
            "servoControl": {
                "running": False,
                "error": None,
                "updatedAt": None,
            },
            "servoPositions": {
                "values": {},
                "updatedAt": None,
                "running": False,
                "error": None,
                "host": None,
                "port": None,
                "user": None,
            },
            "queue": [],
            "history": [],
        }

    def _job_view(self, job: dict) -> dict:
        return {
            "queueId": job["queueId"],
            "kind": job["kind"],
            "itemId": job["itemId"],
            "title": job["title"],
            "status": job["status"],
            "queuedAt": job["queuedAt"],
            "startedAt": job.get("startedAt"),
            "host": job["host"],
            "port": job["port"],
            "user": job["user"],
        }

    def _current_view(self) -> dict | None:
        if self.current_job is None:
            return None
        job = self.current_job
        return {
            "kind": job["kind"],
            "id": job["itemId"],
            "queueId": job["queueId"],
            "title": job["title"],
            "host": job["host"],
            "port": job["port"],
        }

    def _refresh_queue_state_locked(self) -> None:
        queue = []
        if self.current_job is not None:
            queue.append(self._job_view(self.current_job))
        queue.extend(self._job_view(job) for job in self.queue)
        self.state["running"] = self.current_job is not None
        self.state["current"] = self._current_view()
        self.state["queue"] = queue

    def snapshot_state(self) -> dict:
        with self.lock:
            return copy.deepcopy(self.state)

    def _should_start_worker_locked(self) -> bool:
        if self.queue and not self.worker_active and not self.position_refresh_running and not self.servo_control_running:
            self.worker_active = True
            return True
        return False

    def _start_worker(self) -> None:
        Thread(target=self._queue_worker_loop, daemon=True).start()

    def enqueue_job(
        self,
        *,
        kind: str,
        item_id: str,
        title: str,
        script: str,
        host: str,
        port: int,
        user: str,
        password: str,
        timeout_seconds: float,
    ) -> dict:
        job = {
            "queueId": uuid4().hex,
            "kind": kind,
            "itemId": item_id,
            "title": title,
            "script": script,
            "host": host,
            "port": port,
            "user": user,
            "password": password,
            "timeoutSeconds": timeout_seconds,
            "status": "pending",
            "queuedAt": timestamp(),
        }
        should_start_worker = False
        with self.lock:
            self.queue.append(job)
            queued = self._job_view(job)
            self._refresh_queue_state_locked()
            should_start_worker = self._should_start_worker_locked()
        if should_start_worker:
            self._start_worker()
        return queued

    def refresh_servo_positions(
        self,
        *,
        host: str,
        port: int,
        user: str,
        password: str,
        timeout_seconds: float,
    ) -> tuple[dict | None, str | None]:
        with self.lock:
            if self.current_job is not None or self.queue or self.worker_active or self.servo_control_running:
                return None, "busy"
            if self.position_refresh_running:
                return None, "refreshing"
            previous_updated_at = self.state["servoPositions"].get("updatedAt")
            self.position_refresh_running = True
            self.state["servoPositions"] = {
                **self.state["servoPositions"],
                "running": True,
                "error": None,
                "host": host,
                "port": port,
                "user": user,
            }

        started = time.monotonic()
        payload = {
            **self.state["servoPositions"],
            "running": False,
            "error": "Servo position refresh did not complete",
            "warning": None,
            "host": host,
            "port": port,
            "user": user,
            "returnCode": -1,
            "durationSeconds": 0.0,
        }
        try:
            try:
                result = run_remote_script(
                    script=SERVO_POSITION_SCRIPT,
                    host=host,
                    port=port,
                    user=user,
                    password=password,
                    timeout_seconds=min(timeout_seconds, 20.0),
                )
            except Exception as exc:  # noqa: BLE001 - keep the dashboard alive on read failures.
                result = {"returnCode": -1, "stdout": "", "stderr": str(exc)}
            result["durationSeconds"] = round(time.monotonic() - started, 3)
            result["script"] = SERVO_POSITION_SCRIPT
            result["host"] = host
            result["port"] = port
            result["user"] = user

            values = parse_servo_positions(result.get("stdout", ""))
            warning = compact_remote_warning(result) if values else None
            error = None if values else (result.get("stderr") or result.get("stdout") or "No servo positions returned")
            payload = {
                "values": values,
                "updatedAt": timestamp() if values else previous_updated_at,
                "running": False,
                "error": error,
                "warning": warning,
                "host": host,
                "port": port,
                "user": user,
                "returnCode": result.get("returnCode"),
                "durationSeconds": result.get("durationSeconds"),
            }
        except Exception as exc:  # noqa: BLE001 - the state flag must always be released.
            payload = {
                "values": {},
                "updatedAt": previous_updated_at,
                "running": False,
                "error": str(exc),
                "warning": None,
                "host": host,
                "port": port,
                "user": user,
                "returnCode": -1,
                "durationSeconds": round(time.monotonic() - started, 3),
            }
        finally:
            should_start_worker = False
            with self.lock:
                self.position_refresh_running = False
                self.state["servoPositions"] = payload
                should_start_worker = self._should_start_worker_locked()
        if should_start_worker:
            self._start_worker()
        return payload, None

    def set_manual_servo_pose(
        self,
        *,
        positions: dict[str, int],
        host: str,
        port: int,
        user: str,
        password: str,
        timeout_seconds: float,
    ) -> tuple[dict | None, dict | None, str | None]:
        with self.lock:
            if self.current_job is not None or self.queue or self.worker_active:
                return None, None, "busy"
            if self.position_refresh_running:
                return None, None, "refreshing"
            if self.servo_control_running:
                return None, None, "controlling"
            previous_values = dict(self.state["servoPositions"].get("values", {}))
            previous_updated_at = self.state["servoPositions"].get("updatedAt")
            self.servo_control_running = True
            self.state["servoControl"] = {
                "running": True,
                "error": None,
                "updatedAt": self.state["servoControl"].get("updatedAt"),
            }

        script = render_servo_pose_script(positions)
        started = time.monotonic()
        try:
            result = run_remote_script(
                script=script,
                host=host,
                port=port,
                user=user,
                password=password,
                timeout_seconds=min(timeout_seconds, 20.0),
            )
        except Exception as exc:  # noqa: BLE001 - keep manual control errors visible.
            result = {"returnCode": -1, "stdout": "", "stderr": str(exc)}
        result["durationSeconds"] = round(time.monotonic() - started, 3)
        result["script"] = script
        result["host"] = host
        result["port"] = port
        result["user"] = user

        ok = result.get("returnCode") == 0
        error = None if ok else (result.get("stderr") or result.get("stdout") or "Manual servo command failed")
        payload = {
            "values": positions if ok else previous_values,
            "updatedAt": timestamp() if ok else previous_updated_at,
            "running": False,
            "error": error,
            "host": host,
            "port": port,
            "user": user,
            "returnCode": result.get("returnCode"),
            "durationSeconds": result.get("durationSeconds"),
        }

        should_start_worker = False
        with self.lock:
            self.servo_control_running = False
            self.state["servoControl"] = {
                "running": False,
                "error": error,
                "updatedAt": timestamp(),
            }
            self.state["servoPositions"] = payload
            should_start_worker = self._should_start_worker_locked()
        if should_start_worker:
            self._start_worker()
        return payload, result, None

    def delete_pending_job(self, queue_id: str) -> tuple[dict | None, str | None]:
        with self.lock:
            if self.current_job is not None and self.current_job["queueId"] == queue_id:
                return None, "running"
            for index, job in enumerate(self.queue):
                if job["queueId"] == queue_id:
                    removed = self.queue.pop(index)
                    removed["status"] = "removed"
                    self._refresh_queue_state_locked()
                    return self._job_view(removed), None
        return None, "not_found"

    def _record_result_locked(self, *, job: dict, result: dict) -> None:
        entry = {
            "at": timestamp(),
            "kind": job["kind"],
            "id": job["itemId"],
            "queueId": job["queueId"],
            "title": job["title"],
            "returnCode": result.get("returnCode"),
        }
        self.state["lastResult"] = {**entry, **result}
        self.state["history"] = [entry, *self.state["history"][:19]]
        if job["itemId"] == "read_positions" and result.get("returnCode") == 0:
            values = parse_servo_positions(result.get("stdout", ""))
            if values:
                self.state["servoPositions"] = {
                    "values": values,
                    "updatedAt": entry["at"],
                    "running": False,
                    "error": None,
                    "host": result.get("host"),
                    "port": result.get("port"),
                    "user": result.get("user"),
                    "returnCode": result.get("returnCode"),
                    "durationSeconds": result.get("durationSeconds"),
                }

    def _run_job(self, job: dict) -> dict:
        started = time.monotonic()
        try:
            result = run_remote_script(
                script=job["script"],
                host=job["host"],
                port=job["port"],
                user=job["user"],
                password=job["password"],
                timeout_seconds=job["timeoutSeconds"],
            )
        except Exception as exc:  # noqa: BLE001 - surface queue failures to the console.
            result = {"returnCode": -1, "stdout": "", "stderr": str(exc)}
        result["durationSeconds"] = round(time.monotonic() - started, 3)
        result["script"] = job["script"]
        result["host"] = job["host"]
        result["port"] = job["port"]
        result["user"] = job["user"]
        return result

    def _queue_error_result(self, job: dict, exc: Exception, started: float) -> dict:
        return {
            "returnCode": -1,
            "stdout": "",
            "stderr": f"Queue worker error: {type(exc).__name__}: {exc}",
            "durationSeconds": round(time.monotonic() - started, 3),
            "script": job.get("script", ""),
            "host": job.get("host"),
            "port": job.get("port"),
            "user": job.get("user"),
        }

    def _queue_worker_loop(self) -> None:
        while True:
            with self.lock:
                if not self.queue:
                    self.current_job = None
                    self.worker_active = False
                    self._refresh_queue_state_locked()
                    return
                job = self.queue.pop(0)
                job["status"] = "running"
                job["startedAt"] = timestamp()
                self.current_job = job
                self._refresh_queue_state_locked()

            started = time.monotonic()
            try:
                result = self._run_job(job)
            except Exception as exc:  # noqa: BLE001 - never leave the queue wedged on worker bugs.
                result = self._queue_error_result(job, exc, started)

            with self.lock:
                job["status"] = "done" if result.get("returnCode") == 0 else "failed"
                job["finishedAt"] = timestamp()
                self._record_result_locked(job=job, result=result)
                self.current_job = None
                self._refresh_queue_state_locked()


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

    def _enqueue_script(self, *, kind: str, item_id: str, title: str, script: str, body: dict) -> dict:
        host, port, user, password, timeout = self._connection_from_body(body)
        return self.server.enqueue_job(
            kind=kind,
            item_id=item_id,
            title=title,
            script=script,
            host=host,
            port=port,
            user=user,
            password=password,
            timeout_seconds=timeout,
        )

    def _record_result(self, *, kind: str, item_id: str, title: str, result: dict) -> None:
        entry = {
            "at": timestamp(),
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
            state = self.server.snapshot_state()
            self._send_json(200, {"ok": True, "state": state})
            return
        self._serve_static(path)

    def do_DELETE(self) -> None:  # noqa: N802
        path = urlparse(self.path).path
        if path.startswith("/api/queue/"):
            queue_id = unquote(path.removeprefix("/api/queue/"))
            removed, reason = self.server.delete_pending_job(queue_id)
            if removed is not None:
                self._send_json(200, {"ok": True, "removed": removed})
                return
            if reason == "running":
                self._send_json(409, {"ok": False, "error": "Running queue item cannot be removed"})
                return
            self._send_json(404, {"ok": False, "error": "Queue item not found"})
            return
        self._send_json(404, {"ok": False, "error": "Unknown endpoint"})

    def do_POST(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        path = parsed.path
        try:
            body = self._read_json()
        except json.JSONDecodeError as exc:
            self._send_json(400, {"ok": False, "error": f"Invalid JSON: {exc}"})
            return

        try:
            if path == "/api/servo-control":
                try:
                    positions = validate_servo_positions(body.get("positions"))
                except (TypeError, ValueError) as exc:
                    self._send_json(400, {"ok": False, "error": str(exc)})
                    return
                host, port, user, password, timeout = self._connection_from_body(body)
                servo_positions, result, reason = self.server.set_manual_servo_pose(
                    positions=positions,
                    host=host,
                    port=port,
                    user=user,
                    password=password,
                    timeout_seconds=timeout,
                )
                if servo_positions is not None:
                    status = 200 if result and result.get("returnCode") == 0 else 502
                    self._send_json(status, {"ok": status == 200, "servoPositions": servo_positions, "result": result})
                    return
                if reason == "busy":
                    self._send_json(409, {"ok": False, "error": "Action queue is busy; manual servo control paused"})
                    return
                if reason == "refreshing":
                    self._send_json(409, {"ok": False, "error": "Servo position refresh is running; retry shortly"})
                    return
                self._send_json(409, {"ok": False, "error": "Manual servo control already running"})
                return

            if path == "/api/servo-positions":
                host, port, user, password, timeout = self._connection_from_body(body)
                positions, reason = self.server.refresh_servo_positions(
                    host=host,
                    port=port,
                    user=user,
                    password=password,
                    timeout_seconds=timeout,
                )
                if positions is not None:
                    status = 200 if positions.get("error") is None else 502
                    self._send_json(status, {"ok": status == 200, "servoPositions": positions})
                    return
                if reason == "busy":
                    self._send_json(409, {"ok": False, "error": "Action queue is busy; servo position refresh paused"})
                    return
                self._send_json(409, {"ok": False, "error": "Servo position refresh already running"})
                return

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
                queued = self._enqueue_script(kind="scene", item_id=scene_id, title=scene["title"], script=script, body=body)
                self._send_json(202, {"ok": True, "queued": queued})
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
                queued = self._enqueue_script(
                    kind="quick-action",
                    item_id=action_id,
                    title=action["title"],
                    script=script,
                    body=body,
                )
                self._send_json(202, {"ok": True, "queued": queued})
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


def warm_ssh_control_master(*, host: str, port: int, user: str, password: str, timeout_seconds: float) -> None:
    if not password:
        return
    result = run_remote_script(
        script="true",
        host=host,
        port=port,
        user=user,
        password=password,
        timeout_seconds=min(timeout_seconds, 10.0),
    )
    status = "ready" if result.get("returnCode") == 0 else f"failed code={result.get('returnCode')}"
    print(f"[shenzhen-console] ssh control master warmup {status}")


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
    if password:
        Thread(
            target=warm_ssh_control_master,
            kwargs={
                "host": board_host,
                "port": board_port,
                "user": board_user,
                "password": password,
                "timeout_seconds": args.timeout_seconds,
            },
            daemon=True,
        ).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("[shenzhen-console] shutdown requested")
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
