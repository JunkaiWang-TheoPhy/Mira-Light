# Mira Light 展位场景能力实施计划书

## 文档目的

这份文档把当前仓库已经有的场景、runtime、视觉、音频、导演台、OpenClaw 与 bridge 能力，整理成一份真正可执行的实施计划书。

它重点回答 4 个问题：

1. 为了实现当前展位方案里的场景，已经可以直接调用哪些功能
2. 哪些功能必须优先加强，才能在会场里稳定工作
3. 哪些功能还需要补充，才能把方案里的体验真正做出来
4. 应该按什么顺序推进，才最有性价比

这份文档不替代动作真值文档。

当前真值顺序仍然建议保持为：

1. `Mira Light 展位交互方案2.pdf`
2. `scripts/scenes.py`
3. `Mira Light 展位交互方案3.pdf`
4. `Mira Light 展位交互方案5.pdf`

说明：

- `方案2` 仍然是动作与 choreography 的主真值
- `方案3` 更偏展位导演感和讲述感
- `方案5` 更偏“评委感受到它真的在感知你”的价值主张和扩展互动方向

## 当前工作目标

当前阶段的目标不是继续增加更多概念场景，而是把已经存在的场景能力做成：

```text
可触发
-> 可联调
-> 可重复演示
-> 可在嘈杂人多的会场中稳定运行
```

对这次展位项目来说，最重要的不是“场景数量”，而是这 3 件事：

- 它真的看见了你
- 它真的会回应你
- 它能稳定演完一整轮

## 会场约束

这份计划默认你们是在“嘈杂、人多、环境复杂、操作员需要随时兜底”的会场条件下工作。

所以所有后续实现都应该遵守下面这些原则：

- 主触发优先级：视觉 > 触摸 / 近距输入 > 导演台 / Claw > 开放式语音
- 开放式麦克风不应作为主链路
- 多人环境里必须有“主目标选择”逻辑
- 所有关键链路都需要 fallback
- 每个演示段落都要能被导演台一键打断并回到 `neutral` 或 `sleep`

## 当前已经可以直接调用的能力

## 1. 场景执行能力

当前场景系统已经具备：

- 十个主场景的 `SCENE_META`
- 十个主场景的 `SCENES`
- 三个补充场景：
  - `sigh_demo`
  - `multi_person_demo`
  - `voice_demo_tired`

对应文件：

- `scripts/scenes.py`
- `scripts/mira_light_runtime.py`

这意味着以下能力已经存在：

- 场景级执行
- `host_line`
- `operatorCue`
- `fallbackHint`
- `cueMode`
- 异步 / 同步运行
- 场景日志
- 中断与停止
- 自动恢复姿态

## 2. 动态场景上下文能力

runtime 当前已经支持把感知结果传成 `scene_context`，并动态生成部分场景：

- 动态 `farewell`
- 动态 `touch_affection`
- 动态 `multi_person_demo`

对应入口：

- `scripts/mira_light_runtime.py`

这意味着：

- 不需要在 `scenes.py` 里硬复制 `farewell_left / farewell_right`
- 不需要把所有“动态场景”都拆成很多静态 scene
- 可以统一走 “感知 -> 标准事件 -> scene_context -> runtime 组装场景”

## 3. 实时 tracking 能力

当前 repo 已经不是只有静态 `track_target` choreography。

已经存在的能力包括：

- 相机帧接收
- 视觉事件提取
- `vision.latest.json` / `vision.events.jsonl`
- 视觉桥接到 runtime
- `runtime.apply_tracking_event(...)`
- 四舵机平滑跟随控制

对应文件：

- `scripts/track_target_event_extractor.py`
- `scripts/vision_runtime_bridge.py`
- `scripts/mira_light_runtime.py`
- `scripts/run_mira_light_vision_stack.sh`
- `scripts/run_mira_light_live_follow_demo.sh`

这意味着：

- `track_target` 已经可以走真实 tracking 更新
- choreography 版本现在更适合当 fallback 或排练路径

## 4. 音频与 TTS 能力

当前音频不再只是占位。

已经存在：

- scene 内 `audio(...)` 步骤
- 主持人口播 `host_line` 的 TTS 播报能力
- `celebrate` 的音乐播放
- `farewell` / `sigh_demo` / `voice_demo_tired` 的 TTS
- 本地蓝牙音箱播放链路

对应文件：

