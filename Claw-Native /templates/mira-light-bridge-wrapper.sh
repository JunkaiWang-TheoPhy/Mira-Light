#!/bin/zsh
set -euo pipefail

ENV_FILE="$HOME/.openclaw/mira-light-bridge.env"
if [[ -f "$ENV_FILE" ]]; then
  source "$ENV_FILE"
fi

SERVICE_START="$HOME/.openclaw/mira-light-service/tools/mira_light_bridge/start_bridge.sh"
REPO_START="__REPO_ROOT__/tools/mira_light_bridge/start_bridge.sh"

if [[ -f "$SERVICE_START" ]]; then
  exec /bin/zsh "$SERVICE_START" "$@"
fi

exec /bin/zsh "$REPO_START" "$@"
