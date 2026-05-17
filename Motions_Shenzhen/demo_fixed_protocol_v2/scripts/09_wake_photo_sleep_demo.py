#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
CONSOLE_DIR = SCRIPT_DIR.parent / "console"
JAVIS_RUNTIME = (
    Path.home()
    / "Documents"
    / "Github"
    / "Javis-Hackathon"
    / "exports"
    / "macbook-camera-print-deploy-pack-20260329"
    / "source"
    / "current"
    / "openclaw-chrome-camera-anime"
    / "runtime"
)
DEFAULT_CAPTURE_DIR = SCRIPT_DIR.parent.parent.parent / "tmp" / "mira-light-board-camera"
DEFAULT_RENDER_OUTPUT_DIR = (
    Path.home()
    / "Documents"
    / "Github"
    / "Javis-Hackathon"
    / "tmp"
    / "digua-console-output"
)
DEFAULT_RENDER_LOG_DIR = SCRIPT_DIR.parent.parent.parent / "tmp" / "mira-light-render-print-logs"
DEFAULT_STYLE_SLUG = "mira-light-wake-photo-anime"
DEFAULT_STYLE_PROMPT = (
    "现代高清的吉卜力动画风格插画，保留 Mira Light 摄像头拍到的真实构图和主体，"
    "画面干净明亮，有电影感，适合6寸照片打印"
)
DEFAULT_PRINTER_QUEUE = "Mi_Wireless_Photo_Printer_9135_IP"
DEFAULT_PRINT_MEDIA = "na_index-4x6_4x6in"
ARK_API_KEYCHAIN_SERVICE = "mira-light-ark-api-key"

if str(CONSOLE_DIR) not in sys.path:
    sys.path.insert(0, str(CONSOLE_DIR))
if str(JAVIS_RUNTIME) not in sys.path:
    sys.path.insert(0, str(JAVIS_RUNTIME))

import shenzhen_console  # noqa: E402
import digua_remote_render_pipeline  # noqa: E402
import rokid_render_pipeline  # noqa: E402


def read_keychain_secret(service: str) -> str:
    command = ["security", "find-generic-password", "-s", service, "-w"]
    account = os.environ.get("USER") or os.environ.get("LOGNAME")
    if account:
        command[2:2] = ["-a", account]
    try:
        result = subprocess.run(command, check=False, capture_output=True, text=True, timeout=5)
    except (OSError, subprocess.TimeoutExpired):
        return ""
    if result.returncode != 0:
        return ""
    return result.stdout.strip()


def default_ark_api_key() -> str:
    return os.environ.get("ARK_API_KEY", "") or read_keychain_secret(ARK_API_KEYCHAIN_SERVICE)


def remote_script(lines: list[str]) -> str:
    return "set -euo pipefail\n" + "\n".join(lines) + "\n"


def run_remote(
    *,
    label: str,
    script: str,
    args: argparse.Namespace,
    timeout_seconds: float,
) -> dict:
    print(f"== {label} ==", flush=True)
    result = shenzhen_console.run_remote_script(
        script=script,
        host=args.host,
        port=args.port,
        user=args.user,
        password=args.password,
        timeout_seconds=timeout_seconds,
    )
    if result.get("stdout"):
        print(result["stdout"], end="" if str(result["stdout"]).endswith("\n") else "\n")
    if result.get("stderr"):
        print(result["stderr"], file=sys.stderr, end="" if str(result["stderr"]).endswith("\n") else "\n")
    if result.get("returnCode") != 0:
        raise RuntimeError(f"{label} failed with return code {result.get('returnCode')}")
    return result


