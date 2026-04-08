# 挥手送别 动作程序化说明

## 场景目标

这个场景要表达的是：

- 先目送评委离开
- 再做两次慢慢点头式挥手
- 最后低头，像有点舍不得

## 真值来源

- 主体逻辑以 [`Mira Light 展位交互方案2.pdf`](/Users/Zhuanz/Documents/Github/Mira-Light/docs/Mira%20Light%20展位交互方案2.pdf) 为准
- 挥手部分的手绘节奏参考 [`Mira Light 展位交互方案3.pdf`](/Users/Zhuanz/Documents/Github/Mira-Light/docs/Mira%20Light%20展位交互方案3.pdf)

## 接口映射说明

- `servo1`：目送方向
- `servo2`：告别时的整体高度变化
- `servo3`：支撑前段姿态
- `servo4`：慢慢点头两次，最后低头

## 灯光策略

- 柔和、略降亮度
- `rgb(255,214,176)`，亮度 `108`
- 收尾 `rgb(255,210,170)`，亮度 `90`

## 详细时序表

| 步骤 | 起始时间 | 时长 | 动作 |
| --- | --- | --- | --- |
| 0 | `0ms` | `420ms` | 先目送评委离开的方向 |
| 1 | `420ms` | `980ms` | 两次慢慢点头式挥手 |
| 2 | `1400ms` | `360ms` | 微微低头 |
| 3 | `1760ms` | `600ms` | 回中性位并降亮度 |

## 当前代码对应片段

```python
steps = [
    pose("neutral"),
    led("solid", brightness=108, color={"r": 255, "g": 214, "b": 176}),
    absolute(servo1=106, servo2=96, servo3=100, servo4=92),
    delay(420),
    nudge(servo4=5),
    delay(180),
    nudge(servo4=-10),
    delay(180),
    nudge(servo4=5),
    delay(220),
    nudge(servo4=5),
    delay(180),
    nudge(servo4=-10),
    delay(180),
    nudge(servo4=5),
    delay(220),
    absolute(servo1=102, servo2=92, servo3=96, servo4=100),
    delay(180),
    pose("neutral"),
    led("solid", brightness=90, color={"r": 255, "g": 210, "b": 170}),
]
```

## 当前状态判断

相比之前固定的 `farewell_look + wave + bow`，现在已经细化成：

- 先目送
- 再挥手
- 再低头

不过它仍然是“固定离场方向版本”。

真正要达到最终版，还需要：

- 根据评委离场方向动态生成 `servo1` 的目标角度
