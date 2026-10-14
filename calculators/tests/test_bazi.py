"""Тесты калькулятора Ба-цзы (calculators/bazi.py).

Сверка: (1) независимые опубликованные источники (URL в комментариях),
(2) lunar-python (ему передаётся пекинское время, эквивалентное моменту рождения, —
для года/месяца/Столпов удачи, и «время карты» — для дня/часа),
(3) инварианты.
"""
from __future__ import annotations

import json
import random
from datetime import date, datetime, timedelta

import pytest
from lunar_python import Solar
from lunar_python.util import LunarUtil

from calculators import bazi
from calculators.bazi import calculate, day_index, ganzhi, year_index
from calculators.common.time import BirthInput, normalize

T1 = BirthInput(1990, 5, 15, 14, 30, place="Москва", gender="female", name="Иванова Анна Сергеевна")
T2 = BirthInput(1984, 2, 4, 23, 30, place="Москва", gender="male", name="Петров Дмитрий Олегович")
T3 = BirthInput(2004, 2, 29, 8, 15, place="Санкт-Петербург", gender="female")
T4 = BirthInput(1879, 3, 14, 11, 30, tz="LMT", lat=48.4011, lon=9.9876, gender="male", name="Albert Einstein")
# Дополнительный вектор: за 19 минут ДО Личуня 1984 (Личунь = 15:18:44 UT = 18:18:44 MSK)
T2_BEFORE = BirthInput(1984, 2, 4, 18, 0, place="Москва", gender="male")


def chart(b, **kw):
    return calculate(b, **kw)["chart"]


# ---------------------------------------------------------------------------
# 1. Шестидесятеричная арифметика — внешние векторы
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("d,expected", [
    # https://en.wikipedia.org/wiki/Sexagenary_cycle (раздел «Sexagenary days», примеры)
    (date(1949, 10, 1), "甲子"),
    (date(1912, 2, 18), "甲子"),
    (date(1592, 12, 31), "甲申"),
    # https://chinadigitaltimes.net/chinese/?p=99537 — день рождения Мао Цзэдуна 26.12.1893 = 丁酉
    (date(1893, 12, 26), "丁酉"),
])
def test_day_pillar_external(d, expected):
    assert ganzhi(day_index(d)) == expected


def test_year_index_external():
    # Wikipedia: 1967 − 3 = 1964; 1964 mod 60 = 44 → 丁未 (нумерация с 1); у нас (Y−4) mod 60
    assert ganzhi(year_index(1967)) == "丁未"
    assert ganzhi(year_index(1984)) == "甲子"
    assert ganzhi(year_index(1879)) == "己卯"


def test_day_formula_vs_lunar_python_many_days():
    d = date(1800, 1, 1)
    while d < date(2200, 1, 1):
        s = Solar.fromYmdHms(d.year, d.month, d.day, 12, 0, 0)
        assert ganzhi(day_index(d)) == s.getLunar().getDayInGanZhi(), d
        d += timedelta(days=97)


def test_five_tigers_and_five_rats_tables():
    # Пять тигров: 甲己→丙寅, 乙庚→戊寅, 丙辛→庚寅, 丁壬→壬寅, 戊癸→甲寅
    assert [bazi.STEMS[bazi.month_first_stem(s)][0] for s in range(10)] == list("丙戊庚壬甲丙戊庚壬甲")
    # Пять крыс (ранняя Крыса) — таблица mingli.ru (https://www.mingli.ru/blog/post/2487):
    # 甲己→甲子, 乙庚→丙子, 丙辛→戊子, 丁壬→庚子, 戊癸→壬子
    assert [bazi.STEMS[bazi.zi_first_stem(s)][0] for s in range(10)] == list("甲丙戊庚壬甲丙戊庚壬")


def test_mingli_early_late_rat_example():
    # mingli.ru (Н. Цыганова, 2023): «1 февраля Ранняя Крыса будет огненной, а Поздняя — земляной».
    # 01.02.2023 — день 庚寅; ранняя Крыса 00:30 → 丙子, поздняя 23:30 → 戊子, день не меняется.
    # https://www.mingli.ru/blog/post/2487
    early = calculate(BirthInput(2023, 2, 1, 0, 30, tz="UTC+08:00"), solar_time="clock")
    late = calculate(BirthInput(2023, 2, 1, 23, 30, tz="UTC+08:00"), solar_time="clock", zi_hour="late")
    assert early["pillars"]["day"]["ganzhi"] == "庚寅" and early["pillars"]["hour"]["ganzhi"] == "丙子"
    assert late["pillars"]["day"]["ganzhi"] == "庚寅" and late["pillars"]["hour"]["ganzhi"] == "戊子"


