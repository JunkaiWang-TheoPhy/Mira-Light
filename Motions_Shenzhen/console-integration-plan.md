# Shenzhen Scene Pack 接入主控台方案

这份文档只讨论一件事：

> 深圳版 scene pack 要怎样接入现有主控台，而不是只停留在文档层。

## 先说结论

不要只新增 `Motions_Shenzhen/` 然后期待主控台自动识别。

现有系统里至少有 4 个地方会卡住：

1. runtime 的导演台主场景集合写死了
2. web 前端的 `DIRECTOR_SCENE_IDS` 写死了
3. `console_server.py` 的 `MOTIONS_ROOT` 默认指向 `Motions/`
4. choreography 真值仍然只来自 `scripts/scenes.py`

所以 Shenzhen pack 的正确接入不是“加目录”，而是“加一个 scene set”。

## 推荐接入方式：scene set

建议新增概念：

- `default`
- `shenzhen`

让主控台、runtime、motion root 都可以切换当前使用的 scene set。

## 服务端应该怎么改

### 1. 让 motions root 可配置

当前：

- `console_server.py` 默认读取 `Motions/`

建议改成：

- `--motions-root`
- 或 `MIRA_LIGHT_MOTIONS_ROOT`

这样才能切到：

- `Motions/`
- `Motions_Shenzhen/`

### 2. 让 `/api/motion-scripts` 带 scene set

当前 `/api/motion-scripts` 只返回一个 motions root 的内容。

建议支持：

- `/api/motion-scripts?sceneSet=default`
- `/api/motion-scripts?sceneSet=shenzhen`

### 3. 让 runtime 支持 Shenzhen pack

当前 scene 真值在：

- `scripts/scenes.py`

建议未来增加：

- `scripts/scenes_shenzhen.py`

然后 runtime 根据 scene set 选择：

- 默认 pack 的 `SCENES`
- Shenzhen pack 的 `SHENZHEN_SCENES`

### 4. 让 `/api/scenes` 不再只看默认主场景

当前 runtime 的导演台主场景集合在代码里写死。

建议变成：

- `DIRECTOR_PRIMARY_SCENES_DEFAULT`
- `DIRECTOR_PRIMARY_SCENES_SHENZHEN`

或直接读配置文件。

## 前端应该怎么改

### 1. 不要再把 `DIRECTOR_SCENE_IDS` 写死成唯一集合

建议新增：

- `sceneSet`
- `sceneSetConfig`

前端根据当前 scene set 决定要渲染哪 10 个按钮。

### 2. 为 Shenzhen 场景增加 context UI

默认 pack 很多场景不怎么吃 context。

但 Shenzhen pack 明显不同。

以下场景建议在主控台加简单的 context 输入：

- `sz_presence_wake`
  - `targetDirection`
  - `wakeReason`
- `sz_cautious_intro`
  - `targetDirection`
  - `targetDistanceBand`
  - `ownerFaceFound`
- `sz_hand_nuzzle`
  - `touchSide`
  - `handDistanceBand`
- `sz_hand_boundary`
  - `approachSide`
  - `approachSpeedBand`
  - `threatLevel`
- `sz_standup_nudge`
  - `responseState`
- `sz_tabletop_follow`
  - `targetId`
  - `lockStrength`
- `sz_sigh_comfort`
  - `transcript`
  - `sighStrength`
- `sz_voice_affect_response`
  - `transcript`
  - `intent`
  - `valence`
- `sz_multi_guest_choice`
  - `primaryDirection`
  - `secondaryDirection`
- `sz_farewell_sleep`
  - `departureDirection`
  - `sleepDelayMs`

### 3. UI 要区分“演示按钮”和“输入上下文”

Shenzhen pack 如果要可信，主控台最好把场景卡片拆成两部分：

- 按钮区
- context 区

不能只保留一个“Run”按钮。

## `Motions_Shenzhen` 将来应该怎么和主控台对接

### 目录层

未来建议是：

```text
Motions_Shenzhen/
  01_presence_wake/scene_script.py
  02_cautious_intro/scene_script.py
  ...
  10_farewell_sleep/scene_script.py
```

### motion script 层

每个 `scene_script.py` 都继续沿用现有规范：

- `SCENE_ID`
- `SCENE_SCRIPT = build_scene_script_info(...)`
- `build_request_body(...)`

### request body 层

每个场景都应把 Shenzhen pack 所需的 context 带进：

- `scene`
- `async`
- `cueMode`
- `context`

### recommended caller path

仍然建议沿用：

- `/api/run-motion-script/<sceneId>`

这样前端无需知道 runtime 细节。

## 实现优先级建议

### P0

- 让 `MOTIONS_ROOT` 可切换
- 让前端支持 `sceneSet`
- 定义 Shenzhen scene ids

### P1

- 新增 `scripts/scenes_shenzhen.py`
- 新增 Shenzhen runtime builder
- 新增 `Motions_Shenzhen/*/scene_script.py`

### P2

- 为 Shenzhen pack 补专用 context UI
- 做 scene set 的持久化
- 为不同 scene set 加不同 showcase 页面

## 不建议的接法

### 不建议 1：直接覆盖默认 `Motions/`

问题：

- 会污染现有 release
- 不利于并行比较 default 与 Shenzhen
- 长期很难维护

### 不建议 2：只加 `scene_script.py` 不加 choreography registry

问题：

- 主控台能看到按钮
- runtime 却没有真正的 scene 真值
- 最终只是“文档化的空按钮”

### 不建议 3：把 Shenzhen pack 硬塞回默认 10 个 `sceneId`

问题：

- 语义冲突
- 旧 UI 和旧测试会误判
- 不利于清楚地区分两个包

## 一句话总结

Shenzhen pack 的正确接入方式不是“新增目录”，而是：

> 新增一套 scene set，让 choreography、runtime、motion manifest、director console 同时认识 Shenzhen 版 10 个交互。
