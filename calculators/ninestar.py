"""Девятизвёздная Ки (九星気学 / 紫白九星), число Гуа (命卦, школа Восьми Дворцов 八宅)
и китайский зодиак (животное и стихия года).

Подробное описание алгоритма, таблицы, расхождения школ и источники лежат
в knowledge-base/03-nine-star-ki-gua.md.

Главные правила по умолчанию:
* Год Девятизвёздной Ки и Гуа начинается в момент Личунь (立春), когда видимая
  тропическая долгота Солнца равна 315°. Сравнение ведётся в UT по точному моменту,
  если известны время и часовой пояс. Если их нет, сравниваются даты, а день Личуня
  относится к новому году.
* Месяц определяется по «узловым» солнечным терминам цзе (節): 315°+30°·k.
* Год популярного китайского зодиака (животное, стихия) меняется в китайский Новый год
  (春节) по календарю КНР (UTC+8). Вариант по Личуню выдаётся отдельно (`zodiac_solar`).
"""
from __future__ import annotations

import re
from datetime import date, datetime, timedelta, timezone
from functools import lru_cache
from zoneinfo import ZoneInfo

from .common.ephemeris import find_sun_longitude, sun_longitude
from .common.time import BirthInput, jd_to_utc, julian_day_ut, normalize

UTC = timezone.utc

# ---------------------------------------------------------------------------
# Справочные таблицы
# ---------------------------------------------------------------------------

#: Атрибуты девяти звёзд (индекс = номер звезды). Триграммы и стороны света
#: даны по «Посленебесному» (後天) порядку Ло Шу.
STARS: dict[int, dict] = {
    1: {"ja": "一白水星", "ru": "Белая Вода", "en": "1 White Water", "element": "Вода", "element_en": "water",
        "color": "белый", "trigram": "☵ 坎 Кань (Вода)", "trigram_key": "kan", "direction": "Север", "dir": "N",
        "family": "средний сын", "xuan_kong": "贪狼 Тань Лан", "trigram_yin_yang": "ян"},
    2: {"ja": "二黒土星", "ru": "Чёрная Земля", "en": "2 Black Earth", "element": "Земля", "element_en": "earth",
        "color": "чёрный", "trigram": "☷ 坤 Кунь (Земля)", "trigram_key": "kun", "direction": "Юго-запад", "dir": "SW",
        "family": "мать", "xuan_kong": "巨门 Цзюй Мэнь", "trigram_yin_yang": "инь"},
    3: {"ja": "三碧木星", "ru": "Изумрудное (ярко-зелёное) Дерево", "en": "3 Jade Wood", "element": "Дерево",
        "element_en": "wood", "color": "изумрудный (碧)", "trigram": "☳ 震 Чжэнь (Гром)", "trigram_key": "zhen",
        "direction": "Восток", "dir": "E", "family": "старший сын", "xuan_kong": "禄存 Лу Цунь", "trigram_yin_yang": "ян"},
    4: {"ja": "四緑木星", "ru": "Зелёное Дерево", "en": "4 Green Wood", "element": "Дерево", "element_en": "wood",
        "color": "зелёный", "trigram": "☴ 巽 Сюнь (Ветер)", "trigram_key": "xun", "direction": "Юго-восток", "dir": "SE",
        "family": "старшая дочь", "xuan_kong": "文曲 Вэнь Цюй", "trigram_yin_yang": "инь"},
    5: {"ja": "五黄土星", "ru": "Жёлтая Земля", "en": "5 Yellow Earth", "element": "Земля", "element_en": "earth",
        "color": "жёлтый", "trigram": "— (центр, 太極)", "trigram_key": None, "direction": "Центр", "dir": "C",
        "family": "— (центр; член семьи не закреплён)", "xuan_kong": "廉贞 Лянь Чжэнь", "trigram_yin_yang": "—"},
    6: {"ja": "六白金星", "ru": "Белый Металл", "en": "6 White Metal", "element": "Металл", "element_en": "metal",
        "color": "белый", "trigram": "☰ 乾 Цянь (Небо)", "trigram_key": "qian", "direction": "Северо-запад", "dir": "NW",
        "family": "отец", "xuan_kong": "武曲 У Цюй", "trigram_yin_yang": "ян"},
    7: {"ja": "七赤金星", "ru": "Красный Металл", "en": "7 Red Metal", "element": "Металл", "element_en": "metal",
        "color": "красный", "trigram": "☱ 兌 Дуй (Озеро)", "trigram_key": "dui", "direction": "Запад", "dir": "W",
        "family": "младшая дочь", "xuan_kong": "破军 По Цзюнь", "trigram_yin_yang": "инь"},
    8: {"ja": "八白土星", "ru": "Белая Земля", "en": "8 White Earth", "element": "Земля", "element_en": "earth",
        "color": "белый", "trigram": "☶ 艮 Гэнь (Гора)", "trigram_key": "gen", "direction": "Северо-восток", "dir": "NE",
        "family": "младший сын", "xuan_kong": "左辅 Цзо Фу", "trigram_yin_yang": "ян"},
    9: {"ja": "九紫火星", "ru": "Пурпурный Огонь", "en": "9 Purple Fire", "element": "Огонь", "element_en": "fire",
        "color": "пурпурный", "trigram": "☲ 離 Ли (Огонь)", "trigram_key": "li", "direction": "Юг", "dir": "S",
        "family": "средняя дочь", "xuan_kong": "右弼 Ю Би", "trigram_yin_yang": "инь"},
}

