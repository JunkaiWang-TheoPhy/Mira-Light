#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
VENV_DIR="${REPO_ROOT}/.venv"

if [[ ! -x "${VENV_DIR}/bin/python" ]]; then
  echo "Missing ${VENV_DIR}. Run 'bash scripts/setup_cam_receiver_env.sh' first." >&2
  exit 1
fi

source "${VENV_DIR}/bin/activate"

if [[ $# -eq 1 && "$1" =~ ^[0-9]+$ ]]; then
  exec python "${REPO_ROOT}/docs/cam_receiver_new.py" --port "$1"
fi

exec python "${REPO_ROOT}/docs/cam_receiver_new.py" "$@"
