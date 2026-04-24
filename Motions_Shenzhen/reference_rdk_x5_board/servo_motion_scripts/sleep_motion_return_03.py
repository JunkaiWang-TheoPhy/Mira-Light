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
DEFAULT_POLL_INTERVAL = 0.03
DEFAULT_MAX_WAIT = 6.0
DEFAULT_RETURN_0 = 2048
DEFAULT_RETURN_3 = 2130
DEFAULT_RETURN_SPEEDS = (160, 160)
DEFAULT_HOLD_TIME = 0.5


def parse_args():
    parser = argparse.ArgumentParser(
        description="Sleep motion, then return servo 0 to 2048 and servo 3 to 2130"
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
        help="Per-servo speeds for servo 0/1/2/3 in the sleep motion",
    )
    parser.add_argument("--delay-ratio", type=float, default=DEFAULT_DELAY_RATIO, help="Start servo 1 when servo 2 reaches this fraction of travel toward target 2")
    parser.add_argument("--poll-interval", type=float, default=DEFAULT_POLL_INTERVAL, help="Polling interval while waiting for servo 2 progress")
    parser.add_argument("--max-wait", type=float, default=DEFAULT_MAX_WAIT, help="Maximum seconds to wait before forcing servo 1 to start")
    parser.add_argument("--hold-0", type=int, help="Optional fixed position for servo 0 during the sleep motion. Default is current position.")
    parser.add_argument("--hold-3", type=int, help="Optional fixed position for servo 3 during the sleep motion. Default is current position.")
    parser.add_argument("--return-0", type=int, default=DEFAULT_RETURN_0, help="Final return target for servo 0")
    parser.add_argument("--return-3", type=int, default=DEFAULT_RETURN_3, help="Final return target for servo 3")
    parser.add_argument(
        "--return-speeds",
        nargs=2,
        type=int,
        default=DEFAULT_RETURN_SPEEDS,
        metavar=("S0", "S3"),
        help="Return speeds for servo 0 and servo 3 in the final stage",
    )
    parser.add_argument("--hold-time", type=float, default=DEFAULT_HOLD_TIME, help="Pause after the sleep motion before returning servo 0 and 3")
    parser.add_argument("--preview", action="store_true", help="Print the three-stage plan without sending packets")
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
    return_speeds = tuple(args.return_speeds)

    if not 0.0 <= args.delay_ratio <= 1.0:
        raise ValueError(f"--delay-ratio must be in [0, 1], got {args.delay_ratio}")

    with serial.Serial(args.device, args.baudrate, timeout=args.timeout) as ser:
        current_positions = tuple(read_position(ser, servo_id) for servo_id in ids)
        hold_0 = args.hold_0 if args.hold_0 is not None else current_positions[0]
        hold_3 = args.hold_3 if args.hold_3 is not None else current_positions[3]

        stage_1_positions = (hold_0, current_positions[1], args.target_2, hold_3)
        stage_2_positions = (hold_0, args.target_1, args.target_2, hold_3)
        stage_3_positions = (args.return_0, args.target_1, args.target_2, args.return_3)
        stage_3_speeds = (return_speeds[0], speeds[1], speeds[2], return_speeds[1])

        print(f"Device         : {args.device}")
        print(f"Baudrate       : {args.baudrate}")
        print(f"Timeout        : {args.timeout}")
        print(f"Servo IDs      : {ids}")
        print(f"Current pos    : {current_positions}")
        print(f"Hold 0 / 3     : ({hold_0}, {hold_3})")
        print(f"Target 1 / 2   : ({args.target_1}, {args.target_2})")
        print(f"Speeds         : {speeds}")
        print(f"Delay ratio    : {args.delay_ratio}")
        print(f"Return 0 / 3   : ({args.return_0}, {args.return_3})")
        print(f"Return speeds  : {return_speeds}")
        print(f"Hold time      : {args.hold_time}")
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
        print("Servo 2 started. Waiting for servo 2 progress before starting servo 1...")

        started = time.monotonic()
        while True:
            current_2 = read_position(ser, ids[2])
            print(f"Servo 2 pos    : {current_2}")
            if crossed_ratio(current_positions[2], current_2, args.target_2, args.delay_ratio):
                print("Servo 2 reached the configured ratio; starting servo 1 now.")
                break
            if (time.monotonic() - started) >= args.max_wait:
                print("Max wait reached; starting servo 1 now.")
                break
            time.sleep(args.poll_interval)

        stage_2_packet = build_sync_packet(ids, stage_2_positions, speeds)
        stage_2_sent = write_packet(ser, stage_2_packet)
        print(f"Stage 2 packet : {stage_2_packet.hex(' ')}")
        print(f"Stage 2 sent   : {stage_2_sent}")

        if args.hold_time > 0:
            print("Holding sleep pose...")
            time.sleep(args.hold_time)

        stage_3_packet = build_sync_packet(ids, stage_3_positions, stage_3_speeds)
        stage_3_sent = write_packet(ser, stage_3_packet)
        print(f"Stage 3 packet : {stage_3_packet.hex(' ')}")
        print(f"Stage 3 sent   : {stage_3_sent}")
        print("Servo 0 returned to 2048 and servo 3 returned to 2130.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
