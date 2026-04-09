#!/usr/bin/env python3
"""Record speech, transcribe it locally, and optionally send it to OpenClaw."""

from __future__ import annotations

import argparse
import json
import math
import os
from datetime import datetime
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import threading
from typing import Any

import mlx_whisper
from mira_name_aliases import normalize_transcript_aliases
import numpy as np
from scipy.signal import resample_poly
import sounddevice as sd
import soundfile as sf


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_RUNTIME_DIR = ROOT / "runtime" / "voice-sessions"
DEFAULT_SAMPLE_RATE = 16000
DEFAULT_CHANNELS = 1
DEFAULT_AGENT = "main"
DEFAULT_LANGUAGE = "zh"
DEFAULT_INITIAL_PROMPT = (
    "这是关于 Mira Light 与 OpenClaw 的中文对话。"
    "术语可能包含 Mira。Mira 发音像米拉 / Mee-ra。"
    "还可能包含 OpenClaw、Claw、smoke ok、DJI、Doubao。"
)
DEFAULT_MODEL_PROFILES = {
    "fast": "mlx-community/whisper-tiny",
    "small": "mlx-community/whisper-small-mlx-q4",
    "balanced": "mlx-community/whisper-small-mlx-q4",
    "accurate": "mlx-community/whisper-medium-mlx-q4",
}
DEFAULT_MODEL_PROFILE = "small"


class VoiceToClawError(RuntimeError):
    """Raised when voice capture or routing fails."""


def timestamp_slug() -> str:
    return datetime.now().strftime("%Y-%m-%dT%H-%M-%S-%f")


def list_input_devices() -> list[dict[str, Any]]:
    devices: list[dict[str, Any]] = []
    for idx, device in enumerate(sd.query_devices()):
        if int(device["max_input_channels"]) <= 0:
            continue
        devices.append(
            {
                "index": idx,
                "name": str(device["name"]),
                "inputs": int(device["max_input_channels"]),
                "defaultSamplerate": float(device["default_samplerate"]),
            }
        )
    return devices


def resolve_input_device(device_hint: str | None) -> dict[str, Any]:
    devices = list_input_devices()
    if not devices:
        raise VoiceToClawError("No input devices available")

    if device_hint:
        hint = device_hint.strip().lower()
        if hint.isdigit():
            for device in devices:
                if device["index"] == int(hint):
                    return device
        for device in devices:
            if hint in device["name"].lower():
                return device
        raise VoiceToClawError(f"Input device not found: {device_hint}")

    env_hint = os.environ.get("MIRA_LIGHT_MIC_DEVICE")
    if env_hint:
        return resolve_input_device(env_hint)

    for preferred in ("DJI MIC MINI", "DJI", "Microphone", "Mic"):
        for device in devices:
            if preferred.lower() in device["name"].lower():
                return device

    default_index = int(sd.default.device[0]) if sd.default.device and sd.default.device[0] is not None else None
    if default_index is not None:
        for device in devices:
            if device["index"] == default_index:
                return device

    return devices[0]


def print_input_devices() -> int:
    devices = list_input_devices()
    if not devices:
        print("No input devices found.")
        return 1

    for device in devices:
        print(
            f"{device['index']:>2}  {device['name']}  "
            f"(inputs={device['inputs']}, default_sr={int(device['defaultSamplerate'])})"
        )
    return 0


def ensure_mono_float32(samples: np.ndarray) -> np.ndarray:
    array = np.asarray(samples, dtype=np.float32)
    if array.ndim == 1:
        return array
    return array.mean(axis=1, dtype=np.float32)


def resample_if_needed(samples: np.ndarray, sample_rate: int, target_rate: int) -> np.ndarray:
    if sample_rate == target_rate:
        return samples.astype(np.float32, copy=False)
    factor = math.gcd(sample_rate, target_rate)
    up = target_rate // factor
    down = sample_rate // factor
    return resample_poly(samples, up, down).astype(np.float32, copy=False)


