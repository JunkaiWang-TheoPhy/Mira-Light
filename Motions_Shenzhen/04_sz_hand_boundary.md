# `sz_hand_boundary` 规格书

## 核心规格

- `sceneId`: `sz_hand_boundary`
- `demo_goal`: 证明 Mira 有边界感；当手突然逼近时，它会礼貌地后缩和回看，而不是无条件继续亲近。
- `scene_mode`: `dynamic_builder`
- `apiContextKeys`: `approachSide`, `approachSpeedBand`, `threatLevel`, `recoveryAllowed`
- `fallback_behavior`: 若没有真实手部输入，则由导演台指定来手方向和威胁级别，运行一版低风险后缩 choreography。
- `operator_cue`: “它不是谁碰都一股脑往前凑，如果你突然逼近，它会先给自己留一点空间。”
- `success_signal`: 评委能清楚看出“后缩 -> 偏头回看 -> 停半拍 -> 慢慢恢复”这四段，而不是惊慌乱躲。

## 这个场景为什么重要

没有边界感的拟生命体，会显得不真实。

Shenzhen 文档里非常重要的一条价值是：

> 它不是永远讨好人的对象，它会保护自己的空间。

`sz_hand_boundary` 的作用就是把这件事明确展示出来。

## 推荐运行逻辑

### 主路径

1. 检测到快速来手或高威胁手势
2. 根据 `approachSide` 生成退让方向
3. 先快速后缩
4. 再朝安全方向偏头回看
5. 停半拍确认
6. 若 `recoveryAllowed=true`，再慢慢恢复

### 分级策略

- `threatLevel=low`
  - 轻后缩、轻偏头
- `threatLevel=medium`
  - 明显后缩、停顿更久
- `threatLevel=high`
  - 立即退出亲近状态，不做再次前探

## 推荐 context 约定

- `approachSide`
  - `left | center | right`
- `approachSpeedBand`
  - `slow | medium | fast`
- `threatLevel`
  - `low | medium | high`
- `recoveryAllowed`
  - `true | false`

## 主控台接入建议

### 按钮文案

- 中文：`手太近了`
- 英文辅助：`Hand Boundary`

### 建议输入控件

- 逼近方向
- 逼近速度
- 威胁级别
- 是否允许恢复

### 建议 step outline

- Retreat from the hand
- Turn away for safety
- Peek back once
- Pause to reassess
- Recover only if safe

## 为什么它必须和 `sz_hand_nuzzle` 分开

因为这两幕要证明的是相反的东西：

- `nuzzle` 证明亲近
- `boundary` 证明边界

如果把它们混成一个 scene，很难在导演台上解释，也很难在现场稳定触发。

## 失败信号

- 动作像受惊抽搐，而不是礼貌退让
- 无论什么来手速度都同一个反应
- 本该躲开时仍然继续前探
- 恢复太快，观众还没看懂它在“保护自己”

## 落地建议

深圳版如果要和普通“会动的灯”拉开差距，这个场景很关键。

它把 Mira 从“永远配合的人形外设”提升成“有边界的生命体”。
