# Camera Streaming

这个目录放的是板端和摄像头、HTTP 图像发送、RTSP 推流相关的脚本。

## 当前包含

- `cam_preview.py`
- `cam_receiver.py`
- `cam_sender.py`
- `rtsp_server.py`

## 对深圳版的作用

这一层不是一级动作种子，但对下面几类事情有帮助：

- `sz_tabletop_follow` 的视觉调试
- 板端摄像头是否能正常出流
- 临时搭建一条“看见板端画面”的联调链路

## 文件说明

### `cam_preview.py`

本地预览板子上的 USB 摄像头。

### `cam_sender.py` / `cam_receiver.py`

一组 HTTP 发图与收图脚本。

更适合快速临时验证图像链路，而不是长期产品化方案。

### `rtsp_server.py`

在板子上起 RTSP 推流。

如果深圳版后面要做更正式的视觉调试，这个文件会比 `cam_sender.py` 更重要。

## 一句话总结

这个目录不是动作本体，但它决定你能不能把板端视觉链路看清楚。
