#!/usr/bin/env python3

from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum
from typing import Iterable, Sequence


HEADER = bytes((0xFF, 0xFF))
BROADCAST_ID = 0xFE
SERVO_ID_MIN = 0
SERVO_ID_MAX = 0xFD


class Instruction(IntEnum):
    PING = 0x01
    READ_DATA = 0x02
    WRITE_DATA = 0x03
    REG_WRITE = 0x04
    ACTION = 0x05
    RESET = 0x06
    SYNC_READ = 0x82
    SYNC_WRITE = 0x83


class Address(IntEnum):
    ID = 0x05
    BAUDRATE = 0x06
    RESPONSE_DELAY = 0x07
    RESPONSE_STATUS_LEVEL = 0x08
    MIN_ANGLE_LIMIT = 0x09
    MAX_ANGLE_LIMIT = 0x0B
    OPERATING_MODE = 0x21
    TORQUE_SWITCH = 0x28
    ACCELERATION = 0x29
    TARGET_POSITION = 0x2A
    RUN_TIME = 0x2C
    RUN_SPEED = 0x2E
    TORQUE_LIMIT = 0x30
    LOCK_FLAG = 0x37
    CURRENT_POSITION = 0x38
    CURRENT_SPEED = 0x3A
    CURRENT_LOAD = 0x3C
    CURRENT_VOLTAGE = 0x3E
    CURRENT_TEMPERATURE = 0x3F
    ASYNC_WRITE_FLAG = 0x40
    SERVO_STATUS = 0x41
    MOVING = 0x42
    CURRENT_CURRENT = 0x45


TORQUE_OFF = 0
TORQUE_ON = 1
TORQUE_DAMP = 2
TORQUE_CALIBRATE_CURRENT_POSITION_TO_2048 = 128


@dataclass(frozen=True)
class StatusPacket:
    servo_id: int
    error: int
    parameters: bytes

    @property
    def length(self) -> int:
        return len(self.parameters) + 2

    @property
    def ok(self) -> bool:
        return self.error == 0

    def encode(self) -> bytes:
        body = bytes((self.servo_id, self.length, self.error)) + self.parameters
        return HEADER + body + bytes((checksum(body),))


def checksum(payload: bytes | bytearray | Sequence[int]) -> int:
    return (~(sum(payload) & 0xFF)) & 0xFF


def build_packet(servo_id: int, instruction: int | Instruction, parameters: Iterable[int] = ()) -> bytes:
    _validate_servo_id(servo_id, allow_broadcast=True)
    params = bytes(parameters)
    body = bytes((servo_id, len(params) + 2, int(instruction))) + params
    return HEADER + body + bytes((checksum(body),))


def build_ping_packet(servo_id: int) -> bytes:
    return build_packet(servo_id, Instruction.PING)


def build_read_packet(servo_id: int, address: int, size: int) -> bytes:
    _validate_size(size)
    return build_packet(servo_id, Instruction.READ_DATA, (address, size))


def build_write_packet(servo_id: int, address: int, data: bytes | Iterable[int]) -> bytes:
    payload = bytes((address,)) + bytes(data)
    if len(payload) < 2:
        raise ValueError("write payload must contain address and at least 1 data byte")
    return build_packet(servo_id, Instruction.WRITE_DATA, payload)


def build_reg_write_packet(servo_id: int, address: int, data: bytes | Iterable[int]) -> bytes:
    payload = bytes((address,)) + bytes(data)
    if len(payload) < 2:
        raise ValueError("reg-write payload must contain address and at least 1 data byte")
    return build_packet(servo_id, Instruction.REG_WRITE, payload)


def build_action_packet() -> bytes:
    return build_packet(BROADCAST_ID, Instruction.ACTION)


def build_reset_packet(servo_id: int) -> bytes:
    return build_packet(servo_id, Instruction.RESET)


def build_sync_write_packet(address: int, data_len: int, items: Iterable[tuple[int, bytes | Iterable[int]]]) -> bytes:
    _validate_size(data_len)
    params = bytearray((address, data_len))
    count = 0
    for servo_id, raw_data in items:
        _validate_servo_id(servo_id)
        data = bytes(raw_data)
        if len(data) != data_len:
            raise ValueError(
                f"sync-write data length mismatch for servo {servo_id}: expected {data_len}, got {len(data)}"
            )
        params.append(servo_id)
        params.extend(data)
        count += 1
    if count == 0:
        raise ValueError("sync-write requires at least 1 servo item")
    return build_packet(BROADCAST_ID, Instruction.SYNC_WRITE, params)


def build_sync_read_packet(address: int, size: int, servo_ids: Iterable[int]) -> bytes:
    _validate_size(size)
    ids = list(servo_ids)
    if not ids:
        raise ValueError("sync-read requires at least 1 servo id")
    for servo_id in ids:
        _validate_servo_id(servo_id)
    return build_packet(BROADCAST_ID, Instruction.SYNC_READ, (address, size, *ids))


