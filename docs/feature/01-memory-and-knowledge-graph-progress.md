# Knowledge Graph and Structured Memory Progress

## Scope of This Document

如果用更严格的工程语言来描述，当前仓库里已经落地的不是一个完整的
`knowledge graph database`，而是一套已经明显朝“知识图谱/关系图谱”方向
铺好的结构化记忆底座。

所以更准确的说法是：

- `已落地`：typed memory、embodied memory、session memory skeleton
- `已具备图谱友好性`：实体锚点、关系候选、事件类型、会话状态
- `尚未完整落地`：独立 graph store、关系抽取服务、图查询 API

## Structured Memory Capabilities Already Landed

当前仓库已经把 `Mira-Light` 从“只会执行动作的桥”推进成了“会产出结构化上下文
与记忆事件的 embodied node”。

主要已落地点：

- scene 成功/失败结果可写入 `memory-context`
- 设备状态与部分设备事件可选择性写入 `memory-context`
- runtime 会维护轻量 session note
- vision bridge 会维护 tracking 相关 session note
- bridge 配置中已经有 `memoryContext` 块
- runtime 已把 scene lifecycle 映射成 typed memory event

主要实现位置：

- [../../tools/mira_light_bridge/embodied_memory_client.py](../../tools/mira_light_bridge/embodied_memory_client.py)
- [../../tools/mira_light_bridge/bridge_server.py](../../tools/mira_light_bridge/bridge_server.py)
- [../../tools/mira_light_bridge/bridge_config.json](../../tools/mira_light_bridge/bridge_config.json)
- [../../scripts/mira_light_runtime.py](../../scripts/mira_light_runtime.py)
- [../../scripts/vision_runtime_bridge.py](../../scripts/vision_runtime_bridge.py)
- [../../tests/test_embodied_memory.py](../../tests/test_embodied_memory.py)
- [../../tests/test_vision_runtime_bridge.py](../../tests/test_vision_runtime_bridge.py)

## Why This Is Already Close to a Knowledge-Graph Foundation

一个真正可用的知识图谱，最重要的不是先有“图数据库”这三个字，而是先有：

- 稳定的实体锚点
- 明确的事件类型
- 可追踪的关系边
- 不会被噪音淹没的写入策略

而这些在当前仓库里已经开始出现。

### 1. Stable Entity Anchors Already Exist

当前结构里已经有一批天然可被图谱化的节点：

- `scene`
- `device`
- `session`
- `vision event`
- `writer identity`

例如：

- `userId=mira-light-bridge`
- `sessionId=mira-light-runtime`
- `sessionId=mira-light-vision`
- `kind=execution_outcome`
- `kind=scene_state`

这意味着后续如果要做图谱层，不需要从零重新设计对象世界。

### 2. Relationship Candidates Already Exist Naturally

当前事件流里已经隐含了很多关系：

- 某个 `scene` 导致了某次 `execution_outcome`
- 某个 `device event` 对应了某次 `warning/error`
- 某个 `vision event` 改写了某个 `tracking session-state`
- 某个 `session` 当前关联着 `nextStep`、`errors`、`keyResults`

这类“谁影响了谁、谁连接着谁”的信息，本质上已经是图谱边的雏形。

### 3. The Write Policy Is Low-Noise and Accretive

仓库并没有把所有 telemetry 都粗暴塞进记忆。

当前策略明确强调：

- 保留对后续判断有价值的 scene outcome
- 保留 degraded / unreachable / warning / error
- 忽略 `hello`
- 忽略 `heartbeat`
- 避免让低价值噪音淹没长期结构

这一点非常重要，因为真正能长成知识图谱的前提，不是“记录一切”，而是
“只保留会形成稳定语义骨架的事件”。

## The Graph Value of the Current Session Memory Layer

仓库当前的 session-memory skeleton 已经开始维护：

- `currentState`
- `nextStep`
- `taskSpec`
- `relevantFiles`
- `errors`
- `keyResults`
- `worklog`

这些字段虽然现在更像 working memory / session memory，而不是长程关系图谱，
但它们已经具备两个关键价值：

- 为后续图谱抽取提供结构化原料
- 让 `Mira-Light` 不只是留下“发生过什么”，还留下“当前还重要什么”

## What Is Not Fully Implemented Yet

如果对外介绍时要严谨，下面这些现在还不能说成“已经有了完整知识图谱”：

- 没有独立的 graph database
- 没有统一的人/设备/场景实体规范化层
- 没有自动 relationship extraction service
- 没有 graph traversal / graph query API
- 没有把 graph ranking 直接接入 OpenClaw retrieval pipeline

所以当前更合适的表述是：

`Mira-Light` 已经完成了面向知识图谱的结构化记忆与事件底座，但还没有把这层
单独产品化成完整的图谱系统。

## Recommended External Framing

如果你要对外讲，可以这样说：

> `Mira-Light` 现在已经不只是一个执行动作的灯，而是一个会把 scene、设备状态、
> vision 状态写成结构化记忆事件的 embodied node。它已经具备向知识图谱演进的
> 数据底座，包括 typed memory、session state 和低噪声写入策略。

## Reasonable Next Steps

如果后续真要把“知识图谱”彻底落地，建议按这个顺序走：

1. 先统一 entity schema
2. 再把现有 typed memory 映射成 relation edges
3. 再加 graph-oriented retrieval / summarization
4. 最后才考虑独立 graph store 或图查询接口

这样可以复用现有底座，而不是另起一套孤立系统。
