# Mock Sensors and 40-Pixel Visualization Progress

## Purpose

这份文档专门记录 `Mira Light` 当前在 mock 排练链路里已经落下来的两类能力：

- `headCapacitive` 头部电容 `0 / 1` 注入与可视化
- `40` 灯 `pixelSignals` 的真实信号链路与图形化面板

它回答的是三个问题：

1. 仓库现在是否已经能完整模拟这两类信号
2. 导演台是否已经能直接操作并看见这些信号
3. 当前边界在哪里，下一步还值得补什么

## Why This Matters

对 `Mira Light` 来说，mock 不只是“没有真灯时凑合看一下”。

如果 mock 能完整覆盖：

- 四关节
- 头部电容
- `40` 灯逐像素信号
- scene / runtime / bridge / console 全链路

那么团队在没有实体灯的时候，仍然可以稳定推进：

- `touch_affection` 相关排练
- LED pattern review
- director console 交互设计
- bridge/runtime 回归验证
- operator training

这会明显降低“真灯不在场就完全停工”的情况。

## Repository Now Includes

### 1. Mock device now covers head capacitive sensor state

相关文件：

- [`../../scripts/mock_mira_light_device.py`](../../scripts/mock_mira_light_device.py)
- [`../../scripts/mock_lamp_server.py`](../../scripts/mock_lamp_server.py)

仓库现在已经支持：

- `GET /sensors`
- `POST /sensors`
- 在 `/status` 里返回 `sensors.headCapacitive`

其中 `headCapacitive` 只接受：

- `0`
- `1`

这意味着 mock 已经不再只是“关节和整体灯光”的模拟，而开始覆盖真实交互输入。

### 2. Mock device now covers 40-light pixel signals

相关文件：

- [`../../scripts/mock_mira_light_device.py`](../../scripts/mock_mira_light_device.py)
- [`../../scripts/mock_lamp_server.py`](../../scripts/mock_lamp_server.py)
- [`../../scripts/mira_light_runtime.py`](../../scripts/mira_light_runtime.py)

当前 mock 已支持的灯信号结构为：

```json
[
  [R, G, B, brightness],
  [R, G, B, brightness],
  ...
]
```

总长度为：

- `40`

其中：

- 前三项是 `R / G / B`
- 第四项是单像素亮度 `brightness`

与此同时，runtime 侧也已经接受：

- `RGB`
- `RGBA-like pixel payload`
- `vector mode` 下的 per-pixel brightness

这让 `solid`、`vector`、以及从统一色推导 `pixelSignals` 的路径都能收敛到一套前端可视化逻辑。

### 3. Bridge API already proxies sensor state

相关文件：

- [`../../tools/mira_light_bridge/bridge_server.py`](../../tools/mira_light_bridge/bridge_server.py)
- [`../../tools/mira_light_bridge/bridge_client.py`](../../tools/mira_light_bridge/bridge_client.py)

当前 bridge 已支持：

- `GET /v1/mira-light/sensors`
- `POST /v1/mira-light/sensors`

这意味着：

```text
director console
-> console proxy
-> bridge
-> mock device
```

已经可以完整读写 `headCapacitive`。

### 4. Director console now includes a mock capacitive switch

相关文件：

- [`../../web/index.html`](../../web/index.html)
- [`../../web/app.js`](../../web/app.js)
- [`../../web/styles.css`](../../web/styles.css)
- [`../../scripts/console_server.py`](../../scripts/console_server.py)

导演台当前已经新增：

- `headCapacitive = 1` 勾选开关
- “发送电容状态”按钮
- “刷新电容状态”按钮
- `TOUCH / IDLE / UNKNOWN` badge
- 头部电容摘要卡

并且这不是前端假状态，而是通过：

- `POST /api/sensors`
- `GET /api/sensors`

真正打到 bridge 和 mock 设备。

### 5. Director console now includes a graphical touch-state widget

相关文件：

- [`../../web/index.html`](../../web/index.html)
- [`../../web/app.js`](../../web/app.js)
- [`../../web/styles.css`](../../web/styles.css)

除了纯文本状态之外，导演台现在还新增了更拟物的触摸状态视觉：

- 灯头示意
- 波纹扩散效果
- `active / idle / unknown` 三态

这样 operator 不需要先读日志或 JSON，单看画面就能判断：

- 头部电容是不是已经触发
- 当前是不是在“接近 / 触摸”状态

### 6. Director console now includes a two-layer 40-pixel visualization

相关文件：

