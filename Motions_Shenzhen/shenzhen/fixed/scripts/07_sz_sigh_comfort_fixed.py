#!/usr/bin/env python3

from __future__ import annotations

from common import RemoteStep, build_common_parser, exit_from_run


def build_steps() -> list[RemoteStep]:
    return [
        RemoteStep("warm comfort light", "python3 /home/sunrise/Desktop/send_uart3_led_cmd.py breathe 255 190 120 110"),
        RemoteStep("turn slightly toward speaker", "python3 /home/sunrise/Desktop/servo_1_3_slow_1800_2750.py --delay-ratio 0 --speed 100"),
        RemoteStep("gentle low nod", "python3 /home/sunrise/Desktop/servo_2_nod_1900_2200.py --cycles 1 --pause 0.1"),
        RemoteStep("hold comfort", "sleep 1.0"),
        RemoteStep(
            "return to waiting pose",
            "python3 /home/sunrise/Desktop/four_servo_control.py pose 2048 2150 2048 2130 --speeds 200 100 100 200",
        ),
        RemoteStep("natural warm light", "python3 /home/sunrise/Desktop/send_uart3_led_cmd.py all 255 220 180 100"),
    ]


def main() -> None:
    parser = build_common_parser("Fixed Shenzhen scene: sigh comfort.")
    args = parser.parse_args()
    exit_from_run(args=args, steps=build_steps())


if __name__ == "__main__":
    main()
