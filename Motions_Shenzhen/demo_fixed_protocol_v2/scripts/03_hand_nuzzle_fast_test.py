#!/usr/bin/env python3

from __future__ import annotations

from common import RemoteStep, build_parser, exit_from_plan


def light_command(style: str) -> str:
    if style == "breathe":
        return "python3 /home/sunrise/Desktop/send_uart3_led_cmd.py breathe 255 178 92 115"
    return "python3 /home/sunrise/Desktop/send_uart3_led_cmd.py all 255 178 92 115"


def pose(
    label: str,
    p0: int,
    p1: int,
    p2: int,
    p3: int,
    speeds: tuple[int, int, int, int],
) -> RemoteStep:
    s0, s1, s2, s3 = speeds
    return RemoteStep(
        label,
        f"python3 /home/sunrise/Desktop/four_servo_control.py pose {p0} {p1} {p2} {p3} --speeds {s0} {s1} {s2} {s3}",
    )


def build_nuzzle_cycles(cycles: int) -> list[RemoteStep]:
    steps: list[RemoteStep] = []
    for idx in range(cycles):
        cycle = idx + 1
        side_left = 2165 if idx % 2 == 0 else 2155
        side_right = 2095 if idx % 2 == 0 else 2105
        return_side = 2130 if idx % 2 == 0 else 2125
        steps.extend(
            [
                pose(
                    f"palm nuzzle cycle {cycle} - body nestles up",
                    2048,
                    2160,
                    1855,
                    return_side,
                    (120, 90, 76, 100),
                ),
                RemoteStep(
                    f"palm nuzzle cycle {cycle} - side rub",
                    (
                        "python3 /home/sunrise/Desktop/servo_3_shake_2100_2000.py "
                        f"--cycles 1 --left {side_left} --right {side_right} "
                        f"--return-target {return_side} --speed 144 --pause 0.03"
                    ),
                ),
                pose(
                    f"palm nuzzle cycle {cycle} - body sinks back under hand",
                    2048,
                    2150,
                    1825,
                    return_side,
                    (116, 84, 70, 100),
                ),
                RemoteStep(f"palm nuzzle cycle {cycle} - soft contact beat", "sleep 0.07"),
            ]
        )
    return steps


def build_steps(*, light_style: str, rub_cycles: int, linger_seconds: float, final_pose: str) -> list[RemoteStep]:
    cycles = max(1, min(rub_cycles, 4))
    linger = max(0.0, linger_seconds)

    steps = [
        RemoteStep("warmest palm-ready light", light_command(light_style)),
        pose("orient gently toward offered hand", 2048, 2140, 1980, 2130, (240, 150, 150, 220)),
        RemoteStep("let the hand arrive", "sleep 0.23"),
        pose("creep closer to palm", 2048, 2170, 1900, 2130, (190, 120, 100, 160)),
        RemoteStep("hold before contact", "sleep 0.18"),
        pose("lower head under palm", 2048, 2150, 1850, 2130, (160, 110, 80, 140)),
        RemoteStep("settle into palm contact", "sleep 0.33"),
    ]

    steps.extend(build_nuzzle_cycles(cycles))

    steps.extend(
        [
            RemoteStep("hand lifts away cue", "sleep 0.10"),
            pose("short follow toward leaving hand", 2048, 2210, 1825, 2130, (150, 100, 80, 130)),
            RemoteStep("linger after short follow", f"sleep {linger:.2f}"),
            pose("hand returns - wait close and warm", 2048, 2160, 1850, 2130, (140, 90, 76, 120)),
            RemoteStep("affectionate close hold", "sleep 0.28"),
        ]
    )

    if final_pose == "close":
        steps.extend(
            [
                pose("finish in near-hand natural light direction", 2048, 2160, 1940, 2130, (172, 108, 116, 160)),
                RemoteStep("keep warm close light", "python3 /home/sunrise/Desktop/send_uart3_led_cmd.py all 255 205 145 105"),
            ]
        )
    else:
        steps.extend(
            [
                pose("soft release from palm", 2048, 2140, 1950, 2130, (180, 110, 100, 150)),
                RemoteStep("release without snapping back", "sleep 0.18"),
                pose("return to natural waiting direction", 2048, 2150, 2048, 2130, (236, 144, 144, 216)),
                RemoteStep("natural warm light", "python3 /home/sunrise/Desktop/send_uart3_led_cmd.py all 255 220 180 100"),
            ]
        )

    return steps


def main() -> None:
    parser = build_parser("Fast test scene 03: hand nuzzle at 2x servo speeds and half pauses.")
    parser.add_argument("--light-style", choices=("all", "breathe"), default="breathe")
    parser.add_argument("--rub-cycles", type=int, default=2)
    parser.add_argument("--linger-seconds", type=float, default=0.4)
    parser.add_argument("--final-pose", choices=("natural", "close"), default="natural")
    args = parser.parse_args()
    exit_from_plan(
        args=args,
        steps=build_steps(
            light_style=args.light_style,
            rub_cycles=args.rub_cycles,
            linger_seconds=args.linger_seconds,
            final_pose=args.final_pose,
        ),
    )


if __name__ == "__main__":
    main()