#: Дворцы Ло Шу (номер = базовое число дворца) — для «наклона» 傾斜宮.
PALACES: dict[int, str] = {1: "坎宮 (Север)", 2: "坤宮 (Юго-запад)", 3: "震宮 (Восток)", 4: "巽宮 (Юго-восток)",
                           5: "中宮 (Центр)", 6: "乾宮 (Северо-запад)", 7: "兌宮 (Запад)", 8: "艮宮 (Северо-восток)",
                           9: "離宮 (Юг)"}

#: Особый «наклон» при совпадении звезды года и месяца (中宮傾斜).
#: Источники: yakumoin.info/about/keisha, amenouranai.com/kyuseikigaku-keisha/ (совпадают).
CENTER_TENDENCY: dict[int, int | dict[str, int]] = {1: 9, 2: 6, 3: 4, 4: 3, 5: {"male": 7, "female": 6},
                                                    6: 2, 7: 8, 8: 7, 9: 1}

#: Звезда первого солнечного месяца (寅, начинается в Личунь) по группе звезды года.
#: 子午卯酉-годы (звёзды 1,4,7) → 8; 辰戌丑未 (3,6,9) → 5; 寅申巳亥 (2,5,8) → 2.
FIRST_MONTH_STAR = {1: 8, 4: 8, 7: 8, 3: 5, 6: 5, 9: 5, 2: 2, 5: 2, 8: 2}

#: Солнечные месяцы: индекс 0 = 寅 (Личунь, 315°) … 11 = 丑 (Сяохань, 285°).
SOLAR_MONTHS = [
    ("寅", "Тигр", "立春 Личунь", 315), ("卯", "Кролик", "驚蟄 Цзинчжэ", 345), ("辰", "Дракон", "清明 Цинмин", 15),
    ("巳", "Змея", "立夏 Лися", 45), ("午", "Лошадь", "芒種 Манчжун", 75), ("未", "Коза", "小暑 Сяошу", 105),
    ("申", "Обезьяна", "立秋 Лицю", 135), ("酉", "Петух", "白露 Байлу", 165), ("戌", "Собака", "寒露 Ханьлу", 195),
    ("亥", "Свинья", "立冬 Лидун", 225), ("子", "Крыса", "大雪 Дасюэ", 255), ("丑", "Бык", "小寒 Сяохань", 285),
]

STEMS = [("甲", "Цзя"), ("乙", "И"), ("丙", "Бин"), ("丁", "Дин"), ("戊", "У"),
         ("己", "Цзи"), ("庚", "Гэн"), ("辛", "Синь"), ("壬", "Жэнь"), ("癸", "Гуй")]
STEM_ELEMENT = ["Дерево", "Дерево", "Огонь", "Огонь", "Земля", "Земля", "Металл", "Металл", "Вода", "Вода"]
STEM_ELEMENT_EN = ["wood", "wood", "fire", "fire", "earth", "earth", "metal", "metal", "water", "water"]
#: Популярные в русскоязычной традиции «цвета года» по стихии ствола.
ELEMENT_COLOR_RU = {"Дерево": ("Зелёная (Синяя)", "Зелёный (Синий)"), "Огонь": ("Красная", "Красный"),
                    "Земля": ("Жёлтая", "Жёлтый"), "Металл": ("Белая", "Белый"), "Вода": ("Чёрная", "Чёрный")}
BRANCHES = [("子", "Крыса", "Rat", "Вода"), ("丑", "Бык", "Ox", "Земля"), ("寅", "Тигр", "Tiger", "Дерево"),
            ("卯", "Кролик (Кот)", "Rabbit", "Дерево"), ("辰", "Дракон", "Dragon", "Земля"),
            ("巳", "Змея", "Snake", "Огонь"), ("午", "Лошадь", "Horse", "Огонь"), ("未", "Коза (Овца)", "Goat", "Земля"),
            ("申", "Обезьяна", "Monkey", "Металл"), ("酉", "Петух", "Rooster", "Металл"),
            ("戌", "Собака", "Dog", "Земля"), ("亥", "Свинья (Кабан)", "Pig", "Вода")]

DIRECTIONS_RU = {"N": "Север", "NE": "Северо-восток", "E": "Восток", "SE": "Юго-восток",
                 "S": "Юг", "SW": "Юго-запад", "W": "Запад", "NW": "Северо-запад"}

