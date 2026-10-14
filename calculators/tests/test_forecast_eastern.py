"""Тесты модуля 19 — восточная прогностика на год/дату (calculators/forecast_eastern.py).

Фиксированная дата прогноза: 2026-10-14 (год 2026), чтобы тесты были детерминированы.

Внешние векторы (URL — в комментариях у каждого блока):
* lunar-python (6tail) — столпы года/месяца/дня, моменты цзе 2026 г. (UTC+8), звёзды года/месяца/дня.
* masterseanchan.com «Fengshui 2026 flying star chart» — 年盤 2026, 12 月盤 с моментами цзе (UTC+8),
  太歲/歲破/三煞 2026; страницы «San Sha» 2027 и 2029; skillon.com — «звёзды болезни» 2026 (5 — юг, 2 — СЗ).
* oggi.jp — 2026: 五黄殺 南, 暗剣殺 北, 歳破 北; ameblo.jp/ej3 — сентябрь 2026: 五黄殺 南, 暗剣殺 北, 月破 東.
* ja.wikipedia «九星気学» — определения 五黄殺/暗剣殺/歳破/本命殺/本命的殺/月命殺/定位対冲;
  ja.wikipedia «九星» — таблица 相生・比和 (吉方).
* global.hk01.com — 2026 犯太岁: 马 (值, 刑), 鼠 (冲), 牛 (害), 兔 (破).
* onlinejyotish.com — ингрессии Сатурна 2020–2052 (даты; аянамша и пояс на странице не названы — совпадение
  с Lahiri/IST получено расчётом).
* oggi.jp/6752236 — 2026年の吉方位 для всех 9 звёзд рождения (независимая сверка правил 吉方/凶方).
* zh.wikisource «滴天髓/09» — «子運午年，謂之運沖歲», «午運子年，謂之歲沖運», «丙運庚年，謂之運伐歲».
* astropatri.com — Юпитер → Рак 02.06.2026 02:25 IST, → Лев 31.10.2026 12:50 IST; Раху → Козерог 05.12.2026 19:28 IST.
* hindutone.com — Саде-сати 2026: Кумбха (последняя фаза), Мина (пик), Меша (начало); Аштама — Симха;
  Ардхаштама/Кантака — Дхану.
* «Пхаладипика» XXVI.2–8 (пер. V. Subrahmanya Sastri, 2-е изд. 1950, archive.org) — таблица гочары и ведхи.
"""
from __future__ import annotations

import json
from datetime import date, datetime, timedelta, timezone

import pytest
from lunar_python import Solar

from calculators import bazi as bz
from calculators import jyotish as jy
from calculators import ninestar as ns
from calculators.common.time import BirthInput, jd_to_utc, julian_day_ut
from calculators.forecast_eastern import (GOCHARA_GOOD, PALACE_PATH, VEDHA_EXEMPT, _pair_relations, bazi_months,
                                          calculate, chart_directions, flying_chart, lucky_stars, ninestar_months,
                                          saturn_periods, sign_segments, tai_sui_table)

ON = "2026-10-14"
UTC8 = timezone(timedelta(hours=8))
IST = timedelta(hours=5, minutes=30)
CN_NUM = {"一": 1, "二": 2, "三": 3, "四": 4, "五": 5, "六": 6, "七": 7, "八": 8, "九": 9}

T = {
    "T1": BirthInput(1990, 5, 15, 14, 30, place="Москва", gender="female"),
    "T2": BirthInput(1984, 2, 4, 23, 30, place="Москва", gender="male"),
    "T3": BirthInput(2004, 2, 29, 8, 15, place="Санкт-Петербург", gender="female"),
    "T4": BirthInput(1879, 3, 14, 11, 30, tz="LMT", lat=48.4011, lon=9.9876, gender="male"),
}


@pytest.fixture(scope="module")
def R() -> dict:
    return {k: calculate(b, on_date=ON, year=2026) for k, b in T.items()}


def _rel_types(rels: dict, key: str) -> set[str]:
    return {r["type"] for r in rels.get(key, [])}


def _jd_from_utc8(s: str) -> float:
    return julian_day_ut(datetime.strptime(s, "%Y-%m-%d %H:%M").replace(tzinfo=UTC8).astimezone(timezone.utc))


# ---------------------------------------------------------------------------
# 0. Структура результата
# ---------------------------------------------------------------------------

def test_result_structure_and_json(R):
    for k, r in R.items():
        json.dumps(r, ensure_ascii=False)
        for key in ("method", "variant", "inputs_used", "warnings", "steps", "bazi_year", "ninestar_year", "jyotish"):
            assert key in r, (k, key)
        assert r["method"] == "forecast_eastern"
        assert r["inputs_used"]["on_date"] == ON and r["inputs_used"]["year"] == 2026
        assert len(r["steps"]) >= 6


