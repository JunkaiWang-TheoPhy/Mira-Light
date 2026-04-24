# Shenzhen Scenes vs Board Seeds

这份文档只回答一个最实际的问题：

> 按最新端侧文件状态看，深圳版 10 个交互分别已经有哪些板端种子，还缺什么。

它和 `10-scene-pack-matrix.md` 的区别是：

- `10-scene-pack-matrix.md` 讲产品目标
- 本文档讲端侧可复用现实

## 最新端侧状态

基于 `2026-04-25` 重新从开发板 `/home/sunrise` 拉取并比对后的结果：

- 昨天已拉回的文件中：`39` 个未变化
- 没有发现已拉回文件被改写
- 端侧新增了 `7` 个动作脚本：
  - `four_servo_pose_2048_2048_2048_2780_separate.py`
  - `servo_12_slow_to_1800_2750.py`
  - `servo_1_2_dodge_1848_1808.py`
  - `servo_1_2_lean_forward_2148_1848.py`
  - `servo_1_3_slow_1800_2750.py`
  - `servo_2_nod_1900_2200.py`
  - `servo_3_shake_2100_2000.py`

这些新增脚本会直接影响深圳版 10 个交互的可实现性判断。

## 10 个交互和板端种子对照

| sceneId | 板端种子强度 | 当前可复用的端侧脚本 | 当前主要缺口 |
| --- | --- | --- | --- |
| `sz_presence_wake` | 强 | `four_servo_pose_delay_2.py`、`four_servo_pose_2048_2048_2048_2780_separate.py`、`servo_12_slow_to_1800_2750.py`、灯头 `WAKE` | 还缺一个正式整合成深圳按钮的 script |
| `sz_cautious_intro` | 中强 | `servo_1_2_lean_forward_2148_1848.py`、`servo_1_2_dodge_1848_1808.py`、`servo_2_nod_1900_2200.py`、`servo_3_shake_2100_2000.py` | 还缺完整“试探 -> 害羞 -> 回看”链 |
| `sz_hand_nuzzle` | 弱 | `servo_1_2_lean_forward_2148_1848.py`、灯头暖光命令 | 没有直接“蹭手”脚本 |
| `sz_hand_boundary` | 中 | `servo_1_2_dodge_1848_1808.py` | 还缺按来手方向和威胁级别分支 |
| `sz_standup_nudge` | 中 | `servo_1_2_lean_forward_2148_1848.py`、`servo_2_nod_1900_2200.py`、`servo_3_shake_2100_2000.py` | 没有现成“三次蹭蹭”脚本 |
| `sz_tabletop_follow` | 弱 | `cam_preview.py`、`cam_sender.py`、`rtsp_server.py`、若干舵机控制脚本 | 没有视觉闭环到关节更新的板端脚本 |
| `sz_sigh_comfort` | 中 | 灯头 `BREATHE` / `BRI` / `WAKE`，加 `servo_2_nod_1900_2200.py` 小幅低头 | 没有完整“叹气安慰”组合脚本 |
| `sz_voice_affect_response` | 中 | `servo_2_nod_1900_2200.py`、`servo_3_shake_2100_2000.py`、`servo_1_2_dodge_1848_1808.py`、灯头命令 | 没有统一分支封装 |
| `sz_multi_guest_choice` | 中 | `servo_3_shake_2100_2000.py`、现有 head turn 脚本 | 没有完整“双目标犹豫”脚本 |
| `sz_farewell_sleep` | 强 | `four_servo_pose_delay_2_return_12_head_turn_once.py`、`four_servo_pose_delay_2_return_12_head_turn.py`、`sleep_motion.py`、`sleep_motion_with_03_return.py` | 还缺正式链式封装 |

## 每个场景更具体的开发判断

### `sz_presence_wake`

现在已经不需要从零想“抬起来”怎么做了。

可以直接围绕：

- 缓慢抬起
- 高位稳定
- 头部轻微定向
- 灯头 `WAKE`

来拼一版深圳开场。

### `sz_cautious_intro`

这是这次比对后变化最大的场景之一。

之前它主要只有旧 head-turn 类脚本可借，现在端侧新增了：

- 前倾
- 躲闪
- 点头
- 摇头

所以它已经具备了做成完整“试探认人”的可能性，不再只是概念场景。

### `sz_hand_nuzzle`

它依然是弱种子场景。

虽然现在有了 `lean_forward`，但这只解决“靠近”问题，没有解决：

- 小幅 rub
- 手离开后追一下

所以它依然是高优先级补写项。

### `sz_hand_boundary`

这次更新后，它不再是完全没有板端种子。

`servo_1_2_dodge_1848_1808.py` 已经是一个明确的躲避脚本，因此深圳版只需要在其上增加：

- 左右方向化
- threat level
- 恢复阶段

### `sz_standup_nudge`

现在已经有条件用：

- 前倾
- 点头
- 轻摇

拼出提醒型动作。

缺的主要不是姿态，而是“三次蹭蹭”的节奏封装。

### `sz_tabletop_follow`

它依然是最弱的主场景之一。

端侧目前有：

- 摄像头预览
- HTTP 发图
- RTSP

但没有“视觉事件 -> 板端舵机持续更新”的真闭环脚本。

### `sz_sigh_comfort`

现在中等可做。

因为灯头端已经能稳定做：

- 暖光
- 呼吸

机械端又新增了慢点头脚本，可以支持轻度低头与安慰表达。

### `sz_voice_affect_response`

这次明显更好做了。

因为：

- `nod` 有种子
- `shake` 有种子
- `dodge` 有种子
- LED 侧也有多种情绪灯效

所以这个场景已经不需要从零写动作，只是需要统一分支调度。

### `sz_multi_guest_choice`

它还是没有现成完整脚本，但比之前强。

因为“左右摇摆”和“最终停住”所需的小动作已经有种子了。

### `sz_farewell_sleep`

仍然是强种子场景。

而且现在有更多微动作种子可借：

- 点头
- 摇头
- 慢速双关节调整

所以深圳版收尾的质感可以做得比之前更细。

## 对后续开发的直接指导

如果按端侧现实来排优先级，建议这样分：

### 先做整合封装

- `sz_presence_wake`
- `sz_farewell_sleep`
- `sz_voice_affect_response`

### 再做中层编排

- `sz_cautious_intro`
- `sz_hand_boundary`
- `sz_standup_nudge`
- `sz_sigh_comfort`
- `sz_multi_guest_choice`

### 最后做真正缺大块能力的

- `sz_hand_nuzzle`
- `sz_tabletop_follow`

## 一句话总结

按最新端侧状态看，深圳版 10 个交互里：

- 不再只有 2 个强种子场景
- `cautious_intro`、`hand_boundary`、`voice_affect_response` 的可实现性都明显提升了
- 真正还明显缺大块能力的，主要只剩 `hand_nuzzle` 和 `tabletop_follow`
