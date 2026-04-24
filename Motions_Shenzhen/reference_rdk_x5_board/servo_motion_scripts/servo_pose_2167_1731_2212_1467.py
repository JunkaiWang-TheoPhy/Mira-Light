#!/usr/bin/env python3

from __future__ import annotations

import argparse

import serial

from bus_servo_protocol import build_sync_move_packet


DEFAULT_DEVICE = "/dev/ttyS1"
DEFAULT_BAUDRATE = 1000000
DEFAULT_TIMEOUT = 0.2
DEFAULT_SPEED = 1000
DEFAULT_RUN_TIME = 0
SERVO_IDS = (0, 1, 2, 3)
TARGET_POSITIONS = (2167, 1731, 2212, 1467)


def parse_args():
    parser = argparse.ArgumentParser(
        description="Move servo 0/1/2/3 to fixed pose 2167/1731/2212/1467 on RDK X5 UART1"
    )
    parser.add_argument("--device", default=DEFAULT_DEVICE, help="UART device path")
    parser.add_argument("--baudrate", type=int, default=DEFAULT_BAUDRATE, help="UART baudrate")
    parser.add_argument("--timeout", type=float, default=DEFAULT_TIMEOUT, help="UART timeout")
    parser.add_argument("--speed", type=int, default=DEFAULT_SPEED, help="Move speed for all 4 servos")
    parser.add_argument("--time", type=int, default=DEFAULT_RUN_TIME, dest="run_time", help="Run time for all 4 servos")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    packet = build_sync_move_packet(
        (servo_id, position, args.run_time, args.speed)
        for servo_id, position in zip(SERVO_IDS, TARGET_POSITIONS)
    )

    print(f"Device      : {args.device}")
    print(f"Baudrate    : {args.baudrate}")
    print(f"Timeout     : {args.timeout}")
    print(f"Servo IDs   : {SERVO_IDS}")
    print(f"Positions   : {TARGET_POSITIONS}")
    print(f"Run time    : {args.run_time}")
    print(f"Speed       : {args.speed}")
    print(f"Packet      : {packet.hex(' ')}")

    with serial.Serial(args.device, args.baudrate, timeout=args.timeout) as ser:
        sent = ser.write(packet)
        ser.flush()

    print(f"Sent bytes  : {sent}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
