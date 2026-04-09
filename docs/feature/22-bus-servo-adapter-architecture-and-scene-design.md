# Bus Servo Adapter Architecture and Scene Design

## Purpose

这份文档解决两个紧挨着的问题：

- 总线舵机协议适配层应该怎么分层，才能不破坏当前已经稳定的 `scene -> runtime -> safety` 结构
- `Mira Light 展位交互方案5.pdf` 对应的 10 个主场景，落到四个关节时应该怎样设计

它不是协议备忘的重复版；协议格式本身已经整理在：

- [21-bus-servo-protocol-and-four-joint-mapping-memo.md](./21-bus-servo-protocol-and-four-joint-mapping-memo.md)

这份文档更偏工程实现：怎么接、接在哪、每个场景怎么拆。

## Current Stable Boundary

当前仓库里已经稳定的真值边界其实很清楚：

- scene 原语：[`pose()` / `absolute()` / `nudge()`](../../Mira_Light_Released_Version/scripts/scenes.py)
- 运行时执行：[`BoothController.run_step()`](../../Mira_Light_Released_Version/scripts/mira_light_runtime.py)
- 安全护栏：[`MiraLightSafetyController`](../../Mira_Light_Released_Version/scripts/mira_light_safety.py)
- 动态场景：[`build_scene()` 和 `farewell` 动态版本](../../Mira_Light_Released_Version/scripts/scenes.py)
- 实时跟随：[`apply_tracking_event()`](../../Mira_Light_Released_Version/scripts/mira_light_runtime.py)

这意味着最稳妥的方向不是重写 `scenes.py`，而是把总线舵机适配器放在：

`安全层之后，设备 transport 之前`

也就是：

`scene -> runtime -> safety -> bus-servo adapter -> serial transport`

## Recommended File Structure

建议新增下面这组文件：

```text
Mira_Light_Released_Version/
  config/
    bus_servo_joint_map.json
    bus_servo_runtime.json
  scripts/
    bus_servo_protocol.py
    bus_servo_mapping.py
    bus_servo_adapter.py
    bus_servo_transport.py
    mira_light_device_router.py
    preview_bus_servo_command.py
  tests/
    test_bus_servo_protocol.py
    test_bus_servo_mapping.py
    test_bus_servo_adapter.py
```

职责建议如下。

### `config/bus_servo_joint_map.json`

保存四个逻辑关节到真实总线舵机的映射。

建议字段：

```json
{
  "servo1": {
    "id": "000",
    "label": "base_yaw",
    "logicalNeutral": 90,
    "logicalMin": 0,
    "logicalMax": 180,
    "neutralPwm": 1500,
    "pwmMin": 500,
    "pwmMax": 2500,
    "directionSign": 1
  }
}
```

关键点：

- `servo1 ~ servo4` 是逻辑名
- `000 ~ 003` 是物理总线 ID
- `directionSign` 必须逐关节配置，不能全局写死
- `logicalNeutral` 默认可直接复用当前 `SERVO_CALIBRATION[*].neutral`

### `config/bus_servo_runtime.json`

保存适配器运行参数，而不是关节几何信息。

建议字段：

```json
{
  "transport": "serial",
  "serialPort": "/dev/tty.usbserial-0001",
  "baudRate": 115200,
  "defaultMoveMs": 220,
  "maxMoveMs": 9999,
  "inferMoveMsFromNextDelay": true,
  "relativeRequiresKnownState": true
}
```

### `scripts/bus_servo_protocol.py`

只负责协议格式化，不掺杂场景语义。

建议暴露：

```python
def format_single_command(servo_id: str, pwm: int, time_ms: int) -> str: ...
def format_multi_command(commands: list[dict[str, int | str]]) -> str: ...
def clamp_pwm(value: int, pwm_min: int = 500, pwm_max: int = 2500) -> int: ...
def clamp_time_ms(value: int, max_time_ms: int = 9999) -> int: ...
```

这层不应该知道什么是 `servo1`、什么是 `farewell`。

### `scripts/bus_servo_mapping.py`

只负责逻辑角度和 PWM 之间的转换。

建议数据结构：

```python
@dataclass
class JointMapping:
    name: str
    servo_id: str
    logical_neutral: int
    logical_min: int
    logical_max: int
    neutral_pwm: int
    pwm_min: int
    pwm_max: int
    direction_sign: int
```

建议核心方法：

