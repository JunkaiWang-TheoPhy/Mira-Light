#!/usr/bin/env python3
"""Minimal HTTP receiver for the ESP32 smart lamp.

The receiver supports:

- `GET /health`
- `POST /device/status`
- `POST /device/upload`
- `POST /device/upload-base64`

Design note:

- binary upload is the preferred/default file path
- base64 upload is a compatibility fallback for constrained senders

Default save root:
`~/Documents/Mira-Light-Runtime/simple-receiver/`
"""

from __future__ import annotations

import argparse
import base64
from datetime import datetime, timezone
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse


DEFAULT_HOST = "0.0.0.0"
DEFAULT_PORT = 9784
DEFAULT_SAVE_ROOT = Path.home() / "Documents" / "Mira-Light-Runtime" / "simple-receiver"
PREFERRED_UPLOAD_MODE = "binary"


class ReceiverServer(ThreadingHTTPServer):
    def __init__(self, server_address, handler_class, save_root: Path):
        super().__init__(server_address, handler_class)
        self.save_root = save_root
        self.snapshots_dir = save_root / "snapshots"
        self.events_dir = save_root / "events"
        self.uploads_dir = save_root / "uploads"

        self.save_root.mkdir(parents=True, exist_ok=True)
        self.snapshots_dir.mkdir(parents=True, exist_ok=True)
        self.events_dir.mkdir(parents=True, exist_ok=True)
        self.uploads_dir.mkdir(parents=True, exist_ok=True)


