# Vision + Runtime + Scene 5-Minute Integration Checklist

## Purpose

This checklist is the next step after the 1-minute smoke checks.

Use it when you want to confirm that the local Mira Light stack is not only:

- receiving JPEG frames
- writing vision state files
- rendering director-console vision state

but also:

- bridging vision events into runtime
- causing believable scene-level behavior transitions
- preserving operator lock and scene fallback behavior

This is still not a full release acceptance test, but it is the first meaningful “system is behaving like a creature” validation pass.

## Companion Checklists

Run these first:

- [Director Console Vision UI 1-Minute Smoke Checklist](./21-director-console-vision-ui-smoke-checklist.md)
- [Vision Pipeline CLI 1-Minute Smoke Checklist](./22-vision-pipeline-cli-1-minute-smoke-checklist.md)

## Preconditions

Start the local vision stack:

```bash
cd /Users/Zhuanz/Documents/Github/Mira-Light
bash scripts/run_mira_light_vision_stack.sh
```

Start the director console:

```bash
cd /Users/Zhuanz/Documents/Github/Mira-Light
python3 scripts/console_server.py
```

Default browser URL:

```text
http://127.0.0.1:8765
```

If you are rehearsing without live upstream camera frames, you may replay demo captures:

```bash
./.venv/bin/python scripts/replay_camera_frames_to_receiver.py \
  --captures-dir runtime/vision-demo-captures \
  --receiver-url http://127.0.0.1:8000/upload \
  --fps 3
```

## 5-Minute Checklist

### 1. Confirm the stack is updating in real time

Open the director console and the CLI side-by-side.

Browser:

- watch the `Vision State` panel

CLI:

```bash
watch -n 1 cat runtime/live-vision/vision.bridge.state.json
```

Expected:

- `lastVisionEvent` keeps changing while frames arrive
- the browser updates without manual reload

### 2. Confirm target appearance can trigger `wake_up`

Bring one clear person into the camera field, or replay a frame sequence that starts with a single visible target.

Expected:

- `scene_hint` becomes `wake_up` or transitions through a plausible first-contact state
- runtime eventually records `wake_up`
- the director console reflects that transition

Optional CLI confirmation:

```bash
python3 - <<'PY'
import json
from pathlib import Path
data = json.loads(Path("runtime/live-vision/vision.bridge.state.json").read_text())
print(data["runtime"].get("lastFinishedScene"))
print((data.get("lastVisionEvent") or {}).get("scene_hint"))
PY
```

### 3. Confirm stable target presence leads to `track_target`

Keep the same target visible for several frames and move it left / right.

Expected:

- `selected_target` remains stable
- `horizontal_zone` changes in a believable way
- runtime either enters `track_target` or stays in live tracking mode
- the lamp behaves like it is continuing to attend to that same person

### 4. Confirm operator lock changes which target is preferred

When two visible tracks exist:

1. use the browser `Vision State` panel to lock one target
2. confirm the lock is written

CLI:

```bash
cat runtime/live-vision/vision.operator.json
```

Expected:

- `lockSelectedTrackId` matches the chosen track
- `selected_target.track_id` converges to the locked one
- tracking and scene selection stop drifting to the other visible target

### 5. Confirm unlock restores automatic selection

Use `解除目标锁定`.

Expected:

- `vision.operator.json` resets to `lockSelectedTrackId = null`
- `selected_target` can change again based on automatic scoring

### 6. Confirm target loss eventually causes a graceful exit

Remove the target from the frame or finish the replay batch.

Expected:

- the bridge does not instantly panic on one missing frame
- after the grace period, runtime transitions away from tracking
- `farewell` or `sleep` behavior appears according to current bridge policy

CLI:

```bash
python3 - <<'PY'
import json
from pathlib import Path
data = json.loads(Path("runtime/live-vision/vision.bridge.state.json").read_text())
print(data["runtime"].get("lastFinishedScene"))
print((data.get("lastVisionEvent") or {}).get("event_type"))
PY
```

### 7. Confirm the system is not over-triggering on weak detections

Introduce brief or noisy motion near the camera without a clear stable target.

Expected:

- the bridge should not repeatedly launch `wake_up`
- the selected target should not jump wildly
- weak motion-only false positives should be damped by the current gating rules

This is one of the most important real-world checks.

## Pass Criteria

Treat the integration checklist as passing if all of the following are true:

- `wake_up` can occur when a clear target appears
- `track_target` can remain active while a target remains visible
- operator lock changes target preference
- operator unlock restores automatic selection
- target disappearance eventually produces a graceful exit
- weak/noisy detections do not cause obvious random scene spam

## Failure Patterns To Watch For

Common failures and their likely causes:

- `wake_up` never triggers
  - detector too weak
  - confidence threshold too high
  - scene persistence too strict

- `track_target` keeps bouncing
  - detector instability
  - latest-frame polling dropping useful continuity
  - target handoff between multiple tracks

- operator lock does nothing
  - `vision.operator.json` path mismatch
  - selected target not present in current track set

- system sleeps too aggressively
  - target absence grace too short
  - detection drops on still targets

- scene spam
  - detector allowlist too broad
  - persistence threshold too low
  - confidence floor too low

## Recommended Follow-up After a Pass

If this 5-minute integration checklist passes, the next high-value validations are:

1. more difficult multi-person scenes
2. hand / object detection integration
3. stronger detector substitution for `person_hog`
4. director-console visualization polish
5. model-assisted high-level scene interpretation

## One-Line Summary

This checklist answers one system-level question:

> Does the current Mira Light vision stack actually drive scene behavior in a stable, operator-observable way?
