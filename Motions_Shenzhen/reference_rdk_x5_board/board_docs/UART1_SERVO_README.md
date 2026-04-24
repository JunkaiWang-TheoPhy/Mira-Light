# UART1 Bus Servo Control

This directory now uses the new binary bus-servo protocol from `Desktop/舵机通信协议`.

All servo commands are sent directly by RDK X5 over `uart1`.
There is no longer any TCP forwarding or upper-layer gateway for servo control.

## Protocol Summary

- packet header: `FF FF`
- command format: `FF FF ID Length Instruction Parameters... Checksum`
- checksum: `~(ID + Length + Instruction + Parameters...) & 0xFF`
- magnetic-encoder series uses little-endian for 2-byte values:
  low byte first, high byte second

## Default UART Settings

- device: `/dev/ttyS1`
- baudrate: `1000000`
- timeout: `0.2`

If your servo ID/baudrate was changed before, override the baudrate on the command line.

## Important Register Addresses

- `0x05`: ID
- `0x28`: torque switch
- `0x29`: acceleration
- `0x2A`: target position
- `0x2C`: run time
- `0x2E`: run speed
- `0x37`: EEPROM lock flag
- `0x38`: current position
- `0x3A`: current speed
- `0x41`: servo status
- `0x42`: moving flag

## Common Commands

Ping one servo:

```bash
python3 /home/sunrise/Desktop/send_uart1_servo_cmd.py ping 1
```

Read current position:

```bash
python3 /home/sunrise/Desktop/send_uart1_servo_cmd.py read-pos 1
```

Read any register:

```bash
python3 /home/sunrise/Desktop/send_uart1_servo_cmd.py read 1 0x38 2 --decode position
python3 /home/sunrise/Desktop/send_uart1_servo_cmd.py read 1 0x3A 2 --decode speed
python3 /home/sunrise/Desktop/send_uart1_servo_cmd.py read 1 0x3E 1 --decode voltage
python3 /home/sunrise/Desktop/send_uart1_servo_cmd.py read 1 0x41 1 --decode status
```

Move one servo in position mode:

```bash
python3 /home/sunrise/Desktop/send_uart1_servo_cmd.py move 1 2048 --time 0 --speed 1000
```

Move one servo and write acceleration first:

```bash
python3 /home/sunrise/Desktop/send_uart1_servo_cmd.py move 1 1024 --speed 800 --accel 10
```

Stage moves with `REG WRITE`, then trigger together:

```bash
python3 /home/sunrise/Desktop/send_uart1_servo_cmd.py reg-move 1 2048 --speed 1000
python3 /home/sunrise/Desktop/send_uart1_servo_cmd.py reg-move 2 2048 --speed 1000
python3 /home/sunrise/Desktop/send_uart1_servo_cmd.py action
```

Broadcast one `SYNC WRITE` move:

```bash
python3 /home/sunrise/Desktop/send_uart1_servo_cmd.py sync-move 1:2048:0:1000 2:1024:0:1000 3:3072:0:1000
```

Torque control:

```bash
python3 /home/sunrise/Desktop/send_uart1_servo_cmd.py torque 1 on
python3 /home/sunrise/Desktop/send_uart1_servo_cmd.py torque 1 off
python3 /home/sunrise/Desktop/send_uart1_servo_cmd.py torque 1 damp
```

Change ID and save it across power cycles:

```bash
python3 /home/sunrise/Desktop/send_uart1_servo_cmd.py set-id 1 2 --persistent
```

Write raw bytes to a register:

```bash
python3 /home/sunrise/Desktop/send_uart1_servo_cmd.py write 1 0x28 1
```

Reset one servo:

```bash
python3 /home/sunrise/Desktop/send_uart1_servo_cmd.py reset 1
```

## 4-Servo Convenience Script

For your current 4-servo setup with ids `0 1 2 3`, you can use:

```bash
python3 /home/sunrise/Desktop/four_servo_control.py ping-all
python3 /home/sunrise/Desktop/four_servo_control.py read-pos-all
python3 /home/sunrise/Desktop/four_servo_control.py torque on
python3 /home/sunrise/Desktop/four_servo_control.py center
python3 /home/sunrise/Desktop/four_servo_control.py deg-all 90 --speed 1000
python3 /home/sunrise/Desktop/four_servo_control.py all 2048 --speed 1000
python3 /home/sunrise/Desktop/four_servo_control.py pose 1024 1536 2048 2560 --speed 1000
```

If the 4-servo group ids change later, override them with:

```bash
python3 /home/sunrise/Desktop/four_servo_control.py --ids 4 5 6 7 ping-all
```

## Wiring

- RDK X5 `pin 8` (`UART1_TXD`) -> servo bus transceiver `DI/TX`
- RDK X5 `pin 10` (`UART1_RXD`) <- servo bus transceiver `RO/RX`
- RDK X5 `GND` -> servo bus transceiver `GND`

If the new servo bus is RS485, make sure the board-side electrical conversion is correct before sending commands directly.
