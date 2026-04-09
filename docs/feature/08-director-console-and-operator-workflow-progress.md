# Director Console and Operator Workflow Progress

## Current Status

当前网页控制台已经不再只是工程按钮面板，而是明显朝“展位导演台”方向演进。

这一层的目标不是单纯发命令，而是帮助现场操作员同时看懂：

- 当前状态
- 下一幕能不能触发
- 主持人该说什么
- 出问题时怎么救场

## What Has Already Been Designed and Landed

基于 [../mira-light-director-console-spec.md](../mira-light-director-console-spec.md)，
当前导演台已经明确覆盖了几个核心区域。

### 1. Top Status Strip

顶部状态区现在应该优先回答：

- 当前是 `idle` 还是 `running`
- 当前 scene 是什么
- 当前 step 是什么
- 设备在线还是离线
- 最近错误是什么
- 当前连接目标 base URL 是什么

这部分依赖：

- `web/index.html`
- `web/app.js`
- `scripts/mira_light_runtime.py`

### 2. Cue Cards Instead of Plain Buttons

中部场景区已经不是简单按钮列表，而是 cue cards。

每张卡现在承载：

- 中文标题
- scene id
- readiness
- duration
- emotion tags
- requirements
- host line

这些信息由 `SCENE_META` 提供，因此它和 scene system 本身是对齐的。

### 3. Director Summary

右侧导演摘要区已经被定义成现场视角，而不只是调试视角。

它应该展示：

- 当前场景
- 当前步骤
- 主持人口播建议
- 依赖条件
- fallback 建议

### 4. Operator Quick Actions

当前导演台已经明确要求内置一批“救场型”快捷动作，例如：

- `Apply Neutral`
- `Apply Sleep`
- `Stop Scene`
- `Stop -> Neutral`
- `Stop -> Sleep`
- `Reset Lamp`

这使它更适合真实展位，而不是只适合工程调试。

### 5. Profile and Pose Visualization

Profile 区已经不只是原始 JSON，而是拆成：

- profile 元信息
- servo calibration 摘要
- pose library 摘要
- 可展开的原始 JSON

这让它兼顾导演使用和现场校准。

### 6. Mock Sensor and Pixel Visualization Panel

导演台现在已经不仅能看真灯状态，也开始认真照顾 mock 排练体验。

当前已经落下来的 mock 面板包括：

- `headCapacitive` 摘要卡
- `headCapacitive = 1` mock 开关
- `TOUCH / IDLE / UNKNOWN` 状态 badge
- 更拟物的灯头触摸状态示意
- `40` 灯 `pixelSignals` 图形化总览
- `40` 灯单像素细节卡片

这意味着导演台已经不只是“给工程师发命令”的地方，而开始具备：

- 排练 `touch_affection`
- review LED pattern
- 在没有真灯时训练 operator

的能力。

更细的 feature 说明见：

- [./27-mock-sensors-and-pixels-visualization-progress.md](./27-mock-sensors-and-pixels-visualization-progress.md)

## Additional Safety-Oriented Progress

除了操作结构本身，这一轮还有一层很重要的进展：导演台背后的 bridge/runtime 不再裸露下发控制，而是已经开始带控制安全语义。

相关进展见：

- [./17-control-safety-and-openclaw-rollback-progress.md](./17-control-safety-and-openclaw-rollback-progress.md)

这意味着当前导演台对应的后端链路已经可以区分：

- 正常通过
- 被 clamp
- 被 reject

虽然导演台前端还没有把这些信息做成完整的可视化提示，但它背后的控制结果已经不是黑盒。

## Additional Product-Oriented Progress

当前导演台还新增了几类很像“产品层”而不是“工程层”的字段。

### 1. Accent

场景现在可以带 `accent`，用来表达当前情绪氛围，例如：

- `dawn`
- `curious`
- `warm`
- `vision`
- `celebrate`
- `farewell`
- `sleep`

### 2. Priority and Readiness

每个 cue card 当前建议都有：

- `priority`
- `readiness`

这让现场能一眼判断：

- 这幕是不是主秀
- 这幕是否稳定
- 这幕是否依赖外部传感器

### 3. Dependency Readiness Panel

导演台还新增了依赖就绪区，用来快速确认：

- tracking 是否可用
- 摄像头是否在线
- 音频是否准备好
- 睡姿是否校准
- 麦克风是否可用

这解决的是“能点，但其实没准备好”的现场问题。

## Why This Matters

导演台的这层演进意味着 `Mira-Light` 已经开始具备真正 booth operation 的产品面。

它不再只是给工程师看的控制面，而是开始照顾：

- 现场节奏
- 主持人协作
- 依赖检查
- 故障 fallback

## Current Boundary

当前导演台仍有几项没有完全成熟：

- `deviceOnline` 仍然主要基于轻量状态推断
- `current step` 仍更接近 runtime step，而不是导演语义 step
- `readiness` 仍是手工定义，而不是自动评估
- `safety` clamp / reject 元数据目前主要在 bridge/runtime 层，尚未完整前端化

所以更准确的表述是：

导演台结构已经成形，但还没有完全变成“自动感知型现场总控”。

## Recommended External Framing

> `Mira-Light` 的网页控制台已经从工程面板演进成 booth director console。它现在不仅能触发 scene，
> 还开始承载 cue cards、导演摘要、优先级、readiness、依赖面板和救场动作，使现场操作更像导演编排而不是调试命令。
