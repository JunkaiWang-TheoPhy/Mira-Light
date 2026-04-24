#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
VENV_DIR="${REPO_ROOT}/.venv"
PYTHON_BIN="${MIRA_LIGHT_PYTHON:-}"
RUN_ONLINE=0
STRICT_ONLINE=0

usage() {
  cat <<'EOF'
Usage:
  bash scripts/doctor_release.sh [options]

Options:
  --offline         Run only offline checks (default)
  --online          Run offline checks, then add relaxed online probes
  --strict-online   Run offline checks, then require online probes to pass
  --help            Show this message
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --offline)
      RUN_ONLINE=0
      shift
      ;;
    --online)
      RUN_ONLINE=1
      shift
      ;;
    --strict-online)
      RUN_ONLINE=1
      STRICT_ONLINE=1
      shift
      ;;
    --help|-h)
      usage
      exit 0
      ;;
    *)
      echo "Unknown option: $1" >&2
      usage >&2
      exit 1
      ;;
  esac
done

if [[ -z "${PYTHON_BIN}" ]]; then
  if [[ -x "${VENV_DIR}/bin/python" ]]; then
    PYTHON_BIN="${VENV_DIR}/bin/python"
  else
    PYTHON_BIN="$(command -v python3)"
  fi
fi

if [[ -z "${PYTHON_BIN}" ]]; then
  echo "python3 is required but was not found in PATH." >&2
  exit 1
fi

if ! "${PYTHON_BIN}" -c 'import sys; raise SystemExit(0 if sys.version_info >= (3, 10) else 1)'; then
  echo "Python 3.10+ is required for Mira Light release scripts." >&2
  "${PYTHON_BIN}" --version >&2 || true
  exit 1
fi

echo "[doctor] offline preflight"
"${PYTHON_BIN}" "${REPO_ROOT}/scripts/preflight_release.py" offline

echo "[doctor] python compile checks"
"${PYTHON_BIN}" -m py_compile \
  "${REPO_ROOT}/scripts/scenes.py" \
  "${REPO_ROOT}/scripts/mira_light_runtime.py" \
  "${REPO_ROOT}/scripts/mira_light_safety.py" \
  "${REPO_ROOT}/scripts/preflight_release.py" \
  "${REPO_ROOT}/scripts/remove_local_openclaw_mira_light.py" \
  "${REPO_ROOT}/scripts/console_server.py" \
  "${REPO_ROOT}/tools/mira_light_bridge/bridge_server.py"

echo "[doctor] unit tests"
bash "${REPO_ROOT}/scripts/run_release_tests.sh"

if [[ "${RUN_ONLINE}" == "1" ]]; then
  ONLINE_ARGS=(online)
  if [[ "${STRICT_ONLINE}" == "1" ]]; then
    ONLINE_ARGS+=(--strict-online)
  fi

  echo "[doctor] online preflight"
  "${PYTHON_BIN}" "${REPO_ROOT}/scripts/preflight_release.py" "${ONLINE_ARGS[@]}"

  if command -v openclaw >/dev/null 2>&1 && [[ -f "${HOME}/.openclaw/openclaw.json" ]]; then
    echo "[doctor] OpenClaw live verification"
    "${PYTHON_BIN}" "${REPO_ROOT}/scripts/verify_local_openclaw_mira_light.py"
  else
    echo "[doctor] OpenClaw not detected locally; skipping live plugin verification"
  fi
else
  echo "[doctor] online checks skipped; use --online after bridge/receiver/lamp are available"
fi

echo "[doctor] done"
