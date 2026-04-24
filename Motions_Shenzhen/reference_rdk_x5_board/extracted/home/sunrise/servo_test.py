#!/usr/bin/env python3
import os
import sys
import time
import signal
import subprocess

def signal_handler(sig, frame):
    print("\nCtrl+C, cleaning up...")
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

# ========== Step 1: 查找 PWM3 对应的 pwmchip ==========
# RDK X5 PWM3 -> pin 32 (ch6), pin 33 (ch7)
# 先扫描 /sys/class/pwm/ 下所有 pwmchip

def run(cmd):
    r = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    return r.stdout.strip(), r.returncode

def find_pwm():
    """扫描所有 pwmchip, 返回 (chip_path, channel)"""
    pwm_base = "/sys/class/pwm"
    out, rc = run(f"ls {pwm_base}")
    if rc != 0:
        print(f"[ERROR] 无法访问 {pwm_base}")
        sys.exit(1)
    chips = [c for c in out.split() if c.startswith("pwmchip")]
    print(f"[INFO] 发现 PWM 控制器: {chips}")
    for chip in chips:
        chip_path = f"{pwm_base}/{chip}"
        npwm, _ = run(f"cat {chip_path}/npwm")
        device, _ = run(f"readlink -f {chip_path}/device")
        print(f"  {chip}: npwm={npwm}, device={device}")
    return chips

def sysfs_pwm_control(chip_path, channel, period_ns, duty_ns):
    """通过 sysfs 设置 PWM"""
    pwm_path = f"{chip_path}/pwm{channel}"
    if not os.path.exists(pwm_path):
        run(f"echo {channel} > {chip_path}/export")
        time.sleep(0.2)
    if not os.path.exists(pwm_path):
        return False
    run(f"echo 0 > {pwm_path}/enable")
    run(f"echo {period_ns} > {pwm_path}/period")
    run(f"echo {duty_ns} > {pwm_path}/duty_cycle")
    run(f"echo 1 > {pwm_path}/enable")
    return True

def set_duty(pwm_path, duty_ns):
    run(f"echo {duty_ns} > {pwm_path}/duty_cycle")

def angle_to_ns(angle, period_ns=20000000):
    """角度 -> 占空比(ns), 0.5ms~2.5ms 对应 0~180度"""
    pulse_min = 500000    # 0.5ms
    pulse_max = 2500000   # 2.5ms
    return int(pulse_min + (pulse_max - pulse_min) * angle / 180.0)

def main():
    print("=" * 50)
    print("  RDK X5 舵机测试 (sysfs PWM 直接控制)")
    print("=" * 50)

    chips = find_pwm()
    if not chips:
        print("[ERROR] 没有找到任何 PWM 控制器")
        sys.exit(1)

    # 尝试每个 pwmchip 的每个通道, 找到能用的
    pwm_base = "/sys/class/pwm"
    period_ns = 20000000  # 20ms = 50Hz
    mid_duty = angle_to_ns(90)

    found = False
    chip_path = ""
    channel = 0

    # 优先试 PWM3 (默认使能的), 通常是最后一个 chip
    # PWM3 有2路: channel 0 = pin32, channel 1 = pin33
    for chip in reversed(chips):
        chip_path = f"{pwm_base}/{chip}"
        npwm_str, _ = run(f"cat {chip_path}/npwm")
        try:
            npwm = int(npwm_str)
        except:
            continue
        for ch in range(npwm):
            pwm_path = f"{chip_path}/pwm{ch}"
            print(f"\n[尝试] {chip} channel {ch} ...")
            if sysfs_pwm_control(chip_path, ch, period_ns, mid_duty):
                # 验证是否成功
                en, _ = run(f"cat {pwm_path}/enable")
                per, _ = run(f"cat {pwm_path}/period")
                dut, _ = run(f"cat {pwm_path}/duty_cycle")
                print(f"  enable={en}, period={per}, duty_cycle={dut}")
                if en.strip() == "1":
                    found = True
                    channel = ch
                    print(f"[OK] 使用 {chip} channel {ch}")
                    break
        if found:
            break

    if not found:
        print("\n[ERROR] 无法启用任何 PWM 通道!")
        print("请先运行 sudo srpi-config 使能 PWM3")
        sys.exit(1)

    pwm_path = f"{chip_path}/pwm{channel}"
    print(f"\n[INFO] PWM 已启动: 50Hz, pin 33 (中位 90度)")
    print("[INFO] 按 Ctrl+C 退出\n")

    try:
        while True:
            # 0 -> 180
            for angle in range(0, 181, 10):
                duty = angle_to_ns(angle)
                set_duty(pwm_path, duty)
                print(f"  角度: {angle:>3}°  脉宽: {duty/1000:.0f}us")
                time.sleep(0.5)
            time.sleep(0.5)
            # 180 -> 0
            for angle in range(180, -1, -10):
                duty = angle_to_ns(angle)
                set_duty(pwm_path, duty)
                print(f"  角度: {angle:>3}°  脉宽: {duty/1000:.0f}us")
                time.sleep(0.5)
            time.sleep(0.5)
    finally:
        run(f"echo 0 > {pwm_path}/enable")
        print("[INFO] PWM 已停止")

if __name__ == "__main__":
    main()