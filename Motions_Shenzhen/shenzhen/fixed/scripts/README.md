# Shenzhen Fixed Scripts

这个目录放的是 `Motions_Shenzhen/shenzhen/fixed/` 对应的**可执行脚本**，不是说明文档。

## 设计原则

- 默认只打印远端执行计划，不直接发到板子
- 传 `--execute` 才真正通过 SSH 在端侧执行
- 优先复用板端已有脚本和灯头命令
- 现阶段尽量使用固定动作，不做实时计算

## 公共辅助层

- `common.py`

它负责：

- 统一解析 SSH 参数
- 统一渲染远端步骤计划
- 统一执行远端 bash 脚本

## 预期脚本清单

当前计划落地：

- `01_sz_presence_wake_fixed.py`
- `02_sz_cautious_intro_fixed.py`
- `03_sz_hand_nuzzle_fixed.py`
- `07_sz_sigh_comfort_fixed.py`
- `08_sz_voice_affect_response_fixed.py`
- `09_sz_multi_guest_choice_fixed.py`
- `10_sz_farewell_sleep_fixed.py`

参考 / 额外脚本：

- `04_pdf_tabletop_follow_fixed.py`
- `05_pdf_offer_celebrate_fixed.py`
- `06_pdf_farewell_fixed.py`
- `06_sz_tabletop_follow_fixed.py`

## 编号说明

这里现在同时存在两套命名：

### Shenzhen 主线命名

- `01_sz_presence_wake_fixed.py`
- `02_sz_cautious_intro_fixed.py`
- `03_sz_hand_nuzzle_fixed.py`
- `07_sz_sigh_comfort_fixed.py`
- `08_sz_voice_affect_response_fixed.py`
- `09_sz_multi_guest_choice_fixed.py`
- `10_sz_farewell_sleep_fixed.py`

### 按 `副本.pdf` / `Videos/01-06` 对照的参考命名

- `04_pdf_tabletop_follow_fixed.py`
- `05_pdf_offer_celebrate_fixed.py`
- `06_pdf_farewell_fixed.py`

这些脚本主要用于：

- 对齐你后来补看的视频 / PDF 副本编号
- 快速做“按视频编号”的演示验证

## 使用方式

打印远端动作计划：

```bash
python3 <script>.py
```

真正执行：

```bash
python3 <script>.py --execute
```

## 示例

预览“起床”固定版：

```bash
python3 01_sz_presence_wake_fixed.py --light-mode warm --hold-high-seconds 1.5
```

执行“好奇你是谁”固定版：

```bash
python3 02_sz_cautious_intro_fixed.py --extra-peek --execute
```

预览“摸一摸”固定版：

```bash
python3 03_sz_hand_nuzzle_fixed.py --light-style breathe --rub-cycles 3
```

执行“叹气安慰”固定版：

```bash
python3 07_sz_sigh_comfort_fixed.py --execute
```

预览“语音情绪反馈”里的 praise 分支：

```bash
python3 08_sz_voice_affect_response_fixed.py --intent praise
```

执行“多人时选谁看”固定版：

```bash
python3 09_sz_multi_guest_choice_fixed.py --winner right --execute
```

执行“送别并睡觉”固定版：

```bash
python3 10_sz_farewell_sleep_fixed.py --execute
```
