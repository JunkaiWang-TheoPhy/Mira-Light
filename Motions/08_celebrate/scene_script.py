"""Per-scene motion script for the director console."""

from __future__ import annotations

SCENE_ID = "celebrate"

SCENE_SCRIPT = {
    "sceneId": SCENE_ID,
    "title": "跳舞模式",
    "folderName": "08_celebrate",
    "sourceSceneFile": "scripts/scenes.py",
    "sourceSceneKey": SCENE_ID,
    "apiRunPath": f"/api/run-motion-script/{SCENE_ID}",
    "stepOutline": [
        "Lift into the opening pose",
        "Rock upward with color changes",
        "Rock downward with more color changes",
        "Switch to rainbow dance mode",
        "Slow down and catch a breath",
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
