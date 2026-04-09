# Portrait Person Count Tolerance Upgrade

## Why This Upgrade Was Needed

在展位近景里，摄像头经常会遇到下面这类画面：

- 人脸是斜的、歪的、只露半张
- 镜头离人很近，只拍到脸的一部分或上半身
- 两个人同时挤进镜头，但没有完整正脸
- 相机刚被转动过，画面里既有灯光天花板，也有人体局部

之前的 release 版 `track_target_event_extractor.py` 主要偏向：

- `frontal face`
- 完整 `HOG person`

这对标准正面人像有效，但对 booth 近景 portrait 还不够宽容，容易把“其实已经进画面的人”判成 `no_target`。

## What Changed

这次在 [Mira_Light_Released_Version/scripts/track_target_event_extractor.py](../../Mira_Light_Released_Version/scripts/track_target_event_extractor.py) 里做了 4 件事：

1. `face` 从单一 frontal cascade 升级成多路融合：
   - `haarcascade_frontalface_default`
   - `haarcascade_frontalface_alt2`
   - `haarcascade_profileface`
   - profile 镜像检测

2. 加入 `upperbody` 作为 booth 近景补充 cue：
   - 当人脸只露一部分、但上半身已进入画面时，仍然可以形成 `person` 候选。

3. 改成 `face + upperbody + HOG` 融合生成 person anchor：
   - face 会扩成更接近真实人的近景 bbox
   - upperbody/HOG 会和已有人像 anchor 合并
   - 不再只靠“完整正脸”或“完整人体框”

4. 增加两层误检抑制：
   - 合并同一人的多个 face-only 锚点，减少“同一人被拆成 2 个目标”
   - 丢弃过小、过高、且没有 upperbody/HOG 支撑的孤立 face 误检

## New Tuning Knobs

新增参数：

- `--face-min-neighbors`
- `--face-min-size`
- `--profile-face-min-neighbors`
- `--upperbody-min-neighbors`
- `--upperbody-min-size`
- `--standalone-hog-min-confidence`

默认值已经调到更适合展位近景 portrait 的口径，不需要先手动调参就能得到比原来更宽容的结果。

## Validation Snapshot

这次不是只跑单测，还直接对 live `captures` 做了抽样回归。

### Unit Tests

`Mira_Light_Released_Version/tests/test_track_target_event_extractor.py`

当前通过：

- `10 / 10`

新增覆盖了：

- 两个 face cue 能形成 `2 人`
- face + upperbody 会并成 `1 人`
- 弱 standalone HOG 不会直接算人

### Live Capture Regression

对最近 3 分钟 `captures` 抽样回归后，当前脚本已经能在真实 booth 近景画面里稳定给出：

- `1 人`
- `2 人`

继续增加“同一人多个人脸 cue 合并”之后，最近 3 分钟最新一轮抽样分布已经变成：

- `2 人`: 21
- `3 人`: 7
- `1 人`: 3

这说明当前口径已经明显从“经常 no_target”推进到了“多数情况下优先读成 2 人”，更贴近展位近景 portrait 的真实预期。

同时也要如实说明：

- 仍然有少量近景局部帧会报到 `3`
- 说明“多人近景 partial-body 计数”还没有完全收敛
- 但它已经明显好于早期版本的 `no_target` 或只认标准正脸

## Current Interpretation Boundary

现在更准确的口径是：

- 它已经能对 booth 近景 portrait 做“宽容的人像存在与人数估计”
- 它可以读出 `1 人 / 2 人`，并把主目标方向映射到 `left / center / right`
- 但它还不是严格意义上的高精度 crowd counting

也就是说，这条线已经足够支撑：

- `wake_up`
- `curious_observe`
- `multi_person_demo`
- 以及多人进入镜头时更合理的 `scene_hint`

但如果要把“2 人和 3 人”的边界在复杂近景里继续压稳，下一步仍然建议：

- 增加 overlay 可视化 bbox
- 用真实 booth 样本继续调 face-only / upperbody / hog 的融合阈值
- 必要时引入更强的人体 detector

## Practical Takeaway

一句话总结：

这次升级已经把 release 版的人像识别从“偏标准正脸/完整人体”推进到了“更像展位现场真实镜头”的宽容版本，并且已经在 live `captures` 上把主流结果压到了 `1 人 / 2 人`。
