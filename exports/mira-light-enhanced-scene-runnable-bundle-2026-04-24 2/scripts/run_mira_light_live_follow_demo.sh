#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
PYTHON_BIN="${REPO_ROOT}/.venv/bin/python"

if [[ ! -x "${PYTHON_BIN}" ]]; then
  echo "Missing ${PYTHON_BIN}. Run 'bash scripts/setup_cam_receiver_env.sh' first." >&2
  exit 1
fi

RECEIVER_HOST="0.0.0.0"
RECEIVER_PORT="8000"
RUNTIME_DIR="${REPO_ROOT}/runtime/live-follow-demo"
CAPTURES_DIR=""
BASE_URL="${MIRA_LIGHT_BASE_URL:-http://172.20.10.3}"
BASE_URL_EXPLICIT="0"
MOCK_DEVICE="0"
MOCK_PORT="9791"
DRY_RUN="0"
ATTACH_EXISTING_RECEIVER="0"
REPLAY_DEMO="0"
REPLAY_LOOP="0"
REPLAY_SOURCE="${REPO_ROOT}/runtime/vision-demo-captures"
REPLAY_FPS="3.0"
POLL_INTERVAL="0.2"
TRACKING_UPDATE_MS="180"
TOUCH_PERSISTENCE_FRAMES="3"
TOUCH_COOLDOWN_MS="9000"
TOUCH_MIN_CONFIDENCE="0.72"
TOUCH_MIN_SIZE_NORM="0.085"
TOUCH_MAX_CENTER_OFFSET="0.32"
TOUCH_HAND_ARM_MIN_CONFIDENCE="0.68"
TOUCH_ALLOW_PERSON_FALLBACK="0"
HAND_AVOID_COOLDOWN_MS="7000"
HAND_AVOID_MIN_CONFIDENCE="0.78"
HAND_AVOID_MAX_CENTER_Y="0.74"
HAND_AVOID_EXTENDED_MAX_CENTER_Y="0.86"
HAND_AVOID_EXTENDED_MIN_CONFIDENCE="0.90"
HAND_AVOID_MIN_LATERAL_OFFSET="0.18"
LOG_LEVEL="INFO"
ALLOW_EXPERIMENTAL="1"
FACE_NEAR_AREA_RATIO="0.08"
FACE_MID_AREA_RATIO="0.025"
MOTION_NEAR_AREA_RATIO="0.16"
MOTION_MID_AREA_RATIO="0.05"
MIN_MOTION_AREA_RATIO="0.012"
WARMUP_FRAMES="8"
HAND_CUE_MIN_AREA_RATIO="0.0015"
HAND_CUE_MAX_AREA_RATIO="0.06"
HAND_CUE_MIN_CENTER_Y="0.34"
HAND_CUE_MIN_MOTION_RATIO="0.12"
HAND_CUE_MIN_CONFIDENCE="0.55"
WARMUP_FRAMES_EXPLICIT="0"

