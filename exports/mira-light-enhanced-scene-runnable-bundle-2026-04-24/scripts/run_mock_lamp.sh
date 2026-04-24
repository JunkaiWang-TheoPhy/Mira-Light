#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
VENV_PYTHON="${REPO_ROOT}/.venv/bin/python"

if [[ -x "${VENV_PYTHON}" ]]; then
  exec "${VENV_PYTHON}" "${REPO_ROOT}/scripts/mock_lamp_server.py" "$@"
fi

exec python3 "${REPO_ROOT}/scripts/mock_lamp_server.py" "$@"
