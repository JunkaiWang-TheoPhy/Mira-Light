# Mira Light: AI That Sees You

`#RedHackathon` `#小红书黑客松巅峰赛`

Mira Light 是一个具身化 AI 交互项目。它把「看见你、理解你、回应你」从屏幕里的聊天框，带到真实空间中的一盏四自由度智能灯上。

## 一句话介绍

Mira Light 让 AI 不再只是等你输入，而是能够主动注意到你的出现、跟随你的移动、理解互动语境，并通过灯光、动作和节奏表达关心。

## 项目定位

这是一个完整、独立、可直接演示的 AI 硬件交互项目，面向小红书黑客松巅峰赛 2026 的现场 Expo 与 Demo Day 场景。

它不是一个单点功能 demo，而是一条已经跑通的端到端链路：

```text
摄像头输入
-> 视觉事件提取
-> 行为/场景决策
-> 台灯动作与灯光表达
-> 可选的上下文与记忆回写
```

## Demo 核心体验

Mira Light 在现场希望传达一种很直观的感受：

- 你走近，它会醒来
- 你停下，它会好奇地看向你
- 你移动，它会跟着你
- 你互动，它会表现出亲近、开心或关心
- 你离开，它会目送你并慢慢回到休息状态

所以它表达的不是「一个会动的灯」，而是「一个在空间里真的注意到你存在的 AI」。

## 为什么这个项目重要

今天大多数 AI 产品仍然停留在：

- 等你开口
- 等你输入
- 在屏幕里回答你

Mira Light 想推进的是另一种方向：

- AI 可以在物理空间里具备存在感
- AI 可以通过感知与动作建立陪伴感
- AI 的回应可以不只是文字和语音，也可以是姿态、方向、节奏和光线

这让它天然适合桌面陪伴、家庭环境、儿童互动、老人关怀、零售展陈、工作提醒等场景。

## 当前已经实现的能力

- 接收实时 JPEG 图像流并本地预览
- 基于单摄像头提取结构化视觉事件
- 判断目标是否出现、位于左中右、是在靠近还是远离
- 将视觉信号映射为高层 scene，而不是直接粗暴控制舵机
- 通过四自由度 ESP32 灯体执行场景动作
- 通过本地 bridge 暴露稳定控制接口
- 支持导演台、本地 dry-run、离线 rehearsal、mock device 和测试验证

## 代表性场景

当前仓库覆盖的代表场景包括：

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

更完整的展位场景说明见：

- [`Mira_Light_Released_Version/docs/mira-light-booth-scene-table.md`](./Mira_Light_Released_Version/docs/mira-light-booth-scene-table.md)
- [`Mira_Light_Released_Version/docs/release-scene-bundles.md`](./Mira_Light_Released_Version/docs/release-scene-bundles.md)

## 为什么适合黑客松现场评审

按照 `小红书黑客松巅峰赛2026` 的评审关注点，这个项目有几个天然优势。

### 创新性

- 把 AI 从屏幕交互推进到具身交互
- 将感知、决策、动作、情绪表达串成同一个产品闭环
- 用最直观的物理反馈，把 “AI That Sees You” 做成现场可感知的体验

### 现场讲述效果

- 观众几秒内就能看懂：它看见你了，它在回应你
- 物理动作比纯软件界面更容易形成记忆点
- 叙事路径清楚：看见 -> 理解 -> 回应 -> 送别

### 完成度

- 仓库内已有视觉接收、事件提取、runtime、bridge、console、测试和演示脚本
- 支持真机、mock、dry-run 和离线验证
- 已形成稳定的 scene bundle 与 booth 演示路径

### 商业潜力

- 可延展到陪伴式桌面硬件
- 可延展到家庭照护与儿童互动
- 可延展到展厅、零售、门店、办公环境中的主动式环境智能

### 技术难度

- 四自由度硬件编排与安全控制
- 单摄像头视觉事件抽取与行为映射
- 本地桥接层与远程控制接口设计
- 记忆 / context integration 的扩展接口

## 系统结构

### 运行时与行为层

- [`scripts/mira_light_runtime.py`](./scripts/mira_light_runtime.py)
- [`scripts/scenes.py`](./scripts/scenes.py)
- [`scripts/vision_runtime_bridge.py`](./scripts/vision_runtime_bridge.py)

这部分负责 scene、pose、动作编排、视觉事件消费，以及安全控制。

