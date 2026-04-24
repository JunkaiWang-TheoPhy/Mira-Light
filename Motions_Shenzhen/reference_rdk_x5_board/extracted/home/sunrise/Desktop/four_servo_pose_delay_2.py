#!/usr/bin/env python3

from __future__ import annotations

import argparse
import time

import serial

from bus_servo_protocol import Address, build_read_packet, build_sync_move_packet, parse_status_packet, unpack_u16
from send_uart1_servo_cmd import DEFAULT_BAUDRATE, DEFAULT_DEVICE, DEFAULT_TIMEOUT, read_status_response


DEFAULT_IDS = (0, 1, 2, 3)
DEFAULT_TARGETS = (2048, 2400, 1700, 2130)
DEFAULT_POLL_INTERVAL = 0.03
DEFAULT_DELAY_RATIO = 0.25
DEFAULT_SPEEDS = (1000, 160, 380, 1000)
DEFAULT_MAX_WAIT = 6.0


def parse_args():
    parser = argparse.ArgumentParser(
        description="Move servo 0/1/3 to fixed targets first, then start servo 2 after servo 1 reaches an adjustable progress ratio"
    )
    parser.add_argument("--device", default=DEFAULT_DEVICE, help="UART device path")
    parser.add_argument("--baudrate", type=int, default=DEFAULT_BAUDRATE, help="UART baudrate")
    parser.add_argument("--timeout", type=float, default=DEFAULT_TIMEOUT, help="UART timeout")
    parser.add_argument(
        "--ids",
        nargs=4,
        type=int,
        default=DEFAULT_IDS,
        metavar=("ID0", "ID1", "ID2", "ID3"),
        help="Servo ids in order (default: 0 1 2 3)",
    )
    parser.add_argument(
        "--targets",
        nargs=4,
        type=int,
        default=DEFAULT_TARGETS,
        metavar=("P0", "P1", "P2", "P3"),
        help="Target positions for servo 0/1/2/3",
    )
    parser.add_argument(
        "--speeds",
        nargs=4,
        type=int,
        default=DEFAULT_SPEEDS,
        metavar=("S0", "S1", "S2", "S3"),
        help="Per-servo speeds for servo 0/1/2/3",
    )
    parser.add_argument(
        "--delay-ratio",
        type=float,
        default=DEFAULT_DELAY_RATIO,
        help="Start servo 2 when servo 1 reaches this fraction of travel toward target 1",
    )
    parser.add_argument(
        "--poll-interval",
        type=float,
        default=DEFAULT_POLL_INTERVAL,
        help="Polling interval while waiting for servo 1 progress",
    )
    parser.add_argument(
        "--max-wait",
        type=float,
        default=DEFAULT_MAX_WAIT,
        help="Maximum seconds to wait before forcing servo 2 to start",
    )
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


def build_sync_packet(ids: tuple[int, int, int, int], positions: tuple[int, int, int, int], speeds: tuple[int, int, int, int]) -> bytes:
    return build_sync_move_packet(
        (servo_id, position, 0, speed)
        for servo_id, position, speed in zip(ids, positions, speeds)
    )


def main() -> int:
    args = parse_args()
    ids = tuple(args.ids)
    targets = tuple(args.targets)
    speeds = tuple(args.speeds)

    if not 0.0 <= args.delay_ratio <= 1.0:
        raise ValueError(f"--delay-ratio must be in [0, 1], got {args.delay_ratio}")

    with serial.Serial(args.device, args.baudrate, timeout=args.timeout) as ser:
        start_positions = tuple(read_position(ser, servo_id) for servo_id in ids)

        stage_1_positions = (
            targets[0],
            targets[1],
            start_positions[2],
            targets[3],
        )
        stage_2_positions = targets

        stage_1_packet = build_sync_packet(ids, stage_1_positions, speeds)
        stage_1_sent = write_packet(ser, stage_1_packet)

        print(f"Device         : {args.device}")
        print(f"Baudrate       : {args.baudrate}")
        print(f"Timeout        : {args.timeout}")
        print(f"Servo IDs      : {ids}")
        print(f"Start pos      : {start_positions}")
        print(f"Targets        : {targets}")
        print(f"Speeds         : {speeds}")
        print(f"Delay ratio    : {args.delay_ratio}")
        print(f"Poll interval  : {args.poll_interval}")
        print(f"Max wait       : {args.max_wait}")
        print(f"Stage 1 pos    : {stage_1_positions}")
        print(f"Stage 2 pos    : {stage_2_positions}")
        print(f"Stage 1 packet : {stage_1_packet.hex(' ')}")
        print(f"Stage 1 sent   : {stage_1_sent}")
        print("Servo 0/1/3 started. Waiting for servo 1 progress before starting servo 2...")

        started = time.monotonic()
        while True:
            current_1 = read_position(ser, ids[1])
            print(f"Servo 1 pos    : {current_1}")
            if crossed_ratio(start_positions[1], current_1, targets[1], args.delay_ratio):
                print("Servo 1 reached the configured ratio; starting servo 2 now.")
                break
            if (time.monotonic() - started) >= args.max_wait:
                print("Max wait reached; starting servo 2 now.")
                break
            time.sleep(args.poll_interval)

        stage_2_packet = build_sync_packet(ids, stage_2_positions, speeds)
        stage_2_sent = write_packet(ser, stage_2_packet)
        print(f"Stage 2 packet : {stage_2_packet.hex(' ')}")
        print(f"Stage 2 sent   : {stage_2_sent}")
        print("Servo 2 started.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
