"""Тесты модуля 03: Девятизвёздная Ки, число Гуа, китайский зодиак.

Запуск из корня репозитория:
    .venv/bin/python -m pytest calculators/tests/test_ninestar.py -q
"""
from __future__ import annotations

import json
import random
from datetime import date, datetime, timedelta, timezone

import pytest

from calculators.common.ephemeris import sun_longitude
from calculators.common.time import BirthInput, jd_to_utc, julian_day_ut
from calculators.ninestar import (
    EAST_GROUP, GUA_DIRECTIONS, WEST_GROUP, calculate, day_star, eight_mansions_by_line_changes,
    gua_number, gua_raw, li_chun, lunar_new_year, month_star, sexagenary_year, solstice,
    tendency_palace, year_star,
)

CN = "一二三四五六七八九"


def nsk(r: dict) -> dict:
    return r["nine_star_ki"]


# ---------------------------------------------------------------------------
# Эталонные персоны T1–T4 (CONVENTIONS.md)
# ---------------------------------------------------------------------------

def test_T1_moscow_1990_female():
    r = calculate(BirthInput(1990, 5, 15, 14, 30, place="Москва", gender="female"))
    n = nsk(r)
    assert r["inputs_used"]["utc"] == "1990-05-15T10:30+00:00"   # летнее время СССР, UTC+4
    assert n["solar_year"] == 1990
    assert n["principal"]["number"] == 1                         # 一白水星
    assert n["month"]["number"] == 5 and n["month"]["branch"] == "巳"
    assert n["tendency"]["number"] == 1                          # 坎宮傾斜
    assert n["notation"] == "1.5.1"
    assert n["day"]["number"] == 2                               # luft.co.jp и lunar-python: 二黒
    assert n["day"]["day_ganzhi"] == "庚辰"
    # Гуа: (1990+4) mod 9 = 5 → у женщин 5 → 8.
    # Внешний вектор: https://www.skillon.com/kua-number-calculator.cfm (15.05.1990, Female) → 8 (Ken 艮)
    assert r["gua"]["raw"] == 5 and r["gua"]["number"] == 8 and r["gua"]["group"] == "west"
    assert r["zodiac"]["ganzhi"] == "庚午" and r["zodiac"]["animal"] == "Лошадь"
    assert r["zodiac"]["element"] == "Металл" and r["zodiac"]["yin_yang"] == "ян"
    assert r["zodiac"]["popular_name_ru"] == "Белая Металлическая Лошадь"


def test_T2_moscow_lichun_day_late_zi():
    r = calculate(BirthInput(1984, 2, 4, 23, 30, place="Москва", gender="male"))
    n = nsk(r)
    # Личунь 1984: 15:18:44 UT = 18:18 MSK (CONVENTIONS: «около 18:19 MSK»)
    assert r["boundaries"]["li_chun_utc"] == "1984-02-04T15:18+00:00"
    assert n["solar_year"] == 1984 and n["principal"]["number"] == 7
    assert n["month"]["number"] == 8 and n["month"]["branch"] == "寅"
    assert n["tendency"]["number"] == 4 and n["notation"] == "7.8.4"
    assert n["day"]["number"] == 2 and n["day"]["alt_if_day_starts_23h"] == 3
    # Внешний вектор: https://www.skillon.com/kua-number-calculator.cfm (04.02.1984, Male) → 7 (Dui 兑)
    assert r["gua"]["number"] == 7 and r["gua"]["group"] == "west"
    assert r["zodiac"]["ganzhi"] == "甲子" and r["zodiac_solar"]["ganzhi"] == "甲子"
    # Японский календарь: Личунь 1984 = 5 февраля (JST) → предупреждение о «1983, звезда 8»
    assert any("1984-02-05" in w and "звезда 8" in w for w in r["warnings"])


def test_T2_date_only_japanese_almanac_gives_previous_year():
    # Японский калькулятор с таблицей дат Личуня по JST: https://shin-yu.net/kyuseikigaku/en/
    # (RISSHUN_DAYS[1984] = 5) → рождение 04.02.1984 относится к 1983 году → звезда 8.
    r = calculate(BirthInput(1984, 2, 4, place="Москва", gender="male"), almanac_tz="UTC+09:00")
    assert r["variant"]["boundary_precision"] == "date"
    assert nsk(r)["solar_year"] == 1983 and nsk(r)["principal"]["number"] == 8
    # Без японского альманаха: дата Личуня в Москве = 04.02 → новый год, но с предупреждением.
    r2 = calculate(BirthInput(1984, 2, 4, place="Москва", gender="male"))
    assert nsk(r2)["principal"]["number"] == 7
    assert any("совпадает с днём Личуня" in w for w in r2["warnings"])


