#!/usr/bin/env python3

from __future__ import annotations

from common import RemoteStep, build_parser, exit_from_plan


def build_steps(*, light_style: str, bounce_twice: bool) -> list[RemoteStep]:
    bright_cmd = (
        "python3 /home/sunrise/Desktop/send_uart3_led_cmd.py rainbow 150"
        if light_style == "rainbow"
        else "python3 /home/sunrise/Desktop/send_uart3_led_cmd.py all 255 220 180 140"
    )
    steps: list[RemoteStep] = [
        RemoteStep(
            "enter neutral start pose",
            "python3 /home/sunrise/Desktop/four_servo_control.py pose 2048 2150 2048 2130 --speeds 200 100 100 200",
        ),
        RemoteStep("brighten into happy state", bright_cmd),
        RemoteStep("look upward", "python3 /home/sunrise/Desktop/servo_12_slow_to_1800_2750.py"),
        RemoteStep("light happy sway", "python3 /home/sunrise/Desktop/servo_3_shake_2100_2000.py --cycles 1 --pause 0.06"),
        RemoteStep("gentle body bounce", "python3 /home/sunrise/Desktop/servo_1_2_lean_forward_2148_1848.py"),
    ]
    if bounce_twice:
        steps.append(
            RemoteStep(
                "second gentle bounce",
                "python3 /home/sunrise/Desktop/servo_1_2_lean_forward_2148_1848.py",
            )
        )
    steps.extend(
        [
            RemoteStep(
                "return to waiting pose",
                "python3 /home/sunrise/Desktop/four_servo_control.py pose 2048 2150 2048 2130 --speeds 180 100 100 180",
            ),
            RemoteStep("settle to natural warm light", "python3 /home/sunrise/Desktop/send_uart3_led_cmd.py all 255 220 180 100"),
        ]
    )
    return steps


def main() -> None:
    parser = build_parser("Fixed demo script for Videos/08 + PDF copy supplemental happy reaction.")
    parser.add_argument("--light-style", choices=("warm", "rainbow"), default="warm")
    parser.add_argument("--bounce-twice", action="store_true")
    args = parser.parse_args()
    exit_from_plan(args=args, steps=build_steps(light_style=args.light_style, bounce_twice=args.bounce_twice))


if __name__ == "__main__":
    main()
