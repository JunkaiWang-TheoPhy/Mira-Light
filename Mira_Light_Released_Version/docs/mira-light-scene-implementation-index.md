# Mira Light 十个主场景代码实现说明

## 文档目的

这份文档面向技术同学，专门解释：

- 当前 `Mira Light` 的十个主场景在代码里是怎么组织的
- 每个场景在 [`scripts/scenes.py`](/Users/Zhuanz/Documents/Github/Mira-Light/scripts/scenes.py) 里用了哪些步骤类型
- 它和 [`docs/mira-light-booth-scene-table.md`](/Users/Zhuanz/Documents/Github/Mira-Light/docs/mira-light-booth-scene-table.md) 的导演层描述是什么关系
- release 目录在移除 `Figs/` 后，动作解释信息应该从哪里继续看

这份文档不是动作真值本身。

当前动作真值仍然优先以：

- [`Mira Light 展位交互方案2.pdf`](/Users/Zhuanz/Documents/Github/Mira-Light/docs/Mira%20Light%20展位交互方案2.pdf)

为准。

## 当前执行边界补充

需要补一句当前 release 已经变化的工程事实：

- 场景步骤虽然仍然定义在 `SCENES`
- 但 scene 里的 `pose` 和 `control` 现在不会再绕开运行时安全层

这意味着：

- 安全范围内会正常执行
- 超出 `rehearsal_range` 但仍在 `hard_range` 内会被 clamp
- 超出 `hard_range` 的危险输入会被 reject

所以当前场景代码已经不是“写什么角度就必定原样下发”，而是“先通过 choreography，再通过安全裁决”。

相关说明见：

- [release-control-safety-and-openclaw-rollback.md](./release-control-safety-and-openclaw-rollback.md)

## 三层关系

如果你是技术同学，先把这三个层次分清：

### 第 1 层：导演层

文件：

- [`docs/mira-light-booth-scene-table.md`](/Users/Zhuanz/Documents/Github/Mira-Light/docs/mira-light-booth-scene-table.md)

它讲的是：

- 这个场景想让评委看到什么
- 主持人该怎么说
- 哪些依赖条件要准备
- 失败时怎么回退

这一层偏“导演稿 / 场景表”。

### 第 2 层：代码层

文件：

- [`scripts/scenes.py`](/Users/Zhuanz/Documents/Github/Mira-Light/scripts/scenes.py)

它讲的是：

- 场景在程序里叫什么
- 有哪些步骤
- 每个步骤何时执行
- 灯光和姿态怎样切换

这一层是当前真正可执行的 choreography。

### 第 3 层：动作解释层

文件：

- 本文档各场景分节
- [`docs/mira-light-pdf2-engineering-handoff.md`](/Users/Zhuanz/Documents/Github/Mira-Light/docs/mira-light-pdf2-engineering-handoff.md)
- [`docs/mira-light-pdf2-implementation-audit.md`](/Users/Zhuanz/Documents/Github/Mira-Light/docs/mira-light-pdf2-implementation-audit.md)

它讲的是：

- 某个具体场景为什么这么写
- 每段动作对应什么姿态
- 当前代码和 PDF 的关系

这一层是 release 里的“逐场景说明书”。

## 当前代码结构总览

### 1. `SCENE_META`

位置：

- [`scripts/scenes.py`](/Users/Zhuanz/Documents/Github/Mira-Light/scripts/scenes.py)

作用：

- 给导演台和其它上层界面提供场景元信息

里面主要包含：

- `emotionTags`
- `readiness`
- `durationMs`
- `accent`
- `priority`
- `requirements`
- `fallbackHint`
- `operatorCue`

也就是说：

- `SCENE_META` 负责“这个场景怎么被展示和管理”
- `SCENES` 负责“这个场景怎么真正执行”

### 2. `SCENES`

位置：

- [`scripts/scenes.py`](/Users/Zhuanz/Documents/Github/Mira-Light/scripts/scenes.py)

每个场景都有这些字段：

- `title`
- `host_line`
- `notes`
- `tuning_notes`
- `steps`

真正执行时，核心是 `steps`。

### 3. 当前场景步骤类型

前十个主场景里，主要使用了下面这些步骤类型：

- `pose`
- `control`
- `led`
- `delay`
- `comment`
- `action`
- `audio`

说明：

- `pose`：调用预定义姿态
- `control`：直接给舵机绝对角度或相对位移
- `led`：设置灯光
- `delay`：控制节奏
- `comment`：给运行日志和导演理解用
- `action`：调用设备内建预设动作
- `audio`：当前仍是占位型步骤

## 真实代码结构长什么样

这一节是给技术同学看的重点。

上面我们一直在说 `pose / control / led / delay`，但如果只停留在这些词，不看真实代码，接手的人还是会抽象地理解，落地时很容易跑偏。

所以这里直接展示当前代码真正使用的结构。

### 1. `servo1 ~ servo4` 到底是什么

基于 [`ESP32 智能台灯.pdf`](/Users/Zhuanz/Documents/Github/Mira-Light/docs/ESP32%20智能台灯.pdf) 和当前动作实现，程序层统一把四个舵机解释为：

