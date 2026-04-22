# Mira Light 方案2代码交付与继续开发说明

## 文档目的

这份文档是给“另一台电脑上的接手工程同学”准备的。

它回答的不是设计问题，而是交付问题：

- 现在到底该信哪份文档
- 现在代码已经做到哪一步
- 哪些文件要先读
- 哪些文件只是参考
- 继续开发时应该先改哪里
- 每一步要怎么验收

## 当前结论先行

### 1. 当前动作真值

当前动作实现、关节理解、场景审核，一律以：

- [`Mira Light 展位交互方案2.pdf`](../docs/Mira%20Light%20展位交互方案2.pdf)

为准。

参考优先级低于它的材料：

- [`Mira Light 展位交互方案.pdf`](../docs/Mira%20Light%20展位交互方案.pdf)
- [`Mira Light 展位交互方案1.pdf`](../docs/Mira%20Light%20展位交互方案1.pdf)
- [`Mira Light 展位交互方案3.pdf`](../docs/Mira%20Light%20展位交互方案3.pdf)

说明：

- `方案2` 是动作真值
- `方案3` 只在局部手绘细节上作为辅助
- 历史裁切图不是动作真值，也不再作为 release 目录的一部分

### 2. 当前硬件程序模型

程序层当前一律按 **4 个舵机关节** 实现：

- `servo1`：底座转向
- `servo2`：下臂抬升
- `servo3`：前段关节 / 中间关节抬升与前探
- `servo4`：灯头俯仰 / 微表情

当前不再假设额外的“底部前后摇摆”第五自由度。

### 3. 当前实现状态

十个主场景现在都已经进入：

- [`scripts/scenes.py`](../scripts/scenes.py)

其中：

- `wake_up / curious_observe / touch_affection / cute_probe / daydream` 已经是比较完整的 choreography
- `standup_reminder / celebrate / farewell / sleep` 也已经按 `方案2` 做了细化
- `track_target` 目前是 **排练用 surrogate choreography**，不是最终视觉闭环

当前逐场景解释已经收敛到：

- [`docs/mira-light-pdf2-implementation-audit.md`](../docs/mira-light-pdf2-implementation-audit.md)
- [`docs/mira-light-scene-implementation-index.md`](../docs/mira-light-scene-implementation-index.md)
- [`scripts/scenes.py`](../scripts/scenes.py)

## 接手时的文件优先级

### 第一层：动作真值

1. [`Mira Light 展位交互方案2.pdf`](../docs/Mira%20Light%20展位交互方案2.pdf)
2. [`ESP32 智能台灯.pdf`](../docs/ESP32%20智能台灯.pdf)

### 第二层：当前程序真值

1. [`scripts/scenes.py`](../scripts/scenes.py)
2. [`scripts/mira_light_runtime.py`](../scripts/mira_light_runtime.py)

### 第三层：场景说明

1. [`docs/mira-light-scene-implementation-index.md`](../docs/mira-light-scene-implementation-index.md)
2. [`docs/mira-light-pdf2-implementation-audit.md`](../docs/mira-light-pdf2-implementation-audit.md)

说明：

- 解释层现在直接留在 release docs 里
- 不再依赖单独的 `Figs` 镜像目录
- 一旦说明文档、代码、PDF 冲突，以 `方案2 PDF` 为准

### 第四层：当前交付状态解释

1. [`docs/mira-light-pdf2-implementation-audit.md`](../docs/mira-light-pdf2-implementation-audit.md)
2. 本文档

## 这轮开发到底做了什么

### 一、统一了四关节结论

之前项目内部存在动作理解不一致：

- 机械分析容易把动作看成五层
- 但 `ESP32` 设备接口只暴露 `servo1~servo4`

现在已经统一成：

- 机械解释可以更细
- 程序实现严格按 4 个舵机关节

### 二、把十个主场景都推进到代码层

当前已经进入 `scripts/scenes.py` 的主场景：

1. `wake_up`
2. `curious_observe`
3. `touch_affection`
4. `cute_probe`
5. `daydream`
6. `standup_reminder`
7. `track_target`（surrogate choreography）
8. `celebrate`
9. `farewell`
10. `sleep`

### 三、把每个场景都落成了代码侧动作说明

当前 release 已经不再保留单独的 `Figs/motions/` 目录。

场景解释统一收敛到：

- `scripts/scenes.py`
- `docs/mira-light-scene-implementation-index.md`
- `docs/mira-light-pdf2-implementation-audit.md`

## 接手时必须知道的三个事实

### 1. 历史裁切说明不是最终真值

原因：

- 它们来自 PDF 裁切
- 某些页跨场景
- 裁切位置是人工估计的

因此：

- 它们只能辅助理解
- 不能反向推翻 `方案2 PDF`

### 2. 旧文档仍然有参考价值，但不是动作真值

以下文档更适合做思路和总表参考：

- [`docs/mira-light-scene-to-code-spec.md`](../docs/mira-light-scene-to-code-spec.md)
- [`docs/mira-light-booth-scene-table.md`](../docs/mira-light-booth-scene-table.md)

### 3. 当前最大缺口已经不是“没场景”，而是“没闭环”

具体来说：

