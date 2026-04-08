# ESP32 智能台灯交付说明

## 文档目的

这份文档面向“设备交付”和“接口交付”两个目标。

它不是在讲 `OpenClaw` 如何接入，而是在明确：

- 这盏 `ESP32` 智能台灯本身有哪些能力
- 交付时应该把哪些接口、参数、调用格式和验收项说清楚
- 调用方应该如何通过 HTTP 直接控制这盏灯

本文内容基于 [`ESP32 智能台灯.pdf`](/Users/Zhuanz/Documents/Github/Mira-Light/docs/ESP32%20智能台灯.pdf) 与 [`danpianji.html`](/Users/Zhuanz/Documents/Github/Mira-Light/docs/danpianji.html) 整理。

## 一句话定义这次要交付的东西

本次交付的不是“一个只能通电亮起来的灯”，而是一个可以通过 RESTful API 控制的四关节智能灯。

这意味着调用方拿到设备后，应该可以：

- 读取 4 个关节的当前角度
- 单独或组合控制 4 个关节
- 控制灯带颜色、模式、亮度
- 执行预设动作
- 停止动作并让关节复位

## 硬件交付范围

根据 PDF 中的描述，当前硬件范围如下：

| 模块 | 规格 | 说明 |
| --- | --- | --- |
| 主控 | `ESP32-CAM` | 作为主控制器 |
| 关节 | `4 × 舵机` | 形成 4 个可控关节 |
| 灯光 | `24 × WS2812` | 可做纯色、呼吸、彩虹等灯效 |
| 摄像头 | 已安装 | 当前版本暂未启用 |

对应 GPIO 信息如下：

| 控制对象 | 引脚 |
| --- | --- |
| `servo1` | `GPIO 18` |
| `servo2` | `GPIO 13` |
| `servo3` | `GPIO 14` |
| `servo4` | `GPIO 15` |
| LED 灯带 | `GPIO 2` |

## “四个关节”在接口层是什么意思

这盏灯在接口层不是写“关节 1、关节 2、关节 3、关节 4”，而是用 4 个舵机字段表示：

- `servo1`
- `servo2`
- `servo3`
- `servo4`

因此，当前对外 API 的“关节控制协议”可以理解为：

- 关节 1 = `servo1`
- 关节 2 = `servo2`
- 关节 3 = `servo3`
- 关节 4 = `servo4`

如果后续产品侧希望把它讲成更自然的动作语言，还需要再补一层语义映射，例如：

- `servo1 = 底座旋转`
- `servo2 = 下臂抬升`
- `servo3 = 上臂俯仰`
- `servo4 = 灯头俯仰或歪头`

但就这次 PDF 已公开的交付内容来说，当前正式接口名称仍然是 `servo1` 到 `servo4`。

## 交付时必须明确给调用方的信息

如果你要把这盏灯交给前端、后端、AI agent、OpenClaw 插件或其它调用方使用，至少要把下面这些信息完整交付出去。

### 1. 设备访问地址

必须告诉调用方设备的 HTTP 基地址，例如：

```text
http://172.20.10.3
```

如果端口不是默认 `80`，还要明确写出端口，例如：

```text
http://172.20.10.3:8080
```

### 2. 四关节控制字段

必须明确四个关节对应：

- `servo1`
- `servo2`
- `servo3`
- `servo4`

### 3. 角度控制模式

必须告诉调用方：

- `mode = relative` 表示相对旋转
- `mode = absolute` 表示绝对角度

### 4. 支持的灯效模式

必须明确：

- `off`
- `solid`
- `breathing`
- `rainbow`
- `rainbow_cycle`

### 5. 支持的预设动作

必须明确：

- `nod`
- `shake`
- `wave`
- `dance`
- `stretch`
- `curious`

### 6. 参数范围

必须明确：

- `absolute` 模式下角度范围是 `0` 到 `180`
- `brightness` 范围是 `0` 到 `255`
- `color.r/g/b` 范围是 `0` 到 `255`

### 7. 返回格式

至少要说明：

- 状态接口返回 JSON
- 灯光接口返回 JSON
- 动作列表接口返回 JSON

如果设备侧还有错误码或错误消息，也应该一并交付。

## 当前 REST API 交付清单

根据 PDF，目前应该交付以下 8 个能力接口。

| 方法 | 路径 | 用途 |
| --- | --- | --- |
| `GET` | `/status` | 读取 4 个关节当前状态 |
| `POST` | `/control` | 控制 1 个或多个关节 |
| `POST` | `/reset` | 所有关节归零 |
| `GET` | `/led` | 读取当前灯光状态 |
| `POST` | `/led` | 设置灯光 |
| `GET` | `/actions` | 读取动作列表 |
| `POST` | `/action` | 执行动作 |
| `POST` | `/action/stop` | 停止动作 |