- `scripts/scenes.py`
- `scripts/mira_light_runtime.py`
- `scripts/mira_light_audio.py`
- `docs/openclaw-local-audio-tts.md`

## 5. 统一触发入口

当前 bridge / runtime 已经有统一事件入口：

- `touch_detected`
- `sigh_detected`
- `voice_tired`
- `multi_person_detected`
- `farewell_detected`

对应文件：

- `tools/mira_light_bridge/bridge_server.py`
- `scripts/mira_light_runtime.py`

这意味着上层系统可以统一发：

```json
{
  "event": "voice_tired",
  "payload": {
    "transcript": "今天好累啊",
    "cueMode": "director"
  }
}
```

而不需要直接耦合某个具体 scene 名称。

## 6. 导演台与校准能力

当前导演台已经具备：

- 主场景运行
- 运行状态查看
- farewell 方向选择
- runtime 状态显示
- profile 查看
- pose 捕获
- servo meta 编辑
- stop to neutral / stop to sleep

对应文件：

- `web/app.js`
- `web/index.html`
- `scripts/console_server.py`
- `tools/mira_light_bridge/bridge_server.py`

## 当前需要调用的现有功能

如果要把目前方案里的主场景真正跑起来，建议直接基于下面这些现有能力组合，而不是重新造新系统。

### A. 基础演示主链路

建议调用：

- `runtime.start_scene(...)`
- `/v1/mira-light/run-scene`
- 导演台 `/api/run/<scene>`

适用场景：

- `wake_up`
- `curious_observe`
- `cute_probe`
- `daydream`
- `standup_reminder`
- `celebrate`
- `sleep`

### B. 感知触发链路

建议调用：

- `runtime.trigger_event(...)`
- `/v1/mira-light/trigger`

适用场景：

- `touch_affection`
- `sigh_demo`
- `voice_demo_tired`
- `multi_person_demo`
- `farewell`

原因：

- 这类场景更适合由“标准事件”驱动
- 不适合让上层直接耦合 choreography

### C. 视觉实时闭环链路

建议调用：

- `track_target_event_extractor.py`
- `vision_runtime_bridge.py`
- `runtime.apply_tracking_event(...)`

适用场景：

- `track_target`
- `farewell`
- `multi_person_demo`
- 未来的 `touch_affection` 视觉版

### D. 音频播报链路

建议调用：

- scene 内 `audio(...)`
- runtime 的 speak / cue-host TTS
- 本地蓝牙音箱播放脚本

适用场景：

- `celebrate`
- `farewell`
- `sigh_demo`
- `voice_demo_tired`
- 主持人口播统一 cue

### E. 导演兜底链路

建议调用：

- 导演台运行 scene
- `operator/stop-to-neutral`
- `operator/stop-to-sleep`
- mock / dry-run / replay

适用范围：

- 所有会场演示

原因：

- 展位现场一定需要人工接管能力
- 导演兜底不应是临时行为，而应是系统设计的一部分

## 当前必须优先加强的功能

下面这些不是“锦上添花”，而是当前最直接影响展位效果的核心短板。

## 1. 真灯联通性与长期在线性

当前 repo 文档已经明确：真实设备联通性仍是关键短板。

必须加强：

- 真实灯 IP 与网络路径确认
- 本机到灯的 `/status` 可达性
- runtime / bridge 到灯的可靠调用
- 灯掉线时的清晰错误提示

如果这件事不闭环，后面的 scene、视觉、导演台都只能算半成品。

## 2. `track_target` 稳定性

这是当前最重要的技术加强项。

必须加强：

- 更稳定的 detector
- 目标保持
- 短时丢失 grace period
- 主目标锁定
- 会场 ROI / engagement zone
- 多人环境下的目标过滤
- 跟随参数调优

目前的核心现实问题不是“能不能看到图”，而是：

```text
能不能在会场里持续盯住对的人，而不是一会儿看人、一会儿丢失、一会儿被路人抢走
```

## 3. 导演台可观测性

当前导演台已经能跑 scene，但还不够“现场操作友好”。

必须加强：

- 当前最后一条 vision event
- 当前 `target_present`
- 当前 `target_count`
- 当前 `selected_target`
- 当前 `horizontal_zone / vertical_zone`
- 当前 `distance_band`
- 当前 detector / confidence
- 当前 tracking 是否在 live 模式

如果导演台看不到这些，现场一旦卡住就很难判断到底是：

- 摄像头没图
- detector 失效
- bridge 没更新
- runtime 没接住
- 灯没有执行

