# Mira Light Realtime Voice Interaction Design

## Scope

这份设计稿面向 `Mira Light` 的“实时语音互动版”。

目标不是只把一句话转成文字，而是把现有的：

- 本地麦克风输入
- 本地 Whisper 转写
- 云端文本回复
- 本地 TTS 播放
- Mira Light scene / trigger 控制

组织成一个可以在展位现场连续运行的交互链路。

这份设计优先满足：

- 本机可运行
- 现场可演示
- 断网时核心链路可退化
- 和现有 runtime / bridge / scenes 尽量复用

## Current Repository Base

仓库里已经有几块可直接复用的基础：

- [`../scripts/openclaw_voice_to_claw.py`](../scripts/openclaw_voice_to_claw.py)
  - 本地录音
  - 本地 MLX Whisper
  - 可把文本送给 OpenClaw
- [`../scripts/mira_realtime_claw_chat.py`](../scripts/mira_realtime_claw_chat.py)
  - 多轮循环
  - 本地 STT
  - 云端回复
  - 本地 TTS
- [`../scripts/mira_light_runtime.py`](../scripts/mira_light_runtime.py)
  - runtime trigger / scene 执行
- [`../tools/mira_light_bridge/README.md`](../tools/mira_light_bridge/README.md)
  - 本地 bridge API
  - `/v1/mira-light/trigger`
  - `/v1/mira-light/run-scene`

因此实时交互版不需要从零开始，重点是补齐“连续对话编排层”。

## Product Goal

展位上的体验应该接近：

1. 用户走近 Mira Light
2. 用户自然说一句话
3. 系统自动判断是否说完
4. 系统在短时间内理解语义
5. Mira Light 用灯光 / 姿态 / 简短语音做回应
6. 下一句还能接住上文，而不是每轮都重新开始

## Non-Goals

这版不以这些为目标：

- 长篇聊天助手
- 高并发多用户对话
- 完整会议纪要系统
- 远场多人说话人分离
- 完整唤醒词产品化

现场版本先优先做：

- 单人近场交互
- 1 到 2 句短回复
- 结构化意图触发

## Realtime Interaction Path

建议主链路如下：

```text
DJI MIC MINI
-> Audio Input / VAD
-> utterance segmentation
-> local MLX Whisper (small)
-> transcript normalization
-> intent + session-state update
-> cloud reply generation
-> Mira action trigger
-> local TTS playback
```

对应职责分为 3 个模块。

## Module 1: Speech IO

职责：

- 从 `DJI MIC MINI` 收音
- 自动断句
- 把音频交给 `small -> mlx-community/whisper-small-mlx-q4`
- 播放 Mira 回复语音

建议实现：

- 保留当前 `PTT` 作为稳定 fallback
- 新增自动连续监听模式
- 自动断句采用：
  - `VAD start`: `200ms`
  - `VAD end`: `800ms`
  - `min utterance`: `400ms`
  - `max utterance`: `6s`

建议参数：

```text
capture sample rate = 48000
channels = 1
asr sample rate = 16000
profile = small
```

建议文件职责：

- 继续以 [`../scripts/openclaw_voice_to_claw.py`](../scripts/openclaw_voice_to_claw.py) 里的录音和转写逻辑为基础
- 在 [`../scripts/mira_realtime_claw_chat.py`](../scripts/mira_realtime_claw_chat.py) 中增加连续监听入口
- 如有必要，再拆一个新文件：
  - `scripts/mira_voice_vad_loop.py`

## Module 2: Conversation Brain

职责：

- 保存最近几轮上下文
- 维护当前会话状态
- 判断意图
- 生成简短自然回复

### Session History

建议只保留最近 `4` 轮 history：

```json
[
  {"role": "user", "content": "我今天好累"},
  {"role": "assistant", "content": "辛苦了，要不要先休息一下？"}
]
```

理由：

- 足够支持“接上文”
- 不会让 prompt 膨胀过快
- 适合展位短对话

### Session State

建议维护一个轻量状态对象：

