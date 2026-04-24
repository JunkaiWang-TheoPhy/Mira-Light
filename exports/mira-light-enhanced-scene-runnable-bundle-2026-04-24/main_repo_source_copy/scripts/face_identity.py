#!/usr/bin/env python3
"""Minimal owner-face registration and matching helpers for Mira Light.

This intentionally stays lightweight and dependency-free beyond OpenCV/Numpy.
It is not meant to replace a production face-recognition stack; the goal is to
support a booth-friendly local owner-registration workflow with the current
repo dependencies.
"""

from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any

try:
    import cv2  # type: ignore
    import numpy as np  # type: ignore
except ImportError:  # pragma: no cover - surfaced by callers at runtime
    cv2 = None  # type: ignore
    np = None  # type: ignore


FACE_REGISTRY_SCHEMA_VERSION = "1.0.0"
FACE_FEATURE_VERSION = "opencv_hog_v1"
_FACE_HOG_DESCRIPTOR = None


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def ensure_dependencies() -> None:
    if cv2 is None or np is None:
        raise RuntimeError("OpenCV/Numpy are required for face identity helpers.")


def get_face_hog_descriptor() -> Any:
    global _FACE_HOG_DESCRIPTOR
    ensure_dependencies()
    if _FACE_HOG_DESCRIPTOR is None:
        _FACE_HOG_DESCRIPTOR = cv2.HOGDescriptor(
            (64, 64),
            (16, 16),
            (8, 8),
            (8, 8),
            9,
        )
    return _FACE_HOG_DESCRIPTOR


def crop_bbox_with_padding(
    image: np.ndarray,
    bbox: tuple[int, int, int, int],
    *,
    pad_ratio: float = 0.18,
) -> np.ndarray | None:
    ensure_dependencies()
    if image is None or image.size == 0:
        return None
    x, y, w, h = bbox
    height, width = image.shape[:2]
    if width <= 0 or height <= 0 or w <= 0 or h <= 0:
        return None
    pad_x = int(round(w * pad_ratio))
    pad_y = int(round(h * pad_ratio))
    left = max(0, x - pad_x)
    top = max(0, y - pad_y)
    right = min(width, x + w + pad_x)
    bottom = min(height, y + h + pad_y)
    if right <= left or bottom <= top:
        return None
    return image[top:bottom, left:right].copy()


def detect_largest_face(gray_image: np.ndarray, cascade: Any) -> tuple[int, int, int, int] | None:
    ensure_dependencies()
    if gray_image is None or gray_image.size == 0:
        return None
    faces = cascade.detectMultiScale(
        gray_image,
        scaleFactor=1.1,
        minNeighbors=5,
        minSize=(28, 28),
    )
    if faces is None or len(faces) == 0:
        return None
    ordered = sorted((tuple(int(value) for value in box) for box in faces), key=lambda item: item[2] * item[3], reverse=True)
    return ordered[0]


def _normalize_face_image(face_image: np.ndarray) -> np.ndarray | None:
    ensure_dependencies()
    if face_image is None or face_image.size == 0:
        return None
    if face_image.ndim == 3:
        gray = cv2.cvtColor(face_image, cv2.COLOR_BGR2GRAY)
    elif face_image.ndim == 2:
        gray = face_image.copy()
    else:
        return None
    if gray.shape[0] < 18 or gray.shape[1] < 18:
        return None
    resized = cv2.resize(gray, (64, 64), interpolation=cv2.INTER_AREA)
    equalized = cv2.equalizeHist(resized)
    return cv2.GaussianBlur(equalized, (3, 3), 0)


