# Mira Light 未完成场景闭环落实方案

## 文档目的

这份文档专门回答当前仓库里最明确还没完成的 4 个缺口，应该如何从“已有骨架”推进到“可联调、可验收、可发布”的状态：

1. `track_target` 的真实视觉闭环
2. `farewell` 的动态离场方向跟随
3. `voice_demo_tired / sigh_demo` 的真实语音触发
4. `multi_person_demo` 的多人目标检测

它的重点不是重复场景设计，而是把：

- 当前仓库已经有什么
- 还缺哪一段链路
- 应该新增或修改哪些文件
- 每一步的最小验收标准是什么

写成一份可以直接照着执行的工程方案。

## 先说当前真相

这 4 个缺口并不是“完全没开始”，而是完成度不一致。

### 已经有的基础

- [`scripts/scenes.py`](/Users/Zhuanz/Documents/Github/Mira-Light/scripts/scenes.py)
  - 已有这 4 个 scene 的 choreography 骨架与 TODO 提示
- [`scripts/mira_light_runtime.py`](/Users/Zhuanz/Documents/Github/Mira-Light/scripts/mira_light_runtime.py)
  - 已支持 `scene_context`
  - 已支持动态 `farewell`
  - 已支持动态 `multi_person_demo`
  - 已支持 `trigger_event(...)`
  - 已支持 `apply_tracking_event(...)`
- [`scripts/vision_runtime_bridge.py`](/Users/Zhuanz/Documents/Github/Mira-Light/scripts/vision_runtime_bridge.py)
  - 已能把视觉事件路由到 `wake_up / curious_observe / sleep`
  - 已能把 `target_updated + track_target` 送入 `runtime.apply_tracking_event(...)`
- [`scripts/mira_realtime_voice_interaction.py`](/Users/Zhuanz/Documents/Github/Mira-Light/scripts/mira_realtime_voice_interaction.py)
  - 已有 `comfort / farewell / praise` 意图分类
  - 已有 `voice_tired` 和 `farewell_detected` 的桥接触发

### 真正还缺的部分

- `track_target`
  - 缺“检测稳定性 + 事件稳定性 + 真实追踪验收”
- `farewell`
  - runtime 已有动态方向 scene builder，但缺“离场方向事件来源”
- `voice_demo_tired / sigh_demo`
  - `voice_demo_tired` 已经有半条链路
  - `sigh_demo` 还缺真实事件生产
- `multi_person_demo`
  - runtime 已有动态 scene builder，但缺“多人检测事件生产”和“主次目标选择策略”

所以正确策略不是重写 `scenes.py`，而是补齐：

```text
感知/识别
-> 标准事件
-> runtime trigger / scene_context
-> scene 动态化执行
-> fixture + 测试 + 验收
```

## 一、`track_target` 的真实视觉闭环

## 当前状态

- 静态 choreography 已在 [`scripts/scenes.py`](/Users/Zhuanz/Documents/Github/Mira-Light/scripts/scenes.py) 中存在
- 单目视觉事件提取器已存在：[`scripts/track_target_event_extractor.py`](/Users/Zhuanz/Documents/Github/Mira-Light/scripts/track_target_event_extractor.py)
- 视觉桥已存在：[`scripts/vision_runtime_bridge.py`](/Users/Zhuanz/Documents/Github/Mira-Light/scripts/vision_runtime_bridge.py)
- runtime 已存在实时控制入口：[`scripts/mira_light_runtime.py`](/Users/Zhuanz/Documents/Github/Mira-Light/scripts/mira_light_runtime.py)

这说明它已经不是“没有闭环入口”，而是“闭环质量还不够稳定”。

## 最小落地路线

### 第 1 步：冻结事件真值

统一 `track_target` 只消费这 4 类事件：

- `target_seen`
- `target_updated`
- `target_lost`
- `no_target`

并且要求事件里至少稳定包含：

