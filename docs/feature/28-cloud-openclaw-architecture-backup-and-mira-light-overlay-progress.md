# Cloud OpenClaw Architecture, Backup, and Mira Light Overlay Progress

## Current Status

这次工作不是直接把云端 `OpenClaw` 改成一套全新的 `Mira Light` 运行时，而是先把服务器上的真实结构查清楚，再在不删除原有功能、性能说明和记忆的前提下，给现有 persona / workspace 模板加上一层 `Mira Light` 的身体语义。

已经完成的事情有三类：

1. 云端 `OpenClaw` 架构检索
2. `SOUL / ROLE / IDENTITY / MEMORY / AGENTS / TOOLS` 等关键文本与状态备份
3. 基于 `Mira Light` 当前仓库文档口径的增量改写

## What Was Actually Found On The Cloud Server

目标服务器是：

- host: `43.160.239.180`
- user: `ubuntu`
- verified at: `2026-04-09`

实际检索结果显示，这台机器上不是“只有一套干净的 OpenClaw 工作区”，而是至少有三条相关痕迹：

1. `~/.openclaw/workspace`
   - 当前非常轻
   - 检索时只有 `MI_BAND_LATEST.json`
2. `/home/ubuntu/mira_import/.openclaw`
   - 这是更丰富、长期使用过的 `OpenClaw` 状态树
   - 里面有 `openclaw.json`
   - 也有持久 identity 文件和 sqlite memory 数据库
3. `/home/ubuntu/mira-active-runtime`
   - 这是一套偏 `home-control / Rokid` 的 runtime blueprint
   - 不是等同于 `Mira Light` 现有本地 bridge/runtime 栈

同时还确认到一个关键事实：

- `/home/ubuntu/mira_import/.openclaw/openclaw.json` 里出现过 `workspace-openclaw-agents/main` 这样的路径指向
- 但检索时该目录并不存在

这意味着当前云端还有一层“配置指向”和“实际 live workspace 位置”不完全一致的问题。

## Which Files Were Treated As The Editable Persona Sources

这次没有直接去覆盖 `~/.openclaw/workspace`，而是把下面两组文件视为更安全的“人格/工作区模板源”：

- `/home/ubuntu/mira_import/mira/core/workspace/`
- `/home/ubuntu/mira_import/mira/core/persona/`

原因很简单：

- 这两处已经有现成的 `SOUL.md / IDENTITY.md / MEMORY.md / AGENTS.md / TOOLS.md / role.md`
- 它们更像云端当前可维护的“源模板”
- 而裸的 `~/.openclaw/workspace` 当时还没有成型文稿，直接往里面写容易误判 live path

## Backup Result

在任何文本修改前，已经先创建了时间戳备份：

- backup root: `/home/ubuntu/mira_import/mira/backups/mira-light-cloud-overlay-20260409T090500Z`

这次备份包含：

- `/home/ubuntu/mira_import/.openclaw/openclaw.json`
- `/home/ubuntu/mira-active-runtime/openclaw-config/openclaw.json`
- `~/.openclaw/workspace/MI_BAND_LATEST.json`
- `/home/ubuntu/mira_import/.openclaw/.openclaw/identity/device.json`
- `/home/ubuntu/mira_import/.openclaw/.openclaw/identity/device-auth.json`
- `/home/ubuntu/mira_import/.openclaw/.openclaw/memory/main.sqlite`
- `core/workspace/` 下的现有 persona / memory / tool 文稿
- `core/persona/` 下的现有 persona 文稿

所以这次增量修改是可回退的，不是“边看边改、改完没有原件”的状态。

## What Was Updated

已经在云端模板里做了增量追加的文件有：

- `/home/ubuntu/mira_import/mira/core/workspace/SOUL.md`
- `/home/ubuntu/mira_import/mira/core/workspace/IDENTITY.md`
- `/home/ubuntu/mira_import/mira/core/workspace/MEMORY.md`
- `/home/ubuntu/mira_import/mira/core/workspace/AGENTS.md`
- `/home/ubuntu/mira_import/mira/core/workspace/TOOLS.md`
- `/home/ubuntu/mira_import/mira/core/workspace/role.md`
- `/home/ubuntu/mira_import/mira/core/persona/SOUL.md`
- `/home/ubuntu/mira_import/mira/core/persona/IDENTITY.md`
- `/home/ubuntu/mira_import/mira/core/persona/role.md`