- [`../../web/index.html`](../../web/index.html)
- [`../../web/app.js`](../../web/app.js)
- [`../../web/styles.css`](../../web/styles.css)

当前导演台里的 `pixelSignals` 展示已经分成两层：

#### A. 图形化总览层

提供：

- `40` 灯环状总览
- 活跃灯数量 `active / total`
- 平均亮度
- 当前 LED mode 摘要

这一层的目标不是看单个值，而是让人一眼看出：

- 当前是整体点亮还是局部点亮
- pattern 是不是在对
- 亮度分布是否异常

#### B. 单像素细节层

提供：

- 每颗灯的 index
- 颜色 glow
- 亮度条
- 悬停查看 `[R, G, B, brightness]`

这一层更适合：

- debug 某个像素值
- 检查 brightness 是否被正确带下来
- 看 pattern 在局部是否断裂

### 7. Console server now exposes sensor proxy endpoints

相关文件：

- [`../../scripts/console_server.py`](../../scripts/console_server.py)

网页控制台这层现在已经新增：

- `GET /api/sensors`
- `POST /api/sensors`

因此导演台不需要直接调用 bridge token，也不需要在浏览器里裸暴露 bridge 地址。

### 8. Tests now cover the sensor path

相关文件：

- [`../../tests/test_console_server.py`](../../tests/test_console_server.py)
- [`../../tests/test_mock_device_e2e.py`](../../tests/test_mock_device_e2e.py)
- [`../../tests/test_mock_lamp_server.py`](../../tests/test_mock_lamp_server.py)
- [`../../tests/test_minimal_smoke.py`](../../tests/test_minimal_smoke.py)

目前已覆盖的验证包括：

- `POST /api/sensors`
- `GET /api/sensors`
- `/api/status` 是否带回 `headCapacitive`
- mock device 与 bridge 的 LED / sensor richer payload

## Operational Flow

当前完整链路可以描述为：

```text
operator click
-> web/app.js
-> /api/sensors
-> console_server.py
-> /v1/mira-light/sensors
-> bridge_server.py
-> mock device / mock lamp
-> status + sensors + led readback
-> web graph widgets
```

对应的 `pixelSignals` 可视化则是：

```text
mock device LED state
-> bridge status/led response
-> director console derivePixelSignals(...)
-> pixel ring overview + per-pixel cards
```

## What The Operator Can Now Do

基于当前代码，现场操作员现在已经可以：

- 在导演台直接把 `headCapacitive` 切到 `0` 或 `1`
- 在不接真灯时排练 `touch / affection` 相关链路
- 直接看 `40` 灯当前哪些亮、亮多少、颜色是什么
- 在 `solid` 模式下看推导后的统一 signal
- 在 `vector` 模式下看真实 per-pixel signal

这已经让 mock 面板从“文本调试页”变成了“排练和 review 面板”。

## Verified Local Results

本机已验证：

### 1. Front-end script syntax passes

```bash
node --check web/app.js
```

### 2. Console server sensor proxy path passes

```bash
./.venv/bin/python -m unittest \
  tests.test_console_server \
  tests.test_mock_device_e2e \
  tests.test_mock_lamp_server \
  tests.test_minimal_smoke
```

已观察到的真实链路行为包括：

- `POST /api/sensors` 成功写入 `headCapacitive`
- `GET /api/sensors` 能读回相同状态
- `/api/status` 反映更新后的 `headCapacitive`
- richer LED vector payload 被 mock 正常接受并返回

## Current Boundary

虽然这一层已经很可用了，但还没到最终版。

当前边界主要有这些：

- `headCapacitive` 仍然是手动发送，不是切换即自动提交
- `pixelSignals` 面板目前以可视化为主，还没有“点击单灯 -> 右侧展开原始值”的 drill-down
- 导演台还没有内置 pattern preset 生成器

## Recommended Next Steps

如果继续沿这条线推进，最值得补的是：

1. `headCapacitive` toggle 改为自动提交
2. `pixelSignals` 面板支持只看 active LEDs
3. 支持一键注入 `pulse / chase / rainbow / center-out` 等 mock pattern
4. 增加点击单灯后的原始 signal 详情卡

## Recommended External Framing

> `Mira Light` 现在已经不仅能用 mock 模拟关节动作，还可以在导演台里直接切换头部电容状态，并且图形化查看 40 灯逐像素信号。这使得触摸排练、灯效 review 和 operator 培训都可以在没有真灯的条件下继续推进。
