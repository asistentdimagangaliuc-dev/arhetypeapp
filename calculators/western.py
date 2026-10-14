"""Западная (тропическая) астрология: натальная карта.

Конвейер: местное время → UTC → юлианский день (UT) → долготы тел (Swiss Ephemeris,
через common.ephemeris) → ASC/MC и куспиды домов → дома планет, аспекты,
конфигурации, достоинства, баланс стихий/крестов, управители, Парс Фортуны.

Значения по умолчанию (обоснование в knowledge-base/06-western-astrology.md):
* дома — Плацидус (P); выше полярного круга Плацидус и Кох не определены, и
  калькулятор переходит на Порфирия (O), как это делает Swiss Ephemeris;
* узел — истинный (true); Лилит — средняя (mean, «Чёрная Луна»);
* орбисы — таблица Astrotheme для натальных карт (опубликована и сверена);
* Парс Фортуны — формула с учётом секты: днём ASC+Луна−Солнце, ночью ASC+Солнце−Луна;
* управители — современные (Плутон/Уран/Нептун), традиционные выдаются как коуправители.

Пример:
    from calculators.common.time import BirthInput
    from calculators.western import calculate
    r = calculate(BirthInput(1879, 3, 14, 11, 30, tz="LMT", lat=48.4011, lon=9.9876))
"""
from __future__ import annotations

import math
from dataclasses import replace
from datetime import datetime, timedelta, timezone

import swisseph as swe

from .common import ephemeris as eph
from .common.time import BirthInput, fmt_offset, jd_to_utc, normalize

# ---------------------------------------------------------------------------
# Справочные данные
# ---------------------------------------------------------------------------

SIGNS_RU = eph.SIGNS_RU
SIGNS_EN = eph.SIGNS_EN
# предложный падеж: «в Овне», «в Тельце» …
SIGNS_RU_PREP = ["Овне", "Тельце", "Близнецах", "Раке", "Льве", "Деве",
                 "Весах", "Скорпионе", "Стрельце", "Козероге", "Водолее", "Рыбах"]
ELEMENTS = ["fire", "earth", "air", "water"] * 3          # по индексу знака
MODALITIES = ["cardinal", "fixed", "mutable"] * 4
POLARITY = ["masculine", "feminine"] * 6
ELEMENT_RU = {"fire": "Огонь", "earth": "Земля", "air": "Воздух", "water": "Вода"}
MODALITY_RU = {"cardinal": "кардинальный", "fixed": "фиксированный", "mutable": "мутабельный"}
POLARITY_RU = {"masculine": "мужской (ян)", "feminine": "женский (инь)"}

BODY_RU = {
    "sun": "Солнце", "moon": "Луна", "mercury": "Меркурий", "venus": "Венера", "mars": "Марс",
    "jupiter": "Юпитер", "saturn": "Сатурн", "uranus": "Уран", "neptune": "Нептун", "pluto": "Плутон",
    "north_node": "Северный узел (Раху)", "south_node": "Южный узел (Кету)",
    "lilith": "Лилит (Чёрная Луна)", "chiron": "Хирон", "asc": "Асцендент", "mc": "MC",
    "part_of_fortune": "Парс Фортуны", "vertex": "Вертекс",
}
PLANETS10 = ["sun", "moon", "mercury", "venus", "mars", "jupiter", "saturn", "uranus", "neptune", "pluto"]
CLASSICAL7 = PLANETS10[:7]

# Управители знаков. Индекс = номер знака (0 = Овен).
RULER_TRADITIONAL = ["mars", "venus", "mercury", "moon", "sun", "mercury",
                     "venus", "mars", "jupiter", "saturn", "saturn", "jupiter"]
RULER_MODERN = ["mars", "venus", "mercury", "moon", "sun", "mercury",
                "venus", "pluto", "jupiter", "saturn", "uranus", "neptune"]

# Эссенциальные достоинства (Птолемей; для высших планет — современная школа).
# Номера знаков: 0 Овен … 11 Рыбы.
DOMICILE = {
    "sun": [4], "moon": [3], "mercury": [2, 5], "venus": [1, 6], "mars": [0, 7],
    "jupiter": [8, 11], "saturn": [9, 10], "uranus": [10], "neptune": [11], "pluto": [7],
}
DETRIMENT = {p: [(s + 6) % 12 for s in signs] for p, signs in DOMICILE.items()}
EXALTATION = {"sun": (0, 19), "moon": (1, 3), "mercury": (5, 15), "venus": (11, 27),
              "mars": (9, 28), "jupiter": (3, 15), "saturn": (6, 21)}
# Экзальтации высших планет спорны; ниже — вариант программы Astrolog (data.cpp, массив exalt).
EXALTATION_OUTER_ASTROLOG = {"uranus": 7, "neptune": 3, "pluto": 10}
FALL = {p: (s + 6) % 12 for p, (s, _deg) in EXALTATION.items()}

# Аспекты: ключ → (угол, русское название, мажорный?, расстояние в знаках для «своего» аспекта)
ASPECTS: dict[str, tuple[float, str, bool, int | None]] = {
    "conjunction":   (0.0,   "соединение",       True,  0),
    "opposition":    (180.0, "оппозиция",        True,  6),
    "trine":         (120.0, "тригон (трин)",    True,  4),
    "square":        (90.0,  "квадрат",          True,  3),
    "sextile":       (60.0,  "секстиль",         True,  2),
    "quincunx":      (150.0, "квинконс (квиконс)", False, 5),
    "semisextile":   (30.0,  "полусекстиль",     False, 1),
    "semisquare":    (45.0,  "полуквадрат",      False, None),
    "sesquisquare":  (135.0, "полутораквадрат (сесквиквадрат)", False, None),
    "quintile":      (72.0,  "квинтиль",         False, None),
    "biquintile":    (144.0, "биквинтиль",       False, None),
}
MAJOR = [k for k, v in ASPECTS.items() if v[2]]

