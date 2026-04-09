#!/usr/bin/env python3
"""CLI wrapper around the reusable Mira Light bridge client."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

try:
    from .bridge_client import MiraLightBridgeClient
except ImportError:  # pragma: no cover
    from bridge_client import MiraLightBridgeClient


def _parse_json_arg(raw: str | None) -> dict:
    if not raw:
        return {}
    parsed = json.loads(raw)
    if not isinstance(parsed, dict):
        raise ValueError("JSON payload must be an object")
    return parsed


def _parse_json_file(path: str | None) -> dict:
    if not path:
        return {}
    parsed = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(parsed, dict):
        raise ValueError("JSON file payload must be an object")
    return parsed


def _load_object(json_arg: str | None, json_file: str | None) -> dict:
    if json_arg and json_file:
        raise ValueError("Provide either --json or --json-file, not both")
    if json_file:
        return _parse_json_file(json_file)
    return _parse_json_arg(json_arg)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Call the Mira Light bridge from Python.")
    parser.add_argument("--base-url", default=None, help="Bridge base URL, defaults to env or http://127.0.0.1:9783")
    parser.add_argument("--token", default=None, help="Bridge bearer token, defaults to env")
    parser.add_argument("--timeout", type=float, default=None, help="HTTP timeout seconds")

    subparsers = parser.add_subparsers(dest="command", required=True)

    for name in ("health", "status", "led-status", "actions", "runtime", "logs", "scenes", "profile", "storage-info"):
        subparsers.add_parser(name)

    run_scene = subparsers.add_parser("run-scene")
    run_scene.add_argument("scene")
    run_scene.add_argument("--sync", action="store_true", help="Run blocking instead of async")
    run_scene.add_argument("--cue-mode")
    run_scene.add_argument("--allow-unavailable", action="store_true")
    run_scene.add_argument("--context-json")
    run_scene.add_argument("--context-file")

    trigger = subparsers.add_parser("trigger")
    trigger.add_argument("event")
    trigger.add_argument("--payload-json")
    trigger.add_argument("--payload-file")

    speak = subparsers.add_parser("speak")
    speak.add_argument("text")
    speak.add_argument("--voice")
    speak.add_argument("--wait", action="store_true")

    apply_pose = subparsers.add_parser("apply-pose")
    apply_pose.add_argument("pose")

    for name in ("stop", "reset", "stop-to-neutral", "stop-to-sleep"):
        subparsers.add_parser(name)

    control = subparsers.add_parser("control")
    control.add_argument("--mode", required=True, choices=["absolute", "relative"])
    control.add_argument("--servo1", type=int)
    control.add_argument("--servo2", type=int)
    control.add_argument("--servo3", type=int)
    control.add_argument("--servo4", type=int)

    led = subparsers.add_parser("set-led")
    led.add_argument("--mode", required=True)
    led.add_argument("--brightness", type=int)
    led.add_argument("--color-json")
    led.add_argument("--pixels-json")

    action = subparsers.add_parser("action")
    action.add_argument("name")
    action.add_argument("--loops", type=int, default=1)

    config = subparsers.add_parser("config")
    config.add_argument("--lamp-base-url")
    config.add_argument("--dry-run", choices=["true", "false"])
    config.add_argument("--auto-recover-pose")

    capture = subparsers.add_parser("capture-pose")
    capture.add_argument("name")
    capture.add_argument("--notes")
    capture.add_argument("--verified", action="store_true")

    servo_meta = subparsers.add_parser("set-servo-meta")
    servo_meta.add_argument("servo")
    servo_meta.add_argument("--label")
    servo_meta.add_argument("--neutral", type=int)
    servo_meta.add_argument("--hard-range-json")
    servo_meta.add_argument("--rehearsal-range-json")
    servo_meta.add_argument("--notes")
    servo_meta.add_argument("--verified", action="store_true")

    device_report = subparsers.add_parser("device-report")
    device_report.add_argument("--kind", required=True, choices=["hello", "heartbeat", "status", "event"])
    device_report.add_argument("--json")
    device_report.add_argument("--json-file")

    return parser


def make_client(args: argparse.Namespace) -> MiraLightBridgeClient:
    client = MiraLightBridgeClient.from_env()
    if args.base_url:
        client.base_url = args.base_url.rstrip("/")
    if args.token is not None:
        client.token = args.token
    if args.timeout is not None:
        client.timeout_seconds = args.timeout
    return client


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    client = make_client(args)

    if args.command == "health":
        result = client.health()
    elif args.command == "status":
        result = client.get_status()
    elif args.command == "led-status":
        result = client.get_led()
    elif args.command == "actions":
        result = client.get_actions()
    elif args.command == "runtime":
        result = client.get_runtime()
    elif args.command == "logs":
        result = client.get_logs()
    elif args.command == "scenes":
        result = client.list_scenes()
    elif args.command == "profile":
        result = client.get_profile()
    elif args.command == "storage-info":
        result = client.get_device_storage_info()
    elif args.command == "run-scene":
        context = _load_object(args.context_json, args.context_file)
        result = client.run_scene(
            args.scene,
            async_run=not args.sync,
            context=context or None,
            cue_mode=args.cue_mode,
            allow_unavailable=args.allow_unavailable or None,
        )
    elif args.command == "trigger":
        payload = _load_object(args.payload_json, args.payload_file)
        result = client.trigger(args.event, payload=payload)
    elif args.command == "speak":
        result = client.speak(args.text, voice=args.voice, wait=True if args.wait else None)
    elif args.command == "apply-pose":
        result = client.apply_pose(args.pose)
    elif args.command == "stop":
        result = client.stop()
    elif args.command == "reset":
        result = client.reset()
    elif args.command == "stop-to-neutral":
        result = client.stop_to_neutral()
    elif args.command == "stop-to-sleep":
        result = client.stop_to_sleep()
    elif args.command == "control":
        result = client.control_joints(
            mode=args.mode,
            servo1=args.servo1,
            servo2=args.servo2,
            servo3=args.servo3,
            servo4=args.servo4,
        )
    elif args.command == "set-led":
        color = _parse_json_arg(args.color_json) if args.color_json else None
        pixels = json.loads(args.pixels_json) if args.pixels_json else None
        result = client.set_led(mode=args.mode, brightness=args.brightness, color=color, pixels=pixels)
    elif args.command == "action":
        result = client.run_action(args.name, loops=args.loops)
    elif args.command == "config":
        dry_run = None
        if args.dry_run is not None:
            dry_run = args.dry_run == "true"
        result = client.update_config(
            base_url=args.lamp_base_url,
            dry_run=dry_run,
            auto_recover_pose=args.auto_recover_pose,
        )
    elif args.command == "capture-pose":
        result = client.capture_pose(args.name, notes=args.notes, verified=True if args.verified else None)
    elif args.command == "set-servo-meta":
        hard_range = json.loads(args.hard_range_json) if args.hard_range_json else None
        rehearsal_range = json.loads(args.rehearsal_range_json) if args.rehearsal_range_json else None
        result = client.set_servo_meta(
            args.servo,
            label=args.label,
            neutral=args.neutral,
            hard_range=hard_range,
            rehearsal_range=rehearsal_range,
            notes=args.notes,
            verified=True if args.verified else None,
        )
    elif args.command == "device-report":
        payload = _load_object(args.json, args.json_file)
        if args.kind == "hello":
            result = client.device_hello(payload)
        elif args.kind == "heartbeat":
            result = client.device_heartbeat(payload)
        elif args.kind == "status":
            result = client.device_status(payload)
        else:
            result = client.device_event(payload)
    else:  # pragma: no cover
        parser.error(f"unsupported command: {args.command}")
        return 2

    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