def test_sections_option_and_missing_data():
    r = calculate(T["T1"], on_date=ON, sections="bazi")
    assert r["bazi_year"] is not None and r["ninestar_year"] is None and r["jyotish"] is None
    # без пола: нет Столпа удачи, есть предупреждение
    b = BirthInput(1990, 5, 15, 14, 30, place="Москва")
    r = calculate(b, on_date=ON, sections=["bazi"])
    assert r["bazi_year"]["luck_pillar"] is None
    assert any("Пол не указан" in w for w in r["warnings"])
    # без времени: три столпа, расчёт не падает
    b = BirthInput(1990, 5, 15, place="Москва", gender="female")
    r = calculate(b, on_date=ON)
    assert r["bazi_year"]["natal"]["pillars"]["hour"] is None
    assert r["jyotish"] is not None and any("знак Луны" in w for w in r["warnings"])


def test_year_only_uses_li_chun_of_that_year():
    """Задан только year (вне текущего года) → «на дату» = Личунь + 1 ч."""
    r = calculate(T["T1"], year=1990, sections=["bazi"])
    assert r["inputs_used"]["year"] == 1990
    assert r["bazi_year"]["annual_pillar"]["ganzhi"] == "庚午"
    assert r["bazi_year"]["month_on_date"]["ganzhi"] == "戊寅"   # первый месяц 1990 (寅) — 五虎遁 от 庚
    assert any("Личунь + 1 ч" in w for w in r["warnings"])


# ---------------------------------------------------------------------------
# A. Ба-цзы
# ---------------------------------------------------------------------------

def test_annual_pillar_2026_and_li_chun(R):
    a = R["T1"]["bazi_year"]["annual_pillar"]
    assert a["ganzhi"] == "丙午"
    # Личунь 2026: 04.02.2026 04:02 UTC+8 (lunar-python, masterseanchan) = 03.02.2026 23:02 MSK
    assert a["li_chun_start"]["utc"] == "2026-02-03 20:02"
    assert a["li_chun_start"]["local"] == "2026-02-03 23:02"
    assert a["li_chun_end"]["utc"] == "2027-02-04 01:46"     # 04.02.2027 09:46 UTC+8


def test_year_boundary_li_chun_moscow():
    """Граничный случай: Личунь 2026 в Москве — 03.02 в 23:02. Полдень 03.02 ещё год 乙巳 (звезда 2)."""
    r = calculate(T["T1"], on_date="2026-02-03", sections=["bazi", "ninestar"])
    assert r["inputs_used"]["year"] == 2025
    assert r["bazi_year"]["annual_pillar"]["ganzhi"] == "乙巳"
    assert r["ninestar_year"]["year"]["star"] == 2
    assert r["bazi_year"]["month_on_date"]["ganzhi"] == "己丑"
    assert any("цзе" in w for w in r["warnings"])          # на эту дату приходится цзе
    r = calculate(T["T1"], on_date="2026-02-03", on_time="23:30", sections=["bazi"])
    assert r["inputs_used"]["year"] == 2026 and r["bazi_year"]["month_on_date"]["ganzhi"] == "庚寅"
    r = calculate(T["T1"], on_date="2026-02-04", sections=["bazi", "ninestar"])
    assert r["bazi_year"]["annual_pillar"]["ganzhi"] == "丙午" and r["ninestar_year"]["year"]["star"] == 1


def test_edge_warnings_li_chun_birth_and_jie_day():
    """Граничные случаи для агента: (1) рождение в день Личуня без времени — предупреждение модуля 03 о звезде
    года доходит до прогноза; (2) день цзе при sections='ninestar' — предупреждение о звезде месяца тоже есть."""
    r = calculate(BirthInput(1984, 2, 4, place="Москва", gender="male"), on_date=ON, sections="ninestar")
    assert any(w.startswith("Ки (натал):") and "Личун" in w for w in r["warnings"])
    r = calculate(T["T1"], on_date="2026-10-08", on_time="08:00", sections="ninestar")
    assert r["ninestar_year"]["month_on_date"]["star"] == 1                  # до 寒露 09:29 MSK — ещё 酉, звезда 1
    assert sum("цзе" in w for w in r["warnings"]) == 1
    r = calculate(T["T1"], on_date="2026-10-08", on_time="10:00")
    assert r["ninestar_year"]["month_on_date"]["star"] == 9 and r["bazi_year"]["month_on_date"]["ganzhi"] == "戊戌"
    assert sum("цзе" in w for w in r["warnings"]) == 1                        # одно, хотя считают оба блока


def test_luck_vs_year_direction_ditiansui():
    """https://zh.wikisource.org/wiki/滴天髓/09 : «如子運午年，謂之運沖歲»; «如午運子年，謂之歲沖運»;
    «如丙運庚年，謂之運伐歲»; «如庚運丙年，謂之歲伐運»; «如庚運辛年…申運酉年…則好»."""
    from calculators.forecast_eastern import _luck_vs_year
    gi = bz.ganzhi_index
    cn = lambda luck, year: {x["cn"] for x in _luck_vs_year(luck, year)}   # noqa: E731
    assert "沖 (運沖歲)" in cn(gi(0, 0), gi(2, 6))       # 甲子 удача, 丙午 год
    assert "沖 (歲沖運)" in cn(gi(2, 6), gi(0, 0))       # 丙午 удача, 甲子 год
    assert "戰 (運伐歲)" in cn(gi(2, 2), gi(6, 8))       # 丙寅 удача, 庚申 год
    assert "戰 (歲伐運)" in cn(gi(6, 8), gi(2, 2))
    assert "好" in cn(gi(6, 8), gi(7, 9))                 # 庚申 / 辛酉


