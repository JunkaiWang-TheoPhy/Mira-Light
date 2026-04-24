#!/usr/bin/env python3

from dataclasses import dataclass
import re
import time
from typing import List, Optional, Tuple

import serial


UART_DEVICE = "/dev/ttyS3"
BAUDRATE = 115200
LINE_ENDINGS = {
    "none": "",
    "lf": "\n",
    "crlf": "\r\n",
}
DEFAULT_LINE_ENDING = "lf"


@dataclass(frozen=True)
class TouchEvent:
    name: str
    value: Optional[int] = None


@dataclass(frozen=True)
class AckMessage:
    text: str


@dataclass(frozen=True)
class ReadyMessage:
    text: str


@dataclass(frozen=True)
class UnknownMessage:
    text: str


TEXT_PATTERNS = (
    re.compile(rb"TOUCH,(?:PRESS|RELEASE|HOLD),\d+"),
    re.compile(rb"\*Ready\.[\x20-\x7e]*"),
    re.compile(rb"OK[\x20-\x7e]*"),
    re.compile(rb"(?:PRESS|RELEASE|HOLD)"),
)


def build_all_command(r: int, g: int, b: int, bri: int) -> str:
    _validate_byte("r", r)
    _validate_byte("g", g)
    _validate_byte("b", b)
    _validate_byte("bri", bri)
    return f"ALL,{r},{g},{b},{bri}"


def build_one_command(grp: int, idx: int, r: int, g: int, b: int, bri: int) -> str:
    _validate_group_and_index(grp, idx)
    _validate_byte("r", r)
    _validate_byte("g", g)
    _validate_byte("b", b)
    _validate_byte("bri", bri)
    return f"ONE,{grp},{idx},{r},{g},{b},{bri}"


def build_bri_command(value: int) -> str:
    _validate_byte("value", value)
    return f"BRI,{value}"


def build_off_command() -> str:
    return "OFF"


def build_thr_command(value: int) -> str:
    if value < 0:
        raise ValueError(f"threshold must be >= 0, got {value}")
    return f"THR,{value}"


def build_help_command() -> str:
    return "HELP"


def build_rainbow_command(brightness: int = 200) -> str:
    _validate_byte("brightness", brightness)
    return f"RAINBOW,{brightness}"


def build_breathe_command(
    r: int | None = None,
    g: int | None = None,
    b: int | None = None,
    brightness: int = 200,
    rainbow: bool = False,
) -> str:
    _validate_byte("brightness", brightness)
    if rainbow:
        return "BREATHE,RAINBOW" if brightness == 200 else f"BREATHE,RAINBOW,{brightness}"
    if r is None or g is None or b is None:
        return "BREATHE" if brightness == 200 else f"BREATHE,255,255,255,{brightness}"
    _validate_byte("r", r)
    _validate_byte("g", g)
    _validate_byte("b", b)
    return f"BREATHE,{r},{g},{b},{brightness}"


def build_wake_command(
    r: int | None = None,
    g: int | None = None,
    b: int | None = None,
    brightness: int = 200,
    rainbow: bool = False,
) -> str:
    _validate_byte("brightness", brightness)
    if rainbow:
        return "WAKE,RAINBOW" if brightness == 200 else f"WAKE,RAINBOW,{brightness}"
    if r is None or g is None or b is None:
        return "WAKE"
    _validate_byte("r", r)
    _validate_byte("g", g)
    _validate_byte("b", b)
    return f"WAKE,{r},{g},{b}" if brightness == 200 else f"WAKE,{r},{g},{b},{brightness}"


