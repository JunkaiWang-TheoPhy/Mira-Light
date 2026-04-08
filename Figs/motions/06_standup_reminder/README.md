# 久坐检测：蹭蹭 动作程序化说明

## 场景目标

这个场景要表达的是：

- 不是发警报，而是像宠物一样提醒你起来
- 通过三次“埋头 -> 顶起 -> 后退”的蹭蹭动作建立节奏
- 问答之后用两次点头表示“是的”
- 被拒绝后轻轻摇一下头，再回到原位

## 接口映射说明

当前版本严格按 4 个舵机关节实现：

- `servo1`：转向评委与轻摇头
- `servo2`：整体抬升与前埋时的身体高度
- `servo3`：往前顶和后退的前段动作
- `servo4`：埋头、抬头、点头

## 当前代码对应动作链条

```text
neutral
-> turn_to_user
-> bump_1
-> bump_2
-> bump_3
-> nod_twice
-> soft_shake_once
-> neutral
```

## 灯光策略

- 起始：柔暖工作光 `rgb(255,218,176)`，亮度 `132`
- 结束：回到 `SOFT_WARM`，亮度 `118`

这个场景不需要强烈灯效，重点是身体节奏。

## 详细时序表

| 步骤 | 起始时间 | 时长 | 动作 |
| --- | --- | --- | --- |
| 0 | `0ms` | `220ms` | 转向评委并前送 |
| 1 | `220ms` | `400ms` | 第一次蹭蹭 |
| 2 | `620ms` | `400ms` | 第二次蹭蹭 |
| 3 | `1020ms` | `440ms` | 第三次蹭蹭 |
| 4 | `1460ms` | `920ms` | 点头两次 |
| 5 | `2380ms` | `420ms` | 轻轻摇头一次 |
| 6 | `2800ms` | `320ms` | 慢慢回到原位 |

## 当前代码对应片段

```python
steps = [
    pose("neutral"),
    led("solid", brightness=132, color={"r": 255, "g": 218, "b": 176}),
    absolute(servo1=98, servo2=100, servo3=102, servo4=92),
    delay(220),
    absolute(servo1=98, servo2=102, servo3=98, servo4=102),
    delay(140),
    absolute(servo1=98, servo2=96, servo3=110, servo4=88),
    delay(140),
    absolute(servo1=96, servo2=100, servo3=102, servo4=94),
    delay(120),
    absolute(servo1=98, servo2=102, servo3=98, servo4=102),
    delay(140),
    absolute(servo1=98, servo2=96, servo3=110, servo4=88),
    delay(140),
    absolute(servo1=96, servo2=100, servo3=102, servo4=94),
    delay(120),
    absolute(servo1=98, servo2=102, servo3=98, servo4=102),
    delay(140),
    absolute(servo1=98, servo2=96, servo3=110, servo4=88),
    delay(140),
    absolute(servo1=96, servo2=100, servo3=102, servo4=94),
    delay(160),
    nudge(servo4=5),
    delay(140),
    nudge(servo4=-10),
    delay(140),
    nudge(servo4=5),
    delay(180),
    nudge(servo4=5),
    delay(140),
    nudge(servo4=-10),
    delay(140),
    nudge(servo4=5),
    delay(180),
    nudge(servo1=4),
    delay(120),
    nudge(servo1=-8),
    delay(120),
    nudge(servo1=4),
    delay(180),
    pose("neutral"),
    led("solid", brightness=118, color=SOFT_WARM),
]
```

## 说明

这个场景现在已经补上了之前缺的动作：

- “不要”之后的轻摇头
- 每次蹭蹭之间的后退节奏

如果后续再改，优先保持这两个动作不要丢。