def test_T3_spb_2004_feb29_female():
    r = calculate(BirthInput(2004, 2, 29, 8, 15, place="Санкт-Петербург", gender="female"))
    n = nsk(r)
    assert n["solar_year"] == 2004 and n["principal"]["number"] == 5
    assert n["month"]["number"] == 2 and n["tendency"]["number"] == 8
    assert n["notation"] == "5.2.8"
    assert n["day"]["number"] == 3 and n["day"]["day_ganzhi"] == "戊寅"
    # 2000-е, женщина: ЦК(04)=4 + 6 = 10 → 1.
    # Внешний вектор: https://www.skillon.com/kua-number-calculator.cfm (29.02.2004, Female) → 1 (Kan 坎)
    assert r["gua"]["number"] == 1 and r["gua"]["group"] == "east"
    assert r["zodiac"]["ganzhi"] == "甲申" and r["zodiac"]["animal"] == "Обезьяна"


def test_T4_einstein_ulm_lmt():
    r = calculate(BirthInput(1879, 3, 14, 11, 30, place="Ульм", gender="male"))
    n = nsk(r)
    assert r["inputs_used"]["utc"] == "1879-03-14T10:50+00:00"  # LMT по долготе 9.9876°E
    assert n["solar_year"] == 1879 and n["principal"]["number"] == 4
    assert n["month"]["number"] == 7 and n["month"]["branch"] == "卯"
    assert n["tendency"]["number"] == 2 and n["notation"] == "4.7.2"
    assert n["day"]["number"] == 3 and n["day"]["day_ganzhi"] == "丙申"
    assert r["gua"]["number"] == 4 and r["gua"]["group"] == "east"
    assert r["zodiac"]["ganzhi"] == "己卯" and r["zodiac"]["element"] == "Земля" and r["zodiac"]["yin_yang"] == "инь"


@pytest.mark.parametrize("b", [
    BirthInput(1990, 5, 15, 14, 30, place="Москва", gender="female"),
    BirthInput(1984, 2, 4, 23, 30, place="Москва", gender="male"),
    BirthInput(2004, 2, 29, 8, 15, place="Санкт-Петербург", gender="female"),
    BirthInput(1879, 3, 14, 11, 30, place="Ульм", gender="male"),
])
def test_T1_T4_match_lunar_python(b):
    """Независимая библиотека lunar-python (年/月/日九星; время → UTC+8)."""
    from lunar_python import Solar
    r = calculate(b)
    u = datetime.fromisoformat(r["inputs_used"]["utc"]) + timedelta(hours=8)
    lu = Solar.fromYmdHms(u.year, u.month, u.day, u.hour, u.minute, 0).getLunar()
    assert CN.index(lu.getYearNineStar(3).getNumber()) + 1 == nsk(r)["principal"]["number"]
    assert CN.index(lu.getMonthNineStar(3).getNumber()) + 1 == nsk(r)["month"]["number"]
    ld = Solar.fromYmd(b.year, b.month, b.day).getLunar()
    assert CN.index(ld.getDayNineStar().getNumber()) + 1 == nsk(r)["day"]["number"]


def test_json_serializable_and_required_keys():
    r = calculate(BirthInput(1990, 5, 15, 14, 30, place="Москва", gender="female"))
    json.dumps(r, ensure_ascii=False)
    for k in ("method", "variant", "inputs_used", "warnings", "steps"):
        assert k in r
    assert len(r["steps"]) >= 8


# ---------------------------------------------------------------------------
# Формула звезды года — опубликованные значения
# ---------------------------------------------------------------------------

# https://www.9starki.com/toolbox.htm : 1922=6, 1947=8, 1924=4, 2023=4; метод Фабера: 2000=9, 2001=8,
# 2002=7, 2006=3, 2055=8.
@pytest.mark.parametrize("year,star", [(1922, 6), (1947, 8), (1924, 4), (2023, 4), (2000, 9), (2001, 8),
                                       (2002, 7), (2006, 3), (2055, 8)])
