"""Per-scene motion script for the director console."""

from __future__ import annotations

SCENE_ID = "track_target"

SCENE_SCRIPT = {
    "sceneId": SCENE_ID,
    "title": "追踪",
    "folderName": "07_track_target",
    "sourceSceneFile": "scripts/scenes.py",
    "sourceSceneKey": SCENE_ID,
    "apiRunPath": f"/api/run-motion-script/{SCENE_ID}",
    "stepOutline": [
        "Look to the left edge",
        "Track back toward center",
        "Continue to the right edge",
        "Pause with the target",
        "Resume motion and settle back",
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
