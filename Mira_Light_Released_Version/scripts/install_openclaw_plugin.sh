#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
PYTHON_BIN="${PYTHON_BIN:-$(command -v python3)}"

if [[ -z "${PYTHON_BIN}" ]]; then
  echo "python3 is required but was not found in PATH." >&2
  exit 1
fi

exec "${PYTHON_BIN}" "${REPO_ROOT}/scripts/install_local_openclaw_mira_light.py" --doctor "$@"
