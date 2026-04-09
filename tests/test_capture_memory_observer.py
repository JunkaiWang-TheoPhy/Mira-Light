from pathlib import Path
from tempfile import TemporaryDirectory
import json
import os
import time
import unittest

import cv2  # type: ignore
import numpy as np  # type: ignore

import sys


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from capture_memory_observer import (
    build_status_payload,
    capture_score_to_dict,
    choose_capture,
    CaptureScore,
    extract_first_json_object,
    prune_json_artifacts,
    should_write_episodic_memory,
    write_local_artifact,
    write_status,
)


class CaptureMemoryObserverTest(unittest.TestCase):
    def test_extract_first_json_object_accepts_wrapped_model_text(self) -> None:
        parsed = extract_first_json_object(
            "下面是结果：\n```json\n{\"peopleCount\": 1, \"sceneSummary\": \"访客站在灯前\"}\n```"
        )
        self.assertEqual(parsed["peopleCount"], 1)
        self.assertEqual(parsed["sceneSummary"], "访客站在灯前")

    def test_should_write_episodic_memory_skips_recent_duplicate_signature(self) -> None:
        summary = {
            "peopleCount": 1,
            "peopleSummary": "一位访客在观看台灯",
            "objects": ["台灯", "桌面"],
            "activity": "观察",
            "sceneSummary": "访客停留在 Mira Light 前方",
            "location": "Shenzhen, Guangdong, CN (IP: 1.2.3.4)",
        }
        from capture_memory_observer import build_observation_signature  # local import to keep test surface compact

        signature = build_observation_signature(summary)
        state = {
            "lastMemorySignature": signature,
            "lastMemorySignatureAt": time.time(),
        }

        should_write, reason = should_write_episodic_memory(
            summary=summary,
            state=state,
            dedup_minutes=30,
        )
        self.assertFalse(should_write)
        self.assertIn("duplicate signature", reason)

    def test_choose_capture_prefers_sharper_image(self) -> None:
        with TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            sharp_path = root / "sharp.jpg"
            blur_path = root / "blur.jpg"

            base = np.zeros((220, 220, 3), dtype=np.uint8)
            cv2.rectangle(base, (20, 20), (200, 200), (255, 255, 255), 4)
            cv2.line(base, (20, 20), (200, 200), (0, 200, 255), 3)
            cv2.putText(base, "Mira", (45, 118), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (255, 255, 255), 2, cv2.LINE_AA)

            blurred = cv2.GaussianBlur(base, (31, 31), 0)

            self.assertTrue(cv2.imwrite(str(sharp_path), base))
            self.assertTrue(cv2.imwrite(str(blur_path), blurred))

            chosen = choose_capture([blur_path, sharp_path], limit=5, min_dimension=64)
            self.assertIsNotNone(chosen)
            assert chosen is not None
            self.assertEqual(chosen.path.name, "sharp.jpg")

    def test_write_local_artifact_serializes_paths(self) -> None:
        with TemporaryDirectory() as tmpdir:
            artifact_path = Path(tmpdir) / "artifact.json"
            write_local_artifact(artifact_path, {"capturePath": Path("/tmp/demo.jpg")})
            text = artifact_path.read_text(encoding="utf-8")
            self.assertIn('"/tmp/demo.jpg"', text)

    def test_capture_score_to_dict_serializes_path(self) -> None:
        payload = capture_score_to_dict(
            CaptureScore(
                path=Path("/tmp/demo.jpg"),
                mtime=123.4,
                width=640,
                height=480,
                file_size=1024,
                sharpness=12.3,
                contrast=22.1,
                brightness=120.0,
                score=456.7,
            )
        )
        self.assertEqual(payload["path"], "/tmp/demo.jpg")

    def test_prune_json_artifacts_respects_max_items(self) -> None:
        with TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            for index in range(4):
                path = root / f"{index}.json"
                path.write_text(json.dumps({"index": index}), encoding="utf-8")
                os_time = time.time() + index
                path.touch()
                os.utime(path, (os_time, os_time))

            removed = prune_json_artifacts(root, max_items=2, max_age_days=7)
            kept = sorted(path.name for path in root.glob("*.json"))
            self.assertEqual(removed, 2)
            self.assertEqual(kept, ["2.json", "3.json"])

    def test_write_status_persists_summary_payload(self) -> None:
        with TemporaryDirectory() as tmpdir:
            status_path = Path(tmpdir) / "status.json"
            payload = build_status_payload(
                state="ok",
                message="Representative capture summarized successfully.",
                captures_dir=Path("/tmp/captures"),
                status_at="2026-04-09T18:40:00+08:00",
                latest_observation_path=Path("/tmp/latest.observation.json"),
                last_processed_path="/tmp/captures/demo.jpg",
                observation={
                    "capturePath": "/tmp/captures/demo.jpg",
                    "signature": "sig-123",
                    "memoryWriteSuggested": True,
                    "memoryWriteReason": "visible people present",
                    "summary": {"sceneSummary": "访客站在灯前"},
                },
            )
            write_status(status_path, payload)
            loaded = json.loads(status_path.read_text(encoding="utf-8"))
            self.assertEqual(loaded["state"], "ok")
            self.assertEqual(loaded["signature"], "sig-123")
            self.assertTrue(loaded["memoryWriteSuggested"])


if __name__ == "__main__":
    unittest.main()