## 4. pose / servo profile 真机固化

当前 profile 能看、能写、能捕获，但还要进一步固化。

必须加强：

- `neutral`
- `sleep`
- `extend_soft`
- `farewell_look`
- `farewell_bow`
- `celebrate` 起手与收尾

原因：

- 场景的“可爱感”与“安全感”都强依赖真实姿态
- 这一步不到位，会导致 scene 看起来机械、冒失或不稳定

## 5. 音频在会场条件下的策略

当前音频已经能播，但在会场里还需要加强策略，而不只是功能。

必须加强：

- TTS / 音乐音量策略
- 蓝牙音箱连接稳定性
- 音频兜底
- 语音触发降级方案

特别强调：

- 会场里适合“播出去”的音频，不一定适合“识别回来”的音频
- 所以播放能力可以是主链路，开放式 ASR 不应该是主链路

## 当前还需要补充的功能

下面这些是 repo 里还没有完全落地、但为了方案 3 / 5 的展位体验值得补的能力。

## 1. `startle_sound` 场景

方案 5 很强调“被突然声音吓到”的小动物感。

当前 repo 里还缺：

- 正式 scene
- 正式 trigger
- 导演台入口

建议补成：

- `startle_sound`
- 先支持导演触发 / Claw 触发
- 后续再评估是否接受控音频事件

不要第一阶段就做环境噪声自动触发，因为会场太吵，误触发概率高。

## 2. `praise_demo` / `criticism_demo`

方案 5 里的“夸奖和批评反馈”当前还没有正式 scene。

建议补：

- `praise_demo`
- `criticism_demo`

第一阶段实现建议：

- 显式 trigger
- 固定话术
- 明确灯光与动作 valence

第二阶段再考虑：

- 文本分类
- 语音分类

## 3. 真实手部 / 触摸输入

`touch_affection` 当前能演，但还缺真实输入来源。

可选补法：

- 手部接近检测
- 红外 / 距离传感器
- 触摸传感器
- 由视觉桥产生 `hand_near`

建议第一阶段优先做“视觉版 hand-near 或按钮版 touch trigger”，不强求立刻做到复杂手势理解。

## 4. 更强的人体 / 物体 detector

为了会场稳定跟随，建议补一个比当前 `face + motion blob` 更强的 detector 路径。

优先级建议：

1. person detector
2. hand detector
3. 书本 / 目标物 detector

说明：

- 展位里真正最重要的是“它能稳定盯住人”
- 书本跟随是加分项，但不应该比稳定跟人更优先

## 5. 有序帧消费或小队列

当前 extractor 主要看“最新 jpg”，已经够跑第一版 demo，但 temporal continuity 不够强。

建议补：

- 有序帧消费
- 小队列缓存
- 更稳定的速度 / approach 估计

这件事会直接提升：

- `track_target`
- `farewell`
- `multi_person_demo`

## 6. 导演台中的视觉控制工具

建议补到前端：

- 锁定当前目标
- 解除目标锁定
- 强制切到 `track_target`
- 强制切到 `sleep`
- 查看 vision state 历史片段
- 一键复制当前 runtime / vision state

## 按场景拆分的能力计划

下面这张表把“当前可以调用什么、要加强什么、要补什么”按场景拆开。

| 场景 | 当前可直接调用 | 必须加强 | 还需补充 | 优先级 |
| --- | --- | --- | --- | --- |
| `wake_up` | scene runner / 导演台 / vision `target_seen` | 唤醒冷却与 engagement zone | 自动唤醒策略 | P0 |
| `curious_observe` | scene runner / 导演台 | 主目标选择 | 与真实视觉目标绑定 | P1 |
| `touch_affection` | trigger / dynamic context | 前探安全范围 | 真实 hand-near / touch 输入 | P0 |
| `cute_probe` | scene runner / 导演台 | 节奏与随机性 | 无硬性补充 | P2 |
| `daydream` | scene runner / 导演台 | idle 策略 | 空闲状态调度 | P2 |
| `standup_reminder` | scene runner / 导演台 | 语境设计 | 久坐来源 | P2 |
| `track_target` | live tracking / 视觉桥 / replay | detector、目标保持、主目标锁定、ROI、参数调优 | 更强 detector / 帧队列 | P0 |
| `celebrate` | scene runner / TTS / 音乐播放 | offer 联动与音频兜底 | 业务事件来源 | P1 |
| `farewell` | dynamic scene / trigger / TTS | 离场方向推断、no-person 状态机 | 自动触发收尾链 | P0 |
| `sleep` | scene runner / 导演台 | 自动入睡条件 | session 结束策略 | P1 |
| `sigh_demo` | 手动 trigger / TTS | 会场里受控音频链路 | sigh detector | P1 |
| `multi_person_demo` | dynamic context / trigger | 主次目标选择、稳定性 | 多目标检测与排序 | P0 |
| `voice_demo_tired` | 手动 trigger / TTS | 关键词触发稳定性 | ASR + 轻量情绪分类 | P1 |
| `startle_sound` | 无 | 无 | scene + trigger + UI | P1 |
| `praise_demo` | 无 | 无 | scene + trigger + UI | P2 |
| `criticism_demo` | 无 | 无 | scene + trigger + UI | P2 |

