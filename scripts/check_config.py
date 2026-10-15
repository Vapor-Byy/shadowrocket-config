#!/usr/bin/env python3
"""Shadowrocket 项目检查器：标准库；静态检查不能代替 iPhone 验收。"""
import argparse
import hashlib
import ipaddress
import json
import re
import ssl
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
KNOWN = {
    'DOMAIN', 'DOMAIN-SUFFIX', 'DOMAIN-KEYWORD', 'DOMAIN-REGEX',
    'IP-CIDR', 'IP-CIDR6', 'GEOIP', 'IP-ASN', 'USER-AGENT', 'URL-REGEX',
    'DST-PORT', 'SRC-PORT', 'SRC-IP', 'RULE-SET', 'DOMAIN-SET', 'FINAL',
}
POLICIES = {'DIRECT', 'PROXY', 'REJECT', 'REJECT-DROP', 'REJECT-TINYGIF'}
PRIVATE = [ipaddress.ip_network(s) for s in (
    '10.0.0.0/8', '127.0.0.0/8', '169.254.0.0/16', '172.16.0.0/12',
    '192.168.0.0/16', '::1/128', 'fc00::/7', 'fe80::/10')]
DEFAULTS = {'dns-server': 'system', 'fallback-dns-server': 'system',
            'dns-direct-system': 'true', 'ipv6': 'true', 'prefer-ipv6': 'false'}
SECRET = re.compile(
    r'(?:ss|ssr|trojan|vless|vmess)://|'
    r'\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b|'
    r'\b(?:password|passwd|token|api[-_ ]?key|cookie|authorization|subscription)\s*[:=]|'
    r'\b(?:gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]+|sk-[A-Za-z0-9_-]{20,})', re.I)


def active_lines(text):
    for n, raw in enumerate(text.splitlines(), 1):
        line = raw.strip()
        if line and not line.startswith(('#', ';', '//')):
            # Shadowrocket 常见行尾注释；URL fragment 不作为注释剥离。
            yield n, re.split(r'\s+[;#]', line, maxsplit=1)[0].rstrip()


def hostname(value, suffix=False):
    if suffix:
        value = value.lstrip('.')
    try:
        encoded = value.rstrip('.').encode('idna').decode('ascii')
    except UnicodeError:
        return False
    return bool(encoded) and len(encoded) <= 253 and all(
        re.fullmatch(r'[A-Za-z0-9_](?:[A-Za-z0-9_-]{0,61}[A-Za-z0-9_])?', label)
        for label in encoded.split('.'))


def url_error(url):
    try:
        u = urllib.parse.urlsplit(url)
        if u.scheme != 'https' or not u.hostname or u.username or u.password or u.fragment:
            return '列表必须是无认证信息的 HTTPS URL'
        if u.query:
            return '本项目远程列表不应带查询认证参数'
        if u.port not in (None, 443):
            return '本项目列表仅使用 HTTPS 默认端口'
        path = u.path
        if not (u.hostname in {'cdn.jsdelivr.net', 'raw.githubusercontent.com'}
                and 'blackmatrix7/ios_rule_script' in path
                and '/rule/Shadowrocket/' in path and path.endswith('.list')):
            return '需使用 blackmatrix7/ios_rule_script 的 Shadowrocket 专用 .list 路径'
    except ValueError:
        return '列表 URL 无效'
    return None


