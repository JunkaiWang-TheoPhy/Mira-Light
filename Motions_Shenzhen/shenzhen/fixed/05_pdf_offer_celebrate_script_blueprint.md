# `副本 PDF 第 5 条：庆祝模式` 具体脚本蓝图

这份文档专门对应下面这组材料：

- `docs/Shenzhen/Videos/05_20260425_043828_01.mp4`
- `docs/Shenzhen/Videos/Mira Light 展位交互方案 副本.pdf`

注意：

当前这个 `副本.pdf` 的第 `5` 条是：

- `模拟拿到 offer 了：跳舞模式`

它和 `Motions_Shenzhen` 当前主线里的：

- `05_sz_standup_nudge_fixed.md`

不是同一件事。

所以这里单独落一份参考蓝图，而**不覆盖**当前主线编号。

## 参考依据

### 视频

- `05_20260425_043828_01.mp4`

这段视频时长约 `47.8s`，说明它不是一句话反馈，而是一段比较完整的庆祝型演示。

从节奏上看，它更像：

- 情绪拉高
- 左右 / 上下摇摆
- 灯效爆发
- 最后回收

### PDF 第 5 条

副本 PDF 第 `9~12` 页说明了这个场景的核心：

1. 收到好消息
2. 很开心
3. 音乐响起
4. 先往上摇
5. 再往下摇
6. 灯光五颜六色，像 disco 球
7. 最后慢慢减速
8. 回到正常姿态
9. 左右摇头、身体转一下，像跳完舞喘口气

所以这个场景最重要的不是“动作多”，而是：

- 起
- 爆发
- 收

三层对比要清楚。

## 当前版本的总体策略

第一版不要接：

- 真实 offer 事件
- 实时节拍同步
- 复杂外部触发链

第一版应该先做：

- 固定庆祝脚本
- 固定彩灯模式
- 固定减速收尾

也就是：

```text
sz_offer_celebrate_fixed.py
```

## 推荐动作分段

建议拆成 **6 段**。

### 第 0 段：正常位预备

目标：

- 从一个精神的正常姿态进入
- 不从睡姿起步

这一步很短，只是让后面的“冲起来”更自然。

## 第 1 段：收到好消息，先抬起来

目标：

- 情绪先往上提
- 身体整体抬高
- 灯头也往上

板端可借种子：

- `servo_12_slow_to_1800_2750.py`
- `four_servo_pose_2048_2048_2048_2780_separate.py`

灯光建议同步切到较亮彩色，例如：

```bash
python3 /home/sunrise/Desktop/send_uart3_led_cmd.py rainbow 180
```

## 第 2 段：上摇左 / 上摇右

目标：

- 做出“开心地往上摇”的感觉
- 左上、回中、右上、回中

板端可借种子：

- `servo_1_3_slow_1800_2750.py`
- `servo_2_nod_1900_2200.py`

## 第 3 段：下摇左 / 下摇右

目标：

- 和上摇形成对比
- 像顺着音乐把重心往下压再回弹

板端可借种子：

- `servo_2_nod_1900_2200.py`
- `servo_3_shake_2100_2000.py`

这一段不能做成“塌下来”，而应该做成“仍然兴奋但更低位”的摇摆。

## 第 4 段：彩色庆祝爆发

目标：

- 进入最明显的庆祝状态
- 灯光承担很大一部分情绪表达

第一版最直接的灯头命令建议：

```bash
python3 /home/sunrise/Desktop/send_uart3_led_cmd.py spin
```

如果想更稳，也可以：

```bash
python3 /home/sunrise/Desktop/send_uart3_led_cmd.py rainbow 200
```

但 `spin` 更接近 PDF 里“disco 球”的意思。

## 第 5 段：慢慢减速

目标：

- 不能突然停
- 要让人看出来“快乐慢慢收回来”

建议动作：

1. 灯光亮度下降
2. 动作幅度减小
3. 回到 normal-ish pose

这一步是这个场景最重要的收束点。

## 第 6 段：喘口气收尾

目标：

- 像刚跳完舞
- 还留一点余韵

建议只保留两个小动作：

- 左右摇一下头
- 或轻微转一下身体再回正

板端可借：

- `servo_3_shake_2100_2000.py`
- `servo_2_nod_1900_2200.py`

## 第一版脚本结构建议

建议结构：

```python
def enter_celebrate_ready():
    ...

def rise_with_excited_light():
    ...

def sway_up_left_right():
    ...

def sway_down_left_right():
    ...

def disco_burst():
    ...

def decelerate_to_neutral():
    ...

def breath_out_finish():
    ...

def main():
    enter_celebrate_ready()
    rise_with_excited_light()
    sway_up_left_right()
    sway_down_left_right()
    disco_burst()
    decelerate_to_neutral()
    breath_out_finish()
```

## 一条能先拼出来的近似命令序列

如果第一版只想快速试演，可以先按这个思路拼：

```bash
python3 /home/sunrise/Desktop/send_uart3_led_cmd.py rainbow 180
python3 /home/sunrise/Desktop/servo_12_slow_to_1800_2750.py
python3 /home/sunrise/Desktop/servo_1_3_slow_1800_2750.py
python3 /home/sunrise/Desktop/servo_2_nod_1900_2200.py --cycles 1
python3 /home/sunrise/Desktop/servo_3_shake_2100_2000.py --cycles 1
python3 /home/sunrise/Desktop/send_uart3_led_cmd.py spin
python3 /home/sunrise/Desktop/servo_2_nod_1900_2200.py --cycles 1
python3 /home/sunrise/Desktop/four_servo_control.py pose 2048 2150 2048 2130 --speeds 200 100 100 200
python3 /home/sunrise/Desktop/send_uart3_led_cmd.py all 255 220 180 100
```

## 当前固定版能证明什么

它能证明：

- Mira 能表达“特别开心”
- 机械动作和灯光可以一起形成情绪高潮
- 这条场景有明显的起伏与收尾

它还不能证明：

- 已经和真实电脑事件联动
- 音乐和动作严格同步
- 会根据事件强弱自动调整幅度

## 第二版再做什么

等第一版固定庆祝版稳定后，再升级：

1. offer 事件触发
2. 音乐节拍点同步
3. 灯光模式和动作段落自动对齐

## 一句话总结

按 `Videos/05` 和这个 PDF 副本里的第 5 条来设计，第一版最正确的做法是：

> 先做一条固定的庆祝脚本：抬起进入高位 -> 上下左右摇 -> 彩灯爆发 -> 慢慢减速 -> 摇头喘口气回正。
