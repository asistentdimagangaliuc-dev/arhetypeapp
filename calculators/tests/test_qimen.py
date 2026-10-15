"""Тесты калькулятора Ци Мэнь Дунь Цзя (calculators/qimen.py).

Сверка:
(1) классические тексты с полностью разобранными картами (URL в комментариях):
    黄宗羲 《易學象數論·超神接氣直指》 (два примера 1589 г.), 《奇門遁甲統宗》 (置闰 1717–1719),
    《遁甲演義》 (值符/值使 для часов 甲), 《御定奇門寶鑑》 (раскладка восьми духов);
(2) опубликованный онлайн-калькулятор Master Sean Chan (карта 11.09.2026 08:00);
(3) снимки выводов независимых библиотек (НЕ импортируются — значения зафиксированы):
    kinqimen 0.0.6.6 (PyPI, Python), kinqimen 0.3.1 (npm, TypeScript), qimen-dunjia 3.1.0 (npm);
    все три принимают время как настенные часы UTC+8, поэтому сверка идёт с
    tz='UTC+08:00', solar_time='clock', zi_hour='early';
(4) инварианты и эталонные персоны T1–T4.
"""
from __future__ import annotations

import json
import random
from dataclasses import replace
from datetime import date, timedelta

import pytest
import swisseph as swe

from calculators import bazi
from calculators.common.time import BirthInput
from calculators.qimen import (
    DOORS,
    JU_TABLE,
    RING,
    STARS,
    STEM_ORDER,
    TERMS,
    _Clock,
    build_chart,
    calculate,
    earth_plate,
    ju_zhirun,
)
from calculators.bazi import STEMS

T1 = BirthInput(1990, 5, 15, 14, 30, place="Москва", gender="female")
T2 = BirthInput(1984, 2, 4, 23, 30, place="Москва", gender="male")
T3 = BirthInput(2004, 2, 29, 8, 15, place="Санкт-Петербург", gender="female")
T4 = BirthInput(1879, 3, 14, 11, 30, tz="LMT", lat=48.4011, lon=9.9876, gender="male")

BJ = dict(solar_time="clock", zi_hour="early")   # режим библиотек: часы UTC+8, день с 23:00

GUA = {"坎": 1, "坤": 2, "震": 3, "巽": 4, "中": 5, "乾": 6, "兑": 7, "兌": 7, "艮": 8, "离": 9, "離": 9}
STAR1 = {"蓬": 1, "芮": 2, "冲": 3, "沖": 3, "辅": 4, "輔": 4, "禽": 2, "心": 6, "柱": 7, "任": 8, "英": 9}
DOOR1 = {"休": 1, "生": 8, "伤": 3, "傷": 3, "杜": 4, "景": 9, "死": 2, "惊": 7, "驚": 7, "开": 6, "開": 6}
GOD1 = {"符": "值符", "蛇": "腾蛇", "阴": "太阴", "陰": "太阴", "合": "六合", "虎": "白虎", "玄": "玄武",
        "勾": "勾陈", "雀": "朱雀", "地": "九地", "天": "九天"}


def bj(y, m, d, h, mi=0):
    return BirthInput(y, m, d, h, mi, tz="UTC+08:00")


def palaces(r):
    return {p["palace"]: p for p in r["palaces"]}


def layout(r):
    """{дворец: (звезда-хозяин, дверь-хозяин, дух, первый небесный ствол)} для 8 внешних дворцов."""
    return {p: (x["star_home"], x["door_home"], x["deity"], x["heaven_stems"][0]) for p, x in palaces(r).items() if p != 5}


# ---------------------------------------------------------------------------
# 1. Таблицы
# ---------------------------------------------------------------------------

def test_ju_table_verse():
    # Стихи «冬至驚蟄一七四，小寒二八五…» / «夏至白露九三六…»; таблица kinqimen 0.0.6.6 config.jieqicode
    # (https://pypi.org/project/kinqimen/0.0.6.6/) и README qimen-dunjia 3.1.0 «節氣局數表»
    # (https://www.npmjs.com/package/qimen-dunjia).
    verse = {
        ("冬至", "惊蛰"): "174", ("小寒",): "285", ("大寒", "春分"): "396", ("立春",): "852", ("雨水",): "963",
        ("清明", "立夏"): "417", ("谷雨", "小满"): "528", ("芒种",): "639", ("夏至", "白露"): "936",
        ("小暑",): "825", ("大暑", "秋分"): "714", ("立秋",): "258", ("处暑",): "147", ("霜降", "小雪"): "582",
        ("寒露", "立冬"): "693", ("大雪",): "471",
    }
    names = [t[0] for t in TERMS]
    seen = 0
    for keys, digits in verse.items():
        for k in keys:
            assert "".join(map(str, JU_TABLE[names.index(k)])) == digits, k
            seen += 1
    assert seen == 24 and len(JU_TABLE) == 24
    # 阳遁 — 冬至…芒种 (12 терминов), 阴遁 — 夏至…大雪
    assert names[0] == "冬至" and names[11] == "芒种" and names[12] == "夏至" and names[23] == "大雪"


def test_earth_plate_tongzong_examples():
    # 《奇門遁甲統宗》: «如一局，甲子戊起坎一宫，則甲戌己在坤二宫，甲申庚在震三宫，甲午辛在巽四宫，甲辰壬在中五宫，
    # 甲寅癸在乾六宫…丁在兑七宫，丙在艮八宫，乙在离九宫»; «阴遁…甲子戊起离九宫，則甲戌己在艮八宫，甲申庚在兑七宫，
    # 甲午辛在乾六宫，甲辰壬在中五宫，甲寅癸在巽四宫…丁在震三宫，丙在坤二宫，乙在坎一宫».
    # https://zh.wikisource.org/wiki/奇門遁甲統宗
    e = {p: STEMS[s][0] for p, s in earth_plate(True, 1).items()}
    assert e == {1: "戊", 2: "己", 3: "庚", 4: "辛", 5: "壬", 6: "癸", 7: "丁", 8: "丙", 9: "乙"}
    e = {p: STEMS[s][0] for p, s in earth_plate(False, 9).items()}
    assert e == {9: "戊", 8: "己", 7: "庚", 6: "辛", 5: "壬", 4: "癸", 3: "丁", 2: "丙", 1: "乙"}
    for yang in (True, False):
        for ju in range(1, 10):
            ep = earth_plate(yang, ju)
            assert sorted(ep) == list(range(1, 10)) and sorted(ep.values()) == sorted(STEM_ORDER)


@pytest.mark.parametrize("yang,ju,expected", [
    # 《遁甲演義》 «時家奇門»: «假如陽遁一局，甲子在坎，天蓬為直符，休門為直使…甲戌在坤，天芮…死門…甲申在震，天冲…
    # 傷門…甲午在巽，天輔…杜門…甲辰在五，天禽為直符，死門為直使…甲寅在乾，天心…開門»;
    # «若陰遁九局，甲子在離，天英…景門。甲戌在艮，天任…生門。甲申在兑，天柱…驚門。甲午在乾，天心…開門。
    # 甲辰在五，天禽為直符，死門為直使…甲寅在巽，天輔…杜門». https://zh.wikisource.org/wiki/遁甲演義
    (True, 1, ["天蓬休门", "天芮死门", "天冲伤门", "天辅杜门", "天禽死门", "天心开门"]),
    (False, 9, ["天英景门", "天任生门", "天柱惊门", "天心开门", "天禽死门", "天辅杜门"]),
])
def test_dunjia_yanyi_zhifu_zhishi(yang, ju, expected):
    got = []
    for xun in range(6):
        ch = build_chart(yang, ju, xun * 10)            # час 甲X —伏吟: всё на своих местах
        got.append(STARS[ch["p0"]][0] + DOORS[ch["door_src"]][0])
        assert ch["star_offset"] == 0 and ch["door_offset"] == 0
    assert got == expected


@pytest.mark.parametrize("yang,expected", [
    # 《御定奇門寶鑑》: «如陽遁坎一宫，甲子時直符到坎，逆布九天，直符坎、九天乾、九地兑、元武坤、白虎離、六合巽、
    # 太陰震、螣蛇艮。陰遁坎一宫，甲子時直符在坎，順布九天。直符坎、九天艮、…元武巽、白虎離、六合坤、太陰兑、螣蛇乾»
    # https://zh.wikisource.org/wiki/奇门宝鉴御定
    (True, {1: "值符", 6: "九天", 7: "九地", 2: "玄武", 9: "白虎", 4: "六合", 3: "太阴", 8: "腾蛇"}),
    (False, {1: "值符", 8: "九天", 3: "九地", 4: "玄武", 9: "白虎", 2: "六合", 7: "太阴", 6: "腾蛇"}),
])
def test_baojian_deities(yang, expected):
    ch = build_chart(yang, 1, 0, deities="baihu")
    assert ch["deity_at"] == expected


# ---------------------------------------------------------------------------
# 2. Классические разобранные карты: 黄宗羲 《易學象數論》 卷六 «超神接氣直指»
#    https://zh.wikisource.org/wiki/易學象數論/超神接氣直指
# ---------------------------------------------------------------------------

