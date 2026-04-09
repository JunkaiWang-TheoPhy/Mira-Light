# Release Environment Reference

## 目的

这份文档把 release 当前会用到的环境变量按层整理出来。

重点不是列出所有可能配置，而是回答：

- 这个变量归谁管
- 默认值是什么
- 什么时候应该改

## Shared Runtime Target

### `MIRA_LIGHT_LAMP_BASE_URL`

- 默认值：`http://172.20.10.3`
- 归属：bridge runtime
- 用途：bridge 当前要去访问的灯地址

### `MIRA_LIGHT_DRY_RUN`

- 默认值：`0`
- 归属：bridge runtime
- 用途：是否让 runtime 只打印动作而不真正打灯

## Director Console

### `MIRA_LIGHT_CONSOLE_HOST`

- 默认值：`127.0.0.1`
- 用途：导演台 HTTP 服务绑定地址

### `MIRA_LIGHT_CONSOLE_PORT`

- 默认值：`8765`
- 用途：导演台 HTTP 服务端口

### `MIRA_LIGHT_CONSOLE_BRIDGE_URL`

- 默认值：`http://127.0.0.1:9783`
- 用途：导演台当前要代理到哪个 bridge

### `MIRA_LIGHT_CONSOLE_BRIDGE_TIMEOUT_SECONDS`

- 默认值：`5`
- 用途：导演台代理请求 bridge 时的超时

### `MIRA_LIGHT_CONSOLE_BRIDGE_TOKEN_ENV`

- 默认值：`MIRA_LIGHT_BRIDGE_TOKEN`
- 用途：导演台从哪个环境变量读取 bridge bearer token

## Bridge

### `MIRA_LIGHT_BRIDGE_HOST`

- 默认值：`127.0.0.1`
- 用途：bridge 本地监听地址

### `MIRA_LIGHT_BRIDGE_PORT`

- 默认值：`9783`
- 用途：bridge 本地监听端口

### `MIRA_LIGHT_BRIDGE_TOKEN`

- 默认值：`test-token`
- 用途：bridge `/v1/...` 鉴权 token

### `MIRA_LIGHT_BRIDGE_URL`

- 默认值：`http://127.0.0.1:9783`
- 用途：给 console 或插件引用的 bridge URL

### `MIRA_LIGHT_BRIDGE_TIMEOUT_MS`

- 默认值：`5000`
- 用途：主要给插件使用的请求超时配置

## Receiver

### `MIRA_LIGHT_RECEIVER_HOST`

- 默认值：`0.0.0.0`
- 用途：receiver 监听地址

### `MIRA_LIGHT_RECEIVER_PORT`

- 默认值：`9784`
- 用途：receiver 监听端口

### `MIRA_LIGHT_RECEIVER_SAVE_ROOT`

- 默认值：`${HOME}/Documents/Mira-Light-Runtime/simple-receiver`
- 用途：receiver 保存状态与上传文件的根目录

## Python / Local Stack

### `MIRA_LIGHT_PYTHON`

- 默认值：空
- 用途：显式指定 release 里脚本要用的 Python
- 备注：如果未设置，脚本会优先使用 `.venv/bin/python`
- 要求：解释器必须是 Python `3.10+`

### `MIRA_LIGHT_STACK_LOG_ROOT`

- 默认值：`.mira-light-runtime/local-stack`
- 用途：`start_local_stack.sh` 写 bridge/receiver 后台日志的位置

### `MIRA_LIGHT_STACK_WAIT_SECONDS`

- 默认值：`15`
- 用途：`start_local_stack.sh` 等待健康检查的最长秒数

## Bootstrap / OpenClaw

### `MIRA_LIGHT_SKIP_OPENCLAW_INSTALL`

- 默认值：`0`
- 用途：一键安装时是否跳过本机 OpenClaw 插件安装

## 最常见的改法

### 真机启动

```bash
export MIRA_LIGHT_LAMP_BASE_URL=http://192.168.0.123
bash scripts/start_local_stack.sh
```

### dry-run 启动

```bash
export MIRA_LIGHT_DRY_RUN=1
bash scripts/start_local_stack.sh
```

### 改 bridge token

```bash
export MIRA_LIGHT_BRIDGE_TOKEN=my-token
bash scripts/start_local_stack.sh --bridge-token "$MIRA_LIGHT_BRIDGE_TOKEN"
```

## 一句话总结

最重要的区分是：

- 灯地址和 dry-run 归 bridge runtime
- 导演台只关心 bridge URL
- receiver 独立运行，不参与控制链
