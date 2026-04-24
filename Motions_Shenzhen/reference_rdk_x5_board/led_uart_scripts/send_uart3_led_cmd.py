#!/usr/bin/env python3

import argparse

from uart3_led_protocol import (
    AckMessage,
    BAUDRATE,
    DEFAULT_LINE_ENDING,
    ReadyMessage,
    UART_DEVICE,
    UnknownMessage,
    TouchEvent,
    build_all_command,
    build_breathe_command,
    build_bri_command,
    build_help_command,
    build_off_command,
    build_one_command,
    build_rainbow_command,
    build_resume_command,
    build_spin_command,
    build_stop_command,
    build_thr_command,
    build_wake_command,
    parse_incoming_message,
    send_command,
)


def parse_args():
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--device", default=UART_DEVICE, help="UART device path")
    common.add_argument("--baudrate", type=int, default=BAUDRATE, help="UART baudrate")
    common.add_argument(
        "--line-ending",
        choices=("none", "lf", "crlf"),
        default=DEFAULT_LINE_ENDING,
        help="Line ending appended after the command",
    )
    common.add_argument(
        "--read-reply",
        action="store_true",
        help="Read and print any data returned by the lower controller",
    )
    common.add_argument(
        "--reply-timeout",
        type=float,
        default=0.2,
        help="Reply wait time in seconds when --read-reply is enabled",
    )

    parser = argparse.ArgumentParser(
        description="Send LED/touch commands over RDK X5 uart3 (/dev/ttyS3)",
        parents=[common],
    )

    subparsers = parser.add_subparsers(dest="command_type", required=True)

    parser_all = subparsers.add_parser("all", help="Send ALL,R,G,B,BRI", parents=[common])
    parser_all.add_argument("r", type=int)
    parser_all.add_argument("g", type=int)
    parser_all.add_argument("b", type=int)
    parser_all.add_argument("bri", type=int)

    parser_one = subparsers.add_parser(
        "one",
        help="Send ONE,grp,idx,R,G,B,BRI",
        parents=[common],
    )
    parser_one.add_argument("grp", type=int, help="0=outer ring, 1=inner ring")
    parser_one.add_argument("idx", type=int, help="0-23 for grp0, 0-15 for grp1")
    parser_one.add_argument("r", type=int)
    parser_one.add_argument("g", type=int)
    parser_one.add_argument("b", type=int)
    parser_one.add_argument("bri", type=int)

    parser_bri = subparsers.add_parser("bri", help="Send BRI,val", parents=[common])
    parser_bri.add_argument("value", type=int)

    subparsers.add_parser("off", help="Send OFF", parents=[common])

    parser_thr = subparsers.add_parser("thr", help="Send THR,val", parents=[common])
    parser_thr.add_argument("value", type=int)

    parser_rainbow = subparsers.add_parser(
        "rainbow",
        help="Send RAINBOW[,brightness]",
        parents=[common],
    )
    parser_rainbow.add_argument(
        "brightness",
        type=int,
        nargs="?",
        default=200,
        help="0-255, default 200",
    )

    parser_breathe = subparsers.add_parser(
        "breathe",
        help="Send BREATHE[,R,G,B[,BRI]] or BREATHE,RAINBOW[,BRI]",
        parents=[common],
    )
    parser_breathe.add_argument("--rainbow", action="store_true")
    parser_breathe.add_argument("values", nargs="*", type=int, help="R G B [BRI]")

    parser_wake = subparsers.add_parser(
        "wake",
        help="Send WAKE[,R,G,B[,BRI]] or WAKE,RAINBOW[,BRI]",
        parents=[common],
    )
    parser_wake.add_argument("--rainbow", action="store_true")
    parser_wake.add_argument("values", nargs="*", type=int, help="R G B [BRI]")

    parser_spin = subparsers.add_parser(
        "spin",
        help="Send SPIN[,R,G,B[,ODIR,IDIR[,BRI]]] or SPIN,RAINBOW[,ODIR,IDIR[,BRI]]",
        parents=[common],
    )
    parser_spin.add_argument("--rainbow", action="store_true")
    parser_spin.add_argument("values", nargs="*", type=int, help="RGB or direction values")

    subparsers.add_parser("stop", help="Send STOP", parents=[common])
    subparsers.add_parser("resume", help="Send RESUME", parents=[common])
    subparsers.add_parser("helpcmd", help="Send HELP", parents=[common])

    return parser.parse_args()


