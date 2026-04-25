#!/usr/bin/env python3

from __future__ import annotations

import argparse

from common import RemoteStep, build_common_parser, exit_from_run


def build_steps(winner: str) -> list[RemoteStep]:
    if winner == "left":
        final_pose = "python3 /home/sunrise/Desktop/servo_1_3_slow_1800_2750.py --target-1 1800 --target-3 2750 --speed 100"
    else:
        final_pose = "python3 /home/sunrise/Desktop/servo_1_3_slow_1800_2750.py --target-1 2200 --target-3 2750 --speed 100"
    return [
        RemoteStep("look to guest A", "python3 /home/sunrise/Desktop/servo_3_shake_2100_2000.py --cycles 1 --start left --pause 0.08"),
        RemoteStep("pause in uncertainty", "sleep 0.4"),
        RemoteStep("shift to guest B", "python3 /home/sunrise/Desktop/servo_3_shake_2100_2000.py --cycles 1 --start right --pause 0.08"),
        RemoteStep("pause before choosing", "sleep 0.4"),
        RemoteStep("settle attention on final guest", final_pose),
        RemoteStep("soft confirming nod", "python3 /home/sunrise/Desktop/servo_2_nod_1900_2200.py --cycles 1 --pause 0.08"),
    ]


def main() -> None:
    parser = build_common_parser("Fixed Shenzhen scene: multi guest choice.")
    parser.add_argument("--winner", choices=("left", "right"), default="left")
    args = parser.parse_args()
    steps = build_steps(args.winner)
    steps.append(
        RemoteStep(
            "return to waiting pose",
            "python3 /home/sunrise/Desktop/four_servo_control.py pose 2048 2150 2048 2130 --speeds 200 100 100 200",
        )
    )
    exit_from_run(args=args, steps=steps)


if __name__ == "__main__":
    main()
