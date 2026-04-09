# Realtime Voice Dialogue, Lingzhu Memory, and Voice Mode Progress

## Current Status

`Mira-Light` 当前已经不只是“本地录一段音然后转文字”。

在验证机器上，这条链路已经推进成一条可连续运行、可接入远端 layered memory、可外放不同人设音色的完整实时对话回路：

```text
Microphone
-> local VAD continuous capture
-> local MLX Whisper STT
-> local realtime session state
-> remote Lingzhu live adapter prompt-pack
-> remote OpenClaw / Spark reply
-> local TTS playback
-> local bridge action trigger
```

更准确地说，当前已经同时具备：

- 实时连续监听
- 本地 STT 和垃圾片段过滤
- 远端 `Lingzhu` prompt-pack 记忆接入
- 云端 `gpt-5.3-codex-spark` 回复
- 本机蓝牙音箱 TTS 外放
- 正式 voice mode 切换

## Repository Status

仓库里已经包含这条链路的核心脚本与测试：

- [`../../scripts/mira_realtime_voice_interaction.py`](../../scripts/mira_realtime_voice_interaction.py)
- [`../../scripts/mira_realtime_claw_chat.py`](../../scripts/mira_realtime_claw_chat.py)
- [`../../scripts/mira_lingzhu_client.py`](../../scripts/mira_lingzhu_client.py)
- [`../../scripts/mira_light_audio.py`](../../scripts/mira_light_audio.py)
- [`../../scripts/ensure_mira_lingzhu_tunnel.sh`](../../scripts/ensure_mira_lingzhu_tunnel.sh)
- [`../../tests/test_realtime_voice_runtime_filters.py`](../../tests/test_realtime_voice_runtime_filters.py)
- [`../../tests/test_realtime_voice_trigger_flow.py`](../../tests/test_realtime_voice_trigger_flow.py)
- [`../../tests/test_mic_event_bridge.py`](../../tests/test_mic_event_bridge.py)
- [`../../tests/test_mira_lingzhu_client.py`](../../tests/test_mira_lingzhu_client.py)
- [`../../tests/test_mira_light_audio.py`](../../tests/test_mira_light_audio.py)

## Reply Path That Is Running Now

当前实时对话默认不是本地 fallback，也不是旧的火山直连回复链。

现在默认回复链路是：

```text
Mira realtime runtime
-> Lingzhu live adapter
-> remote OpenClaw gateway
-> openai-codex / gpt-5.3-codex-spark
```

本机入口会优先读取：

- [`/Users/huhulitong/.openclaw/mira-light-realtime.env`](/Users/huhulitong/.openclaw/mira-light-realtime.env)

其中已经固定：

- `MIRA_LIGHT_REPLY_BACKEND='lingzhu'`
- `MIRA_LIGHT_LINGZHU_BASE_URL='http://127.0.0.1:31879'`
- `MIRA_LIGHT_LINGZHU_AUTO_TUNNEL='1'`

这意味着本机脚本并不是直接裸连公网，而是：

```text
local runtime
-> local SSH tunnel 127.0.0.1:31879
-> 43.160.239.180 remote Lingzhu live adapter
-> remote root OpenClaw gateway
```

## Layered Memory Status

这部分现在已经不只是“有设计”，而是本机实际跑通了方案 B。

当前状态是：

- `Mira-Light bridge` 可以把 scene 和 device 状态写进远端 `memory-context`
- `Lingzhu live adapter` 会在回复前拉 `prompt-pack`
- 当前回复链已经能读取 `mira-light-bridge` 的 embodied memory

但这轮实现也补上了两个重要约束，避免“记忆把对话带偏”：

### 1. 简短问候轮禁用具身记忆推断

如果这一轮只是：

- `你好`
- `嗨`
- `hello`

这类简短问候，那么 reply 请求不会注入 `mira-light-bridge` 的 `additionalUserIds`。

这样做的目的是避免：

- 用户只说一句“你好”
- 模型却因为当前设备状态是 `comfort / breathing`
- 自动脑补成“你累了，先休息一下”

### 2. additional user id 允许显式清空

当前本地客户端和远端 adapter 都支持：

- 显式空 `additional_user_ids`
- `disable_default_additional_user_ids=true`

这让“问候轮不注入 embodied memory”不再只是本地约定，而是整条链路真正生效。