| 字段 | 当前工程语义 | 常见用途 |
| --- | --- | --- |
| `servo1` | 底座转向 | 看向评委、左右扫视、轻摇头时的身体方向 |
| `servo2` | 下臂抬升 | 起身、降臂、整体抬高或压低 |
| `servo3` | 前段关节 / 中间关节抬升与前探 | 探头、回缩、往前顶、保持工作位 |
| `servo4` | 灯头俯仰 / 微表情 | 点头、低头、抬头、害羞、抖毛 |

这四个字段都遵守 `ESP32` 设备接口的约束：

- `absolute` 模式：`0~180`
- `relative` 模式：正负值表示相对位移

### 2. `control` 步骤的真实代码

程序里真正的低层控制长这样：

```python
{"type": "control", "payload": {"mode": "absolute", "servo1": 96, "servo2": 98, "servo3": 102, "servo4": 90}}
```

这表示：

- 这是一个 `control` 类型的步骤
- 它会调用 `POST /control`
- `mode = absolute` 表示四个舵机都直接打到目标角度

如果是相对位移，则长这样：

```python
{"type": "control", "payload": {"mode": "relative", "servo1": 4, "servo4": -2}}
```

这表示：

- `servo1` 相对当前角度 `+4`
- `servo4` 相对当前角度 `-2`

### 3. 你要求出现的这种真实代码序列，程序里到底代表什么

下面这个序列就是当前场景代码里常见的“细小抖动 / 摇动 / 微表情组合”写法：

```json
[
  {"mode":"relative","servo1":4,  "servo4":-2},
  {"delayMs":120},
  {"mode":"relative","servo1":-8, "servo4":4},
  {"delayMs":120},
  {"mode":"relative","servo1":4,  "servo4":-2},
  {"delayMs":120},
  {"mode":"relative","servo1":-4, "servo4":2},
  {"delayMs":120},
  {"mode":"relative","servo1":8,  "servo4":-4},
  {"delayMs":120},
  {"mode":"relative","servo1":-4, "servo4":2}
]
```

这串代码的工程含义是：

- `servo1` 在左右轻摆，制造“身体在抖 / 摇”的感觉
- `servo4` 同步做小幅俯仰，制造“头部也在抖”的感觉
- 每次 `delayMs: 120` 是动作间隔
- 组合起来形成连续的微表情动作，而不是单次抽动

在当前项目里，这种结构主要用在：

- `wake_up` 的“抖毛”
- `curious_observe` 的“缓慢摇头”
- `farewell` 的“点头式挥手”

### 4. `delay` 步骤的真实代码

```python
{"type": "delay", "ms": 180}
```

解释：

- 当前步骤执行完后，停 `180ms`
- 这个步骤只负责节奏，不发设备请求

导演上看它只是“停一下”，但工程上它非常重要，因为：

- 没有 `delay`，动作会显得像故障
- `delay` 太长，场景会拖沓

### 5. `led` 步骤的真实代码

真实代码长这样：

```python
{"type": "led", "payload": {"mode": "solid", "brightness": 132, "color": {"r": 255, "g": 220, "b": 180}}}
```

它表示：

- 调用 `POST /led`
- `mode = solid`
- 亮度 `132`
- 颜色是暖白

如果要做渐变感，当前项目不是靠一个真正的 gradient API，而是靠多次 `led` 步骤模拟，例如：

```python
[
    {"type": "led", "payload": {"mode": "solid", "brightness": 6, "color": {"r": 255, "g": 176, "b": 116}}},
    {"type": "delay", "ms": 220},
    {"type": "led", "payload": {"mode": "solid", "brightness": 12, "color": {"r": 255, "g": 188, "b": 130}}},
    {"type": "delay", "ms": 180},
    {"type": "led", "payload": {"mode": "solid", "brightness": 22, "color": {"r": 255, "g": 200, "b": 148}}},
]
```

也就是说：

- 所谓“渐变色 / 渐变亮度”
- 在当前代码里本质上是“分段逼近”

### 6. `pose` 步骤的真实代码

代码里经常看到：

```python
pose("neutral")
pose("sleep")
pose("wake_half")
```

它们在 `scenes.py` 中最终会展开成：

```python
{"type": "pose", "name": "neutral"}
```

运行时再去 `POSES` 字典里查这个名字对应的四个舵机角度，并最终变成：

```python
{"mode": "absolute", "servo1": 96, "servo2": 96, "servo3": 98, "servo4": 90}
```

所以：

- `pose` 是“命名姿态”
- `control` 是“直接角度控制”

### 7. `action` 步骤的真实代码

当前只有少数场景还直接用设备内建预设动作，例如：

```python
{"type": "action", "payload": {"name": "dance", "loops": 1}}
```

它会调用：

- `POST /action`

并执行设备固件里已有的预设动作。

当前项目中：

- `celebrate` 仍然保留了一次 `dance`
- 但大多数主场景已经不依赖预设动作，而是自己写 choreography

### 8. `audio` 步骤的真实代码

```python
{"type": "audio", "name": "dance.mp3"}
```

这里要特别说明：

- 当前运行时里 `audio` 还只是占位
- 它会记录日志，但不会真的在 Python 里播放音乐

也就是说，看到 `audio("dance.mp3")` 不等于音频链路已经做完。

### 9. 运行时如何解释这些步骤

