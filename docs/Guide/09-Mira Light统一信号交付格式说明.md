# Mira Light 统一信号交付格式说明

更新时间：2026-04-09

## 文档目的

这份文档把 `Mira Light` 当前对外和对设备相关的三类信号统一收口成一份正式说明：

1. `9527` 原始 TCP 总线舵机帧
2. `40` 灯 `pixelSignals`
3. 头部电容 `headCapacitive`

它要解决的是一个现实问题：

- 9527 原始舵机帧已经有单独文档
- 40 灯和电容信息分散在 mock 排练、导演台和代码里
- 调用方容易误以为这些信号都走同一种协议

这份文档给出的统一结论是：

- 四关节底层运动信号可以走 raw TCP 舵机帧
- `40` 灯 `pixelSignals` 和 `headCapacitive` 不走 9527 raw TCP 帧
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

例如：

- `3` 号舵机必须写成 `003`
- `PWM 800` 必须写成 `P0800`
- `TIME 500ms` 必须写成 `T0500`

### 1.3 多舵机控制帧

格式：

```text
{#000P1602T1000!#001P2500T0000!#002P1500T1000!}
```

规则：

- 当同时下发 `2` 条或以上单舵机帧时，整条命令必须包在 `{}` 里
- 花括号内部只能是若干条合法单帧直接拼接
- 不允许插入空格、逗号、分号或其他分隔符

### 1.4 物理语义

当前对 270 度舵机的口径是：

- `P1500`：中位
- `P1500 -> P2500`：舵机轴朝向自己时，为逆时针方向
- `P1500 -> P0500`：舵机轴朝向自己时，为顺时针方向
- `0500-2500` 对应完整 PWM 工作区间
- `T0000-T9999` 表示移动时间，单位毫秒

### 1.5 示例

单舵机中位：

```text
#003P1500T1000!
```

单舵机逆时针快速移动：

```text
#003P2500T0000!
```

多舵机同时移动：

```text
{#001P2000T1000!#003P0833T2000!}
```

### 1.6 仓库中的实现位置

- [bus_servo_protocol.py](/Users/huhulitong/Documents/GitHub/Mira-Light/scripts/bus_servo_protocol.py)
- [bus_servo_transport.py](/Users/huhulitong/Documents/GitHub/Mira-Light/scripts/bus_servo_transport.py)
- [bus_servo_mapping.py](/Users/huhulitong/Documents/GitHub/Mira-Light/scripts/bus_servo_mapping.py)
- [04-9527总线舵机TCP帧协议与仓库对齐说明.md](/Users/huhulitong/Documents/GitHub/Mira-Light/docs/Guide/04-9527总线舵机TCP帧协议与仓库对齐说明.md)

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

对应实现见：

- [mock_lamp_server.py](/Users/huhulitong/Documents/GitHub/Mira-Light/scripts/mock_lamp_server.py)

### 2.2 Bridge HTTP 典型路径

对上层调用方更推荐的入口是 bridge：

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| `GET` | `/v1/mira-light/status` | 汇总状态 |
| `GET` | `/v1/mira-light/led` | 灯光状态 |
| `GET` | `/v1/mira-light/sensors` | 传感器状态 |
| `GET` | `/v1/mira-light/actions` | 动作状态 |
| `POST` | `/v1/mira-light/control` | 四关节语义控制 |
| `POST` | `/v1/mira-light/led` | 灯光控制 |
| `POST` | `/v1/mira-light/sensors` | 电容状态写入 |
| `POST` | `/v1/mira-light/action` | 触发动作 |

这些路径都走 JSON，并且 `/v1/...` 需要 bridge token。

## 3. 四关节 JSON 控制格式

### 3.1 请求格式

```json
{
  "mode": "absolute",
  "servo1": 120,
  "servo2": 95,
  "servo3": 88,
  "servo4": 70
}
```

字段说明：

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `mode` | `string` | 是 | `absolute` 或 `relative` |
| `servo1` | `int` | 否 | 第 1 关节 |
| `servo2` | `int` | 否 | 第 2 关节 |
| `servo3` | `int` | 否 | 第 3 关节 |
| `servo4` | `int` | 否 | 第 4 关节 |

规则：

- 至少传一个 `servo*`
- `absolute` 表示目标逻辑角度
- `relative` 表示相对当前的增量
- runtime 会做范围校验，再决定最终是否下沉为 TCP raw frame

### 3.2 返回格式

典型返回：

```json
{
  "ok": true,
  "mode": "absolute",
  "updated": 4,
  "servos": [
    {"id": 1, "name": "servo1", "angle": 120, "pin": 18},
    {"id": 2, "name": "servo2", "angle": 95, "pin": 13},
    {"id": 3, "name": "servo3", "angle": 88, "pin": 14},
    {"id": 4, "name": "servo4", "angle": 70, "pin": 15}
  ],
  "sensors": {"headCapacitive": 0},
  "led": {
    "mode": "solid",
    "brightness": 128,
    "color": {"r": 255, "g": 255, "b": 255},
    "led_count": 40,
    "pin": 2,
    "pixelSignals": [[255,255,255,128]]
  }
}
```

