#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON_BIN="${ROOT}/.venv/bin/python"

if [[ ! -x "${PYTHON_BIN}" ]]; then
  echo "Missing ${PYTHON_BIN}. Create the repo venv first." >&2
  exit 1
fi

exec "${PYTHON_BIN}" "${ROOT}/scripts/openclaw_voice_to_claw.py" "$@"
