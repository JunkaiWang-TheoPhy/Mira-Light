# Vision Pipeline CLI 1-Minute Smoke Checklist

## Purpose

This checklist is the command-line companion to:

- [Director Console Vision UI 1-Minute Smoke Checklist](./21-director-console-vision-ui-smoke-checklist.md)

Use it when you want to confirm, in under one minute, that the vision pipeline itself is alive from the terminal side:

- receiver process
- saved frame output
- latest vision event
- bridge state
- operator lock file

This checklist does not depend on clicking through the browser UI.

## Preconditions

Run the local vision stack first:

```bash
cd /Users/Zhuanz/Documents/Github/Mira-Light
bash scripts/run_mira_light_vision_stack.sh
```

This should create or update files under:

```text
runtime/live-vision/
```

Key files:

- `runtime/live-vision/captures/`
- `runtime/live-vision/vision.latest.json`
- `runtime/live-vision/vision.events.jsonl`
- `runtime/live-vision/vision.bridge.state.json`
- `runtime/live-vision/vision.operator.json`

## 1-Minute Checklist

### 1. Confirm the camera receiver is listening

Run:

```bash
lsof -nP -iTCP:8000 -sTCP:LISTEN
```

Expected:

- a Python receiver process is listening on `*:8000`

### 2. Confirm captures are being written

Run:

```bash
find runtime/live-vision/captures -type f -name '*.jpg' | tail -n 5
```

Expected:

- at least one `.jpg` frame exists

### 3. Confirm the latest event file exists

Run:

```bash
sed -n '1,200p' runtime/live-vision/vision.latest.json
```

Expected:

- a valid JSON object
- contains at least:
  - `event_type`
  - `tracking`
  - `scene_hint`

### 4. Confirm multi-target fields are available

Run:

```bash
python3 - <<'PY'
import json
from pathlib import Path
path = Path("runtime/live-vision/vision.latest.json")
data = json.loads(path.read_text(encoding="utf-8"))
print("tracks:", len(data.get("tracks", [])))
print("selected_target:", bool(data.get("selected_target")))
print("scene_hint:", (data.get("scene_hint") or {}).get("name"))
PY
```

Expected:

- script prints without error
- `tracks` and/or `selected_target` fields are visible

### 5. Confirm bridge state exists

Run:

```bash
sed -n '1,220p' runtime/live-vision/vision.bridge.state.json
```

Expected:

- valid JSON
- includes:
  - `runtime`
  - `bridge`
  - `lastVisionEvent`

### 6. Confirm operator lock file exists or can be created

If the file already exists:

```bash
cat runtime/live-vision/vision.operator.json
```

If it does not exist yet, create a lock manually:

```bash
cat > runtime/live-vision/vision.operator.json <<'EOF'
{
  "lockSelectedTrackId": 1,
  "updatedAt": null,
  "note": "manual smoke test"
}
EOF
```

Then read it:

```bash
cat runtime/live-vision/vision.operator.json
```

Expected:

- the file is valid JSON
- `lockSelectedTrackId` is visible

### 7. Confirm the event log is appending

Run:

```bash
tail -n 5 runtime/live-vision/vision.events.jsonl
```

Expected:

- multiple JSONL lines
- recent events are visible

## Pass Criteria

Treat the CLI smoke check as passing if all of the following are true:

- receiver is listening on `8000`
- `.jpg` frames are present in `captures/`
- `vision.latest.json` exists and parses
- `vision.bridge.state.json` exists and parses
- `vision.events.jsonl` contains entries
- `vision.operator.json` can be read or written

## Fast Failure Clues

If the checklist fails, the most likely causes are:

- the receiver process is not running
- the upstream camera/relay is not currently sending frames
- the vision stack is writing to a different runtime directory
- file permissions prevent writing to `runtime/live-vision/`
- the extractor crashed before producing `vision.latest.json`
- the bridge crashed before producing `vision.bridge.state.json`

## Recommended Follow-up After a Pass

Once this CLI checklist passes, continue with:

1. [Director Console Vision UI 1-Minute Smoke Checklist](./21-director-console-vision-ui-smoke-checklist.md)
2. a manual operator lock / unlock check in the browser
3. a scene-behavior verification against `wake_up`, `track_target`, and `sleep`

## One-Line Summary

This checklist answers one narrow question:

> Is the local vision pipeline producing the files and state needed for the browser console and runtime bridge to function?