## 4. 40 灯 `pixelSignals` 交付格式

### 4.1 当前口径

当前仓库默认灯珠数量为 `40`。

对应代码口径：

- mock 设备默认 `DEFAULT_LED_COUNT = 40`
- runtime 默认 `LED_PIXEL_COUNT = 40`

因此当前统一要求是：

- `vector` 模式下必须一次性提交完整 `40` 个像素

### 4.2 灯光模式

当前支持的 LED `mode`：

- `off`
- `solid`
- `breathing`
- `rainbow`
- `rainbow_cycle`
- `vector`

### 4.3 `solid` / `breathing` 请求格式

```json
{
  "mode": "solid",
  "brightness": 200,
  "color": {"r": 255, "g": 200, "b": 120}
}
```

规则：

- `brightness` 可选，范围 `0-255`
- `color` 在 `solid` 和 `breathing` 模式下必填
- `color` 必须是 RGB 三通道
- `rainbow`、`rainbow_cycle`、`off` 不接受 `color`

### 4.4 `vector` 请求格式

bridge / runtime 推荐格式：

```json
{
  "mode": "vector",
  "pixels": [
    [255, 0, 0, 180],
    [255, 64, 0, 180]
  ]
}
```

这里的完整规则是：

- `mode=vector` 时必须提供 `pixels`
- `pixels` 必须是长度为 `40` 的数组
- 每一项可以是：
  - RGB 对象：`{"r":255,"g":0,"b":0}`
  - RGBA 对象：`{"r":255,"g":0,"b":0,"brightness":180}`
  - RGB 向量：`[255,0,0]`
  - RGBA 向量：`[255,0,0,180]`
- 每个通道和 `brightness` 都必须在 `0-255`
- 若某个像素未显式提供 `brightness`，则使用全局 `brightness`

### 4.5 `pixelSignals` 的标准结构

统一对外展示和状态返回时，40 灯信号使用：

```text
pixelSignals = [R, G, B, brightness]
```

也就是说每个像素最终都是：

```json
[255, 0, 0, 180]
```

这四个值分别表示：

- `R`
- `G`
- `B`
- `brightness`

### 4.6 `vector` 返回格式

mock 设备在 `GET /led` 或 `GET /status` 里会返回：

```json
{
  "mode": "vector",
  "brightness": 180,
  "color": {"r": 255, "g": 255, "b": 255},
  "led_count": 40,
  "pin": 2,
  "pixelSignals": [
    [255,0,0,180],
    [255,64,0,180]
  ],
  "pixels": [
    {"r":255,"g":0,"b":0},
    {"r":255,"g":64,"b":0}
  ]
}
```

注意：

- `pixelSignals` 是带亮度的四通道结构
- `pixels` 是不带亮度的 RGB 结构
- `pixels` 只在 `mode=vector` 时返回

### 4.7 重要兼容性说明

当前存在一个“入口差异”：

- bridge / runtime 的 LED 写入口正式字段是 `pixels`
- mock 设备的 `/led` 在 `mode=vector` 时同时兼容 `pixels` 和 `pixelSignals`

因此推荐口径是：

- 上层调用方永远发 `pixels`
- 展示层和状态层统一读 `pixelSignals`

## 5. `headCapacitive` 交付格式

### 5.1 请求格式

```json
{
  "headCapacitive": 1
}
```

规则：

- 目前只支持字段 `headCapacitive`
- 只能是整数 `0` 或 `1`
- `0` 表示空闲 / 未触摸
- `1` 表示触摸或贴近已触发

### 5.2 返回格式

读取 `/sensors` 时的典型返回：

```json
{
  "headCapacitive": 1
}
```

写入成功后的典型返回：

```json
{
  "ok": true,
  "headCapacitive": 1
}
```

### 5.3 当前语义边界

`headCapacitive` 当前是一个二值信号，不是连续模拟量。

因此：

- 这不是电容原始采样值
- 也不是带阈值信息的传感器诊断包
- 当前交付口径就是 `0 / 1`

## 6. 统一状态读取格式

### 6.1 `/status` 结构

当前统一状态面建议理解为：

```json
{
  "servos": [
    {"id": 1, "name": "servo1", "angle": 90, "pin": 18},
    {"id": 2, "name": "servo2", "angle": 90, "pin": 13},
    {"id": 3, "name": "servo3", "angle": 90, "pin": 14},
    {"id": 4, "name": "servo4", "angle": 90, "pin": 15}
  ],
  "sensors": {
    "headCapacitive": 0
  },
  "led": {
    "mode": "solid",
    "brightness": 128,
    "color": {"r": 255, "g": 255, "b": 255},
    "led_count": 40,
    "pin": 2,
    "pixelSignals": [
      [255,255,255,128]
    ]
  }
}
```

这意味着：

- 四关节状态
- 头部电容状态
- 灯效摘要与逐像素信号

都应该能在一个统一状态面中读到。

### 6.2 `/health` 结构

mock 设备还提供：

