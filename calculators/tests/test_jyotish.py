"""Тесты модуля 07 — Джйотиш (calculators/jyotish.py).

Внешние векторы (URL — в комментариях у каждого блока):
* AstroSage, опубликованные карты знаменитостей (Lahiri, средний узел): Эйнштейн, Обама,
  Ганди, Стив Джобс, Индира Ганди — долготы, накшатры/пады, «Relation», баланс и даты махадаш.
* starmani.onrender.com — D9 (навамша) Эйнштейна.
* PVR Narasimha Rao, «Vedic Astrology: An Integrated Approach» (учебник, гл. 16) — примеры 50–55.
* Prokerala, ежедневная панчанга (Уджджайн, IST) — моменты смены титхи/накшатры/йоги/караны
  и время восхода для дат T1–T3.
* Определение аянамши Lahiri (Indian Calendar Reform Committee): 23°15′00.658″ на 21.03.1956 0h TT.
"""
from __future__ import annotations

import json
from datetime import date, datetime, timedelta

import pytest
import swisseph as swe

from calculators.common.time import BirthInput
from calculators.jyotish import (DASHA_ORDER, DASHA_YEARS, NAKSHATRAS, SIGN_LORDS, calculate,
                                 dasamsa_sign, dignity_bphs, nakshatra_of, navamsa_sign, vimshottari,
                                 years_to_ymd)

UJJAIN = (23.1765, 75.7885)


def dms(s: str) -> float:
    """'22-09-55' → градусы."""
    d, m, x = (float(t) for t in s.split("-"))
    return d + m / 60 + x / 3600


def arcmin(a: float, b: float) -> float:
    return abs((a - b + 180.0) % 360.0 - 180.0) * 60.0


# ---------------------------------------------------------------------------
# 1. Справочные таблицы и формулы
# ---------------------------------------------------------------------------

def test_tables_invariants():
    assert len(NAKSHATRAS) == 27
    assert sum(DASHA_YEARS.values()) == 120
    # управители накшатр циклически повторяют порядок Вимшоттари: Кету, Венера, Солнце, ...
    assert [n[2] for n in NAKSHATRAS] == DASHA_ORDER * 3
    # по 9 накшатр в каждой гане
    for g in ("deva", "manushya", "rakshasa"):
        assert sum(1 for n in NAKSHATRAS if n[5] == g) == 9


@pytest.mark.parametrize("lon,idx,pada", [
    (0.0, 1, 1), (3.3333, 1, 1), (3.3334, 1, 2), (13.3333, 1, 4), (13.33334, 2, 1),
    (226.6667, 18, 1), (359.9999, 27, 4), (360.0, 1, 1),
])
def test_nakshatra_boundaries(lon, idx, pada):
    n = nakshatra_of(lon)
    assert (n["index"], n["pada"]) == (idx, pada)


def test_navamsa_equals_bphs_rule():
    """Сквозная формула floor(lon/3°20′) mod 12 ≡ правилу BPHS
    (подвижные — от себя, фиксированные — от 9-го, двойственные — от 5-го)."""
    for s in range(12):
        start = {0: s, 1: (s + 8) % 12, 2: (s + 4) % 12}[s % 3]
        for k in range(9):
            lon = s * 30 + k * (30 / 9) + 0.5
            assert navamsa_sign(lon) == (start + k) % 12


def test_dasamsa_rule():
    # Овен (нечётный) 0–3° → Овен; Телец (чётный) 0–3° → Козерог (9-й от Тельца)
    assert dasamsa_sign(1.0) == 0
    assert dasamsa_sign(31.0) == 9
    assert dasamsa_sign(59.9) == (9 + 9) % 12   # последний дашамша Тельца → Весы
    # Близнецы 27–30° → 10-й от Близнецов = Рыбы
    assert dasamsa_sign(89.0) == 11


def test_dignity_degrees_bphs():
    # BPHS 3.51–54: Луна — 0–3° Тельца экзальтация, далее мулатрикона
    assert dignity_bphs("moon", 31.0) == "exalted"
    assert dignity_bphs("moon", 40.0) == "moolatrikona"
    # Меркурий: Дева 0–15 экз., 15–20 мулатрикона, 20–30 свой
    assert dignity_bphs("mercury", 155.0) == "exalted"
    assert dignity_bphs("mercury", 167.0) == "moolatrikona"
    assert dignity_bphs("mercury", 175.0) == "own"
    assert dignity_bphs("sun", 125.0) == "moolatrikona"
    assert dignity_bphs("sun", 145.0) == "own"
    assert dignity_bphs("saturn", 15.0) == "debilitated"
    assert dignity_bphs("jupiter", 245.0) == "moolatrikona"
    assert SIGN_LORDS[10] == "saturn"


def test_ymd_split():
    # PVR пример 50: 2.24875 г. = 2 г. 2 мес. 29 дн. (33 гхати)
    assert years_to_ymd(2.24875) == "2 г. 2 мес. 29 дн."


def test_lahiri_definition():
    """ICRC: аянамша Lahiri = 23°15′00.658″ на 21.03.1956 0h ET/TT (истинная, с нутацией).
    https://github.com/maniya81/swiss-ephemeris-mcp-server/pull/4 (разбор определения; SE выше на ~0.14″)"""
    swe.set_sid_mode(swe.SIDM_LAHIRI)
    val = swe.get_ayanamsa_ex(2435553.5, swe.FLG_SWIEPH)[1]
    assert abs(val - (23 + 15 / 60 + 0.658 / 3600)) * 3600 < 0.5


# ---------------------------------------------------------------------------
# 2. Эталонные персоны T1–T4 (регрессия + внешние сверки там, где есть)
# ---------------------------------------------------------------------------

