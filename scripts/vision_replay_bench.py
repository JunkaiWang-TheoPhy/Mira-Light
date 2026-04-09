#!/usr/bin/env python3
"""Offline replay bench for the Mira Light vision pipeline."""

from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
import json
from pathlib import Path
from types import SimpleNamespace
from typing import Any

from mira_light_runtime import MiraLightRuntime
from track_target_event_extractor import (
    ExtractorState,
    cv2,
    np,
    process_frame,
    write_event_outputs,
)
from vision_runtime_bridge import BridgeState, resolve_candidate_scene, should_start_scene, write_state_file


def now_iso() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Replay saved frames through the Mira Light vision pipeline.")
    parser.add_argument("--captures-dir", type=Path, required=True, help="Directory of JPEG frames to replay.")
    parser.add_argument("--out-dir", type=Path, default=Path("./runtime/vision-replay"), help="Output directory.")
    parser.add_argument("--base-url", default="http://127.0.0.1:9799", help="Lamp or mock device base URL.")
    parser.add_argument("--dry-run", action="store_true", help="Use dry-run runtime mode.")
    parser.add_argument("--allow-experimental", action="store_true", help="Allow tuning/prototype scenes.")
    parser.add_argument("--frame-spacing-ms", type=int, default=1400, help="Virtual time between frames.")
    parser.add_argument("--scene-cooldown-ms", type=int, default=1200, help="Cooldown for repeated scene starts.")
    parser.add_argument("--wake-up-cooldown-ms", type=int, default=2200, help="Cooldown before wake_up repeats.")
    parser.add_argument("--sleep-grace-ms", type=int, default=2200, help="Absence grace period before sleep.")
    parser.add_argument("--warmup-frames", type=int, default=1, help="Motion warmup frames for replay.")
    parser.add_argument("--generate-synthetic-demo", action="store_true", help="Seed captures-dir with demo JPEGs.")
    return parser


def ensure_vision_deps() -> None:
    if cv2 is None or np is None:
        raise SystemExit(
            "OpenCV/Numpy are required for vision replay. "
            "Use the repository .venv or install requirements first."
        )


def build_extractor_args(args: argparse.Namespace) -> argparse.Namespace:
    return SimpleNamespace(
        face_near_area_ratio=0.10,
        face_mid_area_ratio=0.03,
        motion_near_area_ratio=0.18,
        motion_mid_area_ratio=0.06,
        warmup_frames=args.warmup_frames,
        min_motion_area_ratio=0.015,
        hold_missing_frames=3,
        engagement_zone_left=0.08,
        engagement_zone_right=0.92,
        operator_state_file=None,
        hog_min_confidence=0.58,
        enable_hog_person=True,
        hand_cue_min_area_ratio=0.0015,
        hand_cue_max_area_ratio=0.06,
        hand_cue_min_center_y=0.34,
        hand_cue_min_motion_ratio=0.12,
        hand_cue_min_confidence=0.55,
        owner_match_threshold=0.82,
        owner_selection_bonus=0.24,
    )


def build_bridge_decision_args(args: argparse.Namespace) -> argparse.Namespace:
    return SimpleNamespace(
        scene_cooldown_ms=args.scene_cooldown_ms,
        wake_up_cooldown_ms=args.wake_up_cooldown_ms,
        sleep_grace_ms=args.sleep_grace_ms,
        log_json=False,
    )


def generate_synthetic_demo_frames(captures_dir: Path) -> list[Path]:
    ensure_vision_deps()
    captures_dir.mkdir(parents=True, exist_ok=True)
    created = []
    frames = [
        None,
        None,
        None,
        {"x": 110, "y": 170, "w": 90, "h": 110},
        {"x": 220, "y": 160, "w": 110, "h": 140},
        {"x": 360, "y": 150, "w": 130, "h": 160},
        None,
        None,
    ]

    for index, rect in enumerate(frames, start=1):
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        if rect is not None:
            x = rect["x"]
            y = rect["y"]
            w = rect["w"]
            h = rect["h"]
            cv2.rectangle(frame, (x, y), (x + w, y + h), (255, 255, 255), thickness=-1)
        path = captures_dir / f"demo-seq-{index:03d}.jpg"
        if not cv2.imwrite(str(path), frame):
            raise RuntimeError(f"Failed to write synthetic frame: {path}")
        created.append(path)
    return created


