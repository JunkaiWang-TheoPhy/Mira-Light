#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
SERVICE_ROOT="${MIRA_LIGHT_MLX_ROOT:-$HOME/.openclaw/mira-light-mlx}"
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
python -m pip install mlx-lm

echo "MLX Qwen environment ready at ${VENV_DIR}"
echo "Next steps:"
echo "  ${VENV_DIR}/bin/python ${REPO_ROOT}/scripts/download_mlx_model.py --model qwen2.5-3b"
echo "  ${VENV_DIR}/bin/python ${REPO_ROOT}/scripts/download_mlx_model.py --verify --model qwen2.5-3b"
echo "  ${VENV_DIR}/bin/python ${REPO_ROOT}/scripts/smoke_test_mlx_model.py --model qwen2.5-3b"
