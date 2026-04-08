# 好奇你是谁动作程序化说明

## 场景目标

这个场景要表达的是：

- Mira 先注意到评委
- 想靠近，但又不敢完全靠近
- 有“试探、害羞、再靠近”的连续情绪

## 接口映射说明

当前 ESP32 只暴露 4 个控制通道：

- `servo1`：底座转向
- `servo2`：下臂抬升
- `servo3`：前段关节 / 探出量
- `servo4`：灯头俯仰 / 点头 / 摇头

根据 [`Mira Light 展位交互方案2.pdf`](/Users/Zhuanz/Documents/Github/Mira-Light/docs/Mira%20Light%20展位交互方案2.pdf)，这里的“有点怕”不是额外后缩自由度，而是：

- `servo1` 转向远离评委侧
- `servo4` 灯头下降
- `servo2/servo3` 做自然过渡

## 当前代码对应姿态

```json
{
  "neutral":        {"servo1": 90,  "servo2": 96, "servo3": 98,  "servo4": 90},
  "notice_user":    {"servo1": 94,  "servo2": 96, "servo3": 98,  "servo4": 90},
  "approach_user":  {"servo1": 100, "servo2": 98, "servo3": 102, "servo4": 90},
  "shy_turn":       {"servo1": 82,  "servo2": 94, "servo3": 94,  "servo4": 100},
  "peek_out":       {"servo1": 96,  "servo2": 98, "servo3": 106, "servo4": 92},
  "nod_ready":      {"servo1": 96,  "servo2": 98, "servo3": 102, "servo4": 90},
  "fear_turn_away": {"servo1": 84,  "servo2": 94, "servo3": 98,  "servo4": 102},
  "return_soft":    {"servo1": 94,  "servo2": 98, "servo3": 102, "servo4": 92}
}
```

## 灯光时序

```json
[
  {"atMs":0,    "mode":"solid","brightness":124,"color":{"r":255,"g":225,"b":190}},
  {"atMs":1240, "mode":"solid","brightness":100,"color":{"r":246,"g":214,"b":186}},
  {"atMs":1980, "mode":"solid","brightness":124,"color":{"r":255,"g":225,"b":190}}
]
```

## 详细时序表

| 步骤 | 起始时间 | 时长 | 动作 | 程序说明 |
| --- | --- | --- | --- | --- |
| 0 | `0ms` | `160ms` | 中性亮起 | 柔暖白进入观察状态 |
| 1 | `160ms` | `220ms` | 注意到评委 | `absolute(94,96,98,90)` |
| 2 | `380ms` | `260ms` | 向评委方向靠近一点 | `absolute(100,98,102,90)` |
| 3 | `640ms` | `420ms` | 缓慢摇头一次 | 小幅左右摇，像确认你是谁 |
| 4 | `1060ms` | `220ms` | 再更靠近一点看着用户 | 对应 PDF2 第 3 步 |
| 5 | `1280ms` | `500ms` | 转开并低头 | 害羞地转开，再做两次上下灯头 |
| 6 | `1780ms` | `620ms` | 再探出来并左右轻移 | 转回并探出来观察 |
| 7 | `2400ms` | `840ms` | 面向你点头 | 先归位再做一次问候式点头 |
| 8 | `3240ms` | `360ms` | 如果继续靠近则转开低头 | `fear_turn_away` |
| 9 | `3600ms` | `0ms` | 害羞结束后慢慢往回和前靠 | `return_soft` |

## 关键动作实现

### 1. 缓慢摇头一次

```json
[
  {"mode":"relative","servo1":4,"servo4":-2},
  {"delayMs":140},
  {"mode":"relative","servo1":-8,"servo4":4},
  {"delayMs":140},
  {"mode":"relative","servo1":4,"servo4":-2}
]
```

### 2. 害羞上下灯头

```json
[
  {"mode":"relative","servo4":4},
  {"delayMs":120},
  {"mode":"relative","servo4":-8},
  {"delayMs":120},
  {"mode":"relative","servo4":4}
]
```

### 3. 点头

```json
[
  {"mode":"relative","servo4":4},
  {"delayMs":120},
  {"mode":"relative","servo4":-8},
  {"delayMs":140},
  {"mode":"relative","servo4":4}
]
```

## 当前代码对应片段

```python
steps = [
    pose("neutral"),
    led("solid", brightness=124, color={"r": 255, "g": 225, "b": 190}),
    delay(160),
    absolute(servo1=94, servo2=96, servo3=98, servo4=90),
    delay(220),
    absolute(servo1=100, servo2=98, servo3=102, servo4=90),
    delay(260),
    nudge(servo1=4, servo4=-2),
    delay(140),
    nudge(servo1=-8, servo4=4),
    delay(140),
    nudge(servo1=4, servo4=-2),
    delay(180),
    absolute(servo1=102, servo2=98, servo3=104, servo4=90),
    delay(220),
    led("solid", brightness=100, color={"r": 246, "g": 214, "b": 186}),
    absolute(servo1=82, servo2=94, servo3=94, servo4=100),
    delay(320),
    nudge(servo4=4),
    delay(120),
    nudge(servo4=-8),
    delay(120),
    nudge(servo4=4),
    delay(180),
    led("solid", brightness=124, color={"r": 255, "g": 225, "b": 190}),
    absolute(servo1=96, servo2=98, servo3=106, servo4=92),
    delay(220),
    nudge(servo1=3),
    delay(110),
    nudge(servo1=-6),
    delay(110),
    nudge(servo1=3),
    delay(160),
    absolute(servo1=96, servo2=98, servo3=102, servo4=90),
    nudge(servo4=4),
    delay(120),
    nudge(servo4=-8),
    delay(140),
    nudge(servo4=4),
    delay(180),
    absolute(servo1=84, servo2=94, servo3=98, servo4=102),
    delay(240),
    absolute(servo1=94, servo2=98, servo3=102, servo4=92),
]
```

## 调试建议

- 如果场景看起来像“攻击性靠近”，先减小 `servo3` 的前探量。
- 如果“害羞”不明显，增加 `servo4` 向下的角度，并把 `servo1` 转开的幅度加大 4 到 6 度。
- 如果点头像抖动，把单次点头延时从 `120ms` 提高到 `160ms`。
