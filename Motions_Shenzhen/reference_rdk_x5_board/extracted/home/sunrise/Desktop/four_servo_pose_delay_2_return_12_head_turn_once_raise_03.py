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
DEFAULT_HOLD_TIME = 1.0
DEFAULT_RETURN_TARGET_1 = 2150
DEFAULT_RETURN_TARGET_2 = 2048
DEFAULT_RETURN_SPEEDS = (120, 120)
DEFAULT_SETTLE_THRESHOLD = 20
DEFAULT_SETTLE_POLLS = 6
DEFAULT_SETTLE_WAIT = 3.0
DEFAULT_STABLE_DELTA = 2
DEFAULT_HEAD_LEFT = 2300
DEFAULT_HEAD_RIGHT = 1760
DEFAULT_HEAD_TURNS = 1
DEFAULT_HEAD_TIME_MS = 1200
DEFAULT_FINAL_HEAD = 2130
DEFAULT_POST_HEAD_PAUSE = 0.5
DEFAULT_FINAL_TARGET_0 = 2400
DEFAULT_FINAL_TARGET_1 = 2000
DEFAULT_FINAL_TARGET_3 = 2748
DEFAULT_FINAL_SPEEDS_03 = (120, 120)


def parse_args():
    parser = argparse.ArgumentParser(
        description="Run the delayed pose motion, return servo 1/2, turn servo 3 once, then slowly move servo 0/3"
    )
    parser.add_argument("--device", default=DEFAULT_DEVICE, help="UART device path")
    parser.add_argument("--baudrate", type=int, default=DEFAULT_BAUDRATE, help="UART baudrate")
    parser.add_argument("--timeout", type=float, default=DEFAULT_TIMEOUT, help="UART timeout")
    parser.add_argument("--ids", nargs=4, type=int, default=DEFAULT_IDS, metavar=("ID0", "ID1", "ID2", "ID3"), help="Servo ids in order (default: 0 1 2 3)")
    parser.add_argument("--targets", nargs=4, type=int, default=DEFAULT_TARGETS, metavar=("P0", "P1", "P2", "P3"), help="Target positions for servo 0/1/2/3 in the first motion")
    parser.add_argument("--speeds", nargs=4, type=int, default=DEFAULT_SPEEDS, metavar=("S0", "S1", "S2", "S3"), help="Per-servo speeds for the first motion")
    parser.add_argument("--delay-ratio", type=float, default=DEFAULT_DELAY_RATIO, help="Start servo 2 when servo 1 reaches this fraction of travel toward target 1")
    parser.add_argument("--poll-interval", type=float, default=DEFAULT_POLL_INTERVAL, help="Polling interval while waiting for progress and settle")
    parser.add_argument("--max-wait", type=float, default=DEFAULT_MAX_WAIT, help="Maximum seconds to wait before forcing servo 2 to start")
    parser.add_argument("--hold-time", type=float, default=DEFAULT_HOLD_TIME, help="Pause time after the first motion settles")
    parser.add_argument("--return-target-1", type=int, default=DEFAULT_RETURN_TARGET_1, help="Return target for servo 1")
    parser.add_argument("--return-target-2", type=int, default=DEFAULT_RETURN_TARGET_2, help="Return target for servo 2")
    parser.add_argument("--return-speeds", nargs=2, type=int, default=DEFAULT_RETURN_SPEEDS, metavar=("S1", "S2"), help="Return speeds for servo 1 and servo 2")
    parser.add_argument("--settle-threshold", type=int, default=DEFAULT_SETTLE_THRESHOLD, help="Position error treated as close enough while waiting for servo 1/2 to settle")
    parser.add_argument("--settle-polls", type=int, default=DEFAULT_SETTLE_POLLS, help="How many consecutive close-enough polls count as settled")
    parser.add_argument("--settle-wait", type=float, default=DEFAULT_SETTLE_WAIT, help="Maximum seconds to wait for servo 1/2 to settle after stage 2 starts")
    parser.add_argument("--stable-delta", type=int, default=DEFAULT_STABLE_DELTA, help="Treat a servo as stable when consecutive reads change by no more than this amount")
    parser.add_argument("--head-left", type=int, default=DEFAULT_HEAD_LEFT, help="Servo 3 left turn position")
    parser.add_argument("--head-right", type=int, default=DEFAULT_HEAD_RIGHT, help="Servo 3 right turn position")
    parser.add_argument("--head-turns", type=int, default=DEFAULT_HEAD_TURNS, help="How many full left-right turns servo 3 performs at the end")
    parser.add_argument("--head-time-ms", type=int, default=DEFAULT_HEAD_TIME_MS, help="Run time for each servo 3 turn segment in milliseconds")
    parser.add_argument("--final-head", type=int, default=DEFAULT_FINAL_HEAD, help="Servo 3 final position after the head turns")
    parser.add_argument("--post-head-pause", type=float, default=DEFAULT_POST_HEAD_PAUSE, help="Pause time after the head turn sequence")
    parser.add_argument("--final-target-0", type=int, default=DEFAULT_FINAL_TARGET_0, help="Final slow target for servo 0")
    parser.add_argument("--final-target-1", type=int, default=DEFAULT_FINAL_TARGET_1, help="Final slow target for servo 1")
    parser.add_argument("--final-target-3", type=int, default=DEFAULT_FINAL_TARGET_3, help="Final slow target for servo 3")
    parser.add_argument("--final-speeds-03", nargs=2, type=int, default=DEFAULT_FINAL_SPEEDS_03, metavar=("S0", "S3"), help="Final slow speeds for servo 0 and servo 3")
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


