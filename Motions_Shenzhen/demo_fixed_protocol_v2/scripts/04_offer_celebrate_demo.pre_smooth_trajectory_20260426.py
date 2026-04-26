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


def _phase_ready() -> list[RemoteStep]:
    return [
        RemoteStep(
            "enter lively neutral pose",
            f"python3 /home/sunrise/Desktop/four_servo_control.py pose 2048 2150 2048 2130 --speeds {_speed(220)} {_speed(150)} {_speed(150)} {_speed(220)}",
        ),
        RemoteStep(
            "prime warm-good-news light",
            "python3 /home/sunrise/Desktop/send_uart3_led_cmd.py rainbow 140",
        ),
    ]


def _phase_rise() -> list[RemoteStep]:
    return [
        RemoteStep(
            "lift into celebration-ready posture",
            f"python3 /home/sunrise/Desktop/servo_12_slow_to_1800_2750.py --target-1 2400 --target-2 2880 --speed-1 {_speed(220)} --speed-2 {_speed(220)}",
        ),
        RemoteStep(
            "arrive at high centered celebration pose",
            f"python3 /home/sunrise/Desktop/four_servo_control.py pose 2048 2420 2880 2200 --speeds {_speed(240)} {_speed(185)} {_speed(185)} {_speed(210)}",
        ),
        RemoteStep("hold the reveal", _sleep(0.45)),
    ]


def _phase_upper_sway(*, party_light: str, hold_seconds: float) -> list[RemoteStep]:
    beat = max(0.18, hold_seconds / 4.0)
    return [
        RemoteStep("enter party light", _party_light_cmd(party_light, 185)),
        RemoteStep(
            "upper sway left",
            f"python3 /home/sunrise/Desktop/four_servo_control.py pose 2105 2460 2940 2360 --speeds {_speed(225)} {_speed(180)} {_speed(180)} {_speed(195)}",
        ),
        RemoteStep("hold upper-left", _sleep(beat)),
        RemoteStep(
            "return to upper center",
            f"python3 /home/sunrise/Desktop/four_servo_control.py pose 2048 2440 2900 2200 --speeds {_speed(205)} {_speed(170)} {_speed(170)} {_speed(180)}",
        ),
        RemoteStep("hold upper-center", _sleep(beat * 0.55)),
        RemoteStep(
            "upper sway right",
            f"python3 /home/sunrise/Desktop/four_servo_control.py pose 1990 2460 2940 2040 --speeds {_speed(225)} {_speed(180)} {_speed(180)} {_speed(195)}",
        ),
        RemoteStep("hold upper-right", _sleep(beat)),
        RemoteStep(
            "return to upper center again",
            f"python3 /home/sunrise/Desktop/four_servo_control.py pose 2048 2425 2860 2180 --speeds {_speed(205)} {_speed(165)} {_speed(165)} {_speed(180)}",
        ),
        RemoteStep("hold upper-center finish", _sleep(beat * 0.8)),
    ]


def _phase_lower_sway(*, party_light: str, hold_seconds: float) -> list[RemoteStep]:
    beat = max(0.18, hold_seconds / 4.0)
    return [
        RemoteStep("intensify party light", _party_light_cmd(party_light, 210)),
        RemoteStep(
            "lower sway left",
            f"python3 /home/sunrise/Desktop/four_servo_control.py pose 2090 2320 2360 2280 --speeds {_speed(210)} {_speed(170)} {_speed(170)} {_speed(185)}",
        ),
        RemoteStep("hold lower-left", _sleep(beat)),
        RemoteStep(
            "return to lower center",
            f"python3 /home/sunrise/Desktop/four_servo_control.py pose 2048 2290 2240 2180 --speeds {_speed(190)} {_speed(155)} {_speed(155)} {_speed(170)}",
        ),
        RemoteStep("hold lower-center", _sleep(beat * 0.55)),
        RemoteStep(
            "lower sway right",
            f"python3 /home/sunrise/Desktop/four_servo_control.py pose 2006 2320 2360 2080 --speeds {_speed(210)} {_speed(170)} {_speed(170)} {_speed(185)}",
        ),
        RemoteStep("hold lower-right", _sleep(beat)),
        RemoteStep(
            "return to lower center again",
            f"python3 /home/sunrise/Desktop/four_servo_control.py pose 2048 2260 2160 2140 --speeds {_speed(190)} {_speed(150)} {_speed(150)} {_speed(165)}",
        ),
        RemoteStep("hold lower-center finish", _sleep(beat * 0.9)),
    ]


