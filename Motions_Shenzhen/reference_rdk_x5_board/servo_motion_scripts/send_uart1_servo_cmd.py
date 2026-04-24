#!/usr/bin/env python3

from __future__ import annotations

import argparse
import time
import serial

from bus_servo_protocol import (
    Address,
    BROADCAST_ID,
    TORQUE_CALIBRATE_CURRENT_POSITION_TO_2048,
    TORQUE_DAMP,
    TORQUE_OFF,
    TORQUE_ON,
    build_acceleration_packet,
    build_action_packet,
    build_lock_packet,
    build_move_packet,
    build_ping_packet,
    build_read_packet,
    build_reg_move_packet,
    build_reset_packet,
    build_set_id_packet,
    build_sync_move_packet,
    build_torque_packet,
    build_write_packet,
    describe_status_bits,
    parse_status_packet,
    unpack_s16,
    unpack_u16,
)


DEFAULT_DEVICE = "/dev/ttyS1"
DEFAULT_BAUDRATE = 1000000
DEFAULT_TIMEOUT = 0.2


def parse_args():
    parser = argparse.ArgumentParser(
        description="Send direct bus-servo commands from RDK X5 over UART1 (/dev/ttyS1)"
    )
    parser.add_argument("--device", default=DEFAULT_DEVICE, help="UART device path")
    parser.add_argument("--baudrate", type=int, default=DEFAULT_BAUDRATE, help="UART baudrate")
    parser.add_argument("--timeout", type=float, default=DEFAULT_TIMEOUT, help="UART read timeout in seconds")
    parser.add_argument(
        "--no-reply",
        action="store_true",
        help="Do not wait for a status reply after sending a packet",
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    parser_ping = subparsers.add_parser("ping", help="Ping a servo and print its status reply")
    parser_ping.add_argument("servo_id", type=int)

    parser_read = subparsers.add_parser("read", help="Read raw bytes from a servo register address")
    parser_read.add_argument("servo_id", type=int)
    parser_read.add_argument("address", type=parse_int)
    parser_read.add_argument("size", type=int)
    parser_read.add_argument(
        "--decode",
        choices=("u8", "u16", "s16", "position", "speed", "load", "voltage", "temperature", "status", "moving"),
        help="Decode returned bytes as a known value type",
    )

    parser_read_pos = subparsers.add_parser("read-pos", help="Read current position")
    parser_read_pos.add_argument("servo_id", type=int)

    parser_move = subparsers.add_parser("move", help="Move one servo in position mode")
    parser_move.add_argument("servo_id", type=int)
    parser_move.add_argument("position", type=int, help="Target position in steps")
    parser_move.add_argument("--time", type=int, default=0, dest="run_time", help="Run time, 0-65535")
    parser_move.add_argument("--speed", type=int, default=0, help="Run speed in steps/s")
    parser_move.add_argument("--accel", type=int, help="Optional acceleration value written to 0x29 first")

    parser_reg_move = subparsers.add_parser("reg-move", help="Stage one move with REG WRITE, do not execute yet")
    parser_reg_move.add_argument("servo_id", type=int)
    parser_reg_move.add_argument("position", type=int)
    parser_reg_move.add_argument("--time", type=int, default=0, dest="run_time")
    parser_reg_move.add_argument("--speed", type=int, default=0)

    subparsers.add_parser("action", help="Execute staged REG WRITE moves using broadcast ACTION")

    parser_sync_move = subparsers.add_parser(
        "sync-move",
        help="Broadcast one SYNC WRITE move. Each item is id:position[:time[:speed]]",
    )
    parser_sync_move.add_argument("items", nargs="+")

    parser_torque = subparsers.add_parser("torque", help="Control torque output")
    parser_torque.add_argument("servo_id", type=int)
    parser_torque.add_argument("mode", choices=("on", "off", "damp", "calibrate"))

    parser_set_id = subparsers.add_parser("set-id", help="Change servo ID")
    parser_set_id.add_argument("current_id", type=int)
    parser_set_id.add_argument("new_id", type=int)
    parser_set_id.add_argument(
        "--persistent",
        action="store_true",
        help="Temporarily open the EEPROM lock (0x37=0) before writing ID so the new ID is saved after power off",
    )

    parser_write = subparsers.add_parser("write", help="Write raw bytes to one start address")
    parser_write.add_argument("servo_id", type=int)
    parser_write.add_argument("address", type=parse_int)
    parser_write.add_argument("values", nargs="+", type=parse_int, help="Byte values such as 1 255 0x2A")

    parser_reset = subparsers.add_parser("reset", help="Reset one servo")
    parser_reset.add_argument("servo_id", type=int)

    parser_raw_hex = subparsers.add_parser("raw-hex", help="Send one raw hex packet, for example 'FF FF 01 02 01 FB'")
    parser_raw_hex.add_argument("hex_bytes", help="Space-separated or compact hex bytes")

    return parser.parse_args()


def parse_int(text: str) -> int:
    return int(text, 0)


def parse_hex_bytes(text: str) -> bytes:
    cleaned = text.replace(" ", "").replace(":", "").replace("-", "")
    if len(cleaned) % 2 != 0:
        raise ValueError(f"hex string must contain an even number of digits: {text}")
    try:
        return bytes.fromhex(cleaned)
    except ValueError as exc:
        raise ValueError(f"invalid hex string: {text}") from exc


def open_serial(args):
    return serial.Serial(args.device, args.baudrate, timeout=args.timeout)


def write_packet(ser: serial.Serial, packet: bytes) -> int:
    ser.reset_input_buffer()
    sent = ser.write(packet)
    ser.flush()
    return sent


def read_status_response(ser: serial.Serial) -> bytes:
    deadline = time.monotonic() + ser.timeout
    header = bytearray()
    observed = bytearray()
    while time.monotonic() < deadline:
        chunk = ser.read(1)
        if not chunk:
            continue
        observed.extend(chunk)
        header.extend(chunk)
        if len(header) > 2:
            del header[:-2]
        if bytes(header) == b"\xFF\xFF":
            break
    else:
        tail = ser.read(ser.in_waiting or 0)
        if tail:
            observed.extend(tail)
        if observed:
            raise TimeoutError(
                f"timed out waiting for servo response header; observed bytes: {observed.hex(' ')}"
            )
        raise TimeoutError("timed out waiting for servo response header; observed bytes: <none>")

    prefix = ser.read(3)
    if len(prefix) != 3:
        partial_prefix = bytes((0xFF, 0xFF)) + prefix
        raise TimeoutError(
            f"timed out while reading servo response prefix; got: {partial_prefix.hex(' ')}"
        )

    length = prefix[1]
    remaining = max(length - 1, 0)
    tail = ser.read(remaining)
    if len(tail) != remaining:
        partial = bytes((0xFF, 0xFF)) + prefix + tail
        raise TimeoutError(
            f"timed out while reading servo response tail; got: {partial.hex(' ')}"
        )

    return bytes((0xFF, 0xFF)) + prefix + tail


def maybe_print_status_reply(ser: serial.Serial, expect_reply: bool, response_label: str = "Reply") -> None:
    if not expect_reply:
        print(f"{response_label:<12}: skipped (--no-reply or command has no status reply)")
        return

    response = read_status_response(ser)
    packet = parse_status_packet(response)
    print(f"{response_label:<12}: {response.hex(' ')}")
    print(f"Reply ID    : {packet.servo_id}")
    print(f"Reply Error : 0x{packet.error:02X}")
    print(f"Reply Param : {packet.parameters.hex(' ')}")
    if packet.error:
        print(f"Reply Flags : {', '.join(describe_status_bits(packet.error))}")


def decode_value(parameters: bytes, decode: str | None) -> str:
    if decode is None:
        return parameters.hex(" ")
    if decode == "u8":
        require_size(parameters, 1, decode)
        return str(parameters[0])
    if decode in {"u16", "position", "voltage"}:
        require_size(parameters, 2 if decode != "voltage" else 1, decode)
        if decode == "voltage":
            return f"{parameters[0] / 10:.1f} V"
        return str(unpack_u16(parameters))
    if decode in {"s16", "speed", "load"}:
        require_size(parameters, 2, decode)
        return str(unpack_s16(parameters))
    if decode == "temperature":
        require_size(parameters, 1, decode)
        return f"{parameters[0]} C"
    if decode == "status":
        require_size(parameters, 1, decode)
        return ", ".join(describe_status_bits(parameters[0]))
    if decode == "moving":
        require_size(parameters, 1, decode)
        return "moving" if parameters[0] else "stopped"
    raise ValueError(f"unsupported decode type: {decode}")


def require_size(parameters: bytes, expected: int, decode: str) -> None:
    if len(parameters) != expected:
        raise ValueError(f"{decode} decode expects {expected} bytes, got {len(parameters)}")


def maybe_write_acceleration(ser: serial.Serial, servo_id: int, accel: int | None) -> None:
    if accel is None:
        return
    packet = build_acceleration_packet(servo_id, accel)
    sent = write_packet(ser, packet)
    print(f"Accel Write : {packet.hex(' ')}")
    print(f"Accel Bytes : {sent}")
    maybe_print_status_reply(ser, expect_reply=servo_id != BROADCAST_ID, response_label="Accel Reply")


def parse_sync_move_item(text: str) -> tuple[int, int, int, int]:
    parts = text.split(":")
    if len(parts) < 2 or len(parts) > 4:
        raise ValueError(f"invalid sync-move item: {text}")
    servo_id = parse_int(parts[0])
    position = int(parts[1])
    run_time = int(parts[2]) if len(parts) >= 3 else 0
    speed = int(parts[3]) if len(parts) >= 4 else 0
    return servo_id, position, run_time, speed


def send_and_maybe_read(ser: serial.Serial, packet: bytes, expect_reply: bool) -> int:
    sent = write_packet(ser, packet)
    print(f"Packet      : {packet.hex(' ')}")
    print(f"Sent bytes  : {sent}")
    maybe_print_status_reply(ser, expect_reply=expect_reply)
    return sent


def run_command(args) -> int:
    with open_serial(args) as ser:
        if args.command == "ping":
            packet = build_ping_packet(args.servo_id)
            send_and_maybe_read(ser, packet, expect_reply=not args.no_reply)
            return 0

        if args.command == "read":
            packet = build_read_packet(args.servo_id, args.address, args.size)
            sent = write_packet(ser, packet)
            print(f"Packet      : {packet.hex(' ')}")
            print(f"Sent bytes  : {sent}")
            if args.no_reply:
                print("Reply       : skipped (--no-reply)")
                return 0
            response = read_status_response(ser)
            status = parse_status_packet(response)
            print(f"Reply       : {response.hex(' ')}")
            print(f"Reply ID    : {status.servo_id}")
            print(f"Reply Error : 0x{status.error:02X}")
            print(f"Reply Param : {status.parameters.hex(' ')}")
            print(f"Decoded     : {decode_value(status.parameters, args.decode)}")
            return 0

        if args.command == "read-pos":
            packet = build_read_packet(args.servo_id, Address.CURRENT_POSITION, 2)
            sent = write_packet(ser, packet)
            print(f"Packet      : {packet.hex(' ')}")
            print(f"Sent bytes  : {sent}")
            if args.no_reply:
                print("Reply       : skipped (--no-reply)")
                return 0
            response = read_status_response(ser)
            status = parse_status_packet(response)
            print(f"Reply       : {response.hex(' ')}")
            print(f"Position    : {unpack_u16(status.parameters)}")
            return 0

        if args.command == "move":
            maybe_write_acceleration(ser, args.servo_id, args.accel)
            packet = build_move_packet(args.servo_id, args.position, args.run_time, args.speed)
            send_and_maybe_read(ser, packet, expect_reply=(args.servo_id != BROADCAST_ID) and (not args.no_reply))
            return 0

        if args.command == "reg-move":
            packet = build_reg_move_packet(args.servo_id, args.position, args.run_time, args.speed)
            send_and_maybe_read(ser, packet, expect_reply=(args.servo_id != BROADCAST_ID) and (not args.no_reply))
            return 0

        if args.command == "action":
            packet = build_action_packet()
            send_and_maybe_read(ser, packet, expect_reply=False)
            return 0

        if args.command == "sync-move":
            items = [parse_sync_move_item(item) for item in args.items]
            packet = build_sync_move_packet(items)
            send_and_maybe_read(ser, packet, expect_reply=False)
            return 0

        if args.command == "torque":
            mode_map = {
                "off": TORQUE_OFF,
                "on": TORQUE_ON,
                "damp": TORQUE_DAMP,
                "calibrate": TORQUE_CALIBRATE_CURRENT_POSITION_TO_2048,
            }
            packet = build_torque_packet(args.servo_id, mode_map[args.mode])
            send_and_maybe_read(ser, packet, expect_reply=(args.servo_id != BROADCAST_ID) and (not args.no_reply))
            return 0

        if args.command == "set-id":
            if args.persistent:
                packet = build_lock_packet(args.current_id, locked=False)
                send_and_maybe_read(ser, packet, expect_reply=(args.current_id != BROADCAST_ID) and (not args.no_reply))

            packet = build_set_id_packet(args.current_id, args.new_id)
            send_and_maybe_read(ser, packet, expect_reply=(args.current_id != BROADCAST_ID) and (not args.no_reply))

            if args.persistent:
                packet = build_lock_packet(args.new_id, locked=True)
                send_and_maybe_read(ser, packet, expect_reply=(args.new_id != BROADCAST_ID) and (not args.no_reply))
            return 0

        if args.command == "write":
            packet = build_write_packet(args.servo_id, args.address, bytes(args.values))
            send_and_maybe_read(ser, packet, expect_reply=(args.servo_id != BROADCAST_ID) and (not args.no_reply))
            return 0

        if args.command == "reset":
            packet = build_reset_packet(args.servo_id)
            send_and_maybe_read(ser, packet, expect_reply=(args.servo_id != BROADCAST_ID) and (not args.no_reply))
            return 0

        if args.command == "raw-hex":
            packet = parse_hex_bytes(args.hex_bytes)
            send_and_maybe_read(ser, packet, expect_reply=not args.no_reply)
            return 0

    raise ValueError(f"unsupported command: {args.command}")


def main() -> int:
    args = parse_args()
    print(f"Device      : {args.device}")
    print(f"Baudrate    : {args.baudrate}")
    print(f"Timeout     : {args.timeout}")
    print(f"Command     : {args.command}")
    return run_command(args)


if __name__ == "__main__":
    raise SystemExit(main())
