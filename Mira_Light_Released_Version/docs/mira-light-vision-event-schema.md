# Mira Light 视觉事件 JSON Schema 说明

## 文档目的

这份文档用于定义“单摄像头视觉层”与“runtime / scenes / OpenClaw / 本地大模型”之间的稳定数据边界。

它解决的问题是：

- 单摄像头应该输出什么，而不是直接控制舵机
- 四自由度灯具真正需要哪些视觉信息
- 二维视觉和“单目伪三维距离感”应该怎样同时表达

对应的机器可读 schema 文件是：

- [`config/mira_light_vision_event.schema.json`](/Users/Zhuanz/Documents/Github/Mira-Light/config/mira_light_vision_event.schema.json)

## 一句话原则

视觉层只负责回答：

```text
我看见了什么
它在画面哪里
它相对变近还是变远
现在更适合哪个 scene
```

视觉层不直接回答：

```text
servo1 应该转多少度
现在立刻执行哪个底层 HTTP 调用
```

## 为什么单摄像头也能做“基本距离感”

单摄像头做不了真正的几何深度恢复，但在 Mira Light 当前场景里，完全可以做“够用的距离感”。

这里的距离感不是毫米级深度，而是：

- `near`
- `mid`
- `far`

以及：

- `approaching`
- `receding`
- `stable`

这个判断来自目标在画面里的：

- 框面积大小
- 面积变化趋势
- 持续帧稳定性

所以这里实际做的是：

```text
二维位置 + 单目尺度启发式
```

而不是：

```text
真正三维深度测量
```

## Schema 分层设计

### 1. 顶层事件类型

推荐只保留四类：

- `target_seen`
- `target_updated`
- `target_lost`
- `no_target`

这四类已经足够覆盖当前展位闭环：

- 有人出现 -> `wake_up`
- 有人停留 -> `curious_observe`
- 有人移动 -> `track_target`
- 目标消失 -> `sleep`

### 2. source

这一层描述“这个视觉事件是怎么来的”。

当前建议固定为：

- `pipeline = saved_jpeg_watch`
- `camera_mode = single_camera_2d`
- `distance_mode = monocular_heuristic`

这能明确区分：

- 它不是双目
- 它不是 ToF
- 它不是 LiDAR
- 它是单摄像头启发式距离感

### 3. frame

这一层记录当前事件对应的图像来源。

核心字段：

- `path`
- `width`
- `height`
- `seq`
- `capture_ts`

这能帮助后续：

- 回放
- 调试
- 导演台日志追踪

### 4. tracking

这是最核心的一层。

它回答的是：

- 有没有目标
- 目标是什么
- 目标在哪
- 当前距离感是什么

关键字段包括：

- `target_present`
- `target_class`
- `detector`
- `confidence`
- `bbox_norm`
- `center_norm`
- `horizontal_zone`
- `vertical_zone`
- `size_norm`
- `distance_band`
- `approach_state`

其中：

- `bbox_norm` 和 `center_norm` 是标准二维视觉输出
- `distance_band` 和 `approach_state` 是单目“伪三维”输出

### 5. scene_hint

这一层不是执行结果，而是建议。

推荐只允许：

- `wake_up`
- `curious_observe`
- `track_target`
- `sleep`
- `none`

原因很简单：

- 第一版视觉闭环不要同时驱动所有 scene
- 先把最基本的“看见 -> 唤醒 / 跟随 / 休眠”做稳定

### 6. control_hint

这一层是给 runtime 做二次映射的中间信号，不是最终舵机角度。

核心字段：

- `yaw_error_norm`
- `pitch_error_norm`
- `lift_intent`
- `reach_intent`

这几个值的作用分别对应四自由度：

- `servo1`：主要看 `yaw_error_norm`
- `servo2`：主要看 `lift_intent`
- `servo3`：主要看 `reach_intent`
- `servo4`：主要看 `pitch_error_norm` 或细微表情

