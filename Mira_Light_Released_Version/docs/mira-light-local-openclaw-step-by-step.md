# Mira Light 接入本机 OpenClaw 逐步操作手册

## 文档目的

这份文档专门回答：

> 如何把当前这盏 `ESP32 Mira Light` 接到你本机已经安装好的 `OpenClaw`。

这里不再停留在架构层，而是给出一步一步的操作顺序。

## 先说当前已确认事实

本机当前已经确认：

- 本机 `openclaw` 可执行文件存在：

```text
/Users/Zhuanz/.local/bin/openclaw
```

- 当前版本：

```text
OpenClaw 2026.4.2
```

- 当前本机配置文件路径：

```text
~/.openclaw/openclaw.json
```

- 当前本机 OpenClaw gateway 运行模式是：

```text
gateway.mode = local
gateway.port = 18889
```

这说明：

> 你不是从零开始装 OpenClaw，而是已经有一个本机 OpenClaw 环境，现在要做的是把 `Mira Light` 接进这个现有环境。

## 一句话接入原则

不要让本机 OpenClaw 直接拼 `curl` 去访问 `ESP32`。

更推荐的路径是：

```text
OpenClaw
-> mira-light-bridge 插件
-> 本机 bridge
-> ESP32
```

这样做的好处是：

- 参数边界清楚
- 本地 scene / pose / reset / stop 都能统一暴露成工具
- 以后迁到云端 OpenClaw 时，不用重做一套逻辑

## 这条链路里有哪些现成文件

### 1. 场景与执行层

- [`scripts/scenes.py`](/Users/Zhuanz/Documents/Github/Mira-Light/scripts/scenes.py)
- [`scripts/mira_light_runtime.py`](/Users/Zhuanz/Documents/Github/Mira-Light/scripts/mira_light_runtime.py)
- [`scripts/booth_controller.py`](/Users/Zhuanz/Documents/Github/Mira-Light/scripts/booth_controller.py)

### 2. 本地 bridge

- [`tools/mira_light_bridge/bridge_server.py`](/Users/Zhuanz/Documents/Github/Mira-Light/tools/mira_light_bridge/bridge_server.py)
- [`tools/mira_light_bridge/start_bridge.sh`](/Users/Zhuanz/Documents/Github/Mira-Light/tools/mira_light_bridge/start_bridge.sh)
- [`tools/mira_light_bridge/bridge_config.json`](/Users/Zhuanz/Documents/Github/Mira-Light/tools/mira_light_bridge/bridge_config.json)

### 3. OpenClaw 插件

- [`tools/mira_light_bridge/openclaw_mira_light_plugin/openclaw.plugin.json`](/Users/Zhuanz/Documents/Github/Mira-Light/tools/mira_light_bridge/openclaw_mira_light_plugin/openclaw.plugin.json)
- [`tools/mira_light_bridge/openclaw_mira_light_plugin/index.mjs`](/Users/Zhuanz/Documents/Github/Mira-Light/tools/mira_light_bridge/openclaw_mira_light_plugin/index.mjs)

## 接入步骤

## 第 1 步：先确认真实灯可达

这一步永远排在最前面。

不要先碰 OpenClaw。

先确认：

```bash
curl http://<真实灯IP>/status
curl http://<真实灯IP>/led
curl http://<真实灯IP>/actions
```

只有这三条成功，说明：

- 灯在线
- 电脑和灯在同一网络平面
- 设备 HTTP 服务正常

如果这一步不通，请先看：

- [`mira-light-device-connection-troubleshooting.md`](/Users/Zhuanz/Documents/Github/Mira-Light/docs/mira-light-device-connection-troubleshooting.md)

## 第 2 步：启动本地 bridge

bridge 的职责是把“裸设备 API”包装成 OpenClaw 更适合调用的工具面。

### 2.1 设置 bridge token

```bash
export MIRA_LIGHT_BRIDGE_TOKEN=test-token
```

### 2.2 启动 bridge

```bash
zsh tools/mira_light_bridge/start_bridge.sh
```

### 2.3 验证 bridge 健康

```bash
curl http://127.0.0.1:9783/health
```

预期应该返回 `ok=true`。

### 2.4 再验证 scene / status API

