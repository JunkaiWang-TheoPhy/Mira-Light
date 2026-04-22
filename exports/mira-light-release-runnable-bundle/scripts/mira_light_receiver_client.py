#!/usr/bin/env python3
"""Client helper for sending Mira Light data to the local receiver.

Binary upload is the default mode.
Base64 is only used when explicitly requested.
"""

from __future__ import annotations

import argparse
import base64
import json
import mimetypes
from pathlib import Path
from typing import Any
from urllib import error, parse, request


DEFAULT_RECEIVER_URL = "http://127.0.0.1:9784"


def send_request(url: str, method: str = "GET", *, body: bytes | None = None, headers: dict[str, str] | None = None) -> Any:
    req = request.Request(url=url, data=body, method=method)
    for key, value in (headers or {}).items():
        req.add_header(key, value)

    with request.urlopen(req, timeout=10) as res:
        text = res.read().decode("utf-8")
        return json.loads(text) if text.strip() else {}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Send status or file data to simple_lamp_receiver.")
    parser.add_argument(
        "--receiver-url",
        default=DEFAULT_RECEIVER_URL,
        help="Receiver base URL, e.g. http://192.168.50.151:9784",
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("health", help="Query receiver health and preferred upload mode")

    status_parser = subparsers.add_parser("status", help="Send a status payload to /device/status")
    status_parser.add_argument("--device-id", default="mira-light-001")
    status_parser.add_argument("--payload-file", type=Path, help="Read full JSON payload from a file")
    status_parser.add_argument("--scene")
    status_parser.add_argument("--playing", action="store_true")
    status_parser.add_argument("--servo1", type=int)
    status_parser.add_argument("--servo2", type=int)
    status_parser.add_argument("--servo3", type=int)
    status_parser.add_argument("--servo4", type=int)
    status_parser.add_argument("--led-mode")
    status_parser.add_argument("--brightness", type=int)

    upload_parser = subparsers.add_parser("upload", help="Upload a file to the receiver")
    upload_parser.add_argument("file", type=Path, help="Path to the local file to upload")
    upload_parser.add_argument("--device-id", default="mira-light-001")
    upload_parser.add_argument("--category", default="images")
    upload_parser.add_argument("--file-name", help="Override uploaded file name")
    upload_parser.add_argument("--content-type", help="Override MIME type")
    upload_parser.add_argument(
        "--mode",
        choices=("binary", "base64"),
        default="binary",
        help="Upload mode; binary is the default and preferred path",
    )

    return parser


def cmd_health(receiver_url: str) -> int:
    payload = send_request(f"{receiver_url.rstrip('/')}/health")
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


def cmd_status(receiver_url: str, args: argparse.Namespace) -> int:
    if args.payload_file:
        payload = json.loads(args.payload_file.read_text(encoding="utf-8"))
    else:
        payload: dict[str, Any] = {"deviceId": args.device_id}
        if args.scene:
            payload["scene"] = args.scene
        if args.playing:
            payload["playing"] = True
        if args.servo1 is not None:
            payload["servo1"] = args.servo1
        if args.servo2 is not None:
            payload["servo2"] = args.servo2
        if args.servo3 is not None:
            payload["servo3"] = args.servo3
        if args.servo4 is not None:
            payload["servo4"] = args.servo4
        if args.led_mode:
            payload["ledMode"] = args.led_mode
        if args.brightness is not None:
            payload["brightness"] = args.brightness

    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    result = send_request(
        f"{receiver_url.rstrip('/')}/device/status",
        method="POST",
        body=body,
        headers={"Content-Type": "application/json; charset=utf-8"},
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


def cmd_upload(receiver_url: str, args: argparse.Namespace) -> int:
    file_path = args.file.expanduser().resolve()
    raw = file_path.read_bytes()
    file_name = args.file_name or file_path.name
    content_type = args.content_type or mimetypes.guess_type(file_name)[0] or "application/octet-stream"

    if args.mode == "binary":
        query = parse.urlencode(
            {
                "deviceId": args.device_id,
                "fileName": file_name,
                "category": args.category,
            }
        )
        result = send_request(
            f"{receiver_url.rstrip('/')}/device/upload?{query}",
            method="POST",
            body=raw,
            headers={
                "Content-Type": content_type,
                "X-Device-Id": args.device_id,
                "X-File-Name": file_name,
                "X-File-Category": args.category,
            },
        )
    else:
        payload = {
            "deviceId": args.device_id,
            "fileName": file_name,
            "category": args.category,
            "contentType": content_type,
            "contentBase64": base64.b64encode(raw).decode("ascii"),
        }
        result = send_request(
            f"{receiver_url.rstrip('/')}/device/upload-base64",
            method="POST",
            body=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
            headers={"Content-Type": "application/json; charset=utf-8"},
        )

    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    receiver_url = args.receiver_url.rstrip("/")

    try:
        if args.command == "health":
            return cmd_health(receiver_url)
        if args.command == "status":
            return cmd_status(receiver_url, args)
        if args.command == "upload":
            return cmd_upload(receiver_url, args)
        parser.error(f"Unknown command: {args.command}")
        return 2
    except error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise SystemExit(f"HTTP {exc.code}: {body}") from exc
    except error.URLError as exc:
        raise SystemExit(f"Request failed: {exc}") from exc


if __name__ == "__main__":
    raise SystemExit(main())
