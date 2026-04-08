#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
VENV_DIR="${REPO_ROOT}/.venv"
PYTHON_BIN="${MIRA_LIGHT_PYTHON:-}"

if [[ -z "${PYTHON_BIN}" ]]; then
  if [[ -x "${VENV_DIR}/bin/python" ]]; then
    PYTHON_BIN="${VENV_DIR}/bin/python"
  else
    PYTHON_BIN="$(command -v python3)"
  fi
fi

if [[ -z "${PYTHON_BIN}" ]]; then
  echo "python3 is required but was not found in PATH." >&2
  exit 1
fi

echo "[doctor] python compile checks"
"${PYTHON_BIN}" -m py_compile \
  "${REPO_ROOT}/scripts/scenes.py" \
  "${REPO_ROOT}/scripts/mira_light_runtime.py" \
  "${REPO_ROOT}/scripts/console_server.py" \
  "${REPO_ROOT}/tools/mira_light_bridge/bridge_server.py"

echo "[doctor] unit tests"
"${PYTHON_BIN}" -m unittest tests.test_minimal_smoke tests.test_embodied_memory

if command -v openclaw >/dev/null 2>&1 && [[ -f "${HOME}/.openclaw/openclaw.json" ]]; then
  echo "[doctor] OpenClaw verification"
  "${PYTHON_BIN}" "${REPO_ROOT}/scripts/verify_local_openclaw_mira_light.py" || true
else
  echo "[doctor] OpenClaw not detected locally; skipping plugin verification"
fi

echo "[doctor] done"
