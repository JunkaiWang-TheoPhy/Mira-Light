#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# Manual mode should be more forgiving than the open mic preset.
# Keep the turn open a bit longer so short pauses do not cut the user off.
exec "${ROOT}/scripts/run_mira_realtime_voice_interaction.sh" enter-vad --vad-end-ms 1200 "$@"
