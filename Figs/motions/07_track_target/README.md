# 追踪 动作程序化说明

## 场景目标

这个场景本来的目标是：

- 评委移动书本
- Mira 的灯头和光跟着书移动
- 评委停，它也停
- 评委再动，它再跟

## 当前实现说明

当前 `scripts/scenes.py` 中的 `track_target` 仍然不是“真实视觉闭环”。

现在实现的是：

- 一个 **展位排练用 surrogate choreography**
- 用固定的左 -> 中 -> 右 -> 停 -> 再移动 的跟随节奏
- 去模拟“目标移动时，灯在跟”

这意味着：

- 它适合先排练舞台语言
- 但不能作为“真实视觉能力已完成”的证据

## 接口映射说明

- `servo1`：左右跟随目标
- `servo2`：保持整体高度稳定
- `servo3`：让前段维持桌面照射位
- `servo4`：灯头下压，形成“盯着桌上物体”的姿态

## 灯光策略

- 冷静功能光 `rgb(232,242,255)`，亮度 `170`
- 收尾回到更中性的工作光 `rgb(244,244,236)`，亮度 `156`

## 详细时序表

| 步骤 | 起始时间 | 时长 | 动作 |
| --- | --- | --- | --- |
| 0 | `0ms` | `420ms` | 书在左侧，灯头压低看左桌面 |
| 1 | `420ms` | `360ms` | 目标往中间移动 |
| 2 | `780ms` | `420ms` | 继续到右侧 |
| 3 | `1200ms` | `520ms` | 停住不动 |
| 4 | `1720ms` | `320ms` | 再次开始移动 |
| 5 | `2040ms` | `420ms` | 跟到更右侧 |
| 6 | `2460ms` | `440ms` | 回到中性工作位 |

## 当前代码对应片段

```python
steps = [
    pose("neutral"),
    led("solid", brightness=170, color={"r": 232, "g": 242, "b": 255}),
    absolute(servo1=78, servo2=96, servo3=96, servo4=102),
    delay(420),
    absolute(servo1=88, servo2=96, servo3=96, servo4=98),
    delay(360),
    absolute(servo1=102, servo2=96, servo3=96, servo4=102),
    delay(420),
    delay(520),
    absolute(servo1=94, servo2=96, servo3=96, servo4=98),
    delay(320),
    absolute(servo1=108, servo2=96, servo3=96, servo4=104),
    delay(420),
    pose("neutral"),
    led("solid", brightness=156, color={"r": 244, "g": 244, "b": 236}),
]
```

## 后续必须补的真实能力

要把这个场景从 surrogate 升级成真追踪，至少还需要：

- 摄像头输入
- 目标检测
- 目标坐标到 `servo1/servo4` 的映射
- 低频平滑控制
- 停止条件

所以这个场景目前是：

- 动作语义已落地
- 感知闭环未完成
