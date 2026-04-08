# Mira 借鉴 AirJelly / MineContext 的上下文与主动性架构说明

## 文档目的

这份文档用于回答一个具体问题：

> Mira 如果要借鉴 AirJelly 与 MineContext，最应该借鉴什么，应该如何落地，又应该与 OpenClaw 保持什么边界？

这里的目标不是写一份产品评论，而是给工程和产品同学一份 **可落地的架构说明**：

- Mira 应该捕捉什么上下文
- 哪些信息值得长期记忆
- 如何从上下文提炼任务
- 如何实现“主动，但不打扰”
- 哪些工作应由 Mira 做，哪些工作应交给 OpenClaw

## 背景结论

基于 AirJelly 与 MineContext 的公开思路，可以把这条路线概括成一句话：

> MineContext 更像上下文地基，AirJelly 更像主动式产品方向，OpenClaw 更像执行引擎。

对应到 Mira：

- `MineContext` 提供的是 **context capture / timeline / resurfacing** 的方法论
- `AirJelly` 提供的是 **intent-centered proactive assistance** 的产品方向
- `OpenClaw` 提供的是 **tool execution / runtime / agent orchestration**

所以 Mira 最合理的位置不是替代 OpenClaw，而是站在它上游，成为：

```text
context-aware + task-forming + proactive companion layer
```

## 为什么 Mira 值得借鉴这条路线

如果 Mira 只是一个“用户问一句，系统答一句”的聊天框，那它的上限会很像普通 assistant：

- 没有上下文连续性
- 没有任务记忆
- 没有下一步判断
- 没有主动推进能力

而 Mira 想做的并不是更强的单轮问答，而是：

- 在跨 app、跨设备、跨传感器的工作流里看见用户的轨迹
- 在不打扰的前提下理解用户的意图
- 在合适的时机给出下一步建议
- 必要时把意图交给 OpenClaw 去执行

也就是说，Mira 真正应该借鉴的不是“更像 AirJelly 的 UI”，而是下面这条抽象链：

```text
Context
-> Timeline
-> Intent
-> Task
-> Proactive Hint
-> Execution
```

## Mira 最应该借鉴的六件事

## 1. 不要只做聊天框，要做“持续上下文层”

Mira 不应该只在用户开口时才开始理解世界。

它应该持续捕捉和维护这些上下文：

- 用户正在做什么任务
- 最近几分钟 / 几小时做了什么
- 目前在什么 app、窗口、文档里反复切换
- 当前有没有未完成事项
- 有没有明显的情绪和节奏变化
- 当前周围环境或设备状态是否变化

这正是 MineContext 的基础价值：

- 先有连续上下文
- 再谈 agent 主动性

如果没有这层，Mira 只能做“问答助手”；有了这层，它才可能做“陪伴式工作伙伴”。

## 2. 不要全量录一切，要抓“意图锚点”

AirJelly 的一个很重要判断是：

> 不要无差别记录一切，而要优先记录最能暴露意图的关键时刻。

对 Mira 来说，最值得记录的不是“屏幕每一帧是什么”，而是这些高信息密度事件：

- 用户按下 Enter / 发送消息
- 新建文档 / 新建任务
- 打开邮件 / 提交表单
- 复制 / 粘贴 / 搜索
- 切换到某个窗口并长时间停留
- 保存、导出、分享、提交
- 打开某个场景页后又切回代码
- 长时间编辑同一文件后突然停住

换句话说，Mira 最该抓的是：

```text
intent anchors
```

而不是：

```text
dense screen logging
```

这对隐私、算力和可维护性都更健康。

## 3. 不要只存记忆，要把上下文任务化

AirJelly 最值得 Mira 借鉴的一点是：

> 不只是保存 timeline，而是把上下文压缩成可以推进的任务对象。

如果 Mira 只存“你刚刚干了什么”，那它更像日志系统。

如果 Mira 能进一步形成：

- 你当前在推进什么
- 这件事卡在什么地方
- 你接下来最可能要做什么
- 哪些后续同步动作容易漏掉

那它才真正具备主动式价值。

建议 Mira 把上下文整理成如下对象：

