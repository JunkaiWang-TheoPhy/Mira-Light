# Mira Light 发布版补齐清单（2026-04-09）

## 文档目的

这份文档把当前对 `Mira_Light_Released_Version/` 的补齐建议收敛成一份可执行清单。

重点不是再讨论“还有哪些想法”，而是明确：

- 还应该补哪些说明文档
- 还应该加哪些文件夹与素材位
- 还应该补哪些代码
- 还应该补哪些测试

目标是把 `Mira_Light_Released_Version/` 从“已经能启动、能演部分场景的 release 骨架”，进一步推进到“更接近展位交付包”的状态。

## 当前口径

先把真值顺序说清楚：

- [`Mira Light 展位交互方案2.pdf`](./Mira%20Light%20展位交互方案2.pdf) 仍然是动作真值
- [`Mira Light 展位交互方案3.pdf`](./Mira%20Light%20展位交互方案3.pdf) 更适合补局部手绘细节和二期交互方向

当前仓库里已经有一致表述：

- [`mira-light-pdf2-engineering-handoff.md`](./mira-light-pdf2-engineering-handoff.md)
- [`mira-light-pdf2-implementation-audit.md`](./mira-light-pdf2-implementation-audit.md)
- [`mira-light-unfinished-scene-closure-plan.md`](./mira-light-unfinished-scene-closure-plan.md)

所以这份补齐清单不会建议把 `方案3` 重新变成第二套动作真值，也不会建议把 `Figs/` 镜像目录加回来。

更合理的做法是：

- 继续以 `方案2` 驱动主场景动作
- 把 `方案3` 里更偏展位体验的内容，转成 release 可交付的素材、输入桥接、补充场景和运行文档

## 当前缺口先行

从发布版现状看，最明显的缺口集中在 4 件事：

1. 主秀素材还没有收进 release 包
2. `track_target` 还没有做成真实视觉闭环
3. `celebrate` 的音频与 offer 素材还停留在 TODO
4. `sigh_demo / multi_person_demo / voice_demo_tired` 这类补充互动场景已经有骨架，但还没有被包装成 release 功能包

这些结论都能在当前代码里直接看到：

- `track_target` 仍是 surrogate choreography，见 [`../Mira_Light_Released_Version/scripts/scenes.py`](../Mira_Light_Released_Version/scripts/scenes.py)
- `celebrate` 明确写了 `dance.mp3` 和 offer 页面 TODO，见 [`../Mira_Light_Released_Version/scripts/scenes.py`](../Mira_Light_Released_Version/scripts/scenes.py)
- runtime 对 `audio` 仍然是 `[skip-audio]`，见 [`../Mira_Light_Released_Version/scripts/mira_light_runtime.py`](../Mira_Light_Released_Version/scripts/mira_light_runtime.py)
- 默认 minimal mode 只开放少量 `ready` 场景，见 [`../Mira_Light_Released_Version/tests/test_minimal_smoke.py`](../Mira_Light_Released_Version/tests/test_minimal_smoke.py)

## 一、建议新增的说明文档

这一部分对应“要加的 docs”。

### P0

- `Mira_Light_Released_Version/docs/release-scene-bundles.md`
  - 目的：把当前场景按 `minimal / booth_core / booth_extended / sensor_demos` 分成几个发布包
  - 原因：现在 runtime 只有 `ready` 和 `show_experimental` 两档，粒度太粗
  - 应说明：
    - 每个 bundle 包含哪些 scene
    - 哪些 bundle 适合“必演版本”
    - 哪些 bundle 依赖摄像头、麦克风、音频、offer 页面

- `Mira_Light_Released_Version/docs/release-demo-assets-manifest.md`
  - 目的：把 `celebrate`、导演台 showcase、offer 页面、音频素材、主持人手卡素材统一列出来
  - 原因：`celebrate` 已经依赖 `offer 页面` 和 `音频素材`，但 release 里还没有正式资产清单
  - 应说明：
    - 资产路径
    - 文件格式
    - 是否必需
    - 谁负责提供

