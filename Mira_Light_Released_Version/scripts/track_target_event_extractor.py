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

from face_identity import (
    crop_bbox_with_padding,
    extract_face_embedding,
    load_face_registry,
    match_face_embedding,
)

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
    parser.add_argument(
        "--selected-target-max-center-distance",
        type=float,
        default=0.16,
        help="Maximum normalized center distance allowed when recovering the previous target after track-id churn.",
    )
    parser.add_argument(
        "--selected-target-max-size-delta",
        type=float,
        default=0.045,
        help="Maximum |size_norm| delta allowed when recovering the previous target by spatial continuity.",
    )
    parser.add_argument(
        "--selected-target-switch-margin",
        type=float,
        default=0.22,
        help="Required score advantage before automatic selection abandons the current stable target.",
    )
    parser.add_argument(
        "--default-target-mode",
        choices=["person_follow", "tabletop_follow"],
        default="person_follow",
        help="Default target-selection strategy when the operator state does not override it.",
    )
    parser.add_argument(
        "--tabletop-roi-top",
        type=float,
        default=0.50,
        help="Normalized top bound of the tabletop/object search ROI.",
    )
    parser.add_argument(
        "--tabletop-roi-bottom",
        type=float,
        default=0.96,
        help="Normalized bottom bound of the tabletop/object search ROI.",
    )
    parser.add_argument(
        "--tabletop-roi-left",
        type=float,
        default=0.08,
        help="Normalized left bound of the tabletop/object search ROI.",
    )
    parser.add_argument(
        "--tabletop-roi-right",
        type=float,
        default=0.92,
        help="Normalized right bound of the tabletop/object search ROI.",
    )
    parser.add_argument(
        "--tabletop-min-area-ratio",
        type=float,
        default=0.004,
        help="Minimum frame-area ratio for a tabletop object candidate.",
    )
    parser.add_argument(
        "--tabletop-max-area-ratio",
        type=float,
        default=0.22,
        help="Maximum frame-area ratio for a tabletop object candidate.",
    )
    parser.add_argument(
        "--tabletop-min-edge-ratio",
        type=float,
        default=0.05,
        help="Minimum Canny-edge occupancy inside a tabletop candidate bbox.",
    )
    parser.add_argument(
        "--tabletop-min-motion-ratio",
        type=float,
        default=0.01,
        help="Minimum foreground-motion occupancy that boosts a tabletop candidate.",
    )
    parser.add_argument(
        "--tabletop-min-aspect-ratio",
        type=float,
        default=0.45,
        help="Minimum bbox aspect ratio (w/h) for a tabletop candidate.",
    )
    parser.add_argument(
        "--tabletop-max-aspect-ratio",
        type=float,
        default=2.2,
        help="Maximum bbox aspect ratio (w/h) for a tabletop candidate.",
    )
    parser.add_argument(
        "--tabletop-hold-missing-frames",
        type=int,
        default=6,
        help="How many consecutive empty frames to keep the last tabletop target alive before declaring loss.",
    )
    parser.add_argument(
        "--tabletop-switch-margin",
        type=float,
        default=0.34,
        help="Required score advantage before tabletop mode abandons the current stable target.",
    )
    parser.add_argument(
        "--tabletop-max-center-distance",
        type=float,
        default=0.22,
        help="Maximum normalized center distance allowed when recovering the previous tabletop target.",
    )
    parser.add_argument(
        "--tabletop-max-size-delta",
        type=float,
        default=0.065,
        help="Maximum |size_norm| delta allowed when recovering the previous tabletop target.",
    )
    parser.add_argument(
        "--tabletop-max-aspect-delta",
        type=float,
        default=0.48,
        help="Maximum |aspect_ratio| delta allowed when recovering the previous tabletop target.",
    )
    parser.add_argument(
        "--owner-face-registry",
        type=Path,
        help="Optional owner-face registry JSON built by register_owner_face.py.",
    )
    parser.add_argument(
        "--owner-match-threshold",
        type=float,
        default=0.82,
        help="Cosine-similarity threshold for treating a detected face as the registered owner.",
    )
    parser.add_argument(
        "--owner-selection-bonus",
        type=float,
        default=0.24,
        help="Selection-score bonus applied when a candidate face/person matches the registered owner.",
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


def match_owner_faces(
    frame: np.ndarray,
    faces: list[tuple[int, int, int, int]],
    owner_registry: dict[str, Any] | None,
    *,
    threshold: float,
) -> list[dict[str, Any]]:
    if owner_registry is None:
        return []

    matches: list[dict[str, Any]] = []
    frame_width = float(frame.shape[1])
    frame_height = float(frame.shape[0])
    for bbox in faces:
        crop = crop_bbox_with_padding(frame, bbox)
        embedding = extract_face_embedding(crop) if crop is not None else None
        match = match_face_embedding(embedding, owner_registry, threshold=threshold)
        if not match["matched"]:
            continue
        x, y, bw, bh = bbox
        center_x = (x + (bw / 2.0)) / frame_width
        center_y = (y + (bh / 2.0)) / frame_height
        matches.append(
            {
                "bbox": tuple(int(value) for value in bbox),
                "owner_id": match["owner_id"],
                "owner_confidence": round(float(match["confidence"]), 4),
                "owner_direction": classify_horizontal_zone(center_x),
                "center_norm": {"x": round(center_x, 4), "y": round(center_y, 4)},
            }
        )
    return matches


def select_best_owner_observation(owner_matches: list[dict[str, Any]]) -> dict[str, Any] | None:
    if not owner_matches:
        return None
    return max(owner_matches, key=lambda item: float(item.get("owner_confidence") or 0.0))


def apply_owner_match_to_track(track: dict[str, Any], owner_match: dict[str, Any], *, selection_bonus: float) -> None:
    track["owner_face_found"] = True
    track["owner_id"] = owner_match.get("owner_id")
    track["owner_confidence"] = round(float(owner_match.get("owner_confidence") or 0.0), 4)
    track["owner_direction"] = owner_match.get("owner_direction") or track.get("horizontal_zone") or "unknown"
    track["selection_score"] = round(float(track.get("selection_score", 0.0) or 0.0) + selection_bonus, 4)
    track["confidence"] = round(min(0.99, float(track.get("confidence", 0.0) or 0.0) + 0.04), 4)


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


def infer_scene_hint(
    target_present: bool,
    distance_band: str,
    approach_state: str,
    horizontal_zone: str,
    *,
    target_mode: str,
    target_class: str,
) -> tuple[str, str]:
    if not target_present:
        return "sleep", "当前没有稳定目标，适合回到休息或等待状态。"
    if target_mode == "tabletop_follow" or target_class == "object":
        return "track_target", "桌面目标已进入工作区，适合进入桌面目标跟随。"
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
    target_mode: str,
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
        "target_mode": target_mode,
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
            "bbox_norm": dict(item["bbox_norm"]),
        }
        for item in assigned
    }
    return assigned