usage() {
  cat <<'EOF'
Usage: bash scripts/run_mira_light_live_follow_demo.sh [options]

Options:
  --base-url URL                 Lamp base URL. Default: http://172.20.10.3
  --receiver-port PORT           Camera receiver port. Default: 8000
  --receiver-host HOST           Camera receiver host. Default: 0.0.0.0
  --runtime-dir DIR              Output directory for captures, events, and logs
  --captures-dir DIR             Override capture directory inside runtime dir
  --mock-device                  Start the local mock lamp on 127.0.0.1:9791
  --mock-port PORT               Mock lamp port. Default: 9791
  --dry-run                      Do not send hardware commands to a real lamp
  --attach-existing-receiver     Reuse the already-running camera receiver and preview
  --replay-demo                  Replay sample frames from runtime/vision-demo-captures
  --replay-source DIR            Override replay frame directory
  --replay-fps FPS               Replay rate. Default: 3.0
  --replay-loop                  Loop sample replay until interrupted
  --poll-interval SEC            Extractor/bridge polling interval. Default: 0.2
  --tracking-update-ms MS        Live tracking update interval. Default: 180
  --touch-persistence-frames N   Near-interaction frames before touch_affection. Default: 3
  --touch-cooldown-ms MS         Cooldown between auto hand-near triggers. Default: 9000
  --touch-min-confidence VALUE   Default: 0.72
  --touch-min-size-norm VALUE    Default: 0.085
  --touch-max-center-offset V    Default: 0.32
  --touch-hand-arm-min-confidence VALUE Default: 0.68
  --touch-allow-person-fallback  Re-enable older near-person touch heuristic
  --hand-avoid-cooldown-ms MS    Default: 7000
  --hand-avoid-min-confidence V  Default: 0.78
  --hand-avoid-max-center-y V    Default: 0.74
  --hand-avoid-extended-max-center-y V Default: 0.86
  --hand-avoid-extended-min-confidence V Default: 0.90
  --hand-avoid-min-lateral-offset V Default: 0.18
  --log-level LEVEL              INFO, DEBUG, WARNING, ERROR. Default: INFO
  --face-near-area-ratio VALUE   Default: 0.08
  --face-mid-area-ratio VALUE    Default: 0.025
  --motion-near-area-ratio VALUE Default: 0.16
  --motion-mid-area-ratio VALUE  Default: 0.05
  --min-motion-area-ratio VALUE  Default: 0.012
  --warmup-frames COUNT          Default: 8
  --hand-cue-min-area-ratio V    Default: 0.0015
  --hand-cue-max-area-ratio V    Default: 0.06
  --hand-cue-min-center-y V      Default: 0.34
  --hand-cue-min-motion-ratio V  Default: 0.12
  --hand-cue-min-confidence V    Default: 0.55
  --no-experimental              Disable prototype scenes in runtime
  --help                         Show this help
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --base-url)
      BASE_URL="$2"
      BASE_URL_EXPLICIT="1"
      shift 2
      ;;
    --receiver-port)
      RECEIVER_PORT="$2"
      shift 2
      ;;
    --receiver-host)
      RECEIVER_HOST="$2"
      shift 2
      ;;
    --runtime-dir)
      RUNTIME_DIR="$2"
      shift 2
      ;;
    --captures-dir)
      CAPTURES_DIR="$2"
      shift 2
      ;;
    --mock-device)
      MOCK_DEVICE="1"
      shift
      ;;
    --mock-port)
      MOCK_PORT="$2"
      shift 2
      ;;
    --dry-run)
      DRY_RUN="1"
      shift
      ;;
    --attach-existing-receiver)
      ATTACH_EXISTING_RECEIVER="1"
      shift
      ;;
    --replay-demo)
      REPLAY_DEMO="1"
      shift
      ;;
    --replay-source)
      REPLAY_SOURCE="$2"
      shift 2
      ;;
    --replay-fps)
      REPLAY_FPS="$2"
      shift 2
      ;;
    --replay-loop)
      REPLAY_LOOP="1"
      shift
      ;;
    --poll-interval)
      POLL_INTERVAL="$2"
      shift 2
      ;;
    --tracking-update-ms)
      TRACKING_UPDATE_MS="$2"
      shift 2
      ;;
    --touch-persistence-frames)
      TOUCH_PERSISTENCE_FRAMES="$2"
      shift 2
      ;;
    --touch-cooldown-ms)
      TOUCH_COOLDOWN_MS="$2"
      shift 2
      ;;
    --touch-min-confidence)
      TOUCH_MIN_CONFIDENCE="$2"
      shift 2
      ;;
    --touch-min-size-norm)
      TOUCH_MIN_SIZE_NORM="$2"
      shift 2
      ;;
    --touch-max-center-offset)
      TOUCH_MAX_CENTER_OFFSET="$2"
      shift 2
      ;;
    --touch-hand-arm-min-confidence)
      TOUCH_HAND_ARM_MIN_CONFIDENCE="$2"
      shift 2
      ;;
    --touch-allow-person-fallback)
      TOUCH_ALLOW_PERSON_FALLBACK="1"
      shift
      ;;
    --hand-avoid-cooldown-ms)
      HAND_AVOID_COOLDOWN_MS="$2"
      shift 2
      ;;
    --hand-avoid-min-confidence)
      HAND_AVOID_MIN_CONFIDENCE="$2"
      shift 2
      ;;
    --hand-avoid-max-center-y)
      HAND_AVOID_MAX_CENTER_Y="$2"
      shift 2
      ;;
    --hand-avoid-extended-max-center-y)
      HAND_AVOID_EXTENDED_MAX_CENTER_Y="$2"
      shift 2
      ;;
    --hand-avoid-extended-min-confidence)
      HAND_AVOID_EXTENDED_MIN_CONFIDENCE="$2"
      shift 2
      ;;
    --hand-avoid-min-lateral-offset)
      HAND_AVOID_MIN_LATERAL_OFFSET="$2"
      shift 2
      ;;
    --log-level)
      LOG_LEVEL="$2"
      shift 2
      ;;
    --face-near-area-ratio)
      FACE_NEAR_AREA_RATIO="$2"
      shift 2
      ;;
    --face-mid-area-ratio)
      FACE_MID_AREA_RATIO="$2"
      shift 2
      ;;
    --motion-near-area-ratio)
      MOTION_NEAR_AREA_RATIO="$2"
      shift 2
      ;;
    --motion-mid-area-ratio)
      MOTION_MID_AREA_RATIO="$2"
      shift 2
      ;;
    --min-motion-area-ratio)
      MIN_MOTION_AREA_RATIO="$2"
      shift 2
      ;;
    --warmup-frames)
      WARMUP_FRAMES="$2"
      WARMUP_FRAMES_EXPLICIT="1"
      shift 2
      ;;
    --hand-cue-min-area-ratio)
      HAND_CUE_MIN_AREA_RATIO="$2"
      shift 2
      ;;
    --hand-cue-max-area-ratio)
      HAND_CUE_MAX_AREA_RATIO="$2"
      shift 2
      ;;
    --hand-cue-min-center-y)
      HAND_CUE_MIN_CENTER_Y="$2"
      shift 2
      ;;
    --hand-cue-min-motion-ratio)
      HAND_CUE_MIN_MOTION_RATIO="$2"
      shift 2
      ;;
    --hand-cue-min-confidence)
      HAND_CUE_MIN_CONFIDENCE="$2"
      shift 2
      ;;
    --no-experimental)
      ALLOW_EXPERIMENTAL="0"
      shift
      ;;
    --help|-h)
      usage
      exit 0
      ;;
    *)
      echo "Unknown option: $1" >&2
      usage >&2
      exit 2
      ;;
  esac
