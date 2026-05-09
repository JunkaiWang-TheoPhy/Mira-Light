#!/usr/bin/env python3

from __future__ import annotations

from common import RemoteStep, build_parser, exit_from_plan


def pose(label: str, p0: int, p1: int, p2: int, p3: int, speeds: tuple[int, int, int, int]) -> RemoteStep:
    s0, s1, s2, s3 = speeds
    return RemoteStep(
        label,
        f"python3 /home/sunrise/Desktop/four_servo_control.py pose {p0} {p1} {p2} {p3} --speeds {s0} {s1} {s2} {s3}",
    )


def build_steps(*, correction_cycles: int, hold_far_seconds: float, final_pose: str, light_brightness: int) -> list[RemoteStep]:
    brightness = max(0, min(255, light_brightness))
    steps: list[RemoteStep] = [
        RemoteStep(
            "functional tabletop light",
            f"python3 /home/sunrise/Desktop/send_uart3_led_cmd.py all 255 255 245 {brightness}",
        ),
        pose("drive joint 2 into tabletop view", 2048, 2150, 2396, 2480, (220, 110, 230, 180)),
        RemoteStep("let tabletop drop settle", "sleep 1.20"),
        pose("set head-down reading height", 2048, 2320, 2416, 2480, (180, 135, 130, 160)),
        RemoteStep("lock low reading height before tracking", "sleep 1.20"),
        pose("book starts on left side", 2260, 2320, 2416, 3030, (170, 75, 80, 260)),
        RemoteStep("hold where the book starts", "sleep 2.00"),
        pose("follow book across shifted center", 2048, 2310, 2396, 2480, (150, 70, 80, 220)),
        RemoteStep("smooth center pass", "sleep 2.50"),
        pose("follow book to right side with base yaw right", 2360, 2300, 2376, 2130, (150, 70, 80, 220)),
        RemoteStep("hold right book lock", f"sleep {hold_far_seconds:.2f}"),
    ]

    for idx in range(max(0, correction_cycles)):
        steps.extend(
            [
                pose(
                    f"book moves again {idx + 1}",
                    2260,
                    2305,
                    2386,
                    2300,
                    (120, 60, 70, 170),
                ),
                RemoteStep(f"hold moved book {idx + 1}", "sleep 1.00"),
                pose(
                    f"book stops again {idx + 1}",
                    2360,
                    2300,
                    2376,
                    2130,
                    (120, 60, 70, 170),
                ),
                RemoteStep(f"hold stopped book {idx + 1}", "sleep 1.20"),
            ]
        )

    if final_pose == "tabletop":
        steps.extend(
            [
                pose("settle tabletop waiting pose", 2048, 2300, 2376, 2130, (150, 80, 120, 160)),
                RemoteStep(
                    "settle functional light",
                    "python3 /home/sunrise/Desktop/send_uart3_led_cmd.py all 255 255 245 105",
                ),
            ]
        )
    else:
        steps.extend(
            [
                pose("end target-oriented with base yaw right and centered head", 2360, 2300, 2376, 2130, (130, 65, 90, 150)),
                RemoteStep(
                    "keep light on target",
                    "python3 /home/sunrise/Desktop/send_uart3_led_cmd.py all 255 255 245 115",
                ),
            ]
        )
    return steps


def main() -> None:
    parser = build_parser("Fixed demo script 07: tabletop object follow, based on Video 08 and PDF item 4.")
    parser.add_argument("--correction-cycles", type=int, default=1)
    parser.add_argument("--hold-far-seconds", type=float, default=2.50)
    parser.add_argument("--final-pose", choices=("target", "tabletop"), default="target")
    parser.add_argument("--light-brightness", type=int, default=125)
    args = parser.parse_args()
    exit_from_plan(
        args=args,
        steps=build_steps(
            correction_cycles=args.correction_cycles,
            hold_far_seconds=max(0.0, args.hold_far_seconds),
            final_pose=args.final_pose,
            light_brightness=args.light_brightness,
        ),
    )


if __name__ == "__main__":
    main()
