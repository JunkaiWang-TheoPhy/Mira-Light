# Mira Light 自然语言到代码功能翻译说明

## 文档目的

注意：

当前仓库里的“动作真值”已经切换到 [`Mira Light 展位交互方案2.pdf`](/Users/Zhuanz/Documents/Github/Mira-Light/docs/Mira%20Light%20展位交互方案2.pdf)。

本文件仍然有价值，但现在更适合作为：

- 自然语言到代码的翻译方法说明
- 原语库设计思路说明

而不是当前排练版动作的唯一依据。

当前实现状态与审计结果请优先对照：

- [`docs/mira-light-pdf2-implementation-audit.md`](/Users/Zhuanz/Documents/Github/Mira-Light/docs/mira-light-pdf2-implementation-audit.md)
- [`docs/mira-light-pdf2-engineering-handoff.md`](/Users/Zhuanz/Documents/Github/Mira-Light/docs/mira-light-pdf2-engineering-handoff.md)

[`Mira Light 展位交互方案.pdf`](/Users/Zhuanz/Documents/Github/Mira-Light/docs/Mira%20Light%20展位交互方案.pdf) 里的内容大多是自然语言描述，例如：

- “像小动物刚醒来抖抖毛”
- “有点好奇又有点怯”
- “靠过去蹭评委的手”
- “像走神了一样发呆”

这些表达很适合讲体验，但不能直接交给工程系统执行。

因此，第一步必须做的事情就是：

> 把自然语言翻译成代码功能。

更具体地说，就是把“情绪与画面感”拆成：

- 可触发的事件
- 可识别的状态
- 可执行的动作原语
- 可调参数
- 可组合的场景脚本

## 一句话原则

自然语言不直接变成代码。

它要先经过这条翻译链：

```text
自然语言描述
-> 交互意图
-> 系统事件
-> 场景状态
-> 动作原语
-> 设备 API 调用
```

例如：

```text
"像小动物醒来"
-> 意图：表达苏醒与欢迎
-> 事件：检测到有人靠近
-> 状态：wake_up
-> 动作原语：亮微光 / 抬臂 / 小抖动 / 伸懒腰
-> API：POST /led + POST /control + POST /action
```

## 为什么这一步必须先做

如果不先翻译，后面会出现三个问题：

### 1. 讲得很美，但写不出程序

例如“有点害羞地看你”这种话，如果不拆成具体动作，程序员不知道应该：

- 转头多少度
- 停顿多久
- 是否要回缩
- 是否要点头
- 灯光要不要变暖

### 2. 每个人理解都不一样

设计同学理解的“好奇”可能是歪头，工程同学理解的“好奇”可能是转头，主持人理解的“好奇”可能是点头。

如果不统一成代码功能，现场效果会非常飘。

### 3. 无法排练、复现和验收

自然语言描述很难验收。  
代码功能就可以验收，例如：

- 检测到人靠近后，`1.5s` 内进入 `wake_up`
- `wake_up` 包含 `breathing -> lift -> shake -> stretch`
- 动作总时长 `4.5s`

## 翻译方法总览

建议把 PDF 里的自然语言拆成 5 层。

### 第 1 层：情绪目标

这是设计想传达的东西，例如：

- 苏醒
- 好奇
- 害羞
- 亲近
- 卖萌
- 走神
- 提醒
- 开心
- 不舍

### 第 2 层：交互意图

这是系统要做的事情，例如：

- 欢迎来人
- 观察目标
- 主动靠近
- 躲避后再观察
- 表达开心
- 表达提醒
- 表达送别

### 第 3 层：系统状态

这是程序里的状态机节点，例如：

- `sleep`
- `wake_up`
- `curious_observe`
- `touch_affection`
- `track_target`
- `idle_daydream`
- `remind_standup`
- `celebrate_dance`
- `farewell`

### 第 4 层：动作原语

这是可复用的小动作单元，例如：