# lunar-python: моменты цзе 2026 г. (UTC+8), `Lunar.getJieQiTable()`; совпадают до минуты с
# https://www.masterseanchan.com/fengshui-2026-flying-star-chart/ (колонка «Solar term start, UTC+8»)
JIE_2026_UTC8 = ["2026-02-04 04:02", "2026-03-05 21:59", "2026-04-05 02:40", "2026-05-05 19:48",
                 "2026-06-05 23:48", "2026-07-07 09:56", "2026-08-07 19:42", "2026-09-07 22:41",
                 "2026-10-08 14:29", "2026-11-07 17:52", "2026-12-07 10:52", "2027-01-05 22:09"]


def test_monthly_pillars_and_jie_vs_lunar_python():
    months = bazi_months(2026)
    table = Solar.fromYmd(2026, 7, 1).getLunar().getJieQiTable()
    names = ["立春", "惊蛰", "清明", "立夏", "芒种", "小暑", "立秋", "白露", "寒露", "立冬", "大雪", "XIAO_HAN"]
    for m, nm, pub in zip(months, names, JIE_2026_UTC8):
        s = table[nm]
        lp = datetime(s.getYear(), s.getMonth(), s.getDay(), s.getHour(), s.getMinute(), s.getSecond(),
                      tzinfo=UTC8).astimezone(timezone.utc)
        assert abs(m["start_jd"] - julian_day_ut(lp)) * 1440 < 1.0, nm
        assert abs(m["start_jd"] - _jd_from_utc8(pub)) * 1440 < 1.5, nm
        # столп месяца — через 10 суток после цзе, lunar-python получает время UTC+8
        mid = jd_to_utc(m["start_jd"] + 10).astimezone(UTC8)
        lun = Solar.fromYmdHms(mid.year, mid.month, mid.day, mid.hour, mid.minute, 0).getLunar()
        assert bz.ganzhi(m["index"]) == lun.getMonthInGanZhiExact(), nm
    assert [bz.ganzhi(m["index"]) for m in months] == ["庚寅", "辛卯", "壬辰", "癸巳", "甲午", "乙未", "丙申",
                                                       "丁酉", "戊戌", "己亥", "庚子", "辛丑"]


def test_month_and_day_on_date_vs_lunar_python(R):
    lun = Solar.fromYmdHms(2026, 10, 14, 17, 0, 0).getLunar()       # 12:00 MSK = 17:00 UTC+8
    b = R["T1"]["bazi_year"]
    assert b["month_on_date"]["ganzhi"] == lun.getMonthInGanZhiExact() == "戊戌"
    assert b["day_on_date"]["ganzhi"] == lun.getDayInGanZhiExact() == "辛酉"
    assert b["month_on_date"]["start"]["local"] == "2026-10-08 09:29"


def test_tai_sui_table_2026():
    """https://global.hk01.com/大国小事/60303627/ : 2026 犯太岁 — 马 (值太岁 + 午午自刑), 鼠 (冲), 牛 (害), 兔 (破)."""
    t = tai_sui_table(2026)
    assert t == {"zhi": ["午"], "chong": ["子"], "xing": ["午"], "hai": ["丑"], "po": ["卯"]}


def test_pair_relations_unit():
    gi = bz.ganzhi_index
    r = {x["type"]: x for x in _pair_relations(gi(0, 0), gi(6, 6))}       # 甲子 (внешний) против 庚午 (натал)
    assert {"stem_clash", "clash", "fan_yin"} <= set(r)
    assert r["fan_yin"]["controller"] == "natal"                          # 庚 подавляет 甲
    assert {x["type"] for x in _pair_relations(gi(2, 6), gi(2, 6))} >= {"fu_yin", "self_punishment"}  # 丙午/丙午
    assert {x["type"] for x in _pair_relations(gi(2, 6), gi(8, 0))} >= {"clash", "stem_clash", "fan_yin"}  # 丙午/壬子
    # 丙午 против 甲子: ветви сталкиваются, но 甲 порождает 丙 — не 天克地冲
    assert "fan_yin" not in {x["type"] for x in _pair_relations(gi(2, 6), gi(0, 0))}
    assert {x["type"] for x in _pair_relations(gi(0, 2), gi(7, 5))} >= {"harm", "punishment"}   # 甲寅/辛巳: 害 + 刑
    assert {x["type"] for x in _pair_relations(gi(3, 3), gi(4, 0))} == {"punishment"}          # 卯子: 无礼之刑


def test_fu_yin_with_annual_pillar():
    """Рождение в год 丙午 (1966): в 2026 годовой столп повторяет столп года — 伏吟."""
    r = calculate(BirthInput(1966, 6, 1, 12, 0, place="Москва", gender="male"), on_date=ON, sections=["bazi"])
    b = r["bazi_year"]
    assert b["natal"]["pillars"]["year"] == "丙午"
    assert {"fu_yin", "self_punishment"} <= _rel_types(b["annual_relations_with_natal"], "year")
    assert {x["type"] for x in b["tai_sui"]["by_year_branch"]} == {"zhi", "xing"}


