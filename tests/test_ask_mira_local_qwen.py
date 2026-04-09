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

from ask_mira_local_qwen import build_request_payload, extract_assistant_text, server_models_url


class AskMiraLocalQwenTest(unittest.TestCase):
    def test_server_models_url_rewrites_chat_path(self) -> None:
        self.assertEqual(
            server_models_url("http://127.0.0.1:8012/v1/chat/completions"),
            "http://127.0.0.1:8012/v1/models",
        )

    def test_extract_assistant_text_returns_first_choice(self) -> None:
        payload = {
            "choices": [
                {
                    "message": {
                        "role": "assistant",
                        "content": "你好，我是 Mira。",
                    }
                }
            ]
        }
        self.assertEqual(extract_assistant_text(payload), "你好，我是 Mira。")

    def test_build_request_payload_uses_server_model(self) -> None:
        with TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir)
            for name in ("IDENTITY.md", "SOUL.md", "MEMORY.md", "AGENTS.md", "USER.md"):
                (workspace / name).write_text(f"{name}\n", encoding="utf-8")

            class Args:
                workspace_root = workspace
                message = "请介绍你是谁。"
                server_model = "qwen2.5-3b-instruct-q4_k_m.gguf"
                state_json = None
                memory_snippet = []
                history_json = None
                temperature = 0.2
                max_tokens = 64

            payload = build_request_payload(Args)
            self.assertEqual(payload["model"], "qwen2.5-3b-instruct-q4_k_m.gguf")
            self.assertEqual(payload["max_tokens"], 64)
            self.assertEqual(payload["temperature"], 0.2)
            self.assertEqual(payload["messages"][0]["role"], "system")
            self.assertIn("当前用户请求", payload["messages"][1]["content"])


if __name__ == "__main__":
    unittest.main()
