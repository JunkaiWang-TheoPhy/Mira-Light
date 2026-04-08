# 摸一摸动作程序化说明

## 场景目标

这个场景要表达的是：

- 用户把手伸过来时，Mira 主动靠近
- 不只是“被摸”，而是像猫一样往手掌下面蹭
- 手拿开之后还会追一下
- 然后回到自然照明的方向等待下一次互动

## 接口映射说明

当前仍然只用 4 个程序通道：

- `servo1`：左右靠向手的位置
- `servo2`：整体把身体往下沉一点
- `servo3`：前探 / 缩回
- `servo4`：灯头在手下上下轻蹭

## 建议关键姿态

```json
{
  "neutral":       {"servo1": 90, "servo2": 96, "servo3": 98,  "servo4": 90},
  "reach_soft":    {"servo1": 94, "servo2": 100,"servo3": 108, "servo4": 90},
  "reach_lower":   {"servo1": 94, "servo2": 104,"servo3": 110, "servo4": 94},
  "rub_left":      {"servo1": 98, "servo2": 104,"servo3": 110, "servo4": 94},
  "rub_right":     {"servo1": 90, "servo2": 104,"servo3": 110, "servo4": 86},
  "follow_hand":   {"servo1": 100,"servo2": 98, "servo3": 104, "servo4": 90},
  "return_soft":   {"servo1": 92, "servo2": 96, "servo3": 98,  "servo4": 92}
}
```

## 灯光策略

这个场景灯光要很暖，而且有“被抚摸时更舒服”的感觉。

- 起始：暖白 `rgb(255,190,120)`，亮度 `168`
- 抚摸中：更暖一点 `rgb(255,175,105)`，亮度 `182`
- 收尾：回到柔暖 `rgb(255,210,170)`，亮度 `138`

可以用下列渐变模拟舒适感：

```json
[
  {"mode":"solid","brightness":168,"color":{"r":255,"g":190,"b":120}},
  {"mode":"solid","brightness":176,"color":{"r":255,"g":182,"b":112}},
  {"mode":"solid","brightness":182,"color":{"r":255,"g":175,"b":105}},
  {"mode":"solid","brightness":152,"color":{"r":255,"g":195,"b":145}},
  {"mode":"solid","brightness":138,"color":{"r":255,"g":210,"b":170}}
]
```

## 详细时序表

| 步骤 | 起始时间 | 时长 | 动作 | 程序说明 |
| --- | --- | --- | --- | --- |
| 0 | `0ms` | `0ms` | 中性准备 | 进入 `neutral` |
| 1 | `0ms` | `260ms` | 主动靠近手 | 到 `reach_soft` |
| 2 | `260ms` | `220ms` | 身体往下送一点 | 到 `reach_lower` |
| 3 | `480ms` | `640ms` | 在手下轻蹭 | 做上下 + 左右组合摆动 |
| 4 | `1120ms` | `260ms` | 灯光升到最暖 | 维持抚摸氛围 |
| 5 | `1380ms` | `320ms` | 追一下手的方向 | `servo1` 朝手的离开方向增加 6 到 10 度 |
| 6 | `1700ms` | `360ms` | 慢慢回来 | 回到 `return_soft` |
| 7 | `2060ms` | `240ms` | 回中性位 | 回到 `neutral` |

## 关键动作实现

### 1. 手下蹭动

这里建议同时做“上下蹭”和“左右蹭”，但幅度都不要太大：

```json
[
  {"mode":"absolute","servo1":98,"servo2":104,"servo3":110,"servo4":94},
  {"delayMs":140},
  {"mode":"absolute","servo1":90,"servo2":104,"servo3":110,"servo4":86},
  {"delayMs":140},
  {"mode":"absolute","servo1":98,"servo2":103,"servo3":109,"servo4":94},
  {"delayMs":140},
  {"mode":"absolute","servo1":90,"servo2":103,"servo3":109,"servo4":86},
  {"delayMs":140}
]
```

### 2. 追手

如果默认手是往右侧拿开：

```json
{
  "mode": "absolute",
  "servo1": 100,
  "servo2": 98,
  "servo3": 104,
  "servo4": 90
}
```

### 3. 回到自然照明方向

```json
{
  "mode": "absolute",
  "servo1": 92,
  "servo2": 96,
  "servo3": 98,
  "servo4": 92
}
```

## 可直接改写成程序步骤

```python
steps = [
    {"type": "control", "atMs": 0, "payload": {"mode": "absolute", "servo1": 90, "servo2": 96, "servo3": 98, "servo4": 90}},
    {"type": "led", "atMs": 0, "payload": {"mode": "solid", "brightness": 168, "color": {"r": 255, "g": 190, "b": 120}}},
    {"type": "control", "payload": {"mode": "absolute", "servo1": 94, "servo2": 100, "servo3": 108, "servo4": 90}},
    {"type": "delay", "ms": 260},
    {"type": "control", "payload": {"mode": "absolute", "servo1": 94, "servo2": 104, "servo3": 110, "servo4": 94}},
    {"type": "delay", "ms": 220},
    {"type": "control", "payload": {"mode": "absolute", "servo1": 98, "servo2": 104, "servo3": 110, "servo4": 94}},
    {"type": "delay", "ms": 140},
    {"type": "control", "payload": {"mode": "absolute", "servo1": 90, "servo2": 104, "servo3": 110, "servo4": 86}},
    {"type": "delay", "ms": 140},
    {"type": "control", "payload": {"mode": "absolute", "servo1": 98, "servo2": 103, "servo3": 109, "servo4": 94}},
    {"type": "delay", "ms": 140},
    {"type": "control", "payload": {"mode": "absolute", "servo1": 90, "servo2": 103, "servo3": 109, "servo4": 86}},
    {"type": "delay", "ms": 140},
    {"type": "led", "payload": {"mode": "solid", "brightness": 182, "color": {"r": 255, "g": 175, "b": 105}}},
    {"type": "delay", "ms": 220},
    {"type": "control", "payload": {"mode": "absolute", "servo1": 100, "servo2": 98, "servo3": 104, "servo4": 90}},
    {"type": "delay", "ms": 320},
    {"type": "control", "payload": {"mode": "absolute", "servo1": 92, "servo2": 96, "servo3": 98, "servo4": 92}},
    {"type": "led", "payload": {"mode": "solid", "brightness": 138, "color": {"r": 255, "g": 210, "b": 170}}},
    {"type": "delay", "ms": 240},
    {"type": "control", "payload": {"mode": "absolute", "servo1": 90, "servo2": 96, "servo3": 98, "servo4": 90}}
]
```

## 调试建议

- 如果蹭动看起来像“撞手”，先减小 `servo1` 的左右摆幅。
- 如果像“只是头在动”，增加 `servo2/servo3` 的参与，让身体稍微跟过去。
- 如果“追手”太明显导致攻击感，把追手幅度控制在 `servo1 ± 6°` 以内。
- 结束时不要停在“探出去”的姿态，应该回到自然照明方向，而不是继续索取互动。