def build_spin_command(
    r: int | None = None,
    g: int | None = None,
    b: int | None = None,
    outer_dir: int = 0,
    inner_dir: int = 0,
    brightness: int = 200,
    rainbow: bool = False,
) -> str:
    _validate_direction("outer_dir", outer_dir)
    _validate_direction("inner_dir", inner_dir)
    _validate_byte("brightness", brightness)
    if rainbow:
        if outer_dir == 0 and inner_dir == 0 and brightness == 200:
            return "SPIN,RAINBOW"
        if brightness == 200:
            return f"SPIN,RAINBOW,{outer_dir},{inner_dir}"
        return f"SPIN,RAINBOW,{outer_dir},{inner_dir},{brightness}"
    if r is None or g is None or b is None:
        if outer_dir == 0 and inner_dir == 0 and brightness == 200:
            return "SPIN"
        return f"SPIN,255,255,255,{outer_dir},{inner_dir},{brightness}"
    _validate_byte("r", r)
    _validate_byte("g", g)
    _validate_byte("b", b)
    if outer_dir == 0 and inner_dir == 0 and brightness == 200:
        return f"SPIN,{r},{g},{b}"
    if brightness == 200:
        return f"SPIN,{r},{g},{b},{outer_dir},{inner_dir}"
    return f"SPIN,{r},{g},{b},{outer_dir},{inner_dir},{brightness}"


def build_stop_command() -> str:
    return "STOP"


def build_resume_command() -> str:
    return "RESUME"


def normalize_outgoing_command(text: str) -> str:
    message = text.strip()
    if not message:
        raise ValueError("empty command")

    parts = [part.strip() for part in message.split(",")]
    command = parts[0].upper()

    if command == "ALL" and len(parts) == 5:
        return build_all_command(
            int(parts[1]),
            int(parts[2]),
            int(parts[3]),
            int(parts[4]),
        )
    if command == "ONE" and len(parts) == 7:
        return build_one_command(
            int(parts[1]),
            int(parts[2]),
            int(parts[3]),
            int(parts[4]),
            int(parts[5]),
            int(parts[6]),
        )
    if command == "BRI" and len(parts) == 2:
        return build_bri_command(int(parts[1]))
    if command == "THR" and len(parts) == 2:
        return build_thr_command(int(parts[1]))
    if command == "OFF" and len(parts) == 1:
        return build_off_command()
    if command == "HELP" and len(parts) == 1:
        return build_help_command()
    if command == "RAINBOW" and len(parts) == 1:
        return build_rainbow_command()
    if command == "RAINBOW" and len(parts) == 2:
        return build_rainbow_command(int(parts[1]))
    if command == "BREATHE" and len(parts) == 1:
        return build_breathe_command()
    if command == "BREATHE" and len(parts) == 2 and parts[1].upper() == "RAINBOW":
        return build_breathe_command(rainbow=True)
    if command == "BREATHE" and len(parts) == 3 and parts[1].upper() == "RAINBOW":
        return build_breathe_command(rainbow=True, brightness=int(parts[2]))
    if command == "BREATHE" and len(parts) == 5:
        return build_breathe_command(
            int(parts[1]), int(parts[2]), int(parts[3]), int(parts[4])
        )
    if command == "WAKE" and len(parts) == 1:
        return build_wake_command()
    if command == "WAKE" and len(parts) == 2 and parts[1].upper() == "RAINBOW":
        return build_wake_command(rainbow=True)
    if command == "WAKE" and len(parts) == 3 and parts[1].upper() == "RAINBOW":
        return build_wake_command(rainbow=True, brightness=int(parts[2]))
    if command == "WAKE" and len(parts) == 4:
        return build_wake_command(
            int(parts[1]), int(parts[2]), int(parts[3])
        )
    if command == "WAKE" and len(parts) == 5:
        return build_wake_command(
            int(parts[1]), int(parts[2]), int(parts[3]), int(parts[4])
        )
    if command == "SPIN" and len(parts) == 1:
        return build_spin_command()
    if command == "SPIN" and len(parts) == 2 and parts[1].upper() == "RAINBOW":
        return build_spin_command(rainbow=True)
    if command == "SPIN" and len(parts) == 4 and parts[1].upper() == "RAINBOW":
        return build_spin_command(rainbow=True, outer_dir=int(parts[2]), inner_dir=int(parts[3]))
    if command == "SPIN" and len(parts) == 5 and parts[1].upper() == "RAINBOW":
        return build_spin_command(
            rainbow=True, outer_dir=int(parts[2]), inner_dir=int(parts[3]), brightness=int(parts[4])
        )
    if command == "SPIN" and len(parts) == 4:
        return build_spin_command(
            int(parts[1]), int(parts[2]), int(parts[3])
        )
    if command == "SPIN" and len(parts) == 6:
        return build_spin_command(
            int(parts[1]), int(parts[2]), int(parts[3]), int(parts[4]), int(parts[5])
        )
    if command == "SPIN" and len(parts) == 7:
        return build_spin_command(
            int(parts[1]), int(parts[2]), int(parts[3]), int(parts[4]), int(parts[5]), int(parts[6])
        )
    if command == "STOP" and len(parts) == 1:
        return build_stop_command()
    if command == "RESUME" and len(parts) == 1:
        return build_resume_command()

    raise ValueError(f"unsupported LED command: {message}")


