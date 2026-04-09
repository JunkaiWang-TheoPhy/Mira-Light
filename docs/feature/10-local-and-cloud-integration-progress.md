# Local and Cloud Integration Progress

## Current Status

当前仓库已经把 `Mira Light` 的接入路线梳理成了比较清楚的三条路径：

1. `ESP32 -> local model`
2. `ESP32 -> local OpenClaw`
3. `ESP32 -> cloud OpenClaw`

这意味着当前不是“只有一个模糊方向”，而是已经有多路径接入框架。

## The Overall Principle Is Already Clear

基于 [../mira-light-local-model-local-openclaw-cloud-openclaw-overview.md](../mira-light-local-model-local-openclaw-cloud-openclaw-overview.md)
和 [../mira-light-local-model-local-openclaw-cloud-openclaw-implementation-guide.md](../mira-light-local-model-local-openclaw-cloud-openclaw-implementation-guide.md)，
当前已经明确的总原则是：

`ESP32 Mira Light` 不应该直接“接大模型”。

更合理的链路是：

```text
ESP32
-> receiver / bridge
-> local model or OpenClaw
-> scene or action decision
-> callback to device API
```

这条链路让设备继续扮演：

- 执行端
- 状态上报端
- 文件/图像上传端

而让模型和 OpenClaw 扮演：

- 感知解释
- 场景选择
- 工具调用
- 编排决策

## Local OpenClaw Progress

本机 OpenClaw 这条线现在已经是仓库里最成熟的一条软件集成线之一。

相关文档已经形成了比较完整的包：

- local step-by-step
- plugin install/config
- final config snippet
- acceptance checklist
- Claw-Native templates and apply flow

这意味着本机 OpenClaw 接入已经不再只是一个想法，而是：

- 有模板
- 有自动化
- 有验收标准
- 有本机 rollout 记录

## Cloud OpenClaw Progress

云端 OpenClaw 这条线现在的核心结论也已经很明确：

- 不推荐服务器直接访问 ESP32
- 更推荐 `plugin -> bridge -> tunnel -> local edge`

相关支撑文档包括：

- router hub architecture
- current status
- implementation guide
- next steps
- delivery index

所以云端这条线虽然还没有完全实灯闭环，但结构设计已经比较稳定。

## Router-Hub Architecture Progress

当前 router-hub 方案已经明确了几个关键点：

- 云服务器与本地 ESP32 不在同一网络平面
- 服务器插件更适合只访问 `127.0.0.1`
- 本地 edge / router-hub 负责真正接触 ESP32
- reverse tunnel 或私网通道是更安全的第一阶段方案

这意味着“云端接入”已经不是一个模糊概念，而是有明确边界的部署方案。

## What Is Still Not Fully Landed

这一层现在的主要未完成项包括：

- 正式长期在线的本地 edge 主机未完全固化
- 实灯网络可达性仍可能是阻塞
- 云端到实灯的端到端长期在线验证还未完全完成

也就是说：

- `架构方向` 已经成熟
- `部分软件链路` 已经落地
- `实灯长期在线部署` 仍然需要继续完善

## Why This Matters

这部分进展让项目不再停留在“灯和模型怎么大概连一下”，而是已经能够回答：

- 本机怎么接
- 云端怎么接
- 为什么不能直连 ESP32
- 中转层该由谁承担
- acceptance 到底看什么

这对真正部署系统非常关键。

## Recommended External Framing

> `Mira-Light` 当前已经形成了从 local model、local OpenClaw 到 cloud OpenClaw 的多路径接入框架。
> 其中本机 OpenClaw 路线的软件集成已经较成熟，云端路线也已经明确收敛到 `plugin -> bridge -> tunnel -> local edge`
> 的安全部署模式。
