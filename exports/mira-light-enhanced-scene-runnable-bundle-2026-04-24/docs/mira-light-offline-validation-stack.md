# Mira Light Offline Validation Stack

This document turns the current offline development order into a concrete local
workflow that does not require the real lamp to be reachable.

## Why this stack exists

The real lamp is still the final authority for calibration, material feel, and
physical safety. But most of the engineering work does not need live hardware.

The offline stack lets us validate:

1. bridge/runtime integration
2. scene choreography shape
3. vision-to-scene decisions
4. degraded/error behavior
5. memory/persona alignment inside OpenClaw

## Actual order

1. Mock Device
2. Mock E2E tests
3. Scene Trace Recorder
4. Vision Replay Bench
5. Fault injection
6. Memory/Persona Eval

That order matters because each layer becomes the substrate for the next one.

## 1. Mock Device

Use [mock_mira_light_device.py](/Users/huhulitong/Documents/GitHub/Mira-Light/scripts/mock_mira_light_device.py)
to simulate the raw ESP32 HTTP contract:

- `GET /health`
- `GET /status`
- `GET /led`
- `GET /sensors`
- `GET /actions`
- `POST /control`
- `POST /led`
- `POST /sensors`
- `POST /action`
- `POST /action/stop`
- `POST /reset`

It also exposes admin endpoints for observability and fault control:

- `GET /__admin/state`
- `GET /__admin/requests`
- `GET /__admin/faults`
- `POST /__admin/faults`
- `POST /__admin/reset-state`
- `POST /__admin/device-state`

The signal contract follows
[09-Mira Light统一信号交付格式说明.md](/Users/huhulitong/Documents/GitHub/Mira-Light/Mira_Light_Released_Version/docs/Guide/09-Mira%20Light统一信号交付格式说明.md):

- `/status` is the formal unified read surface: `servos + sensors + led`
- LED writes should send `pixels`
- LED reads should inspect `pixelSignals`
- `headCapacitive` remains `0 | 1`

Example:

```bash
./.venv/bin/python scripts/mock_mira_light_device.py \
  --port 9799 \
  --request-log-out runtime/mock-device.requests.jsonl \
  --state-out runtime/mock-device.state.json
```

## 2. Mock E2E tests

The offline bridge/runtime/device path is covered by
[test_mock_device_e2e.py](/Users/huhulitong/Documents/GitHub/Mira-Light/tests/test_mock_device_e2e.py).

It proves two things:

- a real scene can flow from bridge -> runtime -> mock device
- faulted device responses still surface cleanly at the bridge

Run:

```bash
./.venv/bin/python -m unittest tests.test_mock_device_e2e
```

## 3. Scene Trace Recorder

Use [scene_trace_recorder.py](/Users/huhulitong/Documents/GitHub/Mira-Light/scripts/scene_trace_recorder.py)
to record a full scene timeline as both JSON and HTML.

This is the best offline way to inspect whether a scene still feels like Mira:

- are the pauses too short
- is the step order emotionally legible
- are raw requests matching the intended choreography

Example:

```bash
./.venv/bin/python scripts/scene_trace_recorder.py farewell \
  --dry-run \
  --skip-delays \
  --out-dir runtime/scene-traces
```

Outputs:

- `runtime/scene-traces/farewell.trace.json`
- `runtime/scene-traces/farewell.trace.html`

## 4. Vision Replay Bench

Use [vision_replay_bench.py](/Users/huhulitong/Documents/GitHub/Mira-Light/scripts/vision_replay_bench.py)
to replay saved JPEGs through:

- extractor
- event generation
- scene suggestion
- runtime decision rules

This bench uses the same extractor and bridge-side decision logic as the live
stack, but makes replay deterministic and hardware-free.

If you do not yet have real captures, generate a synthetic demo sequence:

```bash
./.venv/bin/python scripts/vision_replay_bench.py \
  --captures-dir runtime/vision-demo-captures \
  --out-dir runtime/vision-replay \
  --dry-run \
  --allow-experimental \
  --generate-synthetic-demo
```

Outputs:

- `runtime/vision-replay/vision.latest.json`
- `runtime/vision-replay/vision.events.jsonl`
- `runtime/vision-replay/vision.bridge.state.json`
- `runtime/vision-replay/vision.replay.report.json`

