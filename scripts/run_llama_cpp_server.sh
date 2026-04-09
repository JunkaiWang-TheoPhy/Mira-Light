#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
MODEL_NAME="${MIRA_LIGHT_LLAMA_MODEL:-qwen2.5-3b}"
PORT="${MIRA_LIGHT_LLAMA_PORT:-8012}"
HOST="${MIRA_LIGHT_LLAMA_HOST:-127.0.0.1}"
THREADS="${MIRA_LIGHT_LLAMA_THREADS:-8}"
GPU_LAYERS="${MIRA_LIGHT_LLAMA_GPU_LAYERS:-0}"

find_llama_server() {
  if command -v llama-server >/dev/null 2>&1; then
    command -v llama-server
    return 0
  fi
  if command -v brew >/dev/null 2>&1; then
    local brew_prefix=""
    brew_prefix="$(brew --prefix 2>/dev/null || true)"
    if [[ -n "${brew_prefix}" && -x "${brew_prefix}/bin/llama-server" ]]; then
      printf '%s\n' "${brew_prefix}/bin/llama-server"
      return 0
    fi
  fi
  local fallback="${HOME}/.openclaw/mira-light-llama.cpp/build/bin/llama-server"
  if [[ -x "${fallback}" ]]; then
    printf '%s\n' "${fallback}"
    return 0
  fi
  return 1
}

LLAMA_SERVER_BIN="$(find_llama_server || true)"
if [[ -z "${LLAMA_SERVER_BIN}" ]]; then
  echo "llama-server was not found. Run bash scripts/setup_llama_cpp_env.sh first." >&2
  exit 1
fi

MODEL_DIR="${MIRA_LIGHT_LLAMA_MODEL_DIR:-$HOME/Library/Caches/Mira-Light/llama-cpp-models/Qwen2.5-3B-Instruct-GGUF}"
MODEL_FILE="${MIRA_LIGHT_LLAMA_MODEL_FILE:-qwen2.5-3b-instruct-q4_k_m.gguf}"
if [[ "${MODEL_NAME}" == "qwen2.5-7b" && -z "${MIRA_LIGHT_LLAMA_MODEL_FILE:-}" ]]; then
  MODEL_DIR="${MIRA_LIGHT_LLAMA_MODEL_DIR:-$HOME/Library/Caches/Mira-Light/llama-cpp-models/Qwen2.5-7B-Instruct-GGUF}"
  MODEL_FILE="qwen2.5-7b-instruct-q4_k_m-00001-of-00002.gguf"
fi

exec "${LLAMA_SERVER_BIN}" \
  -m "${MODEL_DIR}/${MODEL_FILE}" \
  --host "${HOST}" \
  --port "${PORT}" \
  -t "${THREADS}" \
  -ngl "${GPU_LAYERS}"