# ---------------------------------------------------------------------------
# 2. Солнечные термины
# ---------------------------------------------------------------------------

def test_li_chun_1984_vs_lunar_python():
    jd = bazi.li_chun_jd(1984)
    utc = bazi.jd_to_utc(jd)
    bj = Solar.fromYmd(1984, 2, 10).getLunar().getJieQiTable()["立春"]
    bj_dt = datetime(bj.getYear(), bj.getMonth(), bj.getDay(), bj.getHour(), bj.getMinute(), bj.getSecond())
    diff = abs((utc.replace(tzinfo=None) + timedelta(hours=8)) - bj_dt).total_seconds()
    assert diff < 60
    assert utc.strftime("%Y-%m-%d %H:%M") == "1984-02-04 15:18"   # = 18:18 MSK


@pytest.mark.parametrize("year,cst", [
    # Личунь по времени CST (UTC+8), Master Sean Chan:
    ("1984", "1984-02-04 23:18"),  # https://www.masterseanchan.com/ru/bazi-1984/
    ("1990", "1990-02-04 10:14"),  # https://www.masterseanchan.com/ru/bazi-1990/
    ("2004", "2004-02-04 19:56"),  # https://www.masterseanchan.com/ru/bazi-2004/
])
def test_li_chun_vs_masterseanchan(year, cst):
    utc = bazi.jd_to_utc(bazi.li_chun_jd(int(year)))
    assert (utc + timedelta(hours=8)).strftime("%Y-%m-%d %H:%M") == cst


@pytest.mark.parametrize("year,deg,hk_date", [
    # Гонконгская обсерватория, таблицы 公曆與農曆日期對照表 (дата цзе по времени UTC+8):
    # https://www.hko.gov.hk/tc/gts/time/calendar/text/files/T1984c.txt
    (1984, 315, "1984-02-04"), (1984, 345, "1984-03-05"), (1984, 15, "1984-04-04"), (1984, 45, "1984-05-05"),
    # https://www.hko.gov.hk/tc/gts/time/calendar/text/files/T1990c.txt
    (1990, 345, "1990-03-06"), (1990, 45, "1990-05-06"),
    # https://www.hko.gov.hk/tc/gts/time/calendar/text/files/T2004c.txt
    (2004, 345, "2004-03-05"), (2004, 45, "2004-05-05"),
])
def test_jie_dates_vs_hong_kong_observatory(year, deg, hk_date):
    import swisseph as swe
    jd = bazi.find_sun_longitude(deg, swe.julday(year, 6, 30, 0.0), search_back=True)
    hk = bazi.jd_to_utc(jd) + timedelta(hours=8)
    assert hk.strftime("%Y-%m-%d") == hk_date


# ---------------------------------------------------------------------------
# 3. Эталонные персоны T1–T4 + вектор перед Личунем
# ---------------------------------------------------------------------------

def test_t1_default():
    r = calculate(T1)
    assert r["chart"] == "庚午 辛巳 庚辰 癸未"
    assert r["inputs_used"]["utc"] == "1990-05-15T10:30:00Z"  # летнее время СССР UTC+4
    assert r["day_master"]["cn"] == "庚"
    lp = r["luck_pillars"]
    assert lp["direction"] == "backward"   # Ян-год (庚) + женщина
    assert [p["ganzhi"] for p in lp["pillars"][:4]] == ["庚辰", "己卯", "戊寅", "丁丑"]
    assert lp["start"]["years"] == 3 and lp["start"]["months"] == 2
    # во всех школах одинаково (14:30 часов / 13:00 LMT / 13:04 истинное — всё час 未)
    assert {(a["day"], a["hour"]) for a in r["alternatives"]} == {("庚辰", "癸未")}