def test_T1_bazi(R):
    b = R["T1"]["bazi_year"]
    assert b["natal"]["chart"] == "庚午 辛巳 庚辰 癸未"
    assert b["annual_pillar"]["ten_gods"]["stem"]["cn"] == "七杀"           # 丙 для 庚
    assert b["annual_pillar"]["ten_gods"]["life_stage_dm"]["cn"] == "沐浴"   # 庚 в 午
    assert {x["type"] for x in b["tai_sui"]["by_year_branch"]} == {"zhi", "xing"}
    assert _rel_types(b["annual_relations_with_natal"], "month") == {"stem_combination"}   # 丙辛
    assert _rel_types(b["annual_relations_with_natal"], "hour") == {"six_combination"}     # 午未
    lp = b["luck_pillar"]
    assert (lp["n"], lp["ganzhi"], lp["start_date"], lp["end_date"]) == (4, "丁丑", "2023-08-04", "2033-08-04")
    assert lp["half"] == "stem"
    assert "fan_yin" in _rel_types(lp["relations_with_natal"], "hour")    # 丁丑 против 癸未: 癸克丁 + 丑未冲
    assert {x["cn"] for x in b["luck_vs_year"]} >= {"好", "六害"}
    f = b["month_on_date"]["formations_with_annual_luck"]
    assert any(x["type"] == "full_punishment" and x["branches"] == "丑戌未" for x in f)


def test_T2_bazi(R):
    b = R["T2"]["bazi_year"]
    assert b["annual_pillar"]["ten_gods"]["stem"]["cn"] == "偏印"           # 丙 для 戊
    assert [x["type"] for x in b["tai_sui"]["by_year_branch"]] == ["chong"]  # 子午
    lp = b["luck_pillar"]
    assert (lp["n"], lp["ganzhi"]) == (4, "庚午")
    assert "fan_yin" in _rel_types(lp["relations_with_natal"], "year")      # 庚午 против 甲子
    assert any(x["cn"] == "戰 (歲伐運)" for x in b["luck_vs_year"])          # 丙 (год) подавляет 庚 (удача)
    f = b["month_on_date"]["formations_with_annual_luck"]
    assert any(x["type"] == "three_harmony" and x["branches"] == "寅午戌" for x in f)


def test_T3_bazi(R):
    b = R["T3"]["bazi_year"]
    assert b["tai_sui"]["by_year_branch"] == []
    assert b["luck_pillar"]["ganzhi"] == "甲子"
    assert any(x["cn"] == "沖 (運沖歲)" for x in b["luck_vs_year"])          # 子 (Вода) подавляет 午 (Огонь)
    assert any(x["branches"] == "申子辰" for x in b["formations"])
    assert any(x["type"] == "zheng" for x in b["zheng_hui"])


def test_T4_bazi(R):
    b = R["T4"]["bazi_year"]
    assert b["natal"]["chart"] == "己卯 丁卯 丙申 甲午"
    assert b["annual_pillar"]["ten_gods"]["stem"]["cn"] == "比肩"
    assert [x["type"] for x in b["tai_sui"]["by_year_branch"]] == ["po"]    # 卯午 破
    lp = b["luck_pillar"]
    assert (lp["n"], lp["ganzhi"]) == (15, "壬子")
    assert any(x["type"] == "fan_yin" for x in b["luck_vs_year"])          # 丙午 / 壬子
    assert {x["cn"] for x in b["luck_vs_year"]} >= {"戰 (運伐歲)", "沖 (運沖歲)"}


# ---------------------------------------------------------------------------
# B. Девятизвёздная Ки / летящие звёзды
# ---------------------------------------------------------------------------

def test_flying_chart_2026_vs_masterseanchan():
    """https://www.masterseanchan.com/fengshui-2026-flying-star-chart/ : SE 9, S 5, SW 7, E 8, C 1, W 3, NE 4, N 6, NW 2."""
    ch = flying_chart(ns.year_star(2026))
    assert ch == {"SE": 9, "S": 5, "SW": 7, "E": 8, "C": 1, "W": 3, "NE": 4, "N": 6, "NW": 2}
    # обратный полёт — те же клетки пути с убывающими номерами
    assert flying_chart(1, forward=False) == {p: (1 - i - 1) % 9 + 1 for i, p in enumerate(PALACE_PATH)}


# там же: 12 月盤 2026 (порядок SE-S-SW-E-C-W-NE-N-NW)
MSC_MONTHS = ["7-3-5-6-8-1-2-4-9", "6-2-4-5-7-9-1-3-8", "5-1-3-4-6-8-9-2-7", "4-9-2-3-5-7-8-1-6",
              "3-8-1-2-4-6-7-9-5", "2-7-9-1-3-5-6-8-4", "1-6-8-9-2-4-5-7-3", "9-5-7-8-1-3-4-6-2",
              "8-4-6-7-9-2-3-5-1", "7-3-5-6-8-1-2-4-9", "6-2-4-5-7-9-1-3-8", "5-1-3-4-6-8-9-2-7"]


