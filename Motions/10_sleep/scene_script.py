"""Per-scene motion script for the director console."""

from __future__ import annotations

SCENE_ID = "sleep"

SCENE_SCRIPT = {
    "sceneId": SCENE_ID,
    "title": "睡觉",
    "folderName": "10_sleep",
    "sourceSceneFile": "scripts/scenes.py",
    "sourceSceneKey": SCENE_ID,
    "apiRunPath": f"/api/run-motion-script/{SCENE_ID}",
    "stepOutline": [
        "Lower the head",
        "Drop the arm slowly",
        "Stretch once before bed",
        "Fold into the sleep pose",
        "Fade the lamp to warm amber",
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