def build_wake_to_photo_pose_script(*, hold_high_seconds: float) -> str:
    return remote_script(
        [
            "echo '== start dark ==' && python3 /home/sunrise/Desktop/send_uart3_led_cmd.py off",
            (
                "echo '== fold to sleep start pose ==' && "
                "python3 /home/sunrise/Desktop/four_servo_control.py pose "
                "2048 1821 2912 2130 --speeds 2000 320 1240 2000"
            ),
            "echo '== hold still before waking ==' && sleep 0.3",
            "echo '== tiny warm pre-glow ==' && python3 /home/sunrise/Desktop/send_uart3_led_cmd.py all 255 180 120 25",
            "echo '== pause before eye-open effect ==' && sleep 0.16",
            "echo '== wake light ==' && python3 /home/sunrise/Desktop/send_uart3_led_cmd.py wake 255 220 180 150",
            "echo '== pause for eye-open effect ==' && sleep 0.28",
            (
                "echo '== half-awake lift ==' && "
                "python3 /home/sunrise/Desktop/four_servo_control.py pose "
                "2048 1900 2750 2130 --speeds 220 90 180 180"
            ),
            "echo '== half-awake pause ==' && sleep 0.22",
            (
                "echo '== stretch to high point ==' && "
                "python3 /home/sunrise/Desktop/four_servo_pose_delay_2.py "
                "--targets 2048 2400 1700 2130 --speeds 1000 160 380 1000 --delay-ratio 0.25"
            ),
            f"echo '== hold high point ==' && sleep {hold_high_seconds:.2f}",
            (
                "echo '== long stretch accent ==' && "
                "python3 /home/sunrise/Desktop/four_servo_pose_2048_2048_2048_2780_separate.py "
                "--speed 250 --delay 0.05"
            ),
            (
                "echo '== settle back to normal height ==' && "
                "python3 /home/sunrise/Desktop/four_servo_control.py pose "
                "2048 2150 2048 2130 --speeds 180 100 100 180"
            ),
            "echo '== steady photo light ==' && python3 /home/sunrise/Desktop/send_uart3_led_cmd.py all 255 255 245 135",
            (
                "echo '== photo pose 2048 1880 1650 2048 ==' && "
                "python3 /home/sunrise/Desktop/four_servo_control.py pose "
                "2048 1880 1650 2048 --speeds 340 340 340 340"
            ),
            "echo '== hold steady before real photo ==' && sleep 0.3",
        ]
    )


def build_sleep_script(*, rest_seconds: float) -> str:
    lines = [
        (
            "echo '== enter attentive end pose ==' && "
            "python3 /home/sunrise/Desktop/four_servo_control.py pose "
            "2048 2180 1980 2240 --speeds 640 360 360 480"
        ),
        "echo '== soft warm pre-sleep light ==' && python3 /home/sunrise/Desktop/send_uart3_led_cmd.py all 255 220 180 95",
        "echo '== glide through attentive pose ==' && sleep 0.18",
        (
            "echo '== settle through mid pose ==' && "
            "python3 /home/sunrise/Desktop/four_servo_control.py pose "
            "2048 2100 2380 2200 --speeds 560 320 520 440"
        ),
        "echo '== glide through mid transition ==' && sleep 0.16",
        (
            "echo '== lower and extend slowly ==' && "
            "python3 /home/sunrise/Desktop/four_servo_control.py pose "
            "2048 2005 2680 2180 --speeds 520 280 460 400"
        ),
        "echo '== dim while lowering ==' && python3 /home/sunrise/Desktop/send_uart3_led_cmd.py all 255 205 155 70",
        "echo '== glide through low extension ==' && sleep 0.14",
        (
            "echo '== small relax stretch before curling ==' && "
            "python3 /home/sunrise/Desktop/four_servo_control.py pose "
            "2048 2080 2500 2240 --speeds 480 280 380 360"
        ),
        "echo '== brief stretch release ==' && sleep 0.12",
        (
            "echo '== begin timed sleep curl ==' && "
            "python3 /home/sunrise/Desktop/four_servo_control.py pose "
            "2048 2080 2912 2130 --speeds 4000 640 2480 4000"
        ),
        "echo '== timed fold delay ==' && sleep 0.08",
        (
            "echo '== finish timed sleep fold ==' && "
            "python3 /home/sunrise/Desktop/four_servo_control.py pose "
            "2048 1821 2912 2130 --speeds 4000 640 2480 4000"
        ),
        "echo '== dim to sleep glow ==' && python3 /home/sunrise/Desktop/send_uart3_led_cmd.py all 255 180 120 20",
        f"echo '== rest hold in final sleep pose ==' && sleep {rest_seconds:.2f}",
        "echo '== fade to almost off ==' && python3 /home/sunrise/Desktop/send_uart3_led_cmd.py all 255 180 120 8",
        "echo '== final lights off ==' && python3 /home/sunrise/Desktop/send_uart3_led_cmd.py off",
    ]
    return remote_script(lines)


