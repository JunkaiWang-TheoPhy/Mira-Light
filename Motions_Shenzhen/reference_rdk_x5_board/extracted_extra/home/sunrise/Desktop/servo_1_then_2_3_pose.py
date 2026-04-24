#!/usr/bin/env python3

from __future__ import annotations

import argparse
import time

import serial

from bus_servo_protocol import Address, build_move_packet, build_read_packet, build_sync_move_packet, parse_status_packet, unpack_u16
from send_uart1_servo_cmd import read_status_response


DEFAULT_DEVICE = "/dev/ttyS1"
DEFAULT_BAUDRATE = 1000000
DEFAULT_TIMEOUT = 0.3
DEFAULT_SERVO_1_ID = 1
DEFAULT_SERVO_2_ID = 2
DEFAULT_SERVO_3_ID = 3
DEFAULT_TARGET_1 = 2365
DEFAULT_TARGET_2 = 1050
DEFAULT_TARGET_3 = 2139
DEFAULT_SPEED_1 = 1000
DEFAULT_SPEED_23 = 1000
DEFAULT_TOLERANCE = 12
DEFAULT_POLL_INTERVAL = 0.03
DEFAULT_NEAR_THRESHOLD = 30
DEFAULT_STABLE_POLLS = 8
DEFAULT_MAX_WAIT = 6.0


def parse_args():
    parser = argparse.ArgumentParser(
        description="Move servo 1 first, then move servo 2 and 3 together after servo 1 reaches its target"
    )
    parser.add_argument("--device", default=DEFAULT_DEVICE, help="UART device path")
    parser.add_argument("--baudrate", type=int, default=DEFAULT_BAUDRATE, help="UART baudrate")
    parser.add_argument("--timeout", type=float, default=DEFAULT_TIMEOUT, help="UART timeout")
    parser.add_argument("--servo-1-id", type=int, default=DEFAULT_SERVO_1_ID)
    parser.add_argument("--servo-2-id", type=int, default=DEFAULT_SERVO_2_ID)
    parser.add_argument("--servo-3-id", type=int, default=DEFAULT_SERVO_3_ID)
    parser.add_argument("--target-1", type=int, default=DEFAULT_TARGET_1)
    parser.add_argument("--target-2", type=int, default=DEFAULT_TARGET_2)
    parser.add_argument("--target-3", type=int, default=DEFAULT_TARGET_3)
    parser.add_argument("--speed-1", type=int, default=DEFAULT_SPEED_1, help="Speed for servo 1")
    parser.add_argument("--speed-23", type=int, default=DEFAULT_SPEED_23, help="Speed for servo 2 and 3")
    parser.add_argument("--tolerance", type=int, default=DEFAULT_TOLERANCE, help="Acceptable final-position error in steps")
    parser.add_argument("--poll-interval", type=float, default=DEFAULT_POLL_INTERVAL, help="Polling interval while waiting for servo 1")
    parser.add_argument(
        "--near-threshold",
        type=int,
        default=DEFAULT_NEAR_THRESHOLD,
        help="If servo 1 stops changing and is this close to target, allow servo 2/3 to start",
    )
    parser.add_argument(
        "--stable-polls",
        type=int,
        default=DEFAULT_STABLE_POLLS,
        help="How many near-identical polls count as 'stopped'",
    )
    parser.add_argument(
        "--max-wait",
        type=float,
        default=DEFAULT_MAX_WAIT,
        help="Maximum seconds to wait for servo 1 before continuing anyway",
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


def move_and_consume_ack(ser: serial.Serial, servo_id: int, target: int, speed: int) -> tuple[bytes, int, bytes]:
    packet = build_move_packet(servo_id, target, 0, speed)
    sent = write_packet(ser, packet)
    response = read_status_response(ser)
    return packet, sent, response


def main() -> int:
    args = parse_args()

    with serial.Serial(args.device, args.baudrate, timeout=args.timeout) as ser:
        start_1 = read_position(ser, args.servo_1_id)
        start_2 = read_position(ser, args.servo_2_id)
        start_3 = read_position(ser, args.servo_3_id)

        packet_1, sent_1, reply_1 = move_and_consume_ack(
            ser, args.servo_1_id, args.target_1, args.speed_1
        )

        print(f"Device         : {args.device}")
        print(f"Baudrate       : {args.baudrate}")
        print(f"Timeout        : {args.timeout}")
        print(f"Servo 1        : {args.servo_1_id} -> {args.target_1}")
        print(f"Servo 2        : {args.servo_2_id} -> {args.target_2}")
        print(f"Servo 3        : {args.servo_3_id} -> {args.target_3}")
        print(f"Start 1        : {start_1}")
        print(f"Start 2        : {start_2}")
        print(f"Start 3        : {start_3}")
        print(f"Speed 1        : {args.speed_1}")
        print(f"Speed 23       : {args.speed_23}")
        print(f"Tolerance      : {args.tolerance}")
        print(f"Near threshold : {args.near_threshold}")
        print(f"Stable polls   : {args.stable_polls}")
        print(f"Max wait       : {args.max_wait}")
        print(f"Packet 1       : {packet_1.hex(' ')}")
        print(f"Sent 1         : {sent_1}")
        print(f"Reply 1        : {reply_1.hex(' ')}")
        print("Waiting for servo 1 to reach target...")

        wait_started = time.monotonic()
        stable_count = 0
        last_1 = None
        while True:
            current_1 = read_position(ser, args.servo_1_id)
            error = abs(current_1 - args.target_1)
            if last_1 is not None and current_1 == last_1:
                stable_count += 1
            else:
                stable_count = 0
            last_1 = current_1

            print(f"Current 1      : {current_1} (error={error}, stable={stable_count})")
            if error <= args.tolerance:
                print("Servo 1 reached target within tolerance.")
                break
            if error <= args.near_threshold and stable_count >= args.stable_polls:
                print("Servo 1 appears mechanically settled near target; continuing with servo 2 and 3.")
                break
            if (time.monotonic() - wait_started) >= args.max_wait:
                print("Servo 1 wait timed out; continuing with servo 2 and 3.")
                break
            time.sleep(args.poll_interval)

        packet_23 = build_sync_move_packet(
            (
                (args.servo_2_id, args.target_2, 0, args.speed_23),
                (args.servo_3_id, args.target_3, 0, args.speed_23),
            )
        )
        sent_23 = write_packet(ser, packet_23)
        print(f"Packet 23      : {packet_23.hex(' ')}")
        print(f"Sent 23        : {sent_23}")
        print("Servo 2 and 3 started.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
