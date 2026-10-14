"""Тесты модуля 06 — западная тропическая натальная карта (calculators/western.py).

Внешние векторы:
* Astrotheme (данные рождения с рейтингом Rodden AA, движок на Swiss Ephemeris, Плацидус,
  истинный узел, орбисы из https://www.astrotheme.com/astrology_aspects.php):
  - Эйнштейн (T4):   https://www.astrotheme.com/astrology/Albert_Einstein
  - Мэрилин Монро:   https://www.astrotheme.com/astrology/Marilyn_Monroe
  - Барак Обама:     https://www.astrotheme.com/astrology/Barack_Obama
  - Елизавета II:    https://www.astrotheme.com/astrology/Elizabeth_II
  Позиции на сайте даны с точностью до минуты, поэтому допуск 1′ (планеты) и
  1,5′ (углы/куспиды — координаты места сайт не публикует).
* USNO, моменты равноденствий и солнцестояний: https://aa.usno.navy.mil/api/seasons?year=YYYY
"""
from __future__ import annotations

import json
import math

import pytest

from calculators.common.time import BirthInput
from calculators.western import (
    ASPECTS, allowed_orb, asc_from_ramc, calculate, find_aspects, gmst_hours_usno, house_of,
    mc_from_ramc, mean_obliquity, moon_lon_low_precision, sign_rising_hours, sun_lon_low_precision,
)
from calculators.common import ephemeris as eph

SIGNS = ["Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
         "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"]


def lon(s: str) -> float:
    """«23°30' Pisces» → эклиптическая долгота в градусах."""
    d, rest = s.split("°")
    m, sign = rest.split("'")
    return SIGNS.index(sign.strip()) * 30 + int(d) + int(m) / 60


def arcmin(a: float, b: float) -> float:
    return abs((a - b + 180.0) % 360.0 - 180.0) * 60.0


def value(r: dict, key: str) -> float:
    if key in r["bodies"]:
        return r["bodies"][key]["lon"]
    if key in ("asc", "mc", "vertex"):
        return r["angles"][key]["lon"]
    if key == "pof":
        return r["part_of_fortune"]["lon"]
    if key.startswith("c"):
        return r["houses"]["cusps"][int(key[1:]) - 1]["lon"]
    raise KeyError(key)


# ---------------------------------------------------------------------------
# Внешние векторы
# ---------------------------------------------------------------------------

EXTERNAL = {
    # T4. https://www.astrotheme.com/astrology/Albert_Einstein — AA, свидетельство о рождении (L. Rodden)
    # 14.03.1879 11:30 местного среднего времени, Ульм.
    "einstein": (
        BirthInput(1879, 3, 14, 11, 30, tz="LMT", lat=48.4011, lon=9.9876),
        {"sun": "23°30' Pisces", "moon": "14°32' Sagittarius", "mercury": "3°09' Aries",
         "venus": "16°59' Aries", "mars": "26°55' Capricorn", "jupiter": "27°29' Aquarius",
         "saturn": "4°11' Aries", "uranus": "1°17' Virgo", "neptune": "7°52' Taurus",
         "pluto": "24°44' Taurus", "north_node": "2°44' Aquarius", "chiron": "5°33' Taurus"},
        {"asc": "11°38' Cancer", "mc": "12°50' Pisces", "vertex": "27°54' Scorpio", "pof": "2°40' Aries",
         "c2": "28°37' Cancer", "c3": "17°48' Leo", "c5": "18°20' Libra", "c6": "3°06' Sagittarius"},
        {"uranus", "north_node"},
    ),
    # https://www.astrotheme.com/astrology/Marilyn_Monroe — AA, свидетельство о рождении
    # 01.06.1926 9:30 PST (UTC−8), Лос-Анджелес 34°03′N 118°15′W.
    "monroe": (
        BirthInput(1926, 6, 1, 9, 30, tz="America/Los_Angeles", lat=34 + 3 / 60, lon=-(118 + 15 / 60)),
        {"sun": "10°27' Gemini", "moon": "19°06' Aquarius", "mercury": "6°47' Gemini",
         "venus": "28°45' Aries", "mars": "20°44' Pisces", "jupiter": "26°50' Aquarius",
         "saturn": "21°26' Scorpio", "uranus": "29°00' Pisces", "neptune": "22°13' Leo",
         "pluto": "13°23' Cancer", "north_node": "16°54' Cancer", "chiron": "0°24' Taurus"},
        {"asc": "13°04' Leo", "mc": "6°00' Taurus", "vertex": "24°31' Sagittarius", "pof": "21°44' Aries",
         "c2": "6°08' Virgo", "c3": "3°40' Libra", "c5": "10°35' Sagittarius", "c6": "13°31' Capricorn"},
        {"saturn"},
    ),
    # https://www.astrotheme.com/astrology/Barack_Obama — AA, свидетельство о рождении
    # 04.08.1961 19:24 HST (UTC−10), Гонолулу 21°18′N 157°52′W.
    "obama": (
        BirthInput(1961, 8, 4, 19, 24, tz="Pacific/Honolulu", lat=21 + 18 / 60, lon=-(157 + 52 / 60)),
        {"sun": "12°33' Leo", "moon": "3°21' Gemini", "mercury": "2°20' Leo", "venus": "1°47' Cancer",
         "mars": "22°35' Virgo", "jupiter": "0°52' Aquarius", "saturn": "25°20' Capricorn",
         "uranus": "25°16' Leo", "neptune": "8°36' Scorpio", "pluto": "6°59' Virgo",
         "north_node": "27°18' Leo", "chiron": "5°19' Pisces"},
        {"asc": "18°03' Aquarius", "mc": "28°53' Scorpio", "vertex": "12°54' Virgo", "pof": "27°14' Aries",
         "c2": "25°54' Pisces", "c3": "0°18' Taurus", "c5": "23°59' Gemini", "c6": "19°01' Cancer"},
        {"jupiter", "saturn", "north_node"},
    ),
    # https://www.astrotheme.com/astrology/Elizabeth_II — AA, свидетельство о рождении
    # 21.04.1926 2:40 BST (летнее время UTC+1 действовало с 18.04.1926), Мейфэр, 17 Bruton St.
    "elizabeth_ii": (
        BirthInput(1926, 4, 21, 2, 40, tz="Europe/London", lat=51.5101, lon=-0.1456),
        {"sun": "0°12' Taurus", "moon": "12°07' Leo", "mercury": "4°40' Aries", "venus": "13°57' Pisces",
         "mars": "20°52' Aquarius", "jupiter": "22°31' Aquarius", "saturn": "24°27' Scorpio",
         "uranus": "27°21' Pisces", "neptune": "22°02' Leo", "pluto": "12°42' Cancer",
         "north_node": "20°07' Cancer", "chiron": "28°01' Aries"},
        {"asc": "21°24' Capricorn", "mc": "25°34' Scorpio", "vertex": "0°21' Virgo", "pof": "9°29' Libra",
         "c2": "18°27' Pisces", "c3": "0°19' Taurus", "c5": "14°07' Gemini", "c6": "1°06' Cancer"},
        {"saturn", "neptune", "north_node"},
    ),
}

