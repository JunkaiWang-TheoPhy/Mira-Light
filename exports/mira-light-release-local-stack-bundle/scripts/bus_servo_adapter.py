#!/usr/bin/env python3
"""Bridge logical four-joint commands to Mira Light bus-servo strings."""

from __future__ import annotations

from copy import deepcopy
from typing import Any

from bus_servo_mapping import BusServoMapper
from bus_servo_protocol import clamp_time_ms, format_multi_command
from bus_servo_transport import (
    BusServoRuntimeConfig,
    BusServoTransport,
    DryRunBusServoTransport,
    TcpBusServoTransport,
)


SERVO_NAMES = ("servo1", "servo2", "servo3", "servo4")


class BusServoAdapter:
    def __init__(
        self,
        *,
        mapper: BusServoMapper | None = None,
        transport: BusServoTransport | None = None,
        runtime_config: BusServoRuntimeConfig | None = None,
    ):
        self.runtime_config = runtime_config or BusServoRuntimeConfig.from_file()
        self.mapper = mapper or BusServoMapper()
        self.transport = transport or TcpBusServoTransport.from_runtime_config(self.runtime_config)
        self._last_command: str | None = None
        self._current_angles: dict[str, int | None] = {name: None for name in SERVO_NAMES if name in self.mapper.mappings}

    @classmethod
    def dry_run(cls) -> "BusServoAdapter":
        return cls(transport=DryRunBusServoTransport())

    def sync_angles(self, angles: dict[str, int | None]) -> None:
        for name, value in angles.items():
            if name in self._current_angles:
                self._current_angles[name] = None if value is None else int(value)

    def current_angles(self) -> dict[str, int | None]:
        return deepcopy(self._current_angles)

    def last_command(self) -> str | None:
        return self._last_command

    def send_angles(self, angles: dict[str, int], *, move_ms: int | None = None, source: str = "direct") -> dict[str, Any]:
        resolved_move_ms = clamp_time_ms(move_ms or self.runtime_config.default_move_ms, self.runtime_config.max_move_ms)
        commands = self.mapper.angles_to_commands(angles, resolved_move_ms)
        command = format_multi_command(commands)
        result = self.transport.send(command)
        self._last_command = command
        self.sync_angles(angles)
        return {
            "ok": True,
            "source": source,
            "moveMs": resolved_move_ms,
            "angles": {key: int(value) for key, value in angles.items()},
            "command": command,
            "transport": result,
        }

    def apply_control_payload(self, payload: dict[str, Any], *, move_ms: int | None = None, source: str = "control") -> dict[str, Any]:
        if not isinstance(payload, dict):
            raise TypeError("payload must be a dict")
        mode = str(payload.get("mode", "relative")).strip().lower()
        if mode not in {"absolute", "relative"}:
            raise ValueError(f"unsupported mode: {mode}")

        if mode == "absolute":
            angles = {name: int(payload[name]) for name in SERVO_NAMES if name in payload}
            return self.send_angles(angles, move_ms=move_ms, source=source)

        next_angles: dict[str, int] = {}
        for name in SERVO_NAMES:
            if name not in payload:
                continue
            current = self._current_angles.get(name)
            if current is None:
                raise RuntimeError(f"{name} current angle is unknown; sync or send absolute first")
            next_angles[name] = int(current) + int(payload[name])
        return self.send_angles(next_angles, move_ms=move_ms, source=source)

    def apply_decision(self, decision: Any, *, move_ms: int | None = None, source: str | None = None) -> dict[str, Any]:
        state_after = getattr(decision, "state_after", None)
        if not isinstance(state_after, dict):
            raise TypeError("decision.state_after must be a dict of resolved logical angles")
        angles = {name: int(value) for name, value in state_after.items() if name in self.mapper.mappings and value is not None}
        return self.send_angles(angles, move_ms=move_ms, source=source or getattr(decision, "source", "decision"))
