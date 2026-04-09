# Claw-Native and Local OpenClaw Integration Progress

## What Has Already Been Completed

仓库现在已经不只是“有一些脚本”，而是已经把本地 `Mira Light + OpenClaw`
集成整理成了一套可以复用的 `Claw-Native` 包。

当前这层进展可以分成两部分理解：

- `仓库打包完成`
- `验证机器已实际 rollout`
- `本机插件 install / remove 已闭环`

## What the Repository Already Contains

仓库里的 `Claw-Native ` 目录现在承担的是“可复用本地节点包”的角色。

它已经包含：

- Mira workspace identity 模板
- 脱敏后的 `openclaw` 配置模板
- bridge / vision env 模板
- wrapper 与 launchd 模板
- 概览、runbook、automation、rollout-state 文档
- 对本机模型配置更友好的 materialize 规则

主要入口：

- [../../Claw-Native /README.md](../../Claw-Native%20/README.md)
- [../../Claw-Native /docs/mira-light-claw-native-overview.md](../../Claw-Native%20/docs/mira-light-claw-native-overview.md)
- [../../Claw-Native /docs/mira-light-claw-native-runbook.md](../../Claw-Native%20/docs/mira-light-claw-native-runbook.md)
- [../../Claw-Native /docs/mira-light-claw-native-automation.md](../../Claw-Native%20/docs/mira-light-claw-native-automation.md)
- [../../scripts/apply_claw_native_local.py](../../scripts/apply_claw_native_local.py)
- [../../scripts/verify_local_openclaw_mira_light.py](../../scripts/verify_local_openclaw_mira_light.py)
- [./17-control-safety-and-openclaw-rollback-progress.md](./17-control-safety-and-openclaw-rollback-progress.md)

## What Has Been Actually Rolled Out on the Verified Machine

当前已验证机器上，下面这些能力已经不是纸面方案，而是实际跑通过：

- OpenClaw 已安装并本地运行
- gateway mode 已设为 `local`
- gateway LaunchAgent 正常
- `mira-light-bridge` 插件可被 OpenClaw 发现
- `plugins.allow`
- `plugins.load.paths`
- `plugins.entries`
- 默认模型不再由模板强制钉死，本机现有模型会被保留
- Mira identity/workspace 文件已落到 `~/.openclaw/workspace`
- bridge LaunchAgent 正常
- vision LaunchAgent 正常
- launchd-friendly service copy 已同步
- `MIRA_LIGHT_SHOW_EXPERIMENTAL=1` 已启用
- local semantic memory 已启用

更完整的已验证状态见：

- [../../Claw-Native /docs/mira-light-claw-native-rollout-state-2026-04-09.md](../../Claw-Native%20/docs/mira-light-claw-native-rollout-state-2026-04-09.md)

## Why This Step Matters

如果没有这层 `Claw-Native` 打包，很多能力虽然能临时跑起来，但会长期存在这些问题：

- 本机配置不可复用
- launchd / wrapper / env 分散在机器里，不易回看
- Mira 身份文件与 bridge 配置容易漂移
- 后续换机器时难以稳定复现

而现在这层打包之后，仓库已经具备了：

- 一个可落地的本地节点模板
- 一个 apply 脚本
- 一个 verify 脚本
- 一份与真实机器状态对齐的 rollout 记录

## OpenClaw Rollback Is Now Explicit

这一轮 release 侧已经补上：

- install 入口
- verify 入口
- remove / rollback 入口

更具体地说，发布版现在已经有：

- `install_local_openclaw_mira_light.py`
- `verify_local_openclaw_mira_light.py`
- `remove_local_openclaw_mira_light.py`

这意味着当前本机 OpenClaw 集成不再只是“把 Mira 接上”，也开始具备“安全退出和恢复”的交付属性。

## Real Remaining Blockers

需要明确的是：当前本机 Claw-Native 集成的主要剩余问题，已经不在 OpenClaw
配置本身，而在真实灯的网络可达性。

已知阻塞：

- 本机在验证时无法到达 `http://172.20.10.3`
- `ping` 失败
- `/status` 超时
- `/led` 超时
- 路由一度被送到了 `utun8`

所以现在更准确的结论是：

`Claw-Native` 的软件集成已经基本完整，剩余主要是物理设备网络问题，而不是
本地 OpenClaw 或 Mira 配置缺失。

如需补充阅读，也可以继续看：

- [./13-mira-identity-and-self-knowledge-progress.md](./13-mira-identity-and-self-knowledge-progress.md)
- [./14-local-configuration-and-model-preservation-progress.md](./14-local-configuration-and-model-preservation-progress.md)

## Recommended External Framing

> `Mira-Light` 已经拥有一套仓库内可复用的 `Claw-Native` 本地节点包，包含 Mira
> 身份模板、OpenClaw 配置模板、launchd 模板、apply/verify 自动化和真实机器
> rollout 记录。与此同时，release 侧 install / remove 闭环也已经补上，软件侧集成已经更接近可交接工程。
