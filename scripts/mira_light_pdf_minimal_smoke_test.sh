#!/usr/bin/env bash
set -euo pipefail

BASE_URL="${MIRA_LIGHT_BASE_URL:-tcp://192.168.31.10:9527}"
READ_ONLY=0

usage() {
  cat <<'EOF'
Strict PDF-only minimal smoke test for Mira Light.

Usage:
  ./scripts/mira_light_pdf_minimal_smoke_test.sh
  ./scripts/mira_light_pdf_minimal_smoke_test.sh --base-url tcp://192.168.31.10:9527
  ./scripts/mira_light_pdf_minimal_smoke_test.sh --read-only

What it does:
  1. Read cached status through the transport-aware runtime client
  2. Read cached LED state
  3. Read advertised actions
  4. Simulate LED update     (unless --read-only)
  5. Simulate action trigger (unless --read-only)
  6. Send TCP servo control  (unless --read-only)

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
  local method_name="$1"
  python3 - "$BASE_URL" "$method_name" <<'PY'
import json
import sys
from pathlib import Path

ROOT = Path.cwd()
SCRIPTS_DIR = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

from mira_light_runtime import DEFAULT_TIMEOUT_SECONDS, MiraLightClient

base_url = sys.argv[1]
method_name = sys.argv[2]
client = MiraLightClient(base_url=base_url, timeout_seconds=DEFAULT_TIMEOUT_SECONDS, dry_run=False)
method = getattr(client, method_name)
print(json.dumps(method(), ensure_ascii=False, indent=2))
PY
}

post_json() {
  local method_name="$1"
  local body="$2"
  python3 - "$BASE_URL" "$method_name" "$body" <<'PY'
import json
import sys
from pathlib import Path

ROOT = Path.cwd()
SCRIPTS_DIR = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

from mira_light_runtime import DEFAULT_TIMEOUT_SECONDS, MiraLightClient

base_url = sys.argv[1]
method_name = sys.argv[2]
payload = json.loads(sys.argv[3])
client = MiraLightClient(base_url=base_url, timeout_seconds=DEFAULT_TIMEOUT_SECONDS, dry_run=False)
method = getattr(client, method_name)
print(json.dumps(method(payload), ensure_ascii=False, indent=2))
PY
}

printf 'Using lamp base URL: %s\n' "${BASE_URL}"
if [[ "${READ_ONLY}" -eq 1 ]]; then
  printf 'Mode: read-only\n'
else
  printf 'Mode: full smoke test\n'
fi

step 'status'
get_json 'get_status'

step 'led'
get_json 'get_led'

step 'actions'
get_json 'get_actions'

if [[ "${READ_ONLY}" -eq 0 ]]; then
  step 'set_led (warm solid)'
  post_json 'set_led' '{"mode":"solid","color":{"r":255,"g":200,"b":120},"brightness":180}'

  step 'run_action (wave x1)'
  post_json 'run_action' '{"name":"wave","loops":1}'

  step 'control (absolute servo4=90)'
  post_json 'control' '{"mode":"absolute","servo4":90}'
fi

printf '\nSmoke test completed.\n'
