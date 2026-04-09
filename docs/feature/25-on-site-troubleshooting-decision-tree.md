# On-Site Troubleshooting Decision Tree

## Purpose

This document is the fast on-site decision tree for Mira Light demos.

Use it when something goes wrong during rehearsal or live presentation and you need to answer one question quickly:

> Should we inspect the browser UI, the local CLI pipeline, or the runtime / behavior layer first?

This page is meant to reduce panic and shorten recovery time.

## How To Use This Page

Start from the symptom you can see right now.

Do not begin with architecture theory.
Do not begin by restarting everything blindly.

Instead:

1. identify the visible symptom
2. enter the matching branch below
3. follow the shortest first check
4. only move deeper if that check passes

## Entry Branches

Choose one starting point:

### A. The browser page looks wrong

Examples:

- the director console does not load
- the page loads but the `Vision State` panel is empty
- the lock button does nothing
- the status strip is stale

Go to:

- [UI Branch](#ui-branch)

### B. The browser looks fine, but the backend feels dead

Examples:

- no new frames appear
- `vision.latest.json` is not changing
- lock state never changes
- no bridge state is written

Go to:

- [CLI Branch](#cli-branch)

### C. The files exist, but the lamp behavior is wrong

Examples:

- target is visible, but no `wake_up`
- target is visible, but tracking is unstable
- target disappears, but the lamp never sleeps
- scene transitions feel wrong

Go to:

- [Behavior Branch](#behavior-branch)

### D. The entire stack feels broken

Examples:

- page is stale
- files are stale
- no tracking
- no scene behavior

Go to:

- [Full Stack Reset Path](#full-stack-reset-path)

## UI Branch

Ask:

> Is this mainly a browser/operator-surface problem?

### Step UI-1

Open:

```text
http://127.0.0.1:8765
```

If the page does not load:

- the issue is almost certainly UI/server-side, not scene logic
- check whether `console_server.py` is running

Command:

```bash
lsof -nP -iTCP:8765 -sTCP:LISTEN
```

If nothing is listening:

- restart the console server

Command:

```bash
cd /Users/Zhuanz/Documents/Github/Mira-Light
python3 scripts/console_server.py
```

### Step UI-2

If the page loads but `Vision State` is empty, check the browser-side checklist:

- [Director Console Vision UI 1-Minute Smoke Checklist](./21-director-console-vision-ui-smoke-checklist.md)

If the browser fails there but CLI files exist:

- treat it as a UI/API rendering issue

Check:

- `GET /api/vision`
- `GET /api/vision-operator`

### Step UI-3

If the lock/unlock buttons do nothing:

Check whether the operator state file changes:

```bash
cat /Users/Zhuanz/Documents/Github/Mira-Light/runtime/live-vision/vision.operator.json
```

Interpretation:

- file changes -> UI write path works, problem is further downstream
- file does not change -> problem is in browser event wiring or `console_server.py`

### UI Branch Conclusion

If the UI branch fails before file writes:

```text
Root cause is UI / local console API
```

If the UI writes files correctly but behavior does not change:

```text
Switch to Behavior Branch
```

## CLI Branch

Ask:

> Are the local receiver / extractor / bridge artifacts updating?

### Step CLI-1

Check the receiver:

```bash
lsof -nP -iTCP:8000 -sTCP:LISTEN
```

If nothing is listening:

- the image ingress layer is down

Restart:

```bash
cd /Users/Zhuanz/Documents/Github/Mira-Light
bash scripts/run_mira_light_vision_stack.sh
```

### Step CLI-2

Check whether JPEG frames are being written:

```bash
find runtime/live-vision/captures -type f -name '*.jpg' | tail -n 5
```

Interpretation:

- no frames -> upstream camera / relay / receiver problem
- frames exist -> continue

### Step CLI-3

Check latest event:

```bash
sed -n '1,200p' runtime/live-vision/vision.latest.json
```

If missing:

- extractor is not producing output

### Step CLI-4

Check bridge state:

```bash
sed -n '1,220p' runtime/live-vision/vision.bridge.state.json
```

If missing:

- bridge is not consuming events

### Step CLI-5

Check event log:

```bash
tail -n 10 runtime/live-vision/vision.events.jsonl
```

Interpretation:

- file updates, but bridge state is stale -> bridge issue
- file and bridge both update -> continue to behavior branch

### CLI Branch Conclusion

If the CLI branch fails before `vision.latest.json` exists:

```text
Root cause is receiver / extractor
```

If `vision.latest.json` exists but `vision.bridge.state.json` does not:

```text
Root cause is bridge
```

If both exist and update:

```text
Switch to Behavior Branch
```

## Behavior Branch

Ask:

> Is the stack alive, but making bad decisions or unstable movements?

### Step B-1

Check the last event:

```bash
python3 - <<'PY'
import json
from pathlib import Path
data = json.loads(Path("runtime/live-vision/vision.latest.json").read_text())
print("event_type:", data.get("event_type"))
print("scene_hint:", (data.get("scene_hint") or {}).get("name"))
print("selected_target:", (data.get("selected_target") or {}).get("track_id"))
print("detector:", (data.get("tracking") or {}).get("detector"))
print("confidence:", (data.get("tracking") or {}).get("confidence"))
PY
```

If these values look wrong:

- the issue is upstream of runtime
- detector quality, target selection, or event extraction is likely the cause

### Step B-2

Check bridge decision state:

```bash
python3 - <<'PY'
import json
from pathlib import Path
data = json.loads(Path("runtime/live-vision/vision.bridge.state.json").read_text())
print("trackingActive:", (data.get("runtime") or {}).get("trackingActive"))
print("lastSceneStarted:", (data.get("bridge") or {}).get("lastSceneStarted"))
print("sceneCounts:", (data.get("bridge") or {}).get("sceneCounts"))
PY
```

If `selected_target` looks right but `lastSceneStarted` is wrong:

- the issue is probably bridge policy / gating

### Step B-3

Check whether the runtime is rejecting direct behavior because another scene is still active.

Look at:

- `running`
- `runningScene`
- `trackingActive`

If the runtime is stuck in a scene:

- stop the current scene
- then re-check tracking

### Step B-4

Check for false positives vs false negatives.

#### If the lamp wakes up too easily

Likely cause:

- detector too weak
- confidence floor too low
- persistence threshold too low

#### If the lamp never reacts

Likely cause:

- detector too weak
- confidence floor too high
- selected target never gets locked or promoted

#### If the lamp tracks but jitters

Likely cause:

- latest-frame-only consumption
- noisy target handoff
- unstable detector identity

### Behavior Branch Conclusion

If files and UI are correct but motion is wrong:

```text
Root cause is bridge policy / detector stability / runtime scene logic
```

At that point, use:

- [Camera CV and Runtime Bridge Progress](./20-camera-cv-runtime-bridge-progress.md)
- [Vision + Runtime + Scene 5-Minute Integration Checklist](./23-vision-runtime-scene-5-minute-integration-checklist.md)

## Full Stack Reset Path

Only use this if you cannot quickly isolate UI, CLI, or behavior failure.

### Step R-1

Stop stale local processes if needed.

### Step R-2

Restart the vision stack:

```bash
cd /Users/Zhuanz/Documents/Github/Mira-Light
bash scripts/run_mira_light_vision_stack.sh
```

### Step R-3

Restart the director console:

```bash
cd /Users/Zhuanz/Documents/Github/Mira-Light
python3 scripts/console_server.py
```

### Step R-4

Run, in order:

1. [Vision Pipeline CLI 1-Minute Smoke Checklist](./22-vision-pipeline-cli-1-minute-smoke-checklist.md)
2. [Director Console Vision UI 1-Minute Smoke Checklist](./21-director-console-vision-ui-smoke-checklist.md)
3. [Vision + Runtime + Scene 5-Minute Integration Checklist](./23-vision-runtime-scene-5-minute-integration-checklist.md)

## Quick Routing Table

| Symptom | Check first | Likely owner |
| --- | --- | --- |
| Page blank / stale | UI branch | console / browser |
| Lock button no effect | UI branch | browser + console API |
| No frames on disk | CLI branch | receiver / upstream camera |
| No `vision.latest.json` | CLI branch | extractor |
| No `vision.bridge.state.json` | CLI branch | bridge |
| Vision files change, lamp behavior wrong | Behavior branch | bridge / runtime |
| Wake-up too easy | Behavior branch | detector gating |
| Tracking unstable | Behavior branch | detector / target continuity |
| Can’t tell where to start | Full reset path | whole stack |

## Related Docs

- [Vision Validation Checklist Index](./24-vision-validation-checklist-index.md)
- [Director Console Vision UI 1-Minute Smoke Checklist](./21-director-console-vision-ui-smoke-checklist.md)
- [Vision Pipeline CLI 1-Minute Smoke Checklist](./22-vision-pipeline-cli-1-minute-smoke-checklist.md)
- [Vision + Runtime + Scene 5-Minute Integration Checklist](./23-vision-runtime-scene-5-minute-integration-checklist.md)
- [Camera CV and Runtime Bridge Progress](./20-camera-cv-runtime-bridge-progress.md)

## One-Line Summary

This page is the fast triage map for on-site failures:

```text
UI problem?
CLI problem?
Behavior problem?
Or reset and rerun the full validation chain?
```
