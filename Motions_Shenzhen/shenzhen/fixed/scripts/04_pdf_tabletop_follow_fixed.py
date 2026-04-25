#!/usr/bin/env python3

from __future__ import annotations

from common import RemoteStep, build_common_parser, exit_from_run


LEFT_TABLE_POSE = "python3 /home/sunrise/Desktop/four_servo_control.py pose 1900 2250 2200 2350 --speeds 180 120 120 180"
CENTER_TABLE_POSE = "python3 /home/sunrise/Desktop/four_servo_control.py pose 2048 2200 2100 2280 --speeds 180 120 120 180"
RIGHT_TABLE_POSE = "python3 /home/sunrise/Desktop/four_servo_control.py pose 2200 2250 2200 2350 --speeds 180 120 120 180"
WAIT_TABLE_POSE = "python3 /home/sunrise/Desktop/four_servo_control.py pose 2048 2180 2080 2260 --speeds 160 100 100 160"


def build_steps() -> list[RemoteStep]:
    return [
        RemoteStep("enter tabletop white light", "python3 /home/sunrise/Desktop/send_uart3_led_cmd.py all 255 255 255 120"),
        RemoteStep("enter tabletop pose", WAIT_TABLE_POSE),
        RemoteStep("look to left target", LEFT_TABLE_POSE),
        RemoteStep("hold left target", "sleep 0.6"),
        RemoteStep("follow to center", CENTER_TABLE_POSE),
        RemoteStep("follow to right target", RIGHT_TABLE_POSE),
        RemoteStep("hold right target", "sleep 0.8"),
        RemoteStep("follow once more", CENTER_TABLE_POSE),
        RemoteStep("settle tabletop waiting pose", WAIT_TABLE_POSE),
    ]


def main() -> None:
    parser = build_common_parser("Fixed script for Videos/04 + PDF copy item 4 tabletop follow.")
    args = parser.parse_args()
    exit_from_run(args=args, steps=build_steps())


if __name__ == "__main__":
    main()
