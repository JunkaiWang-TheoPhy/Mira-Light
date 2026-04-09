# Mira Light Feature Progress

这组文档用于集中记录 `Mira-Light` 当前已经落地的功能进展，方便后续：

- 查阅
- 对外介绍
- 区分“仓库已具备”“本机已验证”“仍在下一步”的边界

建议按主题阅读：

## Memory and Cognition

1. [Knowledge Graph and Structured Memory Progress](./01-memory-and-knowledge-graph-progress.md)
2. [Local Vector Memory and Semantic Retrieval Progress](./02-local-vector-memory-progress.md)
3. [Context, Proactivity, and Layered Memory Progress](./06-context-proactivity-and-layered-memory-progress.md)
4. [Mira Identity and Self-Knowledge Progress](./13-mira-identity-and-self-knowledge-progress.md)

## Runtime and Product Surface

1. [Scene System and Choreography Progress](./07-scene-system-and-choreography-progress.md)
2. [Director Console and Operator Workflow Progress](./08-director-console-and-operator-workflow-progress.md)
3. [Control Safety and OpenClaw Rollback Progress](./17-control-safety-and-openclaw-rollback-progress.md)
4. [Device Ingress and Receiver Progress](./09-device-ingress-and-receiver-progress.md)
5. [Vision Replay and Observability Progress](./05-vision-replay-and-observability-progress.md)
6. [Offline Rehearsal and Mock Validation Progress](./04-offline-rehearsal-progress.md)
7. [Embodied Speech and Formal Speak Tool Progress](./15-embodied-speech-and-formal-speak-tool-progress.md)
8. [Speech-to-Text and Claw Voice Ingress Progress](./16-speech-to-text-and-claw-voice-ingress-progress.md)

## Integration and Operations

1. [Claw-Native and Local OpenClaw Integration Progress](./03-claw-native-local-openclaw-progress.md)
2. [Local and Cloud Integration Progress](./10-local-and-cloud-integration-progress.md)
3. [Delivery, Audit, and Acceptance Progress](./11-delivery-audit-and-acceptance-progress.md)
4. [Local Audio and TTS Progress](./12-local-audio-and-tts-progress.md)
5. [Local Configuration and Model Preservation Progress](./14-local-configuration-and-model-preservation-progress.md)
6. [Control Safety and OpenClaw Rollback Progress](./17-control-safety-and-openclaw-rollback-progress.md)

## Reading Guide

为了避免把不同成熟度的内容混在一起，这组文档统一采用三层口径：

- `仓库已具备`：代码、脚本、模板、文档已经进入仓库
- `本机已验证`：已经在验证机器上实际跑通
- `下一步`：尚未完整实现，但当前结构已经为它留出了接口或数据底座

## Related Overview Docs

如果你希望先看更大的背景，再回来看具体 feature 进展，可以先读：

- [../mira-light-embodied-memory-integration-2026-04-09.md](../mira-light-embodied-memory-integration-2026-04-09.md)
- [../mira-light-offline-validation-stack.md](../mira-light-offline-validation-stack.md)
- [../../Claw-Native /docs/mira-light-claw-native-overview.md](../../Claw-Native%20/docs/mira-light-claw-native-overview.md)
- [../../Claw-Native /docs/mira-light-claw-native-rollout-state-2026-04-09.md](../../Claw-Native%20/docs/mira-light-claw-native-rollout-state-2026-04-09.md)

## What This Index Covers

这组 `feature` 文档现在已经覆盖：

- 结构化记忆、向量记忆、layered memory 与主动性
- Mira 的身份、自我认知与 workspace 自说明
- 场景系统、导演台、视觉回放与离线演练
- 简接收器、图像接收器与设备入口
- 本机 OpenClaw、Claw-Native、云端接入与 router-hub
- 设备交付、实现审计、验收标准
- 本机音频与 TTS 扩展
- 正式 speak tool、短句语音出口与本机模型保留规则
- 本机语音转文本与 Claw 语音入口
- 控制安全护栏、clamp / reject 行为与 OpenClaw 回滚闭环
