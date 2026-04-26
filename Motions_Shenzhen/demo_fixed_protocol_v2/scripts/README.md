# Demo Fixed Protocol Scripts

这个目录放的是深圳演示用的**可执行固定动作脚本**。

## 使用规则

- 默认只打印远端执行计划
- 加 `--execute` 才真正通过 SSH 执行
- 所有动作都基于板端现有命令和脚本
- 不引入实时视觉或语音输入

## 脚本清单

- `01_presence_wake_demo.py`
- `02_cautious_intro_demo.py`
- `03_hand_nuzzle_faithful_demo.py`
- `03_from_07_right_hand_nuzzle_test.py`
- `04_offer_celebrate_demo.py`
- `05_farewell_demo.py`
- `06_sleep_demo.py`
- `07_tabletop_follow_demo.py`
- `08_photo_pose_demo.py`

## 对应关系

- `01_presence_wake_demo.py`
  - 对应：`Videos/01`
  - PDF 副本第 1 条
- `02_cautious_intro_demo.py`
  - 对应：`Videos/02`
  - PDF 副本第 2 条
- `03_hand_nuzzle_faithful_demo.py`
  - 对应：`Videos/03`
  - PDF 副本第 3 条
- `03_hand_nuzzle_demo.py`
  - 旧版备用脚本；其中 `--variant 04` 可作为 `Videos/04` 的短版接近 fallback
- `03_from_07_right_hand_nuzzle_test.py`
  - 测试脚本；承接 `03_from_07_start_light_test.py` 的 07 结束起始位和暖色灯光，直接实现右侧近距离摸一摸。
- `04_offer_celebrate_demo.py`
  - 对应：`Videos/05`
  - PDF 副本第 5 条
- `05_farewell_demo.py`
  - 对应：`Videos/06`
  - PDF 副本第 6 条
- `06_sleep_demo.py`
  - 对应：`Videos/07`
  - PDF 副本第 7 条
- `07_tabletop_follow_demo.py`
  - 对应：`Videos/08`
  - PDF 副本第 4 条：追踪 / 展示感知能力
- `08_photo_pose_demo.py`
  - 额外控制台动作：拍照
  - 只动 1/2 号关节，0/3 号不发动作命令

## 特别说明

`Videos/03` 和 `Videos/04` 都服务于第三个动作“摸一摸”，但分工不同。

因此：

- `03_hand_nuzzle_faithful_demo.py` 是主控台使用的新版主脚本，忠实表达 `Videos/03` 和 PDF 第 3 条的掌下亲密蹭手。
- `03_hand_nuzzle_demo.py --variant 04` 保留为手比较远时的短版目标接近备用。

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
python3 03_hand_nuzzle_faithful_demo.py --rub-cycles 6 --linger-seconds 1.0
python3 03_from_07_right_hand_nuzzle_test.py --nuzzle-cycles 2 --final-pose scene07
python3 03_hand_nuzzle_demo.py --variant 04 --rub-cycles 3
python3 04_offer_celebrate_demo.py --party-light spin --hold-seconds 1.2
python3 05_farewell_demo.py --nod-cycles 2 --linger-seconds 0.8
python3 06_sleep_demo.py --lights-off
python3 07_tabletop_follow_demo.py --correction-cycles 2 --final-pose target
python3 08_photo_pose_demo.py --target-1 1880 --target-2 1650
```
