# Mira Light Mock 排练指南

## 文档目的

这份文档专门解决一个现实问题：

> 还没接上真实灯，但希望导演台、bridge、OpenClaw、scene 编排都先跑通。

这里使用的是仓库里的假设备服务：

- [`mock_lamp_server.py`](/Users/huhulitong/Documents/GitHub/Mira-Light/scripts/mock_lamp_server.py)
- [`run_mock_lamp.sh`](/Users/huhulitong/Documents/GitHub/Mira-Light/scripts/run_mock_lamp.sh)

它不是简单的 `dry-run`，而是一台有状态的本地“假灯”。

## 它和 dry-run 的区别

`dry-run` 的作用是：

- 让 runtime 不真的访问设备
- 适合验证 scene 调度和 bridge 是否工作

`mock lamp` 的作用是：

- 真的提供 HTTP 设备接口
- 真的保存 `servo1` 到 `servo4` 当前角度
- 真的保存 LED 状态和 40 灯信号
- 真的保存 40 个小灯的 `pixelSignals = [R, G, B, brightness]`
- 真的保存头部电容 `headCapacitive = 0 | 1`
- 真的模拟 action 播放和停止

所以：

> `mock lamp` 更接近“没有实体硬件，但软件链路都当成真机来跑”。

## 当前推荐的本地端口

- mock 灯：`http://127.0.0.1:9791`
- 本地 bridge：`http://127.0.0.1:9783`
- 导演台：`http://127.0.0.1:8765`

## 第 1 步：启动 mock 灯

```bash
bash scripts/run_mock_lamp.sh
```

如果你希望显式指定端口：

```bash
bash scripts/run_mock_lamp.sh --host 127.0.0.1 --port 9791 --led-count 40
```

启动后先验证：

```bash
curl http://127.0.0.1:9791/health
curl http://127.0.0.1:9791/status
curl http://127.0.0.1:9791/led
curl http://127.0.0.1:9791/sensors
curl http://127.0.0.1:9791/actions
```

## 第 2 步：让 bridge 指向 mock 灯

如果你的 bridge 已经在运行，最方便的是直接调用配置接口。

```bash
export MIRA_LIGHT_BRIDGE_TOKEN=<你的 bridge token>

curl -X POST http://127.0.0.1:9783/v1/mira-light/config \
  -H "Authorization: Bearer $MIRA_LIGHT_BRIDGE_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"baseUrl":"http://127.0.0.1:9791","dryRun":false}'
```

然后确认 runtime 已经切换：

```bash
curl http://127.0.0.1:8765/api/runtime
```

你应该看到：

- `baseUrl = http://127.0.0.1:9791`
- `dryRun = false`

## 第 3 步：验证上层接口

### 3.1 读取 mock 设备状态

```bash
curl http://127.0.0.1:9783/v1/mira-light/status \
  -H "Authorization: Bearer $MIRA_LIGHT_BRIDGE_TOKEN"
```

如果你想单独看电容 mock：

```bash
curl http://127.0.0.1:9783/v1/mira-light/sensors \
  -H "Authorization: Bearer $MIRA_LIGHT_BRIDGE_TOKEN"
```

### 3.2 直接控制四个关节

```bash
curl -X POST http://127.0.0.1:9783/v1/mira-light/control \
  -H "Authorization: Bearer $MIRA_LIGHT_BRIDGE_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"mode":"absolute","servo1":120,"servo2":95,"servo3":88,"servo4":70}'
```

### 3.3 测试 40 灯 RGBA 信号

下面这个例子会把 40 个小灯写成 `R,G,B,brightness` 四通道信号：

