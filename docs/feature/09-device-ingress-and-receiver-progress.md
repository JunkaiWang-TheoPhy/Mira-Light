# Device Ingress and Receiver Progress

## Current Status

当前仓库已经具备两类不同定位的设备入口，而不是只有“电脑去控制灯”的单向链路：

- 最简接收器
- 图像接收器

这意味着仓库现在不仅有控制面，也开始有设备到电脑的 ingress 面。

## 1. Minimal Receiver Progress

基于 [../simple-lamp-receiver-overview.md](../simple-lamp-receiver-overview.md)，
当前仓库已经有一个很清晰的最简接收器方案：

- `scripts/simple_lamp_receiver.py`

它承担的是：

- `GET /health`
- `POST /device/status`
- `POST /device/upload`
- `POST /device/upload-base64`

它的角色可以理解成：

> 灯给电脑发状态、图片和文件的收件箱。

### Why This Matters

这一步很重要，因为早期很多系统只有：

- 电脑控制灯

但没有：

- 灯向电脑持续回传状态与文件

而最简接收器把这条链先打通了。

### What It Already Produces

当前最简接收器已经定义了标准落盘结构：

- `snapshots/`
- `events/`
- `uploads/`

这意味着它已经不只是 demo 接口，而是开始具备运行时记录价值。

## 2. Camera Receiver Progress

仓库还已经有 formalized HTTP camera receiver 路线，主入口包括：

- `docs/cam_receiver_new.py`
- `scripts/run_cam_receiver.sh`
- `scripts/setup_cam_receiver_env.sh`

当前已知输入是：

- JPEG 帧

当前已知监听端口：

- `8000`

它的作用是：

- 接连续图像流
- 让视觉理解系统有明确 ingress
- 为后续 extractor / replay / vision bridge 提供稳定输入

## 3. The Role Boundary Is Already Clear

当前仓库对这两类入口的定位其实已经很清楚：

- `simple_lamp_receiver.py` 是最小起步方案
- `mira_light_bridge` 是后续完整系统方案
- `cam_receiver` 是图像流 ingress

也就是说：

- 最简接收器负责“先把设备上报链接好”
- 图像接收器负责“先把视觉输入链接好”
- bridge/runtime/OpenClaw 负责“把这些输入吸收到更完整的编排系统里”

## 4. What Is Still Not Fully Landed

这里也需要区分已具备和未完全闭环：

- `已具备`：状态上传、文件上传、JPEG 接收、保存落盘、开发脚本
- `未完全闭环`：正式的大模型自动决策器、完整的 ingress-to-decision-to-action 主线

所以当前更准确的说法是：

仓库已经把设备回传入口和图像流入口搭好了，但“自动读取这些输入并做最终稳定决策”
仍然不是完全落地状态。

## Why This Progress Matters

这部分进展很关键，因为它让 `Mira-Light` 不再只是：

- 被电脑控制的输出设备

而开始成为：

- 会回传状态的设备节点
- 会上传图片/文件的设备节点
- 可进入 vision/runtime 系统的输入端

## Recommended External Framing

> `Mira-Light` 现在已经不只有控制接口，也有设备 ingress 层。仓库里既有最简状态/文件接收器，
> 也有图像流接收器，这为后续视觉理解、本机决策和 OpenClaw 编排提供了稳定的输入入口。