done

if [[ "${REPLAY_DEMO}" == "1" && "${WARMUP_FRAMES_EXPLICIT}" != "1" ]]; then
  WARMUP_FRAMES="1"
fi

if [[ -z "${CAPTURES_DIR}" ]]; then
  if [[ "${ATTACH_EXISTING_RECEIVER}" == "1" ]]; then
    CAPTURES_DIR="$HOME/.openclaw/workspace/runtime/captures"
  else
    CAPTURES_DIR="${RUNTIME_DIR}/captures"
  fi
fi

mkdir -p "$(dirname "${RUNTIME_DIR}")" "$(dirname "${CAPTURES_DIR}")"
RUNTIME_DIR="$(cd "$(dirname "${RUNTIME_DIR}")" && pwd)/$(basename "${RUNTIME_DIR}")"
CAPTURES_DIR="$(cd "$(dirname "${CAPTURES_DIR}")" && pwd)/$(basename "${CAPTURES_DIR}")"
REPLAY_SOURCE="$(cd "$(dirname "${REPLAY_SOURCE}")" && pwd)/$(basename "${REPLAY_SOURCE}")"

mkdir -p "${RUNTIME_DIR}" "${CAPTURES_DIR}"

LATEST_EVENT_OUT="${RUNTIME_DIR}/vision.latest.json"
EVENTS_JSONL="${RUNTIME_DIR}/vision.events.jsonl"
BRIDGE_STATE_OUT="${RUNTIME_DIR}/vision.bridge.state.json"
VISION_OPERATOR_STATE_PATH="${RUNTIME_DIR}/vision.operator.json"
STACK_LOG="${RUNTIME_DIR}/vision-stack.log"
REPLAY_LOG="${RUNTIME_DIR}/vision-replay.log"
MOCK_LOG="${RUNTIME_DIR}/mock-lamp.log"

if [[ "${MOCK_DEVICE}" == "1" && "${BASE_URL_EXPLICIT}" != "1" ]]; then
  BASE_URL="http://127.0.0.1:${MOCK_PORT}"
fi

