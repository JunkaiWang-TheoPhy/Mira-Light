#!/usr/bin/env python3
"""Calibration helper for Mira Light.

This tool is intentionally practical rather than elegant:

- inspect current lamp status
- jog one servo at a time
- move a servo to an absolute angle
- apply a named pose
- capture the current hardware pose into a local profile file

The profile file is then loaded by `scripts/scenes.py` through
`MIRA_LIGHT_PROFILE_PATH` or the default local path.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict

from mira_light_runtime import DEFAULT_TIMEOUT_SECONDS, MiraLightClient
from scenes import DEFAULT_PROFILE_PATH, POSES, PROFILE_INFO, SERVO_CALIBRATION


def load_profile(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {"servoCalibration": {}, "poses": {}}

    raw = path.read_text(encoding="utf-8").strip()
    if not raw:
        return {"servoCalibration": {}, "poses": {}}
    parsed = json.loads(raw)
    if not isinstance(parsed, dict):
        raise ValueError(f"Invalid profile file: {path}")
    parsed.setdefault("servoCalibration", {})
    parsed.setdefault("poses", {})
    return parsed


def save_profile(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def status_to_angles(status_payload: dict[str, Any]) -> dict[str, int]:
    servos = status_payload.get("servos", [])
    result: dict[str, int] = {}
    for item in servos:
        name = item.get("name")
        angle = item.get("angle")
        if isinstance(name, str) and isinstance(angle, int | float):
            result[name] = int(angle)
    return result


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Calibrate Mira Light servo ranges and poses.")
    parser.add_argument("--base-url", default="http://172.20.10.3", help="Lamp base URL")
    parser.add_argument("--profile-path", default=str(DEFAULT_PROFILE_PATH), help="Local calibration profile path")
    parser.add_argument("--dry-run", action="store_true", help="Do not send real device requests")

    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("status", help="Read current /status")
    subparsers.add_parser("actions", help="Read current /actions")
    subparsers.add_parser("show-profile", help="Print current effective profile metadata")
    subparsers.add_parser("list-poses", help="List currently known poses")

    move = subparsers.add_parser("move", help="Move one or more servos")
    move.add_argument("--mode", choices=["absolute", "relative"], required=True)
    move.add_argument("--servo1", type=int)
    move.add_argument("--servo2", type=int)
    move.add_argument("--servo3", type=int)
    move.add_argument("--servo4", type=int)

    set_led = subparsers.add_parser("set-led", help="Set LED mode for rehearsal")
    set_led.add_argument("--mode", required=True)
    set_led.add_argument("--brightness", type=int)
    set_led.add_argument("--r", type=int)
    set_led.add_argument("--g", type=int)
    set_led.add_argument("--b", type=int)

    apply_pose = subparsers.add_parser("apply-pose", help="Apply a known pose")
    apply_pose.add_argument("name", help="Pose name")

    capture_pose = subparsers.add_parser("capture-pose", help="Capture current /status into a named pose")
    capture_pose.add_argument("name", help="Pose name to save")
    capture_pose.add_argument("--notes", default="", help="Optional note saved with the pose")
    capture_pose.add_argument("--verified", action="store_true", help="Mark captured pose as verified")

    set_servo_meta = subparsers.add_parser("set-servo-meta", help="Update local metadata for one servo")
    set_servo_meta.add_argument("servo", choices=list(SERVO_CALIBRATION.keys()))
    set_servo_meta.add_argument("--label")
    set_servo_meta.add_argument("--neutral", type=int)
    set_servo_meta.add_argument("--hard-min", type=int)
    set_servo_meta.add_argument("--hard-max", type=int)
    set_servo_meta.add_argument("--rehearsal-min", type=int)
    set_servo_meta.add_argument("--rehearsal-max", type=int)
    set_servo_meta.add_argument("--notes")
    set_servo_meta.add_argument("--verified", action="store_true")

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    client = MiraLightClient(base_url=args.base_url, timeout_seconds=DEFAULT_TIMEOUT_SECONDS, dry_run=args.dry_run)
    profile_path = Path(args.profile_path)

    if args.command == "status":
        print(json.dumps(client.get_status(), ensure_ascii=False, indent=2))
        return 0

    if args.command == "actions":
        print(json.dumps(client.get_actions(), ensure_ascii=False, indent=2))
        return 0

    if args.command == "show-profile":
        payload = {
            "profileInfo": PROFILE_INFO,
            "resolvedProfilePath": str(profile_path),
            "servoCalibration": SERVO_CALIBRATION,
            "poseCount": len(POSES),
        }
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 0

    if args.command == "list-poses":
        print(json.dumps(POSES, ensure_ascii=False, indent=2))
        return 0

    if args.command == "move":
        payload = {"mode": args.mode}
        for key in ("servo1", "servo2", "servo3", "servo4"):
            value = getattr(args, key)
            if value is not None:
                payload[key] = value
        if len(payload) == 1:
            raise SystemExit("No servo values provided")
        print(json.dumps(client.control(payload), ensure_ascii=False, indent=2))
        return 0

    if args.command == "set-led":
        payload: dict[str, Any] = {"mode": args.mode}
        if args.brightness is not None:
            payload["brightness"] = args.brightness
        if args.r is not None and args.g is not None and args.b is not None:
            payload["color"] = {"r": args.r, "g": args.g, "b": args.b}
        print(json.dumps(client.set_led(payload), ensure_ascii=False, indent=2))
        return 0

    if args.command == "apply-pose":
        if args.name not in POSES:
            raise SystemExit(f"Unknown pose: {args.name}")
        payload = {"mode": "absolute", **POSES[args.name]["angles"]}
        print(json.dumps(client.control(payload), ensure_ascii=False, indent=2))
        return 0

    if args.command == "capture-pose":
        profile = load_profile(profile_path)
        status_payload = client.get_status()
        angles = status_to_angles(status_payload)
        if not angles:
            raise SystemExit("Could not extract servo angles from /status")

        profile["poses"][args.name] = {
            "verified": bool(args.verified),
            "angles": angles,
            "notes": args.notes or f"Captured from lamp status at {args.base_url}",
        }
        save_profile(profile_path, profile)
        print(json.dumps({"saved": args.name, "path": str(profile_path), "angles": angles}, ensure_ascii=False, indent=2))
        return 0

    if args.command == "set-servo-meta":
        profile = load_profile(profile_path)
        current = dict(profile["servoCalibration"].get(args.servo, {}))

        if args.label:
            current["label"] = args.label
        if args.neutral is not None:
            current["neutral"] = args.neutral
        if args.hard_min is not None or args.hard_max is not None:
            hard_min = args.hard_min if args.hard_min is not None else current.get("hard_range", [0, 180])[0]
            hard_max = args.hard_max if args.hard_max is not None else current.get("hard_range", [0, 180])[1]
            current["hard_range"] = [hard_min, hard_max]
        if args.rehearsal_min is not None or args.rehearsal_max is not None:
            existing = current.get("rehearsal_range", [0, 180])
            rehearsal_min = args.rehearsal_min if args.rehearsal_min is not None else existing[0]
            rehearsal_max = args.rehearsal_max if args.rehearsal_max is not None else existing[1]
            current["rehearsal_range"] = [rehearsal_min, rehearsal_max]
        if args.notes is not None:
            current["notes"] = args.notes
        if args.verified:
            current["verified"] = True

        profile["servoCalibration"][args.servo] = current
        save_profile(profile_path, profile)
        print(json.dumps({"saved": args.servo, "path": str(profile_path), "value": current}, ensure_ascii=False, indent=2))
        return 0

    parser.print_help()
    return 1


if __name__ == "__main__":
    raise SystemExit(main())

