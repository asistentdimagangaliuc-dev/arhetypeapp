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
    gua_number, gua_raw, hour_star, li_chun, lunar_new_year, month_star, sexagenary_year, solstice,
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
# 04.02.2000 → 9. (Проверка 2-й волны: примеров «1985» на странице нет — убраны.)
@pytest.mark.parametrize("d,star", [((1989, 3, 15), 2), ((2003, 1, 22), 7), ((2000, 2, 4), 9)])
def test_year_star_jobcannon_examples(d, star):
    r = calculate(BirthInput(*d, tz="Asia/Tokyo"), day_star_method=None)
    assert nsk(r)["principal"]["number"] == star


# Та же страница: «A birth on January 15, 1995 is treated as belonging to 1994's cycle …
# A birth on February 5, 1995 is treated as belonging to 1995's cycle» (звёзды там не названы).
@pytest.mark.parametrize("d,solar_year", [((1995, 1, 15), 1994), ((1995, 2, 5), 1995)])
def test_solar_year_jobcannon_1995(d, solar_year):
    r = calculate(BirthInput(*d, tz="Asia/Tokyo"), day_star_method=None)
    assert nsk(r)["solar_year"] == solar_year


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


@pytest.mark.parametrize("hh,mm,year,star", [(0, 10, 1983, 8), (0, 30, 1984, 7)])
def test_boundary_feb5_tokyo_1984(hh, mm, year, star):
    # Личунь 1984 = 05.02 00:18:44 JST: 5 февраля до и после момента (проверка 2-й волны, расчёт вручную).
    r = calculate(BirthInput(1984, 2, 5, hh, mm, tz="Asia/Tokyo", gender="male"), day_star_method=None)
    assert nsk(r)["solar_year"] == year and nsk(r)["principal"]["number"] == star
    assert r["gua"]["number"] == star                      # мужское Гуа = звезда года (8 и 7, замены 5 нет)
    assert r["zodiac"]["ganzhi"] == "甲子"                  # китайский НГ 02.02.1984 уже прошёл


def test_1800s_lichun_day_utc():
    # Личунь 1868: 04.02 11:45:32 UT (Swiss Ephemeris). До момента → 1867 (丁卯, звезда 7); после → 1868 (戊辰, 6).
    before = calculate(BirthInput(1868, 2, 4, 11, 0, tz="UTC", gender="female"), day_star_method=None)
    after = calculate(BirthInput(1868, 2, 4, 12, 0, tz="UTC", gender="female"), day_star_method=None)
    assert (nsk(before)["principal"]["number"], before["zodiac_solar"]["ganzhi"]) == (7, "丁卯")
    assert (nsk(after)["principal"]["number"], after["zodiac_solar"]["ganzhi"]) == (6, "戊辰")
    assert before["gua"]["number"] == 8 and after["gua"]["number"] == 9   # ж: (1867+4) mod 9 = 8; (1868+4) mod 9 = 0 → 9
    assert nsk(after)["notation"] == "6.5.6"


def test_cross_module_gua_kua_and_bazi_year():
    """Гуа = Куа модуля 12 (tarot_loshu), год по Личуню = столп года модуля 01 (bazi), если время известно."""
    from calculators import bazi, tarot_loshu
    for hh, g in ((23, "male"), (10, "male"), (20, "male"), (10, "female")):
        b = BirthInput(1984, 2, 4, hh, 30 if hh == 23 else 0, place="Москва", gender=g)
        r = calculate(b, day_star_method=None)
        kua = tarot_loshu.calculate(b)["loshu"]["kua"]
        assert (kua["number"], kua["year_used"]) == (r["gua"]["number"], r["gua"]["year_used"])
        assert bazi.calculate(b)["pillars"]["year"]["ganzhi"] == r["zodiac_solar"]["ganzhi"]


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
    # Там же, Kua 7 (POST 01.06.1984, Male). Проверка 2-й волны: все 8 таблиц skillon совпадают с GUA_DIRECTIONS.
    assert GUA_DIRECTIONS[7] == {"sheng_qi": "NW", "tian_yi": "SW", "yan_nian": "NE", "fu_wei": "W",
                                 "huo_hai": "N", "wu_gui": "S", "liu_sha": "SE", "jue_ming": "E"}
    # Взаимность пар (одна и та же пара триграмм в обе стороны): 生气, 天医, 延年, 祸害, 五鬼, 六煞, 绝命.
    # Ловит перестановку 六煞/绝命 между В и ЮВ, встречающуюся в некоторых веб-таблицах.
    dir2gua = {d: g for g, d in {1: "N", 2: "SW", 3: "E", 4: "SE", 6: "NW", 7: "W", 8: "NE", 9: "S"}.items()}
    for g, t in GUA_DIRECTIONS.items():
        for k, d in t.items():
            if k != "fu_wei":
                assert GUA_DIRECTIONS[dir2gua[d]][k] == {1: "N", 2: "SW", 3: "E", 4: "SE", 6: "NW", 7: "W",
                                                        8: "NE", 9: "S"}[g], (g, k)


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


