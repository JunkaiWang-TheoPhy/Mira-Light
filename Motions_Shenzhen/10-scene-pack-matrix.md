# Shenzhen Scene Pack Matrix

这份文档把深圳版 10 个交互先压成一张总表，方便在进入单场景规格书之前快速建立全局认识。

## 10 个交互总表

| 场景 | sceneId | 核心证明 | scene_mode | 主 context |
| --- | --- | --- | --- | --- |
| 1 | `sz_presence_wake` | 它感知到“有人来了” | `hybrid` | `targetDirection`, `presenceConfidence`, `engagementZone`, `wakeReason` |
| 2 | `sz_cautious_intro` | 它在认人，而不是机械转头 | `dynamic_builder` | `targetDirection`, `targetDistanceBand`, `ownerFaceFound`, `judgeDirection` |
| 3 | `sz_hand_nuzzle` | 它会主动亲近人的手 | `dynamic_builder` | `touchSide`, `handDistanceBand`, `handSpeedBand`, `touchDetected` |
| 4 | `sz_hand_boundary` | 它有边界感，不是无条件迎合 | `dynamic_builder` | `approachSide`, `approachSpeedBand`, `threatLevel`, `recoveryAllowed` |
| 5 | `sz_standup_nudge` | 它会可爱地提醒你动一动 | `chain_scene` | `reminderLevel`, `responseState`, `targetDirection` |
| 6 | `sz_tabletop_follow` | 它真的看见并跟随桌上目标 | `hybrid` | `targetId`, `targetClass`, `horizontalZone`, `distanceBand`, `lockStrength` |
| 7 | `sz_sigh_comfort` | 它感知到你的疲惫和叹气 | `event_scene` | `transcript`, `sighStrength`, `speakerDirection` |
| 8 | `sz_voice_affect_response` | 它对不同语义/情绪输入有不同反应 | `event_scene` | `transcript`, `intent`, `valence`, `speakerDirection` |
| 9 | `sz_multi_guest_choice` | 它会在两个人之间犹豫并作选择 | `dynamic_builder` | `primaryDirection`, `secondaryDirection`, `selectionReason`, `confidence` |
| 10 | `sz_farewell_sleep` | 它能完成目送到入睡的完整收尾 | `chain_scene` | `departureDirection`, `lingerMs`, `sleepDelayMs`, `guestId` |

## 为什么不用现有 release 的 10 主场景直接照搬

因为深圳现场更需要的是“感知可信度”，不是“动作数量”。

所以这套 scene pack 有三条硬原则：

1. 一级按钮优先证明“看见你、理解你、对你有反应”
2. filler 型表达场景不占一级主按钮
3. 所有按钮都应能被主持人口播一句话解释清楚

## 哪些旧场景被吸收了

### 被重写进新包的

- `wake_up` -> `sz_presence_wake`
- `curious_observe` -> `sz_cautious_intro`
- `touch_affection` -> `sz_hand_nuzzle`
- `standup_reminder` -> `sz_standup_nudge`
- `track_target` -> `sz_tabletop_follow`
- `farewell` + `sleep` -> `sz_farewell_sleep`

### 被升级为“感知主证据”的

- `sigh_demo` -> `sz_sigh_comfort`
- `voice_demo_tired`、`praise_demo`、`criticism_demo` -> `sz_voice_affect_response`
- `multi_person_demo` -> `sz_multi_guest_choice`
- `hand_avoid` -> `sz_hand_boundary`

### 刻意不放入一级主包的

- `cute_probe`
- `daydream`
- `celebrate`

原因：

- 它们可以继续存在
- 但更适合作为次级展示或过渡镜头
- 不应挤占深圳主包的一级证明位

## 设计上的真正差别

Shenzhen pack 和默认 pack 最大的区别，不是“动作更复杂”，而是：

- 每个场景的 `demo_goal` 更明确
- 每个场景更依赖上下文和输入证据
- 主控台要能传入 `context`
- runtime 需要更多 builder，而不是只靠静态 scene

## 下一步实现顺序

如果按工程推进顺序，建议这样做：

1. 先确认这 10 个 `sceneId`
2. 再新增 `scripts/scenes_shenzhen.py`
3. 再补 Shenzhen builder 到 runtime
4. 再新增 `Motions_Shenzhen/*/scene_script.py`
5. 最后做主控台 scene set 切换

不要反过来先堆 motion script。

## 一句话总结

这 10 个场景不是“深圳版更花哨的动作包”，而是：

> 一套围绕感知证明、情绪证明和社交闭环重排后的主按钮系统。
