"""Цзы Вэй Доу Шу (紫微斗数, «Пурпурная звезда»): построение натальной карты.

Описание метода, школы и ручной алгоритм — knowledge-base/02-ziwei-doushu.md.

Что считается:
* лунная дата (китайский календарь через lunar-python), час-ветвь (时辰), год по
  китайскому Новому году (по умолчанию) или по Личуню;
* Дворец Судьбы (命宫) и Дворец Тела (身宫), 12 дворцов и их небесные стволы (五虎遁);
* «бюро» пяти элементов (五行局) по на-инь ствола-ветви Дворца Судьбы;
* 14 главных звёзд (группы Цзы Вэй и Тянь Фу) и 14 основных вспомогательных
  (左辅 右弼 文昌 文曲 天魁 天钺 禄存 擎羊 陀罗 火星 铃星 地空 地劫 天马);
* четыре трансформации (四化) по стволу года — 4 варианта таблиц школ;
* яркость (庙旺得利平不陷) по таблице iztro (⚠ различается по школам);
* 命主/身主, десятилетние периоды (大限), малые пределы (小限), основы года (流年).

Независимая сверка: npm-пакет iztro 2.6.2 (calculators/tools/iztro_crosscheck.mjs),
эталонные значения заморожены в calculators/tests/test_ziwei.py.

Индексация: ветви 子=0 … 亥=11, стволы 甲=0 … 癸=9. «Вперёд» (順) = по возрастанию
индекса ветви (子→丑→寅…), т.е. по часовой стрелке на стандартной схеме карты.
"""
from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from typing import Any

from lunar_python import LunarMonth, Solar

from .common.time import BirthInput, fmt_offset, local_mean_time, normalize, true_solar_time

# ---------------------------------------------------------------------------
# Базовые справочники
# ---------------------------------------------------------------------------

STEMS = "甲乙丙丁戊己庚辛壬癸"
BRANCHES = "子丑寅卯辰巳午未申酉戌亥"
STEMS_PINYIN = ["цзя", "и", "бин", "дин", "у", "цзи", "гэн", "синь", "жэнь", "гуй"]
BRANCHES_PINYIN = ["цзы", "чоу", "инь", "мао", "чэнь", "сы", "у", "вэй", "шэнь", "ю", "сюй", "хай"]
BRANCH_ANIMALS_RU = ["Крыса", "Бык", "Тигр", "Кролик", "Дракон", "Змея",
                     "Лошадь", "Коза", "Обезьяна", "Петух", "Собака", "Свинья"]
HOUR_RANGES = ["23:00–01:00", "01:00–03:00", "03:00–05:00", "05:00–07:00", "07:00–09:00",
               "09:00–11:00", "11:00–13:00", "13:00–15:00", "15:00–17:00", "17:00–19:00",
               "19:00–21:00", "21:00–23:00"]

YIN, CHOU, ZI = 2, 1, 0
CHEN, XU, HAI, WU = 4, 10, 11, 6

# 12 дворцов в порядке ОТ Дворца Судьбы ПРОТИВ хода ветвей (命 в ветви X, 兄弟 в X−1, …)
PALACES: list[tuple[str, str]] = [
    ("命宫", "Судьба (Мин)"),
    ("兄弟", "Братья и сёстры"),
    ("夫妻", "Супруг(а)"),
    ("子女", "Дети"),
    ("财帛", "Богатство"),
    ("疾厄", "Здоровье"),
    ("迁移", "Перемещения"),
    ("仆役", "Друзья/подчинённые"),
    ("官禄", "Карьера"),
    ("田宅", "Дом и имущество"),
    ("福德", "Благополучие духа"),
    ("父母", "Родители"),
]

# На-инь 60 пар (纳音): пара (ствол, ветвь) с одинаковой чётностью -> (название, стихия)
_NAYIN_PAIRS = [
    "海中金", "炉中火", "大林木", "路旁土", "剑锋金", "山头火", "涧下水", "城头土", "白蜡金", "杨柳木",
    "泉中水", "屋上土", "霹雳火", "松柏木", "长流水", "沙中金", "山下火", "平地木", "壁上土", "金箔金",
    "覆灯火", "天河水", "大驿土", "钗钏金", "桑柘木", "大溪水", "沙中土", "天上火", "石榴木", "大海水",
]
BUREAU_BY_ELEMENT = {"水": 2, "木": 3, "金": 4, "土": 5, "火": 6}
BUREAU_NAMES = {2: "水二局", 3: "木三局", 4: "金四局", 5: "土五局", 6: "火六局"}
BUREAU_RU = {2: "Вода-2", 3: "Дерево-3", 4: "Металл-4", 5: "Земля-5", 6: "Огонь-6"}

