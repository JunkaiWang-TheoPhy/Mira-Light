# Claw-Native

`Claw-Native ` collects the repository-native form of the local Mira Light +
OpenClaw rollout that is already working on the machine.

This folder is meant to solve two problems at once:

1. Keep the working local setup visible inside the repository instead of only
   existing under `~/.openclaw/`.
2. Make it easy to explain, clone, and re-apply the same setup later.

Note: the directory name currently ends with a trailing space because that is
how it already exists in this repository. The contents here keep using it as-is
instead of renaming it mid-stream.

## What is inside

- `templates/`
  - redacted local config templates for `openclaw.json`, env helpers, wrapper
    launchers, and launchd plists
- `workspace/`
  - repo copy of the Mira workspace identity files that were written into the
    local OpenClaw workspace
- `docs/`
  - overview and runbook material for future onboarding, demos, and handoff

## What this package captures

- Mira identity, soul, operator style, and skill policy
- local OpenClaw plugin wiring for `mira-light-bridge`
- explicit default model pinning to `openai-codex/gpt-5.4`
- bridge and vision env layout
- launchd-based always-on gateway, bridge, and vision topology
- memory indexing strategy and current limitations

## What it does not commit

- real gateway tokens
- real bridge tokens
- user-specific secrets
- machine-private runtime state under `~/.openclaw/`

## Main entry points

- Overview: `docs/mira-light-claw-native-overview.md`
- Runbook: `docs/mira-light-claw-native-runbook.md`
- Automation: `docs/mira-light-claw-native-automation.md`
- Verified rollout note: `docs/mira-light-claw-native-rollout-state-2026-04-09.md`
- Offline validation stack: `../docs/mira-light-offline-validation-stack.md`
- OpenClaw config template: `templates/openclaw.template.jsonc`
- Workspace template root: `workspace/`

## Related repository scripts

- `scripts/install_local_openclaw_mira_light.py`
- `scripts/apply_claw_native_local.py`
- `scripts/verify_local_openclaw_mira_light.py`
- `scripts/sync_local_mira_light_service.py`
- `scripts/setup_local_mira_light_service_env.sh`
- `scripts/run_mira_light_vision_stack.sh`
- `scripts/diagnose_mira_light_network.sh`

Those scripts are the operational layer. `Claw-Native ` is the packaged
definition and documentation layer.
