# Mira Light 图像流与 Gemini 接入现状说明

## 文档目的

这份文档用于把当前已经确认的图像接收、视觉链路、Gemini 调用实测和下一步建议集中整理到一处，避免信息只留在对话记录里。

本文主要回答这些问题：

- 现在本地到底有哪些接收端在跑
- 图像流现在是怎么进来的
- 当前是否已经能把图片送到 Gemini
- Gemini 系列里更适合当前开发环境的是哪条线
- 下一步最合理的工程推进顺序是什么

## 当前系统现状

截至 `2026-04-08`，当前本地已经确认有两条不同的接收链路。

### 1. 图像流接收链路

这条链路的主入口已经切换到：

- [`cam_receiver_new.py`](../docs/cam_receiver_new.py)
- [`run_cam_receiver.sh`](../scripts/run_cam_receiver.sh)
- [`setup_cam_receiver_env.sh`](../scripts/setup_cam_receiver_env.sh)

当前接收端运行特征：

- 监听端口：`8000`
- 接收内容：JPEG 二进制帧
- 提供接口：
  - `POST /upload`
  - `GET /health`
- 运行方式：仓库内 `.venv` 虚拟环境

当前曾观测到的局域网图像流链路是：

```text
转发电脑 172.20.10.13
-> 本机 172.20.10.11:8000
-> cam_receiver_new.py
```

也就是说，这条链路当前更像是：

```text
摄像头/边缘设备
-> 另一台转发电脑
-> 本机图像接收端
```

### 2. 文件/状态接收链路

另一条链路是：

- [`simple_lamp_receiver.py`](../scripts/simple_lamp_receiver.py)

它当前监听：

- 端口：`9784`

作用不是实时视频预览，而是：

- 状态上报
- 文件上传
- 可选 Base64 上传

因此当前仓库里要明确区分：

- `8000`：图像流预览 / JPEG 帧接收
- `9784`：状态与文件接收器

## 当前图像接收链路在工程里的意义

当前已经完成的并不是“视觉理解”，而是“视觉输入接入”。

也就是说，现在已经确认：

- 本机能够收到连续 JPEG 帧
- 接收端能够做实时显示
- 接收端能够提供健康检查
- 接收端已经完成正式化脚本和依赖管理

但目前还没有完整完成的是：

- 从图像帧中提取稳定的视觉事件
- 把视觉事件接到 runtime / scenes
- 把视觉理解结果稳定接到 OpenClaw / Claw

所以当前阶段的正确理解是：

```text
已完成：图像流接入
未完成：图像理解编排
```

## 与 ESP32 控制面的关系

这里要特别避免混淆。

[`ESP32 智能台灯.pdf`](../docs/ESP32%20智能台灯.pdf) 定义的是设备控制面：

- `GET /status`
- `POST /control`
- `POST /reset`
- `GET /led`
- `POST /led`
- `GET /actions`
- `POST /action`
- `POST /action/stop`

而当前 `8000` 上跑的 `cam_receiver_new.py` 不是控制面，而是图像接收面。

这意味着现阶段应该坚持：

```text
图像输入链路
!=
ESP32 控制链路
```

正确系统结构应该是：

```text
图像流
-> 视觉理解
-> 结构化事件
-> runtime / scene selection
-> ESP32 控制 API
```

而不是：

```text
图像流
-> 直接控制舵机
```

## Gemini 方向测试结果

### 当前是否已经能调用 Gemini

是，但要区分“key 是否有效”和“模型是否每次都能成功生成”。

本地实测已经确认：

- Gemini API key 可以列出模型
- 普通 `generateContent` 调用部分模型可以成功
- 部分模型会因为配额或繁忙返回 `429` 或 `503`

因此更准确的判断是：

```text
Gemini API 已可接入
但并非所有模型 / 所有请求当前都稳定成功
```

### 当前看到的相关模型

本地实际列到过这些与当前讨论有关的模型：

- `models/gemini-2.5-flash`
- `models/gemini-2.5-flash-lite`
- `models/gemini-flash-lite-latest`
- `models/gemini-3.1-flash-live-preview`

其中：

- `gemini-2.5-flash`
- `gemini-2.5-flash-lite`
- `gemini-flash-lite-latest`

支持的调用方式是：

- `generateContent`

而：

- `gemini-3.1-flash-live-preview`

支持的是：

- `bidiGenerateContent`

这意味着 `flash-live` 不是普通单次 HTTP 文本/图像请求模型，而是需要走 Live 双向会话。

## Gemini 延迟实测

### 1. 本地接收端延迟

为了测量本地图像接收端延迟，已在 [`cam_receiver_new.py`](../docs/cam_receiver_new.py) 中加入基于 `X-Timestamp` 的延迟统计。

