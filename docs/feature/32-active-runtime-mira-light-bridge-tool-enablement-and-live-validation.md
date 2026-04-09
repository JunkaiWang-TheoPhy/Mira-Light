# Active Runtime Mira Light Bridge Tool Enablement and Live Validation

## Current Status

这次工作的目标，不是继续补一套旁路配置，而是把当前**真正在线服务语音和飞书**的那条 `OpenClaw` 运行链，补成能实际调用 `Mira Light` 工具的状态。

现在已经可以明确下结论：

- active runtime 已经接上 `mira-light-bridge`
- live 语音链已经可以调用 `mira_light_runtime_status`
- live 语音链已经可以调用 `mira_light_run_scene`
- 当前更适合线上使用的调用方式是 `async=true`

但同时也要明确边界：

- 当前 `deviceOnline=false`
- 所以这次已经完成的是“云端 active runtime 工具链打通”
- 还没有完成“真灯硬件在线动作验收”

## What The Active Runtime Actually Is

这次排查确认了一件非常关键的事实：

当前真正在线服务的不是：

- `/home/ubuntu/mira_import/.openclaw/openclaw.json`

也不是：

- `/home/ubuntu/mira_import/mira/.mira-runtime/...`

真正在线服务语音与飞书的，是远端 root 用户的：

- `/root/.openclaw/openclaw.json`

对应 systemd user service 是：

- `openclaw-gateway.service`

也就是说，后续凡是要补“当前 live 入口能不能看到某个 plugin / tool”，优先检查的都应该是 root 侧这套 active config。

## Why The Previous Runtime Path Failed

一开始排查时，`mira-light-bridge` 已经被放到：

- `/home/ubuntu/mira_import/mira/.mira-runtime/mira-openclaw/core/plugins/mira-light-bridge`

但 root 侧 active gateway 启动时会把这条目录当作：

- `suspicious ownership`

原因很简单：

- 这批 runtime plugin 目录是 `uid=1000`
- active gateway 是 root 侧进程
- OpenClaw 会拒绝加载 ownership 不匹配的 plugin candidate

实际报错表现是：

- `plugins.allow: plugin not found: mira-light-bridge`
- `blocked plugin candidate: suspicious ownership`

因此这次没有去硬改原有 runtime 目录 ownership，而是改走 root 自己可信的扩展目录。

## What Was Actually Deployed

这次最终落地的是：

### 1. Root-side trusted plugin path

把 `mira-light-bridge` 部署到：

- `/root/.openclaw/extensions/mira-light-bridge`

这条路径和当前 active gateway 已经在使用的其他插件路径保持一致，更适合线上稳定运行。

### 2. Active config patch

补的是：

- `/root/.openclaw/openclaw.json`

具体包括：

- `plugins.allow` 允许 `mira-light-bridge`
- `plugins.entries["mira-light-bridge"]` 指向远端本地桥地址
- `plugins.load.paths` 包含 `/root/.openclaw/extensions`
- `tools.allow` 放通 `mira_light_*` 系列工具

### 3. Plugin entry target

远端 plugin 指向的是：

- `http://127.0.0.1:19783`

这不是公网桥地址，也不是灯的原始 TCP 地址。

它背后的实际链路是：

```text
remote OpenClaw plugin
-> remote 127.0.0.1:19783
-> SSH reverse tunnel
-> local 127.0.0.1:9783
-> local mira-light-bridge
-> local runtime
-> lamp TCP
```

### 4. Package identity fix

同时还修正了本仓库里 `mira-light-bridge` plugin 的 package name，使它和 manifest id 保持一致，避免：

- `plugin id mismatch`

## What Was Cleaned Up

为了避免 active gateway 每次启动都继续扫描那批会被拒绝的 runtime plugin 目录，这次还从 root active config 里移除了：

- `/home/ubuntu/mira_import/mira/.mira-runtime/mira-openclaw/core/plugins`

移除后的 root-side `plugins.load.paths` 只保留 root 自己可信的路径。

这样做的直接好处是：

- 启动日志更干净
- 不再被旧 runtime ownership 警告污染
- 后续排查时更容易聚焦真正 live 的配置面

## Tools That Are Now Enabled

当前 active runtime 已经放通的 `Mira Light` 工具包括：

- `mira_light_list_scenes`
- `mira_light_runtime_status`
- `mira_light_status`
- `mira_light_run_scene`
- `mira_light_trigger_event`
- `mira_light_apply_pose`
- `mira_light_speak`
- `mira_light_stop_to_neutral`
- `mira_light_stop_to_sleep`
- `mira_light_stop`
- `mira_light_reset`
- `mira_light_set_led`
- `mira_light_control_joints`

