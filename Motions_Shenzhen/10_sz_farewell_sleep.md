# `sz_farewell_sleep` 规格书

## 核心规格

- `sceneId`: `sz_farewell_sleep`
- `demo_goal`: 证明 Mira 能完成一段完整的社交收尾：先目送离开的人，再慢慢收回自己，回到休息状态。
- `scene_mode`: `chain_scene`
- `apiContextKeys`: `departureDirection`, `lingerMs`, `sleepDelayMs`, `guestId`
- `fallback_behavior`: 如果没有离场方向检测，就由导演台指定一个离场方向，运行“目送 -> 点头告别 -> 低头 -> 入睡”固定版。
- `operator_cue`: “当你离开的时候，它不会突然结束，而会先目送你，再慢慢回到休息状态。”
- `success_signal`: 评委能清楚看懂这是一个有情绪的结束动作：先看着你离开，再依依不舍地低下来，最后睡去。

## 为什么深圳版要把 `farewell` 和 `sleep` 合并

默认主包里：

- `farewell`
- `sleep`

是两个一级按钮。

但深圳版更强调完整社交闭环，所以更合理的设计是：

> 一个按钮完成“送别到入睡”的完整链路。

这样既更自然，也能把一级按钮位让给更有感知证明价值的 scene。

## 推荐运行逻辑

### 第 1 段：目送

1. 根据 `departureDirection` 朝离场方向看过去
2. 保持一小段停顿
3. 如果有 `guestId`，runtime 可记录它正在送别谁

### 第 2 段：告别

1. 做 1 到 2 次慢速点头式挥手
2. 轻轻低头

### 第 3 段：收回

1. 保持 `lingerMs`
2. 再转入收臂与低头
3. 按 `sleepDelayMs` 进入 sleep choreography

## 推荐 context 约定

- `departureDirection`
  - `left | center | right`
- `lingerMs`
  - 目送后保持在告别姿态多久
- `sleepDelayMs`
  - 从告别结束到进入 sleep 的延迟
- `guestId`
  - 可选，用于运行时记录

## 主控台接入建议

### 按钮文案

- 中文：`送别并入睡`
- 英文辅助：`Farewell Sleep`

### 建议输入控件

- 离场方向
- 目送停留时间
- 入睡延迟

### 建议 step outline

- Look toward the departure side
- Hold the goodbye gaze
- Nod softly like a wave
- Lower the head with reluctance
- Fold back into sleep

## 为什么它是 `chain_scene`

因为这里不是两个不相干的场景。

对观众来说，真正自然的体验是：

- 你走了
- 它先送你
- 然后才安静下来

如果拆成两个独立按钮，现场会更像“导演在切 cue”，而不是一个完整生命体的收尾。

## 失败信号

- 一离场就立刻睡下，没有目送过程
- 挥手太快，像故障抽动
- 看向离场方向的朝向不对
- `farewell` 和 `sleep` 之间没有情绪过渡

## 落地建议

这应该是 Shenzhen pack 的最后一个主按钮。

它决定评委离开展位时，对 Mira 留下的是“突然停掉”的印象，还是“它真的在送我走”的印象。
