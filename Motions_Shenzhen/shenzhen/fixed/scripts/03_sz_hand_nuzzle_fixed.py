#!/usr/bin/env python3

from __future__ import annotations

import argparse

from common import RemoteStep, build_common_parser, exit_from_run


def build_steps(*, light_style: str, rub_cycles: int) -> list[RemoteStep]:
    light_cmd = (
        "python3 /home/sunrise/Desktop/send_uart3_led_cmd.py breathe 255 190 120 120"
        if light_style == "breathe"
        else "python3 /home/sunrise/Desktop/send_uart3_led_cmd.py all 255 190 120 120"
    )
    steps = [
        RemoteStep("warm ready light", light_cmd),
        RemoteStep("pause before approach", "sleep 0.4"),
        RemoteStep("lean toward hand", "python3 /home/sunrise/Desktop/servo_1_2_lean_forward_2148_1848.py"),
    ]
    for idx in range(max(1, rub_cycles)):
        steps.extend(
            [
                RemoteStep(f"dip under palm rub {idx + 1}", "python3 /home/sunrise/Desktop/servo_2_nod_1900_2200.py --cycles 1 --pause 0.05"),
                RemoteStep(f"side rub {idx + 1}", "python3 /home/sunrise/Desktop/servo_3_shake_2100_2000.py --cycles 1 --pause 0.05"),
            ]
        )
    steps.extend(
        [
            RemoteStep("follow once as hand leaves", "python3 /home/sunrise/Desktop/servo_1_2_lean_forward_2148_1848.py"),
            RemoteStep(
                "return to waiting pose",
                "python3 /home/sunrise/Desktop/four_servo_control.py pose 2048 2150 2048 2130 --speeds 200 100 100 200",
            ),
            RemoteStep("natural warm light", "python3 /home/sunrise/Desktop/send_uart3_led_cmd.py all 255 220 180 100"),
        ]
    )
    return steps


def main() -> None:
    parser = build_common_parser("Fixed Shenzhen scene: hand nuzzle.")
    parser.add_argument("--light-style", choices=("all", "breathe"), default="all")
    parser.add_argument("--rub-cycles", type=int, default=2)
    args = parser.parse_args()
    exit_from_run(args=args, steps=build_steps(light_style=args.light_style, rub_cycles=args.rub_cycles))


if __name__ == "__main__":
    main()
