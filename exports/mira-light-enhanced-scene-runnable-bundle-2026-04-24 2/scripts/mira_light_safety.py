#!/usr/bin/env python3
"""Shared control safety helpers for Mira Light runtime and bridge."""

from __future__ import annotations

from dataclasses import dataclass
import threading
from typing import Any


SERVO_NAMES = ("servo1", "servo2", "servo3", "servo4")


@dataclass
class SafetyDecision:
    source: str
    kind: str
    mode: str
    requested_payload: dict[str, Any]
    sanitized_payload: dict[str, Any]
    status: str
    changes: list[dict[str, Any]]
    state_before: dict[str, int | None]
    state_after: dict[str, int | None]
    pose_name: str | None = None

    def to_dict(self) -> dict[str, Any]:
        payload = {
            "status": self.status,
            "source": self.source,
            "kind": self.kind,
            "mode": self.mode,
            "requestedPayload": self.requested_payload,
            "sanitizedPayload": self.sanitized_payload,
            "changes": self.changes,
            "stateBefore": self.state_before,
            "stateAfter": self.state_after,
        }
        if self.pose_name:
            payload["pose"] = self.pose_name
        return payload


class SafetyViolation(RuntimeError):
    def __init__(
        self,
        message: str,
        *,
        source: str,
        kind: str,
        mode: str,
        requested_payload: dict[str, Any],
        detail: dict[str, Any] | None = None,
    ):
        super().__init__(message)
        self.source = source
        self.kind = kind
        self.mode = mode
        self.requested_payload = requested_payload
        self.detail = detail or {}

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": "rejected",
            "source": self.source,
            "kind": self.kind,
            "mode": self.mode,
            "requestedPayload": self.requested_payload,
            "detail": self.detail,
            "error": str(self),
        }


