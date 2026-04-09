# 云端大脑延迟评估与本地热枢纽部署建议

## Current Status

当前可以更明确地回答一个关键问题：

`Mira Light` 是否适合把云端 `OpenClaw` 作为大脑？

结论是：

- 适合把云端作为高层认知与调度大脑
- 不适合把云端作为强实时身体反射大脑

更准确地说，当前最推荐的形态不是“全部搬上云端”，而是：

```text
云端认知 / 记忆 / 调度
-> 本地热枢纽
-> 本地 bridge / runtime
-> ESP32 Mira Light
```

这里的“本地热枢纽”指的就是仓库文档里描述的本地中转枢纽、router-hub 或 local edge 节点。

## Why This Matters

这个判断重要，是因为 `Mira Light` 不是一个纯聊天系统。

它同时涉及：

- 角色与记忆
- scene 编排
- 本地语音输出
- 灯光、姿态和舵机动作
- 真实设备网络可达性

因此问题不只是“云上能不能跑模型”，而是：

当 `Mira` 要像一个具身角色行动时，哪些部分应该放在云端，哪些部分必须留在本地。

## Architectural Principle

当前仓库里对这件事的推荐原则已经很明确：

- 云端 `OpenClaw` 不应直接访问局域网里的 `ESP32`
- 云端更适合调用服务器本地 bridge 地址
- 再通过反向隧道或私网通道回到本地热枢纽
- 本地热枢纽负责真正访问 `ESP32`

相关架构说明见：

- [../mira-light-router-hub-architecture.md](../mira-light-router-hub-architecture.md)
- [../mira-light-local-model-local-openclaw-cloud-openclaw-overview.md](../mira-light-local-model-local-openclaw-cloud-openclaw-overview.md)

最推荐的链路是：

```text
用户
-> 云端 OpenClaw
-> mira-light 插件
-> 服务器本地 bridge / loopback
-> 反向隧道 / 私网通道
-> 本地热枢纽
-> 本地 bridge / runtime
-> ESP32 Mira Light
```

## What Was Verified

这次判断不是纯理论，而是基于本机和云端服务器的实际检查。

### 1. 本机 Claw 已经是“本地身体”形态

当前本机 `OpenClaw` 节点已经明确采用：

- 本地 gateway
- 本地 `mira-light-bridge` plugin
- `bridgeBaseUrl = http://127.0.0.1:9783`

这说明当前本机形态已经天然符合“身体留在本地”的部署思路。

### 2. 云端服务器确实存在 OpenClaw 相关运行环境

在 `2026-04-09` 实际登录 `43.160.239.180` 后，已经确认：

- 有运行中的 `openclaw-gateway`
- 有 `mira-dm-relay.service`
- 存在多份 `openclaw.json` 配置痕迹
- `20656`、`19783`、`9783` 等端口可建立 TCP 连接

这说明云端不是“空白服务器”，而是已经有一套 `OpenClaw` 相关环境。

但当前看到的服务暴露形态更像内部链路或中转点，还不是一个面向公网直接调试的干净 body API。

## Measured Network Results

本次判断的核心依据之一，是 `2026-04-09` 同一天在两种网络环境下对同一云服务器 `43.160.239.180` 的实测结果。

### A. 旧网络环境

测量时间：

- `2026-04-09 11:26 CST`

测得：

- `ping` 平均 RTT 约 `788ms`
- 最低约 `772ms`
- 最高约 `811ms`
- 丢包约 `20%`

这类链路质量意味着：

- 云端工具调用会明显拖慢体感
- 多轮状态读取与动作确认会快速累积等待
- 具身互动会呈现明显迟滞

### B. 更换后的网络环境

测量时间：

- `2026-04-09 11:49:30 CST`

测得：

- `ping` 平均 RTT 约 `247ms`
- 最低约 `230ms`
- 最高约 `276ms`
- 丢包 `0%`

这说明更换网络后，云端链路质量已经显著改善。

它不再是“明显不适合”，而是进入了“可以认真采用，但需要分层”的区间。

## Latency Interpretation

需要特别说明的是：

- `ping` 不是完整工具调用时间
- TCP 建连可能比 `ping` 更快
- 但真实体验也不会只由 TCP 建连决定

