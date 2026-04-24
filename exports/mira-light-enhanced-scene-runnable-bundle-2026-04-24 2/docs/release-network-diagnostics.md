# Release Network Diagnostics

## 目的

这份文档专门说明发布版里和真灯联网有关的排障脚本。

最常见的现实问题不是代码本身，而是：

- 你以为灯在 `172.20.10.3`，其实已经换了 IP
- Mac 已经连上热点，但路由没走到灯
- bridge 正常、console 正常，只有灯的 `/status` 打不通

## 脚本一：网络诊断

```bash
bash scripts/diagnose_mira_light_network.sh 172.20.10.3
```

这个脚本会输出：

- 当前到目标 IP 的 route
- 当前 active interface 和本机 IP
- 对灯的 `ping`
- `http://<lamp>/status`
- `http://<lamp>/led`

如果你已经把 `MIRA_LIGHT_LAMP_BASE_URL` export 了，也可以直接不带参数运行。

## 脚本二：热点路由修复

```bash
bash scripts/fix_mira_light_hotspot_route.sh 172.20.10.3 172.20.10.1
```

这个脚本适合 macOS 接 iPhone 热点、灯在 `172.20.10.x` 网段时使用。

它会：

- 确认本机当前确实有接口拿到了 `172.20.10.1`
- 使用 `sudo route -n add -host ...` 给灯补一条主机路由
- 再打印一遍目标 route

注意：

- 这一步需要 `sudo`
- 它是网络环境修正，不是应用层修正
- 如果你根本没连对热点，它不会替你解决 Wi-Fi 连接问题

## 推荐排障顺序

如果在线 preflight 里 `lamp status` 失败，建议按这个顺序查：

1. `bash scripts/diagnose_mira_light_network.sh 172.20.10.3`
2. 确认当前 Wi-Fi / 热点是不是对的
3. 确认灯是否仍然在这个 IP
4. 如果是热点路由问题，再跑 `fix_mira_light_hotspot_route.sh`
5. 重新执行 `bash scripts/run_preflight_release.sh online`

## 一句话总结

发布版现在已经把“网络是不是通”的排障入口单独带进来了。  
先诊断，再修 route，最后再回到 online preflight，不要一开始就怀疑 bridge 或场景代码。
