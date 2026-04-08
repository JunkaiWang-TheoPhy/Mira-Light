# Mira Light 方案2实现审计记录

## 文档目的

这份文档记录当前仓库针对 [`Mira Light 展位交互方案2.pdf`](/Users/Zhuanz/Documents/Github/Mira-Light/docs/Mira%20Light%20展位交互方案2.pdf) 的实现状态、修复记录和剩余缺口。

如果你需要把当前状态完整交给另一台电脑继续执行，请优先再看：

- [`docs/mira-light-pdf2-engineering-handoff.md`](/Users/Zhuanz/Documents/Github/Mira-Light/docs/mira-light-pdf2-engineering-handoff.md)

## 当前真值来源

当前动作设计、关节理解和场景审核，一律以：

- [`Mira Light 展位交互方案2.pdf`](/Users/Zhuanz/Documents/Github/Mira-Light/docs/Mira%20Light%20展位交互方案2.pdf)

为准。

辅助参考材料：

- [`Mira Light 展位交互方案1.pdf`](/Users/Zhuanz/Documents/Github/Mira-Light/docs/Mira%20Light%20展位交互方案1.pdf)
- [`Mira Light 展位交互方案3.pdf`](/Users/Zhuanz/Documents/Github/Mira-Light/docs/Mira%20Light%20展位交互方案3.pdf)

说明：

- `方案2` 是当前动作真值
- `方案3` 只在局部动作细节上作为补充参考
- `Figs/motions/*.jpg` 只是裁切辅助图，不是动作真值

## 当前机械结论

当前版本严格按 4 个舵机关节实现，不再假设额外的“底部前后摇摆”自由度。

程序层统一使用：

- `servo1`：底座转向
- `servo2`：下臂抬升
- `servo3`：前段关节 / 中间关节抬升与前探
- `servo4`：灯头俯仰 / 微表情

这个结论已同步到：

- [`scripts/scenes.py`](/Users/Zhuanz/Documents/Github/Mira-Light/scripts/scenes.py)
- [`Figs/motions/*/README.md`](/Users/Zhuanz/Documents/Github/Mira-Light/Figs/motions)

## 这轮已经修掉的问题

### 1. 五自由度残留表述

之前部分文档还保留了“第五个自由度 / 五层动作”的说法。

当前已经统一改为：

- 机械解释可以有更细的动作语义
- 程序实现严格按 4 个舵机关节

### 2. 前五个场景缺少关键动作

本轮补上的关键动作包括：

- `wake_up`：高位停顿
- `curious_observe`：摇头后再次更靠近
- `curious_observe`：有点怕时转开并低头，而不是依赖额外后缩自由度
- `touch_affection`：回到自然照明方向
- `touch_affection`：显式 `neutral` 起始姿态

### 3. 第六到第十个场景已进入代码

当前这几个场景已经细化进 [`scripts/scenes.py`](/Users/Zhuanz/Documents/Github/Mira-Light/scripts/scenes.py)：

- `standup_reminder`
- `track_target`
- `celebrate`
- `farewell`
- `sleep`

其中：

- `standup_reminder / celebrate / farewell / sleep` 已经是明确的 choreography
- `track_target` 目前是展位排练用 surrogate choreography，不是真实视觉闭环

### 4. `motions` 目录已扩展到 1~10

当前 `Figs/motions/` 已经覆盖前十个主场景，每个目录里包含：

- 一个 `README.md`
- 一组从 PDF 裁切出的辅助图

说明：

- `README.md` 用来解释当前代码动作
- `jpg` 用来辅助理解 PDF 手绘动作
- 图裁切可能不完美，因此不能反向覆盖 PDF2 真值

## 当前十个主场景实现状态

### 1. `wake_up`

已实现：

- 睡姿进入
- 微光亮起
- 多段提亮
- 半醒起身
- 抬高并后仰
- 高位停顿
- 回正并抖毛
- 看向评委
- 收尾常亮