def check_rule(line, n, errors, warnings, external=False):
    parts = [p.strip() for p in line.split(',')]
    typ = parts[0]
    label = f'第 {n} 行'
    if typ not in KNOWN:
        warnings.append(f'{label}：未自动验证规则类型 {typ}，须人工核对 Shadowrocket 文档/参数')
        return parts
    if typ == 'FINAL':
        if external or parts != ['FINAL', 'PROXY']:
            errors.append(f'{label}：本配置只允许 FINAL,PROXY，外部列表不应有 FINAL')
        return parts
    expected = 2 if external else 3
    extra = parts[expected:]
    if len(parts) < expected or any(not p for p in parts[:expected]):
        errors.append(f'{label}：规则参数缺失')
        return parts
    if extra and not (typ in {'IP-CIDR', 'IP-CIDR6', 'GEOIP', 'IP-ASN', 'RULE-SET'} and extra == ['no-resolve']):
        errors.append(f'{label}：规则参数/修饰符未支持，请核对上游语法')
    if not external and parts[2] not in POLICIES:
        errors.append(f'{label}：策略必须来自本项目本地内建策略，不加入节点或策略组')
    value = parts[1]
    if typ in {'DOMAIN', 'DOMAIN-SUFFIX'} and not hostname(value, suffix=typ == 'DOMAIN-SUFFIX'):
        errors.append(f'{label}：域名值无效；DOMAIN 不支持通配符或 URL')
    if typ in {'IP-CIDR', 'IP-CIDR6', 'SRC-IP'}:
        try:
            if '/' not in value:
                raise ValueError('缺少 CIDR 前缀')
            net = ipaddress.ip_network(value, strict=False)
            # Shadowrocket 上游 Lan/Proxy/China 实际以 IP-CIDR 表示两种地址族。
            # https://github.com/blackmatrix7/ios_rule_script/blob/master/rule/Shadowrocket/Lan/Lan.list
            if typ == 'IP-CIDR6' and net.version != 6:
                raise ValueError('IPv4/IPv6 类型不符')
            if not external and parts[2] != 'DIRECT' and any(
                    net.version == p.version and net.overlaps(p) for p in PRIVATE):
                errors.append(f'{label}：非 DIRECT 地址规则与私有/本地网络重叠，请收窄')
        except ValueError as e:
            errors.append(f'{label}：IP/CIDR 无效（{e}）')
    if typ == 'GEOIP' and not re.fullmatch(r'[A-Z]{2}', value):
        errors.append(f'{label}：GEOIP 国家代码应为两个大写字母')
    if typ == 'IP-ASN' and not value.isdecimal():
        errors.append(f'{label}：ASN 应为数字')
    if typ in {'DST-PORT', 'SRC-PORT'}:
        try:
            endpoints = value.split('-')
            if not 1 <= len(endpoints) <= 2 or not all(1 <= int(p) <= 65535 for p in endpoints):
                raise ValueError()
            if len(endpoints) == 2 and int(endpoints[0]) > int(endpoints[1]):
                raise ValueError()
        except ValueError:
            errors.append(f'{label}：端口或端口范围无效')
    if typ in {'RULE-SET', 'DOMAIN-SET'}:
        problem = url_error(value)
        if problem:
            errors.append(f'{label}：{problem}')
        if value.endswith('/China/China_Domain.list') and typ != 'DOMAIN-SET':
            errors.append(f'{label}：China_Domain.list 必须用 DOMAIN-SET')
        if value.endswith('/China/China.list') and typ != 'RULE-SET':
            errors.append(f'{label}：China.list 必须用 RULE-SET')
    return parts


def parse(text, errors):
    sections, section = {}, None
    for n, line in active_lines(text):
        if line.startswith('['):
            if not re.fullmatch(r'\[[A-Za-z][A-Za-z0-9_-]*\]', line):
                errors.append(f'第 {n} 行：Section 结构无效')
                section = None
                continue
            section = line[1:-1]
            if section in sections:
                errors.append(f'第 {n} 行：重复 Section {section}')
            sections.setdefault(section, [])
            if section not in {'General', 'Rule', 'Host'}:
                errors.append(f'第 {n} 行：本项目不启用 [{section}]，包括节点/MITM/rewrite/脚本')
        elif section is None:
            errors.append(f'第 {n} 行：内容不在有效 Section 中')
        else:
            sections[section].append((n, line))
    for section in ('General', 'Rule', 'Host'):
        if section not in sections:
            errors.append(f'缺少 [{section}]')
    return sections


def settings(sections, errors):
    result = {}
    for section in ('General', 'Host'):
        values = result.setdefault(section, {})
        for n, line in sections.get(section, []):
            if '=' not in line:
                errors.append(f'第 {n} 行：[{section}] 应为键 = 值')
                continue
            key, value = [p.strip() for p in line.split('=', 1)]
            if not key or not value or key in values:
                errors.append(f'第 {n} 行：键/值为空或键重复')
            if section == 'General' and not re.fullmatch(r'[a-z][a-z0-9-]*', key):
                errors.append(f'第 {n} 行：General 键结构无效')
            if section == 'Host':
                if not hostname(key.removeprefix('*.')):
                    errors.append(f'第 {n} 行：Host 主机名无效')
                try:
                    if not value.startswith('server:'):
                        ipaddress.ip_address(value)
                except ValueError:
                    errors.append(f'第 {n} 行：Host 地址无效')
            values[key] = value
    return result


