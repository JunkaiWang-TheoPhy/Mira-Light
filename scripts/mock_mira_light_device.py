#!/usr/bin/env python3
"""Mock ESP32-style device for offline Mira Light development.

This server mirrors the raw lamp-facing HTTP contract used by
``scripts/mira_light_runtime.py`` so the higher-level runtime and bridge can be
exercised without the real lamp being online.

It supports two categories of endpoints:

- Device endpoints: ``/status``, ``/led``, ``/actions``, ``/control``,
  ``/action``, ``/action/stop``, ``/reset``.
- Admin endpoints: ``/__admin/state``, ``/__admin/requests``,
  ``/__admin/faults``, ``/__admin/reset-state``.

Fault rules are intentionally simple and designed for local rehearsals:

```json
{
  "replace": true,
  "rules": [
    {"method": "GET", "path": "/status", "mode": "http_error", "status": 503, "times": 1},
    {"method": "POST", "path": "/control", "mode": "invalid_json", "times": 1},
    {"method": "POST", "path": "/led", "mode": "timeout", "delayMs": 700, "times": 1}
  ]
}
```
"""

from __future__ import annotations

import argparse
from collections import deque
from copy import deepcopy
from dataclasses import dataclass
from datetime import datetime, timezone
import json
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from scenes import POSES


DEFAULT_ACTIONS = [
    {"name": "dance", "label": "Dance", "loopsSupported": True},
    {"name": "wiggle", "label": "Wiggle", "loopsSupported": True},
    {"name": "wave", "label": "Wave", "loopsSupported": False},
]


def now_iso() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


@dataclass
class FaultRule:
    method: str
    path: str
    mode: str
    status: int = 500
    delay_ms: int = 0
    times: int | None = 1
    body: Any = None
    content_type: str = "application/json; charset=utf-8"

    @classmethod
    def from_payload(cls, payload: dict[str, Any]) -> "FaultRule":
        method = str(payload.get("method", "GET")).upper()
        path = str(payload.get("path", "/"))
        mode = str(payload.get("mode", "")).strip().lower()
        if mode not in {"http_error", "invalid_json", "timeout", "disconnect", "delay"}:
            raise ValueError(f"Unsupported fault mode: {mode}")

        times_raw = payload.get("times", 1)
        if times_raw is None:
            times = None
        else:
            times = int(times_raw)
            if times <= 0:
                raise ValueError("times must be positive when provided")

        default_status = 200 if mode == "invalid_json" else 500
        return cls(
            method=method,
            path=path,
            mode=mode,
            status=int(payload.get("status", default_status)),
            delay_ms=int(payload.get("delayMs", 0)),
            times=times,
            body=payload.get("body"),
            content_type=str(payload.get("contentType", "application/json; charset=utf-8")),
        )

    def matches(self, method: str, path: str) -> bool:
        return self.method == method.upper() and self.path == path

    def as_dict(self) -> dict[str, Any]:
        return {
            "method": self.method,
            "path": self.path,
            "mode": self.mode,
            "status": self.status,
            "delayMs": self.delay_ms,
            "times": self.times,
            "body": self.body,
            "contentType": self.content_type,
        }