def _leap_positions(method: str) -> list[str]:
    """Положения «閏» 1873–2100 в обозначениях ja.wikipedia: «<год солнцестояния>夏/冬»."""
    out = []
    for y in range(1873, 2101):
        for kind, lab in (("summer", "夏"), ("winter", "冬")):
            sol = (jd_to_utc(solstice(y, kind)) + timedelta(hours=9)).date()   # дата по JST
            # Сегмент 閏 длится 30 дней и лежит в пределах ±31 дня от солнцестояния: шаг 10 дней его не пропустит.
            if any(day_star(sol + timedelta(days=k), method)["leap_segment"] for k in range(-35, 36, 10)):
                out.append(f"{y}{lab}")
    return sorted(set(out))


def test_day_star_leap_list_vs_ja_wikipedia():
    """ja.wikipedia «九星», раздел 日家九星: базовый список «閏» 1882–2100 (солнцестояние 癸巳 → следующий 甲子)
    и альтернативы в скобках. https://ja.wikipedia.org/wiki/九星"""
    wiki_base = ["1882冬", "1894夏", "1905冬", "1916冬", "1928夏", "1939冬", "1951夏", "1962冬", "1974夏", "1985冬",
                 "1997夏", "2008冬", "2019冬", "2031冬", "2042冬", "2054夏", "2065冬", "2077夏", "2088冬", "2100夏"]
    assert _leap_positions("ja_leap_wiki") == sorted(wiki_base)
    # Вариант по умолчанию (癸巳 → предыдущий 甲子, как luft.co.jp) совпадает со «скобочными» альтернативами
    # ja.wikipedia в 1917 夏, 1928 冬, 1951 冬, 2020 夏, 2054 冬, в остальных годах — с базовым списком.
    alt = {"1916冬": "1917夏", "1928夏": "1928冬", "1951夏": "1951冬", "2019冬": "2020夏", "2054夏": "2054冬"}
    assert _leap_positions("ja_leap") == sorted(alt.get(x, x) for x in wiki_base)


def test_day_star_school_window_warning():
    # Зимнее солнцестояние 22.12.2019 (JST) — день 癸巳. ja_leap: Ян-дунь с 甲子 23.11.2019, 15.01.2020 = 53-й день
    # → 1 + 53 = 54 → 9. ja_leap_wiki: Инь-дунь 27.05.2019–22.01.2020 (240 дн.), 閏 с 甲午 23.12.2019 со звезды 7
    # по возрастанию → 15.01.2020 = 7 + 23 = 30 → 3. Ручной расчёт проверки 2-й волны.
    r = calculate(BirthInput(2020, 1, 15, place="Москва"))
    assert nsk(r)["day"]["number"] == 9
    assert nsk(r)["day"]["alt_other_school"] == {"method": "ja_leap_wiki", "number": 3}
    assert any("школы расходятся" in w for w in r["warnings"])
    assert "alt_other_school" not in nsk(calculate(BirthInput(1990, 5, 15, place="Москва")))["day"]


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


# ---------------------------------------------------------------------------
# Повторная проверка (приоритет 1): варианты «閏», китайское правило, звезда часа, западное третье число
# ---------------------------------------------------------------------------

