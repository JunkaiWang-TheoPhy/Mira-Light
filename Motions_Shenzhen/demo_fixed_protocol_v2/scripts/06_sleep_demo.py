#!/usr/bin/env python3

from __future__ import annotations

from common import RemoteStep, build_parser, exit_from_plan


def build_steps(*, lights_off: bool, lead_sleep_only: bool, rest_seconds: float) -> list[RemoteStep]:
    steps: list[RemoteStep] = [
        RemoteStep(
            "enter attentive end pose",
            "python3 /home/sunrise/Desktop/four_servo_control.py pose 2048 2180 1980 2240 --speeds 160 90 90 120",
        ),
        RemoteStep("soft warm pre-sleep light", "python3 /home/sunrise/Desktop/send_uart3_led_cmd.py all 255 220 180 95"),
        RemoteStep("hold attentive before sleep", "sleep 0.7"),
        RemoteStep(
            "settle through mid pose",
            "python3 /home/sunrise/Desktop/four_servo_control.py pose 2048 2100 2380 2200 --speeds 140 80 130 110",
        ),
        RemoteStep("hold mid transition", "sleep 0.6"),
        RemoteStep(
            "lower and extend slowly",
            "python3 /home/sunrise/Desktop/four_servo_control.py pose 2048 1980 2780 2180 --speeds 130 70 120 100",
        ),
        RemoteStep("dim while lowering", "python3 /home/sunrise/Desktop/send_uart3_led_cmd.py all 255 205 155 70"),
        RemoteStep("hold low extension", "sleep 0.5"),
        RemoteStep(
            "small relax stretch before curling",
            "python3 /home/sunrise/Desktop/four_servo_control.py pose 2048 2070 2580 2240 --speeds 120 70 100 90",
        ),
        RemoteStep("pause after stretch", "sleep 0.45"),
        RemoteStep(
            "begin staged sleep curl",
            "python3 /home/sunrise/Desktop/sleep_motion.py --speeds 1000 160 680 1000 --delay-ratio 0.68 --hold-0 2048 --hold-3 2130",
        ),
    ]
    if not lead_sleep_only:
        steps.append(
            RemoteStep(
                "finish full sleep fold",
                "python3 /home/sunrise/Desktop/sleep_motion_with_03_return.py --speeds 1000 160 680 1000 --delay-ratio 0.68 --return03-ratio 0.25 --return-0 2048 --return-3 2130",
            )
        )
    steps.extend(
        [
            RemoteStep("dim to sleep glow", "python3 /home/sunrise/Desktop/send_uart3_led_cmd.py all 255 180 120 20"),
            RemoteStep("rest hold in final sleep pose", f"sleep {rest_seconds:.2f}"),
        ]
    )
    if lights_off:
        steps.extend(
            [
                RemoteStep("fade to almost off", "python3 /home/sunrise/Desktop/send_uart3_led_cmd.py all 255 180 120 8"),
                RemoteStep("lights off", "python3 /home/sunrise/Desktop/send_uart3_led_cmd.py off"),
            ]
        )
    return steps


def main() -> None:
    parser = build_parser("Fixed demo script 06: sleepy settle-down and final sleep fold.")
    parser.add_argument("--lights-off", action="store_true", help="Turn the light fully off after the low sleep glow.")
    parser.add_argument(
        "--lead-sleep-only",
        action="store_true",
        help="Only run the first staged sleep step and skip the final 0/3 return step.",
    )
    parser.add_argument("--rest-seconds", type=float, default=1.5, help="Hold time in the final sleep pose.")
    args = parser.parse_args()
    exit_from_plan(
        args=args,
        steps=build_steps(lights_off=args.lights_off, lead_sleep_only=args.lead_sleep_only, rest_seconds=args.rest_seconds),
    )


if __name__ == "__main__":
    main()
