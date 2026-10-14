"""Западная прогностика: транзиты, вторичные прогрессии, дирекции солнечной дуги,
соляр (и лунар), годовые профекции — для натальной карты и целевой даты/периода.

Конвейер: натальная карта (calculators.western) → целевой момент `on_date` (UTC, JD) →
1) транзиты: положения на дату, аспекты к натальным точкам с транзитными орбисами, точные
   моменты аспектов в периоде (поиск корней с учётом ретроградных петель — «тройные проходы»),
   стоянки, ингрессии в натальные дома и знаки;
2) вторичные прогрессии («день за год»): прогрессивная дата, планеты, прогрессивные углы
   (несколько методов), прогрессивная Луна (смены знаков и домов), фаза прогрессивной лунации;
3) дирекции солнечной дуги (истинная дуга или ключ Наибода) и их аспекты к радиксу;
4) соляр — точный момент возврата Солнца к натальной долготе, карта на место рождения или
   на другое место (`sr_*`); лунар — по желанию;
5) годовые профекции (эллинистическая техника) и управитель года.

Значения по умолчанию (обоснование и источники — knowledge-base/18-forecast-western.md):
* транзитный орбис 1° для всех транзитов ко всем натальным точкам (astro.com, отчёты Роберта
  Хэнда: «an orb of 1° for all transits to all natal planets»);
* год прогрессий = 365,24219 сут (тропический год, константа rDayInYear в Astrolog);
* прогрессивные углы — 'mean_sun': к звёздному времени рождения (ARMC) прибавляется
  0,98564733° × возраст (ключ Наибода в прямом восхождении), как в astro.com;
* дуга дирекций — 'true' (прогрессивное Солнце − натальное), орбис 1°;
* соляр — тропический, на место рождения (как astro.com по умолчанию), Плацидус;
* профекции — от знака ASC, целые знаки, традиционные управители, смена года в момент соляра.

Пример:
    from calculators.common.time import BirthInput
    from calculators.forecast_western import calculate
    r = calculate(BirthInput(1879, 3, 14, 11, 30, tz="LMT", lat=48.4011, lon=9.9876),
                  on_date="1905-06-30", sr_lat=46.9480, sr_lon=7.4474, sr_tz="Europe/Zurich")
"""
from __future__ import annotations

import math
import re
from datetime import date, datetime, timedelta, timezone
from zoneinfo import ZoneInfo

import swisseph as swe

from . import western as w
from .common import ephemeris as eph
from .common.places import resolve_place, tz_for_coords
from .common.time import BirthInput, jd_to_utc, julian_day_ut
from .western import (ASPECTS, BODY_RU, HOUSE_SYSTEMS, MAJOR, PLANETS10, RULER_MODERN, RULER_TRADITIONAL,
                      SIGNS_EN, SIGNS_RU, compute_houses, dms, find_aspects, fmt_orb, house_of, norm360,
                      sign_index, signed_diff)

# ---------------------------------------------------------------------------
# Константы
# ---------------------------------------------------------------------------

# Ключ Наибода — среднее суточное движение Солнца, °/сут (= °/год в прогрессиях):
# astro.com, FAQ «Overview chart types»: «The mean daily motion of the Sun (the so-called
# 'Naibod key') is 0.98564733°»; AstroWiki «Naibodic Arc»: 59′08,33″.
NAIBOD = 0.98564733
# Длина года для «день = год»: тропический год (Astrolog, astrolog.h: #define rDayInYear 365.24219).
YEAR_LENGTHS = {"tropical": 365.24219, "julian": 365.25}

# Транзитные орбисы. 'hand' — astro.com, FAQ «Forecast Horoscopes»: «Astrotext Forecast by Robert
# Hand use an orb of 1° for all transits to all natal planets».
TRANSIT_ORB_SCHEMES: dict[str, float] = {"hand": 1.0}

PROGRESSION_ANGLE_METHODS = {
    "mean_sun": "ARMC рождения + 0,98564733° × возраст (ключ Наибода в прямом восхождении; astro.com)",
    "naibod": "MC рождения + 0,98564733° × возраст (ключ Наибода в долготе)",
    "solar_arc": "MC рождения + истинная солнечная дуга в долготе (Solar Fire; astro.com: «MC from solar arc»)",
    "solar_arc_ra": "ARMC рождения + солнечная дуга в прямом восхождении",
    "quotidian": "карта на прогрессивный момент: ARMC +361°/прогр. сутки (astro.com: «ARMC 361° / prog. Day»)",
}

# Фазы лунации по Д. Радьяру (8 × 45°); границы — F. Boele, «The Progressed Lunation Cycle», astro.com.
LUNATION_PHASES = [
    ("new", "Новолуние (New Moon)"),
    ("crescent", "Растущий серп (Crescent)"),
    ("first_quarter", "Первая четверть (First Quarter)"),
    ("gibbous", "Выпуклая растущая Луна (Gibbous)"),
    ("full", "Полнолуние (Full Moon)"),
    ("disseminating", "Распространяющая, убывающая выпуклая (Disseminating)"),
    ("last_quarter", "Последняя четверть (Last Quarter)"),
    ("balsamic", "Бальзамическая (Balsamic)"),
]

# Шаг сетки поиска (сут) — меньше времени, за которое тело проходит заметную дугу, и заведомо
# меньше длительности ретроградной петли. Между узлами сетки (и найденными стоянками) движение
# монотонно, поэтому смена знака разности = ровно одно прохождение.
STEP = {"moon": 0.25, "sun": 1.0, "mercury": 1.0, "venus": 1.0, "mars": 2.0, "jupiter": 4.0,
        "saturn": 4.0, "uranus": 5.0, "neptune": 5.0, "pluto": 5.0, "chiron": 4.0, "north_node": 0.5}
# Окно поиска ближайших точных моментов для аспекта «на дату» (сут).
NEAR_WINDOW = {"moon": 1.5, "sun": 3.0, "mercury": 30.0, "venus": 50.0, "mars": 100.0, "jupiter": 250.0,
               "saturn": 400.0, "uranus": 400.0, "neptune": 400.0, "pluto": 400.0, "chiron": 400.0,
               "north_node": 40.0}
SLOW = ["mars", "jupiter", "saturn", "uranus", "neptune", "pluto"]
STATION_BODIES = ["mercury", "venus", "mars", "jupiter", "saturn", "uranus", "neptune", "pluto"]

ASPECT_SETS = {"major": MAJOR, "all": list(ASPECTS)}


# ---------------------------------------------------------------------------
# Время и вспомогательные функции
# ---------------------------------------------------------------------------

_OFFSET_RE = re.compile(r"^(?:UTC|GMT)?([+-])(\d{1,2})(?::?(\d{2}))?$")


def _tzinfo(tz: str | None, lon: float | None = None):
    """'UTC' / 'UTC+03:00' / '+3' / IANA / 'LMT' (нужна долгота) → tzinfo."""
    if tz is None or tz.upper() in ("UTC", "GMT", "UT", "Z"):
        return timezone.utc
    if tz.upper() == "LMT":
        if lon is None:
            raise ValueError("Для LMT нужна долгота.")
        return timezone(timedelta(hours=lon / 15.0))
    m = _OFFSET_RE.match(tz.strip().upper())
    if m:
        sign = -1 if m.group(1) == "-" else 1
        return timezone(sign * timedelta(hours=int(m.group(2)), minutes=int(m.group(3) or 0)))
    return ZoneInfo(tz)