T = {
    "T1": BirthInput(1990, 5, 15, 14, 30, place="Москва"),
    "T2": BirthInput(1984, 2, 4, 23, 30, place="Москва"),
    "T3": BirthInput(2004, 2, 29, 8, 15, place="Санкт-Петербург"),
    "T4": BirthInput(1879, 3, 14, 11, 30, tz="LMT", lat=48.4011, lon=9.9876),
}

# lagna(знак, градус), Луна (знак, накшатра, пада), первая даша, баланс (лет), панчанга
EXPECTED_T = {
    "T1": dict(lagna=(5, 21.652), moon=(10, "Uttara Ashadha", 2), dasha=("sun", 3.3010),
               tithi=21, nak="Uttara Ashadha", yoga="Shubha", karana="Gara", vara="Mangalavara"),
    "T2": dict(lagna=(6, 25.844), moon=(11, "Purva Bhadrapada", 1), dasha=("jupiter", 12.6999),
               tithi=3, nak="Purva Bhadrapada", yoga="Shiva", karana="Gara", vara="Shanivara"),
    "T3": dict(lagna=(11, 25.109), moon=(2, "Mrigashira", 2), dasha=("mars", 4.7111),
               tithi=9, nak="Mrigashira", yoga="Priti", karana="Balava", vara="Ravivara"),
    "T4": dict(lagna=(3, 19.473), moon=(8, "Jyeshtha", 2), dasha=("mercury", 9.7510),
               tithi=22, nak="Jyeshtha", yoga="Siddhi", karana="Bava", vara="Shukravara"),
}


@pytest.mark.parametrize("tid", list(T))
def test_reference_persons(tid):
    r = calculate(T[tid])
    e = EXPECTED_T[tid]
    assert r["lagna"]["sign"] == e["lagna"][0]
    assert abs(r["lagna"]["deg_in_sign"] - e["lagna"][1]) < 0.01
    m = r["grahas"]["moon"]
    assert (m["sign"], m["nakshatra"], m["pada"]) == e["moon"]
    assert r["dasha"]["first_lord"] == e["dasha"][0]
    assert abs(r["dasha"]["balance"]["years"] - e["dasha"][1]) < 0.001
    p = r["panchanga"]
    assert p["tithi"]["index"] == e["tithi"]
    assert p["nakshatra"]["name"] == e["nak"]
    assert p["yoga"]["name"] == e["yoga"]
    assert p["karana"]["name"] == e["karana"]
    assert p["vara"]["name"] == e["vara"]
    json.dumps(r, ensure_ascii=False)        # результат сериализуем


def test_t1_soviet_dst():
    """T1: летнее время СССР 1990 (UTC+4) → 10:30 UT."""
    r = calculate(T["T1"])
    assert r["inputs_used"]["utc"].startswith("1990-05-15T10:30")
    assert any("летнее время" in w for w in r["warnings"])


def test_t3_boundaries():
    """T3: Венера в 29°52′ Рыб (7′ до Овна) — варготтама; Меркурий сожжён."""
    g = calculate(T["T3"])["grahas"]
    assert g["venus"]["sign"] == 12 and g["venus"]["deg_in_sign"] > 29.8
    assert g["venus"]["vargottama"] and g["venus"]["dignity"] == "exalted"
    assert g["mercury"]["combust"]
    assert g["moon"]["dignity"] == "moolatrikona" and g["moon"]["relation"] == "exalted"


def test_t4_einstein_lmt():
    """T4 по данным Astro-Databank (11:30 LMT Ульм): Лагна 19°28′ Близнецов (Ардра-4), D9-лагна Рыбы.
    AstroSage/Starmani считают 11:30 как CET (UTC+1) — отсюда их Лагна 15°15′ и D9-лагна Водолей
    (см. test_astrosage_* и test_starmani_einstein_d9)."""
    r = calculate(T["T4"])
    assert r["inputs_used"]["offset_source"] == "LMT(longitude)"
    assert r["lagna"]["nakshatra"] == "Ardra" and r["lagna"]["pada"] == 4
    assert r["lagna"]["d9_sign_ru"] == "Рыбы"
    md = r["dasha"]["mahadashas"]
    assert md[0]["lord"] == "mercury" and md[1]["lord"] == "ketu"
    assert md[1]["start"].startswith("1888-12-1")
    # Меркурий в 10-м доме по знакам, но в 11-й бхаве по Шрипати
    assert r["grahas"]["mercury"]["house"] == 10 and r["grahas"]["mercury"]["bhava"] == 11


# ---------------------------------------------------------------------------
# 3. AstroSage: опубликованные карты (Lahiri, средний узел)
# ---------------------------------------------------------------------------