这些步骤最终由：

- [`scripts/mira_light_runtime.py`](/Users/Zhuanz/Documents/Github/Mira-Light/scripts/mira_light_runtime.py)

来解释和执行。

简单说：

- `pose` -> 查 `POSES` 后发 `POST /control`
- `control` -> 直接发 `POST /control`
- `led` -> 发 `POST /led`
- `action` -> 发 `POST /action`
- `delay` -> 本地等待
- `comment` -> 只进日志
- `audio` -> 当前只打印 TODO

所以从技术角度看，这一套场景系统其实就是：

```text
场景定义（scenes.py）
-> 逐步解释 step
-> 映射成 ESP32 REST API
```

## 真实代码片段示例

下面给技术同学放几个“当前项目里真实出现”的代码形状。

### 示例 A：`wake_up` 的微光 + 起身 + 抖毛

```python
steps = [
    pose("sleep"),
    led("solid", brightness=6, color={"r": 255, "g": 176, "b": 116}),
    delay(220),
    led("solid", brightness=12, color={"r": 255, "g": 188, "b": 130}),
    delay(180),
    led("solid", brightness=22, color={"r": 255, "g": 200, "b": 148}),
    delay(180),
    led("breathing", brightness=42, color={"r": 255, "g": 214, "b": 172}),
    delay(420),
    pose("wake_half"),
    delay(360),
    absolute(servo1=90, servo2=98, servo3=108, servo4=84),
    delay(320),
    absolute(servo1=90, servo2=100, servo3=112, servo4=82),
    delay(700),
    absolute(servo1=90, servo2=96, servo3=98, servo4=90),
    nudge(servo1=4, servo4=-2),
    delay(120),
    nudge(servo1=-8, servo4=4),
    delay(120),
    nudge(servo1=4, servo4=-2),
]
```

技术解读：

- 前半段是灯光渐亮
- 中间是姿态抬升和后仰
- 最后是通过 `nudge()` 做相对抖动，形成“抖毛”

### 示例 B：`curious_observe` 的害羞段

```python
led("solid", brightness=100, color={"r": 246, "g": 214, "b": 186}),
absolute(servo1=82, servo2=94, servo3=94, servo4=100),
delay(320),
nudge(servo4=4),
delay(120),
nudge(servo4=-8),
delay(120),
nudge(servo4=4),
delay(180),
```

技术解读：

- 先把灯光压暗一点
- 再把底座转开、灯头压低
- 接着用 `servo4` 做上下灯头，表达害羞

### 示例 C：`celebrate` 的多色跳舞段

```python
absolute(servo1=90, servo2=108, servo3=116, servo4=80),
led("solid", brightness=198, color={"r": 255, "g": 64, "b": 64}),
delay(180),
absolute(servo1=78, servo2=108, servo3=112, servo4=82),
led("solid", brightness=202, color={"r": 64, "g": 128, "b": 255}),
delay(180),
absolute(servo1=90, servo2=106, servo3=114, servo4=80),
delay(140),
absolute(servo1=102, servo2=108, servo3=112, servo4=82),
led("solid", brightness=202, color={"r": 72, "g": 220, "b": 132}),
delay(180),
```

技术解读：

- 这不是单纯调用 `dance`
- 而是用多组绝对角度和多次灯光变色来写“上摇”

## 技术同学最需要记住的三句话

1. `mira-light-booth-scene-table.md` 讲的是“导演意图”，不是代码真值。
2. `scripts/scenes.py` 是当前真正的可执行 choreography。
3. release 不再附带 `Figs/motions/*/README.md`，逐场景解释以本文、handoff 和 audit 文档为准。

## 当前十个主场景在代码里的写法

下面按场景逐个说明。

---

## 1. `wake_up`

### 代码 id

```text
wake_up
```

### 导演层含义

对应：

- “起床”
- 从蜷缩状态慢慢醒来
- 微光 -> 起身 -> 伸懒腰 -> 抖毛 -> 看向评委

### 当前代码组织方式

步骤类型组合：

- `pose`
- `led`
- `delay`
- `control`
- `comment`

也就是说，它主要靠：

- 预定义姿态切换
- 几段亮度 / 颜色变化
- 一段绝对角度抬高
- 一组相对抖动

来完成。

### 当前实现状态

当前已覆盖：

- 睡姿进入
- 微光亮起
- 多段提亮
- 半醒起身
- 抬高并后仰
- 高位停顿
- 回正并抖毛
- 看向评委

### 当前真实代码摘录

