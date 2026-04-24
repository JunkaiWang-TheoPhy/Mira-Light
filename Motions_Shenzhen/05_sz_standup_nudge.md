# `sz_standup_nudge` 规格书

## 核心规格

- `sceneId`: `sz_standup_nudge`
- `demo_goal`: 证明 Mira 不只会表达情绪，还会以可爱、不冒犯的方式提醒人改变状态，比如久坐后起来活动。
- `scene_mode`: `chain_scene`
- `apiContextKeys`: `reminderLevel`, `responseState`, `targetDirection`
- `fallback_behavior`: 没有任何久坐来源时，由主持人口播建立情境，再手动触发固定“三次蹭蹭 + 双点头 + 轻摇头”版本。
- `operator_cue`: “你现在假装已经坐了一小时没动，Mira 不会警报，而会像宠物一样蹭蹭提醒你。”
- `success_signal`: 评委能看懂这是“提醒你起来”的动作，不会误解成攻击、故障或随机前冲。

## 这个场景为什么值得保留在深圳主包

虽然它不是最强的感知场景，但它证明的是：

> Mira 的价值不只在陪伴，还在会温柔地改变你的行为。

这很接近真实产品价值，而不是单纯表演。

## 推荐运行逻辑

### 主路径

1. 根据 `targetDirection` 对准评委
2. 做 2 到 3 次节奏分明的“埋头 -> 上顶 -> 后退”
3. 停一下
4. 清晰点两次头
5. 如果 `responseState=reject`，再轻轻摇一次头
6. 慢慢恢复中性位

### `responseState` 建议

- `unknown`
  - 只演提醒本体，不演后续反馈
- `accept`
  - 提醒后停稳，等待人起身
- `reject`
  - 轻轻摇头，然后收回

## 推荐 context 约定

- `reminderLevel`
  - `soft | medium | strong`
- `responseState`
  - `unknown | accept | reject`
- `targetDirection`
  - `left | center | right`

## 主控台接入建议

### 按钮文案

- 中文：`久坐提醒`
- 英文辅助：`Standup Nudge`

### 建议输入控件

- 提醒力度
- 用户反馈状态
- 目标方向

### 建议 step outline

- Turn toward the guest
- Nudge forward in three beats
- Nod twice to confirm
- Shake softly if refused
- Return to neutral

## 为什么它是 `chain_scene`

因为它不是一个单拍动作，而是一个很完整的小流程：

- 提醒
- 等待理解
- 对用户回应作出反应
- 恢复

如果只把它当成固定 choreography，会丢掉“沟通感”。

## 失败信号

- 蹭蹭动作太猛，像撞人
- 三次前顶没有节奏差异
- 点头和摇头的语义看不懂
- 没有主持人口播时，这个 scene 显得突然

## 落地建议

这个场景在深圳版里适合作为“产品价值证明型互动”。

它证明 Mira 不是只会可爱，而是会用一种可接受的方式影响人的行为。