- `led_breath_in`
- `led_warm_glow`
- `joint_raise_arm`
- `joint_head_tilt_left`
- `joint_head_tilt_right`
- `joint_nod_once`
- `joint_shake_once`
- `joint_retract`
- `joint_extend`
- `joint_follow_x`
- `pose_folded`
- `pose_normal`

### 第 5 层：设备 API 调用

这是当前 ESP32 已有的接口能力，例如：

- `POST /led`
- `POST /control`
- `POST /action`
- `POST /action/stop`
- `POST /reset`

## 先明确：当前硬件和 API 真正能做什么

根据 [`ESP32 智能台灯.pdf`](/Users/Zhuanz/Documents/Github/Mira-Light/docs/ESP32%20智能台灯.pdf) 与 [`danpianji.html`](/Users/Zhuanz/Documents/Github/Mira-Light/docs/danpianji.html)，当前已经明确可调用的能力有：

### 关节能力

- `servo1`
- `servo2`
- `servo3`
- `servo4`

控制方式：

- `relative`
- `absolute`

### 灯光能力

- `off`
- `solid`
- `breathing`
- `rainbow`
- `rainbow_cycle`

### 预设动作能力

- `nod`
- `shake`
- `wave`
- `dance`
- `stretch`
- `curious`

所以自然语言翻译时，优先要往这些现成能力上靠。  
如果自然语言超出了现有 API，就要记为“二期功能”。

## 动作原语库应该怎么定义

这是整个系统最重要的中间层。

建议先不要直接把每个场景写死，而是先建一个“动作原语库”。

每个原语应该包含：

- 原语名
- 作用说明
- 输入参数
- 调用哪些设备接口
- 默认时长

下面是一份适合当前项目的最小原语库示例。

### 灯光原语

| 原语名 | 作用 | 典型实现 |
| --- | --- | --- |
| `light_dim_warm` | 微暖光亮起 | `POST /led` with `solid` low brightness |
| `light_breath_warm` | 暖色呼吸 | `POST /led` with `breathing` |
| `light_focus_white` | 桌面照明白光 | `POST /led` with bright `solid` |
| `light_disco` | 跳舞灯效 | `POST /led` with `rainbow_cycle` |
| `light_sleep_fade` | 慢慢变暗 | 多次调用 `/led` 降亮度 |

### 姿态原语

| 原语名 | 作用 | 典型实现 |
| --- | --- | --- |
| `pose_sleep` | 蜷缩姿态 | `POST /control` 设置 4 关节默认睡姿 |
| `pose_normal` | 正常站姿 | `POST /control` 设置正常位 |
| `pose_curious_half_turn` | 半转头观察 | 单独调整头部相关关节 |
| `pose_head_tilt_left` | 左歪头 | 调整灯头关节 |
| `pose_head_tilt_right` | 右歪头 | 调整灯头关节 |
| `pose_retract` | 微微后缩 | 某个关节负向调整 |
| `pose_extend` | 微微前探 | 某个关节正向调整 |

### 表情性动作原语

| 原语名 | 作用 | 典型实现 |
| --- | --- | --- |
| `act_nod` | 点头 | `POST /action {"name":"nod"}` |
| `act_shake` | 摇头 | `POST /action {"name":"shake"}` |
| `act_wave` | 打招呼 | `POST /action {"name":"wave"}` |
| `act_stretch` | 伸懒腰 | `POST /action {"name":"stretch"}` |
| `act_curious` | 好奇张望 | `POST /action {"name":"curious"}` |
| `act_dance` | 跳舞 | `POST /action {"name":"dance"}` |

### 组合行为原语

| 原语名 | 作用 | 典型实现 |
| --- | --- | --- |
| `micro_shiver` | 抖两下 | 用 `/control` 做两个来回小幅相对动作 |
| `gentle_follow` | 平滑跟随 | 根据目标位置循环发 `/control` |
| `pawing_bump` | 蹭蹭 | 前探、回收、前探的序列 |
| `sleepy_drop_and_bounce` | 打瞌睡后惊醒 | 逐步低头再快速抬回 |

## 如何把 PDF 场景翻译成代码功能

下面按场景逐个翻译。

## 场景 1：起床

