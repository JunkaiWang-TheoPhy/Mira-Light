#!/usr/bin/env python3
"""Unit tests for the bus-servo adapter."""

from __future__ import annotations

from pathlib import Path
import sys
import unittest


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = REPO_ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from bus_servo_adapter import BusServoAdapter
from bus_servo_transport import DryRunBusServoTransport, DEFAULT_RDK_X5_HOST, DEFAULT_RDK_X5_PORT


class _Decision:
    def __init__(self, state_after: dict[str, int], source: str = "unit"):
        self.state_after = state_after
        self.source = source


class BusServoAdapterTests(unittest.TestCase):
    def test_absolute_payload_formats_multi_command(self) -> None:
        transport = DryRunBusServoTransport()
        adapter = BusServoAdapter(transport=transport)
        result = adapter.apply_control_payload({"mode": "absolute", "servo1": 90, "servo4": 90}, move_ms=1000)
        self.assertEqual(result["command"], "{#000P1500T1000!#003P1500T1000!}")
        self.assertEqual(result["transport"]["host"], DEFAULT_RDK_X5_HOST)
        self.assertEqual(result["transport"]["port"], DEFAULT_RDK_X5_PORT)

    def test_relative_payload_requires_synced_state(self) -> None:
        adapter = BusServoAdapter(transport=DryRunBusServoTransport())
        with self.assertRaises(RuntimeError):
            adapter.apply_control_payload({"mode": "relative", "servo4": 4}, move_ms=300)

    def test_apply_decision_uses_state_after(self) -> None:
        adapter = BusServoAdapter(transport=DryRunBusServoTransport())
        result = adapter.apply_decision(_Decision({"servo4": 90}), move_ms=1000)
        self.assertEqual(result["command"], "#003P1500T1000!")


if __name__ == "__main__":
    unittest.main()