本机模拟送帧的健康检查返回值示例：

```text
status=ok frame_count=4 saved_count=0 latest_seq=local-test-2 latency_samples=4 latency_last_ms=0.8 latency_avg_ms=11.1 latency_min_ms=0.8 latency_max_ms=21.5
```

这说明在本机回环测试里：

- 本地接收延迟大约为毫秒级
- 平均约 `11.1 ms`

这部分不是系统瓶颈。

### 2. 单帧送 Gemini 的实测延迟

当前做过的测试不是 Live 会话，而是：

```text
单张 JPEG 帧
-> generateContent
-> 等模型返回文本
```

测试提示词是：

```text
Reply with OK only.
```

因此成功时模型的返回文本是：

```text
OK
```

### 3. 目前测到的结果

#### `gemini-2.5-flash`

成功返回过两次，实测大致在：

- `1789.4 ms`
- `2334.7 ms`

可粗略理解为：

```text
约 1.8s 到 2.3s
```

#### `gemini-2.5-flash-lite`

成功返回，实测：

- `1646.8 ms`

这是当前成功模型里最好的结果。

#### `gemini-flash-lite-latest`

成功返回，实测：

- `2383.2 ms`

这说明：

- `latest` 别名不一定意味着当前条件下就是最快

#### `gemini-2.0-flash`

调用失败，返回：

- `429 RESOURCE_EXHAUSTED`

#### `gemini-2.0-flash-lite-001`

调用失败，返回：

- `429 RESOURCE_EXHAUSTED`

#### `gemini-3.1-flash-live-preview`

当前还没有测到真实 Live 时延。  
原因不是模型不存在，而是它必须通过：

- `bidiGenerateContent`

也就是 Live 双向会话方式来测，不能直接沿用普通 `generateContent` 的单次请求测试方式。

## 当前环境下应该选 Gemini 还是 GPT

基于当前开发环境，我更推荐：

```text
实时视觉主线优先选 Gemini
```

原因不是 GPT 不强，而是当前项目形态更贴近 Gemini Live 的官方定位。

当前你们已有的是：

- 图片流
- 实时接收端
- 后续希望做视觉理解
- 再接 Claw / runtime / ESP32 控制

这和 Gemini Live 的官方方向更一致：

- 低延迟实时多模态
- 连续视觉输入
- 语义理解和即时响应

相比之下，OpenAI 的 `gpt-realtime` 当前更明显偏向：

- 语音 agent
- 音频输入输出
- 图像辅助输入

因此更合理的系统分工是：

```text
本地 10 FPS / 5 FPS 图像流
-> 本地快速视觉分析
-> 每秒抽 1 帧
-> Gemini Live 或 Gemini Flash
-> 输出高层语义事件
-> Claw / runtime
-> ESP32 控制面
```

## 现在最合理的下一步

### 不建议做的事

当前不建议马上去做：

- 让 Gemini 直接控制舵机
- 把高频视频流全量塞给模型
- 先上 OpenClaw 全量远程编排

### 建议优先做的事

#### 1. 先把图像流变成结构化事件

目标是：

```text
图片
-> 目标检测 / tracking / presence
-> event
```

第一版事件建议只做：

- `target_seen`
- `target_lost`
- `target_moved`
- `target_x`
- `target_y`
- `target_size`

#### 2. 再用 Gemini 做高层语义解释

例如：

- 画面里是不是有人正在观察灯
- 目标是在靠近还是路过
- 当前更适合进入 `wake_up` 还是 `curious_observe`

#### 3. 最后接 Claw / runtime

正确路径应该是：

```text
视觉事件 / Gemini 解释
-> runtime
-> scene selection
-> ESP32 API
```

而不是让 Claw 去直接处理高频原始视频流。

## 推荐推进顺序

建议按下面顺序继续开发：

1. 固定 `cam_receiver_new.py` 的正式运行参数
2. 打开 `--save-dir`，积累真实样本
3. 写最小视觉事件提取器
4. 把视觉事件接到 `mira_light_runtime.py`
5. 再做 Gemini 单帧解释器
6. 最后再做 Gemini Live / Claw 编排接入

## 一句话总结

当前系统已经完成了“图像流接入”，并且已经实测确认：

- 本地接收延迟是毫秒级
- 单帧送 `Gemini 2.5 Flash` 大约是 `1.8s` 到 `2.3s`
- 单帧送 `Gemini 2.5 Flash-Lite` 大约是 `1.65s`
- `Flash Live` 还需要单独走 Live 双向会话才能测真实时延

因此当前最合理的工程路线不是继续扩接收器，而是：

```text
图像流 -> 事件提取 -> Gemini 高层理解 -> runtime -> ESP32 控制
```