```python
steps = [
    pose("sleep"),
    comment("微光亮起，像刚睁眼。"),
    led("solid", brightness=6, color={"r": 255, "g": 176, "b": 116}),
    delay(220),
    led("solid", brightness=12, color={"r": 255, "g": 188, "b": 130}),
    delay(180),
    led("solid", brightness=22, color={"r": 255, "g": 200, "b": 148}),
    delay(180),
    led("breathing", brightness=42, color={"r": 255, "g": 214, "b": 172}),
    delay(420),
    comment("身体抬到半醒。"),
    pose("wake_half"),
    delay(360),
    comment("继续升高并仰头，做伸懒腰。"),
    absolute(servo1=90, servo2=98, servo3=108, servo4=84),
    delay(320),
    absolute(servo1=90, servo2=100, servo3=112, servo4=82),
    delay(700),
    comment("回到正常高度并抖两下，像小动物醒来抖毛。"),
    absolute(servo1=90, servo2=96, servo3=98, servo4=90),
    nudge(servo1=4, servo4=-2),
    delay(120),
    nudge(servo1=-8, servo4=4),
    delay(120),
    nudge(servo1=4, servo4=-2),
    delay(120),
    nudge(servo1=-4, servo4=2),
    delay(120),
    nudge(servo1=8, servo4=-4),
    delay(120),
    nudge(servo1=-4, servo4=2),
    delay(120),
    comment("最后慢慢看向评委。"),
    absolute(servo1=96, servo2=96, servo3=98, servo4=90),
    led("solid", brightness=132, color=SOFT_WARM),
]
```

### 相关说明

- 当前 release 不再附带单独的 `motions README`；本节与 [`scripts/scenes.py`](/Users/Zhuanz/Documents/Github/Mira-Light/scripts/scenes.py) 一起构成 `wake_up` 的解释层

---

## 2. `curious_observe`

### 代码 id

```text
curious_observe
```

### 导演层含义

对应：

- “好奇你是谁”
- 不是冷冰冰直视
- 而是靠近、试探、害羞、再探出来

### 当前代码组织方式

步骤类型组合：

- `pose`
- `led`
- `delay`
- `control`
- `comment`

这个场景没有直接用设备内建 `curious` 动作，而是把试探过程拆成了程序侧 choreography。

### 当前实现状态

当前已覆盖：

- 看向评委
- 靠近
- 缓慢摇头
- 再更靠近一点
- 转开并低头
- 上下轻动灯头
- 再探出来
- 左右轻移
- 面向你点头
- 用户继续靠近时再次转开低头
- 再往回和往前靠

### 当前真实代码摘录

```python
steps = [
    pose("neutral"),
    led("solid", brightness=124, color={"r": 255, "g": 225, "b": 190}),
    delay(160),
    comment("先注意到评委。"),
    absolute(servo1=94, servo2=96, servo3=98, servo4=90),
    delay(220),
    comment("向评委方向靠近一点。"),
    absolute(servo1=100, servo2=98, servo3=102, servo4=90),
    delay(260),
    comment("缓慢摇头一次，像在确认你是谁。"),
    nudge(servo1=4, servo4=-2),
    delay(140),
    nudge(servo1=-8, servo4=4),
    delay(140),
    nudge(servo1=4, servo4=-2),
    delay(180),
    comment("再更靠近一点，看着用户。"),
    absolute(servo1=102, servo2=98, servo3=104, servo4=90),
    delay(220),
    comment("转开并低头，表示害羞。"),
    led("solid", brightness=100, color={"r": 246, "g": 214, "b": 186}),
    absolute(servo1=82, servo2=94, servo3=94, servo4=100),
    delay(320),
    nudge(servo4=4),
    delay(120),
    nudge(servo4=-8),
    delay(120),
    nudge(servo4=4),
    delay(180),
    comment("再转向你，慢慢探出来看。"),
    led("solid", brightness=124, color={"r": 255, "g": 225, "b": 190}),
    absolute(servo1=96, servo2=98, servo3=106, servo4=92),
    delay(220),
    nudge(servo1=3),
    delay(110),
    nudge(servo1=-6),
    delay(110),
    nudge(servo1=3),
    delay(160),
    comment("面对你点头一下。"),
    absolute(servo1=96, servo2=98, servo3=102, servo4=90),
    nudge(servo4=4),
    delay(120),
    nudge(servo4=-8),
    delay(140),
    nudge(servo4=4),
    delay(180),
    comment("如果对方继续靠近，则转向远离评委侧并低头，表示有点怕。"),
    absolute(servo1=84, servo2=94, servo3=98, servo4=102),
    delay(240),
    comment("害羞结束后，再慢慢往回和往前靠。"),
    absolute(servo1=94, servo2=98, servo3=102, servo4=92),
]
```

### 相关说明

- 当前 release 不再附带单独的 `motions README`；本节与 [`scripts/scenes.py`](/Users/Zhuanz/Documents/Github/Mira-Light/scripts/scenes.py) 一起构成 `curious_observe` 的解释层

---

## 3. `touch_affection`

### 代码 id

```text
touch_affection
```

### 导演层含义

对应：

- “摸一摸”
- 用户伸手时，Mira 主动靠过去
- 在手下上下左右轻蹭
- 灯光变暖
- 手拿开后追一下，再回到自然照明方向

### 当前代码组织方式

步骤类型组合：

- `pose`
- `led`
- `control`
- `delay`
- `comment`

这里也没有完全依赖预设动作，而是把“靠近、下送、蹭、追手”全部拆成了程序编排。

### 当前实现状态

当前已覆盖：

- 中性起步
- 靠近手
- 身体下送
- 灯头上下左右轻蹭
- 灯光变暖
- 追手
- 回到自然照明方向
- 回中性位

### 当前真实代码摘录