def test_huang_zongxi_example_a_chaoshen():
    # «萬曆己丑年正月初二庚戌日辛巳時…符頭係己酉管事。本月初六日交雨水節上局，乃超神也。從九宫起…»
    # 正月初二 = 16.02.1589 (庚戌). Вариант духов 句陳/朱雀 (deities='gouchen').
    r = calculate(bj(1589, 2, 16, 10), ju_method="zhirun", deities="gouchen", **BJ)
    assert r["pillars"]["day"] == "庚戌" and r["pillars"]["hour"] == "辛巳"
    assert r["ju"]["label"] == "阳遁9局 雨水上元" and r["ju"]["zhirun"]["state"] == "chaoshen"
    p = palaces(r)
    # «戊在離，己在坎，庚在坤，辛在震，壬在巽，癸在中宫…乙在艮…丙在兑…丁在乾»
    assert {k: v["earth_stem"] for k, v in p.items()} == {9: "戊", 1: "己", 2: "庚", 3: "辛", 4: "壬", 5: "癸",
                                                         8: "乙", 7: "丙", 6: "丁"}
    # «以天蓬爲直符，加在地盤震宫…任在巽…衝在離，輔在坤，英在兑，芮在乾，柱在坎…心在艮»
    assert r["zhi_fu"]["star"] == "天蓬" and r["zhi_fu"]["palace"] == 3
    assert {k: v["star"] for k, v in p.items() if k != 5} == {
        3: "天蓬", 4: "天任", 9: "天冲", 2: "天辅", 7: "天英", 6: "天芮", 1: "天柱", 8: "天心"}
    # «天任星帶艮之乙奇到巽…天柱星帶兑之丙奇到坎…天心星帶乾之丁奇到艮»
    assert p[4]["heaven_stems"][0] == "乙" and p[1]["heaven_stems"][0] == "丙" and p[8]["heaven_stems"][0] == "丁"
    # «以直使休門加地盤之艮，順數，生在震，傷在巽，杜在離，景在坤，死在兑，驚在乾，開在坎»
    assert {k: v["door"] for k, v in p.items() if k != 5} == {
        8: "休门", 3: "生门", 4: "伤门", 9: "杜门", 2: "景门", 7: "死门", 6: "惊门", 1: "开门"}
    # «直符…在震宫，順數則騰蛇在巽，大陰在離，六合在坤，句陳在兑，朱雀在乾，九地在坎，九天在艮»
    assert {k: v["deity"] for k, v in p.items() if k != 5} == {
        3: "值符", 4: "腾蛇", 9: "太阴", 2: "六合", 7: "勾陈", 6: "朱雀", 1: "九地", 8: "九天"}
    # При 拆补法 (тот же момент) — ещё 立春: 符头 己酉 → 上元 → 阳8 (超神 действует только в 置闰法)
    assert calculate(bj(1589, 2, 16, 10), **BJ)["ju"]["label"] == "阳遁8局 立春上元"


def test_huang_zongxi_example_b_leap():
    # «萬曆己丑年十一月初六庚戌日戊寅時…符已超節九日，正當置閏…自初五日己酉至初九日癸丑…爲大雪閏奇上局…
    # 係夏至後未交冬至，尚用陰遁逆局。從四宫巽起六儀…» 十一月初六 = 13.12.1589.
    r = calculate(bj(1589, 12, 13, 4), ju_method="zhirun", deities="gouchen", **BJ)
    assert r["pillars"]["day"] == "庚戌" and r["pillars"]["hour"] == "戊寅"
    assert r["ju"]["label"] == "阴遁4局 大雪闰上元" and r["ju"]["leap"] and r["ju"]["zhirun"]["state"] == "leap"
    p = palaces(r)
    # «戊在巽，己在辰(震)，庚在坤，辛在坎，壬在離，癸在艮。乙奇在中宫寄坤，丙奇在乾，丁奇在兑»
    assert {k: v["earth_stem"] for k, v in p.items()} == {4: "戊", 3: "己", 2: "庚", 1: "辛", 9: "壬", 8: "癸",
                                                         5: "乙", 6: "丙", 7: "丁"}
    # «天衝爲直符，傷門爲直使。時干戊泊在巽。以天衝直符加巽，輔在離，英在坤，芮在兑…柱在乾…心在坎…蓬在艮，任在震»
    assert r["zhi_fu"]["star"] == "天冲" and r["zhi_shi"]["door"] == "伤门"
    assert {k: v["star"] for k, v in p.items() if k != 5} == {
        4: "天冲", 9: "天辅", 2: "天英", 7: "天芮", 6: "天柱", 1: "天心", 8: "天蓬", 3: "天任"}
    # «天芮星帶中宫之乙奇到兑» — 天禽 и ствол центра едут с 天芮 (寄坤 и в 阴遁)
    assert p[7]["heaven_stems"] == ["庚", "乙"] and p[7]["star_guest"] == "天禽"
    assert p[6]["heaven_stems"][0] == "丁" and p[1]["heaven_stems"][0] == "丙"
    # «以直使傷門加艮，杜在震，景在巽，死在離，驚在坤，開在兑，休在乾，生在坎»
    assert {k: v["door"] for k, v in p.items() if k != 5} == {
        8: "伤门", 3: "杜门", 4: "景门", 9: "死门", 2: "惊门", 7: "开门", 6: "休门", 1: "生门"}
    # «直符…在巽，逆行，騰蛇在震，太陰在艮，六合在坎，句陳在乾，朱雀在兑，九地在坤，九天在離»
    assert {k: v["deity"] for k, v in p.items() if k != 5} == {
        4: "值符", 3: "腾蛇", 8: "太阴", 1: "六合", 6: "勾陈", 7: "朱雀", 2: "九地", 9: "九天"}
    # «生門屬土，臨坎宫，乃門制其宫，謂之迫»
    assert {"door": "生门", "palace": 1, "trigram": "坎"} in r["patterns"]["men_po"]


# ---------------------------------------------------------------------------
# 3. 置闰法: 《奇門遁甲統宗》 «置閏法», 康熙 56–58 (1717–1719)
#    https://zh.wikisource.org/wiki/奇門遁甲統宗
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("d,label,state", [
    # «五月初一己酉即為芒種上局…十六日甲子不作夏至上局，而為芒種閏奇上局，二十一日己巳作芒種閏奇中局，
    # 二十六日甲戌作芒種閏奇下局…六月初二日己卯始得為夏至上局。斯乃謂之接氣»
    (date(1718, 5, 30), "阳遁6局 芒种上元", "chaoshen"),       # 五月初一 己酉
    (date(1718, 6, 14), "阳遁6局 芒种闰上元", "leap"),          # 五月十六 甲子
    (date(1718, 6, 19), "阳遁3局 芒种闰中元", "leap"),          # 五月廿一 己巳
    (date(1718, 6, 24), "阳遁9局 芒种闰下元", "leap"),          # 五月廿六 甲戌
    (date(1718, 6, 29), "阴遁9局 夏至上元", "jieqi"),           # 六月初二 己卯
    # «直至康熙五十八年六月二十三日立秋，而甲子符頭恰當日，是為正授，本日即是陰遁二局»
    (date(1719, 8, 8), "阴遁2局 立秋上元", "zhengshou"),
    # «上元至七月初九日庚辰處暑即超一日矣»
    (date(1719, 8, 24), "阴遁1局 处暑上元", "chaoshen"),
])
def test_tongzong_zhirun_1718_1719(d, label, state):
    r = calculate(bj(d.year, d.month, d.day, 12), ju_method="zhirun", **BJ)
    assert r["ju"]["label"] == label
    assert r["ju"]["zhirun"]["state"] == state
    if d == date(1719, 8, 24):
        assert r["ju"]["zhirun"]["chao_days"] == 1


def test_tongzong_leap_needs_threshold_8():
    # 統宗 считает «超九日» включительно (16-е…24-е = разность 8 дней). Порог 9 по разности дат
    # пропускает этот 置闰 — поэтому по умолчанию zhirun_leap_days=8 (так же в qimen-dunjia 3.1.0).
    r9 = calculate(bj(1718, 6, 14, 12), ju_method="zhirun", zhirun_leap_days=9, **BJ)
    assert r9["ju"]["label"] == "阴遁9局 夏至上元"


def test_zhirun_leaps_only_at_mangzhong_daxue_and_no_gaps():
    """1950–2030: блоки по 15 дней без пропусков терминов, 闰 — только 芒种/大雪, 超神 до 二至 в [−7, 8)."""
    clock = _Clock("UTC+08:00", "fixed", 8.0, None, "clock")
    leaps = 0
    prev = None
    d = date(1950, 1, 1)
    while d < date(2030, 1, 1):
        if bazi.day_index(d) % 15 == 0:                 # верхний 符头: начало блока
            r = ju_zhirun(d, swe.julday(d.year, d.month, d.day, 4.0), clock, 8)
            k = r["term"]
            assert r["yuan"] == 0
            if r["leap"]:
                leaps += 1
                assert TERMS[k][0] in ("芒种", "大雪") and k == prev
            elif prev is not None:
                assert k == (prev + 1) % 24
                if TERMS[k][0] in ("夏至", "冬至"):
                    assert -7 <= r["chao_days"] < 8
            prev = k
        d += timedelta(days=1)
    assert 25 <= leaps <= 30     # ≈ 80 лет / 2,86 года


# ---------------------------------------------------------------------------
# 4. Опубликованный онлайн-калькулятор
# ---------------------------------------------------------------------------

