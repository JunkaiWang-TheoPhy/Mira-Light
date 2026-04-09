# Context, Proactivity, and Layered Memory Progress

## Current Status

当前仓库已经不只是讨论“灯怎么动”，而是开始把 `Mira-Light` 放进更大的
`Mira + OpenClaw` 关系里理解：

- `Mira` 更像 context-aware companion layer
- `OpenClaw` 更像 execution engine
- `Mira-Light` 更像 embodied event producer 和具身执行节点

也就是说，这部分进展的核心不是新加了一个按钮，而是职责边界开始变清楚了。

## What the Architecture Docs Have Already Made Clear

基于 [../mira-context-proactivity-architecture.md](../mira-context-proactivity-architecture.md)
和 [../mira-light-to-mira-v3-layered-memory-integration-plan.md](../mira-light-to-mira-v3-layered-memory-integration-plan.md)，
当前已经明确了几条重要原则。

### 1. Mira Should Sit Above OpenClaw, Not Replace It

当前推荐的分工是：

- `Mira` 负责上下文连续性、意图判断、任务形成、时机判断、主动提示、人格表达
- `OpenClaw` 负责工具调用、运行时编排、系统执行闭环
- `Mira-Light` 负责 scene/runtime/vision/device 事件的具身生产与执行

这让整个系统不会陷入“所有东西都揉成一个 agent”的混乱结构。

### 2. Context Should Be Compressed into Tasks, Not Just Logged

当前架构文档已经很明确地提出：

- 不应该只做 dense screen logging
- 更应该抓 `intent anchors`
- 上下文最终应被压缩成可推进的 task object

这意味着 Mira 的价值不只是“记住发生过什么”，而是“知道下一步最值得推进什么”。

### 3. Proactivity Should Be Timing-Aware

当前定义的主动性不是“频繁打扰用户”，而是：

- 只提示，不执行
- 先准备，再等待确认
- 低风险动作才自动执行

这部分虽然现在更多还是架构原则，但它已经对后续设计口径产生了明确约束。

## Layered Memory Integration Progress

从 `Mira-Light -> Mira_v3` 的 layered memory 角度看，当前已经有两层成果。

### 1. The Foundation Already Exists

`Mira_v3` 侧当前已有：

- `memory-context`
- `session-memory`
- `prompt-pack`
- `additionalUserIds`

而 `Mira-Light` 侧当前已有：

- embodied memory writer 雏形
- scene outcome memory write
- device status / event selective write
- vision bridge session note skeleton

这意味着“写 memory”已经不是假设，而是现成能力。

### 2. The Full Loop Is Designed, but Not Fully Closed

当前目标闭环已经很清楚：

```text
Mira-Light scene / device / vision event
-> embodied memory write
-> Mira_v3 memory-context
-> prompt-pack
-> Mira decision
-> OpenClaw execution
-> Mira-Light runtime / bridge
```

但现在仍然要严谨地区分：

- `已具备`：memory write、session skeleton、prompt-pack-ready writer 设计
- `未完全闭环`：continuous context capture、timing-aware proactivity、完整 session-state 驱动 execution

## Why This Progress Matters

这部分进展的价值在于，它开始把 `Mira-Light` 从“一个受控灯具 demo”推进成：

- Mira 体系里的具身上下文节点
- 可以参与 prompt-pack 的记忆生产者
- 能被更高层判断逻辑重新吸收的 embodied runtime

这会直接影响以后怎么介绍项目：

- 不再只是“灯会动”
- 而是“灯的状态、视觉与 scene 结果能进入 Mira 的长期上下文体系”

## Current Boundary

目前还不能直接说已经拥有了完整的 proactive companion loop，因为以下内容仍未完全落地：

- 持续上下文捕捉系统
- 稳定 task formation pipeline
- 明确的 proactive timing engine
- 由 prompt-pack 驱动的长期闭环验证

所以更准确的表述是：

`Mira-Light` 已经开始接入上下文、记忆与 prompt-pack 体系，但主动性本身仍然主要
停留在“架构已定义、基础底座已开始落地”的阶段。

## Recommended External Framing

> `Mira-Light` 当前已经不只是一个会执行 scene 的设备节点，而是开始具备参与
> `Mira` layered memory 体系的能力。它可以把具身 scene、设备状态与 vision 事件
> 写成结构化上下文，为后续的 prompt-pack、时机判断与主动式陪伴提供底座。
