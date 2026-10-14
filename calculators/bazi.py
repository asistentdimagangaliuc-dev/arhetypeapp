"""Ба-цзы (八字, 四柱命理 — «Четыре столпа судьбы»), классическая школа Цзы Пин (子平).

Калькулятор написан с нуля: солнечные термины (节, цзе) ищутся через Swiss Ephemeris
(`common.ephemeris.find_sun_longitude`) в UT, шестидесятеричная арифметика своя.
lunar-python используется ТОЛЬКО в тестах для сверки.

Принятые по умолчанию соглашения (подробно — knowledge-base/01-bazi.md):
* Граница года — Личунь (立春, долгота Солнца 315°), а не китайский Новый год.
* Граница месяца — 12 «цзе» (节): 315°, 345°, 15°, …, 285° (каждые 30°).
* Столп дня — по гражданской дате в выбранной шкале «времени карты»:
  индекс = (JDN + 49) mod 60, где JDN — номер юлианского дня (полдень даты).
* zi_hour='late' (по умолчанию): 23:00–24:00 — «поздний час Крысы» (晚子时/夜子时):
  столп дня НЕ меняется, ствол часа берётся как у следующего дня (Joey Yap / Mastery
  Academy, mingli.ru, lunar-python sect=2). zi_hour='early': день меняется в 23:00
  (子初换日, вся двухчасовка Цзы относится к следующему дню; lunar-python sect=1).
* solar_time='true' (по умолчанию): часы считаются по истинному солнечному времени
  места (真太阳时) = UTC + долгота/15 + уравнение времени. 'mean' — местное среднее
  солнечное время (LMT, так делает mingli.ru), 'clock' — часы как ввёл пользователь.
* Начало Столпов удачи (大运): 3 дня до/после ближайшего цзе = 1 год (1 день = 4 мес.,
  1 час = 5 дней, 1 мин = 2 часа).
"""
from __future__ import annotations

from dataclasses import replace
from datetime import date, datetime, timedelta, timezone

import swisseph as swe

from calculators.common.ephemeris import find_sun_longitude, sun_longitude
from calculators.common.time import (
    BirthInput,
    fmt_offset,
    jd_to_utc,
    local_mean_time,
    normalize,
    true_solar_time,
)

# ---------------------------------------------------------------------------
# Справочники
# ---------------------------------------------------------------------------

ELEMENTS = ["wood", "fire", "earth", "metal", "water"]
ELEMENT_RU = {"wood": "Дерево", "fire": "Огонь", "earth": "Земля", "metal": "Металл", "water": "Вода"}
ELEMENT_CN = {"wood": "木", "fire": "火", "earth": "土", "metal": "金", "water": "水"}
POLARITY_RU = {"yang": "Ян", "yin": "Инь"}

# (иероглиф, пиньинь, русское чтение (Палладий), образ)
STEMS = [
    ("甲", "jiǎ", "Цзя", "большое дерево, сосна"),
    ("乙", "yǐ", "И", "трава, цветы, лиана"),
    ("丙", "bǐng", "Бин", "Солнце"),
    ("丁", "dīng", "Дин", "свеча, пламя лампы"),
    ("戊", "wù", "У", "гора, скала"),
    ("己", "jǐ", "Цзи", "плодородная почва, поле"),
    ("庚", "gēng", "Гэн", "руда, топор, меч"),
    ("辛", "xīn", "Синь", "ювелирное украшение, игла"),
    ("壬", "rén", "Жэнь", "океан, большая река"),
    ("癸", "guǐ", "Гуй", "дождь, роса, туман"),
]

# (иероглиф, пиньинь, русское чтение, животное, элемент, интервал часов, месяц (цзе))
BRANCHES = [
    ("子", "zǐ", "Цзы", "Крыса", "water", "23:00–01:00", "大雪 Дасюэ 255° (~7 дек) – 小寒 (~6 янв)"),
    ("丑", "chǒu", "Чоу", "Бык", "earth", "01:00–03:00", "小寒 Сяохань 285° (~6 янв) – 立春 (~4 фев)"),
    ("寅", "yín", "Инь", "Тигр", "wood", "03:00–05:00", "立春 Личунь 315° (~4 фев) – 惊蛰 (~6 мар)"),
    ("卯", "mǎo", "Мао", "Кролик (Заяц)", "wood", "05:00–07:00", "惊蛰 Цзинчжэ 345° (~6 мар) – 清明 (~5 апр)"),
    ("辰", "chén", "Чэнь", "Дракон", "earth", "07:00–09:00", "清明 Цинмин 15° (~5 апр) – 立夏 (~6 мая)"),
    ("巳", "sì", "Сы", "Змея", "fire", "09:00–11:00", "立夏 Лися 45° (~6 мая) – 芒种 (~6 июн)"),
    ("午", "wǔ", "У", "Лошадь", "fire", "11:00–13:00", "芒种 Манчжун 75° (~6 июн) – 小暑 (~7 июл)"),
    ("未", "wèi", "Вэй", "Коза (Овца)", "earth", "13:00–15:00", "小暑 Сяошу 105° (~7 июл) – 立秋 (~8 авг)"),
    ("申", "shēn", "Шэнь", "Обезьяна", "metal", "15:00–17:00", "立秋 Лицю 135° (~8 авг) – 白露 (~8 сен)"),
    ("酉", "yǒu", "Ю", "Петух", "metal", "17:00–19:00", "白露 Байлу 165° (~8 сен) – 寒露 (~8 окт)"),
    ("戌", "xū", "Сюй", "Собака", "earth", "19:00–21:00", "寒露 Ханьлу 195° (~8 окт) – 立冬 (~7 ноя)"),
    ("亥", "hài", "Хай", "Свинья (Кабан)", "water", "21:00–23:00", "立冬 Лидун 225° (~7 ноя) – 大雪 (~7 дек)"),
]

# 12 «цзе» (节) — границы месяцев. Индекс 0 = месяц 寅.
JIE = [
    (315, "立春", "Личунь", "Начало весны"),
    (345, "惊蛰", "Цзинчжэ", "Пробуждение насекомых"),
    (15, "清明", "Цинмин", "Чистый свет"),
    (45, "立夏", "Лися", "Начало лета"),
    (75, "芒种", "Манчжун", "Колошение хлебов"),
    (105, "小暑", "Сяошу", "Малая жара"),
    (135, "立秋", "Лицю", "Начало осени"),
    (165, "白露", "Байлу", "Белые росы"),
    (195, "寒露", "Ханьлу", "Холодные росы"),
    (225, "立冬", "Лидун", "Начало зимы"),
    (255, "大雪", "Дасюэ", "Большой снег"),
    (285, "小寒", "Сяохань", "Малые холода"),
]

