from __future__ import annotations

import unittest

import sys
from pathlib import Path
from tempfile import TemporaryDirectory

import cv2
import numpy as np


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = ROOT / "scripts"

if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from face_identity import (
    build_face_registry,
    cosine_similarity,
    extract_face_embedding,
    load_face_registry,
    match_face_embedding,
    save_face_registry,
)


def make_face_like_image(*, eye_shift: int = 0, mouth_raise: int = 0) -> np.ndarray:
    image = np.zeros((96, 96, 3), dtype=np.uint8)
    cv2.circle(image, (48, 48), 32, (220, 220, 220), thickness=-1)
    cv2.circle(image, (38 + eye_shift, 40), 5, (30, 30, 30), thickness=-1)
    cv2.circle(image, (58 + eye_shift, 40), 5, (30, 30, 30), thickness=-1)
    cv2.ellipse(image, (48, 60 - mouth_raise), (14, 8), 0, 10, 170, (40, 40, 40), thickness=3)
    return image


class FaceIdentityTest(unittest.TestCase):
    def test_embedding_similarity_prefers_same_face_variant(self) -> None:
        owner_a = extract_face_embedding(make_face_like_image())
        owner_b = extract_face_embedding(make_face_like_image(eye_shift=1, mouth_raise=1))
        stranger = extract_face_embedding(make_face_like_image(eye_shift=8, mouth_raise=-8))

        self.assertIsNotNone(owner_a)
        self.assertIsNotNone(owner_b)
        self.assertIsNotNone(stranger)

        same_score = cosine_similarity(owner_a, owner_b)
        different_score = cosine_similarity(owner_a, stranger)

        self.assertGreater(same_score, different_score)

    def test_registry_roundtrip_and_match(self) -> None:
        owner_embeddings = [
            extract_face_embedding(make_face_like_image()),
            extract_face_embedding(make_face_like_image(eye_shift=1)),
        ]
        owner_embeddings = [item for item in owner_embeddings if item is not None]
        registry = build_face_registry("owner_main", owner_embeddings, sample_paths=["a.jpg", "b.jpg"])

        with TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "owner.json"
            save_face_registry(path, registry)
            loaded = load_face_registry(path)

            self.assertEqual(loaded["owner_id"], "owner_main")
            self.assertEqual(loaded["sample_count"], 2)

            owner_probe = extract_face_embedding(make_face_like_image(eye_shift=1, mouth_raise=1))
            stranger_probe = extract_face_embedding(make_face_like_image(eye_shift=10, mouth_raise=-10))
            owner_score = cosine_similarity(owner_probe, loaded["embedding_mean"])
            stranger_score = cosine_similarity(stranger_probe, loaded["embedding_mean"])
            threshold = (owner_score + stranger_score) / 2.0
            owner_match = match_face_embedding(owner_probe, loaded, threshold=threshold)
            stranger_match = match_face_embedding(stranger_probe, loaded, threshold=threshold)

            self.assertTrue(owner_match["matched"])
            self.assertEqual(owner_match["owner_id"], "owner_main")
            self.assertFalse(stranger_match["matched"])


if __name__ == "__main__":
    unittest.main()
