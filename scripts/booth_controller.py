#!/usr/bin/env python3
"""Terminal entrypoint for the shared Mira Light runtime."""

from __future__ import annotations

import argparse
import json
import os
import sys
from mira_light_runtime import DEFAULT_TIMEOUT_SECONDS, MiraLightRuntime


DEFAULT_BASE_URL = os.environ.get("MIRA_LIGHT_BASE_URL", "http://172.20.10.3").rstrip("/")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run a Mira Light booth scene.",
        epilog=(
            "Examples:\n"
            "  python3 scripts/booth_controller.py --list\n"
            "  python3 scripts/booth_controller.py --base-url http://172.20.10.3 wake_up\n"
            "  python3 scripts/booth_controller.py --base-url http://172.20.10.3 celebrate\n"
            "  python3 scripts/booth_controller.py --base-url http://172.20.10.3 --reset\n"
            "  python3 scripts/booth_controller.py --base-url http://172.20.10.3 --stop\n"
            "\n"
            "Recommended OpenClaw integration:\n"
            "  Let OpenClaw execute the same terminal command instead of assuming\n"
            "  extra physical buttons or keyboard shortcuts."
        ),
        formatter_class=argparse.RawTextHelpFormatter,
    )
    parser.add_argument("scene", nargs="?", help="Scene name to run")
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL, help="Lamp base URL, e.g. http://172.20.10.3")
    parser.add_argument("--list", action="store_true", help="List available scenes")
    parser.add_argument("--dry-run", action="store_true", help="Print calls without sending them")
    parser.add_argument("--status", action="store_true", help="Print current /status before exiting")
    parser.add_argument("--led-status", action="store_true", help="Print current /led before exiting")
    parser.add_argument("--actions", action="store_true", help="Print current /actions before exiting")
    parser.add_argument("--reset", action="store_true", help="Send POST /reset and print the result")
    parser.add_argument("--stop", action="store_true", help="Send POST /action/stop and request scene stop")
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    runtime = MiraLightRuntime(
        base_url=args.base_url,
        timeout_seconds=DEFAULT_TIMEOUT_SECONDS,
        dry_run=args.dry_run,
    )

    if args.list:
        print("Available scenes:")
        for scene in runtime.list_scenes():
            print(f"- {scene['id']}: {scene['title']}")
        return 0

    if args.status:
        print(json.dumps(runtime.get_status(), ensure_ascii=False, indent=2))
        return 0

    if args.led_status:
        print(json.dumps(runtime.get_led(), ensure_ascii=False, indent=2))
        return 0

    if args.actions:
        print(json.dumps(runtime.get_actions(), ensure_ascii=False, indent=2))
        return 0

    if args.reset:
        print(json.dumps(runtime.reset_lamp(), ensure_ascii=False, indent=2))
        return 0

    if args.stop:
        print(json.dumps(runtime.stop_scene(), ensure_ascii=False, indent=2))
        return 0

    if not args.scene:
        parser.print_help()
        return 1

    runtime.run_scene_blocking(args.scene)
    return 0


if __name__ == "__main__":
    sys.exit(main())
