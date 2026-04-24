# `sz_farewell_sleep` 固定动作实现指导

## 当前目标

先做一版能稳定演出的“送别 -> 收回 -> 入睡”固定收尾场景。

## 固定版实现原则

- 先固定一个离场方向版本
- 再固定一条收回路径
- 不急着做动态 departureDirection

## 优先复用的板端脚本

- `four_servo_pose_delay_2_return_12_head_turn_once.py`
- `four_servo_pose_delay_2_return_12_head_turn.py`
- `sleep_motion.py`
- `sleep_motion_with_03_return.py`
- `servo_2_nod_1900_2200.py`

## 第一版推荐实现

1. 固定看向一个离场方向
2. 慢点头一次或两次
3. 稍停
4. 执行 `sleep_motion.py`
5. 必要时补 `sleep_motion_with_03_return.py`

## 为什么这个场景非常适合先做固定版

因为它本来就是链式场景：

- 告别
- 回收
- 入睡

这条链不依赖实时 tracking 也能成立。

## 当前固定版能证明什么

它能证明：

- Mira 的一轮互动有完整结尾
- 它不是突然停掉，而是有情绪地退场

## 后续升级方向

以后再补：

- `departureDirection`
- `lingerMs`
- `sleepDelayMs`
