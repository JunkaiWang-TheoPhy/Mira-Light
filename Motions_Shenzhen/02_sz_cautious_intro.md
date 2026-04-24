# `sz_cautious_intro` 规格书

## 核心规格

- `sceneId`: `sz_cautious_intro`
- `demo_goal`: 证明 Mira 在“认你”，而不是机械地把头转过来；它会先试探、再靠近、再害羞回避。
- `scene_mode`: `dynamic_builder`
- `apiContextKeys`: `targetDirection`, `targetDistanceBand`, `ownerFaceFound`, `judgeDirection`
- `fallback_behavior`: 如果没有可靠的人脸和方向输入，则退化成“固定半转 -> 害羞转开 -> 再探回来”的导演版。
- `operator_cue`: “它不会一上来就盯着你，而是会先试探一下，像在确认你是谁。”
- `success_signal`: 评委能看懂“靠近、停顿、害羞、再探回来”的心理变化，而且朝向与真实目标方向匹配。

## 这个场景为什么比默认 `curious_observe` 更重要

默认版 `curious_observe` 已经能演出“好奇”。

但深圳版需要额外证明两件事：

1. 它知道自己在看谁
2. 它会根据目标和主人的关系决定靠近还是回避

所以 Shenzhen 版不能只是一条固定 choreography，而必须是一个 builder。

## 场景的真正意图

这个交互的核心不是“歪头很可爱”，而是：

> Mira 对人有判断过程。

它应该表现出：

- 看见你
- 还不完全确定
- 想靠近一点
- 又有点害羞
- 但还是忍不住再看一眼

## 推荐运行逻辑

### 如果找到了主人的脸

优先按 `ownerFaceFound=true` 的路径：

1. 先扫描
2. 朝主人方向半转
3. 轻轻靠近
4. 做一次辨认式小摇头
5. 害羞转开
6. 再回看一眼

### 如果没有找到主人的脸

走 fallback 理解：

1. 先扫描
2. 以 `judgeDirection` 为参考，做一个安全的回退偏转
3. 停半拍
4. 回到中性等待位

## 推荐 context 约定

- `targetDirection`
  - 当前主要关注对象的方向
- `targetDistanceBand`
  - `near | mid | far`
- `ownerFaceFound`
  - `true | false`
- `judgeDirection`
  - 当前评委大致方位

## 主控台接入建议

### 按钮文案

- 中文：`试探认人`
- 英文辅助：`Cautious Intro`

### 建议输入控件

- 目标方向
- 距离带
- 是否识别到主人
- 评委方向

### 建议 step outline

- Scan for a face
- Half-turn toward the target
- Lean in to inspect
- Turn away shyly
- Peek back once

## 为什么它必须是 `dynamic_builder`

因为这个场景的可信度几乎完全取决于“它看向哪边”。

如果仍然做成固定左侧版本，会有两个问题：

- 观众未必理解它在看谁
- 一旦现场站位改变，整个 scene 的意义就掉了

所以 Shenzhen 版必须把方向感绑定到 context。

## 失败信号

- 朝向和来人方向不对应
- 没有“停顿”和“回避”，只剩下转头
- 害羞动作太快，看起来像故障闪避
- 重新探出来的时机没有心理连贯性

## 落地建议

这个场景适合作为 Shenzhen 主包的第二按钮，因为它能在“醒来”之后立刻证明：

> Mira 不是随便动，它在理解“眼前这个人是谁”。
