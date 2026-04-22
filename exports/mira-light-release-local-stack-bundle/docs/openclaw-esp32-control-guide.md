# OpenClaw 接入并控制 ESP32 Mira Light 指南

## 背景

当前仓库中的 [`danpianji.html`](../docs/danpianji.html) 是从 ESP32 单片机设备中下载出来的页面。

这份 HTML 的价值不是“前端页面本身”，而是它已经把这块 ESP32 暴露出来的 REST API 说明清楚了。也就是说，这块板子已经不是只能烧录程序的“黑盒单片机”，而是一台可以通过 HTTP 请求控制的网络设备。

因此，`OpenClaw` 想要控制它，真正需要的不是“去读网页”，而是：

1. 知道设备的网络地址
2. 知道设备有哪些可调用的接口
3. 把这些接口包装成 OpenClaw 可以稳定调用的工具

## 这块 ESP32 现在已经能做什么

根据 [`danpianji.html`](../docs/danpianji.html) 中的说明，这块 ESP32 已经暴露了以下接口。

| 能力 | 方法 | 路径 | 作用 |
| --- | --- | --- | --- |
| 读取舵机状态 | `GET` | `/status` | 返回 4 个舵机当前角度 |
| 控制舵机 | `POST` | `/control` | 相对或绝对控制 `servo1` 到 `servo4` |
| 舵机归零 | `POST` | `/reset` | 所有舵机回到 `0°` |
| 读取灯光状态 | `GET` | `/led` | 返回当前灯光模式、亮度、颜色 |
| 设置灯光 | `POST` | `/led` | 修改灯效模式、颜色、亮度 |
| 读取预设动作 | `GET` | `/actions` | 返回预设动作列表与播放状态 |
| 执行动作 | `POST` | `/action` | 执行 `nod`、`wave`、`dance` 等动作 |
| 停止动作 | `POST` | `/action/stop` | 停止当前正在播放的动作 |

换句话说，这块板子本身已经具备了三类控制面：

- 舵机控制
- 灯光控制
- 高层动作控制

## 最关键的理解

### HTML 不是给 Claw 用的

`danpianji.html` 主要是给人看的接口文档。它告诉我们：

- 有哪些接口
- 每个接口接收什么参数
- 会返回什么结构

但 `OpenClaw` 不能稳定地靠“每次先读网页再自己发挥”去控制设备。这样做的问题是：

- 不稳定，模型可能误解页面内容
- 不安全，模型可能构造出不合适的参数
- 不可维护，后续很难加边界和权限控制

### 真正应该给 Claw 的是工具层

对 `OpenClaw` 来说，正确的做法是把设备接口封装成明确工具，例如：

- `mira_light_get_status`
- `mira_light_set_led`
- `mira_light_run_action`
- `mira_light_control_servos`
- `mira_light_stop_action`

这样之后，Claw 看到的就不是一堆散乱接口，而是一套可被调用、可被限制、可被解释的能力。

## 整体架构应该是什么样

最推荐的调用路径如下：

```text
你
-> OpenClaw
-> mira-light 插件或本地桥接服务
-> HTTP 请求
-> ESP32
-> 舵机 / LED / 动作执行
```

这里有两个典型部署方式。

### 方案一：OpenClaw 与 ESP32 在同一局域网

如果 `OpenClaw` 运行在你的本地电脑、树莓派或同一 Wi-Fi 下的服务器上，并且能直接访问单片机 IP，那么路径最简单：

```text
OpenClaw -> 直接访问 http://ESP32_IP
```

例如：

```text
OpenClaw -> http://192.168.31.42/status
OpenClaw -> http://192.168.31.42/led
OpenClaw -> http://192.168.31.42/action
```

这是最推荐的第一阶段接法。

### 方案二：OpenClaw 在远端，ESP32 在本地局域网

如果 `OpenClaw` 跑在远端 `devbox`，而 ESP32 还在你家的 `192.168.x.x` 局域网中，那么远端通常不能直接访问这块板子。