- `tracking.target_present`
- `tracking.horizontal_zone`
- `tracking.vertical_zone`
- `tracking.distance_band`
- `tracking.confidence`
- `control_hint.yaw_error_norm`
- `control_hint.pitch_error_norm`
- `control_hint.lift_intent`
- `control_hint.reach_intent`

如果没有这些字段，就不要让 bridge/runtime 猜。

### 第 2 步：先把检测稳定性做够

优先改 [`scripts/track_target_event_extractor.py`](/Users/Zhuanz/Documents/Github/Mira-Light/scripts/track_target_event_extractor.py)，不是先改 runtime。

需要补的能力：

- 加事件去抖
  - 同一目标短时间内位置轻微抖动，不要重复发大幅变化事件
- 加目标保持
  - 检测短时丢帧时，不要立刻触发 `target_lost`
- 加最小置信度和最小面积门槛
- 加目标 ID 或至少“当前主目标”稳定逻辑

### 第 3 步：把 runtime 的 tracking 当成主路径，不再把 `track_target` 当成静态 scene 主路径

建议执行语义改成：

- `target_seen`
  - 触发 `wake_up`
- `target_updated + scene_hint=track_target`
  - 主走 `apply_tracking_event(...)`
- `target_lost`
  - 进入 grace period
- `no_target`
  - 触发 `sleep`

也就是说：
- `track_target` 保留 choreography 作为排练 fallback
- 真正展示“它看得见”的时候，主路径应该是 live tracking

### 第 4 步：补 fixture 和回放

新增或补强：

- `fixtures/vision_events/target_seen.json`
- `fixtures/vision_events/target_updated_left.json`
- `fixtures/vision_events/target_updated_right.json`
- `fixtures/vision_events/target_lost.json`
- `fixtures/vision_events/no_target.json`

配合：

- [`scripts/vision_replay_bench.py`](/Users/Zhuanz/Documents/Github/Mira-Light/scripts/vision_replay_bench.py)
- [`tests/test_vision_runtime_bridge.py`](/Users/Zhuanz/Documents/Github/Mira-Light/tests/test_vision_runtime_bridge.py)

### 最小验收标准

- 单目标左右移动时，servo yaw 会跟随，而不是只跑固定 choreography
- 短时遮挡不会立刻进入 `sleep`
- 连续 replay 同一批 fixture，事件计数和 scene 计数稳定
- `tests/test_vision_runtime_bridge.py` 增加：
  - `target_seen -> wake_up`
  - `target_updated -> apply_tracking_event`
  - `target_lost -> grace`
  - `no_target -> sleep`

## 二、`farewell` 的动态离场方向跟随

## 当前状态

这部分不是从零开始。

[`scripts/mira_light_runtime.py`](/Users/Zhuanz/Documents/Github/Mira-Light/scripts/mira_light_runtime.py) 已经有：

- `_build_dynamic_farewell_scene(...)`
- `_direction_from_context(...)`
- `trigger_event("farewell_detected", {...})`

也就是说，动态版 `farewell` 的 scene 生成逻辑已经有了。  
真正缺的是：

- 谁来提供 `departureDirection`
- 何时判定“人正在离开”

## 最小落地路线

### 第 1 步：把离场方向判定放进视觉桥，不要放进 `scenes.py`

在 [`scripts/vision_runtime_bridge.py`](/Users/Zhuanz/Documents/Github/Mira-Light/scripts/vision_runtime_bridge.py) 增加一条专门的离场逻辑：

- 连续若干帧 `target_present=false`
- 且最近一次 `horizontal_zone` 有稳定值
- 且最近运动方向是远离中心

则发：

```json
{
  "event": "farewell_detected",
  "payload": {
    "direction": "left"
  }
}
```

### 第 2 步：不要新增第二份 `farewell` choreography

动态 `farewell` 仍然应该复用 runtime 里的 `_build_dynamic_farewell_scene(...)`。  
不要再在 `scripts/scenes.py` 里复制出 `farewell_left / farewell_right / farewell_center` 三个场景。

