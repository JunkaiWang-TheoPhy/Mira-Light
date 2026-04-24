# Release Local Stack Runbook

## 目的

这份 runbook 面向第一次接手 `Mira_Light_Released_Version/` 的同学。

目标很简单：

- 最少命令启动完整本地栈
- 最快确认三个 HTTP 端口都健康
- 明确遇到问题时先看哪里

## 推荐流程

### 1. 先进入 release 目录

```bash
cd Mira_Light_Released_Version
```

### 2. 先跑离线 preflight

```bash
bash scripts/run_preflight_release.sh offline
```

### 3. 再准备灯地址或 dry-run

真机模式：

```bash
export MIRA_LIGHT_LAMP_BASE_URL=http://172.20.10.3
```

排练模式：

```bash
export MIRA_LIGHT_DRY_RUN=1
```

如果真机模式下不确定当前路由是否正确，建议先执行：

```bash
bash scripts/diagnose_mira_light_network.sh 172.20.10.3
```

### 4. 启动完整本地栈

```bash
bash scripts/start_local_stack.sh
```

也可以一次性带参数：

```bash
bash scripts/start_local_stack.sh --lamp-url http://172.20.10.3
```

或者：

```bash
bash scripts/start_local_stack.sh --dry-run
```

### 5. 跑在线 preflight 和 HTTP 冒烟检查

```bash
bash scripts/run_preflight_release.sh online
```

再继续：

```bash
bash scripts/smoke_local_stack.sh
```

通过后应至少确认：

- `127.0.0.1:8765` 的导演台首页可返回
- `127.0.0.1:9783/health` 的 bridge 可返回
- `127.0.0.1:9784/health` 的 receiver 可返回

如果你准备继续发控制命令，也建议确认：

- bridge 控制接口返回里已经能看到 `safety` 字段
- `bridge.log` 里没有连续的 `[safety-reject]`

### 6. 打开导演台

```text
http://127.0.0.1:8765/
```

## 这条命令实际做了什么

`scripts/start_local_stack.sh` 会：

1. 启动 bridge
2. 等待 bridge `/health`
3. 启动 receiver
4. 等待 receiver `/health`
5. 前台启动导演台

bridge 和 receiver 的后台日志默认写到：

```text
.mira-light-runtime/local-stack/
```

如果动作被 clamp 或 reject，优先看：

- `.mira-light-runtime/local-stack/bridge.log`

当前本地栈是 bridge 进程内嵌 runtime，所以安全相关日志也会出现在 `bridge.log` 里。

当前会显式记录：

- `[safety-clamp]`
- `[safety-reject]`

## 常见参数

### 指定灯地址

```bash
bash scripts/start_local_stack.sh --lamp-url http://192.168.0.123
```

### 强制 dry-run

```bash
bash scripts/start_local_stack.sh --dry-run
```

### 指定 bridge token

```bash
bash scripts/start_local_stack.sh --bridge-token my-token
```

## 如果你想分开启动

### 只起 bridge

```bash
bash tools/mira_light_bridge/start_bridge.sh
```

### 只起 receiver

```bash
bash scripts/start_simple_lamp_receiver.sh
```

### 只起导演台

```bash
bash scripts/start_director_console.sh
```

## 排障顺序

如果导演台打不开或没有状态，建议按下面顺序看：

1. `bash scripts/smoke_local_stack.sh`
2. bridge `/health` 是否正常
3. receiver `/health` 是否正常
4. 导演台日志
5. `.mira-light-runtime/local-stack/bridge.log`
6. `.mira-light-runtime/local-stack/receiver.log`
7. `bridge.log` 里是否出现 `[safety-clamp]` 或 `[safety-reject]`

如果 bridge 正常但灯离线，再去确认：

- `MIRA_LIGHT_LAMP_BASE_URL`
- 当前 Wi-Fi / 网段
- 真实灯的 `/status`

如果 bridge 正常、灯也在线，但动作结果和输入不完全一致，再去确认：

- bridge 返回的 `safety` 元数据
- runtime `estimatedServoState`
- 当前 profile / calibration 是否还是默认值

## 一句话总结

第一次接手 release 时，最推荐的路径就是：

```text
offline preflight
-> 设置灯地址或 dry-run
-> start_local_stack.sh
-> online preflight
-> smoke_local_stack.sh
-> 留意 safety 日志与 bridge `safety` 返回
-> 打开导演台
```