def test_master_sean_chan_calculator_2026_09_11():
    # https://www.masterseanchan.com/qi-men-dun-jia-calculator/ (просмотр 14.10.2026): «Chart for 2026-09-11 08:00,
    # 節氣 白露, 陰遁9局, 元 0, 四柱 丙午 丁酉 戊子 丙辰»; сайт пишет «follows the 拆補 method», но 上元 для дня 戊子
    # (符头 甲申 → 中元) получается только счётом 5 суток от термина — это наш 'maoshan'.
    r = calculate(bj(2026, 9, 11, 8), ju_method="maoshan", **BJ)
    assert r["ju"]["label"] == "阴遁9局 白露上元"
    assert [r["pillars"][k] for k in ("year", "month", "day", "hour")] == ["丙午", "丁酉", "戊子", "丙辰"]
    p = palaces(r)
    site = {  # дворец: (звезда, дверь, небесный ствол, земной ствол)
        4: ("天任", "生门", "己", "癸"), 9: ("天冲", "伤门", "丁", "戊"), 2: ("天辅", "杜门", "癸", "丙"),
        3: ("天蓬", "休门", "乙", "丁"), 7: ("天英", "景门", "戊", "庚"), 8: ("天心", "开门", "辛", "己"),
        1: ("天柱", "惊门", "庚", "乙"), 6: ("天芮", "死门", "丙", "辛"),
    }
    for q, (st, dr, hv, ea) in site.items():
        assert (p[q]["star"], p[q]["door"], p[q]["heaven_stems"][0], p[q]["earth_stem"]) == (st, dr, hv, ea), q
    assert p[5]["earth_stem"] == "壬"
    # Расхождение: на сайте духи в 阴遁 идут ПО часовой стрелке (2 值符, 7 螣蛇, 6 太阴, 1 六合, 8 白虎, 3 玄武,
    # 4 九地, 9 九天). Классика (黄宗羲, 寶鑑, 演義) — против часовой: 2 值符, 9 腾蛇, 4 太阴, 3 六合, 8 白虎…
    assert {q: p[q]["deity"] for q in (2, 9, 4, 3, 8, 1, 6, 7)} == {
        2: "值符", 9: "腾蛇", 4: "太阴", 3: "六合", 8: "白虎", 1: "玄武", 6: "九地", 7: "九天"}
    # При 拆补法 (符头) тот же момент — 中元: 阴遁3局
    assert calculate(bj(2026, 9, 11, 8), **BJ)["ju"]["label"] == "阴遁3局 白露中元"


# ---------------------------------------------------------------------------
# 5. Снимки независимых библиотек (выполнены 14.10.2026 в отдельном окружении, не зависимости проекта)
# ---------------------------------------------------------------------------

# kinqimen 0.3.1 (npm, TypeScript, «时家奇门拆补法»): https://www.npmjs.com/package/kinqimen
# Духи у этой версии — 白虎/玄武 в обоих 遁 (= deities='baihu'); 暗干 — правило этой библиотеки.
KT_031 = {
    (2024, 6, 1, 10): ("阳五局上",
                       {"坎": "柱", "艮": "心", "震": "蓬", "巽": "任", "离": "冲", "坤": "辅", "兑": "英", "乾": "禽"},
                       {"兑": "惊", "乾": "开", "坎": "休", "艮": "生", "震": "伤", "巽": "杜", "离": "景", "坤": "死"},
                       {"坎": "符", "艮": "蛇", "震": "阴", "巽": "合", "离": "虎", "坤": "玄", "兑": "地", "乾": "天"},
                       {"坎": "庚", "艮": "己", "震": "癸", "巽": "辛", "离": "丙", "坤": "乙", "兑": "壬", "乾": "丁"},
                       {"兑": "癸", "艮": "丁", "离": "丙", "坎": "乙", "坤": "戊", "震": "己", "巽": "庚", "中": "辛", "乾": "壬"}),
    (1961, 1, 23, 9): ("阳九局中",
                       {"坤": "禽", "兑": "柱", "乾": "心", "坎": "蓬", "艮": "任", "震": "冲", "巽": "辅", "离": "英"},
                       {"坤": "死", "兑": "惊", "乾": "开", "坎": "休", "艮": "生", "震": "伤", "巽": "杜", "离": "景"},
                       {"坤": "符", "兑": "蛇", "乾": "阴", "坎": "合", "艮": "虎", "震": "玄", "巽": "地", "离": "天"},
                       {"坤": "庚", "兑": "丙", "乾": "丁", "坎": "己", "艮": "乙", "震": "辛", "巽": "壬", "离": "戊"},
                       {"坤": "癸", "震": "丁", "巽": "丙", "中": "乙", "乾": "戊", "兑": "己", "艮": "庚", "离": "辛", "坎": "壬"}),
    (1999, 1, 5, 11): ("阳七局中",
                       {"坤": "禽", "兑": "柱", "乾": "心", "坎": "蓬", "艮": "任", "震": "冲", "巽": "辅", "离": "英"},
                       {"巽": "死", "离": "惊", "坤": "开", "兑": "休", "乾": "生", "坎": "伤", "艮": "杜", "震": "景"},
                       {"坤": "符", "兑": "蛇", "乾": "阴", "坎": "合", "艮": "虎", "震": "玄", "巽": "地", "离": "天"},
                       {"坤": "壬", "兑": "戊", "乾": "乙", "坎": "辛", "艮": "己", "震": "癸", "巽": "丁", "离": "庚"},
                       {"巽": "丙", "中": "乙", "乾": "戊", "兑": "己", "艮": "庚", "离": "辛", "坎": "壬", "坤": "癸", "震": "丁"}),
    (1965, 10, 17, 23): ("阴三局下",
                         {"坤": "禽", "离": "英", "巽": "辅", "震": "冲", "艮": "任", "坎": "蓬", "乾": "心", "兑": "柱"},
                         {"离": "死", "巽": "景", "震": "杜", "艮": "伤", "坎": "生", "乾": "休", "兑": "开", "坤": "惊"},
                         {"坤": "符", "离": "蛇", "巽": "阴", "震": "合", "艮": "虎", "坎": "玄", "乾": "地", "兑": "天"},
                         {"坤": "己", "离": "辛", "巽": "乙", "震": "戊", "艮": "壬", "坎": "庚", "乾": "丁", "兑": "癸"},
                         {"离": "丙", "艮": "乙", "兑": "戊", "乾": "己", "中": "庚", "巽": "辛", "震": "壬", "坤": "癸", "坎": "丁"}),
    (1977, 9, 4, 1): ("阴一局上",
                      {"坤": "蓬", "离": "心", "巽": "柱", "震": "禽", "艮": "英", "坎": "辅", "乾": "冲", "兑": "任"},
                      {"离": "休", "巽": "开", "震": "惊", "艮": "死", "坎": "景", "乾": "杜", "兑": "伤", "坤": "生"},
                      {"坤": "符", "离": "蛇", "巽": "阴", "震": "合", "艮": "虎", "坎": "玄", "乾": "地", "兑": "天"},
                      {"坤": "戊", "离": "壬", "巽": "辛", "震": "乙", "艮": "己", "坎": "丁", "乾": "丙", "兑": "庚"},
                      {"离": "乙", "艮": "戊", "兑": "己", "乾": "庚", "中": "辛", "巽": "壬", "震": "癸", "坤": "丁", "坎": "丙"}),
    # Эталонные персоны: библиотеке подано время карты (истинное солнечное) как часы UTC+8 — термин,
    # день и час те же, что у T1/T3/T4 (T2 так не воспроизводится: в пекинских часах 亥 ещё до Личуня).
    (1990, 5, 15, 13, 4): ("阳四局上",
                           {"离": "禽", "坤": "柱", "兑": "心", "乾": "蓬", "坎": "任", "艮": "冲", "震": "辅", "巽": "英"},
                           {"坤": "死", "兑": "惊", "乾": "开", "坎": "休", "艮": "生", "震": "伤", "巽": "杜", "离": "景"},
                           {"离": "符", "坤": "蛇", "兑": "阴", "乾": "合", "坎": "虎", "艮": "玄", "震": "地", "巽": "天"},
                           {"离": "丙", "坤": "辛", "兑": "庚", "乾": "丁", "坎": "壬", "艮": "乙", "震": "戊", "巽": "癸"},
                           {"中": "癸", "乾": "丁", "兑": "丙", "艮": "乙", "离": "戊", "坎": "己", "坤": "庚", "震": "辛", "巽": "壬"}),
    (2004, 2, 29, 7, 3): ("阳三局下",
                          {"坎": "任", "艮": "冲", "震": "辅", "巽": "英", "离": "禽", "坤": "柱", "兑": "心", "乾": "蓬"},
                          {"坎": "生", "艮": "伤", "震": "杜", "巽": "景", "离": "死", "坤": "惊", "兑": "开", "乾": "休"},
                          {"坎": "符", "艮": "蛇", "震": "阴", "巽": "合", "离": "虎", "坤": "玄", "兑": "地", "乾": "天"},
                          {"坎": "癸", "艮": "戊", "震": "己", "巽": "丁", "离": "乙", "坤": "壬", "兑": "辛", "乾": "丙"},
                          {"中": "丙", "乾": "乙", "兑": "戊", "艮": "己", "离": "庚", "坎": "辛", "坤": "壬", "震": "癸", "巽": "丁"}),
    (1879, 3, 14, 11, 20): ("阳一局上",
                            {"巽": "辅", "离": "英", "坤": "禽", "兑": "柱", "乾": "心", "坎": "蓬", "艮": "任", "震": "冲"},
                            {"巽": "杜", "离": "景", "坤": "死", "兑": "惊", "乾": "开", "坎": "休", "艮": "生", "震": "伤"},
                            {"巽": "符", "离": "蛇", "坤": "阴", "兑": "合", "乾": "虎", "坎": "玄", "艮": "地", "震": "天"},
                            {"巽": "辛", "离": "乙", "坤": "己", "兑": "丁", "乾": "癸", "坎": "戊", "艮": "丙", "震": "庚"},
                            {"中": "辛", "乾": "壬", "兑": "癸", "艮": "丁", "离": "丙", "坎": "乙", "坤": "戊", "震": "己", "巽": "庚"}),
    (1977, 7, 7, 16): ("阴八局上",
                       {"乾": "心", "兑": "柱", "坤": "禽", "离": "英", "巽": "辅", "震": "冲", "艮": "任", "坎": "蓬"},
                       {"乾": "开", "兑": "惊", "坤": "死", "离": "景", "巽": "杜", "震": "伤", "艮": "生", "坎": "休"},
                       {"乾": "符", "兑": "蛇", "坤": "阴", "离": "合", "巽": "虎", "震": "玄", "艮": "地", "坎": "天"},
                       {"乾": "庚", "兑": "己", "坤": "丁", "离": "乙", "巽": "壬", "震": "癸", "艮": "戊", "坎": "丙"},
                       {"中": "庚", "巽": "辛", "震": "壬", "坤": "癸", "坎": "丁", "离": "丙", "艮": "乙", "兑": "戊", "乾": "己"}),
}


