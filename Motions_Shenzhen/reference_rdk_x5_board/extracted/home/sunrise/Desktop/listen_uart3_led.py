#!/usr/bin/env python3

import argparse
import time

import serial

from uart3_led_protocol import (
    AckMessage,
    BAUDRATE,
    ReadyMessage,
    TouchEvent,
    UART_DEVICE,
    UnknownMessage,
    parse_incoming_message,
    split_uart_chunk,
)


DEFAULT_IDLE_TIMEOUT = 0.2


def parse_args():
    parser = argparse.ArgumentParser(
        description="Listen to PRESS / RELEASE / HOLD events from RDK X5 uart3"
    )
    parser.add_argument("--device", default=UART_DEVICE, help="UART device path")
    parser.add_argument("--baudrate", type=int, default=BAUDRATE, help="UART baudrate")
    parser.add_argument(
        "--idle-timeout",
        type=float,
        default=DEFAULT_IDLE_TIMEOUT,
        help="Flush buffered data when UART stays idle for this many seconds",
    )
    parser.add_argument(
        "--hex",
        action="store_true",
        help="Also print raw bytes in hex",
    )
    return parser.parse_args()


def emit_message(raw_bytes: bytes, print_hex: bool):
    for part_type, part_bytes in split_uart_chunk(raw_bytes):
        if part_type == "binary":
            print(f"Binary : {part_bytes.hex(' ')}")
            if print_hex:
                print(f"Hex    : {part_bytes.hex(' ')}")
            print("")
            continue

        text = part_bytes.decode("utf-8", errors="replace").strip()
        if not text:
            continue

        parsed = parse_incoming_message(text)
        print(f"Text   : {text}")
        if isinstance(parsed, TouchEvent):
            if parsed.value is None:
                print(f"Event  : {parsed.name}")
            else:
                print(f"Event  : {parsed.name} ({parsed.value})")
        elif isinstance(parsed, AckMessage):
            print("Event  : ACK")
        elif isinstance(parsed, ReadyMessage):
            print("Event  : READY")
        elif isinstance(parsed, UnknownMessage):
            print(f"Event  : UNKNOWN ({parsed.text})")

        if print_hex:
            print(f"Hex    : {part_bytes.hex(' ')}")
        print("")


def main():
    args = parse_args()
    print(f"Listen  : {args.device} @ {args.baudrate}")
    print("Events  : PRESS / RELEASE / HOLD")
    print("Press Ctrl+C to stop")

    buffer = bytearray()
    last_rx_time = 0.0

    with serial.Serial(args.device, args.baudrate, timeout=0.2) as ser:
        try:
            while True:
                chunk = ser.read(ser.in_waiting or 1)
                if not chunk:
                    if buffer and (time.monotonic() - last_rx_time) > args.idle_timeout:
                        emit_message(bytes(buffer), args.hex)
                        buffer.clear()
                    continue

                last_rx_time = time.monotonic()
                buffer.extend(chunk)

                while True:
                    line_end = -1
                    marker_len = 0
                    for marker in (b"\r\n", b"\n", b"\r"):
                        idx = buffer.find(marker)
                        if idx != -1:
                            line_end = idx
                            marker_len = len(marker)
                            break

                    if line_end == -1:
                        break

                    raw = bytes(buffer[:line_end])
                    del buffer[: line_end + marker_len]
                    emit_message(raw, args.hex)
        except KeyboardInterrupt:
            print("\nStopped by user")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
