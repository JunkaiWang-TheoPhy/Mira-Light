#!/usr/bin/env python3
"""Replay saved JPEG frames into the Mira Light camera receiver."""

from __future__ import annotations

import argparse
from pathlib import Path
import time
from typing import Iterable
from urllib import error, request


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Replay saved JPEG frames into cam_receiver_service.py.")
    parser.add_argument(
        "--captures-dir",
        type=Path,
        required=True,
        help="Directory containing .jpg frames to replay.",
    )
    parser.add_argument(
        "--receiver-url",
        default="http://127.0.0.1:8000",
        help="Base URL of the HTTP receiver.",
    )
    parser.add_argument(
        "--fps",
        type=float,
        default=3.0,
        help="Replay rate. Use 0 to send as fast as possible.",
    )
    parser.add_argument(
        "--loop",
        action="store_true",
        help="Replay frames in a loop until interrupted.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=0,
        help="Optional max number of frames to send from the sorted capture list.",
    )
    return parser


def iter_frames(captures_dir: Path, limit: int) -> list[Path]:
    frames = sorted(captures_dir.rglob("*.jpg"))
    if limit > 0:
        frames = frames[:limit]
    return frames


def send_frame(receiver_url: str, frame_path: Path, seq: str) -> int:
    payload = frame_path.read_bytes()
    req = request.Request(
        receiver_url.rstrip("/"),
        data=payload,
        method="POST",
        headers={
            "Content-Type": "image/jpeg",
            "Content-Length": str(len(payload)),
            "X-Seq": seq,
            "X-Timestamp": str(time.time()),
        },
    )
    with request.urlopen(req, timeout=10) as response:
        response.read()
        return response.status


def replay(frames: Iterable[Path], *, receiver_url: str, interval_s: float) -> int:
    sent = 0
    for index, frame_path in enumerate(frames, start=1):
        seq = frame_path.stem or f"frame-{index:04d}"
        status = send_frame(receiver_url, frame_path, seq)
        sent += 1
        print(f"[vision-replay] sent seq={seq} status={status} path={frame_path}")
        if interval_s > 0:
            time.sleep(interval_s)
    return sent


def main() -> int:
    args = build_parser().parse_args()
    captures_dir = args.captures_dir.expanduser().resolve()
    if not captures_dir.exists():
        raise SystemExit(f"captures dir not found: {captures_dir}")

    frames = iter_frames(captures_dir, args.limit)
    if not frames:
        raise SystemExit(f"no jpg frames found in {captures_dir}")

    interval_s = 0.0 if args.fps <= 0 else 1.0 / args.fps

    try:
        while True:
            sent = replay(frames, receiver_url=args.receiver_url, interval_s=interval_s)
            print(f"[vision-replay] batch complete sent={sent} receiver={args.receiver_url}")
            if not args.loop:
                return 0
    except KeyboardInterrupt:
        print("[vision-replay] stopped by user")
        return 0
    except error.URLError as exc:
        raise SystemExit(f"receiver request failed: {exc}") from exc


if __name__ == "__main__":
    raise SystemExit(main())