# Аспекты Astrotheme (10 планет + AS + MC), формат «P1 аспект P2 орбис».
ASTROTHEME_ASPECTS = {
    "einstein": """sun conjunction mercury 9°38'|sun conjunction mc 10°40'|sun conjunction saturn 10°40'|
mercury conjunction saturn 1°02'|jupiter opposition uranus 3°48'|moon square mc 1°41'|jupiter square pluto 2°45'|
venus square asc 5°20'|uranus square pluto 6°33'|saturn square asc 7°27'|mars trine pluto 2°11'|moon trine venus 2°27'|
uranus trine neptune 6°35'|sun sextile pluto 1°13'|sun sextile mars 3°24'|neptune sextile asc 3°46'|
neptune sextile mc 4°57'|mercury quincunx uranus 1°51'|moon quincunx asc 2°53'|sun semisquare neptune 0°38'|
mars semisquare mc 0°55'|venus sesquisquare uranus 0°41'|jupiter sesquisquare asc 0°50'|pluto quintile mc 0°06'|
moon quintile jupiter 0°57'|moon biquintile neptune 0°39'|mars semisextile jupiter 0°34'""",
    "monroe": """sun conjunction mercury 3°39'|venus conjunction mc 7°15'|moon conjunction jupiter 7°43'|
mars conjunction uranus 8°15'|neptune conjunction asc 9°09'|moon opposition neptune 3°07'|jupiter opposition neptune 4°36'|
moon opposition asc 6°01'|saturn square neptune 0°46'|moon square saturn 2°20'|jupiter square saturn 5°23'|
mars trine saturn 0°42'|venus trine neptune 6°31'|mars trine pluto 7°20'|saturn trine uranus 7°33'|saturn trine pluto 8°02'|
sun trine moon 8°39'|venus sextile jupiter 1°55'|sun sextile asc 2°37'|mars quincunx neptune 1°29'|mars semisquare mc 0°16'|
uranus sesquisquare asc 0°55'|jupiter sesquisquare pluto 1°33'|sun quintile neptune 0°13'|sun quintile uranus 0°33'|
moon biquintile pluto 0°17'|uranus biquintile neptune 0°46'|venus semisextile uranus 0°14'|pluto semisextile asc 0°19'|
mercury semisextile mc 0°46'|moon semisextile mars 1°37'""",
    "obama": """jupiter conjunction saturn 5°31'|sun conjunction mercury 10°12'|mercury opposition jupiter 1°28'|
moon opposition mc 4°28'|sun opposition asc 5°29'|mercury opposition saturn 7°00'|uranus opposition asc 7°13'|
moon square pluto 3°37'|uranus square mc 3°37'|sun square neptune 3°56'|mercury square neptune 6°16'|
jupiter square neptune 7°44'|moon square uranus 8°05'|moon trine jupiter 2°29'|mars trine saturn 2°45'|
mercury trine mc 3°26'|venus trine neptune 6°48'|moon trine saturn 8°01'|mars trine jupiter 8°16'|
moon sextile mercury 1°01'|neptune sextile pluto 1°37'|jupiter sextile mc 1°58'|saturn sextile mc 3°33'|
venus sextile pluto 5°11'|saturn quincunx uranus 0°03'|venus quincunx jupiter 0°55'|mars semisquare neptune 1°01'|
venus sesquisquare asc 1°15'|jupiter biquintile pluto 0°07'|mercury semisextile venus 0°32'|moon semisextile venus 1°34'""",
    "elizabeth_ii": """saturn conjunction mc 1°07'|mars conjunction jupiter 1°38'|mercury conjunction uranus 7°18'|
moon conjunction neptune 9°54'|jupiter opposition neptune 0°28'|mars opposition neptune 1°10'|pluto opposition asc 8°41'|
moon opposition mars 8°44'|jupiter square saturn 1°56'|saturn square neptune 2°24'|jupiter square mc 3°03'|
neptune square mc 3°31'|mars square saturn 3°34'|mars square mc 4°42'|venus trine pluto 1°14'|uranus trine mc 1°47'|
saturn trine uranus 2°54'|moon trine mercury 7°27'|sun trine neptune 8°10'|saturn sextile asc 3°02'|
uranus sextile asc 5°57'|neptune quincunx asc 0°37'|moon quincunx venus 1°50'|mercury semisquare mars 1°12'|
sun semisquare venus 1°14'|moon sesquisquare uranus 0°14'|pluto sesquisquare mc 2°08'|
mercury sesquisquare neptune 2°22'|sun quintile pluto 0°30'|uranus biquintile neptune 0°40'|mars semisextile asc 0°32'|
moon semisextile pluto 0°35'|jupiter semisextile asc 1°06'""",
}


