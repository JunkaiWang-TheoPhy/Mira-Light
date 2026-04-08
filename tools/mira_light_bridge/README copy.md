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
POST /v1/mira-light/stop
POST /v1/mira-light/reset
POST /v1/mira-light/control
POST /v1/mira-light/led
POST /v1/mira-light/action
POST /v1/mira-light/config
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

## Mock Device Rehearsal

When the physical lamp is unavailable, you can rehearse the full stack against a
stateful local mock device instead of plain `dryRun`.

Start the mock lamp:

```bash
bash scripts/run_mock_lamp.sh --host 127.0.0.1 --port 9791 --led-count 40
```

Point the bridge at the mock lamp and disable `dryRun`:

```bash
curl -X POST http://127.0.0.1:9783/v1/mira-light/config \
  -H "Authorization: Bearer $MIRA_LIGHT_BRIDGE_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"baseUrl":"http://127.0.0.1:9791","dryRun":false}'
```

The mock device exposes:

```text
GET  /health
GET  /status
GET  /led
GET  /actions
POST /control
POST /reset
POST /led
POST /action
POST /action/stop
```

This lets the bridge, director console, and OpenClaw plugin work against a
real HTTP target with servo state, LED state, and action playback.

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
<<<<<<< Updated upstream

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
=======
>>>>>>> Stashed changes
