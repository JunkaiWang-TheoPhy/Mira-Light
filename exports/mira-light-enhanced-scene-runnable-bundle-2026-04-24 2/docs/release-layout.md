# Release Layout

`Mira_Light_Released_Version/` 当前采用的是“尽量保持原有相对路径兼容”的发布结构。

这样做的好处是：

- 现有 Python 脚本几乎不用改路径逻辑
- 现有 bridge / console / web 可以直接复用
- 以后从这个目录独立成 repo 的成本更低

## 当前结构

```text
Mira_Light_Released_Version/
├─ README.md
├─ LICENSE
├─ package.json
├─ requirements.txt
├─ config/
├─ deploy/
├─ docs/
├─ scripts/
├─ tests/
├─ tools/
└─ web/
```

## 各目录职责

- `config/`
  保存本地 profile 模板和 vision schema

- `deploy/`
  保存一键安装约定、manifest 和环境变量模板

- `docs/`
  保存 release 版说明文档和原始 PDF

- `scripts/`
  核心运行时、安装脚本、console、scene 定义、receiver、vision 入口

- `tests/`
  当前最重要的轻量验证脚本

- `tools/mira_light_bridge/`
  本地 bridge 与 OpenClaw 插件

- `web/`
  导演台前端与少量场景展示页
