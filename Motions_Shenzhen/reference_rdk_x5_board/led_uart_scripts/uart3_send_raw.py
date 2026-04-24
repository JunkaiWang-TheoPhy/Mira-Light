#!/usr/bin/env python3

from __future__ import annotations

import argparse

import serial


DEFAULT_DEVICE = "/dev/ttyS3"
DEFAULT_BAUDRATE = 115200
LINE_ENDINGS = {
    "none": "",
    "lf": "\n",
    "crlf": "\r\n",
}


def parse_args():
    parser = argparse.ArgumentParser(
        description="Send raw text or hex bytes from RDK X5 UART3 (/dev/ttyS3)"
    )
    parser.add_argument("--device", default=DEFAULT_DEVICE, help="UART device path")
    parser.add_argument("--baudrate", type=int, default=DEFAULT_BAUDRATE, help="UART baudrate")
    parser.add_argument(
        "--line-ending",
        choices=sorted(LINE_ENDINGS),
        default="lf",
        help="Append a line ending after text payloads",
    )

    subparsers = parser.add_subparsers(dest="mode", required=True)

    parser_text = subparsers.add_parser("text", help="Send a text payload")
    parser_text.add_argument("payload", help='Text to send, for example "HELP" or "ALL,255,255,255,255"')

    parser_hex = subparsers.add_parser("hex", help="Send raw hex bytes")
    parser_hex.add_argument("payload", help='Hex bytes, for example "48 45 4C 50 0A"')

    return parser.parse_args()


def parse_hex_bytes(text: str) -> bytes:
    cleaned = text.replace(" ", "").replace(":", "").replace("-", "")
    if len(cleaned) % 2 != 0:
        raise ValueError(f"hex payload must contain an even number of digits: {text}")
    return bytes.fromhex(cleaned)


def build_payload(args) -> bytes:
    if args.mode == "text":
        return (args.payload + LINE_ENDINGS[args.line_ending]).encode("utf-8")
    if args.mode == "hex":
        return parse_hex_bytes(args.payload)
    raise ValueError(f"unsupported mode: {args.mode}")


def main() -> int:
    args = parse_args()
    payload = build_payload(args)

    print(f"Device      : {args.device}")
    print(f"Baudrate    : {args.baudrate}")
    print(f"Mode        : {args.mode}")
    if args.mode == "text":
        print(f"Line ending : {args.line_ending}")
    print(f"Payload hex : {payload.hex(' ')}")

    with serial.Serial(args.device, args.baudrate, timeout=0.2) as ser:
        sent = ser.write(payload)
        ser.flush()

    print(f"Sent bytes  : {sent}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