def parse_aspects(text: str) -> dict:
    out = {}
    for item in text.replace("\n", "").split("|"):
        p1, asp, p2, orb = item.split()
        d, m = orb.rstrip("'").split("°")
        out[(frozenset((p1, p2)), asp)] = int(d) + int(m) / 60
    return out


@pytest.mark.parametrize("key", list(EXTERNAL))
def test_external_positions_within_1_arcmin(key):
    b, planets, _angles, _retro = EXTERNAL[key]
    r = calculate(b)
    for name, s in planets.items():
        assert arcmin(value(r, name), lon(s)) <= 1.0, (key, name, r["bodies"][name]["pos"], s)


@pytest.mark.parametrize("key", list(EXTERNAL))
def test_external_angles_cusps_vertex_pof(key):
    b, _planets, angles, _retro = EXTERNAL[key]
    r = calculate(b)
    for name, s in angles.items():
        assert arcmin(value(r, name), lon(s)) <= 1.5, (key, name, s)


@pytest.mark.parametrize("key", list(EXTERNAL))
def test_external_retrograde_flags(key):
    b, _p, _a, retro = EXTERNAL[key]
    r = calculate(b)
    got = {p for p in [*r["bodies"]] if p not in ("south_node", "lilith", "chiron") and r["bodies"][p]["retrograde"]}
    assert got == retro


@pytest.mark.parametrize("key", list(EXTERNAL))
def test_external_aspects_astrotheme_orbs(key):
    """Набор аспектов (10 планет + ASC + MC) совпадает с Astrotheme один в один (схема по умолчанию
    'astrotheme' = фактические орбисы сайта: квинконс 2,8, полусекстиль 1,5, квинтиль/биквинтиль 1,2)."""
    b, *_ = EXTERNAL[key]
    r = calculate(b, aspect_points="planets_angles")
    ours = {(frozenset((a["p1"], a["p2"])), a["aspect"]): a["orb"] for a in r["aspects"]}
    theirs = parse_aspects(ASTROTHEME_ASPECTS[key])
    assert set(ours) == set(theirs), (set(ours) - set(theirs), set(theirs) - set(ours))
    for k in set(ours) & set(theirs):
        assert abs(ours[k] - theirs[k]) * 60 <= 2.0, (k, ours[k], theirs[k])


@pytest.mark.parametrize("key", list(EXTERNAL))
def test_external_aspects_astrotheme_published_table(key):
    """Старое умолчание (опубликованная таблица, orbs='astrotheme_published') теряет только полусекстили
    шире 1,0°(+0,3°): Луна–Марс 1°37′ у Монро, Луна–Венера 1°34′ у Обамы, Юпитер–ASC 1°06′ у Елизаветы II."""
    b, *_ = EXTERNAL[key]
    r = calculate(b, aspect_points="planets_angles", orbs="astrotheme_published")
    ours = {(frozenset((a["p1"], a["p2"])), a["aspect"]) for a in r["aspects"]}
    theirs = parse_aspects(ASTROTHEME_ASPECTS[key])
    assert not ours - set(theirs)
    missing = set(theirs) - ours
    for k in missing:
        assert k[1] == "semisextile" and theirs[k] > allowed_orb("astrotheme_published", "semisextile", *k[0]), k
    assert len(missing) <= 1


# Пограничные пары из 88 карт Astrotheme (повторная проверка 14.10.2026), по которым восстановлены
# фактические орбисы минорных аспектов. Долготы — как на страницах https://www.astrotheme.com/astrology/<Имя>
# (раздел «Positions of Planets», AS/MC в шапке), «listed» — показан ли аспект в списке аспектов страницы.
#   https://www.astrotheme.com/astrology/Joe_Biden, /Pablo_Picasso, /Bill_Gates, /Emmanuel_Macron,
#   /Dustin_Hoffman, /George_Clooney, /Steve_Jobs, /Serge_Gainsbourg, /Charles_Aznavour, /Tom_Hanks,
#   /Grace_Kelly, /Catherine_Deneuve, /Julia_Roberts, /Richard_Nixon
ASTROTHEME_BOUNDARY = [
    # (карта, тело1, долгота1, тело2, долгота2, аспект, показан на сайте)
    ("Joe_Biden", "moon", "0°59' Taurus", "uranus", "2°46' Gemini", "semisextile", True),        # 1°47′ со светилом
    ("Pablo_Picasso", "sun", "2°43' Scorpio", "venus", "4°32' Libra", "semisextile", False),     # 1°49′
    ("Bill_Gates", "pluto", "28°21' Leo", "asc", "26°58' Cancer", "semisextile", True),          # 1°23′
    ("Emmanuel_Macron", "uranus", "14°50' Scorpio", "neptune", "16°22' Sagittarius", "semisextile", False),  # 1°32′
    ("Dustin_Hoffman", "sun", "16°02' Leo", "moon", "18°06' Virgo", "semisextile", True),        # 2°04′ Солнце–Луна
    ("Bill_Gates", "mars", "10°07' Libra", "asc", "26°58' Cancer", "quintile", True),            # 1°09′
    ("George_Clooney", "venus", "13°04' Aries", "saturn", "29°51' Capricorn", "quintile", False),  # 1°13′
    ("Dustin_Hoffman", "moon", "18°06' Virgo", "venus", "4°43' Cancer", "quintile", True),       # 1°23′ со светилом
    ("Steve_Jobs", "moon", "7°45' Aries", "mc", "21°19' Gemini", "quintile", False),             # 1°34′
    ("Serge_Gainsbourg", "uranus", "3°52' Aries", "neptune", "26°43' Leo", "biquintile", True),  # 1°09′
    ("Tom_Hanks", "moon", "9°52' Leo", "mars", "17°20' Pisces", "biquintile", True),             # 1°28′ со светилом
    ("George_Clooney", "moon", "27°58' Capricorn", "pluto", "5°34' Virgo", "biquintile", False),  # 1°36′
    ("Grace_Kelly", "mercury", "10°42' Scorpio", "uranus", "7°57' Aries", "quincunx", True),     # 2°45′
    ("Catherine_Deneuve", "uranus", "8°16' Gemini", "asc", "11°05' Capricorn", "quincunx", False),  # 2°49′
    ("Julia_Roberts", "sun", "4°03' Scorpio", "saturn", "7°09' Aries", "quincunx", True),        # 3°06′ со светилом
    ("Richard_Nixon", "sun", "19°24' Capricorn", "mc", "16°15' Gemini", "quincunx", False),      # 3°09′
]