def continuity_center_distance(track: dict[str, Any], reference: dict[str, Any]) -> float | None:
    center = track.get("center_norm")
    ref_center = reference.get("center_norm")
    if not isinstance(center, dict) or not isinstance(ref_center, dict):
        return None
    try:
        dx = float(center.get("x", 0.5)) - float(ref_center.get("x", 0.5))
        dy = float(center.get("y", 0.5)) - float(ref_center.get("y", 0.5))
    except (TypeError, ValueError):
        return None
    return (dx * dx + dy * dy) ** 0.5


def continuity_size_delta(track: dict[str, Any], reference: dict[str, Any]) -> float | None:
    try:
        track_size = float(track.get("size_norm"))
        ref_size = float(reference.get("size_norm"))
    except (TypeError, ValueError):
        return None
    return abs(track_size - ref_size)


def continuity_metric_delta(track: dict[str, Any], reference: dict[str, Any], key: str) -> float | None:
    try:
        track_value = float(track.get(key))
        ref_value = float(reference.get(key))
    except (TypeError, ValueError):
        return None
    return abs(track_value - ref_value)


def find_continuity_target(
    tracks: list[dict[str, Any]],
    reference: dict[str, Any] | None,
    *,
    max_center_distance: float,
    max_size_delta: float,
) -> tuple[dict[str, Any] | None, float | None, float | None]:
    if reference is None:
        return None, None, None

    best_track = None
    best_center_distance = None
    best_size_delta = None
    best_metric = 999.0
    reference_class = str(reference.get("target_class") or "")

    for item in tracks:
        if reference_class and str(item.get("target_class") or "") != reference_class:
            continue
        center_distance = continuity_center_distance(item, reference)
        if center_distance is None or center_distance > max_center_distance:
            continue
        size_delta = continuity_size_delta(item, reference)
        if size_delta is not None and size_delta > max_size_delta:
            continue
        detector_penalty = 0.0 if str(item.get("detector") or "") == str(reference.get("detector") or "") else 0.03
        metric = center_distance + ((size_delta or 0.0) * 0.85) + detector_penalty
        if metric < best_metric:
            best_metric = metric
            best_track = item
            best_center_distance = center_distance
            best_size_delta = size_delta

    return best_track, best_center_distance, best_size_delta