def build_sync_packet(ids: tuple[int, int, int, int], positions: tuple[int, int, int, int], speeds: tuple[int, int, int, int], run_time_ms: int = 0) -> bytes:
    return build_sync_move_packet(
        (servo_id, position, run_time_ms, speed)
        for servo_id, position, speed in zip(ids, positions, speeds)
    )


def wait_until_settled(
    ser: serial.Serial,
    ids: tuple[int, int, int, int],
    targets: tuple[int, int, int, int],
    poll_interval: float,
    settle_threshold: int,
    settle_polls: int,
    settle_wait: float,
    stable_delta: int,
) -> tuple[int, int, int, int]:
    stable_target_count = 0
    stable_motion_count = 0
    started = time.monotonic()
    last_positions = targets
    previous_pos1 = None
    previous_pos2 = None

    while True:
        pos1 = read_position(ser, ids[1])
        pos2 = read_position(ser, ids[2])
        last_positions = (targets[0], pos1, pos2, targets[3])
        print(f"Settle pos      : servo1={pos1} servo2={pos2}")

        if abs(pos1 - targets[1]) <= settle_threshold and abs(pos2 - targets[2]) <= settle_threshold:
            stable_target_count += 1
            if stable_target_count >= settle_polls:
                print("Stage settled near both targets.")
                return last_positions
        else:
            stable_target_count = 0

        if previous_pos1 is not None and previous_pos2 is not None:
            if (
                abs(pos2 - targets[2]) <= settle_threshold
                and abs(pos1 - previous_pos1) <= stable_delta
                and abs(pos2 - previous_pos2) <= stable_delta
            ):
                stable_motion_count += 1
                if stable_motion_count >= settle_polls:
                    print("Stage settled with servo 2 at target and motion stabilized.")
                    return last_positions
            else:
                stable_motion_count = 0

        previous_pos1 = pos1
        previous_pos2 = pos2

        if (time.monotonic() - started) >= settle_wait:
            print("Settle wait reached; continuing with current positions.")
            return last_positions

        time.sleep(poll_interval)