## Realtime Voice Runtime Status

当前实时语音主链路已经支持：

- `continuous`
- `ptt`
- `fixed`

其中 `continuous` 已经有：

- VAD 起止检测
- idle timeout 自动结束
- 短垃圾片段过滤
- 空文本不再整场退出
- 重复字符/重复 token 异常片段跳过
- 动作触发 cooldown

当前关键默认参数在 [`../../scripts/mira_realtime_voice_interaction.py`](../../scripts/mira_realtime_voice_interaction.py)：

- `vad-start-ms = 150`
- `vad-end-ms = 650`
- `profile = small`
- `history-turns = 4`

## Voice Output Status

当前实时对话默认已经不再依赖裸的 `tts/openclaw/say` 选择，而是收口成正式的 voice mode。

### Default Mode

默认 voice mode 是：

- `gentle_sister`

当前对应参数是：

- voice: `zh-CN-XiaoyiNeural`
- rate: `-12%`
- pitch: `-20%`

### Secondary Mode

新增 voice mode：

- `warm_gentleman`

当前对应参数是：

- voice: `zh-CN-YunxiNeural`
- rate: `-6%`
- pitch: `-6%`

### Compatibility

为了不打断旧调用，当前仍然兼容：

- `female` -> `gentle_sister`
- `male` -> `warm_gentleman`

## Machine Verification

当前验证机器已经完成了以下几类验证：

### 1. 单元测试

已经验证通过的测试包括：

- realtime voice runtime filter
- realtime trigger flow
- mic event bridge
- Lingzhu client
- voice mode preset

### 2. 真实历史音频回放

已经确认：

- 正常问候音频可以稳定进入 reply
- 重复字垃圾片段会被标记为 `repetitive-transcript`
- 空文本片段会被标记为 `empty-transcript`

### 3. 真实外放

已经通过 `HP BTS01 Bluetooth Speaker` 实际测试过：

- 女声 `XiaoyiNeural`
- 男声 `YunxiNeural`

### 4. Prompt-pack 行为验证

已经确认：

- 问候轮 `additionalUserIds` 可为空
- prompt-pack 在问候轮不会偷偷回填 `mira-light-bridge`

## How To Run

### 完整实时对话

```bash
scripts/run_mira_realtime_voice_interaction.sh
```

### 完整实时对话，但禁用动作触发

```bash
scripts/run_mira_realtime_voice_interaction.sh --no-trigger
```

### 指定 voice mode

```bash
scripts/run_mira_realtime_voice_interaction.sh --voice-mode gentle_sister
scripts/run_mira_realtime_voice_interaction.sh --voice-mode warm_gentleman
```

### 文件回放调试

```bash
scripts/run_mira_realtime_voice_interaction.sh \
  --file runtime/realtime-voice-interaction/2026-04-09T13-06-20-940875/turn-001/input.wav \
  --once \
  --dry-run-audio \
  --no-trigger
```

## Latency Interpretation

当前完整回路的延迟主要来自四段：

- VAD 等待句尾静默
- 本地 Whisper 推理
- 远端 Lingzhu / gateway / Spark 回复
- 本地 TTS 生成与同步播报

其中最像“固定税”的部分是：

- `vad-end-ms = 650`
- `speak_text(..., wait=True)`

因此当前最值得优先尝试的低延迟调法是：

```bash
scripts/run_mira_realtime_voice_interaction.sh \
  --vad-start-ms 100 \
  --vad-end-ms 400 \
  --profile fast \
  --no-trigger
```

这套参数的目标是：

- 更快切句
- 更快 STT
- 先把体感延迟压下来

## Current Boundary

虽然这条完整对话回路已经能跑，但仍然要区分边界：

- 它已经是“完整 booth 对话链路”
- 但还不是“流式回复 + 流式 TTS”的最低延迟形态
- 它已经接上 prompt-pack memory
- 但尚未把 `additionalUserIds` 全面升级成会话级 writer

所以更准确的对外表述是：

> `Mira-Light` 当前已经具备一条可运行、可验证、可外放的实时语音对话回路，
> 并且已经接入远端 layered memory 与云端 Spark 回复。
> 它现在的重点已不再是“能不能说话”，而是继续优化稳定性、延迟和 memory relevance。
