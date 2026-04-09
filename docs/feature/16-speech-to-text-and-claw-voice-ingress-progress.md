# Speech-to-Text and Claw Voice Ingress Progress

## Scope

这份文档记录 `Mira-Light` 当前在“语音输入 -> 转文本 -> 送入 OpenClaw 理解”这条链路上的实际进展。

目标不是只做一个独立录音脚本，而是给后续的：

- 语音演示
- 本机交互
- 展位话筒输入
- Claw-Native 口语入口

提供一个已经可运行、可验证、可继续扩展的基础能力。

## Repository Status

仓库中已经补齐了以下内容：

- [`scripts/openclaw_voice_to_claw.py`](../../scripts/openclaw_voice_to_claw.py)
- [`scripts/run_openclaw_voice_to_claw.sh`](../../scripts/run_openclaw_voice_to_claw.sh)
- [`docs/mira-light-openclaw-voice-stt-guide.md`](../mira-light-openclaw-voice-stt-guide.md)

依赖也已经进入 [`requirements.txt`](../../requirements.txt)：

- `sounddevice`
- `soundfile`
- `mlx-whisper`

## Implemented Path

当前实际落地的路径是：

```text
Microphone
-> local capture
-> local MLX Whisper transcription
-> transcript.txt / transcript.json
-> openclaw agent --agent main --message "<transcript>"
```

而在 `2026-04-09` 之后，仓库里已经进一步出现了第二条更完整的 booth 实时路径：

```text
Microphone
-> continuous VAD
-> local MLX Whisper transcription
-> realtime session state
-> Lingzhu / OpenClaw reply
-> local TTS playback
-> optional Mira-Light trigger
```

对应入口是：

- [`../../scripts/mira_realtime_voice_interaction.py`](../../scripts/mira_realtime_voice_interaction.py)
- [`../../scripts/mira_realtime_claw_chat.py`](../../scripts/mira_realtime_claw_chat.py)

这条路径优先保证：

- 本机可运行
- 低依赖
- 足够快
- 不依赖云端 STT 的可用性

## Why Local MLX Whisper Was Chosen

这台机器上虽然已经配置了火山引擎文本模型，但当前 OpenClaw 的音频转写 provider 列表里并没有一个已经打通的 `volcengine` STT 入口。

同时，`openclaw infer audio transcribe` 在合成烟雾样本上的结果不稳定，不适合作为当前最主干的本机语音入口。

所以目前最稳妥的选择是：

- 文字理解继续走 OpenClaw 当前默认模型
- 语音转文本先走本地 MLX Whisper

## Current Profiles

当前本地转写 profile 为：

- `fast` -> `mlx-community/whisper-tiny`
- `balanced` -> `mlx-community/whisper-small-mlx-q4`
- `accurate` -> `mlx-community/whisper-medium-mlx-q4`

其中：

- `fast` 适合快速联调
- `balanced` 是当前默认值
- `accurate` 为更高精度预留，但首轮下载和推理成本更高

## Accuracy Improvements Already Applied

为了提升 Mira 相关术语的识别质量，脚本已经默认注入一段项目术语提示词。

它会优先帮助模型识别：

- `Mira`
- `OpenClaw`
- `Claw`
- `DJI`
- `smoke ok`
- `Doubao`

这一步对中文语句里混杂英文品牌名、项目名、短口令时很有帮助。

## Machine Verification

本机已经完成的验证包括：

- Python 音频层可见 `DJI MIC MINI`
- 本地 MLX Whisper 能从现成 wav 样本输出转写
- 转写结果已能进入 `openclaw agent --agent main`
- 每次运行都会落地产物到 `runtime/voice-sessions/<timestamp>/`

当前产物会包含：

- `input.wav`
- `transcript.txt`
- `transcript.json`
- `claw-response.txt` 或 `claw-response.json`
- `session.json`

## Reliability Improvements Already Applied

本轮已经额外补了两个细节：

1. 运行目录时间戳改成带微秒，避免同一秒内多次调用互相覆盖。
2. 本地模型加载失败时会返回更清晰的错误信息，而不是只抛底层堆栈。

## What Has Been Added Beyond The Original Ingress Script

相较于最初的 `openclaw_voice_to_claw.py`，当前 realtime 版本已经额外补上：

- 连续监听模式
- VAD 起止切句
- idle timeout 自动收尾
- 空文本跳过而不是整场退出
- 重复字符/重复 token 垃圾转写过滤
- runtime artifact 中的 `audioMetrics`、`memoryPolicy`、reply metadata 记录

所以这部分能力现在已经不只是“语音入口”，而是“完整 booth 对话入口”的基础层。

## What This Enables Next

在不连真灯的前提下，这条能力已经足够支撑：

- 展位口述指令转文字
- 语音驱动 director/operator 模式
- 语音回放与 persona eval 联动
- 之后接入 VAD、热词唤醒、持续监听

## Next Step

下一步最值得继续补的是：

- 继续降低 realtime 延迟
- 继续压缩非必要 prompt-pack 和记忆噪声
- 评估是否需要流式回复 / 流式 TTS
- 把 `additionalUserIds` 从全局 writer 升级成会话级 writer