@pytest.mark.parametrize("key", list(KT_031))
def test_kinqimen_ts_0_3_1_snapshot(key):
    ju, star, door, god, sky, angan = KT_031[key]
    r = calculate(bj(*key), deities="baihu", **BJ)
    assert (r["ju"]["dun_cn"][0], r["ju"]["number"], r["ju"]["yuan_cn"][0]) == (
        ju[0], "一二三四五六七八九".index(ju[1]) + 1, ju[3])
    p = palaces(r)
    for g, s in star.items():
        assert p[GUA[g]]["star_home"] == STAR1[s]
        if s == "禽":
            assert p[GUA[g]].get("star_guest") == "天禽"
    for g, s in door.items():
        assert p[GUA[g]]["door_home"] == DOOR1[s]
    for g, s in god.items():
        assert p[GUA[g]]["deity"] == GOD1[s]
    for g, s in sky.items():
        assert p[GUA[g]]["heaven_stems"][0] == s
    for g, s in angan.items():
        assert p[GUA[g]]["hidden_stem"] == s


# kinqimen 0.0.6.6 (PyPI, Python; https://pypi.org/project/kinqimen/0.0.6.6/), pan(1) = 拆補.
# Духи: 陽遁 — 勾/雀, 陰遁 — 虎/玄 (= deities='split').
KQ_066 = {
    (2024, 6, 1, 10): ("陽遁五局上元", {"坎": "柱", "艮": "心", "震": "蓬", "巽": "任", "離": "沖", "坤": "輔", "兌": "英", "乾": "禽"},
                       {"兌": "驚", "乾": "開", "坎": "休", "艮": "生", "震": "傷", "巽": "杜", "離": "景", "坤": "死"},
                       {"坎": "符", "艮": "蛇", "震": "陰", "巽": "合", "離": "勾", "坤": "雀", "兌": "地", "乾": "天"},
                       {"坎": "庚", "艮": "己", "震": "癸", "巽": "辛", "離": "丙", "坤": "乙", "兌": "壬", "乾": "丁"}),
    (1977, 9, 4, 1): ("陰遁一局上元", {"坤": "蓬", "離": "心", "巽": "柱", "震": "禽", "艮": "英", "坎": "輔", "乾": "沖", "兌": "任"},
                      {"離": "休", "巽": "開", "震": "驚", "艮": "死", "坎": "景", "乾": "杜", "兌": "傷", "坤": "生"},
                      {"坤": "符", "離": "蛇", "巽": "陰", "震": "合", "艮": "虎", "坎": "玄", "乾": "地", "兌": "天"},
                      {"坤": "戊", "離": "壬", "巽": "辛", "震": "乙", "艮": "己", "坎": "丁", "乾": "丙", "兌": "庚"}),
    (1999, 1, 5, 11): ("陽遁七局中元", {"坤": "禽", "兌": "柱", "乾": "心", "坎": "蓬", "艮": "任", "震": "沖", "巽": "輔", "離": "英"},
                       {"巽": "死", "離": "驚", "坤": "開", "兌": "休", "乾": "生", "坎": "傷", "艮": "杜", "震": "景"},
                       {"坤": "符", "兌": "蛇", "乾": "陰", "坎": "合", "艮": "勾", "震": "雀", "巽": "地", "離": "天"},
                       None),   # 天盤 у kinqimen 0.0.6.6 в этом случае (值符 в центре) ошибочен — см. протокол
}


@pytest.mark.parametrize("key", list(KQ_066))
def test_kinqimen_py_0_0_6_6_snapshot(key):
    ju, star, door, god, sky = KQ_066[key]
    r = calculate(bj(*key), deities="split", **BJ)
    assert (r["ju"]["dun_cn"][0], r["ju"]["number"]) == ({"陽": "阳", "陰": "阴"}[ju[0]], "一二三四五六七八九".index(ju[2]) + 1)
    p = palaces(r)
    for g, s in star.items():
        assert p[GUA[g]]["star_home"] == STAR1[s]
    for g, s in door.items():
        assert p[GUA[g]]["door_home"] == DOOR1[s]
    for g, s in god.items():
        assert p[GUA[g]]["deity"] == GOD1[s]
    if sky:
        for g, s in sky.items():
            assert p[GUA[g]]["heaven_stems"][0] == s


@pytest.mark.parametrize("args,method,label", [
    # README qimen-dunjia 3.1.0 (https://www.npmjs.com/package/qimen-dunjia): «generateChartByDatetime('2024011510')
    # … // 小寒 中元 8»; «'2024061512' // 芒種中元 陽遁3局（拆補，預設）»; «{ 定局法: '符頭' } // 夏至上元 陰遁9局».
    # «拆補» этой библиотеки = счёт 5 суток от момента термина = наш 'maoshan'; «符頭» = наш 'zhirun'.
    ((2024, 1, 15, 10), "maoshan", "阳遁8局 小寒中元"),
    ((2024, 6, 15, 12), "maoshan", "阳遁3局 芒种中元"),
    ((2024, 6, 15, 12), "zhirun", "阴遁9局 夏至上元"),
    # снимок вывода qimen-dunjia 3.1.0 для 1977-09-04 01:00: 拆補 → 陰7 處暑下元, 符頭 → 陰9 白露上元
    ((1977, 9, 4, 1), "maoshan", "阴遁7局 处暑下元"),
    ((1977, 9, 4, 1), "zhirun", "阴遁9局 白露上元"),
])
def test_qimen_dunjia_npm_snapshot(args, method, label):
    assert calculate(bj(*args), ju_method=method, **BJ)["ju"]["label"] == label


@pytest.mark.parametrize("d,label", [
    # Независимая проверка 14.10.2026 (qimen-dunjia 3.1.0 «符頭», полдень UTC+8; цепочка 1900–2100 совпала
    # за все 73 414 дней). Эти даты различают два прочтения триггера 置闰: по удалённости 符头 от
    # солнцестояния (《統宗» 1718, наш zhirun) и по 超 самого 芒种/大雪 (《演義» «遇芒種大雪超過九日»):
    # 1987 — 芒种 超 7 дн., 夏至 超 8 → 闰; 2012 — 大雪 超 8, 冬至 超 7 → без 闰.
    (date(1987, 6, 14), "阳遁6局 芒种闰上元"),
    (date(2012, 12, 14), "阳遁1局 冬至上元"),
])
def test_qimen_dunjia_zhirun_trigger_dates(d, label):
    assert calculate(bj(d.year, d.month, d.day, 12), ju_method="zhirun", **BJ)["ju"]["label"] == label


def test_qimen_dunjia_late_rat_pillars():
    # README qimen-dunjia: «'2024011523' // 日柱己卯、時柱甲子（預設，次日派）»
    r = calculate(bj(2024, 1, 15, 23), **BJ)
    assert (r["pillars"]["day"], r["pillars"]["hour"]) == ("己卯", "甲子")
    # zi_hour='late': день 戊寅 остаётся, ствол часа — от следующего дня (как в модуле 01) → 甲子.
    # (qimen-dunjia «當日» даёт 壬子 — ствол от того же дня; это расхождение описано в базе знаний.)
    r = calculate(bj(2024, 1, 15, 23), solar_time="clock", zi_hour="late")
    assert (r["pillars"]["day"], r["pillars"]["hour"]) == ("戊寅", "甲子")


# ---------------------------------------------------------------------------
# 6. Эталонные персоны T1–T4 (умолчания: chaibu, true, early, kun, baihu)
# ---------------------------------------------------------------------------

def test_t1():
    r = calculate(T1)
    assert r["pillars"] == {"year": "庚午", "month": "辛巳", "day": "庚辰", "hour": "癸未", "day_date": "1990-05-15"}
    assert r["ju"]["label"] == "阳遁4局 立夏上元"
    assert r["zhi_fu"]["star"] == "天禽" and r["zhi_fu"]["palace"] == 9 and r["zhi_fu"]["carried_by"] == "天芮"
    assert r["zhi_shi"]["door"] == "死门" and r["zhi_shi"]["palace_raw"] == 5 and r["zhi_shi"]["palace"] == 2
    assert r["xun"]["head"] == "甲戌" and r["xun"]["kong_hour"] == ["申", "酉"]
    assert r["horse"] == {"branch": "巳", "palace": 4}
    assert r["patterns"]["door_fuyin"] and not r["patterns"]["star_fuyin"]
    assert r["natal"]["ming_palace_heaven"] == 7 and r["natal"]["ming"]["star"] == "天心"
    assert r["alternatives"]["ju_methods"] == {"chaibu": "阳遁4局 立夏上元", "zhirun": "阳遁5局 小满上元",
                                               "maoshan": "阳遁1局 立夏中元"}


