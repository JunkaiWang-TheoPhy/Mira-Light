# Mira Light 单摄像头 + 四自由度视觉开发详细说明

## 文档目的

这份文档专门回答一个工程问题：

> 在当前仓库已经有的 `docs/`、接收端、runtime、scene 定义和导演台基础上，如何把“单摄像头视觉”真正接到“四自由度灯具控制”和“大模型高层解读”里？

这里不再重复抽象概念，而是把当前仓库已经有的内容串成一条能继续开发的落地路线。

本文适合这些读者：

- 继续接手本仓库开发的工程同学
- 负责视觉算法或视觉接入的同学
- 负责 runtime / scene 编排的同学
- 负责本地大模型、OpenClaw 或云端接入的同学

## 先说结论

当前最合理的系统结构不是：

```text
单摄像头
-> 直接控制 servo1~servo4
```

而是：

```text
单摄像头图像流
-> 本地图像接收端
-> 视觉事件提取器
-> 结构化 vision event JSON
-> runtime / scene selection
-> 动作原语 / pose / scene choreography
-> ESP32 REST API
-> 四自由度灯具动作
```

如果后面要接大模型，则放在视觉事件提取器之后：

```text
vision event
-> 大模型高层解释 / scene hint
-> runtime
```

而不是让大模型或视觉识别代码直接输出底层舵机指令。

## 当前仓库里，哪些文档和文件是这条链路的真值

## 第一层：硬件与设备控制真值

### 1. [`ESP32 智能台灯.pdf`](../docs/ESP32%20智能台灯.pdf)

它定义的是硬件能力边界和设备原始 API：

- `GET /status`
- `POST /control`
- `POST /reset`
- `GET /led`
- `POST /led`
- `GET /actions`
- `POST /action`
- `POST /action/stop`

### 2. [`docs/esp32-smart-lamp-delivery-spec.md`](../docs/esp32-smart-lamp-delivery-spec.md)

这是 PDF 的工程翻译版，适合作为“设备控制真值表”。

## 第二层：场景与动作真值

### 1. [`docs/Mira Light 展位交互方案2.pdf`](../docs/Mira%20Light%20展位交互方案2.pdf)

当前动作真值以这份方案 2 为准。

### 2. [`docs/mira-light-pdf2-engineering-handoff.md`](../docs/mira-light-pdf2-engineering-handoff.md)

说明：

- 当前真值文件优先级
- 程序层如何解释 4 个舵机
- 当前哪些场景已较完整落地

### 3. [`docs/mira-light-pdf2-implementation-audit.md`](../docs/mira-light-pdf2-implementation-audit.md)

说明：

- 当前实现状态
- 剩余缺口
- 目前最大的工程缺口是 `track_target` 的真实视觉闭环

## 第三层：自然语言到工程对象的翻译真值

### 1. [`docs/mira-light-scene-to-code-spec.md`](../docs/mira-light-scene-to-code-spec.md)

它不是当前动作唯一真值，但它仍然是最关键的“翻译方法说明”。

它强调：

```text
自然语言描述
-> 交互意图
-> 系统事件
-> 场景状态
-> 动作原语
-> 设备 API
```

这条链路正是视觉接入时必须遵守的原则。

### 2. [`docs/mira-light-booth-scene-table.md`](../docs/mira-light-booth-scene-table.md)

它把场景整理成：

- 触发条件
- 情绪目标
- 动作序列
- 灯光设计
- 主持人口播
- 失败回退

这非常适合后面把视觉事件映射到具体 scene。

## 第四层：当前图像流 / 模型接入现状

### 1. [`docs/mira-light-vision-stream-and-gemini-summary.md`](../docs/mira-light-vision-stream-and-gemini-summary.md)

这份文档已经明确：

- 当前图像流接收已经打通
- 图像流接收不等于视觉理解
- 当前 Gemini 单帧调用时延大约在 `1.6s ~ 2.3s`
- `flash live` 需要单独走 `bidiGenerateContent`

### 2. [`docs/mira-light-vision-event-schema.md`](../docs/mira-light-vision-event-schema.md)

这份文档解释了：

- 单摄像头如何做二维定位
- 如何做“伪三维”距离感
- 如何把视觉输出映射到四自由度

## 当前代码中，这条链路对应哪些文件

### 图像输入层

- [`docs/cam_receiver_new.py`](../docs/cam_receiver_new.py)
- [`scripts/run_cam_receiver.sh`](../scripts/run_cam_receiver.sh)
- [`scripts/setup_cam_receiver_env.sh`](../scripts/setup_cam_receiver_env.sh)

