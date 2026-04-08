"""
图像接收端脚本（正式版）

功能：
- 使用 argparse 管理启动参数
- 支持自定义监听 host / port
- 可选将接收到的 JPEG 帧保存到磁盘
- 使用 logging 输出结构化运行日志

用法示例：
    python cam_receiver_new.py --host 0.0.0.0 --port 8000
    python cam_receiver_new.py --port 9000 --save-dir ./captures
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


LOGGER = logging.getLogger("cam_receiver")


@dataclass
class ReceiverState:
    latest_frame: np.ndarray | None = None
    latest_seq: str = "?"
    frame_count: int = 0
    saved_count: int = 0
    latency_sample_count: int = 0
    latency_last_ms: float | None = None
    latency_total_ms: float = 0.0
    latency_min_ms: float | None = None
    latency_max_ms: float | None = None
    frame_lock: threading.Lock = field(default_factory=threading.Lock)


class FrameHandler(BaseHTTPRequestHandler):
    server: "CameraHTTPServer"

    def do_POST(self) -> None:
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

        saved_path = None
        with state.frame_lock:
            state.latest_frame = img
            state.latest_seq = seq
            state.frame_count += 1
            current_frame_count = state.frame_count
            if latency_ms is not None:
                state.latency_last_ms = latency_ms
                state.latency_sample_count += 1
                state.latency_total_ms += latency_ms
                state.latency_min_ms = latency_ms if state.latency_min_ms is None else min(state.latency_min_ms, latency_ms)
                state.latency_max_ms = latency_ms if state.latency_max_ms is None else max(state.latency_max_ms, latency_ms)

            if self.server.save_dir is not None:
                saved_path = self.server.save_dir / build_frame_name(
                    current_frame_count,
                    seq,
                )
                saved_path.write_bytes(data)
                state.saved_count += 1

        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"OK")

        if saved_path is not None:
            LOGGER.info(
                "Received frame seq=%s size=%s bytes count=%s latency_ms=%s saved=%s",
                seq,
                length,
                current_frame_count,
                format_latency(latency_ms),
                saved_path,
            )
        else:
            LOGGER.info(
                "Received frame seq=%s size=%s bytes count=%s latency_ms=%s",
                seq,
                length,
                current_frame_count,
                format_latency(latency_ms),
            )

    def do_GET(self) -> None:
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
            payload = (
                f"status=ok frame_count={state.frame_count} "
                f"saved_count={state.saved_count} latest_seq={state.latest_seq} "
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
    def __init__(self, server_address: tuple[str, int], handler_cls, state: ReceiverState, save_dir: Path | None):
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
    parser = argparse.ArgumentParser(description="接收 JPEG 帧并在本地显示。")
    parser.add_argument("port_pos", nargs="?", type=int, help="兼容旧用法的位置端口参数")
    parser.add_argument("--host", default="0.0.0.0", help="监听地址，默认 0.0.0.0")
    parser.add_argument("--port", type=int, help="监听端口，默认 8000")
    parser.add_argument(
        "--save-dir",
        type=Path,
        help="可选，保存收到的 JPEG 帧目录；未指定则只显示不落盘",
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="日志级别，默认 INFO",
    )
    return parser.parse_args()


def configure_logging(level: str) -> None:
    logging.basicConfig(
        level=getattr(logging, level),
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )


def run_server(server: CameraHTTPServer) -> None:
    LOGGER.info(
        "HTTP server listening on %s:%s",
        server.server_address[0],
        server.server_address[1],
    )
    server.serve_forever()


def ensure_save_dir(save_dir: Path | None) -> Path | None:
    if save_dir is None:
        return None

    save_dir.mkdir(parents=True, exist_ok=True)
    LOGGER.info("Saving received frames to %s", save_dir)
    return save_dir


def display_loop(state: ReceiverState) -> None:
    LOGGER.info("Waiting for frames... press q to quit the preview window")

    last_reported_count = -1
    while True:
        with state.frame_lock:
            frame = state.latest_frame.copy() if state.latest_frame is not None else None
            cnt = state.frame_count
            seq = state.latest_seq
            saved = state.saved_count

        if frame is not None:
            info = f"frames: {cnt}  seq: {seq}  saved: {saved}"
            cv2.putText(
                frame,
                info,
                (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (0, 255, 0),
                2,
            )
            cv2.imshow("RDK X5 Camera Stream", frame)

        if cnt != last_reported_count and cnt > 0 and cnt % 50 == 0:
            LOGGER.info("Processed %s frames (saved=%s)", cnt, saved)
            last_reported_count = cnt

        key = cv2.waitKey(30) & 0xFF
        if key == ord("q"):
            break

        time.sleep(0.01)

    cv2.destroyAllWindows()
    LOGGER.info("Preview closed. Total frames=%s saved=%s", state.frame_count, state.saved_count)


def main() -> None:
    args = parse_args()
    configure_logging(args.log_level)

    port = args.port if args.port is not None else (args.port_pos if args.port_pos is not None else 8000)
    save_dir = ensure_save_dir(args.save_dir)
    state = ReceiverState()
    server = CameraHTTPServer((args.host, port), FrameHandler, state, save_dir)

    server_thread = threading.Thread(target=run_server, args=(server,), daemon=True)
    server_thread.start()

    try:
        display_loop(state)
    finally:
        server.shutdown()
        server.server_close()
        LOGGER.info("Receiver stopped")


if __name__ == "__main__":
    main()
