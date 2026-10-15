# 项目说明

- 长期事项：Vapor_Shadowrocket分流配置_030。
- 仓库：https://github.com/Vapor-Byy/shadowrocket-config；main 发布；shadowrocket.conf 为固定入口。
- 导入 URL：https://raw.githubusercontent.com/Vapor-Byy/shadowrocket-config/main/shadowrocket.conf
- 用户使用中国大陆 iPhone，希望 VPN 始终开启，局域网/大陆服务尽量 DIRECT，境外及未识别服务 PROXY。
- 规则从上往下匹配；用户例外放在相关宽泛规则前，局域网最高优先，最终 FINAL,PROXY。
- 系统 DNS、IPv6 开启但不优先；节点本地管理，无节点/凭据、MITM 或 rewrite。
- 远程规则来自 blackmatrix7/ios_rule_script 的 Shadowrocket Lan、Proxy、China、China_Domain，通过 jsDelivr。China 的两个列表共同使用；上游 master 动态变化，每次联网验证以当前下载为准。
- 日常维护仅需 Cloud、已有 GitHub 授权及手机，不依赖 Mac 或常驻服务器。项目记忆存放本仓库七份中文 Markdown；检查脚本仅 Python 标准库。
- 交接已知历史提交：2880a7487481c005f467ca0aefed515f78c06e2e（2026-10-07），不是未来固定版本。

## 历史诊断边界

Telegram：2026-10-07 曾将官方 CIDR 与 Proxy 对照，当时 9 个 IPv4 网段已覆盖，且存在 DOMAIN-KEYWORD,telegram。这是历史规则核查，未获得 iPhone 媒体连接证据，不能作为当前实测或确诊。

notes.vapor299.cn：2026-10-07 Mac 曾匹配 China 的 DOMAIN-SUFFIX,cn；当时公网 IP 43.135.48.68。VPN 虚拟 IP 198.18.0.81 的 0.524 ms 不是服务器延迟；物理接口到公网 IP 的五次 ping 平均 212.578 ms，HTTPS 200/0.693916 秒。以上只保留历史上下文，不复用为当前 IP 或手机结果。配置 icmp-auto-reply=true，诊断须说明虚拟地址/自动回复及实际测试路径。
