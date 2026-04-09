# Mira-Lume

## Claw-Native

The repository now includes a packaged `Claw-Native ` folder for the local
Mira Light + OpenClaw rollout. It contains:

- workspace identity templates for Mira
- redacted local config templates
- launchd and wrapper templates
- overview and runbook documentation

Start here:

- `Claw-Native /README.md`
- `Claw-Native /docs/mira-light-claw-native-overview.md`
- `Claw-Native /docs/mira-light-claw-native-runbook.md`
- `Claw-Native /docs/mira-light-claw-native-automation.md`
- `docs/mira-light-offline-validation-stack.md`

One-click offline rehearsal:

```bash
bash scripts/run_mira_light_offline_rehearsal.sh --mode quick
```

## Camera Receiver

This repository includes a formalized HTTP camera receiver at
[docs/cam_receiver_new.py](/Users/Zhuanz/Documents/Github/Mira-Light/docs/cam_receiver_new.py).
It accepts JPEG frames over `POST`, displays the latest frame locally,
and can optionally save frames to disk.

### Local setup

```bash
cd /Users/Zhuanz/Documents/Github/Mira-Light
bash scripts/setup_cam_receiver_env.sh
```

This creates a repository-local virtual environment at `.venv/` and
installs the dependencies from `requirements.txt`.

### Run the receiver

```bash
cd /Users/Zhuanz/Documents/Github/Mira-Light
bash scripts/run_cam_receiver.sh
```

To use a different port with the old one-argument style:

```bash
bash scripts/run_cam_receiver.sh 9000
```

To use the new formalized arguments:

```bash
bash scripts/run_cam_receiver.sh --host 0.0.0.0 --port 8000 --save-dir ./captures
```

Default listener:

- Host: `0.0.0.0`
- Port: `8000`

Additional behavior:

- `GET /health` returns simple receiver status
- `--save-dir` writes each received JPEG to the selected directory
- `--log-level` controls runtime log verbosity

## Architecture Docs

The most relevant design notes in this repository right now are:

- [docs/feature/README.md](./docs/feature/README.md)
- [docs/mira-context-proactivity-architecture.md](./docs/mira-context-proactivity-architecture.md)
- [docs/mira-light-embodied-memory-integration-2026-04-09.md](./docs/mira-light-embodied-memory-integration-2026-04-09.md)
- [docs/mira-light-to-mira-v3-layered-memory-integration-plan.md](./docs/mira-light-to-mira-v3-layered-memory-integration-plan.md)

Those two documents together explain:

- how Mira should evolve from context capture into proactive companionship
- how `Mira-Light` now participates as an embodied memory producer for cloud Mira

The feature progress index additionally separates current status by topic:

- memory and knowledge-graph-ready structure
- local vector memory and semantic retrieval
- Claw-Native local rollout
- offline rehearsal and mock validation
- vision replay and observability

The layered-memory execution guide additionally explains:

- how to connect `Mira-Light` into `Mira_v3` memory-context, session-memory, and prompt-pack
- how to implement and run that integration step by step
