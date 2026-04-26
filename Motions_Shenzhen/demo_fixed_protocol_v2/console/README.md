# Shenzhen Demo Console

这是 `demo_fixed_protocol_v2` 的本地主控台。

它复用旧版 Mira Light Director Console 的基本形态：

- Python 本地 HTTP server
- 浏览器按钮界面
- 后端代理执行
- 静态前端，无额外前端构建步骤

但它不走旧 release 的 bridge/runtime，而是直接适配当前深圳固定动作脚本。

## 启动

```bash
cd /Users/Zhuanz/Documents/Github/Mira-Light/Motions_Shenzhen/demo_fixed_protocol_v2/console
./start_shenzhen_console.sh
```

打开：

```text
http://127.0.0.1:8777
```

## 执行方式

每个场景有两个按钮：

- `预览命令`：只生成将要发往板端的 shell，不碰真机。
- `执行真机`：把生成的 shell 通过 SSH 发到板端。

默认板端连接：

```text
root@192.168.0.183 -p 22
```

如果没有免密 SSH，有两种方式：

```bash
export MIRA_SHENZHEN_BOARD_PASSWORD='rootroot'
./start_shenzhen_console.sh
```

或者在网页连接区临时输入密码。

## 文件说明

- `scene_registry.json`：场景和救场动作的主控台登记表。
- `console_v2_videos_mapping.md`：`console v2 01-08` 与 `Videos/01-08`、PDF 副本条目和额外动作的对照表。
- `shenzhen_console.py`：本地 HTTP server，负责预览和 SSH 执行。
- `web/`：主控台前端页面。
- `start_shenzhen_console.sh`：启动脚本。

## 安全边界

- 默认不会执行真机，只会预览。
- 真机执行时有超时保护。
- 密码不会写入代码或 registry。
- `torque off` 这类可能导致机械臂下坠的动作没有放进救场按钮。
