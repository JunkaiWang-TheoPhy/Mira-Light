"""Per-scene motion script for the director console."""

from __future__ import annotations

SCENE_ID = "standup_reminder"

SCENE_SCRIPT = {
    "sceneId": SCENE_ID,
    "title": "久坐检测：蹭蹭",
    "folderName": "06_standup_reminder",
    "sourceSceneFile": "scripts/scenes.py",
    "sourceSceneKey": SCENE_ID,
    "apiRunPath": f"/api/run-motion-script/{SCENE_ID}",
    "stepOutline": [
        "Turn toward the guest",
        "Nuzzle once",
        "Nuzzle twice",
        "Nuzzle a third time",
        "Double nod and back off",
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