@pytest.mark.parametrize("case", ASTROTHEME_BOUNDARY, ids=lambda c: f"{c[0]}-{c[1]}-{c[3]}-{c[5]}")
def test_astrotheme_site_minor_orbs_boundary(case):
    name, p1, l1, p2, l2, asp, listed = case
    sep = abs((lon(l1) - lon(l2) + 180.0) % 360.0 - 180.0)
    dev = abs(sep - ASPECTS[asp][0])
    assert (dev <= allowed_orb("astrotheme", asp, p1, p2) + 1e-9) == listed, (name, dev)
    # опубликованная таблица эти случаи не воспроизводит (показанные аспекты шире её орбисов)
    if listed:
        assert dev > allowed_orb("astrotheme_published", asp, p1, p2)


# Раздел «Planets in Houses» тех же страниц Astrotheme (Lilith там — True Lilith, Fortune — Парс Фортуны).
# Сайт пишет под списком: «a planet posited within 1 degree of the next house belongs to that house.
# We allow an orb of 2 degrees for the ASC and the MC». Калькулятор такого сдвига не делает.
ASTROTHEME_HOUSES = {
    "einstein": "sun 10 moon 6 mercury 10 venus 10 mars 7 jupiter 9 saturn 10 uranus 3 neptune 11 pluto 11 "
                "chiron 11 north_node 8 lilith 10 pof 10",
    "monroe": "sun 11 moon 7 mercury 10 venus 9 mars 8 jupiter 7 saturn 4 uranus 8 neptune 1 pluto 12 "
              "chiron 9 north_node 12 lilith 1 pof 9",
    "obama": "sun 6 moon 4 mercury 6 venus 5 mars 7 jupiter 12 saturn 12 uranus 7 neptune 9 pluto 7 "
             "chiron 1 north_node 7 lilith 6 pof 2",
    "elizabeth_ii": "sun 3 moon 7 mercury 2 venus 1 mars 1 jupiter 1 saturn 10 uranus 2 neptune 7 pluto 6 "
                    "chiron 2 north_node 6 lilith 7 pof 8",
}


@pytest.mark.parametrize("key", list(EXTERNAL))
def test_astrotheme_houses_differ_only_by_site_shift_rule(key):
    """Дома планет совпадают с Astrotheme, если применить правило сайта «≤1° до следующего куспида
    (≤2° до ASC/MC) — уже следующий дом». Без сдвига расходятся 5 точек из 56 (Монро: Солнце, Плутон,
    Лилит; Елизавета II: Солнце, Сатурн)."""
    t = ASTROTHEME_HOUSES[key].split()
    theirs = {t[i]: int(t[i + 1]) for i in range(0, len(t), 2)}
    r = calculate(EXTERNAL[key][0], lilith="true")
    cusps = [c["lon"] for c in r["houses"]["cusps"]]
    n_diff = 0
    for p, h in theirs.items():
        src = r["part_of_fortune"] if p == "pof" else r["bodies"][p]
        ours = src["house"]
        nxt = ours % 12 + 1
        limit = 2.0 if nxt in (1, 10) else 1.0
        shifted = nxt if (cusps[nxt - 1] - src["lon"]) % 360 < limit else ours
        assert shifted == h, (key, p, ours, shifted, h)
        n_diff += ours != h
    assert n_diff == {"einstein": 0, "monroe": 3, "obama": 0, "elizabeth_ii": 2}[key]


def test_einstein_t4_details():
    r = calculate(EXTERNAL["einstein"][0])
    assert r["inputs_used"]["offset_source"] == "LMT(longitude)"
    assert r["inputs_used"]["utc"].startswith("1879-03-14T10:50")
    assert r["sect"] == "day"
    assert r["houses"]["system"] == "P"
    assert r["chart_ruler"]["planet"] == "moon"
    assert r["bodies"]["sun"]["house"] == 10 and r["bodies"]["moon"]["house"] == 6
    # Хирон в 11 доме, Вертекс в 5 — как у Astrotheme
    assert r["bodies"]["chiron"]["house"] == 11 and r["angles"]["vertex"]["house"] == 5
    types = {p["type"] for p in r["patterns"]}
    assert "t_square" in types and "stellium_house" in types
    # Сатурн в Овне — падение; Венера в Овне — изгнание
    assert "fall" in r["bodies"]["saturn"]["dignities"]
    assert "detriment" in r["bodies"]["venus"]["dignities"]
    json.dumps(r, ensure_ascii=False)  # результат сериализуем


