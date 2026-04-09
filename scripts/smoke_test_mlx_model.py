#!/usr/bin/env python3
"""Run a short local smoke test against a downloaded MLX model."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

from download_mlx_model import MODEL_PRESETS, default_model_root, slugify_repo_id


DEFAULT_PROMPT = "请用中文用两句话介绍你自己，并说明你可以如何帮助 Mira Light。"
DEFAULT_SYSTEM_PROMPT = "你是 Mira Light 的本地中文助手，回答简洁、稳定、结构清楚。"


def resolve_model_dir(args: argparse.Namespace) -> Path:
    if args.model_dir:
        return Path(args.model_dir).expanduser()
    preset = MODEL_PRESETS[args.model]
    return default_model_root() / slugify_repo_id(preset["repo"])


def build_prompt(tokenizer: object, *, system_prompt: str | None, prompt: str) -> str:
    apply_chat_template = getattr(tokenizer, "apply_chat_template", None)
    if callable(apply_chat_template):
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        return str(apply_chat_template(messages, tokenize=False, add_generation_prompt=True))
    return prompt


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Load a local MLX model and run a short smoke test prompt.")
    parser.add_argument("--model", default="qwen2.5-3b", choices=sorted(MODEL_PRESETS), help="Model preset to resolve.")
    parser.add_argument("--model-dir", help="Explicit path to the downloaded MLX model directory.")
    parser.add_argument("--prompt", default=DEFAULT_PROMPT, help="User prompt for the smoke test.")
    parser.add_argument("--system-prompt", default=DEFAULT_SYSTEM_PROMPT, help="Optional system prompt.")
    parser.add_argument("--max-tokens", type=int, default=96, help="Maximum tokens for the smoke response.")
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    model_dir = resolve_model_dir(args)
    if not model_dir.is_dir():
        raise SystemExit(
            f"Model directory not found: {model_dir}\n"
            "Download it first with: python3 scripts/download_mlx_model.py --model "
            f"{args.model}"
        )

    try:
        from mlx_lm import generate, load
    except ImportError as exc:
        raise SystemExit(
            "mlx-lm is not installed in the current Python environment.\n"
            "Install it with: bash scripts/setup_mlx_qwen_env.sh"
        ) from exc

    model, tokenizer = load(str(model_dir))
    prompt = build_prompt(tokenizer, system_prompt=args.system_prompt, prompt=args.prompt)
    result = generate(
        model,
        tokenizer,
        prompt=prompt,
        max_tokens=args.max_tokens,
        verbose=False,
    )

    if result is None:
        return 0
    print(str(result).strip())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
