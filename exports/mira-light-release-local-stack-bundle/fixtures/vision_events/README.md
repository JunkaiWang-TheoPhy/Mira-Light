# Vision Event Fixtures

这个目录存放发布版 `vision_runtime_bridge.py` 的离线输入样例。

这些 fixture 的目标不是替代真实摄像头链路，而是：

- 给测试提供稳定输入
- 给接手同学提供可读的事件样本
- 让 `track_target` / `sleep` 这类闭环逻辑可以先做离线验证

当前包含：

- `01-target-seen-left-mid.json`
- `02-target-updated-right-mid-track-target.json`
- `03-target-lost-after-track.json`
- `04-no-target.json`

推荐的理解顺序：

```text
target_seen
-> target_updated
-> target_lost
-> no_target
```

这组事件正好对应视觉桥当前最关键的三条路径：

- 有人出现时唤醒
- 目标稳定存在时进入 `track_target`
- 目标消失并超过 grace period 后进入 `sleep`
