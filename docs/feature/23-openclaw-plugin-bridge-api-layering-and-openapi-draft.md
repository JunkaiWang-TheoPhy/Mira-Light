# OpenClaw Plugin, Bridge API, and OpenAPI Draft

## Purpose

这份文档把当前仓库里已经逐渐清晰的接入边界正式压成一个统一口径，回答三个紧挨着的问题：

- `OpenClaw` 现在最适合通过哪一层理解和调用 `Mira Light`
- `API` 应该固定在哪一层，而不是一路向下泄漏到 runtime 内部或总线舵机协议
- 当前阶段到底需不需要先写 `MCP`

它的结论不是抽象建议，而是直接建立在当前仓库已经存在的几层实现之上：

- [20-camera-cv-runtime-bridge-progress.md](./20-camera-cv-runtime-bridge-progress.md)
- [21-bus-servo-protocol-and-four-joint-mapping-memo.md](./21-bus-servo-protocol-and-four-joint-mapping-memo.md)
- [22-bus-servo-adapter-architecture-and-scene-design.md](./22-bus-servo-adapter-architecture-and-scene-design.md)
- [../../tools/mira_light_bridge/README.md](../../tools/mira_light_bridge/README.md)
- [../../tools/mira_light_bridge/openclaw_mira_light_plugin/openclaw.plugin.json](../../tools/mira_light_bridge/openclaw_mira_light_plugin/openclaw.plugin.json)
- [../../tools/mira_light_bridge/openclaw_mira_light_plugin/index.mjs](../../tools/mira_light_bridge/openclaw_mira_light_plugin/index.mjs)

## Current Recommendation

当前最适合仓库方向的主链路不是：

```text
OpenClaw -> 直接理解底层串口协议
```

也不是：

```text
OpenClaw -> 先写 MCP -> 再想办法落到现有 bridge
```

而是：

```text
OpenClaw
-> 本地 plugin
-> bridge HTTP API
-> runtime
-> 设备适配层
-> 真灯
```

更完整地写成当前推荐分层，则是：

```text
OpenClaw
-> mira-light-bridge plugin
-> bridge HTTP API
-> runtime / scene engine / safety
-> bus-servo adapter
-> serial transport or device transport
-> real lamp
```

## Why This Boundary Is The Right One

这条边界不是随意选的，而是和最近两份 feature 文档的结论严格一致。

### 1. CV 到 runtime 之间应该走标准化事件

[20-camera-cv-runtime-bridge-progress.md](./20-camera-cv-runtime-bridge-progress.md)
已经把边界写清楚了：

- 视觉层输出的是标准化 `vision event JSON`
- bridge/runtime 负责 scene 决策与 tracking 更新
- detector 不应该直接写原始舵机控制

这意味着系统上层应该理解：

- `scene_hint`
- `control_hint`
- `target_seen`
- `target_updated`

而不是越过 runtime 去理解底层执行细节。

### 2. 总线舵机协议应该留在设备适配层

[21-bus-servo-protocol-and-four-joint-mapping-memo.md](./21-bus-servo-protocol-and-four-joint-mapping-memo.md)
和
[22-bus-servo-adapter-architecture-and-scene-design.md](./22-bus-servo-adapter-architecture-and-scene-design.md)
已经把另一条边界也写清楚了：

- scene 层继续保留 `servo1 ~ servo4`
- choreography 继续保留 `pose()` / `absolute()` / `nudge()`
- 总线舵机字符串例如 `#000P1500T1000!` 放到 adapter / transport 层翻译

所以真正该让上层理解的不是串口格式，而是一层稳定的语义接口。

## Layered Diagram

下面这张图是当前最推荐的分层方式。

```text
                           Mira Light Recommended Control Stack

  +-------------------+
  | OpenClaw runtime  |
  | model / planner   |
  +---------+---------+
            |
            v
  +-------------------+
  | mira-light-bridge |
  | OpenClaw plugin   |
  | tools + schema    |
  +---------+---------+
            |
            v
  +-------------------------------+
  | Bridge HTTP API               |
  | /v1/mira-light/*              |
  | auth / logs / status / scenes |
  +---------+---------------------+
            |
            v
  +-------------------------------+
  | Runtime                       |
  | scene engine / safety /       |
  | tracking / speak / LED logic  |
  +---------+---------------------+
            |
            v
  +-------------------------------+
  | Bus-Servo Adapter             |
  | servo1~servo4 -> PWM/T        |
  | logical -> physical mapping   |
  +---------+---------------------+
            |
            v
  +-------------------------------+
  | Transport / Device Driver     |
  | serial / ESP32 / mock device  |
  +---------+---------------------+
            |
            v
  +-------------------+
  | Real lamp         |
  | 4 joints + LED    |
  +-------------------+
```

如果把视觉路径也一起标出来，则推荐关系是：

```text
camera / CV
-> standardized vision event JSON
-> runtime bridge
-> runtime
```

而不是：

```text
camera / CV
-> raw servo command
```

## What OpenClaw Should Understand

`OpenClaw` 当前最应该理解的是 plugin 暴露出的工具，而不是总线舵机协议。

仓库里已经存在的 plugin 入口是：