```python
class BusServoMapper:
    def angle_to_pwm(self, joint_name: str, logical_angle: int) -> int: ...
    def delta_to_pwm(self, joint_name: str, current_angle: int, delta: int) -> int: ...
    def payload_to_commands(
        self,
        payload: dict[str, int | str],
        resolved_angles: dict[str, int],
        time_ms: int,
    ) -> list[dict[str, int | str]]: ...
```

### `scripts/bus_servo_transport.py`

只负责把协议字符串送出去。

建议先定义抽象接口：

```python
class BusServoTransport(Protocol):
    def send(self, command: str) -> dict[str, Any]: ...
```

然后至少准备两种实现：

- `DryRunBusServoTransport`
- `SerialBusServoTransport`

前者给测试和排练用，后者才是真的串口下发。

### `scripts/bus_servo_adapter.py`

这是最关键的一层。

它不直接理解 scene，但理解：

- 安全层决策结果
- 当前已知关节状态
- 总线协议命令

建议不要让它直接吃原始 payload，而是吃 `SafetyDecision`。原因很重要：

- 当前 safety 对 `relative` 模式输出的仍然是相对增量
- 但总线舵机最终需要的是绝对 `PWM + T`
- `SafetyDecision.state_after` 已经给出了安全层最终认可的绝对角度

所以适配器的最佳输入不是“请求前的 payload”，而是“安全层审核后的决策”。

建议接口：

```python
class BusServoAdapter:
    def apply_decision(
        self,
        decision: SafetyDecision,
        *,
        move_ms: int | None = None,
        source: str | None = None,
    ) -> dict[str, Any]: ...

    def sync_angles(self, angles: dict[str, int | None]) -> None: ...
    def last_command(self) -> str | None: ...
```

`apply_decision()` 内部做三件事：

1. 读取 `decision.state_after`
2. 把目标逻辑角度转成每个关节的目标 PWM
3. 拼成单条或多条总线字符串并下发

### `scripts/mira_light_device_router.py`

建议引入一个“设备路由器”，不要让 runtime 自己判断所有 transport 细节。

建议接口：

```python
class MotionOutput(Protocol):
    def apply_decision(self, decision: SafetyDecision, *, move_ms: int | None = None) -> dict[str, Any]: ...

class HttpMotionOutput:
    ...

class BusServoMotionOutput:
    ...

class HybridMiraLightDevice:
    def control_from_decision(self, decision: SafetyDecision, *, move_ms: int | None = None) -> dict[str, Any]: ...
    def set_led(self, payload: dict[str, Any]) -> Any: ...
    def run_action(self, payload: dict[str, Any]) -> Any: ...
    def reset(self) -> Any: ...
```

这里的核心思想是：

- “动作控制” 可以切到 bus-servo
- “灯光 / action / reset / status” 暂时仍可保留现有 HTTP mock/ESP32 路径

这样迁移风险最低。

## The Most Important Timing Design

总线舵机协议比当前 HTTP `/control` 多了一个关键字段：

- `Txxxx`

也就是运动时间。

当前 scene 系统没有显式 `move_ms`，但已经有大量：

- `absolute(...)`
- `nudge(...)`
- `delay(180)`

所以适配器必须回答一个问题：

`总线命令里的 T 应该取多少？`

### Recommended rule

第一版建议采用下面的优先级：

1. 如果 step 明确提供 `moveMs`，就用它
2. 否则如果下一步是 `delay`，就直接用这段 delay 作为 `T`
3. 否则回退到 `defaultMoveMs`

这个规则的好处是：

- 不需要立刻重写所有场景
- scene 当前的节奏感几乎可以原样保留
- 一个 `absolute(...); delay(260)` 很自然就翻成 `T0260`

### Recommended small scene API extension

建议把 scene helper 稍微扩一下：

```python
def pose(name: str, move_ms: int | None = None) -> Step: ...
def absolute(move_ms: int | None = None, **servo_values: int) -> Step: ...
def nudge(move_ms: int | None = None, **servo_values: int) -> Step: ...
```

这样：

- 旧场景不改也能跑
- 新场景或精修场景可以显式指定 `move_ms`

## Recommended Runtime Integration

当前最自然的接入点就在 [`MiraLightRuntime`](../../Mira_Light_Released_Version/scripts/mira_light_runtime.py)。

建议改法不是推翻，而是做最小替换：

