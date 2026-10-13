#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
历法回归测试。

跑法：
    python3 tests/test_calendar.py

覆盖：干支基准点、春节、中秋、闰月边界、十二建星、时辰。
任何一项失败都会以非零码退出。
"""

import os
import sys
from datetime import date

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "scripts"))

from almanac import (  # noqa: E402
    day_pillar, jianchu_index, month_pillar, solar_to_lunar, year_pillar,
)

PASS, FAIL = [], []


def check(label, got, want):
    if got == want:
        PASS.append(label)
    else:
        FAIL.append(f"{label}\n    得到：{got!r}\n    期望：{want!r}")


def lunar(y, m, d):
    ly, lm, ld, leap = solar_to_lunar(y, m, d)
    return (ly, lm, ld, leap)


def main():
    # ── 干支基准点 ────────────────────────────────────────
    check("2000-01-01 应为戊午日", day_pillar(2000, 1, 1)[0], "戊午")
    check("1949-10-01 日柱", day_pillar(1949, 10, 1)[0], "甲子")
    check("2026-10-12 日柱", day_pillar(2026, 10, 12)[0], "己未")

    # ── 年柱 ──────────────────────────────────────────────
    check("2024 年柱", year_pillar(2024)[0], "甲辰")
    check("2025 年柱", year_pillar(2025)[0], "乙巳")
    check("2026 年柱", year_pillar(2026)[0], "丙午")

    # ── 春节（农历正月初一）────────────────────────────────
    for y, m, d in [(2023, 1, 22), (2024, 2, 10), (2025, 1, 29),
                    (2026, 2, 17), (2027, 2, 6)]:
        check(f"{y}-{m:02d}-{d:02d} 应为正月初一", lunar(y, m, d), (y, 1, 1, False))

    # ── 中秋（农历八月十五）────────────────────────────────
    for y, m, d in [(2024, 9, 17), (2025, 10, 6), (2026, 9, 25)]:
        check(f"{y}-{m:02d}-{d:02d} 应为八月十五", lunar(y, m, d), (y, 8, 15, False))

    # ── 闰月 ──────────────────────────────────────────────
    check("2023-03-22 应为闰二月初一", lunar(2023, 3, 22), (2023, 2, 1, True))
    check("2023-03-21 应为二月三十", lunar(2023, 3, 21), (2023, 2, 30, False))
    check("2023-04-20 应为三月初一", lunar(2023, 4, 20), (2023, 3, 1, False))
    check("2025-07-25 应为闰六月初一", lunar(2025, 7, 25), (2025, 6, 1, True))

    # ── 十二建星 ──────────────────────────────────────────
    # 2026-10-12：农历九月，月建戌，日支未 -> (7-10)%12 = 9 = 收
    check("2026-10-12 应为收日", jianchu_index(7, 9), 9)

    # ── 月柱（五虎遁）──────────────────────────────────────
    check("丙年正月应为庚寅", month_pillar(2, 1), "庚寅")
    check("丙年九月应为戊戌", month_pillar(2, 9), "戊戌")
    check("甲年正月应为丙寅", month_pillar(0, 1), "丙寅")

    # ── 自动扫描：连续 4000 天不应抛异常 ────────────────────
    try:
        d = date(2020, 1, 1)
        from datetime import timedelta
        for _ in range(4000):
            solar_to_lunar(d.year, d.month, d.day)
            day_pillar(d.year, d.month, d.day)
            d += timedelta(days=1)
        PASS.append("连续 4000 天换算无异常")
    except Exception as exc:  # pragma: no cover
        FAIL.append(f"连续换算抛异常：{exc!r}")

    # ── 输出 ──────────────────────────────────────────────
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
