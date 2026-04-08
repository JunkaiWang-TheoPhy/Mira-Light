# Mira Light 本机 OpenClaw 最终可粘贴配置片段

## 文档目的

这份文档只提供一件东西：

> 可以直接对照 `~/.openclaw/openclaw.json` 修改的插件配置片段。

## 当前建议值

假设本机 bridge 使用：

```text
http://127.0.0.1:9783
```

并且 token 是：

```text
test-token
```

那么插件相关配置建议改成：

```json
"plugins": {
  "allow": [
    "scientify",
    "mira-light-bridge"
  ],
  "load": {
    "paths": [
      "/Users/Zhuanz/Documents/Github/scientify"
    ]
  },
  "entries": {
    "scientify": {
      "enabled": true
    },
    "mira-light-bridge": {
      "enabled": true,
      "config": {
        "bridgeBaseUrl": "http://127.0.0.1:9783",
        "bridgeToken": "test-token",
        "requestTimeoutMs": 5000
      }
    }
  }
}
```

## 更推荐的现状提醒

你本机当前 `openclaw plugins doctor` 会对 `scientify` 报 stale config warning。

这意味着你之后更理想的做法是：

- 要么修正 `scientify` 当前实际 plugin id
- 要么移除这个失效条目

但这不影响 `mira-light-bridge` 先接入。

## 配置后该做什么

1. 启动本地 bridge  
2. 确认 bridge 健康  
3. 重启本机 OpenClaw  
4. 运行：

```bash
openclaw plugins doctor
```

5. 再跑：

```bash
python3 scripts/verify_local_openclaw_mira_light.py
```