```bash
curl -X POST http://127.0.0.1:9783/v1/mira-light/led \
  -H "Authorization: Bearer $MIRA_LIGHT_BRIDGE_TOKEN" \
  -H "Content-Type: application/json" \
  -d @- <<'JSON'
{
  "mode": "vector",
  "pixels": [
    [255,0,0,180],[255,64,0,180],[255,128,0,180],[255,192,0,180],[255,255,0,180],
    [192,255,0,180],[128,255,0,180],[64,255,0,180],[0,255,0,180],[0,255,64,180],
    [0,255,128,180],[0,255,192,180],[0,255,255,180],[0,192,255,180],[0,128,255,180],
    [0,64,255,180],[0,0,255,180],[64,0,255,180],[128,0,255,180],[192,0,255,180],
    [255,0,255,180],[255,0,192,180],[255,0,128,180],[255,0,64,180],[255,64,64,180],
    [255,96,64,180],[255,128,64,180],[255,160,64,180],[255,192,64,180],[255,224,64,180],
    [224,255,64,180],[192,255,64,180],[160,255,64,180],[128,255,64,180],[96,255,64,180],
    [64,255,64,180],[64,255,96,180],[64,255,128,180],[64,255,160,180],[64,255,192,180]
  ]
}
JSON
```

如果你只想模拟头部电容：

```bash
curl -X POST http://127.0.0.1:9791/sensors \
  -H "Content-Type: application/json" \
  -d '{"headCapacitive":1}'
```

然后读取：

```bash
curl http://127.0.0.1:9791/sensors
curl http://127.0.0.1:9791/status
```

### 3.4 触发一个场景

```bash
curl -X POST http://127.0.0.1:9783/v1/mira-light/run-scene \
  -H "Authorization: Bearer $MIRA_LIGHT_BRIDGE_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"scene":"wake_up","async":false}'
```

跑完后你可以直接对 mock 灯读状态，看看 scene 是否真的改了姿态和灯效：

```bash
curl http://127.0.0.1:9791/status
curl http://127.0.0.1:9791/led
curl http://127.0.0.1:9791/sensors
curl http://127.0.0.1:9791/actions
```

## 第 4 步：在导演台里排练

打开导演台：

```text
http://127.0.0.1:8765
```

重点确认这几件事：

- 顶部 runtime 状态不是 `dry-run`
- `Lamp Base URL` 显示的是 `http://127.0.0.1:9791`
- 点击 `wake_up`、`curious_observe`、`celebrate` 等场景后，日志会更新
- 使用 `Stop -> Neutral` 和 `Stop -> Sleep` 时，mock 状态会跟着变化

## 第 5 步：建议你现在就做的排练内容

### 关节层

- 测试 `absolute` 模式是否符合预期
- 测试 `relative` 模式是否被正确限制
- 验证四个关节在导演台、bridge、mock 三层状态一致

### 灯效层

- 试纯色 `solid`
- 试 `breathing`
- 试 `vector`
- 确认 40 灯必须整条提交，长度错误时能正确报错
- 确认 `pixelSignals` 里每一项都是 `[R, G, B, brightness]`
- 确认 `headCapacitive` 只能是 `0` 或 `1`

### 场景层

- 至少验证 `wake_up`
- 至少验证 `curious_observe`
- 至少验证 `celebrate`
- 至少验证 `farewell`
- 至少验证 `sleep`

## 常见问题

### 为什么我已经有 dry-run 了，还要 mock lamp？

因为 `dry-run` 不会给你一台“会保存状态的设备”。

mock lamp 可以让你继续做这些事：

- 校对 `/status` 返回结构
- 校对 `/led` 返回结构
- 校对 `/sensors` 返回结构
- 验证 40 灯四通道信号接口
- 验证 action 播放与停止
- 验证 scene 执行后设备状态是否真的变化

### 如果以后接回真实灯怎么办？

把 bridge 配置改回真实 IP 即可，例如：

```bash
curl -X POST http://127.0.0.1:9783/v1/mira-light/config \
  -H "Authorization: Bearer $MIRA_LIGHT_BRIDGE_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"baseUrl":"http://<真实灯IP>","dryRun":false}'
```

### 如果只是临时演示，不想连真机也不想起 mock 呢？

那就继续使用：

- `dryRun = true`

但这种模式更适合验证“上层流程没报错”，不适合验证设备状态闭环。