```json
{
  "mode": "chat",
  "lastIntent": "none",
  "lastScene": null,
  "lastUserText": "",
  "lastReplyText": "",
  "startedAt": "...",
  "lastActiveAt": "..."
}
```

初版只需要 3 个模式：

- `chat`
- `comfort`
- `farewell`

### Intent Layer

初版不要上复杂分类器，先用规则判断：

- 包含 `累 / 好累 / 辛苦 / 难受` -> `comfort`
- 包含 `拜拜 / 再见 / 我走了` -> `farewell`
- 包含 `好可爱 / 喜欢你 / 好漂亮` -> `praise`
- 其他 -> `chat`

这一层的目标不是完整理解用户，而是保证现场互动稳定。

### Reply Generation

继续复用当前云端回复 API，但把单轮请求改成多轮 `messages`：

```json
[
  {"role": "system", "content": "你是 Mira ... 当前模式是 comfort ..."},
  {"role": "user", "content": "我今天好累"},
  {"role": "assistant", "content": "辛苦了，要不要先休息一下？"},
  {"role": "user", "content": "为什么你这么说？"}
]
```

回复约束保持：

- 简体中文
- 1 到 2 句
- 简短自然
- 不用 emoji

建议直接扩展 [`../scripts/mira_realtime_claw_chat.py`](../scripts/mira_realtime_claw_chat.py)：

- `send_via_cloud_agent()` 改为支持 `messages`
- 新增 `ConversationSession`
- 新增 `classify_intent()`
- 新增 `build_messages()`
- 新增 `update_session()`

## Module 3: Mira Action Layer

职责：

- 把对话意图映射成具身动作
- 调现有 runtime / bridge
- 决定回复时是否联动灯光与姿态

建议不要直接把“原始文本”拿去驱动动作，而是先转成结构化事件。

推荐映射：

- `comfort`
  - trigger: `voice_tired`
  - scene: `voice_demo_tired`
- `farewell`
  - trigger: `farewell_detected`
  - scene: `farewell`
- `praise`
  - trigger: `celebration_triggered` 或后续单独加 `praise_detected`
- `chat`
  - 默认只播报，不强制切 scene

可优先复用：

- [`../scripts/mira_light_runtime.py`](../scripts/mira_light_runtime.py)
- [`../tools/mira_light_bridge/README.md`](../tools/mira_light_bridge/README.md)

建议触发方式：

```text
POST /v1/mira-light/trigger
{
  "event": "voice_tired",
  "payload": {
    "source": "voice-realtime",
    "transcript": "我今天好累"
  }
}
```

## State Machine

建议实时互动版采用一个很轻量的状态机：

```text
idle
-> listening
-> thinking
-> acting
-> listening
```

### idle

- 没人在说话
- 等待人声或 operator 启动

### listening

- 正在收音
- 用 VAD 判断起止

### thinking

- 运行 ASR
- 判断 intent
- 请求回复

### acting

- 触发 scene / trigger
- 播报回复
- 播放期间暂停监听

### return to idle

以下情况回到 `idle`：

- 用户明确说“退出对话”
- 检测到 `farewell`
- 连续静默 `30s`

## Turn-Boundary Strategy

这版建议采用：

- `voice detected for 200ms` -> start utterance
- `non-voice for 800ms` -> close utterance
- utterance `< 400ms` -> drop
- utterance `> 6s` -> force close

这样做的原因：

- 比固定 6 秒录音更自然
- 比纯音量阈值更稳
- 对展位短句交互已经足够

## Anti-Echo / Self-Listening Guard

连续对话里必须避免 Mira 自己把自己的 TTS 再听进去。

初版方案：

- TTS 播放时暂停收音
- TTS 结束后再恢复监听

后续增强可以考虑：

- 输出期间加短暂冷却时间
- 软件回声消除
- 单独的近讲麦和外放隔离

但初版只做“播报时暂停监听”就已经很值。

## Latency Budget

基于当前机器的已有表现，建议把展位预期控制在：

- `VAD + 断句等待`: `0.8s`
- `local small ASR`: `2.0s - 3.5s`
- `reply generation`: `0.8s - 2.5s`
- `trigger + TTS start`: `0.3s - 1.0s`

