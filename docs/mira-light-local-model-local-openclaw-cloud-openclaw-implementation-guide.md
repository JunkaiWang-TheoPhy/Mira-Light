# Mira Light 接入本机大模型 / 本机 OpenClaw / 云端 OpenClaw 实施指南

## 文档目的

这份文档不是再讲抽象架构，而是给出实际执行顺序。

目标是把下面三条路径具体化：

1. `ESP32 -> 本机大模型`
2. `ESP32 -> 本机 OpenClaw`
3. `ESP32 -> 云端 OpenClaw`

## 第 0 步：所有路径的共同前提

无论接哪条路径，第一步都必须成立：

```bash
curl http://<真实灯IP>/status
curl http://<真实灯IP>/led
curl http://<真实灯IP>/actions
```

如果这三条不通，后面一切都不用继续。

这一步的本质是：

> 先确认真实设备在线，再谈大模型、OpenClaw、bridge、云端。

## 路径 A：接到本机大模型

### 推荐目标

让本机大模型具备：

- 读取灯状态
- 读取图片 / 文件 / 图像帧
- 决定当前进入哪个 scene
- 再调用本机控制链执行

### 建议步骤

#### A1. 启动状态 / 文件接收器

```bash
python3 scripts/simple_lamp_receiver.py
```

默认保存目录：

```text
~/Documents/Mira-Light-Runtime/simple-receiver/
```

#### A2. 如果需要视觉输入，启动图像接收器

参考：

- [`mira-light-vision-stream-and-gemini-summary.md`](/Users/Zhuanz/Documents/Github/Mira-Light/docs/mira-light-vision-stream-and-gemini-summary.md)

当前图像流入口是：

```bash
zsh scripts/setup_cam_receiver_env.sh
zsh scripts/run_cam_receiver.sh
```

#### A2.5. `macOS 13.0` 优先走 `llama.cpp`

```bash
bash scripts/setup_llama_cpp_env.sh
```

这台机器当前更推荐：

- `llama.cpp`
- `Qwen` 官方 `GGUF`
- 先用 `Qwen2.5-3B-Instruct q4_k_m`

当前要特别注意：

- `MLX` 模型文件虽然可以先下载
- 但当前官方 `MLX` runtime 要求 `macOS >= 14.0`
- 所以这台 `13.0` 机器要真正常驻本地推理，应该切到 `llama.cpp`

#### A2.6. 下载官方 Qwen GGUF 到本地

推荐先下轻量且最稳的版本：

```bash
python3 scripts/download_llama_cpp_model.py --model qwen2.5-3b
```

这会下载官方仓库：

- `Qwen/Qwen2.5-3B-Instruct-GGUF`
- 默认文件：`qwen2.5-3b-instruct-q4_k_m.gguf`

如果后续觉得质量还不够，再下 7B：

```bash
python3 scripts/download_llama_cpp_model.py --model qwen2.5-7b
```

这个下载脚本复用了前面那套“可中断恢复”的思路，但目标文件改成了 `GGUF`：

- 从 `Qwen` 官方 Hugging Face `GGUF` 仓库拉取模型
- 下载中断后保留 `.part` 文件
- 再次执行时自动从断点续传
- 对瞬时网络错误自动重试
- 下载前做磁盘空间检查
- 下载后自动对远端文件尺寸做 verify

也可以单独验证本地模型目录是否完整：

```bash
python3 scripts/download_llama_cpp_model.py --model qwen2.5-3b --verify
```

默认下载目录：

```text
~/Library/Caches/Mira-Light/llama-cpp-models/
```

要说明白的一点是：

- 之前已经下载好的 `MLX` 模型文件不能直接给 `llama.cpp` 用
- 现在复用的是下载/续传/verify 的工程思路
- 真正运行时仍然需要重新下载 `GGUF`

#### A2.7. 用 `llama.cpp` 做一次 smoke test

```bash
python3 scripts/smoke_test_llama_cpp.py --model qwen2.5-3b
```

如果你已经下载了 7B，也可以直接指向本地目录：

