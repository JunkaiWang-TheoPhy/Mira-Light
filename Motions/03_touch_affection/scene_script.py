"""Per-scene motion script for the director console."""

from __future__ import annotations

SCENE_ID = "touch_affection"

SCENE_SCRIPT = {
    "sceneId": SCENE_ID,
    "title": "摸一摸",
    "folderName": "03_touch_affection",
    "sourceSceneFile": "scripts/scenes.py",
    "sourceSceneKey": SCENE_ID,
    "apiRunPath": f"/api/run-motion-script/{SCENE_ID}",
    "stepOutline": [
        "Approach the hand softly",
        "Dip under the palm",
        "Rub with small nudges",
        "Follow the hand once",
        "Return to neutral light",
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