def find_tabletop_continuity_target(
    tracks: list[dict[str, Any]],
    reference: dict[str, Any] | None,
    *,
    max_center_distance: float,
    max_size_delta: float,
    max_aspect_delta: float,
) -> tuple[dict[str, Any] | None, dict[str, float | None]]:
    if reference is None:
        return None, {}

    best_track = None
    best_metric = 999.0
    best_diagnostics: dict[str, float | None] = {}

    for item in tracks:
        if str(item.get("target_mode") or "") != "tabletop_follow":
            continue
        center_distance = continuity_center_distance(item, reference)
        if center_distance is None or center_distance > max_center_distance:
            continue
        size_delta = continuity_size_delta(item, reference)
        if size_delta is not None and size_delta > max_size_delta:
            continue
        aspect_delta = continuity_metric_delta(item, reference, "aspect_ratio")
        if aspect_delta is not None and aspect_delta > max_aspect_delta:
            continue
        edge_delta = continuity_metric_delta(item, reference, "edge_ratio")
        motion_delta = continuity_metric_delta(item, reference, "motion_ratio")
        metric = center_distance
        metric += (size_delta or 0.0) * 0.7
        metric += (aspect_delta or 0.0) * 0.3
        metric += (edge_delta or 0.0) * 0.25
        metric += (motion_delta or 0.0) * 0.15
        if metric < best_metric:
            best_metric = metric
            best_track = item
            best_diagnostics = {
                "continuity_distance_norm": center_distance,
                "continuity_size_delta": size_delta,
                "continuity_aspect_delta": aspect_delta,
                "continuity_edge_delta": edge_delta,
                "continuity_motion_delta": motion_delta,
            }

    return best_track, best_diagnostics


def decorate_selected_target(
    track: dict[str, Any],
    *,
    lock_state: str,
    reason: str,
    best_score: float | None = None,
    continuity_distance_norm: float | None = None,
    continuity_size_delta: float | None = None,
    continuity_aspect_delta: float | None = None,
    continuity_edge_delta: float | None = None,
    continuity_motion_delta: float | None = None,
) -> dict[str, Any]:
    selected = dict(track)
    selected["lock_state"] = lock_state
    selected["reason"] = reason
    if best_score is not None:
        try:
            margin = max(0.0, float(best_score) - float(track.get("selection_score", 0.0) or 0.0))
        except (TypeError, ValueError):
            margin = 0.0
        selected["score_margin_to_best"] = round(margin, 4)
    if continuity_distance_norm is not None:
        selected["continuity_distance_norm"] = round(continuity_distance_norm, 4)
    if continuity_size_delta is not None:
        selected["continuity_size_delta"] = round(continuity_size_delta, 4)
    if continuity_aspect_delta is not None:
        selected["continuity_aspect_delta"] = round(continuity_aspect_delta, 4)
    if continuity_edge_delta is not None:
        selected["continuity_edge_delta"] = round(continuity_edge_delta, 4)
    if continuity_motion_delta is not None:
        selected["continuity_motion_delta"] = round(continuity_motion_delta, 4)
    return selected


