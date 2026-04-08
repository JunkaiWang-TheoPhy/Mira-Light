# Mira Light 展位导演台说明

## 文档目的

这份文档说明当前网页控制台为什么要从“工程操作面板”升级成“展位导演台”，以及这一版已经覆盖了什么、还缺什么。

相关实现文件：

- [`web/index.html`](/Users/Zhuanz/Documents/Github/Mira-Light/web/index.html)
- [`web/app.js`](/Users/Zhuanz/Documents/Github/Mira-Light/web/app.js)
- [`web/styles.css`](/Users/Zhuanz/Documents/Github/Mira-Light/web/styles.css)
- [`scripts/mira_light_runtime.py`](/Users/Zhuanz/Documents/Github/Mira-Light/scripts/mira_light_runtime.py)
- [`scripts/console_server.py`](/Users/Zhuanz/Documents/Github/Mira-Light/scripts/console_server.py)

## 为什么不只是“把按钮做大一点”

普通控制台通常只解决：

- 点一个按钮
- 发一个命令
- 看一下日志

但展位现场真正需要的是：

- 一眼看懂现在灯在干什么
- 一眼知道下一幕适不适合触发
- 一眼知道主持人该说什么
- 一眼知道出了问题怎么收场

所以导演台必须是：

```text
状态总控 + cue 选择器 + 导演摘要 + operator 快捷动作 + 调试信息
```

## 当前导演台的目标结构

### 1. 顶部大状态区

顶部应该首先回答下面这些问题：

- 现在系统是 `idle` 还是 `running`
- 当前 scene 是什么
- 当前 step 是什么
- 设备在线还是离线
- 最近错误是什么
- 当前连接目标的 base URL 是什么

对应实现：

- [`web/index.html`](/Users/Zhuanz/Documents/Github/Mira-Light/web/index.html) 中的 `status-strip`
- [`web/app.js`](/Users/Zhuanz/Documents/Github/Mira-Light/web/app.js) 中的 `renderRuntime()`
- [`scripts/mira_light_runtime.py`](/Users/Zhuanz/Documents/Github/Mira-Light/scripts/mira_light_runtime.py) 中的 runtime state

### 2. 中部 Cue Cards

场景区不再只是按钮列表，而是 cue cards。

每张卡片现在承载这些信息：

- 中文标题
- 英文 scene id
- readiness
- 预计时长
- 情绪标签
- 依赖条件
- 一句话口播

这些信息来自：

- [`scripts/scenes.py`](/Users/Zhuanz/Documents/Github/Mira-Light/scripts/scenes.py) 中的 `SCENE_META`

### 3. 右侧导演摘要

右侧摘要区用来给现场操作员一个“当前导演视角”：

- 当前场景
- 当前步骤
- 主持人口播建议
- 本场景依赖条件
- 失败回退建议

这一块的重点不是调试，而是让现场更像“导演操作”。

### 4. Operator Quick Actions

导演台必须内置一些不经过完整场景的快捷动作：

- `Apply Neutral`
- `Apply Sleep`
- `Stop Scene`
- `Stop → Neutral`
- `Stop → Sleep`
- `Reset Lamp`
- 刷新状态
- 刷新灯光
- 刷新动作列表

这部分比普通 reset 更适合现场救场。

### 5. Profile / Pose 可视化

Profile 区域现在不只是原始 JSON。

它被拆成：

- Profile 元信息
- Servo Calibration 摘要
- Pose Library 摘要
- 可展开的原始 JSON

这样更适合现场校准。

### 6. 底部导演日志

日志仍然保留，但定位是：

- 先看摘要
- 再看工程细节

它不是单纯的 debug 输出，而是导演台的“执行记录”。

## 这版已经覆盖了什么

当前这版已经覆盖了导演台最核心的 7 个要素：

- 顶部大状态区
- 中部 cue cards
- 右侧导演摘要
- 底部日志
- scene readiness 标识
- operator 快捷动作
- profile / pose 简明可视化