def _coerce_int(value: Any, *, field_name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{field_name} must be an integer")
    if int(value) != value:
        raise ValueError(f"{field_name} must be an integer")
    return int(value)


def _clamp(value: int, lower: int, upper: int) -> int:
    return max(lower, min(upper, value))


class MiraLightSafetyController:
    def __init__(self, servo_calibration: dict[str, dict[str, Any]]):
        self.servo_calibration = servo_calibration
        self._lock = threading.Lock()
        self._current_state: dict[str, int | None] = {servo: None for servo in SERVO_NAMES if servo in servo_calibration}

    def snapshot(self) -> dict[str, int | None]:
        with self._lock:
            return dict(self._current_state)

    def mark_unknown(self) -> None:
        with self._lock:
            for servo in self._current_state:
                self._current_state[servo] = None

    def sync_from_status(self, payload: Any) -> bool:
        parsed = self._extract_servo_state(payload)
        if not parsed:
            return False
        with self._lock:
            self._current_state.update(parsed)
        return True

    def commit(self, decision: SafetyDecision) -> None:
        with self._lock:
            self._current_state.update(decision.state_after)

    def plan_pose(self, pose_name: str, angles: dict[str, Any], *, source: str) -> SafetyDecision:
        payload = {"mode": "absolute", **angles}
        decision = self._plan(payload, source=source, kind="pose", pose_name=pose_name)
        return decision

    def plan_control(self, payload: dict[str, Any], *, source: str) -> SafetyDecision:
        return self._plan(payload, source=source, kind="control", pose_name=None)

    def _plan(
        self,
        payload: dict[str, Any],
        *,
        source: str,
        kind: str,
        pose_name: str | None,
    ) -> SafetyDecision:
        if not isinstance(payload, dict):
            raise SafetyViolation(
                "control payload must be a JSON object",
                source=source,
                kind=kind,
                mode="unknown",
                requested_payload={},
            )

        mode = str(payload.get("mode", "relative")).strip().lower()
        if mode not in {"absolute", "relative"}:
            raise SafetyViolation(
                f"unsupported control mode: {mode}",
                source=source,
                kind=kind,
                mode=mode,
                requested_payload=dict(payload),
                detail={"reason": "unsupported_mode"},
            )

        keys = [key for key in payload if key != "mode"]
        unknown_keys = [key for key in keys if key not in self._current_state]
        if unknown_keys:
            raise SafetyViolation(
                f"unsupported control fields: {', '.join(sorted(unknown_keys))}",
                source=source,
                kind=kind,
                mode=mode,
                requested_payload=dict(payload),
                detail={"reason": "unsupported_fields", "fields": sorted(unknown_keys)},
            )

        servo_fields = [servo for servo in SERVO_NAMES if servo in payload]
        if not servo_fields:
            raise SafetyViolation(
                "at least one servo field is required",
                source=source,
                kind=kind,
                mode=mode,
                requested_payload=dict(payload),
                detail={"reason": "missing_servo_fields"},
            )

        with self._lock:
            current_state = dict(self._current_state)

        sanitized_payload: dict[str, Any] = {"mode": mode}
        next_state = dict(current_state)
        changes: list[dict[str, Any]] = []

        for servo in servo_fields:
            try:
                requested = _coerce_int(payload[servo], field_name=servo)
            except ValueError as exc:
                raise SafetyViolation(
                    str(exc),
                    source=source,
                    kind=kind,
                    mode=mode,
                    requested_payload=dict(payload),
                    detail={"reason": "invalid_integer", "servo": servo},
                ) from exc

            hard_min, hard_max, rehearsal_min, rehearsal_max = self._ranges(servo)

            if mode == "absolute":
                target = requested
                if target < hard_min or target > hard_max:
                    raise SafetyViolation(
                        (
                            f"{servo} absolute target {target} exceeds hard range "
                            f"[{hard_min}, {hard_max}]"
                        ),
                        source=source,
                        kind=kind,
                        mode=mode,
                        requested_payload=dict(payload),
                        detail={
                            "reason": "target_exceeds_hard_range",
                            "servo": servo,
                            "requestedAngle": target,
                            "hardRange": [hard_min, hard_max],
                        },
                    )
                applied_target = _clamp(target, rehearsal_min, rehearsal_max)
                sanitized_payload[servo] = applied_target
                next_state[servo] = applied_target
                if applied_target != target:
                    changes.append(
                        {
                            "servo": servo,
                            "reason": "clamped_to_rehearsal_range",
                            "requestedAngle": target,
                            "appliedAngle": applied_target,
                            "rehearsalRange": [rehearsal_min, rehearsal_max],
                            "hardRange": [hard_min, hard_max],
                        }
                    )
                continue

            current = current_state.get(servo)
            if current is None:
                raise SafetyViolation(
                    (
                        f"{servo} relative target is unsafe because the current angle is unknown; "
                        "apply a named pose, send an absolute control, or fetch /status first"
                    ),
                    source=source,
                    kind=kind,
                    mode=mode,
                    requested_payload=dict(payload),
                    detail={"reason": "unknown_current_state", "servo": servo},
                )

            target = current + requested
            if target < hard_min or target > hard_max:
                raise SafetyViolation(
                    (
                        f"{servo} relative target {target} exceeds hard range "
                        f"[{hard_min}, {hard_max}]"
                    ),
                    source=source,
                    kind=kind,
                    mode=mode,
                    requested_payload=dict(payload),
                    detail={
                        "reason": "target_exceeds_hard_range",
                        "servo": servo,
                        "currentAngle": current,
                        "requestedDelta": requested,
                        "targetAngle": target,
                        "hardRange": [hard_min, hard_max],
                    },
                )

            applied_target = _clamp(target, rehearsal_min, rehearsal_max)
            applied_delta = applied_target - current
            sanitized_payload[servo] = applied_delta
            next_state[servo] = applied_target
            if applied_delta != requested:
                changes.append(
                    {
                        "servo": servo,
                        "reason": "clamped_to_rehearsal_range",
                        "currentAngle": current,
                        "requestedDelta": requested,
                        "appliedDelta": applied_delta,
                        "targetAngle": target,
                        "appliedTargetAngle": applied_target,
                        "rehearsalRange": [rehearsal_min, rehearsal_max],
                        "hardRange": [hard_min, hard_max],
                    }
                )

        return SafetyDecision(
            source=source,
            kind=kind,
            mode=mode,
            requested_payload=dict(payload),
            sanitized_payload=sanitized_payload,
            status="clamped" if changes else "passed",
            changes=changes,
            state_before=current_state,
            state_after=next_state,
            pose_name=pose_name,
        )

    def _ranges(self, servo: str) -> tuple[int, int, int, int]:
        cfg = self.servo_calibration.get(servo)
        if not isinstance(cfg, dict):
            raise SafetyViolation(
                f"missing servo calibration for {servo}",
                source="safety",
                kind="control",
                mode="unknown",
                requested_payload={},
                detail={"reason": "missing_servo_calibration", "servo": servo},
            )

        hard = cfg.get("hard_range") or [0, 180]
        rehearsal = cfg.get("rehearsal_range") or hard
        if not isinstance(hard, (list, tuple)) or len(hard) != 2:
            raise SafetyViolation(
                f"invalid hard_range for {servo}",
                source="safety",
                kind="control",
                mode="unknown",
                requested_payload={},
                detail={"reason": "invalid_hard_range", "servo": servo},
            )
        if not isinstance(rehearsal, (list, tuple)) or len(rehearsal) != 2:
            raise SafetyViolation(
                f"invalid rehearsal_range for {servo}",
                source="safety",
                kind="control",
                mode="unknown",
                requested_payload={},
                detail={"reason": "invalid_rehearsal_range", "servo": servo},
            )

        hard_min = _coerce_int(hard[0], field_name=f"{servo}.hard_range[0]")
        hard_max = _coerce_int(hard[1], field_name=f"{servo}.hard_range[1]")
        rehearsal_min = _coerce_int(rehearsal[0], field_name=f"{servo}.rehearsal_range[0]")
        rehearsal_max = _coerce_int(rehearsal[1], field_name=f"{servo}.rehearsal_range[1]")
        if hard_min > hard_max or rehearsal_min > rehearsal_max:
            raise SafetyViolation(
                f"invalid range ordering for {servo}",
                source="safety",
                kind="control",
                mode="unknown",
                requested_payload={},
                detail={"reason": "invalid_range_order", "servo": servo},
            )
        return hard_min, hard_max, rehearsal_min, rehearsal_max

    def _extract_servo_state(self, payload: Any) -> dict[str, int]:
        if not isinstance(payload, dict):
            return {}

        if isinstance(payload.get("servos"), list):
            extracted: dict[str, int] = {}
            for item in payload["servos"]:
                if not isinstance(item, dict):
                    continue
                name = item.get("name")
                angle = item.get("angle")
                if name in self._current_state:
                    try:
                        extracted[name] = _coerce_int(angle, field_name=f"{name}.angle")
                    except ValueError:
                        continue
            return extracted

        if isinstance(payload.get("status"), dict):
            return self._extract_servo_state(payload["status"])

        extracted = {}
        for servo in self._current_state:
            if servo not in payload:
                continue
            try:
                extracted[servo] = _coerce_int(payload[servo], field_name=servo)
            except ValueError:
                continue
        return extracted
