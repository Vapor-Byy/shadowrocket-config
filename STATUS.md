# 当前状态

更新日期：2026-10-15（Asia/Shanghai）；2026-10-08 开始准备，中断后恢复完成。

## 首次 Cloud 接管

- 真实 Cloud 已连接并运行；开始时没有仓库 checkout，现已在云端克隆唯一仓库，main 基线为 2880a7487481c005f467ca0aefed515f78c06e2e，初始工作区干净。
- GitHub 连接读取显示 push 权限，main 未保护且无 ruleset；发布仍以实际写入结果为准。
- 本次补齐七份中文维护文件和 scripts/check_config.py；shadowrocket.conf 保持原样。
- 静态校验通过（对照 origin/main）；19 项标准库回归测试通过。最终联网内容校验四项均通过，TLS 验证保持开启，未修改分流配置。
- GitHub 发布：检查完成、待普通发布；发布后追加实际提交及远端核验结果。iPhone 仍未实测。
- 环境报告网络 unrestricted/enforced，本次不扩大放行范围；HTTPS 命令需执行工具的网络权限，保持继承代理和 TLS 校验。
- 本会话只提供环境状态读取能力，无持久配置创建/发布工具；source_config_id/source_config_version_id 均为空。当前会话可执行维护，但不能据此声称已有发布的、下次手机可选择的仓库环境。

## 2026-10-15 外部列表检查

当前配置引用的四个 jsDelivr URL 均为 HTTP 200，非空文本，RULE-SET/DOMAIN-SET 内容检查无错误/未知语法。有效条目数仅记录当前观察，不作为未来固定条件。

| 列表 | 字节 | 有效条目 | SHA-256 |
| --- | ---: | ---: | --- |
| Lan.list | 4776 | 140 | e524edec216ed7f2fa2f3eb3fe09fe70121acf88408c2394d19b3e2331c54de7 |
| Proxy.list | 4477 | 134 | 0b27399c8fd125af42af729a4da9e45919b849f48a24ce2e41054c733e76a266 |
| China.list | 2038 | 63 | 65477cd1e2917a8ca09ba08132e9d9131c54c0d9e1cfcba0be2eaa8ea1a04b75 |
| China_Domain.list | 51067 | 3689 | d35eec789ae09a6d2b6dd48ed2c52d6d811f433b1e73a92b2f9246b778fa7923 |

准备期间部分请求曾返回 403，重试及最终完整检查成功；未将失败请求记为通过。初版检查器误拒 IP-CIDR 的 IPv6 值，已依据上游 Shadowrocket 列表修正并加入回归，未修改上游规则或关闭 IPv6。云端检查不代表中国大陆手机的下载或访问效果。

## 待用户验收

- iPhone 未实测。完成后在 Shadowrocket 更新原 URL，确认远程列表加载及国内、境外、局域网命中策略。
- Telegram 文字正常而媒体慢，尚未确诊；等待脱敏媒体连接策略、节点切换和 Wi-Fi/蜂窝对照。
