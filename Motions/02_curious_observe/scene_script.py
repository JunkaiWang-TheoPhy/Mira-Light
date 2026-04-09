"""Per-scene motion script for the director console."""

from __future__ import annotations

SCENE_ID = "curious_observe"

SCENE_SCRIPT = {
    "sceneId": SCENE_ID,
    "title": "好奇你是谁",
    "folderName": "02_curious_observe",
    "sourceSceneFile": "scripts/scenes.py",
    "sourceSceneKey": SCENE_ID,
    "apiRunPath": f"/api/run-motion-script/{SCENE_ID}",
    "stepOutline": [
        "Notice the guest",
        "Lean in partway",
        "Slowly shake once",
        "Turn away and bow shyly",
        "Peek back and nod",
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
