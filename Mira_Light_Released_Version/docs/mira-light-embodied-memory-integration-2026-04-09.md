# Mira Light Embodied Memory Integration

## Purpose

This document explains the concrete `Mira-Light` changes that turn the lamp
bridge from a pure execution surface into an **embodied memory producer** for
cloud Mira.

It is not a generic architecture essay. It documents what was actually added,
why it matters, and how it should be used together with `Mira_v3`.

## What Changed

The `Mira-Light` codebase now contains a first-pass embodied memory writer.

New behavior:

- scene outcomes can be written into Mira's `memory-context`
- selected device reports can be written into Mira's `memory-context`
- bridge configuration now contains a `memoryContext` block
- the runtime records scene completion and failure as typed memory events

Primary implementation files:

- [tools/mira_light_bridge/embodied_memory_client.py](./../tools/mira_light_bridge/embodied_memory_client.py)
- [tools/mira_light_bridge/bridge_server.py](./../tools/mira_light_bridge/bridge_server.py)
- [tools/mira_light_bridge/bridge_config.json](./../tools/mira_light_bridge/bridge_config.json)
- [scripts/mira_light_runtime.py](./../scripts/mira_light_runtime.py)
- [tests/test_embodied_memory.py](./../tests/test_embodied_memory.py)

## Why This Matters

Before this change, `Mira-Light` was mostly an execution surface:

- it could run scenes
- it could expose bridge endpoints
- it could receive device reports

But none of those events naturally became part of Mira's longer-lived memory.

After this change, `Mira-Light` can contribute:

- scene success or failure
- bridge-relevant device state
- device warning or error events

to Mira's typed memory layer.

That moves `Mira-Light` one step higher in the companion architecture:

```text
scene bridge
-> embodied event capture
-> typed memory write
-> prompt-pack resurfacing in cloud Mira
```

## Data Flow

The new intended path is:

```text
Mira-Light scene or device event
-> embodied_memory_client.py
-> Mira_v3 memory-context /v1/memory/write
-> typed memory tables
-> prompt-pack retrieval
-> Lingzhu adapter system prompt
-> Mira reply / decision
```

This is intentionally **not** a direct path from lamp event to autonomous
action. The memory write creates context. It does not skip judgment.

## What Gets Written

### Scene outcomes

When a scene finishes, `MiraLightRuntime` now records an embodied outcome.

Typical episodic write:

- `namespace=home`
- `layer=episodic`
- `kind=execution_outcome`

If a scene fails or stops abnormally, a second working-memory item is written
to keep the failure visible for a limited time.

Typical working write:

- `namespace=home`
- `layer=working`
- `kind=scene_state`

This is the right split:

- episodic memory preserves what happened
- working memory preserves what still matters *right now*

### Device reports

`bridge_server.py` now selectively mirrors some `/device/*` reports:

- `/device/status`
- `/device/event`

into `memory-context`.

The policy is intentionally selective:

- `hello` is ignored
- `heartbeat` is ignored
- normal low-value traffic should not flood memory

This keeps the embodied layer useful instead of noisy.

## Current Write Policy

Persist first:

- scene success or failure that affects later decisions
- degraded or unreachable device state
- explicit device error or warning events

Do not persist by default:

- repetitive heartbeats
- pure liveness chatter
- raw telemetry without decision value

This follows the same design rule stated in
[mira-context-proactivity-architecture.md](./mira-context-proactivity-architecture.md):

capture **intent-relevant anchors**, not endless dense logging.

## Configuration

`bridge_config.json` now contains:

```json
{
  "memoryContext": {
    "enabled": false,
    "baseUrl": "http://127.0.0.1:3301",
    "authTokenEnv": "MIRA_MEMORY_CONTEXT_AUTH_TOKEN",
    "userId": "mira-light-bridge",
    "requestTimeoutSeconds": 2,
    "deviceStatusTtlSeconds": 900,
    "failureTtlSeconds": 3600
  }
}
```

Meaning:

- `enabled`
  turns embodied memory writes on or off
- `baseUrl`
  points to the cloud or local `memory-context` service
- `authTokenEnv`
  tells the bridge where to read the bearer token from
- `userId`
  defines the shared embodied writer identity

Recommended value:

- `userId=mira-light-bridge`

That shared id is what `Mira_v3` can later include through:

- `MIRA_LINGZHU_PROMPT_PACK_ADDITIONAL_USER_IDS=mira-light-bridge`

## Runtime Boundary

`Mira-Light` should **not** become a second full Mira runtime.

It should remain:

- the physical bridge
- the scene execution surface
- the embodied event producer

It should not own:

- long-term judgment
- proactive suggestion timing
- general-purpose companion conversation

That remains the job of `Mira_v3`.

## Relationship To The Five-Layer Mira Architecture

This implementation mainly strengthens:

- `Context Capture`
- `Timeline Memory`
- part of `Execution Layer`

It does **not** implement:

- task inference
- proactive suggestion logic
- conversation-level companion judgment

Those belong upstream in `Mira_v3`.

## Tests Added

Added test:

- [tests/test_embodied_memory.py](./../tests/test_embodied_memory.py)

It verifies:

- embodied memory client posts memory writes correctly
- bridge/runtime hooks actually emit scene and device outcomes

This makes the embodied-memory behavior part of the repository's formal
behavior, not just an undocumented side effect.

## Practical Interpretation

If someone asks what changed in `Mira-Light`, the shortest correct answer is:

`Mira-Light` can now feed the cloud Mira memory layer with selected scene and
device outcomes, so the lamp is no longer only something Mira controls - it is
also something Mira can remember.
