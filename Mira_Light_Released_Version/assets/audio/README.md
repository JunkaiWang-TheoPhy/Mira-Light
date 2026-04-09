# Release Audio Assets

这个目录存放发布版可直接携带的音频 cue。

当前默认包含：

- `dance.wav`

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
