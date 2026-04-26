# Demo Fixed Protocol

这是一个全新、干净的演示脚本目录。

目的只有一个：

> 把 `docs/Shenzhen/Videos/01-08` 和 `Mira Light 展位交互方案 副本.pdf` 对齐成 **7 个固定动作演示脚本**，并保留一个额外的 `08` 拍照姿态。

## 设计原则

- 不复用旧的混乱命名
- 不依赖实时视觉或语音输入
- 严格对齐当前板端已有命令格式
- 默认只打印远端执行计划
- 传 `--execute` 才真正通过 SSH 执行

## 8 个视频到 7 个脚本的映射

1. `01_20260425_043820_01.mp4`
   -> `01_presence_wake_demo.py`
2. `02_20260425_043823_01.mp4`
   -> `02_cautious_intro_demo.py`
3. `03_20260425_043824_01.mp4`
   -> `03_hand_nuzzle_faithful_demo.py`
4. `04_20260425_043825_01.mp4`
   -> `03_hand_nuzzle_demo.py`
   说明：视频 03 是第三个动作“摸一摸”的主参考；视频 04 保留在旧脚本里作为手较远时的短版接近备用。
5. `05_20260425_043828_01.mp4`
   -> `04_offer_celebrate_demo.py`
6. `06_20260425_043829_01.mp4`
   -> `05_farewell_demo.py`
7. `07_20260425_043829_02.mp4`
   -> `06_sleep_demo.py`
8. `08_20260425_043832_01.mp4`
   -> `07_tabletop_follow_demo.py`

额外控制台动作：

- `08_photo_pose_demo.py`
  -> 控制台 `08` 拍照；只动 1/2 号关节，0/3 号不发动作命令。

## 对应关系到 PDF 副本

- 视频 01 -> PDF 第 1 条：起床
- 视频 02 -> PDF 第 2 条：好奇你是谁
- 视频 03/04 -> PDF 第 3 条：摸一摸
- 视频 05 -> PDF 第 5 条：庆祝 / offer 模式
- 视频 06 -> PDF 第 6 条：挥手送别
- 视频 07 -> PDF 第 7 条：睡觉
- 视频 08 -> PDF 第 4 条：追踪 / 展示感知能力

## 实机方向 Lesson

这些方向来自深圳桌面追踪实机观察，后续改 `four_servo_control.py pose p0 p1 p2 p3` 时优先按这里理解：

- 3 号关节数字变小是向左偏移，不要仅凭脚本里的 `left/right` 文案反推物理方向。
- 0 号关节数字变大是向右偏移。
- 1 号关节数字增大表示更向上 / 抬起。
- 2 号关节数字增大表示更向下 / 低头贴桌面。

## 脚本目录

见：

- [scripts/README.md](./scripts/README.md)

## 深圳版主控台

这一版新增了一个专门适配深圳固定动作任务的本地 Web 主控台：

- [console/](./console/)

启动：

```bash
cd /Users/Zhuanz/Documents/Github/Mira-Light/Motions_Shenzhen/demo_fixed_protocol_v2/console
./start_shenzhen_console.sh
```

然后打开：

```text
http://127.0.0.1:8777
```

主控台默认只预览命令；点击“执行真机”才会通过 SSH 发到板端。

如果板端没有配置免密 SSH，可以在网页里临时输入密码，或在启动前设置：

```bash
export MIRA_SHENZHEN_BOARD_PASSWORD='rootroot'
./start_shenzhen_console.sh
```

密码不会写进仓库；它只在本地控制台进程中使用。

## 一句话总结

这里不是规格文档层，而是：

> 一套按“最新视频 + PDF 副本”重新编号、重新命名、固定动作优先、协议对齐的演示脚本层。
