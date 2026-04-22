#!/usr/bin/env bash
set -euo pipefail

CONSOLE_PORT="${MIRA_LIGHT_CONSOLE_PORT:-8765}"
BRIDGE_PORT="${MIRA_LIGHT_BRIDGE_PORT:-9783}"
RECEIVER_PORT="${MIRA_LIGHT_RECEIVER_PORT:-9784}"

CONSOLE_URL="http://127.0.0.1:${CONSOLE_PORT}/"
BRIDGE_URL="http://127.0.0.1:${BRIDGE_PORT}/health"
RECEIVER_URL="http://127.0.0.1:${RECEIVER_PORT}/health"

echo "[smoke] checking bridge ${BRIDGE_URL}"
curl -fsS "${BRIDGE_URL}" | grep -q '"ok"'

echo "[smoke] checking receiver ${RECEIVER_URL}"
curl -fsS "${RECEIVER_URL}" | grep -q '"ok"'

echo "[smoke] checking console ${CONSOLE_URL}"
curl -fsS "${CONSOLE_URL}" | grep -q "Mira Light Director Console"

echo "[smoke] ok console=${CONSOLE_URL} bridge=${BRIDGE_URL} receiver=${RECEIVER_URL}"
