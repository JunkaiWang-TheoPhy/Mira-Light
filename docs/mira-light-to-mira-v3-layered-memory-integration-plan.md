# Mira Light 对接 Mira V3 Layered Memory 实施方案

## 文档目的

这份文档用于把下面这件事讲清楚，并且讲到可以直接执行：

> 如何把 `Mira-Light` 现有的 bridge / scene runtime / device reports / vision pipeline，
> 真正接进 `Mira_v3` 最近新增的 `memory-context + session memory + prompt-pack` 这条链路。

这里不是产品评论，也不是抽象架构说明，而是：

- 当前已经有什么
- 还缺什么
- 分几步做
- 每一步改哪些文件
- 每一步跑哪些命令
- 每一步怎么验收

## 当前前提

需要先接受这几个事实：

### 1. `Mira_v3` 最近已经有了 layered memory 的第一版实现

关键能力包括：

- `memory-context` SQLite 持久化
- `session_notes`
- `POST /v1/session-memory/update`
- `POST /v1/session-memory/current`
- `POST /v1/memory/prompt-pack`
- Lingzhu adapter 在请求前拉 prompt-pack、请求后写 session memory
- `additionalUserIds` 允许把其它 writer id 的记忆也带进 prompt-pack

关键参考：

- [`Mira_v3/docs/architecture/mira-v3-layered-memory-and-proactivity-implementation-2026-04-09.md`](/Users/Zhuanz/Documents/Github/Javis-Hackathon/Mira_v3/docs/architecture/mira-v3-layered-memory-and-proactivity-implementation-2026-04-09.md)

### 2. `Mira-Light` 已经有 embodied memory producer 雏形

当前仓库已经具备：

- scene outcome 写入 memory-context
- device status / event 选择性写入 memory-context
- bridge 级 memoryContext 配置

关键文件：

- [`tools/mira_light_bridge/embodied_memory_client.py`](/Users/Zhuanz/Documents/Github/Mira-Light/tools/mira_light_bridge/embodied_memory_client.py)
- [`tools/mira_light_bridge/bridge_server.py`](/Users/Zhuanz/Documents/Github/Mira-Light/tools/mira_light_bridge/bridge_server.py)
- [`tools/mira_light_bridge/bridge_config.json`](/Users/Zhuanz/Documents/Github/Mira-Light/tools/mira_light_bridge/bridge_config.json)

### 3. 当前最大的缺口不是“能不能写 memory”，而是“怎么形成完整闭环”

也就是说：

- 写 memory 已经不是零
- 但“session memory / prompt-pack / director console / track_target 闭环”还没全部打通

## 当前已经具备的能力

## 一、Mira-Light 侧

### 1. Scene runtime

- [`scripts/scenes.py`](/Users/Zhuanz/Documents/Github/Mira-Light/scripts/scenes.py)
- [`scripts/mira_light_runtime.py`](/Users/Zhuanz/Documents/Github/Mira-Light/scripts/mira_light_runtime.py)
- [`scripts/console_server.py`](/Users/Zhuanz/Documents/Github/Mira-Light/scripts/console_server.py)

当前已经能：

- 执行 10 个主场景
- 返回 runtime state
- 提供导演台 API

### 2. Bridge

- [`tools/mira_light_bridge/bridge_server.py`](/Users/Zhuanz/Documents/Github/Mira-Light/tools/mira_light_bridge/bridge_server.py)

当前已经能：

- 暴露 `/v1/mira-light/*` API
- 运行 scene
- 接收 `/device/status`
- 接收 `/device/event`
- 在启用 memory context 时把部分事件写到 `memory-context`

### 3. Vision side

- [`scripts/track_target_event_extractor.py`](/Users/Zhuanz/Documents/Github/Mira-Light/scripts/track_target_event_extractor.py)
- [`scripts/vision_runtime_bridge.py`](/Users/Zhuanz/Documents/Github/Mira-Light/scripts/vision_runtime_bridge.py)

当前已经能：

- 从 JPEG/视频帧提取一个 first-pass target signal
- 写出结构化 vision event
- 用 surrogate choreography 触发 runtime scene

