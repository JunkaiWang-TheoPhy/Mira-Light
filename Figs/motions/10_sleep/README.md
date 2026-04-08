# 睡觉 动作程序化说明

## 场景目标

这个场景要表达的是：

- 评委走远后，Mira 慢慢把自己收回去
- 先低头、降臂
- 再做一次小伸懒腰
- 最后蜷缩起来
- 灯光慢慢变暗到微光

## 真值来源

- 主体逻辑以 [`Mira Light 展位交互方案2.pdf`](/Users/Zhuanz/Documents/Github/Mira-Light/docs/Mira%20Light%20展位交互方案2.pdf) 为准
- 手绘姿态参考 [`Mira Light 展位交互方案3.pdf`](/Users/Zhuanz/Documents/Github/Mira-Light/docs/Mira%20Light%20展位交互方案3.pdf)

## 接口映射说明

- `servo1`：保持中性朝向
- `servo2`：灯臂缓缓降下去
- `servo3`：舒展后再收回
- `servo4`：先低头，再回到睡姿灯头角度

## 灯光策略

当前使用的是暖琥珀的渐暗收尾：

```json
[
  {"mode":"solid","brightness":118,"color":{"r":250,"g":226,"b":184}},
  {"mode":"solid","brightness":60,"color":{"r":255,"g":180,"b":120}},
  {"mode":"solid","brightness":30,"color":{"r":255,"g":180,"b":120}},
  {"mode":"solid","brightness":12,"color":{"r":255,"g":180,"b":120}},
  {"mode":"off","brightness":0}
]
```

## 详细时序表

| 步骤 | 起始时间 | 时长 | 动作 |
| --- | --- | --- | --- |
| 0 | `0ms` | `280ms` | 慢慢低头 |
| 1 | `280ms` | `320ms` | 灯臂缓缓降下去 |
| 2 | `600ms` | `260ms` | 做一次小伸懒腰 |
| 3 | `860ms` | `300ms` | 回到准备睡觉姿态 |
| 4 | `1160ms` | `220ms` | 进入睡姿 |
| 5 | `1380ms` | `2060ms` | 暖光渐暗到微光再熄灭 |

## 当前代码对应片段

```python
steps = [
    pose("neutral"),
    led("solid", brightness=118, color={"r": 250, "g": 226, "b": 184}),
    absolute(servo1=90, servo2=94, servo3=96, servo4=98),
    delay(280),
    absolute(servo1=90, servo2=90, servo3=90, servo4=102),
    delay(320),
    absolute(servo1=90, servo2=96, servo3=104, servo4=88),
    delay(260),
    pose("sleep_ready"),
    delay(300),
    pose("sleep"),
    delay(220),
    led("solid", brightness=60, color=WARM_AMBER),
    delay(260),
    led("solid", brightness=30, color=WARM_AMBER),
    delay(320),
    led("solid", brightness=12, color=WARM_AMBER),
    delay(380),
    led("off", brightness=0),
]
```

## 当前状态判断

这个场景当前已经比较接近完成态：

- 低头
- 降臂
- 小伸懒腰
- 蜷缩
- 渐暗

后续如果还要继续细化，优先改的是：

- 低头到降臂之间的衔接是否更柔和
- 渐暗阶段是否还要增加一段更长的微光停留
