#!/usr/bin/env python3

from __future__ import annotations

import argparse
from dataclasses import dataclass
import shlex
import subprocess
import sys
from typing import Iterable


DEFAULT_HOST = "82.157.174.100"
DEFAULT_PORT = 6000
DEFAULT_USER = "root"


@dataclass(frozen=True)
class RemoteStep:
    label: str
    command: str


def build_common_parser(description: str) -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument("--host", default=DEFAULT_HOST, help="Remote board SSH host")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT, help="Remote board SSH port")
    parser.add_argument("--user", default=DEFAULT_USER, help="Remote board SSH user")
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Actually run over SSH. Without this flag, only print the remote script.",
    )
    return parser


def render_remote_script(steps: Iterable[RemoteStep]) -> str:
    lines: list[str] = ["set -euo pipefail"]
    for step in steps:
        lines.append(f"echo '== {step.label} =='")
        lines.append(step.command)
    return "\n".join(lines) + "\n"


def print_remote_plan(steps: Iterable[RemoteStep]) -> None:
    script = render_remote_script(steps)
    print(script, end="")


def execute_remote_steps(*, host: str, port: int, user: str, steps: Iterable[RemoteStep]) -> int:
    script = render_remote_script(steps)
    ssh_cmd = [
        "ssh",
        "-o",
        "StrictHostKeyChecking=no",
        "-p",
        str(port),
        f"{user}@{host}",
        f"bash -lc {shlex.quote(script)}",
    ]
    completed = subprocess.run(ssh_cmd, check=False)
    return completed.returncode


def maybe_run(*, args: argparse.Namespace, steps: list[RemoteStep]) -> int:
    if not args.execute:
        print_remote_plan(steps)
        return 0
    return execute_remote_steps(host=args.host, port=args.port, user=args.user, steps=steps)


def exit_from_run(*, args: argparse.Namespace, steps: list[RemoteStep]) -> None:
    raise SystemExit(maybe_run(args=args, steps=steps))
