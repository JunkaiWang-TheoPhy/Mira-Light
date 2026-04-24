# RDK X5 UART3 Loopback

## What This Script Tests

- `test_uart3_loopback.py` targets the second 40PIN UART on RDK X5
- Default device: `/dev/ttyS3`
- Default loopback payload: `AA55`

## RDK X5 40PIN Wiring

- Physical pin `3` is multiplexed as `I2C5_SDA / UART3_TXD`
- Physical pin `5` is multiplexed as `I2C5_SCL / UART3_RXD`
- For loopback, short `pin 3` and `pin 5`

## Pinmux Reminder

On RDK X5, `uart3` and `i2c5` are one multiplexed group.

Before testing:

1. Open `sudo srpi-config`
2. Go to `3 Interface Options`
3. Enter `I3 Peripheral bus config`
4. Set `uart3` to `okay`
5. Set `i2c5` to `disabled`
6. Reboot

## Example Commands

```bash
python3 /home/sunrise/Desktop/test_uart3_loopback.py
python3 /home/sunrise/Desktop/test_uart3_loopback.py --baudrate 921600
python3 /home/sunrise/Desktop/test_uart3_loopback.py --count 5
```
