#!/usr/bin/env python3

from __future__ import annotations

import argparse
import time

import serial

from bus_servo_protocol import build_move_packet, parse_status_packet
from send_uart1_servo_cmd import DEFAULT_BAUDRATE, DEFAULT_DEVICE, DEFAULT_TIMEOUT, read_status_response


DEFAULT_IDS = (0, 1, 2, 3)
DEFAULT_TARGETS = (2048, 2048, 2048, 2780)
DEFAULT_SPEEDS = (300, 300, 300, 300)
DEFAULT_RUN_TIME = 0
DEFAULT_DELAY = 0.05


def parse_args():
    parser = argparse.ArgumentParser(
        description="Send four independent move commands for pose 2048 2048 2048 2780"
    )
    parser.add_argument("--device", default=DEFAULT_DEVICE, help="UART device path")
    parser.add_argument("--baudrate", type=int, default=DEFAULT_BAUDRATE, help="UART baudrate")
    parser.add_argument("--timeout", type=float, default=DEFAULT_TIMEOUT, help="UART timeout")
    parser.add_argument("--ids", nargs=4, type=int, default=DEFAULT_IDS, metavar=("ID0", "ID1", "ID2", "ID3"), help="Servo ids")
    parser.add_argument("--targets", nargs=4, type=int, default=DEFAULT_TARGETS, metavar=("P0", "P1", "P2", "P3"), help="Target positions")
    parser.add_argument("--speed", type=int, help="Same speed for all servos")
    parser.add_argument("--speeds", nargs=4, type=int, default=DEFAULT_SPEEDS, metavar=("S0", "S1", "S2", "S3"), help="Per-servo speeds")
    parser.add_argument("--time", type=int, default=DEFAULT_RUN_TIME, dest="run_time", help="Run time value")
    parser.add_argument("--delay", type=float, default=DEFAULT_DELAY, help="Delay between individual commands")
    parser.add_argument("--no-reply", action="store_true", help="Do not wait for servo status replies")
    parser.add_argument("--preview", action="store_true", help="Print packets without sending")
    return parser.parse_args()


def write_packet(ser: serial.Serial, packet: bytes) -> int:
    ser.reset_input_buffer()
    sent = ser.write(packet)
    ser.flush()
    return sent


def main() -> int:
    args = parse_args()
    ids = tuple(args.ids)
    targets = tuple(args.targets)
    speeds = (args.speed, args.speed, args.speed, args.speed) if args.speed is not None else tuple(args.speeds)

    packets = [
        build_move_packet(servo_id, target, args.run_time, speed)
        for servo_id, target, speed in zip(ids, targets, speeds)
    ]

    print(f"Device      : {args.device}")
    print(f"Baudrate    : {args.baudrate}")
    print(f"Timeout     : {args.timeout}")
    print(f"Servo IDs   : {ids}")
    print(f"Targets     : {targets}")
    print(f"Speeds      : {speeds}")
    print(f"Run time    : {args.run_time}")
    print(f"Delay       : {args.delay}")
    print(f"No reply    : {args.no_reply}")
    print(f"Preview     : {args.preview}")

    for servo_id, target, speed, packet in zip(ids, targets, speeds, packets):
        print(f"Servo {servo_id} -> {target} speed={speed}: {packet.hex(' ')}")

    if args.preview:
        return 0

    with serial.Serial(args.device, args.baudrate, timeout=args.timeout) as ser:
        for servo_id, target, speed, packet in zip(ids, targets, speeds, packets):
            sent = write_packet(ser, packet)
            print(f"Sent servo {servo_id} -> {target} speed={speed}: {sent} bytes")
            if not args.no_reply:
                reply = read_status_response(ser)
                status = parse_status_packet(reply)
                print(f"Reply servo {status.servo_id}: {reply.hex(' ')} error=0x{status.error:02X}")
            if args.delay > 0:
                time.sleep(args.delay)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
