"""Тесты модуля 18 — западная прогностика (calculators/forecast_western.py).

Внешние векторы и источники:
* astro.com, FAQ «Overview chart types» (вторичные прогрессии, ключ Наибода 0.98564733°, способы углов):
  https://www.astro.com/cgi/xa.cgi/faq/fq_fh_owtype_e.htm
* astro.com, FAQ «Forecast Horoscopes» (транзитный орбис 1° у Р. Хэнда):
  https://www.astro.com/cgi/xa.cgi/faq/fq_sh_fore_e.htm
* AstroWiki (astro.com), «Naibodic Arc», «Secondary Progression», «Solar Arc», «Solar Return Chart»:
  https://www.astro.com/wiki/astrowiki-en/index.php?title=Naibodic_Arc&action=raw (и т. п.)
* Wikipedia, «Astrological progression» — пример 02.04.1982 → прогрессии на 2007 г. = 27.04.1982:
  https://en.wikipedia.org/wiki/Astrological_progression
* F. Boele, «The Progressed Lunation Cycle» (The Mountain Astrologer 2006, astro.com) — даты событий
  и фазы прогрессивной лунации с данными рождения: https://www.astro.com/astrology/in_progmoon_e.htm
* C. Brennan, «Introduction to Hellenistic Astrology (2) — Annual Profections…» (TMA, astro.com) —
  профекции Ф. Ф. Копполы: https://www.astro.com/astrology/tma_article190314_e.htm ;
  данные рождения Копполы (AA): https://www.astrotheme.com/astrology/Francis_Ford_Coppola
* JPL Horizons (DE441), видимая геоцентрическая эклиптическая долгота даты (ObsEcLon) — независимая
  эфемерида для моментов соляров, точных транзитов и стоянок: https://ssd.jpl.nasa.gov/api/horizons.api
"""
from __future__ import annotations

import json
import math
from datetime import datetime, timezone

import pytest
import swisseph as swe

from calculators.common import ephemeris as eph
from calculators.common.time import BirthInput, julian_day_ut
from calculators.forecast_western import NAIBOD, calculate, crossings, stations
from calculators.western import ASPECTS

ON = "2026-10-14"
Y = 365.24219


def T1() -> BirthInput:
    return BirthInput(1990, 5, 15, 14, 30, place="Москва")


def T2() -> BirthInput:
    return BirthInput(1984, 2, 4, 23, 30, place="Москва")


def T3() -> BirthInput:
    return BirthInput(2004, 2, 29, 8, 15, place="Санкт-Петербург")


def T4() -> BirthInput:
    return BirthInput(1879, 3, 14, 11, 30, tz="LMT", lat=48.4011, lon=9.9876)


def sd(a: float, b: float) -> float:
    d = (b - a) % 360.0
    return d - 360.0 if d > 180.0 else d


def jd_of(iso: str) -> float:
    return julian_day_ut(datetime.fromisoformat(iso).astimezone(timezone.utc))


def lon(body: int, jd: float) -> float:
    return swe.calc_ut(jd, body, swe.FLG_SWIEPH | swe.FLG_SPEED)[0][0]


def speed(body: int, jd: float) -> float:
    return swe.calc_ut(jd, body, swe.FLG_SWIEPH | swe.FLG_SPEED)[0][3]


CODES = {**eph.PLANETS}


@pytest.fixture(scope="module")
def r1():
    return calculate(T1(), on_date=ON)


@pytest.fixture(scope="module")
def r2():
    return calculate(T2(), on_date=ON)


@pytest.fixture(scope="module")
def r3():
    return calculate(T3(), on_date=ON)


@pytest.fixture(scope="module")
def r4():
    # Эйнштейн, 1905 — annus mirabilis; соляр на Берн (место жительства в 1905 г.)
    return calculate(T4(), on_date="1905-06-30", sr_place="Берн", sr_lat=46.9480, sr_lon=7.4474,
                     sr_tz="Europe/Zurich", period_start="1905-01-01", period_end="1905-12-31")


# ---------------------------------------------------------------------------
# Общие свойства
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("fx", ["r1", "r2", "r3", "r4"])
def test_contract_and_json(fx, request):
    r = request.getfixturevalue(fx)
    for k in ("method", "variant", "inputs_used", "warnings", "steps", "transits", "progressions",
              "solar_arc", "solar_return", "lunar_return", "profections"):
        assert k in r
    assert r["method"] == "western_forecast"
    json.dumps(r, ensure_ascii=False)
    assert len(r["steps"]) == 7


def test_deterministic_fixed_date(r1):
    again = calculate(T1(), on_date=ON)
    assert json.dumps(again, sort_keys=True, ensure_ascii=False) == json.dumps(r1, sort_keys=True, ensure_ascii=False)


