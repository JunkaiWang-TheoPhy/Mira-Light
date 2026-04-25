# Demo Fixed Protocol

这是一个全新、干净的演示脚本目录。

目的只有一个：

> 把 `docs/Shenzhen/Videos/01-08` 和 `Mira Light 展位交互方案 副本.pdf` 对齐成 **7 个固定动作演示脚本**。

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
   -> `03_hand_nuzzle_demo.py`
4. `04_20260425_043825_01.mp4`
   -> `03_hand_nuzzle_demo.py`
   说明：视频 03 和 04 都视作第三个动作的不同取样 / 演示切片
5. `05_20260425_043828_01.mp4`
   -> `04_offer_celebrate_demo.py`
6. `06_20260425_043829_01.mp4`
   -> `05_farewell_demo.py`
7. `07_20260425_043829_02.mp4`
   -> `06_sleep_demo.py`
8. `08_20260425_043832_01.mp4`
   -> `07_tabletop_follow_demo.py`

## 对应关系到 PDF 副本

- 视频 01 -> PDF 第 1 条：起床
- 视频 02 -> PDF 第 2 条：好奇你是谁
- 视频 03/04 -> PDF 第 3 条：摸一摸
- 视频 05 -> PDF 第 5 条：庆祝 / offer 模式
- 视频 06 -> PDF 第 6 条：挥手送别
- 视频 07 -> PDF 第 7 条：睡觉
- 视频 08 -> PDF 第 4 条：追踪 / 展示感知能力

## 脚本目录

见：

- [scripts/README.md](./scripts/README.md)

## 深圳版主控台

这一版新增了一个专门适配 7 个固定动作任务的本地 Web 主控台：

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
