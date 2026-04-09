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

from mira_lingzhu_client import send_via_lingzhu_messages
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
    parse_openclaw_agent_response,
    print_input_devices,
    record_fixed_duration,
    record_push_to_talk,
    resolve_input_device,
    save_wav,
    send_to_openclaw,
    transcribe_local,
)


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_RUNTIME_DIR = ROOT / "runtime" / "realtime-claw-chat"
DEFAULT_VOICE = "tts"
DEFAULT_TIMEOUT = 45
DEFAULT_AGENT = "main"
DEFAULT_REPLY_AGENT = "mira-voice-spark"
DEFAULT_REPLY_BACKEND = "openclaw-agent"
DEFAULT_CAPTURE_SAMPLE_RATE = 48000
DEFAULT_STT_PROFILE = DEFAULT_MODEL_PROFILE
DEFAULT_REPLY_THINKING = "off"
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


def build_openclaw_reply_prompt(transcript: str, *, system_prompt: str | None = None) -> str:
    prompt = system_prompt or DEFAULT_API_SYSTEM_PROMPT
    return (
        "你现在只负责为展位里的 Mira 生成直接说给用户听的简短中文回复。\n"
        "只输出 Mira 最终要说的话，不要解释任务，不要复述规则，不要输出分析、标签、引号或多余前缀。\n"
        "尽量只用 1 到 2 句。\n\n"
        f"[系统设定]\n{prompt}\n\n"
        f"[用户]\n{transcript}\n\n"
        "请直接输出 Mira 的最终回复正文。"
    )


def send_via_openclaw_agent(
    transcript: str,
    *,
    agent: str,
    thinking: str,
    timeout_seconds: int,
    system_prompt: str | None = None,
) -> tuple[str, dict[str, Any]]:
    prompt = build_openclaw_reply_prompt(transcript, system_prompt=system_prompt)
    code, stdout, stderr = send_to_openclaw(
        prompt,
        agent=agent,
        session_id=None,
        thinking=thinking,
        timeout_seconds=timeout_seconds,
        json_output=True,
    )
    if code != 0:
        raise VoiceToClawError(stderr.strip() or stdout.strip() or "openclaw agent reply failed")
    parsed = parse_openclaw_agent_response(stdout)
    meta = parsed.get("meta") or {}
    agent_meta = meta.get("agentMeta") if isinstance(meta, dict) else {}
    return str(parsed["text"]).strip(), {
        "provider": str(agent_meta.get("provider") or "openclaw-agent"),
        "model": str(agent_meta.get("model") or ""),
        "agent": agent,
        "thinking": thinking,
        "payload": parsed.get("payload"),
    }


def send_reply(
    transcript: str,
    *,
    args: argparse.Namespace,
    session_id: str,
) -> tuple[str, dict[str, Any], str]:
    if args.reply_backend == "lingzhu":
        text, meta = send_via_lingzhu_messages(
            [{"role": "system", "content": args.api_system_prompt}, {"role": "user", "content": transcript}],
            base_url=args.lingzhu_base_url,
            auth_ak=args.lingzhu_auth_ak,
            agent_id=args.lingzhu_agent_id,
            user_id=args.lingzhu_user_id or session_id,
            session_id=session_id,
            additional_user_ids=args.lingzhu_additional_user_ids,
            timeout_seconds=args.timeout,
        )
        return text, meta, "lingzhu-live-adapter"

    text, meta = send_via_openclaw_agent(
        transcript,
        agent=args.reply_agent,
        thinking=args.reply_thinking,
        timeout_seconds=args.timeout,
        system_prompt=args.api_system_prompt,
    )
    return text, meta, "openclaw-agent"


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
    session_id: str,
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

    raw_reply_text, api_meta, reply_backend = send_reply(transcript, args=args, session_id=session_id)
    reply_text = strip_emoji(raw_reply_text)
    (turn_dir / "reply.txt").write_text(reply_text + "\n", encoding="utf-8")
    write_json(turn_dir / "reply.api.json", api_meta["payload"])
    result["replyBackend"] = reply_backend
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
    parser.add_argument("--api-system-prompt", default=DEFAULT_API_SYSTEM_PROMPT, help="System prompt for reply generation.")
    parser.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT, help="OpenClaw agent timeout in seconds.")
    parser.add_argument(
        "--reply-backend",
        choices=["openclaw-agent", "lingzhu"],
        default=os.environ.get("MIRA_LIGHT_REPLY_BACKEND", DEFAULT_REPLY_BACKEND),
        help="Reply backend for Mira dialogue.",
    )
    parser.add_argument("--reply-agent", default=os.environ.get("MIRA_LIGHT_REPLY_AGENT", DEFAULT_REPLY_AGENT), help="OpenClaw agent id for reply generation.")
    parser.add_argument("--reply-thinking", default=os.environ.get("MIRA_LIGHT_REPLY_THINKING", DEFAULT_REPLY_THINKING), help="Thinking level for OpenClaw reply generation.")
    parser.add_argument("--lingzhu-base-url", default=os.environ.get("MIRA_LIGHT_LINGZHU_BASE_URL", ""), help="Lingzhu live adapter base URL.")
    parser.add_argument("--lingzhu-auth-ak", default=os.environ.get("MIRA_LIGHT_LINGZHU_AUTH_AK", ""), help="Lingzhu live adapter auth AK.")
    parser.add_argument("--lingzhu-agent-id", default=os.environ.get("MIRA_LIGHT_LINGZHU_AGENT_ID", "main"), help="Lingzhu agent id.")
    parser.add_argument("--lingzhu-user-id", default=os.environ.get("MIRA_LIGHT_LINGZHU_USER_ID", ""), help="Override Lingzhu user id for the whole session.")
    parser.add_argument(
        "--lingzhu-additional-user-ids",
        default=os.environ.get("MIRA_LIGHT_LINGZHU_ADDITIONAL_USER_IDS", "mira-light-bridge"),
        help="Comma-separated additional user ids for Lingzhu prompt-pack memory.",
    )
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
    if args.reply_backend == "lingzhu":
        print(f"Reply backend: lingzhu ({args.lingzhu_base_url or '-'})")
    else:
        print(f"Reply backend: openclaw-agent ({args.reply_agent})")

    turn_index = 0
    try:
        while True:
            turn_index += 1
            turn_dir = session_dir / f"turn-{turn_index:03d}"
            turn_dir.mkdir(parents=True, exist_ok=True)

            print(f"\n[turn {turn_index:03d}] listening...")
            turn_result = run_turn(turn_dir=turn_dir, args=args, audio_player=audio_player, session_id=session_dir.name)
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