def _parse_moment(value, tz: str = "UTC") -> tuple[datetime, bool]:
    """Дата/время → (момент UTC, было ли задано время). Дата без времени = 00:00 в зоне tz
    (как astro.com: прогрессии считаются на полночь UT)."""
    has_time = True
    if isinstance(value, datetime):
        dt = value
    elif isinstance(value, date):
        dt, has_time = datetime(value.year, value.month, value.day), False
    elif isinstance(value, str):
        s = value.strip().replace(" ", "T")
        if "T" in s:
            dt = datetime.fromisoformat(s)
        else:
            d = date.fromisoformat(s)
            dt, has_time = datetime(d.year, d.month, d.day), False
    else:
        raise ValueError(f"Не удалось разобрать дату {value!r}: ожидается YYYY-MM-DD или YYYY-MM-DDTHH:MM")
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=_tzinfo(tz))
    return dt.astimezone(timezone.utc), has_time


def _iso(jd: float) -> str:
    return jd_to_utc(jd).isoformat(timespec="seconds")


def _local(jd: float, tz: str | None, lon: float | None) -> dict:
    """Момент JD UT в местном времени зоны tz (IANA, смещение или LMT)."""
    utc = jd_to_utc(jd)
    loc = utc.astimezone(_tzinfo(tz, lon))
    off = loc.utcoffset().total_seconds() / 3600.0
    sign = "+" if off >= 0 else "-"
    tot = round(abs(off) * 60)
    return {"local": loc.replace(tzinfo=None).isoformat(timespec="seconds"), "tz": tz,
            "utc_offset": f"UTC{sign}{tot // 60:02d}:{tot % 60:02d}"}


def _code(body: str, node: str) -> int:
    if body == "north_node":
        return swe.TRUE_NODE if node == "true" else swe.MEAN_NODE
    if body == "chiron":
        return swe.CHIRON
    return eph.PLANETS[body]


def _lon(body: str, jd: float, node: str = "true") -> float:
    return eph.body_position(jd, _code(body, node))["lon"]


def _lon_speed(body: str, jd: float, node: str = "true") -> tuple[float, float]:
    r = eph.body_position(jd, _code(body, node))
    return r["lon"], r["speed"]


def _true_obliquity(jd: float) -> float:
    return swe.calc_ut(jd, swe.ECL_NUT)[0][0]


def _ra_of_ecliptic(lon: float, eps: float) -> float:
    """Прямое восхождение точки эклиптики (β = 0)."""
    lr, er = math.radians(lon), math.radians(eps)
    return norm360(math.degrees(math.atan2(math.sin(lr) * math.cos(er), math.cos(lr))))


def _arc(a: float, b: float) -> float:
    """Дуга от a до b вперёд по зодиаку, [0, 360); ≈360 из-за округления → 0."""
    d = (b - a) % 360.0
    return 0.0 if d > 359.9999999 else d


def _pt(name: str, lon: float, speed: float | None = None) -> dict:
    s = sign_index(lon)
    out = {"name": name, "name_ru": BODY_RU.get(name, name), "lon": round(norm360(lon), 6),
           "sign": SIGNS_EN[s], "sign_ru": SIGNS_RU[s], "sign_index": s,
           "deg_in_sign": round(norm360(lon) - 30 * s, 6), "pos": dms(lon)}
    if speed is not None:
        out["speed"] = round(speed, 6)
        out["retrograde"] = speed < 0
    return out


def _bisect(fun, a: float, b: float, fa: float, tol: float = 1e-6) -> float:
    """Корень непрерывной функции на [a, b] при разных знаках на концах."""
    for _ in range(80):
        m = 0.5 * (a + b)
        fm = fun(m)
        if fm == 0.0:
            return m
        if (fm < 0) == (fa < 0):
            a, fa = m, fm
        else:
            b = m
        if b - a < tol:
            break
    return 0.5 * (a + b)


def _root_search(fun, t0: float, t1: float, step: float, tol: float = 1e-6) -> list[float]:
    """Все корни f(t) = 0 на [t0, t1], где f — угловая разность в (−180°, 180°].

    Перескок f через ±180° (дальняя сторона круга) корнем не считается: требуется |Δf| < 90°
    между соседними узлами сетки."""
    n = max(1, int(math.ceil((t1 - t0) / step)))
    ts = [t0 + (t1 - t0) * i / n for i in range(n + 1)]
    fs = [fun(t) for t in ts]
    roots: list[float] = []
    for i in range(n):
        fa, fb = fs[i], fs[i + 1]
        if fa == 0.0:
            roots.append(ts[i])
        elif (fa < 0) != (fb < 0) and fb != 0.0 and abs(fb - fa) < 90.0:
            roots.append(_bisect(fun, ts[i], ts[i + 1], fa, tol))
    if fs[-1] == 0.0:
        roots.append(ts[-1])
    return roots


# ---------------------------------------------------------------------------
# Поиск точных моментов для транзитов
# ---------------------------------------------------------------------------

def stations(body: str, t0: float, t1: float, node: str = "true") -> list[dict]:
    """Стоянки (смена знака скорости) тела на [t0, t1]: 'retrograde' — начало попятного движения."""
    if body in ("sun", "moon"):
        return []
    h = STEP[body]
    n = max(1, int(math.ceil((t1 - t0) / h)))
    ts = [t0 + (t1 - t0) * i / n for i in range(n + 1)]
    sp = [_lon_speed(body, t, node)[1] for t in ts]
    out = []
    for i in range(n):
        if (sp[i] < 0) != (sp[i + 1] < 0):
            def fun(t: float) -> float:
                return _lon_speed(body, t, node)[1]
            t = _bisect(fun, ts[i], ts[i + 1], sp[i], 1e-5)
            lon = _lon(body, t, node)
            kind = "retrograde" if sp[i] > 0 else "direct"
            out.append({"body": body, "body_ru": BODY_RU.get(body, body), "type": kind,
                        "type_ru": "стоянка R (начало попятного движения)" if kind == "retrograde"
                        else "стоянка D (возврат к прямому движению)",
                        "jd": round(t, 6), "utc": _iso(t), "lon": round(lon, 6), "pos": dms(lon)})
    return out


def crossings(body: str, targets: list[float], t0: float, t1: float, node: str = "true",
              split_at: list[float] | None = None, tol: float = 1e-6) -> list[tuple[float, int, float]]:
    """Все прохождения тела через долготы targets на [t0, t1] → [(jd, индекс цели, скорость)].

    Сетка шага STEP[body] дополняется моментами стоянок split_at: между соседними узлами движение
    монотонно, поэтому каждое прохождение (в том числе 3 прохода ретроградной петли) ловится
    сменой знака f = λ(t) − цель. tol — точность корня, сут (в прогрессиях 1e-8 прогр. сут ≈ 0,3 с)."""
    h = STEP[body]
    n = max(1, int(math.ceil((t1 - t0) / h)))
    ts = sorted({t0 + (t1 - t0) * i / n for i in range(n + 1)} | {t for t in (split_at or []) if t0 < t < t1})
    lons = [_lon(body, t, node) for t in ts]
    out: list[tuple[float, int, float]] = []
    for k, tau in enumerate(targets):
        def fun(t: float, tau: float = tau) -> float:
            return signed_diff(tau, _lon(body, t, node))
        for i in range(len(ts) - 1):
            fa, fb = signed_diff(tau, lons[i]), signed_diff(tau, lons[i + 1])
            root = None
            if fa == 0.0:
                root = ts[i]
            elif (fa < 0) != (fb < 0) and fb != 0.0 and abs(fb - fa) < 90.0:
                root = _bisect(fun, ts[i], ts[i + 1], fa, tol)
            elif fb == 0.0 and i == len(ts) - 2:
                root = ts[i + 1]
            if root is not None:
                out.append((root, k, _lon_speed(body, root, node)[1]))
    out.sort()
    return out


def _orb_for(transit_orbs, body: str) -> float:
    if isinstance(transit_orbs, (int, float)):
        return float(transit_orbs)
    if isinstance(transit_orbs, str):
        if transit_orbs in TRANSIT_ORB_SCHEMES:
            return TRANSIT_ORB_SCHEMES[transit_orbs]
        return float(transit_orbs)
    if isinstance(transit_orbs, dict):
        return float(transit_orbs.get(body, transit_orbs.get("default", 1.0)))
    raise ValueError("transit_orbs: число, имя схемы ('hand') или словарь {тело: орбис}")


