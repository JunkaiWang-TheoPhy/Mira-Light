#!/usr/bin/env python3
"""Unit tests for bus-servo protocol formatting."""

from __future__ import annotations

from pathlib import Path
import sys
import unittest


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = REPO_ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from bus_servo_protocol import format_multi_command, format_single_command


class BusServoProtocolTests(unittest.TestCase):
    def test_single_command_zero_pads_everything(self) -> None:
        self.assertEqual(format_single_command("3", 800, 500), "#003P0800T0500!")

    def test_multi_command_wraps_braces(self) -> None:
        command = format_multi_command(
            [
                {"id": "001", "pwm": 2000, "timeMs": 1000},
                {"id": "003", "pwm": 833, "timeMs": 2000},
            ]
        )
        self.assertEqual(command, "{#001P2000T1000!#003P0833T2000!}")


if __name__ == "__main__":
    unittest.main()