def test_t2_lichun_and_zi_hour():
    r = calculate(T2)                              # истинное солнечное 22:46 → час 亥
    assert r["pillars"]["day"] == "戊辰" and r["pillars"]["hour"] == "癸亥"
    assert r["ju"]["label"] == "阳遁8局 立春上元"
    assert r["patterns"]["star_fuyin"] and r["patterns"]["door_fuyin"]
    alts = {(a["solar_time"], a["zi_hour"]): (a["day"], a["hour"], a["ju"]) for a in r["alternatives"]["time_bases"]}
    assert alts[("clock", "early")] == ("己巳", "甲子", "阳遁5局 立春中元")
    assert alts[("clock", "late")] == ("戊辰", "甲子", "阳遁8局 立春上元")
    assert any("立春" in w for w in r["warnings"])
    # 18:00 MSK — за 19 мин до Личуня: ещё 大寒
    assert calculate(BirthInput(1984, 2, 4, 18, 0, place="Москва"))["ju"]["term_used"]["cn"] == "大寒"


def test_t3():
    r = calculate(T3)
    assert r["pillars"]["day"] == "戊寅" and r["pillars"]["hour"] == "丙辰"
    assert r["ju"]["label"] == "阳遁3局 雨水下元"
    assert (r["zhi_fu"]["star"], r["zhi_fu"]["palace"], r["zhi_shi"]["door"], r["zhi_shi"]["palace"]) == ("天任", 1, "生门", 1)
    assert {"door": "生门", "palace": 1, "trigram": "坎"} in r["patterns"]["men_po"]


def test_t4_lmt():
    r = calculate(T4)
    assert r["inputs_used"]["offset_source"] == "LMT(longitude)"
    assert r["pillars"]["day"] == "丙申" and r["pillars"]["hour"] == "甲午"
    assert r["ju"]["label"] == "阳遁1局 惊蛰上元"
    assert r["patterns"]["star_fuyin"]                     # час 甲 — всегда 伏吟
    assert r["natal"]["year_stem"] == "己" and r["natal"]["ming_palace_heaven"] == 2


@pytest.mark.parametrize("b,clock_equiv,qd", [(T1, (1990, 5, 15, 13, 4), (5, 1)), (T3, (2004, 2, 29, 7, 3), (3, 6)),
                                              (T4, (1879, 3, 14, 11, 20), (1, 7))])
def test_t_subjects_equal_chart_time_snapshot(b, clock_equiv, qd):
    # карта T по истинному солнечному времени = карта «времени карты» в часах UTC+8 (тот же термин, день, час);
    # последняя сверена со снимком kinqimen 0.3.1 (KT_031) и с qimen-dunjia 3.1.0 для альтернатив:
    # T1: 符頭 → 小滿上元 5, 拆補 → 1; T3: 符頭 3, 拆補 6; T4: 符頭 1, 拆補 7.
    r = calculate(b)
    r2 = calculate(bj(*clock_equiv), **BJ)
    assert layout(r) == layout(r2) and r["ju"]["label"] == r2["ju"]["label"]
    alt = r["alternatives"]["ju_methods"]
    assert (int(alt["zhirun"][2]), int(alt["maoshan"][2])) == qd


@pytest.mark.parametrize("b", [T1, T2, T3, T4])
@pytest.mark.parametrize("st,zh",[("true", "late"), ("mean", "early"), ("clock", "late"), ("clock", "early")])
def test_pillars_match_bazi_module(b, st, zh):
    q = calculate(b, solar_time=st, zi_hour=zh)["pillars"]
    z = bazi.calculate(b, solar_time=st, zi_hour=zh)["pillars"]
    assert [q[k] for k in ("year", "month", "day", "hour")] == [z[k]["ganzhi"] for k in ("year", "month", "day", "hour")]


# ---------------------------------------------------------------------------
# 7. Инварианты
# ---------------------------------------------------------------------------

def _random_inputs(n=120, seed=16):
    rnd = random.Random(seed)
    zones = ["Europe/Moscow", "Asia/Shanghai", "America/New_York", "Australia/Sydney", "UTC+08:00"]
    for _ in range(n):
        yield BirthInput(rnd.randint(1900, 2050), rnd.randint(1, 12), rnd.randint(1, 28), rnd.randint(0, 23),
                         rnd.randint(0, 59), tz=rnd.choice(zones), lon=rnd.uniform(-170, 170))


@pytest.mark.parametrize("method", ["chaibu", "zhirun", "maoshan"])
def test_invariants(method):
    for b in _random_inputs(60 if method == "zhirun" else 120):
        r = calculate(b, ju_method=method, deities="baihu")
        p = palaces(r)
        earth = [x["earth_stem"] for x in p.values()]
        heaven = [s for x in p.values() for s in x["heaven_stems"]]
        nine = sorted(STEMS[s][0] for s in STEM_ORDER)
        assert sorted(earth) == nine                         # каждый из 9 стволов на земном диске один раз
        assert sorted(heaven) == nine                        # и на небесном (天禽 несёт ствол центра)
        assert sorted(x["star_home"] for q, x in p.items() if q != 5) == sorted(RING)
        assert sorted(x["door_home"] for q, x in p.items() if q != 5) == sorted(RING)
        assert sorted(x["hidden_stem"] for x in p.values()) == nine
        # 值符 стоит там, где ствол часа на земном диске (центр → 坤2)
        hs = r["pillars"]["hour"][0]
        eff = r["xun"]["yi"] if hs == "甲" else hs
        tgt = next(q for q, x in p.items() if x["earth_stem"] == eff)
        assert r["zhi_fu"]["palace"] == (2 if tgt == 5 else tgt)
        assert p[r["zhi_fu"]["palace"]]["deity"] == "值符"
        assert p[r["zhi_fu"]["palace"]]["star_home"] == (2 if r["zhi_fu"]["home_palace"] == 5 else r["zhi_fu"]["home_palace"])
        # ствол-укрытие 甲 часа (旬首仪) приходит на небесном диске в дворец 值符
        assert r["xun"]["yi"] in p[r["zhi_fu"]["palace"]]["heaven_stems"]
        # 值使: смещение по числам Ло Шу на номер часа в декаде
        yang = r["ju"]["dun"] == "yang"
        home = r["zhi_shi"]["home_palace"]
        steps = r["xun"]["hour_position"]
        raw = ((home - 1 + (steps if yang else -steps)) % 9) + 1
        assert r["zhi_shi"]["palace_raw"] == raw and p[r["zhi_shi"]["palace"]]["door"] == r["zhi_shi"]["door"]
        # звёзды и двери сохраняют порядок по часовой стрелке
        for key in ("star_home", "door_home"):
            seq = [p[q][key] for q in RING]
            i0 = RING.index(seq[0])
            assert seq == [RING[(i0 + i) % 8] for i in range(8)]
        # духи: 阳 по часовой, 阴 против
        names = ["值符", "腾蛇", "太阴", "六合", "白虎", "玄武", "九地", "九天"]
        start = RING.index(r["zhi_fu"]["palace"])
        for i, nm in enumerate(names):
            q = RING[(start + i) % 8] if yang else RING[(start - i) % 8]
            assert p[q]["deity"] == nm
        # 局 = таблица по термину и юаню
        k = r["ju"]["term_used"]["index"]
        assert r["ju"]["number"] == JU_TABLE[k][["upper", "middle", "lower"].index(r["ju"]["yuan"])]
        assert (k < 12) == yang
        json.dumps(r, ensure_ascii=False)


def test_chaibu_yuan_by_futou_cycle():
    # 符头 甲子/己卯/甲午/己酉 (子午卯酉) → 上元; 甲寅/甲申/己巳/己亥 → 中元; 甲辰/甲戌/己丑/己未 → 下元
    from calculators.qimen import yuan_by_futou, futou_index
    for i in range(60):
        f = futou_index(i)
        assert STEMS[f % 10][0] in "甲己" and 0 <= i - f <= 4
        b = bazi.BRANCHES[f % 12][0]
        assert yuan_by_futou(i) == ("子午卯酉".find(b) < 0) + ("辰戌丑未".find(b) >= 0)


def test_tianqin_kun_gen_variant():
    # 《統宗》: «天禽陽遁陰遁俱寄坤宫，一本陽遁寄坤宫陰遁寄艮宫». 阴遁, 旬首仪 в центре: 值使 = 生门 (艮8).
    ch = build_chart(False, 9, 40, tianqin="kun_gen")      # 阴9: 壬 в центре; час 甲辰
    assert ch["p0"] == 5 and ch["ji_gong"] == 8 and DOORS[ch["door_src"]][0] == "生门"
    assert 5 in ch["star_at"][8]                            # 天禽 вместе с 天任
    ch2 = build_chart(False, 9, 40)                         # умолчание: 寄坤 → 死门
    assert DOORS[ch2["door_src"]][0] == "死门" and 5 in ch2["star_at"][2]


def test_deity_variants():
    r = calculate(bj(1589, 12, 13, 4), ju_method="zhirun", deities="split", **BJ)   # 阴遁 → 白虎/玄武
    names = {x["deity"] for x in r["palaces"] if x["deity"]}
    assert "白虎" in names and "勾陈" not in names
    r = calculate(bj(1589, 2, 16, 10), ju_method="zhirun", deities="split", **BJ)   # 阳遁 → 勾陈/朱雀
    names = {x["deity"] for x in r["palaces"] if x["deity"]}
    assert "勾陈" in names and "白虎" not in names


# ---------------------------------------------------------------------------
# 8. Без времени, опции, сериализация
# ---------------------------------------------------------------------------

