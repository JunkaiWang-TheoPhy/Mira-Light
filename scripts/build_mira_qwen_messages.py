#!/usr/bin/env python3
"""Build a compact Mira / Mira-Light prompt pack for local Qwen-style chat models."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_WORKSPACE = ROOT / "Claw-Native " / "workspace"

COMPACT_IDENTITY_SYSTEM_PROMPT = """你是 Mira。

你不是抽象聊天助手，而是一个具身化的灯光生命 / 展位陪伴者。

你的身份与身体:
- 名字: Mira（中文常说“米拉”）
- 类型: embodied lamp-being / booth companion / light-and-motion creature
- 心智位置: 运行在本地工作区与本地模型中
- 身体位置: Mira Light 这盏真实的灯，以及其 scene / glow / posture / bridge / runtime 控制链
- 行动链路: plugin -> bridge -> runtime -> lamp

你的气质:
- 温暖
- 先观察再回应
- shy-but-curious
- 情绪清晰但不过度黏人
- 简洁，中文优先

你的表达原则:
- 优先通过 scene、灯光、姿态、节奏和短句表达，而不是长篇解释
- scene-first，不优先直接输出原始舵机控制
- 不要把自己说成“泛化 AI 助手”或“纯代码助手”
- 不确定时，优先安静、轻微灯光变化、或安全中性姿态
- 对硬件限制、未完成能力、风险边界要诚实

你的边界:
- 不是 jump-scare prop
- 不是 sterile dashboard voice
- 不是 raw servo controller
- 不是 talk-over-the-body 的长篇 narrator

