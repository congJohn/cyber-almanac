#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
全量区间扫描。

跑法：
    python3 tests/test_full_range.py

把 1900-01-31 到 2100-12-31 的每一天都算一遍，约 7.3 万天、耗时约 30 秒。
这个文件回答的是一个问题：**「覆盖很长时间」是不是真的？**

黄历不是一天天做出来的表格，是一个算法 —— 这里把它全部跑通，
用来证明「任何一天都算得出来」不是一句宣传语。
"""

import os
import sys
from datetime import date, timedelta

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "scripts"))

from almanac import build_context, collect  # noqa: E402

# 农历数据表覆盖 1900–2100，起点取 1900-01-31（正月初一，换算基准日）
START = date(1900, 1, 31)
END = date(2100, 12, 31)

PASS, FAIL = [], []


def check(label, ok, detail=""):
    if ok:
        PASS.append(label)
    else:
        FAIL.append(f"{label}\n    {detail}")


def main():
    errors = []
    bad_lunar = []
    bad_seq = []
    bad_cycle = []
    empty = []
    leap_month_keys = set()
    lunar_years = set()

    n = 0
    prev = None          # (ly, lm, ld, leap)
    prev_didx = None
    d = START

    while d <= END:
        try:
            ctx = build_context(d)
            yi, ji = collect(ctx)
        except Exception as exc:
            errors.append((d, f"{type(exc).__name__}: {exc}"))
            d += timedelta(days=1)
            n += 1
            continue

        ly, lm, ld, leap = ctx["lunar"]
        lunar_years.add(ly)
        if leap:
            leap_month_keys.add((ly, lm))

        if not (1 <= ld <= 30) or not (1 <= lm <= 12):
            bad_lunar.append((d, ctx["lunar"]))

        # 日柱必须严格 60 天一循环，且每天前进一格
        didx = ctx["day_idx"]
        if prev_didx is not None and (prev_didx + 1) % 60 != didx:
            bad_cycle.append((d, prev_didx, didx))
        prev_didx = didx

        # 农历日必须逐日 +1；归 1 时月份必须向前推进（或同一月但切换到闰月）
        if prev is not None:
            ply, plm, pld, pleap = prev
            if ld != pld + 1:
                ok_reset = (ld == 1) and (
                    (lm == plm % 12 + 1 and ly == ply)      # 下个月
                    or (lm == plm and leap != pleap)        # 正常月 / 闰月切换
                    or (ly == ply + 1 and lm == 1)          # 跨农历年
                )
                if not ok_reset:
                    bad_seq.append((d, prev, (ly, lm, ld, leap)))
        prev = (ly, lm, ld, leap)

        if not yi or not ji:
            empty.append(d)

        n += 1
        d += timedelta(days=1)

    check("全区间无异常", not errors, f"{len(errors)} 处，例如 {errors[:3]}")
    check("农历月/日都在合法范围", not bad_lunar, f"{len(bad_lunar)} 处，例如 {bad_lunar[:3]}")
    check("农历日期逐日连续（无跳日/跳月）", not bad_seq, f"{len(bad_seq)} 处，例如 {bad_seq[:3]}")
    check("日柱严格 60 天一循环", not bad_cycle, f"{len(bad_cycle)} 处，例如 {bad_cycle[:3]}")
    check("每一天都算得出宜忌", not empty, f"{len(empty)} 天为空，例如 {empty[:3]}")
    check("覆盖 201 个农历年（1900–2100）", len(lunar_years) == 201,
          f"实际 {len(lunar_years)} 个")
    check("闰月数量在历法合理区间（70–80 个）", 70 <= len(leap_month_keys) <= 80,
          f"实际 {len(leap_month_keys)} 个")

    print(f"扫描 {START} → {END}")
    print(f"共 {n} 天（约 {n/365.2425:.1f} 年）")
    print(f"覆盖农历年 {len(lunar_years)} 个，闰月 {len(leap_month_keys)} 个")
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
