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


def warm_spin(label: str, r: int, g: int, b: int, brightness: int) -> RemoteStep:
    return RemoteStep(label, led(f"spin {r} {g} {b} 0 1 {brightness}"))


def build_nuzzle_cycles(cycles: int) -> list[RemoteStep]:
    steps: list[RemoteStep] = []
    for idx in range(max(1, min(cycles, 4))):
        cycle = idx + 1
        steps.extend(
            [
                warm_spin(f"D warm rotation during nuzzle {cycle} - palm warm", 255, 145, 48, 155),
                pose(
                    f"D small nuzzle {cycle} - lift from palm",
                    (2400, 2255, 2355, 2180),
                    (110, 95, 130, 110),
                ),
                RemoteStep(f"D small nuzzle {cycle} - upper beat", "sleep 0.30"),
                pose(
                    f"D small nuzzle {cycle} - sink under palm",
                    (2400, 2245, 2420, 2180),
                    (110, 95, 130, 110),
                ),
                RemoteStep(f"D small nuzzle {cycle} - lower beat", "sleep 0.32"),
                warm_spin(f"D warm rotation during nuzzle {cycle} - gentle glow", 255, 166, 76, 145),
                pose(
                    f"D small nuzzle {cycle} - rub slightly left",
                    (2400, 2245, 2400, 2100),
                    (100, 85, 115, 145),
                ),
                RemoteStep(f"D small nuzzle {cycle} - left beat", "sleep 0.28"),
                pose(
                    f"D small nuzzle {cycle} - rub slightly right",
                    (2400, 2245, 2400, 2220),
                    (100, 85, 115, 145),
                ),
                RemoteStep(f"D small nuzzle {cycle} - right beat", "sleep 0.28"),
                warm_spin(f"D warm rotation during nuzzle {cycle} - soft amber", 255, 132, 48, 135),
                pose(
                    f"D small nuzzle {cycle} - return under palm center",
                    (2400, 2245, 2420, 2180),
                    (100, 85, 115, 130),
                ),
                RemoteStep(f"D small nuzzle {cycle} - center beat", "sleep 0.30"),
            ]
        )
    return steps


def build_steps(
    *,
    recognition_seconds: float,
    nuzzle_cycles: int,
    final_pose: str,
    skip_start_pose: bool,
) -> list[RemoteStep]:
    steps: list[RemoteStep] = [
        RemoteStep("03 from 07 right-hand nuzzle safety note", "echo '[03-from-07] right-side hand nuzzle from scene 07 end pose'"),
    ]
    if not skip_start_pose:
        steps.append(pose("A set 03 initial pose from 07 end", START_POSE, START_SPEEDS_OLD03_2X))

    steps.extend(
        [
            RemoteStep("A warm palm contact breathe", led("breathe 255 128 48 150")),
            RemoteStep("A right-side recognition hold", f"sleep {max(0.0, recognition_seconds):.2f}"),
            pose("B slowly approach right palm", (2400, 2260, 2360, 2180), (180, 120, 110, 160)),
            RemoteStep("B soft approach settle", "sleep 0.35"),
            pose("C lower head under palm", (2400, 2240, 2420, 2180), (150, 100, 120, 140)),
            RemoteStep("C under-palm settle", "sleep 0.35"),
        ]
    )

    steps.extend(build_nuzzle_cycles(nuzzle_cycles))
    steps.extend(
        [
            pose("E short follow as hand leaves", (2440, 2220, 2360, 2220), (130, 90, 100, 130)),
            RemoteStep("E short follow hold", "sleep 0.45"),
        ]
    )

    if final_pose == "soft-natural":
        steps.extend(
            [
                pose("F soft return to natural right-side direction", (2360, 2280, 2320, 2130), (140, 90, 100, 130)),
                RemoteStep("F natural warm light", led("all 255 220 180 100")),
            ]
        )
    else:
        steps.extend(
            [
                pose("F return to scene 07 end pose", START_POSE, (160, 110, 120, 140)),
                RemoteStep("F keep warm palm breathe", led("breathe 255 128 48 135")),
            ]
        )

    return steps


def main() -> None:
    parser = build_parser("Test scene 03: PDF-faithful right-hand nuzzle starting from scene 07 end pose.")
    parser.add_argument("--recognition-seconds", type=float, default=1.2)
    parser.add_argument("--nuzzle-cycles", type=int, default=2)
    parser.add_argument("--final-pose", choices=("scene07", "soft-natural"), default="scene07")
    parser.add_argument("--skip-start-pose", action="store_true", help="Do not send the start-pose command if already in 07 end pose.")
    args = parser.parse_args()
    exit_from_plan(
        args=args,
        steps=build_steps(
            recognition_seconds=args.recognition_seconds,
            nuzzle_cycles=args.nuzzle_cycles,
            final_pose=args.final_pose,
            skip_start_pose=args.skip_start_pose,
        ),
    )


if __name__ == "__main__":
    main()