def _aspect_targets(natal: dict[str, float], kinds: list[str]) -> list[tuple[float, str, str, int]]:
    """Долготы, в которых транзит образует аспект: (долгота, натальная точка, аспект, сторона ±1)."""
    out = []
    for name, lon in natal.items():
        for k in kinds:
            ang = ASPECTS[k][0]
            if ang in (0.0, 180.0):
                out.append((norm360(lon + ang), name, k, 1))
            else:
                out.append((norm360(lon + ang), name, k, 1))
                out.append((norm360(lon - ang), name, k, -1))
    return out


def _phase(delta: float, d: float, rate: float) -> str:
    """Фаза аспекта: delta = |разделение| − угол аспекта; d — разность (подвижная − неподвижная)
    со знаком; rate — скорость подвижной точки (°/ед. времени)."""
    if abs(delta) < 1e-6 or rate == 0:
        return "exact"
    dsep = math.copysign(1.0, d) * rate if d != 0 else rate
    return "applying" if delta * dsep < 0 else "separating"


PHASE_RU = {"applying": "сходящийся", "separating": "расходящийся", "exact": "точный"}


def _aspects_moving_to_fixed(moving: dict[str, dict], fixed: dict[str, float], kinds: list[str],
                             orb_of, skip_same: bool = False, skip_self_conj_except: tuple = ()) -> list[dict]:
    """Аспекты подвижных точек (lon, rate) к неподвижным натальным долготам.

    skip_same — пропускать пары «точка — та же точка радикса» (дирекции: у всех точек одна дуга);
    skip_self_conj_except — в прогрессиях пропускать соединение точки со своим натальным положением
    (медленные планеты «стоят» в орбисе десятилетиями), кроме перечисленных (Луна)."""
    res = []
    for mn, mv in moving.items():
        for fn, flon in fixed.items():
            if skip_same and mn == fn:
                continue
            if skip_self_conj_except and mn == fn and mn not in skip_self_conj_except \
                    and abs(signed_diff(flon, mv["lon"])) < 30.0:
                continue
            d = signed_diff(flon, mv["lon"])
            sep = abs(d)
            best = None
            orb_allowed = orb_of(mn)
            for k in kinds:
                delta = sep - ASPECTS[k][0]
                if abs(delta) <= orb_allowed + 1e-9 and (best is None or abs(delta) < abs(best[1])):
                    best = (k, delta)
            if best is None:
                continue
            k, delta = best
            ph = _phase(delta, d, mv.get("rate", 0.0))
            side = 1 if d >= 0 else -1
            res.append({"moving": mn, "moving_ru": BODY_RU.get(mn, mn), "natal": fn, "natal_ru": BODY_RU.get(fn, fn),
                        "aspect": k, "aspect_ru": ASPECTS[k][1], "angle": ASPECTS[k][0],
                        "separation": round(sep, 4), "orb": round(abs(delta), 4), "orb_dm": fmt_orb(delta),
                        "orb_allowed": round(orb_allowed, 3), "phase": ph, "phase_ru": PHASE_RU[ph],
                        "_target": norm360(flon + side * ASPECTS[k][0]) if ASPECTS[k][0] not in (0.0, 180.0)
                        else norm360(flon + ASPECTS[k][0])})
    res.sort(key=lambda x: (x["orb"], list(ASPECTS).index(x["aspect"])))
    return res


# ---------------------------------------------------------------------------
# Прогрессивные углы
# ---------------------------------------------------------------------------

def _houses_from_armc(armc: float, lat: float, eps: float, hsys: str) -> tuple[list[float], float, float, str]:
    """Куспиды, ASC, MC по ARMC; за полярным кругом — Порфирий (как в western.compute_houses)."""
    used = hsys
    try:
        cusps, ascmc = swe.houses_armc(norm360(armc), lat, eps, hsys.encode())
    except swe.Error:
        used = "O"
        cusps, ascmc = swe.houses_armc(norm360(armc), lat, eps, b"O")
    return [norm360(c) for c in cusps[:12]], norm360(ascmc[0]), norm360(ascmc[1]), used


# ---------------------------------------------------------------------------
# Основная функция
# ---------------------------------------------------------------------------

