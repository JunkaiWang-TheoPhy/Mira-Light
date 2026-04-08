# Mira Light 本机 OpenClaw 接入验收清单

## 文档目的

这份文档用于回答：

> 本机 OpenClaw 接 Mira Light，什么叫“真的接上了”？

## 最小通过标准

至少满足下面 5 条，才算“本机 OpenClaw 接入完成”。

## 1. 真实灯在线

```bash
curl http://<真实灯IP>/status
curl http://<真实灯IP>/led
curl http://<真实灯IP>/actions
```

预期：

- 3 条都返回 JSON

## 2. 本机 bridge 在线

```bash
export MIRA_LIGHT_BRIDGE_TOKEN=test-token
zsh tools/mira_light_bridge/start_bridge.sh
curl http://127.0.0.1:9783/health
```

预期：

- `health` 返回 `ok=true`

## 3. bridge scene/status API 在线

```bash
curl http://127.0.0.1:9783/v1/mira-light/scenes \
  -H "Authorization: Bearer test-token"

curl http://127.0.0.1:9783/v1/mira-light/status \
  -H "Authorization: Bearer test-token"
```

预期：

- `scenes` 返回场景列表
- `status` 返回当前灯状态

## 4. 本机 OpenClaw 配置已写入

检查：

- `~/.openclaw/extensions/mira-light-bridge/` 存在
- `~/.openclaw/openclaw.json` 中：
  - `plugins.allow` 包含 `mira-light-bridge`
  - `plugins.entries["mira-light-bridge"]` 存在

建议辅助脚本：

```bash
python3 scripts/verify_local_openclaw_mira_light.py
```

## 5. OpenClaw 插件医生检查通过

```bash
openclaw plugins doctor
```

预期：

- 没有 `mira-light-bridge` 相关错误

## 推荐的自动化辅助

### 安装脚本

```bash
python3 scripts/install_local_openclaw_mira_light.py --doctor
```

### 验证脚本

```bash
python3 scripts/verify_local_openclaw_mira_light.py
```

## 一句话结论

只有当：

```text
真实灯可达
-> bridge 可达
-> OpenClaw 配置已写入
-> plugins doctor 通过
```

这四层都成立，才能说“本机 OpenClaw 已接入 Mira Light”。

