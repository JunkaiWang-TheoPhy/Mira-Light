from __future__ import annotations

import math
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
import wave

import sys


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = ROOT / "scripts"

if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from mic_event_bridge import analyze_sigh_audio, classify_transcript_event, load_wav_mono
from mira_voice_intents import action_for_intent, classify_intent


def write_sine_wav(path: Path, *, freq_hz: float, duration_s: float, sample_rate: int = 16000, amplitude: float = 0.25) -> None:
    frame_count = int(sample_rate * duration_s)
    path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(path), "wb") as handle:
        handle.setnchannels(1)
        handle.setsampwidth(2)
        handle.setframerate(sample_rate)
        frames = bytearray()
        for index in range(frame_count):
            sample = math.sin((2.0 * math.pi * freq_hz * index) / sample_rate)
            value = int(max(-1.0, min(1.0, sample * amplitude)) * 32767)
            frames.extend(int(value).to_bytes(2, byteorder="little", signed=True))
        handle.writeframes(bytes(frames))


class MicEventBridgeTest(unittest.TestCase):
    def test_voice_intent_mapping_distinguishes_tired_and_sigh(self) -> None:
        self.assertEqual(classify_intent("我今天好累啊"), "comfort")
        self.assertEqual(action_for_intent("comfort"), {"type": "trigger", "name": "voice_tired"})
        self.assertEqual(classify_intent("唉"), "sigh")
        self.assertEqual(action_for_intent("sigh"), {"type": "trigger", "name": "sigh_detected"})

    def test_classify_transcript_event_maps_to_bridge_trigger(self) -> None:
        tired = classify_transcript_event("我今天好累啊")
        self.assertEqual(tired["event"], "voice_tired")
        self.assertEqual(tired["triggerPayload"]["transcript"], "我今天好累啊")

        sigh = classify_transcript_event("唉")
        self.assertEqual(sigh["event"], "sigh_detected")
        self.assertEqual(sigh["triggerPayload"]["transcript"], "唉")

    def test_analyze_sigh_audio_accepts_low_frequency_long_exhale(self) -> None:
        with TemporaryDirectory() as tmpdir:
            wav_path = Path(tmpdir) / "sigh.wav"
            write_sine_wav(wav_path, freq_hz=8.0, duration_s=1.4, amplitude=0.22)
            samples, sample_rate = load_wav_mono(wav_path)
            analysis = analyze_sigh_audio(
                samples,
                sample_rate=sample_rate,
                min_duration_ms=700,
                min_rms=0.015,
                max_zero_crossing_rate=0.12,
            )
            self.assertTrue(analysis["detected"])
            self.assertEqual(analysis["event"], "sigh_detected")
            self.assertGreaterEqual(analysis["confidence"], 0.5)

    def test_analyze_sigh_audio_rejects_short_higher_frequency_signal(self) -> None:
        with TemporaryDirectory() as tmpdir:
            wav_path = Path(tmpdir) / "speechy.wav"
            write_sine_wav(wav_path, freq_hz=180.0, duration_s=0.28, amplitude=0.18)
            samples, sample_rate = load_wav_mono(wav_path)
            analysis = analyze_sigh_audio(
                samples,
                sample_rate=sample_rate,
                min_duration_ms=700,
                min_rms=0.015,
                max_zero_crossing_rate=0.12,
            )
            self.assertFalse(analysis["detected"])
            self.assertEqual(analysis["event"], "none")


if __name__ == "__main__":
    unittest.main()