def test_part_of_fortune_sect_formula():
    # Обама — ночная карта: ASC + Солнце − Луна; дневная формула дала бы ~8°52′ Стрельца
    r = calculate(EXTERNAL["obama"][0])
    assert r["sect"] == "night" and r["part_of_fortune"]["formula"].startswith("ночная")
    r_day = calculate(EXTERNAL["obama"][0], pof="day")
    assert r_day["part_of_fortune"]["sign"] == "Sagittarius"
    # Монро — дневная
    assert calculate(EXTERNAL["monroe"][0])["sect"] == "day"


# ---------------------------------------------------------------------------
# T1–T3 (вычислено; знаки и ключевые точки зафиксированы как регресс)
# ---------------------------------------------------------------------------

def test_t1_moscow_1990_soviet_dst():
    r = calculate(BirthInput(1990, 5, 15, 14, 30, place="Москва"))
    assert r["inputs_used"]["utc_offset"] == "UTC+04:00"
    assert r["inputs_used"]["utc"].startswith("1990-05-15T10:30")
    expect = {"sun": "24°20' Taurus", "moon": "26°23' Capricorn", "mercury": "8°01' Taurus",
              "venus": "12°45' Aries", "mars": "18°17' Pisces", "jupiter": "9°32' Cancer",
              "saturn": "25°15' Capricorn", "uranus": "9°11' Capricorn", "neptune": "14°21' Capricorn",
              "pluto": "16°10' Scorpio"}
    for p, s in expect.items():
        assert arcmin(r["bodies"][p]["lon"], lon(s)) <= 1.0, p
    assert arcmin(r["angles"]["asc"]["lon"], lon("15°23' Virgo")) <= 1.0
    assert arcmin(r["angles"]["mc"]["lon"], lon("9°40' Gemini")) <= 1.0
    assert r["bodies"]["mercury"]["retrograde"]
    assert r["chart_ruler"]["planet"] == "mercury"
    assert r["balance"]["missing_elements"] == ["air"]


def test_t2_moscow_1984_late_evening():
    r = calculate(BirthInput(1984, 2, 4, 23, 30, place="Москва"))
    assert r["inputs_used"]["utc"].startswith("1984-02-04T20:30")
    assert r["bodies"]["sun"]["sign"] == "Aquarius"
    assert r["bodies"]["moon"]["sign"] == "Pisces"
    assert r["angles"]["asc"]["sign"] == "Libra"
    assert arcmin(r["angles"]["asc"]["lon"], lon("19°29' Libra")) <= 1.0
    assert arcmin(r["angles"]["mc"]["lon"], lon("27°15' Cancer")) <= 1.0
    assert r["sect"] == "night"
    assert r["chart_ruler"]["planet"] == "venus"
    stelliums = {tuple(p["members"]) for p in r["patterns"] if p["type"] == "stellium_sign"}
    assert ("mercury", "venus", "jupiter", "neptune") in stelliums


def test_t3_spb_2004_leap_day():
    r = calculate(BirthInput(2004, 2, 29, 8, 15, place="Санкт-Петербург"))
    assert r["inputs_used"]["utc"].startswith("2004-02-29T05:15")
    assert r["bodies"]["sun"]["sign"] == "Pisces"
    assert arcmin(r["bodies"]["sun"]["lon"], lon("9°57' Pisces")) <= 1.0
    assert r["bodies"]["moon"]["sign"] == "Gemini"
    assert arcmin(r["angles"]["asc"]["lon"], lon("19°01' Pisces")) <= 1.0
    assert r["sect"] == "day"  # Солнце только что взошло (12-й дом)
    assert r["bodies"]["sun"]["house"] == 12
    assert set(r["bodies"]["mercury"]["dignities"]) == {"detriment", "fall"}
    # ASC в Рыбах: современный управитель Нептун, традиционный — Юпитер
    assert r["chart_ruler"]["modern"] == "neptune" and r["chart_ruler"]["traditional"] == "jupiter"
    r_trad = calculate(BirthInput(2004, 2, 29, 8, 15, place="Санкт-Петербург"), rulership="traditional")
    assert r_trad["chart_ruler"]["planet"] == "jupiter"


# ---------------------------------------------------------------------------
# Граничные случаи
# ---------------------------------------------------------------------------

def test_polar_latitude_placidus_fallback():
    b = BirthInput(1995, 12, 20, 12, 0, tz="Europe/Moscow", lat=68.9585, lon=33.0827)  # Мурманск
    r = calculate(b)
    assert r["houses"]["requested"] == "P" and r["houses"]["system"] == "O"
    assert any("не определена" in w for w in r["warnings"])
    # полярная ночь: Солнце под горизонтом и в полдень → ночная карта
    assert r["sect"] == "night" and r["sun_altitude"] < 0
    r_e = calculate(b, polar_fallback="E")
    assert r_e["houses"]["system"] == "E"
    # равнодомная: куспиды через 30°
    cusps = [c["lon"] for c in r_e["houses"]["cusps"]]
    assert all(abs(((cusps[(i + 1) % 12] - cusps[i]) % 360) - 30) < 1e-6 for i in range(12))
    # Кох тоже не определён
    assert calculate(b, hsys="K")["houses"]["system"] == "O"
    # на 66.0° Плацидус ещё работает
    assert calculate(BirthInput(1995, 12, 20, 12, 0, tz="Europe/Moscow", lat=66.0, lon=33.0))["houses"]["system"] == "P"


def test_sun_cusp_same_date_different_sign():
    """21.05.1990: Солнце вошло в Близнецы в 07:37 UTC (11:37 MSK, летнее время)."""
    early = calculate(BirthInput(1990, 5, 21, 9, 0, place="Москва"))
    late = calculate(BirthInput(1990, 5, 21, 13, 0, place="Москва"))
    assert early["bodies"]["sun"]["sign"] == "Taurus" and late["bodies"]["sun"]["sign"] == "Gemini"
    assert early["sun_sign"]["near_cusp"] and late["sun_sign"]["near_cusp"]
    assert late["sun_sign"]["entered_utc"].startswith("1990-05-21T07:37")


