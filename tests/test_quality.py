#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
宜忌质量守卫。

跑法：
    python3 tests/test_quality.py

这个文件防的不是「算错」，是「写水」。黄历最容易烂掉的方式，是
每天都说同样几句正确而无用的废话 —— 那样的黄历等于没有。

所以这里把它变成硬性约束：
  1. 同一件事不能既宜又忌
  2. 每天都得有足够内容，不能空
  3. 任何单条出现率不得超过 40%（否则就是水词）
  4. 「常年不变」的内容不许混进每日宜忌
  5. 条目种类不能太少
"""

import os
import sys
from collections import Counter
from datetime import date, timedelta

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "scripts"))

from almanac import ALWAYS, build_context, collect  # noqa: E402

PASS, FAIL = [], []

# 宜忌条目在 HTML 里是竖排短句，超过这个长度就会把版式撑歪、语气也散
MAX_ITEM_LEN = 9


def check(label, ok, detail=""):
    if ok:
        PASS.append(label)
    else:
        FAIL.append(f"{label}\n    {detail}")


def scan(start, days):
    yi_c, ji_c = Counter(), Counter()
    contradict = []
    thin = []
    bad_why = []
    always_leak = []
    too_long = []
    n = 0
    d = start
    for _ in range(days):
        ctx = build_context(d)
        yi, ji = collect(ctx)
        n += 1

        ys = {i["text"] for i in yi}
        js = {i["text"] for i in ji}

        both = ys & js
        if both:
            contradict.append((d, sorted(both)))
        # 除了完全同名，还要抓包含关系：「宜上线」撞「忌季末冲业绩式上线」
        for a in ys:
            for b in js:
                if a != b and (a in b or b in a):
                    contradict.append((d, [a, b]))
        if len(yi) < 3 or len(ji) < 3:
            thin.append((d, len(yi), len(ji)))
        for it in yi + ji:
            # 阈值取 4：中文里「明天是周五」只有 5 个字，但它是条好理由。
            # 这里要拦的是空理由和「待补充」这类退化情况，不是拦短句。
            if not it["why"] or len(it["why"].strip()) < 4:
                bad_why.append((d, it["text"], it["why"]))
            if it["text"] in ALWAYS:
                always_leak.append((d, it["text"]))
            # 宜忌在 HTML 里是竖排短句，超过 9 个字会把版式撑歪
            if len(it["text"]) > MAX_ITEM_LEN:
                too_long.append((d, it["text"]))

        for i in yi:
            yi_c[i["text"]] += 1
        for i in ji:
            ji_c[i["text"]] += 1
        d += timedelta(days=1)

    return n, yi_c, ji_c, contradict, thin, bad_why, always_leak, too_long


def main():
    # 扫一年就够抓住规律性问题；全量扫描在 test_full_range.py 里
    start, days = date(2026, 1, 1), 365
    n, yi_c, ji_c, contradict, thin, bad_why, always_leak, too_long = scan(start, days)

    check(f"{start.year} 年全年无「既宜又忌」",
          not contradict,
          f"{len(contradict)} 天冲突，例如 {contradict[:3]}")

    check("每天至少 3 条宜 / 3 条忌",
          not thin,
          f"{len(thin)} 天太干瘪，例如 {thin[:3]}")

    check(f"条目都 <= {MAX_ITEM_LEN} 字（竖排不撑版）",
          not too_long,
          f"{len(too_long)} 条过长，例如 {too_long[:3]}")

    worst_yi, cy = (yi_c.most_common(1) or [("", 0)])[0]
    worst_ji, cj = (ji_c.most_common(1) or [("", 0)])[0]
    check("单条宜出现率 <= 40%（防废话刷屏）",
          cy / n <= 0.40,
          f"最高是「{worst_yi}」{cy/n:.1%}")
    check("单条忌出现率 <= 40%（防废话刷屏）",
          cj / n <= 0.40,
          f"最高是「{worst_ji}」{cj/n:.1%}")

    check("「常年不变」的内容没有渗进每日宜忌",
          not always_leak,
          f"{len(always_leak)} 处泄漏，例如 {always_leak[:3]}")

    check("每条都带说得出口的理由",
          not bad_why,
          f"{len(bad_why)} 条理由缺失或过短，例如 {bad_why[:3]}")

    check("宜的条目种类 >= 60", len(yi_c) >= 60, f"实际 {len(yi_c)} 种")
    check("忌的条目种类 >= 50", len(ji_c) >= 50, f"实际 {len(ji_c)} 种")

    print(f"扫描 {n} 天（{start} 起）")
    print(f"条目种类：宜 {len(yi_c)} 种 / 忌 {len(ji_c)} 种")
    print(f"最高出现率：宜 {cy/n:.1%}（{worst_yi}）/ 忌 {cj/n:.1%}（{worst_ji}）")
    print()
    print(f"通过 {len(PASS)} 项")
    for p in PASS:
        print(f"  ok  {p}")
    if FAIL:
        print(f"\n失败 {len(FAIL)} 项")
        for f in FAIL:
            print(f"  FAIL  {f}")
        return 1
    print("\n全部通过。")
    return 0


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    raise SystemExit(main())
