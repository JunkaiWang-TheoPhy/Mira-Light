# Mira Light 路由器中转枢纽实施指南

## 文档目的

这份文档把“路由器作为中转枢纽接入 OpenClaw”的方案展开成可执行步骤。

实施目标是：

- 不把 `ESP32` 暴露到公网
- 让云服务器上的 `OpenClaw` 稳定控制本地 `Mira Light`
- 保留 bridge 作为明确、安全、可维护的边界层

## 实施前提

在开始前，默认以下条件成立：

- `ESP32 Mira Light` 已经联网
- `ESP32` 的 HTTP API 可正常工作
- 云服务器上的 `OpenClaw` 已经可运行
- 本地有一台能长期在线的中转设备

当前还已知服务器上的 `OpenClaw` 采用本地模式，绑定在：

```text
127.0.0.1:20656
```

因此，bridge 的服务器侧入口也应尽量保持在回环地址上，例如：

```text
127.0.0.1:9783
```

如果“路由器”不能跑服务，请把本指南里的“路由器中转枢纽”理解为：

- 路由器后的树莓派
- 路由器后的 mini PC
- 路由器后的 NAS 容器

## 推荐部署形态

### 方案 A：OpenWrt 路由器直跑 bridge

适用条件：

- 路由器能装软件
- 有 shell 环境
- 能运行 `autossh`

### 方案 B：路由器 + 边缘主机

适用条件：

- 家用路由器本身不可编程
- 你希望后续更容易调试和扩展

这是最推荐的长期方案。

### 方案 C：电脑临时验证

适用条件：

- 只想先验证第一条链路
- 手头还没有长期在线的边缘设备

## 第 1 步：固定 ESP32 地址

### 目标

让本地中转枢纽始终能用固定地址访问 `ESP32`。

### 建议做法

在路由器中做 DHCP 保留，把 `ESP32` 固定成类似：

```text
192.168.31.42
```

### 验证命令

在本地中转枢纽上执行：

```bash
curl http://192.168.31.42/status
curl http://192.168.31.42/led
curl http://192.168.31.42/actions
```

如果这些命令失败，先不要继续做 bridge。

## 第 2 步：在本地中转枢纽上实现 bridge

### bridge 职责

bridge 不负责理解自然语言，它只负责把云端请求安全、稳定地转发给本地 `ESP32`。

### 推荐本地监听地址

```text
127.0.0.1:9783
```

这样本地 bridge 不直接暴露在局域网里。

### 推荐对外 API

#### 读取状态

```text
GET /v1/mira-light/status
GET /v1/mira-light/led
GET /v1/mira-light/actions
```

#### 执行动作

```text
POST /v1/mira-light/led
POST /v1/mira-light/action
POST /v1/mira-light/action/stop
POST /v1/mira-light/control
POST /v1/mira-light/reset
```

### bridge 建议附加能力

除了纯转发，推荐 bridge 增加：

- `Authorization: Bearer <token>` 校验
- 请求超时
- 参数结构校验
- 错误统一返回
- 健康检查接口

### 推荐健康检查接口

```text
GET /health
```

返回示例：

```json
{
  "ok": true,
  "esp32Reachable": true,
  "esp32BaseUrl": "http://192.168.31.42",
  "timestamp": "2026-04-08T00:00:00Z"
}
```

## 第 3 步：建立到云服务器的反向隧道

### 为什么选反向隧道

因为这是本地主动连云端，最适合“云上 OpenClaw + 本地硬件”的结构。

### 最小命令

```bash
ssh -N -R 127.0.0.1:9783:127.0.0.1:9783 ubuntu@43.160.217.153
```

含义是：

- 服务器上的 `127.0.0.1:9783`
- 转发到本地中转枢纽的 `127.0.0.1:9783`

### 长期运行建议

不要长期手工跑 `ssh -R`，推荐用：

```bash
autossh -M 0 -N \
  -o ServerAliveInterval=30 \
  -o ServerAliveCountMax=3 \
  -o ExitOnForwardFailure=yes \
  -R 127.0.0.1:9783:127.0.0.1:9783 \
  ubuntu@43.160.217.153
```