def test_on_date_default_warns():
    r = calculate(T1(), hit_bodies=[])
    assert any("on_date не задан" in w for w in r["warnings"])


# ---------------------------------------------------------------------------
# Транзиты
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("fx", ["r1", "r2", "r3", "r4"])
def test_transit_aspects_invariants(fx, request):
    r = request.getfixturevalue(fx)
    natal = {**{p: v["lon"] for p, v in r["natal"]["bodies"].items()}, "asc": r["natal"]["asc"], "mc": r["natal"]["mc"]}
    for a in r["transits"]["aspects"]:
        assert a["orb"] <= a["orb_allowed"] + 1e-9 and a["orb_allowed"] == 1.0   # орбис Хэнда 1°
        t = r["transits"]["positions"][a["transit"]]["lon"]
        assert abs(abs(abs(sd(natal[a["natal"]], t)) - a["angle"]) - a["orb"]) < 1e-3
        for key in ("exact_prev_utc", "exact_next_utc"):
            if a[key]:
                jd = jd_of(a[key])
                x = abs(sd(natal[a["natal"]], lon(CODES[a["transit"]], jd)))
                assert abs(x - a["angle"]) < 1e-4


@pytest.mark.parametrize("fx", ["r1", "r2", "r3", "r4"])
def test_exact_hits_are_roots(fx, request):
    """Независимая проверка pyswisseph: в момент попадания долгота транзита = натал ± угол."""
    r = request.getfixturevalue(fx)
    natal = {**{p: v["lon"] for p, v in r["natal"]["bodies"].items()}, "asc": r["natal"]["asc"], "mc": r["natal"]["mc"]}
    assert r["transits"]["exact_hits"]
    for h in r["transits"]["exact_hits"]:
        L = lon(CODES[h["transit"]], h["jd"])
        assert abs(sd(h["transit_lon"], L)) < 2e-4
        target = (natal[h["natal"]] + h["side"] * ASPECTS[h["aspect"]][0]) % 360
        assert abs(sd(target, h["transit_lon"])) < 1e-5
        assert h["retrograde"] == (speed(CODES[h["transit"]], h["jd"]) < 0)


def test_triple_pass_structure(r1, r4):
    for r in (r1, r4):
        groups: dict = {}
        for h in r["transits"]["exact_hits"]:
            groups.setdefault((h["transit"], h["natal"], h["aspect"], h["side"]), []).append(h)
        triples = [g for g in groups.values() if len(g) == 3]
        assert triples
        for g in triples:
            assert [h["pass_index"] for h in g] == [1, 2, 3]
            assert [h["retrograde"] for h in g] == [False, True, False]


# Моменты точных аспектов по JPL Horizons (DE441): поправка Ньютона по долготам ObsEcLon вокруг нашего
# момента (запросы к https://ssd.jpl.nasa.gov/api/horizons.api, 14.10.2026). Расхождение с нашими ≤ 2,5 мин
# (Уран 1905 г. движется 0,04°/сут — это 0,15″), для 2026–2027 гг. ≤ 15 с.
HORIZONS_HITS = [
    ("r1", "jupiter", "square", "sun", 1, "2026-11-01T02:29:56+00:00"),
    ("r1", "jupiter", "square", "sun", 2, "2027-01-24T00:11:21+00:00"),
    ("r1", "jupiter", "square", "sun", 3, "2027-06-26T12:28:04+00:00"),
    ("r1", "saturn", "square", "uranus", 1, "2026-11-02T15:04:35+00:00"),
    ("r1", "saturn", "square", "uranus", 2, "2027-01-17T12:47:36+00:00"),
    ("r4", "uranus", "trine", "uranus", 1, "1905-01-11T04:04:14+00:00"),
    ("r4", "uranus", "trine", "uranus", 2, "1905-07-19T02:28:08+00:00"),
    ("r4", "uranus", "trine", "uranus", 3, "1905-10-29T21:00:28+00:00"),
    ("r4", "saturn", "conjunction", "jupiter", 1, "1905-03-19T04:07:32+00:00"),
    ("r4", "saturn", "conjunction", "jupiter", 2, "1905-09-21T09:40:29+00:00"),
    ("r4", "saturn", "conjunction", "jupiter", 3, "1905-12-09T07:49:09+00:00"),
]


@pytest.mark.parametrize("fx,body,asp,natal,idx,hz", HORIZONS_HITS)
def test_exact_hits_vs_horizons(fx, body, asp, natal, idx, hz, request):
    r = request.getfixturevalue(fx)
    h = [x for x in r["transits"]["exact_hits"] if (x["transit"], x["aspect"], x["natal"], x["pass_index"]) ==
         (body, asp, natal, idx)]
    assert len(h) == 1
    assert abs(h[0]["jd"] - jd_of(hz)) * 1440 < 3.0


