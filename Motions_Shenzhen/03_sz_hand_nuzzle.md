# `sz_hand_nuzzle` 规格书

## 核心规格

- `sceneId`: `sz_hand_nuzzle`
- `demo_goal`: 证明 Mira 会主动亲近人的手，并把“触摸”理解成一种值得靠近的互动。
- `scene_mode`: `dynamic_builder`
- `apiContextKeys`: `touchSide`, `handDistanceBand`, `handSpeedBand`, `touchDetected`
- `fallback_behavior`: 如果没有可靠手部输入，则由导演台手动指定左右方向，运行一版低风险的固定靠近与轻蹭 choreography。
- `operator_cue`: “你可以摸摸它，它不会只是被动接受，而会主动靠过来蹭你一下。”
- `success_signal`: 评委能看到它朝正确侧靠近、进入手掌下方、做小幅蹭动，并在手离开后轻追一下。

## 当前端侧种子

这个场景目前仍然是弱种子。

板端可借的只有：

- `servo_1_2_lean_forward_2148_1848.py`
- 灯头暖光与呼吸灯命令

还没有直接可复用的“蹭手 / rub / 追手一下”脚本，所以它仍然属于高优先级补写项。

## 这个场景要证明什么

它要证明的不是“触摸传感器通了”，而是：

> Mira 把人的手理解成可以靠近的社交对象。

这是深圳现场里最容易让人直接笑出来、也最容易让人相信“它有性格”的场景之一。

## 与 `sz_hand_boundary` 的关系

这两个场景必须成对设计。

- `sz_hand_nuzzle`
  证明它愿意亲近你
- `sz_hand_boundary`
  证明它不是无底线迎合你

如果只有 `nuzzle` 没有 `boundary`，Mira 会显得像一个永远单向讨好的机械玩具。

## 推荐运行逻辑

### 主路径

1. 检测到 `touchDetected=true` 或稳定的 `hand_near`
2. 判断 `touchSide`
3. 如果 `handSpeedBand` 不高，进入亲近路径
4. 前探并微微下送，进入手掌下方
5. 执行 1 到 2 轮小幅 rub
6. 手拿开后追一下
7. 回到自然照明方向

### 安全边界

如果靠近速度太快，或出现高威胁接近，则不要走这个 scene，而应该切到 `sz_hand_boundary`。

## 推荐 context 约定

- `touchSide`
  - `left | center | right`
- `handDistanceBand`
  - `near | contact | leaving`
- `handSpeedBand`
  - `slow | medium | fast`
- `touchDetected`
  - `true | false`

## 主控台接入建议

### 按钮文案

- 中文：`靠手蹭蹭`
- 英文辅助：`Hand Nuzzle`

### 建议输入控件

- 来手方向
- 距离状态
- 接近速度
- 是否已接触

### 建议 step outline

- Approach the hand softly
- Dip under the palm
- Rub with tiny nudges
- Follow once as the hand leaves
- Return to neutral light

## 为什么它必须是 `dynamic_builder`

因为这个 scene 的成败几乎都在方向和幅度上。

如果不根据 `touchSide` 和距离生成 scene，很容易出现：

- 人在左边，动作却偏右
- 手还没到，灯已经空蹭
- 手刚离开就继续顶上去

## 失败信号

- 看起来像撞手，而不是靠近
- 手在左侧，灯体明显往右偏
- 手还没稳定进入交互区就误触发
- 手离开后还持续贴着不退

## 落地建议

这是 Shenzhen 主包里优先级非常高的场景，因为它是最直接的“亲近感证明”。

如果现场只有 2 到 3 个按钮能演得特别稳，这个必须算一个。
