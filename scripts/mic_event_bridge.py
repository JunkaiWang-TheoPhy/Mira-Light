#!/usr/bin/env python3
"""Bridge lightweight microphone/text events into the Mira Light runtime."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
import struct
import urllib.error
import urllib.request
import wave
from typing import Any

from mira_voice_intents import action_for_intent, bridge_payload_for_intent, classify_intent


DEFAULT_BRIDGE_URL = "http://127.0.0.1:9783"


def load_wav_mono(path: Path) -> tuple[list[float], int]:
    with wave.open(str(path), "rb") as handle:
        channels = handle.getnchannels()
        sample_width = handle.getsampwidth()
        frame_rate = handle.getframerate()
        frame_count = handle.getnframes()
        raw = handle.readframes(frame_count)

    if sample_width == 1:
        fmt = f"<{frame_count * channels}B"
        scale = 128.0
        offset = 128.0
    elif sample_width == 2:
        fmt = f"<{frame_count * channels}h"
        scale = 32768.0
        offset = 0.0
    elif sample_width == 4:
        fmt = f"<{frame_count * channels}i"
        scale = float(2**31)
        offset = 0.0
    else:
        raise RuntimeError(f"Unsupported wav sample width: {sample_width}")

    unpacked = struct.unpack(fmt, raw)
    samples: list[float] = []
    for index in range(0, len(unpacked), channels):
        frame = unpacked[index : index + channels]
        mono = (sum(frame) / len(frame)) - offset
        samples.append(float(mono) / scale)
    return samples, frame_rate


def rms_level(samples: list[float]) -> float:
    if not samples:
        return 0.0
    return math.sqrt(sum(sample * sample for sample in samples) / len(samples))


def peak_level(samples: list[float]) -> float:
    if not samples:
        return 0.0
    return max(abs(sample) for sample in samples)


def zero_crossing_rate(samples: list[float]) -> float:
    if len(samples) < 2:
        return 0.0
    crossings = 0
    prev_positive = samples[0] >= 0.0
    for sample in samples[1:]:
        positive = sample >= 0.0
        if positive != prev_positive:
            crossings += 1
        prev_positive = positive
    return crossings / float(len(samples) - 1)


def analyze_sigh_audio(
    samples: list[float],
    *,
    sample_rate: int,
    min_duration_ms: int,
    min_rms: float,
    max_zero_crossing_rate: float,
) -> dict[str, Any]:
    duration_ms = (len(samples) / float(sample_rate)) * 1000.0 if sample_rate > 0 else 0.0
    rms = rms_level(samples)
    peak = peak_level(samples)
    zcr = zero_crossing_rate(samples)

    detected = (
        duration_ms >= min_duration_ms
        and rms >= min_rms
        and peak >= min_rms * 1.6
        and zcr <= max_zero_crossing_rate
    )
    confidence = 0.0
    if detected:
        duration_score = min(1.0, duration_ms / max(float(min_duration_ms), 1.0))
        rms_score = min(1.0, rms / max(min_rms, 1e-6))
        zcr_score = 1.0 - min(1.0, zcr / max(max_zero_crossing_rate, 1e-6))
        confidence = round(max(0.0, min(1.0, (duration_score + rms_score + zcr_score) / 3.0)), 4)

    payload = {
        "detected": detected,
        "event": "sigh_detected" if detected else "none",
        "durationMs": round(duration_ms, 1),
        "rms": round(rms, 6),
        "peak": round(peak, 6),
        "zeroCrossingRate": round(zcr, 6),
        "confidence": confidence,
    }
    if detected:
        payload["triggerPayload"] = {
            "confidence": confidence,
            "source": "mic-event-bridge",
            "cueMode": "scene",
        }
    return payload


def classify_transcript_event(transcript: str) -> dict[str, Any]:
    intent = classify_intent(transcript)
    action = action_for_intent(intent)
    payload = {
        "intent": intent,
        "transcript": transcript,
        "detected": bool(action),
    }
    if action is None:
        payload["event"] = "none"
        return payload

    bridge_payload = bridge_payload_for_intent(intent, transcript)
    payload["event"] = action["name"]
    payload["triggerPayload"] = bridge_payload
    return payload


def post_bridge_trigger(
    *,
    bridge_url: str,
    bridge_token: str,
    event_name: str,
    trigger_payload: dict[str, Any],
    timeout_seconds: float,
) -> dict[str, Any]:
    req = urllib.request.Request(
        f"{bridge_url.rstrip('/')}/v1/mira-light/trigger",
        data=json.dumps({"event": event_name, "payload": trigger_payload}).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            **({"Authorization": f"Bearer {bridge_token}"} if bridge_token else {}),
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout_seconds) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace").strip()
        raise RuntimeError(f"Bridge HTTP {exc.code}: {detail}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"Bridge request failed: {exc}") from exc


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Convert transcript/audio cues into Mira Light trigger events.")
    parser.add_argument("--audio-file", type=Path, help="Analyze a local wav file for a sigh-like event.")
    parser.add_argument("--transcript", help="Analyze text and map it to a bridge trigger.")
    parser.add_argument("--bridge-url", default=DEFAULT_BRIDGE_URL, help="Bridge base URL.")
    parser.add_argument("--bridge-token", default="", help="Bridge bearer token.")
    parser.add_argument("--timeout", type=float, default=8.0, help="Bridge request timeout in seconds.")
    parser.add_argument("--dry-run", action="store_true", help="Do not post to bridge; just print the analysis.")
    parser.add_argument("--min-duration-ms", type=int, default=700, help="Minimum sigh duration in milliseconds.")
    parser.add_argument("--min-rms", type=float, default=0.015, help="Minimum RMS energy for sigh detection.")
    parser.add_argument(
        "--max-zero-crossing-rate",
        type=float,
        default=0.12,
        help="Maximum zero-crossing rate to still count as a sigh-like low-frequency event.",
    )
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    if not args.audio_file and not args.transcript:
        parser.error("Either --audio-file or --transcript is required")

    if args.audio_file:
        samples, sample_rate = load_wav_mono(args.audio_file.expanduser().resolve())
        analysis = analyze_sigh_audio(
            samples,
            sample_rate=sample_rate,
            min_duration_ms=args.min_duration_ms,
            min_rms=args.min_rms,
            max_zero_crossing_rate=args.max_zero_crossing_rate,
        )
    else:
        analysis = classify_transcript_event(str(args.transcript or "").strip())

    print(json.dumps(analysis, ensure_ascii=False, indent=2))

    event_name = str(analysis.get("event") or "none")
    trigger_payload = analysis.get("triggerPayload")
    if event_name == "none" or not isinstance(trigger_payload, dict):
        return 0
    if args.dry_run:
        return 0

    response = post_bridge_trigger(
        bridge_url=args.bridge_url,
        bridge_token=args.bridge_token,
        event_name=event_name,
        trigger_payload=trigger_payload,
        timeout_seconds=args.timeout,
    )
    print(json.dumps(response, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
