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

## 一句话总结

如果深圳版最终要落到真机，这个目录比默认 `Motions/` 更接近真正的动作实现现实。
