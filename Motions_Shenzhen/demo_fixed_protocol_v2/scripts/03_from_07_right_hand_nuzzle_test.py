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
                    f"D wide nuzzle {cycle} - lift from palm",
                    (2400, 2255, 2265, 2180),
                    (165, 145, 195, 165),
                ),
                RemoteStep(f"D wide nuzzle {cycle} - upper beat", "sleep 0.20"),
                pose(
                    f"D wide nuzzle {cycle} - sink under palm",
                    (2400, 2245, 2510, 2180),
                    (165, 145, 195, 165),
                ),
                RemoteStep(f"D wide nuzzle {cycle} - lower beat", "sleep 0.21"),
                pose(
                    f"D wide nuzzle {cycle} - rub left",
                    (2400, 2245, 2400, 1920),
                    (150, 130, 175, 220),
                ),
                RemoteStep(f"D wide nuzzle {cycle} - left beat", "sleep 0.19"),
                pose(
                    f"D wide nuzzle {cycle} - rub right",
                    (2400, 2245, 2400, 2400),
                    (150, 130, 175, 220),
                ),
                RemoteStep(f"D wide nuzzle {cycle} - right beat", "sleep 0.19"),
                pose(
                    f"D wide nuzzle {cycle} - return under palm center",
                    (2400, 2245, 2420, 2180),
                    (150, 130, 175, 195),
                ),
                RemoteStep(f"D wide nuzzle {cycle} - center beat", "sleep 0.20"),
            ]
        )
    return steps


def build_steps(
    *,
    stage1_seconds: float,
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
            RemoteStep("A stage 1 warm palm contact breathe", led("breathe 255 128 48 150")),
            RemoteStep("A stage 1 hold warm breathe", f"sleep {max(0.0, stage1_seconds):.2f}"),
            RemoteStep("A stage 2 warm rotating palm light starts with motion", led("spin 255 145 48 0 1 155")),
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

    return steps


def main() -> None:
    parser = build_parser("Test scene 03: PDF-faithful right-hand nuzzle starting from scene 07 end pose.")
    parser.add_argument("--stage1-seconds", type=float, default=3.5)
    parser.add_argument("--stage2-seconds", type=float, default=0.0, help="Compatibility option; stage 2 rotation now runs during motion.")
    parser.add_argument("--recognition-seconds", type=float, default=None, help="Legacy alias for --stage1-seconds.")
    parser.add_argument("--nuzzle-cycles", type=int, default=2)
    parser.add_argument("--final-pose", choices=("scene07", "soft-natural"), default="scene07")
    parser.add_argument("--skip-start-pose", action="store_true", help="Do not send the start-pose command if already in 07 end pose.")
    args = parser.parse_args()
    stage1_seconds = args.stage1_seconds if args.recognition_seconds is None else args.recognition_seconds
    exit_from_plan(
        args=args,
        steps=build_steps(
            stage1_seconds=stage1_seconds,
            nuzzle_cycles=args.nuzzle_cycles,
            final_pose=args.final_pose,
            skip_start_pose=args.skip_start_pose,
        ),
    )


if __name__ == "__main__":
    main()
