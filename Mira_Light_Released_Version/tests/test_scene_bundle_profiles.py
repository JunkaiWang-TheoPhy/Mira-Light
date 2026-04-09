import os
import unittest
from unittest.mock import patch

from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = ROOT / "scripts"

if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from mira_light_runtime import MiraLightRuntime


class SceneBundleProfilesTest(unittest.TestCase):
    def test_default_bundle_matches_minimal_profile(self) -> None:
        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop("MIRA_LIGHT_SCENE_BUNDLE", None)
            os.environ.pop("MIRA_LIGHT_SHOW_EXPERIMENTAL", None)
            runtime = MiraLightRuntime(base_url="http://127.0.0.1:9", dry_run=True)
            scenes = {item["id"] for item in runtime.list_scenes()}
            self.assertEqual(scenes, {"cute_probe", "daydream", "farewell"})
            state = runtime.get_runtime_state()
            self.assertEqual(state["sceneBundle"], "minimal")
            self.assertEqual(state["sceneBundleSource"], "config_default")

    def test_booth_core_bundle_exposes_main_show_scenes(self) -> None:
        with patch.dict(
            os.environ,
            {
                "MIRA_LIGHT_SCENE_BUNDLE": "booth_core",
            },
            clear=False,
        ):
            runtime = MiraLightRuntime(base_url="http://127.0.0.1:9", dry_run=True)
            scenes = {item["id"] for item in runtime.list_scenes()}
            self.assertEqual(
                scenes,
                {
                    "wake_up",
                    "curious_observe",
                    "touch_affection",
                    "track_target",
                    "celebrate",
                    "farewell",
                    "sleep",
                },
            )
            state = runtime.get_runtime_state()
            self.assertEqual(state["sceneBundle"], "booth_core")
            self.assertEqual(state["sceneBundleSource"], "env")

    def test_show_experimental_without_bundle_exposes_all_scenes(self) -> None:
        with patch.dict(
            os.environ,
            {
                "MIRA_LIGHT_SHOW_EXPERIMENTAL": "1",
            },
            clear=False,
        ):
            os.environ.pop("MIRA_LIGHT_SCENE_BUNDLE", None)
            runtime = MiraLightRuntime(base_url="http://127.0.0.1:9", dry_run=True)
            scenes = {item["id"] for item in runtime.list_scenes()}
            self.assertIn("track_target", scenes)
            self.assertIn("sigh_demo", scenes)
            self.assertIn("voice_demo_tired", scenes)
            state = runtime.get_runtime_state()
            self.assertIsNone(state["sceneBundle"])
            self.assertEqual(state["sceneBundleSource"], "show_experimental")


if __name__ == "__main__":
    unittest.main()
