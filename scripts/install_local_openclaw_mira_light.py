#!/usr/bin/env python3
"""Install and configure the local Mira Light bridge plugin for OpenClaw.

This script is intentionally practical:

- create a timestamped backup of ~/.openclaw/openclaw.json
- link the local plugin source into ~/.openclaw/extensions/mira-light-bridge
- patch plugins.allow, plugins.load.paths, and plugins.entries in the local OpenClaw config
- optionally validate with `openclaw plugins doctor`

It does not try to be a general plugin manager. It is a project-local helper
for making the current repository actually usable with the local OpenClaw
instance.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_STATE_DIR = Path.home() / ".openclaw"
DEFAULT_CONFIG_PATH = DEFAULT_STATE_DIR / "openclaw.json"
DEFAULT_EXTENSIONS_DIR = DEFAULT_STATE_DIR / "extensions"
PLUGIN_ID = "mira-light-bridge"
PLUGIN_SOURCE_DIR = REPO_ROOT / "tools" / "mira_light_bridge" / "openclaw_mira_light_plugin"


def now_stamp() -> str:
    return datetime.now(timezone.utc).astimezone().strftime("%Y%m%d-%H%M%S")


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def backup_config(config_path: Path) -> Path:
    target = config_path.with_name(f"{config_path.name}.bak.mira-light-{now_stamp()}")
    shutil.copy2(config_path, target)
    return target


def ensure_plugin_link(target_dir: Path, source_dir: Path, *, dry_run: bool) -> str:
    if dry_run:
        return f"[dry-run] would link {target_dir} -> {source_dir}"

    target_dir.parent.mkdir(parents=True, exist_ok=True)
    if target_dir.exists() or target_dir.is_symlink():
        if target_dir.is_symlink() and Path(os.readlink(target_dir)) == source_dir:
            return f"plugin link already exists: {target_dir}"
        if target_dir.is_symlink() or target_dir.is_file():
            target_dir.unlink()
        else:
            shutil.rmtree(target_dir)
    target_dir.symlink_to(source_dir, target_is_directory=True)
    return f"linked plugin dir: {target_dir} -> {source_dir}"


def ensure_plugin_config(
    config: dict[str, Any],
    *,
    bridge_base_url: str,
    bridge_token: str,
    request_timeout_ms: int,
) -> dict[str, Any]:
    plugins = config.setdefault("plugins", {})
    allow = plugins.setdefault("allow", [])
    if PLUGIN_ID not in allow:
        allow.append(PLUGIN_ID)

    load = plugins.setdefault("load", {})
    paths = load.setdefault("paths", [])
    plugin_source = str(PLUGIN_SOURCE_DIR)
    if plugin_source not in paths:
        paths.append(plugin_source)

    entries = plugins.setdefault("entries", {})
    entries[PLUGIN_ID] = {
        "enabled": True,
        "config": {
            "bridgeBaseUrl": bridge_base_url,
            "bridgeToken": bridge_token,
            "requestTimeoutMs": request_timeout_ms,
        },
    }
    return config


def run_plugins_doctor() -> tuple[int, str]:
    result = subprocess.run(
        ["openclaw", "plugins", "doctor"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        check=False,
    )
    return result.returncode, result.stdout


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Install Mira Light into the local OpenClaw config.")
    parser.add_argument("--config-path", default=str(DEFAULT_CONFIG_PATH), help="Path to ~/.openclaw/openclaw.json")
    parser.add_argument("--extensions-dir", default=str(DEFAULT_EXTENSIONS_DIR), help="Path to ~/.openclaw/extensions")
    parser.add_argument("--bridge-base-url", default="http://127.0.0.1:9783", help="Local bridge base URL")
    parser.add_argument(
        "--bridge-token",
        default=os.environ.get("MIRA_LIGHT_BRIDGE_TOKEN", "test-token"),
        help="Bridge token written into the local OpenClaw config",
    )
    parser.add_argument("--request-timeout-ms", type=int, default=5000, help="Plugin request timeout")
    parser.add_argument("--dry-run", action="store_true", help="Show planned changes without writing them")
    parser.add_argument("--doctor", action="store_true", help="Run `openclaw plugins doctor` after apply")
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    config_path = Path(args.config_path).expanduser().resolve()
    extensions_dir = Path(args.extensions_dir).expanduser().resolve()
    plugin_target_dir = extensions_dir / PLUGIN_ID

    if not config_path.is_file():
        raise SystemExit(f"OpenClaw config not found: {config_path}")

    if not PLUGIN_SOURCE_DIR.is_dir():
        raise SystemExit(f"Plugin source dir not found: {PLUGIN_SOURCE_DIR}")

    config = load_json(config_path)
    config = ensure_plugin_config(
        config,
        bridge_base_url=args.bridge_base_url,
        bridge_token=args.bridge_token,
        request_timeout_ms=args.request_timeout_ms,
    )

    print(f"Config path: {config_path}")
    print(f"Extensions dir: {extensions_dir}")
    print(f"Plugin source: {PLUGIN_SOURCE_DIR}")
    print(ensure_plugin_link(plugin_target_dir, PLUGIN_SOURCE_DIR, dry_run=args.dry_run))

    if args.dry_run:
        print(json.dumps(config.get("plugins", {}), ensure_ascii=False, indent=2))
        return 0

    backup_path = backup_config(config_path)
    write_json(config_path, config)
    print(f"Backed up config to: {backup_path}")
    print(f"Updated config: {config_path}")

    if args.doctor:
        code, output = run_plugins_doctor()
        print("--- openclaw plugins doctor ---")
        print(output.rstrip())
        return code

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