def choose_selected_target(
    tracks: list[dict[str, Any]],
    state: ExtractorState,
    *,
    args: argparse.Namespace | None = None,
    operator_state: dict[str, Any] | None = None,
) -> dict[str, Any] | None:
    if not tracks:
        return None

    ranked = sorted(tracks, key=lambda item: item.get("selection_score", 0.0), reverse=True)
    best_track = ranked[0]
    best_score = float(best_track.get("selection_score", 0.0) or 0.0)
    last_selected_mode = state.last_selected_target.get("target_mode") if state.last_selected_target else None
    mode = str(best_track.get("target_mode") or last_selected_mode or "person_follow")
    is_tabletop = mode == "tabletop_follow"
    switch_margin = float(
        getattr(args, "tabletop_switch_margin", 0.34)
        if is_tabletop
        else getattr(args, "selected_target_switch_margin", 0.22)
    )
    max_center_distance = float(
        getattr(args, "tabletop_max_center_distance", 0.22)
        if is_tabletop
        else getattr(args, "selected_target_max_center_distance", 0.16)
    )
    max_size_delta = float(
        getattr(args, "tabletop_max_size_delta", 0.065)
        if is_tabletop
        else getattr(args, "selected_target_max_size_delta", 0.045)
    )
    max_aspect_delta = float(getattr(args, "tabletop_max_aspect_delta", 0.48))

    operator_lock_track_id = parse_operator_lock_track_id(operator_state)
    if operator_lock_track_id is not None:
        for item in tracks:
            if int(item["track_id"]) == operator_lock_track_id:
                state.selected_track_id = operator_lock_track_id
                return decorate_selected_target(
                    item,
                    lock_state="operator_locked",
                    reason="director console requested target lock",
                    best_score=best_score,
                )

    locked_track = None
    if state.selected_track_id is not None:
        for item in tracks:
            if int(item["track_id"]) == state.selected_track_id:
                locked_track = item
                break

    if locked_track is not None:
        margin = max(0.0, best_score - float(locked_track.get("selection_score", 0.0) or 0.0))
        if int(best_track["track_id"]) != int(locked_track["track_id"]) and margin > switch_margin:
            state.selected_track_id = int(best_track["track_id"])
            return decorate_selected_target(
                best_track,
                lock_state="locked",
                reason=(
                    f"auto-switched from track {locked_track['track_id']} because "
                    f"score margin {margin:.2f} exceeded {switch_margin:.2f}"
                ),
                best_score=best_score,
            )
        return decorate_selected_target(
            locked_track,
            lock_state="locked",
            reason=(
                "previous selected tabletop target still visible"
                if str(locked_track.get("target_mode") or "") == "tabletop_follow"
                else "previous selected target still visible"
            ),
            best_score=best_score,
        )

    if is_tabletop:
        continuity_track, continuity_diagnostics = find_tabletop_continuity_target(
            tracks,
            state.last_selected_target,
            max_center_distance=max_center_distance,
            max_size_delta=max_size_delta,
            max_aspect_delta=max_aspect_delta,
        )
        if continuity_track is not None:
            margin = max(0.0, best_score - float(continuity_track.get("selection_score", 0.0) or 0.0))
            if int(continuity_track["track_id"]) == int(best_track["track_id"]) or margin <= switch_margin:
                state.selected_track_id = int(continuity_track["track_id"])
                return decorate_selected_target(
                    continuity_track,
                    lock_state="locked",
                    reason="recovered previous tabletop target by spatial continuity",
                    best_score=best_score,
                    continuity_distance_norm=continuity_diagnostics.get("continuity_distance_norm"),
                    continuity_size_delta=continuity_diagnostics.get("continuity_size_delta"),
                    continuity_aspect_delta=continuity_diagnostics.get("continuity_aspect_delta"),
                    continuity_edge_delta=continuity_diagnostics.get("continuity_edge_delta"),
                    continuity_motion_delta=continuity_diagnostics.get("continuity_motion_delta"),
                )
    else:
        continuity_track, continuity_distance, continuity_size = find_continuity_target(
            tracks,
            state.last_selected_target,
            max_center_distance=max_center_distance,
            max_size_delta=max_size_delta,
        )
        if continuity_track is not None:
            margin = max(0.0, best_score - float(continuity_track.get("selection_score", 0.0) or 0.0))
            if int(continuity_track["track_id"]) == int(best_track["track_id"]) or margin <= switch_margin:
                state.selected_track_id = int(continuity_track["track_id"])
                return decorate_selected_target(
                    continuity_track,
                    lock_state="locked",
                    reason="recovered previous selected target by spatial continuity",
                    best_score=best_score,
                    continuity_distance_norm=continuity_distance,
                    continuity_size_delta=continuity_size,
                )

    selected = dict(best_track)
    if len(tracks) == 1:
        state.selected_track_id = int(selected["track_id"])
        return decorate_selected_target(
            selected,
            lock_state="locked",
            reason="single visible tabletop target" if is_tabletop else "single visible target",
            best_score=best_score,
        )
    else:
        state.selected_track_id = None
        return decorate_selected_target(
            selected,
            lock_state="candidate",
            reason=(
                "highest score among multiple visible tabletop targets"
                if is_tabletop
                else "highest score among multiple visible targets"
            ),
            best_score=best_score,
        )

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


