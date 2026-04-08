# Mira Light 集成状态矩阵

## 文档目的

这份文档用一张状态表回答：

> 目前这套系统到底哪些部分已经成熟、哪些只做到一半、哪些还没有闭环。

如需看 `Mira-Light` 如何具体接入 `Mira_v3` 最近新增的 layered memory / prompt-pack 链路，请优先对照：

- [`mira-light-to-mira-v3-layered-memory-integration-plan.md`](/Users/Zhuanz/Documents/Github/Mira-Light/docs/mira-light-to-mira-v3-layered-memory-integration-plan.md)

它的重点不是重复架构说明，而是把当前仓库里的：

- 文档
- 脚本
- 控制台
- 接收器
- bridge
- OpenClaw 接入
- 真实设备联通性

统一到一个“现实状态视图”中。

## 当前总体结论

截至当前这次梳理，仓库的整体状态是：

> 文档和代码骨架已经很完整，但真实设备接入与端到端实机验证仍然没有全部闭环。

更具体地说：

- `设备 API 定义`：比较成熟
- `展位场景设计`：比较成熟
- `导演台前端`：可运行且持续增强中
- `本地状态 / 文件接收器`：最简版可运行
- `本地 bridge / OpenClaw plugin`：骨架已成
- `真实灯接入`：当前仍是关键短板

## 当前状态矩阵