```bash
curl http://127.0.0.1:9783/v1/mira-light/scenes \
  -H "Authorization: Bearer $MIRA_LIGHT_BRIDGE_TOKEN"

curl http://127.0.0.1:9783/v1/mira-light/status \
  -H "Authorization: Bearer $MIRA_LIGHT_BRIDGE_TOKEN"
```

如果这一层不通，先不要继续碰 OpenClaw 插件。

## 第 3 步：准备 OpenClaw 插件目录

当前插件源目录在：

[`tools/mira_light_bridge/openclaw_mira_light_plugin/`](/Users/Zhuanz/Documents/Github/Mira-Light/tools/mira_light_bridge/openclaw_mira_light_plugin/index.mjs)

本机 OpenClaw 的扩展目录当前存在于：

```text
~/.openclaw/extensions/
```

建议把插件复制到：

```text
~/.openclaw/extensions/mira-light-bridge/
```

例如：

```bash
mkdir -p ~/.openclaw/extensions/mira-light-bridge
cp tools/mira_light_bridge/openclaw_mira_light_plugin/* ~/.openclaw/extensions/mira-light-bridge/
```

说明：

- 当前插件目录只有少量文件，直接复制即可
- 后续如果改了插件代码，再重新覆盖同步一次

## 第 4 步：备份本机 OpenClaw 配置

在修改本机 OpenClaw 配置前，建议先备份：

```bash
cp ~/.openclaw/openclaw.json ~/.openclaw/openclaw.json.bak.mira-light
```

## 第 5 步：把插件注册进本机 OpenClaw

你当前 `~/.openclaw/openclaw.json` 里已经有：

- `plugins.allow`
- `plugins.load.paths`
- `plugins.entries`

所以 `mira-light-bridge` 最合理的接入方式是：

### 5.1 在 `plugins.allow` 中加入

```json
"mira-light-bridge"
```

### 5.2 在 `plugins.entries` 中加入

```json
"mira-light-bridge": {
  "enabled": true,
  "config": {
    "bridgeBaseUrl": "http://127.0.0.1:9783",
    "bridgeToken": "test-token",
    "requestTimeoutMs": 5000
  }
}
```

说明：

- `bridgeBaseUrl` 指向本机 loopback bridge
- `bridgeToken` 要和环境变量一致
- `requestTimeoutMs` 先用默认值即可

## 第 6 步：重启本机 OpenClaw gateway

修改配置后，需要让 OpenClaw 重新加载插件配置。

如果你是手动启动本机 gateway，就重启当前 gateway 进程。  
如果由其它系统守护，请按当前环境的实际方式重启。

## 第 7 步：验证本机 OpenClaw 是否真正看到 Mira Light 工具

这一层的目标不是“页面漂亮”，而是确认：

> 本机 OpenClaw 已经能把 Mira Light 当作受控工具集使用。

建议至少验证下面这些工具概念：

- `mira_light_list_scenes`
- `mira_light_runtime_status`
- `mira_light_status`
- `mira_light_run_scene`
- `mira_light_stop`
- `mira_light_reset`
- `mira_light_set_led`
- `mira_light_control_joints`

## 第 8 步：先让 OpenClaw 调 scene，不要直接调裸关节

虽然插件也支持：

- `mira_light_control_joints`

但推荐在接入初期优先使用：

- `mira_light_run_scene`

优先暴露这些稳定场景：

- `wake_up`
- `curious_observe`
- `touch_affection`
- `celebrate`
- `farewell`
- `sleep`

原因：

- scene 的体验一致性更好
- 不容易乱打角度
- 更适合展位演示

## 第 9 步：把本机导演台作为辅助验证界面

本机 OpenClaw 接入不是为了取代导演台。

导演台仍然很有价值，因为它能帮助你：

- 看当前状态
- 看最近错误
- 快速 reset
- 快速回 neutral / sleep

所以接入本机 OpenClaw 后，导演台依然建议保留。

## 一句话收尾

本机 OpenClaw 接 Mira Light 的核心并不是：

```text
OpenClaw -> 直接访问 ESP32
```

而是：

```text
OpenClaw -> 本机 bridge -> ESP32
```

先跑通真实灯，再跑通 bridge，再让 OpenClaw 接插件，这才是最稳的本机接法。

