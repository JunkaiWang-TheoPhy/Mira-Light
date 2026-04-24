# Motions

This directory keeps one motion-launch script per primary scene button in the
director console.

- `Motions/01_wake_up/scene_script.py`
- `Motions/02_curious_observe/scene_script.py`
- `Motions/03_touch_affection/scene_script.py`
- `Motions/04_cute_probe/scene_script.py`
- `Motions/05_daydream/scene_script.py`
- `Motions/06_standup_reminder/scene_script.py`
- `Motions/07_track_target/scene_script.py`
- `Motions/08_celebrate/scene_script.py`
- `Motions/09_farewell/scene_script.py`
- `Motions/10_sleep/scene_script.py`

The choreography source of truth still lives in `scripts/scenes.py`. The files
here are thin launch manifests so the navigation page can route each scene
button through its own script file.

Additional planning notes live under:

- `Motions/test/README.md`
- `Motions/test/10-scene-capability-matrix.md`