### 第 3 步：补 fixture 和测试

新增 fixture：

- `fixtures/vision_events/farewell_left.json`
- `fixtures/vision_events/farewell_right.json`

新增测试建议：

- `tests/test_farewell_direction_flow.py`
  - 验证 `farewell_detected + direction=left` 时首个 look yaw 走左侧角度
  - 验证 `direction=right` 时走右侧角度

### 最小验收标准

- 用户从左侧离开时，`farewell` 首段目送角度明显偏左
- 用户从右侧离开时，`farewell` 首段目送角度明显偏右
- 如果方向未知，fallback 到当前默认方向，而不是报错

## 三、`voice_demo_tired / sigh_demo` 的真实语音触发

## 当前状态

这里也不是完全没开始：

- [`scripts/mira_realtime_voice_interaction.py`](/Users/Zhuanz/Documents/Github/Mira-Light/scripts/mira_realtime_voice_interaction.py)
  - 已支持 `comfort` 意图
  - 已支持把 `comfort` 映射到 `voice_tired`
  - 已支持把 `farewell` 映射到 `farewell_detected`

所以：

- `voice_demo_tired` 已经有一条“语音 -> 意图 -> bridge trigger”的半闭环
- `sigh_demo` 才是真正还缺事件生产器的部分

## 最小落地路线

### 第 1 步：拆成两种输入，不要混成一种

- `voice_demo_tired`
  - 来源：ASR 文本 + 简单语义分类
- `sigh_demo`
  - 来源：非语义音频事件检测

也就是说：
- “今天好累啊” 是文本意图
- “唉……” 是音频模式

它们都能归到 comfort，但事件源不应该混。

### 第 2 步：先落实 `voice_demo_tired`

这部分最省事，因为当前链路已经有了。

建议只补 3 件事：

- 给 `classify_intent(...)` 增加更稳的 tired 关键词集
- 给 `maybe_trigger_mira_action(...)` 增加 fixture 回放测试
- 在 `turn.json` / session artifact 里记录“触发了哪个 scene”

### 第 3 步：新增 `scripts/mic_event_bridge.py`

这个脚本负责：

- 读取麦克风流或离线 wav
- 做简单叹气检测
- 输出标准事件：

```json
{
  "event": "sigh_detected",
  "payload": {
    "confidence": 0.81
  }
}
```

然后由 runtime `trigger_event(...)` 路由到 `sigh_demo`。

第一版不要做复杂情绪识别，只做：

- 低频、长呼气、无明显语音音节的简单启发式检测
- fixture 驱动验证

### 第 4 步：补离线 fixture

建议新增：

- `fixtures/audio_events/voice_tired_01.wav`
- `fixtures/audio_events/voice_tired_02.wav`
- `fixtures/audio_events/sigh_01.wav`
- `fixtures/audio_events/sigh_02.wav`

以及：

- `tests/test_realtime_voice_trigger_flow.py`
- `tests/test_mic_event_bridge.py`

### 最小验收标准

- “我今天好累啊” 能稳定触发 `voice_demo_tired`
- “拜拜” 能继续稳定触发 `farewell`
- `sigh_01.wav` 能触发 `sigh_demo`
- 正常短句不会被误判成 `sigh_detected`

## 四、`multi_person_demo` 的多人目标检测

## 当前状态

[`scripts/mira_light_runtime.py`](/Users/Zhuanz/Documents/Github/Mira-Light/scripts/mira_light_runtime.py) 已经有：

- `_build_dynamic_multi_person_scene(...)`
- `trigger_event("multi_person_detected", payload)`

所以这部分也不是场景层缺，而是：

- 上游没有产出 `primaryDirection / secondaryDirection`

## 最小落地路线

### 第 1 步：先不要追求真正的多人身份跟踪

第一版只做：