这时就应该加一层本地桥接：

```text
OpenClaw(devbox)
-> 本地 bridge 服务
-> ESP32
```

这和现有项目中的 `Mi Band bridge`、`printer bridge` 是同一种思路：

- 本地 bridge 负责接近真实硬件
- OpenClaw 插件只与 bridge 通信
- bridge 再转发到设备

如果未来要走远端部署，这条路线会比直接暴露单片机到公网安全得多。

## 为什么推荐做 OpenClaw 插件

在现有 Mira / Javis 体系中，硬件接入的成熟模式并不是“让大模型随意发 HTTP”，而是：

1. 定义插件配置
2. 注册工具
3. 在工具内部调用外部桥接服务或设备 API

仓库里已经有现成参考：

- `Mi Band` 使用了 `bridgeBaseUrl` 和 `bridgeToken` 形式的插件配置
- `printer bridge` 使用了队列和工具注册形式
- `Hue direct adapter` 展示了直接调用 HTTP 设备接口的方式

因此，对这块 ESP32 来说，最自然的实现方式就是新增一个 `mira-light` 插件。

## 最小可行集成方案

### 第一步：先手动验证单片机 API

在写插件前，先确认设备接口真的能从你的电脑上访问。

假设单片机地址是 `http://192.168.31.42`，可以先测试：

```bash
curl http://192.168.31.42/status
curl http://192.168.31.42/led
curl http://192.168.31.42/actions
```

再测试几个写操作：

```bash
curl -X POST http://192.168.31.42/led \
  -H 'Content-Type: application/json' \
  -d '{"mode":"solid","color":{"r":255,"g":200,"b":120},"brightness":180}'

curl -X POST http://192.168.31.42/action \
  -H 'Content-Type: application/json' \
  -d '{"name":"wave","loops":1}'

curl -X POST http://192.168.31.42/control \
  -H 'Content-Type: application/json' \
  -d '{"mode":"absolute","servo1":90,"servo3":45}'
```

如果这些 `curl` 都成功，说明设备侧接口已经够用了，下一步就只是做 OpenClaw 集成。

### 第二步：给四个舵机补上语义

当前接口里只有：

- `servo1`
- `servo2`
- `servo3`
- `servo4`

这对机器来说是可用的，但对大模型来说不够“语义化”。最好补一份约定，例如：

- `servo1 = base_yaw`
- `servo2 = arm_lift`
- `servo3 = head_pitch`
- `servo4 = head_roll`

这一步非常重要，因为未来当 Claw 需要理解“抬头”“看左边”“探头”“低头”这类自然语言时，必须知道该动哪一个舵机。

如果暂时还不清楚物理含义，也建议先写一张映射表，后续再修正。

### 第三步：定义 OpenClaw 插件配置

下面是一份适合这个设备的最小 `openclaw.plugin.json` 示例：

```json
{
  "id": "mira-light",
  "configSchema": {
    "type": "object",
    "additionalProperties": false,
    "properties": {
      "baseUrl": {
        "type": "string",
        "default": "http://192.168.31.42"
      },
      "requestTimeoutMs": {
        "type": "number",
        "default": 3000
      }
    }
  }
}
```

这份配置只做两件事：

- 告诉插件设备在哪里
- 告诉插件请求多久算超时

如果将来需要鉴权，也可以补：

- `apiToken`
- `basicAuth`
- `allowWrite`

### 第四步：把设备接口包装成 Claw 工具

下面是一个最小 `index.mjs` 思路示例：

