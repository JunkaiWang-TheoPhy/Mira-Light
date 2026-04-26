#!/usr/bin/env python3

from __future__ import annotations

from common import RemoteStep, build_parser, exit_from_plan

DEFAULT_SPEED_MULTIPLIER = 1.8
DEFAULT_TIME_MULTIPLIER = 1.0


def _speed(value: int) -> int:
    return max(1, round(value * DEFAULT_SPEED_MULTIPLIER))


def _sleep(seconds: float) -> str:
    return f"sleep {max(0.0, seconds / DEFAULT_TIME_MULTIPLIER):.2f}"


def _party_light_cmd(brightness: int) -> str:
    return f"python3 /home/sunrise/Desktop/send_uart3_led_cmd.py spin --rainbow 0 1 {brightness}"


def _pose_step(
    label: str,
    p0: int,
    p1: int,
    p2: int,
    p3: int,
    *,
    time_ms: int,
    s0: int,
    s1: int,
    s2: int,
    s3: int,
) -> RemoteStep:
    return RemoteStep(
        label,
        (
            "python3 /home/sunrise/Desktop/four_servo_control.py "
            f"pose {p0} {p1} {p2} {p3} "
            f"--time {time_ms} "
            f"--speeds {_speed(s0)} {_speed(s1)} {_speed(s2)} {_speed(s3)}"
        ),
    )


def _smooth_round(
    *,
    index: int,
    left_mid: tuple[int, int, int, int],
    left_peak: tuple[int, int, int, int],
    center: tuple[int, int, int, int],
    right_mid: tuple[int, int, int, int],
    right_peak: tuple[int, int, int, int],
) -> list[RemoteStep]:
    return [
        _pose_step(
            f"round {index} left glide in",
            *left_mid,
            time_ms=180,
            s0=260,
            s1=190,
            s2=215,
            s3=190,
        ),
        RemoteStep(f"round {index} left glide buffer", _sleep(0.08)),
        _pose_step(
            f"round {index} left peak",
            *left_peak,
            time_ms=220,
            s0=290,
            s1=205,
            s2=240,
            s3=205,
        ),
        RemoteStep(f"round {index} left peak hold", _sleep(0.10)),
        _pose_step(
            f"round {index} left glide out",
            *left_mid,
            time_ms=170,
            s0=250,
            s1=185,
            s2=210,
            s3=185,
        ),
        RemoteStep(f"round {index} center transition from left", _sleep(0.06)),
        _pose_step(
            f"round {index} obvious center",
            *center,
            time_ms=210,
            s0=235,
            s1=180,
            s2=205,
            s3=180,
        ),
        RemoteStep(f"round {index} center hold", _sleep(0.18)),
        _pose_step(
            f"round {index} right glide in",
            *right_mid,
            time_ms=180,
            s0=260,
            s1=190,
            s2=215,
            s3=190,
        ),
        RemoteStep(f"round {index} right glide buffer", _sleep(0.08)),
        _pose_step(
            f"round {index} right peak",
            *right_peak,
            time_ms=220,
            s0=290,
            s1=205,
            s2=240,
            s3=205,
        ),
        RemoteStep(f"round {index} right peak hold", _sleep(0.10)),
        _pose_step(
            f"round {index} right glide out",
            *right_mid,
            time_ms=170,
            s0=250,
            s1=185,
            s2=210,
            s3=185,
        ),
        RemoteStep(f"round {index} center transition from right", _sleep(0.06)),
        _pose_step(
            f"round {index} obvious center reset",
            *center,
            time_ms=210,
            s0=235,
            s1=180,
            s2=205,
            s3=180,
        ),
        RemoteStep(f"round {index} center reset hold", _sleep(0.18)),
    ]


def build_steps() -> list[RemoteStep]:
    high_center = (2048, 2520, 2300, 2200)
    center_high = (2048, 2360, 2160, 2130)
    left_mid_high = (1760, 2480, 2230, 2240)
    right_mid_high = (2330, 2480, 2230, 2090)
    left_peak_high = (1560, 2600, 2200, 2280)
    right_peak_high = (2535, 2600, 2200, 2040)

    center_low = (2048, 2000, 1700, 2130)
    left_mid_low = (1760, 2060, 1760, 2240)
    right_mid_low = (2330, 2060, 1760, 2090)
    left_peak_low = (1560, 2100, 1700, 2280)
    right_peak_low = (2535, 2100, 1700, 2040)

    steps = [
        _pose_step(
            "enter lively neutral pose",
            2048,
            2150,
            2048,
            2130,
            time_ms=220,
            s0=220,
            s1=150,
            s2=150,
            s3=220,
        ),
        RemoteStep("prime warm-good-news light", "python3 /home/sunrise/Desktop/send_uart3_led_cmd.py rainbow 140"),
        _pose_step(
            "single-step rise into high centered celebration pose",
            *high_center,
            time_ms=280,
            s0=225,
            s1=180,
            s2=205,
            s3=210,
        ),
        RemoteStep("hold the reveal", _sleep(0.28)),
        RemoteStep("enter party light", _party_light_cmd(185)),
    ]

    steps.extend(
        _smooth_round(
            index=1,
            left_mid=left_mid_high,
            left_peak=left_peak_high,
            center=center_high,
            right_mid=right_mid_high,
            right_peak=right_peak_high,
        )
    )
    steps.extend(
        _smooth_round(
            index=2,
            left_mid=left_mid_high,
            left_peak=left_peak_high,
            center=center_high,
            right_mid=right_mid_high,
            right_peak=right_peak_high,
        )
    )
    steps.extend(
        _smooth_round(
            index=3,
            left_mid=left_mid_low,
            left_peak=left_peak_low,
            center=center_low,
            right_mid=right_mid_low,
            right_peak=right_peak_low,
        )
    )
    steps.extend(
        _smooth_round(
            index=4,
            left_mid=left_mid_low,
            left_peak=left_peak_low,
            center=center_low,
            right_mid=right_mid_low,
            right_peak=right_peak_low,
        )
    )

    steps.extend(
        [
            RemoteStep("lower party brightness", "python3 /home/sunrise/Desktop/send_uart3_led_cmd.py rainbow 110"),
            _pose_step(
                "return to normal pose",
                2048,
                2150,
                2048,
                2130,
                time_ms=260,
                s0=160,
                s1=125,
                s2=125,
                s3=160,
            ),
            RemoteStep("settle to warm neutral light", "python3 /home/sunrise/Desktop/send_uart3_led_cmd.py all 255 220 180 100"),
        ]
    )
    return steps


def main() -> None:
    parser = build_parser("Smooth trajectory celebration test with four flowing left-center-right rounds.")
    parser.parse_args()
    args = parser.parse_args()
    exit_from_plan(args=args, steps=build_steps())


if __name__ == "__main__":
    main()
