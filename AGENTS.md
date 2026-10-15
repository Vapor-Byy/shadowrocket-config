# 云端维护约定

适用于本仓库及子目录。先读 README.md、PROJECT.md、STATUS.md、TASKS.md、DECISIONS.md、CHANGELOG.md 和当前 shadowrocket.conf，再实施明确任务。

- 唯一仓库：Vapor-Byy/shadowrocket-config；发布分支 main；核心文件 shadowrocket.conf；固定 URL 不变。以远端当前版本为准，不用历史基线覆盖更新。
- 目标：iPhone 长期开启 Shadowrocket，局域网和中国大陆服务尽量直连，境外及未识别流量代理。节点由手机管理，不扩展为代理平台、订阅管理器或服务器系统。
- 规则第一条匹配生效：局域网/私有地址 DIRECT → 用户例外及特殊服务 → China 域名 DIRECT → GEOIP,CN,DIRECT → 唯一且最后有效的 FINAL,PROXY。保留 [General]、[Rule]、[Host]。
- 强制 DIRECT 例外在可能抢先匹配的 Proxy 前；强制 PROXY 在 China/GEOIP,CN 前；不得把私有网络送去代理。DOMAIN 仅单一主机，DOMAIN-SUFFIX 包含根域及子域；意图不明时只询问必要范围。
- 保留现有系统 DNS、ipv6=true、prefer-ipv6=false、skip-proxy、tun-excluded-routes 及 Apple 系统 DNS 行为。更改需要具体任务或连接/解析证据，记录原因和恢复方式。
- 继续使用 blackmatrix7/ios_rule_script 的 Shadowrocket 专用 HTTPS 列表。China.list 和 China_Domain.list 共同使用，分别为 RULE-SET 和 DOMAIN-SET。不混入 Clash YAML 或其他客户端专用语法。
- 不加入 [Proxy]、订阅、节点认证、MITM、解密证书、rewrite 或 HTTPS 抓取脚本。不上传私人聊天、凭据、节点、完整本机目录。只记录必要非敏感事实，不依赖 Mac 路径、钥匙串或个人技能。
- 环境最少 Git、Python 3、HTTPS 工具，无第三方依赖。必要网络目的地 github.com、raw.githubusercontent.com、cdn.jsdelivr.net；API 用 api.github.com。保留正常 TLS 校验，不绕过网络限制，不索取密码或 Token。
- 发布前获取 main 最新状态并保护未提交改动；分叉先检查解决，不 reset 覆盖、不强推。运行 `python3 scripts/check_config.py --baseline-ref origin/main`、同命令加 `--network`、`git diff --check`，审阅相关 diff。联网失败明确未验证，不冒充通过；静态检查不是客户端验证。
- 每次更新 STATUS.md、TASKS.md、CHANGELOG.md；重要选择写 DECISIONS.md，使用方式变化更新 README.md。未知规则/无法自动判断的例外需要核对上游和人工顺序审阅。
- 用户默认授权明确任务及首次维护准备在检查后普通提交并发布 main，无需反复确认。只暂存明确文件，禁止 `git add .`。允许使用现有 GitHub 连接的 API，基于最新树保留历史，用非强制更新及 expected_sha 防并发覆盖。
- main 保护或环境只允许任务分支时走 PR；普通合并须满足规则。不改权限/保护。无写权限交付完整补丁并说明最小连接操作。
- 发布后读取 main 文件确认一致，核验固定 Raw URL（注意缓存）。分别报告静态校验、外部 URL 下载、GitHub 发布、iPhone 验收；本地提交、PR、main、手机更新不是同一状态。
- Telegram 文字正常而媒体慢尚未确诊。先获取脱敏策略/节点记录、换节点、Wi-Fi/蜂窝及同节点其他境外服务对照，不重复堆规则、无证据改 DNS/IPv6 或承诺提速。

Cloud 任务使用实际 checkout，不要求电脑开机。持久环境配置发布与仓库发布分开核验；没有环境管理能力时说明网页剩余步骤，不能声称已创建或发布环境。