ASTROSAGE = {
    # https://astrosage.com/celebrity-Horoscope/albert-einstein-birth-chart.asp (11:30, TZ 1.0, 48N23 10E00)
    "einstein": dict(
        b=BirthInput(1879, 3, 14, 11, 30, tz="UTC+01:00", lat=48 + 23 / 60, lon=10.0),
        pos={"asc": (2, "15-14-52", "Ardra", 3), "sun": (11, "01-19-48", "Purva Bhadrapada", 4),
             "moon": (7, "22-09-55", "Jyeshtha", 2), "mars": (9, "04-44-48", "Uttara Ashadha", 3),
             "mercury": (11, "10-57-33", "Uttara Bhadrapada", 3), "jupiter": (10, "05-18-54", "Dhanishtha", 4),
             "venus": (11, "24-48-29", "Revati", 3), "saturn": (11, "12-01-15", "Uttara Bhadrapada", 3),
             "rahu": (9, "09-18-23", "Uttara Ashadha", 4)},
        rel={"sun": "friend", "moon": "debilitated", "mars": "exalted", "mercury": "debilitated",
             "jupiter": "neutral", "venus": "exalted", "saturn": "neutral"},
        combust={"mercury", "saturn"},
        balance=("mercury", "9 11 26"),
        ends=["1889-03-11", "1896-03-11", "1916-03-11", "1922-03-11", "1932-03-11", "1939-03-11",
              "1957-03-11", "1973-03-11", "1992-03-11"]),
    # https://astrosage.com/celebrity-Horoscope/barack-obama-birth-chart.asp (19:24, TZ −10, 21N18 157W51)
    "obama": dict(
        b=BirthInput(1961, 8, 4, 19, 24, tz="UTC-10:00", lat=21.3, lon=-(157 + 51 / 60)),
        pos={"asc": (9, "24-44-16", "Dhanishtha", 1), "sun": (3, "19-14-19", "Ashlesha", 1),
             "moon": (1, "10-02-15", "Rohini", 1), "mars": (4, "29-16-14", "Uttara Phalguni", 1),
             "mercury": (3, "09-01-47", "Pushya", 2), "jupiter": (9, "07-34-28", "Uttara Ashadha", 4),
             "venus": (2, "08-28-55", "Ardra", 1), "saturn": (9, "01-59-09", "Uttara Ashadha", 2),
             "rahu": (4, "04-34-19", "Magha", 2)},
        rel={"sun": "friend", "moon": "exalted", "mars": "friend", "mercury": "enemy",
             "jupiter": "debilitated", "venus": "friend", "saturn": "own"},
        combust={"mercury"},
        balance=("moon", "9 11 20"),
        ends=["1971-07-24", "1978-07-24", "1996-07-24", "2012-07-24", "2031-07-24", "2048-07-24",
              "2055-07-24", "2075-07-24", "2081-07-24"]),
    # https://astrosage.com/celebrity-Horoscope/mahatma-gandhi-birth-chart.asp (08:36:19, TZ 5.5, 21N40 69E40)
    # Секунды важны: без 19 с Лагна была бы на 3.9′ меньше (4 с времени ≈ 1′ Лагны); с ними — 0.4′.
    "gandhi": dict(
        b=BirthInput(1869, 10, 2, 8, 36, tz="UTC+05:30", lat=21 + 40 / 60, lon=69 + 40 / 60, second=19),
        pos={"asc": (6, "12-06-43", "Svati", 2), "sun": (5, "16-55-40", "Hasta", 3),
             "moon": (3, "28-16-51", "Ashlesha", 4), "mars": (6, "26-22-48", "Vishakha", 2),
             "mercury": (6, "11-45-36", "Svati", 2), "jupiter": (0, "28-09-47", "Krittika", 1),
             "venus": (6, "24-26-18", "Vishakha", 2), "saturn": (7, "20-21-25", "Jyeshtha", 2),
             "rahu": (3, "12-08-44", "Pushya", 3)},
        rel={"sun": "neutral", "moon": "own", "mars": "neutral", "mercury": "friend",
             "jupiter": "friend", "venus": "own", "saturn": "enemy"},
        combust=set(),
        balance=("mercury", "2 2 9"),
        ends=["1871-12-12", "1878-12-12", "1898-12-12", "1904-12-12", "1914-12-12", "1921-12-12",
              "1939-12-12", "1955-12-12", "1974-12-12"]),
    # https://astrosage.com/celebrity-Horoscope/steve-jobs-birth-chart.asp (19:15, TZ −8, 37N46 122W25)
    "jobs": dict(
        b=BirthInput(1955, 2, 24, 19, 15, tz="UTC-08:00", lat=37 + 46 / 60, lon=-(122 + 25 / 60)),
        pos={"asc": (4, "29-03-13", "Uttara Phalguni", 1), "sun": (10, "12-31-12", "Shatabhisha", 2),
             "moon": (11, "14-30-37", "Uttara Bhadrapada", 4), "mars": (0, "05-50-48", "Ashvini", 2),
             "mercury": (9, "21-07-45", "Shravana", 4), "jupiter": (2, "27-15-47", "Punarvasu", 3),
             "venus": (8, "27-56-41", "Uttara Ashadha", 1), "saturn": (6, "27-56-11", "Vishakha", 3),
             "rahu": (8, "09-16-02", "Mula", 3)},
        rel={"sun": "enemy", "moon": "neutral", "mars": "own", "mercury": "neutral",
             "jupiter": "enemy", "venus": "neutral", "saturn": "exalted"},
        combust=set(),
        balance=("saturn", "3 0 27"),
        ends=["1958-03-21", "1975-03-21", "1982-03-21", "2002-03-21", "2008-03-21", "2018-03-21",
              "2025-03-21", "2043-03-21", "2059-03-21"]),
    # https://astrosage.com/celebrity-Horoscope/indira-gandhi-birth-chart.asp (23:11, TZ 5.5, 25N57 81E50)
    "indira": dict(
        b=BirthInput(1917, 11, 19, 23, 11, tz="UTC+05:30", lat=25 + 57 / 60, lon=81 + 50 / 60),
        pos={"asc": (3, "27-29-48", "Ashlesha", 4), "sun": (7, "04-07-59", "Anuradha", 1),
             "moon": (9, "05-35-20", "Uttara Ashadha", 3), "mars": (4, "16-23-06", "Purva Phalguni", 1),
             "mercury": (7, "13-14-36", "Anuradha", 3), "jupiter": (1, "14-58-03", "Rohini", 2),
             "venus": (8, "21-00-39", "Purva Ashadha", 3), "saturn": (3, "21-53-28", "Ashlesha", 2),
             "rahu": (8, "10-33-52", "Mula", 4)},
        rel={"sun": "friend", "moon": "neutral", "mars": "friend", "mercury": "neutral",
             "jupiter": "enemy", "venus": "neutral", "saturn": "enemy"},
        # ⚠ AstroSage НЕ ставит «C» Меркурию (9.1° от Солнца, прямой) — при орбе 14° он сожжён;
        # правило AstroSage для сожжения не опубликовано, поэтому для этой карты флаг не сверяем.
        combust=None,
        balance=("sun", "1 11 25"),
        ends=["1919-11-14", "1929-11-14", "1936-11-14", "1954-11-14", "1970-11-14", "1989-11-14",
              "2006-11-14", "2013-11-14", "2033-11-14"]),
}