另外，这一版还新增了两个更偏“展位产品”的部分：

- 场景情绪 accent
- 附件 / 依赖就绪面板

## 新增：场景情绪 Accent

每个场景现在都可以带一个 `accent`，用于驱动页面的情绪光感背景。

例如：

- `dawn`
- `curious`
- `warm`
- `vision`
- `celebrate`
- `farewell`
- `sleep`

它的目的不是替代 scene 本身，而是让控制台在视觉上也有“现在正在进入哪种情绪”的感觉。

## 新增：Priority 与 Readiness

每个 cue card 现在建议同时携带：

- `priority`
- `readiness`

示例：

- `P0`：主秀场景
- `P1`：加分场景
- `P2`：概念 / 原型场景

以及：

- `ready`
- `tuning`
- `sensor-needed`
- `prototype`

这能帮助现场操作员一眼判断：

- 这幕是不是主打
- 这幕是否已经足够稳定
- 这幕是否依赖外部传感器

## 新增：附件 / 依赖就绪面板

导演台新增了一个依赖就绪区，用来标记：

- 基础姿态是否校准
- 手部互动是否就绪
- tracking 是否可用
- 摄像头是否在线
- offer 页面是否准备好
- 音频是否准备好
- 睡姿是否校准
- 麦克风是否可用

这个面板的作用不是自动检测，而是给现场操作员一个快速确认机制。

它解决的问题是：

- 某个 scene 看起来能点，但其实缺附件
- 现场临时换电脑或素材后，没有统一地方确认准备状态

在 cue card 和导演摘要中，未就绪的依赖会被显式高亮。

## 这版还没有完全覆盖的内容

虽然结构已经像导演台了，但仍然有一些能力还没有完全做完。

### 1. 设备在线状态仍然是轻量级推断

当前 `deviceOnline` 主要依赖状态查询结果，而不是更完整的设备心跳系统。

### 2. 当前 step 仍然是“运行时执行步骤”

它已经够用，但还没有细化成导演级语义，例如：

- `进入起床阶段`
- `完成抖毛`
- `等待评委伸手`

### 3. readiness 仍然是手工定义

目前是通过 `SCENE_META` 手动标注：

- `ready`
- `tuning`
- `sensor-needed`
- `prototype`

未来可以改成更动态的状态。

### 4. scene 依赖条件是静态文本

例如：

- 需要 offer 页面
- 需要摄像头
- 需要 tracking

当前还没有自动检测这些依赖是否真的就绪。

### 5. 日志仍然偏工程语言

虽然颜色和结构更适合现场看，但还没有分成：

- 导演日志
- 设备日志
- 低层 HTTP 日志

## 当前最适合怎么用

当前这版最适合：

1. 本地电脑打开导演台
2. 用浏览器点击 cue card 触发场景
3. 观察顶部状态区和右侧导演摘要
4. 用 operator 快捷动作做收场或回正
5. 用 profile 区辅助校准

## 下一步最值得补的内容

如果继续往更像“产品”的方向推进，下一步建议补：

### 1. 设备在线心跳

由设备定期上报状态，而不只是被动查询。

### 2. scene step 更导演化

把当前 step 名称从低层动作名变成更贴近导演理解的 cue。

### 3. cue card 分层

例如：

- `P0`
- `P1`
- `Prototype`

### 4. 依赖就绪检查

例如：

- 摄像头是否在线
- 音乐文件是否存在
- offer 页面是否就绪

### 5. 上传文件预览

如果后续单片机会发图片，这个导演台还可以直接显示最新上传图像。

## 一句话总结

这版网页已经从“工程操作面板”升级成了“展位导演台”的第一版。

它不只是让你点击按钮，而是开始承担：

- 现场状态总控
- cue card 选择
- 主持人辅助
- 应急收场
- pose 校准辅助
