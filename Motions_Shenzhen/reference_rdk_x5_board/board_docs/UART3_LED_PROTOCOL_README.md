# UART3 Light Head Control

This script family sends the new light-head text protocol directly from RDK X5 over `uart3`.

There is no longer any TCP gateway or upper-layer bridge for light-head control.

Default UART settings:

- device: `/dev/ttyS3`
- baudrate: `115200`
- line ending: `\n`

## Files

- `uart3_led_protocol.py`: protocol builder, validator, UART sender, and reply parser
- `send_uart3_led_cmd.py`: local command line sender on RDK X5
- `listen_uart3_led.py`: local UART listener for touch events and replies

## Wiring

Remove the loopback wire first.

- RDK X5 `pin 3` (`UART3_TXD`) -> light-head controller `RX`
- RDK X5 `pin 5` (`UART3_RXD`) <- light-head controller `TX`
- RDK X5 `GND` -> light-head controller `GND`

`uart3` and `i2c5` share the same 40PIN pins, so keep `uart3=okay` and `i2c5=disabled`.

## Basic Commands

All 40 LEDs white full brightness:

```bash
python3 /home/sunrise/Desktop/send_uart3_led_cmd.py all 255 255 255 255
```

All LEDs red half brightness:

```bash
python3 /home/sunrise/Desktop/send_uart3_led_cmd.py all 255 0 0 128
```

Outer ring LED 0 green:

```bash
python3 /home/sunrise/Desktop/send_uart3_led_cmd.py one 0 0 0 255 0 200
```

Inner ring LED 5 purple:

```bash
python3 /home/sunrise/Desktop/send_uart3_led_cmd.py one 1 5 255 0 255 255
```

Set global brightness:

```bash
python3 /home/sunrise/Desktop/send_uart3_led_cmd.py bri 50
```

Turn all LEDs off:

```bash
python3 /home/sunrise/Desktop/send_uart3_led_cmd.py off
```

## Effect Commands

Static rainbow:

```bash
python3 /home/sunrise/Desktop/send_uart3_led_cmd.py rainbow
python3 /home/sunrise/Desktop/send_uart3_led_cmd.py rainbow 150
```

Breathe effect:

```bash
python3 /home/sunrise/Desktop/send_uart3_led_cmd.py breathe
python3 /home/sunrise/Desktop/send_uart3_led_cmd.py breathe 0 0 255 150
python3 /home/sunrise/Desktop/send_uart3_led_cmd.py breathe --rainbow
python3 /home/sunrise/Desktop/send_uart3_led_cmd.py breathe --rainbow 180
```

Wake effect:

```bash
python3 /home/sunrise/Desktop/send_uart3_led_cmd.py wake
python3 /home/sunrise/Desktop/send_uart3_led_cmd.py wake 0 200 255
python3 /home/sunrise/Desktop/send_uart3_led_cmd.py wake --rainbow 150
```

Spin effect:

```bash
python3 /home/sunrise/Desktop/send_uart3_led_cmd.py spin
python3 /home/sunrise/Desktop/send_uart3_led_cmd.py spin 255 0 0 0 1
python3 /home/sunrise/Desktop/send_uart3_led_cmd.py spin --rainbow 0 1 180
```

Stop and resume animation:

```bash
python3 /home/sunrise/Desktop/send_uart3_led_cmd.py stop
python3 /home/sunrise/Desktop/send_uart3_led_cmd.py resume
```

## Touch and Replies

Set touch threshold:

```bash
python3 /home/sunrise/Desktop/send_uart3_led_cmd.py thr 300
```

Ask device to print help:

```bash
python3 /home/sunrise/Desktop/send_uart3_led_cmd.py helpcmd --read-reply
```

Read back text replies from one command:

```bash
python3 /home/sunrise/Desktop/send_uart3_led_cmd.py wake --rainbow 150 --read-reply
```

Continuously listen to data returned by the light-head controller:

```bash
python3 /home/sunrise/Desktop/listen_uart3_led.py
python3 /home/sunrise/Desktop/listen_uart3_led.py --hex
```

If your lower controller does not need a line ending, append:

```bash
--line-ending none
```
