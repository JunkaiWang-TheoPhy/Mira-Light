"""Per-scene motion script for the director console."""

from __future__ import annotations

SCENE_ID = "cute_probe"

SCENE_SCRIPT = {
    "sceneId": SCENE_ID,
    "title": "卖萌",
    "folderName": "04_cute_probe",
    "sourceSceneFile": "scripts/scenes.py",
    "sourceSceneKey": SCENE_ID,
    "apiRunPath": f"/api/run-motion-script/{SCENE_ID}",
    "stepOutline": [
        "Tiny nod",
        "Look left and right",
        "Lift and lower the middle joint",
        "Lean forward carefully",
        "Retreat and peek out again",
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
