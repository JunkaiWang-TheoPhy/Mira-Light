# Motions Shenzhen

这个目录不是现有 `Motions/` 的简单复制，而是一套面向深圳现场的全新 scene pack 规格文档。

它的目标不是先写 choreography，而是先把下面三件事讲清楚：

1. 深圳现场到底要证明什么
2. 哪 10 个交互最值得占用导演台主按钮
3. 这些交互未来应该怎样接到现有 `scene -> runtime -> director console` 链路

## 这套 Shenzhen pack 的核心判断

深圳版不应该简单复刻当前 release 的 10 个主场景。

原因是当前默认 10 场景里有几类内容更像：

- 情绪 filler
- 过渡用演出段落
- 舞台效果证明

而不是“感知能力证明”。

深圳现场更应该优先证明下面 4 件事：

1. Mira 看见了人
2. Mira 接住了人的状态
3. Mira 有边界感和偏好
4. Mira 能完成一段完整社交闭环

因此，这套 Shenzhen pack 重新选取了 10 个一级交互。

## Shenzhen 主包的 10 个交互

1. `sz_presence_wake`
2. `sz_cautious_intro`
3. `sz_hand_nuzzle`
4. `sz_hand_boundary`
5. `sz_standup_nudge`
6. `sz_tabletop_follow`
7. `sz_sigh_comfort`
8. `sz_voice_affect_response`
9. `sz_multi_guest_choice`
10. `sz_farewell_sleep`

## 为什么是这 10 个

这 10 个交互覆盖了深圳资料里最重要的体验证据：

- 开场欢迎：`sz_presence_wake`
- 认人与试探：`sz_cautious_intro`
- 亲近与边界：`sz_hand_nuzzle`、`sz_hand_boundary`
- 可爱提醒：`sz_standup_nudge`
- 真正看见桌面目标：`sz_tabletop_follow`
- 情绪感知：`sz_sigh_comfort`
- 语言理解后的情绪表达：`sz_voice_affect_response`
- 多人情况下的“活物感”：`sz_multi_guest_choice`
- 收尾社交闭环：`sz_farewell_sleep`

相对地，下面几类内容被刻意放出了一级主包：

- `cute_probe`
- `daydream`
- `celebrate`

不是因为它们不重要，而是因为它们更适合作为：

- 次级 filler scene
- 主秀中的过渡动作
- 演出性加分彩蛋

而不是深圳场景包的一级“能力证明按钮”。

## 这套 pack 的层次定义

这套文档默认沿用仓库现有分层。

### 1. 场景规格层

就是当前 `Motions_Shenzhen/*.md` 这些文档。

它负责定义：

- `sceneId`
- `demo_goal`
- `scene_mode`
- `apiContextKeys`
- `fallback_behavior`
- `operator_cue`
- `success_signal`

### 2. choreography 真值层

未来不应该写在 `Motions_Shenzhen/` 里，而应该新增：

- `scripts/scenes_shenzhen.py`

它负责：

- `SCENE_META`
- `SCENES`
- Shenzhen 版姿态骨架
- Shenzhen 版动作编排

### 3. runtime 动态生成层

未来应该在 runtime 中增加 Shenzhen 版 builder。

它负责：

- 根据 `scene_context` 动态生成 scene
- 把事件 payload 转成 scene context
- 区分 `static`、`dynamic_builder`、`hybrid`、`event_scene`、`chain_scene`

### 4. motion manifest 层

未来才是：

- `Motions_Shenzhen/<scene>/scene_script.py`

它的职责只应该是：

- 让导演台知道这个场景存在
- 暴露 `stepOutline`
- 生成统一 request body

它不应该重新成为动作真值。

## `scene_mode` 约定

本目录里的 10 个交互使用以下模式标签。

- `static`
  固定 choreography，运行前不依赖动态上下文
- `dynamic_builder`
  运行开始前，根据 context 生成一次定制 scene
- `hybrid`
  有固定进入/退出段，中间核心行为由实时输入驱动
- `event_scene`
  由事件直接触发，动作本体较短，重点在“响应正确”
- `chain_scene`
  一个按钮触发多个阶段，可能包含轻分支或收尾串联

## 文件说明

- [10-scene-pack-matrix.md](./10-scene-pack-matrix.md)
  10 个交互的总表
- [console-integration-plan.md](./console-integration-plan.md)
  深圳场景包如何接入当前主控台
- [reference_default_pack/README.md](./reference_default_pack/README.md)
  从默认 `Motions/` 复制进来的参考层，包含可复用的 `scene_script.py` 与测试文档
- [reference_rdk_x5_board/README.md](./reference_rdk_x5_board/README.md)
  从远程地瓜开发板 `/home/sunrise` 拉回来的板端参考层，包含真实动作脚本、协议文档和 UART 工具
- [01_sz_presence_wake.md](./01_sz_presence_wake.md)
- [02_sz_cautious_intro.md](./02_sz_cautious_intro.md)
- [03_sz_hand_nuzzle.md](./03_sz_hand_nuzzle.md)
- [04_sz_hand_boundary.md](./04_sz_hand_boundary.md)
- [05_sz_standup_nudge.md](./05_sz_standup_nudge.md)
- [06_sz_tabletop_follow.md](./06_sz_tabletop_follow.md)
- [07_sz_sigh_comfort.md](./07_sz_sigh_comfort.md)
- [08_sz_voice_affect_response.md](./08_sz_voice_affect_response.md)
- [09_sz_multi_guest_choice.md](./09_sz_multi_guest_choice.md)
- [10_sz_farewell_sleep.md](./10_sz_farewell_sleep.md)

## 建议阅读顺序

1. `README.md`
2. `10-scene-pack-matrix.md`
3. `reference_default_pack/README.md`
4. `reference_rdk_x5_board/README.md`
5. `console-integration-plan.md`
6. 10 个场景规格书

## 一句话总结

`Motions_Shenzhen/` 不应该是“又一个动作目录”，而应该先成为：

> 深圳现场 scene pack 的产品规格层、导演层和主控台接入设计层。
