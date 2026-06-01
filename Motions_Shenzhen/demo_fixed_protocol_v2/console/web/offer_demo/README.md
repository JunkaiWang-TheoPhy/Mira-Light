# Offer Demo Asset

这个目录提供发布版自带的假 offer 演示页。

当前入口：

- [`index.html`](./index.html)

用途：

- 配合 `celebrate` 场景做“收到好消息”的展位剧情
- 给导演台依赖项里的 `offer_ready` 一个真实落点
- 让接手电脑不需要额外找一张截图或临时做网页

最简单的打开方式：

1. 直接用浏览器打开 `index.html`
2. 或者在 release 根目录起一个静态服务：

```bash
python3 -m http.server 8876
```

然后访问：

```text
http://127.0.0.1:8876/assets/offer_demo/index.html
```

如果你想临时改候选人名字，可以用 URL 参数：

```text
...?candidate=Mira
```
