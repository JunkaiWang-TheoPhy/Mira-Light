#!/usr/bin/env python3
"""Ask the local Mira brain through llama.cpp with a compact identity prompt pack."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from datetime import datetime
import json
import os
from pathlib import Path
import subprocess
import time
from typing import Any
from urllib import error, parse, request

from build_mira_qwen_messages import DEFAULT_WORKSPACE, build_payload


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SERVER_URL = "http://127.0.0.1:8012/v1/chat/completions"
DEFAULT_SERVER_MODEL = "qwen2.5-3b-instruct-q4_k_m.gguf"
DEFAULT_TIMEOUT_SECONDS = 240.0
DEFAULT_STARTUP_TIMEOUT_SECONDS = 240.0
DEFAULT_MAX_TOKENS = 96
DEFAULT_TEMPERATURE = 0.2
DEFAULT_RUNTIME_DIR = ROOT / "runtime" / "local-qwen"


@dataclass
class ServerHandle:
    process: subprocess.Popen[str]
    log_path: Path


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Ask the local Mira brain through llama.cpp.")
    parser.add_argument("message", help="What to ask Mira.")
    parser.add_argument("--workspace-root", type=Path, default=DEFAULT_WORKSPACE, help="Workspace root that contains IDENTITY/SOUL/MEMORY/AGENTS/USER.")
    parser.add_argument("--state-json", type=Path, help="Optional current runtime/device state JSON file.")
    parser.add_argument("--memory-snippet", action="append", default=[], help="Optional text file to include as retrieved memory. Can be passed multiple times.")
    parser.add_argument("--history-json", type=Path, help="Optional prior chat messages JSON list.")
    parser.add_argument("--server-url", default=DEFAULT_SERVER_URL, help="Local OpenAI-compatible chat completion endpoint.")
    parser.add_argument("--server-model", default=DEFAULT_SERVER_MODEL, help="Model name exposed by llama-server.")
    parser.add_argument("--max-tokens", type=int, default=DEFAULT_MAX_TOKENS, help="Maximum completion tokens.")
    parser.add_argument("--temperature", type=float, default=DEFAULT_TEMPERATURE, help="Sampling temperature.")
    parser.add_argument("--timeout-seconds", type=float, default=DEFAULT_TIMEOUT_SECONDS, help="Request timeout.")
    parser.add_argument("--startup-timeout-seconds", type=float, default=DEFAULT_STARTUP_TIMEOUT_SECONDS, help="How long to wait for auto-started llama-server.")
    parser.add_argument("--no-auto-start", action="store_true", help="Do not auto-start llama-server when the server is unavailable.")
    parser.add_argument("--show-timings", action="store_true", help="Print prompt/generation timing details.")
    parser.add_argument("--show-payload", action="store_true", help="Print the final request payload before sending it.")
    parser.add_argument("--out", type=Path, help="Optional JSON file for the full response payload.")
    return parser


def json_request(
    url: str,
    payload: dict[str, Any] | None = None,
    *,
    method: str = "POST",
    timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS,
) -> tuple[int, dict[str, Any]]:
    body = None if payload is None else json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = request.Request(
        url,
        data=body,
        headers={"Content-Type": "application/json"},
        method=method,
    )
    try:
        with request.urlopen(req, timeout=timeout_seconds) as response:
            text = response.read().decode("utf-8")
            data = json.loads(text) if text else {}
            return response.status, data
    except error.HTTPError as exc:
        text = exc.read().decode("utf-8")
        try:
            payload = json.loads(text) if text else {}
        finally:
            exc.close()
        return exc.code, payload


def server_models_url(server_url: str) -> str:
    parsed = parse.urlsplit(server_url)
    base_path = parsed.path
    if "/v1/" in base_path:
        prefix, _, _ = base_path.partition("/v1/")
        new_path = f"{prefix}/v1/models"
    else:
        new_path = "/v1/models"
    return parse.urlunsplit((parsed.scheme, parsed.netloc, new_path, "", ""))


def server_is_ready(server_url: str, *, timeout_seconds: float = 3.0) -> bool:
    try:
        status, _ = json_request(server_models_url(server_url), None, method="GET", timeout_seconds=timeout_seconds)
    except OSError:
        return False
    return status == 200


def infer_llama_model_preset(server_model: str) -> str:
    lowered = server_model.lower()
    if "7b" in lowered:
        return "qwen2.5-7b"
    return "qwen2.5-3b"


def start_local_server(*, server_model: str) -> ServerHandle:
    runtime_dir = DEFAULT_RUNTIME_DIR
    runtime_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y-%m-%dT%H-%M-%S")
    log_path = runtime_dir / f"llama-server-{stamp}.log"
    log_handle = log_path.open("w", encoding="utf-8")
    env = dict(os.environ)
    env["MIRA_LIGHT_LLAMA_MODEL"] = infer_llama_model_preset(server_model)
    env["MIRA_LIGHT_LLAMA_MODEL_FILE"] = server_model
    env.setdefault("MIRA_LIGHT_LLAMA_GPU_LAYERS", "0")
    process = subprocess.Popen(
        ["bash", str(ROOT / "scripts" / "run_llama_cpp_server.sh")],
        stdout=log_handle,
        stderr=subprocess.STDOUT,
        text=True,
        start_new_session=True,
        cwd=str(ROOT),
        env=env,
    )
    return ServerHandle(process=process, log_path=log_path)


def wait_for_server(server_url: str, *, timeout_seconds: float) -> None:
    deadline = time.monotonic() + timeout_seconds
    while time.monotonic() < deadline:
        if server_is_ready(server_url):
            return
        time.sleep(1.0)
    raise SystemExit(f"Timed out waiting for local llama-server at {server_url}")


def build_request_payload(args: argparse.Namespace) -> dict[str, Any]:
    class PromptArgs:
        workspace_root = args.workspace_root
        user_message = args.message
        model = args.server_model
        state_json = args.state_json
        memory_snippet = args.memory_snippet
        history_json = args.history_json

    payload = build_payload(PromptArgs)
    payload["model"] = args.server_model
    payload["temperature"] = args.temperature
    payload["max_tokens"] = args.max_tokens
    payload["stream"] = False
    return payload


def extract_assistant_text(response_payload: dict[str, Any]) -> str:
    choices = response_payload.get("choices")
    if not isinstance(choices, list) or not choices:
        raise SystemExit(f"Unexpected response payload: {json.dumps(response_payload, ensure_ascii=False)}")
    message = choices[0].get("message") or {}
    content = str(message.get("content") or "").strip()
    if not content:
        raise SystemExit(f"Assistant response was empty: {json.dumps(response_payload, ensure_ascii=False)}")
    return content


def main() -> int:
    args = build_parser().parse_args()

    started_handle: ServerHandle | None = None
    if not server_is_ready(args.server_url):
        if args.no_auto_start:
            raise SystemExit(f"Local llama-server is not reachable at {args.server_url}")
        started_handle = start_local_server(server_model=args.server_model)
        print(f"[server] started local llama-server, log: {started_handle.log_path}")
        wait_for_server(args.server_url, timeout_seconds=args.startup_timeout_seconds)
        print("[server] ready")

    payload = build_request_payload(args)
    if args.show_payload:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        print("")

    status, response_payload = json_request(
        args.server_url,
        payload,
        timeout_seconds=args.timeout_seconds,
    )
    if status != 200:
        raise SystemExit(f"Local Qwen request failed (HTTP {status}): {json.dumps(response_payload, ensure_ascii=False)}")

    if args.out:
        out_path = args.out.expanduser().resolve()
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(response_payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(extract_assistant_text(response_payload))
    if args.show_timings:
        timings = response_payload.get("timings") or {}
        usage = response_payload.get("usage") or {}
        if timings or usage:
            print("")
            print(json.dumps({"usage": usage, "timings": timings}, ensure_ascii=False, indent=2))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