```js
const PLUGIN_ID = "mira-light";

function asTextContent(data) {
  return {
    content: [
      {
        type: "text",
        text: typeof data === "string" ? data : JSON.stringify(data, null, 2),
      },
    ],
  };
}

function getCfg(api) {
  return api.config?.plugins?.entries?.[PLUGIN_ID]?.config ?? {};
}

async function callBoard(api, method, endpoint, body) {
  const cfg = getCfg(api);
  const res = await fetch(`${cfg.baseUrl}${endpoint}`, {
    method,
    headers: {
      "Content-Type": "application/json",
    },
    body: body ? JSON.stringify(body) : undefined,
  });

  const text = await res.text();
  const data = text ? JSON.parse(text) : {};

  if (!res.ok) {
    throw new Error(typeof data === "string" ? data : JSON.stringify(data));
  }

  return data;
}

const plugin = {
  id: PLUGIN_ID,
  register(api) {
    api.registerTool({
      name: "mira_light_get_status",
      description: "Read current servo state from the ESP32 board.",
      parameters: {
        type: "object",
        properties: {},
      },
      async execute() {
        return asTextContent(await callBoard(api, "GET", "/status"));
      },
    });

    api.registerTool({
      name: "mira_light_get_led",
      description: "Read current LED state from the ESP32 board.",
      parameters: {
        type: "object",
        properties: {},
      },
      async execute() {
        return asTextContent(await callBoard(api, "GET", "/led"));
      },
    });

    api.registerTool({
      name: "mira_light_set_led",
      description: "Set LED mode, color, and brightness.",
      parameters: {
        type: "object",
        properties: {
          mode: { type: "string" },
          brightness: { type: "number" },
          color: { type: "object" }
        },
      },
      async execute(_id, params) {
        return asTextContent(await callBoard(api, "POST", "/led", params));
      },
    });

    api.registerTool({
      name: "mira_light_run_action",
      description: "Run a preset action such as wave, nod, dance, or curious.",
      parameters: {
        type: "object",
        required: ["name"],
        properties: {
          name: { type: "string" },
          loops: { type: "number" }
        },
      },
      async execute(_id, params) {
        return asTextContent(await callBoard(api, "POST", "/action", params));
      },
    });

    api.registerTool({
      name: "mira_light_stop_action",
      description: "Stop the currently playing action.",
      parameters: {
        type: "object",
        properties: {},
      },
      async execute() {
        return asTextContent(await callBoard(api, "POST", "/action/stop"));
      },
    });

    api.registerTool({
      name: "mira_light_control_servos",
      description: "Directly control raw servo angles on the ESP32 board.",
      parameters: {
        type: "object",
        properties: {
          mode: { type: "string", enum: ["relative", "absolute"] },
          servo1: { type: "number" },
          servo2: { type: "number" },
          servo3: { type: "number" },
          servo4: { type: "number" }
        },
      },
      async execute(_id, params) {
        return asTextContent(await callBoard(api, "POST", "/control", params));
      },
    });

    api.registerTool({
      name: "mira_light_reset_servos",
      description: "Reset all servos to zero position.",
      parameters: {
        type: "object",
        properties: {},
      },
      async execute() {
        return asTextContent(await callBoard(api, "POST", "/reset"));
      },
    });
  },
};

export default plugin;
```

这一层的意义是：

- Claw 不再直接面对零散 HTTP 接口
- Claw 拥有一组语义清晰的工具
- 后续可以很方便地加约束、日志、鉴权和回退逻辑

### 第五步：在 OpenClaw 配置中启用插件

插件准备好之后，需要把它加到 `OpenClaw` 配置中。一个典型配置片段如下：

```json
{
  "plugins": {
    "allow": ["lingzhu", "mira-light"],
    "entries": {
      "mira-light": {
        "enabled": true,
        "config": {
          "baseUrl": "http://192.168.31.42",
          "requestTimeoutMs": 3000
        }
      }
    }
  }
}
```

这样做完后，`OpenClaw` 在运行时就可以调用你定义的 `mira-light` 工具。

## Claw 实际会怎么控制这块板子

接入完成后，控制过程可以理解成“自然语言 -> 工具调用 -> HTTP 请求 -> 单片机执行”。

例如：

### 示例一：打招呼

用户说：

```text
跟我打个招呼
```

Claw 内部可能会选择：

```json
{
  "tool": "mira_light_run_action",
  "args": {
    "name": "wave",
    "loops": 1
  }
}
```

