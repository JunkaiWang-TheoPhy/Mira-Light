# Vision Target Stability and Bridge Observability Upgrade

## Purpose

This document records the first implementation pass for the roadmap item:

```text
make target selection more stable
and make bridge decisions easier to see on-site
```

It focuses on two booth-critical gaps:

- stationary or briefly occluded people should not disappear too easily
- operators should be able to see why the bridge selected, blocked, or switched a target

This upgrade does not yet add a true book/object detector.
It strengthens the existing person-following line so the current prototype is easier to trust and debug.

## What Changed

### 1. Selected-target continuity is now stronger

File:

- [`../../scripts/track_target_event_extractor.py`](../../scripts/track_target_event_extractor.py)

The extractor now adds three stability behaviors:

- it can recover the previous selected target by spatial continuity when `track_id` churns
- it keeps a visible selected target unless a new target wins by a clear score margin
- it emits extra selected-target metadata for debugging

New selected-target fields may now include:

- `reason`
- `score_margin_to_best`
- `continuity_distance_norm`
- `continuity_size_delta`

The main outcome is:

```text
less accidental target handoff
less loss when the same person remains in view
better visibility into why a target stayed selected
```

### 2. HOG detector naming is normalized for bridge gating

The extractor now consistently emits `hog_person`.

This matches the runtime-bridge allowlist and avoids one class of confusing detector mismatch.

### 3. Tracking metadata is richer

The event payload now writes selected-target context back into `tracking`:

- `selected_lock_state`
- `selected_reason`

This lets runtime and observability surfaces understand not only which target is active, but why.

### 4. Bridge state now records the latest decision summary

File:

- [`../../scripts/vision_runtime_bridge.py`](../../scripts/vision_runtime_bridge.py)

`vision.bridge.state.json` now includes `lastDecision`, which captures:

- `candidateScene`
- `candidateReason`
- `sceneAllowed`
- `sceneAllowedReason`
- detector gate results
- touch / hand-avoid evaluation results
- `selectedTrackId`
- `selectedReason`
- final `action`
- final `actionReason`

This is the new primary source for answering:

```text
why did the bridge choose this
why was it blocked
why did the lamp react this way
```

### 5. Director console now surfaces bridge decision context

Files:

- [`../../web/index.html`](../../web/index.html)
- [`../../web/app.js`](../../web/app.js)
- [`../../web/styles.css`](../../web/styles.css)

The Vision panel now shows:

- a `Bridge Decision` summary card
- selected-target reason text in the tracks area

This reduces the need to tail logs during rehearsal.

### 6. Vision stack launcher exposes new tuning knobs

File:

- [`../../scripts/run_mira_light_vision_stack.sh`](../../scripts/run_mira_light_vision_stack.sh)

New environment variables:

- `MIRA_LIGHT_SELECTED_TARGET_MAX_CENTER_DISTANCE`
- `MIRA_LIGHT_SELECTED_TARGET_MAX_SIZE_DELTA`
- `MIRA_LIGHT_SELECTED_TARGET_SWITCH_MARGIN`

These map directly to the extractor continuity tuning.

## Why This Matters

Before this upgrade, the system already had:

```text
camera input -> event extractor -> runtime bridge -> tracking updates
```

But the highest-value stability gap was still:

```text
can the lamp keep attending to the same person
without jittering, dropping, or switching too easily
```

This change is meant to improve exactly that layer before adding more scene complexity.

## Validation

### Unit Tests

Relevant test files:

- [`../../tests/test_track_target_event_extractor.py`](../../tests/test_track_target_event_extractor.py)
- [`../../tests/test_vision_runtime_bridge.py`](../../tests/test_vision_runtime_bridge.py)

New test coverage now includes:

- recovering a previous selected target by spatial continuity
- keeping a visible target when the score gap is not decisive
- recording bridge `lastDecision` for both successful tracking and blocked detections

### Manual Validation

Run in this order:

1. [Director Console Vision UI 1-Minute Smoke Checklist](./21-director-console-vision-ui-smoke-checklist.md)
2. [Vision Pipeline CLI 1-Minute Smoke Checklist](./22-vision-pipeline-cli-1-minute-smoke-checklist.md)
3. [Vision + Runtime + Scene 5-Minute Integration Checklist](./23-vision-runtime-scene-5-minute-integration-checklist.md)

During rehearsal, pay special attention to:

- `selected_target.reason`
- `lastDecision.candidateReason`
- `lastDecision.action`
- `lastDecision.actionReason`

## Recommended Tuning Order

If target selection still feels unstable, adjust in this order:

1. `MIRA_LIGHT_SELECTED_TARGET_SWITCH_MARGIN`
2. `MIRA_LIGHT_SELECTED_TARGET_MAX_CENTER_DISTANCE`
3. `MIRA_LIGHT_SELECTED_TARGET_MAX_SIZE_DELTA`

Guidance:

- increase `SWITCH_MARGIN` when the lamp switches too eagerly between nearby candidates
- increase `MAX_CENTER_DISTANCE` slightly when the same person jitters enough to lose continuity
- increase `MAX_SIZE_DELTA` only if scale changes are real and continuity still fails

Keep changes small.
Large increases can make the lamp cling to the wrong target.

## Current Limits

This upgrade still does not solve:

- true tabletop object tracking
- robust hand detection under complex lighting
- identity-grade multi-person tracking
- true depth estimation

Those remain the next layers after this stability pass.

## One-Line Summary

This upgrade makes the current person-following CV line more usable for booth rehearsal by improving selected-target continuity, exposing bridge decisions, and adding tuning knobs that can be adjusted without changing code.
