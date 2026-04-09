# Director Console Vision UI 1-Minute Smoke Checklist

## Purpose

This checklist is the fastest manual browser-side validation for the new vision-aware director console.

Use it when you want to confirm, in under one minute, that:

- the director console is loading
- vision state is visible
- operator lock writes are working
- the UI is reading the current live-vision files instead of showing stale placeholders

This is intentionally lightweight.
It is not a full acceptance test for the entire vision stack.

## Preconditions

Before starting, make sure these two processes are available:

1. The vision stack

Recommended:

```bash
cd /Users/Zhuanz/Documents/Github/Mira-Light
bash scripts/run_mira_light_vision_stack.sh
```

2. The local director console

```bash
cd /Users/Zhuanz/Documents/Github/Mira-Light
python3 scripts/console_server.py
```

Default browser URL:

```text
http://127.0.0.1:8765
```

If you are not running a real live-vision stack yet, you can still use seeded demo files in:

- `runtime/live-vision/vision.latest.json`
- `runtime/live-vision/vision.bridge.state.json`
- `runtime/live-vision/vision.operator.json`

## 1-Minute Checklist

### 1. Open the director console

Open:

```text
http://127.0.0.1:8765
```

Expected:

- the page loads successfully
- no obvious blank-screen or broken-script behavior

### 2. Confirm the Vision section is visible

Look for the `Vision State` panel.

Expected:

- there is a vision summary area
- there is a tracks list area
- there are lock/unlock controls

### 3. Confirm the page is reading live vision data

Within the vision panel, confirm you can see:

- current `scene_hint`
- current visible `tracks`
- current `selected_target` or “未锁定”
- detector / confidence / distance / zone-style information

Expected:

- these values are not all stuck at `-`
- they reflect the current content of the live-vision JSON files

### 4. Lock one visible track

In the tracks list, click one `锁定` button.

Expected:

- the `Operator Lock` summary updates
- the chosen track is visually distinguishable as the selected one
- the lock state changes from automatic/candidate behavior to explicit lock behavior

### 5. Confirm operator lock file changed

Without leaving the browser open, run:

```bash
cat /Users/Zhuanz/Documents/Github/Mira-Light/runtime/live-vision/vision.operator.json
```

Expected:

- `lockSelectedTrackId` exists
- its value matches the track you clicked

### 6. Clear the lock

Click `解除目标锁定`.

Expected:

- the `Operator Lock` summary returns to unlocked state
- the selection clears

### 7. Confirm operator lock file cleared

Run:

```bash
cat /Users/Zhuanz/Documents/Github/Mira-Light/runtime/live-vision/vision.operator.json
```

Expected:

- `lockSelectedTrackId` becomes `null`

## Pass Criteria

Treat the smoke check as passing if all of the following are true:

- the page loads
- the vision panel is visible
- `tracks[]` and `selected_target` are rendered
- clicking `锁定` updates the operator state
- clicking `解除目标锁定` clears it again
- the browser behavior and `vision.operator.json` stay consistent

## Fast Failure Clues

If the check fails, the most likely causes are:

- `scripts/console_server.py` is not running
- the page is pointed at the wrong port
- `runtime/live-vision/vision.latest.json` is missing
- `runtime/live-vision/vision.bridge.state.json` is missing
- front-end JavaScript failed to load
- the live-vision stack is writing to a different runtime directory than the console is reading

## Recommended Follow-up After a Pass

If this 1-minute smoke check passes, the next manual validation should be:

1. verify that the selected track changes when the upstream target changes
2. verify that `track_target` behavior in runtime follows the selected target
3. verify that false positives do not cause random operator lock drift

## One-Line Summary

This checklist answers one narrow question:

> Can the browser director console see the current vision state and let the operator lock or clear the active target?
