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
    next_track_id: int = 1
    previous_tracks: dict[int, dict[str, Any]] = None  # type: ignore[assignment]
    selected_track_id: int | None = None
    missing_frame_count: int = 0
    last_selected_target: dict[str, Any] | None = None

    def __post_init__(self) -> None:
        if self.previous_tracks is None:
            self.previous_tracks = {}


@dataclass
class CascadeBundle:
    frontal_default: Any
    frontal_alt2: Any | None = None
    profile: Any | None = None
    upperbody: Any | None = None


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
        "--selection-lock-file",
        type=Path,
        help="Optional JSON file describing a manually selected target lock.",
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
    parser.add_argument(
        "--hold-missing-frames",
        type=int,
        default=3,
        help="How many consecutive empty frames to keep the last selected target alive before declaring loss.",
    )
    parser.add_argument(
        "--engagement-zone-left",
        type=float,
        default=0.08,
        help="Ignore detections whose center is left of this normalized x bound.",
    )
    parser.add_argument(
        "--engagement-zone-right",
        type=float,
        default=0.92,
        help="Ignore detections whose center is right of this normalized x bound.",
    )
    parser.add_argument(
        "--operator-state-file",
        type=Path,
        default=Path("./runtime/vision.operator.json"),
        help="Optional JSON file written by the director console to request target locking.",
    )
    parser.add_argument(
        "--hog-min-confidence",
        type=float,
        default=0.58,
        help="Minimum normalized confidence for OpenCV HOG person detections.",
    )
    parser.set_defaults(enable_hog_person=True)
    parser.add_argument(
        "--disable-hog-person",
        dest="enable_hog_person",
        action="store_false",
        help="Disable HOG person detector fallback when face detection misses.",
    )
    parser.add_argument(
        "--face-min-neighbors",
        type=int,
        default=4,
        help="Base minNeighbors used by the frontal-face cascades.",
    )
    parser.add_argument(
        "--face-min-size",
        type=int,
        default=30,
        help="Minimum face size in pixels for near-field booth portraits.",
    )
    parser.add_argument(
        "--profile-face-min-neighbors",
        type=int,
        default=4,
        help="minNeighbors used by the profile-face cascade.",
    )
    parser.add_argument(
        "--upperbody-min-neighbors",
        type=int,
        default=3,
        help="minNeighbors used by the upper-body cascade.",
    )
    parser.add_argument(
        "--upperbody-min-size",
        type=int,
        default=56,
        help="Minimum upper-body size in pixels for tolerant person counting.",
    )
    parser.add_argument(
        "--standalone-hog-min-confidence",
        type=float,
        default=0.72,
        help="Minimum confidence required before an unanchored HOG box counts as a person.",
    )
    parser.add_argument(
        "--hand-cue-min-area-ratio",
        type=float,
        default=0.0015,
        help="Minimum area ratio for a skin+motion hand/arm cue contour.",
    )
    parser.add_argument(
        "--hand-cue-max-area-ratio",
        type=float,
        default=0.06,
        help="Maximum area ratio for a skin+motion hand/arm cue contour.",
    )
    parser.add_argument(
        "--hand-cue-min-center-y",
        type=float,
        default=0.34,
        help="Ignore hand/arm cues whose center is above this normalized y bound.",
    )
    parser.add_argument(
        "--hand-cue-min-motion-ratio",
        type=float,
        default=0.12,
        help="Minimum foreground-motion occupancy inside the cue bbox.",
    )
    parser.add_argument(
        "--hand-cue-min-confidence",
        type=float,
        default=0.55,
        help="Minimum normalized confidence emitted for a hand/arm cue.",
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


def candidate_score(*, confidence: float, size_norm: float | None, center_x: float | None, center_y: float | None) -> float:
    size_component = 0.0 if size_norm is None else min(size_norm * 4.0, 1.0)
    center_penalty = 0.0
    if center_x is not None and center_y is not None:
        center_penalty = abs(center_x - 0.5) + abs(center_y - 0.5)
    return confidence + size_component - (center_penalty * 0.35)


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


def make_track_entry(
    *,
    track_id: int,
    bbox: tuple[int, int, int, int],
    detector: str,
    target_class: str,
    confidence: float,
    frame_width: int,
    frame_height: int,
    previous_size_norm: float | None,
) -> dict[str, Any]:
    x, y, bw, bh = bbox
    bbox_area_px = bw * bh
    size_norm = bbox_area_px / float(frame_width * frame_height)
    center_x = (x + (bw / 2.0)) / frame_width
    center_y = (y + (bh / 2.0)) / frame_height

    if detector in {"haar_face", "hog_person"}:
        distance_band = classify_distance_band(size_norm, near_threshold=0.10, mid_threshold=0.03)
    elif detector == "background_motion":
        distance_band = classify_distance_band(size_norm, near_threshold=0.18, mid_threshold=0.06)
    else:
        distance_band = "unknown"

    approach_state, size_delta_norm = classify_approach_state(size_norm, previous_size_norm)
    return {
        "track_id": track_id,
        "target_class": target_class,
        "detector": detector,
        "confidence": round(confidence, 4),
        "bbox_norm": {
            "x": round(x / frame_width, 4),
            "y": round(y / frame_height, 4),
            "w": round(bw / frame_width, 4),
            "h": round(bh / frame_height, 4),
        },
        "center_norm": {"x": round(center_x, 4), "y": round(center_y, 4)},
        "horizontal_zone": classify_horizontal_zone(center_x),
        "vertical_zone": classify_vertical_zone(center_y),
        "size_norm": round(size_norm, 6),
        "distance_band": distance_band,
        "approach_state": approach_state,
        "bbox_area_px": bbox_area_px,
        "size_delta_norm": None if size_delta_norm is None else round(size_delta_norm, 6),
        "selection_score": round(candidate_score(confidence=confidence, size_norm=size_norm, center_x=center_x, center_y=center_y), 4),
    }


def assign_track_ids(candidates: list[dict[str, Any]], state: ExtractorState) -> list[dict[str, Any]]:
    assigned: list[dict[str, Any]] = []
    used_previous: set[int] = set()

    for candidate in candidates:
        center = candidate["center_norm"]
        detector = candidate["detector"]
        target_class = candidate["target_class"]

        best_track_id = None
        best_distance = 999.0
        for track_id, previous in state.previous_tracks.items():
            if track_id in used_previous:
                continue
            if previous.get("detector") != detector or previous.get("target_class") != target_class:
                continue
            prev_center = previous.get("center_norm")
            if not isinstance(prev_center, dict):
                continue
            dx = float(center["x"]) - float(prev_center.get("x", 0.5))
            dy = float(center["y"]) - float(prev_center.get("y", 0.5))
            distance = (dx * dx + dy * dy) ** 0.5
            if distance < 0.18 and distance < best_distance:
                best_distance = distance
                best_track_id = track_id

        if best_track_id is None:
            best_track_id = state.next_track_id
            state.next_track_id += 1

        used_previous.add(best_track_id)
        candidate["track_id"] = best_track_id
        assigned.append(candidate)

    state.previous_tracks = {
        int(item["track_id"]): {
            "center_norm": dict(item["center_norm"]),
            "detector": item["detector"],
            "target_class": item["target_class"],
            "size_norm": item["size_norm"],
        }
        for item in assigned
    }
    return assigned


def choose_selected_target(
    tracks: list[dict[str, Any]],
    state: ExtractorState,
    *,
    operator_state: dict[str, Any] | None = None,
) -> dict[str, Any] | None:
    if not tracks:
        return None

    operator_lock_track_id = parse_operator_lock_track_id(operator_state)
    if operator_lock_track_id is not None:
        for item in tracks:
            if int(item["track_id"]) == operator_lock_track_id:
                state.selected_track_id = operator_lock_track_id
                selected = dict(item)
                selected["lock_state"] = "operator_locked"
                selected["reason"] = "director console requested target lock"
                return selected

    locked_track = None
    if state.selected_track_id is not None:
        for item in tracks:
            if int(item["track_id"]) == state.selected_track_id:
                locked_track = item
                break

    if locked_track is not None:
        selected = dict(locked_track)
        selected["lock_state"] = "locked"
        selected["reason"] = "previous selected target still visible"
        return selected

    ranked = sorted(tracks, key=lambda item: item.get("selection_score", 0.0), reverse=True)
    selected = dict(ranked[0])
    if len(tracks) == 1:
        selected["lock_state"] = "locked"
        selected["reason"] = "single visible target"
        state.selected_track_id = int(selected["track_id"])
    else:
        selected["lock_state"] = "candidate"
        selected["reason"] = "highest score among multiple visible targets"
        state.selected_track_id = None
    return selected

def parse_operator_lock_track_id(operator_state: dict[str, Any] | None) -> int | None:
    if not isinstance(operator_state, dict):
        return None
    raw = operator_state.get("lockSelectedTrackId")
    if raw in {None, "", False}:
        return None
    try:
        value = int(raw)
    except (TypeError, ValueError):
        return None
    return value if value > 0 else None


def load_operator_state(path: Path | None) -> dict[str, Any]:
    if path is None or not path.is_file():
        return {}
    try:
        raw = path.read_text(encoding="utf-8").strip()
        if not raw:
            return {}
        parsed = json.loads(raw)
        return parsed if isinstance(parsed, dict) else {}
    except Exception:
        return {}


def within_engagement_zone(track: dict[str, Any], args: argparse.Namespace) -> bool:
    center = track.get("center_norm")
    if not isinstance(center, dict):
        return True
    x_norm = float(center.get("x", 0.5))
    return args.engagement_zone_left <= x_norm <= args.engagement_zone_right


def hold_selected_target(state: ExtractorState, args: argparse.Namespace) -> dict[str, Any] | None:
    if state.last_selected_target is None:
        return None
    if not state.last_target_present:
        return None
    if state.missing_frame_count > args.hold_missing_frames:
        return None

    held = dict(state.last_selected_target)
    held["confidence"] = round(max(0.35, float(held.get("confidence") or 0.0) * 0.84), 4)
    held["lock_state"] = "held"
    held["reason"] = f"short occlusion hold ({state.missing_frame_count}/{args.hold_missing_frames})"
    held["approach_state"] = "stable"
    return held


def detect_people(frame: np.ndarray, hog: Any, *, min_confidence: float) -> list[tuple[tuple[int, int, int, int], float]]:
    if hog is None:
        return []
    boxes, weights = hog.detectMultiScale(frame, winStride=(8, 8), padding=(8, 8), scale=1.05)
    detections: list[tuple[tuple[int, int, int, int], float]] = []
    for box, weight in zip(boxes, weights):
        confidence = clamp(float(weight) / 2.5, 0.0, 0.95)
        if confidence < min_confidence:
            continue
        x, y, bw, bh = [int(value) for value in box]
        detections.append(((x, y, bw, bh), confidence))
    return detections


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


def bbox_iou(a: tuple[int, int, int, int], b: tuple[int, int, int, int]) -> float:
    ax, ay, aw, ah = a
    bx, by, bw, bh = b
    left = max(ax, bx)
    top = max(ay, by)
    right = min(ax + aw, bx + bw)
    bottom = min(ay + ah, by + bh)
    if right <= left or bottom <= top:
        return 0.0
    intersection = float((right - left) * (bottom - top))
    union = float(max(1, aw * ah) + max(1, bw * bh) - intersection)
    return intersection / union


def clip_bbox(
    bbox: tuple[int, int, int, int],
    *,
    frame_width: int,
    frame_height: int,
) -> tuple[int, int, int, int] | None:
    x, y, bw, bh = bbox
    left = max(0, int(round(x)))
    top = max(0, int(round(y)))
    right = min(frame_width, int(round(x + bw)))
    bottom = min(frame_height, int(round(y + bh)))
    if right <= left or bottom <= top:
        return None
    return (left, top, right - left, bottom - top)


def expand_face_bbox(
    bbox: tuple[int, int, int, int],
    *,
    frame_width: int,
    frame_height: int,
) -> tuple[int, int, int, int] | None:
    x, y, bw, bh = bbox
    expanded = (
        x - (bw * 0.55),
        y - (bh * 0.35),
        bw * 2.1,
        bh * 3.3,
    )
    return clip_bbox(expanded, frame_width=frame_width, frame_height=frame_height)


def merge_ranked_boxes(
    detections: list[tuple[tuple[int, int, int, int], float]],
    *,
    iou_threshold: float,
) -> list[tuple[tuple[int, int, int, int], float]]:
    merged: list[tuple[tuple[int, int, int, int], float]] = []
    for bbox, score in sorted(detections, key=lambda item: item[1], reverse=True):
        if any(bbox_iou(bbox, existing_bbox) >= iou_threshold for existing_bbox, _ in merged):
            continue
        merged.append((bbox, score))
    return merged


def detect_faces(gray: np.ndarray, cascades: CascadeBundle, args: argparse.Namespace) -> list[tuple[tuple[int, int, int, int], float]]:
    min_face = max(18, int(args.face_min_size))
    detections: list[tuple[tuple[int, int, int, int], float]] = []

    frontal_specs = [
        (cascades.frontal_default, 0.92, max(3, int(args.face_min_neighbors))),
        (cascades.frontal_alt2, 0.84, max(2, int(args.face_min_neighbors) - 1)),
    ]
    for cascade, confidence, min_neighbors in frontal_specs:
        if cascade is None:
            continue
        faces = cascade.detectMultiScale(
            gray,
            scaleFactor=1.08,
            minNeighbors=min_neighbors,
            minSize=(min_face, min_face),
        )
        detections.extend((tuple(int(value) for value in box), confidence) for box in faces)

    if cascades.profile is not None:
        profile_neighbors = max(2, int(args.profile_face_min_neighbors))
        profile_faces = cascades.profile.detectMultiScale(
            gray,
            scaleFactor=1.08,
            minNeighbors=profile_neighbors,
            minSize=(min_face, min_face),
        )
        detections.extend((tuple(int(value) for value in box), 0.8) for box in profile_faces)

        flipped = cv2.flip(gray, 1)
        mirrored_faces = cascades.profile.detectMultiScale(
            flipped,
            scaleFactor=1.08,
            minNeighbors=profile_neighbors,
            minSize=(min_face, min_face),
        )
        frame_width = gray.shape[1]
        for x, y, bw, bh in mirrored_faces:
            mirrored_x = frame_width - int(x) - int(bw)
            detections.append(((mirrored_x, int(y), int(bw), int(bh)), 0.8))

    return merge_ranked_boxes(detections, iou_threshold=0.24)


def detect_upper_bodies(
    gray: np.ndarray,
    cascades: CascadeBundle,
    args: argparse.Namespace,
) -> list[tuple[tuple[int, int, int, int], float]]:
    if cascades.upperbody is None:
        return []
    min_size = max(32, int(args.upperbody_min_size))
    bodies = cascades.upperbody.detectMultiScale(
        gray,
        scaleFactor=1.06,
        minNeighbors=max(2, int(args.upperbody_min_neighbors)),
        minSize=(min_size, min_size),
    )
    detections: list[tuple[tuple[int, int, int, int], float]] = []
    for x, y, bw, bh in bodies:
        aspect = float(bh) / max(1.0, float(bw))
        if aspect < 0.8 or aspect > 3.4:
            continue
        detections.append(((int(x), int(y), int(bw), int(bh)), 0.72))
    return merge_ranked_boxes(detections, iou_threshold=0.28)


def is_plausible_standalone_hog(
    bbox: tuple[int, int, int, int],
    *,
    frame_width: int,
    frame_height: int,
    confidence: float,
    min_confidence: float,
) -> bool:
    if confidence < min_confidence:
        return False
    x, y, bw, bh = bbox
    center_y = (y + (bh / 2.0)) / max(1.0, float(frame_height))
    width_norm = bw / max(1.0, float(frame_width))
    height_norm = bh / max(1.0, float(frame_height))
    aspect = float(bh) / max(1.0, float(bw))
    if center_y < 0.30:
        return False
    if width_norm < 0.10 or height_norm < 0.18:
        return False
    if aspect < 1.05 or aspect > 3.8:
        return False
    return True


def same_person_candidate(a: dict[str, Any], b: dict[str, Any], *, frame_width: int, frame_height: int) -> bool:
    bbox_a = denormalize_bbox(a.get("bbox_norm"), frame_width=frame_width, frame_height=frame_height)
    bbox_b = denormalize_bbox(b.get("bbox_norm"), frame_width=frame_width, frame_height=frame_height)
    if bbox_a is None or bbox_b is None:
        return False
    if bbox_iou(bbox_a, bbox_b) >= 0.18:
        return True

    center_a = a.get("center_norm") if isinstance(a.get("center_norm"), dict) else {}
    center_b = b.get("center_norm") if isinstance(b.get("center_norm"), dict) else {}
    try:
        ax = float(center_a.get("x", 0.5))
        ay = float(center_a.get("y", 0.5))
        bx = float(center_b.get("x", 0.5))
        by = float(center_b.get("y", 0.5))
    except (TypeError, ValueError):
        return False

    support_a = a.get("cue_support") if isinstance(a.get("cue_support"), dict) else {}
    support_b = b.get("cue_support") if isinstance(b.get("cue_support"), dict) else {}
    face_only_a = bool(support_a.get("face")) and not bool(support_a.get("upperbody")) and not bool(support_a.get("hog"))
    face_only_b = bool(support_b.get("face")) and not bool(support_b.get("upperbody")) and not bool(support_b.get("hog"))
    if face_only_a and face_only_b and abs(ax - bx) <= 0.16 and abs(ay - by) <= 0.5:
        return True
    if abs(ax - bx) <= 0.11 and abs(ay - by) <= 0.42 and (face_only_a or face_only_b):
        return True
    return False


def build_person_candidates(
    *,
    face_detections: list[tuple[tuple[int, int, int, int], float]],
    upperbody_detections: list[tuple[tuple[int, int, int, int], float]],
    hog_detections: list[tuple[tuple[int, int, int, int], float]],
    frame_width: int,
    frame_height: int,
    previous_size_norm: float | None,
    standalone_hog_min_confidence: float,
) -> list[dict[str, Any]]:
    anchors: list[dict[str, Any]] = []
    frame_area = float(max(1, frame_width * frame_height))

    for bbox, confidence in face_detections:
        expanded = expand_face_bbox(bbox, frame_width=frame_width, frame_height=frame_height)
        if expanded is None:
            continue
        face_center_x = (bbox[0] + (bbox[2] / 2.0)) / frame_width
        face_center_y = (bbox[1] + (bbox[3] / 2.0)) / frame_height
        merged = False
        for anchor in anchors:
            if not anchor["has_face"]:
                continue
            existing_face_center_x, existing_face_center_y = anchor["face_center"]
            if abs(face_center_x - existing_face_center_x) > 0.1:
                continue
            if abs(face_center_y - existing_face_center_y) > 0.3:
                continue
            if bbox_iou(expanded, anchor["bbox"]) < 0.05 and face_center_y <= existing_face_center_y:
                continue
            anchor["bbox"] = clip_bbox(
                (
                    min(anchor["bbox"][0], expanded[0]),
                    min(anchor["bbox"][1], expanded[1]),
                    max(anchor["bbox"][0] + anchor["bbox"][2], expanded[0] + expanded[2]) - min(anchor["bbox"][0], expanded[0]),
                    max(anchor["bbox"][1] + anchor["bbox"][3], expanded[1] + expanded[3]) - min(anchor["bbox"][1], expanded[1]),
                ),
                frame_width=frame_width,
                frame_height=frame_height,
            ) or anchor["bbox"]
            anchor["confidence"] = max(anchor["confidence"], confidence)
            anchor["face_hits"] += 1
            anchor["face_area"] = max(anchor["face_area"], float(max(1, bbox[2] * bbox[3])))
            anchor["face_center"] = (
                (existing_face_center_x + face_center_x) / 2.0,
                (existing_face_center_y + face_center_y) / 2.0,
            )
            merged = True
            break
        if merged:
            continue
        anchors.append(
            {
                "bbox": expanded,
                "confidence": confidence,
                "has_face": True,
                "face_hits": 1,
                "face_area": float(max(1, bbox[2] * bbox[3])),
                "face_center": (face_center_x, face_center_y),
                "has_upperbody": False,
                "has_hog": False,
            }
        )

    for bbox, confidence in upperbody_detections:
        merged = False
        for anchor in anchors:
            if bbox_iou(bbox, anchor["bbox"]) >= 0.12:
                anchor["bbox"] = clip_bbox(
                    (
                        min(anchor["bbox"][0], bbox[0]),
                        min(anchor["bbox"][1], bbox[1]),
                        max(anchor["bbox"][0] + anchor["bbox"][2], bbox[0] + bbox[2]) - min(anchor["bbox"][0], bbox[0]),
                        max(anchor["bbox"][1] + anchor["bbox"][3], bbox[1] + bbox[3]) - min(anchor["bbox"][1], bbox[1]),
                    ),
                    frame_width=frame_width,
                    frame_height=frame_height,
                ) or anchor["bbox"]
                anchor["confidence"] = max(anchor["confidence"], confidence)
                anchor["has_upperbody"] = True
                merged = True
                break
        if not merged:
            anchors.append(
                {
                    "bbox": bbox,
                    "confidence": confidence,
                    "has_face": False,
                    "face_hits": 0,
                    "face_area": 0.0,
                    "face_center": (0.5, 0.5),
                    "has_upperbody": True,
                    "has_hog": False,
                }
            )

    for bbox, confidence in hog_detections:
        matched = False
        for anchor in anchors:
            if bbox_iou(bbox, anchor["bbox"]) >= 0.1:
                anchor["bbox"] = clip_bbox(
                    (
                        min(anchor["bbox"][0], bbox[0]),
                        min(anchor["bbox"][1], bbox[1]),
                        max(anchor["bbox"][0] + anchor["bbox"][2], bbox[0] + bbox[2]) - min(anchor["bbox"][0], bbox[0]),
                        max(anchor["bbox"][1] + anchor["bbox"][3], bbox[1] + bbox[3]) - min(anchor["bbox"][1], bbox[1]),
                    ),
                    frame_width=frame_width,
                    frame_height=frame_height,
                ) or anchor["bbox"]
                anchor["confidence"] = max(anchor["confidence"], min(0.96, confidence + 0.04))
                anchor["has_hog"] = True
                matched = True
                break
        if not matched and is_plausible_standalone_hog(
            bbox,
            frame_width=frame_width,
            frame_height=frame_height,
            confidence=confidence,
            min_confidence=standalone_hog_min_confidence,
        ):
            anchors.append(
                {
                    "bbox": bbox,
                    "confidence": confidence,
                    "has_face": False,
                    "face_hits": 0,
                    "face_area": 0.0,
                    "face_center": (0.5, 0.5),
                    "has_upperbody": False,
                    "has_hog": True,
                }
            )

    candidates: list[dict[str, Any]] = []
    for anchor in anchors:
        bbox = anchor["bbox"]
        confidence = float(anchor["confidence"])
        face_area_ratio = float(anchor.get("face_area") or 0.0) / frame_area
        bbox_top_norm = bbox[1] / max(1.0, float(frame_height))
        bbox_size_norm = (bbox[2] * bbox[3]) / frame_area
        if (
            anchor["has_face"]
            and not anchor["has_upperbody"]
            and not anchor["has_hog"]
            and anchor["face_hits"] <= 1
            and face_area_ratio < 0.0018
            and bbox_top_norm < 0.24
            and bbox_size_norm < 0.018
        ):
            continue
        if anchor["has_face"]:
            detector = "haar_face"
            confidence = min(0.98, confidence + (0.03 if anchor["has_upperbody"] else 0.0) + (0.02 if anchor["has_hog"] else 0.0))
        else:
            detector = "hog_person"
            confidence = min(0.94, confidence + (0.04 if anchor["has_upperbody"] else 0.0))

        candidates.append(
            make_track_entry(
                track_id=0,
                bbox=bbox,
                detector=detector,
                target_class="person",
                confidence=confidence,
                frame_width=frame_width,
                frame_height=frame_height,
                previous_size_norm=previous_size_norm,
            )
        )
        candidates[-1]["cue_support"] = {
            "face": bool(anchor["has_face"]),
            "upperbody": bool(anchor["has_upperbody"]),
            "hog": bool(anchor["has_hog"]),
        }
        candidates[-1]["face_hits"] = int(anchor["face_hits"])

    ranked = sorted(candidates, key=lambda item: item.get("selection_score", 0.0), reverse=True)
    filtered: list[dict[str, Any]] = []
    for item in ranked:
        if any(same_person_candidate(item, existing, frame_width=frame_width, frame_height=frame_height) for existing in filtered):
            continue
        filtered.append(item)
    return filtered


def compute_foreground_mask(frame: np.ndarray, subtractor: cv2.BackgroundSubtractor) -> np.ndarray:
    fg = subtractor.apply(frame)
    kernel = np.ones((5, 5), np.uint8)
    fg = cv2.morphologyEx(fg, cv2.MORPH_OPEN, kernel)
    fg = cv2.morphologyEx(fg, cv2.MORPH_CLOSE, kernel)
    return fg


def detect_motion_from_mask(
    frame: np.ndarray,
    fg: np.ndarray,
    *,
    min_area_ratio: float,
    warmup_count: int,
    warmup_frames: int,
) -> tuple[tuple[int, int, int, int] | None, int]:
    contours, _ = cv2.findContours(fg, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    h, w = frame.shape[:2]
    min_area_px = min_area_ratio * w * h

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


def detect_motion(
    frame: np.ndarray,
    subtractor: cv2.BackgroundSubtractor,
    *,
    min_area_ratio: float,
    warmup_count: int,
    warmup_frames: int,
) -> tuple[tuple[int, int, int, int] | None, int]:
    fg = compute_foreground_mask(frame, subtractor)
    return detect_motion_from_mask(
        frame,
        fg,
        min_area_ratio=min_area_ratio,
        warmup_count=warmup_count,
        warmup_frames=warmup_frames,
    )


def denormalize_bbox(bbox_norm: dict[str, Any] | None, *, frame_width: int, frame_height: int) -> tuple[int, int, int, int] | None:
    if not isinstance(bbox_norm, dict):
        return None
    try:
        return (
            int(round(float(bbox_norm["x"]) * frame_width)),
            int(round(float(bbox_norm["y"]) * frame_height)),
            int(round(float(bbox_norm["w"]) * frame_width)),
            int(round(float(bbox_norm["h"]) * frame_height)),
        )
    except (KeyError, TypeError, ValueError):
        return None


def overlap_ratio(a: tuple[int, int, int, int], b: tuple[int, int, int, int] | None) -> float:
    if b is None:
        return 0.0
    ax, ay, aw, ah = a
    bx, by, bw, bh = b
    left = max(ax, bx)
    top = max(ay, by)
    right = min(ax + aw, bx + bw)
    bottom = min(ay + ah, by + bh)
    if right <= left or bottom <= top:
        return 0.0
    intersection = float((right - left) * (bottom - top))
    a_area = float(max(1, aw * ah))
    return intersection / a_area


def detect_hand_arm_cue(
    frame: np.ndarray,
    fg_mask: np.ndarray,
    *,
    selected_target: dict[str, Any] | None,
    warmup_count: int,
    warmup_frames: int,
    args: argparse.Namespace,
) -> dict[str, Any] | None:
    if warmup_count <= warmup_frames:
        return None

    h, w = frame.shape[:2]
    ycrcb = cv2.cvtColor(frame, cv2.COLOR_BGR2YCrCb)
    skin = cv2.inRange(
        ycrcb,
        np.array((0, 133, 77), dtype=np.uint8),
        np.array((255, 178, 127), dtype=np.uint8),
    )
    motion = cv2.threshold(fg_mask, 127, 255, cv2.THRESH_BINARY)[1]

    kernel = np.ones((5, 5), np.uint8)
    combined = cv2.bitwise_and(skin, motion)
    combined = cv2.morphologyEx(combined, cv2.MORPH_OPEN, kernel)
    combined = cv2.morphologyEx(combined, cv2.MORPH_CLOSE, kernel)
    contours, _ = cv2.findContours(combined, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    selected_bbox = denormalize_bbox(
        selected_target.get("bbox_norm") if isinstance(selected_target, dict) else None,
        frame_width=w,
        frame_height=h,
    )
    selected_center = None
    if isinstance(selected_target, dict) and isinstance(selected_target.get("center_norm"), dict):
        selected_center = selected_target["center_norm"]

    best: dict[str, Any] | None = None
    best_score = 0.0
    frame_area = float(w * h)

    for contour in contours:
        area = float(cv2.contourArea(contour))
        area_ratio = area / frame_area
        if area_ratio < args.hand_cue_min_area_ratio or area_ratio > args.hand_cue_max_area_ratio:
            continue

        x, y, bw, bh = cv2.boundingRect(contour)
        bbox_area = float(max(1, bw * bh))
        center_x = (x + (bw / 2.0)) / w
        center_y = (y + (bh / 2.0)) / h
        if center_y < args.hand_cue_min_center_y:
            continue

        fill_ratio = area / bbox_area
        if fill_ratio < 0.12:
            continue

        motion_ratio = float(cv2.countNonZero(motion[y : y + bh, x : x + bw])) / bbox_area
        if motion_ratio < args.hand_cue_min_motion_ratio:
            continue

        if selected_center is not None:
            try:
                selected_center_x = float(selected_center.get("x", 0.5))
                selected_center_y = float(selected_center.get("y", 0.5))
            except (TypeError, ValueError):
                selected_center_x = 0.5
                selected_center_y = 0.5
            if center_y <= selected_center_y + 0.02:
                continue
            if abs(center_x - selected_center_x) > 0.38:
                continue
        else:
            # Without a stable tracked person, only trust cues that come from the
            # lower booth interaction zone instead of the upper-right face region.
            if center_y < 0.60:
                continue
            if center_x < 0.38 or center_x > 0.78:
                continue

        if overlap_ratio((x, y, bw, bh), selected_bbox) > 0.35:
            continue

        size_score = min(area_ratio / max(args.hand_cue_min_area_ratio * 6.0, 1e-6), 1.0)
        motion_score = min(motion_ratio / max(args.hand_cue_min_motion_ratio * 2.0, 1e-6), 1.0)
        confidence = round(min(0.98, 0.35 + (size_score * 0.25) + (motion_score * 0.25) + (fill_ratio * 0.2)), 4)
        if confidence < args.hand_cue_min_confidence:
            continue

        candidate = {
            "hand_arm_present": True,
            "detector": "skin_motion_hand",
            "confidence": confidence,
            "bbox_norm": {
                "x": round(x / w, 4),
                "y": round(y / h, 4),
                "w": round(bw / w, 4),
                "h": round(bh / h, 4),
            },
            "center_norm": {"x": round(center_x, 4), "y": round(center_y, 4)},
            "horizontal_zone": classify_horizontal_zone(center_x),
            "vertical_zone": classify_vertical_zone(center_y),
            "area_ratio": round(area_ratio, 6),
            "motion_ratio": round(motion_ratio, 4),
            "reason": "skin+motion cue in lower interaction region",
        }
        if confidence > best_score:
            best_score = confidence
            best = candidate

    return best


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
    tracks: list[dict[str, Any]] | None = None,
    selected_target: dict[str, Any] | None = None,
    multi_target_payload: dict[str, Any] | None = None,
    interaction_hint: dict[str, Any] | None = None,
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

    if selected_target is not None:
        detector = str(selected_target.get("detector") or detector)
        target_class = str(selected_target.get("target_class") or target_class)
        confidence = float(selected_target.get("confidence") or confidence)
        bbox_norm = selected_target.get("bbox_norm")
        center = selected_target.get("center_norm")
        if isinstance(center, dict):
            center_x = float(center.get("x", 0.5))
            center_y = float(center.get("y", 0.5))
        horizontal_zone = str(selected_target.get("horizontal_zone") or "unknown")
        vertical_zone = str(selected_target.get("vertical_zone") or "unknown")
        size_norm = selected_target.get("size_norm")
        distance_band = str(selected_target.get("distance_band") or "unknown")
        approach_state = str(selected_target.get("approach_state") or "unknown")
        bbox_area_px = selected_target.get("bbox_area_px")
        size_delta_norm = selected_target.get("size_delta_norm")
        target_present = True

    selected_lock_state = None if selected_target is None else selected_target.get("lock_state")
    if target_count >= 2 and selected_lock_state != "locked":
        event_type = "multi_target_seen"
    elif target_present and not state.last_target_present:
        event_type = "target_seen"
    elif target_present and state.last_target_present:
        event_type = "target_updated"
    elif (not target_present) and state.last_target_present:
        event_type = "target_lost"
    else:
        event_type = "no_target"

    if target_count >= 2 and selected_lock_state != "locked":
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
            "track_id": None if selected_target is None else selected_target.get("track_id"),
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
    if tracks is not None:
        event["tracks"] = tracks
    if selected_target is not None:
        event["selected_target"] = {
            "track_id": selected_target.get("track_id"),
            "lock_state": selected_target.get("lock_state"),
            "reason": selected_target.get("reason"),
            "target_class": selected_target.get("target_class"),
            "detector": selected_target.get("detector"),
            "confidence": selected_target.get("confidence"),
            "bbox_norm": selected_target.get("bbox_norm"),
            "center_norm": selected_target.get("center_norm"),
            "horizontal_zone": selected_target.get("horizontal_zone"),
            "vertical_zone": selected_target.get("vertical_zone"),
            "size_norm": selected_target.get("size_norm"),
            "distance_band": selected_target.get("distance_band"),
            "approach_state": selected_target.get("approach_state"),
            "selection_score": selected_target.get("selection_score"),
        }
    if multi_target_payload:
        event["payload"] = multi_target_payload
    if interaction_hint is not None:
        event["interaction_hint"] = interaction_hint
    return event


def extract_seq_from_name(filename: str) -> str | None:
    if "-seq-" not in filename:
        return None
    seq = filename.split("-seq-", 1)[1]
    if seq.lower().endswith(".jpg"):
        seq = seq[:-4]
    return seq


def process_frame(
    path: Path,
    state: ExtractorState,
    subtractor: cv2.BackgroundSubtractor,
    cascades: CascadeBundle,
    hog: Any,
    args: argparse.Namespace,
) -> dict[str, Any]:
    frame = load_image(path)
    if frame is None:
        raise RuntimeError(f"Failed to decode JPEG frame: {path}")

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    operator_state = load_operator_state(args.operator_state_file)
    fg_mask = compute_foreground_mask(frame, subtractor)
    state.bg_warmup_count += 1

    person_detections = detect_people(frame, hog, min_confidence=args.hog_min_confidence) if args.enable_hog_person else []
    faces = detect_faces(gray, cascades, args)
    upper_bodies = detect_upper_bodies(gray, cascades, args)
    candidates = build_person_candidates(
        face_detections=faces,
        upperbody_detections=upper_bodies,
        hog_detections=person_detections,
        frame_width=frame.shape[1],
        frame_height=frame.shape[0],
        previous_size_norm=state.last_size_norm,
        standalone_hog_min_confidence=args.standalone_hog_min_confidence,
    )
    if not candidates:
        motion_bbox, warmup_count = detect_motion_from_mask(
            frame,
            fg_mask,
            min_area_ratio=args.min_motion_area_ratio,
            warmup_count=state.bg_warmup_count,
            warmup_frames=args.warmup_frames,
        )
        state.bg_warmup_count = warmup_count
        if motion_bbox is not None:
            candidates.append(
                make_track_entry(
                    track_id=0,
                    bbox=motion_bbox,
                    detector="background_motion",
                    target_class="motion_blob",
                    confidence=0.55,
                    frame_width=frame.shape[1],
                    frame_height=frame.shape[0],
                    previous_size_norm=state.last_size_norm,
                )
            )

    candidates = [item for item in candidates if within_engagement_zone(item, args)]

    tracks = assign_track_ids(candidates, state)
    selected_target = choose_selected_target(tracks, state, operator_state=operator_state)
    bbox = None
    detector = "none"
    target_class = "none"
    confidence = 0.0
    target_count = len(tracks)
    multi_target_payload = None

    if selected_target is not None:
        state.missing_frame_count = 0
        state.last_selected_target = dict(selected_target)
        detector = str(selected_target["detector"])
        target_class = str(selected_target["target_class"])
        confidence = float(selected_target["confidence"])
        bbox_norm = selected_target["bbox_norm"]
        if isinstance(bbox_norm, dict):
            bbox = (
                int(round(float(bbox_norm["x"]) * frame.shape[1])),
                int(round(float(bbox_norm["y"]) * frame.shape[0])),
                int(round(float(bbox_norm["w"]) * frame.shape[1])),
                int(round(float(bbox_norm["h"]) * frame.shape[0])),
            )
    else:
        state.missing_frame_count += 1
        selected_target = hold_selected_target(state, args)
        if selected_target is None:
            state.selected_track_id = None
            state.last_selected_target = None
        else:
            detector = str(selected_target["detector"])
            target_class = str(selected_target["target_class"])
            confidence = float(selected_target["confidence"])
            bbox_norm = selected_target.get("bbox_norm")
            if isinstance(bbox_norm, dict):
                bbox = (
                    int(round(float(bbox_norm["x"]) * frame.shape[1])),
                    int(round(float(bbox_norm["y"]) * frame.shape[0])),
                    int(round(float(bbox_norm["w"]) * frame.shape[1])),
                    int(round(float(bbox_norm["h"]) * frame.shape[0])),
                )

    if len(tracks) >= 2:
        ranked = sorted(tracks, key=lambda item: item.get("selection_score", 0.0), reverse=True)
        primary = ranked[0]
        secondary = ranked[1]
        multi_target_payload = {
            "targetCount": len(tracks),
            "primaryDirection": primary["horizontal_zone"],
            "secondaryDirection": secondary["horizontal_zone"],
        }

    interaction_hint = detect_hand_arm_cue(
        frame,
        fg_mask,
        selected_target=selected_target,
        warmup_count=state.bg_warmup_count,
        warmup_frames=args.warmup_frames,
        args=args,
    )

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
        tracks=tracks,
        selected_target=selected_target,
        multi_target_payload=multi_target_payload,
        interaction_hint=interaction_hint,
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

    frontal_default = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
    if frontal_default.empty():
        raise SystemExit("OpenCV haarcascade_frontalface_default.xml is unavailable.")
    frontal_alt2 = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_alt2.xml")
    if frontal_alt2.empty():
        frontal_alt2 = None
    profile = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_profileface.xml")
    if profile.empty():
        profile = None
    upperbody = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_upperbody.xml")
    if upperbody.empty():
        upperbody = None
    cascades = CascadeBundle(
        frontal_default=frontal_default,
        frontal_alt2=frontal_alt2,
        profile=profile,
        upperbody=upperbody,
    )

    hog = None
    if args.enable_hog_person:
        hog = cv2.HOGDescriptor()
        hog.setSVMDetector(cv2.HOGDescriptor_getDefaultPeopleDetector())

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
            event = process_frame(latest, state, subtractor, cascades, hog, args)
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
