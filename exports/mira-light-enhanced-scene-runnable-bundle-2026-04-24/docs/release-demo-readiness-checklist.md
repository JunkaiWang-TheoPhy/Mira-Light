# Release Demo Readiness Checklist

## 目的

这份清单是给演示前最后 `5~10` 分钟使用的。

它不是完整 runbook，而是现场版快速检查：

- 什么必须是绿的
- 什么可以先降级
- 哪些结果需要截图留证

建议在每次正式演示前都完整过一遍。

## T-10 分钟

### 1. 环境变量确认

- `MIRA_LIGHT_LAMP_BASE_URL` 已设置为真实灯地址，或者明确设置了 `MIRA_LIGHT_DRY_RUN=1`
- `MIRA_LIGHT_BRIDGE_TOKEN` 已设置
- `MIRA_LIGHT_SCENE_BUNDLE` 已确认
  - 主秀推荐：`booth_core`
  - 扩展版：`booth_extended`

### 2. 先跑离线检查

```bash
bash scripts/run_preflight_release.sh offline
```

预期：

- `pass > 0`
- `fail = 0`

如果这里失败，不要继续往下演。

## T-5 分钟

### 3. 启动本地栈

```bash
bash scripts/start_local_stack.sh
```

或者主秀模式：

```bash
MIRA_LIGHT_SCENE_BUNDLE=booth_core bash scripts/start_local_stack.sh
```

### 4. 跑在线检查

```bash
bash scripts/run_preflight_release.sh online
bash scripts/smoke_local_stack.sh
```

预期至少满足：

- `http://127.0.0.1:8765/` 可打开
- `http://127.0.0.1:9783/health` 返回 `ok=true`
- `http://127.0.0.1:9784/health` 返回 `ok=true`
- `curl "$MIRA_LIGHT_LAMP_BASE_URL/status"` 返回 JSON

## T-3 分钟

### 5. 主秀场景快速抽测

至少手动试这几个：

- `wake_up`
- `curious_observe`
- `celebrate`
- `farewell`
- `sleep`

检查点：

- 没有连续的 `[safety-reject]`
- `celebrate` 的音频 cue / offer 资产已准备
- `farewell` 能正常收尾
- `sleep` 能平稳回落

## T-2 分钟

### 6. 导演台状态确认

打开：

```text
http://127.0.0.1:8765/
```

确认：

- 当前 bundle 正确
- 当前 base URL 正确
- logs 正在刷新
- profile / pose 数据能显示
- scene 卡片中没有明显不该出现的实验场景

## T-1 分钟

### 7. 现场素材确认

- `assets/audio/dance.wav` 可用
- `assets/offer_demo/index.html` 可打开
- 主持人口播卡已打开或打印
- 网络诊断脚本随时可用：

```bash
bash scripts/diagnose_mira_light_network.sh <灯IP>
```

## 建议留证的 4 个东西

每次正式演示前，建议保存：

1. offline preflight 输出
2. online preflight 输出
3. `smoke_local_stack.sh` 输出
4. 导演台首页截图

如果现场出问题，这 4 份是最快的回溯材料。

## 红线

下面任何一项不满足，都不建议直接进入正式演示：

- bridge `/health` 不通
- receiver `/health` 不通
- 真实灯 `/status` 不通
- 连续出现 `[safety-reject]`
- `wake_up / celebrate / farewell` 任一主秀场景明显异常

## 一句话结论

正式演示前的最小标准就是：

```text
offline preflight 通过
-> local stack 正常
-> online preflight 通过
-> 主秀场景抽测通过
-> 导演台与素材就绪
```
