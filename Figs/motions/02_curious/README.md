# 好奇你是谁动作程序化说明

## 场景目标

这个场景要表达的是：

- Mira 先注意到评委
- 想靠近，但又不敢完全靠近
- 有“害羞、试探、再靠近”的连续情绪

## 接口映射说明

当前 ESP32 仍然只暴露 4 个控制通道：

- `servo1`：底座转向
- `servo2`：下臂抬升
- `servo3`：前段关节 / 探出量
- `servo4`：灯头俯仰 / 点头 / 摇头

根据 [`Mira Light 展位交互方案2.pdf`](/Users/Zhuanz/Documents/Github/Mira-Light/docs/Mira%20Light%20展位交互方案2.pdf)，这里的“害羞”不再理解成额外的前后缩关节，而是通过：

- `servo1` 转向远离评委一侧
- `servo4` 灯头下降
- `servo2/servo3` 保持四关节结构下的自然过渡

来表达“有点怕”的感觉。

## 建议关键姿态

```json
{
  "neutral":         {"servo1": 90,  "servo2": 96, "servo3": 98,  "servo4": 90},
  "notice_user":     {"servo1": 94,  "servo2": 96, "servo3": 98,  "servo4": 90},
  "approach_user":   {"servo1": 100, "servo2": 98, "servo3": 102, "servo4": 90},
  "shy_away":        {"servo1": 82,  "servo2": 94, "servo3": 94,  "servo4": 100},
  "peek_out":        {"servo1": 96,  "servo2": 98, "servo3": 106, "servo4": 92},
  "nod_ready":       {"servo1": 96,  "servo2": 98, "servo3": 102, "servo4": 90},
  "fear_turn_away":  {"servo1": 84,  "servo2": 94, "servo3": 98,  "servo4": 102},
  "return_soft":     {"servo1": 94,  "servo2": 98, "servo3": 102, "servo4": 92}
}
```

## 灯光策略

这个场景灯光不要太戏剧化，重点是动作。

- 主色：柔暖白 `rgb(255,225,190)`
- 亮度：`118~132`
- 当进入“害羞/后缩”时，短暂把亮度压到 `96`
- 返回时再回到 `124`

可用渐变模拟：

```json
[
  {"mode":"solid","brightness":124,"color":{"r":255,"g":225,"b":190}},
  {"mode":"solid","brightness":108,"color":{"r":250,"g":220,"b":190}},
  {"mode":"solid","brightness":96,"color":{"r":245,"g":214,"b":188}},
  {"mode":"solid","brightness":124,"color":{"r":255,"g":225,"b":190}}
]
```

## 详细时序表

| 步骤 | 起始时间 | 时长 | 动作 | 程序说明 |
| --- | --- | --- | --- | --- |
| 0 | `0ms` | `0ms` | 中性站姿 | 进入 `neutral` |
| 1 | `0ms` | `280ms` | 注意到评委 | 微转向用户 |
| 2 | `280ms` | `420ms` | 往用户方向靠近 | 底座和前段轻靠近 |
| 3 | `700ms` | `260ms` | 缓慢摇头一次 | 轻微左右摇 |
| 4 | `960ms` | `420ms` | 更靠近地看着你 | 进一步转向与前探 |
| 5 | `1380ms` | `420ms` | 转开并低头 | 朝反方向转开，灯头下压 |
| 6 | `1800ms` | `380ms` | 害羞上下轻动 | 用灯头上下点两次 |
| 7 | `2180ms` | `420ms` | 再探出来 | 转回并前探 |
| 8 | `2600ms` | `260ms` | 左右轻移 | 像试探性观察 |
| 9 | `2860ms` | `280ms` | 面向你点头 | 一次问候式点头 |
| 10 | `3140ms` | `360ms` | 受惊后转开并低头 | 用户靠近时可触发 |
| 11 | `3500ms` | `420ms` | 害羞结束后慢慢往回和前靠 | 回到 `return_soft` |

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

### 3. 再探出来并左右移动

```json
[
  {"mode":"absolute","servo1":96,"servo2":98,"servo3":106,"servo4":92},
  {"delayMs":180},
  {"mode":"relative","servo1":3},
  {"delayMs":120},
  {"mode":"relative","servo1":-6},
  {"delayMs":120},
  {"mode":"relative","servo1":3}
]
```

### 4. 点头

```json
[
  {"mode":"relative","servo4":4},
  {"delayMs":120},
  {"mode":"relative","servo4":-8},
  {"delayMs":140},
  {"mode":"relative","servo4":4}
]
```

## 可直接改写成程序步骤

```python
steps = [
    {"type": "control", "atMs": 0, "payload": {"mode": "absolute", "servo1": 90, "servo2": 96, "servo3": 98, "servo4": 90}},
    {"type": "led", "atMs": 0, "payload": {"mode": "solid", "brightness": 124, "color": {"r": 255, "g": 225, "b": 190}}},
    {"type": "delay", "ms": 280},
    {"type": "control", "payload": {"mode": "absolute", "servo1": 100, "servo2": 98, "servo3": 102, "servo4": 90}},
    {"type": "control", "payload": {"mode": "relative", "servo1": 4, "servo4": -2}},
    {"type": "delay", "ms": 140},
    {"type": "control", "payload": {"mode": "relative", "servo1": -8, "servo4": 4}},
    {"type": "delay", "ms": 140},
    {"type": "control", "payload": {"mode": "relative", "servo1": 4, "servo4": -2}},
    {"type": "delay", "ms": 240},
    {"type": "control", "payload": {"mode": "absolute", "servo1": 82, "servo2": 94, "servo3": 94, "servo4": 100}},
    {"type": "led", "payload": {"mode": "solid", "brightness": 96, "color": {"r": 245, "g": 214, "b": 188}}},
    {"type": "delay", "ms": 380},
    {"type": "control", "payload": {"mode": "absolute", "servo1": 96, "servo2": 98, "servo3": 106, "servo4": 92}},
    {"type": "delay", "ms": 180},
    {"type": "control", "payload": {"mode": "relative", "servo1": 3}},
    {"type": "delay", "ms": 120},
    {"type": "control", "payload": {"mode": "relative", "servo1": -6}},
    {"type": "delay", "ms": 120},
    {"type": "control", "payload": {"mode": "relative", "servo1": 3}},
    {"type": "delay", "ms": 120},
    {"type": "control", "payload": {"mode": "relative", "servo4": 4}},
    {"type": "delay", "ms": 120},
    {"type": "control", "payload": {"mode": "relative", "servo4": -8}},
    {"type": "delay", "ms": 140},
    {"type": "control", "payload": {"mode": "relative", "servo4": 4}},
    {"type": "led", "payload": {"mode": "solid", "brightness": 124, "color": {"r": 255, "g": 225, "b": 190}}}
]
```

## 调试建议

- 如果场景看起来像“攻击性靠近”，先减小 `servo3` 的前探量。
- 如果“害羞”不明显，增加 `servo4` 向下的角度，并把 `servo1` 转开的幅度加大 4 到 6 度。
- 如果点头像抖动，把单次点头延时从 `120ms` 提高到 `160ms`。
