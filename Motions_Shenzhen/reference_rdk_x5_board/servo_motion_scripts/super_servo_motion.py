#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
import time
from dataclasses import dataclass
from typing import Any

import serial

from bus_servo_protocol import (
    Address,
    build_move_packet,
    build_read_packet,
    parse_status_packet,
    unpack_u16,
)
from send_uart1_servo_cmd import DEFAULT_BAUDRATE, DEFAULT_DEVICE, DEFAULT_TIMEOUT, read_status_response


DEFAULT_IDS = (0, 1, 2, 3)
DEFAULT_POLL_INTERVAL = 0.03
DEFAULT_TIMEOUT_S = 8.0
DEGREES_PER_TURN = 360.0
STEPS_PER_TURN = 4096.0


@dataclass
class ServoPlan:
    servo_id: int
    target_steps: int
    speed: int
    trigger: dict[str, Any]


def degrees_to_steps(degrees: float) -> int:
    if not 0.0 <= degrees <= DEGREES_PER_TURN:
        raise ValueError(f"degrees out of range: {degrees} (expected 0-360)")
    return round(degrees / DEGREES_PER_TURN * STEPS_PER_TURN)


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


def send_move_and_consume_ack(ser: serial.Serial, servo_id: int, target_steps: int, speed: int) -> tuple[bytes, int, bytes]:
    packet = build_move_packet(servo_id, target_steps, 0, speed)
    sent = write_packet(ser, packet)
    response = read_status_response(ser)
    return packet, sent, response


def validate_ids(ids: list[int]) -> tuple[int, int, int, int]:
    if len(ids) != 4:
        raise ValueError(f"ids must contain exactly 4 servo ids, got {len(ids)}")
    return tuple(ids)  # type: ignore[return-value]


def normalize_targets(targets: list[float | int], unit: str) -> list[int]:
    if len(targets) != 4:
        raise ValueError(f"targets must contain exactly 4 values, got {len(targets)}")
    if unit == "steps":
        return [int(value) for value in targets]
    if unit == "degrees":
        return [degrees_to_steps(float(value)) for value in targets]
    raise ValueError(f"unsupported unit: {unit}")


def normalize_speeds(speeds: list[int]) -> list[int]:
    if len(speeds) != 4:
        raise ValueError(f"speeds must contain exactly 4 values, got {len(speeds)}")
    return [int(value) for value in speeds]


def normalize_triggers(triggers: list[dict[str, Any] | str]) -> list[dict[str, Any]]:
    if len(triggers) != 4:
        raise ValueError(f"triggers must contain exactly 4 rules, got {len(triggers)}")
    normalized = []
    for trigger in triggers:
        if isinstance(trigger, str):
            normalized.append({"type": trigger})
        elif isinstance(trigger, dict):
            normalized.append(dict(trigger))
        else:
            raise ValueError(f"unsupported trigger type: {trigger!r}")
    return normalized


def build_plans(ids: tuple[int, int, int, int], targets: list[int], speeds: list[int], triggers: list[dict[str, Any]]) -> list[ServoPlan]:
    return [
        ServoPlan(servo_id=servo_id, target_steps=target, speed=speed, trigger=trigger)
        for servo_id, target, speed, trigger in zip(ids, targets, speeds, triggers)
    ]


def trigger_ready(
    trigger: dict[str, Any],
    index: int,
    start_positions: dict[int, int],
    current_positions: dict[int, int],
    started_at: dict[int, float],
    now: float,
) -> bool:
    trigger_type = trigger.get("type", "immediate")

    if trigger_type == "immediate":
        return True

    if trigger_type == "after_started":
        ref = int(trigger["servo"])
        delay = float(trigger.get("delay", 0.0))
        return ref in started_at and (now - started_at[ref]) >= delay

    if trigger_type == "after_delay":
        delay = float(trigger.get("delay", 0.0))
        return delay <= 0 or now >= delay

    if trigger_type == "after_ratio":
        ref = int(trigger["servo"])
        ratio = float(trigger["ratio"])
        ref_target = int(trigger["target"])
        if ref not in started_at:
            return False
        start = start_positions[ref]
        current = current_positions[ref]
        threshold = start + (ref_target - start) * ratio
        if ref_target >= start:
            return current >= threshold
        return current <= threshold

    if trigger_type == "after_position":
        ref = int(trigger["servo"])
        position = int(trigger["position"])
        direction = trigger.get("direction", "auto")
        if ref not in started_at:
            return False
        current = current_positions[ref]
        start = start_positions[ref]
        if direction == "gte":
            return current >= position
        if direction == "lte":
            return current <= position
        return current >= position if position >= start else current <= position

    if trigger_type == "when_stable_near":
        ref = int(trigger["servo"])
        near_threshold = int(trigger.get("near_threshold", 20))
        stable_count = int(trigger.get("stable_count", 5))
        ref_target = int(trigger["target"])
        current = current_positions[ref]
        error = abs(current - ref_target)
        return error <= near_threshold and int(trigger.get("_stable_hits", 0)) >= stable_count

    raise ValueError(f"unsupported trigger type for servo index {index}: {trigger_type}")


def update_stability(triggers: list[dict[str, Any]], previous_positions: dict[int, int], current_positions: dict[int, int]) -> None:
    for trigger in triggers:
        if trigger.get("type") != "when_stable_near":
            continue
        ref = int(trigger["servo"])
        prev = previous_positions.get(ref)
        current = current_positions.get(ref)
        if prev is None or current is None:
            trigger["_stable_hits"] = 0
            continue
        trigger["_stable_hits"] = int(trigger.get("_stable_hits", 0)) + 1 if current == prev else 0


