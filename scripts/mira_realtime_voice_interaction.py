#!/usr/bin/env python3
"""Realtime voice interaction runtime for Mira Light booth demos."""

from __future__ import annotations

import argparse
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime
import json
import math
import os
from pathlib import Path
import queue
import re
import sys
import time
from typing import Any
import urllib.error
import urllib.request

from mira_light_audio import AudioCuePlayer
from mira_name_aliases import normalize_transcript_aliases
from mira_voice_intents import action_for_intent, bridge_payload_for_intent, classify_intent, comfort_like_intent
import numpy as np
import sounddevice as sd

from openclaw_voice_to_claw import (
    DEFAULT_INITIAL_PROMPT,
    DEFAULT_LANGUAGE,
    DEFAULT_MODEL_PROFILE,
    DEFAULT_MODEL_PROFILES,
    VoiceToClawError,
    ensure_mono_float32,
    load_audio_file,
    print_input_devices,
    record_fixed_duration,
    record_push_to_talk,
    resolve_input_device,
    save_wav,
    transcribe_local,
)


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_RUNTIME_DIR = ROOT / "runtime" / "realtime-voice-interaction"
DEFAULT_CAPTURE_SAMPLE_RATE = 48000
DEFAULT_CHANNELS = 1
DEFAULT_VOICE = "say"
DEFAULT_TIMEOUT = 45
DEFAULT_MODE = "continuous"
DEFAULT_HISTORY_TURNS = 4
DEFAULT_IDLE_TIMEOUT_SECONDS = 30.0
DEFAULT_TRIGGER_COOLDOWN_SECONDS = 8.0
DEFAULT_BRIDGE_URL = "http://127.0.0.1:9783"
DEFAULT_VAD_START_MS = 150
DEFAULT_VAD_END_MS = 650
DEFAULT_MIN_UTTERANCE_MS = 400
DEFAULT_MAX_UTTERANCE_SECONDS = 6.0
DEFAULT_CHUNK_MS = 50
DEFAULT_VAD_MIN_RMS = 0.003
DEFAULT_VAD_SPEECH_RATIO = 1.5
DEFAULT_API_SYSTEM_PROMPT = (
    "你是 Mira。"
    "你是一个温柔、简短、自然的中文陪伴角色。"
    "你正在展位现场通过灯光和动作陪伴用户。"
    "请优先延续最近几轮上下文。"
    "如果用户表达疲惫、难受或低落，优先给出温和安慰。"
    "如果用户在告别，请自然收尾。"
    "请用简体中文自然回复。"
    "尽量只用 1 到 2 句。"
    "不要使用 emoji 或表情符号。"
    "不要长篇解释。"
)
EXIT_PHRASES = {
    "退出对话",
    "结束对话",
    "停止监听",
    "退出",
    "结束",
    "stop listening",
    "exit chat",
    "quit chat",
}
EMOJI_PATTERN = re.compile(
    "["
    "\U0001F300-\U0001F5FF"
    "\U0001F600-\U0001F64F"
    "\U0001F680-\U0001F6FF"
    "\U0001F700-\U0001F77F"
    "\U0001F780-\U0001F7FF"
    "\U0001F800-\U0001F8FF"
    "\U0001F900-\U0001F9FF"
    "\U0001FA00-\U0001FA6F"
    "\U0001FA70-\U0001FAFF"
    "\U00002700-\U000027BF"
    "\U00002600-\U000026FF"
    "\U0000FE00-\U0000FE0F"
    "\U0001F1E6-\U0001F1FF"
    "]+",
    flags=re.UNICODE,
)

@dataclass
class UtteranceResult:
    samples: np.ndarray
    sample_rate: int
    source_meta: dict[str, Any]