```bash
python3 scripts/smoke_test_llama_cpp.py \
  --model-dir ~/Library/Caches/Mira-Light/llama-cpp-models/Qwen2.5-7B-Instruct-GGUF \
  --model-file qwen2.5-7b-instruct-q4_k_m-00001-of-00002.gguf
```

这一步的目标不是调优，而是确认三件事：

- `llama.cpp` 在当前机器能正常启动
- 本地 `GGUF` 文件已经可被加载
- 本地生成链路已经通了

对这台 `macOS 13.0` 机器，脚本默认会走更稳的 `CPU-only` 路线，也就是 `-ngl 0`。

#### A2.8. 如果要常驻服务，启动本地 `llama-server`

```bash
bash scripts/run_llama_cpp_server.sh
```

默认监听：

- `127.0.0.1:8012`

当前默认仍然是：

- `Qwen2.5-3B-Instruct q4_k_m`
- `CPU-only`

#### A3. 本机大模型读取输入

输入来源可以是：

- `simple-receiver/snapshots/*.json`
- `simple-receiver/uploads/...`
- `cam_receiver_new.py` 收到的 JPEG 帧

#### A3.1. 把 `Mira / Mira-Light` 自我身份输入给本地 Qwen

不要把整套 workspace 文档原样塞给模型。

原因很直接：

- 本地模型上下文越长，响应越慢
- 前面的实测已经说明，长 prompt 会显著拖慢 `Qwen2.5-3B`
- 所以更推荐“压缩后的身份输入包 + 按需检索的记忆片段”

仓库里现在提供了一个构建脚本：

```bash
python3 scripts/build_mira_qwen_messages.py \
  --user-message "请先介绍你是谁，再说你如何帮助 Mira Light。" \
  --out /tmp/mira-qwen-payload.json
```

这个脚本会把输入分成四层：

1. `system`
   压缩后的 Mira 身份与行为边界
2. `workspace context`
   Mira Light 的稳定身体事实与 scene-first 约束
3. `runtime state`
   可选，当前 scene / 设备状态 / 桥接状态
4. `retrieved memory`
   可选，只把这轮真正相关的记忆片段塞进来

如果你有当前运行时状态，也可以一起带上：

```bash
python3 scripts/build_mira_qwen_messages.py \
  --user-message "当前应该进入哪个 scene？" \
  --state-json runtime/vision-replay/vision.latest.json \
  --memory-snippet Claw-Native\ /workspace/IDENTITY.md \
  --out /tmp/mira-qwen-payload.json
```

更推荐的做法不是直接传完整 `IDENTITY.md`，而是只传这轮检索出的短片段。

#### A3.2. 一条命令问本地 Mira 脑子

如果你已经把 `llama.cpp + Qwen GGUF` 跑起来，仓库现在也提供了一个整合入口：

```bash
python3 scripts/ask_mira_local_qwen.py "请先介绍你是谁，再说你如何帮助 Mira Light。"
```

这个命令会做三件事：

1. 构建压缩后的 `Mira / Mira-Light` 身份输入包
2. 必要时自动拉起本地 `llama-server`
3. 通过本地 OpenAI-compatible 接口请求本地 Qwen，并打印最终回答

默认还会尽量自动补两类上下文：

- 当前 `bridge / runtime / live-vision` 状态
- 基于当前问题的 `openclaw memory search` 检索片段

如果你想同时带入当前状态和额外记忆片段：

```bash
python3 scripts/ask_mira_local_qwen.py \
  "当前应该进入哪个 scene？" \
  --state-json runtime/vision-replay/vision.latest.json \
  --memory-snippet /tmp/retrieved-memory.txt \
  --show-timings
```

#### A4. 大模型不要直接发裸舵机命令

建议先输出：

- `wake_up`
- `curious_observe`
- `touch_affection`
- `celebrate`
- `farewell`

然后调用：

```bash
python3 scripts/booth_controller.py --base-url http://<真实灯IP> <scene-name>
```

或者：

```text
POST http://127.0.0.1:8765/api/run/<scene>
```

#### A5. 当前是否已有完整实现

还没有完整的“本机大模型自动决策器”，但接收器、视觉输入、scene runner 都已经有骨架。

## 路径 B：接到本机 OpenClaw

### 推荐目标

让本机 OpenClaw 把灯当作一个受控工具集，而不是直接拼 curl。