def _phase_deceleration() -> list[RemoteStep]:
    return [
        RemoteStep("stop party spin and lower brightness", "python3 /home/sunrise/Desktop/send_uart3_led_cmd.py rainbow 110"),
        RemoteStep(
            "slow into almost-normal pose",
            f"python3 /home/sunrise/Desktop/four_servo_control.py pose 2048 2210 2100 2160 --speeds {_speed(150)} {_speed(120)} {_speed(120)} {_speed(135)}",
        ),
        RemoteStep("hold the first slowdown", _sleep(0.45)),
        RemoteStep(
            "settle to near-normal pose",
            f"python3 /home/sunrise/Desktop/four_servo_control.py pose 2048 2165 2050 2135 --speeds {_speed(125)} {_speed(105)} {_speed(105)} {_speed(120)}",
        ),
        RemoteStep("hold the near-normal settle", _sleep(0.35)),
        RemoteStep(
            "return to normal pose",
            f"python3 /home/sunrise/Desktop/four_servo_control.py pose 2048 2150 2048 2130 --speeds {_speed(100)} {_speed(85)} {_speed(85)} {_speed(100)}",
        ),
        RemoteStep("hold the normal pose", _sleep(0.28)),
    ]


def _phase_finish() -> list[RemoteStep]:
    return [
        RemoteStep(
            "head shake after returning to normal",
            f"python3 /home/sunrise/Desktop/servo_3_shake_2100_2000.py --cycles 1 --left 2230 --right 2050 --return-target 2130 --speed {_speed(120)} --pause {0.08 / DEFAULT_TIME_MULTIPLIER:.2f}",
        ),
        RemoteStep("hold after head shake", _sleep(0.16)),
        RemoteStep(
            "single body turn",
            f"python3 /home/sunrise/Desktop/four_servo_control.py pose 2100 2150 2048 2130 --speeds {_speed(115)} {_speed(90)} {_speed(90)} {_speed(100)}",
        ),
        RemoteStep("hold after body turn", _sleep(0.18)),
        RemoteStep(
            "return from body turn to normal",
            f"python3 /home/sunrise/Desktop/four_servo_control.py pose 2048 2150 2048 2130 --speeds {_speed(105)} {_speed(85)} {_speed(85)} {_speed(95)}",
        ),
        RemoteStep(
            "settle to warm neutral light",
            "python3 /home/sunrise/Desktop/send_uart3_led_cmd.py all 255 220 180 100",
        ),
    ]


def build_steps(*, party_light: str, hold_seconds: float) -> list[RemoteStep]:
    steps: list[RemoteStep] = []
    steps.extend(_phase_ready())
    steps.extend(_phase_rise())
    steps.extend(_phase_upper_sway(party_light=party_light, hold_seconds=hold_seconds))
    steps.extend(_phase_lower_sway(party_light=party_light, hold_seconds=hold_seconds))
    steps.extend(_phase_deceleration())
    steps.extend(_phase_finish())
    return steps


def main() -> None:
    parser = build_parser("Redesigned fixed demo script for Videos/05 + PDF copy item 5 offer celebration.")
    parser.add_argument("--party-light", choices=("spin", "rainbow"), default="spin")
    parser.add_argument("--hold-seconds", type=float, default=1.4)
    args = parser.parse_args()
    exit_from_plan(args=args, steps=build_steps(party_light=args.party_light, hold_seconds=args.hold_seconds))


if __name__ == "__main__":
    main()
