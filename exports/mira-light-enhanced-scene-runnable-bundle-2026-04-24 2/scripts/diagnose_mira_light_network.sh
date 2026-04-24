#!/usr/bin/env bash
set -euo pipefail

TARGET_INPUT="${1:-${MIRA_LIGHT_LAMP_BASE_URL:-http://172.20.10.3}}"
TARGET_IP="$(printf '%s\n' "${TARGET_INPUT}" | sed -E 's#^https?://([^/]+).*$#\1#')"

usage() {
  cat <<'EOF'
Usage:
  bash scripts/diagnose_mira_light_network.sh [lamp-ip-or-url]

Examples:
  bash scripts/diagnose_mira_light_network.sh 172.20.10.3
  bash scripts/diagnose_mira_light_network.sh http://172.20.10.3
EOF
}

if [[ "${TARGET_INPUT}" == "--help" || "${TARGET_INPUT}" == "-h" ]]; then
  usage
  exit 0
fi

echo "[network] target input: ${TARGET_INPUT}"
echo "[network] target ip: ${TARGET_IP}"
echo

echo "** route"
route -n get "${TARGET_IP}" || true
echo

echo "** active interfaces"
ifconfig | awk '
  /^[a-z0-9]/ { iface=$1; sub(":", "", iface); active=0; ip="" }
  /status: active/ { active=1 }
  /^\tinet / && $2 != "127.0.0.1" { ip=$2 }
  active && ip != "" { print iface, ip; active=0; ip="" }
' || true
echo

echo "** ping"
ping -c 1 -W 2000 "${TARGET_IP}" || true
echo

echo "** http /status"
curl -sS --max-time 5 "http://${TARGET_IP}/status" || true
echo
echo

echo "** http /led"
curl -sS --max-time 5 "http://${TARGET_IP}/led" || true
echo
