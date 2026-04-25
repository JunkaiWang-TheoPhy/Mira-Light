#!/usr/bin/env python3

from __future__ import annotations

from common import RemoteStep, build_parser, exit_from_plan


def build_steps(*, keep_glow: bool, lead_sleep_only: bool) -> list[RemoteStep]:
    steps: list[RemoteStep] = [
        RemoteStep(
            "enter soft end pose",
            "python3 /home/sunrise/Desktop/four_servo_control.py pose 2048 2150 2048 2130 --speeds 200 100 100 200",
        ),
        RemoteStep("soft warm pre-sleep light", "python3 /home/sunrise/Desktop/send_uart3_led_cmd.py all 255 220 180 100"),
        RemoteStep(
            "begin staged sleep fold",
            "python3 /home/sunrise/Desktop/sleep_motion.py --speeds 1000 160 680 1000 --delay-ratio 0.68",
        ),
    ]
    if not lead_sleep_only:
        steps.append(
            RemoteStep(
                "finish 0 and 3 return",
                "python3 /home/sunrise/Desktop/sleep_motion_with_03_return.py",
            )
        )
    if keep_glow:
        steps.append(
            RemoteStep(
                "dim to sleep glow",
                "python3 /home/sunrise/Desktop/send_uart3_led_cmd.py all 255 180 120 20",
            )
        )
    else:
        steps.extend(
            [
                RemoteStep(
                    "dim to low glow",
                    "python3 /home/sunrise/Desktop/send_uart3_led_cmd.py all 255 180 120 40",
                ),
                RemoteStep("lights off", "python3 /home/sunrise/Desktop/send_uart3_led_cmd.py off"),
            ]
        )
    return steps


def main() -> None:
    parser = build_parser("Fixed demo script for Videos/07 + PDF copy item 7 sleep.")
    parser.add_argument("--keep-glow", action="store_true", help="Keep a low sleep glow instead of turning fully off.")
    parser.add_argument(
        "--lead-sleep-only",
        action="store_true",
        help="Only run the first staged sleep step and skip the final 0/3 return step.",
    )
    args = parser.parse_args()
    exit_from_plan(
        args=args,
        steps=build_steps(keep_glow=args.keep_glow, lead_sleep_only=args.lead_sleep_only),
    )


if __name__ == "__main__":
    main()