STARS_RU: dict[str, str] = {
    "紫微": "Цзы Вэй (Пурпурная, «император»)", "天机": "Тянь Цзи (Небесный механизм)",
    "太阳": "Тай Ян (Солнце)", "武曲": "У Цюй (Военная мелодия)", "天同": "Тянь Тун (Небесное согласие)",
    "廉贞": "Лянь Чжэнь (Целомудрие)", "天府": "Тянь Фу (Небесная казна)", "太阴": "Тай Инь (Луна)",
    "贪狼": "Тань Лан (Жадный волк)", "巨门": "Цзюй Мэнь (Великие врата)", "天相": "Тянь Сян (Небесный министр)",
    "天梁": "Тянь Лян (Небесная опора)", "七杀": "Ци Ша (Семь убийств)", "破军": "По Цзюнь (Разрушитель армий)",
    "左辅": "Цзо Фу (Левый помощник)", "右弼": "Ю Би (Правый помощник)", "文昌": "Вэнь Чан (Литературный блеск)",
    "文曲": "Вэнь Цюй (Литературная мелодия)", "天魁": "Тянь Куй (Небесный вожак)", "天钺": "Тянь Юэ (Небесная секира)",
    "禄存": "Лу Цунь (Хранилище удачи)", "擎羊": "Цин Ян (Поднятый клинок)", "陀罗": "То Ло (Волчок, задержка)",
    "火星": "Хо Син (Огненная звезда)", "铃星": "Лин Син (Звезда-колокол)", "地空": "Ди Кун (Земная пустота)",
    "地劫": "Ди Цзе (Земной грабёж)", "天马": "Тянь Ма (Небесный конь)",
}
ZIWEI_GROUP = [("紫微", 0), ("天机", -1), ("太阳", -3), ("武曲", -4), ("天同", -5), ("廉贞", -8)]
TIANFU_GROUP = [("天府", 0), ("太阴", 1), ("贪狼", 2), ("巨门", 3), ("天相", 4), ("天梁", 5), ("七杀", 6), ("破军", 10)]
MAJOR_STARS = [s for s, _ in ZIWEI_GROUP] + [s for s, _ in TIANFU_GROUP]
AUX_STARS = ["左辅", "右弼", "文昌", "文曲", "天魁", "天钺", "禄存", "擎羊", "陀罗", "火星", "铃星", "地空", "地劫", "天马"]

SIHUA_KEYS = ["禄", "权", "科", "忌"]
SIHUA_RU = {"禄": "Хуа Лу (удача/доход)", "权": "Хуа Цюань (власть)", "科": "Хуа Кэ (репутация)", "忌": "Хуа Цзи (препятствие)"}

# Четыре трансформации [禄, 权, 科, 忌] по стволу года.
_SIHUA_COMMON = {
    "甲": ["廉贞", "破军", "武曲", "太阳"],
    "乙": ["天机", "天梁", "紫微", "太阴"],
    "丙": ["天同", "天机", "文昌", "廉贞"],
    "丁": ["太阴", "天同", "天机", "巨门"],
    "戊": ["贪狼", "太阴", "右弼", "天机"],
    "己": ["武曲", "贪狼", "天梁", "文曲"],
    "庚": ["太阳", "武曲", "太阴", "天同"],
    "辛": ["巨门", "太阳", "文曲", "文昌"],
    "壬": ["天梁", "紫微", "左辅", "武曲"],
    "癸": ["破军", "巨门", "太阴", "贪狼"],
}
SIHUA_TABLES: dict[str, dict[str, list[str]]] = {
    # 《紫微斗数全集》; так же iztro и большинство современных программ — по умолчанию
    "quanji": dict(_SIHUA_COMMON),
    # 《紫微斗数全书》 (zh.wikipedia): 庚 阳武同阴, 壬 梁紫府武
    "quanshu": {**_SIHUA_COMMON, "庚": ["太阳", "武曲", "天同", "太阴"], "壬": ["天梁", "紫微", "天府", "武曲"]},
    # 中州派 (линия Ван Тинчжи) по ncc.com.tw и qqqtseng.pixnet: 戊 贪阴阳机, 庚 阳武府同, 壬 梁紫府武
    "zhongzhou": {**_SIHUA_COMMON, "戊": ["贪狼", "太阴", "太阳", "天机"],
                  "庚": ["太阳", "武曲", "天府", "天同"], "壬": ["天梁", "紫微", "天府", "武曲"]},
    # «北派» по qqqtseng.pixnet (и издание 吴师青 по haozh.com): 庚 阳武同相
    "beipai": {**_SIHUA_COMMON, "庚": ["太阳", "武曲", "天同", "天相"]},
}

# Лу Цунь по стволу года (индекс ветви)
LUCUN = {"甲": 2, "乙": 3, "丙": 5, "丁": 6, "戊": 5, "己": 6, "庚": 8, "辛": 9, "壬": 11, "癸": 0}
# Тянь Куй / Тянь Юэ по стволу года: (魁, 钺)
KUIYUE: dict[str, dict[str, tuple[int, int]]] = {
    # 「甲戊庚牛羊，乙己鼠猴乡，丙丁猪鸡位，壬癸兔蛇藏，六辛逢马虎」 — iztro, ncc.com.tw
    "geng_chou_wei": {"甲": (1, 7), "戊": (1, 7), "庚": (1, 7), "乙": (0, 8), "己": (0, 8),
                      "丙": (11, 9), "丁": (11, 9), "壬": (3, 5), "癸": (3, 5), "辛": (6, 2)},
    # вариант «庚辛逢马虎» (как 天乙贵人 в Бацзы): 庚 -> 午/寅 (⚠ см. базу знаний)
    "geng_wu_yin": {"甲": (1, 7), "戊": (1, 7), "庚": (6, 2), "乙": (0, 8), "己": (0, 8),
                    "丙": (11, 9), "丁": (11, 9), "壬": (3, 5), "癸": (3, 5), "辛": (6, 2)},
}
# Группы «трёх гармоний» ветвей года -> (Тянь Ма, старт Хо Син, старт Лин Син, старт 小限)
_SANHE = {
    (2, 6, 10): {"tianma": 8, "huo": 1, "ling": 3, "xiaoxian": 4},    # 寅午戌: 马申, 火丑, 铃卯, 小限辰
    (8, 0, 4): {"tianma": 2, "huo": 2, "ling": 10, "xiaoxian": 10},   # 申子辰: 马寅, 火寅, 铃戌, 小限戌
    (5, 9, 1): {"tianma": 11, "huo": 3, "ling": 10, "xiaoxian": 7},   # 巳酉丑: 马亥, 火卯, 铃戌, 小限未
    (11, 3, 7): {"tianma": 5, "huo": 9, "ling": 10, "xiaoxian": 1},   # 亥卯未: 马巳, 火酉, 铃戌, 小限丑
}

