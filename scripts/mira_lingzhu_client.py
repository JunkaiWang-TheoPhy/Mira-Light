#!/usr/bin/env python3
"""HTTP client helpers for the remote Mira Lingzhu live adapter."""

from __future__ import annotations

from datetime import datetime
import json
from typing import Any
import urllib.error
import urllib.request


def normalize_string_list(value: str | list[str] | tuple[str, ...] | None) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        raw_items = value.split(",")
    else:
        raw_items = list(value)

    items: list[str] = []
    for raw in raw_items:
        text = str(raw).strip()
        if text and text not in items:
            items.append(text)
    return items


def _post_json(base_url: str, path: str, payload: dict[str, Any], *, auth_ak: str, timeout_seconds: int) -> dict[str, Any]:
    request = urllib.request.Request(
        f"{base_url.rstrip('/')}{path}",
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={
            "Content-Type": "application/json; charset=utf-8",
            **({"Authorization": f"Bearer {auth_ak}"} if auth_ak else {}),
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
            raw = response.read().decode("utf-8").strip()
            return json.loads(raw) if raw else {"ok": True}
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace").strip()
        raise RuntimeError(f"Lingzhu HTTP {exc.code} calling {path}: {detail}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"Lingzhu request failed: {exc}") from exc


def _message_items(messages: list[dict[str, str]]) -> list[dict[str, str]]:
    items: list[dict[str, str]] = []
    for message in messages:
        role = str(message.get("role") or "user").strip() or "user"
        content = str(message.get("content") or "").strip()
        if not content:
            continue
        items.append({"role": role, "type": "text", "text": content})
    return items


def send_via_lingzhu_messages(
    messages: list[dict[str, str]],
    *,
    base_url: str,
    auth_ak: str,
    agent_id: str,
    user_id: str,
    session_id: str,
    additional_user_ids: str | list[str] | tuple[str, ...] | None,
    timeout_seconds: int,
) -> tuple[str, dict[str, Any]]:
    if not base_url.strip():
        raise RuntimeError("Lingzhu base URL is required")
    if not auth_ak.strip():
        raise RuntimeError("Lingzhu auth AK is required")

    normalized_additional_user_ids = normalize_string_list(additional_user_ids)
    payload = _post_json(
        base_url,
        "/v1/chat",
        {
            "agent_id": agent_id,
            "user_id": user_id,
            "session_id": session_id,
            "message_id": f"mira-light-{datetime.now().strftime('%Y%m%d%H%M%S%f')}",
            "additional_user_ids": normalized_additional_user_ids,
            "disable_default_additional_user_ids": len(normalized_additional_user_ids) == 0,
            "message": _message_items(messages),
        },
        auth_ak=auth_ak,
        timeout_seconds=timeout_seconds,
    )
    text = str(payload.get("text") or "").strip()
    upstream = payload.get("upstream") if isinstance(payload.get("upstream"), dict) else {}
    return text, {
        "provider": "lingzhu-live-adapter",
        "model": str(upstream.get("model") or ""),
        "agent": agent_id,
        "userId": user_id,
        "sessionId": session_id,
        "additionalUserIds": normalized_additional_user_ids,
        "payload": payload,
    }
