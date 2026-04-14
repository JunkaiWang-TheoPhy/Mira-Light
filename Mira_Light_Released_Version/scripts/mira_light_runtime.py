#!/usr/bin/env python3
"""Shared runtime for Mira Light booth control.

This module is the common execution surface for:

- terminal triggering
- future OpenClaw triggering
- the local booth web console

It intentionally keeps the control surface small and scene-first.

The bridge-facing API remains HTTP, but the device-facing transport can now be
either:

- HTTP REST (legacy / mock devices)
- raw TCP servo frames (`tcp://host:port`, e.g. the RDK X5 bridge at 9527)

For raw TCP endpoints, status / LED / action reads are served from local cached
state so the rest of the booth stack can stay stable without sending invalid
HTTP requests to the servo socket.
"""

from __future__ import annotations

from collections import deque
from copy import deepcopy
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import threading
import time
import urllib.error
import urllib.request
from typing import Any, Callable, Dict
from urllib.parse import urlparse

from bus_servo_adapter import BusServoAdapter
from bus_servo_transport import (
    DEFAULT_RDK_X5_HOST,
    DEFAULT_RDK_X5_PORT,
    BusServoRuntimeConfig,
    DryRunBusServoTransport,
    TcpBusServoTransport,
)
from mira_light_signal_contract import (
    DEFAULT_LED_PIN,
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
    rgb_channels,
)
from mira_light_audio import AudioCuePlayer
from scenes import (
    COMFORT_WARM,
    POSES,
    PROFILE_INFO,
    SCENE_META,
    SCENES,
    SERVO_CALIBRATION,
    SOFT_WARM,
    absolute,
    audio,
    comment,
    delay,
    led,
    nudge,
    pose,
)


DEFAULT_TIMEOUT_SECONDS = 3.0
SERVO_KEYS = ("servo1", "servo2", "servo3", "servo4")
VALID_CONTROL_MODES = {"absolute", "relative"}
VALID_SPEAK_VOICES = {"tts", "openclaw", "say", "default", "host", "narration"}
MAX_RELATIVE_DELTA = 45
LED_PIXEL_COUNT = int(os.environ.get("MIRA_LIGHT_LED_PIXEL_COUNT", str(DEFAULT_LED_PIXEL_COUNT)))
MAX_PUBLIC_SPEAK_CHARS = int(os.environ.get("MIRA_LIGHT_MAX_SPEAK_CHARS", "80"))
SUPPORTED_TCP_ACTIONS = ("control", "pose", "scene", "tracking", "sensor_cache")
TCP_LED_UNSUPPORTED_REASON = "raw TCP servo endpoint does not expose a dedicated LED protocol"
SCENE_START_ALIGN_ENABLED = os.environ.get("MIRA_LIGHT_SCENE_START_ALIGN", "0").strip().lower() not in {
    "0",
    "false",
    "no",
    "off",
}
SCENE_START_ALIGN_TOLERANCE_DEG = int(os.environ.get("MIRA_LIGHT_SCENE_START_ALIGN_TOLERANCE_DEG", "3"))
SCENE_START_ALIGN_MOVE_MS = int(os.environ.get("MIRA_LIGHT_SCENE_START_ALIGN_MOVE_MS", "700"))
SCENE_START_ALIGN_SETTLE_MS = int(os.environ.get("MIRA_LIGHT_SCENE_START_ALIGN_SETTLE_MS", "180"))


class SceneStopped(RuntimeError):
    """Raised when a running scene is asked to stop early."""


class PayloadValidationError(RuntimeError):
    """Raised when incoming HTTP control payloads are structurally invalid."""


def _coerce_int(value: Any, *, field_name: str) -> int:
    return coerce_int(value, field_name=field_name, error_cls=PayloadValidationError)