但还不能：

- 做真正的闭环 track_target

## 二、Mira_v3 侧

### 1. Memory Context

默认：

- host: `127.0.0.1`
- port: `3301`
- DB path: `.mira-runtime/memory-context/memory.sqlite`

关键文件：

- [`Mira_v3/services/memory-context/README.md`](/Users/Zhuanz/Documents/Github/Javis-Hackathon/Mira_v3/services/memory-context/README.md)
- [`Mira_v3/services/memory-context/src/server.ts`](/Users/Zhuanz/Documents/Github/Javis-Hackathon/Mira_v3/services/memory-context/src/server.ts)

### 2. Lingzhu adapter

关键文件：

- [`Mira_v3/services/lingzhu-live-adapter/src/server.js`](/Users/Zhuanz/Documents/Github/Javis-Hackathon/Mira_v3/services/lingzhu-live-adapter/src/server.js)
- [`Mira_v3/services/lingzhu-live-adapter/src/prompt-pack-client.js`](/Users/Zhuanz/Documents/Github/Javis-Hackathon/Mira_v3/services/lingzhu-live-adapter/src/prompt-pack-client.js)
- [`Mira_v3/services/lingzhu-live-adapter/src/session-memory-client.js`](/Users/Zhuanz/Documents/Github/Javis-Hackathon/Mira_v3/services/lingzhu-live-adapter/src/session-memory-client.js)

当前已经能：

- 在一轮请求前拉 `prompt-pack`
- 在一轮请求后写 `session-memory`
- 通过 `additionalUserIds` 把 `mira-light-bridge` 这种 writer id 的内容也带进 prompt

## 目标闭环

目标不是只写 memory，而是形成下面这条链路：

```text
Mira-Light scene / device / vision event
-> embodied_memory_client.py
-> Mira_v3 memory-context
-> prompt-pack
-> Lingzhu adapter system prompt reinjection
-> Mira decision
-> OpenClaw execution
-> Mira-Light scene / bridge
```

从角色分工上看：

- `Mira-Light`：具身事件生产者
- `memory-context`：结构化记忆底座
- `Lingzhu adapter`：会话级 prompt reinjection
- `OpenClaw`：执行引擎
- `Mira`：判断、主动性、时机

## 实施范围建议

为了避免一次做太多，建议分三波：

### Wave 1：把 `Mira-Light` 稳定接入 `memory-context`

目标：

- 场景结果、设备状态、设备错误稳定写入 `memory-context`

### Wave 2：让 `Mira-Light` 参与 `prompt-pack`

目标：

- 在 Mira 对话前，`mira-light-bridge` writer 的关键信息能被带进 prompt-pack

### Wave 3：给 `Mira-Light` 增加 session-state / next-step 层

目标：

- 不只写 episodic outcome
- 还写“当前具身状态 / 下一步 / relevant files / blocking reason”

## Wave 1 实现：先把写入链路打稳

## 第 1 步：在 Mira_v3 侧启动 `memory-context`

如果你在 `Mira_v3` 仓库里单独起 `memory-context`，可以进入服务目录：

```bash
cd /Users/Zhuanz/Documents/Github/Javis-Hackathon/Mira_v3/services/memory-context
npm install
npm run start
```

默认端口：

```text
http://127.0.0.1:3301
```

健康检查：

```bash
curl http://127.0.0.1:3301/v1/health
```

如果你走的是 `Mira_v3` 的 integrated runtime 路径，则应确保其环境变量允许 memory sidecar：

参考：

- [`Mira_v3/deploy/mira-openclaw/env.example`](/Users/Zhuanz/Documents/Github/Javis-Hackathon/Mira_v3/deploy/mira-openclaw/env.example)

关键变量：

```bash
MIRA_OPENCLAW_MEMORY_CONTEXT_ENABLED=true
MIRA_OPENCLAW_MEMORY_CONTEXT_URL=http://127.0.0.1:3301/v1/memory/context
MIRA_OPENCLAW_SESSION_MEMORY_ENABLED=true
MIRA_OPENCLAW_PROMPT_PACK_ENABLED=true
MIRA_LINGZHU_PROMPT_PACK_ADDITIONAL_USER_IDS=mira-light-bridge
```

