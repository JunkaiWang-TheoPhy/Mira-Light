# Release Final Hardware Blockers Checklist

## 目的

这份清单只记录：

> 到当前为止，release 剩余还没收尾的部分里，哪些已经明确是“仅硬件阻塞”？

它不再罗列软件侧待开发项，而是把最后的实机与现场工作压缩成一份短清单。

## 使用方式

建议把这份清单当成 release 收尾的最后门槛。

满足下面所有项后，才适合把 release 对外说成：

> 已完成软件交付，并已完成真实设备验收。

## 必须完成

### 1. 确认真实灯地址

- [ ] 已确认真实 `MIRA_LIGHT_LAMP_BASE_URL`
- [ ] 当前电脑与灯在可达路径上
- [ ] `curl "$MIRA_LIGHT_LAMP_BASE_URL/status"` 返回 JSON
- [ ] `curl "$MIRA_LIGHT_LAMP_BASE_URL/led"` 返回 JSON
- [ ] `curl "$MIRA_LIGHT_LAMP_BASE_URL/actions"` 返回 JSON

### 2. 确认真实 bridge 鉴权

- [ ] 已设置真实 `MIRA_LIGHT_BRIDGE_TOKEN`
- [ ] `curl http://127.0.0.1:9783/health` 返回 `ok=true`
- [ ] 认证后的 `/v1/mira-light/scenes` 可访问
- [ ] 认证后的 `/v1/mira-light/status` 可访问

### 3. 确认完整本地栈在线

- [ ] `http://127.0.0.1:8765/` 可打开
- [ ] `http://127.0.0.1:9783/health` 可访问
- [ ] `http://127.0.0.1:9784/health` 可访问
- [ ] `bash scripts/smoke_local_stack.sh` 通过

### 4. 完成主秀场景真机抽测

至少真机抽测下面这些：

- [ ] `wake_up`
- [ ] `curious_observe`
- [ ] `celebrate`
- [ ] `farewell`
- [ ] `sleep`

每个场景都应满足：

- [ ] 没有连续 `[safety-reject]`
- [ ] 动作节奏符合当前导演稿
- [ ] 不出现明显机械碰撞或危险边界

### 5. 完成真实校准

- [ ] 当前灯的实际 profile 已保存
- [ ] `neutral`、`sleep`、`wake_half`、`wake_high` 等关键 pose 已真机确认
- [ ] `sleep` 回落姿态安全
- [ ] `celebrate` 的高姿态与减速收尾安全

### 6. 完成在线验收留证

- [ ] 跑过 `python3 scripts/preflight_release.py online`
- [ ] 跑过 `bash scripts/doctor_release.sh --strict-online`
- [ ] 保存了 offline preflight 输出
- [ ] 保存了 online preflight 输出
- [ ] 保存了 smoke 输出
- [ ] 保存了导演台首页截图

## 可选但建议完成

### 7. 视觉 / 语音额外演示链路

- [ ] `track_target` 在真实摄像头输入下可稳定展示
- [ ] `farewell` 动态离场方向与真实移动方向一致
- [ ] `voice_demo_tired` 在真实麦克风环境下可稳定触发
- [ ] `sigh_demo` 在真实麦克风环境下误判率可接受
- [ ] `multi_person_demo` 在多人场景下不会明显误触发

这部分不是 release 软件交付的硬阻塞，但如果要现场主打这些能力，建议补完。

## 完成后可使用的最终口径

当“必须完成”这一节全部打勾以后，可以用下面这句作为最终交付口径：

> `Mira_Light_Released_Version` 已完成软件交付、已完成本地控制链验收，并已通过真实设备与现场网络条件下的最终验证。

## 一句话结论

当前 release 剩余真正没收尾的部分，已经主要不是代码问题，而是：

```text
真实灯
-> 真实网络
-> 真实校准
-> 在线验收留证
```
