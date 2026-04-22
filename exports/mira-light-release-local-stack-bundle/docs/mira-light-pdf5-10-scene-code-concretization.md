# Mira Light 方案5十个场景代码具体化说明

## 文档目的

这份文档专门回答两个问题：

1. 基于 [`Mira Light 展位交互方案5.pdf`](./Mira%20Light%20%E5%B1%95%E4%BD%8D%E4%BA%A4%E4%BA%92%E6%96%B9%E6%A1%885.pdf)，十个主场景现在应该怎样继续落实成代码
2. 当前代码版本里，每个场景实际上是如何实现的，哪些部分已经是现成能力，哪些部分应该改成动态输入

这份文档不是从零发明一套新场景系统。

它建立在当前已经存在的代码基础上，主要参考：

- [`../Mira_Light_Released_Version/scripts/scenes.py`](../Mira_Light_Released_Version/scripts/scenes.py)
- [`../Mira_Light_Released_Version/scripts/mira_light_runtime.py`](../Mira_Light_Released_Version/scripts/mira_light_runtime.py)
- [`../Mira_Light_Released_Version/scripts/mira_light_safety.py`](../Mira_Light_Released_Version/scripts/mira_light_safety.py)
- [`../Mira_Light_Released_Version/scripts/vision_runtime_bridge.py`](../Mira_Light_Released_Version/scripts/vision_runtime_bridge.py)
- [`./mira-light-booth-scene-capability-implementation-plan.md`](./mira-light-booth-scene-capability-implementation-plan.md)
- [`./mira-light-scene-implementation-index.md`](./mira-light-scene-implementation-index.md)

一句话说：

> 这份文档的目标不是“重新解释导演稿”，而是把 `方案5` 的导演语言，压成一份可以继续写代码、接真实硬件、接导演台、接视觉桥的具体实施说明。

## 当前代码真值边界

如果接下来还要继续推进这十个场景，建议保持下面这个真值顺序不变：

1. `方案5` 负责说明“评委应该感受到什么”
2. `scenes.py` 负责说明“程序里怎么编排这段 choreography”
3. `mira_light_runtime.py` 负责说明“这些步骤如何被安全地执行”
4. `vision_runtime_bridge.py` 负责说明“哪些场景应该被动态事件驱动”
5. 后续总线舵机适配层负责说明“最终如何发到真实关节”

也就是说，当前最应该做的不是推翻 `scenes.py`，而是继续沿用下面这套结构：

```text
scene id
-> build_scene(scene_name, scene_context)
-> BoothController.run_step(...)
-> MiraLightSafetyController
-> device output
```

## 十个场景应该怎么继续落代码

先把十个场景按“应该继续保持静态 choreography，还是应该改成动态驱动”分成三类。

### A. 应继续保持静态 choreography

- `wake_up`
- `cute_probe`
- `daydream`
- `standup_reminder`
- `celebrate`
- `sleep`

这些场景的核心价值在于：

- 节奏
- 停顿
- 情绪转折
- 灯光与动作的配合

也就是说，这些场景最重要的是“编排”而不是“感知输入”。

### B. 以静态 choreography 为主，但应支持上下文

- `curious_observe`

这个场景当前固定按“左前方评委”写是合理的，但中期最好支持：

- `targetDirection`
- `targetDistanceBand`

这样导演台或视觉桥可以让“好奇”朝向真实来人。

### C. 必须走动态输入

- `touch_affection`
- `track_target`
- `farewell`

这三个场景的灵魂不在“动作本身”，而在“动作和外部人的关系”：

- `touch_affection` 依赖手的位置
- `track_target` 依赖目标的实时位置
- `farewell` 依赖评委离开的方向

所以这三者不应该长期停留在纯固定 choreography。

## 实现总原则

### 1. Scene 仍然用现有原语

建议继续使用：

- `pose(...)`
- `absolute(...)`
- `nudge(...)`
- `led(...)`
- `delay(...)`
- `comment(...)`
- `audio(...)`
- `action(...)`

不要把 scene 直接改写成底层舵机协议字符串。

### 2. 动态能力优先通过 `scene_context` 或 runtime 输入接入

建议遵循下面这条线：

- 静态主场景：继续由 `SCENES[...]` 定义
- 动态变体：优先由 `build_scene(...)` 根据 `scene_context` 生成
- 实时连续控制：优先由 runtime 的专门入口处理，而不是在 `steps` 里硬写

