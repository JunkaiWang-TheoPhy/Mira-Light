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

    def test_prepare_command_prefers_hp_then_beosound_then_builtin(self) -> None:
        player = AudioCuePlayer(dry_run=True)

        def fake_find(name: str) -> str | None:
            mapping = {
                "speaker-beosound-use": "/tmp/speaker-beosound-use",
            }
            return mapping.get(name)

        with patch.object(player, "_find_command", side_effect=fake_find):
            command = player._resolve_prepare_command()
        self.assertEqual(command, ["/tmp/speaker-beosound-use"])

    def test_play_command_prefers_builtin_helper_before_afplay(self) -> None:
        def fake_find(name: str) -> str | None:
            mapping = {
                "speaker-builtin-play": "/tmp/speaker-builtin-play",
                "afplay": "/usr/bin/afplay",
            }
            return mapping.get(name)

        with patch.object(self.player, "_find_command", side_effect=fake_find):
            command = self.player._build_play_command(Path("/tmp/test.wav"))
        self.assertEqual(command, ["/tmp/speaker-builtin-play", "/tmp/test.wav"])


if __name__ == "__main__":
    unittest.main()
