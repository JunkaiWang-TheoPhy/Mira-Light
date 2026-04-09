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

## 2.5 直接挂接你现在这台机器上的实时预览器

如果你已经在用现成的接收器和预览窗口：

- receiver: `0.0.0.0:8000`
- captures: `/Users/huhulitong/.openclaw/workspace/runtime/captures`
- preview window: `Mira Light Capture Preview`

那最推荐的跑法是只启动 extractor + bridge，直接复用当前链路：

```bash
cd /Users/huhulitong/Documents/GitHub/Mira-Light
bash scripts/run_mira_light_live_follow_demo.sh \
  --attach-existing-receiver \
  --base-url http://172.20.10.3 \
  --runtime-dir ./runtime/live-follow-demo-real
```

如果要先用 mock 灯验证后半段控制链路，也可以：

```bash
cd /Users/huhulitong/Documents/GitHub/Mira-Light
bash scripts/run_mira_light_live_follow_demo.sh \
  --attach-existing-receiver \
  --mock-device \
  --mock-port 19791 \
  --runtime-dir ./runtime/live-follow-demo-attach-mock
```

这时脚本不会再启动新的 `8000` 接收器，也不会动你的预览窗口；
它只会消费现成的 `captures/` 目录。

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
- `touch-persistence-frames = 3`
- `touch-cooldown-ms = 9000`
- `touch-hand-arm-min-confidence = 0.68`
- `hand-avoid-cooldown-ms = 7000`
- `hand-avoid-min-confidence = 0.78`
- `hand-avoid-max-center-y = 0.74`
- `hand-avoid-extended-max-center-y = 0.86`
- `hand-avoid-extended-min-confidence = 0.90`
- `hand-avoid-min-lateral-offset = 0.18`
- `hand-cue-min-area-ratio = 0.0015`
- `hand-cue-max-area-ratio = 0.06`
- `hand-cue-min-center-y = 0.34`
- `hand-cue-min-motion-ratio = 0.12`
- `hand-cue-min-confidence = 0.55`
- 默认关闭 `touch-allow-person-fallback`

### 4.1 `touch_affection` 的当前推荐策略

`touch_affection` 现在默认不再仅靠“近距人体”自动触发，而是优先依赖 extractor 产出的显式 `hand / arm cue`：

- `track_target_event_extractor.py` 会输出 `interaction_hint`
- `vision_runtime_bridge.py` 只在 `interaction_hint` 满足连续帧和冷却条件时才触发 `hand_near`
- 如果你确实要回退到旧的“人靠近就算 touch 候选”逻辑，可以显式加：

```bash
--touch-allow-person-fallback
```

### 4.2 `hand_avoid` 的当前推荐策略

`hand_avoid` 现在和 `touch_affection` 共用同一份显式 `hand / arm cue`，但判定更保守：

- 只有显式 `interaction_hint.hand_arm_present = true` 才会考虑躲避
- cue 需要在画面左侧或右侧，`center` 默认更像亲近而不是威胁
- cue 需要相对更高一些，低位、靠近灯前方的手更容易被当成 `touch_affection`
- 但如果 cue 明显从侧边侵入，而且 lateral offset 足够大、置信度也很高，那么即使更低一些也能触发轻躲避
- `hand_avoid` 会先于 `touch_affection` 评估，所以“侧边突然伸来的手”会优先触发轻轻躲开

如果你想让它更不容易躲，可以收紧：

```bash
bash scripts/run_mira_light_live_follow_demo.sh \
  --attach-existing-receiver \
  --hand-avoid-min-confidence 0.84 \
  --hand-avoid-max-center-y 0.68
```

如果你想让它更敏感一点，可以逐步放宽：

```bash
bash scripts/run_mira_light_live_follow_demo.sh \
  --attach-existing-receiver \
  --hand-avoid-min-confidence 0.74 \
  --hand-avoid-cooldown-ms 5000
```

### 4.3 这台机器当前真实摄像头的调参结果

按 `2026-04-09` 这台 Mac 当前的 `8000 + captures` 实况画面做过一轮负样本调参后：

- 最近 `120` 帧里仍然会出现少量 `interaction_hint`
- 这些 cue 主要来自画面下方交互区，而不是右侧人脸边缘
- 同一段回放里，最终 `hand_near_trigger_count = 0`

也就是说，当前默认值已经更偏“保守不乱动”，适合先在嘈杂会场里压低误触发。

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

如果 `touch_affection` 还是太容易触发，就继续收紧 hand cue：

```bash
bash scripts/run_mira_light_live_follow_demo.sh \
  --attach-existing-receiver \
  --hand-cue-min-center-y 0.60 \
  --touch-persistence-frames 4 \
  --touch-hand-arm-min-confidence 0.74
```

如果 `touch_affection` 太难触发，再逐步放宽：

```bash
bash scripts/run_mira_light_live_follow_demo.sh \
  --attach-existing-receiver \
  --hand-cue-min-motion-ratio 0.10 \
  --touch-persistence-frames 2 \
  --touch-hand-arm-min-confidence 0.64
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
