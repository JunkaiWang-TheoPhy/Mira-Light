# `sz_voice_affect_response` 规格书

## 核心规格

- `sceneId`: `sz_voice_affect_response`
- `demo_goal`: 证明 Mira 对不同语义和情绪输入会产生不同的身体与灯光反应，而不是所有语音都映射到同一个动作。
- `scene_mode`: `event_scene`
- `apiContextKeys`: `transcript`, `intent`, `valence`, `speakerDirection`
- `fallback_behavior`: 没有实时语音理解时，由主持人或导演台手动选择一种意图，例如 `tired`、`praise`、`criticism`，运行相应分支。
- `operator_cue`: “如果你夸它，它会开心；如果你说你很累，它会安静一点接住你；如果你说不好听的话，它会表现出委屈。”
- `success_signal`: 评委能直观看出不同输入语义对应的反应明显不同，而不是“任何一句话它都只是点点头”。

## 当前端侧种子

这个场景在最新版端侧里已经从“弱种子”升级为“中种子”。

可直接借用：

- `servo_2_nod_1900_2200.py`
- `servo_3_shake_2100_2000.py`
- `servo_1_2_dodge_1848_1808.py`
- 灯头 `ALL / BRI / BREATHE / WAKE / SPIN`

所以现在更缺的是分支逻辑统一，而不是每个微动作都得重新写。

## 为什么要把多种语音反应合成一个 scene

Shenzhen pack 只有 10 个一级交互。

如果把下面内容拆成三个按钮：

- tired
- praise
- criticism

会让一级按钮过于碎片化。

更合理的做法是保留一个统一 scene：

- `sz_voice_affect_response`

再通过 `intent` 和 `valence` 决定内部走哪条表达分支。

## 推荐 intent 设计

- `tired`
  - 低头一点，暖呼吸，动作克制
- `praise`
  - 轻快点头，亮一点，像被夸开心
- `criticism`
  - 微微后缩、摇头或略暗，表达委屈

## 推荐 context 约定

- `transcript`
  - 原始说话文本
- `intent`
  - `tired | praise | criticism | unknown`
- `valence`
  - `positive | neutral | negative`
- `speakerDirection`
  - `left | center | right`

## 主控台接入建议

### 按钮文案

- 中文：`语音情绪反馈`
- 英文辅助：`Voice Affect`

### 建议输入控件

- transcript 输入框
- intent 下拉
- valence 下拉
- 说话方向

### 建议 step outline

- Parse the voice affect
- Turn toward the speaker
- Choose an emotion branch
- Express the branch with body and light
- Return to neutral baseline

## 为什么它是 `event_scene`

因为它本质上是“输入驱动的短反应”，不是长篇 narrative scene。

它的成功标准是分支差异足够清楚：

- 累了时是接住
- 被夸时是开心
- 被说重话时是委屈

## 失败信号

- 三种 intent 看起来几乎一样
- 明明是负向输入，结果灯反而更兴奋
- 没有朝说话人方向对齐
- 每次都做得太大，像短舞蹈而不是情绪回应

## 落地建议

这个场景会非常适合深圳现场，因为它把“它好像听懂了”从一句口号变成可观察的证据。