def test_day_star_ja_leap_is_sonoda_rule():
    """園田真次郎『干支九星閏解説』(1930), NDL https://dl.ndl.go.jp/pid/1104437 , с. 28–29: «閏», если день 甲午
    совпадает с солнцестоянием или раньше него («甲午の日が冬至の日と一致するか亦は冬至の日より手前に這入るを以て
    置閏歳»). Значит, солнцестояние 癸巳 → предыдущий 甲子 (閏 нет), 甲午 → следующий 甲子 (閏) — это `ja_leap`.
    Зимнее солнцестояние 22.12.2019 (JST) = 癸巳, 23.12.1939 = 甲午."""
    assert day_star(date(2019, 12, 22), "ja_leap")["switch_jiazi"] == "2019-11-23"      # 癸巳 → предыдущий 甲子
    assert day_star(date(2020, 1, 21), "ja_leap")["leap_segment"] is False
    r = day_star(date(1939, 12, 23), "ja_leap")                                         # 甲午 → «閏»
    assert r["leap_segment"] and r["number"] == 7 and r["day_ganzhi"] == "甲午"
    # Сонода, с. 15–16 (зимний «閏»): «癸己の七赤中宮の日の、翌日甲午の日にも、亦七赤が中宮に起つて» — 七赤 два дня
    assert day_star(date(1939, 12, 22), "ja_leap")["number"] == 7


def test_day_star_ja_leap_wiki_vs_nob2018_calendmate():
    """NOB «日家九星の計算方法（改訂版）» (способ K.Oka / Calend Mate):
    https://nobml.hatenablog.jp/entry/20180113/1515770790 — «1951年〜2050年の間で「九星の閏」が置かれるのは、
    1951年夏、1962年冬、1974年夏、1985年冬、1997年夏、2008年冬、2019年冬、2031年冬、2042年冬»; пример: 2008-12-31 = 九紫,
    переключения 2008-05-24 (九紫), 2008-12-20 (甲午, 七赤), 2009-07-18 (九紫), 2010-01-14 (一白)."""
    got = [x for x in _leap_positions("ja_leap_wiki") if 1951 <= int(x[:4]) <= 2050]
    assert got == ["1951夏", "1962冬", "1974夏", "1985冬", "1997夏", "2008冬", "2019冬", "2031冬", "2042冬"]
    for d, star in [("2008-12-31", 9), ("2008-05-24", 9), ("2008-12-20", 7), ("2009-07-18", 9), ("2010-01-14", 1)]:
        assert day_star(date.fromisoformat(d), "ja_leap_wiki")["number"] == star, d


def test_day_star_ja_jiawu_vs_nob2012_and_wiki_brackets():
    """Второе правило ja.wikipedia «九星» («冬至または夏至の前後1日以内に甲午がある場合に九星の閏を置く»), источник —
    NOB 2012: https://nobml.hatenablog.jp/entry/20121231/1356881216 : «1951年〜2050年の間で「九星の閏」が置かれるのは、
    1951年夏、1962年冬、1974年夏、1985年冬、1997年夏、2008年冬、2020年夏、2031年冬、2043年夏»; примеры таблиц 2019 и 2031
    (после «調整»). Этот вариант даёт «скобочные» альтернативы ja.wikipedia 1940 夏 и 2043 夏."""
    got = _leap_positions("ja_jiawu")
    assert [x for x in got if 1951 <= int(x[:4]) <= 2050] == [
        "1951夏", "1962冬", "1974夏", "1985冬", "1997夏", "2008冬", "2020夏", "2031冬", "2043夏"]
    assert "1940夏" in got and "1939冬" not in got and "2043夏" in got and "2042冬" not in got
    assert "1917夏" in got and "1928夏" in got and "2054夏" in got
    for d, star in [("2008-12-31", 9), ("2018-06-01", 9), ("2018-11-28", 1), ("2019-05-27", 9), ("2019-11-23", 1),
                    ("2020-06-20", 3), ("2021-01-16", 1), ("2031-05-24", 9), ("2031-12-20", 7), ("2032-07-17", 9),
                    ("2033-01-13", 1)]:
        assert day_star(date.fromisoformat(d), "ja_jiawu")["number"] == star, d


def test_day_star_every_wiki_bracket_is_some_variant():
    """Каждая альтернатива в скобках ja.wikipedia даётся одним из вариантов модуля."""
    union = set(_leap_positions("ja_leap")) | set(_leap_positions("ja_jiawu"))
    for x in ["1917夏", "1928冬", "1940夏", "1951冬", "2020夏", "2043夏", "2054冬"]:
        assert x in union, x


