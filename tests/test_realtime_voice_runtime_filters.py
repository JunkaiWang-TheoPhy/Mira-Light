from __future__ import annotations

import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = ROOT / "scripts"

if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from mira_realtime_voice_interaction import low_energy_skip_reason, repetitive_transcript_details


class RealtimeVoiceRuntimeFiltersTest(unittest.TestCase):
    def test_low_energy_continuous_utterance_is_skipped(self) -> None:
        reason = low_energy_skip_reason(
            {"captureMode": "continuous"},
            {"durationMs": 1269.0, "rms": 0.003872, "peak": 0.032471},
        )
        self.assertEqual(reason, "low-energy-utterance")

    def test_ptt_utterance_is_not_skipped_by_low_energy_rule(self) -> None:
        reason = low_energy_skip_reason(
            {"captureMode": "ptt"},
            {"durationMs": 1269.0, "rms": 0.003872, "peak": 0.032471},
        )
        self.assertIsNone(reason)

    def test_repetitive_transcript_is_detected(self) -> None:
        payload = {
            "text": "请" * 223,
            "segments": [
                {
                    "start": 0.0,
                    "end": 0.61,
                    "compression_ratio": 37.1666,
                }
            ],
        }
        details = repetitive_transcript_details(
            payload,
            audio_metrics={"durationMs": 619.0, "rms": 0.043194, "peak": 0.235138},
        )
        self.assertIsNotNone(details)
        assert details is not None
        self.assertEqual(details["reason"], "repetitive-transcript")
        self.assertEqual(details["dominantChar"], "请")

    def test_normal_transcript_is_not_flagged(self) -> None:
        payload = {
            "text": "你好，我们继续聊吧。",
            "segments": [
                {
                    "start": 0.0,
                    "end": 1.2,
                    "compression_ratio": 1.2,
                }
            ],
        }
        details = repetitive_transcript_details(
            payload,
            audio_metrics={"durationMs": 1200.0, "rms": 0.016747, "peak": 0.117035},
        )
        self.assertIsNone(details)

    def test_repeated_word_transcript_is_detected(self) -> None:
        payload = {
            "text": "有 " + " ".join(["lawmakers"] * 23),
            "segments": [
                {
                    "start": 0.0,
                    "end": 1.4,
                    "compression_ratio": 12.0,
                }
            ],
        }
        details = repetitive_transcript_details(
            payload,
            audio_metrics={"durationMs": 1400.0, "rms": 0.025, "peak": 0.12},
        )
        self.assertIsNotNone(details)
        assert details is not None
        self.assertEqual(details["reason"], "repetitive-transcript")
        self.assertEqual(details["mode"], "token")
        self.assertEqual(details["dominantToken"], "lawmakers")


if __name__ == "__main__":
    unittest.main()
