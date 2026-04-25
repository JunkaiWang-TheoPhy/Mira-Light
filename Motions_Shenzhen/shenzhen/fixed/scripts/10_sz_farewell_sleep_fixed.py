#!/usr/bin/env python3

from __future__ import annotations

from common import RemoteStep, build_common_parser, exit_from_run


def build_steps() -> list[RemoteStep]:
    return [
        RemoteStep("look and wave goodbye", "python3 /home/sunrise/Desktop/four_servo_pose_delay_2_return_12_head_turn_once.py"),
        RemoteStep("hold farewell gaze", "sleep 0.8"),
        RemoteStep("begin sleep fold", "python3 /home/sunrise/Desktop/sleep_motion.py --speeds 1000 160 680 1000 --delay-ratio 0.68"),
        RemoteStep("finish 0/3 return", "python3 /home/sunrise/Desktop/sleep_motion_with_03_return.py"),
        RemoteStep("lights off", "python3 /home/sunrise/Desktop/send_uart3_led_cmd.py off"),
    ]


def main() -> None:
    parser = build_common_parser("Fixed Shenzhen scene: farewell sleep.")
    args = parser.parse_args()
    exit_from_run(args=args, steps=build_steps())


if __name__ == "__main__":
    main()
