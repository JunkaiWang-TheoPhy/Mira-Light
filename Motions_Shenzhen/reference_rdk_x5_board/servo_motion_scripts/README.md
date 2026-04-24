# Servo Motion Scripts

这个目录放的是板端最重要的一类文件：

> 已经在地瓜板上存在、并且和真机舵机动作直接相关的 Python 脚本。

## 当前包含

### 协议与基础控制

- `bus_servo_protocol.py`
- `send_uart1_servo_cmd.py`
- `four_servo_control.py`
- `servo_test.py`

### 姿态与动作序列

- `four_servo_center_delay_2.py`
- `four_servo_pose_delay_2.py`
- `four_servo_pose_delay_2_return_12.py`
- `four_servo_pose_delay_2_return_12_head_turn.py`
- `four_servo_pose_delay_2_return_12_head_turn_once.py`
- `four_servo_pose_delay_2_return_12_head_turn_once_raise_03.py`
- `return_servo_012_center.py`
- `sleep_motion.py`
- `sleep_motion_return_03.py`
- `sleep_motion_with_03_return.py`
- `super_servo_motion.py`
- `servo_1_2_to_2048.py`
- `servo_1_then_2_3_pose.py`
- `servo_pose_2167_1731_2212_1467.py`

### 最新增补的微动作脚本

- `four_servo_pose_2048_2048_2048_2780_separate.py`
- `servo_12_slow_to_1800_2750.py`
- `servo_1_2_dodge_1848_1808.py`
- `servo_1_2_lean_forward_2148_1848.py`
- `servo_1_3_slow_1800_2750.py`
- `servo_2_nod_1900_2200.py`
- `servo_3_shake_2100_2000.py`

## 这个目录为什么是深圳版最重要的参考层

因为这里的脚本不是“设计稿”，而是：

- 已经面向这台板子写过
- 已经考虑了当前串口和协议
- 很多动作已经是实机联调过的

也就是说，如果未来要把深圳版 scene pack 真正落到真机，这里是最接近“硬件真种子”的地方。

## 对深圳 10 交互最直接有帮助的文件

### 直接相关

- `sleep_motion.py`
  - 对应“睡觉 / 收回 / 前后分阶段收拢”
- `four_servo_center_delay_2.py`
  - 对应“先归中再延迟启动某个关节”
- `four_servo_pose_delay_2.py`
  - 对应“先动一部分，再延迟启动另一部分”的分阶段动作结构
- `four_servo_pose_delay_2_return_12.py`
  - 对应“伸出去再回正常形态”
- `four_servo_pose_delay_2_return_12_head_turn.py`
  - 对应“回正常形态后转头”
- `four_servo_pose_delay_2_return_12_head_turn_once.py`
  - 对应“单次转头”
- `four_servo_pose_delay_2_return_12_head_turn_once_raise_03.py`
  - 对应“回正后再抬某些关节”

### 这次新增后特别重要的文件

- `servo_1_2_lean_forward_2148_1848.py`
  - 对应“前倾 / 探身 / 靠近”
- `servo_1_2_dodge_1848_1808.py`
  - 对应“躲闪 / 退让 / 让出空间”
- `servo_2_nod_1900_2200.py`
  - 对应“慢点头”
- `servo_3_shake_2100_2000.py`
  - 对应“慢摇头”

这些文件直接改变了深圳版部分场景的可实现性判断。

### 作为基础能力非常重要

- `bus_servo_protocol.py`
- `send_uart1_servo_cmd.py`
- `four_servo_control.py`

## 对深圳版的实际建议

未来如果你要写：

- `scripts/scenes_shenzhen.py`

不要只看仓库默认 `scripts/scenes.py`。

还应该同时对照这里的板端动作脚本，看看：

- 哪些动作在真机上已经被拆成两段 / 三段
- 哪些动作明显依赖延迟启动
- 哪些“回头”“归中”“抬头”“低头”在板端已有现成脚本
- 哪些新的微动作已经可以直接拼装成更细的情绪表达

## 一句话总结

如果深圳版最终要落到真机，这个目录比默认 `Motions/` 更接近真正的动作实现现实，而且最新版里已经开始出现足够细的微动作积木。
