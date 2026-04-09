# Mira Light 路由器中转枢纽接入交付包

## 文档目的

这组文件用于把 `Mira Light` 接入远端 `OpenClaw` 的推荐方案正式化为可交付材料。

这里的重点不是“让服务器直接访问单片机”，而是明确：

- 为什么需要本地中转枢纽
- 路由器或边缘主机应该承担什么职责
- 当前项目已经确认了什么、还缺什么
- 下一步应该按什么顺序实施

本文档包主要面向：

- 方案设计者
- OpenClaw 插件开发者
- 本地 bridge 开发者
- 网络与部署执行者

## 阅读顺序

建议按下面顺序阅读。

1. [`mira-light-router-hub-architecture.md`](../docs/mira-light-router-hub-architecture.md)
   先看整体架构、角色分工和为什么这么设计。
2. [`mira-light-router-hub-current-status.md`](../docs/mira-light-router-hub-current-status.md)
   再看当前状态、已确认项、缺口和风险。
3. [`mira-light-router-hub-implementation-guide.md`](../docs/mira-light-router-hub-implementation-guide.md)
   然后按步骤实施。
4. [`mira-light-router-hub-next-steps.md`](../docs/mira-light-router-hub-next-steps.md)
   最后对照下一步清单推进。

## 相关基础文档

这套交付包建立在以下已有文档之上：

- [`openclaw-esp32-control-guide.md`](../docs/openclaw-esp32-control-guide.md)
- [`esp32-smart-lamp-delivery-spec.md`](../docs/esp32-smart-lamp-delivery-spec.md)
- [`mira-light-scene-to-code-spec.md`](../docs/mira-light-scene-to-code-spec.md)
- [`mira-light-pdf2-implementation-audit.md`](../docs/mira-light-pdf2-implementation-audit.md)
- [`mira-light-pdf2-engineering-handoff.md`](../docs/mira-light-pdf2-engineering-handoff.md)
- [`danpianji.html`](../docs/danpianji.html)

## 一句话结论

如果 `OpenClaw` 在云服务器上，而 `ESP32 Mira Light` 在你身边的局域网里，那么最稳妥的方案不是公网直连单片机，而是：

```text
ESP32 Mira Light
-> 本地路由器/边缘主机
-> 本地 mira-light bridge
-> 反向隧道或私网通道
-> 云服务器
-> OpenClaw mira-light 插件
-> OpenClaw
```

其中，“路由器”更准确地说是“本地中转枢纽”。  
它可以是：

- 可编程的 `OpenWrt` 路由器
- 软路由
- 树莓派
- 长期开机的小主机

普通只负责发 Wi‑Fi、不能装服务的家用路由器，不适合承担这项职责。
