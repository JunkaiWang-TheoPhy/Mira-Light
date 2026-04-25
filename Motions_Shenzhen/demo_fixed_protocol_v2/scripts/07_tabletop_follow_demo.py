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
        pose("enter tabletop focus pose", 2048, 2180, 2080, 2260, (150, 90, 90, 130)),
        RemoteStep("briefly lock workspace", "sleep 0.55"),
        pose("acquire near-side target", 1940, 2220, 2160, 2320, (130, 90, 90, 120)),
        RemoteStep("hold near target", "sleep 0.75"),
        pose("continuous follow path one", 2025, 2230, 2180, 2290, (120, 80, 80, 115)),
        RemoteStep("short moving hold one", "sleep 0.25"),
        pose("continuous follow path two", 2120, 2245, 2190, 2340, (120, 80, 80, 115)),
        RemoteStep("short moving hold two", "sleep 0.25"),
        pose("arrive far-side target", 2230, 2260, 2220, 2400, (120, 80, 80, 115)),
        RemoteStep("hold far-side target", f"sleep {hold_far_seconds:.2f}"),
    ]

    for idx in range(max(1, correction_cycles)):
        steps.extend(
            [
                pose(
                    f"local correction {idx + 1} inward",
                    2180,
                    2270,
                    2240,
                    2360,
                    (90, 70, 70, 90),
                ),
                RemoteStep(f"hold correction {idx + 1} inward", "sleep 0.18"),
                pose(
                    f"local correction {idx + 1} back to target",
                    2240,
                    2260,
                    2220,
                    2410,
                    (90, 70, 70, 90),
                ),
                RemoteStep(f"hold correction {idx + 1} target", "sleep 0.25"),
            ]
        )

    if final_pose == "tabletop":
        steps.extend(
            [
                pose("settle tabletop waiting pose", 2048, 2180, 2080, 2260, (130, 80, 80, 120)),
                RemoteStep(
                    "settle functional light",
                    "python3 /home/sunrise/Desktop/send_uart3_led_cmd.py all 255 255 245 105",
                ),
            ]
        )
    else:
        steps.extend(
            [
                pose("end target-oriented at far side", 2220, 2250, 2200, 2390, (100, 70, 70, 90)),
                RemoteStep(
                    "keep light on target",
                    "python3 /home/sunrise/Desktop/send_uart3_led_cmd.py all 255 255 245 115",
                ),
            ]
        )
    return steps


def main() -> None:
    parser = build_parser("Fixed demo script 07: tabletop object follow, based on Video 08 and PDF item 4.")
    parser.add_argument("--correction-cycles", type=int, default=2)
    parser.add_argument("--hold-far-seconds", type=float, default=1.4)
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
