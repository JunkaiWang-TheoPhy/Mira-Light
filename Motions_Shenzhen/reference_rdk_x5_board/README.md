# RDK X5 Board Reference

这个目录收的是：

> 从远程地瓜开发板 `/home/sunrise` 直接拉回来的“板端有用文件”参考层。

这里和 `reference_default_pack/` 的区别很大。

## 两个参考层的区别

### `reference_default_pack/`

来源：

- 本地仓库当前默认 `Motions/`

用途：

- 参考主控台 manifest 怎么写
- 参考默认主包的测试文档怎么写

### `reference_rdk_x5_board/`

来源：

- 远程地瓜板 `/home/sunrise`

用途：

- 找真实板端已经跑通过的动作脚本
- 找 UART1 舵机、UART3 灯头的协议说明
- 找板上实际联调过的控制脚本
- 找深圳版动作设计最贴近真机的“硬件种子”

## 当前目录结构

- [end-side-protocol-layer.md](./end-side-protocol-layer.md)
  端侧真实协议层说明
- [python-motion-orchestration-layer.md](./python-motion-orchestration-layer.md)
  端侧 Python 动作编排层说明
- [latest-board-diff-2026-04-25.md](./latest-board-diff-2026-04-25.md)
  与昨日快照相比的最新差异
- [board-file-index.md](./board-file-index.md)
  板端文件总索引
- [board_docs/README.md](./board_docs/README.md)
  板端说明文档与协议资料
- [servo_motion_scripts/README.md](./servo_motion_scripts/README.md)
  板端舵机动作脚本
- [led_uart_scripts/README.md](./led_uart_scripts/README.md)
  板端灯头 UART 控制脚本
- [camera_streaming/README.md](./camera_streaming/README.md)
  摄像头和 RTSP 相关脚本
- [hardware_experiments/README.md](./hardware_experiments/README.md)
  板端实验性脚本
- [network_config/README.md](./network_config/README.md)
  板端远程连接相关配置

同时保留两层原始快照目录：

- `raw_snapshot/`
  原始 tar 包
- `extracted/`、`extracted_extra/`
  从板端 tar 包直接解开的原始目录

这三层不要当作最终整理结果读，主要用于溯源。

## 这层为什么重要

如果你后面要真正把深圳版 scene pack 落到真机，最重要的不是默认 `Motions/`，而是：

- 板上现成能跑的舵机动作脚本
- 板上真实使用的串口协议文档
- 板上真实联调过的 LED/UART/RTSP 工具
- 板端新增的微动作种子脚本

也就是说：

- `reference_default_pack/` 更偏“主控台和软件结构”
- `reference_rdk_x5_board/` 更偏“板端真实控制能力”

## 一句话总结

这个目录不是仓库里已有 motion 的复制品，而是：

> 从远程地瓜板 `/home/sunrise` 拉回来的板端控制种子层。