def build_move_data(position: int, run_time: int = 0, speed: int = 0) -> bytes:
    return pack_s16(position) + pack_u16(run_time) + pack_s16(speed)


def build_move_packet(
    servo_id: int,
    position: int,
    run_time: int = 0,
    speed: int = 0,
) -> bytes:
    return build_write_packet(servo_id, Address.TARGET_POSITION, build_move_data(position, run_time, speed))


def build_reg_move_packet(
    servo_id: int,
    position: int,
    run_time: int = 0,
    speed: int = 0,
) -> bytes:
    return build_reg_write_packet(servo_id, Address.TARGET_POSITION, build_move_data(position, run_time, speed))


def build_sync_move_packet(moves: Iterable[tuple[int, int, int, int]]) -> bytes:
    items = []
    for servo_id, position, run_time, speed in moves:
        items.append((servo_id, build_move_data(position, run_time, speed)))
    return build_sync_write_packet(Address.TARGET_POSITION, 6, items)


def build_torque_packet(servo_id: int, torque_mode: int) -> bytes:
    _validate_u8(torque_mode, "torque_mode")
    return build_write_packet(servo_id, Address.TORQUE_SWITCH, bytes((torque_mode,)))


def build_acceleration_packet(servo_id: int, acceleration: int) -> bytes:
    _validate_u8(acceleration, "acceleration")
    return build_write_packet(servo_id, Address.ACCELERATION, bytes((acceleration,)))


def build_set_id_packet(current_id: int, new_id: int) -> bytes:
    _validate_servo_id(current_id, allow_broadcast=True)
    _validate_servo_id(new_id)
    return build_write_packet(current_id, Address.ID, bytes((new_id,)))


def build_lock_packet(servo_id: int, locked: bool) -> bytes:
    return build_write_packet(servo_id, Address.LOCK_FLAG, bytes((1 if locked else 0,)))


def parse_status_packet(packet: bytes | bytearray | Sequence[int]) -> StatusPacket:
    raw = bytes(packet)
    if len(raw) < 6:
        raise ValueError(f"status packet too short: {len(raw)}")
    if raw[:2] != HEADER:
        raise ValueError(f"invalid header: {raw[:2].hex(' ')}")

    servo_id = raw[2]
    length = raw[3]
    expected_len = length + 4
    if len(raw) != expected_len:
        raise ValueError(f"status packet length mismatch: expected {expected_len}, got {len(raw)}")

    body = raw[2:-1]
    recv_checksum = raw[-1]
    calc_checksum = checksum(body)
    if recv_checksum != calc_checksum:
        raise ValueError(f"checksum mismatch: expected 0x{calc_checksum:02X}, got 0x{recv_checksum:02X}")

    error = raw[4]
    parameters = raw[5:-1]
    return StatusPacket(servo_id=servo_id, error=error, parameters=parameters)


def parse_sync_read_response(packets: Iterable[bytes]) -> list[StatusPacket]:
    return [parse_status_packet(packet) for packet in packets]


def pack_u16(value: int) -> bytes:
    _validate_range(value, 0, 0xFFFF, "u16 value")
    return value.to_bytes(2, byteorder="little", signed=False)


def pack_s16(value: int) -> bytes:
    _validate_range(value, -32768, 32767, "s16 value")
    return value.to_bytes(2, byteorder="little", signed=True)


def unpack_u16(data: bytes | bytearray | Sequence[int]) -> int:
    raw = bytes(data)
    if len(raw) != 2:
        raise ValueError(f"u16 requires 2 bytes, got {len(raw)}")
    return int.from_bytes(raw, byteorder="little", signed=False)


def unpack_s16(data: bytes | bytearray | Sequence[int]) -> int:
    raw = bytes(data)
    if len(raw) != 2:
        raise ValueError(f"s16 requires 2 bytes, got {len(raw)}")
    return int.from_bytes(raw, byteorder="little", signed=True)


def describe_status_bits(status: int) -> list[str]:
    mapping = (
        (0x01, "voltage"),
        (0x02, "magnetic-encoder"),
        (0x04, "over-temperature"),
        (0x08, "over-current"),
        (0x20, "over-load"),
    )
    labels = [name for bit, name in mapping if status & bit]
    return labels or ["ok"]


def _validate_servo_id(servo_id: int, allow_broadcast: bool = False) -> None:
    if allow_broadcast and servo_id == BROADCAST_ID:
        return
    if not SERVO_ID_MIN <= servo_id <= SERVO_ID_MAX:
        raise ValueError(f"servo id out of range: {servo_id}")


def _validate_u8(value: int, name: str) -> None:
    _validate_range(value, 0, 0xFF, name)


def _validate_size(size: int) -> None:
    _validate_range(size, 1, 0xFF, "size")


def _validate_range(value: int, minimum: int, maximum: int, name: str) -> None:
    if not minimum <= value <= maximum:
        raise ValueError(f"{name} out of range: {value} (expected {minimum}-{maximum})")
