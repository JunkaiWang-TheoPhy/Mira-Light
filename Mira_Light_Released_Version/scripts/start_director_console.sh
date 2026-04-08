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

HOST="${MIRA_LIGHT_CONSOLE_HOST:-127.0.0.1}"
PORT="${MIRA_LIGHT_CONSOLE_PORT:-8765}"
BASE_URL="${MIRA_LIGHT_BASE_URL:-http://172.20.10.3}"
DRY_RUN="${MIRA_LIGHT_DRY_RUN:-0}"

ARGS=(
  "${REPO_ROOT}/scripts/console_server.py"
  "--host" "${HOST}"
  "--port" "${PORT}"
  "--base-url" "${BASE_URL}"
)

if [[ "${DRY_RUN}" == "1" ]]; then
  ARGS+=("--dry-run")
fi

exec "${PYTHON_BIN}" "${ARGS[@]}"
