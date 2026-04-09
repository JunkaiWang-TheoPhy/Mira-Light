#!/usr/bin/env python3
"""Minimal realtime microphone/file -> local STT -> OpenClaw -> speaker loop."""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Any
import urllib.error
import urllib.request

from mira_light_audio import AudioCuePlayer
from mira_name_aliases import normalize_transcript_aliases
from openclaw_voice_to_claw import (
    DEFAULT_INITIAL_PROMPT,
    DEFAULT_LANGUAGE,
    DEFAULT_MODEL_PROFILE,
    DEFAULT_MODEL_PROFILES,
    DEFAULT_SAMPLE_RATE,
    VoiceToClawError,
    load_audio_file,
    print_input_devices,
    record_fixed_duration,
    record_push_to_talk,
    resolve_input_device,
    save_wav,
    transcribe_local,
)


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_RUNTIME_DIR = ROOT / "runtime" / "realtime-claw-chat"
DEFAULT_VOICE = "openclaw"
DEFAULT_TIMEOUT = 45
DEFAULT_AGENT = "main"
DEFAULT_CAPTURE_SAMPLE_RATE = 48000
DEFAULT_STT_PROFILE = DEFAULT_MODEL_PROFILE
DEFAULT_REPLY_STYLE_HINT = "请用简短自然的中文回复，不要使用 emoji 或表情符号。"
DEFAULT_API_SYSTEM_PROMPT = (
    "你是 Mira。"
    "你是一个温柔、简短、自然的中文陪伴角色。"
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


def timestamp_slug() -> str:
    return datetime.now().strftime("%Y-%m-%dT%H-%M-%S-%f")


def build_session_dir(base_dir: Path) -> Path:
    run_dir = base_dir / timestamp_slug()
    run_dir.mkdir(parents=True, exist_ok=True)
    return run_dir


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def normalize_turn_transcript(raw_text: str) -> tuple[str, bool]:
    cleaned = raw_text.strip()
    normalized = normalize_transcript_aliases(cleaned)
    return normalized, normalized != cleaned


def strip_emoji(text: str) -> str:
    cleaned = EMOJI_PATTERN.sub("", text)
    cleaned = re.sub(r"\s{2,}", " ", cleaned)
    return cleaned.strip()


def build_agent_message(transcript: str) -> str:
    return f"{DEFAULT_REPLY_STYLE_HINT}\n\n用户刚刚说：{transcript}"


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


def send_via_cloud_agent(transcript: str, *, timeout_seconds: int, system_prompt: str | None = None) -> tuple[str, dict[str, Any]]:
    config = load_reply_api_config()
    endpoint = f"{config['baseUrl']}/chat/completions"
    request_payload = {
        "model": config["model"],
        "messages": [
            {"role": "system", "content": system_prompt or DEFAULT_API_SYSTEM_PROMPT},
            {"role": "user", "content": transcript},
        ],
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


def should_exit(transcript: str) -> bool:
    lowered = " ".join(transcript.strip().lower().split())
    return lowered in EXIT_PHRASES


def capture_audio_for_turn(args: argparse.Namespace) -> tuple[Any, int, dict[str, Any]]:
    if args.file:
        source_path = Path(args.file).expanduser().resolve()
        if not source_path.is_file():
            raise VoiceToClawError(f"Audio file not found: {source_path}")
        samples, sample_rate = load_audio_file(source_path)
        return samples, sample_rate, {"sourceFile": str(source_path)}

    device = resolve_input_device(args.device)
    if args.ptt:
        samples = record_push_to_talk(
            device_index=int(device["index"]),
            sample_rate=args.sample_rate,
            channels=args.channels,
        )
    else:
        samples = record_fixed_duration(
            device_index=int(device["index"]),
            sample_rate=args.sample_rate,
            channels=args.channels,
            seconds=args.seconds,
        )
    return samples, int(args.sample_rate), {"inputDevice": device}


def run_turn(
    *,
    turn_dir: Path,
    args: argparse.Namespace,
    audio_player: AudioCuePlayer,
) -> dict[str, Any]:
    samples, sample_rate, source_meta = capture_audio_for_turn(args)
    audio_path = save_wav(samples, sample_rate=sample_rate, path=turn_dir / "input.wav")

    model_repo = args.model_repo or DEFAULT_MODEL_PROFILES[args.profile]
    initial_prompt = args.initial_prompt or DEFAULT_INITIAL_PROMPT
    transcript_payload = transcribe_local(
        samples,
        sample_rate=sample_rate,
        language=args.language,
        model_repo=model_repo,
        initial_prompt=initial_prompt,
    )

    raw_transcript = str(transcript_payload.get("text") or "").strip()
    transcript, normalization_applied = normalize_turn_transcript(raw_transcript)
    transcript_payload["rawText"] = raw_transcript
    transcript_payload["text"] = transcript
    transcript_payload["normalizationApplied"] = normalization_applied
    (turn_dir / "transcript.txt").write_text(transcript + "\n", encoding="utf-8")
    write_json(turn_dir / "transcript.json", transcript_payload)

    result: dict[str, Any] = {
        "audioPath": str(audio_path),
        "transcript": transcript,
        "rawTranscript": raw_transcript,
        "normalizationApplied": normalization_applied,
        "initialPrompt": initial_prompt,
        "modelRepo": model_repo,
        **source_meta,
    }

    if should_exit(transcript):
        result["exitRequested"] = True
        return result

    agent_message = build_agent_message(transcript)
    result["agentMessage"] = agent_message

    raw_reply_text, api_meta = send_via_cloud_agent(
        transcript,
        timeout_seconds=args.timeout,
        system_prompt=args.api_system_prompt,
    )
    reply_text = strip_emoji(raw_reply_text)
    (turn_dir / "reply.txt").write_text(reply_text + "\n", encoding="utf-8")
    write_json(turn_dir / "reply.api.json", api_meta["payload"])
    result["replyBackend"] = "cloud-api"
    result["replyText"] = reply_text
    result["rawReplyText"] = raw_reply_text
    result["emojiStripped"] = reply_text != raw_reply_text
    result["apiMeta"] = {k: v for k, v in api_meta.items() if k != "payload"}

    reply_text = str(result.get("replyText") or "").strip()
    if reply_text:
        audio_result = audio_player.speak_text(reply_text, voice=args.voice, wait=True)
        write_json(turn_dir / "reply.audio.json", audio_result)
        result["audioResult"] = audio_result

    return result


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Minimal local STT -> OpenClaw -> speaker loop.")
    parser.add_argument("--list-inputs", action="store_true", help="List audio input devices and exit.")
    parser.add_argument("--device", default="DJI MIC MINI", help="Input device name or index.")
    parser.add_argument("--sample-rate", type=int, default=DEFAULT_CAPTURE_SAMPLE_RATE, help="Microphone capture sample rate.")
    parser.add_argument("--channels", type=int, default=1, help="Microphone capture channels.")
    parser.add_argument("--seconds", type=float, default=6.0, help="Fixed recording length when not using PTT.")
    parser.add_argument("--no-ptt", dest="ptt", action="store_false", help="Use fixed-duration recording instead of push-to-talk.")
    parser.set_defaults(ptt=True)
    parser.add_argument("--file", help="Run a single turn from an existing audio file.")
    parser.add_argument("--once", action="store_true", help="Run only one turn and exit.")
    parser.add_argument(
        "--profile",
        choices=sorted(DEFAULT_MODEL_PROFILES),
        default=DEFAULT_STT_PROFILE,
        help="Local MLX Whisper profile.",
    )
    parser.add_argument("--model-repo", help="Override the MLX Whisper model repo.")
    parser.add_argument("--language", default=DEFAULT_LANGUAGE, help="Language hint for STT.")
    parser.add_argument("--initial-prompt", help="Optional STT prompt.")
    parser.add_argument("--api-system-prompt", default=DEFAULT_API_SYSTEM_PROMPT, help="System prompt for cloud replies.")
    parser.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT, help="OpenClaw agent timeout in seconds.")
    parser.add_argument("--voice", default=DEFAULT_VOICE, help="Audio voice mode for speaker playback.")
    parser.add_argument("--runtime-dir", default=str(DEFAULT_RUNTIME_DIR), help="Directory for saved turn artifacts.")
    parser.add_argument("--dry-run-audio", action="store_true", help="Do not actually play speaker audio.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    if args.list_inputs:
        return print_input_devices()

    session_dir = build_session_dir(Path(args.runtime_dir).expanduser())
    audio_player = AudioCuePlayer(dry_run=args.dry_run_audio)

    print("Mira realtime chat is ready.")
    if args.file:
        print(f"Using audio file: {Path(args.file).expanduser()}")
    else:
        if args.ptt:
            print("Press Enter to start recording, then Enter again to stop. Say '退出对话' to exit.")
        else:
            print(f"Recording fixed {args.seconds:.1f}s turns from '{args.device}'. Say '退出对话' to exit.")
    print(f"STT profile: {args.profile} @ {args.sample_rate} Hz")
    print("Reply backend: cloud-api")

    turn_index = 0
    try:
        while True:
            turn_index += 1
            turn_dir = session_dir / f"turn-{turn_index:03d}"
            turn_dir.mkdir(parents=True, exist_ok=True)

            print(f"\n[turn {turn_index:03d}] listening...")
            turn_result = run_turn(turn_dir=turn_dir, args=args, audio_player=audio_player)
            write_json(turn_dir / "turn.json", turn_result)

            transcript = str(turn_result.get("transcript") or "").strip()
            if transcript:
                print(f"[turn {turn_index:03d}] transcript: {transcript}")

            if turn_result.get("exitRequested"):
                print(f"[turn {turn_index:03d}] exit requested by user speech.")
                break

            reply_text = str(turn_result.get("replyText") or "").strip()
            if reply_text:
                print(f"[turn {turn_index:03d}] claw: {reply_text}")
            elif turn_result.get("replyStderr"):
                print(f"[turn {turn_index:03d}] claw stderr: {turn_result['replyStderr']}", file=sys.stderr)

            if args.file or args.once:
                break
    except KeyboardInterrupt:
        print("\nInterrupted. Exiting.")

    print(f"Saved session under: {session_dir}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except VoiceToClawError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        raise SystemExit(1)
