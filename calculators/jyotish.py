"""Джйотиш (ведическая астрология, школа Парашары): эталонный калькулятор.

Что считает:
* сидерические (нирайана) долготы 9 грах (Солнце…Сатурн, Раху, Кету) по аянамше
  Lahiri/Chitrapaksha (по умолчанию), Raman или KP (Krishnamurti);
* Лагну (сидерический асцендент), дома по целым знакам (по умолчанию) и бхава-чалит
  по Шрипати (Порфирий, Лагна = середина 1-го дома);
* накшатру и паду каждой грахи и Лагны, D9 (навамша), D10 (дашамша), варготтаму;
* достоинства (экзальтация/падение/мулатрикона/свой знак/отношение к диспозитору),
  сожжение (астангата), натуральные и составные (панчадха) дружбы;
* панчангу момента рождения: титхи, вару (от восхода!), накшатру, йогу, карану;
* Вимшоттари-дашу: баланс при рождении, махадаши, антардаши (+ пратьянтардаши по запросу).

Подробности и обоснование умолчаний: knowledge-base/07-jyotish.md.
"""
from __future__ import annotations

import math
from datetime import date, datetime, timedelta

import swisseph as swe

from .common import ephemeris as eph
from .common.time import BirthInput, normalize

# ---------------------------------------------------------------------------
# Справочные таблицы
# ---------------------------------------------------------------------------

NAK_SPAN = 360.0 / 27.0          # 13°20′
PADA_SPAN = NAK_SPAN / 4.0       # 3°20′
NAVAMSA_SPAN = 30.0 / 9.0        # 3°20′

SIGNS_RU = eph.SIGNS_RU
SIGNS_EN = eph.SIGNS_EN
SIGNS_SA = ["Mesha", "Vrishabha", "Mithuna", "Karka", "Simha", "Kanya",
            "Tula", "Vrishchika", "Dhanu", "Makara", "Kumbha", "Mina"]

GRAHAS = ["sun", "moon", "mars", "mercury", "jupiter", "venus", "saturn", "rahu", "ketu"]
GRAHA_RU = {"sun": "Солнце", "moon": "Луна", "mars": "Марс", "mercury": "Меркурий",
            "jupiter": "Юпитер", "venus": "Венера", "saturn": "Сатурн", "rahu": "Раху", "ketu": "Кету"}
GRAHA_SA = {"sun": "Surya", "moon": "Chandra", "mars": "Mangala", "mercury": "Budha",
            "jupiter": "Guru", "venus": "Shukra", "saturn": "Shani", "rahu": "Rahu", "ketu": "Ketu"}
GRAHA_ABBR = {"sun": "Су", "moon": "Лу", "mars": "Ма", "mercury": "Ме", "jupiter": "Юп",
              "venus": "Ве", "saturn": "Са", "rahu": "Ра", "ketu": "Ке"}

# Управители знаков (0 = Овен … 11 = Рыбы)
SIGN_LORDS = ["mars", "venus", "mercury", "moon", "sun", "mercury",
              "venus", "mars", "jupiter", "saturn", "saturn", "jupiter"]

# 27 накшатр: (санскрит, рус., управитель, божество, символ, гана)
NAKSHATRAS: list[tuple[str, str, str, str, str, str]] = [
    ("Ashvini", "Ашвини", "ketu", "Ашвины", "голова коня", "deva"),
    ("Bharani", "Бхарани", "venus", "Яма", "йони", "manushya"),
    ("Krittika", "Криттика", "sun", "Агни", "нож/бритва, пламя", "rakshasa"),
    ("Rohini", "Рохини", "moon", "Брахма (Праджапати)", "колесница, баньян", "manushya"),
    ("Mrigashira", "Мригашира", "mars", "Сома", "голова оленя", "deva"),
    ("Ardra", "Ардра", "rahu", "Рудра", "слеза, алмаз", "manushya"),
    ("Punarvasu", "Пунарвасу", "jupiter", "Адити", "лук и колчан", "deva"),
    ("Pushya", "Пушья", "saturn", "Брихаспати", "вымя коровы, лотос, круг", "deva"),
    ("Ashlesha", "Ашлеша", "mercury", "Наги (Сарпы)", "свернувшийся змей", "rakshasa"),
    ("Magha", "Магха", "ketu", "Питри (предки)", "царский трон", "rakshasa"),
    ("Purva Phalguni", "Пурва-Пхалгуни", "venus", "Бхага", "передние ножки ложа, гамак", "manushya"),
    ("Uttara Phalguni", "Уттара-Пхалгуни", "sun", "Арьяман", "задние ножки ложа", "manushya"),
    ("Hasta", "Хаста", "moon", "Савитар", "ладонь", "deva"),
    ("Chitra", "Читра", "mars", "Тваштар (Вишвакарман)", "сияющая жемчужина", "rakshasa"),
    ("Svati", "Свати", "rahu", "Ваю", "росток, коралл", "deva"),
    ("Vishakha", "Вишакха", "jupiter", "Индра и Агни", "триумфальная арка, гончарный круг", "rakshasa"),
    ("Anuradha", "Анурадха", "saturn", "Митра", "арка, лотос", "deva"),
    ("Jyeshtha", "Джйештха", "mercury", "Индра", "серьга-амулет, зонт", "rakshasa"),
    ("Mula", "Мула", "ketu", "Ниррити", "связка корней, слоновий анкус", "rakshasa"),
    ("Purva Ashadha", "Пурва-Ашадха", "venus", "Апас (воды)", "бивень слона, веер", "manushya"),
    ("Uttara Ashadha", "Уттара-Ашадха", "sun", "Вишведевы", "бивень слона, малое ложе", "manushya"),
    ("Shravana", "Шравана", "moon", "Вишну", "ухо, три следа", "deva"),
    ("Dhanishtha", "Дхаништха", "mars", "Восемь Васу", "барабан (мриданга), флейта", "rakshasa"),
    ("Shatabhisha", "Шатабхиша", "rahu", "Варуна", "пустой круг", "rakshasa"),
    ("Purva Bhadrapada", "Пурва-Бхадрапада", "jupiter", "Аджа Экапада", "мечи, передние ножки погребального ложа", "manushya"),
    ("Uttara Bhadrapada", "Уттара-Бхадрапада", "saturn", "Ахирбудхнья", "близнецы, задние ножки погребального ложа", "manushya"),
    ("Revati", "Ревати", "mercury", "Пушан", "рыба (пара рыб), барабан", "deva"),
]

