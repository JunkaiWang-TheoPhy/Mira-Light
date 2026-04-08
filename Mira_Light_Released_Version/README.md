# Mira Light Released Version

Mira Light 是一个围绕四关节 ESP32 智能台灯构建的发布版目录。  
这个目录的目标不是继续承载所有原型上下文，而是把当前已经可以交付的运行时、bridge、导演台、场景编排和说明文档整理成一个可独立拆出去的 repo。

它当前包含：

- 四关节台灯的可执行 choreography
- 本地导演台
- 本地 bridge 与 OpenClaw 插件
- 最简 receiver
- 场景说明与交付文档
- 可独立运行的一键安装入口

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

如需跳过 OpenClaw 插件安装：

```bash
MIRA_LIGHT_SKIP_OPENCLAW_INSTALL=1 bash scripts/one_click_install.sh
```

## 常用命令

```bash
# 一键安装
bash scripts/one_click_install.sh

# 检查当前 release 目录是否完整
bash scripts/doctor_release.sh

# 启动导演台
bash scripts/start_director_console.sh

# 启动本地 bridge
bash tools/mira_light_bridge/start_bridge.sh

# 启动最简 receiver
bash scripts/start_simple_lamp_receiver.sh

# 安装 OpenClaw 插件
bash scripts/install_openclaw_plugin.sh

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
├─ Figs/
├─ scripts/
├─ tests/
├─ tools/
└─ web/
```

## 阅读顺序

建议按这个顺序理解当前 release：

1. [docs/README.md](./docs/README.md)
2. [docs/getting-started.md](./docs/getting-started.md)
3. [docs/mira-light-pdf2-engineering-handoff.md](./docs/mira-light-pdf2-engineering-handoff.md)
4. [docs/mira-light-scene-implementation-index.md](./docs/mira-light-scene-implementation-index.md)
5. [scripts/scenes.py](./scripts/scenes.py)

## 当前定位

这个目录已经尽量自包含，但仍然属于“可独立 repo 的发布骨架”，不是最终的稳定产品版。

当前最适合的用途是：

- 交给另一台电脑继续开发
- 作为 OpenClaw / Claw 可读取的一键安装目录
- 作为后续独立拆 repo 的起点
