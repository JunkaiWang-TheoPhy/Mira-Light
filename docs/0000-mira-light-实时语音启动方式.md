# 0000 Mira Light 实时语音启动方式

## 说明

这份文档用于集中说明 `Mira Light` 当前实时语音对话链路的启动入口。

这份文档只讲两件事：

1. 现在有哪些推荐启动方式。
2. 启动之后终端会显示什么提示文本。

## 推荐入口一：开放连续对话模式

这个模式适合展位现场持续接待。

这个模式会一直监听。

用户说完后，系统会自动检测静默并结束当前轮。

```bash
scripts/mira-talk-open.sh
```

如果要切男声：

```bash
scripts/mira-talk-open.sh --voice-mode warm_gentleman
```

如果只测对话，不触发动作：

```bash
scripts/mira-talk-open.sh --no-trigger
```

## 推荐入口二：手动开始，自动结束模式

这个模式适合需要更可控、避免误触的场景。

这个模式不是一直开着监听。

每一轮由操作员按一次 `Enter` 开始。

开始后不需要再按第二次 `Enter`。

用户说完后，系统会自动检测静默并结束这一轮。

```bash
scripts/mira-talk-manual.sh
```

如果要切男声：

```bash
scripts/mira-talk-manual.sh --voice-mode warm_gentleman
```

如果只测对话，不触发动作：

```bash
scripts/mira-talk-manual.sh --no-trigger
```

## 底层正式入口

上面两个脚本本质上都是对正式入口的封装。

底层主入口仍然是：

```bash
scripts/run_mira_realtime_voice_interaction.sh
```

它现在支持直接把模式名放在第一个参数位置。

连续模式：

```bash
scripts/run_mira_realtime_voice_interaction.sh continuous
```

手动开始、自动结束模式：

```bash
scripts/run_mira_realtime_voice_interaction.sh enter-vad
```

完整写法也仍然可用：

```bash
scripts/run_mira_realtime_voice_interaction.sh --mode continuous
```

```bash
scripts/run_mira_realtime_voice_interaction.sh --mode enter-vad
```

## 当前默认语音与延迟策略

当前默认 voice mode 是女声。

```bash
--voice-mode gentle_sister
```

当前也已经默认启用低延迟 preset。

```bash
--latency-preset low
```

如果要明确指定，也可以手动写出来：

```bash
scripts/mira-talk-open.sh --voice-mode gentle_sister --latency-preset low
```

## 可以直接复制运行的完整命令

查看麦克风输入设备：

```bash
scripts/run_mira_realtime_voice_interaction.sh --list-inputs
```

查看完整帮助：

```bash
scripts/mira-talk-open.sh --help
```

连续模式，默认女声，默认低延迟：

```bash
scripts/mira-talk-open.sh
```

连续模式，男声，默认低延迟：

```bash
scripts/mira-talk-open.sh --voice-mode warm_gentleman
```

连续模式，默认女声，但不触发动作：

```bash
scripts/mira-talk-open.sh --no-trigger
```

连续模式，默认女声，切回标准延迟策略：

```bash
scripts/mira-talk-open.sh --latency-preset standard
```

连续模式，默认女声，关闭启动预热：

```bash
scripts/mira-talk-open.sh --no-startup-warmup
```

连续模式，指定输入设备名称：

```bash
scripts/mira-talk-open.sh --device "DJI MIC MINI"
```

手动开始、自动结束，默认女声，默认低延迟：

```bash
scripts/mira-talk-manual.sh
```

手动开始、自动结束，男声，默认低延迟：

```bash
scripts/mira-talk-manual.sh --voice-mode warm_gentleman
```

手动开始、自动结束，默认女声，但不触发动作：

```bash
scripts/mira-talk-manual.sh --no-trigger
```

手动开始、自动结束，默认女声，切回标准延迟策略：

```bash
scripts/mira-talk-manual.sh --latency-preset standard
```

