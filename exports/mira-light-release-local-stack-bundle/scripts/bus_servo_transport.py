#!/usr/bin/env python3
"""TCP transport for Mira Light bus-servo commands."""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
import socket
from typing import Any, Protocol

from bus_servo_protocol import validate_command_frame


DEFAULT_RDK_X5_HOST = "192.168.31.10"
DEFAULT_RDK_X5_PORT = 9527
DEFAULT_TIMEOUT_SECONDS = 2.0
DEFAULT_RUNTIME_CONFIG_PATH = Path(__file__).resolve().parents[1] / "config" / "bus_servo_runtime.json"


class BusServoTransport(Protocol):
    def send(self, command: str) -> dict[str, Any]:
        """Send a raw bus-servo command string."""


class BusServoTransportError(RuntimeError):
    """Raised when the bus-servo transport cannot reach the RDK X5 endpoint."""


@dataclass(frozen=True)
class BusServoRuntimeConfig:
    transport: str = "tcp"
    tcp_host: str = DEFAULT_RDK_X5_HOST
    tcp_port: int = DEFAULT_RDK_X5_PORT
    timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS
    default_move_ms: int = 220
    max_move_ms: int = 9999
    infer_move_ms_from_next_delay: bool = True
    relative_requires_known_state: bool = True

    @classmethod
    def from_file(cls, path: Path = DEFAULT_RUNTIME_CONFIG_PATH) -> "BusServoRuntimeConfig":
        raw = json.loads(path.read_text(encoding="utf-8"))
        return cls(
            transport=str(raw.get("transport", "tcp")),
            tcp_host=str(raw.get("tcpHost", DEFAULT_RDK_X5_HOST)),
            tcp_port=int(raw.get("tcpPort", DEFAULT_RDK_X5_PORT)),
            timeout_seconds=float(raw.get("timeoutSeconds", DEFAULT_TIMEOUT_SECONDS)),
            default_move_ms=int(raw.get("defaultMoveMs", 220)),
            max_move_ms=int(raw.get("maxMoveMs", 9999)),
            infer_move_ms_from_next_delay=bool(raw.get("inferMoveMsFromNextDelay", True)),
            relative_requires_known_state=bool(raw.get("relativeRequiresKnownState", True)),
        )


class DryRunBusServoTransport:
    def __init__(self) -> None:
        self.sent_commands: list[str] = []

    def send(self, command: str) -> dict[str, Any]:
        validated = validate_command_frame(command)
        self.sent_commands.append(validated)
        return {
            "ok": True,
            "dryRun": True,
            "command": validated,
            "host": DEFAULT_RDK_X5_HOST,
            "port": DEFAULT_RDK_X5_PORT,
        }


class TcpBusServoTransport:
    def __init__(
        self,
        host: str = DEFAULT_RDK_X5_HOST,
        port: int = DEFAULT_RDK_X5_PORT,
        *,
        timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS,
    ):
        self.host = host
        self.port = int(port)
        self.timeout_seconds = timeout_seconds

    @classmethod
    def from_runtime_config(cls, config: BusServoRuntimeConfig | None = None) -> "TcpBusServoTransport":
        cfg = config or BusServoRuntimeConfig.from_file()
        return cls(host=cfg.tcp_host, port=cfg.tcp_port, timeout_seconds=cfg.timeout_seconds)

    def send(self, command: str) -> dict[str, Any]:
        validated = validate_command_frame(command)
        payload = validated + "\n"
        try:
            with socket.create_connection((self.host, self.port), timeout=self.timeout_seconds) as sock:
                sock.sendall(payload.encode("utf-8"))
                sock.shutdown(socket.SHUT_WR)
                chunks: list[bytes] = []
                sock.settimeout(self.timeout_seconds)
                while True:
                    try:
                        chunk = sock.recv(4096)
                    except socket.timeout:
                        break
                    if not chunk:
                        break
                    chunks.append(chunk)
        except OSError as exc:
            raise BusServoTransportError(
                f"Failed to reach Mira Light bus-servo endpoint {self.host}:{self.port}: {exc}"
            ) from exc
        raw_response = b"".join(chunks).decode("utf-8", errors="replace").strip()
        return {
            "ok": True,
            "host": self.host,
            "port": self.port,
            "command": validated,
            "response": raw_response,
        }
