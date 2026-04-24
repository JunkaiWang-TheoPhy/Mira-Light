#!/usr/bin/env python3

from __future__ import annotations

import argparse
import time

import serial

from bus_servo_protocol import Address, build_move_packet, build_read_packet, build_sync_move_packet, parse_status_packet, unpack_u16
from send_uart1_servo_cmd import DEFAULT_BAUDRATE, DEFAULT_DEVICE, DEFAULT_TIMEOUT, read_status_response


DEFAULT_SERVO_IDS = (1, 3)
DEFAULT_TARGETS = (1800, 2750)
DEFAULT_SPEEDS = (120, 120)
DEFAULT_RUN_TIME = 0
DEFAULT_DELAY_RATIO = 0.0
DEFAULT_POLL_INTERVAL = 0.03
DEFAULT_MAX_WAIT = 6.0


def parse_args():
    parser = argparse.ArgumentParser(
        description="Slowly move servo 1 and servo 3 to 1800 and 2750"
    )
    parser.add_argument("--device", default=DEFAULT_DEVICE, help="UART device path")
    parser.add_argument("--baudrate", type=int, default=DEFAULT_BAUDRATE, help="UART baudrate")
    parser.add_argument("--timeout", type=float, default=DEFAULT_TIMEOUT, help="UART timeout")
    parser.add_argument(
        "--ids",
        nargs=2,
        type=int,
        default=DEFAULT_SERVO_IDS,
        metavar=("ID1", "ID3"),
        help="Two servo ids to move",
    )
    parser.add_argument(
        "--targets",
        nargs=2,
        type=int,
        default=DEFAULT_TARGETS,
        metavar=("P1", "P3"),
        help="Target positions for the two servos",
    )
    parser.add_argument("--target-1", type=int, help="Target position for servo 1")
    parser.add_argument("--target-3", type=int, help="Target position for servo 3")
    parser.add_argument(
        "--speeds",
        nargs=2,
        type=int,
        default=DEFAULT_SPEEDS,
        metavar=("S1", "S3"),
        help="Speed values for the two servos",
    )
    parser.add_argument(
        "--time",
        type=int,
        default=DEFAULT_RUN_TIME,
        dest="run_time",
        help="Run time value for both servos. Default 0 uses speed control.",
    )
    parser.add_argument(
        "--delay-ratio",
        type=float,
        default=DEFAULT_DELAY_RATIO,
        help="Start the second servo when the first servo reaches this progress ratio. 0 means start together.",
    )
    parser.add_argument(
        "--poll-interval",
        type=float,
        default=DEFAULT_POLL_INTERVAL,
        help="Polling interval while waiting for the delayed servo",
    )
    parser.add_argument(
        "--max-wait",
        type=float,
        default=DEFAULT_MAX_WAIT,
        help="Maximum seconds to wait before forcing the delayed servo to start",
    )
    parser.add_argument("--preview", action="store_true", help="Print the packet without sending it")
    return parser.parse_args()


def write_packet(ser: serial.Serial, packet: bytes) -> int:
    ser.reset_input_buffer()
    sent = ser.write(packet)
    ser.flush()
    return sent


def read_position(ser: serial.Serial, servo_id: int) -> int:
    packet = build_read_packet(servo_id, Address.CURRENT_POSITION, 2)
    write_packet(ser, packet)
    response = read_status_response(ser)
    status = parse_status_packet(response)
    return unpack_u16(status.parameters)


def crossed_ratio(start_pos: int, current_pos: int, target: int, ratio: float) -> bool:
    threshold = start_pos + (target - start_pos) * ratio
    if target >= start_pos:
        return current_pos >= threshold
    return current_pos <= threshold


def main() -> int:
    args = parse_args()
    ids = tuple(args.ids)
    raw_targets = list(args.targets)
    if args.target_1 is not None:
        raw_targets[0] = args.target_1
    if args.target_3 is not None:
        raw_targets[1] = args.target_3
    targets = tuple(raw_targets)
    speeds = tuple(args.speeds)

    if not 0.0 <= args.delay_ratio <= 1.0:
        raise ValueError(f"--delay-ratio must be in [0, 1], got {args.delay_ratio}")

    packet = build_sync_move_packet(
        (servo_id, position, args.run_time, speed)
        for servo_id, position, speed in zip(ids, targets, speeds)
    )
    first_packet = build_move_packet(ids[0], targets[0], args.run_time, speeds[0])
    second_packet = build_move_packet(ids[1], targets[1], args.run_time, speeds[1])

    print(f"Device      : {args.device}")
    print(f"Baudrate    : {args.baudrate}")
    print(f"Timeout     : {args.timeout}")
    print(f"Servo IDs   : {ids}")
    print(f"Targets     : {targets}")
    print(f"Speeds      : {speeds}")
    print(f"Run time    : {args.run_time}")
    print(f"Delay ratio : {args.delay_ratio}")
    print(f"Sync packet : {packet.hex(' ')}")
    print(f"First packet: {first_packet.hex(' ')}")
    print(f"Second pkt  : {second_packet.hex(' ')}")
    print(f"Preview     : {args.preview}")

    if args.preview:
        return 0

    with serial.Serial(args.device, args.baudrate, timeout=args.timeout) as ser:
        if args.delay_ratio == 0:
            sent = write_packet(ser, packet)
            print(f"Sent bytes  : {sent}")
            return 0

        start_pos = read_position(ser, ids[0])
        first_sent = write_packet(ser, first_packet)
        first_reply = read_status_response(ser)
        print(f"Start pos   : servo {ids[0]} = {start_pos}")
        print(f"First sent  : {first_sent}")
        print(f"First reply : {first_reply.hex(' ')}")

        started = time.monotonic()
        while True:
            current_pos = read_position(ser, ids[0])
            print(f"Servo {ids[0]} pos : {current_pos}")
            if crossed_ratio(start_pos, current_pos, targets[0], args.delay_ratio):
                print(f"Delay ratio reached; starting servo {ids[1]}.")
                break
            if (time.monotonic() - started) >= args.max_wait:
                print(f"Max wait reached; starting servo {ids[1]}.")
                break
            time.sleep(args.poll_interval)

        second_sent = write_packet(ser, second_packet)
        second_reply = read_status_response(ser)
        print(f"Second sent : {second_sent}")
        print(f"Second reply: {second_reply.hex(' ')}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
