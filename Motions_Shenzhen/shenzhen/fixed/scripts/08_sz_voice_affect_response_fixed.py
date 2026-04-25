#!/usr/bin/env python3

from __future__ import annotations

import argparse

from common import RemoteStep, build_common_parser, exit_from_run, maybe_run


def build_steps(intent: str) -> list[RemoteStep]:
    if intent == "tired":
        return [
            RemoteStep("warm comfort light", "python3 /home/sunrise/Desktop/send_uart3_led_cmd.py breathe 255 190 120 110"),
            RemoteStep("soft low nod", "python3 /home/sunrise/Desktop/servo_2_nod_1900_2200.py --cycles 1 --pause 0.1"),
            RemoteStep("hold gentle response", "sleep 0.8"),
        ]
    if intent == "praise":
        return [
            RemoteStep("bright happy light", "python3 /home/sunrise/Desktop/send_uart3_led_cmd.py all 255 220 180 150"),
            RemoteStep("happy nod", "python3 /home/sunrise/Desktop/servo_2_nod_1900_2200.py --cycles 1 --pause 0.05"),
            RemoteStep("small excited shake", "python3 /home/sunrise/Desktop/servo_3_shake_2100_2000.py --cycles 1 --pause 0.05"),
        ]
    return [
        RemoteStep("dimmer withdrawn light", "python3 /home/sunrise/Desktop/send_uart3_led_cmd.py all 255 170 140 70"),
        RemoteStep("small dodge away", "python3 /home/sunrise/Desktop/servo_1_2_dodge_1848_1808.py"),
        RemoteStep("small no-like shake", "python3 /home/sunrise/Desktop/servo_3_shake_2100_2000.py --cycles 1 --pause 0.08"),
    ]


def main() -> None:
    parser = build_common_parser("Fixed Shenzhen scene: voice affect response.")
    parser.add_argument("--intent", choices=("tired", "praise", "criticism"), default="tired")
    args = parser.parse_args()
    steps = build_steps(args.intent)
    steps.extend(
        [
            RemoteStep(
                "return to waiting pose",
                "python3 /home/sunrise/Desktop/four_servo_control.py pose 2048 2150 2048 2130 --speeds 200 100 100 200",
            ),
            RemoteStep("neutral warm light", "python3 /home/sunrise/Desktop/send_uart3_led_cmd.py all 255 220 180 100"),
        ]
    )
    exit_from_run(args=args, steps=steps)


if __name__ == "__main__":
    main()
