import argparse
import json
import unittest

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = ROOT / "scripts"

if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from vision_runtime_bridge import BridgeState, handle_event


class FakeRuntime:
    def __init__(self) -> None:
        self.started_scenes: list[str] = []
        self.tracking_events: list[dict] = []
        self.triggered_events: list[dict] = []
        self.dry_run = True

    def get_runtime_state(self) -> dict:
        return {
            "running": False,
            "runningScene": None,
            "trackingActive": False,
        }

    def start_scene(self, scene_name: str) -> None:
        self.started_scenes.append(scene_name)

    def trigger_event(self, event_name: str, payload: dict | None = None) -> dict:
        self.triggered_events.append({"event": event_name, "payload": payload or {}})
        scene_name = {
            "farewell_detected": "farewell",
            "multi_person_detected": "multi_person_demo",
            "hand_near": "touch_affection",
            "hand_avoid_detected": "hand_avoid",
        }.get(event_name, event_name)
        self.started_scenes.append(scene_name)
        return {"runningScene": scene_name, "lastFinishedScene": scene_name}

    def apply_tracking_event(self, event: dict, *, source: str = "vision") -> None:
        self.tracking_events.append({"event": event, "source": source})


class FakeMemoryClient:
    def __init__(self) -> None:
        self.tracking_states: list[dict] = []

    def record_tracking_session_state(self, **payload) -> None:
        self.tracking_states.append(payload)


