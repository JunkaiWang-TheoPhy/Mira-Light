#!/usr/bin/env python3

from __future__ import annotations

import argparse
import time

import serial

from bus_servo_protocol import (
    Address,
    build_read_packet,
    build_sync_move_packet,
    parse_status_packet,
    unpack_u16,
)
from send_uart1_servo_cmd import DEFAULT_BAUDRATE, DEFAULT_DEVICE, DEFAULT_TIMEOUT, read_status_response


DEFAULT_SERVO_IDS = (1, 2)
DEFAULT_TARGETS = (1848, 1808)
DEFAULT_SPEEDS = (80, 80)
DEFAULT_RUN_TIME = 0
DEFAULT_TOLERANCE = 20
DEFAULT_SETTLE_POLLS = 3
DEFAULT_WAIT_MARGIN = 2.0
DEFAULT_MAX_WAIT = 20.0


def parse_args():
    parser = argparse.ArgumentParser(
        description="Dodge-away motion: move servo 1 and 2 to 1848 and 1808"
    )
    parser.add_argument("--device", default=DEFAULT_DEVICE, help="UART device path")
    parser.add_argument("--baudrate", type=int, default=DEFAULT_BAUDRATE, help="UART baudrate")
    parser.add_argument("--timeout", type=float, default=DEFAULT_TIMEOUT, help="UART timeout")
    parser.add_argument("--ids", nargs=2, type=int, default=DEFAULT_SERVO_IDS, metavar=("ID1", "ID2"), help="Two servo ids")
    parser.add_argument("--targets", nargs=2, type=int, default=DEFAULT_TARGETS, metavar=("P1", "P2"), help="Target positions")
    parser.add_argument("--target-1", type=int, help="Target position for servo 1")
    parser.add_argument("--target-2", type=int, help="Target position for servo 2")
    parser.add_argument("--speed", type=int, help="Move speed for both servos")
    parser.add_argument("--speeds", nargs=2, type=int, default=DEFAULT_SPEEDS, metavar=("S1", "S2"), help="Move speeds for servo 1 and servo 2")
    parser.add_argument("--time", type=int, default=DEFAULT_RUN_TIME, dest="run_time", help="Run time value")
    parser.add_argument("--tolerance", type=int, default=DEFAULT_TOLERANCE, help="Position error accepted as reached")
    parser.add_argument("--settle-polls", type=int, default=DEFAULT_SETTLE_POLLS, help="Consecutive reached polls before finishing")
    parser.add_argument("--wait-margin", type=float, default=DEFAULT_WAIT_MARGIN, help="Extra seconds added to estimated move time")
    parser.add_argument("--max-wait", type=float, default=DEFAULT_MAX_WAIT, help="Maximum seconds to wait for the pose")
    parser.add_argument("--preview", action="store_true", help="Print packet without sending it")
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


def wait_until_reached(
    ser: serial.Serial,
    ids: tuple[int, int],
    targets: tuple[int, int],
    timeout_s: float,
    tolerance: int,
    settle_polls: int,
) -> tuple[int, int]:
    stable_count = 0
    last_positions = targets
    deadline = time.monotonic() + timeout_s

    while True:
        positions = tuple(read_position(ser, servo_id) for servo_id in ids)
        last_positions = positions
        errors = tuple(abs(position - target) for position, target in zip(positions, targets))
        print(f"Positions   : servo {ids[0]}={positions[0]} err={errors[0]}, servo {ids[1]}={positions[1]} err={errors[1]}")

        if all(error <= tolerance for error in errors):
            stable_count += 1
            if stable_count >= settle_polls:
                print("Reached     : yes")
                return positions
        else:
            stable_count = 0

        if time.monotonic() >= deadline:
            print("Reached     : timeout, finishing")
            return last_positions

        time.sleep(0.1)


def main() -> int:
    args = parse_args()
    if args.settle_polls < 1:
        raise ValueError(f"--settle-polls must be >= 1, got {args.settle_polls}")

    ids = tuple(args.ids)
    raw_targets = list(args.targets)
    if args.target_1 is not None:
        raw_targets[0] = args.target_1
    if args.target_2 is not None:
        raw_targets[1] = args.target_2
    targets = tuple(raw_targets)
    speeds = (args.speed, args.speed) if args.speed is not None else tuple(args.speeds)

    packet = build_sync_move_packet(
        (servo_id, target, args.run_time, speed)
        for servo_id, target, speed in zip(ids, targets, speeds)
    )

    print(f"Device      : {args.device}")
    print(f"Baudrate    : {args.baudrate}")
    print(f"Timeout     : {args.timeout}")
    print(f"Servo IDs   : {ids}")
    print(f"Targets     : {targets}")
    print(f"Speeds      : {speeds}")
    print(f"Run time    : {args.run_time}")
    print(f"Tolerance   : {args.tolerance}")
    print(f"Settle polls: {args.settle_polls}")
    print(f"Wait margin : {args.wait_margin}")
    print(f"Max wait    : {args.max_wait}")
    print(f"Packet      : {packet.hex(' ')}")
    print(f"Preview     : {args.preview}")

    if args.preview:
        return 0

    with serial.Serial(args.device, args.baudrate, timeout=args.timeout) as ser:
        starts = tuple(read_position(ser, servo_id) for servo_id in ids)
        slowest_estimates = [
            abs(target - start) / speed
            for start, target, speed in zip(starts, targets, speeds)
            if speed > 0
        ]
        if args.run_time > 0:
            wait_s = min(args.run_time / 1000.0 + args.wait_margin, args.max_wait)
        elif slowest_estimates:
            wait_s = min(max(slowest_estimates) + args.wait_margin, args.max_wait)
        else:
            wait_s = args.max_wait
        sent = write_packet(ser, packet)
        print(f"Starts      : {starts}")
        print(f"Wait max    : {wait_s:.1f}s")
        print(f"Sent bytes  : {sent}")
        wait_until_reached(ser, ids, targets, wait_s, args.tolerance, args.settle_polls)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
