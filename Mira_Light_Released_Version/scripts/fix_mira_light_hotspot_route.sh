#!/usr/bin/env bash
set -euo pipefail

TARGET_INPUT="${1:-${MIRA_LIGHT_LAMP_BASE_URL:-http://172.20.10.3}}"
TARGET_IP="$(printf '%s\n' "${TARGET_INPUT}" | sed -E 's#^https?://([^/]+).*$#\1#')"
HOTSPOT_GW="${2:-172.20.10.1}"

usage() {
  cat <<'EOF'
Usage:
  bash scripts/fix_mira_light_hotspot_route.sh [lamp-ip-or-url] [hotspot-gateway]

Examples:
  bash scripts/fix_mira_light_hotspot_route.sh 172.20.10.3 172.20.10.1
  bash scripts/fix_mira_light_hotspot_route.sh http://172.20.10.3

Notes:
  - This is intended for macOS / iPhone hotspot style 172.20.10.x routing.
  - The route add step uses sudo.
EOF
}

if [[ "${TARGET_INPUT}" == "--help" || "${TARGET_INPUT}" == "-h" ]]; then
  usage
  exit 0
fi

echo "Checking hotspot route for ${TARGET_IP} via ${HOTSPOT_GW}..."

if ! ifconfig | grep -q "inet ${HOTSPOT_GW}"; then
  echo "No local interface currently owns ${HOTSPOT_GW}." >&2
  echo "This usually means the Mac is not connected to the expected iPhone hotspot / 172.20.10.x network." >&2
  exit 1
fi

sudo route -n add -host "${TARGET_IP}" "${HOTSPOT_GW}"
route -n get "${TARGET_IP}"
