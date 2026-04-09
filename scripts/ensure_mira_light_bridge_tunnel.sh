#!/usr/bin/env bash
set -euo pipefail

LOCAL_HOST="${MIRA_LIGHT_BRIDGE_TUNNEL_LOCAL_HOST:-127.0.0.1}"
LOCAL_PORT="${MIRA_LIGHT_BRIDGE_TUNNEL_LOCAL_PORT:-9783}"
REMOTE_HOST="${MIRA_LIGHT_BRIDGE_REMOTE_HOST:-43.160.239.180}"
REMOTE_USER="${MIRA_LIGHT_BRIDGE_REMOTE_USER:-ubuntu}"
REMOTE_PASSWORD="${MIRA_LIGHT_BRIDGE_REMOTE_PASSWORD:-${MIRA_LIGHT_LINGZHU_REMOTE_PASSWORD:-}}"
REMOTE_BIND_HOST="${MIRA_LIGHT_BRIDGE_REMOTE_BIND_HOST:-127.0.0.1}"
REMOTE_BIND_PORT="${MIRA_LIGHT_BRIDGE_REMOTE_BIND_PORT:-19783}"
LOCAL_WAIT_SECONDS="${MIRA_LIGHT_BRIDGE_TUNNEL_LOCAL_WAIT_SECONDS:-20}"
STATE_DIR="${HOME}/.openclaw/mira-light-runtime"
PID_FILE="${STATE_DIR}/bridge-tunnel.pid"
LOG_FILE="${STATE_DIR}/bridge-tunnel.log"
EXPECT_FILE="${STATE_DIR}/bridge-tunnel.expect"
LOCAL_HEALTH_URL="http://${LOCAL_HOST}:${LOCAL_PORT}/health"
REMOTE_HEALTH_COMMAND="curl -fsS http://${REMOTE_BIND_HOST}:${REMOTE_BIND_PORT}/health >/dev/null"

mkdir -p "${STATE_DIR}"

if [[ -z "${REMOTE_PASSWORD}" ]]; then
  echo "[bridge-tunnel] missing MIRA_LIGHT_BRIDGE_REMOTE_PASSWORD" >&2
  exit 1
fi

wait_for_local_bridge() {
  local waited=0
  while (( waited < LOCAL_WAIT_SECONDS )); do
    if curl -fsS "${LOCAL_HEALTH_URL}" >/dev/null 2>&1; then
      return 0
    fi
    sleep 1
    waited=$((waited + 1))
  done
  return 1
}

remote_health_ok() {
  expect <<EOF >/dev/null 2>&1
set timeout 15
spawn ssh -o StrictHostKeyChecking=no ${REMOTE_USER}@${REMOTE_HOST} "${REMOTE_HEALTH_COMMAND}"
expect {
  "password:" {
    send "${REMOTE_PASSWORD}\r"
    exp_continue
  }
  timeout {
    exit 124
  }
  eof {
    catch wait result
    exit [lindex \$result 3]
  }
}
EOF
}

find_existing_tunnel_pid() {
  pgrep -f "ssh .* -R ${REMOTE_BIND_HOST}:${REMOTE_BIND_PORT}:${LOCAL_HOST}:${LOCAL_PORT} ${REMOTE_USER}@${REMOTE_HOST}" | head -n 1 || true
}

if ! wait_for_local_bridge; then
  echo "[bridge-tunnel] local bridge did not become healthy at ${LOCAL_HEALTH_URL}" >&2
  exit 1
fi

if remote_health_ok; then
  EXISTING_PID="$(find_existing_tunnel_pid)"
  if [[ -n "${EXISTING_PID}" ]]; then
    printf '%s\n' "${EXISTING_PID}" >"${PID_FILE}"
  fi
  echo "[bridge-tunnel] already healthy at ${REMOTE_BIND_HOST}:${REMOTE_BIND_PORT}"
  exit 0
fi

if [[ -f "${PID_FILE}" ]]; then
  EXISTING_PID="$(cat "${PID_FILE}")"
  if [[ -n "${EXISTING_PID}" ]] && kill -0 "${EXISTING_PID}" >/dev/null 2>&1; then
    kill "${EXISTING_PID}" >/dev/null 2>&1 || true
    sleep 1
  fi
  rm -f "${PID_FILE}"
fi

EXISTING_PID="$(find_existing_tunnel_pid)"
if [[ -n "${EXISTING_PID}" ]]; then
  kill "${EXISTING_PID}" >/dev/null 2>&1 || true
  sleep 1
fi

cat >"${EXPECT_FILE}" <<EOF
set timeout 20
spawn ssh -f -o StrictHostKeyChecking=no -o ExitOnForwardFailure=yes -o ServerAliveInterval=30 -o ServerAliveCountMax=3 -N -R ${REMOTE_BIND_HOST}:${REMOTE_BIND_PORT}:${LOCAL_HOST}:${LOCAL_PORT} ${REMOTE_USER}@${REMOTE_HOST}
expect {
  "password:" {
    send "${REMOTE_PASSWORD}\r"
    exp_continue
  }
  timeout {
    exit 124
  }
  eof {
    exit [lindex [wait] 3]
  }
}
EOF

expect "${EXPECT_FILE}" >"${LOG_FILE}" 2>&1 || {
  echo "[bridge-tunnel] failed to launch ssh reverse tunnel; log: ${LOG_FILE}" >&2
  exit 1
}

for _ in $(seq 1 15); do
  if remote_health_ok; then
    EXISTING_PID="$(find_existing_tunnel_pid)"
    if [[ -n "${EXISTING_PID}" ]]; then
      printf '%s\n' "${EXISTING_PID}" >"${PID_FILE}"
    fi
    echo "[bridge-tunnel] ready at ${REMOTE_BIND_HOST}:${REMOTE_BIND_PORT}"
    exit 0
  fi
  sleep 1
done

echo "[bridge-tunnel] failed to become healthy on remote; log: ${LOG_FILE}" >&2
exit 1