# Стоянки по Horizons: экстремум долготы (часовая сетка ±2 сут, парабола). Для Плутона экстремум очень
# плоский, точность метода ~1 ч.
HORIZONS_STATIONS = [
    ("r1", "mercury", "retrograde", 2461337.7986, 0.25), ("r1", "mercury", "direct", 2461358.1638, 0.25),
    ("r1", "venus", "direct", 2461358.5194, 0.25), ("r1", "saturn", "direct", 2461385.4777, 0.25),
    ("r1", "neptune", "direct", 2461387.4299, 0.25), ("r1", "jupiter", "retrograde", 2461387.5376, 0.25),
    ("r1", "pluto", "direct", 2461329.5661, 1.5),
    ("r4", "mercury", "retrograde", 2417073.8479, 0.25), ("r4", "uranus", "direct", 2417098.1371, 0.25),
    ("r4", "neptune", "retrograde", 2417132.7227, 0.25), ("r4", "saturn", "direct", 2417149.8751, 0.25),
]


@pytest.mark.parametrize("fx,body,kind,hz,tol_h", HORIZONS_STATIONS)
def test_stations_vs_horizons(fx, body, kind, hz, tol_h, request):
    r = request.getfixturevalue(fx)
    st = [s for s in r["transits"]["stations"] if s["body"] == body and s["type"] == kind and abs(s["jd"] - hz) < 5]
    assert len(st) == 1
    assert abs(st[0]["jd"] - hz) * 24 < tol_h
    # смена знака скорости вокруг стоянки (независимо, pyswisseph)
    s0, s1 = speed(CODES[body], st[0]["jd"] - 1), speed(CODES[body], st[0]["jd"] + 1)
    assert (s0 > 0 > s1) if kind == "retrograde" else (s0 < 0 < s1)


def test_station_before_perfection_t2(r2):
    """T2: транзитный Плутон ретрограден и «сходится» к квадрату натального Плутона, но встаёт в директную
    стоянку 16.10.2026 раньше точного аспекта: следующего точного момента нет."""
    a = [x for x in r2["transits"]["aspects"] if (x["transit"], x["aspect"], x["natal"]) == ("pluto", "square", "pluto")]
    assert len(a) == 1 and a[0]["phase"] == "applying" and a[0]["exact_next_utc"] is None
    assert a[0]["exact_prev_utc"].startswith("2025-12-11")
    st = [s for s in r2["transits"]["stations"] if s["body"] == "pluto" and s["type"] == "direct"][0]
    assert st["utc"].startswith("2026-10-16") and st["aspects_to_natal"][0]["natal"] == "pluto"


def test_house_and_sign_ingresses(r1):
    cusps = r1["natal"]["cusps"]
    for h in r1["transits"]["house_ingresses"]:
        L = lon(CODES[h["body"]], h["jd"])
        assert abs(sd(cusps[h["cusp"] - 1], L)) < 1e-4
        from calculators.western import house_of
        after = lon(CODES[h["body"]], h["jd"] + 0.5)
        assert house_of(after, cusps) == h["enters_house"]
    for s in r1["transits"]["sign_ingresses"]:
        after = lon(CODES[s["body"]], s["jd"] + 0.5)
        assert int(after // 30) == ["Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo", "Libra", "Scorpio",
                                    "Sagittarius", "Capricorn", "Aquarius", "Pisces"].index(s["to_sign"])


def test_transit_orb_options():
    r = calculate(T1(), on_date=ON, transit_orbs=3, hit_bodies=[])
    r_d = calculate(T1(), on_date=ON, transit_orbs={"default": 0.5, "saturn": 2.0}, hit_bodies=[])
    assert len(r["transits"]["aspects"]) > 4
    assert all(a["orb_allowed"] == (2.0 if a["transit"] == "saturn" else 0.5) for a in r_d["transits"]["aspects"])
    r_s = calculate(T1(), on_date=ON, hit_bodies="jupiter,saturn")
    assert {h["transit"] for h in r_s["transits"]["exact_hits"]} <= {"jupiter", "saturn"}


def test_moon_hits_month():
    r = calculate(T1(), on_date=ON, period_start="2026-10-01", period_end="2026-10-31", hit_bodies="all_with_moon")
    moon = [h for h in r["transits"]["exact_hits"] if h["transit"] == "moon"]
    # Луна за ~31 сут проходит все 12 натальных точек: соединение и оппозиция с каждой ≥ 1 раза
    assert sum(1 for h in moon if h["aspect"] == "conjunction") >= 12
    assert r["transits"]["period"]["end_utc"].startswith("2026-11-01")


