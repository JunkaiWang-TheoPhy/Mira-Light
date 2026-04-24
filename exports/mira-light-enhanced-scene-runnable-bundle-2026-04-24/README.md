# Mira Light 增强可运行导出包

生成时间：`2026-04-24`

这个目录以 `mira-light-release-runnable-bundle` 为可运行底座，再补上：

- 主仓十个主场景的源码镜像
- 主仓导演台 / bridge / vision 相关源码镜像
- `Motions/` 每场景 motion script
- 一个可选的增强版导演台启动脚本
- 多份新的中文解读文档
- 十个主场景 -> 对应代码文件 -> 动态/静态 -> 触发方式 的对照表

目标是同时满足两件事：

1. 新电脑上能直接按 release 路径启动
2. 接手同学能直接看到主仓当前的场景源码组织方式

## 这个包和原始 release 包的关系

- `README.release-base.md`
  保留了原始 runnable bundle 的说明
- 当前 `README.md`
  是这个增强包的新入口
- 运行层默认仍沿用 release 版的稳定脚本
- `main_repo_source_copy/`
  是主仓当前源码镜像层，主要给阅读、对照、继续开发用

## 目录结构

- `scripts/`
  可直接运行的 release 脚本
- `web/`
  release 导演台和 showcase 页面
- `tools/mira_light_bridge/`
  release bridge
- `Motions/`
  从主仓复制进来的 per-scene motion scripts
- `main_repo_source_copy/`
  主仓源码镜像，包括 `scripts/`、`web/`、`Motions/`、部分 `docs/`
- `docs_export/`
  本次新增的中文解读文档
- `scene_mapping.csv`
- `scene_mapping.json`

## 新电脑快速启动

### 1. 安装依赖

```bash
bash scripts/one_click_install.sh
```

或：

```bash
npm run bootstrap
```

### 2. 启动完整本地栈

```bash
bash scripts/start_local_stack.sh
```

如果只想起主秀 bundle：

```bash
MIRA_LIGHT_SCENE_BUNDLE=booth_core bash scripts/start_local_stack.sh
```

### 3. 打开导演台

浏览器访问：

```text
http://127.0.0.1:8765/
```

### 4. 可选：启动带主仓 motion scripts 的增强版导演台

这个增强包额外提供了：

```bash
bash scripts/start_director_console_with_motion_scripts.sh
```

或者：

```bash
npm run start:console:motions
```

它会启动 `scripts/console_server_with_motion_scripts.py`，方便直接读取根目录 `Motions/` 下的十个 scene launch manifests。

## 十个主场景对照表