def test_month_charts_2026_vs_masterseanchan_and_lunar_python(R):
    months = R["T1"]["ninestar_year"]["months"]
    assert [m["layout_compact"] for m in months] == MSC_MONTHS
    for m, nm in zip(ninestar_months(2026), range(12)):
        mid = jd_to_utc(m["start_jd"] + 10).astimezone(UTC8)
        lun = Solar.fromYmdHms(mid.year, mid.month, mid.day, 12, 0, 0).getLunar()
        assert m["star"] == CN_NUM[lun.getMonthNineStar(3).getNumber()]
        assert CN_NUM[lun.getYearNineStar(3).getNumber()] == 1


def test_annual_afflictions_2026(R):
    y = R["T1"]["ninestar_year"]["year"]
    # https://oggi.jp/6779413 : 「2026年の五黄殺の方角は「南」」「暗剣殺が「北」、歳破も「北」」
    assert (y["go_o_satsu"], y["anken_satsu"], y["ha"]["palace"]) == ("S", "N", "N")
    # masterseanchan: TaiSui S (午), Year Breaker N (子), San Sha N (亥子丑)
    c = R["T1"]["ninestar_year"]["chinese_annual_afflictions"]
    assert (c["tai_sui"]["palace"], c["sui_po"]["palace"], c["san_sha"]["palace"]) == ("S", "N", "N")
    # https://www.skillon.com/bazi-feng-shui.cfm/topic/2764/2026-feng-shui-illness-stars : #5 — юг, #2 — северо-запад
    assert c["san_sha"]["branches"] == "亥子丑" and c["wu_huang"] == "S" and c["er_hei"] == "NW"


def test_san_sha_rule_other_years():
    """https://www.masterseanchan.com/fengshui-2027-san-sha/ (未, 亥卯未 → запад 申酉戌) и
    https://www.masterseanchan.com/fengshui-2029-san-sha/ (酉 → восток)."""
    for year, palace in ((2027, "W"), (2029, "E"), (2026, "N")):
        r = calculate(T["T1"], on_date=f"{year}-06-01", sections=["ninestar"])
        assert r["ninestar_year"]["chinese_annual_afflictions"]["san_sha"]["palace"] == palace, year


def test_september_2026_month_chart():
    """https://ameblo.jp/ej3/entry-12974149199.html : 2026年9月 — 暗剣殺 北, 五黄殺 南, 月破 東."""
    m = ninestar_months(2026)[7]
    d = chart_directions(flying_chart(m["star"]), m["branch_index"], "month")
    assert m["star"] == 1 and (d["go_o_satsu"], d["anken_satsu"], d["ha"]["palace"]) == ("S", "N", "E")


def test_2025_chart_and_center_five():
    """2025 — звезда 2 (ja.wikipedia: 11 − (Y mod 9)): 五黄殺 北東, 暗剣殺 南西, 歳破 北西 (亥).
    ⚠ crexgroup.com называет для 2025 центр 三碧 и 五黄殺 西 — это карта 2024 г. (ошибка источника)."""
    d = chart_directions(flying_chart(ns.year_star(2025)), bz.year_index(2025) % 12, "year")
    assert (d["center"], d["go_o_satsu"], d["anken_satsu"], d["ha"]["palace"]) == (2, "NE", "SW", "NW")
    d24 = chart_directions(flying_chart(ns.year_star(2024)), bz.year_index(2024) % 12, "year")
    assert (d24["center"], d24["go_o_satsu"], d24["anken_satsu"]) == (3, "W", "E")
    # ja.wikipedia «九星気学»: при 5 в центре 暗剣殺 нет; при звезде рождения в центре нет 本命殺
    d22 = chart_directions(flying_chart(ns.year_star(2022)), bz.year_index(2022) % 12, "year", honmei=5)
    assert ns.year_star(2022) == 5 and d22["go_o_satsu"] is None and d22["anken_satsu"] is None
    assert d22["honmei"]["honmei_satsu"] is None and d22["honmei"]["honmei_teki_satsu"] is None


def test_lucky_stars_vs_ja_wikipedia_table():
    """ja.wikipedia «九星»: 相生・比和 без ※ (свой знак — 本命殺, 五黄 — 五黄殺)."""
    exp = {1: {3, 4, 6, 7}, 2: {6, 7, 9, 8}, 3: {9, 1, 4}, 4: {9, 1, 3}, 5: {6, 7, 9, 2, 8},
           6: {1, 2, 8, 7}, 7: {1, 2, 8, 6}, 8: {6, 7, 9, 2}, 9: {2, 8, 3, 4}}
    for p, stars in exp.items():
        assert set(lucky_stars(p)) == stars, p


# https://oggi.jp/6752236 «2026年の吉方位と凶方位»: 吉方位 по звезде рождения (年盤 2026).
OGGI_2026_LUCKY = {2: {"SW", "E"}, 3: {"SE", "NE"}, 4: {"W", "SE"}, 5: {"SW", "NW", "E", "SE"},
                   6: {"SW", "NW", "E"}, 7: {"NW", "E"}, 8: {"SW", "NW", "SE"}, 9: {"W", "NE", "E"}}