def send_command(
    command: str,
    uart_device: str = UART_DEVICE,
    baudrate: int = BAUDRATE,
    line_ending: str = DEFAULT_LINE_ENDING,
    read_reply: bool = False,
    reply_timeout: float = 0.2,
):
    if line_ending not in LINE_ENDINGS:
        raise ValueError(f"unsupported line ending: {line_ending}")

    payload = f"{command}{LINE_ENDINGS[line_ending]}".encode("utf-8")
    timeout = reply_timeout if read_reply else 0.05

    with serial.Serial(uart_device, baudrate, timeout=timeout) as ser:
        ser.reset_input_buffer()
        sent = ser.write(payload)
        ser.flush()

        reply = ""
        if read_reply:
            time.sleep(reply_timeout)
            if ser.in_waiting:
                reply = ser.read(ser.in_waiting).decode("utf-8", errors="replace")

    return sent, reply


def parse_incoming_message(text: str):
    message = text.strip()
    if not message:
        raise ValueError("empty message")

    touch_match = re.fullmatch(r"TOUCH,(PRESS|RELEASE|HOLD),(\d+)", message)
    if touch_match:
        return TouchEvent(name=touch_match.group(1), value=int(touch_match.group(2)))

    if message == "PRESS":
        return TouchEvent(name="PRESS")
    if message == "RELEASE":
        return TouchEvent(name="RELEASE")
    if message == "HOLD":
        return TouchEvent(name="HOLD")
    if message.startswith("OK"):
        return AckMessage(text=message)
    if message.startswith("*Ready."):
        return ReadyMessage(text=message)
    return UnknownMessage(text=message)


def split_uart_chunk(raw_bytes: bytes) -> List[Tuple[str, bytes]]:
    matches = []
    for pattern in TEXT_PATTERNS:
        for match in pattern.finditer(raw_bytes):
            matches.append((match.start(), match.end()))

    matches.sort(key=lambda item: (item[0], -(item[1] - item[0])))

    merged = []
    last_end = -1
    for start, end in matches:
        if start < last_end:
            continue
        merged.append((start, end))
        last_end = end

    if not merged:
        return [("binary", raw_bytes)] if raw_bytes else []

    parts: List[Tuple[str, bytes]] = []
    cursor = 0
    for start, end in merged:
        if start > cursor:
            binary = raw_bytes[cursor:start]
            if binary.strip(b"\x00\r\n\t "):
                parts.append(("binary", binary))
        parts.append(("text", raw_bytes[start:end]))
        cursor = end

    if cursor < len(raw_bytes):
        binary = raw_bytes[cursor:]
        if binary.strip(b"\x00\r\n\t "):
            parts.append(("binary", binary))

    return parts


def _validate_group_and_index(grp: int, idx: int) -> None:
    if grp not in (0, 1):
        raise ValueError(f"grp must be 0 or 1, got {grp}")

    max_idx = 23 if grp == 0 else 15
    if not 0 <= idx <= max_idx:
        raise ValueError(
            f"idx out of range for grp {grp}: {idx} (allowed 0-{max_idx})"
        )


def _validate_byte(name: str, value: int) -> None:
    if not 0 <= value <= 255:
        raise ValueError(f"{name} must be in 0-255, got {value}")


def _validate_direction(name: str, value: int) -> None:
    if value not in (0, 1):
        raise ValueError(f"{name} must be 0 or 1, got {value}")
