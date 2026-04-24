#!/usr/bin/env python3

from __future__ import annotations

import argparse

import serial

from bus_servo_protocol import build_sync_move_packet
from send_uart1_servo_cmd import DEFAULT_BAUDRATE, DEFAULT_DEVICE, DEFAULT_TIMEOUT


DEFAULT_SERVO_1_ID = 1
DEFAULT_SERVO_2_ID = 2
DEFAULT_TARGET_1 = 1800
DEFAULT_TARGET_2 = 2750
DEFAULT_SPEED_1 = 120
DEFAULT_SPEED_2 = 120
DEFAULT_RUN_TIME = 0


def parse_args():
    parser = argparse.ArgumentParser(
        description="Slowly move servo 1 and servo 2 to 1800 / 2750 on RDK X5 UART1"
    )
    parser.add_argument("--device", default=DEFAULT_DEVICE, help="UART device path")
    parser.add_argument("--baudrate", type=int, default=DEFAULT_BAUDRATE, help="UART baudrate")
    parser.add_argument("--timeout", type=float, default=DEFAULT_TIMEOUT, help="UART timeout")
    parser.add_argument("--servo-1-id", type=int, default=DEFAULT_SERVO_1_ID)
    parser.add_argument("--servo-2-id", type=int, default=DEFAULT_SERVO_2_ID)
    parser.add_argument("--target-1", type=int, default=DEFAULT_TARGET_1)
    parser.add_argument("--target-2", type=int, default=DEFAULT_TARGET_2)
    parser.add_argument("--speed-1", type=int, default=DEFAULT_SPEED_1)
    parser.add_argument("--speed-2", type=int, default=DEFAULT_SPEED_2)
    parser.add_argument("--time", type=int, default=DEFAULT_RUN_TIME, dest="run_time")
    parser.add_argument(
        "--preview",
        action="store_true",
        help="Print the packet without sending it",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    moves = (
        (args.servo_1_id, args.target_1, args.run_time, args.speed_1),
        (args.servo_2_id, args.target_2, args.run_time, args.speed_2),
    )
    packet = build_sync_move_packet(moves)

    print(f"Device      : {args.device}")
    print(f"Baudrate    : {args.baudrate}")
    print(f"Timeout     : {args.timeout}")
    print(f"Servo 1     : id={args.servo_1_id} -> {args.target_1}, speed={args.speed_1}")
    print(f"Servo 2     : id={args.servo_2_id} -> {args.target_2}, speed={args.speed_2}")
    print(f"Run time    : {args.run_time}")
    print(f"Packet      : {packet.hex(' ')}")

    if args.preview:
        print("Preview     : not sent")
        return 0

    with serial.Serial(args.device, args.baudrate, timeout=args.timeout) as ser:
        sent = ser.write(packet)
        ser.flush()

    print(f"Sent bytes  : {sent}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
