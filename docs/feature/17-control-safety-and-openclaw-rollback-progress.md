# Control Safety and OpenClaw Rollback Progress

## Current Status

这一轮进展的重点不是再加新能力，而是把 `Mira-Light` 从“能跑”进一步推进到“带安全边界地跑”。

当前已经落地两件很关键的事情：

- 控制安全层已经进入 release runtime 和 bridge 主链路
- OpenClaw 本地安装现在不再只有 apply，也已经具备 remove / rollback 闭环

这意味着项目开始从“原型脚本集合”走向“可交接、可恢复、可在现场更安心运行的系统”。

## 1. Shared Safety Module Has Landed

发布版脚本目录里已经新增了共享安全模块：

- [../../Mira_Light_Released_Version/scripts/mira_light_safety.py](../../Mira_Light_Released_Version/scripts/mira_light_safety.py)

它不是一层文档约定，而是已经实际进入代码主链的控制裁决层。

当前它统一管理三类控制：

- `pose`
- `absolute control`
- `relative nudge`

## 2. Servo Ranges Are No Longer Just Comments

这一层安全逻辑直接复用了 `scenes.py` 里已经存在的关节语义与范围定义：

- `hard_range`
- `rehearsal_range`
- `neutral`

也就是说，这些范围信息不再只是排练注释，而是已经真正影响运行时行为。

更准确地说：

- `hard_range` 用于决定哪些输入必须被拒绝
- `rehearsal_range` 用于决定哪些输入可以被保守地 clamp

## 3. Clamp and Reject Rules Are Now Explicit

当前控制安全规则已经很清楚：

### `pose`

- 如果 pose 目标角度都在 rehearsal range 内，直接通过
- 如果 pose 在 hard range 内但超过 rehearsal range，会被 clamp
- 如果 pose 超过 hard range，会被 reject

### `absolute control`

- 如果目标角度在 rehearsal range 内，直接通过
- 如果目标角度超过 rehearsal range 但仍在 hard range 内，会被 clamp
- 如果目标角度超过 hard range，会被 reject

### `relative nudge`

- 先根据当前已知姿态推导目标角度
- 如果当前姿态未知，直接 reject
- 如果推导后的目标角度超过 hard range，直接 reject
- 如果目标角度仍在 hard range 内但超出 rehearsal range，则把 delta 缩回安全范围

这一步非常重要，因为它避免了“相对位移在未知当前位置上盲推”的风险。

## 4. Runtime and Bridge Both Use the Same Safety Layer

这次不是只在某一处补校验，而是把安全层同时接进了：

- [../../Mira_Light_Released_Version/scripts/mira_light_runtime.py](../../Mira_Light_Released_Version/scripts/mira_light_runtime.py)
- [../../Mira_Light_Released_Version/tools/mira_light_bridge/bridge_server.py](../../Mira_Light_Released_Version/tools/mira_light_bridge/bridge_server.py)

这意味着：

- scene 执行走安全层
- runtime `apply_pose` 走安全层
- bridge 的 `POST /v1/mira-light/control` 走安全层
- bridge 的 `POST /v1/mira-light/apply-pose` 走安全层

所以现场无论是导演台、bridge API，还是内部 choreography，都不再绕开边界判断。

## 5. Safety Decisions Are Visible Instead of Silent

当前这层安全逻辑不只是偷偷改值，而是会把结果显式记录出来。

已落地的行为包括：

- clamp 会写 runtime 日志
- reject 会写 runtime 日志
- bridge 响应会带 `safety` 字段

因此现在至少能回答：

- 是不是被 clamp 了
- clamp 了哪个舵机
- 原始值和实际下发值分别是多少
- 为什么被 reject

这对导演台、交付验收和现场排障都很关键。

## 6. Runtime Now Tracks Estimated Servo State

为了让 `relative nudge` 有依据，runtime 这一轮还开始维护：

- `estimatedServoState`

它的状态来源包括：