def capture_photo(args: argparse.Namespace, *, timestamp: str) -> Path:
    print("== capture real Mira Light camera photo ==", flush=True)
    path = digua_remote_render_pipeline.capture_remote_image(
        host=args.host,
        user=args.user,
        port=args.port,
        password=args.password,
        bind_address=args.bind_address,
        known_hosts_path=args.known_hosts_path,
        connect_timeout=args.connect_timeout,
        remote_device=args.remote_device,
        input_format=args.input_format,
        video_size=args.video_size,
        remote_temp_path=args.remote_temp_path,
        capture_dir=args.capture_dir,
        timestamp=timestamp,
        timeout=args.capture_timeout,
        ssh_retries=args.ssh_retries,
        ssh_retry_delay_seconds=args.ssh_retry_delay_seconds,
    )
    print(f"PHOTO_SAVED_LOCAL={path}", flush=True)
    return path


def spawn_render_print_worker(args: argparse.Namespace, *, source_image_path: Path, timestamp: str) -> Path:
    args.render_log_dir.mkdir(parents=True, exist_ok=True)
    log_path = args.render_log_dir / f"wake-photo-render-print-{timestamp}.log"
    command = [
        sys.executable,
        str(Path(__file__).resolve()),
        "--render-print-worker",
        "--source-image-path",
        str(source_image_path),
        "--render-output-dir",
        str(args.render_output_dir),
        "--style-slug",
        args.style_slug,
        "--style-prompt",
        args.style_prompt,
        "--timestamp",
        timestamp,
        "--printer-queue",
        args.printer_queue,
        "--print-media",
        args.print_media,
    ]
    if args.no_print:
        command.append("--no-print")
    env = dict(os.environ)
    with log_path.open("ab") as log_file:
        process = subprocess.Popen(
            command,
            stdout=log_file,
            stderr=subprocess.STDOUT,
            env=env,
            start_new_session=True,
        )
    print(f"RENDER_PRINT_STARTED pid={process.pid} log={log_path}", flush=True)
    return log_path


def run_render_print_worker(args: argparse.Namespace) -> int:
    started = datetime.now().isoformat(timespec="seconds")
    print(json.dumps({"event": "render_print_started", "at": started, "source": str(args.source_image_path)}, ensure_ascii=False))
    if not args.api_key:
        raise RuntimeError("ARK_API_KEY is required for anime rendering.")
    generation = rokid_render_pipeline.generate_from_image_path(
        api_key=args.api_key,
        image_path=args.source_image_path,
        output_dir=args.render_output_dir,
        style_slug=args.style_slug,
        style_prompt=args.style_prompt,
        timestamp=args.timestamp,
    )
    print(json.dumps({"event": "render_complete", **generation}, ensure_ascii=False, indent=2))
    if not args.no_print:
        print_command = [
            "lp",
            "-d",
            args.printer_queue,
            "-o",
            f"media={args.print_media}",
            "-o",
            "print-scaling=fill",
            "-o",
            "print-quality=5",
            "-o",
            "fit-to-page=false",
            str(generation["output_path"]),
        ]
        result = subprocess.run(print_command, check=False, capture_output=True, text=True)
        if result.returncode != 0:
            raise RuntimeError((result.stderr or result.stdout or "lp print submission failed").strip())
        print(
            json.dumps(
                {
                    "event": "print_submitted",
                    "printer_queue": args.printer_queue,
                    "print_media": args.print_media,
                    "stdout": result.stdout.strip(),
                },
                ensure_ascii=False,
                indent=2,
            )
        )
    return 0


