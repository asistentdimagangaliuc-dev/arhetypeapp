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


def test_season_table_all_rows():
    # таблица 4.11 базы знаний
    rows = {2: "旺相死囚休", 5: "休旺相死囚", 8: "死囚休旺相", 11: "相死囚休旺", 4: "囚休旺相死"}
    for mb, exp in rows.items():
        assert "".join(bazi.season_state(e, mb)["cn"] for e in bazi.ELEMENTS) == exp


def test_einstein_strength_strong():
    # synthesisastrology.com называет ДМ 丙 Эйнштейна сильным («strong in the technical sense»)
    # https://synthesisastrology.com/chart/albert-einstein/example/bazi
    assert calculate(T4)["strength_hint"]["label"] == "скорее сильный"


def test_luck_start_bound_and_void_and_nobleman_variant():
    rnd = random.Random(7)
    for _ in range(60):
        dt = datetime(1950, 1, 1) + timedelta(minutes=rnd.randrange(0, 70 * 365 * 1440))
        r = calculate(BirthInput(dt.year, dt.month, dt.day, dt.hour, dt.minute, tz="UTC", gender="male"),
                      solar_time="clock")
        assert 0 <= r["luck_pillars"]["start"]["decimal_years"] <= 10.5
    r = calculate(T4)
    void = [s for s in r["symbolic_stars"] if s["star"] == "空亡"]
    assert void[0]["branches"] == "辰巳"          # 丙申 → 甲午旬 → 辰巳
    # 庚: основной вариант 丑未, альтернативный 寅午 (T1: ДМ 庚)
    main = calculate(T1)["symbolic_stars"][0]["branches"]
    alt = calculate(T1, nobleman_variant="alt")["symbolic_stars"][0]["branches"]
    assert (main, alt) == ("丑未", "寅午")


# ---------------------------------------------------------------------------
# 7. Добавлено при адверсариальной проверке (волна 2, 14.10.2026)
# ---------------------------------------------------------------------------

def test_cli_boolean_solar_time_option():
    # CLI превращает `--opt solar_time=true` в булево True — раньше это падало с ValueError.
    from calculators.cli import _options
    opts = _options(["solar_time=true"])
    assert opts == {"solar_time": True}
    assert calculate(T2, **opts)["chart"] == calculate(T2)["chart"] == "甲子 丙寅 戊辰 癸亥"
    assert calculate(T2, solar_time="TRUE", zi_hour="Late")["chart"] == "甲子 丙寅 戊辰 癸亥"


def test_day_cycle_julian_eclipse_720bc():
    # https://zh.wikipedia.org/wiki/干支 : 鲁隐公三年二月己巳日 = 22.02.720 до н. э. (юлианский календарь)
    # Формула (JDN + 49) mod 60 верна и для юлианского JDN.
    import swisseph as swe
    jdn_jul = int(round(swe.julday(-719, 2, 22, 12.0, swe.JUL_CAL)))
    assert jdn_jul == 1458496
    assert ganzhi((jdn_jul + 49) % 60) == "己巳"


def test_skillon_late_rat_gui_wei_day():
    # https://www.skillon.com/bazi-feng-shui.cfm/topic/2728/early-vs-late-rat-hour :
    # «11:00 PM – 11:59 PM GuiWei 癸未 day, 甲子 JiaZi hour… day only changes at midnight»
    late = calculate(BirthInput(2025, 7, 13, 23, 30, tz="UTC+08:00"), solar_time="clock", zi_hour="late")
    early = calculate(BirthInput(2025, 7, 13, 23, 30, tz="UTC+08:00"), solar_time="clock", zi_hour="early")
    assert (late["pillars"]["day"]["ganzhi"], late["pillars"]["hour"]["ganzhi"]) == ("癸未", "甲子")
    assert (early["pillars"]["day"]["ganzhi"], early["pillars"]["hour"]["ganzhi"]) == ("甲申", "甲子")


def test_mao_four_pillars_external():
    # https://chinadigitaltimes.net/chinese/?p=99537 : «乾：癸巳 甲子 丁酉 甲辰» (час 辰 = 07–09; берём 08:00 LMT)
    r = calculate(BirthInput(1893, 12, 26, 8, 0, tz="LMT", lat=27.915, lon=112.53, gender="male"))
    assert r["chart"] == "癸巳 甲子 丁酉 甲辰"


