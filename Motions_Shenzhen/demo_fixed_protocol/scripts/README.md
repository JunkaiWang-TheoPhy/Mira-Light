# Demo Fixed Protocol Scripts

这个目录放的是 7 个**可执行的固定动作演示脚本**。

## 使用规则

- 默认只打印远端执行计划
- 加 `--execute` 才真正通过 SSH 执行
- 所有动作都基于板端现有命令和脚本
- 不引入实时视觉或语音输入

## 脚本清单

- `01_presence_wake_demo.py`
- `02_cautious_intro_demo.py`
- `03_hand_nuzzle_demo.py`
- `04_offer_celebrate_demo.py`
- `05_farewell_demo.py`
- `06_sleep_demo.py`
- `07_happy_reaction_demo.py`

## 对应关系

- `01_presence_wake_demo.py`
  - 对应：`Videos/01`
  - PDF 副本第 1 条
- `02_cautious_intro_demo.py`
  - 对应：`Videos/02`
  - PDF 副本第 2 条
- `03_hand_nuzzle_demo.py`
  - 对应：`Videos/03` 与 `Videos/04`
  - PDF 副本第 3 条
- `04_offer_celebrate_demo.py`
  - 对应：`Videos/05`
  - PDF 副本第 5 条
- `05_farewell_demo.py`
  - 对应：`Videos/06`
  - PDF 副本第 6 条
- `06_sleep_demo.py`
  - 对应：`Videos/07`
  - PDF 副本第 7 条
- `07_happy_reaction_demo.py`
  - 对应：`Videos/08`
  - PDF 副本后半段“开心”补充交互

## 特别说明

`Videos/03` 和 `Videos/04` 都对应第三个动作“摸一摸”。

因此：

- 不新建两个脚本
- 只保留一个 `03_hand_nuzzle_demo.py`
- 如有需要，通过 `--variant` 区分两段视频强调的不同节奏

## 示例

预览：

```bash
python3 01_presence_wake_demo.py
```

执行：

```bash
python3 01_presence_wake_demo.py --execute
```

更多示例：

```bash
python3 03_hand_nuzzle_demo.py --variant 04 --rub-cycles 3
python3 04_offer_celebrate_demo.py --party-light spin --hold-seconds 1.2
python3 05_farewell_demo.py --nod-cycles 2 --linger-seconds 0.8
python3 06_sleep_demo.py --keep-glow
python3 07_happy_reaction_demo.py --light-style rainbow --bounce-twice
```
