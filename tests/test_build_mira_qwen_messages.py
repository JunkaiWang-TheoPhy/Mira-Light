from __future__ import annotations

import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

import sys


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = ROOT / "scripts"

if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from build_mira_qwen_messages import build_payload


class BuildMiraQwenMessagesTest(unittest.TestCase):
    def test_build_payload_includes_identity_and_user_request(self) -> None:
        with TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir)
            for name in ("IDENTITY.md", "SOUL.md", "MEMORY.md", "AGENTS.md", "USER.md"):
                (workspace / name).write_text(f"{name}\n", encoding="utf-8")

            state_path = workspace / "state.json"
            state_path.write_text(json.dumps({"scene": "wake_up", "mood": "curious"}), encoding="utf-8")

            memory_path = workspace / "memory-snippet.txt"
            memory_path.write_text("Mira prefers scene-first responses.", encoding="utf-8")

            class Args:
                workspace_root = workspace
                user_message = "请介绍你自己。"
                model = "qwen2.5-3b"
                state_json = state_path
                memory_snippet = [str(memory_path)]
                history_json = None

            payload = build_payload(Args)

            self.assertEqual(payload["model"], "qwen2.5-3b")
            self.assertEqual(payload["messages"][0]["role"], "system")
            self.assertIn("你是 Mira", payload["messages"][0]["content"])
            self.assertIn("当前运行时状态", payload["messages"][1]["content"])
            self.assertIn("scene-first", payload["messages"][1]["content"])
            self.assertIn("当前用户请求", payload["messages"][1]["content"])
            self.assertIn("请介绍你自己", payload["messages"][1]["content"])


if __name__ == "__main__":
    unittest.main()
