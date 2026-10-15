# 维护决策

## 2026-10-15：首次云端准备（2026-10-08 开始）

- 在原仓库增加必要维护记忆和标准库检查器，保留仓库名、main、shadowrocket.conf、固定 Raw URL 及现有历史。
- 首次准备无配置修改证据，因此保留系统 DNS、IPv6、路由和 Apple 系统解析设置；恢复不需要操作配置。
- 检查器自行逐行处理 Shadowrocket 配置，不使用通用 INI 解析器。自动检查结构、常用规则、地址、列表内容和明确顺序；未知语法提示人工核对，不能宣称完整客户端验证。支持新增例外与列表，不锁定行数、列表数或上游注释统计。
- 实际上游 Shadowrocket Lan/Proxy/China 用 IP-CIDR 表示 IPv4 与 IPv6；检查器按此兼容，IP-CIDR6 别名要求 IPv6。依据：https://github.com/blackmatrix7/ios_rule_script/blob/master/rule/Shadowrocket/Lan/Lan.list 。不将其他客户端的地址族限制套用到这里。
- `--baseline-ref` 对照实际 Git 版本保护全部已有 DNS 设置、IPv6、skip-proxy、tun-excluded-routes 和 Host 的 Apple 系统解析；经明确任务/证据授权更改时才使用 `--allow-settings-change`，并记录原因和恢复方案。
- 使用现有 GitHub 连接普通发布；不复制本机凭据、不改账号权限或保护。API 发布以最新树为基础、保留父提交，非强制移动 main 且核对预期头。
- 仓库发布与 Cloud 持久环境发布独立报告。当前环境正常运行但无持久配置绑定，只读状态工具不能创建/发布环境；必要网页设置由用户完成，不要求开电脑。