这正是当前：

- `farewell`
- `track_target`

已经采用的思路。

### 3. 四关节分工保持稳定

当前最适合继续沿用的语义是：

| 逻辑关节 | 工程语义 | 常见职责 |
| --- | --- | --- |
| `servo1` | 底座转向 | 左右注意力、看向人、目送、跟随 |
| `servo2` | 下臂抬升 | 起身、降臂、整体抬高或压低 |
| `servo3` | 前段关节 / 中间关节前探与抬升 | 探头、回缩、前顶、工作位 |
| `servo4` | 灯头俯仰 / 微表情 | 点头、低头、抬头、害羞、可爱感 |

后续真实硬件适配时，最好保留这层语义不变。

### 4. 场景实现时先确定“主关节”

每个场景都应该先确定：

- 哪 1 到 2 个关节是主角
- 哪些只是辅助

不要让四个关节在每一段里都抢戏。

## 十个场景逐项具体化

## 1. `wake_up`

### `方案5` 的导演目标

- 从蜷缩状态醒来
- 微光亮起
- 慢慢起身
- 做一次伸懒腰
- 回落时抖两下
- 最后看向评委

### 当前代码入口

- scene id：`wake_up`
- 文件：[`../Mira_Light_Released_Version/scripts/scenes.py`](../Mira_Light_Released_Version/scripts/scenes.py)

### 当前实现结构

当前代码已经基本符合 `方案5`：

1. `pose("sleep")` 进入睡姿
2. 多段 `led("solid")` 与 `led("breathing")` 完成“睁眼”
3. `pose("wake_half")` 进入半醒姿态
4. 两段 `absolute(...)` 完成升高和后仰
5. 回到正常高度后，用多段 `nudge(servo1, servo4)` 做“抖毛”
6. 最后 `absolute(servo1=96, ...)` 看向评委

### 主关节设计

- 主关节：`servo2 + servo3`
- 辅关节：`servo4`
- `servo1` 只负责最后轻微定向和抖毛时的小摆

### 继续实现建议

- 保持为静态 choreography，不需要改成动态 builder
- 如果要接真实硬件，优先校准：
  - `sleep`
  - `wake_half`
  - `wake_high`
  - `neutral`
- 如果要精修代码，可以给关键 `absolute(...)` 增加显式 `move_ms`

### 最关键的代码边界

- `wake_up` 的“情绪感”主要来自 `delay` 和灯光节奏
- 不要把它简化成一次 `stretch` 预设动作

## 2. `curious_observe`

### `方案5` 的导演目标

- 先看向评委
- 靠近一点
- 缓慢摇头一次
- 更靠近
- 转开、低头、害羞
- 再探出来
- 点头
- 对方继续靠近时再害羞

### 当前代码入口

- scene id：`curious_observe`
- 文件：[`../Mira_Light_Released_Version/scripts/scenes.py`](../Mira_Light_Released_Version/scripts/scenes.py)

### 当前实现结构

当前 scene 已经把“好奇又害怕”的完整路径拆开了：

1. `neutral` 起步
2. `absolute(servo1=94...)` 先注意到你
3. `absolute(servo1=100...)` 再靠近一点
4. 用 `nudge(servo1, servo4)` 做缓慢摇头
5. `absolute(servo1=82, servo4=100)` 做转开与低头
6. 用 `nudge(servo4)` 做上下轻动
7. 再次探出来，看向你
8. 再做一次点头
9. 最后以“又有点怕”为结尾

### 主关节设计

- 主关节：`servo1 + servo4`
- 辅关节：`servo3`
- `servo2` 只做轻微整体高度支撑

### 继续实现建议

- 现阶段继续保留固定版是合理的
- 下一步建议新增 `_build_dynamic_curious_scene(scene_context)`：
  - `targetDirection`
  - `targetNear`
- 动态化时，只改“朝向”和“靠近方向”，不要动整体节奏骨架

### 最关键的代码边界

- 这个 scene 的重点是“停顿和犹豫”
- 不能简单理解成“转头 + 点头”

## 3. `touch_affection`

### `方案5` 的导演目标

- 主动靠近手
- 在手掌下轻蹭
- 灯光变暖
- 手拿开后追一下
- 回到自然照明方向

### 当前代码入口

- scene id：`touch_affection`
- 文件：[`../Mira_Light_Released_Version/scripts/scenes.py`](../Mira_Light_Released_Version/scripts/scenes.py)

