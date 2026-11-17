#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""可复制的脚本骨架 —— 复制到 tools/ 改用途。写库/取数/批量都能用这个骨架。

为什么这么写（每条都对应一个真实教训）：
  - sys.exit(main())：让 `echo $?` 是真的，否则 0 也可能失败
  - ecomdb._cfg()：统一连接配置，别各自读 db_config.json（现有 14 个脚本在重复读）
  - --dry-run：只对写库脚本强制，但骨架里留着，省得以后补
  - 回执行：99/102 个老脚本没有，导致出错无法追溯是哪次跑的
  - Decimal：金额用 float 比较会误报

用法：python 脚本名.py <参数> [--dry-run]
"""
import argparse
import os
import sys
import time
from decimal import Decimal

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))   # 把本脚本放在你的 tools/ 里即可 import 同目录模块


def retry(fn, tries=3, base=2):
    """统一的网络/DB 重试。只包临时性错误，逻辑错误不要用这个。"""
    for i in range(tries):
        try:
            return fn()
        except Exception as e:                       # noqa: BLE001
            if i == tries - 1:
                raise
            wait = base ** i
            print("[retry %d/%d] %s；%.0fs 后重试" % (i + 1, tries, str(e)[:80], wait), file=sys.stderr)
            time.sleep(wait)


def main():
    ap = argparse.ArgumentParser(description="一句话说明这个脚本干什么")
    ap.add_argument("--dry-run", action="store_true", help="只打印将要做什么，不落库")
    ap.add_argument("--self-test", action="store_true", help="自检骨架：跑一遍回执与退出码，不碰数据")
    args = ap.parse_args()

    if args.self_test:
        # 复制模板后先跑这个：能打印 [done] 且 exit 0，说明骨架可用
        print("[self-test] 骨架可用：参数解析 / 回执行 / 退出码 都正常")
        print("[done] 读入 0 / 写入 0 / 跳过 0 / 耗时 0s")
        return 0

    t0 = time.time()
    read_n = write_n = skip_n = 0
    skip_reasons = {}

    # ---- 1. 取数 / 读文件 ----
    rows = []                                        # 占位：替换成真实读取
    read_n = len(rows)

    # ---- 2. 处理（逐行允许跳过，但要计数） ----
    good = []
    for idx, r in enumerate(rows):
        try:
            good.append(r)
        except Exception as e:                       # noqa: BLE001
            skip_n += 1
            key = str(e)[:40]
            skip_reasons[key] = skip_reasons.get(key, 0) + 1
            print("[skip] 第 %d 行：%s" % (idx, key), file=sys.stderr)

    # ---- 3. 跳过比例上限（铁律 4，别省） ----
    if read_n and skip_n / read_n > 0.01:
        print("跳过比例 %.1f%% 超过 1%%，中止。原因：%s" % (skip_n / read_n * 100, skip_reasons), file=sys.stderr)
        return 2

    # ---- 4. 写入 ----
    # 只读/增量：事务即可
    # 区间重建/覆盖历史：**必须先备份原行到 CSV**，再 DELETE，再 INSERT（三件套，缺一不可）
    if args.dry_run:
        print("[DRY] 将写入 %d 行，跳过 %d 行" % (len(good), skip_n))
        return 0

    # cfg = {k: v for k, v in ecomdb._cfg().items() if k != "charset"}
    # conn = pymysql.connect(charset="utf8mb4", **cfg)
    # with conn.cursor() as cur:
    #     cur.executemany(sql, good)
    # conn.commit()
    write_n = len(good)

    # ---- 5. 自证：写库/月报才强制，核心是金额合计 ----
    # 用 if + return 2，不要用 assert —— python -O 会把 assert 剥掉，校验会静默失效
    # if abs(total - Decimal("93470.31")) > Decimal("0.01"):
    #     print("失败：金额合计不符，差 %s" % (total - Decimal("93470.31")), file=sys.stderr)
    #     return 2

    # ---- 6. 回执行（必须） ----
    print("[done] 读入 %d / 写入 %d / 跳过 %d / 耗时 %.0fs" % (read_n, write_n, skip_n, time.time() - t0))
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:                           # noqa: BLE001
        print("失败：%s" % e, file=sys.stderr)
        sys.exit(1)