def build_command(args) -> str:
    if args.command_type == "all":
        return build_all_command(args.r, args.g, args.b, args.bri)
    if args.command_type == "one":
        return build_one_command(args.grp, args.idx, args.r, args.g, args.b, args.bri)
    if args.command_type == "bri":
        return build_bri_command(args.value)
    if args.command_type == "off":
        return build_off_command()
    if args.command_type == "thr":
        return build_thr_command(args.value)
    if args.command_type == "rainbow":
        return build_rainbow_command(args.brightness)
    if args.command_type == "breathe":
        return build_breathe_args(args)
    if args.command_type == "wake":
        return build_wake_args(args)
    if args.command_type == "spin":
        return build_spin_args(args)
    if args.command_type == "stop":
        return build_stop_command()
    if args.command_type == "resume":
        return build_resume_command()
    if args.command_type == "helpcmd":
        return build_help_command()
    raise ValueError(f"unsupported command type: {args.command_type}")


def build_breathe_args(args) -> str:
    values = args.values
    if args.rainbow:
        if len(values) == 0:
            return build_breathe_command(rainbow=True)
        if len(values) == 1:
            return build_breathe_command(rainbow=True, brightness=values[0])
        raise ValueError("breathe --rainbow accepts at most 1 value: [BRI]")
    if len(values) == 0:
        return build_breathe_command()
    if len(values) == 3:
        return build_breathe_command(values[0], values[1], values[2])
    if len(values) == 4:
        return build_breathe_command(values[0], values[1], values[2], values[3])
    raise ValueError("breathe expects no values, R G B, or R G B BRI")


def build_wake_args(args) -> str:
    values = args.values
    if args.rainbow:
        if len(values) == 0:
            return build_wake_command(rainbow=True)
        if len(values) == 1:
            return build_wake_command(rainbow=True, brightness=values[0])
        raise ValueError("wake --rainbow accepts at most 1 value: [BRI]")
    if len(values) == 0:
        return build_wake_command()
    if len(values) == 3:
        return build_wake_command(values[0], values[1], values[2])
    if len(values) == 4:
        return build_wake_command(values[0], values[1], values[2], values[3])
    raise ValueError("wake expects no values, R G B, or R G B BRI")


def build_spin_args(args) -> str:
    values = args.values
    if args.rainbow:
        if len(values) == 0:
            return build_spin_command(rainbow=True)
        if len(values) == 2:
            return build_spin_command(rainbow=True, outer_dir=values[0], inner_dir=values[1])
        if len(values) == 3:
            return build_spin_command(
                rainbow=True, outer_dir=values[0], inner_dir=values[1], brightness=values[2]
            )
        raise ValueError("spin --rainbow expects [], ODIR IDIR, or ODIR IDIR BRI")
    if len(values) == 0:
        return build_spin_command()
    if len(values) == 3:
        return build_spin_command(values[0], values[1], values[2])
    if len(values) == 5:
        return build_spin_command(values[0], values[1], values[2], values[3], values[4])
    if len(values) == 6:
        return build_spin_command(values[0], values[1], values[2], values[3], values[4], values[5])
    raise ValueError("spin expects [], R G B, R G B ODIR IDIR, or R G B ODIR IDIR BRI")


def main():
    args = parse_args()
    command = build_command(args)

    print(f"Device      : {args.device}")
    print(f"Baudrate    : {args.baudrate}")
    print(f"Line ending : {args.line_ending}")
    print(f"Send        : {command}")

    sent, reply = send_command(
        command=command,
        uart_device=args.device,
        baudrate=args.baudrate,
        line_ending=args.line_ending,
        read_reply=args.read_reply,
        reply_timeout=args.reply_timeout,
    )

    print(f"Sent bytes  : {sent}")
    if args.read_reply:
        if reply:
            text = reply.strip()
            print(f"Reply       : {text}")
            parsed = parse_incoming_message(text)
            if isinstance(parsed, TouchEvent):
                if parsed.value is None:
                    print(f"Reply type  : {parsed.name}")
                else:
                    print(f"Reply type  : {parsed.name} ({parsed.value})")
            elif isinstance(parsed, AckMessage):
                print("Reply type  : ack")
            elif isinstance(parsed, ReadyMessage):
                print("Reply type  : ready")
            elif isinstance(parsed, UnknownMessage):
                print("Reply type  : unknown text")
        else:
            print("Reply       : no data")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
