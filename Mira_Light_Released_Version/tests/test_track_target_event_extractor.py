from __future__ import annotations

import argparse
import unittest

import sys
from pathlib import Path

import cv2
import numpy as np


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = ROOT / "scripts"

if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from track_target_event_extractor import (
    ExtractorState,
    build_event,
    build_person_candidates,
    choose_selected_target,
    detect_hand_arm_cue,
    hold_selected_target,
)


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
            standalone_hog_min_confidence=0.72,
            hand_cue_min_area_ratio=0.0015,
            hand_cue_max_area_ratio=0.06,
            hand_cue_min_center_y=0.34,
            hand_cue_min_motion_ratio=0.12,
            hand_cue_min_confidence=0.55,
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

    def test_detect_hand_arm_cue_finds_moving_skin_blob_in_lower_region(self) -> None:
        frame = np.zeros((120, 200, 3), dtype=np.uint8)
        frame[60:96, 126:166] = (80, 120, 180)
        fg_mask = np.zeros((120, 200), dtype=np.uint8)
        fg_mask[58:100, 122:170] = 255

        cue = detect_hand_arm_cue(
            frame,
            fg_mask,
            selected_target=None,
            warmup_count=10,
            warmup_frames=3,
            args=self.make_args(),
        )

        self.assertIsNotNone(cue)
        self.assertTrue(cue["hand_arm_present"])
        self.assertEqual(cue["detector"], "skin_motion_hand")
        self.assertEqual(cue["horizontal_zone"], "right")

    def test_detect_hand_arm_cue_rejects_static_skin_blob_without_motion(self) -> None:
        frame = np.zeros((120, 200, 3), dtype=np.uint8)
        frame[60:96, 126:166] = (80, 120, 180)
        fg_mask = np.zeros((120, 200), dtype=np.uint8)

        cue = detect_hand_arm_cue(
            frame,
            fg_mask,
            selected_target=None,
            warmup_count=10,
            warmup_frames=3,
            args=self.make_args(),
        )

        self.assertIsNone(cue)

    def test_detect_hand_arm_cue_rejects_upper_right_skin_blob_when_no_target(self) -> None:
        frame = np.zeros((120, 200, 3), dtype=np.uint8)
        frame[36:72, 164:194] = (80, 120, 180)
        fg_mask = np.zeros((120, 200), dtype=np.uint8)
        fg_mask[34:76, 160:198] = 255

        cue = detect_hand_arm_cue(
            frame,
            fg_mask,
            selected_target=None,
            warmup_count=10,
            warmup_frames=3,
            args=self.make_args(),
        )

        self.assertIsNone(cue)

    def test_build_person_candidates_counts_two_people_from_two_face_cues(self) -> None:
        candidates = build_person_candidates(
            face_detections=[((20, 12, 28, 32), 0.92), ((132, 18, 26, 30), 0.88)],
            upperbody_detections=[],
            hog_detections=[],
            frame_width=200,
            frame_height=120,
            previous_size_norm=None,
            standalone_hog_min_confidence=0.72,
        )

        self.assertEqual(len(candidates), 2)
        self.assertEqual(candidates[0]["target_class"], "person")
        self.assertIn(candidates[0]["detector"], {"haar_face", "hog_person"})

    def test_build_person_candidates_merges_face_and_upperbody_for_same_person(self) -> None:
        candidates = build_person_candidates(
            face_detections=[((72, 10, 26, 30), 0.92)],
            upperbody_detections=[((55, 8, 64, 92), 0.72)],
            hog_detections=[],
            frame_width=200,
            frame_height=120,
            previous_size_norm=None,
            standalone_hog_min_confidence=0.72,
        )

        self.assertEqual(len(candidates), 1)
        self.assertEqual(candidates[0]["detector"], "haar_face")
        self.assertGreaterEqual(float(candidates[0]["confidence"]), 0.9)

    def test_build_person_candidates_rejects_weak_standalone_hog_false_positive(self) -> None:
        candidates = build_person_candidates(
            face_detections=[],
            upperbody_detections=[],
            hog_detections=[((16, 2, 18, 42), 0.66)],
            frame_width=200,
            frame_height=120,
            previous_size_norm=None,
            standalone_hog_min_confidence=0.72,
        )

        self.assertEqual(candidates, [])

    def test_build_person_candidates_merges_split_vertical_face_cues_for_same_person(self) -> None:
        candidates = build_person_candidates(
            face_detections=[
                ((92, 10, 28, 30), 0.92),
                ((100, 62, 34, 34), 0.88),
                ((18, 54, 30, 32), 0.9),
            ],
            upperbody_detections=[],
            hog_detections=[],
            frame_width=200,
            frame_height=120,
            previous_size_norm=None,
            standalone_hog_min_confidence=0.72,
        )

        self.assertEqual(len(candidates), 2)


if __name__ == "__main__":
    unittest.main()
