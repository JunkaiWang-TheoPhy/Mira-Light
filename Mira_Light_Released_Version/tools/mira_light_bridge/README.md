# Mira Light Bridge

This directory contains the local bridge layer for the physical Mira Light lamp.

It follows the same local-device pattern already used elsewhere in the Mira /
Javis ecosystem:

- the physical device stays on the local LAN
- a loopback bridge wraps that device with a stable API
- a remote OpenClaw runtime can later reach the bridge through an SSH reverse tunnel

## Why This Exists

The ESP32 lamp itself exposes a simple HTTP API, but it is not the right
long-term contract for remote orchestration:

- the lamp usually lives on a private LAN
- the lamp IP may change
- scene triggering should be higher-level than raw `/control`
- OpenClaw should talk to a bridge, not to ad hoc booth scripts

## Local Bridge

Local bridge default:

```text
http://127.0.0.1:9783
```

Health endpoint:

```text
GET /health
```

Authenticated endpoints:

```text
GET  /v1/mira-light/status
GET  /v1/mira-light/led
GET  /v1/mira-light/actions
GET  /v1/mira-light/runtime
GET  /v1/mira-light/scenes
GET  /v1/mira-light/profile
POST /v1/mira-light/run-scene
POST /v1/mira-light/trigger
POST /v1/mira-light/speak
POST /v1/mira-light/stop
POST /v1/mira-light/reset
POST /v1/mira-light/control
POST /v1/mira-light/led
POST /v1/mira-light/action
POST /v1/mira-light/config
POST /v1/mira-light/profile/capture-pose
POST /v1/mira-light/profile/set-servo-meta
```

All `/v1/...` endpoints require:

```text
Authorization: Bearer $MIRA_LIGHT_BRIDGE_TOKEN
```

If `MIRA_LIGHT_BRIDGE_TOKEN` is unset, the bridge currently accepts local calls
without authorization. For remote use, set the token before exposing the bridge
through a tunnel.

## Files

- `bridge_config.json`: local bridge defaults
- `bridge_server.py`: local loopback bridge service
- `start_bridge.sh`: bring up the bridge locally
- `start_tunnel.sh`: open an SSH reverse tunnel to a remote host
- `openclaw_mira_light_plugin/`: remote OpenClaw plugin package

## Local Usage

Set a token:

```bash
export MIRA_LIGHT_BRIDGE_TOKEN=test-token
```

Start the bridge:

```bash
zsh tools/mira_light_bridge/start_bridge.sh
```

Check health:

```bash
curl http://127.0.0.1:9783/health
```

Read scenes:

```bash
curl http://127.0.0.1:9783/v1/mira-light/scenes \
  -H "Authorization: Bearer $MIRA_LIGHT_BRIDGE_TOKEN"
```

Run a scene:

```bash
curl http://127.0.0.1:9783/v1/mira-light/run-scene \
  -H "Authorization: Bearer $MIRA_LIGHT_BRIDGE_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"scene":"wake_up","async":true}'
```

Speak a short public line:

```bash
curl http://127.0.0.1:9783/v1/mira-light/speak \
  -H "Authorization: Bearer $MIRA_LIGHT_BRIDGE_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"text":"你好，我是 Mira。","voice":"openclaw","wait":true}'
```

The bridge keeps `speak` intentionally constrained:

- prefer `run-scene` for expressive behavior
- use `speak` for short public lines, host cues, and quick confirmations
- the bridge rejects overlong text instead of turning Mira into a long-form TTS narrator

## Offline Rehearsal

The repository now includes a one-click offline rehearsal entry that uses the
new mock device and validation tools instead of the real lamp.

Primary entry points:

- `bash scripts/run_mira_light_offline_rehearsal.sh --mode quick`
- `bash scripts/run_mira_light_offline_rehearsal.sh --mode full`
- `bash scripts/run_mira_light_offline_rehearsal.sh --mode fault`
- `bash scripts/run_mira_light_offline_rehearsal.sh --mode interactive`

This runner orchestrates:

- `scripts/mock_mira_light_device.py`
- `tests.test_mock_device_e2e`
- `scripts/scene_trace_recorder.py`
- `scripts/vision_replay_bench.py`
- `scripts/mira_memory_persona_eval.py`

Outputs land under:

```text
runtime/offline-rehearsal/<timestamp>-<mode>/
```

Look at `summary.json` or `index.html` in that folder for the final report.
For the full step-by-step explanation, see:

- `docs/mira-light-offline-validation-stack.md`

Run a scene as a full director cue:

```bash
curl http://127.0.0.1:9783/v1/mira-light/run-scene \
  -H "Authorization: Bearer $MIRA_LIGHT_BRIDGE_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "scene": "celebrate",
    "async": true,
    "cueMode": "director"
  }'
```

Trigger a live interaction:

```bash
curl http://127.0.0.1:9783/v1/mira-light/trigger \
  -H "Authorization: Bearer $MIRA_LIGHT_BRIDGE_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "event": "farewell_detected",
    "payload": {
      "direction": "right",
      "cueMode": "director"
    }
  }'
```

## Remote Tunnel

Recommended tunnel style:

```bash
MIRA_LIGHT_BRIDGE_REMOTE=ubuntu@43.160.217.153 \
MIRA_LIGHT_BRIDGE_REMOTE_BIND_PORT=19783 \
zsh tools/mira_light_bridge/start_tunnel.sh
```

This makes the bridge available to the remote host on:

```text
http://127.0.0.1:19783
```

## OpenClaw Plugin

The plugin package in `openclaw_mira_light_plugin/` is the intended remote
consumer of this bridge. The long-term shape is:

```text
ESP32 lamp
-> local bridge
-> SSH reverse tunnel
-> remote OpenClaw plugin
-> OpenClaw tools
```

## Embodied Memory

The bridge can now write selected scene and device outcomes into Mira's
`memory-context` service without changing the existing bridge API.

Configure `bridge_config.json`:

```json
{
  "memoryContext": {
    "enabled": true,
    "baseUrl": "http://127.0.0.1:3301",
    "authTokenEnv": "MIRA_MEMORY_CONTEXT_AUTH_TOKEN",
    "userId": "mira-light-bridge"
  }
}
```

Recommended cloud-side pairing in Mira V3:

- keep `MIRA_OPENCLAW_PROMPT_PACK_ENABLED=true`
- set `MIRA_LINGZHU_PROMPT_PACK_ADDITIONAL_USER_IDS=mira-light-bridge`

That lets the main Mira prompt pack pull recent embodied memories written by
the bridge, such as:

- scene success or failure outcomes
- device status snapshots
- device error or warning events

The bridge intentionally skips low-value `hello` and `heartbeat` reports to
avoid flooding memory with telemetry noise.
