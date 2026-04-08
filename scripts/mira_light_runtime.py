#!/usr/bin/env python3
"""Shared runtime for Mira Light booth control.

This module is the common execution surface for:

- terminal triggering
- future OpenClaw triggering
- the local booth web console

It intentionally keeps the control surface small and grounded in the existing
ESP32 REST API:

- GET /status
- GET /led
- GET /actions
- POST /control
- POST /led
- POST /action
- POST /action/stop
- POST /reset
"""

from __future__ import annotations

from collections import deque
from datetime import datetime, timezone
import json
import os
import threading
import time
import urllib.error
import urllib.request
from typing import Any, Callable, Dict

from scenes import POSES, PROFILE_INFO, SCENE_META, SCENES, SERVO_CALIBRATION


DEFAULT_TIMEOUT_SECONDS = 3.0
SERVO_KEYS = ("servo1", "servo2", "servo3", "servo4")
VALID_CONTROL_MODES = {"absolute", "relative"}
VALID_LED_MODES = {"off", "solid", "breathing", "rainbow", "rainbow_cycle", "vector"}
MAX_RELATIVE_DELTA = 45
LED_PIXEL_COUNT = int(os.environ.get("MIRA_LIGHT_LED_PIXEL_COUNT", "40"))


class SceneStopped(RuntimeError):
    """Raised when a running scene is asked to stop early."""


class PayloadValidationError(RuntimeError):
    """Raised when incoming HTTP control payloads are structurally invalid."""


