# Local Audio and TTS Progress

## Current Status

当前仓库中还记录了一条比较特别但很实用的进展：

这台验证机器已经具备 `OpenClaw` 的本地音频播放与 TTS 输出路径。

这部分能力是 machine-specific 的，不是所有机器默认都有，但它已经被正式记录成文档。

如果你想看“这条能力是否已经被正式封装成 `Mira` 的 speak tool”，请继续看
[15-embodied-speech-and-formal-speak-tool-progress.md](./15-embodied-speech-and-formal-speak-tool-progress.md)。

## What Is Already Available on the Verified Machine

基于 [../openclaw-local-audio-tts.md](../openclaw-local-audio-tts.md)，当前机器已经明确具备：

- 蓝牙音箱播放路径
- 本机系统语音直出
- 本地 TTS 文件生成
- OpenClaw first-party TTS 生成与播放

文档里已经列出了一组可用命令，例如：

- `speaker-hp-status`
- `speaker-hp-use`
- `speaker-hp-release`
- `speaker-hp-play`
- `speaker-hp-say`
- `speaker-hp-tts-play`
- `speaker-hp-tts-file`
- `speaker-hp-openclaw-tts-play`
- `speaker-hp-openclaw-tts-file`

## New Runtime-Level Packaging

这轮之后，机器级 TTS helper 已经进一步收口成实时语音链里的正式 voice mode。

当前默认和新增模式是：

- `gentle_sister`
  - `zh-CN-XiaoyiNeural`
  - `rate -12%`
  - `pitch -20%`
- `warm_gentleman`
  - `zh-CN-YunxiNeural`
  - `rate -6%`
  - `pitch -6%`

实时入口现在可以直接使用：

```bash
scripts/run_mira_realtime_voice_interaction.sh --voice-mode gentle_sister
scripts/run_mira_realtime_voice_interaction.sh --voice-mode warm_gentleman
```

旧别名仍兼容：

- `female` -> `gentle_sister`
- `male` -> `warm_gentleman`

## Why This Matters

这层能力的意义不只是“能出声音”，而是：

- 让本机 OpenClaw 节点具备 spoken feedback 能力
- 让后续 booth、导演台或 agent 工作流可以更自然地接入语音输出
- 让生成语音文件与直接播放都成为可选路径

如果以后 `Mira-Light` 需要更完整的具身表达，这条能力会很有用。

## Current Boundary

这里需要特别说明边界：

- 这是验证机器能力，不是仓库默认普适能力
- 它依赖本机蓝牙设备、macOS 音频输出和既有命令环境
- 它是本地扩展能力，不等于 `Mira-Light` 主链已经有完整音频交互产品闭环

所以更准确的表述是：

仓库现在已经把本机可用的音频/TTS 扩展路径记录下来了，而且已经把其中最常用的 booth 人设音色正式封装成实时 voice mode。

它现在也可以成为 formal speak path 的底座，但那是下一层能力，不是这篇文档的重点。

## Recommended External Framing

> 在验证机器上，`OpenClaw` 已经具备本地音频与 TTS 输出路径，可以通过蓝牙音箱直接播放语音或生成语音文件。
> 这让后续 booth 语音反馈、导演台辅助播报或 agent 语音输出有了现成基础，但它目前仍是机器级扩展能力，而不是整个仓库的默认闭环。