底层主入口，连续模式：

```bash
scripts/run_mira_realtime_voice_interaction.sh continuous
```

底层主入口，手动开始、自动结束模式：

```bash
scripts/run_mira_realtime_voice_interaction.sh enter-vad
```

底层主入口，完整写法，连续模式：

```bash
scripts/run_mira_realtime_voice_interaction.sh --mode continuous --voice-mode gentle_sister --latency-preset low
```

底层主入口，完整写法，手动开始、自动结束模式：

```bash
scripts/run_mira_realtime_voice_interaction.sh --mode enter-vad --voice-mode gentle_sister --latency-preset low
```

只回放现有音频文件，不真的外放，不触发动作：

```bash
scripts/run_mira_realtime_voice_interaction.sh \
  --file runtime/realtime-voice-interaction/2026-04-09T13-06-20-940875/turn-001/input.wav \
  --once \
  --dry-run-audio \
  --no-trigger
```

只回放现有音频文件，保留动作关闭，但切男声 dry-run：

```bash
scripts/run_mira_realtime_voice_interaction.sh \
  --file runtime/realtime-voice-interaction/2026-04-09T13-06-20-940875/turn-001/input.wav \
  --once \
  --dry-run-audio \
  --no-trigger \
  --voice-mode warm_gentleman
```

如果需要最小化排查，只看“脚本能不能起”：

```bash
scripts/mira-talk-open.sh --help
scripts/mira-talk-manual.sh --help
```

## 启动后常见终端提示文本

连续模式下，常见启动文本类似下面这样：

```text
Mira realtime voice interaction is ready.
Capture mode: continuous
Input device: DJI MIC MINI
STT profile: small @ 48000 Hz
Latency preset: low
Reply backend: lingzhu (http://127.0.0.1:31879)
Bridge: http://127.0.0.1:9783 (trigger enabled=True)
Continuous mode with VAD start=100ms end=400ms idle-timeout=30s.
```

手动开始、自动结束模式下，常见启动文本类似下面这样：

```text
Mira realtime voice interaction is ready.
Capture mode: enter-vad
Input device: DJI MIC MINI
STT profile: small @ 48000 Hz
Latency preset: low
Reply backend: lingzhu (http://127.0.0.1:31879)
Bridge: http://127.0.0.1:9783 (trigger enabled=True)
Enter-VAD mode with VAD start=100ms end=400ms. Press Enter to start each turn; silence will end it automatically.
```

每一轮开始前，终端通常会显示：

```text
[turn 001] listening...
```

如果这一轮被过滤掉，例如只有一个字、空文本或垃圾转写，终端会显示类似：

```text
[turn 001] skipped: short-low-information-transcript
```

如果识别和回复正常，终端会显示类似：

```text
[turn 001] transcript: 你好。
[turn 001] intent: chat mode=chat
[turn 001] mira: 你好，我在这儿。你今天想聊点什么？
```

## 最常用的现场命令

开放连续接待：

```bash
scripts/mira-talk-open.sh
```

手动一轮一轮接待：

```bash
scripts/mira-talk-manual.sh
```

开放连续接待，但禁用动作：

```bash
scripts/mira-talk-open.sh --no-trigger
```

手动一轮一轮接待，并切男声：

```bash
scripts/mira-talk-manual.sh --voice-mode warm_gentleman
```

现场若只记 4 条命令，建议记下面这组：

```bash
scripts/mira-talk-open.sh
scripts/mira-talk-open.sh --no-trigger
scripts/mira-talk-manual.sh
scripts/mira-talk-manual.sh --voice-mode warm_gentleman
```

## 结论

如果你只想记最简单的两条命令，就记这两个：

```bash
scripts/mira-talk-open.sh
scripts/mira-talk-manual.sh
```

前者是连续对话。

后者是按一次 `Enter` 开一轮，然后自动检测结束。