# 命主 по ветви (Дворца Судьбы — общепринято; ветви года — 中州派), 身主 по ветви года
MING_ZHU = ["贪狼", "巨门", "禄存", "文曲", "廉贞", "武曲", "破军", "武曲", "廉贞", "文曲", "禄存", "巨门"]
SHEN_ZHU = ["火星", "天相", "天梁", "天同", "文昌", "天机", "火星", "天相", "天梁", "天同", "文昌", "天机"]

# Яркость (iztro 2.6.2, data/stars.js), порядок ветвей ОТ 寅: 寅卯辰巳午未申酉戌亥子丑.
# Обозначения: 庙 мяо, 旺 ван, 得 дэ, 利 ли, 平 пин, 不 бу, 陷 сянь; "" — нет оценки.
_BRIGHTNESS_FROM_YIN: dict[str, str] = {
    "紫微": "旺旺得旺庙庙旺旺得旺平庙",
    "天机": "得旺利平庙陷得旺利平庙陷",
    "太阳": "旺庙旺旺旺得得平不陷陷不",
    "武曲": "得利庙平旺庙得利庙平旺庙",
    "天同": "利平平庙陷不旺平平庙旺不",
    "廉贞": "庙平利陷平利庙平利陷平利",
    "天府": "庙得庙得旺庙得旺庙得庙庙",
    "太阴": "旺陷陷陷不不利旺旺庙庙庙",
    "贪狼": "平利庙陷旺庙平利庙陷旺庙",
    "巨门": "庙庙陷旺旺不庙庙陷旺旺不",
    "天相": "庙陷得得庙得庙陷得得庙庙",
    "天梁": "庙庙庙陷庙旺陷得庙陷庙旺",
    "七杀": "庙旺庙平旺庙庙旺庙平旺庙",
    "破军": "得陷旺平庙旺得陷旺平庙旺",
    "文昌": "陷利得庙陷利得庙陷利得庙",
    "文曲": "平旺得庙陷旺得庙陷旺得庙",
    "火星": "庙利陷得庙利陷得庙利陷得",
    "铃星": "庙利陷得庙利陷得庙利陷得",
    "擎羊": "-陷庙-陷庙-陷庙-陷庙",
    "陀罗": "陷-庙陷-庙陷-庙陷-庙",
}


def _brightness_table() -> dict[str, list[str]]:
    out: dict[str, list[str]] = {}
    for star, s in _BRIGHTNESS_FROM_YIN.items():
        vals = ["" if ch == "-" else ch for ch in s]
        by_branch = [""] * 12
        for i, v in enumerate(vals):
            by_branch[(YIN + i) % 12] = v
        out[star] = by_branch
    return out


BRIGHTNESS = _brightness_table()
BRIGHTNESS_RU = {"庙": "мяо (храм, максимум)", "旺": "ван (процветание)", "得": "дэ (на своём месте)",
                 "利": "ли (благоприятно)", "平": "пин (нейтрально)", "不": "бу (не на месте)", "陷": "сянь (падение)"}

DEFAULTS: dict[str, Any] = {
    "time_basis": None,          # None -> "true_solar" при известной долготе, иначе "clock"
    "solar_time": None,          # синоним time_basis в стиле bazi.py: "true" | "mean" | "clock"
    "zi_hour": "next_day",       # 23:00–24:00: "next_day" (隔夜晚子, мейнстрим) | "same_day";
                                 # синонимы как в bazi.py: "early" = next_day, "late" = same_day
    "year_boundary": "lunar_new_year",  # | "lichun"
    "leap_month": "split_15",    # | "same" | "next"
    "sihua": "quanji",           # | "quanshu" | "zhongzhou" | "beipai"
    "kui_yue": "geng_chou_wei",  # | "geng_wu_yin"
    "ming_zhu": "ming_branch",   # | "year_branch" (中州派)
    "hour_branch": None,         # явная ветвь часа 0..11 / "子".."亥" / "晚子" (перекрывает время)
    "flow_year": None,           # год (григорианский номер лунного года) для блока 流年
}


# ---------------------------------------------------------------------------
# Чистые функции алгоритма (используются и в тестах)
# ---------------------------------------------------------------------------

def gz(stem: int, branch: int) -> str:
    return STEMS[stem % 10] + BRANCHES[branch % 12]