### 自然语言

“从蜷缩起来的状态起来，抖一抖的感觉。”

### 翻译后的交互意图

- 检测有人来了
- 从睡眠态切到欢迎态
- 表达“醒来”而不是“突然启动”

### 翻译后的代码功能

- 触发事件：`person_detected_near`
- 前置状态：`sleep`
- 目标状态：`wake_up`
- 动作序列：
  - `light_dim_warm`
  - `joint_raise_arm`
  - `micro_shiver`
  - `act_stretch`
  - `pose_normal`

### 适合写成的函数

```python
def scene_wake_up():
    light_dim_warm()
    arm_raise_slow()
    micro_shiver(times=2)
    run_action("stretch")
    pose_normal()
```

### 依赖

- 人体接近检测，或由 `OpenClaw` / 电脑终端直接触发

## 场景 2：好奇你是谁

### 自然语言

“先转过去一半，停一下，再慢慢转过去。歪头看你，然后轻轻点一下头。”

### 翻译后的交互意图

- 不是冷冰冰地直视
- 而是有试探、停顿、好奇和礼貌

### 翻译后的代码功能

- 触发事件：`person_in_front`
- 目标状态：`curious_observe`
- 动作序列：
  - `pose_curious_half_turn`
  - `delay(500ms)`
  - `turn_to_target_full`
  - `pose_head_tilt_left`
  - `delay(2000ms)`
  - `act_nod`

### 适合写成的函数

```python
def scene_curious_observe(target):
    turn_to_target(target, ratio=0.5)
    delay_ms(500)
    turn_to_target(target, ratio=1.0)
    head_tilt("left", hold_ms=2000)
    run_action("nod")
```

### 依赖

- 目标方向估计
- 最低也可人工指定“向左/向右看”

## 场景 3：摸一摸

### 自然语言

“灯头靠过去蹭评委的手，在手掌下小幅左右摆动。手拿开后追一下。”

### 翻译后的交互意图

- 表达亲近
- 表达被触摸时的舒适感
- 表达意犹未尽

### 翻译后的代码功能

- 触发事件：`hand_near_head` 或 `touch_detected`
- 目标状态：`touch_affection`
- 动作序列：
  - `light_breath_warm`
  - `pose_extend`
  - `small_rub_motion`
  - `follow_hand_short`
  - `pose_normal`

### 适合写成的函数

```python
def scene_touch_affection(hand_target):
    set_led(mode="solid", color=warmest_color(), brightness=180)
    extend_toward(hand_target)
    rub_motion(amplitude=small, loops=3)
    follow_target_once(hand_target)
    pose_normal()
```

### 依赖

- 手部位置检测，或人工触发

## 场景 4：卖萌

### 自然语言

“左歪一下右歪一下，像小狗歪头看你。或者探头、缩回、再探头。”

### 翻译后的交互意图

- 卖萌
- 表达研究你
- 表达胆小但好奇

### 翻译后的代码功能

- 状态：`cute_probe`
- 动作原语：
  - `pose_head_tilt_left`
  - `pose_head_tilt_right`
  - `pose_extend`
  - `pose_retract`

### 适合写成的函数

```python
def scene_cute_probe():
    head_tilt("left", hold_ms=1200)
    head_tilt("right", hold_ms=1200)
```

或者：

```python
def scene_timidscout():
    extend_forward()
    delay_ms(800)
    retract_fast()
    delay_ms(300)
    extend_forward()
```

## 场景 5：发呆

### 自然语言

“突然看向一个莫名其妙的方向，停 3-4 秒，然后快速回神。”

### 翻译后的交互意图

- 表达走神
- 表达“不是机械执行器，而是有自己的节奏”

### 翻译后的代码功能

- 触发事件：`idle_timeout`
- 状态：`idle_daydream`
- 动作序列：
  - `look_random_direction`
  - `hold(3000~4000ms)`
  - `snap_back_to_normal`

### 适合写成的函数

```python
def scene_daydream():
    look_random_direction()
    delay_ms(random_between(3000, 4000))
    snap_back_to_normal()
```