def extract_face_embedding(face_image: np.ndarray) -> np.ndarray | None:
    ensure_dependencies()
    normalized = _normalize_face_image(face_image)
    if normalized is None:
        return None

    hog = get_face_hog_descriptor()
    hog_vector = hog.compute(normalized)
    if hog_vector is None:
        return None
    hog_vector = hog_vector.reshape(-1).astype(np.float32)

    pooled = cv2.resize(normalized, (16, 16), interpolation=cv2.INTER_AREA).reshape(-1).astype(np.float32) / 255.0
    grad_x = cv2.Sobel(normalized, cv2.CV_32F, 1, 0, ksize=3)
    grad_y = cv2.Sobel(normalized, cv2.CV_32F, 0, 1, ksize=3)
    gradient_stats = np.array(
        [
            float(np.mean(np.abs(grad_x))),
            float(np.mean(np.abs(grad_y))),
            float(np.std(grad_x)),
            float(np.std(grad_y)),
        ],
        dtype=np.float32,
    )

    feature = np.concatenate([hog_vector, pooled, gradient_stats]).astype(np.float32)
    norm = float(np.linalg.norm(feature))
    if norm <= 1e-8:
        return None
    return feature / norm


def cosine_similarity(vector_a: np.ndarray, vector_b: np.ndarray) -> float:
    ensure_dependencies()
    if vector_a is None or vector_b is None:
        return 0.0
    a = vector_a.astype(np.float32, copy=False)
    b = vector_b.astype(np.float32, copy=False)
    denom = float(np.linalg.norm(a) * np.linalg.norm(b))
    if denom <= 1e-8:
        return 0.0
    return float(np.dot(a, b) / denom)


def serialize_embedding(embedding: np.ndarray) -> list[float]:
    ensure_dependencies()
    return [round(float(value), 6) for value in embedding.tolist()]


def build_face_registry(
    owner_id: str,
    embeddings: list[np.ndarray],
    *,
    sample_paths: list[str],
) -> dict[str, Any]:
    ensure_dependencies()
    if not embeddings:
        raise RuntimeError("Cannot build a face registry without at least one embedding.")
    stacked = np.stack([item.astype(np.float32, copy=False) for item in embeddings], axis=0)
    mean_embedding = np.mean(stacked, axis=0).astype(np.float32)
    norm = float(np.linalg.norm(mean_embedding))
    if norm <= 1e-8:
        raise RuntimeError("Face embedding mean collapsed to zero.")
    mean_embedding /= norm
    return {
        "schema_version": FACE_REGISTRY_SCHEMA_VERSION,
        "feature_version": FACE_FEATURE_VERSION,
        "owner_id": owner_id,
        "created_at": now_iso(),
        "embedding_dim": int(mean_embedding.shape[0]),
        "sample_count": len(sample_paths),
        "sample_paths": sample_paths,
        "embedding_mean": serialize_embedding(mean_embedding),
    }


def save_face_registry(path: Path, registry: dict[str, Any]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(registry, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path


def load_face_registry(path: Path | None) -> dict[str, Any] | None:
    ensure_dependencies()
    if path is None or not path.is_file():
        return None
    parsed = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(parsed, dict):
        raise RuntimeError(f"Face registry must be a JSON object: {path}")
    raw_embedding = parsed.get("embedding_mean")
    if not isinstance(raw_embedding, list) or not raw_embedding:
        raise RuntimeError(f"Face registry is missing embedding_mean: {path}")
    embedding = np.array(raw_embedding, dtype=np.float32)
    norm = float(np.linalg.norm(embedding))
    if norm <= 1e-8:
        raise RuntimeError(f"Face registry embedding_mean is invalid: {path}")
    embedding /= norm
    return {
        "path": str(path),
        "schema_version": parsed.get("schema_version"),
        "feature_version": parsed.get("feature_version"),
        "owner_id": str(parsed.get("owner_id") or "owner_main"),
        "embedding_dim": int(parsed.get("embedding_dim") or embedding.shape[0]),
        "sample_count": int(parsed.get("sample_count") or 0),
        "sample_paths": parsed.get("sample_paths") or [],
        "embedding_mean": embedding,
    }


def match_face_embedding(
    embedding: np.ndarray | None,
    registry: dict[str, Any] | None,
    *,
    threshold: float,
) -> dict[str, Any]:
    ensure_dependencies()
    if embedding is None or registry is None:
        return {
            "matched": False,
            "owner_id": None,
            "confidence": 0.0,
            "threshold": threshold,
        }

    score = cosine_similarity(embedding, registry["embedding_mean"])
    matched = score >= threshold
    return {
        "matched": matched,
        "owner_id": registry.get("owner_id") if matched else None,
        "confidence": round(score, 4),
        "threshold": threshold,
    }