def test_year_star_9starki_com(year, star):
    assert year_star(year) == star


# https://jobcannon.io/blog/how-nine-star-ki-is-calculated : 15.03.1989 → 2; 22.01.2003 → 7 (год 2002);
# 04.02.2000 → 9; 1985 → 6, январь 1985 → 7.
@pytest.mark.parametrize("d,star", [((1989, 3, 15), 2), ((2003, 1, 22), 7), ((2000, 2, 4), 9),
                                    ((1985, 6, 1), 6), ((1985, 1, 15), 7)])
def test_year_star_jobcannon_examples(d, star):
    r = calculate(BirthInput(*d, tz="Asia/Tokyo"), day_star_method=None)
    assert nsk(r)["principal"]["number"] == star


def test_year_star_formula_equivalences():
    for y in range(1800, 2201):
        dr = sum(int(c) for c in str(y))
        while dr >= 10:
            dr = sum(int(c) for c in str(dr))
        s = 11 - dr
        s = s - 9 if s > 9 else s
        assert year_star(y) == s                                     # «11 − цифровой корень» (ja.wikipedia)
        assert year_star(y) == gua_raw(y, "male")                    # звезда года = мужское Гуа до замены 5
        if 1900 <= y <= 1999:
            r = sum(int(c) for c in f"{y % 100:02d}")
            r = 0 if r == 0 else (r - 1) % 9 + 1
            assert year_star(y) == (10 - r - 1) % 9 + 1              # 10 − ЦК(две последние цифры)
        if 2000 <= y <= 2099:
            r = sum(int(c) for c in f"{y % 100:02d}")
            r = 0 if r == 0 else (r - 1) % 9 + 1
            assert year_star(y) == ((9 - r) or 9)                    # 9 − ЦК(две последние цифры)


def test_year_and_month_star_random_vs_lunar_python():
    """lunar-python (sect=3, точный момент цзеци, время КНР) на 300 случайных моментах 1801–2098."""
    from lunar_python import Solar
    rnd = random.Random(42)
    checked = 0
    while checked < 300:
        y = rnd.randint(1801, 2098)
        dt = datetime(y, 1, 1, tzinfo=timezone.utc) + timedelta(minutes=rnd.randint(0, 365 * 24 * 60 - 1))
        lon = sun_longitude(julian_day_ut(dt))
        if min((lon - 315) % 30, 30 - (lon - 315) % 30) < 0.05:     # ±~1 ч от цзе — пропускаем
            continue
        r = calculate(BirthInput(dt.year, dt.month, dt.day, dt.hour, dt.minute, tz="UTC"), day_star_method=None)
        bj = dt + timedelta(hours=8)
        lu = Solar.fromYmdHms(bj.year, bj.month, bj.day, bj.hour, bj.minute, 0).getLunar()
        assert CN.index(lu.getYearNineStar(3).getNumber()) + 1 == nsk(r)["principal"]["number"], dt
        assert CN.index(lu.getMonthNineStar(3).getNumber()) + 1 == nsk(r)["month"]["number"], dt
        checked += 1


# ---------------------------------------------------------------------------
# Звезда месяца и «наклон» (傾斜 / energetic number)
# ---------------------------------------------------------------------------

def test_month_star_tables():
    # 子午卯酉-годы (1,4,7): 寅=8; 辰戌丑未 (3,6,9): 寅=5; 寅申巳亥 (2,5,8): 寅=2; далее по убыванию.
    assert [month_star(1, m) for m in range(12)] == [8, 7, 6, 5, 4, 3, 2, 1, 9, 8, 7, 6]
    assert [month_star(3, m) for m in range(12)] == [5, 4, 3, 2, 1, 9, 8, 7, 6, 5, 4, 3]
    assert [month_star(2, m) for m in range(12)] == [2, 1, 9, 8, 7, 6, 5, 4, 3, 2, 1, 9]
    # Январь (丑) любого года стыкуется с февралём (寅) следующего года без разрыва:
    for ys in range(1, 10):
        nxt = (ys - 2) % 9 + 1                                        # звезда следующего года на 1 меньше
        assert (month_star(ys, 11) - 2) % 9 + 1 == month_star(nxt, 0)


