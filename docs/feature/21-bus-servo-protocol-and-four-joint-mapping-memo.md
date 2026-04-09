# Bus Servo Protocol and Four-Joint Mapping Memo

## Purpose

这份备忘文档用于把三件原本分散的信息压到一处：

- `Mira Light 展位交互方案5.pdf` 里对动作与情绪的导演层要求
- 仓库当前已经形成的 `servo1 ~ servo4` 场景控制语义
- 新提供的 270 度总线舵机串口协议格式

它的目标不是替代运行时代码，而是给后续真正接总线舵机时提供一份统一的工程口径。

这份文档最适合作为下面几类工作的前置备忘：

- 把当前 mock / HTTP 控制链迁移到总线舵机协议
- 为四个关节建立真实硬件 ID 与中位映射
- 把 `方案5` 的动作稿落成可下发的总线字符串
- 给 OpenClaw、bridge、runtime 和真实硬件接线方共享同一套术语

## Why This Memo Matters

当前仓库的 scene choreography 已经相当完整，但底层控制面还主要是这一套 mock / HTTP 语义：

```json
{"mode":"absolute","servo1":90,"servo2":96,"servo3":98,"servo4":90}
```

也就是说，仓库今天最稳定的“动作真值”是：

- `servo1 ~ servo4`
- `pose()`
- `absolute()`
- `nudge()`

而你现在补充的真实硬件协议真值则是：

```text
#000P1500T1000!
```

如果没有一层明确的协议说明和映射规则，后面很容易出现三种“真值彼此打架”的问题：

- 导演稿说的是“抬头、低头、目送、蹭蹭”
- 仓库说的是 `servo1 ~ servo4`
- 硬件实际收的是 `#IDPxxxxTxxxx!`

这份文档的作用，就是把这三层先统一起来。

## The Canonical Bus-Servo Command Format

单舵机指令格式：

```text
#000P1500T1000!
```

字段含义：

- `#`：固定前缀
- `000`：舵机 ID，范围 `000-254`，必须补足 3 位
- `P1500`：PWM 目标值，范围 `0500-2500`，必须补足 4 位
- `T1000`：时间值，范围 `0000-9999`，单位毫秒，必须补足 4 位
- `!`：固定结束符

多个舵机同时控制时，整条命令需要包在 `{}` 中：

```text
{#000P1602T1000!#001P2500T0000!#002P1500T1000!}
```

这表示：

- 可以把多个舵机的目标在同一条指令里同时下发
- 多条舵机控制组合时必须加 `{}`，单条时不需要

## Protocol Rules That Must Not Drift

### 1. ID must always be 3 digits

例如：

- 舵机 `3` 必须写成 `003`
- 不能写成 `#3P1500T1000!`

### 2. PWM must always be 4 digits

例如：

- `800` 必须写成 `P0800`
- `2500` 写成 `P2500`

### 3. Time must always be 4 digits

例如：

- `500 ms` 必须写成 `T0500`
- `0 ms` 必须写成 `T0000`

### 4. The documented physical range is 270 degrees

当前你给出的协议约定是：

- `P0500 ~ P2500` 对应总计 `270°` 物理行程
- `P1500` 为中位
- 轴朝向自己时：
  - `1500 -> 2500` 表示逆时针
  - `1500 -> 0500` 表示顺时针

这条方向约定非常重要，但也必须提醒一句：

> 真实装配后，每个关节都可能因为连杆方向和安装朝向不同而需要单独反向。

所以这条物理方向规则在软件里不应被硬编码成“所有关节统一正负方向”，而应成为每个关节的一项配置。

## Recommended Software Meaning of The Four Joints

仓库当前对 `servo1 ~ servo4` 的工程语义已经相对稳定，主要来自：

- [../mira-light-scene-implementation-index.md](../mira-light-scene-implementation-index.md)
- [../openclaw-esp32-control-guide.md](../openclaw-esp32-control-guide.md)
- [../../Mira_Light_Released_Version/docs/esp32-smart-lamp-delivery-spec.md](../../Mira_Light_Released_Version/docs/esp32-smart-lamp-delivery-spec.md)

当前最适合继续沿用的语义是：

