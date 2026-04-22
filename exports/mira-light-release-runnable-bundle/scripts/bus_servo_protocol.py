#!/usr/bin/env python3
"""Helpers for formatting Mira Light bus-servo commands."""

from __future__ import annotations

import re


MIN_SERVO_ID = 0
MAX_SERVO_ID = 254
MIN_PWM = 500
MAX_PWM = 2500
MIN_TIME_MS = 0
MAX_TIME_MS = 9999
SINGLE_COMMAND_RE = re.compile(r"#(?P<id>\d{3})P(?P<pwm>\d{4})T(?P<time>\d{4})!")


def clamp_pwm(value: int, pwm_min: int = MIN_PWM, pwm_max: int = MAX_PWM) -> int:
    return max(int(pwm_min), min(int(pwm_max), int(value)))


def clamp_time_ms(value: int, max_time_ms: int = MAX_TIME_MS) -> int:
    return max(MIN_TIME_MS, min(int(max_time_ms), int(value)))


def normalize_servo_id(value: str | int) -> str:
    if isinstance(value, str):
        raw = value.strip()
        if not raw:
            raise ValueError("servo id must not be empty")
        parsed = int(raw, 10)
    else:
        parsed = int(value)

    if parsed < MIN_SERVO_ID or parsed > MAX_SERVO_ID:
        raise ValueError(f"servo id must be between {MIN_SERVO_ID:03d} and {MAX_SERVO_ID:03d}")
    return f"{parsed:03d}"


def format_single_command(servo_id: str | int, pwm: int, time_ms: int) -> str:
    sid = normalize_servo_id(servo_id)
    return f"#{sid}P{clamp_pwm(pwm):04d}T{clamp_time_ms(time_ms):04d}!"


def format_multi_command(commands: list[dict[str, int | str]]) -> str:
    if not commands:
        raise ValueError("at least one command is required")

    parts = [
        format_single_command(
            item["id"],
            int(item["pwm"]),
            int(item["timeMs"]),
        )
        for item in commands
    ]
    if len(parts) == 1:
        return parts[0]
    return "{" + "".join(parts) + "}"


def _validate_single_command(command: str) -> None:
    match = SINGLE_COMMAND_RE.fullmatch(command)
    if not match:
        raise ValueError(
            "invalid servo frame; expected #IDPWWWWTTTT! with 3-digit ID and 4-digit PWM/TIME fields"
        )

    servo_id = int(match.group("id"))
    pwm = int(match.group("pwm"))
    time_ms = int(match.group("time"))

    if not MIN_SERVO_ID <= servo_id <= MAX_SERVO_ID:
        raise ValueError(f"servo id must be between {MIN_SERVO_ID:03d} and {MAX_SERVO_ID:03d}")
    if not MIN_PWM <= pwm <= MAX_PWM:
        raise ValueError(f"PWM must be between {MIN_PWM:04d} and {MAX_PWM:04d}")
    if not MIN_TIME_MS <= time_ms <= MAX_TIME_MS:
        raise ValueError(f"TIME must be between {MIN_TIME_MS:04d} and {MAX_TIME_MS:04d}")


def validate_command_frame(command: str) -> str:
    stripped = command.strip()
    if not stripped:
        raise ValueError("servo command must not be empty")

    if stripped.startswith("{") or stripped.endswith("}"):
        if not (stripped.startswith("{") and stripped.endswith("}")):
            raise ValueError("multi-servo command must wrap the full command in {}")
        inner = stripped[1:-1]
        parts = SINGLE_COMMAND_RE.findall(inner)
        matches = list(SINGLE_COMMAND_RE.finditer(inner))
        if len(matches) < 2:
            raise ValueError("multi-servo command must contain at least two single-servo frames inside {}")
        rebuilt = "".join(match.group(0) for match in matches)
        if rebuilt != inner:
            raise ValueError("multi-servo command contains invalid characters or malformed frame boundaries")
        for match in matches:
            _validate_single_command(match.group(0))
        return stripped

    _validate_single_command(stripped)
    return stripped