## 工具与技术总表

为了避免后面把“场景想法”和“落地技术”混在一起，这里先把当前会用到的工具与技术分层列清楚。

| 能力域 | 当前工具 / 技术 | 当前现成情况 | 还需补充 |
| --- | --- | --- | --- |
| 场景编排 | `scripts/scenes.py`、`scripts/mira_light_runtime.py` | 已有主场景、动态 scene context、cue mode、stop / recover | 新 scene、更多 scene context 字段、失败恢复策略 |
| 设备控制 | ESP32 REST API、runtime client | `/status`、`/control`、`/led`、`/action` 已成型 | 真灯长期在线、自启动、掉线重试 |
| 视觉接收 | `docs/cam_receiver.py`、`scripts/cam_receiver_service.py`、JPEG receiver | `8000` 端口与落盘链路已可用 | 更稳定的长期运行、自监控 |
| 单目视觉理解 | `opencv-python`、`numpy`、Haar face、background subtraction | 已能产出 `vision.latest.json`、`vision.events.jsonl` | 更强 detector、ROI、目标保持、帧队列 |
| 视觉决策桥 | `scripts/vision_runtime_bridge.py` | scene gate、tracking gate、sleep grace、farewell / multi-person 路由已存在 | 更强主目标选择、更强会场过滤 |
| 实时 tracking | `runtime.apply_tracking_event(...)`、四舵机平滑控制 | 已可真实跟随 | 参数调优、真机联调、更稳定 control hint |
| 音频播放 | `scripts/mira_light_audio.py`、`speaker-hp-play`、`afplay` | 资产播放与 TTS 已可用 | 音量策略、音箱稳定性、素材管理 |
| TTS | `speaker-hp-tts-play`、`speaker-hp-openclaw-tts-play`、`say` | scene 内文本播报已可用 | 声线统一、离线兜底策略 |
| 语音输入 | `sounddevice`、本地录音、OpenClaw / 本地转写 | `mira_realtime_voice_interaction.py` 已能跑实时语音链路 | 会场抗噪、短语触发、意图扩展 |
| 语义意图 | `scripts/mira_voice_intents.py` 关键词分类 | `comfort / sigh / farewell / praise` 已有骨架 | `criticism`、更稳分类、会场误触防护 |
| 操作台 | `web/app.js`、`console_server.py`、bridge API | 场景触发、profile 编辑、trigger demo 已有 | 视觉状态可视化、目标锁定、更多应急按钮 |
| OpenClaw 接入 | bridge、plugin、TTS/音箱脚本 | 已有本地可调用骨架 | 云端与长期运行闭环 |

## 逐场景工程清单

这一节把每个场景拆成最实际的 5 个问题：

1. 这个场景依赖什么工具和技术
2. 当前 repo 里已经现成的部分是什么
3. 还缺哪些功能
4. 需要新写或重点改哪些文件
5. 在会场里最容易出什么问题

## 1. `wake_up`

### 需要的工具和技术

- scene runner
- runtime 状态机
- 基础姿态 profile
- 视觉 `target_seen` 或导演台触发
- 灯光基础控制

### 当前现成的部分

- `scenes.py` 里已有成熟 choreography
- `SCENE_META` 已配置 requirement / fallback / operator cue
- `vision_runtime_bridge.py` 已能把 `target_seen` 提升为 `wake_up`
- 导演台已能直接触发

### 还需要补充或加强的部分

- engagement zone，避免路过的人也把它叫醒
- `wake_up` 冷却策略，避免频繁重复触发
- 真机 `sleep -> wake_half -> wake_high -> neutral` 的姿态安全校准