总交互时间目标：

- `3s - 6s` 内给出完整回应

如果需要更灵敏的“先动一下”体验，可以增加一个前置快速反应层：

- 一旦检测到用户正在说话
- Mira 先轻微抬头 / 暖灯
- 再等待完整语义回复

## Runtime Artifacts

建议持续沿用现有 runtime 目录风格，并新增会话级文件：

```text
runtime/realtime-claw-chat/<session>/
  session.json
  turn-001/
    input.wav
    transcript.json
    reply.txt
    reply.audio.json
    turn.json
```

建议在 `session.json` 中额外记录：

- session state snapshot
- recent history summary
- idle timeout config
- VAD config

## Implementation Plan

### Phase 1: Multi-turn context

目标：

- 先把“连续多轮”从采集层推进到语义层

改动：

- 给 [`../scripts/mira_realtime_claw_chat.py`](../scripts/mira_realtime_claw_chat.py) 加 `ConversationSession`
- 支持 history
- 把单轮 `messages` 改成多轮
- 保留 PTT / fixed-duration 模式不变

验收：

- 用户说“我今天好累”
- Mira 回复安慰
- 用户再说“为什么你这么说”
- 回复能接上文

### Phase 2: Auto segmentation

目标：

- 去掉对固定录音长度的依赖

改动：

- 加 VAD
- 用静音阈值自动断句
- 增加最短 / 最长句长保护

验收：

- 用户说短句时无需手动按键结束
- 说完后系统自动进入 thinking

### Phase 3: Intent -> action bridge

目标：

- 把“对话回复”升级为“具身互动”

改动：

- 增加 `comfort / farewell / praise` 意图
- 映射到 runtime trigger / scene
- 在 turn artifact 中记录 `intent` 和 `triggerResult`

验收：

- `我今天好累` 能触发 `voice_demo_tired`
- `拜拜` 能触发 `farewell`

### Phase 4: Booth hardening

目标：

- 做成可长时间跑的展位模式

改动：

- 静默超时
- 自说自听防护
- 错误恢复
- operator-safe fallback

验收：

- 连续运行不崩
- 网络波动时能优雅失败
- STT 或 reply 失败时仍有兜底话术

## Recommended File Layout

建议按下面的方式最小改动：

- `scripts/mira_realtime_claw_chat.py`
  - 主入口
  - session / history / state / reply
- `scripts/openclaw_voice_to_claw.py`
  - 继续承接录音、转写基础函数
- `scripts/mira_light_runtime.py`
  - 继续承接 trigger / scene 执行
- 可选新增 `scripts/mira_voice_realtime_session.py`
  - 如果 `mira_realtime_claw_chat.py` 变太长，再拆出 session 管理

## Recommended First Command

在第一阶段完成前，最实用的启动方式仍建议保留当前入口：

```bash
./.venv/bin/python scripts/mira_realtime_claw_chat.py \
  --device "DJI MIC MINI" \
  --profile small
```

第一阶段完成后，建议新增一个更明确的命令：

```bash
./.venv/bin/python scripts/mira_realtime_claw_chat.py \
  --device "DJI MIC MINI" \
  --profile small \
  --continuous
```

第二阶段再让 `--continuous` 默认启用 VAD 分段。

## Acceptance Criteria

可以把“实时交互版完成”定义为以下标准：

1. 用户无需手动重启脚本，就能连续对话多轮。
2. 系统能记住最近几轮上下文，而不是每轮重新开始。
3. `我今天好累` 能稳定触发 `voice_demo_tired`。
4. `拜拜` 能稳定触发 `farewell`。
5. Mira 说话时不会把自己的语音再次当成用户输入。
6. 在当前 Mac 上，完整一轮互动大多数情况下可控制在 `6s` 以内。

## Recommended Next Step

建议按下面顺序推进：

1. 先实现 `history + state + multi-turn messages`
2. 再实现 `VAD + auto segmentation`
3. 再把 `intent -> trigger` 接进 runtime / bridge
4. 最后再做展位 hardening

这样风险最低，也最符合当前仓库已经存在的能力边界。
