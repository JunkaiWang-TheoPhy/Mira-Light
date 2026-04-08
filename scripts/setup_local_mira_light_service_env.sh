#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
SERVICE_ROOT="${MIRA_LIGHT_SERVICE_ROOT:-$HOME/.openclaw/mira-light-service}"
VENV_DIR="${SERVICE_ROOT}/.venv"
PYTHON_BIN="${PYTHON_BIN:-$(command -v python3)}"

if [[ -z "${PYTHON_BIN}" ]]; then
  echo "python3 is required but was not found in PATH." >&2
  exit 1
fi

mkdir -p "${SERVICE_ROOT}"

if [[ ! -d "${VENV_DIR}" ]]; then
  "${PYTHON_BIN}" -m venv "${VENV_DIR}"
fi

source "${VENV_DIR}/bin/activate"
python -m pip install --upgrade pip
python -m pip install -r "${REPO_ROOT}/requirements.txt"

echo "Local Mira Light service vision env ready at ${VENV_DIR}"
