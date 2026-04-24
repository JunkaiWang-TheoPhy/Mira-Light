#!/usr/bin/env python3

from __future__ import annotations

import argparse
import time

import serial

from bus_servo_protocol import Address, build_move_packet, build_read_packet, parse_status_packet, unpack_u16
from send_uart1_servo_cmd import DEFAULT_BAUDRATE, DEFAULT_DEVICE, DEFAULT_TIMEOUT, read_status_response


DEFAULT_SERVO_ID = 3
DEFAULT_LEFT_TARGET = 2100
DEFAULT_RIGHT_TARGET = 2000
DEFAULT_RETURN_TARGET = 2048
DEFAULT_SPEED = 100
DEFAULT_RUN_TIME = 0
DEFAULT_PAUSE = 0.0
DEFAULT_CYCLES = 3
DEFAULT_START = "left"
DEFAULT_TOLERANCE = 20
DEFAULT_SETTLE_POLLS = 3
DEFAULT_WAIT_MARGIN = 2.0
DEFAULT_MAX_SEGMENT_WAIT = 20.0


def parse_args():
    parser = argparse.ArgumentParser(
        description="Shake-head motion for servo 3 between two targets, then return to 2048"
    )
    parser.add_argument("--device", default=DEFAULT_DEVICE, help="UART device path")
    parser.add_argument("--baudrate", type=int, default=DEFAULT_BAUDRATE, help="UART baudrate")
    parser.add_argument("--timeout", type=float, default=DEFAULT_TIMEOUT, help="UART timeout")
    parser.add_argument("--servo-id", type=int, default=DEFAULT_SERVO_ID, help="Servo id to shake")
    parser.add_argument("--left", type=int, default=DEFAULT_LEFT_TARGET, help="Left shake target")
    parser.add_argument("--right", type=int, default=DEFAULT_RIGHT_TARGET, help="Right shake target")
    parser.add_argument("--target-left", type=int, help="Alias for --left")
    parser.add_argument("--target-right", type=int, help="Alias for --right")
    parser.add_argument("--return-target", type=int, default=DEFAULT_RETURN_TARGET, help="Final return target")
    parser.add_argument("--speed", type=int, default=DEFAULT_SPEED, help="Move speed")
    parser.add_argument("--time", type=int, default=DEFAULT_RUN_TIME, dest="run_time", help="Run time value")
    parser.add_argument("--pause", type=float, default=DEFAULT_PAUSE, help="Extra pause after each move reaches target")
    parser.add_argument("--cycles", type=int, default=DEFAULT_CYCLES, help="Number of left-right shake cycles")
    parser.add_argument("--start", choices=("left", "right"), default=DEFAULT_START, help="First shake target")
    parser.add_argument("--tolerance", type=int, default=DEFAULT_TOLERANCE, help="Position error accepted as reached")
    parser.add_argument("--settle-polls", type=int, default=DEFAULT_SETTLE_POLLS, help="Consecutive reached polls before continuing")
    parser.add_argument("--wait-margin", type=float, default=DEFAULT_WAIT_MARGIN, help="Extra seconds added to estimated move time")
    parser.add_argument("--max-segment-wait", type=float, default=DEFAULT_MAX_SEGMENT_WAIT, help="Fallback max wait for one move")
    parser.add_argument("--preview", action="store_true", help="Print packets without sending them")
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


def estimate_wait_seconds(start: int, target: int, run_time: int, speed: int, wait_margin: float, max_segment_wait: float) -> float:
    if run_time > 0:
        return max(run_time / 1000.0 + wait_margin, wait_margin)
    if speed > 0:
        return min(abs(target - start) / speed + wait_margin, max_segment_wait)
    return max_segment_wait


def wait_until_reached(
    ser: serial.Serial,
    servo_id: int,
    target: int,
    timeout_s: float,
    tolerance: int,
    settle_polls: int,
) -> int:
    stable_count = 0
    last_position = target
    deadline = time.monotonic() + timeout_s

    while True:
        position = read_position(ser, servo_id)
        last_position = position
        error = abs(position - target)
        print(f"Position    : servo {servo_id} = {position} (target={target}, error={error})")

        if error <= tolerance:
            stable_count += 1
            if stable_count >= settle_polls:
                print("Reached     : yes")
                return position
        else:
            stable_count = 0

        if time.monotonic() >= deadline:
            print("Reached     : timeout, continuing")
            return last_position

        time.sleep(0.1)


def move_and_print(
    ser: serial.Serial,
    servo_id: int,
    target: int,
    run_time: int,
    speed: int,
    tolerance: int,
    settle_polls: int,
    wait_margin: float,
    max_segment_wait: float,
) -> None:
    start = read_position(ser, servo_id)
    packet = build_move_packet(servo_id, target, run_time, speed)
    sent = write_packet(ser, packet)
    reply = read_status_response(ser)
    wait_s = estimate_wait_seconds(start, target, run_time, speed, wait_margin, max_segment_wait)
    print(f"Servo ID    : {servo_id}")
    print(f"Start       : {start}")
    print(f"Target      : {target}")
    print(f"Wait max    : {wait_s:.1f}s")
    print(f"Packet      : {packet.hex(' ')}")
    print(f"Sent bytes  : {sent}")
    print(f"Reply       : {reply.hex(' ')}")
    wait_until_reached(ser, servo_id, target, wait_s, tolerance, settle_polls)


def main() -> int:
    args = parse_args()
    if args.cycles < 1:
        raise ValueError(f"--cycles must be >= 1, got {args.cycles}")
    if args.pause < 0:
        raise ValueError(f"--pause must be >= 0, got {args.pause}")
    if args.settle_polls < 1:
        raise ValueError(f"--settle-polls must be >= 1, got {args.settle_polls}")

    if args.target_left is not None:
        args.left = args.target_left
    if args.target_right is not None:
        args.right = args.target_right

    first = args.left if args.start == "left" else args.right
    second = args.right if args.start == "left" else args.left
    targets = [target for _ in range(args.cycles) for target in (first, second)]
    targets.append(args.return_target)
    packets = [
        build_move_packet(args.servo_id, target, args.run_time, args.speed)
        for target in targets
    ]

    print(f"Device      : {args.device}")
    print(f"Baudrate    : {args.baudrate}")
    print(f"Timeout     : {args.timeout}")
    print(f"Servo ID    : {args.servo_id}")
    print(f"Left / Right: {args.left} / {args.right}")
    print(f"Order       : {first} -> {second}")
    print(f"Return      : {args.return_target}")
    print(f"Speed       : {args.speed}")
    print(f"Run time    : {args.run_time}")
    print(f"Pause       : {args.pause}")
    print(f"Tolerance   : {args.tolerance}")
    print(f"Settle polls: {args.settle_polls}")
    print(f"Wait margin : {args.wait_margin}")
    print(f"Max wait    : {args.max_segment_wait}")
    print(f"Cycles      : {args.cycles}")
    print(f"Start       : {args.start}")
    print(f"Preview     : {args.preview}")

    if args.preview:
        for target, packet in zip(targets, packets):
            print(f"Target {target}: {packet.hex(' ')}")
        return 0

    with serial.Serial(args.device, args.baudrate, timeout=args.timeout) as ser:
        for target in targets:
            move_and_print(
                ser,
                args.servo_id,
                target,
                args.run_time,
                args.speed,
                args.tolerance,
                args.settle_polls,
                args.wait_margin,
                args.max_segment_wait,
            )
            time.sleep(args.pause)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
