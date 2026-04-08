#!/bin/zsh
set -euo pipefail

ENV_FILE="$HOME/.openclaw/mira-light-vision.env"
if [[ -f "$ENV_FILE" ]]; then
  source "$ENV_FILE"
fi

SERVICE_SCRIPT="$HOME/.openclaw/mira-light-service/scripts/run_mira_light_vision_stack.sh"
REPO_SCRIPT="__REPO_ROOT__/scripts/run_mira_light_vision_stack.sh"

if [[ -f "$SERVICE_SCRIPT" ]]; then
  exec /bin/zsh "$SERVICE_SCRIPT" "$@"
fi

exec /bin/zsh "$REPO_SCRIPT" "$@"