```python
steps = [
    pose("neutral"),
    led("solid", brightness=168, color={"r": 255, "g": 190, "b": 120}),
    comment("先温和地靠近手。"),
    absolute(servo1=94, servo2=100, servo3=108, servo4=90),
    delay(260),
    comment("身体往下送一点，让灯头进入手掌下方。"),
    absolute(servo1=94, servo2=104, servo3=110, servo4=94),
    delay(240),
    comment("在手下做小幅上下和左右蹭动。"),
    led("solid", brightness=182, color={"r": 255, "g": 176, "b": 106}),
    absolute(servo1=98, servo2=104, servo3=110, servo4=94),
    delay(140),
    absolute(servo1=90, servo2=104, servo3=110, servo4=86),
    delay(140),
    absolute(servo1=98, servo2=103, servo3=109, servo4=94),
    delay(140),
    absolute(servo1=90, servo2=103, servo3=109, servo4=86),
    delay(140),
    comment("手拿开后轻轻追一下手的方向。"),
    absolute(servo1=100, servo2=98, servo3=104, servo4=90),
    delay(320),
    comment("慢慢回到自然照明的方向，等下一次互动。"),
    absolute(servo1=92, servo2=96, servo3=98, servo4=92),
    led("solid", brightness=138, color={"r": 255, "g": 210, "b": 170}),
    delay(220),
    pose("neutral"),
]
```

### 相关说明

- 当前 release 不再附带单独的 `motions README`；本节与 [`scripts/scenes.py`](/Users/Zhuanz/Documents/Github/Mira-Light/scripts/scenes.py) 一起构成 `touch_affection` 的解释层

---

## 4. `cute_probe`

### 代码 id

```text
cute_probe
```

### 导演层含义

对应：

- “卖萌”
- 轻点头
- 左右找角度
- 中间关节上提又放下
- 探头
- 缩回
- 再探出去

### 当前代码组织方式

步骤类型组合：

- `pose`
- `led`
- `control`
- `delay`
- `comment`

这个场景的特点是：完全是“分解动作式 choreography”，不是只用一个内建动作。

### 当前实现状态

当前已覆盖：

- 轻点头
- 左右找角度
- 中间关节上提再下放
- 探头
- 缩回
- 再探出去

### 当前真实代码摘录

```python
steps = [
    pose("neutral"),
    led("solid", brightness=124, color={"r": 255, "g": 222, "b": 178}),
    comment("先轻轻点头，再停住。"),
    absolute(servo1=90, servo2=96, servo3=98, servo4=96),
    delay(120),
    absolute(servo1=90, servo2=96, servo3=98, servo4=90),
    delay(140),
    comment("底座向一侧，再向另一侧，像在找角度研究你。"),
    absolute(servo1=82, servo2=96, servo3=98, servo4=90),
    delay(180),
    absolute(servo1=98, servo2=96, servo3=98, servo4=90),
    delay(180),
    comment("中间关节先抬一下，再往下放。"),
    absolute(servo1=90, servo2=96, servo3=108, servo4=88),
    delay(180),
    absolute(servo1=90, servo2=96, servo3=92, servo4=94),
    delay(180),
    comment("慢慢探头。"),
    led("solid", brightness=138, color={"r": 255, "g": 228, "b": 188}),
    absolute(servo1=92, servo2=102, servo3=114, servo4=90),
    delay(260),
    comment("突然缩回，像被吓到了。"),
    absolute(servo1=90, servo2=92, servo3=92, servo4=96),
    delay(180),
    comment("再慢慢探出去，胆小但还是好奇。"),
    led("solid", brightness=118, color={"r": 252, "g": 216, "b": 174}),
    absolute(servo1=92, servo2=100, servo3=110, servo4=90),
    delay(260),
    pose("neutral"),
]
```

### 相关说明

- 当前 release 不再附带单独的 `motions README`；本节与 [`scripts/scenes.py`](/Users/Zhuanz/Documents/Github/Mira-Light/scripts/scenes.py) 一起构成 `cute_probe` 的解释层

---

## 5. `daydream`

### 代码 id

```text
daydream
```

### 导演层含义

对应：

- “发呆”
- 走神看远处
- 停住
- 快速回神
- 或者像打瞌睡一样慢慢低下去，再惊醒

### 当前代码组织方式

步骤类型组合：

- `pose`
- `led`
- `control`
- `delay`
- `comment`

当前写法直接把“走神版”和“打盹版”两种变体串在同一个 scene 里。

### 当前实现状态

当前已覆盖：

- 走神看远处
- 停住
- 快速回神
- 打瞌睡版逐步下沉
- 快贴桌面时弹回来

### 当前真实代码摘录

```python
steps = [
    pose("neutral"),
    led("solid", brightness=118, color={"r": 245, "g": 235, "b": 210}),
    comment("先慢慢抬头，看向一个莫名其妙的方向。"),
    absolute(servo1=74, servo2=98, servo3=100, servo4=80),
    delay(520),
    led("solid", brightness=108, color={"r": 240, "g": 232, "b": 208}),
    delay(3200),
    comment("突然回过神来。"),
    pose("neutral"),
    delay(180),
    comment("再来一次打瞌睡版。"),
    led("solid", brightness=110, color={"r": 245, "g": 230, "b": 205}),
    absolute(servo1=90, servo2=92, servo3=92, servo4=96),
    delay(420),
    led("solid", brightness=96, color={"r": 240, "g": 225, "b": 200}),
    absolute(servo1=90, servo2=88, servo3=86, servo4=102),
    delay(420),
    led("solid", brightness=72, color={"r": 230, "g": 214, "b": 190}),
    absolute(servo1=90, servo2=84, servo3=82, servo4=108),
    delay(520),
    comment("快贴到桌面时突然弹回来。"),
    pose("neutral"),
    led("solid", brightness=120, color={"r": 245, "g": 235, "b": 210}),
]
```

