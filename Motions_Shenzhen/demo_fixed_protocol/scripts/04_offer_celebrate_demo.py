#!/usr/bin/env python3

from __future__ import annotations

from common import RemoteStep, build_parser, exit_from_plan


def build_steps(*, party_light: str, hold_seconds: float) -> list[RemoteStep]:
    light_cmd = (
        "python3 /home/sunrise/Desktop/send_uart3_led_cmd.py spin"
        if party_light == "spin"
        else "python3 /home/sunrise/Desktop/send_uart3_led_cmd.py rainbow 180"
    )
    return [
        RemoteStep("enter bright celebration light", "python3 /home/sunrise/Desktop/send_uart3_led_cmd.py rainbow 180"),
        RemoteStep("lift into celebrate-ready pose", "python3 /home/sunrise/Desktop/servo_12_slow_to_1800_2750.py"),
        RemoteStep("sway upward", "python3 /home/sunrise/Desktop/servo_1_3_slow_1800_2750.py"),
        RemoteStep("up-beat nod", "python3 /home/sunrise/Desktop/servo_2_nod_1900_2200.py --cycles 1"),
        RemoteStep("side excitement shake", "python3 /home/sunrise/Desktop/servo_3_shake_2100_2000.py --cycles 1"),
        RemoteStep("party-light burst", light_cmd),
        RemoteStep("hold celebration", f"sleep {hold_seconds}"),
        RemoteStep("decelerate with one nod", "python3 /home/sunrise/Desktop/servo_2_nod_1900_2200.py --cycles 1 --pause 0.08"),
        RemoteStep(
            "return to normal pose",
            "python3 /home/sunrise/Desktop/four_servo_control.py pose 2048 2150 2048 2130 --speeds 200 100 100 200",
        ),
        RemoteStep("settle to warm neutral light", "python3 /home/sunrise/Desktop/send_uart3_led_cmd.py all 255 220 180 100"),
    ]


def main() -> None:
    parser = build_parser("Fixed demo script for Videos/05 + PDF copy item 5 offer celebration.")
    parser.add_argument("--party-light", choices=("spin", "rainbow"), default="spin")
    parser.add_argument("--hold-seconds", type=float, default=1.0)
    args = parser.parse_args()
    exit_from_plan(args=args, steps=build_steps(party_light=args.party_light, hold_seconds=args.hold_seconds))


if __name__ == "__main__":
    main()
