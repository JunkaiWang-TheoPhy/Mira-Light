# Mira Light Runnable Export: Start Here

## 这是什么

这个目录是一个面向**新电脑直接运行**准备的 Mira Light 发布版导出包。

它保留了当前本地栈运行所需的源码、配置、文档、前端、bridge、场景、素材与测试，
同时去掉了本机运行缓存和虚拟环境。

如果你的目标是：

- 在新电脑上快速启动导演台
- 在没有真机的情况下先跑通完整本地栈
- 再根据需要切到真实灯具

那么就从这份文档开始。

## 前置要求

新电脑至少需要：

- Python `3.10+`
- 本地可用 `curl`

可选：

- `openclaw`
- 本地真实台灯网络可达

## 最短可运行路径

进入导出目录：

```bash
cd mira-light-release-runnable-bundle
```

安装本地环境：

```bash
bash scripts/one_click_install.sh
```

先做一次离线检查：

```bash
bash scripts/run_preflight_release.sh offline
```

如果你是在新电脑上第一次启动，建议先用 **dry-run** 路径，不依赖真机：

```bash
export MIRA_LIGHT_DRY_RUN=1
MIRA_LIGHT_SCENE_BUNDLE=booth_core bash scripts/start_local_stack.sh
```

启动后打开：

```text
http://127.0.0.1:8765/
```

## 推荐的新电脑第一次启动顺序

### 方案 A：最稳妥，先不碰真机

```bash
bash scripts/one_click_install.sh
bash scripts/run_preflight_release.sh offline
export MIRA_LIGHT_DRY_RUN=1
MIRA_LIGHT_SCENE_BUNDLE=booth_core bash scripts/start_local_stack.sh
```

这个方案的好处是：

- 不依赖灯是否在线
- bridge、receiver、console 都能起来
- 场景和导演台可以先确认工作正常

### 方案 B：直接连真实台灯

如果你已经知道灯地址：

```bash
export MIRA_LIGHT_LAMP_BASE_URL=http://172.20.10.3
MIRA_LIGHT_SCENE_BUNDLE=booth_core bash scripts/start_local_stack.sh
```

如果网络不稳，先诊断：

```bash
bash scripts/diagnose_mira_light_network.sh 172.20.10.3
```

必要时：

```bash
bash scripts/fix_mira_light_hotspot_route.sh 172.20.10.3 172.20.10.1
```

## 端口说明

当前本地栈默认端口：

- 导演台 console：`127.0.0.1:8765`
- 本地 bridge：`127.0.0.1:9783`
- simple receiver：`127.0.0.1:9784`

## 常用命令

```bash
# 一键安装
bash scripts/one_click_install.sh

# 离线 preflight
bash scripts/run_preflight_release.sh offline

# 在线 preflight
bash scripts/run_preflight_release.sh online

# 启动完整本地栈
bash scripts/start_local_stack.sh

# 启动主秀 bundle
MIRA_LIGHT_SCENE_BUNDLE=booth_core bash scripts/start_local_stack.sh

# 只启动导演台
bash scripts/start_director_console.sh

# 只启动 bridge
bash tools/mira_light_bridge/start_bridge.sh

# 启动 mock 灯
bash scripts/run_mock_lamp.sh

# 跑 quick offline rehearsal
bash scripts/run_mira_light_offline_rehearsal.sh --mode quick

# HTTP 冒烟检查
bash scripts/smoke_local_stack.sh

# 发布 doctor
bash scripts/doctor_release.sh
```

## 第一次接手建议读哪些文档

建议按这个顺序读：

1. `README.md`
2. `docs/getting-started.md`
3. `docs/release-startup-contract.md`
4. `docs/release-scene-bundles.md`
5. `docs/release-local-stack-runbook.md`
6. `docs/mira-light-pdf2-engineering-handoff.md`
7. `docs/mira-light-scene-implementation-index.md`

## 当前推荐 bundle

如果你的目标是“新电脑上先稳定看到主秀版本”，优先用：

```text
booth_core
```

它会放出：

- `wake_up`
- `curious_observe`
- `touch_affection`
- `track_target`
- `celebrate`
- `farewell`
- `sleep`

## 这个导出包不包含什么

为了保证新电脑复制后仍然干净可启动，这个包不包含：

- `.venv/`
- `.mira-light-runtime/`
- `__pycache__/`
- `*.pyc`

也就是说：

- 运行环境需要在新电脑上重新创建
- 运行日志和缓存会在新电脑首次启动后重新生成

## 一句话总结

这份导出包的核心目标不是“归档阅读”，而是：

> 拷到一台新电脑后，先安装，再启动，再打开 `127.0.0.1:8765`，就能把 Mira Light 的本地栈跑起来。
