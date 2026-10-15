"""检查器行为回归：不联网、不修改真实配置；运行 python3 -m unittest discover -s scripts。"""
import unittest
from pathlib import Path

import check_config as check


class ConfigTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.base = (Path(__file__).resolve().parents[1] / 'shadowrocket.conf').read_text()
        cls.proxy = next(line for line in cls.base.splitlines() if '/Proxy/Proxy.list' in line)

    def report(self, text):
        return check.check_config(text, self.base)

    def add_before_proxy(self, rule):
        return self.base.replace(self.proxy, rule + '\n' + self.proxy)

    def test_current_config_and_host_after_final(self):
        result = self.report(self.base)
        self.assertEqual(result['errors'], [])
        self.assertEqual(result['warnings'], [])

    def test_missing_required_sections(self):
        for section in ('General', 'Rule', 'Host'):
            with self.subTest(section=section):
                self.assertTrue(self.report(self.base.replace(f'[{section}]', '[Other]'))['errors'])

    def test_final_unique_policy_and_position(self):
        for replacement in ('FINAL,DIRECT', 'FINAL,PROXY\nFINAL,PROXY',
                            'FINAL,PROXY\nDOMAIN,example.com,PROXY', '# FINAL removed'):
            with self.subTest(replacement=replacement):
                self.assertTrue(self.report(self.base.replace('FINAL,PROXY', replacement))['errors'])

    def test_direct_and_proxy_exceptions_before_broad_rules(self):
        for rule in ('DOMAIN,example.com,DIRECT', 'DOMAIN-SUFFIX,example.com,PROXY'):
            with self.subTest(rule=rule):
                result = self.report(self.add_before_proxy(rule))
                self.assertEqual(result['errors'], [])
                self.assertEqual(result['warnings'], [])

    def test_direct_exception_after_proxy_needs_review(self):
        text = self.base.replace(self.proxy, self.proxy + '\nDOMAIN,example.com,DIRECT')
        self.assertTrue(self.report(text)['warnings'])

    def test_proxy_after_china_rejected(self):
        text = self.base.replace('GEOIP,CN,DIRECT', 'DOMAIN,example.com,PROXY\nGEOIP,CN,DIRECT')
        self.assertTrue(self.report(text)['errors'])

    def test_local_direct_can_precede_lan(self):
        text = self.base.replace('[Rule]', '[Rule]\nIP-CIDR,192.168.1.0/24,DIRECT,no-resolve')
        self.assertEqual(self.report(text)['errors'], [])

    def test_nonlocal_rule_cannot_precede_lan(self):
        text = self.base.replace('[Rule]', '[Rule]\nDOMAIN,example.com,PROXY')
        self.assertTrue(self.report(text)['errors'])

    def test_private_network_proxy_rejected(self):
        for cidr in ('192.168.0.0/16', 'fc00::/7'):
            with self.subTest(cidr=cidr):
                self.assertTrue(self.report(self.add_before_proxy(f'IP-CIDR,{cidr},PROXY'))['errors'])

    def test_ipv6_ip_cidr_and_no_resolve_supported(self):
        text = self.add_before_proxy('IP-CIDR,2001:4860::/32,PROXY,no-resolve')
        self.assertEqual(self.report(text)['errors'], [])
        errors, warnings, count = check.validate_list('IP-CIDR,fc00::/7,no-resolve\n', 'RULE-SET')
        self.assertEqual((errors, warnings, count), ([], [], 1))

    def test_invalid_cidr_and_ipv6_alias(self):
        for rule in ('IP-CIDR,300.0.0.0/8,PROXY', 'IP-CIDR,1.2.3.4/99,PROXY',
                     'IP-CIDR6,8.8.8.0/24,PROXY'):
            with self.subTest(rule=rule):
                self.assertTrue(self.report(self.add_before_proxy(rule))['errors'])

    def test_domain_is_host_not_url_or_wildcard(self):
        for value in ('https://example.com', '*.example.com'):
            with self.subTest(value=value):
                self.assertTrue(self.report(self.add_before_proxy(f'DOMAIN,{value},DIRECT'))['errors'])

    def test_baseline_protects_network_settings(self):
        changes = (('dns-server = system', 'dns-server = 8.8.8.8'),
                   ('ipv6 = true', 'ipv6 = false'),
                   ('skip-proxy =', 'skip-proxy-old ='),
                   ('tun-excluded-routes =', 'tun-excluded-routes-old ='),
                   ('*.apple.com = server:system', '*.apple.com = 1.2.3.4'))
        for old, new in changes:
            with self.subTest(key=old):
                self.assertTrue(self.report(self.base.replace(old, new))['errors'])

    def test_mitm_proxy_rewrite_and_secrets_rejected(self):
        for extra in ('\n[MITM]\nenable = true', '\n[Proxy]\nnode = example',
                      '\n[URL-Rewrite]\nexample = test', '\n# vmess://example',
                      '\n# token = example'):
            with self.subTest(extra=extra):
                self.assertTrue(self.report(self.base + extra)['errors'])

    def test_unknown_syntax_needs_review(self):
        self.assertTrue(self.report(self.add_before_proxy('FUTURE-TYPE,example.com,PROXY'))['warnings'])

    def test_additional_list_without_fixed_count(self):
        url = 'https://cdn.jsdelivr.net/gh/blackmatrix7/ios_rule_script@master/rule/Shadowrocket/Telegram/Telegram.list'
        self.assertEqual(self.report(self.add_before_proxy(f'RULE-SET,{url},PROXY'))['errors'], [])

    def test_url_security_and_china_type(self):
        self.assertTrue(self.report(self.base.replace('https://cdn.jsdelivr.net', 'http://cdn.jsdelivr.net'))['errors'])
        self.assertTrue(self.report(self.base.replace('DOMAIN-SET,', 'RULE-SET,'))['errors'])

    def test_lists_reject_error_pages_empty_and_wrong_types(self):
        for text, typ in (('', 'RULE-SET'), ('# comments only', 'DOMAIN-SET'),
                          ('<html>error</html>', 'RULE-SET'), ('{"error": true}', 'DOMAIN-SET'),
                          ('payload:\n  - example.com', 'RULE-SET'),
                          ('DOMAIN,example.com', 'DOMAIN-SET'), ('.example.com', 'RULE-SET')):
            with self.subTest(text=text, typ=typ):
                self.assertTrue(check.validate_list(text, typ)[0])

    def test_domain_set_accepts_exact_suffix_and_ignores_counts(self):
        result = check.validate_list('# TOTAL: 9999\nexample.com\n.example.org\n', 'DOMAIN-SET')
        self.assertEqual(result, ([], [], 2))


if __name__ == '__main__':
    unittest.main()
