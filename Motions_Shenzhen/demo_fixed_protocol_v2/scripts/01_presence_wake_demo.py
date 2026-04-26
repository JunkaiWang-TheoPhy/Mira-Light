#!/usr/bin/env python3

from __future__ import annotations

from common import RemoteStep, build_parser, exit_from_plan


def build_steps(
    *,
    light_mode: str,
    hold_high_seconds: float,
    skip_start_sleep: bool,
    final_look: str,
) -> list[RemoteStep]:
    if light_mode == "warm":
        light_cmd = "python3 /home/sunrise/Desktop/send_uart3_led_cmd.py all 255 220 180 70"
    else:
        light_cmd = "python3 /home/sunrise/Desktop/send_uart3_led_cmd.py wake 255 220 180 150"

    if final_look == "center":
        final_look_cmd = "python3 /home/sunrise/Desktop/four_servo_control.py pose 2048 2150 2048 2130 --speeds 160 90 90 160"
    else:
        # Board convention from existing scripts: servo3 > neutral points toward the left judge side.
        final_look_cmd = "python3 /home/sunrise/Desktop/four_servo_control.py pose 2365 2150 2048 2686 --speeds 120 100 100 120"

    steps: list[RemoteStep] = []
    if not skip_start_sleep:
        steps.extend(
            [
                RemoteStep("start dark", "python3 /home/sunrise/Desktop/send_uart3_led_cmd.py off"),
                RemoteStep(
                    "fold to sleep start pose",
                    "python3 /home/sunrise/Desktop/four_servo_control.py pose 2048 1821 2912 2130 --speeds 2000 320 1240 2000",
                ),
                RemoteStep("hold still before waking", "sleep 0.8"),
            ]
        )

    steps.extend(
        [
            RemoteStep("tiny warm pre-glow", "python3 /home/sunrise/Desktop/send_uart3_led_cmd.py all 255 180 120 25"),
            RemoteStep("pause before eye-open effect", "sleep 0.35"),
            RemoteStep("wake light", light_cmd),
            RemoteStep("pause for eye-open effect", "sleep 0.6"),
            RemoteStep(
                "half-awake lift",
                "python3 /home/sunrise/Desktop/four_servo_control.py pose 2048 1900 2750 2130 --speeds 220 90 180 180",
            ),
            RemoteStep("half-awake pause", "sleep 0.5"),
            RemoteStep(
                "stretch to high point",
                "python3 /home/sunrise/Desktop/four_servo_pose_delay_2.py --targets 2048 2400 1700 2130 --speeds 1000 160 380 1000 --delay-ratio 0.25",
            ),
            RemoteStep("hold high point", f"sleep {hold_high_seconds:.2f}"),
            RemoteStep(
                "long stretch accent",
                "python3 /home/sunrise/Desktop/four_servo_pose_2048_2048_2048_2780_separate.py --speed 250 --delay 0.05",
            ),
            RemoteStep(
                "settle back to normal height",
                "python3 /home/sunrise/Desktop/four_servo_control.py pose 2048 2150 2048 2130 --speeds 180 100 100 180",
            ),
            RemoteStep("pause before shiver", "sleep 0.25"),
            RemoteStep(
                "small wake shiver - vertical",
                "python3 /home/sunrise/Desktop/servo_2_nod_1900_2200.py --cycles 1 --low 1960 --high 2140 --return-target 2048 --pre-target 2130 --speed 140 --pause 0.03",
            ),
            RemoteStep(
                "small wake shiver - side",
                "python3 /home/sunrise/Desktop/servo_3_shake_2100_2000.py --cycles 1 --left 2210 --right 2050 --return-target 2130 --speed 180 --pause 0.03",
            ),
            RemoteStep("look to left-side judges", final_look_cmd),
            RemoteStep("hold left-side judge attention", "sleep 0.7"),
            RemoteStep("natural warm light", "python3 /home/sunrise/Desktop/send_uart3_led_cmd.py all 255 220 180 100"),
        ]
    )
    return steps


def main() -> None:
    parser = build_parser("Demo scene 01 v2: video-faithful presence wake.")
    parser.add_argument("--light-mode", choices=("wake", "warm"), default="wake")
    parser.add_argument("--hold-high-seconds", type=float, default=1.2)
    parser.add_argument("--skip-start-sleep", action="store_true", help="Skip the initial fold-to-sleep preparation.")
    parser.add_argument("--final-look", choices=("judge-left", "center"), default="judge-left")
    args = parser.parse_args()
    exit_from_plan(
        args=args,
        steps=build_steps(
            light_mode=args.light_mode,
            hold_high_seconds=args.hold_high_seconds,
            skip_start_sleep=args.skip_start_sleep,
            final_look=args.final_look,
        ),
    )


if __name__ == "__main__":
    main()
