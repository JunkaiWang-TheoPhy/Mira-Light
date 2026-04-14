#!/usr/bin/env python3
"""Map logical Mira Light servo angles to bus-servo PWM targets."""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path


DEFAULT_JOINT_MAP_PATH = Path(__file__).resolve().parents[1] / "config" / "bus_servo_joint_map.json"


@dataclass(frozen=True)
class JointMapping:
    name: str
    servo_id: str
    label: str
    logical_neutral: int
    logical_min: int
    logical_max: int
    neutral_pwm: int
    pwm_min: int
    pwm_max: int
    direction_sign: int


def load_joint_map(config_path: Path = DEFAULT_JOINT_MAP_PATH) -> dict[str, JointMapping]:
    raw = json.loads(config_path.read_text(encoding="utf-8"))
    mappings: dict[str, JointMapping] = {}
    for name, payload in raw.items():
        mappings[name] = JointMapping(
            name=name,
            servo_id=str(payload["id"]),
            label=str(payload.get("label", name)),
            logical_neutral=int(payload["logicalNeutral"]),
            logical_min=int(payload["logicalMin"]),
            logical_max=int(payload["logicalMax"]),
            neutral_pwm=int(payload["neutralPwm"]),
            pwm_min=int(payload["pwmMin"]),
            pwm_max=int(payload["pwmMax"]),
            direction_sign=int(payload.get("directionSign", 1) or 1),
        )
    return mappings


class BusServoMapper:
    def __init__(self, mappings: dict[str, JointMapping] | None = None, *, config_path: Path = DEFAULT_JOINT_MAP_PATH):
        self.mappings = mappings or load_joint_map(config_path)

    def angle_to_pwm(self, joint_name: str, logical_angle: int) -> int:
        mapping = self._mapping(joint_name)
        clamped_angle = max(mapping.logical_min, min(mapping.logical_max, int(logical_angle)))
        logical_delta = clamped_angle - mapping.logical_neutral
        pwm_delta = round((logical_delta / 135.0) * 1000)
        target_pwm = mapping.neutral_pwm + (mapping.direction_sign * pwm_delta)
        return max(mapping.pwm_min, min(mapping.pwm_max, int(target_pwm)))

    def angles_to_commands(self, angles: dict[str, int], time_ms: int) -> list[dict[str, int | str]]:
        commands: list[dict[str, int | str]] = []
        for joint_name, logical_angle in angles.items():
            mapping = self._mapping(joint_name)
            commands.append(
                {
                    "id": mapping.servo_id,
                    "pwm": self.angle_to_pwm(joint_name, logical_angle),
                    "timeMs": int(time_ms),
                }
            )
        return commands

    def _mapping(self, joint_name: str) -> JointMapping:
        if joint_name not in self.mappings:
            raise KeyError(f"unknown joint mapping: {joint_name}")
        return self.mappings[joint_name]
