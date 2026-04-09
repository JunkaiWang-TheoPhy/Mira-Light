#!/usr/bin/env bash
set -euo pipefail

LOCAL_HOST="${MIRA_LIGHT_LINGZHU_TUNNEL_LOCAL_HOST:-127.0.0.1}"
LOCAL_PORT="${MIRA_LIGHT_LINGZHU_TUNNEL_LOCAL_PORT:-31879}"
REMOTE_HOST="${MIRA_LIGHT_LINGZHU_REMOTE_HOST:-43.160.239.180}"
REMOTE_USER="${MIRA_LIGHT_LINGZHU_REMOTE_USER:-ubuntu}"
REMOTE_PASSWORD="${MIRA_LIGHT_LINGZHU_REMOTE_PASSWORD:-}"
REMOTE_TARGET_HOST="${MIRA_LIGHT_LINGZHU_REMOTE_TARGET_HOST:-127.0.0.1}"
REMOTE_TARGET_PORT="${MIRA_LIGHT_LINGZHU_REMOTE_TARGET_PORT:-18789}"
STATE_DIR="${HOME}/.openclaw/mira-light-runtime"
PID_FILE="${STATE_DIR}/lingzhu-tunnel.pid"
LOG_FILE="${STATE_DIR}/lingzhu-tunnel.log"
EXPECT_FILE="${STATE_DIR}/lingzhu-tunnel.expect"
HEALTH_URL="http://${LOCAL_HOST}:${LOCAL_PORT}/v1/health"

mkdir -p "${STATE_DIR}"

if curl -fsS "${HEALTH_URL}" >/dev/null 2>&1; then
  echo "[lingzhu-tunnel] already healthy at ${HEALTH_URL}"
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

if command -v lsof >/dev/null 2>&1; then
  EXISTING_LISTENER="$(lsof -t -iTCP:${LOCAL_PORT} -sTCP:LISTEN 2>/dev/null | head -n 1 || true)"
  if [[ -n "${EXISTING_LISTENER}" ]]; then
    kill "${EXISTING_LISTENER}" >/dev/null 2>&1 || true
    sleep 1
  fi
fi

if [[ -z "${REMOTE_PASSWORD}" ]]; then
  echo "[lingzhu-tunnel] missing MIRA_LIGHT_LINGZHU_REMOTE_PASSWORD" >&2
  exit 1
fi

cat >"${EXPECT_FILE}" <<EOF
set timeout 20
spawn ssh -f -o StrictHostKeyChecking=no -o ExitOnForwardFailure=yes -o ServerAliveInterval=30 -o ServerAliveCountMax=3 -N -L ${LOCAL_HOST}:${LOCAL_PORT}:${REMOTE_TARGET_HOST}:${REMOTE_TARGET_PORT} ${REMOTE_USER}@${REMOTE_HOST}
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
  echo "[lingzhu-tunnel] failed to launch ssh tunnel; log: ${LOG_FILE}" >&2
  exit 1
}

for _ in $(seq 1 15); do
  if curl -fsS "${HEALTH_URL}" >/dev/null 2>&1; then
    if command -v lsof >/dev/null 2>&1; then
      lsof -t -iTCP:${LOCAL_PORT} -sTCP:LISTEN 2>/dev/null | head -n 1 >"${PID_FILE}" || true
    fi
    echo "[lingzhu-tunnel] ready at ${HEALTH_URL}"
    exit 0
  fi
  sleep 1
done

echo "[lingzhu-tunnel] failed to become healthy; log: ${LOG_FILE}" >&2
exit 1
