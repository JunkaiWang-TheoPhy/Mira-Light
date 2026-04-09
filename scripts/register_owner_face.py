#!/usr/bin/env python3
"""Register an owner face for the minimal Mira Light identity pipeline."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Iterable

from face_identity import (
    build_face_registry,
    crop_bbox_with_padding,
    detect_largest_face,
    ensure_dependencies,
    extract_face_embedding,
    save_face_registry,
)

import cv2  # type: ignore


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Register owner-face images for Mira Light.")
    parser.add_argument(
        "inputs",
        nargs="+",
        help="Image files or directories containing owner reference photos.",
    )
    parser.add_argument(
        "--owner-id",
        default="owner_main",
        help="Logical owner identifier written into the registry.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("./runtime/face_registry/owner_main.json"),
        help="Registry JSON output path.",
    )
    parser.add_argument(
        "--min-face-width",
        type=int,
        default=28,
        help="Skip detections smaller than this width in pixels.",
    )
    return parser.parse_args()


def iter_image_paths(inputs: Iterable[str]) -> list[Path]:
    paths: list[Path] = []
    for raw in inputs:
        path = Path(raw).expanduser().resolve()
        if path.is_dir():
            for pattern in ("*.jpg", "*.jpeg", "*.png", "*.webp"):
                paths.extend(sorted(path.rglob(pattern)))
        elif path.is_file():
            paths.append(path)
    deduped: list[Path] = []
    seen: set[str] = set()
    for path in paths:
        key = str(path)
        if key not in seen:
            deduped.append(path)
            seen.add(key)
    return deduped


def main() -> int:
    args = parse_args()
    ensure_dependencies()

    image_paths = iter_image_paths(args.inputs)
    if not image_paths:
        raise SystemExit("No image files found for owner registration.")

    cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
    if cascade.empty():
        raise SystemExit("OpenCV haarcascade_frontalface_default.xml is unavailable.")

    embeddings = []
    sample_paths: list[str] = []
    skipped = 0

    for image_path in image_paths:
        image = cv2.imread(str(image_path))
        if image is None:
            print(f"[skip] failed to read image: {image_path}")
            skipped += 1
            continue
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        face_bbox = detect_largest_face(gray, cascade)
        if face_bbox is None or face_bbox[2] < args.min_face_width:
            print(f"[skip] no usable face found: {image_path}")
            skipped += 1
            continue
        face_crop = crop_bbox_with_padding(image, face_bbox)
        embedding = extract_face_embedding(face_crop) if face_crop is not None else None
        if embedding is None:
            print(f"[skip] failed to build embedding: {image_path}")
            skipped += 1
            continue
        embeddings.append(embedding)
        sample_paths.append(str(image_path))
        print(f"[ok] registered face from {image_path}")

    if not embeddings:
        raise SystemExit("No valid owner-face samples were registered.")

    registry = build_face_registry(str(args.owner_id), embeddings, sample_paths=sample_paths)
    output_path = save_face_registry(args.output.expanduser().resolve(), registry)
    print(
        f"[done] owner={args.owner_id} samples={len(sample_paths)} skipped={skipped} registry={output_path}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