对 `Mira Light` 这种系统而言，用户真正感受到的延迟通常来自四部分叠加：

- 云端与本地之间的网络 RTT
- 插件到 bridge 的调用开销
- 模型推理时间
- 本地 runtime 与设备执行时间

因此，把当前网络换算成体验时，更合理的估计是：

- 简单高层动作或短句语音：常见总等待约 `1s - 3s`
- 多工具调用或复杂推理：常见总等待约 `3s - 6s+`
- 高频闭环或连续细控制：体感通常仍然不够自然

## Current Realtime Voice Interpretation

在 `2026-04-09` 这一轮集成里，实时 booth 对话链已经采用：

```text
local VAD + local Whisper
-> local SSH tunnel
-> remote Lingzhu live adapter
-> remote OpenClaw / Spark
-> local TTS playback
```

因此，用户当前实际感受到的等待时间不只来自云端模型，还来自：

- 本地 VAD 等句尾静默
- 本地 STT
- 远端 prompt-pack / reply
- 本地 TTS 同步播放前等待

当前代码里最像“固定税”的参数是：

- `vad-end-ms = 650`
- `AudioCuePlayer.speak_text(..., wait=True)`

这意味着，哪怕网络质量稳定，完整回路里仍然有两段机器级延迟会稳定叠加在体感上。

## Highest-Value Low-Latency Knobs

对于当前这条实时 booth 链路，最值得优先尝试的优化不是先换模型，而是先动下面几项：

1. 更快切句  
   建议先试把 `vad-end-ms` 从 `650` 降到 `350-450`

2. 更轻的本地 STT profile  
   短句场景可优先试 `--profile fast`

3. 收紧上下文与 prompt-pack  
   减少非必要的 history turn 与 stale memory

4. 让回复更短  
   booth 现场更需要先开口，而不是多说半句

这类调整往往比“单纯换更大的云模型”更能直接改善体感。

## What Cloud Brain Is Good At

在当前链路质量下，把云端作为以下能力的承载层是合理的：

- 长期记忆与角色一致性
- 高层认知、解释与规划
- 对话生成
- scene 选择与策略判断
- 远程导演台式调度
- 低频的 `mira_light_speak`、scene 触发与状态查询

这些任务的共同特点是：

- 单次调用价值高
- 不要求几十毫秒级反馈
- 更依赖推理质量，而不是身体反射速度

## What Cloud Brain Is Not Good At

在当前链路质量下，不推荐让云端承担以下部分：

- 视觉跟随闭环
- 触摸后瞬时反应
- 高频舵机微调
- 高频状态轮询
- 强实时的声音打断与身体抢响应

这些任务的共同特点是：

- 对抖动很敏感
- 往往需要多轮快速来回
- 一旦跨公网，体验会迅速失去“像活物”的感觉

## Deployment Recommendation

当前最推荐的部署分工是：

### 云端负责

- 大模型推理
- 长记忆
- 高层策略
- 远程运营入口

### 本地热枢纽负责

- 反向隧道或私网连接
- `bridge` 与 `runtime`
- 本地语音播放
- scene 执行
- 安全边界、限流、日志与断网降级

### ESP32 负责

- 执行动作
- 提供状态
- 保持设备 API 简洁稳定

## Practical Conclusion

把云端作为 `Mira` 的大脑，当前已经是可行的。

但要把这个判断说完整，应该是：

> 云端适合作为 `Mira` 的认知大脑，不适合作为 `Mira` 的反射神经。

如果目标是：

- 角色更聪明
- 记忆更长
- 远程运营更方便

那么云端大脑是合适的。

如果目标是：

- 身体更灵敏
- 反应更自然
- 更像一个具身生命体

那么执行层和热枢纽仍然应该留在本地。

## Recommended External Framing

> 在当前验证条件下，`Mira Light` 已经适合采用“云端认知、本地身体”的分层架构。
> 云端 `OpenClaw` 或云端模型可以承担长期记忆、角色推理、scene 选择与远程调度，
> 但本地热枢纽仍应负责 bridge、runtime、语音输出与设备执行。
> 这样既能获得云端智能，又不会把具身体验交给高延迟公网链路。