# Схемы орбисов ------------------------------------------------------------
# astrotheme (по умолчанию) — орбисы, которые сайт Astrotheme ФАКТИЧЕСКИ применяет в картах знаменитостей.
#   Правило со страницы https://www.astrotheme.com/astrology_aspects.php: орбис по аспекту + 0,3° если
#   участвует Солнце или Луна, + 0,6° для пары Солнце–Луна; для узлов и Лилит орбис ограничен 3°.
#   Базовые орбисы мажорных аспектов, полуквадрата и полутораквадрата — как в опубликованной таблице;
#   квинконс 2,8 (опубл. 2,7), полусекстиль 1,5 (опубл. 1,0), квинтиль и биквинтиль 1,2 (опубл. 0,8)
#   восстановлены по 88 картам https://www.astrotheme.com/astrology/<Имя> (2802 аспекта, повторная проверка
#   14.10.2026): с этими значениями 0 пропущенных аспектов и 11 «лишних» — все в пределах 1′ от границы
#   (округление позиций сайта), с опубликованными — 82 пропущенных. Сводка — 06-western-astrology.md §4.4(а).
# astrotheme_published — опубликованная таблица той же страницы без поправок (умолчание до 14.10.2026).
# astrolog: https://github.com/CruiserOne/Astrolog/blob/master/data.cpp (rAspOrb, rObjAdd)
#   + general.cpp GetOrb(): min(орбис аспекта, rObjOrb каждого объекта) + добавка Солнца (1°) + Луны (1°).
#   rObjOrb = 2° у узлов (oNod, oSou) и Вертекса, у остальных объектов 360° (без ограничения).
# moiety: традиционные «половины орбисов» (moieties) по Лилли, стандартный список Skyscript
#   https://www.skyscript.co.uk/aspectorbs.html: допустимо (orbA + orbB) / 2, только птолемеевы аспекты.
# ru_points: «баллы» планет по astromaya.ru (рус. школа):
#   https://astromaya.ru/astroschool/postroenie-goroskopa/hand1/aspectcalculation
ORB_SCHEMES: dict[str, dict] = {
    "astrotheme": {
        "base": {"conjunction": 10.5, "opposition": 10.0, "trine": 8.3, "square": 7.8, "sextile": 6.1,
                 "quincunx": 2.8, "sesquisquare": 2.5, "semisquare": 1.5, "semisextile": 1.5,
                 "quintile": 1.2, "biquintile": 1.2},
        "luminary_add": 0.3, "sun_moon_add": 0.6, "point_cap": 3.0,
    },
    "astrotheme_published": {
        "base": {"conjunction": 10.5, "opposition": 10.0, "trine": 8.3, "square": 7.8, "sextile": 6.1,
                 "quincunx": 2.7, "sesquisquare": 2.5, "semisquare": 1.5, "semisextile": 1.0,
                 "quintile": 0.8, "biquintile": 0.8},
        "luminary_add": 0.3, "sun_moon_add": 0.6, "point_cap": 3.0,
    },
    "astrolog": {
        "base": {"conjunction": 7.0, "opposition": 7.0, "square": 7.0, "trine": 7.0, "sextile": 6.0,
                 "quincunx": 3.0, "semisextile": 3.0, "semisquare": 3.0, "sesquisquare": 3.0,
                 "quintile": 2.0, "biquintile": 2.0},
        "add": {"sun": 1.0, "moon": 1.0},
        "obj_cap": {"north_node": 2.0, "south_node": 2.0, "vertex": 2.0},
    },
    "moiety": {
        "orb": {"sun": 15.0, "moon": 12.0, "mercury": 7.0, "venus": 7.0, "mars": 7.0,
                "jupiter": 9.0, "saturn": 9.0},
        "default_orb": 5.0,   # высшие планеты, углы и прочие точки (Skyscript: 5°)
        "aspects": MAJOR,
    },
    "ru_points": {
        "points": {"sun": 10, "moon": 10, "mercury": 8, "venus": 8, "mars": 8,
                   "jupiter": 6, "saturn": 6, "chiron": 6, "uranus": 4, "neptune": 4, "pluto": 4},
        "node_angle_orb": 4.0,
        "fixed": {"sextile": 5.0, "trine": 5.0, "square": 5.0, "semisquare": 1.5, "sesquisquare": 1.5},
        "trine_luminary": 7.0,
        "aspects": ["conjunction", "opposition", "trine", "square", "sextile", "semisquare", "sesquisquare"],
    },
}

# Swiss Ephemeris, документация §2.3.4: Хирон надёжно считается в 700–4650 гг. н.э.
# (сближение с Сатурном в 720 г.). 1 января 700 г. по юлианскому календарю:
CHIRON_RELIABLE_FROM_JD = 1976732.5

HOUSE_SYSTEMS = {"P": "Плацидус (Placidus)", "K": "Кох (Koch)", "E": "Равнодомная от ASC (Equal)",
                 "W": "Целые знаки (Whole Sign)", "O": "Порфирий (Porphyry)",
                 "R": "Региомонтан (Regiomontanus)", "C": "Кампанус (Campanus)",
                 "T": "Топоцентрическая (Polich-Page)", "B": "Алькабитий (Alcabitius)"}

# Веса для баланса стихий/крестов/полярностей
BALANCE_WEIGHTS = {
    # по 1 баллу каждой из 10 планет
    "equal": {p: 1.0 for p in PLANETS10},
    # «внутренняя сила» объектов из Astrolog (data.cpp, rObjInf): Солнце 30, Луна 25, остальные 10,
    # ASC 20, MC 15. Применение этих весов к стихиям — решение этого калькулятора.
    "astrolog": {"sun": 30.0, "moon": 25.0, **{p: 10.0 for p in PLANETS10[2:]}, "asc": 20.0, "mc": 15.0},
}


# ---------------------------------------------------------------------------
# Вспомогательные функции
# ---------------------------------------------------------------------------

def norm360(x: float) -> float:
    return x % 360.0


def signed_diff(a: float, b: float) -> float:
    """b − a, приведённое к (−180, 180]."""
    d = (b - a) % 360.0
    return d - 360.0 if d > 180.0 else d