```json
{
  "task_id": "task_sync_director_console_showcases",
  "title": "同步 06~10 场景展示页到导演台",
  "status": "active",
  "source_context": [
    "edited web/index.html",
    "added web/06_standup_reminder/index.html",
    "added web/07_track_target/index.html",
    "added web/09_farewell/index.html",
    "added web/10_sleep/index.html"
  ],
  "next_step": "检查导演台主界面能否打开 06~10 场景展示页",
  "confidence": 0.86,
  "updated_at": "2026-04-09T10:00:00+08:00"
}
```

这比单纯保留大量原始上下文更有用。

## 4. 把主动性建立在“时机判断”上

AirJelly 真正值得借鉴的不是“主动”本身，而是：

> 在对的时机主动。

Mira 不应该做成频繁打扰的系统，而应该分层主动：

### A. 只提示，不执行

例如：

- 你刚改了 `scripts/scenes.py`，要不要同步更新对应的 `Figs/motions/*/README.md`？
- 你已经把 `06~10` 场景加进代码，是否需要同步导演台展示？

### B. 先准备，再等确认

例如：

- 自动整理 handoff 文档草稿
- 自动列出可能漏掉的同步文件
- 自动生成 patch 草案

### C. 低风险自动执行

例如：

- 更新索引文档
- 挂接场景说明入口
- 生成中间裁切图
- 刷新状态页

所以 Mira 的“主动”应该是：

```text
提前准备好下一步，而不是擅自行动
```

## 5. 把 Mira 放在 OpenClaw 上层，而不是替代 OpenClaw

这是最重要的边界判断。

Mira 不应该和 OpenClaw 争“谁更会执行工具”。

更合理的职责分工是：

### Mira 负责

- 上下文连续性
- 时间线理解
- 意图判断
- 任务形成
- 主动提示
- 何时提醒、何时克制
- 人格化与陪伴式表达

### OpenClaw 负责

- 工具调用
- 运行时编排
- 代码编辑
- shell 执行
- 系统操作
- 真正的 agent 执行闭环

可以抽象成：

```text
MineContext 风格层
-> Context Capture / Timeline

AirJelly 风格层
-> Intent / Task / Proactive Layer

Mira
-> Companion Judgment / Timing / Persona

OpenClaw
-> Execution Runtime
```

## 6. 坚持 local-first / privacy-aware

MineContext 的另一个很适合 Mira 的点是：

> 尽量本地保存原始上下文，只把提炼后的上下文交给模型。

建议 Mira 默认这样处理：

- 原始窗口标题、本地截图、焦点文件路径、输入事件先本地化
- 先在本地压缩成：
  - 时间线
  - 任务对象
  - 摘要
  - missed follow-ups
- 再把必要信息交给模型

同时必须给用户足够明确的控制：

- 哪些 app 可以被看见
- 哪些 app 永远排除
- 什么会被长期记忆
- 什么只做短期缓存
- 什么时候允许主动

## Mira 的五层落地架构

下面给出一份适合 Mira 的落地版本。

## 第一层：Context Capture

### 目标

采集“高价值、低打扰”的上下文，而不是全量监控。

### 推荐采集对象

- 当前活跃 app
- 当前窗口标题
- 当前文件路径
- 当前网页标题
- 最近打开 / 保存 / 分享的文件
- Enter / 发送 / 提交类事件
- 搜索 / 复制 / 粘贴 / 拖拽
- 日历事件切换
- 设备状态变化
- 可穿戴状态变化
- 家居与外设状态变化

### 不建议直接采集

- 长时全量录屏
- 无差别键盘录制
- 无筛选剪贴板归档

## 第二层：Timeline Memory

### 目标

把离散事件串成有顺序的工作流轨迹。

### 事件对象建议

```json
{
  "ts": "2026-04-09T10:12:00+08:00",
  "kind": "intent_anchor",
  "app": "VS Code",
  "resource": "scripts/scenes.py",
  "event": "edited_scene_definition",
  "hint": "user is refining choreography"
}
```

### 对 Mira 的意义

它让 Mira 不只是知道：

- “你现在打开了什么”

而是知道：

- “你正在推进哪条工作流”
- “你刚刚从哪个上下文切过来”
- “你是不是把某个任务做了一半就跳走了”

## 第三层：Task Capture

### 目标

从 timeline 中提取出真正能推进的任务对象。

### 任务对象建议

