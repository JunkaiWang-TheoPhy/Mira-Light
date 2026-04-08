#!/usr/bin/env bash
set -euo pipefail

TARGET_IP="${1:-172.20.10.3}"
HOTSPOT_GW="${2:-172.20.10.1}"

echo "Checking hotspot route for ${TARGET_IP} via ${HOTSPOT_GW}..."

if ! ifconfig | rg -q "inet ${HOTSPOT_GW}"; then
  echo "No local interface currently owns ${HOTSPOT_GW}." >&2
  echo "This usually means the Mac is not connected to the expected iPhone hotspot / 172.20.10.x network." >&2
  exit 1
fi

sudo route -n add -host "${TARGET_IP}" "${HOTSPOT_GW}"
route -n get "${TARGET_IP}"