### 相关说明

- 当前 release 不再附带单独的 `motions README`；本节与 [`scripts/scenes.py`](/Users/Zhuanz/Documents/Github/Mira-Light/scripts/scenes.py) 一起构成 `daydream` 的解释层

---

## 6. `standup_reminder`

### 代码 id

```text
standup_reminder
```

### 导演层含义

对应：

- “久坐检测：蹭蹭”
- 像宠物提醒你起来
- 三次蹭蹭
- 两次点头
- 被拒绝后轻摇头

### 当前代码组织方式

步骤类型组合：

- `pose`
- `led`
- `control`
- `delay`
- `comment`

这个场景已经不再只是粗糙复用 `pawing_bump`，而是直接写出了“埋头 -> 顶起 -> 后退”的三次节奏。

### 当前实现状态

当前已覆盖：

- 转向评委
- 灯臂前送
- 三次蹭蹭
- 两次点头
- 被拒绝后的轻摇头
- 慢慢回到原位

### 当前真实代码摘录

```python
steps = [
    pose("neutral"),
    led("solid", brightness=132, color={"r": 255, "g": 218, "b": 176}),
    comment("先转向评委并把灯臂往前送。"),
    absolute(servo1=98, servo2=100, servo3=102, servo4=92),
    delay(220),
    comment("第一次蹭蹭：先往下埋，再往上顶，然后后退一点。"),
    absolute(servo1=98, servo2=102, servo3=98, servo4=102),
    delay(140),
    absolute(servo1=98, servo2=96, servo3=110, servo4=88),
    delay(140),
    absolute(servo1=96, servo2=100, servo3=102, servo4=94),
    delay(120),
    comment("第二次蹭蹭。"),
    absolute(servo1=98, servo2=102, servo3=98, servo4=102),
    delay(140),
    absolute(servo1=98, servo2=96, servo3=110, servo4=88),
    delay(140),
    absolute(servo1=96, servo2=100, servo3=102, servo4=94),
    delay(120),
    comment("第三次蹭蹭。"),
    absolute(servo1=98, servo2=102, servo3=98, servo4=102),
    delay(140),
    absolute(servo1=98, servo2=96, servo3=110, servo4=88),
    delay(140),
    absolute(servo1=96, servo2=100, servo3=102, servo4=94),
    delay(160),
    comment("清晰地点两次头。"),
    nudge(servo4=5),
    delay(140),
    nudge(servo4=-10),
    delay(140),
    nudge(servo4=5),
    delay(180),
    nudge(servo4=5),
    delay(140),
    nudge(servo4=-10),
    delay(140),
    nudge(servo4=5),
    delay(180),
    comment("评委说不要后，轻轻摇一下头。"),
    nudge(servo1=4),
    delay(120),
    nudge(servo1=-8),
    delay(120),
    nudge(servo1=4),
    delay(180),
    comment("慢慢回到原位。"),
    pose("neutral"),
    led("solid", brightness=118, color=SOFT_WARM),
]
```

### 相关说明

- 当前 release 不再附带单独的 `motions README`；本节与 [`scripts/scenes.py`](/Users/Zhuanz/Documents/Github/Mira-Light/scripts/scenes.py) 一起构成 `standup_reminder` 的解释层

---

## 7. `track_target`

### 代码 id

```text
track_target
```

### 导演层含义

对应：

- “追踪（展示感知能力）”
- 书从左到右移动时，灯头跟着书走
- 停则停，再动则再跟

### 当前代码组织方式

步骤类型组合：

- `pose`
- `led`
- `control`
- `delay`
- `comment`

但要强调：

当前这个场景**不是最终真实实现**，而是：

- 一个排练用 surrogate choreography

也就是用固定的左 -> 中 -> 右 -> 停 -> 再跟，来先把展位上的“跟随感”排练出来。

### 当前实现状态

当前已覆盖：

- 左 -> 中 -> 右 -> 停 -> 再跟 的排练节奏
- 低头看向桌面目标
- 冷静工作光
- 回中性工作位

当前缺口：

- 还没有真实目标检测
- 还没有目标坐标到舵机角度的映射
- 还没有连续闭环控制

### 当前真实代码摘录

```python
steps = [
    pose("neutral"),
    led("solid", brightness=170, color={"r": 232, "g": 242, "b": 255}),
    comment("书在左侧时，灯头压低并看向左侧桌面。"),
    absolute(servo1=78, servo2=96, servo3=96, servo4=102),
    delay(420),
    comment("目标开始向中间移动。"),
    absolute(servo1=88, servo2=96, servo3=96, servo4=98),
    delay(360),
    comment("目标继续到右侧。"),
    absolute(servo1=102, servo2=96, servo3=96, servo4=102),
    delay(420),
    comment("评委停下来，Mira 也停住。"),
    delay(520),
    comment("评委再移动，Mira 再跟。"),
    absolute(servo1=94, servo2=96, servo3=96, servo4=98),
    delay(320),
    absolute(servo1=108, servo2=96, servo3=96, servo4=104),
    delay(420),
    comment("回到中性工作位。"),
    pose("neutral"),
    led("solid", brightness=156, color={"r": 244, "g": 244, "b": 236}),
]
```

