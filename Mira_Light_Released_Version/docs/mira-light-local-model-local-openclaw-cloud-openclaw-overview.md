# Mira Light 本机大模型 / 本机 OpenClaw / 云端 OpenClaw 接入总览

## 文档目的

这份文档专门回答一个问题：

> 在当前仓库已经有的文件、脚本和文档基础上，如何把 `ESP32 Mira Light` 接到：
>
> 1. 本机器上的大模型
> 2. 本机器上的 `OpenClaw`
> 3. 云端的 `OpenClaw`

这里不只讲概念，而是把当前已经存在的实现入口、端口和推荐链路整理到一处。

## 先说一句总原则

`ESP32 Mira Light` 不应该直接“接大模型”。

它更合理的角色是：

- 硬件执行端
- 状态上报端
- 图像 / 文件上传端

而大模型和 `OpenClaw` 更适合扮演：

- 感知解释
- 决策编排
- 工具调用
- 场景选择

所以最清晰的链路应该是：

```text
ESP32
-> 本地接收器 / bridge
-> 本机大模型 或 OpenClaw
-> scene / action 决策
-> 回调 ESP32 控制 API
```

## 当前仓库里已经有的基础能力

### 1. 设备控制面

根据以下文档：

- [`ESP32 智能台灯.pdf`](../docs/ESP32%20智能台灯.pdf)
- [`danpianji.html`](../docs/danpianji.html)
- [`esp32-smart-lamp-delivery-spec.md`](../docs/esp32-smart-lamp-delivery-spec.md)

当前灯已经支持：

- `GET /status`
- `POST /control`
- `POST /reset`
- `GET /led`
- `POST /led`
- `GET /actions`
- `POST /action`
- `POST /action/stop`

### 2. 本机控制层

当前仓库已经有：

- [`scripts/mira_light_runtime.py`](../scripts/mira_light_runtime.py)
- [`scripts/booth_controller.py`](../scripts/booth_controller.py)
- [`scripts/console_server.py`](../scripts/console_server.py)
- [`scripts/scenes.py`](../scripts/scenes.py)

这意味着本机已经具备：

- scene runner
- pose / calibration / operator action 逻辑
- 网页导演台

### 3. 本机状态 / 文件接收层

当前仓库已经有：

- [`scripts/simple_lamp_receiver.py`](../scripts/simple_lamp_receiver.py)

它支持：

- `GET /health`
- `POST /device/status`
- `POST /device/upload`
- `POST /device/upload-base64`

并默认把内容保存到：

[`~/Documents/Mira-Light-Runtime/simple-receiver/`](~/Documents/Mira-Light-Runtime/simple-receiver/)

### 4. 本地图像流接入层

当前仓库已经有：

- [`docs/cam_receiver_new.py`](../docs/cam_receiver_new.py)
- [`scripts/run_cam_receiver.sh`](../scripts/run_cam_receiver.sh)
- [`scripts/setup_cam_receiver_env.sh`](../scripts/setup_cam_receiver_env.sh)
- [`mira-light-vision-stream-and-gemini-summary.md`](../docs/mira-light-vision-stream-and-gemini-summary.md)

当前已知图像流接收端是：

- 监听端口：`8000`
- 输入：JPEG 帧

### 5. 本地 bridge 与 OpenClaw 插件层

当前仓库已经有：

- [`tools/mira_light_bridge/README.md`](../tools/mira_light_bridge/README.md)
- [`tools/mira_light_bridge/bridge_server.py`](../tools/mira_light_bridge/bridge_server.py)
- [`tools/mira_light_bridge/start_tunnel.sh`](../tools/mira_light_bridge/start_tunnel.sh)
- [`tools/mira_light_bridge/openclaw_mira_light_plugin/index.mjs`](../tools/mira_light_bridge/openclaw_mira_light_plugin/index.mjs)

## 一、接到本机器上的大模型

### 最适合的角色分工

