#!/usr/bin/env python3

from __future__ import annotations

from common import RemoteStep, build_parser, exit_from_plan


def build_steps(*, light_style: str, rub_cycles: int, variant: str) -> list[RemoteStep]:
    if light_style == "breathe":
        light_cmd = "python3 /home/sunrise/Desktop/send_uart3_led_cmd.py breathe 255 190 120 120"
    else:
        light_cmd = "python3 /home/sunrise/Desktop/send_uart3_led_cmd.py all 255 190 120 120"

    if variant == "04":
        steps = [
            RemoteStep("warm target-follow light", light_cmd),
            RemoteStep(
                "settle into table-side attention",
                "python3 /home/sunrise/Desktop/four_servo_control.py pose 2048 2120 1980 2240 --speeds 160 90 90 130",
            ),
            RemoteStep("hold target lock", "sleep 0.8"),
            RemoteStep(
                "tiny tracking correction - vertical",
                "python3 /home/sunrise/Desktop/servo_2_nod_1900_2200.py --cycles 1 --low 1985 --high 2085 --return-target 2015 --pre-target 2240 --speed 120 --pause 0.04",
            ),
            RemoteStep(
                "tiny tracking correction - side",
                "python3 /home/sunrise/Desktop/servo_3_shake_2100_2000.py --cycles 1 --left 2290 --right 2190 --return-target 2240 --speed 130 --pause 0.04",
            ),
            RemoteStep("prepare decisive reach", "sleep 0.35"),
            RemoteStep(
                "decisive forward-down reach",
                "python3 /home/sunrise/Desktop/servo_1_2_lean_forward_2148_1848.py --target-1 2200 --target-2 1800 --speed 75",
            ),
            RemoteStep("hold reached target pose", "sleep 1.2"),
            RemoteStep("soft follow light", "python3 /home/sunrise/Desktop/send_uart3_led_cmd.py all 255 205 150 105"),
        ]
    else:
        steps = [
            RemoteStep("warm ready light", light_cmd),
            RemoteStep(
                "settle into near-hand waiting pose",
                "python3 /home/sunrise/Desktop/four_servo_control.py pose 2048 2120 1980 2180 --speeds 160 90 90 130",
            ),
            RemoteStep("pause before approach", "sleep 0.4"),
            RemoteStep(
                "lean toward hand",
                "python3 /home/sunrise/Desktop/servo_1_2_lean_forward_2148_1848.py --target-1 2148 --target-2 1848 --speed 85",
            ),
            RemoteStep("hold close approach", "sleep 0.35"),
            RemoteStep(
                "dip under palm",
                "python3 /home/sunrise/Desktop/servo_1_2_lean_forward_2148_1848.py --target-1 2180 --target-2 1820 --speed 70",
            ),
        ]

    for idx in range(rub_cycles):
        steps.append(
            RemoteStep(
                f"micro nuzzle cycle {idx + 1} - vertical",
                "python3 /home/sunrise/Desktop/servo_2_nod_1900_2200.py --cycles 1 --low 1910 --high 1995 --return-target 1955 --pre-target 2180 --speed 120 --pause 0.04",
            )
        )
        steps.append(
            RemoteStep(
                f"micro nuzzle cycle {idx + 1} - side",
                "python3 /home/sunrise/Desktop/servo_3_shake_2100_2000.py --cycles 1 --left 2240 --right 2160 --return-target 2200 --speed 130 --pause 0.04",
            )
        )

    if variant == "04":
        steps.append(
            RemoteStep(
                "hold short-video target contact",
                "sleep 0.8",
            )
        )
    else:
        steps.extend(
            [
                RemoteStep(
                    "short follow as hand leaves",
                    "python3 /home/sunrise/Desktop/servo_1_2_lean_forward_2148_1848.py --target-1 2210 --target-2 1805 --speed 80",
                ),
                RemoteStep("hold close after follow", "sleep 0.8"),
            ]
        )

    steps.extend(
        [
            RemoteStep(
                "soft release from close pose",
                "python3 /home/sunrise/Desktop/four_servo_control.py pose 2048 2110 1985 2180 --speeds 140 80 80 120",
            ),
            RemoteStep("linger in affectionate pose", "sleep 0.5"),
            RemoteStep(
                "return to natural waiting pose",
                "python3 /home/sunrise/Desktop/four_servo_control.py pose 2048 2150 2048 2130 --speeds 140 90 90 140",
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
