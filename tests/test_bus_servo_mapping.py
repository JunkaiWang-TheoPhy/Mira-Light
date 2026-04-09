#!/usr/bin/env python3
"""Unit tests for bus-servo logical-to-PWM mapping."""

from __future__ import annotations

from pathlib import Path
import sys
import unittest


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = REPO_ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from bus_servo_mapping import BusServoMapper, load_joint_map


class BusServoMappingTests(unittest.TestCase):
    def setUp(self) -> None:
        self.mapper = BusServoMapper(load_joint_map())

    def test_neutral_maps_to_neutral_pwm(self) -> None:
        self.assertEqual(self.mapper.angle_to_pwm("servo4", 90), 1500)

    def test_logical_angle_maps_to_expected_pwm(self) -> None:
        self.assertEqual(self.mapper.angle_to_pwm("servo1", 117), 1700)

    def test_angles_to_commands_uses_joint_ids(self) -> None:
        commands = self.mapper.angles_to_commands({"servo2": 96, "servo4": 90}, 1000)
        self.assertEqual(commands, [{"id": "001", "pwm": 1500, "timeMs": 1000}, {"id": "003", "pwm": 1500, "timeMs": 1000}])


if __name__ == "__main__":
    unittest.main()