def test_year_lucky_directions_2026_vs_oggi():
    """Правила 相生/比和 минус 五黄殺/暗剣殺/歳破/本命殺/本命的殺 дают ровно списки oggi.jp для звёзд 2–9.
    Для 一白 (1 в центре, 八方塞がり) oggi добавляет ещё 東南 (там 九紫 — 相剋 с 一白, по правилу ja.wikipedia
    «九星» не 吉方): расхождение источника, калькулятор следует правилу."""
    ch = flying_chart(ns.year_star(2026))
    yb = bz.year_index(2026) % 12
    for honmei, exp in OGGI_2026_LUCKY.items():
        d = chart_directions(ch, yb, "year", honmei)
        assert {x["direction"] for x in d["lucky"]} == exp, honmei
    d1 = chart_directions(ch, yb, "year", 1)
    assert {x["direction"] for x in d1["lucky"]} == {"SW", "W", "NE"} and ch["SE"] == 9


def test_year_max_lucky_uses_month_star(R):
    """«最大吉方» (а) — звезда, благоприятная и для 本命星, и для 月命星, — считается и в 年盤.
    T1 (1.5): 7 (ЮЗ) хороша и для 1, и для 5; T2 (7.8): 2 (СЗ); T3 (5.2): 7, 8, 9; T4 (4.7): нет."""
    exp = {"T1": ["SW"], "T2": ["NW"], "T3": ["SW", "E", "SE"], "T4": []}
    for k, v in exp.items():
        y = R[k]["ninestar_year"]["year"]
        assert y["max_lucky_honmei_getsumei"] == v, k
        assert "getsumei" not in y                      # 月命殺 в 年盤 не ставится
        assert not any("月命" in r for u in y["unlucky"] for r in u["reasons"]), k


def test_chart_invariants_all_centers():
    """Инварианты §6: каждая звезда один раз; 五黄殺 ↔ 暗剣殺 противоположны; 吉方 не пересекается с 凶方."""
    for c in range(1, 10):
        ch = flying_chart(c)
        assert sorted(ch.values()) == list(range(1, 10))
        for br in range(12):
            for h in range(1, 10):
                for g in range(1, 10):
                    d = chart_directions(ch, br, "month", h, g)
                    if c == 5:
                        assert d["go_o_satsu"] is None and d["anken_satsu"] is None
                    else:
                        assert d["anken_satsu"] == {"N": "S", "S": "N", "E": "W", "W": "E", "NE": "SW", "SW": "NE",
                                                    "SE": "NW", "NW": "SE"}[d["go_o_satsu"]]
                    bad = {u["direction"] for u in d["unlucky"]}
                    assert not bad & {x["direction"] for x in d["lucky"]}


def test_teii_taichu_2026(R):
    """2026: 三碧 (дом — Восток) стоит на Западе → 定位対冲 W."""
    assert R["T1"]["ninestar_year"]["year"]["teii_taichu"] == ["W"]


def test_person_directions_T1_T2(R):
    n1 = R["T1"]["ninestar_year"]
    assert n1["natal"]["honmei"] == 1 and n1["year"]["honmei"]["in_center"]
    assert any("八方塞がり" in w for w in R["T1"]["warnings"])
    assert [x["direction"] for x in n1["year"]["lucky"]] == ["W", "NE", "SW"]   # 3, 4, 7; Север (6) — 暗剣殺+歳破
    mo = n1["month_on_date"]
    assert mo["star"] == 9 and mo["getsumei"]["star"] == 5
    assert {x["direction"]: x["reasons"] for x in mo["unlucky"]}["N"] == ["五黄殺", "月命殺"]
    n2 = R["T2"]["ninestar_year"]
    assert n2["natal"]["notation"] == "7.8.4"
    assert (n2["year"]["honmei"]["honmei_satsu"], n2["year"]["honmei"]["honmei_teki_satsu"]) == ("SW", "NE")
    assert [x["direction"] for x in n2["year"]["lucky"]] == ["NW", "E"]


def test_day_star_on_date(R):
    d = R["T1"]["ninestar_year"]["day_on_date"]
    lun = Solar.fromYmdHms(2026, 10, 14, 12, 0, 0).getLunar()
    assert d["star"] == CN_NUM[lun.getDayNineStar().getNumber()] == 9
    assert d["nippa"]["palace"] == "E"          # день 辛酉 → 日破 卯 (восток)


# ---------------------------------------------------------------------------
# C. Джйотиш
# ---------------------------------------------------------------------------