# Допуски по долготам (угл. мин): AstroSage использует свою эфемериду; расхождения до ~1′,
# у медленных планет XIX–начала XX в. — до 6′ (Сатурн Индиры).
POS_TOL = {"asc": 1.0, "sun": 1.0, "moon": 1.2, "mars": 1.2, "mercury": 1.2, "jupiter": 2.2,
           "venus": 1.0, "saturn": 6.5, "rahu": 0.3}


@pytest.mark.parametrize("name", list(ASTROSAGE))
def test_astrosage_positions(name):
    v = ASTROSAGE[name]
    r = calculate(v["b"])
    for k, (sign, deg, nak, pada) in v["pos"].items():
        rec = r["lagna"] if k == "asc" else r["grahas"][k]
        exp_lon = sign * 30 + dms(deg)
        assert arcmin(rec["lon"], exp_lon) < POS_TOL[k], (name, k, rec["lon"], exp_lon)
        assert rec["sign"] == sign + 1, (name, k)
        assert (rec["nakshatra"], rec["pada"]) == (nak, pada), (name, k)
    # колонка Relation и пометка C (сожжение)
    for g, rel in v["rel"].items():
        assert r["grahas"][g]["relation"] == rel, (name, g)
    if v["combust"] is not None:
        for g in ("moon", "mars", "mercury", "jupiter", "venus", "saturn"):
            assert r["grahas"][g]["combust"] == (g in v["combust"]), (name, g)


@pytest.mark.parametrize("name", list(ASTROSAGE))
def test_astrosage_mean_node(name):
    """Раху AstroSage совпадает со СРЕДНИМ узлом (до 0.3′), истинный узел отличается на ≥ 0.5°."""
    v = ASTROSAGE[name]
    exp = v["pos"]["rahu"][0] * 30 + dms(v["pos"]["rahu"][1])
    mean = calculate(v["b"], node="mean")["grahas"]["rahu"]["lon"]
    true = calculate(v["b"], node="true")["grahas"]["rahu"]["lon"]
    assert arcmin(mean, exp) < 0.3
    assert arcmin(true, exp) > 5


@pytest.mark.parametrize("name", list(ASTROSAGE))
def test_astrosage_dasha(name):
    v = ASTROSAGE[name]
    r = calculate(v["b"], dasha_levels=1)
    d = r["dasha"]
    lord, ymd = v["balance"]
    assert d["first_lord"] == lord
    y, m, dd = (int(t) for t in ymd.split())
    exp_years = y + m / 12 + dd / 360
    # Луна у AstroSage отличается до ~1′: 1′ = P/800 лет (для Меркурия ≈ 7.8 сут)
    assert abs(d["balance"]["years"] - exp_years) < 0.03
    tol = 7 if name == "gandhi" else 3        # у Ганди наша Луна на 0.8′ меньше → даты +5…6 сут
    for md, e in zip(d["mahadashas"], v["ends"]):
        diff = (date.fromisoformat(md["end"][:10]) - date.fromisoformat(e)).days
        assert abs(diff) <= tol, (name, md["lord"], md["end"], e)


def test_astrosage_balance_from_their_moon():
    """Тот же алгоритм на долготе Луны, напечатанной AstroSage, даёт их баланс до дня."""
    # Эйнштейн: Луна 22-09-55 Скорпиона → Меркурий 9 г. 11 мес. 26 дн.
    d = vimshottari(7 * 30 + dms("22-09-55"), 2407422.9375, 1.0)
    assert d["balance"]["ymd"] == "9 г. 11 мес. 26 дн."
    # Ганди: Луна 28-16-51 Рака → Меркурий 2 г. 2 мес. 9 дн.
    d = vimshottari(3 * 30 + dms("28-16-51"), 2404342.6, 5.5)
    assert d["balance"]["ymd"] == "2 г. 2 мес. 9 дн."


def test_starmani_einstein_d9():
    """https://starmani.onrender.com/celebrity-charts/8f9855e0a2a342d9b428e73969c8dc23
    D9: Ма, Ве — Водолей; Ра — Рыбы; Су — Рак; Ке — Дева; Ме, Са — Весы; Юп — Скорпион; Лу — Козерог;
    D9-лагна Водолей (их время = CET)."""
    exp = {"mars": 11, "venus": 11, "rahu": 12, "sun": 4, "ketu": 6, "mercury": 7, "saturn": 7,
           "jupiter": 8, "moon": 10}
    for b in (ASTROSAGE["einstein"]["b"], T["T4"]):           # от времени не зависит
        r = calculate(b)
        for g, s in exp.items():
            assert r["d9"][g]["sign"] == s, g
    assert calculate(ASTROSAGE["einstein"]["b"])["d9"]["lagna"]["sign"] == 11


# ---------------------------------------------------------------------------
# 4. Учебник PVR Narasimha Rao (гл. 16, Вимшоттари) — https://www.vedicastrologer.org/articles/vedic_astro_textbook.pdf
# ---------------------------------------------------------------------------

