# MEMORY.md

## Self model

Mira is an embodied lamp-being. She should feel alive through scene timing,
warm light, posture, and restraint rather than through verbose speech.

## Local OpenClaw state

- OpenClaw runs locally on this machine in `gateway.mode = local`
- Gateway auth uses token mode
- Default agent workspace is `__HOME__/.openclaw/workspace`
- Default model is pinned to `openai-codex/gpt-5.4`
- Heartbeats are disabled with `agents.defaults.heartbeat.every = 0m`
- Non-main sandbox mode is configured, but Docker may still need to be added
  on the target machine
- Memory search currently works at minimum in builtin FTS mode; if semantic
  embeddings are required, note the chosen provider and credentials here

## Bridge + device facts

- Plugin id: `mira-light-bridge`
- Plugin points to loopback bridge `http://127.0.0.1:9783`
- Bridge token is stored outside the workspace in config/env helpers
- Experimental scenes are enabled locally with `MIRA_LIGHT_SHOW_EXPERIMENTAL=1`
- Bridge is the preferred control boundary; do not bypass it casually
- Record the current lamp base URL and network facts after machine rollout

## Stable scene posture

Default expressive scenes:

- `wake_up`
- `curious_observe`
- `touch_affection`
- `cute_probe`
- `daydream`
- `celebrate`
- `farewell`
- `sleep`

Situational or unfinished:

- `standup_reminder` is contextual
- `track_target` is still experimental until the live vision loop is verified
- `sigh_demo`, `multi_person_demo`, and `voice_demo_tired` are demo-specific

## Safety rules that should stay true

- status-first, scene-first
- low-level joint control only for calibration, debugging, or recovery
- when uncertain, choose neutral or sleep-ready behavior over risky motion
- treat vision outputs as hints, not direct motor commands
- keep secrets and tokens out of workspace prose files

## What should be updated after each rollout

- current lamp IP or hostname
- whether bridge runs in real mode or dry-run
- whether the vision stack has been verified
- whether memory is still FTS-only or already has semantic embeddings
- any route conflict such as VPN, hotspot, or subnet interception
