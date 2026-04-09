#!/usr/bin/env bash
set -euo pipefail

TARGET_INPUT="${1:-tcp://192.168.31.10:9527}"
TARGET_IP="$(printf '%s\n' "${TARGET_INPUT}" | sed -E 's#^[a-z]+://([^/:]+).*$#\1#; s#:.*$##')"
HOTSPOT_GW="${2:-$(printf '%s\n' "${TARGET_IP}" | awk -F. 'NF==4 {print $1 "." $2 "." $3 ".1"}')}"

echo "Checking hotspot route for ${TARGET_IP} via ${HOTSPOT_GW}..."

if ! ifconfig | rg -q "inet ${HOTSPOT_GW}"; then
  echo "No local interface currently owns ${HOTSPOT_GW}." >&2
  echo "This usually means the Mac is not connected to the expected local network segment for ${TARGET_IP}." >&2
  exit 1
fi

sudo route -n add -host "${TARGET_IP}" "${HOTSPOT_GW}"
route -n get "${TARGET_IP}"