当前最推荐 live agent 优先使用的是：

- `mira_light_runtime_status`
- `mira_light_list_scenes`
- `mira_light_run_scene`
- `mira_light_trigger_event`

也就是优先 scene / event 级调用，而不是直接下低层控制。

## What Was Actually Verified

这次不是只改完配置就停了，而是做了几轮 live 验证。

### 1. Live runtime status tool works

通过当前正在使用的 `Lingzhu live adapter` 链路调用：

- `mira_light_runtime_status`

已经不再返回：

- `TOOL_UNAVAILABLE`

而是返回真实 JSON，例如：

```json
{"running":false,"deviceOnline":false,"sceneCount":13,"scene":null}
```

这说明：

- live 语音链已经能真正看到 `mira-light-bridge`

### 2. Scene list tool works

通过 live 链调用：

- `mira_light_list_scenes`

已经能拿到当前 profile 下真实可用的 scene 列表。

这里也顺手确认了一件事：

- `welcome` 不是当前 profile 的 scene id

所以后续不要再把：

- `welcome`

当成正式 `run_scene` 参数。

当前已经确认存在的 scene id 包括：

- `wake_up`
- `curious_observe`
- `touch_affection`
- `cute_probe`
- `daydream`
- `standup_reminder`
- `track_target`
- `celebrate`
- `farewell`
- `sleep`
- `sigh_demo`
- `multi_person_demo`
- `voice_demo_tired`

### 3. Scene write path works

用真实存在的 scene：

- `cute_probe`

做 live 写操作测试时，得到两个重要结论：

#### `async=false`

同步模式下，云端或本地有时会返回：

- `timed out`

但本机 runtime 中仍能看到：

- `lastStartedAt`
- `lastFinishedAt`
- `lastFinishedScene = cute_probe`

也就是说：

- “返回超时”不等于“没有触发”

#### `async=true`

异步模式下，云端 live 链已经返回成功：

```json
{"attempted":true,"scene":"cute_probe","ok":true,"message":"已触发场景运行（异步模式）；执行开始且状态显示 running=true，当前场景为 cute_probe。"}
```

而本机 runtime 也记录到了对应的运行结果：

- `lastStartedAt: 2026-04-09T18:09:17+08:00`
- `lastFinishedAt: 2026-04-09T18:09:21+08:00`
- `lastFinishedScene: cute_probe`

这说明：

- 云端 active runtime
- plugin
- reverse tunnel
- local bridge
- local runtime

这整条写操作链路已经打通。

## Current Boundary

当前还没有通过的，不是工具链，而是硬件在线状态。

本机 bridge runtime 目前显示：

```json
"deviceOnline": false
```

因此现在更准确的说法是：

- 云端已经能实际调到本地 bridge
- 场景执行逻辑已经能被触发
- 但灯本体当前不在线
- 所以还不能把这轮算成“硬件动作验收通过”

## Recommended Runtime Policy

基于这轮验证，当前更推荐的 live policy 是：

### 1. Prefer `async=true`

在云端 agent 调用：

- `mira_light_run_scene`

时，默认优先：

```json
"async": true
```

原因是：

- `async=false` 容易把“已触发但等待超时”误判成失败
- `async=true` 更适合 booth / live control 场景

### 2. Prefer real scene ids, not natural-language aliases

当前不要直接把：

- `welcome`
- `hello`
- `comfort`

这类自然语言词当成 scene id。

更稳的做法是：

- 先做 alias 映射
- 再落到真实 scene id

例如：

- “欢迎一下” -> `wake_up`
- “卖萌” -> `cute_probe`
- “送别” -> `farewell`

### 3. Treat `deviceOnline=false` as a hardware boundary, not a plugin boundary

当 `deviceOnline=false` 时，应理解为：

- 工具层可能仍可调用
- 但硬件动作结果不可作为最终验收

不要把它误判成：

- plugin 没接上
- tunnel 断了
- active runtime 没补成功

## Recommended Next Step

下一步最值得做的是：

1. 先让灯本体上线，让 `deviceOnline=true`
2. 用真实存在且低风险的 scene 再做一次硬件动作验收
3. 在实时语音主链里引入 `cloud-action-mode`
4. 先跑 `shadow mode`
5. 后续再切 `primary`

如果只看这份文档对应的阶段结论，可以用一句话概括：

> 这次已经把“active runtime 工具接入”做完，并且完成了 live 语音链到本地 bridge 的真实读写验证；剩下只差灯本体在线后的最终硬件验收。