def resolve_target_mode(operator_state: dict[str, Any] | None, args: argparse.Namespace) -> str:
    raw = ""
    if isinstance(operator_state, dict):
        raw = str(operator_state.get("targetMode") or "").strip().lower()
    if raw in {"person_follow", "tabletop_follow"}:
        return raw
    return str(getattr(args, "default_target_mode", "person_follow"))


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
    target_mode = str(state.last_selected_target.get("target_mode") or "person_follow")
    hold_limit = args.tabletop_hold_missing_frames if target_mode == "tabletop_follow" else args.hold_missing_frames
    if state.missing_frame_count > hold_limit:
        return None

    held = dict(state.last_selected_target)
    confidence_decay = 0.90 if target_mode == "tabletop_follow" else 0.84
    held["confidence"] = round(max(0.35, float(held.get("confidence") or 0.0) * confidence_decay), 4)
    held["lock_state"] = "held"
    hold_label = "tabletop occlusion hold" if target_mode == "tabletop_follow" else "short occlusion hold"
    held["reason"] = f"{hold_label} ({state.missing_frame_count}/{hold_limit})"
    held["approach_state"] = "stable"
    held["score_margin_to_best"] = 0.0
    return held


def detect_tabletop_object_candidates(
    frame: np.ndarray,
    fg_mask: np.ndarray,
    *,
    args: argparse.Namespace,
    previous_size_norm: float | None,
) -> list[dict[str, Any]]:
    h, w = frame.shape[:2]
    roi_left = int(round(clamp(args.tabletop_roi_left, 0.0, 1.0) * w))
    roi_right = int(round(clamp(args.tabletop_roi_right, 0.0, 1.0) * w))
    roi_top = int(round(clamp(args.tabletop_roi_top, 0.0, 1.0) * h))
    roi_bottom = int(round(clamp(args.tabletop_roi_bottom, 0.0, 1.0) * h))
    roi_left = max(0, min(roi_left, w - 1))
    roi_right = max(roi_left + 1, min(roi_right, w))
    roi_top = max(0, min(roi_top, h - 1))
    roi_bottom = max(roi_top + 1, min(roi_bottom, h))

    roi = frame[roi_top:roi_bottom, roi_left:roi_right]
    fg_roi = fg_mask[roi_top:roi_bottom, roi_left:roi_right]
    if roi.size == 0 or fg_roi.size == 0:
        return []

    gray_roi = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
    edges = cv2.Canny(gray_roi, 60, 150)
    edges = cv2.dilate(edges, np.ones((3, 3), np.uint8), iterations=1)
    motion = cv2.threshold(fg_roi, 127, 255, cv2.THRESH_BINARY)[1]
    combined = cv2.bitwise_or(edges, motion)
    combined = cv2.morphologyEx(combined, cv2.MORPH_CLOSE, np.ones((5, 5), np.uint8))
    contours, _ = cv2.findContours(combined, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    candidates: list[dict[str, Any]] = []
    frame_area = float(w * h)
    for contour in contours:
        area = float(cv2.contourArea(contour))
        if area <= 0:
            continue
        x, y, bw, bh = cv2.boundingRect(contour)
        bbox_area = float(max(1, bw * bh))
        area_ratio = bbox_area / frame_area
        if area_ratio < args.tabletop_min_area_ratio or area_ratio > args.tabletop_max_area_ratio:
            continue
        aspect_ratio = bw / float(max(1, bh))
        if aspect_ratio < args.tabletop_min_aspect_ratio or aspect_ratio > args.tabletop_max_aspect_ratio:
            continue
        edge_ratio = float(cv2.countNonZero(edges[y : y + bh, x : x + bw])) / bbox_area
        motion_ratio = float(cv2.countNonZero(motion[y : y + bh, x : x + bw])) / bbox_area
        fill_ratio = area / bbox_area
        if edge_ratio < args.tabletop_min_edge_ratio:
            continue
        if fill_ratio < 0.18:
            continue

        edge_score = min(edge_ratio / max(args.tabletop_min_edge_ratio * 2.2, 1e-6), 1.0)
        motion_score = min(motion_ratio / max(args.tabletop_min_motion_ratio * 3.0, 1e-6), 1.0)
        size_score = min(area_ratio / max(args.tabletop_min_area_ratio * 6.0, 1e-6), 1.0)
        confidence = round(min(0.97, 0.34 + (edge_score * 0.28) + (motion_score * 0.16) + (size_score * 0.14) + (fill_ratio * 0.16)), 4)
        if motion_ratio < args.tabletop_min_motion_ratio and confidence < 0.62:
            continue

        bbox = (x + roi_left, y + roi_top, bw, bh)
        entry = make_track_entry(
            track_id=0,
            bbox=bbox,
            detector="tabletop_object",
            target_class="object",
            target_mode="tabletop_follow",
            confidence=confidence,
            frame_width=w,
            frame_height=h,
            previous_size_norm=previous_size_norm,
        )
        entry["roi_mode"] = "tabletop"
        object_lock_strength = 0.0
        object_lock_strength += float(entry["selection_score"])
        object_lock_strength += min(edge_ratio * 0.9, 0.18)
        object_lock_strength += min(motion_ratio * 0.6, 0.10)
        object_lock_strength += min(fill_ratio * 0.18, 0.08)
        entry["selection_score"] = round(object_lock_strength + 0.12, 4)
        entry["edge_ratio"] = round(edge_ratio, 4)
        entry["motion_ratio"] = round(motion_ratio, 4)
        entry["aspect_ratio"] = round(aspect_ratio, 4)
        entry["fill_ratio"] = round(fill_ratio, 4)
        entry["object_lock_strength"] = round(object_lock_strength, 4)
        candidates.append(entry)

    return candidates


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


def detect_faces(gray: np.ndarray, cascade: cv2.CascadeClassifier) -> list[tuple[int, int, int, int]]:
    faces = cascade.detectMultiScale(
        gray,
        scaleFactor=1.1,
        minNeighbors=5,
        minSize=(40, 40),
    )
    return [tuple(int(value) for value in box) for box in faces]


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
    target_mode: str = "person_follow",
    target_count: int = 0,
    tracks: list[dict[str, Any]] | None = None,
    selected_target: dict[str, Any] | None = None,
    multi_target_payload: dict[str, Any] | None = None,
    interaction_hint: dict[str, Any] | None = None,
    owner_observation: dict[str, Any] | None = None,
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
        scene_name, scene_reason = infer_scene_hint(
            target_present,
            distance_band,
            approach_state,
            horizontal_zone,
            target_mode=target_mode,
            target_class=target_class,
        )

    frame_age_ms = max(0.0, (time.time() - path.stat().st_mtime) * 1000.0)
    event = {
        "schema_version": SCHEMA_VERSION,
        "event_type": event_type,
        "timestamp": now_iso(),
        "source": {
            "pipeline": "saved_jpeg_watch",
            "camera_mode": "single_camera_2d",
            "distance_mode": "monocular_heuristic",
            "target_mode": target_mode,
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
            "target_mode": target_mode,
            "detector": detector,
            "confidence": round(confidence if target_present else 0.0, 4),
            "bbox_norm": bbox_norm,
            "center_norm": None if center_x is None or center_y is None else {"x": round(center_x, 4), "y": round(center_y, 4)},
            "horizontal_zone": horizontal_zone if target_present else "unknown",
            "vertical_zone": vertical_zone if target_present else "unknown",
            "size_norm": None if size_norm is None else round(size_norm, 6),
            "distance_band": distance_band,
            "approach_state": approach_state,
            "owner_face_found": False,
            "owner_id": None,
            "owner_confidence": None,
            "owner_direction": "unknown",
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
    owner_source = None
    if selected_target is not None and bool(selected_target.get("owner_face_found")):
        owner_source = selected_target
    elif owner_observation is not None:
        owner_source = owner_observation
    if owner_source is not None:
        event["tracking"]["owner_face_found"] = True
        event["tracking"]["owner_id"] = owner_source.get("owner_id")
        event["tracking"]["owner_confidence"] = owner_source.get("owner_confidence")
        event["tracking"]["owner_direction"] = owner_source.get("owner_direction") or owner_source.get("horizontal_zone") or "unknown"
    if selected_target is not None:
        event["tracking"]["selected_lock_state"] = selected_target.get("lock_state")
        event["tracking"]["selected_reason"] = selected_target.get("reason")
        event["tracking"]["roi_mode"] = selected_target.get("roi_mode")
        event["tracking"]["object_lock_strength"] = selected_target.get("object_lock_strength")
        event["selected_target"] = {
            "track_id": selected_target.get("track_id"),
            "lock_state": selected_target.get("lock_state"),
            "reason": selected_target.get("reason"),
            "target_class": selected_target.get("target_class"),
            "target_mode": selected_target.get("target_mode"),
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
            "score_margin_to_best": selected_target.get("score_margin_to_best"),
            "continuity_distance_norm": selected_target.get("continuity_distance_norm"),
            "continuity_size_delta": selected_target.get("continuity_size_delta"),
            "continuity_aspect_delta": selected_target.get("continuity_aspect_delta"),
            "continuity_edge_delta": selected_target.get("continuity_edge_delta"),
            "continuity_motion_delta": selected_target.get("continuity_motion_delta"),
            "roi_mode": selected_target.get("roi_mode"),
            "edge_ratio": selected_target.get("edge_ratio"),
            "motion_ratio": selected_target.get("motion_ratio"),
            "aspect_ratio": selected_target.get("aspect_ratio"),
            "fill_ratio": selected_target.get("fill_ratio"),
            "object_lock_strength": selected_target.get("object_lock_strength"),
        }
        if "owner_face_found" in selected_target:
            event["selected_target"]["owner_face_found"] = bool(selected_target.get("owner_face_found"))
            event["selected_target"]["owner_id"] = selected_target.get("owner_id")
            event["selected_target"]["owner_confidence"] = selected_target.get("owner_confidence")
            event["selected_target"]["owner_direction"] = selected_target.get("owner_direction")
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
    cascade: cv2.CascadeClassifier,
    hog: Any,
    owner_registry: dict[str, Any] | None,
    args: argparse.Namespace,
) -> dict[str, Any]:
    frame = load_image(path)
    if frame is None:
        raise RuntimeError(f"Failed to decode JPEG frame: {path}")

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    operator_state = load_operator_state(args.operator_state_file)
    target_mode = resolve_target_mode(operator_state, args)
    fg_mask = compute_foreground_mask(frame, subtractor)
    state.bg_warmup_count += 1

    candidates: list[dict[str, Any]] = []
    owner_observation = None
    if target_mode == "tabletop_follow":
        candidates = detect_tabletop_object_candidates(
            frame,
            fg_mask,
            args=args,
            previous_size_norm=state.last_size_norm,
        )
    else:
        person_detections = detect_people(frame, hog, min_confidence=args.hog_min_confidence) if args.enable_hog_person else []
        faces = detect_faces(gray, cascade)
        owner_matches = match_owner_faces(
            frame,
            faces,
            owner_registry,
            threshold=float(getattr(args, "owner_match_threshold", 0.82)),
        )
        owner_observation = select_best_owner_observation(owner_matches)
        owner_matches_by_bbox = {
            tuple(int(value) for value in item["bbox"]): item
            for item in owner_matches
        }
        if person_detections:
            for bbox, weight in person_detections:
                candidates.append(
                    make_track_entry(
                        track_id=0,
                        bbox=bbox,
                        detector="hog_person",
                        target_class="person",
                        target_mode="person_follow",
                        confidence=weight,
                        frame_width=frame.shape[1],
                        frame_height=frame.shape[0],
                        previous_size_norm=state.last_size_norm,
                    )
                )

            # Face detections are used as confidence hints when they land inside a person box.
            for face_bbox in faces:
                fx, fy, fw, fh = face_bbox
                face_cx = fx + (fw / 2.0)
                face_cy = fy + (fh / 2.0)
                owner_match = owner_matches_by_bbox.get(tuple(int(value) for value in face_bbox))
                for item in candidates:
                    bx = item["bbox_norm"]["x"] * frame.shape[1]
                    by = item["bbox_norm"]["y"] * frame.shape[0]
                    bw = item["bbox_norm"]["w"] * frame.shape[1]
                    bh = item["bbox_norm"]["h"] * frame.shape[0]
                    if bx <= face_cx <= bx + bw and by <= face_cy <= by + bh:
                        item["confidence"] = round(min(0.98, float(item["confidence"]) + 0.08), 4)
                        item["selection_score"] = round(float(item["selection_score"]) + 0.12, 4)
                        if owner_match is not None:
                            apply_owner_match_to_track(
                                item,
                                owner_match,
                                selection_bonus=float(getattr(args, "owner_selection_bonus", 0.24)),
                            )
                        break
        elif faces:
            confidence = 0.92 if len(faces) >= 2 else 0.90
            for bbox in faces:
                entry = make_track_entry(
                    track_id=0,
                    bbox=bbox,
                    detector="haar_face",
                    target_class="person",
                    target_mode="person_follow",
                    confidence=confidence,
                    frame_width=frame.shape[1],
                    frame_height=frame.shape[0],
                    previous_size_norm=state.last_size_norm,
                )
                owner_match = owner_matches_by_bbox.get(tuple(int(value) for value in bbox))
                if owner_match is not None:
                    apply_owner_match_to_track(
                        entry,
                        owner_match,
                        selection_bonus=float(getattr(args, "owner_selection_bonus", 0.24)),
                    )
                candidates.append(entry)
        elif args.enable_hog_person:
            people = detect_people(frame, hog, min_confidence=args.hog_min_confidence)
            for bbox, confidence in people:
                candidates.append(
                    make_track_entry(
                        track_id=0,
                        bbox=bbox,
                        detector="hog_person",
                        target_class="person",
                        target_mode="person_follow",
                        confidence=confidence,
                        frame_width=frame.shape[1],
                        frame_height=frame.shape[0],
                        previous_size_norm=state.last_size_norm,
                    )
                )
        else:
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
                        target_mode="person_follow",
                        confidence=0.55,
                        frame_width=frame.shape[1],
                        frame_height=frame.shape[0],
                        previous_size_norm=state.last_size_norm,
                    )
                )

        if not candidates and args.enable_hog_person:
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
                        target_mode="person_follow",
                        confidence=0.55,
                        frame_width=frame.shape[1],
                        frame_height=frame.shape[0],
                        previous_size_norm=state.last_size_norm,
                    )
                )

    candidates = [item for item in candidates if within_engagement_zone(item, args)]
    owner_candidate_observations = [
        {
            "owner_id": item.get("owner_id"),
            "owner_confidence": item.get("owner_confidence"),
            "owner_direction": item.get("owner_direction") or item.get("horizontal_zone"),
            "horizontal_zone": item.get("horizontal_zone"),
        }
        for item in candidates
        if bool(item.get("owner_face_found"))
    ]
    owner_observation = select_best_owner_observation(owner_candidate_observations)

    tracks = assign_track_ids(candidates, state)
    selected_target = choose_selected_target(tracks, state, args=args, operator_state=operator_state)
    bbox = None
    detector = "none"
    target_class = "none"
    active_target_mode = target_mode
    confidence = 0.0
    target_count = len(tracks)
    multi_target_payload = None

    if selected_target is not None:
        state.missing_frame_count = 0
        state.last_selected_target = dict(selected_target)
        detector = str(selected_target["detector"])
        target_class = str(selected_target["target_class"])
        active_target_mode = str(selected_target.get("target_mode") or target_mode)
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
            active_target_mode = str(selected_target.get("target_mode") or target_mode)
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
        target_mode=active_target_mode,
        target_count=target_count,
        tracks=tracks,
        selected_target=selected_target,
        multi_target_payload=multi_target_payload,
        interaction_hint=interaction_hint,
        owner_observation=owner_observation,
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
    owner_registry_path = args.owner_face_registry.expanduser().resolve() if args.owner_face_registry else None

    cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
    if cascade.empty():
        raise SystemExit("OpenCV haarcascade_frontalface_default.xml is unavailable.")

    hog = None
    if args.enable_hog_person:
        hog = cv2.HOGDescriptor()
        hog.setSVMDetector(cv2.HOGDescriptor_getDefaultPeopleDetector())

    owner_registry = load_face_registry(owner_registry_path)
    subtractor = cv2.createBackgroundSubtractorMOG2(history=100, varThreshold=32, detectShadows=False)
    state = ExtractorState()

    LOGGER.info("Watching %s for JPEG frames", captures_dir)
    if latest_event_out:
        LOGGER.info("Latest event output: %s", latest_event_out)
    if events_jsonl:
        LOGGER.info("JSONL event log: %s", events_jsonl)
    if owner_registry is not None:
        LOGGER.info(
            "Owner-face registry loaded: %s (owner=%s samples=%s)",
            owner_registry_path,
            owner_registry.get("owner_id"),
            owner_registry.get("sample_count"),
        )

    while True:
        latest = find_latest_jpg(captures_dir)
        if latest is not None and latest != state.last_frame_path:
            event = process_frame(latest, state, subtractor, cascade, hog, owner_registry, args)
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
