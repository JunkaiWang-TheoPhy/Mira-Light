# 起床动作程序化说明

## 场景目标

这个场景要表达的是：

- 从蜷缩睡眠状态慢慢醒来
- 先有微光，再有身体起身
- 起身后做一次伸懒腰
- 回到正常位时抖两下，像小动物醒来抖毛
- 最后把注意力转向评委

## 接口映射说明

基于 [`ESP32 智能台灯.pdf`](/Users/Zhuanz/Documents/Github/Mira-Light/docs/ESP32%20智能台灯.pdf) 与 [`Mira Light 展位交互方案2.pdf`](/Users/Zhuanz/Documents/Github/Mira-Light/docs/Mira%20Light%20展位交互方案2.pdf)，当前版本严格按 4 个舵机关节实现：

- `servo1`：底座转向
- `servo2`：下臂抬升
- `servo3`：前段抬升 / 前探
- `servo4`：灯头俯仰 / 微表情

不再假设底部存在额外的前后摇摆自由度。

## 当前代码对应姿态

```json
{
  "sleep":    {"servo1": 90, "servo2": 80,  "servo3": 82,  "servo4": 98},
  "wakeHalf": {"servo1": 90, "servo2": 88,  "servo3": 90,  "servo4": 94},
  "wakeHigh": {"servo1": 90, "servo2": 98,  "servo3": 108, "servo4": 84},
  "stretch":  {"servo1": 90, "servo2": 100, "servo3": 112, "servo4": 82},
  "neutral":  {"servo1": 96, "servo2": 96,  "servo3": 98,  "servo4": 90}
}
```

## 灯光时序

```json
[
  {"atMs":0,    "mode":"solid",     "brightness":6,   "color":{"r":255,"g":176,"b":116}},
  {"atMs":220,  "mode":"solid",     "brightness":12,  "color":{"r":255,"g":188,"b":130}},
  {"atMs":400,  "mode":"solid",     "brightness":22,  "color":{"r":255,"g":200,"b":148}},
  {"atMs":580,  "mode":"breathing", "brightness":42,  "color":{"r":255,"g":214,"b":172}},
  {"atMs":2660, "mode":"solid",     "brightness":132, "color":{"r":255,"g":220,"b":180}}
]
```

## 详细时序表

| 步骤 | 起始时间 | 时长 | 动作 | 程序说明 |
| --- | --- | --- | --- | --- |
| 0 | `0ms` | `0ms` | 进入睡姿 | `pose("sleep")` |
| 1 | `0ms` | `220ms` | 微光亮起 | 最低亮度暖琥珀 |
| 2 | `220ms` | `180ms` | 第一段提亮 | 稍微亮一点，仍然克制 |
| 3 | `400ms` | `180ms` | 第二段提亮 | 从“睁眼”过渡到“醒来” |
| 4 | `580ms` | `420ms` | 呼吸灯过渡 | 让情绪感先起来 |
| 5 | `1000ms` | `360ms` | 身体抬到半醒 | `pose("wake_half")` |
| 6 | `1360ms` | `320ms` | 抬到高位 | `absolute(90,98,108,84)` |
| 7 | `1680ms` | `700ms` | 伸懒腰停顿 | 高于正常位并后仰，按 PDF2 停约 1 秒 |
| 8 | `2380ms` | `720ms` | 回到正常位并抖毛 | 回 `neutral` 后做 6 个小抖动阶段 |
| 9 | `3100ms` | `0ms` | 看向评委并常亮收尾 | `absolute(96,96,98,90)` + 柔暖常亮 |

## 抖毛动作细节

```json
[
  {"mode":"relative","servo1":4,  "servo4":-2},
  {"delayMs":120},
  {"mode":"relative","servo1":-8, "servo4":4},
  {"delayMs":120},
  {"mode":"relative","servo1":4,  "servo4":-2},
  {"delayMs":120},
  {"mode":"relative","servo1":-4, "servo4":2},
  {"delayMs":120},
  {"mode":"relative","servo1":8,  "servo4":-4},
  {"delayMs":120},
  {"mode":"relative","servo1":-4, "servo4":2}
]
```

## 当前代码对应片段

```python
steps = [
    pose("sleep"),
    led("solid", brightness=6, color={"r": 255, "g": 176, "b": 116}),
    delay(220),
    led("solid", brightness=12, color={"r": 255, "g": 188, "b": 130}),
    delay(180),
    led("solid", brightness=22, color={"r": 255, "g": 200, "b": 148}),
    delay(180),
    led("breathing", brightness=42, color={"r": 255, "g": 214, "b": 172}),
    delay(420),
    pose("wake_half"),
    delay(360),
    absolute(servo1=90, servo2=98, servo3=108, servo4=84),
    delay(320),
    absolute(servo1=90, servo2=100, servo3=112, servo4=82),
    delay(700),
    absolute(servo1=90, servo2=96, servo3=98, servo4=90),
    nudge(servo1=4, servo4=-2),
    delay(120),
    nudge(servo1=-8, servo4=4),
    delay(120),
    nudge(servo1=4, servo4=-2),
    delay(120),
    nudge(servo1=-4, servo4=2),
    delay(120),
    nudge(servo1=8, servo4=-4),
    delay(120),
    nudge(servo1=-4, servo4=2),
    delay(120),
    absolute(servo1=96, servo2=96, servo3=98, servo4=90),
    led("solid", brightness=132, color=SOFT_WARM),
]
```

## 调试建议

- 如果看起来像“抽动”，先缩小 `servo1` 与 `servo4` 的抖动幅度。
- 如果像“没睡醒”而不是“伸懒腰”，提高 `servo3` 高位并让 `servo4` 再减小 2 到 4 度。
- 如果结构有拉扯感，先把 `servo2/servo3` 的高位一起各减 4 到 6 度。
