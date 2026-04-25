# Shenzhen Fixed Scenes

这个目录专门回答一个现实问题：

> 在当前阶段，深圳版 10 个场景如果尽量不用实时计算，而优先使用板端已有固定动作，该怎么做。

这里的文档不是最终真值代码，也不是导演稿摘要，而是：

- 固定动作优先的实现指导
- 端侧已有脚本如何拼成一幕
- 哪些地方先用固定版本占位
- 后续什么时候再升级到动态 / 实时

## 当前策略

本目录统一遵循这条路线：

1. 能用板端现成脚本拼出来的，就先不用实时计算
2. 能用固定方向、固定幅度、固定节奏完成证明的，就先不要引入视觉闭环
3. 先做可演示、可复现、可回退的版本
4. 只有固定版明显不够用时，才升级到 dynamic builder 或实时 tracking

## 当前实施范围

当前固定版文档虽然覆盖了 10 个场景，但本轮真正要推进的是：

- `1. sz_presence_wake`
- `2. sz_cautious_intro`
- `3. sz_hand_nuzzle`
- `7. sz_sigh_comfort`
- `8. sz_voice_affect_response`
- `9. sz_multi_guest_choice`
- `10. sz_farewell_sleep`

当前明确暂不推进：

- `4. sz_hand_boundary`
- `5. sz_standup_nudge`
- `6. sz_tabletop_follow`

这三份文档目前保留为后续预研材料，不进入本轮固定版优先实现范围。

## 10 个场景

1. [01_sz_presence_wake_fixed.md](./01_sz_presence_wake_fixed.md)
1a. [01_sz_presence_wake_script_blueprint.md](./01_sz_presence_wake_script_blueprint.md)
2. [02_sz_cautious_intro_fixed.md](./02_sz_cautious_intro_fixed.md)
2a. [02_sz_cautious_intro_script_blueprint.md](./02_sz_cautious_intro_script_blueprint.md)
3. [03_sz_hand_nuzzle_fixed.md](./03_sz_hand_nuzzle_fixed.md)
3a. [03_sz_hand_nuzzle_script_blueprint.md](./03_sz_hand_nuzzle_script_blueprint.md)
4. [04_sz_hand_boundary_fixed.md](./04_sz_hand_boundary_fixed.md)
5. [05_sz_standup_nudge_fixed.md](./05_sz_standup_nudge_fixed.md)
5b. [05_pdf_offer_celebrate_script_blueprint.md](./05_pdf_offer_celebrate_script_blueprint.md)
6. [06_sz_tabletop_follow_fixed.md](./06_sz_tabletop_follow_fixed.md)
6a. [06_sz_tabletop_follow_script_blueprint.md](./06_sz_tabletop_follow_script_blueprint.md)
7. [07_sz_sigh_comfort_fixed.md](./07_sz_sigh_comfort_fixed.md)
8. [08_sz_voice_affect_response_fixed.md](./08_sz_voice_affect_response_fixed.md)
8a. [08_sz_happy_reaction_script_blueprint.md](./08_sz_happy_reaction_script_blueprint.md)
9. [09_sz_multi_guest_choice_fixed.md](./09_sz_multi_guest_choice_fixed.md)
10. [10_sz_farewell_sleep_fixed.md](./10_sz_farewell_sleep_fixed.md)
10a. [10_sz_farewell_sleep_script_blueprint.md](./10_sz_farewell_sleep_script_blueprint.md)
10b. [10_sz_sleep_script_blueprint.md](./10_sz_sleep_script_blueprint.md)

## 推荐阅读顺序

1. 本文档
2. `01 / 01a / 02 / 02a / 03 / 03a / 10 / 10a / 10b`
3. `04 / 07 / 08 / 08a`
4. `05 / 05b / 09`
5. `06 / 06a`

原因很简单：

- `presence_wake`
- `cautious_intro`
- `farewell_sleep`

最容易先形成一套完整主秀骨架。

而 `tabletop_follow` 仍然是最依赖实时能力的一项，所以放最后。

## 一句话总结

这个目录的目标不是“把深圳版做得最聪明”，而是：

> 先把深圳版做成一套基于固定动作也能稳定演、稳定讲、稳定回退的 scene pack。
