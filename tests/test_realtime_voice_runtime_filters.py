from __future__ import annotations

import argparse
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = ROOT / "scripts"

if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from mira_realtime_voice_interaction import (
    DEFAULT_API_SYSTEM_PROMPT,
    apply_latency_preset,
    build_low_latency_system_prompt,
    low_energy_skip_reason,
    normalize_reply_text,
    repetitive_transcript_details,
)
from mira_voice_intents import is_brief_greeting, should_skip_short_reply


class RealtimeVoiceRuntimeFiltersTest(unittest.TestCase):
    def test_low_latency_preset_reduces_wait_but_keeps_small_profile(self) -> None:
        args = argparse.Namespace(
            latency_preset="low",
            vad_start_ms=150,
            vad_end_ms=650,
            history_turns=4,
            profile="small",
            api_system_prompt=DEFAULT_API_SYSTEM_PROMPT,
            startup_warmup=None,
            keep_warm_seconds=0.0,
        )
        applied = apply_latency_preset(args)
        self.assertEqual(args.vad_start_ms, 100)
        self.assertEqual(args.vad_end_ms, 400)
        self.assertEqual(args.history_turns, 2)
        self.assertEqual(args.profile, "small")
        self.assertTrue(args.startup_warmup)
        self.assertEqual(args.keep_warm_seconds, 90.0)
        self.assertEqual(applied["preset"], "low")

    def test_low_latency_prompt_hint_prefers_short_replies(self) -> None:
        prompt = build_low_latency_system_prompt(DEFAULT_API_SYSTEM_PROMPT)
        self.assertIn("低延迟回复策略", prompt)
        self.assertIn("完整、自然的短句", prompt)

    def test_brief_greeting_is_detected(self) -> None:
        self.assertTrue(is_brief_greeting("你好。"))
        self.assertTrue(is_brief_greeting("hello!"))

    def test_non_greeting_is_not_detected_as_brief_greeting(self) -> None:
        self.assertFalse(is_brief_greeting("你好，我今天有点累。"))
        self.assertFalse(is_brief_greeting("你是谁"))

    def test_short_low_information_chat_is_skipped(self) -> None:
        self.assertTrue(should_skip_short_reply("嗯。", intent="chat"))
        self.assertTrue(should_skip_short_reply("啊", intent="chat"))

    def test_short_meaningful_transcript_is_not_skipped(self) -> None:
        self.assertFalse(should_skip_short_reply("你好。", intent="chat"))
        self.assertFalse(should_skip_short_reply("拜拜", intent="farewell"))

    def test_single_character_transcript_is_skipped_even_if_meaningful(self) -> None:
        self.assertTrue(should_skip_short_reply("唉", intent="sigh"))
        self.assertTrue(should_skip_short_reply("嗨", intent="chat"))

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

    def test_instructional_reply_prefix_and_markdown_are_removed(self) -> None:
        text, flags = normalize_reply_text('你可以直接回： **“你可以叫我米拉，是一个温柔陪伴你的助手。”**')
        self.assertEqual(text, "你可以叫我米拉，是一个温柔陪伴你的助手。")
        self.assertTrue(flags["markdownStripped"])
        self.assertTrue(flags["instructionalPrefixStripped"])

    def test_normal_reply_text_is_preserved(self) -> None:
        text, flags = normalize_reply_text("你好呀，我在这里。")
        self.assertEqual(text, "你好呀，我在这里。")
        self.assertFalse(flags["instructionalPrefixStripped"])


if __name__ == "__main__":
    unittest.main()