# Вимшоттари: порядок управителей и длительности (лет), сумма 120
DASHA_ORDER = ["ketu", "venus", "sun", "moon", "mars", "rahu", "jupiter", "saturn", "mercury"]
DASHA_YEARS = {"ketu": 7, "venus": 20, "sun": 6, "moon": 10, "mars": 7,
               "rahu": 18, "jupiter": 16, "saturn": 19, "mercury": 17}
DASHA_TOTAL = 120

# Длина «года» даши в сутках. true_solar — год = полный оборот сидерического Солнца
YEAR_LENGTHS: dict[str, float | None] = {
    "gregorian": 365.2425,     # средний григорианский (по умолчанию)
    "julian": 365.25,          # юлианский
    "tropical": 365.24219,     # тропический
    "sidereal": 365.256363,    # средний сидерический
    "savana": 360.0,           # савана-год (360 суток), PVR Narasimha Rao в учебнике
    "true_solar": None,        # истинный сидерический солнечный год (как в JHora по данным PyJHora)
}

# Экзальтация: знак и градус глубочайшей экзальтации (BPHS 3.49–50); падение — 7-й знак, тот же градус
EXALTATION = {"sun": (0, 10.0), "moon": (1, 3.0), "mars": (9, 28.0), "mercury": (5, 15.0),
              "jupiter": (3, 5.0), "venus": (11, 27.0), "saturn": (6, 20.0)}
# Мулатрикона: (знак, от°, до°) (BPHS 3.51–54)
MOOLATRIKONA = {"sun": (4, 0.0, 20.0), "moon": (1, 3.0, 30.0), "mars": (0, 0.0, 12.0),
                "mercury": (5, 15.0, 20.0), "jupiter": (8, 0.0, 10.0), "venus": (6, 0.0, 15.0),
                "saturn": (10, 0.0, 20.0)}
OWN_SIGNS = {"sun": [4], "moon": [3], "mars": [0, 7], "mercury": [2, 5], "jupiter": [8, 11],
             "venus": [1, 6], "saturn": [9, 10]}

# Натуральная (найсаргика) дружба (BPHS 3.55): друзья / нейтралы / враги
NATURAL_FRIENDS = {
    "sun": (["moon", "mars", "jupiter"], ["mercury"], ["venus", "saturn"]),
    "moon": (["sun", "mercury"], ["mars", "jupiter", "venus", "saturn"], []),
    "mars": (["sun", "moon", "jupiter"], ["venus", "saturn"], ["mercury"]),
    "mercury": (["sun", "venus"], ["mars", "jupiter", "saturn"], ["moon"]),
    "jupiter": (["sun", "moon", "mars"], ["saturn"], ["mercury", "venus"]),
    "venus": (["mercury", "saturn"], ["mars", "jupiter"], ["sun", "moon"]),
    "saturn": (["mercury", "venus"], ["jupiter"], ["sun", "moon", "mars"]),
}

# Орбы сожжения (астангата), градусы от Солнца; для ретроградных Меркурия/Венеры — меньше
COMBUSTION_ORBS = {"moon": 12.0, "mars": 17.0, "mercury": 14.0, "jupiter": 11.0, "venus": 10.0, "saturn": 15.0}
COMBUSTION_ORBS_RETRO = {"mercury": 12.0, "venus": 8.0}

TITHI_NAMES = ["Pratipada", "Dvitiya", "Tritiya", "Chaturthi", "Panchami", "Shashthi", "Saptami",
               "Ashtami", "Navami", "Dashami", "Ekadashi", "Dvadashi", "Trayodashi", "Chaturdashi"]
TITHI_NAMES_RU = ["Пратипада", "Двития", "Тритья", "Чатуртхи", "Панчами", "Шаштхи", "Саптами",
                  "Аштами", "Навами", "Дашами", "Экадаши", "Двадаши", "Трайодаши", "Чатурдаши"]
YOGA_NAMES = ["Vishkambha", "Priti", "Ayushman", "Saubhagya", "Shobhana", "Atiganda", "Sukarma",
              "Dhriti", "Shula", "Ganda", "Vriddhi", "Dhruva", "Vyaghata", "Harshana", "Vajra",
              "Siddhi", "Vyatipata", "Variyana", "Parigha", "Shiva", "Siddha", "Sadhya", "Shubha",
              "Shukla", "Brahma", "Indra", "Vaidhriti"]
KARANA_MOVABLE = ["Bava", "Balava", "Kaulava", "Taitila", "Gara", "Vanija", "Vishti"]
VARA = [("Ravivara", "воскресенье", "sun"), ("Somavara", "понедельник", "moon"),
        ("Mangalavara", "вторник", "mars"), ("Budhavara", "среда", "mercury"),
        ("Guruvara", "четверг", "jupiter"), ("Shukravara", "пятница", "venus"),
        ("Shanivara", "суббота", "saturn")]

# Южноиндийская карта: знаки зафиксированы в клетках 4×4 (строка, столбец)
SOUTH_INDIAN_CELLS = {11: (0, 0), 0: (0, 1), 1: (0, 2), 2: (0, 3), 3: (1, 3), 4: (2, 3),
                      5: (3, 3), 6: (3, 2), 7: (3, 1), 8: (3, 0), 9: (2, 0), 10: (1, 0)}

AYANAMSA_LABELS = {"lahiri": "Lahiri (Chitrapaksha)", "raman": "B.V. Raman",
                   "krishnamurti": "Krishnamurti (KP, старая)", "fagan_bradley": "Fagan-Bradley (западная сидерическая)",
                   "true_citra": "True Chitrapaksha (Спика ровно 0° Весов)",
                   "krishnamurti_vp291": "Krishnamurti (KP, новая, VP291)",
                   "yukteshwar": "Sri Yukteshwar"}


# ---------------------------------------------------------------------------
# Вспомогательные функции
# ---------------------------------------------------------------------------

def dms(x: float, signed: bool = False) -> str:
    """Градусы → строка D°MM′SS″ (с округлением до секунды)."""
    neg = x < 0
    total = round(abs(x) * 3600)
    d, rem = divmod(total, 3600)
    m, s = divmod(rem, 60)
    out = f"{d}°{m:02d}′{s:02d}″"
    return ("-" + out) if (neg and signed) else out


