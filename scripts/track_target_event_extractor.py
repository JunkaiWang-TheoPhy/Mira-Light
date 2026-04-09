#!/usr/bin/env python3
"""First-pass single-camera track_target event extractor.

This script watches saved JPEG frames, extracts a simple target signal, and
emits structured JSON events aligned with the Mira Light runtime.

Design goals:
- no new dependencies beyond opencv-python + numpy
- prefer stable 2D signals first
- provide only heuristic monocular distance bands
- do not directly control servos
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from datetime import datetime, timezone
import json
import logging
from pathlib import Path
import time
from typing import Any

try:
    import cv2  # type: ignore
    import numpy as np  # type: ignore
except ImportError:  # pragma: no cover - handled at runtime for CLI usability
    cv2 = None  # type: ignore
    np = None  # type: ignore


LOGGER = logging.getLogger("track_target_event_extractor")

SCHEMA_VERSION = "1.0.0"


@dataclass
class ExtractorState:
    last_frame_path: Path | None = None
    last_target_present: bool = False
    last_size_norm: float | None = None
    bg_warmup_count: int = 0
    last_target_count: int = 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Watch saved JPEGs and emit Mira Light vision events.")
    parser.add_argument(
        "--captures-dir",
        type=Path,
        default=Path("./captures"),
        help="Directory containing received JPEG frames.",
    )
    parser.add_argument(
        "--poll-interval",
        type=float,
        default=0.5,
        help="Seconds between directory polls.",
    )
    parser.add_argument(
        "--latest-event-out",
        type=Path,
        help="Optional path to overwrite with the latest event JSON.",
    )
    parser.add_argument(
        "--events-jsonl",
        type=Path,
        help="Optional path to append JSONL events.",
    )
    parser.add_argument(
        "--once",
        action="store_true",
        help="Process the latest JPEG once and exit.",
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Logging verbosity.",
    )
    parser.add_argument(
        "--face-near-area-ratio",
        type=float,
        default=0.10,
        help="Area ratio threshold for classifying a face/person target as near.",
    )
    parser.add_argument(
        "--face-mid-area-ratio",
        type=float,
        default=0.03,
        help="Area ratio threshold for classifying a face/person target as mid distance.",
    )
    parser.add_argument(
        "--motion-near-area-ratio",
        type=float,
        default=0.18,
        help="Area ratio threshold for classifying a motion blob as near.",
    )
    parser.add_argument(
        "--motion-mid-area-ratio",
        type=float,
        default=0.06,
        help="Area ratio threshold for classifying a motion blob as mid distance.",
    )
    parser.add_argument(
        "--warmup-frames",
        type=int,
        default=5,
        help="Background subtractor warmup frames before motion events are trusted.",
    )
    parser.add_argument(
        "--min-motion-area-ratio",
        type=float,
        default=0.015,
        help="Minimum contour area ratio before a motion blob is treated as a target.",
    )
    return parser.parse_args()


def configure_logging(level: str) -> None:
    logging.basicConfig(
        level=getattr(logging, level),
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )


def find_latest_jpg(captures_dir: Path) -> Path | None:
    if not captures_dir.exists():
        return None
    files = sorted(captures_dir.rglob("*.jpg"), key=lambda p: p.stat().st_mtime)
    return files[-1] if files else None


def load_image(path: Path) -> np.ndarray | None:
    data = np.frombuffer(path.read_bytes(), dtype=np.uint8)
    return cv2.imdecode(data, cv2.IMREAD_COLOR)


def classify_horizontal_zone(x_norm: float | None) -> str:
    if x_norm is None:
        return "unknown"
    if x_norm < 0.33:
        return "left"
    if x_norm > 0.66:
        return "right"
    return "center"


def classify_vertical_zone(y_norm: float | None) -> str:
    if y_norm is None:
        return "unknown"
    if y_norm < 0.33:
        return "upper"
    if y_norm > 0.66:
        return "lower"
    return "middle"


def classify_distance_band(size_norm: float | None, *, near_threshold: float, mid_threshold: float) -> str:
    if size_norm is None:
        return "unknown"
    if size_norm >= near_threshold:
        return "near"
    if size_norm >= mid_threshold:
        return "mid"
    return "far"


def classify_approach_state(size_norm: float | None, previous_size_norm: float | None) -> tuple[str, float | None]:
    if size_norm is None or previous_size_norm is None:
        return "unknown", None
    delta = size_norm - previous_size_norm
    if delta > 0.012:
        return "approaching", delta
    if delta < -0.012:
        return "receding", delta
    return "stable", delta


def clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def make_control_hint(center_x: float | None, center_y: float | None, distance_band: str) -> dict[str, float]:
    yaw_error = 0.0 if center_x is None else clamp((center_x - 0.5) * 2.0, -1.0, 1.0)
    pitch_error = 0.0 if center_y is None else clamp((0.5 - center_y) * 2.0, -1.0, 1.0)

    reach_by_band = {
        "near": 0.8,
        "mid": 0.55,
        "far": 0.25,
        "unknown": 0.0,
    }
    lift_by_y = 0.5 if center_y is None else clamp(1.0 - center_y, 0.0, 1.0)

    return {
        "yaw_error_norm": round(yaw_error, 4),
        "pitch_error_norm": round(pitch_error, 4),
        "lift_intent": round(lift_by_y, 4),
        "reach_intent": round(reach_by_band.get(distance_band, 0.0), 4),
    }


def infer_scene_hint(target_present: bool, distance_band: str, approach_state: str, horizontal_zone: str) -> tuple[str, str]:
    if not target_present:
        return "sleep", "当前没有稳定目标，适合回到休息或等待状态。"
    if distance_band == "far":
        return "wake_up", "目标刚进入可见范围，适合先进入唤醒与注意建立。"
    if approach_state == "approaching" or horizontal_zone != "center":
        return "track_target", "目标正在移动或偏离中心，适合进入跟随观察。"
    return "curious_observe", "目标稳定停留且距离适中，适合进入好奇观察。"


def write_event_outputs(event: dict[str, Any], latest_event_out: Path | None, events_jsonl: Path | None) -> None:
    payload = json.dumps(event, ensure_ascii=False, indent=2)

    if latest_event_out is not None:
        latest_event_out.parent.mkdir(parents=True, exist_ok=True)
        latest_event_out.write_text(payload + "\n", encoding="utf-8")

    if events_jsonl is not None:
        events_jsonl.parent.mkdir(parents=True, exist_ok=True)
        with events_jsonl.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(event, ensure_ascii=False) + "\n")


def now_iso() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def detect_faces(gray: np.ndarray, cascade: cv2.CascadeClassifier) -> list[tuple[int, int, int, int]]:
    faces = cascade.detectMultiScale(
        gray,
        scaleFactor=1.1,
        minNeighbors=5,
        minSize=(40, 40),
    )
    return [tuple(int(value) for value in box) for box in faces]


def detect_motion(frame: np.ndarray, subtractor: cv2.BackgroundSubtractor, *, min_area_ratio: float, warmup_count: int, warmup_frames: int) -> tuple[tuple[int, int, int, int] | None, int]:
    fg = subtractor.apply(frame)
    kernel = np.ones((5, 5), np.uint8)
    fg = cv2.morphologyEx(fg, cv2.MORPH_OPEN, kernel)
    fg = cv2.morphologyEx(fg, cv2.MORPH_CLOSE, kernel)
    contours, _ = cv2.findContours(fg, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    h, w = frame.shape[:2]
    min_area_px = min_area_ratio * w * h
    warmup_count += 1

    if warmup_count <= warmup_frames:
        return None, warmup_count

    best = None
    best_area = 0.0
    for contour in contours:
        area = cv2.contourArea(contour)
        if area < min_area_px:
            continue
        x, y, bw, bh = cv2.boundingRect(contour)
        if area > best_area:
            best_area = area
            best = (x, y, bw, bh)

    return best, warmup_count


def build_event(
    *,
    path: Path,
    frame: np.ndarray,
    bbox: tuple[int, int, int, int] | None,
    detector: str,
    target_class: str,
    confidence: float,
    state: ExtractorState,
    args: argparse.Namespace,
    target_count: int = 0,
    multi_target_payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    h, w = frame.shape[:2]
    size_norm = None
    center_x = None
    center_y = None
    bbox_norm = None
    bbox_area_px = None

    if bbox is not None:
        x, y, bw, bh = bbox
        bbox_area_px = bw * bh
        size_norm = bbox_area_px / float(w * h)
        center_x = (x + (bw / 2.0)) / w
        center_y = (y + (bh / 2.0)) / h
        bbox_norm = {
            "x": round(x / w, 4),
            "y": round(y / h, 4),
            "w": round(bw / w, 4),
            "h": round(bh / h, 4),
        }

    if detector == "haar_face":
        distance_band = classify_distance_band(
            size_norm,
            near_threshold=args.face_near_area_ratio,
            mid_threshold=args.face_mid_area_ratio,
        )
    elif detector == "background_motion":
        distance_band = classify_distance_band(
            size_norm,
            near_threshold=args.motion_near_area_ratio,
            mid_threshold=args.motion_mid_area_ratio,
        )
    else:
        distance_band = "unknown"

    approach_state, size_delta_norm = classify_approach_state(size_norm, state.last_size_norm)
    horizontal_zone = classify_horizontal_zone(center_x)
    vertical_zone = classify_vertical_zone(center_y)
    target_present = bbox is not None

    if target_count >= 2:
        event_type = "multi_target_seen"
    elif target_present and not state.last_target_present:
        event_type = "target_seen"
    elif target_present and state.last_target_present:
        event_type = "target_updated"
    elif (not target_present) and state.last_target_present:
        event_type = "target_lost"
    else:
        event_type = "no_target"

    if target_count >= 2:
        scene_name, scene_reason = "multi_person_demo", "同一帧检测到两个稳定目标，适合进入多人反应。"
    else:
        scene_name, scene_reason = infer_scene_hint(target_present, distance_band, approach_state, horizontal_zone)

    frame_age_ms = max(0.0, (time.time() - path.stat().st_mtime) * 1000.0)
    event = {
        "schema_version": SCHEMA_VERSION,
        "event_type": event_type,
        "timestamp": now_iso(),
        "source": {
            "pipeline": "saved_jpeg_watch",
            "camera_mode": "single_camera_2d",
            "distance_mode": "monocular_heuristic",
        },
        "frame": {
            "path": str(path.resolve()),
            "width": w,
            "height": h,
            "seq": extract_seq_from_name(path.name),
            "capture_ts": None,
        },
        "tracking": {
            "target_present": target_present,
            "target_count": target_count if target_count > 0 else (1 if target_present else 0),
            "target_class": target_class if target_present else "none",
            "detector": detector,
            "confidence": round(confidence if target_present else 0.0, 4),
            "bbox_norm": bbox_norm,
            "center_norm": None if center_x is None or center_y is None else {"x": round(center_x, 4), "y": round(center_y, 4)},
            "horizontal_zone": horizontal_zone if target_present else "unknown",
            "vertical_zone": vertical_zone if target_present else "unknown",
            "size_norm": None if size_norm is None else round(size_norm, 6),
            "distance_band": distance_band,
            "approach_state": approach_state,
        },
        "scene_hint": {
            "name": scene_name,
            "reason": scene_reason,
        },
        "control_hint": make_control_hint(center_x, center_y, distance_band),
        "raw_measurements": {
            "frame_age_ms": round(frame_age_ms, 1),
            "bbox_area_px": bbox_area_px,
            "size_delta_norm": None if size_delta_norm is None else round(size_delta_norm, 6),
        },
    }
    if multi_target_payload:
        event["payload"] = multi_target_payload
    return event


def extract_seq_from_name(filename: str) -> str | None:
    if "-seq-" not in filename:
        return None
    seq = filename.split("-seq-", 1)[1]
    if seq.lower().endswith(".jpg"):
        seq = seq[:-4]
    return seq


def process_frame(path: Path, state: ExtractorState, subtractor: cv2.BackgroundSubtractor, cascade: cv2.CascadeClassifier, args: argparse.Namespace) -> dict[str, Any]:
    frame = load_image(path)
    if frame is None:
        raise RuntimeError(f"Failed to decode JPEG frame: {path}")

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    faces = detect_faces(gray, cascade)
    bbox = max(faces, key=lambda box: box[2] * box[3]) if faces else None
    detector = "none"
    target_class = "none"
    confidence = 0.0
    target_count = 0
    multi_target_payload = None

    if len(faces) >= 2:
        primary, secondary = sorted(faces, key=lambda box: box[2] * box[3], reverse=True)[:2]
        bbox = primary
        detector = "haar_face"
        target_class = "person"
        confidence = 0.92
        target_count = len(faces)
        primary_center_x = (primary[0] + (primary[2] / 2.0)) / frame.shape[1]
        secondary_center_x = (secondary[0] + (secondary[2] / 2.0)) / frame.shape[1]
        multi_target_payload = {
            "targetCount": len(faces),
            "primaryDirection": classify_horizontal_zone(primary_center_x),
            "secondaryDirection": classify_horizontal_zone(secondary_center_x),
        }
    elif bbox is not None:
        detector = "haar_face"
        target_class = "person"
        confidence = 0.9
        target_count = 1
    else:
        motion_bbox, warmup_count = detect_motion(
            frame,
            subtractor,
            min_area_ratio=args.min_motion_area_ratio,
            warmup_count=state.bg_warmup_count,
            warmup_frames=args.warmup_frames,
        )
        state.bg_warmup_count = warmup_count
        if motion_bbox is not None:
            bbox = motion_bbox
            detector = "background_motion"
            target_class = "motion_blob"
            confidence = 0.55
            target_count = 1

    event = build_event(
        path=path,
        frame=frame,
        bbox=bbox,
        detector=detector,
        target_class=target_class,
        confidence=confidence,
        state=state,
        args=args,
        target_count=target_count,
        multi_target_payload=multi_target_payload,
    )

    state.last_frame_path = path
    state.last_target_present = event["tracking"]["target_present"]
    state.last_size_norm = event["tracking"]["size_norm"]
    state.last_target_count = event["tracking"]["target_count"]
    return event


def main() -> int:
    args = parse_args()
    configure_logging(args.log_level)

    if cv2 is None or np is None:
        raise SystemExit(
            "OpenCV/Numpy are required. Run 'bash scripts/setup_cam_receiver_env.sh' "
            "and use the repository .venv, or install requirements.txt first."
        )

    captures_dir = args.captures_dir.expanduser().resolve()
    latest_event_out = args.latest_event_out.expanduser().resolve() if args.latest_event_out else None
    events_jsonl = args.events_jsonl.expanduser().resolve() if args.events_jsonl else None

    cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
    if cascade.empty():
        raise SystemExit("OpenCV haarcascade_frontalface_default.xml is unavailable.")

    subtractor = cv2.createBackgroundSubtractorMOG2(history=100, varThreshold=32, detectShadows=False)
    state = ExtractorState()

    LOGGER.info("Watching %s for JPEG frames", captures_dir)
    if latest_event_out:
        LOGGER.info("Latest event output: %s", latest_event_out)
    if events_jsonl:
        LOGGER.info("JSONL event log: %s", events_jsonl)

    while True:
        latest = find_latest_jpg(captures_dir)
        if latest is not None and latest != state.last_frame_path:
            event = process_frame(latest, state, subtractor, cascade, args)
            print(json.dumps(event, ensure_ascii=False))
            write_event_outputs(event, latest_event_out, events_jsonl)

            LOGGER.info(
                "event=%s target=%s detector=%s scene=%s distance=%s position=%s size=%s",
                event["event_type"],
                event["tracking"]["target_class"],
                event["tracking"]["detector"],
                event["scene_hint"]["name"],
                event["tracking"]["distance_band"],
                event["tracking"]["horizontal_zone"],
                event["tracking"]["size_norm"],
            )

            if args.once:
                return 0

        if args.once:
            LOGGER.warning("No JPEG frame found in %s", captures_dir)
            return 1

        time.sleep(args.poll_interval)


if __name__ == "__main__":
    raise SystemExit(main())