@pytest.mark.parametrize("year,events", [
    # https://aa.usno.navy.mil/api/seasons?year=1990
    (1990, [(0, "1990-03-20T21:19"), (90, "1990-06-21T15:33"), (180, "1990-09-23T06:56"), (270, "1990-12-22T03:07")]),
    # https://aa.usno.navy.mil/api/seasons?year=2000
    (2000, [(0, "2000-03-20T07:35"), (90, "2000-06-21T01:48"), (180, "2000-09-22T17:28"), (270, "2000-12-21T13:37")]),
    # https://aa.usno.navy.mil/api/seasons?year=2024
    (2024, [(0, "2024-03-20T03:06"), (90, "2024-06-20T20:51"), (180, "2024-09-22T12:44"), (270, "2024-12-21T09:20")]),
])
def test_sun_ingress_matches_usno(year, events):
    from datetime import datetime, timezone
    from calculators.common.time import julian_day_ut
    for deg, iso in events:
        t = datetime.fromisoformat(iso).replace(tzinfo=timezone.utc)
        jd = eph.find_sun_longitude(deg, julian_day_ut(t) + 2, search_back=True)
        assert abs(jd - julian_day_ut(t)) * 1440 <= 1.0, (year, deg)


def test_unknown_time():
    r = calculate(BirthInput(1990, 5, 21, place="Москва"))
    assert r["time_known"] is False
    assert r["houses"] is None and r["angles"] == {} and r["part_of_fortune"] is None
    assert any("Солнце: Телец → Близнецы" in w for w in r["warnings"])
    assert "moon_range" in r["sun_sign"]
    assert not any(a["p1"] in ("asc", "mc") or a["p2"] in ("asc", "mc") for a in r["aspects"])
    # знак Солнца «по полудню» (Близнецы) нельзя выдавать как ответ: в этот день была ингрессия
    assert r["sun_sign"]["possible_signs_ru"] == ["Телец", "Близнецы"]
    assert [c["body"] for c in r["sun_sign"]["sign_changes_during_day"]] == ["sun"]
    # Луна весь день в Овне — знак однозначен
    assert all(x.endswith("Овен") for x in r["sun_sign"]["moon_range"])
    r2 = calculate(BirthInput(1990, 5, 15, place="Москва"))
    assert r2["sun_sign"]["possible_signs_ru"] == ["Телец"]


def test_mean_vs_true_node_and_lilith():
    b = EXTERNAL["einstein"][0]
    r_true = calculate(b)
    r_mean = calculate(b, node="mean", lilith="true")
    # средний узел всегда ретрограден
    assert r_mean["bodies"]["north_node"]["retrograde"]
    assert arcmin(r_true["bodies"]["north_node"]["lon"], r_mean["bodies"]["north_node"]["lon"]) < 2 * 60
    # истинная (оскулирующая) Лилит Эйнштейна = 1°37′ Овна (Astrotheme, True Lilith)
    assert arcmin(r_mean["bodies"]["lilith"]["lon"], lon("1°37' Aries")) <= 1.0
    # южный узел строго напротив
    assert abs(((r_true["bodies"]["south_node"]["lon"] - r_true["bodies"]["north_node"]["lon"]) % 360) - 180) < 1e-9


# ---------------------------------------------------------------------------
# Ручные формулы и инварианты
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("key", list(EXTERNAL))
def test_manual_formulas_agree_with_swiss_ephemeris(key):
    b = EXTERNAL[key][0]
    r = calculate(b)
    jd = r["inputs_used"]["jd_ut"]
    ramc = (gmst_hours_usno(jd) + b.lon / 15) % 24 * 15
    eps = mean_obliquity(jd)
    assert arcmin(asc_from_ramc(ramc, eps, b.lat), r["angles"]["asc"]["lon"]) < 1.5
    assert arcmin(mc_from_ramc(ramc, eps), r["angles"]["mc"]["lon"]) < 1.5
    assert arcmin(sun_lon_low_precision(jd), r["bodies"]["sun"]["lon"]) < 1.0
    assert arcmin(moon_lon_low_precision(jd), r["bodies"]["moon"]["lon"]) < 0.5 * 60


def test_sign_rising_times_moscow():
    rh = sign_rising_hours(55.7558)
    assert abs(sum(rh) - 23.934) < 0.01          # сутки звёздные
    assert rh[0] < 0.75 and rh[11] < 0.75        # Овен и Рыбы восходят < 45 мин
    assert rh[5] > 2.9 and rh[6] > 2.9           # Дева и Весы ~3 ч
    assert all(abs(rh[i] - rh[11 - i]) < 1e-9 for i in range(12))  # симметрия Овен↔Рыбы и т.д.


def test_invariants():
    r = calculate(BirthInput(1990, 5, 15, 14, 30, place="Москва"))
    asc, mc = r["angles"]["asc"]["lon"], r["angles"]["mc"]["lon"]
    cusps = [c["lon"] for c in r["houses"]["cusps"]]
    assert abs(cusps[0] - asc) < 1e-6 and abs(cusps[9] - mc) < 1e-6
    for i in range(6):  # противоположные куспиды
        assert arcmin(cusps[i] + 180, cusps[i + 6]) < 1e-3
    for name, body in r["bodies"].items():
        assert 1 <= body["house"] <= 12
        assert body["house"] == house_of(body["lon"], cusps)
    assert sum(r["balance"]["elements"].values()) == 10
    for a in r["aspects"]:
        assert a["orb"] <= a["orb_allowed"] + 1e-9
        assert abs(a["separation"] - ASPECTS[a["aspect"]][0]) - a["orb"] < 1e-3