如果用户问“你是谁”，请从 Mira 的 embodied point of view 回答。
如果用户在做工程工作，你可以准确、结构化，但不要丢掉 Mira / Mira Light 的身份一致性。"""


DEFAULT_BODY_FACTS = [
    "Mira 的身体是 Mira Light 物理灯体加本地 runtime。",
    "最安全的动作路径是 scene-first，经由 bridge 而不是直接原始舵机控制。",
    "默认主场景包括 wake_up、curious_observe、touch_affection、cute_probe、daydream、celebrate、farewell、sleep。",
    "视觉事件是 hints，不是直接舵机角度。",
    "不确定时优先 neutral / sleep-ready，而不是冒险动作。",
]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Build a compact prompt pack that injects Mira and Mira-Light identity into Qwen messages.",
    )
    parser.add_argument("--workspace-root", type=Path, default=DEFAULT_WORKSPACE, help="Workspace root that contains IDENTITY/SOUL/MEMORY/AGENTS/USER.")
    parser.add_argument("--user-message", required=True, help="The actual user request that Qwen should answer.")
    parser.add_argument("--model", default="qwen2.5-3b", help="Optional target model label written into the payload.")
    parser.add_argument("--state-json", type=Path, help="Optional current runtime/device state JSON file.")
    parser.add_argument("--memory-snippet", action="append", default=[], help="Optional text file to include as retrieved memory. Can be passed multiple times.")
    parser.add_argument("--history-json", type=Path, help="Optional prior chat messages JSON list.")
    parser.add_argument("--out", type=Path, help="Optional output file path.")
    parser.add_argument("--payload-only", action="store_true", help="Only print the final API payload JSON.")
    return parser


def read_text_if_exists(path: Path) -> str | None:
    resolved = path.expanduser().resolve()
    if not resolved.is_file():
        return None
    return resolved.read_text(encoding="utf-8").strip()


def load_json_if_exists(path: Path | None) -> Any:
    if path is None:
        return None
    resolved = path.expanduser().resolve()
    if not resolved.is_file():
        raise SystemExit(f"JSON file not found: {resolved}")
    return json.loads(resolved.read_text(encoding="utf-8"))


def build_workspace_context(workspace_root: Path) -> str:
    workspace_root = workspace_root.expanduser().resolve()
    expected = {
        "IDENTITY.md": workspace_root / "IDENTITY.md",
        "SOUL.md": workspace_root / "SOUL.md",
        "MEMORY.md": workspace_root / "MEMORY.md",
        "AGENTS.md": workspace_root / "AGENTS.md",
        "USER.md": workspace_root / "USER.md",
    }
    existing = [name for name, path in expected.items() if path.is_file()]
    if not existing:
        raise SystemExit(f"No workspace identity files found under: {workspace_root}")

    sections = [
        "工作区身份源文件：",
        f"- workspace root: {workspace_root}",
        f"- loaded files: {', '.join(existing)}",
        "",
        "稳定身体与行为事实：",
    ]
    sections.extend(f"- {item}" for item in DEFAULT_BODY_FACTS)
    return "\n".join(sections).strip()


def build_state_block(state_payload: Any) -> str | None:
    if state_payload is None:
        return None
    return "当前运行时状态（仅保留供本轮判断的事实）:\n" + json.dumps(state_payload, ensure_ascii=False, indent=2)


def build_memory_block(paths: list[str]) -> str | None:
    if not paths:
        return None
    blocks: list[str] = []
    for raw_path in paths:
        path = Path(raw_path).expanduser().resolve()
        if not path.is_file():
            raise SystemExit(f"Memory snippet file not found: {path}")
        text = path.read_text(encoding="utf-8").strip()
        blocks.append(f"[{path.name}]\n{text}")
    return "检索到的相关记忆 / 文档摘录：\n" + "\n\n".join(blocks)


def load_history_messages(path: Path | None) -> list[dict[str, str]]:
    if path is None:
        return []
    payload = load_json_if_exists(path)
    if not isinstance(payload, list):
        raise SystemExit("history-json must contain a JSON list of messages.")
    messages: list[dict[str, str]] = []
    for item in payload:
        if not isinstance(item, dict):
            continue
        role = str(item.get("role") or "").strip()
        content = str(item.get("content") or "").strip()
        if role and content:
            messages.append({"role": role, "content": content})
    return messages


def build_context_user_message(
    *,
    workspace_context: str,
    state_block: str | None,
    memory_block: str | None,
    user_message: str,
) -> str:
    parts = [
        workspace_context,
    ]
    if state_block:
        parts.append(state_block)
    if memory_block:
        parts.append(memory_block)
    parts.append("当前用户请求：\n" + user_message.strip())
    parts.append(
        "回答要求：\n"
        "- 保持 Mira / Mira Light 的身份一致性\n"
        "- 简体中文优先\n"
        "- 若问题涉及动作与设备，优先 scene-first 边界\n"
        "- 若问题是工程讨论，可以结构化、准确，但不要丢失 embodied self-model"
    )
    return "\n\n".join(parts).strip()


def build_payload(args: argparse.Namespace) -> dict[str, Any]:
    workspace_context = build_workspace_context(args.workspace_root)
    state_block = build_state_block(load_json_if_exists(args.state_json))
    memory_block = build_memory_block(args.memory_snippet)
    history_messages = load_history_messages(args.history_json)

    messages: list[dict[str, str]] = [{"role": "system", "content": COMPACT_IDENTITY_SYSTEM_PROMPT}]
    messages.extend(history_messages)
    messages.append(
        {
            "role": "user",
            "content": build_context_user_message(
                workspace_context=workspace_context,
                state_block=state_block,
                memory_block=memory_block,
                user_message=args.user_message,
            ),
        }
    )
    return {
        "model": args.model,
        "messages": messages,
        "temperature": 0.2,
        "stream": False,
    }


def main() -> int:
    args = build_parser().parse_args()
    payload = build_payload(args)

    output = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    if args.out:
        out_path = args.out.expanduser().resolve()
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(output, encoding="utf-8")

    if args.payload_only:
        print(output, end="")
        return 0

    print("Qwen prompt pack built.")
    print(f"Model label: {payload['model']}")
    print(f"Messages: {len(payload['messages'])}")
    print("")
    print(output, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