| 逻辑字段 | 当前工程语义 | 常见用途 |
| --- | --- | --- |
| `servo1` | 底座转向 | 看向左/右、扫视、目送、跟随 |
| `servo2` | 下臂抬升 | 起身、降臂、整体抬高或压低 |
| `servo3` | 前段关节 / 中间关节前探与抬升 | 探头、回缩、往前顶、保持工作位 |
| `servo4` | 灯头俯仰 / 微表情 | 点头、低头、抬头、害羞、抖毛 |

这意味着：

- `方案5` 里的“目送”首先会影响 `servo1`
- “整体升起 / 下降”主要影响 `servo2`
- “探出来 / 缩回来 / 往前蹭”主要影响 `servo3`
- “点头 / 低头 / 害羞 / 微微抬头”主要影响 `servo4`

## The Most Important Engineering Boundary

**逻辑关节名** 和 **总线舵机 ID** 不是一回事。

也就是说：

- `servo1` 不应该直接等于总线 ID `001`
- `servo2` 也不应该被假定为 `002`

更稳妥的做法是引入一层独立映射：

```json
{
  "servo1": {"id": "000", "neutralPwm": 1500, "invert": false},
  "servo2": {"id": "001", "neutralPwm": 1500, "invert": true},
  "servo3": {"id": "002", "neutralPwm": 1500, "invert": false},
  "servo4": {"id": "003", "neutralPwm": 1500, "invert": true}
}
```

真正应该长期稳定的是：

- 场景层使用 `servo1 ~ servo4`
- 硬件层再把它翻译成 bus-servo ID

这样以后改接线、改 ID、改方向，不需要回头重写所有场景。

## Recommended Adapter Layer

### 1. Keep the choreography layer unchanged

建议继续保留当前仓库的 scene 原语：

- `pose("neutral")`
- `absolute(servo1=..., servo2=..., servo3=..., servo4=...)`
- `nudge(servo4=5)`

原因很简单：

- 这层已经被 `方案2 / 方案3 / 方案5` 的动作整理、mock 设备、runtime、安全层和测试覆盖反复使用
- 如果此时直接把 scene 层改成 `#000P1500T1000!`，会让 scene 可读性和可维护性大幅下降

### 2. Add a dedicated bus-servo translator under the device layer

推荐增加一层专门负责：

- `logical servo angle -> pwm`
- `relative nudge -> absolute target -> pwm`
- `multi-servo payload -> {...}` 字符串拼接

这层最适合位于：

- release 版可以放在 `Mira_Light_Released_Version/scripts/`
- 主仓可以放在 `scripts/`

更具体一点，它应该只做下面几件事：

- 读取四关节配置
- 计算每个关节目标 PWM
- 生成总线指令串
- 决定是否单条还是多条包在 `{}` 中
- 把 `Txxxx` 统一写进去

## Recommended Conversion Formula

如果继续沿用当前仓库的 `servo1 ~ servo4 = 0~180` 逻辑角度语义，而真实舵机是 `270°` / `P0500~P2500`，建议使用“以中位为锚”的转换方式，而不是把 `0~180` 直接线性映射到 `0500~2500`。

推荐的思路是：

```text
logical angle delta = logical_angle - logical_neutral
physical pwm delta = (logical angle delta / 135.0) * 1000
target pwm = neutral_pwm + direction_sign * physical pwm delta
```

这里的关键参数应该按关节配置，而不是写死：

- `logical_neutral`
- `neutral_pwm`
- `direction_sign`
- `pwm_min`
- `pwm_max`

对于当前仓库默认姿态，常见中位大致是：

- `servo1 = 90`
- `servo2 = 96`
- `servo3 = 98`
- `servo4 = 90`

这意味着：

```text
servo1 absolute 90 -> P1500
servo1 absolute 106 -> P1500 + (16 / 135) * 1000
servo1 absolute 78  -> P1500 - (12 / 135) * 1000
```

这个公式比“把 0~180 直接映射到 0500~2500”更适合当前仓库，因为仓库里真正稳定的动作语义是“围绕中位做表情和姿态变化”。

## Absolute and Relative Should Be Treated Differently

### Absolute

当前 runtime / scene 层的绝对控制：

```json
{"mode":"absolute","servo1":106,"servo2":96,"servo3":100,"servo4":92}
```

推荐翻译流程：