1. 继续保留 `MiraLightSafetyController`
2. 让 `_run_safe_control(...)` 在拿到 `SafetyDecision` 后，不再固定调用 `client.control(...)`
3. 改为调用 `device_router.control_from_decision(decision, move_ms=...)`
4. HTTP 模式下，router 仍然内部走现有 `POST /control`
5. bus-servo 模式下，router 改走 `BusServoAdapter.apply_decision(...)`

这样 scene、导演台、vision bridge 都不需要知道底层已经换成总线舵机。

## Recommended Scene Design Template

每个场景都建议按同一个模板设计，而不是每次重新想一遍。

### 1. Anchor Pose

先定义场景开始、最高点、最低点、收尾点。

例如：

- `neutral`
- `wake_half`
- `wake_high`
- `sleep`

### 2. Primary Joints

每个场景只允许 1 到 2 个主导关节，其他关节做辅助。

这样动作才会清楚。

### 3. Emotional Accent

“情绪”应该主要靠：

- `servo4` 微表情
- `servo1` 方向意图

不要把所有情绪都靠四个关节一起大摆。

### 4. Safety Envelope

每个场景先写：

- 正常排练范围
- 绝对不能越过的范围
- 哪个关节最容易风险大

### 5. Dynamic Context

先想清楚这个场景是否应该动态化：

- `farewell`：是，按离场方向
- `track_target`：是，按实时视觉目标
- `touch_affection`：是，按来手方向
- `cute_probe`：不一定，固定版也成立

## How To Design Each Main Scene

下面这部分不是重复 scene 文案，而是给“总线舵机时代的场景设计”一个明确口径。

### `wake_up`

- 主关节：`servo2 + servo3`
- 辅关节：`servo4`
- `servo1` 只做很轻的最后定向
- 必备锚点：`sleep -> wake_half -> wake_high -> neutral`
- 总线设计重点：
  - 起身阶段 `T` 稍长，避免像弹起来
  - 抖毛阶段用短 `nudge`，但幅度很小
  - 第一阶段先调 `servo2/servo3`，最后才细调 `servo4`

### `curious_observe`

- 主关节：`servo1 + servo4`
- 辅关节：`servo3`
- 核心不是“大转身”，而是“半转停顿 + 歪头”
- 必备锚点：`neutral -> half_turn -> shy_lookaway -> curious_return`
- 总线设计重点：
  - `servo1` 变化比 `touch_affection` 更明显
  - `servo4` 要比 `servo1` 稍慢半拍，像在犹豫
  - 害羞低头时优先让 `servo4` 下压，不要先猛拉 `servo2`

### `touch_affection`

- 主关节：`servo3 + servo2`
- 辅关节：`servo1`
- 情绪核心是“靠近并轻蹭”，不是“撞上去”
- 必备锚点：`neutral -> approach_under_hand -> rub -> retract`
- 总线设计重点：
  - `servo3` 负责前探
  - `servo2` 负责上下送进手心
  - `servo1` 只做小范围跟手修正
  - 这个场景最应该最早接真实输入方向

### `cute_probe`

- 主关节：`servo4 + servo3`
- 辅关节：`servo1`
- 核心是“胆小探头”
- 必备锚点：`neutral -> tilt -> tiny_probe -> retract -> tiny_probe_again`
- 总线设计重点：
  - `servo3` 的前探量要比 `touch_affection` 小
  - `servo4` 负责可爱感，幅度宁小勿大
  - 适合保留大量显式 `move_ms`

### `daydream`

- 主关节：`servo1 + servo4`
- 辅关节：`servo2`
- 核心是“长 hold + 突然回神”
- 必备锚点：`neutral -> look_away_hold -> snap_back -> sleepy_drop -> bounce_back`
- 总线设计重点：
  - 这个场景最吃 `T` 和 `delay` 的关系
  - 前半段用长 `T`，后半段回神用短 `T`
  - 如果真实机构风险高，优先减小 `servo2/servo3` 的下沉

### `standup_reminder`

- 主关节：`servo3 + servo2`
- 辅关节：`servo4`
- 核心是“三次蹭蹭 + 双点头”
- 必备锚点：`neutral -> approach -> bump_loop -> double_nod -> return`
- 总线设计重点：
  - 每次 bump 都应是完整的“压低 -> 顶起 -> 退回”
  - 不要只发抖动式 `nudge`
  - 双点头可以保持现有 `servo4` 微动作逻辑

