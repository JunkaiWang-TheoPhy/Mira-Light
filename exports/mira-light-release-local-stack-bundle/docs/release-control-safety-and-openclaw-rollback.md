# Release Control Safety and OpenClaw Rollback

## 目的

这份文档专门说明发布版当前已经落地的两件工程能力：

- 控制安全层
- OpenClaw 本机安装与回滚闭环

它不是新的规划说明，而是对当前 release 目录里已经存在实现的整理。

## 当前结论

这一轮之后，发布版已经不再只是“能把动作发出去”。

更准确地说，它现在具备：

- 对 `pose`、绝对控制、相对 `nudge` 的统一安全裁决
- runtime 与 bridge 共用一套 clamp / reject 规则
- OpenClaw 插件 install / remove / verify 的闭环入口

## 对应实现文件

当前 release 里与这部分能力直接相关的文件包括：

- [`../scripts/mira_light_safety.py`](../scripts/mira_light_safety.py)
- [`../scripts/mira_light_runtime.py`](../scripts/mira_light_runtime.py)
- [`../tools/mira_light_bridge/bridge_server.py`](../tools/mira_light_bridge/bridge_server.py)
- [`../scripts/install_local_openclaw_mira_light.py`](../scripts/install_local_openclaw_mira_light.py)
- [`../scripts/remove_local_openclaw_mira_light.py`](../scripts/remove_local_openclaw_mira_light.py)
- [`../scripts/install_openclaw_plugin.sh`](../scripts/install_openclaw_plugin.sh)
- [`../scripts/remove_openclaw_plugin.sh`](../scripts/remove_openclaw_plugin.sh)

## 控制安全规则

### `pose`

- pose 目标角度都在 `rehearsal_range` 内时，直接通过
- 超出 `rehearsal_range` 但仍在 `hard_range` 内时，会被 clamp
- 超出 `hard_range` 时，直接 reject

### 绝对控制

- 目标角度在 `rehearsal_range` 内时，直接通过
- 超出 `rehearsal_range` 但仍在 `hard_range` 内时，会被 clamp
- 超出 `hard_range` 时，直接 reject

### 相对 `nudge`

- 会先基于当前已知姿态推导目标角度
- 如果当前姿态未知，直接 reject
- 如果推导结果超过 `hard_range`，直接 reject
- 如果推导结果还在 `hard_range` 内但超出 `rehearsal_range`，会把 delta 缩回安全范围

## 安全边界的来源

当前安全层直接复用了 [`../scripts/scenes.py`](../scripts/scenes.py) 里已有的关节定义：

- `hard_range`
- `rehearsal_range`
- `neutral`

这意味着这些范围现在不再只是排练注释，而是已经真正进入运行时裁决链。

## 安全层接在哪些地方

当前 release 里，下面这些路径都会经过同一套安全层：

- scene 执行
- runtime `apply_pose`
- bridge `POST /v1/mira-light/control`
- bridge `POST /v1/mira-light/apply-pose`

所以更准确的描述是：

```text
console -> bridge -> runtime -> lamp
```

在这条链上，bridge 和 runtime 都不会再绕开安全判断。

## clamp / reject 现在如何可见

这层安全逻辑不会静默吞掉结果。

当前已经落地的可见性包括：

- runtime 会记录 `[safety-clamp]`
- runtime 会记录 `[safety-reject]`
- bridge 响应会返回 `safety` 字段

这意味着调用方现在至少能知道：

- 是否发生了 clamp
- 哪个舵机被 clamp
- 原始输入和实际下发值分别是多少
- 为什么被 reject

## `estimatedServoState`

为了让相对 `nudge` 有统一依据，runtime 现在会维护：

- `estimatedServoState`

它会在下面几种情况下更新：

- 安全层成功提交控制以后
- 同步 `/status` 结果以后
- 接收到设备状态上报以后
- `reset` 以后重新标记为未知

这不是高频真实闭环传感，但已经比“完全不知道当前姿态”更接近可控系统。

## 对导演台和操作员意味着什么

导演台当前仍然主要展示 bridge / runtime 状态，但底层控制语义已经变了：

- 操作请求可能被 clamp
- 危险输入可能被 reject
- bridge API 已经能把 `safety` 元数据带回来

所以如果现场出现“动作没有完全按输入执行”，现在应该先看：

- bridge 响应里的 `safety`
- bridge / runtime 日志里的 `[safety-clamp]` 或 `[safety-reject]`

## OpenClaw 现在已经有回滚闭环

发布版当前推荐用脚本而不是手改配置文件。

安装入口：

```bash
bash scripts/install_openclaw_plugin.sh
```

移除入口：

```bash
bash scripts/remove_openclaw_plugin.sh
```

或者：

```bash
npm run remove:openclaw
```

当前 install / remove 已经能处理：

- 备份 `~/.openclaw/openclaw.json`
- 写入或移除 `plugins.allow`
- 写入或移除 `plugins.entries`
- 建立或清理本地插件目录 / 软链

这意味着本机 OpenClaw 接入不再是“只会加不会退”的一次性动作。

## 自动化验证

这一轮新增的自动化验证主要包括：

- [`../tests/test_release_safety.py`](../tests/test_release_safety.py)
- [`../tests/test_openclaw_plugin_lifecycle.py`](../tests/test_openclaw_plugin_lifecycle.py)

覆盖重点：

- 安全范围内通过
- 超范围被 clamp
- 危险输入被 reject
- bridge 返回 `safety` 元数据
- OpenClaw install / remove 的 round-trip

## 推荐使用方式

如果你是第一次接手 release，最稳的顺序是：

1. 先看 [release-startup-contract.md](./release-startup-contract.md)
2. 再按 [release-local-stack-runbook.md](./release-local-stack-runbook.md) 启动本地栈
3. 用 [release-preflight-runbook.md](./release-preflight-runbook.md) 做离线 / 在线检查
4. 接入 OpenClaw 时优先用安装脚本和移除脚本，不要先手改配置

## 当前边界

这部分也需要保持说法准确：

- 当前安全边界仍然基于仓库里的 `SERVO_CALIBRATION` / profile
- clamp / reject 已经落地，但导演台还没有把这些元数据做成完整可视化
- `estimatedServoState` 是运行时估计状态，不等于真实硬件闭环传感

所以当前最准确的结论不是“机械安全已完全验证”，而是：

> 软件层的安全护栏和 OpenClaw 回滚能力已经在发布版落地，下一步仍应继续用真实设备校准这些边界。
