#!/usr/bin/env python3
"""Run a short local smoke test against a downloaded llama.cpp GGUF model."""

from __future__ import annotations

import argparse
from pathlib import Path
import platform
import shutil
import subprocess
import sys

from download_llama_cpp_model import MODEL_PRESETS, default_model_root, resolve_entry_filename


DEFAULT_PROMPT = "请用中文用两句话介绍你自己，并说明你可以如何帮助 Mira Light。"


def resolve_model_dir(args: argparse.Namespace) -> Path:
    if args.model_dir:
        return Path(args.model_dir).expanduser()
    preset = MODEL_PRESETS[args.model]
    return default_model_root() / Path(str(preset["repo"])).name


def resolve_default_model_files(model_name: str) -> tuple[str, ...]:
    preset = MODEL_PRESETS[model_name]
    quant = str(preset["default_quant"])
    base_name = str(preset["base_name"])
    if model_name == "qwen2.5-3b":
        return (f"{base_name}-{quant}.gguf",)
    if model_name == "qwen2.5-7b":
        return (
            f"{base_name}-{quant}-00001-of-00002.gguf",
            f"{base_name}-{quant}-00002-of-00002.gguf",
        )
    raise SystemExit(f"Unsupported model preset: {model_name}")


def resolve_model_file(args: argparse.Namespace, model_dir: Path) -> Path:
    if args.model_file:
        return model_dir / args.model_file
    default_entry = resolve_entry_filename(resolve_default_model_files(args.model))
    return model_dir / default_entry


def find_llama_binary(binary_name: str) -> str:
    direct = shutil.which(binary_name)
    if direct:
        return direct

    brew_prefix = shutil.which("brew")
    if brew_prefix:
        try:
            prefix = subprocess.check_output([brew_prefix, "--prefix"], text=True).strip()
        except subprocess.SubprocessError:
            prefix = ""
        if prefix:
            candidate = Path(prefix) / "bin" / binary_name
            if candidate.is_file():
                return str(candidate)

    fallback_root = Path.home() / ".openclaw" / "mira-light-llama.cpp" / "build" / "bin" / binary_name
    if fallback_root.is_file():
        return str(fallback_root)

    raise SystemExit(
        f"{binary_name} was not found.\n"
        "Run `bash scripts/setup_llama_cpp_env.sh` first."
    )


def default_gpu_layers() -> int:
    version = platform.mac_ver()[0]
    major = int(version.split(".", 1)[0]) if version else 0
    return 0 if major and major < 14 else 999


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Load a local GGUF model with llama.cpp and run a short smoke test.")
    parser.add_argument("--model", default="qwen2.5-3b", choices=sorted(MODEL_PRESETS), help="Model preset to resolve.")
    parser.add_argument("--model-dir", help="Explicit path to the downloaded GGUF model directory.")
    parser.add_argument("--model-file", help="Explicit GGUF file to load. Use the first shard for split models.")
    parser.add_argument("--prompt", default=DEFAULT_PROMPT, help="User prompt for the smoke test.")
    parser.add_argument("--max-tokens", type=int, default=96, help="Maximum tokens for the smoke response.")
    parser.add_argument("--threads", type=int, default=8, help="CPU threads for llama.cpp.")
    parser.add_argument("--n-gpu-layers", type=int, default=default_gpu_layers(), help="GPU layers for llama.cpp.")
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    model_dir = resolve_model_dir(args)
    if not model_dir.is_dir():
        raise SystemExit(
            f"Model directory not found: {model_dir}\n"
            "Download it first with: python3 scripts/download_llama_cpp_model.py --model "
            f"{args.model}"
        )

    model_file = resolve_model_file(args, model_dir)
    if not model_file.is_file():
        raise SystemExit(
            f"GGUF file not found: {model_file}\n"
            "Run the downloader again or pass --model-file explicitly."
        )

    llama_cli = find_llama_binary("llama-cli")
    command = [
        llama_cli,
        "-m",
        str(model_file),
        "-p",
        args.prompt,
        "-n",
        str(args.max_tokens),
        "-t",
        str(args.threads),
        "-ngl",
        str(args.n_gpu_layers),
        "--no-display-prompt",
    ]

    print(f"[smoke] llama-cli: {llama_cli}")
    print(f"[smoke] model: {model_file}")
    print(f"[smoke] gpu layers: {args.n_gpu_layers}")
    print("[smoke] generating...\n")
    result = subprocess.run(command, check=False)
    return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())
