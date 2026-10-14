"""Обёртка над Swiss Ephemeris (pyswisseph).

Файлы эфемерид лежат в calculators/ephe (sepl_18/semo_18/seas_18: 1800–2399 гг.).
Вне диапазона Swiss Ephemeris сама переходит на аналитическую теорию Moshier.
"""
from __future__ import annotations

import math
import os

import swisseph as swe

EPHE_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "ephe")
swe.set_ephe_path(EPHE_PATH)

FLAGS = swe.FLG_SWIEPH | swe.FLG_SPEED

PLANETS = {
    "sun": swe.SUN, "moon": swe.MOON, "mercury": swe.MERCURY, "venus": swe.VENUS,
    "mars": swe.MARS, "jupiter": swe.JUPITER, "saturn": swe.SATURN, "uranus": swe.URANUS,
    "neptune": swe.NEPTUNE, "pluto": swe.PLUTO,
}

SIGNS_RU = ["Овен", "Телец", "Близнецы", "Рак", "Лев", "Дева",
            "Весы", "Скорпион", "Стрелец", "Козерог", "Водолей", "Рыбы"]
SIGNS_EN = ["Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
            "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"]

AYANAMSAS = {
    "lahiri": swe.SIDM_LAHIRI,
    "raman": swe.SIDM_RAMAN,
    "krishnamurti": swe.SIDM_KRISHNAMURTI,
    "fagan_bradley": swe.SIDM_FAGAN_BRADLEY,
    "true_citra": swe.SIDM_TRUE_CITRA,
    "krishnamurti_vp291": swe.SIDM_KRISHNAMURTI_VP291,
    "yukteshwar": swe.SIDM_YUKTESHWAR,
}


def body_position(jd_ut: float, body: int, sidereal: str | None = None) -> dict:
    flags = FLAGS
    if sidereal:
        swe.set_sid_mode(AYANAMSAS[sidereal])
        flags |= swe.FLG_SIDEREAL
    xx, _ = swe.calc_ut(jd_ut, body, flags)
    return {"lon": xx[0] % 360.0, "lat": xx[1], "dist": xx[2], "speed": xx[3], "retro": xx[3] < 0}


def planet_positions(jd_ut: float, sidereal: str | None = None, node: str = "true",
                     include_chiron: bool = False) -> dict:
    """Долготы Солнца…Плутона + лунные узлы (true/mean) (+ Хирон)."""
    out = {name: body_position(jd_ut, code, sidereal) for name, code in PLANETS.items()}
    node_code = swe.TRUE_NODE if node == "true" else swe.MEAN_NODE
    nn = body_position(jd_ut, node_code, sidereal)
    out["north_node"] = nn
    out["south_node"] = {**nn, "lon": (nn["lon"] + 180.0) % 360.0}
    if include_chiron:
        out["chiron"] = body_position(jd_ut, swe.CHIRON, sidereal)
    return out


def houses(jd_ut: float, lat: float, lon: float, hsys: str = "P", sidereal: str | None = None) -> dict:
    """Куспиды домов и ASC/MC. hsys: P=Плацидус, K=Кох, W=целые знаки, E=равные, O=Порфирий."""
    if sidereal:
        swe.set_sid_mode(AYANAMSAS[sidereal])
        cusps, ascmc = swe.houses_ex(jd_ut, lat, lon, hsys.encode(), swe.FLG_SIDEREAL)
    else:
        cusps, ascmc = swe.houses_ex(jd_ut, lat, lon, hsys.encode())
    return {"cusps": list(cusps[:12]), "asc": ascmc[0], "mc": ascmc[1], "armc": ascmc[2], "vertex": ascmc[3]}


def ayanamsa(jd_ut: float, mode: str = "lahiri", true: bool = False) -> float:
    """Аянамша, градусы. true=False — средняя (без нутации), true=True — истинная (с нутацией).

    Сидерические долготы Swiss Ephemeris (FLG_SIDEREAL) соответствуют истинной аянамше.
    Внимание: функция (как и planet_positions/houses с sidereal=...) глобально выставляет
    swe.set_sid_mode — это побочный эффект на последующие сидерические вызовы.
    """
    swe.set_sid_mode(AYANAMSAS[mode])
    if true:
        return swe.get_ayanamsa_ex_ut(jd_ut, swe.FLG_SWIEPH)[1]
    return swe.get_ayanamsa_ut(jd_ut)


def sun_longitude(jd_ut: float) -> float:
    return body_position(jd_ut, swe.SUN)["lon"]


def find_sun_longitude(target_deg: float, jd_near: float, search_back: bool = True) -> float:
    """Найти момент (JD UT), когда тропическая долгота Солнца = target_deg.

    Ищется ближайшее прохождение ДО jd_near (search_back=True) или ПОСЛЕ.
    Точность ~0.1 с (бисекция). Используется для солнечных терминов (цзеци)
    и для даты «Дизайна» в Human Design (Солнце на 88° раньше).
    """
    target = target_deg % 360.0

    def diff(jd: float) -> float:
        d = (sun_longitude(jd) - target + 540.0) % 360.0 - 180.0
        return d

    step = 1.0 if not search_back else -1.0
    jd = jd_near
    d0 = diff(jd)
    # шагаем по дню, пока не сменится знак разности
    for _ in range(400):
        jd2 = jd + step
        d1 = diff(jd2)
        crossed = (d0 <= 0 < d1) if step > 0 else (d1 <= 0 < d0)
        if crossed and abs(d1 - d0) < 5:
            lo, hi = (jd, jd2) if step > 0 else (jd2, jd)
            for _ in range(60):
                mid = (lo + hi) / 2
                if diff(mid) > 0:
                    hi = mid
                else:
                    lo = mid
            return (lo + hi) / 2
        jd, d0 = jd2, d1
    raise RuntimeError("Не удалось найти момент долготы Солнца")


def format_lon(lon: float, lang: str = "ru") -> str:
    """Долгота -> «Г°ММ′ Знак», минуты отбрасываются (не округляются): 29°59.99′ остаётся 29°59′ того же
    знака — как в эфемеридах и западных программах; знак в строке всегда совпадает с sign_of(lon)."""
    total_min = int(math.floor((lon % 360.0) * 60 + 1e-9)) % (360 * 60)
    sign, rest = divmod(total_min, 30 * 60)
    d, m = divmod(rest, 60)
    names = SIGNS_RU if lang == "ru" else SIGNS_EN
    return f"{d}°{m:02d}′ {names[sign]}"


def sign_of(lon: float) -> int:
    return int((lon % 360.0) // 30)