- `Mira_Light_Released_Version/docs/release-host-cue-sheet.md`
  - 目的：把 [`mira-light-booth-scene-table.md`](./mira-light-booth-scene-table.md) 压缩成现场主持与导演可直接拿来排练的一页手卡
  - 原因：当前场景表很完整，但不够轻量
  - 应说明：
    - 每个主秀场景的主持人口播
    - 触发前提
    - 失败回退

- `Mira_Light_Released_Version/docs/release-scheme2-vs-scheme3.md`
  - 目的：彻底说清 `方案2` 和 `方案3` 在发布版中的角色
  - 原因：否则未来很容易再次出现“双份真相”
  - 应说明：
    - 哪些动作以 `方案2` 为准
    - 哪些局部细节参考 `方案3`
    - 哪些二期互动方向来自 `方案3`

### P1

- `Mira_Light_Released_Version/docs/release-sensor-demos.md`
  - 目的：把 `sigh_demo / multi_person_demo / voice_demo_tired` 作为一个明确的“补充互动场景包”来解释
  - 原因：这几个 scene 已经有元信息和动作骨架，但还没有被包装成正式 release 能力

- `Mira_Light_Released_Version/docs/release-calibration-and-profiles.md`
  - 目的：把 `base_calibrated / sleep_calibrated / profile overrides / rehearsal_range` 讲成一份现场标定说明
  - 原因：现在 profile 信息分散在代码和若干文档中，不适合现场接手

- `Mira_Light_Released_Version/docs/release-vision-closure-plan.md`
  - 目的：专门描述 `track_target` 从 surrogate choreography 升级到真实闭环的路径
  - 原因：这已经是发布版最大的工程缺口

## 二、建议新增的文件夹

这一部分对应“要加的 folders”。

### P0

- `Mira_Light_Released_Version/assets/audio/`
  - 放 `dance.mp3`、备用音频、授权说明、音量建议
  - 作用：补齐 `celebrate` 的真实演示素材

- `Mira_Light_Released_Version/assets/offer_demo/`
  - 放假 offer 邮件页、截图、演示用 HTML
  - 作用：让 `celebrate` 不再只停留在主持人口头说明

- `Mira_Light_Released_Version/assets/host_cards/`
  - 放主持人口播卡、cue sheet 导出稿、展位演示顺序卡
  - 作用：把导演层信息从长文档里分离出来

### P1

- `Mira_Light_Released_Version/fixtures/vision_events/`
  - 放 `track_target`、目标丢失、目标重现、多目标等 JSON/JSONL 样例
  - 作用：给视觉桥接与测试共用

- `Mira_Light_Released_Version/fixtures/audio_events/`
  - 放叹气、疲惫语句、夸奖/批评的 mock 事件样例
  - 作用：给语音和麦克风链路做离线验证

- `Mira_Light_Released_Version/calibration/profiles/`
  - 放 `default`、`booth-a`、`booth-b`、`sleep-calibrated` 等 profile
  - 作用：避免发布版只依赖某一台电脑上的本地 profile

### 不建议加的目录

- 不建议恢复 `Mira_Light_Released_Version/Figs/`
  - 原因：它会重新制造“动作真值”和“辅助镜像”之间的双份真相

## 三、建议新增或补齐的代码

这一部分对应“要加的 code”。

### P0：先把主秀所需的缺口补齐

- `Mira_Light_Released_Version/config/release_scene_bundles.json`
  - 作用：定义 `minimal / booth_core / booth_extended / sensor_demos`
  - 需要改动：
    - [`../Mira_Light_Released_Version/scripts/mira_light_runtime.py`](../Mira_Light_Released_Version/scripts/mira_light_runtime.py)
    - [`../Mira_Light_Released_Version/tools/mira_light_bridge/bridge_server.py`](../Mira_Light_Released_Version/tools/mira_light_bridge/bridge_server.py)
  - 目标：不再只靠 `readiness == ready` 或 `MIRA_LIGHT_SHOW_EXPERIMENTAL=1`

