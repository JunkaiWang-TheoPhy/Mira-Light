# Mira Light 本机 OpenClaw 插件安装与配置说明

## 文档目的

这份文档只聚焦一件事：

> 如何把 `mira-light-bridge` 插件装进本机 `OpenClaw`，并完成最小配置。

它是 [`mira-light-local-openclaw-step-by-step.md`](/Users/Zhuanz/Documents/Github/Mira-Light/docs/mira-light-local-openclaw-step-by-step.md) 的插件专项补充。

## 当前本机 OpenClaw 已确认信息

本机已确认：

- OpenClaw 可执行文件：

```text
/Users/Zhuanz/.local/bin/openclaw
```

- OpenClaw 版本：

```text
OpenClaw 2026.4.2
```

- 本机配置文件：

```text
~/.openclaw/openclaw.json
```

- 本机扩展目录：

```text
~/.openclaw/extensions/
```

## 当前插件源目录

仓库内插件源目录是：

[`tools/mira_light_bridge/openclaw_mira_light_plugin/`](/Users/Zhuanz/Documents/Github/Mira-Light/tools/mira_light_bridge/openclaw_mira_light_plugin/index.mjs)

关键文件：

- [`openclaw.plugin.json`](/Users/Zhuanz/Documents/Github/Mira-Light/tools/mira_light_bridge/openclaw_mira_light_plugin/openclaw.plugin.json)
- [`index.mjs`](/Users/Zhuanz/Documents/Github/Mira-Light/tools/mira_light_bridge/openclaw_mira_light_plugin/index.mjs)
- [`package.json`](/Users/Zhuanz/Documents/Github/Mira-Light/tools/mira_light_bridge/openclaw_mira_light_plugin/package.json)

插件 ID 是：

```text
mira-light-bridge
```

## 插件职责

插件不是直接理解自然语言，它负责把本地 bridge 暴露成工具。

当前代码里已经实现的工具包括：

- `mira_light_list_scenes`
- `mira_light_runtime_status`
- `mira_light_status`
- `mira_light_run_scene`
- `mira_light_stop`
- `mira_light_reset`
- `mira_light_set_led`
- `mira_light_control_joints`

## 安装步骤

## 第 1 步：确认本地 bridge 先能工作

插件之前必须先有 bridge。

例如：

```bash
export MIRA_LIGHT_BRIDGE_TOKEN=test-token
zsh tools/mira_light_bridge/start_bridge.sh
```

验证：

```bash
curl http://127.0.0.1:9783/health
```

## 第 2 步：创建本机插件目录

```bash
mkdir -p ~/.openclaw/extensions/mira-light-bridge
```

## 第 3 步：复制插件文件

```bash
cp tools/mira_light_bridge/openclaw_mira_light_plugin/* \
  ~/.openclaw/extensions/mira-light-bridge/
```

复制后，目标目录里至少应有：

- `openclaw.plugin.json`
- `index.mjs`
- `package.json`

## 第 4 步：备份 OpenClaw 配置

```bash
cp ~/.openclaw/openclaw.json ~/.openclaw/openclaw.json.bak.mira-light
```

## 第 5 步：修改 `~/.openclaw/openclaw.json`

你当前配置里已经有：

- `plugins.allow`
- `plugins.entries`
- `plugins.load.paths`

所以只需要把 `mira-light-bridge` 补进去。

### 5.1 `plugins.allow`

确保包含：

```json
"mira-light-bridge"
```

### 5.2 `plugins.entries`

新增：

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

## 推荐配置说明

### `bridgeBaseUrl`

本机接法推荐：

```text
http://127.0.0.1:9783
```

不要直接填 `ESP32` 的私网地址。

### `bridgeToken`

应与本地 bridge 环境变量一致：

```bash
export MIRA_LIGHT_BRIDGE_TOKEN=test-token
```

### `requestTimeoutMs`

推荐初始值：

```text
5000
```

## 配置片段示例

下面是一个最小示例，仅展示插件相关部分。

```json
{
  "plugins": {
    "allow": [
      "scientify",
      "mira-light-bridge"
    ],
    "entries": {
      "scientify": {
        "enabled": true
      },
      "mira-light-bridge": {
        "enabled": true,
        "config": {
          "bridgeBaseUrl": "http://127.0.0.1:9783",
          "bridgeToken": "test-token",
          "requestTimeoutMs": 5000
        }
      }
    }
  }
}
```

## 第 6 步：重启本机 OpenClaw

修改配置后，需要让当前 OpenClaw gateway 重新加载配置。

重启后，再去验证插件是否生效。

## 第 7 步：验证插件行为

建议至少验证以下能力：

### 1. 读取场景列表

确认插件可以读到本地 bridge 的 scene 数据。

### 2. 读取运行时状态

确认插件可以读到：

- 当前场景
- 当前状态
- 最近错误

### 3. 执行一个稳定场景

推荐先试：

- `wake_up`
- `farewell`
- `sleep`

而不要一开始就试：

- 跟踪
- 语音理解
- 叹气检测

## 推荐先暴露给 OpenClaw 的能力

如果你想先让本机 OpenClaw 稳稳地控制灯，推荐优先顺序是：

### 第一组：只读

- `mira_light_list_scenes`
- `mira_light_runtime_status`
- `mira_light_status`

### 第二组：高层动作

- `mira_light_run_scene`
- `mira_light_stop`
- `mira_light_reset`

### 第三组：底层控制

- `mira_light_set_led`
- `mira_light_control_joints`

## 常见问题

### 问题 1：为什么不让 OpenClaw 直接访问 `http://<lamp-ip>`？

因为：

- 边界不清晰
- 后续接云端时要重做
- scene / runtime / operator 行为难统一

### 问题 2：本机 bridge 明明就在本机，为何还要 token？

因为：

- 现在就把边界做好，后面迁云端更容易
- 本机调试和未来远端方案保持一致

### 问题 3：本机 OpenClaw 接入后还要不要保留导演台？

要。

导演台更适合：

- 现场操作
- 观察状态
- reset / 回姿态
- operator 救场

OpenClaw 更适合：

- 自然语言调用
- 工具编排
- 场景选择

## 一句话总结

本机 OpenClaw 插件安装的最小路线是：

```text
先确认 bridge
-> 复制插件到 ~/.openclaw/extensions/mira-light-bridge/
-> 修改 ~/.openclaw/openclaw.json
-> 重启 OpenClaw
-> 验证工具可用
```