@pytest.mark.parametrize("year,deg,hk_date", [
    # https://www.hko.gov.hk/tc/gts/time/calendar/text/files/T2022c.txt
    (2022, 285, "2022-01-05"), (2022, 315, "2022-02-04"), (2022, 345, "2022-03-05"), (2022, 15, "2022-04-05"),
    (2022, 75, "2022-06-06"), (2022, 165, "2022-09-07"), (2022, 195, "2022-10-08"), (2022, 255, "2022-12-07"),
])
def test_jie_dates_vs_hko_2022(year, deg, hk_date):
    import swisseph as swe
    y, m, d = (int(x) for x in hk_date.split("-"))
    jd = bazi.find_sun_longitude(deg, swe.julday(y, m, d, 12.0) + 3, search_back=True)
    assert (bazi.jd_to_utc(jd) + timedelta(hours=8)).strftime("%Y-%m-%d") == hk_date


# Векторы вне России (южное полушарие, США, ±1 ч от цзе, 23:00–00:59). Ожидания получены НЕЗАВИСИМО:
# UT через zoneinfo; год/месяц/удача — lunar-python с пекинским эквивалентом (UT+8);
# день/час — lunar-python со «временем карты», где LMT = UT + долгота/15, EoT — по формуле Meeus (не Swiss Ephemeris).
WORLD = [
    # (вход, пол, год+месяц, {(solar_time, zi_hour): "день час"}, направление, (лет, мес, дн) старта)
    (BirthInput(2022, 2, 3, 15, 11, tz="America/New_York", lat=40.7128, lon=-74.006, gender="female"),
     "辛丑 辛丑", {k: "丁亥 戊申" for k in [("clock", "late"), ("clock", "early"), ("mean", "late"),
                                         ("mean", "early"), ("true", "late"), ("true", "early")]}, "forward", (0, 0, 3)),
    (BirthInput(2022, 2, 3, 16, 31, tz="America/New_York", lat=40.7128, lon=-74.006, gender="female"),
     "壬寅 壬寅", {k: "丁亥 戊申" for k in [("clock", "late"), ("clock", "early"), ("mean", "late"),
                                         ("mean", "early"), ("true", "late"), ("true", "early")]}, "backward", (0, 0, 3)),
    (BirthInput(1995, 11, 20, 23, 40, tz="Australia/Sydney", lat=-33.8688, lon=151.2093, gender="male"),
     "乙亥 丁亥", {("clock", "late"): "乙卯 戊子", ("clock", "early"): "丙辰 戊子", ("mean", "late"): "乙卯 丁亥",
                 ("mean", "early"): "乙卯 丁亥", ("true", "late"): "乙卯 丁亥", ("true", "early"): "乙卯 丁亥"},
     "backward", (4, 2, 15)),
    (BirthInput(1986, 6, 29, 0, 30, tz="America/Argentina/Buenos_Aires", lat=-34.6037, lon=-58.3816, gender="female"),
     "丙寅 甲午", {("clock", "late"): "甲辰 甲子", ("clock", "early"): "甲辰 甲子", ("mean", "late"): "癸卯 甲子",
                 ("mean", "early"): "甲辰 甲子", ("true", "late"): "癸卯 甲子", ("true", "early"): "甲辰 甲子"},
     "backward", (7, 8, 18)),
    (BirthInput(1977, 7, 4, 0, 50, tz="America/Los_Angeles", lat=34.0522, lon=-118.2437, gender="male"),
     "丁巳 丙午", {("clock", "late"): "壬戌 庚子", ("clock", "early"): "壬戌 庚子", ("mean", "late"): "辛酉 庚子",
                 ("mean", "early"): "壬戌 庚子", ("true", "late"): "辛酉 庚子", ("true", "early"): "壬戌 庚子"},
     "backward", (9, 6, 1)),
]


