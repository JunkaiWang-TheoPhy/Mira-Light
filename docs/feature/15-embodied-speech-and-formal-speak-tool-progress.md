# Embodied Speech and Formal Speak Tool Progress

## Current Status

`Mira Light` 现在已经不只是“本机能播音频”。

在当前验证机器上，这条能力已经进一步被正式封装成 Claw 可调用的工具：

- repo 里有受约束的 `speak` 实现
- live bridge 暴露了正式 endpoint
- plugin 暴露了 `mira_light_speak`
- 并且已经完成真实外放验证

所以更准确的说法是：

本机音频/TTS 基础能力已经从 machine-specific helper，推进成了 `Mira` 的正式身体出口之一。

## What The Repository Now Contains

这一轮之后，仓库已经具备一条完整的 formal speak path：

- `scripts/mira_light_audio.py` 负责选择本机说话/播放命令
- `scripts/mira_light_runtime.py` 新增 `speak_text` 和 payload 校验
- `tools/mira_light_bridge/bridge_server.py` 新增 `POST /v1/mira-light/speak`
- `tools/mira_light_bridge/openclaw_mira_light_plugin/index.mjs` 新增 `mira_light_speak` tool
- `scripts/sync_local_mira_light_service.py` 现在会把 `mira_light_audio.py` 一起同步到 service copy

此外，workspace 层也同步补上了使用边界：

- `mira_light_speak` 只应用于短句、host line、确认语和简短安抚语
- 更复杂的表达仍然优先由 scene 承担

## What Has Been Verified On The Verified Machine

这条能力已经完成了三层验证：

### 1. 基础音频与 TTS 路径可用

当前机器已经确认具备：

- 蓝牙音箱输出
- 本地 TTS 文件生成
- `OpenClaw` first-party TTS 生成与播放

### 2. Live bridge speak endpoint 已经可用

当前 live bridge 已经实际返回：

- `GET /health` 正常
- `POST /v1/mira-light/speak` 可用
- speak 请求可以返回 `HTTP 200`

### 3. 真实外放已经打通

通过 live bridge 发送短句后，实际执行的命令已经确认是：

- `speaker-hp-openclaw-tts-play "你好，我是 Mira。"`

也就是说，现在跑通的不是“一个本地脚本”，而是：

```text
Claw tool
-> plugin
-> bridge
-> runtime
-> local OpenClaw TTS / speaker path
-> Bluetooth speaker playback
```

## Interaction Boundary

这条线虽然已经可用，但被故意做成了受约束的能力，而不是任意外放器。

当前边界包括：

- `text` 必须存在
- 长度上限是 `80` 个字符
- `voice` 目前限制为 `tts`、`openclaw`、`say`
- `wait` 必须是布尔值
- 运行时会继续遵守 manual control 边界
- 多步具身表达仍应优先使用 scene

因此它更适合：

- 主持短句
- 确认语
- 安抚语
- 调试与现场验证

而不适合被当成一个长段自由播报器。

## Why This Matters

这一步真正完成的是“声音正式进入 Mira 的身体接口”。

之前已经能出声，但更像验证机器上的 helper extension。

现在则不同：

- Claw 可以用统一工具名调用说话能力
- bridge/runtime 可以记录 speak 行为
- 现场操作时不需要再记 shell helper 命令
- 后续也更容易把说话和 scene 编排在一起

## Relationship To The Existing Audio/TTS Doc

[12-local-audio-and-tts-progress.md](./12-local-audio-and-tts-progress.md) 记录的是机器级音频与 TTS 基础能力。

这篇文档记录的是下一步：

- 把那条基础能力封装成正式的 `Mira` 工具体验
- 并确认它已经在当前 Claw 链路里 live 可用

## Recommended External Framing

> `Mira Light` 现在已经拥有一条正式的 Claw-native 语音输出路径。
> 这条路径不是孤立的本地脚本，而是以 `mira_light_speak` tool 的形式接入了 plugin、bridge 和 runtime，
> 并且已经在验证机器上完成真实外放。与此同时，它仍然保持 scene-first 和短句约束，不会把 Mira 退化成任意播报器。