def sign_dms(lon: float) -> str:
    """Долгота → «22°09′30″ Скорпион»."""
    lon %= 360.0
    s = int(lon // 30)
    return f"{dms(lon - 30 * s)} {SIGNS_RU[s]}"


def nakshatra_of(lon: float) -> dict:
    """Накшатра и пада по сидерической долготе."""
    lon %= 360.0
    n = int(lon // NAK_SPAN)
    within = lon - n * NAK_SPAN
    pada = int(within // PADA_SPAN) + 1
    sa, ru, lord, deity, symbol, gana = NAKSHATRAS[n]
    return {"index": n + 1, "name": sa, "name_ru": ru, "pada": pada, "lord": lord,
            "deity": deity, "symbol": symbol, "gana": gana,
            "degrees_in_nakshatra": round(within, 6), "fraction_elapsed": round(within / NAK_SPAN, 8)}


def navamsa_sign(lon: float) -> int:
    """D9: знак навамши = номер 3°20′-сегмента от 0° Овна по модулю 12.

    Эквивалентно правилу BPHS: подвижные знаки начинают счёт от себя, фиксированные —
    от 9-го, двойственные — от 5-го знака.
    """
    return int((lon % 360.0) // NAVAMSA_SPAN) % 12


def dasamsa_sign(lon: float) -> int:
    """D10: 10 частей по 3°; нечётные знаки считают от себя, чётные — от 9-го знака."""
    lon %= 360.0
    s = int(lon // 30)
    k = int((lon - 30 * s) // 3.0)
    start = s if s % 2 == 0 else (s + 8) % 12   # s%2==0 → нечётный знак (Овен=1)
    return (start + k) % 12


def natural_relation(planet: str, other: str) -> str:
    """Натуральное отношение planet → other: friend / neutral / enemy."""
    if planet == other:
        return "self"
    fr, ne, en = NATURAL_FRIENDS[planet]
    if other in fr:
        return "friend"
    if other in en:
        return "enemy"
    return "neutral"


def temporary_relation(sign_a: int, sign_b: int) -> str:
    """Временная (таткалика) дружба: B во 2,3,4,10,11,12 от A → друг, иначе враг (BPHS 3.56)."""
    h = (sign_b - sign_a) % 12 + 1
    return "friend" if h in (2, 3, 4, 10, 11, 12) else "enemy"


def compound_relation(natural: str, temporary: str) -> str:
    """Панчадха-майтри (BPHS 3.57–58)."""
    table = {("friend", "friend"): "great_friend", ("friend", "enemy"): "neutral",
             ("neutral", "friend"): "friend", ("neutral", "enemy"): "enemy",
             ("enemy", "friend"): "neutral", ("enemy", "enemy"): "great_enemy"}
    return table[(natural, temporary)]


def dignity_bphs(planet: str, lon: float) -> str:
    """Достоинство по градусам BPHS: exalted / debilitated / moolatrikona / own, иначе —
    натуральное отношение к управителю знака (friend / neutral / enemy)."""
    if planet not in EXALTATION:
        return "n/a"
    s = int((lon % 360) // 30)
    d = (lon % 360) - 30 * s
    ex_sign, _ = EXALTATION[planet]
    mt_sign, mt_from, mt_to = MOOLATRIKONA[planet]
    if s == ex_sign:
        # у Луны и Меркурия знак экзальтации совпадает со знаком мулатриконы
        if s == mt_sign:
            if d < mt_from:
                return "exalted"
            if d < mt_to:
                return "moolatrikona"
            return "own" if s in OWN_SIGNS[planet] else "exalted"
        return "exalted"
    if s == (ex_sign + 6) % 12:
        return "debilitated"
    if s == mt_sign and mt_from <= d < mt_to:
        return "moolatrikona"
    if s in OWN_SIGNS[planet]:
        return "own"
    return natural_relation(planet, SIGN_LORDS[s])


def relation_simple(planet: str, sign: int) -> str:
    """«Relation» как в таблицах AstroSage: знак экзальтации/падения/свой, иначе
    натуральное отношение к управителю знака (без мулатриконы и без градусов)."""
    if planet not in EXALTATION:
        return "-"
    ex_sign, _ = EXALTATION[planet]
    if sign == ex_sign:
        return "exalted"
    if sign == (ex_sign + 6) % 12:
        return "debilitated"
    if sign in OWN_SIGNS[planet]:
        return "own"
    return natural_relation(planet, SIGN_LORDS[sign])


def _angle_diff(a: float, b: float) -> float:
    """Кратчайшая угловая разность |a−b| в градусах (0…180)."""
    return abs((a - b + 180.0) % 360.0 - 180.0)


def _local_str(jd_ut: float, offset_hours: float) -> str:
    """JD (UT) → местное время 'YYYY-MM-DD HH:MM' (смещение пояса рождения)."""
    y, m, d, h = swe.revjul(jd_ut + offset_hours / 24.0, swe.GREG_CAL)
    base = datetime(y, m, d) + timedelta(hours=h)
    base = base + timedelta(seconds=30)  # округление до минуты
    return base.strftime("%Y-%m-%d %H:%M")


def years_to_ymd(years: float) -> str:
    """Дробные годы → «Y л M м D д» по традиционной разбивке 1 год = 12 мес. × 30 дн."""
    total = years * 360.0 + 1e-6          # в «днях по 30»; эпсилон против 7.9999… мес.
    y = int(total // 360)
    rem = total - 360 * y
    m = int(rem // 30)
    d = int(rem - 30 * m)
    return f"{y} г. {m} мес. {d} дн."


def _sid_sun(jd_ut: float, ayan: str) -> float:
    return eph.body_position(jd_ut, swe.SUN, ayan)["lon"]


class _DashaClock:
    """Перевод «лет даши от момента рождения» в юлианский день."""

    def __init__(self, jd_birth: float, year: str, ayan: str):
        if year not in YEAR_LENGTHS:
            raise ValueError(f"Неизвестная длина года даши: {year}. Варианты: {list(YEAR_LENGTHS)}")
        self.jd0 = jd_birth
        self.year = year
        self.ayan = ayan
        self.days = YEAR_LENGTHS[year]
        self.sun0 = _sid_sun(jd_birth, ayan) if year == "true_solar" else None

    def jd(self, years: float) -> float:
        if self.days is not None:
            return self.jd0 + years * self.days
        # истинный солнечный год: прошло N лет, когда сидерическое Солнце сместилось на N×360°
        target = self.sun0 + years * 360.0
        jd = self.jd0 + years * 365.256363
        for _ in range(8):
            cur = _sid_sun(jd, self.ayan)
            # разность в пределах ±180°, полное число оборотов задаёт начальное приближение
            delta = ((cur - target) + 180.0) % 360.0 - 180.0
            jd -= delta / 0.98564736
            if abs(delta) < 1e-7:
                break
        return jd


# ---------------------------------------------------------------------------
# Вимшоттари-даша
# ---------------------------------------------------------------------------

def _sub_periods(lord: str, start_y: float, length_y: float) -> list[tuple[str, float, float]]:
    """Делит период lord длиной length_y на 9 подпериодов, начиная с самого lord."""
    i0 = DASHA_ORDER.index(lord)
    out = []
    t = start_y
    for k in range(9):
        sub = DASHA_ORDER[(i0 + k) % 9]
        dur = length_y * DASHA_YEARS[sub] / DASHA_TOTAL
        out.append((sub, t, t + dur))
        t += dur
    return out


def vimshottari(moon_lon: float, jd_birth: float, offset_hours: float, year: str = "gregorian",
                ayan: str = "lahiri", levels: int = 2, on_date: str | None = None,
                cycles: int = 1, start_star: int = 1) -> dict:
    """Вимшоттари-даша от сидерической долготы Луны.

    levels: 1 — только махадаши, 2 — + антардаши, 3 — + пратьянтардаши.
    on_date: 'YYYY-MM-DD' — дополнительно вернуть текущие периоды на эту дату (полдень UT).
    start_star: 1 — от накшатры Луны (стандарт); 4 (кшема), 5 (утпанна), 8 (адхана) —
        вариации из учебника PVR Narasimha Rao (§16.4): первая даша принадлежит управителю
        N-й накшатры от Луны, доля остатка — та же, что у накшатры Луны.
    """
    clock = _DashaClock(jd_birth, year, ayan)
    nak = nakshatra_of(moon_lon)
    lord = NAKSHATRAS[(nak["index"] - 1 + start_star - 1) % 27][2]
    frac = nak["degrees_in_nakshatra"] / NAK_SPAN
    p = DASHA_YEARS[lord]
    elapsed = frac * p
    balance = p - elapsed
    i0 = DASHA_ORDER.index(lord)

    mds = []
    t = -elapsed
    for k in range(9 * cycles):
        md_lord = DASHA_ORDER[(i0 + k) % 9]
        length = DASHA_YEARS[md_lord]
        md = {"lord": md_lord, "lord_ru": GRAHA_RU[md_lord], "years": length,
              "start": _local_str(clock.jd(t), offset_hours),
              "end": _local_str(clock.jd(t + length), offset_hours),
              "start_jd_ut": round(clock.jd(t), 5), "end_jd_ut": round(clock.jd(t + length), 5)}
        if levels >= 2:
            ads = []
            for ad_lord, a0, a1 in _sub_periods(md_lord, t, length):
                ad = {"lord": ad_lord, "start": _local_str(clock.jd(a0), offset_hours),
                      "end": _local_str(clock.jd(a1), offset_hours),
                      "years": round(a1 - a0, 6)}
                if levels >= 3:
                    ad["pratyantardashas"] = [
                        {"lord": pl, "start": _local_str(clock.jd(p0), offset_hours),
                         "end": _local_str(clock.jd(p1), offset_hours)}
                        for pl, p0, p1 in _sub_periods(ad_lord, a0, a1 - a0)]
                ads.append(ad)
            md["antardashas"] = ads
        mds.append(md)
        t += length

    result = {
        "system": "vimshottari",
        "year_length": year,
        "year_days": YEAR_LENGTHS[year],
        "moon_nakshatra": nak["name"],
        "moon_nakshatra_index": nak["index"],
        "first_lord": lord,
        "start_star": start_star,
        "fraction_elapsed": round(frac, 8),
        "fraction_remaining": round(1 - frac, 8),
        "balance": {"lord": lord, "years": round(balance, 6), "ymd": years_to_ymd(balance),
                    "ends": _local_str(clock.jd(balance), offset_hours)},
        "mahadashas": mds,
    }

    if on_date:
        d = date.fromisoformat(on_date)
        jd_q = swe.julday(d.year, d.month, d.day, 12.0, swe.GREG_CAL)
        cur: dict = {"date": on_date}
        t = -elapsed
        for k in range(9 * cycles):
            md_lord = DASHA_ORDER[(i0 + k) % 9]
            length = DASHA_YEARS[md_lord]
            if clock.jd(t) <= jd_q < clock.jd(t + length):
                cur["mahadasha"] = md_lord
                for ad_lord, a0, a1 in _sub_periods(md_lord, t, length):
                    if clock.jd(a0) <= jd_q < clock.jd(a1):
                        cur["antardasha"] = ad_lord
                        cur["antardasha_period"] = [_local_str(clock.jd(a0), offset_hours),
                                                    _local_str(clock.jd(a1), offset_hours)]
                        for pl, p0, p1 in _sub_periods(ad_lord, a0, a1 - a0):
                            if clock.jd(p0) <= jd_q < clock.jd(p1):
                                cur["pratyantardasha"] = pl
                                cur["pratyantardasha_period"] = [_local_str(clock.jd(p0), offset_hours),
                                                                 _local_str(clock.jd(p1), offset_hours)]
                        break
                break
            t += length
        result["current"] = cur
    return result


# ---------------------------------------------------------------------------
# Панчанга
# ---------------------------------------------------------------------------

def _sunrise_before(jd_ut: float, lat: float, lon: float, method: str) -> float | None:
    """Последний восход Солнца до момента jd_ut (UT). None — если восхода нет (полярный день/ночь)."""
    rsmi = swe.CALC_RISE
    if method == "hindu":
        rsmi |= swe.BIT_HINDU_RISING     # центр диска, без рефракции
    geopos = (lon, lat, 0.0)

    def rise_after(t: float) -> float | None:
        try:
            res, tret = swe.rise_trans(t, swe.SUN, rsmi, geopos, 1013.25, 15.0, swe.FLG_SWIEPH)
        except swe.Error:
            return None
        return tret[0] if res == 0 else None

    r = rise_after(jd_ut - 1.5)
    if r is None or r > jd_ut:
        return None
    while True:
        r2 = rise_after(r + 0.01)
        if r2 is None or r2 > jd_ut:
            return r
        r = r2


def panchanga(jd_ut: float, sun_sid: float, moon_sid: float, offset_hours: float,
              lat: float | None, lon: float | None, sunrise_method: str = "hindu") -> dict:
    """Пять элементов панчанги на момент рождения."""
    warnings: list[str] = []
    elong = (moon_sid - sun_sid) % 360.0              # = тропическая элонгация (аянамша сокращается)
    t_idx = int(elong // 12.0)                        # 0..29
    paksha = "shukla" if t_idx < 15 else "krishna"
    if t_idx == 14:
        t_name, t_ru = "Purnima", "Пурнима (полнолуние)"
    elif t_idx == 29:
        t_name, t_ru = "Amavasya", "Амавасья (новолуние)"
    else:
        t_name, t_ru = TITHI_NAMES[t_idx % 15], TITHI_NAMES_RU[t_idx % 15]
    tithi = {"index": t_idx + 1, "paksha": paksha, "paksha_ru": "шукла (растущая)" if paksha == "shukla" else "кришна (убывающая)",
             "name": t_name, "name_ru": t_ru, "number_in_paksha": t_idx % 15 + 1,
             "elongation": round(elong, 6), "fraction_elapsed": round((elong - 12 * t_idx) / 12.0, 6)}

    y_val = (sun_sid + moon_sid) % 360.0
    y_idx = int(y_val // NAK_SPAN)
    yoga = {"index": y_idx + 1, "name": YOGA_NAMES[y_idx], "sum_longitude": round(y_val, 6),
            "fraction_elapsed": round((y_val - y_idx * NAK_SPAN) / NAK_SPAN, 6)}

    k = int(elong // 6.0)                             # 0..59 — номер половины титхи
    if k == 0:
        k_name = "Kimstughna"
    elif k == 57:
        k_name = "Shakuni"
    elif k == 58:
        k_name = "Chatushpada"
    elif k == 59:
        k_name = "Naga"
    else:
        k_name = KARANA_MOVABLE[(k - 1) % 7]
    karana = {"index": k + 1, "name": k_name, "fixed": k in (0, 57, 58, 59)}

    # вара: день недели ВОСХОДА, предшествующего рождению
    civil_dow = int(math.floor(jd_ut + offset_hours / 24.0 + 0.5) + 1) % 7   # 0 = воскресенье
    sunrise_jd = None
    if lat is not None and lon is not None:
        sunrise_jd = _sunrise_before(jd_ut, lat, lon, sunrise_method)
    if sunrise_jd is None:
        vara_dow = civil_dow
        if lat is None or lon is None:
            warnings.append("Нет координат: вара взята по гражданскому дню недели (без учёта восхода).")
        else:
            warnings.append("Не удалось найти восход (полярные широты): вара по гражданскому дню.")
    else:
        vara_dow = int(math.floor(sunrise_jd + offset_hours / 24.0 + 0.5) + 1) % 7
    vsa, vru, vlord = VARA[vara_dow]
    vara = {"index": vara_dow, "name": vsa, "name_ru": vru, "lord": vlord,
            "civil_weekday_ru": VARA[civil_dow][1],
            "differs_from_civil": vara_dow != civil_dow,
            "sunrise_local": _local_str(sunrise_jd, offset_hours) if sunrise_jd else None,
            "sunrise_method": sunrise_method}
    nak = nakshatra_of(moon_sid)
    return {"tithi": tithi, "vara": vara,
            "nakshatra": {"index": nak["index"], "name": nak["name"], "name_ru": nak["name_ru"],
                          "pada": nak["pada"], "lord": nak["lord"]},
            "yoga": yoga, "karana": karana, "_warnings": warnings}


# ---------------------------------------------------------------------------
# Основной расчёт
# ---------------------------------------------------------------------------

def _graha_record(name: str, pos: dict, lagna_sign: int | None, sun_lon: float, ayan_true: float) -> dict:
    lon = pos["lon"] % 360.0
    s = int(lon // 30)
    nak = nakshatra_of(lon)
    rec = {
        "name": name, "name_ru": GRAHA_RU[name], "name_sa": GRAHA_SA[name],
        "lon": round(lon, 6), "lon_tropical": round((lon + ayan_true) % 360.0, 6),
        "sign": s + 1, "sign_ru": SIGNS_RU[s], "sign_sa": SIGNS_SA[s],
        "deg_in_sign": round(lon - 30 * s, 6), "position": sign_dms(lon),
        "speed": round(pos["speed"], 6), "retrograde": bool(pos["speed"] < 0),
        "nakshatra": nak["name"], "nakshatra_ru": nak["name_ru"], "nakshatra_index": nak["index"],
        "pada": nak["pada"], "nakshatra_lord": nak["lord"],
        "house": ((s - lagna_sign) % 12 + 1) if lagna_sign is not None else None,
        "d9_sign": navamsa_sign(lon) + 1, "d9_sign_ru": SIGNS_RU[navamsa_sign(lon)],
        "d10_sign": dasamsa_sign(lon) + 1, "d10_sign_ru": SIGNS_RU[dasamsa_sign(lon)],
        "vargottama": navamsa_sign(lon) == s,
        "sign_lord": SIGN_LORDS[s],
    }
    if name in EXALTATION:
        rec["dignity"] = dignity_bphs(name, lon)
        rec["relation"] = relation_simple(name, s)
        rec["natural_relation_to_sign_lord"] = natural_relation(name, SIGN_LORDS[s])
        if name != "sun":
            orb = COMBUSTION_ORBS[name]
            if rec["retrograde"] and name in COMBUSTION_ORBS_RETRO:
                orb = COMBUSTION_ORBS_RETRO[name]
            sep = _angle_diff(lon, sun_lon)
            rec["distance_from_sun"] = round(sep, 4)
            rec["combust"] = sep < orb
        else:
            rec["combust"] = False
    else:
        rec["dignity"] = "n/a"
        rec["relation"] = "-"
        rec["combust"] = False
    return rec


def _south_indian_ascii(content: dict[int, list[str]]) -> str:
    """Южноиндийская карта ASCII (знаки фиксированы, Рыбы — левый верхний угол)."""
    w = 14
    cell = {}
    for s, (r, c) in SOUTH_INDIAN_CELLS.items():
        cell[(r, c)] = (SIGNS_RU[s][:3] + ": " + " ".join(content.get(s, [])))[:w].ljust(w)
    full = "+" + "+".join(["-" * w] * 4) + "+"
    mid = "+" + "-" * w + "+" + " " * (2 * w + 1) + "+" + "-" * w + "+"
    rows = [full, "|" + "|".join(cell[(0, c)] for c in range(4)) + "|", full]
    for r in (1, 2):
        rows.append("|" + cell[(r, 0)] + "|" + " " * (2 * w + 1) + "|" + cell[(r, 3)] + "|")
        rows.append(mid if r == 1 else full)
    rows += ["|" + "|".join(cell[(3, c)] for c in range(4)) + "|", full]
    return "\n".join(rows)


def calculate(b: BirthInput, ayanamsa: str = "lahiri", node: str = "mean",
              dasha_year: str = "gregorian", dasha_levels: int = 2, on_date: str | None = None,
              dasha_start_star: int = 1,
              bhava_system: str = "sripati", sunrise_method: str = "hindu",
              include_outer: bool = False, **_ignored) -> dict:
    """Ведическая натальная карта (D1, D9, D10), панчанга и Вимшоттари-даша.

    Параметры:
      ayanamsa: 'lahiri' (по умолчанию) | 'raman' | 'krishnamurti' | 'krishnamurti_vp291' |
                'true_citra' | 'yukteshwar' | 'fagan_bradley'
      node: 'mean' (по умолчанию, средний узел) | 'true' (истинный)
      dasha_year: 'gregorian' (365.2425, по умолчанию) | 'julian' (365.25) | 'tropical' |
                  'sidereal' (365.256363) | 'savana' (360) | 'true_solar' (как JHora)
      dasha_levels: 1/2/3 — махадаши / + антардаши / + пратьянтардаши
      on_date: 'YYYY-MM-DD' — показать периоды даши, действующие на эту дату
      dasha_start_star: 1 (от накшатры Луны, стандарт) | 4 | 5 | 8 (вариации PVR)
      bhava_system: 'sripati' (Порфирий, Лагна = середина 1-го дома) | 'placidus' (KP,
                  куспид = начало дома) | 'equal' (равные от Лагны как середины)
      sunrise_method: 'hindu' (центр диска без рефракции, по умолчанию — как JHora/Prokerala) |
                  'apparent' (верхний край + рефракция, гражданский восход)
      include_outer: добавить Уран/Нептун/Плутон (в классический анализ не входят)
    """
    if ayanamsa not in eph.AYANAMSAS or ayanamsa not in AYANAMSA_LABELS:
        raise ValueError(f"Аянамша {ayanamsa!r} не поддерживается: "
                         f"{[k for k in eph.AYANAMSAS if k in AYANAMSA_LABELS]}")
    if isinstance(node, bool):              # CLI: --opt node=true превращается в True
        node = "true" if node else "mean"
    if node not in ("mean", "true"):
        raise ValueError("node: 'mean' или 'true'")
    if bhava_system not in ("sripati", "placidus", "equal"):
        raise ValueError("bhava_system: 'sripati' | 'placidus' | 'equal'")
    if sunrise_method not in ("hindu", "apparent"):
        raise ValueError("sunrise_method: 'hindu' | 'apparent'")
    if dasha_start_star not in (1, 4, 5, 8):
        raise ValueError("dasha_start_star: 1 | 4 | 5 | 8")
    warnings: list[str] = []
    steps: list[str] = []
    if _ignored:
        warnings.append(f"Неизвестные опции проигнорированы: {sorted(_ignored)}")

    time_known = b.has_time
    if not time_known:
        b_calc = BirthInput(b.year, b.month, b.day, 12, 0, tz=b.tz, lat=b.lat, lon=b.lon, place=b.place)
        warnings.append("Время рождения неизвестно: карта построена на 12:00 местного времени. Лагна, дома, "
                        "D9-лагна и вара не определяются; Луна за сутки проходит ~12–15° — накшатра и баланс "
                        "даши могут быть неверны (см. moon_range_for_day).")
    else:
        b_calc = b
    if b_calc.tz is None:
        raise ValueError("Нужен часовой пояс (tz) или место (place) — без них нельзя перевести время в UT.")
    nt = normalize(b_calc)
    warnings += nt.warnings
    jd = nt.jd_ut
    off = nt.utc_offset_hours
    has_place = b_calc.lat is not None and b_calc.lon is not None
    if not has_place:
        warnings.append("Нет координат места: Лагна, дома и восход (вара) не определяются.")

    local_fmt = "%Y-%m-%d %H:%M:%S" if nt.local.second else "%Y-%m-%d %H:%M"
    steps.append(f"1. Местное время {nt.local.strftime(local_fmt)} (смещение {off:+.4f} ч, источник {nt.offset_source}) → "
                 f"UT {nt.utc:%Y-%m-%d %H:%M:%S}, JD(UT) = {jd:.6f}.")

    # --- аянамша
    ayan_mean = eph.ayanamsa(jd, ayanamsa)
    trop = eph.planet_positions(jd, sidereal=None, node=node)
    sid = eph.planet_positions(jd, sidereal=ayanamsa, node=node)
    ayan_true = (trop["sun"]["lon"] - sid["sun"]["lon"]) % 360.0
    comparison = {key: {"mean": round(eph.ayanamsa(jd, key), 6), "true": round(eph.ayanamsa(jd, key, true=True), 6)}
                  for key in ("lahiri", "raman", "krishnamurti")}
    swe.set_sid_mode(eph.AYANAMSAS[ayanamsa])   # eph.ayanamsa меняет глобальный режим — вернуть выбранный
    steps.append(f"2. Аянамша {AYANAMSA_LABELS[ayanamsa]}: средняя {dms(ayan_mean)}, истинная (с нутацией) "
                 f"{dms(ayan_true)}. Сидерическая долгота = тропическая − истинная аянамша.")

    # --- Лагна
    lagna = None
    lagna_sign = None
    bhava = None
    if time_known and has_place:
        h_sid = eph.houses(jd, b_calc.lat, b_calc.lon, "W", sidereal=ayanamsa)
        h_trop = eph.houses(jd, b_calc.lat, b_calc.lon, "W")
        asc = h_sid["asc"] % 360.0
        lagna_sign = int(asc // 30)
        lnak = nakshatra_of(asc)
        lagna = {"lon": round(asc, 6), "lon_tropical": round(h_trop["asc"], 6), "position": sign_dms(asc),
                 "sign": lagna_sign + 1, "sign_ru": SIGNS_RU[lagna_sign], "sign_sa": SIGNS_SA[lagna_sign],
                 "deg_in_sign": round(asc - 30 * lagna_sign, 6),
                 "nakshatra": lnak["name"], "nakshatra_ru": lnak["name_ru"], "pada": lnak["pada"],
                 "nakshatra_lord": lnak["lord"], "lord": SIGN_LORDS[lagna_sign],
                 "d9_sign": navamsa_sign(asc) + 1, "d9_sign_ru": SIGNS_RU[navamsa_sign(asc)],
                 "d10_sign": dasamsa_sign(asc) + 1, "d10_sign_ru": SIGNS_RU[dasamsa_sign(asc)],
                 "mc_sidereal": round(h_sid["mc"] % 360.0, 6)}
        steps.append(f"3. Тропический ASC {sign_dms(h_trop['asc'])} (RAMC {h_sid['armc']:.4f}°) → сидерическая Лагна "
                     f"{sign_dms(asc)} ({lnak['name']} пада {lnak['pada']}).")
        dd = asc - 30 * lagna_sign
        if dd < 1.0 or dd > 29.0:
            warnings.append(f"Лагна в {dd:.2f}° знака — у границы: ошибка времени в ±4 мин может сменить знак Лагны.")
        # бхава-чалит
        hs = {"sripati": "O", "placidus": "P", "equal": "E"}[bhava_system]
        hb = eph.houses(jd, b_calc.lat, b_calc.lon, hs, sidereal=ayanamsa)
        cusps = [c % 360.0 for c in hb["cusps"]]
        if bhava_system in ("sripati", "equal"):
            madhya = cusps if bhava_system == "sripati" else [(asc + 30 * i) % 360.0 for i in range(12)]
            starts = []
            for i in range(12):
                prev = madhya[i - 1]
                cur = madhya[i]
                arc = (cur - prev) % 360.0
                starts.append((prev + arc / 2.0) % 360.0)   # сандхи между (i-1) и i
        else:
            madhya = None
            starts = cusps
        bhava = {"system": bhava_system,
                 "bhava_madhya": [round(x, 4) for x in madhya] if madhya else None,
                 "bhava_start": [round(x, 4) for x in starts]}
    elif not time_known:
        steps.append("3. Лагна не вычисляется (время неизвестно); дома ниже — от знака Луны (Чандра-лагна).")

    def bhava_of(lon_: float) -> int | None:
        if bhava is None:
            return None
        st = bhava["bhava_start"]
        for i in range(12):
            a, z = st[i], st[(i + 1) % 12]
            if (lon_ - a) % 360.0 < (z - a) % 360.0:
                return i + 1
        return None

    # --- грахи
    sun_lon = sid["sun"]["lon"]
    ref_sign = lagna_sign if lagna_sign is not None else int(sid["moon"]["lon"] // 30)
    grahas: dict[str, dict] = {}
    for g in GRAHAS[:7]:
        grahas[g] = _graha_record(g, sid[g], ref_sign, sun_lon, ayan_true)
    grahas["rahu"] = _graha_record("rahu", sid["north_node"], ref_sign, sun_lon, ayan_true)
    ketu_pos = dict(sid["north_node"])
    ketu_pos["lon"] = (sid["north_node"]["lon"] + 180.0) % 360.0
    grahas["ketu"] = _graha_record("ketu", ketu_pos, ref_sign, sun_lon, ayan_true)
    for g in GRAHAS:
        grahas[g]["bhava"] = bhava_of(grahas[g]["lon"])
    # составная дружба с диспозитором
    for g in GRAHAS[:7]:
        lord = grahas[g]["sign_lord"]
        if lord == g:
            grahas[g]["compound_relation_to_sign_lord"] = "self"
        else:
            nat = natural_relation(g, lord)
            tmp = temporary_relation(grahas[g]["sign"] - 1, grahas[lord]["sign"] - 1)
            grahas[g]["compound_relation_to_sign_lord"] = compound_relation(nat, tmp)
    steps.append("4. Грахи (сидерически, " + ("средний" if node == "mean" else "истинный") + " узел): " +
                 "; ".join(f"{GRAHA_RU[g]} {grahas[g]['position']} ({grahas[g]['nakshatra']}-{grahas[g]['pada']})"
                           for g in GRAHAS) + ".")

    outer = None
    if include_outer:
        outer = {g: {"lon": round(sid[g]["lon"], 6), "position": sign_dms(sid[g]["lon"]),
                     "nakshatra": nakshatra_of(sid[g]["lon"])["name"], "pada": nakshatra_of(sid[g]["lon"])["pada"],
                     "retrograde": sid[g]["retro"]} for g in ("uranus", "neptune", "pluto")}

    # --- дома (целые знаки)
    houses_ws = []
    for i in range(12):
        s = (ref_sign + i) % 12
        houses_ws.append({"house": i + 1, "sign": s + 1, "sign_ru": SIGNS_RU[s], "lord": SIGN_LORDS[s],
                          "occupants": [g for g in GRAHAS if grahas[g]["sign"] - 1 == s]})

    # --- D9 / D10
    def varga(fn) -> dict:
        signs = {g: fn(grahas[g]["lon"]) + 1 for g in GRAHAS}
        if lagna is not None:
            signs = {"lagna": fn(lagna["lon"]) + 1, **signs}
        return {k: {"sign": v, "sign_ru": SIGNS_RU[v - 1]} for k, v in signs.items()}

    d9 = varga(navamsa_sign)
    d10 = varga(dasamsa_sign)
    m = grahas["moon"]
    steps.append(f"5. D9 Луны: долгота {m['lon']:.4f}° / 3.3333° = сегмент {int(m['lon'] // NAVAMSA_SPAN)}, "
                 f"mod 12 = {navamsa_sign(m['lon'])} → {m['d9_sign_ru']}.")

    # --- даша
    dasha = vimshottari(m["lon"], jd, off, year=dasha_year, ayan=ayanamsa, levels=dasha_levels, on_date=on_date,
                        start_star=dasha_start_star)
    steps.append(f"6. Вимшоттари: Луна в {m['nakshatra']} (№{m['nakshatra_index']}, управитель {GRAHA_RU[dasha['first_lord']]}), "
                 f"пройдено {dasha['fraction_elapsed']:.6f} накшатры; баланс = (1 − {dasha['fraction_elapsed']:.6f}) × "
                 f"{DASHA_YEARS[dasha['first_lord']]} = {dasha['balance']['years']:.4f} г. ({dasha['balance']['ymd']}), "
                 f"конец первой махадаши {dasha['balance']['ends']}; год = {dasha_year}.")
    within = m["lon"] % NAK_SPAN
    if within < 0.1 or within > NAK_SPAN - 0.1:
        warnings.append("Луна в пределах 6′ от границы накшатры: при ошибке времени ±10 мин меняется управитель первой даши.")

    # --- панчанга
    pan = panchanga(jd, sid["sun"]["lon"], sid["moon"]["lon"], off,
                    b_calc.lat if time_known else None, b_calc.lon if time_known else None, sunrise_method)
    pw = pan.pop("_warnings")
    warnings += pw if time_known else []
    if not time_known:
        pan["vara"]["note"] = "Время неизвестно: вара по гражданскому дню."
    steps.append(f"7. Панчанга: титхи {pan['tithi']['index']} ({pan['tithi']['name']}, {pan['tithi']['paksha']}), "
                 f"вара {pan['vara']['name']} (восход {pan['vara']['sunrise_local']}), накшатра {pan['nakshatra']['name']}, "
                 f"йога {pan['yoga']['name']}, карана {pan['karana']['name']}.")

    # --- раскладки карт
    content: dict[int, list[str]] = {}
    if lagna_sign is not None:
        content.setdefault(lagna_sign, []).append("Лг")
    for g in GRAHAS:
        content.setdefault(grahas[g]["sign"] - 1, []).append(GRAHA_ABBR[g])
    south = [["" for _ in range(4)] for _ in range(4)]
    for s, (r, c) in SOUTH_INDIAN_CELLS.items():
        south[r][c] = SIGNS_RU[s] + (": " + " ".join(content[s]) if s in content else "")
    north = [{"house": i + 1, "sign_number": (ref_sign + i) % 12 + 1,
              "contents": content.get((ref_sign + i) % 12, [])} for i in range(12)]

    moon_range = None
    if not time_known:
        lo = BirthInput(b.year, b.month, b.day, 0, 0, tz=b.tz, lat=b.lat, lon=b.lon, place=b.place)
        hi = BirthInput(b.year, b.month, b.day, 23, 59, tz=b.tz, lat=b.lat, lon=b.lon, place=b.place)
        m0 = eph.planet_positions(normalize(lo).jd_ut, sidereal=ayanamsa, node=node)["moon"]["lon"]
        m1 = eph.planet_positions(normalize(hi).jd_ut, sidereal=ayanamsa, node=node)["moon"]["lon"]
        moon_range = {"00:00": {"position": sign_dms(m0), "nakshatra": nakshatra_of(m0)["name"]},
                      "23:59": {"position": sign_dms(m1), "nakshatra": nakshatra_of(m1)["name"]}}

    variant = (f"Парашари; аянамша {AYANAMSA_LABELS[ayanamsa]}; узлы {node}; дома — целые знаки; "
               f"бхава-чалит {bhava_system}; год даши {dasha_year}")
    return {
        "method": "jyotish",
        "variant": variant,
        "inputs_used": {
            "date": f"{b.year:04d}-{b.month:02d}-{b.day:02d}",
            "date_julian_input": ("{:04d}-{:02d}-{:02d}".format(*b.julian_date)
                                  if getattr(b, "julian_date", None) else None),
            "time": f"{b_calc.hour:02d}:{(b_calc.minute or 0):02d}"
                    + (f":{b_calc.second:02d}" if getattr(b_calc, "second", 0) else "")
                    + ("" if time_known else " (подставлено)"),
            "tz": b_calc.tz, "lat": b_calc.lat, "lon": b_calc.lon, "place": b.place,
            "utc": nt.utc.isoformat(), "jd_ut": round(jd, 6), "utc_offset_hours": round(off, 6),
            "offset_source": nt.offset_source,
            "options": {"ayanamsa": ayanamsa, "node": node, "dasha_year": dasha_year,
                        "dasha_start_star": dasha_start_star,
                        "bhava_system": bhava_system, "sunrise_method": sunrise_method},
        },
        "warnings": warnings,
        "ayanamsa": {"name": ayanamsa, "label": AYANAMSA_LABELS[ayanamsa],
                     "mean": round(ayan_mean, 6), "true": round(ayan_true, 6),
                     "mean_dms": dms(ayan_mean), "true_dms": dms(ayan_true), "comparison": comparison},
        "lagna": lagna,
        "grahas": grahas,
        "outer_planets": outer,
        "houses_whole_sign": houses_ws,
        "houses_reference": "lagna" if lagna_sign is not None else "moon (chandra lagna)",
        "bhava_chalit": bhava,
        "moon_sign": {"sign": m["sign"], "sign_ru": m["sign_ru"], "sign_sa": m["sign_sa"]},
        "janma_nakshatra": {"name": m["nakshatra"], "name_ru": m["nakshatra_ru"], "index": m["nakshatra_index"],
                            "pada": m["pada"], "lord": m["nakshatra_lord"],
                            "deity": NAKSHATRAS[m["nakshatra_index"] - 1][3],
                            "symbol": NAKSHATRAS[m["nakshatra_index"] - 1][4],
                            "gana": NAKSHATRAS[m["nakshatra_index"] - 1][5]},
        "d9": d9,
        "d10": d10,
        "panchanga": pan,
        "dasha": dasha,
        "layout": {"south_indian_grid": south, "north_indian_houses": north,
                   "south_indian_ascii": _south_indian_ascii(content)},
        "moon_range_for_day": moon_range,
        "steps": steps,
    }


__all__ = ["calculate", "vimshottari", "panchanga", "nakshatra_of", "navamsa_sign", "dasamsa_sign",
           "dignity_bphs", "relation_simple", "NAKSHATRAS", "DASHA_ORDER", "DASHA_YEARS", "YEAR_LENGTHS"]
