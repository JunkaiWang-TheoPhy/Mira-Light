# Mira Light Released Version

Mira Light 是一个围绕四关节 ESP32 智能台灯构建的独立运行目录。  
这里收纳了可直接演示和交付的运行时、bridge、导演台、场景编排与说明文档，目标是让整套系统能够在一台机器上快速安装、启动和排练。

它当前包含：

- 四关节台灯的可执行 choreography
- 本地导演台
- 图形化 mock 面板，支持 `headCapacitive` 与 `40` 灯 `pixelSignals`
- 本地 bridge 与 OpenClaw 插件
- 最简 receiver
- mock 排练、离线 rehearsal 与 live-follow demo 入口
- 控制安全层与 OpenClaw 回滚闭环
- scene bundle 与本地演示素材
- 场景说明与交付文档
- 可独立运行的一键安装入口

## 本次发行重点

这版发布目录已经把最近一轮真正适合“交付”的内容收稳了，重点是：

- 现场主持词与关键台词优先走本地预录音资产，没命中时再回退到本机 `say`
- mock / bridge / device 的状态与信号口径更统一，`/status`、`/led`、`/sensors`、`/health` 的职责更清楚
- 离线排练、mock 验收和真机切换的路径更完整

如果你想先快速看这次发行版到底整合了什么，建议先读：

- [docs/release-2026-04-09-integration-summary.md](./docs/release-2026-04-09-integration-summary.md)
- [docs/Guide/06-2026-04-09最近6小时高价值更新.md](./docs/Guide/06-2026-04-09最近6小时高价值更新.md)
- [docs/Guide/09-Mira Light统一信号交付格式说明.md](./docs/Guide/09-Mira%20Light统一信号交付格式说明.md)

当前默认前提：

- Python `3.10+`
- 本地可用 `curl`

## 当前启动契约

发布版当前统一采用这一条控制链：

```text
浏览器
-> 导演台 console (127.0.0.1:8765)
-> 本地 bridge (127.0.0.1:9783)
-> 真实台灯 / dry-run runtime
```

同时保留一个独立 receiver：

```text
device / camera sender
-> simple receiver (127.0.0.1:9784)
```

这意味着：

- console 只连 bridge，不直接连灯
- 灯的真实地址和 `dry-run` 都属于 bridge runtime 配置
- 第一次启动 release 时，优先使用一键本地栈入口

## 一键安装

最快安装路径：

```bash
cd Mira_Light_Released_Version
bash scripts/one_click_install.sh
```

如果你的环境更习惯 `npm` 脚本，也可以：

```bash
cd Mira_Light_Released_Version
npm run bootstrap
```

默认行为：

1. 创建本地 `.venv/`
2. 安装 `requirements.txt`
3. 如果检测到本机有 `openclaw` 且存在 `~/.openclaw/openclaw.json`，自动尝试安装 `mira-light-bridge` 插件
4. 输出下一步可直接运行的命令

如果后面需要从本机 OpenClaw 干净移除 Mira Light 插件，也已经有对应回滚入口：

```bash
bash scripts/remove_openclaw_plugin.sh
```

如需跳过 OpenClaw 插件安装：

```bash
MIRA_LIGHT_SKIP_OPENCLAW_INSTALL=1 bash scripts/one_click_install.sh
```

## 最快启动

推荐第一次按这个顺序走：

### 1. 先跑离线 preflight

```bash
cd Mira_Light_Released_Version
bash scripts/run_preflight_release.sh offline
```

或者：

```bash
npm run preflight
```

### 2. 确认灯 IP

如果你已经知道灯地址，直接设置：

```bash
export MIRA_LIGHT_LAMP_BASE_URL=http://172.20.10.3
```

如果网络不稳，先跑诊断：

```bash
bash scripts/diagnose_mira_light_network.sh 172.20.10.3
```

必要时再用热点路由修复脚本：

```bash
bash scripts/fix_mira_light_hotspot_route.sh 172.20.10.3 172.20.10.1
```

如果你只是想先做不碰真机的演练：

```bash
export MIRA_LIGHT_DRY_RUN=1
```

### 3. 启动完整本地栈

```bash
bash scripts/start_local_stack.sh
```

如果你想直接起主秀版本：

```bash
MIRA_LIGHT_SCENE_BUNDLE=booth_core bash scripts/start_local_stack.sh
```

### 4. 跑在线 preflight 或 HTTP 冒烟检查

bridge / receiver / lamp 都准备好以后，可以继续：

```bash
bash scripts/run_preflight_release.sh online
```

或者：

```bash
npm run preflight:online
```

再补一个 HTTP 冒烟检查确认本地三个端口都通了：

```bash
bash scripts/smoke_local_stack.sh
```

如果你准备接真实控制，建议顺手看一眼：

- [docs/release-scene-bundles.md](./docs/release-scene-bundles.md)
- [docs/release-control-safety-and-openclaw-rollback.md](./docs/release-control-safety-and-openclaw-rollback.md)

因为当前 bridge / runtime 已经会对 `pose`、绝对控制和相对 `nudge` 做 clamp 或 reject。
同时 `MIRA_LIGHT_SCENE_BUNDLE` 已经可以切换 `minimal / booth_core / booth_extended / sensor_demos`。

### 5. 打开导演台

浏览器打开：

