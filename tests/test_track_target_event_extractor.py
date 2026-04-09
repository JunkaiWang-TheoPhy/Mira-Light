from __future__ import annotations

import argparse
import unittest

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = ROOT / "scripts"

if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from track_target_event_extractor import ExtractorState, build_event, choose_selected_target, hold_selected_target


class DummyFrame:
    shape = (120, 200, 3)


class TrackTargetEventExtractorTest(unittest.TestCase):
    def make_args(self) -> argparse.Namespace:
        return argparse.Namespace(
            face_near_area_ratio=0.10,
            face_mid_area_ratio=0.03,
            motion_near_area_ratio=0.18,
            motion_mid_area_ratio=0.06,
            hold_missing_frames=3,
        )

    def test_multi_target_payload_promotes_to_multi_person_scene(self) -> None:
        event = build_event(
            path=ROOT / "fixtures" / "vision_events" / "multi_person_left_right.json",
            frame=DummyFrame(),
            bbox=(10, 10, 50, 60),
            detector="haar_face",
            target_class="person",
            confidence=0.92,
            state=ExtractorState(last_target_present=True),
            args=self.make_args(),
            target_count=2,
            multi_target_payload={"primaryDirection": "left", "secondaryDirection": "right", "targetCount": 2},
        )

        self.assertEqual(event["event_type"], "multi_target_seen")
        self.assertEqual(event["scene_hint"]["name"], "multi_person_demo")
        self.assertEqual(event["tracking"]["target_count"], 2)
        self.assertEqual(event["payload"]["primaryDirection"], "left")
        self.assertEqual(event["payload"]["secondaryDirection"], "right")

    def test_hold_selected_target_keeps_recent_target_alive_for_short_occlusion(self) -> None:
        state = ExtractorState(
            last_target_present=True,
            missing_frame_count=2,
            last_selected_target={
                "track_id": 7,
                "lock_state": "locked",
                "reason": "previous selected target still visible",
                "target_class": "person",
                "detector": "haar_face",
                "confidence": 0.92,
                "bbox_norm": {"x": 0.4, "y": 0.2, "w": 0.2, "h": 0.3},
                "center_norm": {"x": 0.5, "y": 0.35},
                "horizontal_zone": "center",
                "vertical_zone": "middle",
                "size_norm": 0.06,
                "distance_band": "mid",
                "approach_state": "stable",
                "selection_score": 1.1,
            },
        )

        held = hold_selected_target(state, self.make_args())

        self.assertIsNotNone(held)
        self.assertEqual(held["track_id"], 7)
        self.assertEqual(held["lock_state"], "held")
        self.assertIn("short occlusion hold", held["reason"])
        self.assertLess(float(held["confidence"]), 0.92)

    def test_operator_lock_prefers_requested_track_when_visible(self) -> None:
        state = ExtractorState(selected_track_id=3)
        tracks = [
            {
                "track_id": 3,
                "detector": "haar_face",
                "target_class": "person",
                "confidence": 0.88,
                "center_norm": {"x": 0.2, "y": 0.4},
                "selection_score": 1.0,
            },
            {
                "track_id": 8,
                "detector": "haar_face",
                "target_class": "person",
                "confidence": 0.91,
                "center_norm": {"x": 0.65, "y": 0.38},
                "selection_score": 1.2,
            },
        ]

        selected = choose_selected_target(
            tracks,
            state,
            operator_state={"lockSelectedTrackId": 8},
        )

        self.assertIsNotNone(selected)
        self.assertEqual(selected["track_id"], 8)
        self.assertEqual(selected["lock_state"], "operator_locked")


if __name__ == "__main__":
    unittest.main()