def hour_branch_index(hour: int, minute: int = 0) -> int:
    """Ветвь часа: 子 = 23:00–00:59, 丑 = 01:00–02:59, …, 亥 = 21:00–22:59."""
    return ((hour * 60 + minute + 60) // 120) % 12


def ming_branch(month: int, hour_branch: int) -> int:
    """命宫: от 寅 вперёд до месяца (寅 = 1-й месяц), затем назад на число часов (子 = 0)."""
    return (YIN + (month - 1) - hour_branch) % 12


def body_branch(month: int, hour_branch: int) -> int:
    """身宫: от 寅 вперёд до месяца, затем вперёд на число часов."""
    return (YIN + (month - 1) + hour_branch) % 12


def yin_stem(year_stem: int) -> int:
    """五虎遁: ствол дворца 寅 по стволу года (甲己→丙, 乙庚→戊, 丙辛→庚, 丁壬→壬, 戊癸→甲)."""
    return ((year_stem % 5) * 2 + 2) % 10


def palace_stem(year_stem: int, branch: int) -> int:
    """Ствол дворца с ветвью branch: идём от 寅 вперёд (寅…亥, затем 子, 丑)."""
    return (yin_stem(year_stem) + (branch - YIN) % 12) % 10


def nayin(stem: int, branch: int) -> str:
    """На-инь (纳音) пары ствол-ветвь, напр. 丙戌 -> 屋上土."""
    if stem % 2 != branch % 2:
        raise ValueError("ствол и ветвь разной чётности — такой пары нет в цикле 60")
    idx60 = next(i for i in range(60) if i % 10 == stem and i % 12 == branch)
    return _NAYIN_PAIRS[idx60 // 2]


def bureau_number(stem: int, branch: int) -> int:
    """Номер бюро (五行局) по на-инь: 水2 木3 金4 土5 火6."""
    return BUREAU_BY_ELEMENT[nayin(stem, branch)[-1]]


def bureau_number_mnemonic(stem: int, branch: int) -> int:
    """Тот же результат «ручным» правилом 甲乙丙丁一到五…: стволы 1..5, ветви 1..3."""
    s = stem // 2 + 1
    b = (branch % 6) // 2 + 1
    n = s + b
    while n > 5:
        n -= 5
    return {1: 3, 2: 4, 3: 2, 4: 6, 5: 5}[n]  # 1木 2金 3水 4火 5土


def ziwei_branch(lunar_day: int, bureau: int) -> tuple[int, dict]:
    """Ветвь звезды 紫微 по лунному дню и бюро; второй элемент — промежуточные числа.

    x — наименьшее x ≥ 0, при котором (день + x) делится на бюро; q = (день + x)/бюро.
    От 寅 (шаг 1) отсчитать q ветвей вперёд; затем, если x нечётно, отступить на x назад,
    если x чётно (в т.ч. 0) — пройти ещё x вперёд.
    """
    x = (-lunar_day) % bureau
    q = (lunar_day + x) // bureau
    base = (YIN + q - 1) % 12
    pos = (base - x) % 12 if x % 2 else (base + x) % 12
    return pos, {"x": x, "q": q, "base_branch": BRANCHES[base]}


def tianfu_branch(ziwei: int) -> int:
    """天府 зеркален 紫微 относительно оси 寅—申: F = (4 − Z) mod 12."""
    return (4 - ziwei) % 12


def major_star_positions(ziwei: int) -> dict[str, int]:
    tf = tianfu_branch(ziwei)
    out = {s: (ziwei + d) % 12 for s, d in ZIWEI_GROUP}
    out.update({s: (tf + d) % 12 for s, d in TIANFU_GROUP})
    return out


def _sanhe(branch: int) -> dict:
    for group, val in _SANHE.items():
        if branch in group:
            return val
    raise ValueError(branch)


def aux_star_positions(year_stem: int, year_branch: int, month: int, hour_branch: int,
                       kui_yue: str = "geng_chou_wei") -> dict[str, int]:
    """14 вспомогательных звёзд (индексы ветвей)."""
    s = STEMS[year_stem]
    lu = LUCUN[s]
    kui, yue = KUIYUE[kui_yue][s]
    sh = _sanhe(year_branch)
    return {
        "左辅": (CHEN + month - 1) % 12,
        "右弼": (XU - (month - 1)) % 12,
        "文昌": (XU - hour_branch) % 12,
        "文曲": (CHEN + hour_branch) % 12,
        "天魁": kui,
        "天钺": yue,
        "禄存": lu,
        "擎羊": (lu + 1) % 12,
        "陀罗": (lu - 1) % 12,
        "火星": (sh["huo"] + hour_branch) % 12,
        "铃星": (sh["ling"] + hour_branch) % 12,
        "地空": (HAI - hour_branch) % 12,
        "地劫": (HAI + hour_branch) % 12,
        "天马": sh["tianma"],
    }


def sihua_for_stem(stem: int, table: str = "quanji") -> dict[str, str]:
    stars = SIHUA_TABLES[table][STEMS[stem]]
    return dict(zip(SIHUA_KEYS, stars))


def decade_forward(year_stem: int, gender: str) -> bool:
    """阳男阴女 — вперёд (順), 阴男阳女 — назад (逆)."""
    yang = year_stem % 2 == 0
    male = gender == "male"
    return yang == male


# ---------------------------------------------------------------------------
# Календарь и время
# ---------------------------------------------------------------------------

def _lunar_of(d: date):
    return Solar.fromYmd(d.year, d.month, d.day).getLunar()


def _elongation(jd: float) -> float:
    import swisseph as swe  # уже инициализирован в common.ephemeris
    from .common import ephemeris  # noqa: F401  (ставит путь к эфемеридам)
    m = swe.calc_ut(jd, swe.MOON)[0][0]
    s = swe.calc_ut(jd, swe.SUN)[0][0]
    return (m - s + 540.0) % 360.0 - 180.0


def _new_moon_near(jd0: float) -> float:
    """Момент новолуния (JD UT), ближайший к jd0 (±3 сут)."""
    jd = jd0 - 3.0
    e0 = _elongation(jd)
    while jd < jd0 + 3.0:
        jd2 = jd + 0.25
        e1 = _elongation(jd2)
        if e0 < 0 <= e1:
            lo, hi = jd, jd2
            for _ in range(50):
                mid = (lo + hi) / 2
                if _elongation(mid) < 0:
                    lo = mid
                else:
                    hi = mid
            return (lo + hi) / 2
        jd, e0 = jd2, e1
    raise RuntimeError("новолуние не найдено")


def _jd_to_date_at_offset(jd: float, offset_hours: float) -> date:
    from .common.time import jd_to_utc
    return (jd_to_utc(jd) + timedelta(hours=offset_hours)).date()


def _check_new_moon_timezone(lunar, chart_date: date, offset_hours: float) -> str | None:
    """Китайский календарь начинает месяц в день новолуния по времени UTC+8. Если по
    местному поясу новолуние приходится на другую дату и дата рождения попадает в
    «сдвинутое» окно, лунный день (а иногда и месяц) по местному календарю другой."""
    if abs(offset_hours - 8.0) < 1e-6:
        return None
    lm = LunarMonth.fromYm(lunar.getYear(), lunar.getMonth())
    first_jd_noon = lm.getFirstJulianDay()  # полдень первого дня месяца
    s = Solar.fromJulianDay(first_jd_noon)
    cn_start = date(s.getYear(), s.getMonth(), s.getDay())
    try:
        loc_start = _jd_to_date_at_offset(_new_moon_near(first_jd_noon), offset_hours)
        loc_next = _jd_to_date_at_offset(_new_moon_near(first_jd_noon + lm.getDayCount()), offset_hours)
    except RuntimeError:
        return None
    if chart_date >= loc_next:
        local = f"уже следующий лунный месяц, день {(chart_date - loc_next).days + 1}"
    elif chart_date < loc_start:
        local = "ещё предыдущий лунный месяц (последний день)"
    else:
        local_day = (chart_date - loc_start).days + 1
        if local_day == lunar.getDay():
            return None
        local = f"лунный день {local_day}"
    return (
        f"Дата рождения у границы лунного месяца: по пекинскому календарю (UTC+8, месяц начался {cn_start}) "
        f"это день {lunar.getDay()}, а если считать новолуние по местному поясу {fmt_offset(offset_hours)} — {local}. "
        "Расчёт по стандартному китайскому календарю (так делает большинство программ); школы, пересчитывающие "
        "календарь на местный пояс, получат другие 紫微/месяц."
    )


def _parse_hour_branch(v: Any) -> tuple[int, bool]:
    """Явно заданная ветвь часа -> (индекс, поздний_цзы)."""
    if isinstance(v, int):
        if not 0 <= v <= 11:
            raise ValueError("hour_branch: 0..11")
        return v, False
    s = str(v).strip()
    if s in ("晚子", "late_zi", "晚子时"):
        return 0, True
    s = s.rstrip("时")
    if s in BRANCHES:
        return BRANCHES.index(s), False
    if s.isdigit():
        return _parse_hour_branch(int(s))
    raise ValueError(f"hour_branch не распознан: {v!r}")


# ---------------------------------------------------------------------------
# Основной расчёт
# ---------------------------------------------------------------------------

def calculate(b: BirthInput, **options: Any) -> dict:
    """Построить карту Цзы Вэй Доу Шу. Опции — см. DEFAULTS и базу знаний (раздел 1)."""
    unknown = set(options) - set(DEFAULTS)
    if unknown:
        raise ValueError(f"Неизвестные опции: {sorted(unknown)}")
    opt = {**DEFAULTS, **options}
    # синонимы опций, совместимые с calculators/bazi.py
    if opt["solar_time"] is not None and opt["time_basis"] is None:
        st = {"true": "true_solar", "mean": "mean_solar", "clock": "clock"}
        if opt["solar_time"] not in st:
            raise ValueError("solar_time: true | mean | clock")
        opt["time_basis"] = st[opt["solar_time"]]
    opt["zi_hour"] = {"early": "next_day", "late": "same_day"}.get(opt["zi_hour"], opt["zi_hour"])
    for key, allowed in (("zi_hour", ("next_day", "same_day")),
                         ("year_boundary", ("lunar_new_year", "lichun")),
                         ("leap_month", ("split_15", "same", "next")),
                         ("sihua", tuple(SIHUA_TABLES)),
                         ("kui_yue", tuple(KUIYUE)),
                         ("ming_zhu", ("ming_branch", "year_branch"))):
        if opt[key] not in allowed:
            raise ValueError(f"{key}: допустимо {allowed}")
    warnings: list[str] = []
    steps: list[str] = []

    if not b.has_time and opt["hour_branch"] is None:
        return _partial_without_time(b, opt, warnings)

    # --- 1. Момент и опорное время ----------------------------------------
    norm = None
    if b.has_time and b.tz is not None:
        norm = normalize(b)
        warnings.extend(norm.warnings)
    basis = opt["time_basis"]
    if basis is None:
        basis = "true_solar" if (b.lon is not None and norm is not None) else "clock"
    if basis not in ("clock", "true_solar", "mean_solar"):
        raise ValueError("time_basis: clock | true_solar | mean_solar")
    if basis != "clock" and (b.lon is None or norm is None):
        raise ValueError("Для time_basis=true_solar/mean_solar нужны долгота и часовой пояс/место.")

    late_zi = False
    alt: dict[str, str] = {}
    if opt["hour_branch"] is not None:
        hb, late_zi = _parse_hour_branch(opt["hour_branch"])
        basis_dt = datetime(b.year, b.month, b.day, 23 if late_zi else (b.hour or 12), 30 if late_zi else (b.minute or 0))
        basis = "explicit_hour_branch"
        steps.append(f"Час-ветвь задана явно: {BRANCHES[hb]}{'(поздний Цзы)' if late_zi else ''}.")
    else:
        clock_dt = datetime(b.year, b.month, b.day, b.hour, b.minute or 0)
        if basis == "clock":
            basis_dt = clock_dt
        elif basis == "true_solar":
            basis_dt = true_solar_time(norm.utc, b.lon)
        else:
            basis_dt = local_mean_time(norm.utc, b.lon)
        hb = hour_branch_index(basis_dt.hour, basis_dt.minute)
        late_zi = basis_dt.hour == 23
        steps.append(
            f"Опорное время ({basis}): {basis_dt:%Y-%m-%d %H:%M}"
            + (f" (часы показывали {clock_dt:%H:%M}, {fmt_offset(norm.utc_offset_hours)})" if norm else "")
            + f" -> час {BRANCHES[hb]} ({HOUR_RANGES[hb]})" + (", поздний Цзы (晚子)" if late_zi else "") + "."
        )
        # проверка: другая основа времени даёт другой час?
        if norm is not None:
            cands = {"clock": clock_dt}
            if b.lon is not None:
                cands["true_solar"] = true_solar_time(norm.utc, b.lon)
                cands["mean_solar"] = local_mean_time(norm.utc, b.lon)
            for k, dt in cands.items():
                h2 = hour_branch_index(dt.hour, dt.minute)
                alt[k] = f"{dt:%Y-%m-%d %H:%M} {BRANCHES[h2]}"
                if h2 != hb or dt.date() != basis_dt.date():
                    warnings.append(
                        f"По основе времени «{k}» ({dt:%Y-%m-%d %H:%M}) час-ветвь {BRANCHES[h2]} — карта будет "
                        f"другой. Сейчас использовано «{basis}» ({BRANCHES[hb]})."
                    )
        minutes = basis_dt.hour * 60 + basis_dt.minute + basis_dt.second / 60
        # границы двухчасовых периодов — нечётные часы 01:00, 03:00, …, 23:00
        dist = min(min(abs(minutes - bnd), 1440 - abs(minutes - bnd)) for bnd in range(60, 1440, 120))
        if dist <= 10:
            warnings.append("Время в пределах 10 минут от границы двухчасового периода — проверьте соседний час.")

    # --- 2. Лунная дата ---------------------------------------------------
    chart_date = basis_dt.date()
    if late_zi and opt["zi_hour"] == "next_day":
        chart_date = chart_date + timedelta(days=1)
        steps.append(f"Поздний Цзы, правило «следующий день» (隔夜晚子): дата карты {chart_date}.")
    elif late_zi:
        steps.append(f"Поздний Цзы, правило «тот же день»: дата карты {chart_date}.")
    lunar = _lunar_of(chart_date)
    l_year, l_month_raw, l_day = lunar.getYear(), lunar.getMonth(), lunar.getDay()
    is_leap = l_month_raw < 0
    l_month = abs(l_month_raw)
    days_in_month = LunarMonth.fromYm(l_year, l_month_raw).getDayCount()
    chart_month = l_month
    if is_leap:
        rule = opt["leap_month"]
        if rule == "next" or (rule == "split_15" and l_day > 15):
            chart_month = l_month % 12 + 1
        warnings.append(
            f"Рождение в високосном месяце (闰{l_month}月, день {l_day}). Правило «{rule}»: для карты взят "
            f"{chart_month}-й месяц. Другие школы: same -> {l_month}, next -> {l_month % 12 + 1}."
        )
    steps.append(
        f"Лунная дата: {l_year} г., {'闰' if is_leap else ''}{l_month}-й месяц, {l_day}-й день "
        f"(в месяце {days_in_month} дн.); месяц для карты: {chart_month}."
    )
    if norm is not None:
        w = _check_new_moon_timezone(lunar, chart_date, norm.utc_offset_hours)
        if w:
            warnings.append(w)

    # --- 3. Год ------------------------------------------------------------
    y_stem = (l_year - 4) % 10
    y_branch = (l_year - 4) % 12
    year_note = "по китайскому Новому году (正月初一)"
    if opt["year_boundary"] == "lichun":
        if norm is not None:
            # Момент Личуня (Солнце на 315°) сравниваем с реальным моментом рождения (UT),
            # поэтому часовой пояс места рождения учтён точно (а не по пекинскому времени).
            from .common.ephemeris import find_sun_longitude
            from .common.time import julian_day_ut
            lc = find_sun_longitude(315.0, julian_day_ut(datetime(b.year, 2, 25, tzinfo=timezone.utc)))
            sy = b.year if norm.jd_ut >= lc else b.year - 1
            y_stem, y_branch = (sy - 4) % 10, (sy - 4) % 12
        else:
            # без часового пояса — приближение lunar-python (Личунь по пекинскому времени)
            y_stem = STEMS.index(lunar.getYearGanByLiChun())
            y_branch = BRANCHES.index(lunar.getYearZhiByLiChun())
            warnings.append("Личунь определён по пекинскому времени (нет часового пояса).")
        year_note = "по Личуню (立春, долгота Солнца 315°)"
        if gz(y_stem, y_branch) != gz((l_year - 4) % 10, (l_year - 4) % 12):
            warnings.append(
                f"Год по Личуню ({gz(y_stem, y_branch)}) отличается от года по лунному Новому году "
                f"({gz((l_year - 4) % 10, (l_year - 4) % 12)}) — школьное расхождение влияет на всю карту."
            )
    else:
        # информативно: отличается ли год по Личуню
        lc_gz = lunar.getYearInGanZhiByLiChun()
        if lc_gz != gz(y_stem, y_branch):
            warnings.append(
                f"Рождение между Личунем и китайским Новым годом: по лунному году {gz(y_stem, y_branch)}, "
                f"по Личуню {lc_gz}. В Цзы Вэй по умолчанию берётся лунный год (опция year_boundary=lichun)."
            )
    steps.append(f"Год {year_note}: {gz(y_stem, y_branch)} ({'ян' if y_stem % 2 == 0 else 'инь'}).")

    # --- 4. Дворцы ---------------------------------------------------------
    m_br = ming_branch(chart_month, hb)
    s_br = body_branch(chart_month, hb)
    steps.append(
        f"命宫: от 寅 вперёд до {chart_month}-го месяца -> {BRANCHES[(YIN + chart_month - 1) % 12]}, "
        f"назад на {hb} (час {BRANCHES[hb]}) -> {BRANCHES[m_br]}. 身宫: вперёд на {hb} -> {BRANCHES[s_br]}."
    )
    ys = yin_stem(y_stem)
    steps.append(f"Стволы дворцов (五虎遁): год {STEMS[y_stem]} -> 寅 = {STEMS[ys]}寅, далее по порядку (子 = ствол 寅, 丑 = ствол 卯).")
    m_stem = palace_stem(y_stem, m_br)
    ny = nayin(m_stem, m_br)
    bureau = bureau_number(m_stem, m_br)
    steps.append(f"五行局: 命宫 {gz(m_stem, m_br)}, на-инь {ny} -> {BUREAU_NAMES[bureau]} (число {bureau}).")

    # --- 5. Звёзды ---------------------------------------------------------
    zw, zinfo = ziwei_branch(l_day, bureau)
    steps.append(
        f"紫微: день {l_day}, бюро {bureau}: x = {zinfo['x']}, q = ({l_day}+{zinfo['x']})/{bureau} = {zinfo['q']}; "
        f"от 寅 {zinfo['q']}-я ветвь = {zinfo['base_branch']}; x {'нечётно — назад' if zinfo['x'] % 2 else 'чётно — вперёд'} "
        f"на {zinfo['x']} -> {BRANCHES[zw]}. 天府 (зеркально по оси 寅—申) -> {BRANCHES[tianfu_branch(zw)]}."
    )
    majors = major_star_positions(zw)
    auxes = aux_star_positions(y_stem, y_branch, chart_month, hb, opt["kui_yue"])
    sihua = sihua_for_stem(y_stem, opt["sihua"])
    sihua_by_star = {star: k for k, star in sihua.items()}
    steps.append("四化 (" + opt["sihua"] + f", ствол {STEMS[y_stem]}): " +
                 ", ".join(f"{s}化{k}" for k, s in sihua.items()) + ".")

    all_pos = {**majors, **auxes}
    sihua_out = {k: {"star": s, "star_ru": STARS_RU.get(s, s), "branch": BRANCHES[all_pos[s]],
                     "meaning_ru": SIHUA_RU[k]} for k, s in sihua.items()}

    # --- 6. Пределы --------------------------------------------------------
    gender = b.gender
    decades: list[dict] = []
    forward = None
    if gender in ("male", "female"):
        forward = decade_forward(y_stem, gender)
        for i in range(12):
            br = (m_br + (i if forward else -i)) % 12
            decades.append({"ages": [bureau + 10 * i, bureau + 10 * i + 9], "branch": BRANCHES[br],
                            "stem_branch": gz(palace_stem(y_stem, br), br),
                            "palace": PALACES[(m_br - br) % 12][0]})
        steps.append(
            f"大限: {'ян' if y_stem % 2 == 0 else 'инь'}ский год, {'мужчина' if gender == 'male' else 'женщина'} -> "
            f"{'вперёд (順)' if forward else 'назад (逆)'}; первый период {bureau}–{bureau + 9} лет (虚岁) в 命宫."
        )
    else:
        warnings.append("Пол не указан: десятилетия (大限) и малые пределы (小限) не рассчитаны.")

    minor_ages: dict[int, list[int]] = {}
    if gender in ("male", "female"):
        start = _sanhe(y_branch)["xiaoxian"]
        step = 1 if gender == "male" else -1
        for k in range(12):
            br = (start + step * k) % 12
            minor_ages[br] = [k + 1 + 12 * j for j in range(10)]

    # --- 7. Сборка дворцов -------------------------------------------------
    palaces: list[dict] = []
    for i, (pname, pru) in enumerate(PALACES):
        br = (m_br - i) % 12
        st = palace_stem(y_stem, br)
        maj = [_star_entry(s, br, sihua_by_star) for s in MAJOR_STARS if majors[s] == br]
        aux = [_star_entry(s, br, sihua_by_star) for s in AUX_STARS if auxes[s] == br]
        dec = next((d["ages"] for d in decades if d["branch"] == BRANCHES[br]), None)
        palaces.append({
            "name": pname, "name_ru": pru, "branch": BRANCHES[br], "stem": STEMS[st], "stem_branch": gz(st, br),
            "is_body_palace": br == s_br, "major_stars": maj, "aux_stars": aux,
            # 三方四正: сам дворец + противоположный (+6) + два «треугольных» (+4, +8)
            "san_fang_si_zheng": [BRANCHES[(br + d) % 12] for d in (0, 6, 4, 8)],
            "empty": not maj,
            "opposite_major_stars": [s for s in MAJOR_STARS if majors[s] == (br + 6) % 12] if not maj else [],
            "decade_ages": dec, "minor_limit_ages": minor_ages.get(br),
        })

    body_palace_name = PALACES[(m_br - s_br) % 12][0]
    mz_branch = m_br if opt["ming_zhu"] == "ming_branch" else y_branch
    result: dict[str, Any] = {
        "method": "ziwei_doushu",
        "variant": {k: opt[k] for k in ("zi_hour", "year_boundary", "leap_month", "sihua", "kui_yue", "ming_zhu")}
        | {"time_basis": basis, "brightness_table": "iztro-2.6.2 (⚠ школы расходятся)"},
        "inputs_used": {
            "local_input": f"{b.year:04d}-{b.month:02d}-{b.day:02d} " + (f"{b.hour:02d}:{(b.minute or 0):02d}" if b.has_time else "—"),
            "tz": b.tz, "lon": b.lon, "gender": gender,
            "basis_time": f"{basis_dt:%Y-%m-%d %H:%M}",
            "chart_date": chart_date.isoformat(),
            "time_alternatives": alt,
        },
        "warnings": warnings,
        "lunar_date": {"year": l_year, "month": l_month, "day": l_day, "is_leap_month": is_leap,
                       "days_in_month": days_in_month, "month_used": chart_month, "text": lunar.toString(),
                       "calendar_text": _lunar_of(basis_dt.date()).toString()},
        "year": {"stem_branch": gz(y_stem, y_branch), "stem": STEMS[y_stem], "branch": BRANCHES[y_branch],
                 "yin_yang": "yang" if y_stem % 2 == 0 else "yin", "animal_ru": BRANCH_ANIMALS_RU[y_branch]},
        "hour": {"branch": BRANCHES[hb], "index": hb, "range": HOUR_RANGES[hb], "late_zi": late_zi},
        "ming_palace": {"branch": BRANCHES[m_br], "stem_branch": gz(m_stem, m_br)},
        "body_palace": {"branch": BRANCHES[s_br], "in_palace": body_palace_name},
        "bureau": {"number": bureau, "name": BUREAU_NAMES[bureau], "name_ru": BUREAU_RU[bureau], "nayin": ny},
        "ming_zhu": MING_ZHU[mz_branch],
        "shen_zhu": SHEN_ZHU[y_branch],
        "star_positions": {s: BRANCHES[all_pos[s]] for s in MAJOR_STARS + AUX_STARS},
        "sihua": sihua_out,
        "palaces": palaces,
        "decades": decades,
        "decade_direction": None if forward is None else ("forward" if forward else "backward"),
        "steps": steps,
    }
    if opt["flow_year"] is not None:
        result["flow_year"] = flow_year(result, int(opt["flow_year"]), opt["sihua"])
    return result


def _star_entry(star: str, br: int, sihua_by_star: dict[str, str]) -> dict:
    return {"star": star, "star_ru": STARS_RU[star], "brightness": BRIGHTNESS.get(star, [""] * 12)[br],
            "sihua": sihua_by_star.get(star, "")}


def flow_year(chart: dict, year: int, sihua_table: str = "quanji") -> dict:
    """Основы года (流年) для лунного года `year` (номер = григорианский год, в котором начался)."""
    stem, branch = (year - 4) % 10, (year - 4) % 12
    birth_lunar_year = chart["lunar_date"]["year"]
    age = year - birth_lunar_year + 1  # номинальный возраст (虚岁)
    by_branch = {p["branch"]: p for p in chart["palaces"]}
    ming = by_branch[BRANCHES[branch]]
    decade = next((d for d in chart["decades"] if d["ages"][0] <= age <= d["ages"][1]), None)
    minor = next((p["branch"] for p in chart["palaces"] if p["minor_limit_ages"] and age in p["minor_limit_ages"]), None)
    sh = sihua_for_stem(stem, sihua_table)
    pos = chart["star_positions"]
    out = {
        "year": year, "stem_branch": gz(stem, branch), "nominal_age": age,
        "flow_ming_branch": BRANCHES[branch], "flow_ming_natal_palace": ming["name"],
        "flow_sihua": {k: {"star": s, "natal_branch": pos.get(s)} for k, s in sh.items()},
        "decade": decade, "minor_limit_branch": minor,
    }
    if decade:
        d_stem = STEMS.index(decade["stem_branch"][0])
        out["decade_sihua"] = {k: {"star": s, "natal_branch": pos.get(s)} for k, s in sihua_for_stem(d_stem, sihua_table).items()}
    return out


def _partial_without_time(b: BirthInput, opt: dict, warnings: list[str]) -> dict:
    """Без времени: только то, что не зависит от часа + 12 вариантов 命宫/бюро/紫微."""
    warnings.append("Время рождения неизвестно: 命宫, 身宫, бюро, 紫微 и часовые звёзды не определены — "
                    "ниже 12 вариантов по часам. Звёзды года и месяца определены.")
    d = date(b.year, b.month, b.day)
    lunar = _lunar_of(d)
    l_year, l_raw, l_day = lunar.getYear(), lunar.getMonth(), lunar.getDay()
    l_month = abs(l_raw)
    chart_month = l_month
    if l_raw < 0 and (opt["leap_month"] == "next" or (opt["leap_month"] == "split_15" and l_day > 15)):
        chart_month = l_month % 12 + 1
    y_stem, y_branch = (l_year - 4) % 10, (l_year - 4) % 12
    aux = aux_star_positions(y_stem, y_branch, chart_month, 0, opt["kui_yue"])
    year_month_stars = {k: BRANCHES[v] for k, v in aux.items() if k in ("左辅", "右弼", "天魁", "天钺", "禄存", "擎羊", "陀罗", "天马")}
    cands = []
    for h in range(12):
        mb = ming_branch(chart_month, h)
        st = palace_stem(y_stem, mb)
        bu = bureau_number(st, mb)
        zw, _ = ziwei_branch(l_day, bu)
        cands.append({"hour_branch": BRANCHES[h], "range": HOUR_RANGES[h], "ming": gz(st, mb),
                      "body": BRANCHES[body_branch(chart_month, h)], "bureau": BUREAU_NAMES[bu], "ziwei": BRANCHES[zw]})
    return {
        "method": "ziwei_doushu", "variant": {k: opt[k] for k in ("year_boundary", "leap_month", "sihua", "kui_yue")},
        "inputs_used": {"date": d.isoformat(), "gender": b.gender}, "warnings": warnings, "status": "partial",
        "lunar_date": {"year": l_year, "month": l_month, "day": l_day, "is_leap_month": l_raw < 0,
                       "month_used": chart_month, "text": lunar.toString()},
        "year": {"stem_branch": gz(y_stem, y_branch)},
        "sihua": sihua_for_stem(y_stem, opt["sihua"]),
        "year_month_stars": year_month_stars,
        "candidates_by_hour": cands,
        "steps": ["Без часа рождения карта строится только по году/месяцу/дню; см. candidates_by_hour."],
    }