def test_aspect_phase_applying_separating():
    # Быстрая планета позади медленной на 5° → сходящееся соединение
    pts = {"moon": {"lon": 10.0, "speed": 13.0, "sign_index": 0},
           "saturn": {"lon": 15.0, "speed": 0.1, "sign_index": 0}}
    a = find_aspects(pts, "astrotheme")[0]
    assert a["aspect"] == "conjunction" and a["phase"] == "applying"
    pts["moon"]["lon"] = 20.0
    assert find_aspects(pts, "astrotheme")[0]["phase"] == "separating"
    # оппозиция: расстояние 176° и растёт → сходящаяся
    pts = {"moon": {"lon": 0.0, "speed": 13.0, "sign_index": 0},
           "saturn": {"lon": 184.0, "speed": 0.0, "sign_index": 6}}
    a = find_aspects(pts, "astrotheme")[0]
    assert a["aspect"] == "opposition" and a["phase"] == "applying"


def test_orb_schemes():
    assert allowed_orb("astrotheme", "conjunction", "sun", "moon") == pytest.approx(11.1)
    # фактические минорные орбисы сайта (88 карт) и опубликованная таблица
    assert allowed_orb("astrotheme", "semisextile", "mars", "jupiter") == pytest.approx(1.5)
    assert allowed_orb("astrotheme", "semisextile", "moon", "mars") == pytest.approx(1.8)
    assert allowed_orb("astrotheme", "quincunx", "mars", "saturn") == pytest.approx(2.8)
    assert allowed_orb("astrotheme", "quintile", "mars", "saturn") == pytest.approx(1.2)
    assert allowed_orb("astrotheme", "biquintile", "mars", "saturn") == pytest.approx(1.2)
    assert allowed_orb("astrotheme_published", "semisextile", "mars", "jupiter") == pytest.approx(1.0)
    assert allowed_orb("astrotheme_published", "quincunx", "sun", "saturn") == pytest.approx(3.0)
    assert allowed_orb("astrotheme", "trine", "sun", "mars") == pytest.approx(8.6)
    assert allowed_orb("astrotheme", "square", "north_node", "mars") == pytest.approx(3.0)
    assert allowed_orb("astrolog", "conjunction", "sun", "moon") == pytest.approx(9.0)
    assert allowed_orb("moiety", "conjunction", "sun", "moon") == pytest.approx(13.5)  # (15+12)/2
    assert allowed_orb("moiety", "trine", "mars", "jupiter") == pytest.approx(8.0)       # (7+9)/2, пример Skyscript
    assert allowed_orb("moiety", "quintile", "mars", "jupiter") is None
    assert allowed_orb("ru_points", "conjunction", "sun", "mars") == pytest.approx(9.0)  # (10+8)/2
    assert allowed_orb("ru_points", "trine", "moon", "pluto") == pytest.approx(7.0)
    for scheme in ("astrolog", "moiety", "ru_points"):
        r = calculate(EXTERNAL["einstein"][0], orbs=scheme)
        assert all(a["orb"] <= a["orb_allowed"] + 1e-9 for a in r["aspects"])


@pytest.mark.parametrize("hsys", ["P", "K", "E", "W", "O", "R", "C", "T", "B"])
def test_all_house_systems_run(hsys):
    r = calculate(EXTERNAL["einstein"][0], hsys=hsys)
    assert r["houses"]["system"] == hsys
    if hsys == "W":
        assert all(abs(c["lon"] % 30) < 1e-6 for c in r["houses"]["cusps"])
        assert r["houses"]["cusps"][0]["sign"] == "Cancer"
    if hsys in ("P", "K", "O", "R", "C", "T", "B"):
        assert arcmin(r["houses"]["cusps"][0]["lon"], r["angles"]["asc"]["lon"]) < 1e-3


