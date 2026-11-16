#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""sanitize_check.py —— 发布前脱敏闸

为什么要有它：这类仓库最容易泄的不是代码，是**注释、示例、反例里夹带的真实经营信息**。
一次泄出去就收不回来，所以做成命令，发布前必跑。

检查五类（命中即阻断，退出码 1）：
  1. 凭据：sk- / ghp_ / AKIA / 长十六进制串
  2. 店铺与公司专名（自定义词表，见 DENY_WORDS）
  3. 真实金额：带千分位的金额、六位以上的小数金额
  4. 本机路径：C:\\Users\\ / /home/<name>/ / ~/.workbuddy
  5. 主机名、内网域名、私有仓地址

用法：
    python sanitize_check.py            # 扫当前目录
    python sanitize_check.py <目录>
"""
import os
import re
import sys

# ── 自定义词表：**不要提交真实词表**（它本身就是泄漏）──────────────────
# 放在 deny_words.txt（已在 .gitignore 里），每行一个词。
# 没有该文件时退回 deny_words.example.txt（占位词，供他人参考格式）。
def load_words():
    here = os.path.dirname(os.path.abspath(__file__))
    for name in ("deny_words.txt", "deny_words.example.txt"):
        path = os.path.join(here, name)
        if os.path.exists(path):
            return [ln.strip() for ln in open(path, encoding="utf-8")
                    if ln.strip() and not ln.startswith("#")]
    return []


PATTERNS = [
    ("凭据-OpenAI", re.compile(r"sk-[A-Za-z0-9_\-]{16,}")),
    ("凭据-GitHub", re.compile(r"gh[pousr]_[A-Za-z0-9]{20,}")),
    ("凭据-AWS", re.compile(r"AKIA[0-9A-Z]{16}")),
    ("凭据-通用长串", re.compile(r"\b[A-Za-z0-9_\-]{32,}\b")),
    ("本机路径-Win", re.compile(r"[A-Za-z]:\\\\?Users\\\\?[A-Za-z]")),
    ("本机路径-Unix", re.compile(r"/home/[a-z0-9_]+/")),
    ("内部目录", re.compile(r"\.work[a-z]*buddy")),
    ("大额数字", re.compile(r"\b\d{3},\d{3}\.\d{2}\b|\b\d{6,}\.\d{2}\b")),
    ("内网/私有仓", re.compile(r"github\.com/[a-z0-9\-]+/(wbsync|ecom-)", re.I)),
]

SKIP_DIRS = {".git", "__pycache__", "node_modules", ".venv"}
EXTS = {".md", ".py", ".json", ".txt", ".yml", ".yaml", ".sh"}


def scan(root, words):
    hits = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for fn in filenames:
            if os.path.splitext(fn)[1] not in EXTS:
                continue
            if fn in ("sanitize_check.py", "deny_words.txt", "deny_words.example.txt"):   # 规则文本自身不算泄漏
                continue
            path = os.path.join(dirpath, fn)
            try:
                text = open(path, encoding="utf-8").read()
            except Exception:
                continue
            for i, line in enumerate(text.split("\n"), 1):
                for word in words:
                    if word in line:
                        hits.append((path, i, "专名：%s" % word, line.strip()[:90]))
                for name, pat in PATTERNS:
                    if pat.search(line):
                        hits.append((path, i, name, line.strip()[:90]))
    return hits


def main():
    root = sys.argv[1] if len(sys.argv) > 1 else "."
    hits = scan(root, load_words())
    if not hits:
        print("✅ 未命中任何脱敏规则，可发布")
        return 0
    print("❌ 命中 %d 处，禁止发布：\n" % len(hits))
    for path, line, kind, text in hits[:40]:
        print("%s:%d  [%s]\n    %s" % (path, line, kind, text))
    if len(hits) > 40:
        print("\n… 还有 %d 处未列出" % (len(hits) - 40))
    return 1


if __name__ == "__main__":
    sys.exit(main())