## 二维视觉怎么映射到四自由度

### `servo1`：底座转向

它主要负责：

- 左右看向目标

输入来自：

- `center_norm.x`
- `horizontal_zone`
- `yaw_error_norm`

### `servo2`：下臂抬升

它主要负责：

- 抬高 / 降低整体姿态

输入来自：

- `vertical_zone`
- `lift_intent`
- `distance_band`

### `servo3`：前探 / 收回

它主要负责：

- 靠近目标
- 收回
- 跟踪时形成“关注感”

输入来自：

- `distance_band`
- `approach_state`
- `reach_intent`

### `servo4`：灯头俯仰 / 微表情

它主要负责：

- 灯头看上 / 看下
- 轻微歪头
- 情绪性补充动作

输入来自：

- `center_norm.y`
- `pitch_error_norm`

## 为什么不让视觉层直接输出舵机角度

因为视觉识别和舵机控制之间必须留一层 runtime。

否则会出现三个问题：

- 视觉代码里掺杂大量硬件细节
- 不同场景下无法复用
- 一旦伺服校准变化，视觉逻辑全部失效

正确关系应该是：

```text
视觉层
-> 输出标准事件
-> runtime 翻译为 scene / pose / primitive
-> ESP32 API
```

## 2D / 3D 的推荐工程划分

### 第一层：二维稳定输出

这是必须先做稳的部分：

- 位置
- 框
- 左中右
- 上中下
- 是否持续存在

### 第二层：单目距离启发式

这是当前最适合单摄像头补的“伪三维”能力：

- `near / mid / far`
- `approaching / receding / stable`

### 第三层：高层模型解释

如果后面接 Gemini / Qwen / Kimi，这一层更适合输出：

- `scene_hint`
- `reason`
- `interaction_intent`

而不是替代第一层和第二层。

## 推荐的第一版使用方式

当前最推荐的落地路径是：

```text
cam_receiver_new.py
-> 保存 JPEG
-> track_target_event_extractor.py
-> 输出 vision event JSON
-> runtime / scenes
```

也就是说：

- 先让本地 CV 产出稳定 schema
- 再让大模型做高层语义增强

## 示例事件

```json
{
  "schema_version": "1.0.0",
  "event_type": "target_updated",
  "timestamp": "2026-04-08T18:00:00+08:00",
  "source": {
    "pipeline": "saved_jpeg_watch",
    "camera_mode": "single_camera_2d",
    "distance_mode": "monocular_heuristic"
  },
  "frame": {
    "path": "/Users/Zhuanz/Documents/Github/Mira-Light/captures/frame-0001.jpg",
    "width": 640,
    "height": 480,
    "seq": "5043",
    "capture_ts": null
  },
  "tracking": {
    "target_present": true,
    "target_class": "person",
    "detector": "haar_face",
    "confidence": 0.89,
    "bbox_norm": {"x": 0.40, "y": 0.22, "w": 0.18, "h": 0.26},
    "center_norm": {"x": 0.49, "y": 0.35},
    "horizontal_zone": "center",
    "vertical_zone": "middle",
    "size_norm": 0.0468,
    "distance_band": "mid",
    "approach_state": "approaching"
  },
  "scene_hint": {
    "name": "track_target",
    "reason": "目标稳定存在且位置正在变化，适合进入跟随观察。"
  },
  "control_hint": {
    "yaw_error_norm": -0.02,
    "pitch_error_norm": 0.30,
    "lift_intent": 0.52,
    "reach_intent": 0.58
  },
  "raw_measurements": {
    "frame_age_ms": 120.5,
    "bbox_area_px": 14372,
    "size_delta_norm": 0.011
  }
}
```

## 一句话总结

对 Mira Light 来说，单摄像头不需要假装做出真正三维重建。  
最正确的方案是：

```text
二维定位做准
单目尺度做基本距离感
高层语义交给大模型
场景编排交给 runtime
```
