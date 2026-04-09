# TOOLS.md

This file records the machine and deployment facts that let Mira understand how
her current body is wired.

## Machine facts

- Repo root: `__REPO_ROOT__`
- OpenClaw state dir: `__HOME__/.openclaw`
- Active workspace: `__HOME__/.openclaw/workspace`
- User timezone: `__TIMEZONE__`
- Repo template does not pin a model; keep the current local model unless a
  human explicitly requests a change

## Self + deployment map

- Packaged identity source: `__REPO_ROOT__/Claw-Native /workspace/`
- Active identity files: `__HOME__/.openclaw/workspace/`
- Active OpenClaw config: `__HOME__/.openclaw/openclaw.json`
- Plugin code is loaded from
  `__REPO_ROOT__/tools/mira_light_bridge/openclaw_mira_light_plugin`
- Bridge and vision daemons run from `__HOME__/.openclaw/mira-light-service`

## Mira Light bridge

- Bridge launcher in repo: `__REPO_ROOT__/tools/mira_light_bridge/start_bridge.sh`
- Convenience launcher on PATH: `mira-light-bridge`
- LaunchAgent label: `ai.mira-light.bridge`
- Bridge config: `__REPO_ROOT__/tools/mira_light_bridge/bridge_config.json`
- Launchd-friendly service copy root: `__HOME__/.openclaw/mira-light-service`
- Bridge listens on `http://127.0.0.1:9783`
- Bridge auth reads env var `MIRA_LIGHT_BRIDGE_TOKEN`
- Bridge env helper file: `__HOME__/.openclaw/mira-light-bridge.env`
- Experimental scenes env: `MIRA_LIGHT_SHOW_EXPERIMENTAL=1`
- Current lamp base URL should be recorded here after machine setup

## OpenClaw gateway service

- LaunchAgent label: `ai.openclaw.gateway`
- Local dashboard: `http://127.0.0.1:18789/`
- Service status command: `openclaw gateway status`

## Update rules

- If `IDENTITY.md`, `SOUL.md`, `MEMORY.md`, `AGENTS.md`, or `TOOLS.md` changes,
  sync the corresponding files into `__HOME__/.openclaw/workspace/` and
  consider `openclaw memory index`
- If plugin files change, restart the gateway:
  `launchctl kickstart -k gui/$(id -u)/ai.openclaw.gateway`
- If bridge or vision runtime files change, run
  `python3 __REPO_ROOT__/scripts/sync_local_mira_light_service.py`, then
  restart:
  `launchctl kickstart -k gui/$(id -u)/ai.mira-light.bridge`
  `launchctl kickstart -k gui/$(id -u)/ai.mira-light.vision`

## OpenClaw plugin surface

The enabled plugin is `mira-light-bridge`. Prefer these tools in this order:

1. `mira_light_runtime_status`
2. `mira_light_status`
3. `mira_light_list_scenes`
4. `mira_light_run_scene`
5. `mira_light_speak` for short public lines only
6. `mira_light_set_led`
7. `mira_light_stop` / `mira_light_reset`
8. `mira_light_control_joints` only for calibration or recovery

## Scene guidance

- Good default scenes: `wake_up`, `curious_observe`, `touch_affection`,
  `cute_probe`, `daydream`, `celebrate`, `farewell`, `sleep`
- `standup_reminder` is situational and presentational
- `track_target` exists, but still depends on an unfinished live vision loop
- `sigh_demo`, `multi_person_demo`, and `voice_demo_tired` are demo-oriented

## Motion semantics

Servo meaning is provisional but stable enough for shared language:

- `servo1`: `base_yaw`
- `servo2`: `lower_arm_lift`
- `servo3`: `upper_arm_pitch`
- `servo4`: `head_tilt`

Canonical references:

- `__REPO_ROOT__/scripts/scenes.py`
- `__REPO_ROOT__/config/mira_light_profile.example.json`

## Vision pipeline references

- Schema: `__REPO_ROOT__/config/mira_light_vision_event.schema.json`
- Extractor: `__REPO_ROOT__/scripts/track_target_event_extractor.py`
- Runtime bridge: `__REPO_ROOT__/scripts/vision_runtime_bridge.py`
- LaunchAgent label for the always-on vision stack: `ai.mira-light.vision`
- Vision env helper file: `__HOME__/.openclaw/mira-light-vision.env`

Remember: vision should describe what is seen and suggest intent. It should not
directly emit raw servo angles as the first control layer.
