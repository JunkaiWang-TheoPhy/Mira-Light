# Mira Light 真人跟随 Demo Runbook

这份 runbook 对应仓库内第一版“单目视觉 -> 事件提取 -> runtime 跟随”的最短运行路径。

核心入口：

- [scripts/run_mira_light_live_follow_demo.sh](/Users/huhulitong/Documents/GitHub/Mira-Light/scripts/run_mira_light_live_follow_demo.sh)
- [scripts/replay_camera_frames_to_receiver.py](/Users/huhulitong/Documents/GitHub/Mira-Light/scripts/replay_camera_frames_to_receiver.py)
- [scripts/run_mira_light_vision_stack.sh](/Users/huhulitong/Documents/GitHub/Mira-Light/scripts/run_mira_light_vision_stack.sh)

## 1. 先做本地自验

不等真实灯，也不等真实摄像头，先用样例帧和 mock 灯把整条链路跑通：

```bash
cd /Users/huhulitong/Documents/GitHub/Mira-Light
bash scripts/run_mira_light_live_follow_demo.sh \
  --mock-device \
  --replay-demo \
  --receiver-port 18000 \
  --runtime-dir ./runtime/live-follow-demo-mock
```

如果你想持续观察 event 和 mock 灯状态，加上 `--replay-loop`：

```bash
bash scripts/run_mira_light_live_follow_demo.sh \
  --mock-device \
  --replay-demo \
  --replay-loop \
  --receiver-port 18000 \
  --runtime-dir ./runtime/live-follow-demo-mock
```

这条命令会同时启动：

- 本地 mock lamp
- HTTP 相机接收器
- `track_target_event_extractor.py`
- `vision_runtime_bridge.py`
- 样例帧回放器

重点看这几个输出：

- [vision.latest.json](/Users/huhulitong/Documents/GitHub/Mira-Light/runtime/live-follow-demo-mock/vision.latest.json)
- [vision.events.jsonl](/Users/huhulitong/Documents/GitHub/Mira-Light/runtime/live-follow-demo-mock/vision.events.jsonl)
- [vision.bridge.state.json](/Users/huhulitong/Documents/GitHub/Mira-Light/runtime/live-follow-demo-mock/vision.bridge.state.json)
- [vision-stack.log](/Users/huhulitong/Documents/GitHub/Mira-Light/runtime/live-follow-demo-mock/vision-stack.log)

快速检查：

```bash
curl http://127.0.0.1:18000/health
curl http://127.0.0.1:9791/health
tail -f ./runtime/live-follow-demo-mock/vision.events.jsonl
```

## 2. 再接真灯

把 `--mock-device` 去掉，换成真实灯地址：

```bash
cd /Users/huhulitong/Documents/GitHub/Mira-Light
bash scripts/run_mira_light_live_follow_demo.sh \
  --base-url http://172.20.10.3 \
  --receiver-port 8000 \
  --runtime-dir ./runtime/live-follow-demo-real
```

这时脚本会等待真实相机推流到本机 `8000` 端口。

如果你已经有外部发送端，只要它持续 `POST image/jpeg` 到：

```text
http://这台Mac的IP:8000
```

并带上可选请求头：

- `X-Seq`
- `X-Timestamp`

就能接进来。

## 3. 没有真实摄像头时，单独回放样例帧

如果视觉栈已经在跑，只想手动把样例帧推到接收器：

```bash
cd /Users/huhulitong/Documents/GitHub/Mira-Light
./.venv/bin/python scripts/replay_camera_frames_to_receiver.py \
  --captures-dir ./runtime/vision-demo-captures \
  --receiver-url http://127.0.0.1:8000 \
  --fps 3
```

循环回放：

```bash
./.venv/bin/python scripts/replay_camera_frames_to_receiver.py \
  --captures-dir ./runtime/vision-demo-captures \
  --receiver-url http://127.0.0.1:8000 \
  --fps 3 \
  --loop
```

## 4. 推荐起步阈值

这套 demo 脚本默认已经用了较适合真人跟随首版的参数：

- `poll-interval = 0.2`
- `tracking-update-ms = 180`
- `face-near-area-ratio = 0.08`
- `face-mid-area-ratio = 0.025`
- `motion-near-area-ratio = 0.16`
- `motion-mid-area-ratio = 0.05`
- `min-motion-area-ratio = 0.012`
- `warmup-frames = 8`

如果你想边跑边调，可以直接在启动脚本上覆写。

例子：目标太难触发，就把面积阈值降一点：

```bash
bash scripts/run_mira_light_live_follow_demo.sh \
  --mock-device \
  --replay-demo \
  --receiver-port 18000 \
  --face-mid-area-ratio 0.02 \
  --motion-mid-area-ratio 0.04
```

如果跟随太抖，就放慢 tracking 更新：

```bash
bash scripts/run_mira_light_live_follow_demo.sh \
  --base-url http://172.20.10.3 \
  --tracking-update-ms 240 \
  --warmup-frames 10
```

## 5. 现场判断有没有跑通

满足下面几条，就说明第一版真人跟随 demo 已经成立：

- `receiver /health` 有持续增长的 `frame_count`
- `vision.events.jsonl` 里 `horizontal_zone` 会跟着人变化
- `vision.latest.json` 里能看到合理的 `distance_band`
- `vision.bridge.state.json` 里 `runtime.trackingActive` 会变成 `true`
- 真灯或 mock 灯的舵机会随着 `yaw_error_norm / pitch_error_norm` 变化

## 6. 最常见的问题

`没有任何 event`

- 先看接收器健康检查是不是有新帧
- 再看 `captures/` 里有没有新的 `.jpg`

`一直只有 sleep`

- 目标太小，先降低 `face-mid-area-ratio` / `motion-mid-area-ratio`
- 背景减除没热起来，先把 `warmup-frames` 调低做验证

`能识别但跟随抖`

- 把 `tracking-update-ms` 调高到 `220` 或 `260`
- 让目标尽量在干净背景前移动，先验证主链路

`真实灯没反应`

- 先 `curl <base-url>/status`
- 如果真灯还没联通，先用 `--mock-device` 验证视觉链路本身
