from __future__ import annotations

import unittest
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = ROOT / "scripts"

if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from mira_light_signal_contract import (
    HEAD_CAPACITIVE_FIELD,
    build_led_status_payload,
    build_servo_status_list,
    normalize_binary_signal,
    normalize_vector_pixels,
)


class MiraLightSignalContractTest(unittest.TestCase):
    def test_normalize_vector_pixels_accepts_rgb_and_rgba_entries(self) -> None:
        raw_pixels = [{"r": 10, "g": 20, "b": 30}] * 39 + [[1, 2, 3, 90]]
        normalized = normalize_vector_pixels(
            raw_pixels,
            pixel_count=40,
            default_brightness=180,
        )
        self.assertEqual(len(normalized), 40)
        self.assertEqual(normalized[0], {"r": 10, "g": 20, "b": 30, "brightness": 180})
        self.assertEqual(normalized[-1], {"r": 1, "g": 2, "b": 3, "brightness": 90})

    def test_normalize_vector_pixels_rejects_wrong_pixel_count(self) -> None:
        with self.assertRaisesRegex(ValueError, "exactly 40"):
            normalize_vector_pixels([[255, 0, 0, 180]] * 39, pixel_count=40, default_brightness=180)

    def test_build_led_status_payload_exposes_pixel_signals(self) -> None:
        payload = build_led_status_payload(
            mode="vector",
            brightness=180,
            color={"r": 255, "g": 255, "b": 255},
            pixels=[{"r": 8, "g": 16, "b": 24, "brightness": 90}] * 40,
            led_count=40,
            pin=2,
        )
        self.assertEqual(payload["pixelSignals"][0], [8, 16, 24, 90])
        self.assertEqual(payload["pixels"][0], {"r": 8, "g": 16, "b": 24})

    def test_normalize_binary_signal_keeps_head_capacitive_binary(self) -> None:
        self.assertEqual(normalize_binary_signal(1, field_name=HEAD_CAPACITIVE_FIELD), 1)
        with self.assertRaisesRegex(ValueError, "must be 0 or 1"):
            normalize_binary_signal(2, field_name=HEAD_CAPACITIVE_FIELD)

    def test_build_servo_status_list_preserves_layout_metadata(self) -> None:
        payload = build_servo_status_list(
            servos={"servo1": 90, "servo4": 70},
            servo_layout=[
                {"id": 1, "name": "servo1", "pin": 18},
                {"id": 2, "name": "servo2", "pin": 13},
                {"id": 4, "name": "servo4", "pin": 15},
            ],
            extra_fields={"estimated": True},
        )
        self.assertEqual(
            payload,
            [
                {"id": 1, "name": "servo1", "pin": 18, "angle": 90, "estimated": True},
                {"id": 4, "name": "servo4", "pin": 15, "angle": 70, "estimated": True},
            ],
        )


if __name__ == "__main__":
    unittest.main()