def _coerce_int(value: Any, *, field_name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise PayloadValidationError(f"{field_name} must be an integer")
    if int(value) != value:
        raise PayloadValidationError(f"{field_name} must be an integer")
    return int(value)


def _normalize_rgb_triplet(value: Any, *, field_name: str) -> dict[str, int]:
    if isinstance(value, dict):
        allowed = {"r", "g", "b"}
        unknown = sorted(set(value) - allowed)
        if unknown:
            raise PayloadValidationError(f"{field_name} has unsupported keys: {', '.join(unknown)}")
        missing = [channel for channel in ("r", "g", "b") if channel not in value]
        if missing:
            raise PayloadValidationError(f"{field_name} is missing channels: {', '.join(missing)}")
        red = _coerce_int(value["r"], field_name=f"{field_name}.r")
        green = _coerce_int(value["g"], field_name=f"{field_name}.g")
        blue = _coerce_int(value["b"], field_name=f"{field_name}.b")
    elif isinstance(value, (list, tuple)) and len(value) == 3:
        red = _coerce_int(value[0], field_name=f"{field_name}[0]")
        green = _coerce_int(value[1], field_name=f"{field_name}[1]")
        blue = _coerce_int(value[2], field_name=f"{field_name}[2]")
    else:
        raise PayloadValidationError(f"{field_name} must be an RGB object or 3-value vector")

    normalized = {"r": red, "g": green, "b": blue}
    for channel_name, channel_value in normalized.items():
        if not 0 <= channel_value <= 255:
            raise PayloadValidationError(f"{field_name}.{channel_name} must be between 0 and 255")
    return normalized


class MiraLightClient:
    """Thin HTTP client around the current ESP32 REST API."""

    def __init__(self, base_url: str, timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS, dry_run: bool = False):
        self.base_url = base_url.rstrip("/")
        self.timeout_seconds = timeout_seconds
        self.dry_run = dry_run

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
        return self._request("GET", "/status")

    def get_led(self) -> Any:
        return self._request("GET", "/led")

    def get_actions(self) -> Any:
        return self._request("GET", "/actions")

    def set_led(self, payload: Dict[str, Any]) -> Any:
        return self._request("POST", "/led", payload)

    def control(self, payload: Dict[str, Any]) -> Any:
        return self._request("POST", "/control", payload)

    def run_action(self, payload: Dict[str, Any]) -> Any:
        return self._request("POST", "/action", payload)

    def stop_action(self) -> Any:
        return self._request("POST", "/action/stop")

    def reset(self) -> Any:
        return self._request("POST", "/reset")


class BoothController:
    """Runs scene steps one by one with optional logging and cancellation."""

    def __init__(
        self,
        client: MiraLightClient,
        emit: Callable[[str], None] | None = None,
        should_stop: Callable[[], bool] | None = None,
        on_step: Callable[[dict[str, Any]], None] | None = None,
    ):
        self.client = client
        self.emit = emit or print
        self.should_stop = should_stop or (lambda: False)
        self.on_step = on_step

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

    def run_scene(self, scene_name: str) -> None:
        if scene_name not in SCENES:
            raise KeyError(f"Unknown scene: {scene_name}")

        scene = SCENES[scene_name]
        self._log(f"=== Scene: {scene_name} / {scene['title']} ===")

        host_line = scene.get("host_line")
        if host_line:
            self._log(f"[host] {host_line}")

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
            self._log(f"[skip-audio] asset={step['name']}")
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
        self.show_experimental = os.environ.get("MIRA_LIGHT_SHOW_EXPERIMENTAL", "").strip().lower() in {
            "1",
            "true",
            "yes",
            "on",
        }

        self._log_lock = threading.Lock()
        self._state_lock = threading.Lock()
        self._run_lock = threading.Lock()
        self._stop_event = threading.Event()
        self._logs: deque[dict[str, str]] = deque(maxlen=300)

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

    def get_client(self) -> MiraLightClient:
        return MiraLightClient(
            base_url=self.base_url,
            timeout_seconds=self.timeout_seconds,
            dry_run=self.dry_run,
        )

    def _ensure_manual_control_allowed(self, capability: str) -> None:
        with self._state_lock:
            running_scene = self._running_scene
        if running_scene:
            raise RuntimeError(
                f"Cannot directly {capability} while a scene is running: {running_scene}. "
                "Stop the scene first."
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

        allowed_keys = {"mode", "brightness", "color", "pixels"}
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
            pixels = payload.get("pixels")
            if not isinstance(pixels, list):
                raise PayloadValidationError("pixels must be a list when mode=vector")
            if len(pixels) != LED_PIXEL_COUNT:
                raise PayloadValidationError(f"pixels must contain exactly {LED_PIXEL_COUNT} RGB entries")
            normalized["pixels"] = [
                _normalize_rgb_triplet(pixel, field_name=f"pixels[{index}]") for index, pixel in enumerate(pixels)
            ]
            return normalized

        if "pixels" in payload:
            raise PayloadValidationError("pixels is only supported when mode=vector")

        if mode in {"solid", "breathing"}:
            if "color" not in payload:
                raise PayloadValidationError(f"color is required when mode={mode}")
            normalized["color"] = _normalize_rgb_triplet(payload["color"], field_name="color")
            return normalized

        if "color" in payload:
            raise PayloadValidationError(f"color is not supported when mode={mode}")

        return normalized

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

    def _record_step(self, step_state: dict[str, Any]) -> None:
        with self._state_lock:
            self._current_step_index = step_state.get("stepIndex")
            self._current_step_total = step_state.get("stepTotal")
            self._current_step_label = step_state.get("stepLabel")
            self._current_step_type = step_state.get("stepType")
            self._last_command = step_state.get("stepLabel")

    def update_config(self, *, base_url: str | None = None, dry_run: bool | None = None) -> dict[str, Any]:
        with self._state_lock:
            if self._running_scene:
                raise RuntimeError("Cannot change runtime config while a scene is running")
            if base_url:
                self.base_url = base_url.rstrip("/")
            if dry_run is not None:
                self.dry_run = bool(dry_run)
        self.log(f"[config] base_url={self.base_url} dry_run={self.dry_run}")
        return self.get_runtime_state()

    def is_scene_available(self, scene_name: str) -> bool:
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
            }

    def get_status(self) -> Any:
        try:
            data = self.get_client().get_status()
        except Exception:
            with self._state_lock:
                self._device_online = False
            raise
        with self._state_lock:
            self._device_online = True
            self._last_status_at = self._now()
        return data

    def get_led(self) -> Any:
        return self.get_client().get_led()

    def get_actions(self) -> Any:
        return self.get_client().get_actions()

    def get_profile(self) -> dict[str, Any]:
        return {
            "info": PROFILE_INFO,
            "servoCalibration": SERVO_CALIBRATION,
            "poses": POSES,
        }

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
        try:
            self.get_client().stop_action()
        except Exception as exc:  # noqa: BLE001 - we want the runtime to survive booth errors
            self.log(f"[runtime-error] stop_action failed: {exc}")
        return self.get_runtime_state()

    def _prepare_run(self, scene_name: str) -> None:
        if scene_name not in SCENES:
            raise KeyError(f"Unknown scene: {scene_name}")
        if not self.is_scene_available(scene_name):
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
        self.log(f"[runtime] start scene {scene_name}")
        self._record_scene_session_state(scene_name, "started")

    def _finish_run(self, scene_name: str, error: str | None = None) -> None:
        with self._state_lock:
            self._running_scene = None
            self._last_finished_at = self._now()
            self._last_finished_scene = scene_name
            self._last_error = error
            self._current_step_index = None
            self._current_step_total = None
            self._current_step_label = None
            self._current_step_type = None
        if error:
            self.log(f"[runtime-error] scene {scene_name}: {error}")
        else:
            self.log(f"[runtime] finished scene {scene_name}")
        status = "completed"
        if error:
            status = "stopped" if isinstance(error, str) and "stop requested" in error.lower() else "failed"
        self._record_scene_outcome(scene_name, status, error)
        self._record_scene_session_state(scene_name, status, error)
        self._run_lock.release()

    def run_scene_blocking(self, scene_name: str) -> dict[str, Any]:
        self._prepare_run(scene_name)
        error_text = None
        try:
            controller = BoothController(
                client=self.get_client(),
                emit=self.log,
                should_stop=self._stop_event.is_set,
                on_step=self._record_step,
            )
            controller.run_scene(scene_name)
        except SceneStopped as exc:
            error_text = str(exc)
        except Exception as exc:  # noqa: BLE001
            error_text = str(exc)
            raise
        finally:
            self._finish_run(scene_name, error_text)
        return self.get_runtime_state()

    def _run_scene_worker(self, scene_name: str) -> None:
        error_text = None
        try:
            controller = BoothController(
                client=self.get_client(),
                emit=self.log,
                should_stop=self._stop_event.is_set,
                on_step=self._record_step,
            )
            controller.run_scene(scene_name)
        except SceneStopped as exc:
            error_text = str(exc)
        except Exception as exc:  # noqa: BLE001
            error_text = str(exc)
        finally:
            self._finish_run(scene_name, error_text)

    def start_scene(self, scene_name: str) -> dict[str, Any]:
        self._prepare_run(scene_name)
        worker = threading.Thread(target=self._run_scene_worker, args=(scene_name,), daemon=True)
        with self._state_lock:
            self._runner_thread = worker
        worker.start()
        return self.get_runtime_state()

    def stop_to_pose(self, pose_name: str) -> dict[str, Any]:
        self.stop_scene()
        self.apply_pose(pose_name)
        return self.get_runtime_state()
