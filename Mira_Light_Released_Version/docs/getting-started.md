# Getting Started

## 一键安装

```bash
cd Mira_Light_Released_Version
bash scripts/one_click_install.sh
```

或者：

```bash
npm run bootstrap
```

## 前置条件

- Python `3.10+`
- 本地可用 `curl`

## 安装会做什么

1. 创建 `.venv/`
2. 安装 `requirements.txt`
3. 如果检测到本机有 `openclaw` 且 `~/.openclaw/openclaw.json` 存在，则自动尝试安装 `mira-light-bridge` 插件
4. 输出下一步命令

## 当前启动约定

这一版 release 统一按下面的链路启动：

```text
browser
-> director console
-> local bridge
-> lamp
```

也就是说：

- 导演台本身不直接访问灯
- `MIRA_LIGHT_LAMP_BASE_URL` 和 `MIRA_LIGHT_DRY_RUN` 都属于 bridge runtime
- console 只需要知道 bridge URL

如果你还没看过完整说明，建议继续看：

- [release-preflight-runbook.md](./release-preflight-runbook.md)
- [release-startup-contract.md](./release-startup-contract.md)
- [release-control-safety-and-openclaw-rollback.md](./release-control-safety-and-openclaw-rollback.md)
- [release-environment-reference.md](./release-environment-reference.md)
- [release-local-stack-runbook.md](./release-local-stack-runbook.md)
- [release-network-diagnostics.md](./release-network-diagnostics.md)

## 最快启动路径

### 1. 先跑离线 preflight

```bash
bash scripts/run_preflight_release.sh offline
```

### 2. 确认灯地址或直接使用 dry-run

真机模式：

```bash
export MIRA_LIGHT_LAMP_BASE_URL=http://172.20.10.3
```

如果不确定当前网络是否真的能打到灯，先诊断：

```bash
bash scripts/diagnose_mira_light_network.sh 172.20.10.3
```

如果暂时不碰真机：

```bash
export MIRA_LIGHT_DRY_RUN=1
```

### 3. 启动完整本地栈

```bash
bash scripts/start_local_stack.sh
```

### 4. 跑在线 preflight 或 HTTP 冒烟检查

```bash
bash scripts/run_preflight_release.sh online
```

以及：

```bash
bash scripts/smoke_local_stack.sh
```

如果后续要从导演台、bridge API 或 OpenClaw 发控制命令，建议继续看：

- [release-control-safety-and-openclaw-rollback.md](./release-control-safety-and-openclaw-rollback.md)

因为发布版当前已经会对 `pose`、绝对控制和相对 `nudge` 做 clamp 或 reject。

### 5. 打开导演台

```text
http://127.0.0.1:8765/
```

## 分开启动时的对应命令

### 启动本地 bridge

```bash
bash tools/mira_light_bridge/start_bridge.sh
```

### 启动导演台

```bash
bash scripts/start_director_console.sh
```

### 启动最简 receiver

```bash
bash scripts/start_simple_lamp_receiver.sh
```

### 安装 OpenClaw 插件

```bash
bash scripts/install_openclaw_plugin.sh
```

### 移除 OpenClaw 插件

```bash
bash scripts/remove_openclaw_plugin.sh
```

或者：

```bash
npm run remove:openclaw
```

### 校验接入

```bash
bash scripts/doctor_release.sh
```

如果 bridge / receiver / lamp 都已经在线，也可以：

```bash
bash scripts/doctor_release.sh --online
```
