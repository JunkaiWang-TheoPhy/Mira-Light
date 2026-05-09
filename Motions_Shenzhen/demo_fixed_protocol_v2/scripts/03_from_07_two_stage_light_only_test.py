#!/usr/bin/env python3

from __future__ import annotations

from common import RemoteStep, build_parser, exit_from_plan


def led(command: str) -> str:
    return f"python3 /home/sunrise/Desktop/send_uart3_led_cmd.py {command}"


def build_steps(*, stage1_seconds: float, stage2_seconds: float, final_mode: str) -> list[RemoteStep]:
    stage1_hold = max(0.0, stage1_seconds)
    stage2_hold = max(0.0, stage2_seconds)

    steps: list[RemoteStep] = [
        RemoteStep("light-only safety note", "echo '[03-from-07 light only] no servo motion commands in this script'"),
        RemoteStep("stage 1 warm palm contact breathe", led("breathe 255 128 48 150")),
        RemoteStep("stage 1 hold warm breathe", f"sleep {stage1_hold:.2f}"),
        RemoteStep("stage 2 warm rotating palm light", led("spin 255 145 48 0 1 155")),
        RemoteStep("stage 2 hold warm rotation", f"sleep {stage2_hold:.2f}"),
    ]

    if final_mode == "breathe":
        steps.append(RemoteStep("finish in warm breathe", led("breathe 255 128 48 135")))
    elif final_mode == "steady":
        steps.append(RemoteStep("finish in steady warm light", led("all 255 180 100 120")))

    return steps


def main() -> None:
    parser = build_parser("Light-only test for scene 03 from 07: warm breathe, then continuous warm spin.")
    parser.add_argument("--stage1-seconds", type=float, default=3.5)
    parser.add_argument("--stage2-seconds", type=float, default=3.5)
    parser.add_argument("--final-mode", choices=("keep-spin", "breathe", "steady"), default="keep-spin")
    args = parser.parse_args()
    exit_from_plan(
        args=args,
        steps=build_steps(
            stage1_seconds=args.stage1_seconds,
            stage2_seconds=args.stage2_seconds,
            final_mode=args.final_mode,
        ),
    )


if __name__ == "__main__":
    main()
