# Release Live Execution Checklist

## 目的

这份文档是“现在立刻执行”的命令清单版本。

它不解释太多背景，只回答一个问题：

> 如果现在就要开始做最终在线验收，应该按什么顺序执行？

建议直接从上往下照着跑。

## 0. 进入 release 目录

```bash
cd /Users/Zhuanz/Documents/Github/Mira-Light/Mira_Light_Released_Version
```

如果你已经在 release 目录里，可以跳过这一步。

## 1. 设置当前运行参数

### 真机模式

把下面两项替换成真实值：

```bash
export MIRA_LIGHT_LAMP_BASE_URL=http://<真实灯IP>
export MIRA_LIGHT_BRIDGE_TOKEN=<你的真实token>
export MIRA_LIGHT_SCENE_BUNDLE=booth_core
```

### dry-run 排练模式

如果这次先不碰真机：

```bash
export MIRA_LIGHT_DRY_RUN=1
export MIRA_LIGHT_BRIDGE_TOKEN=test-token
export MIRA_LIGHT_SCENE_BUNDLE=booth_core
```

## 2. 先确认真实灯本身可达

真机模式下，先直接打灯本体接口：

```bash
curl "$MIRA_LIGHT_LAMP_BASE_URL/status"
curl "$MIRA_LIGHT_LAMP_BASE_URL/led"
curl "$MIRA_LIGHT_LAMP_BASE_URL/actions"
```

预期：

- 三条都返回 JSON

如果这里失败，先不要继续往下验收。

先跑：

```bash
bash scripts/diagnose_mira_light_network.sh "$MIRA_LIGHT_LAMP_BASE_URL"
```

## 3. 跑离线 preflight

```bash
bash scripts/run_preflight_release.sh offline
```

预期：

- `fail = 0`

如果这里失败，优先修环境，不要继续。

## 4. 启动完整本地栈

```bash
bash scripts/start_local_stack.sh
```

如果你想显式指定参数：

```bash
bash scripts/start_local_stack.sh \
  --lamp-url "$MIRA_LIGHT_LAMP_BASE_URL" \
  --bridge-token "$MIRA_LIGHT_BRIDGE_TOKEN"
```

## 5. 跑在线 preflight

```bash
bash scripts/run_preflight_release.sh online
```

## 6. 跑本地 HTTP smoke

```bash
bash scripts/smoke_local_stack.sh
```

预期至少满足：

- `http://127.0.0.1:8765/` 可打开
- `http://127.0.0.1:9783/health` 返回 `ok=true`
- `http://127.0.0.1:9784/health` 返回 `ok=true`

## 7. 跑最终严格验收

```bash
bash scripts/doctor_release.sh --strict-online
```

如果这一步通过，说明 release 在当前这台机器上的软件链路已经基本完整。

## 8. 打开导演台

浏览器打开：

```text
http://127.0.0.1:8765/
```

确认：

- 当前 bundle 正确
- 当前 base URL 正确
- logs 正在刷新
- scene 列表正常

## 9. 主秀场景真机抽测

至少依次测这几个：

- `wake_up`
- `curious_observe`
- `celebrate`
- `farewell`
- `sleep`

### 如果用 bridge API 逐个触发

```bash
curl -X POST http://127.0.0.1:9783/v1/mira-light/run-scene \
  -H "Authorization: Bearer $MIRA_LIGHT_BRIDGE_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"scene":"wake_up","async":false}'

curl -X POST http://127.0.0.1:9783/v1/mira-light/run-scene \
  -H "Authorization: Bearer $MIRA_LIGHT_BRIDGE_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"scene":"curious_observe","async":false}'

curl -X POST http://127.0.0.1:9783/v1/mira-light/run-scene \
  -H "Authorization: Bearer $MIRA_LIGHT_BRIDGE_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"scene":"celebrate","async":false}'

curl -X POST http://127.0.0.1:9783/v1/mira-light/run-scene \
  -H "Authorization: Bearer $MIRA_LIGHT_BRIDGE_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"scene":"farewell","async":false}'

curl -X POST http://127.0.0.1:9783/v1/mira-light/run-scene \
  -H "Authorization: Bearer $MIRA_LIGHT_BRIDGE_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"scene":"sleep","async":false}'
```

### 抽测时重点看

- 没有连续 `[safety-reject]`
- `celebrate` 的音频和素材已就绪
- `farewell` 能自然收尾
- `sleep` 回落平稳

## 10. 保存验收证据

把下面这些至少留一份：

1. offline preflight 输出
2. online preflight 输出
3. `smoke_local_stack.sh` 输出
4. `doctor_release.sh --strict-online` 输出
5. 导演台首页截图
6. 如有问题，再留 `.mira-light-runtime/local-stack/bridge.log`

## 11. 如果现场不稳，先切保守演示

优先保留：

- `wake_up`
- `curious_observe`
- `celebrate`
- `farewell`
- `sleep`

暂时不要主打：

- `track_target`
- `multi_person_demo`
- `sigh_demo`
- `voice_demo_tired`

## 一句话结论

当前最终在线验收的最短路径就是：

```text
设置参数
-> 确认真机接口
-> offline preflight
-> start_local_stack
-> online preflight
-> smoke
-> strict-online doctor
-> 主秀场景抽测
-> 留证
```