- [../../tools/mira_light_bridge/openclaw_mira_light_plugin/openclaw.plugin.json](../../tools/mira_light_bridge/openclaw_mira_light_plugin/openclaw.plugin.json)
- [../../tools/mira_light_bridge/openclaw_mira_light_plugin/index.mjs](../../tools/mira_light_bridge/openclaw_mira_light_plugin/index.mjs)

当前已经明确暴露的 tool 包括：

- `mira_light_list_scenes`
- `mira_light_runtime_status`
- `mira_light_status`
- `mira_light_run_scene`
- `mira_light_speak`
- `mira_light_set_led`
- `mira_light_control_joints`

这意味着：

- `OpenClaw` 不需要懂 `#000P1500T1000!`
- `OpenClaw` 不需要直接管理四个关节到 bus-servo ID 的映射
- `OpenClaw` 只需要理解 tool 名字、参数 schema、返回值

这正是 plugin 层存在的意义。

## What API Callers Should Understand

普通 API 调用方最适合理解的是 bridge 这一层，而不是 runtime 内部对象。

当前最适合固定成“官方控制面”的接口就是 bridge 这组 endpoint：

- `GET /v1/mira-light/scenes`
- `GET /v1/mira-light/runtime`
- `GET /v1/mira-light/status`
- `POST /v1/mira-light/run-scene`
- `POST /v1/mira-light/speak`
- `POST /v1/mira-light/led`
- `POST /v1/mira-light/control`

推荐原则是：

- 上层只碰语义接口
- runtime 内部结构可以继续演进
- bus-servo 协议可以继续在 adapter 层迭代
- 只要 bridge 语义不漂移，上层接入就不会被硬件细节拖着跑

## Why MCP Is Not The First Step

当前阶段不需要先写 `MCP`，甚至不建议把它作为第一步。

原因不是 `MCP` 没价值，而是当前仓库已经有一条更贴合现状的接入路径：

- `OpenClaw` 走 plugin
- 浏览器 / 导演台走 bridge HTTP API
- runtime 内部继续保留 scene / servo 语义
- 真正的总线舵机协议放到设备适配层翻译

如果只是为了让 `OpenClaw` 正确调用 `Mira Light`，现有 plugin 已经足够承担这项职责。

## When MCP Starts To Make Sense

只有在下面这类场景里，`MCP` 才会开始明显变得值得：

- 不只是 `OpenClaw`，还希望 `ChatGPT`、`Claude`、`Codex` 等都通过同一套工具协议访问 `Mira Light`
- 希望把 `Mira Light` 做成一个独立的通用工具服务，而不是 `OpenClaw` 专属插件
- 需要长期维护“跨 agent 平台统一接入层”

换句话说：

> `MCP` 更像是“统一工具协议层”的升级项，而不是当前把 OpenClaw 接上真灯的必经第一步。

## Recommended Implementation Order

当前最推荐的落地顺序是：

1. 固化 bridge 语义接口，不让上层直接碰底层 bus-servo 协议。
2. 继续使用 `OpenClaw plugin` 暴露 tool schema，让模型理解 `scene / speak / led / joints`。
3. 在设备层新增 `bus-servo adapter`，把 `servo1 ~ servo4` 翻译成 `#IDPxxxxTxxxx!`。
4. 把 bus-servo ID、方向、neutral、PWM 范围都收进独立 mapping 配置。
5. 如果后面出现多客户端统一接入需求，再把 bridge 或 plugin 包成 `MCP server`。

## Minimal OpenAPI Draft

如果当前目标是让“普通 API 调用方”更容易接，而不是先统一 agent 工具协议，那么最值得补的是 OpenAPI，而不是 MCP。

本仓库现在已经补了一版更适合直接交给 `Swagger UI / Redoc` 使用的草案：

- [../mira-light-bridge-openapi-minimal.yaml](../mira-light-bridge-openapi-minimal.yaml)

这份草案当前覆盖最核心的 bridge 接口：

- `GET /health`
- `GET /v1/mira-light/scenes`
- `GET /v1/mira-light/runtime`
- `GET /v1/mira-light/status`
- `POST /v1/mira-light/run-scene`
- `POST /v1/mira-light/speak`
- `POST /v1/mira-light/led`
- `POST /v1/mira-light/control`

同时已经补入：

- 统一的 `401 / 404 / 409 / 500` 响应
- 更明确的 `runtime / scenes / status / speak` 响应 schema
- 鉴权声明
- 示例请求与示例响应

它的定位仍然不是最终定稿，而是：

- 先把 bridge 控制面稳定描述出来
- 给 HTTP 客户端、文档工具、未来测试脚本一个统一起点
- 让后续接口演进有明确基线

## Practical Conclusion

当前最准确的工程口径应该是：

> `Mira Light` 现在最适合的接入主链是 `OpenClaw -> 本地 plugin -> bridge HTTP API -> runtime -> 设备适配层 -> 真灯`。  
> OpenClaw 不需要理解总线舵机协议，只需要理解 plugin 暴露的工具；普通 API 调用方则应面向 bridge 语义接口，而不是 runtime 内部细节。  
> 在当前阶段，优先补强 bridge 语义和 OpenAPI 文档，比先写 MCP 更符合仓库实际演进方向。