注意：

- `MIRA_OPENCLAW_MEMORY_CONTEXT_URL` 是 **读取上下文 / prompt-pack** 用的 URL
- `Mira-Light bridge_config.json` 里的 `memoryContext.baseUrl` 是 **写入 memory** 用的 base URL

两者不要混淆。

## 第 2 步：在 Mira-Light 侧启用 embodied memory 写入

当前配置在：

- [`tools/mira_light_bridge/bridge_config.json`](/Users/Zhuanz/Documents/Github/Mira-Light/tools/mira_light_bridge/bridge_config.json)

其中已经有：

```json
"memoryContext": {
  "enabled": false,
  "baseUrl": "http://127.0.0.1:3301",
  "authTokenEnv": "MIRA_MEMORY_CONTEXT_AUTH_TOKEN",
  "userId": "mira-light-bridge",
  "requestTimeoutSeconds": 2,
  "deviceStatusTtlSeconds": 900,
  "failureTtlSeconds": 3600
}
```

建议这样启动：

```bash
export MIRA_LIGHT_MEMORY_CONTEXT_ENABLED=1
export MIRA_MEMORY_CONTEXT_AUTH_TOKEN=<your-token-if-needed>
python3 tools/mira_light_bridge/bridge_server.py
```

或者用现有脚本：

```bash
export MIRA_LIGHT_MEMORY_CONTEXT_ENABLED=1
export MIRA_MEMORY_CONTEXT_AUTH_TOKEN=<your-token-if-needed>
bash tools/mira_light_bridge/start_bridge.sh
```

桥接健康检查：

```bash
curl http://127.0.0.1:9783/health
```

## 第 3 步：验证 scene outcome 能写入 memory-context

先触发一个场景：

```bash
curl http://127.0.0.1:9783/v1/mira-light/run-scene \
  -H "Authorization: Bearer $MIRA_LIGHT_BRIDGE_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"scene":"farewell","async":false}'
```

你应该在 bridge 日志里看到：

```text
[memory] ...
```

并在 `memory-context` 那边看到对应 write 请求。

当前已经有测试覆盖这件事：

- [`tests/test_embodied_memory.py`](/Users/Zhuanz/Documents/Github/Mira-Light/tests/test_embodied_memory.py)

## 第 4 步：验证 device report 会写 working / episodic memory

模拟一个设备状态：

```bash
curl http://127.0.0.1:9783/v1/mira-light/device/status \
  -H "Authorization: Bearer $MIRA_LIGHT_BRIDGE_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "deviceId": "mira-light-001",
    "scene": "farewell",
    "playing": false,
    "ledMode": "warm"
  }'
```

模拟一个设备错误事件：

```bash
curl http://127.0.0.1:9783/v1/mira-light/device/event \
  -H "Authorization: Bearer $MIRA_LIGHT_BRIDGE_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "deviceId": "mira-light-001",
    "eventType": "warning",
    "scene": "track_target",
    "detail": "target lost too often"
  }'
```

按当前策略：

- `hello / heartbeat` 会被跳过
- `status` 会写 working memory
- `event` 会写 episodic，严重事件还会补 working memory

## Wave 2 实现：让 Mira 在 prompt-pack 里看到 Mira-Light

## 第 5 步：在 Mira_v3 打开 prompt-pack 与 session-memory

在 `Mira_v3` 的 `.env.local` 或相应运行时环境中设置：

```bash
MIRA_OPENCLAW_MEMORY_CONTEXT_ENABLED=true
MIRA_OPENCLAW_MEMORY_CONTEXT_URL=http://127.0.0.1:3301/v1/memory/context
MIRA_OPENCLAW_SESSION_MEMORY_ENABLED=true
MIRA_OPENCLAW_SESSION_MEMORY_MAX_CHARS=1200
MIRA_OPENCLAW_PROMPT_PACK_ENABLED=true
MIRA_OPENCLAW_PROMPT_PACK_TIMEOUT_MS=1500
MIRA_LINGZHU_PROMPT_PACK_ADDITIONAL_USER_IDS=mira-light-bridge
```