# Календарь skillon.com «Daily Feng Shui» (строка «Day Flying Star»), страницы
# https://www.skillon.com/feng-shui-flying-star.cfm/date/<YYYY-MM-DD> (доступны 2020–2030), запрошены 14.10.2026.
# Окна вокруг солнцестояний 21.06.2025, 21.12.2025 (день 甲子), 21.06.2026 и случайные даты 2020–2030.
@pytest.mark.parametrize("d,star", [
    ("2020-03-13", 7), ("2020-04-06", 4), ("2020-04-20", 9), ("2020-07-11", 9), ("2020-11-09", 5),
    ("2022-03-17", 3), ("2023-12-17", 6), ("2024-02-01", 5),
    ("2025-06-20", 6), ("2025-06-21", 3), ("2025-06-22", 2), ("2025-06-23", 1), ("2025-06-24", 9), ("2025-06-25", 8),
    ("2025-12-19", 2), ("2025-12-20", 1), ("2025-12-21", 4), ("2025-12-22", 5),
    ("2026-01-24", 2), ("2026-03-21", 4), ("2026-06-19", 4), ("2026-06-20", 5), ("2026-06-21", 4), ("2026-06-22", 3),
    ("2026-07-01", 3), ("2027-02-08", 4), ("2027-05-26", 3), ("2027-11-12", 8), ("2028-06-10", 6),
    ("2029-07-27", 6), ("2030-06-27", 4), ("2030-09-21", 8),
])
def test_day_star_cn_after_vs_skillon(d, star):
    assert day_star(date.fromisoformat(d), "cn_after")["number"] == star


def test_day_star_cn_after_differs_from_nearest():
    # 01.07.2026: летнее солнцестояние 21.06 (день 丙寅), ближайший 甲子 — 19.06 (Инь-дунь с 9 → 6),
    # первый 甲子 после — 18.08 (до него звёзды считаются от него назад: 9 + 48 → 3). skillon: 3.
    assert day_star(date(2026, 7, 1), "ja_leap")["number"] == 6
    r = day_star(date(2026, 7, 1), "cn_after")
    assert r["number"] == 3 and r["switch_jiazi"] == "2026-08-18" and r["dun"] == "yin"


def test_hour_star_table_vs_ja_wikipedia():
    """ja.wikipedia «九星», таблица «時刻と九星の対応» (陽遁/陰遁 × три группы ветвей дня × 12 часов)."""
    yang = {0: [1, 2, 3, 4, 5, 6, 7, 8, 9, 1, 2, 3], 1: [4, 5, 6, 7, 8, 9, 1, 2, 3, 4, 5, 6],
            2: [7, 8, 9, 1, 2, 3, 4, 5, 6, 7, 8, 9]}
    yin = {0: [9, 8, 7, 6, 5, 4, 3, 2, 1, 9, 8, 7], 1: [6, 5, 4, 3, 2, 1, 9, 8, 7, 6, 5, 4],
           2: [3, 2, 1, 9, 8, 7, 6, 5, 4, 3, 2, 1]}
    # Дни внутри сегментов ja_leap: Ян-дунь 30.12.1989–27.06.1990, Инь-дунь с 28.06.1990.
    for base, table in ((date(1990, 1, 29), yang), (date(1990, 7, 10), yin)):
        for k in range(12):                      # 12 дней подряд покрывают все ветви
            d = base + timedelta(days=k)
            br = (d.toordinal() + 1721425 + 49) % 60 % 12
            grp = 0 if br in (0, 3, 6, 9) else 1 if br in (1, 4, 7, 10) else 2
            for hi in range(1, 12):              # 丑…亥 (子 в 23:00 относится к следующему дню, см. ниже)
                h = 2 * hi - 1
                r = hour_star(datetime(d.year, d.month, d.day, h, 30), "ja")
                assert r["hour_branch_index"] == hi and r["number"] == table[grp][hi], (d, h)
            assert hour_star(datetime(d.year, d.month, d.day, 0, 30), "ja")["number"] == table[grp][0]


