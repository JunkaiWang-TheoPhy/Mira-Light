#!/usr/bin/env python3
"""Remove the local Mira Light bridge plugin from OpenClaw."""

from __future__ import annotations

import argparse
from pathlib import Path
import shutil
import sys

from install_local_openclaw_mira_light import (  # noqa: E402
    DEFAULT_CONFIG_PATH,
    DEFAULT_EXTENSIONS_DIR,
    PLUGIN_ID,
    backup_config,
    load_json,
    run_plugins_doctor,
    write_json,
)


def remove_plugin_config(config: dict) -> tuple[dict, list[str]]:
    changes: list[str] = []
    plugins = config.get("plugins")
    if not isinstance(plugins, dict):
        return config, changes

    allow = plugins.get("allow")
    if isinstance(allow, list) and PLUGIN_ID in allow:
        plugins["allow"] = [item for item in allow if item != PLUGIN_ID]
        changes.append(f"removed {PLUGIN_ID} from plugins.allow")

    entries = plugins.get("entries")
    if isinstance(entries, dict) and PLUGIN_ID in entries:
        entries.pop(PLUGIN_ID, None)
        changes.append(f"removed {PLUGIN_ID} from plugins.entries")

    return config, changes


def remove_plugin_link(target_dir: Path, *, dry_run: bool) -> str:
    if not target_dir.exists() and not target_dir.is_symlink():
        return f"plugin dir already absent: {target_dir}"

    if dry_run:
        return f"[dry-run] would remove plugin dir: {target_dir}"

    if target_dir.is_symlink() or target_dir.is_file():
        target_dir.unlink()
    else:
        shutil.rmtree(target_dir)
    return f"removed plugin dir: {target_dir}"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Remove Mira Light from the local OpenClaw config.")
    parser.add_argument("--config-path", default=str(DEFAULT_CONFIG_PATH), help="Path to ~/.openclaw/openclaw.json")
    parser.add_argument("--extensions-dir", default=str(DEFAULT_EXTENSIONS_DIR), help="Path to ~/.openclaw/extensions")
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

    config = load_json(config_path)
    config, config_changes = remove_plugin_config(config)

    print(f"Config path: {config_path}")
    print(f"Extensions dir: {extensions_dir}")
    print(remove_plugin_link(plugin_target_dir, dry_run=args.dry_run))
    if config_changes:
        for item in config_changes:
            print(item)
    else:
        print("No config changes were needed.")

    if args.dry_run:
        print(config.get("plugins", {}))
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
