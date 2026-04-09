#!/usr/bin/env python3
"""Sync a launchd-friendly local Mira Light service copy under ~/.openclaw.

Why this exists:

- the main repository currently lives under ~/Documents
- macOS launchd jobs can be awkward around Documents/Desktop protected paths
- copying the minimum runtime tree into ~/.openclaw keeps the always-on bridge
  outside that protected area while still letting the repo remain the source of truth
"""

from __future__ import annotations

import argparse
from pathlib import Path
import shutil


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_TARGET_ROOT = Path.home() / ".openclaw" / "mira-light-service"

RELATIVE_PATHS = [
    Path("tools/mira_light_bridge/bridge_server.py"),
    Path("tools/mira_light_bridge/bridge_config.json"),
    Path("tools/mira_light_bridge/embodied_memory_client.py"),
    Path("tools/mira_light_bridge/start_bridge.sh"),
    Path("scripts/cam_receiver_service.py"),
    Path("scripts/mira_light_audio.py"),
    Path("scripts/mira_light_runtime.py"),
    Path("scripts/run_mira_light_vision_stack.sh"),
    Path("scripts/setup_local_mira_light_service_env.sh"),
    Path("scripts/scenes.py"),
    Path("scripts/track_target_event_extractor.py"),
    Path("scripts/vision_runtime_bridge.py"),
    Path("config/mira_light_profile.local.json"),
    Path("requirements.txt"),
]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Sync the local Mira Light service copy under ~/.openclaw.")
    parser.add_argument(
        "--target-root",
        default=str(DEFAULT_TARGET_ROOT),
        help="Target service root (default: ~/.openclaw/mira-light-service)",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    target_root = Path(args.target_root).expanduser().resolve()

    print(f"Repo root: {REPO_ROOT}")
    print(f"Target root: {target_root}")

    for relative_path in RELATIVE_PATHS:
        source = REPO_ROOT / relative_path
        if not source.exists():
            raise SystemExit(f"Missing source file: {source}")

        target = target_root / relative_path
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
        print(f"[copied] {source} -> {target}")

    executable_paths = [
        target_root / "tools" / "mira_light_bridge" / "start_bridge.sh",
        target_root / "scripts" / "run_mira_light_vision_stack.sh",
        target_root / "scripts" / "setup_local_mira_light_service_env.sh",
    ]
    for executable_path in executable_paths:
        executable_path.chmod(0o755)
        print(f"[chmod] {executable_path} -> 755")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