def test_gochara_table_vs_phaladeepika():
    """«Пхаладипика» XXVI.2: «all planets in the 11th»; Венера хороша везде, кроме 10, 7, 6; Раху/Кету как Солнце."""
    for g, t in GOCHARA_GOOD.items():
        assert 11 in t, g
    assert set(GOCHARA_GOOD["venus"]) == set(range(1, 13)) - {6, 7, 10}
    assert set(GOCHARA_GOOD["rahu"]) == set(GOCHARA_GOOD["ketu"]) == set(GOCHARA_GOOD["sun"])
    assert GOCHARA_GOOD["saturn"] == GOCHARA_GOOD["mars"] == {3: 12, 6: 9, 11: 5}      # XXVI.5
    assert GOCHARA_GOOD["jupiter"] == {2: 12, 11: 8, 9: 10, 5: 4, 7: 3}               # XXVI.7
    # Полная таблица XXVI.3–8 (archive.org, djvu-текст перевода 1950 г.), включая порядок «respectively»:
    assert GOCHARA_GOOD["sun"] == {11: 5, 3: 9, 10: 4, 6: 12}                           # XXVI.3
    assert GOCHARA_GOOD["moon"] == {7: 2, 1: 5, 6: 12, 11: 8, 10: 4, 3: 9}              # XXVI.4
    assert GOCHARA_GOOD["mercury"] == {2: 5, 4: 3, 6: 9, 8: 1, 10: 8, 11: 12}           # XXVI.6
    # XXVI.8: «1st, 2nd, 3rd, 4th, 5th, 8th, 9th, 12th and 11th … 8th, 7th, 1st, 10th, 9th, 5th, 11th, 6th and 3rd»
    assert GOCHARA_GOOD["venus"] == {1: 8, 2: 7, 3: 1, 4: 10, 5: 9, 8: 5, 9: 11, 12: 6, 11: 3}
    assert VEDHA_EXEMPT == {"sun": "saturn", "saturn": "sun", "moon": "mercury", "mercury": "moon"}
    for g in ("sun", "moon", "mars", "mercury", "jupiter", "venus", "saturn"):      # у каждого дома своя ведха
        assert len(set(GOCHARA_GOOD[g].values())) == len(GOCHARA_GOOD[g])


# https://www.onlinejyotish.com/hindi-astrology/shani-sadesathi/mesha-rashi.php — даты смены знака Сатурном (IST)
SATURN_INGRESS_IST = [("2020-01-24", 9), ("2022-04-29", 10), ("2022-07-12", 9), ("2023-01-17", 10),
                      ("2025-03-29", 11), ("2027-06-03", 0), ("2027-10-20", 11), ("2028-02-23", 0),
                      ("2029-08-08", 1), ("2029-10-05", 0), ("2030-04-17", 1), ("2032-05-31", 2),
                      ("2034-07-13", 3), ("2036-08-27", 4), ("2038-10-22", 5), ("2039-04-05", 4),
                      ("2039-07-13", 5), ("2041-01-28", 6), ("2041-02-06", 5), ("2041-09-26", 6),
                      ("2043-12-11", 7), ("2044-06-23", 6), ("2044-08-30", 7), ("2046-12-08", 8),
                      ("2049-03-06", 9), ("2049-07-10", 8), ("2049-12-04", 9), ("2052-02-25", 10)]


def test_saturn_ingresses_vs_onlinejyotish():
    """Все 27 смен знака из таблицы onlinejyotish (2020–2052), включая 9-дневный заход в Весы 28.01–06.02.2041."""
    a = julian_day_ut(datetime(2019, 6, 1, tzinfo=timezone.utc))
    z = julian_day_ut(datetime(2052, 6, 1, tzinfo=timezone.utc))
    segs = sign_segments("saturn", a, z)
    got = [((jd_to_utc(s["start_jd"]) + IST).date().isoformat(), s["sign"]) for s in segs if s["start_jd"]]
    assert got == SATURN_INGRESS_IST


def test_jupiter_and_rahu_2026_vs_astropatri():
    """https://astropatri.com/transits/jupiter : Рак 02.06.2026 02:25 IST, Лев 31.10.2026 12:50 IST;
    https://astropatri.com/transits/rahu : Раху → Козерог 05.12.2026 19:28 IST (средний узел, Lahiri — у нас)."""
    a = julian_day_ut(datetime(2026, 1, 1, tzinfo=timezone.utc))
    z = julian_day_ut(datetime(2027, 1, 1, tzinfo=timezone.utc))
    jup = [(s["start_jd"], s["sign"]) for s in sign_segments("jupiter", a, z) if s["start_jd"]]
    exp = [(datetime(2026, 6, 2, 2, 25), 3), (datetime(2026, 10, 31, 12, 50), 4)]
    assert [s for _, s in jup] == [3, 4]
    for (jd, _), (dt, _) in zip(jup, exp):
        got = jd_to_utc(jd).replace(tzinfo=None) + IST
        assert abs((got - dt).total_seconds()) < 3600           # расхождение 35–47 мин: вариант аянамши
    rahu = [(s["start_jd"], s["sign"]) for s in sign_segments("rahu", a, z, step=0.5) if s["start_jd"]]
    assert [s for _, s in rahu] == [9]
    got = jd_to_utc(rahu[0][0]).replace(tzinfo=None) + IST
    assert got.date() == date(2026, 12, 5) and abs((got - datetime(2026, 12, 5, 19, 28)).total_seconds()) < 4 * 3600


def test_sade_sati_status_2026_by_moon_sign():
    """https://hindutone.com/astrology/sade-sati-2026-which-rashis-saturn-in-meena/ : Сатурн в Мине —
    Саде-сати у Кумбхи (последняя фаза), Мины (пик), Меши (первая); Аштама — Симха; Ардхаштама — Дхану."""
    jd = julian_day_ut(datetime(2026, 10, 14, 9, 0, tzinfo=timezone.utc))
    zone = ns._Zone("UTC+05:30")
    status = {}
    for ms in range(12):
        s = saturn_periods(ms, jd, zone, span_years=4)
        status[ms] = (s["sade_sati"]["active"], s.get("sade_sati_phase_now"), s["ashtama_shani"]["active"],
                      s["ardhashtama_shani"]["active"])
    assert {m for m, v in status.items() if v[0]} == {10, 11, 0}
    assert (status[10][1], status[11][1], status[0][1]) == ("setting", "peak", "rising")
    assert {m for m, v in status.items() if v[2]} == {4}
    assert {m for m, v in status.items() if v[3]} == {8}