@pytest.mark.parametrize("b,ym,dh,direction,start", WORLD)
def test_world_vectors_independent(b, ym, dh, direction, start):
    for (mode, zi), exp in dh.items():
        r = calculate(b, solar_time=mode, zi_hour=zi)
        assert r["chart"] == f"{ym} {exp}", (mode, zi)
        lp = r["luck_pillars"]
        assert lp["direction"] == direction
        assert (lp["start"]["years"], lp["start"]["months"]) == start[:2]
        assert abs(lp["start"]["days"] - start[2]) <= 1


def test_no_time_jie_warning_only_on_local_birth_date():
    # 04.02.1984 — Личунь в 18:18 MSK в этот же день: предупреждение есть
    r = calculate(BirthInput(1984, 2, 4, place="Москва"))
    assert any("立春" in w and "неоднозначен" in w for w in r["warnings"])
    # 03.02.1984 — до Личуня больше суток по местной дате: предупреждения о цзе нет
    r = calculate(BirthInput(1984, 2, 3, place="Москва"))
    assert not any("立春" in w for w in r["warnings"])


def test_decade_anchor_table_from_doc():
    # таблица «индекс 01.01» из шага 4 базы знаний + правило +5/+6 за год
    anchors = {1900: 10, 1910: 2, 1920: 54, 1930: 47, 1940: 39, 1950: 32, 1960: 24, 1970: 17,
               1980: 9, 1990: 2, 2000: 54, 2010: 47, 2020: 39, 2030: 32, 2040: 24}
    for y, idx in anchors.items():
        assert day_index(date(y, 1, 1)) == idx
    for y in range(1900, 2045):
        dec = y - y % 10
        idx = anchors[dec]
        for yy in range(dec, y):
            idx += 6 if (yy % 4 == 0 and (yy % 100 != 0 or yy % 400 == 0)) else 5
        assert idx % 60 == day_index(date(y, 1, 1)), y


def test_meeus_low_precision_formula_from_doc():
    # Формула из шага 1а базы знаний: ошибка момента цзе ≤ 12 мин на 1850–2100 гг.
    import math
    import swisseph as swe

    def lam(jd):
        t = (jd - 2451545.0) / 36525
        l0 = 280.46646 + 36000.76983 * t + 0.0003032 * t * t
        m = math.radians(357.52911 + 35999.05029 * t - 0.0001537 * t * t)
        c = ((1.914602 - 0.004817 * t - 0.000014 * t * t) * math.sin(m)
             + (0.019993 - 0.000101 * t) * math.sin(2 * m) + 0.000289 * math.sin(3 * m))
        om = math.radians(125.04 - 1934.136 * t)
        return (l0 + c - 0.00569 - 0.00478 * math.sin(om)) % 360

    worst = 0.0
    for y in range(1850, 2101, 10):
        for k in range(12):
            deg = (315 + 30 * k) % 360
            ref = bazi.find_sun_longitude(deg, swe.julday(y, 2, 4, 0.0) + 30.4 * k + 15, search_back=True)
            jd = ref + 0.5
            for _ in range(4):
                jd += (((deg - lam(jd)) + 180) % 360 - 180) / 0.9856
            worst = max(worst, abs(jd - ref) * 1440)
    assert worst <= 12.5


# ---------------------------------------------------------------------------
# 8. Повторная проверка (приоритет 1): таблицы против классических текстов
# ---------------------------------------------------------------------------

def _br(s: str) -> list[int]:
    return [[b[0] for b in bazi.BRANCHES].index(ch) for ch in s]


def _st(s: str) -> list[int]:
    return [[x[0] for x in bazi.STEMS].index(ch) for ch in s]


