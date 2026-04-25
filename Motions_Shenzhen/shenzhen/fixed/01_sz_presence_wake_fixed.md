# `sz_presence_wake` 固定动作实现指导

## 当前目标

在没有稳定 presence detection 和实时方向输入的前提下，先做一版：

- 看起来像“感知到来人”
- 又不依赖实时视觉计算

的固定版开场。

## 配套蓝图

如果需要更具体到“每一段应该怎么落脚本”，继续看：

- [01_sz_presence_wake_script_blueprint.md](./01_sz_presence_wake_script_blueprint.md)

那份文档已经把：

- `Mira Light 展位交互方案 副本.pdf` 第一条
- `01_20260425_043820_01.mp4`

压成了一份可执行脚本设计。

## 固定版实现原则

- 先用灯光表达“醒来”
- 再用机械臂表达“抬起和注意力启动”
- 最后只选一个固定朝向，作为“看向来人”的占位版本

## 优先复用的板端脚本

- `send_uart3_led_cmd.py wake ...`
- `four_servo_pose_delay_2.py`
- `four_servo_pose_2048_2048_2048_2780_separate.py`
- `servo_12_slow_to_1800_2750.py`

## 第一版推荐实现

### 步骤 1：灯头先醒

先发：

```bash
python3 /home/sunrise/Desktop/send_uart3_led_cmd.py wake 255 220 180 150
```

它负责“先睁眼”。

### 步骤 2：身体抬起

再执行一条固定的抬起动作。

优先考虑：

```bash
python3 /home/sunrise/Desktop/four_servo_pose_delay_2.py
```

理由：

- 它已经是 staged motion
- 不会一下子全关节同时突兀启动

### 步骤 3：固定看向来人

在没有方向输入时，先约定一个默认朝向版本，例如：

- 面向正前
- 或略偏主持人常站的方向

如果要继续补一个固定高位姿态，可以尝试：

```bash
python3 /home/sunrise/Desktop/four_servo_pose_2048_2048_2048_2780_separate.py
```

## 当前不建议做的事

- 不要一上来就接 `targetDirection`
- 不要第一版就把“醒来”和“追踪来人”绑在一起
- 不要为了看起来像“智能唤醒”而强接不稳定视觉条件

## 当前固定版足够证明什么

它能证明：

- Mira 会从静止态醒来
- Mira 会经历一个分阶段的抬起过程
- Mira 的灯和身体是一起进入“苏醒状态”的

它还不能证明：

- Mira 真的知道人从哪边来
- Mira 会根据不同来人方向自动对准

## 后续升级方向

第二版再补：

- `targetDirection`
- `presenceConfidence`
- `engagementZone`

但第一版不要急着上。