cleanup() {
  local exit_code=$?
  if [[ -n "${REPLAY_PID:-}" ]]; then kill "${REPLAY_PID}" >/dev/null 2>&1 || true; fi
  if [[ -n "${STACK_PID:-}" ]]; then kill "${STACK_PID}" >/dev/null 2>&1 || true; fi
  if [[ -n "${MOCK_PID:-}" ]]; then kill "${MOCK_PID}" >/dev/null 2>&1 || true; fi
  wait || true
  exit "${exit_code}"
}
trap cleanup EXIT INT TERM

if [[ "${MOCK_DEVICE}" == "1" ]]; then
  "${PYTHON_BIN}" "${REPO_ROOT}/scripts/mock_lamp_server.py" \
    --host 127.0.0.1 \
    --port "${MOCK_PORT}" \
    >"${MOCK_LOG}" 2>&1 &
  MOCK_PID=$!
fi

export MIRA_LIGHT_SERVICE_ROOT="${REPO_ROOT}"
export MIRA_LIGHT_VISION_PYTHON="${PYTHON_BIN}"
export MIRA_LIGHT_WORKSPACE_RUNTIME_DIR="${RUNTIME_DIR}"
export MIRA_LIGHT_CAPTURES_DIR="${CAPTURES_DIR}"
export MIRA_LIGHT_LATEST_EVENT_OUT="${LATEST_EVENT_OUT}"
export MIRA_LIGHT_EVENTS_JSONL="${EVENTS_JSONL}"
export MIRA_LIGHT_BRIDGE_STATE_OUT="${BRIDGE_STATE_OUT}"
export MIRA_LIGHT_VISION_OPERATOR_STATE_PATH="${VISION_OPERATOR_STATE_PATH}"
export MIRA_LIGHT_VISION_HOST="${RECEIVER_HOST}"
export MIRA_LIGHT_VISION_PORT="${RECEIVER_PORT}"
export MIRA_LIGHT_BASE_URL="${BASE_URL}"
export MIRA_LIGHT_VISION_POLL_INTERVAL="${POLL_INTERVAL}"
export MIRA_LIGHT_TRACKING_UPDATE_MS="${TRACKING_UPDATE_MS}"
export MIRA_LIGHT_TOUCH_PERSISTENCE_FRAMES="${TOUCH_PERSISTENCE_FRAMES}"
export MIRA_LIGHT_TOUCH_COOLDOWN_MS="${TOUCH_COOLDOWN_MS}"
export MIRA_LIGHT_TOUCH_MIN_CONFIDENCE="${TOUCH_MIN_CONFIDENCE}"
export MIRA_LIGHT_TOUCH_MIN_SIZE_NORM="${TOUCH_MIN_SIZE_NORM}"
export MIRA_LIGHT_TOUCH_MAX_CENTER_OFFSET="${TOUCH_MAX_CENTER_OFFSET}"
export MIRA_LIGHT_TOUCH_HAND_ARM_MIN_CONFIDENCE="${TOUCH_HAND_ARM_MIN_CONFIDENCE}"
export MIRA_LIGHT_TOUCH_ALLOW_PERSON_FALLBACK="${TOUCH_ALLOW_PERSON_FALLBACK}"
export MIRA_LIGHT_HAND_AVOID_COOLDOWN_MS="${HAND_AVOID_COOLDOWN_MS}"
export MIRA_LIGHT_HAND_AVOID_MIN_CONFIDENCE="${HAND_AVOID_MIN_CONFIDENCE}"
export MIRA_LIGHT_HAND_AVOID_MAX_CENTER_Y="${HAND_AVOID_MAX_CENTER_Y}"
export MIRA_LIGHT_HAND_AVOID_EXTENDED_MAX_CENTER_Y="${HAND_AVOID_EXTENDED_MAX_CENTER_Y}"
export MIRA_LIGHT_HAND_AVOID_EXTENDED_MIN_CONFIDENCE="${HAND_AVOID_EXTENDED_MIN_CONFIDENCE}"
export MIRA_LIGHT_HAND_AVOID_MIN_LATERAL_OFFSET="${HAND_AVOID_MIN_LATERAL_OFFSET}"
export MIRA_LIGHT_VISION_LOG_LEVEL="${LOG_LEVEL}"
export MIRA_LIGHT_FACE_NEAR_AREA_RATIO="${FACE_NEAR_AREA_RATIO}"
export MIRA_LIGHT_FACE_MID_AREA_RATIO="${FACE_MID_AREA_RATIO}"
export MIRA_LIGHT_MOTION_NEAR_AREA_RATIO="${MOTION_NEAR_AREA_RATIO}"
export MIRA_LIGHT_MOTION_MID_AREA_RATIO="${MOTION_MID_AREA_RATIO}"
export MIRA_LIGHT_MIN_MOTION_AREA_RATIO="${MIN_MOTION_AREA_RATIO}"
export MIRA_LIGHT_WARMUP_FRAMES="${WARMUP_FRAMES}"
export MIRA_LIGHT_HAND_CUE_MIN_AREA_RATIO="${HAND_CUE_MIN_AREA_RATIO}"
export MIRA_LIGHT_HAND_CUE_MAX_AREA_RATIO="${HAND_CUE_MAX_AREA_RATIO}"
export MIRA_LIGHT_HAND_CUE_MIN_CENTER_Y="${HAND_CUE_MIN_CENTER_Y}"
export MIRA_LIGHT_HAND_CUE_MIN_MOTION_RATIO="${HAND_CUE_MIN_MOTION_RATIO}"
export MIRA_LIGHT_HAND_CUE_MIN_CONFIDENCE="${HAND_CUE_MIN_CONFIDENCE}"
export MIRA_LIGHT_ALLOW_EXPERIMENTAL="${ALLOW_EXPERIMENTAL}"
export MIRA_LIGHT_VISION_DRY_RUN="${DRY_RUN}"
export MIRA_LIGHT_SKIP_RECEIVER="${ATTACH_EXISTING_RECEIVER}"

