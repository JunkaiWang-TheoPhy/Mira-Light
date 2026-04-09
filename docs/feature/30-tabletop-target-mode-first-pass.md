# Tabletop Target Mode First Pass

## Purpose

This document records the first implementation pass for:

```text
track_target should be able to follow a tabletop object,
not only a person
```

The goal of this pass is not to build a perfect book detector.
It is to add a practical booth-ready mode that is easier to align with the original `track_target` story:

- the judge moves a book or object on the desk
- Mira keeps attending to that desk target
- the operator can explicitly switch into that mode

## What Was Added

### 1. New operator-selectable target mode

The operator state file now supports:

- `targetMode = person_follow`
- `targetMode = tabletop_follow`

Relevant file:

- [`../../scripts/console_server.py`](../../scripts/console_server.py)

The director console can now persist this mode into:

- `runtime/live-vision/vision.operator.json`

### 2. First tabletop-object detector path

Relevant file:

- [`../../scripts/track_target_event_extractor.py`](../../scripts/track_target_event_extractor.py)

When `targetMode = tabletop_follow`, the extractor now:

- limits search to a configurable tabletop ROI
- combines edge density and foreground motion
- emits `target_class = object`
- emits `detector = tabletop_object`
- emits `target_mode = tabletop_follow`

This mode intentionally avoids depending on face/HOG signals.

### 3. Bridge routing now respects tabletop mode

Relevant file:

- [`../../scripts/vision_runtime_bridge.py`](../../scripts/vision_runtime_bridge.py)

For tabletop mode, a visible target now prefers:

```text
track_target
```

instead of the older person-oriented:

```text
target_seen -> wake_up
```

This keeps the desk-follow story aligned with what the operator expects.

### 4. Director console can switch modes directly

Relevant files:

- [`../../web/index.html`](../../web/index.html)
- [`../../web/app.js`](../../web/app.js)

The Vision panel now includes:

- `切到人物跟随`
- `切到桌面目标`

The panel also shows the currently effective mode and a short explanation.

## New Tuning Knobs

These are exposed through [`../../scripts/run_mira_light_vision_stack.sh`](../../scripts/run_mira_light_vision_stack.sh):

- `MIRA_LIGHT_DEFAULT_TARGET_MODE`
- `MIRA_LIGHT_TABLETOP_ROI_TOP`
- `MIRA_LIGHT_TABLETOP_ROI_BOTTOM`
- `MIRA_LIGHT_TABLETOP_ROI_LEFT`
- `MIRA_LIGHT_TABLETOP_ROI_RIGHT`
- `MIRA_LIGHT_TABLETOP_MIN_AREA_RATIO`
- `MIRA_LIGHT_TABLETOP_MAX_AREA_RATIO`
- `MIRA_LIGHT_TABLETOP_MIN_EDGE_RATIO`
- `MIRA_LIGHT_TABLETOP_MIN_MOTION_RATIO`
- `MIRA_LIGHT_TABLETOP_MIN_ASPECT_RATIO`
- `MIRA_LIGHT_TABLETOP_MAX_ASPECT_RATIO`

Recommended first use:

```bash
export MIRA_LIGHT_DEFAULT_TARGET_MODE=tabletop_follow
bash scripts/run_mira_light_vision_stack.sh
```

## Expected Behavior

### In `person_follow`

The system should continue to behave like the current person-oriented tracking path:

- face / HOG / motion cues
- `wake_up`, `curious_observe`, `track_target`
- person-first target selection

### In `tabletop_follow`

The system should behave more like a desk-object tracker:

- object candidates only from tabletop ROI
- `target_class = object`
- `detector = tabletop_object`
- visible target goes straight toward `track_target`

## Validation

### Unit Tests

Relevant tests:

- [`../../tests/test_track_target_event_extractor.py`](../../tests/test_track_target_event_extractor.py)
- [`../../tests/test_vision_runtime_bridge.py`](../../tests/test_vision_runtime_bridge.py)
- [`../../tests/test_console_server.py`](../../tests/test_console_server.py)

Coverage added in this pass:

- tabletop candidate extraction from a synthetic desk frame
- event payload carries `target_mode = tabletop_follow`
- bridge prefers `track_target` for tabletop `target_seen`
- console persists `targetMode` in operator state

### Manual Validation

Recommended quick validation order:

1. start the vision stack
2. open the director console
3. click `切到桌面目标`
4. confirm `vision.operator.json` now contains `targetMode = tabletop_follow`
5. move a book or rectangular object inside the desk ROI
6. confirm `selected_target.target_class = object`
7. confirm `scene_hint` and bridge action prefer `track_target`

## Current Limits

This is still a first-pass tabletop mode.
It does not yet provide:

- category-level book recognition
- robust object identity across cluttered desks
- color-specific or marker-specific tracking
- strong occlusion recovery for multiple desk objects

So the right framing is:

```text
desk-target mode now exists
but it is still heuristic
```

## Recommended Next Step

If the booth story depends strongly on “follow this exact book,” the next upgrade should be one of:

1. marker-assisted tabletop target selection
2. stronger object detector path
3. operator-assisted object lock from a visual overlay

## One-Line Summary

This upgrade adds the first real `tabletop_follow` mode so `track_target` can be steered toward desk objects instead of only people, while keeping the mode switchable and observable from the director console.