1. 先把每个逻辑角度转成目标 PWM
2. 再按总线 ID 排序
3. 生成多舵机串

例如：

```text
{#000P1619T0420!#001P1500T0420!#002P1515T0420!#003P1515T0420!}
```

这里的数值只是示意，真实值必须以每个关节的中位和方向配置为准。

### Relative

当前仓库大量使用：

```json
{"mode":"relative","servo4":5}
```

总线舵机协议本身没有“相对增量”字段，所以相对动作必须在软件里先展开成绝对目标。

推荐流程：

1. 读取当前已知逻辑角度
2. 算出目标逻辑角度
3. 走安全层校验 / clamp
4. 再换算成 PWM
5. 生成总线指令

这也是为什么当前仓库已经补上的 `estimatedServoState` 和安全层很重要：

- 没有当前位置，就不应该盲算相对控制

## Bus Command Examples for Four-Joint Scenes

### Neutral pose

当前场景层常见的 neutral：

```json
{"mode":"absolute","servo1":90,"servo2":96,"servo3":98,"servo4":90}
```

推荐总线拼接形式：

```text
{#000P1500T1000!#001P1500T1000!#002P1500T1000!#003P1500T1000!}
```

这里隐含的前提是：

- 四个关节都已经完成各自 neutral 校准
- 当前示例为了说明格式，先把 neutral 都写成 `1500`

### Farewell looking left

当前 release 版动态 `farewell` 左侧目送的第一段逻辑姿态是：

```json
{"mode":"absolute","servo1":78,"servo2":96,"servo3":100,"servo4":92}
```

它对应的是：

- `servo1` 明显向左偏
- `servo2` 保持常规高度
- `servo3` 轻微前探
- `servo4` 微微低头

总线层应该把它翻译成一条四关节同步命令，而不是四条分散命令。

### Farewell nodding wave

当前 release 版 `farewell` 里的“挥手”实际上是 `servo4` 的相对点头序列：

```json
{"mode":"relative","servo4":5}
{"mode":"relative","servo4":-10}
{"mode":"relative","servo4":5}
```

总线层落地时必须先把这三步展开成：

- 当前 `servo4` 的绝对逻辑角度
- 目标绝对逻辑角度
- 对应 PWM

然后再分别发成：

```text
#003PxxxxT0180!
#003PyyyyT0180!
#003PzzzzT0220!
```

### Track target

`方案5` 第 7 段强调的是：

- 灯头下降
- 跟着书移动
- 停下来就停
- 再移动就再跟

当前仓库里这层已经拆成：

- `track_target_event_extractor.py` 输出 `control_hint`
- `vision_runtime_bridge.py` 负责节流和路由
- `mira_light_runtime.py` 把 `control_hint` 变成四关节平滑控制

如果接总线协议，最重要的不是“再重新设计 tracking”，而是把 runtime 最终算出来的四关节绝对目标，稳定转成总线多关节同步串。

## Which Scenes in Scheme 5 Depend Most on Four-Joint Coordination

根据 `方案5`，最依赖四关节姿态协调的主场景包括：

### 1. 起床

核心是：

- `servo2 / servo3` 整体升起
- `servo4` 抬头
- `servo1 + servo4` 做抖毛

### 2. 好奇你是谁

核心是：

- `servo1` 缓慢靠向评委
- `servo4` 摇头、低头、上下灯头
- `servo3` 做探头与回缩

### 3. 摸一摸

核心是：

- `servo3` 前探蹭手
- `servo2` 往下走
- `servo1` 跟一下手离开的方向

### 4. 追踪

核心是：

- `servo1` 左右跟随
- `servo2 / servo3 / servo4` 根据目标位置和距离做细调

### 5. 跳舞模式

核心是：

- 四关节一起做上下摇和左右摆
- 节奏比单关节动作更重要

### 6. 挥手送别

核心是：

- `servo1` 先目送离场方向
- `servo4` 两次点头式挥手
- `servo1 + servo4` 收尾低头

### 7. 睡觉

核心是：

- `servo4` 慢慢低头
- `servo2 / servo3` 降下去并蜷缩

## Current Repository Files That Already Define Four-Joint Posture

### Core scripts