### 主要要写或要改的文件

- `scripts/vision_runtime_bridge.py`
- `scripts/scenes.py`
- `config/mira_light_profile.local.json`

### 会场风险

- 路人从边缘经过时误唤醒
- 真机起身动作过猛

## 2. `curious_observe`

### 需要的工具和技术

- scene runner
- 主目标方向判断
- 基础 yaw / tilt 姿态
- 导演台触发或视觉导向

### 当前现成的部分

- 场景 choreography 已可运行
- 主持人口播、fallback 已写好
- 导演台现可直接触发

### 还需要补充或加强的部分

- 与真实目标方向绑定，而不是默认看固定方向
- 如果当前已经有 `selected_target`，应优先朝该目标半转和歪头

### 主要要写或要改的文件

- `scripts/mira_light_runtime.py`
- `scripts/vision_runtime_bridge.py`
- `web/app.js`

### 会场风险

- 演出来很可爱，但评委不一定看得出“它在看谁”

## 3. `touch_affection`

### 需要的工具和技术

- scene trigger
- 近距交互输入
- 前探 / 回缩姿态
- 轻微 rub motion

### 当前现成的部分

- `trigger_event("touch_detected", ...)` 已存在
- 动态 `touch_affection` scene builder 已存在
- 导演台已有手动触发入口

### 还需要补充或加强的部分

- 真正的 hand-near / touch 输入来源
- 前探安全范围
- 根据触摸侧别决定偏左还是偏右靠近

### 可选技术路线

- 视觉 hand-near
- 红外接近
- 电容触摸
- 按钮式导演触发

### 主要要写或要改的文件

- `scripts/mira_light_runtime.py`
- `scripts/vision_runtime_bridge.py`
- 可新增 `scripts/hand_near_event_bridge.py`

### 会场风险

- 没有人伸手时误触发，会显得“空蹭”

## 4. `cute_probe`

### 需要的工具和技术

- scene runner
- pose / nudge
- 轻随机节奏

### 当前现成的部分

- choreography 已成熟
- 导演台可直接调用

### 还需要补充或加强的部分

- 轻微随机化，不要每次一模一样
- 根据当前目标方向决定先左探还是先右探

### 主要要写或要改的文件

- `scripts/scenes.py`
- 可能在 `runtime` 里增加简单 context 支持

### 会场风险

- 如果动作节奏过于机械，会从“卖萌”变成“摆头”

## 5. `daydream`

### 需要的工具和技术

- scene runner
- idle 状态管理
- 固定 look-away pose

### 当前现成的部分

- choreography 已可运行
- 导演台可直接演示

### 还需要补充或加强的部分

- 决定什么时候进入 idle / 发呆
- 被人靠近或被主持人 cue 后如何优雅退出发呆

### 主要要写或要改的文件

- `scripts/vision_runtime_bridge.py`
- `scripts/mira_light_runtime.py`

### 会场风险

- 如果触发时机不对，会像“没反应”

## 6. `standup_reminder`

### 需要的工具和技术

- scene runner
- 主持人上下文
- 可选的计时器或久坐上下文

### 当前现成的部分

- choreography 已存在
- 导演台可直接触发

### 还需要补充或加强的部分

- 真实“久坐”来源
- 操作台里的一键 reminder cue

### 技术建议

- 第一阶段不要接复杂人体姿态识别
- 先由主持人口播或导演按钮进入该场景

### 主要要写或要改的文件

- `web/app.js`
- `scripts/mira_light_runtime.py`

### 会场风险

- 没有上下文时突然提醒，会让评委摸不着头脑

## 7. `track_target`

### 需要的工具和技术

- 摄像头接收
- OpenCV / NumPy
- 单目目标检测
- tracking event schema
- vision runtime bridge
- runtime live servo mapping

### 当前现成的部分

- 相机接收链路已可用
- `track_target_event_extractor.py` 已能输出 `track_id`、`tracks`、`selected_target`
- `vision_runtime_bridge.py` 已能把 `target_updated + track_target` 路由到 `apply_tracking_event(...)`
- runtime 已能把 `control_hint` 映射成平滑四舵机控制
- replay bench 和 live follow launcher 已存在

### 还需要补充或加强的部分

- 目标保持
- 短时丢失缓冲
- 主目标锁定
- ROI / engagement zone
- 多人环境下的目标抢占策略
- 更强 detector
- 更稳定的帧时序消费

### 现有技术栈

