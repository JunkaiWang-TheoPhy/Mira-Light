# `track_target` 测试文档

## 场景信息

- 场景名：`track_target`
- 对应脚本：`Motions/07_track_target/scene_script.py`
- 主要目标：验证 Mira 是否能稳定跟住目标，而不是只跑固定 choreography

## 测试目标

本轮主要确认：

1. 当前是 surrogate choreography 还是 live tracking
2. 如果是 live tracking，能否稳定锁住目标
3. 目标停下时能否停住，目标再动时能否继续跟
4. 导演台能否看清当前 target 状态

## 测试前准备

- 导演台在线
- 视觉栈在线
- 如果测桌面书本版本，建议切到 `tabletop_follow`
- 准备一本主测试书和一个次级干扰物

## 测试步骤

1. 将灯复位到 `neutral`
2. 在导演台确认当前 `targetMode`
3. 点击 `追踪 / track_target` 或让视觉桥自然进入 tracking
4. 将目标从左侧缓慢移动到中间
5. 停住 3 到 5 秒
6. 再从中间移动到右侧
7. 在桌面上加入第二个矩形物体，观察是否误切
8. 观察导演台里的 `selected_target`、`selected_reason`、`Bridge Decision`

## 预期结果

- 灯头移动应连续，不应一步一跳
- 目标停下时，灯也应稳定停住
- 同一本目标再次移动时能继续跟
- 干扰物出现时不应频繁切换

## 失败信号

- 目标停下后立刻丢失
- 出现第二个桌面物体就切走
- `wake_up / sleep` 来回抖动
- 导演台看不出当前到底锁了谁

## 失败回退

- `Stop -> Neutral`
- 如果 tracking 状态卡住，切回 `person_follow` 或清空锁定

## 测试记录模板

```text
测试日期：
测试模式：dry-run / 真机
targetMode：person_follow / tabletop_follow
目标类型：人 / 书 / 其他
是否通过：通过 / 不通过 / 部分通过
问题摘要：
1.
2.
3.
导演台观测：
- selected_target:
- selected_reason:
- bridge decision:
建议后续修改：
1.
2.
```
