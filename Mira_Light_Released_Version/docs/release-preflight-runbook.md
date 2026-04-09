# Release Preflight Runbook

## 目的

这份文档专门说明 release 目录的 preflight 怎么用。

它回答 3 个问题：

1. 接手发布版时先检查什么
2. 哪些检查不需要真机
3. 哪些检查只有 bridge / receiver / lamp 都在线时才有意义

## 两类 preflight

### Offline

离线 preflight 不依赖真机，也不要求 bridge / receiver 已经启动。

它主要检查：

- 当前 Python 版本
- release `.venv`
- `curl`
- OpenClaw CLI / config / plugin 入口
- bridge token 是否配置
- lamp URL 是否已经准备

命令：

```bash
bash scripts/run_preflight_release.sh offline
```

或者：

```bash
npm run preflight
```

### Online

在线 preflight 只在以下条件满足时才值得跑：

- bridge 已经启动
- receiver 已经启动
- lamp URL 已经确认
- 如果要验证鉴权，bridge token 已经配置

它主要检查：

- bridge `/health`
- receiver `/health`
- lamp `/status`
- bridge 认证后的 `/v1/mira-light/scenes`

命令：

```bash
bash scripts/run_preflight_release.sh online
```

或者：

```bash
npm run preflight:online
```

## doctor 和 preflight 的关系

### `preflight_release.py`

这是最轻量的环境 / 联通检查。

适合：

- 交接前先确认这台电脑能不能接手
- 启动前先确认环境是否齐
- 启动后快速确认 bridge / receiver / lamp 是否都在线

### `doctor_release.sh`

这是更重的 release 校验。

它会在 preflight 之外继续做：

- Python compile check
- release 单元测试
- 可选的 OpenClaw live verification

命令：

```bash
# 只跑离线阶段
bash scripts/doctor_release.sh

# 离线 + 在线，但在线失败默认按 warning 处理
bash scripts/doctor_release.sh --online

# 离线 + 在线，在线失败直接返回非 0
bash scripts/doctor_release.sh --strict-online
```

## 推荐顺序

第一次接手 release 时，建议顺序固定成：

```text
offline preflight
-> 确认灯 IP
-> 启动本地 stack
-> online preflight
-> 打开导演台
```

## 什么时候需要 strict online

下面这些场景适合 `--strict-online`：

- 你要把 release 交给别人
- 你要做真机演示前最后一次检查
- 你想确认 bridge token、bridge、receiver、lamp 全都真的可用

如果只是本地整理文档或还在找灯 IP，就先不要上 strict。