## 5. Fault injection

The mock device has built-in fault rules, so fault injection does not need a
separate simulator.

Example one-shot rules are in
[mira_light_mock_faults.example.json](/Users/huhulitong/Documents/GitHub/Mira-Light/config/mira_light_mock_faults.example.json).

You can load them at process start:

```bash
./.venv/bin/python scripts/mock_mira_light_device.py \
  --port 9799 \
  --fault-file config/mira_light_mock_faults.example.json
```

Or inject them live:

```bash
curl -X POST http://127.0.0.1:9799/__admin/faults \
  -H 'Content-Type: application/json' \
  -d @config/mira_light_mock_faults.example.json
```

Current fault modes:

- `http_error`
- `invalid_json`
- `timeout`
- `disconnect`
- `delay`

## 6. Memory / Persona Eval

Use [mira_memory_persona_eval.py](/Users/huhulitong/Documents/GitHub/Mira-Light/scripts/mira_memory_persona_eval.py)
with the default checklist
[mira_memory_persona_eval.json](/Users/huhulitong/Documents/GitHub/Mira-Light/config/mira_memory_persona_eval.json).

This evaluator checks three layers:

1. `openclaw memory search` retrieval quality
2. whether workspace files still encode Mira correctly
3. whether the local OpenClaw agent answers in-character

Example against the live local workspace:

```bash
./.venv/bin/python scripts/mira_memory_persona_eval.py \
  --workspace ~/.openclaw/workspace \
  --out runtime/mira-memory-persona-eval.json
```

Example against the repository template workspace only:

```bash
./.venv/bin/python scripts/mira_memory_persona_eval.py \
  --workspace "Claw-Native /workspace" \
  --skip-agent-prompts
```

## Fast smoke ladder

When you only want the shortest confidence pass, use this order:

```bash
./.venv/bin/python -m unittest tests.test_mock_device_e2e
./.venv/bin/python scripts/scene_trace_recorder.py farewell --dry-run --skip-delays
./.venv/bin/python scripts/vision_replay_bench.py --captures-dir runtime/vision-demo-captures --out-dir runtime/vision-replay --dry-run --allow-experimental --generate-synthetic-demo
./.venv/bin/python scripts/mira_memory_persona_eval.py --workspace ~/.openclaw/workspace
```

## One-click rehearsal

The repository now includes a thin one-click entry point on top of the
individual tools:

- [run_mira_light_offline_rehearsal.py](/Users/huhulitong/Documents/GitHub/Mira-Light/scripts/run_mira_light_offline_rehearsal.py)
- [run_mira_light_offline_rehearsal.sh](/Users/huhulitong/Documents/GitHub/Mira-Light/scripts/run_mira_light_offline_rehearsal.sh)
- [mira_light_offline_rehearsal.json](/Users/huhulitong/Documents/GitHub/Mira-Light/config/mira_light_offline_rehearsal.json)

Supported modes:

- `quick`: mock E2E + one scene trace + retrieval/file eval
- `full`: tests + scene trace + vision replay + live persona prompts
- `fault`: boot with injected faults, then rehearse bridge/runtime resilience
- `interactive`: keep the mock device running for manual experimentation

Examples:

```bash
bash scripts/run_mira_light_offline_rehearsal.sh --mode quick
bash scripts/run_mira_light_offline_rehearsal.sh --mode full
bash scripts/run_mira_light_offline_rehearsal.sh --mode fault
bash scripts/run_mira_light_offline_rehearsal.sh --mode interactive
```

Each run creates a timestamped folder under:

```text
runtime/offline-rehearsal/<timestamp>-<mode>/
```

That folder contains:

- `summary.json`
- `index.html`
- per-step logs
- mock device request/state artifacts
- scene trace outputs
- vision replay outputs
- memory/persona report when enabled

Use this entry point when you want a repeatable offline demo or regression pass
without remembering the exact tool order.

## What this still does not replace

- true servo calibration
- thermal / power behavior on the real lamp
- real hotspot or booth network behavior
- real material feel of light through the physical shell
- touch or proximity sensor tuning on hardware