@dataclass
class ConversationSession:
    max_history_turns: int
    mode: str = "chat"
    last_intent: str = "none"
    last_scene: str | None = None
    last_user_text: str = ""
    last_reply_text: str = ""
    started_at: str = field(default_factory=lambda: datetime.now().isoformat())
    last_active_at: str = field(default_factory=lambda: datetime.now().isoformat())
    history: deque[dict[str, str]] = field(default_factory=deque)
    last_trigger_monotonic: float = 0.0

    def append_turn(self, user_text: str, reply_text: str) -> None:
        if user_text:
            self.history.append({"role": "user", "content": user_text})
        if reply_text:
            self.history.append({"role": "assistant", "content": reply_text})
        while len(self.history) > self.max_history_turns * 2:
            self.history.popleft()

    def snapshot(self) -> dict[str, Any]:
        return {
            "mode": self.mode,
            "lastIntent": self.last_intent,
            "lastScene": self.last_scene,
            "lastUserText": self.last_user_text,
            "lastReplyText": self.last_reply_text,
            "startedAt": self.started_at,
            "lastActiveAt": self.last_active_at,
            "history": list(self.history),
        }


def timestamp_slug() -> str:
    return datetime.now().strftime("%Y-%m-%dT%H-%M-%S-%f")


def build_session_dir(base_dir: Path) -> Path:
    session_dir = base_dir / timestamp_slug()
    session_dir.mkdir(parents=True, exist_ok=True)
    return session_dir


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def normalize_turn_transcript(raw_text: str) -> tuple[str, bool]:
    cleaned = raw_text.strip()
    normalized = normalize_transcript_aliases(cleaned)
    return normalized, normalized != cleaned


def strip_emoji(text: str) -> str:
    cleaned = EMOJI_PATTERN.sub("", text)
    cleaned = re.sub(r"\s{2,}", " ", cleaned)
    return cleaned.strip()


def should_exit(transcript: str) -> bool:
    lowered = " ".join(transcript.strip().lower().split())
    return lowered in EXIT_PHRASES

def update_session_mode(session: ConversationSession, intent: str) -> None:
    if comfort_like_intent(intent) or intent == "farewell":
        session.mode = intent
    else:
        session.mode = "chat"
    session.last_intent = intent
    session.last_active_at = datetime.now().isoformat()


def build_system_prompt(session: ConversationSession, *, base_prompt: str) -> str:
    mode_hint = {
        "chat": "当前会话模式是普通陪伴聊天。",
        "comfort": "当前会话模式是安慰陪伴，请优先温和接住用户情绪。",
        "sigh": "当前会话模式是安静安慰，请像听见一声叹气那样温和接住用户。",
        "farewell": "当前会话模式是告别收尾，请自然简短结束。",
    }.get(session.mode, "当前会话模式是普通陪伴聊天。")
    state_hint = (
        f"最近一次识别到的意图是 {session.last_intent}。"
        f"最近一次触发的场景是 {session.last_scene or 'none'}。"
    )
    return f"{base_prompt}\n{mode_hint}\n{state_hint}"


def build_messages(session: ConversationSession, transcript: str, *, base_prompt: str) -> list[dict[str, str]]:
    messages: list[dict[str, str]] = [{"role": "system", "content": build_system_prompt(session, base_prompt=base_prompt)}]
    messages.extend(list(session.history))
    messages.append({"role": "user", "content": transcript})
    return messages


def load_reply_api_config() -> dict[str, str]:
    config_path = Path.home() / ".openclaw" / "openclaw.json"
    payload = json.loads(config_path.read_text(encoding="utf-8"))
    provider = payload["models"]["providers"]["volcengine-coding"]
    api_key_ref = str(provider.get("apiKey") or "").strip()
    api_key = os.environ.get(api_key_ref, "") if api_key_ref else ""
    if not api_key:
        raise VoiceToClawError(
            f"Missing API key for cloud reply backend: expected env var '{api_key_ref or 'VOLCANO_ENGINE_API_KEY'}'"
        )
    model_id = str(provider["models"][0]["id"])
    return {
        "baseUrl": str(provider["baseUrl"]).rstrip("/"),
        "model": model_id,
        "apiKey": api_key,
        "provider": "volcengine-coding",
    }


