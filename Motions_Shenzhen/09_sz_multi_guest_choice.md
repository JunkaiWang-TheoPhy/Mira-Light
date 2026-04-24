# `sz_multi_guest_choice` 规格书

## 核心规格

- `sceneId`: `sz_multi_guest_choice`
- `demo_goal`: 证明当同时存在两位观众时，Mira 会短暂犹豫并做出选择，从而体现“活物感”和社交注意力。
- `scene_mode`: `dynamic_builder`
- `apiContextKeys`: `primaryDirection`, `secondaryDirection`, `selectionReason`, `confidence`
- `fallback_behavior`: 没有多人检测时，由导演台手动指定左右两位来宾方向，运行固定“左看 -> 右看 -> 回到主目标”的版本。
- `operator_cue`: “如果两个人同时在场，它不会像摄像头那样平均扫，而会像小动物一样先犹豫，再决定看谁。”
- `success_signal`: 现场观众能看懂它确实在两人之间犹豫过，并最终稳定选定一个对象，而不是机械来回摆头。

## 当前端侧种子

这个场景当前已经具备基本可做的材料：

- `servo_3_shake_2100_2000.py`
- 现有 head turn 系列脚本
- `servo_2_nod_1900_2200.py`

还缺的是“为什么最后选了谁”的逻辑，以及多目标输入到方向序列的调度。

## 为什么这个场景值得进 Shenzhen 主包

它不是最实用的产品功能，但它非常有“活物感”。

而且它很容易在现场引发笑声，因为观众会自然把“犹豫和选择”理解为一种性格。

## 推荐运行逻辑

1. 接收两个候选方向
2. 先看 `primaryDirection`
3. 再被 `secondaryDirection` 吸引过去
4. 停半拍，像在判断
5. 根据 `selectionReason` 和 `confidence` 最终回到主选对象

## `selectionReason` 建议

- `closer`
- `speaking`
- `owner_priority`
- `manual_director`

## 推荐 context 约定

- `primaryDirection`
  - 初始主候选方向
- `secondaryDirection`
  - 第二候选方向
- `selectionReason`
  - 为什么最后选中某一侧
- `confidence`
  - `0.0 ~ 1.0`

## 主控台接入建议

### 按钮文案

- 中文：`多人时选谁看`
- 英文辅助：`Multi Guest Choice`

### 建议输入控件

- 第一目标方向
- 第二目标方向
- 选择理由
- 选择置信度

### 建议 step outline

- Look at guest A
- Shift to guest B
- Pause in uncertainty
- Choose one side
- Settle attention there

## 为什么它必须是 `dynamic_builder`

因为这个场景的可信度来自“方向组合是真的”。

如果永远做成固定左-右-左，观众很快会看出它不是在当下做选择。

## 失败信号

- 左右切换速度太快，像监控扫描
- 没有停顿，观众感受不到“犹豫”
- 最终停留点不稳定
- 没有任何可解释的选择理由

## 落地建议

这不是深圳版最优先的技术场景，但它是非常值得保留的“人格化证明”。

它会让 Mira 更像一个在社交环境中有偏好的存在。
