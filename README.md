# Mira-Lume

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

- [docs/mira-context-proactivity-architecture.md](./docs/mira-context-proactivity-architecture.md)
- [docs/mira-light-embodied-memory-integration-2026-04-09.md](./docs/mira-light-embodied-memory-integration-2026-04-09.md)
- [docs/mira-light-to-mira-v3-layered-memory-integration-plan.md](./docs/mira-light-to-mira-v3-layered-memory-integration-plan.md)

Those two documents together explain:

- how Mira should evolve from context capture into proactive companionship
- how `Mira-Light` now participates as an embodied memory producer for cloud Mira

The layered-memory execution guide additionally explains:

- how to connect `Mira-Light` into `Mira_v3` memory-context, session-memory, and prompt-pack
- how to implement and run that integration step by step
