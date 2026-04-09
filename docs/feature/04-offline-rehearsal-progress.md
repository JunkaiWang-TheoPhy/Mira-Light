# Offline Rehearsal and Mock Validation Progress

## Current Status

在真实灯暂时不可连接的前提下，仓库已经具备了一套可以长期使用的离线开发与
验证主链，而不只是零散脚本。

这条链现在已经覆盖：

- Mock Device
- Mock E2E tests
- Scene Trace Recorder
- Vision Replay Bench
- Fault injection
- Memory / Persona Eval
- One-click offline rehearsal

## Why This Progress Matters

真实灯当然仍然是最终权威，尤其涉及：

- 舵机标定
- 真实灯光材质
- 物理安全
- 热 / 电源行为

但绝大多数工程工作其实并不需要实灯在线。

离线演练链路的价值就在于：

- 让 bridge/runtime/integration 可以持续迭代
- 让 scene 编排能被可视化 review
- 让 vision-to-scene 决策可重复回放
- 让错误与降级行为可系统压测
- 让 Mira 的记忆与人格一致性可以被回归验证

## Core Capabilities Already in the Repository

### 1. Mock Device

- [../../scripts/mock_mira_light_device.py](../../scripts/mock_mira_light_device.py)

这层模拟了原始 ESP32 HTTP 契约，并提供状态与 fault 管理接口。

### 2. Mock E2E tests

- [../../tests/test_mock_device_e2e.py](../../tests/test_mock_device_e2e.py)

这层验证 `bridge -> runtime -> mock device` 的完整链路，并覆盖部分异常返回。

### 3. Scene Trace Recorder

- [../../scripts/scene_trace_recorder.py](../../scripts/scene_trace_recorder.py)

这层负责把 scene 输出成 JSON / HTML 时间线，便于 review “它还像不像 Mira”。

### 4. Vision Replay Bench

- [../../scripts/vision_replay_bench.py](../../scripts/vision_replay_bench.py)

这层负责对 vision capture 做离线回放。

### 5. Fault injection

- [../../config/mira_light_mock_faults.example.json](../../config/mira_light_mock_faults.example.json)

fault 注入已经直接内建在 mock device 里，不需要额外起第二套模拟器。

### 6. Memory / Persona Eval

- [../../scripts/mira_memory_persona_eval.py](../../scripts/mira_memory_persona_eval.py)
- [../../config/mira_memory_persona_eval.json](../../config/mira_memory_persona_eval.json)

这层用来检查检索质量、workspace 是否仍然编码了 Mira、以及 agent 是否保持
in-character。

### 7. One-Click Offline Rehearsal Entry

- [../../scripts/run_mira_light_offline_rehearsal.py](../../scripts/run_mira_light_offline_rehearsal.py)
- [../../scripts/run_mira_light_offline_rehearsal.sh](../../scripts/run_mira_light_offline_rehearsal.sh)
- [../../config/mira_light_offline_rehearsal.json](../../config/mira_light_offline_rehearsal.json)
- [../../tests/test_offline_rehearsal_smoke.py](../../tests/test_offline_rehearsal_smoke.py)

## Supported Offline Modes

当前 one-click rehearsal 已经支持：

- `quick`
- `full`
- `fault`
- `interactive`

它会自动创建一次 timestamped run 目录，收集：

- `summary.json`
- `index.html`
- per-step logs
- mock device artifacts
- scene traces
- vision replay outputs
- persona eval report

## Verified Local Results

在验证机器上，下面这两种模式已经实际跑通：

- `quick`
- `full`

生成过的 run 目录示例：

- `runtime/offline-rehearsal/2026-04-09T07-24-12-quick/`
- `runtime/offline-rehearsal/2026-04-09T07-26-08-full/`

这说明当前离线演练已经不是概念设计，而是本机可运行的稳定入口。

## Why This Changes the Project Pace

离线演练链的意义非常大，因为它把“灯不在线”从阻塞，降级成了“暂时不能做实机校准”。

换句话说，当前即使不连实灯，团队仍然可以继续推进：

- scene 设计
- tool/bridge 改动
- 集成回归
- 视觉回放
- 故障压测
- Mira 人格一致性验证

## Boundary

这套离线链仍然不能替代：

- 真实舵机校准
- 真实光感和材质观感
- 真实 booth 网络
- 真机触摸/距离传感器调优

所以最准确的表述是：

离线演练现在已经覆盖了“软件闭环”和“人格/行为回归”，但不替代最终的物理闭环。

## Related Overview Docs

更完整的说明见：

- [../mira-light-offline-validation-stack.md](../mira-light-offline-validation-stack.md)