def test_freeflow_2018_june_9_1_4():
    # http://www.freeflow-fengshui.com/resources/the_ki_astrology.php : 2018 = 9 Fire, июнь = 1 Water, «9 . 1 . 4»
    r = calculate(BirthInput(2018, 6, 20, 12, 0, tz="Europe/London"))
    assert nsk(r)["notation"] == "9.1.4"


def test_art_of_wind_and_water_2_5_2():
    # https://the-art-of-wind-and-water.com/9-star-ki-astrology/calculate-your-superficial-star/
    # Principal 2 Earth, рождение 15 августа → «2.5.2». Год со звездой 2 — например, 2016.
    r = calculate(BirthInput(2016, 8, 15, 12, 0, tz="Europe/London"))
    assert nsk(r)["principal"]["number"] == 2 and nsk(r)["notation"] == "2.5.2"


def test_tendency_published_examples():
    # https://yakumoin.info/about/keisha : 本命 一白 + 月命 三碧 → 震宮傾斜
    assert tendency_palace(1, 3)["number"] == 3
    # https://amenouranai.com/kyuseikigaku-keisha/ : 本命 一白 + 月命 四緑 → 坤宮傾斜
    assert tendency_palace(1, 4)["number"] == 2
    # 中宮傾斜 (одинаковые звёзды) — таблица обоих источников
    expected = {1: 9, 2: 6, 3: 4, 4: 3, 6: 2, 7: 8, 8: 7, 9: 1}
    for s, p in expected.items():
        t = tendency_palace(s, s)
        assert t["number"] == p and t["special_center_case"]
    assert tendency_palace(5, 5, "male")["number"] == 7
    assert tendency_palace(5, 5, "female")["number"] == 6
    assert tendency_palace(5, 5)["number"] is None


# ---------------------------------------------------------------------------
# Границы года: Личунь (точный момент) против китайского Нового года
# ---------------------------------------------------------------------------

# Даты Личуня и китайского Нового года по Гонконгской обсерватории (UTC+8):
# https://www.hko.gov.hk/en/gts/time/calendar/text/files/T1984e.txt (и T1985e, T1990e, T1997e, T2004e, T2021e)
@pytest.mark.parametrize("year,lichun_hk,cny", [
    (1984, date(1984, 2, 4), date(1984, 2, 2)), (1985, date(1985, 2, 4), date(1985, 2, 20)),
    (1990, date(1990, 2, 4), date(1990, 1, 27)), (1997, date(1997, 2, 4), date(1997, 2, 7)),
    (2004, date(2004, 2, 4), date(2004, 1, 22)), (2021, date(2021, 2, 3), date(2021, 2, 12)),
])
def test_lichun_and_cny_vs_hko(year, lichun_hk, cny):
    assert (jd_to_utc(li_chun(year)) + timedelta(hours=8)).date() == lichun_hk
    assert lunar_new_year(year) == cny


def test_lichun_jst_dates_vs_shinyu_table():
    """Даты Личуня по JST 1900–2101 из https://shin-yu.net/kyuseikigaku/en/ (RISSHUN_DAYS, «天文真値»)."""
    table = (
        [4, 4, 5, 5, 5, 4, 5, 5, 5, 4, 5, 5, 5, 4, 5, 5, 5, 4, 4, 5,
         5, 4, 4, 5, 5, 4, 4, 5, 5, 4, 4, 5, 5, 4, 4, 5, 5, 4, 4, 5,
         5, 4, 4, 5, 5, 4, 4, 5, 5, 4, 4, 5, 5, 4, 4, 4, 5, 4, 4, 4,
         5, 4, 4, 4, 5, 4, 4, 4, 5, 4, 4, 4, 5, 4, 4, 4, 5, 4, 4, 4,
         5, 4, 4, 4, 5, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4]
        + [4] * 20
        + [4, 3, 4, 4, 4, 3, 4, 4, 4, 3, 4, 4, 4, 3, 4, 4, 4, 3, 4, 4,
           4, 3, 4, 4, 4, 3, 4, 4, 4, 3, 4, 4, 4, 3, 4, 4, 4, 3, 3, 4,
           4, 3, 3, 4, 4, 3, 3, 4, 4, 3, 3, 4, 4, 3, 3, 4, 4, 3, 3, 4,
           4, 3, 3, 4, 4, 3, 3, 4, 4, 3, 3, 3, 4, 3, 3, 3, 4, 3, 3, 3,
           4, 4]
    )
    for i, day in enumerate(table):
        jst = jd_to_utc(li_chun(1900 + i)) + timedelta(hours=9)
        assert (jst.month, jst.day) == (2, day), 1900 + i