### 相关说明

- 当前 release 不再附带单独的 `motions README`；本节与 [`scripts/scenes.py`](/Users/Zhuanz/Documents/Github/Mira-Light/scripts/scenes.py) 一起构成 `track_target` 的解释层

---

## 8. `celebrate`

### 代码 id

```text
celebrate
```

### 导演层含义

对应：

- “模拟拿到 offer：跳舞模式”
- 上摇
- 下摇
- 多色变化
- 音乐
- 减速
- 左右摇头
- 身体转一下

### 当前代码组织方式

步骤类型组合：

- `pose`
- `led`
- `delay`
- `control`
- `comment`
- `audio`
- `action`

这是十个主场景里类型最丰富的一个：

- 有灯光 choreography
- 有机械 choreography
- 有 `audio` 占位
- 有一次 `dance` 预设动作

### 当前实现状态

当前已覆盖：

- 上摇
- 下摇
- 多色切换
- `rainbow_cycle`
- 音乐触发
- 减速
- 左右摇头
- 身体转一下
- 回暖光收尾

### 当前真实代码摘录

```python
steps = [
    pose("neutral"),
    led("solid", brightness=168, color={"r": 255, "g": 236, "b": 180}),
    delay(180),
    comment("收到 offer 后先整体往上摇。"),
    absolute(servo1=90, servo2=108, servo3=116, servo4=80),
    led("solid", brightness=198, color={"r": 255, "g": 64, "b": 64}),
    delay(180),
    absolute(servo1=78, servo2=108, servo3=112, servo4=82),
    led("solid", brightness=202, color={"r": 64, "g": 128, "b": 255}),
    delay(180),
    absolute(servo1=90, servo2=106, servo3=114, servo4=80),
    delay(140),
    absolute(servo1=102, servo2=108, servo3=112, servo4=82),
    led("solid", brightness=202, color={"r": 72, "g": 220, "b": 132}),
    delay(180),
    absolute(servo1=90, servo2=106, servo3=114, servo4=80),
    delay(160),
    comment("再整体往下摇。"),
    absolute(servo1=90, servo2=94, servo3=98, servo4=100),
    led("solid", brightness=196, color={"r": 255, "g": 168, "b": 72}),
    delay(180),
    absolute(servo1=82, servo2=94, servo3=96, servo4=100),
    led("solid", brightness=198, color={"r": 208, "g": 96, "b": 255}),
    delay(180),
    absolute(servo1=90, servo2=96, servo3=98, servo4=98),
    delay(140),
    absolute(servo1=100, servo2=94, servo3=96, servo4=100),
    led("solid", brightness=198, color={"r": 64, "g": 224, "b": 224}),
    delay(180),
    absolute(servo1=90, servo2=96, servo3=98, servo4=98),
    delay(180),
    comment("进入彩色庆祝灯效。"),
    led("rainbow_cycle", brightness=210),
    audio("dance.mp3"),
    action("dance", loops=1),
    delay(380),
    comment("音乐停后慢慢减速，回到正常姿态。"),
    led("solid", brightness=176, color={"r": 255, "g": 208, "b": 156}),
    absolute(servo1=94, servo2=102, servo3=106, servo4=88),
    delay(180),
    absolute(servo1=90, servo2=98, servo3=102, servo4=90),
    delay(180),
    comment("左右摇头，再身体转一下，像刚跳完舞喘口气。"),
    nudge(servo4=4),
    delay(120),
    nudge(servo4=-8),
    delay(120),
    nudge(servo4=4),
    delay(120),
    nudge(servo1=6),
    delay(140),
    nudge(servo1=-6),
    delay(140),
    pose("neutral"),
    led("solid", brightness=140, color=SOFT_WARM),
]
```

### 相关说明

- 当前 release 不再附带单独的 `motions README`；本节与 [`scripts/scenes.py`](/Users/Zhuanz/Documents/Github/Mira-Light/scripts/scenes.py) 一起构成 `celebrate` 的解释层

---

## 9. `farewell`

### 代码 id

```text
farewell
```

### 导演层含义

对应：

- “挥手送别”
- 先目送评委离开
- 再做两次慢慢点头式挥手
- 最后低头表示舍不得

### 当前代码组织方式

步骤类型组合：

- `pose`
- `led`
- `control`
- `delay`
- `comment`

相比之前固定 `farewell_look + wave + bow` 的写法，现在已经更贴近导演稿里的节奏。

### 当前实现状态

当前已覆盖：

- 先目送
- 两次慢慢点头式挥手
- 最后低头
- 回到中性位并降亮度

当前缺口：

- 还不是动态离场方向版

### 当前真实代码摘录

