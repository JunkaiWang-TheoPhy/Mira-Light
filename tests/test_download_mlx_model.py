from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import socket
from tempfile import TemporaryDirectory
import threading
from types import SimpleNamespace
import unittest
from unittest import mock
from urllib import parse

import sys


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = ROOT / "scripts"

if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from download_mlx_model import (
    DEFAULT_DISK_HEADROOM_BYTES,
    SnapshotInfo,
    build_file_url,
    collect_remote_file_info,
    download_file,
    ensure_disk_headroom,
    fetch_snapshot_info,
    part_path_for,
    verify_local_snapshot,
)


REPO_ID = "test-org/test-model"
REVISION = "test-sha"
MODEL_BYTES = (b"mira-light-qwen-" * 256)[:3072]
CONFIG_BYTES = json.dumps({"architectures": ["Qwen2ForCausalLM"]}).encode("utf-8")


class FakeSnapshotHandler(BaseHTTPRequestHandler):
    files = {
        "model.safetensors": MODEL_BYTES,
        "config.json": CONFIG_BYTES,
    }
    drop_first_model_request = False
    drop_after_bytes = 768
    range_requests: list[str | None] = []
    model_requests = 0

    def log_message(self, format: str, *args) -> None:  # noqa: A003
        del format, args

    @classmethod
    def reset(cls) -> None:
        cls.range_requests = []
        cls.model_requests = 0
        cls.drop_first_model_request = False

    def do_HEAD(self) -> None:
        self._handle_request(send_body=False)

    def do_GET(self) -> None:
        self._handle_request(send_body=True)

    def _handle_request(self, *, send_body: bool) -> None:
        parsed = parse.urlparse(self.path)
        if parsed.path in {
            f"/api/models/{REPO_ID}",
            f"/api/models/{parse.quote(REPO_ID, safe='')}",
        }:
            self._write_json(
                {
                    "id": REPO_ID,
                    "sha": REVISION,
                    "usedStorage": len(MODEL_BYTES) + len(CONFIG_BYTES),
                    "siblings": [
                        {"rfilename": ".gitattributes"},
                        {"rfilename": "config.json"},
                        {"rfilename": "model.safetensors"},
                    ],
                },
                send_body=send_body,
            )
            return

        file_prefix = f"/{REPO_ID}/resolve/{REVISION}/"
        if parsed.path.startswith(file_prefix):
            filename = parse.unquote(parsed.path[len(file_prefix) :])
            payload = self.files.get(filename)
            if payload is None:
                self.send_error(404)
                return
            self._write_file(filename, payload, send_body=send_body)
            return

        self.send_error(404)

    def _write_json(self, payload: dict, *, send_body: bool) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        if send_body:
            self.wfile.write(body)

    def _write_file(self, filename: str, payload: bytes, *, send_body: bool) -> None:
        range_header = self.headers.get("Range")
        if send_body:
            self.__class__.range_requests.append(range_header)
        start = 0
        if range_header:
            prefix = "bytes="
            if not range_header.startswith(prefix) or not range_header.endswith("-"):
                self.send_error(400)
                return
            start = int(range_header[len(prefix) : -1])
            if start >= len(payload):
                self.send_response(416)
                self.send_header("Content-Range", f"bytes */{len(payload)}")
                self.end_headers()
                return
            body = payload[start:]
            self.send_response(206)
            self.send_header("Content-Range", f"bytes {start}-{len(payload) - 1}/{len(payload)}")
        else:
            body = payload
            self.send_response(200)

        self.send_header("Content-Type", "application/octet-stream")
        self.send_header("Accept-Ranges", "bytes")
        self.send_header("ETag", f'"{filename}-etag"')
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()

        if not send_body:
            return

        if filename == "model.safetensors":
            self.__class__.model_requests += 1
            if self.__class__.drop_first_model_request and self.__class__.model_requests == 1 and start == 0:
                partial = body[: self.__class__.drop_after_bytes]
                self.wfile.write(partial)
                self.wfile.flush()
                try:
                    self.connection.shutdown(socket.SHUT_RDWR)
                except OSError:
                    pass
                self.connection.close()
                return

        self.wfile.write(body)


