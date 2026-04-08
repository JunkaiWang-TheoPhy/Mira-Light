#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="${MIRA_LIGHT_SERVICE_ROOT:-$HOME/.openclaw/mira-light-service}"
WORKSPACE_RUNTIME_DIR="${MIRA_LIGHT_WORKSPACE_RUNTIME_DIR:-$HOME/.openclaw/workspace/runtime}"
VISION_PORT="${MIRA_LIGHT_VISION_PORT:-8000}"
BASE_URL="${MIRA_LIGHT_BASE_URL:-http://172.20.10.3}"
PYTHON_BIN="${MIRA_LIGHT_VISION_PYTHON:-$ROOT_DIR/.venv/bin/python}"

CAPTURES_DIR="$WORKSPACE_RUNTIME_DIR/captures"
LATEST_EVENT_OUT="$WORKSPACE_RUNTIME_DIR/vision.latest.json"
EVENTS_JSONL="$WORKSPACE_RUNTIME_DIR/vision.events.jsonl"
BRIDGE_STATE_OUT="$WORKSPACE_RUNTIME_DIR/vision.bridge.state.json"

mkdir -p "$CAPTURES_DIR"
mkdir -p "$(dirname "$LATEST_EVENT_OUT")"

if [[ ! -x "$PYTHON_BIN" ]]; then
  echo "Missing Python runtime: $PYTHON_BIN" >&2
  echo "Run: bash scripts/setup_local_mira_light_service_env.sh" >&2
  exit 1
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

"$PYTHON_BIN" "$ROOT_DIR/scripts/cam_receiver_service.py" \
  --host 0.0.0.0 \
  --port "$VISION_PORT" \
  --save-dir "$CAPTURES_DIR" \
  --log-level INFO &
RECEIVER_PID=$!

"$PYTHON_BIN" "$ROOT_DIR/scripts/track_target_event_extractor.py" \
  --captures-dir "$CAPTURES_DIR" \
  --latest-event-out "$LATEST_EVENT_OUT" \
  --events-jsonl "$EVENTS_JSONL" \
  --poll-interval 0.5 \
  --log-level INFO &
EXTRACTOR_PID=$!

"$PYTHON_BIN" "$ROOT_DIR/scripts/vision_runtime_bridge.py" \
  --event-file "$LATEST_EVENT_OUT" \
  --bridge-state-out "$BRIDGE_STATE_OUT" \
  --poll-interval 0.5 \
  --base-url "$BASE_URL" \
  --allow-experimental &
BRIDGE_PID=$!

wait "$RECEIVER_PID" "$EXTRACTOR_PID" "$BRIDGE_PID"