def test_no_time_day_level():
    r = calculate(BirthInput(1990, 5, 15, place="Москва"))
    assert r["inputs_used"]["has_time"] is False and r["chart"] is None
    assert r["ju"]["label"] == "阳遁4局 立夏上元" and r["pillars"]["hour"] is None
    assert any("нужен час" in w for w in r["warnings"])
    c = r["hour_candidates"]
    # Истинное солнечное время Москвы (MSD) отстаёт от часов на ~1 ч 26 мин: местные 00:00–00:26 — ещё 亥
    # предыдущего дня (己卯), далее 丙子…丁亥 дня 庚辰 → 13 вариантов, покрывающих сутки по часам без дыр.
    assert len(c) == 13 and (c[0]["day_pillar"], c[0]["hour_pillar"], c[0]["clock_hours"]) == ("己卯", "乙亥", "00:00–00:26")
    assert (c[1]["hour_pillar"], c[1]["hours"], c[1]["clock_hours"]) == ("丙子", "23:00–01:00", "00:26–02:26")
    assert c[-1]["clock_hours"].endswith("24:00") and c[0]["clock_hours"].startswith("00:00")
    assert all(a["clock_hours"].split("–")[1] == b["clock_hours"].split("–")[0] for a, b in zip(c, c[1:]))
    # Время часов + early: 23:00–24:00 — уже следующий день (辛巳, 戊子); с late — тот же день, ствол часа от следующего
    c = calculate(BirthInput(1990, 5, 15, place="Москва"), solar_time="clock")["hour_candidates"]
    assert len(c) == 13 and c[0]["hour_pillar"] == "丙子" and (c[-1]["day_pillar"], c[-1]["hour_pillar"]) == ("辛巳", "戊子")
    c = calculate(BirthInput(1990, 5, 15, place="Москва"), solar_time="clock", zi_hour="late")["hour_candidates"]
    assert (c[-1]["day_pillar"], c[-1]["hour_pillar"], c[-1]["clock_hours"]) == ("庚辰", "戊子", "23:00–24:00")
    # День Личуня (T2): 局 меняется в 18:19 MSK (термин) и в 23:44 (истинный 23:00 → день 己巳 при early)
    r = calculate(BirthInput(1984, 2, 4, place="Москва"))
    assert [(v["local_from"], v["local_to"], v["ju"]) for v in r["ju"]["variants_in_day"]] == [
        ("00:00", "18:19", "阳遁3局 大寒上元"), ("18:19", "23:44", "阳遁8局 立春上元"), ("23:44", "24:00", "阳遁5局 立春中元")]
    assert r["ju"]["label"] == "阳遁8局 立春上元"       # 局 дня 戊辰 — на последнюю минуту с этим столпом дня
    assert any("局 меняется" in w for w in r["warnings"])
    r = calculate(BirthInput(1984, 2, 4, place="Москва"), solar_time="clock", zi_hour="late")
    assert [v["ju"] for v in r["ju"]["variants_in_day"]] == ["阳遁3局 大寒上元", "阳遁8局 立春上元"]
    json.dumps(r, ensure_ascii=False)


