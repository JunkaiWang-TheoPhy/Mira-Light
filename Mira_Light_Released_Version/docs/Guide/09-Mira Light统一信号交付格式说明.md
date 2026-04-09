# Mira Light 统一信号交付格式说明

更新时间：2026-04-09

## 文档目的

这份文档把 `Mira Light` 当前对外和对设备相关的三类信号统一收口成一份正式说明：

1. `9527` 原始 TCP 总线舵机帧
2. `40` 灯 `pixelSignals`
3. 头部电容 `headCapacitive`

它要解决的是一个现实问题：

- `9527` 原始舵机帧已经有单独文档
- `40` 灯和电容信息分散在 mock 排练、导演台和代码里
- 调用方容易误以为这些信号都走同一种协议

这份文档给出的统一结论是：

- 四关节底层运动信号可以走 raw TCP 舵机帧
- `40` 灯 `pixelSignals` 和 `headCapacitive` 不走 `9527` raw TCP 帧
- `40` 灯和电容当前通过 HTTP 设备接口 / bridge 接口表达

## 一句话结论

当前 Mira Light 的完整信号面可以概括为：

```text
上层调用方
-> bridge HTTP / 导演台 HTTP
-> runtime
-> 四关节动作最终可下沉为 9527 raw TCP 舵机帧
-> 灯效与电容仍通过 HTTP 设备状态面表达
```

也就是说：

- `#003P1500T1000!` 这类帧只负责舵机运动
- `pixelSignals` 和 `headCapacitive` 由 `/led`、`/sensors`、`/status` 这些 HTTP 结构携带

## 适用范围

这份文档覆盖三层：

| 层级 | 主要入口 | 负责什么 |
| --- | --- | --- |
| raw device transport | `tcp://192.168.31.10:9527` | 四关节舵机动作底层帧 |
| device HTTP / mock device | `/status` `/control` `/led` `/sensors` `/actions` | 设备状态、40 灯、电容、动作 |
| local bridge HTTP | `/v1/mira-light/*` | 给导演台、脚本、插件的统一语义接口 |

## 信号总表

| 信号类别 | 当前格式 | 承载层 | 是否走 9527 raw TCP |
| --- | --- | --- | --- |
| 四关节目标动作 | `#IDPWWWWTTTT!` / `{...}` | raw TCP transport | 是 |
| 四关节语义控制 | JSON：`mode + servo1~servo4` | bridge / HTTP device | 否 |
| 40 灯逐像素信号 | JSON：`pixels` / `pixelSignals` | HTTP device / mock / status | 否 |
| 头部电容 | JSON：`headCapacitive: 0|1` | HTTP device / mock / bridge | 否 |
| 汇总设备状态 | JSON：`servos + sensors + led` | HTTP device / bridge | 否 |

## 1. 9527 原始 TCP 舵机帧

### 1.1 目标地址

当前联调目标：

```text
tcp://192.168.31.10:9527
```

这是一条原始总线舵机 TCP 控制口，不是 HTTP REST 端口。

### 1.2 单舵机控制帧

格式：

```text
#000P1500T1000!
```

字段含义：

- `#`：固定起始符
- `000`：舵机 `ID`
- `P1500`：PWM 脉宽
- `T1000`：执行时间，单位毫秒
- `!`：固定结束符

严格规则：

- `ID` 范围：`000-254`
- `ID` 必须始终是 `3` 位，不足补 `0`
- `PWM` 范围：`0500-2500`
- `PWM` 必须始终是 `4` 位，不足补 `0`
- `TIME` 范围：`0000-9999`
- `TIME` 必须始终是 `4` 位，不足补 `0`

### 1.3 多舵机控制帧

格式：

```text
{#000P1602T1000!#001P2500T0000!#002P1500T1000!}
```

规则：

- 当同时下发 `2` 条或以上单舵机帧时，整条命令必须包在 `{}` 里
- 花括号内部只能是若干条合法单帧直接拼接
- 不允许插入空格、逗号、分号或其他分隔符

### 1.4 示例

单舵机中位：

```text
#003P1500T1000!
```

多舵机同时移动：

```text
{#001P2000T1000!#003P0833T2000!}
```

## 2. 设备 HTTP / Bridge HTTP 语义面

raw TCP 舵机帧只解决“怎么动四个关节”。

但 Mira Light 的完整设备面还包括：

- 40 灯状态
- 电容状态
- 动作列表 / 动作播放状态
- 汇总状态读取

这些信息当前统一通过 HTTP JSON 表达。

### 2.1 设备 HTTP 典型路径

mock 设备当前支持：

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| `GET` | `/health` | 健康检查和快照 |
| `GET` | `/status` | 汇总读取四关节 + 灯 + 电容 |
| `POST` | `/control` | 四关节控制 |
| `POST` | `/reset` | 复位 |
| `GET` | `/led` | 读取灯光状态 |
| `POST` | `/led` | 设置灯光 |
| `GET` | `/sensors` | 读取电容状态 |
| `POST` | `/sensors` | 写入电容状态 |
| `GET` | `/actions` | 读取动作列表和播放状态 |
| `POST` | `/action` | 启动预设动作 |
| `POST` | `/action/stop` | 停止预设动作 |

### 2.2 统一口径

- `/status`：正式统一读取面，只读 `servos + sensors + led`
- 灯光写入：统一发 `pixels`
- 灯光读取：统一看 `pixelSignals`
- `headCapacitive`：只接受 `0 | 1`
- `/health`：只做健康检查和快照，不拿它当正式状态面

## 3. 对发布版的实际意义

这份文档最重要的不是“多讲一个协议”，而是把发布版里最容易混淆的三件事拆开：

- 舵机怎么下发
- 40 灯怎么表达
- 电容状态怎么读写

这样 mock 排练、bridge 联调、现场控制三边就能统一口径。
