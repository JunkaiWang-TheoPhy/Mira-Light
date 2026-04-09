import argparse
import json
import unittest
from unittest.mock import patch

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = ROOT / "scripts"
FIXTURE_DIR = ROOT / "fixtures" / "vision_events"

if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from mira_light_runtime import MiraLightRuntime
from vision_runtime_bridge import BridgeState, handle_event, load_json_file


def load_fixture(name: str) -> dict:
    return json.loads((FIXTURE_DIR / name).read_text(encoding="utf-8"))


class FakeRuntime:
    def __init__(self) -> None:
        self.started_scenes: list[str] = []
        self.tracking_events: list[dict] = []
        self.dry_run = True
        self.running = False
        self.running_scene: str | None = None
        self.tracking_active = False
        self.tracking_target: dict = {"active": False}

    def get_runtime_state(self) -> dict:
        return {
            "running": self.running,
            "runningScene": self.running_scene,
            "trackingActive": self.tracking_active,
        }

    def start_scene(self, scene_name: str) -> None:
        self.started_scenes.append(scene_name)

    def apply_tracking_event(self, event: dict, *, source: str = "vision") -> dict:
        self.tracking_events.append({"event": event, "source": source})
        tracking = event.get("tracking", {})
        self.tracking_active = bool(tracking.get("target_present"))
        self.tracking_target = {
            "active": self.tracking_active,
            "horizontalZone": tracking.get("horizontal_zone"),
            "distanceBand": tracking.get("distance_band"),
            "source": source,
        }
        return self.get_runtime_state()


