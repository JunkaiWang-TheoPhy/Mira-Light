#!/usr/bin/env python3
"""Verify the local Mira Light + OpenClaw setup."""

from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path
import sys


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG_PATH = Path.home() / ".openclaw" / "openclaw.json"
PLUGIN_SOURCE_DIR = REPO_ROOT / "tools" / "mira_light_bridge" / "openclaw_mira_light_plugin"


def run(cmd: list[str]) -> tuple[int, str]:
    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, check=False)
    return result.returncode, result.stdout


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify local Mira Light OpenClaw setup.")
    parser.add_argument("--config-path", default=str(DEFAULT_CONFIG_PATH))
    parser.add_argument("--bridge-url", default="http://127.0.0.1:9783")
    parser.add_argument("--vision-url", default="http://127.0.0.1:8000")
    parser.add_argument("--bridge-token", default="test-token")
    args = parser.parse_args()

    config_path = Path(args.config_path).expanduser().resolve()
    if not config_path.is_file():
        print(f"[fail] missing config: {config_path}")
        return 1

    raw = json.loads(config_path.read_text(encoding="utf-8"))
    plugins = raw.get("plugins", {})
    allow = plugins.get("allow", [])
    load = plugins.get("load", {})
    load_paths = load.get("paths", [])
    entries = plugins.get("entries", {})

    print(f"[ok] config found: {config_path}")
    print(f"[check] plugin allowed: {'mira-light-bridge' in allow}")
    print(f"[check] plugin entry exists: {'mira-light-bridge' in entries}")
    print(f"[check] plugin load path registered: {str(PLUGIN_SOURCE_DIR) in load_paths}")
    model_primary = raw.get("agents", {}).get("defaults", {}).get("model", {}).get("primary")
    print(f"[check] default model: {model_primary}")
    extra_paths = raw.get("agents", {}).get("defaults", {}).get("memorySearch", {}).get("extraPaths", [])
    print(f"[check] memorySearch.extraPaths count: {len(extra_paths)}")

    plugin_dir = Path.home() / ".openclaw" / "extensions" / "mira-light-bridge"
    print(f"[check] plugin dir exists: {plugin_dir.exists()} -> {plugin_dir}")

    code, output = run(["curl", "-s", f"{args.bridge_url}/health"])
    print(f"[curl bridge health exit={code}]")
    print(output[:1200].rstrip())

    code, output = run(
        [
            "curl",
            "-s",
            f"{args.bridge_url}/v1/mira-light/scenes",
            "-H",
            f"Authorization: Bearer {args.bridge_token}",
        ]
    )
    print(f"[curl bridge scenes exit={code}]")
    print(output[:1200].rstrip())

    code, output = run(
        [
            "curl",
            "-s",
            f"{args.bridge_url}/v1/mira-light/runtime",
            "-H",
            f"Authorization: Bearer {args.bridge_token}",
        ]
    )
    print(f"[curl bridge runtime exit={code}]")
    print(output[:1200].rstrip())

    code, output = run(["curl", "-s", f"{args.vision_url}/health"])
    print(f"[curl vision health exit={code}]")
    print(output[:1200].rstrip())

    code, output = run(["openclaw", "models", "status", "--json"])
    print(f"[openclaw models status exit={code}]")
    print(output[:2000].rstrip())

    code, output = run(["openclaw", "memory", "status", "--json"])
    print(f"[openclaw memory status exit={code}]")
    print(output[:2500].rstrip())

    code, output = run(["openclaw", "plugins", "doctor"])
    print(f"[openclaw plugins doctor exit={code}]")
    print(output[:2000].rstrip())

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