- 场景 choreography 已经有了
- 真正最大的工程缺口是 `track_target` 的感知闭环

## 当前十个主场景实现状态

### 已较完整实现的场景

- `wake_up`
- `curious_observe`
- `touch_affection`
- `cute_probe`
- `daydream`
- `standup_reminder`
- `celebrate`
- `farewell`（固定角度版）
- `sleep`

### 仍有关键剩余工程问题的场景

- `track_target`
  - 现在只是排练版 surrogate choreography
  - 还没有真实目标检测与闭环控制

- `farewell`
  - 现在是固定方向版
  - 还没有根据真实离场方向动态目送

## 接手电脑上的第一轮执行步骤

### 第 0 步：先建立真值顺序

按下面顺序读：

1. [`docs/Mira Light 展位交互方案2.pdf`](../docs/Mira%20Light%20展位交互方案2.pdf)
2. [`docs/ESP32 智能台灯.pdf`](../docs/ESP32%20智能台灯.pdf)
3. [`scripts/scenes.py`](../scripts/scenes.py)
4. [`docs/mira-light-pdf2-implementation-audit.md`](../docs/mira-light-pdf2-implementation-audit.md)
5. 本文档
6. [`docs/mira-light-scene-implementation-index.md`](../docs/mira-light-scene-implementation-index.md)

### 第 1 步：先验证代码可加载

```bash
cd Mira_Light_Released_Version
python3 -m py_compile scripts/scenes.py
python3 scripts/booth_controller.py --list
```

### 第 2 步：先用 dry-run 看动作

```bash
python3 scripts/booth_controller.py --base-url http://172.20.10.3 --dry-run wake_up
python3 scripts/booth_controller.py --base-url http://172.20.10.3 --dry-run curious_observe
python3 scripts/booth_controller.py --base-url http://172.20.10.3 --dry-run touch_affection
python3 scripts/booth_controller.py --base-url http://172.20.10.3 --dry-run cute_probe
python3 scripts/booth_controller.py --base-url http://172.20.10.3 --dry-run daydream
python3 scripts/booth_controller.py --base-url http://172.20.10.3 --dry-run standup_reminder
python3 scripts/booth_controller.py --base-url http://172.20.10.3 --dry-run track_target
python3 scripts/booth_controller.py --base-url http://172.20.10.3 --dry-run celebrate
python3 scripts/booth_controller.py --base-url http://172.20.10.3 --dry-run farewell
python3 scripts/booth_controller.py --base-url http://172.20.10.3 --dry-run sleep
```

目标：

- 先验证动作顺序和灯光顺序
- 不要一上来就在真机上大幅动作

### 第 3 步：真机校准

优先校准这些关键姿态：

- `sleep`
- `neutral`
- `wake_half`
- `wake_high`
- `extend_soft`
- `retract_soft`
- `reminder_ready`
- `celebrate_ready`
- `farewell_bow`
- `sleep_ready`

推荐工具：

- [`scripts/calibrate_lamp.py`](../scripts/calibrate_lamp.py)
- [`config/mira_light_profile.example.json`](../config/mira_light_profile.example.json)

### 第 4 步：改任何一个场景时，至少同步三处

1. [`scripts/scenes.py`](../scripts/scenes.py)
2. [`docs/mira-light-scene-implementation-index.md`](/Users/Zhuanz/Documents/GitHub/Mira-Light/docs/mira-light-scene-implementation-index.md)
3. [`docs/mira-light-pdf2-implementation-audit.md`](../docs/mira-light-pdf2-implementation-audit.md)

如果影响导演台语义，还要同步：

- [`web/app.js`](../web/app.js)
- [`web/index.html`](../web/index.html)

## 当前最推荐的下一步开发顺序

推荐顺序：

1. 真机校准十个主场景的关键姿态
2. `track_target`
3. `farewell` 动态目送
4. 导演台同步

原因：

- 前九个场景现在都已经有较清晰的 choreography
- 最大工程缺口已经变成 `track_target` 的感知闭环
- `farewell` 的主要剩余价值是动态离场方向跟随

## 每个后续任务的最小验收标准

### `track_target`

验收通过标准：

- 目标移动时，灯头连续跟随
- 目标停时，跟随停止
- 再移动时，恢复跟随

### `farewell` 动态版

验收通过标准：

- 目送方向不再固定
- 挥手和低头仍然保留

### 导演台同步

验收通过标准：

- 导演台显示的 scene 信息、时长、动作语义和当前代码一致

## 不要做的事

- 不要根据历史裁切图或旧图示反推真值
- 不要重新引入“第五个程序关节”抽象
- 不要跳过 dry-run 就直接上真机乱试
- 不要把旧 `方案.pdf / 方案1.pdf` 当作当前实现真值

## 一句话总结

这次 handoff 的核心不是“把仓库丢给另一台电脑”，而是把真值顺序、当前实现状态和继续开发顺序一起交过去。

对于接手者来说，最重要的不是先写代码，而是先接受这三件事：

1. 动作真值现在是 `方案2 PDF`
2. 程序实现严格按 4 个舵机关节
3. 十个主场景已经都进入代码层，但 `track_target` 仍需要真正做成感知闭环
