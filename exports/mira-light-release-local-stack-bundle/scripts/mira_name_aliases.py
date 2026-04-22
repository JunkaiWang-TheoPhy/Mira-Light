#!/usr/bin/env python3
"""Shared pronunciation and alias normalization helpers for Mira."""

from __future__ import annotations

import os
import re


CANONICAL_NAME = "Mira"
DEFAULT_SPOKEN_ZH_ALIAS = "米拉"
DEFAULT_SPOKEN_EN_ALIAS = "Mee-ra"

_TRANSCRIPT_ALIAS_PATTERNS: tuple[tuple[re.Pattern[str], str], ...] = (
    (re.compile(r"(?<![A-Za-z])mee[\s-]?ra(?![A-Za-z])", re.IGNORECASE), CANONICAL_NAME),
    (re.compile(r"(?<![A-Za-z])meera(?![A-Za-z])", re.IGNORECASE), CANONICAL_NAME),
    (re.compile(r"(?<![A-Za-z])mi[\s-]?ra(?![A-Za-z])", re.IGNORECASE), CANONICAL_NAME),
    (re.compile(r"米拉|咪拉|弥拉|密拉|迷拉"), CANONICAL_NAME),
)

_PUBLIC_SPEECH_NAME_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"(?<![A-Za-z])mira(?![A-Za-z])", re.IGNORECASE),
    re.compile(r"(?<![A-Za-z])mee[\s-]?ra(?![A-Za-z])", re.IGNORECASE),
)


def get_spoken_name_alias() -> str:
    alias = os.environ.get("MIRA_LIGHT_TTS_NAME_ALIAS", "").strip()
    return alias or DEFAULT_SPOKEN_ZH_ALIAS


def normalize_transcript_aliases(text: str) -> str:
    normalized = text.strip()
    for pattern, replacement in _TRANSCRIPT_ALIAS_PATTERNS:
        normalized = pattern.sub(replacement, normalized)
    return normalized


def normalize_public_speech_text(text: str) -> str:
    normalized = text.strip()
    spoken_alias = get_spoken_name_alias()
    for pattern in _PUBLIC_SPEECH_NAME_PATTERNS:
        normalized = pattern.sub(spoken_alias, normalized)
    normalized = re.sub(rf"([\u4e00-\u9fff])\s+({re.escape(spoken_alias)})", r"\1\2", normalized)
    normalized = re.sub(rf"([，。！？；：、])\s+({re.escape(spoken_alias)})", r"\1\2", normalized)
    normalized = re.sub(rf"({re.escape(spoken_alias)})\s+([，。！？；：、\u4e00-\u9fff])", r"\1\2", normalized)
    return normalized