### 视觉输入层

- [`docs/cam_receiver_new.py`](./docs/cam_receiver_new.py)
- [`scripts/track_target_event_extractor.py`](./scripts/track_target_event_extractor.py)
- [`config/mira_light_vision_event.schema.json`](./config/mira_light_vision_event.schema.json)

这部分负责把图像流变成结构化事件，而不是直接把识别结果硬连到底层舵机控制。

### 设备桥接层

- [`tools/mira_light_bridge/README.md`](./tools/mira_light_bridge/README.md)
- [`tools/mira_light_bridge/bridge_server.py`](./tools/mira_light_bridge/bridge_server.py)
- [`scripts/simple_lamp_receiver.py`](./scripts/simple_lamp_receiver.py)

这部分负责本地稳定 API、设备接入、OpenClaw 集成，以及后续的远程调用路径。

### 可直接运行的稳定目录

- [`Mira_Light_Released_Version/README.md`](./Mira_Light_Released_Version/README.md)

这里提供一套更偏交付和演示的独立运行入口，适合快速起完整本地栈。

## 快速开始

### 1. 初始化本地环境

```bash
bash scripts/setup_cam_receiver_env.sh
```

### 2. 启动图像接收端

```bash
bash scripts/run_cam_receiver.sh --host 0.0.0.0 --port 8000 --save-dir ./captures
```

### 3. 运行 live-follow demo

```bash
bash scripts/run_mira_light_live_follow_demo.sh --mock-device --replay-demo --receiver-port 18000
```

### 4. 运行离线演练

```bash
bash scripts/run_mira_light_offline_rehearsal.sh --mode quick
```

### 5. 启动完整本地栈

```bash
cd Mira_Light_Released_Version
bash scripts/one_click_install.sh
bash scripts/start_local_stack.sh
```

## 仓库结构

```text
.
├── docs/                              设计说明、接收端、赛事材料与运行文档
├── scripts/                           runtime、vision、scene、演练与控制脚本
├── tools/mira_light_bridge/           bridge 与 OpenClaw 集成层
├── web/                               本地导演台与场景演示页面
├── config/                            配置与事件 schema
├── tests/                             测试与验证
├── Figs/                              动作参考与视觉素材
└── Mira_Light_Released_Version/       可直接运行的稳定目录
```

## 我们在做什么

我们在做具身化 AI，让感知、情绪和动作在真实空间里形成闭环。

这句话对我们来说，不只是一个抽象的方向描述，而是整个项目真正想推进的交互范式。我们想把 AI 从屏幕里的输入框和语音助手，推进到真实空间中的可感知存在：它能够注意到你的出现，理解你正在靠近、停留、移动还是互动，并把这种理解转化成有节奏、有姿态、有温度的回应。

在 Mira Light 里，感知不是孤立的识别模块，情绪也不是一层附着在结果外面的包装，动作更不是机械执行的终点。我们希望这三者在同一个系统里自然联动：看见你，产生判断；理解语境，形成状态；再通过方向、姿态、灯光、节奏和场景编排，把这种状态表达回空间。这种从观察到理解、再到表达的连续过程，才是我们想做的具身化 AI 闭环。

我们相信，下一代 AI 体验不应该只停留在“你问，它答”，而应该能够在物理环境中建立存在感、注意力和陪伴感。Mira Light 想验证的正是这种可能性：AI 不只是一个回答问题的接口，而是一个能在真实空间里感知你、回应你、和你共处的交互主体。

## 延伸阅读

- [`docs/feature/README.md`](./docs/feature/README.md)
- [`docs/mira-context-proactivity-architecture.md`](./docs/mira-context-proactivity-architecture.md)
- [`docs/mira-light-embodied-memory-integration-2026-04-09.md`](./docs/mira-light-embodied-memory-integration-2026-04-09.md)
- [`docs/mira-light-to-mira-v3-layered-memory-integration-plan.md`](./docs/mira-light-to-mira-v3-layered-memory-integration-plan.md)

如果你是评委、协作者或技术同学，最快的阅读路径是：

1. 先看上面的“一句话介绍”和“Demo 核心体验”
2. 再看“为什么适合黑客松现场评审”
3. 最后直接跑 quick start 或进入 [`Mira_Light_Released_Version/README.md`](./Mira_Light_Released_Version/README.md)
