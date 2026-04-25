#!/usr/bin/env python3

from __future__ import annotations

from common import RemoteStep, build_parser, exit_from_plan


def build_steps(*, light_style: str, rub_cycles: int, variant: str) -> list[RemoteStep]:
    if light_style == "breathe":
        light_cmd = "python3 /home/sunrise/Desktop/send_uart3_led_cmd.py breathe 255 190 120 120"
    else:
        light_cmd = "python3 /home/sunrise/Desktop/send_uart3_led_cmd.py all 255 190 120 120"

    steps = [
        RemoteStep("warm ready light", light_cmd),
        RemoteStep("pause before approach", "sleep 0.4"),
        RemoteStep("lean toward hand", "python3 /home/sunrise/Desktop/servo_1_2_lean_forward_2148_1848.py"),
    ]

    if variant == "04":
        steps.append(
            RemoteStep(
                "deeper under-palm dip",
                "python3 /home/sunrise/Desktop/servo_1_2_lean_forward_2148_1848.py --target-1 2180 --target-2 1820",
            )
        )
    else:
        steps.append(RemoteStep("enter under-palm pose", "sleep 0.2"))

    for idx in range(rub_cycles):
        steps.append(
            RemoteStep(
                f"rub cycle {idx + 1} - nod",
                "python3 /home/sunrise/Desktop/servo_2_nod_1900_2200.py --cycles 1 --pause 0.05",
            )
        )
        steps.append(
            RemoteStep(
                f"rub cycle {idx + 1} - shake",
                "python3 /home/sunrise/Desktop/servo_3_shake_2100_2000.py --cycles 1 --pause 0.05",
            )
        )

    if variant == "04":
        steps.append(
            RemoteStep(
                "follow once as hand leaves",
                "python3 /home/sunrise/Desktop/servo_1_2_lean_forward_2148_1848.py --target-1 2200 --target-2 1800",
            )
        )
    else:
        steps.append(RemoteStep("follow once as hand leaves", "python3 /home/sunrise/Desktop/servo_1_2_lean_forward_2148_1848.py"))

    steps.extend(
        [
            RemoteStep(
                "return to waiting pose",
                "python3 /home/sunrise/Desktop/four_servo_control.py pose 2048 2150 2048 2130 --speeds 200 100 100 200",
            ),
            RemoteStep("natural warm light", "python3 /home/sunrise/Desktop/send_uart3_led_cmd.py all 255 220 180 100"),
        ]
    )
    return steps


def main() -> None:
    parser = build_parser("Demo scene 03: hand nuzzle (Videos 03 and 04).")
    parser.add_argument("--light-style", choices=("all", "breathe"), default="all")
    parser.add_argument("--rub-cycles", type=int, default=2)
    parser.add_argument("--variant", choices=("03", "04"), default="03")
    args = parser.parse_args()
    exit_from_plan(
        args=args,
        steps=build_steps(light_style=args.light_style, rub_cycles=max(1, args.rub_cycles), variant=args.variant),
    )


if __name__ == "__main__":
    main()
