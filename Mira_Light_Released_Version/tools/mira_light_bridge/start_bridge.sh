#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
VENV_DIR="${REPO_ROOT}/.venv"
CONFIG_PATH="${MIRA_LIGHT_BRIDGE_CONFIG:-$SCRIPT_DIR/bridge_config.json}"
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

ARGS=(
  "$SCRIPT_DIR/bridge_server.py"
  "--config" "$CONFIG_PATH"
)

if [[ -n "${MIRA_LIGHT_BRIDGE_HOST:-}" ]]; then
  ARGS+=("--host" "${MIRA_LIGHT_BRIDGE_HOST}")
fi

if [[ -n "${MIRA_LIGHT_BRIDGE_PORT:-}" ]]; then
  ARGS+=("--port" "${MIRA_LIGHT_BRIDGE_PORT}")
fi

if [[ -n "${MIRA_LIGHT_LAMP_BASE_URL:-${MIRA_LIGHT_BASE_URL:-}}" ]]; then
  ARGS+=("--base-url" "${MIRA_LIGHT_LAMP_BASE_URL:-${MIRA_LIGHT_BASE_URL:-}}")
fi

if [[ "${MIRA_LIGHT_DRY_RUN:-0}" == "1" ]]; then
  ARGS+=("--dry-run")
fi

exec "${PYTHON_BIN}" "${ARGS[@]}" "$@"
