#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
SERVICE_ROOT="${MIRA_LIGHT_MLX_ROOT:-$HOME/.openclaw/mira-light-mlx}"
VENV_DIR="${SERVICE_ROOT}/.venv"
REQUIRED_PYTHON_MINOR="${MIRA_LIGHT_MLX_PYTHON_MINOR:-3.11}"

require_supported_macos() {
  if [[ "${MIRA_LIGHT_SKIP_MLX_OS_CHECK:-0}" == "1" ]]; then
    return 0
  fi
  if ! command -v sw_vers >/dev/null 2>&1; then
    return 0
  fi

  local product_version=""
  product_version="$(sw_vers -productVersion 2>/dev/null || true)"
  if [[ -z "${product_version}" ]]; then
    return 0
  fi

  local major="${product_version%%.*}"
  if [[ "${major}" -lt 14 ]]; then
    echo "MLX currently requires macOS 14.0 or higher, but this machine is ${product_version}." >&2
    echo "You can still pre-download MLX model files, but the official MLX runtime will not load on this OS." >&2
    echo "Upgrade macOS or rerun with MIRA_LIGHT_SKIP_MLX_OS_CHECK=1 only if you are intentionally experimenting." >&2
    exit 2
  fi
}

choose_python_bin() {
  if [[ -n "${PYTHON_BIN:-}" ]]; then
    printf '%s\n' "${PYTHON_BIN}"
    return 0
  fi

  local candidates=(
    "python${REQUIRED_PYTHON_MINOR}"
    "python3.12"
    "python3.11"
    "python3.10"
    "python3"
  )

  local candidate=""
  for candidate in "${candidates[@]}"; do
    if command -v "${candidate}" >/dev/null 2>&1; then
      command -v "${candidate}"
      return 0
    fi
  done

  return 1
}

PYTHON_BIN="$(choose_python_bin || true)"

if [[ -z "${PYTHON_BIN}" ]]; then
  echo "A compatible Python interpreter was not found in PATH." >&2
  exit 1
fi

require_supported_macos

mkdir -p "${SERVICE_ROOT}"

if [[ -x "${VENV_DIR}/bin/python" ]]; then
  CURRENT_VENV_MINOR="$("${VENV_DIR}/bin/python" - <<'PY'
import sys
print(f"{sys.version_info.major}.{sys.version_info.minor}")
PY
)"
  if [[ "${CURRENT_VENV_MINOR}" != "${REQUIRED_PYTHON_MINOR}" ]]; then
    BACKUP_DIR="${VENV_DIR}.bak-py${CURRENT_VENV_MINOR//./}-$(date +%Y%m%d-%H%M%S)"
    mv "${VENV_DIR}" "${BACKUP_DIR}"
    echo "Moved incompatible MLX venv to ${BACKUP_DIR}"
  fi
fi

if [[ ! -d "${VENV_DIR}" ]]; then
  "${PYTHON_BIN}" -m venv "${VENV_DIR}"
fi

source "${VENV_DIR}/bin/activate"
python -m pip install --upgrade pip
python -m pip install mlx-lm

echo "MLX Qwen environment ready at ${VENV_DIR}"
echo "Python: $("${VENV_DIR}/bin/python" -V)"
echo "Next steps:"
echo "  ${VENV_DIR}/bin/python ${REPO_ROOT}/scripts/download_mlx_model.py --model qwen2.5-3b"
echo "  ${VENV_DIR}/bin/python ${REPO_ROOT}/scripts/download_mlx_model.py --verify --model qwen2.5-3b"
echo "  ${VENV_DIR}/bin/python ${REPO_ROOT}/scripts/smoke_test_mlx_model.py --model qwen2.5-3b"