### 当前实现结构

当前代码已经把动作拆成四段：

1. `neutral`
2. 靠近手
3. 往下送到手掌下
4. 用一组小幅 `absolute(...)` 组合成上下左右轻蹭
5. 手拿开后追一下
6. 回到自然照明位和 `neutral`

### 主关节设计

- 主关节：`servo3 + servo2`
- 辅关节：`servo1`
- `servo4` 负责小幅可爱感，不应过大

### 继续实现建议

这是最适合下一个阶段动态化的 scene。

建议新增：

- `_build_dynamic_touch_affection_scene(scene_context)`

建议支持的上下文字段：

```json
{
  "handDirection": "left|center|right",
  "handDistanceBand": "near|mid",
  "touchConfidence": 0.92
}
```

动态化时推荐只改三件事：

- 靠近时的 `servo1`
- 下送幅度
- 追手时的最终方向

不要把“蹭”的骨架也完全改掉。

### 最关键的代码边界

- 这个 scene 不能仅仅靠 `nudge` 抖动实现
- 真正的亲近感来自：
  - 前探
  - 下送
  - 小范围上下左右磨蹭

## 4. `cute_probe`

### `方案5` 的导演目标

- 呆萌看着你
- 轻点头
- 底座左右找角度
- 中间关节先上再下
- 探头
- 缩回
- 再探出去

### 当前代码入口

- scene id：`cute_probe`
- 文件：[`../Mira_Light_Released_Version/scripts/scenes.py`](../Mira_Light_Released_Version/scripts/scenes.py)

### 当前实现结构

当前 scene 基本已经是 `方案5` 的逐项翻译：

1. 轻点头
2. 左右找角度
3. `servo3` 上抬再下放
4. 慢慢探头
5. 突然缩回
6. 再慢慢探出去

### 主关节设计

- 主关节：`servo3 + servo4`
- 辅关节：`servo1`

### 继续实现建议

- 继续保持静态 choreography 即可
- 不需要优先做动态版
- 如果接真实总线舵机，优先验证：
  - 探头是否过冲
  - 缩回是否显得像卡顿

### 最关键的代码边界

- 它的“可爱”不是靠大幅度，而是靠：
  - 小点头
  - 小停顿
  - 胆小探头

## 5. `daydream`

### `方案5` 的导演目标

- 工作中突然抬头看向奇怪方向
- 停住 3 到 4 秒
- 快速回神
- 另一种版本是打瞌睡，越低越低，然后弹回来

### 当前代码入口

- scene id：`daydream`
- 文件：[`../Mira_Light_Released_Version/scripts/scenes.py`](../Mira_Light_Released_Version/scripts/scenes.py)

### 当前实现结构

当前代码把两种版本都串在一个 scene 里：

1. 走神看远处
2. 长时间 hold
3. 快速回到 `neutral`
4. 再执行打盹版本
5. 逐步下沉
6. 突然弹回

### 主关节设计

- 主关节：`servo1 + servo4`
- 辅关节：`servo2`

### 继续实现建议

- scene 本体保持静态 choreography
- 中期建议由 idle scheduler 触发，而不是手动触发
- 如果要细化代码，建议把它拆成两个 helper：
  - `daydream_lookaway_variant`
  - `daydream_sleepy_variant`

### 最关键的代码边界

- 这个 scene 的主角是“hold”
- 如果没有 3 到 4 秒的停顿，就不会像走神

## 6. `standup_reminder`

### `方案5` 的导演目标

- 面向评委
- 灯臂往前
- 先轻轻蹭，后面加大
- 往后退一点再蹭
- 评委问“是要我起来吗”
- Mira 点头两次
- 评委说不要，Mira 轻轻摇头

### 当前代码入口

- scene id：`standup_reminder`
- 文件：[`../Mira_Light_Released_Version/scripts/scenes.py`](../Mira_Light_Released_Version/scripts/scenes.py)

### 当前实现结构

当前 scene 已经被写成很明确的三段 bump：

1. 转向评委并前送
2. 三轮“埋头 -> 顶起 -> 后退”
3. 双点头
4. 轻摇头
5. 回中位

### 主关节设计

- 主关节：`servo3 + servo2`
- 辅关节：`servo4`
- `servo1` 只负责轻摇头和面向评委

### 继续实现建议

- 继续保持静态 choreography
- 真正动态化的不是动作，而是触发来源
- 后续只需要把久坐事件接到：
  - 导演台
  - 电脑端计时器
  - bridge 事件入口