class VisionRuntimeBridgeTest(unittest.TestCase):
    def make_args(self) -> argparse.Namespace:
        return argparse.Namespace(
            scene_cooldown_ms=3500,
            wake_up_cooldown_ms=6000,
            sleep_grace_ms=4000,
            tracking_update_ms=220,
            log_json=False,
        )

    def test_target_seen_fixture_starts_wake_up(self) -> None:
        runtime = FakeRuntime()
        bridge_state = BridgeState()
        args = self.make_args()
        event = load_fixture("01-target-seen-left-mid.json")

        with patch("vision_runtime_bridge.time.monotonic", return_value=100.0):
            handle_event(event, runtime, bridge_state, args)

        self.assertEqual(runtime.started_scenes, ["wake_up"])
        self.assertTrue(bridge_state.last_target_present)
        self.assertEqual(bridge_state.last_scene_started, "wake_up")
        self.assertEqual(bridge_state.scene_counts["wake_up"], 1)

    def test_target_updated_track_target_fixture_applies_live_tracking(self) -> None:
        runtime = FakeRuntime()
        bridge_state = BridgeState()
        args = self.make_args()
        event = load_fixture("02-target-updated-right-mid-track-target.json")

        with patch("vision_runtime_bridge.time.monotonic", return_value=220.0):
            handle_event(event, runtime, bridge_state, args)

        self.assertEqual(runtime.started_scenes, [])
        self.assertEqual(len(runtime.tracking_events), 1)
        self.assertEqual(runtime.tracking_events[0]["source"], "vision")
        self.assertTrue(bridge_state.last_target_present)
        self.assertEqual(bridge_state.last_scene_started, "track_target")
        self.assertEqual(bridge_state.scene_counts["track_target"], 1)
        self.assertEqual(bridge_state.last_tracking_applied_at_monotonic, 220.0)
        self.assertEqual(bridge_state.last_seen_horizontal_zone, "right")
        self.assertEqual(bridge_state.last_seen_distance_band, "mid")

    def test_target_lost_clears_live_tracking_and_records_departure_direction(self) -> None:
        runtime = FakeRuntime()
        args = self.make_args()
        seen_event = load_fixture("02-target-updated-right-mid-track-target.json")
        lost_event = load_fixture("03-target-lost-after-track.json")

        bridge_state = BridgeState(last_target_present=True)
        with patch("vision_runtime_bridge.time.monotonic", return_value=220.0):
            handle_event(seen_event, runtime, bridge_state, args)

        with patch("vision_runtime_bridge.time.monotonic", return_value=500.0):
            handle_event(lost_event, runtime, bridge_state, args)

        self.assertEqual(runtime.started_scenes, [])
        self.assertEqual(len(runtime.tracking_events), 2)
        self.assertEqual(runtime.tracking_events[-1]["source"], "vision-clear")
        self.assertFalse(runtime.tracking_active)
        self.assertFalse(bridge_state.last_target_present)
        self.assertEqual(bridge_state.target_missing_since_monotonic, 500.0)
        self.assertEqual(bridge_state.last_departure_direction, "right")

    def test_target_lost_then_no_target_fixture_enters_sleep_after_grace(self) -> None:
        runtime = FakeRuntime()
        args = self.make_args()
        seen_event = load_fixture("02-target-updated-right-mid-track-target.json")
        lost_event = load_fixture("03-target-lost-after-track.json")
        no_target_event = load_fixture("04-no-target.json")

        bridge_state = BridgeState(last_target_present=True)
        with patch("vision_runtime_bridge.time.monotonic", return_value=220.0):
            handle_event(seen_event, runtime, bridge_state, args)

        with patch("vision_runtime_bridge.time.monotonic", return_value=500.0):
            handle_event(lost_event, runtime, bridge_state, args)

        self.assertEqual(runtime.started_scenes, [])
        self.assertFalse(bridge_state.last_target_present)
        self.assertEqual(bridge_state.target_missing_since_monotonic, 500.0)

        with patch("vision_runtime_bridge.time.monotonic", return_value=505.2):
            handle_event(no_target_event, runtime, bridge_state, args)

        self.assertEqual(runtime.started_scenes, ["sleep"])
        self.assertEqual(bridge_state.last_scene_started, "sleep")
        self.assertEqual(bridge_state.scene_counts["sleep"], 1)

    def test_target_updated_respects_tracking_update_interval(self) -> None:
        runtime = FakeRuntime()
        bridge_state = BridgeState(last_scene_started="track_target", last_tracking_applied_at_monotonic=220.0)
        args = self.make_args()
        event = load_fixture("02-target-updated-right-mid-track-target.json")

        with patch("vision_runtime_bridge.time.monotonic", return_value=220.1):
            handle_event(event, runtime, bridge_state, args)

        self.assertEqual(runtime.started_scenes, [])
        self.assertEqual(runtime.tracking_events, [])
        self.assertEqual(bridge_state.last_tracking_applied_at_monotonic, 220.0)

    def test_release_runtime_apply_tracking_event_updates_runtime_state(self) -> None:
        runtime = MiraLightRuntime(base_url="http://127.0.0.1:19783", dry_run=True)
        track_event = load_fixture("02-target-updated-right-mid-track-target.json")
        lost_event = load_fixture("03-target-lost-after-track.json")

        tracked_state = runtime.apply_tracking_event(track_event, source="vision")
        self.assertTrue(tracked_state["trackingActive"])
        self.assertEqual(tracked_state["trackingTarget"]["horizontalZone"], "right")
        self.assertEqual(tracked_state["trackingTarget"]["distanceBand"], "mid")
        self.assertEqual(tracked_state["currentStepType"], "tracking")
        self.assertTrue(str(tracked_state["lastCommand"]).startswith("tracking:"))
        self.assertIsNotNone(tracked_state["estimatedServoState"]["servo1"])

        cleared_state = runtime.apply_tracking_event(lost_event, source="vision-clear")
        self.assertFalse(cleared_state["trackingActive"])
        self.assertEqual(cleared_state["trackingTarget"]["reason"], "target_missing")
        self.assertEqual(cleared_state["lastCommand"], "tracking-clear:target_missing")

    def test_load_json_file_reads_release_fixture(self) -> None:
        payload = load_json_file(FIXTURE_DIR / "02-target-updated-right-mid-track-target.json")
        self.assertIsNotNone(payload)
        assert payload is not None
        self.assertEqual(payload["event_type"], "target_updated")
        self.assertEqual(payload["scene_hint"]["name"], "track_target")


if __name__ == "__main__":
    unittest.main()
