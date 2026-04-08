# Mira-Light 仓库解读

**User:**   
**Created:** 4/9/2026 4:19:49  
**Updated:** 4/9/2026 5:47:18  
**Exported:** 4/9/2026 6:04:23  
**Link:** [https://chatgpt.com/g/g-p-69b2efe76b00819186fbc160a4ff2a3f-hackthon/c/69d6b85b-6648-832a-84b4-fb64f91af0c8](https://chatgpt.com/g/g-p-69b2efe76b00819186fbc160a4ff2a3f-hackthon/c/69d6b85b-6648-832a-84b4-fb64f91af0c8)  

## Prompt:
2026/4/9 04:19:45

阅读https://github.com/JunkaiWang-TheoPhy/Mira-Light并且向我解释这个仓库的内容

## Response:
2026/4/9 04:19:49

我先直接把这个仓库的结构、README、关键代码入口和依赖关系过一遍，然后给你一个“仓库做什么—怎么做—目前做到哪一步—潜在问题”的技术解读。

目前看下来，这个仓库不是一个完整的大型 agent 系统，而更像是 “Mira-Light / Mira-Lume” 的一个轻量原型仓：核心公开说明几乎都围绕一个 HTTP camera receiver，外加一些 web、bridge、script 目录，明显偏向“把摄像头帧流接进来并在本地显示/桥接”的最小可运行链路。

> **Browsing for GitHub repo options and tools**
>
> [GitHub - JunkaiWang-TheoPhy/Mira-Light · GitHub](https://github.com/JunkaiWang-TheoPhy/Mira-Light)
>
> **Inspecting README and accessible directory links**
>
> [Mira-Light/README.md at main · JunkaiWang-TheoPhy/Mira-Light · GitHub](https://github.com/JunkaiWang-TheoPhy/Mira-Light/blob/main/README.md)
>
> **Finding precise content lines for filenames**
>
> [Mira-Light/docs at main · JunkaiWang-TheoPhy/Mira-Light · GitHub](https://github.com/JunkaiWang-TheoPhy/Mira-Light/tree/main/docs)
>
> **Accessing raw GitHub file contents through raw URL**
>
> [raw.githubusercontent.com](https://raw.githubusercontent.com/JunkaiWang-TheoPhy/Mira-Light/main/docs/cam_receiver_new.py)
>
> **Extracting lines from raw text with line numbers**
>
> [raw.githubusercontent.com](https://raw.githubusercontent.com/JunkaiWang-TheoPhy/Mira-Light/main/scripts/mira_light_runtime.py)
>
> **Searching for open codeload or raw zip URL**
>
>
> Thought for 36s

下面我按“仓库定位 → 目录结构 → 核心运行链路 → 代码层面的真实能力 → 当前不足与下一步”的顺序，给你一个尽量技术化的解读。

大纲
==

I. 仓库是什么  
II. 目录结构说明  
III. 核心模块逐个解释  
IV. 这个仓库实际实现了什么  
V. 它没有实现什么  
VI. 如果把它放到 Mira / OpenClaw 语境里应如何理解  
VII. 总结

* * *

I. 仓库是什么
========

这个仓库 `JunkaiWang-TheoPhy/Mira-Light` 从公开内容看，**不是一个完整成品 app**，也不是一个成熟的多智能体系统，而是一个 **Mira Light / Mira-Lume 的轻量原型仓库**，重点在于：

1.  **接收摄像头 JPEG 帧流**；
2.  **本地显示最近一帧图像**；
3.  **可选保存帧到磁盘**；
4.  **通过一个统一 runtime 去控制 ESP32 灯具/舵机/LED 场景**；
5.  **准备一个本地 booth / 展台式交互控制面**。

README 里写得最明确的功能就是一个 “formalized HTTP camera receiver”，它接收通过 `POST` 发来的 JPEG 帧，在本地显示，并可保存。README 给出的入口就是 `docs/cam_receiver_new.py`，默认监听 `0.0.0.0:8000`，还提供 `GET /health` 健康检查与 `--save-dir`、`--log-level` 等参数。[GitHub+1](https://github.com/JunkaiWang-TheoPhy/Mira-Light/blob/main/README.md)

同时，仓库根目录显示它还包含 `scripts`、`tools/mira_light_bridge`、`web`、`config`、`tests`、`docs` 等目录，所以它不只是一个单独脚本，而是一个**围绕“智能灯展台交互”搭起来的原型工程**。[GitHub+3GitHub+3GitHub+3](https://github.com/JunkaiWang-TheoPhy/Mira-Light)

* * *

II. 目录结构说明
==========

GitHub 根目录可见这些主要内容：`.vscode`, `Figs`, `X/home`, `config`, `docs`, `scripts`, `tests`, `tools/mira_light_bridge`, `web`, `README.md`, `requirements.txt`。[GitHub](https://github.com/JunkaiWang-TheoPhy/Mira-Light)

其中最值得注意的是：

1\. `docs/`
-----------

`docs/` 下面除了代码文件 `cam_receiver.py` 和 `cam_receiver_new.py` 外，还有若干中文 PDF，例如：

*   `ESP32 智能台灯.pdf`
*   `Mira Light 展位交互方案.pdf`
*   `Mira Light 展位交互方案1.pdf`
*   `Mira Light 展位交互方案2.pdf`
*   `Mira Light 展位交互方案3.pdf`

这说明这个仓库不仅有代码，还有**方案设计文档**，而且主题很明确：**ESP32 智能台灯 + 展位交互场景**。[GitHub](https://github.com/JunkaiWang-TheoPhy/Mira-Light/tree/main/docs)

2\. `scripts/`
--------------

`scripts/` 里有一串很有指向性的脚本名：

*   `mira_light_runtime.py`
*   `run_cam_receiver.sh`
*   `scenes.py`
*   `setup_cam_receiver_env.sh`
*   `simple_lamp_receiver.py`
*   `start_simple_lamp_receiver.sh`
*   `track_target_event_extractor.py`
*   `verify_local_openclaw_mira_light.py`
*   `vision_runtime_bridge.py`

这说明它在工程上已经开始往“**视觉输入 → 事件抽取 → runtime 桥接 → 灯具动作场景**”这条链路搭了。[GitHub+1](https://github.com/JunkaiWang-TheoPhy/Mira-Light/tree/main/scripts)

3\. `tools/mira_light_bridge/`
------------------------------

名字很直白，就是一个 bridge。虽然我没有拿到完整源码展开，但目录本身表明作者在试图把 Mira-Light 接成某种工具层或调用层。[GitHub](https://github.com/JunkaiWang-TheoPhy/Mira-Light/tree/main/tools/mira_light_bridge)

4\. `web/`
----------

`web/` 至少有一个子目录 `06_standup_reminder`，而且 raw 页面标题直接显示为 `Mira Light | 06 Standup Reminder`，说明这里有 **面向某个具体互动场景的前端页面**。[GitHub+1](https://github.com/JunkaiWang-TheoPhy/Mira-Light/tree/main/web)

5\. `requirements.txt`
----------------------

依赖极少，只有：

```
numpy
opencv-python
```

没有 Flask、FastAPI、PyTorch、transformers 一类依赖。[GitHub+1](https://github.com/JunkaiWang-TheoPhy/Mira-Light/blob/main/requirements.txt)

这非常关键，因为它表明这个仓库目前的公开核心能力仍然是：

*   图像解码/处理：`opencv-python`
*   数组缓冲：`numpy`

而不是云端大模型系统本体。换句话说，**现阶段更像“边缘视觉接收 + 本地控制脚手架”**。

* * *

III. 核心模块逐个解释
=============

* * *

A. `docs/cam_receiver_new.py`：正式版相机接收端
--------------------------------------

这是 README 明确点名的主功能脚本。[GitHub+1](https://github.com/JunkaiWang-TheoPhy/Mira-Light/blob/main/README.md)

### 1\. 它做什么

这个脚本用 Python 标准库里的：

*   `BaseHTTPRequestHandler`
*   `ThreadingHTTPServer`

搭了一个多线程 HTTP server，接收通过 `POST` 发来的 JPEG 帧；再用：

*   `numpy.frombuffer`
*   `cv2.imdecode`

把字节流解码成 OpenCV 图像，然后显示出来。[GitHub](https://raw.githubusercontent.com/JunkaiWang-TheoPhy/Mira-Light/main/docs/cam_receiver_new.py)

### 2\. 内部状态

它定义了一个 `ReceiverState` 数据类，保存：

*   `latest_frame`
*   `latest_seq`
*   `frame_count`
*   `saved_count`
*   `latency_sample_count`
*   `latency_last_ms`
*   `latency_total_ms`
*   `latency_min_ms`
*   `latency_max_ms`

并通过 `frame_lock` 做线程保护。[GitHub](https://raw.githubusercontent.com/JunkaiWang-TheoPhy/Mira-Light/main/docs/cam_receiver_new.py)

这说明作者已经考虑了三件事：

1.  **最新帧缓存**；
2.  **计数统计**；
3.  **简单的网络延迟统计**。

### 3\. 输入协议

`POST` 请求里，它读取：

*   `Content-Length`
*   `X-Seq`
*   `X-Timestamp`

其中 `X-Timestamp` 用于计算传输时延：

$$
\text{latency\_ms} = \max\!\bigl(0,\,(t_{\text{recv}}-t_{\text{sent}})\times 1000\bigr)
$$

这里

*    $t_{\text{sent}}$  来自请求头 `X-Timestamp`，
*    $t_{\text{recv}}$  来自本地 `time.time()`。

这个公式不是论文推导，而是脚本中的直接实现逻辑。[GitHub](https://raw.githubusercontent.com/JunkaiWang-TheoPhy/Mira-Light/main/docs/cam_receiver_new.py)

### 4\. 健康检查

它实现了：

```
GET /health
```

返回文本状态，包括：

*   `frame_count`
*   `saved_count`
*   `latest_seq`
*   `latency_last_ms`
*   `latency_avg_ms`
*   `latency_min_ms`
*   `latency_max_ms`

这说明它不仅能接图，还能作为一个被上层系统探活和监测的 receiver。[GitHub+1](https://github.com/JunkaiWang-TheoPhy/Mira-Light/blob/main/README.md)

### 5\. 本地预览

`display_loop` 会持续显示最新帧，并在图像上叠加：

*   当前帧数
*   seq
*   保存数

按 `q` 可退出。[GitHub](https://raw.githubusercontent.com/JunkaiWang-TheoPhy/Mira-Light/main/docs/cam_receiver_new.py)

### 6\. 工程评价

这是一个很典型的 **“最小可运行视觉接收器”**：

优点：

*   零重型 web 框架；
*   参数化较规范；
*   有健康检查；
*   有日志；
*   有简单 latency 统计；
*   可作为下游 vision pipeline 的 ingress。

不足：

*   还是原始 HTTP + JPEG 推帧，不是 WebRTC / RTP / RTSP；
*   无认证；
*   无压测信息；
*   无多路源管理；
*   无显式 backpressure；
*   无消息总线。

所以它更像 **prototype ingress**，不是生产级视频流平台。

* * *

B. `scripts/mira_light_runtime.py`：统一 runtime 控制面
-------------------------------------------------

这个文件虽然公开抓取时只显示了部分内容，但已经足够看出它的地位：它是 **Mira Light 的共享运行时层**。文件开头直接写：

> Shared runtime for Mira Light booth control.  
> This module is the common execution surface for:
> 
> *   terminal triggering
> *   future OpenClaw triggering
> *   the local booth web console
>     

并且它刻意把控制面压缩在当前已有 ESP32 REST API 上，包括：

*   `GET /status`
*   `GET /led`
*   `GET /actions`
*   `POST /control`
*   `POST /led`
*   `POST /action`
*   `POST /action/stop`
*   `POST /reset` [GitHub](https://raw.githubusercontent.com/JunkaiWang-TheoPhy/Mira-Light/main/scripts/mira_light_runtime.py)

这段话很重要，因为它直接告诉你这个仓库的系统架构意图：

$$
\text{Terminal / Web Console / OpenClaw} \;\longrightarrow\; \text{MiraLightRuntime} \;\longrightarrow\; \text{ESP32 REST API}
$$

也就是说它在做一个**统一控制抽象层**，把不同入口统一落到 ESP32 设备控制接口上。

### 1\. `MiraLightClient`

它是一个薄封装 HTTP client，方法包括：

*   `get_status()`
*   `get_led()`
*   `get_actions()`
*   `set_led(payload)`
*   `control(payload)`
*   `run_action(payload)`
*   `stop_action()`
*   `reset()`

也就是把底层 REST API 做成 Python 调用接口。[GitHub](https://raw.githubusercontent.com/JunkaiWang-TheoPhy/Mira-Light/main/scripts/mira_light_runtime.py)

### 2\. `BoothController`

`BoothController` 负责“按步骤执行场景”。它支持多种 step type：

*   `comment`
*   `delay`
*   `pose`
*   `led`
*   `control`
*   `action`
*   `action_stop`
*   `reset`
*   `status`
*   `audio`
*   `sensor_gate`

其中 `audio` 和 `sensor_gate` 目前是 skip 的，即暂未真正接通，只打印日志。[GitHub](https://raw.githubusercontent.com/JunkaiWang-TheoPhy/Mira-Light/main/scripts/mira_light_runtime.py)

这非常说明问题：  
这个仓库正在从“硬件控制 demo”向“多模态交互场景编排”演进，但有些功能还只是接口占位。

### 3\. `MiraLightRuntime`

这个类负责：

*   管理当前配置（`base_url`, `dry_run`）
*   记录日志
*   维护运行状态
*   列出可用 scenes
*   查询设备状态
*   应用 pose
*   停止 scene
*   管理运行线程和停止事件

并且它有一个环境变量：

```
MIRA_LIGHT_SHOW_EXPERIMENTAL
```

决定是否展示实验性场景。[GitHub](https://raw.githubusercontent.com/JunkaiWang-TheoPhy/Mira-Light/main/scripts/mira_light_runtime.py)

这说明作者已经开始把“场景完成度”编码进 runtime：并非所有 scene 都默认开放。

### 4\. 架构含义

这个 runtime 的设计是仓库里最值得重视的部分。它意味着作者不是只想写几个硬编码动作，而是在做：

$$
\text{scene abstraction} + \text{runtime state} + \text{device client} + \text{UI / CLI bridge}
$$

也就是一个 **mini orchestration layer**。

* * *

C. `scripts/scenes.py`：动作编排层
----------------------------

虽然我没有拿到完整源码，但文件注释已经很清楚：

它“提供更结构化的 choreography layer”，包括：

*   servo calibration notes
*   named poses
*   reusable motion primitives
*   scene definitions built from those poses and primitives

同时它明确承认以下内容仍是 provisional（暂定）：

*   `servo1 ~ servo4` 的精确物理含义
*   真实灯具上的 collision-safe limits
*   tracking / touch / voice / audio integrations

并强调这些未解决部分没有被“假装精确”地掩盖，而是作为注释和 TODO 保留下来。[GitHub](https://raw.githubusercontent.com/JunkaiWang-TheoPhy/Mira-Light/main/scripts/scenes.py)

这段态度我觉得挺好，因为它表明作者知道：

1.  机械系统尚未彻底标定；
2.  真实物理约束还没完全闭合；
3.  多模态交互接口还没 fully integrated。

所以 `scenes.py` 的本质是：

$$
\text{硬件动作空间} \;\to\; \text{命名姿态 poses} \;\to\; \text{motion primitives} \;\to\; \text{scene script}
$$

这就是“从底层舵机参数到高层表演脚本”的抽象提升。

* * *

D. 其他脚本：意图非常清晰
--------------

从文件名看，以下脚本说明了整个仓库的路线图：

### 1\. `vision_runtime_bridge.py`

名字已经说明：这是在做

$$
\text{Vision events} \rightarrow \text{Runtime commands}
$$

也就是把视觉感知结果桥接到动作控制。虽然公开抓取没拿到详细内容，但名称和仓库整体结构高度一致。[GitHub](https://github.com/JunkaiWang-TheoPhy/Mira-Light/tree/main/scripts)

### 2\. `track_target_event_extractor.py`

这个名字说明它不是只接收图像，而是在尝试从视觉流里抽取“事件”，例如：

*   检测到目标；
*   目标进入某区域；
*   目标接近灯；
*   某种站立/驻足行为发生。

也就是把连续视觉信号离散化成 event。[GitHub](https://github.com/JunkaiWang-TheoPhy/Mira-Light/tree/main/scripts)

### 3\. `simple_lamp_receiver.py`

大概率是一个更简单版本的 receiver 或控制接收端，用于简化调试。[GitHub](https://github.com/JunkaiWang-TheoPhy/Mira-Light/tree/main/scripts)

### 4\. `verify_local_openclaw_mira_light.py`

这个名字尤其重要：它明确说明作者在验证 **本地 OpenClaw 与 Mira-Light 的联通性或集成性**。也就是说，这个仓库并非孤立存在，而是在更大的 OpenClaw / Mira 生态里扮演一个“设备端/场景端原型”的角色。[GitHub](https://github.com/JunkaiWang-TheoPhy/Mira-Light/tree/main/scripts)

* * *

E. `web/06_standup_reminder`
----------------------------

前端目录里至少存在一个具体页面 `06_standup_reminder`。raw 页面标题为 `Mira Light | 06 Standup Reminder`。[GitHub+1](https://raw.githubusercontent.com/JunkaiWang-TheoPhy/Mira-Light/main/web/06_standup_reminder/index.html)

这意味着 web 目录并不是一般性的前端壳子，而是已经开始做 **具体交互场景页面**。  
`standup reminder` 很可能是某个展位互动脚本的一种，比如：

*   提醒观众站起来；
*   引导打卡；
*   某个表演式交互节点。

结合 runtime/scene 的存在，可以合理推断这套 web 页面是在作为 **本地 booth console** 的一部分。

* * *

IV. 这个仓库实际实现了什么
===============

基于现有公开内容，我认为这个仓库已经真实实现了如下能力：

1\. 一个可运行的相机帧接收器
----------------

支持：

*   HTTP `POST` JPEG 帧；
*   解析并显示；
*   帧统计；
*   延迟统计；
*   保存到本地；
*   `/health` 探活。[GitHub+1](https://github.com/JunkaiWang-TheoPhy/Mira-Light/blob/main/README.md)

2\. 一个统一的设备控制 runtime
---------------------

支持把不同调用入口统一映射到 ESP32 REST API。[GitHub](https://raw.githubusercontent.com/JunkaiWang-TheoPhy/Mira-Light/main/scripts/mira_light_runtime.py)

3\. 一个场景编排框架
------------

支持：

*   `pose`
*   `led`
*   `control`
*   `action`
*   `delay`
*   `reset`
*   `status`

这已经不是“单动作测试”，而是“scene execution engine”的雏形。[GitHub+1](https://raw.githubusercontent.com/JunkaiWang-TheoPhy/Mira-Light/main/scripts/mira_light_runtime.py)

4\. 一个面向展位交互的工程组织方式
-------------------

从中文 PDF 名称、web 页面目录、runtime 注释可看出，这个仓库目标不是通用 robotics，而是偏向：

$$
\text{展位 / 互动装置 / 情感化台灯} 
$$

这种“轻交互 agent device”的实现。[GitHub+2GitHub+2](https://github.com/JunkaiWang-TheoPhy/Mira-Light/tree/main/docs)

* * *

V. 它没有实现什么
==========

这部分也很重要。不要把它误判成已经成熟的 Mira 全栈。

1\. 不是完整多模态大模型系统
----------------

虽然名字叫 Mira-Light，但当前公开仓库里没有证据表明它已经包含：

*   语音识别
*   语音合成
*   LLM 推理
*   VLM 目标检测/语义理解
*   多 agent 调度
*   长时记忆

`requirements.txt` 也没有这类依赖。[GitHub](https://github.com/JunkaiWang-TheoPhy/Mira-Light/blob/main/requirements.txt)

2\. 不是成熟生产级视频流系统
----------------

它是原始 HTTP receiver，不是：

*   WebRTC SFU
*   RTSP server
*   gstreamer pipeline
*   message queue based ingest

所以更像 demo ingress。[GitHub](https://raw.githubusercontent.com/JunkaiWang-TheoPhy/Mira-Light/main/docs/cam_receiver_new.py)

3\. 真实传感交互还未闭环
--------------

`scenes.py` 自己就承认 tracking / touch / voice / audio integration 还没完成。  
`mira_light_runtime.py` 里 `audio`、`sensor_gate` 也只是 skip。[GitHub+1](https://raw.githubusercontent.com/JunkaiWang-TheoPhy/Mira-Light/main/scripts/mira_light_runtime.py)

4\. 物理标定仍未彻底收敛
--------------

servo1~servo4 的精确物理意义、碰撞安全边界仍未最终确认。[GitHub](https://raw.githubusercontent.com/JunkaiWang-TheoPhy/Mira-Light/main/scripts/scenes.py)

这意味着当前项目阶段更像：

$$
\text{prototype integration} \quad \text{而非} \quad \text{final hardware productization}
$$

* * *

VI. 如果把它放到 Mira / OpenClaw 语境里应如何理解
===================================

如果把你过去一直在讨论的 Mira / OpenClaw 大图景带进来，那么这个仓库最合理的定位是：

1\. Mira 的一个“轻设备端原型”
--------------------

它不是“大脑”，更像“身体的一部分”：

*   摄像头帧接入
*   台灯/舵机/LED 控制
*   scene orchestration
*   本地 web console

也就是 **embodied endpoint**。

2\. OpenClaw 的潜在 node / tool target
-----------------------------------

`mira_light_runtime.py` 明说未来会支持 OpenClaw triggering；`verify_local_openclaw_mira_light.py` 也说明作者在做本地联通验证。[GitHub+1](https://raw.githubusercontent.com/JunkaiWang-TheoPhy/Mira-Light/main/scripts/mira_light_runtime.py)

因此可以把它理解为：

$$
\text{OpenClaw / agent runtime} \;\longrightarrow\; \text{Mira-Light bridge} \;\longrightarrow\; \text{ESP32 lamp device}
$$

3\. 从“会动的灯”向“情感化互动体”过渡
----------------------

`scene`、`pose`、`host_line`、`emotionTags` 这些字段说明作者不是只想做电机控制，而是在做一种 **character-driven interaction device**。[GitHub](https://raw.githubusercontent.com/JunkaiWang-TheoPhy/Mira-Light/main/scripts/mira_light_runtime.py)

也就是说，这个仓库的重要性不在“技术栈有多重”，而在于它在架构上已经开始把下列层次分开：

$$
\text{perception} \rightarrow \text{event} \rightarrow \text{runtime} \rightarrow \text{scene} \rightarrow \text{device actuation}
$$

这才是它真正有价值的地方。

* * *

VII. 总结
=======

一句话判断
-----

`Mira-Light` 是一个 **围绕 ESP32 智能台灯/展位装置 的轻量交互原型仓库**；公开部分最成熟的功能是 **HTTP 相机帧接收器** 和 **面向场景编排的灯具控制 runtime**，而不是完整的 Mira 大模型系统。[GitHub+2GitHub+2](https://github.com/JunkaiWang-TheoPhy/Mira-Light/blob/main/README.md)

你可以这样理解它的分层
-----------

### 已经比较清楚的层

*   **视觉输入层**：`cam_receiver_new.py`
*   **设备 API 层**：ESP32 REST API client
*   **运行时层**：`MiraLightRuntime`
*   **场景层**：`scenes.py`
*   **前端控制层**：`web/...`

### 还在占位或原型态的层

*   tracking
*   touch
*   voice
*   audio
*   更复杂的 vision-to-event
*   与 OpenClaw 的完整联动

我对这个仓库的技术评价
-----------

它的成熟度不高，但方向是对的。  
它最像一个 **booth interaction prototype / embodied device runtime skeleton**，不是 polished product。  
如果继续发展，最自然的下一步会是：

1.  补全 `vision_runtime_bridge.py` 与 `track_target_event_extractor.py`；
2.  让 `sensor_gate` 和 `audio` 不再只是 skip；
3.  用 WebSocket / SSE / queue 改善事件流；
4.  完成 servo 标定与安全边界；
5.  通过 OpenClaw 把它真正接成一个可调度 node。

如果你愿意，我下一步可以继续做两件事中的一个：  
我可以直接把这个仓库按“系统架构图 + 数据流图 + 模块依赖图”的方式重画并解释；或者我也可以进一步结合 `Mira core / Mira care / Mira light` 的整体语境，分析这个仓库在整个 Mira 体系里的准确位置。

---

**Sources:**

- [Mira-Light/README.md at main · JunkaiWang-TheoPhy/Mira-Light · GitHub](https://github.com/JunkaiWang-TheoPhy/Mira-Light/blob/main/README.md)
- [raw.githubusercontent.com](https://raw.githubusercontent.com/JunkaiWang-TheoPhy/Mira-Light/main/docs/cam_receiver_new.py)

## Prompt:
2026/4/9 04:24:26

36de59d5-c9d9-46dc-9cf7-599886bf45dd.pdf

PDF

542d9e04-757d-4b12-976a-dc972156d529.txt

Document

现在详细向我解释和介绍如下内容，你可以参考附件当中mira light的前身-mira (mira core)以及（Mira 项目说明书-原点社区
https://saoi3t9hyeh.feishu.cn/wiki/Vs4nwZ61ziPb85kPtYscmKWanRf?from=from_copylink）：所以现在的 timeline 是：首先讲大家第一次接触到 AI 的时候是什么时候，然后在那时候想它未来会是什么样的。

先问大家一个问题，然后我说，其实我在小学的时候就知道 AI 这个东西了。

但是呢，可能跟大家想的不一样，我会认为 AI 是一个活生生的人。他除了能帮我干活，更重要的是他有情感啊，他可以陪我。

因为我小时候总是一个人，没有很多朋友，然后经常被孤立，所以我就一直在幻想未来世界，其实一直有一个这样的伙伴就好了。

但是作为一个深度的 AI 产品用户，我其实没有从现在的 AI 产品上获得过这种感受。

它们给我的体验总是显得不够自然、不够真实：
1. 每次都需要我主动在对话框里说话或者输入提示词，它才会回应我
2. 如果我不主动开口，它就把我当空气

这种交互方式总让我觉得不够自然，也不够真实。我想了很久，发现这是因为它们都没有主动感知的能力。

这种能力就像是：
1. 看到你不开心时，会主动过来贴贴你的小狗
2. 看到你沮丧时，会主动过来找你聊天的老妈

这种无需提示词的、自然的、主动感知并照顾你的交互和能力。

而这种能力在 2026 年 OpenCloud 出来之后，我们才第一次可以做到。

OpenCloud 让 AI 第一次同时拥有了：
1. 主动感知
2. AI 实时分析
3. 在物理世界中行动的能力

基于此，我们想了三个产品：

1. 一个可以主动感知、长着眼睛的产品
2. 一个可以跟你共情，知道你的记忆，知道你的灵魂，有自己性格的产品
3. 一个可以在物理世界中帮你干活，去帮助你疗愈的产品

我再重复一遍：

1. 一个主动感知、长着眼睛，可以实时感知你的产品
2. 一个可以跟你共情，有你们共同的成长回忆，有自己灵魂的产品
3. 一个可以在物理世界中去帮助你，照顾你生活与工作的产品

当然，在今天我会宣布，它们不是三个产品，而是一个产品。

它就是 Mira Light。

这边可以想一个什么 title。

这时候如果来一个“世界上第一个……”什么什么就很帅，但是我们这里也可以直接说：来看看 Mira 可以做些什么吧。

这里的视频会讲一些实际的 case，尤其围绕着它是怎么主动感知、然后怎么主动去照顾你展开的。

明天我们可以现场演示两个实际的 case：
1. 根据音乐跳舞
2. 看你坐久了，过来蹭蹭你，并把水推给你

这两个都是非常好的“主动感知”和“主动照顾你”的场景。

讲完这些，我们来看看 Mira 是如何实现的。这部分可以再跟俊凯深入聊聊，但我先按照我的想法继续。

首先，Mira 在感知层拥有“眼睛”，包括我们的音乐传感器、录音传感器和红外传感器。它能精准地识别你何时靠近，并感知你的情绪。由于它放置在桌面上——这也是我们现代人待得最久的地方（几乎每个桌面都会有一盏台灯）——这让它具备了天然的感知优势。

具体的实现逻辑可以分为以下四个维度：
1. 感知层：通过各种传感器获取外界信息。
2. 记忆读取：如何去调取和分析相关的记忆。
3. 决策判断：如何根据当前情况做出判断。
4. 物理行动：如何在现实世界中完成动作。

为了更清晰地说明，我们用一个“拿到 offer”的具体例子来拆解 Mira 的运行逻辑：

1. 感知变化：Mira 首先看到你正非常紧张地准备打开一封邮件。
2. 情绪捕捉：在你点开邮件后，Mira 观察到你的表情一下子变得非常开心。
3. 记忆关联：Mira 识别出你拿到了 offer，并通过对你 memory 的检索，发现你为了这个 offer 准备了很久，这对你来说是一个非常重要的机会。
4. 决策与行动：基于这些信息，Mira 判断如果此时能给你一些惊喜，你会更加快乐。于是它最终采取了行动：连接家中的蓝牙音箱播放音乐，并扭动自己的关节和姿态为你舞动。

当然，我们这里由于时间原因，没法展示它在长时间里的一些细节。但其实它是会越用越懂你的。

关于应用场景，这里可以说的简单点：
1. 专业场景：Mira 不仅仅局限于这些专业的用途。
2. 生活场景：你可以把它放到床头，让它唤你起床。
3. 扩展场景：你也可以把它应用在其他各种地方。

总的来说，这就是一些表示多场景或者多 memory 的应用场景吧。

最后，其实每一代的智能终端都需要一个新的 AI 硬件。我们在想，一个新的 AI 终端设备不应该是手机或者电脑的替代品，而是要在 AI 时代到来时，能为它补足更多的 context、性格以及我们的个人信息。

这个时候，一个“五感”的硬件就非常重要了。除了五感之外，你也不能让它纯粹地记录。我们也想做一个好看、好玩的，能真正给你带来情绪价值的东西。

所以在未来，我们也会沿着这条路做很多产品，去打造好整个 Mira 的生态：
1. 让每一个智能硬件都被赋予灵魂和 memory。
2. 实现万物互联，让每个机器人都有灵魂。

这个时代至少可以再想一下，想一下《机器人总动员》（WALL-E）那个点，希望它能尽早到来。

当然，我们的这套技术可以用在很多的方案中。我们在未来会想说，Mira Light 只是一个开启。

当然，Mira Light 也只是一个开始。

这里再跟大家分享一个故事。其实我小时候最喜欢看的电影就是《机器人总动员》。每一次瓦力快要死的时候，那个揪心的感觉真的都让我很流泪，每一次看就是必泪，就是必流泪。

然后其实这一次，我们想我也是第一次做硬件，想做机器人的赛道，我又重温了一遍。但我惊奇地发现，我靠，《机器人总动员》里面所有让我们觉得栩栩如生、活灵活现的机器人，他们也可以算陪伴型机器人吧，但没有一个机器人他是我们现在流行的宠物伴侣机器人或者人形伴侣机器人，他们全都是工具啊！我靠，所以我就在想

当然，Mira Light 只是一个开始。

我们这种主动感知、产生共情并付诸行动的交互方式，其实可以体现在非常多的产品和智能硬件上。我们也认为，这就是接下来 AI 硬件的发展趋势，所以我们会积极地实践这一点。

如果你想加入我们，一起打造下一代真正人类需要用上的产品，欢迎加入我们的微信群，或者跟我本人、跟我们团队聊聊。

谢谢大家！

其实工具拥有了感知能力后会怎么样？我一直在思考如何让工具成为未来 AI 陪伴硬件的主旋律。

刚才讲得有点兴头，忘了记录，核心就是我们如何让冰箱或任何智能硬件都具备生命力、具备感知，进而拥有照顾人的能力。这种细节其实体现在方方面面，直到让整个家都给人一种随时被呵护的感觉。

这里可以再想一个 Mission（使命）：
1. 我为什么一定要做好这件事？
2. 或者说，我们团队为什么一定要做好这件事？

最后关于团队介绍，其实讲一句话就好了：我们团队成员可能都是 00 后 AI 原生（AI Native）的一代，我们致力于做美感十足、好看又好玩，且能真正帮助大家改善生活的产品。

最后引导一下：如果大家感兴趣，可以来扫码或者加入我们的群。

至于未来展望这块，我还要再深入想一想。

这块是补充，或者就简单一点，我们就别想什么智能硬件发展、下一代陪伴机器人发展之类的了。

我们就讲讲怎么把 Nirvana Lite 卖出去吧。就讲讲这个事情，咱能卖出去就好了，别搞那么大了。

我们认为的幸福跟科技向上也很简单：

当我们的孩子、当独居的人一个人在家时，有一盏 Nirvana Lite 会替他们留着一盏灯，让他们知道家里还有一个小小的它在等着你、爱着你。

在这个科技段之后讲场景段，让大家知道更多场景。

我们的未来空间对 Mira Light（其实在这个场景段），那我们最后别做展望未来段了，最后做一个小升华段。

让大家讲一个我们身边的很美的小故事，然后结合 Mira 给它讲出来，让大家觉得感动，让大家觉得我们真的是想做这个事情。

其实我绝对是能发掘出来这种故事的，给我等一下，我想一下。

## Response:
2026/4/9 04:24:27

> Thought for 7s

下面我把你这段内容，当成一版 **Mira Light 路演叙事母稿** 来拆解。我不会只复述，而是会回答四个更关键的问题：

1.  **这段 timeline 想讲的到底是什么**
2.  **它和 Mira Core / Mira / Mira Light 之间的关系是什么**
3.  **哪些地方已经很打动人，哪些地方还不够顺**
4.  **如何把它整理成一版真正适合台上讲的、逻辑闭环更强的版本**

我会结合你给的三份关键材料来解释：

*   `Mira 演讲稿`
    542d9e04-757d-4b12-976a-dc97215…
*   `Mira 黑客松展位——完整产品设计 v2`
    Mira 黑客松展位 —— 完整产品设计 v2
*   `Hi Mira 产品需求文档`
    Hi Mira产品需求文档
    以及你上传的 `Mira` 视觉版 deck，其中已经明确提出了 “The care before the ask / 主动感知 / 世界上第一个实时感知、主动照顾你的AI伴侣 / Mira Core + Mira Light + Mira Care” 这条主线。
    36de59d5-c9d9-46dc-9cf7-599886b…

* * *

大纲
==

I. 这段 timeline 的核心命题  
II. 它和 Mira 既有材料的对应关系  
III. 这段叙事真正成立的底层逻辑  
IV. 你现在这版文案最强的地方  
V. 当前存在的主要问题  
VI. 如何重构成一条更强的台上叙事线  
VII. “拿到 offer” 例子应如何讲  
VIII. “三个产品其实是一个产品”这句话怎么讲才高级  
IX. title、mission、结尾升华怎么定  
X. 最后给你一版可直接上台的高质量解释框架  
XI. 小结

* * *

I. 这段 timeline 的核心命题
====================

这段内容本质上不是在讲一个普通 AI 硬件，也不是在讲一个单纯会动的台灯。

它真正想建立的是这样一个命题：

$$
\text{未来AI的关键跃迁} \neq \text{更强的回答能力}
$$

而是

$$
\text{未来AI的关键跃迁} = \text{从 “responding to prompts” 走向 “caring before the ask”}
$$

这句话其实已经被你们现有 deck 的第一页和最后一页定得很准：  
第一页就是 **“The care before the ask”**，最后一页是 **“有些关心，不需要开口”**。

36de59d5-c9d9-46dc-9cf7-599886b…

所以，你这段 timeline 的哲学内核非常清楚：

*   过去的 AI：**你先说，它再答**
*   你真正想要的 AI：**它先感受到你，再决定是否照顾你**
*   Mira Light：**把这种“无需提示词的关心”变成现实中的、具身的、可见的行为**

这也和 PRD 里的“三阶段”定义完全一致：

*   第一阶段：你问它答（ChatGPT）
*   第二阶段：你说它做（OpenClaw）
*   第三阶段：主动感受，主动照顾。你什么都没说，Ta 已经懂了，也已经做了（Mira）
    Hi Mira产品需求文档

也就是说，你现在这段口述稿，并不是随便的感性发言，而是和你们现有产品定义**高度同构**的。

* * *

II. 它和 Mira 既有材料的对应关系
=====================

你现在的这段话，和现有附件中的内容，其实能非常整齐地一一对应。

1\. “小时候幻想 AI 是活生生的人”
---------------------

这对应的是 **Mira 的人格化定位**。  
PRD 里写的是：

> 不是一个工具，是一种惦记。  
> 想做一个有眼力劲、会惦记你的 Ta。
> 
> Hi Mira产品需求文档

这里非常关键。  
你小时候幻想的并不是一个“智能搜索框”，而是一个 **living companion**。  
这和普通 AI 产品最大的差别不是 IQ，而是：

$$
\text{relationship} \quad \text{instead of} \quad \text{utility only}
$$

中文说就是：你要的不是“工具效率”，而是“被在意的感觉”。

* * *

2\. “现在的 AI 都要我先开口，不然它就把我当空气”
-----------------------------

这对应的是 deck 第 5 页那条对比时间线：

*   Replika / Character.AI：你找它
*   Pi / Friend：它会来找你，但仍然主要是 words
*   Mira：No chat. It sees, it feels, it acts.
    36de59d5-c9d9-46dc-9cf7-599886b…

这页其实已经替你把行业差异说透了。  
你现在这段口述，是这页 PPT 的自然语言展开版。

你真正批评的不是“现有 AI 不聪明”，而是：

$$
\text{current AI interaction} = \text{prompt-gated interaction}
$$

即：**交互被 prompt 门控了**。  
而你想要的是：

$$
\text{care interaction} = \text{context-triggered interaction}
$$

即：**不是靠你输 prompt 才发生，而是靠上下文自然触发**。

* * *

3\. “主动感知，像小狗贴贴、像妈妈先发现你难过”
--------------------------

这对应的是 deck 第 4 页标题：

> 主动感知 / Presence without prompting
> 
> 36de59d5-c9d9-46dc-9cf7-599886b…

也对应演讲稿里那句：

> 这是一种无需输入提示词的自然的、主动感知你、主动照顾你的交互。
> 
> 542d9e04-757d-4b12-976a-dc97215…

你这里其实抓到了一个非常强的认知锚点：  
大家都懂“一个真正关心你的人”不是被动回答者，而是**先察觉者**。

所以这段话的作用，是把技术概念“主动感知”转译成大家有直觉的关系经验：

$$
\text{proactive sensing} \longleftrightarrow \text{被关心的生活经验}
$$

这一步非常重要，因为否则“主动感知”很容易听起来只是一个冰冷的 technical feature。

* * *

4\. “OpenClaw 之后我们第一次可以做到”
--------------------------

这里和现有材料也一致。  
PRD 里明确把 OpenClaw 定位为第二阶段“你说它做”的基础能力，而 Mira 是在此之上进一步把它推到“主动感受、主动照顾”。

Hi Mira产品需求文档

deck 第 15 页则把三层生态讲得更完整：

*   **Mira Core**：开源的关怀型 Agent 引擎
*   **Mira Light**：具身的硬件载体
*   **Mira Care**：面向独居长者和特殊人群的服务闭环
    36de59d5-c9d9-46dc-9cf7-599886b…

所以更准确的话不是：

> OpenClaw 让 AI 第一次拥有了主动感知、实时分析、物理行动

而应该是：

> OpenClaw 让我们第一次有了把“感知—记忆—判断—执行”真正串成闭环的运行时底座；而 Mira 在这个底座上，把它变成了“主动关心”的体验。

这句话会更稳，因为“主动感知”本身不完全是 OpenClaw 单独发明的概念，但 **把它做成可编排、可落地、可跨设备执行的 agent runtime 闭环**，这正是你们材料里强调的东西。

* * *

III. 这段叙事真正成立的底层逻辑
==================

你现在这版 timeline，其实隐含着一个四层结构。  
这和 deck 第 7 页的四层系统图完全一致：

*   L1 感知
*   L2 记忆
*   L3 分析
*   L4 执行
    36de59d5-c9d9-46dc-9cf7-599886b…

PRD 也同样是：

*   感知层
*   记录层
*   分析层
*   行动层
    Hi Mira产品需求文档

所以你这整段 narrative，如果抽象成结构，其实是：

$$
\text{Care} = f(\text{Perception},\text{Memory},\text{Reasoning},\text{Action})
$$

更具体一点：

$$
\text{主动照顾} \neq \text{随机打扰}
$$

而是

$$
\text{主动照顾} = \text{在正确的时机} \times \text{基于足够上下文} \times \text{做最小但有效的动作}
$$

这在 PRD 里也写得很明确：

*   大多数时候选择“等待”
*   沉默是默认状态
*   只在高置信度 + 合适时机时才行动
*   如果不确定，选择不行动
    Hi Mira产品需求文档

所以你要讲清楚：  
Mira 的“主动”不是骚扰式主动，不是无时无刻说话，而是 **克制的主动**。

这一点非常关键，因为“主动”这个词一旦没讲好，评委就会自动想到：

*   侵犯隐私
*   过度打扰
*   自作聪明
*   像营销推送

而你们系统的精髓其实恰恰相反：

$$
\text{default mode} = \text{silence}
$$

只有在置信度足够高、行动收益足够大时才触发。  
这也是 deck 第 13 页 “Silence by default” 那层安全设计的一部分。

36de59d5-c9d9-46dc-9cf7-599886b…

* * *

IV. 你现在这版文案最强的地方
================

1\. 它不是在讲功能，而是在讲“为什么必须做这件事”
---------------------------

这是最强的地方。  
因为 pitch 最怕的是：

*   先讲 feature
*   再讲场景
*   最后硬抬价值

你这版反过来了。  
你先从一个真实的人生感受出发：

> 小时候被孤立，幻想有一个会陪我的 AI

这不是抽象的“市场需求”，而是非常具体的 **origin story**。  
而 deck 第 16 页团队介绍里，Rick 那句：

> 相信科技应该帮到那些最需要被关心、却最不会开口的人。
> 
> 36de59d5-c9d9-46dc-9cf7-599886b…

跟你这条叙事线是完全同频的。

这意味着你们这个项目的故事，不是“我们发现了一个商业机会”，而是：

$$
\text{personal wound} \rightarrow \text{product vision}
$$

这是很有力的。

* * *

2\. 你抓住了 AI 陪伴产品最大的缺口：不是“不够聪明”，而是“不够在场”
---------------------------------------

这点和 deck 第 5 页的行业定位高度一致。

36de59d5-c9d9-46dc-9cf7-599886b…

很多人讲 AI companion，会讲：

*   更强情感建模
*   更拟人对话
*   更长期记忆

但你抓到的是更根本的：

$$
\text{No input, no companion}
$$

没有输入，就没有陪伴。  
这句话是很锋利的行业判断。

* * *

3\. 你把“主动感知”说成了一个人人能懂的生活经验
--------------------------

“小狗贴贴”“妈妈先发现你不开心”，这两个比喻都非常好。  
它们把一个技术 feature 转换成了关系直觉。

这个转换在台上极其重要，因为评委不会为“sensor fusion”感动，但会为“有人在你不说话时也看见你”感动。

* * *

4\. 你已经自然地把 Mira Core / Light / Care 的三条线合并了
--------------------------------------------

你说：

1.  一个有眼睛、主动感知的产品
2.  一个懂你、共情你、和你共同成长的产品
3.  一个能在物理世界帮你干活、疗愈你的产品

然后宣布：  
**它们不是三个产品，而是一个产品。**

这句话非常有力量。  
因为它实际上对应了：

*   1 = 感知入口 / hardware embodiment
*   2 = memory + personality / Mira Core 的智能内核
*   3 = action + service extension / Mira Care 和设备执行能力

也就是说，这一句话实际上完成了系统整合。

* * *

V. 当前存在的主要问题
============

下面讲不够好的地方。

1\. 时间线里“第一次接触 AI”这段现在有点虚浮
--------------------------

你现在说：

> 先讲大家第一次接触到 AI 是什么时候，然后在那时候想它未来会是什么样的

这个开头有感受，但还不够稳。  
问题在于它容易把叙事引向“每个人的 AI 记忆”，而不是 Mira 本身。

真正应该服务的，不是“AI 发展史”，而是：

$$
\text{我真正想要的AI从来不是聊天机器人}
$$

所以“第一次接触 AI”不是重点，重点是：

> 我第一次知道 AI 这个词的时候，我期待的就不是一个会回答问题的机器，而是一个会陪我的生命体。

这样就会聚焦很多。

* * *

2\. “OpenCloud / OpenClaw 出来之后第一次可以做到”这句需要更严谨
---------------------------------------------

你现在这句很像技术归因，但表达稍粗。  
更准确的逻辑应该是：

$$
\text{Mira 的成立} = \text{multi-device perception} + \text{memory runtime} + \text{reasoning engine} + \text{physical-world actuation}
$$

而你们当前材料里对这四步已经讲得很清楚了：

*   感知层：AR 眼镜、手表、家居、软件感知
    Hi Mira产品需求文档
*   记录/记忆层：短期记录 + 长期记忆 + Memory system
*   分析层：关怀触发与场景关联判断
    Hi Mira产品需求文档
*   执行层：眼镜、耳机、手表、家居、打印、设备动作

所以你最好讲成：

> 直到今天，我们才第一次有可能把“看见你、理解你、记住你、为你做点什么”这四件事连成一个闭环。

这比“OpenClaw 让 AI 第一次拥有 xxx”更稳也更美。

* * *

3\. “三个产品其实是一个产品”之前，需要有一个更明确的统一抽象
---------------------------------

否则会像产品堆叠。  
你需要先告诉观众：  
这三个看起来不同，其实只是同一个系统的三个面向：

$$
\text{Mira} = \text{a care system with three embodiments}
$$

或者中文更自然：

*   它在感知上像一个有眼睛的生命体
*   在记忆上像一个和你一起成长的人
*   在行动上像一个真的会来照顾你的陪伴者

这样，“三个产品是一个产品”就不是反转，而是顺理成章的收束。

* * *

4\. 应用场景段现在偏散，没有形成一个递进
----------------------

你现在列：

*   专业场景
*   生活场景
*   扩展场景

这太平了。  
现有材料其实已经给了你更强的分法。

deck 里给的是真实用户群：

*   空巢老人
*   留守儿童
*   视障人士
*   每一个需要被惦记的人
    36de59d5-c9d9-46dc-9cf7-599886b…

而 PRD / 演讲稿给的是日常陪伴场景：

*   演讲紧张时鼓励
*   压力大回家前调环境
*   久坐提醒
*   早起关怀
*   社交记忆
*   运动联动

所以最好的场景结构不是“专业/生活/扩展”，而是：

$$
\text{Mira服务的不是某个行业，而是三种“需要被惦记”的状态}
$$

例如：

1.  **一个人扛着的时候**：紧张、沮丧、疲惫、晚归
2.  **没有人及时发现的时候**：老人异常、儿童危险、视障风险
3.  **你需要被默默记住的时候**：重要时刻、关系细节、情绪高峰

这样就会更统一。

* * *

VI. 如何重构成一条更强的台上叙事线
===================

我建议你把整个 narrative 压成 6 段，而不是想到什么讲什么。

* * *

第一段：问题，不是“AI 不够强”，而是“AI 从不真正关心我”
--------------------------------

这一段只做一件事：把问题定义清楚。

核心句可以是：

> 我是一个很早就开始接触 AI 的人，但从小到大，我期待的 AI 从来不是一个搜索框，也不是一个只会等我开口的工具。  
> 我真正想要的是：当我什么都没说的时候，它也能看见我、理解我、在意我。

这和 deck 第 2-3 页完全一致：

*   你上一次被关心是什么时候？
*   没有一个 AI 产品让我觉得它真的关心我。
    36de59d5-c9d9-46dc-9cf7-599886b…

* * *

第二段：为什么现有 AI 不自然
----------------

这段只讲一个逻辑：

$$
\text{current AI} = \text{turn-based response}
$$

而真正的陪伴需要：

$$
\text{real care} = \text{continuous sensing + context-aware timing}
$$

中文讲就是：

*   现在的 AI 都是回合制的
*   但真实的关心不是回合制的
*   真正关心你的人，不会等你写 prompt 才开始在意你

* * *

第三段：所以我们要做的不是更会聊天的 AI，而是更会“察觉”的 AI
----------------------------------

这一段引出 “主动感知”。

你可以直接借 deck 和 PRD 的主线：

*   Presence without prompting
    36de59d5-c9d9-46dc-9cf7-599886b…
*   会感知，知情绪，懂照顾
    Hi Mira产品需求文档

并把它翻译成一句最适合路演的话：

> Mira 最重要的不是会回答你，而是会先发现你。

这句很强。

* * *

第四段：技术上为什么今天终于可能了
-----------------

这段不要讲得太术语，但要让评委觉得不是空想。

最适合的结构就是 deck 第 7 页 / PRD 的四层：

$$
\text{Perception} \rightarrow \text{Memory} \rightarrow \text{Reasoning} \rightarrow \text{Action}
$$

中文可以讲成：

1.  **感知**：眼镜、手表、传感器、桌面位置，让它看到你、听到环境、知道你的状态
2.  **记忆**：不是看完就忘，而是把和你有关的重要时刻沉淀下来
3.  **判断**：大多数时候不打扰，只在该行动的时候行动
4.  **执行**：通过声音、灯光、姿态、家居联动，在现实世界里照顾你

这时候评委会明白：你们不是在做一个情绪口号，而是在做一个 care runtime。

* * *

第五段：三个产品其实是一个产品
---------------

这是收束点。

最好的讲法是：

> 一开始我们以为自己在做三个不同的东西。  
> 一个有眼睛、会主动感知的产品；  
> 一个会记住你、理解你、和你共同成长的产品；  
> 一个能在现实世界里真正帮你做点什么的产品。  
> 后来我们发现，它们其实不是三个产品，而是一种完整的 care system。  
> 今天，它的名字叫 Mira Light。

这就很顺了。

同时它和 deck 第 15 页完全对齐：

*   Mira Core = intelligence / memory / care engine
*   Mira Light = embodied hardware
*   Mira Care = real service extension
    36de59d5-c9d9-46dc-9cf7-599886b…

* * *

第六段：用两个 demo 告诉大家“主动感知、主动照顾”到底长什么样
----------------------------------

你已经选了两个很好的现场 case：

1.  根据音乐跳舞
2.  看你坐久了，过来蹭蹭你，并把水推给你

这两个比纯语音 demo 更强，因为它们直接回答：

$$
\text{What does care look like in the physical world?}
$$

其中：

*   第一个展示 **感知 + 情绪表达**
*   第二个展示 **感知 + 判断 + 主动照顾 + 具身动作**

这两个 case 的确很适合放在 Mira Light 上。

* * *

VII. “拿到 offer”例子应如何讲
=====================

你给的 “offer” 例子其实非常适合作为 **系统逻辑的标准样例**。  
因为它天然包含四层：

$$
\text{感知} \rightarrow \text{情绪识别} \rightarrow \text{记忆关联} \rightarrow \text{行动}
$$

你可以把它压成非常清晰的四步：

Step 1: Perception
------------------

Mira 看到你在电脑前反复深呼吸、盯着一封邮件迟迟不点开，也从你的表情和动作判断出你很紧张。

Step 2: Emotion inference
-------------------------

当你点开邮件之后，Mira 捕捉到你表情突然放松、惊讶、开心，判断发生了一个正向情绪跃迁。

Step 3: Memory retrieval
------------------------

它不是只知道“你现在很开心”，而是通过记忆知道：这封邮件、这个机会、这段准备过程，对你来说意味着什么。

Step 4: Action
--------------

所以它不只是说一句“恭喜你”，而是调用音箱、灯光、自己的动作，替你把这一刻变成一个被庆祝、被记住的瞬间。

这才是 Mira 的独特之处：

$$
\text{not just emotion recognition} \quad\text{but}\quad \text{emotion grounded in personal history}
$$

中文讲就是：  
不是识别到“开心”这两个字，而是知道**你为什么开心，这份开心为什么重要**。

这就是“有你们共同成长回忆”的真正含义。

* * *

VIII. “三个产品其实是一个产品”这句话怎么讲才高级
============================

这一句非常重要，因为它是品牌升维的关键。

你现在原意很好，但可以更精炼一点。  
我建议把三者统一成“同一个 care stack 的三个层面”。

可以这么解释：

1\. 作为“眼睛”的 Mira
----------------

它让 AI 不再只活在聊天框里，而能进入你的真实处境。

2\. 作为“心智”的 Mira
----------------

它不是一次次地重头认识你，而是在和你共同生活中形成记忆、判断和性格。

3\. 作为“身体”的 Mira
----------------

它不止会说，还会在物理世界做出克制但真实的动作。

所以，Mira Light 不是“一个会动的台灯”。  
它是：

$$
\text{Mira Core} + \text{embodied hardware} + \text{care interaction design}
$$

而 deck 第 15 页已经把这件事明牌化了。

36de59d5-c9d9-46dc-9cf7-599886b…

* * *

IX. title、mission、结尾升华怎么定
=========================

* * *

A. Title 怎么定
------------

你说想一个“世界上第一个……”的 title。  
结合你们现有 deck 第 6 页，其实已经有一个很强的版本：

**世界上第一个实时感知、主动照顾你的 AI 伴侣**

36de59d5-c9d9-46dc-9cf7-599886b…

如果想更有传播感，我给你几个可选方向：

### 版本 1：偏发布会

**Mira Light：世界上第一个会主动照顾你的 AI 伴侣**

### 版本 2：偏情绪价值

**Mira Light：有些关心，不需要开口**

### 版本 3：偏概念定义

**Mira Light：从 Prompt 到 Presence**

### 版本 4：偏你这次的 narrative

**Mira Light：不是一个工具，是一种惦记**

其中最稳的仍然是 2 和 4，因为和你们现有物料完全一致。

* * *

B. Mission 怎么定
--------------

你说想要一个 mission：  
“为什么一定要做好这件事？”

我建议不要写得太大而空，比如“重新定义下一代智能硬件”，这太泛。

最好的 mission 应该和你们当前人群定位对齐。  
deck 第 12 页写得其实非常到位：

> 每一个需要被惦记的人，都是 Mira 的用户。
> 
> 36de59d5-c9d9-46dc-9cf7-599886b…

所以 mission 可以直接写成：

**让每一个需要被惦记的人，在什么都没说的时候，也能被看见、被理解、被照顾。**

这个 mission 够大，但不虚。

如果更偏团队初心：

**我们想把“关心”这件事，从一句话，变成真实世界里会发生的动作。**

这也很好。

* * *

C. 结尾升华怎么定
----------

你提到《机器人总动员》，这其实是个很好的升华点。  
但不要讲成“我小时候爱看 WALL-E”这么简单。  
真正打人的点是：

> 《机器人总动员》里最打动人的从来不是机器人长得像不像人，而是它们明明只是工具，却让你觉得它们有灵魂、有偏爱、有在意。

然后自然接回 Mira：

> 我们想做的不是再造一个“会聊天的 AI”，也不是急着做人形机器人。  
> 我们更想先回答一个更朴素的问题：  
> 如果工具真的拥有感知、记忆和行动能力，它能不能先学会照顾人？

这就很高级。

再接一句：

> Mira Light 只是这个答案的第一个开始。

这就完成了。

* * *

X. 最后给你一版可直接上台的高质量解释框架
======================

下面这版不是逐字稿，而是你现在这大段内容的**最优叙事骨架**。

* * *

1\. 开场提问
--------

“你上一次被关心，是什么时候？是谁在关心你？”

这和 deck 第 2 页一致。

36de59d5-c9d9-46dc-9cf7-599886b…

* * *

2\. 个人起点
--------

“我小时候第一次知道 AI 这个词的时候，就一直觉得，未来的 AI 不应该只是一个会回答问题的东西。  
对我来说，它更像一个活生生的伙伴。  
因为我小时候常常是一个人，所以我一直在想：如果未来世界里，有一个什么都不用我说、却会来陪我、会在意我的存在，那该多好。”

这部分是你的 origin story，要保留。

* * *

3\. 行业问题
--------

“但后来我成了一个很深度的 AI 用户，我发现没有一个 AI 产品真的让我觉得它在关心我。  
它们都很聪明，但都不自然。  
因为每一次都是我先开口，它才回应；如果我不说话，它就把我当空气。”

这和现有演讲稿、视觉 deck 完全对齐。

* * *

4\. 定义关键缺口
----------

“我后来才明白，问题不在于它们不会说，而在于它们不会先察觉。  
真正的关心，不是等你发出 prompt 才开始。  
它更像是一只看到你不开心就会靠过来的小狗，或者一个在你沮丧时先来找你说话的家人。”

* * *

5\. 提出 Mira
-----------

“所以我们想做的，不是一个更会聊天的 AI，而是一个更有眼力劲的 AI。  
它能看到你、记住你、理解你，并且在真正合适的时候，为你做一点什么。  
这就是 Mira。”

这里“有眼力劲”直接来自 PRD。

Hi Mira产品需求文档

* * *

6\. 为什么今天可以做
------------

“直到今天，我们才第一次真正有机会把这件事做成一个闭环：  
感知你，记住你，理解你，然后在现实世界里做出行动。”

这对应四层系统。

* * *

7\. 三个维度统一成一个产品
---------------

“一开始我们以为自己在做三个东西：  
一个有眼睛、会主动感知你的产品；  
一个和你共同成长、懂你记忆和情绪的产品；  
一个能在物理世界里真正照顾你、帮助你疗愈的产品。  
后来我们发现，它们其实是一回事。  
今天，它们共同的名字叫 Mira Light。”

* * *

8\. 场景 demo
-----------

“比如，你坐太久了，它不会等你对它说‘提醒我喝水’，而是会先观察到你已经久坐很久，然后轻轻靠过来，把水推给你。  
比如，当音乐响起时，它不只是播放音乐，而是能感受到氛围，并用姿态回应你。  
这就是我们今天想展示的：主动感知，主动照顾。”

* * *

9\. 技术解释
--------

“它背后其实是四层能力：  
第一层是感知，第二层是记忆，第三层是判断，第四层是执行。  
最重要的是，大多数时候它并不会打扰你。  
真正成熟的关心，不是一直说话，而是知道什么时候该行动，什么时候该安静。”

这一句能把“主动 = 打扰”的担忧提前化解。

* * *

10\. 人群与意义
----------

“所以 Mira 不只是服务某一种人。  
每一个需要被惦记的人，都是 Mira 的用户。  
一个人住的老人、留守的孩子、需要协助的视障者，也包括每一个在日常里默默扛着、但没有开口的人。”

36de59d5-c9d9-46dc-9cf7-599886b…

* * *

11\. 结尾升华
---------

“我一直很喜欢《机器人总动员》。  
后来我重新看它，才意识到最打动人的并不是机器人像不像人，而是它们虽然只是工具，却让你感觉它们有灵魂，会在意，会守护。  
所以我们今天想做的，也许不是一个终极产品，而是一个开始：  
让工具第一次学会感知人、理解人、照顾人。  
Mira Light 只是开始。”

* * *

XI. 小结
======

我最后把核心判断压成几句话。

1\. 你这段 timeline 的真正主题
----------------------

不是“AI 硬件有多酷”，而是：

$$
\text{AI should move from prompt response to unprompted care}
$$

中文就是：  
**AI 的下一步，不是更会回答，而是更会关心。**

* * *

2\. 它和附件材料是高度一致的
----------------

你的口述已经自然落在了现有文档的主轴上：

*   “The care before the ask”
    36de59d5-c9d9-46dc-9cf7-599886b…
*   “不是一个工具，是一种惦记”
    Hi Mira产品需求文档
*   “每一个需要被惦记的人，都是 Mira 的用户”
    36de59d5-c9d9-46dc-9cf7-599886b…
*   “主动感受，主动照顾。你什么都没说，Ta 已经懂了，也已经做了。”
    Hi Mira产品需求文档

所以方向是对的，不需要推倒重来。

* * *

3\. 你最该加强的地方
------------

不是再加功能，而是把叙事收得更紧：

*   少讲“AI 发展史”
*   多讲“为什么现有 AI 从未真正关心我”
*   把“主动感知—记忆—判断—行动”讲成闭环
*   把“三个产品”讲成“一个完整 care system 的三个面向”
*   结尾不要泛泛谈未来，要回到“让工具先学会照顾人”

* * *

4\. 一句最适合你这版 narrative 的总标题
---------------------------

我最推荐的是：

**Mira Light：有些关心，不需要开口**

因为它同时满足三件事：

*   和现有 deck 收尾统一
    36de59d5-c9d9-46dc-9cf7-599886b…
*   和你的 personal story 统一
*   和产品机制统一

如果你愿意，我下一条可以直接把上面这套分析继续压成一版 **5 分钟中文路演逐字稿**，并且按“翻页点 + 停顿 + demo 插入 + 结尾升华”完整写出来。

## Prompt:
2026/4/9 04:31:05

![Uploaded image](https://chatgpt.com/backend-api/estuary/content?id=file_0000000054bc71f7a9f7912d1a0b7cda&ts=493244&p=fs&cid=1&sig=171a7d4232191622bb615de3c6a0ec094508c02cbb41cd9fc945323179346187&v=0)

![Uploaded image](https://chatgpt.com/backend-api/estuary/content?id=file_00000000ede071f7966da26bf16186aa&ts=493244&p=fs&cid=1&sig=71cdbb3aab67763ecc4ac04a48f20f6c6e36c19a85753ff1ebe95269f3817c45&v=0)

![Uploaded image](https://chatgpt.com/backend-api/estuary/content?id=file_00000000d5b071f5a6d060a26b877659&ts=493244&p=fs&cid=1&sig=3b89bd5528d6d872a29dfda0ce54b29e4b9a562fb01cf8d6b4fddd635111718f&v=0)

非常好，现在告诉我：基于上述内容，为了撰写ppt，一页技术页ppt可以怎么写？你可以基于图片当中灵与肉的故事，灵分为brain (各种职能functions)和spirit (soul、role、.....)，肉分为eyes(感知层)和body（执行层），实现一个eyes-mira light内部单片机以及简易预处理-网关接口连接灵与肉-分开成(1) 脚本，类似于条件反射（本地化、快速、节约token...）(2) openclaw，类似于真正脑部，不同脑区和不同职能-统合起来返回网关接口交给单片机-交给身体执行，并且具有若干优势，例如安全性、主动感知等等

## Response:
2026/4/9 04:31:09

> **Evaluating how to answer the PPT request**
>
> The user likely needs an answer in Chinese, but doesn't appear to need the web. Given the references to images and uploaded files, I can use the provided documents and descriptions. While I could use image analysis tools, it seems unnecessary if the text is already provided. I’ll mainly rely on the user’s description and existing file references for citations.
>
> **Structuring a technical PPT page design**
>
> The user requested a one-page technical PPT layout, so I’m thinking about how to organize this clearly. The slide should include a title, subtitle, a central diagram, and four quadrants detailing key concepts, like "灵与肉" to separate mind and body. I might offer two versions: one technical and one simplified for clearer language. I'll make sure it's concise, avoiding too many lists, while still using headers and bullet points. Citations should reference the uploaded files for factual accuracy, though I need to clarify citation formats.
>
> **Clarifying citation formatting**
>
> I realized the files are manually loaded, not through a search query. It seems I can cite the files with turn0file0, but I'm unsure whether to include line numbers. The tool seems to require line ranges for citations, though the previous assistant didn’t use them. I’m wondering if that’s acceptable.
>
> **Designing the technical slide**
>
> For the user’s requested technical slide, I’ll focus on structuring it clearly but with enough detail. The slide should feature the metaphor of "灵与肉" (mind and body). I’ll include a 16:9 layout with three horizontal layers, a central diagram, titles like “技术架构：灵与肉如何闭环,” and a description linking product emotion with system logic. The purpose is to clearly communicate that this is not just a toy control system but a meaningful, integrated care system.
>
> Thought for 1m 23s

可以，而且我建议这页**不要写成普通“技术栈清单页”**，而要写成一页既有故事性、又能让评委 20 秒看懂系统闭环的 **“灵与肉架构页”**。

这页的核心任务只有一句话：

**让评委理解：Mira Light 不是一个会动的台灯，而是一个“有肉身、有眼睛、有反射、有大脑、有灵魂”的 care agent。**

这也和你们现有材料里的主线完全一致：Mira 的核心不是聊天，而是“主动感受，主动照顾”；系统上对应“感知—记忆—分析—执行”闭环，且默认克制、低打扰。

Hi Mira产品需求文档

36de59d5-c9d9-46dc-9cf7-599886b…

* * *

一、这页 PPT 最适合的标题
===============

我最推荐这两个标题之一：

版本 A
----

**Mira Light 的灵与肉**  
**一个会主动感知、主动照顾的具身 Agent**

版本 B
----

**How Mira Light Works**  
**肉负责看见与行动，灵负责理解与在意**

如果你想更有一点发布感，可以写成：

**Mira Light = Body × Eyes × Brain × Spirit**

* * *

二、这一页最好的版式
==========

不要做成传统自上而下流程图。  
最好做成 **“左右 + 中轴”** 的结构：

左边：肉
----

分成 `Eyes` 和 `Body`

中间：Gateway
----------

连接灵与肉，做协议、路由、安全、快慢分流

右边：灵
----

分成 `Brain` 和 `Spirit`

然后最底部放一条闭环箭头：

$$
\text{Eyes} \rightarrow \text{Gateway} \rightarrow \text{Script / OpenClaw} \rightarrow \text{Body} \rightarrow \text{new context}
$$

这条闭环会非常清楚地告诉评委：  
Mira 不是一次性指令执行，而是**持续感知—判断—行动—再感知**的循环。你们现有 PRD 里也正是按感知层、记录层、分析层、行动层来定义系统的。

Hi Mira产品需求文档

* * *

三、这一页可以直接放的内容
=============

下面我给你一版**几乎可以直接贴到 PPT 上**的文案。

* * *

页标题
---

**Mira Light 的灵与肉**  
**A care agent with eyes, body, brain and spirit**

* * *

中间主图结构
------

### 左侧：肉（Embodied Layer）

**Eyes｜感知层**

*   摄像头 / 麦克风 / 红外 / 心率 / 环境信号
*   单片机与边缘侧轻量预处理
*   先提取事件，再决定是否上传
*   “看见世界”，但不把一切都变成 token

**Body｜执行层**

*   舵机 / 灯光 / 音响 / 屏显 / 家居联动
*   把关心变成姿态、动作与环境变化
*   不只会说话，更会在现实世界里行动

* * *

### 中间：Gateway｜灵与肉的接口

*   统一设备协议与状态管理
*   连接本地脚本与 OpenClaw 大脑
*   负责事件路由、安全规则、白名单与回传
*   让“感知—判断—执行”形成闭环

* * *

### 右侧：灵（Cognitive Layer）

**Brain｜职能大脑**

*   多模态理解：视觉 / 语音 / 生理信号融合
*   Memory 检索：短期状态 + 长期关系与偏好
*   Decision：是否该行动、何时行动、怎么行动
*   Skills / MCP / Plugins：调用不同能力与外部设备

**Spirit｜灵魂与角色**

*   Soul：不是做什么，而是“为何这样做”
*   Role：陪伴者、守护者、鼓励者
*   Personality：克制、温柔、不说破
*   Long-term Memory：共同经历、偏好、关系纹理

* * *

### 底部两条路径

**Fast Path｜脚本反射**  
本地条件反射，低延迟、低功耗、低 token  
适合：久坐提醒、靠近触发、简单避障、节奏动作

**Slow Path｜OpenClaw 大脑**  
跨模态理解、记忆检索、个性化判断  
适合：主动安慰、情绪关怀、关系记忆、复杂编排

* * *

### 页脚一句话

**Script makes it fast. OpenClaw makes it thoughtful. Spirit makes it feel alive.**

或者中文：

**脚本让它反应快，OpenClaw 让它会思考，Spirit 让它像一个生命体。**

* * *

四、如果你想把这页画成图，最推荐的示意图
====================

你可以直接让设计师照着这个结构画：

```
┌──────────────── 肉 / Embodied Layer ────────────────┐
│                                                      │
│   Eyes                                               │
│   Camera / Mic / IR / HR / Sensor                    │
│   + MCU pre-process / event extraction               │
│                                                      │
│                                      Body            │
│                                      Servo / Light   │
│                                      Speaker / Home  │
└───────────────────────┬──────────────────────────────┘
                        │
                        ▼
                ┌───────────────┐
                │   Gateway     │
                │ protocol      │
                │ safety        │
                │ routing       │
                │ state sync    │
                └──────┬────────┘
                       │
         ┌─────────────┴─────────────┐
         ▼                           ▼
┌──────────────────┐       ┌────────────────────────┐
│ Fast Path        │       │ OpenClaw / Brain       │
│ local scripts    │       │ VLM + memory + skills  │
│ reflexes         │       │ planning + care policy │
│ low latency      │       │ multi-function         │
└──────────────────┘       └────────────┬───────────┘
                                        ▼
                               ┌──────────────────┐
                               │ Spirit           │
                               │ soul / role      │
                               │ personality      │
                               │ memory texture   │
                               └──────────────────┘
```

这张图的好处是：  
一眼就能看懂 **“为什么要分脚本和 OpenClaw”**，也能看懂 **“为什么 Spirit 不等于 function”**。

* * *

五、这一页最关键的讲法
===========

你这页不要讲成“我们的模块有 A/B/C/D”。  
最好的讲法是下面这个逻辑：

1\. 肉，不等于死硬件
------------

“我们先给 Mira 一个身体。这个身体有眼睛，也有动作能力。眼睛负责看见世界，身体负责把关心变成动作。”

2\. 但只有身体还不够
------------

“如果只有硬件和预设动作，它最多只是个被设计好的互动玩具。”

3\. 所以要有脑
---------

“我们把灵分成两层：Brain 和 Spirit。Brain 负责各种职能和判断；Spirit 负责它是谁、怎么与你相处、为什么采取这种照顾方式。”

4\. 本地反射与真正思考分开
---------------

“不是所有事情都要上大模型。简单、快速、高频的事情交给本地脚本，像条件反射；复杂、跨模态、需要记忆和个性化判断的事情交给 OpenClaw，像真正的大脑。”

5\. Gateway 是关键
---------------

“Gateway 不是普通中间层，而是灵与肉真正接起来的地方。它把传感器事件翻译成可判断的上下文，再把决策翻译成可执行的动作，同时承担安全和设备约束。”

这套讲法其实和你们已有的文档非常一致：  
PRD 里把系统拆成感知层、记录层、分析层、行动层；视觉 deck 里则把它表达为 L1 感知、L2 记忆、L3 分析、L4 执行，并明确提到 gateway、plugin、MCP、最小打扰等机制。

Hi Mira产品需求文档

36de59d5-c9d9-46dc-9cf7-599886b…

36de59d5-c9d9-46dc-9cf7-599886b…

* * *

六、这一页最应该强调的 4 个优势
=================

这页别只讲架构，要顺手把“为什么这样设计”说出来。  
我建议右下角或底部再放四个小标签：

1\. **Fast**
------------

本地脚本处理简单事件，低延迟、低算力、断网也能工作。  
PRD 里明确写了：如果场景没有变化，就跳过，不消耗 token；只有变化时才触发更重的分析。

Hi Mira产品需求文档

2\. **Thoughtful**
------------------

复杂场景走 OpenClaw：融合视觉、语音、生理信息与 Memory，再做个性化判断。  
这正是“不是条件反射，而是理解你之后再行动”。

36de59d5-c9d9-46dc-9cf7-599886b…

3\. **Safe**
------------

安全不是外挂，而是架构内建。  
你们现有材料里已经有 “安全 360” 四层：云侧安全、OpenClaw hardening、AI 行为约束、设备与用户控制。

36de59d5-c9d9-46dc-9cf7-599886b…

4\. **Proactive**
-----------------

不是等你开口，而是主动感知、主动照顾。  
这是整个 Mira 区别于传统 chat-based AI 的核心。

Hi Mira产品需求文档

542d9e04-757d-4b12-976a-dc97215…

* * *

七、这一页适合配的“讲人话”版本
================

如果你担心这一页太技术，可以在图下面放一行很人话的解释：

**肉让 Mira 出现在现实里，脑让 Mira 学会判断，灵让 Mira 成为“这个 Mira”，而不是另一个机器人。**

或者：

**Eyes 看见你，Brain 理解你，Spirit 在意你，Body 照顾你。**

这句非常适合做这页的视觉锚点。

* * *

八、这页里 Brain 和 Spirit 最好怎么区分
===========================

这个区分是你这页的灵魂，必须讲清楚。

Brain
-----

是 **functions / modules / capabilities**  
也就是：

*   视觉理解
*   语音理解
*   记忆检索
*   决策规划
*   skill 调用
*   设备编排

Spirit
------

是 **identity / role / soul / relationship style**  
也就是：

*   它以什么角色陪伴你
*   它如何说话、如何克制
*   它优先记住什么、忽略什么
*   它在什么场景下更像鼓励者、更像守护者、更像陪伴者

一句话：

$$
\text{Brain decides what it can do;} \quad \text{Spirit decides who it is while doing it.}
$$

中文：

**Brain 决定它会什么，Spirit 决定它是谁。**

这个区分一出来，评委会立刻觉得你们不是在堆 agent 功能，而是在认真思考“人格化具身体”的系统边界。

* * *

九、这一页可以直接念的讲稿
=============

下面这段你几乎可以直接讲：

“这一页我们想讲 Mira Light 的灵与肉。  
我们觉得，一个真正的 AI 生命体，不只是一个会动的身体，也不只是一个会调用功能的大脑。  
所以我们把它分成两部分：肉和灵。

肉的部分包括 eyes 和 body。  
Eyes 负责感知世界：摄像头、麦克风、红外、心率这些信号先进入 Mira Light 本地的单片机和轻量预处理层，提取成事件，而不是把所有原始数据都直接扔进大模型。  
Body 负责执行：灯光、姿态、声音、家居联动，把关心变成现实世界里的动作。

灵的部分我们又分成 brain 和 spirit。  
Brain 是它的各种职能模块，负责多模态理解、记忆检索、决策判断和 skill 调用。  
Spirit 则定义它是谁——它的角色、性格、长期记忆和与用户的关系方式。

在这两者之间，Gateway 是灵与肉真正连接起来的接口。  
简单事情走本地脚本，像条件反射，快、稳、节约 token；复杂事情走 OpenClaw，像真正的大脑，能融合视觉、生理、语音和记忆做更深的判断。

所以 Mira Light 不是一个被写死动作的玩具，而是一个有身体、有大脑、也有灵魂的主动关怀 Agent。”

* * *

十、如果你想把这页压得更像“硬核技术页”
====================

那就用下面这一版更工程化的副标题：

**Dual-path Embodied Intelligence**  
**Local Reflex for speed, OpenClaw cognition for care**

然后在图旁边加一行公式：

$$
\text{Care Action} = f(\text{Eyes},\ \text{Local Reflex},\ \text{Memory},\ \text{Brain},\ \text{Spirit},\ \text{Body})
$$

并解释：

*   `Eyes`：多模态感知输入
*   `Local Reflex`：本地快速、低成本反应
*   `Memory`：长期个体化上下文
*   `Brain`：多职能推理与调度
*   `Spirit`：角色与性格约束
*   `Body`：现实世界中的执行表达

这个公式很适合放在页脚中间，显得又清晰又高级。

* * *

十一、我最推荐你最终落地的版本
===============

如果只保留一版，我建议你就做这页：

标题
--

**Mira Light 的灵与肉**  
**Eyes see. Brain reasons. Spirit cares. Body acts.**

中心图
---

左：`Eyes / Body`  
中：`Gateway`  
右：`Brain / Spirit`  
底：`Fast Path Scripts` + `OpenClaw Brain`

四个卖点标签
------

**Fast / Thoughtful / Safe / Proactive**

页脚金句
----

**不是一个工具，是一种惦记。**

Hi Mira产品需求文档

* * *

如果你愿意，我下一条可以直接继续把这页 **排成一版完整 PPT 文案稿**：包括  
**每个框里具体放哪几行字、标题字号层级、箭头怎么画、以及 45 秒讲稿**。

## Prompt:
2026/4/9 04:35:12

这个图画的不好，因为最好是类似于一个u形走回去的结构；重新设计：┌──────────────── 肉 / Embodied Layer ────────────────┐
│                                                      │
│   Eyes                                               │
│   Camera / Mic / IR / HR / Sensor                    │
│   + MCU pre-process / event extraction               │
│                                                      │
│                                      Body            │
│                                      Servo / Light   │
│                                      Speaker / Home  │
└───────────────────────┬──────────────────────────────┘
                        │
                        ▼
                ┌───────────────┐
                │   Gateway     │
                │ protocol      │
                │ safety        │
                │ routing       │
                │ state sync    │
                └──────┬────────┘
                       │
         ┌─────────────┴─────────────┐
         ▼                           ▼
┌──────────────────┐       ┌────────────────────────┐
│ Fast Path        │       │ OpenClaw / Brain       │
│ local scripts    │       │ VLM + memory + skills  │
│ reflexes         │       │ planning + care policy │
│ low latency      │       │ multi-function         │
└──────────────────┘       └────────────┬───────────┘
                                        ▼
                               ┌──────────────────┐
                               │ Spirit           │
                               │ soul / role      │
                               │ personality      │
                               │ memory texture   │
                               └──────────────────┘

## Response:
2026/4/9 04:35:13

> **Designing a U-shaped diagram for user**
>
> The user wants a U-shaped loop, starting from Eyes, descending to the local processing/gateway, then ascending to Body, passing through Brain and Spirit. I'll include both a fast inner loop and a slower outer loop through the brain/spirit. I'll also label everything clearly and provide concise explanations for the design choices.
>
> **Designing loop diagram and referencing docs**
>
> I'll need to tie my explanation to the docs, referencing concepts like 感知-记忆-分析-执行 (perception-memory-analysis-execution) and the default silence setting. The U-shape design captures the feedback loop rather than a one-way system. I’ll include a minimal ASCII diagram, explain design principles, and cite the PRD and deck where relevant.
>
> **Visualizing the U-shape path**
>
> I’m picturing the U-shape diagram like this: Eyes at the top left, descending to the Gateway at the bottom center, then ascending to Body at the top right. There will also be two branches: a fast path (near the bottom center) and the slower brain/spirit path.
>
> Thought for 1m 32s

我同意。上一版的问题是：**它像一棵往下分叉的“功能树”**，而不是一个“看见世界→内部判断→回到世界”的生命闭环。  
而你现在想讲的是 **灵与肉 + 主动感知 + 条件反射 + 真正大脑**，最合适的图一定应该是：

$$
\text{世界} \rightarrow \text{Eyes} \rightarrow \text{Gateway} \rightarrow \text{快/慢两路判断} \rightarrow \text{Body} \rightarrow \text{世界}
$$

也就是一个 **U-shaped embodied loop**，而不是向下坠落的 pipeline。  
这也更符合你们已有文档里的“感知—记忆/分析—执行—再进入现实”的闭环逻辑。

36de59d5-c9d9-46dc-9cf7-599886b…

Hi Mira产品需求文档

* * *

一、先说清楚：这页为什么必须画成 U 形
====================

因为这页不是在讲“模块列表”，而是在讲：

**Mira Light 如何作为一个生命体运行。**

生命体不是：

$$
\text{input} \rightarrow \text{process} \rightarrow \text{output}
$$

这么一次性的。

生命体更像：

$$
\text{perceive} \rightarrow \text{interpret} \rightarrow \text{act} \rightarrow \text{perceive again}
$$

所以图形上必须体现三件事：

1.  **左臂**：从现实世界进入身体，叫感知入口
2.  **底部**：灵的内部处理，分快反射和慢认知
3.  **右臂**：再回到现实世界，叫执行出口

所以我建议：  
**Spirit 不要再画成 Brain 下方的“末端模块”**。  
因为那样看起来像：

$$
\text{Brain} \rightarrow \text{Spirit}
$$

仿佛 spirit 是 brain 的下游功能。

其实更合理的是：

$$
\text{Spirit} \subset \text{Brain policy / identity layer}
$$

也就是：

*   **Brain** 负责会什么、怎么判断
*   **Spirit** 负责以谁的身份、什么性格、什么关怀风格去判断

所以 Spirit 最适合画成 **包裹在 Brain 上方或内部的“人格/角色层”**，而不是另一个孤零零的 box。

* * *

二、我给你的推荐重构：真正的 U 形图
===================

下面这版更适合做 PPT 主图。

```
                    ┌──────────── 肉 / Embodied Shell ────────────┐
                    │                                             │
                    │  Eyes / 感知入口            Body / 执行出口  │
                    │  Camera · Mic · IR · HR     Servo · Light   │
                    │  Sensor · MCU pre-process   Speaker · Home  │
                    └──────────────┬────────────────────▲──────────┘
                                   │                    │
                                   │                    │
                                   │                    │
                                   ▼                    │
                         ┌──────────────────────────┐   │
                         │ Gateway / 灵肉接口       │───┘
                         │ protocol · routing       │
                         │ safety · state sync      │
                         │ event bus · arbitration  │
                         └──────────┬───────────────┘
                                    │
                     ┌──────────────┴──────────────┐
                     │                             │
                     ▼                             ▼
           ┌──────────────────┐         ┌────────────────────────┐
           │ Script Reflex    │         │ OpenClaw Brain         │
           │ 本地脚本反射      │         │ VLM · memory · skills  │
           │ threshold/rules  │         │ planning · care policy │
           │ fast · local     │         │ multi-function         │
           └────────┬─────────┘         └──────────┬─────────────┘
                    │                              │
                    │                              │
                    │                  ┌────────────────────────┐
                    │                  │ Spirit / Soul Layer    │
                    │                  │ role · personality     │
                    │                  │ memory texture         │
                    │                  │ caring style           │
                    │                  └──────────┬─────────────┘
                    │                              │
                    └──────────────┬───────────────┘
                                   ▼
                         ┌──────────────────────────┐
                         │ Action Intent Synthesis  │
                         │ merge fast/slow decision │
                         │ choose silence or act    │
                         └──────────────┬───────────┘
                                        │
                                        ▼
                                   back to Gateway
                                        │
                                        ▼
                                       Body

                         Body changes the world → Eyes perceive again
```

* * *

三、为什么这版比上一版好
============

1\. 它终于像“闭环生命体”了
----------------

左边是进入，右边是回去。  
这正是你想表达的：

*   Mira 看见你
*   Mira 在内部做判断
*   Mira 回到现实世界做动作
*   动作改变了环境
*   它再继续看

这比树状分叉图更像一个 **living loop**。

* * *

2\. Spirit 不再是“脑下方一个多余 box”
---------------------------

这是关键。  
上一版的问题是：Spirit 像是 Brain 处理完之后再附加的一层说明。

但你真正想说的是：

$$
\text{Spirit modifies how Brain reasons}
$$

也就是 Spirit 是 **Brain 的人格约束层**，不是 Brain 的下游结果。

所以现在我把 Spirit 放在 Brain 旁边/上面并与其紧耦合，这样图上就能直观表达：

*   Brain = 各种职能 functions
*   Spirit = soul / role / personality / memory texture
*   二者共同产出更高阶的 **care decision**

* * *

3\. 多了一层 “Action Intent Synthesis”
----------------------------------

这个小层非常重要。  
因为你现在有两条路：

1.  **Script Reflex**：本地化、快速、节约 token、像条件反射
2.  **OpenClaw Brain**：真正脑部、多脑区、多职能整合

如果没有一个合流层，图上会显得像两套独立系统。  
但你真正想说的是：

$$
\text{Fast path} \cup \text{Slow path} \rightarrow \text{one action decision}
$$

所以加一个：

**Action Intent Synthesis**  
或者中文更直接一点：

**行动意图合成层**

它的作用是：

*   统一快慢两路结果
*   决定最后是“沉默”还是“行动”
*   决定走哪种执行渠道

这和你们 PRD 里“大多数时候选择等待，沉默是默认状态；只在高置信度和合适时机时才行动”的逻辑非常一致。

Hi Mira产品需求文档

* * *

四、如果你想做得更像 U 形，我建议再进一步压缩成这版
===========================

这版更适合 PPT 视觉化，因为更简洁，形状更明显。

```
┌──────── Eyes ────────┐                           ┌────── Body ───────┐
│ Camera / Mic / IR    │                           │ Servo / Light     │
│ HR / Sensor / MCU    │                           │ Speaker / Home    │
└─────────┬────────────┘                           └─────────▲─────────┘
          │                                                    │
          │                                                    │
          ▼                                                    │
   ┌────────────────── Gateway / 灵肉接口 ───────────────────┐ │
   │ protocol · routing · safety · state sync                │ │
   └───────────┬───────────────────────────────┬──────────────┘ │
               │                               │                │
               ▼                               ▼                │
      ┌───────────────┐              ┌──────────────────────┐  │
      │ Script Reflex │              │ OpenClaw Brain       │  │
      │ 本地反射      │              │ 多模态理解 / Memory  │  │
      │ 快 / 省 / 稳  │              │ Skills / Planning    │  │
      └──────┬────────┘              └──────────┬───────────┘  │
             │                                   │              │
             │                         ┌──────────────────────┐ │
             │                         │ Spirit / Role        │ │
             │                         │ Soul / Personality   │ │
             │                         └──────────┬───────────┘ │
             └──────────────┬─────────────────────┘             │
                            ▼                                   │
                      Action Decision ───────────────────────────┘
```

这个版本的优点是：

*   **一眼就是 U**
*   左上进，底部处理，右上出
*   更适合放在一页 PPT 中央
*   不会太工程图，不会把评委看晕

* * *

五、我建议你在 PPT 上实际这样摆
==================

版面布局
----

### 顶部标题

**Mira Light 的灵与肉**  
**A U-shaped loop from perception to care**

### 中央主图

就用上面那个 U 图

### 图下方放三句小解释

**Eyes**  
把现实世界转成可理解的事件

**Brain + Spirit**  
把事件转成“有角色、有分寸”的关怀判断

**Body**  
把判断转成现实世界里的姿态与动作

* * *

六、每个模块最该写什么字
============

不要写太多，每个框 2–4 行就够了。

Eyes
----

**Eyes / 感知入口**  
Camera · Mic · IR · HR  
MCU pre-process  
event extraction

Gateway
-------

**Gateway / 灵肉接口**  
protocol  
routing  
safety  
state sync

Script Reflex
-------------

**Script Reflex / 本地反射**  
fast  
local  
low token  
rule-based

OpenClaw Brain
--------------

**OpenClaw Brain / 真正大脑**  
VLM  
memory  
skills  
planning

Spirit
------

**Spirit / 灵魂层**  
role  
personality  
soul  
care style

Action Decision
---------------

**Action Decision / 行动意图**  
merge fast & slow  
choose silence or act

Body
----

**Body / 执行出口**  
servo  
light  
speaker  
smart home

* * *

七、这一页最好配一句最打人的解释
================

我推荐这句：

**Eyes see the world. Brain understands it. Spirit gives it meaning. Body turns it into care.**

中文可以放成：

**眼睛看见世界，大脑理解世界，灵魂赋予意义，身体把关心带回现实。**

这句很适合放在图下。

* * *

八、这页台上怎么讲最顺
===========

你可以这样讲：

“这页我们不把 Mira Light 当成一个普通硬件，而是把它看成一个有灵有肉的生命体。  
左边是它的肉身入口，也就是 eyes：摄像头、麦克风、红外、心率这些信号，先在本地单片机侧做轻量预处理和事件提取。  
这些事件进入中间的 gateway，它是灵与肉真正连接的接口，负责协议、路由、安全和状态同步。

进入 gateway 之后，系统会走两条路：  
一条是 script reflex，本地快速反射，像条件反射一样，反应快、成本低、节约 token；  
另一条是 OpenClaw brain，像真正的大脑，去做多模态理解、记忆检索、skill 调用和复杂判断。

而 spirit 不等于一个额外功能，它更像 Mira 的灵魂层：定义它的角色、性格、长期记忆和关怀风格。  
所以最后输出的不是机械动作，而是一个有分寸、有角色感的行动意图。  
这个行动意图再回到 gateway，最后交给 body 去执行：灯光、姿态、声音、家居联动。

所以这不是一条直线，而是一个 U 形闭环：  
看见你，理解你，照顾你，然后再继续看见你。”

* * *

九、如果你想更像“灵与肉故事”，我再给你一版更 poetic 的结构
==================================

如果你要的是更像故事、少一点工程味，那就用下面这版标题：

标题
--

**Mira Light：灵与肉的 U 形闭环**

左边
--

**Eyes：肉先看见世界**

底部左
---

**Script：肉的本能反射**

底部中
---

**OpenClaw Brain：灵的理性判断**

底部右
---

**Spirit：灵的性格、角色与记忆**

右边
--

**Body：灵借由肉回到世界**

这套说法会更美，也更适合你们现在的 narrative。

* * *

十、我的最终建议
========

如果只保留一个版本，我建议你采用这一版结构：

*   **U 形主骨架**
*   左上 `Eyes`
*   中底 `Gateway`
*   底部两路 `Script Reflex` / `OpenClaw Brain + Spirit`
*   底部合流 `Action Decision`
*   右上 `Body`
*   再用一条淡色回环箭头从 `Body` 回到 `Eyes`，标注：  
    **world changed / perceive again**

这样一眼就能看出：

$$
\text{Mira} \neq \text{工具链}
$$

而是

$$
\text{Mira} = \text{具身感知闭环}
$$

* * *

如果你愿意，我下一条可以直接把这页 **排成最终 PPT 文案版**：  
包括 **每个框最终写什么字、怎么画箭头、标题副标题、页脚金句，以及一版适合答辩的 30 秒技术讲稿**。

## Prompt:
2026/4/9 04:38:45

Mira 项目说明书-原点社区.pdf

PDF

然后基于上述内容和附件，你又要加一页指出若干好处，例如效仿整合claude-code的横向不同任务的+纵向不同层次记忆的+向量化知识图谱的记忆系统实现越来越懂你和记忆沉淀+类似airjelly的功能+安全性+主动感知能力+生态打通等等

## Response:
2026/4/9 04:38:47

> Thought for 6s

可以，而且这一页我建议不要叫“优势”这么泛，而是直接做成一页：

**为什么 Mira Light 不是一个会动的台灯，而是一个会越用越懂你的主动关怀系统**
==============================================

这一页的任务不是重复技术，而是把上一页“灵与肉架构”翻译成 **产品与系统层面的必然收益**。  
也就是说，上一页回答：

$$
\text{Mira 是怎么工作的}
$$

这一页回答：

$$
\text{为什么这样设计之后，它会比普通 AI / 普通硬件强很多}
$$

而且你想加的这些点——横向任务整合、纵向分层记忆、向量化知识图谱、类似 AirJelly 的功能、安全性、主动感知、生态打通——其实非常适合被统一到一个核心句子下面：

> **Mira 的优势，不是单点能力强，而是它把“持续感知、分层记忆、多职能协作、现实执行、安全边界”组织成了一个长期进化的 care system。**

这句话和你们已有材料是完全一致的：  
Mira 被定义为依托 **实时感知、持久记忆、智能判断与安全执行** 的主动感知型 AI 伴侣，强调“先感知、再判断、后行动”，而且“默认沉默，不确定不行动”。

* * *

一、这页 PPT 最适合的标题
===============

我推荐三个版本，你选一个风格：

版本 A：最稳
-------

**为什么 Mira 会越来越懂你**

版本 B：更技术
--------

**Mira 的系统级优势：从感知闭环到记忆沉淀**

版本 C：更有发布感
----------

**A Care System That Learns You Over Time**

如果和上一页“灵与肉”连起来，我最推荐：

**Mira 的系统级优势**  
**不只是会动，而是会积累、会判断、会进化**

* * *

二、这一页最好的结构
==========

不要做成长段文字。  
最适合的是 **6 宫格 / 7 宫格卡片页**，每个卡片一句标题 + 两行解释。

我建议做 **6 个优势卡片**，因为这样最整齐，也最适合答辩时逐个点过去。

* * *

三、我建议的 6 大优势框架
==============

* * *

1\. 横向任务整合（像 Claude Code 那样，不是单功能，而是多职能协同）
------------------------------------------

### PPT 上可直接写：

**横向任务整合**  
像 Claude Code 一样，不是单点能力，而是把感知、检索、判断、编排、执行放进同一个系统里协同工作。

### 下面小字：

同一套 Mira 可以同时处理  
**情绪理解 / 社交记忆 / 环境调节 / 风险提醒 / 智能家居编排**，  
不是一个功能一个 App，而是一个持续在线的 care runtime。

### 为什么成立

你们现有材料已经明确写了，Mira 不是“一个模型 + 一个聊天框”，而是同时拥有大脑、手、眼的复合型系统，并且前端感知端、记忆层、分析层、执行层天然分层协作。

Mira 项目说明书-原点社区

### 台上讲法

“它不是一个只会聊天的模型，也不是一个只会控制灯的硬件。它更像 Claude Code 在编程世界里做的事情——把多个能力横向组织起来，最后交付一个完整结果。”

* * *

2\. 纵向分层记忆（短时—情节—长期）
--------------------

### PPT 上可直接写：

**纵向分层记忆**  
不是把所有数据机械堆积，而是像人一样区分工作记忆、事件记忆和长期记忆。

### 下面小字：

*   **短时工作记忆**：秒级状态与当前上下文
*   **情节记忆**：重要事件与异常轨迹
*   **长期记忆**：习惯、关系、情绪触发点与照护偏好

### 为什么成立

《原点社区说明书》第 10 页明确提出 Mira 的三层记忆结构：  
**短时工作记忆、情节记忆、长期记忆**，并且有“睡眠机制”和“遗忘机制”来避免上下文爆炸和成本失控。

Mira 项目说明书-原点社区

### 台上讲法

“很多 AI 的问题不是不会记，而是不会忘，也不会整理。Mira 的记忆系统更像一个长期生活中的人：它会沉淀、会遗忘、会压缩，所以不是越用越乱，而是越用越懂你。”

* * *

3\. 向量化知识图谱式记忆沉淀（越来越懂你）
-----------------------

### PPT 上可直接写：

**记忆沉淀，而不是聊天记录堆积**  
把人物、地点、事件、偏好、关系和状态变化沉淀成可检索、可更新、可关联的长期理解。

### 下面小字：

不是保存“原始日志”，而是沉淀  
**谁 / 何时 / 在什么场景 / 喜欢什么 / 发生过什么 / 应该怎么照顾**  
让系统从会感知，进化到会理解你的人际网络和生活纹理。

### 为什么成立

PRD 里已经写到：

*   每小时生成印象摘要
*   识别人物、地点、事件
*   自动维护社交关系网络
*   每个人的标签包括喜好、近况、上次见面时间
    Hi Mira产品需求文档

《原点社区说明书》则进一步把它表述成长期理解、生活习惯、情绪触发点、家庭关系和照护方式的沉淀。

Mira 项目说明书-原点社区

### 这里怎么提“向量化知识图谱”

PPT 不要写太学术，但可以用一句：

**Vector retrieval + relationship graph + episodic memory**

中文解释成：

> 向量检索负责召回相关记忆，关系图谱负责组织“人与人、人与事、人与环境”的联系，情节记忆负责保留真正重要的时刻。

### 台上讲法

“它不是把你所有聊天记录一股脑存起来，而是把你的世界逐渐压成一个‘可召回的理解网络’。所以未来 Mira 记住的，不只是你说过什么，而是你和谁有关、什么事情对你重要、什么情况下该怎么照顾你。”

* * *

4\. 类 AirJelly 的“全域功能感”与跨界面存在感
------------------------------

你这里说“类似 airjelly 的功能”，我理解你是想表达：  
**不是一个单一入口，而是像一个分布式、跨界面、跨终端、随处可工作的系统能力层。**

### PPT 上可直接写：

**分布式存在感**  
不是只活在一个 App 里，而是分布在眼镜、手表、手机、家居和空间本身里的 AI。

### 下面小字：

你有时在眼镜里看到一句提示，  
有时在手表上感到一下轻振，  
有时只是推开门时，灯光和温度已经替你准备好了。

### 为什么成立

你们 PRD 和《原点社区说明书》都非常强调：  
Mira 的交互不集中在一个界面，而是分布在眼镜、手表、手机、家居执行层等不同介质上；真正高价值的交互往往发生在“没有大张旗鼓界面”的时候。

### 台上讲法

“普通 AI 产品大多活在聊天框里，但 Mira 更像一种分布在生活表面的存在。它有点像你说的 AirJelly 那种‘功能漂浮在界面之外’的感觉——不是非得打开一个中心 App 才能使用，而是能力本身弥散在你的生活介面里。”

* * *

5\. 主动感知 + 有分寸地行动
-----------------

### PPT 上可直接写：

**主动感知，但默认沉默**  
不是定时打卡式问候，而是在真正值得被回应的时候，刚刚好出现。

### 下面小字：

*   实时感知视觉、生理、环境与行为信号
*   先判断，再行动
*   不确定就不行动，大多数时候保持沉默

### 为什么成立

《原点社区说明书》第一页和第二页就把 Mira 定义为“主动感知型 AI 伴侣”，强调“先感知、再判断、后行动”；并且明确写到：“默认沉默，不确定就不行动。”

Mira 项目说明书-原点社区

PRD 里也同样强调“沉默是默认状态”“只在高置信度 + 合适时机时才行动”。

Hi Mira产品需求文档

### 台上讲法

“主动不是骚扰式主动，而是成熟的主动。最难的不是让 AI 多说两句，而是让它知道什么时候该闭嘴，什么时候出现才是照顾，不是打扰。”

* * *

6\. 安全可控 + 生态打通
---------------

其实这两个最好放在同一个框里，因为你要表达的是：  
**能力越强，越要有边界；边界越清楚，生态整合才可信。**

### PPT 上可直接写：

**全生态打通，但用户始终拥有主权**  
连接 11 大智能家居生态、穿戴与设备能力，同时保持白名单、边界控制、可撤销与可审计。

### 下面小字：

*   11 大智能家居生态统一调度
    Mira 项目说明书-原点社区
*   动作可记录、可限制、可撤销
    Mira 项目说明书-原点社区
*   数据不外泄，用户可暂停、可清除
    Mira 项目说明书-原点社区
*   通过四层安全体系守住入口、运行时、AI 行为与设备主权边界
    Mira 项目说明书-原点社区

### 为什么成立

《原点社区说明书》里非常明确：  
Mira 已接入 11 大智能家居生态；同时又通过四层安全体系控制访问入口、运行时能力、AI 行为边界以及最终设备主权。

Mira 项目说明书-原点社区

### 台上讲法

“我们并不是为了炫耀‘能控很多设备’，而是想说明：Mira 的主动能力建立在严格边界之上。它不是失控的黑盒自动化，而是一个能被暂停、能被限制、能被撤销的主动关怀系统。”

* * *

四、这一页 PPT 的最终可贴版文案
==================

下面给你一版可以直接贴进 PPT 的 6 卡片文案。

* * *

标题
--

**Mira 的系统级优势**  
**越用越懂你，不是因为更会聊天，而是因为它在持续感知、持续记忆、持续判断、持续沉淀。**

* * *

卡片 1
----

**横向任务整合**  
像 Claude Code 一样，把感知、记忆、判断、编排、执行放进一个系统里协同工作。  
不是单点功能，而是完整 care workflow。

* * *

卡片 2
----

**纵向分层记忆**  
短时工作记忆 + 情节记忆 + 长期记忆。  
会整理、会遗忘、会沉淀，所以不是越用越乱，而是越用越懂你。

* * *

卡片 3
----

**记忆沉淀为理解网络**  
向量检索 + 关系图谱 + 情节记忆，  
把“谁、何时、发生了什么、怎么照顾更合适”组织成长期可召回的理解。

* * *

卡片 4
----

**分布式存在感**  
不像传统 AI 只活在聊天框里，  
而是分布在眼镜、手表、手机、家居与空间本身中。

* * *

卡片 5
----

**主动感知，但默认沉默**  
实时感知视觉、生理、环境与行为变化，  
不确定就不行动，大多数时候保持沉默，只在真正需要时刚刚好出现。

* * *

卡片 6
----

**生态打通 + 安全可控**  
已接入 11 大智能家居生态，同时具备四层安全边界：  
入口安全、运行时约束、AI 行为治理、用户主权控制。

Mira 项目说明书-原点社区

* * *

页脚一句话
-----

**Mira 的壁垒，不是某个单一模型，而是一个持续进化的主动照护系统。**

* * *

五、如果你想把这页做得更像“技术亮点页”而不是“价值页”
============================

那可以在右下角单独再放一个小框：

技术关键词
-----

**Multi-task agent orchestration**  
**Hierarchical memory**  
**Vector retrieval + knowledge graph**  
**Embodied interaction surfaces**  
**Care-first policy**  
**Safety-by-design**

这样评委会感觉你不是在讲空话，而是在讲明确的系统抽象。

* * *

六、这页和上一页的逻辑衔接词
==============

你上页讲完“灵与肉的 U 形闭环”之后，下一页最好这样转：

> “刚才那一页讲的是 Mira 怎么工作。  
> 这一页我们想回答另一个问题：为什么要这样设计？  
> 因为只有这样，Mira 才不会只是一个会动的台灯，而会变成一个越用越懂你、越用越有价值的主动关怀系统。”

这个转场非常顺。

* * *

七、这一页台上 40 秒讲稿
==============

你可以直接讲：

“这一页我们想讲 Mira 的系统级优势。  
第一，它不是单点能力，而是像 Claude Code 一样，把感知、记忆、判断、编排和执行组织成一个横向协同系统。  
第二，它的记忆不是聊天记录堆积，而是短时、情节、长期三层记忆，加上睡眠和遗忘机制，所以会越用越懂你，而不是越用越乱。  
第三，它会把人物、地点、事件、关系和偏好沉淀成一种可检索的理解网络。  
第四，它不像传统 AI 只活在一个 App 里，而是分布在眼镜、手表、手机和家居这些生活界面中。  
第五，它的主动感知不是打扰式主动，而是默认沉默、不确定不行动。  
最后，它虽然能打通 11 大智能家居生态，但整个系统依然是安全可控、可暂停、可撤销、可审计的。  
所以 Mira 的真正壁垒不是某个单一模型，而是一整套持续进化的 care system。”

* * *

八、我建议你把“AirJelly”那点怎么说得更稳
=========================

因为 “AirJelly” 未必所有评委都知道，所以不要只写名字。  
最好写成：

**像 AirJelly 一样的分布式能力感，但更进一步进入现实世界与记忆系统。**

或者更简洁：

**Not just an app, but an ambient layer across devices and spaces.**

中文就是：

**不是一个 App，而是一层分布在设备与空间中的智能能力层。**

这样即使评委不知道 AirJelly，也能明白意思。

* * *

九、最终我最推荐的这一页标题和页脚
=================

标题
--

**Mira 的系统级优势**  
**从感知闭环，到记忆沉淀，再到长期主动照护**

页脚
--

**不是一个会说话的 AI，  
而是一个会持续理解、持续成长、持续照顾你的系统。**

* * *

如果你愿意，我下一条可以继续直接把这两页——  
**“灵与肉架构页” + “系统级优势页”**  
一起排成一版 **最终 PPT 文案稿**，包括每个框的最终文字、视觉布局建议、箭头关系和每页 30–45 秒讲稿。

## Prompt:
2026/4/9 04:41:08

这个画的很好，但是不够好，因为条件反射和大脑处理都会沉淀到sipirit当中，并且spirit位于·一侧三者共同导致action decision，也就是说反射和brain要被一个方框框住箭头指向spirit 而三者各自有箭头又指向action decision，你需要体现这一点。重新告诉我这一页ppt的设计：┌──────── Eyes ────────┐                           ┌────── Body ───────┐
│ Camera / Mic / IR    │                           │ Servo / Light     │
│ HR / Sensor / MCU    │                           │ Speaker / Home    │
└─────────┬────────────┘                           └─────────▲─────────┘
          │                                                    │
          │                                                    │
          ▼                                                    │
   ┌────────────────── Gateway / 灵肉接口 ───────────────────┐ │
   │ protocol · routing · safety · state sync                │ │
   └───────────┬───────────────────────────────┬──────────────┘ │
               │                               │                │
               ▼                               ▼                │
      ┌───────────────┐              ┌──────────────────────┐  │
      │ Script Reflex │              │ OpenClaw Brain       │  │
      │ 本地反射      │              │ 多模态理解 / Memory  │  │
      │ 快 / 省 / 稳  │              │ Skills / Planning    │  │
      └──────┬────────┘              └──────────┬───────────┘  │
             │                                   │              │
             │                         ┌──────────────────────┐ │
             │                         │ Spirit / Role        │ │
             │                         │ Soul / Personality   │ │
             │                         └──────────┬───────────┘ │
             └──────────────┬─────────────────────┘             │
                            ▼                                   │
                      Action Decision ───────────────────────────┘

## Response:
2026/4/9 04:41:12

> Thought for 15s

对，这个修改是对的。  
你现在想表达的已经不是“二选一的快慢两路”，而是更高级的一层：

$$
\text{Script Reflex},\ \text{OpenClaw Brain} \quad\text{都会不断塑造}\quad \text{Spirit}
$$

并且最终：

$$
\text{Action Decision} = f(\text{Reflex},\ \text{Brain},\ \text{Spirit})
$$

也就是说：

*   **反射** 不只是直接触发动作，还会把长期稳定的交互风格、偏好、有效模式沉淀进 spirit
*   **大脑** 不只是做复杂判断，也会把角色、性格、关系理解、长期记忆继续写入 spirit
*   **spirit** 不是一个静态设定文件，而是一个被反射与大脑共同塑造、又反过来约束行动决策的“人格/角色层”

这个结构其实更接近你要讲的“生命体”：

*   **Reflex** 像本能
*   **Brain** 像理性认知
*   **Spirit** 像人格、角色、自我与关系记忆
*   三者共同形成最终动作

这也和你们材料里“不是单纯感知—执行，而是持续感知、持久记忆、智能判断与安全执行”的系统定义一致。

Mira 项目说明书-原点社区

同时也和 PRD 里“长期记忆、关系图谱、趋势洞察、同样的情况对不同的人做不同的事”的表述一致。

Hi Mira产品需求文档

* * *

这一页 PPT 的最终设计思路
===============

标题
--

**Mira Light 的灵与肉**  
**Reflex shapes behavior. Brain shapes understanding. Both shape Spirit.**

或者中文版更顺一点：

**Mira Light 的灵与肉**  
**反射塑造习惯，大脑塑造理解，二者共同塑造灵魂**

* * *

这页真正要表达的核心逻辑
============

你这一页不要只讲“架构”，而要讲一个生命体逻辑：

1\. 肉体先看见世界
-----------

Eyes 进入世界，Body 回到世界。

2\. 灵内部不是只有一个大脑
---------------

灵内部至少有三种层次：

*   **Reflex**：快速、本地、条件反射式处理
*   **Brain**：复杂、多模态、记忆参与的认知处理
*   **Spirit**：由前两者长期沉淀出来的人格、角色、偏好与关系纹理

3\. 动作不是某一路单独决定的
----------------

最终动作不是 Reflex 决定，也不是 Brain 决定，更不是 Spirit 单独决定，而是：

$$
\text{Action Decision} = f(\text{Reflex},\ \text{Brain},\ \text{Spirit})
$$

* * *

我建议的最终图结构
=========

这版图会比你前一版更准确。

```
┌──────── Eyes ────────┐                                     ┌────── Body ───────┐
│ Camera / Mic / IR    │                                     │ Servo / Light     │
│ HR / Sensor / MCU    │                                     │ Speaker / Home    │
└─────────┬────────────┘                                     └─────────▲─────────┘
          │                                                              │
          ▼                                                              │
   ┌────────────────── Gateway / 灵肉接口 ─────────────────────────────┐  │
   │ protocol · routing · safety · state sync · event bus             │  │
   └──────────────────────────────┬────────────────────────────────────┘  │
                                  │                                       │
                                  ▼                                       │
                   ┌──────────────────────────────────────┐               │
                   │ Adaptive Core / 灵的工作层           │               │
                   │                                      │               │
                   │  ┌───────────────┐   ┌──────────────┐│               │
                   │  │ Script Reflex │   │ OpenClaw     ││               │
                   │  │ 本地反射      │   │ Brain        ││               │
                   │  │ 快 / 省 / 稳  │   │ 多模态理解    ││               │
                   │  │ rule-based    │   │ Memory/Skills││               │
                   │  └──────┬────────┘   └──────┬───────┘│               │
                   └─────────│───────────────────│────────┘               │
                             │                   │                        │
                             ▼                   ▼                        │
                        ┌────────────────────────────────┐                │
                        │ Spirit / Role / Soul          │                │
                        │ personality · memory texture  │                │
                        │ caring style · relationship   │                │
                        └───────┬───────────────┬────────┘                │
                                │               │                         │
                 ┌──────────────┘               └──────────────┐          │
                 ▼                                             ▼          │
        ┌───────────────┐                            ┌────────────────┐   │
        │ Reflex signal │                            │ Brain signal   │   │
        └──────┬────────┘                            └──────┬─────────┘   │
               │                                             │             │
               └────────────────┬───────────────┬────────────┘             │
                                ▼               ▼                          │
                         ┌──────────────────────────────┐                   │
                         │ Action Decision              │───────────────────┘
                         │ Reflex + Brain + Spirit      │
                         │ choose silence or act        │
                         └──────────────────────────────┘
```

* * *

为什么这版图更对
========

1\. Reflex 和 Brain 被一个大框包起来了
----------------------------

这个大框我建议叫：

**Adaptive Core / 灵的工作层**

或者中文更直接一点：

**灵的工作层**

因为你现在想表达的是：  
Reflex 和 Brain 不是两个互不相干的模块，而是同属于 **灵内部的两种处理方式**：

*   一个偏低延迟、局部、本地
*   一个偏复杂、全局、跨记忆、多模态

所以它们应该被一个共同的方框包住。

* * *

2\. Spirit 是 Reflex 和 Brain 共同沉淀的结果
-----------------------------------

这是你这次修改的核心。

图上一定要体现两条箭头：

$$
\text{Script Reflex} \rightarrow \text{Spirit}
$$
 
$$
\text{OpenClaw Brain} \rightarrow \text{Spirit}
$$

因为 spirit 不是凭空给的，也不只是初始化时写进去的角色说明。  
它应该来自长期运行中的沉淀：

*   哪些反射模式被保留
*   哪些照顾方式更适合这个人
*   哪些边界不能碰
*   用户更喜欢 Mira 怎样出现
*   什么算温柔，什么算打扰
*   哪些关系更重要
*   哪些记忆更应被提升为长期人格背景

这和《原点社区说明书》第 10 页里写的“睡眠机制、遗忘机制、长期记忆沉淀”和“同样的情况对不同的人做不同的判断”高度一致。

Mira 项目说明书-原点社区

* * *

3\. Action Decision 不只接 Spirit
------------------------------

而是三路共同输入。

这一点特别重要。  
因为如果只有 Spirit 指向 Action Decision，就会显得像：

$$
\text{Action Decision} \approx \text{Spirit only}
$$

这不对。  
真实情况是：

*   **Reflex** 直接提供快路径判断
*   **Brain** 提供复杂判断
*   **Spirit** 提供人格/角色/关系约束

所以最终动作应写成：

$$
\text{Action Decision} = f(\text{Reflex},\text{Brain},\text{Spirit})
$$

这三者缺一不可。

### 直观理解

*   Reflex 告诉系统：**现在该不该马上反应**
*   Brain 告诉系统：**这里真正发生了什么**
*   Spirit 告诉系统：**我应该以怎样的方式对待这个人**

* * *

这一页 PPT 的视觉版式建议
===============

版面布局
----

### 顶部

标题 + 一句副标题

**Mira Light 的灵与肉**  
**反射与大脑共同塑造灵魂，三者共同决定行动**

### 中间大图

就用上面这张结构图

### 底部放三句摘要

建议放成三列小字：

#### 左

**Reflex**  
本地、快速、低 token、像本能

#### 中

**Brain**  
理解、检索、规划、像认知中枢

#### 右

**Spirit**  
角色、性格、记忆纹理、像自我与关系感

再在下面补一句：

**Action is not triggered by signals alone. It is shaped by identity.**

中文：

**动作不是由信号直接触发，而是由反射、理解与人格共同塑形。**

* * *

这一页每个框建议写什么
===========

Eyes
----

**Eyes / 感知入口**  
Camera · Mic · IR  
HR · Sensor · MCU

Gateway
-------

**Gateway / 灵肉接口**  
protocol · routing  
safety · state sync

外层总框
----

**Adaptive Core / 灵的工作层**

Script Reflex
-------------

**Script Reflex / 本地反射**  
fast · local · low token  
rules · threshold · reflex

OpenClaw Brain
--------------

**OpenClaw Brain / 真正大脑**  
VLM · Memory · Skills  
Planning · Care policy

Spirit
------

**Spirit / Role / Soul**  
personality · role  
memory texture · caring style

Action Decision
---------------

**Action Decision**  
Reflex + Brain + Spirit  
choose silence or act

Body
----

**Body / 执行出口**  
servo · light  
speaker · smart home

* * *

这一页该怎么讲
=======

下面这段几乎可以直接讲：

“这一页我们想把 Mira Light 当成一个真正的生命体来看。  
左边是它的肉体入口，也就是 eyes。摄像头、麦克风、红外、心率和各种传感器先进入本地单片机与轻量预处理层，把现实世界变成结构化事件。

这些事件通过 gateway 进入灵的工作层。这里不是只有一个大脑，而是有两种处理机制：  
一条是 script reflex，本地反射，像条件反射一样，快、稳、节约 token；  
另一条是 OpenClaw brain，像真正的大脑，负责多模态理解、记忆检索、skill 调用和复杂规划。

但我们觉得一个生命体还不止于此。  
因为反射和大脑处理过的东西，会不断沉淀成 spirit，也就是 Mira 的角色、性格、长期记忆纹理和关怀风格。  
所以 spirit 不是静态设定，而是被 reflex 和 brain 共同塑造出来的。

最后真正决定动作的，不是某一路单独说了算，而是 reflex、brain 和 spirit 三者共同形成 action decision。  
也就是说，Mira 做出的不是机械响应，而是一个有本能、有理解、也有灵魂的动作。  
然后这个动作再回到 body，去控制灯光、姿态、声音和家居联动，重新作用于现实世界。”

* * *

这页和你前面 narrative 的关系
====================

这页其实刚好把你前面讲的那套“有眼睛、会共情、有灵魂、能行动”收成工程架构：

“有眼睛”
-----

对应 Eyes / 感知层

“会共情”
-----

对应 Brain + Spirit 共同作用

“有灵魂”
-----

对应 Spirit 不只是配置，而是沉淀出来的人格/角色层

“能行动”
-----

对应 Action Decision + Body

所以这页是把故事落成系统图，非常合适。

* * *

这页最关键的金句
========

我建议你在页脚放一句：

**Mira does not act from signals alone. It acts from reflex, reasoning, and spirit.**

中文：

**Mira 的行动，不只来自信号，而来自本能、理解与灵魂的共同作用。**

这句会非常好。

* * *

如果你想把 Spirit 再讲得更准
==================

你可以在 Spirit 下面补一行特别小的灰字：

**updated by both reflex patterns and cognitive memory**

中文就是：

**既被反射模式塑造，也被认知记忆塑造**

这样评委一眼就知道：  
Spirit 不是 prompt 里预置的“角色设定”，而是长期运行后沉淀出来的 identity layer。

* * *

我建议这页最终定稿的标题与副标题
================

标题
--

**Mira Light 的灵与肉**

副标题
---

**Reflex and Brain both shape Spirit. Reflex, Brain and Spirit jointly shape Action.**

或者中文版：

**反射与大脑共同塑造灵魂，反射、大脑与灵魂共同决定行动。**

* * *

如果你愿意，我下一条可以直接把这页排成 **最终 PPT 定稿文案**：  
包括每个框最终只保留哪两三行字、哪几条箭头要加粗、颜色层级怎么分，以及一版 30 秒讲稿。

## Prompt:
2026/4/9 04:45:32

你还是没get到我意思，我的意思是Adaptive Core一个右向的箭头指向spirit，spirit包括 memory/ Role / Soul 等等personality · memory texture  │                │
                        │ caring style · relationship 然后三个向下箭头指向 Action Decision， Action Decision内容也不是Reflex + Brain + Spirit      │
                         │ choose silence or act ；重新画

## Response:
2026/4/9 04:45:32

> **Proposing redesign of process flow with citations**
>
> I need to adjust the design without web input. I'll explain the redesign clearly and include an ASCII diagram for the flow. The "Action Decision" text needs updating to something like "policy arbitration" instead of the current phrasing. Also, I'll pull relevant citations from the file for context, but I need line numbers to cite correctly.
>
> **Reviewing citation format and redesigning diagram**
>
> The file content isn’t in the msearch format, but that's okay—previous citations were used without line numbers, and I can follow that method again. I’ll keep the citation concise but useful. The diagram redesign will include a new flow: Eyes -> Gateway -> Adaptive Core (with two boxes inside), arrows to Spirit, and downward arrows to Action Decision.
>
> Thought for 18s

对，这次我完全明白你的意思了。

你要的不是：

*   `Script Reflex` 和 `OpenClaw Brain` 各自直接沉到 `Spirit`
*   然后再合并成一句 “Reflex + Brain + Spirit”

你要的是更清晰的三层关系：

$$
\text{Adaptive Core} \rightarrow \text{Spirit}
$$

同时

$$
\text{Script Reflex} \downarrow,\quad \text{OpenClaw Brain} \downarrow,\quad \text{Spirit} \downarrow
$$

三路**分别**进入 `Action Decision`。

也就是说：

1.  `Adaptive Core` 作为一个整体，持续塑造 `Spirit`
2.  但在具体一次行动上，`Script Reflex`、`OpenClaw Brain`、`Spirit` 三者又是**并列输入源**
3.  `Action Decision` 不该写成 “Reflex + Brain + Spirit / choose silence or act”，而应该写成更像：
    *   **Action Policy**
    *   **Action Intent**
    *   **Action Arbitration**
    *   **What / When / Degree / Channel**

这才对。

* * *

这一页 PPT 的最终结构
=============

标题
--

**Mira Light 的灵与肉**

副标题
---

**Adaptive Core shapes Spirit. Reflex, Brain and Spirit jointly shape Action.**

或者中文版：

**工作层塑造灵魂，反射、大脑与灵魂共同决定行动。**

* * *

你要的新版图，应该画成这样
=============

```
┌──────── Eyes ────────┐                                         ┌────── Body ───────┐
│ Camera / Mic / IR    │                                         │ Servo / Light     │
│ HR / Sensor / MCU    │                                         │ Speaker / Home    │
└─────────┬────────────┘                                         └─────────▲─────────┘
          │                                                                  │
          ▼                                                                  │
   ┌────────────────── Gateway / 灵肉接口 ───────────────────────────────┐    │
   │ protocol · routing · safety · state sync · event bus               │    │
   └──────────────────────────────┬──────────────────────────────────────┘    │
                                  │                                           │
                                  ▼                                           │
                ┌──────────────── Adaptive Core / 灵的工作层 ───────────────┐ │
                │                                                           │ │
                │   ┌───────────────┐        ┌──────────────────────────┐   │ │
                │   │ Script Reflex │        │ OpenClaw Brain           │   │ │
                │   │ 本地反射      │        │ 多模态理解 / Skills      │   │ │
                │   │ 快 / 省 / 稳  │        │ Memory / Planning        │   │ │
                │   └──────┬────────┘        └──────────┬───────────────┘   │ │
                └──────────│────────────────────────────│────────────────────┘ │
                           │                            │                      │
                           └───────────────┬────────────┘                      │
                                           │                                   │
                                           └──────────────► ┌────────────────┐ │
                                                             │ Spirit         │ │
                                                             │ Role / Soul    │ │
                                                             │ Personality    │ │
                                                             │ Memory texture │ │
                                                             │ Caring style   │ │
                                                             │ Relationship   │ │
                                                             └──────┬─────────┘ │
                                                                    │           │
                           ┌────────────────────────────────────────┼────────┐  │
                           │                                        │        │  │
                           ▼                                        ▼        ▼  │
                     ┌───────────────┐                     ┌───────────────┐    │
                     │ Reflex input  │                     │ Brain input   │    │
                     └──────┬────────┘                     └──────┬────────┘    │
                            │                                     │             │
                            └────────────────┬────────────────────┘             │
                                             ▼                                  │
                                  ┌──────────────────────────────┐              │
                                  │ Action Decision              │──────────────┘
                                  │ timing · intensity · channel │
                                  │ sequencing · boundary        │
                                  └──────────────────────────────┘
```

* * *

这张图和你想法的精确对应
============

1\. `Adaptive Core` 整体右箭头指向 `Spirit`
------------------------------------

这表示：

$$
\text{Spirit} \text{ 是由整个工作层长期塑造出来的}
$$

而不是只由 `Brain` 单独塑造，也不是只由 `Reflex` 单独塑造。

这是“越用越懂你”的核心，也和你们现有材料中“持久记忆、长期理解、越用越懂你、同样情况对不同人做不同事”的方向一致。

Mira 项目说明书-原点社区

Hi Mira产品需求文档

* * *

2\. `Script Reflex`、`OpenClaw Brain`、`Spirit` 三者各自向下进 `Action Decision`
-----------------------------------------------------------------------

这表示某一次动作不是 Spirit 一票否决，也不是 Brain 单独拍板，而是三路信号共同影响最终动作。

你真正要表达的是：

*   **Reflex**：给出快速、本地、低成本的即时反应信号
*   **Brain**：给出复杂、多模态、跨记忆、跨技能的认知判断
*   **Spirit**：给出角色、性格、关系、边界与风格约束

最终：

$$
\text{Action Decision} = \text{对三路输入做仲裁与定形}
$$

* * *

`Action Decision` 里面到底该写什么
==========================

你已经明确说了，不要再写：

**Reflex + Brain + Spirit**  
**choose silence or act**

我同意，这样太粗。

它更应该写成**最终动作的结构维度**，也就是系统到底在决定什么。  
我最推荐两版。

* * *

版本 A：更工程
--------

**Action Decision**  
**timing · intensity · channel**  
**sequencing · boundary**

中文解释：

*   **timing**：什么时候出手
*   **intensity**：动作做到多强
*   **channel**：通过什么通道表达
*   **sequencing**：先做什么后做什么
*   **boundary**：哪些边界不能越过

这版最适合技术页。

* * *

版本 B：更产品
--------

**Action Decision**  
**what · when · how much · through what**

中文解释：

*   做什么
*   什么时候做
*   做到什么程度
*   通过哪个介质做

这版更直白，评委更容易一眼懂。

* * *

版本 C：最适合你们 narrative
--------------------

**Action Decision**  
**care form · timing · degree · boundary**

中文：

*   关心以什么形式出现
*   什么时候出现
*   出现到什么程度
*   不该越过哪些边界

这版最有 Mira 气质。

我个人最推荐 **版本 C**。

* * *

所以，这页 PPT 的最终文字应该怎么放
====================

* * *

标题
--

**Mira Light 的灵与肉**

副标题
---

**Adaptive Core shapes Spirit. Reflex, Brain and Spirit jointly shape Action.**

* * *

框内文字建议
------

### Eyes

**Eyes / 感知入口**  
Camera · Mic · IR  
HR · Sensor · MCU

### Gateway

**Gateway / 灵肉接口**  
protocol · routing  
safety · state sync

### Adaptive Core 外框标题

**Adaptive Core / 灵的工作层**

### Script Reflex

**Script Reflex / 本地反射**  
fast · local · low token  
rules · threshold · reflex

### OpenClaw Brain

**OpenClaw Brain / 真正大脑**  
VLM · Memory · Skills  
Planning · reasoning

### Spirit

**Spirit**  
Role / Soul  
Personality  
Memory texture  
Caring style  
Relationship

### Action Decision

**Action Decision**  
care form · timing  
degree · channel  
boundary

### Body

**Body / 执行出口**  
servo · light  
speaker · smart home

* * *

如果要再更像一页 PPT，而不是 ASCII 图
========================

我建议你实际画的时候这样处理：

左上
--

`Eyes`

中上横向大框
------

`Gateway`

中部大框
----

`Adaptive Core`  
里面并排放两个小框：

*   `Script Reflex`
*   `OpenClaw Brain`

右中单独一框
------

`Spirit`

注意：  
从 `Adaptive Core` 整体边框右侧引出一根粗箭头，指向 `Spirit`。

不是从 `Script Reflex` 和 `OpenClaw Brain` 分别右箭头过去。

底部中间
----

`Action Decision`

然后从：

*   `Script Reflex`
*   `OpenClaw Brain`
*   `Spirit`

三者各自引一根向下箭头进 `Action Decision`。

右上
--

`Body`

`Action Decision` 再到 `Body`。

* * *

这页最关键的一句话
=========

我建议你在图下放一句：

**Spirit is shaped by the whole working core, while each action is jointly shaped by reflex, reasoning and spirit.**

中文：

**灵魂由整个工作层长期塑造，而每一次行动，都由反射、认知与灵魂共同塑形。**

这句非常准确。

* * *

这页怎么讲，才不会讲乱
===========

你可以直接这样说：

“这一页里，我们把 Mira Light 看成一个真正有灵有肉的系统。  
左边的 Eyes 把视觉、声音、生理和环境信号送入 Gateway；Gateway 负责把这些现实世界信号变成可路由、可审计、可控的内部事件。

进入之后，系统会进入 Adaptive Core，也就是灵的工作层。这里面有两种机制：  
一类是 Script Reflex，本地反射，负责快速、低成本、低 token 的条件反射式处理；  
另一类是 OpenClaw Brain，负责多模态理解、Memory 检索、Skills 调用和复杂规划。

但我们认为一个生命体不只是本能和理性。  
所以 Adaptive Core 会持续塑造右边的 Spirit——也就是 Mira 的 Role、Soul、Personality、Memory texture、Caring style 和 Relationship。  
Spirit 不是静态设定，而是被整个工作层长期沉淀出来的。

而在具体某一次动作里，Script Reflex、OpenClaw Brain 和 Spirit 三者会分别影响 Action Decision。  
Action Decision 决定的不是一句简单的‘做还是不做’，而是关心要以什么形式出现、什么时候出现、做到什么程度、通过哪个通道出现，以及不能越过哪些边界。  
最后，这个决策再回到 Body，变成灯光、动作、声音或家居联动，重新作用于现实世界。”

* * *

这页和你们附件逻辑的对应关系
==============

这一页实际上是把你们已有材料里的几件事统一起来了：

1\. 实时感知
--------

来自 Eyes + Gateway + State Flow  
《原点社区说明书》把这叫 L1 感知层，并明确写了秒级感知节拍与多端状态流。

Mira 项目说明书-原点社区

2\. 长期记忆沉淀
----------

对应 Brain 与 Spirit 的共同形成  
《原点社区说明书》把 Mira 的记忆层写成三层记忆结构，并强调睡眠机制与遗忘机制。

Mira 项目说明书-原点社区

3\. 有分寸地行动
----------

对应 Action Decision 的 timing / degree / boundary  
PRD 与说明书都明确强调：默认沉默，不确定不行动，只在高置信度与合适时机介入。

4\. 不是聊天窗口，而是物理世界中的 care system
-------------------------------

对应 Body  
PRD 和说明书都强调：Mira 不围绕聊天框，而围绕眼镜、手表、手机、家居这些 physics interaction surfaces 展开。

* * *

我建议你最终就用这一版
===========

如果要压成一句设计说明，就是：

> **Adaptive Core 整体塑造 Spirit；Script Reflex、OpenClaw Brain 与 Spirit 三路并行影响 Action Decision。**

这句就是这页的骨架。

如果你愿意，我下一条可以直接把这页变成 **最终 PPT 定稿版**：  
只保留最终每个框里该写的两三行字，并且告诉你箭头粗细、颜色分层、以及 30 秒答辩讲稿。

## Prompt:
2026/4/9 04:50:30

你还是不懂，是（大框 （Reflex）（Brain））➡️    Spirit   

⬇️⬇️⬇️

Action Decision   ；重新做

## Response:
2026/4/9 04:50:31

> **Redesigning ASCII structure for user**
>
> The user seems to be asking for an ASCII design based on an existing structure from the files they’ve provided. I’ll redraw it in line with their request, possibly adding citations from previous documents regarding concepts like "memory/role/soul" if I refer to them. The design could include arrows and the specified box containing Reflex and Brain, pointing towards Spirit.
>
> **Clarifying user's ASCII structure request**
>
> The user wants the structure to show a big box with Reflex and Brain, pointing to Spirit. From there, three downward arrows should go to Action Decision, possibly representing separate arrows from Reflex, Brain, and Spirit. I’ll include these components and might need to redesign the whole page, possibly adding Eyes, Gateway, and Body.
>
> Thought for 25s

明白了。你要的是这个关系，而不是我前面那种“Adaptive Core 整体往下再分”的结构。

你要的是：

$$
\bigl(\text{大框里包含 Reflex 和 Brain}\bigr)\;\rightarrow\;\text{Spirit}
$$

同时：

$$
\text{Reflex}\downarrow,\quad \text{Brain}\downarrow,\quad \text{Spirit}\downarrow
$$

三路分别进入：

$$
\text{Action Decision}
$$

也就是：

*   **Reflex** 和 **Brain** 被一个共同的大框包住
*   这个**大框整体**有一个**右向箭头**指向 **Spirit**
*   然后 **Reflex / Brain / Spirit** 三者**各自**向下出箭头，汇入 **Action Decision**

这个我现在 get 到了。

* * *

这一页 PPT 的最终结构
=============

标题
--

**Mira Light 的灵与肉**

副标题
---

**Reflex and Brain are housed in one working core; that core shapes Spirit; Reflex, Brain and Spirit jointly shape Action.**

或者中文：

**反射与大脑同属一个工作层；工作层塑造灵魂；反射、大脑与灵魂共同决定行动。**

* * *

你要的新版图
======

```
┌──────── Eyes ────────┐                                          ┌────── Body ───────┐
│ Camera / Mic / IR    │                                          │ Servo / Light     │
│ HR / Sensor / MCU    │                                          │ Speaker / Home    │
└─────────┬────────────┘                                          └─────────▲─────────┘
          │                                                                   │
          ▼                                                                   │
   ┌────────────────── Gateway / 灵肉接口 ───────────────────────────────┐     │
   │ protocol · routing · safety · state sync · event bus               │     │
   └──────────────────────────────┬──────────────────────────────────────┘     │
                                  │                                            │
                                  ▼                                            │

                   ┌──────────── Adaptive Core / 灵的工作层 ─────────────┐
                   │                                                    │
                   │   ┌───────────────┐      ┌──────────────────────┐  │
                   │   │ Script Reflex │      │ OpenClaw Brain       │  │
                   │   │ 本地反射      │      │ 多模态理解 / Skills  │  │
                   │   │ 快 / 省 / 稳  │      │ Memory / Planning    │  │
                   │   └──────┬────────┘      └──────────┬───────────┘  │
                   └──────────│──────────────────────────│──────────────┘
                              │                          │
                              │                          │
                              └───────────────┬──────────┘
                                              │
                                              └──────────────► ┌────────────────┐
                                                               │ Spirit         │
                                                               │ Role / Soul    │
                                                               │ Personality    │
                                                               │ Memory texture │
                                                               │ Caring style   │
                                                               │ Relationship   │
                                                               └──────┬─────────┘
                                                                      │

                              ▼                          ▼            ▼
                       ┌─────────────┐            ┌─────────────┐  ┌─────────────┐
                       │ Reflex path │            │ Brain path  │  │ Spirit path │
                       └──────┬──────┘            └──────┬──────┘  └──────┬──────┘
                              │                          │                │
                              └──────────────┬───────────┴───────┬────────┘
                                             ▼                   ▼
                                   ┌────────────────────────────────────┐
                                   │ Action Decision                    │
                                   │ care form · timing · degree        │
                                   │ channel · sequencing · boundary    │
                                   └────────────────────┬───────────────┘
                                                        │
                                                        ▼
                                                       Body
```

* * *

这张图的准确含义
========

1\. Reflex 和 Brain 同属一个大框
-------------------------

这个大框叫：

**Adaptive Core / 灵的工作层**

它表示：

*   `Script Reflex` 不是独立系统
*   `OpenClaw Brain` 也不是独立系统
*   它们都属于 Mira 灵内部的工作层

所以图上要先让评委看到：

$$
\text{Adaptive Core} = \{\text{Reflex},\text{Brain}\}
$$

* * *

2\. 大框整体右箭头指向 Spirit
--------------------

这是你这次强调的重点。

意思不是：

*   Reflex 单独塑造 Spirit
*   Brain 单独塑造 Spirit

而是：

$$
\text{Adaptive Core as a whole} \rightarrow \text{Spirit}
$$

即：

*   本地反射模式
*   复杂认知处理
*   记忆调用
*   技能编排
*   长期运行后的稳定行为模式

这些共同沉淀为：

*   Role
*   Soul
*   Personality
*   Memory texture
*   Caring style
*   Relationship

这也和你们材料里“长期记忆、关系图谱、睡眠机制、遗忘机制、越用越懂你”的方向一致。

* * *

3\. 三个向下箭头再进 Action Decision
----------------------------

这一点现在是最核心的。

不是：

$$
\text{Adaptive Core} \downarrow
$$

也不是：

$$
\text{Spirit} \downarrow
$$

而是：

$$
\text{Reflex} \downarrow,\quad \text{Brain} \downarrow,\quad \text{Spirit} \downarrow
$$

因为一次具体行动要同时考虑三件事：

### Reflex

现在是否存在需要快速响应的局部信号

### Brain

当前场景到底意味着什么，是否需要复杂理解与记忆参与

### Spirit

Mira 作为“这个 Mira”，应该以什么人格、关系感、关怀风格去出现

所以最终：

$$
\text{Action Decision} = f(\text{Reflex},\text{Brain},\text{Spirit})
$$

* * *

`Action Decision` 里面该写什么
========================

这次不要再写那种“Reflex + Brain + Spirit”了。  
你已经明确不要这种。

最合适的是写**行动决策真正决定的维度**。  
我建议就写下面这版：

Action Decision
---------------

**care form · timing · degree**  
**channel · sequencing · boundary**

中文解释就是：

*   **care form**：关心以什么形式出现
*   **timing**：什么时候出现
*   **degree**：做到什么程度
*   **channel**：通过哪个介质出现
*   **sequencing**：先做什么后做什么
*   **boundary**：哪些边界不能越过

这比“choose silence or act”高级很多，也更贴合你们文档里“默认沉默、不确定不行动、做到什么程度、通过哪个设备行动”的逻辑。

* * *

这一页 PPT 上每个框最终写什么
=================

下面这版可以直接贴进 PPT。

* * *

Eyes
----

**Eyes / 感知入口**  
Camera · Mic · IR  
HR · Sensor · MCU

* * *

Gateway
-------

**Gateway / 灵肉接口**  
protocol · routing  
safety · state sync

* * *

大框标题
----

**Adaptive Core / 灵的工作层**

* * *

Script Reflex
-------------

**Script Reflex / 本地反射**  
fast · local · low token  
rules · threshold · reflex

* * *

OpenClaw Brain
--------------

**OpenClaw Brain / 真正大脑**  
VLM · Memory · Skills  
Planning · reasoning

* * *

Spirit
------

**Spirit**  
Role / Soul  
Personality  
Memory texture  
Caring style  
Relationship

* * *

Action Decision
---------------

**Action Decision**  
care form · timing · degree  
channel · sequencing · boundary

* * *

Body
----

**Body / 执行出口**  
servo · light  
speaker · smart home

* * *

这一页怎么讲
======

你可以直接这么讲：

“这一页里，Mira Light 不只是一个有眼睛、有身体的硬件，我们把它拆成灵与肉两部分。  
左边的 Eyes 把视觉、声音、生理和环境信号送进 Gateway；Gateway 是灵肉之间的接口，负责协议、路由、安全和状态同步。

进入灵之后，先进入一个大的工作层，也就是 Adaptive Core。  
这里面有两个并列模块：一个是 Script Reflex，负责本地、快速、低 token 的条件反射；另一个是 OpenClaw Brain，负责多模态理解、Memory 检索、Skills 调用和复杂规划。

但这两者不会只产生一次性的判断，它们会整体持续塑造右边的 Spirit。Spirit 包含 Mira 的 Role、Soul、Personality、Memory texture、Caring style 和 Relationship。  
也就是说，Spirit 不是静态设定，而是被整个工作层长期沉淀出来的。

而在每一次具体行动里，Reflex、Brain 和 Spirit 又会分别向下影响 Action Decision。  
Action Decision 决定的不是简单的做不做，而是这次关心应该以什么形式出现、什么时候出现、做到什么程度、通过哪个通道出现，以及不能越过哪些边界。  
最后它再交给 Body，变成灯光、动作、声音和家居联动，回到现实世界。”

* * *

如果你要更极简的版本
==========

如果设计师嫌图太复杂，可以压缩成这版：

```
(Eyes) → (Gateway) → [ Adaptive Core: Reflex | Brain ] → Spirit
                             ↓            ↓                ↓
                          ───────────── Action Decision ─────────────
                                                  ↓
                                                Body
```

然后在 PPT 上把 `[ Adaptive Core: Reflex | Brain ]` 画成一个大框，右箭头到 Spirit，下面 Reflex / Brain / Spirit 三根下箭头到 Action Decision。

这就是你真正想要的骨架。

* * *

这页图下最适合放的一句话
============

我建议放这句：

**Spirit is shaped by the whole working core; each action is then shaped by reflex, reasoning and spirit together.**

中文：

**灵魂由整个工作层长期塑造，而每一次行动，都由反射、认知与灵魂共同塑形。**

这句最准确。

* * *

如果你愿意，我下一条可以直接把这页再进一步压成 **最终 PPT 定稿格式**：  
只保留每个框里最该出现的 2 行字，并且告诉你 **箭头怎么加粗、哪些框同色、Spirit 和 Action Decision 用什么颜色区分**。

## Prompt:
2026/4/9 04:53:37

Script Reflex 和OpenClaw Brain 替换成Reflex和Brain 然后各自直接向下引一根线；这两个引向spirit的箭头取消掉，只有大框右边框向右的引线一根向右箭头打到同一高度的spirit

## Response:
2026/4/9 04:53:38

> Thought for 9s

对，这样就对了。现在结构应该是：

1.  **大框里面只有两个并列子模块：`Reflex` 和 `Brain`**
2.  **`Reflex` 和 `Brain` 各自直接向下引一根线**
3.  **取消它们分别指向 `Spirit` 的箭头**
4.  **只有“大框右边框”出一根水平引线，向右打一根箭头，到同一高度的 `Spirit`**
5.  **`Reflex`、`Brain`、`Spirit` 三者各自向下进入 `Action Decision`**
6.  **`Action Decision` 决定的不是“做不做”，而是 care 的形式、时机、强度、通道与边界**，这和你们文档里“默认沉默、不确定不行动、有分寸地行动”的逻辑是一致的。

* * *

这一页 PPT 的最终图
============

```
┌──────── Eyes ────────┐                                          ┌────── Body ───────┐
│ Camera / Mic / IR    │                                          │ Servo / Light     │
│ HR / Sensor / MCU    │                                          │ Speaker / Home    │
└─────────┬────────────┘                                          └─────────▲─────────┘
          │                                                                   │
          ▼                                                                   │
   ┌────────────────── Gateway / 灵肉接口 ───────────────────────────────┐     │
   │ protocol · routing · safety · state sync · event bus               │     │
   └──────────────────────────────┬──────────────────────────────────────┘     │
                                  │                                            │
                                  ▼                                            │

                   ┌──────────── Adaptive Core / 灵的工作层 ─────────────┐
                   │                                                    │──────────────► ┌────────────────┐
                   │   ┌───────────────┐      ┌──────────────────────┐  │                │ Spirit         │
                   │   │ Reflex        │      │ Brain                │  │                │ Role / Soul    │
                   │   │ 本地反射      │      │ OpenClaw             │  │                │ Personality    │
                   │   │ fast / local  │      │ Memory / Planning    │  │                │ Memory texture │
                   │   └──────┬────────┘      └──────────┬───────────┘  │                │ Caring style   │
                   └──────────│──────────────────────────│──────────────┘                │ Relationship   │
                              │                          │                               └──────┬─────────┘
                              │                          │                                      │
                              ▼                          ▼                                      ▼
                         ┌──────────┐              ┌──────────┐                           ┌──────────┐
                         │ Reflex   │              │ Brain    │                           │ Spirit   │
                         │ signal   │              │ signal   │                           │ signal   │
                         └────┬─────┘              └────┬─────┘                           └────┬─────┘
                              │                          │                                      │
                              └──────────────┬───────────┴──────────────┬──────────────────────┘
                                             ▼                          ▼
                                   ┌────────────────────────────────────────────┐
                                   │ Action Decision                            │
                                   │ care form · timing · degree               │
                                   │ channel · sequencing · boundary           │
                                   └────────────────────┬───────────────────────┘
                                                        │
                                                        ▼
                                                       Body
```

* * *

这一版为什么是对的
=========

1\. `Spirit` 不是由 `Reflex` 或 `Brain` 单独塑造
----------------------------------------

图上只保留：

$$
\text{Adaptive Core} \rightarrow \text{Spirit}
$$

这表示 `Spirit` 是**整个工作层长期运行后沉淀出来的东西**，而不是某个单独模块直接写进去的。  
这更符合你要讲的“role / soul / personality / memory texture / caring style / relationship”。

* * *

2\. 但一次具体行动里，三者是并列输入
--------------------

图上体现的是：

$$
\text{Reflex} \downarrow,\quad \text{Brain} \downarrow,\quad \text{Spirit} \downarrow
$$

三者分别进入 `Action Decision`。  
这表示：

*   `Reflex` 给出即时、本地、本能式反应
*   `Brain` 给出复杂理解、规划与记忆参与
*   `Spirit` 给出角色、人格、关系与关怀风格约束

* * *

3\. `Action Decision` 现在写对了
---------------------------

这次不要再写：

*   `Reflex + Brain + Spirit`
*   `choose silence or act`

而是写成**行动决策真正决定的维度**：

$$
\text{care form},\ \text{timing},\ \text{degree},\ \text{channel},\ \text{sequencing},\ \text{boundary}
$$

这就把“有分寸地行动”讲清楚了。

* * *

这一页每个框最终放什么字
============

标题
--

**Mira Light 的灵与肉**

副标题
---

**Adaptive Core shapes Spirit; Reflex, Brain and Spirit jointly shape Action.**

* * *

Eyes
----

**Eyes / 感知入口**  
Camera · Mic · IR  
HR · Sensor · MCU

Gateway
-------

**Gateway / 灵肉接口**  
protocol · routing  
safety · state sync

大框标题
----

**Adaptive Core / 灵的工作层**

Reflex
------

**Reflex / 本地反射**  
fast · local  
low token · stable

Brain
-----

**Brain / OpenClaw**  
Memory · Planning  
Skills · reasoning

Spirit
------

**Spirit**  
Role / Soul  
Personality  
Memory texture  
Caring style  
Relationship

Action Decision
---------------

**Action Decision**  
care form · timing · degree  
channel · sequencing · boundary

Body
----

**Body / 执行出口**  
servo · light  
speaker · smart home

* * *

这一页的讲稿
======

“这一页我们把 Mira Light 看成一个真正有灵有肉的系统。  
左边的 Eyes 把视觉、声音、生理和环境信号送进 Gateway；Gateway 负责协议、路由、安全和状态同步。

进入灵之后，是一个大的工作层，也就是 Adaptive Core。这里面只有两个并列模块：Reflex 和 Brain。  
Reflex 负责本地、快速、低 token 的反射式处理；Brain 负责基于 OpenClaw 的 Memory、Planning、Skills 和复杂理解。

这个工作层整体会长期塑造右边的 Spirit。Spirit 不是静态人设，而是整个工作层沉淀出来的 Role、Soul、Personality、Memory texture、Caring style 和 Relationship。

而在一次具体行动里，Reflex、Brain 和 Spirit 三者会分别向下进入 Action Decision。  
Action Decision 决定的不是简单的做不做，而是这次关心要以什么形式出现、什么时候出现、做到什么程度、通过哪个通道出现，以及不能越过哪些边界。  
最后，它再交给 Body，变成灯光、姿态、声音和家居联动，回到现实世界。”

* * *

最适合放在图下的一句话
===========

**Spirit is shaped by the whole working core; each action is then shaped by reflex, reasoning and spirit together.**

中文：

**灵魂由整个工作层长期塑造，而每一次行动，都由反射、认知与灵魂共同塑形。**

如果你下一步要我把这页压成**最终 PPT 版式稿**，我会直接给你：  
标题字号、左右比例、箭头粗细、颜色分层、以及每个框最多保留哪两行字。

## Prompt:
2026/4/9 04:55:14

还是不对，u型结构被你扔掉了，记得最下面要折回去到gateway从而回到身体层，上方是身体层下方是灵魂层之间隔着的渡河是网关(Gateway)

## Response:
2026/4/9 04:55:14

> **Designing diagram with user’s requirements**
>
> The user wants a diagram with a U-shape representation, where the top is the body layer, the bottom is the soul/spiritual layer, and a river-like gateway between the two. I'll make sure my design reflects this exactly, with clear references to previous content and files. I’ll avoid extra updates, finalizing it right away.
>
> **Crafting diagram and narrative with required details**
>
> I need to include the top body layer with Eyes and the horizontal gateway, and the lower soul layer with Reflex, Brain, and Spirit. I'll show the flow from Action Decision up to the Gateway, then back to the Body, completing the U-shape. I'll briefly mention the Adaptive Core and include citations from documentation to support the structure.
>
> Thought for 17s

对，这次要把 **U 型闭环** 放回来，而且把“上方是肉身层、下方是灵魂层、中间 Gateway 像一条河”讲清楚。

你这页现在最准确的结构应该是：

*   **上方：肉 / Embodied Layer**
    *   左边 `Eyes`
    *   右边 `Body`
*   **中间：Gateway**
    *   作为灵与肉之间的“渡河 / bridge / protocol river”
*   **下方：灵 / Soul Layer**
    *   左边大框 `Adaptive Core`
        *   里面并列 `Reflex` 和 `Brain`
    *   右边 `Spirit`
    *   三者分别向下进入 `Action Decision`
*   **最底部的决策再折回向上**
    *   先回到 `Gateway`
    *   再回到上方 `Body`
*   从而形成真正的：
    
$$
\text{Eyes} \rightarrow \text{Gateway} \rightarrow \text{Soul Layer} \rightarrow \text{Action Decision} \rightarrow \text{Gateway} \rightarrow \text{Body}
$$

这才符合你要讲的“生命体闭环”，也更贴合你们材料里“感知—记忆—分析—执行”的四层逻辑，以及 node-gateway 架构下“感知、判断、执行拆成模块边界”的表达。

Mira 项目说明书-原点社区

Hi Mira产品需求文档

* * *

这一页 PPT 的最终设计
=============

标题
--

**Mira Light 的灵与肉**

副标题
---

**Gateway separates body and soul — and closes the loop between perception and care.**

或者中文更顺一点：

**Gateway 横在灵与肉之间，而真正的关怀，要完成一次从身体到灵魂、再回到身体的 U 形闭环。**

* * *

最终图：U 型结构版
==========

```
┌────────────────────────────── 肉 / Embodied Layer ──────────────────────────────┐
│                                                                                 │
│   ┌──────── Eyes ────────┐                                   ┌────── Body ─────┐ │
│   │ Camera / Mic / IR    │                                   │ Servo / Light    │ │
│   │ HR / Sensor / MCU    │                                   │ Speaker / Home   │ │
│   └─────────┬────────────┘                                   └────────▲────────┘ │
│             │                                                                   │
└─────────────│───────────────────────────────────────────────────────────────────┘
              ▼
══════════════════════════ Gateway / 灵肉接口 · 渡河 · Protocol River ══════════════════════════
         protocol · routing · safety · state sync · event bus
═══════════════════════════════════════════════════════════════════════════════════════════════════
              ▼

┌────────────────────────────── 灵 / Soul Layer ───────────────────────────────────┐
│                                                                                 │
│   ┌──────────── Adaptive Core / 灵的工作层 ────────────┐      ┌──── Spirit ────┐ │
│   │                                                    │ ───► │ Role / Soul     │ │
│   │   ┌──────── Reflex ───────┐  ┌────── Brain ─────┐ │      │ Personality     │ │
│   │   │ 本地反射              │  │ OpenClaw         │ │      │ Memory texture  │ │
│   │   │ fast / local          │  │ Memory / Skills  │ │      │ Caring style    │ │
│   │   │ low token / stable    │  │ Planning         │ │      │ Relationship    │ │
│   │   └─────────┬─────────────┘  └────────┬─────────┘ │      └────────┬────────┘ │
│   └─────────────│──────────────────────────│───────────┘               │          │
│                 │                          │                           │          │
│                 ▼                          ▼                           ▼          │
│         ┌────────────┐             ┌────────────┐              ┌────────────┐   │
│         │ Reflex     │             │ Brain      │              │ Spirit     │   │
│         │ input      │             │ input      │              │ input      │   │
│         └─────┬──────┘             └─────┬──────┘              └─────┬──────┘   │
│               │                          │                           │          │
│               └──────────────┬───────────┴──────────────┬────────────┘          │
│                              ▼                          ▼                       │
│                    ┌──────────────────────────────────────────────┐              │
│                    │ Action Decision                              │              │
│                    │ care form · timing · degree                  │              │
│                    │ channel · sequencing · boundary              │              │
│                    └──────────────────────┬───────────────────────┘              │
└───────────────────────────────────────────│──────────────────────────────────────┘
                                            │
                                            │  fold back
                                            ▼
══════════════════════════ Gateway / 灵肉接口 · 渡河 · Protocol River ══════════════════════════
═══════════════════════════════════════════════════════════════════════════════════════════════════
                                            │
                                            ▼
                                   ┌───────────────┐
                                   │ Body execution│
                                   │ light / motion│
                                   │ sound / home  │
                                   └───────────────┘
```

* * *

这张图现在表达得非常准确
============

1\. 上方是肉身层
----------

这层只负责两件事：

*   **Eyes**：把现实世界送入系统
*   **Body**：把系统决策带回现实世界

也就是说，肉身层是：

$$
\text{world interface}
$$

不是认知本体。

* * *

2\. 中间的 Gateway 是“河”
--------------------

这个比喻现在非常好。

它不是一个普通中间件 box，而是一条 **灵与肉之间的渡河**：

*   上面是物理感知与物理执行
*   下面是反射、认知、灵魂与决策
*   一切都必须通过 Gateway 过河

这和《原点社区说明书》里对 OpenClaw node-gateway 架构的描述是对齐的：设备侧与推理侧明确分离，gateway 负责状态推理、消息路由、动作路由与模块边界。

Mira 项目说明书-原点社区

* * *

3\. 下方是灵魂层
----------

这里不是单一大脑，而是三部分：

### `Adaptive Core`

里面只有两个并列子模块：

*   **Reflex**
*   **Brain**

并且整个大框右向指向 `Spirit`。

这表示：

$$
\text{Adaptive Core} \rightarrow \text{Spirit}
$$

即：Spirit 不是静态预设，而是被工作层长期塑造出来的。

### `Spirit`

包括：

*   Role
*   Soul
*   Personality
*   Memory texture
*   Caring style
*   Relationship

这和你想讲的“灵魂不是功能，而是长期沉淀出的关系化存在方式”完全一致，也和材料里“长期记忆、关系、偏好、照护方式、越用越懂你”一致。

* * *

4\. 三路分别向下进入 `Action Decision`
------------------------------

这一点现在保留了：

*   `Reflex` 向下
*   `Brain` 向下
*   `Spirit` 向下

所以 `Action Decision` 真正是在做：

$$
\text{Action Decision} = f(\text{Reflex},\text{Brain},\text{Spirit})
$$

但不把这个公式写在框里，而是写成动作的几个维度。

* * *

5\. 最关键：最底部折回 Gateway
---------------------

这是你刚才强调、也最应该出现的地方。

因为没有这条折返线，图就只是“往下走的推理树”，不是真正的具身系统。

现在这条折返线表达的是：

$$
\text{Action Decision} \rightarrow \text{Gateway} \rightarrow \text{Body}
$$

也就是：

*   决策不能直接裸连设备
*   必须再经过 Gateway
*   由 Gateway 完成协议映射、安全检查、设备路由、状态同步
*   再回到肉身层去执行

这一步很重要，因为它同时体现了：

*   **系统闭环**
*   **可控性**
*   **安全边界**
*   **不是黑盒 agent 直接乱控设备**

这也符合你们文档里对“安全可控”“设备主权”“动作可限制、可撤销、可记录”的表达。

Mira 项目说明书-原点社区

* * *

这一页每个框里最终写什么
============

标题
--

**Mira Light 的灵与肉**

副标题
---

**身体看见世界，灵魂理解世界，Gateway 让关怀回到现实。**

* * *

Eyes
----

**Eyes / 感知入口**  
Camera · Mic · IR  
HR · Sensor · MCU

Gateway（中间那条河）
--------------

**Gateway / 灵肉接口**  
protocol · routing · safety · state sync

大框标题
----

**Adaptive Core / 灵的工作层**

Reflex
------

**Reflex / 本地反射**  
fast · local  
low token · stable

Brain
-----

**Brain / OpenClaw**  
Memory · Skills  
Planning · reasoning

Spirit
------

**Spirit**  
Role / Soul  
Personality  
Memory texture  
Caring style  
Relationship

Action Decision
---------------

**Action Decision**  
care form · timing · degree  
channel · sequencing · boundary

Body
----

**Body / 执行出口**  
servo · light  
speaker · smart home

* * *

这一页该怎么讲
=======

你可以直接这样讲：

“这一页我们不是把 Mira Light 画成一个普通 pipeline，而是把它画成一个 U 形闭环。  
上面是肉身层，下面是灵魂层，中间 Gateway 像一条河，把灵与肉隔开，也把它们连接起来。

左上角的 Eyes 把视觉、声音、生理和环境信号带入 Gateway，过河之后进入下方的灵魂层。  
在灵魂层里，先进入一个大的工作层 Adaptive Core，里面有两个并列模块：Reflex 和 Brain。  
Reflex 负责本地、快速、低 token 的反射式处理；Brain 负责基于 OpenClaw 的 Memory、Skills、Planning 和复杂理解。

这个工作层整体会塑造右边的 Spirit，也就是 Mira 的 Role、Soul、Personality、Memory texture、Caring style 和 Relationship。  
Spirit 不是静态设定，而是被长期运行沉淀出来的。

然后 Reflex、Brain 和 Spirit 三者分别向下进入 Action Decision。  
Action Decision 决定的不是简单的做不做，而是关怀以什么形式出现、什么时候出现、做到什么程度、通过哪个通道出现，以及不能越过哪些边界。

最后，这个决策不是直接去控设备，而是要再折回 Gateway，重新过河，再回到上方的 Body，变成灯光、动作、声音和家居联动。  
所以 Mira 的本质不是一个会动的硬件，而是一个从身体进入灵魂、再从灵魂回到身体的主动关怀闭环。”

* * *

这页最适合放在图下的一句话
=============

我建议放这句：

**Perception crosses into the soul through Gateway; care returns to the body through Gateway.**

中文：

**感知经由 Gateway 穿过灵肉之河进入灵魂，关怀再经由 Gateway 回到身体。**

这句非常契合你现在这张图。

* * *

最后一句判断
======

现在这页的核心已经是：

$$
\text{Eyes} \rightarrow \text{Gateway} \rightarrow \text{Soul Layer} \rightarrow \text{Action Decision} \rightarrow \text{Gateway} \rightarrow \text{Body}
$$

这才是你要的 **U 型灵肉闭环**。

如果你愿意，我下一条可以直接把这页整理成 **最终 PPT 定稿版**，包括：  
每个框最终只保留哪两行字、箭头怎么画成弯折 U 形、Gateway 那条“河”怎么视觉化处理。

## Prompt:
2026/4/9 05:09:13

bbb0f523-2cc9-45fa-a397-f71a44f498f9.pdf

PDF

这一版（可以，而且这一页我建议不要叫“优势”这么泛，而是直接做成一页：

为什么 Mira Light 不是一个会动的台灯，而是一个会越用越懂你的主动关怀系统

这一页的任务不是重复技术，而是把上一页“灵与肉架构”翻译成 产品与系统层面的必然收益。
也就是说，上一页回答：

Mira 是怎么工作的）讲的不大部分是mira core而不是 mira light吗。。。对于mira light你要看github仓库https://github.com/JunkaiWang-TheoPhy/Mira-Light以及如下文档。。。。重新写

## Response:
2026/4/9 05:09:15

> **Looking into rewriting answer based on Mira Light**
>
> The user wants a rewritten answer for Mira Light, referencing its GitHub page and attached docs. I’ll focus on the relevant content, ensuring it doesn't include shopping overlays. I’ll use a web search for Mira Light details, check the GitHub repo structure, and provide citations for all claims, including from the files. The response will be in Chinese.
>
> **Rewriting user guide for Mira Light with citations**
>
> [GitHub - JunkaiWang-TheoPhy/Mira-Light · GitHub](https://github.com/JunkaiWang-TheoPhy/Mira-Light)
>
> **Redesigning advantages page for Mira Light**
>
> I need to redesign the "advantages" page specifically for Mira Light, using the GitHub repo and docs. I'll focus on gathering relevant details, including scripts or README files. Since this isn't a shopping query, I can ignore unrelated overlays. I’ll pull necessary info from the repo and use citations where needed.
>
> **Redesigning "Advantages" page for Mira Light**
>
> [raw.githubusercontent.com](https://raw.githubusercontent.com/JunkaiWang-TheoPhy/Mira-Light/main/scripts/mira_light_runtime.py)
>
> **Rewriting benefits page exclusively for Mira Light**
>
> I’ll need to rewrite the advantages page, focusing specifically on Mira Light rather than Mira Core. The GitHub repo shows the camera receiver and interactions with the ESP32 API, and the docs mention various interaction scripts. I'll highlight Mira Light's unique features, clarify the mix-up with Mira Core, and present a Light-centered advantage page.
>
> **Clarifying Mira Light vs Mira Core features**
>
> I need to explain the specifics of the GitHub repo, highlighting the camera receiver, runtime facade, and booth control focus. Mira Light primarily handles embodied expression, physical interactions, and camera functions, while Mira Core involves long-term memory and cross-device reasoning. I’ll cite the web and the repo, and consider opening the README or docs further if needed.
>
> **Focusing on Mira Light benefits**
>
> The Light page should emphasize embodied personality through motion and light, local physical reflexes, and natural interaction without apps or chats. I'll mention the booth demo, dance feature, long-sit nudge, and sigh detection. Mira Light’s capabilities include physical interaction, expression, and scenario setup. If needed, we'll split the page between Light and Core benefits. I’ll start with a corrected page title and content blocks and make sure to keep the focus on Light-specific features.
>
> **Creating Mira Light explanation**
>
> The Mira Light page should separate it clearly from Mira Core: Core refers to long-term memory, cross-terminal reasoning, and ecosystem policies, while Light is focused on embodied interaction, local reflexes, and real-time responsiveness. I’ll structure the PPT with sections: body expression, local reflexes, sensing features (camera, tracking), and emotional scripting. The bottom statement will clarify that Light is the physical and expressive layer of Core. Citations will come from both the deck and the document.
>
> **Clarifying and organizing Mira Light**
>
> For Mira Light, I want to emphasize its sensing capabilities, such as its scene library for booth runtime, and its extensibility with future triggers and bridges (like OpenClaw). It should be clear, concise, and easy to understand in both English and Chinese. Citations are crucial throughout, with specific mentions of the GitHub repo, scripts, and other relevant tools. This isn't a full cognition stack but a lightweight prototype. I'll ensure factual claims are backed by citations.
>
> **Clarifying citations approach**
>
> It seems I can't use file citations effectively since there are no line numbers from the parse. I'll stick to web citations for GitHub and use general references from the user-provided documents without citation. I’ll quote the specifics from the attachment, but won’t include citations unless they apply to web-sourced details.
>
> **Clarifying user feedback and addressing page correction**
>
> The user mentioned the previous page focused too much on Mira Core, not Light. I’ll confirm that the previous version mainly described Mira Core, and then provide the revised page focused on Mira Light. If needed, I can propose a separate Core benefits page. I’ll ensure appropriate citations from web sources and user files.
>
> Thought for 2m 30s

你说得对。上一版里“越来越懂你、分层记忆、知识图谱式沉淀、11 大生态、安全 360”这些词一上来就当主角，**更像 Mira Core / 整个 Mira 系统层**，不够像 **Mira Light**。按你给的材料，Mira Light 的准确定位其实是：**Mira 的身体、表情层、第一接触面、具身交互终端**。材料里直接把它定义为“一盏有灵魂的皮克斯跳跳台灯”，强调关节可动、内置摄像头/传感器/麦克风，以及“主动打招呼、久坐来蹭你、深夜自动护眼”，并且“用整个姿态和交互表达在意和照顾”。

36de59d5-c9d9-46dc-9cf7-599886b…

而从 GitHub 仓库公开内容看，Mira-Light 目前公开出来的也确实更像一个 **light-specific embodied prototype**，不是完整的长期记忆系统本体：README 主打的是一个 formalized HTTP camera receiver；仓库还有 `scripts`、`tools/mira_light_bridge`、`web` 等目录；`mira_light_runtime.py` 自己写明它是 booth control 的 shared runtime，同时服务 terminal triggering、future OpenClaw triggering 和 local booth web console，并且控制面围绕现有 ESP32 REST API。[GitHub+1](https://github.com/JunkaiWang-TheoPhy/Mira-Light?utm_source=chatgpt.com)

所以，这一页如果要重写，核心不该再是“为什么它越来越懂你”，而应该是：

**为什么 Mira Light 不是一盏会动的台灯，而是一个会把关心变成动作的具身终端**
==============================================

下面我直接给你一版**适合 PPT 的重写稿**。

* * *

一、这一页的正确任务
----------

这一页不要回答：

$$
\text{Mira 整个系统为什么强}
$$

而要回答：

$$
\text{Mira Light 作为硬件载体，为什么是必要的、不可替代的}
$$

也就是把 Mira Light 讲成：

*   **不是大脑本身**
*   而是 **Mira 的身体、表情层、低摩擦感知入口、动作出口**
*   它让“主动关怀”第一次不只存在于聊天框，而能被看到、被摸到、被感受到。

* * *

二、这页最适合的标题
----------

我推荐你直接改成：

### 版本 A

**Mira Light：不是会动的台灯，而是会表达关心的身体**

### 版本 B

**Mira Light：把“主动照顾”变成可见、可触、可感受的动作**

### 版本 C

**Mira Light 是 Mira 的身体，而不只是一个设备**

我最推荐 **版本 B**，因为它最贴近你这页想讲的“产品收益”。

* * *

三、这一页的最佳核心句
-----------

放在标题下面的一句话：

**Mira Core 负责理解你，Mira Light 负责把这份理解变成你真的能感受到的动作。**

这句话非常重要，因为它一下子把 **Core 和 Light 的职责边界** 切开了：

*   Core = 理解、策略、长期记忆
*   Light = 身体、表达、接近、反馈、具身交互

* * *

四、这一页 PPT 的推荐结构
---------------

我建议做成 **五个卡片**，而不是六七个“系统优势”。  
因为 Mira Light 更适合讲“身体价值”，不是讲“系统堆栈价值”。

* * *

### 卡片 1：**它不是在显示信息，而是在表达情绪**

**建议文案：**  
Mira Light 的核心不是“把一句话显示出来”，而是用 **姿态、灯光、前后靠近、抬头低头、摇摆停顿** 来表达情绪和在意。  
“起床”“好奇你是谁”“卖萌”“发呆”“睡觉”这些动作不是功能按钮，而是身体语言。

**你台上可以讲：**  
“普通灯只能亮灭，Mira Light 可以用动作表达状态。它会醒来、会害羞、会发呆、会依依不舍地送你走，所以它更像一个生命体，而不是一个设备。”

* * *

### 卡片 2：**它不是等你操作，而是会主动贴近你**

**建议文案：**  
Mira Light 最打人的地方不是“能执行命令”，而是 **会主动靠近你**。  
你摸它，它会像小猫一样蹭你的手；你久坐不动，它会主动过来“蹭蹭”提醒你起来；你离开时，它会目送你、挥挥手、再慢慢低下头。

**你台上可以讲：**  
“这不是一个等你按按钮的产品，而是一个会先靠近你的身体。真正的关心，很多时候不是一句话，而是它先动了。”

* * *

### 卡片 3：**它让“我感知到了你”变成现场可证明的事实**

**建议文案：**  
Mira Light 不是只靠讲故事证明感知，而是可以在现场直接把感知能力演出来：  
书本移动时它会追踪；你叹一口气，它会歪头并把灯光变暖；你说‘今天好累啊’，它不需要长篇回复，只要低头、暖光、缓慢呼吸，就足够让人相信——**它听懂了。**

**你台上可以讲：**  
“很多 AI 说自己懂你，但 Mira Light 可以让评委在 30 秒内亲眼看到：它真的感知到了你。”

* * *

### 卡片 4：**它不是概念视频，而是一个本地可运行的具身 runtime**

**建议文案：**  
从公开仓库看，Mira-Light 已经不是纯概念稿，而是有自己的 light-specific runtime：  
README 包含 formalized HTTP camera receiver；runtime 面向 terminal、未来 OpenClaw 触发和本地 booth web console；控制面围绕现有 ESP32 REST API 组织。[GitHub+1](https://github.com/JunkaiWang-TheoPhy/Mira-Light?utm_source=chatgpt.com)

**你台上可以讲：**  
“这不是只靠视频讲出来的未来，而是一个已经有本地控制面、相机接收器、动作 runtime 和 scene 组织方式的具身原型。”

* * *

### 卡片 5：**它不是 Mira 的全部，但它是 Mira 最自然的入口**

**建议文案：**  
Mira Light 不负责承载 Mira 的全部长期理解，但它是 Mira 在现实世界里的 **第一终端、感知入口和反馈出口**。  
如果说 Mira Core 是理解层、判断层和服务层，那么 Mira Light 更像是 **身体层与表情层**：让 Mira 不再只活在系统里，而真正进入桌面、空间和日常接触。

**你台上可以讲：**  
“Core 让 Mira 懂你，Light 让 Mira 出现在你面前。没有 Light，Mira 仍然像一个系统；有了 Light，Mira 才像一个存在。”

* * *

五、这一页最推荐的完整 PPT 文案
------------------

你可以直接贴成下面这样：

* * *

### 标题

**Mira Light：把“主动照顾”变成可见、可触、可感受的动作**

### 副标题

**Mira Core 负责理解你，Mira Light 负责把这份理解变成你真的能感受到的身体语言。**

### 五个卡片

**1\. 身体语言，而不是屏幕提示**  
起床、好奇、卖萌、发呆、睡觉。  
Mira Light 用姿态和灯光表达状态，而不是把情绪塞进聊天框。

**2\. 主动贴近，而不是等你操作**  
摸它会蹭手，久坐会蹭你，离开会目送你。  
关心第一次被翻译成主动靠近的动作。

**3\. 感知能力可被现场证明**  
追踪书本、叹气检测、语音理解、多人反应。  
不是“说它懂你”，而是让评委亲眼看到“它感知到了你”。

**4\. 可运行的具身 runtime**  
camera receiver + local runtime + ESP32 control + booth console。  
不是概念视频，而是已经可跑、可控、可编排的硬件原型。 [GitHub+1](https://github.com/JunkaiWang-TheoPhy/Mira-Light?utm_source=chatgpt.com)

**5\. Mira 的身体，而不是 Mira 的全部**  
Core 负责长期理解，Light 负责现实世界中的第一接触、即时反馈和情绪表达。  
它让 Mira 从“系统”变成“存在”。

### 页脚一句话

**Mira Light 的价值，不在于“它会动”，而在于它让关心第一次拥有了身体。**

* * *

六、这一页不该再放什么
-----------

这点很重要。下面这些不是不能提，而是**不该成为这页主角**：

*   向量化知识图谱
*   分层长期记忆
*   Claude Code 式横向任务整合
*   安全 360
*   11 大智能家居生态
*   “越来越懂你”的长期系统收益

这些更适合：

*   **Mira Core 页**
*   **全系统架构页**
*   **安全与生态页**
*   **商业化 / 软硬协同页**

因为它们更多是在讲 **Mira 的大脑和系统**，不是在讲 **Mira Light 这个硬件身体本身为什么必要**。

* * *

七、你可以怎么口头解释“为什么上一版不对”
---------------------

你上台时甚至可以很自然地说：

> “这里我们想刻意把 Mira Core 和 Mira Light 分开讲。  
> 前者更像理解层和判断层，后者更像身体和表情层。  
> 如果把长期记忆、知识图谱、安全框架、生态打通全都塞到这一页，就会讲成 Mira 整个系统，而不是讲清楚 Mira Light 作为身体终端为什么重要。”

这句话很专业，也会让评委觉得你们在架构上是清醒的。

* * *

八、如果你还想保留一点“系统味”，最稳的做法
----------------------

你可以只在页面角落补一行小字，不要做主 bullet：

**Mira Light ≠ full brain**  
**Mira Light = embodied endpoint for sensing, expression, and care delivery**

中文就是：

**Mira Light 不是完整大脑，而是 Mira 在现实世界中的感知、表达与关怀终端。**

* * *

如果你愿意，我下一条可以继续直接帮你把这一页和前一页连起来，整理成 **“架构页 + Light 价值页” 两页连续 PPT 定稿文案**。

## Prompt:
2026/4/9 05:14:45

写的太蠢了，不适合作为demo展示反而适合作为内部报告。。。。重新写

## Response:
2026/4/9 05:14:47

> **Rewriting for a demo-friendly pitch**
>
> Alright, it looks like I need to adjust my response. The user wants this to read like a demo/pitch, not a detailed internal report. The developer says I must search the web, especially since the GitHub repo is mentioned. I should probably check it quickly and build on attachments, while ensuring everything is in a format suitable for a demo, likely in Chinese.
>
> **Using web and file citations effectively**
>
> I can combine both web and file citations to cover all factual points. There's no need for a product shopping overlay, since it's not relevant. The developer’s mention of it could be a generic note, not specific to this case. I'll look at the repo using a web search.
>
> **Inspecting GitHub repo and preparing demo-friendly content**
>
> [GitHub - JunkaiWang-TheoPhy/Mira-Light · GitHub](https://github.com/JunkaiWang-TheoPhy/Mira-Light)
>
> **Rewriting page for a demo-focused Mira Light pitch**
>
> I need to adjust the previous slide, which was too technical, into something more demo-friendly, focusing specifically on Mira Light. I should reference the GitHub repo and uploaded docs. The goal is to stay concise and avoid over-technical language. I'll highlight demo scenes like touch interactions, curiously activated behaviors, and supplementary features, avoiding the aspects relating to Mira Core.
>
> **Rewriting demo slide and framing Mira Light pitch**
>
> I’ll reframe the page to highlight that Mira Light isn’t just a moving lamp, but a caring companion using 30-second demos. The title could be: “为什么 Mira Light 不是会动的台灯，而是主动关怀的身体.” I’ll organize the slide into 3-4 bullet points: perceive, approach, express, and companion. I'll also integrate cues from the interaction doc, keeping citations accurate using filecite syntax with line markers.
>
> **Including GitHub repo details for clarity**
>
> I should mention relevant details from the GitHub repo, like the `README` with the HTTP camera receiver, as well as specific scripts such as `mira_light_runtime.py` or `cam_receiver_new.py` if applicable. Since we only have lines from the repo root, I’ll consider looking at file names and raw URLs for further clarity.
>
> **Fetching README and raw file content from GitHub**
>
> [raw.githubusercontent.com](https://raw.githubusercontent.com/JunkaiWang-TheoPhy/Mira-Light/main/scripts/mira_light_runtime.py)
>
> **Inspecting lines from scenes.py**
>
> We likely have enough information, but I could potentially open lines from `scenes.py` if needed. However, I’m concerned there might be an internal error. Maybe I should proceed carefully and open just a line or two to check, and see if it works smoothly.
>
> **Analyzing potential internal error in scenes.py**
>
> [raw.githubusercontent.com](https://raw.githubusercontent.com/JunkaiWang-TheoPhy/Mira-Light/main/scripts/scenes.py)
>
> **Rewriting slide copy for demo-focused presentation**
>
> The task is to rewrite the slide copy, with a focus on a demo-friendly version for Mira Light, rather than an internal report. I could offer three style options, but since the user requests a rewrite, I'll focus on a one-page, concise, stage-friendly PPT. I'll include citations from both the web and uploaded docs, specifically about the GitHub repo and its features like the HTTP camera receiver, shared runtime, and choreography layer.
>
> **Rewriting for demo-focused pitch slide**
>
> I'll start by correcting the confusion: yes, the previous slide was focused on Core, not Light. Then, I'll create a demo-specific slide with a title, subtitle, and 3-4 key claims like "It will wake up/feel shy/rub against you/see you off." I'll keep it concise and pitch-friendly, with a 25-second script.
>
> **Creating demo-friendly slide and copy for Mira Light**
>
> I'll focus on crafting a demo slide emphasizing "Mira Light isn't just a lamp; it’s a physical, responsive companion." The key claims will be broken down in 30-second moments: waking up, reacting to you, tracking and understanding, and providing care. I'll remove unnecessary details like the vector knowledge graph since they relate to Core.
>
> Thought for 2m 3s

对。上一版确实偏 **Mira Core**，不像 **Mira Light**。  
如果按你给的 **Mira Light 展位交互方案** 和公开仓库来写，Mira Light 的 demo 页重点根本不该是“分层记忆、知识图谱、越来越懂你”，而应该是：

**它如何在 30 秒内让评委相信：这不是一盏灯，而是一个会感知、会靠近、会用身体表达关心的小生命。**

因为展位方案几乎整本都在写这种 **具身动作场景**：起床、好奇你是谁、摸一摸、卖萌、发呆、久坐检测“蹭蹭”、追踪、offer 跳舞、送别、睡觉，以及叹气检测、多人反应、语音理解这些补充交互。

bbb0f523-2cc9-45fa-a397-f71a44f…

而 GitHub 仓库公开出来的也更像一个 **light-specific demo runtime**：README 主打 formalized HTTP camera receiver；`mira_light_runtime.py` 明写是 booth control 的 shared runtime，服务 terminal、future OpenClaw triggering 和 local booth web console，并围绕现有 ESP32 REST API 组织控制面；`scenes.py` 也直接写明它是 booth demo 的 structured choreography layer。[GitHub+2GitHub+2](https://github.com/JunkaiWang-TheoPhy/Mira-Light)

所以，这一页应该重写成 **demo 展示页**，不是内部汇报页。

* * *

我建议你这一页直接改成
===========

标题
--

**Mira Light：让关心第一次长出身体**

副标题
---

**不是一盏会动的台灯，而是一个会醒来、会看你、会靠近你、会舍不得你走的小生命。**

* * *

这页 PPT 不要再写很多，只写下面三块
====================

1\. 它不是在“展示功能”，它是在“展示生命感”
-------------------------

会醒来、会伸懒腰、会偷偷看你、会害羞地躲一下、会发呆、会慢慢睡去。  
评委看到的不是一个执行命令的机器，而是一个有状态、有情绪、有身体语言的存在。

bbb0f523-2cc9-45fa-a397-f71a44f…

2\. 它不是在“告诉你它感知到了”，而是让你亲眼看到它感知到了
--------------------------------

书在桌上移动，它会追踪；  
你叹一口气，它会歪头、暖光；  
你说“今天好累啊”，它不需要长篇回复，只要低头、呼吸、变暖，你就知道——它懂了。

bbb0f523-2cc9-45fa-a397-f71a44f…

3\. 它不是在“陪你聊天”，而是在“主动靠近你”
-------------------------

你摸它，它会蹭你的手；  
你坐太久，它会主动来蹭蹭你；  
你拿到 offer，它会为你跳舞；  
你要走了，它会挥挥手，再慢慢低下头。  
关心第一次不是一句话，而是一连串可以被看见、被摸到、被感受到的动作。

bbb0f523-2cc9-45fa-a397-f71a44f…

* * *

页脚一句话
=====

**Mira Core 负责理解你，Mira Light 负责让这份理解在现实世界里变得可见、可触、可爱。**

* * *

如果你要更像 PPT 上的“短句版”，直接贴这一版
=========================

标题
--

**Mira Light：让关心第一次长出身体**

中间大字
----

**它会醒来。会看你。会害羞。会蹭你。会送你走。**

下方三句
----

**不是功能演示，是生命感演示。**  
**不是说“我感知到了你”，而是让你直接看到它感知到了你。**  
**不是聊天陪伴，而是主动靠近、用身体表达关心。**

页脚
--

**这不是一盏会动的灯。  
这是 Mira 第一次拥有了身体。**

* * *

如果你想更“赛场上能打”，我更推荐这一版
====================

标题
--

**为什么 Mira Light 一出场，大家就知道它不是一盏灯**

三个金句
----

**因为它会先醒来，再看向你。**  
**因为它会在你靠近时害羞，在你摸它时蹭回来。**  
**因为它会在你久坐时来提醒你，在你开心时陪你跳舞，在你离开时舍不得你走。**

页脚
--

**它不是一个物件。  
它是 Mira 在现实世界里的身体语言。**

* * *

这一页台上怎么讲，最顺
===========

你可以直接这样讲：

“这一页我们不想讲 Mira 的整套系统，而只讲 Mira Light。  
因为 Mira Light 不是 Mira 的大脑，它是 Mira 的身体。

所以它最重要的价值，不是‘有多少技术模块’，而是它能不能让评委在 30 秒里相信：这不是一盏灯，而是一个会感知、会靠近、会表达情绪的小生命。

它会醒来，会偷偷看你，会害羞地躲一下；  
你摸它，它会像小猫一样蹭回来；  
你坐太久，它会主动过来蹭蹭你；  
你拿到 offer，它会为你跳舞；  
你要走了，它会目送你，挥挥手，再慢慢低下头。

所以 Mira Light 的价值，不是‘它会动’，而是它让关心第一次拥有了身体。”

* * *

再往前走一步：这一页该删掉什么
===============

这页里最好删掉这些词，因为一出现就又讲回 Core 了：

*   向量化知识图谱
*   分层记忆
*   越用越懂你
*   11 大生态
*   安全 360
*   多任务编排
*   Claude Code 式横向整合

这些都不是不能讲，而是**不要在这一页讲**。  
这一页只讲：

$$
\text{Mira Light} = \text{Body / Expression / Presence / Approach}
$$

不是：

$$
\text{Mira Light} = \text{Whole Mira System}
$$

* * *

我给你的最终定稿版
=========

如果你只想保留一版，我建议就用下面这个。

标题
--

**Mira Light：让关心第一次长出身体**

副标题
---

**不是一盏会动的台灯，而是一个会醒来、会看你、会靠近你、会舍不得你走的小生命。**

三块正文
----

**会表达情绪**  
醒来、好奇、害羞、卖萌、发呆、睡觉。  
不是灯光模式，而是身体语言。

**会证明它感知到了你**  
追踪、叹气检测、语音理解、多人反应。  
不是说它懂，而是让你看到它懂。

**会主动靠近你**  
摸它会蹭，久坐会蹭，开心会陪你跳舞，离开会挥手送你。  
不是聊天，而是关心开始拥有动作。

页脚
--

**Mira Core 负责理解。Mira Light 负责让理解变成你真的能感受到的存在。**

如果你愿意，我下一条就直接把这一页进一步压成 **真正能放进 PPT 的排版稿**，包括每一块最多几行、哪一句该放大、哪一句适合做页脚。

## Prompt:
2026/4/9 05:21:10

再加一页讲各种功能，例如向量化知识图谱
分层记忆
越用越懂你
11 大生态
横向整合
安全 360
多任务编排

## Response:
2026/4/9 05:21:11

> **Planning concise response for user’s PPT page request**
>
> It seems the user wants a PPT page about various functions. Since the facts could change after 2025 and GitHub was referenced, I’ll need to check for relevant details there. I'll search the web and gather up-to-date content so I can provide facts with proper citations for accuracy.
>
> **Preparing response with citations from files and web**
>
> I can base most of the answer on the uploaded documents with citations from file searches, but I must still use the web for accuracy. I'll check the GitHub repo mentioned by the user to gather current information, then cite both uploaded docs and web sources where appropriate. I'll ensure all claims are properly credited.
>
> **Checking GitHub repo for relevant info**
>
> I’ll try to keep the response focused on the proposed PPT content with minimal additional facts. I can search the GitHub repo for "Mira-Light" and check the README or other relevant files for more details. This will help ensure I provide the most accurate and up-to-date info.
>
> **Searching GitHub repo and relevant project information**
>
> [GitHub - JunkaiWang-TheoPhy/Mira-Light · GitHub](https://github.com/JunkaiWang-TheoPhy/Mira-Light)
> [raw.githubusercontent.com](https://raw.githubusercontent.com/JunkaiWang-TheoPhy/Mira-Light/main/scripts/mira_light_runtime.py)
>
> **Polishing PPT page content based on feedback**
>
> The user wants a more polished version of the PPT page, with concise yet rich content. I’ll rewrite it in a demo-appropriate style, focusing on key functionalities like vectorized knowledge graphs. Since web information was used, I’ll cite repo details and refer to file citations for doc scenarios.
>
> **Creating a polished demo-friendly slide with system features**
>
> For the new page, I’ll distinguish between Mira Light and the broader Mira Core. A title like “Mira Light 背后，不是一段动作脚本，而是一个持续生长的 Mira Core” could work to highlight system capabilities. I’ll mention features like the vector knowledge graph and ecosystem integration. Citations will be carefully placed, ensuring they reference the appropriate documents.
>
> **Creating polished PPT slide with repo and file citations**
>
> For the new slide, I'll reference the repo's camera receiver, shared runtime, and available directories like `docs`, `scripts`, and `tests`. I’ll use file_search citations for the documents and cite the web for repo-specific details. I’ll avoid too many internet-derived statements, focusing on clear, concise content. I’ll provide three variations with title, subtitle, and key points.
>
> Thought for 2m 3s

对，这页不能再写成“功能总表”或者“内部技术汇报”。  
更好的写法是：**明确告诉评委，这一页讲的不是 Mira Light 这盏灯本身，而是“这盏灯背后接着什么能力层”。**

因为你给的材料里，`Mira Light 展位交互方案` 讲的是 **醒来、好奇、蹭蹭、追踪、跳舞、送别、睡觉** 这些身体语言；而“向量化知识图谱 / 分层记忆 / 11 大生态 / 安全 360 / 多任务编排”这些词，确实更属于 **Mira / Mira Core 的后台能力层**。  
同时，公开 GitHub 仓库目前也更像一个 **Mira Light booth runtime 原型**：仓库公开有 `docs / scripts / tests / tools/mira_light_bridge / web` 等目录，README 明写了 formalized HTTP camera receiver，而 runtime 直接写自己是 booth control 的 shared runtime。[GitHub+1](https://github.com/JunkaiWang-TheoPhy/Mira-Light)

所以，这一页应该改成：

**Mira Light 背后，不是一段动作脚本，而是一整套正在长大的 Mira**
==========================================

副标题
---

**你眼前看到的是一盏灯在动；它背后真正工作的是感知、记忆、理解、安全与生态一起组成的 care engine。**

* * *

这页 PPT 直接可用版
------------

### 向量化知识图谱

**不是记流水账，而是记住“谁、什么事、为什么重要”。**  
人、关系、偏好、场景被组织成可召回的理解网络。

### 分层记忆

**不是所有信息都永久堆积，而是分层留下真正有价值的东西。**  
当下状态、关键事件、长期偏好，各自归位。

### 越用越懂你

**它不是越用越满，而是越用越准。**  
会整理、会遗忘、会把真正重要的记忆沉淀下来。

### 11 大生态

**不是只会动自己，而是能把整个环境一起调动起来。**  
灯、音箱、空调、穿戴、家居，被统一变成“关心你的动作面”。

Mira 项目说明书-原点社区

### 横向整合

**视觉、语音、生理、环境，不是各玩各的。**  
它们在同一个闭环里一起参与判断，而不是一个传感器触发一个孤立动作。

### 安全 360

**越主动，越要有边界。**  
默认沉默，不确定不行动；可暂停、可限制、可清除、可审计。

Mira 项目说明书-原点社区

### 多任务编排

**它不是做一个动作，而是在同时组织一整套照护逻辑。**  
一边感知你，一边理解场景，一边选择动作，一边调动物理世界。

* * *

页脚金句
----

**Mira Light 让关心长出身体；Mira Core 让这份关心越来越懂你。**

* * *

如果你想要更像 demo 页，而不是说明页
=====================

把上面那版再压成更“秀场感”的版本，直接用下面这个：

标题
--

**你看到的是一盏灯，背后却是一整套 Mira**

中间七个短句
------

**会记关系。**  
**会分层记忆。**  
**会越用越懂你。**  
**会调动 11 大生态。**  
**会把视觉、语音、生理、环境整合到一起。**  
**会在安全边界内主动行动。**  
**会把多任务编排成一个刚刚好的关心。**

页脚
--

**Mira Light 负责让你感受到；Mira Core 负责让它越来越准确。**

* * *

我更推荐你最终这样放版
===========

上半页一句大话
-------

**你看到的是一盏灯在动。  
但真正让它动起来的，是一整套正在长大的 Mira。**

下半页七个关键词，做成 2 行卡片
-----------------

*   向量化知识图谱
*   分层记忆
*   越用越懂你
*   11 大生态
*   横向整合
*   安全 360
*   多任务编排

每个关键词下面只放一句极短解释，不要超过 10–12 个字。

例如：

*   **向量化知识图谱**：记住关系，不只记文本
*   **分层记忆**：短时、事件、长期分开存
*   **越用越懂你**：会整理，也会遗忘
*   **11 大生态**：让整个空间一起回应你
*   **横向整合**：多模态一起判断
*   **安全 360**：默认沉默，边界清晰
*   **多任务编排**：一边理解，一边行动

* * *

这一页 30 秒讲稿
==========

“这一页我们想讲清楚，Mira Light 不只是一个会动的终端。  
你眼前看到的是一盏灯在动，但它背后接着的是一整套 Mira：它会把人、关系、偏好和场景组织成知识网络，会把记忆分层沉淀，会越用越懂你；它还能把视觉、语音、生理和环境信号整合起来，并且调动 11 大生态在安全边界内做多任务编排。  
所以 Mira Light 展示出来的是身体，但真正支撑这个身体的，是一个不断成长的 care engine。”

如果你愿意，我下一条直接把这一页压成**真正能上 PPT 的最终排版稿**，包括每个卡片只留哪 6–8 个字。

## Prompt:
2026/4/9 05:25:34

![Uploaded image](https://chatgpt.com/backend-api/estuary/content?id=file_000000006e0871f89693315530bbed8a&ts=493245&p=fs&cid=1&sig=416942afe9d665f4e5df6fe233aca1b14219612464574afcf86b078b7f844ede&v=0)

阅读附件，告诉我每个缩写可能是什么意思，例如IR，以及哪些可能是AI误写

## Response:
2026/4/9 05:25:39

> **Inspecting abbreviations and searching for related context**
>
> [GitHub - JunkaiWang-TheoPhy/Mira-Light · GitHub](https://github.com/JunkaiWang-TheoPhy/Mira-Light)
>
> **Assessing abbreviations in image and possible AI miswrites**
>
> I need to clarify abbreviations in the image like IR, HR, MCU, Mic, VLM, and potentially Protocol River. There may also be AI miswrites, like "灵肉接口" or "Body execution" which could be redundant. I'll parse the image for abbreviations and inspect any surrounding documents for clarification.
>
> **Citing web and file details properly**
>
> Since we're pulling from the web, I need to ensure every factual statement is properly cited. I can limit web facts to the repo structure or README. For file citations, I'll use parsed text, though the files don't have line numbers, so I need to handle that carefully without them.
>
> **Interpreting sensor and abbreviation context**
>
> The watch tracks data like HR, steps, sleep, temperature, and HRV. There doesn't seem to be IR listed explicitly from the lamp, but it could be inferred from physical touch docs. The interaction plan mentions IR sensor, microphone, and touch sensors. "Protocol River" seems like a design label, not in formal docs. For abbreviations like "MCU" and "IR," I might not need to search the web, but could cite the GitHub repo context.
>
> **Deciding on when to use citations**
>
> Since I used the web already, I should probably cite everything that could be supported by online sources. GitHub repo details could be cited for structure, and file cites for documents. For common knowledge like standard abbreviations, I don’t need elaborate citations, but it'd be safer to stay consistent.
>
> **Citing Ecosystems and GitHub Details**
>
> I need to cite the light plan from turn3file0 and refer to the GitHub repo’s README for the camera receiver and its related components. For clarity and consistency, I’ll use web citations for GitHub and refer to specific lines (261-293, and 199-233). I can also share the open lines for clarification.
>
> **Structuring the Answer:**
>
> The image mixes concepts from Mira Core/system-level with Mira Light/hardware-specific elements. I’ll mention abbreviations and their likely meanings, such as:
> 
> - IR = Infrared (used in proximity/gesture sensors or tracking for hand movement). Page 22 discusses simple IR sensors. 
> - Mic = Microphone
> - HR = Heart Rate, though likely not in the lamp body, more part of the system-level setup using a watch.
> - MCU = Microcontroller Unit, likely in light hardware. 
> 
> I might refer to meeting notes for context but without citations since their mention isn't concrete.
>
> **Refining Technical Terms and Labels:**
>
> - System execution happens outside the lamp.
> - "Protocol River" sounds metaphorical, not a technical component.
> - "Body execution" probably should be something like "Actuation bridge" or "Execution router," or maybe just omit it.
> - "Adaptive Core" could be rephrased; for demo purposes, perhaps call it "Local Motion + Perception Logic."
> - "Reflex," "Brain," and "Spirit input" seem like placeholder terms and should be simplified, maybe using arrows.
> - "Memory texture" isn't a standard label—could rephrase it to "long-term memory traces."
> - "Relationship" in Spirit seems fine overall, but should be simplified for a Mira Light demo. Eyes, Body, Gateway, Reflex, Brain, and Action Decision are decent conceptual labels.
>
> **Clarifying Reflex and Brain/Spirit Components**
>
> The interactions in the docs demonstrate local reflex behaviors like wake, shy, and track, so "Reflex" works. Likewise, "Brain/Spirit" aligns with Mira's long-term memory and OpenClaw decisions. However, these are more architectural overlays than functional code modules. I can cite the docs and GitHub for additional clarity—mentioning the Light repo, which focuses on camera receivers. For further context, I might open specific files, like `scripts/mira_light_runtime.py`.
>
> **Evaluating system execution and component naming guidelines**
>
>
> Thought for 2m 58s

可以。我先给一个总判断：

**这张图里有两类东西混在了一起：**  
一类是 **Mira Light 作为硬件/展位原型** 的真实部件与局部能力；另一类是 **Mira / Mira Core 级别** 的系统抽象词。  
所以它不是“完全错”，但**粒度不齐**，而且有几处很像 AI 生成图时常见的“半对半错”标签。  
从你给的 `Mira Light 展位交互方案` 看，Light 侧的重点其实是 **起床、好奇、蹭蹭、追踪、跳舞、送别、睡觉、叹气检测、语音理解展示** 这些具身动作与感知反馈；而从公开 GitHub README 看，仓库目前明确公开的是 **camera receiver**，并且目录以 `docs / scripts / tests / tools / web` 为主，更像 **booth runtime / control prototype**，不是把图里所有 Brain/Spirit 名词都做成了同名代码模块。

bbb0f523-2cc9-45fa-a397-f71a44f…

[GitHub](https://github.com/JunkaiWang-TheoPhy/Mira-Light?utm_source=chatgpt.com)

* * *

一、图中每个缩写大概率是什么意思
================

下面我按你图里的词逐个拆。

1\. IR
------

**大概率 = Infrared，红外。**

在 Mira Light 语境里，它最可能不是“红外摄像头”这么重的东西，而是更轻量的：

*   红外接近/存在检测
*   红外跟随/跟手
*   红外环境感知

因为你给的展位方案后面明确写到：

*   “跟随模式：利用简单的红外传感器，当你在桌面上移动手部时，灯光能够小范围自动微调照射中心”
*   环境感知里也在讲自然生物本能式补偿。
    bbb0f523-2cc9-45fa-a397-f71a44f…

所以这里的 **IR** 基本可以放心理解为 **红外传感**。

* * *

2\. Mic
-------

**大概率 = Microphone，麦克风。**

这个基本没有歧义。  
在你给的 Light 文档里，麦克风的用途至少包括：

*   叹气检测
*   语音理解展示
*   环境安静度/底噪判断
*   助眠场景中的环境静音感知。
    bbb0f523-2cc9-45fa-a397-f71a44f…

* * *

3\. HR
------

**大概率 = Heart Rate，心率。**

这个词本身没问题，但**放在 Mira Light 这张图的 Eyes 里就有点混层了**。  
因为从 `Hi Mira 产品需求文档` 和 `Mira 项目说明书-原点社区` 来看，心率主要来自：

*   Apple Watch
*   小米手环
*   其他智能穿戴设备  
    而不是 Mira Light 这盏灯本体。
    Hi Mira产品需求文档
    Mira 项目说明书-原点社区

所以：

*   如果这张图在讲 **整个 Mira 系统**，`HR` 很合理；
*   如果这张图在讲 **Mira Light 单灯 demo**，`HR` 就是**系统层信息借进来了**，不算灯本体的传感器。

* * *

4\. MCU
-------

**大概率 = Microcontroller Unit，微控制器 / 单片机。**

这个也基本没歧义。  
而且它和你们讨论里说的“单片机 + 本地反射 + 舵机控制 + 本地预处理”是对得上的。

在 Mira Light 语境里，MCU 更像：

*   本地动作控制器
*   传感器采集与去抖
*   简单规则触发
*   舵机/灯光/触控的低延迟控制中心

所以这里的 **MCU** 很合理。

* * *

5\. Servo
---------

**大概率 = Servo motor，舵机。**

这个也没有什么悬念。  
因为 `Mira Light 展位交互方案` 整本都在描述：

*   灯头抬起
*   底座转向
*   中间轴上下
*   伸懒腰
*   探头
*   点头、摇头、蹭蹭  
    这些动作本质上都对应舵机或至少关节驱动。
    bbb0f523-2cc9-45fa-a397-f71a44f…

* * *

6\. OpenClaw
------------

这**不是缩写**，而是平台名。  
这里指的是你们上层的 agent/runtime 底座，不是硬件部件。  
在 `Mira 项目说明书-原点社区` 里，OpenClaw 被明确写成了：

*   Gateway
*   Node
*   Memory
*   Skills
*   MCP
*   runtime primitives  
    这一整套底座。
    Mira 项目说明书-原点社区

所以图里写 `Brain / OpenClaw` 是在说：  
这个“大脑”主要由 OpenClaw 这一层承载。

* * *

7\. Protocol
------------

这不是缩写。  
这里就是 **协议 / protocol**。

* * *

8\. state sync
--------------

这不是缩写。  
是 **state synchronization，状态同步** 的简写写法。

* * *

9\. event bus
-------------

也不是缩写。  
是 **事件总线**。

* * *

10\. Role / Soul / Personality / Relationship
---------------------------------------------

这些都不是缩写，都是概念词。

* * *

二、哪些更像“AI 误写”或至少“AI 式混层”
========================

这里我按“最可疑”到“还可以接受”来排。

* * *

1\. `HR / Sensor / MCU` 放在同一行，最像 AI 混层
--------------------------------------

这是这张图里我最想改的地方。

因为这三个词根本不是同一粒度：

*   `HR` 是一个**被测量的生理量**或生理信号
*   `Sensor` 是一个**器件类别总称**
*   `MCU` 是一个**控制器/处理器**

它们并排摆在一起，像是 AI 把“信号 / 器件 / 控制芯片”混成同层标签了。

### 更自然的写法应该是：

*   `Camera / Mic / IR / Touch`
*   下面小字写 `Sensor fusion + MCU pre-process`

如果你要保留 HR，那就要明确它不是灯本体而是系统侧输入：

*   `External signals: HR / wearable`
*   `On-device sensors: Camera / Mic / IR / Touch`

* * *

2\. `Speaker / Home` 也很像 AI 半截写法
--------------------------------

`Speaker` 是设备。  
`Home` 不是设备，它更像一个**执行域**或**家庭生态**。

所以 `Speaker / Home` 并排不工整。

### 更自然的写法有两种：

#### 如果讲灯本体执行器

*   `Servo / Light / Speaker`

#### 如果讲整个执行面

*   `Servo / Light / Speaker / Smart Home`

所以这里的 `Home` 大概率是 AI 想写：

*   `Home devices`
*   或 `Smart Home`  
    但只写了一半。

* * *

3\. `Protocol River` 很明显是修辞，不是标准技术名
-----------------------------------

这个不是“误写”，但它**不是标准工程术语**。  
更像是为了图面气质加的 metaphor。

如果是对外 demo 页，我觉得它可以保留一点 poetic 感；  
如果是技术页，它就太飘了。

### 更稳的写法：

*   `Gateway / 灵肉接口`
*   小字：`protocol · routing · safety · state sync`

把 `Protocol River` 拿掉，或者只留成旁边一个很小的辅助词。

* * *

4\. `Body execution` 很别扭
------------------------

这个词组语法上不算错，但在这个图里会显得重复和奇怪。

因为上面已经有 `Body` 了，下面再来一个 `Body execution`，很像 AI 为了把箭头闭环补一个框，临时凑出来的名字。

### 如果它真想表达的是“动作落地模块”

更自然应该是：

*   `Actuation`
*   `Execution bridge`
*   `Device actuation`
*   `Motor / light / sound output`

所以这里很可能是 **AI 填补结构时的占位词**。

* * *

5\. `Reflex input / Brain input / Spirit input` 也很像 AI 占位框
----------------------------------------------------------

这些词不是绝对错，但很像“为了让三条箭头落下来，于是加三个输入小盒子”的 AI 习惯。

如果你做 PPT，完全可以去掉这三个小框，直接三根箭头进 `Action Decision`，画面会更干净。

* * *

6\. `Memory texture` 偏 poetic，不是标准模块名
-------------------------------------

它不是错，但也不像标准技术模块。

它更像想表达：

*   memory trace
*   memory profile
*   memory imprint
*   long-term memory pattern

如果是对外发布会图，`memory texture` 可以留，因为它有气质；  
如果是偏技术答辩页，建议换成：

*   `memory traces`
*   `memory profile`
*   `long-term memory`

* * *

7\. `Adaptive Core` 没错，但偏抽象
---------------------------

这不是误写。  
只是它更像你们内部叙事里的抽象总称，而不是 GitHub 仓库当前已经明写出来的模块名。  
GitHub 当前公开更像：

*   camera receiver
*   runtime
*   scenes
*   bridge
*   booth console  
    这一类。[GitHub](https://github.com/JunkaiWang-TheoPhy/Mira-Light?utm_source=chatgpt.com)

所以它没问题，但**更像架构概念，不像代码同名实体**。

* * *

三、哪些词是合理的，不像误写
==============

这些词我觉得是可以保留的：

*   `Eyes`
*   `Body`
*   `Gateway`
*   `Reflex`
*   `Brain`
*   `Spirit`
*   `Action Decision`
*   `Servo`
*   `Mic`
*   `IR`
*   `MCU`

因为它们都和你现在这套“灵与肉 / U 型闭环 / 灯的身体语言”叙事是对得上的。

* * *

四、我对这张图的总体判断
============

1\. 它不是“完全错”
------------

它抓住了几个对的骨架：

*   灵 / 肉分层
*   Gateway 作为中介
*   Reflex / Brain / Spirit 三分
*   Action Decision 再折返回身体

这几个大的想法都对。

* * *

2\. 但它确实把 Mira 系统层和 Mira Light 灯本体层混在一起了
----------------------------------------

最明显的就是：

*   `HR`
*   `Home`
*   `OpenClaw Brain`
*   `Relationship / Spirit`  
    这些都更偏系统层，不完全是灯本体的东西。  
    而 `Mira Light 展位交互方案` 里的重点则更偏：
*   靠近
*   蹭蹭
*   追踪
*   点头
*   发呆
*   跳舞
*   送别
*   睡觉  
    这些身体语言。
    bbb0f523-2cc9-45fa-a397-f71a44f…

所以更准确地说，这图不是 “Mira Light 纯硬件图”，而是：

$$
\text{Mira Light as embodied endpoint} + \text{Mira system overlay}
$$

* * *

五、我建议你把这些缩写和标签改成下面这版
====================

如果你想让这张图更专业、更不“AI 味”，我建议直接改成：

Eyes
----

`Camera / Mic / IR / Touch`  
小字：`sensor fusion + MCU pre-process`

Body
----

`Servo / Light / Speaker / Smart Home`

Adaptive Core
-------------

里面两个并列：

*   `Reflex`
*   `Brain`

Spirit
------

`Role / Soul / Personality`  
`Memory traces / Caring style / Relationship`

Action Decision
---------------

`care form · timing · degree`  
`channel · sequencing · boundary`

这样会比原图顺很多。

* * *

六、最核心的几个缩写，你可以直接这样解释
====================

如果你只是想快速回答别人“这些缩写什么意思”，最短版就是：

*   **IR** = `Infrared`，红外，通常指红外接近/跟随/存在检测
*   **Mic** = `Microphone`，麦克风
*   **HR** = `Heart Rate`，心率，但在这张图里更像 Mira 整体系统输入，不一定是灯本体
*   **MCU** = `Microcontroller Unit`，单片机/微控制器
*   **Servo** = `Servo motor`，舵机
*   **OpenClaw** = 平台名，不是缩写
*   **state sync** = `state synchronization`，状态同步
*   **event bus** = 事件总线

### 可能是 AI 误写或半截写法的：

*   `HR / Sensor / MCU`（粒度混乱）
*   `Speaker / Home`（Home 少了 devices / smart）
*   `Protocol River`（修辞，不是标准名）
*   `Body execution`（占位感很强）
*   `Reflex input / Brain input / Spirit input`（AI 占位框）
*   `Memory texture`（偏 poetic，不像标准模块）

* * *

如果你愿意，我下一条可以直接继续帮你做一件更有用的事：  
我把这张图里的**所有标签**重写成一版 **既适合 PPT、又不那么 AI 味、并且区分 Mira 与 Mira Light 层级** 的最终文案。



---
Powered by [ChatGPT Exporter](https://www.chatgptexporter.com)