# Tabletop Target Locking and Selection Policy

## Purpose

This document records the next implementation pass after the first `tabletop_follow` mode landed.

The question for this pass is narrower:

```text
can Mira keep following the same book-like desk target
without switching too eagerly or disappearing when the object pauses
```

The answer in this pass is:

- tabletop mode now has a stricter switch policy
- tabletop mode now holds targets longer through short gaps
- tabletop diagnostics are now visible in the director console

## What Changed

### 1. Tabletop mode now has its own hold and switch thresholds

File:

- [`../../scripts/track_target_event_extractor.py`](../../scripts/track_target_event_extractor.py)

New tabletop-specific knobs:

- `--tabletop-hold-missing-frames`
- `--tabletop-switch-margin`
- `--tabletop-max-center-distance`
- `--tabletop-max-size-delta`
- `--tabletop-max-aspect-delta`

These are intentionally more conservative than the person-follow settings.

The goal is:

- do not abandon the current desk target too quickly
- tolerate brief pauses and short missing spans
- avoid bouncing between two nearby rectangular objects

### 2. Tabletop continuity now uses more than center distance

For tabletop targets, continuity now looks at:

- center distance
- size delta
- aspect-ratio delta
- edge-ratio delta
- motion-ratio delta

This helps the system treat “the same book, slightly moved or slightly rotated” as the same target.

### 3. Tabletop candidates now emit richer diagnostics

The tabletop candidate path now emits:

- `roi_mode`
- `edge_ratio`
- `motion_ratio`
- `aspect_ratio`
- `fill_ratio`
- `object_lock_strength`

These fields are propagated into `selected_target` and the effective `tracking` block for observability.

### 4. Director console now shows tabletop diagnostics

Files:

- [`../../web/app.js`](../../web/app.js)
- [`../../web/styles.css`](../../web/styles.css)

When the selected target is in `tabletop_follow`, the Vision panel now shows:

- ROI mode
- edge ratio
- motion ratio
- aspect ratio
- object lock strength
- score margin to best
- continuity deltas

This makes it much easier to answer:

```text
why is this book still locked
why didn’t the system switch
why did it finally switch
```

## Recommended Tuning Order

If tabletop tracking feels unstable, tune in this order:

1. `MIRA_LIGHT_TABLETOP_SWITCH_MARGIN`
2. `MIRA_LIGHT_TABLETOP_HOLD_MISSING_FRAMES`
3. `MIRA_LIGHT_TABLETOP_MAX_CENTER_DISTANCE`
4. `MIRA_LIGHT_TABLETOP_MAX_ASPECT_DELTA`
5. `MIRA_LIGHT_TABLETOP_MIN_EDGE_RATIO`

Heuristic guidance:

- raise `SWITCH_MARGIN` if the lamp keeps jumping between two desk objects
- raise `HOLD_MISSING_FRAMES` if the same book disappears too quickly after pausing
- raise `MAX_CENTER_DISTANCE` only slightly if the same book is moved in broader arcs
- tighten `MAX_ASPECT_DELTA` if different rectangular objects keep stealing the lock

## Validation

### Unit Tests

Relevant test file:

- [`../../tests/test_track_target_event_extractor.py`](../../tests/test_track_target_event_extractor.py)

This pass adds coverage for:

- tabletop hold using a longer missing-frame policy
- keeping a locked tabletop target unless the score lead is decisive
- recovering a previous tabletop target with feature continuity
- carrying tabletop diagnostics into the event payload

### Manual Booth Validation

Use this checklist:

1. switch the console to `tabletop_follow`
2. place one book-like target in the tabletop ROI
3. confirm `selected_target.target_class = object`
4. move the object slowly left and right
5. stop moving for a few seconds
6. add a second rectangular object nearby
7. confirm the selected target does not bounce unnecessarily

In the console, watch:

- `selected_target.reason`
- `object_lock_strength`
- `score_margin_to_best`
- `continuity_*` fields

## Current Limits

This still does not solve:

- explicit per-book identity
- cluttered multi-object desk scenes
- true book classification
- visual overlay selection on top of the camera frame

So this pass should be understood as:

```text
more stable tabletop locking
not yet full object identity tracking
```

## One-Line Summary

This pass turns `tabletop_follow` from a simple desk-object detector into a more conservative tabletop locking policy that is better suited for a live book-follow demo.
