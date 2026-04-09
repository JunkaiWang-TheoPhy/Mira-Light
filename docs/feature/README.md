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
9. [Camera CV and Runtime Bridge Progress](./20-camera-cv-runtime-bridge-progress.md)
10. [Director Console Vision UI 1-Minute Smoke Checklist](./21-director-console-vision-ui-smoke-checklist.md)
11. [Vision Pipeline CLI 1-Minute Smoke Checklist](./22-vision-pipeline-cli-1-minute-smoke-checklist.md)
12. [Vision + Runtime + Scene 5-Minute Integration Checklist](./23-vision-runtime-scene-5-minute-integration-checklist.md)
13. [Vision Validation Checklist Index](./24-vision-validation-checklist-index.md)
14. [On-Site Troubleshooting Decision Tree](./25-on-site-troubleshooting-decision-tree.md)
15. [Realtime Voice Dialogue, Lingzhu Memory, and Voice Mode Progress](./26-realtime-voice-dialogue-lingzhu-and-voice-mode-progress.md)
16. [Mock Sensors and 40-Pixel Visualization Progress](./27-mock-sensors-and-pixels-visualization-progress.md)
17. [Bus Servo Protocol and Four-Joint Mapping Memo](./21-bus-servo-protocol-and-four-joint-mapping-memo.md)
18. [Bus Servo Adapter Architecture and Scene Design](./22-bus-servo-adapter-architecture-and-scene-design.md)
19. [OpenClaw Plugin, Bridge API, and OpenAPI Draft](./23-openclaw-plugin-bridge-api-layering-and-openapi-draft.md)
20. [Vision Target Stability and Bridge Observability Upgrade](./29-vision-target-stability-and-bridge-observability-upgrade.md)
21. [Tabletop Target Mode First Pass](./30-tabletop-target-mode-first-pass.md)
22. [Tabletop Target Locking and Selection Policy](./31-tabletop-target-locking-and-selection-policy.md)
23. [Active Runtime Mira Light Bridge Tool Enablement and Live Validation](./32-active-runtime-mira-light-bridge-tool-enablement-and-live-validation.md)
24. [Portrait Person Count Tolerance Upgrade](./33-portrait-person-count-tolerance-upgrade.md)

## Integration and Operations

1. [Claw-Native and Local OpenClaw Integration Progress](./03-claw-native-local-openclaw-progress.md)
2. [Local and Cloud Integration Progress](./10-local-and-cloud-integration-progress.md)
3. [Delivery, Audit, and Acceptance Progress](./11-delivery-audit-and-acceptance-progress.md)
4. [Local Audio and TTS Progress](./12-local-audio-and-tts-progress.md)
5. [Local Configuration and Model Preservation Progress](./14-local-configuration-and-model-preservation-progress.md)
6. [Cloud Brain Latency and Local Hot-Hub Deployment Recommendation](./18-cloud-brain-latency-and-local-hot-hub-deployment-recommendation.md)
7. [Full Local Deployment and Data-Locality Security Recommendation](./19-full-local-deployment-and-data-locality-security-recommendation.md)
8. [Cloud OpenClaw Architecture, Backup, and Mira Light Overlay Progress](./28-cloud-openclaw-architecture-backup-and-mira-light-overlay-progress.md)

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
- mock 设备 richer sensor / pixel signal 与导演台图形化 mock 面板
- 简接收器、图像接收器与设备入口
- 本机 OpenClaw、Claw-Native、云端接入与 router-hub
- 设备交付、实现审计、验收标准
- 本机音频与 TTS 扩展
- 正式 speak tool、短句语音出口与本机模型保留规则
- 云端大脑延迟评估与本地热枢纽部署建议
- 完整本地部署、数据不出本地与高安全边界建议
- 本机语音转文本与 Claw 语音入口
- 完整实时语音对话、远端 Lingzhu prompt-pack 与 voice mode
- 控制安全护栏、clamp / reject 行为与 OpenClaw 回滚闭环
