# `sz_tabletop_follow` 规格书

## 核心规格

- `sceneId`: `sz_tabletop_follow`
- `demo_goal`: 证明 Mira 真的能看见并连续跟随桌面目标，而不是只运行一段预录 choreography。
- `scene_mode`: `hybrid`
- `apiContextKeys`: `targetId`, `targetClass`, `horizontalZone`, `distanceBand`, `lockStrength`
- `fallback_behavior`: 当视觉闭环不可用时，退化成“说明性跟随 choreography”，明确告诉评委这是 fallback 演示，不把它包装成真跟随。
- `operator_cue`: “你可以试着在桌上移动这本书，它会一直看着书走，停下来的时候也会停住。”
- `success_signal`: 目标移动时，灯头连续跟随；目标停下时，灯也停下；出现干扰物时，不会马上乱切。

## 这个场景为什么是深圳主包中的 P0

这是最直接的“感知可信度”证明之一。

只要这一幕稳定，评委就会立刻把 Mira 从“会演动作的灯”升级理解为：

> 它真的看见了桌上的东西。

## 为什么它必须是 `hybrid`

因为它天然有两层：

1. 进入和退出需要固定 choreography
2. 中间核心必须由实时 tracking 驱动

如果全做成静态 scene，它就失去了真正价值。
如果全做成实时控制，又很难给导演台一个稳定可解释的入口。

## 推荐运行逻辑

### 进入段

1. 从 `neutral` 或当前工作位切入
2. 灯光切到功能性聚焦白光
3. runtime 标记 tracking active

### 实时段

1. 接收 `targetId`
2. 读取 `horizontalZone`、`distanceBand`
3. 根据 `lockStrength` 决定是否继续保持当前目标
4. 更新 servo 和光照焦点

### 退出段

1. 目标丢失或手动 stop
2. 平滑回到 `neutral`
3. 恢复普通照明

## 推荐 context 约定

- `targetId`
  - 当前锁定目标的稳定 ID
- `targetClass`
  - `book | object | hand | unknown`
- `horizontalZone`
  - `left | center | right`
- `distanceBand`
  - `near | mid | far`
- `lockStrength`
  - `0.0 ~ 1.0`

## 主控台接入建议

### 按钮文案

- 中文：`桌面追踪`
- 英文辅助：`Tabletop Follow`

### 建议输入控件

- target id
- 目标类别
- 当前方向
- 距离带
- 锁定强度

### 建议 step outline

- Enter tracking posture
- Lock on the tabletop target
- Follow continuously
- Hold when the target stops
- Recover to neutral

## fallback 的表达方式必须诚实

如果视觉栈没工作，不要假装这是真 tracking。

Shenzhen 版应该明确区分：

- `live follow`
- `fallback choreography`

否则一旦评委故意测试，它会立刻掉可信度。

## 失败信号

- 灯头一步一跳
- 目标停下时马上丢失
- 第二个矩形物体出现就频繁切换
- 导演台看不出当前锁定的是谁

## 落地建议

这是 Shenzhen pack 的头号技术难点，也是头号说服力来源。

如果必须给 10 个场景排优先级，它一定在第一梯队。