### 最关键的代码边界

- “蹭蹭”必须是完整的前后节奏
- 不能退化成单轴高频抖动

## 7. `track_target`

### `方案5` 的导演目标

- 评委移动桌上的书
- 灯头压低并持续跟随
- 评委停，Mira 也停
- 评委再动，Mira 再跟

### 当前代码入口

- fallback scene：[`../Mira_Light_Released_Version/scripts/scenes.py`](../Mira_Light_Released_Version/scripts/scenes.py)
- 实时实现：[`../Mira_Light_Released_Version/scripts/mira_light_runtime.py`](../Mira_Light_Released_Version/scripts/mira_light_runtime.py)
- 事件桥：[`../Mira_Light_Released_Version/scripts/vision_runtime_bridge.py`](../Mira_Light_Released_Version/scripts/vision_runtime_bridge.py)

### 当前实现结构

这里要明确区分两条路径。

#### 路径 A：scene fallback

`scenes.py` 里仍然保留了一版 `left -> center -> right` 的 surrogate choreography，作用是：

- 排练
- 无视觉时的 fallback
- 展示节奏

#### 路径 B：真实 tracking

runtime 现在已经支持：

- `apply_tracking_event(...)`
- 根据 `yaw_error_norm / pitch_error_norm / lift_intent / reach_intent` 计算四关节目标
- 对目标做平滑
- 通过安全层执行

### 主关节设计

- 主关节：`servo1 + servo4`
- 辅关节：`servo2 + servo3`

### 继续实现建议

- 这个场景不应该再继续加重 `SCENES["track_target"]` 的固定 choreography
- 继续推进的重点应该放在：
  - `track_target_event_extractor.py`
  - `vision_runtime_bridge.py`
  - `apply_tracking_event(...)`

也就是说：

- `scene` 负责进入和退出 tracking 模式
- `runtime` 负责连续更新关节

### 最关键的代码边界

- `track_target` 的核心不是“预写 5 个位置”
- 而是“持续把实时视觉误差转成平滑关节命令”

## 8. `celebrate`

### `方案5` 的导演目标

- offer 被打开
- Mira 感知到开心
- 蓝牙音箱放音乐
- 整体往上摇
- 整体往下摇
- 灯光五颜六色
- 音乐停后减速
- 左右摇头和身体转一下

### 当前代码入口

- scene id：`celebrate`
- 文件：[`../Mira_Light_Released_Version/scripts/scenes.py`](../Mira_Light_Released_Version/scripts/scenes.py)
- 音频执行：[`../Mira_Light_Released_Version/scripts/audio_cue_player.py`](../Mira_Light_Released_Version/scripts/audio_cue_player.py)

### 当前实现结构

当前 scene 已经非常接近 `方案5`：

1. 暖光起手
2. 上摇
3. 左上回中、右上回中
4. 下摇
5. 左下回中、右下回中
6. `rainbow_cycle`
7. `audio("dance.mp3")`
8. `action("dance")`
9. 减速收尾
10. 左右摇头、身体转一下
11. 回暖光和 `neutral`

### 主关节设计

- 主关节：`servo2 + servo3`
- 辅关节：`servo1 + servo4`

### 继续实现建议

- 继续保持静态 choreography
- 下一步重点不是改动作本身，而是接业务事件：
  - offer 打开
  - 音乐兜底
  - 导演台一键触发

### 最关键的代码边界

- `celebrate` 的主价值已经不是“能不能动”
- 而是“音频、灯光、动作能不能稳定联动”

## 9. `farewell`

### `方案5` 的导演目标

- 评委离开时先目送
- 再用灯头慢慢点头两下，像挥手说拜拜
- 然后微微低头
- 最后再抬头看一眼，再睡觉

### 当前代码入口

- scene builder：[`../Mira_Light_Released_Version/scripts/scenes.py`](../Mira_Light_Released_Version/scripts/scenes.py)
- runtime 场景上下文：[`../Mira_Light_Released_Version/scripts/mira_light_runtime.py`](../Mira_Light_Released_Version/scripts/mira_light_runtime.py)
- 视觉桥方向信息：[`../Mira_Light_Released_Version/scripts/vision_runtime_bridge.py`](../Mira_Light_Released_Version/scripts/vision_runtime_bridge.py)

### 当前实现结构

`farewell` 已经不再是纯静态 scene。