def test_pvr_example_50_51():
    """Пример 50: 2000-04-28 5:50, пояс 4 ч к западу; Луна 2°23′ Водолея (Дхаништха-3);
    остаток Марса 7×0.32125 = 2.24875 г. = 2 г. 2 мес. 29 дн. 33 гхати; конец Марса ≈ 19:00 15.07.2002
    (книга использует савана-год 360 сут). Пример 51: от 4/5/8-й звезды — Сатурн 6.10375,
    Меркурий 5.46125, Солнце 1.9275 г."""
    b = BirthInput(2000, 4, 28, 5, 50, tz="UTC-04:00")
    r = calculate(b, dasha_year="savana")
    m = r["grahas"]["moon"]
    assert m["sign"] == 11 and abs(m["deg_in_sign"] - (2 + 23 / 60)) < 1 / 60
    assert (m["nakshatra"], m["pada"]) == ("Dhanishtha", 3)
    assert r["dasha"]["first_lord"] == "mars"
    assert r["dasha"]["balance"]["ends"].startswith("2002-07-15")
    # точная арифметика книги — на её округлённой Луне 2°23′
    moon = 300 + 2 + 23 / 60
    for star, lord, yrs in ((1, "mars", 2.24875), (4, "saturn", 6.10375), (5, "mercury", 5.46125),
                            (8, "sun", 1.9275)):
        d = vimshottari(moon, r["inputs_used"]["jd_ut"], -4.0, year="savana", start_star=star, levels=1)
        assert d["first_lord"] == lord
        assert abs(d["balance"]["years"] - yrs) < 1e-6


def test_pvr_antardasha_lengths():
    """§16.3: в даше Венеры (20 л.) антардаша Венеры 3 г. 4 мес., Солнца 1 г., Луны 1 г. 8 мес., Марса 1 г. 2 мес."""
    d = vimshottari(300 + 2 + 23 / 60, 2451662.9, -4.0, year="savana", levels=2)
    venus = next(md for md in d["mahadashas"] if md["lord"] == "venus")
    yrs = {ad["lord"]: ad["years"] for ad in venus["antardashas"]}
    assert [ad["lord"] for ad in venus["antardashas"]][:4] == ["venus", "sun", "moon", "mars"]
    assert abs(yrs["venus"] - (3 + 4 / 12)) < 1e-6 and abs(yrs["sun"] - 1) < 1e-6
    assert abs(yrs["moon"] - (1 + 8 / 12)) < 1e-6 and abs(yrs["mars"] - (1 + 2 / 12)) < 1e-6


@pytest.mark.parametrize("dt,lat,lon,lord,ymd", [
    # Пример 53 / карта 18 (баланс Солнца «около 4 лет 9 мес.»; точное значение — тест PyJHora pvr_tests.py)
    ((1972, 6, 1, 4, 16), 16.25, 81.2, "sun", "4 г. 8 мес. 27 дн."),
    # Пример 55 / карта 20 (PyJHora: (4,7,3))
    ((1954, 11, 12, 7, 52), 12.5, 78 + 50 / 60, "moon", "4 г. 7 мес. 3 дн."),
])
def test_pvr_balances(dt, lat, lon, lord, ymd):
    # https://raw.githubusercontent.com/naturalstupid/PyJHora/main/src/jhora/tests/pvr_tests.py
    r = calculate(BirthInput(*dt, tz="UTC+05:30", lat=lat, lon=lon), dasha_year="savana")
    assert r["dasha"]["first_lord"] == lord
    assert r["dasha"]["balance"]["ymd"] == ymd


def test_pvr_example_52_53_55_dates():
    # Пр. 52 (Санджай Рат, 1963-08-07 21:14 IST, Самбалпур): «осталось несколько дней Раху»,
    # «даша Меркурия идёт с 1998 г.»
    r = calculate(BirthInput(1963, 8, 7, 21, 14, tz="UTC+05:30", lat=21.45, lon=83 + 58 / 60),
                  dasha_year="savana", dasha_levels=1)
    assert r["dasha"]["first_lord"] == "rahu" and r["dasha"]["balance"]["years"] < 0.05
    merc = next(md for md in r["dasha"]["mahadashas"] if md["lord"] == "mercury")
    assert merc["start"].startswith("1998")
    # Пр. 53: «Раху-даша началась в конце 1993 г.»
    r = calculate(BirthInput(1972, 6, 1, 4, 16, tz="UTC+05:30", lat=16.25, lon=81.2),
                  dasha_year="savana", dasha_levels=1)
    rahu = next(md for md in r["dasha"]["mahadashas"] if md["lord"] == "rahu")
    assert rahu["start"][:7] >= "1993-09" and rahu["start"][:4] == "1993"
    # Пр. 55: конец 1995 — Юпитер/Луна; от утпанна-звезды Венера-даша «февраль 1987 — октябрь 2006»
    b = BirthInput(1954, 11, 12, 7, 52, tz="UTC+05:30", lat=12.5, lon=78 + 50 / 60)
    cur = calculate(b, dasha_year="savana", on_date="1995-12-15")["dasha"]["current"]
    assert (cur["mahadasha"], cur["antardasha"]) == ("jupiter", "moon")
    ven = next(md for md in calculate(b, dasha_year="savana", dasha_start_star=5, dasha_levels=1)
               ["dasha"]["mahadashas"] if md["lord"] == "venus")
    assert ven["start"][:7] == "1987-02" and ven["end"][:7] == "2006-10"


# ---------------------------------------------------------------------------
# 5. Панчанга: Prokerala (Уджджайн, IST) — смены элементов ±2 мин
# ---------------------------------------------------------------------------

def _pan(dt: datetime) -> dict:
    r = calculate(BirthInput(dt.year, dt.month, dt.day, dt.hour, dt.minute, tz="UTC+05:30",
                             lat=UJJAIN[0], lon=UJJAIN[1]), dasha_levels=1)
    return r["panchanga"]


