# Mira Light 10 场景能力细表

这份文档把 10 个主场景整理成一张可执行的工程表，字段统一为：

- 场景名
- PDF 意图
- 代码现状
- 依赖能力
- 当前缺口
- 必改文件
- 优先级
- 验收标准

主要依据：

- `docs/Mira Light 展位交互方案3.pdf`
- `docs/mira-light-booth-scene-table.md`
- `docs/mira-light-scene-implementation-index.md`
- `docs/mira-light-booth-scene-capability-implementation-plan.md`
- `scripts/scenes.py`
- `scripts/mira_light_runtime.py`
- `scripts/vision_runtime_bridge.py`
- `scripts/mira_voice_intents.py`
- `scripts/mira_realtime_voice_interaction.py`
- `Figs/motions/*/README.md`

## 10 场景细表

| 场景名 | PDF 意图 | 代码现状 | 依赖能力 | 当前缺口 | 必改文件 | 优先级 | 验收标准 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `wake_up` | 有人来了后，先微光亮起，再起身、抖毛、伸懒腰，最后看向评委。 | choreography 已比较完整，scene 已可直接运行，motion 说明清楚，runtime 可直接触发。 | scene runner、基础 pose/profile、视觉 `target_seen` 或导演台触发、暖光渐亮。 | 缺会场级唤醒条件，容易被边缘路人误唤醒；缺 engagement zone 和 wake cooldown 的展位级调参。 | `scripts/vision_runtime_bridge.py`、`scripts/track_target_event_extractor.py`、`config/mira_light_profile.local.json` | P0 | 单人进入主展示区能稳定触发；边缘经过不乱醒；动作观感像“醒来”而不是“弹起”；结束后稳定落回 `neutral`。 |
| `curious_observe` | 先看你，再试探着靠近，害羞转开，随后再探出来并点头。 | choreography 已可运行，动作层较完整，但更偏固定导演版。 | scene runner、目标方向判断、yaw/tilt 姿态、主目标持续选择。 | 缺和真实目标方向绑定；现在观众未必看得懂它在看谁；“靠近就害羞转开”的逻辑还没和真实 hand/near-person 输入严格闭环。 | `scripts/vision_runtime_bridge.py`、`scripts/mira_light_runtime.py`、`web/app.js` | P1 | 当主目标在左/中/右时，灯的半转和探头方向一致；近距离逼近时能转开低头；场景看起来像“在观察人”，不是机械摆头。 |
| `touch_affection` | 评委把手伸来时，灯主动靠近蹭手；手移开后追一下，再回到自然位。 | scene 和动态触发骨架已存在，runtime 已支持 `touch_detected -> touch_affection`。 | 近距输入、hand-near、左右侧别、前探安全范围、暖光变化。 | 最大缺口是真实输入源；没有稳定的 hand-near/touch side 时，场景只能手动演；还缺 `touch_affection` 和 `hand_avoid` 的优先级处理。 | `scripts/vision_runtime_bridge.py`、`scripts/track_target_event_extractor.py`、`scripts/mira_light_runtime.py` | P0 | 伸手接近时能稳定触发；左手和右手接近时靠近方向合理；无人伸手时不“空蹭”；手拿开后会短暂追一下再自然回位。 |
| `cute_probe` | 呆萌地看着你，轻点头、左右找角度、抬一下中段，再做一次胆小探头。 | 这是当前最成熟的纯动作场景之一，基本可直接演。 | scene runner、pose/nudge、轻微节奏变化。 | 技术缺口不大，主要是轻随机化和一点方向感，否则多次演示会太模板化。 | `scripts/scenes.py`、`scripts/mira_light_runtime.py` | P2 | 每次演都稳定可爱；动作幅度不大不冒失；不会显得像机械测试；如果有目标方向，探头方向能稍微呼应目标。 |
| `daydream` | 工作一会后突然看向远处发呆，或慢慢打瞌睡后惊醒。 | choreography 已成熟，基本不依赖外部感知即可演。 | idle 计时、scene runner、look-away pose、被打断后的退出逻辑。 | 缺的是触发时机，不是动作；现在更像导演触发 scene，还不是自然 idle 行为。 | `scripts/vision_runtime_bridge.py`、`scripts/mira_light_runtime.py` | P2 | 无互动一段时间后能自然进入；有人重新靠近时能优雅退出；观感是“走神/打盹”，不是“卡住没反应”。 |
| `standup_reminder` | 像宠物一样蹭蹭提醒你起来，随后点头确认，被拒绝后轻轻摇头。 | 动作已写好，scene 可直接点。 | timer 或久坐来源、主持人口播上下文、scene runner。 | 缺真实“久坐来源”；如果没有上下文，场景会显得突然。 | `web/app.js`、`scripts/mira_light_runtime.py` | P2 | 主持人一引导就能自然成立；三次“蹭蹭”节奏清楚；点头和摇头逻辑完整；没有上下文时不自动乱触发。 |
| `track_target` | 评委在桌上移动书，灯头和光持续跟着书走，停时停，再动再跟。 | 这是当前最大工程项。scene fallback 已有；真实 live tracking 已存在；`tabletop_follow` 和桌面目标锁定策略也已推进。 | 摄像头、目标检测、桌面 ROI、目标锁定、tracking bridge、servo 平滑映射、operator lock。 | 仍缺“指定书本强锁定”、多桌面物体稳定仲裁、真实物体 identity、overlay；虽然已经能跑 tabletop heuristic，但还不是“展会级稳定跟书”。 | `scripts/track_target_event_extractor.py`、`scripts/vision_runtime_bridge.py`、`scripts/mira_light_runtime.py`、`web/app.js` | P0 | 同一本书移动时持续跟住；书停住 3 到 5 秒不丢；桌面有第二个矩形物体时不乱切；导演台能看出当前锁的是谁、为什么没切。 |
| `celebrate` | 打开 offer 后，音乐起，灯光多色变化，动作上下摇，最后慢慢减速收尾。 | choreography、灯效、音频、dance 已经很接近完成态。 | scene runner、音频播放、LED 模式切换、可能的网页/业务事件联动。 | 缺的是真实业务事件来源和音箱/音量策略，不是动作本身。 | `scripts/mira_light_audio.py`、`scripts/scenes.py`、`web/app.js` | P1 | 无论音乐是否在场，都能完整演完；有音乐时高潮清楚，结束后能平稳收回来；不会因为音箱问题导致整幕崩掉。 |
| `farewell` | 先目送离开的方向，再做两次慢慢点头式挥手，最后低头不舍。 | scene 已较成熟，runtime 已支持动态 `farewell_detected -> farewell`。 | 离场方向推断、`target_missing` 状态机、动态 scene context、可选语音告别映射。 | 动态 scene builder 已有，真正缺的是可靠的 `departureDirection` 事件来源，以及“只是短遮挡不是离场”的判断。 | `scripts/vision_runtime_bridge.py`、`scripts/mira_light_runtime.py`、`web/app.js` | P0 | 左侧离开时明显目送左边，右侧离开时明显目送右边；短时遮挡不误触发 farewell；结束后能顺滑衔接 `sleep`。 |
| `sleep` | 人走远后慢慢低头、降臂、做小伸懒腰，再蜷缩回睡姿，灯光渐暗。 | 动作已经很接近完成态，更多是状态机问题。 | sleep pose、fade-to-sleep 灯光、no-target timeout、与 `farewell` 的衔接。 | 缺更自然的入睡条件；如果视觉抖动或目标短丢，容易睡得太早。 | `scripts/vision_runtime_bridge.py`、`scripts/mira_light_runtime.py`、`config/mira_light_profile.local.json` | P1 | `farewell` 后能自然收场；长时间无目标才进入睡眠；不会在互动仍在继续时突然睡下去；最终姿态稳定、安全、可重复。 |

## 总结优先级

如果按“最影响展位可信度”的顺序排，建议优先处理：

1. `track_target`
2. `touch_affection`
3. `farewell`
4. `wake_up`

原因：

- 这 4 个场景最直接决定观众会不会相信 “Mira 真的感知到了你”
- 它们也是最依赖真实视觉/输入闭环的部分
- 它们一旦稳定，会反过来抬升整套展位系统的说服力

## 推荐下一步

如果这张表后面还要继续用来排开发任务，建议下一步继续拆成：

- 场景名
- 对应 trigger
- 对应 scene context
- 当前已有测试
- 缺失测试
- 最小开发包
- 真机验收动作

这样就能直接转成 issue 或 sprint 清单。