它现在通过 `build_scene("farewell", scene_context)` 动态生成：

1. `neutral`
2. 朝离场方向的 `farewell_look`
3. 两轮慢点头式挥手
4. 朝同方向的 `farewell_bow`
5. 回到 `neutral`

### 主关节设计

- 主关节：`servo1 + servo4`
- 辅关节：`servo2`

### 继续实现建议

基于 `方案5`，下一步最自然的补充是：

- 在最后 bow 之后，增加一次“又抬头看一眼”
- 然后再接 `sleep`

也就是说，`farewell` 现在已经完成了动态方向版，接下来更适合补：

- `farewell -> sleep` 自动衔接
- “回头再看一眼”这一步

### 最关键的代码边界

- 这个 scene 已经不应该再改回固定版
- 它就是动态场景的标准范例

## 10. `sleep`

### `方案5` 的导演目标

- 评委走远后慢慢低头
- 灯臂缓缓降下去
- 先做一个小伸懒腰
- 再蜷缩起来
- 灯光逐步变暗
- 回到等待下一个评委的状态

### 当前代码入口

- scene id：`sleep`
- 文件：[`../Mira_Light_Released_Version/scripts/scenes.py`](../Mira_Light_Released_Version/scripts/scenes.py)

### 当前实现结构

当前 scene 已经按 `方案5` 的逻辑落成：

1. `neutral`
2. 慢慢低头
3. 灯臂缓缓降下去
4. 先做一个小舒展
5. `sleep_ready`
6. `sleep`
7. `fade_to_sleep(...)`

### 主关节设计

- 主关节：`servo2 + servo3`
- 辅关节：`servo4`

### 继续实现建议

- 继续保持静态 choreography
- 下一步重点是自动触发策略，而不是动作本身：
  - `no_target` grace timeout
  - `session_end`
  - 导演台 stop-to-sleep

### 最关键的代码边界

- `sleep` 不应该像断电
- 必须保留“先收回，再慢慢熄灯”的过程

## 这十个场景分别应该改哪里

如果要继续写代码，最建议按下面这张表推进。

| 场景 | 主要继续修改的文件 | 最关键的下一步 |
| --- | --- | --- |
| `wake_up` | `scenes.py` | 真机校准 `sleep / wake_half / wake_high / neutral` |
| `curious_observe` | `scenes.py` | 做方向上下文版 builder |
| `touch_affection` | `scenes.py` + `bridge/runtime` | 做 `handDirection` 动态版 |
| `cute_probe` | `scenes.py` | 只做真机节奏微调 |
| `daydream` | `scenes.py` + idle 调度 | 接空闲调度策略 |
| `standup_reminder` | `bridge/runtime` | 接久坐事件来源 |
| `track_target` | `vision_runtime_bridge.py` + `mira_light_runtime.py` | 稳定实时 tracking，而不是加固定 step |
| `celebrate` | `scenes.py` + 音频入口 | 接 offer 事件和音频兜底 |
| `farewell` | `scenes.py` + `vision_runtime_bridge.py` | 补“再看一眼”与自动接 `sleep` |
| `sleep` | `vision_runtime_bridge.py` + runtime | 补自动入睡策略 |

## 一条最重要的落实顺序

如果要继续把 `方案5` 落深，我建议顺序固定成这样：

1. 保持 `wake_up / celebrate / sleep` 这类情绪型场景继续走静态 choreography
2. 让 `farewell` 保持动态 builder，并补齐“再看一眼”
3. 让 `touch_affection` 进入真实方向输入版
4. 把 `track_target` 真正做成会场级稳定实时能力

原因很简单：

- 纯编排场景已经很成熟，不值得推翻重来
- 真正会决定“它像不像真的在回应人”的，是 `touch_affection / track_target / farewell`

## 结论

基于当前代码版本，`方案5` 的十个主场景其实已经不是“有没有代码”的问题，而是“哪些场景应该继续作为 choreography，哪些场景应该升级成动态输入驱动”的问题。

当前最合理的划分是：

- 编排型场景继续留在 `SCENES`
- 方向型场景继续收敛到 `build_scene(scene_context)`
- 实时型场景继续收敛到 runtime 专门入口

如果继续按这条线推进，现有的：

- `scenes.py`
- `mira_light_runtime.py`
- `vision_runtime_bridge.py`
- 安全层
- 导演台

都不需要推翻，只需要继续把三个“真正依赖外部输入”的场景做深。
