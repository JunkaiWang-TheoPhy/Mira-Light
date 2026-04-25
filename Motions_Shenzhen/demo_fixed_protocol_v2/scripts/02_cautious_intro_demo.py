#!/usr/bin/env python3

from __future__ import annotations

from common import RemoteStep, build_parser, exit_from_plan


def build_steps(*, pause_seconds: float, skip_final_peek: bool) -> list[RemoteStep]:
    steps = [
        RemoteStep(
            "settle to neutral waiting pose",
            "python3 /home/sunrise/Desktop/four_servo_control.py pose 2048 2150 2048 2130 --speeds 180 100 100 180",
        ),
        RemoteStep("soft curious light", "python3 /home/sunrise/Desktop/send_uart3_led_cmd.py all 255 220 180 90"),
        RemoteStep(
            "slow look toward left-side judges",
            "python3 /home/sunrise/Desktop/servo_1_3_slow_1800_2750.py --target-1 2050 --target-3 2460 --speeds 110 110 --delay-ratio 0",
        ),
        RemoteStep("pause to register attention", f"sleep {pause_seconds:.2f}"),
        RemoteStep(
            "first cautious lean",
            "python3 /home/sunrise/Desktop/servo_1_2_lean_forward_2148_1848.py --target-1 2100 --target-2 1900 --speed 90",
        ),
        RemoteStep(
            "small uncertain shake",
            "python3 /home/sunrise/Desktop/servo_3_shake_2100_2000.py --cycles 1 --left 2210 --right 2070 --return-target 2130 --speed 130 --pause 0.08",
        ),
        RemoteStep(
            "second deeper peek",
            "python3 /home/sunrise/Desktop/servo_1_2_lean_forward_2148_1848.py --target-1 2148 --target-2 1848 --speed 80",
        ),
        RemoteStep("hold close curiosity", "sleep 0.35"),
        RemoteStep(
            "shy retreat",
            "python3 /home/sunrise/Desktop/servo_1_2_dodge_1848_1808.py --target-1 1880 --target-2 1860 --speed 90",
        ),
        RemoteStep("warmer shy light", "python3 /home/sunrise/Desktop/send_uart3_led_cmd.py all 255 205 155 75"),
        RemoteStep(
            "shy head dip",
            "python3 /home/sunrise/Desktop/servo_2_nod_1900_2200.py --cycles 1 --low 1960 --high 2140 --return-target 2048 --pre-target 2130 --speed 110 --pause 0.08",
        ),
    ]

    if not skip_final_peek:
        steps.extend(
            [
                RemoteStep(
                    "peek back once",
                    "python3 /home/sunrise/Desktop/servo_1_2_lean_forward_2148_1848.py --target-1 2105 --target-2 1900 --speed 80",
                ),
                RemoteStep(
                    "final single nod",
                    "python3 /home/sunrise/Desktop/servo_2_nod_1900_2200.py --cycles 1 --low 1980 --high 2110 --return-target 2048 --pre-target 2130 --speed 120 --pause 0.05",
                ),
            ]
        )

    steps.append(
        RemoteStep(
            "settle to soft attention pose",
            "python3 /home/sunrise/Desktop/four_servo_control.py pose 2048 2150 2048 2130 --speeds 160 90 90 160",
        )
    )
    steps.append(RemoteStep("natural warm light", "python3 /home/sunrise/Desktop/send_uart3_led_cmd.py all 255 220 180 100"))
    return steps


def main() -> None:
    parser = build_parser("Demo scene 02 v2: cautious intro aligned to board commands.")
    parser.add_argument("--extra-peek", action="store_true", help="Deprecated: final peek is now part of the default flow.")
    parser.add_argument("--skip-final-peek", action="store_true", help="Skip the final peek-back and nod beat.")
    parser.add_argument("--pause-seconds", type=float, default=0.6)
    args = parser.parse_args()
    exit_from_plan(args=args, steps=build_steps(pause_seconds=args.pause_seconds, skip_final_peek=args.skip_final_peek))


if __name__ == "__main__":
    main()