class VisionRuntimeBridgeTest(unittest.TestCase):
    def make_args(self, **overrides) -> argparse.Namespace:
        defaults = {
            "scene_cooldown_ms": 3500,
            "wake_up_cooldown_ms": 6000,
            "sleep_grace_ms": 4000,
            "tracking_update_ms": 200,
            "scene_persistence_frames": 1,
            "tracking_persistence_frames": 1,
            "scene_min_confidence": 0.70,
            "tracking_min_confidence": 0.50,
            "touch_persistence_frames": 3,
            "touch_cooldown_ms": 9000,
            "touch_min_confidence": 0.72,
            "touch_min_size_norm": 0.085,
            "touch_max_center_offset": 0.32,
            "touch_hand_arm_min_confidence": 0.68,
            "hand_avoid_cooldown_ms": 7000,
            "hand_avoid_min_confidence": 0.78,
            "hand_avoid_max_center_y": 0.74,
            "hand_avoid_extended_max_center_y": 0.86,
            "hand_avoid_extended_min_confidence": 0.90,
            "hand_avoid_min_lateral_offset": 0.18,
            "scene_allowed_detectors": "haar_face",
            "tracking_allowed_detectors": "haar_face,background_motion",
            "touch_allowed_detectors": "haar_face,hog_person",
            "touch_allow_person_fallback": False,
            "log_json": False,
            "memory_session_id": "mira-light-vision",
        }
        defaults.update(overrides)
        return argparse.Namespace(**defaults)

    def load_fixture(self, name: str) -> dict:
        path = ROOT / "fixtures" / "vision_events" / name
        return json.loads(path.read_text(encoding="utf-8"))

    def test_handle_event_writes_tracking_session_state(self) -> None:
        runtime = FakeRuntime()
        memory_client = FakeMemoryClient()
        bridge_state = BridgeState()
        args = self.make_args()

        event = {
            "event_type": "target_seen",
            "scene_hint": {"name": "track_target"},
            "tracking": {
                "target_present": True,
                "detector": "haar_face",
                "confidence": 0.90,
                "horizontal_zone": "left",
                "vertical_zone": "middle",
                "distance_band": "mid",
            },
        }

        handle_event(event, runtime, bridge_state, args, memory_client)

        self.assertTrue(runtime.started_scenes)
        self.assertEqual(runtime.started_scenes[0], "wake_up")
        self.assertEqual(len(memory_client.tracking_states), 1)
        self.assertEqual(memory_client.tracking_states[0]["event_type"], "target_seen")
        self.assertEqual(memory_client.tracking_states[0]["session_id"], "mira-light-vision")

    def test_handle_event_uses_live_tracking_for_track_target_updates(self) -> None:
        runtime = FakeRuntime()
        bridge_state = BridgeState()
        args = self.make_args()
        event = self.load_fixture("track_target_update_right.json")

        handle_event(event, runtime, bridge_state, args, None)

        self.assertFalse(runtime.started_scenes)
        self.assertEqual(len(runtime.tracking_events), 1)
        self.assertEqual(runtime.tracking_events[0]["source"], "vision")
        self.assertEqual(bridge_state.last_decision["action"], "apply_tracking")
        self.assertEqual(bridge_state.last_decision["candidateScene"], "track_target")

    def test_target_lost_triggers_dynamic_farewell_event(self) -> None:
        runtime = FakeRuntime()
        bridge_state = BridgeState(last_target_present=True, last_horizontal_zone="left")
        args = self.make_args(scene_cooldown_ms=0)
        event = self.load_fixture("farewell_left.json")

        handle_event(event, runtime, bridge_state, args, None)

        self.assertEqual(runtime.triggered_events[0]["event"], "farewell_detected")
        self.assertEqual(runtime.triggered_events[0]["payload"]["direction"], "left")
        self.assertIn("farewell", runtime.started_scenes)

    def test_multi_target_event_routes_to_multi_person_trigger(self) -> None:
        runtime = FakeRuntime()
        bridge_state = BridgeState()
        args = self.make_args(scene_cooldown_ms=0)
        event = self.load_fixture("multi_person_left_right.json")

        handle_event(event, runtime, bridge_state, args, None)

        self.assertEqual(runtime.triggered_events[0]["event"], "multi_person_detected")
        self.assertEqual(runtime.triggered_events[0]["payload"]["primaryDirection"], "left")
        self.assertEqual(runtime.triggered_events[0]["payload"]["secondaryDirection"], "right")
        self.assertIn("multi_person_demo", runtime.started_scenes)

    def test_low_confidence_motion_blob_does_not_trigger_scene(self) -> None:
        runtime = FakeRuntime()
        bridge_state = BridgeState()
        args = self.make_args(scene_cooldown_ms=0)
        event = {
            "event_type": "target_seen",
            "scene_hint": {"name": "wake_up", "reason": "weak motion blob"},
            "tracking": {
                "target_present": True,
                "detector": "background_motion",
                "target_class": "motion_blob",
                "horizontal_zone": "center",
                "vertical_zone": "middle",
                "distance_band": "mid",
                "confidence": 0.55
            },
            "control_hint": {
                "yaw_error_norm": 0.0,
                "pitch_error_norm": 0.0,
                "lift_intent": 0.5,
                "reach_intent": 0.5
            }
        }

        handle_event(event, runtime, bridge_state, args, None)

        self.assertFalse(runtime.started_scenes)
        self.assertFalse(runtime.tracking_events)
        self.assertEqual(bridge_state.last_decision["action"], "blocked")
        self.assertIn("background_motion", bridge_state.last_decision["sceneGateReason"])

    def test_locked_selected_target_prefers_tracking_over_multi_person_demo(self) -> None:
        runtime = FakeRuntime()
        bridge_state = BridgeState()
        args = self.make_args(scene_cooldown_ms=0)
        event = {
            "event_type": "target_updated",
            "scene_hint": {"name": "track_target", "reason": "selected target moving right"},
            "tracking": {
                "target_present": True,
                "target_count": 2,
                "target_class": "person",
                "detector": "haar_face",
                "horizontal_zone": "left",
                "vertical_zone": "middle",
                "distance_band": "mid",
                "confidence": 0.92,
            },
            "tracks": [
                {
                    "track_id": 3,
                    "target_class": "person",
                    "detector": "haar_face",
                    "confidence": 0.91,
                    "bbox_norm": {"x": 0.12, "y": 0.22, "w": 0.18, "h": 0.26},
                    "center_norm": {"x": 0.21, "y": 0.35},
                    "horizontal_zone": "left",
                    "vertical_zone": "middle",
                    "size_norm": 0.046,
                    "distance_band": "mid",
                    "approach_state": "stable",
                    "selection_score": 1.08
                },
                {
                    "track_id": 4,
                    "target_class": "person",
                    "detector": "haar_face",
                    "confidence": 0.92,
                    "bbox_norm": {"x": 0.60, "y": 0.20, "w": 0.20, "h": 0.28},
                    "center_norm": {"x": 0.70, "y": 0.34},
                    "horizontal_zone": "right",
                    "vertical_zone": "middle",
                    "size_norm": 0.056,
                    "distance_band": "mid",
                    "approach_state": "approaching",
                    "selection_score": 1.25
                }
            ],
            "selected_target": {
                "track_id": 4,
                "lock_state": "locked",
                "reason": "operator selected and still visible",
                "target_class": "person",
                "detector": "haar_face",
                "confidence": 0.92,
                "bbox_norm": {"x": 0.60, "y": 0.20, "w": 0.20, "h": 0.28},
                "center_norm": {"x": 0.70, "y": 0.34},
                "horizontal_zone": "right",
                "vertical_zone": "middle",
                "size_norm": 0.056,
                "distance_band": "mid",
                "approach_state": "approaching",
                "selection_score": 1.25
            },
            "control_hint": {
                "yaw_error_norm": 0.40,
                "pitch_error_norm": -0.16,
                "lift_intent": 0.58,
                "reach_intent": 0.57,
            },
        }

        handle_event(event, runtime, bridge_state, args, None)

        self.assertFalse(runtime.started_scenes)
        self.assertEqual(len(runtime.tracking_events), 1)
        self.assertEqual(runtime.tracking_events[0]["event"]["tracking"]["track_id"], 4)

    def test_near_single_target_triggers_hand_near_touch_scene(self) -> None:
        runtime = FakeRuntime()
        bridge_state = BridgeState()
        args = self.make_args(scene_cooldown_ms=0, touch_persistence_frames=1)
        event = {
            "event_type": "target_updated",
            "scene_hint": {"name": "curious_observe", "reason": "near target lingering in front"},
            "tracking": {
                "target_present": True,
                "target_count": 1,
                "track_id": 7,
                "target_class": "person",
                "detector": "haar_face",
                "horizontal_zone": "center",
                "vertical_zone": "middle",
                "distance_band": "near",
                "approach_state": "stable",
                "size_norm": 0.132,
                "confidence": 0.94,
                "center_norm": {"x": 0.58, "y": 0.42},
            },
            "selected_target": {
                "track_id": 7,
                "lock_state": "candidate",
                "reason": "single confident target",
                "target_class": "person",
                "detector": "haar_face",
                "confidence": 0.94,
                "bbox_norm": {"x": 0.46, "y": 0.20, "w": 0.24, "h": 0.42},
                "center_norm": {"x": 0.58, "y": 0.42},
                "horizontal_zone": "center",
                "vertical_zone": "middle",
                "size_norm": 0.132,
                "distance_band": "near",
                "approach_state": "stable",
                "selection_score": 1.31,
            },
            "interaction_hint": {
                "hand_arm_present": True,
                "detector": "skin_motion_hand",
                "confidence": 0.83,
                "bbox_norm": {"x": 0.51, "y": 0.46, "w": 0.18, "h": 0.18},
                "center_norm": {"x": 0.60, "y": 0.55},
                "horizontal_zone": "center",
                "vertical_zone": "middle",
                "area_ratio": 0.018,
                "motion_ratio": 0.33,
            },
        }

        handle_event(event, runtime, bridge_state, args, None)

        self.assertEqual(len(runtime.triggered_events), 1)
        self.assertEqual(runtime.triggered_events[0]["event"], "hand_near")
        self.assertEqual(runtime.triggered_events[0]["payload"]["side"], "center")
        self.assertIn("touch_affection", runtime.started_scenes)

    def test_multi_target_without_lock_prefers_multi_person_over_hand_near(self) -> None:
        runtime = FakeRuntime()
        bridge_state = BridgeState()
        args = self.make_args(scene_cooldown_ms=0, touch_persistence_frames=1)
        event = {
            "event_type": "multi_target_seen",
            "scene_hint": {"name": "multi_person_demo", "reason": "two targets in booth"},
            "tracking": {
                "target_present": True,
                "target_count": 2,
                "track_id": 3,
                "target_class": "person",
                "detector": "haar_face",
                "horizontal_zone": "center",
                "vertical_zone": "middle",
                "distance_band": "near",
                "approach_state": "stable",
                "size_norm": 0.141,
                "confidence": 0.91,
                "center_norm": {"x": 0.49, "y": 0.39},
            },
            "selected_target": {
                "track_id": 3,
                "lock_state": "candidate",
                "reason": "highest score",
                "target_class": "person",
                "detector": "haar_face",
                "confidence": 0.91,
                "bbox_norm": {"x": 0.35, "y": 0.18, "w": 0.28, "h": 0.46},
                "center_norm": {"x": 0.49, "y": 0.39},
                "horizontal_zone": "center",
                "vertical_zone": "middle",
                "size_norm": 0.141,
                "distance_band": "near",
                "approach_state": "stable",
                "selection_score": 1.28,
            },
            "payload": {"targetCount": 2, "primaryDirection": "left", "secondaryDirection": "right"},
        }

        handle_event(event, runtime, bridge_state, args, None)

        self.assertEqual(len(runtime.triggered_events), 1)
        self.assertEqual(runtime.triggered_events[0]["event"], "multi_person_detected")

    def test_hand_near_respects_touch_cooldown(self) -> None:
        runtime = FakeRuntime()
        bridge_state = BridgeState()
        args = self.make_args(scene_cooldown_ms=0, touch_persistence_frames=1, touch_cooldown_ms=120000)
        event = {
            "event_type": "target_updated",
            "scene_hint": {"name": "curious_observe", "reason": "near target lingering in front"},
            "tracking": {
                "target_present": True,
                "target_count": 1,
                "track_id": 9,
                "target_class": "person",
                "detector": "haar_face",
                "horizontal_zone": "center",
                "vertical_zone": "middle",
                "distance_band": "near",
                "approach_state": "stable",
                "size_norm": 0.145,
                "confidence": 0.95,
                "center_norm": {"x": 0.52, "y": 0.40},
            },
            "selected_target": {
                "track_id": 9,
                "lock_state": "candidate",
                "reason": "single confident target",
                "target_class": "person",
                "detector": "haar_face",
                "confidence": 0.95,
                "bbox_norm": {"x": 0.38, "y": 0.16, "w": 0.28, "h": 0.48},
                "center_norm": {"x": 0.52, "y": 0.40},
                "horizontal_zone": "center",
                "vertical_zone": "middle",
                "size_norm": 0.145,
                "distance_band": "near",
                "approach_state": "stable",
                "selection_score": 1.34,
            },
            "interaction_hint": {
                "hand_arm_present": True,
                "detector": "skin_motion_hand",
                "confidence": 0.86,
                "bbox_norm": {"x": 0.41, "y": 0.48, "w": 0.16, "h": 0.16},
                "center_norm": {"x": 0.49, "y": 0.56},
                "horizontal_zone": "center",
                "vertical_zone": "middle",
                "area_ratio": 0.014,
                "motion_ratio": 0.29,
            },
        }

        handle_event(event, runtime, bridge_state, args, None)
        handle_event(event, runtime, bridge_state, args, None)

        self.assertEqual([item["event"] for item in runtime.triggered_events], ["hand_near"])

    def test_explicit_hand_arm_cue_can_trigger_without_visible_target(self) -> None:
        runtime = FakeRuntime()
        bridge_state = BridgeState()
        args = self.make_args(scene_cooldown_ms=0, touch_persistence_frames=1)
        event = {
            "event_type": "no_target",
            "scene_hint": {"name": "sleep", "reason": "no stable face but hand reaches into interaction zone"},
            "tracking": {
                "target_present": False,
                "target_count": 0,
                "detector": "none",
                "horizontal_zone": "unknown",
                "vertical_zone": "unknown",
                "distance_band": "unknown",
                "approach_state": "unknown",
                "confidence": 0.0,
            },
            "interaction_hint": {
                "hand_arm_present": True,
                "detector": "skin_motion_hand",
                "confidence": 0.88,
                "bbox_norm": {"x": 0.48, "y": 0.50, "w": 0.12, "h": 0.20},
                "center_norm": {"x": 0.54, "y": 0.60},
                "horizontal_zone": "center",
                "vertical_zone": "middle",
                "area_ratio": 0.010,
                "motion_ratio": 0.31,
            },
        }

        handle_event(event, runtime, bridge_state, args, None)

        self.assertEqual(len(runtime.triggered_events), 1)
        self.assertEqual(runtime.triggered_events[0]["event"], "hand_near")
        self.assertIn("touch_affection", runtime.started_scenes)

    def test_side_hand_cue_triggers_hand_avoid_before_touch(self) -> None:
        runtime = FakeRuntime()
        bridge_state = BridgeState()
        args = self.make_args(scene_cooldown_ms=0, touch_persistence_frames=1)
        event = {
            "event_type": "target_updated",
            "scene_hint": {"name": "track_target", "reason": "person is watching while hand enters from the right"},
            "tracking": {
                "target_present": True,
                "target_count": 1,
                "track_id": 11,
                "target_class": "person",
                "detector": "haar_face",
                "horizontal_zone": "right",
                "vertical_zone": "middle",
                "distance_band": "mid",
                "approach_state": "stable",
                "size_norm": 0.061,
                "confidence": 0.88,
                "center_norm": {"x": 0.69, "y": 0.36},
            },
            "selected_target": {
                "track_id": 11,
                "lock_state": "locked",
                "reason": "operator selected and still visible",
                "target_class": "person",
                "detector": "haar_face",
                "confidence": 0.88,
                "bbox_norm": {"x": 0.58, "y": 0.14, "w": 0.18, "h": 0.28},
                "center_norm": {"x": 0.69, "y": 0.36},
                "horizontal_zone": "right",
                "vertical_zone": "middle",
                "size_norm": 0.061,
                "distance_band": "mid",
                "approach_state": "stable",
                "selection_score": 1.21,
            },
            "interaction_hint": {
                "hand_arm_present": True,
                "detector": "skin_motion_hand",
                "confidence": 0.84,
                "bbox_norm": {"x": 0.64, "y": 0.49, "w": 0.08, "h": 0.18},
                "center_norm": {"x": 0.68, "y": 0.58},
                "horizontal_zone": "right",
                "vertical_zone": "middle",
                "area_ratio": 0.006,
                "motion_ratio": 0.41,
            },
        }

        handle_event(event, runtime, bridge_state, args, None)

        self.assertEqual(len(runtime.triggered_events), 1)
        self.assertEqual(runtime.triggered_events[0]["event"], "hand_avoid_detected")
        self.assertIn("hand_avoid", runtime.started_scenes)

    def test_deeper_lateral_hand_cue_can_still_trigger_hand_avoid(self) -> None:
        runtime = FakeRuntime()
        bridge_state = BridgeState()
        args = self.make_args(scene_cooldown_ms=0, touch_persistence_frames=1)
        event = {
            "event_type": "target_updated",
            "scene_hint": {"name": "track_target", "reason": "side hand pushes into the lamp's boundary"},
            "tracking": {
                "target_present": True,
                "target_count": 1,
                "track_id": 12,
                "target_class": "person",
                "detector": "haar_face",
                "horizontal_zone": "right",
                "vertical_zone": "middle",
                "distance_band": "mid",
                "approach_state": "stable",
                "size_norm": 0.064,
                "confidence": 0.9,
                "center_norm": {"x": 0.72, "y": 0.40},
            },
            "selected_target": {
                "track_id": 12,
                "lock_state": "tracked",
                "reason": "stable face while hand enters from lower-right",
                "target_class": "person",
                "detector": "haar_face",
                "confidence": 0.9,
                "bbox_norm": {"x": 0.60, "y": 0.15, "w": 0.18, "h": 0.30},
                "center_norm": {"x": 0.72, "y": 0.40},
                "horizontal_zone": "right",
                "vertical_zone": "middle",
                "size_norm": 0.064,
                "distance_band": "mid",
                "approach_state": "stable",
                "selection_score": 1.18,
            },
            "interaction_hint": {
                "hand_arm_present": True,
                "detector": "skin_motion_hand",
                "confidence": 0.94,
                "bbox_norm": {"x": 0.68, "y": 0.72, "w": 0.11, "h": 0.16},
                "center_norm": {"x": 0.735, "y": 0.80},
                "horizontal_zone": "right",
                "vertical_zone": "lower",
                "area_ratio": 0.009,
                "motion_ratio": 0.46,
            },
        }

        handle_event(event, runtime, bridge_state, args, None)

        self.assertEqual(len(runtime.triggered_events), 1)
        self.assertEqual(runtime.triggered_events[0]["event"], "hand_avoid_detected")
        self.assertEqual(runtime.triggered_events[0]["payload"]["reason"], "explicit side hand intrusion")


if __name__ == "__main__":
    unittest.main()
