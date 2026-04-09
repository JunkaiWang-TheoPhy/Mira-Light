#!/usr/bin/env python3
"""Optional memory-context writer for embodied Mira Light events."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
import json
from typing import Any
import urllib.error
import urllib.request


def _now_iso() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def _expires_after(seconds: int) -> str:
    return (datetime.now(timezone.utc) + timedelta(seconds=max(1, seconds))).astimezone().isoformat(timespec="seconds")


def _trim_text(value: Any, max_chars: int = 280) -> str:
    if not isinstance(value, str):
        return ""
    return " ".join(value.strip().split())[:max_chars]


def _normalize_string_list(values: list[Any] | None, *, max_items: int = 12, max_chars: int = 240) -> list[str]:
    items: list[str] = []
    for value in values or []:
        text = _trim_text(value, max_chars)
        if text and text not in items:
            items.append(text)
        if len(items) >= max_items:
            break
    return items


def _prepend_unique(existing: list[str], new_items: list[str], *, max_items: int = 12) -> list[str]:
    merged: list[str] = []
    for item in [*new_items, *existing]:
        if item and item not in merged:
            merged.append(item)
        if len(merged) >= max_items:
            break
    return merged


def _scene_note_profile(scene_name: str, phase: str) -> dict[str, Any]:
    scene_id = _trim_text(scene_name, 80) or "unknown-scene"
    phase_label = _trim_text(phase, 40) or "unknown"

    default_profile = {
        "title": f"Mira Light runtime · {scene_id}",
        "currentState": f"Mira Light scene '{scene_id}' changed phase to '{phase_label}'.",
        "nextStep": "Continue monitoring the scene runtime and check whether operator follow-up is needed.",
        "taskSpec": f"Run and monitor Mira Light scene '{scene_id}' within the embodied booth runtime.",
        "relevantFiles": [
            "scripts/scenes.py",
            "scripts/mira_light_runtime.py",
            "docs/mira-light-scene-implementation-index.md",
        ],
    }

    by_scene = {
        "wake_up": {
            "title": "Mira Light runtime · wake_up",
            "currentStateByPhase": {
                "started": "wake_up is running: the lamp is transitioning from sleep posture into greeting posture with staged warm light and wake-up shiver.",
                "completed": "wake_up completed: the lamp reached its neutral greeting state after light ramp-up, stretch, and shiver.",
                "stopped": "wake_up was interrupted before fully settling into its neutral greeting state.",
                "failed": "wake_up failed during the wake / stretch / shiver sequence.",
            },
            "nextStepByPhase": {
                "started": "Watch whether the lamp completes wake, stretch, and shiver cleanly, then decide if the next human-facing scene should start.",
                "completed": "If a person is still present, the next likely scene is curious_observe or touch_affection.",
                "stopped": "Re-check neutral / wake_half / wake_high poses before re-running wake_up.",
                "failed": "Inspect wake poses and shiver amplitudes, especially servo1 and servo4 ranges, before retrying wake_up.",
            },
            "taskSpec": "Execute the booth wake-up choreography and confirm the lamp can move from sleep into a friendly greeting state.",
            "relevantFiles": [
                "scripts/scenes.py",
                "Figs/motions/01_wake_up/README.md",
                "docs/mira-light-scene-implementation-index.md",
            ],
        },
        "celebrate": {
            "title": "Mira Light runtime · celebrate",
            "currentStateByPhase": {
                "started": "celebrate is running: the lamp is executing the offer celebration choreography with upper/lower sways, color changes, and dance-phase transitions.",
                "completed": "celebrate completed: the lamp returned to neutral after dance, slowdown, and recovery light.",
                "stopped": "celebrate was stopped before the celebration finished and returned to neutral.",
                "failed": "celebrate failed during the celebration choreography, likely around light sequencing, motion extremes, or dance timing.",
            },
            "nextStepByPhase": {
                "started": "Verify that the offer trigger, audio cue, color transitions, and slowdown all stay coherent from a booth-operator perspective.",
                "completed": "If the celebration was part of a live demo, the next likely scene is farewell or sleep.",
                "stopped": "Check whether the stop happened during upper/lower sway or rainbow phase, then decide whether to replay celebrate.",
                "failed": "Inspect celebration motion amplitudes, color timing, and audio placeholder behavior before retrying celebrate.",
            },
            "taskSpec": "Run the offer-celebration choreography and verify that lighting, motion, and demo staging feel like a coherent emotional peak.",
            "relevantFiles": [
                "scripts/scenes.py",
                "web/08_celebrate/index.html",
                "Figs/motions/08_celebrate/README.md",
                "docs/mira-light-scene-implementation-index.md",
            ],
        },
        "track_target": {
            "title": "Mira Light runtime · track_target",
            "currentStateByPhase": {
                "started": "track_target is running: the runtime is executing the current surrogate left-to-right tracking choreography rather than a true closed-loop visual tracker.",
                "completed": "track_target completed: the surrogate tracking choreography returned the lamp to its neutral work pose.",
                "stopped": "track_target stopped before finishing its current tracking pass.",
                "failed": "track_target failed while trying to simulate or execute tracking behavior.",
            },
            "nextStepByPhase": {
                "started": "Continue monitoring target movement quality and check whether the current event stream is still only driving surrogate choreography.",
                "completed": "The next engineering step is still to replace this surrogate choreography with a true visual closed-loop tracker.",
                "stopped": "Check whether the stop was due to target loss, cooldown gating, or scene overlap before retrying track_target.",
                "failed": "Inspect the vision event source, track_target event extraction, and scene mapping before retrying.",
            },
            "taskSpec": "Translate structured vision events into stable target-following behavior, and eventually replace the current surrogate choreography with a true closed-loop tracker.",
            "relevantFiles": [
                "scripts/scenes.py",
                "scripts/track_target_event_extractor.py",
                "scripts/vision_runtime_bridge.py",
                "Figs/motions/07_track_target/README.md",
                "config/mira_light_vision_event.schema.json",
            ],
        },
        "farewell": {
            "title": "Mira Light runtime · farewell",
            "currentStateByPhase": {
                "started": "farewell is running: the lamp is entering the send-off sequence of look, nod-like waving, and lowered head posture.",
                "completed": "farewell completed: the lamp finished its send-off sequence and settled back toward neutral.",
                "stopped": "farewell was stopped before the send-off sequence fully resolved.",
                "failed": "farewell failed during the look / slow nod-wave / lowered-head sequence.",
            },
            "nextStepByPhase": {
                "started": "Watch whether the fixed-angle farewell still reads clearly as look-first, wave-second, lower-head-last.",
                "completed": "If the booth loop is ending, the next likely scene is sleep.",
                "stopped": "Check whether farewell was interrupted before the second nod-wave or the final lowered-head pose.",
                "failed": "Inspect the farewell angle choice and nod timing; if the booth needs dynamic departure following, that feature is still pending.",
            },
            "taskSpec": "Run the current farewell choreography and validate that the send-off reads clearly even before dynamic departure-direction following is implemented.",
            "relevantFiles": [
                "scripts/scenes.py",
                "Figs/motions/09_farewell/README.md",
                "docs/mira-light-scene-implementation-index.md",
            ],
        },
    }

    profile = by_scene.get(scene_id)
    if not profile:
        return default_profile

    return {
        "title": profile["title"],
        "currentState": profile["currentStateByPhase"].get(phase_label, default_profile["currentState"]),
        "nextStep": profile["nextStepByPhase"].get(phase_label, default_profile["nextStep"]),
        "taskSpec": profile["taskSpec"],
        "relevantFiles": profile["relevantFiles"],
    }


class EmbodiedMemoryClient:
    """Write selected scene/device outcomes into Mira's typed memory-context."""

    def __init__(
        self,
        *,
        base_url: str = "",
        auth_token: str = "",
        user_id: str = "mira-light-bridge",
        request_timeout_seconds: float = 2.0,
        device_status_ttl_seconds: int = 900,
        failure_ttl_seconds: int = 3600,
        enabled: bool = False,
        emit: callable | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.auth_token = auth_token
        self.user_id = user_id
        self.request_timeout_seconds = max(0.2, float(request_timeout_seconds))
        self.device_status_ttl_seconds = max(30, int(device_status_ttl_seconds))
        self.failure_ttl_seconds = max(60, int(failure_ttl_seconds))
        self.enabled = bool(enabled and self.base_url)
        self.emit = emit

    def _log(self, message: str) -> None:
        if self.emit:
            self.emit(message)

    def _post_json(self, path: str, body: dict[str, Any]) -> dict[str, Any]:
        if not self.enabled:
            return {"ok": True, "skipped": True}

        encoded = json.dumps(body, ensure_ascii=False).encode("utf-8")
        req = urllib.request.Request(
            f"{self.base_url}{path}",
            data=encoded,
            method="POST",
            headers={
                "Content-Type": "application/json; charset=utf-8",
                **({"Authorization": f"Bearer {self.auth_token}"} if self.auth_token else {}),
            },
        )
        try:
            with urllib.request.urlopen(req, timeout=self.request_timeout_seconds) as response:
                raw = response.read().decode("utf-8").strip()
                return json.loads(raw) if raw else {"ok": True}
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace").strip()
            raise RuntimeError(f"memory-context HTTP {exc.code} calling {path}: {detail}") from exc
        except urllib.error.URLError as exc:
            raise RuntimeError(f"memory-context unavailable: {exc}") from exc

    def _post_write(self, source: str, items: list[dict[str, Any]]) -> dict[str, Any]:
        if not self.enabled or not items:
            return {"ok": True, "skipped": True}
        return self._post_json("/v1/memory/write", {"source": source, "items": items})

    def get_current_session_note(self, *, session_id: str, user_id: str | None = None) -> dict[str, Any]:
        return self._post_json(
            "/v1/session-memory/current",
            {
                "userId": user_id or self.user_id,
                "sessionId": session_id,
            },
        )

    def update_session_note(
        self,
        *,
        session_id: str,
        note: dict[str, Any],
        source_message_id: str | None = None,
        user_id: str | None = None,
    ) -> dict[str, Any]:
        body: dict[str, Any] = {
            "userId": user_id or self.user_id,
            "sessionId": session_id,
            "note": note,
        }
        if source_message_id:
            body["sourceMessageId"] = source_message_id
        return self._post_json("/v1/session-memory/update", body)

    def _merged_session_note(
        self,
        *,
        existing_note: dict[str, Any] | None,
        title: str | None = None,
        current_state: str = "",
        next_step: str = "",
        task_spec: str = "",
        relevant_files: list[str] | None = None,
        errors: list[str] | None = None,
        key_results: list[str] | None = None,
        worklog: list[str] | None = None,
    ) -> dict[str, Any]:
        existing_note = existing_note or {}
        existing_relevant = _normalize_string_list(existing_note.get("relevantFiles"))
        existing_errors = _normalize_string_list(existing_note.get("errors"))
        existing_results = _normalize_string_list(existing_note.get("keyResults"))
        existing_worklog = _normalize_string_list(existing_note.get("worklog"), max_items=20)

        next_relevant = _prepend_unique(
            existing_relevant,
            _normalize_string_list(relevant_files),
            max_items=12,
        )
        next_errors = _prepend_unique(
            existing_errors,
            _normalize_string_list(errors),
            max_items=12,
        )
        next_results = _prepend_unique(
            existing_results,
            _normalize_string_list(key_results),
            max_items=12,
        )
        next_worklog = _prepend_unique(
            existing_worklog,
            _normalize_string_list(worklog, max_items=20),
            max_items=20,
        )

        return {
            "title": _trim_text(title, 120) or existing_note.get("title") or None,
            "currentState": _trim_text(current_state, 1200) or existing_note.get("currentState", ""),
            "nextStep": _trim_text(next_step, 600) or existing_note.get("nextStep", ""),
            "taskSpec": _trim_text(task_spec, 1200) or existing_note.get("taskSpec", ""),
            "relevantFiles": next_relevant,
            "errors": next_errors,
            "keyResults": next_results,
            "worklog": next_worklog,
        }

    def record_scene_session_state(
        self,
        *,
        scene_name: str,
        phase: str,
        runtime_state: dict[str, Any],
        error: str | None = None,
        session_id: str = "mira-light-runtime",
    ) -> dict[str, Any]:
        if not self.enabled:
            return {"ok": True, "skipped": True}

        phase_label = _trim_text(phase, 40) or "unknown"
        scene_label = _trim_text(scene_name, 80) or "unknown-scene"
        observed_at = _now_iso()
        profile = _scene_note_profile(scene_name, phase_label)

        try:
            existing = self.get_current_session_note(session_id=session_id).get("note")
        except Exception as exc:  # noqa: BLE001
            self._log(f"[session-memory] current note read failed: {exc}")
            existing = None

        note = self._merged_session_note(
            existing_note=existing,
            title=profile["title"],
            current_state=profile["currentState"],
            next_step=profile["nextStep"],
            task_spec=profile["taskSpec"],
            relevant_files=[
                *profile["relevantFiles"],
                "scripts/mira_light_runtime.py",
            ],
            errors=[error] if error else [],
            key_results=[f"{observed_at} scene={scene_name} phase={phase_label}"],
            worklog=[f"{observed_at} scene '{scene_name}' -> {phase_label}"],
        )
        return self.update_session_note(session_id=session_id, note=note)

    def record_tracking_session_state(
        self,
        *,
        event_type: str,
        candidate_scene: str,
        candidate_reason: str,
        allowed: bool,
        allowed_reason: str,
        tracking: dict[str, Any],
        session_id: str = "mira-light-vision",
    ) -> dict[str, Any]:
        if not self.enabled:
            return {"ok": True, "skipped": True}

        observed_at = _now_iso()
        target_present = bool(tracking.get("target_present"))
        horizontal = _trim_text(tracking.get("horizontal_zone"), 40) or "unknown"
        vertical = _trim_text(tracking.get("vertical_zone"), 40) or "unknown"
        distance_band = _trim_text(tracking.get("distance_band"), 40) or "unknown"

        current_state = (
            f"Latest vision event '{event_type}' suggests candidate scene '{candidate_scene}'. "
            f"target_present={target_present}, horizontal={horizontal}, vertical={vertical}, distance={distance_band}."
        )
        next_step = (
            "Continue watching vision events and trigger the next runtime scene when the gating rules allow it."
            if allowed
            else f"Do not trigger a new scene yet because: {_trim_text(allowed_reason, 240)}"
        )
        task_spec = "Translate structured vision events into runtime scenes and future closed-loop tracking behavior."

        try:
            existing = self.get_current_session_note(session_id=session_id).get("note")
        except Exception as exc:  # noqa: BLE001
            self._log(f"[session-memory] current note read failed: {exc}")
            existing = None

        note = self._merged_session_note(
            existing_note=existing,
            title="Mira Light vision bridge",
            current_state=current_state,
            next_step=next_step,
            task_spec=task_spec,
            relevant_files=[
                "scripts/track_target_event_extractor.py",
                "scripts/vision_runtime_bridge.py",
                "config/mira_light_vision_event.schema.json",
                "scripts/scenes.py",
            ],
            errors=[allowed_reason] if ("error" in allowed_reason.lower() or "failed" in allowed_reason.lower()) else [],
            key_results=[f"{observed_at} event={event_type} candidate={candidate_scene} allowed={allowed}"],
            worklog=[f"{observed_at} vision candidate={candidate_scene} reason={_trim_text(candidate_reason, 180)}"],
        )
        return self.update_session_note(session_id=session_id, note=note)

    def record_scene_outcome(
        self,
        *,
        scene_name: str,
        status: str,
        runtime_state: dict[str, Any],
        error: str | None = None,
    ) -> dict[str, Any]:
        scene_label = _trim_text(scene_name, 80) or "unknown-scene"
        status_label = _trim_text(status, 40) or "unknown"
        message = f"Mira Light scene '{scene_label}' finished with status '{status_label}'."
        if error:
            message = f"{message} Error: {_trim_text(error, 180)}"

        items: list[dict[str, Any]] = [
            {
                "user_id": self.user_id,
                "namespace": "home",
                "layer": "episodic",
                "kind": "execution_outcome",
                "content": message,
                "structured_value": {
                    "system": "mira-light",
                    "sceneName": scene_name,
                    "status": status,
                    "error": error,
                    "runtimeState": runtime_state,
                    "observedAt": _now_iso(),
                },
                "confidence": 0.96,
                "salience": 0.88 if status == "completed" else 0.95,
                "sensitivity": "normal",
                "tags": ["mira-light", f"scene:{scene_name}", f"status:{status}"],
                "evidence_refs": [f"mira-light:scene:{scene_name}:{status}"],
            }
        ]

        if status != "completed":
            items.append(
                {
                    "user_id": self.user_id,
                    "namespace": "home",
                    "layer": "working",
                    "kind": "scene_state",
                    "content": (
                        f"Mira Light scene '{scene_label}' most recently ended with status '{status_label}'. "
                        "Check bridge/device state before retrying."
                    ),
                    "structured_value": {
                        "system": "mira-light",
                        "sceneName": scene_name,
                        "status": status,
                        "error": error,
                    },
                    "confidence": 1,
                    "salience": 0.95,
                    "sensitivity": "normal",
                    "tags": ["mira-light", "working", f"scene:{scene_name}", f"status:{status}"],
                    "evidence_refs": [f"mira-light:scene:{scene_name}:{status}"],
                    "expires_at": _expires_after(self.failure_ttl_seconds),
                }
            )

        return self._post_write("scene_execution", items)

    def record_device_report(
        self,
        *,
        report_type: str,
        payload: dict[str, Any],
        stored: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        if report_type in {"hello", "heartbeat"}:
            return {"ok": True, "skipped": True, "reason": "low_signal_report"}

        device_id = _trim_text(str(payload.get("deviceId", "unknown-device")), 120) or "unknown-device"
        scene = _trim_text(str(payload.get("scene", payload.get("scene_hint", ""))), 120)
        event_type = _trim_text(str(payload.get("eventType", "")), 80).lower()
        led_mode = _trim_text(str(payload.get("ledMode", "")), 80)
        playing = payload.get("playing")

        if report_type == "status":
            content_bits = [f"Mira Light device '{device_id}' reported status"]
            if scene:
                content_bits.append(f"scene={scene}")
            if isinstance(playing, bool):
                content_bits.append(f"playing={playing}")
            if led_mode:
                content_bits.append(f"ledMode={led_mode}")

            item = {
                "user_id": self.user_id,
                "namespace": "home",
                "layer": "working",
                "kind": "scene_state",
                "content": ", ".join(content_bits) + ".",
                "structured_value": {
                    "system": "mira-light",
                    "reportType": report_type,
                    "deviceId": device_id,
                    "payload": payload,
                    "stored": stored,
                },
                "confidence": 0.86,
                "salience": 0.72,
                "sensitivity": "normal",
                "tags": ["mira-light", "device-status", f"device:{device_id}"],
                "evidence_refs": [f"mira-light:device:{device_id}:status"],
                "expires_at": _expires_after(self.device_status_ttl_seconds),
            }
            return self._post_write("device_observation", [item])

        if report_type == "event":
            severity = "normal"
            if event_type in {"error", "warning", "fault", "blocked", "offline"}:
                severity = event_type
            elif not event_type:
                return {"ok": True, "skipped": True, "reason": "event_missing_type"}

            content = f"Mira Light device '{device_id}' emitted event '{event_type}'."
            if scene:
                content = f"{content} scene={scene}."

            items: list[dict[str, Any]] = [
                {
                    "user_id": self.user_id,
                    "namespace": "home",
                    "layer": "episodic",
                    "kind": "execution_outcome",
                    "content": content,
                    "structured_value": {
                        "system": "mira-light",
                        "reportType": report_type,
                        "eventType": event_type,
                        "deviceId": device_id,
                        "payload": payload,
                        "stored": stored,
                    },
                    "confidence": 0.9,
                    "salience": 0.9 if severity != "normal" else 0.7,
                    "sensitivity": "normal",
                    "tags": ["mira-light", "device-event", f"device:{device_id}", f"event:{event_type}"],
                    "evidence_refs": [f"mira-light:device:{device_id}:event:{event_type}"],
                }
            ]

            if severity != "normal":
                items.append(
                    {
                        "user_id": self.user_id,
                        "namespace": "home",
                        "layer": "working",
                        "kind": "scene_state",
                        "content": (
                            f"Mira Light device '{device_id}' recently reported event '{event_type}'. "
                            "Treat device or bridge state as potentially degraded until re-checked."
                        ),
                        "structured_value": {
                            "system": "mira-light",
                            "eventType": event_type,
                            "deviceId": device_id,
                        },
                        "confidence": 0.96,
                        "salience": 0.92,
                        "sensitivity": "normal",
                        "tags": ["mira-light", "working", f"device:{device_id}", f"event:{event_type}"],
                        "evidence_refs": [f"mira-light:device:{device_id}:event:{event_type}"],
                        "expires_at": _expires_after(self.failure_ttl_seconds),
                    }
                )
            return self._post_write("device_observation", items)

        return {"ok": True, "skipped": True, "reason": "unsupported_report_type"}