def test_T2_sade_sati_dates(R):
    """T2: Луна в Водолее (Кумбха). Саде-сати 24.01.2020 – 23.02.2028 (IST) с ретро-перерывом 03.06–20.10.2027
    (Сатурн уходит в Овен — 3-й дом); даты ингрессий — onlinejyotish.com (см. выше)."""
    s = R["T2"]["jyotish"]["saturn"]
    assert R["T2"]["jyotish"]["natal"]["moon_sign_ru"] == "Водолей"
    ss = s["sade_sati"]
    assert ss["active"] and s["sade_sati_phase_now"] == "setting"
    assert ss["current"]["start"]["ist"][:10] == "2020-01-24" and ss["current"]["end"]["ist"][:10] == "2028-02-23"
    assert [(i["from"]["ist"][:10], i["to"]["ist"][:10]) for i in ss["current"]["interruptions"]] == [
        ("2027-06-03", "2027-10-20")]
    assert [x["phase"] for x in ss["current"]["segments"]] == ["rising", "peak", "rising", "peak", "setting", "setting"]


def test_T3_next_sade_sati(R):
    s = R["T3"]["jyotish"]["saturn"]
    assert R["T3"]["jyotish"]["natal"]["moon_sign_ru"] == "Телец"
    assert not s["sade_sati"]["active"] and s["saturn_house_from_moon_now"] == 11
    nxt = s["sade_sati"]["next"]
    assert nxt["start"]["ist"][:10] == "2027-06-03" and nxt["end"]["ist"][:10] == "2034-07-13"


def test_transits_and_vedha_T1(R):
    t = R["T1"]["jyotish"]["transits_on_date"]
    assert R["T1"]["jyotish"]["natal"]["moon_sign_ru"] == "Козерог"
    # Юпитер в Раке — 7-й от Луны (благоприятный), ведха в 3-м (Рыбы) — там Сатурн
    assert (t["jupiter"]["house_from_moon"], t["jupiter"]["vedha_house"], t["jupiter"]["vedha_by"]) == (7, 3, ["saturn"])
    assert t["jupiter"]["result"] == "favorable_obstructed"
    assert t["saturn"]["house_from_moon"] == 3 and t["saturn"]["result"] == "favorable"
    assert t["rahu"]["house_from_moon"] == 2 and t["ketu"]["house_from_moon"] == 8
    assert t["jupiter"]["house_from_lagna"] == 12                 # Лагна T1 — Лев
    jup = R["T1"]["jyotish"]["slow_transits_in_year"]["jupiter"]
    assert [(x["sign_ru"], x["house_from_moon"]) for x in jup] == [("Близнецы", 6), ("Рак", 7), ("Лев", 8)]


def test_dasha_on_date_matches_module_07(R):
    for k, r in R.items():
        d = r["jyotish"]["dasha"]
        cur, mod = d["on_date"], d["jyotish_module_current"]
        assert (cur["mahadasha"]["lord"], cur["antardasha"]["lord"], cur["pratyantardasha"]["lord"]) == (
            mod["mahadasha"], mod["antardasha"], mod["pratyantardasha"]), k
    # T1: Раху / Луна / Сатурн (модуль 07, test_current_dasha_on_date)
    c = R["T1"]["jyotish"]["dasha"]["on_date"]
    assert (c["mahadasha"]["lord"], c["antardasha"]["lord"], c["pratyantardasha"]["lord"]) == ("rahu", "moon", "saturn")


def test_dasha_boundary_T3_on_time():
    """T3: пратьянтардаша Луны начинается 14.10.2026 в 10:57 MSK — на 09:00 ещё Солнце."""
    r = calculate(T["T3"], on_date=ON, on_time="09:00", sections=["jyotish"])
    assert r["jyotish"]["dasha"]["on_date"]["pratyantardasha"]["lord"] == "sun"
    r = calculate(T["T3"], on_date=ON, sections=["jyotish"])
    assert r["jyotish"]["dasha"]["on_date"]["pratyantardasha"]["lord"] == "moon"
    assert r["jyotish"]["dasha"]["on_date"]["pratyantardasha"]["start"] == "2026-10-14 10:57"


def test_dasha_periods_in_year_are_contiguous(R):
    d = R["T1"]["jyotish"]["dasha"]
    ads = d["antardashas_in_year"]
    assert [(x["antardasha"], x["end"]) for x in ads] == [("sun", "2026-02-13 08:02"), ("moon", "2027-08-15 04:46")]
    pds = d["pratyantardashas_in_year"]
    for a, b in zip(pds, pds[1:]):
        assert a["end"] == b["start"]
    assert pds[0]["start"] <= "2026-01-01 00:00" and pds[-1]["end"] >= "2027-01-01 00:00"
