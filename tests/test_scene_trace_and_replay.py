from __future__ import annotations

import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace

import sys


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = ROOT / "scripts"

if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from scene_trace_recorder import record_scene_trace
from vision_replay_bench import cv2, run_replay_bench


class SceneTraceAndReplayTest(unittest.TestCase):
    def test_scene_trace_recorder_writes_json_and_html(self) -> None:
        with TemporaryDirectory() as tmpdir:
            out_dir = Path(tmpdir) / "trace"
            result = record_scene_trace(
                scene_name="farewell",
                out_dir=out_dir,
                base_url="http://127.0.0.1:9799",
                timeout_seconds=1.0,
                dry_run=True,
                skip_delays=True,
            )
            json_path = Path(result["jsonPath"])
            html_path = Path(result["htmlPath"])
            self.assertTrue(json_path.exists())
            self.assertTrue(html_path.exists())

            payload = json.loads(json_path.read_text(encoding="utf-8"))
            self.assertEqual(payload["scene"]["name"], "farewell")
            self.assertGreater(payload["summary"]["requestCount"], 0)
            self.assertTrue(any(item["kind"] == "request" for item in payload["timeline"]))

    @unittest.skipIf(cv2 is None, "OpenCV is not installed in the current environment")
    def test_vision_replay_bench_generates_decisions_and_state(self) -> None:
        with TemporaryDirectory() as tmpdir:
            tmp_root = Path(tmpdir)
            args = SimpleNamespace(
                captures_dir=tmp_root / "captures",
                out_dir=tmp_root / "out",
                base_url="http://127.0.0.1:9799",
                dry_run=True,
                allow_experimental=True,
                frame_spacing_ms=2400,
                scene_cooldown_ms=800,
                wake_up_cooldown_ms=1400,
                sleep_grace_ms=1800,
                warmup_frames=1,
                generate_synthetic_demo=True,
            )
            report = run_replay_bench(args)
            self.assertEqual(report["summary"]["processedFrames"], 8)
            self.assertIn("target_seen", report["summary"]["eventCounts"])
            self.assertIn("sleep", report["summary"]["sceneCounts"])
            self.assertTrue(Path(report["summary"]["bridgeStatePath"]).exists())
            self.assertTrue(Path(report["summary"]["eventsJsonlPath"]).exists())


if __name__ == "__main__":
    unittest.main()