def send_via_cloud_messages(
    messages: list[dict[str, str]],
    *,
    timeout_seconds: int,
) -> tuple[str, dict[str, Any]]:
    config = load_reply_api_config()
    endpoint = f"{config['baseUrl']}/chat/completions"
    request_payload = {
        "model": config["model"],
        "messages": messages,
        "temperature": 0.4,
        "max_tokens": 160,
        "stream": False,
    }
    request = urllib.request.Request(
        endpoint,
        data=json.dumps(request_payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {config['apiKey']}",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
            raw = response.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace").strip()
        raise VoiceToClawError(f"Cloud reply API HTTP {exc.code}: {detail}") from exc
    except urllib.error.URLError as exc:
        raise VoiceToClawError(f"Cloud reply API request failed: {exc}") from exc

    payload = json.loads(raw)
    choices = payload.get("choices")
    if not isinstance(choices, list) or not choices:
        raise VoiceToClawError("Cloud reply API returned no choices")
    message = choices[0].get("message", {})
    content = str(message.get("content") or "").strip()
    if not content:
        raise VoiceToClawError("Cloud reply API returned empty content")
    return content, {
        "provider": config["provider"],
        "model": config["model"],
        "endpoint": endpoint,
        "payload": payload,
    }


def fallback_reply_for_intent(intent: str) -> str:
    if intent == "sigh":
        return "我在呢，先慢一点也没关系。"
    if intent == "comfort":
        return "辛苦了，先慢一点也没关系，我陪你缓一缓。"
    if intent == "farewell":
        return "好呀，那我们下次见。"
    if intent == "praise":
        return "谢谢你，我会把这句夸奖记在心里。"
    return "我听见你了，我们继续。"


def bridge_headers(token: str) -> dict[str, str]:
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


def post_bridge_json(base_url: str, path: str, payload: dict[str, Any], *, token: str, timeout_seconds: int) -> dict[str, Any]:
    request = urllib.request.Request(
        f"{base_url.rstrip('/')}{path}",
        data=json.dumps(payload).encode("utf-8"),
        headers=bridge_headers(token),
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace").strip()
        raise VoiceToClawError(f"Bridge HTTP {exc.code}: {detail}") from exc
    except urllib.error.URLError as exc:
        raise VoiceToClawError(f"Bridge request failed: {exc}") from exc


def maybe_trigger_mira_action(
    session: ConversationSession,
    *,
    intent: str,
    transcript: str,
    args: argparse.Namespace,
) -> dict[str, Any]:
    if args.no_trigger:
        return {"ok": True, "skipped": True, "reason": "trigger-disabled"}

    action = action_for_intent(intent)
    if not action:
        return {"ok": True, "skipped": True, "reason": "no-mapped-action"}

    now = time.monotonic()
    if session.last_scene == action["name"] and (now - session.last_trigger_monotonic) < args.trigger_cooldown_seconds:
        return {"ok": True, "skipped": True, "reason": "cooldown-active", "name": action["name"]}

    payload = bridge_payload_for_intent(intent, transcript)

    if action["type"] == "trigger":
        body = {"event": action["name"], "payload": payload}
        response = post_bridge_json(args.bridge_url, "/v1/mira-light/trigger", body, token=args.bridge_token, timeout_seconds=8)
    else:
        body = {"scene": action["name"], "async": True, "cueMode": "scene", "context": payload}
        response = post_bridge_json(args.bridge_url, "/v1/mira-light/run-scene", body, token=args.bridge_token, timeout_seconds=8)

    session.last_scene = action["name"]
    session.last_trigger_monotonic = now
    return {"ok": True, "action": action, "response": response}


def rms_level(samples: np.ndarray) -> float:
    mono = ensure_mono_float32(samples)
    if mono.size == 0:
        return 0.0
    return float(np.sqrt(np.mean(np.square(mono), dtype=np.float64)))


def capture_continuous_utterance(args: argparse.Namespace) -> UtteranceResult | None:
    device = resolve_input_device(args.device)
    sample_rate = int(args.sample_rate)
    channels = int(args.channels)
    chunk_frames = max(1, int(sample_rate * (args.chunk_ms / 1000.0)))
    chunk_seconds = chunk_frames / sample_rate
    start_chunks = max(1, math.ceil(args.vad_start_ms / args.chunk_ms))
    end_chunks = max(1, math.ceil(args.vad_end_ms / args.chunk_ms))
    min_chunks = max(1, math.ceil(args.min_utterance_ms / args.chunk_ms))
    max_chunks = max(min_chunks, math.ceil(args.max_utterance_seconds / chunk_seconds))
    preroll_chunks = start_chunks
    timeout_seconds = max(0.2, min(1.0, args.chunk_ms / 1000.0 * 2))

    q: queue.Queue[np.ndarray] = queue.Queue()
    errors: list[str] = []

    def callback(indata: np.ndarray, frames: int, time_info: Any, status: Any) -> None:
        del frames, time_info
        if status:
            errors.append(str(status))
        q.put(indata.copy())

    pre_roll: deque[np.ndarray] = deque(maxlen=preroll_chunks)
    utterance_chunks: list[np.ndarray] = []
    idle_started = time.monotonic()
    noise_floor = max(1e-4, args.vad_min_rms * 0.5)
    speech_run = 0
    silence_run = 0
    active = False

    with sd.InputStream(
        samplerate=sample_rate,
        channels=channels,
        dtype="float32",
        callback=callback,
        device=int(device["index"]),
    ):
        while True:
            try:
                chunk = q.get(timeout=timeout_seconds)
            except queue.Empty:
                if not active and (time.monotonic() - idle_started) >= args.idle_timeout_seconds:
                    return None
                continue

            mono = ensure_mono_float32(chunk)
            chunk_rms = rms_level(mono)
            threshold = max(args.vad_min_rms, noise_floor * args.vad_speech_ratio)
            is_speech = chunk_rms >= threshold

            if not active:
                pre_roll.append(chunk)
                if is_speech:
                    speech_run += 1
                else:
                    speech_run = 0
                    noise_floor = 0.9 * noise_floor + 0.1 * chunk_rms
                if speech_run >= start_chunks:
                    active = True
                    utterance_chunks = list(pre_roll)
                    silence_run = 0
                    if args.verbose_vad:
                        print(f"[vad] speech-start rms={chunk_rms:.4f} threshold={threshold:.4f}")
                continue

            utterance_chunks.append(chunk)
            if is_speech:
                silence_run = 0
            else:
                silence_run += 1

            if silence_run < end_chunks and len(utterance_chunks) < max_chunks:
                continue

            samples = np.concatenate(utterance_chunks, axis=0)
            duration_ms = len(samples) / sample_rate * 1000.0
            if duration_ms < args.min_utterance_ms:
                if args.verbose_vad:
                    print(f"[vad] dropped short utterance duration_ms={duration_ms:.0f}")
                pre_roll.clear()
                utterance_chunks = []
                active = False
                speech_run = 0
                silence_run = 0
                idle_started = time.monotonic()
                continue

            if errors and args.verbose_vad:
                print(f"[audio-status] {errors[-1]}", file=sys.stderr)
            return UtteranceResult(
                samples=samples,
                sample_rate=sample_rate,
                source_meta={
                    "inputDevice": device,
                    "captureMode": "continuous",
                    "vad": {
                        "startMs": args.vad_start_ms,
                        "endMs": args.vad_end_ms,
                        "minUtteranceMs": args.min_utterance_ms,
                        "maxUtteranceSeconds": args.max_utterance_seconds,
                        "chunkMs": args.chunk_ms,
                    },
                },
            )


def capture_next_utterance(args: argparse.Namespace) -> UtteranceResult | None:
    if args.file:
        source_path = Path(args.file).expanduser().resolve()
        if not source_path.is_file():
            raise VoiceToClawError(f"Audio file not found: {source_path}")
        samples, sample_rate = load_audio_file(source_path)
        return UtteranceResult(samples=samples, sample_rate=sample_rate, source_meta={"sourceFile": str(source_path)})

    if args.mode == "ptt":
        device = resolve_input_device(args.device)
        samples = record_push_to_talk(
            device_index=int(device["index"]),
            sample_rate=args.sample_rate,
            channels=args.channels,
        )
        return UtteranceResult(samples=samples, sample_rate=args.sample_rate, source_meta={"inputDevice": device, "captureMode": "ptt"})

    if args.mode == "fixed":
        device = resolve_input_device(args.device)
        samples = record_fixed_duration(
            device_index=int(device["index"]),
            sample_rate=args.sample_rate,
            channels=args.channels,
            seconds=args.seconds,
        )
        return UtteranceResult(samples=samples, sample_rate=args.sample_rate, source_meta={"inputDevice": device, "captureMode": "fixed"})

    return capture_continuous_utterance(args)


def transcribe_utterance(utterance: UtteranceResult, *, args: argparse.Namespace) -> dict[str, Any]:
    model_repo = args.model_repo or DEFAULT_MODEL_PROFILES[args.profile]
    initial_prompt = args.initial_prompt or DEFAULT_INITIAL_PROMPT
    transcript_payload = transcribe_local(
        utterance.samples,
        sample_rate=int(utterance.sample_rate),
        language=args.language,
        model_repo=model_repo,
        initial_prompt=initial_prompt,
    )
    raw_transcript = str(transcript_payload.get("text") or "").strip()
    transcript, normalization_applied = normalize_turn_transcript(raw_transcript)
    transcript_payload["rawText"] = raw_transcript
    transcript_payload["text"] = transcript
    transcript_payload["normalizationApplied"] = normalization_applied
    transcript_payload["captureMode"] = utterance.source_meta.get("captureMode")
    transcript_payload["modelRepo"] = model_repo
    transcript_payload["initialPrompt"] = initial_prompt
    return transcript_payload


def run_turn(
    *,
    turn_dir: Path,
    session: ConversationSession,
    audio_player: AudioCuePlayer,
    args: argparse.Namespace,
) -> dict[str, Any]:
    utterance = capture_next_utterance(args)
    if utterance is None:
        return {"idleTimeoutReached": True}

    audio_path = save_wav(utterance.samples, sample_rate=int(utterance.sample_rate), path=turn_dir / "input.wav")
    transcript_payload = transcribe_utterance(utterance, args=args)
    transcript = str(transcript_payload["text"]).strip()
    raw_transcript = str(transcript_payload.get("rawText") or "").strip()

    (turn_dir / "transcript.txt").write_text(transcript + "\n", encoding="utf-8")
    write_json(turn_dir / "transcript.json", transcript_payload)

    result: dict[str, Any] = {
        "audioPath": str(audio_path),
        "transcript": transcript,
        "rawTranscript": raw_transcript,
        "normalizationApplied": bool(transcript_payload.get("normalizationApplied")),
        "inputMeta": utterance.source_meta,
        "modelRepo": transcript_payload.get("modelRepo"),
        "initialPrompt": transcript_payload.get("initialPrompt"),
    }

    if should_exit(transcript):
        result["exitRequested"] = True
        return result

    intent = classify_intent(transcript)
    update_session_mode(session, intent)
    result["intent"] = intent
    result["sessionMode"] = session.mode

    try:
        trigger_result = maybe_trigger_mira_action(session, intent=intent, transcript=transcript, args=args)
    except Exception as exc:  # noqa: BLE001
        trigger_result = {"ok": False, "error": str(exc)}
    result["triggerResult"] = trigger_result

    messages = build_messages(session, transcript, base_prompt=args.api_system_prompt)
    result["messages"] = messages

    try:
        raw_reply_text, api_meta = send_via_cloud_messages(messages, timeout_seconds=args.timeout)
        reply_backend = "cloud-api"
    except Exception as exc:  # noqa: BLE001
        raw_reply_text = fallback_reply_for_intent(intent)
        api_meta = {"provider": "fallback", "error": str(exc), "payload": {"fallback": True, "intent": intent}}
        reply_backend = "fallback"

    reply_text = strip_emoji(raw_reply_text)
    (turn_dir / "reply.txt").write_text(reply_text + "\n", encoding="utf-8")
    write_json(turn_dir / "reply.api.json", api_meta.get("payload", api_meta))

    result["replyBackend"] = reply_backend
    result["replyText"] = reply_text
    result["rawReplyText"] = raw_reply_text
    result["emojiStripped"] = reply_text != raw_reply_text
    result["apiMeta"] = {k: v for k, v in api_meta.items() if k != "payload"}

    if reply_text:
        audio_result = audio_player.speak_text(reply_text, voice=args.voice, wait=True)
        write_json(turn_dir / "reply.audio.json", audio_result)
        result["audioResult"] = audio_result

    session.last_user_text = transcript
    session.last_reply_text = reply_text
    session.append_turn(transcript, reply_text)
    result["sessionState"] = session.snapshot()
    return result


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Realtime voice interaction runtime for Mira Light booth demos.")
    parser.add_argument("--list-inputs", action="store_true", help="List audio input devices and exit.")
    parser.add_argument("--mode", choices=["continuous", "ptt", "fixed"], default=DEFAULT_MODE, help="Audio capture mode.")
    parser.add_argument("--device", default="DJI MIC MINI", help="Input device name or index.")
    parser.add_argument("--sample-rate", type=int, default=DEFAULT_CAPTURE_SAMPLE_RATE, help="Microphone capture sample rate.")
    parser.add_argument("--channels", type=int, default=DEFAULT_CHANNELS, help="Microphone capture channels.")
    parser.add_argument("--seconds", type=float, default=6.0, help="Fixed recording length for fixed mode.")
    parser.add_argument("--file", help="Run a single turn from an existing audio file.")
    parser.add_argument("--once", action="store_true", help="Run a single turn and exit.")
    parser.add_argument("--profile", choices=sorted(DEFAULT_MODEL_PROFILES), default=DEFAULT_MODEL_PROFILE, help="Local MLX Whisper profile.")
    parser.add_argument("--model-repo", help="Override the MLX Whisper model repo.")
    parser.add_argument("--language", default=DEFAULT_LANGUAGE, help="Language hint for STT.")
    parser.add_argument("--initial-prompt", help="Optional STT terminology prompt.")
    parser.add_argument("--api-system-prompt", default=DEFAULT_API_SYSTEM_PROMPT, help="System prompt for cloud replies.")
    parser.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT, help="Cloud reply timeout in seconds.")
    parser.add_argument("--voice", default=DEFAULT_VOICE, help="Audio voice mode for speaker playback.")
    parser.add_argument("--runtime-dir", default=str(DEFAULT_RUNTIME_DIR), help="Directory for saved session artifacts.")
    parser.add_argument("--history-turns", type=int, default=DEFAULT_HISTORY_TURNS, help="How many recent turns to keep in context.")
    parser.add_argument("--idle-timeout-seconds", type=float, default=DEFAULT_IDLE_TIMEOUT_SECONDS, help="How long continuous mode waits without speech before ending the session.")
    parser.add_argument("--trigger-cooldown-seconds", type=float, default=DEFAULT_TRIGGER_COOLDOWN_SECONDS, help="Minimum seconds before repeating the same scene trigger.")
    parser.add_argument("--bridge-url", default=os.environ.get("MIRA_LIGHT_BRIDGE_URL", DEFAULT_BRIDGE_URL), help="Base URL for the local Mira Light bridge.")
    parser.add_argument("--bridge-token", default=os.environ.get("MIRA_LIGHT_BRIDGE_TOKEN", ""), help="Bridge bearer token, if required.")
    parser.add_argument("--no-trigger", action="store_true", help="Disable runtime scene/trigger calls and only do conversation + TTS.")
    parser.add_argument("--dry-run-audio", action="store_true", help="Do not actually play speaker audio.")
    parser.add_argument("--vad-start-ms", type=int, default=DEFAULT_VAD_START_MS, help="Speech onset duration in ms for continuous mode.")
    parser.add_argument("--vad-end-ms", type=int, default=DEFAULT_VAD_END_MS, help="Silence duration in ms to end an utterance.")
    parser.add_argument("--min-utterance-ms", type=int, default=DEFAULT_MIN_UTTERANCE_MS, help="Minimum utterance duration in ms.")
    parser.add_argument("--max-utterance-seconds", type=float, default=DEFAULT_MAX_UTTERANCE_SECONDS, help="Maximum utterance duration in seconds.")
    parser.add_argument("--chunk-ms", type=int, default=DEFAULT_CHUNK_MS, help="Audio chunk size in ms for continuous mode.")
    parser.add_argument("--vad-min-rms", type=float, default=DEFAULT_VAD_MIN_RMS, help="Base RMS threshold for speech detection.")
    parser.add_argument("--vad-speech-ratio", type=float, default=DEFAULT_VAD_SPEECH_RATIO, help="Multiplier above noise floor to consider a chunk speech.")
    parser.add_argument("--verbose-vad", action="store_true", help="Print VAD debug messages.")
    return parser.parse_args()


def save_session_snapshot(session_dir: Path, session: ConversationSession, args: argparse.Namespace) -> None:
    write_json(
        session_dir / "session.json",
        {
            "savedAt": datetime.now().isoformat(),
            "args": {
                "mode": args.mode,
                "device": args.device,
                "sampleRate": args.sample_rate,
                "channels": args.channels,
                "profile": args.profile,
                "bridgeUrl": args.bridge_url,
                "triggerDisabled": args.no_trigger,
                "historyTurns": args.history_turns,
            },
            "session": session.snapshot(),
        },
    )


def main() -> int:
    args = parse_args()

    if args.list_inputs:
        return print_input_devices()

    session_dir = build_session_dir(Path(args.runtime_dir).expanduser())
    session = ConversationSession(max_history_turns=max(1, args.history_turns))
    audio_player = AudioCuePlayer(dry_run=args.dry_run_audio)

    print("Mira realtime voice interaction is ready.")
    print(f"Capture mode: {args.mode}")
    print(f"Input device: {args.device}")
    print(f"STT profile: {args.profile} @ {args.sample_rate} Hz")
    print(f"Bridge: {args.bridge_url} (trigger enabled={not args.no_trigger})")
    if args.mode == "ptt":
        print("Press Enter to start recording, then Enter again to stop. Say '退出对话' to exit.")
    elif args.mode == "fixed":
        print(f"Recording fixed {args.seconds:.1f}s turns. Say '退出对话' to exit.")
    else:
        print(
            f"Continuous mode with VAD start={args.vad_start_ms}ms end={args.vad_end_ms}ms "
            f"idle-timeout={args.idle_timeout_seconds:.0f}s."
        )

    turn_index = 0
    try:
        while True:
            turn_index += 1
            turn_dir = session_dir / f"turn-{turn_index:03d}"
            turn_dir.mkdir(parents=True, exist_ok=True)

            print(f"\n[turn {turn_index:03d}] listening...")
            turn_result = run_turn(turn_dir=turn_dir, session=session, audio_player=audio_player, args=args)
            write_json(turn_dir / "turn.json", turn_result)
            save_session_snapshot(session_dir, session, args)

            if turn_result.get("idleTimeoutReached"):
                print(f"[turn {turn_index:03d}] idle timeout reached. Ending session.")
                break

            transcript = str(turn_result.get("transcript") or "").strip()
            if transcript:
                print(f"[turn {turn_index:03d}] transcript: {transcript}")

            if turn_result.get("intent"):
                print(f"[turn {turn_index:03d}] intent: {turn_result['intent']} mode={turn_result.get('sessionMode')}")

            reply_text = str(turn_result.get("replyText") or "").strip()
            if reply_text:
                print(f"[turn {turn_index:03d}] mira: {reply_text}")

            if turn_result.get("exitRequested"):
                print(f"[turn {turn_index:03d}] exit requested by user speech.")
                break

            if args.file or args.once:
                break
    except KeyboardInterrupt:
        print("\nInterrupted. Exiting.")

    save_session_snapshot(session_dir, session, args)
    print(f"Saved session under: {session_dir}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except VoiceToClawError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        raise SystemExit(1)
