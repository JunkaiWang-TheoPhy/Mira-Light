# End-Side Python Motion Orchestration Layer

这份文档讲的是：

> 端侧 Python 动作脚本究竟怎样表达动作编排。

它不是协议文档，而是“板端动作编排真值”说明。

## 先说结论

端侧 Python 脚本并不是直接存储一个个高层 scene 名。

它们当前主要通过下面这些参数表达动作：

- `ids`
- `targets`
- `speeds`
- `run_time`
- `delay_ratio`
- `poll_interval`
- `hold_time`
- `return_target_*`
- `settle_threshold`
- `head_left` / `head_right`
- `cycles`

也就是说，端侧 Python 编排层的现实是：

> **参数化 staged motion**

而不是“scene name -> 下位机自动理解”。

## 1. 这一层的 4 种脚本角色

### A. 协议原语层

文件：

- `bus_servo_protocol.py`
- `send_uart1_servo_cmd.py`

职责：

- 构建协议包
- 发包
- 读位置
- 读状态

这是编排层的基础，不直接代表完整动作。

### B. 四舵机基础控制层

文件：

- `four_servo_control.py`

职责：

- `ping-all`
- `read-pos-all`
- `center`
- `all`
- `pose`
- `deg-all`

它更像板端的小控制台。

### C. staged choreography 层

文件：

- `four_servo_pose_delay_2.py`
- `four_servo_pose_delay_2_return_12.py`
- `sleep_motion.py`
- `sleep_motion_return_03.py`
- `sleep_motion_with_03_return.py`

职责：

- 多阶段动作
- 条件触发后再启动下一个关节
- 动作完成后回姿态

### D. 单功能微动作层

最新版端侧新增了 7 个非常重要的脚本：

- `four_servo_pose_2048_2048_2048_2780_separate.py`
- `servo_12_slow_to_1800_2750.py`
- `servo_1_2_dodge_1848_1808.py`
- `servo_1_2_lean_forward_2148_1848.py`
- `servo_1_3_slow_1800_2750.py`
- `servo_2_nod_1900_2200.py`
- `servo_3_shake_2100_2000.py`

这些脚本的意义很大，因为它们让“微动作拼装”成为可能。

## 2. 当前最常见的编排模式

### 模式一：同步发送固定姿态

例如：

- `four_servo_control.py pose ...`
- `servo_pose_2167_1731_2212_1467.py`

特点：

- 一次性给多个舵机发目标位置
- 适合“去某个姿态”

### 模式二：延迟触发第二阶段

例如：

- `four_servo_pose_delay_2.py`
- `sleep_motion.py`

特点：

- 第一阶段先发一组关节
- 轮询某个舵机位置
- 到达设定 progress ratio 后，再发第二阶段

这说明端侧现实里已经大量使用：

- `delay_ratio`
- `poll_interval`
- `max_wait`

这样的条件式阶段触发。

### 模式三：到位后回归

例如：

- `four_servo_pose_delay_2_return_12.py`
- `sleep_motion_return_03.py`

特点：

- 先到目标姿态
- 判断稳定
- 停一段时间
- 再回到某个“正常态”

### 模式四：姿态后接微动作

例如：

- `...head_turn.py`
- `...head_turn_once.py`
- `servo_2_nod_1900_2200.py`
- `servo_3_shake_2100_2000.py`

特点：

- 主姿态先完成
- 再执行点头、转头、摇头
- 最后回到 return target

## 3. 这对深圳版后续开发意味着什么

### 不能再把深圳版理解成“从零写 10 个大 scene”

更准确的做法应该是：

1. 先识别板端已有 staged motion
2. 再识别新增微动作种子
3. 然后在 `scenes_shenzhen.py` 里重新组合

### 深圳版真正缺的不是所有动作

按端侧现实来看：

- `presence_wake`
  主要缺整合
- `farewell_sleep`
  主要缺链式封装
- `cautious_intro`
  已经有“前倾 + 躲闪 + 点头 + 摇头”材料
- `voice_affect_response`
  已经有 nod / shake / dodge 材料

真正还明显缺大的，是：

- `hand_nuzzle`
- `tabletop_follow`

## 4. 写 `scenes_shenzhen.py` 时推荐的编排方式

建议优先遵循下面这条线：

```text
端侧微动作种子
-> 端侧 staged 组合
-> 高层 Shenzhen scene
```

而不是反过来：

```text
先写一个抽象 scene
-> 再强行找底层去凑
```

## 5. 这层和协议层的关系

这层不是在替代协议层。

关系应该理解成：

```text
Python 动作编排层
决定阶段、节奏、条件触发

协议层
负责把阶段结果发给舵机和灯头
```

## 一句话总结

端侧 Python 动作编排层的现实不是“高层 scene 驱动 everything”，而是：

> 一组参数化 staged motion + 一组新出现的微动作脚本，二者组合起来才构成端侧真实编排能力。