def test_lichun_moment_vs_lunar_python():
    from lunar_python import Solar
    for y in (1879, 1984, 1985, 1990, 2004, 2021):
        t = Solar.fromYmd(y, 6, 1).getLunar().getJieQiTable()["立春"]
        lp = datetime(t.getYear(), t.getMonth(), t.getDay(), t.getHour(), t.getMinute(), t.getSecond())
        ours = (jd_to_utc(li_chun(y)) + timedelta(hours=8)).replace(tzinfo=None)
        assert abs((ours - lp).total_seconds()) < 10


@pytest.mark.parametrize("hh,mm,year,star,gua_m,solar_gz", [
    (17, 0, 1983, 8, 8, "癸亥"),     # до Личуня (18:18 MSK) → 1983, Свинья
    (19, 0, 1984, 7, 7, "甲子"),     # после → 1984, Крыса
])
def test_boundary_1984_feb4_before_after_lichun(hh, mm, year, star, gua_m, solar_gz):
    r = calculate(BirthInput(1984, 2, 4, hh, mm, place="Москва", gender="male"))
    assert nsk(r)["solar_year"] == year and nsk(r)["principal"]["number"] == star
    assert r["gua"]["number"] == gua_m
    assert r["zodiac_solar"]["ganzhi"] == solar_gz
    assert r["zodiac"]["ganzhi"] == "甲子"          # китайский НГ 02.02.1984 уже прошёл → Крыса в обоих случаях


def test_boundary_2021_feb3_local_time_matters():
    # Личунь 2021: 03.02 14:58:47 UT = 17:58 MSK (HKO: 03.02.2021 по UTC+8)
    before = calculate(BirthInput(2021, 2, 3, 17, 30, place="Москва", gender="male"))
    after = calculate(BirthInput(2021, 2, 3, 18, 30, place="Москва", gender="male"))
    assert nsk(before)["principal"]["number"] == 7 and nsk(after)["principal"]["number"] == 6
    # Упрощённая «граница 4 февраля» (как на многих сайтах) ошибается для 03.02.2021 18:30:
    simple = calculate(BirthInput(2021, 2, 3, 18, 30, place="Москва", gender="male"), year_boundary="feb4")
    assert nsk(simple)["principal"]["number"] == 7
    assert any("4 февраля" in w for w in simple["warnings"])


def test_boundary_1985_same_moment_different_local_dates():
    # Личунь 1985: 03.02 21:11:48 UT = 04.02 00:11 MSK. Местная дата для одного и того же решения разная.
    msk_before = calculate(BirthInput(1985, 2, 3, 23, 30, place="Москва"))      # 20:30 UT — до
    msk_after = calculate(BirthInput(1985, 2, 4, 0, 30, place="Москва"))        # 21:30 UT — после
    ny_after = calculate(BirthInput(1985, 2, 3, 17, 0, place="Нью-Йорк"))      # 22:00 UT — после, хотя 3 февраля
    assert nsk(msk_before)["principal"]["number"] == 7
    assert nsk(msk_after)["principal"]["number"] == 6
    assert nsk(ny_after)["principal"]["number"] == 6


def test_between_lichun_and_cny_1985():
    # 10.02.1985: Личунь (04.02) прошёл, китайский НГ (20.02) — нет.
    r = calculate(BirthInput(1985, 2, 10, 12, 0, place="Москва", gender="male"))
    assert nsk(r)["principal"]["number"] == 6
    assert r["zodiac_solar"]["ganzhi"] == "乙丑" and r["zodiac"]["ganzhi"] == "甲子"
    assert r["gua"]["number"] == 6 and r["gua"]["alt_other_boundary"]["number"] == 7
    # Внешний вектор (граница по китайскому НГ): https://www.skillon.com/kua-number-calculator.cfm
    # (10.02.1985, Male) → 7 (Dui 兑)
    r2 = calculate(BirthInput(1985, 2, 10, 12, 0, place="Москва", gender="male"), gua_boundary="lunar_new_year")
    assert r2["gua"]["number"] == 7
    assert any("Знак года различается" in w for w in r["warnings"])


