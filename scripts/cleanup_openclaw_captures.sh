#!/usr/bin/env bash
set -euo pipefail

TARGET_DIR="${HOME}/.openclaw/workspace/runtime/captures"
MAX_BYTES=$((1024 * 1024 * 1024))
INTERVAL_SECONDS=60
RUN_ONCE=0
LAUNCH_AGENT_LABEL="${LAUNCH_AGENT_LABEL:-com.huhulitong.cleanup-openclaw-captures}"
LAUNCH_AGENT_PLIST="${LAUNCH_AGENT_PLIST:-${HOME}/Library/LaunchAgents/${LAUNCH_AGENT_LABEL}.plist}"
SCRIPT_PATH="${SCRIPT_PATH:-$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/$(basename "${BASH_SOURCE[0]}")}"
EXPIRE_AT="${CLEANUP_EXPIRE_AT:-2026-04-13 00:00:00}"

usage() {
  cat <<'EOF'
Usage: cleanup_openclaw_captures.sh [options]

Automatically watches the OpenClaw captures directory. When the directory size
exceeds the configured limit, it deletes every image except the newest one.

Options:
  --dir PATH          Directory to monitor.
  --max-bytes BYTES   Cleanup threshold in bytes. Default: 1073741824 (1 GiB)
  --interval SEC      Poll interval in seconds. Default: 60
  --once              Run a single check and exit.
  --help              Show this help.

Examples:
  bash scripts/cleanup_openclaw_captures.sh --once
  bash scripts/cleanup_openclaw_captures.sh --interval 30
EOF
}

log() {
  printf '[%s] %s\n' "$(date '+%Y-%m-%d %H:%M:%S')" "$*"
}

expiry_epoch() {
  date -j -f '%Y-%m-%d %H:%M:%S' "$EXPIRE_AT" '+%s'
}

now_epoch() {
  date '+%s'
}

unique_trash_path() {
  local source_path="$1"
  local trash_dir="${HOME}/.Trash"
  local base_name
  local candidate
  local counter=1

  mkdir -p "$trash_dir"
  base_name="$(basename "$source_path")"
  candidate="${trash_dir}/${base_name}"

  while [[ -e "$candidate" ]]; do
    candidate="${trash_dir}/${base_name}.${counter}"
    ((counter+=1))
  done

  printf '%s' "$candidate"
}

move_to_trash() {
  local source_path="$1"
  local trash_path

  if [[ ! -e "$source_path" ]]; then
    return 0
  fi

  trash_path="$(unique_trash_path "$source_path")"
  mv "$source_path" "$trash_path"
  log "retire: moved '$source_path' to '$trash_path'"
}

retire_self() {
  log "retire: expiry reached (${EXPIRE_AT}), disabling cleanup job"

  move_to_trash "$LAUNCH_AGENT_PLIST"
  move_to_trash "$SCRIPT_PATH"

  launchctl bootout "gui/$(id -u)/${LAUNCH_AGENT_LABEL}" >/dev/null 2>&1 \
    || launchctl remove "${LAUNCH_AGENT_LABEL}" >/dev/null 2>&1 \
    || true

  exit 0
}

check_expiry() {
  local expires_at
  expires_at="$(expiry_epoch)"

  if (( "$(now_epoch)" >= expires_at )); then
    retire_self
  fi
}

is_image_file() {
  local path="$1"
  local lower="${path##*/}"
  lower="$(printf '%s' "$lower" | tr '[:upper:]' '[:lower:]')"

  case "$lower" in
    *.jpg|*.jpeg|*.png|*.webp|*.gif|*.bmp|*.tif|*.tiff)
      return 0
      ;;
    *)
      return 1
      ;;
  esac
}

dir_size_bytes() {
  if [[ ! -d "$TARGET_DIR" ]]; then
    echo 0
    return
  fi

  local size_kib
  size_kib="$(du -sk "$TARGET_DIR" | awk '{print $1}')"
  echo $((size_kib * 1024))
}

newest_image_path() {
  local newest_file=""
  local newest_birth=-1
  local newest_mtime=-1
  local file birth mtime

  while IFS= read -r -d '' file; do
    is_image_file "$file" || continue

    birth="$(stat -f '%B' "$file" 2>/dev/null || echo 0)"
    mtime="$(stat -f '%m' "$file" 2>/dev/null || echo 0)"

    if (( birth > newest_birth || (birth == newest_birth && mtime > newest_mtime) )); then
      newest_birth="$birth"
      newest_mtime="$mtime"
      newest_file="$file"
    fi
  done < <(find "$TARGET_DIR" -type f -print0)

  printf '%s' "$newest_file"
}

cleanup_once() {
  check_expiry

  if [[ ! -d "$TARGET_DIR" ]]; then
    log "skip: directory not found: $TARGET_DIR"
    return 0
  fi

  local size_bytes
  size_bytes="$(dir_size_bytes)"

  if (( size_bytes <= MAX_BYTES )); then
    log "skip: size ${size_bytes} bytes is within limit ${MAX_BYTES} bytes"
    return 0
  fi

  local newest_file
  newest_file="$(newest_image_path)"

  if [[ -z "$newest_file" ]]; then
    log "skip: no image files found in $TARGET_DIR"
    return 0
  fi

  local deleted_count=0
  local file
  while IFS= read -r -d '' file; do
    is_image_file "$file" || continue
    if [[ "$file" == "$newest_file" ]]; then
      continue
    fi

    rm -f -- "$file"
    ((deleted_count+=1))
  done < <(find "$TARGET_DIR" -type f -print0)

  log "cleanup: kept newest image '$newest_file', deleted ${deleted_count} older image(s)"
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --dir)
      TARGET_DIR="$2"
      shift 2
      ;;
    --max-bytes)
      MAX_BYTES="$2"
      shift 2
      ;;
    --interval)
      INTERVAL_SECONDS="$2"
      shift 2
      ;;
    --once)
      RUN_ONCE=1
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

check_expiry
cleanup_once

if (( RUN_ONCE == 1 )); then
  exit 0
fi

log "watching $TARGET_DIR with limit ${MAX_BYTES} bytes, interval ${INTERVAL_SECONDS}s"
while true; do
  sleep "$INTERVAL_SECONDS"
  cleanup_once
done