def iter_frames(captures_dir: Path) -> list[Path]:
    return sorted(captures_dir.rglob("*.jpg"))


def run_replay_bench(args: argparse.Namespace) -> dict[str, Any]:
    ensure_vision_deps()
    captures_dir = args.captures_dir.expanduser().resolve()
    out_dir = args.out_dir.expanduser().resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    if args.generate_synthetic_demo:
        generate_synthetic_demo_frames(captures_dir)

    frames = iter_frames(captures_dir)
    if not frames:
        raise FileNotFoundError(f"No JPEG frames found in {captures_dir}")

    latest_event_out = out_dir / "vision.latest.json"
    events_jsonl = out_dir / "vision.events.jsonl"
    bridge_state_out = out_dir / "vision.bridge.state.json"

    extractor_args = build_extractor_args(args)
    decision_args = build_bridge_decision_args(args)
    cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
    if cascade.empty():
        raise RuntimeError("OpenCV haarcascade_frontalface_default.xml is unavailable.")
    hog = cv2.HOGDescriptor()
    hog.setSVMDetector(cv2.HOGDescriptor_getDefaultPeopleDetector())
    subtractor = cv2.createBackgroundSubtractorMOG2(history=100, varThreshold=32, detectShadows=False)
    extractor_state = ExtractorState()

    runtime = MiraLightRuntime(base_url=args.base_url, dry_run=args.dry_run)
    runtime.show_experimental = args.allow_experimental or runtime.show_experimental
    bridge_state = BridgeState()

    event_counter: Counter[str] = Counter()
    scene_counter: Counter[str] = Counter()
    decisions: list[dict[str, Any]] = []
    simulated_mono = 0.0

    for index, frame_path in enumerate(frames, start=1):
        event = process_frame(frame_path, extractor_state, subtractor, cascade, hog, None, extractor_args)
        write_event_outputs(event, latest_event_out, events_jsonl)
        event_counter[event["event_type"]] += 1

        candidate_scene, candidate_reason = resolve_candidate_scene(event, bridge_state, simulated_mono, decision_args)
        runtime_state_before = runtime.get_runtime_state()
        allowed, allowed_reason = should_start_scene(
            candidate_scene,
            runtime_state=runtime_state_before,
            bridge_state=bridge_state,
            now_mono=simulated_mono,
            args=decision_args,
        )

        started_scene = None
        if allowed:
            runtime.run_scene_blocking(candidate_scene)
            bridge_state.last_scene_started = candidate_scene
            bridge_state.last_scene_started_at_monotonic = simulated_mono
            bridge_state.scene_counts[candidate_scene] = bridge_state.scene_counts.get(candidate_scene, 0) + 1
            scene_counter[candidate_scene] += 1
            started_scene = candidate_scene

        bridge_state.last_target_present = bool((event.get("tracking") or {}).get("target_present"))
        write_state_file(bridge_state_out, runtime, bridge_state, event)

        decisions.append(
            {
                "frameIndex": index,
                "framePath": str(frame_path),
                "simulatedMonotonicSeconds": round(simulated_mono, 3),
                "eventType": event["event_type"],
                "sceneHint": (event.get("scene_hint") or {}).get("name"),
                "candidateScene": candidate_scene,
                "candidateReason": candidate_reason,
                "allowed": allowed,
                "allowedReason": allowed_reason,
                "startedScene": started_scene,
                "tracking": event["tracking"],
                "runtimeBefore": runtime_state_before,
                "runtimeAfter": runtime.get_runtime_state(),
            }
        )

        simulated_mono += args.frame_spacing_ms / 1000.0

    summary = {
        "generatedAt": now_iso(),
        "capturesDir": str(captures_dir),
        "outDir": str(out_dir),
        "dryRun": args.dry_run,
        "allowExperimental": runtime.show_experimental,
        "processedFrames": len(frames),
        "eventCounts": dict(event_counter),
        "sceneCounts": dict(scene_counter),
        "latestEventPath": str(latest_event_out),
        "eventsJsonlPath": str(events_jsonl),
        "bridgeStatePath": str(bridge_state_out),
    }
    report = {"summary": summary, "decisions": decisions}
    (out_dir / "vision.replay.report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return report


def main() -> int:
    args = build_parser().parse_args()
    report = run_replay_bench(args)
    print(json.dumps(report["summary"], ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