### 建议步骤

#### B1. 本机确认真实设备地址

例如：

```text
http://172.20.10.3
```

只是示例，必须先验证。

#### B2. 启动本地 bridge

```bash
export MIRA_LIGHT_BRIDGE_TOKEN=test-token
zsh tools/mira_light_bridge/start_bridge.sh
```

验证：

```bash
curl http://127.0.0.1:9783/health
```

#### B3. 本地 OpenClaw 安装 / 读取插件

插件目录：

- [`tools/mira_light_bridge/openclaw_mira_light_plugin/`](/Users/Zhuanz/Documents/Github/Mira-Light/tools/mira_light_bridge/openclaw_mira_light_plugin/index.mjs)

应暴露的工具包括：

- `mira_light_list_scenes`
- `mira_light_run_scene`
- `mira_light_status`
- `mira_light_set_led`
- `mira_light_control_joints`
- `mira_light_stop`
- `mira_light_reset`

#### B4. 配置本机 OpenClaw 指向本地 bridge

推荐配置：

```json
{
  "bridgeBaseUrl": "http://127.0.0.1:9783",
  "bridgeToken": "test-token"
}
```

#### B5. 优先让 OpenClaw 调 scene

推荐先暴露：

- `wake_up`
- `curious_observe`
- `touch_affection`
- `celebrate`
- `farewell`
- `sleep`

而不是让模型一上来就直接控制 `servo1~servo4`。

#### B6. 当前是否已有完整实现

当前已经有：

- 本地 bridge 骨架
- 本地 runtime
- 本地 scene runner
- 本地 plugin 骨架

当前还差：

- 真正把插件装进本机 OpenClaw
- 用真实灯地址做端到端实机验证

## 路径 C：接到云端 OpenClaw

### 推荐目标

让云服务器上的 OpenClaw 通过受控本地 bridge 来调用灯，而不是直接访问私网单片机。

### 建议步骤

#### C1. 本地先跑通 bridge

还是先做：

```bash
curl http://127.0.0.1:9783/health
curl http://127.0.0.1:9783/v1/mira-light/status
```

#### C2. 开 reverse tunnel

```bash
MIRA_LIGHT_BRIDGE_REMOTE=ubuntu@43.160.217.153 \
MIRA_LIGHT_BRIDGE_REMOTE_BIND_PORT=19783 \
zsh tools/mira_light_bridge/start_tunnel.sh
```

#### C3. 在服务器上验证

```bash
curl http://127.0.0.1:19783/health
curl http://127.0.0.1:19783/v1/mira-light/scenes
```

#### C4. 云端 OpenClaw 插件配置

应该改成：

```json
{
  "bridgeBaseUrl": "http://127.0.0.1:19783",
  "bridgeToken": "<your-token>"
}
```

#### C5. 云端 OpenClaw 只调插件

不要让云端 OpenClaw 直接访问：

```text
http://192.168.x.x
http://172.20.x.x
```

#### C6. 当前是否已有完整实现

当前已有：

- 路由器中转方案文档
- reverse tunnel 脚本
- bridge 骨架
- OpenClaw 插件骨架

当前未完成：

- 远端插件的最终自动部署
- 云端 OpenClaw 的真实实机接通

## 最推荐的实际推进顺序

### 第 1 步

先打通：

```text
本机 -> 真实灯
```

### 第 2 步

再打通：

```text
本机 bridge -> 真实灯
```

### 第 3 步

再打通：

```text
本机 OpenClaw -> 本机 bridge -> 真实灯
```

### 第 4 步

最后打通：

```text
云端 OpenClaw -> reverse tunnel -> 本机 bridge -> 真实灯
```

### 第 5 步

本机大模型链路作为并行实验线推进，用于：

- 图像理解
- Gemini
- 状态推理
- scene 选择

## 当前阶段最重要的结论

在当前仓库已有文件基础上，最现实的路径不是直接上云，而是：

```text
先接本机
-> 再接本机 bridge
-> 再接本机 OpenClaw
-> 最后接云端 OpenClaw
```

本机大模型路径可以并行存在，但更适合先做感知和实验，而不是作为第一条正式控制链路。
