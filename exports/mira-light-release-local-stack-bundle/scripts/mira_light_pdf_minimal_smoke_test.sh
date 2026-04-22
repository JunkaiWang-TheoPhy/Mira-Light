#!/usr/bin/env bash
set -euo pipefail

BASE_URL="${MIRA_LIGHT_BASE_URL:-http://172.20.10.3}"
READ_ONLY=0

usage() {
  cat <<'EOF'
Strict PDF-only minimal smoke test for Mira Light.

Usage:
  ./scripts/mira_light_pdf_minimal_smoke_test.sh
  ./scripts/mira_light_pdf_minimal_smoke_test.sh --base-url http://172.20.10.3
  ./scripts/mira_light_pdf_minimal_smoke_test.sh --read-only

What it does:
  1. GET /status
  2. GET /led
  3. GET /actions
  4. POST /led          (unless --read-only)
  5. POST /action       (unless --read-only)
  6. POST /control      (unless --read-only)

This script intentionally does NOT use:
  - simple_lamp_receiver.py
  - OpenClaw
  - local bridge
  - reverse tunnel
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --base-url)
      if [[ $# -lt 2 ]]; then
        echo "Missing value for --base-url" >&2
        exit 1
      fi
      BASE_URL="${2%/}"
      shift 2
      ;;
    --read-only)
      READ_ONLY=1
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown argument: $1" >&2
      echo >&2
      usage >&2
      exit 1
      ;;
  esac
done

BASE_URL="${BASE_URL%/}"

step() {
  printf '\n== %s ==\n' "$1"
}

get_json() {
  local path="$1"
  curl --fail --silent --show-error --location "${BASE_URL}${path}"
  printf '\n'
}

post_json() {
  local path="$1"
  local body="$2"
  curl --fail --silent --show-error --location \
    -X POST "${BASE_URL}${path}" \
    -H 'Content-Type: application/json' \
    -d "${body}"
  printf '\n'
}

printf 'Using lamp base URL: %s\n' "${BASE_URL}"
if [[ "${READ_ONLY}" -eq 1 ]]; then
  printf 'Mode: read-only\n'
else
  printf 'Mode: full smoke test\n'
fi

step 'GET /status'
get_json '/status'

step 'GET /led'
get_json '/led'

step 'GET /actions'
get_json '/actions'

if [[ "${READ_ONLY}" -eq 0 ]]; then
  step 'POST /led (warm solid)'
  post_json '/led' '{"mode":"solid","color":{"r":255,"g":200,"b":120},"brightness":180}'

  step 'POST /action (wave x1)'
  post_json '/action' '{"name":"wave","loops":1}'

  step 'POST /control (absolute servo1=90 servo3=45)'
  post_json '/control' '{"mode":"absolute","servo1":90,"servo3":45}'
fi

printf '\nSmoke test completed.\n'
