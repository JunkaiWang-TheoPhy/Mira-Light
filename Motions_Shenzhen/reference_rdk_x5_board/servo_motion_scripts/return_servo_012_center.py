#!/usr/bin/env python3

from __future__ import annotations

import argparse

import serial

from bus_servo_protocol import build_action_packet, build_reg_move_packet, parse_status_packet
from send_uart1_servo_cmd import DEFAULT_BAUDRATE, DEFAULT_DEVICE, DEFAULT_TIMEOUT, read_status_response


DEFAULT_TARGET = 2048
DEFAULT_SPEED_SERVO0 = 800
DEFAULT_SPEED_SERVO1 = 700
DEFAULT_SPEED_SERVO2 = 700
DEFAULT_RUN_TIME = 0


def parse_args():
    parser = argparse.ArgumentParser(
        description="Return servo 0/1/2 to position 2048 using the known speed rule"
    )
    parser.add_argument("--device", default=DEFAULT_DEVICE, help="UART device path")
    parser.add_argument("--baudrate", type=int, default=DEFAULT_BAUDRATE, help="UART baudrate")
    parser.add_argument("--timeout", type=float, default=DEFAULT_TIMEOUT, help="UART read timeout in seconds")
    parser.add_argument("--target", type=int, default=DEFAULT_TARGET, help="Target position for servo 0/1/2")
    parser.add_argument("--time", type=int, default=DEFAULT_RUN_TIME, dest="run_time", help="Run time value")
    parser.add_argument("--speed0", type=int, default=DEFAULT_SPEED_SERVO0, help="Speed for servo 0")
    parser.add_argument("--speed1", type=int, default=DEFAULT_SPEED_SERVO1, help="Speed for servo 1")
    parser.add_argument("--speed2", type=int, default=DEFAULT_SPEED_SERVO2, help="Speed for servo 2")
    return parser.parse_args()


def write_packet(ser: serial.Serial, packet: bytes) -> int:
    ser.reset_input_buffer()
    sent = ser.write(packet)
    ser.flush()
    return sent


def send_reg_move(ser: serial.Serial, servo_id: int, target: int, run_time: int, speed: int) -> None:
    packet = build_reg_move_packet(servo_id, target, run_time, speed)
    sent = write_packet(ser, packet)
    response = read_status_response(ser)
    status = parse_status_packet(response)
    print(f"Servo ID    : {servo_id}")
    print(f"Packet      : {packet.hex(' ')}")
    print(f"Sent bytes  : {sent}")
    print(f"Reply       : {response.hex(' ')}")
    print(f"Reply Error : 0x{status.error:02X}")
    print("")


def main() -> int:
    args = parse_args()

    print(f"Device      : {args.device}")
    print(f"Baudrate    : {args.baudrate}")
    print(f"Timeout     : {args.timeout}")
    print(f"Target      : {args.target}")
    print(f"Run time    : {args.run_time}")
    print(f"Speed map   : 0->{args.speed0}, 1->{args.speed1}, 2->{args.speed2}")

    with serial.Serial(args.device, args.baudrate, timeout=args.timeout) as ser:
        send_reg_move(ser, 0, args.target, args.run_time, args.speed0)
        send_reg_move(ser, 1, args.target, args.run_time, args.speed1)
        send_reg_move(ser, 2, args.target, args.run_time, args.speed2)

        action_packet = build_action_packet()
        sent = write_packet(ser, action_packet)
        print("ACTION")
        print(f"Packet      : {action_packet.hex(' ')}")
        print(f"Sent bytes  : {sent}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
