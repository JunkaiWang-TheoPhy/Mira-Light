#!/usr/bin/env python3

from __future__ import annotations

from common import RemoteStep, build_parser, exit_from_plan


def build_steps(*, nod_cycles: int, linger_seconds: float) -> list[RemoteStep]:
    return [
        RemoteStep(
            "enter soft left-farewell start pose",
            "python3 /home/sunrise/Desktop/four_servo_control.py pose 2048 2140 2048 2200 --speeds 160 90 90 130",
        ),
        RemoteStep("soft farewell light", "python3 /home/sunrise/Desktop/send_uart3_led_cmd.py all 255 220 180 95"),
        RemoteStep(
            "look toward left-side departure",
            "python3 /home/sunrise/Desktop/servo_1_3_slow_1800_2750.py --target-1 2050 --target-3 2460 --speeds 100 100 --delay-ratio 0",
        ),
        RemoteStep("hold the goodbye gaze", "sleep 0.6"),
        RemoteStep(
            "small nod goodbye",
            f"python3 /home/sunrise/Desktop/servo_2_nod_1900_2200.py --cycles {nod_cycles} --low 1980 --high 2120 --return-target 2048 --pre-target 2460 --speed 110 --pause 0.08",
        ),
        RemoteStep(
            "lower head reluctantly",
            "python3 /home/sunrise/Desktop/four_servo_control.py pose 2048 2040 2100 2380 --speeds 140 75 75 110",
        ),
        RemoteStep("dim farewell light", "python3 /home/sunrise/Desktop/send_uart3_led_cmd.py all 255 210 165 70"),
        RemoteStep("hold reluctance", f"sleep {linger_seconds}"),
        RemoteStep(
            "look back left once",
            "python3 /home/sunrise/Desktop/four_servo_control.py pose 2048 2110 2048 2460 --speeds 120 80 80 100",
        ),
        RemoteStep("hold final farewell pose", "sleep 0.5"),
        RemoteStep(
            "settle to soft farewell pose",
            "python3 /home/sunrise/Desktop/four_servo_control.py pose 2048 2120 2048 2300 --speeds 120 75 75 100",
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
