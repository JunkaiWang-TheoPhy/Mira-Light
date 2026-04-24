# Latest Board Diff 2026-04-25

这份文档记录 `2026-04-25` 重新连上端侧后，与本地已拉回快照相比的差异。

## 比对结果

- 已拉回的文件中：
  - `39` 个未变化
  - `0` 个被改写
  - `0` 个在远端消失
- 远端新增：
  - `7` 个新的舵机动作脚本

## 新增文件

- `four_servo_pose_2048_2048_2048_2780_separate.py`
- `servo_12_slow_to_1800_2750.py`
- `servo_1_2_dodge_1848_1808.py`
- `servo_1_2_lean_forward_2148_1848.py`
- `servo_1_3_slow_1800_2750.py`
- `servo_2_nod_1900_2200.py`
- `servo_3_shake_2100_2000.py`

## 这 7 个新增文件为什么重要

因为它们把端侧动作能力从“少量大动作脚本”推进到了：

- 分离姿态脚本
- 小幅闪避脚本
- 前倾脚本
- 点头脚本
- 摇头脚本

也就是说，深圳版后续开发不再只有“大 scene 种子”，而是开始具备：

> 微动作级别的积木。

## 对开发判断的直接影响

### 被显著增强的场景

- `sz_cautious_intro`
- `sz_hand_boundary`
- `sz_voice_affect_response`
- `sz_multi_guest_choice`

### 仍然偏弱的场景

- `sz_hand_nuzzle`
- `sz_tabletop_follow`

## 一句话总结

这次差异不是“旧文件被改乱了”，而是：

> 端侧新增了 7 个小而关键的动作脚本，使深圳版后续编排空间明显变大。