def check_config(text, baseline=None, allow_settings_change=False):
    errors, warnings = [], []
    if SECRET.search(text):
        errors.append('配置含疑似节点/订阅/UUID/私有认证信息，请移除（不输出内容）')
    sections = parse(text, errors)
    current = settings(sections, errors)
    if not allow_settings_change:
        if baseline is None:
            for k, v in DEFAULTS.items():
                if current['General'].get(k) != v:
                    errors.append(f'关键设置 {k} 应保留 {v}；授权修改需明确记录')
        else:
            base_errors = []
            old = settings(parse(baseline, base_errors), base_errors)
            if base_errors:
                errors.append('基线结构无效，不能用于设置保护')
            protected = {k for k in old['General'] | current['General']
                         if k.startswith('dns-') or 'dns' in k or k in {
                             'ipv6', 'prefer-ipv6', 'skip-proxy', 'tun-excluded-routes'}}
            for k in sorted(protected):
                if old['General'].get(k) != current['General'].get(k):
                    errors.append(f'相对基线关键设置 {k} 改变，需明确授权/证据及恢复说明')
            for k in old['Host'] | current['Host']:
                if any(s in k for s in ('apple.com', 'icloud.com')) and old['Host'].get(k) != current['Host'].get(k):
                    errors.append(f'相对基线 Apple 系统 DNS Host {k} 改变')
    rules = [(n, check_rule(line, n, errors, warnings)) for n, line in sections.get('Rule', [])]
    finals = [i for i, (_, p) in enumerate(rules) if p[0] == 'FINAL']
    if len(finals) != 1 or finals[0] != len(rules) - 1:
        errors.append('[Rule] 必须有唯一 FINAL,PROXY 且为最后一条有效规则')
    lan = [i for i, (_, p) in enumerate(rules) if len(p) >= 3 and
           p[0] == 'RULE-SET' and p[1].endswith('/Lan/Lan.list') and p[2] == 'DIRECT']
    china = [i for i, (_, p) in enumerate(rules) if len(p) >= 3 and
             p[1].endswith(('/China/China.list', '/China/China_Domain.list')) and p[2] == 'DIRECT']
    cn = [i for i, (_, p) in enumerate(rules) if p == ['GEOIP', 'CN', 'DIRECT'] or p == ['GEOIP', 'CN', 'DIRECT', 'no-resolve']]
    def local_direct(parts):
        if len(parts) < 3 or parts[2] != 'DIRECT':
            return False
        if parts[0] in {'IP-CIDR', 'IP-CIDR6'}:
            try:
                net = ipaddress.ip_network(parts[1], strict=False)
                return any(net.version == p.version and net.subnet_of(p) for p in PRIVATE)
            except ValueError:
                return False
        return parts[0] in {'DOMAIN', 'DOMAIN-SUFFIX'} and parts[1] in {'localhost', 'local'}

    if not lan or any(not local_direct(p) for _, p in rules[:min(lan)]):
        errors.append('本项目 Lan DIRECT 应优先于非局域网规则；其前仅可添加本地 DIRECT')
    china_paths = {p[1].rsplit('/', 1)[-1] for _, p in rules if len(p) >= 3 and
                   '/China/' in p[1] and p[2] == 'DIRECT'}
    if not {'China.list', 'China_Domain.list'} <= china_paths:
        errors.append('需共同保留 China.list 与 China_Domain.list 的 DIRECT 规则')
    if not cn or (china and max(china) >= min(cn)):
        errors.append('China 域名应在 GEOIP,CN,DIRECT 前，且保留该 CN 规则')
    for i, (n, p) in enumerate(rules):
        if len(p) < 3:
            continue
        if p[2] == 'PROXY' and (china or cn) and i >= min(china + cn):
            errors.append(f'第 {n} 行：强制代理应在 China 与 GEOIP,CN 前')
        if p[2] == 'DIRECT' and p[0] in {'DOMAIN', 'DOMAIN-SUFFIX', 'DOMAIN-KEYWORD'}:
            if any(len(q) >= 3 and q[2] == 'PROXY' for _, q in rules[:i]):
                warnings.append(f'第 {n} 行：DIRECT 例外位于代理规则后，需核对是否会被抢先匹配')
    if warnings:
        warnings.append('警告须人工审阅；自动检查无法判定所有域名/列表交集及用户例外意图')
    urls = [(p[0], p[1]) for _, p in rules if len(p) >= 3 and p[0] in {'RULE-SET', 'DOMAIN-SET'}]
    return {'errors': errors, 'warnings': warnings, 'urls': urls,
            'settings_guard': '授权跳过' if allow_settings_change else ('Git 基线' if baseline is not None else '默认 DNS/IPv6；未对照全部旧设置')}