```text
ESP32
-> simple_lamp_receiver.py / cam_receiver_new.py
-> 本机大模型应用
-> 选择 scene 或生成控制意图
-> 调用 booth_controller.py / console_server.py / 设备 API
-> ESP32
```

### 这条链路里每层做什么

#### ESP32

负责：

- 上报状态
- 上传图片 / 文件
- 执行动作

#### `simple_lamp_receiver.py`

负责：

- 收状态
- 收图片
- 保存到 `Documents`

#### `cam_receiver_new.py`

负责：

- 收连续 JPEG 图像流
- 供视觉理解系统使用

#### 本机大模型应用

负责：

- 看文本 / 看状态 / 看图像
- 判断当前应该进入哪个 scene
- 决定是否调用：
  - `wake_up`
  - `curious_observe`
  - `touch_affection`
  - `celebrate`
  - `farewell`

#### `booth_controller.py` 或 `console_server.py`

负责：

- 执行 scene
- 将高层场景翻译成真实 HTTP 控制

### 当前最推荐的实现方式

如果现在只想把灯先接到“本机大模型”，最推荐先做：

1. 跑 `simple_lamp_receiver.py`
2. 跑 `cam_receiver_new.py`
3. 写一个本机推理脚本，读取：
   - 最新状态文件
   - 图像帧
4. 推理后调用：

```bash
python3 scripts/booth_controller.py --base-url http://<lamp-ip> wake_up
```

或者调用本地控制台后端：

```text
POST /api/run/<scene>
```

### 这条链路当前是否已经完全接好

没有。

当前状态是：

- 接收器已有
- 图像流接收器已有
- scene runner 已有
- 大模型决策脚本还没有正式落到仓库里

也就是说：

> 本机大模型链路已经有骨架，但还没有最终的“自动决策器”。

## 二、接到本机器上的 OpenClaw

### 最推荐链路

```text
ESP32
-> 本机局域网地址
-> 本机 mira-light bridge
-> 本机 OpenClaw 插件
-> 本机 OpenClaw
```

### 这条链路里每层做什么

#### ESP32

继续提供原始 REST API：

- `/status`
- `/control`
- `/led`
- `/action`

#### 本机 bridge

使用：

- [`tools/mira_light_bridge/bridge_server.py`](../tools/mira_light_bridge/bridge_server.py)

负责：

- 把单片机裸 API 包装成更稳定的受控 bridge
- 提供 scene-first 和 hardware-first 接口

#### 本机 OpenClaw 插件

使用：

- [`tools/mira_light_bridge/openclaw_mira_light_plugin/index.mjs`](../tools/mira_light_bridge/openclaw_mira_light_plugin/index.mjs)

负责：

- 注册工具，例如：
  - `mira_light_list_scenes`
  - `mira_light_run_scene`
  - `mira_light_status`
  - `mira_light_set_led`
  - `mira_light_control_joints`

#### 本机 OpenClaw

负责：

- 通过这些工具调度灯
- 把自然语言转成 scene / 动作调用

### 最适合当前阶段的做法

因为本机 OpenClaw 和灯都在同一局域网，第一阶段最简单做法其实是：

```text
OpenClaw
-> 直接访问 bridge
-> bridge 再访问 ESP32
```

具体上可以做成：

1. 本机启动 bridge：

```bash
export MIRA_LIGHT_BRIDGE_TOKEN=test-token
zsh tools/mira_light_bridge/start_bridge.sh
```

2. 本机 OpenClaw 插件配置：

```json
{
  "bridgeBaseUrl": "http://127.0.0.1:9783",
  "bridgeToken": "test-token"
}
```

3. OpenClaw 只调用插件，不直接碰 ESP32 地址。

### 这条链路当前是否已经完全接好

还没有完全接好，但已经比“本机大模型直连灯”更接近完成。

当前状态是：

- bridge 已有
- plugin 已有
- scene runner 已有
- 缺的是：
  - 真正把插件安装进本机 OpenClaw
  - 用真实灯地址验证 bridge 健康

