#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
LLAMA_CPP_ROOT="${MIRA_LIGHT_LLAMA_CPP_ROOT:-$HOME/.openclaw/mira-light-llama.cpp}"

print_next_steps() {
  local llama_cli_bin="$1"
  echo "llama.cpp is ready."
  echo "llama-cli: ${llama_cli_bin}"
  echo "Next steps:"
  echo "  python3 ${REPO_ROOT}/scripts/download_llama_cpp_model.py --model qwen2.5-3b"
  echo "  python3 ${REPO_ROOT}/scripts/download_llama_cpp_model.py --verify --model qwen2.5-3b"
  echo "  python3 ${REPO_ROOT}/scripts/smoke_test_llama_cpp.py --model qwen2.5-3b"
}

resolve_brew_llama_bin() {
  if ! command -v brew >/dev/null 2>&1; then
    return 1
  fi
  local brew_prefix=""
  brew_prefix="$(brew --prefix 2>/dev/null || true)"
  if [[ -n "${brew_prefix}" && -x "${brew_prefix}/bin/llama-cli" ]]; then
    printf '%s\n' "${brew_prefix}/bin/llama-cli"
    return 0
  fi
  return 1
}

ensure_homebrew_llama_cpp() {
  if ! command -v brew >/dev/null 2>&1; then
    return 1
  fi
  if command -v llama-cli >/dev/null 2>&1; then
    command -v llama-cli
    return 0
  fi
  if resolve_brew_llama_bin >/dev/null 2>&1; then
    resolve_brew_llama_bin
    return 0
  fi

  brew install llama.cpp
  if command -v llama-cli >/dev/null 2>&1; then
    command -v llama-cli
    return 0
  fi
  if resolve_brew_llama_bin >/dev/null 2>&1; then
    resolve_brew_llama_bin
    return 0
  fi
  return 1
}

fallback_build_from_source() {
  mkdir -p "${LLAMA_CPP_ROOT}"
  if [[ ! -d "${LLAMA_CPP_ROOT}/src/.git" ]]; then
    git clone https://github.com/ggml-org/llama.cpp.git "${LLAMA_CPP_ROOT}/src"
  else
    git -C "${LLAMA_CPP_ROOT}/src" pull --ff-only
  fi

  cmake -S "${LLAMA_CPP_ROOT}/src" -B "${LLAMA_CPP_ROOT}/build" -DGGML_METAL=ON -DLLAMA_BUILD_SERVER=ON
  cmake --build "${LLAMA_CPP_ROOT}/build" --parallel

  if [[ -x "${LLAMA_CPP_ROOT}/build/bin/llama-cli" ]]; then
    printf '%s\n' "${LLAMA_CPP_ROOT}/build/bin/llama-cli"
    return 0
  fi
  return 1
}

LLAMA_CLI_BIN=""
if command -v llama-cli >/dev/null 2>&1; then
  LLAMA_CLI_BIN="$(command -v llama-cli)"
elif LLAMA_CLI_BIN="$(ensure_homebrew_llama_cpp 2>/dev/null)"; then
  :
elif LLAMA_CLI_BIN="$(fallback_build_from_source 2>/dev/null)"; then
  :
else
  echo "Unable to prepare llama.cpp. Install Homebrew or ensure git/cmake are available for the source build fallback." >&2
  exit 1
fi

"${LLAMA_CLI_BIN}" --help >/dev/null
print_next_steps "${LLAMA_CLI_BIN}"
