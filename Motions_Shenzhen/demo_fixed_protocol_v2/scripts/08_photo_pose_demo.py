#!/usr/bin/env python3

from __future__ import annotations

from common import RemoteStep, build_parser, exit_from_plan


def build_steps(
    *,
    target_0: int,
    target_1: int,
    target_2: int,
    target_3: int,
    speed: int,
    hold_seconds: float,
    light_brightness: int,
) -> list[RemoteStep]:
    brightness = max(0, min(255, light_brightness))
    return [
        RemoteStep(
            "photo-ready light",
            f"python3 /home/sunrise/Desktop/send_uart3_led_cmd.py all 255 255 245 {brightness}",
        ),
        RemoteStep(
            "photo pose - joints 0 and 3 centered, joints 1 and 2 set for photo",
            (
                "python3 /home/sunrise/Desktop/four_servo_control.py "
                f"pose {target_0} {target_1} {target_2} {target_3} "
                f"--speeds {speed} {speed} {speed} {speed}"
            ),
        ),
        RemoteStep("hold photo pose", f"sleep {max(0.0, hold_seconds):.2f}"),
    ]


def main() -> None:
    parser = build_parser("Demo scene 08: photo pose, centering joints 0 and 3 while moving joints 1 and 2.")
    parser.add_argument("--target-0", type=int, default=2048, help="Joint 0 center target.")
    parser.add_argument("--target-1", type=int, default=1880, help="Joint 1 low target. Smaller means lower.")
    parser.add_argument("--target-2", type=int, default=1650, help="Joint 2 high target. Smaller means higher.")
    parser.add_argument("--target-3", type=int, default=2048, help="Joint 3 center target.")
    parser.add_argument("--speed", type=int, default=340)
    parser.add_argument("--hold-seconds", type=float, default=1.2)
    parser.add_argument("--light-brightness", type=int, default=135)
    args = parser.parse_args()
    exit_from_plan(
        args=args,
        steps=build_steps(
            target_0=args.target_0,
            target_1=args.target_1,
            target_2=args.target_2,
            target_3=args.target_3,
            speed=args.speed,
            hold_seconds=args.hold_seconds,
            light_brightness=args.light_brightness,
        ),
    )


if __name__ == "__main__":
    main()