## 三、接到云端 OpenClaw

### 最推荐链路

```text
ESP32
-> 本地中转枢纽 / 本机 bridge
-> SSH reverse tunnel
-> 云服务器 127.0.0.1:9783
-> 云端 OpenClaw mira-light 插件
-> 云端 OpenClaw
```

### 为什么不能直接云端直连 ESP32

原因已经在这些文档里说明过：

- [`mira-light-router-hub-architecture.md`](../docs/mira-light-router-hub-architecture.md)
- [`mira-light-router-hub-current-status.md`](../docs/mira-light-router-hub-current-status.md)
- [`mira-light-router-hub-implementation-guide.md`](../docs/mira-light-router-hub-implementation-guide.md)

总结起来就是：

- ESP32 通常在私有局域网
- 云服务器看不到 `192.168.x.x` 或 `172.20.x.x`
- 不应该把单片机直接暴露到公网

### 最合理的边界

云端 OpenClaw 应该只看到：

```text
http://127.0.0.1:9783
```

而不是看到真实 ESP32 的私网地址。

### 推荐实施顺序

1. 先在本地把 bridge 跑起来
2. 本地确认：

```bash
curl http://127.0.0.1:9783/health
curl http://127.0.0.1:9783/v1/mira-light/status
```

3. 打 SSH reverse tunnel：

```bash
MIRA_LIGHT_BRIDGE_REMOTE=ubuntu@43.160.217.153 \
MIRA_LIGHT_BRIDGE_REMOTE_BIND_PORT=9783 \
zsh tools/mira_light_bridge/start_tunnel.sh
```

4. 在服务器上验证：

```bash
curl http://127.0.0.1:9783/health
```

5. 云端 OpenClaw 插件配置改成：

```json
{
  "bridgeBaseUrl": "http://127.0.0.1:9783",
  "bridgeToken": "<token>"
}
```

### 这条链路当前是否已经完全接好

没有。

当前状态是：

- 架构和文档已经整理好了
- 本地 bridge 已经有实现
- tunnel 脚本已有
- 远端插件已有骨架
- 但真正“服务器 OpenClaw -> tunnel -> 本地 bridge -> ESP32”还没完成最终实机打通

## 四、这三条路径之间的关系

这三条路径不是互斥的，而是逐层递进的。

### 路径 A：本机大模型

最适合：

- 快速试验
- 视觉理解实验
- 把图片 / 状态 / Gemini 先接起来

### 路径 B：本机 OpenClaw

最适合：

- 做真正的工具编排
- 做 scene / pose / operator action 的本地代理

### 路径 C：云端 OpenClaw

最适合：

- 长期在线
- 脱离这台电脑继续控制
- 真正接入 Mira 体系

## 五、现在最现实的推荐推进顺序

如果按当前仓库真实完成度来排，最推荐的顺序是：

### 第 1 步：先把“本机 -> 真实 ESP32”打通

也就是先确认：

```bash
curl http://<真实灯IP>/status
```

### 第 2 步：再把本机 bridge 打通

让这台电脑的 bridge 可以稳定代理真实灯。

### 第 3 步：再接本机 OpenClaw

因为这一步最接近真实产品链路，而且调试最方便。

### 第 4 步：最后再接云端 OpenClaw

因为这一步依赖本地 bridge 和 tunnel 先稳定。

### 第 5 步：本机大模型链路作为并行实验线

尤其适合视觉理解、Gemini、图像流分析，但不建议作为第一条主控制链路。

## 六、一句话总结

如果你想把这盏灯按“当前仓库已有内容”真正接起来，最清晰的结论是：

```text
ESP32
先接本机
-> 再接本机 bridge
-> 再接本机 OpenClaw
-> 最后通过隧道接云端 OpenClaw
```

其中：

- 本机大模型更适合做感知和实验
- 本机 OpenClaw更适合做本地编排和调试
- 云端 OpenClaw 更适合做长期在线和正式接入

