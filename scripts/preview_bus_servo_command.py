#!/usr/bin/env python3
"""Preview or send Mira Light bus-servo commands to the default RDK X5 endpoint."""

from __future__ import annotations

import argparse
import json
import sys

from bus_servo_adapter import BusServoAdapter
from bus_servo_transport import BusServoTransportError, DEFAULT_RDK_X5_HOST, DEFAULT_RDK_X5_PORT


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Preview or send Mira Light bus-servo commands.",
        epilog=(
            "Examples:\n"
            "  python3 scripts/preview_bus_servo_command.py --raw '#003P1500T1000!'\n"
            "  python3 scripts/preview_bus_servo_command.py --mode absolute --servo4 90 --move-ms 1000\n"
            "  python3 scripts/preview_bus_servo_command.py --mode absolute --servo2 96 --servo4 92 --dry-run\n"
            f"\nDefault target is hardcoded to {DEFAULT_RDK_X5_HOST}:{DEFAULT_RDK_X5_PORT}.\n"
        ),
        formatter_class=argparse.RawTextHelpFormatter,
    )
    parser.add_argument("--raw", help="Send a raw bus-servo string directly")
    parser.add_argument("--mode", choices=["absolute", "relative"], help="Logical control mode")
    parser.add_argument("--servo1", type=int)
    parser.add_argument("--servo2", type=int)
    parser.add_argument("--servo3", type=int)
    parser.add_argument("--servo4", type=int)
    parser.add_argument("--move-ms", type=int)
    parser.add_argument("--sync-state-json", help="Sync known logical angles before a relative command")
    parser.add_argument("--dry-run", action="store_true", help="Format and print without touching the RDK X5")
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    adapter = BusServoAdapter.dry_run() if args.dry_run else BusServoAdapter()

    if args.sync_state_json:
        adapter.sync_angles(json.loads(args.sync_state_json))

    try:
        if args.raw:
            result = adapter.transport.send(args.raw)
            print(json.dumps(result, ensure_ascii=False, indent=2))
            return 0

        if not args.mode:
            parser.error("either --raw or --mode is required")

        payload = {"mode": args.mode}
        for name in ("servo1", "servo2", "servo3", "servo4"):
            value = getattr(args, name)
            if value is not None:
                payload[name] = value

        if len(payload) == 1:
            parser.error("at least one servo field is required")

        result = adapter.apply_control_payload(payload, move_ms=args.move_ms, source="preview-cli")
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except BusServoTransportError as exc:
        print(str(exc), file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
