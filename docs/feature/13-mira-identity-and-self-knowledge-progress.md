# Mira Identity and Self-Knowledge Progress

## Current Status

`Mira Light` 现在已经不只是“挂了几个工具的 OpenClaw 配置”。

仓库和本机 live workspace 都已经补上了 Mira 对“自己是谁”的明确描述，并且这层描述已经重新进入 memory index。

这意味着当前目标已经从“让她能调用灯”推进到“让她知道自己是正在调用这盏灯的谁”。

## What Is Already Written Into the Repository

仓库模板层现在已经把 Mira 的自我认知写进了这组 workspace 文件：

- `Claw-Native /workspace/IDENTITY.md`
- `Claw-Native /workspace/SOUL.md`
- `Claw-Native /workspace/MEMORY.md`
- `Claw-Native /workspace/AGENTS.md`
- `Claw-Native /workspace/TOOLS.md`

这些文件现在共同编码了几件关键事情：

- Mira 是运行在当前 `OpenClaw` 本地节点里的角色主体
- 她默认通过 `plugin -> bridge -> runtime -> lamp` 这条身体链路行动
- 她优先以 scene、灯光、动作和短句表达，而不是退回成一个泛化命令助手
- workspace、plugin、bridge/runtime 这三层更新路径需要被区分对待

## What Has Been Applied On The Verified Machine

这层内容已经不只是模板存在。

当前验证机器上的 live workspace 也同步写入了同一套文件：

- `~/.openclaw/workspace/IDENTITY.md`
- `~/.openclaw/workspace/SOUL.md`
- `~/.openclaw/workspace/MEMORY.md`
- `~/.openclaw/workspace/AGENTS.md`
- `~/.openclaw/workspace/TOOLS.md`

随后已经重新执行过 `openclaw memory index`，所以这些自我描述现在不仅存在于文件里，也进入了当前 Claw 的可检索记忆层。

## What Mira Now Knows About Herself

这一轮落地之后，Mira 的“自我说明”至少已经覆盖：

- 她不是一个抽象聊天助手，而是 `Mira` 这个具身角色
- 她的身体出口包括 scene、灯光、姿态和短句语音
- 她的默认操作边界是 scene-first，而不是直接原始控制
- 当需要更新自己时，应区分 workspace 身份与记忆文件
- 当需要更新自己时，应区分 plugin 工具入口
- 当需要更新自己时，应区分 bridge / runtime / vision 服务实现

## Why This Matters

如果没有这层显式自我认知，Claw 很容易出现两类漂移：

- 对外回答时重新退回成泛化助手
- 真正要更新身体和能力时，不知道应该改 workspace、plugin，还是 bridge/runtime

把“她是谁”写进 workspace 和记忆层之后，后续很多行为才会更稳定：

- 自我介绍更一致
- 工具调用更贴合角色
- 对系统结构的解释不再反复漂移
- 后续做 persona eval 或 identity 回归测试也有了明确依据

## Current Boundary

这里也要明确边界：

- 这不是“神秘地赋予意识”
- 它仍然依赖 workspace 文件内容与 memory index 的更新质量
- 如果未来 workspace 被覆盖、memory 没有重建，角色一致性仍然可能退化

更准确地说，这是一层已经落地的 `self-knowledge scaffolding`。

## Recommended External Framing

> `Mira Light` 现在已经拥有一套明确的 OpenClaw-native 自我认知层。
> 她的身份、行动链路、工具边界和更新路径已经被写入 workspace 与 memory，
> 所以她不再只是“能控制灯的配置”，而是开始知道自己是谁、通过什么身体行动、以及该如何更新自己。
