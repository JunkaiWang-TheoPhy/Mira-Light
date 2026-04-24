# End-Side Protocol Layer

这份文档只讲端侧真实协议层，不讲高层 scene 抽象。

目标是把下面三件事讲清楚：

1. 舵机主链最终理解什么格式
2. 灯头主链最终理解什么格式
3. 哪些路径是主链，哪些只是旁路实验

## 1. 舵机主链：UART1 二进制总线协议

依据：

- `board_docs/UART1_SERVO_README.md`
- `servo_motion_scripts/bus_servo_protocol.py`
- `servo_motion_scripts/send_uart1_servo_cmd.py`

### 当前事实

- RDK X5 直接通过 `uart1` 发送总线协议
- 默认设备：`/dev/ttyS1`
- 默认波特率：`1000000`
- 默认超时：`0.2`

### 协议包格式

```text
FF FF ID Length Instruction Parameters... Checksum
```

字段含义：

- `FF FF`
  包头
- `ID`
  舵机 ID
- `Length`
  数据长度
- `Instruction`
  指令类型
- `Parameters`
  参数区
- `Checksum`
  校验和

### 当前常用指令

- `PING`
- `READ_DATA`
- `WRITE_DATA`
- `REG_WRITE`
- `ACTION`
- `RESET`
- `SYNC_READ`
- `SYNC_WRITE`

### 当前常用寄存器

- `0x2A`
  目标位置
- `0x2C`
  运行时间
- `0x2E`
  运行速度
- `0x38`
  当前位置

### 最重要的现实判断

端侧并没有一个统一“单片机 scene 协议”来吃高层场景名。

端侧舵机主链真正理解的是：

> **二进制总线舵机协议包**

高层 scene 必须先被板端 Python 脚本拆成位置、速度、时间、阶段，再转成这些包。

## 2. 灯头主链：UART3 文本协议

依据：

- `board_docs/UART3_LED_PROTOCOL_README.md`
- `board_docs/灯头指令.md`
- `led_uart_scripts/uart3_led_protocol.py`

### 当前事实

- RDK X5 通过 `uart3` 给灯头控制器发命令
- 默认设备：`/dev/ttyS3`
- 默认波特率：`115200`
- 每条命令以 `\n` 结尾

### 文本协议格式

这条链理解的是字符串命令，例如：

```text
ALL,255,255,255,120
OFF
BREATHE,0,0,255,150
RAINBOW,150
WAKE,255,220,180,150
```

### 当前支持的主命令

- `ALL`
- `ONE`
- `BRI`
- `OFF`
- `RAINBOW`
- `BREATHE`
- `WAKE`
- `SPIN`
- `STOP`
- `RESUME`
- `THR`
- `HELP`

### 当前支持的事件与回包

- `TOUCH,PRESS,<val>`
- `TOUCH,RELEASE,<val>`
- `TOUCH,HOLD,<val>`
- `OK ...`
- `ERR ...`

### 最重要的现实判断

灯头控制器理解的是：

> **文本灯光协议**

它和舵机链路不是同一种格式，也不是同一个传输层。

## 3. PWM 路径只是旁路实验

依据：

- `servo_motion_scripts/servo_test.py`

这个文件走的是：

- `/sys/class/pwm`
- sysfs PWM

它不属于当前深圳版 scene pack 的主动作链，只能算：

- 单独硬件试验
- 旁路验证

## 4. 当前端侧协议层的正确分层

如果用一句话描述端侧现实，最准确的是：

```text
RDK X5 Python 脚本
-> UART1 二进制总线舵机协议
-> 4 个舵机

RDK X5 Python 脚本
-> UART3 文本灯头协议
-> 灯头 ESP32 / 40 灯 / 触摸
```

而不是：

```text
高层 scene 名
-> 某个统一单片机动作协议
```

## 5. 对后续开发的指导

### 写 `scenes_shenzhen.py` 时

不要假设底层只有一条输出链。

你需要同时考虑：

- 舵机动作怎么拆成阶段
- 灯效命令怎么并行或串行插入

### 写 `scene_script.py` 时

不要把 `sceneId` 当成端侧最终格式。

它只是一层 launch manifest。

真正落到底层时，仍然要回到：

- UART1 二进制包
- UART3 文本命令

## 一句话总结

端侧真实协议层不是一个东西，而是：

> 舵机一条、灯头一条、PWM 实验一条，其中前两条才是深圳版后续开发必须对齐的主链。
