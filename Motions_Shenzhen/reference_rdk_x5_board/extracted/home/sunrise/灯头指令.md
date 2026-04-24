# esp-mira 串口控制指令文档

## 硬件配置

| 参数 | 值 |
|------|----|
| 控制器 | ESP32 |
| LED 引脚 / 触摸引脚 | GPIO 15 / GPIO 14 |
| UART2 RX/TX | GPIO 16 / 17 |
| LED 总数 | 40 颗（外环 group=0：0\~23，内环 group=1：0\~15） |
| LED 类型 | NeoPixel（NEO_GRB, 800KHz） |
| 串口波特率 | 115200，文本格式，每条指令以 `\n` 结尾 |

两路串口同时有效：**USB Serial**（Arduino IDE）和 **UART2**（外部硬件）。

---

## 指令速查

| 指令 | 格式 | 说明 |
|------|------|------|
| ALL | `ALL,R,G,B,BRI` | 全部 40 颗设为同一颜色 |
| ONE | `ONE,grp,idx,R,G,B,BRI` | 点亮单颗，其余熄灭 |
| BRI | `BRI,val` | 整体调亮度，颜色不变 |
| OFF | `OFF` | 熄灭全部 |
| RAINBOW | `RAINBOW[,BRI]` | 静态彩虹渐变（默认亮度 200） |
| *(预制效果)* BREATHE | `BREATHE[,R,G,B[,BRI]\|RAINBOW[,BRI]]` | 呼吸灯（循环淡入淡出） |
| *(预制效果)* WAKE | `WAKE[,R,G,B[,BRI]\|RAINBOW[,BRI]]` | 唤醒：内环→外环依次淡入 |
| *(预制效果)* SPIN | `SPIN[,R,G,B[,ODIR,IDIR[,BRI]]\|RAINBOW[,ODIR,IDIR[,BRI]]]` | 旋转流光 |
| STOP | `STOP` | 暂停动画（自动保存状态） |
| RESUME | `RESUME` | 从上次 STOP 恢复动画 |
| THR | `THR,val` | 触摸阈值（1\~2000，默认 32） |
| HELP | `HELP` | 串口打印指令列表 |

> **颜色参数通用规则**：`R/G/B` 范围 0\~255；`BRI` 亮度 0\~255，默认 200；`RAINBOW` 替代固定颜色时按环内位置分配色相。

---

## 指令详情

### ALL / ONE / BRI / OFF

```
ALL,255,0,0,200          → 全部红色，亮度 200
ONE,0,12,0,255,0,200     → 外环第 13 颗绿色，其余熄灭
ONE,1,0,0,0,255,200      → 内环第 1 颗蓝色，其余熄灭
BRI,128                  → 当前颜色半亮度
OFF                      → 全部熄灭
```

### RAINBOW

```
RAINBOW          → 彩虹，亮度 200
RAINBOW,150      → 彩虹，亮度 150
```

---

## 预制灯光效果

### BREATHE — 呼吸灯

全部 LED 循环淡入淡出。

```
BREATHE                  → 白色呼吸
BREATHE,0,0,255,150      → 蓝色呼吸，最大亮度 150
BREATHE,RAINBOW          → 彩虹呼吸
```

### WAKE — 唤醒动画

内环 16 颗整体淡入（约 1.6s）→ 外环 24 颗整体淡入（约 1.6s），结束后保持全亮。

```
WAKE                 → 白色唤醒
WAKE,0,200,255       → 青色唤醒
WAKE,RAINBOW,150     → 彩虹唤醒，亮度 150
```

### SPIN — 旋转流光

内外环各一道流光持续旋转，头部最亮尾部渐暗，首尾无缝衔接。`ODIR`/`IDIR`：`0`=顺时针（默认），`1`=逆时针。

```
SPIN                      → 白色同向旋转
SPIN,255,0,0,0,1          → 红色，外顺内逆
SPIN,RAINBOW,0,1,180      → 彩虹，外顺内逆，亮度 180
```

### STOP / RESUME

`STOP` 暂停动画并保存当前状态；`RESUME` 从该状态继续。
使用 ALL / ONE / BRI / OFF / RAINBOW 也会停止动画，但**不**保存状态。

---

## 触摸配置与事件

### THR — 触摸阈值

触摸值低于阈值时判定为触摸，数值越大越灵敏。

```
THR,50    → 提高灵敏度
THR,20    → 降低灵敏度
```

### 触摸事件上报

```
TOUCH,PRESS,<val>      → 按下
TOUCH,RELEASE,<val>    → 松开
TOUCH,HOLD,<val>       → 持续按住（每 500ms 一次）
```

---

## 响应格式

| 响应 | 说明 |
|------|------|
| `OK ALL R,G,B,BRI` | 成功 |
| `OK ONE grp=x idx=x R,G,B,BRI` | 成功 |
| `OK BRI val` | 成功 |
| `OK OFF` | 成功 |
| `OK RAINBOW bri=val` | 成功 |
| `OK THR val` | 成功 |
| `OK BREATHE COLOR\|RAINBOW bri=val` | 动画已启动 |
| `OK WAKE COLOR\|RAINBOW bri=val` | 动画已启动 |
| `OK SPIN COLOR\|RAINBOW outer=CW\|CCW inner=CW\|CCW bri=val` | 动画已启动 |
| `OK STOP` | 已暂停（状态已保存） |
| `OK RESUME BREATHE\|WAKE\|SPIN` | 已恢复 |
| `ERR ...` | 格式错误或参数非法 |