def run_orchestrator(args: argparse.Namespace) -> int:
    timestamp = args.timestamp or datetime.now().strftime("%Y%m%d-%H%M%S-%f")
    run_remote(
        label="wake to photo pose",
        script=build_wake_to_photo_pose_script(hold_high_seconds=args.hold_high_seconds),
        args=args,
        timeout_seconds=args.motion_timeout,
    )
    source_image_path = capture_photo(args, timestamp=timestamp)
    render_log_path = spawn_render_print_worker(args, source_image_path=source_image_path, timestamp=timestamp)
    run_remote(
        label="return to sleep while render/print continues",
        script=build_sleep_script(rest_seconds=args.rest_seconds),
        args=args,
        timeout_seconds=args.motion_timeout,
    )
    print(
        json.dumps(
            {
                "ok": True,
                "source_image_path": str(source_image_path),
                "render_print_log_path": str(render_log_path),
                "render_print_mode": "background",
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Wake Mira Light, take a real photo, start anime render/print immediately, then return to sleep."
    )
    parser.add_argument("--host", default=digua_remote_render_pipeline.DEFAULT_HOST)
    parser.add_argument("--user", default=digua_remote_render_pipeline.DEFAULT_USER)
    parser.add_argument("--port", type=int, default=digua_remote_render_pipeline.DEFAULT_PORT)
    parser.add_argument("--password", default=os.environ.get("DIGUA_SSH_PASSWORD", ""))
    parser.add_argument("--bind-address", default=os.environ.get("DIGUA_SSH_BIND_ADDRESS", ""))
    parser.add_argument("--known-hosts-path", type=Path, default=digua_remote_render_pipeline.DEFAULT_KNOWN_HOSTS_PATH)
    parser.add_argument("--connect-timeout", type=int, default=digua_remote_render_pipeline.DEFAULT_CONNECT_TIMEOUT)
    parser.add_argument("--remote-device", default=digua_remote_render_pipeline.DEFAULT_DEVICE)
    parser.add_argument("--input-format", default=digua_remote_render_pipeline.DEFAULT_INPUT_FORMAT)
    parser.add_argument("--video-size", default=digua_remote_render_pipeline.DEFAULT_VIDEO_SIZE)
    parser.add_argument("--remote-temp-path", default="/tmp/mira-light-wake-photo.jpg")
    parser.add_argument("--capture-dir", type=Path, default=DEFAULT_CAPTURE_DIR)
    parser.add_argument("--capture-timeout", type=int, default=90)
    parser.add_argument("--ssh-retries", type=int, default=digua_remote_render_pipeline.DEFAULT_SSH_RETRIES)
    parser.add_argument(
        "--ssh-retry-delay-seconds",
        type=float,
        default=digua_remote_render_pipeline.DEFAULT_SSH_RETRY_DELAY_SECONDS,
    )
    parser.add_argument("--hold-high-seconds", type=float, default=1.2)
    parser.add_argument("--rest-seconds", type=float, default=0.3)
    parser.add_argument("--lights-off", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("--motion-timeout", type=float, default=180.0)
    parser.add_argument("--render-output-dir", type=Path, default=DEFAULT_RENDER_OUTPUT_DIR)
    parser.add_argument("--render-log-dir", type=Path, default=DEFAULT_RENDER_LOG_DIR)
    parser.add_argument("--style-slug", default=DEFAULT_STYLE_SLUG)
    parser.add_argument("--style-prompt", default=DEFAULT_STYLE_PROMPT)
    parser.add_argument("--printer-queue", default=os.environ.get("MIRA_LIGHT_PRINT_QUEUE", DEFAULT_PRINTER_QUEUE))
    parser.add_argument("--print-media", default=os.environ.get("MIRA_LIGHT_PRINT_MEDIA", DEFAULT_PRINT_MEDIA))
    parser.add_argument("--no-print", action="store_true")
    parser.add_argument("--timestamp")
    parser.add_argument("--render-print-worker", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("--source-image-path", type=Path, help=argparse.SUPPRESS)
    parser.add_argument("--api-key", default=default_ark_api_key(), help=argparse.SUPPRESS)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.render_print_worker:
            return run_render_print_worker(args)
        return run_orchestrator(args)
    except Exception as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False, indent=2), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
