# OpenClaw Local Audio And TTS

This machine has a local Bluetooth-speaker playback path for OpenClaw.

Primary speaker:

- Name: `HP BTS01 Bluetooth Speaker`
- Bluetooth MAC: `6d-db-b4-e4-e0-d6`

Available local commands:

- `speaker-hp-status`
  - Shows Bluetooth and current audio-output state.
- `speaker-hp-use`
  - Connects the HP speaker and switches macOS output to it.
- `speaker-hp-release`
  - Switches output back to `Mac mini扬声器` and disconnects the HP speaker.
- `speaker-hp-play <audio-file>`
  - Plays an existing local audio file through the HP Bluetooth speaker.
- `speaker-hp-say <text...>`
  - Speaks text directly with macOS system voice through the HP Bluetooth speaker.
- `speaker-hp-tts-play <text...>`
  - Generates MP3 TTS with the bundled `node-edge-tts` runtime, then plays it through the HP Bluetooth speaker.
- `speaker-hp-tts-file --output <file.{mp3|wav|m4a|aiff}> <text...>`
  - Generates a local speech file. Default voice is `zh-CN-XiaoyiNeural`.
- `speaker-hp-openclaw-tts-play <text...>`
  - Uses `openclaw infer tts convert` with the configured OpenClaw TTS provider, then plays the result through the HP Bluetooth speaker.
- `speaker-hp-openclaw-tts-file --output <file.mp3> <text...>`
  - Uses OpenClaw's first-party TTS pipeline to generate a saved speech file.

Suggested usage:

- If the user wants immediate spoken playback on this Mac, prefer `speaker-hp-tts-play`.
- If the user explicitly wants OpenClaw's first-party provider-backed TTS path, prefer `speaker-hp-openclaw-tts-play`.
- If the user wants a saved audio artifact, use `speaker-hp-tts-file`.
- If network TTS fails, fall back to `speaker-hp-say`.
- If the user already has an audio file, use `speaker-hp-play`.

OpenClaw exec notes:

- Gateway/default exec host is currently `gateway`.
- A connected macOS node is also available as `胡胡立桐的Mac mini`.
- Both gateway and node approvals already allow the speaker commands and their supporting binaries.