def record_fixed_duration(
    *,
    device_index: int,
    sample_rate: int,
    channels: int,
    seconds: float,
) -> np.ndarray:
    frame_count = max(1, int(sample_rate * seconds))
    print(f"Recording {seconds:.1f}s from input device {device_index} ...")
    recording = sd.rec(
        frame_count,
        samplerate=sample_rate,
        channels=channels,
        dtype="float32",
        device=device_index,
    )
    sd.wait()
    return np.asarray(recording)


def record_push_to_talk(
    *,
    device_index: int,
    sample_rate: int,
    channels: int,
) -> np.ndarray:
    print("Press Enter to start recording.")
    input()
    print("Recording... Press Enter again to stop.")
    chunks: list[np.ndarray] = []
    stop_event = threading.Event()

    def callback(indata: np.ndarray, frames: int, time_info: Any, status: Any) -> None:
        del frames, time_info
        if status:
            print(f"[audio-status] {status}", file=sys.stderr)
        chunks.append(indata.copy())
        if stop_event.is_set():
            raise sd.CallbackStop

    with sd.InputStream(
        samplerate=sample_rate,
        channels=channels,
        dtype="float32",
        callback=callback,
        device=device_index,
    ):
        input()
        stop_event.set()

    if not chunks:
        raise VoiceToClawError("No audio captured")
    return np.concatenate(chunks, axis=0)


