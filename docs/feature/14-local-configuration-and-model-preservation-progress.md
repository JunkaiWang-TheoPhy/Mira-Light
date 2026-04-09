# Local Configuration and Model Preservation Progress

## Current Status

`Claw-Native` 现在已经取消了“模板强制指定默认模型”的做法。

这意味着仓库模板不再擅自替每台机器决定 `agents.defaults.model`，而是把模型选择权重新交还给本机节点。

## What Changed In The Repository

这一轮已经完成两件关键调整：

1. `Claw-Native /templates/openclaw.template.jsonc` 不再写死默认模型
2. `scripts/apply_claw_native_local.py` 在模板没有提供模型时，会保留本机现有的 `agents.defaults.model`

因此现在的 `Claw-Native` apply 流程，仍然会负责：

- gateway 配置
- plugin 配置
- bridge / vision env
- workspace 身份文件
- wrapper 与 launchd 模板

但它不再默认替操作者覆盖本机正在使用的模型。

## What Has Been Verified On The Verified Machine

这条规则已经不只是代码层面的“看起来合理”。

在验证机器上，它已经被实际核对过：

- 当前 live `openclaw.json` 的现有模型配置可以被保留
- 再次 materialize `Claw-Native` 时，不会因为模板而回写一个新的默认模型
- workspace、plugin、bridge、vision 这些其他 `Claw-Native` 组成部分仍然照常可被 apply

也就是说，现在的行为已经从“apply 可能顺手改模型”变成了“apply 负责节点形态，模型仍由本机自己决定”。

## Why This Matters

这一步很重要，因为模型配置往往是部署机最容易出现漂移、也最容易引发误解的地方。

如果模板继续强行钉死模型，会带来几个问题：

- 一键 apply 会悄悄覆盖操作者当前选择
- 文档模板会和 live 节点策略绑死
- 不同机器难以保留各自的模型实验与运营偏好

取消模板级硬编码之后，`Claw-Native` 更像一个真正可复用的部署包，而不是带有隐含策略覆盖的“半模板半成品”。

## Current Boundary

这一轮改变的是“默认策略”，不是“禁止配置模型”。

边界应该这样理解：

- 如果某台机器显式设置了自己的模型，它会被保留
- 如果未来运营上需要固定某个模型，仍然可以在本机配置里明确设置
- `Claw-Native` 现在默认只提供节点骨架，不再把模型选择伪装成仓库共识

## Recommended External Framing

> `Claw-Native` 现在已经取消模板层面对默认模型的硬编码。
> 它仍然负责把 Mira 的本地节点骨架、workspace、plugin 与常驻服务部署到位，
> 但不会再在 apply 时悄悄覆盖每台机器自己的模型选择。
