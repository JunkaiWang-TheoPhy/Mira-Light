#!/usr/bin/env python3
"""Local audio helpers for Mira Light booth scenes."""

from __future__ import annotations

import os
from pathlib import Path
import shlex
import shutil
import subprocess
from typing import Any, Callable

from mira_name_aliases import normalize_public_speech_text

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_ASSET_DIRS = [
    ROOT / "assets" / "audio",
    ROOT / "web" / "assets" / "audio",
    ROOT / "runtime" / "audio",
    Path.home() / "Music" / "Mira-Light",
]

SYSTEM_FALLBACK_ASSETS: dict[str, list[Path]] = {
    "dance.mp3": [
        Path("/System/Library/Sounds/Hero.aiff"),
        Path("/System/Library/Sounds/Funk.aiff"),
        Path("/System/Library/Sounds/Glass.aiff"),
    ]
}


def _truthy(value: str | None, *, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


class AudioCuePlayer:
    """Play booth cue audio through the preferred local speaker path when available."""

    def __init__(self, *, emit: Callable[[str], None] | None = None, dry_run: bool = False):
        self.emit = emit or print
        self.dry_run = dry_run
        self._active_processes: list[subprocess.Popen[str]] = []
        self._output_prepared = False

        self.asset_dirs = self._resolve_asset_dirs()
        self.prepare_command = self._resolve_prepare_command()

    def _log(self, message: str) -> None:
        self.emit(message)

    def _resolve_asset_dirs(self) -> list[Path]:
        extra_dirs = []
        raw = os.environ.get("MIRA_LIGHT_AUDIO_DIRS", "").strip()
        if raw:
            for item in raw.split(os.pathsep):
                item = item.strip()
                if item:
                    extra_dirs.append(Path(os.path.expanduser(item)))

        seen: set[str] = set()
        resolved: list[Path] = []
        for directory in [*extra_dirs, *DEFAULT_ASSET_DIRS]:
            key = str(directory)
            if key in seen:
                continue
            seen.add(key)
            resolved.append(directory)
        return resolved

    def _find_command(self, name: str) -> str | None:
        if not name:
            return None

        if os.sep in name:
            path = Path(os.path.expanduser(name))
            if path.is_file():
                return str(path)

        found = shutil.which(name)
        if found:
            return found

        local_bin = Path.home() / ".local" / "bin" / name
        if local_bin.is_file():
            return str(local_bin)
        return None

    def _resolve_prepare_command(self) -> list[str] | None:
        raw = os.environ.get("MIRA_LIGHT_AUDIO_PREPARE_CMD", "").strip()
        if raw:
            return shlex.split(raw)

        if not _truthy(os.environ.get("MIRA_LIGHT_AUDIO_PREPARE_ENABLED"), default=True):
            return None

        preferred = self._find_command("speaker-hp-use")
        if preferred:
            return [preferred]
        return None

    def _resolve_asset_path(self, name: str, fallback_asset: str | None = None) -> Path | None:
        candidates: list[Path] = []

        direct = Path(os.path.expanduser(name))
        if direct.is_file():
            return direct

        for directory in self.asset_dirs:
            path = directory / name
            candidates.append(path)
            if path.is_file():
                return path

        if fallback_asset:
            fallback = Path(os.path.expanduser(fallback_asset))
            if fallback.is_file():
                return fallback

        for fallback in SYSTEM_FALLBACK_ASSETS.get(name, []):
            if fallback.is_file():
                return fallback

        return None

    def _ensure_output_ready(self) -> None:
        if self._output_prepared or not self.prepare_command:
            return
        self._run(self.prepare_command, wait=True, description="prepare-output")
        self._output_prepared = True

    def _run(self, command: list[str], *, wait: bool, description: str) -> dict[str, Any]:
        if self.dry_run:
            self._log(f"[audio-dry-run] {description} -> {' '.join(command)}")
            return {"ok": True, "dryRun": True, "command": command, "description": description}

        self._log(f"[audio] {description} -> {' '.join(command)}")
        if wait:
            completed = subprocess.run(command, check=True, capture_output=True, text=True)
            return {
                "ok": True,
                "command": command,
                "description": description,
                "stdout": completed.stdout.strip(),
                "stderr": completed.stderr.strip(),
            }

        process = subprocess.Popen(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, text=True)
        self._active_processes.append(process)
        return {"ok": True, "command": command, "description": description, "pid": process.pid}

    def _build_play_command(self, asset_path: Path) -> list[str]:
        player = self._find_command("speaker-hp-play")
        if player:
            return [player, str(asset_path)]

        player = self._find_command("afplay")
        if player:
            return [player, str(asset_path)]

        raise RuntimeError("No local audio playback command found (expected speaker-hp-play or afplay)")

    def _build_speech_command(self, text: str, *, voice: str) -> list[str]:
        requested = (voice or "tts").strip().lower()

        if requested == "openclaw":
            command = self._find_command("speaker-hp-openclaw-tts-play")
            if command:
                return [command, text]

        if requested in {"tts", "default", "narration", "host"}:
            for name in ("speaker-hp-tts-play", "speaker-hp-openclaw-tts-play", "speaker-hp-say", "say"):
                command = self._find_command(name)
                if command:
                    return [command, text]

        if requested == "say":
            for name in ("speaker-hp-say", "say"):
                command = self._find_command(name)
                if command:
                    return [command, text]

        raise RuntimeError("No local speech command found (expected speaker-hp-tts-play, speaker-hp-say, or say)")

    def play_asset(
        self,
        name: str,
        *,
        wait: bool = False,
        allow_missing: bool = True,
        fallback_asset: str | None = None,
    ) -> dict[str, Any]:
        asset_path = self._resolve_asset_path(name, fallback_asset=fallback_asset)
        if asset_path is None:
            if allow_missing:
                self._log(f"[audio-skip] missing asset={name}")
                return {"ok": False, "skipped": True, "reason": "missing-asset", "name": name}
            raise RuntimeError(f"Audio asset not found: {name}")

        self._ensure_output_ready()
        command = self._build_play_command(asset_path)
        return self._run(command, wait=wait, description=f"asset:{asset_path.name}")

    def speak_text(self, text: str, *, voice: str = "tts", wait: bool = True) -> dict[str, Any]:
        cleaned = text.strip()
        if not cleaned:
            self._log("[audio-skip] empty text")
            return {"ok": False, "skipped": True, "reason": "empty-text"}

        spoken_text = normalize_public_speech_text(cleaned)
        if spoken_text != cleaned:
            self._log(f"[audio-normalized] {cleaned} -> {spoken_text}")

        self._ensure_output_ready()
        command = self._build_speech_command(spoken_text, voice=voice)
        result = self._run(command, wait=wait, description=f"speech:{voice}")
        result["requestedText"] = cleaned
        result["spokenText"] = spoken_text
        return result

    def play_step(self, step: dict[str, Any]) -> dict[str, Any]:
        text = str(step.get("text") or "").strip()
        name = str(step.get("name") or step.get("asset") or "").strip()
        wait = bool(step.get("wait", bool(text)))

        if text:
            return self.speak_text(text, voice=str(step.get("voice") or "tts"), wait=wait)
        if name:
            return self.play_asset(
                name,
                wait=wait,
                allow_missing=bool(step.get("allowMissing", True)),
                fallback_asset=step.get("fallbackAsset"),
            )
        raise RuntimeError("Audio step requires either text or asset name")

    def stop_all(self) -> None:
        while self._active_processes:
            process = self._active_processes.pop()
            if process.poll() is not None:
                continue
            try:
                process.terminate()
                process.wait(timeout=1.0)
                self._log(f"[audio-stop] pid={process.pid}")
            except Exception:
                try:
                    process.kill()
                except Exception:
                    pass
