# Scene System and Choreography Progress

## Current Status

当前仓库已经具备一个成形的 `scene system`，而不是零散动作脚本。

这套系统现在已经明确分成三层：

- 导演层
- 代码层
- 动作解释层

对应材料现在更准确地分成：

- [../mira-light-booth-scene-table.md](../mira-light-booth-scene-table.md)
- [../mira-light-scene-implementation-index.md](../mira-light-scene-implementation-index.md)
- [./17-control-safety-and-openclaw-rollback-progress.md](./17-control-safety-and-openclaw-rollback-progress.md)

## The Three-Layer Scene Model Is Already Clear

### 1. Director Layer

导演层负责表达：

- 想让观众看到什么
- 主持人口播怎么说
- 依赖条件是什么
- 出错怎么回退

它更像 scene table / booth direction，而不是代码真值。

### 2. Code Layer

代码层主要由 [../../scripts/scenes.py](../../scripts/scenes.py) 承担。

这一层负责：

- 场景 id
- 场景步骤
- 步骤顺序
- 灯光与姿态切换

它是当前真正可执行的 choreography。

### 3. Runtime Safety Layer

当前已经不能再把 scene 看成“脚本直接打设备”。

scene 执行现在还会经过 release runtime 和 bridge 共享的控制安全层，它负责：

- `pose` 校验
- `absolute control` 校验
- `relative nudge` 校验
- `rehearsal_range` clamp
- `hard_range` reject

因此 scene 的真实执行边界，已经不只由 choreography 本身决定，还由安全层共同约束。

## The Runtime Structure Is No Longer Ad Hoc

当前场景系统已经有比较稳定的内部结构：

- `SCENE_META`
- `SCENES`
- 标准步骤类型

`SCENE_META` 负责展示和管理字段，例如：

- `emotionTags`
- `readiness`
- `durationMs`
- `accent`
- `priority`
- `requirements`
- `fallbackHint`
- `operatorCue`

`SCENES` 负责真正执行字段，例如：

- `title`
- `host_line`
- `notes`
- `tuning_notes`
- `steps`

## Step Types Already Standardized

前十个主场景已经主要收敛到这些步骤类型：

- `pose`
- `control`
- `led`
- `delay`
- `comment`
- `action`
- `audio`

这很重要，因为它意味着 scene 已经不只是临时 if/else，而是有自己的动作原语层。

同时也意味着：

- `control` 仍然是统一步骤类型
- 但它现在不再代表“原样下发”
- 运行时会根据安全边界决定 pass / clamp / reject

## The Mechanical Interpretation Has Been Tightened

当前程序层已经统一按四舵机关节来解释机械结构：

- `servo1`：底座转向
- `servo2`：下臂抬升
- `servo3`：前段关节 / 中间关节抬升与前探
- `servo4`：灯头俯仰 / 微表情

这个结论在实现审计中已经明确收口，不再继续沿用早期的“五自由度残留表述”。

## The Ten Core Scenes Are Already in Code

基于 [../mira-light-pdf2-implementation-audit.md](../mira-light-pdf2-implementation-audit.md)
和 scene implementation index，当前十个主场景已经进入代码主干。

其中包括：

- `wake_up`
- `curious_observe`
- `touch_affection`
- `cute_probe`
- `daydream`
- `standup_reminder`
- `track_target`
- `celebrate`
- `farewell`
- `sleep`

其中：

- 大部分主场景已经是明确 choreography
- `track_target` 目前仍是 surrogate choreography，不是真实视觉闭环

## Why This Progress Matters

这部分进展意味着：

- Mira Light 已经有可排练的主场景库
- 代码、导演稿、动作说明开始彼此对齐
- 场景可以被运行时、导演台、OpenClaw、离线演练工具共同引用

这也是后续离线 trace、导演台 cue card、以及 OpenClaw scene-first 策略成立的前提。

## Current Boundary

这里也有几个需要继续保持严谨的边界：

- 动作真值目前仍优先以 PDF2 为准
- `mira-light-booth-scene-table.md` 更偏导演阅读材料，不应直接当代码真值
- `audio` 仍然更多是占位或扩展点，不是完整音频闭环
- `track_target` 还没有成为稳定视觉闭环
- scene 安全边界已经进入软件主干，但这些边界仍需继续用真机校准

## Recommended External Framing

> `Mira-Light` 现在已经拥有一个比较完整的 scene system。它不只是零散动作脚本，
> 而是包含场景元数据、动作原语、导演层 cue、代码 choreography 和逐场景解释文档
> 的多层结构，而且十个主场景已经基本进入代码主干。
