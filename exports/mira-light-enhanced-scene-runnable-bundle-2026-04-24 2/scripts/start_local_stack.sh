#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
LOG_ROOT="${MIRA_LIGHT_STACK_LOG_ROOT:-${REPO_ROOT}/.mira-light-runtime/local-stack}"

LAMP_URL="${MIRA_LIGHT_LAMP_BASE_URL:-${MIRA_LIGHT_BASE_URL:-http://172.20.10.3}}"
DRY_RUN="${MIRA_LIGHT_DRY_RUN:-0}"
BRIDGE_TOKEN="${MIRA_LIGHT_BRIDGE_TOKEN:-test-token}"
BRIDGE_HOST="${MIRA_LIGHT_BRIDGE_HOST:-127.0.0.1}"
BRIDGE_PORT="${MIRA_LIGHT_BRIDGE_PORT:-9783}"
CONSOLE_HOST="${MIRA_LIGHT_CONSOLE_HOST:-127.0.0.1}"
CONSOLE_PORT="${MIRA_LIGHT_CONSOLE_PORT:-8765}"
RECEIVER_HOST="${MIRA_LIGHT_RECEIVER_HOST:-0.0.0.0}"
RECEIVER_PORT="${MIRA_LIGHT_RECEIVER_PORT:-9784}"
WAIT_SECONDS="${MIRA_LIGHT_STACK_WAIT_SECONDS:-15}"

usage() {
  cat <<'EOF'
Usage:
  bash scripts/start_local_stack.sh [options]

Options:
  --lamp-url URL         Override the lamp base URL that the bridge talks to
  --dry-run              Start the bridge runtime in dry-run mode
  --bridge-token TOKEN   Export the bridge bearer token before launch
  --wait-seconds N       Maximum seconds to wait for bridge/receiver health
  --help                 Show this message
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --lamp-url)
      LAMP_URL="${2:?missing value for --lamp-url}"
      shift 2
      ;;
    --dry-run)
      DRY_RUN="1"
      shift
      ;;
    --bridge-token)
      BRIDGE_TOKEN="${2:?missing value for --bridge-token}"
      shift 2
      ;;
    --wait-seconds)
      WAIT_SECONDS="${2:?missing value for --wait-seconds}"
      shift 2
      ;;
    --help|-h)
      usage
      exit 0
      ;;
    *)
      echo "Unknown option: $1" >&2
      usage >&2
      exit 1
      ;;
  esac
done

mkdir -p "${LOG_ROOT}"
BRIDGE_LOG="${LOG_ROOT}/bridge.log"
RECEIVER_LOG="${LOG_ROOT}/receiver.log"

export MIRA_LIGHT_BRIDGE_TOKEN="${BRIDGE_TOKEN}"
export MIRA_LIGHT_BRIDGE_HOST="${BRIDGE_HOST}"
export MIRA_LIGHT_BRIDGE_PORT="${BRIDGE_PORT}"
export MIRA_LIGHT_LAMP_BASE_URL="${LAMP_URL}"
export MIRA_LIGHT_DRY_RUN="${DRY_RUN}"
export MIRA_LIGHT_CONSOLE_HOST="${CONSOLE_HOST}"
export MIRA_LIGHT_CONSOLE_PORT="${CONSOLE_PORT}"
export MIRA_LIGHT_CONSOLE_BRIDGE_URL="http://127.0.0.1:${BRIDGE_PORT}"
export MIRA_LIGHT_RECEIVER_HOST="${RECEIVER_HOST}"
export MIRA_LIGHT_RECEIVER_PORT="${RECEIVER_PORT}"
export MIRA_LIGHT_BRIDGE_URL="http://127.0.0.1:${BRIDGE_PORT}"

BRIDGE_HEALTH_URL="http://127.0.0.1:${BRIDGE_PORT}/health"
RECEIVER_HEALTH_URL="http://127.0.0.1:${RECEIVER_PORT}/health"
CONSOLE_URL="http://127.0.0.1:${CONSOLE_PORT}/"

BG_PIDS=()

cleanup() {
  local exit_code=$?
  trap - EXIT INT TERM
  for pid in "${BG_PIDS[@]:-}"; do
    if kill -0 "${pid}" >/dev/null 2>&1; then
      kill "${pid}" >/dev/null 2>&1 || true
    fi
  done
  for pid in "${BG_PIDS[@]:-}"; do
    wait "${pid}" >/dev/null 2>&1 || true
  done
  exit "${exit_code}"
}

trap cleanup EXIT INT TERM

wait_for_http() {
  local url="$1"
  local label="$2"
  local deadline=$((SECONDS + WAIT_SECONDS))

  until curl -fsS "${url}" >/dev/null 2>&1; do
    if (( SECONDS >= deadline )); then
      echo "[local-stack] ${label} did not become healthy in ${WAIT_SECONDS}s: ${url}" >&2
      return 1
    fi
    sleep 0.5
  done
  echo "[local-stack] ${label} healthy: ${url}"
}

echo "[local-stack] log root: ${LOG_ROOT}"
echo "[local-stack] lamp url: ${LAMP_URL}"
echo "[local-stack] bridge token present: $([[ -n "${BRIDGE_TOKEN}" ]] && echo true || echo false)"
echo "[local-stack] dry run: ${DRY_RUN}"

echo "[local-stack] starting bridge"
bash "${REPO_ROOT}/tools/mira_light_bridge/start_bridge.sh" >"${BRIDGE_LOG}" 2>&1 &
BG_PIDS+=("$!")
wait_for_http "${BRIDGE_HEALTH_URL}" "bridge"

echo "[local-stack] starting receiver"
bash "${REPO_ROOT}/scripts/start_simple_lamp_receiver.sh" >"${RECEIVER_LOG}" 2>&1 &
BG_PIDS+=("$!")
wait_for_http "${RECEIVER_HEALTH_URL}" "receiver"

echo "[local-stack] bridge log: ${BRIDGE_LOG}"
echo "[local-stack] receiver log: ${RECEIVER_LOG}"
echo "[local-stack] console url: ${CONSOLE_URL}"
echo "[local-stack] press Ctrl-C to stop bridge + receiver + console"

bash "${REPO_ROOT}/scripts/start_director_console.sh"
