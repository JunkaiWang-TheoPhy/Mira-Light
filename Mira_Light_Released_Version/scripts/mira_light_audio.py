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

PRESET_SPEECH_ASSETS: dict[str, str] = {
    "当 Mira 感觉到有人靠近，它不会立刻机械转头，而是像刚醒的小动物一样慢慢睁眼、抖一抖、伸个懒腰。": "speech/wake_up_host.aiff",
    "Mira 不会机械地直接盯着你，它会先试探着转过去一半，停一下，再歪头看你。": "speech/curious_observe_host.aiff",
    "你可以摸摸它。它会主动靠过来，不只是响应动作，而是在表达亲近。": "speech/touch_affection_host.aiff",
    "它会像小狗一样歪头研究你，有时还会探头一下又缩回去。": "speech/cute_probe_host.aiff",
    "它不会一直表演，它也会像人一样走神，盯着某个方向发一会儿呆。": "speech/daydream_host.aiff",
    "如果你坐太久，它不会直接警报，而是会像宠物一样蹭蹭你，提醒你起来动一动。": "speech/standup_reminder_host.aiff",
    "你试着在桌上移动这本书，它会一直跟着书看，这一段是用来证明它真的看得见。": "speech/track_target_host.aiff",
    "当它收到一个超级开心的消息时，它会像真的高兴一样跳起来。": "speech/celebrate_host.aiff",
    "当你离开时，它会目送你，还会轻轻摆摆头像在说再见。": "speech/farewell_host.aiff",
    "当人离开后，它会慢慢收回自己，回到休息状态，等下一个人来。": "speech/sleep_host.aiff",
    "你对着它叹一口气，它就会像听懂了一样看你一下，光也会变暖。": "speech/sigh_demo_host.aiff",
    "如果同时有两个人，它会短暂纠结，不知道该先看谁，最后才选定一个。": "speech/multi_person_demo_host.aiff",
    "你只要说一句‘今天好累啊’，它就会用动作和灯光告诉你：它听懂了。": "speech/voice_demo_tired_host.aiff",
    "太好了，我们来庆祝一下！": "speech/celebrate_line.aiff",
    "谢谢你来看我，下次见。": "speech/farewell_line.aiff",
    "我在呢，慢一点也没关系。": "speech/sigh_demo_line.aiff",
    "辛苦了，要不要先休息一下？": "speech/voice_demo_tired_line.aiff",
    "谢谢你，我有点开心。": "speech/thank_you_happy_line.aiff",
    "我会再努力一点。": "speech/try_harder_line.aiff",
}
DEFAULT_MIRA_TTS_MODE = "gentle_sister"
DEFAULT_MIRA_TTS_LANG = "zh-CN"
VOICE_PRESETS: dict[str, dict[str, str]] = {
    "gentle_sister": {
        "voice": "zh-CN-XiaoyiNeural",
        "lang": DEFAULT_MIRA_TTS_LANG,
        "rate": "-12%",
        "pitch": "-20%",
    },
    "warm_gentleman": {
        "voice": "zh-CN-YunxiNeural",
        "lang": DEFAULT_MIRA_TTS_LANG,
        "rate": "-6%",
        "pitch": "-6%",
    },
}
VOICE_MODE_ALIASES = {
    "female": "gentle_sister",
    "male": "warm_gentleman",
    "tts": DEFAULT_MIRA_TTS_MODE,
    "default": DEFAULT_MIRA_TTS_MODE,
    "narration": DEFAULT_MIRA_TTS_MODE,
    "host": DEFAULT_MIRA_TTS_MODE,
    "": DEFAULT_MIRA_TTS_MODE,
}

PREPARE_COMMAND_CANDIDATES = [
    "speaker-preferred-use",
    "speaker-hp-use",
    "speaker-beosound-use",
    "speaker-builtin-use",
]

PLAY_COMMAND_CANDIDATES = [
    "speaker-preferred-play",
    "speaker-hp-play",
    "speaker-beosound-play",
    "speaker-builtin-play",
    "afplay",
]

TTS_PLAY_COMMAND_CANDIDATES = [
    "speaker-preferred-tts-play",
    "speaker-hp-tts-play",
    "speaker-beosound-tts-play",
    "speaker-builtin-tts-play",
]

OPENCLAW_TTS_PLAY_COMMAND_CANDIDATES = [
    "speaker-preferred-openclaw-tts-play",
    "speaker-hp-openclaw-tts-play",
    "speaker-beosound-openclaw-tts-play",
    "speaker-builtin-openclaw-tts-play",
]

