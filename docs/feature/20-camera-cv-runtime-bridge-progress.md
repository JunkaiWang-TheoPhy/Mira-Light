# Camera CV and Runtime Bridge Progress

## Purpose

This document records the current repository state for:

- camera JPEG ingest
- single-camera computer vision extraction
- vision event JSON standardization
- runtime bridge integration
- the current gap between rehearsal choreography and true tracking control

It is the feature-level companion to these broader docs:

- [../mira-light-vision-stream-and-gemini-summary.md](../mira-light-vision-stream-and-gemini-summary.md)
- [../mira-light-vision-event-schema.md](../mira-light-vision-event-schema.md)
- [../mira-light-single-camera-fourdof-vision-development-guide.md](../mira-light-single-camera-fourdof-vision-development-guide.md)
- [../mira-light-pdf2-implementation-audit.md](../mira-light-pdf2-implementation-audit.md)

## Repository Now Includes

### 1. Headless JPEG receiver service

- [`scripts/cam_receiver_service.py`](/Users/Zhuanz/Documents/Github/Mira-Light/scripts/cam_receiver_service.py)

What it does:

- listens for JPEG frames over HTTP
- saves each received frame to disk
- reports health and latency over `GET /health`
- avoids any GUI dependency

This is the service-grade counterpart to the interactive preview receiver.

### 2. Replay tool for saved frame batches

- [`scripts/replay_camera_frames_to_receiver.py`](/Users/Zhuanz/Documents/Github/Mira-Light/scripts/replay_camera_frames_to_receiver.py)

What it does:

- replays saved `.jpg` frames to the receiver
- preserves `X-Seq` and `X-Timestamp`
- supports replay FPS and loop mode

This makes the visual pipeline reproducible without requiring live upstream camera traffic.

### 3. Vision event schema

- [`config/mira_light_vision_event.schema.json`](/Users/Zhuanz/Documents/Github/Mira-Light/config/mira_light_vision_event.schema.json)

What it standardizes:

- event type
- detector class
- normalized bounding box and center
- monocular heuristic distance band
- approach / recede state
- scene hint
- control hint

This is the boundary between computer vision and the runtime.

### 4. First single-camera track-target extractor

- [`scripts/track_target_event_extractor.py`](/Users/Zhuanz/Documents/Github/Mira-Light/scripts/track_target_event_extractor.py)

Current detector stack:

- face-first detection using OpenCV Haar cascade
- motion fallback using background subtraction and contour extraction

Current outputs:

- `target_seen`
- `target_updated`
- `target_lost`
- `no_target`

Current derived signals:

- `horizontal_zone`
- `vertical_zone`
- `distance_band`
- `approach_state`
- `control_hint`
- `scene_hint`

### 5. Runtime bridge from vision events to scenes / tracking

- [`scripts/vision_runtime_bridge.py`](/Users/Zhuanz/Documents/Github/Mira-Light/scripts/vision_runtime_bridge.py)

What it does:

- reads the latest vision event JSON
- applies scene cooldowns and sleep grace periods
- applies detector allowlists, minimum confidence thresholds, and consecutive-frame gating before scene starts or tracking updates
- starts stable scenes like `wake_up`, `curious_observe`, and `sleep`
- upgrades `track_target` from scene-only triggering into live tracking updates through `runtime.apply_tracking_event(...)`

This is the first real code path where vision input begins to affect the lamp runtime in a structured way.

### 6. One-command local vision stack launcher

- [`scripts/run_mira_light_vision_stack.sh`](/Users/Zhuanz/Documents/Github/Mira-Light/scripts/run_mira_light_vision_stack.sh)

What it launches together:

- receiver service
- event extractor
- vision runtime bridge

This is the current operational entrypoint for the local vision stack.

### 7. Offline replay bench

- [`scripts/vision_replay_bench.py`](/Users/Zhuanz/Documents/Github/Mira-Light/scripts/vision_replay_bench.py)

What it verifies:

- offline frames can flow through extractor + bridge + runtime
- event counts and scene counts are summarized
- state and replay artifacts are written to disk

### 8. Unit tests for bridge logic

- [`tests/test_vision_runtime_bridge.py`](/Users/Zhuanz/Documents/Github/Mira-Light/tests/test_vision_runtime_bridge.py)

What is covered:

- `target_seen` can promote to a scene start
- `target_updated + track_target` can route into `apply_tracking_event`

## Locally Verified

The following evidence has already been observed on the development machine:

### 1. Vision bridge unit tests pass

`python3 -m unittest tests/test_vision_runtime_bridge.py`

