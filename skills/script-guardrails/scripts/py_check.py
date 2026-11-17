#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""py_check.py —— 按《脚本规范》静态扫脚本，出问题清单

为什么有它（2026-11-16）：
    规范写完了，但「文档没人看，命令才会被执行」。把四条铁律里能静态判的做成检查。

检查项：
  E1 裸 except: pass            → 失败被伪装成成功
  E2 DELETE/TRUNCATE/REPLACE 但无 --dry-run → 破坏性操作不能预演
  E4 金额求和未用 Decimal        → 自证 assert 本身会误报
  E7 load_workbook 未用 read_only → 大文件吃满内存
  W1 有跳过逻辑但无比例上限      → 九成跳过仍退出 0
  W2 含写库 SQL，建议加 --dry-run
  W3 无运行回执（全库习惯，不阻断）

已删除的检查项：
  E6「保留字未加反引号」——实测 3 命中全是误报。静态正则分不清 ORDER BY 的关键字
  和「列名叫 order」；ecomdb.py 的 key 只是 Python 变量。SQL 语义交给数据库报错。

局限：
  W2 只看文件里有没有写库 SQL 字符串，含 SQL 但由调用方决定是否执行的文件也会被标
  （如 ecomdb.py）。所以 W2 是线索，不是结论。

用法：
    python py_check.py [路径...] [--top N]
"""
import argparse
import os
import re
import sys
from collections import Counter

TOOLS = os.path.expanduser("~/tools")   # 默认扫这个目录，可用参数覆盖
# 必须匹配「SQL 句式」，不能只匹配关键字——否则 str.replace() 和 JSON 里的 "delete" 都会被误报
# （2026-11-16 实测：不限定句式时 E2 报了 36 个，抽查两个全是误报）
WRITE_SQL = re.compile(r"\bINSERT\s+INTO\b|\bUPDATE\s+\S+\s+SET\b|\bDELETE\s+FROM\b", re.I)
DESTRUCTIVE = re.compile(r"\bDELETE\s+FROM\b|\bTRUNCATE\s+TABLE\b|\bREPLACE\s+INTO\b", re.I)


def check(path):
    try:
        src = open(path, encoding="utf-8").read()
    except Exception:
        return []
    if len(src.split("\n")) < 15:
        return []
    out = []

    for m in re.finditer(r"except[^\n]*:\s*\n\s*pass\s*(\n|$)", src):
        line = src[: m.start()].count("\n") + 1
        out.append(("E1", line, "裸 except: pass（失败会被伪装成成功）"))

    has_dry = "dry" in src.lower()
    if WRITE_SQL.search(src) and not has_dry:
        if DESTRUCTIVE.search(src):
            out.append(("E2", 0, "含 DELETE/TRUNCATE/REPLACE 但不支持 --dry-run"))
        else:
            out.append(("W2", 0, "含写库 SQL，建议加 --dry-run"))

    if re.search(r"sum\([^)]*(amount|amt)", src) and "Decimal" not in src:
        out.append(("E4", 0, "金额求和未用 Decimal（自证会误报）"))

    if "load_workbook" in src and "read_only" not in src:
        out.append(("E7", 0, "load_workbook 未加 read_only（大文件吃满内存）"))

    if re.search(r"except[^\n]*:\s*\n\s*continue", src) and not re.search(
            r"skip_n\s*/\s*read_n|skip_ratio|跳过比例", src):
        out.append(("W1", 0, "有跳过逻辑但没设比例上限（九成跳过仍退出 0）"))

    if not re.search(r"\[done\]|\[summary\]|logging\.", src):
        out.append(("W3", 0, "无运行回执（全库 102/102 都没有，属习惯问题）"))
    return out


def collect(paths):
    files, me = [], os.path.abspath(__file__)
    for p in paths:
        p = os.path.expanduser(p)
        if os.path.isdir(p):
            for f in os.listdir(p):
                fp = os.path.abspath(os.path.join(p, f))
                if f.endswith(".py") and fp != me:
                    files.append(fp)
        elif p.endswith(".py") and os.path.abspath(p) != me:
            files.append(p)
    return files


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("paths", nargs="*", default=[TOOLS])
    ap.add_argument("--top", type=int, default=0)
    a = ap.parse_args()

    files = collect(a.paths or [TOOLS])
    results = []
    for f in sorted(files):
        iss = check(f)
        if iss:
            results.append((len(iss), f, iss))

    cnt = Counter(c for _, _, iss in results for c, _, _ in iss)
    total = sum(len(i) for _, _, i in results)
    print("扫描 %d 个脚本，%d 个有问题，共 %d 处" % (len(files), len(results), total))
    print()

    show = results[: a.top] if a.top else results
    for _, f, iss in show:
        print("%-28s %d 处" % (os.path.basename(f), len(iss)))
        for code, line, msg in iss:
            print("    %-3s %s%s" % (code, ("L%d " % line) if line else "", msg))

    print()
    print("统计：", dict(cnt.most_common()))
    print("E=会导致数据错或返工（阻断），W=建议。只扫 >=15 行的脚本。")
    print("局限：W2 只看文件里有没有写库 SQL 字符串，含 SQL 但由调用方执行的文件也会被标（如 ecomdb.py）。")
    return 1 if sum(cnt.get(k, 0) for k in ("E1", "E2", "E7")) else 0


if __name__ == "__main__":
    sys.exit(main())
