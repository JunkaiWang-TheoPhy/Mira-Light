# `sz_presence_wake` 规格书

## 核心规格

- `sceneId`: `sz_presence_wake`
- `demo_goal`: 证明 Mira 能感知“有人进入主展示区”，并以“醒来迎接”的方式表达注意力启动，而不是突然机械开机。
- `scene_mode`: `hybrid`
- `apiContextKeys`: `targetDirection`, `presenceConfidence`, `engagementZone`, `wakeReason`
- `fallback_behavior`: 没有稳定人体检测时，由导演台手动触发固定 wake choreography，并在请求里标记 `wakeReason=manual_demo`。
- `operator_cue`: “当 Mira 感觉到有人来了，它不会立刻转过去，而是会先醒来，再慢慢把注意力放到你身上。”
- `success_signal`: 评委能明显看出“微光 -> 半醒 -> 起身 -> 伸展 -> 看向来人”的分层，且看向方向与来人方向一致。

## 当前端侧种子

当前板端已经有较强种子，可以支撑第一版实现：

- `four_servo_pose_delay_2.py`
- `four_servo_pose_2048_2048_2048_2780_separate.py`
- `servo_12_slow_to_1800_2750.py`
- 灯头 `WAKE` / `BREATHE` / `BRI`

所以这个场景当前主要缺的是“整合成深圳版脚本”，不是缺底层动作材料。

## 这个场景为什么必须存在

Shenzhen pack 的第一幕不能只是“灯动起来了”，而必须是：

> 它察觉到了你的存在，所以它醒了。

这和默认 `wake_up` 的区别在于：

- 默认版更像导演稿中的开场动作
- 深圳版更强调“presence-driven wake”

也就是说，这一幕证明的不是“动作丰富”，而是“注意力被激活”。

## 设计目标

这个场景要同时满足 3 个层次：

1. 视觉上像从睡姿苏醒
2. 语义上像注意到有人
3. 工程上允许既能手动演，也能自动触发

## 推荐运行逻辑

### 自动主路径

当视觉层确认有人进入主展示区时：

1. 记录 `engagementZone`
2. 根据来人方向填充 `targetDirection`
3. 若 `presenceConfidence` 超过阈值，则触发 `sz_presence_wake`
4. 醒来后把最后一个停留点对准 `targetDirection`

### 手动 fallback 路径

如果现场视觉不稳定：

1. 主持人先说“它感觉到有人来了”
2. 导演台手动按 `sz_presence_wake`
3. context 里只保留一个简化方向值

## 推荐 choreography 骨架

这一幕不建议做得很长。

推荐分 5 段：

1. `sleep` 等待姿态
2. 微光亮起
3. 半醒抬头
4. 高位伸展
5. 朝 `targetDirection` 慢慢落稳

不要把“抖毛”做得太重。

深圳版的重点是“注意力启动”，不是“可爱程度最大化”。

## 推荐 context 约定

- `targetDirection`
  - `left | center | right`
- `presenceConfidence`
  - `0.0 ~ 1.0`
- `engagementZone`
  - `edge | primary | near`
- `wakeReason`
  - `vision_presence`
  - `manual_demo`
  - `re_entry`

## 主控台接入建议

### 按钮文案

- 中文：`感知到来人 / 醒来`
- 英文辅助：`Presence Wake`

### 主控台最小输入控件

- 来人方向下拉
- 触发原因下拉

### 建议 step outline

- Warm glow starts
- Half-awake lift
- Stretch upward
- Stabilize attention
- Look toward the guest

## 与现有系统的关系

这个场景可以借用现有：

- `wake_up` 的姿态骨架

但不建议直接等同于 `wake_up`，因为 Shenzhen 版需要额外绑定：

- `presenceConfidence`
- `engagementZone`
- `targetDirection`

## 失败信号

- 一开始就突然抬起，像机械上电
- 最后朝向和来人方向不一致
- 边缘路人路过也频繁误触发
- 每次演示都像同一个固定方向预录动作

## 落地建议

这应该是 Shenzhen pack 最优先落地的场景之一，因为它决定评委在第一个 3 秒里会不会相信：

> 这盏灯真的在“注意到人”。
