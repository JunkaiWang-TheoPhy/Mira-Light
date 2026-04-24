#!/usr/bin/env python3
"""Headless camera receiver service for Mira Light.

This is the launchd-friendly counterpart to docs/cam_receiver_new.py:

- accepts JPEG frames over HTTP
- saves them to disk for downstream vision extraction
- exposes GET /health
- does not open any GUI preview window
"""

from __future__ import annotations

import argparse
import logging
import threading
import time
from dataclasses import dataclass, field
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import cv2
import numpy as np


LOGGER = logging.getLogger("cam_receiver_service")


@dataclass
class ReceiverState:
    latest_seq: str = "?"
    frame_count: int = 0
    saved_count: int = 0
    latency_sample_count: int = 0
    latency_last_ms: float | None = None
    latency_total_ms: float = 0.0
    latency_min_ms: float | None = None
    latency_max_ms: float | None = None
    latest_frame_shape: tuple[int, int, int] | None = None
    frame_lock: threading.Lock = field(default_factory=threading.Lock)


class FrameHandler(BaseHTTPRequestHandler):
    server: "CameraHTTPServer"

    def do_POST(self) -> None:  # noqa: N802
        state = self.server.state
        length = int(self.headers.get("Content-Length", 0))
        seq = self.headers.get("X-Seq", "?")
        latency_ms = self._compute_latency_ms()

        if length <= 0:
            self.send_response(400)
            self.end_headers()
            self.wfile.write(b"Missing Content-Length")
            LOGGER.warning("Rejected empty frame: seq=%s", seq)
            return

        data = self.rfile.read(length)
        arr = np.frombuffer(data, dtype=np.uint8)
        img = cv2.imdecode(arr, cv2.IMREAD_COLOR)

        if img is None:
            self.send_response(400)
            self.end_headers()
            self.wfile.write(b"Invalid JPEG payload")
            LOGGER.warning("Rejected invalid JPEG: seq=%s size=%s", seq, length)
            return

        saved_path = self.server.save_dir / build_frame_name(state.frame_count + 1, seq)
        saved_path.write_bytes(data)

        with state.frame_lock:
            state.latest_seq = seq
            state.frame_count += 1
            state.saved_count += 1
            state.latest_frame_shape = img.shape
            if latency_ms is not None:
                state.latency_last_ms = latency_ms
                state.latency_sample_count += 1
                state.latency_total_ms += latency_ms
                state.latency_min_ms = latency_ms if state.latency_min_ms is None else min(state.latency_min_ms, latency_ms)
                state.latency_max_ms = latency_ms if state.latency_max_ms is None else max(state.latency_max_ms, latency_ms)
            current_frame_count = state.frame_count

        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"OK")

        LOGGER.info(
            "Received frame seq=%s size=%s bytes count=%s latency_ms=%s saved=%s",
            seq,
            length,
            current_frame_count,
            format_latency(latency_ms),
            saved_path,
        )

    def do_GET(self) -> None:  # noqa: N802
        if self.path.rstrip("/") != "/health":
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b"Not Found")
            return

        state = self.server.state
        with state.frame_lock:
            avg_ms = (
                state.latency_total_ms / state.latency_sample_count
                if state.latency_sample_count > 0
                else None
            )
            shape = state.latest_frame_shape
            payload = (
                f"status=ok frame_count={state.frame_count} "
                f"saved_count={state.saved_count} latest_seq={state.latest_seq} "
                f"shape={shape} "
                f"latency_samples={state.latency_sample_count} "
                f"latency_last_ms={format_latency(state.latency_last_ms)} "
                f"latency_avg_ms={format_latency(avg_ms)} "
                f"latency_min_ms={format_latency(state.latency_min_ms)} "
                f"latency_max_ms={format_latency(state.latency_max_ms)}\n"
            )

        self.send_response(200)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.end_headers()
        self.wfile.write(payload.encode("utf-8"))

    def log_message(self, fmt: str, *args: object) -> None:
        return

    def _compute_latency_ms(self) -> float | None:
        raw = self.headers.get("X-Timestamp")
        if raw is None:
            return None
        try:
            sent_ts = float(raw)
        except (TypeError, ValueError):
            LOGGER.warning("Invalid X-Timestamp header: %r", raw)
            return None
        return max(0.0, (time.time() - sent_ts) * 1000.0)


class CameraHTTPServer(ThreadingHTTPServer):
    def __init__(self, server_address: tuple[str, int], handler_cls, state: ReceiverState, save_dir: Path):
        self.state = state
        self.save_dir = save_dir
        super().__init__(server_address, handler_cls)


def build_frame_name(frame_count: int, seq: str) -> str:
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S-%f")
    safe_seq = "".join(ch if ch.isalnum() or ch in ("-", "_") else "_" for ch in seq)
    return f"{timestamp}-frame-{frame_count:06d}-seq-{safe_seq}.jpg"


def format_latency(value: float | None) -> str:
    if value is None:
        return "na"
    return f"{value:.1f}"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Headless JPEG receiver for Mira Light vision.")
    parser.add_argument("--host", default="0.0.0.0", help="Listen host")
    parser.add_argument("--port", type=int, default=8000, help="Listen port")
    parser.add_argument("--save-dir", type=Path, required=True, help="Directory to save JPEG frames")
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Logging verbosity",
    )
    return parser.parse_args()


def configure_logging(level: str) -> None:
    logging.basicConfig(
        level=getattr(logging, level),
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )


def main() -> int:
    args = parse_args()
    configure_logging(args.log_level)

    save_dir = args.save_dir.expanduser().resolve()
    save_dir.mkdir(parents=True, exist_ok=True)
    LOGGER.info("Saving received frames to %s", save_dir)

    state = ReceiverState()
    server = CameraHTTPServer((args.host, args.port), FrameHandler, state, save_dir)
    LOGGER.info("Headless receiver listening on %s:%s", args.host, args.port)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        LOGGER.info("Receiver shutdown requested")
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
