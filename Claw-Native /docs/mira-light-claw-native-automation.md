# Mira Light Claw-Native Automation

## Goal

This note explains the automation path that now exists in the repository.

Instead of manually copying every file from `Claw-Native ` into `~/.openclaw`,
the repository now provides a machine-apply script:

```bash
python3 scripts/apply_claw_native_local.py --write
```

## What the apply script does

It materializes the repository package into the local machine by writing:

- `~/.openclaw/openclaw.json`
- `~/.openclaw/mira-light-bridge.env`
- `~/.openclaw/mira-light-vision.env`
- `~/.openclaw/workspace/*`
- `~/.local/bin/mira-light-bridge`
- `~/.local/bin/mira-light-vision`
- `~/Library/LaunchAgents/ai.mira-light.bridge.plist`
- `~/Library/LaunchAgents/ai.mira-light.vision.plist`

It also runs the operational helpers unless explicitly skipped:

- `openclaw gateway install --force --json`
- `bash scripts/setup_local_mira_light_service_env.sh`
- `python3 scripts/sync_local_mira_light_service.py`
- launchd bootstrap or kickstart for bridge and vision
- `openclaw memory index`
- `python3 scripts/verify_local_openclaw_mira_light.py`

## Placeholder values

The script fills these placeholders from local machine state or explicit flags:

- `__HOME__`
- `__REPO_ROOT__`
- `__TIMEZONE__`
- `__GATEWAY_TOKEN__`
- `__BRIDGE_TOKEN__`
- `__LAMP_BASE_URL__`

Resolution order is conservative:

- explicit CLI flag first
- existing local config or env file next
- process environment next
- generated or default fallback last

## Safe defaults

- existing unrelated plugin entries are preserved
- existing `plugins.allow` and `plugins.load.paths` are merged, not wiped
- machine-private secrets stay on the machine
- template files in the repo stay redacted

## Useful modes

Dry-run:

```bash
python3 scripts/apply_claw_native_local.py
```

Full apply:

```bash
python3 scripts/apply_claw_native_local.py --write
```

Apply without restarting launchd services:

```bash
python3 scripts/apply_claw_native_local.py --write --skip-launchd
```

Apply without rebuilding memory:

```bash
python3 scripts/apply_claw_native_local.py --write --skip-memory-index
```
