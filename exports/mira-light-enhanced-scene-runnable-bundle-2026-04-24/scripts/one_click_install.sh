#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
VENV_DIR="${REPO_ROOT}/.venv"
PYTHON_BIN="${PYTHON_BIN:-$(command -v python3)}"

if [[ -z "${PYTHON_BIN}" ]]; then
  echo "python3 is required but was not found in PATH." >&2
  exit 1
fi

if ! "${PYTHON_BIN}" -c 'import sys; raise SystemExit(0 if sys.version_info >= (3, 10) else 1)'; then
  echo "Python 3.10+ is required for Mira Light release scripts." >&2
  "${PYTHON_BIN}" --version >&2 || true
  exit 1
fi

echo "[mira-light] repo root: ${REPO_ROOT}"

if [[ ! -d "${VENV_DIR}" ]]; then
  echo "[mira-light] creating venv at ${VENV_DIR}"
  "${PYTHON_BIN}" -m venv "${VENV_DIR}"
fi

source "${VENV_DIR}/bin/activate"
python -m pip install --upgrade pip
if [[ -f "${REPO_ROOT}/requirements.txt" ]]; then
  echo "[mira-light] installing python requirements"
  python -m pip install -r "${REPO_ROOT}/requirements.txt"
fi

if [[ "${MIRA_LIGHT_SKIP_OPENCLAW_INSTALL:-0}" == "1" ]]; then
  echo "[mira-light] skipping OpenClaw plugin installation because MIRA_LIGHT_SKIP_OPENCLAW_INSTALL=1"
elif command -v openclaw >/dev/null 2>&1 && [[ -f "${HOME}/.openclaw/openclaw.json" ]]; then
  echo "[mira-light] detected local OpenClaw; installing mira-light plugin"
  python "${REPO_ROOT}/scripts/install_local_openclaw_mira_light.py" --doctor || true
else
  echo "[mira-light] OpenClaw not detected locally; plugin install skipped"
fi

echo
echo "[mira-light] next steps:"
echo "  - start director console: bash scripts/start_director_console.sh"
echo "  - start bridge:          bash tools/mira_light_bridge/start_bridge.sh"
echo "  - doctor:                bash scripts/doctor_release.sh"