def dms(lon: float, with_sign: bool = True, seconds: bool = True) -> str:
    """Долгота в виде «23°30′28″ Рыбы» (минуты и секунды усечены, не округлены)."""
    lon = norm360(lon)
    s = int(lon // 30)
    x = lon - 30 * s
    # усечение; эпсилон гасит ошибку плавающей точки, а min() не даёт получить «30°00′00″»
    total = min(int(x * 3600 + 1e-7), 30 * 3600 - 1)
    d, rem = divmod(total, 3600)
    m, sec = divmod(rem, 60)
    body = f"{d}°{m:02d}′{sec:02d}″" if seconds else f"{d}°{m:02d}′"
    return f"{body} {SIGNS_RU[s]}" if with_sign else body


def dm_rounded(lon: float) -> str:
    """Долгота с округлением до минуты (как печатают большинство сайтов), но без выхода за знак.

    Общий common.ephemeris.format_lon переносит 29°59,5′+ в «0°00′ следующего знака».
    Здесь знак — самостоятельный результат (знак Солнца, управитель куспида), поэтому подпись
    должна совпадать с полем sign: 29°59′56″ Тельца печатается как «29°59′ Телец»."""
    lon = norm360(lon)
    s = int(lon // 30)
    total = min(int(round((lon - 30 * s) * 60)), 30 * 60 - 1)
    d, m = divmod(total, 60)
    return f"{d}°{m:02d}′ {SIGNS_RU[s]}"


def fmt_orb(x: float) -> str:
    total = int(round(abs(x) * 60))
    return f"{total // 60}°{total % 60:02d}′"


def sign_index(lon: float) -> int:
    return int(norm360(lon) // 30)


def _point(name: str, lon: float, speed: float | None = None, lat: float | None = None) -> dict:
    s = sign_index(lon)
    out = {
        "name": name, "name_ru": BODY_RU.get(name, name),
        "lon": round(norm360(lon), 6), "sign_index": s, "sign": SIGNS_EN[s], "sign_ru": SIGNS_RU[s],
        "deg_in_sign": round(norm360(lon) - 30 * s, 6), "pos": dms(lon), "pos_rounded": dm_rounded(lon),
        "element": ELEMENTS[s], "modality": MODALITIES[s], "polarity": POLARITY[s],
    }
    if speed is not None:
        out["speed"] = round(speed, 6)
        out["retrograde"] = speed < 0
    if lat is not None:
        out["lat"] = round(lat, 6)
    return out


def dignities_of(planet: str, s: int, outer_exaltations: bool = False) -> list[str]:
    """Эссенциальные достоинства планеты в знаке s."""
    res: list[str] = []
    if s in DOMICILE.get(planet, []):
        res.append("domicile")
    if planet in EXALTATION and EXALTATION[planet][0] == s:
        res.append("exaltation")
    if s in DETRIMENT.get(planet, []):
        res.append("detriment")
    if planet in FALL and FALL[planet] == s:
        res.append("fall")
    if outer_exaltations and planet in EXALTATION_OUTER_ASTROLOG:
        ex = EXALTATION_OUTER_ASTROLOG[planet]
        if ex == s:
            res.append("exaltation")
        elif (ex + 6) % 12 == s:
            res.append("fall")
    return res


DIGNITY_RU = {"domicile": "обитель", "exaltation": "экзальтация", "detriment": "изгнание", "fall": "падение"}


def house_of(lon: float, cusps: list[float]) -> int:
    """Номер дома (1..12) по эклиптической долготе между куспидами."""
    lon = norm360(lon)
    for i in range(12):
        a, b = cusps[i], cusps[(i + 1) % 12]
        width = (b - a) % 360.0
        if (lon - a) % 360.0 < width:
            return i + 1
    return 12  # недостижимо при корректных куспидах


# ---------------------------------------------------------------------------
# Ручные (приближённые) формулы — для самопроверки и для объяснения агенту
# ---------------------------------------------------------------------------

def gmst_hours_usno(jd_ut: float) -> float:
    """Гринвичское среднее звёздное время, ч (USNO, https://aa.usno.navy.mil/faq/GAST)."""
    jd0 = math.floor(jd_ut - 0.5) + 0.5
    h = (jd_ut - jd0) * 24.0
    d_ut = jd0 - 2451545.0
    t = (jd_ut - 2451545.0) / 36525.0
    return (6.697375 + 0.065709824279 * d_ut + 1.0027379 * h + 0.0000258 * t * t) % 24.0


def mean_obliquity(jd_ut: float) -> float:
    t = (jd_ut - 2451545.0) / 36525.0
    return 23.4392911 - 0.0130041667 * t


def mc_from_ramc(ramc: float, eps: float) -> float:
    r, e = math.radians(ramc), math.radians(eps)
    return norm360(math.degrees(math.atan2(math.sin(r), math.cos(r) * math.cos(e))))


def asc_from_ramc(ramc: float, eps: float, lat: float) -> float:
    """ASC по RAMC. Последняя строка — правило «ASC в восточной половине неба»:
    (ASC − MC) mod 360 ∈ (0°, 180°). На обычных широтах оно выполняется само,
    за полярным кругом формула может дать Десцендент, и тогда прибавляем 180°
    (так же поступает Swiss Ephemeris)."""
    r, e, f = math.radians(ramc), math.radians(eps), math.radians(lat)
    asc = norm360(math.degrees(math.atan2(math.cos(r), -(math.sin(r) * math.cos(e) + math.tan(f) * math.sin(e)))))
    if (asc - mc_from_ramc(ramc, eps)) % 360.0 > 180.0:
        asc = norm360(asc + 180.0)
    return asc


def vertex_from_ramc(ramc: float, eps: float, lat: float) -> float:
    """Вертекс: формула ASC с RAMC + 180° и широтой 90° − φ, затем правило «Вертекс в западной
    половине»: (Vx − MC) mod 360 ∈ [180°, 360°). В тропиках (|φ| < ε) сырая формула иногда даёт
    Антивертекс, и тогда прибавляем 180° (так делает Swiss Ephemeris, документация §6.4)."""
    r, e, f = math.radians(ramc + 180.0), math.radians(eps), math.radians(90.0 - lat)
    vx = norm360(math.degrees(math.atan2(math.cos(r), -(math.sin(r) * math.cos(e) + math.tan(f) * math.sin(e)))))
    if (vx - mc_from_ramc(ramc, eps)) % 360.0 < 180.0:
        vx = norm360(vx + 180.0)
    return vx


def sun_lon_low_precision(jd_ut: float) -> float:
    """Видимая долгота Солнца, точность ~0,01° (Meeus, Astronomical Algorithms, гл. 25)."""
    t = (jd_ut - 2451545.0) / 36525.0
    l0 = 280.46646 + 36000.76983 * t + 0.0003032 * t * t
    m = math.radians(357.52911 + 35999.05029 * t - 0.0001537 * t * t)
    c = ((1.914602 - 0.004817 * t - 0.000014 * t * t) * math.sin(m)
         + (0.019993 - 0.000101 * t) * math.sin(2 * m) + 0.000289 * math.sin(3 * m))
    omega = math.radians(125.04 - 1934.136 * t)
    return norm360(l0 + c - 0.00569 - 0.00478 * math.sin(omega))


def moon_lon_low_precision(jd_ut: float) -> float:
    """Долгота Луны по 6 главным членам теории (Meeus, гл. 47), точность ~0,3°."""
    t = (jd_ut - 2451545.0) / 36525.0
    lp = 218.3164477 + 481267.88123421 * t
    d = math.radians(297.8501921 + 445267.1114034 * t)
    m = math.radians(357.5291092 + 35999.0502909 * t)
    mp = math.radians(134.9633964 + 477198.8675055 * t)
    f = math.radians(93.2720950 + 483202.0175233 * t)
    return norm360(lp + 6.288774 * math.sin(mp) + 1.274027 * math.sin(2 * d - mp)
                   + 0.658314 * math.sin(2 * d) + 0.213618 * math.sin(2 * mp)
                   - 0.185116 * math.sin(m) - 0.114332 * math.sin(2 * f))


def sign_rising_hours(lat: float, eps: float = 23.4393) -> list[float]:
    """Сколько солнечных часов восходит каждый знак на широте lat (косые восхождения)."""
    def oblique_asc(lam: float) -> float:
        lr, er, fr = math.radians(lam), math.radians(eps), math.radians(lat)
        ra = math.degrees(math.atan2(math.sin(lr) * math.cos(er), math.cos(lr))) % 360.0
        dec = math.asin(math.sin(er) * math.sin(lr))
        ad = math.degrees(math.asin(max(-1.0, min(1.0, math.tan(dec) * math.tan(fr)))))
        return ra - ad
    out = []
    for s in range(12):
        a, b = oblique_asc(30.0 * s), oblique_asc(30.0 * s + 30.0)
        out.append(((b - a) % 360.0) / 15.0 * 0.9972696)
    return out


# ---------------------------------------------------------------------------
# Дома
# ---------------------------------------------------------------------------

def compute_houses(jd_ut: float, lat: float, lon: float, hsys: str = "P",
                   polar_fallback: str = "O") -> tuple[dict, list[str]]:
    """Куспиды и углы. Если система не определена (Плацидус/Кох за полярным кругом) —
    переход на polar_fallback с предупреждением."""
    warnings: list[str] = []
    used = hsys
    try:
        h = eph.houses(jd_ut, lat, lon, hsys)
    except swe.Error:
        used = polar_fallback
        h = eph.houses(jd_ut, lat, lon, polar_fallback)
        warnings.append(
            f"Система домов {HOUSE_SYSTEMS.get(hsys, hsys)} не определена на широте {lat:.4f}° "
            f"(за полярным кругом, |φ| > 90° − ε ≈ 66°33′): использована {HOUSE_SYSTEMS.get(used, used)}."
        )
    h["system"] = used
    return h, warnings


def altitude(jd_ut: float, lat: float, lon: float, ecl_lon: float, ecl_lat: float, dist: float) -> float:
    """Геометрическая (без рефракции) высота точки над горизонтом, градусы."""
    _az, true_alt, _app = swe.azalt(jd_ut, swe.ECL2HOR, (lon, lat, 0.0), 0.0, 0.0, (ecl_lon, ecl_lat, dist))
    return true_alt


def angle_speeds(jd_ut: float, lat: float, lon: float, hsys: str) -> dict[str, float]:
    """Скорости ASC и MC (°/сут) конечной разностью ±1 мин."""
    dt = 1.0 / 1440.0
    a = eph.houses(jd_ut - dt, lat, lon, hsys)
    b = eph.houses(jd_ut + dt, lat, lon, hsys)
    return {"asc": signed_diff(a["asc"], b["asc"]) / (2 * dt), "mc": signed_diff(a["mc"], b["mc"]) / (2 * dt)}


# ---------------------------------------------------------------------------
# Аспекты и конфигурации
# ---------------------------------------------------------------------------

POINT_CLASS = {"north_node": "point", "lilith": "point", "chiron": "point", "asc": "angle", "mc": "angle"}


def allowed_orb(scheme: str, asp: str, p1: str, p2: str) -> float | None:
    """Допустимый орбис аспекта asp между p1 и p2 по схеме; None — аспект схемой не используется."""
    cfg = ORB_SCHEMES[scheme]
    pair = {p1, p2}
    if scheme in ("astrotheme", "astrotheme_published"):
        orb = cfg["base"][asp]
        if pair == {"sun", "moon"}:
            orb += cfg["sun_moon_add"]
        elif pair & {"sun", "moon"}:
            orb += cfg["luminary_add"]
        if pair & {"north_node", "lilith", "chiron"}:
            orb = min(orb, cfg["point_cap"])
        return orb
    if scheme == "astrolog":
        orb = min(cfg["base"][asp], cfg["obj_cap"].get(p1, 360.0), cfg["obj_cap"].get(p2, 360.0))
        return orb + cfg["add"].get(p1, 0.0) + cfg["add"].get(p2, 0.0)
    if scheme == "moiety":
        if asp not in cfg["aspects"]:
            return None
        o1 = cfg["orb"].get(p1, cfg["default_orb"])
        o2 = cfg["orb"].get(p2, cfg["default_orb"])
        return (o1 + o2) / 2.0
    if scheme == "ru_points":
        if asp not in cfg["aspects"]:
            return None
        special = pair & {"north_node", "asc", "mc", "lilith"}
        if asp in ("conjunction", "opposition"):
            if special:
                return cfg["node_angle_orb"]
            return min(10.0, (cfg["points"].get(p1, 4) + cfg["points"].get(p2, 4)) / 2.0)
        if asp == "trine" and pair & {"sun", "moon"}:
            return cfg["trine_luminary"]
        return cfg["fixed"][asp]
    raise ValueError(f"Неизвестная схема орбисов: {scheme}")


def find_aspects(points: dict[str, dict], scheme: str, aspect_set: str = "all") -> list[dict]:
    """Все аспекты между точками. points: name → {lon, speed}."""
    kinds = MAJOR if aspect_set == "major" else list(ASPECTS)
    names = list(points)
    res: list[dict] = []
    for i, a in enumerate(names):
        for b in names[i + 1:]:
            if {a, b} == {"asc", "mc"}:
                continue
            pa, pb = points[a], points[b]
            d = signed_diff(pa["lon"], pb["lon"])
            sep = abs(d)
            best = None
            for k in kinds:
                angle = ASPECTS[k][0]
                orb_allowed = allowed_orb(scheme, k, a, b)
                if orb_allowed is None:
                    continue
                delta = sep - angle
                if abs(delta) <= orb_allowed + 1e-9 and (best is None or abs(delta) < abs(best[1])):
                    best = (k, delta, orb_allowed)
            if best is None:
                continue
            k, delta, orb_allowed = best
            # сходящийся (applying) / расходящийся (separating)
            dsep = math.copysign(1.0, d) * (pb.get("speed", 0.0) - pa.get("speed", 0.0)) if d != 0 else 0.0
            if abs(delta) < 1e-6 or dsep == 0:
                phase = "exact"
            else:
                phase = "applying" if delta * dsep < 0 else "separating"
            steps_apart = ASPECTS[k][3]
            sdist = abs(pa["sign_index"] - pb["sign_index"]) % 12
            sdist = min(sdist, 12 - sdist)
            res.append({
                "p1": a, "p2": b, "p1_ru": BODY_RU.get(a, a), "p2_ru": BODY_RU.get(b, b),
                "aspect": k, "aspect_ru": ASPECTS[k][1], "angle": ASPECTS[k][0], "major": ASPECTS[k][2],
                "separation": round(sep, 4), "orb": round(abs(delta), 4), "orb_dm": fmt_orb(delta),
                "orb_allowed": round(orb_allowed, 3), "phase": phase,
                "out_of_sign": (steps_apart is not None and sdist != steps_apart),
            })
    res.sort(key=lambda x: (list(ASPECTS).index(x["aspect"]), x["orb"]))
    return res


def find_patterns(aspects: list[dict], bodies: dict[str, dict], members: list[str],
                  houses_of: dict[str, int] | None, stellium_min: int = 3) -> list[dict]:
    """Конфигурации: Большой тригон, Тау-квадрат, Большой крест, Йод, Воздушный змей, Стеллиум."""
    rel: dict[frozenset, str] = {}
    for a in aspects:
        if a["p1"] in members and a["p2"] in members:
            rel[frozenset((a["p1"], a["p2"]))] = a["aspect"]

    def is_(x: str, y: str, k: str) -> bool:
        return rel.get(frozenset((x, y))) == k

    out: list[dict] = []
    n = len(members)
    grand_trines, crosses = [], []
    for i in range(n):
        for j in range(i + 1, n):
            for k in range(j + 1, n):
                a, b, c = members[i], members[j], members[k]
                if is_(a, b, "trine") and is_(b, c, "trine") and is_(a, c, "trine"):
                    els = {bodies[x]["element"] for x in (a, b, c)}
                    grand_trines.append((a, b, c))
                    out.append({"type": "grand_trine", "type_ru": "Большой тригон", "members": [a, b, c],
                                "element": els.pop() if len(els) == 1 else "mixed"})
    for gt in grand_trines:
        for d in members:
            if d in gt:
                continue
            for x in gt:
                others = [y for y in gt if y != x]
                if is_(d, x, "opposition") and all(is_(d, y, "sextile") for y in others):
                    out.append({"type": "kite", "type_ru": "Воздушный змей", "members": [*gt, d],
                                "apex": d, "focus": x})
    # Большой крест
    opps = [tuple(sorted(k)) for k, v in rel.items() if v == "opposition"]
    for i in range(len(opps)):
        for j in range(i + 1, len(opps)):
            a, b = opps[i]
            c, d = opps[j]
            if len({a, b, c, d}) == 4 and all(is_(x, y, "square") for x in (a, b) for y in (c, d)):
                crosses.append({a, b, c, d})
                mods = {bodies[x]["modality"] for x in (a, b, c, d)}
                out.append({"type": "grand_cross", "type_ru": "Большой крест", "members": sorted([a, b, c, d]),
                            "modality": mods.pop() if len(mods) == 1 else "mixed"})
    # Тау-квадрат (не выводится, если входит в Большой крест)
    for a, b in opps:
        for c in members:
            if c in (a, b):
                continue
            if is_(a, c, "square") and is_(b, c, "square"):
                if any({a, b, c} <= cr for cr in crosses):
                    continue
                out.append({"type": "t_square", "type_ru": "Тау-квадрат", "members": [a, b, c], "apex": c,
                            "apex_modality": bodies[c]["modality"]})
    # Йод (Перст судьбы)
    sext = [tuple(sorted(k)) for k, v in rel.items() if v == "sextile"]
    for a, b in sext:
        for c in members:
            if c in (a, b):
                continue
            if is_(a, c, "quincunx") and is_(b, c, "quincunx"):
                out.append({"type": "yod", "type_ru": "Йод (Перст судьбы)", "members": [a, b, c], "apex": c})
    # Стеллиум по знаку и по дому (только 10 планет)
    by_sign: dict[int, list[str]] = {}
    for p in PLANETS10:
        by_sign.setdefault(bodies[p]["sign_index"], []).append(p)
    for s, ps in sorted(by_sign.items()):
        if len(ps) >= stellium_min:
            out.append({"type": "stellium_sign", "type_ru": f"Стеллиум в знаке {SIGNS_RU[s]}", "members": ps,
                        "sign": SIGNS_EN[s]})
    if houses_of:
        by_house: dict[int, list[str]] = {}
        for p in PLANETS10:
            by_house.setdefault(houses_of[p], []).append(p)
        for h, ps in sorted(by_house.items()):
            if len(ps) >= stellium_min:
                out.append({"type": "stellium_house", "type_ru": f"Стеллиум в {h}-м доме", "members": ps,
                            "house": h})
    return out


# ---------------------------------------------------------------------------
# Солнечные ингрессии (переходы Солнца в знаки)
# ---------------------------------------------------------------------------

def sun_ingresses(jd_ut: float) -> dict:
    """Момент входа Солнца в текущий знак и в следующий (JD UT и UTC)."""
    s = sign_index(eph.sun_longitude(jd_ut))
    prev = eph.find_sun_longitude(30.0 * s, jd_ut, search_back=True)
    nxt = eph.find_sun_longitude(30.0 * ((s + 1) % 12), jd_ut, search_back=False)
    return {"sign_index": s, "entered_jd": prev, "entered_utc": jd_to_utc(prev).isoformat(timespec="seconds"),
            "next_jd": nxt, "next_utc": jd_to_utc(nxt).isoformat(timespec="seconds"),
            "next_sign_ru": SIGNS_RU[(s + 1) % 12]}


# ---------------------------------------------------------------------------
# Основная функция
# ---------------------------------------------------------------------------

def calculate(b: BirthInput, hsys: str = "P", node: str = "true", lilith: str = "mean",
              orbs: str = "astrotheme", aspect_set: str = "all", pof: str = "sect",
              rulership: str = "modern", balance_weights: str = "equal", include_chiron: bool = True,
              include_vertex: bool = True, polar_fallback: str = "O", stellium_min: int = 3,
              outer_exaltations: bool = False, aspect_points: str = "standard") -> dict:
    """Натальная карта тропической западной астрологии.

    Параметры:
      hsys — система домов: P (Плацидус, по умолчанию), K, E, W, O, R, C, T, B;
      node — 'true' (истинный, по умолчанию) | 'mean';
      lilith — 'mean' (средняя Чёрная Луна, по умолчанию) | 'true' (оскулирующий апогей);
      orbs — 'astrotheme' (по умолчанию; фактические орбисы сайта) | 'astrotheme_published'
             (опубликованная таблица Astrotheme, умолчание до 14.10.2026) | 'astrolog' | 'moiety' | 'ru_points';
      aspect_set — 'all' (мажорные + минорные) | 'major';
      pof — 'sect' (день/ночь, по умолчанию) | 'day' (всегда ASC+Луна−Солнце);
      rulership — 'modern' | 'traditional' (для управителей домов и карты);
      balance_weights — 'equal' | 'astrolog';
      polar_fallback — система, если выбранная не определена за полярным кругом (O/E/W);
      aspect_points — 'standard' (10 планет + ASC + MC + узел + Лилит + Хирон) | 'planets_angles'.
    """
    if hsys not in HOUSE_SYSTEMS:
        raise ValueError(f"hsys должен быть одним из {sorted(HOUSE_SYSTEMS)}")
    if orbs not in ORB_SCHEMES:
        raise ValueError(f"orbs должен быть одним из {sorted(ORB_SCHEMES)}")
    allowed = {"node": (node, ("true", "mean")), "lilith": (lilith, ("mean", "true")),
               "aspect_set": (aspect_set, ("all", "major")), "pof": (pof, ("sect", "day")),
               "rulership": (rulership, ("modern", "traditional")),
               "balance_weights": (balance_weights, tuple(BALANCE_WEIGHTS)),
               "polar_fallback": (polar_fallback, ("O", "E", "W")),
               "aspect_points": (aspect_points, ("standard", "planets_angles"))}
    for opt, (val, ok) in allowed.items():
        if val not in ok:
            raise ValueError(f"{opt} должен быть одним из {ok}, получено {val!r}")
    warnings: list[str] = []
    steps: list[dict] = []

    # --- 1. Время -----------------------------------------------------------
    time_known = b.has_time
    bb = b if time_known else replace(b, hour=12, minute=0)
    if bb.tz is None:
        if b.has_place:
            from .common.places import tz_for_coords
            bb = replace(bb, tz=tz_for_coords(b.lat, b.lon))
            warnings.append(f"Часовой пояс определён по координатам: {bb.tz}.")
        else:
            bb = replace(bb, tz="UTC")
            warnings.append("Не задан часовой пояс и место: время трактуется как UTC.")
    if not time_known:
        warnings.append("Время рождения неизвестно: положения взяты на 12:00 местного времени; "
                        "дома, ASC/MC, Парс Фортуны и аспекты к углам не вычисляются; "
                        "Луна за сутки смещается на ~12–15°.")
    n = normalize(bb)
    warnings.extend(n.warnings)
    jd = n.jd_ut
    steps.append({"step": "1. Местное время → UTC",
                  "detail": f"{n.local:%d.%m.%Y %H:%M} местного ({n.offset_source}, {fmt_offset(n.utc_offset_hours)}) "
                            f"→ {n.utc:%d.%m.%Y %H:%M:%S} UTC"})
    steps.append({"step": "2. Юлианский день (UT)", "detail": f"JD = {jd:.6f}"})

    # --- 2. Тела ------------------------------------------------------------
    raw = eph.planet_positions(jd, node=node, include_chiron=False)
    if include_chiron:
        # Хирону нужен файл астероидов seas_*.se1 (в репозитории только seas_18: 1800–2399 гг.);
        # аналитической замены (Moshier), как у планет, для него нет.
        try:
            raw["chiron"] = eph.body_position(jd, swe.CHIRON)
        except swe.Error:
            include_chiron = False
            warnings.append("Хирон не вычислен: нет файла эфемерид астероидов (seas_*.se1) для этой даты "
                            "(в calculators/ephe только 1800–2399 гг.). Аспекты к Хирону не считались.")
        else:
            if jd < CHIRON_RELIABLE_FROM_JD:
                warnings.append("Хирон до 700 г. н.э. недостоверен (Swiss Ephemeris, документация §2.3.4).")
    lil_code = swe.MEAN_APOG if lilith == "mean" else swe.OSCU_APOG
    raw["lilith"] = eph.body_position(jd, lil_code)
    bodies: dict[str, dict] = {}
    for name, v in raw.items():
        bodies[name] = _point(name, v["lon"], v["speed"], v["lat"])
    steps.append({"step": "3. Положения тел (Swiss Ephemeris, тропический зодиак, геоцентрически, видимые)",
                  "detail": "; ".join(f"{bodies[p]['name_ru']} {bodies[p]['pos']}{' R' if bodies[p]['retrograde'] else ''}"
                                      for p in PLANETS10)})

    # ручная самопроверка Солнца и Луны
    sun_lp, moon_lp = sun_lon_low_precision(jd), moon_lon_low_precision(jd)
    steps.append({"step": "3a. Самопроверка приближёнными формулами (Meeus)",
                  "detail": f"Солнце ≈ {dms(sun_lp)} (Δ={signed_diff(sun_lp, bodies['sun']['lon']) * 60:+.1f}′), "
                            f"Луна ≈ {dms(moon_lp)} (Δ={signed_diff(moon_lp, bodies['moon']['lon']):+.2f}°)"})

    # --- 3. Солнечный знак и куспид ------------------------------------------
    ing = sun_ingresses(jd)
    sun_info = {"sign": SIGNS_EN[ing["sign_index"]], "sign_ru": SIGNS_RU[ing["sign_index"]],
                "entered_utc": ing["entered_utc"], "next_ingress_utc": ing["next_utc"],
                "next_sign_ru": ing["next_sign_ru"], "near_cusp": False}
    hours_from_ingress = (jd - ing["entered_jd"]) * 24
    hours_to_next = (ing["next_jd"] - jd) * 24
    if hours_from_ingress < 48 or hours_to_next < 48:
        sun_info["near_cusp"] = True
        warnings.append(
            f"Солнце в пределах 2 суток от смены знака (куспид): вход в {sun_info['sign_ru']} "
            f"{ing['entered_utc']} UTC, следующий знак ({ing['next_sign_ru']}) с {ing['next_utc']} UTC. "
            f"Знак определяется только по моменту ингрессии, а не по таблице дат.")
    steps.append({"step": "4. Знак Солнца по моменту ингрессии (не по таблице дат)",
                  "detail": f"Солнце вошло в {sun_info['sign_ru']} {ing['entered_utc']} UTC; "
                            f"переход в {ing['next_sign_ru']} {ing['next_utc']} UTC"})

    if not time_known:
        # диапазон за сутки для Луны и смены знаков
        start = normalize(replace(bb, hour=0, minute=0)).jd_ut
        end = start + 1.0
        pos0, pos1 = eph.planet_positions(start), eph.planet_positions(end - 1e-6)
        changes = []
        day_changes = []
        for p in PLANETS10:
            s0 = sign_index(pos0[p]["lon"])
            s1 = sign_index(pos1[p]["lon"])
            if s0 != s1:
                changes.append(f"{BODY_RU[p]}: {SIGNS_RU[s0]} → {SIGNS_RU[s1]}")
                day_changes.append({"body": p, "from": SIGNS_EN[s0], "from_ru": SIGNS_RU[s0],
                                    "to": SIGNS_EN[s1], "to_ru": SIGNS_RU[s1]})
        if changes:
            warnings.append("В течение суток меняют знак: " + "; ".join(changes) + ". Знак зависит от времени.")
        # структурно: агент не должен сообщать знак «по полудню», если он менялся в этот день
        sun_info["sign_changes_during_day"] = day_changes
        sun_info["possible_signs_ru"] = next(([c["from_ru"], c["to_ru"]] for c in day_changes if c["body"] == "sun"),
                                             [sun_info["sign_ru"]])
        moon0 = pos0["moon"]["lon"]
        moon1 = eph.planet_positions(end)["moon"]["lon"]
        sun_info["moon_range"] = [dms(moon0), dms(moon1)]

    # --- 4. Дома и углы -------------------------------------------------------
    houses_info = None
    angles: dict[str, dict] = {}
    house_pos: dict[str, int] | None = None
    sect = None
    sun_alt = None
    part_of_fortune = None
    chart_ruler = None
    house_rulers: list[dict] = []
    if time_known and b.has_place:
        h, hw = compute_houses(jd, b.lat, b.lon, hsys, polar_fallback)
        warnings.extend(hw)
        used = h["system"]
        spd = angle_speeds(jd, b.lat, b.lon, used)
        angles["asc"] = _point("asc", h["asc"], spd["asc"])
        angles["mc"] = _point("mc", h["mc"], spd["mc"])
        angles["dsc"] = _point("dsc", h["asc"] + 180.0)
        angles["ic"] = _point("ic", h["mc"] + 180.0)
        angles["dsc"]["name_ru"] = "Десцендент"
        angles["ic"]["name_ru"] = "IC"
        if include_vertex:
            angles["vertex"] = _point("vertex", h["vertex"])
        cusps = [norm360(c) for c in h["cusps"]]
        ruler_tab = RULER_MODERN if rulership == "modern" else RULER_TRADITIONAL
        cusp_list = []
        for i, c in enumerate(cusps):
            s = sign_index(c)
            cusp_list.append({"house": i + 1, "lon": round(c, 6), "pos": dms(c), "pos_rounded": dm_rounded(c),
                              "sign_ru": SIGNS_RU[s], "sign": SIGNS_EN[s],
                              "ruler_modern": RULER_MODERN[s], "ruler_traditional": RULER_TRADITIONAL[s]})
        houses_info = {"system": used, "system_name": HOUSE_SYSTEMS[used], "requested": hsys, "cusps": cusp_list}
        house_pos = {}
        for name in bodies:
            hp = house_of(bodies[name]["lon"], cusps)
            bodies[name]["house"] = hp
            house_pos[name] = hp
        if include_vertex:
            angles["vertex"]["house"] = house_of(h["vertex"], cusps)

        # ручная самопроверка звёздного времени и углов
        gmst = gmst_hours_usno(jd)
        lst = (gmst + b.lon / 15.0) % 24.0
        ramc_manual = lst * 15.0
        eps = mean_obliquity(jd)
        asc_m = asc_from_ramc(ramc_manual, eps, b.lat)
        mc_m = mc_from_ramc(ramc_manual, eps)
        steps.append({"step": "5. Звёздное время и углы (ручная формула)",
                      "detail": f"GMST={gmst:.4f} ч; LST=GMST+λ/15={lst:.4f} ч; RAMC={ramc_manual:.3f}° "
                                f"(SE: {h['armc']:.3f}°); ε={eps:.4f}°; "
                                f"MC=atan2(sin RAMC, cos RAMC·cos ε)={dms(mc_m)}; "
                                f"ASC=atan2(cos RAMC, −(sin RAMC·cos ε + tg φ·sin ε))={dms(asc_m)}"})
        steps.append({"step": "6. ASC/MC и куспиды (Swiss Ephemeris)",
                      "detail": f"ASC {angles['asc']['pos']}, MC {angles['mc']['pos']}; система {HOUSE_SYSTEMS[used]}: "
                                + ", ".join(f"{c['house']}: {c['pos_rounded']}" for c in cusp_list)})

        # секта и Парс Фортуны. Дневная карта — Солнце над истинным горизонтом
        # (геометрическая высота > 0). На обычных широтах это то же, что «Солнце в домах 7–12»,
        # но за полярным кругом (MC под горизонтом, полярная ночь/день) правило по домам ломается.
        sun_raw = raw["sun"]
        sun_alt = altitude(jd, b.lat, b.lon, sun_raw["lon"], sun_raw["lat"], sun_raw["dist"])
        sun_above = sun_alt > 0.0
        sect = "day" if sun_above else "night"
        by_houses = (bodies["sun"]["lon"] - h["asc"]) % 360.0 >= 180.0
        if by_houses != sun_above:
            warnings.append("Секта по истинной высоте Солнца не совпадает с правилом «Солнце в домах 7–12» "
                            "(полярные широты): принята высота Солнца.")
        if abs(sun_alt) < 1.0:
            warnings.append(f"Высота Солнца {sun_alt:+.2f}° — у самого горизонта: дневная/ночная карта "
                            f"зависит от точности времени.")
        mc_alt = altitude(jd, b.lat, b.lon, h["mc"], 0.0, 1.0)
        if mc_alt < 0:
            warnings.append(f"MC находится под горизонтом (высота {mc_alt:+.1f}°) — бывает только за полярным кругом.")
        lon_sun, lon_moon = bodies["sun"]["lon"], bodies["moon"]["lon"]
        if pof == "sect" and sect == "night":
            pf = h["asc"] + lon_sun - lon_moon
            formula = "ночная: ASC + Солнце − Луна"
        else:
            pf = h["asc"] + lon_moon - lon_sun
            formula = "дневная: ASC + Луна − Солнце" if pof == "sect" else "всегда ASC + Луна − Солнце"
        part_of_fortune = _point("part_of_fortune", pf)
        part_of_fortune["formula"] = formula
        part_of_fortune["house"] = house_of(pf, cusps)
        steps.append({"step": "7. Секта и Парс Фортуны",
                      "detail": f"Высота Солнца {sun_alt:+.2f}°: Солнце {'над' if sun_above else 'под'} горизонтом → "
                                f"{'дневная' if sun_above else 'ночная'} "
                                f"карта; Парс Фортуны ({formula}) = {part_of_fortune['pos']}"})

        # управители
        asc_sign = angles["asc"]["sign_index"]
        cr = ruler_tab[asc_sign]
        chart_ruler = {"planet": cr, "planet_ru": BODY_RU[cr], "asc_sign_ru": SIGNS_RU[asc_sign],
                       "traditional": RULER_TRADITIONAL[asc_sign], "modern": RULER_MODERN[asc_sign],
                       "in_sign_ru": bodies[cr]["sign_ru"], "in_house": bodies[cr]["house"]}
        for c in cusp_list:
            r = c["ruler_modern"] if rulership == "modern" else c["ruler_traditional"]
            entry = {"house": c["house"], "cusp_sign_ru": c["sign_ru"], "ruler": r, "ruler_ru": BODY_RU[r],
                     "ruler_in_house": bodies[r]["house"], "ruler_in_sign_ru": bodies[r]["sign_ru"]}
            if c["ruler_modern"] != c["ruler_traditional"]:
                other = c["ruler_traditional"] if rulership == "modern" else c["ruler_modern"]
                entry["co_ruler"] = other
                entry["co_ruler_in_house"] = bodies[other]["house"]
            house_rulers.append(entry)
        steps.append({"step": "8. Управитель карты",
                      "detail": f"ASC в {SIGNS_RU_PREP[asc_sign]} → управитель {BODY_RU[cr]} "
                                f"(трад. {BODY_RU[RULER_TRADITIONAL[asc_sign]]}), стоит в "
                                f"{SIGNS_RU_PREP[bodies[cr]['sign_index']]}, дом {bodies[cr]['house']}"})
    elif time_known and not b.has_place:
        warnings.append("Нет координат места: дома и углы не вычислены.")

    # --- 5. Достоинства --------------------------------------------------------
    for p in PLANETS10:
        dg = dignities_of(p, bodies[p]["sign_index"], outer_exaltations)
        bodies[p]["dignities"] = dg
        bodies[p]["dignities_ru"] = [DIGNITY_RU[x] for x in dg]

    # --- 6. Аспекты ------------------------------------------------------------
    pts: dict[str, dict] = {p: bodies[p] for p in PLANETS10}
    if aspect_points == "standard":
        pts["north_node"] = bodies["north_node"]
        pts["lilith"] = bodies["lilith"]
        if include_chiron:
            pts["chiron"] = bodies["chiron"]
    if angles:
        pts["asc"] = angles["asc"]
        pts["mc"] = angles["mc"]
    aspects = find_aspects(pts, orbs, aspect_set)
    if orbs in ("moiety", "ru_points") and aspect_set == "all":
        warnings.append(f"Схема орбисов '{orbs}' не задаёт орбисы для части минорных аспектов: они не вычислялись.")
    steps.append({"step": "9. Аспекты",
                  "detail": f"Схема орбисов '{orbs}'. Для каждой пары: угол = |Δλ| (≤180°), аспект — если "
                            f"|угол − точный угол| ≤ орбис. Найдено {len(aspects)}."})

    # --- 7. Конфигурации ------------------------------------------------------
    patterns = find_patterns(aspects, bodies, PLANETS10, house_pos, stellium_min)

    # --- 8. Баланс ------------------------------------------------------------
    weights = BALANCE_WEIGHTS[balance_weights]
    elem = {k: 0.0 for k in ELEMENT_RU}
    mod = {k: 0.0 for k in MODALITY_RU}
    pol = {k: 0.0 for k in POLARITY_RU}
    for name, w in weights.items():
        src = bodies.get(name) or angles.get(name)
        if src is None:
            continue
        elem[src["element"]] += w
        mod[src["modality"]] += w
        pol[src["polarity"]] += w
    balance = {"weights": balance_weights, "elements": elem, "modalities": mod, "polarity": pol,
               # при равенстве баллов доминант несколько — выдаются все
               "dominant_elements": [k for k, v in elem.items() if v == max(elem.values())],
               "dominant_modalities": [k for k, v in mod.items() if v == max(mod.values())],
               "missing_elements": [k for k, v in elem.items() if v == 0],
               "missing_modalities": [k for k, v in mod.items() if v == 0]}
    if balance_weights == "astrolog" and not angles:
        warnings.append("Веса 'astrolog' включают ASC/MC, а они не вычислены: баланс неполный.")

    retro = [p for p in PLANETS10 if bodies[p]["retrograde"]]

    variant = (f"тропический зодиак; дома {HOUSE_SYSTEMS[houses_info['system']] if houses_info else '—'}; "
               f"узел {'истинный' if node == 'true' else 'средний'}; Лилит {'средняя' if lilith == 'mean' else 'истинная (оскулирующая)'}; "
               f"орбисы {orbs}; управители {'современные' if rulership == 'modern' else 'традиционные'}; "
               f"Парс Фортуны {'по секте' if pof == 'sect' else 'дневная формула'}")

    return {
        "method": "western_natal",
        "variant": variant,
        "inputs_used": {
            "date": f"{b.year:04d}-{b.month:02d}-{b.day:02d}",
            "time": (f"{b.hour:02d}:{(b.minute or 0):02d}" + (f":{b.second:02d}" if getattr(b, "second", 0) else ""))
                    if time_known else None,
            "tz": bb.tz, "lat": b.lat, "lon": b.lon, "place": b.place,
            "utc": n.utc.isoformat(), "utc_offset": fmt_offset(n.utc_offset_hours),
            "offset_source": n.offset_source, "jd_ut": round(jd, 6),
            "options": {"hsys": hsys, "node": node, "lilith": lilith, "orbs": orbs, "aspect_set": aspect_set,
                        "pof": pof, "rulership": rulership, "balance_weights": balance_weights,
                        "polar_fallback": polar_fallback, "stellium_min": stellium_min},
        },
        "warnings": warnings,
        "time_known": time_known,
        "bodies": bodies,
        "angles": angles,
        "houses": houses_info,
        "sect": sect,
        "sun_altitude": round(sun_alt, 4) if sun_alt is not None else None,
        "part_of_fortune": part_of_fortune,
        "chart_ruler": chart_ruler,
        "house_rulers": house_rulers,
        "aspects": aspects,
        "patterns": patterns,
        "balance": balance,
        "retrograde": retro,
        "sun_sign": sun_info,
        "summary": {
            "sun": f"Солнце {bodies['sun']['pos_rounded']}",
            "moon": f"Луна {bodies['moon']['pos_rounded']}",
            "asc": f"ASC {angles['asc']['pos_rounded']}" if angles else None,
            "mc": f"MC {angles['mc']['pos_rounded']}" if angles else None,
        },
        "steps": steps,
    }


__all__ = ["calculate", "find_aspects", "allowed_orb", "compute_houses", "sign_rising_hours",
           "gmst_hours_usno", "asc_from_ramc", "mc_from_ramc", "vertex_from_ramc", "sun_lon_low_precision",
           "moon_lon_low_precision", "dignities_of", "house_of", "ORB_SCHEMES", "ASPECTS"]
