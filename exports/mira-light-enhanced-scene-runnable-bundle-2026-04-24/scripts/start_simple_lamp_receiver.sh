#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
VENV_DIR="${REPO_ROOT}/.venv"

PYTHON_BIN="${MIRA_LIGHT_RECEIVER_PYTHON:-}"
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

HOST="${MIRA_LIGHT_RECEIVER_HOST:-0.0.0.0}"
PORT="${MIRA_LIGHT_RECEIVER_PORT:-9784}"
SAVE_ROOT="${MIRA_LIGHT_RECEIVER_SAVE_ROOT:-${HOME}/Documents/Mira-Light-Runtime/simple-receiver}"

if [[ -f "${SCRIPT_DIR}/simple_lamp_receiver.py" ]]; then
  RECEIVER_SCRIPT="${SCRIPT_DIR}/simple_lamp_receiver.py"
elif [[ -f "${SCRIPT_DIR}/../scripts/simple_lamp_receiver.py" ]]; then
  RECEIVER_SCRIPT="${SCRIPT_DIR}/../scripts/simple_lamp_receiver.py"
else
  echo "Could not locate simple_lamp_receiver.py from ${SCRIPT_DIR}" >&2
  exit 1
fi

exec "${PYTHON_BIN}" \
  "${RECEIVER_SCRIPT}" \
  --host "${HOST}" \
  --port "${PORT}" \
  --save-root "${SAVE_ROOT}"
