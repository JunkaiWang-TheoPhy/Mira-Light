# Mira Light Release Local Stack Export

## 说明

这个目录是从：

```text
Mira_Light_Released_Version/
```

整理导出的一个“本地栈参考包”。

它对应的是当前 Mira Light 发布版里，和下面这条运行链路直接相关的文件集合：

```text
browser
-> director console (127.0.0.1:8765)
-> local bridge (127.0.0.1:9783)
-> lamp runtime target
```

同时保留了与这套链路直接相关的：

- 场景编排
- bridge / runtime
- 导演台前端
- receiver / vision
- mock / offline rehearsal
- OpenClaw 插件接入
- 配置模板
- 测试与 runbook

## 导出目的

这个导出包适合下面几类用途：

- 给接手同学做结构化阅读
- 单独归档“本地栈相关文件”
- 做交付包、说明包或审阅包
- 在不带 `.venv` 和运行缓存的前提下查看完整代码结构

## 导出范围

当前导出保留了这些目录：

- `assets/`
- `config/`
- `deploy/`
- `docs/`
- `fixtures/`
- `scripts/`
- `tests/`
- `tools/`
- `web/`

同时保留了这些根文件：

- `README.md`
- `CHANGELOG.md`
- `CONTRIBUTING.md`
- `LICENSE`
- `package.json`
- `requirements.txt`
- `.gitignore`

## 刻意排除的内容

为了保持文件格式和目录边界干净，这个导出包刻意没有带入：

- `.venv/`
- `.mira-light-runtime/`
- `__pycache__/`
- `*.pyc`

也就是说，这个目录是“源码 + 配置 + 文档 + 测试 + 素材”的参考包，而不是一个
带运行时状态的工作目录镜像。

## 当前导出规模

当前导出包包含：

- `24` 个目录
- `216` 个文件

## 关键入口

如果你只想快速把这套本地栈看懂，建议优先看这些文件：

### 启动入口

- `scripts/start_local_stack.sh`
- `scripts/start_director_console.sh`
- `tools/mira_light_bridge/start_bridge.sh`
- `scripts/start_simple_lamp_receiver.sh`

### 运行时核心

- `scripts/mira_light_runtime.py`
- `scripts/scenes.py`
- `scripts/mira_light_safety.py`
- `scripts/booth_controller.py`

### bridge 层

- `tools/mira_light_bridge/bridge_server.py`
- `tools/mira_light_bridge/bridge_client.py`
- `tools/mira_light_bridge/embodied_memory_client.py`
- `tools/mira_light_bridge/README.md`

### 导演台前端

- `web/index.html`
- `web/app.js`
- `web/styles.css`
- `scripts/console_server.py`

### 视觉与 receiver

- `scripts/cam_receiver_service.py`
- `scripts/simple_lamp_receiver.py`
- `scripts/track_target_event_extractor.py`
- `scripts/vision_runtime_bridge.py`

### 文档真值

- `docs/release-startup-contract.md`
- `docs/release-layout.md`
- `docs/getting-started.md`
- `docs/release-scene-bundles.md`
- `docs/mira-light-pdf2-engineering-handoff.md`
- `docs/mira-light-scene-implementation-index.md`

## 建议阅读顺序

建议按这个顺序读：

1. `README.md`
2. `docs/getting-started.md`
3. `docs/release-startup-contract.md`
4. `docs/release-layout.md`
5. `scripts/scenes.py`
6. `scripts/mira_light_runtime.py`
7. `tools/mira_light_bridge/README.md`
8. `web/index.html`
9. `tests/test_release_startup_contract.py`

## 这个导出包不是什么

这个目录不是：

- 一个独立安装好的运行环境
- 一个包含运行日志和缓存的完整现场镜像
- 一个删减到只剩十几个文件的最小包

它更准确的定位是：

> 一个面向阅读、交付、接手和结构化审阅的本地栈源码参考包。

## 来源说明

本导出包来源于仓库根目录下的：

```text
Mira_Light_Released_Version/
```

如果后续上游目录继续迭代，这个导出包不会自动同步，需要手动重新导出。