def test_crossings_and_stations_helpers():
    # Меркурий 2026: R 24.10 – D 13.11; точка 15° Скорпиона пройдена трижды
    st = stations("mercury", jd_of("2026-10-01T00:00+00:00"), jd_of("2026-12-01T00:00+00:00"))
    assert [s["type"] for s in st] == ["retrograde", "direct"]
    cr = crossings("mercury", [225.0], jd_of("2026-10-01T00:00+00:00"), jd_of("2026-12-31T00:00+00:00"),
                   split_at=[s["jd"] for s in st])
    assert len(cr) == 3 and [c[2] < 0 for c in cr] == [False, True, False]


# ---------------------------------------------------------------------------
# Вторичные прогрессии
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("fx", ["r1", "r2", "r3", "r4"])
def test_progressed_date_and_positions(fx, request):
    r = request.getfixturevalue(fx)
    jd_b, jd_on = r["inputs_used"]["birth_jd"], r["inputs_used"]["on_jd"]
    pjd = jd_b + (jd_on - jd_b) / Y
    assert abs(r["progressions"]["progressed_jd"] - pjd) < 2e-6
    for p in ("sun", "moon", "mercury", "venus", "mars", "jupiter", "saturn"):
        assert abs(sd(r["progressions"]["positions"][p]["lon"], lon(CODES[p], pjd))) < 1e-5
    # контрольная точка: прогрессивное Солнце ≈ 1° в год (0,953–1,019°/сут)
    arc = r["solar_arc"]["arc_true"]
    assert 0.95 < arc / r["age_years"] < 1.02


def test_wikipedia_progressed_date():
    """«a person born April 2, 1982 … 2007 progressed chart … April 27, 1982» (Wikipedia)."""
    r = calculate(BirthInput(1982, 4, 2, 12, 0, tz="UTC", lat=51.5, lon=0.0), on_date="2007-04-02T12:00", hit_bodies=[])
    assert r["progressions"]["progressed_utc"].startswith("1982-04-27")


def test_naibod_key_constants():
    # AstroWiki: 59′08,33″ = 0,98564733°; суточный прирост звёздного времени 3 мин 56,555 с
    assert abs(NAIBOD - (59 / 60 + 8.33 / 3600)) < 1e-6
    assert abs(NAIBOD / 15 * 3600 - 236.555) < 1e-3


@pytest.mark.parametrize("method", ["mean_sun", "naibod", "solar_arc", "solar_arc_ra", "quotidian"])
def test_progressed_angle_methods(method):
    r = calculate(T4(), on_date="1905-06-30", progression_angles=method, hit_bodies=[])
    age, mc_n = r["age_years"], r["natal"]["mc"]
    pr = r["progressions"]
    ang, mc_p = pr["angles"], pr["positions"]["mc"]["lon"]
    if method == "mean_sun":       # astro.com: ARMC + 0,98564733° × возраст
        assert abs(sd(r["natal"]["armc"], ang["armc"]) - NAIBOD * age) < 1e-6
    elif method == "naibod":
        assert abs(sd(mc_n, mc_p) - NAIBOD * age) < 1e-5
    elif method == "solar_arc":    # MC + истинная солнечная дуга
        assert abs(sd(mc_n, mc_p) - r["solar_arc"]["arc_true"]) < 1e-5
    elif method == "quotidian":    # карта на прогрессивный момент
        h = eph.houses(pr["progressed_jd"], 48.4011, 9.9876, "P")
        assert abs(sd(h["mc"], mc_p)) < 5e-4      # progressed_jd округлён до 1e-6 сут, MC — 361°/сут
    # куспид 1 = ASC, куспид 10 = MC
    assert abs(sd(ang["cusps"][0]["lon"], pr["positions"]["asc"]["lon"])) < 1e-6
    assert abs(sd(ang["cusps"][9]["lon"], mc_p)) < 1e-6
    # в момент рождения все способы дают натальные углы
    r0 = calculate(T4(), on_date="1879-03-14T10:50:03+00:00", progression_angles=method, hit_bodies=[])
    assert abs(sd(r0["natal"]["mc"], r0["progressions"]["positions"]["mc"]["lon"])) < 1e-3
    assert abs(sd(r0["natal"]["asc"], r0["progressions"]["positions"]["asc"]["lon"])) < 2e-3


def test_t4_progressions_1905(r4):
    pr = r4["progressions"]
    assert pr["progressed_utc"] == "1879-04-09T17:52:53+00:00"
    assert pr["positions"]["sun"]["pos"] == "19°30′08″ Овен"
    assert pr["positions"]["moon"]["pos"] == "29°27′03″ Скорпион"
    assert pr["positions"]["mc"]["pos"] == "10°59′20″ Овен" and pr["positions"]["asc"]["pos"] == "1°45′00″ Лев"
    assert pr["lunation"]["phase"] == "full" and abs(pr["lunation"]["elongation"] - 219.9487) < 1e-3
    assert pr["moon"]["next_sign_change"]["utc"].startswith("1905-07-13") and pr["moon"]["next_sign_change"]["to_sign"] == "Sagittarius"
    a = pr["aspects_to_natal"][0]
    assert (a["progressed"], a["aspect"], a["natal"]) == ("mercury", "trine", "uranus") and a["exact_utc"].startswith("1905-04-07")