class MockDeviceState:
    def __init__(
        self,
        *,
        request_log_path: Path | None = None,
        state_dump_path: Path | None = None,
        request_log_limit: int = 400,
    ) -> None:
        self.request_log_path = request_log_path
        self.state_dump_path = state_dump_path
        self.request_log_limit = request_log_limit

        self._lock = threading.Lock()
        self._booted_at = now_iso()
        self._request_counter = 0
        self._requests: deque[dict[str, Any]] = deque(maxlen=request_log_limit)
        self._fault_rules: list[FaultRule] = []

        self._default_servos = deepcopy(POSES["neutral"]["angles"])
        self._default_led = {"mode": "off", "brightness": 0}
        self._default_actions = deepcopy(DEFAULT_ACTIONS)

        self._servos = deepcopy(self._default_servos)
        self._led_state = deepcopy(self._default_led)
        self._action_state = {
            "running": False,
            "name": None,
            "payload": None,
            "startedAt": None,
            "stoppedAt": None,
        }
        self._last_reset_at = now_iso()
        self._persist_state()

    def _persist_state(self) -> None:
        if self.state_dump_path is None:
            return
        self.state_dump_path.parent.mkdir(parents=True, exist_ok=True)
        self.state_dump_path.write_text(
            json.dumps(self.snapshot(), ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )

    def _append_request_log(self, record: dict[str, Any]) -> None:
        if self.request_log_path is None:
            return
        self.request_log_path.parent.mkdir(parents=True, exist_ok=True)
        with self.request_log_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")

    def snapshot(self) -> dict[str, Any]:
        with self._lock:
            return {
                "service": "mock-mira-light-device",
                "bootedAt": self._booted_at,
                "requestCount": self._request_counter,
                "lastResetAt": self._last_reset_at,
                "servos": deepcopy(self._servos),
                "led": deepcopy(self._led_state),
                "actions": {
                    "available": deepcopy(self._default_actions),
                    "active": deepcopy(self._action_state),
                },
                "faults": [rule.as_dict() for rule in self._fault_rules],
                "recentRequests": list(self._requests),
            }

    def status_payload(self) -> dict[str, Any]:
        with self._lock:
            return {
                "ok": True,
                "device": "mock-mira-light-device",
                "online": True,
                "bootedAt": self._booted_at,
                "lastResetAt": self._last_reset_at,
                "servos": deepcopy(self._servos),
                "activeAction": deepcopy(self._action_state),
                "requestCount": self._request_counter,
            }

    def led_payload(self) -> dict[str, Any]:
        with self._lock:
            return deepcopy(self._led_state)

    def actions_payload(self) -> dict[str, Any]:
        with self._lock:
            return {
                "available": deepcopy(self._default_actions),
                "active": deepcopy(self._action_state),
            }

    def record_request(
        self,
        *,
        method: str,
        path: str,
        payload: Any,
        response_status: int | None,
        outcome: str,
        fault_mode: str | None = None,
    ) -> None:
        record = {
            "ts": now_iso(),
            "method": method,
            "path": path,
            "payload": payload,
            "responseStatus": response_status,
            "outcome": outcome,
            "faultMode": fault_mode,
        }
        with self._lock:
            self._request_counter += 1
            record["seq"] = self._request_counter
            self._requests.append(record)
        self._append_request_log(record)
        self._persist_state()

    def reset_state(self, *, clear_requests: bool, clear_faults: bool) -> None:
        with self._lock:
            self._servos = deepcopy(self._default_servos)
            self._led_state = deepcopy(self._default_led)
            self._action_state = {
                "running": False,
                "name": None,
                "payload": None,
                "startedAt": None,
                "stoppedAt": now_iso(),
            }
            self._last_reset_at = now_iso()
            if clear_requests:
                self._requests.clear()
                self._request_counter = 0
            if clear_faults:
                self._fault_rules = []
        self._persist_state()

    def set_fault_rules(self, rules: list[dict[str, Any]], *, replace: bool) -> list[dict[str, Any]]:
        parsed = [FaultRule.from_payload(rule) for rule in rules]
        with self._lock:
            if replace:
                self._fault_rules = parsed
            else:
                self._fault_rules.extend(parsed)
            active = [rule.as_dict() for rule in self._fault_rules]
        self._persist_state()
        return active

    def current_fault_rules(self) -> list[dict[str, Any]]:
        with self._lock:
            return [rule.as_dict() for rule in self._fault_rules]

    def consume_matching_fault(self, method: str, path: str) -> FaultRule | None:
        should_persist = False
        with self._lock:
            for index, rule in enumerate(self._fault_rules):
                if not rule.matches(method, path):
                    continue
                chosen = deepcopy(rule)
                if rule.times is not None:
                    rule.times -= 1
                    if rule.times <= 0:
                        self._fault_rules.pop(index)
                    should_persist = True
                elif rule.mode:
                    should_persist = True
                break
            else:
                return None
        if should_persist:
            self._persist_state()
        return chosen

    def apply_control(self, payload: dict[str, Any]) -> dict[str, Any]:
        mode = str(payload.get("mode", ""))
        if mode not in {"absolute", "relative"}:
            raise ValueError("mode must be absolute or relative")

        changed = {}
        with self._lock:
            for key, value in payload.items():
                if key == "mode":
                    continue
                if key not in self._servos:
                    raise ValueError(f"Unsupported servo field: {key}")
                int_value = int(value)
                if mode == "absolute":
                    self._servos[key] = int_value
                else:
                    self._servos[key] += int_value
                changed[key] = self._servos[key]
            response = {
                "ok": True,
                "mode": mode,
                "applied": deepcopy(payload),
                "servos": deepcopy(self._servos),
                "changed": changed,
            }
        self._persist_state()
        return response

    def apply_led(self, payload: dict[str, Any]) -> dict[str, Any]:
        with self._lock:
            self._led_state = deepcopy(payload)
            response = {
                "ok": True,
                "applied": deepcopy(payload),
                "led": deepcopy(self._led_state),
            }
        self._persist_state()
        return response

    def start_action(self, payload: dict[str, Any]) -> dict[str, Any]:
        action_name = str(payload.get("name", "")).strip()
        if not action_name:
            raise ValueError("name is required")
        with self._lock:
            self._action_state = {
                "running": True,
                "name": action_name,
                "payload": deepcopy(payload),
                "startedAt": now_iso(),
                "stoppedAt": None,
            }
            response = {
                "ok": True,
                "action": deepcopy(self._action_state),
            }
        self._persist_state()
        return response

    def stop_action(self) -> dict[str, Any]:
        with self._lock:
            self._action_state["running"] = False
            self._action_state["stoppedAt"] = now_iso()
            response = {"ok": True, "action": deepcopy(self._action_state)}
        self._persist_state()
        return response


class MockDeviceHTTPServer(ThreadingHTTPServer):
    def __init__(
        self,
        server_address: tuple[str, int],
        handler_class: type[BaseHTTPRequestHandler],
        *,
        state: MockDeviceState,
    ) -> None:
        super().__init__(server_address, handler_class)
        self.state = state


class MockDeviceHandler(BaseHTTPRequestHandler):
    server: MockDeviceHTTPServer

    def log_message(self, format: str, *args) -> None:  # noqa: A003
        print(f"[mock-device] {self.address_string()} - {format % args}")

    def _send_json(self, status_code: int, payload: dict[str, Any]) -> None:
        self._send_bytes(
            status_code,
            json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8"),
            content_type="application/json; charset=utf-8",
        )

    def _send_bytes(self, status_code: int, body: bytes, *, content_type: str) -> None:
        self.send_response(status_code)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _read_json_body(self) -> dict[str, Any]:
        length = int(self.headers.get("Content-Length", "0") or 0)
        if length <= 0:
            return {}
        raw = self.rfile.read(length).decode("utf-8")
        if not raw.strip():
            return {}
        parsed = json.loads(raw)
        if not isinstance(parsed, dict):
            raise ValueError("JSON body must be an object")
        return parsed

    def _apply_fault(self, method: str, path: str, payload: dict[str, Any] | None) -> bool:
        fault = self.server.state.consume_matching_fault(method, path)
        if fault is None:
            return False

        if fault.mode == "delay":
            time.sleep(fault.delay_ms / 1000.0)
            return False

        if fault.mode == "timeout":
            time.sleep(fault.delay_ms / 1000.0)
            self.server.state.record_request(
                method=method,
                path=path,
                payload=payload,
                response_status=None,
                outcome="fault-timeout",
                fault_mode=fault.mode,
            )
            self.close_connection = True
            return True

        if fault.mode == "disconnect":
            self.server.state.record_request(
                method=method,
                path=path,
                payload=payload,
                response_status=None,
                outcome="fault-disconnect",
                fault_mode=fault.mode,
            )
            self.close_connection = True
            return True

        if fault.mode == "invalid_json":
            body = fault.body if fault.body is not None else "{invalid-json"
            if isinstance(body, str):
                encoded = body.encode("utf-8")
            else:
                encoded = json.dumps(body, ensure_ascii=False).encode("utf-8")
            self._send_bytes(fault.status or 200, encoded, content_type=fault.content_type)
            self.server.state.record_request(
                method=method,
                path=path,
                payload=payload,
                response_status=fault.status or 200,
                outcome="fault-invalid-json",
                fault_mode=fault.mode,
            )
            return True

        if fault.mode == "http_error":
            body = fault.body
            if not isinstance(body, dict):
                body = {
                    "ok": False,
                    "error": "Injected mock device fault",
                    "faultMode": fault.mode,
                }
            self._send_json(fault.status, body)
            self.server.state.record_request(
                method=method,
                path=path,
                payload=payload,
                response_status=fault.status,
                outcome="fault-http-error",
                fault_mode=fault.mode,
            )
            return True

        return False

    def do_GET(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        path = parsed.path
        if self._apply_fault("GET", path, None):
            return

        try:
            if path == "/health":
                payload = self.server.state.snapshot()
                payload["ok"] = True
                self._send_json(200, payload)
                self.server.state.record_request(
                    method="GET",
                    path=path,
                    payload=None,
                    response_status=200,
                    outcome="ok",
                )
                return

            if path == "/status":
                self._send_json(200, self.server.state.status_payload())
                self.server.state.record_request(
                    method="GET",
                    path=path,
                    payload=None,
                    response_status=200,
                    outcome="ok",
                )
                return

            if path == "/led":
                self._send_json(200, self.server.state.led_payload())
                self.server.state.record_request(
                    method="GET",
                    path=path,
                    payload=None,
                    response_status=200,
                    outcome="ok",
                )
                return

            if path == "/actions":
                self._send_json(200, self.server.state.actions_payload())
                self.server.state.record_request(
                    method="GET",
                    path=path,
                    payload=None,
                    response_status=200,
                    outcome="ok",
                )
                return

            if path == "/__admin/state":
                self._send_json(200, self.server.state.snapshot())
                return

            if path == "/__admin/requests":
                self._send_json(200, {"items": self.server.state.snapshot()["recentRequests"]})
                return

            if path == "/__admin/faults":
                self._send_json(200, {"rules": self.server.state.current_fault_rules()})
                return

            self._send_json(404, {"ok": False, "error": "Unknown endpoint"})
            self.server.state.record_request(
                method="GET",
                path=path,
                payload=None,
                response_status=404,
                outcome="not-found",
            )
        except Exception as exc:  # noqa: BLE001
            self._send_json(500, {"ok": False, "error": str(exc)})
            self.server.state.record_request(
                method="GET",
                path=path,
                payload=None,
                response_status=500,
                outcome="exception",
            )

    def do_POST(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        path = parsed.path

        try:
            body = self._read_json_body()
        except Exception as exc:  # noqa: BLE001
            self._send_json(400, {"ok": False, "error": f"Invalid JSON: {exc}"})
            self.server.state.record_request(
                method="POST",
                path=path,
                payload=None,
                response_status=400,
                outcome="invalid-json",
            )
            return

        if self._apply_fault("POST", path, body):
            return

        try:
            if path == "/control":
                response = self.server.state.apply_control(body)
                self._send_json(200, response)
                self.server.state.record_request(
                    method="POST",
                    path=path,
                    payload=body,
                    response_status=200,
                    outcome="ok",
                )
                return

            if path == "/led":
                response = self.server.state.apply_led(body)
                self._send_json(200, response)
                self.server.state.record_request(
                    method="POST",
                    path=path,
                    payload=body,
                    response_status=200,
                    outcome="ok",
                )
                return

            if path == "/action":
                response = self.server.state.start_action(body)
                self._send_json(200, response)
                self.server.state.record_request(
                    method="POST",
                    path=path,
                    payload=body,
                    response_status=200,
                    outcome="ok",
                )
                return

            if path == "/action/stop":
                response = self.server.state.stop_action()
                self._send_json(200, response)
                self.server.state.record_request(
                    method="POST",
                    path=path,
                    payload=body,
                    response_status=200,
                    outcome="ok",
                )
                return

            if path == "/reset":
                self.server.state.reset_state(clear_requests=False, clear_faults=False)
                response = {"ok": True, "status": self.server.state.status_payload()}
                self._send_json(200, response)
                self.server.state.record_request(
                    method="POST",
                    path=path,
                    payload=body,
                    response_status=200,
                    outcome="ok",
                )
                return

            if path == "/__admin/faults":
                rules = body.get("rules", [])
                if not isinstance(rules, list):
                    raise ValueError("rules must be a list")
                active = self.server.state.set_fault_rules(rules, replace=bool(body.get("replace", True)))
                self._send_json(200, {"ok": True, "rules": active})
                return

            if path == "/__admin/reset-state":
                self.server.state.reset_state(
                    clear_requests=bool(body.get("clearRequests", False)),
                    clear_faults=bool(body.get("clearFaults", False)),
                )
                self._send_json(200, {"ok": True, "state": self.server.state.snapshot()})
                return

            self._send_json(404, {"ok": False, "error": "Unknown endpoint"})
            self.server.state.record_request(
                method="POST",
                path=path,
                payload=body,
                response_status=404,
                outcome="not-found",
            )
        except ValueError as exc:
            self._send_json(400, {"ok": False, "error": str(exc)})
            self.server.state.record_request(
                method="POST",
                path=path,
                payload=body,
                response_status=400,
                outcome="validation-error",
            )
        except Exception as exc:  # noqa: BLE001
            self._send_json(500, {"ok": False, "error": str(exc)})
            self.server.state.record_request(
                method="POST",
                path=path,
                payload=body,
                response_status=500,
                outcome="exception",
            )


def create_server(
    host: str,
    port: int,
    *,
    request_log_path: Path | None = None,
    state_dump_path: Path | None = None,
) -> MockDeviceHTTPServer:
    state = MockDeviceState(request_log_path=request_log_path, state_dump_path=state_dump_path)
    return MockDeviceHTTPServer((host, port), MockDeviceHandler, state=state)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the local mock Mira Light device.")
    parser.add_argument("--host", default="127.0.0.1", help="Listen host.")
    parser.add_argument("--port", type=int, default=9799, help="Listen port.")
    parser.add_argument(
        "--request-log-out",
        type=Path,
        help="Optional JSONL file to append request records.",
    )
    parser.add_argument(
        "--state-out",
        type=Path,
        help="Optional JSON file to keep the latest state snapshot.",
    )
    parser.add_argument(
        "--fault-file",
        type=Path,
        help="Optional JSON file with the same payload accepted by /__admin/faults.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    server = create_server(
        args.host,
        args.port,
        request_log_path=args.request_log_out.expanduser().resolve() if args.request_log_out else None,
        state_dump_path=args.state_out.expanduser().resolve() if args.state_out else None,
    )

    if args.fault_file:
        payload = json.loads(args.fault_file.expanduser().resolve().read_text(encoding="utf-8"))
        rules = payload.get("rules", payload)
        if not isinstance(rules, list):
            raise SystemExit("fault file must contain a rules list or be a rules list")
        server.state.set_fault_rules(rules, replace=True)

    host, port = server.server_address
    print(f"[mock-device] listening at http://{host}:{port}")
    if args.request_log_out:
        print(f"[mock-device] request log: {args.request_log_out}")
    if args.state_out:
        print(f"[mock-device] state snapshot: {args.state_out}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("[mock-device] shutdown requested")
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