#: Восемь направлений по школе Восьми Дворцов (八宅). Порядок ключей:
#: благоприятные 生气, 天医, 延年, 伏位; неблагоприятные 祸害, 五鬼, 六煞, 绝命.
GUA_DIRECTIONS: dict[int, dict[str, str]] = {
    1: {"sheng_qi": "SE", "tian_yi": "E", "yan_nian": "S", "fu_wei": "N",
        "huo_hai": "W", "wu_gui": "NE", "liu_sha": "NW", "jue_ming": "SW"},
    2: {"sheng_qi": "NE", "tian_yi": "W", "yan_nian": "NW", "fu_wei": "SW",
        "huo_hai": "E", "wu_gui": "SE", "liu_sha": "S", "jue_ming": "N"},
    3: {"sheng_qi": "S", "tian_yi": "N", "yan_nian": "SE", "fu_wei": "E",
        "huo_hai": "SW", "wu_gui": "NW", "liu_sha": "NE", "jue_ming": "W"},
    4: {"sheng_qi": "N", "tian_yi": "S", "yan_nian": "E", "fu_wei": "SE",
        "huo_hai": "NW", "wu_gui": "SW", "liu_sha": "W", "jue_ming": "NE"},
    6: {"sheng_qi": "W", "tian_yi": "NE", "yan_nian": "SW", "fu_wei": "NW",
        "huo_hai": "SE", "wu_gui": "E", "liu_sha": "N", "jue_ming": "S"},
    7: {"sheng_qi": "NW", "tian_yi": "SW", "yan_nian": "NE", "fu_wei": "W",
        "huo_hai": "N", "wu_gui": "S", "liu_sha": "SE", "jue_ming": "E"},
    8: {"sheng_qi": "SW", "tian_yi": "NW", "yan_nian": "W", "fu_wei": "NE",
        "huo_hai": "S", "wu_gui": "N", "liu_sha": "E", "jue_ming": "SE"},
    9: {"sheng_qi": "E", "tian_yi": "SE", "yan_nian": "N", "fu_wei": "S",
        "huo_hai": "NE", "wu_gui": "W", "liu_sha": "SW", "jue_ming": "NW"},
}
GUA_STAR_NAMES = {
    "sheng_qi": "生气 Шэн Ци", "tian_yi": "天医 Тянь И", "yan_nian": "延年 Янь Нянь", "fu_wei": "伏位 Фу Вэй",
    "huo_hai": "祸害 Хо Хай", "wu_gui": "五鬼 У Гуй", "liu_sha": "六煞 Лю Ша", "jue_ming": "绝命 Цзюэ Мин",
}
FAVORABLE_KEYS = ["sheng_qi", "tian_yi", "yan_nian", "fu_wei"]
UNFAVORABLE_KEYS = ["huo_hai", "wu_gui", "liu_sha", "jue_ming"]
EAST_GROUP = {1, 3, 4, 9}
WEST_GROUP = {2, 6, 7, 8}

#: Триграммы как тройки черт снизу вверх (1 = ян, 0 = инь) — для самопроверки таблицы 八宅.
TRIGRAM_LINES = {1: (0, 1, 0), 2: (0, 0, 0), 3: (1, 0, 0), 4: (0, 1, 1),
                 6: (1, 1, 1), 7: (1, 1, 0), 8: (0, 0, 1), 9: (1, 0, 1)}
GUA_DIR = {1: "N", 2: "SW", 3: "E", 4: "SE", 6: "NW", 7: "W", 8: "NE", 9: "S"}


# ---------------------------------------------------------------------------
# Базовые формулы
# ---------------------------------------------------------------------------

def _to9(n: int) -> int:
    """Привести целое к диапазону 1…9 (остаток 0 → 9)."""
    r = n % 9
    return 9 if r == 0 else r


def digital_root(n: int) -> int:
    """Цифровой корень (повторное сложение цифр), 0 → 0."""
    n = abs(n)
    return 0 if n == 0 else _to9(n)


def year_star(solar_year: int) -> int:
    """Звезда года (本命星) для солнечного года (начало — Личунь).

    Формула: (11 − Y mod 9) приведённое к 1…9. Эквивалентно «11 − цифровой корень года»
    (если > 9, вычесть 9) — так её дают ja.wikipedia «九星» и большинство калькуляторов.
    """
    return _to9(11 - solar_year % 9)


def month_star(year_star_number: int, solar_month_index: int) -> int:
    """Звезда месяца (月命星): индекс 0 = 寅 (с Личуня) … 11 = 丑 (январь)."""
    start = FIRST_MONTH_STAR[year_star_number]
    return _to9(start - solar_month_index)


def tendency_palace(principal: int, month: int, gender: str | None = None) -> dict:
    """«Наклон» (傾斜宮) / энергетическое число западной Девятизвёздной Ки.

    Звезду месяца ставим в центр Ло Шу (прямой полёт), ищем дворец, куда попала
    звезда года; номер дворца — это и есть число. При совпадении звёзд — особая таблица.
    """
    if principal != month:
        palace = (principal - month + 4) % 9 + 1
        return {"number": palace, "palace": PALACES[palace], "special_center_case": False}
    rule = CENTER_TENDENCY[principal]
    if isinstance(rule, dict):
        if gender in ("male", "female"):
            p = rule[gender]
            return {"number": p, "palace": PALACES[p], "special_center_case": True}
        return {"number": None, "palace": None, "special_center_case": True,
                "by_gender": {g: {"number": v, "palace": PALACES[v]} for g, v in rule.items()}}
    return {"number": rule, "palace": PALACES[rule], "special_center_case": True}


def gua_raw(solar_year: int, gender: str) -> int:
    """«Сырое» число Гуа (до замены 5): мужчины (11 − Y) mod 9, женщины (Y + 4) mod 9; 0 → 9."""
    if gender == "male":
        return _to9(11 - solar_year)
    if gender == "female":
        return _to9(solar_year + 4)
    raise ValueError("gender должен быть 'male' или 'female'")


def gua_number(solar_year: int, gender: str) -> int:
    """Число Гуа (命卦) с заменой 5: мужчинам → 2 (坤), женщинам → 8 (艮)."""
    raw = gua_raw(solar_year, gender)
    if raw == 5:
        return 2 if gender == "male" else 8
    return raw


