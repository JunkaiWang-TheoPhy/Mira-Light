# Mira Light OpenClaw 插件工具与动态场景参数说明

## 文档目的

这份文档专门说明当前 `mira-light-bridge` OpenClaw 插件已经暴露了哪些工具，以及这些工具应该如何使用。

它重点回答 4 个问题：

1. OpenClaw 现在到底能调用 Mira Light 的哪些工具
2. 哪些工具适合做高层 scene 触发，哪些只适合做底层校准
3. `mira_light_run_scene` 现在如何携带 `context` 和 `cueMode`
4. 什么时候该用 `run_scene`，什么时候该用 `trigger`、`apply_pose` 或 `control_joints`

如果你先看安装步骤，再回来看工具细节，建议先读：

- [`mira-light-local-openclaw-step-by-step.md`](/Users/huhulitong/Documents/GitHub/Mira-Light/docs/mira-light-local-openclaw-step-by-step.md)
- [`mira-light-local-openclaw-plugin-install-config.md`](/Users/huhulitong/Documents/GitHub/Mira-Light/docs/mira-light-local-openclaw-plugin-install-config.md)

## 当前结构

当前推荐调用链路仍然是：

```text
OpenClaw
-> mira-light-bridge plugin
-> 本地 bridge
-> runtime / safety
-> 真实灯或 mock 灯
```

也就是说：

- OpenClaw 不应该直接理解底层硬件协议
- 插件不应该直接访问裸 ESP32 IP
- 桥接层负责提供稳定的 scene-first API

插件代码位置：

- [`tools/mira_light_bridge/openclaw_mira_light_plugin/index.mjs`](/Users/huhulitong/Documents/GitHub/Mira-Light/tools/mira_light_bridge/openclaw_mira_light_plugin/index.mjs)
- [`tools/mira_light_bridge/openclaw_mira_light_plugin/openclaw.plugin.json`](/Users/huhulitong/Documents/GitHub/Mira-Light/tools/mira_light_bridge/openclaw_mira_light_plugin/openclaw.plugin.json)

## 当前插件已暴露工具

### 只读工具

- `mira_light_list_scenes`
- `mira_light_runtime_status`
- `mira_light_status`

用途：

- 看有哪些 scene 可用
- 看 runtime 当前状态
- 看灯当前四关节状态

### 高层动作工具

- `mira_light_run_scene`
- `mira_light_trigger_event`
- `mira_light_apply_pose`
- `mira_light_stop`
- `mira_light_stop_to_neutral`
- `mira_light_stop_to_sleep`
- `mira_light_reset`
- `mira_light_speak`

用途：

- 触发主场景
- 触发语义事件
- 切到某个稳定姿态
- 打断并回到安全位
- 做短句播报

### 底层控制工具

- `mira_light_set_led`
- `mira_light_control_joints`

用途：

- 校准
- 调灯
- 验证四个关节

不建议把它们作为主展位交互入口。

## 每个工具应该怎么理解

## 1. `mira_light_run_scene`

这是最推荐的主入口。

适用：

- `wake_up`
- `curious_observe`
- `touch_affection`
- `cute_probe`
- `daydream`
- `standup_reminder`
- `track_target` 的 fallback scene
- `celebrate`
- `farewell`
- `sleep`

当前参数：

```json
{
  "scene": "farewell",
  "async": true,
  "cueMode": "director",
  "context": {
    "departureDirection": "left"
  },
  "allowUnavailable": false
}
```

字段说明：

- `scene`：场景名
- `async`：是否异步执行，默认建议 `true`
- `cueMode`：运行语境
- `context`：动态上下文
- `allowUnavailable`：在 scene 暂未开放时是否强行运行

### `cueMode` 应该怎么用

当前推荐值：

- `scene`
- `director`
- `trigger`
- `operator`

建议口径：

- `scene`：普通场景调用
- `director`：导演台或正式 cue
- `trigger`：来自视觉 / 触摸 / 语音桥的触发
- `operator`：人工应急或校准动作

### `context` 应该怎么用

`context` 是给动态 scene builder 或 runtime 用的。

典型例子：

#### `farewell`

```json
{
  "scene": "farewell",
  "cueMode": "director",
  "context": {
    "departureDirection": "right"
  }
}
```

这会让动态 `farewell` 按右侧离场来生成目送动作。

#### `touch_affection`

```json
{
  "scene": "touch_affection",
  "cueMode": "trigger",
  "context": {
    "handDirection": "left",
    "handDistanceBand": "near"
  }
}
```

当前代码里 `touch_affection` 还主要是固定 choreography，但后续动态版最适合从这里收上下文。

#### `curious_observe`

```json
{
  "scene": "curious_observe",
  "cueMode": "director",
  "context": {
    "targetDirection": "center",
    "targetNear": true
  }
}
```

这个 scene 当前也主要是固定版，但后续方向版 builder 很适合沿用这套参数口径。

## 2. `mira_light_trigger_event`

这是“语义事件入口”。

它不直接要求你知道 scene 怎么编排，而是要求你知道“发生了什么”。

典型输入：