# Скрытые стволы (藏干): (индекс ствола, роль, доля). Порядок как в lunar-python/«三命通会».
# Доли 0.6/0.3/0.1 (три ствола), 0.7/0.3 (два), 1.0 (один) — соглашение этого калькулятора
# (⚠ веса зависят от школы; «по дням» — см. базу знаний).
HIDDEN_STEMS: dict[int, list[tuple[int, str, float]]] = {
    0: [(9, "main", 1.0)],                                           # 子: 癸
    1: [(5, "main", 0.6), (9, "residual", 0.3), (7, "middle", 0.1)],  # 丑: 己 癸 辛
    2: [(0, "main", 0.6), (2, "middle", 0.3), (4, "residual", 0.1)],  # 寅: 甲 丙 戊
    3: [(1, "main", 1.0)],                                           # 卯: 乙
    4: [(4, "main", 0.6), (1, "residual", 0.3), (9, "middle", 0.1)],  # 辰: 戊 乙 癸
    5: [(2, "main", 0.6), (6, "middle", 0.3), (4, "residual", 0.1)],  # 巳: 丙 庚 戊
    6: [(3, "main", 0.7), (5, "middle", 0.3)],                        # 午: 丁 己
    7: [(5, "main", 0.6), (3, "residual", 0.3), (1, "middle", 0.1)],  # 未: 己 丁 乙
    8: [(6, "main", 0.6), (8, "middle", 0.3), (4, "residual", 0.1)],  # 申: 庚 壬 戊
    9: [(7, "main", 1.0)],                                           # 酉: 辛
    10: [(4, "main", 0.6), (7, "residual", 0.3), (3, "middle", 0.1)],  # 戌: 戊 辛 丁
    11: [(8, "main", 0.7), (0, "middle", 0.3)],                       # 亥: 壬 甲
}
HIDDEN_ROLE_RU = {"main": "основная ци (本气)", "middle": "средняя ци (中气)", "residual": "остаточная ци (余气)"}

# Десять божеств (十神): ключ (отношение, та же полярность?)
# отношение d = (элемент_другого − элемент_ДМ) mod 5:
# 0 — тот же элемент, 1 — ДМ порождает, 2 — ДМ контролирует, 3 — контролирует ДМ, 4 — порождает ДМ.
TEN_GODS = {
    (0, True): ("比肩", "bǐ jiān", "Friend", "Друг", ["Братство", "Плечо к плечу", "Компаньон"]),
    (0, False): ("劫财", "jié cái", "Rob Wealth", "Грабитель Богатства", ["Соперник", "Похититель богатства"]),
    (1, True): ("食神", "shí shén", "Eating God", "Бог Еды", ["Дух Наслаждения", "Божество пищи"]),
    (1, False): ("伤官", "shāng guān", "Hurting Officer", "Ранящий Офицер", ["Вызов власти", "Ранящий Чиновник", "Повреждающий чиновник"]),
    (2, True): ("偏财", "piān cái", "Indirect Wealth", "Непрямое Богатство", ["Косвенное богатство", "Склонность к богатству"]),
    (2, False): ("正财", "zhèng cái", "Direct Wealth", "Прямое Богатство", []),
    (3, True): ("七杀", "qī shā", "Seven Killings", "Семь Убийц", ["7 убийц", "Убийца на 7 позиции", "Непрямой Офицер (偏官)"]),
    (3, False): ("正官", "zhèng guān", "Direct Officer", "Прямой Офицер", ["Чиновник", "Прямой чиновник"]),
    (4, True): ("偏印", "piān yìn", "Indirect Resource", "Непрямой Ресурс", ["Косвенный Ресурс", "Косая Печать", "Косвенная печать", "枭神"]),
    (4, False): ("正印", "zhèng yìn", "Direct Resource", "Прямой Ресурс", ["Правильная Печать", "Прямая печать"]),
}

# 12 стадий жизненного цикла (十二长生)
LIFE_STAGES = [
    ("长生", "Рождение (Долголетие)"),
    ("沐浴", "Омовение"),
    ("冠带", "Облачение (Пояс и шапка)"),
    ("临官", "Должность (建禄, Становление)"),
    ("帝旺", "Расцвет (Император)"),
    ("衰", "Упадок"),
    ("病", "Болезнь"),
    ("死", "Смерть"),
    ("墓", "Могила (Хранилище)"),
    ("绝", "Исчезновение (Пустота)"),
    ("胎", "Зачатие (Зародыш)"),
    ("养", "Вскармливание"),
]
# ветвь «Рождения» (长生) для каждого ствола; Ян — по кругу вперёд, Инь — назад (阳顺阴逆).
# 戊 следует за 丙, 己 — за 丁 (火土同宫, наиболее распространённый вариант).
CHANG_SHENG_START = {0: 11, 1: 6, 2: 2, 3: 9, 4: 2, 5: 9, 6: 5, 7: 0, 8: 8, 9: 3}

# Звук Наинь (纳音): 30 названий, по одному на пару соседних столпов цикла.
NAYIN = [
    ("海中金", "Золото в море", "metal"), ("炉中火", "Огонь в очаге", "fire"),
    ("大林木", "Дерево большого леса", "wood"), ("路旁土", "Земля у дороги", "earth"),
    ("剑锋金", "Металл острия меча", "metal"), ("山头火", "Огонь на вершине горы", "fire"),
    ("涧下水", "Вода горного ручья", "water"), ("城头土", "Земля городской стены", "earth"),
    ("白蜡金", "Металл белого воска", "metal"), ("杨柳木", "Дерево ивы", "wood"),
    ("泉中水", "Вода источника", "water"), ("屋上土", "Земля на крыше", "earth"),
    ("霹雳火", "Огонь молнии", "fire"), ("松柏木", "Дерево сосны и кипариса", "wood"),
    ("长流水", "Вода длинной реки", "water"), ("沙中金", "Золото в песке", "metal"),
    ("山下火", "Огонь у подножия горы", "fire"), ("平地木", "Дерево равнины", "wood"),
    ("壁上土", "Земля на стене", "earth"), ("金箔金", "Металл золотой фольги", "metal"),
    ("覆灯火", "Огонь лампады", "fire"), ("天河水", "Вода Небесной реки", "water"),
    ("大驿土", "Земля большого тракта", "earth"), ("钗钏金", "Металл шпилек и браслетов", "metal"),
    ("桑柘木", "Дерево шелковицы", "wood"), ("大溪水", "Вода большого ручья", "water"),
    ("沙中土", "Земля в песке", "earth"), ("天上火", "Огонь в небе", "fire"),
    ("石榴木", "Дерево граната", "wood"), ("大海水", "Вода великого моря", "water"),
]

