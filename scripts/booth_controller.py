#!/usr/bin/env python3
"""Minimal booth controller for Mira Light.

This controller is intentionally a skeleton:

- It already knows how to call the existing ESP32 REST API.
- It can run a scene step-by-step from `scripts/scenes.py`.
- It keeps unknown parts as TODO comments instead of pretending they are done.

Why this shape:
- We already know the device can handle `/control`, `/led`, `/action`, `/reset`.
- We do NOT yet have finalized implementations for vision, touch, voice, or audio.
- So the safest next step is a "director script" that can drive the lamp manually,
  while leaving sensor-dependent features as explicit placeholders.

Current trigger model:
- Option A: run this file directly from the terminal
- Option B: let OpenClaw call the same terminal command

We intentionally do NOT assume:
- physical keyboard hotkeys
- dedicated booth buttons
- a finished web control panel
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.request
from typing import Any, Dict

from scenes import SCENES


DEFAULT_BASE_URL = os.environ.get("MIRA_LIGHT_BASE_URL", "http://172.20.10.3").rstrip("/")
DEFAULT_TIMEOUT_SECONDS = float(os.environ.get("MIRA_LIGHT_TIMEOUT_SECONDS", "3"))


class MiraLightClient:
    """Thin HTTP client around the current ESP32 REST API."""

    def __init__(self, base_url: str, timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS, dry_run: bool = False):
        self.base_url = base_url.rstrip("/")
        self.timeout_seconds = timeout_seconds
        self.dry_run = dry_run

    def _request(self, method: str, path: str, payload: Dict[str, Any] | None = None) -> Any:
        url = f"{self.base_url}{path}"

        if self.dry_run:
            print(f"[dry-run] {method} {url}")
            if payload is not None:
                print(json.dumps(payload, ensure_ascii=False, indent=2))
            return {"dry_run": True, "method": method, "url": url, "payload": payload}

        data = None
        headers = {}
        if payload is not None:
            data = json.dumps(payload).encode("utf-8")
            headers["Content-Type"] = "application/json"

        req = urllib.request.Request(url, data=data, headers=headers, method=method)
        try:
            with urllib.request.urlopen(req, timeout=self.timeout_seconds) as response:
                body = response.read().decode("utf-8").strip()
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace").strip()
            raise RuntimeError(f"HTTP {exc.code} calling {path}: {detail}") from exc
        except urllib.error.URLError as exc:
            raise RuntimeError(f"Failed to reach Mira Light at {url}: {exc}") from exc

        if not body:
            return {}

        try:
            return json.loads(body)
        except json.JSONDecodeError:
            return body

    def get_status(self) -> Any:
        return self._request("GET", "/status")

    def get_led(self) -> Any:
        return self._request("GET", "/led")

    def get_actions(self) -> Any:
        return self._request("GET", "/actions")

    def set_led(self, payload: Dict[str, Any]) -> Any:
        return self._request("POST", "/led", payload)

    def control(self, payload: Dict[str, Any]) -> Any:
        return self._request("POST", "/control", payload)

    def run_action(self, payload: Dict[str, Any]) -> Any:
        return self._request("POST", "/action", payload)

    def stop_action(self) -> Any:
        return self._request("POST", "/action/stop")

    def reset(self) -> Any:
        return self._request("POST", "/reset")


class BoothController:
    """Runs scene steps one by one.

    The controller only implements primitives we can honestly support now.
    Anything sensor-heavy or system-heavy is left as an explicit TODO step.
    """

    def __init__(self, client: MiraLightClient):
        self.client = client

    def run_scene(self, scene_name: str) -> None:
        if scene_name not in SCENES:
            raise KeyError(f"Unknown scene: {scene_name}")

        scene = SCENES[scene_name]
        print(f"\n=== Scene: {scene_name} / {scene['title']} ===")

        host_line = scene.get("host_line")
        if host_line:
            print(f"[host] {host_line}")

        for note in scene.get("notes", []):
            print(f"[note] {note}")

        for step in scene.get("steps", []):
            self.run_step(step)

    def run_step(self, step: Dict[str, Any]) -> None:
        step_type = step["type"]

        if step_type == "comment":
            print(f"[comment] {step['text']}")
            return

        if step_type == "delay":
            ms = int(step["ms"])
            print(f"[delay] {ms}ms")
            if not self.client.dry_run:
                time.sleep(ms / 1000)
            return

        if step_type == "led":
            print("[led]")
            self.client.set_led(step["payload"])
            return

        if step_type == "control":
            print("[control]")
            self.client.control(step["payload"])
            return

        if step_type == "action":
            print("[action]")
            self.client.run_action(step["payload"])
            return

        if step_type == "action_stop":
            print("[action_stop]")
            self.client.stop_action()
            return

        if step_type == "reset":
            print("[reset]")
            self.client.reset()
            return

        if step_type == "status":
            print("[status]")
            result = self.client.get_status()
            print(json.dumps(result, ensure_ascii=False, indent=2))
            return

        if step_type == "audio":
            # TODO:
            # We do not know yet whether audio will be played by:
            # - local laptop media player
            # - Bluetooth speaker integration
            # - a dedicated booth control app
            #
            # So for now we keep this as a visible placeholder.
            print(f"[todo-audio] play audio asset: {step['name']}")
            return

        if step_type == "sensor_gate":
            # TODO:
            # Future place for gating scene steps behind real sensor conditions,
            # such as person_detected_near, hand_near, tracked_object_ready, etc.
            print(f"[todo-sensor] wait for sensor condition: {step['name']}")
            return

        raise ValueError(f"Unsupported step type: {step_type}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run a Mira Light booth scene.",
        epilog=(
            "Examples:\n"
            "  python3 scripts/booth_controller.py --list\n"
            "  python3 scripts/booth_controller.py --base-url http://172.20.10.3 wake_up\n"
            "  python3 scripts/booth_controller.py --base-url http://172.20.10.3 celebrate\n"
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
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    client = MiraLightClient(base_url=args.base_url, dry_run=args.dry_run)

    if args.list:
        print("Available scenes:")
        for key, scene in SCENES.items():
            print(f"- {key}: {scene['title']}")
        return 0

    if args.status:
        print(json.dumps(client.get_status(), ensure_ascii=False, indent=2))
        return 0

    if args.led_status:
        print(json.dumps(client.get_led(), ensure_ascii=False, indent=2))
        return 0

    if args.actions:
        print(json.dumps(client.get_actions(), ensure_ascii=False, indent=2))
        return 0

    if not args.scene:
        parser.print_help()
        return 1

    controller = BoothController(client)
    controller.run_scene(args.scene)
    return 0


if __name__ == "__main__":
    sys.exit(main())
