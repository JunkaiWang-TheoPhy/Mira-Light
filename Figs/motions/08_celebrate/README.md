# 跳舞模式 动作程序化说明

## 场景目标

这个场景要表达的是：

- 收到超级开心的消息后，Mira 情绪爆发
- 先往上摇，再往下摇
- 同时灯光做多色变化
- 音乐停后慢慢减速
- 最后左右摇头、身体转一下，像刚跳完舞喘口气

## 真值来源

- 主体动作逻辑以 [`Mira Light 展位交互方案2.pdf`](/Users/Zhuanz/Documents/Github/Mira-Light/docs/Mira%20Light%20展位交互方案2.pdf) 为准
- 上下摇和减速收尾的手绘细节参考 [`Mira Light 展位交互方案3.pdf`](/Users/Zhuanz/Documents/Github/Mira-Light/docs/Mira%20Light%20展位交互方案3.pdf)

## 接口映射说明

- `servo1`：左右上摇 / 左右下摇 / 身体转一下
- `servo2`：整体抬高或压低
- `servo3`：前段配合上扬或下压
- `servo4`：灯头朝上、朝下和收尾摇头

## 灯光策略

这个场景需要明显的多色变化。

当前代码里已经用了：

- 红
- 蓝
- 绿
- 橙
- 紫
- 青
- 最后回暖

并在中段切入：

- `rainbow_cycle`

## 详细时序表

| 步骤 | 起始时间 | 时长 | 动作 |
| --- | --- | --- | --- |
| 0 | `0ms` | `180ms` | 收到消息后预热 |
| 1 | `180ms` | `860ms` | 上摇：中 -> 左上 -> 中 -> 右上 -> 中 |
| 2 | `1040ms` | `860ms` | 下摇：中 -> 左下 -> 中 -> 右下 -> 中 |
| 3 | `1900ms` | `380ms` | 进入彩色庆祝灯效 + 音乐 |
| 4 | `2280ms` | `760ms` | 慢慢减速回正 |
| 5 | `3040ms` | `520ms` | 左右摇头，再身体转一下 |
| 6 | `3560ms` | `420ms` | 回到中性暖光收尾 |

## 当前代码对应片段

```python
steps = [
    pose("neutral"),
    led("solid", brightness=168, color={"r": 255, "g": 236, "b": 180}),
    delay(180),
    absolute(servo1=90, servo2=108, servo3=116, servo4=80),
    led("solid", brightness=198, color={"r": 255, "g": 64, "b": 64}),
    delay(180),
    absolute(servo1=78, servo2=108, servo3=112, servo4=82),
    led("solid", brightness=202, color={"r": 64, "g": 128, "b": 255}),
    delay(180),
    absolute(servo1=90, servo2=106, servo3=114, servo4=80),
    delay(140),
    absolute(servo1=102, servo2=108, servo3=112, servo4=82),
    led("solid", brightness=202, color={"r": 72, "g": 220, "b": 132}),
    delay(180),
    absolute(servo1=90, servo2=106, servo3=114, servo4=80),
    delay(160),
    absolute(servo1=90, servo2=94, servo3=98, servo4=100),
    led("solid", brightness=196, color={"r": 255, "g": 168, "b": 72}),
    delay(180),
    absolute(servo1=82, servo2=94, servo3=96, servo4=100),
    led("solid", brightness=198, color={"r": 208, "g": 96, "b": 255}),
    delay(180),
    absolute(servo1=90, servo2=96, servo3=98, servo4=98),
    delay(140),
    absolute(servo1=100, servo2=94, servo3=96, servo4=100),
    led("solid", brightness=198, color={"r": 64, "g": 224, "b": 224}),
    delay(180),
    absolute(servo1=90, servo2=96, servo3=98, servo4=98),
    delay(180),
    led("rainbow_cycle", brightness=210),
    audio("dance.mp3"),
    action("dance", loops=1),
    delay(380),
    led("solid", brightness=176, color={"r": 255, "g": 208, "b": 156}),
    absolute(servo1=94, servo2=102, servo3=106, servo4=88),
    delay(180),
    absolute(servo1=90, servo2=98, servo3=102, servo4=90),
    delay(180),
    nudge(servo4=4),
    delay(120),
    nudge(servo4=-8),
    delay(120),
    nudge(servo4=4),
    delay(120),
    nudge(servo1=6),
    delay(140),
    nudge(servo1=-6),
    delay(140),
    pose("neutral"),
    led("solid", brightness=140, color=SOFT_WARM),
]
```

## 当前状态判断

这个场景已经从“只调用一个 `dance` 预设”升级成了：

- 上摇
- 下摇
- 多色切换
- 音乐触发
- 减速
- 收尾摇头与转身

但如果以后要继续精细化，还可以再把“快手摇 / 低头摇摆”等拆成更独立的段落。