def save_wav(samples: np.ndarray, *, sample_rate: int, path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    sf.write(path, ensure_mono_float32(samples), sample_rate, subtype="PCM_16")
    return path


def load_audio_file(path: Path) -> tuple[np.ndarray, int]:
    try:
        samples, sample_rate = sf.read(path, dtype="float32")
        return ensure_mono_float32(samples), int(sample_rate)
    except RuntimeError:
        afconvert = shutil.which("afconvert")
        if not afconvert:
            raise
        with tempfile.TemporaryDirectory(prefix="mira-light-audio-") as tmp_dir:
            converted = Path(tmp_dir) / "converted.wav"
            subprocess.run(
                [afconvert, "-f", "WAVE", "-d", "LEI16@16000", str(path), str(converted)],
                check=True,
                capture_output=True,
                text=True,
            )
            samples, sample_rate = sf.read(converted, dtype="float32")
            return ensure_mono_float32(samples), int(sample_rate)


def transcribe_local(
    samples: np.ndarray,
    *,
    sample_rate: int,
    language: str,
    model_repo: str,
    initial_prompt: str | None,
) -> dict[str, Any]:
    normalized = ensure_mono_float32(samples)
    normalized = resample_if_needed(normalized, sample_rate, DEFAULT_SAMPLE_RATE)
    try:
        result = mlx_whisper.transcribe(
            normalized,
            path_or_hf_repo=model_repo,
            language=language or None,
            initial_prompt=initial_prompt,
            verbose=False,
        )
    except Exception as exc:  # pragma: no cover - depends on local model availability
        raise VoiceToClawError(f"Local transcription failed for model {model_repo}: {exc}") from exc
    text = str(result.get("text") or "").strip()
    if not text:
        raise VoiceToClawError("Local transcription returned empty text")
    return {
        "text": text,
        "language": result.get("language"),
        "segments": result.get("segments", []),
        "modelRepo": model_repo,
        "sampleRate": DEFAULT_SAMPLE_RATE,
    }


def extract_infer_transcript(payload: dict[str, Any]) -> str:
    direct = str(payload.get("text") or payload.get("transcript") or "").strip()
    if direct:
        return direct
    outputs = payload.get("outputs")
    if isinstance(outputs, list):
        for item in outputs:
            if not isinstance(item, dict):
                continue
            for key in ("text", "transcript", "content"):
                value = item.get(key)
                if isinstance(value, str) and value.strip():
                    return value.strip()
            data = item.get("data")
            if isinstance(data, dict):
                for key in ("text", "transcript", "content"):
                    value = data.get(key)
                    if isinstance(value, str) and value.strip():
                        return value.strip()
    raise VoiceToClawError("OpenClaw infer returned no transcript text")


def transcribe_with_openclaw_infer(
    audio_path: Path,
    *,
    language: str,
    model: str,
    prompt: str | None,
) -> dict[str, Any]:
    cmd = [
        "openclaw",
        "infer",
        "audio",
        "transcribe",
        "--file",
        str(audio_path),
        "--model",
        model,
        "--json",
    ]
    if language:
        cmd.extend(["--language", language])
    if prompt:
        cmd.extend(["--prompt", prompt])
    completed = subprocess.run(cmd, check=False, capture_output=True, text=True)
    if completed.returncode != 0:
        raise VoiceToClawError(completed.stderr.strip() or completed.stdout.strip() or "openclaw infer failed")
    payload = json.loads(completed.stdout)
    return {
        "text": extract_infer_transcript(payload),
        "payload": payload,
        "model": model,
    }


def send_to_openclaw(
    transcript: str,
    *,
    agent: str,
    session_id: str | None,
    thinking: str,
    timeout_seconds: int,
    json_output: bool,
) -> tuple[int, str, str]:
    cmd = ["openclaw", "agent"]
    if session_id:
        cmd.extend(["--session-id", session_id])
    else:
        cmd.extend(["--agent", agent])
    if thinking:
        cmd.extend(["--thinking", thinking])
    if timeout_seconds > 0:
        cmd.extend(["--timeout", str(timeout_seconds)])
    if json_output:
        cmd.append("--json")
    cmd.extend(["--message", transcript])
    completed = subprocess.run(cmd, check=False, capture_output=True, text=True)
    return completed.returncode, completed.stdout, completed.stderr


def build_runtime_dir(base_dir: Path) -> Path:
    run_dir = base_dir / timestamp_slug()
    run_dir.mkdir(parents=True, exist_ok=True)
    return run_dir


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Record from microphone, transcribe, and optionally send to OpenClaw.")
    parser.add_argument("--list-inputs", action="store_true", help="List available input devices and exit.")
    parser.add_argument("--device", help="Input device index or name substring. Defaults to DJI MIC MINI if found.")
    parser.add_argument("--seconds", type=float, default=6.0, help="Fixed recording length in seconds.")
    parser.add_argument("--ptt", action="store_true", help="Press Enter to start and stop recording instead of fixed duration.")
    parser.add_argument("--sample-rate", type=int, default=DEFAULT_SAMPLE_RATE, help="Recording sample rate.")
    parser.add_argument("--channels", type=int, default=DEFAULT_CHANNELS, help="Recording channel count.")
    parser.add_argument("--file", help="Transcribe an existing audio file instead of recording from microphone.")
    parser.add_argument(
        "--transcriber",
        choices=["local-mlx", "openclaw-infer"],
        default="local-mlx",
        help="Speech-to-text backend.",
    )
    parser.add_argument(
        "--profile",
        choices=sorted(DEFAULT_MODEL_PROFILES),
        default=DEFAULT_MODEL_PROFILE,
        help="Local MLX Whisper profile.",
    )
    parser.add_argument("--model-repo", help="Override the MLX Whisper Hugging Face repo id.")
    parser.add_argument("--infer-model", default="openai/gpt-4o-transcribe", help="Model for openclaw infer audio transcribe.")
    parser.add_argument("--language", default=DEFAULT_LANGUAGE, help="Spoken language hint, e.g. zh or en.")
    parser.add_argument("--initial-prompt", help="Optional transcription prompt for names or jargon.")
    parser.add_argument("--runtime-dir", default=str(DEFAULT_RUNTIME_DIR), help="Where to save audio and transcript artifacts.")
    parser.add_argument("--transcribe-only", action="store_true", help="Do not send transcript to OpenClaw.")
    parser.add_argument("--agent", default=DEFAULT_AGENT, help="OpenClaw agent id when sending transcript.")
    parser.add_argument("--session-id", help="Existing OpenClaw session id to continue.")
    parser.add_argument("--thinking", default="off", help="Thinking level for openclaw agent send.")
    parser.add_argument("--timeout", type=int, default=45, help="Timeout in seconds for openclaw agent.")
    parser.add_argument("--json", action="store_true", help="Ask openclaw agent for JSON output and save it verbatim.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    if args.list_inputs:
        return print_input_devices()

    runtime_dir = build_runtime_dir(Path(args.runtime_dir).expanduser())
    metadata: dict[str, Any] = {
        "createdAt": datetime.now().isoformat(),
        "transcriber": args.transcriber,
        "language": args.language,
    }
    initial_prompt = (
        args.initial_prompt
        or os.environ.get("MIRA_LIGHT_STT_INITIAL_PROMPT")
        or DEFAULT_INITIAL_PROMPT
    )

    samples: np.ndarray
    sample_rate: int
    audio_path = runtime_dir / "input.wav"

    if args.file:
        source_path = Path(args.file).expanduser().resolve()
        if not source_path.is_file():
            raise VoiceToClawError(f"Audio file not found: {source_path}")
        samples, sample_rate = load_audio_file(source_path)
        save_wav(samples, sample_rate=sample_rate, path=audio_path)
        metadata["sourceFile"] = str(source_path)
    else:
        device = resolve_input_device(args.device)
        metadata["inputDevice"] = device
        if args.ptt:
            recorded = record_push_to_talk(
                device_index=int(device["index"]),
                sample_rate=args.sample_rate,
                channels=args.channels,
            )
        else:
            recorded = record_fixed_duration(
                device_index=int(device["index"]),
                sample_rate=args.sample_rate,
                channels=args.channels,
                seconds=args.seconds,
            )
        samples = ensure_mono_float32(recorded)
        sample_rate = int(args.sample_rate)
        save_wav(samples, sample_rate=sample_rate, path=audio_path)

    transcript_payload: dict[str, Any]
    if args.transcriber == "local-mlx":
        model_repo = args.model_repo or DEFAULT_MODEL_PROFILES[args.profile]
        transcript_payload = transcribe_local(
            samples,
            sample_rate=sample_rate,
            language=args.language,
            model_repo=model_repo,
            initial_prompt=initial_prompt,
        )
    else:
        transcript_payload = transcribe_with_openclaw_infer(
            audio_path,
            language=args.language,
            model=args.infer_model,
            prompt=initial_prompt,
        )

    raw_transcript = transcript_payload["text"].strip()
    transcript = normalize_transcript_aliases(raw_transcript)
    transcript_payload["rawText"] = raw_transcript
    transcript_payload["text"] = transcript
    transcript_payload["normalizationApplied"] = transcript != raw_transcript
    transcript_path = runtime_dir / "transcript.txt"
    transcript_path.write_text(transcript + "\n", encoding="utf-8")
    (runtime_dir / "transcript.json").write_text(
        json.dumps(transcript_payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    metadata["audioPath"] = str(audio_path)
    metadata["transcriptPath"] = str(transcript_path)
    metadata["transcriptPreview"] = transcript
    metadata["rawTranscriptPreview"] = raw_transcript
    metadata["initialPrompt"] = initial_prompt
    if args.transcriber == "local-mlx":
        metadata["modelProfile"] = args.profile
        metadata["modelRepo"] = transcript_payload.get("modelRepo")
    else:
        metadata["inferModel"] = args.infer_model

    print(f"Transcript: {transcript}")

    if args.transcribe_only:
        (runtime_dir / "session.json").write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"Saved artifacts under: {runtime_dir}")
        return 0

    code, stdout, stderr = send_to_openclaw(
        transcript,
        agent=args.agent,
        session_id=args.session_id,
        thinking=args.thinking,
        timeout_seconds=args.timeout,
        json_output=args.json,
    )
    metadata["openclawExitCode"] = code

    if stdout:
        (runtime_dir / ("claw-response.json" if args.json else "claw-response.txt")).write_text(stdout, encoding="utf-8")
        print(stdout.strip())
    if stderr:
        (runtime_dir / "claw-response.stderr.txt").write_text(stderr, encoding="utf-8")
        if not stdout:
            print(stderr.strip(), file=sys.stderr)

    (runtime_dir / "session.json").write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Saved artifacts under: {runtime_dir}")
    return 0 if code == 0 else code


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except VoiceToClawError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        raise SystemExit(1)
