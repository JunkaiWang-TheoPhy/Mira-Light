#!/usr/bin/env python3

from __future__ import annotations

from common import RemoteStep, build_parser, exit_from_plan


def led(command: str) -> str:
    return f"python3 /home/sunrise/Desktop/send_uart3_led_cmd.py {command}"


def build_steps(*, linger_seconds: float, pulse_cycles: int) -> list[RemoteStep]:
    linger = max(0.0, linger_seconds)
    cycles = max(1, min(pulse_cycles, 6))

    steps: list[RemoteStep] = [
        RemoteStep("light-only safety note", "echo '[light only] no servo motion commands in this script'"),
        RemoteStep("stage 1 warm palm contact breathe", led("breathe 255 128 48 150")),
        RemoteStep("stage 1 hold warm breathe", f"sleep {linger:.2f}"),
    ]

    for idx in range(cycles):
        cycle = idx + 1
        steps.extend(
            [
                RemoteStep(f"stage 2 pulse {cycle} bright warm", led("all 255 118 42 200")),
                RemoteStep(f"stage 2 pulse {cycle} bright hold", "sleep 0.18"),
                RemoteStep(f"stage 2 pulse {cycle} soft dim", led("all 255 168 86 120")),
                RemoteStep(f"stage 2 pulse {cycle} dim hold", "sleep 0.18"),
                RemoteStep(f"stage 2 pulse {cycle} light spin sparkle", led("spin 255 145 48 0 1 160")),
                RemoteStep(f"stage 2 pulse {cycle} spin hold", "sleep 0.28"),
                RemoteStep(f"stage 2 pulse {cycle} return warm breathe", led("breathe 255 128 48 145")),
                RemoteStep(f"stage 2 pulse {cycle} breathe hold", "sleep 0.20"),
            ]
        )

    return steps


def main() -> None:
    parser = build_parser("Light-only test for scene 03 hand nuzzle with two warm lighting stages.")
    parser.add_argument("--linger-seconds", type=float, default=3.5)
    parser.add_argument("--pulse-cycles", type=int, default=2)
    args = parser.parse_args()
    exit_from_plan(
        args=args,
        steps=build_steps(
            linger_seconds=args.linger_seconds,
            pulse_cycles=args.pulse_cycles,
        ),
    )


if __name__ == "__main__":
    main()