def gua_century_formula(solar_year: int, gender: str) -> str:
    """Текст «школьной» формулы (через две последние цифры) для шагов расчёта."""
    yy = solar_year % 100
    r = digital_root(yy)
    if 1900 <= solar_year <= 1999:
        if gender == "male":
            v = 10 - r
            return f"1900-е, мужчина: 10 − ЦК({yy:02d})={r} → {v}" + (f" → {_to9(v)}" if v > 9 else "")
        v = r + 5
        return f"1900-е, женщина: ЦК({yy:02d})={r} + 5 = {v}" + (f" → {_to9(v)}" if v > 9 else "")
    if 2000 <= solar_year <= 2099:
        if gender == "male":
            v = 9 - r
            return f"2000-е, мужчина: 9 − ЦК({yy:02d})={r} → {v}" + (" → 9 (0 считается 9)" if v == 0 else "")
        v = r + 6
        return f"2000-е, женщина: ЦК({yy:02d})={r} + 6 = {v}" + (f" → {_to9(v)}" if v > 9 else "")
    return "вне 1900–2099: используется общая формула"


def eight_mansions(gua: int) -> dict:
    """Восемь направлений для числа Гуа (без 5)."""
    t = GUA_DIRECTIONS[gua]

    def item(k: str) -> dict:
        return {"key": k, "name": GUA_STAR_NAMES[k], "direction": t[k], "direction_ru": DIRECTIONS_RU[t[k]]}

    return {"favorable": [item(k) for k in FAVORABLE_KEYS],
            "unfavorable": [item(k) for k in UNFAVORABLE_KEYS]}


def eight_mansions_by_line_changes(gua: int) -> dict[str, str]:
    """Самопроверка таблицы 八宅 через «Большое странствие» (大游年): последовательная смена черт.

    Порядок: верхняя → 生气, средняя → 五鬼, нижняя → 延年, средняя → 六煞,
    верхняя → 祸害, средняя → 天医, нижняя → 绝命, средняя → 伏位 (возврат к исходной).
    """
    by_lines = {v: k for k, v in TRIGRAM_LINES.items()}
    lines = list(TRIGRAM_LINES[gua])
    seq = [(2, "sheng_qi"), (1, "wu_gui"), (0, "yan_nian"), (1, "liu_sha"),
           (2, "huo_hai"), (1, "tian_yi"), (0, "jue_ming"), (1, "fu_wei")]
    out: dict[str, str] = {}
    for pos, key in seq:
        lines[pos] ^= 1
        out[key] = GUA_DIR[by_lines[tuple(lines)]]
    return out


def sexagenary_year(year: int) -> dict:
    """Ствол, ветвь, животное, стихия, инь-ян и номер в 60-летнем цикле для года Y."""
    i = (year - 4) % 60
    s, br = i % 10, i % 12
    element = STEM_ELEMENT[s]
    animal = BRANCHES[br][1]
    yin_yang = "ян" if s % 2 == 0 else "инь"
    return {
        "year": year,
        "cycle_index": i + 1,            # 1 = 甲子 … 60 = 癸亥
        "ganzhi": STEMS[s][0] + BRANCHES[br][0],
        "ganzhi_ru": f"{STEMS[s][1]}-{['цзы', 'чоу', 'инь', 'мао', 'чэнь', 'сы', 'у', 'вэй', 'шэнь', 'ю', 'сюй', 'хай'][br]}",
        "stem": STEMS[s][0], "branch": BRANCHES[br][0],
        "animal": animal, "animal_en": BRANCHES[br][2],
        "element": element, "element_en": STEM_ELEMENT_EN[s],
        "yin_yang": yin_yang,
        "branch_fixed_element": BRANCHES[br][3],
        "popular_name_ru": f"{_color(element, animal)} {_adj(element, animal)} {animal}",
    }


def _is_fem(animal: str) -> bool:
    return animal.split(" ")[0] in ("Крыса", "Змея", "Лошадь", "Коза", "Обезьяна", "Собака", "Свинья")


def _color(element: str, animal: str) -> str:
    return ELEMENT_COLOR_RU[element][0 if _is_fem(animal) else 1]


def _adj(element: str, animal: str) -> str:
    """Прилагательное стихии с согласованием по роду популярного русского названия животного."""
    fem = _is_fem(animal)
    forms = {"Дерево": ("Деревянная", "Деревянный"), "Огонь": ("Огненная", "Огненный"),
             "Земля": ("Земляная", "Земляной"), "Металл": ("Металлическая", "Металлический"),
             "Вода": ("Водяная", "Водяной")}
    return forms[element][0 if fem else 1]


# ---------------------------------------------------------------------------
# Время, часовые пояса, моменты солнечных терминов
# ---------------------------------------------------------------------------

_FIXED_RE = re.compile(r"^(?:UTC|GMT)\s*([+-])?\s*(\d{1,2})(?::?(\d{2}))?$", re.I)


def _fixed_offset(tz: str) -> timedelta | None:
    s = tz.strip().upper()
    if s in ("UTC", "GMT"):
        return timedelta(0)
    m = _FIXED_RE.match(s)
    if not m:
        return None
    sign = -1 if m.group(1) == "-" else 1
    return sign * timedelta(hours=int(m.group(2)), minutes=int(m.group(3) or 0))