另外还新增了一份云端说明文档：

- `/home/ubuntu/mira_import/mira/docs/plans/mira-light-cloud-openclaw-overlay-2026-04-09.md`

## What The Overlay Added

这次增量修改加进去的，不是一整套替代人格，而是几条明确的 `Mira Light` 身体层原则：

- `Mira Light` 是 `Mira` 的身体、表情层和第一接触面
- 云端 `OpenClaw` 更适合承担高层理解、编排和记忆
- 本地 `bridge / runtime / safety` 更适合承担反射、执行和运动安全边界
- 云端优先理解 `scene / trigger / pose`
- 不应让模型直接把原始设备协议当作第一控制面
- 默认推荐链路是：
  `cloud OpenClaw -> Mira Light plugin -> SSH reverse tunnel -> local bridge -> runtime -> lamp`
- `Mira Light` 应该把“看见你、理解你、记住你、为你做点什么”变成可见动作

这些表述不是凭空写进去的，而是和当前仓库里已经成熟的本地口径对齐：

- `docs/feature/10-local-and-cloud-integration-progress.md`
- `docs/feature/13-mira-identity-and-self-knowledge-progress.md`
- `docs/feature/23-openclaw-plugin-bridge-api-layering-and-openapi-draft.md`
- `Claw-Native /workspace/SOUL.md`
- `Claw-Native /workspace/MEMORY.md`
- `Claw-Native /workspace/TOOLS.md`
- `tools/mira_light_bridge/README.md`

## What Was Intentionally Preserved

这次最重要的约束不是“写进去多少 Mira Light”，而是“不要把原来的东西冲掉”。

因此被明确保留的包括：

- 原有的 Mira 陪伴人格语气
- 原有的 `Mi Band` 相关记忆与读数边界
- 原有的本地设备、bridge、home-control 说明
- 原有的能力与性能记忆
- 原有的 `AttraX / Outlier` 用户偏好上下文

换句话说，这次做的是：

`旧有记忆层 + Mira Light 身体层`

而不是：

`删掉旧有记忆层 -> 换成一个新角色`

## Current Boundary

这里还要非常明确一个边界：

这次已经完成的是：

- 云端结构摸底
- 关键状态与文稿备份
- 模板源文件的非破坏式增量改写

但这次还没有完成的是：

- 确认云端正在运行的 `OpenClaw` 进程究竟加载哪一个 workspace 路径
- 把更新后的模板同步进那个真正 live 的 workspace
- 重建云端 memory index

所以目前更准确的说法是：

> 云端 `Mira Light` 相关人格与工作区文案已经完成备份与模板增量改写，但还没有把“模板层变化”完全推进到一个已验证的 live workspace path。

## Recommended Next Step

下一步最合理的顺序是：

1. 在云端确认真正被 `OpenClaw` 进程加载的 workspace 路径
2. 把这次修改后的 `core/workspace` 文件同步进去
3. 如果 live runtime 依赖可检索 prose memory，则重建 index
4. 再去接 `Mira Light plugin -> tunnel -> local bridge` 的实际调用链

## Reference Note

用户提到可以参考 `mira-light` 和 `mira-light-ai-that-sees-you` 的说明文件。当前仓库里没有检索到完全同名的 `mira-light-ai-that-sees-you` 文件，所以这次实际使用的是同一语义带上的现有材料，例如：

- `docs/ChatGPT-Mira-Light 仓库解读.md` 里关于“看见你、理解你、记住你、为你做点什么”的叙述
- `docs/feature/13-mira-identity-and-self-knowledge-progress.md`
- `Claw-Native /workspace/` 里已经成型的 `Mira` 自我说明

这保证了云端 overlay 的语义来源仍然和当前仓库主线一致。
