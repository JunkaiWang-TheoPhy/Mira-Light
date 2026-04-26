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
        pose("drive joint 2 into tabletop view", 2048, 2150, 2396, 2480, (440, 220, 460, 360)),
        RemoteStep("let tabletop drop settle", "sleep 0.60"),
        pose("set head-down reading height", 2048, 2320, 2416, 2480, (360, 270, 260, 320)),
        RemoteStep("lock low reading height before tracking", "sleep 0.60"),
        pose("book starts on left side", 2260, 2320, 2416, 3030, (340, 150, 160, 520)),
        RemoteStep("hold where the book starts", "sleep 1.00"),
        pose("follow book across shifted center", 2048, 2310, 2396, 2480, (300, 140, 160, 440)),
        RemoteStep("smooth center pass", "sleep 1.25"),
        pose("follow book to right side with base yaw right", 2360, 2300, 2376, 2130, (300, 140, 160, 440)),
        RemoteStep("hold right book lock", f"sleep {max(0.0, hold_far_seconds):.2f}"),
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
                    (240, 120, 140, 340),
                ),
                RemoteStep(f"hold moved book {idx + 1}", "sleep 0.50"),
                pose(
                    f"book stops again {idx + 1}",
                    2360,
                    2300,
                    2376,
                    2130,
                    (240, 120, 140, 340),
                ),
                RemoteStep(f"hold stopped book {idx + 1}", "sleep 0.60"),
            ]
        )

    if final_pose == "tabletop":
        steps.extend(
            [
                pose("settle tabletop waiting pose", 2048, 2300, 2376, 2130, (300, 160, 240, 320)),
                RemoteStep(
                    "settle functional light",
                    "python3 /home/sunrise/Desktop/send_uart3_led_cmd.py all 255 255 245 105",
                ),
            ]
        )
    else:
        steps.extend(
            [
                pose("end target-oriented with base yaw right and centered head", 2360, 2300, 2376, 2130, (260, 130, 180, 300)),
                RemoteStep(
                    "keep light on target",
                    "python3 /home/sunrise/Desktop/send_uart3_led_cmd.py all 255 255 245 115",
                ),
            ]
        )
    return steps


def main() -> None:
    parser = build_parser("Fast test script 07: tabletop follow at 2x servo speeds and half pauses.")
    parser.add_argument("--correction-cycles", type=int, default=1)
    parser.add_argument("--hold-far-seconds", type=float, default=1.25)
    parser.add_argument("--final-pose", choices=("target", "tabletop"), default="target")
    parser.add_argument("--light-brightness", type=int, default=125)
    args = parser.parse_args()
    exit_from_plan(
        args=args,
        steps=build_steps(
            correction_cycles=args.correction_cycles,
            hold_far_seconds=args.hold_far_seconds,
            final_pose=args.final_pose,
            light_brightness=args.light_brightness,
        ),
    )


if __name__ == "__main__":
    main()
