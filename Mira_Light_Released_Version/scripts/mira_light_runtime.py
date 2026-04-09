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
from pathlib import Path
import threading
import time
import urllib.error
import urllib.request
from typing import Any, Callable, Dict

from audio_cue_player import AudioCuePlayer
from mira_light_safety import MiraLightSafetyController, SafetyDecision, SafetyViolation
from scenes import POSES, PROFILE_INFO, SCENE_META, SCENES, SERVO_CALIBRATION


DEFAULT_TIMEOUT_SECONDS = 3.0
DEFAULT_SCENE_BUNDLE_CONFIG_PATH = Path(__file__).resolve().parent.parent / "config" / "release_scene_bundles.json"
DEFAULT_AUDIO_CUE_ROOT = Path(__file__).resolve().parent.parent / "assets" / "audio"
TRACKING_FOCUS = {"r": 232, "g": 242, "b": 255}


class SceneStopped(RuntimeError):
    """Raised when a running scene is asked to stop early."""


def _load_scene_bundle_config(config_path: Path) -> tuple[dict[str, dict[str, Any]], str | None, str | None]:
    if not config_path.exists():
        return {}, None, None

    try:
        payload = json.loads(config_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return {}, None, f"Failed to load scene bundle config {config_path}: {exc}"

    bundles: dict[str, dict[str, Any]] = {}
    for name, raw_bundle in payload.get("bundles", {}).items():
        scenes = [scene for scene in raw_bundle.get("scenes", []) if scene in SCENES]
        if not scenes:
            continue
        bundles[name] = {
            "title": raw_bundle.get("title", name),
            "description": raw_bundle.get("description", ""),
            "scenes": scenes,
        }

    default_bundle = payload.get("defaultBundle")
    if default_bundle not in bundles:
        default_bundle = next(iter(bundles), None)
    return bundles, default_bundle, None


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
        apply_control: Callable[[dict[str, Any]], Any] | None = None,
        reset_lamp: Callable[[], Any] | None = None,
        play_audio: Callable[[str], dict[str, Any]] | None = None,
    ):
        self.client = client
        self.emit = emit or print
        self.should_stop = should_stop or (lambda: False)
        self.on_step = on_step
        self.apply_control = apply_control or client.control
        self.reset_lamp = reset_lamp or client.reset
        self.play_audio = play_audio or (
            lambda name: {
                "ok": False,
                "cue": name,
                "reason": "audio_player_not_configured",
            }
        )

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
            self.apply_control(payload)
            return

        if step_type == "led":
            self._log(f"[led] {json.dumps(step['payload'], ensure_ascii=False)}")
            self.client.set_led(step["payload"])
            return

        if step_type == "control":
            self._log(f"[control] {json.dumps(step['payload'], ensure_ascii=False)}")
            self.apply_control(step["payload"])
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
            self.reset_lamp()
            return

        if step_type == "status":
            self._log("[status]")
            result = self.client.get_status()
            self._log(json.dumps(result, ensure_ascii=False, indent=2))
            return

        if step_type == "audio":
            result = self.play_audio(step["name"])
            label = "audio" if result.get("ok") else "audio-skip"
            self._log(f"[{label}] {json.dumps(result, ensure_ascii=False)}")
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
        self._scene_bundle_config_path = Path(
            os.environ.get("MIRA_LIGHT_SCENE_BUNDLES_PATH", str(DEFAULT_SCENE_BUNDLE_CONFIG_PATH))
        )
        self._scene_bundles, self._default_scene_bundle, self._scene_bundle_config_error = _load_scene_bundle_config(
            self._scene_bundle_config_path
        )
        self._scene_bundle_requested = os.environ.get("MIRA_LIGHT_SCENE_BUNDLE", "").strip() or None
        self._scene_bundle_warning: str | None = None
        self._scene_bundle_name: str | None = None
        self._scene_bundle_source = "readiness"
        if self._scene_bundle_requested:
            if self._scene_bundle_requested in self._scene_bundles:
                self._scene_bundle_name = self._scene_bundle_requested
                self._scene_bundle_source = "env"
            elif self._scene_bundles:
                self._scene_bundle_warning = (
                    f"Unknown scene bundle: {self._scene_bundle_requested}; "
                    f"available={','.join(sorted(self._scene_bundles))}"
                )
        elif not self.show_experimental and self._default_scene_bundle:
            self._scene_bundle_name = self._default_scene_bundle
            self._scene_bundle_source = "config_default"
        elif self.show_experimental:
            self._scene_bundle_source = "show_experimental"
        self._audio_cue_root = Path(os.environ.get("MIRA_LIGHT_AUDIO_ASSET_ROOT", str(DEFAULT_AUDIO_CUE_ROOT)))

        self._log_lock = threading.Lock()
        self._state_lock = threading.Lock()
        self._run_lock = threading.Lock()
        self._stop_event = threading.Event()
        self._logs: deque[dict[str, str]] = deque(maxlen=300)
        self._safety = MiraLightSafetyController(SERVO_CALIBRATION)
        self._audio_player = AudioCuePlayer(cue_root=self._audio_cue_root, dry_run=self.dry_run)

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
        self._tracking_active = False
        self._tracking_last_update_at: str | None = None
        self._tracking_target: dict[str, Any] = {"active": False}
        self._tracking_servo_state: dict[str, int] = {}
        self._tracking_led_state: dict[str, Any] | None = None

        if self._scene_bundle_config_error:
            self.log(f"[config-warning] {self._scene_bundle_config_error}")
        if self._scene_bundle_warning:
            self.log(f"[config-warning] {self._scene_bundle_warning}")

    def set_embodied_memory_client(self, client: Any | None) -> None:
        self.embodied_memory_client = client

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

    def _clear_tracking_state(self, *, reason: str, set_command: bool = True, log_message: bool = True) -> None:
        with self._state_lock:
            self._tracking_active = False
            self._tracking_last_update_at = self._now()
            self._tracking_target = {"reason": reason, "active": False}
            if set_command:
                self._last_command = f"tracking-clear:{reason}"
            if self._current_step_type == "tracking":
                self._current_step_index = None
                self._current_step_total = None
                self._current_step_label = None
                self._current_step_type = None
        self._tracking_led_state = None
        if log_message:
            self.log(f"[tracking] cleared reason={reason}")

    def _smooth_servo_target(self, servo_name: str, target: int, alpha: float = 0.42) -> int:
        current = int(self._tracking_servo_state.get(servo_name, self._servo_neutral(servo_name, 90)))
        next_value = round(current + (target - current) * alpha)
        if abs(next_value - current) <= 1:
            next_value = current if abs(target - current) <= 2 else target
        self._tracking_servo_state[servo_name] = int(next_value)
        return int(next_value)

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
                self._audio_player.dry_run = self.dry_run
        self.log(f"[config] base_url={self.base_url} dry_run={self.dry_run}")
        return self.get_runtime_state()

    def _bundle_scene_ids(self) -> set[str] | None:
        if not self._scene_bundle_name:
            return None
        bundle = self._scene_bundles.get(self._scene_bundle_name)
        if not bundle:
            return None
        return set(bundle.get("scenes", []))

    def is_scene_available(self, scene_name: str) -> bool:
        bundle_scene_ids = self._bundle_scene_ids()
        if bundle_scene_ids is not None:
            return scene_name in bundle_scene_ids
        readiness = SCENE_META.get(scene_name, {}).get("readiness", "prototype")
        return self.show_experimental or readiness == "ready"

    def list_scenes(self) -> list[dict[str, Any]]:
        items = []
        bundle_scene_ids = self._bundle_scene_ids()
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
                    "sceneBundle": self._scene_bundle_name,
                    "enabledByBundle": bundle_scene_ids is not None,
                }
            )
        return items

    def get_runtime_state(self) -> dict[str, Any]:
        with self._state_lock:
            return {
                "baseUrl": self.base_url,
                "dryRun": self.dry_run,
                "showExperimental": self.show_experimental,
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
                "sceneBundle": self._scene_bundle_name,
                "sceneBundleSource": self._scene_bundle_source,
                "sceneBundleRequested": self._scene_bundle_requested,
                "sceneBundleConfigPath": str(self._scene_bundle_config_path),
                "sceneBundleAvailable": sorted(self._scene_bundles),
                "audioCueRoot": str(self._audio_cue_root),
                "estimatedServoState": self._safety.snapshot(),
                "trackingActive": self._tracking_active,
                "trackingLastUpdateAt": self._tracking_last_update_at,
                "trackingTarget": self._tracking_target,
            }

    def get_status(self) -> Any:
        try:
            data = self.get_client().get_status()
        except Exception:
            with self._state_lock:
                self._device_online = False
            raise
        self._safety.sync_from_status(data)
        with self._state_lock:
            self._device_online = True
            self._last_status_at = self._now()
        return data

    def get_led(self) -> Any:
        return self.get_client().get_led()

    def get_actions(self) -> Any:
        return self.get_client().get_actions()

    def play_audio(self, cue_name: str) -> dict[str, Any]:
        self._audio_player.dry_run = self.dry_run
        return self._audio_player.play(cue_name, blocking=False)

    def get_profile(self) -> dict[str, Any]:
        return {
            "info": PROFILE_INFO,
            "servoCalibration": SERVO_CALIBRATION,
            "poses": POSES,
        }

    def sync_safety_from_status(self, payload: Any) -> bool:
        return self._safety.sync_from_status(payload)

    def _log_safety_decision(self, decision: SafetyDecision) -> None:
        if decision.status != "clamped":
            return
        for change in decision.changes:
            servo = change["servo"]
            if decision.mode == "relative":
                self.log(
                    "[safety-clamp] "
                    f"source={decision.source} servo={servo} "
                    f"requested_delta={change['requestedDelta']} applied_delta={change['appliedDelta']} "
                    f"target={change['targetAngle']} applied_target={change['appliedTargetAngle']} "
                    f"rehearsal_range={change['rehearsalRange']}"
                )
                continue
            self.log(
                "[safety-clamp] "
                f"source={decision.source} servo={servo} "
                f"requested_angle={change['requestedAngle']} applied_angle={change['appliedAngle']} "
                f"rehearsal_range={change['rehearsalRange']}"
            )

    def _log_safety_rejection(self, exc: SafetyViolation) -> None:
        detail = exc.detail
        servo = detail.get("servo", "-")
        self.log(f"[safety-reject] source={exc.source} servo={servo} error={exc}")

    def _run_safe_control(
        self,
        payload: dict[str, Any],
        *,
        source: str,
        update_last_command: bool,
    ) -> tuple[Any, SafetyDecision]:
        try:
            decision = self._safety.plan_control(payload, source=source)
        except SafetyViolation as exc:
            self._log_safety_rejection(exc)
            raise

        result = self.get_client().control(decision.sanitized_payload)
        self._safety.commit(decision)
        self._log_safety_decision(decision)
        if update_last_command:
            with self._state_lock:
                self._last_command = source
        return result, decision

    def control_lamp(
        self,
        payload: dict[str, Any],
        *,
        source: str = "runtime.control",
        update_last_command: bool = True,
    ) -> dict[str, Any]:
        result, decision = self._run_safe_control(payload, source=source, update_last_command=update_last_command)
        return {"data": result, "safety": decision.to_dict()}

    def send_control(
        self,
        payload: dict[str, Any],
        *,
        source: str = "runtime.control",
        update_last_command: bool = True,
    ) -> Any:
        return self.control_lamp(payload, source=source, update_last_command=update_last_command)["data"]

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
        control_result = self.control_lamp(payload, source=f"tracking:{source}", update_last_command=False)
        normalized_payload = dict(control_result["safety"]["sanitizedPayload"])

        led_payload = {
            "mode": "solid",
            "brightness": 166 if tracking.get("distance_band") == "near" else 150,
            "color": TRACKING_FOCUS,
        }

        self.log(
            "[tracking] "
            f"{source} yaw={yaw_error:.2f} pitch={pitch_error:.2f} "
            f"distance={tracking.get('distance_band')} zone={tracking.get('horizontal_zone')} "
            f"-> {json.dumps(normalized_payload, ensure_ascii=False)}"
        )

        if led_payload != self._tracking_led_state:
            self.get_client().set_led(led_payload)
            self._tracking_led_state = dict(led_payload)

        with self._state_lock:
            self._tracking_active = True
            self._tracking_last_update_at = self._now()
            self._tracking_target = {
                "active": True,
                "source": source,
                "eventType": event.get("event_type"),
                "horizontalZone": tracking.get("horizontal_zone"),
                "verticalZone": tracking.get("vertical_zone"),
                "distanceBand": tracking.get("distance_band"),
                "approachState": tracking.get("approach_state"),
                "targetClass": tracking.get("target_class"),
                "confidence": tracking.get("confidence"),
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
        result = self.get_client().reset()
        self._safety.mark_unknown()
        self._clear_tracking_state(reason="reset", set_command=False, log_message=False)
        return result

    def apply_pose_with_safety(
        self,
        pose_name: str,
        *,
        source: str | None = None,
        update_last_command: bool = True,
    ) -> dict[str, Any]:
        if pose_name not in POSES:
            raise KeyError(f"Unknown pose: {pose_name}")
        payload = {"mode": "absolute", **POSES[pose_name]["angles"]}
        source_name = source or f"apply-pose:{pose_name}"
        try:
            decision = self._safety.plan_pose(pose_name, POSES[pose_name]["angles"], source=source_name)
        except SafetyViolation as exc:
            self._log_safety_rejection(exc)
            raise

        result = self.get_client().control(decision.sanitized_payload)
        self._safety.commit(decision)
        self._log_safety_decision(decision)
        if update_last_command:
            with self._state_lock:
                self._last_command = f"apply-pose:{pose_name}"
        return {"data": result, "safety": decision.to_dict(), "payload": payload}

    def apply_pose(self, pose_name: str) -> Any:
        self.log(f"[runtime] apply pose {pose_name}")
        return self.apply_pose_with_safety(pose_name)["data"]

    def stop_scene(self) -> dict[str, Any]:
        self.log("[runtime] stop requested")
        self._stop_event.set()
        with self._state_lock:
            self._last_command = "stop"
            self._tracking_active = False
            self._tracking_target = {"reason": "manual-stop", "active": False}
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

        self._clear_tracking_state(reason=f"scene:{scene_name}", set_command=False, log_message=False)
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
                apply_control=lambda payload: self.send_control(
                    payload,
                    source=f"scene:{scene_name}:{payload.get('mode', 'relative')}",
                    update_last_command=False,
                ),
                reset_lamp=self.reset_lamp,
                play_audio=self.play_audio,
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
                apply_control=lambda payload: self.send_control(
                    payload,
                    source=f"scene:{scene_name}:{payload.get('mode', 'relative')}",
                    update_last_command=False,
                ),
                reset_lamp=self.reset_lamp,
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