def test_between_jan1_and_cny_1990():
    # 20.01.1990: до китайского НГ (27.01.1990) и до Личуня → оба метода дают 1989 (己巳, Змея).
    r = calculate(BirthInput(1990, 1, 20, 12, 0, place="Москва", gender="female"))
    assert r["zodiac"]["ganzhi"] == "己巳" and r["zodiac_solar"]["ganzhi"] == "己巳"
    assert nsk(r)["principal"]["number"] == 2 and nsk(r)["month"]["branch"] == "丑"
    assert r["gua"]["number"] == 4                 # (1989 + 4) mod 9 = 4


def test_between_cny_and_lichun_2004():
    # 25.01.2004: китайский НГ (22.01.2004) прошёл, Личунь (04.02) — нет.
    r = calculate(BirthInput(2004, 1, 25, 12, 0, place="Москва", gender="female"))
    assert r["zodiac"]["ganzhi"] == "甲申" and r["zodiac_solar"]["ganzhi"] == "癸未"
    assert nsk(r)["principal"]["number"] == 6      # 2003
    assert r["gua"]["number"] == 9                 # Личунь: (2003 + 4) mod 9 = 0 → 9
    # Внешний вектор: https://www.skillon.com/kua-number-calculator.cfm (25.01.2004, Female) → 1 (Kan 坎)
    r2 = calculate(BirthInput(2004, 1, 25, 12, 0, place="Москва", gender="female"), gua_boundary="lunar_new_year")
    assert r2["gua"]["number"] == 1


# ---------------------------------------------------------------------------
# Число Гуа
# ---------------------------------------------------------------------------

# https://www.skillon.com/kua-number-calculator.cfm (POST, даты в середине года, граница не влияет)
@pytest.mark.parametrize("d,male,female", [
    ((1974, 2, 14), 8, 7), ((1999, 6, 1), 1, 8), ((2000, 6, 1), 9, 6), ((1977, 6, 1), 2, 1),
    ((2008, 6, 1), 1, 8), ((2013, 6, 1), 2, 1),
])
def test_gua_skillon_vectors(d, male, female):
    r = calculate(BirthInput(*d, tz="Asia/Shanghai"), day_star_method=None)
    assert r["gua"]["male"]["number"] == male
    assert r["gua"]["female"]["number"] == female


def test_gua_special_five_and_groups():
    for y in range(1850, 2150):
        for g in ("male", "female"):
            raw, num = gua_raw(y, g), gua_number(y, g)
            assert num != 5
            if raw == 5:
                assert num == (2 if g == "male" else 8)
            assert num in EAST_GROUP | WEST_GROUP
        # сумма мужского и женского «сырых» чисел ≡ 6 (mod 9)
        assert (gua_raw(y, "male") + gua_raw(y, "female")) % 9 == 6


def test_eight_mansions_table_self_check():
    dirs_east = {"N", "S", "E", "SE"}
    for g, t in GUA_DIRECTIONS.items():
        assert sorted(t.values()) == sorted(["N", "NE", "E", "SE", "S", "SW", "W", "NW"])
        assert eight_mansions_by_line_changes(g) == t                # «大游年» по сменам черт
        fav = {t[k] for k in ("sheng_qi", "tian_yi", "yan_nian", "fu_wei")}
        assert fav == (dirs_east if g in EAST_GROUP else {"NE", "SW", "W", "NW"})
    # https://www.skillon.com/kua-number-calculator.cfm — таблица для Kua 8
    assert GUA_DIRECTIONS[8] == {"jue_ming": "SE", "huo_hai": "S", "sheng_qi": "SW", "liu_sha": "E",
                                 "yan_nian": "W", "fu_wei": "NE", "wu_gui": "N", "tian_yi": "NW"}


def test_no_gender_gives_both_gua():
    r = calculate(BirthInput(1990, 5, 15, 14, 30, place="Москва"))
    assert r["gua"]["male"]["number"] == 1 and r["gua"]["female"]["number"] == 8
    assert any("Пол не указан" in w for w in r["warnings"])


# ---------------------------------------------------------------------------
# Китайский зодиак
# ---------------------------------------------------------------------------