这一步的关键不是 `memory_context_url` 本身，而是：

```bash
MIRA_LINGZHU_PROMPT_PACK_ADDITIONAL_USER_IDS=mira-light-bridge
```

因为这决定了 Mira 在请求前拉 prompt-pack 时，是否会把 `Mira-Light` 写进去的那些 embodied outcomes 一起拉进 prompt。

## 第 6 步：验证 Lingzhu adapter 真正拉到了 Mira-Light 的 memory

验证逻辑应该是：

1. 先让 `Mira-Light` 写几条 scene outcome / device event
2. 再触发一次 Mira 对话请求
3. 检查 prompt-pack 是否包含来自 `mira-light-bridge` 的内容

你可以先从测试和日志入手：

- `Mira_v3/services/lingzhu-live-adapter/tests/server.test.js`
- `Mira_v3/services/memory-context/tests/prompt-pack.test.ts`

当前这轮更新已经说明，这条路在 `Mira_v3` 侧是有实现基础的。

## Wave 3 实现：给 Mira-Light 增加 session-state / next-step 层

这一层现在已经有了第一版 skeleton，实现点包括：

- `EmbodiedMemoryClient` 已新增：
  - `get_current_session_note(...)`
  - `update_session_note(...)`
  - `record_scene_session_state(...)`
  - `record_tracking_session_state(...)`
- `MiraLightRuntime` 在 scene `started / completed / stopped / failed` 时会写 `mira-light-runtime` session note
- `vision_runtime_bridge.py` 在处理 vision event 时会写 `mira-light-vision` session note

当前相关实现文件：

- [`tools/mira_light_bridge/embodied_memory_client.py`](/Users/Zhuanz/Documents/Github/Mira-Light/tools/mira_light_bridge/embodied_memory_client.py)
- [`scripts/mira_light_runtime.py`](/Users/Zhuanz/Documents/Github/Mira-Light/scripts/mira_light_runtime.py)
- [`scripts/vision_runtime_bridge.py`](/Users/Zhuanz/Documents/Github/Mira-Light/scripts/vision_runtime_bridge.py)
- [`tests/test_embodied_memory.py`](/Users/Zhuanz/Documents/Github/Mira-Light/tests/test_embodied_memory.py)
- [`tests/test_vision_runtime_bridge.py`](/Users/Zhuanz/Documents/Github/Mira-Light/tests/test_vision_runtime_bridge.py)

## 当前还剩下的缺口

现在 `Mira-Light` 写入 `memory-context` 的主要内容已经包含：

- `execution_outcome`
- `scene_state`
- `device-status`
- `device-event`
- scene lifecycle session note
- tracking session note

也就是说，它已经不再只是：

```text
episodic + working memory producer
```

但它仍然还不是：

```text
full task-capture and proactive-state producer
```

## 这版 skeleton 现在会写什么

当前 session note 结构已经会写类似下面的内容：

```json
{
  "title": "Mira-Light tracking rehearsal",
  "currentState": "track_target 目前仍是 surrogate choreography，真实视觉闭环未接入",
  "nextStep": "把 target extractor 的 horizontal_zone / vertical_zone 映射到 servo1 / servo4",
  "taskSpec": "完成从 JPEG 帧到真实 track_target 控制回路",
  "relevantFiles": [
    "scripts/track_target_event_extractor.py",
    "scripts/vision_runtime_bridge.py",
    "scripts/scenes.py"
  ],
  "errors": [
    "target jitter too high in current heuristic"
  ],
  "keyResults": [
    "surrogate choreography already runs"
  ],
  "worklog": [
    "added scene outcome writing",
    "connected additionalUserIds=mira-light-bridge"
  ]
}
```

推荐解释：

- `mira-light-runtime` session id
  负责描述当前 scene 的运行状态
- `mira-light-vision` session id
  负责描述 vision / tracking 侧的当前判断

## 当前实现策略

当前策略是有意克制的：

1. 不在每个 step 都写 session note
2. 只在关键点更新：
   - scene start
   - scene completed / stopped / failed
   - vision event 处理