- [../../Mira_Light_Released_Version/scripts/scenes.py](../../Mira_Light_Released_Version/scripts/scenes.py)
- [../../Mira_Light_Released_Version/scripts/mira_light_runtime.py](../../Mira_Light_Released_Version/scripts/mira_light_runtime.py)
- [../../Mira_Light_Released_Version/scripts/mira_light_safety.py](../../Mira_Light_Released_Version/scripts/mira_light_safety.py)
- [../../Mira_Light_Released_Version/scripts/vision_runtime_bridge.py](../../Mira_Light_Released_Version/scripts/vision_runtime_bridge.py)
- [../../Mira_Light_Released_Version/scripts/track_target_event_extractor.py](../../Mira_Light_Released_Version/scripts/track_target_event_extractor.py)
- [../../Mira_Light_Released_Version/scripts/booth_controller.py](../../Mira_Light_Released_Version/scripts/booth_controller.py)
- [../../Mira_Light_Released_Version/scripts/calibrate_lamp.py](../../Mira_Light_Released_Version/scripts/calibrate_lamp.py)

### Mock and rehearsal scripts

- [../../scripts/mock_mira_light_device.py](../../scripts/mock_mira_light_device.py)
- [../../scripts/mock_lamp_server.py](../../scripts/mock_lamp_server.py)
- [../../scripts/run_mock_lamp.sh](../../scripts/run_mock_lamp.sh)
- [../../scripts/run_mira_light_offline_rehearsal.py](../../scripts/run_mira_light_offline_rehearsal.py)

### Tests that currently protect posture behavior

- [../../Mira_Light_Released_Version/tests/test_dynamic_farewell.py](../../Mira_Light_Released_Version/tests/test_dynamic_farewell.py)
- [../../Mira_Light_Released_Version/tests/test_vision_runtime_bridge.py](../../Mira_Light_Released_Version/tests/test_vision_runtime_bridge.py)
- [../../Mira_Light_Released_Version/tests/test_release_safety.py](../../Mira_Light_Released_Version/tests/test_release_safety.py)
- [../../tests/test_mock_device_e2e.py](../../tests/test_mock_device_e2e.py)

## Current Repository Docs That Already Explain Four-Joint Control

- [../mira-light-scene-implementation-index.md](../mira-light-scene-implementation-index.md)
- [../mira-light-booth-scene-table.md](../mira-light-booth-scene-table.md)
- [../mira-light-scene-to-code-spec.md](../mira-light-scene-to-code-spec.md)
- [../mira-light-booth-scene-capability-implementation-plan.md](../mira-light-booth-scene-capability-implementation-plan.md)
- [../../Mira_Light_Released_Version/docs/openclaw-esp32-control-guide.md](../../Mira_Light_Released_Version/docs/openclaw-esp32-control-guide.md)
- [../../Mira_Light_Released_Version/docs/esp32-smart-lamp-delivery-spec.md](../../Mira_Light_Released_Version/docs/esp32-smart-lamp-delivery-spec.md)
- [../Mira Light 展位交互方案5.pdf](../Mira%20Light%20%E5%B1%95%E4%BD%8D%E4%BA%A4%E4%BA%92%E6%96%B9%E6%A1%885.pdf)

## Recommended Next Step

下一步最应该做的是新增一层“总线舵机协议适配器”，而不是重写 scene choreography。

推荐顺序：

1. 新增关节映射配置文件  
字段至少包括：`id`、`neutralPwm`、`invert`、`pwmMin`、`pwmMax`

2. 新增协议转换脚本  
把 `servo1 ~ servo4` 的绝对 / 相对控制翻译成 bus-servo 字符串

3. 先接 mock-compatible runtime  
让 runtime 先同时支持：
   - mock HTTP `/control`
   - bus-servo protocol 输出

4. 先校准 neutral / farewell / sleep 三组关键姿态  
这三组最容易暴露方向反转、连杆限制和中位偏差

5. 再用 `track_target` 做连续控制调优  
因为 tracking 最能暴露节流、抖动和平滑性问题

## One-Sentence Summary

`方案5` 已经把“做什么动作”说清楚了，仓库也已经把大部分动作落成了 `servo1 ~ servo4` choreography；现在真正缺的是把这套四关节逻辑，稳定翻译成你提供的 bus-servo 协议，并为每个关节建立真实硬件 ID、中位、方向和边界配置。
