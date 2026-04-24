# `sz_sigh_comfort` 规格书

## 核心规格

- `sceneId`: `sz_sigh_comfort`
- `demo_goal`: 证明 Mira 能捕捉到人的疲惫和叹气，并用低侵入、暖色、安静的方式给出安慰反馈。
- `scene_mode`: `event_scene`
- `apiContextKeys`: `transcript`, `sighStrength`, `speakerDirection`
- `fallback_behavior`: 没有麦克风或叹气检测时，由主持人先说“你对着它叹口气”，再手动触发固定安慰版 scene。
- `operator_cue`: “你可以对着它轻轻叹口气，它会像听懂了一样看你一下，光也会变暖。”
- `success_signal`: 评委能明显感受到“它接住了你的状态”，而不是听到一句话后做了一个普通打招呼动作。

## 当前端侧种子

这个场景现在已经有一版可落地的一阶材料：

- 灯头 `BREATHE` / `BRI` / `WAKE`
- `servo_2_nod_1900_2200.py`

也就是说，第一版“暖光 + 小幅低头 / 点头”的安慰表达已经能做，不再需要从零想动作。

## 为什么这个场景非常关键

深圳材料里已经把“叹气检测”定义成一个非常强的价值主张：

> 只用 30 秒，就证明它感知到了你的状态。

这说明它不是附加功能，而是深圳版必须认真设计的一级交互。

## 这个场景不应该怎么演

它不应该：

- 太热情
- 太活泼
- 太像问候
- 太像“被触发了一个固定动作”

它应该更像：

- 安静看向你
- 稍微低一点
- 灯光变暖
- 呼吸更慢

## 推荐运行逻辑

1. 收到 `sigh_detected`
2. 提取 `speakerDirection`
3. 以小幅度朝说话方向偏转
4. 稍微低头
5. 灯光切到暖呼吸
6. 如果有 `transcript`，记录在 notes 或 runtime state 中

## 推荐 context 约定

- `transcript`
  - 例如 `唉`
- `sighStrength`
  - `light | medium | heavy`
- `speakerDirection`
  - `left | center | right`

## 主控台接入建议

### 按钮文案

- 中文：`叹气安慰`
- 英文辅助：`Sigh Comfort`

### 建议输入控件

- 文本记录
- 叹气强度
- 说话方向

### 建议 step outline

- Notice the sigh
- Turn softly toward the speaker
- Lower and warm the light
- Hold a slow breathing glow
- Recover gently

## 为什么它是 `event_scene`

因为这不是一幕长戏，而是一种即时情绪反馈。

重点不在复杂 choreography，而在：

- 触发正确
- 情绪方向正确
- 幅度克制

## 失败信号

- 反应太大，像被惊吓
- 灯光没变暖，观众看不出安慰感
- 总是固定朝一个方向，不像在回应当下的人
- 动作显得积极兴奋，而不是共情

## 落地建议

这个场景非常适合深圳现场，因为它能把 Mira 从“会动的展品”提升成“能理解状态的对象”。