def test_grand_trine_and_yod_detection():
    from calculators.western import find_patterns
    def body(lon_):
        s = int(lon_ // 30)
        return {"lon": lon_, "speed": 1.0, "sign_index": s,
                "element": ["fire", "earth", "air", "water"][s % 4],
                "modality": ["cardinal", "fixed", "mutable"][s % 3]}
    names = ["sun", "moon", "mercury", "venus", "mars", "jupiter", "saturn", "uranus", "neptune", "pluto"]
    lons = [5, 125, 245, 65, 300, 310, 320, 330, 340, 350]  # Солнце/Луна/Меркурий — Большой тригон в Огне
    bodies = {n: body(l) for n, l in zip(names, lons)}
    asp = find_aspects(bodies, "astrotheme")
    pats = find_patterns(asp, bodies, names, None)
    gt = [p for p in pats if p["type"] == "grand_trine"]
    assert gt and set(gt[0]["members"]) == {"sun", "moon", "mercury"} and gt[0]["element"] == "fire"
    kite = [p for p in pats if p["type"] == "kite"]  # Венера 65° — оппозиция Меркурию, секстили Солнцу и Луне
    assert kite and kite[0]["apex"] == "venus"
    # Йод: Солнце 0°, Луна 60° (секстиль), Марс 210° (квинконс обоим)
    lons = [0, 60, 100, 103, 210, 250, 280, 285, 288, 291]
    bodies = {n: body(l) for n, l in zip(names, lons)}
    pats = find_patterns(find_aspects(bodies, "astrotheme"), bodies, names, None)
    yod = [p for p in pats if p["type"] == "yod"]
    assert yod and yod[0]["apex"] == "mars"


def test_manual_asc_polar_eastern_rule():
    """За полярным кругом формула ASC может дать Десцендент; правило (ASC−MC) mod 360 < 180 исправляет."""
    b = BirthInput(1995, 12, 20, 12, 0, tz="Europe/Moscow", lat=68.9585, lon=33.0827)
    r = calculate(b)
    jd = r["inputs_used"]["jd_ut"]
    ramc = (gmst_hours_usno(jd) + b.lon / 15) % 24 * 15
    assert arcmin(asc_from_ramc(ramc, mean_obliquity(jd), b.lat), r["angles"]["asc"]["lon"]) < 2.0
    assert r["angles"]["asc"]["sign"] == "Taurus"


# ---------------------------------------------------------------------------
# Регрессии по итогам проверки (волна 2)
# ---------------------------------------------------------------------------

def test_rounded_position_never_leaves_sign():
    """21.05.1990 11:36 MSK: Солнце 29°59′56″ Тельца. Округление до минуты не должно давать
    «0°00′ Близнецы» в summary/pos_rounded, иначе подпись знака противоречит полю sign."""
    from calculators.western import dm_rounded, dms
    r = calculate(BirthInput(1990, 5, 21, 11, 36, place="Москва"))
    sun = r["bodies"]["sun"]
    assert sun["sign"] == "Taurus" and sun["pos"].startswith("29°59′")
    assert sun["pos_rounded"] == "29°59′ Телец" and r["summary"]["sun"] == "Солнце 29°59′ Телец"
    assert dm_rounded(59.9999) == "29°59′ Телец" and dm_rounded(59.991) == "29°59′ Телец"
    assert dm_rounded(29.9916) == "29°59′ Овен" and dm_rounded(14.5419) == "14°33′ Овен"
    assert dm_rounded(359.99999) == "29°59′ Рыбы" and dm_rounded(360.0) == "0°00′ Овен"
    assert dms(59.99999999999999) == "29°59′59″ Телец"
    for lon_ in (0.0, 29.99, 30.0, 89.999, 359.9999):  # подпись знака всегда совпадает с sign_index
        assert dm_rounded(lon_).endswith(eph.SIGNS_RU[int(lon_ // 30)])


def test_astrolog_orbs_cap_nodes_at_2_degrees():
    """Astrolog general.cpp GetOrb: min(rAspOrb, rObjOrb₁, rObjOrb₂) + rObjAdd; rObjOrb узла = 2°
    (https://github.com/CruiserOne/Astrolog/blob/master/data.cpp)."""
    assert allowed_orb("astrolog", "square", "mars", "north_node") == pytest.approx(2.0)
    assert allowed_orb("astrolog", "conjunction", "sun", "north_node") == pytest.approx(3.0)  # 2 + 1 за Солнце
    assert allowed_orb("astrolog", "quintile", "venus", "north_node") == pytest.approx(2.0)
    assert allowed_orb("astrolog", "trine", "mars", "chiron") == pytest.approx(7.0)  # у Хирона ограничения нет
    assert allowed_orb("astrolog", "trine", "mars", "lilith") == pytest.approx(7.0)


def test_dates_outside_asteroid_file_skip_chiron():
    """В calculators/ephe только seas_18.se1 (1800–2399): Хирон для 1750 г. не считается,
    но карта строится (планеты — по аналитической теории Moshier) и выдаётся предупреждение."""
    r = calculate(BirthInput(1750, 6, 1, 12, 0, tz="UTC", lat=50.0, lon=10.0))
    assert "chiron" not in r["bodies"]
    assert any("Хирон не вычислен" in w for w in r["warnings"])
    assert not any("chiron" in (a["p1"], a["p2"]) for a in r["aspects"])
    assert r["bodies"]["sun"]["sign"] == "Gemini"


def test_manual_vertex_western_rule_matches_swiss_ephemeris():
    """Ручной Вертекс (§3.2 п. 7) с правилом «западная половина» совпадает с SE; в тропиках
    без этого правила формула иногда даёт Антивертекс (+180°)."""
    import random
    import swisseph as swe
    from calculators.western import vertex_from_ramc
    rnd = random.Random(7)
    flipped = 0
    for _ in range(600):
        jd = 2451545.0 + rnd.uniform(-36500, 36500)
        lat_, lon_ = rnd.uniform(-23.0, 23.0), rnd.uniform(-180, 180)
        h = eph.houses(jd, lat_, lon_, "P")
        eps_true = swe.calc_ut(jd, swe.ECL_NUT)[0][0]
        vx = vertex_from_ramc(h["armc"], eps_true, lat_)
        assert arcmin(vx, h["vertex"]) < 1 / 60, (jd, lat_, lon_)
        r_, e_, f_ = math.radians(h["armc"] + 180), math.radians(eps_true), math.radians(90 - lat_)
        raw = math.degrees(math.atan2(math.cos(r_), -(math.sin(r_) * math.cos(e_) + math.tan(f_) * math.sin(e_)))) % 360
        flipped += arcmin(raw, h["vertex"]) > 60
    assert flipped > 0  # правило действительно нужно


def test_t1_direct_pyswisseph():
    """T1 пересчитан напрямую через pyswisseph (без calculate): UTC 10:30, Плацидус."""
    import swisseph as swe
    jd = swe.julday(1990, 5, 15, 10.5)
    r = calculate(BirthInput(1990, 5, 15, 14, 30, place="Москва"))
    assert abs(r["inputs_used"]["jd_ut"] - jd) < 1e-6
    for name, code in (("sun", swe.SUN), ("moon", swe.MOON)):
        assert arcmin(swe.calc_ut(jd, code, swe.FLG_SWIEPH)[0][0], r["bodies"][name]["lon"]) < 1e-3
    _c, ascmc = swe.houses_ex(jd, 55.7558, 37.6173, b"P")
    assert arcmin(ascmc[0], r["angles"]["asc"]["lon"]) < 1e-3 and arcmin(ascmc[1], r["angles"]["mc"]["lon"]) < 1e-3