SEASON_STATES = {0: ("旺", "Процветание"), 1: ("相", "Рост (Министр)"), 4: ("休", "Отдых"),
                 3: ("囚", "Заключение"), 2: ("死", "Смерть")}

# --- взаимодействия ---
STEM_COMBOS = {frozenset({0, 5}): "earth", frozenset({1, 6}): "metal", frozenset({2, 7}): "water",
               frozenset({3, 8}): "wood", frozenset({4, 9}): "fire"}
STEM_CLASHES = {frozenset({0, 6}), frozenset({1, 7}), frozenset({2, 8}), frozenset({3, 9})}
SIX_COMBOS = {frozenset({0, 1}): "earth", frozenset({2, 11}): "wood", frozenset({3, 10}): "fire",
              frozenset({4, 9}): "metal", frozenset({5, 8}): "water", frozenset({6, 7}): "fire/earth"}
THREE_HARMONIES = [((8, 0, 4), "water"), ((11, 3, 7), "wood"), ((2, 6, 10), "fire"), ((5, 9, 1), "metal")]
DIRECTIONAL = [((2, 3, 4), "wood"), ((5, 6, 7), "fire"), ((8, 9, 10), "metal"), ((11, 0, 1), "water")]
HARMS = {frozenset(p) for p in [(0, 7), (1, 6), (2, 5), (3, 4), (8, 11), (9, 10)]}
DESTRUCTIONS = {frozenset(p) for p in [(0, 9), (3, 6), (4, 1), (7, 10), (2, 11), (5, 8)]}
PUNISHMENT_GROUPS = [((2, 5, 8), "无恩之刑 — наказание неблагодарности"),
                     ((1, 10, 7), "恃势之刑 — наказание злоупотребления силой")]
PUNISHMENT_PAIR = (frozenset({0, 3}), "无礼之刑 — наказание неучтивости (子卯)")
SELF_PUNISH = {4, 6, 9, 11}  # 辰 午 酉 亥

# --- символические звёзды (神煞) ---
# Благородный человек (天乙贵人), основной вариант «甲戊庚牛羊…六辛逢马虎»
NOBLEMAN = {0: (1, 7), 4: (1, 7), 6: (1, 7), 1: (0, 8), 5: (0, 8), 2: (11, 9), 3: (11, 9),
            7: (2, 6), 8: (3, 5), 9: (3, 5)}
# вариант «庚辛逢虎马»: 庚 -> 寅午
NOBLEMAN_ALT = {**NOBLEMAN, 6: (2, 6)}
ACADEMIC = {0: 5, 1: 6, 2: 8, 3: 9, 4: 8, 5: 9, 6: 11, 7: 0, 8: 2, 9: 3}  # 文昌
# по тройке (三合) ветви года/дня: 申子辰, 寅午戌, 巳酉丑, 亥卯未
TRINE_OF = {8: 0, 0: 0, 4: 0, 2: 1, 6: 1, 10: 1, 5: 2, 9: 2, 1: 2, 11: 3, 3: 3, 7: 3}
PEACH = {0: 9, 1: 3, 2: 6, 3: 0}     # 桃花 (咸池)
HORSE = {0: 2, 1: 8, 2: 11, 3: 5}    # 驿马
CANOPY = {0: 4, 1: 10, 2: 1, 3: 7}   # 华盖

PILLAR_KEYS = ["year", "month", "day", "hour"]
PILLAR_RU = {"year": "год", "month": "месяц", "day": "день", "hour": "час"}
PILLAR_RU_GEN = {"year": "года", "month": "месяца", "day": "дня", "hour": "часа"}

# ---------------------------------------------------------------------------
# Базовая шестидесятеричная арифметика
# ---------------------------------------------------------------------------


