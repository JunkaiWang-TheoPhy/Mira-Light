# Mira Light 十个主场景代码索引包

生成时间：`2026-04-24`

这个导出包把 `Mira Light` 十个主场景最关键的代码位置、动态/静态属性、以及主要触发方式整理到一处，方便：

- 快速接手代码
- 给协作者做场景定位
- 给导演台/桥接层/视觉链路做联调参考

## 包内文件

- `README.md`
  当前说明文档，含十个主场景对照表
- `scene_mapping.csv`
  适合导入表格工具继续整理
- `scene_mapping.json`
  适合程序化消费或继续生成其它文档

## 十个主场景对照表

| 场景 ID | 中文名 | 主编排代码 | 运行时扩展 | Motion Script | 动态/静态 | 主要触发方式 |
| --- | --- | --- | --- | --- | --- | --- |
| `wake_up` | 起床 | `scripts/scenes.py:187` `scripts/scenes.py:574` | 无额外动态 builder | `Motions/01_wake_up/scene_script.py:14` | 静态 choreography | 终端 `scripts/booth_controller.py`；导演台 `/api/run/wake_up`；bridge `/v1/mira-light/run-scene`；视觉 `target_seen -> wake_up` |
| `curious_observe` | 好奇你是谁 | `scripts/scenes.py:198` `scripts/scenes.py:623` | `scripts/mira_light_runtime.py:1226` | `Motions/02_curious_observe/scene_script.py:14` | 动态 builder | 终端/导演台/bridge `run-scene`；视觉 `scene_hint=curious_observe`；runtime 会按 `scene_context` 生成动态版本 |
| `touch_affection` | 摸一摸 | `scripts/scenes.py:209` `scripts/scenes.py:689` | `scripts/mira_light_runtime.py:1408` | `Motions/03_touch_affection/scene_script.py:14` | 动态 builder | 终端/导演台/bridge `run-scene`；事件 `touch_detected`/`hand_near` -> `trigger_event(...)`；视觉 hand cue 可触发 |
| `cute_probe` | 卖萌 | `scripts/scenes.py:231` `scripts/scenes.py:757` | 无额外动态 builder | `Motions/04_cute_probe/scene_script.py:14` | 静态 choreography | 终端/导演台/bridge `run-scene` |
| `daydream` | 发呆 | `scripts/scenes.py:242` `scripts/scenes.py:799` | 无额外动态 builder | `Motions/05_daydream/scene_script.py:14` | 静态 choreography | 终端/导演台/bridge `run-scene` |
| `standup_reminder` | 久坐检测：蹭蹭 | `scripts/scenes.py:253` `scripts/scenes.py:837` | 无额外动态 builder | `Motions/06_standup_reminder/scene_script.py:14` | 静态 choreography | 终端/导演台/bridge `run-scene`；当前主仓里没有独立 `trigger_event` 映射 |
| `track_target` | 追踪 | `scripts/scenes.py:264` `scripts/scenes.py:900` | `scripts/mira_light_runtime.py:1602` | `Motions/07_track_target/scene_script.py:14` | 混合：静态 fallback + 实时 tracking | 终端/导演台/bridge `run-scene` 可跑 fallback；视觉链主路径是 `vision_runtime_bridge.py -> apply_tracking_event(...)` |
| `celebrate` | 跳舞模式 | `scripts/scenes.py:275` `scripts/scenes.py:935` | 无额外动态 builder | `Motions/08_celebrate/scene_script.py:14` | 静态 choreography | 终端/导演台/bridge `run-scene` |
| `farewell` | 挥手送别 | `scripts/scenes.py:286` `scripts/scenes.py:1007` | `scripts/mira_light_runtime.py:1369` | `Motions/09_farewell/scene_script.py:14` | 动态 builder | 终端/导演台/bridge `run-scene`；事件 `farewell_detected` -> `trigger_event(...)`；视觉 `target_lost` 可路由到动态送别 |
| `sleep` | 睡觉 | `scripts/scenes.py:297` `scripts/scenes.py:1045` | 无额外动态 builder | `Motions/10_sleep/scene_script.py:14` | 静态 choreography | 终端/导演台/bridge `run-scene`；视觉丢目标超时后可进入 `sleep` |

## 关键运行入口

- `scripts/scenes.py:573`
  十个主场景的 choreography 真值
- `scripts/mira_light_runtime.py:1866`
  `start_scene(...)`，所有场景统一启动入口
- `scripts/mira_light_runtime.py:1892`
  `trigger_event(...)`，事件驱动入口
- `scripts/mira_light_runtime.py:1602`
  `apply_tracking_event(...)`，实时 tracking 入口
- `scripts/booth_controller.py:45`
  终端执行入口
- `scripts/console_server.py:417`
  导演台 `/api/run/<scene>` 转发到 bridge
- `tools/mira_light_bridge/bridge_server.py:310`
  bridge `/v1/mira-light/run-scene`

## 触发方式说明

- `run-scene`
  适合静态 choreography 场景。典型入口是终端、导演台和 bridge API。
- `trigger_event`
  适合“由感知事件驱动的场景”，例如 `touch_affection`、`farewell`。
- `apply_tracking_event`
  适合实时连续控制，当前主要对应 `track_target`。

## 当前最值得注意的 3 个特殊场景

- `curious_observe`
  不是纯静态版。runtime 会根据 `ownerDirection`、`judgeDirection`、`ownerFaceFound` 等上下文生成动态版本。
- `touch_affection`
  当前已经支持按左/中/右来手方向生成动态 scene，但“蹭手”本体仍以 choreography 为主。
- `track_target`
  这是最特殊的一幕。`scripts/scenes.py` 里那版更像排练 fallback，真正的会场级跟随应该走视觉事件和 runtime 的实时 tracking 入口。

## 相关参考文件

- `Motions/README.md:1`
  十个主场景的 motion script 索引
- `docs/mira-light-scene-implementation-index.md:1`
  主场景实现说明
- `docs/mira-light-pdf5-10-scene-code-concretization.md:1`
  从导演稿到代码的具体化说明