def test_t2_li_chun_day_late_zi_variants():
    # По умолчанию (истинное солнечное время 22:46) — час 亥, день 戊辰
    assert chart(T2) == "甲子 丙寅 戊辰 癸亥"
    # Время часов 23:30, поздний час Крысы (晚子时): день остаётся 戊辰, час 甲子
    assert chart(T2, solar_time="clock", zi_hour="late") == "甲子 丙寅 戊辰 甲子"
    # Время часов, смена дня в 23:00: день 己巳, час 甲子
    assert chart(T2, solar_time="clock", zi_hour="early") == "甲子 丙寅 己巳 甲子"
    # Среднее солнечное (LMT 23:00:28) — тоже час Крысы
    assert chart(T2, solar_time="mean") == "甲子 丙寅 戊辰 甲子"
    assert chart(T2, solar_time="mean", zi_hour="early") == "甲子 丙寅 己巳 甲子"
    r = calculate(T2)
    assert r["solar_terms"]["li_chun_utc"].startswith("1984-02-04T15:18")
    assert r["luck_pillars"]["direction"] == "forward"
    assert r["luck_pillars"]["pillars"][0]["ganzhi"] == "丁卯"
    assert abs(r["luck_pillars"]["start"]["decimal_years"] - 9.846) < 0.01
    assert any("立春" in w for w in r["warnings"])


def test_t2_before_li_chun():
    r = calculate(T2_BEFORE, solar_time="clock")
    assert r["chart"] == "癸亥 乙丑 戊辰 辛酉"
    assert r["solar_terms"]["bazi_year"] == 1983
    lp = r["luck_pillars"]
    assert lp["direction"] == "backward"   # Инь-год (癸) + мужчина
    assert lp["pillars"][0]["ganzhi"] == "甲子"
    assert lp["jie_used"]["cn"] == "小寒"


def test_t3_feb29():
    r = calculate(T3)
    assert r["chart"] == "甲申 丙寅 戊寅 丙辰"
    assert r["luck_pillars"]["direction"] == "backward"   # Ян-год + женщина
    assert r["luck_pillars"]["pillars"][0]["ganzhi"] == "乙丑"
    assert chart(T3, solar_time="clock") == "甲申 丙寅 戊寅 丙辰"


def test_t4_einstein_external():
    # https://synthesisastrology.com/chart/albert-einstein/example/bazi :
    # 己卯 丁卯 丙申 甲午; Столпы удачи обратные с 2.8 лет: 丙寅 乙丑 甲子 癸亥 壬戌 辛酉 庚申 己未
    r = calculate(T4)
    assert r["chart"] == "己卯 丁卯 丙申 甲午"
    lp = r["luck_pillars"]
    assert lp["direction"] == "backward"
    assert [p["ganzhi"] for p in lp["pillars"][:8]] == ["丙寅", "乙丑", "甲子", "癸亥", "壬戌", "辛酉", "庚申", "己未"]
    assert round(lp["start"]["decimal_years"], 1) == 2.8
    # там же: скрытые стволы ветви дня 申 — 庚 壬 戊, десять божеств
    hs = r["pillars"]["day"]["hidden_stems"]
    assert [h["cn"] for h in hs] == ["庚", "壬", "戊"]
    assert [h["ten_god"]["cn"] for h in hs] == ["偏财", "七杀", "食神"]
    assert r["pillars"]["year"]["stem_ten_god"]["cn"] == "伤官"
    assert r["pillars"]["month"]["stem_ten_god"]["cn"] == "劫财"
    assert r["pillars"]["hour"]["stem_ten_god"]["cn"] == "偏印"


def test_mao_three_pillars_external():
    # https://chinadigitaltimes.net/chinese/?p=99537 — 26.12.1893: 癸巳 甲子 丁酉 (без часа)
    r = calculate(BirthInput(1893, 12, 26, tz="LMT", lat=27.915, lon=112.53, gender="male"))
    assert r["chart"].startswith("癸巳 甲子 丁酉")
    assert r["pillars"]["hour"] is None
    assert any("неизвестно" in w for w in r["warnings"])


# ---------------------------------------------------------------------------
# 4. Сверка с lunar-python
# ---------------------------------------------------------------------------

def _lunar_ec(dt: datetime, sect: int):
    ec = Solar.fromYmdHms(dt.year, dt.month, dt.day, dt.hour, dt.minute, dt.second).getLunar().getEightChar()
    ec.setSect(sect)
    return ec