PROKERALA_TRANSITIONS = [
    # https://www.prokerala.com/astrology/panchang/1990-may-15.html
    ("1990-05-15 11:39", "tithi", 20, 21),
    ("1990-05-16 06:10", "nakshatra", "Uttara Ashadha", "Shravana"),
    ("1990-05-15 22:05", "yoga", "Shubha", "Shukla"),
    ("1990-05-16 00:17", "karana", "Gara", "Vanija"),
    ("1990-05-16 12:47", "tithi", 21, 22),
    # https://www.prokerala.com/astrology/panchang/1984-february-04.html
    ("1984-02-04 10:08", "tithi", 2, 3),
    ("1984-02-04 20:26", "nakshatra", "Shatabhisha", "Purva Bhadrapada"),
    ("1984-02-05 00:08", "yoga", "Parigha", "Shiva"),
    ("1984-02-04 23:25", "karana", "Taitila", "Gara"),
    ("1984-02-05 12:42", "tithi", 3, 4),
    # https://www.prokerala.com/astrology/panchang/2004-february-29.html
    ("2004-02-29 10:00", "yoga", "Vishkambha", "Priti"),
    ("2004-02-29 11:31", "karana", "Balava", "Kaulava"),
    ("2004-03-01 00:46", "tithi", 9, 10),
    ("2004-03-01 04:52", "nakshatra", "Mrigashira", "Ardra"),
    ("2004-03-01 10:47", "yoga", "Priti", "Ayushman"),
]


@pytest.mark.parametrize("when,elem,before,after", PROKERALA_TRANSITIONS)
def test_prokerala_transitions(when, elem, before, after):
    t = datetime.fromisoformat(when)
    key = "index" if elem == "tithi" else "name"
    assert _pan(t - timedelta(minutes=2))[elem][key] == before
    assert _pan(t + timedelta(minutes=2))[elem][key] == after


@pytest.mark.parametrize("d,exp", [((1990, 5, 15), "05:49"), ((1984, 2, 4), "07:09"), ((2004, 2, 29), "06:53")])
def test_prokerala_sunrise_hindu(d, exp):
    """Prokerala печатает восход центра диска без рефракции (наш 'hindu') — совпадение до 1 мин."""
    p = _pan(datetime(*d, 12, 0))
    ours = datetime.strptime(p["vara"]["sunrise_local"][11:], "%H:%M")
    assert abs((ours - datetime.strptime(exp, "%H:%M")).total_seconds()) <= 60


def test_vara_before_sunrise():
    """Вара меняется на восходе, а не в полночь.
    Prokerala: панчанга «29.02.2004 (воскресенье)» продолжается до восхода 01.03 —
    в 00:44 IST 01.03 гражданский понедельник, но вара — Равивара (воскресенье)."""
    p = _pan(datetime(2004, 3, 1, 0, 44))
    assert p["vara"]["name"] == "Ravivara" and p["vara"]["differs_from_civil"]
    # Санкт-Петербург, 29.02.2004 07:30 MSK — до восхода (~07:56–08:06 MSK): вара — суббота.
    # Восход: https://api.sunrise-sunset.org/json?lat=59.9343&lng=30.3351&date=2004-02-29 → 04:56 UT
    r = calculate(BirthInput(2004, 2, 29, 7, 30, place="Санкт-Петербург"))
    assert r["panchanga"]["vara"]["name"] == "Shanivara"
    assert r["panchanga"]["vara"]["civil_weekday_ru"] == "воскресенье"


# ---------------------------------------------------------------------------
# 6. Инварианты даши и опции
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("year", ["gregorian", "julian", "sidereal", "savana", "true_solar"])
def test_dasha_invariants(year):
    r = calculate(T["T2"], dasha_year=year, dasha_levels=3)
    mds = r["dasha"]["mahadashas"]
    assert [m["lord"] for m in mds] == DASHA_ORDER[DASHA_ORDER.index("jupiter"):] + DASHA_ORDER[:DASHA_ORDER.index("jupiter")]
    for a, b in zip(mds, mds[1:]):
        assert a["end"] == b["start"]
    for m in mds:
        ads = m["antardashas"]
        assert ads[0]["lord"] == m["lord"] and ads[0]["start"] == m["start"] and ads[-1]["end"] == m["end"]
        assert abs(sum(ad["years"] for ad in ads) - m["years"]) < 1e-5
        for ad in ads:
            assert ad["pratyantardashas"][0]["lord"] == ad["lord"]
            assert ad["pratyantardashas"][-1]["end"] == ad["end"]
    # баланс (в годах) не зависит от длины года
    assert abs(r["dasha"]["balance"]["years"] - 12.699872) < 1e-5


def test_year_length_effect():
    """Савана-год (360 сут) сокращает 120 лет на ~1.7 года; true_solar ≈ sidereal: на целых годах
    совпадают, на дробных расходятся до ~3–4 сут из-за неравномерного движения Солнца."""
    end = {y: calculate(T["T1"], dasha_year=y, dasha_levels=1)["dasha"]["mahadashas"][-1]["end_jd_ut"]
           for y in ("gregorian", "julian", "sidereal", "savana", "true_solar")}
    assert 600 < end["gregorian"] - end["savana"] < 640
    assert 0 < end["julian"] - end["gregorian"] < 1.0
    assert abs(end["true_solar"] - end["sidereal"]) < 4.0


def test_ayanamsa_variants():
    """Raman меньше Lahiri на ~1°26′, KP (старая) — на ~5.8′; знаки/накшатры могут сдвигаться."""
    base = calculate(T["T4"])
    a = base["ayanamsa"]["comparison"]
    assert abs((a["lahiri"]["mean"] - a["raman"]["mean"]) * 60 - 86.8) < 0.5
    assert abs((a["lahiri"]["mean"] - a["krishnamurti"]["mean"]) * 60 - 5.8) < 0.2
    raman = calculate(T["T4"], ayanamsa="raman")
    d = raman["grahas"]["moon"]["lon"] - base["grahas"]["moon"]["lon"]
    assert abs(d - (a["lahiri"]["true"] - a["raman"]["true"])) < 1e-6
    assert base["ayanamsa"]["true"] == pytest.approx(22.174241, abs=1e-5)