```json
{
  "event": "farewell_detected",
  "payload": {
    "direction": "left",
    "cueMode": "director"
  }
}
```

更适合：

- 视觉桥
- 触摸桥
- 语音桥
- 外部事件系统

而不是人工逐步调姿态。

建议优先用它来承接：

- `farewell_detected`
- `touch_detected`
- `sigh_detected`
- `voice_tired`
- `multi_person_detected`

## 3. `mira_light_apply_pose`

这是“把灯切到一个已知稳定姿态”的工具。

适合：

- 校准
- 排练前复位
- 录 pose
- 确认真实硬件姿态

典型输入：

```json
{
  "pose": "neutral"
}
```

比 `control_joints` 更安全的原因是：

- 它走命名 pose
- 它天然更适合作为“稳定落点”
- 当前 runtime 已经会经过安全层

建议最常用的 pose：

- `neutral`
- `sleep`
- `sleep_ready`
- `wake_half`

## 4. `mira_light_stop_to_neutral`

这是应急工具，不是表演工具。

适用：

- 当前 scene 不对劲
- 需要快速拉回到安全展示位
- 导演想立刻切到下一幕

语义是：

```text
先 stop 当前场景
-> 再 apply neutral
```

## 5. `mira_light_stop_to_sleep`

这也是应急工具，但更适合：

- 结束演示
- 需要立刻收口
- 会场临时中断

语义是：

```text
先 stop 当前场景
-> 再 apply sleep
```

## 6. `mira_light_control_joints`

这是底层关节工具。

适用：

- 校准单个关节
- 真机调角度
- 调试 tracking 输出

不适合：

- 让模型自由发挥复杂表演

典型输入：

```json
{
  "mode": "absolute",
  "servo1": 90,
  "servo4": 92
}
```

## 如何选择工具

最推荐的选择顺序是：

### 第一优先：`run_scene`

当你已经知道要跑哪一幕时，用它。

### 第二优先：`trigger_event`

当你知道“发生了什么”，但不想自己决定 scene 时，用它。

### 第三优先：`apply_pose`

当你只是想切到一个稳定姿态时，用它。

### 第四优先：`control_joints`

只在校准、验证和底层调试时用它。

## 动态场景的推荐用法

## `farewell`

推荐：

```json
{
  "scene": "farewell",
  "cueMode": "director",
  "context": {
    "departureDirection": "left"
  }
}
```

或者：

```json
{
  "event": "farewell_detected",
  "payload": {
    "direction": "left",
    "cueMode": "director"
  }
}
```

如果你已经明确知道要跑 `farewell`，优先 `run_scene`。  
如果你是从视觉桥过来的，优先 `trigger_event`。

## `touch_affection`

当前主路径还是 scene，但未来最适合加在：

```json
{
  "scene": "touch_affection",
  "cueMode": "trigger",
  "context": {
    "handDirection": "right",
    "handDistanceBand": "near"
  }
}
```

## `track_target`

这个场景长期不应该主要靠 `run_scene`。

推荐理解是：

- `run_scene("track_target")` 只作为 fallback choreography
- 真正的 live tracking 应来自视觉桥和 runtime 的连续更新

## Python 调用层

除了 OpenClaw 插件，这一轮仓库还补了一层可复用 Python 封装：

- [`tools/mira_light_bridge/bridge_client.py`](/Users/huhulitong/Documents/GitHub/Mira-Light/tools/mira_light_bridge/bridge_client.py)
- [`tools/mira_light_bridge/bridge_cli.py`](/Users/huhulitong/Documents/GitHub/Mira-Light/tools/mira_light_bridge/bridge_cli.py)

这意味着以后：

- 普通 Python 脚本
- 定时任务
- 外部桥接脚本
- 未来如果真要写 MCP server

都不需要重新手写 `curl`。

最小示例：

```python
from tools.mira_light_bridge import MiraLightBridgeClient

client = MiraLightBridgeClient.from_env()
client.run_scene("farewell", context={"departureDirection": "right"}, cue_mode="director")
client.stop_to_neutral()
```

## 要不要写 MCP

当前阶段，不需要为了 OpenClaw 先写 MCP。

更合适的结构仍然是：

```text
OpenClaw plugin
-> bridge API
-> runtime / safety
-> 硬件
```

只有在你想让：

- ChatGPT
- Claude Desktop
- 其他 MCP host

都共享同一套 Mira Light 工具时，才值得额外做一层 MCP server。

即便那样，也应该是：

```text
MCP server
-> bridge_client.py
-> bridge API
```

而不是让 MCP 直接碰底层设备接口。

## 最后建议

如果你只是想让 OpenClaw 先把 Mira Light 用起来，推荐策略非常简单：

1. 默认优先 `mira_light_run_scene`
2. 动态交互优先 `mira_light_trigger_event`
3. 复位和收口优先 `mira_light_apply_pose` / `mira_light_stop_to_neutral` / `mira_light_stop_to_sleep`
4. `mira_light_control_joints` 只留给校准与调试

这样 OpenClaw 看到的是一套稳定、语义化、可控的工具面，而不是一堆需要现场猜的底层接口。