@pytest.mark.parametrize("b,opts", [
    (BirthInput(1984, 2, 4, place="Москва"), {}),
    (BirthInput(1984, 2, 4, place="Москва"), {"solar_time": "clock", "zi_hour": "late"}),
    (BirthInput(1990, 5, 15, place="Москва"), {"ju_method": "maoshan"}),     # граница 10 сут 茅山 в 22:36
    (BirthInput(1718, 6, 29, tz="UTC+08:00"), {"ju_method": "zhirun"}),
])
def test_no_time_candidates_match_timed_chart(b, opts):
    """Каждый вариант без времени = расчёт с конкретным временем из его диапазона clock_hours (середина)."""
    for c in calculate(b, **opts)["hour_candidates"]:
        s, e = c["clock_hours"].split("–")
        m0 = int(s[:2]) * 60 + int(s[3:])
        m1 = int(e[:2]) * 60 + int(e[3:])
        mid = (m0 + m1) // 2
        r = calculate(replace(b, hour=mid // 60, minute=mid % 60), **opts)
        assert (r["pillars"]["day"], r["pillars"]["hour"], r["ju"]["label"]) == (c["day_pillar"], c["hour_pillar"], c["ju"])
        assert (r["zhi_fu"]["star"], r["zhi_fu"]["palace"], r["zhi_shi"]["door"], r["zhi_shi"]["palace"]) == (
            c["zhi_fu_star"], c["zhi_fu_palace"], c["zhi_shi_door"], c["zhi_shi_palace"])


def test_no_time_pre_1645_warning():
    r = calculate(BirthInput(1589, 12, 13, tz="UTC+08:00"), ju_method="zhirun")
    assert any("1645" in w for w in r["warnings"]) and r["ju"]["label"] == "阴遁4局 大雪闰上元"


def test_zhirun_threshold_dependence_is_warned():
    # 《統宗» 1718: при пороге 8 — 闰 (芒种闰上元), при 9 — уже 夏至 (7,7 % дней 1900–2100 зависят от порога)
    r = calculate(bj(1718, 6, 14, 12), ju_method="zhirun", **BJ)
    assert r["ju"]["label"] == "阳遁6局 芒种闰上元"
    assert r["alternatives"]["zhirun_other_threshold"] == {"zhirun_leap_days": 9, "label": "阴遁9局 夏至上元"}
    assert any("порога 置闰" in w for w in r["warnings"])
    assert calculate(T1)["alternatives"]["zhirun_other_threshold"] is None


@pytest.mark.parametrize("opt", [{"ju_method": "x"}, {"solar_time": "x"}, {"zi_hour": "x"}, {"tianqin": "x"},
                                 {"deities": "x"}, {"zhirun_leap_days": 0}])
def test_bad_options(opt):
    with pytest.raises(ValueError):
        calculate(T1, **opt)


def test_cli_boolean_solar_time():
    # CLI превращает 'true' в True — должно работать как в модуле 01
    assert calculate(T1, solar_time=True)["inputs_used"]["options"]["solar_time"] == "true"


def test_no_lon_falls_back_to_clock():
    r = calculate(BirthInput(1990, 5, 15, 14, 30, tz="Europe/Moscow"))
    assert r["inputs_used"]["options"]["solar_time"] == "clock"
    assert any("Долгота неизвестна" in w for w in r["warnings"])


def test_steps_and_json():
    r = calculate(T1)
    assert r["method"] == "qimen" and "chaibu" in r["variant"]
    assert len(r["steps"]) >= 12 and r["steps"][-1].startswith("Итог")
    s = json.dumps(r, ensure_ascii=False)
    assert "值符" in s and "值使" not in r["warnings"]


# ---------------------------------------------------------------------------
# 9. Повторная проверка (приоритет 1): 平气, «гибрид» 《遁甲演義》/李氏, граница термина по 时辰,
#    阴盘 王凤麟, 隐干 王凤麟, 三奇入墓
# ---------------------------------------------------------------------------

from calculators.qimen import _patterns, ju_chaibu, ju_hybrid, term_start  # noqa: E402

BJL = dict(tz="UTC+08:00", lat=39.9, lon=116.4)        # 北京, местное среднее время (как в 授时历/大统历)
PING = dict(solar_time="mean", qi="ping")


def bjl(y, m, d, h, mi=0):
    return BirthInput(y, m, d, h, mi, **BJL)


def _lmt_day_branch(jd_ut):
    """(день-ганьчжи, ветвь часа, часы) по местному среднему времени Пекина (116,4° в. д.)."""
    loc = jd_ut + 116.4 / 360.0 + 0.5
    jdn = int(loc // 1)
    h = (loc - jdn) * 24
    return bazi.ganzhi((jdn + 49) % 60), bazi.BRANCHES[int(((h + 1) % 24) // 2)][0], h


@pytest.mark.parametrize("k,approx,day,branch", [
    # 《明史·曆志一》 (https://zh.wikisource.org/wiki/明史/卷31): «乃以推壬申冬至，《大統》得己亥寅正一刻»
    (0, (1631, 12, 21), "己亥", "寅"),
    # 《遁甲演義》 «又引證» (https://zh.wikisource.org/wiki/遁甲演義): «萬曆二十四年丙申，正月初九日丑時立春…
    # 初九丙子日…二十四日辛卯日辰時雨水…初九日丙午日午時驚蟄節…至二十四辛酉日申時止» (春分 — 酉時)
    (3, (1596, 2, 5), "丙子", "丑"), (4, (1596, 2, 20), "辛卯", "辰"), (5, (1596, 3, 6), "丙午", "午"),
    (6, (1596, 3, 21), "辛酉", "酉"),
    # «萬曆二十六年戊戌正月初八甲午日…十五日戌時雨水» (正月十五 = 辛丑)
    (4, (1598, 2, 19), "辛丑", "戌"),
    # «萬曆二十七年己亥，五月十七甲子日子時小暑節»; «初四庚辰日丑時秋分»
    (13, (1599, 7, 7), "甲子", "子"), (18, (1599, 9, 22), "庚辰", "丑"),
    # «萬曆二十九年辛丑…五月初七甲辰日丑時，交芒種節»
    (11, (1601, 6, 6), "甲辰", "丑"),
    # 《演義» 1346: «丙戌年五月初一日己卯，至初九日…芒種» (初九 = 丁亥), «二十四日已交夏至» (壬寅)
    (11, (1346, 6, 6), "丁亥", None), (12, (1346, 6, 21), "壬寅", None),
    # 黄宗羲 «超神接氣直指»: «本月初六日交雨水節» (正月初六 = 甲寅 20.02.1589); «冬至…十四日戊午»
    (4, (1589, 2, 19), "甲寅", None), (0, (1589, 12, 21), "戊午", None),
])
def test_pingqi_datong_model_matches_ming_calendar(k, approx, day, branch):
    jd = swe.julday(*approx, 12.0) + 5.0
    g, br, h = _lmt_day_branch(term_start(k, jd, "ping"))
    assert g == day
    if branch:
        assert br == branch
    if approx[0] == 1631:
        assert abs(h - 4.25) < 0.2                      # «寅正一刻» = 04:15
    # 定气 в этих случаях часто даёт другой день (平气 и 定气 расходятся до 2 сут)
    if (k, approx) in ((3, (1596, 2, 5)), (0, (1589, 12, 21))):
        assert _lmt_day_branch(term_start(k, jd, "ding"))[0] != day


@pytest.mark.parametrize("t,label", [
    # 《遁甲演義» «又引證», 1596: 接气 по 拆补 (殘局/補局) — каждый отрезок текста.
    ((1596, 2, 6, 0, 30), "阳遁6局 大寒下元"),     # «初九丙子日戊子時還是先年大寒下局»
    ((1596, 2, 6, 1, 30), "阳遁2局 立春下元"),     # «自丑時至亥…俱借立春下局．陽二遁…此為殘局» (термин 02:28, весь 丑)
    ((1596, 2, 8, 22, 0), "阳遁2局 立春下元"),
    ((1596, 2, 8, 23, 30), "阳遁8局 立春上元"),    # «十二己卯日符頭，才到甲子時起…立春上局，陽遁八宮»
    ((1596, 2, 14, 12), "阳遁5局 立春中元"),        # «十七甲申日換局…立春中局。陽五遁中宮»
    ((1596, 2, 19, 0, 30), "阳遁2局 立春下元"),    # «二十二日，己丑日甲子時至辛卯日卯時止…補足前立春下局»
    ((1596, 2, 21, 6, 30), "阳遁2局 立春下元"),
    ((1596, 2, 21, 7, 30), "阳遁3局 雨水下元"),    # «辛卯日辰時雨水…俱借雨水下局，陽三遁震宮»
    ((1596, 2, 24, 0, 30), "阳遁9局 雨水上元"),    # «二十七甲午日符頭方到…雨水上局，陽九遁離宮»
    ((1596, 2, 29, 12), "阳遁6局 雨水中元"),        # «二月初二己亥日…雨水中局，陽六遁乾宮»
    ((1596, 3, 5, 12), "阳遁3局 雨水下元"),         # «初七甲辰日…補足前雨水下局»
    ((1596, 3, 7, 11, 20), "阳遁4局 惊蛰下元"),    # «初九日丙午日午時驚蟄節…驚蟄下局，陽四巽宮…此為殘局»
    ((1596, 3, 10, 12), "阳遁1局 惊蛰上元"),        # «十二己酉日符頭始到…驚蟄上局，陽一遁坎宮»
    ((1596, 3, 15, 12), "阳遁7局 惊蛰中元"),        # «十七甲寅日…驚蟄中局，陽七遁兑宮»
    ((1596, 3, 22, 16, 0), "阳遁4局 惊蛰下元"),    # «二十二己未日…至二十四辛酉日申時止…補足前驚蟄所少下局»
    ((1596, 3, 22, 17, 30), "阳遁6局 春分下元"),   # 春分 в 酉時 辛酉 → 殘局 春分下元
])
def test_yanyi_1596_hybrid_hour_by_hour(t, label):
    # Часы UTC+8 подобраны так, чтобы местное среднее время Пекина попадало в названный 时辰.
    r = calculate(bjl(*t), ju_method="hybrid", term_boundary="hour", **PING)
    assert r["ju"]["label"] == label
    # Чистый 置闰 даёт в окнах 殘局 старый термин («初一至初四仍行大寒下元» — 《統宗»), т.е. 1596 г. у 《演義» — не он:
    if t in ((1596, 2, 6, 1, 30), (1596, 2, 21, 7, 30)):
        assert calculate(bjl(*t), ju_method="zhirun", **PING)["ju"]["label"] != label
        assert r["ju"]["hybrid_canju"]["canju"] is True


def test_term_boundary_hour_only_moves_term_inside_its_hour():
    # 雨水 1596 — 07:43 по местному среднему времени; 07:15 (辰) по моменту — ещё 立春, по 时辰 — уже 雨水
    b = bjl(1596, 2, 21, 7, 30)
    assert calculate(b, **PING)["ju"]["term_used"]["cn"] == "立春"
    assert calculate(b, term_boundary="hour", **PING)["ju"]["term_used"]["cn"] == "雨水"
    assert calculate(T1, term_boundary="hour")["ju"]["label"] == calculate(T1)["ju"]["label"]


@pytest.mark.parametrize("d,label,state,chao", [
    # 《遁甲演義»: «十一月…十三甲午日疊作大雪節，此名閏奇…至萬曆二十七年己亥五月十七甲子日子時，正交小暑節，
    # 此名正授奇也…八月初三己卯日，符頭已到，初四秋分，乃符先到而節氣後到，又當超用…四月二十七甲午日，超用芒種，
    # 五月初七甲辰日丑時，交芒種節，已超過十日…五月十二己酉日，疊起又作芒種節上局，陽六遁，乾宫»
    (date(1598, 12, 25), "阳遁1局 冬至上元", "jieqi", -3),
    (date(1599, 7, 8), "阴遁8局 小暑上元", "zhengshou", 0),
    (date(1599, 9, 21), "阴遁7局 秋分上元", "chaoshen", 1),
    (date(1601, 5, 28), "阳遁6局 芒种上元", "chaoshen", 10),
    (date(1601, 6, 12), "阳遁6局 芒种闰上元", "leap", 10),
    (date(1601, 6, 27), "阴遁9局 夏至上元", "jieqi", -5),
])
def test_yanyi_1598_1601_zhirun_pingqi(d, label, state, chao):
    r = calculate(bjl(d.year, d.month, d.day, 12), ju_method="zhirun", **PING)
    assert (r["ju"]["label"], r["ju"]["zhirun"]["state"], r["ju"]["zhirun"]["chao_days"]) == (label, state, chao)


def test_yanyi_1598_known_divergence():
    # 《演義» проводит 1598 г. без 闰 у 夏至 (符头 13.06 甲午, 夏至 22.06 — разность 9) и ставит 闰 только у 大雪
    # («十月二十七己卯日超用大雪…已過十一日，合當置閏»). Порог 8 (и 9) даёт 闰 уже у 夏至 1598 — это противоречит
    # его же примеру 1346 г. (разность 8 → 闰). Расхождение зафиксировано (§1.3), с 10.12.1598 局 снова совпадают.
    r = calculate(bjl(1598, 6, 13, 12), ju_method="zhirun", **PING)
    assert r["ju"]["leap"] and r["ju"]["zhirun"]["chao_days"] == 9
    assert calculate(bjl(1598, 12, 10, 12), ju_method="zhirun", **PING)["ju"]["number"] == 4   # книга: 大雪閏上 阴4


@pytest.mark.parametrize("qi", ["ding", "ping"])
def test_yanyi_1346_leap(qi):
    # 《演義»: «丙戌年五月初一日己卯，至初九日…芒種，奇超九日，則當置閏，即用初一日己卯作芒種上超局…以十六日甲午作
    # 芒種閏奇…二十四日已交夏至…至六月初二己酉，方作夏至上局，初七日甲寅，作夏至中局». 1346 г. (至正六年).
    opts = dict(ju_method="zhirun", solar_time="mean", qi=qi)
    assert calculate(bjl(1346, 5, 30, 12), **opts)["ju"]["label"] == "阳遁6局 芒种上元"
    r = calculate(bjl(1346, 6, 14, 12), **opts)
    assert r["ju"]["label"] == "阳遁6局 芒种闰上元" and r["ju"]["zhirun"]["chao_days"] == 8
    assert calculate(bjl(1346, 6, 29, 12), **opts)["ju"]["label"] == "阴遁9局 夏至上元"
    assert calculate(bjl(1346, 7, 4, 12), **opts)["ju"]["label"] == "阴遁3局 夏至中元"
    # порог 9 этот 闰 пропускает — ещё один довод за 8
    assert not calculate(bjl(1346, 6, 14, 12), zhirun_leap_days=9, **opts)["ju"]["leap"]


def test_huang_zongxi_counts_with_pingqi():
    # С 平气 (大统历) и местным временем Пекина: «初六日交雨水» → 超 5 дн. от 符头 己酉 (正月初一);
    # «不知符已超節九日» → разность 冬至 (十四日戊午) − 符头 (初五日己酉) = 9 — ровно как у автора (с 定气 — 10).
    r = calculate(bjl(1589, 2, 16, 10), ju_method="zhirun", deities="gouchen", **PING)
    assert r["ju"]["label"] == "阳遁9局 雨水上元" and r["ju"]["zhirun"]["chao_days"] == 5
    r = calculate(bjl(1589, 12, 13, 4), ju_method="zhirun", deities="gouchen", **PING)
    assert r["ju"]["label"] == "阴遁4局 大雪闰上元" and r["ju"]["zhirun"]["chao_days"] == 9
    assert calculate(bjl(1589, 12, 13, 4), ju_method="zhirun", solar_time="mean")["ju"]["zhirun"]["chao_days"] == 10
    # предупреждение и альтернатива для дат до 1645 г.
    r = calculate(bjl(1589, 2, 16, 10), ju_method="zhirun", solar_time="mean")
    assert r["alternatives"]["qi_other"]["qi"] == "ping" and any("qi='ping'" in w for w in r["warnings"])


def test_hybrid_is_zhirun_except_canju_window():
    """hybrid = 置闰, кроме окна 殘局: там термин — следующий за блоком (= 拆补 по моменту), юань 下."""
    clock = _Clock("UTC+08:00", "fixed", 8.0, None, "clock")
    rnd = random.Random(16)
    n_canju = 0
    for _ in range(300):
        d = date(1950, 1, 1) + timedelta(days=rnd.randrange(80 * 365))
        jd = swe.julday(d.year, d.month, d.day, rnd.uniform(0, 23.9) - 8.0)
        h = ju_hybrid(jd, d, clock, 8)
        z = ju_zhirun(d, jd, clock, 8)
        if not h["canju"]:
            assert (h["term"], h["yuan"], h["leap"]) == (z["term"], z["yuan"], z["leap"])
        else:
            n_canju += 1
            assert h["term"] == (z["term"] + 1) % 24 and h["yuan"] == 2 and not z["leap"]
            assert h["term"] == ju_chaibu(jd, bazi.day_index(d))["term"]
    assert n_canju > 5


WFL = "https://archive.org/details/wfl-002.-2009-381"   # 王凤麟, 2009, гл. 2 «阴盘遁甲的定局排盘» и разборы


def test_yinpan_wangfenglin_full_chart():
    # WFL, с. 41–53: «2006年5月23日19时45分，农历:四月廿六日…年支戌序数为11，四月廿六为4+26，时支戌序数为11，
    # 所以(11+4+26+11)/9余数为7…定为阳局，所以此局为阳7局»; «阳七局，甲辰壬，天芮星为值符，死门为值使»;
    # «死门落艮八宫后，惊门落震宫，开门落巽宫，休门落离宫，生门落坤宫，伤门落兑宫，杜门落乾宫，景门落坎宫»;
    # 八神 «值符,腾蛇,太阴,六合,白虎,玄武,九地,九天…阳遁顺时…阴遁逆时»; 隐干 «时干加在值使门上，然后按照天盘的
    # 顺序…排列一圈».
    r = calculate(BirthInput(2006, 5, 23, 19, 45, tz="UTC+08:00"), ju_method="yinpan", solar_time="clock")
    assert r["ju"]["label"] == "阳遁7局 阴盘" and r["ju"]["yinpan"]["lunar"]["sum"] == 52
    assert (r["zhi_fu"]["star"], r["zhi_shi"]["door"], r["zhi_shi"]["palace"]) == ("天芮", "死门", 8)
    p = palaces(r)
    assert {k: v["door"] for k, v in p.items() if k != 5} == {
        8: "死门", 3: "惊门", 4: "开门", 9: "休门", 2: "生门", 7: "伤门", 6: "杜门", 1: "景门"}
    assert {k: v["star"] for k, v in p.items() if k != 5} == {
        4: "天英", 9: "天芮", 2: "天柱", 3: "天辅", 7: "天心", 8: "天冲", 1: "天任", 6: "天蓬"}
    assert {k: "".join(v["heaven_stems"]) for k, v in p.items() if k != 5} == {
        4: "庚", 9: "壬丙", 2: "戊", 3: "丁", 7: "乙", 8: "癸", 1: "己", 6: "辛"}
    assert {k: v["deity"] for k, v in p.items() if k != 5} == {
        9: "值符", 2: "腾蛇", 7: "太阴", 6: "六合", 1: "白虎", 8: "玄武", 3: "九地", 4: "九天"}
    # 隐干 на рисунке книги: 巽 戊, 離 乙, 坤 辛, 震 壬丙, 兑 己, 艮 庚, 乾 癸 (坎 — 丁)
    assert {k: v["hidden_stem"] for k, v in p.items()} == {
        4: "戊", 9: "乙", 2: "辛", 3: "壬丙", 5: None, 7: "己", 8: "庚", 1: "丁", 6: "癸"}


@pytest.mark.parametrize("t,label", [
    # WFL: «公元:…» и «…阳/阴N局» разобранных случаев (часы — пекинские, UTC+8)
    ((2007, 5, 16, 17, 48), "阳遁1局 阴盘"), ((2007, 6, 8, 9, 8), "阳遁9局 阴盘"),
    ((2007, 8, 24, 13, 20), "阴遁3局 阴盘"), ((2007, 9, 17, 11, 14), "阴遁7局 阴盘"),
    ((2008, 10, 14, 9, 37), "阴遁5局 阴盘"), ((2008, 10, 16, 11, 19), "阴遁8局 阴盘"),
    ((2008, 8, 1, 12, 10), "阴遁7局 阴盘"), ((2008, 8, 28, 17, 41), "阴遁1局 阴盘"),
    ((2008, 10, 19, 13, 11), "阴遁3局 阴盘"), ((2006, 1, 18, 12, 57), "阳遁3局 阴盘"),
    ((2007, 11, 19, 12, 51), "阴遁3局 阴盘"), ((2007, 12, 3, 13, 51), "阴遁9局 阴盘"),
    ((2008, 6, 6, 21, 40), "阳遁3局 阴盘"), ((2007, 4, 13, 17, 10), "阳遁5局 阴盘"),
    ((2007, 4, 13, 19, 32), "阳遁6局 阴盘"), ((2007, 12, 14, 15, 29), "阴遁1局 阴盘"),
    ((2007, 12, 23, 9, 30), "阳遁7局 阴盘"), ((2007, 12, 24, 10, 14), "阳遁8局 阴盘"),
    ((2008, 9, 8, 8, 39), "阴遁5局 阴盘"), ((2007, 5, 14, 21, 8), "阳遁1局 阴盘"),
])
def test_yinpan_wangfenglin_ju(t, label):
    assert calculate(BirthInput(*t, tz="UTC+08:00"), ju_method="yinpan", solar_time="clock")["ju"]["label"] == label


@pytest.mark.parametrize("t,hidden", [
    # 隐干 на рисунках WFL (читаемые клетки)
    ((2007, 5, 16, 17, 48), {4: "乙", 3: "辛", 8: "庚", 6: "戊", 9: "己壬", 1: "丙"}),
    ((2007, 6, 8, 9, 8), {8: "丁", 3: "己", 4: "乙", 9: "辛", 2: "壬", 7: "戊", 6: "庚癸"}),
    ((2008, 10, 14, 9, 37), {4: "丙", 2: "壬", 3: "辛戊", 8: "癸", 6: "庚", 9: "乙"}),
])
def test_hidden_stems_ring_wangfenglin(t, hidden):
    p = palaces(calculate(BirthInput(*t, tz="UTC+08:00"), ju_method="yinpan", solar_time="clock"))
    assert {k: p[k]["hidden_stem"] for k in hidden} == hidden
    # правило kinqimen (luoshu) даёт другое — это разные школы
    p2 = palaces(calculate(BirthInput(*t, tz="UTC+08:00"), ju_method="yinpan", solar_time="clock",
                           hidden_stems="luoshu"))
    assert {k: p2[k]["hidden_stem"] for k in hidden} != hidden


def test_san_qi_ru_mu_yanyi_example():
    # 《遁甲演義»: «假如陰遁四局，丙辛日庚寅時六丙月奇下臨六宮，是謂月奇入墓»
    hour = next(i for i in range(60) if bazi.ganzhi(i) == "庚寅")
    pat = _patterns(build_chart(False, 4, hour))
    assert {"stem": "丙", "palace": 6, "trigram": "乾"} in pat["san_qi_ru_mu"]
    # T1: 天盘 — 乙 в 艮8, 丙 в 离9, 丁 в 乾6 → по основному правилу入墓 нет, по варианту (丁→乾) есть
    r = calculate(T1)
    assert r["patterns"]["san_qi_ru_mu"] == []
    assert r["patterns"]["san_qi_ru_mu_variant"] == [{"stem": "丁", "palace": 6, "trigram": "乾"}]


def test_new_options_keep_defaults():
    base = calculate(T1)
    same = calculate(T1, qi="ding", term_boundary="moment", hidden_stems="luoshu")
    assert layout(base) == layout(same) and base["ju"] == same["ju"]
    assert set(base["alternatives"]["ju_methods"]) == {"chaibu", "zhirun", "maoshan"}
    assert set(base["alternatives"]["ju_methods_extra"]) == {"hybrid", "yinpan"}
    assert base["alternatives"]["qi_other"] is None
    assert "qi='ping'" not in base["variant"]
    for opt in ({"qi": "x"}, {"term_boundary": "x"}, {"hidden_stems": "x"}):
        with pytest.raises(ValueError):
            calculate(T1, **opt)


@pytest.mark.parametrize("b,opts", [
    (BirthInput(1596, 2, 21, **BJL), {"ju_method": "hybrid", "term_boundary": "hour", **PING}),
    (BirthInput(2006, 5, 23, tz="UTC+08:00"), {"ju_method": "yinpan", "solar_time": "clock"}),
])
def test_no_time_candidates_new_methods(b, opts):
    for c in calculate(b, **opts)["hour_candidates"]:
        s, e = c["clock_hours"].split("–")
        m0 = int(s[:2]) * 60 + int(s[3:])
        m1 = int(e[:2]) * 60 + int(e[3:])
        mid = (m0 + m1) // 2
        r = calculate(replace(b, hour=mid // 60, minute=mid % 60), **opts)
        assert (r["pillars"]["day"], r["pillars"]["hour"], r["ju"]["label"]) == (c["day_pillar"], c["hour_pillar"], c["ju"])