插件再转成：

```http
POST /action
Content-Type: application/json

{"name":"wave","loops":1}
```

### 示例二：把灯调成暖白

用户说：

```text
把灯调成暖白，亮一点
```

Claw 内部可能会选择：

```json
{
  "tool": "mira_light_set_led",
  "args": {
    "mode": "solid",
    "color": { "r": 255, "g": 200, "b": 120 },
    "brightness": 180
  }
}
```

### 示例三：抬头看向我

如果以后已经给 `servo1` 到 `servo4` 建立语义映射，那么 Claw 可以根据高层语义转成：

```json
{
  "tool": "mira_light_control_servos",
  "args": {
    "mode": "absolute",
    "servo1": 90,
    "servo3": 45
  }
}
```

## 高层动作优先，原始角度次之

集成时建议优先让 Claw 调用高层动作，而不是大量直接控制裸舵机角度。

推荐优先级如下：

1. 优先调用预设动作，如 `wave`、`nod`、`shake`、`stretch`、`curious`
2. 其次调用灯效工具，如 `solid`、`breathing`、`rainbow`
3. 最后才开放原始 `servo1` 到 `servo4` 角度控制

这样做的原因有三点：

- 高层动作更稳定，不容易把姿态打乱
- 更符合产品体验，动作更像“有生命的行为”
- 更容易加安全边界，避免模型乱发角度

## 需要特别加上的安全边界

如果后续让 Claw 自动控制硬件，一定要尽早加上这些保护：

### 1. 参数范围限制

- `absolute` 模式下角度必须限制在 `0` 到 `180`
- `relative` 模式下步进幅度不要太大，例如单次不超过 `30` 或 `45`
- `brightness` 限制在 `0` 到 `255`
- `color.r/g/b` 限制在 `0` 到 `255`

### 2. 动作白名单

只允许这些动作名：

- `nod`
- `shake`
- `wave`
- `dance`
- `stretch`
- `curious`

不要让模型随意发未知动作名。

### 3. 写操作开关

如果以后要更安全，可以加入：

- `allowWrite = false`
- `allowServoControl = false`

这样在测试阶段只允许读状态，不允许真动硬件。

### 4. 超时与失败回退

每次请求都要设置超时。

当连续失败或动作中断时，最好支持自动回退到：

- `mira_light_stop_action`
- `mira_light_reset_servos`

### 5. 不要直接暴露到公网

如果这块 ESP32 没有完善鉴权，不应该直接暴露在公网。

更推荐：

- 只放在局域网
- 或只允许本地 bridge 服务访问

## 推荐的实施顺序

如果要从“现在”走到“Claw 真能控制单片机”，建议按下面顺序推进：

1. 确认 ESP32 的固定地址
2. 用 `curl` 验证所有核心接口
3. 梳理 4 个舵机的物理含义
4. 新建 `mira-light` OpenClaw 插件
5. 先只开放读状态和高层动作
6. 确认动作稳定后，再开放底层舵机角度控制
7. 如果 OpenClaw 在远端，再补本地 bridge 层

## 对 Mira Light 项目的直接意义

这条集成路径一旦完成，`Mira Light` 就不再只是一个“能亮、能动的 ESP32 台灯”，而会变成 Mira 体系中的一个实体执行端：

- Mira 负责理解用户状态和上下文
- OpenClaw 负责选择工具和编排动作
- `mira-light` 插件负责把意图翻译成设备 API
- ESP32 负责真正驱动舵机和灯光

也就是说，Mira 的“感知与陪伴逻辑”会通过这块灯具被具象地表达出来。

## 当前阶段最实用的结论

对当前项目来说，最关键的结论可以压缩成一句话：

> `danpianji.html` 已经把设备 API 暴露出来了。下一步不是继续研究 HTML，而是把这些接口正式封装成一个 `OpenClaw` 可调用的 `mira-light` 插件。

只要这一步完成，Claw 就能稳定地“告诉灯做什么”，而不是停留在文档阅读阶段。

