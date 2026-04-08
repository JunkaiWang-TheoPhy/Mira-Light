# 发呆动作程序化说明

## 场景目标

这个场景不是“再演一个动作”，而是要让观众感觉：

- Mira 有一瞬间走神了
- 它像在盯着某个方向发呆
- 或者像打瞌睡一样慢慢低下去
- 然后突然回过神来

## 接口映射说明

- 当前版本严格按 4 个舵机关节实现，不再假设第 5 个底部前后摇摆自由度。
- `servo1`：转向某个莫名其妙的方向
- `servo2`：身体高度变化
- `servo3`：配合抬头或下沉
- `servo4`：灯头仰起或低垂

## 两个推荐变体

### 变体 A：走神看远处

```json
{
  "neutral":     {"servo1": 90, "servo2": 96, "servo3": 98, "servo4": 90},
  "lookaway":    {"servo1": 74, "servo2": 96, "servo3": 96, "servo4": 84},
  "lookawayHigh":{"servo1": 74, "servo2": 98, "servo3": 100,"servo4": 80},
  "snapBack":    {"servo1": 90, "servo2": 96, "servo3": 98, "servo4": 90}
}
```

### 变体 B：打瞌睡后惊醒

```json
{
  "neutral":     {"servo1": 90, "servo2": 96, "servo3": 98, "servo4": 90},
  "droop1":      {"servo1": 90, "servo2": 92, "servo3": 92, "servo4": 96},
  "droop2":      {"servo1": 90, "servo2": 88, "servo3": 86, "servo4": 102},
  "droop3":      {"servo1": 90, "servo2": 84, "servo3": 82, "servo4": 108},
  "snapBack":    {"servo1": 90, "servo2": 96, "servo3": 98, "servo4": 90}
}
```

## 灯光策略

发呆场景建议光尽量少变化，重点留给停顿。

### 走神版

- 主光：`rgb(245,235,210)`，亮度 `118`
- 停顿时略微降低到 `108`

### 打盹版

- 主光：`rgb(245,230,205)`，亮度 `110`
- 下沉过程中依次降到 `96 / 84 / 70`
- 惊醒后回到 `120`

## 详细时序表

### 变体 A：走神版

| 步骤 | 起始时间 | 时长 | 动作 | 程序说明 |
| --- | --- | --- | --- | --- |
| 0 | `0ms` | `0ms` | 正常照桌面 | 进入 `neutral` |
| 1 | `0ms` | `520ms` | 慢慢抬头并看向远处 | 到 `lookawayHigh` |
| 2 | `520ms` | `3200ms` | 停住发呆 | 什么都不做 |
| 3 | `3720ms` | `180ms` | 快速回神 | 回到 `snapBack` |
| 4 | `3900ms` | `0ms` | 回正常照明 | 结束 |

### 变体 B：打盹版

| 步骤 | 起始时间 | 时长 | 动作 | 程序说明 |
| --- | --- | --- | --- | --- |
| 0 | `0ms` | `0ms` | 正常照桌面 | 进入 `neutral` |
| 1 | `0ms` | `420ms` | 稍微低头 | 到 `droop1` |
| 2 | `420ms` | `420ms` | 再低一点 | 到 `droop2` |
| 3 | `840ms` | `520ms` | 接近睡着 | 到 `droop3` |
| 4 | `1360ms` | `120ms` | 快速惊醒 | 回到 `snapBack` |
| 5 | `1480ms` | `0ms` | 稳定结束 | 继续照桌面 |

## 可直接改写成程序步骤

### 变体 A：走神版

```python
steps = [
    {"type": "control", "atMs": 0, "payload": {"mode": "absolute", "servo1": 90, "servo2": 96, "servo3": 98, "servo4": 90}},
    {"type": "led", "atMs": 0, "payload": {"mode": "solid", "brightness": 118, "color": {"r": 245, "g": 235, "b": 210}}},
    {"type": "control", "payload": {"mode": "absolute", "servo1": 74, "servo2": 98, "servo3": 100, "servo4": 80}},
    {"type": "delay", "ms": 520},
    {"type": "led", "payload": {"mode": "solid", "brightness": 108, "color": {"r": 240, "g": 232, "b": 208}}},
    {"type": "delay", "ms": 3200},
    {"type": "control", "payload": {"mode": "absolute", "servo1": 90, "servo2": 96, "servo3": 98, "servo4": 90}},
    {"type": "led", "payload": {"mode": "solid", "brightness": 118, "color": {"r": 245, "g": 235, "b": 210}}}
]
```

### 变体 B：打盹版

```python
steps = [
    {"type": "control", "atMs": 0, "payload": {"mode": "absolute", "servo1": 90, "servo2": 96, "servo3": 98, "servo4": 90}},
    {"type": "led", "atMs": 0, "payload": {"mode": "solid", "brightness": 110, "color": {"r": 245, "g": 230, "b": 205}}},
    {"type": "control", "payload": {"mode": "absolute", "servo1": 90, "servo2": 92, "servo3": 92, "servo4": 96}},
    {"type": "led", "payload": {"mode": "solid", "brightness": 96, "color": {"r": 240, "g": 225, "b": 200}}},
    {"type": "delay", "ms": 420},
    {"type": "control", "payload": {"mode": "absolute", "servo1": 90, "servo2": 88, "servo3": 86, "servo4": 102}},
    {"type": "led", "payload": {"mode": "solid", "brightness": 84, "color": {"r": 235, "g": 220, "b": 196}}},
    {"type": "delay", "ms": 420},
    {"type": "control", "payload": {"mode": "absolute", "servo1": 90, "servo2": 84, "servo3": 82, "servo4": 108}},
    {"type": "led", "payload": {"mode": "solid", "brightness": 70, "color": {"r": 228, "g": 214, "b": 190}}},
    {"type": "delay", "ms": 520},
    {"type": "control", "payload": {"mode": "absolute", "servo1": 90, "servo2": 96, "servo3": 98, "servo4": 90}},
    {"type": "led", "payload": {"mode": "solid", "brightness": 120, "color": {"r": 245, "g": 235, "b": 210}}}
]
```

## 调试建议

- 发呆版最重要的是停顿时间，不要急着切下一步。
- 如果“惊醒”不够明显，就把回正时长压缩到 `120~180ms`。
- 如果打盹版结构太危险，优先减少 `servo2` 和 `servo3` 的下沉幅度，而不是只改 `servo4`。