### 安全建议

隧道必须绑定到服务器本机回环地址：

```text
127.0.0.1:9783
```

不要绑定：

```text
0.0.0.0:9783
```

这样可以避免把 bridge 端口暴露给公网。

## 第 4 步：在服务器验证隧道

在接入 `OpenClaw` 之前，先直接在服务器验证 bridge。

### 验证命令

```bash
curl http://127.0.0.1:9783/health
curl http://127.0.0.1:9783/v1/mira-light/status
curl http://127.0.0.1:9783/v1/mira-light/led
```

只有当这些请求返回正常 JSON，才说明：

- 本地中转枢纽正常
- 隧道正常
- 服务器到本地的链路正常

## 第 5 步：在 OpenClaw 中接入 `mira-light` 插件

### 插件推荐配置

```json
{
  "plugins": {
    "entries": {
      "mira-light": {
        "enabled": true,
        "config": {
          "bridgeBaseUrl": "http://127.0.0.1:9783",
          "bridgeToken": "replace-me",
          "requestTimeoutMs": 3000
        }
      }
    }
  }
}
```

### 插件建议暴露的工具

- `mira_light_get_status`
- `mira_light_get_led`
- `mira_light_set_led`
- `mira_light_run_action`
- `mira_light_stop_action`
- `mira_light_control_servos`
- `mira_light_reset_servos`

### 为什么插件只连 bridge

插件只连：

```text
http://127.0.0.1:9783
```

而不是直接连：

```text
http://192.168.x.x
```

这样做有三个好处：

- 云服务器不需要知道本地网络细节
- 插件接口更稳定
- 后面更容易做鉴权和日志

## 第 6 步：做端到端验证

### 验证顺序

必须按依赖顺序验证，不要跳步。

#### 验证 1：本地直连 ESP32

```bash
curl http://ESP32_IP/status
```

#### 验证 2：本地直连 bridge

```bash
curl http://127.0.0.1:9783/v1/mira-light/status
```

#### 验证 3：服务器直连 tunnel 后的 bridge

```bash
curl http://127.0.0.1:9783/v1/mira-light/status
```

#### 验证 4：OpenClaw 工具调用

先试读取：

- 读取状态
- 读取灯光状态

再试写操作：

- 暖白常亮
- `wave`
- `dance`

### 建议的最小测试动作

#### 灯光

```json
{
  "mode": "solid",
  "color": {"r":255, "g":200, "b":120},
  "brightness": 180
}
```

#### 动作

```json
{
  "name": "wave",
  "loops": 1
}
```

#### 舵机

```json
{
  "mode": "absolute",
  "servo1": 90,
  "servo3": 45
}
```

## 第 7 步：把链路做成长期运行

如果验证通过，下一步不要停留在“能手工跑起来”，而要升级成长期可用。

### 推荐补齐项

- DHCP 保留地址
- bridge 开机自启
- `autossh` 开机自启
- bridge token
- 服务器侧插件配置固化
- 日志路径
- 断线告警

### 推荐运行形态

#### 如果是 OpenWrt

推荐：

- `procd` 守护 `autossh`
- `procd` 守护 bridge

#### 如果是 Linux 边缘主机

推荐：

- `systemd` 守护 bridge
- `systemd` 守护 `autossh`

## 不推荐的做法

### 1. 不推荐让 ESP32 直接暴露公网

### 2. 不推荐跳过 bridge 直接让 OpenClaw 调单片机

### 3. 不推荐把服务监听在 `0.0.0.0`

### 4. 不推荐第一阶段就上复杂公网 tunnel 平台

像 `Cloudflare Tunnel`、`ngrok` 不是不能做，而是不应该作为第一步。

先把：

- 本地 bridge
- 回环监听
- 反向隧道
- 插件调用

这条最短路径打通，才是最稳的。

## 一句话总结

这套实施方案的关键不是“把本地硬件暴露给云”，而是“让本地中转枢纽替云服务器代为接近硬件”，再由 bridge 和插件组成清晰、稳定的控制边界。
