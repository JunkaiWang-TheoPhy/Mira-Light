#!/bin/zsh
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
CONFIG_PATH="${MIRA_LIGHT_BRIDGE_CONFIG:-$SCRIPT_DIR/bridge_config.json}"

BRIDGE_HOST="${MIRA_LIGHT_BRIDGE_HOST:-127.0.0.1}"
BRIDGE_PORT="${MIRA_LIGHT_BRIDGE_PORT:-9783}"
REMOTE="${MIRA_LIGHT_BRIDGE_REMOTE:-ubuntu@43.160.217.153}"
REMOTE_BIND_PORT="${MIRA_LIGHT_BRIDGE_REMOTE_BIND_PORT:-9783}"

echo "Starting SSH reverse tunnel:"
echo "  remote: $REMOTE"
echo "  remote loopback bind: 127.0.0.1:$REMOTE_BIND_PORT"
echo "  local bridge target: $BRIDGE_HOST:$BRIDGE_PORT"
echo "  config: $CONFIG_PATH"

ssh -N -R "127.0.0.1:${REMOTE_BIND_PORT}:${BRIDGE_HOST}:${BRIDGE_PORT}" "$REMOTE"