class ReceiverHandler(BaseHTTPRequestHandler):
    server: ReceiverServer

    def log_message(self, format: str, *args) -> None:  # noqa: A003
        print(f"[simple-receiver] {self.address_string()} - {format % args}")

    def _now(self) -> datetime:
        return datetime.now(timezone.utc).astimezone()

    def _send_json(self, status_code: int, payload: dict) -> None:
        body = json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _read_json(self) -> dict:
        length = int(self.headers.get("Content-Length", "0") or 0)
        if length <= 0:
            return {}
        raw = self.rfile.read(length).decode("utf-8")
        return json.loads(raw) if raw.strip() else {}

    def _read_bytes(self) -> bytes:
        length = int(self.headers.get("Content-Length", "0") or 0)
        if length <= 0:
            return b""
        return self.rfile.read(length)

    def _safe_name(self, value: str | None, fallback: str) -> str:
        raw = (value or fallback).strip()
        if not raw:
            raw = fallback
        return "".join(ch if ch.isalnum() or ch in ("-", "_", ".", "@") else "-" for ch in raw)

    def _append_event(self, payload: dict) -> Path:
        now = self._now()
        event_path = self.server.events_dir / f"{now.strftime('%Y-%m-%d')}.jsonl"
        with event_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(payload, ensure_ascii=False) + "\n")
        return event_path

    def do_GET(self) -> None:  # noqa: N802
        if self.path == "/health":
            self._send_json(
                200,
                {
                    "ok": True,
                    "service": "simple-lamp-receiver",
                    "preferredUploadMode": PREFERRED_UPLOAD_MODE,
                    "saveRoot": str(self.server.save_root),
                    "uploadsRoot": str(self.server.uploads_dir),
                    "time": self._now().isoformat(timespec="seconds"),
                },
            )
            return

        self._send_json(404, {"ok": False, "error": "Not found"})

    def do_POST(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        path = parsed.path

        if path == "/device/status":
            try:
                body = self._read_json()
            except Exception as exc:  # noqa: BLE001
                self._send_json(400, {"ok": False, "error": f"Invalid JSON: {exc}"})
                return

            now = self._now()
            device_id = str(body.get("deviceId") or "mira-light-001").strip() or "mira-light-001"

            snapshot_payload = {
                "receivedAt": now.isoformat(timespec="seconds"),
                "deviceId": device_id,
                "payload": body,
            }

            snapshot_path = self.server.snapshots_dir / f"{device_id}.latest.json"
            snapshot_path.write_text(json.dumps(snapshot_payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

            event_path = self._append_event(snapshot_payload)

            self._send_json(
                200,
                {
                    "ok": True,
                    "saved": True,
                    "deviceId": device_id,
                    "snapshotPath": str(snapshot_path),
                    "eventPath": str(event_path),
                },
            )
            return

        if path == "/device/upload":
            now = self._now()
            query = parse_qs(parsed.query)
            device_id = self._safe_name(
                self.headers.get("X-Device-Id") or query.get("deviceId", [None])[0],
                "mira-light-001",
            )
            file_name = self._safe_name(
                self.headers.get("X-File-Name") or query.get("fileName", [None])[0],
                "upload.bin",
            )
            category = self._safe_name(
                self.headers.get("X-File-Category") or query.get("category", [None])[0],
                "misc",
            )
            content_type = self.headers.get("Content-Type") or "application/octet-stream"

            payload = self._read_bytes()
            if not payload:
                self._send_json(400, {"ok": False, "error": "Empty upload body"})
                return

            target_dir = self.server.uploads_dir / now.strftime("%Y-%m-%d") / device_id / category
            target_dir.mkdir(parents=True, exist_ok=True)
            target_path = target_dir / file_name
            target_path.write_bytes(payload)

            meta = {
                "receivedAt": now.isoformat(timespec="seconds"),
                "deviceId": device_id,
                "category": category,
                "filename": file_name,
                "contentType": content_type,
                "size": len(payload),
                "path": str(target_path),
            }

            meta_path = target_path.with_suffix(target_path.suffix + ".meta.json")
            meta_path.write_text(json.dumps(meta, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            event_path = self._append_event({"type": "file_upload", **meta})

            self._send_json(
                200,
                {
                    "ok": True,
                    "saved": True,
                    "uploadMode": "binary",
                    "deviceId": device_id,
                    "path": str(target_path),
                    "metaPath": str(meta_path),
                    "eventPath": str(event_path),
                },
            )
            return

        if path == "/device/upload-base64":
            try:
                body = self._read_json()
            except Exception as exc:  # noqa: BLE001
                self._send_json(400, {"ok": False, "error": f"Invalid JSON: {exc}"})
                return

            device_id = self._safe_name(body.get("deviceId"), "mira-light-001")
            file_name = self._safe_name(body.get("fileName"), "upload.bin")
            category = self._safe_name(body.get("category"), "misc")
            content_type = str(body.get("contentType") or "application/octet-stream")
            content_base64 = body.get("contentBase64")

            if not isinstance(content_base64, str) or not content_base64.strip():
                self._send_json(400, {"ok": False, "error": "contentBase64 is required"})
                return

            try:
                payload = base64.b64decode(content_base64, validate=True)
            except Exception as exc:  # noqa: BLE001
                self._send_json(400, {"ok": False, "error": f"Invalid base64 payload: {exc}"})
                return

            now = self._now()
            target_dir = self.server.uploads_dir / now.strftime("%Y-%m-%d") / device_id / category
            target_dir.mkdir(parents=True, exist_ok=True)
            target_path = target_dir / file_name
            target_path.write_bytes(payload)

            meta = {
                "receivedAt": now.isoformat(timespec="seconds"),
                "deviceId": device_id,
                "category": category,
                "filename": file_name,
                "contentType": content_type,
                "size": len(payload),
                "path": str(target_path),
            }

            meta_path = target_path.with_suffix(target_path.suffix + ".meta.json")
            meta_path.write_text(json.dumps(meta, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            event_path = self._append_event({"type": "file_upload_base64", **meta})

            self._send_json(
                200,
                {
                    "ok": True,
                    "saved": True,
                    "uploadMode": "base64",
                    "deviceId": device_id,
                    "path": str(target_path),
                    "metaPath": str(meta_path),
                    "eventPath": str(event_path),
                },
            )
            return

        self._send_json(404, {"ok": False, "error": "Not found"})


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run the simplest Mira Light HTTP receiver.")
    parser.add_argument("--host", default=DEFAULT_HOST, help="Bind host")
    parser.add_argument("--port", default=DEFAULT_PORT, type=int, help="Bind port")
    parser.add_argument("--save-root", default=str(DEFAULT_SAVE_ROOT), help="Directory for saved reports")
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    save_root = Path(args.save_root).expanduser().resolve()
    print(f"[simple-receiver] starting on http://{args.host}:{args.port}")
    print(f"[simple-receiver] saving into {save_root}")

    server = ReceiverServer((args.host, args.port), ReceiverHandler, save_root=save_root)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("[simple-receiver] shutdown requested")
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
