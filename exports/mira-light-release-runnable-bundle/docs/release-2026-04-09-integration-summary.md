# Mira Light Release Integration Summary (2026-04-09)

## 目的

这份说明用来把 `2026-04-09` 最近一轮整理后的发布版能力收成一页，方便回答三个最实际的问题：

1. 这次发行版真正保留了什么
2. 为什么这些内容值得进入发布版
3. 现场启动和验收时，应该优先看哪些入口

它不是开发日志，也不是完整 feature 清单。

它只关注已经适合放进 `Mira_Light_Released_Version` 的稳定内容。

## 这次发行版保留的重点

### 1. 现场播报稳定性提升

发布版现在把“主持词”和“少量关键台词”按两层做了稳定化：

- 第一层：优先播放本地预录音资产 `assets/audio/speech/*.aiff`
- 第二层：如果没有对应预录音，再回退到本机 `say`

对应代码：

- [scripts/mira_light_audio.py](/Users/huhulitong/Documents/GitHub/Mira-Light/Mira_Light_Released_Version/scripts/mira_light_audio.py)
- [scripts/mira_light_runtime.py](/Users/huhulitong/Documents/GitHub/Mira-Light/Mira_Light_Released_Version/scripts/mira_light_runtime.py)
- [scripts/scenes.py](/Users/huhulitong/Documents/GitHub/Mira-Light/Mira_Light_Released_Version/scripts/scenes.py)

这带来的实际收益是：

- 展位主持词更稳定
- 不把成败压在临时网络 TTS 上
- 同一场景多次演示时，语气、语速和音色更统一

### 2. mock / bridge / device 的读写口径更统一

发布版现在明确区分了三类信号：

- 四关节运动底层：`9527` raw TCP 舵机帧
- 40 灯状态：`pixels / pixelSignals`
- 头部电容：`headCapacitive`

对应文档：

- [docs/Guide/04-9527总线舵机TCP帧协议与仓库对齐说明.md](/Users/huhulitong/Documents/GitHub/Mira-Light/Mira_Light_Released_Version/docs/Guide/04-9527总线舵机TCP帧协议与仓库对齐说明.md)
- [docs/Guide/09-Mira Light统一信号交付格式说明.md](/Users/huhulitong/Documents/GitHub/Mira-Light/Mira_Light_Released_Version/docs/Guide/09-Mira%20Light统一信号交付格式说明.md)

统一后的推荐理解是：

- `/status`：正式统一状态面，读 `servos + sensors + led`
- `/led`：单独灯效状态
- `/sensors`：单独电容状态
- `/health`：健康检查和快照，不当正式状态面

这个整理对发布版很重要，因为它直接减少了：

- “所有信号是不是都走 9527” 的误解
- mock 排练时接口读错的情况
- bridge / device / 导演台之间的状态理解偏差

### 3. 发布版的离线排练路径更清楚

这次保留下来的不是新花样，而是更明确的排练口径：

- 真实灯接不上时，优先走 mock lamp
- 场景编排先用离线 rehearsal 验节奏
- bridge / runtime / mock device 先在本机闭环

对应文档：

- [docs/mira-light-mock-rehearsal-guide.md](/Users/huhulitong/Documents/GitHub/Mira-Light/Mira_Light_Released_Version/docs/mira-light-mock-rehearsal-guide.md)
- [docs/mira-light-offline-validation-stack.md](/Users/huhulitong/Documents/GitHub/Mira-Light/Mira_Light_Released_Version/docs/mira-light-offline-validation-stack.md)

这意味着发布版更像“一套能排练、能验收、能上展的包”，而不是只留一个 runtime 脚本。

## 这次没有带进发布版的内容

下面这些内容本轮没有作为发布版主能力收进来：

- 导演台视觉排版调整
- 贴纸、烟花、按钮动效等网页表现实验
- 临时网络联调页面逻辑
- 面向单次排练的前端交互钩子

原因不是这些内容没价值，而是它们更适合留在主仓库继续迭代。

对发布版来说，更重要的是：

- 现场能稳
- 信号口径清楚
- mock 和真机切换有明确路径

## 建议的发行版阅读顺序

如果要把当前 release 当成正式交付包使用，建议按这个顺序看：

1. [../README.md](/Users/huhulitong/Documents/GitHub/Mira-Light/Mira_Light_Released_Version/README.md)
2. [getting-started.md](/Users/huhulitong/Documents/GitHub/Mira-Light/Mira_Light_Released_Version/docs/getting-started.md)
3. [release-preflight-runbook.md](/Users/huhulitong/Documents/GitHub/Mira-Light/Mira_Light_Released_Version/docs/release-preflight-runbook.md)
4. [release-startup-contract.md](/Users/huhulitong/Documents/GitHub/Mira-Light/Mira_Light_Released_Version/docs/release-startup-contract.md)
5. [mira-light-mock-rehearsal-guide.md](/Users/huhulitong/Documents/GitHub/Mira-Light/Mira_Light_Released_Version/docs/mira-light-mock-rehearsal-guide.md)
6. [Guide/09-Mira Light统一信号交付格式说明.md](/Users/huhulitong/Documents/GitHub/Mira-Light/Mira_Light_Released_Version/docs/Guide/09-Mira%20Light统一信号交付格式说明.md)

## 最小验收建议

如果你只想快速确认这次整理后的发行版是否“够发布”，至少做这 4 件事：

1. 启动 `offline preflight`
2. 跑一次 `mock lamp + bridge + runtime` 闭环
3. 确认 `celebrate` / `farewell` 等关键台词能走本地音频或 `say`
4. 明确现场要用真机还是 mock，不混淆 `/status` 和 `/health`

## 一句话结论

这次发行版整理的核心不是“加了更多东西”，而是把最影响现场成功率的三件事收稳了：

- 语音播报更稳
- 信号口径更清楚
- mock 到真机的切换更可控
