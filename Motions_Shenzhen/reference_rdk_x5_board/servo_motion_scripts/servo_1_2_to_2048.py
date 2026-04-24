#!/usr/bin/env python3

from __future__ import annotations

import argparse
import time

import serial

from bus_servo_protocol import build_move_packet, build_read_packet, parse_status_packet, unpack_u16
from send_uart1_servo_cmd import read_status_response


DEFAULT_DEVICE = "/dev/ttyS1"
DEFAULT_BAUDRATE = 1000000
DEFAULT_TIMEOUT = 0.3
FIRST_SERVO_ID = 1
SECOND_SERVO_ID = 2
DEFAULT_TARGET = 2048
DEFAULT_HALF_RATIO = 0.5
DEFAULT_FIRST_SPEED = 1000
DEFAULT_SECOND_SPEED = 1000
DEFAULT_POLL_INTERVAL = 0.03


def parse_args():
    parser = argparse.ArgumentParser(
        description="Return two servos to target in sequence: start second servo when first servo reaches halfway"
    )
    parser.add_argument("--device", default=DEFAULT_DEVICE, help="UART device path")
    parser.add_argument("--baudrate", type=int, default=DEFAULT_BAUDRATE, help="UART baudrate")
    parser.add_argument("--timeout", type=float, default=DEFAULT_TIMEOUT, help="UART timeout")
    parser.add_argument("--first-id", type=int, default=FIRST_SERVO_ID, help="First servo id to move")
    parser.add_argument("--second-id", type=int, default=SECOND_SERVO_ID, help="Second servo id to move after halfway")
    parser.add_argument("--target", type=int, default=DEFAULT_TARGET, help="Final target position")
    parser.add_argument(
        "--half-ratio",
        type=float,
        default=DEFAULT_HALF_RATIO,
        help="Start second servo when first servo reaches this fraction of travel toward target",
    )
    parser.add_argument("--first-speed", type=int, default=DEFAULT_FIRST_SPEED, help="Speed of first servo")
    parser.add_argument("--second-speed", type=int, default=DEFAULT_SECOND_SPEED, help="Speed of second servo")
    parser.add_argument(
        "--poll-interval",
        type=float,
        default=DEFAULT_POLL_INTERVAL,
        help="Polling interval in seconds while waiting for halfway point",
    )
    return parser.parse_args()


def write_packet(ser: serial.Serial, packet: bytes) -> int:
    ser.reset_input_buffer()
    sent = ser.write(packet)
    ser.flush()
    return sent


def read_position(ser: serial.Serial, servo_id: int) -> int:
    packet = build_read_packet(servo_id, 0x38, 2)
    write_packet(ser, packet)
    response = read_status_response(ser)
    status = parse_status_packet(response)
    return unpack_u16(status.parameters)


def move_and_consume_ack(ser: serial.Serial, servo_id: int, target: int, speed: int) -> tuple[bytes, int, bytes]:
    packet = build_move_packet(servo_id, target, 0, speed)
    sent = write_packet(ser, packet)
    response = read_status_response(ser)
    return packet, sent, response


def crossed_halfway(start_pos: int, current_pos: int, target: int, ratio: float) -> bool:
    threshold = start_pos + (target - start_pos) * ratio
    if target >= start_pos:
        return current_pos >= threshold
    return current_pos <= threshold


def main() -> int:
    args = parse_args()
    if not 0.0 < args.half_ratio < 1.0:
        raise ValueError(f"--half-ratio must be between 0 and 1, got {args.half_ratio}")

    with serial.Serial(args.device, args.baudrate, timeout=args.timeout) as ser:
        first_start = read_position(ser, args.first_id)
        second_start = read_position(ser, args.second_id)

        first_packet, first_sent, first_response = move_and_consume_ack(
            ser, args.first_id, args.target, args.first_speed
        )

        print(f"Device         : {args.device}")
        print(f"Baudrate       : {args.baudrate}")
        print(f"First servo    : {args.first_id}")
        print(f"Second servo   : {args.second_id}")
        print(f"Target         : {args.target}")
        print(f"Half ratio     : {args.half_ratio}")
        print(f"First start    : {first_start}")
        print(f"Second start   : {second_start}")
        print(f"First speed    : {args.first_speed}")
        print(f"Second speed   : {args.second_speed}")
        print(f"First packet   : {first_packet.hex(' ')}")
        print(f"First sent     : {first_sent}")
        print(f"First reply    : {first_response.hex(' ')}")
        print("Waiting for first servo to reach halfway...")

        while True:
            current_first = read_position(ser, args.first_id)
            print(f"First current  : {current_first}")
            if crossed_halfway(first_start, current_first, args.target, args.half_ratio):
                break
            time.sleep(args.poll_interval)

        second_packet, second_sent, second_response = move_and_consume_ack(
            ser, args.second_id, args.target, args.second_speed
        )
        print(f"Second packet  : {second_packet.hex(' ')}")
        print(f"Second sent    : {second_sent}")
        print(f"Second reply   : {second_response.hex(' ')}")
        print("Second servo started.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
