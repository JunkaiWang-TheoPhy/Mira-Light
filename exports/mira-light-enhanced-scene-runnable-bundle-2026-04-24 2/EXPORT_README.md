# Mira Light Runnable Export Bundle

## 导出定位

这个目录是从：

```text
Mira_Light_Released_Version/
```

导出的一个**可在新电脑上直接安装与启动**的发布版运行包。

它不是只供审阅的“结构参考包”，而是更偏向：

- 新电脑交接
- 本地复刻
- 快速带起导演台 / bridge / receiver
- 现场准备前的独立启动副本

## 和源码目录的关系

上游源目录：

```text
Mira_Light_Released_Version/
```

当前导出目录：

```text
exports/mira-light-release-runnable-bundle/
```

它保留了上游目录的大部分相对路径结构，因此：

- 大多数脚本路径不用改
- `scripts/`、`tools/`、`web/`、`config/`、`docs/` 之间的引用仍然成立
- 在新电脑上更容易直接运行

## 本次导出的内容

保留的目录：

- `assets/`
- `config/`
- `deploy/`
- `docs/`
- `fixtures/`
- `scripts/`
- `tests/`
- `tools/`
- `web/`

保留的根文件：

- `README.md`
- `CHANGELOG.md`
- `CONTRIBUTING.md`
- `LICENSE`
- `package.json`
- `requirements.txt`
- `.gitignore`
- `START_HERE.md`
- `EXPORT_README.md`

## 刻意删掉的内容

为保证新电脑复制后不会带入旧机器状态，本次导出删除了：

- `.venv/`
- `.mira-light-runtime/`
- `__pycache__/`
- `*.pyc`

这意味着：

- 导出包在新电脑上需要重新执行安装脚本
- 首次启动时会重新生成本地运行状态

## 为什么这版更适合“新电脑直接运行”

因为它不是简单把当前机器的运行目录整体打包，而是保留了：

- 源码
- 配置
- 文档
- 前端
- 素材
- 测试

同时删除了：

- 当前机器特有的环境
- 当前机器的运行缓存
- Python 编译缓存

这样做可以避免“拷过去以后路径没问题，但状态脏了”的情况。

## 关键入口

### 安装

- `scripts/one_click_install.sh`

### 启动

- `scripts/start_local_stack.sh`
- `scripts/start_director_console.sh`
- `tools/mira_light_bridge/start_bridge.sh`
- `scripts/start_simple_lamp_receiver.sh`

### 运行时核心

- `scripts/mira_light_runtime.py`
- `scripts/scenes.py`
- `scripts/mira_light_safety.py`

### 导演台

- `scripts/console_server.py`
- `web/index.html`
- `web/app.js`
- `web/styles.css`

### bridge

- `tools/mira_light_bridge/bridge_server.py`
- `tools/mira_light_bridge/bridge_client.py`
- `tools/mira_light_bridge/embodied_memory_client.py`

### 文档真值

- `docs/getting-started.md`
- `docs/release-startup-contract.md`
- `docs/release-scene-bundles.md`
- `docs/release-local-stack-runbook.md`
- `docs/mira-light-pdf2-engineering-handoff.md`
- `docs/mira-light-scene-implementation-index.md`

## 推荐使用方式

对于第一次在新电脑运行，建议优先看：

- `START_HERE.md`

那份文档更偏“直接执行”，而不是结构说明。

## 适用场景

这个导出包适合：

- 交给另一台 Mac / Linux 机器继续跑
- 交给协作者本地复刻
- 交付现场机器做彩排准备
- 作为 release 本地栈的独立副本

## 不适用场景

这个导出包不适合：

- 直接当当前机器的运行日志备份
- 指望保留现有 `.venv` 或运行状态
- 替代完整 Git 仓库历史

## 一句话总结

这份导出包是一个：

> 去掉运行缓存、保留运行能力、适合新电脑直接安装启动的 Mira Light 本地栈副本。
