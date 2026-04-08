#!/usr/bin/env bash
set -euo pipefail

TARGET_IP="${1:-172.20.10.3}"

echo "** route"
route -n get "$TARGET_IP" || true
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
ping -c 1 -W 2000 "$TARGET_IP" || true
echo

echo "** http /status"
curl -sS --max-time 5 "http://${TARGET_IP}/status" || true
echo
echo

echo "** http /led"
curl -sS --max-time 5 "http://${TARGET_IP}/led" || true
echo
