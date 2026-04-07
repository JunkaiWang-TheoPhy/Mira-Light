#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

PYTHON_BIN="${MIRA_LIGHT_RECEIVER_PYTHON:-$(command -v python3)}"
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
