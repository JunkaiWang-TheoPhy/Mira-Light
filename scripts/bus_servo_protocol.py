#!/usr/bin/env python3
"""Helpers for formatting Mira Light bus-servo commands."""

from __future__ import annotations


MIN_SERVO_ID = 0
MAX_SERVO_ID = 254
MIN_PWM = 500
MAX_PWM = 2500
MIN_TIME_MS = 0
MAX_TIME_MS = 9999


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
