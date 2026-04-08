# Mira Light Claw-Native Rollout State

Date: `2026-04-09`

## Purpose

This note records what was actually completed on the verified local machine, so
future work can distinguish between:

- repository packaging that exists
- machine rollout that was really executed
- remaining blockers outside the repository

## Completed on the local machine

- OpenClaw installed and running locally
- gateway mode set to `local`
- gateway LaunchAgent working
- `mira-light-bridge` plugin discoverable through:
  - `plugins.allow`
  - `plugins.load.paths`
  - `plugins.entries`
- default model pinned to `openai-codex/gpt-5.4`
- Mira workspace identity files installed under `~/.openclaw/workspace`
- bridge env helper installed
- vision env helper installed
- bridge LaunchAgent working
- vision LaunchAgent working
- launchd-friendly service copy synced under `~/.openclaw/mira-light-service`
- bridge loading a real local profile
- `MIRA_LIGHT_SHOW_EXPERIMENTAL=1` enabled locally
- repository-native Claw-Native templates now exist under `Claw-Native `
- `python3 scripts/apply_claw_native_local.py --write` successfully materialized
  those templates back into the local machine
- memory indexing rebuilt successfully
- repo docs added through `memorySearch.extraPaths`
- local semantic memory is now enabled through `node-llama-cpp`
- local embedding model file exists at
  `~/.openclaw/models/embeddinggemma-300m-qat-Q8_0.gguf`

## Verified with commands

- `openclaw models status --json`
- `openclaw memory status --json`
- `openclaw gateway status --json`
- `openclaw plugins doctor`
- `python3 scripts/apply_claw_native_local.py --write`
- `python3 scripts/verify_local_openclaw_mira_light.py`
- `openclaw memory index --force`
- `openclaw memory status --deep --json`
- `curl http://127.0.0.1:9783/health`
- `curl http://127.0.0.1:8000/health`

## Vision stack verification result

The vision stack was verified end to end with a synthetic local JPEG frame.

Observed outputs:

- saved capture under `workspace/runtime/captures`
- generated `vision.latest.json`
- appended `vision.events.jsonl`
- updated `vision.bridge.state.json`

This confirms that the local software chain is alive even before the real lamp
becomes reachable again.

## Remaining blockers

### Physical lamp network

The lamp URL used by the local machine is:

- `http://172.20.10.3`

The local machine still could not reach it at verification time:

- `ping` failed
- `/status` timed out
- `/led` timed out

An additional clue on that machine:

- route to `172.20.10.3` was being sent via `utun8`

So the current blocker is network reachability, not missing OpenClaw or Mira
configuration.

### Semantic memory

Semantic memory is now working locally.

Verified state on the machine:

- `provider = local`
- `requestedProvider = local`
- `vector.available = true`
- `custom.searchMode = hybrid`
- `embeddingProbe.ok = true`

This means the verified machine no longer depends on a cloud embeddings API for
memory search.

## How to read this with the rest of Claw-Native

- `README.md`: package map
- `mira-light-claw-native-overview.md`: architecture and introduction
- `mira-light-claw-native-runbook.md`: rollout instructions
- `mira-light-claw-native-automation.md`: automation and apply flow
- this file: actual rollout state on the verified machine
