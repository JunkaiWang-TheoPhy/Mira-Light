import tempfile
import unittest
from pathlib import Path

import sys


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = ROOT / "scripts"

if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from audio_cue_player import AudioCuePlayer


class AudioCuePlayerTest(unittest.TestCase):
    def test_resolves_legacy_mp3_name_to_wav_asset(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            cue_root = Path(tmpdir)
            (cue_root / "dance.wav").write_bytes(b"RIFFdemo")
            player = AudioCuePlayer(cue_root=cue_root, dry_run=True)
            result = player.play("dance.mp3")
            self.assertTrue(result["ok"])
            self.assertEqual(result["reason"], "dry_run")
            self.assertEqual(Path(result["resolvedAsset"]).name, "dance.wav")

    def test_missing_asset_is_reported_cleanly(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            player = AudioCuePlayer(cue_root=Path(tmpdir), dry_run=True)
            result = player.play("missing.mp3")
            self.assertFalse(result["ok"])
            self.assertEqual(result["reason"], "asset_not_found")
            self.assertIsNone(result["resolvedAsset"])


if __name__ == "__main__":
    unittest.main()
