# Contributing

## Scope

`Mira_Light_Released_Version/` is intended to be the release-oriented, self-contained tree for Mira Light.

If you modify this directory, prefer:

- minimal diffs
- release-safe docs
- relative-path friendly references
- keeping `scripts/`, `tools/`, `web/`, and `docs/` in sync

## Required Sync Rules

When changing a scene:

1. update [`scripts/scenes.py`](./scripts/scenes.py)
2. update the relevant release docs if behavior or scope changed
3. update the user-facing web or handoff docs if the scene contract changed

When changing release install or startup behavior:

1. update [`README.md`](./README.md)
2. update [`docs/getting-started.md`](./docs/getting-started.md)
3. update [`deploy/repo-manifest.json`](./deploy/repo-manifest.json) when commands change

## Verification

Before handing off changes, run:

```bash
bash scripts/doctor_release.sh
```

## Independence Goal

This directory should stay as close as possible to a future standalone repo.

That means:

- avoid depending on files outside this folder
- prefer relative links inside docs
- keep copied reference docs clearly marked when they still contain legacy links
- avoid reintroducing release-side mirror assets that are not runtime truth
