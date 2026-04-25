# `sz_farewell_sleep` 送别段具体脚本蓝图

这份文档是在 [10_sz_farewell_sleep_fixed.md](./10_sz_farewell_sleep_fixed.md) 的基础上，再往前推进一层。

它专门回答：

> 如果基于 `06_20260425_043829_01.mp4` 和 `Mira Light 展位交互方案 副本.pdf` 第 6 条来写第一版脚本，应该怎样具体拆动作。

## 参考依据

### 视频

- `docs/Shenzhen/Videos/06_20260425_043829_01.mp4`

这段视频时长约 `17s`，说明它不是长剧情，而是一条短而明确的情绪收尾片段。

视频节奏给人的感觉是：

- 先把注意力送过去
- 再做一个礼貌但可爱的 goodbye 动作
- 再把情绪收下来

### PDF 第 6 条

副本 PDF 第 `12~13` 页写得很明确：

1. 评委准备离开
2. Mira 跟着评委移动方向转过去，像在目送
3. 评委挥手说再见
4. Mira 用灯头做“挥手”的动作
5. 慢慢点头两下
6. 灯头微微低下来，像有点舍不得
7. 又抬头看了一眼
8. 然后才睡觉

这说明这条 scene 的本质是：

> 先送别，再不舍得，最后才进入睡觉链。

## 当前版本的总体策略

第一版先只把“送别段”做稳，不急着把后半段 `sleep` 完全绑死。

也就是说，虽然挂在 `sz_farewell_sleep` 名下，但脚本上要分清：

- 第 6 条：farewell 段
- 第 7 条：sleep 段

第一版先让 farewell 段本身成立。

## 推荐脚本名

如果单独落成脚本，建议：

```text
sz_farewell_fixed.py
```

如果继续挂在主线命名里，则未来可以对应：

```text
scripts/scenes_shenzhen.py -> sz_farewell_sleep
```

但 scene 内部要保留：

- farewell_phase
- sleep_phase

两个阶段的清晰边界。

## 推荐动作分段

建议先拆成 **5 段**。

### 第 0 段：中性等待位

目标：

- 所有送别动作都从一个平静、自然的工作位开始

建议起点：

- `four_servo_control.py pose 2048 2150 2048 2130`

## 第 1 段：看向离场方向

目标：

- 清楚表达“我在目送你”
- 第一版先固定一个离场方向版本

建议：

- 先做固定右前方版
- 第二版再扩成左右分支

板端可借：

- `servo_1_3_slow_1800_2750.py`

建议时长：

- `0.8s ~ 1.2s`

## 第 2 段：慢点头两下，像挥手

目标：

- 不是大幅度 nod
- 而是“像摆手一样的礼貌 goodbye”

板端可借：

- `servo_2_nod_1900_2200.py`

第一版建议：

- `cycles=2`
- 每拍之间稍微停顿

这一步是整条送别 scene 的识别点。

## 第 3 段：微微低头，不舍得

目标：

- 从“礼貌告别”转成“有点舍不得”

要求：

- 幅度小
- 速度慢
- 明显比点头更柔和

建议做法：

- 进入一个固定的轻低头 pose
- 停 `0.6s ~ 1.0s`

## 第 4 段：再抬头看一眼

目标：

- 保留 PDF 里最值钱的小细节
- 让这条 scene 变得像活物，不像单纯礼貌动作

做法：

- 从低头位抬回一点
- 再看一眼离场方向
- 停半拍

这一步不要太大，否则会像重新开始一条场景。

## 第 5 段：进入收尾等待位

目标：

- 先停在一个柔和 farewell pose
- 不要在这一拍就直接折叠进 sleep

原因：

- 第 6 条和第 7 条应先在设计上分层
- 这样后续组合成 chain scene 时会更清楚

## 第一版最推荐的命令拼装顺序

如果你先不写完整脚本，只想做一版近似演示，可以这样拼：

```bash
python3 /home/sunrise/Desktop/four_servo_control.py pose 2048 2150 2048 2130 --speeds 200 100 100 200
python3 /home/sunrise/Desktop/servo_1_3_slow_1800_2750.py --speed 100
python3 /home/sunrise/Desktop/servo_2_nod_1900_2200.py --cycles 2 --pause 0.08
python3 /home/sunrise/Desktop/four_servo_control.py pose 2048 2050 2048 2200 --speeds 160 80 80 160
python3 /home/sunrise/Desktop/four_servo_control.py pose 2048 2120 2048 2160 --speeds 140 80 80 140
python3 /home/sunrise/Desktop/send_uart3_led_cmd.py all 255 220 180 90
```

这条近似版表达的是：

- 正常位
- 看过去
- 点头两次
- 低下来
- 再看一眼
- 留在一个柔和送别位

## 第一版脚本结构建议

建议写成：

```python
def enter_neutral():
    ...

def look_to_departure_side():
    ...

def nod_goodbye_twice():
    ...

def lower_head_reluctantly():
    ...

def look_back_once():
    ...

def settle_farewell_pose():
    ...

def main():
    enter_neutral()
    look_to_departure_side()
    nod_goodbye_twice()
    lower_head_reluctantly()
    look_back_once()
    settle_farewell_pose()
```

## 当前固定版能证明什么

它能证明：

- Mira 会目送人离开
- 它会做一个明显可理解的 goodbye
- 它的收尾带着一点不舍得

它还不能证明：

- 已经在实时判断离场方向
- 已经和 `sleep` 完整链起来

## 第二版再做什么

第二版再补：

1. `departureDirection`
2. farewell -> sleep 的自动串联
3. `lingerMs`
4. `sleepDelayMs`

## 一句话总结

按 `Videos/06` 和这个 PDF 副本里的第 6 条来设计，第一版最正确的做法是：

> 先做一条固定送别脚本：看向离场方向 -> 慢点头两下 -> 微微低头 -> 再看一眼 -> 落到柔和送别位。
