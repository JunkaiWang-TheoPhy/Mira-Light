from __future__ import annotations

import unittest

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = ROOT / "scripts"

if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from download_llama_cpp_model import build_target_snapshot, resolve_entry_filename, select_model_filenames
from download_mlx_model import SnapshotInfo
from smoke_test_llama_cpp import resolve_default_model_files


class DownloadLlamaCppModelTest(unittest.TestCase):
    def test_select_model_filenames_for_3b_q4_k_m(self) -> None:
        snapshot = SnapshotInfo(
            repo_id="Qwen/Qwen2.5-3B-Instruct-GGUF",
            revision="test",
            used_storage=0,
            files=(
                "README.md",
                "LICENSE",
                "qwen2.5-3b-instruct-q4_k_m.gguf",
                "qwen2.5-3b-instruct-q5_k_m.gguf",
            ),
        )

        selected = select_model_filenames(snapshot, base_name="qwen2.5-3b-instruct", quant="q4_k_m")

        self.assertEqual(selected, ("qwen2.5-3b-instruct-q4_k_m.gguf",))

    def test_select_model_filenames_for_7b_split_quant(self) -> None:
        snapshot = SnapshotInfo(
            repo_id="Qwen/Qwen2.5-7B-Instruct-GGUF",
            revision="test",
            used_storage=0,
            files=(
                "qwen2.5-7b-instruct-q4_k_m-00002-of-00002.gguf",
                "qwen2.5-7b-instruct-q4_k_m-00001-of-00002.gguf",
                "qwen2.5-7b-instruct-q8_0-00001-of-00003.gguf",
            ),
        )

        selected = select_model_filenames(snapshot, base_name="qwen2.5-7b-instruct", quant="q4_k_m")

        self.assertEqual(
            selected,
            (
                "qwen2.5-7b-instruct-q4_k_m-00001-of-00002.gguf",
                "qwen2.5-7b-instruct-q4_k_m-00002-of-00002.gguf",
            ),
        )

    def test_build_target_snapshot_keeps_meta_files(self) -> None:
        snapshot = SnapshotInfo(
            repo_id="Qwen/Qwen2.5-3B-Instruct-GGUF",
            revision="test",
            used_storage=0,
            files=("README.md", "LICENSE", "qwen2.5-3b-instruct-q4_k_m.gguf"),
        )

        narrowed = build_target_snapshot(
            snapshot,
            selected_files=("qwen2.5-3b-instruct-q4_k_m.gguf",),
        )

        self.assertEqual(
            narrowed.files,
            ("LICENSE", "README.md", "qwen2.5-3b-instruct-q4_k_m.gguf"),
        )

    def test_resolve_entry_filename_uses_first_shard(self) -> None:
        self.assertEqual(
            resolve_entry_filename(resolve_default_model_files("qwen2.5-7b")),
            "qwen2.5-7b-instruct-q4_k_m-00001-of-00002.gguf",
        )


if __name__ == "__main__":
    unittest.main()