这样做的原因是：

- 避免过量写入
- 避免把 session note 变成噪声日志
- 先建立“会话状态骨架”，而不是一上来就做完整任务系统

## 下一步推荐的代码扩展方向

### A. 给 `EmbodiedMemoryClient` 增加 session-memory client

这一项已经完成第一版。

下一步不是“再加接口”，而是：

- 提升 note 内容质量
- 增加更好的 merge 策略
- 避免 keyResults / worklog 变得过度冗长

### B. 在 `MiraLightRuntime._finish_run()` 里构建 session note

这一项已经完成第一版。

下一步可以补的是：

- scene-specific `relevantFiles`
- scene-specific `nextStep`
- 更明确的 operator follow-up hint

### C. 在 `vision_runtime_bridge.py` 里对 tracking 状态写 session note

这一项也已经完成第一版。

下一步可以补的是：

- 把 `target jitter` / `quality degrade` 明确写入 `errors`
- 区分 surrogate 跟随与真实闭环跟随
- 对 “target lost too often” 给出更明确的 `nextStep`

## 推荐执行顺序

如果你现在就要开始干，我建议按这个顺序：

### 第 1 阶段：打通 memory write 基础链路

1. 启动 `Mira_v3/services/memory-context`
2. 启动 `Mira-Light bridge`
3. 触发一个 scene
4. 验证 scene outcome 写入
5. 上报一个设备状态 / 错误
6. 验证 device write 生效

### 第 2 阶段：打开 prompt-pack

1. 打开 `Mira_v3` 的：
   - `MIRA_OPENCLAW_MEMORY_CONTEXT_ENABLED=true`
   - `MIRA_OPENCLAW_SESSION_MEMORY_ENABLED=true`
   - `MIRA_OPENCLAW_PROMPT_PACK_ENABLED=true`
   - `MIRA_LINGZHU_PROMPT_PACK_ADDITIONAL_USER_IDS=mira-light-bridge`
2. 触发一次 Mira 对话
3. 检查 prompt pack 是否包含 `Mira-Light` 写入内容

### 第 3 阶段：实现 session-state 层

1. 强化 `session note` 内容质量
2. 在更多关键 tracking 状态变化时更新
3. 再次验证 prompt-pack 是否能把这些信息带进去
4. 逐步把 session-state 推进成 task-capture skeleton

## 每一步的验收标准

### 验收 A：memory-context 通了

判定标准：

- `Mira-Light` 触发场景后，`memory-context` 收到 `/v1/memory/write`

### 验收 B：prompt-pack 带上了 Mira-Light

判定标准：

- 在 Mira 请求前，prompt-pack 中能看到 `mira-light-bridge` writer 的关键信息

### 验收 C：Mira 真的开始“记得灯”

判定标准：

- Mira 在相关对话中能引用：
  - 最近 scene 成败
  - 最近设备 warning/error
  - 当前 embodied 状态

### 验收 D：session-state 生效

判定标准：

- Prompt 中不只是“发生过什么”，还出现：
  - 当前状态
  - 下一步
  - 相关文件

当前第一版 skeleton 已经满足这条的基础形态，但还需要在真实运行环境里验证 prompt-pack 的最终注入效果。

## 当前最值得优先实现的两件事

如果时间有限，最值得做的是：

1. **先把 `Mira-Light -> memory-context -> prompt-pack` 打通**
2. **再做 `track_target` 的真实闭环**

原因：

- 第一件事能让 Mira 开始“记得灯”
- 第二件事能让灯开始“真的看见”

这两个一旦成立，Mira-Light 才会真正从“会动的外设”变成“具身上下文生产者”。

## 一句话总结

当前最合理的路线不是让 `Mira-Light` 自己变成一个完整的 Mira runtime，而是：

```text
Mira-Light 负责产生具身事件
-> memory-context 负责存储与组织
-> prompt-pack 负责把关键状态重新注入 Mira
-> OpenClaw 负责执行
```

而这条链路，当前仓库和 `Mira_v3` 仓库里都已经有了第一版落点，现在差的是把它真正按步骤跑起来。 
