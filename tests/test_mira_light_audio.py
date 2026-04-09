from __future__ import annotations

from pathlib import Path
import sys
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from mira_light_audio import AudioCuePlayer


class MiraLightAudioVoicePresetTests(unittest.TestCase):
    def setUp(self) -> None:
        self.player = AudioCuePlayer(dry_run=True)

    def test_gentle_sister_mode_uses_expected_preset(self) -> None:
        with patch.object(self.player, "_find_command", return_value="/tmp/speaker-hp-tts-play"):
            command = self.player._build_speech_command("你好", voice="gentle_sister")
        self.assertEqual(
            command,
            [
                "/tmp/speaker-hp-tts-play",
                "--voice",
                "zh-CN-XiaoyiNeural",
                "--lang",
                "zh-CN",
                "--rate",
                "-12%",
                "--pitch",
                "-20%",
                "你好",
            ],
        )

    def test_warm_gentleman_mode_uses_expected_preset(self) -> None:
        with patch.object(self.player, "_find_command", return_value="/tmp/speaker-hp-tts-play"):
            command = self.player._build_speech_command("你好", voice="warm_gentleman")
        self.assertEqual(
            command,
            [
                "/tmp/speaker-hp-tts-play",
                "--voice",
                "zh-CN-YunxiNeural",
                "--lang",
                "zh-CN",
                "--rate",
                "-6%",
                "--pitch",
                "-6%",
                "你好",
            ],
        )

    def test_legacy_alias_resolves_to_gentle_sister(self) -> None:
        with patch.object(self.player, "_find_command", return_value="/tmp/speaker-hp-tts-play"):
            command = self.player._build_speech_command("你好", voice="female")
        self.assertEqual(command[2], "zh-CN-XiaoyiNeural")
        self.assertEqual(command[8], "-20%")


if __name__ == "__main__":
    unittest.main()