当前职责：

- 接收 JPEG 帧
- 实时预览
- 可选落盘
- 暴露 `GET /health`

### 视觉事件层

- [`config/mira_light_vision_event.schema.json`](../config/mira_light_vision_event.schema.json)
- [`scripts/track_target_event_extractor.py`](../scripts/track_target_event_extractor.py)

当前职责：

- 从 `captures/` 里读取最新 JPEG
- 提取最基础的目标事件
- 输出标准 vision event JSON

### 场景与运行时层

- [`scripts/scenes.py`](../scripts/scenes.py)
- [`scripts/mira_light_runtime.py`](../scripts/mira_light_runtime.py)
- [`scripts/booth_controller.py`](../scripts/booth_controller.py)

当前职责：

- 管理 pose / calibration / scene meta
- 运行 scene
- 调用 ESP32 REST API

### 本地导演台层

- [`scripts/console_server.py`](../scripts/console_server.py)
- [`web/index.html`](../web/index.html)
- [`web/app.js`](../web/app.js)
- [`docs/mira-light-director-console-spec.md`](../docs/mira-light-director-console-spec.md)

当前职责：

- 现场控制
- 状态观察
- Cue 卡片触发
- 故障回退

## 为什么单摄像头仍然足够做当前版本

单摄像头当然做不了真正完整三维重建，但对当前展位系统来说，它已经足够支持第一阶段的闭环。

你们真正需要的不是：

- 毫米级深度
- 机械臂级空间控制
- 多目标长期身份保持

而是：

- 目标有没有出现
- 在左 / 中 / 右哪里
- 在上 / 中 / 下哪里
- 比上一帧更近还是更远
- 是否持续存在

这就足够驱动四自由度灯具去表达：

- 看向目标
- 跟随目标
- 前探
- 回缩
- 低头
- 歪头
- 发呆
- 进入睡眠

## 单摄像头的“二维 / 三维”在本项目里分别是什么意思

### 二维能力

二维能力是：

- 框位置
- 中心位置
- 左中右分区
- 上中下分区

这些能力主要解决：

- `servo1` 应该往哪边看
- `servo4` 应该稍微看高一点还是低一点

### “伪三维”能力

这里说的三维不是严格几何深度，而是单目尺度启发式距离感。

它来自：

- 目标框面积
- 目标面积变化趋势

因此它能输出：

- `near`
- `mid`
- `far`

以及：

- `approaching`
- `receding`
- `stable`

这类信息主要服务于：

- `servo2` 的抬升意图
- `servo3` 的前探 / 回缩意图
- scene 的选择

### 为什么这已经够用

当前灯具的动作重点不是“精确操作物体”，而是“表达对目标的注意与情绪”。

所以只要知道：

- 有人来了
- 人偏左
- 人更近了

就已经足够驱动：

- `wake_up`
- `curious_observe`
- `track_target`

## 四自由度应如何映射视觉信息

根据最新文档约定：

- `servo1`：底座转向
- `servo2`：下臂抬升
- `servo3`：前段关节 / 中间关节抬升与前探
- `servo4`：灯头俯仰 / 微表情

### `servo1`

主要响应：

- `horizontal_zone`
- `center_norm.x`
- `yaw_error_norm`

作用：

- 左右看向目标
- 跟随目标左右移动

### `servo2`

主要响应：

- `distance_band`
- `vertical_zone`
- `lift_intent`

作用：

- 抬起 / 俯下整体姿态
- 形成“警觉”“靠近”“缩回”的大体身态

### `servo3`

主要响应：

- `distance_band`
- `approach_state`
- `reach_intent`

作用：

- 前探
- 回缩
- 更靠近人或目标

### `servo4`

主要响应：

- `center_norm.y`
- `pitch_error_norm`

作用：

- 灯头抬起 / 压低
- 轻微表情
- 辅助“害羞”“疑惑”“专注”感

## 大模型在这套系统里应该放哪一层

最重要的一点是：

**大模型不是高频 tracking 层。**

高频 tracking 应该由本地 CV 处理：

- 每秒 `10 FPS / 5 FPS`
- 位置
- 运动
- 存在性

大模型更适合做：

- 高层场景解释
- 模糊意图判断
- 语义描述
- 给出 `scene_hint`

所以更合理的结构是：

```text
10 FPS / 5 FPS 本地帧流
-> 本地视觉事件提取
-> 每秒抽 1 帧给大模型
-> 大模型输出高层 JSON 提示
-> runtime 结合本地事件决定 scene
```

