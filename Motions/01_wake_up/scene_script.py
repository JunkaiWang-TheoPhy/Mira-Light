"""Per-scene motion script for the director console."""

from __future__ import annotations

SCENE_ID = "wake_up"

SCENE_SCRIPT = {
    "sceneId": SCENE_ID,
    "title": "起床",
    "folderName": "01_wake_up",
    "sourceSceneFile": "scripts/scenes.py",
    "sourceSceneKey": SCENE_ID,
    "apiRunPath": f"/api/run-motion-script/{SCENE_ID}",
    "stepOutline": [
        "Sleep pose and warm glow",
        "Lift to half-awake",
        "Stretch upward",
        "Shake out the head",
        "Look toward the guest",
    ],
}


def build_request_body(*, cue_mode="director", context=None, async_run=True, allow_unavailable=None):
    payload = {
        "scene": SCENE_ID,
        "async": bool(async_run),
        "cueMode": cue_mode or "director",
    }
    if context:
        payload["context"] = context
    if allow_unavailable is not None:
        payload["allowUnavailable"] = bool(allow_unavailable)
    return payload