SAY_COMMAND_CANDIDATES = [
    "speaker-preferred-say",
    "speaker-hp-say",
    "speaker-beosound-say",
    "speaker-builtin-say",
    "say",
]


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

    def _find_first_command(self, candidates: list[str]) -> str | None:
        for candidate in candidates:
            found = self._find_command(candidate)
            if found:
                return found
        return None

    def _resolve_prepare_command(self) -> list[str] | None:
        raw = os.environ.get("MIRA_LIGHT_AUDIO_PREPARE_CMD", "").strip()
        if raw:
            return shlex.split(raw)

        if not _truthy(os.environ.get("MIRA_LIGHT_AUDIO_PREPARE_ENABLED"), default=True):
            return None

        preferred = self._find_first_command(PREPARE_COMMAND_CANDIDATES)
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

    def _resolve_preset_speech_asset(self, text: str) -> tuple[str, Path] | None:
        asset_name = PRESET_SPEECH_ASSETS.get(text)
        if not asset_name:
            return None
        asset_path = self._resolve_asset_path(asset_name)
        if asset_path is None:
            return None
        return asset_name, asset_path

    def _ensure_output_ready(self) -> None:
        if self._output_prepared or not self.prepare_command:
            return
        self._run(self.prepare_command, wait=True, description="prepare-output")
        self._output_prepared = True

    def prepare_output(self) -> dict[str, Any]:
        if self._output_prepared:
            return {"ok": True, "skipped": True, "reason": "already-prepared"}
        if not self.prepare_command:
            return {"ok": True, "skipped": True, "reason": "no-prepare-command"}
        result = self._run(self.prepare_command, wait=True, description="prepare-output")
        self._output_prepared = True
        return result

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
        player = self._find_first_command(PLAY_COMMAND_CANDIDATES)
        if player:
            return [player, str(asset_path)]

        if self.dry_run:
            return ["play-asset", str(asset_path)]

        raise RuntimeError(
            "No local audio playback command found "
            "(expected speaker-hp-play, speaker-beosound-play, speaker-builtin-play, or afplay)"
        )

    def _resolve_voice_mode(self, requested: str) -> str:
        normalized = (requested or "").strip().lower()
        if normalized in VOICE_PRESETS:
            return normalized
        alias = VOICE_MODE_ALIASES.get(normalized)
        if alias:
            return alias
        if normalized in {"tts", "default", "narration", "host", ""}:
            configured = os.environ.get("MIRA_LIGHT_TTS_MODE", DEFAULT_MIRA_TTS_MODE).strip().lower()
            resolved_configured = VOICE_MODE_ALIASES.get(configured, configured)
            if resolved_configured in VOICE_PRESETS:
                return resolved_configured
            return DEFAULT_MIRA_TTS_MODE
        return normalized

    def _resolve_tts_profile(self, requested: str) -> dict[str, str] | None:
        mode = self._resolve_voice_mode(requested)
        preset = VOICE_PRESETS.get(mode)
        if preset is None:
            return None
        return {
            "mode": mode,
            "voice": os.environ.get("MIRA_LIGHT_TTS_VOICE", preset["voice"]).strip() or preset["voice"],
            "lang": os.environ.get("MIRA_LIGHT_TTS_LANG", preset["lang"]).strip() or preset["lang"],
            "rate": os.environ.get("MIRA_LIGHT_TTS_RATE", preset["rate"]).strip() or preset["rate"],
            "pitch": os.environ.get("MIRA_LIGHT_TTS_PITCH", preset["pitch"]).strip() or preset["pitch"],
        }

    def _build_speech_command(self, text: str, *, voice: str) -> list[str]:
        requested = self._resolve_voice_mode(voice)

        if requested == "openclaw":
            command = self._find_first_command(OPENCLAW_TTS_PLAY_COMMAND_CANDIDATES)
            if command:
                return [command, text]

        profile = self._resolve_tts_profile(requested)
        if profile is not None:
            preferred_tts = self._find_first_command(TTS_PLAY_COMMAND_CANDIDATES)
            if preferred_tts:
                return [
                    preferred_tts,
                    "--voice",
                    profile["voice"],
                    "--lang",
                    profile["lang"],
                    "--rate",
                    profile["rate"],
                    "--pitch",
                    profile["pitch"],
                    text,
                ]

            command = self._find_first_command(
                [*OPENCLAW_TTS_PLAY_COMMAND_CANDIDATES, *SAY_COMMAND_CANDIDATES]
            )
            if command:
                return [command, text]

        if requested == "say":
            command = self._find_first_command(SAY_COMMAND_CANDIDATES)
            if command:
                return [command, text]

        if self.dry_run:
            return [f"speech:{requested or 'tts'}", text]

        raise RuntimeError(
            "No local speech command found "
            "(expected HP/Beosound/Built-in TTS helpers or say)"
        )

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

        preset_asset = self._resolve_preset_speech_asset(spoken_text)
        if preset_asset is not None:
            asset_name, asset_path = preset_asset
            self._ensure_output_ready()
            command = self._build_play_command(asset_path)
            result = self._run(command, wait=wait, description=f"speech-asset:{asset_path.name}")
            result["requestedText"] = cleaned
            result["spokenText"] = spoken_text
            result["presetAsset"] = asset_name
            return result

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