def execute_super_motion(
    targets: list[float | int],
    speeds: list[int],
    triggers: list[dict[str, Any] | str],
    *,
    ids: list[int] | tuple[int, int, int, int] = DEFAULT_IDS,
    unit: str = "steps",
    device: str = DEFAULT_DEVICE,
    baudrate: int = DEFAULT_BAUDRATE,
    timeout: float = DEFAULT_TIMEOUT,
    poll_interval: float = DEFAULT_POLL_INTERVAL,
    max_wait: float = DEFAULT_TIMEOUT_S,
    preview: bool = False,
) -> dict[str, Any]:
    servo_ids = validate_ids(list(ids))
    target_steps = normalize_targets(list(targets), unit)
    speed_values = normalize_speeds(list(speeds))
    trigger_rules = normalize_triggers(list(triggers))

    for index, trigger in enumerate(trigger_rules):
        if trigger.get("type") in {"after_ratio", "when_stable_near"} and "target" not in trigger:
            ref = int(trigger["servo"])
            try:
                ref_index = servo_ids.index(ref)
            except ValueError as exc:
                raise ValueError(f"trigger for servo {servo_ids[index]} references unknown servo id {ref}") from exc
            trigger["target"] = target_steps[ref_index]

    plans = build_plans(servo_ids, target_steps, speed_values, trigger_rules)

    if preview:
        return {
            "ids": servo_ids,
            "targets_steps": target_steps,
            "speeds": speed_values,
            "triggers": trigger_rules,
        }

    with serial.Serial(device, baudrate, timeout=timeout) as ser:
        start_positions = {servo_id: read_position(ser, servo_id) for servo_id in servo_ids}
        current_positions = dict(start_positions)
        previous_positions = dict(start_positions)
        started_at: dict[int, float] = {}
        sent_packets: list[dict[str, Any]] = []
        motion_start = time.monotonic()

        print(f"Device         : {device}")
        print(f"Baudrate       : {baudrate}")
        print(f"Timeout        : {timeout}")
        print(f"Poll interval  : {poll_interval}")
        print(f"Max wait       : {max_wait}")
        print(f"Servo IDs      : {servo_ids}")
        print(f"Targets steps  : {tuple(target_steps)}")
        print(f"Speeds         : {tuple(speed_values)}")
        print(f"Start pos      : {start_positions}")

        while len(started_at) < len(plans):
            for servo_id in servo_ids:
                previous_positions[servo_id] = current_positions[servo_id]
                current_positions[servo_id] = read_position(ser, servo_id)

            update_stability(trigger_rules, previous_positions, current_positions)

            now = time.monotonic() - motion_start
            for index, plan in enumerate(plans):
                if plan.servo_id in started_at:
                    continue
                if trigger_ready(plan.trigger, index, start_positions, current_positions, started_at, now):
                    packet, sent, reply = send_move_and_consume_ack(ser, plan.servo_id, plan.target_steps, plan.speed)
                    started_at[plan.servo_id] = now
                    sent_packets.append(
                        {
                            "servo_id": plan.servo_id,
                            "target_steps": plan.target_steps,
                            "speed": plan.speed,
                            "packet_hex": packet.hex(" "),
                            "sent_bytes": sent,
                            "reply_hex": reply.hex(" "),
                            "started_at": round(now, 3),
                        }
                    )
                    print(f"Started servo  : {plan.servo_id} at {now:.3f}s -> {plan.target_steps} speed={plan.speed}")
                    print(f"Packet         : {packet.hex(' ')}")
                    print(f"Reply          : {reply.hex(' ')}")

            if (time.monotonic() - motion_start) >= max_wait:
                missing = [plan.servo_id for plan in plans if plan.servo_id not in started_at]
                raise TimeoutError(f"super motion timed out before starting servos: {missing}")

            if len(started_at) < len(plans):
                time.sleep(poll_interval)

    return {
        "ids": servo_ids,
        "targets_steps": target_steps,
        "speeds": speed_values,
        "triggers": trigger_rules,
        "sent_packets": sent_packets,
    }


def parse_args():
    parser = argparse.ArgumentParser(
        description="Super servo motion function: 4 targets, 4 speeds, 4 trigger rules"
    )
    parser.add_argument("--device", default=DEFAULT_DEVICE, help="UART device path")
    parser.add_argument("--baudrate", type=int, default=DEFAULT_BAUDRATE, help="UART baudrate")
    parser.add_argument("--timeout", type=float, default=DEFAULT_TIMEOUT, help="UART timeout")
    parser.add_argument("--poll-interval", type=float, default=DEFAULT_POLL_INTERVAL, help="Polling interval")
    parser.add_argument("--max-wait", type=float, default=DEFAULT_TIMEOUT_S, help="Maximum wait time before aborting")
    parser.add_argument("--unit", choices=("steps", "degrees"), default="steps", help="Unit for target values")
    parser.add_argument("--preview", action="store_true", help="Validate inputs and print the parsed plan without sending")
    parser.add_argument(
        "--config-json",
        required=True,
        help=(
            "JSON string with keys ids, targets, speeds, triggers. "
            "Example: "
            '\'{"ids":[0,1,2,3],"targets":[2048,1700,2200,1500],"speeds":[1000,800,900,900],'
            '"triggers":["immediate",{"type":"after_ratio","servo":1,"ratio":0.5},"immediate","immediate"]}\''
        ),
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    config = json.loads(args.config_json)
    result = execute_super_motion(
        targets=config["targets"],
        speeds=config["speeds"],
        triggers=config["triggers"],
        ids=config.get("ids", list(DEFAULT_IDS)),
        unit=config.get("unit", args.unit),
        device=args.device,
        baudrate=args.baudrate,
        timeout=args.timeout,
        poll_interval=args.poll_interval,
        max_wait=args.max_wait,
        preview=args.preview,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