def test_shensha_tables_vs_sanming_tonghui():
    # 《三命通会》卷三 «论驿马» (https://zh.wikisource.org/wiki/三命通會/卷三):
    # «寅午戌生人，马在申…申子辰人，马在寅…巳酉丑人，马在亥…亥卯未人，马在巳»
    for group, horse in (("寅午戌", "申"), ("申子辰", "寅"), ("巳酉丑", "亥"), ("亥卯未", "巳")):
        for b in _br(group):
            assert bazi.HORSE[bazi.TRINE_OF[b]] == _br(horse)[0]
    # 卷三 «总论诸神煞»: «亥卯未在子，巳酉丑在午，寅午戌在卯，申子辰在酉，为桃花煞»
    for group, peach in (("亥卯未", "子"), ("巳酉丑", "午"), ("寅午戌", "卯"), ("申子辰", "酉")):
        for b in _br(group):
            assert bazi.PEACH[bazi.TRINE_OF[b]] == _br(peach)[0]
    # 卷二 «论咸池»: «五行沐浴之地，名咸池» — 桃花 = 沐浴 Ян-ствола элемента тройки (水 壬, 火 丙, 金 庚, 木 甲)
    for group, stem in (("申子辰", "壬"), ("寅午戌", "丙"), ("巳酉丑", "庚"), ("亥卯未", "甲")):
        peach = bazi.PEACH[bazi.TRINE_OF[_br(group)[0]]]
        assert bazi.life_stage(_st(stem)[0], peach)["cn"] == "沐浴"
    # 卷二 «论将星华盖»: «以三合底处得库谓之华盖» — последняя ветвь тройки (库)
    for group in ("申子辰", "寅午戌", "巳酉丑", "亥卯未"):
        assert bazi.CANOPY[bazi.TRINE_OF[_br(group)[0]]] == _br(group)[2]
    # 卷三 «论天乙贵人»: «甲阳木、戊阳土、庚阳金，皆喜土位…所以牛羊为贵»; 乙己 «鼠猴为贵»;
    # 丙丁 «以酉亥阴气和而为贵»; 壬癸 «以巳卯阳气和而为贵»; «六辛…故以马虎为贵»
    expected = {"甲": "丑未", "戊": "丑未", "庚": "丑未", "乙": "子申", "己": "子申",
                "丙": "亥酉", "丁": "亥酉", "壬": "卯巳", "癸": "卯巳", "辛": "寅午"}
    for stem, brs in expected.items():
        assert set(bazi.NOBLEMAN[_st(stem)[0]]) == set(_br(brs))


def test_hidden_stems_vs_yuanhai_ziping_and_sanming():
    # 《渊海子平》 «又地支藏遁歌» (https://zh.wikisource.org/wiki/淵海子平): «子宫癸水在其中，丑癸辛金己土同；
    # 寅宫甲木兼丙戊，卯宫乙木独相逢。辰藏乙戊三分癸，巳中庚金丙戊丛；午宫丁火并己土，未宫乙己丁共宗。
    # 申位庚金壬水戊，酉宫辛金独丰隆；戌宫辛金及丁戊，亥藏壬甲是真踪。» — состав (без порядка)
    verse = {"子": "癸", "丑": "癸辛己", "寅": "甲丙戊", "卯": "乙", "辰": "乙戊癸", "巳": "庚丙戊",
             "午": "丁己", "未": "乙己丁", "申": "庚壬戊", "酉": "辛", "戌": "辛丁戊", "亥": "壬甲"}
    for br, stems in verse.items():
        assert {s for s, _r, _w in bazi.HIDDEN_STEMS[_br(br)[0]]} == set(_st(stems))
    # 《三命通会》卷二 «论人元司事» (https://zh.wikisource.org/wiki/三命通會/卷二):
    # «已中有戊土七日，庚金长生五日，丙火一十八日» — 本气 丙, 中气 (长生) 庚, 余气 戊
    roles = {s: r for s, r, _w in bazi.HIDDEN_STEMS[_br("巳")[0]]}
    assert roles == {_st("丙")[0]: "main", _st("庚")[0]: "middle", _st("戊")[0]: "residual"}
    # 卷二 «论天干阴阳生死»: «阳生阴死，阳死阴生»; «戊土生于寅，寅中有火» (火土同宫), 己 — в 酉
    assert bazi.life_stage(_st("戊")[0], _br("寅")[0])["cn"] == "长生"
    assert bazi.life_stage(_st("己")[0], _br("酉")[0])["cn"] == "长生"
    for yang, yin in ((0, 1), (2, 3), (4, 5), (6, 7), (8, 9)):   # 长生 Инь-ствола = 死 Ян-пары
        yin_birth = bazi.CHANG_SHENG_START[yin]
        assert bazi.life_stage(yang, yin_birth)["cn"] == "死"