### 为什么不让大模型直接输出舵机角度

因为那会造成：

- 不稳定
- 难复现
- 难调参
- 不利于安全边界

正确做法是：

```text
大模型输出 scene_hint / interaction_hint
runtime 再翻译成具体动作
```

## 现在应该优先做什么，而不是做什么

### 优先做的

#### 1. 把 `captures/` 当成真实视觉样本库

当前应该固定接收器运行方式：

```bash
cd Mira_Light_Released_Version
bash scripts/run_cam_receiver.sh --host 0.0.0.0 --port 8000 --save-dir ./captures --log-level INFO
```

这样你们后续每次做视觉开发，都有真实样本可回放。

#### 2. 跑通事件提取器

当前最直接的命令是：

```bash
./.venv/bin/python scripts/track_target_event_extractor.py \
  --captures-dir ./captures \
  --latest-event-out ./runtime/vision.latest.json \
  --events-jsonl ./runtime/vision.events.jsonl
```

这一步的目标是：

- 不再只是“看到图”
- 而是能稳定产出 vision event

#### 3. 先做 `track_target` 闭环

当前 handoff / audit 文档已经明确：

- `track_target` 还是 surrogate choreography

所以当前最大的工程价值不是继续堆接收器，而是：

```text
把视觉事件真正接到 track_target 场景
```

#### 4. 大模型先只做高层 JSON 输出

第一版不建议让大模型输出长文本说明。  
建议让它输出类似：

```json
{
  "scene_hint": "curious_observe",
  "target": "person",
  "interaction_intent": "observing",
  "confidence": 0.84,
  "reason": "目标稳定停留在设备正前方"
}
```

### 当前不建议优先做的

- 不要先做复杂多目标身份跟踪
- 不要先做语音理解
- 不要先让大模型直接控硬件
- 不要先接云端 OpenClaw
- 不要先重构 runtime 大架构

## 具体开发分期建议

## Phase 1：把视觉输入做成可复用事件

目标：

- `cam_receiver_new.py` 收图稳定
- `track_target_event_extractor.py` 输出稳定 JSON

验收标准：

- 能持续得到 `vision.latest.json`
- 同一目标移动时，`horizontal_zone / distance_band / scene_hint` 变化合理

## Phase 2：把事件接进本地 runtime

目标：

- 不再只人工触发 `track_target`
- 让视觉事件触发基本场景切换

推荐方式：

- 新增一个很薄的 `vision_runtime_bridge.py`
- 它读取 `vision.latest.json`
- 只把事件映射成：
  - `wake_up`
  - `curious_observe`
  - `track_target`
  - `sleep`

## Phase 3：把大模型加进高层解释层

目标：

- 让大模型补充高层语义，不替代本地 tracking

输入：

- 每秒抽 1 帧
- 当前 vision event
- 当前 runtime state

输出：

- `scene_hint`
- `interaction_intent`
- `reason`

## Phase 4：再接导演台与 OpenClaw

目标：

- 导演台能看到 vision state
- OpenClaw / Claw 能在高层做编排

但这一步必须晚于前面三步。

## 仓库里下一步最值得新增的代码文件

### 1. `scripts/vision_runtime_bridge.py`

作用：

- 读 `vision.latest.json`
- 调 `booth_controller.py` 或 `MiraLightRuntime`
- 做最小场景映射

### 2. `scripts/gemini_flash_live_probe.py` 或同类脚本

作用：

- 每秒读一张最新图
- 发给 Gemini Live / Flash
- 输出结构化高层语义 JSON

### 3. 导演台状态接入

把 vision state 暴露给：

- [`scripts/console_server.py`](../scripts/console_server.py)
- [`web/app.js`](../web/app.js)

让现场操作员能看到：

- 当前有没有目标
- 目标在左中右哪里
- 当前 scene_hint 是什么

## 最短落地路径

如果只说一句最实用的话：

```text
先把图像接收器固定落盘
-> 再把单摄像头事件提取器稳定输出
-> 再把事件接到 track_target
-> 最后才加大模型和 Claw
```

## 一句话总结

当前仓库已经具备：

- 图像流入口
- scene 定义
- runtime
- 导演台
- 视觉事件 schema
- 第一版事件提取器

真正还没闭环的，是：

```text
单摄像头事件
-> runtime
-> track_target / wake_up / sleep
```

所以现在要做的不是再想新架构，而是把这条已经铺好的仓库内链路，真正落成代码与自动触发。
