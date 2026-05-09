#!/usr/bin/env python3

from __future__ import annotations

from common import RemoteStep, build_parser, exit_from_plan


def led(command: str) -> str:
    return f"python3 /home/sunrise/Desktop/send_uart3_led_cmd.py {command}"


def build_steps(*, breathe_seconds: float, spin_seconds: float) -> list[RemoteStep]:
    breathe_hold = max(0.0, breathe_seconds)
    spin_hold = max(0.0, spin_seconds)
    return [
        RemoteStep("light-only safety note", "echo '[light only] right-hand nuzzle light, no servo motion commands'"),
        RemoteStep("D warm palm light", led("breathe 255 128 48 145")),
        RemoteStep("D warm palm light hold", f"sleep {breathe_hold:.2f}"),
        RemoteStep("D stage 2 warm palm rotation", led("spin 255 145 48 0 1 155")),
        RemoteStep("D stage 2 rotation hold", f"sleep {spin_hold:.2f}"),
    ]


def main() -> None:
    parser = build_parser("Light-only test for right-hand nuzzle D-stage lighting.")
    parser.add_argument("--breathe-seconds", type=float, default=0.2)
    parser.add_argument("--spin-seconds", type=float, default=0.6)
    args = parser.parse_args()
    exit_from_plan(args=args, steps=build_steps(breathe_seconds=args.breathe_seconds, spin_seconds=args.spin_seconds))


if __name__ == "__main__":
    main()
