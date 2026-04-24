#!/usr/bin/env python3

from __future__ import annotations

import argparse
import time

import serial

from bus_servo_protocol import (
    Address,
    TORQUE_OFF,
    TORQUE_ON,
    build_ping_packet,
    build_read_packet,
    build_sync_move_packet,
    build_torque_packet,
    parse_status_packet,
    unpack_u16,
)
from send_uart1_servo_cmd import DEFAULT_BAUDRATE, DEFAULT_DEVICE, DEFAULT_TIMEOUT, read_status_response


DEFAULT_SERVO_IDS = (0, 1, 2, 3)
DEFAULT_SPEED = 1000
DEFAULT_RUN_TIME = 0
DEFAULT_CENTER = 2048
STEPS_PER_TURN = 4096
DEGREES_PER_TURN = 360.0


def parse_args():
    parser = argparse.ArgumentParser(
        description="Convenience controller for 4 bus servos on RDK X5 UART1"
    )
    parser.add_argument("--device", default=DEFAULT_DEVICE, help="UART device path")
    parser.add_argument("--baudrate", type=int, default=DEFAULT_BAUDRATE, help="UART baudrate")
    parser.add_argument("--timeout", type=float, default=DEFAULT_TIMEOUT, help="UART read timeout in seconds")
    parser.add_argument(
        "--ids",
        nargs=4,
        type=int,
        default=DEFAULT_SERVO_IDS,
        metavar=("ID0", "ID1", "ID2", "ID3"),
        help="Servo ids for this 4-servo group",
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("ping-all", help="Ping the 4 configured servos")
    subparsers.add_parser("read-pos-all", help="Read current position of the 4 configured servos")

    parser_torque = subparsers.add_parser("torque", help="Turn torque on/off for all 4 servos")
    parser_torque.add_argument("mode", choices=("on", "off"))

    parser_center = subparsers.add_parser("center", help="Move all 4 servos to center position")
    parser_center.add_argument("--speed", type=int, default=DEFAULT_SPEED)
    parser_center.add_argument(
        "--speeds",
        nargs=4,
        type=int,
        metavar=("S0", "S1", "S2", "S3"),
        help="Optional per-servo speeds for servo 0/1/2/3",
    )
    parser_center.add_argument("--time", type=int, default=DEFAULT_RUN_TIME, dest="run_time")
    parser_center.add_argument("--position", type=int, default=DEFAULT_CENTER)

    parser_all = subparsers.add_parser("all", help="Move all 4 servos to the same position")
    parser_all.add_argument("position", type=int)
    parser_all.add_argument("--speed", type=int, default=DEFAULT_SPEED)
    parser_all.add_argument(
        "--speeds",
        nargs=4,
        type=int,
        metavar=("S0", "S1", "S2", "S3"),
        help="Optional per-servo speeds for servo 0/1/2/3",
    )
    parser_all.add_argument("--time", type=int, default=DEFAULT_RUN_TIME, dest="run_time")

    parser_pose = subparsers.add_parser("pose", help="Move 4 servos to 4 independent positions")
    parser_pose.add_argument("p0", type=int)
    parser_pose.add_argument("p1", type=int)
    parser_pose.add_argument("p2", type=int)
    parser_pose.add_argument("p3", type=int)
    parser_pose.add_argument("--speed", type=int, default=DEFAULT_SPEED)
    parser_pose.add_argument(
        "--speeds",
        nargs=4,
        type=int,
        metavar=("S0", "S1", "S2", "S3"),
        help="Optional per-servo speeds for servo 0/1/2/3",
    )
    parser_pose.add_argument("--time", type=int, default=DEFAULT_RUN_TIME, dest="run_time")

    parser_deg_all = subparsers.add_parser("deg-all", help="Move all 4 servos to the same absolute angle")
    parser_deg_all.add_argument("degrees", type=float, help="Absolute angle in degrees, 0-360")
    parser_deg_all.add_argument("--speed", type=int, default=DEFAULT_SPEED)
    parser_deg_all.add_argument("--time", type=int, default=DEFAULT_RUN_TIME, dest="run_time")

    return parser.parse_args()


def open_serial(args):
    return serial.Serial(args.device, args.baudrate, timeout=args.timeout)


def write_packet(ser: serial.Serial, packet: bytes) -> int:
    ser.reset_input_buffer()
    sent = ser.write(packet)
    ser.flush()
    return sent


def ping_one(ser: serial.Serial, servo_id: int) -> None:
    packet = build_ping_packet(servo_id)
    sent = write_packet(ser, packet)
    response = read_status_response(ser)
    status = parse_status_packet(response)
    print(f"Ping ID     : {servo_id}")
    print(f"Packet      : {packet.hex(' ')}")
    print(f"Sent bytes  : {sent}")
    print(f"Reply       : {response.hex(' ')}")
    print(f"Reply Error : 0x{status.error:02X}")
    print("")


def read_position(ser: serial.Serial, servo_id: int) -> None:
    packet = build_read_packet(servo_id, Address.CURRENT_POSITION, 2)
    sent = write_packet(ser, packet)
    response = read_status_response(ser)
    status = parse_status_packet(response)
    position = unpack_u16(status.parameters)
    print(f"Read ID     : {servo_id}")
    print(f"Packet      : {packet.hex(' ')}")
    print(f"Sent bytes  : {sent}")
    print(f"Reply       : {response.hex(' ')}")
    print(f"Position    : {position}")
    print("")


def set_torque_all(ser: serial.Serial, ids: tuple[int, int, int, int], mode: str) -> None:
    torque_value = TORQUE_ON if mode == "on" else TORQUE_OFF
    for servo_id in ids:
        packet = build_torque_packet(servo_id, torque_value)
        sent = write_packet(ser, packet)
        response = read_status_response(ser)
        status = parse_status_packet(response)
        print(f"Torque ID   : {servo_id}")
        print(f"Packet      : {packet.hex(' ')}")
        print(f"Sent bytes  : {sent}")
        print(f"Reply       : {response.hex(' ')}")
        print(f"Reply Error : 0x{status.error:02X}")
        print("")


def move_group(
    ser: serial.Serial,
    ids: tuple[int, int, int, int],
    positions: tuple[int, int, int, int],
    run_time: int,
    speeds: tuple[int, int, int, int],
) -> None:
    packet = build_sync_move_packet(
        (servo_id, position, run_time, speed)
        for servo_id, position, speed in zip(ids, positions, speeds)
    )
    sent = write_packet(ser, packet)
    print(f"Packet      : {packet.hex(' ')}")
    print(f"Sent bytes  : {sent}")
    print(f"Servo IDs   : {ids}")
    print(f"Positions   : {positions}")
    print(f"Run time    : {run_time}")
    print(f"Speeds      : {speeds}")


def degrees_to_steps(degrees: float) -> int:
    if not 0.0 <= degrees <= DEGREES_PER_TURN:
        raise ValueError(f"degrees out of range: {degrees} (expected 0-360)")
    return round(degrees / DEGREES_PER_TURN * STEPS_PER_TURN)


def resolve_speeds(args) -> tuple[int, int, int, int]:
    if getattr(args, "speeds", None):
        return tuple(args.speeds)
    return (args.speed, args.speed, args.speed, args.speed)


def main() -> int:
    args = parse_args()
    ids = tuple(args.ids)

    print(f"Device      : {args.device}")
    print(f"Baudrate    : {args.baudrate}")
    print(f"Timeout     : {args.timeout}")
    print(f"Servo IDs   : {ids}")
    print(f"Command     : {args.command}")

    with open_serial(args) as ser:
        if args.command == "ping-all":
            for servo_id in ids:
                ping_one(ser, servo_id)
            return 0

        if args.command == "read-pos-all":
            for servo_id in ids:
                read_position(ser, servo_id)
            return 0

        if args.command == "torque":
            set_torque_all(ser, ids, args.mode)
            return 0

        if args.command == "center":
            positions = (args.position, args.position, args.position, args.position)
            move_group(ser, ids, positions, args.run_time, resolve_speeds(args))
            return 0

        if args.command == "all":
            positions = (args.position, args.position, args.position, args.position)
            move_group(ser, ids, positions, args.run_time, resolve_speeds(args))
            return 0

        if args.command == "pose":
            positions = (args.p0, args.p1, args.p2, args.p3)
            move_group(ser, ids, positions, args.run_time, resolve_speeds(args))
            return 0

        if args.command == "deg-all":
            position = degrees_to_steps(args.degrees)
            positions = (position, position, position, position)
            move_group(ser, ids, positions, args.run_time, resolve_speeds(args))
            return 0

    raise ValueError(f"unsupported command: {args.command}")


if __name__ == "__main__":
    raise SystemExit(main())
