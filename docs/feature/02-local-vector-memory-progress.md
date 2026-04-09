# Local Vector Memory and Semantic Retrieval Progress

## Current Status

`Mira-Light` 相关的本地 `OpenClaw` 节点，已经具备了真正的本地 semantic
memory，而不再只是关键词检索。

更具体地说：

- `已验证机器` 上已经切到 `local embeddings`
- 当前 provider 是 `local`
- 当前搜索模式是 `hybrid`
- 已经不再依赖云端 embeddings API

## Core Capabilities Already Completed

### 1. Upgraded from FTS-Only to Local Semantic Memory

本地语义记忆现在通过下面这组能力落地：

- `node-llama-cpp`
- 本地 GGUF embedding 模型
- `openclaw memorySearch.provider = local`
- memory index 重建

验证机上使用的模型文件是：

- `~/.openclaw/models/embeddinggemma-300m-qat-Q8_0.gguf`

## Verified State

在已验证机器上，`openclaw memory status --deep --json` 的关键状态是：

- `provider = local`
- `requestedProvider = local`
- `vector.available = true`
- `vector.dims = 768`
- `custom.searchMode = hybrid`
- `embeddingProbe.ok = true`

这说明当前检索能力已经不是单纯的“搜到同一个词”，而是能开始做语义相近检索。

## What This Means for Mira

### 1. Retrieval No Longer Depends Only on Literal Matching

以前如果文档里写的是：

- `scene_hint`
- `tracking-oriented session note`
- `vision event pipeline`

而提问时写的是：

- “看到人之后怎么决定 scene”
- “视觉闭环怎么接”

那纯 FTS 可能命中不稳定。

切到本地 embeddings 之后，语义相近的问题更容易命中正确文档块。

### 2. Persona and Skill Recall Are More Stable

本地向量检索会直接影响：

- `openclaw memory search`
- agent 对 workspace 和记忆文件的召回质量
- `mira_memory_persona_eval.py` 这类评估工具的表现

这意味着 Mira 的“像不像自己”不再只依赖 prompt 静态注入，也开始依赖可检索的
长期语义记忆。

### 3. Repository Docs Are Now in Semantic Retrieval Scope

已验证机器上的 memory 配置已经把部分关键仓库文档接进 `memorySearch.extraPaths`。

这让本地 OpenClaw 在回答时，能把下面这些文档当成可检索知识源：

- `openclaw-esp32-control-guide`
- `mira-light-local-openclaw-plugin-install-config`
- `mira-light-vision-event-schema`
- `mira-light-single-camera-fourdof-vision-development-guide`
- `mira-light-router-hub-architecture`

## Repository Support Already in Place

虽然 embedding 模型文件本身不会直接提交进仓库，但仓库里已经有配套的落地材料：

- [../../scripts/apply_claw_native_local.py](../../scripts/apply_claw_native_local.py)
- [../../scripts/verify_local_openclaw_mira_light.py](../../scripts/verify_local_openclaw_mira_light.py)
- [../../Claw-Native /templates/openclaw.template.jsonc](../../Claw-Native%20/templates/openclaw.template.jsonc)
- [../../Claw-Native /docs/mira-light-claw-native-rollout-state-2026-04-09.md](../../Claw-Native%20/docs/mira-light-claw-native-rollout-state-2026-04-09.md)

这些内容负责：

- 把本机配置 materialize 出来
- 验证 memory/provider/model 状态
- 记录已验证机器上的真实 rollout 结果

## Current Boundary

这里也要区分“仓库有”和“机器上有”：

- `仓库里有`：模板、apply 脚本、verify 脚本、说明文档
- `机器上有`：本地模型文件、本地 node 依赖、实际 index、实际 vector search

也就是说，仓库现在已经具备“可重复落地”的自动化基础，但真正的本地语义检索
仍然需要在目标机器上完成一次 materialize 与 index。

## Recommended External Framing

> `Mira-Light` 对接的本地 OpenClaw 现在已经具备本地向量化语义记忆能力。它不再
> 只靠关键词检索，而是通过本地 embeddings + hybrid retrieval 做更贴近语义的
> memory search，而且这套能力已经在验证机器上跑通。
