# Mira Light Operator Cheatsheet

## Service layout

- Gateway LaunchAgent: `ai.openclaw.gateway`
- Bridge LaunchAgent: `ai.mira-light.bridge`
- Vision LaunchAgent: `ai.mira-light.vision`
- Bridge env helper: `__HOME__/.openclaw/mira-light-bridge.env`
- Vision env helper: `__HOME__/.openclaw/mira-light-vision.env`
- Service copy root: `__HOME__/.openclaw/mira-light-service`

## Verification commands

- `openclaw gateway status --json`
- `launchctl print gui/$(id -u)/ai.mira-light.bridge | sed -n '1,120p'`
- `launchctl print gui/$(id -u)/ai.mira-light.vision | sed -n '1,120p'`
- `curl -s http://127.0.0.1:9783/health`
- `curl -s http://127.0.0.1:8000/health`
- `source ~/.openclaw/mira-light-bridge.env && python3 scripts/verify_local_openclaw_mira_light.py --bridge-token "$MIRA_LIGHT_BRIDGE_TOKEN"`

## Sync + restart flow

- If workspace identity files changed:
  - copy the updated files into `__HOME__/.openclaw/workspace/`
  - run `openclaw memory index`
- If plugin files changed:
  - `launchctl kickstart -k gui/$(id -u)/ai.openclaw.gateway`
- `python3 scripts/sync_local_mira_light_service.py`
- `launchctl kickstart -k gui/$(id -u)/ai.mira-light.bridge`
- `launchctl kickstart -k gui/$(id -u)/ai.mira-light.vision`

## Current limitations to record per machine

- whether the lamp is physically reachable
- whether vision has been validated with a real stream or only a synthetic frame
- whether memory is FTS-only or has semantic embeddings
- whether Docker is installed for non-main sandbox execution