def calculate(b: BirthInput, on_date=None, on_tz: str = "UTC", period_start=None, period_end=None,
              transit_orbs="hand", transit_aspects: str = "major", hit_bodies="slow",
              natal_points: str = "planets_angles", progression_angles: str = "mean_sun",
              year_length: str = "tropical", progression_orb: float = 1.0, arc: str = "true",
              sa_asc: str = "arc", direction_orb: float = 1.0, direction_aspects: str = "major",
              sr_place: str | None = None, sr_lat: float | None = None, sr_lon: float | None = None,
              sr_tz: str | None = None, sr_year: int | None = None, sr_zodiac: str = "tropical",
              sr_ayanamsa: str = "fagan_bradley", include_lunar_return: bool = True,
              profection_from: str = "asc", profection_boundary: str = "solar_return",
              hsys: str = "P", node: str = "true") -> dict:
    """Прогностика западной астрологии на дату on_date (и период для точных транзитов).

    Параметры:
      on_date — дата/время (YYYY-MM-DD[THH:MM]) в зоне on_tz (по умолчанию UTC); без времени — 00:00;
                по умолчанию — сегодня (с предупреждением: результат зависит от дня запуска);
      period_start, period_end — период поиска точных транзитов, стоянок и ингрессий
                (по умолчанию [on_date, on_date + 1 год));
      transit_orbs — 'hand' (1°, по умолчанию) | число | {тело: орбис, 'default': …};
      transit_aspects, direction_aspects — 'major' (☌ ⚹ □ △ ☍, по умолчанию) | 'all' (+ минорные);
      hit_bodies — 'slow' (Марс…Плутон, по умолчанию) | 'all' (Солнце…Плутон) | 'all_with_moon' | список;
      natal_points — 'planets_angles' (10 планет + ASC + MC) | 'all' (+ сев. узел);
      progression_angles — 'mean_sun' (по умолчанию) | 'naibod' | 'solar_arc' | 'solar_arc_ra' | 'quotidian';
      year_length — 'tropical' (365,24219 сут, по умолчанию) | 'julian' (365,25);
      progression_orb, direction_orb — орбисы аспектов прогрессий и дирекций к радиксу (1°);
      arc — 'true' (истинная солнечная дуга, по умолчанию) | 'naibod' (0,98564733° в год);
      sa_asc — 'arc' (ASC + дуга, по умолчанию) | 'from_mc' (ASC из направленного MC на широте рождения);
      sr_place | sr_lat/sr_lon[/sr_tz] — место соляра (по умолчанию — место рождения);
      sr_year — соляр конкретного года (по умолчанию — действующий на on_date);
      sr_zodiac — 'tropical' (по умолчанию) | 'sidereal' (соляр «с поправкой на прецессию», аянамша sr_ayanamsa);
      profection_from — 'asc' (по умолчанию) | 'sun' | 'moon' | 'mc';
      profection_boundary — 'solar_return' (смена года в момент соляра, по умолчанию) | 'birthday';
      hsys, node — как в western (P; true).
    """
    # --- проверка опций --------------------------------------------------------
    checks = {"transit_aspects": (transit_aspects, tuple(ASPECT_SETS)),
              "direction_aspects": (direction_aspects, tuple(ASPECT_SETS)),
              "natal_points": (natal_points, ("planets_angles", "all")),
              "progression_angles": (progression_angles, tuple(PROGRESSION_ANGLE_METHODS)),
              "year_length": (year_length, tuple(YEAR_LENGTHS)), "arc": (arc, ("true", "naibod")),
              "sa_asc": (sa_asc, ("arc", "from_mc")), "sr_zodiac": (sr_zodiac, ("tropical", "sidereal")),
              "profection_from": (profection_from, ("asc", "sun", "moon", "mc")),
              "profection_boundary": (profection_boundary, ("solar_return", "birthday")),
              "node": (node, ("true", "mean"))}
    for opt, (val, ok) in checks.items():
        if val not in ok:
            raise ValueError(f"{opt} должен быть одним из {ok}, получено {val!r}")
    if hsys not in HOUSE_SYSTEMS:
        raise ValueError(f"hsys должен быть одним из {sorted(HOUSE_SYSTEMS)}")
    if isinstance(hit_bodies, str):
        hb = {"slow": SLOW, "all": PLANETS10[:1] + PLANETS10[2:], "all_with_moon": PLANETS10}.get(hit_bodies)
        if hb is None:
            hb = [x.strip() for x in hit_bodies.split(",")]
    else:
        hb = list(hit_bodies)
    for x in hb:
        if x not in STEP:
            raise ValueError(f"hit_bodies: неизвестное тело {x!r}")
    Y = YEAR_LENGTHS[year_length]
    asp_kinds = ASPECT_SETS[transit_aspects]
    dir_kinds = ASPECT_SETS[direction_aspects]

    warnings: list[str] = []
    steps: list[dict] = []

    # --- 1. Натальная карта (calculators.western) --------------------------------
    nat = w.calculate(b, hsys=hsys, node=node, include_chiron=False, include_vertex=False, aspect_set="major")
    time_known = nat["time_known"]
    has_houses = bool(nat["angles"])
    warnings.extend(f"Натал: {x}" for x in nat["warnings"])
    jd_b = julian_day_ut(datetime.fromisoformat(nat["inputs_used"]["utc"]))
    natal_lon = {p: nat["bodies"][p]["lon"] for p in PLANETS10}
    natal_lon["north_node"] = nat["bodies"]["north_node"]["lon"]
    cusps: list[float] = []
    armc_n = None
    if has_houses:
        natal_lon["asc"] = nat["angles"]["asc"]["lon"]
        natal_lon["mc"] = nat["angles"]["mc"]["lon"]
        cusps = [c["lon"] for c in nat["houses"]["cusps"]]
        used_hsys = nat["houses"]["system"]
        armc_n = eph.houses(jd_b, b.lat, b.lon, used_hsys)["armc"]
    else:
        used_hsys = hsys
    targets_natal = {p: natal_lon[p] for p in PLANETS10}
    if has_houses:
        targets_natal["asc"], targets_natal["mc"] = natal_lon["asc"], natal_lon["mc"]
    if natal_points == "all":
        targets_natal["north_node"] = natal_lon["north_node"]
    if not time_known:
        warnings.append("Время рождения неизвестно (натал на 12:00): нет натальных домов и углов, прогрессивных "
                        "углов, дирекций ASC/MC и профекций от ASC; натальная Луна неточна на ±6–7° — транзиты к Луне, "
                        "прогрессивная Луна (±6 мес.) и момент соляра (±12 ч) ненадёжны.")
    steps.append({"step": "1. Натальная карта", "detail":
                  f"{nat['inputs_used']['utc']} UTC, JD {jd_b:.6f}; Солнце {dms(natal_lon['sun'])}"
                  + (f"; ASC {dms(natal_lon['asc'])}, MC {dms(natal_lon['mc'])}, ARMC {armc_n:.4f}°" if has_houses else "")})

    # --- 2. Целевой момент и период ------------------------------------------------
    if on_date is None:
        on_date = datetime.now(timezone.utc).date()
        warnings.append(f"on_date не задан: взята текущая дата {on_date.isoformat()} (результат зависит от дня запуска).")
    on_utc, on_has_time = _parse_moment(on_date, on_tz)
    jd_on = julian_day_ut(on_utc)
    if jd_on < jd_b:
        raise ValueError("on_date раньше момента рождения: конверсные методы не поддерживаются.")
    if not on_has_time:
        warnings.append(f"Для on_date без времени взято 00:00 ({on_tz}); Луна за сутки проходит 12–15°.")
    if period_start is None and period_end is None:
        p0, p1 = jd_on, jd_on + Y
    else:
        p0 = julian_day_ut(_parse_moment(period_start if period_start is not None else on_utc, on_tz)[0])
        if period_end is None:
            p1 = p0 + Y
        else:
            e_utc, e_has_time = _parse_moment(period_end, on_tz)
            p1 = julian_day_ut(e_utc) + (0.0 if e_has_time else 1.0)   # дата конца включительно
        if p1 <= p0:
            raise ValueError("period_end должен быть позже period_start")
        if p1 - p0 > 3660:
            raise ValueError("Период поиска ограничен 10 годами")
    age = (jd_on - jd_b) / Y
    steps.append({"step": "2. Целевой момент", "detail":
                  f"{on_utc.isoformat(timespec='seconds')} = JD {jd_on:.6f}; возраст (JD − JD₀)/{Y} = {age:.6f} лет; "
                  f"период поиска {_iso(p0)} … {_iso(p1)}"})

    # --- 3. Транзиты ---------------------------------------------------------------
    transit_bodies = PLANETS10 + ["north_node"]
    tpos: dict[str, dict] = {}
    for p in transit_bodies:
        lon, spd = _lon_speed(p, jd_on, node)
        d = _pt(p, lon, spd)
        if has_houses:
            d["natal_house"] = house_of(lon, cusps)
        tpos[p] = d
    moving = {p: {"lon": tpos[p]["lon"], "rate": tpos[p]["speed"]} for p in PLANETS10}
    t_aspects = _aspects_moving_to_fixed(moving, targets_natal, asp_kinds, lambda m: _orb_for(transit_orbs, m))
    for a in t_aspects:
        body = a["moving"]
        win = NEAR_WINDOW[body]
        st = [s["jd"] for s in stations(body, jd_on - win, jd_on + win, node)]
        roots = [r[0] for r in crossings(body, [a.pop("_target")], jd_on - win, jd_on + win, node, st)]
        prev = [r for r in roots if r <= jd_on]
        nxt = [r for r in roots if r > jd_on]
        a["transit_retrograde"] = tpos[body]["retrograde"]
        a["exact_prev_utc"] = _iso(prev[-1]) if prev else None
        a["exact_next_utc"] = _iso(nxt[0]) if nxt else None
        a["exact_search_window_days"] = win
        a["transit"], a["transit_ru"] = a.pop("moving"), a.pop("moving_ru")

    # точные моменты в периоде, стоянки, ингрессии
    station_list: list[dict] = []
    for p in STATION_BODIES:
        station_list.extend(stations(p, p0, p1, node))
    station_list.sort(key=lambda s: s["jd"])
    for s in station_list:
        near = []
        for name, lon in targets_natal.items():
            d = signed_diff(lon, s["lon"])
            for k in asp_kinds:
                if abs(abs(d) - ASPECTS[k][0]) <= _orb_for(transit_orbs, s["body"]):
                    near.append({"natal": name, "natal_ru": BODY_RU.get(name, name), "aspect": k,
                                 "aspect_ru": ASPECTS[k][1], "orb": round(abs(abs(d) - ASPECTS[k][0]), 4)})
        s["aspects_to_natal"] = near
    targets = _aspect_targets(targets_natal, asp_kinds)
    hits: list[dict] = []
    house_ingresses: list[dict] = []
    sign_ingresses: list[dict] = []
    for p in hb:
        if p in STATION_BODIES:
            st = [s["jd"] for s in station_list if s["body"] == p]
        else:
            st = [s["jd"] for s in stations(p, p0, p1, node)]
        for jd, k, spd in crossings(p, [t[0] for t in targets], p0, p1, node, st):
            tau, name, asp, side = targets[k]
            hits.append({"transit": p, "transit_ru": BODY_RU.get(p, p), "natal": name, "natal_ru": BODY_RU.get(name, name),
                         "aspect": asp, "aspect_ru": ASPECTS[asp][1], "side": side, "jd": round(jd, 6), "utc": _iso(jd),
                         "transit_lon": round(tau, 6), "transit_pos": dms(tau), "retrograde": spd < 0})
        for jd, k, spd in crossings(p, [30.0 * i for i in range(12)], p0, p1, node, st):
            to = k if spd > 0 else (k - 1) % 12
            sign_ingresses.append({"body": p, "body_ru": BODY_RU.get(p, p), "jd": round(jd, 6), "utc": _iso(jd),
                                   "to_sign": SIGNS_EN[to], "to_sign_ru": SIGNS_RU[to], "retrograde": spd < 0})
        if has_houses:
            for jd, k, spd in crossings(p, cusps, p0, p1, node, st):
                to = k + 1 if spd > 0 else (k - 1) % 12 + 1
                house_ingresses.append({"body": p, "body_ru": BODY_RU.get(p, p), "jd": round(jd, 6), "utc": _iso(jd),
                                        "cusp": k + 1, "enters_house": to, "retrograde": spd < 0})
    # номера проходов: 1/3, 2/3, 3/3 у ретроградной петли
    groups: dict[tuple, list[dict]] = {}
    for h in hits:
        groups.setdefault((h["transit"], h["natal"], h["aspect"], h["side"]), []).append(h)
    for g in groups.values():
        g.sort(key=lambda x: x["jd"])
        for i, h in enumerate(g):
            h["pass_index"], h["passes_in_period"] = i + 1, len(g)
    hits.sort(key=lambda x: x["jd"])
    sign_ingresses.sort(key=lambda x: x["jd"])
    house_ingresses.sort(key=lambda x: x["jd"])
    steps.append({"step": "3. Транзиты", "detail":
                  f"Орбис {transit_orbs!r} ({_orb_for(transit_orbs, 'sun')}° для Солнца); аспектов на дату {len(t_aspects)}; "
                  f"точных попаданий тел {', '.join(hb)} в периоде {len(hits)}; стоянок {len(station_list)}. "
                  "Точный момент — корень f(t) = λ_тр(t) − (λ_натал ± угол), бисекция до 0,1 с; сетка дополнена "
                  "моментами стоянок, поэтому все 3 прохода ретроградной петли находятся отдельно."})
    transits = {"jd": round(jd_on, 6), "utc": on_utc.isoformat(timespec="seconds"), "positions": tpos,
                "aspects": t_aspects, "orbs": transit_orbs if not isinstance(transit_orbs, dict) else dict(transit_orbs),
                "period": {"start_utc": _iso(p0), "end_utc": _iso(p1), "bodies": hb},
                "exact_hits": hits, "stations": station_list, "sign_ingresses": sign_ingresses,
                "house_ingresses": house_ingresses}

    # --- 4. Вторичные прогрессии -------------------------------------------------------
    def pjd_of(jd_real: float) -> float:
        return jd_b + (jd_real - jd_b) / Y

    def real_of(pjd: float) -> float:
        return jd_b + (pjd - jd_b) * Y

    pjd = pjd_of(jd_on)
    sun_n = natal_lon["sun"]
    ppos: dict[str, dict] = {}
    for p in PLANETS10 + ["north_node"]:
        lon, spd = _lon_speed(p, pjd, node)
        d = _pt(p, lon, spd)
        d["speed_per_year"] = d.pop("speed")
        if has_houses:
            d["natal_house"] = house_of(lon, cusps)
        ppos[p] = d

    def prog_angles(jd_real: float) -> dict:
        """Прогрессивные ARMC, ASC, MC, куспиды методом progression_angles на реальный момент."""
        a_ = (jd_real - jd_b) / Y
        pj = jd_b + a_
        eps = _true_obliquity(pj)
        if progression_angles == "mean_sun":
            armc = armc_n + NAIBOD * a_
        elif progression_angles == "naibod":
            armc = _ra_of_ecliptic(natal_lon["mc"] + NAIBOD * a_, eps)
        elif progression_angles == "solar_arc":
            armc = _ra_of_ecliptic(natal_lon["mc"] + _arc(sun_n, _lon("sun", pj)), eps)
        elif progression_angles == "solar_arc_ra":
            ra_n = swe.calc_ut(jd_b, swe.SUN, swe.FLG_SWIEPH | swe.FLG_EQUATORIAL)[0][0]
            ra_p = swe.calc_ut(pj, swe.SUN, swe.FLG_SWIEPH | swe.FLG_EQUATORIAL)[0][0]
            armc = armc_n + _arc(ra_n, ra_p)
        else:  # quotidian: карта на сам прогрессивный момент
            armc = eph.houses(pj, b.lat, b.lon, used_hsys)["armc"]
        cs, asc, mc, used = _houses_from_armc(armc, b.lat, eps, used_hsys)
        return {"armc": norm360(armc), "asc": asc, "mc": mc, "cusps": cs, "system": used, "eps": eps}

    prog_houses = None
    if has_houses:
        pa = prog_angles(jd_on)
        da = prog_angles(jd_on + 10.0)
        rate_asc = signed_diff(pa["asc"], da["asc"]) / 10.0 * Y
        rate_mc = signed_diff(pa["mc"], da["mc"]) / 10.0 * Y
        ppos["asc"] = _pt("asc", pa["asc"])
        ppos["mc"] = _pt("mc", pa["mc"])
        ppos["asc"]["speed_per_year"], ppos["mc"]["speed_per_year"] = round(rate_asc, 6), round(rate_mc, 6)
        ppos["asc"]["natal_house"] = house_of(pa["asc"], cusps)
        ppos["mc"]["natal_house"] = house_of(pa["mc"], cusps)
        for p in PLANETS10 + ["north_node"]:
            ppos[p]["progressed_house"] = house_of(ppos[p]["lon"], pa["cusps"])
        prog_houses = {"method": progression_angles, "method_ru": PROGRESSION_ANGLE_METHODS[progression_angles],
                       "armc": round(pa["armc"], 6), "armc_natal": round(armc_n, 6),
                       "armc_advance": round(_arc(armc_n, pa["armc"]), 6), "system": pa["system"],
                       "cusps": [{"house": i + 1, "lon": round(c, 6), "pos": dms(c)} for i, c in enumerate(pa["cusps"])]}

    def prog_lon_fun(name: str):
        if name in ("asc", "mc"):
            return lambda t: prog_angles(t)[name]
        return lambda t: _lon(name, pjd_of(t), node)

    pmoving = {p: {"lon": ppos[p]["lon"], "rate": ppos[p]["speed_per_year"]} for p in ppos}
    p_aspects = _aspects_moving_to_fixed({k: v for k, v in pmoving.items() if k != "north_node"},
                                         targets_natal, asp_kinds, lambda m: float(progression_orb),
                                         skip_self_conj_except=("moon",))
    for a in p_aspects:
        tau = a.pop("_target")
        fun_lon = prog_lon_fun(a["moving"])
        win, stp = (120.0, 3.0) if a["moving"] == "moon" else (3 * Y, 20.0)
        roots = _root_search(lambda t: signed_diff(tau, fun_lon(t)), max(jd_b, jd_on - win), jd_on + win, stp, 1e-4)
        best = min(roots, key=lambda r: abs(r - jd_on)) if roots else None
        a["exact_utc"] = _iso(best) if best is not None else None
        a["progressed"], a["progressed_ru"] = a.pop("moving"), a.pop("moving_ru")

    # прогрессивная Луна: смены знаков и натальных домов
    def moon_events(pj0: float, pj1: float) -> list[dict]:
        ev = []
        for jd, k, _s in crossings("moon", [30.0 * i for i in range(12)], pj0, pj1, node, tol=1e-8):
            ev.append({"type": "sign", "utc": _iso(real_of(jd)), "jd": round(real_of(jd), 6),
                       "to_sign": SIGNS_EN[k], "to_sign_ru": SIGNS_RU[k]})
        if has_houses:
            for jd, k, _s in crossings("moon", cusps, pj0, pj1, node, tol=1e-8):
                ev.append({"type": "natal_house", "utc": _iso(real_of(jd)), "jd": round(real_of(jd), 6),
                           "to_house": k + 1})
        ev.sort(key=lambda x: x["jd"])
        return ev

    back = moon_events(max(jd_b, pjd - 3.0), pjd)
    fwd = moon_events(pjd, pjd + 6.0)
    pmoon = {**ppos["moon"],
             "entered_sign_utc": next((e["utc"] for e in reversed(back) if e["type"] == "sign"), None),
             "next_sign_change": next((e for e in fwd if e["type"] == "sign"), None),
             "next_natal_house_change": next((e for e in fwd if e["type"] == "natal_house"), None),
             "events_in_period": moon_events(pjd_of(p0), pjd_of(p1))}

    # фаза прогрессивной лунации
    def elong(pj: float) -> float:
        return norm360(_lon("moon", pj, node) - _lon("sun", pj, node))

    el = elong(pjd)
    ph = int(el // 45.0)
    starts = _root_search(lambda t: signed_diff(45.0 * ph, elong(t)), pjd - 4.5, pjd, 0.25, 1e-8)
    ends = _root_search(lambda t: signed_diff(45.0 * ((ph + 1) % 8), elong(t)), pjd, pjd + 4.5, 0.25, 1e-8)
    nm_prev = _root_search(lambda t: signed_diff(0.0, elong(t)), pjd - 31.0, pjd, 0.5, 1e-8)
    nm_next = _root_search(lambda t: signed_diff(0.0, elong(t)), pjd, pjd + 31.0, 0.5, 1e-8)
    fm_next = _root_search(lambda t: signed_diff(180.0, elong(t)), pjd, pjd + 31.0, 0.5, 1e-8)

    def _ev(roots: list[float], last: bool) -> dict | None:
        if not roots:
            return None
        r = roots[-1] if last else roots[0]
        jr = real_of(r)
        return {"utc": _iso(jr), "jd": round(jr, 6), "before_birth": jr < jd_b,
                "age_years": round((jr - jd_b) / Y, 3)}

    lunation = {"elongation": round(el, 4), "phase": LUNATION_PHASES[ph][0], "phase_ru": LUNATION_PHASES[ph][1],
                "phase_index": ph + 1, "phase_range": f"{45 * ph}°–{45 * ph + 44}°",
                "phase_started": _ev(starts, True), "next_phase": _ev(ends, False),
                "next_phase_name": LUNATION_PHASES[(ph + 1) % 8][0],
                "last_new_moon": _ev(nm_prev, True), "next_new_moon": _ev(nm_next, False),
                "next_full_moon": _ev(fm_next, False)}
    progressions = {"progressed_jd": round(pjd, 6), "progressed_utc": _iso(pjd), "age_years": round(age, 6),
                    "year_length_days": Y, "positions": ppos, "angles": prog_houses, "aspects_to_natal": p_aspects,
                    "moon": pmoon, "lunation": lunation}
    steps.append({"step": "4. Вторичные прогрессии", "detail":
                  f"Прогрессивный момент = JD₀ + возраст = {jd_b:.6f} + {age:.6f} = {pjd:.6f} ({_iso(pjd)} UTC); "
                  f"прогр. Солнце {dms(ppos['sun']['lon'])}, Луна {dms(ppos['moon']['lon'])}"
                  + (f"; углы ({progression_angles}): ARMC {prog_houses['armc']:.4f}° (натал {armc_n:.4f}°), "
                     f"MC {dms(ppos['mc']['lon'])}, ASC {dms(ppos['asc']['lon'])}" if prog_houses else "")
                  + f"; элонгация Луны {el:.2f}° → фаза {LUNATION_PHASES[ph][1]}"})

    # --- 5. Дирекции солнечной дуги --------------------------------------------------
    arc_true = _arc(sun_n, _lon("sun", pjd, node))
    arc_naibod = NAIBOD * age

    def arc_at(jd_real: float) -> float:
        if arc == "naibod":
            return NAIBOD * (jd_real - jd_b) / Y
        return _arc(sun_n, _lon("sun", pjd_of(jd_real), node))

    def directed_fun(name: str):
        if name == "asc" and sa_asc == "from_mc":
            eps_n = _true_obliquity(jd_b)

            def f(t: float) -> float:
                armc = _ra_of_ecliptic(natal_lon["mc"] + arc_at(t), eps_n)
                return _houses_from_armc(armc, b.lat, eps_n, used_hsys)[1]
            return f
        return lambda t: norm360(natal_lon[name] + arc_at(t))

    sa_value = arc_true if arc == "true" else arc_naibod
    dir_names = PLANETS10 + ["north_node"] + (["asc", "mc"] if has_houses else [])
    directed: dict[str, dict] = {}
    for p in dir_names:
        lon = directed_fun(p)(jd_on)
        d = _pt(p, lon)
        if has_houses:
            d["natal_house"] = house_of(lon, cusps)
        directed[p] = d
    rate = NAIBOD if arc == "naibod" else max(1e-6, ppos["sun"]["speed_per_year"])
    dmoving = {p: {"lon": directed[p]["lon"], "rate": rate} for p in dir_names if p != "north_node"}
    d_aspects = _aspects_moving_to_fixed(dmoving, targets_natal, dir_kinds, lambda m: float(direction_orb),
                                         skip_same=True)
    for a in d_aspects:
        tau = a.pop("_target")
        f = directed_fun(a["moving"])
        roots = _root_search(lambda t: signed_diff(tau, f(t)), max(jd_b, jd_on - 3 * Y), jd_on + 3 * Y, 20.0, 1e-4)
        best = min(roots, key=lambda r: abs(r - jd_on)) if roots else None
        a["exact_utc"] = _iso(best) if best is not None else None
        a["exact_age_years"] = round((best - jd_b) / Y, 3) if best is not None else None
        a["directed"], a["directed_ru"] = a.pop("moving"), a.pop("moving_ru")
    solar_arc = {"arc_method": arc, "arc": round(sa_value, 6), "arc_dms": fmt_orb(sa_value),
                 "arc_true": round(arc_true, 6), "arc_naibod": round(arc_naibod, 6),
                 "asc_method": sa_asc, "directed": directed, "aspects_to_natal": d_aspects}
    steps.append({"step": "5. Дирекции солнечной дуги", "detail":
                  f"Истинная дуга = прогр. Солнце − натальное = {arc_true:.4f}°; дуга Наибода = 0,98564733 × "
                  f"{age:.4f} = {arc_naibod:.4f}°; принята {'истинная' if arc == 'true' else 'Наибода'} "
                  f"({sa_value:.4f}°), прибавлена ко всем точкам; аспектов к радиксу в орбисе {direction_orb}°: {len(d_aspects)}"})

    # --- 6. Соляр (и лунар) -----------------------------------------------------------
    if sr_place or sr_lat is not None or sr_lon is not None:
        p_ = resolve_place(sr_place) if sr_place else None
        if sr_place and p_ is None and (sr_lat is None or sr_lon is None):
            raise ValueError(f"Место соляра «{sr_place}» нет в справочнике — передайте sr_lat/sr_lon[/sr_tz].")
        s_lat = sr_lat if sr_lat is not None else (p_["lat"] if p_ else None)
        s_lon = sr_lon if sr_lon is not None else (p_["lon"] if p_ else None)
        if s_lat is None or s_lon is None:
            raise ValueError("Для места соляра нужны обе координаты sr_lat и sr_lon (или sr_place).")
        s_tz = sr_tz or (p_["tz"] if p_ else None) or tz_for_coords(s_lat, s_lon) or "UTC"
        s_name = sr_place or (p_["name"] if p_ else f"{s_lat:.4f}, {s_lon:.4f}")
        sr_where = "relocated"
    else:
        s_lat, s_lon, s_tz, s_name, sr_where = b.lat, b.lon, nat["inputs_used"]["tz"], b.place, "birthplace"

    def sun_return(jd_near: float, back: bool, target: float) -> float:
        return eph.find_sun_longitude(target, jd_near, search_back=back)

    if sr_year is not None:
        bm, bd = b.month, b.day
        if (bm, bd) == (2, 29):
            try:
                date(sr_year, 2, 29)
            except ValueError:
                bm, bd = 3, 1
        anchor = swe.julday(sr_year, bm, bd, 12.0) + 3.0
    else:
        anchor = jd_on
    if sr_year is not None and anchor - 3.0 < jd_b:
        raise ValueError("sr_year раньше года рождения")

    sid_note = None
    jd_trop = sun_return(anchor, True, sun_n)
    if sr_zodiac == "tropical":
        jd_sr, sr_target = jd_trop, sun_n
        jd_sr_next = sun_return(jd_sr + 300.0, False, sun_n)
    else:
        ay_b = eph.ayanamsa(jd_b, sr_ayanamsa, true=True)

        def sidereal_near(jd_t: float) -> tuple[float, float]:
            """Сидерический возврат рядом с тропическим jd_t: Солнце догоняет натальную долготу
            + накопленную прецессию (≈0,014 сут на год возраста), уточнение итерациями."""
            jd_s, tgt = jd_t, sun_n
            for _ in range(4):
                tgt = norm360(sun_n + eph.ayanamsa(jd_s, sr_ayanamsa, true=True) - ay_b)
                jd_s = sun_return(jd_t + 3.0, True, tgt)
            return jd_s, tgt

        jd_sr, sr_target = sidereal_near(jd_trop)
        if sr_year is None and jd_sr > jd_on:      # сидерический соляр этого года ещё не наступил
            jd_sr, sr_target = sidereal_near(sun_return(jd_trop - 300.0, True, sun_n))
        jd_sr_next = sidereal_near(sun_return(jd_sr + 300.0, False, sun_n))[0]
        sid_note = (f"сидерический соляр: Солнце возвращается к натальной сидерической долготе "
                    f"(аянамша {sr_ayanamsa}); тропическая цель {dms(sr_target)}")
        warnings.append("Соляр с поправкой на прецессию (sidereal): astro.com такой расчёт не предлагает и считает "
                        "его несогласованным с тропической астрологией; по умолчанию — тропический соляр.")
    sr_sun = _lon("sun", jd_sr, node)
    pos_sr = eph.planet_positions(jd_sr, node=node)
    sr_bodies: dict[str, dict] = {}
    for p in PLANETS10 + ["north_node"]:
        sr_bodies[p] = _pt(p, pos_sr[p]["lon"], pos_sr[p]["speed"])
    sr_chart = {"moment_jd": round(jd_sr, 6), "moment_utc": _iso(jd_sr), "zodiac": sr_zodiac,
                "natal_sun": round(sun_n, 6), "sr_sun": round(sr_sun, 6),
                "sun_check_arcsec": round(abs(signed_diff(sr_target, sr_sun)) * 3600.0, 3),
                "next_moment_utc": _iso(jd_sr_next), "place": s_name, "lat": s_lat, "lon": s_lon,
                "where": sr_where, "bodies": sr_bodies, "angles": None, "houses": None, "aspects": None}
    if sid_note:
        sr_chart["note"] = sid_note
    # отклонение от «дня рождения»: момент соляра − годовщина момента рождения (UT), сутки
    by = jd_to_utc(jd_sr).year
    bu = jd_to_utc(jd_b)
    try:
        anniv = julian_day_ut(bu.replace(year=by))
    except ValueError:   # 29 февраля в невисокосный год
        anniv = julian_day_ut(bu.replace(year=by, month=3, day=1))
    if abs(jd_sr - anniv) > 200:
        anniv = julian_day_ut(bu.replace(year=by + (1 if jd_sr > anniv else -1)))
    sr_chart["days_from_birth_anniversary_utc"] = round(jd_sr - anniv, 4)
    if s_lat is not None and s_lon is not None and s_tz is not None:
        sr_chart.update(_local(jd_sr, s_tz, s_lon))
    if time_known and s_lat is not None and s_lon is not None:
        h, hw = compute_houses(jd_sr, s_lat, s_lon, hsys)
        warnings.extend(f"Соляр: {x}" for x in hw)
        sr_cusps = [norm360(c) for c in h["cusps"]]
        sr_chart["angles"] = {"asc": _pt("asc", h["asc"]), "mc": _pt("mc", h["mc"])}
        if has_houses:
            for k in ("asc", "mc"):
                sr_chart["angles"][k]["natal_house"] = house_of(sr_chart["angles"][k]["lon"], cusps)
        sr_chart["houses"] = {"system": h["system"], "system_name": HOUSE_SYSTEMS[h["system"]],
                              "cusps": [{"house": i + 1, "lon": round(c, 6), "pos": dms(c)} for i, c in enumerate(sr_cusps)]}
        for p in sr_bodies:
            sr_bodies[p]["sr_house"] = house_of(sr_bodies[p]["lon"], sr_cusps)
            if has_houses:
                sr_bodies[p]["natal_house"] = house_of(sr_bodies[p]["lon"], cusps)
        pts = {p: sr_bodies[p] for p in PLANETS10}
        pts["asc"], pts["mc"] = sr_chart["angles"]["asc"], sr_chart["angles"]["mc"]
        sr_chart["aspects"] = [{k: v for k, v in a.items() if k in ("p1", "p2", "p1_ru", "p2_ru", "aspect", "aspect_ru",
                                                                    "orb", "orb_dm", "phase")}
                               for a in find_aspects(pts, "astrotheme", "major")]
    elif not time_known:
        warnings.append("Соляр: без времени рождения натальная долгота Солнца известна лишь ±0,5°, момент соляра "
                        "±12 ч — углы и дома соляра не вычисляются.")
    steps.append({"step": "6. Соляр", "detail":
                  f"Момент, когда видимая тропическая долгота Солнца = натальной {dms(sun_n)}: {sr_chart['moment_utc']} UTC"
                  + (f" = {sr_chart['local']} ({sr_chart['utc_offset']}, {s_tz})" if "local" in sr_chart else "")
                  + f"; отклонение от годовщины момента рождения {sr_chart['days_from_birth_anniversary_utc']:+.3f} сут; "
                  f"место: {s_name or '—'} ({'место рождения' if sr_where == 'birthplace' else 'релокация'})"
                  + (f"; ASC соляра {sr_chart['angles']['asc']['pos']}, MC {sr_chart['angles']['mc']['pos']}"
                     if sr_chart["angles"] else "")})

    lunar_return = None
    if include_lunar_return:
        moon_n = natal_lon["moon"]
        lr = crossings("moon", [moon_n], jd_on - 28.0, jd_on)
        lr_next = crossings("moon", [moon_n], jd_on, jd_on + 28.0)
        if lr:
            jd_lr = lr[-1][0]
            lunar_return = {"moment_utc": _iso(jd_lr), "moment_jd": round(jd_lr, 6),
                            "next_moment_utc": _iso(lr_next[0][0]) if lr_next else None,
                            "natal_moon": round(moon_n, 6), "place": s_name}
            if s_tz and s_lon is not None:
                lunar_return.update(_local(jd_lr, s_tz, s_lon))
            if time_known and s_lat is not None:
                h, _hw = compute_houses(jd_lr, s_lat, s_lon, hsys)
                lr_cusps = [norm360(c) for c in h["cusps"]]
                lunar_return["asc"] = _pt("asc", h["asc"])
                lunar_return["mc"] = _pt("mc", h["mc"])
                lunar_return["moon_house"] = house_of(moon_n, lr_cusps)
                if has_houses:
                    lunar_return["asc"]["natal_house"] = house_of(h["asc"], cusps)

    # --- 7. Годовые профекции ------------------------------------------------------------
    profections = None
    start_lon = None
    if profection_from in ("asc", "mc"):
        if has_houses:
            start_lon = natal_lon[profection_from]
        else:
            warnings.append(f"Профекции от {profection_from.upper()} требуют времени и места рождения — не вычислены "
                            "(можно profection_from='sun').")
    else:
        start_lon = natal_lon[profection_from]
    if start_lon is not None:
        # границы годов профекции: моменты соляров (или годовщины даты рождения)
        if profection_boundary == "solar_return":
            y0 = sun_return(jd_on, True, sun_n)
            y1 = sun_return(y0 + 300.0, False, sun_n)
            if y0 < jd_b + 1.0:           # первый год жизни: начало — рождение
                y0 = jd_b
        else:
            loc_b = datetime(b.year, b.month, b.day)
            on_loc = on_utc.astimezone(_tzinfo(nat["inputs_used"]["tz"], b.lon)).replace(tzinfo=None)
            yy = on_loc.year if (on_loc.month, on_loc.day) >= (b.month, b.day) else on_loc.year - 1

            def bday(year: int) -> float:
                try:
                    dt = loc_b.replace(year=year)
                except ValueError:
                    dt = loc_b.replace(year=year, month=3, day=1)
                return julian_day_ut(dt.replace(tzinfo=_tzinfo(nat["inputs_used"]["tz"], b.lon)).astimezone(timezone.utc))
            y0, y1 = bday(yy), bday(yy + 1)
            if yy == b.year:
                y0 = jd_b
        n_years = int(round((y0 - jd_b) / Y))
        s0 = sign_index(start_lon)
        s = (s0 + n_years) % 12
        lord = RULER_TRADITIONAL[s]
        asc_s = sign_index(natal_lon["asc"]) if has_houses else None
        in_sign = [p for p in PLANETS10 if sign_index(natal_lon[p]) == s]
        frac = (jd_on - y0) / (y1 - y0)
        m = min(11, int(frac * 12))
        ms = (s + m) % 12
        profections = {
            "from": profection_from, "age_completed": n_years, "house_whole_sign": n_years % 12 + 1,
            "sign": SIGNS_EN[s], "sign_ru": SIGNS_RU[s], "lord": lord, "lord_ru": BODY_RU[lord],
            "lord_modern": RULER_MODERN[s], "lord_modern_ru": BODY_RU[RULER_MODERN[s]],
            "year_start_utc": _iso(y0), "year_end_utc": _iso(y1), "boundary": profection_boundary,
            "natal_planets_in_sign": in_sign,
            "lord_natal": {"pos": dms(natal_lon[lord]), "sign_ru": SIGNS_RU[sign_index(natal_lon[lord])],
                           "house_whole_sign": ((sign_index(natal_lon[lord]) - asc_s) % 12 + 1) if asc_s is not None else None,
                           "house": house_of(natal_lon[lord], cusps) if has_houses else None},
            "lord_transit": {"pos": tpos[lord]["pos"], "sign_ru": tpos[lord]["sign_ru"],
                             "retrograde": tpos[lord]["retrograde"],
                             "natal_house": tpos[lord].get("natal_house"),
                             "house_whole_sign": ((tpos[lord]["sign_index"] - asc_s) % 12 + 1) if asc_s is not None else None},
            "month": {"index": m + 1, "sign": SIGNS_EN[ms], "sign_ru": SIGNS_RU[ms], "lord": RULER_TRADITIONAL[ms],
                      "lord_ru": BODY_RU[RULER_TRADITIONAL[ms]],
                      "start_utc": _iso(y0 + (y1 - y0) * m / 12.0), "end_utc": _iso(y0 + (y1 - y0) * (m + 1) / 12.0),
                      "variant": "месяц = 1/12 года профекции, от знака года (⚠ одна из версий)"},
        }
        if profection_from != "asc":
            profections["house_whole_sign"] = None
            if asc_s is not None:
                profections["house_whole_sign"] = (s - asc_s) % 12 + 1
            warnings.append(f"Профекции от {profection_from} — вариант; классическое правило — от знака ASC.")
        steps.append({"step": "7. Годовые профекции", "detail":
                      f"Полных лет {n_years} (граница — {'соляр' if profection_boundary == 'solar_return' else 'день рождения'}); "
                      f"знак = {SIGNS_RU[s0]} + {n_years} mod 12 = {SIGNS_RU[s]} ({n_years % 12 + 1}-й от исходного); "
                      f"управитель года (трад.) {BODY_RU[lord]}; месяц {m + 1}: {SIGNS_RU[ms]}"})

    variant = (f"тропический зодиак; транзитные орбисы {transit_orbs!r}; прогрессии 1 сут = 1 год "
               f"({Y} сут); углы {progression_angles}; дуга {arc}; соляр {sr_zodiac}, "
               f"{'место рождения' if sr_where == 'birthplace' else 'релокация'}; дома {HOUSE_SYSTEMS[used_hsys]}; "
               f"профекции от {profection_from}, целые знаки, трад. управители")
    return {
        "method": "western_forecast",
        "variant": variant,
        "inputs_used": {
            "birth_utc": nat["inputs_used"]["utc"], "birth_jd": round(jd_b, 6), "tz": nat["inputs_used"]["tz"],
            "lat": b.lat, "lon": b.lon, "place": b.place, "time_known": time_known,
            "on_date_utc": on_utc.isoformat(timespec="seconds"), "on_jd": round(jd_on, 6),
            "period": {"start_utc": _iso(p0), "end_utc": _iso(p1)},
            "options": {"transit_orbs": transit_orbs if not isinstance(transit_orbs, dict) else dict(transit_orbs),
                        "transit_aspects": transit_aspects, "hit_bodies": hb, "natal_points": natal_points,
                        "progression_angles": progression_angles, "year_length": year_length,
                        "progression_orb": progression_orb, "arc": arc, "sa_asc": sa_asc,
                        "direction_orb": direction_orb, "direction_aspects": direction_aspects,
                        "sr_place": sr_place, "sr_lat": sr_lat, "sr_lon": sr_lon, "sr_tz": sr_tz, "sr_year": sr_year,
                        "sr_zodiac": sr_zodiac, "profection_from": profection_from,
                        "profection_boundary": profection_boundary, "hsys": hsys, "node": node},
        },
        "warnings": warnings,
        "natal": {"bodies": {p: {"lon": natal_lon[p], "pos": dms(natal_lon[p]),
                                 "house": nat["bodies"][p].get("house")} for p in PLANETS10 + ["north_node"]},
                  "asc": natal_lon.get("asc"), "mc": natal_lon.get("mc"), "armc": round(armc_n, 6) if armc_n else None,
                  "cusps": [round(c, 6) for c in cusps], "house_system": used_hsys},
        "age_years": round(age, 6),
        "transits": transits,
        "progressions": progressions,
        "solar_arc": solar_arc,
        "solar_return": sr_chart,
        "lunar_return": lunar_return,
        "profections": profections,
        "steps": steps,
    }


def _main(argv: list[str] | None = None) -> int:
    """CLI до регистрации метода в calculators/cli.py:
    python -m calculators.forecast_western --date 1990-05-15 --time 14:30 --place Москва --opt on_date=2026-10-14"""
    import json
    import sys

    from .cli import _options, _parse_args, build_input
    a = _parse_args(["forecast_western"] + list(sys.argv[1:] if argv is None else argv))
    print(json.dumps(calculate(build_input(a), **_options(a.opt)), ensure_ascii=False, indent=2, default=str))
    return 0


__all__ = ["calculate", "stations", "crossings", "NAIBOD", "YEAR_LENGTHS", "TRANSIT_ORB_SCHEMES",
           "PROGRESSION_ANGLE_METHODS", "LUNATION_PHASES"]

if __name__ == "__main__":
    raise SystemExit(_main())