```json
{
  "task_id": "task_finish_director_console_scene_showcases",
  "title": "补完导演台 06~10 场景展示页",
  "status": "active",
  "source_context": [
    "added 06_standup_reminder page",
    "added 07_track_target page",
    "updated main director console links"
  ],
  "next_step": "补 08/09/10 的展示页或检查现有入口",
  "confidence": 0.84,
  "updated_at": "2026-04-09T10:15:00+08:00"
}
```

### 对 Mira 的意义

任务对象是 Mira 主动性的前提。  
没有任务对象，就很难判断：

- 什么时候提醒
- 提醒什么
- 哪些是被遗忘的后续动作

## 第四层：Proactive Layer

### 目标

基于 context + task + timing 生成“合适的主动行为”。

### Mira 可执行的主动行为

- 提醒遗漏同步项
- 识别被打断的任务
- 生成下一步建议
- 预生成 brief / patch 草稿
- 在低风险场景自动更新索引

### 当前项目里的典型例子

- 刚补完 `scripts/scenes.py` 的 `06~10`，Mira 应该提醒：
  - 是否同步 `Figs/motions/06~10/README.md`
  - 是否同步导演台场景展示页
  - 是否同步 handoff 文档

- 刚生成了 `web/06~10` 页面，Mira 应该提醒：
  - 是否在导演台主界面挂展示页入口
  - 是否检查 `/scene-folder/` 的静态服务兼容性

### 主动策略建议

建议把 Mira 的主动性分成三档：

- `hint-only`
- `prepare-and-wait`
- `auto-do-low-risk`

## 第五层：Execution Layer

### 目标

把真正执行留给 OpenClaw 或其它 runtime。

### Mira 与 OpenClaw 的边界

Mira 输出：

```json
{
  "intent": "sync_scene_docs",
  "targets": [
    "docs/mira-light-scene-implementation-index.md",
    "docs/mira-light-pdf2-implementation-audit.md"
  ],
  "reason": "scene implementation changed",
  "risk": "low"
}
```

OpenClaw 负责：

- 编辑文件
- 运行检查
- 执行命令
- 调工具

这就避免 Mira 自己既做上下文判断，又做底层执行，导致职责混乱。

## 结合 Mira-Light 这个项目，Mira 可以具体借鉴什么

## 1. 对开发流的上下文理解

Mira 可以持续理解：

- 当前在改 `scripts/scenes.py`
- 当前在补哪个场景
- 当前是否正在同步 `Figs/motions/*`
- 当前是否在改导演台
- 当前是否已经进入“交付给另一台电脑”的阶段

## 2. 对场景实现状态的任务化

比如把当前项目状态压缩成：

- `前十个主场景已进代码`
- `track_target 仍是 surrogate`
- `farewell 仍缺动态离场方向`
- `导演台 06~10 已有展示入口`

## 3. 对“下一步”的主动判断

例如：

- 你现在最该做的是 `track_target` 的真实视觉闭环
- 或者先做真机校准
- 或者先同步导演台和 handoff 文档

## Mira 不应该直接照搬的地方

### 1. 不要做成监控感太强的系统

上下文系统一旦过量，就会从 companion 变成 surveillance。

### 2. 不要把主动性做成频繁打断

Mira 应该在高价值时刻轻轻出现，而不是像提醒软件一样不停弹窗。

### 3. 不要把记忆做成垃圾堆

真正有价值的不是原始海量日志，而是：

- timeline
- task object
- next step
- blocker
- confidence

## 推荐给 Mira 的实施顺序

### Phase 1

先做 `MineContext` 式轻量上下文层：

- 活跃 app
- 窗口标题
- 文件路径
- Enter / 保存 / 搜索 / 复制 等关键意图锚点

### Phase 2

再做 `AirJelly` 式任务化层：

- timeline
- task capture
- next step prediction
- missed follow-up detection

### Phase 3

最后和 OpenClaw 深度耦合：

- 把任务对象交给 execution runtime
- 把主动提醒和真实执行分层

## 一句话结论

Mira 最值得借鉴 AirJelly / MineContext 的，不是某个界面或某个 slogan，而是：

> 先构建连续上下文，再提炼任务，再做温和主动，最后把执行交给 OpenClaw。

如果继续落地，Mira 最合理的定位是：

```text
context-aware + task-forming + proactive companion layer
```