- 通过安全层成功下发后的内部状态更新
- `/status` 返回后的同步
- device status ingress 后的同步
- `reset` 后重新标记为未知

这使得“相对控制到底是相对于谁”开始有了统一答案，而不是纯粹依赖调用方的想象。

## 7. Safety Tests Are No Longer Missing

这一轮已经补上了专门测试，而不再只是依赖人工理解。

主要新增：

- [../../Mira_Light_Released_Version/tests/test_release_safety.py](../../Mira_Light_Released_Version/tests/test_release_safety.py)

它覆盖的重点包括：

- 安全范围内通过
- 超范围被 clamp
- 危险输入被 reject
- bridge 返回 `safety` 元数据

这意味着安全层现在已经进入 release 的自动验证主干。

## 8. OpenClaw Install and Remove Are Now a Closed Loop

除了安全层，这一轮还把本机 OpenClaw 插件管理补成了真正闭环。

新增入口：

- [../../Mira_Light_Released_Version/scripts/remove_local_openclaw_mira_light.py](../../Mira_Light_Released_Version/scripts/remove_local_openclaw_mira_light.py)
- [../../Mira_Light_Released_Version/scripts/remove_openclaw_plugin.sh](../../Mira_Light_Released_Version/scripts/remove_openclaw_plugin.sh)

对应的 install 入口仍然是：

- [../../Mira_Light_Released_Version/scripts/install_local_openclaw_mira_light.py](../../Mira_Light_Released_Version/scripts/install_local_openclaw_mira_light.py)
- [../../Mira_Light_Released_Version/scripts/install_openclaw_plugin.sh](../../Mira_Light_Released_Version/scripts/install_openclaw_plugin.sh)

现在已经能做到：

- 备份 `~/.openclaw/openclaw.json`
- 写入 `plugins.allow`
- 写入 `plugins.entries`
- 建立本地插件目录 / 软链
- 之后再干净移除这些改动

这对交付和换机尤其重要，因为本地接入不再是“只会加不会退”的单向动作。

## 9. Rollback Lifecycle Is Also Covered by Tests

这一轮还补了 OpenClaw 生命周期测试：

- [../../Mira_Light_Released_Version/tests/test_openclaw_plugin_lifecycle.py](../../Mira_Light_Released_Version/tests/test_openclaw_plugin_lifecycle.py)

它验证的是：

- install 后配置已写入
- 插件目录已建立
- remove 后配置被清理
- 非 Mira 插件条目不会被误删
- 安装和卸载都会留下配置备份

这让 rollback 不再只是“理论上能做”，而是已经有自动测试兜底。

## Why This Progress Matters

如果没有这一轮，项目会继续暴露几个现实风险：

- 现场 raw control 可能越界
- `relative nudge` 可能在未知姿态上乱推
- clamp / reject 结果不可见
- OpenClaw 本地接入一旦写入就缺少正式退出路径

而现在更准确的表述是：

`Mira-Light` 已经开始拥有运行时安全边界和本地插件回滚能力，这两件事都比“再多一幕 demo”更接近正式交付工程所需的底线能力。

## Current Boundary

需要继续保持准确的是：

- 安全边界当前仍基于仓库里的 `SERVO_CALIBRATION` / profile，而不是最终实灯确认值
- clamp / reject 已经进入 runtime 与 bridge，但导演台还没有把这些元数据完整可视化
- `estimatedServoState` 是运行时估计状态，不等于高频真实闭环传感

所以当前最准确的结论不是“机械安全已完全验证”，而是：

软件层的安全护栏已经落地，下一步应继续用真实设备校准这些边界。

## Recommended External Framing

> `Mira-Light` 这一轮最重要的进展不是新增更多功能，而是把控制安全和本机回滚补成了正式工程能力。现在 release runtime 与 bridge 已经共享一套控制安全层，能够对 pose、绝对控制和相对 nudge 做 clamp 或 reject；同时本地 OpenClaw 插件也已经具备 install / remove 闭环和自动测试覆盖。
