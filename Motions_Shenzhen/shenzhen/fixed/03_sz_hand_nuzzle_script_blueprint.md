# `sz_hand_nuzzle` 具体脚本蓝图

这份文档是在 [03_sz_hand_nuzzle_fixed.md](./03_sz_hand_nuzzle_fixed.md) 的基础上，再往前推进一层。

它专门回答：

> 如果基于 `03_20260425_043824_01.mp4` 和 `Mira Light 展位交互方案 副本.pdf` 第 3 条来写第一版脚本，应该怎样具体拆动作。

## 参考依据

### 视频

- `docs/Shenzhen/Videos/03_20260425_043824_01.mp4`

这段视频时长约 `55.3s`，比第二条短，说明它更像：

- 一段聚焦型近距离互动
- 而不是长链条剧情动作

从视频和抽帧能读出来的重点是：

1. 主体动作幅度不大
2. 重点是靠近后保持亲密距离
3. “蹭”的感觉来自小动作，不是大位移
4. 手拿开后的“追一下”很短

### PDF 第 3 条

根据 `Mira Light 展位交互方案 副本.pdf` 第 `6~8` 页，第 3 条“摸一摸”的关键点是：

1. 评委把手伸向灯头
2. Mira 靠过去蹭评委的手
3. 灯头在手掌下小幅上下、左右摆动
4. 灯光变成最暖色温
5. 身子往下走，再蹭
6. 手拿开后追一下
7. 手回来后，等在自然照明方向

这说明第三条的关键不在“看见手”，而在：

> Mira 主动进入一种亲近、贴近、柔软的身体状态。

## 当前版本的总体策略

第一版先做 **固定方向版**，不要急着接手部实时检测。

原因：

- 当前板端还没有真正稳定的“追手 / rub / 离手再跟一下”闭环
- 但“靠近 + 暖光 + 小幅蹭动”已经足够演出第一版的亲密感

所以第一版建议：

- 固定一个“手从右前方伸来”的版本
- 先用固定动作做出亲近感

## 推荐脚本名

建议脚本名直接叫：

```text
sz_hand_nuzzle_fixed.py
```

如果先只落到 repo 的 scene 层，则未来可对应：

```text
scripts/scenes_shenzhen.py -> sz_hand_nuzzle
```

## 推荐动作分段

建议拆成 **6 段**。

### 第 0 段：中性等待位

目标：

- 从平静工作位开始
- 不从睡姿起步

要求：

- 这是一条“互动中的亲近”动作
- 不是开场动作

建议起点：

- `normal_pose`
- 或轻微面向观众的等待位

## 第 1 段：暖灯预热

目标：

- 先让观众感到它愿意亲近
- 机械臂还未明显动作前，气氛已经变暖

推荐命令：

```bash
python3 /home/sunrise/Desktop/send_uart3_led_cmd.py all 255 190 120 120
```

如果想更柔一点，也可以：

```bash
python3 /home/sunrise/Desktop/send_uart3_led_cmd.py breathe 255 190 120 120
```

但第一版建议先用 `all`，更稳，更容易复现。

建议时长：

- `0.4s ~ 0.8s`

## 第 2 段：主动靠近手

目标：

- 明确表达“不是被摸，而是主动靠近”

第一版最适合直接借：

- `servo_1_2_lean_forward_2148_1848.py`

这条板端脚本本身就很像“试探性前倾 / 靠近”。

建议时长：

- `0.8s ~ 1.2s`

## 第 3 段：钻到掌下

目标：

- 从“靠近”变成“贴到手掌下面”
- 这是第三条和第二条最大的区别

实现上不要大幅移动。

第一版建议：

- 在前倾之后，再补一个更低一点的姿态
- 重点是低一点、近一点，而不是再往前冲很多

板端可参考：

- 继续复用 `servo_1_2_lean_forward_2148_1848.py` 的姿态思路
- 或在未来 scene 里单独定义一个 `under_palm_pose`

建议时长：

- `0.5s ~ 0.8s`

## 第 4 段：小幅蹭动

目标：

- 这是整条 scene 的核心
- 必须小、密、柔
- 不能像摇头，也不能像点头过大

板端可以借的微动作思路：

- `servo_2_nod_1900_2200.py`
- `servo_3_shake_2100_2000.py`

但第一版不要原样整段调用。

更推荐的做法是：

- 取它们的“慢、小、单轮”思路
- 在上层脚本里做一个 `micro_nuzzle_loop()`

建议形态：

1. 一次小幅上下轻压 / 回弹
2. 一次小幅左右轻摆 / 回正
3. 再重复 1 轮

建议总时长：

- `0.8s ~ 1.2s`

## 第 5 段：手拿开后追一下

目标：

- 表达“还想再贴一下”
- 但不能变成第二次完整前探

第一版建议：

- 只再靠近一点点
- 停 `0.2s ~ 0.4s`
- 然后马上准备回等待位

这一步不要做成动态追踪。

它现在更适合：

- 用一个固定的小位移占位

## 第 6 段：回到自然照明方向

目标：

- 姿态退回到中性
- 灯光从“最暖亲近”退回“自然暖白”

推荐命令：

```bash
python3 /home/sunrise/Desktop/send_uart3_led_cmd.py all 255 220 180 100
```

姿态建议：

- 回到 normal-ish pose
- 不要突然抽离

建议时长：

- `0.6s ~ 1.0s`

## 第一版最推荐的命令拼装顺序

如果你现在先不写完整 Python，而只是做一条“可演示近似版”，可以按这个顺序拼：

```bash
python3 /home/sunrise/Desktop/send_uart3_led_cmd.py all 255 190 120 120
python3 /home/sunrise/Desktop/servo_1_2_lean_forward_2148_1848.py
python3 /home/sunrise/Desktop/servo_2_nod_1900_2200.py --cycles 1 --pause 0.05
python3 /home/sunrise/Desktop/servo_3_shake_2100_2000.py --cycles 1 --pause 0.05
python3 /home/sunrise/Desktop/servo_2_nod_1900_2200.py --cycles 1 --pause 0.05
python3 /home/sunrise/Desktop/four_servo_control.py pose 2048 2150 2048 2130 --speeds 200 100 100 200
python3 /home/sunrise/Desktop/send_uart3_led_cmd.py all 255 220 180 100
```

这还不是最终真值，但已经能比较像：

- 靠近
- 钻到掌下
- 蹭两下
- 回等待位

## 第一版脚本结构建议

建议写成这种结构：

```python
def warm_ready_light():
    ...

def lean_forward_soft():
    ...

def dip_under_palm():
    ...

def micro_nuzzle_loop():
    ...

def follow_once():
    ...

def settle_to_waiting_pose():
    ...

def main():
    warm_ready_light()
    lean_forward_soft()
    dip_under_palm()
    micro_nuzzle_loop()
    follow_once()
    settle_to_waiting_pose()
```

## 当前固定版能证明什么

它能证明：

- Mira 会主动靠近
- Mira 会进入一种亲近、柔软的状态
- 灯光和机械动作会一起表达“舒服地蹭你”

它还不能证明：

- Mira 已经真的实时识别到手的位置
- Mira 会按手拿开的真实方向追一下

## 第二版再做什么

等第一版固定版稳定后，再升级：

1. `touchSide`
2. `handDistanceBand`
3. `touchDetected`
4. 手离开方向的短追踪

## 一句话总结

第三条“摸一摸”的第一版正确写法不是“追踪手”，而是：

> 暖灯预热 -> 主动前倾 -> 钻到掌下 -> 小幅蹭动 -> 追一下 -> 回等待位。
