#!/usr/bin/env python3

from __future__ import annotations

from common import RemoteStep, build_parser, exit_from_plan


def build_steps(*, target_1: int, target_2: int, speed: int, hold_seconds: float, light_brightness: int) -> list[RemoteStep]:
    brightness = max(0, min(255, light_brightness))
    return [
        RemoteStep(
            "photo-ready light",
            f"python3 /home/sunrise/Desktop/send_uart3_led_cmd.py all 255 255 245 {brightness}",
        ),
        RemoteStep(
            "photo pose - joint 1 low and joint 2 high",
            (
                "python3 /home/sunrise/Desktop/servo_1_2_lean_forward_2148_1848.py "
                f"--target-1 {target_1} --target-2 {target_2} --speed {speed}"
            ),
        ),
        RemoteStep("hold photo pose", f"sleep {max(0.0, hold_seconds):.2f}"),
    ]


def main() -> None:
    parser = build_parser("Demo scene 08: photo pose, only moving joints 1 and 2.")
    parser.add_argument("--target-1", type=int, default=1880, help="Joint 1 low target. Smaller means lower.")
    parser.add_argument("--target-2", type=int, default=1650, help="Joint 2 high target. Smaller means higher.")
    parser.add_argument("--speed", type=int, default=170)
    parser.add_argument("--hold-seconds", type=float, default=1.2)
    parser.add_argument("--light-brightness", type=int, default=135)
    args = parser.parse_args()
    exit_from_plan(
        args=args,
        steps=build_steps(
            target_1=args.target_1,
            target_2=args.target_2,
            speed=args.speed,
            hold_seconds=args.hold_seconds,
            light_brightness=args.light_brightness,
        ),
    )


if __name__ == "__main__":
    main()
