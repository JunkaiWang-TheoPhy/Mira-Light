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
offer_celebrate = load_script_module("_offer_celebrate", "04_offer_celebrate_demo.py")


def pause_between(label: str, seconds: float) -> RemoteStep:
    return RemoteStep(label, f"sleep {max(0.0, seconds):.2f}")


def build_steps(
    *,
    gap_seconds: float,
    correction_cycles: int,
    nuzzle_cycles: int,
    party_light: str,
    offer_hold_seconds: float,
    skip_start_sleep: bool,
) -> list[RemoteStep]:
    steps: list[RemoteStep] = []

    steps.extend(
        wake_tabletop.build_steps(
            correction_cycles=correction_cycles,
            hold_high_seconds=0.6,
            hold_far_seconds=1.25,
            final_pose="target",
            light_brightness=125,
            skip_start_sleep=skip_start_sleep,
        )
    )
    steps.append(pause_between("intermission 01+07 to 03 right-hand nuzzle", gap_seconds))

    steps.extend(
        right_hand_nuzzle.build_steps(
            nuzzle_cycles=nuzzle_cycles,
            skip_start_pose=False,
        )
    )
    steps.append(pause_between("intermission 03 right-hand nuzzle to 04 offer celebration", gap_seconds))

    steps.extend(
        offer_celebrate.build_steps(
            party_light=party_light,
            hold_seconds=offer_hold_seconds,
        )
    )

    return steps


def main() -> None:
    parser = build_parser("Combo test: 01+07 wake/tabletop, then 03 right-hand nuzzle, then 04 offer celebration.")
    parser.add_argument("--gap-seconds", type=float, default=3.0, help="Pause between the three major scenes.")
    parser.add_argument("--correction-cycles", type=int, default=1, help="07 tabletop correction cycles.")
    parser.add_argument("--nuzzle-cycles", type=int, default=2, help="03 nuzzle cycles.")
    parser.add_argument("--party-light", choices=("spin", "rainbow"), default="spin")
    parser.add_argument("--offer-hold-seconds", type=float, default=1.4)
    parser.add_argument("--skip-start-sleep", action="store_true", help="Skip the 01 initial sleep preparation.")
    args = parser.parse_args()
    exit_from_plan(
        args=args,
        steps=build_steps(
            gap_seconds=args.gap_seconds,
            correction_cycles=args.correction_cycles,
            nuzzle_cycles=args.nuzzle_cycles,
            party_light=args.party_light,
            offer_hold_seconds=args.offer_hold_seconds,
            skip_start_sleep=args.skip_start_sleep,
        ),
    )


if __name__ == "__main__":
    main()
