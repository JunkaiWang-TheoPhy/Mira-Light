#!/usr/bin/env python3

from __future__ import annotations

from common import RemoteStep, build_parser, exit_from_plan

DEFAULT_SPEED_MULTIPLIER = 1.5
DEFAULT_TIME_MULTIPLIER = 1.5


def _speed(value: int) -> int:
    return max(1, round(value * DEFAULT_SPEED_MULTIPLIER))


def _sleep(seconds: float) -> str:
    return f"sleep {max(0.0, seconds / DEFAULT_TIME_MULTIPLIER):.2f}"


def _party_light_cmd(party_light: str, brightness: int) -> str:
    if party_light == "spin":
        return f"python3 /home/sunrise/Desktop/send_uart3_led_cmd.py spin --rainbow 0 1 {brightness}"
    return f"python3 /home/sunrise/Desktop/send_uart3_led_cmd.py rainbow {brightness}"


def build_steps(*, party_light: str) -> list[RemoteStep]:
    return [
        RemoteStep(
            "enter lively neutral pose",
            f"python3 /home/sunrise/Desktop/four_servo_control.py pose 2048 2150 2048 2130 --speeds {_speed(220)} {_speed(150)} {_speed(150)} {_speed(220)}",
        ),
        RemoteStep(
            "prime warm-good-news light",
            "python3 /home/sunrise/Desktop/send_uart3_led_cmd.py rainbow 140",
        ),
        RemoteStep(
            "single-step rise into high centered celebration pose",
            f"python3 /home/sunrise/Desktop/four_servo_control.py pose 2048 2520 2300 2200 --speeds {_speed(225)} {_speed(180)} {_speed(205)} {_speed(210)}",
        ),
        RemoteStep("hold the reveal", _sleep(0.45)),
        RemoteStep("enter party light", _party_light_cmd(party_light, 185)),
        RemoteStep(
            "upper sway left only",
            f"python3 /home/sunrise/Desktop/four_servo_control.py pose 1560 2600 2200 2280 --speeds {_speed(270)} {_speed(175)} {_speed(230)} {_speed(175)}",
        ),
        RemoteStep("hold upper-left", _sleep(0.35)),
        RemoteStep(
            "return to upper center",
            f"python3 /home/sunrise/Desktop/four_servo_control.py pose 2048 2540 2240 2200 --speeds {_speed(215)} {_speed(170)} {_speed(215)} {_speed(180)}",
        ),
        RemoteStep("hold upper-center", _sleep(0.35)),
        RemoteStep(
            "return to normal pose",
            f"python3 /home/sunrise/Desktop/four_servo_control.py pose 2048 2150 2048 2130 --speeds {_speed(135)} {_speed(110)} {_speed(110)} {_speed(135)}",
        ),
        RemoteStep(
            "settle to warm neutral light",
            "python3 /home/sunrise/Desktop/send_uart3_led_cmd.py all 255 220 180 100",
        ),
    ]


def main() -> None:
    parser = build_parser("Single left-up celebration round test derived from Videos/05.")
    parser.add_argument("--party-light", choices=("spin", "rainbow"), default="spin")
    args = parser.parse_args()
    exit_from_plan(args=args, steps=build_steps(party_light=args.party_light))


if __name__ == "__main__":
    main()