def test_hour_star_ja_takashima_1935():
    """高島易断所本部神宮館『九星極意八百十通変化奥伝』(1935), NDL https://dl.ndl.go.jp/pid/1137380 , с. 25:
    «陽遁となりたる甲子の日の子の刻（午後十一時より午前一時迄）に時家九星の一白を配し、丑の刻に二黑、寅の刻に三碧»;
    陰遁 — «夏至に近き…甲子の日の子の刻に九紫を配し丑の刻に八白…»; таблица: «冬至に最も近き甲子の日より夏至に近き
    癸亥の日迄用ゆ». 甲子, ближайший к зимнему солнцестоянию 1989 г. (22.12 JST), — 30.12.1989."""
    assert day_star(date(1989, 12, 30), "ja_leap")["switch_jiazi"] == "1989-12-30"
    assert hour_star(datetime(1989, 12, 30, 0, 30), "ja")["number"] == 1        # 子 дня 甲子 → 一白
    assert hour_star(datetime(1989, 12, 30, 1, 30), "ja")["number"] == 2        # 丑 → 二黒
    assert hour_star(datetime(1989, 12, 30, 3, 30), "ja")["number"] == 3        # 寅 → 三碧
    r = hour_star(datetime(1989, 12, 29, 23, 30), "ja")                          # 23:30 — уже 子 дня 甲子
    assert r["day_for_hour"] == "1989-12-30" and r["number"] == 1
    # Тот же день по lunar-python (дунь по дате солнцестояния, 23:00 — тот же день 癸亥): Ян-дунь с 22.12 → 7.
    assert hour_star(datetime(1989, 12, 29, 23, 30), "cn_solstice")["number"] == 7
    # 23.12.1989 (дата после солнцестояния, но до 甲子): ja ещё Инь-дунь, cn_solstice уже Ян-дунь.
    assert hour_star(datetime(1989, 12, 23, 12, 0), "ja")["dun"] == "yin"
    assert hour_star(datetime(1989, 12, 23, 12, 0), "cn_solstice")["dun"] == "yang"
    # Инь-дунь: 甲子, ближайший к летнему солнцестоянию 1990 (21.06 JST), — 28.06.1990 → час 子 = 九紫.
    assert day_star(date(1990, 6, 28), "ja_leap")["switch_jiazi"] == "1990-06-28"
    assert hour_star(datetime(1990, 6, 28, 0, 10), "ja")["number"] == 9
    assert hour_star(datetime(1990, 6, 28, 1, 10), "ja")["number"] == 8


def test_hour_star_cn_solstice_vs_lunar_python():
    """lunar-python `Lunar.getTimeNineStar` — 200 случайных моментов (время считается местным)."""
    from lunar_python import Solar
    rnd = random.Random(11)
    for _ in range(200):
        d = date(1901, 3, 1) + timedelta(days=rnd.randint(0, 72000))
        h, mi = rnd.randint(0, 23), rnd.randint(0, 59)
        lp = CN.index(Solar.fromYmdHms(d.year, d.month, d.day, h, mi, 0).getLunar().getTimeNineStar().getNumber()) + 1
        assert hour_star(datetime(d.year, d.month, d.day, h, mi), "cn_solstice")["number"] == lp, (d, h, mi)


def test_hour_star_in_calculate():
    r = calculate(BirthInput(1990, 5, 15, 14, 30, place="Москва", gender="female"))      # T1: день 庚辰, час 未
    h = nsk(r)["hour"]
    assert h["hour_branch"] == "未" and h["zi_hour_star"] == 4 and h["number"] == 2 and h["dun"] == "yang"
    r2 = calculate(BirthInput(1984, 2, 4, 23, 30, place="Москва", gender="male"))         # T2: 23:30 → 子 дня 己巳
    h2 = nsk(r2)["hour"]
    assert h2["day_for_hour"] == "1984-02-05" and h2["number"] == 7
    assert h2["alt_other_school"] == {"method": "cn_solstice", "number": 4}
    assert "hour" not in nsk(calculate(BirthInput(1990, 5, 15, place="Москва")))
    assert "hour" not in nsk(calculate(BirthInput(1990, 5, 15, 14, 30, place="Москва"), hour_star_method=None))