```text
http://127.0.0.1:8765/
```

### 6. 如果先做 mock / 视觉排练

```bash
# 启动 mock 灯
bash scripts/run_mock_lamp.sh

# 跑 quick offline rehearsal
bash scripts/run_mira_light_offline_rehearsal.sh --mode quick

# 跑真人跟随 demo（mock + dry-run）
bash scripts/run_mira_light_live_follow_demo.sh --mock-device --dry-run
```

相关说明：

- [docs/mira-light-mock-rehearsal-guide.md](./docs/mira-light-mock-rehearsal-guide.md)
- [docs/mira-light-live-follow-demo-runbook.md](./docs/mira-light-live-follow-demo-runbook.md)
- [docs/mira-light-offline-validation-stack.md](./docs/mira-light-offline-validation-stack.md)

## 常用命令

```bash
# 一键安装
bash scripts/one_click_install.sh

# 发布前置检查
bash scripts/run_preflight_release.sh offline

# 在线联通检查
bash scripts/run_preflight_release.sh online

# 启动完整本地栈
bash scripts/start_local_stack.sh

# 启动主秀 bundle
MIRA_LIGHT_SCENE_BUNDLE=booth_core bash scripts/start_local_stack.sh

# 启动导演台
bash scripts/start_director_console.sh

# 启动 mock 灯
bash scripts/run_mock_lamp.sh

# 跑真人跟随 demo（mock / dry-run）
bash scripts/run_mira_light_live_follow_demo.sh --mock-device --dry-run

# 跑 offline rehearsal
bash scripts/run_mira_light_offline_rehearsal.sh --mode quick

# 启动本地 bridge
bash tools/mira_light_bridge/start_bridge.sh

# 启动最简 receiver
bash scripts/start_simple_lamp_receiver.sh

# HTTP 冒烟检查
bash scripts/smoke_local_stack.sh

# 离线 doctor
bash scripts/doctor_release.sh

# 在线 doctor
bash scripts/doctor_release.sh --online

# 检查当前 release 目录是否完整
bash scripts/doctor_release.sh --strict-online

# 网络诊断
bash scripts/diagnose_mira_light_network.sh 172.20.10.3

# 热点路由修复
bash scripts/fix_mira_light_hotspot_route.sh 172.20.10.3 172.20.10.1

# 安装 OpenClaw 插件
bash scripts/install_openclaw_plugin.sh

# 检查本地音频 cue 解析
python3 scripts/audio_cue_player.py dance.mp3 --dry-run

# 移除 OpenClaw 插件
bash scripts/remove_openclaw_plugin.sh

# 或者走 npm 回滚入口
npm run remove:openclaw

# 校验 OpenClaw + Mira Light 接入
python3 scripts/verify_local_openclaw_mira_light.py
```

## 当前目录结构

```text
Mira_Light_Released_Version/
├─ README.md
├─ LICENSE
├─ package.json
├─ requirements.txt
├─ config/
├─ deploy/
├─ docs/
├─ scripts/
├─ tests/
├─ tools/
└─ web/
```

## 阅读顺序

建议按这个顺序理解当前 release：

1. [docs/README.md](./docs/README.md)
2. [docs/getting-started.md](./docs/getting-started.md)
3. [docs/release-preflight-runbook.md](./docs/release-preflight-runbook.md)
4. [docs/release-startup-contract.md](./docs/release-startup-contract.md)
5. [docs/release-scene-bundles.md](./docs/release-scene-bundles.md)
6. [docs/release-control-safety-and-openclaw-rollback.md](./docs/release-control-safety-and-openclaw-rollback.md)
7. [docs/release-local-stack-runbook.md](./docs/release-local-stack-runbook.md)
8. [docs/mira-light-mock-rehearsal-guide.md](./docs/mira-light-mock-rehearsal-guide.md)
9. [docs/mira-light-live-follow-demo-runbook.md](./docs/mira-light-live-follow-demo-runbook.md)
10. [docs/mira-light-offline-validation-stack.md](./docs/mira-light-offline-validation-stack.md)
8. [docs/release-demo-readiness-checklist.md](./docs/release-demo-readiness-checklist.md)
9. [docs/release-failure-playbook.md](./docs/release-failure-playbook.md)
8. [docs/release-network-diagnostics.md](./docs/release-network-diagnostics.md)
9. [docs/release-environment-reference.md](./docs/release-environment-reference.md)
10. [docs/mira-light-pdf2-engineering-handoff.md](./docs/mira-light-pdf2-engineering-handoff.md)
11. [docs/mira-light-scene-implementation-index.md](./docs/mira-light-scene-implementation-index.md)
12. [scripts/scenes.py](./scripts/scenes.py)

## 当前定位

这个目录已经具备独立运行和演示能力，适合作为 Mira Light 的稳定交付入口。

当前最适合的用途是：

- 作为展位演示与现场联调入口
- 作为 OpenClaw / Claw 可读取的一键安装目录
- 作为团队内部继续开发和排练的统一运行目录

补充说明：

- release 目录已经刻意移除了 `Figs/`
- 主秀素材当前统一放在 `assets/audio/` 和 `assets/offer_demo/`
- raw control 不再直接裸发，当前 bridge / runtime 已经共享安全层
- 场景真值与实现说明统一以 `docs/`、`scripts/scenes.py` 和源 PDF 为准
