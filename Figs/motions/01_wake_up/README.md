# 起床动作程序化说明

## 场景目标

这个场景要表达的是：

- 从蜷缩睡眠状态慢慢醒来
- 先有微光，再有身体起身
- 起身后做一次伸懒腰
- 回到正常位时抖两下，像小动物醒来抖毛
- 最后把注意力转向评委

## 接口映射说明

基于 [`ESP32 智能台灯.pdf`](/Users/Zhuanz/Documents/Github/Mira-Light/docs/ESP32%20智能台灯.pdf)，当前程序层只能直接控制 4 个舵机：

- `servo1`：底座转向
- `servo2`：下臂抬升
- `servo3`：前段抬升 / 前探
- `servo4`：灯头俯仰 / 微表情

根据 [`Mira Light 展位交互方案2.pdf`](/Users/Zhuanz/Documents/Github/Mira-Light/docs/Mira%20Light%20展位交互方案2.pdf)，当前版本按 4 个关节理解和实现，不再额外假设底部前后摇摆的第 5 个自由度。

## 建议姿态

```json
{
  "sleep":   {"servo1": 90, "servo2": 80, "servo3": 82,  "servo4": 98},
  "wakeHalf":{"servo1": 90, "servo2": 88, "servo3": 90,  "servo4": 94},
  "wakeHigh":{"servo1": 90, "servo2": 98, "servo3": 108, "servo4": 84},
  "neutral": {"servo1": 96, "servo2": 96, "servo3": 98,  "servo4": 90}
}
```

## 灯光策略

- 起始微光：暖琥珀 `rgb(255,180,120)`，亮度 `8`
- 醒来过渡：同色呼吸，亮度上限 `42`
- 正常状态：柔暖白 `rgb(255,220,180)`，亮度 `132`

如果你希望更明显的“渐变色”观感，但设备只支持 `solid/breathing`，建议用多次 `POST /led` 模拟：

```json
[
  {"mode":"solid","brightness":8,"color":{"r":255,"g":180,"b":120}},
  {"mode":"solid","brightness":18,"color":{"r":255,"g":190,"b":135}},
  {"mode":"solid","brightness":30,"color":{"r":255,"g":205,"b":155}},
  {"mode":"breathing","brightness":42,"color":{"r":255,"g":220,"b":180}},
  {"mode":"solid","brightness":132,"color":{"r":255,"g":220,"b":180}}
]
```

## 详细时序表

| 步骤 | 起始时间 | 时长 | 动作 | 程序说明 |
| --- | --- | --- | --- | --- |
| 0 | `0ms` | `0ms` | 进入睡姿 | `POST /control` 绝对角度到 `sleep` |
| 1 | `0ms` | `280ms` | 微光亮起 | `POST /led` 暖色低亮 |
| 2 | `280ms` | `480ms` | 呼吸变亮 | `POST /led` 切 `breathing` |
| 3 | `760ms` | `420ms` | 身体抬到半醒 | `POST /control` 到 `wakeHalf` |
| 4 | `1180ms` | `320ms` | 继续抬高、仰头 | `POST /control` 到 `wakeHigh` |
| 5 | `1500ms` | `420ms` | 伸懒腰停顿 | 保持姿态，灯继续呼吸 |
| 6 | `1920ms` | `480ms` | 回到正常位并抖两下 | `POST /control` 回 `neutral`，再做两次小幅相对摆动 |
| 7 | `2400ms` | `320ms` | 转向评委 | `servo1` 向评委方向微转 |
| 8 | `2720ms` | `0ms` | 常亮结束态 | `POST /led` 切柔暖常亮 |

## 动作细节

### 1. 睡姿进入

```json
{
  "mode": "absolute",
  "servo1": 90,
  "servo2": 80,
  "servo3": 82,
  "servo4": 98
}
```

### 2. 半醒

```json
{
  "mode": "absolute",
  "servo1": 90,
  "servo2": 88,
  "servo3": 90,
  "servo4": 94
}
```

### 3. 醒到最高点

```json
{
  "mode": "absolute",
  "servo1": 90,
  "servo2": 98,
  "servo3": 108,
  "servo4": 84
}
```

### 4. 抖毛动作

这里不建议大幅摇头，而是用底座和灯头一起做小幅抖动：

```json
[
  {"mode":"relative","servo1":4,"servo4":-3},
  {"delayMs":120},
  {"mode":"relative","servo1":-8,"servo4":6},
  {"delayMs":120},
  {"mode":"relative","servo1":4,"servo4":-3},
  {"delayMs":120},
  {"mode":"relative","servo1":-4,"servo4":3},
  {"delayMs":120},
  {"mode":"relative","servo1":8,"servo4":-6},
  {"delayMs":120},
  {"mode":"relative","servo1":-4,"servo4":3}
]
```

### 5. 转向评委

默认先向左前方看：

```json
{
  "mode": "absolute",
  "servo1": 96,
  "servo2": 96,
  "servo3": 98,
  "servo4": 90
}
```

## 可直接改写成程序步骤

```python
steps = [
    {"type": "control", "atMs": 0, "payload": {"mode": "absolute", "servo1": 90, "servo2": 80, "servo3": 82, "servo4": 98}},
    {"type": "led", "atMs": 0, "payload": {"mode": "solid", "brightness": 8, "color": {"r": 255, "g": 180, "b": 120}}},
    {"type": "delay", "ms": 280},
    {"type": "led", "payload": {"mode": "breathing", "brightness": 42, "color": {"r": 255, "g": 180, "b": 120}}},
    {"type": "delay", "ms": 480},
    {"type": "control", "payload": {"mode": "absolute", "servo1": 90, "servo2": 88, "servo3": 90, "servo4": 94}},
    {"type": "delay", "ms": 420},
    {"type": "control", "payload": {"mode": "absolute", "servo1": 90, "servo2": 98, "servo3": 108, "servo4": 84}},
    {"type": "delay", "ms": 420},
    {"type": "control", "payload": {"mode": "absolute", "servo1": 90, "servo2": 96, "servo3": 98, "servo4": 90}},
    {"type": "control", "payload": {"mode": "relative", "servo1": 4, "servo4": -3}},
    {"type": "delay", "ms": 120},
    {"type": "control", "payload": {"mode": "relative", "servo1": -8, "servo4": 6}},
    {"type": "delay", "ms": 120},
    {"type": "control", "payload": {"mode": "relative", "servo1": 4, "servo4": -3}},
    {"type": "delay", "ms": 120},
    {"type": "control", "payload": {"mode": "absolute", "servo1": 96, "servo2": 96, "servo3": 98, "servo4": 90}},
    {"type": "led", "payload": {"mode": "solid", "brightness": 132, "color": {"r": 255, "g": 220, "b": 180}}}
]
```

## 调试建议

- 如果看起来像“抽动”，先缩小 `servo1` 与 `servo4` 的抖动幅度。
- 如果像“没睡醒”而不是“伸懒腰”，就提高 `wakeHigh.servo3`，同时把 `servo4` 再减小 2 到 4 度，让灯头更仰。
- 如果结构有拉扯感，先把 `servo2/servo3` 的最高位一起各减 4 到 6 度。