def test_tendency_western_center_rule():
    """Западная школа: при совпадении звёзд третье число = 5 (звезда года в центре таблицы месяца).
    Плагин WordPress «Nine Star Ki» 1.1.1 (https://wordpress.org/plugins/nine-star-ki/, changelog «use method of
    Yoshikawa for the calculation of the third number»): таблицы zoekmaandgetal/zoekuitingsgetal в nine-star-ki.php.
    9starki.com Lesson 6: «find the position of the first number (the annual number) in the monthly chart»."""
    zm = {1: [6, 8, 7, 6, 5, 4, 3, 2, 1, 9, 8, 7], 2: [9, 2, 1, 9, 8, 7, 6, 5, 4, 3, 2, 1],
          3: [3, 5, 4, 3, 2, 1, 9, 8, 7, 6, 5, 4]}
    zm.update({4: zm[1], 7: zm[1], 5: zm[2], 8: zm[2], 6: zm[3], 9: zm[3]})
    zu = {1: [9, 7, 8, 9, 1, 2, 3, 4, 5, 6, 7, 8], 2: [7, 5, 6, 7, 8, 9, 1, 2, 3, 4, 5, 6],
          3: [5, 3, 4, 5, 6, 7, 8, 9, 1, 2, 3, 4], 4: [3, 1, 2, 3, 4, 5, 6, 7, 8, 9, 1, 2],
          5: [1, 8, 9, 1, 2, 3, 4, 5, 6, 7, 8, 9], 6: [8, 6, 7, 8, 9, 1, 2, 3, 4, 5, 6, 7],
          7: [6, 4, 5, 6, 7, 8, 9, 1, 2, 3, 4, 5], 8: [4, 2, 3, 4, 5, 6, 7, 8, 9, 1, 2, 3],
          9: [2, 9, 1, 2, 3, 4, 5, 6, 7, 8, 9, 1]}
    for p in range(1, 10):
        for i, mth in enumerate(zm[p]):
            assert tendency_palace(p, mth, "male", "western")["number"] == zu[p][i], (p, mth)
        assert tendency_palace(p, p, None, "western")["number"] == 5
    # Вне диагонали школы совпадают.
    for p in range(1, 10):
        for mth in range(1, 10):
            if p != mth:
                assert tendency_palace(p, mth, "female", "western")["number"] == tendency_palace(p, mth, "female")["number"]
    # 01.08.2000: 9.9 → японский 中宮傾斜 1, западная запись 9.9.5.
    r = calculate(BirthInput(2000, 8, 1, 12, 0, place="Москва", gender="female"))
    assert nsk(r)["notation"] == "9.9.1" and nsk(r)["tendency"]["alt_western"]["number"] == 5
    rw = calculate(BirthInput(2000, 8, 1, 12, 0, place="Москва", gender="female"), tendency_method="western")
    assert nsk(rw)["notation"] == "9.9.5" and nsk(rw)["tendency"]["alt_japanese"]["number"] == 1


def test_day_star_switch_intervals_invariant():
    """Между 甲子-переключениями любого японского варианта — ровно 180 или 240 дней (1800–2200)."""
    from calculators.ninestar import _Zone, _day_star_switches
    for m in ("ja_leap", "ja_leap_wiki", "ja_jiawu"):
        ev = _day_star_switches(1800, 2200, m, _Zone("UTC+09:00"))
        assert {(b[0] - a[0]).days for a, b in zip(ev, ev[1:])} == {180, 240}, m


def test_hour_star_zi_invariant():
    """Звезда часа 子: Ян-дунь только 1/4/7, Инь-дунь только 9/6/3; за сутки 12 значений подряд."""
    rnd = random.Random(3)
    for _ in range(60):
        d = date(1950, 1, 1) + timedelta(days=rnd.randint(0, 36000))
        for meth in ("ja", "cn_solstice"):
            z = hour_star(datetime(d.year, d.month, d.day, 0, 30), meth)
            assert z["number"] in ({1, 4, 7} if z["dun"] == "yang" else {9, 6, 3})
            seq = [hour_star(datetime(d.year, d.month, d.day, 2 * k + 1, 0), meth)["number"] for k in range(11)]
            step = 1 if z["dun"] == "yang" else -1
            assert all((b - a - step) % 9 == 0 for a, b in zip([z["number"]] + seq, seq))