另一种“打瞌睡”版本：

```python
def scene_sleepy_nod():
    lower_head_gradually()
    bounce_back_fast()
```

## 场景 6：久坐检测蹭蹭

### 自然语言

“先往里收再往前顶，蹭蹭、蹭蹭、蹭蹭。评委问是不是要我起来，Mira 点两次头。”

### 翻译后的交互意图

- 提醒
- 但提醒方式要可爱，不是冷冰冰警报

### 翻译后的代码功能

- 触发事件：`sedentary_detected`
- 状态：`remind_standup`
- 动作序列：
  - `pawing_bump(loops=3)`
  - `act_nod` twice
  - 若收到否定 -> `act_shake`

### 适合写成的函数

```python
def scene_standup_reminder():
    pawing_bump(loops=3)
    run_action("nod")
    run_action("nod")
```

## 场景 7：追踪书本

### 自然语言

“书从左移到右，灯头跟着书移动，光照始终跟着书。”

### 翻译后的交互意图

- 展示视觉感知
- 展示它看得见，不只是随机动

### 翻译后的代码功能

- 触发事件：`tracked_object_moved`
- 输入数据：`target_x`, `target_y`
- 状态：`track_target`
- 动作功能：
  - `gentle_follow(target_x)`
  - 灯头朝目标方向修正
  - 光照中心同步跟随

### 适合写成的函数

```python
def scene_track_target(target):
    while tracking_active():
        update_head_follow(target)
        update_beam_focus(target)
```

### 依赖

- 摄像头检测或简化目标跟踪模块

## 场景 8：拿到 offer 跳舞

### 自然语言

“往左上、右上、上下、左右反复摇摆，灯光 disco，音乐停后慢慢减速。”

### 翻译后的交互意图

- 表达极度开心
- 这是全场最强烈的情绪输出

### 翻译后的代码功能

- 触发事件：`celebration_triggered`
- 状态：`celebrate_dance`
- 动作序列：
  - `light_disco`
  - `act_dance`
  - 播放音乐
  - `decelerate_to_normal`

### 适合写成的函数

```python
def scene_celebrate():
    set_led(mode="rainbow_cycle", brightness=220)
    play_music("dance.mp3")
    run_action("dance", loops=2)
    slow_return_to_normal()
```

## 场景 9：挥手送别

### 自然语言

“灯头跟着评委离开的方向转，像目送你。然后快速左右摆两下，像在说拜拜。”

### 翻译后的交互意图

- 目送
- 不舍
- 礼貌结束

### 翻译后的代码功能

- 触发事件：`person_leaving`
- 状态：`farewell`
- 动作序列：
  - `follow_departing_direction`
  - `act_wave`
  - `head_lower_slightly`

### 适合写成的函数

```python
def scene_farewell(target):
    follow_target_once(target)
    run_action("wave")
    head_lower_gently()
```

## 场景 10：睡觉

### 自然语言

“慢慢低头，灯臂降下去，先舒展一下再蜷缩，最后微光。”

### 翻译后的交互意图

- 从活跃退回待机
- 用动作表达“今天结束了”

### 翻译后的代码功能

- 触发事件：`no_person_timeout`
- 状态：`go_to_sleep`
- 动作序列：
  - `act_stretch`
  - `pose_sleep`
  - `light_sleep_fade`

### 适合写成的函数

```python
def scene_sleep():
    run_action("stretch")
    pose_sleep()
    fade_to_dim()
```

## 补充交互如何翻译成代码功能

PDF 后面那些“补充交互”里，有些能进一期，有些应该先记成二期。

## 可进入一期的

### 多人反应

自然语言：
“两个评委同时在，Mira 在两个人之间来回看，最后选一个面对。”

可翻译为：

- 输入：多个目标方位
- 功能：`select_primary_target()`
- 原语：`scan_between_targets()`

示例函数：

```python
def scene_multi_person_attention(targets):
    scan_targets(targets)
    face_target(select_primary_target(targets))
```

### 语音理解展示

