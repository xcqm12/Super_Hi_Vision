#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""check_no_secrets.py - 阻止凭据被误提交/误打包

扫描「git 会包含的文件」（已跟踪 + 未跟踪但未被 .gitignore 排除），匹配常见
凭据特征：GitHub / HuggingFace / OpenAI / Anthropic / AWS / Google / Slack /
GitLab / npm token、私钥块、硬编码口令等。

设计要点：
- **只报告「文件路径 + 命中类型」，绝不回显命中的内容**（避免把凭据写进 CI 日志）。
- 按字节匹配，压缩包/文本一视同仁。
- 模式字面量本身不会自匹配（私钥块与 npm token 两条已拆开写）。
- 对明显占位符（your_password / changeme / xxxx / <token> 等）不报，避免误伤。

退出码：0 = 干净；1 = 发现疑似凭据；2 = 拿不到文件清单。

用法（仓库根目录）：
    python tools/check_no_secrets.py
    python tools/check_no_secrets.py --all-files     # 连被忽略的文件也扫（自查用）
"""
from __future__ import annotations

import os
import re
import subprocess
import sys

# 单文件扫描上限：超过就只扫前 8MB（凭据不会藏在几十 MB 的尾部）
MAX_BYTES = 8 * 1024 * 1024

PATTERNS = [
    ('GitHub classic token', re.compile(rb'ghp_[A-Za-z0-9]{20,}')),
    ('GitHub fine-grained token', re.compile(rb'github_pat_[A-Za-z0-9_]{20,}')),
    ('GitHub oauth/app/refresh token', re.compile(rb'gh[osr]_[A-Za-z0-9]{20,}')),
    ('HuggingFace token', re.compile(rb'hf_[A-Za-z0-9]{20,}')),
    ('OpenAI-style key', re.compile(rb'sk-[A-Za-z0-9]{32,}')),
    ('Anthropic key', re.compile(rb'sk-ant-[A-Za-z0-9\-_]{20,}')),
    ('AWS access key id', re.compile(rb'AKIA[0-9A-Z]{16}')),
    ('Google API key', re.compile(rb'AIza[0-9A-Za-z\-_]{35}')),
    ('Slack token', re.compile(rb'xox[baprs]-[0-9A-Za-z\-]{10,}')),
    ('GitLab token', re.compile(rb'glpat-[A-Za-z0-9\-_]{20,}')),
    # 拆开写，否则这一行自己就会被匹配到
    ('npm auth token', re.compile(rb'//registry\.npmjs\.org/:_auth' + rb'Token=\S+')),
    ('private key block', re.compile(b'-----BEGIN ' + rb'[A-Z ]*PRIVATE KEY-----')),
    ('Azure storage account key', re.compile(rb'AccountKey=[A-Za-z0-9+/=]{40,}')),
    ('bearer JWT', re.compile(rb'Bearer\s+ey[A-Za-z0-9_\-]{10,}\.[A-Za-z0-9_\-]{10,}\.')),
    ('hardcoded password', re.compile(
        rb'(?i)(password|passwd|pwd|secret|api[_-]?key)\s*[:=]\s*["\']([^"\'\s]{8,})["\']')),
]

# 这些「值」是模板/占位，不当作泄漏
PLACEHOLDER = re.compile(
    rb'(?i)^(your|my|the|some|example|test|dummy|sample|fake|placeholder|none|null|'
    rb'changeme|change_me|password|passwd|secret|token|apikey|api_key|xxx+|'
    rb'\*+|\.\.\.+|<[^>]*>|\$\{[^}]*\}|%[A-Z_]+%)$')


def looks_placeholder(value: bytes) -> bool:
    v = value.strip()
    if not v:
        return True
    if PLACEHOLDER.match(v):
        return True
    # 只由一两种字符组成（xxxxxx、------、......）也算占位
    return len(set(v)) <= 2


# 拿不到 git 时的回退：目录遍历 + 跳过明显的忽略目录
SKIP_DIRS = {'.git', 'build', 'dist', '__pycache__', '.venv', 'venv', 'env',
             'node_modules', '.idea', '.vscode', '.pytest_cache', '.mypy_cache'}


def walk_files():
    files = []
    for dirpath, dirnames, filenames in os.walk('.'):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for fn in filenames:
            rel = os.path.relpath(os.path.join(dirpath, fn), '.')
            files.append(rel.replace(os.sep, '/'))
    return sorted(files)


def list_files(include_ignored: bool):
    """git 视角的文件清单；git 不可用时退回目录遍历（更严格，可能多扫）。"""
    cmds = [['ls-files', '--cached', '--others', '--exclude-standard']]
    if include_ignored:
        cmds.append(['ls-files', '--cached', '--others'])
    cmds.append(['ls-files'])
    for args in cmds:
        try:
            out = subprocess.run(['git', *args], capture_output=True, check=True)
        except Exception:
            continue
        text = out.stdout.decode('utf-8', 'replace')
        files = [line.strip() for line in text.splitlines() if line.strip()]
        if files:
            return files
    print('note: git is unavailable here - falling back to a directory walk',
          file=sys.stderr)
    return walk_files()


def scan(path: str):
    """返回 [(类型, 命中的值的长度)]，不返回值本身。"""
    try:
        with open(path, 'rb') as f:
            data = f.read(MAX_BYTES)
    except Exception:
        return None
    found = []
    for label, pattern in PATTERNS:
        m = pattern.search(data)
        if not m:
            continue
        # 取最后一个捕获组（口令类规则）或整段匹配，交给占位判断
        value = m.group(m.lastindex) if m.lastindex else m.group(0)
        if label == 'hardcoded password' and looks_placeholder(value):
            continue
        found.append((label, value))
    return found


def main() -> int:
    include_ignored = '--all-files' in sys.argv

    files = list_files(include_ignored)
    if not files:
        print('ERROR: cannot list files (git not available?)')
        return 2

    findings = []
    scanned = 0
    for rel in files:
        if not os.path.isfile(rel):
            continue
        hits = scan(rel)
        if hits is None:
            continue
        scanned += 1
        for label, _value in hits:
            findings.append((rel, label))

    print(f'files considered: {len(files)}   scanned: {scanned}')
    print()
    if not findings:
        print('OK: no credential-looking content in the files that would be committed.')
        return 0

    print('FAIL: credential-looking content found (values are NOT printed):')
    for rel, label in findings:
        print(f'  [!] {rel}  ->  {label}')
    print()
    print('Fix: remove the secret from the file, or store it outside the repo')
    print('     (see docs/CODE_SIGNING.md for the DPAPI-encrypted pattern).')
    print('     If this is a false positive, refine the pattern in')
    print('     tools/check_no_secrets.py - do not disable the check.')
    return 1


if __name__ == '__main__':
    sys.exit(main())
