# 卖萌动作程序化说明

## 场景目标

这个场景不是单一歪头，而是要做出：

- 呆萌看着你
- 身体轻轻左右找角度
- 中间关节上提又放下
- 然后做一次胆小探头

## 接口映射说明

- 当前版本严格按 4 个舵机关节实现，不再假设底部额外前后摆自由度。
- `servo1`：底座左右偏摆
- `servo2`：主臂高度
- `servo3`：中间关节抬起/放下以及探头时伸出
- `servo4`：轻点头与探头时灯头角度

## 建议关键姿态

```json
{
  "cute_idle":       {"servo1": 90, "servo2": 96, "servo3": 98,  "servo4": 90},
  "cute_nod":        {"servo1": 90, "servo2": 96, "servo3": 98,  "servo4": 96},
  "base_left":       {"servo1": 82, "servo2": 96, "servo3": 98,  "servo4": 90},
  "base_right":      {"servo1": 98, "servo2": 96, "servo3": 98,  "servo4": 90},
  "elbow_up":        {"servo1": 90, "servo2": 96, "servo3": 108, "servo4": 88},
  "elbow_down":      {"servo1": 90, "servo2": 96, "servo3": 92,  "servo4": 94},
  "probe_forward":   {"servo1": 92, "servo2": 102,"servo3": 114, "servo4": 90},
  "probe_retract":   {"servo1": 90, "servo2": 92, "servo3": 92,  "servo4": 96}
}
```

## 灯光策略

卖萌场景灯光不要太花，核心是动作。

- 主色：暖白 `rgb(255,222,178)`
- 亮度：`124`
- 探头时短暂提升到 `138`
- 缩回时回到 `118`

```json
[
  {"mode":"solid","brightness":124,"color":{"r":255,"g":222,"b":178}},
  {"mode":"solid","brightness":138,"color":{"r":255,"g":228,"b":188}},
  {"mode":"solid","brightness":118,"color":{"r":252,"g":216,"b":174}}
]
```

## 详细时序表

| 步骤 | 起始时间 | 时长 | 动作 | 程序说明 |
| --- | --- | --- | --- | --- |
| 0 | `0ms` | `0ms` | 呆萌站姿 | `cute_idle` |
| 1 | `0ms` | `220ms` | 轻点头 | `servo4` 向下再回来 |
| 2 | `220ms` | `260ms` | 向左看一点 | 底座转左 |
| 3 | `480ms` | `260ms` | 向右看一点 | 底座转右 |
| 4 | `740ms` | `260ms` | 中间关节抬起 | `servo3` 上提 |
| 5 | `1000ms` | `260ms` | 中间关节放下 | `servo3` 下放 |
| 6 | `1260ms` | `420ms` | 慢慢探头 | 主臂和前段一起前伸 |
| 7 | `1680ms` | `180ms` | 突然缩回 | 快速收回 |
| 8 | `1860ms` | `420ms` | 再慢慢探出去 | 再次试探 |
| 9 | `2280ms` | `280ms` | 回到中性位 | 收尾 |

## 关键动作实现

### 1. 轻点头

```json
[
  {"mode":"absolute","servo1":90,"servo2":96,"servo3":98,"servo4":96},
  {"delayMs":120},
  {"mode":"absolute","servo1":90,"servo2":96,"servo3":98,"servo4":90}
]
```

### 2. 左右找角度

```json
[
  {"mode":"absolute","servo1":82,"servo2":96,"servo3":98,"servo4":90},
  {"delayMs":180},
  {"mode":"absolute","servo1":98,"servo2":96,"servo3":98,"servo4":90},
  {"delayMs":180},
  {"mode":"absolute","servo1":90,"servo2":96,"servo3":98,"servo4":90}
]
```

### 3. 探头与缩回

```json
[
  {"mode":"absolute","servo1":92,"servo2":102,"servo3":114,"servo4":90},
  {"delayMs":260},
  {"mode":"absolute","servo1":90,"servo2":92,"servo3":92,"servo4":96},
  {"delayMs":180},
  {"mode":"absolute","servo1":92,"servo2":100,"servo3":110,"servo4":90}
]
```

## 可直接改写成程序步骤

```python
steps = [
    {"type": "control", "atMs": 0, "payload": {"mode": "absolute", "servo1": 90, "servo2": 96, "servo3": 98, "servo4": 90}},
    {"type": "led", "atMs": 0, "payload": {"mode": "solid", "brightness": 124, "color": {"r": 255, "g": 222, "b": 178}}},
    {"type": "control", "payload": {"mode": "absolute", "servo1": 90, "servo2": 96, "servo3": 98, "servo4": 96}},
    {"type": "delay", "ms": 120},
    {"type": "control", "payload": {"mode": "absolute", "servo1": 90, "servo2": 96, "servo3": 98, "servo4": 90}},
    {"type": "delay", "ms": 100},
    {"type": "control", "payload": {"mode": "absolute", "servo1": 82, "servo2": 96, "servo3": 98, "servo4": 90}},
    {"type": "delay", "ms": 180},
    {"type": "control", "payload": {"mode": "absolute", "servo1": 98, "servo2": 96, "servo3": 98, "servo4": 90}},
    {"type": "delay", "ms": 180},
    {"type": "control", "payload": {"mode": "absolute", "servo1": 90, "servo2": 96, "servo3": 108, "servo4": 88}},
    {"type": "delay", "ms": 180},
    {"type": "control", "payload": {"mode": "absolute", "servo1": 90, "servo2": 96, "servo3": 92, "servo4": 94}},
    {"type": "delay", "ms": 180},
    {"type": "led", "payload": {"mode": "solid", "brightness": 138, "color": {"r": 255, "g": 228, "b": 188}}},
    {"type": "control", "payload": {"mode": "absolute", "servo1": 92, "servo2": 102, "servo3": 114, "servo4": 90}},
    {"type": "delay", "ms": 260},
    {"type": "control", "payload": {"mode": "absolute", "servo1": 90, "servo2": 92, "servo3": 92, "servo4": 96}},
    {"type": "delay", "ms": 180},
    {"type": "led", "payload": {"mode": "solid", "brightness": 118, "color": {"r": 252, "g": 216, "b": 174}}},
    {"type": "control", "payload": {"mode": "absolute", "servo1": 92, "servo2": 100, "servo3": 110, "servo4": 90}},
    {"type": "delay", "ms": 260},
    {"type": "control", "payload": {"mode": "absolute", "servo1": 90, "servo2": 96, "servo3": 98, "servo4": 90}}
]
```

## 调试建议

- 如果探头太“凶”，减小 `servo3` 的探出量，或者把 `servo2` 再往上提一点，减少压迫感。
- 如果卖萌感不足，增加轻点头前的停顿。
- 如果左右看太像摇头，缩小 `servo1` 偏转幅度到 `±6°`。
