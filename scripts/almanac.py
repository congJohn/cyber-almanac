#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
赛博黄历 · cyber-almanac

把中国老黄历那套壳子，套在今天真正要操心的事上。
宜忌不是抽签抽出来的 —— 从日期里推出来：周几、农历、十二建星、日干，每条都给理由。

用法：
    python3 almanac.py                      看今天
    python3 almanac.py --date 2026-11-11    看任意一天
    python3 almanac.py --week               看这一周
    python3 almanac.py --html p.html        生成可截图的老黄历页面
    python3 almanac.py --json               机器可读
    python3 almanac.py --no-color           关掉颜色（重定向到文件时用）

纯标准库。Python 3.9+。
"""

from __future__ import annotations

import argparse
import html as _html
import json
import sys
from datetime import date, timedelta

VERSION = "1.0.0"

# ─────────────────────────────────────────────────────────────
# 一、农历数据表（1900-2100）
# ─────────────────────────────────────────────────────────────
# 每个整数编码一年：低 4 位是闰月月份（0 表示无闰月），
# 0x10000 位表示闰月是大月（30 天），其余位从高到低依次表示正月到大月/小月。
LUNAR_INFO = [
    0x04bd8, 0x04ae0, 0x0a570, 0x054d5, 0x0d260, 0x0d950, 0x16554, 0x056a0, 0x09ad0, 0x055d2,
    0x04ae0, 0x0a5b6, 0x0a4d0, 0x0d250, 0x1d255, 0x0b540, 0x0d6a0, 0x0ada2, 0x095b0, 0x14977,
    0x04970, 0x0a4b0, 0x0b4b5, 0x06a50, 0x06d40, 0x1ab54, 0x02b60, 0x09570, 0x052f2, 0x04970,
    0x06566, 0x0d4a0, 0x0ea50, 0x06e95, 0x05ad0, 0x02b60, 0x186e3, 0x092e0, 0x1c8d7, 0x0c950,
    0x0d4a0, 0x1d8a6, 0x0b550, 0x056a0, 0x1a5b4, 0x025d0, 0x092d0, 0x0d2b2, 0x0a950, 0x0b557,
    0x06ca0, 0x0b550, 0x15355, 0x04da0, 0x0a5b0, 0x14573, 0x052b0, 0x0a9a8, 0x0e950, 0x06aa0,
    0x0aea6, 0x0ab50, 0x04b60, 0x0aae4, 0x0a570, 0x05260, 0x0f263, 0x0d950, 0x05b57, 0x056a0,
    0x096d0, 0x04dd5, 0x04ad0, 0x0a4d0, 0x0d4d4, 0x0d250, 0x0d558, 0x0b540, 0x0b6a0, 0x195a6,
    0x095b0, 0x049b0, 0x0a974, 0x0a4b0, 0x0b27a, 0x06a50, 0x06d40, 0x0af46, 0x0ab60, 0x09570,
    0x04af5, 0x04970, 0x064b0, 0x074a3, 0x0ea50, 0x06b58, 0x055c0, 0x0ab60, 0x096d5, 0x092e0,
    0x0c960, 0x0d954, 0x0d4a0, 0x0da50, 0x07552, 0x056a0, 0x0abb7, 0x025d0, 0x092d0, 0x0cab5,
    0x0a950, 0x0b4a0, 0x0baa4, 0x0ad50, 0x055d9, 0x04ba0, 0x0a5b0, 0x15176, 0x052b0, 0x0a930,
    0x07954, 0x06aa0, 0x0ad50, 0x05b52, 0x04b60, 0x0a6e6, 0x0a4e0, 0x0d260, 0x0ea65, 0x0d530,
    0x05aa0, 0x076a3, 0x096d0, 0x04afb, 0x04ad0, 0x0a4d0, 0x1d0b6, 0x0d250, 0x0d520, 0x0dd45,
    0x0b5a0, 0x056d0, 0x055b2, 0x049b0, 0x0a577, 0x0a4b0, 0x0aa50, 0x1b255, 0x06d20, 0x0ada0,
    0x14b63, 0x09370, 0x049f8, 0x04970, 0x064b0, 0x168a6, 0x0ea50, 0x06b20, 0x1a6c4, 0x0aae0,
    0x0a2e0, 0x0d2e3, 0x0c960, 0x0d557, 0x0d4a0, 0x0da50, 0x05d55, 0x056a0, 0x0a6d0, 0x055d4,
    0x052d0, 0x0a9b8, 0x0a950, 0x0b4a0, 0x0b6a6, 0x0ad50, 0x055a0, 0x0aba4, 0x0a5b0, 0x052b0,
    0x0b273, 0x06930, 0x07337, 0x06aa0, 0x0ad50, 0x14b55, 0x04b60, 0x0a570, 0x054e4, 0x0d160,
    0x0e968, 0x0d520, 0x0daa0, 0x16aa6, 0x056d0, 0x04ae0, 0x0a9d4, 0x0a2d0, 0x0d150, 0x0f252,
    0x0d520,
]

GAN = "甲乙丙丁戊己庚辛壬癸"
ZHI = "子丑寅卯辰巳午未申酉戌亥"
ANIMALS = "鼠牛虎兔龙蛇马羊猴鸡狗猪"
ZHI_ANIMALS = {z: a for z, a in zip(ZHI, ANIMALS)}
CN_DIGITS = "〇一二三四五六七八九"
CN_DAYS = "初一 初二 初三 初四 初五 初六 初七 初八 初九 初十 十一 十二 十三 十四 十五 " \
          "十六 十七 十八 十九 二十 廿一 廿二 廿三 廿四 廿五 廿六 廿七 廿八 廿九 三十".split()
CN_MONTHS = "正二三四五六七八九十冬腊"
BASE = date(1900, 1, 31)

# 六十甲子纳音，每两个甲子共用一个
NAYIN = [
    "海中金", "炉中火", "大林木", "路旁土", "剑锋金", "山头火", "涧下水", "城头土", "白蜡金",
    "杨柳木", "泉中水", "屋上土", "霹雳火", "松柏木", "长流水", "砂中金", "山下火", "平地木",
    "壁上土", "金箔金", "覆灯火", "天河水", "大驿土", "钗钏金", "桑柘木", "大溪水", "沙中土",
    "天上火", "石榴木", "大海水",
]

# 十二建星：全称建除十二神，老黄历里决定「今天适合开还是收」
JIANCHU = ["建", "除", "满", "平", "定", "执", "破", "危", "成", "收", "开", "闭"]
JIANCHU_CYBER = {
    "建": ("万事之始", "适合开新坑。今天起的项目，后面不会怪你没提醒"),
    "除": ("除旧布新", "适合删代码、退订阅。今天删掉的东西，你大概率不会再想起来"),
    "满": ("日中则昃", "适合提交、适合合并。东西攒到今天已经够了，再攒就溢出来"),
    "平": ("平常而已", "适合摸鱼。今天不适合做大决定，也不适合逼自己"),
    "定": ("定而后安", "适合写文档、拍方案、把来回扯了三天的需求定死"),
    "执": ("执守有成", "适合坚持那件你想放弃的事。今天放弃，明天还得重来"),
    "破": ("大耗之日", "今天什么都别动。忌上线、忌动生产、忌改配置，宜复盘事故、宜躺平"),
    "危": ("危中求安", "不适合冒任何险。今天赌赢不算本事，赌输代价翻倍"),
    "成": ("诸事可成", "适合上线、交付、表白。今天成的事，后面不容易翻"),
    "收": ("收成之时", "适合收尾、催款、要回欠你的。今天开口，对方不太好意思拒绝"),
    "开": ("开张纳采", "适合开会、开新需求、开口谈条件。今天说的话，别人听得进去"),
    "闭": ("闭塞不通", "忌发消息、忌提 PR、忌在群里表态。今天闭嘴比说话值钱"),
}

# 彭祖百忌的赛博版：按日干
PENGZU = {
    "甲": ("不开新账", "今天记的账、囤的货，最后都是废品"),
    "乙": ("不起新项目", "今天种下去的东西，长不出来"),
    "丙": ("不动基础设施", "今天碰机房和部署脚本，必出事"),
    "丁": ("不改头像", "今天换的东西，你会在三天内后悔"),
    "戊": ("不接锅", "今天别人递过来的「机会」，都是坑"),
    "己": ("不签合同", "今天按的手印、点的同意，后面会咬你"),
    "庚": ("不做大重构", "今天织了半天，织不出东西"),
    "辛": ("不尝鲜", "今天上的新框架、新版本，会给你颜色看"),
    "壬": ("不往生产灌东西", "今天放进去的，会自己长腿跑出来"),
    "癸": ("不与人争", "今天开口吵架、提意见，你说不过人家"),
}

# 十二时辰
HOURS = [
    ("子", "23:00-00:59", "忌醒着", "这个点做的决定，明天全部要重做"),
    ("丑", "01:00-02:59", "忌醒着", "没什么好说的"),
    ("寅", "03:00-04:59", "忌醒着", "这会儿还醒着，就是白天欠的债"),
    ("卯", "05:00-06:59", "宜起床", "醒了就起。躺着刷手机是最贵的睡法"),
    ("辰", "07:00-08:59", "宜通勤", "路上听的、看的，会占掉一天里最好的记性"),
    ("巳", "09:00-10:59", "宜干最难的活", "一天里脑子最清楚的两小时，别拿去回消息"),
    ("午", "11:00-12:59", "宜吃饭", "好好吃。边吃边开会，两件事都没做好"),
    ("未", "13:00-14:59", "宜沟通", "刚吃完饭本来也想不了事，拿来做沟通正好"),
    ("申", "15:00-16:59", "宜写代码收尾", "下午这一截适合把早上开的头收干净"),
    ("酉", "17:00-18:59", "宜收工忌上线", "这个点上线，出事就是你自己扛"),
    ("戌", "19:00-20:59", "忌加班", "这段时间的效率大约是白天的三分之一"),
    ("亥", "21:00-22:59", "宜放下", "别再看一眼 issue，那一眼通常是两小时"),
]

XINGZUO = [
    (1, 20, "水瓶座", "摩羯座"), (2, 19, "双鱼座", "水瓶座"), (3, 21, "白羊座", "双鱼座"),
    (4, 20, "金牛座", "白羊座"), (5, 21, "双子座", "金牛座"), (6, 22, "巨蟹座", "双子座"),
    (7, 23, "狮子座", "巨蟹座"), (8, 23, "处女座", "狮子座"), (9, 23, "天秤座", "处女座"),
    (10, 24, "天蝎座", "天秤座"), (11, 23, "射手座", "天蝎座"), (12, 22, "摩羯座", "射手座"),
]

# 今日一签
SIGNS = [
    "你今天省下的那二十分钟，下周三会连本带利还给你。",
    "没有一个 bug 是被群消息修好的。",
    "先做那件你一直在躲的。做完你会发现它只有十分钟。",
    "今天不适合做决定，适合先睡一觉。",
    "你上次说「下周一定」的那件事，现在怎么样了？",
    "能跑就行。先让它跑起来。",
    "「我最后再改一处」——这句话之后平均还要改六处。",
    "这件事周五做会出事，那它今天做也可能出事，只是今天有人接电话。",
    "备份。现在。别问为什么。",
    "今天要开的那个会，不去的成本比去的低。",
    "别在情绪里发消息。存草稿，明早再看。",
    "你不是没时间。你是把时间给了通知栏。",
    "能一句话说清的事，别写三句。",
    "先写测试，或者先承认你不打算写。",
    "你不是在等灵感，你是在等一个不用开始的借口。",
    "把那个文件关掉。你已经盯着它四十分钟了。",
    "今天适合说「不」。说一次，你就知道没那么难。",
    "别优化还没坏的东西。",
    "你担心的那件事，九成不会发生。剩下一成，担心也拦不住。",
    "先把桌子收干净，再开始。",
    "今天就发那条消息吧。你已经写了三遍了。",
    "别人的节奏不是你的进度条。",
    "删掉比加上更难，也更有用。",
    "你把「学点新东西」当成了拖延的借口，这事你自己知道。",
    "活是干不完的。挑最重要的那件做完，今天就算赢了。",
    "你不会记得今天加班做了什么，但会记得又没睡好。",
    "先跑通，再跑快。",
    "今天适合把一件事做完，而不是每件事都推进一步。",
    "让子弹飞一会儿。明天再看这封邮件，你会庆幸自己没发。",
    "把「回头再说」换成「现在两分钟」。",
    "你不是缺乏自律，你是目标定太大了。切小一点。",
    "今天不要碰那台正在跑的服务器。",
    "想清楚再动手，比动手之后再想清楚便宜十倍。",
    "有疑问就问。猜错的代价，比问一句高得多。",
    "把这件事写下来。写下来你就知道它到底有多小。",
    "今天最好的投资是睡够七小时。",
]

# 赛博冲煞：老黄历说「冲鼠煞北」，我们说这个
CHONG_POOL = [
    "产品经理", "甲方", "需求变更", "线上环境", "钉钉群", "周报", "季度 OKR", "晨会",
    "团建", "报销流程", "代码评审", "打卡机", "会议室", "临时通知", "联调", "灰度发布",
]
SHA_POOL = ["会议室东侧", "工位正南", "茶水间", "电梯口", "线上环境", "项目群", "五号会议室"]

# ─────────────────────────────────────────────────────────────
# 二、历法核心
# ─────────────────────────────────────────────────────────────


def _leap_month(y: int) -> int:
    return LUNAR_INFO[y - 1900] & 0xF


def _leap_days(y: int) -> int:
    if _leap_month(y):
        return 30 if (LUNAR_INFO[y - 1900] & 0x10000) else 29
    return 0


def _month_days(y: int, m: int) -> int:
    return 30 if (LUNAR_INFO[y - 1900] & (0x10000 >> m)) else 29


def _lunar_year_days(y: int) -> int:
    res = 348
    i = 0x8000
    while i > 0x8:
        if LUNAR_INFO[y - 1900] & i:
            res += 1
        i >>= 1
    return res + _leap_days(y)


def solar_to_lunar(y: int, m: int, d: int):
    offset = (date(y, m, d) - BASE).days
    ly = 1900
    while ly < 2101:
        yd = _lunar_year_days(ly)
        if offset < yd:
            break
        offset -= yd
        ly += 1
    leap = _leap_month(ly)
    is_leap = False
    lm = 1
    while lm < 13:
        if leap > 0 and lm == leap + 1 and not is_leap:
            days = _leap_days(ly)
            is_leap = True
            lm -= 1
        else:
            days = _month_days(ly, lm)
            is_leap = False
        if offset < days:
            break
        offset -= days
        lm += 1
    return ly, lm, offset + 1, is_leap


def _jdn(y: int, m: int, d: int) -> int:
    a = (14 - m) // 12
    yy = y + 4800 - a
    mm = m + 12 * a - 3
    return d + (153 * mm + 2) // 5 + 365 * yy + yy // 4 - yy // 100 + yy // 400 - 32045


def day_pillar(y: int, m: int, d: int):
    """返回 (干支字符串, 0-59 序号)。用儒略日推，2000-01-01 = 戊午日。"""
    idx = (_jdn(y, m, d) + 49) % 60
    return GAN[idx % 10] + ZHI[idx % 12], idx


def year_pillar(ly: int):
    idx = (ly - 4) % 60
    return GAN[idx % 10] + ZHI[idx % 12], idx


def month_pillar(year_gan_i: int, lunar_month: int):
    """五虎遁：甲己之年丙作首。月支按农历月起寅（非节气月，注意这个简化）。"""
    first_gan = (year_gan_i % 5) * 2 + 2
    gan_i = (first_gan + lunar_month - 1) % 10
    zhi_i = (2 + lunar_month - 1) % 12
    return GAN[gan_i] + ZHI[zhi_i]


def jianchu_index(day_zhi_i: int, lunar_month: int) -> int:
    """十二建星 = 日支 与 月建 的差。月建按农历月起寅。"""
    month_zhi = (lunar_month + 1) % 12
    return (day_zhi_i - month_zhi) % 12


def xingzuo_of(m: int, d: int) -> str:
    for mm, dd, cur, prev in XINGZUO:
        if m == mm:
            return cur if d >= dd else prev
    return "摩羯座"


def cn_year(ly: int) -> str:
    return "".join(CN_DIGITS[int(c)] for c in str(ly))


def cn_month(lm: int, is_leap: bool) -> str:
    return ("闰" if is_leap else "") + CN_MONTHS[lm - 1] + "月"


def cn_day(ld: int) -> str:
    return CN_DAYS[ld - 1]


# ─────────────────────────────────────────────────────────────
# 三、宜忌规则引擎
# ─────────────────────────────────────────────────────────────
# 每条规则：条件成立就往宜或忌里加条目。条目 = (事项, 理由, 权重)

def _build_rules():
    R = []

    def rule(name, when):
        def deco(fn):
            R.append({"name": name, "when": when, "fn": fn})
            return fn
        return deco

    # ── 星期 ──────────────────────────────────────────────
    @rule("周一", lambda c: c["wd"] == 0)
    def _(c):
        return (
            [("先列本周要交付的", "今天想清楚，周三能救命", 6),
             ("给上周的自己善后", "上周五走得急，没给你留说明书", 5)],
            [("一上班就埋头开干", "先花二十分钟看看上周收到了什么尾", 6),
             ("把重要会议排在上午", "全公司都在消化周末，没人真在听", 5)],
        )

    @rule("周二", lambda c: c["wd"] == 1)
    def _(c):
        return (
            [("干最难的活", "一周里干扰最少的一天，别浪费在回消息上", 7),
             ("提需求", "周一太早，周五太晚，今天是对方最可能点头的窗口", 6)],
            [("下午排满会", "把最好的一段时间切碎了", 4)],
        )

    @rule("周三", lambda c: c["wd"] == 2)
    def _(c):
        return (
            [("把手上的活推进一步", "卡在一半的东西今天推一把，周内还看得到结果", 6),
             ("摸鱼", "统计上这是一周士气最低的一天，硬撑效率更低", 7)],
            [("做重大决定", "周三的你只想快点结束，不想清楚", 6)],
        )

    @rule("周四", lambda c: c["wd"] == 3)
    def _(c):
        return (
            [("上线", "出了事还有明天一整天可以救", 7),
             ("请年假", "连着周末能凑四天，而且周五的会通常会取消", 5)],
            [("把发版推到明天", "明天是周五", 5)],
        )

    @rule("周五", lambda c: c["wd"] == 4)
    def _(c):
        return (
            [("写周报", "写得好不好另说，今天写最省事", 6),
             ("收尾清理", "把桌面清干净，周一回来的你会好受", 6)],
            [("上线", "出事你得赔上周末，而且没人会感激你", 10),
             ("改配置、动数据库", "周末没人值班，你改的东西会自己长腿跑", 9),
             ("四点后提小改动", "小改动是最大的改动", 8),
             ("删库", "哪天都忌，今天就别试探了", 8)],
        )

    @rule("周六", lambda c: c["wd"] == 5)
    def _(c):
        return (
            [("睡到自然醒", "这是你今天最该做的事", 7),
             ("把拖最久的小事做完", "它占的心理空间，比实际工作量大得多", 6)],
            [("打开 IDE", "你说就看一眼，我们都知道那是多久", 6),
             ("点开工作群", "看了也干不了，只会多一件心事", 7)],
        )

    @rule("周日", lambda c: c["wd"] == 6)
    def _(c):
        return (
            [("把明天先定下来", "省掉明早的三十分钟决策", 6)],
            [("晚上想周一的事", "想了也没用，只会少睡两小时", 7),
             ("下午补觉超过两小时", "晚上你就知道了", 5)],
        )

    # ── 日期数 ────────────────────────────────────────────
    @rule("月初一号", lambda c: c["dd"] == 1)
    def _(c):
        return ([("立个 flag", "一个月里唯一还愿意相信自己的时刻", 5)], [])

    @rule("发薪窗口", lambda c: 9 <= c["dd"] <= 11)
    def _(c):
        return (
            [("看工资条", "少了就说，不说就永远少", 6)],
            [("当天就下单", "今天的购物车里，一周后有八成会被退货", 6)],
        )

    @rule("月中十五", lambda c: c["dd"] == 15)
    def _(c):
        return (
            [("复盘这半个月", "现在看清还来得及，月末就只剩叹气", 5)],
            [("查信用卡账单", "如果你刚发的是工资，就别这么做", 4)],
        )

    @rule("月初三日", lambda c: 2 <= c["dd"] <= 3)
    def _(c):
        return ([("写下这个月想做的", "写在纸上的才叫计划", 5)], [])

    @rule("月末最后一天", lambda c: c["days_left"] == 0)
    def _(c):
        return (
            [("退掉没用过的订阅", "明天就扣费了", 8),
             ("清收件箱和下载夹", "新的一个月从干净的地方开始", 5)],
            [("开新坑", "你会在下个月的今天来还这笔债", 7)],
        )

    @rule("月末三天", lambda c: 1 <= c["days_left"] <= 2)
    def _(c):
        return ([("把手上的事收个尾", "留到明年你会更不想做", 5)], [])

    @rule("十三号", lambda c: c["dd"] == 13)
    def _(c):
        return ([],
                [("今天什么都别信", "包括这一条", 3)])

    @rule("季末", lambda c: c["quarter_end"])
    def _(c):
        return ([("把季度的坑填一填", "下个季度开始，没人愿意回头擦屁股", 6)],
                [("季末冲业绩式上线", "冲出来的东西，下个月就要还", 7)])

    # ── 十二建星 ──────────────────────────────────────────
    @rule("建日", lambda c: c["jianchu"] == 0)
    def _(c):
        return ([("开新东西", "今天起的头，后面会走得顺一点", 7)], [])

    @rule("除日", lambda c: c["jianchu"] == 1)
    def _(c):
        return ([("删代码、退订阅", "今天删掉的，你大概率不会再想起来", 8)], [])

    @rule("满日", lambda c: c["jianchu"] == 2)
    def _(c):
        return ([("提交、合并、发版", "东西攒到今天够了，再攒就溢出来", 7)], [])

    @rule("平日", lambda c: c["jianchu"] == 3)
    def _(c):
        return ([("摸鱼", "今天不是发力的日子", 6)],
                [("做重大决定", "平常心不等于想清楚了", 5)])

    @rule("定日", lambda c: c["jianchu"] == 4)
    def _(c):
        return ([("写文档、拍方案", "来回扯了三天的事，今天定死", 8)], [])

    @rule("执日", lambda c: c["jianchu"] == 5)
    def _(c):
        return ([("坚持那件想放弃的事", "今天放弃，明天还得重来", 6)], [])

    @rule("破日", lambda c: c["jianchu"] == 6)
    def _(c):
        return ([("复盘事故", "今天只适合看已经发生的", 6),
                 ("躺平", "今天不做事，就是做事", 7)],
                [("上线", "破日上线，等于给自己找活", 10),
                 ("动生产环境", "今天动的东西都会出问题", 10),
                 ("改配置", "改完就忘改哪儿了", 8)])

    @rule("危日", lambda c: c["jianchu"] == 7)
    def _(c):
        return ([],
                [("冒任何险", "今天赌赢不算本事，赌输代价翻倍", 8),
                 ("上线", "挑个别的日子", 8)])

    @rule("成日", lambda c: c["jianchu"] == 8)
    def _(c):
        return ([("上线、交付", "今天成的事，后面不容易翻", 9),
                 ("说那句一直没说的话", "成日，适合开口", 6)], [])

    @rule("收日", lambda c: c["jianchu"] == 9)
    def _(c):
        return ([("把开了头的收干净", "留着的尾巴，下周还得再捡一次", 8),
                 ("催款、要回欠你的", "今天开口，对方不太好意思拒绝", 7)], [])

    @rule("开日", lambda c: c["jianchu"] == 10)
    def _(c):
        return ([("开会、开新需求", "今天说的话，别人听得进去", 7),
                 ("开口谈条件", "开日谈条件，是挑日子谈的", 8)], [])

    @rule("闭日", lambda c: c["jianchu"] == 11)
    def _(c):
        return ([("闭嘴、关通知", "今天沉默比表达划算", 6)],
                [("发消息", "今天发的消息，明天你会想撤回", 8),
                 ("提 PR", "审的人今天心情不对", 7),
                 ("在群里表态", "今天表态，等于给自己挖坑", 7)])

    # ── 彭祖百忌（日干）────────────────────────────────────
    def pengzu_rule(gan_name, text, why):
        @rule("彭祖百忌·" + gan_name, lambda c, g=gan_name: c["day_ganzhi"][0] == g)
        def _(c):
            return ([], [(text, why, 7)])
    for g, (t, w) in PENGZU.items():
        pengzu_rule(g, t, w)

    # ── 农历 ──────────────────────────────────────────────
    @rule("农历初一十五", lambda c: c["lunar"][2] in (1, 15))
    def _(c):
        return ([("给服务器上炷香", "传统上今天是敬神的日子，服务器现在就是你的神", 6)], [])

    @rule("农历七月", lambda c: c["lunar"][1] == 7)
    def _(c):
        return ([], [("上线", "农历七月，传统上不适合开张", 4)])

    @rule("腊月", lambda c: c["lunar"][1] == 12)
    def _(c):
        return ([("把今年的烂尾清一清", "过年之前，你还有机会把欠的还完", 6)], [])

    # ── 农历节令 ──────────────────────────────────────────
    @rule("正月初五", lambda c: c["lunar"][1] == 1 and c["lunar"][2] == 5 and not c["lunar"][3])
    def _(c):
        return ([("把该扔的扔一扔", "初五送穷，规矩上今天可以动扫帚了", 6)], [])

    @rule("开年第一周", lambda c: c["lunar"][1] == 1 and 6 <= c["lunar"][2] <= 12 and not c["lunar"][3])
    def _(c):
        return ([("目标只留一个", "开年列一长串，年底一个都不剩", 7),
                 ("回完没回的新年祝福", "现在回还来得及，拖到正月十五就算了", 5)],
                [("别把旧账带进今年", "它不会自己消失，只会长个", 6)])

    @rule("元宵", lambda c: c["lunar"][1] == 1 and c["lunar"][2] == 15)
    def _(c):
        return ([("给自己一个晚上", "年过到这天，才算过完", 7)],
                [("今天加班到忘了日子", "这个需求三天后没人记得，这晚你记得", 6)])

    @rule("龙抬头", lambda c: c["lunar"][1] == 2 and c["lunar"][2] == 2 and not c["lunar"][3])
    def _(c):
        return ([("去理个发", "排队也认了，一年里唯一理直气壮的一天", 5),
                 ("接着做停了的那件", "抬头的日子，适合起步", 6)], [])

    @rule("端午", lambda c: c["lunar"][1] == 5 and c["lunar"][2] == 5)
    def _(c):
        return ([("吃个粽子，歇半天", "假是给你用的，不是给你补班的", 7)],
                [("这几天提大需求", "没人真的在状态，包括提的人", 6)])

    @rule("七夕", lambda c: c["lunar"][1] == 7 and c["lunar"][2] == 7)
    def _(c):
        return ([("早点收工", "今晚留给谁，你自己清楚", 7),
                 ("说那句没说的谢谢", "不必等节日，但今天最容易说", 5)], [])

    @rule("中元", lambda c: c["lunar"][1] == 7 and c["lunar"][2] == 15)
    def _(c):
        return ([], [("深夜一个人加班", "传统上今天不熬夜，就当借个由头", 6)])

    @rule("中秋", lambda c: c["lunar"][1] == 8 and c["lunar"][2] == 15)
    def _(c):
        return ([("回家吃饭", "听着老套，但你算算一年回去几次", 8),
                 ("给远方的人发条消息", "不用长，一句就够", 6)], [])

    @rule("重阳", lambda c: c["lunar"][1] == 9 and c["lunar"][2] == 9)
    def _(c):
        return ([("给长辈打个电话", "重阳就该干这件事，别的都是借口", 8),
                 ("出门走二十分钟", "登高不必，走走出汗算数", 5)], [])

    @rule("腊八", lambda c: c["lunar"][1] == 12 and c["lunar"][2] == 8)
    def _(c):
        return ([("开始收尾", "过了腊八就是年，剩下的日子都在收拾", 6)],
                [("这时候再开新项目", "你会在春节前把它挂在那儿，一动不动", 7)])

    @rule("小年", lambda c: c["lunar"][1] == 12 and c["lunar"][2] == 23 and not c["lunar"][3])
    def _(c):
        return ([("把今年欠的消息回完", "过年见面要打招呼的人，先在这几天清掉", 6)], [])

    @rule("除夕", lambda c: c["lunar"][1] == 12 and c["lunar"][2] >= 29 and not c["lunar"][3])
    def _(c):
        return ([("今天不干活", "一年就这一天，理由不用更充分", 9)],
                [("在群里抢着表忠心", "没人记得，你自己会后悔", 7)])

    # ── 公历节点 ──────────────────────────────────────────
    @rule("元旦", lambda c: c["m"] == 1 and c["dd"] == 1)
    def _(c):
        return ([("今年想干的三件事", "三件就够，三十件等于没写", 8),
                 ("清空上一年的收件箱", "躺在那儿的事，你其实早不打算做了", 6)],
                [("立宏大的年度计划", "去年那份还开着，一个字没动", 7)])

    @rule("跨年前夜", lambda c: c["m"] == 12 and c["dd"] == 31)
    def _(c):
        return ([("把今年做过的列一遍", "你会发现自己不是没干成，是忘了", 8)],
                [("今晚定明年的计划", "今晚定的，1 月 3 号就废了", 6)])

    @rule("愚人节", lambda c: c["m"] == 4 and c["dd"] == 1)
    def _(c):
        return ([("开一个不伤人的玩笑", "这个难度比你以为的高", 4)],
                [("今天发公告、发通知", "没人会当真，包括你自己", 8)])

    @rule("长假头几天", lambda c: (c["m"] == 10 and c["dd"] <= 3) or (c["m"] == 5 and c["dd"] <= 3))
    def _(c):
        return ([("把手机调静音", "这不叫失联，这叫放假", 7)],
                [("去最热门的那个地方", "你排的队，够看完一本小说", 6)])

    @rule("购物节", lambda c: (c["m"] == 11 and c["dd"] == 11) or (c["m"] == 6 and c["dd"] == 18))
    def _(c):
        return ([("想买的先放一天再说", "热乎劲过了，你会发现一半用不上", 8),
                 ("先列清单再看价格", "反着来就是被推着走", 6)],
                [("零点准时付款", "省下的钱，会在退货时花回来", 6)])

    @rule("购物节前夜", lambda c: (c["m"] == 11 and c["dd"] == 10) or (c["m"] == 6 and c["dd"] == 17))
    def _(c):
        return ([], [("把购物车加满", "加满了，明天你只会照着它付款", 7)])

    @rule("金三银四", lambda c: (c["m"] == 3 and 5 <= c["dd"] <= 20) or (c["m"] == 4 and 5 <= c["dd"] <= 20))
    def _(c):
        return ([("更新一下简历", "不一定要走，但得知道自己现在值多少", 5)],
                [("因为焦虑而换工作", "现在这个坑，多半换个形状在新公司等你", 6)])

    @rule("开学季", lambda c: c["m"] == 9 and c["dd"] <= 5)
    def _(c):
        return ([("把作息调回来", "夏天欠的觉，现在开始还利息", 6)], [])

    @rule("年末", lambda c: c["m"] == 12 and c["dd"] >= 15)
    def _(c):
        return ([("把这年干成的列一列", "谈绩效前你会庆幸自己记了", 8)],
                [("年底硬赶一个上线", "赶出来的东西，一月会回来找你", 7)])

    @rule("盛夏", lambda c: c["m"] == 7 and 10 <= c["dd"] <= 25)
    def _(c):
        return ([("费脑子的会挪上午", "下午的你会变成另一个人", 5)],
                [("在午后拍板", "你自己也知道那不叫决定", 5)])

    @rule("换季", lambda c: c["m"] in (3, 9) and 4 <= c["dd"] <= 8)
    def _(c):
        return ([("清一次衣柜", "换季的时候扔，最下得去手", 5),
                 ("做一次常规体检", "换季最容易忽略身体", 4)], [])

    @rule("逢十", lambda c: c["dd"] % 10 == 0)
    def _(c):
        return ([("把这十天的事过一遍", "十天看一次，不至于积成山", 5)], [])

    # ── 日支／旬 ──────────────────────────────────────────
    @rule("日支为子午", lambda c: c["day_zhi_i"] in (0, 6))
    def _(c):
        return ([], [("今天硬扛", "冲得最厉害的两天之一，能挪就挪", 5)])

    return R


RULES = _build_rules()

# 常年不变的三条。它们不该去占「今日宜忌」的位置 —— 天天出现等于没信息量。
# 所以单独抽出来，在输出里固定放一行。
ALWAYS = [
    "密钥不进仓库",
    "生产环境不是试验田",
    "备份不用等出事",
]

# 兜底池：某天命中太少时用来补位。按日子轮换取，所以不会天天长一个样。
FALLBACK_YI = [
    ("整理一下收藏夹", "存的时候都想着会看，之后再没打开过"),
    ("把桌面文件归位", "桌面是心里的投影"),
    ("删掉三个没用的应用", "它们推送的消息，你一次都没点开"),
    ("处理待办里最老的", "它在列表里躺了一个月，这件事本身就是信号"),
    ("联系一个老朋友", "不用有事，问声好就行"),
    ("清一遍手机相册", "你真的不需要那七百张截图"),
    ("好好吃顿饭，不看屏", "这一条你今天就能做到"),
    ("换掉用久了的密码", "顺手的事，拖了很久了"),
    ("退掉几个订阅邮件", "你没在读，只是不好意思退"),
    ("早睡半小时", "不用一小时，半小时就够"),
    ("先找齐明天要用的", "省掉早晨最烦的那十分钟"),
    ("泡杯茶，空十分钟", "这不叫浪费"),
    ("别再「回头再说」", "回头从来没来过"),
    ("常用链接收进书签", "找它的时间，比整理它长"),
    ("拒掉不想去的会", "理由可以很简单"),
]

FALLBACK_JI = [
    ("边吃饭边回消息", "两件都没做好，饭也不香"),
    ("把决定拖到临睡前", "那个点的你不适合拍板"),
    ("只回一个「收到」", "对方要的不是收到，是结论"),
    ("顺手改个「小地方」", "小地方往往连着大地方"),
    ("在饿的时候做选择", "饿着的人做不出好决定，这是有实验的"),
    ("拿「我很忙」当理由", "忙不忙是结果，不是解释"),
    ("情绪最差时发消息", "写完放十分钟，你会删掉一半"),
    ("把重要的事排在最后", "它永远不会轮到自己"),
    ("连续盯屏两小时", "站起来走两步，比再刷十分钟管用"),
    ("为了省事跳过检查", "省下的两分钟，事后要还两小时"),
    ("在没想清楚时先答应", "答应只要一秒，反悔要一个月"),
    ("别老说回头请你吃饭", "这句话你说过很多次了"),
]


def _fill(pool, need, seed, used):
    """从兜底池里按日子轮换取 need 条，避免补位内容天天重复。"""
    out = []
    if need <= 0 or not pool:
        return out
    n = len(pool)
    start = seed % n
    for i in range(n):
        t, w = pool[(start + i) % n]
        if t in used:
            continue
        used.add(t)
        out.append({"text": t, "why": w, "w": 1, "from": "兜底"})
        if len(out) >= need:
            break
    return out


def build_context(d: date) -> dict:
    y, m, dd = d.year, d.month, d.day
    ly, lm, ld, is_leap = solar_to_lunar(y, m, dd)
    dgz, didx = day_pillar(y, m, dd)
    ygz, yidx = year_pillar(ly)
    mgz = month_pillar(yidx % 10, lm)
    first = date(y, m, 1)
    nxt = date(y + (m == 12), (m % 12) + 1, 1)
    days_in_month = (nxt - first).days
    ctx = {
        "date": d,
        "y": y, "m": m, "dd": dd,
        "wd": d.weekday(),
        "is_weekend": d.weekday() >= 5,
        "lunar": (ly, lm, ld, is_leap),
        "day_ganzhi": dgz,
        "day_gan_i": didx % 10,
        "day_zhi_i": didx % 12,
        "day_idx": didx,
        "year_ganzhi": ygz,
        "month_ganzhi": mgz,
        "jianchu": jianchu_index(didx % 12, lm),
        "nayin": NAYIN[didx // 2],
        "xingzuo": xingzuo_of(m, dd),
        "days_in_month": days_in_month,
        "days_left": days_in_month - dd,
        "quarter_end": m in (3, 6, 9, 12) and (days_in_month - dd) <= 2,
    }
    return ctx


def collect(ctx: dict):
    yi, ji = [], []
    for r in RULES:
        try:
            if not r["when"](ctx):
                continue
            y_items, j_items = r["fn"](ctx)
        except Exception:
            continue
        for t, w, wt in y_items:
            yi.append({"text": t, "why": w, "w": wt, "from": r["name"]})
        for t, w, wt in j_items:
            ji.append({"text": t, "why": w, "w": wt, "from": r["name"]})

    # 同名条目只留权重最高的那条
    def best(items):
        d = {}
        for it in items:
            k = it["text"]
            if k not in d or it["w"] > d[k]["w"]:
                d[k] = it
        return d

    yb, jb = best(yi), best(ji)

    # 仲裁：同一件事不能既「宜」又「忌」。
    # 两条规则各自命中时会撞车 —— 比如周四「宜上线」撞上月末「忌上线」，
    # 或者「宜上线」撞上「忌季末冲业绩式上线」。
    # 所以判重不能只看完全相同，还要看包含关系。
    # 权重高的赢；平手时「忌」赢 —— 保守比激进划算。
    for ky in sorted(yb, key=lambda k: -yb[k]["w"]):
        if ky not in yb:
            continue
        for kj in sorted(jb, key=lambda k: -jb[k]["w"]):
            if kj not in jb:
                continue
            if ky in kj or kj in ky:
                if yb[ky]["w"] > jb[kj]["w"]:
                    del jb[kj]          # 宜赢，删忌
                else:
                    del yb[ky]          # 忌赢（含平手），这条宜作废
                    break

    def pick(items, cap):
        seen, out = set(), []
        for it in sorted(items, key=lambda x: -x["w"]):
            if it["text"] in seen:
                continue
            seen.add(it["text"])
            out.append(it)
            if len(out) >= cap:
                break
        return out

    yi_out = pick(list(yb.values()), 8)
    ji_out = pick(list(jb.values()), 8)

    # 兜底：命中太少的日子补到至少 4 条，免得出现干瘪的一天。
    # 按日子轮换取，所以补位内容不会天天长一个样。
    # 两边共用同一个 used，保证补位也不会撞成自相矛盾。
    seed = ctx["day_idx"] * 7 + ctx["m"] * 3 + ctx["dd"]
    used = {i["text"] for i in yi_out} | {i["text"] for i in ji_out}
    yi_out += _fill(FALLBACK_YI, 4 - len(yi_out), seed, used)
    ji_out += _fill(FALLBACK_JI, 4 - len(ji_out), seed + 5, used)

    return yi_out, ji_out


# ─────────────────────────────────────────────────────────────
# 四、指数
# ─────────────────────────────────────────────────────────────

def indices(ctx: dict) -> list:
    wd = ctx["wd"]
    jc = ctx["jianchu"]
    out = []

    moyu = 40
    moyu += {0: -20, 1: -10, 2: 25, 3: 0, 4: 20, 5: 45, 6: 35}[wd]
    if jc in (3, 6, 11):
        moyu += 15
    if jc in (0, 8, 10):
        moyu -= 15
    out.append(("摸鱼", moyu))

    shangxian = 70
    shangxian += {0: -10, 1: 5, 2: 5, 3: 20, 4: -55, 5: -60, 6: -50}[wd]
    if jc == 8:
        shangxian += 20
    if jc in (6, 7):
        shangxian -= 40
    if ctx["days_left"] == 0:
        shangxian -= 15
    out.append(("上线", shangxian))

    tanpan = 45
    if jc == 10:
        tanpan += 25
    if jc in (9, 8):
        tanpan += 15
    if jc in (6, 7, 11):
        tanpan -= 25
    if 9 <= ctx["dd"] <= 11:
        tanpan -= 20
    out.append(("谈加薪", tanpan))

    zaoshui = 50
    zaoshui += {0: -10, 1: -5, 2: 0, 3: 5, 4: 15, 5: 25, 6: 5}[wd]
    if jc == 6:
        zaoshui += 10
    out.append(("早睡", zaoshui))

    return [(n, max(0, min(100, v))) for n, v in out]


def bar(v: int, width: int = 10) -> str:
    filled = int(round(v / 100 * width))
    return "█" * filled + "░" * (width - filled)


# ─────────────────────────────────────────────────────────────
# 五、终端渲染
# ─────────────────────────────────────────────────────────────

WEEK_CN = "一二三四五六日"
ANSI = {
    "red": "\033[31m", "green": "\033[32m", "yellow": "\033[33m",
    "dim": "\033[2m", "bold": "\033[1m", "reset": "\033[0m",
}


def dw(s: str) -> int:
    """显示宽度：CJK 算 2 列。"""
    w = 0
    for ch in s:
        w += 2 if (ord(ch) > 0x1100 and (
            0x2E80 <= ord(ch) <= 0xA4CF or 0xAC00 <= ord(ch) <= 0xD7A3
            or 0xF900 <= ord(ch) <= 0xFAFF or 0xFE30 <= ord(ch) <= 0xFE6F
            or 0xFF00 <= ord(ch) <= 0xFF60 or 0xFFE0 <= ord(ch) <= 0xFFE6
            or 0x20000 <= ord(ch) <= 0x3FFFD)) else 1
    return w


def pad(s: str, width: int) -> str:
    d = dw(s)
    return s + " " * max(0, width - d)


class Painter:
    def __init__(self, on: bool):
        self.on = on

    def __call__(self, s, *keys):
        if not self.on or not keys:
            return s
        return "".join(ANSI[k] for k in keys) + s + ANSI["reset"]


def render_text(ctx, yi, ji, idx_list, color=True) -> str:
    p = Painter(color)
    L = []
    wide = 62
    ly, lm, ld, leap = ctx["lunar"]
    d = ctx["date"]
    year_animal = ZHI_ANIMALS[ctx["year_ganzhi"][1]]
    key = lambda s: p(pad(s, 6), "dim")

    L.append("")
    L.append(p("═" * wide, "red"))
    L.append(p("                      賽  博  黃  曆", "red", "bold"))
    L.append(p(f"              {cn_year(ly)}年{cn_month(lm, leap)}{cn_day(ld)}", "red"))
    L.append(p(f"              公历 {d.isoformat()}   星期{WEEK_CN[ctx['wd']]}", "red"))
    L.append(p("═" * wide, "red"))
    L.append("")
    L.append("  " + key("干支") + f"{ctx['year_ganzhi']}年 {ctx['month_ganzhi']}月 "
             f"{ctx['day_ganzhi']}日")
    L.append("  " + key("纳音") + ctx["nayin"])
    L.append("  " + key("生肖") + f"{year_animal}（{ctx['year_ganzhi']}年）")
    L.append("  " + key("星座") + ctx["xingzuo"])

    jc_name = JIANCHU[ctx["jianchu"]]
    jc_tag, jc_desc = JIANCHU_CYBER[jc_name]
    L.append("  " + key("建除") + f"{jc_name}日（{jc_tag}）")
    L.append("        " + p(jc_desc, "dim"))

    chong_zhi = (ctx["day_zhi_i"] + 6) % 12
    sha = "南" if ctx["day_zhi_i"] in (0, 4, 8) else \
          "北" if ctx["day_zhi_i"] in (2, 6, 10) else \
          "西" if ctx["day_zhi_i"] in (3, 7, 11) else "东"
    c_chong = CHONG_POOL[ctx["day_idx"] % len(CHONG_POOL)]
    c_sha = SHA_POOL[ctx["day_idx"] % len(SHA_POOL)]
    L.append("  " + key("冲煞") + f"冲{ZHI_ANIMALS[ZHI[chong_zhi]]} 煞{sha}"
             f"    " + p("（赛博：冲" + c_chong + "，煞" + c_sha + "）", "dim"))

    L.append("")
    L.append(p("─" * wide, "dim"))

    w_txt = max([dw(i["text"]) for i in yi + ji] + [20]) + 2
    L.append("")
    L.append(p("  【宜】", "green", "bold"))
    for it in yi:
        L.append("    " + p(pad(it["text"], w_txt), "green") + p(it["why"], "dim"))
    L.append("")
    L.append(p("  【忌】", "red", "bold"))
    for it in ji:
        L.append("    " + p(pad(it["text"], w_txt), "red") + p(it["why"], "dim"))

    L.append("")
    L.append(p("  常年不变：" + " · ".join(ALWAYS), "dim"))

    L.append("")
    L.append(p("─" * wide, "dim"))
    L.append("")
    L.append(p("  【十二时辰】", "yellow", "bold"))
    now_hour = None
    if d == date.today():
        from datetime import datetime
        now_hour = datetime.now().hour
    w_tag = max(dw(t) for _, _, t, _ in HOURS) + 2
    for zhi, span, tag, why in HOURS:
        mark = " "
        if now_hour is not None and span.startswith(f"{now_hour:02d}"):
            mark = p("◀ 此刻", "yellow", "bold")
        good = tag.startswith("宜")
        L.append("    " + p(f"{zhi}时", "bold") + f" {span}  "
                 + p(pad(tag, w_tag), "green" if good else "red") + p(why, "dim") + "  " + mark)

    L.append("")
    L.append(p("─" * wide, "dim"))
    L.append("")
    L.append(p("  【指数】", "yellow", "bold"))
    for n, v in idx_list:
        L.append("    " + pad(n, 8) + p(bar(v), "green" if v >= 60 else "red")
                 + f"  {v:>3}")

    L.append("")
    L.append(p("─" * wide, "dim"))
    L.append("")
    L.append(p("  【今日一签】", "yellow", "bold"))
    L.append("    " + p(SIGNS[ctx["day_idx"] % len(SIGNS)], "bold"))

    L.append("")
    L.append(p("─" * wide, "dim"))
    L.append("")
    L.append(p("  宜忌不是抽签抽出来的。周几、农历、十二建星、日干，每条都有理由。", "dim"))
    L.append(p("  历法部分（农历、干支、建除）可核对；宜忌部分是本工具的赛博解读。", "dim"))
    L.append("")
    return "\n".join(L)


# ─────────────────────────────────────────────────────────────
# 六、HTML 渲染（老黄历页面，可直接截图）
# ─────────────────────────────────────────────────────────────

HTML_CSS = """
*{box-sizing:border-box}
body{margin:0;padding:28px 12px;background:#E6DCC8;
 font-family:"Songti SC","STSong","SimSun","Noto Serif CJK SC",serif;color:#2B2118}
.page{max-width:700px;margin:0 auto;background:#FCF7E8;
 border:3px double #B23B2E;padding:26px 22px 20px;box-shadow:0 2px 0 #C9BEA6}
.hd{text-align:center;border-bottom:2px solid #B23B2E;padding-bottom:12px}
.title{font-size:36px;letter-spacing:14px;color:#B23B2E;font-weight:700;text-indent:14px}
.sub{font-size:14px;color:#6B5A44;margin-top:8px}
.cal{font-size:15px;color:#8A2B1F;margin-top:4px}
.grid{display:grid;grid-template-columns:auto 1fr auto 1fr;gap:6px 10px;
 margin:16px 0;font-size:14px;line-height:1.7}
.k{color:#8A7660;white-space:nowrap}
.v{color:#2B2118}
.jc{font-size:20px;text-align:center;color:#8A2B1F;letter-spacing:4px;
 margin:6px 0 0;padding:10px 0;border-top:1px dashed #C9BEA6;border-bottom:1px dashed #C9BEA6}
.jc small{display:block;font-size:12px;color:#8A7660;letter-spacing:0;margin-top:6px}
.yiji{display:flex;border:2px solid #B23B2E;margin:18px 0}
.half{flex:1;padding:16px 8px;display:flex;gap:18px;justify-content:center}
.half.ji{border-left:1px dashed #C9BEA6;background:#FDF3F1}
.half .lb{writing-mode:vertical-rl;font-size:26px;font-weight:700;letter-spacing:6px}
.half.yi .lb{color:#1F6B3B}
.half.ji .lb{color:#B23B2E}
.items{display:flex;gap:12px;flex-wrap:wrap;justify-content:center}
.item{writing-mode:vertical-rl;font-size:16px;line-height:1.5;letter-spacing:2px}
.half.yi .item{color:#1F6B3B}
.half.ji .item{color:#B23B2E}
.sec{margin-top:18px}
.sec h3{font-size:15px;color:#8A2B1F;letter-spacing:3px;margin:0 0 8px;
 padding-bottom:5px;border-bottom:1px solid #C9BEA6;font-weight:700}
.hr{display:flex;justify-content:space-between;font-size:13px;padding:3px 0;color:#4A3C2C}
.hr b{color:#2B2118;font-weight:700}
.hrs{display:grid;grid-template-columns:58px 104px 92px 1fr;gap:3px 8px;
 font-size:13px;color:#4A3C2C;align-items:baseline;padding:2px 0}
.hrs .tm{color:#8A7660}
.idx{display:grid;grid-template-columns:auto 1fr auto;gap:4px 10px;align-items:center;font-size:13px}
.track{background:#E6DCC8;height:10px;border-radius:5px;overflow:hidden}
.fill{height:100%;background:#B23B2E}
.fill.good{background:#1F6B3B}
.sign{margin-top:6px;padding:12px 14px;background:#F5EBD5;border-left:4px solid #B23B2E;
 font-size:15px;line-height:1.8}
.always{margin-top:14px;padding:9px 12px;background:#EFE7D6;border:1px solid #DDD2BB;
 border-radius:3px;font-size:12px;color:#7A6A55;text-align:center;letter-spacing:.3px}
.ft{margin-top:20px;padding-top:12px;border-top:1px dashed #C9BEA6;
 font-size:11px;color:#8A7660;line-height:1.7}
.foot{max-width:700px;margin:14px auto 0;text-align:center;font-size:11px;color:#8A7660}
"""


def render_html(ctx, yi, ji, idx_list) -> str:
    ly, lm, ld, leap = ctx["lunar"]
    d = ctx["date"]
    e = _html.escape
    jc_name = JIANCHU[ctx["jianchu"]]
    jc_tag, jc_desc = JIANCHU_CYBER[jc_name]
    chong_zhi = (ctx["day_zhi_i"] + 6) % 12
    sha = "南" if ctx["day_zhi_i"] in (0, 4, 8) else \
          "北" if ctx["day_zhi_i"] in (2, 6, 10) else \
          "西" if ctx["day_zhi_i"] in (3, 7, 11) else "东"
    c_chong = CHONG_POOL[ctx["day_idx"] % len(CHONG_POOL)]
    c_sha = SHA_POOL[ctx["day_idx"] % len(SHA_POOL)]

    yi_items = "".join(f'<span class="item">{e(i["text"])}</span>' for i in yi)
    ji_items = "".join(f'<span class="item">{e(i["text"])}</span>' for i in ji)

    jc_list = "".join(
        f'<div class="hrs"><div><b>{z}时</b></div><div class="tm">{sp}</div>'
        f'<div style="color:{"#1F6B3B" if tg.startswith("宜") else "#B23B2E"}">{tg}</div>'
        f'<div style="color:#8A7660">{e(wy)}</div></div>'
        for z, sp, tg, wy in HOURS)

    idx_html = "".join(
        f'<div>{n}</div><div class="track"><div class="fill{" good" if v >= 60 else ""}" '
        f'style="width:{v}%"></div></div><div>{v}</div>'
        for n, v in idx_list)

    why_yi = "".join(f'<div class="hr"><span><b>{e(i["text"])}</b></span>'
                     f'<span style="color:#8A7660;text-align:right">{e(i["why"])}</span></div>'
                     for i in yi)
    why_ji = "".join(f'<div class="hr"><span><b>{e(i["text"])}</b></span>'
                     f'<span style="color:#8A7660;text-align:right">{e(i["why"])}</span></div>'
                     for i in ji)

    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>赛博黄历 · {d.isoformat()}</title>
<style>{HTML_CSS}</style>
</head>
<body>
<div class="page">
  <div class="hd">
    <div class="title">賽博黃曆</div>
    <div class="sub">公历 {d.isoformat()} &nbsp; 星期{WEEK_CN[ctx['wd']]}</div>
    <div class="cal">{cn_year(ly)}年{cn_month(lm, leap)}{cn_day(ld)}</div>
  </div>

  <div class="grid">
    <div class="k">干支</div>
    <div class="v">{ctx['year_ganzhi']}年 {ctx['month_ganzhi']}月 {ctx['day_ganzhi']}日</div>
    <div class="k">纳音</div>
    <div class="v">{ctx['nayin']}</div>
    <div class="k">生肖</div>
    <div class="v">{ZHI_ANIMALS[ctx['year_ganzhi'][1]]}</div>
    <div class="k">星座</div>
    <div class="v">{ctx['xingzuo']}</div>
    <div class="k">冲煞</div>
    <div class="v">冲{ZHI_ANIMALS[ZHI[chong_zhi]]} 煞{sha}</div>
    <div class="k">赛博冲煞</div>
    <div class="v">冲{c_chong} 煞{c_sha}</div>
  </div>

  <div class="jc">{jc_name}日 · {jc_tag}<small>{e(jc_desc)}</small></div>

  <div class="yiji">
    <div class="half yi"><div class="lb">宜</div><div class="items">{yi_items}</div></div>
    <div class="half ji"><div class="lb">忌</div><div class="items">{ji_items}</div></div>
  </div>

  <div class="always">常年不变：{' · '.join(ALWAYS)}</div>

  <div class="sec"><h3>宜 · 为什么</h3>{why_yi}</div>
  <div class="sec"><h3>忌 · 为什么</h3>{why_ji}</div>
  <div class="sec"><h3>十二时辰</h3>{jc_list}</div>
  <div class="sec"><h3>指数</h3><div class="idx">{idx_html}</div></div>
  <div class="sec"><h3>今日一签</h3>
    <div class="sign">{SIGNS[ctx['day_idx'] % len(SIGNS)]}</div>
  </div>

  <div class="ft">
    历法部分（农历、干支、十二建星）依据通行历法数据推算，可以核对。<br>
    宜忌部分是本工具的赛博解读，不构成任何形式的建议。<br>
    赛博黄历 v{VERSION} · 纯本地生成
  </div>
</div>
<div class="foot">由 cyber-almanac 生成</div>
</body>
</html>"""


# ─────────────────────────────────────────────────────────────
# 七、入口
# ─────────────────────────────────────────────────────────────

def to_json(ctx, yi, ji, idx_list) -> str:
    ly, lm, ld, leap = ctx["lunar"]
    jc_name = JIANCHU[ctx["jianchu"]]
    chong_zhi = (ctx["day_zhi_i"] + 6) % 12
    return json.dumps({
        "version": VERSION,
        "date": ctx["date"].isoformat(),
        "weekday": "星期" + WEEK_CN[ctx["wd"]],
        "lunar": {
            "year": ly, "month": lm, "day": ld, "leap": leap,
            "text": f"{cn_year(ly)}年{cn_month(lm, leap)}{cn_day(ld)}",
        },
        "ganzhi": {
            "year": ctx["year_ganzhi"], "month": ctx["month_ganzhi"],
            "day": ctx["day_ganzhi"],
        },
        "nayin": ctx["nayin"],
        "zodiac": ZHI_ANIMALS[ctx["year_ganzhi"][1]],
        "constellation": ctx["xingzuo"],
        "jianchu": {"name": jc_name, "tag": JIANCHU_CYBER[jc_name][0],
                    "desc": JIANCHU_CYBER[jc_name][1]},
        "chong": {"animal": ZHI_ANIMALS[ZHI[chong_zhi]],
                  "cyber": CHONG_POOL[ctx["day_idx"] % len(CHONG_POOL)]},
        "yi": yi,
        "ji": ji,
        "always": ALWAYS,
        "indices": [{"name": n, "value": v} for n, v in idx_list],
        "hours": [{"zhi": z, "span": s, "advice": t, "why": w} for z, s, t, w in HOURS],
        "sign": SIGNS[ctx["day_idx"] % len(SIGNS)],
    }, ensure_ascii=False, indent=2)


def main(argv=None):
    ap = argparse.ArgumentParser(
        prog="almanac",
        description="赛博黄历 —— 把老黄历套在今天真正要操心的事上",
    )
    ap.add_argument("--date", help="指定日期，格式 YYYY-MM-DD")
    ap.add_argument("--week", action="store_true", help="输出今天起的一周")
    ap.add_argument("--html", metavar="FILE", help="生成 HTML 老黄历页面")
    ap.add_argument("--json", action="store_true", help="输出 JSON")
    ap.add_argument("--no-color", action="store_true", help="关闭终端颜色")
    ap.add_argument("--version", action="version", version=f"cyber-almanac {VERSION}")
    args = ap.parse_args(argv)

    if args.date:
        try:
            y, m, d = (int(x) for x in args.date.split("-"))
            base = date(y, m, d)
        except Exception:
            print("日期格式不对，应该是 YYYY-MM-DD", file=sys.stderr)
            return 2
    else:
        base = date.today()

    if not (date(1900, 2, 1) <= base <= date(2100, 12, 31)):
        print("农历数据只覆盖 1900-02 到 2100-12。", file=sys.stderr)
        return 2

    color = (not args.no_color) and sys.stdout.isatty()

    if args.week:
        out = []
        for i in range(7):
            d = base + timedelta(days=i)
            ctx = build_context(d)
            yi, ji = collect(ctx)
            idx_list = indices(ctx)
            out.append(render_text(ctx, yi, ji, idx_list, color=False))
        text = "\n".join(out)
        print(text)
        return 0

    ctx = build_context(base)
    yi, ji = collect(ctx)
    idx_list = indices(ctx)

    if args.json:
        print(to_json(ctx, yi, ji, idx_list))
        return 0

    if args.html:
        path = args.html
        with open(path, "w", encoding="utf-8") as f:
            f.write(render_html(ctx, yi, ji, idx_list))
        print(f"已生成：{path}")
        return 0

    print(render_text(ctx, yi, ji, idx_list, color=color))
    return 0


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    raise SystemExit(main())