## 四关节控制接口交付格式

这是本次最核心的接口之一。

### 接口

```text
POST /control
Content-Type: application/json
```

### 参数

| 字段 | 类型 | 是否必填 | 说明 |
| --- | --- | --- | --- |
| `mode` | `string` | 否 | `relative` 或 `absolute`，默认 `relative` |
| `servo1` | `int` | 否 | 第 1 关节角度或增量 |
| `servo2` | `int` | 否 | 第 2 关节角度或增量 |
| `servo3` | `int` | 否 | 第 3 关节角度或增量 |
| `servo4` | `int` | 否 | 第 4 关节角度或增量 |

### 规则

- 只需要传想操作的关节字段
- 不传的关节保持不动
- `relative` 模式下，正数和负数表示相对旋转方向与幅度
- `absolute` 模式下，值表示目标角度

### 标准交付示例 1：相对控制两个关节

这就是你在需求中给出的标准交付格式：

```bash
curl --location 'http://172.20.10.3/control' \
--header 'Content-Type: application/json' \
--data '{
    "mode": "relative",
    "servo1": 30,
    "servo2": -20
}'
```

含义是：

- 第 1 关节相对当前姿态转动 `+30`
- 第 2 关节相对当前姿态转动 `-20`
- 第 3、4 关节保持不动

### 标准交付示例 2：绝对控制两个关节

```bash
curl --location 'http://172.20.10.3/control' \
--header 'Content-Type: application/json' \
--data '{
    "mode": "absolute",
    "servo1": 90,
    "servo3": 45
}'
```

含义是：

- 第 1 关节转到 `90°`
- 第 3 关节转到 `45°`
- 其余关节不变

### 标准交付示例 3：只控制单个关节

```bash
curl --location 'http://172.20.10.3/control' \
--header 'Content-Type: application/json' \
--data '{
    "mode": "relative",
    "servo4": 15
}'
```

这说明接口支持“单关节控制”，而不要求每次都传 4 个值。

## 状态读取接口交付格式

### 接口

```text
GET /status
```

### 典型调用

```bash
curl --location 'http://172.20.10.3/status'
```

### 典型返回

```json
{
  "servos": [
    {"id":1, "name":"servo1", "angle":90, "pin":18},
    {"id":2, "name":"servo2", "angle":90, "pin":13},
    {"id":3, "name":"servo3", "angle":90, "pin":14},
    {"id":4, "name":"servo4", "angle":90, "pin":15}
  ]
}
```

这个返回值对调用方非常重要，因为它能确认：

- 4 个关节当前角度
- 每个关节的名称
- 每个关节绑定的引脚

## 复位接口交付格式

### 接口

```text
POST /reset
```

### 典型调用

```bash
curl --location --request POST 'http://172.20.10.3/reset'
```

### 含义

- 所有关节回到 `0°`
- 无需请求体

如果设备后续实现上不是完全回到 `0°`，而是回到“默认站姿”，则交付文档中必须改写清楚，避免实现和文档不一致。

## 灯光接口交付格式

### 读取灯光状态

```bash
curl --location 'http://172.20.10.3/led'
```

典型返回：

```json
{
  "mode": "solid",
  "brightness": 128,
  "color": {"r":255, "g":255, "b":255},
  "led_count": 24,
  "pin": 2
}
```

### 设置灯光

```bash
curl --location 'http://172.20.10.3/led' \
--header 'Content-Type: application/json' \
--data '{
    "mode": "solid",
    "color": {"r":255,"g":200,"b":120},
    "brightness": 200
}'
```

### 可交付灯效模式

| `mode` 值 | 含义 |
| --- | --- |
| `off` | 关灯 |
| `solid` | 纯色常亮 |
| `breathing` | 呼吸灯 |
| `rainbow` | 彩虹流动 |
| `rainbow_cycle` | 彩虹循环 |

### 灯光交付说明

- `color` 只在 `solid` 和 `breathing` 模式下有明确意义
- `brightness` 是全局亮度
- `led_count = 24`
- 灯带引脚是 `GPIO 2`

## 预设动作接口交付格式

### 查询动作列表

```bash
curl --location 'http://172.20.10.3/actions'
```

典型返回：

```json
{
  "playing": false,
  "available": [
    {"name":"nod",     "frames":5},
    {"name":"shake",   "frames":5},
    {"name":"wave",    "frames":7},
    {"name":"dance",   "frames":12},
    {"name":"stretch", "frames":5},
    {"name":"curious", "frames":8}
  ]
}
```

