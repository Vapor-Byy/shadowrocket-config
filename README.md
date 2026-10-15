# Shadowrocket 中国大陆长期分流配置

这是个人 Shadowrocket 分流配置。中国大陆服务尽量直连，境外流量默认代理，适合长期保持 Shadowrocket 开启。节点由 Shadowrocket 本地管理，本仓库不存放节点、订阅、密码或认证信息。

## 固定配置地址

https://raw.githubusercontent.com/Vapor-Byy/shadowrocket-config/main/shadowrocket.conf

## iPhone 首次导入

1. 打开 Shadowrocket → 配置 → 添加配置（+）→ URL。
2. 粘贴上面的地址，下载后选择并使用该配置。
3. 返回首页，将“全局路由”设为“配置”，选择有效节点，开启 Shadowrocket。
4. 确认四个远程规则列表均加载成功。首次下载可能需要先使用可用节点。

以后在“配置”页更新同一 URL 即可。更新主配置后，也要确认远程规则加载成功；规则源为动态更新的 master 分支。

## 匹配顺序

1. 局域网和私有网络：DIRECT。
2. Proxy 规则中的特殊服务：PROXY。
3. China 域名规则：DIRECT。
4. 中国大陆 IP（GEOIP,CN）：DIRECT。
5. 其他流量：FINAL,PROXY。

保留系统 DNS、IPv6 开启且不优先。不启用 MITM、HTTPS 解密、CA 证书、脚本或 rewrite。

## 规则来源

使用 [blackmatrix7 的 Shadowrocket 规则](https://github.com/blackmatrix7/ios_rule_script/tree/master/rule/Shadowrocket)，通过 jsDelivr HTTPS 引用 Lan、Proxy、China 和 China_Domain。按照上游说明，China.list 使用 RULE-SET，China_Domain.list 使用 DOMAIN-SET，两者共同使用。

远程规则下载失败时不能保证完整的国内/局域网匹配，请检查列表加载状态。国内网站是否直连取决于域名规则、解析结果和 GeoIP 数据，实际路由以 Shadowrocket 连接记录为准。

## 修改与维护

分流修改编辑 shadowrocket.conf，同时更新 STATUS.md、TASKS.md、CHANGELOG.md；配置固定 URL 不变。规则从上往下匹配，所有自定义规则必须在 FINAL 前。强制直连规则应放在可能命中的 Proxy 规则之前；强制代理规则应放在 China 和 GEOIP,CN 之前，并保留局域网规则最高优先级。DOMAIN 匹配单一主机；DOMAIN-SUFFIX 匹配根域及子域，按实际意图选择范围。

每次修改检查 [General]、[Rule]、[Host] 完整；FINAL,PROXY 唯一且为规则末行；国内规则在 FINAL 前；远程 URL 为 HTTPS 且返回 Shadowrocket 格式；文件不含节点或凭据。

```bash
git status
git fetch origin main
python3 scripts/check_config.py --baseline-ref origin/main
python3 scripts/check_config.py --baseline-ref origin/main --network
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s scripts
git diff --check
git diff -- shadowrocket.conf
```

这些命令在 Cloud 运行，手机无需开电脑或执行终端命令。检查后仅暂存本次明确修改的文件，普通提交并推送 main；不使用 `git add .`、force push 或重写历史。发布前再次获取远端；有并发更新先审阅合并，保留未提交修改。GitHub 连接支持时也可基于最新树使用 API 普通发布，不改账号权限或分支保护。

检查器仅用 Python 标准库，不需安装依赖。`--baseline-ref` 保护全部原有 DNS、IPv6、skip-proxy、tun-excluded-routes 和 Apple Host 设置；单独运行 `python3 scripts/check_config.py` 只检查当前结构和默认关键值，不能替代基线对照。明确任务或实际证据授权更改设置时，可加 `--allow-settings-change`，须记录原因及恢复方式。

`--network` 下载实际引用列表，验证非空、非 HTML/JSON、RULE-SET/DOMAIN-SET 内容及地址格式；不以注释统计或固定列表数量判断损坏。可加 `--json` 输出报告，`--timeout 20` 设置每次请求超时。退出码 0 为已执行检查通过，1 为内容/结构错误，2 为读取失败、网络未验证或语法需要人工核对。未知客户端语法、域名交集和例外意图必须人工审阅；这不是完整的 Shadowrocket 语法验证器。

## 从手机发起 Cloud 维护

1. 在手机 ChatGPT 的 Codex Cloud 中选择本仓库环境，直接描述目标，例如“将 example.com 及子域直连”或“检查 Telegram 媒体慢”。后续上下文以本仓库 AGENTS.md 和六份其他中文文档为准。
2. Cloud 先读取最新 main、保护工作区和历史，再依据证据最小修改、检查和更新维护记忆。对明确任务，用户已授权检查后普通发布 main，无需每次确认。
3. 查看报告中的四个独立状态：静态校验、外部 URL 下载、GitHub 发布、iPhone 验收。只有实际落入 main，固定 URL 才反映修改；本地提交或仅创建 PR 不算发布。
4. 若 main 保护或只能任务分支，则提供 PR；手机打开 PR，查看 Files changed 和 Checks，条件满足时点 Merge pull request 并确认。需要新增权限时只在账号界面授权本仓库，不向聊天粘贴密码、Token 或节点订阅。
5. 发布后 Cloud 读取 main 和 Raw 核验；用户在 Shadowrocket“配置”页更新原 URL，确认远程规则列表也加载成功，再执行下方手机验收。Raw 可能缓存，未能核验须明确报告。

## Cloud 环境的单独设置

本次会话真实运行于 Cloud，但环境状态没有关联已发布的持久配置；当前工具只能读取状态，不能替用户创建或发布可长期选择的环境。仓库发布成功不代表此设置已完成。

若手机尚不能选到本仓库环境：用手机浏览器打开 [Codex](https://chatgpt.com/codex) → 设置中的环境（Environments）→ 创建环境，选择现有 Vapor-Byy/shadowrocket-config、默认 main，仅本人使用。使用包含 Git、Python 3、curl 的默认环境即可，无需启动脚本或第三方依赖。保存；若界面显示“发布”按钮，需发布后再回手机 Cloud 选择。入口名称以账号当前界面为准；已有合适环境则直接选择，不重复创建仓库。

需要受限联网时，仅为 github.com、raw.githubusercontent.com、cdn.jsdelivr.net、api.github.com 配置必要 HTTPS 访问；新诊断目标按任务增加。当前会话的网络策略为 unrestricted，本项目没有扩大设置。网络放行不等于 GitHub 写权限，仍使用已有 GitHub 连接授权。若仓库不在选择列表，在 Codex 设置中的 GitHub 连接管理里仅添加本仓库访问权限。不要把 Cloud 环境共享给他人。

## 人工验收

- 国内：baidu.com、taobao.com、jd.com、bilibili.com，应正常打开并在连接记录中显示 DIRECT。
- 境外：google.com、youtube.com、chatgpt.com、github.com，应显示 PROXY。
- 局域网：路由器或 NAS 的 192.168.x.x，应显示 DIRECT。
- 未命中其他规则的流量应命中 FINAL,PROXY。

境外访问失败先检查节点；国内异常先确认“全局路由”为“配置”，再检查规则加载、命中记录与 DNS。配置静态校验不能代替 iPhone 上的实际验收。