class _Zone:
    """Перевод UTC ↔ местное гражданское время для IANA-зоны, фиксированного смещения или LMT."""

    def __init__(self, tz: str | None, lon: float | None = None, force_offset_hours: float | None = None) -> None:
        self.label = tz or "UTC+08:00"
        self.zone: ZoneInfo | None = None
        self.offset: timedelta | None = None
        if force_offset_hours is not None:
            self.offset = timedelta(hours=force_offset_hours)
            self.label = f"{tz} (смещение {force_offset_hours:+.4f} ч)"
        elif tz is None:
            self.offset = timedelta(hours=8)
        elif tz.upper() == "LMT":
            if lon is None:
                raise ValueError("Для LMT нужна долгота.")
            self.offset = timedelta(hours=lon / 15.0)
        else:
            fo = _fixed_offset(tz)
            if fo is not None:
                self.offset = fo
            else:
                self.zone = ZoneInfo(tz)

    def to_local(self, utc: datetime) -> datetime:
        if self.zone is not None:
            return utc.astimezone(self.zone).replace(tzinfo=None)
        return (utc + self.offset).replace(tzinfo=None)

    def to_utc(self, local: datetime) -> datetime:
        if self.zone is not None:
            return local.replace(tzinfo=self.zone).astimezone(UTC)
        return (local - self.offset).replace(tzinfo=UTC)


def _jd(dt_utc: datetime) -> float:
    return julian_day_ut(dt_utc)


@lru_cache(maxsize=1024)
def li_chun(year: int) -> float:
    """Момент Личуня (Солнце 315°) григорианского года `year`, JD UT."""
    return find_sun_longitude(315.0, _jd(datetime(year, 2, 20, tzinfo=UTC)), search_back=True)


@lru_cache(maxsize=2048)
def solstice(year: int, kind: str) -> float:
    """Момент солнцестояния: kind='summer' (90°) или 'winter' (270°), JD UT."""
    if kind == "summer":
        return find_sun_longitude(90.0, _jd(datetime(year, 7, 10, tzinfo=UTC)), search_back=True)
    return find_sun_longitude(270.0, _jd(datetime(year, 12, 31, tzinfo=UTC)), search_back=True)


def lunar_new_year(year: int) -> date | None:
    """Дата китайского Нового года (春节) по календарю КНР (UTC+8), через lunar-python."""
    try:
        from lunar_python import Lunar
        s = Lunar.fromYmd(year, 1, 1).getSolar()
        return date(s.getYear(), s.getMonth(), s.getDay())
    except Exception:  # pragma: no cover - библиотека недоступна или год вне диапазона
        return None