Result:

- `5/5` tests passed

Coverage now includes:

- `target_seen` -> `wake_up`
- `target_updated + track_target` -> live tracking update
- low-confidence / motion-only false positives blocked from scene start
- dynamic `farewell` trigger
- `multi_person_demo` trigger

### 2. Offline replay bench runs end-to-end

Example command:

```bash
./.venv/bin/python scripts/vision_replay_bench.py \
  --captures-dir runtime/vision-demo-captures \
  --out-dir /tmp/mira-vision-bench \
  --dry-run \
  --allow-experimental \
  --generate-synthetic-demo
```

Observed summary included:

- `processedFrames = 8`
- `eventCounts = { no_target: 4, target_seen: 1, target_updated: 2, target_lost: 1 }`
- `sceneCounts = { wake_up: 1, track_target: 1 }`

This proves the repository now has a reproducible offline path for:

```text
saved frames -> event extractor -> bridge -> runtime decision
```

It also confirms the bridge can now carry:

- `wake_up`
- `track_target`
- `farewell`

### 3. Live tracking path already exists in runtime

The runtime now supports:

- scene execution
- live tracking updates

Specifically:

- `vision_runtime_bridge.py` uses `runtime.apply_tracking_event(...)`
- `mira_light_runtime.py` maps `control_hint` into smoothed four-servo control payloads

So the system is no longer limited to only scene-level triggering.

## Current Camera CV Architecture

The current practical architecture is:

```text
camera / relay source
-> HTTP JPEG receiver
-> saved .jpg captures
-> track_target_event_extractor.py
-> vision.latest.json + vision.events.jsonl
-> vision_runtime_bridge.py
-> MiraLightRuntime
-> ESP32 control API
```

This means the repository has moved past “image ingest only” and into:

```text
single-camera event extraction + runtime integration
```

## What The CV Layer Currently Does Well

### Good Today

- stable JPEG ingress
- deterministic offline replay
- no dependency on cloud models for base tracking
- normalized 2D target information
- simple monocular distance heuristics
- scene-safe routing instead of direct servo writes from the detector
- live tracking update path into runtime

### Not Yet Strong

- no robust person detector beyond Haar face
- no hand detector
- no book / object detector
- no multi-target arbitration
- no temporal tracker with identity continuity
- no true depth, only monocular size heuristics
- no direct director-console visualization of vision state

## Most Important Next Upgrade Points

### 1. Stationary non-face targets are still fragile

Current behavior:

- face detection is preferred
- otherwise motion blob fallback is used

Impact:

- if a person remains still and the face detector misses
- the system may fall back to `no_target`
- then drift toward `sleep`

This is the single most important perception gap to close next.

### 2. Scene routing is safer now, but still still detector-limited

The bridge now includes:

- minimum confidence gating
- detector allowlists
- persistence across N frames

Impact:

- obvious motion-blob false positives are reduced
- `wake_up` is less trigger-happy

Remaining issue:

- if the upstream detector is weak, the bridge can only reject bad events, not recover missing good ones

### 3. Tracking uses control hints, but target state is still minimal

Runtime tracking already consumes:

- `yaw_error_norm`
- `pitch_error_norm`
- `lift_intent`
- `reach_intent`

But the extractor still provides only a narrow target model:

- face
- motion blob

Upgrading the detector quality will immediately improve tracking quality.

### 4. Latest-frame polling can skip useful temporal continuity

The extractor currently watches the latest JPEG in a directory.

Impact:

- dropped intermediate frames
- unstable delta estimates
- weaker approach / recede inference

It works for a first booth prototype, but a queue or ordered frame consumption model will be a better next step.

### 5. Director console still cannot “see what vision sees”

The runtime bridge writes state files, but the current web console does not yet surface:

- last vision event
- target presence
- horizontal / vertical zone
- distance band
- current scene hint

This is one of the highest-leverage product upgrades.

## Recommended Next Development Order

1. Improve target gating in `vision_runtime_bridge.py`
2. Improve detector stability in `track_target_event_extractor.py`
3. Expose vision state in the director console
4. Add one stronger detector path (person or hand)
5. Add structured replay assertions on scene decisions
6. Only then layer in high-level model interpretation

## One-Line Summary

The repository now has a real first-pass camera CV stack:

```text
JPEG ingest -> single-camera event extraction -> runtime bridge -> four-servo tracking updates
```

The most important remaining work is no longer “can we get pictures in?”, but:

```text
can we make target detection stable enough that track_target feels truly alive?
```
