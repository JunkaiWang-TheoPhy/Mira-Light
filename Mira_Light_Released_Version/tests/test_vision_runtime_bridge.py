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

from vision_runtime_bridge import BridgeState, handle_event, load_json_file


def load_fixture(name: str) -> dict:
    return json.loads((FIXTURE_DIR / name).read_text(encoding="utf-8"))


class FakeRuntime:
    def __init__(self) -> None:
        self.started_scenes: list[str] = []
        self.dry_run = True
        self.running = False

    def get_runtime_state(self) -> dict:
        return {
            "running": self.running,
            "runningScene": None,
        }

    def start_scene(self, scene_name: str) -> None:
        self.started_scenes.append(scene_name)


class VisionRuntimeBridgeTest(unittest.TestCase):
    def make_args(self) -> argparse.Namespace:
        return argparse.Namespace(
            scene_cooldown_ms=3500,
            wake_up_cooldown_ms=6000,
            sleep_grace_ms=4000,
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

    def test_target_updated_track_target_fixture_starts_track_target(self) -> None:
        runtime = FakeRuntime()
        bridge_state = BridgeState()
        args = self.make_args()
        event = load_fixture("02-target-updated-right-mid-track-target.json")

        with patch("vision_runtime_bridge.time.monotonic", return_value=220.0):
            handle_event(event, runtime, bridge_state, args)

        self.assertEqual(runtime.started_scenes, ["track_target"])
        self.assertTrue(bridge_state.last_target_present)
        self.assertEqual(bridge_state.last_scene_started, "track_target")
        self.assertEqual(bridge_state.scene_counts["track_target"], 1)

    def test_target_lost_then_no_target_fixture_enters_sleep_after_grace(self) -> None:
        runtime = FakeRuntime()
        bridge_state = BridgeState(last_target_present=True)
        args = self.make_args()
        lost_event = load_fixture("03-target-lost-after-track.json")
        no_target_event = load_fixture("04-no-target.json")

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

    def test_load_json_file_reads_release_fixture(self) -> None:
        payload = load_json_file(FIXTURE_DIR / "02-target-updated-right-mid-track-target.json")
        self.assertIsNotNone(payload)
        assert payload is not None
        self.assertEqual(payload["event_type"], "target_updated")
        self.assertEqual(payload["scene_hint"]["name"], "track_target")


if __name__ == "__main__":
    unittest.main()
