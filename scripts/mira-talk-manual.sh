#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

exec "${ROOT}/scripts/run_mira_realtime_voice_interaction.sh" enter-vad "$@"
