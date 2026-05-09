#!/usr/bin/env python3

from __future__ import annotations

from common import RemoteStep, build_parser, exit_from_plan


SOURCE_03_END_POSE = (2480, 2200, 2300, 2260)
INITIAL_POSE = (2200, 2182, 2783, 2131)
SWING_POSE = (2900, 2182, 2783, 2131)
RETURN_POSE = INITIAL_POSE


def pose(label: str, positions: tuple[int, int, int, int], speeds: tuple[int, int, int, int]) -> RemoteStep:
    p0, p1, p2, p3 = positions
    s0, s1, s2, s3 = speeds
    return RemoteStep(
        label,
        f"python3 /home/sunrise/Desktop/four_servo_control.py pose {p0} {p1} {p2} {p3} --speeds {s0} {s1} {s2} {s3}",
    )


def build_steps(
    *,
    correction_cycles: int = 1,
    hold_far_seconds: float = 2.5,
    final_pose: str = "target",
    light_brightness: int = 125,
    speed_0: int = 440,
    transition_seconds: float = 0.25,
    settle_seconds: float = 0.6,
    out_hold_seconds: float = 1.8,
    return_hold_seconds: float = 0.8,
    skip_transition_pose: bool = False,
) -> list[RemoteStep]:
    del correction_cycles, hold_far_seconds, final_pose
    speed_0 = max(1, speed_0)
    brightness = max(0, min(255, light_brightness))
    steps: list[RemoteStep] = [
        RemoteStep(
            "07 replacement warm tabletop light",
            f"python3 /home/sunrise/Desktop/send_uart3_led_cmd.py all 255 255 245 {brightness}",
        ),
        RemoteStep(
            "07 replacement safety note",
            "echo '[07-replacement] from 03 end 2480/2200/2300/2260 to 2200/2182/2783/2131, then servo 00 swings to 2900 and back once'",
        ),
    ]

    if not skip_transition_pose:
        steps.extend(
            [
                pose("07 replacement mark source 03 real end pose", SOURCE_03_END_POSE, (160, 100, 130, 140)),
                RemoteStep("07 replacement hold source 03 end pose", f"sleep {max(0.0, transition_seconds):.2f}"),
                pose("07 replacement transition to base00 swing start", INITIAL_POSE, (220, 120, 180, 160)),
                RemoteStep("07 replacement settle base00 swing start pose", f"sleep {max(0.0, settle_seconds):.2f}"),
            ]
        )

    steps.extend(
        [
            pose("07 replacement servo 00 swing out to 2900", SWING_POSE, (speed_0, 80, 80, 80)),
            RemoteStep("07 replacement hold swing out until servo 00 can reach 2900", f"sleep {max(0.0, out_hold_seconds):.2f}"),
            pose("07 replacement servo 00 swing back to 2200", RETURN_POSE, (speed_0, 80, 80, 80)),
            RemoteStep("07 replacement hold returned pose", f"sleep {max(0.0, return_hold_seconds):.2f}"),
        ]
    )

    return steps


def main() -> None:
    parser = build_parser("Replacement demo script 07: transition from 03 end pose, then swing servo 00 once.")
    parser.add_argument("--correction-cycles", type=int, default=1, help="Compatibility option; ignored by this replacement.")
    parser.add_argument("--hold-far-seconds", type=float, default=2.5, help="Compatibility option; ignored by this replacement.")
    parser.add_argument("--final-pose", choices=("target", "tabletop"), default="target", help="Compatibility option; ignored.")
    parser.add_argument("--light-brightness", type=int, default=125)
    parser.add_argument("--speed-0", type=int, default=440, help="Servo 00 speed for the out-and-back swing.")
    parser.add_argument("--transition-seconds", type=float, default=0.25, help="Pause after marking the source 03 end pose.")
    parser.add_argument("--settle-seconds", type=float, default=0.6, help="Pause after reaching the swing start pose.")
    parser.add_argument("--out-hold-seconds", type=float, default=1.8, help="Pause after commanding servo 00 to 2900.")
    parser.add_argument("--return-hold-seconds", type=float, default=0.8, help="Pause after commanding servo 00 back to 2200.")
    parser.add_argument("--hold-seconds", type=float, default=None, help="Compatibility alias: set both out/return holds.")
    parser.add_argument("--skip-transition-pose", action="store_true", help="Assume the lamp is already at 2200/2182/2783/2131.")
    args = parser.parse_args()
    out_hold_seconds = args.hold_seconds if args.hold_seconds is not None else args.out_hold_seconds
    return_hold_seconds = args.hold_seconds if args.hold_seconds is not None else args.return_hold_seconds
    exit_from_plan(
        args=args,
        steps=build_steps(
            correction_cycles=args.correction_cycles,
            hold_far_seconds=args.hold_far_seconds,
            final_pose=args.final_pose,
            light_brightness=args.light_brightness,
            speed_0=args.speed_0,
            transition_seconds=args.transition_seconds,
            settle_seconds=args.settle_seconds,
            out_hold_seconds=out_hold_seconds,
            return_hold_seconds=return_hold_seconds,
            skip_transition_pose=args.skip_transition_pose,
        ),
    )


if __name__ == "__main__":
    main()
