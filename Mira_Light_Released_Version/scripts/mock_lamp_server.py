#!/usr/bin/env python3
"""Mock Mira Light device server for local rehearsal without physical hardware.

This server emulates the current ESP32 HTTP surface:

- GET /status
- POST /control
- POST /reset
- GET /led
- POST /led
- GET /actions
- POST /action
- POST /action/stop

It is intentionally stateful so bridge/runtime/director-console flows can be
rehearsed against something closer to a real lamp than plain dry-run mode.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass, field
from datetime import datetime, timezone
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from threading import Event, Lock, Thread
import time
from typing import Any

from mira_light_signal_contract import (
    DEFAULT_LED_PIXEL_COUNT,
    HEAD_CAPACITIVE_FIELD,
    VALID_LED_MODES,
    build_led_status_payload,
    coerce_int,
    make_uniform_pixels,
    normalize_binary_signal,
    normalize_rgb_triplet,
    normalize_vector_pixels,
    off_pixels,
)


DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 9791
DEFAULT_LED_COUNT = DEFAULT_LED_PIXEL_COUNT
DEFAULT_LED_PIN = 2
SERVO_LAYOUT = [
    {"id": 1, "name": "servo1", "pin": 18},
    {"id": 2, "name": "servo2", "pin": 13},
    {"id": 3, "name": "servo3", "pin": 14},
    {"id": 4, "name": "servo4", "pin": 15},
]
AVAILABLE_ACTIONS = [
    {"name": "nod", "frames": 5},
    {"name": "shake", "frames": 5},
    {"name": "wave", "frames": 7},
    {"name": "dance", "frames": 12},
    {"name": "stretch", "frames": 5},
    {"name": "curious", "frames": 8},
]


def now_iso() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def clamp_angle(value: int) -> int:
    return max(0, min(180, value))


@dataclass
class MockLampState:
    led_count: int = DEFAULT_LED_COUNT
    servos: dict[str, int] = field(default_factory=lambda: {item["name"]: 90 for item in SERVO_LAYOUT})
    led_mode: str = "solid"
    brightness: int = 128
    color: dict[str, int] = field(default_factory=lambda: {"r": 255, "g": 255, "b": 255})
    pixels: list[dict[str, int]] = field(default_factory=list)
    head_capacitive: int = 0
    playing: bool = False
    current_action: str | None = None
    current_action_loops: int = 0
    last_command_at: str | None = None
    last_action_started_at: str | None = None

    def __post_init__(self) -> None:
        if not self.pixels:
            self.pixels = make_uniform_pixels(
                count=self.led_count,
                color=self.color,
                brightness=self.brightness,
            )

    def sensors_payload(self) -> dict[str, int]:
        return {HEAD_CAPACITIVE_FIELD: self.head_capacitive}

    def status_payload(self) -> dict[str, Any]:
        return {
            "servos": [
                {
                    "id": meta["id"],
                    "name": meta["name"],
                    "angle": self.servos[meta["name"]],
                    "pin": meta["pin"],
                }
                for meta in SERVO_LAYOUT
            ],
            "sensors": self.sensors_payload(),
            "led": self.led_payload(),
        }

    def led_payload(self) -> dict[str, Any]:
        return build_led_status_payload(
            mode=self.led_mode,
            brightness=self.brightness,
            color=self.color,
            pixels=self.pixels,
            led_count=self.led_count,
            pin=DEFAULT_LED_PIN,
        )

    def actions_payload(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "playing": self.playing,
            "available": AVAILABLE_ACTIONS,
        }
        if self.current_action:
            payload["currentAction"] = {
                "name": self.current_action,
                "loops": self.current_action_loops,
                "startedAt": self.last_action_started_at,
            }
        return payload


class MockLampController:
    def __init__(self, *, led_count: int):
        self._lock = Lock()
        self._action_stop = Event()
        self._action_thread: Thread | None = None
        self.state = MockLampState(led_count=led_count)

    def snapshot(self) -> dict[str, Any]:
        with self._lock:
            return {
                "status": self.state.status_payload(),
                "led": self.state.led_payload(),
                "actions": self.state.actions_payload(),
                "lastCommandAt": self.state.last_command_at,
            }

    def get_status(self) -> dict[str, Any]:
        with self._lock:
            return self.state.status_payload()

    def get_led(self) -> dict[str, Any]:
        with self._lock:
            return self.state.led_payload()

    def get_actions(self) -> dict[str, Any]:
        with self._lock:
            return self.state.actions_payload()

    def get_sensors(self) -> dict[str, Any]:
        with self._lock:
            return self.state.sensors_payload()

    def _rebuild_uniform_pixels(self, *, off: bool = False) -> None:
        if off:
            self.state.pixels = off_pixels(count=self.state.led_count)
            return
        self.state.pixels = make_uniform_pixels(
            count=self.state.led_count,
            color=self.state.color,
            brightness=self.state.brightness,
        )

    def apply_control(self, payload: dict[str, Any]) -> dict[str, Any]:
        mode = payload.get("mode", "relative")
        if mode not in {"absolute", "relative"}:
            raise ValueError("mode must be absolute or relative")

        updates = 0
        with self._lock:
            for servo_name in ("servo1", "servo2", "servo3", "servo4"):
                if servo_name not in payload:
                    continue
                value = coerce_int(payload[servo_name], field_name=servo_name)
                current = self.state.servos[servo_name]
                target = value if mode == "absolute" else current + value
                self.state.servos[servo_name] = clamp_angle(target)
                updates += 1

            if updates == 0:
                raise ValueError("At least one servo field is required")

            self.state.last_command_at = now_iso()
            return {
                "ok": True,
                "mode": mode,
                "updated": updates,
                **self.state.status_payload(),
            }

    def reset(self) -> dict[str, Any]:
        with self._lock:
            for servo_name in self.state.servos:
                self.state.servos[servo_name] = 0
            self.state.last_command_at = now_iso()
            return {
                "ok": True,
                "resetTo": 0,
                **self.state.status_payload(),
            }

    def set_led(self, payload: dict[str, Any]) -> dict[str, Any]:
        with self._lock:
            if "mode" in payload:
                mode = str(payload["mode"])
                if mode not in VALID_LED_MODES:
                    raise ValueError("Unsupported LED mode")
                self.state.led_mode = mode

            if "brightness" in payload:
                brightness = coerce_int(payload["brightness"], field_name="brightness")
                if not 0 <= brightness <= 255:
                    raise ValueError("brightness must be between 0 and 255")
                self.state.brightness = brightness

            if "color" in payload:
                self.state.color = normalize_rgb_triplet(payload["color"], field_name="color")

            if self.state.led_mode == "vector":
                raw_pixels = payload.get("pixelSignals", payload.get("pixels"))
                if "pixels" in payload and "pixelSignals" in payload:
                    raise ValueError("Use either pixels or pixelSignals when mode=vector")
                if raw_pixels is None:
                    raise ValueError("pixels or pixelSignals is required when mode=vector")
                self.state.pixels = normalize_vector_pixels(
                    raw_pixels,
                    pixel_count=self.state.led_count,
                    default_brightness=self.state.brightness,
                )
            elif "pixels" in payload or "pixelSignals" in payload:
                raise ValueError("pixels and pixelSignals are only supported when mode=vector")
            elif self.state.led_mode == "off":
                self._rebuild_uniform_pixels(off=True)
            else:
                self._rebuild_uniform_pixels()

            self.state.last_command_at = now_iso()
            return {
                "ok": True,
                **self.state.led_payload(),
            }

    def set_sensors(self, payload: dict[str, Any]) -> dict[str, Any]:
        with self._lock:
            if HEAD_CAPACITIVE_FIELD not in payload:
                raise ValueError(f"{HEAD_CAPACITIVE_FIELD} is required")
            self.state.head_capacitive = normalize_binary_signal(
                payload[HEAD_CAPACITIVE_FIELD],
                field_name=HEAD_CAPACITIVE_FIELD,
            )
            self.state.last_command_at = now_iso()
            return {
                "ok": True,
                **self.state.sensors_payload(),
            }

    def start_action(self, payload: dict[str, Any]) -> dict[str, Any]:
        action_name = str(payload.get("name") or "").strip()
        if not action_name:
            raise ValueError("name is required")

        action_meta = next((item for item in AVAILABLE_ACTIONS if item["name"] == action_name), None)
        if action_meta is None:
            raise ValueError(f"Unknown action: {action_name}")

        loops = coerce_int(payload.get("loops", 1), field_name="loops")
        if loops <= 0:
            raise ValueError("loops must be >= 1")

        self.stop_action()
        self._action_stop.clear()

        def worker() -> None:
            duration = max(0.4, action_meta["frames"] * 0.08 * loops)
            started_at = now_iso()
            with self._lock:
                self.state.playing = True
                self.state.current_action = action_name
                self.state.current_action_loops = loops
                self.state.last_action_started_at = started_at
                self.state.last_command_at = started_at

            end_at = time.monotonic() + duration
            while time.monotonic() < end_at:
                if self._action_stop.wait(timeout=0.05):
                    break

            with self._lock:
                self.state.playing = False
                self.state.current_action = None
                self.state.current_action_loops = 0
                self.state.last_command_at = now_iso()

        self._action_thread = Thread(target=worker, daemon=True)
        self._action_thread.start()
        return {
            "ok": True,
            "started": action_name,
            "loops": loops,
            **self.get_actions(),
        }

    def stop_action(self) -> dict[str, Any]:
        self._action_stop.set()
        worker = self._action_thread
        if worker and worker.is_alive():
            worker.join(timeout=1.0)
        with self._lock:
            self.state.playing = False
            self.state.current_action = None
            self.state.current_action_loops = 0
            self.state.last_command_at = now_iso()
            return {
                "ok": True,
                "stopped": True,
                **self.state.actions_payload(),
            }


class MockLampHTTPServer(ThreadingHTTPServer):
    def __init__(self, server_address, handler_class, controller: MockLampController):
        super().__init__(server_address, handler_class)
        self.controller = controller


class MockLampHandler(BaseHTTPRequestHandler):
    server: MockLampHTTPServer

    def log_message(self, format: str, *args) -> None:  # noqa: A003
        print(f"[mock-lamp] {self.address_string()} - {format % args}")

    def _send_json(self, status_code: int, payload: dict[str, Any]) -> None:
        body = json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _read_json(self) -> dict[str, Any]:
        length = int(self.headers.get("Content-Length", "0") or 0)
        if length <= 0:
            return {}
        raw = self.rfile.read(length).decode("utf-8")
        return json.loads(raw) if raw.strip() else {}

    def do_GET(self) -> None:  # noqa: N802
        try:
            if self.path == "/health":
                self._send_json(
                    200,
                    {
                        "ok": True,
                        "service": "mock-mira-light-device",
                        "time": now_iso(),
                        "snapshot": self.server.controller.snapshot(),
                    },
                )
                return
            if self.path == "/status":
                self._send_json(200, self.server.controller.get_status())
                return
            if self.path == "/led":
                self._send_json(200, self.server.controller.get_led())
                return
            if self.path == "/sensors":
                self._send_json(200, self.server.controller.get_sensors())
                return
            if self.path == "/actions":
                self._send_json(200, self.server.controller.get_actions())
                return
            self._send_json(404, {"ok": False, "error": "Not found"})
        except Exception as exc:  # noqa: BLE001
            self._send_json(500, {"ok": False, "error": str(exc)})

    def do_POST(self) -> None:  # noqa: N802
        try:
            if self.path == "/control":
                self._send_json(200, self.server.controller.apply_control(self._read_json()))
                return
            if self.path == "/reset":
                self._send_json(200, self.server.controller.reset())
                return
            if self.path == "/led":
                self._send_json(200, self.server.controller.set_led(self._read_json()))
                return
            if self.path == "/sensors":
                self._send_json(200, self.server.controller.set_sensors(self._read_json()))
                return
            if self.path == "/action":
                self._send_json(200, self.server.controller.start_action(self._read_json()))
                return
            if self.path == "/action/stop":
                self._send_json(200, self.server.controller.stop_action())
                return
            self._send_json(404, {"ok": False, "error": "Not found"})
        except ValueError as exc:
            self._send_json(400, {"ok": False, "error": str(exc)})
        except json.JSONDecodeError as exc:
            self._send_json(400, {"ok": False, "error": f"Invalid JSON: {exc}"})
        except Exception as exc:  # noqa: BLE001
            self._send_json(500, {"ok": False, "error": str(exc)})


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run a mock Mira Light HTTP server.")
    parser.add_argument("--host", default=DEFAULT_HOST, help="Bind host")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT, help="Bind port")
    parser.add_argument("--led-count", type=int, default=DEFAULT_LED_COUNT, help="Mock LED pixel count")
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    controller = MockLampController(led_count=args.led_count)
    server = MockLampHTTPServer((args.host, args.port), MockLampHandler, controller=controller)
    print(f"[mock-lamp] starting at http://{args.host}:{args.port}")
    print(f"[mock-lamp] led_count={args.led_count}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("[mock-lamp] shutdown requested")
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
