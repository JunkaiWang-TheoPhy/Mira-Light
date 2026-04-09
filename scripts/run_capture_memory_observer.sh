#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

if [[ -n "${MIRA_LIGHT_VISION_PYTHON:-}" ]]; then
  PYTHON_BIN="${MIRA_LIGHT_VISION_PYTHON}"
elif [[ -x "${REPO_ROOT}/.venv/bin/python" ]]; then
  PYTHON_BIN="${REPO_ROOT}/.venv/bin/python"
else
  PYTHON_BIN="$(command -v python3)"
fi

if [[ ! -x "${PYTHON_BIN}" ]]; then
  echo "Missing Python runtime: ${PYTHON_BIN}" >&2
  echo "Run: bash scripts/setup_local_mira_light_service_env.sh" >&2
  exit 1
fi

exec "${PYTHON_BIN}" "${REPO_ROOT}/scripts/capture_memory_observer.py" "$@"
