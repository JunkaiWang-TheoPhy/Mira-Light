import argparse
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
        self.dry_run = True

    def get_runtime_state(self) -> dict:
        return {
            "running": False,
            "runningScene": None,
            "trackingActive": False,
        }

    def start_scene(self, scene_name: str) -> None:
        self.started_scenes.append(scene_name)

    def apply_tracking_event(self, event: dict, *, source: str = "vision") -> None:
        self.tracking_events.append({"event": event, "source": source})


class FakeMemoryClient:
    def __init__(self) -> None:
        self.tracking_states: list[dict] = []

    def record_tracking_session_state(self, **payload) -> None:
        self.tracking_states.append(payload)


class VisionRuntimeBridgeTest(unittest.TestCase):
    def test_handle_event_writes_tracking_session_state(self) -> None:
        runtime = FakeRuntime()
        memory_client = FakeMemoryClient()
        bridge_state = BridgeState()
        args = argparse.Namespace(
            scene_cooldown_ms=3500,
            wake_up_cooldown_ms=6000,
            sleep_grace_ms=4000,
            log_json=False,
            memory_session_id="mira-light-vision",
        )

        event = {
            "event_type": "target_seen",
            "scene_hint": {"name": "track_target"},
            "tracking": {
                "target_present": True,
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
        args = argparse.Namespace(
            scene_cooldown_ms=3500,
            wake_up_cooldown_ms=6000,
            sleep_grace_ms=4000,
            tracking_update_ms=200,
            log_json=False,
            memory_session_id="mira-light-vision",
        )

        event = {
            "event_type": "target_updated",
            "scene_hint": {"name": "track_target"},
            "tracking": {
                "target_present": True,
                "horizontal_zone": "right",
                "vertical_zone": "middle",
                "distance_band": "mid",
                "target_class": "person",
                "confidence": 0.9,
            },
            "control_hint": {
                "yaw_error_norm": 0.42,
                "pitch_error_norm": -0.18,
                "lift_intent": 0.6,
                "reach_intent": 0.55,
            },
        }

        handle_event(event, runtime, bridge_state, args, None)

        self.assertFalse(runtime.started_scenes)
        self.assertEqual(len(runtime.tracking_events), 1)
        self.assertEqual(runtime.tracking_events[0]["source"], "vision")


if __name__ == "__main__":
    unittest.main()
