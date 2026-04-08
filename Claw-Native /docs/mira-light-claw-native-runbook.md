# Mira Light Claw-Native Runbook

## Purpose

This runbook explains how to take the templates in `Claw-Native ` and apply
them to a real local OpenClaw machine.

## 1. Prepare the machine

Requirements:

- `openclaw` already installed
- local repository checkout available
- `python3` available
- a valid OpenClaw auth path for the chosen model

Optional but recommended:

- Docker, if you want non-main sandbox execution to actually run

## 2. Adapt the templates

Before copying files, replace the placeholders:

- `__HOME__`
- `__REPO_ROOT__`
- `__BRIDGE_TOKEN__`
- `__GATEWAY_TOKEN__`
- `__TIMEZONE__`
- `__LAMP_BASE_URL__`

Files that usually need adaptation first:

- `templates/openclaw.template.jsonc`
- `templates/mira-light-bridge.env.example`
- `templates/mira-light-vision.env.example`
- `templates/launchd/ai.mira-light.bridge.plist.example`
- `templates/launchd/ai.mira-light.vision.plist.example`
- `workspace/TOOLS.md`
- `workspace/MEMORY.md`

## 3. Materialize the local OpenClaw files

Copy the adapted versions into the local state tree:

```text
~/.openclaw/openclaw.json
~/.openclaw/mira-light-bridge.env
~/.openclaw/mira-light-vision.env
~/.openclaw/workspace/AGENTS.md
~/.openclaw/workspace/SOUL.md
~/.openclaw/workspace/IDENTITY.md
~/.openclaw/workspace/TOOLS.md
~/.openclaw/workspace/MEMORY.md
~/.openclaw/workspace/USER.md
~/.openclaw/workspace/HEARTBEAT.md
~/.openclaw/workspace/skills/mira-light-orchestrator/SKILL.md
```

Important:

- do not commit real tokens back into the repository
- do not treat the repo templates as already machine-valid without editing

If you want the repository to do this rendering for you, use:

```bash
python3 scripts/apply_claw_native_local.py --write
```

That is now the preferred path for a full local rollout.

## 4. Install the plugin side

Use the repository helper:

```bash
export MIRA_LIGHT_BRIDGE_TOKEN='your-token'
python3 scripts/install_local_openclaw_mira_light.py --doctor
```

This helper:

- links the plugin into `~/.openclaw/extensions/mira-light-bridge`
- patches `plugins.allow`
- patches `plugins.load.paths`
- patches `plugins.entries`

## 5. Prepare the local service copy

```bash
bash scripts/setup_local_mira_light_service_env.sh
python3 scripts/sync_local_mira_light_service.py
```

This creates:

- `~/.openclaw/mira-light-service/.venv`
- a launchd-friendly copy of the runtime files under `~/.openclaw/mira-light-service`

## 6. Install the wrapper launchers

Copy the adapted wrapper scripts to:

```text
~/.local/bin/mira-light-bridge
~/.local/bin/mira-light-vision
```

Make them executable:

```bash
chmod 755 ~/.local/bin/mira-light-bridge
chmod 755 ~/.local/bin/mira-light-vision
```

## 7. Install the launchd agents

Copy the adapted plist files to:

```text
~/Library/LaunchAgents/ai.mira-light.bridge.plist
~/Library/LaunchAgents/ai.mira-light.vision.plist
```

Then load them:

```bash
uid=$(id -u)
launchctl bootstrap gui/$uid ~/Library/LaunchAgents/ai.mira-light.bridge.plist
launchctl bootstrap gui/$uid ~/Library/LaunchAgents/ai.mira-light.vision.plist
```

If they were already loaded:

```bash
uid=$(id -u)
launchctl kickstart -k gui/$uid/ai.mira-light.bridge
launchctl kickstart -k gui/$uid/ai.mira-light.vision
```

## 8. Verify the stack

```bash
openclaw models status --json
openclaw memory status --json
openclaw gateway status --json
source ~/.openclaw/mira-light-bridge.env
python3 scripts/verify_local_openclaw_mira_light.py --bridge-token "$MIRA_LIGHT_BRIDGE_TOKEN"
curl http://127.0.0.1:9783/health
curl http://127.0.0.1:8000/health
```

## 9. Update flow after code changes

When runtime or bridge code changes in the repo:

```bash
python3 scripts/sync_local_mira_light_service.py
uid=$(id -u)
launchctl kickstart -k gui/$uid/ai.mira-light.bridge
launchctl kickstart -k gui/$uid/ai.mira-light.vision
```

## 10. What still requires human judgment

- choosing the real lamp IP
- handling VPN or hotspot route conflicts
- real servo calibration
- deciding when experimental scenes should be enabled
- deciding which embeddings provider to use for semantic memory