- `Mira_Light_Released_Version/scripts/audio_cue_player.py`
  - 作用：把 `audio("dance.mp3")` 从 TODO 变成真实执行链
  - 需要改动：
    - [`../Mira_Light_Released_Version/scripts/mira_light_runtime.py`](../Mira_Light_Released_Version/scripts/mira_light_runtime.py)
    - [`../Mira_Light_Released_Version/scripts/scenes.py`](../Mira_Light_Released_Version/scripts/scenes.py)
  - 目标：`celebrate` 不再只记录 `[skip-audio]`

- `Mira_Light_Released_Version/web/offer_demo/`
  - 需要文件：
    - `index.html`
    - `app.js`
    - `styles.css`
  - 作用：给 `celebrate` 提供一个可打开、可截图、可联动的假 offer 页面

- `Mira_Light_Released_Version/scripts/run_booth_mvp.sh`
  - 作用：一次拉起 bridge、console、receiver、offer demo、音频素材检查
  - 目标：让“主秀版本”不再只是启动基础服务，而是把主秀所需依赖也一起带起来

### P1：把方案3里的感知互动方向落成代码闭环

- 增强 [`../Mira_Light_Released_Version/scripts/vision_runtime_bridge.py`](../Mira_Light_Released_Version/scripts/vision_runtime_bridge.py)
  - 当前已有“视觉事件 -> scene 选择”雏形
  - 还应该补：
    - 持续 `target_updated` 时的 follow 策略
    - 目标丢失时的 graceful fallback
    - `farewell` 动态离场方向判断

- 新增 `Mira_Light_Released_Version/scripts/farewell_direction_mapper.py`
  - 作用：把离场方向事件映射成 `farewell_look` 或动态角度
  - 目标：补齐 `farewell` 当前“固定方向版”的缺口

- 新增 `Mira_Light_Released_Version/scripts/mic_event_bridge.py`
  - 作用：把麦克风输入转成：
    - `sigh_detected`
    - `speech_emotion_detected=tired`
    - 后续 `praise_detected / criticism_detected`
  - 目标：让 `sigh_demo`、`voice_demo_tired` 不再只是手动触发动画

- 扩展 [`../Mira_Light_Released_Version/scripts/scenes.py`](../Mira_Light_Released_Version/scripts/scenes.py)
- 当前已存在：
  - `sigh_demo`
  - `multi_person_demo`
  - `voice_demo_tired`
- 还建议新增：
  - `praise_feedback`
  - `criticism_feedback`
  - 原因：这两类交互已经在导演稿中出现，但还没有进入代码层

### P2：把 OpenClaw / Director Console 体验也拉齐

- 更新 [`../Mira_Light_Released_Version/tools/mira_light_bridge/openclaw_mira_light_plugin/index.mjs`](../Mira_Light_Released_Version/tools/mira_light_bridge/openclaw_mira_light_plugin/index.mjs)
  - 作用：让 scene bundles、额外场景、safety 元数据对 OpenClaw 更可见

- 更新 [`../Mira_Light_Released_Version/web/app.js`](../Mira_Light_Released_Version/web/app.js)
  - 作用：把以下信息做成更明显的导演态信息：
    - 当前 scene bundle
    - 当前触发来源
    - 最近一次 `safety` clamp / reject
    - 视觉 / 麦克风依赖是否在线

## 四、建议新增的测试

这一部分对应“要加的 tests”。

### P0

- `Mira_Light_Released_Version/tests/test_scene_bundle_profiles.py`
  - 验证不同 bundle 返回的场景列表是否符合预期

- `Mira_Light_Released_Version/tests/test_audio_cue_player.py`
  - 验证：
    - 素材存在时可触发
    - 素材缺失时有明确错误
    - dry-run 时行为可预测

