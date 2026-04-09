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

if ! "${PYTHON_BIN}" -c 'import sys; raise SystemExit(0 if sys.version_info >= (3, 10) else 1)'; then
  echo "Python 3.10+ is required for Mira Light release scripts." >&2
  "${PYTHON_BIN}" --version >&2 || true
  exit 1
fi

HOST="${MIRA_LIGHT_CONSOLE_HOST:-127.0.0.1}"
PORT="${MIRA_LIGHT_CONSOLE_PORT:-8765}"
BRIDGE_BASE_URL="${MIRA_LIGHT_CONSOLE_BRIDGE_URL:-${MIRA_LIGHT_BRIDGE_URL:-http://127.0.0.1:9783}}"
BRIDGE_TOKEN_ENV="${MIRA_LIGHT_CONSOLE_BRIDGE_TOKEN_ENV:-MIRA_LIGHT_BRIDGE_TOKEN}"
BRIDGE_TIMEOUT_SECONDS="${MIRA_LIGHT_CONSOLE_BRIDGE_TIMEOUT_SECONDS:-5}"

ARGS=(
  "${REPO_ROOT}/scripts/console_server.py"
  "--host" "${HOST}"
  "--port" "${PORT}"
  "--bridge-base-url" "${BRIDGE_BASE_URL}"
  "--bridge-token-env" "${BRIDGE_TOKEN_ENV}"
  "--bridge-timeout" "${BRIDGE_TIMEOUT_SECONDS}"
)

if [[ "${MIRA_LIGHT_DRY_RUN:-0}" == "1" ]]; then
  echo "[console-start] note: MIRA_LIGHT_DRY_RUN is a bridge/runtime setting." >&2
  echo "[console-start] note: start the bridge with --dry-run or use scripts/start_local_stack.sh --dry-run." >&2
fi

exec "${PYTHON_BIN}" "${ARGS[@]}"