### 执行动作

```bash
curl --location 'http://172.20.10.3/action' \
--header 'Content-Type: application/json' \
--data '{
    "name": "dance",
    "loops": 2
}'
```

### 停止动作

```bash
curl --location --request POST 'http://172.20.10.3/action/stop'
```

### 动作名交付清单

| 动作名 | 含义 |
| --- | --- |
| `nod` | 点头 |
| `shake` | 摇头 |
| `wave` | 打招呼 |
| `dance` | 跳舞 |
| `stretch` | 伸懒腰 |
| `curious` | 好奇张望 |

## 从“设备交付”角度，你还需要补充什么

如果你是要把这盏灯正式交给别人调用，仅仅给一个 PDF 和一个 HTML 页面通常还不够。更完整的交付至少还应包含下面这些信息。

### 1. 基地址说明

例如：

```text
设备默认地址：http://172.20.10.3
```

如果地址会变化，还应说明：

- 是否使用 DHCP
- 是否支持固定 IP
- 是否支持热点模式
- 如果设备离线如何重新发现 IP

### 2. 四关节物理定义

PDF 里已经说明有 4 个舵机，但还没有明确写出每个舵机在机械结构上的真实职责。

对调用方来说，最好补出：

- `servo1` 对应哪个物理关节
- `servo2` 对应哪个物理关节
- `servo3` 对应哪个物理关节
- `servo4` 对应哪个物理关节

否则调用方虽然能发命令，但很难构建“抬头”“扭身”“歪头”这类高层动作。

### 3. 安全范围

PDF 给出了 `absolute = 0°~180°`，但真正交付时最好补：

- 每个关节的推荐安全范围
- 哪些关节不适合长时间打到极限角度
- 是否需要限速

### 4. 错误返回

交付时最好再明确：

- 参数错误时返回什么
- 动作名不存在时返回什么
- 设备忙碌时返回什么
- 设备断网时返回什么

### 5. 验收样例

建议交付时至少附上下面这些“可执行验收命令”。

## 建议作为交付附件的验收命令

### 验收 1：读取关节状态

```bash
curl --location 'http://172.20.10.3/status'
```

### 验收 2：相对控制两个关节

```bash
curl --location 'http://172.20.10.3/control' \
--header 'Content-Type: application/json' \
--data '{
    "mode": "relative",
    "servo1": 30,
    "servo2": -20
}'
```

### 验收 3：绝对控制两个关节

```bash
curl --location 'http://172.20.10.3/control' \
--header 'Content-Type: application/json' \
--data '{
    "mode": "absolute",
    "servo1": 90,
    "servo3": 45
}'
```

### 验收 4：灯光常亮

```bash
curl --location 'http://172.20.10.3/led' \
--header 'Content-Type: application/json' \
--data '{
    "mode": "solid",
    "color": {"r":255,"g":200,"b":120},
    "brightness": 200
}'
```

### 验收 5：执行动作

```bash
curl --location 'http://172.20.10.3/action' \
--header 'Content-Type: application/json' \
--data '{
    "name": "wave",
    "loops": 1
}'
```

### 验收 6：停止动作

```bash
curl --location --request POST 'http://172.20.10.3/action/stop'
```

### 验收 7：复位

```bash
curl --location --request POST 'http://172.20.10.3/reset'
```

## 这次更适合交付给别人的完整内容包

如果你的目标是把这盏灯正式交给别人接入或调用，我建议最终交付包至少包括：

- 本文档：接口与验收说明
- [`ESP32 智能台灯.pdf`](/Users/Zhuanz/Documents/Github/Mira-Light/docs/ESP32%20智能台灯.pdf)
- [`danpianji.html`](/Users/Zhuanz/Documents/Github/Mira-Light/docs/danpianji.html)
- 设备当前基地址或网络发现说明
- 4 个关节的物理语义映射表
- 一份可直接执行的 `curl` 验收脚本

## 当前阶段最重要的结论

根据 `ESP32 智能台灯.pdf`，当前这盏灯最核心的交付能力不是“摄像头”或“复杂 AI”，而是下面这三件事：

- 4 个关节可通过 `/control` 控制
- 24 灯珠可通过 `/led` 控制
- 一组预设动作可通过 `/action` 控制

如果你要对外讲“这次到底交付了什么”，最准确的说法可以是：

> 本次交付的是一个带 4 个关节、24 灯珠、支持 REST API 控制的 ESP32 智能台灯。调用方可通过 HTTP 直接读取状态、控制关节、控制灯效以及执行预设动作。

