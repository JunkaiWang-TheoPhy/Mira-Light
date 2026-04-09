from __future__ import annotations

import unittest

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = ROOT / "scripts"

if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from mira_voice_intents import bridge_payload_for_intent, classify_intent


class RealtimeVoiceTriggerFlowTest(unittest.TestCase):
    def test_tired_transcript_maps_to_voice_tired_path(self) -> None:
        intent = classify_intent("我今天好累啊")
        self.assertEqual(intent, "comfort")
        payload = bridge_payload_for_intent(intent, "我今天好累啊")
        self.assertEqual(payload["source"], "voice-realtime")
        self.assertEqual(payload["transcript"], "我今天好累啊")

    def test_sigh_transcript_maps_to_sigh_path(self) -> None:
        intent = classify_intent("唉")
        self.assertEqual(intent, "sigh")
        payload = bridge_payload_for_intent(intent, "唉")
        self.assertEqual(payload["source"], "voice-realtime")
        self.assertEqual(payload["transcript"], "唉")

    def test_farewell_payload_keeps_center_direction_default(self) -> None:
        intent = classify_intent("拜拜")
        self.assertEqual(intent, "farewell")
        payload = bridge_payload_for_intent(intent, "拜拜")
        self.assertEqual(payload["direction"], "center")


if __name__ == "__main__":
    unittest.main()