@pytest.mark.parametrize("b", [T1, T2, T3, T4, T2_BEFORE])
@pytest.mark.parametrize("mode", ["clock", "mean", "true"])
@pytest.mark.parametrize("zi", ["late", "early"])
def test_reference_persons_vs_lunar_python(b, mode, zi):
    r = calculate(b, solar_time=mode, zi_hour=zi)
    n = normalize(b)
    # год/месяц: lunar-python получает пекинское время, эквивалентное моменту рождения
    bj = (n.utc + timedelta(hours=8)).replace(tzinfo=None)
    ec_bj = _lunar_ec(bj, 2)
    assert r["pillars"]["year"]["ganzhi"] == ec_bj.getYear()
    assert r["pillars"]["month"]["ganzhi"] == ec_bj.getMonth()
    # день/час: lunar-python получает «время карты» (sect 2 = поздний Цзы, 1 = смена в 23:00)
    ct = datetime.fromisoformat(r["inputs_used"]["chart_time"])
    ec = _lunar_ec(ct, 2 if zi == "late" else 1)
    assert r["pillars"]["day"]["ganzhi"] == ec.getDay()
    assert r["pillars"]["hour"]["ganzhi"] == ec.getTime()
    # Столпы удачи (sect 2: 4320 мин = 1 год)
    yun = ec_bj.getYun(1 if b.gender == "male" else 0, 2)
    lp = r["luck_pillars"]
    assert (lp["direction"] == "forward") == yun.isForward()
    assert [p["ganzhi"] for p in lp["pillars"][:8]] == [d.getGanZhi() for d in yun.getDaYun(9)[1:]]
    ours = lp["start"]["years"] * 360 + lp["start"]["months"] * 30 + lp["start"]["days"]
    theirs = yun.getStartYear() * 360 + yun.getStartMonth() * 30 + yun.getStartDay()
    assert abs(ours - theirs) <= 1


def test_random_charts_vs_lunar_python():
    """400 случайных моментов 1901–2099 (UTC+8, время часов): все 4 столпа + Столпы удачи."""
    rnd = random.Random(20261014)
    checked = 0
    for _ in range(400):
        dt = datetime(1901, 1, 1) + timedelta(minutes=rnd.randrange(0, 199 * 365 * 1440))
        g = rnd.choice(["male", "female"])
        zi = rnd.choice(["late", "early"])
        b = BirthInput(dt.year, dt.month, dt.day, dt.hour, dt.minute, tz="UTC+08:00", gender=g)
        r = calculate(b, solar_time="clock", zi_hour=zi)
        jd = normalize(b).jd_ut
        st = r["solar_terms"]
        near = min(abs(jd - st["prev_jie"]["jd_ut"]), abs(st["next_jie"]["jd_ut"] - jd))
        if near < 10 / 1440:      # ближе 10 минут к цзе — точность lunar-python недостаточна
            continue
        ec = _lunar_ec(dt, 2 if zi == "late" else 1)
        assert r["chart"] == f"{ec.getYear()} {ec.getMonth()} {ec.getDay()} {ec.getTime()}", (dt, zi)
        yun = ec.getYun(1 if g == "male" else 0, 2)
        lp = r["luck_pillars"]
        assert lp["pillars"][0]["ganzhi"] == yun.getDaYun(2)[1].getGanZhi()
        ours = lp["start"]["years"] * 360 + lp["start"]["months"] * 30 + lp["start"]["days"]
        theirs = yun.getStartYear() * 360 + yun.getStartMonth() * 30 + yun.getStartDay()
        assert abs(ours - theirs) <= 1, dt
        # стадии жизненного цикла ДМ по ветвям и十神 стволов
        assert r["pillars"]["year"]["life_stage_dm"]["cn"] == ec.getYearDiShi()
        assert r["pillars"]["month"]["life_stage_dm"]["cn"] == ec.getMonthDiShi()
        assert r["pillars"]["day"]["life_stage_dm"]["cn"] == ec.getDayDiShi()
        assert r["pillars"]["hour"]["life_stage_dm"]["cn"] == ec.getTimeDiShi()
        assert r["pillars"]["year"]["stem_ten_god"]["cn"] == ec.getYearShiShenGan()
        assert [h["ten_god"]["cn"] for h in r["pillars"]["hour"]["hidden_stems"]] == ec.getTimeShiShenZhi()
        assert r["pillars"]["day"]["nayin"]["cn"] == ec.getDayNaYin()
        assert r["tai_yuan"]["ganzhi"] == ec.getTaiYuan()
        checked += 1
    assert checked > 380


# ---------------------------------------------------------------------------
# 5. Справочные таблицы против lunar-python
# ---------------------------------------------------------------------------

def test_tables_vs_lunar_python():
    for i in range(60):
        gz = ganzhi(i)
        assert bazi.nayin(i)["cn"] == LunarUtil.NAYIN[gz]
        assert LunarUtil.JIA_ZI[i] == gz
    for b in range(12):
        assert [bazi.STEMS[s][0] for s, _r, _w in bazi.HIDDEN_STEMS[b]] == LunarUtil.ZHI_HIDE_GAN[bazi.BRANCHES[b][0]]
        assert abs(sum(w for _s, _r, w in bazi.HIDDEN_STEMS[b]) - 1.0) < 1e-9
    for a in range(10):
        for c in range(10):
            key = bazi.STEMS[a][0] + bazi.STEMS[c][0]
            assert bazi.ten_god(a, c)["cn"] == LunarUtil.SHI_SHEN[key]