```json
{
  "ok": true,
  "service": "mock-mira-light-device",
  "time": "2026-04-09T12:00:00+08:00",
  "snapshot": {
    "status": {},
    "led": {},
    "actions": {},
    "lastCommandAt": "2026-04-09T12:00:00+08:00"
  }
}
```

适合用来快速查看当前整机快照。

## 7. 分层边界与推荐对接方式

### 7.1 raw TCP 9527 只做什么

9527 raw TCP 只适合做：

- 四关节底层舵机动作下发
- 把逻辑角度转换为底层 `PWM + TIME`

它不适合直接承载：

- `40` 灯 `pixelSignals`
- `headCapacitive`
- `GET /status`
- `GET /led`
- `GET /actions`

### 7.2 bridge / HTTP 应该做什么

bridge / HTTP 负责：

- 给导演台和脚本稳定 JSON 接口
- 屏蔽底层是否是 HTTP 灯还是 raw TCP 舵机口
- 提供设备状态、灯效状态、传感器状态
- 让 `40` 灯和电容在没有真实硬件时也能继续排练

### 7.3 推荐调用顺序

推荐调用方按下面这套思路接入：

1. 上层永远优先调用 bridge HTTP
2. 四关节场景和姿态通过 `/control`、`/run-scene`、`/apply-pose`
3. 40 灯逐像素控制通过 `/led`
4. 电容状态通过 `/sensors`
5. 只有 transport / adapter 层才直接理解 `#IDPWWWWTTTT!`

## 8. 最小可执行示例

### 8.1 下发单舵机 raw TCP 帧

```bash
printf '#003P1500T1000!\n' | nc 192.168.31.10 9527
```

### 8.2 通过 bridge 控制四关节

```bash
curl -X POST http://127.0.0.1:9783/v1/mira-light/control \
  -H "Authorization: Bearer $MIRA_LIGHT_BRIDGE_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"mode":"absolute","servo1":120,"servo2":95,"servo3":88,"servo4":70}'
```

### 8.3 通过 bridge 写 40 灯信号

```bash
curl -X POST http://127.0.0.1:9783/v1/mira-light/led \
  -H "Authorization: Bearer $MIRA_LIGHT_BRIDGE_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "mode": "vector",
    "pixels": [
      [255,0,0,180],[255,64,0,180],[255,128,0,180],[255,192,0,180],[255,255,0,180],
      [192,255,0,180],[128,255,0,180],[64,255,0,180],[0,255,0,180],[0,255,64,180],
      [0,255,128,180],[0,255,192,180],[0,255,255,180],[0,192,255,180],[0,128,255,180],
      [0,64,255,180],[0,0,255,180],[64,0,255,180],[128,0,255,180],[192,0,255,180],
      [255,0,255,180],[255,0,192,180],[255,0,128,180],[255,0,64,180],[255,64,64,180],
      [255,96,64,180],[255,128,64,180],[255,160,64,180],[255,192,64,180],[255,224,64,180],
      [224,255,64,180],[192,255,64,180],[160,255,64,180],[128,255,64,180],[96,255,64,180],
      [64,255,64,180],[64,255,96,180],[64,255,128,180],[64,255,160,180],[64,255,192,180]
    ]
  }'
```

### 8.4 写入头部电容状态

```bash
curl -X POST http://127.0.0.1:9783/v1/mira-light/sensors \
  -H "Authorization: Bearer $MIRA_LIGHT_BRIDGE_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"headCapacitive":1}'
```

### 8.5 读取统一状态

```bash
curl http://127.0.0.1:9783/v1/mira-light/status \
  -H "Authorization: Bearer $MIRA_LIGHT_BRIDGE_TOKEN"
```

## 9. 代码中的信号真值来源

如果需要和实现再次核对，优先看这些文件：

- [bus_servo_protocol.py](/Users/huhulitong/Documents/GitHub/Mira-Light/scripts/bus_servo_protocol.py)
- [mock_lamp_server.py](/Users/huhulitong/Documents/GitHub/Mira-Light/scripts/mock_lamp_server.py)
- [mira_light_runtime.py](/Users/huhulitong/Documents/GitHub/Mira-Light/scripts/mira_light_runtime.py)
- [bridge_server.py](/Users/huhulitong/Documents/GitHub/Mira-Light/tools/mira_light_bridge/bridge_server.py)
- [mira-light-mock-rehearsal-guide.md](/Users/huhulitong/Documents/GitHub/Mira-Light/docs/mira-light-mock-rehearsal-guide.md)

## 10. 当前推荐口径

如果要对外发给联调方或硬件方，建议统一使用下面这段话：

> Mira Light 当前采用分层交付：四关节底层运动使用 9527 raw TCP 舵机帧 `#IDPWWWWTTTT!`；40 灯逐像素信号使用 HTTP JSON `pixels` / `pixelSignals`，当前固定为 40 个灯、每个像素为 `[R,G,B,brightness]`；头部电容使用 HTTP JSON `headCapacitive: 0|1`。上层调用方建议统一对接 bridge HTTP，而不要直接混用 raw TCP 和设备内部实现细节。
