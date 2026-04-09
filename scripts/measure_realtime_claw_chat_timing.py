#!/usr/bin/env python3
"""Measure step-by-step latency for the realtime claw chat pipeline."""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

from mira_light_audio import AudioCuePlayer
from mira_realtime_claw_chat import build_agent_message, normalize_turn_transcript
from openclaw_voice_to_claw import (
    DEFAULT_INITIAL_PROMPT,
    DEFAULT_LANGUAGE,
    DEFAULT_MODEL_PROFILE,
    DEFAULT_MODEL_PROFILES,
    load_audio_file,
    send_to_openclaw,
    transcribe_local,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Measure realtime chat pipeline timings.")
    parser.add_argument("--file", required=True, help="Audio file to test.")
    parser.add_argument(
        "--profile",
        choices=sorted(DEFAULT_MODEL_PROFILES),
        default=DEFAULT_MODEL_PROFILE,
        help="Local MLX Whisper profile.",
    )
    parser.add_argument("--model-repo", help="Override the MLX Whisper model repo.")
    parser.add_argument("--language", default=DEFAULT_LANGUAGE, help="Language hint.")
    parser.add_argument("--initial-prompt", default=DEFAULT_INITIAL_PROMPT, help="STT prompt.")
    parser.add_argument("--agent", default="main", help="OpenClaw agent id.")
    parser.add_argument("--thinking", default="off", help="Thinking level.")
    parser.add_argument("--timeout", type=int, default=45, help="OpenClaw timeout in seconds.")
    parser.add_argument(
        "--voice-mode",
        dest="voice_mode",
        default="gentle_sister",
        choices=["gentle_sister", "warm_gentleman", "female", "male"],
        help="Audio voice mode.",
    )
    parser.add_argument("--voice", dest="voice_mode", choices=["gentle_sister", "warm_gentleman", "female", "male"], help=argparse.SUPPRESS)
    parser.add_argument("--dry-run-audio", action="store_true", help="Skip actual playback.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    audio_path = Path(args.file).expanduser().resolve()
    if not audio_path.is_file():
        raise SystemExit(f"Audio file not found: {audio_path}")

    timings: list[dict[str, float]] = []

    t0 = time.perf_counter()
    samples, sample_rate = load_audio_file(audio_path)
    t1 = time.perf_counter()
    timings.append({"step": "load_audio", "seconds": t1 - t0})

    model_repo = args.model_repo or DEFAULT_MODEL_PROFILES[args.profile]
    transcript_payload = transcribe_local(
        samples,
        sample_rate=sample_rate,
        language=args.language,
        model_repo=model_repo,
        initial_prompt=args.initial_prompt,
    )
    t2 = time.perf_counter()
    timings.append({"step": "stt_local_mlx", "seconds": t2 - t1})

    raw_transcript = str(transcript_payload.get("text") or "").strip()
    transcript, normalization_applied = normalize_turn_transcript(raw_transcript)
    agent_message = build_agent_message(transcript)
    t3 = time.perf_counter()
    timings.append({"step": "normalize_and_build_prompt", "seconds": t3 - t2})

    code, stdout, stderr = send_to_openclaw(
        agent_message,
        agent=args.agent,
        session_id=None,
        thinking=args.thinking,
        timeout_seconds=args.timeout,
        json_output=False,
    )
    t4 = time.perf_counter()
    timings.append({"step": "claw_reply", "seconds": t4 - t3})

    reply_text = (stdout or "").strip()
    audio_player = AudioCuePlayer(dry_run=args.dry_run_audio)
    audio_result = audio_player.speak_text(reply_text, voice=args.voice_mode, wait=True) if reply_text else {}
    t5 = time.perf_counter()
    timings.append({"step": "tts_and_playback", "seconds": t5 - t4})

    total = t5 - t0
    payload = {
        "audioFile": str(audio_path),
        "profile": args.profile,
        "modelRepo": model_repo,
        "transcript": transcript,
        "rawTranscript": raw_transcript,
        "normalizationApplied": normalization_applied,
        "agentMessage": agent_message,
        "openclawExitCode": code,
        "replyText": reply_text,
        "replyStderr": (stderr or "").strip(),
        "audioResult": audio_result,
        "timings": timings,
        "totalSeconds": total,
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if code == 0 else code


if __name__ == "__main__":
    raise SystemExit(main())