class DownloadMLXModelTest(unittest.TestCase):
    def setUp(self) -> None:
        FakeSnapshotHandler.reset()
        self.server = ThreadingHTTPServer(("127.0.0.1", 0), FakeSnapshotHandler)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.base_url = f"http://127.0.0.1:{self.server.server_address[1]}"

    def tearDown(self) -> None:
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=3)

    def test_download_file_resumes_from_existing_part_file(self) -> None:
        with TemporaryDirectory() as tmpdir:
            destination = Path(tmpdir) / "model.safetensors"
            partial = part_path_for(destination)
            partial.write_bytes(MODEL_BYTES[:1024])

            result = download_file(
                url=build_file_url(REPO_ID, "model.safetensors", base_url=self.base_url, revision=REVISION),
                destination=destination,
                timeout_seconds=2.0,
                chunk_size=128,
                max_retries=0,
                expected_size=len(MODEL_BYTES),
            )

            self.assertEqual(result["status"], "downloaded")
            self.assertEqual(destination.read_bytes(), MODEL_BYTES)
            self.assertFalse(partial.exists())
            self.assertIn("bytes=1024-", FakeSnapshotHandler.range_requests)

    def test_download_file_retries_and_resumes_after_interrupted_transfer(self) -> None:
        with TemporaryDirectory() as tmpdir:
            FakeSnapshotHandler.drop_first_model_request = True
            destination = Path(tmpdir) / "model.safetensors"

            result = download_file(
                url=build_file_url(REPO_ID, "model.safetensors", base_url=self.base_url, revision=REVISION),
                destination=destination,
                timeout_seconds=2.0,
                chunk_size=128,
                max_retries=2,
                expected_size=len(MODEL_BYTES),
            )

            self.assertEqual(result["status"], "downloaded")
            self.assertEqual(destination.read_bytes(), MODEL_BYTES)
            self.assertGreaterEqual(FakeSnapshotHandler.model_requests, 2)
            self.assertIn(f"bytes={FakeSnapshotHandler.drop_after_bytes}-", FakeSnapshotHandler.range_requests)

    def test_download_file_replaces_existing_size_mismatch(self) -> None:
        with TemporaryDirectory() as tmpdir:
            destination = Path(tmpdir) / "model.safetensors"
            destination.write_bytes(MODEL_BYTES[:128])

            result = download_file(
                url=build_file_url(REPO_ID, "model.safetensors", base_url=self.base_url, revision=REVISION),
                destination=destination,
                timeout_seconds=2.0,
                chunk_size=128,
                max_retries=0,
                expected_size=len(MODEL_BYTES),
            )

            self.assertEqual(result["status"], "downloaded")
            self.assertEqual(destination.read_bytes(), MODEL_BYTES)

    def test_verify_local_snapshot_reports_partial_files(self) -> None:
        snapshot = fetch_snapshot_info(
            REPO_ID,
            api_base_url=f"{self.base_url}/api/models",
            timeout_seconds=2.0,
        )
        remote_files = collect_remote_file_info(
            snapshot,
            timeout_seconds=2.0,
            base_url=self.base_url,
        )

        with TemporaryDirectory() as tmpdir:
            tmp_root = Path(tmpdir)
            (tmp_root / "config.json").write_bytes(CONFIG_BYTES)
            part_path_for(tmp_root / "model.safetensors").write_bytes(MODEL_BYTES[:256])

            issues = verify_local_snapshot(
                tmp_root,
                snapshot,
                base_url=self.base_url,
                timeout_seconds=2.0,
                remote_info_by_file=remote_files,
            )

            self.assertEqual(len(issues), 1)
            self.assertIn("partial download still present", issues[0])

    def test_ensure_disk_headroom_accounts_for_existing_bytes(self) -> None:
        snapshot = SnapshotInfo(
            repo_id=REPO_ID,
            revision=REVISION,
            used_storage=10 * 1024,
            files=("model.safetensors", "config.json"),
        )
        with TemporaryDirectory() as tmpdir:
            tmp_root = Path(tmpdir)
            (tmp_root / "model.safetensors").write_bytes(b"x" * 4096)

            with mock.patch("download_mlx_model.shutil.disk_usage", return_value=SimpleNamespace(free=9000)):
                with self.assertRaisesRegex(RuntimeError, "Not enough free disk space"):
                    ensure_disk_headroom(tmp_root, snapshot)

            with mock.patch(
                "download_mlx_model.shutil.disk_usage",
                return_value=SimpleNamespace(free=10 * 1024 - 4096 + DEFAULT_DISK_HEADROOM_BYTES + 1),
            ):
                ensure_disk_headroom(tmp_root, snapshot)


if __name__ == "__main__":
    unittest.main()
