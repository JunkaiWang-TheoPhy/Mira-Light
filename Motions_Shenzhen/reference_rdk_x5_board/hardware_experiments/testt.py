import os
import time

class HardwareServo:
    def __init__(self, pwmchip=0, channel=0):
        """
        通过 Linux Sysfs 直接操作硬件 PWM 寄存器
        pwmchip: PWM 控制器编号 (通常是 0 或 1)
        channel: 该控制器下的通道编号 (通常是 0 或 1)
        """
        self.base_dir = f"/sys/class/pwm/pwmchip{pwmchip}"
        self.pwm_dir = f"{self.base_dir}/pwm{channel}"
        self.channel = channel
        
        print(f"[硬件PWM] 正在初始化 {self.pwm_dir} ...")
        
        # 1. 导出 PWM 通道 (如果还没有导出的话)
        if not os.path.exists(self.pwm_dir):
            try:
                self._write_file(f"{self.base_dir}/export", str(self.channel))
                time.sleep(0.1)  # 等待系统生成目录
            except Exception as e:
                print(f"导出 PWM 失败: {e}。请确认引脚映射并使用 sudo 运行。")
                return

        # 2. 设置周期 (Period)
        # 50Hz = 20毫秒 (ms) = 20,000,000 纳秒 (ns)
        # 注意：必须先设周期，再设占空比，否则内核会报错
        self._write_file(f"{self.pwm_dir}/period", "20000000")
        
        # 3. 设置默认占空比 (90度中位)
        # 1.5ms = 1,500,000 ns
        self._write_file(f"{self.pwm_dir}/duty_cycle", "1500000")
        
        # 4. 使能输出 (Enable)
        self._write_file(f"{self.pwm_dir}/enable", "1")
        print("[硬件PWM] 舵机已锁定在中位，此时应完全无抖动。")

    def _write_file(self, path, value):
        """写入系统文件的辅助函数"""
        try:
            with open(path, 'w') as f:
                f.write(value)
        except PermissionError:
            print(f"❌ 权限被拒绝: 无法写入 {path}。")
            print("👉 必须使用 sudo 权限运行此脚本！")
            exit(1)
        except Exception as e:
            print(f"写入 {path} 失败: {e}")

    def set_angle(self, angle):
        """
        设置舵机角度 (0 - 180)
        """
        # 限制角度范围
        angle = max(0, min(180, angle))
        
        # 计算高电平时间（纳秒）
        # 0度 = 0.5ms = 500,000 ns
        # 180度 = 2.5ms = 2,500,000 ns
        ns_per_degree = (2500000 - 500000) / 180.0
        duty_cycle_ns = int(500000 + (angle * ns_per_degree))
        
        # 直接写入底层寄存器，瞬间生效，零延迟零抖动
        self._write_file(f"{self.pwm_dir}/duty_cycle", str(duty_cycle_ns))

    def stop(self):
        """关闭 PWM 输出"""
        self._write_file(f"{self.pwm_dir}/enable", "0")
        print("[硬件PWM] 舵机信号已切断。")

# =========================================
# 测试逻辑
# =========================================
if __name__ == '__main__':
    # 注意：Hobot 物理引脚 33 具体对应哪个 pwmchip 和 channel
    # 如果运行报错找不到路径，请尝试 pwmchip=1, channel=0 或 pwmchip=0, channel=1
    servo = HardwareServo(pwmchip=0, channel=0)
    
    try:
        print("\n准备测试，你可以尝试用手掰一下舵机摇臂，它现在应该像焊死了一样稳。")
        time.sleep(2)
        
        for target in [0, 90, 180, 45, 135]:
            print(f"前往 {target} 度...")
            servo.set_angle(target)
            time.sleep(1.5)
            
    except KeyboardInterrupt:
        pass
    finally:
        servo.stop()