# Release Failure Playbook

## 目的

这份文档专门给现场使用。

它回答的不是“架构为什么这样”，而是：

> 演示现场如果坏了，先怎么保住场面？

优先级永远是：

1. 保住现场节奏
2. 快速判断是灯、bridge、receiver、还是网络问题
3. 能降级就降级，不要一开始就重启所有东西

## 情况 1：导演台打不开

先检查：

```bash
curl http://127.0.0.1:8765/
```

如果不通：

- 看 `console` 是否还在前台
- 如果是分开启动，重新执行：

```bash
bash scripts/start_director_console.sh
```

如果 bridge 正常但导演台仍异常：

- 先直接用 bridge API 或 OpenClaw 控灯
- 不要现场先大改 UI

## 情况 2：bridge 不通

先检查：

```bash
curl http://127.0.0.1:9783/health
```

如果不通：

- 先看 bridge 日志
- 重新启动：

```bash
bash tools/mira_light_bridge/start_bridge.sh
```

如果现场不能马上恢复：

- 切到 `dry-run` 讲解模式
- 或改成静态网页 + 主持人口播演示

## 情况 3：receiver 不通

先检查：

```bash
curl http://127.0.0.1:9784/health
```

如果不通：

- 重新起 receiver

```bash
bash scripts/start_simple_lamp_receiver.sh
```

影响判断：

- 如果当前不演示图像/文件回传，可以先继续主秀
- receiver 不是所有场景的硬阻塞项

## 情况 4：真实灯不响应

先检查：

```bash
curl "$MIRA_LIGHT_LAMP_BASE_URL/status"
```

如果超时或失败：

1. 跑网络诊断

```bash
bash scripts/diagnose_mira_light_network.sh "$MIRA_LIGHT_LAMP_BASE_URL"
```

2. 确认当前 Wi‑Fi / 热点是否切换
3. 确认灯 IP 是否变化

如果短时间修不好：

- 立刻切到 `MIRA_LIGHT_DRY_RUN=1`
- 保留导演台和场景讲解
- 不要在现场继续赌网络会自己恢复

## 情况 5：动作异常或被 safety 拦截

优先看：

- `bridge.log`
- 响应里的 `safety`

如果是 `[safety-clamp]`

- 可以继续演，但要避免继续手工打更激进的动作

如果是 `[safety-reject]`

- 立即停止重复发送同类控制
- 先切回：
  - `neutral`
  - `sleep`
  - 或 `reset`

对应动作：

```bash
curl -X POST http://127.0.0.1:9783/v1/mira-light/apply-pose \
  -H "Authorization: Bearer $MIRA_LIGHT_BRIDGE_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"pose":"neutral"}'
```

## 情况 6：`track_target` 看起来不稳定

现场优先策略：

- 不要硬讲“它已经完全闭环”
- 切回 surrogate choreography 或普通 `curious_observe`
- 把视觉部分降级成“方向感知演示”

如果 live tracking 抖动明显：

- 降低演示强度，不要继续让目标大幅快速移动
- 先用 `farewell`、`celebrate`、`wake_up` 这类更稳的 scene 保场

## 情况 7：语音触发不稳定

区分两类：

- `voice_demo_tired`
  - 看 transcript 是否识别正确
- `sigh_demo`
  - 看 mic bridge 是否误判或没判到

如果语音链不稳：

- 退回人工点按钮或 OpenClaw 手动触发
- 不要现场把时间花在调麦克风阈值上

## 最稳的降级组合

如果现场环境不稳定，建议直接切这套“保守可演版”：

- `wake_up`
- `curious_observe`
- `celebrate`
- `farewell`
- `sleep`

暂时不主打：

- `track_target`
- `multi_person_demo`
- `sigh_demo`
- `voice_demo_tired`

## 应急顺序

出问题时建议固定按这个顺序：

1. 看导演台是否还活着
2. 看 bridge `/health`
3. 看灯 `/status`
4. 看 `bridge.log`
5. 再决定是重启 bridge、重启 receiver、还是改成 dry-run

## 一句话结论

现场失败时最重要的不是“找出所有根因”，而是：

```text
先把控制链缩回稳定版本
-> 用最稳的 scene 保住演示
-> 再留日志和证据，演后排查
```
