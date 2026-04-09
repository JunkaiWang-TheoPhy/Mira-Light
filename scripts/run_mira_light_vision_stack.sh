#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
DEFAULT_SERVICE_ROOT="$HOME/.openclaw/mira-light-service"
DEFAULT_WORKSPACE_RUNTIME_DIR="$HOME/.openclaw/workspace/runtime"

ROOT_DIR="${MIRA_LIGHT_SERVICE_ROOT:-$DEFAULT_SERVICE_ROOT}"
if [[ ! -d "${ROOT_DIR}/scripts" && -d "${REPO_ROOT}/scripts" ]]; then
  ROOT_DIR="${REPO_ROOT}"
fi

if [[ -n "${MIRA_LIGHT_WORKSPACE_RUNTIME_DIR:-}" ]]; then
  WORKSPACE_RUNTIME_DIR="${MIRA_LIGHT_WORKSPACE_RUNTIME_DIR}"
elif [[ "${ROOT_DIR}" == "${REPO_ROOT}" ]]; then
  WORKSPACE_RUNTIME_DIR="${REPO_ROOT}/runtime/live-vision"
else
  WORKSPACE_RUNTIME_DIR="${DEFAULT_WORKSPACE_RUNTIME_DIR}"
fi

VISION_HOST="${MIRA_LIGHT_VISION_HOST:-0.0.0.0}"
VISION_PORT="${MIRA_LIGHT_VISION_PORT:-8000}"
BASE_URL="${MIRA_LIGHT_BASE_URL:-http://172.20.10.3}"
POLL_INTERVAL="${MIRA_LIGHT_VISION_POLL_INTERVAL:-0.5}"
TRACKING_UPDATE_MS="${MIRA_LIGHT_TRACKING_UPDATE_MS:-220}"
LOG_LEVEL="${MIRA_LIGHT_VISION_LOG_LEVEL:-INFO}"
FACE_NEAR_AREA_RATIO="${MIRA_LIGHT_FACE_NEAR_AREA_RATIO:-0.10}"
FACE_MID_AREA_RATIO="${MIRA_LIGHT_FACE_MID_AREA_RATIO:-0.03}"
MOTION_NEAR_AREA_RATIO="${MIRA_LIGHT_MOTION_NEAR_AREA_RATIO:-0.18}"
MOTION_MID_AREA_RATIO="${MIRA_LIGHT_MOTION_MID_AREA_RATIO:-0.06}"
MIN_MOTION_AREA_RATIO="${MIRA_LIGHT_MIN_MOTION_AREA_RATIO:-0.015}"
WARMUP_FRAMES="${MIRA_LIGHT_WARMUP_FRAMES:-5}"

if [[ -n "${MIRA_LIGHT_VISION_PYTHON:-}" ]]; then
  PYTHON_BIN="${MIRA_LIGHT_VISION_PYTHON}"
elif [[ -x "${ROOT_DIR}/.venv/bin/python" ]]; then
  PYTHON_BIN="${ROOT_DIR}/.venv/bin/python"
elif [[ -x "${REPO_ROOT}/.venv/bin/python" ]]; then
  PYTHON_BIN="${REPO_ROOT}/.venv/bin/python"
else
  PYTHON_BIN="$(command -v python3)"
fi

CAPTURES_DIR="${MIRA_LIGHT_CAPTURES_DIR:-$WORKSPACE_RUNTIME_DIR/captures}"
LATEST_EVENT_OUT="${MIRA_LIGHT_LATEST_EVENT_OUT:-$WORKSPACE_RUNTIME_DIR/vision.latest.json}"
EVENTS_JSONL="${MIRA_LIGHT_EVENTS_JSONL:-$WORKSPACE_RUNTIME_DIR/vision.events.jsonl}"
BRIDGE_STATE_OUT="${MIRA_LIGHT_BRIDGE_STATE_OUT:-$WORKSPACE_RUNTIME_DIR/vision.bridge.state.json}"

mkdir -p "$CAPTURES_DIR"
mkdir -p "$(dirname "$LATEST_EVENT_OUT")"

if [[ ! -x "$PYTHON_BIN" ]]; then
  echo "Missing Python runtime: $PYTHON_BIN" >&2
  echo "Run: bash scripts/setup_local_mira_light_service_env.sh" >&2
  exit 1
fi

append_optional_flag() {
  local flag="$1"
  local value="${2:-}"
  if [[ -n "$value" ]]; then
    printf '%s %s ' "$flag" "$value"
  fi
}

append_bool_flag() {
  local flag="$1"
  local value="${2:-0}"
  case "${value,,}" in
    1|true|yes|on)
      printf '%s ' "$flag"
      ;;
  esac
}

RECEIVER_ARGS=(
  --host "$VISION_HOST"
  --port "$VISION_PORT"
  --save-dir "$CAPTURES_DIR"
  --log-level "$LOG_LEVEL"
)

EXTRACTOR_ARGS=(
  --captures-dir "$CAPTURES_DIR"
  --latest-event-out "$LATEST_EVENT_OUT"
  --events-jsonl "$EVENTS_JSONL"
  --poll-interval "$POLL_INTERVAL"
  --log-level "$LOG_LEVEL"
  --face-near-area-ratio "$FACE_NEAR_AREA_RATIO"
  --face-mid-area-ratio "$FACE_MID_AREA_RATIO"
  --motion-near-area-ratio "$MOTION_NEAR_AREA_RATIO"
  --motion-mid-area-ratio "$MOTION_MID_AREA_RATIO"
  --min-motion-area-ratio "$MIN_MOTION_AREA_RATIO"
  --warmup-frames "$WARMUP_FRAMES"
)

BRIDGE_ARGS=(
  --event-file "$LATEST_EVENT_OUT"
  --bridge-state-out "$BRIDGE_STATE_OUT"
  --poll-interval "$POLL_INTERVAL"
  --tracking-update-ms "$TRACKING_UPDATE_MS"
  --base-url "$BASE_URL"
)

if [[ "$(append_bool_flag --dry-run "${MIRA_LIGHT_VISION_DRY_RUN:-0}")" != "" ]]; then
  BRIDGE_ARGS+=(--dry-run)
fi

if [[ "$(append_bool_flag --allow-experimental "${MIRA_LIGHT_ALLOW_EXPERIMENTAL:-0}")" != "" ]]; then
  BRIDGE_ARGS+=(--allow-experimental)
fi

cleanup() {
  local exit_code=$?
  if [[ -n "${RECEIVER_PID:-}" ]]; then kill "$RECEIVER_PID" >/dev/null 2>&1 || true; fi
  if [[ -n "${EXTRACTOR_PID:-}" ]]; then kill "$EXTRACTOR_PID" >/dev/null 2>&1 || true; fi
  if [[ -n "${BRIDGE_PID:-}" ]]; then kill "$BRIDGE_PID" >/dev/null 2>&1 || true; fi
  wait || true
  exit "$exit_code"
}
trap cleanup EXIT INT TERM

"$PYTHON_BIN" "$ROOT_DIR/scripts/cam_receiver_service.py" "${RECEIVER_ARGS[@]}" &
RECEIVER_PID=$!

"$PYTHON_BIN" "$ROOT_DIR/scripts/track_target_event_extractor.py" "${EXTRACTOR_ARGS[@]}" &
EXTRACTOR_PID=$!

"$PYTHON_BIN" "$ROOT_DIR/scripts/vision_runtime_bridge.py" "${BRIDGE_ARGS[@]}" &
BRIDGE_PID=$!

wait "$RECEIVER_PID" "$EXTRACTOR_PID" "$BRIDGE_PID"
