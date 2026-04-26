#!/usr/bin/env python3

from __future__ import annotations

from common import RemoteStep, build_parser, exit_from_plan


def pose(label: str, p0: int, p1: int, p2: int, p3: int, speeds: tuple[int, int, int, int]) -> RemoteStep:
    s0, s1, s2, s3 = speeds
    return RemoteStep(
        label,
        f"python3 /home/sunrise/Desktop/four_servo_control.py pose {p0} {p1} {p2} {p3} --speeds {s0} {s1} {s2} {s3}",
    )


def build_steps(
    *,
    correction_cycles: int,
    hold_high_seconds: float,
    hold_far_seconds: float,
    final_pose: str,
    light_brightness: int,
    skip_start_sleep: bool,
) -> list[RemoteStep]:
    brightness = max(0, min(255, light_brightness))
    steps: list[RemoteStep] = []

    if not skip_start_sleep:
        steps.extend(
            [
                RemoteStep("01 start dark", "python3 /home/sunrise/Desktop/send_uart3_led_cmd.py off"),
                pose("01 fold to sleep start pose", 2048, 1821, 2912, 2130, (4000, 640, 2480, 4000)),
                RemoteStep("01 hold still before waking", "sleep 0.40"),
            ]
        )

    steps.extend(
        [
            RemoteStep("01 tiny warm pre-glow", "python3 /home/sunrise/Desktop/send_uart3_led_cmd.py all 255 180 120 25"),
            RemoteStep("01 pause before eye-open effect", "sleep 0.18"),
            RemoteStep("01 wake light", "python3 /home/sunrise/Desktop/send_uart3_led_cmd.py wake 255 220 180 150"),
            RemoteStep("01 pause for eye-open effect", "sleep 0.30"),
            pose("01 half-awake lift", 2048, 1900, 2750, 2130, (440, 180, 360, 360)),
            RemoteStep("01 half-awake pause", "sleep 0.25"),
            RemoteStep(
                "01 stretch to high point",
                "python3 /home/sunrise/Desktop/four_servo_pose_delay_2.py --targets 2048 2400 1700 2130 --speeds 2000 320 760 2000 --delay-ratio 0.25",
            ),
            RemoteStep("01 hold high point", f"sleep {max(0.0, hold_high_seconds):.2f}"),
            RemoteStep(
                "01 long stretch accent",
                "python3 /home/sunrise/Desktop/four_servo_pose_2048_2048_2048_2780_separate.py --speed 500 --delay 0.05",
            ),
            RemoteStep(
                "handoff: skip 01 normal return and 07 neutral entry",
                "sleep 0.08",
            ),
            RemoteStep(
                "07 functional tabletop light",
                f"python3 /home/sunrise/Desktop/send_uart3_led_cmd.py all 255 255 245 {brightness}",
            ),
            pose("07 drive joint 2 into tabletop view", 2048, 2150, 2396, 2480, (440, 220, 460, 360)),
            RemoteStep("07 let tabletop drop settle", "sleep 0.60"),
            pose("07 set head-down reading height", 2048, 2320, 2416, 2480, (360, 270, 260, 320)),
            RemoteStep("07 lock low reading height before tracking", "sleep 0.60"),
            pose("07 book starts on left side", 2260, 2320, 2416, 3030, (340, 150, 160, 520)),
            RemoteStep("07 hold where the book starts", "sleep 1.00"),
            pose("07 follow book across shifted center", 2048, 2310, 2396, 2480, (300, 140, 160, 440)),
            RemoteStep("07 smooth center pass", "sleep 1.25"),
            pose("07 follow book to right side with base yaw right", 2360, 2300, 2376, 2130, (300, 140, 160, 440)),
            RemoteStep("07 hold right book lock", f"sleep {max(0.0, hold_far_seconds):.2f}"),
        ]
    )

    for idx in range(max(0, correction_cycles)):
        steps.extend(
            [
                pose(
                    f"07 book moves again {idx + 1}",
                    2260,
                    2305,
                    2386,
                    2300,
                    (240, 120, 140, 340),
                ),
                RemoteStep(f"07 hold moved book {idx + 1}", "sleep 0.50"),
                pose(
                    f"07 book stops again {idx + 1}",
                    2360,
                    2300,
                    2376,
                    2130,
                    (240, 120, 140, 340),
                ),
                RemoteStep(f"07 hold stopped book {idx + 1}", "sleep 0.60"),
            ]
        )

    if final_pose == "tabletop":
        steps.extend(
            [
                pose("07 settle tabletop waiting pose", 2048, 2300, 2376, 2130, (300, 160, 240, 320)),
                RemoteStep("07 settle functional light", "python3 /home/sunrise/Desktop/send_uart3_led_cmd.py all 255 255 245 105"),
            ]
        )
    else:
        steps.extend(
            [
                pose("07 end target-oriented with base yaw right and centered head", 2360, 2300, 2376, 2130, (260, 130, 180, 300)),
                RemoteStep("07 keep light on target", "python3 /home/sunrise/Desktop/send_uart3_led_cmd.py all 255 255 245 115"),
            ]
        )

    return steps


def main() -> None:
    parser = build_parser("Test combo script: scene 01 wake directly into scene 07 tabletop follow at 2x servo speeds.")
    parser.add_argument("--correction-cycles", type=int, default=1)
    parser.add_argument("--hold-high-seconds", type=float, default=0.6)
    parser.add_argument("--hold-far-seconds", type=float, default=1.25)
    parser.add_argument("--final-pose", choices=("target", "tabletop"), default="target")
    parser.add_argument("--light-brightness", type=int, default=125)
    parser.add_argument("--skip-start-sleep", action="store_true", help="Skip the initial fold-to-sleep preparation.")
    args = parser.parse_args()
    exit_from_plan(
        args=args,
        steps=build_steps(
            correction_cycles=args.correction_cycles,
            hold_high_seconds=args.hold_high_seconds,
            hold_far_seconds=args.hold_far_seconds,
            final_pose=args.final_pose,
            light_brightness=args.light_brightness,
            skip_start_sleep=args.skip_start_sleep,
        ),
    )


if __name__ == "__main__":
    main()
