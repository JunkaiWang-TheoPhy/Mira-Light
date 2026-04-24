"""Per-scene motion script for the director console."""

from __future__ import annotations

import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parents[2] / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from mira_light_signal_delivery import build_scene_request_body, build_scene_script_info

SCENE_ID = "touch_affection"

SCENE_SCRIPT = build_scene_script_info(
    scene_id=SCENE_ID,
    title="摸一摸",
    folder_name="03_touch_affection",
    step_outline=[
        "Approach the hand softly",
        "Dip under the palm",
        "Rub with small nudges",
        "Follow the hand once",
        "Return to neutral light",
    ],
)


def build_request_body(*, cue_mode="director", context=None, async_run=True, allow_unavailable=None):
    return build_scene_request_body(
        SCENE_ID,
        cue_mode=cue_mode,
        context=context,
        async_run=async_run,
        allow_unavailable=allow_unavailable,
    )
