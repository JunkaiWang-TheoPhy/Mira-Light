#!/usr/bin/env python3

from __future__ import annotations

import argparse
from dataclasses import dataclass
import shlex
import subprocess
from typing import Iterable


DEFAULT_HOST = "192.168.0.183"
DEFAULT_PORT = 22
DEFAULT_USER = "root"


@dataclass(frozen=True)
class RemoteStep:
    label: str
    command: str


def build_parser(description: str) -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument("--host", default=DEFAULT_HOST, help="Remote board SSH host")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT, help="Remote board SSH port")
    parser.add_argument("--user", default=DEFAULT_USER, help="Remote board SSH user")
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Actually run on the remote board. Without this flag, only print the plan.",
    )
    return parser


def render_script(steps: Iterable[RemoteStep]) -> str:
    lines = ["set -euo pipefail"]
    for step in steps:
        lines.append(f"echo '== {step.label} =='")
        lines.append(step.command)
    return "\n".join(lines) + "\n"


def run_or_print(*, args: argparse.Namespace, steps: list[RemoteStep]) -> int:
    script = render_script(steps)
    if not args.execute:
        print(script, end="")
        return 0
    cmd = [
        "ssh",
        "-o",
        "StrictHostKeyChecking=no",
        "-p",
        str(args.port),
        f"{args.user}@{args.host}",
        f"bash -lc {shlex.quote(script)}",
    ]
    return subprocess.run(cmd, check=False).returncode


def exit_from_plan(*, args: argparse.Namespace, steps: list[RemoteStep]) -> None:
    raise SystemExit(run_or_print(args=args, steps=steps))
