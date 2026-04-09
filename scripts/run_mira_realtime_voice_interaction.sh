#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON_BIN="${ROOT}/.venv/bin/python"
LOCAL_ENV_FILE="${HOME}/.openclaw/mira-light-realtime.env"

if [[ ! -x "${PYTHON_BIN}" ]]; then
  echo "Missing ${PYTHON_BIN}. Create the repo venv first." >&2
  exit 1
fi

if [[ -f "${LOCAL_ENV_FILE}" ]]; then
  # shellcheck disable=SC1090
  source "${LOCAL_ENV_FILE}"
fi

if [[ "${MIRA_LIGHT_LINGZHU_AUTO_TUNNEL:-0}" == "1" ]]; then
  /bin/bash "${ROOT}/scripts/ensure_mira_lingzhu_tunnel.sh"
fi

exec "${PYTHON_BIN}" "${ROOT}/scripts/mira_realtime_voice_interaction.py" "$@"
