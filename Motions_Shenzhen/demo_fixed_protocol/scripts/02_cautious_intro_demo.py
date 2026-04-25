#!/usr/bin/env python3

from __future__ import annotations

from common import RemoteStep, build_parser, exit_from_plan


def build_steps(*, extra_peek: bool, pause_seconds: float) -> list[RemoteStep]:
    steps = [
        RemoteStep(
            "look toward guest side",
            "python3 /home/sunrise/Desktop/servo_1_3_slow_1800_2750.py --speed 120 --delay-ratio 0",
        ),
        RemoteStep("pause to register attention", f"sleep {pause_seconds:.2f}"),
        RemoteStep("lean forward softly", "python3 /home/sunrise/Desktop/servo_1_2_lean_forward_2148_1848.py"),
        RemoteStep("slow uncertain shake", "python3 /home/sunrise/Desktop/servo_3_shake_2100_2000.py --cycles 1 --pause 0.08"),
        RemoteStep("lean a little deeper", "python3 /home/sunrise/Desktop/servo_1_2_lean_forward_2148_1848.py"),
        RemoteStep("shy dodge away", "python3 /home/sunrise/Desktop/servo_1_2_dodge_1848_1808.py"),
        RemoteStep("shy head dip", "python3 /home/sunrise/Desktop/servo_2_nod_1900_2200.py --cycles 1 --pause 0.08"),
    ]
    if extra_peek:
        steps.extend(
            [
                RemoteStep("peek back once", "python3 /home/sunrise/Desktop/servo_1_2_lean_forward_2148_1848.py"),
                RemoteStep("final single nod", "python3 /home/sunrise/Desktop/servo_2_nod_1900_2200.py --cycles 1 --pause 0.05"),
            ]
        )
    steps.append(
        RemoteStep(
            "settle to normal waiting pose",
            "python3 /home/sunrise/Desktop/four_servo_control.py pose 2048 2150 2048 2130 --speeds 200 100 100 200",
        )
    )
    return steps


def main() -> None:
    parser = build_parser("Demo scene 02: cautious intro.")
    parser.add_argument("--extra-peek", action="store_true")
    parser.add_argument("--pause-seconds", type=float, default=0.6)
    args = parser.parse_args()
    exit_from_plan(args=args, steps=build_steps(extra_peek=args.extra_peek, pause_seconds=args.pause_seconds))


if __name__ == "__main__":
    main()
