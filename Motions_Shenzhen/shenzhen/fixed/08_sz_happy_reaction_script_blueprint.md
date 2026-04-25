# `sz_happy_reaction` 具体脚本蓝图

这份文档挂在 [08_sz_voice_affect_response_fixed.md](./08_sz_voice_affect_response_fixed.md) 之下，作为其中 `praise / positive` 子分支的强化说明。

它专门回答：

> 如果基于 `08_20260425_043832_01.mp4` 和 `Mira Light 展位交互方案 副本.pdf` 后半段的“开心”来写第一版脚本，应该怎样具体拆动作。

## 参考依据

### 视频

- `docs/Shenzhen/Videos/08_20260425_043832_01.mp4`

这段视频时长约 `39.6s`，更像一条短情绪表达，而不是长剧情动作。

从视频节奏看，它强调的是：

- 抬头向上
- 左右轻浮动
- 一点弹性和伸缩
- 然后回到等待位

### PDF 后半段“开心”

副本 PDF 第 `18` 页写的是：

1. 往上面看
2. 左右浮动
3. 同时轻微伸缩

所以这条的本质不是“狂喜庆祝”，而是：

> 一个轻、活、上扬的正向情绪反应。

## 当前版本的总体策略

第一版先做 **固定微情绪脚本**。

不要直接把它做成：

- `offer celebrate`
- 强灯效爆发
- 大幅摆动

它更适合作为：

- `voice_affect_response` 中 `praise` 分支的正向表达

## 推荐脚本名

如果独立落成脚本，建议：

```text
sz_happy_reaction_fixed.py
```

如果继续挂在主线里，则未来可作为：

- `sz_voice_affect_response` 的 `praise` 强化版

## 推荐动作分段

建议拆成 **5 段**。

### 第 0 段：中性等待位

目标：

- 从平静工作位开始
- 给“开心”创造对比

建议起点：

```bash
python3 /home/sunrise/Desktop/four_servo_control.py pose 2048 2150 2048 2130 --speeds 200 100 100 200
```

## 第 1 段：抬头向上看

目标：

- “开心”的第一拍是上扬
- 不是左右摆

可借板端种子：

- `servo_12_slow_to_1800_2750.py`
- `four_servo_pose_2048_2048_2048_2780_separate.py`

建议时长：

- `0.6s ~ 1.0s`

## 第 2 段：左右轻浮动

目标：

- 不要做成拒绝式摇头
- 而是“高兴地左右晃一下”

可借板端种子：

- `servo_3_shake_2100_2000.py`

但第一版建议只做一轮小幅轻摆，不要大幅多轮。

## 第 3 段：轻微伸缩

目标：

- 给动作增加“弹性”
- 让开心不只是头在摆

可借板端种子：

- `servo_1_2_lean_forward_2148_1848.py`

但这里不要把它用成“靠过去”，而应把它理解为：

- 身体轻轻弹一下

## 第 4 段：暖亮一点

目标：

- 灯光配合“开心”
- 但不要像 disco 爆发

第一版建议：

```bash
python3 /home/sunrise/Desktop/send_uart3_led_cmd.py all 255 220 180 150
```

如果想更活一点，也可以：

```bash
python3 /home/sunrise/Desktop/send_uart3_led_cmd.py rainbow 150
```

但暖亮通常更适合“开心”而不是“庆祝”。

## 第 5 段：回到等待位

目标：

- 情绪表达完后，平滑回到中性
- 不能突然停死

建议：

```bash
python3 /home/sunrise/Desktop/four_servo_control.py pose 2048 2150 2048 2130 --speeds 180 100 100 180
python3 /home/sunrise/Desktop/send_uart3_led_cmd.py all 255 220 180 100
```

## 一条能先拼出来的近似命令序列

```bash
python3 /home/sunrise/Desktop/four_servo_control.py pose 2048 2150 2048 2130 --speeds 200 100 100 200
python3 /home/sunrise/Desktop/send_uart3_led_cmd.py all 255 220 180 140
python3 /home/sunrise/Desktop/servo_12_slow_to_1800_2750.py
python3 /home/sunrise/Desktop/servo_3_shake_2100_2000.py --cycles 1 --pause 0.06
python3 /home/sunrise/Desktop/servo_1_2_lean_forward_2148_1848.py
python3 /home/sunrise/Desktop/four_servo_control.py pose 2048 2150 2048 2130 --speeds 180 100 100 180
python3 /home/sunrise/Desktop/send_uart3_led_cmd.py all 255 220 180 100
```

## 当前固定版能证明什么

它能证明：

- Mira 会有轻量正向情绪反应
- 身体和灯光都会一起“变开心”
- 这可以作为主秀里的短反馈插入

它还不能证明：

- Mira 已经理解了具体夸奖内容
- 会根据开心程度自动调整幅度

## 第二版再做什么

第二版再补：

1. 直接挂到 `praise` 意图上
2. 根据 `valence` 强弱调整幅度
3. 让灯光和动作幅度联动

## 一句话总结

按 `Videos/08` 和副本 PDF 里的“开心”来设计，第一版最正确的做法是：

> 先做一条固定微情绪脚本：抬头向上看 -> 左右轻浮动 -> 轻微伸缩 -> 灯光变得更暖更亮 -> 回到等待位。
