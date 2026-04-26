#!/usr/bin/env python3

from __future__ import annotations

from common import RemoteStep, build_parser, exit_from_plan


def build_steps(*, party_light: str, hold_seconds: float) -> list[RemoteStep]:
    light_cmd = (
        "python3 /home/sunrise/Desktop/send_uart3_led_cmd.py spin --rainbow"
        if party_light == "spin"
        else "python3 /home/sunrise/Desktop/send_uart3_led_cmd.py rainbow 200"
    )
    return [
        RemoteStep(
            "enter energetic normal pose",
            "python3 /home/sunrise/Desktop/four_servo_control.py pose 2048 2150 2048 2130 --speeds 405 225 225 405",
        ),
        RemoteStep("bright celebration light", "python3 /home/sunrise/Desktop/send_uart3_led_cmd.py rainbow 180"),
        RemoteStep(
            "rise with good-news excitement",
            "python3 /home/sunrise/Desktop/servo_12_slow_to_1800_2750.py --target-1 2540 --target-2 3152 --speed-1 315 --speed-2 315",
        ),
        RemoteStep(
            "base twist during rise",
            "python3 /home/sunrise/Desktop/four_servo_control.py pose 1888 2540 3152 2130 --speeds 430 292 292 360",
        ),
        RemoteStep("high-energy pause", "sleep 0.35"),
        RemoteStep(
            "up sway left",
            "python3 /home/sunrise/Desktop/servo_1_3_slow_1800_2750.py --target-1 2570 --target-3 3230 --speeds 338 338 --delay-ratio 0",
        ),
        RemoteStep(
            "base twist through left sway",
            "python3 /home/sunrise/Desktop/four_servo_control.py pose 2220 2570 3152 3230 --speeds 450 315 292 405",
        ),
        RemoteStep(
            "up sway right",
            "python3 /home/sunrise/Desktop/servo_1_3_slow_1800_2750.py --target-1 2520 --target-3 1970 --speeds 338 338 --delay-ratio 0",
        ),
        RemoteStep(
            "base twist through right sway",
            "python3 /home/sunrise/Desktop/four_servo_control.py pose 1888 2520 3152 1970 --speeds 450 315 292 405",
        ),
        RemoteStep(
            "up bounce",
            "python3 /home/sunrise/Desktop/servo_2_nod_1900_2200.py --cycles 1 --low 1752 --high 2352 --return-target 2048 --pre-target 2130 --speed 338 --pause 0.04",
        ),
        RemoteStep(
            "base twist after bounce",
            "python3 /home/sunrise/Desktop/four_servo_control.py pose 2220 2520 2048 2130 --speeds 430 292 292 382",
        ),
        RemoteStep(
            "down sway left",
            "python3 /home/sunrise/Desktop/four_servo_control.py pose 1900 2200 1752 2630 --speeds 405 292 292 360",
        ),
        RemoteStep(
            "down sway right",
            "python3 /home/sunrise/Desktop/four_servo_control.py pose 2200 2200 1752 1910 --speeds 405 292 292 360",
        ),
        RemoteStep(
            "rhythmic side shake",
            "python3 /home/sunrise/Desktop/servo_3_shake_2100_2000.py --cycles 2 --left 2540 --right 1780 --return-target 2180 --speed 405 --pause 0.04",
        ),
        RemoteStep(
            "base twist after side shake",
            "python3 /home/sunrise/Desktop/four_servo_control.py pose 1888 2200 1752 2180 --speeds 450 292 292 405",
        ),
        RemoteStep("party-light burst", light_cmd),
        RemoteStep(
            "base twist left",
            "python3 /home/sunrise/Desktop/four_servo_control.py pose 1888 2540 1752 2380 --speeds 450 315 292 405",
        ),
        RemoteStep(
            "base twist right",
            "python3 /home/sunrise/Desktop/four_servo_control.py pose 2220 2540 1752 1980 --speeds 450 315 292 405",
        ),
        RemoteStep(
            "base twist rebound",
            "python3 /home/sunrise/Desktop/four_servo_control.py pose 1920 2520 1752 2320 --speeds 430 292 292 382",
        ),
        RemoteStep(
            "base twist center",
            "python3 /home/sunrise/Desktop/four_servo_control.py pose 2048 2540 1752 2180 --speeds 405 292 292 360",
        ),
        RemoteStep(
            "peak dance bounce",
            "python3 /home/sunrise/Desktop/servo_2_nod_1900_2200.py --cycles 2 --low 1712 --high 2352 --return-target 2048 --pre-target 2180 --speed 382 --pause 0.03",
        ),
        RemoteStep(
            "hold celebration peak twist left",
            "python3 /home/sunrise/Desktop/four_servo_control.py pose 1888 2540 2048 2380 --speeds 430 292 292 382",
        ),
        RemoteStep("hold celebration peak beat", f"sleep {max(0.0, hold_seconds / 4):.2f}"),
        RemoteStep(
            "hold celebration peak twist right",
            "python3 /home/sunrise/Desktop/four_servo_control.py pose 2220 2540 2048 1980 --speeds 430 292 292 382",
        ),
        RemoteStep("hold celebration peak beat", f"sleep {max(0.0, hold_seconds / 4):.2f}"),
        RemoteStep(
            "hold celebration peak twist left again",
            "python3 /home/sunrise/Desktop/four_servo_control.py pose 1900 2520 2048 2320 --speeds 405 292 292 360",
        ),
        RemoteStep("hold celebration peak beat", f"sleep {max(0.0, hold_seconds / 4):.2f}"),
        RemoteStep(
            "hold celebration peak twist center",
            "python3 /home/sunrise/Desktop/four_servo_control.py pose 2048 2520 2048 2180 --speeds 382 270 270 338",
        ),
        RemoteStep("hold celebration peak beat", f"sleep {max(0.0, hold_seconds / 4):.2f}"),
        RemoteStep("lower party brightness", "python3 /home/sunrise/Desktop/send_uart3_led_cmd.py rainbow 120"),
        RemoteStep(
            "decelerate smaller bounce",
            "python3 /home/sunrise/Desktop/servo_2_nod_1900_2200.py --cycles 1 --low 1912 --high 2172 --return-target 2048 --pre-target 2130 --speed 248 --pause 0.08",
        ),
        RemoteStep(
            "decelerate base twist",
            "python3 /home/sunrise/Desktop/four_servo_control.py pose 2180 2180 2048 2130 --speeds 292 180 180 292",
        ),
        RemoteStep(
            "breath-out head shake",
            "python3 /home/sunrise/Desktop/servo_3_shake_2100_2000.py --cycles 1 --left 2350 --right 2010 --return-target 2130 --speed 248 --pause 0.08",
        ),
        RemoteStep(
            "final small base twist",
            "python3 /home/sunrise/Desktop/four_servo_control.py pose 1940 2180 2048 2130 --speeds 270 160 160 270",
        ),
        RemoteStep(
            "soft body settle",
            "python3 /home/sunrise/Desktop/four_servo_control.py pose 2048 2180 2048 2130 --speeds 315 180 180 315",
        ),
        RemoteStep(
            "return to normal pose",
            "python3 /home/sunrise/Desktop/four_servo_control.py pose 2048 2150 2048 2130 --speeds 315 202 202 315",
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