bash "${REPO_ROOT}/scripts/run_mira_light_vision_stack.sh" >"${STACK_LOG}" 2>&1 &
STACK_PID=$!

sleep 1
if ! kill -0 "${STACK_PID}" >/dev/null 2>&1; then
  echo "Vision stack exited early. Last log lines:" >&2
  tail -n 40 "${STACK_LOG}" >&2 || true
  exit 1
fi

if [[ "${REPLAY_DEMO}" == "1" ]]; then
  REPLAY_ARGS=(
    --captures-dir "${REPLAY_SOURCE}"
    --receiver-url "http://127.0.0.1:${RECEIVER_PORT}"
    --fps "${REPLAY_FPS}"
  )
  if [[ "${REPLAY_LOOP}" == "1" ]]; then
    REPLAY_ARGS+=(--loop)
  fi
  "${PYTHON_BIN}" "${REPO_ROOT}/scripts/replay_camera_frames_to_receiver.py" "${REPLAY_ARGS[@]}" \
    >"${REPLAY_LOG}" 2>&1 &
  REPLAY_PID=$!
fi

echo "Mira Light live-follow demo is running."
echo "  base_url:           ${BASE_URL}"
echo "  receiver_url:       http://127.0.0.1:${RECEIVER_PORT}"
if [[ "${ATTACH_EXISTING_RECEIVER}" == "1" ]]; then
  echo "  receiver_mode:      attach-existing"
else
  echo "  receiver_mode:      managed-by-demo"
fi
echo "  runtime_dir:        ${RUNTIME_DIR}"
echo "  captures_dir:       ${CAPTURES_DIR}"
echo "  latest_event:       ${LATEST_EVENT_OUT}"
echo "  bridge_state:       ${BRIDGE_STATE_OUT}"
echo "  stack_log:          ${STACK_LOG}"
if [[ "${MOCK_DEVICE}" == "1" ]]; then
  echo "  mock_lamp_log:      ${MOCK_LOG}"
fi
if [[ "${REPLAY_DEMO}" == "1" ]]; then
  echo "  replay_log:         ${REPLAY_LOG}"
fi
echo
echo "Useful checks:"
echo "  curl http://127.0.0.1:${RECEIVER_PORT}/health"
echo "  tail -f ${STACK_LOG}"
echo "  tail -f ${EVENTS_JSONL}"
if [[ "${MOCK_DEVICE}" == "1" ]]; then
  echo "  curl ${BASE_URL}/health"
fi
echo
echo "Press Ctrl+C to stop."

wait "${STACK_PID}"