def main() -> int:
    args = parse_args()
    ids = tuple(args.ids)
    targets = tuple(args.targets)
    speeds = tuple(args.speeds)
    return_speeds = tuple(args.return_speeds)
    final_speeds_03 = tuple(args.final_speeds_03)

    if not 0.0 <= args.delay_ratio <= 1.0:
        raise ValueError(f"--delay-ratio must be in [0, 1], got {args.delay_ratio}")
    if args.settle_polls < 1:
        raise ValueError(f"--settle-polls must be >= 1, got {args.settle_polls}")
    if args.head_turns < 1:
        raise ValueError(f"--head-turns must be >= 1, got {args.head_turns}")

    with serial.Serial(args.device, args.baudrate, timeout=args.timeout) as ser:
        start_positions = tuple(read_position(ser, servo_id) for servo_id in ids)
        stage_1_positions = (targets[0], targets[1], start_positions[2], targets[3])
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
        print(f"Hold time      : {args.hold_time}")
        print(f"Return target  : ({args.return_target_1}, {args.return_target_2})")
        print(f"Head turn      : left={args.head_left} right={args.head_right} turns={args.head_turns}")
        print(f"Head time ms   : {args.head_time_ms}")
        print(f"Final head     : {args.final_head}")
        print(f"Final 0/1/3    : ({args.final_target_0}, {args.final_target_1}, {args.final_target_3})")
        print(f"Final 0/3 spd  : {final_speeds_03}")
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

        settled_positions = wait_until_settled(
            ser=ser,
            ids=ids,
            targets=stage_2_positions,
            poll_interval=args.poll_interval,
            settle_threshold=args.settle_threshold,
            settle_polls=args.settle_polls,
            settle_wait=args.settle_wait,
            stable_delta=args.stable_delta,
        )

        if args.hold_time > 0:
            print("Holding final pose...")
            time.sleep(args.hold_time)

        return_positions = (
            stage_2_positions[0],
            args.return_target_1,
            args.return_target_2,
            stage_2_positions[3],
        )
        return_speed_packet = (
            speeds[0],
            return_speeds[0],
            return_speeds[1],
            speeds[3],
        )
        return_packet = build_sync_packet(ids, return_positions, return_speed_packet)
        return_sent = write_packet(ser, return_packet)
        print(f"Settled pos     : {settled_positions}")
        print(f"Return pos      : {return_positions}")
        print(f"Return packet   : {return_packet.hex(' ')}")
        print(f"Return sent     : {return_sent}")

        return_settled_positions = wait_until_settled(
            ser=ser,
            ids=ids,
            targets=return_positions,
            poll_interval=args.poll_interval,
            settle_threshold=args.settle_threshold,
            settle_polls=args.settle_polls,
            settle_wait=args.settle_wait,
            stable_delta=args.stable_delta,
        )
        print(f"Return settled  : {return_settled_positions}")

        head_speeds = (speeds[0], return_speeds[0], return_speeds[1], 120)
        total_segments = args.head_turns * 2
        for segment_index in range(total_segments):
            head_position = args.head_left if segment_index % 2 == 0 else args.head_right
            head_positions = (
                return_positions[0],
                return_positions[1],
                return_positions[2],
                head_position,
            )
            head_packet = build_sync_packet(ids, head_positions, head_speeds, run_time_ms=args.head_time_ms)
            head_sent = write_packet(ser, head_packet)
            print(f"Head pos {segment_index + 1:02d}   : {head_positions}")
            print(f"Head packet {segment_index + 1:02d}: {head_packet.hex(' ')}")
            print(f"Head sent {segment_index + 1:02d} : {head_sent}")
            time.sleep(max(args.head_time_ms / 1000.0, 0.02))

        final_head_positions = (
            return_positions[0],
            return_positions[1],
            return_positions[2],
            args.final_head,
        )
        final_head_packet = build_sync_packet(ids, final_head_positions, head_speeds, run_time_ms=args.head_time_ms)
        final_head_sent = write_packet(ser, final_head_packet)
        print(f"Final head pos  : {final_head_positions}")
        print(f"Final head pkt  : {final_head_packet.hex(' ')}")
        print(f"Final head sent : {final_head_sent}")

        if args.post_head_pause > 0:
            print("Pausing after head turn...")
            time.sleep(args.post_head_pause)

        final_positions_03 = (
            args.final_target_0,
            args.final_target_1,
            return_positions[2],
            args.final_target_3,
        )
        final_speed_packet_03 = (
            final_speeds_03[0],
            return_speeds[0],
            return_speeds[1],
            final_speeds_03[1],
        )
        final_packet_03 = build_sync_packet(ids, final_positions_03, final_speed_packet_03)
        final_sent_03 = write_packet(ser, final_packet_03)
        print(f"Final 0/3 pos   : {final_positions_03}")
        print(f"Final 0/3 spd   : {final_speed_packet_03}")
        print(f"Final 0/3 pkt   : {final_packet_03.hex(' ')}")
        print(f"Final 0/3 sent  : {final_sent_03}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
