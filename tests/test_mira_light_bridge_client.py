#!/usr/bin/env python3
"""Unit tests for the reusable Mira Light bridge client."""

from __future__ import annotations

from pathlib import Path
import sys
import unittest
from unittest import mock


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from tools.mira_light_bridge.bridge_client import MiraLightBridgeClient


class MiraLightBridgeClientTests(unittest.TestCase):
    def setUp(self) -> None:
        self.client = MiraLightBridgeClient(base_url="http://127.0.0.1:9783", token="test-token")

    def test_run_scene_uses_expected_payload(self) -> None:
        with mock.patch.object(self.client, "_request", return_value={"ok": True}) as patched:
            self.client.run_scene(
                "farewell",
                async_run=False,
                context={"departureDirection": "left"},
                cue_mode="director",
                allow_unavailable=True,
            )

        patched.assert_called_once_with(
            "POST",
            "/v1/mira-light/run-scene",
            {
                "scene": "farewell",
                "async": False,
                "context": {"departureDirection": "left"},
                "cueMode": "director",
                "allowUnavailable": True,
            },
        )

    def test_control_joints_omits_none_fields(self) -> None:
        with mock.patch.object(self.client, "_request", return_value={"ok": True}) as patched:
            self.client.control_joints(mode="absolute", servo1=90, servo4=92)

        patched.assert_called_once_with(
            "POST",
            "/v1/mira-light/control",
            {"mode": "absolute", "servo1": 90, "servo4": 92},
        )

    def test_set_servo_meta_uses_bridge_field_names(self) -> None:
        with mock.patch.object(self.client, "_request", return_value={"ok": True}) as patched:
            self.client.set_servo_meta(
                "servo2",
                neutral=96,
                hard_range=[0, 180],
                rehearsal_range=[78, 112],
                verified=True,
            )

        patched.assert_called_once_with(
            "POST",
            "/v1/mira-light/profile/set-servo-meta",
            {
                "servo": "servo2",
                "neutral": 96,
                "hardRange": [0, 180],
                "rehearsalRange": [78, 112],
                "verified": True,
            },
        )


if __name__ == "__main__":
    unittest.main()