def test_unknown_time():
    r = calculate(BirthInput(1990, 5, 15, place="Москва"))
    assert r["lagna"] is None and r["houses_reference"].startswith("moon")
    assert r["moon_range_for_day"]["00:00"]["nakshatra"] == "Purva Ashadha"
    assert r["moon_range_for_day"]["23:59"]["nakshatra"] == "Uttara Ashadha"
    assert any("неизвестно" in w for w in r["warnings"])
    json.dumps(r, ensure_ascii=False)


def test_no_place_only_tz():
    r = calculate(BirthInput(1990, 5, 15, 14, 30, tz="Europe/Moscow"))
    assert r["lagna"] is None and r["bhava_chalit"] is None
    assert r["grahas"]["moon"]["nakshatra"] == "Uttara Ashadha"


def test_layouts():
    r = calculate(T["T4"])
    grid = r["layout"]["south_indian_grid"]
    assert grid[0][0].startswith("Рыбы") and "Су" in grid[0][0]
    assert "Лг" in grid[0][3]                     # Лагна — Близнецы
    north = r["layout"]["north_indian_houses"]
    assert north[0]["sign_number"] == 3 and "Лг" in north[0]["contents"]
    assert north[9]["sign_number"] == 12          # 10-й дом — Рыбы


def test_current_dasha_on_date():
    r = calculate(T["T1"], on_date="2026-10-14")
    cur = r["dasha"]["current"]
    assert cur["mahadasha"] == "rahu"
    assert cur["antardasha"] == "moon"


# ---------------------------------------------------------------------------
# 7. Независимая перепроверка (верификация, волна 2)
# ---------------------------------------------------------------------------

def test_independent_swisseph_t1_t4():
    """T1 и T4 пересчитаны напрямую через pyswisseph (без обёрток common/ephemeris):
    тропическая видимая долгота − истинная аянамша Lahiri, Лагна по формуле §3.4 из GAST."""
    import math
    for tid, ut_h, (y, mo, d), lat, lon in (
            ("T1", 10.5, (1990, 5, 15), 55.7558, 37.6173),
            ("T4", 11.5 - 9.9876 / 15, (1879, 3, 14), 48.4011, 9.9876)):
        r = calculate(T[tid])
        jd = swe.julday(y, mo, d, ut_h, swe.GREG_CAL)
        swe.set_sid_mode(swe.SIDM_LAHIRI)
        a_true = swe.get_ayanamsa_ex_ut(jd, swe.FLG_SWIEPH)[1]
        for g, code in (("sun", swe.SUN), ("moon", swe.MOON), ("mars", swe.MARS), ("mercury", swe.MERCURY),
                        ("jupiter", swe.JUPITER), ("venus", swe.VENUS), ("saturn", swe.SATURN),
                        ("rahu", swe.MEAN_NODE)):
            lam = (swe.calc_ut(jd, code, swe.FLG_SWIEPH)[0][0] - a_true) % 360
            assert arcmin(r["grahas"][g]["lon"], lam) < 0.01, (tid, g)
        eps = swe.calc_ut(jd, swe.ECL_NUT, 0)[0][0]
        ramc = math.radians((swe.sidtime(jd) * 15 + lon) % 360)
        e, f = math.radians(eps), math.radians(lat)
        asc = math.degrees(math.atan2(math.cos(ramc), -(math.sin(e) * math.tan(f) + math.cos(e) * math.sin(ramc))))
        assert arcmin(r["lagna"]["lon"], (asc - a_true) % 360) < 0.01, tid


def test_natural_friendship_derived_from_bphs_rule():
    """BPHS 3.55 (https://yourastroguide.wordpress.com/2012/09/01/brihat-parashara-hora-sashtra-chapter-3/):
    друзья — управители 2, 4, 5, 8, 9, 12-го от мулатриконы и знака экзальтации; враги — управители
    остальных знаков; посчитан и тем и другим → нейтрал. Вывод из правила = таблица NATURAL_FRIENDS."""
    from calculators.jyotish import EXALTATION, MOOLATRIKONA, NATURAL_FRIENDS
    seven = list(NATURAL_FRIENDS)
    for p in seven:
        m = MOOLATRIKONA[p][0]
        fr = {SIGN_LORDS[(m + h - 1) % 12] for h in (2, 4, 5, 8, 9, 12)} | {SIGN_LORDS[EXALTATION[p][0]]}
        en = {SIGN_LORDS[(m + h - 1) % 12] for h in (1, 3, 6, 7, 10, 11)}
        fr.discard(p)
        en.discard(p)
        friends, neutral, enemies = NATURAL_FRIENDS[p]
        assert set(friends) == {x for x in fr - en if x in seven}, p
        assert set(neutral) == {x for x in fr & en if x in seven}, p
        assert set(enemies) == {x for x in en - fr if x in seven}, p


def test_pvr_varga_examples():
    """PVR, гл. 6, пример 16 (D9: Меркурий 11° Близнецов → Козерог; Юпитер 19° Скорпиона → Стрелец;
    правило «огненные от Овна, земные от Козерога, воздушные от Весов, водные от Рака») и
    пример 17 (D10: Меркурий 10° Близнецов → Дева; Юпитер 19° Скорпиона → Козерог)."""
    assert navamsa_sign(60 + 11) == 9 and navamsa_sign(210 + 19) == 8
    assert dasamsa_sign(60 + 10) == 5 and dasamsa_sign(210 + 19) == 9
    for s in range(12):      # стихийное правило ≡ правилу подвижные/фиксированные/двойственные
        start = (0, 9, 6, 3)[s % 4]
        assert navamsa_sign(30 * s + 0.1) == start