def test_progressed_moon_events(r1):
    pm = r1["progressions"]["moon"]
    jd_b = r1["inputs_used"]["birth_jd"]
    ev = pm["next_sign_change"]
    pjd = jd_b + (ev["jd"] - jd_b) / Y
    assert abs(sd(90.0, lon(swe.MOON, pjd))) < 1e-5 and ev["to_sign"] == "Cancer"
    hv = pm["next_natal_house_change"]
    pjd = jd_b + (hv["jd"] - jd_b) / Y
    assert abs(sd(r1["natal"]["cusps"][hv["to_house"] - 1], lon(swe.MOON, pjd))) < 1e-5


@pytest.mark.parametrize("fx", ["r1", "r2", "r3", "r4"])
def test_lunation_invariants(fx, request):
    r = request.getfixturevalue(fx)
    pr, lu = r["progressions"], r["progressions"]["lunation"]
    el = (pr["positions"]["moon"]["lon"] - pr["positions"]["sun"]["lon"]) % 360
    assert abs(el - lu["elongation"]) < 1e-3 and lu["phase_index"] == int(el // 45) + 1
    assert lu["phase_started"]["jd"] <= r["inputs_used"]["on_jd"] <= lu["next_phase"]["jd"]
    # прогрессивный лунационный цикл ≈ 29,5 лет
    assert 28.5 < (lu["next_new_moon"]["jd"] - lu["last_new_moon"]["jd"]) / Y < 31.0


# F. Boele, «The Progressed Lunation Cycle» (astro.com, 2006): события и фазы прогрессивной лунации.
# Данные рождения — из раздела «Chart (and Biographical) Data and Sources» статьи.
def dm(d: int, m: int) -> float:
    return d + m / 60


BOELE = {
    "aldrin": BirthInput(1930, 1, 20, 14, 17, tz="UTC-05:00", lat=dm(40, 48), lon=-dm(74, 12)),
    "ali": BirthInput(1942, 1, 17, 18, 35, tz="UTC-06:00", lat=dm(38, 15), lon=-dm(85, 46)),
    "armstrong": BirthInput(1930, 8, 5, 0, 31, tz="UTC-05:00", lat=dm(40, 34), lon=-dm(84, 12)),
    "churchill": BirthInput(1874, 11, 30, 1, 30, tz="UTC", lat=dm(51, 52), lon=-dm(1, 21)),
    "diana": BirthInput(1961, 7, 1, 19, 45, tz="UTC+01:00", lat=dm(52, 50), lon=-dm(0, 30)),
    "lennon": BirthInput(1940, 10, 9, 18, 30, tz="UTC+01:00", lat=dm(53, 25), lon=-dm(2, 55)),
    "mandela": BirthInput(1918, 7, 18, 14, 54, tz="UTC+02:00", lat=-dm(31, 35), lon=dm(28, 47)),
    "mccartney": BirthInput(1942, 6, 18, 14, 0, tz="UTC+02:00", lat=dm(53, 25), lon=-dm(2, 55)),
    "jp2": BirthInput(1920, 5, 18, 17, 30, tz="UTC+02:00", lat=dm(49, 53), lon=dm(19, 30)),
    "roosevelt": BirthInput(1884, 10, 11, 11, 0, tz="UTC-05:00", lat=dm(40, 42), lon=-dm(74, 0)),
    "rushdie": BirthInput(1947, 6, 19, 2, 30, tz="UTC+05:30", lat=dm(18, 58), lon=dm(72, 50)),
    "ringo": BirthInput(1940, 7, 7, 0, 5, tz="UTC+01:00", lat=dm(53, 25), lon=-dm(2, 55)),
    "thatcher": BirthInput(1925, 10, 13, 9, 0, tz="UTC", lat=dm(52, 55), lon=-dm(0, 29)),
    "tolkien": BirthInput(1892, 1, 3, 22, 0, tz="LMT", lat=-dm(29, 12), lon=dm(26, 7)),   # «между 20 и 24 ч»
    "vangogh": BirthInput(1853, 3, 30, 11, 0, tz="LMT", lat=dm(51, 28), lon=dm(4, 40)),
}
BOELE_CASES = [
    ("thatcher", "1990-11-22", "new"), ("mccartney", "1970-04-09", "new"), ("ringo", "1970-04-10", "new"),
    ("aldrin", "1969-07-20", "new"), ("aldrin", "1971-10-15", "new"), ("armstrong", "1951-01-01", "new"),
    ("jp2", "1978-10-16", "new"), ("lennon", "1962-01-24", "new"), ("churchill", "1945-05-08", "new"),
    ("tolkien", "1954-07-29", "first_quarter"), ("diana", "1981-07-29", "first_quarter"),
    ("lennon", "1969-03-20", "first_quarter"), ("rushdie", "1989-02-14", "gibbous"),
    ("armstrong", "1936-08-05", "full"), ("armstrong", "1966-03-16", "full"),
    ("mccartney", "1957-10-18", "disseminating"), ("armstrong", "1969-07-20", "disseminating"),
    ("mandela", "1990-02-11", "last_quarter"), ("ali", "1964-03-06", "last_quarter"),
    ("vangogh", "1890-07-27", "balsamic"), ("ali", "1967-04-28", "balsamic"), ("mccartney", "1995-06-01", "balsamic"),
    ("ringo", "1995-06-01", "balsamic"), ("churchill", "1940-05-10", "balsamic"), ("churchill", "1940-06-04", "balsamic"),
    ("churchill", "1940-08-20", "balsamic"), ("roosevelt", "1948-12-10", "balsamic"), ("mandela", "1994-05-10", "balsamic"),
]


@pytest.mark.parametrize("who,day,phase", BOELE_CASES)
def test_progressed_lunation_boele(who, day, phase):
    r = calculate(BOELE[who], on_date=day, hit_bodies=[], include_lunar_return=False)
    assert r["progressions"]["lunation"]["phase"] == phase


@pytest.mark.parametrize("who,day,phase_article,days_to_boundary", [
    ("lennon", "1961-11-15", "new", 33),            # Эпштейн впервые увидел группу 09.11.1961
    ("lennon", "1968-11-08", "first_quarter", 25),  # развод с Синтией
])
def test_progressed_lunation_boele_boundary(who, day, phase_article, days_to_boundary):
    """Граничные события статьи: по нашему расчёту фаза наступает на 25–33 дня позже (≈0,8–1,1°
    прогрессивной элонгации — это ±1 ч во времени рождения рейтинга A)."""
    r = calculate(BOELE[who], on_date=day, hit_bodies=[], include_lunar_return=False)
    lu = r["progressions"]["lunation"]
    assert lu["next_phase_name"] == phase_article
    assert abs((lu["next_phase"]["jd"] - jd_of(day + "T00:00+00:00")) - days_to_boundary) < 2


# ---------------------------------------------------------------------------
# Дирекции солнечной дуги
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("fx", ["r1", "r2", "r3", "r4"])
def test_solar_arc(fx, request):
    r = request.getfixturevalue(fx)
    sa = r["solar_arc"]
    assert abs(sa["arc_true"] - (r["progressions"]["positions"]["sun"]["lon"] - r["natal"]["bodies"]["sun"]["lon"]) % 360) < 1e-6
    assert abs(sa["arc_naibod"] - NAIBOD * r["age_years"]) < 1e-6
    for p, d in sa["directed"].items():
        base = r["natal"]["asc"] if p == "asc" else r["natal"]["mc"] if p == "mc" else r["natal"]["bodies"][p]["lon"]
        assert abs(sd(base + sa["arc"], d["lon"])) < 1e-5
    jd_b = r["inputs_used"]["birth_jd"]
    for a in sa["aspects_to_natal"]:
        assert a["orb"] <= 1.0 and a["directed"] != a["natal"]
        # в момент exact_utc направленная точка точно в аспекте (истинная дуга по pyswisseph)
        jd = jd_of(a["exact_utc"])
        arc = (lon(swe.SUN, jd_b + (jd - jd_b) / Y) - r["natal"]["bodies"]["sun"]["lon"]) % 360
        p = a["directed"]
        base = r["natal"]["asc"] if p == "asc" else r["natal"]["mc"] if p == "mc" else r["natal"]["bodies"][p]["lon"]
        q = a["natal"]
        tgt = r["natal"]["asc"] if q == "asc" else r["natal"]["mc"] if q == "mc" else r["natal"]["bodies"][q]["lon"]
        assert abs(abs(abs(sd(tgt, base + arc)) - a["angle"])) < 2e-4


def test_solar_arc_naibod_and_from_mc():
    r = calculate(T4(), on_date="1905-06-30", arc="naibod", sa_asc="from_mc", hit_bodies=[])
    sa = r["solar_arc"]
    assert sa["arc"] == pytest.approx(NAIBOD * r["age_years"], abs=1e-6)
    assert sa["directed"]["mc"]["pos"] == "8°45′22″ Овен" and sa["directed"]["asc"]["pos"] == "0°13′03″ Лев"
    # ASC «из MC» совпадает с ASC прогрессий методом naibod (тот же MC на широте рождения)
    rp = calculate(T4(), on_date="1905-06-30", progression_angles="naibod", hit_bodies=[])
    assert abs(sd(rp["progressions"]["positions"]["asc"]["lon"], sa["directed"]["asc"]["lon"])) < 0.02


# ---------------------------------------------------------------------------
# Соляр и лунар
# ---------------------------------------------------------------------------

def test_t4_solar_return_bern(r4):
    sr = r4["solar_return"]
    # JPL Horizons: Солнце в момент рождения 353.5076977°, в наш момент соляра 353.5077229° (Δ 0,09″ ≈ 2 с)
    assert abs(jd_of(sr["moment_utc"]) - jd_of("1905-03-14T18:12:59+00:00")) * 86400 < 10
    assert sr["local"] == "1905-03-14T19:13:01" and sr["utc_offset"] == "UTC+01:00"   # Берн, CET
    assert sr["sun_check_arcsec"] < 0.01
    assert sr["angles"]["asc"]["pos"] == "1°46′52″ Весы" and sr["angles"]["mc"]["pos"] == "2°11′44″ Рак"
    assert sr["where"] == "relocated" and sr["houses"]["system"] == "P"


def test_t1_solar_return_vs_horizons(r1):
    # Horizons: натальное Солнце 54.3358312°, в наш момент соляра 54.3358333° (Δ 0,01″)
    sr = r1["solar_return"]
    assert sr["moment_utc"] == "2026-05-15T03:34:26+00:00" and sr["local"] == "2026-05-15T06:34:26"
    assert sr["where"] == "birthplace"


@pytest.mark.parametrize("b", [T1(), T2(), T3(), T4()])
@pytest.mark.parametrize("offset", [1, 4, 26, 50, 96])
def test_solar_return_within_a_day(b, offset):
    """Соляр каждого года отстоит от годовщины момента рождения (UT) меньше чем на сутки
    (AstroWiki: «either on the same date as the day of birth or the day before or after»).
    Годы — от рождения: 1-й, 4-й (високосный цикл), 26-й, 50-й и 96-й (у T4 — 1975 г., через
    невисокосный 1900 г.; у T3 — 2100 г., невисокосный по григорианскому правилу)."""
    year = b.year + offset
    r = calculate(b, on_date=ON, sr_year=year, hit_bodies=[], include_lunar_return=False)
    sr = r["solar_return"]
    assert abs(sr["days_from_birth_anniversary_utc"]) < 1.0
    assert abs(sd(sr["natal_sun"], lon(swe.SUN, sr["moment_jd"]))) < 1e-6
    assert jd_of(sr["moment_utc"][:4] + "-01-01T00:00+00:00") <= sr["moment_jd"]
    assert sr["moment_utc"].startswith(str(year))


def test_t3_feb29_solar_returns():
    """29 февраля: в невисокосный год соляр приходится на 28.02 (местное время), в високосный — на 29.02."""
    for year, local in [(2026, "2026-02-28T16:17:55"), (2027, "2027-02-28T22:03:16"), (2028, "2028-02-29T03:47:54")]:
        r = calculate(T3(), on_date=ON, sr_year=year, hit_bodies=[])
        assert r["solar_return"]["local"] == local


def test_relocated_vs_birthplace_same_moment():
    a = calculate(T1(), on_date=ON, hit_bodies=[])
    b = calculate(T1(), on_date=ON, sr_place="Новосибирск", hit_bodies=[])
    assert a["solar_return"]["moment_utc"] == b["solar_return"]["moment_utc"]
    assert b["solar_return"]["utc_offset"] == "UTC+07:00" and b["solar_return"]["local"] == "2026-05-15T10:34:26"
    assert a["solar_return"]["angles"]["asc"]["sign"] != b["solar_return"]["angles"]["asc"]["sign"]


def test_polar_solar_return_fallback():
    r = calculate(T1(), on_date=ON, sr_lat=68.9585, sr_lon=33.0827, sr_tz="Europe/Moscow", hit_bodies=[])
    assert r["solar_return"]["houses"]["system"] == "O"
    assert any(w.startswith("Соляр:") and "Порфирий" in w for w in r["warnings"])


def test_sidereal_solar_return_later_by_precession(r4):
    s = calculate(T4(), on_date="1905-06-30", sr_zodiac="sidereal", hit_bodies=[])
    dt = s["solar_return"]["moment_jd"] - r4["solar_return"]["moment_jd"]
    # прецессия 50,29″/год × 26 лет / (0,9956°/сут) ≈ 0,365 сут
    assert 0.33 < dt < 0.40
    assert any("прецесси" in w for w in s["warnings"])


def test_lunar_return(r1):
    lr = r1["lunar_return"]
    jd = jd_of(lr["moment_utc"])
    assert abs(sd(r1["natal"]["bodies"]["moon"]["lon"], lon(swe.MOON, jd))) < 1e-3
    assert jd <= r1["inputs_used"]["on_jd"] < jd_of(lr["next_moment_utc"])
    assert 27.0 < jd_of(lr["next_moment_utc"]) - jd < 27.7


# ---------------------------------------------------------------------------
# Профекции
# ---------------------------------------------------------------------------

COPPOLA = BirthInput(1939, 4, 7, 1, 38, tz="America/Detroit", lat=42.3314, lon=-83.0458)


@pytest.mark.parametrize("day,sign,lord,house", [
    ("1971-06-01", "Virgo", "mercury", 9),      # «Virgo profection year … turned 32 on April 7, 1971»
    ("1972-06-01", "Libra", "venus", 10),       # «10th-house Libra profection year»
    ("1976-06-01", "Aquarius", "saturn", 2),    # «turned 37 … Aquarius profection year … ruled by Saturn»
    ("1979-07-01", "Taurus", "venus", 5),       # «summer of 1979 … Taurus profection year … Venus»
])
def test_profections_coppola_brennan(day, sign, lord, house):
    r = calculate(COPPOLA, on_date=day, hit_bodies=[])
    p = r["profections"]
    assert (p["sign"], p["lord"], p["house_whole_sign"]) == (sign, lord, house)
    assert r["natal"]["bodies"]["sun"]["pos"].endswith("Овен")
    assert 277.38 < r["natal"]["asc"] < 277.44     # Astrotheme: AS 7°24′ Capricorn


@pytest.mark.parametrize("fx,age,house,sign,lord", [
    ("r1", 36, 1, "Virgo", "mercury"), ("r2", 42, 7, "Aries", "mars"),
    ("r3", 22, 11, "Capricorn", "saturn"), ("r4", 26, 3, "Virgo", "mercury"),
])
def test_profections_t1_t4(fx, age, house, sign, lord, request):
    p = request.getfixturevalue(fx)["profections"]
    assert (p["age_completed"], p["house_whole_sign"], p["sign"], p["lord"]) == (age, house, sign, lord)
    assert p["year_start_utc"] == request.getfixturevalue(fx)["solar_return"]["moment_utc"]


def test_profection_cycle_and_boundaries():
    # 12-летний цикл: в 12, 24 и 36 лет — снова 1-й дом; граница — момент соляра
    for d, h in [("2002-05-15T12:00+00:00", 1), ("2014-05-15T12:00+00:00", 1), ("2026-05-15T12:00+00:00", 1),
                 ("2026-05-15T00:00+00:00", 12)]:
        r = calculate(T1(), on_date=d, hit_bodies=[])
        assert r["profections"]["house_whole_sign"] == h
    rb = calculate(T1(), on_date="2026-05-15T00:00+00:00", profection_boundary="birthday", hit_bodies=[])
    assert rb["profections"]["house_whole_sign"] == 1     # 15.05 00:00 MSK = 14.05 21:00 UTC — уже день рождения


# ---------------------------------------------------------------------------
# Неизвестное время, ошибки
# ---------------------------------------------------------------------------

def test_unknown_time():
    r = calculate(BirthInput(1990, 5, 15, place="Москва"), on_date=ON)
    assert r["inputs_used"]["time_known"] is False
    assert r["progressions"]["angles"] is None and r["profections"] is None
    assert r["solar_return"]["angles"] is None
    assert "asc" not in r["solar_arc"]["directed"]
    assert any("Время рождения неизвестно" in w for w in r["warnings"])
    rs = calculate(BirthInput(1990, 5, 15, place="Москва"), on_date=ON, profection_from="sun")
    assert rs["profections"]["sign"] == "Taurus" and rs["profections"]["age_completed"] == 36   # Телец + 36 ≡ Телец


def test_errors():
    with pytest.raises(ValueError):
        calculate(T1(), on_date="1980-01-01")
    with pytest.raises(ValueError):
        calculate(T1(), on_date=ON, progression_angles="primary")
    with pytest.raises(ValueError):
        calculate(T1(), on_date=ON, arc="mean")
    with pytest.raises(ValueError):
        calculate(T1(), on_date=ON, period_start="2026-10-14", period_end="2026-10-01")
    with pytest.raises(ValueError):
        calculate(T1(), on_date=ON, hit_bodies="vulcan")


def test_steps_text_t4(r4):
    s = {x["step"]: x["detail"] for x in r4["steps"]}
    assert "26.293645" in s["2. Целевой момент"]
    assert "25.9945" in s["5. Дирекции солнечной дуги"] and "25.9163" in s["5. Дирекции солнечной дуги"]
    assert "Рак + 26 mod 12 = Дева" in s["7. Годовые профекции"]
