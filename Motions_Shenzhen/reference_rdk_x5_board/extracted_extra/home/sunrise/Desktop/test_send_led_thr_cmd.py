#!/usr/bin/env python3

from servo_uart_protocol import build_led_threshold_command, send_packet


PACKET = build_led_threshold_command(1100)


def main():
    print(f"Send: {PACKET}")
    sent = send_packet(PACKET)
    print(f"Sent bytes: {sent}")


if __name__ == "__main__":
    main()
