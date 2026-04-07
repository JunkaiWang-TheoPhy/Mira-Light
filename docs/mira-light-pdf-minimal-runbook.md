# Mira Light 严格按 PDF 的最小跑通步骤

## 文档目的

这份文档只保留“严格按 [`ESP32 智能台灯.pdf`](/Users/Zhuanz/Documents/Github/Mira-Light/docs/ESP32%20智能台灯.pdf) 跑通”的最小步骤。

它明确排除这些额外方案：

- `simple_lamp_receiver.py`
- 本地 bridge
- OpenClaw 插件
- 路由器中转枢纽
- 图片上传或状态回传扩展接口

也就是说，这份文档只处理一件事：

> 用这台电脑直接调用单片机 PDF 中已有的 REST API，确认灯能被控制。

## 适用前提

开始前默认以下条件成立：

- 电脑和 `ESP32 Mira Light` 在同一个局域网
- 你已经知道单片机地址
- 单片机固件是按 PDF 中那套接口实现的

如果设备地址还不确定，先不要继续做下面命令。

## 一句话原则

先只验证 PDF 里的原始控制面：

- `GET /status`
- `GET /led`
- `GET /actions`
- `POST /led`
- `POST /action`
- `POST /control`

其它扩展接口一律先不碰。

## 最小跑通命令

先把设备地址写成一个变量。

如果你当前设备地址就是文档里常用的 `172.20.10.3`，可以直接执行：

```bash
export LAMP_BASE_URL="http://172.20.10.3"
```

如果你的设备地址不是这个，就把它改成实际 IP。

### 1. 读取当前舵机状态

这是第一条必须成功的命令。

```bash
curl "$LAMP_BASE_URL/status"
```

预期：

- 返回 JSON
- 能看到 `servo1` 到 `servo4` 的当前角度

### 2. 读取当前灯光状态

```bash
curl "$LAMP_BASE_URL/led"
```

预期：

- 返回 JSON
- 能看到 `mode`、`brightness`、`color`

### 3. 读取预设动作列表

```bash
curl "$LAMP_BASE_URL/actions"
```

预期：

- 返回 JSON
- 能看到 `nod`、`shake`、`wave`、`dance`、`stretch`、`curious`

### 4. 切换为暖白常亮

这是最小灯光写操作。

```bash
curl -X POST "$LAMP_BASE_URL/led" \
  -H 'Content-Type: application/json' \
  -d '{"mode":"solid","color":{"r":255,"g":200,"b":120},"brightness":180}'
```

预期：

- 灯光变成暖白常亮

### 5. 执行一次 wave

这是最小动作写操作。

```bash
curl -X POST "$LAMP_BASE_URL/action" \
  -H 'Content-Type: application/json' \
  -d '{"name":"wave","loops":1}'
```

预期：

- 灯执行一次打招呼动作

### 6. 控制一次关节角度

这是最小舵机写操作。

```bash
curl -X POST "$LAMP_BASE_URL/control" \
  -H 'Content-Type: application/json' \
  -d '{"mode":"absolute","servo1":90,"servo3":45}'
```

预期：

- 指定关节转到目标角度

## 跑通标准

如果下面 4 件事都成立，就可以认为“严格按 PDF 最小跑通”已经完成：

1. `curl "$LAMP_BASE_URL/status"` 成功返回 JSON
2. `curl "$LAMP_BASE_URL/led"` 成功返回 JSON
3. `POST /led` 后灯光有明显变化
4. `POST /action` 或 `POST /control` 后机械动作确实发生

## 失败时先排查什么

如果命令没有返回或设备没有动作，先只查这 4 项：

1. 电脑和单片机是否在同一局域网
2. `LAMP_BASE_URL` 是否写成了正确 IP
3. 单片机是否已经连上 `2.4GHz Wi‑Fi`
4. 单片机固件是否真的按 PDF 实现了对应接口

## 当前阶段不建议做的事

在这条最小跑通链路完成之前，先不要引入：

- `simple_lamp_receiver.py`
- 图片上传
- Base64 上传
- OpenClaw 插件
- 本地 bridge
- 反向隧道

因为这些都会增加额外变量，不利于先确认“PDF 控制面本身是否工作”。

## 一句话总结

当前最稳的起点不是扩展协议，而是先用这台电脑直接把 PDF 里原始的 `status / led / actions / action / control` 调通。
