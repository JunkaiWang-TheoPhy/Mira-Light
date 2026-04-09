# Mira Light 集成状态矩阵

## 文档目的

这份文档回答：

> 当前 `Mira_Light_Released_Version/` 到底完成到了什么程度？

它现在采用的是**最终收尾口径**，不再沿用原型阶段那种“还有很多软件缺口”的说法。

也就是说，这份矩阵要和下面两份文档保持一致：

- [release-final-status-matrix.md](./release-final-status-matrix.md)
- [release-final-hardware-blockers-checklist.md](./release-final-hardware-blockers-checklist.md)

## 当前总体结论

截至当前这一轮整理，最准确的说法是：

> 软件交付面已基本完成；剩余工作已主要收敛为硬件联通、真机校准和现场验收留证。

更直接一点说：

- 代码、文档、runbook、测试、bridge、console、receiver、OpenClaw 本机接入骨架都已经基本到位
- 剩下没有收尾的部分，已经不再主要是“缺少大块代码”
- 真正剩下的是：
  - 真实灯是否在线
  - 当前网络是否可达
  - 当前机械姿态是否完成真实校准
  - strict-online 验收是否留证

## 状态分级说明

### `已完成`

表示这部分已经可以作为 release 软件交付内容对外说明。

### `已完成软件闭环`

表示代码、fixture、测试、脚本已经具备，但最后一公里仍需要真实现场确认。

### `仅硬件阻塞`

表示当前剩余问题不再主要是软件开发问题，而是：

- 实机
- 实网
- 实际桌面/姿态
- 在线验收留证

## 当前状态矩阵

| 模块 | 当前状态 | 结论 | 说明 |
| --- | --- | --- | --- |
| release 目录结构 | 已完成 | 可交付 | `README`、`docs/`、`scripts/`、`tests/`、`tools/`、`web/` 已构成独立交付包。 |
| 文档入口与阅读顺序 | 已完成 | 可交付 | release 目录已具备清晰入口、启动说明、交接说明与排障说明。 |
| release 环境模板 | 已完成 | 可交付 | `repo.env.example` 已覆盖灯地址、bridge、console、receiver、bundle、日志等关键变量。 |
| 安装 / 启动 / rollback 脚本 | 已完成 | 可交付 | bootstrap、start、doctor、OpenClaw install/remove、verify 路径都已具备。 |
| director console -> bridge -> lamp 契约 | 已完成 | 可交付 | console 连 bridge、bridge 连 lamp 的链路与实际代码一致。 |
| bridge 统一控制面 | 已完成 | 可交付 | console 不再直接持有另一套 runtime；bridge 是统一状态真相源。 |
| 控制安全层 | 已完成 | 可交付 | `pose`、绝对控制、相对控制统一走 clamp / reject。 |
| OpenClaw 本机接入 | 已完成 | 可交付 | install / verify / rollback 已成闭环，且有测试覆盖。 |
| scene bundle 管理 | 已完成 | 可交付 | `minimal / booth_core / booth_extended / sensor_demos` 已具备发布语义。 |
| 音频 cue 基础能力 | 已完成 | 可交付 | 音频资产路径、播放器、dry-run fallback 与测试已具备。 |
| 本机最简 receiver | 已完成 | 可交付 | receiver 运行与文档都已成型。 |
| 视觉 bridge 基础能力 | 已完成 | 可交付 | `target_seen / target_updated / target_lost / no_target` 路由已具备，fixture 与测试已补齐。 |
| `farewell` 动态方向链路 | 已完成软件闭环 | 待真机确认 | runtime / vision bridge / tests 已支持动态方向；剩余是现场视觉输入和真实观感确认。 |
| `multi_person_demo` 事件链路 | 已完成软件闭环 | 待真机确认 | 多目标事件路由、动态 scene builder、tests 已具备；剩余是现场多人检测稳定性。 |
| `voice_demo_tired / sigh_demo` 触发链路 | 已完成软件闭环 | 待真机确认 | 文本意图、mic event bridge、tests 已具备；剩余是麦克风真实环境误判控制。 |
| `track_target` live tracking 主路径 | 已完成基础闭环 | 待真机强化 | bridge 路由、runtime tracking、fixture、测试已具备；剩余是 detector 稳定性与现场表现优化。 |
| release docs 路径独立性 | 已完成 | 可交付 | 文档中原型仓绝对路径和旧端口口径已清理。 |
| demo readiness / failure playbook | 已完成 | 可交付 | 演示前检查单与失败应急文档已经补齐。 |
| 自动化测试 | 已完成 | 可交付 | release tests 当前可通过，已足够作为交付前默认检查面。 |
| 真实灯联通性 | 未完成 | 仅硬件阻塞 | 需要真实灯在线、真实 IP 正确、当前网络路径可达。 |
| 真实 pose / servo 校准 | 未完成 | 仅硬件阻塞 | 需要真实灯、真实桌面条件和当前机械结构状态。 |
| strict-online 验收留证 | 未完成 | 仅硬件阻塞 | 需要 bridge、receiver、lamp 全在线后执行。 |

## 已完成部分现在可以怎么说

当前可以比较稳地对外表述为：

- 发布版的软件结构已经成型
- 本地控制链路已经统一
- OpenClaw 本机接入和回滚已经成闭环
- bridge、console、receiver、bundle、safety、fixture、tests、runbook 已具备
- 额外互动场景的很多能力已经进入“软件闭环完成、等待真机确认”的阶段

## 当前不应再用的旧口径

下面这些原型阶段说法，现在不适合继续作为主口径：

- “bridge / plugin 还只是骨架”
- “自动化测试基本没有”
- “控制链还没成型”
- “主要还差大量软件开发”

这些说法在更早阶段成立，但和当前 release 现状已经不一致了。

## 当前仍不宜过度表述的点

下面这些现在仍然不适合写成“已最终完成”：

- “真实灯端到端已经闭环”
- “所有主秀场景都已完成真机校准”
- “track_target 已经在现场足够稳定”
- “语音与多人检测已经过真实噪声环境验证”

原因不是代码没写，而是还缺最终现场证据。

## 最终剩余阻塞是什么

现在剩余阻塞已经高度收敛成 4 类：

1. 真实灯是否在线
2. 当前网络是否真的可达
3. 当前机械姿态是否完成真实校准
4. 在线验收是否留证

这 4 类之外，当前已经不再有明显的大块软件阻塞项。

## 推荐阅读顺序

如果你想快速理解“当前完成到哪里、还差什么”，建议按这个顺序看：

1. [release-final-status-matrix.md](./release-final-status-matrix.md)
2. [release-final-hardware-blockers-checklist.md](./release-final-hardware-blockers-checklist.md)
3. [release-demo-readiness-checklist.md](./release-demo-readiness-checklist.md)
4. [release-failure-playbook.md](./release-failure-playbook.md)

## 一句话结论

这份集成状态矩阵现在的最终口径就是：

> `Mira_Light_Released_Version/` 的软件交付面已基本完成；剩余工作已主要变成真实硬件、真实网络、真实校准和在线验收留证的问题。
