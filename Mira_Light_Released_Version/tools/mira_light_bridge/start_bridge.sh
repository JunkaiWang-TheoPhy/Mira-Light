#!/bin/zsh
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
CONFIG_PATH="${MIRA_LIGHT_BRIDGE_CONFIG:-$SCRIPT_DIR/bridge_config.json}"

python3 "$SCRIPT_DIR/bridge_server.py" --config "$CONFIG_PATH" "$@"

