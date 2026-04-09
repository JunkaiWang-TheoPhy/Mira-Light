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
            "scene_allowed_detectors": "haar_face",
            "tracking_allowed_detectors": "haar_face,background_motion",
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


if __name__ == "__main__":
    unittest.main()