def test_life_stage_anchor_points():
    # 甲 长生 в 亥, 帝旺 в 卯; 乙 长生 в 午, 帝旺 в 寅; 庚 长生 в 巳; 辛 长生 в 子; 壬 长生 в 申; 癸 长生 в 卯
    assert bazi.life_stage(0, 11)["cn"] == "长生" and bazi.life_stage(0, 3)["cn"] == "帝旺"
    assert bazi.life_stage(1, 6)["cn"] == "长生" and bazi.life_stage(1, 2)["cn"] == "帝旺"
    assert bazi.life_stage(6, 5)["cn"] == "长生" and bazi.life_stage(7, 0)["cn"] == "长生"
    assert bazi.life_stage(8, 8)["cn"] == "长生" and bazi.life_stage(9, 3)["cn"] == "长生"
    assert bazi.life_stage(2, 6)["cn"] == "帝旺" and bazi.life_stage(4, 6)["cn"] == "帝旺"


def test_season_states():
    # весна (寅): 木旺 火相 水休 金囚 土死
    got = {e: bazi.season_state(e, 2)["cn"] for e in bazi.ELEMENTS}
    assert got == {"wood": "旺", "fire": "相", "water": "休", "metal": "囚", "earth": "死"}


# ---------------------------------------------------------------------------
# 6. Инварианты и граничные случаи
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("b", [T1, T2, T3, T4, T2_BEFORE])
def test_invariants(b):
    r = calculate(b)
    json.dumps(r, ensure_ascii=False)
    p = r["pillars"]
    for k in ("year", "month", "day", "hour"):
        assert p[k]["stem"]["index"] % 2 == p[k]["branch"]["index"] % 2   # полярность ствола = ветви
    # правило пяти тигров и пяти крыс
    ys = p["year"]["stem"]["index"]
    slot = (p["month"]["branch"]["index"] - 2) % 12
    assert p["month"]["stem"]["index"] == (bazi.month_first_stem(ys) + slot) % 10
    assert p["day"]["stem_ten_god"] is None
    assert sum(r["elements"]["visible"].values()) == 8
    assert abs(sum(r["elements"]["weighted_with_hidden"].values()) - 8.0) < 0.05
    assert r["method"] == "bazi" and r["steps"]


def test_no_gender_no_luck_and_no_longitude_fallback():
    r = calculate(BirthInput(1990, 5, 15, 14, 30, tz="Europe/Moscow"))
    assert r["luck_pillars"] is None
    assert r["inputs_used"]["options"]["solar_time"] == "clock"
    assert any("Пол не указан" in w for w in r["warnings"])


def test_new_day_after_midnight_with_solar_time():
    # 00:20 MSK (UTC+3) в Москве: LMT ≈ 23:50 предыдущих суток → школа 'late' даёт день ПРЕДЫДУЩЕЙ даты
    b = BirthInput(1984, 2, 5, 0, 20, place="Москва", gender="male")
    r_late = calculate(b, solar_time="mean", zi_hour="late")
    r_early = calculate(b, solar_time="mean", zi_hour="early")
    r_clock = calculate(b, solar_time="clock")
    assert r_late["pillars"]["day"]["ganzhi"] == "戊辰"
    assert r_early["pillars"]["day"]["ganzhi"] == "己巳"
    assert r_clock["pillars"]["day"]["ganzhi"] == "己巳"
    assert r_late["pillars"]["hour"]["ganzhi"] == r_early["pillars"]["hour"]["ganzhi"] == "甲子"


def test_interactions_and_stars_examples():
    r = calculate(T3)
    clashes = {c["branches"] for c in r["interactions"]["branch_clashes"]}
    assert "申寅" in clashes
    stars = {(s["star"], s["ru"]): s for s in r["symbolic_stars"]}
    assert stars[("文昌", "Академическая звезда (Вэньчан, по стволу дня)")]["branches"] == "申"
    r2 = calculate(T1)
    assert any(d["branches"] == "巳午未" for d in r2["interactions"]["directional_combinations"])


def test_annual_pillars():
    r = calculate(T2, annual_from=2024, annual_to=2026)
    assert [a["ganzhi"] for a in r["annual_pillars"]] == ["甲辰", "乙巳", "丙午"]
