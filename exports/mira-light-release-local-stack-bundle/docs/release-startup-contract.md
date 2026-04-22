# Release Startup Contract

## 目的

这份文档专门说明 release 目录当前的启动拓扑与责任边界。

它回答 3 个问题：

1. 导演台到底连谁
2. bridge 到底连谁
3. 哪些环境变量应该作用在哪一层

## 当前统一链路

发布版当前统一采用：

```text
browser
-> director console (127.0.0.1:8765)
-> local bridge (127.0.0.1:9783)
-> lamp runtime target
```

这里的 lamp runtime target 可以是：

- 真实台灯地址，例如 `http://172.20.10.3`
- dry-run 模式下的虚拟目标

同时保留一个独立 receiver：

```text
device / camera sender
-> simple receiver (127.0.0.1:9784)
```

## 谁负责什么

### Director Console

导演台负责：

- 提供浏览器操作界面
- 代理请求到 bridge
- 展示 runtime、scene、profile、logs

导演台不负责：

- 直接访问灯
- 决定灯的最终 base URL
- 决定 runtime 是否 dry-run

### Bridge

bridge 负责：

- 统一对外 API
- 管理 runtime 状态
- 决定当前 lamp base URL
- 决定当前是否 dry-run
- 对控制请求执行统一安全裁决

### Lamp

灯本身只暴露底层设备接口。

release 当前希望所有上层访问都先经过 bridge，而不是让导演台或外部工具直接打灯。

## 当前控制安全约定

发布版当前不再把 raw control 当成“收到什么就发什么”。

当前运行时与 bridge 已经共享一套控制安全层：

- `pose` 会做范围校验
- 绝对控制会做范围校验
- 相对 `nudge` 会结合当前已知姿态做范围推导

对应结果分两类：

- 还在 `hard_range` 内但超出 `rehearsal_range` 时，会被 clamp
- 超出 `hard_range` 或缺少必要状态时，会被 reject

所以现在更准确的理解是：

```text
console 负责发请求
bridge / runtime 负责决定这次控制是否能安全执行
```

详细规则见：

- [release-control-safety-and-openclaw-rollback.md](./release-control-safety-and-openclaw-rollback.md)

## 命令对应关系

### 启动完整本地栈

```bash
bash scripts/start_local_stack.sh
```

这条命令会：

- 启动 bridge
- 启动 receiver
- 前台启动导演台

### 只启动导演台

```bash
bash scripts/start_director_console.sh
```

这时导演台只会连 bridge，不会替你启动 bridge，也不会直接改灯地址。

### 只启动 bridge

```bash
bash tools/mira_light_bridge/start_bridge.sh
```

这时 `MIRA_LIGHT_LAMP_BASE_URL` 和 `MIRA_LIGHT_DRY_RUN` 会真正影响 runtime。

## 环境变量应该归哪一层

### 归 bridge runtime

- `MIRA_LIGHT_LAMP_BASE_URL`
- `MIRA_LIGHT_DRY_RUN`
- `MIRA_LIGHT_BRIDGE_TOKEN`
- `MIRA_LIGHT_BRIDGE_HOST`
- `MIRA_LIGHT_BRIDGE_PORT`

### 归 director console

- `MIRA_LIGHT_CONSOLE_HOST`
- `MIRA_LIGHT_CONSOLE_PORT`
- `MIRA_LIGHT_CONSOLE_BRIDGE_URL`
- `MIRA_LIGHT_CONSOLE_BRIDGE_TIMEOUT_SECONDS`
- `MIRA_LIGHT_CONSOLE_BRIDGE_TOKEN_ENV`

### 归 receiver

- `MIRA_LIGHT_RECEIVER_HOST`
- `MIRA_LIGHT_RECEIVER_PORT`
- `MIRA_LIGHT_RECEIVER_SAVE_ROOT`

## 为什么 `MIRA_LIGHT_DRY_RUN` 不属于 console

因为 dry-run 的本质是：

> bridge runtime 是否真的把动作发给灯

而不是：

> 浏览器界面是否只显示不执行

所以当前 release 约定是：

- `MIRA_LIGHT_DRY_RUN` 由 bridge 消费
- `scripts/start_local_stack.sh --dry-run` 会把这个选项传给 bridge
- 单独启动 console 时，只会给出提示，不会把它当成 console 自身参数

## 向后兼容

为了避免旧命令立刻失效，console CLI 仍然接受：

```text
--base-url
```

但它现在只被当作 `--bridge-base-url` 的兼容别名，而不再代表灯地址。

## 一句话总结

当前 release 的启动契约可以简化为：

```text
console 连 bridge
bridge 连 lamp
bridge / runtime 共享安全层
dry-run 只属于 bridge runtime
```