| 场景 ID | 中文名 | release 底座代码 | 主仓源码镜像 | 动态/静态 | 主要触发方式 |
| --- | --- | --- | --- | --- | --- |
| `wake_up` | 起床 | `scripts/scenes.py:187` `scripts/scenes.py:574` | `main_repo_source_copy/scripts/scenes.py:187` `main_repo_source_copy/scripts/scenes.py:574` | 静态 choreography | 终端 `booth_controller.py`；导演台 `/api/run/wake_up`；bridge `/v1/mira-light/run-scene`；视觉 `target_seen -> wake_up` |
| `curious_observe` | 好奇你是谁 | `scripts/scenes.py:198` `scripts/scenes.py:623` | `main_repo_source_copy/scripts/scenes.py:198` `main_repo_source_copy/scripts/scenes.py:623` | 动态 builder | `run-scene`；视觉 `scene_hint=curious_observe`；runtime 动态 builder |
| `touch_affection` | 摸一摸 | `scripts/scenes.py:209` `scripts/scenes.py:689` | `main_repo_source_copy/scripts/scenes.py:209` `main_repo_source_copy/scripts/scenes.py:689` | 动态 builder | `run-scene`；`trigger_event(hand_near/touch_detected)`；视觉 hand cue |
| `cute_probe` | 卖萌 | `scripts/scenes.py:231` `scripts/scenes.py:757` | `main_repo_source_copy/scripts/scenes.py:231` `main_repo_source_copy/scripts/scenes.py:757` | 静态 choreography | `run-scene` |
| `daydream` | 发呆 | `scripts/scenes.py:242` `scripts/scenes.py:799` | `main_repo_source_copy/scripts/scenes.py:242` `main_repo_source_copy/scripts/scenes.py:799` | 静态 choreography | `run-scene` |
| `standup_reminder` | 久坐检测：蹭蹭 | `scripts/scenes.py:253` `scripts/scenes.py:837` | `main_repo_source_copy/scripts/scenes.py:253` `main_repo_source_copy/scripts/scenes.py:837` | 静态 choreography | `run-scene` |
| `track_target` | 追踪 | `scripts/scenes.py:264` `scripts/scenes.py:900` + `scripts/mira_light_runtime.py:1602` | `main_repo_source_copy/scripts/scenes.py:264` `main_repo_source_copy/scripts/scenes.py:900` + `main_repo_source_copy/scripts/mira_light_runtime.py:1602` | 混合：静态 fallback + 实时 tracking | fallback `run-scene`；主路径 `vision_runtime_bridge -> apply_tracking_event(...)` |
| `celebrate` | 跳舞模式 | `scripts/scenes.py:275` `scripts/scenes.py:935` | `main_repo_source_copy/scripts/scenes.py:275` `main_repo_source_copy/scripts/scenes.py:935` | 静态 choreography | `run-scene` |
| `farewell` | 挥手送别 | `scripts/scenes.py:286` `scripts/scenes.py:1007` + `scripts/mira_light_runtime.py:1369` | `main_repo_source_copy/scripts/scenes.py:286` `main_repo_source_copy/scripts/scenes.py:1007` + `main_repo_source_copy/scripts/mira_light_runtime.py:1369` | 动态 builder | `run-scene`；`trigger_event(farewell_detected)`；视觉 `target_lost -> farewell` |
| `sleep` | 睡觉 | `scripts/scenes.py:297` `scripts/scenes.py:1045` | `main_repo_source_copy/scripts/scenes.py:297` `main_repo_source_copy/scripts/scenes.py:1045` | 静态 choreography | `run-scene`；视觉丢目标超时后进入 `sleep` |

## 关键入口

- 终端运行入口：`scripts/booth_controller.py`
- runtime 启动 scene：`scripts/mira_light_runtime.py`
- runtime 事件触发：`scripts/mira_light_runtime.py`
- runtime 实时 tracking：`scripts/mira_light_runtime.py`
- 导演台：`scripts/console_server.py`
- 可选增强版导演台：`scripts/console_server_with_motion_scripts.py`
- bridge API：`tools/mira_light_bridge/bridge_server.py`
- motion script 索引：`Motions/README.md`

## 推荐阅读顺序

1. [docs_export/01-增强包总览与新电脑启动.md](./docs_export/01-%E5%A2%9E%E5%BC%BA%E5%8C%85%E6%80%BB%E8%A7%88%E4%B8%8E%E6%96%B0%E7%94%B5%E8%84%91%E5%90%AF%E5%8A%A8.md)
2. [docs_export/02-十个主场景代码对照表.md](./docs_export/02-%E5%8D%81%E4%B8%AA%E4%B8%BB%E5%9C%BA%E6%99%AF%E4%BB%A3%E7%A0%81%E5%AF%B9%E7%85%A7%E8%A1%A8.md)
3. [docs_export/03-主控台与运行链路解读.md](./docs_export/03-%E4%B8%BB%E6%8E%A7%E5%8F%B0%E4%B8%8E%E8%BF%90%E8%A1%8C%E9%93%BE%E8%B7%AF%E8%A7%A3%E8%AF%BB.md)
4. [docs_export/04-主仓源码镜像说明.md](./docs_export/04-%E4%B8%BB%E4%BB%93%E6%BA%90%E7%A0%81%E9%95%9C%E5%83%8F%E8%AF%B4%E6%98%8E.md)

## 结构化文件

- [scene_mapping.csv](./scene_mapping.csv)
- [scene_mapping.json](./scene_mapping.json)

