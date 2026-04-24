# Board File Index

这份索引列出当前从远程地瓜板 `/home/sunrise` 拉回来的主要文件，以及它们对深圳版 scene pack 的价值。

## 1. 舵机动作脚本

目录：

- [servo_motion_scripts](./servo_motion_scripts/README.md)

这里是最重要的一层，因为它直接决定：

- 深圳版有哪些动作已经在板上跑通过
- 哪些动作可以拿来作为 `scenes_shenzhen.py` 的硬件骨架

重点文件包括：

- `sleep_motion.py`
- `four_servo_center_delay_2.py`
- `four_servo_pose_delay_2.py`
- `four_servo_pose_delay_2_return_12.py`
- `four_servo_pose_delay_2_return_12_head_turn.py`
- `four_servo_pose_delay_2_return_12_head_turn_once.py`
- `four_servo_pose_delay_2_return_12_head_turn_once_raise_03.py`
- `super_servo_motion.py`
- `four_servo_control.py`
- `send_uart1_servo_cmd.py`
- `bus_servo_protocol.py`

最新版端侧新增的关键脚本：

- `four_servo_pose_2048_2048_2048_2780_separate.py`
- `servo_12_slow_to_1800_2750.py`
- `servo_1_2_dodge_1848_1808.py`
- `servo_1_2_lean_forward_2148_1848.py`
- `servo_1_3_slow_1800_2750.py`
- `servo_2_nod_1900_2200.py`
- `servo_3_shake_2100_2000.py`

这些文件让板端从“大动作脚本集合”进一步演进成了“可组合微动作种子集合”。

## 0. 协议层和编排层文档

在真正看目录文件前，建议先读：

- [end-side-protocol-layer.md](./end-side-protocol-layer.md)
- [python-motion-orchestration-layer.md](./python-motion-orchestration-layer.md)
- [latest-board-diff-2026-04-25.md](./latest-board-diff-2026-04-25.md)

## 2. 灯头 UART 控制脚本

目录：

- [led_uart_scripts](./led_uart_scripts/README.md)

这一层的价值在于：

- 深圳版如果要把灯光情绪化做实，就必须理解板端 UART3 协议和现有脚本工具

重点文件包括：

- `send_uart3_led_cmd.py`
- `uart3_led_protocol.py`
- `listen_uart3_led.py`
- `uart3_send_raw.py`
- `test_uart3_loopback.py`

## 3. 板端说明文档和协议资料

目录：

- [board_docs](./board_docs/README.md)

这一层是“真值说明层”。

重点文件包括：

- `UART1_SERVO_README.md`
- `UART3_LED_PROTOCOL_README.md`
- `UART3_LOOPBACK_NOTES.md`
- `灯头指令.md`
- `舵机协议手册(191218-0923)(1).pdf`
- `磁编码sts-内存表解析_220714_v3.xlsx`

## 4. 摄像头 / RTSP / 视频转发

目录：

- [camera_streaming](./camera_streaming/README.md)

这一层对深圳版不是一级必须，但对：

- `sz_tabletop_follow`
- 视觉调试
- RTSP 可视化

会有帮助。

## 5. 板端实验脚本

目录：

- [hardware_experiments](./hardware_experiments/README.md)

这一层是低优先级。

可以当：

- 调试痕迹
- PWM 或小功能试验

但不适合直接当深圳版 scene seed。

## 6. 远程网络配置

目录：

- [network_config](./network_config/README.md)

这里目前只有 `frpc.ini`，主要是为了保留：

- 这台板子目前 SSH/VNC 穿透的真实配置痕迹

它对动作设计帮助不大，但对远程联调有帮助。

## 对深圳 10 交互最有价值的板端文件

如果只看“未来要写深圳版动作真值”，优先顺序建议是：

1. `servo_motion_scripts/`
2. `board_docs/`
3. `led_uart_scripts/`
4. `camera_streaming/`

如果只看“最新版新增价值”，优先顺序建议是：

1. `servo_1_2_dodge_1848_1808.py`
2. `servo_1_2_lean_forward_2148_1848.py`
3. `servo_2_nod_1900_2200.py`
4. `servo_3_shake_2100_2000.py`

## 一句话总结

这批板端文件里，真正最值钱的不是相机脚本，而是：

> 板上已经跑通过的舵机动作脚本和 UART 协议说明。