def test_pada_to_navamsa():
    """Пада p накшатры n (обе с 1) → знак D9 = ((n − 1)·4 + p − 1) mod 12 + 1 (108 пад = 9 кругов зодиака)."""
    for n in range(1, 28):
        for p in range(1, 5):
            lon = (n - 1) * 40 / 3 + (p - 1) * 10 / 3 + 0.01
            assert nakshatra_of(lon)["pada"] == p
            assert navamsa_sign(lon) + 1 == ((n - 1) * 4 + p - 1) % 12 + 1


def test_pyjhora_example_51_balances():
    """PyJHora pvr_tests.py, Example 50/51 (наша Луна 2°23′15″, а не округлённая 2°23′ книги):
    кшема Сатурн (6,1,5), утпанна Меркурий (5,5,14), адхана Солнце (1,11,3).
    https://raw.githubusercontent.com/naturalstupid/PyJHora/main/src/jhora/tests/pvr_tests.py"""
    b = BirthInput(2000, 4, 28, 5, 50, tz="UTC-04:00")
    for star, lord, ymd in ((4, "saturn", "6 г. 1 мес. 5 дн."), (5, "mercury", "5 г. 5 мес. 14 дн."),
                            (8, "sun", "1 г. 11 мес. 3 дн.")):
        d = calculate(b, dasha_year="savana", dasha_levels=1, dasha_start_star=star)["dasha"]
        assert (d["first_lord"], d["balance"]["ymd"]) == (lord, ymd)


def test_pvr_example_50_book_moon_date():
    """Книга: «about 7 pm on 2002 July 15». На округлённой Луне книги (2°23′) 2.24875 савана-года =
    809.55 сут дают 16.07.2002 19:02 — время совпадает, дата на 1 сут позже (⚠ вероятно, арифметика книги).
    На нашей Луне 2°23′15″ — 15.07.2002 23:37 (см. test_pvr_example_50_51)."""
    from calculators.common.time import normalize
    jd = normalize(BirthInput(2000, 4, 28, 5, 50, tz="UTC-04:00")).jd_ut
    d = vimshottari(300 + 2 + 23 / 60, jd, -4.0, year="savana", levels=1)
    assert d["balance"]["ends"] == "2002-07-16 19:02"


@pytest.mark.parametrize("mode,diff_arcmin", [
    ("true_citra", -0.65), ("krishnamurti_vp291", -4.6), ("yukteshwar", -82.7), ("krishnamurti", -5.8)])
def test_extra_ayanamsas(mode, diff_arcmin):
    """Аянамши, добавленные в common/ephemeris, работают в калькуляторе (раньше — KeyError в подписи).
    Разность с Lahiri для T1 (Swiss Ephemeris 2.10)."""
    base = calculate(T["T1"], dasha_levels=1)
    r = calculate(T["T1"], ayanamsa=mode, dasha_levels=1)
    assert r["ayanamsa"]["name"] == mode and r["ayanamsa"]["label"]
    assert abs((r["ayanamsa"]["true"] - base["ayanamsa"]["true"]) * 60 - diff_arcmin) < 0.1
    d = r["grahas"]["moon"]["lon"] - base["grahas"]["moon"]["lon"]
    assert abs(d - (base["ayanamsa"]["true"] - r["ayanamsa"]["true"])) < 1e-6
    with pytest.raises(ValueError):
        calculate(T["T1"], ayanamsa="no_such_ayanamsa")


def test_seconds_and_julian_calendar_inputs():
    """BirthInput.second попадает в расчёт; дата по старому стилю переводится в григорианскую."""
    r = calculate(BirthInput(1869, 10, 2, 8, 36, tz="UTC+05:30", lat=21 + 40 / 60, lon=69 + 40 / 60, second=19),
                  dasha_levels=1)
    assert r["inputs_used"]["time"] == "08:36:19" and r["inputs_used"]["utc"].startswith("1869-10-02T03:06:19")
    # 02.10.1869 н. ст. = 20.09.1869 ст. ст. (разница 12 сут в XIX в.)
    j = calculate(BirthInput(1869, 9, 20, 8, 36, tz="UTC+05:30", lat=21 + 40 / 60, lon=69 + 40 / 60, second=19,
                             calendar="julian"), dasha_levels=1)
    assert j["inputs_used"]["date"] == "1869-10-02" and j["inputs_used"]["date_julian_input"] == "1869-09-20"
    assert j["grahas"]["moon"]["lon"] == r["grahas"]["moon"]["lon"]


def test_einstein_place_ulm_is_lmt():
    """place='Ульм' (tz Europe/Berlin): до 01.04.1893 tzdb даёт LMT, common/time подставляет LMT по долготе
    Ульма → тот же результат, что tz='LMT'. Astro-Databank/Halloran: 11:30, «Time Zone −00:40 (LT)», BC/AA
    (https://www.halloran.com/Albert_Einstein_Ranking.pdf)."""
    a = calculate(BirthInput(1879, 3, 14, 11, 30, place="Ульм"), dasha_levels=1)
    b = calculate(T["T4"], dasha_levels=1)
    assert a["inputs_used"]["offset_source"] == "LMT(longitude)"
    assert a["lagna"]["lon"] == b["lagna"]["lon"]
    # координаты ADB (48N24, 10E00) меняют Лагну лишь на 3″
    c = calculate(BirthInput(1879, 3, 14, 11, 30, tz="UTC+00:40", lat=48.4, lon=10.0), dasha_levels=1)
    assert arcmin(c["lagna"]["lon"], b["lagna"]["lon"]) < 0.1