# https://en.wikipedia.org/wiki/Chinese_zodiac — таблица 1984–1995
@pytest.mark.parametrize("year,animal,element,yy,gz", [
    (1984, "Крыса", "Дерево", "ян", "甲子"), (1985, "Бык", "Дерево", "инь", "乙丑"),
    (1986, "Тигр", "Огонь", "ян", "丙寅"), (1987, "Кролик (Кот)", "Огонь", "инь", "丁卯"),
    (1988, "Дракон", "Земля", "ян", "戊辰"), (1989, "Змея", "Земля", "инь", "己巳"),
    (1990, "Лошадь", "Металл", "ян", "庚午"), (1991, "Коза (Овца)", "Металл", "инь", "辛未"),
    (1992, "Обезьяна", "Вода", "ян", "壬申"), (1993, "Петух", "Вода", "инь", "癸酉"),
    (1994, "Собака", "Дерево", "ян", "甲戌"), (1995, "Свинья (Кабан)", "Дерево", "инь", "乙亥"),
])
def test_zodiac_wikipedia(year, animal, element, yy, gz):
    z = sexagenary_year(year)
    assert (z["animal"], z["element"], z["yin_yang"], z["ganzhi"]) == (animal, element, yy, gz)


def test_zodiac_cycle_index():
    assert sexagenary_year(1984)["cycle_index"] == 1 and sexagenary_year(2043)["cycle_index"] == 60
    assert sexagenary_year(1924)["ganzhi"] == "甲子" and sexagenary_year(2044)["ganzhi"] == "甲子"


# ---------------------------------------------------------------------------
# Звезда дня (日家九星)
# ---------------------------------------------------------------------------

# Векторы получены алгоритмом страницы https://www.luft.co.jp/cgi/nine-star-ki-table.php
# (японское правило с «閏»; JS-функции страницы запущены без DOM). Включены сегменты 閏:
# 1985-12-21 甲午 → 七赤 «два дня подряд» и 2020-06-20 甲午 → 三碧 (см. ja.wikipedia «九星»).
@pytest.mark.parametrize("d,star", [
    ("1990-05-14", 1), ("1990-05-15", 2),
    ("1951-12-19", 7), ("1951-12-20", 7), ("1951-12-21", 8), ("1952-01-18", 9), ("1952-01-19", 1),
    ("1985-12-20", 7), ("1985-12-21", 7), ("1986-01-19", 9), ("1986-01-20", 1),
    ("1974-06-21", 3), ("1974-06-22", 3), ("1974-07-21", 1), ("1974-07-22", 9),
    ("2020-06-19", 3), ("2020-06-20", 3), ("2020-06-21", 2), ("2020-07-19", 1), ("2020-07-20", 9),
])
def test_day_star_ja_leap_vs_luft(d, star):
    assert day_star(date.fromisoformat(d), "ja_leap")["number"] == star


def test_day_star_ja_leap_rule_on_jiazi_solstice():
    # Зимнее солнцестояние 2002 пришлось на день 甲子 (22.12.2002): «ближайший甲子» — этот же день → звезда 1.
    # (Скрипт luft.co.jp в этом случае берёт предыдущий 甲子 — ошибка поиска, см. базу знаний.)
    r = day_star(date(2002, 12, 22), "ja_leap")
    assert r["day_ganzhi"] == "甲子" and r["number"] == 1 and r["dun"] == "yang"


def test_day_star_nearest_no_leap_vs_lunar_python():
    """lunar-python getDayNineStar (без 閏) — 150 случайных дат вне январских окон, где у неё артефакт."""
    from lunar_python import Solar
    rnd = random.Random(7)
    for _ in range(150):
        d = date(1901, 3, 1) + timedelta(days=rnd.randint(0, 72000))
        if d.month == 1:
            continue
        lp = CN.index(Solar.fromYmd(d.year, d.month, d.day).getLunar().getDayNineStar().getNumber()) + 1
        assert day_star(d, "nearest_no_leap")["number"] == lp, d


def test_solstice_dates_vs_hko():
    # HKO T2004e.txt: Summer Solstice 2004-06-21, Winter Solstice 2004-12-21 (UTC+8)
    assert (jd_to_utc(solstice(2004, "summer")) + timedelta(hours=8)).date() == date(2004, 6, 21)
    assert (jd_to_utc(solstice(2004, "winter")) + timedelta(hours=8)).date() == date(2004, 12, 21)
