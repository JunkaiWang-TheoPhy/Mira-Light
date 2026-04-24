# Release Scene Bundles

## 目的

这份文档说明发布版当前新增的 scene bundle 机制。

它解决的问题是：

- 不能再只靠 `ready` / `show experimental` 两档切换场景
- 需要把“最小可演版本”和“完整展位版本”拆开
- 需要把方案 3 里提到的补充互动场景收进一个明确的发布层级

## 配置文件

当前 bundle 定义保存在：

- [`../config/release_scene_bundles.json`](../config/release_scene_bundles.json)

runtime 会默认读取这份配置。

## 当前 bundle 列表

### `minimal`

- 目标：最小可跑、最稳
- 当前场景：
  - `cute_probe`
  - `daydream`
  - `farewell`

这组 bundle 对应当前 release 的默认行为，尽量保持和原来的 ready-only mode 一致。

### `booth_core`

- 目标：展位主秀 MVP
- 当前场景：
  - `wake_up`
  - `curious_observe`
  - `touch_affection`
  - `track_target`
  - `celebrate`
  - `farewell`
  - `sleep`

这组更接近导演层的主秀版本，适合完整演练。

### `booth_extended`

- 目标：十个主场景的完整排练包
- 当前场景：
  - `wake_up`
  - `curious_observe`
  - `touch_affection`
  - `cute_probe`
  - `daydream`
  - `standup_reminder`
  - `track_target`
  - `celebrate`
  - `farewell`
  - `sleep`

### `sensor_demos`

- 目标：感知类补充互动
- 当前场景：
  - `track_target`
  - `sigh_demo`
  - `multi_person_demo`
  - `voice_demo_tired`

这组更接近方案 3 里的补充互动方向，不建议直接当默认主秀包。

## 使用方法

### 默认行为

如果不显式设置 bundle，runtime 会读取配置里的默认 bundle：

```text
minimal
```

### 指定 bundle

```bash
export MIRA_LIGHT_SCENE_BUNDLE=booth_core
bash scripts/start_local_stack.sh
```

或者：

```bash
export MIRA_LIGHT_SCENE_BUNDLE=sensor_demos
bash tools/mira_light_bridge/start_bridge.sh
```

### 临时放开全部场景

如果你不设置 `MIRA_LIGHT_SCENE_BUNDLE`，但设置：

```bash
export MIRA_LIGHT_SHOW_EXPERIMENTAL=1
```

runtime 会回到“放开全部场景”的旧模式。

## 和 readiness 的关系

需要特别注意：

- `readiness` 仍然保留
- 但 bundle 可以显式放行某些 `tuning` / `sensor-needed` 场景

也就是说，当前机制变成了：

```text
默认看 scene bundle
没有 bundle 时再回退到 readiness / show experimental
```

## 推荐怎么选

### 第一次接手 release

优先：

```text
minimal
```

### 做完整展位彩排

优先：

```text
booth_core
```

### 做十个主场景的技术排练

优先：

```text
booth_extended
```

### 做摄像头 / 麦克风 / 补充互动演示

优先：

```text
sensor_demos
```

## 为什么这比只看 `ready` 更合理

因为当前发布版已经不是“只有动作代码”的阶段了。

像下面这些场景是否该显示，取决于的不是一个抽象 readiness，而是现场到底准备了什么：

- `track_target`
- `celebrate`
- `sigh_demo`
- `multi_person_demo`
- `voice_demo_tired`

bundle 能把：

- 主秀必演版本
- 完整排练版本
- 感知补充版本

分得更清楚。

## 一句话总结

scene bundle 的目标不是取代 `readiness`，而是让发布版开始具备：

> “按交付场景切换场景可见性”的能力。
