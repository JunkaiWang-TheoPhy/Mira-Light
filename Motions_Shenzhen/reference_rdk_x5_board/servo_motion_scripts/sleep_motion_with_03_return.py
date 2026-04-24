#!/usr/bin/env python3

from __future__ import annotations

import argparse
import time

import serial

from bus_servo_protocol import Address, build_read_packet, build_sync_move_packet, parse_status_packet, unpack_u16
from send_uart1_servo_cmd import DEFAULT_BAUDRATE, DEFAULT_DEVICE, DEFAULT_TIMEOUT, read_status_response


DEFAULT_IDS = (0, 1, 2, 3)
DEFAULT_TARGET_1 = 1711
DEFAULT_TARGET_2 = 3145
DEFAULT_SPEEDS = (1000, 160, 680, 1000)
DEFAULT_DELAY_RATIO = 0.68
DEFAULT_RETURN03_RATIO = 0.25
DEFAULT_RETURN_0 = 2048
DEFAULT_RETURN_3 = 2130
DEFAULT_POLL_INTERVAL = 0.03
DEFAULT_MAX_WAIT = 6.0


def parse_args():
    parser = argparse.ArgumentParser(
        description="Sleep motion with servo 2 first; at 25% trigger servo 0/3 return, at 68% trigger servo 1"
    )
    parser.add_argument("--device", default=DEFAULT_DEVICE, help="UART device path")
    parser.add_argument("--baudrate", type=int, default=DEFAULT_BAUDRATE, help="UART baudrate")
    parser.add_argument("--timeout", type=float, default=DEFAULT_TIMEOUT, help="UART read timeout in seconds")
    parser.add_argument(
        "--ids",
        nargs=4,
        type=int,
        default=DEFAULT_IDS,
        metavar=("ID0", "ID1", "ID2", "ID3"),
        help="Servo ids in order (default: 0 1 2 3)",
    )
    parser.add_argument("--target-1", type=int, default=DEFAULT_TARGET_1, help="Target position for servo 1")
    parser.add_argument("--target-2", type=int, default=DEFAULT_TARGET_2, help="Target position for servo 2")
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
        help="Start servo 1 when servo 2 reaches this fraction of travel toward target 2",
    )
    parser.add_argument(
        "--return03-ratio",
        type=float,
        default=DEFAULT_RETURN03_RATIO,
        help="Start servo 0->2048 and servo 3->2130 when servo 2 reaches this fraction of travel",
    )
    parser.add_argument("--return-0", type=int, default=DEFAULT_RETURN_0, help="Servo 0 return target")
    parser.add_argument("--return-3", type=int, default=DEFAULT_RETURN_3, help="Servo 3 return target")
    parser.add_argument(
        "--poll-interval",
        type=float,
        default=DEFAULT_POLL_INTERVAL,
        help="Polling interval while waiting for servo 2 progress",
    )
    parser.add_argument(
        "--max-wait",
        type=float,
        default=DEFAULT_MAX_WAIT,
        help="Maximum seconds to wait before forcing later stages to start",
    )
    parser.add_argument("--preview", action="store_true", help="Print planned stages without sending packets")
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
    speeds = tuple(args.speeds)

    if not 0.0 <= args.return03_ratio <= 1.0:
        raise ValueError(f"--return03-ratio must be in [0, 1], got {args.return03_ratio}")
    if not 0.0 <= args.delay_ratio <= 1.0:
        raise ValueError(f"--delay-ratio must be in [0, 1], got {args.delay_ratio}")
    if args.return03_ratio > args.delay_ratio:
        raise ValueError("--return03-ratio should be <= --delay-ratio for this staged motion")

    with serial.Serial(args.device, args.baudrate, timeout=args.timeout) as ser:
        current_positions = tuple(read_position(ser, servo_id) for servo_id in ids)

        stage_1_positions = (
            current_positions[0],
            current_positions[1],
            args.target_2,
            current_positions[3],
        )
        stage_2_positions = (
            args.return_0,
            current_positions[1],
            args.target_2,
            args.return_3,
        )
        stage_3_positions = (
            args.return_0,
            args.target_1,
            args.target_2,
            args.return_3,
        )

        print(f"Device         : {args.device}")
        print(f"Baudrate       : {args.baudrate}")
        print(f"Timeout        : {args.timeout}")
        print(f"Servo IDs      : {ids}")
        print(f"Current pos    : {current_positions}")
        print(f"Target 1 / 2   : ({args.target_1}, {args.target_2})")
        print(f"Return 0 / 3   : ({args.return_0}, {args.return_3})")
        print(f"Speeds         : {speeds}")
        print(f"Return03 ratio : {args.return03_ratio}")
        print(f"Delay ratio    : {args.delay_ratio}")
        print(f"Poll interval  : {args.poll_interval}")
        print(f"Max wait       : {args.max_wait}")
        print(f"Preview        : {args.preview}")
        print(f"Stage 1 pos    : {stage_1_positions}")
        print(f"Stage 2 pos    : {stage_2_positions}")
        print(f"Stage 3 pos    : {stage_3_positions}")

        if args.preview:
            return 0

        stage_1_packet = build_sync_packet(ids, stage_1_positions, speeds)
        stage_1_sent = write_packet(ser, stage_1_packet)
        print(f"Stage 1 packet : {stage_1_packet.hex(' ')}")
        print(f"Stage 1 sent   : {stage_1_sent}")
        print("Servo 2 started. Waiting for 25% and 68% trigger points...")

        started = time.monotonic()
        stage_2_done = False
        stage_3_done = False
        while True:
            current_2 = read_position(ser, ids[2])
            print(f"Servo 2 pos    : {current_2}")

            if (not stage_2_done) and crossed_ratio(current_positions[2], current_2, args.target_2, args.return03_ratio):
                stage_2_packet = build_sync_packet(ids, stage_2_positions, speeds)
                stage_2_sent = write_packet(ser, stage_2_packet)
                print("Servo 2 reached the 25% trigger; starting servo 0 and 3 return now.")
                print(f"Stage 2 packet : {stage_2_packet.hex(' ')}")
                print(f"Stage 2 sent   : {stage_2_sent}")
                stage_2_done = True

            if (not stage_3_done) and crossed_ratio(current_positions[2], current_2, args.target_2, args.delay_ratio):
                stage_3_packet = build_sync_packet(ids, stage_3_positions, speeds)
                stage_3_sent = write_packet(ser, stage_3_packet)
                print("Servo 2 reached the configured delay ratio; starting servo 1 now.")
                print(f"Stage 3 packet : {stage_3_packet.hex(' ')}")
                print(f"Stage 3 sent   : {stage_3_sent}")
                stage_3_done = True
                break

            if (time.monotonic() - started) >= args.max_wait:
                if not stage_2_done:
                    stage_2_packet = build_sync_packet(ids, stage_2_positions, speeds)
                    stage_2_sent = write_packet(ser, stage_2_packet)
                    print("Max wait reached; forcing servo 0 and 3 return now.")
                    print(f"Stage 2 packet : {stage_2_packet.hex(' ')}")
                    print(f"Stage 2 sent   : {stage_2_sent}")
                    stage_2_done = True

                if not stage_3_done:
                    stage_3_packet = build_sync_packet(ids, stage_3_positions, speeds)
                    stage_3_sent = write_packet(ser, stage_3_packet)
                    print("Max wait reached; forcing servo 1 start now.")
                    print(f"Stage 3 packet : {stage_3_packet.hex(' ')}")
                    print(f"Stage 3 sent   : {stage_3_sent}")
                    stage_3_done = True
                break

            time.sleep(args.poll_interval)

        print("Sleep motion command finished.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