def validate_list(text, typ):
    errors, warnings = [], []
    lines = list(active_lines(text))
    if not lines:
        return ['列表为空或只有注释'], warnings, 0
    if re.search(r'<(?:!doctype|html|head|body)\b', text, re.I) or text.lstrip().startswith(('{', '[')):
        return ['内容为 HTML/JSON/其他格式，非规则列表'], warnings, len(lines)
    for n, line in lines:
        if typ == 'DOMAIN-SET':
            if ',' in line or not hostname(line, suffix=True):
                errors.append(f'第 {n} 行：非 DOMAIN-SET 域名项')
        else:
            if ',' not in line:
                errors.append(f'第 {n} 行：非 RULE-SET 规则项')
            else:
                check_rule(line, n, errors, warnings, external=True)
    return errors, warnings, len(lines)


def download(typ, url, timeout):
    result = {'type': typ, 'url': url}
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'shadowrocket-config-check/1.0'})
        with urllib.request.urlopen(req, timeout=timeout, context=ssl.create_default_context()) as response:
            if response.status != 200 or urllib.parse.urlsplit(response.url).scheme != 'https':
                raise ValueError('HTTP 非 200 或重定向不为 HTTPS')
            body = response.read(20 * 1024 * 1024 + 1)
            if len(body) > 20 * 1024 * 1024:
                raise ValueError('列表过大，未验证')
            text = body.decode('utf-8-sig')
            errors, warnings, count = validate_list(text, typ)
            result.update(status='内容错误' if errors else ('需人工核对' if warnings else '通过'),
                          http_status=response.status, content_type=response.headers.get('Content-Type'),
                          bytes=len(body), entries=count, sha256=hashlib.sha256(body).hexdigest(),
                          errors=errors[:20], warnings=warnings[:20])
    except urllib.error.HTTPError as e:
        result.update(status='未验证', reason=f'HTTP {e.code}；需区分目的地限制、CDN 和上游错误')
    except (OSError, ValueError, urllib.error.URLError) as e:
        reason = getattr(e, 'reason', e)
        kind = 'TLS 证书验证失败' if isinstance(reason, ssl.SSLCertVerificationError) else type(e).__name__
        result.update(status='未验证', reason=f'{kind}: {reason}')
    return result


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('config', nargs='?', type=Path, default=ROOT / 'shadowrocket.conf')
    ap.add_argument('--baseline-ref', help='与实际 Git ref 的 shadowrocket.conf 对照，保护已有设置')
    ap.add_argument('--allow-settings-change', action='store_true', help='仅在任务明确授权时使用，须记录原因及恢复方式')
    ap.add_argument('--network', action='store_true', help='下载当前引用列表，保持 TLS 验证')
    ap.add_argument('--timeout', type=float, default=20)
    ap.add_argument('--json', action='store_true', help='输出机器可读报告')
    args = ap.parse_args()
    if args.timeout <= 0:
        ap.error('--timeout 必须大于零')
    try:
        baseline = None
        if args.baseline_ref:
            if not re.fullmatch(r'[A-Za-z0-9_./-]+', args.baseline_ref) or args.baseline_ref.startswith('-'):
                ap.error('基线 ref 无效')
            baseline = subprocess.run(['git', 'show', f'{args.baseline_ref}:shadowrocket.conf'],
                                      cwd=ROOT, check=True, capture_output=True, text=True).stdout
        report = check_config(args.config.read_text(encoding='utf-8-sig'), baseline, args.allow_settings_change)
    except (OSError, UnicodeError, subprocess.CalledProcessError) as e:
        print(f'读取配置/基线失败：{type(e).__name__}', file=sys.stderr)
        return 2
    report['static'] = '失败' if report['errors'] else ('需人工核对' if report['warnings'] else '通过')
    report['network'] = []
    if args.network and not report['errors']:
        for typ, url in dict.fromkeys(map(tuple, report['urls'])):
            report['network'].append(download(typ, url, args.timeout))
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(f"静态校验：{report['static']}；设置保护：{report['settings_guard']}")
        for key in ('errors', 'warnings'):
            for message in report[key]:
                print(f'{key}: {message}')
        for row in report['network']:
            print(f"外部列表：{row['status']} {row['url']}（{row.get('entries', '未知')} 条）")
            if row.get('reason'):
                print(row['reason'])
            for message in row.get('errors', []) + row.get('warnings', []):
                print(message)
        if not args.network:
            print('外部 URL 下载：未执行（可加 --network）；iPhone 验收：未执行')
    if report['errors'] or any(r['status'] == '内容错误' for r in report['network']):
        return 1
    if report['warnings'] or any(r['status'] != '通过' for r in report['network']):
        return 2
    return 0


if __name__ == '__main__':
    sys.exit(main())
