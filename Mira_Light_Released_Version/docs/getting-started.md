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

## 安装会做什么

1. 创建 `.venv/`
2. 安装 `requirements.txt`
3. 如果检测到本机有 `openclaw` 且 `~/.openclaw/openclaw.json` 存在，则自动尝试安装 `mira-light-bridge` 插件
4. 输出下一步命令

## 最快启动路径

### 启动导演台

```bash
bash scripts/start_director_console.sh
```

浏览器打开：

```text
http://127.0.0.1:8765/
```

### 启动本地 bridge

```bash
bash tools/mira_light_bridge/start_bridge.sh
```

### 安装 OpenClaw 插件

```bash
bash scripts/install_openclaw_plugin.sh
```

### 校验接入

```bash
bash scripts/doctor_release.sh
```