### `track_target`

- 主关节：`servo1 + servo4`
- 辅关节：`servo2 + servo3`
- 这是唯一一个不应主要靠预编排 step 的主场景
- 必备状态：`tracking_active`、`selected_target`、`last_seen_zone`
- 总线设计重点：
  - scene 只负责“进入 tracking 模式”和“退出 tracking 模式”
  - 实际角度更新应交给 runtime 的 live tracking
  - 对总线输出必须做节流和低通平滑，避免每帧都大跳
  - `servo1` 负责水平跟随，`servo4` 负责俯仰，`servo2/servo3` 只做弱跟随

### `celebrate`

- 主关节：`servo2 + servo3`
- 辅关节：`servo1 + servo4`
- 核心是“整体抬起 + 左右摇摆 + 收尾喘口气”
- 必备锚点：`neutral -> celebrate_ready -> high_sway -> low_sway -> cool_down`
- 总线设计重点：
  - 起手式必须高
  - 左右摇摆由 `servo1` 带动
  - 不要用过多单关节高速小抖动，容易显机械
  - 彩灯和音频触发仍可留在现有 runtime

### `farewell`

- 主关节：`servo1 + servo4`
- 辅关节：`servo2`
- 核心是“先看过去，再挥手，再低头”
- 必备锚点：`neutral -> farewell_look(direction) -> nod_wave -> farewell_bow(direction)`
- 总线设计重点：
  - 应继续沿用现有动态 builder 模式
  - 只把 `direction -> servo1 first pose / last bow pose` 做动态化
  - 挥手本身仍由 `servo4` 慢点头完成

### `sleep`

- 主关节：`servo2 + servo3`
- 辅关节：`servo4`
- 核心是“缓慢收回，而不是断电趴下”
- 必备锚点：`neutral -> head_down -> arm_lower -> stretch_once -> sleep_ready -> sleep`
- 总线设计重点：
  - 这是 bus-servo 上最适合做长 `T` 的场景之一
  - 最终一定落固定 sleep pose
  - `fade_to_sleep` 仍可保持现有灯光逻辑

## Which Scenes Should Become Dynamic Builders

建议分三类：

### Keep Static

- `cute_probe`
- `daydream`
- `standup_reminder`
- `sleep`

### Keep Static Core, Add Optional Context

- `wake_up`
- `curious_observe`
- `celebrate`

### Must Be Dynamic

- `track_target`
- `farewell`
- `touch_affection`

原因很简单：这三个场景的“灵魂”就是外部方向或外部目标，而不是固定 choreography。

## Recommended Implementation Order

最稳妥的落地顺序是：

1. 加 `bus_servo_joint_map.json`
2. 实现 `bus_servo_protocol.py`
3. 实现 `bus_servo_mapping.py`
4. 实现 `bus_servo_adapter.py`
5. 让 runtime 的 `_run_safe_control(...)` 支持 router 模式
6. 先在 `wake_up / farewell / sleep` 三个场景上做真机调试
7. 再推进 `track_target`
8. 最后做 `touch_affection`

这样做的原因是：

- `wake_up / farewell / sleep` 容易看懂，也容易暴露关节方向问题
- `track_target` 对平滑和状态同步要求更高
- `touch_affection` 对安全性和外部输入依赖最强，应该晚一点

## Minimum Test Plan

适配器层最少要补这几类测试：

- `angle -> pwm` 映射正确
- `directionSign = -1` 时会反向
- 单舵机命令和多舵机命令字符串格式正确
- `relative` 模式通过 `SafetyDecision.state_after` 正确转成绝对 PWM
- `move_ms` 显式传入时覆盖默认值
- 从下一条 `delay` 推导 `T` 的逻辑正确
- `farewell(left/right/center)` 会输出不同的 `servo1`
- `track_target` 连续输入时命令变化平滑

## Design Summary

最重要的设计原则只有三条：

1. 不要把 `scenes.py` 改写成总线协议字符串生成器
2. 让适配器吃 `SafetyDecision`，不要吃裸 payload
3. 对每个场景先确定主关节，再决定动态输入，不要四个关节同时抢戏

如果按这条线落地，现有的 mock / runtime / director console / dynamic scene builder 基本都能继续复用，只是设备出口从 HTTP `/control` 多了一条 bus-servo 路径。
