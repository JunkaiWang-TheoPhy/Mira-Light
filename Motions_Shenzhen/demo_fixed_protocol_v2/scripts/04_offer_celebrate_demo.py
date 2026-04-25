#!/usr/bin/env python3

from __future__ import annotations

from common import RemoteStep, build_parser, exit_from_plan


def build_steps(*, party_light: str, hold_seconds: float) -> list[RemoteStep]:
    light_cmd = (
        "python3 /home/sunrise/Desktop/send_uart3_led_cmd.py spin"
        if party_light == "spin"
        else "python3 /home/sunrise/Desktop/send_uart3_led_cmd.py rainbow 200"
    )
    return [
        RemoteStep(
            "enter energetic normal pose",
            "python3 /home/sunrise/Desktop/four_servo_control.py pose 2048 2150 2048 2130 --speeds 180 100 100 180",
        ),
        RemoteStep("bright celebration light", "python3 /home/sunrise/Desktop/send_uart3_led_cmd.py rainbow 180"),
        RemoteStep(
            "rise with good-news excitement",
            "python3 /home/sunrise/Desktop/servo_12_slow_to_1800_2750.py --target-1 1880 --target-2 2600 --speed-1 140 --speed-2 140",
        ),
        RemoteStep("high-energy pause", "sleep 0.35"),
        RemoteStep(
            "up sway left",
            "python3 /home/sunrise/Desktop/servo_1_3_slow_1800_2750.py --target-1 1850 --target-3 2680 --speeds 150 150 --delay-ratio 0",
        ),
        RemoteStep(
            "up sway right",
            "python3 /home/sunrise/Desktop/servo_1_3_slow_1800_2750.py --target-1 1900 --target-3 2050 --speeds 150 150 --delay-ratio 0",
        ),
        RemoteStep(
            "up bounce",
            "python3 /home/sunrise/Desktop/servo_2_nod_1900_2200.py --cycles 1 --low 1900 --high 2200 --return-target 2048 --pre-target 2130 --speed 150 --pause 0.04",
        ),
        RemoteStep(
            "down sway left",
            "python3 /home/sunrise/Desktop/four_servo_control.py pose 2048 2240 1900 2380 --speeds 180 130 130 160",
        ),
        RemoteStep(
            "down sway right",
            "python3 /home/sunrise/Desktop/four_servo_control.py pose 2048 2240 1900 2020 --speeds 180 130 130 160",
        ),
        RemoteStep(
            "rhythmic side shake",
            "python3 /home/sunrise/Desktop/servo_3_shake_2100_2000.py --cycles 2 --left 2360 --right 1980 --return-target 2180 --speed 180 --pause 0.04",
        ),
        RemoteStep("party-light burst", light_cmd),
        RemoteStep(
            "peak dance bounce",
            "python3 /home/sunrise/Desktop/servo_2_nod_1900_2200.py --cycles 2 --low 1880 --high 2200 --return-target 2048 --pre-target 2180 --speed 170 --pause 0.03",
        ),
        RemoteStep("hold celebration peak", f"sleep {hold_seconds:.2f}"),
        RemoteStep("lower party brightness", "python3 /home/sunrise/Desktop/send_uart3_led_cmd.py rainbow 120"),
        RemoteStep(
            "decelerate smaller bounce",
            "python3 /home/sunrise/Desktop/servo_2_nod_1900_2200.py --cycles 1 --low 1980 --high 2110 --return-target 2048 --pre-target 2130 --speed 110 --pause 0.08",
        ),
        RemoteStep(
            "breath-out head shake",
            "python3 /home/sunrise/Desktop/servo_3_shake_2100_2000.py --cycles 1 --left 2240 --right 2070 --return-target 2130 --speed 110 --pause 0.08",
        ),
        RemoteStep(
            "soft body settle",
            "python3 /home/sunrise/Desktop/four_servo_control.py pose 2048 2120 2048 2130 --speeds 140 80 80 140",
        ),
        RemoteStep(
            "return to normal pose",
            "python3 /home/sunrise/Desktop/four_servo_control.py pose 2048 2150 2048 2130 --speeds 140 90 90 140",
        ),
        RemoteStep("settle to warm neutral light", "python3 /home/sunrise/Desktop/send_uart3_led_cmd.py all 255 220 180 100"),
    ]


def main() -> None:
    parser = build_parser("Fixed demo script for Videos/05 + PDF copy item 5 offer celebration.")
    parser.add_argument("--party-light", choices=("spin", "rainbow"), default="spin")
    parser.add_argument("--hold-seconds", type=float, default=1.4)
    args = parser.parse_args()
    exit_from_plan(args=args, steps=build_steps(party_light=args.party_light, hold_seconds=args.hold_seconds))


if __name__ == "__main__":
    main()