def _fmt(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%d %H:%M")


def day_ganzhi_index(d: date) -> int:
    """Индекс циклического знака дня 0…59 (0 = 甲子). JDN + 49 (mod 60)."""
    jdn = d.toordinal() + 1721425
    return (jdn + 49) % 60


def ganzhi_name(i: int) -> str:
    return STEMS[i % 10][0] + BRANCHES[i % 12][0]


# ---------------------------------------------------------------------------
# Звезда дня (日家九星)
# ---------------------------------------------------------------------------

def _switch_jiazi(sol_date: date) -> date:
    """День 甲子, ближайший к дате солнцестояния (индекс ≤ 29 → предыдущий, иначе следующий)."""
    i = day_ganzhi_index(sol_date)
    return sol_date - timedelta(days=i) if i <= 29 else sol_date + timedelta(days=60 - i)


def day_star(d: date, method: str = "ja_leap", almanac_tz: str | None = None) -> dict:
    """Звезда дня.

    method:
      * 'ja_leap' — японское правило (ja.wikipedia «九星»): Ян-дунь (陽遁) с дня 甲子, ближайшего
        к зимнему солнцестоянию, звезда 1 по возрастанию; Инь-дунь (陰遁) с 甲子, ближайшего к
        летнему, звезда 9 по убыванию. Если между переключениями 240 дней, последние 60 — «閏»:
        в день 甲午 (210-й) начинается следующий дунь со звезды 7 (Ян) или 3 (Инь).
      * 'nearest_no_leap' — то же без «閏» (так считает lunar-python `getDayNineStar`).
    almanac_tz — пояс, в котором берётся дата солнцестояния ('ja_leap' → UTC+9 (JST),
    'nearest_no_leap' → UTC+8 (как lunar-python) по умолчанию).
    """
    if method not in ("ja_leap", "nearest_no_leap"):
        raise ValueError("method: 'ja_leap' или 'nearest_no_leap'")
    # Альманахи используют поясное время без летнего: Япония UTC+9, КНР UTC+8.
    tzname = almanac_tz or ("UTC+09:00" if method == "ja_leap" else "UTC+08:00")
    zone = _Zone(tzname)
    events: list[tuple[date, str, date]] = []
    for y in range(d.year - 2, d.year + 2):
        for kind, dun in (("summer", "yin"), ("winter", "yang")):
            sol_local = zone.to_local(jd_to_utc(solstice(y, kind))).date()
            events.append((_switch_jiazi(sol_local), dun, sol_local))
    events.sort()
    k = max(i for i, e in enumerate(events) if e[0] <= d)
    cur, nxt = events[k], events[k + 1]
    period = (nxt[0] - cur[0]).days
    n = (d - cur[0]).days
    dun, start, seg_start, leap = cur[1], (1 if cur[1] == "yang" else 9), cur[0], False
    if method == "ja_leap" and period > 200 and n >= 210:
        dun, start, leap = nxt[1], (7 if nxt[1] == "yang" else 3), True
        seg_start = cur[0] + timedelta(days=210)
        n -= 210
    star = _to9(start + n) if dun == "yang" else _to9(start - n)
    return {
        "number": star, "dun": dun, "dun_ru": "Ян-дунь (陽遁, по возрастанию)" if dun == "yang"
        else "Инь-дунь (陰遁, по убыванию)",
        "method": method, "almanac_tz": tzname,
        "day_ganzhi": ganzhi_name(day_ganzhi_index(d)),
        "segment_start": seg_start.isoformat(), "segment_start_star": start, "days_from_segment_start": n,
        "leap_segment": leap, "period_days": period,
        "solstice_date": cur[2].isoformat(), "switch_jiazi": cur[0].isoformat(),
    }


# ---------------------------------------------------------------------------
# Основной расчёт
# ---------------------------------------------------------------------------

def _star_info(n: int) -> dict:
    return {"number": n, **STARS[n]}


def _solar_month_index(jd_ut: float) -> int:
    lon = sun_longitude(jd_ut)
    return int(((lon - 315.0) % 360.0) // 30.0)


def calculate(b: BirthInput, **options) -> dict:
    """Девятизвёздная Ки, число Гуа и китайский зодиак.

    Опции:
      year_boundary: 'li_chun' (по умолчанию) | 'feb4' (упрощённо, 4 февраля) | 'lunar_new_year'
      boundary_precision: 'auto' (момент, если известны время и пояс; иначе дата) | 'moment' | 'date'
      almanac_tz: пояс для сравнения по датам (по умолчанию пояс рождения, иначе UTC+8);
                  'UTC+09:00' воспроизводит японские таблицы, 'UTC+08:00' — китайские.
      gua_boundary: 'li_chun' (по умолчанию, как у Ки) | 'lunar_new_year'
      zodiac_boundary: 'lunar_new_year' (по умолчанию) | 'li_chun'
      day_star_method: 'ja_leap' (по умолчанию) | 'nearest_no_leap' | None (не считать)
    """
    year_boundary = options.get("year_boundary", "li_chun")
    precision = options.get("boundary_precision", "auto")
    gua_boundary = options.get("gua_boundary", "li_chun")
    zodiac_boundary = options.get("zodiac_boundary", "lunar_new_year")
    day_method = options.get("day_star_method", "ja_leap")
    gender = (b.gender or "").lower() or None
    if gender in ("m", "м", "муж", "мужской"):
        gender = "male"
    elif gender in ("f", "ж", "жен", "женский"):
        gender = "female"

    warnings: list[str] = []
    steps: list[str] = []
    birth_date = b.date

    # --- 1. Время рождения → UT (если возможно) --------------------------------
    nt = None
    if b.has_time and b.tz is not None:
        nt = normalize(b)
        warnings.extend(nt.warnings)
    elif b.has_time and b.tz is None:
        warnings.append("Время рождения указано без часового пояса/места — граница Личуня определяется по дате.")

    if precision == "auto":
        precision = "moment" if nt is not None else "date"
    if precision == "moment" and nt is None:
        warnings.append("Точный момент недоступен (нет времени или пояса) — сравнение по датам.")
        precision = "date"

    # Пояс для пересчёта моментов терминов в местные даты
    if options.get("almanac_tz"):
        zone = _Zone(options["almanac_tz"], b.lon)
    elif nt is not None and nt.offset_source != "tzdb":
        zone = _Zone(b.tz, b.lon, force_offset_hours=nt.utc_offset_hours)
    elif b.tz is not None:
        zone = _Zone(b.tz, b.lon)
    else:
        zone = _Zone(None)
        warnings.append("Часовой пояс неизвестен: даты солнечных терминов взяты по UTC+8 (китайский календарь).")

    if precision == "moment":
        jd_ref = nt.jd_ut
        steps.append(f"Момент рождения: местное {_fmt(nt.local)} ({nt.offset_source}, UTC{nt.utc_offset_hours:+.2f}) "
                     f"= {_fmt(nt.utc)} UT, JD {nt.jd_ut:.5f}.")
    else:
        end_of_day_utc = zone.to_utc(datetime.combine(birth_date + timedelta(days=1), datetime.min.time()))
        jd_ref = _jd(end_of_day_utc) - 1e-7
        steps.append(f"Время/пояс не используются: сравнение по дате {birth_date.isoformat()} "
                     f"с датами терминов в поясе {zone.label} (день термина относится к новому периоду).")

    # --- 2. Личунь и китайский Новый год ----------------------------------------
    y_civ = birth_date.year
    lc_jd = li_chun(y_civ)
    lc_utc = jd_to_utc(lc_jd)
    lc_local = zone.to_local(lc_utc)
    after_lc = jd_ref >= lc_jd
    solar_year = y_civ if after_lc else y_civ - 1
    steps.append(f"Личунь {y_civ} г. (Солнце 315°): {_fmt(lc_utc)} UT = {_fmt(lc_local)} ({zone.label}). "
                 f"Рождение {'после' if after_lc else 'до'} Личуня → солнечный год {solar_year}.")
    if precision == "date" and birth_date == lc_local.date():
        alt = year_star(y_civ - 1)
        warnings.append(f"Дата рождения совпадает с днём Личуня ({lc_local.strftime('%H:%M')} {zone.label}); "
                        f"без точного времени год взят новым ({y_civ}). Если рождение было раньше этого момента, "
                        f"звезда года была бы {alt}.")
    if precision == "moment" and abs(nt.jd_ut - lc_jd) < 1.0:
        warnings.append(f"Рождение в пределах суток от момента Личуня ({_fmt(lc_utc)} UT): результат чувствителен "
                        f"к точности времени рождения и пояса.")
        loc_tables = {"UTC+08:00": "КНР", "UTC+09:00": "Японии"}
        for tzn, nm in loc_tables.items():
            lc_alm = _Zone(tzn).to_local(lc_utc).date()
            if lc_alm != birth_date and abs((lc_alm - birth_date).days) <= 1:
                yr_alm = y_civ if birth_date >= lc_alm else y_civ - 1
                if yr_alm != solar_year:
                    warnings.append(f"По календарю {nm} Личунь выпадает на {lc_alm.isoformat()}: таблицы, "
                                    f"сравнивающие только даты по этому календарю, дадут год {yr_alm} "
                                    f"(звезда {year_star(yr_alm)}).")

    cny = lunar_new_year(y_civ)
    lunar_year = None
    if cny is not None:
        lunar_year = y_civ if birth_date >= cny else y_civ - 1
        steps.append(f"Китайский Новый год {y_civ}: {cny.isoformat()} (календарь КНР) → лунный год {lunar_year}.")
    else:
        warnings.append("Не удалось определить дату китайского Нового года (lunar-python).")

    if year_boundary == "li_chun":
        nsk_year = solar_year
    elif year_boundary == "feb4":
        nsk_year = y_civ if (birth_date.month, birth_date.day) >= (2, 4) else y_civ - 1
        steps.append(f"Упрощённая граница «4 февраля» → год {nsk_year}.")
        if nsk_year != solar_year:
            warnings.append(f"Граница «4 февраля» даёт год {nsk_year}, точный Личунь — {solar_year}.")
    elif year_boundary == "lunar_new_year":
        if lunar_year is None:
            raise ValueError("Дата китайского Нового года недоступна.")
        nsk_year = lunar_year
        warnings.append("Граница года по китайскому Новому году не классическая для Девятизвёздной Ки.")
    else:
        raise ValueError("year_boundary: 'li_chun' | 'feb4' | 'lunar_new_year'")

    # --- 3. Звезда года ---------------------------------------------------------
    ys = year_star(nsk_year)
    dr = digital_root(nsk_year)
    steps.append(f"Звезда года: цифровой корень {nsk_year} = {dr}; 11 − {dr} = {11 - dr}"
                 + (f" → {ys}" if 11 - dr != ys else "") + f" ⇒ {ys} {STARS[ys]['ja']} ({STARS[ys]['ru']}).")

    # --- 4. Солнечный месяц и звезда месяца -------------------------------------
    m = _solar_month_index(jd_ref)
    m_start = find_sun_longitude(SOLAR_MONTHS[m][3], jd_ref, search_back=True)
    m_end = find_sun_longitude(SOLAR_MONTHS[(m + 1) % 12][3], jd_ref, search_back=False)
    ms = month_star(ys, m)
    steps.append(f"Солнечный месяц {SOLAR_MONTHS[m][0]} ({SOLAR_MONTHS[m][1]}), №{m + 1} от Личуня: с "
                 f"{SOLAR_MONTHS[m][2]} {_fmt(zone.to_local(jd_to_utc(m_start)))} до "
                 f"{_fmt(zone.to_local(jd_to_utc(m_end)))} ({zone.label}).")
    steps.append(f"Звезда месяца: в год звезды {ys} месяц 寅 начинается со звезды {FIRST_MONTH_STAR[ys]}; "
                 f"сдвиг на {m} назад → {ms} {STARS[ms]['ja']}.")
    if precision == "date":
        mloc = zone.to_local(jd_to_utc(m_start)).date()
        if mloc == birth_date:
            warnings.append(f"Дата рождения совпадает с днём смены солнечного месяца ({SOLAR_MONTHS[m][2]}); без "
                            f"времени взят новый месяц. Иначе звезда месяца была бы {month_star(ys, m - 1) if m else month_star(year_star(nsk_year - 1), 11)}.")
    elif abs(jd_ref - m_start) < 1.0 or abs(m_end - jd_ref) < 1.0:
        warnings.append("Рождение в пределах суток от смены солнечного месяца: звезда месяца чувствительна "
                        "к точности времени.")

    # --- 5. Наклон (傾斜) / энергетическое число ---------------------------------
    tend = tendency_palace(ys, ms, gender)
    if tend["number"] is None:
        warnings.append("Звёзды года и месяца — обе 5: наклон зависит от пола (м → 兌宮 7, ж → 乾宮 6); пол не указан.")
    steps.append("Наклон (傾斜宮): звезду месяца ставим в центр Ло Шу, ищем дворец звезды года: "
                 + (f"({ys} − {ms} + 4) mod 9 + 1 = {tend['number']} → {tend['palace']}." if not tend["special_center_case"]
                    else f"звёзды совпадают (中宮傾斜) → особая таблица → {tend['number'] or tend.get('by_gender')}."))

    nsk = {
        "solar_year": nsk_year,
        "principal": _star_info(ys),
        "month": {**_star_info(ms), "solar_month_index": m, "branch": SOLAR_MONTHS[m][0],
                  "jie": SOLAR_MONTHS[m][2],
                  "starts_utc": jd_to_utc(m_start).isoformat(timespec="minutes"),
                  "ends_utc": jd_to_utc(m_end).isoformat(timespec="minutes")},
        "tendency": tend,
        "notation": f"{ys}.{ms}.{tend['number'] if tend['number'] is not None else '?'}",
    }

    # --- 6. Звезда дня ----------------------------------------------------------
    if day_method:
        ds = day_star(birth_date, day_method, options.get("day_almanac_tz"))
        nsk["day"] = {**_star_info(ds["number"]), **ds}
        steps.append(f"Звезда дня ({day_method}): день {ds['day_ganzhi']}; отсчёт от {ds['segment_start']} "
                     f"(звезда {ds['segment_start_star']}, {ds['dun_ru']}), прошло {ds['days_from_segment_start']} дн. "
                     f"→ {ds['number']}" + (" [сегмент 閏]" if ds["leap_segment"] else "") + ".")
        warnings.append("Звезда дня: правило переключения Ян/Инь-дуня различается по школам (⚠ см. базу знаний).")
        if b.has_time and (b.hour or 0) >= 23:
            alt = day_star(birth_date + timedelta(days=1), day_method, options.get("day_almanac_tz"))
            nsk["day"]["alt_if_day_starts_23h"] = alt["number"]
            warnings.append(f"Поздний час Цзы (23:00–24:00): если сутки начинать в 23:00, звезда дня = {alt['number']}.")

    # --- 7. Гуа -----------------------------------------------------------------
    if gua_boundary == "li_chun":
        gua_year = nsk_year if year_boundary == "li_chun" else solar_year
    elif gua_boundary == "lunar_new_year":
        gua_year = lunar_year
    else:
        raise ValueError("gua_boundary: 'li_chun' | 'lunar_new_year'")
    alt_gua_year = lunar_year if gua_boundary == "li_chun" else solar_year

    def gua_block(g: str) -> dict:
        raw = gua_raw(gua_year, g)
        num = gua_number(gua_year, g)
        blk = {
            "gender": g, "year_used": gua_year, "raw": raw, "number": num,
            "replaced_5": raw == 5, "trigram": STARS[num]["trigram"], "element": STARS[num]["element"],
            "group": "east" if num in EAST_GROUP else "west",
            "group_ru": "Восточная группа (东四命)" if num in EAST_GROUP else "Западная группа (西四命)",
            "century_formula": gua_century_formula(gua_year, g),
            **eight_mansions(num),
        }
        if alt_gua_year is not None and alt_gua_year != gua_year:
            blk["alt_other_boundary"] = {"year_used": alt_gua_year, "number": gua_number(alt_gua_year, g)}
        return blk

    gua: dict
    if gender in ("male", "female"):
        gua = gua_block(gender)
        steps.append(f"Гуа ({'мужчина' if gender == 'male' else 'женщина'}, год {gua_year}): "
                     + ("(11 − Y mod 9)" if gender == "male" else "(Y + 4) mod 9")
                     + f" → {gua['raw']}" + (f" → замена 5 → {gua['number']}" if gua["replaced_5"] else "")
                     + f"; {gua['century_formula']}; {gua['group_ru']}.")
    else:
        gua = {"gender": None, "male": gua_block("male"), "female": gua_block("female")}
        warnings.append("Пол не указан: Гуа рассчитано для обоих вариантов.")
    if alt_gua_year is not None and alt_gua_year != gua_year:
        warnings.append(f"Граница года для Гуа: по Личуню год {solar_year}, по китайскому Новому году {lunar_year}; "
                        f"Гуа зависит от выбранной школы (выбрано: {gua_boundary}).")

    # --- 8. Китайский зодиак ----------------------------------------------------
    zodiac_solar = sexagenary_year(solar_year)
    zodiac_lunar = sexagenary_year(lunar_year) if lunar_year is not None else None
    zodiac = zodiac_lunar if (zodiac_boundary == "lunar_new_year" and zodiac_lunar) else zodiac_solar
    steps.append(f"Зодиак: (Y − 4) mod 60 → по Новому году {zodiac_lunar['ganzhi'] if zodiac_lunar else '—'} "
                 f"({zodiac_lunar['popular_name_ru'] if zodiac_lunar else '—'}); по Личуню {zodiac_solar['ganzhi']} "
                 f"({zodiac_solar['popular_name_ru']}).")
    if zodiac_lunar and zodiac_lunar["year"] != zodiac_solar["year"]:
        warnings.append(f"Знак года различается: по китайскому Новому году — {zodiac_lunar['popular_name_ru']} "
                        f"({zodiac_lunar['year']}), по Личуню (Ба-цзы, Ки, Гуа) — {zodiac_solar['popular_name_ru']} "
                        f"({zodiac_solar['year']}).")

    inputs_used = {
        "date": birth_date.isoformat(),
        "time": f"{b.hour:02d}:{(b.minute or 0):02d}" if b.has_time else None,
        "tz": b.tz, "lat": b.lat, "lon": b.lon, "gender": gender,
        "utc": nt.utc.isoformat(timespec="minutes") if nt else None,
    }
    return {
        "method": "nine_star_ki_gua_zodiac",
        "variant": {
            "year_boundary": year_boundary, "boundary_precision": precision, "almanac_tz": zone.label,
            "gua_boundary": gua_boundary, "zodiac_boundary": zodiac_boundary, "day_star_method": day_method,
            "tendency_center_table": "yakumoin/amenouranai (1→9, 2→6, 3→4, 4→3, 5→м7/ж6, 6→2, 7→8, 8→7, 9→1)",
        },
        "inputs_used": inputs_used,
        "warnings": warnings,
        "boundaries": {
            "li_chun_utc": lc_utc.isoformat(timespec="minutes"),
            "li_chun_local": lc_local.isoformat(timespec="minutes"),
            "lunar_new_year": cny.isoformat() if cny else None,
            "solar_year": solar_year, "lunar_year": lunar_year,
        },
        "nine_star_ki": nsk,
        "gua": gua,
        "zodiac": zodiac,
        "zodiac_lunar": zodiac_lunar,
        "zodiac_solar": zodiac_solar,
        "steps": steps,
    }


if __name__ == "__main__":  # pragma: no cover
    import json

    r = calculate(BirthInput(1990, 5, 15, 14, 30, place="Москва", gender="female"))
    print(json.dumps(r, ensure_ascii=False, indent=2))
