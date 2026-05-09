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


combo_01_07_03_offer = load_script_module("_combo_01_07_03_offer", "01_07_03_offer_combo_test.py")
tabletop_follow = load_script_module("_tabletop_follow_scene_07", "07_tabletop_follow_demo.py")


def pause_between(label: str, seconds: float) -> RemoteStep:
    return RemoteStep(label, f"sleep {max(0.0, seconds):.2f}")


def build_steps(
    *,
    scene_gap_seconds: float,
    tabletop_gap_seconds: float,
    correction_cycles: int,
    final_tabletop_correction_cycles: int,
    nuzzle_cycles: int,
    party_light: str,
    offer_hold_seconds: float,
    final_tabletop_hold_far_seconds: float,
    final_tabletop_pose: str,
    final_tabletop_light_brightness: int,
    skip_start_sleep: bool,
) -> list[RemoteStep]:
    steps: list[RemoteStep] = []

    steps.extend(
        combo_01_07_03_offer.build_steps(
            gap_seconds=scene_gap_seconds,
            correction_cycles=correction_cycles,
            nuzzle_cycles=nuzzle_cycles,
            party_light=party_light,
            offer_hold_seconds=offer_hold_seconds,
            skip_start_sleep=skip_start_sleep,
        )
    )

    steps.append(pause_between("intermission after offer celebration before final 07 tabletop follow", tabletop_gap_seconds))

    steps.extend(
        tabletop_follow.build_steps(
            correction_cycles=final_tabletop_correction_cycles,
            hold_far_seconds=max(0.0, final_tabletop_hold_far_seconds),
            final_pose=final_tabletop_pose,
            light_brightness=final_tabletop_light_brightness,
        )
    )

    return steps


def main() -> None:
    parser = build_parser(
        "Combo test: 01+07 wake/tabletop, 03 right-hand nuzzle, 04 offer celebration, then final 07 tabletop follow."
    )
    parser.add_argument("--scene-gap-seconds", type=float, default=3.0, help="Pause inside the first 01+07/03/04 combo.")
    parser.add_argument("--tabletop-gap-seconds", type=float, default=10.0, help="Pause after offer before the final 07.")
    parser.add_argument("--correction-cycles", type=int, default=1, help="07 correction cycles inside the first 01+07 combo.")
    parser.add_argument("--final-tabletop-correction-cycles", type=int, default=1, help="Correction cycles for the final 07.")
    parser.add_argument("--nuzzle-cycles", type=int, default=2, help="03 nuzzle cycles.")
    parser.add_argument("--party-light", choices=("spin", "rainbow"), default="spin")
    parser.add_argument("--offer-hold-seconds", type=float, default=1.4)
    parser.add_argument("--final-tabletop-hold-far-seconds", type=float, default=2.5)
    parser.add_argument("--final-tabletop-pose", choices=("target", "tabletop"), default="target")
    parser.add_argument("--final-tabletop-light-brightness", type=int, default=125)
    parser.add_argument("--skip-start-sleep", action="store_true", help="Skip the 01 initial sleep preparation.")
    args = parser.parse_args()

    exit_from_plan(
        args=args,
        steps=build_steps(
            scene_gap_seconds=args.scene_gap_seconds,
            tabletop_gap_seconds=args.tabletop_gap_seconds,
            correction_cycles=args.correction_cycles,
            final_tabletop_correction_cycles=args.final_tabletop_correction_cycles,
            nuzzle_cycles=args.nuzzle_cycles,
            party_light=args.party_light,
            offer_hold_seconds=args.offer_hold_seconds,
            final_tabletop_hold_far_seconds=args.final_tabletop_hold_far_seconds,
            final_tabletop_pose=args.final_tabletop_pose,
            final_tabletop_light_brightness=args.final_tabletop_light_brightness,
            skip_start_sleep=args.skip_start_sleep,
        ),
    )


if __name__ == "__main__":
    main()