- `opencv-python`
- `numpy`
- Haar face
- background subtraction

### 下一步推荐补的技术

- 轻量 person detector
- hand detector
- 小队列帧消费

### 主要要写或要改的文件

- `scripts/track_target_event_extractor.py`
- `scripts/vision_runtime_bridge.py`
- `scripts/mira_light_runtime.py`
- `web/app.js`

### 会场风险

- 静止目标丢失
- 被边缘路人抢目标
- 频繁 `wake_up / sleep`

## 8. `celebrate`

### 需要的工具和技术

- scene runner
- 音乐资产播放
- TTS
- LED 模式切换
- 内建 `dance` action
- 可选的屏幕素材联动

### 当前现成的部分

- 场景已真正播放 TTS 与音乐
- `AudioCuePlayer` 已支持 `speaker-hp-play` / `afplay`
- `dance.mp3` 缺失时有系统音频兜底
- 导演台可直接触发

### 还需要补充或加强的部分

- 真正的庆祝业务事件来源
- 音量与时长策略
- 音箱断连时的更清晰 fallback
- 屏幕 offer 页面联动

### 主要要写或要改的文件

- `scripts/mira_light_audio.py`
- `scripts/scenes.py`
- `web/app.js`

### 会场风险

- 音乐太吵盖过主持人
- 音频资源不在时现场临时失效

## 9. `farewell`

### 需要的工具和技术

- 动态 scene context
- 离场方向推断
- `no_target` 到 `farewell` 的时机控制
- TTS

### 当前现成的部分

- 动态 `farewell` scene builder 已有
- `farewell_detected` trigger 已有
- 导演台已支持选择 farewell 方向并手动触发
- 场景内 TTS 已存在

### 还需要补充或加强的部分

- 真实离场方向事件来源
- 离场后多久触发 farewell
- `farewell -> sleep` 自动衔接

### 推荐技术路线

- 从视觉桥读取最近稳定的 `horizontal_zone`
- 结合 `target_missing_since` 与最后方向推断 `departureDirection`

### 主要要写或要改的文件

- `scripts/vision_runtime_bridge.py`
- `scripts/mira_light_runtime.py`
- `web/app.js`

### 会场风险

- 人只是暂时低头或遮挡，却被错误识别成离开

## 10. `sleep`

### 需要的工具和技术

- scene runner
- sleep pose
- no-person timeout
- fade-to-sleep 灯光

### 当前现成的部分

- choreography 已成熟
- 导演台已支持 stop-to-sleep
- 视觉桥已有 sleep grace 机制

### 还需要补充或加强的部分

- 更自然的入睡状态机
- session 结束与无目标状态的明确分离

### 主要要写或要改的文件

- `scripts/vision_runtime_bridge.py`
- `scripts/mira_light_runtime.py`
- `config/mira_light_profile.local.json`

### 会场风险

- 还在互动时过早睡下去

## 11. `sigh_demo`

### 需要的工具和技术

- 受控语音 / 音频输入
- sigh 事件检测
- trigger 路由
- TTS 和暖光呼吸

### 当前现成的部分

- scene 已有
- `sigh_detected` trigger 已有
- 导演台已有手动触发
- `mira_voice_intents.py` 已能把典型“唉 / 哎”文本映射成 `sigh`

### 还需要补充或加强的部分

- 真正的 sigh audio event bridge
- 会场里的低误触发策略

### 推荐技术路线

- 第一阶段：导演台 / Claw / 关键词文本触发
- 第二阶段：单独 `mic_event_bridge.py` 做非语义 sigh 检测

### 主要要写或要改的文件

- `scripts/mira_voice_intents.py`
- `scripts/mira_realtime_voice_interaction.py`
- 可新增 `scripts/mic_event_bridge.py`

### 会场风险

- 现场环境声复杂，开放式 sigh 检测误触发高

## 12. `multi_person_demo`

### 需要的工具和技术

- 多目标检测
- `track_id`
- `selected_target`
- 主次目标策略
- 动态 scene context

### 当前现成的部分

- extractor 已输出多目标结构
- runtime 已支持动态 `multi_person_demo`
- bridge 已有 `multi_person_demo` 路由
- 导演台已有手动 trigger

### 还需要补充或加强的部分

- 明确“主目标”选择规则
- 谁是短暂停留者、谁是路过者
- 什么时候触发“纠结一下再选定”的场景

### 推荐策略

- 优先正前方
- 优先停留更久
- 忽略边缘瞬时目标