| 模块 | 当前状态 | 成熟度 | 说明 |
| --- | --- | --- | --- |
| 设备原始控制面 | 已明确 | 已经成熟 | `ESP32` 控制接口已由 [`ESP32 智能台灯.pdf`](/Users/Zhuanz/Documents/Github/Mira-Light/docs/ESP32%20智能台灯.pdf) 与 [`danpianji.html`](/Users/Zhuanz/Documents/Github/Mira-Light/docs/danpianji.html) 定义清楚。 |
| 设备交付文档 | 已整理 | 已经成熟 | [`esp32-smart-lamp-delivery-spec.md`](/Users/Zhuanz/Documents/Github/Mira-Light/docs/esp32-smart-lamp-delivery-spec.md) 已能作为设备接口交付文档使用。 |
| OpenClaw 控制思路 | 已整理 | 已经成熟 | [`openclaw-esp32-control-guide.md`](/Users/Zhuanz/Documents/Github/Mira-Light/docs/openclaw-esp32-control-guide.md) 已说明插件/bridge 路线。 |
| 展位场景翻译层 | 已整理 | 已经成熟 | [`mira-light-scene-to-code-spec.md`](/Users/Zhuanz/Documents/Github/Mira-Light/docs/mira-light-scene-to-code-spec.md) 已建立自然语言到动作原语映射。 |
| 展位场景表 | 已整理 | 已经成熟 | [`mira-light-booth-scene-table.md`](/Users/Zhuanz/Documents/Github/Mira-Light/docs/mira-light-booth-scene-table.md) 已经支持导演 / 主持人口播 / 失败回退。 |
| 最小展位 runbook | 已整理 | 半成熟 | [`mira-light-pdf-minimal-runbook.md`](/Users/Zhuanz/Documents/Github/Mira-Light/docs/mira-light-pdf-minimal-runbook.md) 适合 smoke test，但还不是完整长期 runbook。 |
| 场景执行脚本 | 已有 | 半成熟 | [`scripts/scenes.py`](/Users/Zhuanz/Documents/Github/Mira-Light/scripts/scenes.py) 和 [`scripts/booth_controller.py`](/Users/Zhuanz/Documents/Github/Mira-Light/scripts/booth_controller.py) 已可跑，但姿态值仍需真实灯校准。 |
| Pose / 校准体系 | 已有骨架 | 半成熟 | [`scripts/calibrate_lamp.py`](/Users/Zhuanz/Documents/Github/Mira-Light/scripts/calibrate_lamp.py) 和 [`config/mira_light_profile.example.json`](/Users/Zhuanz/Documents/Github/Mira-Light/config/mira_light_profile.example.json) 已就位，但本地真实 profile 还未确认。 |
| 导演台前端 | 已可运行 | 半成熟 | [`mira-light-director-console-spec.md`](/Users/Zhuanz/Documents/Github/Mira-Light/docs/mira-light-director-console-spec.md) 对应的页面已能运行，但更偏“骨架+polish中”。 |
| 本机最简接收器 | 已可运行 | 已经成熟 | [`scripts/simple_lamp_receiver.py`](/Users/Zhuanz/Documents/Github/Mira-Light/scripts/simple_lamp_receiver.py) 已支持状态与文件上传，对应 docs 已较完整。 |
| 状态 / 文件接收文档 | 已整理 | 已经成熟 | [`simple-lamp-receiver-overview.md`](/Users/Zhuanz/Documents/Github/Mira-Light/docs/simple-lamp-receiver-overview.md)、[`simple-lamp-receiver-api.md`](/Users/Zhuanz/Documents/Github/Mira-Light/docs/simple-lamp-receiver-api.md)、[`simple-lamp-receiver-esp32-examples.md`](/Users/Zhuanz/Documents/Github/Mira-Light/docs/simple-lamp-receiver-esp32-examples.md) 已适合交付。 |
| 图像流接收 | 已接入 | 半成熟 | [`mira-light-vision-stream-and-gemini-summary.md`](/Users/Zhuanz/Documents/Github/Mira-Light/docs/mira-light-vision-stream-and-gemini-summary.md) 已明确图像流入口，但视觉理解编排未闭环。 |
| 本机大模型接入思路 | 已整理 | 半成熟 | [`mira-light-local-model-local-openclaw-cloud-openclaw-overview.md`](/Users/Zhuanz/Documents/Github/Mira-Light/docs/mira-light-local-model-local-openclaw-cloud-openclaw-overview.md) 已有清楚路径，但自动决策器还未实现。 |
| 本机 OpenClaw 接入 | 已有骨架 | 半成熟 | 本机 runtime、bridge、plugin 骨架都在，但本机 OpenClaw 还没完成实机插件安装与闭环验证。 |
| 云端 OpenClaw 接入 | 已有方案 | 半成熟 | 路由器中转 / bridge / tunnel / plugin 路线已经明确，但还没有真正完成云端到真实灯的端到端打通。 |
| 路由器 / 本地中转枢纽文档 | 已成体系 | 已经成熟 | 相关 5 份 router hub 文档已经形成一个清晰的交付包。 |
| 多版本 PDF 梳理 | 未收束 | 还未闭环 | 当前 `展位交互方案.pdf` 存在多个版本，尚未明确哪个是主版本。 |
| docs 内的代码型文件 | 未收束 | 还未闭环 | `docs/cam_receiver.py`、`docs/cam_receiver_new.py` 更像实现入口，位置暂不够规范。 |
| 真实灯联通性 | 未确认 | 还未闭环 | 当前最关键短板。设备是否真的在线、真实 IP 是否正确、当前 Wi‑Fi 是否一致，仍未完成最终闭环。 |

## 当前最关键的现实问题

当前最重要的不是再补新方案，而是：

> 真实设备是否已经处于当前控制链可达状态。

当前已确认：

- 本机当前 IP：`192.168.0.101`
- 控制台之前尝试访问的设备地址：`172.20.10.3`
- 当前请求：

```bash
curl http://172.20.10.3/status
```

返回超时。

这意味着至少当前这一刻：

- 本机与 `172.20.10.3` 不在同一可达路径上
- 或者该地址上没有灯在响应

所以当前的真实短板不是“控制台 UI 不够漂亮”，而是：

**底层设备在线性还没有确认。**

## 如果按优先级只看 3 件事

### 1. 先确认真实设备在线

先确认：

```bash
curl http://<真实灯IP>/status
```

### 2. 再确认本机 runtime / 控制台能打到这台灯

只有当第 1 步成功后，导演台和 scene runner 的价值才会真正体现出来。

### 3. 再继续推进本机 OpenClaw 与云端 OpenClaw

否则 bridge / plugin / router hub 都会停留在纸面上。

## 一句话总结

如果把当前仓库整体看作一个工程系统，那么它现在处于：

> 文档体系成熟、代码骨架完整、真实设备链路未最终闭环的阶段。
