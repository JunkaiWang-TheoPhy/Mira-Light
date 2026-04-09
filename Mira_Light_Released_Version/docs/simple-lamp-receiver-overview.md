# Mira Light 最简接收器总览

## 文档目的

这份文档说明当前仓库中“最简单可用”的 HTTP 接收器方案。

它的目标不是替代完整的 `bridge + OpenClaw plugin` 架构，而是提供一个最快可落地的入口，让当前 ESP32 单片机可以立即做到两件事：

1. 向本机电脑上报当前状态
2. 向本机电脑上传图片或其他文件

对应实现文件是：

- [`scripts/simple_lamp_receiver.py`](../scripts/simple_lamp_receiver.py)

## 为什么需要这个最简方案

根据 [`ESP32 智能台灯.pdf`](../docs/ESP32%20智能台灯.pdf) 和 [`danpianji.html`](../docs/danpianji.html)，当前灯具已经有自己的控制接口：

- `GET /status`
- `POST /control`
- `POST /reset`
- `GET /led`
- `POST /led`
- `GET /actions`
- `POST /action`
- `POST /action/stop`

这些接口解决的是：

> “电脑怎么控制灯”

但你后续又提出了另一个需求：

> “灯怎么把状态、图片、文件发给我电脑”

`simple_lamp_receiver.py` 就是专门为这个方向准备的最小 server。

## 一句话理解

可以把这个 server 理解成：

> 灯给电脑发消息的收件箱。

它不是控制灯的那一套接口，而是：

- 灯主动 `POST` 给电脑
- 电脑收到后自动保存

## 当前支持的能力

当前最简接收器支持 4 类能力：

| 能力 | 方法 | 路径 | 用途 |
| --- | --- | --- | --- |
| 健康检查 | `GET` | `/health` | 测试接收器是否在线 |
| 状态上报 | `POST` | `/device/status` | 灯把当前状态发给电脑 |
| 二进制上传 | `POST` | `/device/upload` | 灯把图片或文件直接传给电脑 |
| Base64 上传 | `POST` | `/device/upload-base64` | 灯把图片或文件以 Base64 JSON 方式传给电脑 |

## 默认保存位置

默认保存根目录是：

[`~/Documents/Mira-Light-Runtime/simple-receiver/`](~/Documents/Mira-Light-Runtime/simple-receiver/)

也就是通常等价于：

[`/Users/Zhuanz/Documents/Mira-Light-Runtime/simple-receiver/`](/Users/Zhuanz/Documents/Mira-Light-Runtime/simple-receiver/)

下面会自动创建这些目录：

- `snapshots/`
- `events/`
- `uploads/`

## 目录结构说明

### 1. 最新状态

目录：

[`~/Documents/Mira-Light-Runtime/simple-receiver/snapshots/`](~/Documents/Mira-Light-Runtime/simple-receiver/snapshots/)

用途：

- 保存每台设备最近一次状态
- 采用覆盖式保存

示例文件：

```text
~/Documents/Mira-Light-Runtime/simple-receiver/snapshots/mira-light-001.latest.json
```

### 2. 事件日志

目录：

[`~/Documents/Mira-Light-Runtime/simple-receiver/events/`](~/Documents/Mira-Light-Runtime/simple-receiver/events/)

用途：

- 追加保存每天收到的状态与上传记录
- 便于排查和回放

示例文件：

```text
~/Documents/Mira-Light-Runtime/simple-receiver/events/2026-04-08.jsonl
```

### 3. 上传文件

目录：

[`~/Documents/Mira-Light-Runtime/simple-receiver/uploads/`](~/Documents/Mira-Light-Runtime/simple-receiver/uploads/)

用途：

- 保存图片、抓拍、日志文件、其它附件

实际路径会按日期、设备和分类自动分层，例如：

```text
~/Documents/Mira-Light-Runtime/simple-receiver/uploads/2026-04-08/mira-light-001/images/frame.jpg
```

同时还会生成一个元数据文件：

```text
~/Documents/Mira-Light-Runtime/simple-receiver/uploads/2026-04-08/mira-light-001/images/frame.jpg.meta.json
```

## 什么时候适合用它

这个最简接收器特别适合以下阶段：

- 现在先把 ESP32 -> 电脑 的链路打通
- 先验证状态上报和图片上传
- 先做现场调试记录
- 还不想立刻接完整 OpenClaw bridge

## 什么时候不应该只停留在它

它不适合作为最终完整架构的唯一接口层。

如果你后面要继续做：

- 本地 bridge
- 远端 OpenClaw 接入
- 场景驱动
- 运行时控制

那还是应该继续保留：

- [`tools/mira_light_bridge/README.md`](../tools/mira_light_bridge/README.md)
- [`scripts/mira_light_runtime.py`](../scripts/mira_light_runtime.py)
- [`scripts/console_server.py`](../scripts/console_server.py)

也就是说：

- `simple_lamp_receiver.py` 是最小起步方案
- `mira_light_bridge` 是后续更完整的系统方案

## 最简启动命令

```bash
python3 scripts/simple_lamp_receiver.py
```

指定端口和保存路径：

```bash
python3 scripts/simple_lamp_receiver.py \
  --host 0.0.0.0 \
  --port 9784 \
  --save-root /Users/Zhuanz/Documents/Mira-Light-Runtime/simple-receiver
```

## 相关文档

- [`simple-lamp-receiver-api.md`](../docs/simple-lamp-receiver-api.md)
- [`simple-lamp-receiver-esp32-examples.md`](../docs/simple-lamp-receiver-esp32-examples.md)