自然语言：
“今天好累啊” -> 低头、暖光、缓慢呼吸

可翻译为：

- 事件：`speech_emotion_detected = tired`
- 状态：`comfort_response`
- 动作：
  - 低头
  - 暖色呼吸

## 建议放到二期的

这些不是不能做，而是当前单片机公开 API 还不够，需要新增传感器或上层系统。

- 叹气检测
- 真实语音理解
- 触摸调光
- 心跳模拟
- 自动天气映射
- 社交点赞提醒
- 无线充电底座响应

## 代码层真正要定义的 4 类对象

把自然语言翻译完之后，代码里建议至少有下面 4 类对象。

## 1. Event 事件

例如：

```python
person_detected_near
person_in_front
hand_near
touch_detected
target_moved
idle_timeout
person_leaving
celebration_triggered
speech_emotion_detected
```

## 2. State 状态

例如：

```python
sleep
wake_up
curious_observe
touch_affection
cute_probe
idle_daydream
track_target
celebrate_dance
farewell
```

## 3. Primitive 原语

例如：

```python
set_led(...)
run_action(...)
move_servo(...)
pose_normal()
pose_sleep()
head_tilt(...)
extend_forward()
retract_fast()
fade_to_dim()
```

## 4. Scene 场景

例如：

```python
scene_wake_up()
scene_curious_observe()
scene_touch_affection()
scene_track_target()
scene_celebrate()
scene_farewell()
scene_sleep()
```

## 推荐的数据结构

建议不要把所有逻辑都写死在代码里，而是把场景写成配置。

例如：

```yaml
wake_up:
  trigger: person_detected_near
  start_state: sleep
  end_state: curious_observe
  steps:
    - primitive: light_breath_warm
      args:
        brightness: 60
    - primitive: arm_raise_slow
    - primitive: micro_shiver
      args:
        times: 2
    - primitive: act_stretch
    - primitive: pose_normal
```

这样以后改动作，不需要反复改主程序。

## 你下一步真正应该做什么

如果按工程顺序推进，建议这样做。

### 第一步：建立“动作原语表”

把所有可复用动作先命名出来，不要直接写完整场景。

### 第二步：为 PDF 场景建立“翻译表”

把每个自然语言场景翻译成：

- 触发事件
- 进入状态
- 动作原语序列
- 结束状态

### 第三步：区分一期与二期

一期：

- 起床
- 好奇
- 卖萌
- 摸一摸
- 追踪
- 跳舞
- 送别
- 睡觉

二期：

- 叹气检测
- 语音理解
- 多人反应
- 触摸调光
- 社交提醒
- 天气映射

### 第四步：先做“手动可触发”的场景

先别一开始全自动。

先用 `OpenClaw` 或电脑终端，确保每个场景都能稳定触发。

推荐的最小触发方式是：

```bash
python3 scripts/booth_controller.py --base-url tcp://192.168.31.10:9527 wake_up
python3 scripts/booth_controller.py --base-url tcp://192.168.31.10:9527 curious_observe
python3 scripts/booth_controller.py --base-url tcp://192.168.31.10:9527 celebrate
```

如果未来接入 `OpenClaw`，推荐方式也不是额外发明一套触发器，而是让 `OpenClaw` 最终调用这同一条终端命令。

### 第五步：再加自动触发

只有当场景稳定之后，再接入：

- 摄像头
- 触摸传感器
- 麦克风
- 视觉跟踪

## 当前阶段最重要的结论

根据 [`Mira Light 展位交互方案.pdf`](/Users/Zhuanz/Documents/Github/Mira-Light/docs/Mira%20Light%20展位交互方案.pdf)，第一步不是直接写展位控制脚本，而是先建立一套“自然语言到代码功能”的翻译层。

可以把这件事压缩成一句话：

> “像小动物一样醒来”不是代码；代码应该是 `person_detected_near -> wake_up -> light_breath_warm + arm_raise_slow + micro_shiver + act_stretch`。

只有先把这一层做出来，后面的附件准备、脚本编排、现场触发和排练才会真正稳定。
