#!/usr/bin/env python3

from __future__ import annotations

import importlib.util
from pathlib import Path
import sys
from types import ModuleType

from common import RemoteStep, build_parser, exit_from_plan


SCRIPT_DIR = Path(__file__).resolve().parent


def load_script_module(module_name: str, filename: str) -> ModuleType:
    path = SCRIPT_DIR / filename
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load script module: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


wake_tabletop = load_script_module("_wake_tabletop_combo", "01_07_wake_tabletop_combo_test.py")
right_hand_nuzzle = load_script_module("_right_hand_nuzzle_from_07", "03_right_hand_nuzzle_from_07_test.py")
tabletop_follow = load_script_module("_tabletop_follow_scene_07", "07_tabletop_follow_demo.py")
photo_pose = load_script_module("_photo_pose_scene_08", "08_photo_pose_demo.py")


def pause_between(label: str, seconds: float) -> RemoteStep:
    return RemoteStep(label, f"sleep {max(0.0, seconds):.2f}")


def build_steps(
    *,
    gap_after_wake_tabletop: float,
    gap_after_nuzzle: float,
    gap_after_tabletop: float,
    first_tabletop_correction_cycles: int,
    final_tabletop_correction_cycles: int,
    nuzzle_cycles: int,
    final_tabletop_hold_far_seconds: float,
    final_tabletop_pose: str,
    final_tabletop_light_brightness: int,
    photo_target_0: int,
    photo_target_1: int,
    photo_target_2: int,
    photo_target_3: int,
    photo_speed: int,
    photo_hold_seconds: float,
    photo_light_brightness: int,
    skip_start_sleep: bool,
) -> list[RemoteStep]:
    steps: list[RemoteStep] = []

    steps.extend(
        wake_tabletop.build_steps(
            correction_cycles=first_tabletop_correction_cycles,
            hold_high_seconds=0.6,
            hold_far_seconds=1.25,
            final_pose="target",
            light_brightness=125,
            skip_start_sleep=skip_start_sleep,
        )
    )
    steps.append(pause_between("intermission 01+07 to 03 right-hand nuzzle", gap_after_wake_tabletop))

    steps.extend(
        right_hand_nuzzle.build_steps(
            nuzzle_cycles=nuzzle_cycles,
            skip_start_pose=False,
        )
    )
    steps.append(pause_between("intermission 03 right-hand nuzzle to final 07 tabletop follow", gap_after_nuzzle))

    steps.extend(
        tabletop_follow.build_steps(
            correction_cycles=final_tabletop_correction_cycles,
            hold_far_seconds=max(0.0, final_tabletop_hold_far_seconds),
            final_pose=final_tabletop_pose,
            light_brightness=final_tabletop_light_brightness,
        )
    )
    steps.append(pause_between("intermission final 07 tabletop follow to 08 photo pose", gap_after_tabletop))

    steps.extend(
        photo_pose.build_steps(
            target_0=photo_target_0,
            target_1=photo_target_1,
            target_2=photo_target_2,
            target_3=photo_target_3,
            speed=photo_speed,
            hold_seconds=photo_hold_seconds,
            light_brightness=photo_light_brightness,
        )
    )

    return steps


def main() -> None:
    parser = build_parser("Combo test: 01+07 wake/tabletop, 03 right-hand nuzzle, 07 tabletop follow, then 08 photo pose.")
    parser.add_argument("--gap-after-wake-tabletop", type=float, default=3.0)
    parser.add_argument("--gap-after-nuzzle", type=float, default=5.0)
    parser.add_argument("--gap-after-tabletop", type=float, default=5.0)
    parser.add_argument("--first-tabletop-correction-cycles", type=int, default=1)
    parser.add_argument("--final-tabletop-correction-cycles", type=int, default=1)
    parser.add_argument("--nuzzle-cycles", type=int, default=2)
    parser.add_argument("--final-tabletop-hold-far-seconds", type=float, default=2.5)
    parser.add_argument("--final-tabletop-pose", choices=("target", "tabletop"), default="target")
    parser.add_argument("--final-tabletop-light-brightness", type=int, default=125)
    parser.add_argument("--photo-target-0", type=int, default=2048)
    parser.add_argument("--photo-target-1", type=int, default=1880)
    parser.add_argument("--photo-target-2", type=int, default=1650)
    parser.add_argument("--photo-target-3", type=int, default=2048)
    parser.add_argument("--photo-speed", type=int, default=340)
    parser.add_argument("--photo-hold-seconds", type=float, default=1.2)
    parser.add_argument("--photo-light-brightness", type=int, default=135)
    parser.add_argument("--skip-start-sleep", action="store_true", help="Skip the 01 initial sleep preparation.")
    args = parser.parse_args()

    exit_from_plan(
        args=args,
        steps=build_steps(
            gap_after_wake_tabletop=args.gap_after_wake_tabletop,
            gap_after_nuzzle=args.gap_after_nuzzle,
            gap_after_tabletop=args.gap_after_tabletop,
            first_tabletop_correction_cycles=args.first_tabletop_correction_cycles,
            final_tabletop_correction_cycles=args.final_tabletop_correction_cycles,
            nuzzle_cycles=args.nuzzle_cycles,
            final_tabletop_hold_far_seconds=args.final_tabletop_hold_far_seconds,
            final_tabletop_pose=args.final_tabletop_pose,
            final_tabletop_light_brightness=args.final_tabletop_light_brightness,
            photo_target_0=args.photo_target_0,
            photo_target_1=args.photo_target_1,
            photo_target_2=args.photo_target_2,
            photo_target_3=args.photo_target_3,
            photo_speed=args.photo_speed,
            photo_hold_seconds=args.photo_hold_seconds,
            photo_light_brightness=args.photo_light_brightness,
            skip_start_sleep=args.skip_start_sleep,
        ),
    )


if __name__ == "__main__":
    main()
