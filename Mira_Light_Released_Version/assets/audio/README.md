# Release Audio Assets

这个目录存放发布版可直接携带的音频 cue。

当前默认包含：

- `dance.wav`
- `speech/*.aiff`

说明：

- `celebrate` 场景当前仍沿用历史 cue 名 `dance.mp3`
- runtime 新增的 `audio_cue_player.py` 会优先找同名文件
- 如果找不到，也会按同一 stem 自动回退到 `dance.wav`

也就是说：

```text
audio("dance.mp3")
```

当前可以实际解析到：

```text
assets/audio/dance.wav
```

如果后面你拿到了正式版 `dance.mp3`，可以直接替换或并存。

## 预录主持词 / 关键台词

发布版现在还携带了一组预录语音：

- `assets/audio/speech/wake_up_host.aiff`
- `assets/audio/speech/celebrate_host.aiff`
- `assets/audio/speech/farewell_line.aiff`

这组资产的用途是：

- 已知主持词和少量关键台词优先直接播本地音频
- 没有命中预录音资产时，再回退到 `say` / TTS

这样做是为了让发布版在现场更稳，不把“主持词能不能及时播出来”完全压在临场 TTS 上。
