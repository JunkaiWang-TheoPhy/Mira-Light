# Release Final Status Matrix

## 目的

这份文档用最终交付口径回答：

> 当前 release 目录里，哪些已经完成，哪些剩下的已经不再是代码问题，而是硬件与现场条件问题？

它不是原型阶段的“缺口讨论”，而是收尾阶段的“完成度声明”。

## 当前总判断

截至当前这一轮整理，`Mira_Light_Released_Version/` 可以用下面一句话概括：

> 软件交付面已经基本完成，剩余主要阻塞项已经收敛到真实灯、真实网络、真实校准和现场验收。

更具体地说：

- 文档入口：已完成
- 安装 / 启动 / rollback：已完成
- bridge / console / receiver 拓扑：已完成
- OpenClaw 本机接入骨架：已完成
- scene bundle / safety / fixture / tests：已完成
- 真实灯端到端：仍需现场硬件闭环

## 最终状态矩阵

| 模块 | 当前状态 | 结论 | 说明 |
| --- | --- | --- | --- |
| release 目录结构 | 已完成 | 可交付 | `README`、`docs/`、`scripts/`、`tests/`、`tools/`、`web/` 已构成独立交付包。 |
| 文档入口与阅读顺序 | 已完成 | 可交付 | [`README.md`](./../README.md) 与 [`README.md`](./README.md) 已明确启动、交接和排障入口。 |
| release 环境模板 | 已完成 | 可交付 | [`repo.env.example`](./../deploy/repo.env.example) 已覆盖灯地址、bridge、console、receiver、bundle、日志等关键变量。 |
| director console -> bridge -> lamp 启动契约 | 已完成 | 可交付 | [`release-startup-contract.md`](./release-startup-contract.md) 与实际代码口径一致。 |
| bridge 统一控制面 | 已完成 | 可交付 | console 已代理 bridge，bridge 持有 runtime，避免双控制面。 |
| 控制安全层 | 已完成 | 可交付 | `pose` / 绝对控制 / 相对控制已统一走 clamp / reject。 |
| OpenClaw install / verify / rollback | 已完成 | 可交付 | install/remove/verify 脚本、doctor、tests 已就位。 |
| scene bundle 管理 | 已完成 | 可交付 | `minimal / booth_core / booth_extended / sensor_demos` 已形成发布语义。 |
| 音频 cue 基础能力 | 已完成 | 可交付 | `AudioCuePlayer`、dry-run fallback、资产根目录、测试链路已具备。 |
| 视觉 bridge 基础能力 | 已完成 | 可交付 | `target_seen / target_updated / target_lost / no_target` 路由已存在，fixture 与测试已补齐。 |
| `farewell` 动态方向链路 | 已完成软件闭环 | 待真机确认 | runtime / vision bridge / tests 已支持动态方向；剩余是现场视觉信号与真实观感确认。 |
| `multi_person_demo` 事件链路 | 已完成软件闭环 | 待真机确认 | 多目标事件路由、动态 scene builder、tests 已具备；剩余是现场检测稳定性。 |
| `voice_demo_tired / sigh_demo` 触发链路 | 已完成软件闭环 | 待真机确认 | `mira_voice_intents.py`、`mic_event_bridge.py`、tests 已具备；剩余是麦克风阈值和真实环境误判控制。 |
| `track_target` live tracking 主路径 | 已完成基础闭环 | 待真机强化 | fixture、bridge 路由和 runtime tracking 已具备；剩余是 detector 稳定性和现场表现。 |
| release docs 路径独立性 | 已完成 | 可交付 | `docs/` 内原型仓绝对路径与旧 `19783` 口径已清理。 |
| demo readiness / failure playbook | 已完成 | 可交付 | 已新增演示前清单与失败应急文档。 |
| 自动化测试 | 已完成 | 可交付 | release tests 当前可通过，作为交付前默认检查面。 |
| 真实灯联通性 | 未完成 | 硬件阻塞 | 必须在现场或真实网络环境中验证。 |
| 真实 pose / servo 校准 | 未完成 | 硬件阻塞 | 需要真实灯、真实结构状态和演示桌面条件。 |
| strict-online 验收留证 | 未完成 | 硬件阻塞 | 需要 bridge、receiver、lamp 全在线后执行。 |

## 已完成项可以如何表述

当前可以较稳地对外表述为：

- 发布版的软件结构已经成型
- 本地控制链路已经统一
- OpenClaw 本机接入和回滚已经成闭环
- scene bundle、safety、fixture、tests、runbook 已具备
- 剩余工作已不再是“缺少大块代码”，而主要是“真实设备与现场环境验证”

## 当前不应过度表述的地方

下面这些说法现在还不适合直接写成“已最终完成”：

- “真实灯端到端已经闭环”
- “所有主秀场景都已完成真机校准”
- “track_target 已经在现场足够稳定”
- “语音与多人检测已经过真实噪声环境验证”

这些并不是代码缺失，而是还没有最终硬件验收证据。

## 最终剩余阻塞的本质

现在剩余阻塞项已经集中成 4 类：

1. 真实灯是否在线
2. 当前网络是否真的可达
3. 当前真实机械姿态是否完成校准
4. 严格在线验收是否留证

也就是说，当前 release 已经从：

```text
代码 / 文档 / 架构不完整
```

推进到了：

```text
软件面基本完成
-> 等待真实硬件与现场条件验收
```

## 一句话结论

当前 release 最准确的最终口径是：

> 软件交付面已基本完成；剩余工作已主要收敛为硬件联通、真机校准和现场验收留证。
