# Mira Light Claw-Native Overview

## What "Claw-Native" means here

In this repository, `Claw-Native` means:

- Mira is not only a chat prompt
- Mira has an OpenClaw-native workspace identity
- Mira uses plugin tools instead of raw device HTTP by default
- Mira can run as an always-on local service stack
- Mira's behavior is organized around scenes, memory, and safety boundaries

This package reflects the local rollout that was verified on this machine on
`2026-04-09`.

## Architecture summary

The current local shape is:

```text
OpenClaw gateway
-> Mira workspace identity + memory
-> mira-light-bridge plugin
-> local bridge on 127.0.0.1:9783
-> Mira Light runtime
-> ESP32 lamp
```

The live vision extension is:

```text
camera JPEG stream
-> cam_receiver_service.py
-> track_target_event_extractor.py
-> vision.latest.json / vision.events.jsonl
-> vision_runtime_bridge.py
-> Mira runtime scene decisions
```

## The five layers

### 1. Identity layer

Defined by workspace files:

- `workspace/IDENTITY.md`
- `workspace/SOUL.md`
- `workspace/AGENTS.md`
- `workspace/USER.md`

This is where OpenClaw stops being a generic coding/runtime agent and starts
behaving like Mira.

### 2. Memory layer

Defined by:

- `workspace/MEMORY.md`
- `workspace/memory/`
- `templates/openclaw.template.jsonc`

Current verified state:

- builtin memory backend
- FTS indexing works
- repo docs are indexed via `memorySearch.extraPaths`
- semantic embeddings are not configured yet

### 3. Tool layer

Defined by:

- `tools/mira_light_bridge/openclaw_mira_light_plugin/`
- `workspace/skills/mira-light-orchestrator/SKILL.md`

This is the layer that keeps Mira scene-first:

- status first
- scenes before raw joints
- low-level control only for calibration or recovery

### 4. Service layer

Defined by:

- `templates/mira-light-bridge-wrapper.sh`
- `templates/mira-light-vision-wrapper.sh`
- `templates/launchd/*.plist.example`
- `scripts/sync_local_mira_light_service.py`
- `scripts/setup_local_mira_light_service_env.sh`
- `scripts/run_mira_light_vision_stack.sh`

This is what turns the repo from "files that can be run" into "a local node
that stays alive after reboot".

### 5. Safety layer

The system is intentionally conservative:

- loopback bridge boundary
- token-protected plugin calls
- scene-first motion policy
- experimental scenes separated from stable defaults
- vision treated as hint data, not direct servo angles

## Current verified status

As of `2026-04-09`, the following are confirmed:

- local OpenClaw gateway is working
- `mira-light-bridge` plugin is discoverable and healthy
- the active local model remains machine-configurable and is no longer
  template-pinned by `Claw-Native`
- Mira workspace identity files are active locally
- launchd-managed bridge service is working
- launchd-managed vision stack is working
- synthetic JPEG test produced:
  - saved capture
  - `vision.latest.json`
  - `vision.events.jsonl`
  - `vision.bridge.state.json`
- memory index includes both workspace notes and key Mira docs

## Current non-local blocker

The remaining blocker is not the Claw-native packaging. It is physical network
reachability to the lamp:

- target lamp URL: `http://172.20.10.3`
- current observed issue on the verified machine:
  - routed via `utun8`
  - `ping` fails
  - `/status` times out
  - `/led` times out

That means the local software stack is ready, but the physical lamp is still
outside the machine's reachable network plane.

## How to introduce this setup to others

The shortest accurate introduction is:

> Mira Light Claw-Native is a local OpenClaw-based embodied agent package.
> It gives Mira a workspace identity, a scene-first motion skill, a protected
> bridge boundary, an always-on local vision/runtime stack, and enough memory
> structure to behave like a persistent character instead of a one-off prompt.
