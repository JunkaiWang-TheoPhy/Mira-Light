#!/usr/bin/env python3

from __future__ import annotations

from common import RemoteStep, build_parser, exit_from_plan


START_POSE = (2360, 2300, 2376, 2130)
START_SPEEDS_OLD03_2X = (240, 150, 150, 220)


def led(command: str) -> str:
    return f"python3 /home/sunrise/Desktop/send_uart3_led_cmd.py {command}"


def pose(label: str, positions: tuple[int, int, int, int], speeds: tuple[int, int, int, int]) -> RemoteStep:
    p0, p1, p2, p3 = positions
    s0, s1, s2, s3 = speeds
    return RemoteStep(
        label,
        f"python3 /home/sunrise/Desktop/four_servo_control.py pose {p0} {p1} {p2} {p3} --speeds {s0} {s1} {s2} {s3}",
    )


def build_nuzzle_cycles(cycles: int) -> list[RemoteStep]:
    steps: list[RemoteStep] = []
    for idx in range(max(1, min(cycles, 4))):
        cycle = idx + 1
        steps.extend(
            [
                pose(
                    f"small nuzzle {cycle} - lift from palm",
                    (2400, 2240, 2070, 2180),
                    (100, 90, 130, 110),
                ),
                RemoteStep(f"small nuzzle {cycle} - upper beat", "sleep 0.18"),
                pose(
                    f"small nuzzle {cycle} - sink under palm",
                    (2400, 2240, 2420, 2180),
                    (100, 90, 130, 110),
                ),
                RemoteStep(f"small nuzzle {cycle} - lower beat", "sleep 0.18"),
                pose(
                    f"small nuzzle {cycle} - rub slightly left",
                    (2400, 2240, 2400, 1730),
                    (90, 80, 110, 145),
                ),
                RemoteStep(f"small nuzzle {cycle} - left beat", "sleep 0.16"),
                pose(
                    f"small nuzzle {cycle} - rub slightly right",
                    (2400, 2240, 2400, 2280),
                    (90, 80, 110, 145),
                ),
                RemoteStep(f"small nuzzle {cycle} - right beat", "sleep 0.16"),
                pose(
                    f"small nuzzle {cycle} - return under palm center",
                    (2400, 2240, 2420, 2180),
                    (90, 80, 110, 130),
                ),
                RemoteStep(f"small nuzzle {cycle} - center beat", "sleep 0.14"),
            ]
        )
    return steps


def build_steps(
    *,
    nuzzle_cycles: int,
    skip_start_pose: bool,
) -> list[RemoteStep]:
    steps: list[RemoteStep] = [
        RemoteStep("03 right-hand nuzzle safety note", "echo '[03-right-hand] D/E only: expanded nuzzle, short follow, no return'"),
    ]
    if not skip_start_pose:
        steps.append(pose("set D initial under-palm pose", (2400, 2240, 2420, 2180), START_SPEEDS_OLD03_2X))

    steps.extend(
        [
            RemoteStep("D warm palm light", led("breathe 255 128 48 145")),
            RemoteStep("D settle before small nuzzle", "sleep 0.20"),
            RemoteStep("D stage 2 warm palm rotation", led("spin 255 145 48 0 1 155")),
            RemoteStep("D stage 2 rotation settle", "sleep 0.60"),
        ]
    )

    steps.extend(build_nuzzle_cycles(nuzzle_cycles))
    steps.extend(
        [
            pose("E short follow as hand leaves", (2480, 2200, 2300, 2260), (170, 115, 130, 150)),
            RemoteStep("E short follow hold", "sleep 0.45"),
        ]
    )

    return steps


def main() -> None:
    parser = build_parser("Test scene 03: right-side hand nuzzle D/E/F only.")
    parser.add_argument("--nuzzle-cycles", type=int, default=2)
    parser.add_argument("--skip-start-pose", action="store_true", help="Do not send the D initial under-palm pose.")
    args = parser.parse_args()
    exit_from_plan(
        args=args,
        steps=build_steps(
            nuzzle_cycles=args.nuzzle_cycles,
            skip_start_pose=args.skip_start_pose,
        ),
    )


if __name__ == "__main__":
    main()
