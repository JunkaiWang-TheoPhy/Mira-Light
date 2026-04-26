#!/usr/bin/env python3

from __future__ import annotations

from common import RemoteStep, build_parser, exit_from_plan


def pose(label: str, positions: tuple[int, int, int, int], speeds: tuple[int, int, int, int]) -> RemoteStep:
    pos = " ".join(str(value) for value in positions)
    speed = " ".join(str(value) for value in speeds)
    return RemoteStep(
        label,
        f"python3 /home/sunrise/Desktop/four_servo_control.py pose {pos} --speeds {speed}",
    )


def hold(label: str, seconds: float) -> RemoteStep:
    return RemoteStep(label, f"sleep {seconds:g}")


def build_micro_nuzzle_steps(*, cycles: int) -> list[RemoteStep]:
    steps: list[RemoteStep] = []
    for idx in range(cycles):
        cycle = idx + 1
        steps.extend(
            [
                pose(
                    f"micro nuzzle {cycle} - soft press under palm",
                    (2048, 2160, 1825, 2130),
                    (55, 45, 35, 55),
                ),
                hold(f"micro nuzzle {cycle} - press hold", 0.12),
                pose(
                    f"micro nuzzle {cycle} - release pressure",
                    (2048, 2150, 1855, 2130),
                    (55, 45, 35, 55),
                ),
                hold(f"micro nuzzle {cycle} - release hold", 0.1),
                pose(
                    f"micro nuzzle {cycle} - small side brush left",
                    (2048, 2150, 1850, 2165),
                    (50, 40, 35, 45),
                ),
                hold(f"micro nuzzle {cycle} - left hold", 0.1),
                pose(
                    f"micro nuzzle {cycle} - small side brush right",
                    (2048, 2150, 1850, 2095),
                    (50, 40, 35, 45),
                ),
                hold(f"micro nuzzle {cycle} - right hold", 0.1),
                pose(
                    f"micro nuzzle {cycle} - settle under palm",
                    (2048, 2150, 1850, 2130),
                    (50, 40, 35, 45),
                ),
                hold(f"micro nuzzle {cycle} - close settle", 0.18),
            ]
        )
    return steps


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
            RemoteStep(
                "hold short-video target contact",
                "sleep 0.8",
            ),
        ]
    else:
        steps = [
            RemoteStep("warm ready light", light_cmd),
            pose(
                "settle into near-hand waiting pose",
                (2048, 2140, 1980, 2130),
                (120, 75, 75, 110),
            ),
            hold("wait for hand to settle", 0.5),
            pose(
                "soft approach into hand zone",
                (2048, 2170, 1900, 2130),
                (95, 60, 50, 80),
            ),
            hold("hold close approach", 0.3),
            pose(
                "dip head under palm",
                (2048, 2150, 1850, 2130),
                (80, 55, 40, 70),
            ),
            hold("settle under palm before nuzzle", 0.35),
        ]
        steps.extend(build_micro_nuzzle_steps(cycles=rub_cycles))

    if variant == "04":
        pass
    else:
        steps.extend(
            [
                pose(
                    "short follow as hand leaves",
                    (2048, 2210, 1825, 2130),
                    (75, 50, 40, 65),
                ),
                hold("hold close after short follow", 0.45),
            ]
        )

    steps.extend(
        [
            pose(
                "soft release from close pose",
                (2048, 2140, 1950, 2130),
                (90, 55, 50, 75),
            ),
            hold("linger in affectionate pose", 0.45),
            pose(
                "return to natural waiting pose",
                (2048, 2150, 2048, 2130),
                (120, 75, 75, 120),
            ),
            RemoteStep("natural warm light", "python3 /home/sunrise/Desktop/send_uart3_led_cmd.py all 255 220 180 100"),
        ]
    )
    return steps


def main() -> None:
    parser = build_parser("Demo scene 03: hand nuzzle (Videos 03 and 04).")
    parser.add_argument("--light-style", choices=("all", "breathe"), default="all")
    parser.add_argument("--rub-cycles", type=int, default=1)
    parser.add_argument("--variant", choices=("03", "04"), default="03")
    args = parser.parse_args()
    exit_from_plan(
        args=args,
        steps=build_steps(light_style=args.light_style, rub_cycles=max(1, min(args.rub_cycles, 3)), variant=args.variant),
    )


if __name__ == "__main__":
    main()
