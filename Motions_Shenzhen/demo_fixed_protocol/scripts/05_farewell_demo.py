#!/usr/bin/env python3

from __future__ import annotations

from common import RemoteStep, build_parser, exit_from_plan


def build_steps(*, nod_cycles: int, linger_seconds: float) -> list[RemoteStep]:
    return [
        RemoteStep(
            "enter neutral farewell start pose",
            "python3 /home/sunrise/Desktop/four_servo_control.py pose 2048 2150 2048 2130 --speeds 200 100 100 200",
        ),
        RemoteStep("look toward departure side", "python3 /home/sunrise/Desktop/servo_1_3_slow_1800_2750.py --speed 100"),
        RemoteStep("hold the goodbye gaze", "sleep 0.6"),
        RemoteStep(
            "nod goodbye",
            f"python3 /home/sunrise/Desktop/servo_2_nod_1900_2200.py --cycles {nod_cycles} --pause 0.08",
        ),
        RemoteStep(
            "lower head reluctantly",
            "python3 /home/sunrise/Desktop/four_servo_control.py pose 2048 2050 2048 2200 --speeds 160 80 80 160",
        ),
        RemoteStep("hold reluctance", f"sleep {linger_seconds}"),
        RemoteStep(
            "look back once",
            "python3 /home/sunrise/Desktop/four_servo_control.py pose 2048 2120 2048 2160 --speeds 140 80 80 140",
        ),
        RemoteStep("settle to soft farewell light", "python3 /home/sunrise/Desktop/send_uart3_led_cmd.py all 255 220 180 90"),
    ]


def main() -> None:
    parser = build_parser("Fixed demo script for Videos/06 + PDF copy item 6 farewell.")
    parser.add_argument("--nod-cycles", type=int, default=2)
    parser.add_argument("--linger-seconds", type=float, default=0.8)
    args = parser.parse_args()
    exit_from_plan(args=args, steps=build_steps(nod_cycles=args.nod_cycles, linger_seconds=args.linger_seconds))


if __name__ == "__main__":
    main()
