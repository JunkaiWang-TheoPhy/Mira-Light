# Vision Replay and Observability Progress

## What This Is Solving

`Mira-Light` 最容易“看起来像在工作、其实很难 review”的部分，就是：

- vision 输入到底变成了什么结构化事件
- runtime 为什么选了某个 scene
- scene 的节奏到底像不像 Mira

所以这部分进展的核心，不只是“能跑视觉链路”，而是“视觉与动作已经开始变得可
观测、可回放、可讨论”。

## Observability Capabilities Already Landed

### 1. Scene Trace Recorder

- [../../scripts/scene_trace_recorder.py](../../scripts/scene_trace_recorder.py)

当前已经可以把一个 scene 的完整执行轨迹导出为：

- JSON timeline
- HTML timeline

这让团队可以离线 review：

- step 顺序
- 时长
- LED / control 请求形态
- 情绪节奏是否可读

### 2. Vision Replay Bench

- [../../scripts/vision_replay_bench.py](../../scripts/vision_replay_bench.py)

当前已经可以把保存的 JPEG 序列重新送入：

- extractor
- event generation
- scene suggestion
- runtime decision rules

这样 vision-to-scene 的判断不再依赖“一次性的现场运气”，而可以离线重复验证。

### 3. Vision Runtime Bridge

- [../../scripts/vision_runtime_bridge.py](../../scripts/vision_runtime_bridge.py)

这层让视觉输出不会直接越权变成低层舵机命令，而是先落成更高层的状态/建议：

- `vision.latest.json`
- `vision.events.jsonl`
- `vision.bridge.state.json`

这对后续安全边界和编排都很重要。

## The Pipeline Already Taking Shape

现在更合适的理解方式是：

```text
camera / replay captures
-> extractor / event generation
-> vision.latest.json + vision.events.jsonl
-> vision runtime bridge
-> scene suggestion / runtime decision
-> trace / report
```

也就是说，视觉现在不只是“收帧”，而是已经开始产出可回放、可讨论、可被 runtime
吸收的中间层状态。

## Verified Offline Artifact Types

当前仓库已经把这类中间产物标准化到了 runtime 目录中，典型包括：

- `runtime/scene-traces/*.trace.json`
- `runtime/scene-traces/*.trace.html`
- `runtime/vision-replay/vision.latest.json`
- `runtime/vision-replay/vision.events.jsonl`
- `runtime/vision-replay/vision.bridge.state.json`
- `runtime/vision-replay/vision.replay.report.json`

这意味着后续无论是 debug、review、做汇报，都会比只看终端日志稳定得多。

## Why This Matters for Mira's Felt Presence

为什么这部分不只是工程可观测性，而跟 `Mira` 的气质也有关系？

因为很多“像不像 Mira”的问题，本质上都必须通过 trace/replay 才能讨论：

- `wake_up` 是不是太生硬
- `curious_observe` 有没有先观察后靠近
- `track_target` 会不会过度触发
- 视觉抖动会不会让它显得焦躁

如果没有 replay 和 trace，这些都很难被稳定复盘。

## Current Boundary

这层能力虽然已经非常有价值，但仍然不等于真实物理体验：

- 不能替代真实灯体的视觉材质反馈
- 不能替代舵机真实惯性与抖动
- 不能替代 booth 现场噪声和网络环境

所以当前这部分更准确的描述是：

`Mira-Light` 已经拥有视觉与动作编排的离线可观测性底座，但仍然需要实灯来完成
最终的物理感受验证。

## Recommended External Framing

> `Mira-Light` 现在已经不只是“能接相机”，而是拥有一套可回放、可追踪、可复盘
> 的视觉到场景决策链。视觉事件、runtime 状态和场景节奏都可以被导出和 review，
> 这让后续的 embodied behavior 调优变得更可控。
