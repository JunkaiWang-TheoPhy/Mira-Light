#!/usr/bin/env python3

from __future__ import annotations

import argparse

from common import RemoteStep, build_common_parser, exit_from_run


def build_steps(*, light_mode: str, hold_high_seconds: float) -> list[RemoteStep]:
    wake_cmd = (
        "python3 /home/sunrise/Desktop/send_uart3_led_cmd.py wake 255 220 180 150"
        if light_mode == "wake"
        else "python3 /home/sunrise/Desktop/send_uart3_led_cmd.py all 255 220 180 90"
    )
    return [
        RemoteStep("warm wake light", wake_cmd),
        RemoteStep("pause for eye-open effect", "sleep 0.6"),
        RemoteStep("raise body in staged motion", "python3 /home/sunrise/Desktop/four_servo_pose_delay_2.py"),
        RemoteStep("hold the high point", f"sleep {hold_high_seconds:.2f}"),
        RemoteStep(
            "accent high pose",
            "python3 /home/sunrise/Desktop/four_servo_pose_2048_2048_2048_2780_separate.py --speed 250 --delay 0.05",
        ),
        RemoteStep("micro shiver down-up", "python3 /home/sunrise/Desktop/servo_2_nod_1900_2200.py --cycles 1 --pause 0.05"),
        RemoteStep("micro shiver side-side", "python3 /home/sunrise/Desktop/servo_3_shake_2100_2000.py --cycles 1 --pause 0.05"),
        RemoteStep(
            "settle to normal attention pose",
            "python3 /home/sunrise/Desktop/four_servo_control.py pose 2048 2150 2048 2130 --speeds 200 100 100 200",
        ),
        RemoteStep("natural warm light", "python3 /home/sunrise/Desktop/send_uart3_led_cmd.py all 255 220 180 100"),
    ]


def main() -> None:
    parser = build_common_parser("Fixed Shenzhen scene: presence wake.")
    parser.add_argument("--light-mode", choices=("wake", "warm"), default="wake")
    parser.add_argument("--hold-high-seconds", type=float, default=1.0)
    args = parser.parse_args()
    exit_from_run(args=args, steps=build_steps(light_mode=args.light_mode, hold_high_seconds=args.hold_high_seconds))


if __name__ == "__main__":
    main()