- 同一帧检测到两个高置信目标
- 根据位置选：
  - `primaryDirection`
  - `secondaryDirection`

不做持久 ID，不做复杂 re-identification。

### 第 2 步：在视觉提取器里补“前二目标排序”

在 [`scripts/track_target_event_extractor.py`](/Users/Zhuanz/Documents/Github/Mira-Light/scripts/track_target_event_extractor.py) 里增加：

- 取前两大目标
- 输出：

```json
{
  "event_type": "multi_target_seen",
  "scene_hint": { "name": "multi_person_demo" },
  "tracking": {
    "target_present": true,
    "target_count": 2
  },
  "payload": {
    "primaryDirection": "left",
    "secondaryDirection": "right"
  }
}
```

### 第 3 步：桥接层只负责路由，不负责重写 scene

在 `vision_runtime_bridge.py` 里识别 `multi_target_seen` 后：

- 走 `runtime.trigger_event("multi_person_detected", payload)`

而不是自己拼动作。

### 第 4 步：先 fixture-backed，再真机

优先加：

- `fixtures/vision_events/multi_person_left_right.json`
- `fixtures/vision_events/multi_person_right_left.json`

和测试：

- `tests/test_multi_person_bridge.py`

### 最小验收标准

- 左右两人出现时，`multi_person_demo` 会先看一边，再看另一边，再回到主目标
- 只检测到一个目标时，不触发 `multi_person_demo`
- 两个人距离太近或置信度不足时，不误触发

## 五、推荐执行顺序

推荐顺序不是按场景排，而是按“上游事件最容易闭环”的顺序排：

1. `voice_demo_tired`
   - 因为已有语音链路和 intent 分类，最容易先闭环
2. `farewell` 动态离场方向
   - 因为 runtime 已有动态 scene builder，只缺事件来源
3. `track_target`
   - 因为已经有 live tracking 路径，但要继续补检测稳定性
4. `multi_person_demo`
   - 因为它对检测质量要求最高，适合放最后
5. `sigh_demo`
   - 如果要做真正可靠的非语义音频事件，通常比 `voice_demo_tired` 更难稳定

## 六、每项应新增或补齐的文件

建议最小新增集合：

- `docs/mira-light-unfinished-scene-closure-plan.md`
- `fixtures/vision_events/farewell_left.json`
- `fixtures/vision_events/farewell_right.json`
- `fixtures/vision_events/multi_person_left_right.json`
- `fixtures/audio_events/sigh_01.wav`
- `fixtures/audio_events/voice_tired_01.wav`
- `scripts/mic_event_bridge.py`
- `tests/test_farewell_direction_flow.py`
- `tests/test_multi_person_bridge.py`
- `tests/test_mic_event_bridge.py`
- `tests/test_realtime_voice_trigger_flow.py`

建议优先修改的现有文件：

- [`scripts/track_target_event_extractor.py`](/Users/Zhuanz/Documents/Github/Mira-Light/scripts/track_target_event_extractor.py)
- [`scripts/vision_runtime_bridge.py`](/Users/Zhuanz/Documents/Github/Mira-Light/scripts/vision_runtime_bridge.py)
- [`scripts/mira_realtime_voice_interaction.py`](/Users/Zhuanz/Documents/Github/Mira-Light/scripts/mira_realtime_voice_interaction.py)
- [`scripts/mira_light_runtime.py`](/Users/Zhuanz/Documents/Github/Mira-Light/scripts/mira_light_runtime.py)

## 一句话结论

这 4 个缺口当前都不应该再理解成“场景没写完”，而应该理解成：

> choreography 已经有了，真正要补的是“上游事件 -> runtime trigger / scene_context -> fixture / 测试 / 验收”的闭环。

最优先推进的是：

- 把 `voice_demo_tired` 从“半闭环”推进到“稳定可测”
- 把 `farewell` 的动态方向事件接上
- 把 `track_target` 从 surrogate choreography 真正升级成 live tracking 主路径

