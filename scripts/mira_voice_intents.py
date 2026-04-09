#!/usr/bin/env python3
"""Shared voice-intent helpers for Mira Light speech pipelines."""

from __future__ import annotations

from typing import Any


INTENT_KEYWORDS: dict[str, tuple[str, ...]] = {
    "comfort": ("好累", "累死", "很累", "今天好累", "辛苦", "难受", "不舒服", "烦", "委屈"),
    "farewell": ("拜拜", "再见", "我走了", "先走了", "下次见", "回头见"),
    "praise": ("好可爱", "可爱", "喜欢你", "真好看", "好漂亮", "真漂亮"),
    "criticism": ("不好看", "不可爱", "不喜欢你", "你表现不好", "你今天不太行", "你今天有点不太行", "一般般", "有点失望"),
}

SIGH_KEYWORDS = {
    "唉",
    "哎",
    "唉呀",
    "哎呀",
    "唉...",
    "哎...",
    "唉……",
    "哎……",
}

INTENT_ACTIONS: dict[str, dict[str, str]] = {
    "sigh": {"type": "trigger", "name": "sigh_detected"},
    "comfort": {"type": "trigger", "name": "voice_tired"},
    "farewell": {"type": "trigger", "name": "farewell_detected"},
    "praise": {"type": "trigger", "name": "praise_detected"},
    "criticism": {"type": "trigger", "name": "criticism_detected"},
}


def _clean_text(text: str) -> str:
    return " ".join(text.strip().lower().split())


def is_sigh_text(transcript: str) -> bool:
    cleaned = _clean_text(transcript)
    if not cleaned:
        return False
    if cleaned in SIGH_KEYWORDS:
        return True
    return cleaned.rstrip("!！?？。,.，") in {"唉", "哎", "唉呀", "哎呀"}


def classify_intent(transcript: str) -> str:
    cleaned = _clean_text(transcript)
    if not cleaned:
        return "chat"
    if is_sigh_text(cleaned):
        return "sigh"
    for intent, keywords in INTENT_KEYWORDS.items():
        if any(keyword in cleaned for keyword in keywords):
            return intent
    return "chat"


def action_for_intent(intent: str) -> dict[str, str] | None:
    return INTENT_ACTIONS.get(intent)


def comfort_like_intent(intent: str) -> bool:
    return intent in {"sigh", "comfort"}


def bridge_payload_for_intent(intent: str, transcript: str) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "source": "voice-realtime",
        "transcript": transcript,
        "cueMode": "scene",
    }
    if intent == "farewell":
        payload["direction"] = "center"
    return payload
