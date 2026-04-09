#!/usr/bin/env python3
"""Materialize the repository's Claw-Native package into the local machine.

This script bridges the gap between:

- repo-native templates under `Claw-Native `
- machine-local state under `~/.openclaw`, `~/.local/bin`, and `~/Library/LaunchAgents`

It intentionally preserves unrelated local config where practical while forcing
the Mira-specific defaults that this repository expects.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import secrets
import shutil
import subprocess
import sys
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
CLAW_NATIVE_ROOT = REPO_ROOT / "Claw-Native "
TEMPLATES_ROOT = CLAW_NATIVE_ROOT / "templates"
WORKSPACE_TEMPLATES_ROOT = CLAW_NATIVE_ROOT / "workspace"
DEFAULT_STATE_DIR = Path.home() / ".openclaw"
DEFAULT_LOCAL_BIN_DIR = Path.home() / ".local" / "bin"
DEFAULT_LAUNCH_AGENTS_DIR = Path.home() / "Library" / "LaunchAgents"
DEFAULT_BRIDGE_CONFIG = REPO_ROOT / "tools" / "mira_light_bridge" / "bridge_config.json"


def now_stamp() -> str:
    return datetime.now(timezone.utc).astimezone().strftime("%Y%m%d-%H%M%S")


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def run(cmd: list[str], *, cwd: Path | None = None) -> tuple[int, str]:
    result = subprocess.run(
        cmd,
        cwd=str(cwd) if cwd is not None else None,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        check=False,
    )
    return result.returncode, result.stdout


def load_shell_exports(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}

    values: dict[str, str] = {}
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or not line.startswith("export "):
            continue
        body = line[len("export ") :]
        key, sep, value = body.partition("=")
        if sep == "":
            continue
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
            value = value[1:-1]
        values[key.strip()] = value
    return values


def render_text(template: str, mapping: dict[str, str]) -> str:
    output = template
    for key, value in mapping.items():
        output = output.replace(key, value)
    return output


def backup_file(path: Path) -> Path | None:
    if not path.exists():
        return None
    backup = path.with_name(f"{path.name}.bak.claw-native-{now_stamp()}")
    backup.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(path, backup)
    return backup


def ensure_text_file(path: Path, content: str, *, mode: int | None = None) -> tuple[bool, Path | None]:
    path.parent.mkdir(parents=True, exist_ok=True)
    existing = path.read_text(encoding="utf-8") if path.exists() else None
    if existing == content:
        if mode is not None and path.exists():
            path.chmod(mode)
        return False, None

    backup = backup_file(path)
    path.write_text(content, encoding="utf-8")
    if mode is not None:
        path.chmod(mode)
    return True, backup


def union_list(existing: list[Any], desired: list[Any]) -> list[Any]:
    seen: set[Any] = set()
    merged: list[Any] = []
    for value in [*existing, *desired]:
        marker = json.dumps(value, ensure_ascii=False, sort_keys=True) if isinstance(value, (dict, list)) else value
        if marker in seen:
            continue
        seen.add(marker)
        merged.append(value)
    return merged


def materialize_openclaw_config(existing: dict[str, Any], desired: dict[str, Any]) -> dict[str, Any]:
    payload = json.loads(json.dumps(existing))

    agents = payload.setdefault("agents", {})
    defaults = agents.setdefault("defaults", {})
    desired_defaults = desired["agents"]["defaults"]
    defaults["workspace"] = desired_defaults["workspace"]
    if "model" in desired_defaults:
        defaults["model"] = desired_defaults["model"]
    defaults["heartbeat"] = desired_defaults["heartbeat"]
    defaults["memorySearch"] = desired_defaults["memorySearch"]
    defaults["sandbox"] = desired_defaults["sandbox"]
    defaults["userTimezone"] = desired_defaults["userTimezone"]
    defaults["timeFormat"] = desired_defaults["timeFormat"]

    gateway = payload.setdefault("gateway", {})
    desired_gateway = desired["gateway"]
    gateway["mode"] = desired_gateway["mode"]
    gateway_auth = gateway.setdefault("auth", {})
    gateway_auth.update(desired_gateway["auth"])

    plugins = payload.setdefault("plugins", {})
    desired_plugins = desired["plugins"]
    plugins["allow"] = union_list(plugins.get("allow", []), desired_plugins.get("allow", []))

    load = plugins.setdefault("load", {})
    load["paths"] = union_list(load.get("paths", []), desired_plugins.get("load", {}).get("paths", []))

    entries = plugins.setdefault("entries", {})
    for key, value in desired_plugins.get("entries", {}).items():
        entries[key] = value

    return payload


def resolve_timezone(existing_cfg: dict[str, Any], args: argparse.Namespace) -> str:
    if args.timezone:
        return args.timezone
    value = existing_cfg.get("agents", {}).get("defaults", {}).get("userTimezone")
    if isinstance(value, str) and value.strip():
        return value.strip()
    return os.environ.get("TZ", "UTC")


def resolve_gateway_token(existing_cfg: dict[str, Any], args: argparse.Namespace) -> str:
    if args.gateway_token:
        return args.gateway_token
    value = existing_cfg.get("gateway", {}).get("auth", {}).get("token")
    if isinstance(value, str) and value.strip():
        return value.strip()
    env_value = os.environ.get("OPENCLAW_GATEWAY_TOKEN")
    if env_value:
        return env_value
    return secrets.token_hex(24)


def resolve_bridge_token(existing_cfg: dict[str, Any], bridge_env: dict[str, str], args: argparse.Namespace) -> str:
    if args.bridge_token:
        return args.bridge_token
    env_value = os.environ.get("MIRA_LIGHT_BRIDGE_TOKEN")
    if env_value:
        return env_value
    env_file_value = bridge_env.get("MIRA_LIGHT_BRIDGE_TOKEN")
    if env_file_value:
        return env_file_value
    value = (
        existing_cfg.get("plugins", {})
        .get("entries", {})
        .get("mira-light-bridge", {})
        .get("config", {})
        .get("bridgeToken")
    )
    if isinstance(value, str) and value.strip():
        return value.strip()
    return secrets.token_hex(24)


def resolve_lamp_base_url(bridge_env: dict[str, str], vision_env: dict[str, str], args: argparse.Namespace) -> str:
    if args.lamp_base_url:
        return args.lamp_base_url
    env_value = os.environ.get("MIRA_LIGHT_BASE_URL")
    if env_value:
        return env_value
    for values in (bridge_env, vision_env):
        current = values.get("MIRA_LIGHT_BASE_URL")
        if current:
            return current
    if DEFAULT_BRIDGE_CONFIG.exists():
        config = load_json(DEFAULT_BRIDGE_CONFIG)
        value = config.get("lampBaseUrl")
        if isinstance(value, str) and value.strip():
            return value.strip()
    return "tcp://192.168.31.10:9527"


def collect_workspace_files() -> list[Path]:
    return sorted(path for path in WORKSPACE_TEMPLATES_ROOT.rglob("*") if path.is_file())


def ensure_launch_agent(label: str, plist_path: Path) -> tuple[int, str]:
    uid = str(os.getuid())
    code, _ = run(["launchctl", "print", f"gui/{uid}/{label}"])
    if code == 0:
        return run(["launchctl", "kickstart", "-k", f"gui/{uid}/{label}"])
    return run(["launchctl", "bootstrap", f"gui/{uid}", str(plist_path)])


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Materialize Claw-Native templates into the local machine.")
    parser.add_argument("--state-dir", default=str(DEFAULT_STATE_DIR), help="Target OpenClaw state dir")
    parser.add_argument("--local-bin-dir", default=str(DEFAULT_LOCAL_BIN_DIR), help="Target local bin dir")
    parser.add_argument("--launch-agents-dir", default=str(DEFAULT_LAUNCH_AGENTS_DIR), help="Target LaunchAgents dir")
    parser.add_argument("--timezone", help="Override user timezone placeholder")
    parser.add_argument("--gateway-token", help="Override gateway auth token")
    parser.add_argument("--bridge-token", help="Override bridge token")
    parser.add_argument("--lamp-base-url", help="Override lamp base URL")
    parser.add_argument("--write", action="store_true", help="Write files instead of dry-run")
    parser.add_argument("--skip-gateway-install", action="store_true", help="Do not run openclaw gateway install")
    parser.add_argument("--skip-setup-venv", action="store_true", help="Do not run the service venv setup script")
    parser.add_argument("--skip-sync-service", action="store_true", help="Do not sync the local service copy")
    parser.add_argument("--skip-launchd", action="store_true", help="Do not bootstrap or kickstart launch agents")
    parser.add_argument("--skip-memory-index", action="store_true", help="Do not rebuild OpenClaw memory")
    parser.add_argument("--skip-verify", action="store_true", help="Do not run the verification script")
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    state_dir = Path(args.state_dir).expanduser().resolve()
    local_bin_dir = Path(args.local_bin_dir).expanduser().resolve()
    launch_agents_dir = Path(args.launch_agents_dir).expanduser().resolve()
    config_path = state_dir / "openclaw.json"
    workspace_dir = state_dir / "workspace"
    bridge_env_path = state_dir / "mira-light-bridge.env"
    vision_env_path = state_dir / "mira-light-vision.env"
    bridge_wrapper_path = local_bin_dir / "mira-light-bridge"
    vision_wrapper_path = local_bin_dir / "mira-light-vision"
    bridge_plist_path = launch_agents_dir / "ai.mira-light.bridge.plist"
    vision_plist_path = launch_agents_dir / "ai.mira-light.vision.plist"

    existing_cfg = load_json(config_path) if config_path.exists() else {}
    current_bridge_env = load_shell_exports(bridge_env_path)
    current_vision_env = load_shell_exports(vision_env_path)

    timezone = resolve_timezone(existing_cfg, args)
    gateway_token = resolve_gateway_token(existing_cfg, args)
    bridge_token = resolve_bridge_token(existing_cfg, current_bridge_env, args)
    lamp_base_url = resolve_lamp_base_url(current_bridge_env, current_vision_env, args)

    mapping = {
        "__HOME__": str(Path.home()),
        "__REPO_ROOT__": str(REPO_ROOT),
        "__TIMEZONE__": timezone,
        "__GATEWAY_TOKEN__": gateway_token,
        "__BRIDGE_TOKEN__": bridge_token,
        "__LAMP_BASE_URL__": lamp_base_url,
    }

    rendered_openclaw = json.loads(render_text((TEMPLATES_ROOT / "openclaw.template.jsonc").read_text(encoding="utf-8"), mapping))
    final_openclaw = materialize_openclaw_config(existing_cfg, rendered_openclaw)

    plan: list[str] = []
    plan.append(f"state_dir={state_dir}")
    plan.append(f"repo_root={REPO_ROOT}")
    plan.append(f"timezone={timezone}")
    plan.append(f"lamp_base_url={lamp_base_url}")
    plan.append(f"workspace_files={len(collect_workspace_files())}")

    if not args.write:
        print("[dry-run] Claw-Native materialization plan:")
        for line in plan:
            print(f"- {line}")
        print(f"- gateway_token={gateway_token[:8]}... (redacted)")
        print(f"- bridge_token={bridge_token[:8]}... (redacted)")
        print(f"- openclaw_config_target={config_path}")
        print(f"- bridge_wrapper_target={bridge_wrapper_path}")
        print(f"- vision_wrapper_target={vision_wrapper_path}")
        print(f"- bridge_plist_target={bridge_plist_path}")
        print(f"- vision_plist_target={vision_plist_path}")
        return 0

    print("[apply] Writing Claw-Native local files")
    changed, backup = ensure_text_file(
        config_path,
        json.dumps(final_openclaw, ensure_ascii=False, indent=2) + "\n",
        mode=0o600,
    )
    print(f"- openclaw.json changed={changed} backup={backup}")

    rendered_bridge_env = render_text((TEMPLATES_ROOT / "mira-light-bridge.env.example").read_text(encoding="utf-8"), mapping) + "\n"
    changed, backup = ensure_text_file(bridge_env_path, rendered_bridge_env, mode=0o600)
    print(f"- bridge env changed={changed} backup={backup}")

    rendered_vision_env = render_text((TEMPLATES_ROOT / "mira-light-vision.env.example").read_text(encoding="utf-8"), mapping) + "\n"
    changed, backup = ensure_text_file(vision_env_path, rendered_vision_env, mode=0o600)
    print(f"- vision env changed={changed} backup={backup}")

    for source in collect_workspace_files():
        relative = source.relative_to(WORKSPACE_TEMPLATES_ROOT)
        target = workspace_dir / relative
        rendered = render_text(source.read_text(encoding="utf-8"), mapping)
        changed, _ = ensure_text_file(target, rendered + ("" if rendered.endswith("\n") else "\n"))
        print(f"- workspace file {relative} changed={changed}")

    rendered_bridge_wrapper = render_text((TEMPLATES_ROOT / "mira-light-bridge-wrapper.sh").read_text(encoding="utf-8"), mapping) + "\n"
    changed, backup = ensure_text_file(bridge_wrapper_path, rendered_bridge_wrapper, mode=0o755)
    print(f"- bridge wrapper changed={changed} backup={backup}")

    rendered_vision_wrapper = render_text((TEMPLATES_ROOT / "mira-light-vision-wrapper.sh").read_text(encoding="utf-8"), mapping) + "\n"
    changed, backup = ensure_text_file(vision_wrapper_path, rendered_vision_wrapper, mode=0o755)
    print(f"- vision wrapper changed={changed} backup={backup}")

    rendered_bridge_plist = render_text((TEMPLATES_ROOT / "launchd" / "ai.mira-light.bridge.plist.example").read_text(encoding="utf-8"), mapping) + "\n"
    changed, backup = ensure_text_file(bridge_plist_path, rendered_bridge_plist, mode=0o644)
    print(f"- bridge plist changed={changed} backup={backup}")

    rendered_vision_plist = render_text((TEMPLATES_ROOT / "launchd" / "ai.mira-light.vision.plist.example").read_text(encoding="utf-8"), mapping) + "\n"
    changed, backup = ensure_text_file(vision_plist_path, rendered_vision_plist, mode=0o644)
    print(f"- vision plist changed={changed} backup={backup}")

    if not args.skip_gateway_install:
        code, output = run(["openclaw", "gateway", "install", "--force", "--json"], cwd=REPO_ROOT)
        print(f"[openclaw gateway install exit={code}]")
        print(output[:2000].rstrip())
        if code != 0:
            return code

    if not args.skip_setup_venv:
        code, output = run(["bash", str(REPO_ROOT / "scripts" / "setup_local_mira_light_service_env.sh")], cwd=REPO_ROOT)
        print(f"[setup service venv exit={code}]")
        print(output[:2000].rstrip())
        if code != 0:
            return code

    if not args.skip_sync_service:
        code, output = run(["python3", str(REPO_ROOT / "scripts" / "sync_local_mira_light_service.py")], cwd=REPO_ROOT)
        print(f"[sync service exit={code}]")
        print(output[:3000].rstrip())
        if code != 0:
            return code

    if not args.skip_launchd:
        for label, plist_path in [
            ("ai.mira-light.bridge", bridge_plist_path),
            ("ai.mira-light.vision", vision_plist_path),
        ]:
            code, output = ensure_launch_agent(label, plist_path)
            print(f"[launchd {label} exit={code}]")
            print(output[:2000].rstrip())
            if code != 0:
                return code

    if not args.skip_memory_index:
        code, output = run(["openclaw", "memory", "index"], cwd=REPO_ROOT)
        print(f"[openclaw memory index exit={code}]")
        print(output[:3000].rstrip())
        if code != 0:
            return code

    if not args.skip_verify:
        code, output = run(
            [
                "python3",
                str(REPO_ROOT / "scripts" / "verify_local_openclaw_mira_light.py"),
                "--bridge-token",
                bridge_token,
            ],
            cwd=REPO_ROOT,
        )
        print(f"[verify exit={code}]")
        print(output[:6000].rstrip())
        if code != 0:
            return code

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