### 主要要写或要改的文件

- `scripts/track_target_event_extractor.py`
- `scripts/vision_runtime_bridge.py`
- `scripts/mira_light_runtime.py`

### 会场风险

- 人多时切换过于频繁，看起来像监控摄像头

## 13. `voice_demo_tired`

### 需要的工具和技术

- ASR 或短语输入
- 关键词 / 轻量情绪分类
- trigger 路由
- TTS 回复
- 暖色呼吸灯

### 当前现成的部分

- scene 已有
- `voice_tired` trigger 已有
- 导演台已有手动触发
- `mira_realtime_voice_interaction.py` 已有实时语音链路
- `mira_voice_intents.py` 已有 `comfort` 关键词集

### 还需要补充或加强的部分

- 会场环境下的抗噪策略
- 更完整的 tired / comfort 关键词
- 触发冷却，避免连续触发

### 推荐技术路线

- 第一阶段：关键词短语触发
- 第二阶段：局部 ASR + 意图分类
- 第三阶段：再考虑开放式语音

### 主要要写或要改的文件

- `scripts/mira_voice_intents.py`
- `scripts/mira_realtime_voice_interaction.py`
- `web/app.js`

### 会场风险

- 麦克风收进主持人或环境声，误判为用户疲惫表达

## 14. `startle_sound`

### 需要的工具和技术

- 新 scene
- 新 trigger
- 导演台按钮
- 可选音频事件输入

### 当前现成的部分

- 当前只有相近的 scene runtime、audio、trigger 基础设施
- 没有正式场景

### 还需要补充或加强的部分

- `startle_sound` 场景 choreography
- `startle_detected` 或 `startle_sound` 触发事件
- 导演台与 bridge 入口

### 第一阶段建议

- 先做导演触发版
- 不先做环境音自动触发

### 主要要写或要改的文件

- `scripts/scenes.py`
- `scripts/mira_light_runtime.py`
- `tools/mira_light_bridge/bridge_server.py`
- `web/app.js`

### 会场风险

- 自动音频触发非常容易误判

## 15. `praise_demo`

### 需要的工具和技术

- 新 scene
- 轻快 nod / brightness positive
- trigger 路由
- 可选文本 / 语音分类

### 当前现成的部分

- `mira_voice_intents.py` 已有 `praise` 关键词
- 语音实时链路已有基础
- 还没有正式 `praise_demo` scene

### 还需要补充或加强的部分

- 正式 choreography
- bridge trigger 映射
- 导演台按钮

### 主要要写或要改的文件

- `scripts/scenes.py`
- `scripts/mira_light_runtime.py`
- `scripts/mira_voice_intents.py`
- `web/app.js`

### 会场风险

- 如果直接映射到 `celebrate`，会显得太夸张

## 16. `criticism_demo`

### 需要的工具和技术

- 新 scene
- 摇头 / 略暗灯光 / 委屈姿态
- trigger 路由
- 负向文本 / 语义分类

### 当前现成的部分

- 基础 runtime、audio、trigger 基础设施已存在
- 没有正式 scene
- `mira_voice_intents.py` 里目前还没有 `criticism` 关键词集

### 还需要补充或加强的部分

- `criticism` 意图分类
- 正式 scene
- 导演台按钮

### 主要要写或要改的文件

- `scripts/scenes.py`
- `scripts/mira_light_runtime.py`
- `scripts/mira_voice_intents.py`
- `web/app.js`

### 会场风险

- 负向反馈如果做得太重，会从“委屈”变成“出戏”

## 推荐推进顺序

## Phase 0：先闭环真实设备与最小演示条件

目标：

- 确认真灯在线
- 确认蓝牙音箱在线
- 确认导演台、runtime、bridge 都能打到真灯

必须完成：

1. 确认真灯 IP 与 `/status`
2. 确认 scene runner 能直接跑主场景
3. 确认音频能从蓝牙音箱播放
4. 确认 stop-to-neutral / stop-to-sleep 可用

完成标志：

- 可以完整演一次：
  - `wake_up`
  - `curious_observe`
  - `celebrate`
  - `farewell`
  - `sleep`

## Phase 1：把视觉主链路做稳

目标：

- 让 `track_target` 成为会场可用能力，而不是实验室 demo

必须完成：

1. 在 `track_target_event_extractor.py` 里加强：
   - 目标保持
   - 短时丢失缓冲
   - 主目标锁定
   - ROI
