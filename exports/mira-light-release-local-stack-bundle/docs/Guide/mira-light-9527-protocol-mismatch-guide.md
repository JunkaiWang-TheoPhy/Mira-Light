# Mira Light 9527 端口协议不匹配说明

更新时间：2026-04-09

## 结论

`192.168.31.10:9527` 当前不是一个给 `MiraLightRuntime` 直接使用的 HTTP REST 设备端口，而是一个接收原始舵机帧的 TCP 端口。

因此：

- 向它发送原始指令，例如 `#003P1500T1000!`，设备会正常响应。
- 但如果把它直接当作 `Lamp Base URL`，现有导演台 / runtime 会自动发出 `GET /status`、`GET /led`、`GET /actions` 这类 HTTP 请求。
- 设备会把这些 HTTP 文本当成舵机帧解析，于是报出 `ERR,invalid servo frame: GET /status HTTP/1.1` 之类错误。

## 现场现象

在 2026-04-09 的联调里，设备日志出现了如下特征：

- 收到 `GET /status HTTP/1.1`
- 收到 `GET /led HTTP/1.1`
- 收到 `GET /actions HTTP/1.1`
- 收到 `Host: 192.168.31.10:9527`
- 收到 `Accept-Encoding: identity`
- 收到 `User-Agent: Python-urllib/3.9`
- 对这些内容返回 `ERR,invalid servo frame: ...`

随后，当直接使用 `nc` 发送原始舵机帧时，设备可以正常执行并返回成功：

```bash
printf '#003P1500T1000!\n' | nc 192.168.31.10 9527
```

设备返回：

```text
OK,#003P1500T1000!,15
```

这说明：

- `9527` 端口本身是通的
- 设备能理解原始帧协议
- 问题不在网络是否可达
- 问题在“访问协议不匹配”

## 为什么会发生

当前仓库中的 `MiraLightRuntime` 默认控制模型是 ESP32 REST API，核心接口包括：

- `GET /status`
- `GET /led`
- `GET /actions`
- `POST /control`
- `POST /led`
- `POST /action`
- `POST /action/stop`
- `POST /reset`

也就是说，当前 runtime 期待的设备是“HTTP 设备”。

而 `192.168.31.10:9527` 这台灯目前暴露的是“原始 TCP 舵机口”，期待的数据是：

```text
#003P1500T1000!
{#001P2000T1000!#003P0833T2000!}
```

它并不会把下面这种内容当成合法控制协议：

```text
GET /status HTTP/1.1
Host: 192.168.31.10:9527
Accept-Encoding: identity
User-Agent: Python-urllib/3.9
```

所以设备会把这些 HTTP 请求行和 Header 逐行识别成“非法舵机帧”。

## 已验证事实

### 1. 设备确实接受原始 TCP 舵机帧

测试命令：

```bash
printf '#003P1500T1000!\n' | nc 192.168.31.10 9527
```

测试结果：

```text
OK,#003P1500T1000!,15
```

### 2. 当前 runtime 的轮询会自动发出 HTTP 请求

导演台和 runtime 会周期性请求：

- `/status`
- `/led`
- `/actions`

因此只要把 `Lamp Base URL` 指到 `http://192.168.31.10:9527`，设备端就会持续收到不符合协议的 HTTP 文本。

### 3. 当前 bridge/runtime 不能直接把 9527 当成 HTTP 设备

这不是“参数小问题”，而是协议层不兼容。

## 正确理解

`192.168.31.10:9527` 应该被视为：

- 原始 TCP 控制入口
- servo frame / frame bundle 入口

而不是：

- 现有 Mira runtime 可直接探测 `/status`、`/led`、`/actions` 的 HTTP Base URL

## 处理建议

当前有两条可行路线。

### 路线 A：找到设备真正的 HTTP API 端口

如果这台灯同时还有一个 HTTP 控制端口，那么现有 runtime 应该继续连接那个 HTTP 端口，而不是 `9527`。

适用情况：

- 设备其实同时支持 REST API
- `9527` 只是底层舵机透传口

### 路线 B：给 bridge 增加 “HTTP -> raw TCP servo frame” 适配层

如果 `9527` 就是唯一对外控制入口，那么需要修改本地 bridge：

- 对外仍然保留现有 HTTP 接口
- 对内把 `/control`、`/action` 等高层调用翻译成原始 TCP 舵机帧
- 不再直接对灯发送 `GET /status`、`GET /led`、`GET /actions`

适用情况：

- 设备只有 raw TCP 控制口
- 希望保留当前导演台、runtime、scene 系统不大改

## 当前建议

在没有完成 bridge 适配之前，不要把 `192.168.31.10:9527` 直接当成现有 runtime 的 HTTP `Lamp Base URL`。

否则会持续出现：

- `ERR,invalid servo frame: GET /status HTTP/1.1`
- `ERR,invalid servo frame: GET /led HTTP/1.1`
- `ERR,invalid servo frame: GET /actions HTTP/1.1`

## 后续实现方向

如果继续接入 `9527`，推荐做一个专门的本地适配器，例如：

1. 导演台仍访问本地 bridge，例如 `127.0.0.1:9783`
2. bridge 内部把高层命令转换为 raw servo frame
3. bridge 通过 TCP 将 frame 发送到 `192.168.31.10:9527`
4. 仅在确实有设备状态协议时，才实现 status/led/actions 查询

这样可以保留：

- 10 个场景调度
- 导演台
- 视觉触发
- 现有 runtime 结构

同时兼容新的台灯控制协议。
