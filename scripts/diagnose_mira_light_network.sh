#!/usr/bin/env bash
set -euo pipefail

TARGET_INPUT="${1:-tcp://192.168.31.10:9527}"
TARGET_IP="$(printf '%s\n' "${TARGET_INPUT}" | sed -E 's#^[a-z]+://([^/:]+).*$#\1#; s#:.*$##')"

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

echo "** tcp port 9527"
nc -vz -w 3 "$TARGET_IP" 9527 || true
echo

echo "** tcp port 9528"
nc -vz -w 3 "$TARGET_IP" 9528 || true
echo

echo "** tcp raw command"
printf '#003P1500T1000!\n' | nc -w 3 "$TARGET_IP" 9527 || true
echo