2. 在 `vision_runtime_bridge.py` 里加强：
   - 更稳的 scene gating
   - farewell / multi-person 的事件路由
3. 跑真实相机联调
4. 留下可回放样本

完成标志：

- 单人靠近时不会反复 `target_seen / target_lost`
- 单人左右移动时灯会平滑跟随
- 路人从边缘经过时不应轻易抢走主目标

## Phase 2：补齐三个最重要的“感知到你”场景

目标：

- 让观众在 30 秒内明显感觉到 Mira 在感知人

优先完成：

1. `farewell` 的真实离场方向触发
2. `multi_person_demo` 的真实多目标版
3. `touch_affection` 的真实输入版

完成标志：

- 离开左侧和右侧时目送方向不同
- 同时两个人出现时会短暂纠结再选定主目标
- 伸手接近时会做出亲近反应

## Phase 3：把情绪型 demo 做成会场可用版

目标：

- 完成方案 5 中“它懂你”的高光片段

优先完成：

1. `voice_demo_tired`
2. `sigh_demo`
3. `startle_sound`

执行原则：

- 先做受控触发版
- 后做自动识别版

完成标志：

- 能通过导演台 / Claw / 关键词稳定演示
- 不依赖安静环境

## Phase 4：补人格化反馈与二期能力

目标：

- 把展位从“有功能”推进到“更像角色”

建议补：

1. `praise_demo`
2. `criticism_demo`
3. 更强 detector
4. 环境光补偿
5. session / idle 策略

## 每一阶段的建议交付物

### 交付物 A：能力状态表

至少包含：

- 当前场景是否可演
- 依赖条件是否具备
- 当前 fallback 是什么

### 交付物 B：验收 runbook

至少包含：

- 演示顺序
- 成功标准
- 失败回退
- 操作员口令

### 交付物 C：样本与回放资产

至少包含：

- 真实视觉样本
- 回放脚本
- 关键日志
- 关键 state 文件

### 交付物 D：导演台升级记录

至少包含：

- 新增状态
- 新增按钮
- 新增 fallback
- 操作说明

## 文件级实施建议

## 第一优先级文件

- `scripts/track_target_event_extractor.py`
- `scripts/vision_runtime_bridge.py`
- `scripts/mira_light_runtime.py`
- `web/app.js`
- `tools/mira_light_bridge/bridge_server.py`

这 5 个文件决定了：

- 感知是否稳定
- 事件是否正确
- runtime 是否接得住
- 导演台能否看明白
- 上层系统是否容易接入

## 第二优先级文件

- `scripts/scenes.py`
- `scripts/mira_light_audio.py`
- `scripts/mira_realtime_voice_interaction.py`
- `docs/mira-light-live-follow-demo-runbook.md`

这组文件决定了：

- 场景呈现质量
- 音频表达质量
- 情绪 demo 是否可演
- 现场运行是否可复现

## 第三优先级文件

- `web/index.html`
- `web/styles.css`
- `config/mira_light_profile.local.json`
- `docs/mira-light-10-scene-rehearsal-checklist.md`

这组文件决定了：

- 导演台的现场体验
- 真机 pose 固化
- 排练与交付质量

## 推荐的近期执行清单

建议下一步直接按这张清单推进：

1. 先确认真灯当前可达
2. 用真实摄像头把 `track_target` 调到稳定
3. 在导演台补 vision state 可视化
4. 补 `farewell` 的真实离场触发
5. 补 `multi_person_demo` 的主次目标逻辑
6. 补 `touch_affection` 的真实输入
7. 把 `voice_demo_tired / sigh_demo` 做成受控演示版
8. 新增 `startle_sound`
9. 再考虑 `praise_demo / criticism_demo`

## 一句话总结

当前 repo 已经不是“从零开始搭系统”，而是已经具备了一套可演示的骨架：

```text
scene + runtime + vision + audio + bridge + director console
```

下一步最重要的，不是继续扩展概念，而是把这套骨架补成：

```text
真灯可达
-> 视觉稳定
-> 关键互动闭环
-> 导演台可观测
-> 会场可用
```

如果按性价比只做一件事，仍然建议优先做：

```text
把 track_target 做成会场级稳定能力
```

因为它会同时抬升：

- `track_target`
- `farewell`
- `multi_person_demo`
- `touch_affection` 的未来视觉版本

也最能让评委在第一时间相信：

> Mira 不是在播预设动作，而是真的在感知你。