判断：

- 主动作链条完整

### 2. `curious_observe`

已实现：

- 看向评委
- 靠近
- 缓慢摇头
- 再更靠近一点
- 转开并低头
- 上下轻动灯头
- 再探出来
- 左右轻移
- 面向你点头
- 用户继续靠近时再次转开低头
- 再往回和往前靠

判断：

- 主动作链条完整

### 3. `touch_affection`

已实现：

- 中性起步
- 靠近手
- 身体下送
- 灯头上下左右轻蹭
- 灯光变暖
- 追手
- 回到自然照明方向
- 回中性位

判断：

- 主动作链条完整

### 4. `cute_probe`

已实现：

- 轻点头
- 左右找角度
- 中间关节上提再下放
- 探头
- 缩回
- 再探出去

判断：

- 主动作链条完整

### 5. `daydream`

已实现：

- 走神看远处
- 停住
- 快速回神
- 打瞌睡版逐步下沉
- 快贴桌面时弹回来

判断：

- 主动作链条完整

### 6. `standup_reminder`

已实现：

- 转向评委
- 灯臂前送
- 三次“埋头 -> 顶起 -> 后退”的蹭蹭
- 两次清晰点头
- 被拒绝后的轻摇头
- 慢慢回到原位

判断：

- 主动作链条完整

### 7. `track_target`

已实现：

- 左 -> 中 -> 右 -> 停 -> 再跟 的 surrogate choreography
- 低头看向桌面目标
- 冷静工作光
- 回中性工作位

判断：

- 动作语义已落地
- 真实视觉闭环尚未完成

### 8. `celebrate`

已实现：

- 上摇
- 下摇
- 多色切换
- 中段进入 `rainbow_cycle`
- 音乐触发
- 减速
- 左右摇头
- 身体转一下
- 回暖光收尾

判断：

- 已经从压缩版升级为较完整 choreography

### 9. `farewell`

已实现：

- 先目送
- 两次慢慢点头式挥手
- 最后低头
- 回到中性位并降亮度

判断：

- 固定角度版完整
- 动态离场方向版本未完成

### 10. `sleep`

已实现：

- 先低头
- 灯臂降下去
- 小伸懒腰
- 回到 `sleep_ready`
- 进入 `sleep`
- 渐暗到微光再熄灭

判断：

- 主动作链条完整

## 当前仍然缺失或压缩实现的动作

### `track_target`

当前缺口最大：

- 还没有真实目标检测
- 还没有目标坐标到关节角度的映射
- 还没有持续闭环控制

### `farewell`

当前仍然缺：

- 根据评委离开方向动态目送

### 真机校准缺口

虽然十个主场景都已经进入代码层，但当前角度仍然是设计值，不是实机安全值。

接下来必须通过真机排练确认：

- 不撞结构
- 不拉扯线材
- 动作节奏自然
- 灯光变化在现场可读

## 与旧文档的关系

目前这两份文档仍然保留早期口径：

- [`docs/mira-light-scene-to-code-spec.md`](/Users/Zhuanz/Documents/Github/Mira-Light/docs/mira-light-scene-to-code-spec.md)
- [`docs/mira-light-booth-scene-table.md`](/Users/Zhuanz/Documents/Github/Mira-Light/docs/mira-light-booth-scene-table.md)

它们仍有价值，但用途是：

- 创意理解
- 场景总览
- 原语设计参考

而不是当前动作真值。

## 当前建议的下一步

最值得继续做的是：

1. 真机校准十个主场景
2. 把 `track_target` 从 surrogate choreography 升级成真实视觉闭环
3. 把 `farewell` 升级成动态离场方向跟随
4. 检查导演台与新增动作的同步程度

## 一句话总结

当前十个主场景已经都进入了代码层，其中前九个都已经具备明确的 choreography 结构；最大的剩余工程缺口集中在 `track_target` 的真实感知闭环，以及 `farewell` 的动态离场跟随。
