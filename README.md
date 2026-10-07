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

后续只编辑 shadowrocket.conf；配置固定 URL 不变。规则从上往下匹配，所有自定义规则必须在 FINAL 前。强制直连规则应放在可能命中的 Proxy 规则之前；强制代理规则应放在 China 和 GEOIP,CN 之前，并保留局域网规则最高优先级。

每次修改检查 [General]、[Rule]、[Host] 完整；FINAL,PROXY 唯一且为规则末行；国内规则在 FINAL 前；远程 URL 为 HTTPS 且返回 Shadowrocket 格式；文件不含节点或凭据。

```bash
git status
git diff --check
git diff -- shadowrocket.conf
git add shadowrocket.conf
git commit -m "update shadowrocket rules"
git push origin main
```

不得 force push 或重写历史。

## 人工验收

- 国内：baidu.com、taobao.com、jd.com、bilibili.com，应正常打开并在连接记录中显示 DIRECT。
- 境外：google.com、youtube.com、chatgpt.com、github.com，应显示 PROXY。
- 局域网：路由器或 NAS 的 192.168.x.x，应显示 DIRECT。
- 未命中其他规则的流量应命中 FINAL,PROXY。

境外访问失败先检查节点；国内异常先确认“全局路由”为“配置”，再检查规则加载、命中记录与 DNS。配置静态校验不能代替 iPhone 上的实际验收。
