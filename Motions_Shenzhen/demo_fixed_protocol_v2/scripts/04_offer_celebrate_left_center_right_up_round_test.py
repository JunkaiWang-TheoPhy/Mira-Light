#!/usr/bin/env python3

from __future__ import annotations

from common import RemoteStep, build_parser, exit_from_plan

DEFAULT_SPEED_MULTIPLIER = 1.8
DEFAULT_TIME_MULTIPLIER = 1.8


def _speed(value: int) -> int:
    return max(1, round(value * DEFAULT_SPEED_MULTIPLIER))


def _sleep(seconds: float) -> str:
    return f"sleep {max(0.0, seconds / DEFAULT_TIME_MULTIPLIER):.2f}"


def _party_light_cmd(party_light: str, brightness: int) -> str:
    if party_light == "spin":
        return f"python3 /home/sunrise/Desktop/send_uart3_led_cmd.py spin --rainbow 0 1 {brightness}"
    return f"python3 /home/sunrise/Desktop/send_uart3_led_cmd.py rainbow {brightness}"


def _upper_round(
    *,
    index: int,
    left_p0: int,
    side_p1: int,
    side_p2: int,
    center_p1: int,
    center_p2: int,
    right_p0: int,
) -> list[RemoteStep]:
    return [
        RemoteStep(
            f"upper sway left round {index}",
            f"python3 /home/sunrise/Desktop/four_servo_control.py pose {left_p0} {side_p1} {side_p2} 2280 --speeds {_speed(270)} {_speed(175)} {_speed(230)} {_speed(175)}",
        ),
        RemoteStep(f"hold upper-left round {index}", _sleep(0.30)),
        RemoteStep(
            f"return to upper center after left round {index}",
            f"python3 /home/sunrise/Desktop/four_servo_control.py pose 2048 {center_p1} {center_p2} 2130 --speeds {_speed(215)} {_speed(165)} {_speed(200)} {_speed(175)}",
        ),
        RemoteStep(f"hold obvious center after left round {index}", _sleep(0.55)),
        RemoteStep(
            f"upper sway right round {index}",
            f"python3 /home/sunrise/Desktop/four_servo_control.py pose {right_p0} {side_p1} {side_p2} 2040 --speeds {_speed(270)} {_speed(175)} {_speed(230)} {_speed(175)}",
        ),
        RemoteStep(f"hold upper-right round {index}", _sleep(0.30)),
        RemoteStep(
            f"return to upper center after right round {index}",
            f"python3 /home/sunrise/Desktop/four_servo_control.py pose 2048 {center_p1} {center_p2} 2130 --speeds {_speed(215)} {_speed(165)} {_speed(200)} {_speed(175)}",
        ),
        RemoteStep(f"hold obvious center after right round {index}", _sleep(0.55)),
    ]


def build_steps(*, party_light: str) -> list[RemoteStep]:
    steps = [
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
            "return to normal pose",
            f"python3 /home/sunrise/Desktop/four_servo_control.py pose 2048 2150 2048 2130 --speeds {_speed(135)} {_speed(110)} {_speed(110)} {_speed(135)}",
        ),
        RemoteStep(
            "settle to warm neutral light",
            "python3 /home/sunrise/Desktop/send_uart3_led_cmd.py all 255 220 180 100",
        ),
    ]
    steps[5:5] = (
        _upper_round(
            index=1,
            left_p0=1560,
            right_p0=2535,
            side_p1=2600,
            side_p2=2200,
            center_p1=2360,
            center_p2=2160,
        )
        + _upper_round(
            index=2,
            left_p0=1560,
            right_p0=2535,
            side_p1=2600,
            side_p2=2200,
            center_p1=2360,
            center_p2=2160,
        )
        + _upper_round(
            index=3,
            left_p0=1560,
            right_p0=2535,
            side_p1=2100,
            side_p2=1700,
            center_p1=2000,
            center_p2=1700,
        )
        + _upper_round(
            index=4,
            left_p0=1560,
            right_p0=2535,
            side_p1=2100,
            side_p2=1700,
            center_p1=2000,
            center_p2=1700,
        )
    )
    return steps


def main() -> None:
    parser = build_parser("Continuous left-up to center to right-up celebration round test.")
    parser.add_argument("--party-light", choices=("spin", "rainbow"), default="spin")
    args = parser.parse_args()
    exit_from_plan(args=args, steps=build_steps(party_light=args.party_light))


if __name__ == "__main__":
    main()
