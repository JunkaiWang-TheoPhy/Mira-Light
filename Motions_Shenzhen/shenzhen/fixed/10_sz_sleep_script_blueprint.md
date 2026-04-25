# `sz_sleep` 具体脚本蓝图

这份文档是在 [10_sz_farewell_sleep_fixed.md](./10_sz_farewell_sleep_fixed.md) 的基础上，再往前推进一层。

它专门回答：

> 如果基于 `07_20260425_043829_02.mp4` 和 `Mira Light 展位交互方案 副本.pdf` 第 7 条来写第一版脚本，应该怎样具体拆动作。

## 参考依据

### 视频

- `docs/Shenzhen/Videos/07_20260425_043829_02.mp4`

这段视频时长约 `51.8s`，明显比送别段更长。

这说明它不是一句“收回去”的机械收尾，而是一段完整的入睡过程。

从节奏上看，它更像：

- 先慢慢松下来
- 中间有一个小舒展
- 再真正折叠回睡姿

### PDF 第 7 条

副本 PDF 第 `14~17` 页写的是：

1. 评委走远了
2. Mira 慢慢低头
3. 灯臂缓缓降下去
4. 做一个“伸懒腰”
5. 先舒展一下
6. 再蜷缩起来
7. 回到折叠状态
8. 灯光变暗到微光

这说明这一条不是“直接关机”，而是：

> 先放松一下，再真正睡下去。

## 当前版本的总体策略

第一版先做 **独立睡觉脚本**，而不是一上来就和 farewell 严格绑死。

原因：

- 送别和入睡虽然可以串联
- 但设计上最好先把“睡觉段”本身做稳

所以第一版建议：

- 先让 `sz_sleep` 成为一个独立固定脚本
- 后续再和 `farewell` 串成 `farewell_sleep`

## 推荐脚本名

建议脚本名：

```text
sz_sleep_fixed.py
```

如果继续挂在主线命名下，也可以在：

```text
sz_farewell_sleep
```

内部保留一个独立 `sleep_phase`。

## 推荐动作分段

建议拆成 **6 段**。

### 第 0 段：柔和结束位

目标：

- 从一个正常或 farewell 之后的柔和姿态开始
- 不要从一个极端高位或乱姿态直接切入

第一版建议先统一到：

```bash
python3 /home/sunrise/Desktop/four_servo_control.py pose 2048 2150 2048 2130 --speeds 200 100 100 200
```

## 第 1 段：慢慢低头

目标：

- 先让“注意力”掉下来
- 让观众感觉到它困了、准备休息了

这一段重点是情绪下降，不是结构折叠。

建议：

- 小幅下压
- 停半拍

## 第 2 段：灯臂缓缓降下去

目标：

- 让身体也进入收场趋势
- 和第 1 段形成“情绪先下去，身体再跟下去”的两层感

这一步不要和低头合成一拍。

## 第 3 段：先舒展一下

目标：

- 这是整条 scene 最关键的生命感细节
- 不是继续收拢，而是先放松地舒展一下

如果没有这一拍，整个 scene 会像直接归零。

当前板端最适合借的就是：

- `sleep_motion.py`

因为它本身就有一种“先一段，再一段”的 staged 收场节奏。

## 第 4 段：再蜷缩起来

目标：

- 这才是真正回到睡姿
- 身体折叠
- 灯头也贴回更休息的位置

推荐板端脚本：

- `sleep_motion_with_03_return.py`
- 或 `sleep_motion_return_03.py`

这一步是“真正归位”的关键。

## 第 5 段：灯光变暗到微光

目标：

- 和动作一起进入睡眠状态
- 不要机械臂睡了，灯还亮着工作光

第一版建议：

```bash
python3 /home/sunrise/Desktop/send_uart3_led_cmd.py all 255 180 120 40
```

如果要更彻底，再补：

```bash
python3 /home/sunrise/Desktop/send_uart3_led_cmd.py off
```

但第一版其实保留微光比直接全灭更像“睡着了”。

## 第一版最推荐的命令拼装顺序

如果先不写完整脚本，只想做一版近似演示，可以这样拼：

```bash
python3 /home/sunrise/Desktop/four_servo_control.py pose 2048 2150 2048 2130 --speeds 200 100 100 200
python3 /home/sunrise/Desktop/send_uart3_led_cmd.py all 255 220 180 100
python3 /home/sunrise/Desktop/sleep_motion.py --speeds 1000 160 680 1000 --delay-ratio 0.68
python3 /home/sunrise/Desktop/sleep_motion_with_03_return.py
python3 /home/sunrise/Desktop/send_uart3_led_cmd.py all 255 180 120 40
python3 /home/sunrise/Desktop/send_uart3_led_cmd.py off
```

这条近似版已经能比较完整地表达：

- 先低下来
- 再收回去
- 光也一起睡下去

## 第一版脚本结构建议

建议写成：

```python
def enter_soft_end_pose():
    ...

def lower_head():
    ...

def lower_arm():
    ...

def small_relax_stretch():
    ...

def fold_into_sleep():
    ...

def dim_to_sleep_light():
    ...

def main():
    enter_soft_end_pose()
    lower_head()
    lower_arm()
    small_relax_stretch()
    fold_into_sleep()
    dim_to_sleep_light()
```

## 当前固定版能证明什么

它能证明：

- Mira 会主动结束一轮互动
- 它的收场像“入睡”，不是机械归零
- 观众能看懂“放松 -> 蜷缩 -> 微光”的过程

它还不能证明：

- 已经根据现场是否还有人自动决定要不要睡
- 已经和 `farewell` 严格自动串联

## 第二版再做什么

第二版再补：

1. 和 `farewell` 串成 `farewell_sleep`
2. 加 `lingerMs`
3. 加 `sleepDelayMs`
4. 决定最后是微光还是全灭

## 一句话总结

按 `Videos/07` 和这个 PDF 副本里的第 7 条来设计，第一版最正确的做法是：

> 先做一条固定睡觉脚本：慢慢低头 -> 缓缓降臂 -> 小舒展一下 -> 再蜷缩回去 -> 灯光变暗到微光。