- `Mira_Light_Released_Version/tests/test_offer_demo_assets.py`
  - 验证 offer 页面关键入口文件存在

### P1

- 扩展 [`../Mira_Light_Released_Version/tests/test_vision_runtime_bridge.py`](../Mira_Light_Released_Version/tests/test_vision_runtime_bridge.py)
  - 增加：
    - `target_seen -> wake_up`
    - `target_updated -> track_target`
    - `target_lost -> sleep grace`
    - 动态 `farewell` 方向决策

- 新增 `Mira_Light_Released_Version/tests/test_mic_event_bridge.py`
  - 验证：
    - 叹气事件能映射到 `sigh_demo`
    - 疲惫语义能映射到 `voice_demo_tired`
    - 无法识别时能安全 fallback

- 新增 `Mira_Light_Released_Version/tests/test_additional_scene_demos.py`
  - 验证：
    - `sigh_demo`
    - `multi_person_demo`
    - `voice_demo_tired`
    - `praise_feedback`
    - `criticism_feedback`
  - 至少能在 dry-run 下通过

### P2

- 新增 `Mira_Light_Released_Version/tests/test_release_assets_manifest.py`
  - 验证 `assets/audio`、`assets/offer_demo`、`fixtures/*` 是否和 manifest 对齐

- 新增 `Mira_Light_Released_Version/tests/test_openclaw_scene_bundle_visibility.py`
  - 验证 OpenClaw 插件能正确看到 bundle 和新增场景

## 五、建议按这个顺序落地

### 第一轮：先补主秀交付缺口

1. `release-scene-bundles.md`
2. `release-demo-assets-manifest.md`
3. `assets/audio/`
4. `assets/offer_demo/`
5. `audio_cue_player.py`
6. `release_scene_bundles.json`

目标：

- 让 `celebrate` 真的像一个展位高光场景，而不只是代码里的 TODO
- 让 release 有“最小可演版本”和“完整主秀版本”两套清晰入口

### 第二轮：再补方案3方向的感知互动

1. `release-sensor-demos.md`
2. `fixtures/vision_events/`
3. `fixtures/audio_events/`
4. `farewell_direction_mapper.py`
5. `mic_event_bridge.py`
6. 扩展 `vision_runtime_bridge.py`
7. 扩展 `scenes.py`

目标：

- 把 `track_target`
- `farewell` 动态版
- `sigh_demo`
- `voice_demo_tired`
- `multi_person_demo`

从“导演稿或骨架”推进到“可排练、可测试的 release 能力”。

### 第三轮：最后补 polish 与交付封装

1. `release-host-cue-sheet.md`
2. `release-calibration-and-profiles.md`
3. `run_booth_mvp.sh`
4. Director Console 的 bundle / safety / trigger-source 展示
5. OpenClaw 插件侧的可见性增强

目标：

- 让接手者不只知道代码怎么跑
- 也知道现场怎么演、怎么切、怎么退

## 六、建议完成标准

当下面这些条件都成立时，可以说发布版已经从“骨架”进化到“更像交付包”：

- `celebrate` 已有真实音频素材和 offer 页面素材
- `track_target` 不再只是 surrogate choreography
- `farewell` 支持动态离场方向
- `sigh_demo / voice_demo_tired / multi_person_demo` 至少有 fixture-backed 演练链路
- scene bundles 可以清楚区分“最小可演”和“完整展位版”
- 发布版 docs 可以告诉接手者：
  - 演什么
  - 用什么素材
  - 哪些输入是真的
  - 哪些只是 fallback

## 一句话结论

`Mira_Light_Released_Version/` 现在最该补的不是第二套动作说明图，而是：

> 把 `方案3` 里那些更像展位体验的内容，落成 release 能真正携带的素材目录、补充互动场景、输入桥接代码和配套测试。

也就是说，下一步最值当补的是：

- `docs`
- `assets / fixtures / calibration`
- `scene bundles / audio / vision / mic bridges`
- 对这些新增链路的自动化测试