```python
steps = [
    pose("neutral"),
    led("solid", brightness=108, color={"r": 255, "g": 214, "b": 176}),
    comment("先目送评委离开的方向。"),
    absolute(servo1=106, servo2=96, servo3=100, servo4=92),
    delay(420),
    comment("再做两次慢慢点头，像挥手说再见。"),
    nudge(servo4=5),
    delay(180),
    nudge(servo4=-10),
    delay(180),
    nudge(servo4=5),
    delay(220),
    nudge(servo4=5),
    delay(180),
    nudge(servo4=-10),
    delay(180),
    nudge(servo4=5),
    delay(220),
    comment("最后微微低头，像有点舍不得。"),
    absolute(servo1=102, servo2=92, servo3=96, servo4=100),
    delay(180),
    pose("neutral"),
    led("solid", brightness=90, color={"r": 255, "g": 210, "b": 170}),
]
```

### 相关说明

- 当前 release 不再附带单独的 `motions README`；本节与 [`scripts/scenes.py`](/Users/Zhuanz/Documents/Github/Mira-Light/scripts/scenes.py) 一起构成 `farewell` 的解释层

---

## 10. `sleep`

### 代码 id

```text
sleep
```

### 导演层含义

对应：

- “睡觉”
- 先低头
- 灯臂缓缓降下去
- 做一次小伸懒腰
- 再蜷缩起来
- 灯光慢慢变暗到微光

### 当前代码组织方式

步骤类型组合：

- `pose`
- `led`
- `control`
- `delay`
- `comment`

这个场景现在已经不再只是简单 `stretch -> sleep`，而是先做回落，再做小舒展，再进入睡姿。

### 当前实现状态

当前已覆盖：

- 先低头
- 灯臂降下去
- 小伸懒腰
- 回到 `sleep_ready`
- 进入 `sleep`
- 渐暗到微光再熄灭

### 当前真实代码摘录

```python
steps = [
    pose("neutral"),
    led("solid", brightness=118, color={"r": 250, "g": 226, "b": 184}),
    comment("先慢慢低头。"),
    absolute(servo1=90, servo2=94, servo3=96, servo4=98),
    delay(280),
    comment("灯臂缓缓降下去。"),
    absolute(servo1=90, servo2=90, servo3=90, servo4=102),
    delay(320),
    comment("做一个小伸懒腰：先舒展一下。"),
    absolute(servo1=90, servo2=96, servo3=104, servo4=88),
    delay(260),
    comment("再慢慢回到准备睡觉的姿态。"),
    pose("sleep_ready"),
    delay(300),
    pose("sleep"),
    delay(220),
    led("solid", brightness=60, color=WARM_AMBER),
    delay(260),
    led("solid", brightness=30, color=WARM_AMBER),
    delay(320),
    led("solid", brightness=12, color=WARM_AMBER),
    delay(380),
    led("off", brightness=0),
]
```

### 相关说明

- 当前 release 不再附带单独的 `motions README`；本节与 [`scripts/scenes.py`](/Users/Zhuanz/Documents/Github/Mira-Light/scripts/scenes.py) 一起构成 `sleep` 的解释层

---

## 当前实现上最重要的技术结论

### 1. 现在的场景大多不是“调用一个内建动作”了

除了少量仍然保留的 `action("dance")` 这类预设动作，现在大多数主场景都已经是：

- `pose`
- `control`
- `led`
- `delay`
- `comment`

组合出来的 choreography。

### 2. `SCENE_META` 是导演台展示层，`SCENES` 是执行层

如果你要改导演台显示的：

- 情绪标签
- 优先级
- 时长
- readiness

看的是：

- [`SCENE_META`](/Users/Zhuanz/Documents/Github/Mira-Light/scripts/scenes.py)

如果你要改动作本身：

- 姿态
- 舵机角度
- 灯光颜色
- 时序

看的是：

- [`SCENES`](/Users/Zhuanz/Documents/Github/Mira-Light/scripts/scenes.py)

### 3. 当前最大工程缺口已经变成 `track_target`

不是“有没有场景”，而是：

- 这些场景虽然都进代码了
- 但 `track_target` 还没有真实视觉闭环

所以如果技术同学要继续推进，最有价值的工作是：

1. 真机校准
2. 视觉闭环
3. 动态离场跟随

## 推荐给技术同学的阅读顺序

1. [`docs/Mira Light 展位交互方案2.pdf`](/Users/Zhuanz/Documents/Github/Mira-Light/docs/Mira%20Light%20展位交互方案2.pdf)
2. [`docs/ESP32 智能台灯.pdf`](/Users/Zhuanz/Documents/Github/Mira-Light/docs/ESP32%20智能台灯.pdf)
3. [`scripts/scenes.py`](/Users/Zhuanz/Documents/Github/Mira-Light/scripts/scenes.py)
4. 本文档对应场景章节
5. [`docs/mira-light-pdf2-engineering-handoff.md`](/Users/Zhuanz/Documents/Github/Mira-Light/docs/mira-light-pdf2-engineering-handoff.md)

## 一句话总结

`mira-light-booth-scene-table.md` 负责讲“演什么”，`scripts/scenes.py` 负责讲“怎么执行”，本文和 handoff / audit 文档负责讲“为什么这么写”。技术同学如果要继续开发，应该优先盯住 `scripts/scenes.py` 和 release docs。 