def _load_profile_file(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {"servoCalibration": {}, "poses": {}}

    raw = path.read_text(encoding="utf-8").strip()
    if not raw:
        return {"servoCalibration": {}, "poses": {}}

    parsed = json.loads(raw)
    if not isinstance(parsed, dict):
        raise ValueError(f"Invalid profile file: {path}")
    parsed.setdefault("servoCalibration", {})
    parsed.setdefault("poses", {})
    return parsed


def _save_profile_file(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _status_to_angles(status_payload: dict[str, Any]) -> dict[str, int]:
    servos = status_payload.get("servos", [])
    result: dict[str, int] = {}
    if isinstance(servos, dict):
        for name, angle in servos.items():
            if isinstance(name, str) and isinstance(angle, (int, float)):
                result[name] = int(angle)
        return result
    for item in servos:
        name = item.get("name")
        angle = item.get("angle")
        if isinstance(name, str) and isinstance(angle, (int, float)):
            result[name] = int(angle)
    return result


DIRECTION_YAW = {
    "left": 78,
    "center": 92,
    "right": 106,
}

TRACKING_FOCUS = {"r": 232, "g": 242, "b": 255}
DIRECTOR_PRIMARY_SCENES = {
    "wake_up",
    "curious_observe",
    "touch_affection",
    "cute_probe",
    "daydream",
    "standup_reminder",
    "track_target",
    "celebrate",
    "farewell",
    "sleep",
}


class MiraLightClient:
    """Transport-aware client for HTTP lamps or raw TCP servo endpoints."""

    def __init__(self, base_url: str, timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS, dry_run: bool = False):
        self.base_url = base_url.rstrip("/")
        self.timeout_seconds = timeout_seconds
        self.dry_run = dry_run
        self._lock = threading.Lock()
        self.transport_kind, self.transport_host, self.transport_port = self._resolve_transport_target(self.base_url)
        self._led_cache = self._build_initial_led_cache()
        self._status_cache = self._build_initial_status_cache()
        self._sensors_cache: dict[str, Any] = {HEAD_CAPACITIVE_FIELD: 0}
        self._actions_cache = self._build_actions_cache()
        self._last_transport_result: dict[str, Any] | None = None
        self._bus_servo_adapter: BusServoAdapter | None = None
        if self.transport_kind == "tcp":
            runtime_config = BusServoRuntimeConfig(
                transport="tcp",
                tcp_host=self.transport_host or DEFAULT_RDK_X5_HOST,
                tcp_port=self.transport_port or DEFAULT_RDK_X5_PORT,
                timeout_seconds=self.timeout_seconds,
            )
            transport = DryRunBusServoTransport() if self.dry_run else TcpBusServoTransport(
                host=runtime_config.tcp_host,
                port=runtime_config.tcp_port,
                timeout_seconds=runtime_config.timeout_seconds,
            )
            self._bus_servo_adapter = BusServoAdapter(
                runtime_config=runtime_config,
                transport=transport,
            )
            self._bus_servo_adapter.sync_angles(self._current_angles_snapshot())

    @staticmethod
    def _resolve_transport_target(base_url: str) -> tuple[str, str | None, int | None]:
        parsed_input = base_url.strip()
        if "://" not in parsed_input:
            if "/" not in parsed_input and ":" in parsed_input:
                parsed_input = f"tcp://{parsed_input}"
            else:
                parsed_input = f"http://{parsed_input}"
        parsed = urlparse(parsed_input)
        scheme = parsed.scheme.lower()
        host = parsed.hostname
        port = parsed.port
        if scheme == "tcp":
            return "tcp", host or DEFAULT_RDK_X5_HOST, port or DEFAULT_RDK_X5_PORT
        if scheme in {"http", "https"} and port == DEFAULT_RDK_X5_PORT and parsed.path in {"", "/"}:
            return "tcp", host or DEFAULT_RDK_X5_HOST, port
        return "http", host, port

    def _default_servo_angles(self) -> dict[str, int]:
        neutral_pose = POSES.get("neutral", {}).get("angles", {})
        angles: dict[str, int] = {}
        for servo_name in SERVO_KEYS:
            pose_angle = neutral_pose.get(servo_name)
            if isinstance(pose_angle, (int, float)):
                angles[servo_name] = int(pose_angle)
                continue
            calibration = SERVO_CALIBRATION.get(servo_name, {})
            neutral = calibration.get("neutral")
            if isinstance(neutral, (int, float)):
                angles[servo_name] = int(neutral)
        return angles

    def _build_initial_status_cache(self) -> dict[str, Any]:
        angles = self._default_servo_angles()
        return {
            "transport": self.transport_kind,
            "baseUrl": self.base_url,
            "host": self.transport_host,
            "port": self.transport_port,
            "online": True if self.dry_run else None,
            "estimated": self.transport_kind == "tcp",
            "servos": [
                {
                    "name": servo_name,
                    "angle": int(angles[servo_name]),
                    "estimated": self.transport_kind == "tcp",
                }
                for servo_name in SERVO_KEYS
                if servo_name in angles
            ],
            "sensors": {HEAD_CAPACITIVE_FIELD: 0},
            "led": self._build_initial_led_cache(),
            "lastTransportResult": None,
        }

    def _build_initial_led_cache(self) -> dict[str, Any]:
        pixels = off_pixels(count=LED_PIXEL_COUNT)
        return {
            **build_led_status_payload(
                mode="off",
                brightness=0,
                color={"r": 0, "g": 0, "b": 0},
                pixels=pixels,
                led_count=LED_PIXEL_COUNT,
                pin=DEFAULT_LED_PIN,
            ),
            "transport": self.transport_kind,
            "simulated": self.transport_kind == "tcp",
            "supported": self.transport_kind != "tcp",
            "reason": None if self.transport_kind != "tcp" else TCP_LED_UNSUPPORTED_REASON,
        }

    def _build_led_cache_from_payload(self, payload: Dict[str, Any]) -> dict[str, Any]:
        mode = str(payload.get("mode", self._led_cache.get("mode", "off")))
        brightness = int(payload.get("brightness", self._led_cache.get("brightness", 0)))
        color = deepcopy(payload.get("color", self._led_cache.get("color", {"r": 0, "g": 0, "b": 0})))

        if mode == "vector":
            raw_pixels = payload.get("pixels", [])
            pixels = [
                {
                    "r": int(pixel["r"]),
                    "g": int(pixel["g"]),
                    "b": int(pixel["b"]),
                    "brightness": int(pixel["brightness"]),
                }
                for pixel in raw_pixels
            ]
            if pixels:
                color = rgb_channels(pixels[0])
                brightness = int(pixels[0]["brightness"])
        elif mode == "off":
            pixels = off_pixels(count=LED_PIXEL_COUNT)
        else:
            pixels = make_uniform_pixels(count=LED_PIXEL_COUNT, color=color, brightness=brightness)

        return {
            **build_led_status_payload(
                mode=mode,
                brightness=brightness,
                color=color,
                pixels=pixels,
                led_count=LED_PIXEL_COUNT,
                pin=DEFAULT_LED_PIN,
            ),
            "transport": self.transport_kind,
            "simulated": self.transport_kind == "tcp",
            "supported": self.transport_kind != "tcp",
            "reason": None if self.transport_kind != "tcp" else TCP_LED_UNSUPPORTED_REASON,
        }

    def _build_actions_cache(self) -> dict[str, Any]:
        if self.transport_kind == "tcp":
            return {
                "transport": "tcp",
                "supported": list(SUPPORTED_TCP_ACTIONS),
                "simulated": True,
                "reason": "bridge exposes high-level actions while hardware endpoint only accepts raw servo frames",
            }
        return {}

    def _current_angles_snapshot(self) -> dict[str, int]:
        return {
            item["name"]: int(item["angle"])
            for item in self._status_cache.get("servos", [])
            if isinstance(item.get("name"), str) and isinstance(item.get("angle"), (int, float))
        }

    def _sync_status_cache(self, angles: dict[str, int], *, transport_result: dict[str, Any] | None = None) -> None:
        normalized = self._current_angles_snapshot()
        normalized.update(
            {
                servo_name: int(angle)
                for servo_name, angle in angles.items()
                if servo_name in SERVO_KEYS
            }
        )
        servos = []
        for servo_name in SERVO_KEYS:
            if servo_name not in normalized:
                continue
            servos.append(
                {
                    "name": servo_name,
                    "angle": normalized[servo_name],
                    "estimated": self.transport_kind == "tcp",
                }
            )
        self._status_cache.update(
            {
                "transport": self.transport_kind,
                "baseUrl": self.base_url,
                "host": self.transport_host,
                "port": self.transport_port,
                "online": True,
                "estimated": self.transport_kind == "tcp",
                "servos": servos,
                "sensors": deepcopy(self._sensors_cache),
                "led": deepcopy(self._led_cache),
                "lastTransportResult": deepcopy(transport_result),
            }
        )
        self._last_transport_result = deepcopy(transport_result)

    def _tcp_action_stub(self, action: str, payload: Dict[str, Any] | None = None) -> dict[str, Any]:
        return {
            "ok": True,
            "transport": "tcp",
            "simulated": True,
            "action": action,
            "payload": deepcopy(payload) if payload is not None else None,
            "reason": "raw TCP servo endpoint does not expose action control APIs",
        }

    def _request(self, method: str, path: str, payload: Dict[str, Any] | None = None) -> Any:
        url = f"{self.base_url}{path}"

        if self.dry_run:
            return {
                "dry_run": True,
                "method": method,
                "url": url,
                "payload": payload,
            }

        data = None
        headers = {}
        if payload is not None:
            data = json.dumps(payload).encode("utf-8")
            headers["Content-Type"] = "application/json"

        req = urllib.request.Request(url, data=data, headers=headers, method=method)
        try:
            with urllib.request.urlopen(req, timeout=self.timeout_seconds) as response:
                body = response.read().decode("utf-8").strip()
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace").strip()
            raise RuntimeError(f"HTTP {exc.code} calling {path}: {detail}") from exc
        except urllib.error.URLError as exc:
            raise RuntimeError(f"Failed to reach Mira Light at {url}: {exc}") from exc

        if not body:
            return {}

        try:
            return json.loads(body)
        except json.JSONDecodeError:
            return body

    def get_status(self) -> Any:
        if self.transport_kind == "tcp":
            with self._lock:
                self._status_cache["sensors"] = deepcopy(self._sensors_cache)
                self._status_cache["led"] = deepcopy(self._led_cache)
                self._status_cache["lastTransportResult"] = deepcopy(self._last_transport_result)
                return deepcopy(self._status_cache)
        return self._request("GET", "/status")

    def get_led(self) -> Any:
        if self.transport_kind == "tcp":
            with self._lock:
                return deepcopy(self._led_cache)
        return self._request("GET", "/led")

    def get_sensors(self) -> Any:
        if self.transport_kind == "tcp":
            with self._lock:
                return {**deepcopy(self._sensors_cache), "transport": "tcp", "simulated": True}
        return self._request("GET", "/sensors")

    def get_actions(self) -> Any:
        if self.transport_kind == "tcp":
            with self._lock:
                return deepcopy(self._actions_cache)
        return self._request("GET", "/actions")

    def set_led(self, payload: Dict[str, Any]) -> Any:
        if self.transport_kind == "tcp":
            with self._lock:
                self._led_cache = self._build_led_cache_from_payload(payload)
                self._status_cache["led"] = deepcopy(self._led_cache)
                return deepcopy(self._led_cache)
        return self._request("POST", "/led", payload)

    def set_sensors(self, payload: Dict[str, Any]) -> Any:
        if self.transport_kind == "tcp":
            with self._lock:
                self._sensors_cache = deepcopy(payload)
                self._status_cache["sensors"] = deepcopy(self._sensors_cache)
                return {"ok": True, **deepcopy(self._sensors_cache), "transport": "tcp", "simulated": True}
        return self._request("POST", "/sensors", payload)

    def control(self, payload: Dict[str, Any], *, move_ms: int | None = None) -> Any:
        if self.transport_kind == "tcp":
            if self._bus_servo_adapter is None:
                raise RuntimeError("TCP control requested but servo adapter is not initialized")
            with self._lock:
                result = self._bus_servo_adapter.apply_control_payload(
                    payload,
                    move_ms=move_ms,
                    source="mira-light-runtime",
                )
                self._sync_status_cache(result.get("angles", {}), transport_result=result.get("transport"))
                return deepcopy(result)
        return self._request("POST", "/control", payload)

    def run_action(self, payload: Dict[str, Any]) -> Any:
        if self.transport_kind == "tcp":
            return self._tcp_action_stub("run_action", payload)
        return self._request("POST", "/action", payload)

    def stop_action(self) -> Any:
        if self.transport_kind == "tcp":
            return self._tcp_action_stub("stop_action")
        return self._request("POST", "/action/stop")

    def reset(self) -> Any:
        if self.transport_kind == "tcp":
            neutral_angles = self._default_servo_angles()
            payload = {"mode": "absolute", **neutral_angles}
            result = self.control(payload)
            with self._lock:
                self._led_cache = self._build_initial_led_cache()
                self._status_cache["led"] = deepcopy(self._led_cache)
                return {
                    "ok": True,
                    "transport": "tcp",
                    "resetPose": "neutral",
                    "control": result,
                    "led": deepcopy(self._led_cache),
                }
        return self._request("POST", "/reset")


class BoothController:
    """Runs scene steps one by one with optional logging and cancellation."""

    def __init__(
        self,
        client: MiraLightClient,
        emit: Callable[[str], None] | None = None,
        should_stop: Callable[[], bool] | None = None,
        on_step: Callable[[dict[str, Any]], None] | None = None,
        audio_player: AudioCuePlayer | None = None,
        cue_mode: str = "scene",
        silent_mode: bool = False,
    ):
        self.client = client
        self.emit = emit or print
        self.should_stop = should_stop or (lambda: False)
        self.on_step = on_step
        self.audio_player = audio_player
        self.cue_mode = cue_mode
        self.silent_mode = silent_mode

    def _log(self, message: str) -> None:
        self.emit(message)

    def _check_stop(self) -> None:
        if self.should_stop():
            raise SceneStopped("Scene stop requested")

    def _sleep_ms(self, ms: int) -> None:
        if self.client.dry_run:
            return

        deadline = time.monotonic() + (ms / 1000.0)
        while time.monotonic() < deadline:
            self._check_stop()
            remaining = deadline - time.monotonic()
            time.sleep(min(0.05, max(0.0, remaining)))

    def run_scene(self, scene_name: str, scene_definition: dict[str, Any] | None = None) -> None:
        if scene_name not in SCENES and scene_definition is None:
            raise KeyError(f"Unknown scene: {scene_name}")

        scene = deepcopy(scene_definition or SCENES[scene_name])
        self._log(f"=== Scene: {scene_name} / {scene['title']} ===")

        operator_cue = scene.get("operator_cue")
        if operator_cue:
            self._log(f"[cue-operator] {operator_cue}")

        fallback_hint = scene.get("fallback_hint")
        if fallback_hint:
            self._log(f"[cue-fallback] {fallback_hint}")

        host_line = scene.get("host_line")
        if host_line:
            self._log(f"[host] {host_line}")
            if self.cue_mode in {"director", "full"} and not self.silent_mode:
                self._log(f"[cue-host] {host_line}")
                self.run_step({"type": "audio", "text": host_line, "voice": "say", "wait": True})
                self._sleep_ms(140)
            elif self.cue_mode in {"director", "full"} and self.silent_mode:
                self._log(f"[cue-host-muted] {host_line}")

        for note in scene.get("notes", []):
            self._log(f"[note] {note}")

        for tuning_note in scene.get("tuning_notes", []):
            self._log(f"[tuning] {tuning_note}")

        total_steps = len(scene.get("steps", []))
        for index, step in enumerate(scene.get("steps", []), start=1):
            self._check_stop()
            if self.on_step:
                self.on_step(
                    {
                        "sceneName": scene_name,
                        "sceneTitle": scene["title"],
                        "stepIndex": index,
                        "stepTotal": total_steps,
                        "stepType": step.get("type"),
                        "stepLabel": self._describe_step(step),
                    }
                )
            self.run_step(step)

        self._log(f"[scene-done] {scene_name}")

    def _describe_step(self, step: Dict[str, Any]) -> str:
        step_type = step["type"]
        if step_type == "pose":
            return f"pose:{step['name']}"
        if step_type == "led":
            return f"led:{step['payload'].get('mode', 'unknown')}"
        if step_type == "action":
            return f"action:{step['payload'].get('name', 'unknown')}"
        if step_type == "control":
            keys = [key for key in ("servo1", "servo2", "servo3", "servo4") if key in step.get("payload", {})]
            return f"control:{','.join(keys)}"
        if step_type == "delay":
            return f"delay:{step.get('ms', 0)}ms"
        if step_type == "comment":
            text = str(step.get("text", "")).strip()
            return text[:40] + ("..." if len(text) > 40 else "")
        return step_type

    def run_step(self, step: Dict[str, Any]) -> None:
        step_type = step["type"]

        if step_type == "comment":
            self._log(f"[comment] {step['text']}")
            return

        if step_type == "delay":
            ms = int(step["ms"])
            self._log(f"[delay] {ms}ms")
            self._sleep_ms(ms)
            return

        if step_type == "pose":
            pose_name = step["name"]
            if pose_name not in POSES:
                raise KeyError(f"Unknown pose: {pose_name}")
            payload = {"mode": "absolute", **POSES[pose_name]["angles"]}
            self._log(f"[pose] {pose_name} -> {json.dumps(payload, ensure_ascii=False)}")
            self.client.control(payload)
            return

        if step_type == "led":
            self._log(f"[led] {json.dumps(step['payload'], ensure_ascii=False)}")
            self.client.set_led(step["payload"])
            return

        if step_type == "control":
            self._log(f"[control] {json.dumps(step['payload'], ensure_ascii=False)}")
            self.client.control(step["payload"])
            return

        if step_type == "action":
            self._log(f"[action] {json.dumps(step['payload'], ensure_ascii=False)}")
            self.client.run_action(step["payload"])
            return

        if step_type == "action_stop":
            self._log("[action_stop] POST /action/stop")
            self.client.stop_action()
            return

        if step_type == "reset":
            self._log("[reset] POST /reset")
            self.client.reset()
            return

        if step_type == "status":
            self._log("[status]")
            result = self.client.get_status()
            self._log(json.dumps(result, ensure_ascii=False, indent=2))
            return

        if step_type == "audio":
            if self.silent_mode:
                self._log(f"[audio-skip-silent] payload={json.dumps(step, ensure_ascii=False)}")
                return
            if self.audio_player is None:
                self._log(f"[skip-audio] payload={json.dumps(step, ensure_ascii=False)}")
                return
            self.audio_player.play_step(step)
            return

        if step_type == "sensor_gate":
            condition = step.get("name") or step.get("condition") or "unknown"
            self._log(f"[skip-sensor-gate] condition={condition}")
            return

        raise ValueError(f"Unsupported step type: {step_type}")


class MiraLightRuntime:
    """Shared runtime facade for terminal and local web console use."""

    def __init__(
        self,
        base_url: str,
        timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS,
        dry_run: bool = False,
        embodied_memory_client: Any | None = None,
    ):
        self.base_url = base_url.rstrip("/")
        self.timeout_seconds = timeout_seconds
        self.dry_run = dry_run
        self.embodied_memory_client = embodied_memory_client
        self.audio_player = AudioCuePlayer(emit=lambda message: self.log(message), dry_run=dry_run)
        self.show_experimental = os.environ.get("MIRA_LIGHT_SHOW_EXPERIMENTAL", "").strip().lower() in {
            "1",
            "true",
            "yes",
            "on",
        }
        self.auto_recover_pose = os.environ.get("MIRA_LIGHT_AUTO_RECOVER_POSE", "").strip()

        self._log_lock = threading.Lock()
        self._state_lock = threading.Lock()
        self._run_lock = threading.Lock()
        self._stop_event = threading.Event()
        self._logs: deque[dict[str, str]] = deque(maxlen=300)
        self._client_lock = threading.Lock()

        self._running_scene: str | None = None
        self._runner_thread: threading.Thread | None = None
        self._last_error: str | None = None
        self._last_started_at: str | None = None
        self._last_finished_at: str | None = None
        self._last_finished_scene: str | None = None
        self._current_step_index: int | None = None
        self._current_step_total: int | None = None
        self._current_step_label: str | None = None
        self._current_step_type: str | None = None
        self._last_command: str | None = None
        self._device_online: bool | None = None
        self._last_status_at: str | None = None
        self._cue_mode = "scene"
        self._active_scene_context: dict[str, Any] = {}
        self._last_scene_context: dict[str, Any] = {}
        self._last_trigger: dict[str, Any] | None = None
        self._tracking_active = False
        self._tracking_last_update_at: str | None = None
        self._tracking_target: dict[str, Any] = {}
        self._tracking_servo_state: dict[str, int] = dict(POSES.get("neutral", {}).get("angles", {}))
        self._tracking_led_state: dict[str, Any] = {}
        self._silent_mode = False
        self._client = self._build_client()

    def set_embodied_memory_client(self, client: Any | None) -> None:
        self.embodied_memory_client = client

    def _now(self) -> str:
        return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")

    def log(self, message: str) -> None:
        entry = {"ts": self._now(), "text": message}
        with self._log_lock:
            self._logs.append(entry)
        print(message)

    def get_logs(self) -> list[dict[str, str]]:
        with self._log_lock:
            return list(self._logs)

    def _build_client(self) -> MiraLightClient:
        return MiraLightClient(
            base_url=self.base_url,
            timeout_seconds=self.timeout_seconds,
            dry_run=self.dry_run,
        )

    def get_client(self) -> MiraLightClient:
        with self._client_lock:
            return self._client

    def _ensure_manual_control_allowed(self, capability: str) -> None:
        with self._state_lock:
            running_scene = self._running_scene
            tracking_active = self._tracking_active
        if running_scene:
            raise RuntimeError(
                f"Cannot directly {capability} while a scene is running: {running_scene}. "
                "Stop the scene first."
            )
        if tracking_active:
            raise RuntimeError(
                f"Cannot directly {capability} while live tracking is active. "
                "Stop tracking first."
            )

    def validate_control_payload(self, payload: Dict[str, Any]) -> dict[str, int | str]:
        if not isinstance(payload, dict):
            raise PayloadValidationError("Control payload must be a JSON object")

        allowed_keys = {"mode", *SERVO_KEYS}
        unknown = sorted(set(payload) - allowed_keys)
        if unknown:
            raise PayloadValidationError(f"Unsupported control fields: {', '.join(unknown)}")

        mode = payload.get("mode")
        if mode not in VALID_CONTROL_MODES:
            raise PayloadValidationError("mode must be one of: absolute, relative")

        normalized: dict[str, int | str] = {"mode": str(mode)}
        servo_count = 0
        for servo_name in SERVO_KEYS:
            if servo_name not in payload:
                continue

            servo_count += 1
            value = _coerce_int(payload[servo_name], field_name=servo_name)
            calibration = SERVO_CALIBRATION.get(servo_name, {})
            hard_range = calibration.get("hard_range", [0, 180])
            rehearsal_range = calibration.get("rehearsal_range", hard_range)

            if mode == "absolute":
                low, high = rehearsal_range
                if not low <= value <= high:
                    raise PayloadValidationError(
                        f"{servo_name} absolute angle must be within rehearsal_range [{low}, {high}]"
                    )
            else:
                if abs(value) > MAX_RELATIVE_DELTA:
                    raise PayloadValidationError(
                        f"{servo_name} relative delta must be between {-MAX_RELATIVE_DELTA} and {MAX_RELATIVE_DELTA}"
                    )
                hard_low, hard_high = hard_range
                neutral = calibration.get("neutral")
                if isinstance(neutral, int | float):
                    projected = int(neutral) + value
                    if not hard_low <= projected <= hard_high:
                        raise PayloadValidationError(
                            f"{servo_name} relative delta projects past hard_range [{hard_low}, {hard_high}]"
                        )

            normalized[servo_name] = value

        if servo_count == 0:
            raise PayloadValidationError("At least one servo field is required")

        return normalized

    def validate_led_payload(self, payload: Dict[str, Any]) -> dict[str, Any]:
        if not isinstance(payload, dict):
            raise PayloadValidationError("LED payload must be a JSON object")

        allowed_keys = {"mode", "brightness", "color", "pixels", "pixelSignals"}
        unknown = sorted(set(payload) - allowed_keys)
        if unknown:
            raise PayloadValidationError(f"Unsupported LED fields: {', '.join(unknown)}")

        mode = payload.get("mode")
        if mode not in VALID_LED_MODES:
            raise PayloadValidationError(
                "mode must be one of: off, solid, breathing, rainbow, rainbow_cycle, vector"
            )

        normalized: dict[str, Any] = {"mode": str(mode)}

        if "brightness" in payload:
            brightness = _coerce_int(payload["brightness"], field_name="brightness")
            if not 0 <= brightness <= 255:
                raise PayloadValidationError("brightness must be between 0 and 255")
            normalized["brightness"] = brightness

        if mode == "vector":
            if "color" in payload:
                raise PayloadValidationError("color is not allowed when mode=vector; use pixels")
            if "pixels" in payload and "pixelSignals" in payload:
                raise PayloadValidationError("Use either pixels or pixelSignals when mode=vector")
            if "pixelSignals" in payload:
                raise PayloadValidationError("pixelSignals is only accepted by the mock device; use pixels")
            pixels = payload.get("pixels")
            if not isinstance(pixels, list):
                raise PayloadValidationError("pixels must be a list when mode=vector")
            if len(pixels) != LED_PIXEL_COUNT:
                raise PayloadValidationError(f"pixels must contain exactly {LED_PIXEL_COUNT} RGB or RGBA entries")
            normalized["pixels"] = normalize_vector_pixels(
                pixels,
                pixel_count=LED_PIXEL_COUNT,
                default_brightness=normalized.get("brightness"),
                error_cls=PayloadValidationError,
            )
            return normalized

        if "pixels" in payload or "pixelSignals" in payload:
            raise PayloadValidationError("pixels and pixelSignals are only supported when mode=vector")

        if mode in {"solid", "breathing"}:
            if "color" not in payload:
                raise PayloadValidationError(f"color is required when mode={mode}")
            normalized["color"] = normalize_rgb_triplet(
                payload["color"],
                field_name="color",
                error_cls=PayloadValidationError,
            )
            return normalized

        if "color" in payload:
            raise PayloadValidationError(f"color is not supported when mode={mode}")

        return normalized

    def validate_speak_payload(self, payload: Dict[str, Any]) -> dict[str, Any]:
        if not isinstance(payload, dict):
            raise PayloadValidationError("Speak payload must be a JSON object")

        allowed_keys = {"text", "voice", "wait"}
        unknown = sorted(set(payload) - allowed_keys)
        if unknown:
            raise PayloadValidationError(f"Unsupported speak fields: {', '.join(unknown)}")

        raw_text = payload.get("text")
        if not isinstance(raw_text, str):
            raise PayloadValidationError("text is required")
        cleaned_text = " ".join(raw_text.split()).strip()
        if not cleaned_text:
            raise PayloadValidationError("text is required")
        if len(cleaned_text) > MAX_PUBLIC_SPEAK_CHARS:
            raise PayloadValidationError(
                f"text must be no longer than {MAX_PUBLIC_SPEAK_CHARS} characters"
            )

        raw_voice = payload.get("voice", "tts")
        if not isinstance(raw_voice, str):
            raise PayloadValidationError("voice must be a string")
        voice = raw_voice.strip().lower() or "tts"
        if voice not in VALID_SPEAK_VOICES:
            raise PayloadValidationError("voice must be one of: " + ", ".join(sorted(VALID_SPEAK_VOICES)))

        wait = payload.get("wait", True)
        if not isinstance(wait, bool):
            raise PayloadValidationError("wait must be a boolean")

        return {
            "text": cleaned_text,
            "voice": voice,
            "wait": wait,
        }

    def validate_sensor_payload(self, payload: Dict[str, Any]) -> dict[str, int]:
        if not isinstance(payload, dict):
            raise PayloadValidationError("Sensor payload must be a JSON object")

        allowed_keys = {HEAD_CAPACITIVE_FIELD}
        unknown = sorted(set(payload) - allowed_keys)
        if unknown:
            raise PayloadValidationError(f"Unsupported sensor fields: {', '.join(unknown)}")

        if HEAD_CAPACITIVE_FIELD not in payload:
            raise PayloadValidationError(f"{HEAD_CAPACITIVE_FIELD} is required")

        signal = normalize_binary_signal(
            payload[HEAD_CAPACITIVE_FIELD],
            field_name=HEAD_CAPACITIVE_FIELD,
            error_cls=PayloadValidationError,
        )
        return {HEAD_CAPACITIVE_FIELD: signal}

    def control_joints(self, payload: Dict[str, Any]) -> Any:
        self._ensure_manual_control_allowed("control joints")
        normalized = self.validate_control_payload(payload)
        self.log(f"[runtime] direct joint control {json.dumps(normalized, ensure_ascii=False)}")
        with self._state_lock:
            self._last_command = f"control:{normalized['mode']}"
        return self.get_client().control(normalized)

    def set_led_state(self, payload: Dict[str, Any]) -> Any:
        self._ensure_manual_control_allowed("set LED state")
        normalized = self.validate_led_payload(payload)
        self.log(f"[runtime] direct led control {json.dumps(normalized, ensure_ascii=False)}")
        with self._state_lock:
            self._last_command = f"led:{normalized['mode']}"
        return self.get_client().set_led(normalized)

    def set_sensors_state(self, payload: Dict[str, Any]) -> Any:
        self._ensure_manual_control_allowed("set sensors")
        normalized = self.validate_sensor_payload(payload)
        self.log(f"[runtime] direct sensor update {json.dumps(normalized, ensure_ascii=False)}")
        with self._state_lock:
            self._last_command = "sensors:update"
        return self.get_client().set_sensors(normalized)

    def speak_text(self, payload: Dict[str, Any]) -> dict[str, Any]:
        self._ensure_manual_control_allowed("speak")
        normalized = self.validate_speak_payload(payload)
        self.log(
            f"[runtime] speak voice={normalized['voice']} "
            f"wait={'true' if normalized['wait'] else 'false'} text={normalized['text']}"
        )
        with self._state_lock:
            self._last_command = f"speak:{normalized['voice']}"
        audio_result = self.audio_player.speak_text(
            normalized["text"],
            voice=str(normalized["voice"]),
            wait=bool(normalized["wait"]),
        )
        return {"payload": normalized, "audio": audio_result}

    def _record_step(self, step_state: dict[str, Any]) -> None:
        with self._state_lock:
            self._current_step_index = step_state.get("stepIndex")
            self._current_step_total = step_state.get("stepTotal")
            self._current_step_label = step_state.get("stepLabel")
            self._current_step_type = step_state.get("stepType")
            self._last_command = step_state.get("stepLabel")

    def update_config(
        self,
        *,
        base_url: str | None = None,
        dry_run: bool | None = None,
        auto_recover_pose: str | None = None,
    ) -> dict[str, Any]:
        with self._state_lock:
            if self._running_scene:
                raise RuntimeError("Cannot change runtime config while a scene is running")
            if base_url:
                self.base_url = base_url.rstrip("/")
            if dry_run is not None:
                self.dry_run = bool(dry_run)
                self.audio_player.dry_run = self.dry_run
            if auto_recover_pose is not None:
                cleaned = auto_recover_pose.strip()
                if cleaned and cleaned not in POSES:
                    raise RuntimeError(f"Unknown recovery pose: {cleaned}")
                self.auto_recover_pose = cleaned
        with self._client_lock:
            self._client = self._build_client()
        self.log(
            f"[config] base_url={self.base_url} dry_run={self.dry_run} "
            f"auto_recover_pose={self.auto_recover_pose or '-'}"
        )
        return self.get_runtime_state()

    def is_scene_available(self, scene_name: str) -> bool:
        if scene_name in DIRECTOR_PRIMARY_SCENES:
            return True
        readiness = SCENE_META.get(scene_name, {}).get("readiness", "prototype")
        return self.show_experimental or readiness == "ready"

    def list_scenes(self) -> list[dict[str, Any]]:
        items = []
        for scene_id, scene in SCENES.items():
            if not self.is_scene_available(scene_id):
                continue
            meta = SCENE_META.get(scene_id, {})
            items.append(
                {
                    "id": scene_id,
                    "title": scene["title"],
                    "hostLine": scene.get("host_line", ""),
                "emotionTags": meta.get("emotionTags", []),
                "readiness": meta.get("readiness", "prototype"),
                "priority": meta.get("priority", "P2"),
                "accent": meta.get("accent", "prototype"),
                "durationMs": meta.get("durationMs", 0),
                "requirements": meta.get("requirements", []),
                "requirementIds": meta.get("requirementIds", []),
                "fallbackHint": meta.get("fallbackHint", ""),
                "operatorCue": meta.get("operatorCue", ""),
                "hostLineAudioReady": True,
            }
            )
        return items

    def get_runtime_state(self) -> dict[str, Any]:
        with self._state_lock:
            return {
                "baseUrl": self.base_url,
                "dryRun": self.dry_run,
                "running": self._running_scene is not None,
                "runningScene": self._running_scene,
                "lastError": self._last_error,
                "lastStartedAt": self._last_started_at,
                "lastFinishedAt": self._last_finished_at,
                "lastFinishedScene": self._last_finished_scene,
                "currentStepIndex": self._current_step_index,
                "currentStepTotal": self._current_step_total,
                "currentStepLabel": self._current_step_label,
                "currentStepType": self._current_step_type,
                "lastCommand": self._last_command,
                "deviceOnline": self._device_online,
                "lastStatusAt": self._last_status_at,
                "sceneCount": len(SCENES),
                "cueMode": self._cue_mode,
                "silentMode": self._silent_mode,
                "sceneContext": deepcopy(self._active_scene_context),
                "lastSceneContext": deepcopy(self._last_scene_context),
                "lastTrigger": deepcopy(self._last_trigger),
                "autoRecoverPose": self.auto_recover_pose,
                "trackingActive": self._tracking_active,
                "trackingLastUpdateAt": self._tracking_last_update_at,
                "trackingTarget": deepcopy(self._tracking_target),
            }

    def get_status(self) -> Any:
        try:
            data = self.get_client().get_status()
        except Exception:
            with self._state_lock:
                self._device_online = False
            raise
        with self._state_lock:
            if isinstance(data, dict) and "online" in data:
                online = data.get("online")
                self._device_online = None if online is None else bool(online)
            else:
                self._device_online = True
            self._last_status_at = self._now()
        return data

    def get_led(self) -> Any:
        return self.get_client().get_led()

    def get_sensors(self) -> Any:
        return self.get_client().get_sensors()

    def get_actions(self) -> Any:
        return self.get_client().get_actions()

    def get_profile(self) -> dict[str, Any]:
        return {
            "info": PROFILE_INFO,
            "servoCalibration": SERVO_CALIBRATION,
            "poses": POSES,
        }

    def _scene_start_target_angles(self, scene_definition: dict[str, Any]) -> dict[str, int] | None:
        for step in scene_definition.get("steps", []):
            step_type = step.get("type")
            if step_type == "pose":
                pose_name = str(step.get("name") or "").strip()
                pose_data = POSES.get(pose_name, {})
                pose_angles = pose_data.get("angles", {})
                angles = {
                    servo_name: int(pose_angles[servo_name])
                    for servo_name in SERVO_KEYS
                    if isinstance(pose_angles.get(servo_name), (int, float))
                }
                return angles or None

            if step_type == "control":
                payload = step.get("payload", {})
                if payload.get("mode") != "absolute":
                    return None
                angles = {
                    servo_name: int(payload[servo_name])
                    for servo_name in SERVO_KEYS
                    if isinstance(payload.get(servo_name), (int, float))
                }
                return angles or None

            if step_type in {"comment", "delay", "led", "audio", "sensor_gate"}:
                continue

            return None
        return None

    def _scene_start_misalignment(
        self,
        current_angles: dict[str, int],
        target_angles: dict[str, int],
    ) -> dict[str, dict[str, int | None]]:
        mismatches: dict[str, dict[str, int | None]] = {}
        for servo_name, target in target_angles.items():
            current = current_angles.get(servo_name)
            if not isinstance(current, int):
                mismatches[servo_name] = {"current": None, "target": int(target), "delta": None}
                continue
            delta = abs(int(current) - int(target))
            if delta > SCENE_START_ALIGN_TOLERANCE_DEG:
                mismatches[servo_name] = {"current": int(current), "target": int(target), "delta": int(delta)}
        return mismatches

    def _maybe_align_scene_start(self, scene_name: str, scene_definition: dict[str, Any]) -> None:
        if not SCENE_START_ALIGN_ENABLED:
            return

        target_angles = self._scene_start_target_angles(scene_definition)
        if not target_angles:
            return

        try:
            status_payload = self.get_status()
        except Exception as exc:  # noqa: BLE001 - alignment should not make scene startup brittle
            self.log(f"[pre-align-skip] {scene_name} could not read /status before start: {exc}")
            return

        if not isinstance(status_payload, dict):
            self.log(f"[pre-align-skip] {scene_name} status payload is not a JSON object")
            return

        current_angles = _status_to_angles(status_payload)
        if not current_angles:
            self.log(f"[pre-align-skip] {scene_name} status did not include current servo angles")
            return

        mismatches = self._scene_start_misalignment(current_angles, target_angles)
        if not mismatches:
            return

        payload = {"mode": "absolute", **target_angles}
        self.log(
            f"[pre-align] {scene_name} -> {json.dumps(payload, ensure_ascii=False)} "
            f"because current={json.dumps(mismatches, ensure_ascii=False)}"
        )
        self.get_client().control(payload, move_ms=SCENE_START_ALIGN_MOVE_MS)
        if not self.dry_run and SCENE_START_ALIGN_SETTLE_MS > 0:
            time.sleep(SCENE_START_ALIGN_SETTLE_MS / 1000.0)

    def _profile_path(self) -> Path:
        return Path(PROFILE_INFO["path"])

    def _mark_profile_updated(self) -> None:
        PROFILE_INFO["exists"] = self._profile_path().is_file()
        PROFILE_INFO["loaded"] = PROFILE_INFO["exists"]

    def _normalize_direction(self, raw: Any, *, default: str = "right") -> str:
        value = str(raw or "").strip().lower()
        if value in {"left", "l", "west"}:
            return "left"
        if value in {"center", "centre", "mid", "middle", "c"}:
            return "center"
        if value in {"right", "r", "east"}:
            return "right"
        return default

    @staticmethod
    def _opposite_direction(direction: str) -> str:
        normalized = str(direction or "").strip().lower()
        if normalized == "left":
            return "right"
        if normalized == "right":
            return "left"
        return "center"

    def _direction_from_context(self, scene_context: dict[str, Any], *, default: str = "right") -> str:
        for key in ("departureDirection", "direction", "horizontalZone", "primaryDirection", "touchSide", "side"):
            if key in scene_context:
                return self._normalize_direction(scene_context.get(key), default=default)
        return default

    def _clamp_servo_target(self, servo_name: str, target: int, fallback: tuple[int, int]) -> int:
        low, high = self._servo_rehearsal_range(servo_name, fallback)
        return max(low, min(high, int(target)))

    def _build_dynamic_curious_scene(self, scene_context: dict[str, Any]) -> dict[str, Any]:
        owner_direction_raw = None
        for key in ("ownerDirection", "ownerFaceDirection", "targetDirection", "targetHorizontalZone"):
            if key in scene_context:
                owner_direction_raw = scene_context.get(key)
                break

        judge_direction = self._normalize_direction(
            scene_context.get("judgeDirection") or scene_context.get("horizontalZone"),
            default="center",
        )
        owner_direction = self._normalize_direction(owner_direction_raw, default="center")

        owner_face_found_raw = scene_context.get("ownerFaceFound")
        if isinstance(owner_face_found_raw, bool):
            owner_face_found = owner_face_found_raw and owner_direction_raw is not None
        else:
            owner_detector = str(
                scene_context.get("ownerDetector")
                or scene_context.get("detector")
                or scene_context.get("targetDetector")
                or ""
            ).strip().lower()
            owner_face_found = owner_direction_raw is not None and owner_detector in {"haar_face", "face"}

        fallback_direction = self._opposite_direction(judge_direction)
        focus_direction = owner_direction if owner_face_found else fallback_direction
        away_direction = self._opposite_direction(focus_direction) if owner_face_found else focus_direction

        label = {"left": "左侧", "center": "正前方", "right": "右侧"}
        focus_label = label[focus_direction]
        judge_label = label[judge_direction]

        search_left_yaw = self._clamp_servo_target("servo1", 80, (72, 110))
        search_right_yaw = self._clamp_servo_target("servo1", 104, (72, 110))
        focus_half_yaw = self._clamp_servo_target("servo1", {"left": 84, "center": 92, "right": 100}[focus_direction], (72, 110))
        focus_full_yaw = self._clamp_servo_target("servo1", {"left": 80, "center": 92, "right": 104}[focus_direction], (72, 110))
        focus_peek_yaw = self._clamp_servo_target("servo1", {"left": 82, "center": 94, "right": 102}[focus_direction], (72, 110))
        away_shy_yaw = self._clamp_servo_target("servo1", {"left": 80, "center": 84, "right": 104}[away_direction], (72, 110))
        away_hold_yaw = self._clamp_servo_target("servo1", {"left": 82, "center": 88, "right": 102}[away_direction], (72, 110))
        fallback_hold_yaw = self._clamp_servo_target("servo1", {"left": 78, "center": 92, "right": 106}[focus_direction], (72, 110))

        scene = deepcopy(SCENES["curious_observe"])
        if owner_face_found:
            scene["notes"] = [
                f"先小幅环顾并上下找主人的脸，确认后朝{focus_label}做半转、试探和害羞回望。",
                *scene.get("notes", []),
            ]
            scene["steps"] = [
                pose("neutral"),
                led("solid", brightness=124, color={"r": 255, "g": 225, "b": 190}),
                delay(160),
                comment("先环顾一下，再上下找主人的脸。"),
                absolute(servo1=search_left_yaw, servo2=94, servo3=96, servo4=86),
                delay(180),
                absolute(servo1=search_right_yaw, servo2=98, servo3=100, servo4=96),
                delay(180),
                comment(f"找到主人的脸后，先朝{focus_label}半转过去。"),
                absolute(servo1=focus_half_yaw, servo2=96, servo3=98, servo4=90),
                delay(220),
                comment("再轻轻靠近一点，像想确认你是谁。"),
                absolute(servo1=focus_full_yaw, servo2=98, servo3=102, servo4=90),
                delay(260),
                comment("缓慢摇头一次，像在认真辨认。"),
                nudge(servo1=3 if focus_direction != "right" else 2, servo4=-2),
                delay(140),
                nudge(servo1=-6 if focus_direction != "left" else -4, servo4=4),
                delay(140),
                nudge(servo1=3 if focus_direction != "right" else 2, servo4=-2),
                delay(180),
                comment("再更靠近一点，看着你。"),
                absolute(servo1=focus_full_yaw, servo2=98, servo3=104, servo4=90),
                delay(220),
                comment("转开并低头，表示它有点害羞。"),
                led("solid", brightness=100, color={"r": 246, "g": 214, "b": 186}),
                absolute(servo1=away_shy_yaw, servo2=94, servo3=94, servo4=100),
                delay(320),
                nudge(servo4=4),
                delay(120),
                nudge(servo4=-8),
                delay(120),
                nudge(servo4=4),
                delay(180),
                comment("又忍不住朝你慢慢探出来。"),
                led("solid", brightness=124, color={"r": 255, "g": 225, "b": 190}),
                absolute(servo1=focus_peek_yaw, servo2=98, servo3=106, servo4=92),
                delay(220),
                nudge(servo1=3 if focus_direction != "right" else 2),
                delay(110),
                nudge(servo1=-6 if focus_direction != "left" else -4),
                delay(110),
                nudge(servo1=3 if focus_direction != "right" else 2),
                delay(160),
                comment("面对你点头一下。"),
                absolute(servo1=focus_peek_yaw, servo2=98, servo3=102, servo4=90),
                nudge(servo4=4),
                delay(120),
                nudge(servo4=-8),
                delay(140),
                nudge(servo4=4),
                delay(180),
                comment("如果你继续靠近，它会再往远离你的方向缩一点。"),
                absolute(servo1=away_hold_yaw, servo2=94, servo3=98, servo4=102),
                delay(240),
                comment("害羞结束后，再慢慢往回和往前靠。"),
                absolute(servo1=focus_half_yaw, servo2=98, servo3=102, servo4=92),
            ]
            return scene

        scene["notes"] = [
            f"先环顾并上下找主人的脸；如果没找到，就朝评委{judge_label}的反方向{focus_label}回退。",
            *scene.get("notes", []),
        ]
        scene["steps"] = [
            pose("neutral"),
            led("solid", brightness=120, color={"r": 255, "g": 223, "b": 188}),
            delay(160),
            comment("先环顾一下，再上下找主人的脸。"),
            absolute(servo1=search_left_yaw, servo2=94, servo3=96, servo4=86),
            delay(180),
            absolute(servo1=search_right_yaw, servo2=98, servo3=100, servo4=96),
            delay(180),
            absolute(servo1=92, servo2=93, servo3=96, servo4=100),
            delay(180),
            comment(f"还没找到主人的脸，就先扭向评委{judge_label}的反方向{focus_label}。"),
            led("solid", brightness=108, color={"r": 246, "g": 214, "b": 186}),
            absolute(servo1=fallback_hold_yaw, servo2=94, servo3=96, servo4=98),
            delay(320),
            comment("在那个方向停半拍，像是先留出一点安全距离。"),
            nudge(servo4=3),
            delay(120),
            nudge(servo4=-6),
            delay(120),
            nudge(servo4=3),
            delay(180),
            comment("确认没有新的脸出现后，慢慢回到等待位。"),
            absolute(servo1=focus_half_yaw, servo2=96, servo3=98, servo4=94),
            delay(220),
            pose("neutral"),
            led("solid", brightness=112, color=SOFT_WARM),
        ]
        return scene

    def _build_dynamic_farewell_scene(self, scene_context: dict[str, Any]) -> dict[str, Any]:
        direction = self._direction_from_context(scene_context, default="right")
        look_yaw = DIRECTION_YAW[direction]
        bow_yaw = {"left": 82, "center": 92, "right": 102}[direction]
        label = {"left": "左侧", "center": "正前方", "right": "右侧"}[direction]

        scene = deepcopy(SCENES["farewell"])
        scene["notes"] = [
            f"当前按评委离场的{label}做动态目送。",
            *scene.get("notes", []),
        ]
        scene["steps"] = [
            pose("neutral"),
            led("solid", brightness=108, color={"r": 255, "g": 214, "b": 176}),
            comment(f"先目送评委离开的{label}。"),
            absolute(servo1=look_yaw, servo2=96, servo3=100, servo4=92),
            delay(420),
            audio(text="谢谢你来看我，下次见。", wait=True, voice="tts"),
            comment("再做两次慢慢点头，像挥手说再见。"),
            {"type": "control", "payload": {"mode": "relative", "servo4": 5}},
            delay(180),
            {"type": "control", "payload": {"mode": "relative", "servo4": -10}},
            delay(180),
            {"type": "control", "payload": {"mode": "relative", "servo4": 5}},
            delay(220),
            {"type": "control", "payload": {"mode": "relative", "servo4": 5}},
            delay(180),
            {"type": "control", "payload": {"mode": "relative", "servo4": -10}},
            delay(180),
            {"type": "control", "payload": {"mode": "relative", "servo4": 5}},
            delay(220),
            comment("最后微微低头，像有点舍不得。"),
            absolute(servo1=bow_yaw, servo2=92, servo3=96, servo4=100),
            delay(180),
            pose("neutral"),
            led("solid", brightness=90, color={"r": 255, "g": 210, "b": 170}),
        ]
        return scene

    def _build_dynamic_touch_scene(self, scene_context: dict[str, Any]) -> dict[str, Any]:
        direction = self._direction_from_context(scene_context, default="center")
        base_yaw = {"left": 84, "center": 92, "right": 100}[direction]
        scene = deepcopy(SCENES["touch_affection"])
        updated_steps: list[dict[str, Any]] = []
        for step in scene["steps"]:
            next_step = deepcopy(step)
            if next_step.get("type") == "control" and next_step.get("payload", {}).get("mode") == "absolute":
                payload = dict(next_step["payload"])
                if "servo1" in payload:
                    payload["servo1"] = max(72, min(110, int(base_yaw + (payload["servo1"] - 92))))
                next_step["payload"] = payload
            updated_steps.append(next_step)
        scene["steps"] = updated_steps
        scene["notes"] = [f"当前按 {direction} 侧来手做前探与蹭蹭。", *scene.get("notes", [])]
        return scene

    def _build_dynamic_hand_avoid_scene(self, scene_context: dict[str, Any]) -> dict[str, Any]:
        direction = self._direction_from_context(scene_context, default="right")
        retreat_direction = {"left": "right", "center": "left", "right": "left"}[direction]
        retreat_yaw = {"left": 82, "center": 84, "right": 102}[retreat_direction]
        glance_yaw = {"left": 78, "center": 88, "right": 106}[retreat_direction]

        scene = deepcopy(SCENES["hand_avoid"])
        scene["notes"] = [f"当前检测到 {direction} 侧有手靠近，Mira 会朝 {retreat_direction} 侧后缩。", *scene.get("notes", [])]
        scene["steps"] = [
            pose("neutral"),
            led("solid", brightness=118, color={"r": 255, "g": 226, "b": 188}),
            comment("先快速后缩一点，像给突然靠近的手留出空间。"),
            absolute(servo1=retreat_yaw, servo2=88, servo3=84, servo4=84),
            delay(140),
            comment("再往安全方向多偏一点，偷偷确认对方没有继续逼近。"),
            absolute(servo1=glance_yaw, servo2=90, servo3=88, servo4=90),
            led("solid", brightness=132, color={"r": 255, "g": 236, "b": 212}),
            delay(220),
            comment("停半拍，再慢慢恢复。"),
            led("breathing", brightness=104, color=SOFT_WARM),
            delay(360),
            pose("neutral"),
            led("solid", brightness=112, color=SOFT_WARM),
        ]
        return scene

    def _build_dynamic_multi_person_scene(self, scene_context: dict[str, Any]) -> dict[str, Any]:
        primary = self._normalize_direction(scene_context.get("primaryDirection"), default="left")
        secondary = self._normalize_direction(scene_context.get("secondaryDirection"), default="right")
        primary_yaw = DIRECTION_YAW[primary]
        secondary_yaw = DIRECTION_YAW[secondary]

        scene = deepcopy(SCENES["multi_person_demo"])
        scene["notes"] = [f"当前按 {primary} -> {secondary} -> {primary} 的顺序模拟纠结。", *scene.get("notes", [])]
        scene["steps"] = [
            pose("neutral"),
            comment("先看向第一个人。"),
            absolute(servo1=primary_yaw, servo2=96, servo3=98, servo4=92),
            delay(420),
            comment("又被第二个人吸引过去。"),
            absolute(servo1=secondary_yaw, servo2=96, servo3=98, servo4=90),
            delay(320),
            comment("犹豫一下，最后还是回到第一个人。"),
            absolute(servo1=primary_yaw, servo2=96, servo3=100, servo4=94),
            delay(420),
            pose("neutral"),
            led("solid", brightness=112, color=SOFT_WARM),
        ]
        return scene

    def _resolve_scene_definition(self, scene_name: str, scene_context: dict[str, Any] | None = None) -> dict[str, Any]:
        resolved_context = deepcopy(scene_context or {})

        if scene_name == "curious_observe":
            scene = self._build_dynamic_curious_scene(resolved_context)
        elif scene_name == "farewell":
            scene = self._build_dynamic_farewell_scene(resolved_context)
        elif scene_name == "touch_affection":
            scene = self._build_dynamic_touch_scene(resolved_context)
        elif scene_name == "hand_avoid":
            scene = self._build_dynamic_hand_avoid_scene(resolved_context)
        elif scene_name == "multi_person_demo":
            scene = self._build_dynamic_multi_person_scene(resolved_context)
        else:
            scene = deepcopy(SCENES[scene_name])

        meta = SCENE_META.get(scene_name, {})
        scene["operator_cue"] = meta.get("operatorCue", "")
        scene["fallback_hint"] = meta.get("fallbackHint", "")

        transcript = str(resolved_context.get("transcript") or "").strip()
        if transcript:
            scene.setdefault("notes", []).insert(0, f"现场输入：{transcript}")

        return scene

    def preview_scene(self, scene_name: str, scene_context: dict[str, Any] | None = None) -> dict[str, Any]:
        if scene_name not in SCENES:
            raise KeyError(f"Unknown scene: {scene_name}")
        return self._resolve_scene_definition(scene_name, scene_context=scene_context)

    def capture_pose_to_profile(self, pose_name: str, *, notes: str = "", verified: bool = False) -> dict[str, Any]:
        status_payload = self.get_status()
        angles = _status_to_angles(status_payload)
        if not angles:
            raise RuntimeError("Could not extract servo angles from /status")

        profile_path = self._profile_path()
        profile = _load_profile_file(profile_path)
        saved_pose = {
            "verified": bool(verified),
            "angles": angles,
            "notes": notes or f"Captured from lamp status at {self.base_url}",
        }
        profile["poses"][pose_name] = saved_pose
        _save_profile_file(profile_path, profile)
        POSES[pose_name] = deepcopy(saved_pose)
        self._mark_profile_updated()
        self.log(f"[profile] captured pose {pose_name} -> {profile_path}")
        return {"saved": pose_name, "path": str(profile_path), "angles": angles}

    def update_servo_meta_in_profile(self, servo_name: str, updates: dict[str, Any]) -> dict[str, Any]:
        if servo_name not in SERVO_CALIBRATION:
            raise KeyError(f"Unknown servo: {servo_name}")

        profile_path = self._profile_path()
        profile = _load_profile_file(profile_path)
        current = dict(profile["servoCalibration"].get(servo_name, {}))
        current.update({key: value for key, value in updates.items() if value is not None})
        profile["servoCalibration"][servo_name] = current
        _save_profile_file(profile_path, profile)
        SERVO_CALIBRATION[servo_name] = deepcopy(current)
        self._mark_profile_updated()
        self.log(f"[profile] updated servo meta {servo_name} -> {profile_path}")
        return {"saved": servo_name, "path": str(profile_path), "value": current}

    def _record_scene_outcome(self, scene_name: str, status: str, error: str | None = None) -> None:
        client = self.embodied_memory_client
        if client is None:
            return
        try:
            client.record_scene_outcome(
                scene_name=scene_name,
                status=status,
                runtime_state=self.get_runtime_state(),
                error=error,
            )
        except Exception as exc:  # noqa: BLE001
            self.log(f"[memory-warning] record_scene_outcome failed: {exc}")

    def _record_scene_session_state(self, scene_name: str, phase: str, error: str | None = None) -> None:
        client = self.embodied_memory_client
        if client is None:
            return
        try:
            client.record_scene_session_state(
                scene_name=scene_name,
                phase=phase,
                runtime_state=self.get_runtime_state(),
                error=error,
            )
        except Exception as exc:  # noqa: BLE001
            self.log(f"[memory-warning] record_scene_session_state failed: {exc}")

    def _servo_neutral(self, servo_name: str, fallback: int) -> int:
        calibration = SERVO_CALIBRATION.get(servo_name, {})
        value = calibration.get("neutral", fallback)
        return int(value) if isinstance(value, (int, float)) else fallback

    def _servo_rehearsal_range(self, servo_name: str, fallback: tuple[int, int]) -> tuple[int, int]:
        calibration = SERVO_CALIBRATION.get(servo_name, {})
        values = calibration.get("rehearsal_range", fallback)
        if (
            isinstance(values, list)
            and len(values) == 2
            and all(isinstance(item, (int, float)) for item in values)
        ):
            return int(values[0]), int(values[1])
        return fallback

    def _clear_tracking_state(self, *, reason: str) -> None:
        with self._state_lock:
            self._tracking_active = False
            self._tracking_last_update_at = self._now()
            self._tracking_target = {"reason": reason, "active": False}
            self._current_step_label = None
            self._current_step_type = None
        self.log(f"[tracking] cleared reason={reason}")

    def _smooth_servo_target(self, servo_name: str, target: int, alpha: float = 0.42) -> int:
        current = int(self._tracking_servo_state.get(servo_name, self._servo_neutral(servo_name, 90)))
        next_value = round(current + (target - current) * alpha)
        if abs(next_value - current) <= 1:
            next_value = current if abs(target - current) <= 2 else target
        self._tracking_servo_state[servo_name] = int(next_value)
        return int(next_value)

    def apply_tracking_event(self, event: dict[str, Any], *, source: str = "vision") -> dict[str, Any]:
        if not isinstance(event, dict):
            raise RuntimeError("tracking event must be a JSON object")

        with self._state_lock:
            running_scene = self._running_scene
        if running_scene and running_scene != "track_target":
            raise RuntimeError(f"Cannot update live tracking while another scene is running: {running_scene}")

        tracking = event.get("tracking", {}) if isinstance(event.get("tracking"), dict) else {}
        control_hint = event.get("control_hint", {}) if isinstance(event.get("control_hint"), dict) else {}
        target_present = bool(tracking.get("target_present"))
        if not target_present:
            self._clear_tracking_state(reason="target_missing")
            return self.get_runtime_state()

        yaw_error = float(control_hint.get("yaw_error_norm", 0.0) or 0.0)
        pitch_error = float(control_hint.get("pitch_error_norm", 0.0) or 0.0)
        lift_intent = float(control_hint.get("lift_intent", 0.5) or 0.5)
        reach_intent = float(control_hint.get("reach_intent", 0.35) or 0.35)

        servo1_neutral = self._servo_neutral("servo1", 90)
        servo2_neutral = self._servo_neutral("servo2", 96)
        servo3_neutral = self._servo_neutral("servo3", 98)
        servo4_neutral = self._servo_neutral("servo4", 90)

        servo1_low, servo1_high = self._servo_rehearsal_range("servo1", (72, 110))
        servo2_low, servo2_high = self._servo_rehearsal_range("servo2", (78, 112))
        servo3_low, servo3_high = self._servo_rehearsal_range("servo3", (80, 120))
        servo4_low, servo4_high = self._servo_rehearsal_range("servo4", (80, 104))

        desired_servo1 = max(servo1_low, min(servo1_high, round(servo1_neutral + yaw_error * 18)))
        desired_servo2 = max(servo2_low, min(servo2_high, round(servo2_neutral + (lift_intent - 0.5) * 16)))
        desired_servo3 = max(servo3_low, min(servo3_high, round(servo3_neutral + (reach_intent - 0.3) * 22)))
        desired_servo4 = max(servo4_low, min(servo4_high, round(servo4_neutral - pitch_error * 10)))

        payload = {
            "mode": "absolute",
            "servo1": self._smooth_servo_target("servo1", desired_servo1),
            "servo2": self._smooth_servo_target("servo2", desired_servo2),
            "servo3": self._smooth_servo_target("servo3", desired_servo3),
            "servo4": self._smooth_servo_target("servo4", desired_servo4),
        }
        normalized_payload = self.validate_control_payload(payload)
        led_payload = {
            "mode": "solid",
            "brightness": 166 if tracking.get("distance_band") == "near" else 150,
            "color": TRACKING_FOCUS,
        }
        normalized_led = self.validate_led_payload(led_payload)

        self.log(
            "[tracking] "
            f"{source} yaw={yaw_error:.2f} pitch={pitch_error:.2f} "
            f"distance={tracking.get('distance_band')} zone={tracking.get('horizontal_zone')} "
            f"-> {json.dumps(normalized_payload, ensure_ascii=False)}"
        )
        self.get_client().control(normalized_payload)

        if normalized_led != self._tracking_led_state:
            self.get_client().set_led(normalized_led)
            self._tracking_led_state = dict(normalized_led)

        with self._state_lock:
            self._tracking_active = True
            self._tracking_last_update_at = self._now()
            self._tracking_target = {
                "source": source,
                "eventType": event.get("event_type"),
                "horizontalZone": tracking.get("horizontal_zone"),
                "verticalZone": tracking.get("vertical_zone"),
                "distanceBand": tracking.get("distance_band"),
                "approachState": tracking.get("approach_state"),
                "targetClass": tracking.get("target_class"),
                "targetMode": tracking.get("target_mode"),
                "targetCount": tracking.get("target_count"),
                "trackId": tracking.get("track_id"),
                "detector": tracking.get("detector"),
                "confidence": tracking.get("confidence"),
                "selectedLockState": tracking.get("selected_lock_state"),
                "selectedReason": tracking.get("selected_reason"),
                "bboxNorm": tracking.get("bbox_norm"),
                "centerNorm": tracking.get("center_norm"),
                "controlHint": {
                    "yawErrorNorm": yaw_error,
                    "pitchErrorNorm": pitch_error,
                    "liftIntent": lift_intent,
                    "reachIntent": reach_intent,
                },
                "servoCommand": dict(normalized_payload),
            }
            self._last_command = f"tracking:{tracking.get('horizontal_zone') or 'unknown'}"
            self._current_step_label = f"tracking:{tracking.get('horizontal_zone') or 'unknown'}"
            self._current_step_type = "tracking"
            self._current_step_index = None
            self._current_step_total = None
        return self.get_runtime_state()

    def reset_lamp(self) -> Any:
        self.log("[runtime] reset lamp")
        with self._state_lock:
            self._last_command = "reset"
        return self.get_client().reset()

    def apply_pose(self, pose_name: str) -> Any:
        if pose_name not in POSES:
            raise KeyError(f"Unknown pose: {pose_name}")
        payload = {"mode": "absolute", **POSES[pose_name]["angles"]}
        self.log(f"[runtime] apply pose {pose_name}")
        with self._state_lock:
            self._last_command = f"apply-pose:{pose_name}"
        return self.get_client().control(payload)

    def stop_scene(self) -> dict[str, Any]:
        self.log("[runtime] stop requested")
        self._stop_event.set()
        with self._state_lock:
            self._last_command = "stop"
            self._tracking_active = False
            self._tracking_target = {"reason": "manual-stop", "active": False}
            self._current_step_label = None
            self._current_step_type = None
        self.audio_player.stop_all()
        try:
            self.get_client().stop_action()
        except Exception as exc:  # noqa: BLE001 - we want the runtime to survive booth errors
            self.log(f"[runtime-error] stop_action failed: {exc}")
        return self.get_runtime_state()

    def _prepare_run(
        self,
        scene_name: str,
        *,
        scene_context: dict[str, Any] | None = None,
        cue_mode: str = "scene",
        silent_mode: bool = False,
        allow_unavailable: bool = False,
    ) -> dict[str, Any]:
        if scene_name not in SCENES:
            raise KeyError(f"Unknown scene: {scene_name}")
        if not allow_unavailable and not self.is_scene_available(scene_name):
            raise RuntimeError(
                f"Scene not enabled for minimal mode: {scene_name}. "
                "Set MIRA_LIGHT_SHOW_EXPERIMENTAL=1 to run non-ready scenes."
            )

        if not self._run_lock.acquire(blocking=False):
            with self._state_lock:
                running_scene = self._running_scene
            raise RuntimeError(f"Another scene is already running: {running_scene}")

        with self._state_lock:
            self._stop_event.clear()
            self._running_scene = scene_name
            self._last_error = None
            self._last_started_at = self._now()
            self._current_step_index = 0
            self._current_step_total = len(SCENES[scene_name].get("steps", []))
            self._current_step_label = "scene:start"
            self._current_step_type = "scene"
            self._last_command = f"run-scene:{scene_name}"
            self._cue_mode = cue_mode
            self._silent_mode = bool(silent_mode)
            self._active_scene_context = deepcopy(scene_context or {})
            self._tracking_active = False
            self._tracking_target = {}
        scene_definition = self._resolve_scene_definition(scene_name, scene_context=scene_context)
        self._maybe_align_scene_start(scene_name, scene_definition)
        with self._state_lock:
            self._current_step_total = len(scene_definition.get("steps", []))
        self.log(f"[runtime] start scene {scene_name} cue_mode={cue_mode} silent_mode={bool(silent_mode)}")
        self._record_scene_session_state(scene_name, "started")
        return scene_definition

    def _finish_run(self, scene_name: str, error: str | None = None) -> None:
        active_context = deepcopy(self._active_scene_context)
        with self._state_lock:
            self._running_scene = None
            self._last_finished_at = self._now()
            self._last_finished_scene = scene_name
            self._last_error = error
            self._current_step_index = None
            self._current_step_total = None
            self._current_step_label = None
            self._current_step_type = None
            self._last_scene_context = active_context
            self._active_scene_context = {}
            self._cue_mode = "scene"
            self._silent_mode = False
        if error:
            self.log(f"[runtime-error] scene {scene_name}: {error}")
        else:
            self.log(f"[runtime] finished scene {scene_name}")
        status = "completed"
        if error:
            status = "stopped" if isinstance(error, str) and "stop requested" in error.lower() else "failed"
        self.audio_player.stop_all()
        if status == "failed" and self.auto_recover_pose:
            try:
                self.apply_pose(self.auto_recover_pose)
                self.log(f"[runtime] auto recovered to pose {self.auto_recover_pose}")
            except Exception as exc:  # noqa: BLE001
                self.log(f"[runtime-error] auto recover failed: {exc}")
        self._record_scene_outcome(scene_name, status, error)
        self._record_scene_session_state(scene_name, status, error)
        self._run_lock.release()

    def run_scene_blocking(
        self,
        scene_name: str,
        *,
        scene_context: dict[str, Any] | None = None,
        cue_mode: str = "scene",
        silent_mode: bool = False,
        allow_unavailable: bool = False,
    ) -> dict[str, Any]:
        scene_definition = self._prepare_run(
            scene_name,
            scene_context=scene_context,
            cue_mode=cue_mode,
            silent_mode=silent_mode,
            allow_unavailable=allow_unavailable,
        )
        error_text = None
        try:
            controller = BoothController(
                client=self.get_client(),
                emit=self.log,
                should_stop=self._stop_event.is_set,
                on_step=self._record_step,
                audio_player=self.audio_player,
                cue_mode=cue_mode,
                silent_mode=silent_mode,
            )
            controller.run_scene(scene_name, scene_definition=scene_definition)
        except SceneStopped as exc:
            error_text = str(exc)
        except Exception as exc:  # noqa: BLE001
            error_text = str(exc)
            raise
        finally:
            self._finish_run(scene_name, error_text)
        return self.get_runtime_state()

    def _run_scene_worker(self, scene_name: str, scene_definition: dict[str, Any], cue_mode: str, silent_mode: bool) -> None:
        error_text = None
        try:
            controller = BoothController(
                client=self.get_client(),
                emit=self.log,
                should_stop=self._stop_event.is_set,
                on_step=self._record_step,
                audio_player=self.audio_player,
                cue_mode=cue_mode,
                silent_mode=silent_mode,
            )
            controller.run_scene(scene_name, scene_definition=scene_definition)
        except SceneStopped as exc:
            error_text = str(exc)
        except Exception as exc:  # noqa: BLE001
            error_text = str(exc)
        finally:
            self._finish_run(scene_name, error_text)

    def start_scene(
        self,
        scene_name: str,
        *,
        scene_context: dict[str, Any] | None = None,
        cue_mode: str = "scene",
        silent_mode: bool = False,
        allow_unavailable: bool = False,
    ) -> dict[str, Any]:
        scene_definition = self._prepare_run(
            scene_name,
            scene_context=scene_context,
            cue_mode=cue_mode,
            silent_mode=silent_mode,
            allow_unavailable=allow_unavailable,
        )
        worker = threading.Thread(
            target=self._run_scene_worker,
            args=(scene_name, scene_definition, cue_mode, silent_mode),
            daemon=True,
        )
        with self._state_lock:
            self._runner_thread = worker
        worker.start()
        return self.get_runtime_state()

    def trigger_event(self, event_name: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        event_key = str(event_name or "").strip().lower()
        event_payload = deepcopy(payload or {})
        scene_name = ""
        scene_context: dict[str, Any] = {}

        if event_key in {"touch", "touch_detected", "hand_near"}:
            scene_name = "touch_affection"
            scene_context = {"touchSide": event_payload.get("side") or event_payload.get("horizontalZone")}
        elif event_key in {"hand_avoid", "hand_avoid_detected", "hand_approach_detected", "avoid_hand"}:
            scene_name = "hand_avoid"
            scene_context = {"touchSide": event_payload.get("side") or event_payload.get("horizontalZone")}
        elif event_key in {"sigh", "sigh_detected"}:
            scene_name = "sigh_demo"
            scene_context = {"transcript": event_payload.get("transcript") or "唉"}
        elif event_key in {"voice_tired", "tired", "voice_demo_tired"}:
            scene_name = "voice_demo_tired"
            scene_context = {"transcript": event_payload.get("transcript") or "今天好累啊"}
        elif event_key in {"praise", "praise_detected", "praised"}:
            scene_name = "praise_demo"
            scene_context = {"transcript": event_payload.get("transcript") or "你好可爱"}
        elif event_key in {"criticism", "criticism_detected", "criticized", "negative_feedback"}:
            scene_name = "criticism_demo"
            scene_context = {"transcript": event_payload.get("transcript") or "你今天表现一般"}
        elif event_key in {"startle", "startle_detected", "startle_sound", "sound_startle"}:
            scene_name = "startle_sound"
            scene_context = {"transcript": event_payload.get("transcript") or "突然的声响"}
        elif event_key in {"multi_person", "multi_person_detected"}:
            scene_name = "multi_person_demo"
            scene_context = {
                "primaryDirection": event_payload.get("primaryDirection") or "left",
                "secondaryDirection": event_payload.get("secondaryDirection") or "right",
            }
        elif event_key in {"farewell", "departing_direction", "farewell_detected"}:
            scene_name = "farewell"
            scene_context = {"departureDirection": event_payload.get("direction") or event_payload.get("horizontalZone")}
        else:
            raise RuntimeError(f"Unsupported trigger event: {event_name}")

        self._last_trigger = {
            "event": event_key,
            "payload": deepcopy(event_payload),
            "scene": scene_name,
            "ts": self._now(),
        }
        self.log(f"[trigger] {event_key} -> {scene_name}")
        return self.start_scene(
            scene_name,
            scene_context=scene_context,
            cue_mode=str(event_payload.get("cueMode") or "scene"),
            silent_mode=bool(event_payload.get("silentMode", False)),
            allow_unavailable=True,
        )

    def stop_to_pose(self, pose_name: str) -> dict[str, Any]:
        self.stop_scene()
        self.apply_pose(pose_name)
        return self.get_runtime_state()