def stem_element(s: int) -> str:
    return ELEMENTS[s // 2]


def stem_polarity(s: int) -> str:
    return "yang" if s % 2 == 0 else "yin"


def branch_element(b: int) -> str:
    return BRANCHES[b][4]


def branch_polarity(b: int) -> str:
    """Полярность по порядку (子 — Ян). ⚠ «по применению» 子/午 — Инь, 巳/亥 — Ян."""
    return "yang" if b % 2 == 0 else "yin"


def ganzhi_index(stem: int, branch: int) -> int:
    """Номер пары в цикле 60 (0 = 甲子). Определён, только если stem ≡ branch (mod 2)."""
    if (stem - branch) % 2:
        raise ValueError("Ствол и ветвь разной полярности — такой пары в цикле нет")
    return (6 * stem - 5 * branch) % 60


def ganzhi(idx: int) -> str:
    idx %= 60
    return STEMS[idx % 10][0] + BRANCHES[idx % 12][0]


def jdn(d: date) -> int:
    """Номер юлианского дня (целый, полдень гражданской даты, пролептический григорианский)."""
    return int(round(swe.julday(d.year, d.month, d.day, 12.0, swe.GREG_CAL)))


def day_index(d: date) -> int:
    """Индекс столпа дня: (JDN + 49) mod 60. Проверка: 01.10.1949 → 0 (甲子)."""
    return (jdn(d) + 49) % 60


def year_index(bazi_year: int) -> int:
    """Индекс столпа года по «году Ба-цзы» (начинается в Личунь): (Y − 4) mod 60."""
    return (bazi_year - 4) % 60


def month_first_stem(year_stem: int) -> int:
    """Правило пяти тигров (五虎遁): ствол месяца 寅 по стволу года."""
    return (year_stem % 5 * 2 + 2) % 10


def zi_first_stem(day_stem: int) -> int:
    """Правило пяти крыс (五鼠遁): ствол часа 子 по стволу дня."""
    return (day_stem % 5) * 2


def hour_branch(minutes_of_day: float) -> int:
    """Ветвь часа по минутам от полуночи: 23:00–00:59 → 子 (0), 01:00–02:59 → 丑 …"""
    return int(((minutes_of_day + 60) // 120) % 12)


def ten_god(dm_stem: int, other_stem: int) -> dict:
    d = (ELEMENTS.index(stem_element(other_stem)) - ELEMENTS.index(stem_element(dm_stem))) % 5
    same = (dm_stem % 2) == (other_stem % 2)
    cn, py, en, ru, alt = TEN_GODS[(d, same)]
    return {"cn": cn, "pinyin": py, "en": en, "ru": ru, "ru_alt": alt}


def life_stage(stem: int, branch: int) -> dict:
    start = CHANG_SHENG_START[stem]
    k = (branch - start) % 12 if stem % 2 == 0 else (start - branch) % 12
    return {"index": k + 1, "cn": LIFE_STAGES[k][0], "ru": LIFE_STAGES[k][1]}


def nayin(idx: int) -> dict:
    cn, ru, el = NAYIN[(idx % 60) // 2]
    return {"cn": cn, "ru": ru, "element": el, "element_ru": ELEMENT_RU[el]}


def season_state(element: str, month_branch: int) -> dict:
    """旺相休囚死 элемента в месяце рождения."""
    if month_branch in (2, 3):
        s = "wood"
    elif month_branch in (5, 6):
        s = "fire"
    elif month_branch in (8, 9):
        s = "metal"
    elif month_branch in (11, 0):
        s = "water"
    else:
        s = "earth"
    rel = (ELEMENTS.index(element) - ELEMENTS.index(s)) % 5
    cn, ru = SEASON_STATES[rel]
    return {"cn": cn, "ru": ru, "season_element": s}


def stem_info(s: int) -> dict:
    hz, py, ru, img = STEMS[s]
    el, pol = stem_element(s), stem_polarity(s)
    return {"index": s, "cn": hz, "pinyin": py, "ru": ru, "element": el, "polarity": pol,
            "name_ru": f"{POLARITY_RU[pol]} {ELEMENT_RU[el]}", "image": img}


def branch_info(b: int) -> dict:
    hz, py, ru, animal, el, hours, _m = BRANCHES[b]
    return {"index": b, "cn": hz, "pinyin": py, "ru": ru, "animal": animal, "element": el,
            "polarity": branch_polarity(b), "hours": hours}


def pillar_brief(idx: int) -> dict:
    s, b = idx % 10, idx % 12
    return {"index": idx, "ganzhi": ganzhi(idx),
            "ru": f"{STEMS[s][2]}-{BRANCHES[b][2]} ({POLARITY_RU[stem_polarity(s)]} {ELEMENT_RU[stem_element(s)]} — {BRANCHES[b][3]})"}


def annual_pillar(year: int) -> dict:
    """Столп года (流年) для года Y: действует с Личуня года Y до Личуня Y+1."""
    return {"year": year, **pillar_brief(year_index(year))}


# ---------------------------------------------------------------------------
# Астрономия: цзе и Личунь (всё в UT)
# ---------------------------------------------------------------------------


def li_chun_jd(year: int) -> float:
    """Момент Личуня (Солнце 315°) григорианского года year, JD UT."""
    return find_sun_longitude(315.0, swe.julday(year, 2, 20, 0.0), search_back=True)


def month_slot(sun_lon: float) -> int:
    """Номер месяца Ба-цзы по долготе Солнца: 0 = 寅 (315°…345°), 11 = 丑."""
    return int(((sun_lon - 315.0) % 360.0) // 30.0)


def _local_converter(tz: str, offset_source: str, offset_h: float):
    """Функция JD(UT) → местное время для сообщений (с учётом истории пояса)."""
    if offset_source == "tzdb":
        from zoneinfo import ZoneInfo
        z = ZoneInfo(tz)
        return lambda jd: _iso(jd_to_utc(jd).astimezone(z).replace(tzinfo=None))
    return lambda jd: _iso((jd_to_utc(jd) + timedelta(hours=offset_h)).replace(tzinfo=None))


def _iso(dt: datetime) -> str:
    return dt.replace(microsecond=0).isoformat()


def _jd_iso(jd: float, offset_h: float | None = None) -> str:
    t = jd_to_utc(jd)
    if offset_h is None:
        return _iso(t.astimezone(timezone.utc)).replace("+00:00", "Z")
    return _iso((t + timedelta(hours=offset_h)).replace(tzinfo=None))


def _add_ymd(dt: datetime, years: int, months: int, days: int, hours: float = 0.0) -> datetime:
    """Календарное прибавление лет/месяцев/дней (как в lunar-python, 29.02 → 28.02)."""
    m0 = dt.month - 1 + months
    y = dt.year + years + m0 // 12
    m = m0 % 12 + 1
    d = dt.day
    while True:
        try:
            base = dt.replace(year=y, month=m, day=d)
            break
        except ValueError:
            d -= 1
    return base + timedelta(days=days, hours=hours)


# ---------------------------------------------------------------------------
# Основной расчёт
# ---------------------------------------------------------------------------


def _gender(g: str | None) -> str | None:
    if g is None:
        return None
    g = g.strip().lower()
    if g in ("male", "m", "м", "муж", "мужской", "man"):
        return "male"
    if g in ("female", "f", "ж", "жен", "женский", "woman"):
        return "female"
    return None


def _chart_time(utc: datetime, local: datetime, lon: float | None, mode: str) -> datetime:
    if mode == "clock" or lon is None:
        return local
    if mode == "mean":
        return local_mean_time(utc, lon)
    return true_solar_time(utc, lon)


def _day_and_hour(chart_t: datetime | None, civil: date, zi_hour: str) -> tuple[int, int | None, bool]:
    """Вернуть (индекс дня, индекс часа или None, флаг «23-й час»)."""
    if chart_t is None:
        return day_index(civil), None, False
    d = chart_t.date()
    is23 = chart_t.hour == 23
    di = day_index(d + timedelta(days=1)) if (is23 and zi_hour == "early") else day_index(d)
    minutes = chart_t.hour * 60 + chart_t.minute + chart_t.second / 60.0
    hb = hour_branch(minutes)
    # ствол часа: после 23:00 — по стволу СЛЕДУЮЩЕГО дня (в обеих школах)
    stem_day = day_index(d + timedelta(days=1)) % 10 if is23 else di % 10
    hs = (zi_first_stem(stem_day) + hb) % 10
    return di, ganzhi_index(hs, hb), is23


def _pillar(key: str, idx: int, dm: int) -> dict:
    s, b = idx % 10, idx % 12
    hidden = []
    for hs, role, w in HIDDEN_STEMS[b]:
        hidden.append({**{k: v for k, v in stem_info(hs).items() if k in ("cn", "ru", "element", "polarity", "name_ru")},
                       "role": role, "role_ru": HIDDEN_ROLE_RU[role], "weight": w,
                       "ten_god": ten_god(dm, hs)})
    out = {
        "pillar": key,
        "index": idx,
        "ganzhi": ganzhi(idx),
        "stem": stem_info(s),
        "branch": branch_info(b),
        "hidden_stems": hidden,
        "stem_ten_god": None if key == "day" else ten_god(dm, s),
        "life_stage_dm": life_stage(dm, b),       # стадия Дневного Мастера в ветви столпа (星运)
        "life_stage_self": life_stage(s, b),      # стадия ствола столпа в своей ветви (自坐)
        "nayin": nayin(idx),
    }
    return out


def _interactions(pillars: dict[str, int]) -> dict:
    keys = [k for k in PILLAR_KEYS if pillars.get(k) is not None]
    st = {k: pillars[k] % 10 for k in keys}
    br = {k: pillars[k] % 12 for k in keys}
    res: dict[str, list] = {"stem_combinations": [], "stem_clashes": [], "branch_six_combinations": [],
                            "branch_clashes": [], "branch_harms": [], "branch_destructions": [],
                            "branch_punishments": [], "three_harmonies": [], "half_harmonies": [],
                            "directional_combinations": []}
    for i, a in enumerate(keys):
        for c in keys[i + 1:]:
            ps = frozenset({st[a], st[c]})
            if ps in STEM_COMBOS:
                res["stem_combinations"].append({"pillars": [a, c], "stems": STEMS[st[a]][0] + STEMS[st[c]][0],
                                                 "element": STEM_COMBOS[ps]})
            if ps in STEM_CLASHES:
                res["stem_clashes"].append({"pillars": [a, c], "stems": STEMS[st[a]][0] + STEMS[st[c]][0]})
            pb = frozenset({br[a], br[c]})
            bb = BRANCHES[br[a]][0] + BRANCHES[br[c]][0]
            if pb in SIX_COMBOS:
                res["branch_six_combinations"].append({"pillars": [a, c], "branches": bb, "element": SIX_COMBOS[pb]})
            if (br[a] - br[c]) % 12 == 6:
                res["branch_clashes"].append({"pillars": [a, c], "branches": bb})
            if pb in HARMS:
                res["branch_harms"].append({"pillars": [a, c], "branches": bb})
            if pb in DESTRUCTIONS:
                res["branch_destructions"].append({"pillars": [a, c], "branches": bb})
            if pb == PUNISHMENT_PAIR[0]:
                res["branch_punishments"].append({"pillars": [a, c], "branches": bb, "type": PUNISHMENT_PAIR[1]})
            if br[a] == br[c] and br[a] in SELF_PUNISH:
                res["branch_punishments"].append({"pillars": [a, c], "branches": bb, "type": "自刑 — самонаказание"})
            for grp, name in PUNISHMENT_GROUPS:
                if br[a] in grp and br[c] in grp and br[a] != br[c]:
                    res["branch_punishments"].append({"pillars": [a, c], "branches": bb, "type": name})
            for (x, mid, z), el in THREE_HARMONIES:
                if pb in (frozenset({x, mid}), frozenset({mid, z})):
                    res["half_harmonies"].append({"pillars": [a, c], "branches": bb, "element": el})
    present = set(br.values())
    for trio, el in THREE_HARMONIES:
        if set(trio) <= present:
            res["three_harmonies"].append({"branches": "".join(BRANCHES[x][0] for x in trio), "element": el})
    for trio, el in DIRECTIONAL:
        if set(trio) <= present:
            res["directional_combinations"].append({"branches": "".join(BRANCHES[x][0] for x in trio), "element": el})
    return res


def _symbolic_stars(pillars: dict[str, int], nobleman_variant: str = "main") -> list[dict]:
    keys = [k for k in PILLAR_KEYS if pillars.get(k) is not None]
    br = {k: pillars[k] % 12 for k in keys}
    out: list[dict] = []

    def where(targets) -> list[str]:
        return [k for k in keys if br[k] in targets]

    ds, ys = pillars["day"] % 10, pillars["year"] % 10
    nob = NOBLEMAN_ALT if nobleman_variant == "alt" else NOBLEMAN
    out.append({"star": "天乙贵人", "ru": "Благородный человек (по стволу дня)",
                "branches": "".join(BRANCHES[x][0] for x in nob[ds]), "found_in": where(nob[ds])})
    out.append({"star": "天乙贵人", "ru": "Благородный человек (по стволу года)",
                "branches": "".join(BRANCHES[x][0] for x in nob[ys]), "found_in": where(nob[ys])})
    out.append({"star": "文昌", "ru": "Академическая звезда (Вэньчан, по стволу дня)",
                "branches": BRANCHES[ACADEMIC[ds]][0], "found_in": where({ACADEMIC[ds]})})
    for base in ("year", "day"):
        t = TRINE_OF[br[base]]
        for name, ru, table in (("桃花", "Цветок персика", PEACH), ("驿马", "Почтовая (Странствующая) лошадь", HORSE),
                                ("华盖", "Балдахин (Хуагай)", CANOPY)):
            out.append({"star": name, "ru": f"{ru} (по ветви {PILLAR_RU_GEN[base]})",
                        "branches": BRANCHES[table[t]][0],
                        "found_in": [k for k in where({table[t]}) if k != base]})
    for base in ("day", "year"):
        idx = pillars[base]
        xun = idx - idx % 10
        void = ((xun % 12) + 10) % 12, ((xun % 12) + 11) % 12
        out.append({"star": "空亡", "ru": f"Пустота (Кун-ван) по столпу {PILLAR_RU_GEN[base]}",
                    "branches": "".join(BRANCHES[x][0] for x in void),
                    "found_in": [k for k in where(set(void)) if k != base]})
    return out


def _elements(pillars: dict[str, int]) -> dict:
    keys = [k for k in PILLAR_KEYS if pillars.get(k) is not None]
    visible = {e: 0 for e in ELEMENTS}
    weighted = {e: 0.0 for e in ELEMENTS}
    yy = {"yang": 0, "yin": 0}
    for k in keys:
        s, b = pillars[k] % 10, pillars[k] % 12
        visible[stem_element(s)] += 1
        visible[branch_element(b)] += 1
        yy[stem_polarity(s)] += 1
        yy[branch_polarity(b)] += 1
        weighted[stem_element(s)] += 1.0
        for hs, _r, w in HIDDEN_STEMS[b]:
            weighted[stem_element(hs)] += w
    return {
        "visible": visible,
        "weighted_with_hidden": {e: round(v, 2) for e, v in weighted.items()},
        "missing": [e for e in ELEMENTS if weighted[e] == 0],
        "yin_yang": yy,
        "note": "visible: 4 ствола + 4 ветви по собственному элементу; weighted: ствол=1, "
                "ветвь=1, распределённая по скрытым стволам (0.6/0.3/0.1; 0.7/0.3). ⚠ веса — соглашение.",
    }


def _strength(pillars: dict[str, int]) -> dict:
    """Эвристика силы Дневного Мастера (⚠ ориентир, не заменяет анализ структуры карты)."""
    dm = pillars["day"] % 10
    dm_el = stem_element(dm)
    mb = pillars["month"] % 12
    support = 0.0
    total = 0.0
    for k in PILLAR_KEYS:
        if pillars.get(k) is None:
            continue
        s, b = pillars[k] % 10, pillars[k] % 12
        items = [] if k == "day" else [(s, 1.0)]
        mult = 2.0 if k == "month" else 1.0   # ветвь месяца (月令) — двойной вес
        items += [(hs, w * mult) for hs, _r, w in HIDDEN_STEMS[b]]
        for st, w in items:
            d = (ELEMENTS.index(stem_element(st)) - ELEMENTS.index(dm_el)) % 5
            total += w
            if d in (0, 4):
                support += w
    share = support / total if total else 0.0
    ss = season_state(dm_el, mb)
    bonus = {"旺": 0.1, "相": 0.05, "休": 0.0, "囚": -0.05, "死": -0.1}[ss["cn"]]
    score = share + bonus
    if score >= 0.5:
        label = "скорее сильный"
    elif score <= 0.35:
        label = "скорее слабый"
    else:
        label = "пограничный (уточнять по структуре)"
    return {"season_state": ss, "support_share": round(share, 3), "season_bonus": bonus,
            "score": round(score, 3), "label": label,
            "method": "score = доля «своих» (тот же элемент + порождающий) среди знаков без ствола дня "
                      "(скрытые стволы по весам, ветвь месяца ×2) + сезонная поправка "
                      "(旺 +0.1, 相 +0.05, 休 0, 囚 −0.05, 死 −0.1); ≥0.5 сильный, ≤0.35 слабый. "
                      "⚠ Эвристика калькулятора: особые структуры (从格, 化格) так не распознаются."}


def calculate(b: BirthInput, **options) -> dict:
    """Рассчитать карту Ба-цзы.

    options:
      zi_hour: 'late' (по умолч.) | 'early' — см. докстринг модуля;
      solar_time: 'true' (по умолч.) | 'mean' | 'clock';
      luck_count: число Столпов удачи (10);
      nobleman_variant: 'main' | 'alt' (庚 → 寅午);
      annual_from, annual_to: диапазон лет для流年 (необязательно).
    """
    zi_hour = str(options.get("zi_hour", "late")).strip().lower()
    solar_time = options.get("solar_time", "true")
    # CLI (`--opt solar_time=true`) превращает строку 'true' в булево True — принимаем и его.
    if solar_time is True:
        solar_time = "true"
    elif solar_time is False:
        solar_time = "clock"
    solar_time = str(solar_time).strip().lower()
    luck_count = int(options.get("luck_count", 10))
    if zi_hour not in ("late", "early"):
        raise ValueError("zi_hour: 'late' | 'early'")
    if solar_time not in ("true", "mean", "clock"):
        raise ValueError("solar_time: 'true' | 'mean' | 'clock'")
    warnings: list[str] = []
    steps: list[str] = []

    def add(msg: str) -> None:
        steps.append(f"Шаг {len(steps) + 1}. {msg}")

    # --- 1. время -> UT ---
    has_time = b.has_time
    if b.tz is None and b.lat is not None and b.lon is not None:
        from calculators.common.places import tz_for_coords
        tzname = tz_for_coords(b.lat, b.lon)
        if tzname:
            b = replace(b, tz=tzname)
            warnings.append(f"Часовой пояс определён по координатам: {tzname}.")
    if b.tz is None:
        if has_time:
            raise ValueError("Не задан часовой пояс (tz) или место — без них нельзя найти момент в UT.")
        b = replace(b, tz="UTC")
        warnings.append("Нет ни времени, ни пояса: год/месяц определены на конец даты по UTC.")
    # Без времени год и месяц определяются на КОНЕЦ местной даты (23:59): день цзе (в т.ч. Личуня)
    # считается уже новым периодом — то же соглашение, что в модулях 03 (ninestar) и 12 (Гуа).
    nb = b if has_time else replace(b, hour=23, minute=59)
    n = normalize(nb)
    warnings.extend(n.warnings)
    jd = n.jd_ut
    if not has_time:
        warnings.append("Время рождения неизвестно: столп часа не строится; год и месяц определены "
                        "на конец местной даты (день цзе/Личуня считается новым периодом, как в модулях 03 и 12).")
    add(f"Местное время {n.local:%d.%m.%Y %H:%M} ({b.tz}, {fmt_offset(n.utc_offset_hours)}, "
                 f"источник смещения: {n.offset_source}) → UTC {n.utc:%d.%m.%Y %H:%M:%S}; JD(UT) = {jd:.5f}.")

    # --- 2. год по Личуню ---
    to_local = _local_converter(b.tz, n.offset_source, n.utc_offset_hours)
    y_utc = n.utc.year
    lc = li_chun_jd(y_utc)
    bazi_year = y_utc if jd >= lc else y_utc - 1
    lc_used = lc if jd >= lc else li_chun_jd(y_utc - 1)
    yi = year_index(bazi_year)
    add(f"Личунь (Солнце 315°) {y_utc} г. = {_jd_iso(lc)} UT "
                 f"({to_local(lc)} по местному). Рождение {'ПОСЛЕ' if jd >= lc else 'ДО'} "
                 f"Личуня → год Ба-цзы {bazi_year}. Индекс года = ({bazi_year} − 4) mod 60 = {yi} → {ganzhi(yi)}.")

    # --- 3. месяц по цзе ---
    lam = sun_longitude(jd)
    slot = month_slot(lam)
    prev_deg = JIE[slot][0]
    next_deg = JIE[(slot + 1) % 12][0]
    prev_jd = find_sun_longitude(prev_deg, jd, search_back=True)
    next_jd = find_sun_longitude(next_deg, jd, search_back=False)
    ys = yi % 10
    m_stem = (month_first_stem(ys) + slot) % 10
    m_branch = (slot + 2) % 12
    mi = ganzhi_index(m_stem, m_branch)
    add(f"Долгота Солнца λ = {lam:.4f}°. Номер месяца = ⌊((λ − 315) mod 360) / 30⌋ = {slot} "
                 f"→ ветвь {BRANCHES[m_branch][0]}. Последнее цзе: {JIE[slot][1]} ({prev_deg}°) "
                 f"{_jd_iso(prev_jd)} UT; следующее: {JIE[(slot + 1) % 12][1]} ({next_deg}°) {_jd_iso(next_jd)} UT.")
    add(f"Пять тигров (五虎遁): ствол года {STEMS[ys][0]} → месяц 寅 начинается со ствола "
                 f"{STEMS[month_first_stem(ys)][0]}; +{slot} → {STEMS[m_stem][0]}. Столп месяца {ganzhi(mi)}.")
    for jd_j, nm in ((prev_jd, JIE[slot][1]), (next_jd, JIE[(slot + 1) % 12][1])):
        if has_time and abs(jd - jd_j) < 1.0:
            warnings.append(f"Рождение в пределах {abs(jd - jd_j) * 24:.1f} ч от цзе {nm}: при ошибке во времени "
                            f"рождения столп месяца{' и года' if nm == '立春' else ''} может смениться.")
        # без времени: предупреждаем, только если цзе попадает на МЕСТНУЮ дату рождения
        if not has_time and to_local(jd_j)[:10] == b.date.isoformat():
            warnings.append(f"Цзе {nm} приходится на дату рождения ({to_local(jd_j)} по местному), время "
                            f"неизвестно — столп месяца{' и года' if nm == '立春' else ''} неоднозначен.")

    # --- 4–5. день и час ---
    chart_t = None
    used_mode = solar_time
    if has_time:
        if solar_time != "clock" and b.lon is None:
            warnings.append("Долгота неизвестна — солнечное время не вычислить, использовано время часов.")
            used_mode = "clock"
        chart_t = _chart_time(n.utc, n.local, b.lon, used_mode)
        mode_ru = {"clock": "время часов", "mean": "местное среднее солнечное (LMT)",
                   "true": "истинное солнечное (LMT + уравнение времени)"}[used_mode]
        add(f"Время карты ({mode_ru}): {chart_t:%d.%m.%Y %H:%M:%S}.")
    di, hi, is23 = _day_and_hour(chart_t, b.date, zi_hour)
    civil_for_day = (chart_t.date() if chart_t else b.date)
    dj = jdn(civil_for_day)
    if is23:
        add(f"Время карты в 23-м часу: школа zi_hour='{zi_hour}' → "
                     + ("столп дня берётся по СЛЕДУЮЩЕЙ дате (день меняется в 23:00)." if zi_hour == "early"
                        else "столп дня остаётся по текущей дате (поздний час Крысы, 晚子时)."))
    add(f"Столп дня: JDN({civil_for_day:%d.%m.%Y}) = {dj}; (JDN + 49) mod 60 = {(dj + 49) % 60}"
                 + (f"; +1 (смена дня в 23:00) → {di}" if (is23 and zi_hour == 'early') else "")
                 + f" → {ganzhi(di)}. Дневной Мастер {STEMS[di % 10][0]} ({stem_info(di % 10)['name_ru']}).")
    if hi is not None:
        hb = hi % 12
        sd = (di + (1 if (is23 and zi_hour == "late") else 0)) % 10
        add(f"Ветвь часа: {chart_t:%H:%M} → {BRANCHES[hb][0]} ({BRANCHES[hb][5]}). Пять крыс (五鼠遁): "
                     f"ствол дня {STEMS[sd][0]}{' (следующего дня)' if is23 and zi_hour == 'late' else ''} → час 子 "
                     f"начинается со ствола {STEMS[zi_first_stem(sd)][0]}; +{hb} → {STEMS[hi % 10][0]}. "
                     f"Столп часа {ganzhi(hi)}.")
        mins = chart_t.hour * 60 + chart_t.minute + chart_t.second / 60.0
        to_b = ((mins + 60) % 120)
        near = min(to_b, 120 - to_b)
        if near < 15:
            warnings.append(f"Время карты в {near:.0f} мин от границы двухчасовки: столп часа чувствителен "
                            f"к точности времени и к выбору solar_time (см. alternatives).")

    pillars_idx = {"year": yi, "month": mi, "day": di, "hour": hi}
    dm = di % 10
    pillars = {k: (_pillar(k, v, dm) if v is not None else None) for k, v in pillars_idx.items()}

    # альтернативы (для пограничных случаев)
    alternatives = []
    if has_time:
        seen = set()
        for mode in ("clock", "mean", "true"):
            if mode != "clock" and b.lon is None:
                continue
            ct = _chart_time(n.utc, n.local, b.lon, mode)
            for zh in ("late", "early"):
                d2, h2, _ = _day_and_hour(ct, b.date, zh)
                key = (d2, h2)
                alternatives.append({"solar_time": mode, "zi_hour": zh, "chart_time": _iso(ct),
                                     "day": ganzhi(d2), "hour": ganzhi(h2)})
                seen.add(key)
        if len(seen) > 1:
            warnings.append("Столп дня/часа зависит от школы (solar_time / zi_hour) — см. alternatives.")

    # --- 6. Столпы удачи ---
    gender = _gender(b.gender)
    luck = None
    if gender is None:
        warnings.append("Пол не указан — Столпы удачи (大运) не рассчитаны.")
    else:
        yang_year = ys % 2 == 0
        forward = (yang_year and gender == "male") or ((not yang_year) and gender == "female")
        delta = (next_jd - jd) if forward else (jd - prev_jd)
        total_minutes = delta * 1440.0
        sy = int(total_minutes // 4320)
        rem = total_minutes - sy * 4320
        sm = int(rem // 360)
        rem -= sm * 360
        sd_ = int(rem // 12)
        rem -= sd_ * 12
        sh = rem * 2
        local_birth = n.local if has_time else datetime(b.year, b.month, b.day, 12)
        start_dt = _add_ymd(local_birth, sy, sm, sd_, sh)
        start_decimal = delta / 3.0
        items = []
        for k in range(1, luck_count + 1):
            idx = (mi + k) % 60 if forward else (mi - k) % 60
            sy_k = start_dt.year + 10 * (k - 1)
            items.append({
                "n": k, **pillar_brief(idx),
                "stem_ten_god": ten_god(dm, idx % 10)["ru"],
                "branch_main_ten_god": ten_god(dm, HIDDEN_STEMS[idx % 12][0][0])["ru"],
                "life_stage_dm": life_stage(dm, idx % 12)["cn"],
                "nayin": nayin(idx)["cn"],
                "start_age": round(start_decimal + 10 * (k - 1), 2),
                "start_date": _iso(_add_ymd(start_dt, 10 * (k - 1), 0, 0)),
                "start_year": sy_k,
                "start_age_nominal_xusui": sy_k - b.year + 1,
                "annual_pillars": [annual_pillar(y) for y in range(sy_k, sy_k + 10)],
            })
        jie_used = JIE[(slot + 1) % 12] if forward else JIE[slot]
        luck = {
            "direction": "forward" if forward else "backward",
            "direction_ru": "прямой (по порядку цикла)" if forward else "обратный (против цикла)",
            "rule": f"год {POLARITY_RU[stem_polarity(ys)]} ({STEMS[ys][0]}) + {'мужчина' if gender == 'male' else 'женщина'}",
            "jie_used": {"cn": jie_used[1], "ru": jie_used[2], "deg": jie_used[0],
                         "utc": _jd_iso(next_jd if forward else prev_jd)},
            "interval_days": round(delta, 5),
            "start": {"years": sy, "months": sm, "days": sd_, "hours": round(sh, 1),
                      "decimal_years": round(start_decimal, 3), "rounded_years": round(start_decimal)},
            "start_date": _iso(start_dt),
            "pillars": items,
        }
        add(f"Столпы удачи: {luck['rule']} → {luck['direction_ru']}. Интервал до "
                     f"{'следующего' if forward else 'предыдущего'} цзе {jie_used[1]} = {delta:.4f} сут; "
                     f"÷3 = {start_decimal:.3f} года = {sy} г {sm} мес {sd_} дн {int(sh)} ч "
                     f"(1 сут = 4 мес, 2 ч = 10 дн). Начало ≈ {start_dt:%d.%m.%Y}. "
                     f"Первый столп = столп месяца {'+' if forward else '−'}1 → {items[0]['ganzhi'] if items else '—'}.")

    annual = None
    if options.get("annual_from") is not None:
        a0 = int(options["annual_from"])
        a1 = int(options.get("annual_to", a0 + 9))
        annual = [annual_pillar(y) for y in range(a0, a1 + 1)]

    tai_yuan = ganzhi_index((m_stem + 1) % 10, (m_branch + 3) % 12)

    chart = " ".join(ganzhi(pillars_idx[k]) if pillars_idx[k] is not None else "??" for k in PILLAR_KEYS)
    steps.append(f"Итог (год месяц день час): {chart}.")

    return {
        "method": "bazi",
        "variant": f"Цзы Пин (子平): год по Личуню, месяц по цзе, zi_hour='{zi_hour}', solar_time='{used_mode}'",
        "inputs_used": {
            "local": _iso(n.local) if has_time else b.date.isoformat(),
            "tz": b.tz, "utc_offset": fmt_offset(n.utc_offset_hours), "offset_source": n.offset_source,
            "utc": _iso(n.utc).replace("+00:00", "Z"), "jd_ut": round(jd, 6),
            "lat": b.lat, "lon": b.lon, "gender": gender, "has_time": has_time,
            "chart_time": _iso(chart_t) if chart_t else None,
            "options": {"zi_hour": zi_hour, "solar_time": used_mode, "luck_count": luck_count},
        },
        "warnings": warnings,
        "chart": chart,
        "pillars": pillars,
        "day_master": {**stem_info(dm), "season_state": season_state(stem_element(dm), m_branch)},
        "solar_terms": {
            "li_chun_utc": _jd_iso(lc_used), "bazi_year": bazi_year,
            "sun_longitude": round(lam, 5),
            "prev_jie": {"cn": JIE[slot][1], "ru": JIE[slot][2], "deg": prev_deg, "utc": _jd_iso(prev_jd),
                         "jd_ut": round(prev_jd, 6)},
            "next_jie": {"cn": JIE[(slot + 1) % 12][1], "ru": JIE[(slot + 1) % 12][2], "deg": next_deg,
                         "utc": _jd_iso(next_jd), "jd_ut": round(next_jd, 6)},
        },
        "elements": _elements(pillars_idx),
        "strength_hint": _strength(pillars_idx),
        "interactions": _interactions(pillars_idx),
        "symbolic_stars": _symbolic_stars(pillars_idx, options.get("nobleman_variant", "main")),
        "tai_yuan": {"ganzhi": ganzhi(tai_yuan), "note": "胎元 «Столп зачатия»: ствол месяца +1, ветвь месяца +3"},
        "luck_pillars": luck,
        "annual_pillars": annual,
        "alternatives": alternatives,
        "steps": steps,
    }


if __name__ == "__main__":  # pragma: no cover
    import json

    r = calculate(BirthInput(1984, 2, 4, 23, 30, place="Москва", gender="male"))
    print(json.dumps(r, ensure_ascii=False, indent=1)[:4000])
