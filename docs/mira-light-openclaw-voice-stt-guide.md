# Mira Light Local Speech-To-Text For OpenClaw

## Purpose

This guide explains the new local `speech -> transcript -> OpenClaw` path on the
current Mac.

The goal is simple:

- speak into a microphone
- convert speech to text quickly on the local machine
- pass the transcript into `openclaw agent`

## What was added

New files:

- [../scripts/openclaw_voice_to_claw.py](../scripts/openclaw_voice_to_claw.py)
- [../scripts/run_openclaw_voice_to_claw.sh](../scripts/run_openclaw_voice_to_claw.sh)

Related dependency additions:

- `sounddevice`
- `soundfile`
- `mlx-whisper`

## Why this path was chosen

On this machine:

- `volcengine` is configured for model inference
- but OpenClaw audio-transcription providers do not currently expose a working
  `volcengine` STT route
- `openclaw infer audio transcribe` with `openai` was not reliable enough on the
  synthetic smoke sample

So the most dependable implementation right now is:

```text
DJI MIC MINI
-> local recording
-> local MLX Whisper
-> transcript
-> openclaw agent --agent main --message "<transcript>"
```

This keeps the core speech-to-text path local and avoids blocking on cloud STT
provider behavior.

## Current microphone status

The repository-local Python audio layer can currently see these input devices:

- `HP BTS01 Bluetooth Speaker`
- `DJI MIC MINI`
- `BlackHole 2ch`

The script prefers `DJI MIC MINI` automatically when present.

## Quick start

List available input devices:

```bash
bash scripts/run_openclaw_voice_to_claw.sh --list-inputs
```

Push-to-talk with the DJI microphone:

```bash
bash scripts/run_openclaw_voice_to_claw.sh --ptt --device "DJI MIC MINI"
```

Fixed-length recording:

```bash
bash scripts/run_openclaw_voice_to_claw.sh --seconds 6 --device "DJI MIC MINI"
```

Transcribe only, without sending to OpenClaw:

```bash
bash scripts/run_openclaw_voice_to_claw.sh \
  --ptt \
  --device "DJI MIC MINI" \
  --transcribe-only
```

## Model profiles

The local MLX Whisper path supports three profiles:

- `fast`
- `small`
- `balanced`
- `accurate`

Current mapping:

- `fast` -> `mlx-community/whisper-tiny`
- `small` -> `mlx-community/whisper-small-mlx-q4`
- `balanced` -> `mlx-community/whisper-small-mlx-q4`
- `accurate` -> `mlx-community/whisper-medium-mlx-q4`

Default:

- `small`

The script also injects a default terminology prompt so mixed Chinese and
project-specific words are recognized more reliably. By default it biases
toward terms such as:

- `Mira`
- `OpenClaw`
- `Claw`
- `DJI`
- `smoke ok`

You can override that prompt explicitly:

```bash
bash scripts/run_openclaw_voice_to_claw.sh \
  --ptt \
  --device "DJI MIC MINI" \
  --initial-prompt "这是关于 Mira 与 OpenClaw 的中文语音。术语可能包含 Mira、Claw、Doubao。"
```

or through the environment:

```bash
export MIRA_LIGHT_STT_INITIAL_PROMPT="这是关于 Mira 与 OpenClaw 的中文语音。"
```

Example:

```bash
bash scripts/run_openclaw_voice_to_claw.sh \
  --ptt \
  --device "DJI MIC MINI" \
  --profile accurate
```

Notes:

- the first run downloads the selected MLX Whisper model from Hugging Face
- later runs reuse the local cache

## Saved artifacts

Each run creates a timestamped folder under:

```text
runtime/voice-sessions/<timestamp>/
```

Typical outputs:

- `input.wav`
- `transcript.txt`
- `transcript.json`
- `claw-response.txt` or `claw-response.json`
- `session.json`

The timestamp now includes microseconds to avoid collisions when two runs start
within the same second.

## Optional OpenClaw-infer mode

The script also supports:

```bash
--transcriber openclaw-infer
```

and defaults that route to:

- `openai/gpt-4o-transcribe`

But the local MLX Whisper path is the recommended default on this machine right
now because it is more controllable and does not depend on cloud STT response
behavior.

## Verified status on this machine

Validated on the current Mac:

- `DJI MIC MINI` is visible through the local Python audio stack
- `fast`, `small`, and `balanced` all resolve successfully
- the transcript can be sent into `openclaw agent --agent main`

Observed behavior:

- `fast` is good for quick iteration
- `small` is the best current default because it improves project term
  recognition, especially when paired with the default terminology prompt

## Recommended usage

For the current Mac, the most practical command is:

```bash
bash scripts/run_openclaw_voice_to_claw.sh \
  --ptt \
  --device "DJI MIC MINI" \
  --profile accurate
```

If you only want to inspect transcript quality first:

```bash
bash scripts/run_openclaw_voice_to_claw.sh \
  --ptt \
  --device "DJI MIC MINI" \
  --profile accurate \
  --transcribe-only
```
