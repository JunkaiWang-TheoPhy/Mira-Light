# LED UART Scripts

这个目录放的是板端和灯头 UART3 控制直接相关的脚本。

## 当前包含

- `send_uart3_led_cmd.py`
- `uart3_led_protocol.py`
- `listen_uart3_led.py`
- `uart3_send_raw.py`
- `test_uart3_loopback.py`
- `test_send_led_speed_cmd.py`
- `test_send_led_thr_cmd.py`

## 这个目录对深圳版的意义

深圳版后面强调了很多“情绪光”：

- 叹气后暖光
- 被夸时更亮
- 害羞时更柔
- 睡觉时慢慢变暗

这些东西最后如果要上真机，不能只停在 `scripts/scenes.py` 的抽象 `led(...)` 上。

你还得知道：

- 板端现在 LED 到底怎么发
- 当前 UART3 已经支持哪些文本命令
- 哪些测试脚本已经存在

## 文件用途

### `uart3_led_protocol.py`

是协议层基础文件，最值得先读。

### `send_uart3_led_cmd.py`

是实际板端命令行入口，最适合拿来跑现成命令。

### `listen_uart3_led.py`

适合看：

- 触摸事件
- 串口回包

### `uart3_send_raw.py`

更偏原始调试发送。

### `test_uart3_loopback.py`

更偏链路验证，不是动作设计本体。

### `test_send_led_speed_cmd.py`、`test_send_led_thr_cmd.py`

是小范围命令测试脚本，说明板端曾经做过针对某些参数的单点验证。

## 对深圳版的实际建议

如果深圳版只是先写 scene pack 规格，可以先不深入这里。

但如果后面要真正落实：

- `sz_sigh_comfort`
- `sz_voice_affect_response`
- `sz_farewell_sleep`

这些场景的灯光表达，这个目录会非常重要。
