"""Модуль 12: арканы Таро по дате рождения, сетка Ло Шу и ведическая (индийская) нумерология.

Что считает:
* **Карты рождения Таро** (Tarot Birth Cards):
  - по Мэри К. Грир (Greer, «Tarot for Your Self», 1984/2002, с. 29–41; таблица
    «Patterns of Personal Destiny», с. 32) — карта Личности (Personality), карта Души (Soul),
    Скрытый фактор / Учитель (Hidden Factor / Teacher), созвездие (constellation);
  - по Tarot School (Р. Э. и У. Амберстоун): ММ + ДД + первые 2 цифры года + последние 2;
  - вариант Анджелес Арриен (Arrien, «The Tarot Handbook», 1987): та же арифметика,
    колода Тота (8 = Adjustment, 11 = Lust), термины Personality/Soul/Growth Symbol.
* **Карта года** (Year Card / Growth Symbol): ММ + ДД + год (Грир) или ММ + ДД + сумма цифр года
  (Tarot School); календарный год или «от дня рождения до дня рождения».
* **Русскоязычные «арканы по дате рождения»**: аркан дня, аркан суммы цифр даты (−22 или
  повторное сложение цифр), аркан «день + месяц + год» с приведением по сумме цифр.
* **Сетка Ло Шу** (Lo Shu, магический квадрат 4-9-2 / 3-5-7 / 8-1-6): цифры даты без нулей,
  по выбору + число Драйвера, Кондуктора, Куа; 8 линий (планы), стрелы силы/слабости,
  отсутствующие числа (стихия, сторона света, цвет — интерпретативно).
* **Ведическая нумерология** (Anka Shastra в современной индийской подаче): Мулянк (Moolank,
  психическое число, Driver), Бхагьянк (Bhagyank, число судьбы, Conductor), Намянк (имя
  по халдейской таблице Хейро), планеты-управители, дружба/вражда чисел через натуральную
  дружбу планет (BPHS 3.55).

Подробности, источники и обоснование умолчаний: knowledge-base/12-tarot-loshu-vedic.md.
"""
from __future__ import annotations

from datetime import date, datetime, timezone

from .common import ephemeris as eph
from .common.time import BirthInput, julian_day_ut, normalize

# ---------------------------------------------------------------------------
# Справочные таблицы: Старшие арканы
# ---------------------------------------------------------------------------

ROMAN = ["0", "I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X", "XI", "XII",
         "XIII", "XIV", "XV", "XVI", "XVII", "XVIII", "XIX", "XX", "XXI", "XXII"]

# Нумерация Райдера–Уэйта–Смит (RWS, Golden Dawn): 8 = Сила, 11 = Справедливость.
# (английское имя, русское имя, ключевые слова)
ARCANA_RWS: dict[int, tuple[str, str, str]] = {
    0: ("The Fool", "Шут (Дурак)", "начало пути, спонтанность, доверие жизни, свобода, риск"),
    1: ("The Magician", "Маг", "воля, мастерство, инициатива, умение воплощать задуманное"),
    2: ("The High Priestess", "Верховная Жрица", "интуиция, тайное знание, внутренний голос, пассивная мудрость"),
    3: ("The Empress", "Императрица", "плодородие, творчество, изобилие, забота, чувственность"),
    4: ("The Emperor", "Император", "структура, власть, порядок, ответственность, отцовское начало"),
    5: ("The Hierophant", "Иерофант (Верховный Жрец)", "традиция, учение, наставничество, ценности, институты"),
    6: ("The Lovers", "Влюблённые", "любовь, выбор, союз, согласование ценностей"),
    7: ("The Chariot", "Колесница", "движение к цели, победа, самоконтроль, амбиции"),
    8: ("Strength", "Сила", "мужество, мягкая сила, самообладание, укрощение страстей"),
    9: ("The Hermit", "Отшельник", "поиск истины, уединение, мудрость, внутренний свет"),
    10: ("Wheel of Fortune", "Колесо Фортуны", "циклы, судьба, перемены, удача, поворотный момент"),
    11: ("Justice", "Справедливость", "равновесие, честность, закон причины и следствия, решения"),
    12: ("The Hanged Man", "Повешенный", "пауза, жертва, иной взгляд, отпускание контроля"),
    13: ("Death", "Смерть", "завершение и трансформация, обновление, отпускание старого"),
    14: ("Temperance", "Умеренность", "гармония, смешение противоположностей, терпение, исцеление"),
    15: ("The Devil", "Дьявол", "привязанности, искушения, материальная власть, тень, страсть"),
    16: ("The Tower", "Башня", "внезапный слом, освобождение от ложного, озарение"),
    17: ("The Star", "Звезда", "надежда, вдохновение, исцеление, вера в будущее"),
    18: ("The Moon", "Луна", "иллюзии, подсознание, страхи, воображение, сны"),
    19: ("The Sun", "Солнце", "радость, успех, ясность, жизненная сила, самовыражение"),
    20: ("Judgement", "Суд (Страшный суд)", "пробуждение, призвание, переоценка, возрождение"),
    21: ("The World", "Мир", "завершённость, целостность, интеграция, достижение"),
}

# Марсельская колода: 8 = Справедливость (La Justice), 11 = Сила (La Force).
ARCANA_MARSEILLE_EN = {
    0: "Le Mat", 1: "Le Bateleur", 2: "La Papesse", 3: "L'Impératrice", 4: "L'Empereur",
    5: "Le Pape", 6: "L'Amoureux", 7: "Le Chariot", 8: "La Justice", 9: "L'Hermite",
    10: "La Roue de Fortune", 11: "La Force", 12: "Le Pendu", 13: "(L'Arcane sans nom)",
    14: "Tempérance", 15: "Le Diable", 16: "La Maison Dieu", 17: "L'Étoile", 18: "La Lune",
    19: "Le Soleil", 20: "Le Jugement", 21: "Le Monde",
}
# Колода Тота (Crowley–Harris), используемая Арриен: 8 = Adjustment, 11 = Lust.
ARCANA_THOTH: dict[int, tuple[str, str]] = {
    0: ("The Fool", "Дурак"), 1: ("The Magus", "Маг"), 2: ("The Priestess", "Жрица"),
    3: ("The Empress", "Императрица"), 4: ("The Emperor", "Император"),
    5: ("The Hierophant", "Иерофант"), 6: ("The Lovers", "Влюблённые"),
    7: ("The Chariot", "Колесница"), 8: ("Adjustment", "Регулирование (≈ Справедливость)"),
    9: ("The Hermit", "Отшельник"), 10: ("Fortune", "Фортуна"),
    11: ("Lust", "Вожделение (≈ Сила)"), 12: ("The Hanged Man", "Повешенный"),
    13: ("Death", "Смерть"), 14: ("Art", "Искусство (≈ Умеренность)"),
    15: ("The Devil", "Дьявол"), 16: ("The Tower", "Башня"), 17: ("The Star", "Звезда"),
    18: ("The Moon", "Луна"), 19: ("The Sun", "Солнце"), 20: ("The Aeon", "Эон (≈ Суд)"),
    21: ("The Universe", "Вселенная (≈ Мир)"),
}

# Созвездия Грир (Tarot for Your Self, с. 32): номер души -> (название, принцип)
GREER_CONSTELLATIONS: dict[int, tuple[str, str, str]] = {
    1: ("Magician", "Маг (Солнце, Колесо Фортуны, Маг)", "Воля и сфокусированное сознание (Will and Focused Consciousness)"),
    2: ("High Priestess", "Верховная Жрица (Суд, Справедливость, Верховная Жрица)",
        "Взвешенное суждение через интуитивное осознание (Balanced Judgment through Intuitive Awareness)"),
    3: ("Empress", "Императрица (Мир, Повешенный, Императрица)", "Любовь и творческое воображение (Love and Creative Imagination)"),
    4: ("Emperor", "Император (Шут, Смерть, Император)", "Жизненная сила и реализация власти (Life Force and Realization of Power)"),
    5: ("Hierophant", "Иерофант (Умеренность, Иерофант)", "Обучение и учение (Teaching and Learning)"),
    6: ("Lovers", "Влюблённые (Дьявол, Влюблённые)", "Отношения и выбор (Relatedness and Choice)"),
    7: ("Chariot", "Колесница (Башня, Колесница)", "Мастерство через перемены (Mastery through Change)"),
    8: ("Strength", "Сила (Звезда, Сила)", "Мужество и самоуважение (Courage and Self-Esteem)"),
    9: ("Hermit", "Отшельник (Луна, Отшельник)", "Самоанализ и личная целостность (Introspection and Personal Integrity)"),
}

# ---------------------------------------------------------------------------
# Справочные таблицы: Ло Шу
# ---------------------------------------------------------------------------

LOSHU_LAYOUT = [[4, 9, 2], [3, 5, 7], [8, 1, 6]]   # юг сверху (Wikipedia: Lo Shu Square)

# (ключ, клетки, тип линии, название плана RU, EN, альтернативные названия в источниках)
LOSHU_LINES: list[tuple[str, tuple[int, int, int], str, str, str, list[str]]] = [
    ("mental", (4, 9, 2), "row", "Ментальный план (план ума)", "Mental / Mind plane",
     ["Thought plane (sheelaa.com)"]),
    ("emotional", (3, 5, 7), "row", "Эмоциональный (духовный) план", "Emotional / Spiritual plane",
     ["Will plane (sheelaa.com)"]),
    ("practical", (8, 1, 6), "row", "Практический (физический) план", "Practical / Physical plane",
     ["Action plane (sheelaa.com)"]),
    ("thought", (4, 3, 8), "column", "План мысли", "Thought plane", ["Mind plane (sheelaa.com)"]),
    ("will", (9, 5, 1), "column", "План воли (решимости и воли)", "Will / Determination and Will plane",
     ["Practical plane (sheelaa.com)"]),
    ("action", (2, 7, 6), "column", "План действия", "Action plane", ["Spiritual plane (sheelaa.com)"]),
    ("golden_yog", (4, 5, 6), "diagonal", "Золотая (Раджа-) йога", "Golden Yog / Raj Yog",
     ["Spiritual plane (ganak.app)", "Determination line (astrosight.ai ⚠ не найдено при повторной проверке)", "Stability arrow (astromedha.in)"]),
    ("silver_yog", (2, 5, 8), "diagonal", "Серебряная йога", "Silver Yog / Rajat Yog",
     ["Material plane (ganak.app)", "Compassion line (astrosight.ai ⚠ не найдено при повторной проверке)", "Prosperity arrow (astromedha.in; sheelaa.com)"]),
]

# Стрелы силы (все три числа присутствуют) — названия разнятся по источникам, см. базу знаний.
LOSHU_STRENGTH_ARROWS: dict[tuple[int, int, int], str] = {
    (4, 9, 2): "Стрела планировщика (Arrow of the Planner; у sheelaa.com — Intellect)",
    (3, 5, 7): "Стрела духовности (Arrow of Spirituality; варианты: Intellect, Willpower)",
    (8, 1, 6): "Стрела активности (Arrow of Activity) ⚠ один источник",
    (4, 3, 8): "Полный план мысли (отдельное имя стрелы не найдено ⚠)",
    (9, 5, 1): "Стрела решимости (Arrow of Determination; вариант: Willpower)",
    (2, 7, 6): "Стрела действия (Arrow of Action; у sheelaa.com — Compassion)",
    (4, 5, 6): "Золотая (Раджа-) йога / Стрела стабильности (Golden Yog / Arrow of Stability)",
    (2, 5, 8): "Серебряная йога / Стрела процветания (Silver Yog / Arrow of Prosperity)",
}
# Стрелы слабости (все три числа отсутствуют) — по astromedha.in.
LOSHU_WEAKNESS_ARROWS: dict[tuple[int, int, int], str] = {
    (4, 5, 6): "Стрела фрустрации (Arrow of Frustration)",
    (3, 5, 7): "Стрела плохой памяти (Arrow of Poor Memory)",
    (2, 7, 6): "Стрела одиночества (Arrow of Loneliness)",
    (8, 1, 6): "Стрела потерь (Arrow of Losses)",
    (4, 3, 8): "Стрела нерешительности (Arrow of Indecision)",
    (9, 5, 1): "Стрела пассивности (Arrow of Passivity)",
    (4, 9, 2): "Пустой ментальный план (имя стрелы слабости не найдено ⚠)",
    (2, 5, 8): "Пустая серебряная линия (имя стрелы слабости не найдено ⚠)",
}

# Число -> (стихия, сторона света, триграмма «Позднего неба», цвет стихии, планета инд. традиции)
LOSHU_NUMBER_INFO: dict[int, tuple[str, str, str, str, str]] = {
    1: ("Вода", "Север", "Кань ☵", "чёрный, синий", "Солнце"),
    2: ("Земля", "Юго-запад", "Кунь ☷", "жёлтый, коричневый", "Луна"),
    3: ("Дерево", "Восток", "Чжэнь ☳", "зелёный", "Юпитер"),
    4: ("Дерево", "Юго-восток", "Сюнь ☴", "зелёный", "Раху"),
    5: ("Земля", "Центр", "—", "жёлтый", "Меркурий"),
    6: ("Металл", "Северо-запад", "Цянь ☰", "белый, золотой, серебряный", "Венера"),
    7: ("Металл", "Запад", "Дуй ☱", "белый, металлик", "Кету"),
    8: ("Земля", "Северо-восток", "Гэнь ☶", "жёлтый, бежевый", "Сатурн"),
    9: ("Огонь", "Юг", "Ли ☲", "красный", "Марс"),
}

# ---------------------------------------------------------------------------
# Справочные таблицы: ведическая нумерология
# ---------------------------------------------------------------------------

PLANETS = {1: "sun", 2: "moon", 3: "jupiter", 4: "rahu", 5: "mercury",
           6: "venus", 7: "ketu", 8: "saturn", 9: "mars"}
PLANET_RU = {"sun": "Солнце (Сурья)", "moon": "Луна (Чандра)", "jupiter": "Юпитер (Гуру)",
             "rahu": "Раху", "mercury": "Меркурий (Будха)", "venus": "Венера (Шукра)",
             "ketu": "Кету", "saturn": "Сатурн (Шани)", "mars": "Марс (Мангал)"}

# Натуральная дружба планет (BPHS 3.55) — та же таблица, что в calculators/jyotish.py.
# Раху и Кету в BPHS 3.55 не входят: в нумерологии считаем их нейтральными ко всем (⚠ конвенция).
NATURAL_FRIENDS: dict[str, tuple[list[str], list[str], list[str]]] = {
    "sun": (["moon", "mars", "jupiter"], ["mercury"], ["venus", "saturn"]),
    "moon": (["sun", "mercury"], ["mars", "jupiter", "venus", "saturn"], []),
    "mars": (["sun", "moon", "jupiter"], ["venus", "saturn"], ["mercury"]),
    "mercury": (["sun", "venus"], ["mars", "jupiter", "saturn"], ["moon"]),
    "jupiter": (["sun", "moon", "mars"], ["saturn"], ["mercury", "venus"]),
    "venus": (["mercury", "saturn"], ["mars", "jupiter"], ["sun", "moon"]),
    "saturn": (["mercury", "venus"], ["jupiter"], ["sun", "moon", "mars"]),
}

# Халдейская таблица (Хейро / Cheiro): 9 буквам не присваивается.
CHALDEAN: dict[str, int] = {}
for _v, _letters in {1: "AIJQY", 2: "BKR", 3: "CGLS", 4: "DMT", 5: "EHNX", 6: "UVW", 7: "OZ", 8: "FP"}.items():
    for _ch in _letters:
        CHALDEAN[_ch] = _v

# Транслитерация кириллицы для заграничного паспорта РФ (ICAO Doc 9303, с 2014 г.)
TRANSLIT_ICAO: dict[str, str] = {
    "А": "A", "Б": "B", "В": "V", "Г": "G", "Д": "D", "Е": "E", "Ё": "E", "Ж": "ZH", "З": "Z",
    "И": "I", "Й": "I", "К": "K", "Л": "L", "М": "M", "Н": "N", "О": "O", "П": "P", "Р": "R",
    "С": "S", "Т": "T", "У": "U", "Ф": "F", "Х": "KH", "Ц": "TS", "Ч": "CH", "Ш": "SH",
    "Щ": "SHCH", "Ъ": "IE", "Ы": "Y", "Ь": "", "Э": "E", "Ю": "IU", "Я": "IA",
}


# ---------------------------------------------------------------------------
# Базовые операции
# ---------------------------------------------------------------------------

def digit_sum(n: int) -> int:
    """Сумма цифр неотрицательного целого."""
    return sum(int(c) for c in str(abs(n)))


def reduce_to_digit(n: int) -> tuple[int, list[int]]:
    """Свести к 1..9 повторным сложением цифр; вернуть результат и цепочку."""
    chain = [n]
    while n > 9:
        n = digit_sum(n)
        chain.append(n)
    return n, chain


def reduce_to_22_digits(n: int) -> tuple[int, list[int]]:
    """Сложение цифр, пока число > 22 (правило Грир для карт рождения и года)."""
    chain = [n]
    while n > 22:
        n = digit_sum(n)
        chain.append(n)
    return n, chain


def reduce_to_22_subtract(n: int) -> tuple[int, list[int]]:
    """Вычитание 22, пока число > 22 (русскоязычное правило «аркана»)."""
    chain = [n]
    while n > 22:
        n -= 22
        chain.append(n)
    return n, chain


def date_digits(y: int, m: int, d: int) -> list[int]:
    """Все цифры даты в записи ДД.ММ.ГГГГ (с нулями)."""
    return [int(c) for c in f"{d:02d}{m:02d}{y:04d}"]


def card(n: int, deck: str = "rws") -> dict:
    """Описание старшего аркана по числу 0..22 (22 = Шут).

    deck: 'rws' (по умолчанию) | 'marseille' | 'thoth'.
    """
    if not 0 <= n <= 22:
        raise ValueError(f"Номер аркана вне диапазона 0..22: {n}")
    idx = 0 if n == 22 else n
    en, ru, kw = ARCANA_RWS[idx]
    out = {"number": n, "roman": ROMAN[n] if n != 22 else "XXII (0)",
           "name_en": en, "name_ru": ru, "keywords_ru": kw, "deck": deck}
    if deck == "marseille":
        out["name_en"] = ARCANA_MARSEILLE_EN[idx]
        if idx in (8, 11):
            sw = 11 if idx == 8 else 8
            out["name_ru"] = ARCANA_RWS[sw][1]
            out["keywords_ru"] = ARCANA_RWS[sw][2]
    elif deck == "thoth":
        out["name_en"], out["name_ru"] = ARCANA_THOTH[idx]
        if idx in (8, 11):
            out["keywords_ru"] = ARCANA_RWS[11 if idx == 8 else 8][2]
    elif deck != "rws":
        raise ValueError(f"Неизвестная колода: {deck}")
    if idx in (8, 11):
        other = {"rws": "марсельской/тотовской", "marseille": "RWS", "thoth": "RWS"}[deck]
        alt = ARCANA_RWS[11 if idx == 8 else 8][1] if deck == "rws" else ARCANA_RWS[idx][1]
        out["numbering_note"] = f"В {other} нумерации №{idx} — «{alt}»."
    return out


# ---------------------------------------------------------------------------
# A. Карты рождения Таро
# ---------------------------------------------------------------------------

def _pattern_cards(personality: int) -> tuple[list[int], int]:
    """Цепочка карт рождения от карты Личности до карты Души (19 → 10 → 1)."""
    chain = [personality]
    n = personality
    while n > 9:
        n = digit_sum(n)
        chain.append(n)
    return chain, n


def _constellation(soul: int) -> list[int]:
    """Созвездие: все старшие арканы с той же «корневой» цифрой (n, n+9, n+18 ≤ 22)."""
    return [k for k in (soul, soul + 9, soul + 18) if k <= 22]


def greer_from_total(total: int, deck: str = "rws") -> dict:
    """Карты рождения по Грир из уже сложенной суммы ММ + ДД + ГГГГ."""
    personality, reduction = reduce_to_22_digits(total)
    birth_chain, soul = _pattern_cards(personality)
    constellation = _constellation(soul)
    hidden = [k for k in constellation if k not in (personality, soul)]
    single = personality == soul
    pattern = f"{soul}-{soul}" if single else "-".join(str(x) for x in birth_chain)
    res = {
        "total": total,
        "reduction": reduction,
        "pattern": pattern,
        "single": single,
        "personality": card(personality, deck),
        "soul": card(soul, deck),
        "birth_cards": [card(k, deck) for k in birth_chain] if not single else [card(soul, deck)],
        "hidden_factor": [card(k, deck) for k in hidden],
        "constellation": {
            "number": soul,
            "cards": constellation,
            "name_en": GREER_CONSTELLATIONS[soul][0],
            "name_ru": GREER_CONSTELLATIONS[soul][1],
            "principle": GREER_CONSTELLATIONS[soul][2],
            "minor_arcana": ([1, 10] if soul == 1 else [soul]),
        },
    }
    notes = []
    if personality == 19:
        notes.append("Особый случай 19-10-1: три карты рождения (Солнце, Колесо Фортуны, Маг); "
                     "в таблице Грир 10 одновременно «Учитель» (Teacher).")
    if personality == 22:
        notes.append("22 = Шут (0) как карта Личности, Душа = 4 (Император); пара работает как единое целое.")
    if not hidden:
        notes.append("Скрытого фактора нет (в таблице Грир «*»): все карты созвездия уже являются картами рождения.")
    res["notes"] = notes
    return res


def greer_birth_cards(y: int, m: int, d: int, deck: str = "rws") -> dict:
    """Метод Грир: ММ + ДД + ГГГГ → сумма цифр, пока > 22 → Личность; сумма цифр → Душа."""
    total = m + d + y
    res = greer_from_total(total, deck)
    res["formula"] = f"{m} + {d} + {y} = {total}"
    res["method"] = "greer"
    return res


def tarot_school_birth_cards(y: int, m: int, d: int, deck: str = "rws") -> dict:
    """Метод Tarot School (Амберстоуны): ММ + ДД + ВВ + ГГ (год делится на две пары цифр).

    Трёхзначная сумма: первые две цифры как число + третья (135 → 13 + 5 = 18).
    Двузначная > 22: сумма цифр. Однозначный итог n: вторая карта n + 9 (8 → 17).
    """
    cc, yy = divmod(y, 100)
    total = m + d + cc + yy
    chain = [total]
    s = total
    while s > 22:
        s = s // 10 + s % 10 if s >= 100 else digit_sum(s)
        chain.append(s)
    notes: list[str] = []
    if s >= 10:
        cards, soul = _pattern_cards(s)
    else:
        soul = s
        cards = [s, s + 9]
        notes.append("Однозначный итог: вторая карта = n + 9 (Biddy Tarot, Labyrinthos). "
                     "Для n ≤ 4 возможна и третья (n + 18) — ⚠ не подтверждено.")
    if s == 19:
        notes.append("Сумма 19 даёт три карты: Солнце, Колесо Фортуны, Маг.")
    return {
        "method": "tarot_school",
        "formula": f"{m} + {d} + {cc} + {yy} = {total}",
        "reduction": chain,
        "first_card": card(cards[0], deck),
        "birth_cards": [card(k, deck) for k in cards],
        "soul_number": soul,
        "notes": notes,
    }


def year_card(m: int, d: int, year: int, method: str = "greer", deck: str = "rws") -> dict:
    """Карта года: Грир — ММ + ДД + год; Tarot School — ММ + ДД + сумма цифр года."""
    if method == "tarot_school":
        total = m + d + digit_sum(year)
        formula = f"{m} + {d} + ({'+'.join(str(year))}) = {total}"
    else:
        total = m + d + year
        formula = f"{m} + {d} + {year} = {total}"
    n, chain = reduce_to_22_digits(total)
    return {"year": year, "method": method, "formula": formula, "reduction": chain,
            "card": card(n, deck)}


def ru_arcana(y: int, m: int, d: int, over22: str = "subtract", deck: str = "rws") -> dict:
    """Русскоязычные «арканы по дате рождения» (три распространённые схемы)."""
    digits = date_digits(y, m, d)
    s = sum(digits)
    # 1. Аркан дня рождения
    if d <= 22:
        day_n, day_chain = d, [d]
    elif over22 == "digits":
        day_n, day_chain = digit_sum(d), [d, digit_sum(d)]
    else:
        day_n, day_chain = d - 22, [d, d - 22]
    # 2. Сумма всех цифр даты, > 22 → −22
    sub_n, sub_chain = reduce_to_22_subtract(s)
    # 3. Сумма всех цифр даты, > 22 → сумма цифр
    dig_n, dig_chain = reduce_to_22_digits(s)
    # 4. День(≤22, иначе сумма цифр) + месяц + сумма цифр года (≤22) → сумма цифр, пока > 22
    day4 = d if d <= 22 else digit_sum(d)
    year4, _ = reduce_to_22_digits(digit_sum(y))
    t4 = day4 + m + year4
    dmy_n, dmy_chain = reduce_to_22_digits(t4)
    expr = "+".join(str(x) for x in digits)
    return {
        "day_arcana": {"rule": f"день ≤ 22, иначе {'сумма цифр' if over22 == 'digits' else 'день − 22'}",
                       "reduction": day_chain, "card": card(day_n, deck)},
        "date_digits_minus22": {"rule": "сумма всех цифр ДД.ММ.ГГГГ; пока > 22 — вычесть 22",
                                "formula": f"{expr} = {s}", "reduction": sub_chain, "card": card(sub_n, deck)},
        "date_digits_reduce": {"rule": "сумма всех цифр ДД.ММ.ГГГГ; пока > 22 — сложить цифры",
                               "formula": f"{expr} = {s}", "reduction": dig_chain, "card": card(dig_n, deck)},
        "day_month_year": {"rule": "день(>22 → сумма цифр) + месяц + сумма цифр года; пока > 22 — сложить цифры",
                           "formula": f"{day4} + {m} + {year4} = {t4}", "reduction": dmy_chain,
                           "card": card(dmy_n, deck)},
    }


# ---------------------------------------------------------------------------
# B. Ло Шу и число Куа
# ---------------------------------------------------------------------------

def kua_number(year: int, gender: str) -> int:
    """Число Куа (Мин Гуа, восемь дворцов) для китайского солнечного года year.

    Мужчины: 10 − r (до 2000), 9 − r (с 2000), r — сумма двух последних цифр года до 1 цифры;
    общая форма: (11 − year) mod 9, 0 → 9. Женщины: r + 5 (до 2000), r + 6 (с 2000);
    общая форма: (year + 4) mod 9, 0 → 9. Куа 5 → 2 у мужчин, 8 у женщин.
    """
    if gender not in ("male", "female"):
        raise ValueError("Для числа Куа нужен пол: male/female")
    if gender == "male":
        k = (11 - year) % 9 or 9
        return 2 if k == 5 else k
    k = (year + 4) % 9 or 9
    return 8 if k == 5 else k


def kua_year(b: BirthInput, boundary: str = "lichun") -> tuple[int, list[str]]:
    """Год для Куа: с границей Личунь (Солнце 315°) или 1 января.

    Правило совпадает с модулем 03 (calculators/ninestar.py, boundary_precision='auto'):
    * есть время и пояс/место → сравнивается точный момент рождения (UT) с моментом Личуня;
    * времени или пояса нет → сравниваются ДАТЫ: дата рождения против местной даты Личуня
      (в поясе рождения, если он известен, иначе по UTC+8 — китайский календарь);
      день Личуня целиком относится к новому году.
    """
    warns: list[str] = []
    if boundary == "jan1":
        return b.year, warns
    if boundary != "lichun":
        raise ValueError(f"Неизвестный kua_boundary: {boundary}")
    jd_lichun = eph.find_sun_longitude(315.0, julian_day_ut(datetime(b.year, 2, 20, tzinfo=timezone.utc)),
                                       search_back=True)
    if b.has_time and b.tz:
        jd_birth = normalize(b).jd_ut
        if abs(jd_birth - jd_lichun) < 1.0:
            warns.append("Рождение в пределах суток от момента Личуня: год для Куа чувствителен "
                         "к точности времени и пояса.")
    else:
        # Конец суток рождения по местному времени (или по UTC+8, если пояс неизвестен).
        if b.tz:
            end = normalize(BirthInput(b.year, b.month, b.day, 23, 59, tz=b.tz, lat=b.lat, lon=b.lon,
                                       second=59)).jd_ut + 0.999 / 86400.0
            zone_label = b.tz
        else:
            end = julian_day_ut(datetime(b.year, b.month, b.day, tzinfo=timezone.utc)) + 1.0 - 8.0 / 24.0
            zone_label = "UTC+8"
        jd_birth = end - 1e-7
        if b.has_time:
            warns.append("Время рождения указано без пояса/места: граница Личуня для Куа определена по дате.")
        if abs(jd_birth - jd_lichun) < 1.5:
            warns.append(f"Рождение рядом с Личунь (≈4 февраля), точного момента нет: год для Куа определён "
                         f"по дате ({zone_label}; день Личуня относится к новому году, как в модуле 03) — "
                         f"уточните время и место.")
    return (b.year if jd_birth >= jd_lichun else b.year - 1), warns


def loshu_grid(numbers: list[int]) -> dict:
    """Разложить числа 1..9 по сетке Ло Шу (нули отбрасываются)."""
    counts = {k: 0 for k in range(1, 10)}
    for n in numbers:
        if n:
            counts[n] += 1
    grid = [[str(c) * counts[c] for c in row] for row in LOSHU_LAYOUT]
    lines = []
    strength, weakness = [], []
    for key, cells, kind, ru, en, alt in LOSHU_LINES:
        present = sum(1 for c in cells if counts[c] > 0)
        status = "full" if present == 3 else ("empty" if present == 0 else "partial")
        lines.append({"key": key, "cells": list(cells), "type": kind, "name_ru": ru, "name_en": en,
                      "alt_names": alt, "present": present, "status": status})
        if status == "full":
            strength.append({"cells": list(cells), "name": LOSHU_STRENGTH_ARROWS[cells]})
        elif status == "empty":
            weakness.append({"cells": list(cells), "name": LOSHU_WEAKNESS_ARROWS[cells]})
    missing = [k for k in range(1, 10) if counts[k] == 0]
    return {
        "layout": LOSHU_LAYOUT,
        "grid": grid,
        "counts": {str(k): v for k, v in counts.items()},
        "missing": missing,
        "repeated": {str(k): v for k, v in counts.items() if v > 1},
        "planes": lines,
        "arrows_of_strength": strength,
        "arrows_of_weakness": weakness,
        "missing_info": [{"number": k, "element": LOSHU_NUMBER_INFO[k][0],
                          "direction": LOSHU_NUMBER_INFO[k][1], "trigram": LOSHU_NUMBER_INFO[k][2],
                          "color": LOSHU_NUMBER_INFO[k][3], "planet": LOSHU_NUMBER_INFO[k][4]}
                         for k in missing],
    }


# ---------------------------------------------------------------------------
# C. Ведическая нумерология
# ---------------------------------------------------------------------------

def natural_relation(a: int, b: int) -> str:
    """Отношение числа a к числу b через натуральную дружбу их планет (friend/neutral/enemy/self)."""
    pa, pb = PLANETS[a], PLANETS[b]
    if pa == pb:
        return "self"
    if pa in ("rahu", "ketu") or pb in ("rahu", "ketu"):
        return "neutral"
    fr, _ne, en = NATURAL_FRIENDS[pa]
    if pb in fr:
        return "friend"
    if pb in en:
        return "enemy"
    return "neutral"


def relation_table() -> dict[str, dict[str, list[int]]]:
    """Полная таблица друзей/нейтралов/врагов для чисел 1..9."""
    out: dict[str, dict[str, list[int]]] = {}
    for a in range(1, 10):
        row = {"friend": [], "neutral": [], "enemy": []}
        for b in range(1, 10):
            r = natural_relation(a, b)
            if r != "self":
                row[r].append(b)
        out[str(a)] = row
    return out


def transliterate(name: str) -> str:
    """Кириллица → латиница по ICAO 9303 (как в загранпаспорте РФ); латиница не меняется."""
    out = []
    for ch in name.upper():
        out.append(TRANSLIT_ICAO.get(ch, ch))
    return "".join(out)


def chaldean_name_number(name: str) -> dict:
    """Число имени по халдейской таблице (Хейро). Кириллица транслитерируется по ICAO.

    Две «составные» суммы (итоговая однозначная цифра у них всегда одна и та же, mod 9):
    * ``compound`` — сумма значений всех букв (так считают современные онлайн-калькуляторы);
    * ``compound_cheiro`` — сумма однозначных чисел отдельных слов, как в примерах самого
      Хейро (Cheiro's Book of Numbers, гл. XIII–XIV: JOHN 18 → 9, SMITH 17 → 8, 9 + 8 = 17 → 8;
      LLOYD 18 → 9, GEORGE 25 → 7, 9 + 7 = 16 → 7).
    Буквы вне латиницы A–Z (после транслитерации) не имеют значения и попадают в ``unmapped``.
    """
    latin = transliterate(name)
    words = [w for w in "".join(c if c.isalpha() else " " for c in latin).split()]
    parts = []
    total = 0
    cheiro_total = 0
    unmapped: list[str] = []
    for w in words:
        vals = [CHALDEAN[c] for c in w if c in CHALDEAN]
        unmapped.extend(c for c in w if c not in CHALDEAN)
        s = sum(vals)
        word_single = reduce_to_digit(s)[0] if s else 0
        total += s
        cheiro_total += word_single
        parts.append({"word": w, "values": vals, "compound": s, "single": word_single})
    single, chain = reduce_to_digit(total) if total else (0, [0])
    _single_ch, chain_ch = reduce_to_digit(cheiro_total) if cheiro_total else (0, [0])
    return {"input": name, "latin": " ".join(words), "words": parts, "compound": total,
            "reduction": chain, "compound_cheiro": cheiro_total, "reduction_cheiro": chain_ch,
            "number": single, "unmapped": sorted(set(unmapped)),
            "planet": PLANETS.get(single), "planet_ru": PLANET_RU.get(PLANETS.get(single, ""), None)}


def vedic_numbers(y: int, m: int, d: int, master: bool = False) -> dict:
    """Мулянк (день → 1..9) и Бхагьянк (все цифры даты → 1..9)."""
    moolank, m_chain = reduce_to_digit(d)
    digits = date_digits(y, m, d)
    s = sum(digits)
    chain = [s]
    n = s
    while n > 9 and not (master and n in (11, 22, 33)):
        n = digit_sum(n)
        chain.append(n)
    bhagyank = n
    b_single = reduce_to_digit(s)[0]
    rel_dc = natural_relation(moolank, b_single)
    rel_cd = natural_relation(b_single, moolank)
    return {
        "moolank": {"number": moolank, "reduction": m_chain, "planet": PLANETS[moolank],
                    "planet_ru": PLANET_RU[PLANETS[moolank]],
                    "aliases": ["Psychic number", "Driver", "Мулянк", "число души/психическое"]},
        "bhagyank": {"number": bhagyank, "single": b_single, "formula": f"{'+'.join(map(str, digits))} = {s}",
                     "reduction": chain, "planet": PLANETS[b_single], "planet_ru": PLANET_RU[PLANETS[b_single]],
                     "aliases": ["Destiny number", "Conductor", "Бхагьянк", "число судьбы"]},
        "driver_conductor": {
            "pair": f"{moolank}-{b_single}",
            "driver_to_conductor": rel_dc,
            "conductor_to_driver": rel_cd,
            "basis": "натуральная дружба планет (BPHS 3.55); Раху/Кету нейтральны ⚠",
        },
    }


# ---------------------------------------------------------------------------
# Главная функция
# ---------------------------------------------------------------------------

def _parse_date(v) -> date | None:
    if v is None or isinstance(v, date):
        return v
    return date.fromisoformat(str(v))


def calculate(b: BirthInput, **options) -> dict:
    """Рассчитать все три подсистемы модуля 12.

    Опции:
      tarot_method: 'greer' (по умолчанию) | 'tarot_school' | 'arrien'
      deck: 'rws' (по умолчанию; для arrien — 'thoth') | 'marseille' | 'thoth'
      year: год для карты года (по умолчанию — текущий)
      year_card_mode: 'calendar' (по умолчанию) | 'birthday' (год последнего дня рождения на on_date)
      on_date: 'YYYY-MM-DD' — дата, на которую ищется карта года в режиме birthday (по умолчанию сегодня)
      ru_day_over22: 'subtract' (по умолчанию; 23 → 1) | 'digits' (23 → 5)
      loshu_include: 'date' (по умолчанию) | 'date+driver+conductor' | 'date+driver+conductor+kua'
      kua_boundary: 'lichun' (по умолчанию) | 'jan1'
      vedic_master_numbers: False (по умолчанию) | True — не сводить 11/22/33 в Бхагьянке
    """
    y, m, d = b.year, b.month, b.day
    warnings: list[str] = []
    steps: list[str] = []

    tarot_method = options.get("tarot_method", "greer")
    if tarot_method not in ("greer", "tarot_school", "arrien"):
        raise ValueError(f"Неизвестный tarot_method: {tarot_method}")
    deck = options.get("deck", "thoth" if tarot_method == "arrien" else "rws")
    year_mode = options.get("year_card_mode", "birthday" if tarot_method == "arrien" else "calendar")
    on_date = _parse_date(options.get("on_date")) or date.today()
    year = options.get("year")
    if year is None:
        if year_mode == "birthday":
            year = on_date.year if (on_date.month, on_date.day) >= (m, d) else on_date.year - 1
        else:
            year = on_date.year
    year = int(year)
    ru_over22 = options.get("ru_day_over22", "subtract")
    loshu_include = options.get("loshu_include", "date")
    if loshu_include not in ("date", "date+driver+conductor", "date+driver+conductor+kua"):
        raise ValueError(f"Неизвестный loshu_include: {loshu_include}")
    kua_boundary = options.get("kua_boundary", "lichun")
    master = bool(options.get("vedic_master_numbers", False))

    if y < 1900 or y > 2099:
        warnings.append("Год вне 1900–2099: методы опубликованы на примерах XX–XXI вв.; арифметика та же.")

    # ---------------- A. Таро ----------------
    greer = greer_birth_cards(y, m, d, deck)
    school = tarot_school_birth_cards(y, m, d, deck)
    if tarot_method == "tarot_school":
        main_cards = school
    else:
        main_cards = dict(greer)
        if tarot_method == "arrien":
            main_cards["method"] = "arrien"
            main_cards["terms"] = {"personality": "Personality Symbol", "soul": "Soul Symbol",
                                   "year": "Growth Symbol"}
            warnings.append("Вариант Арриен: арифметика как у Грир, колода Тота; детали книги "
                            "(диапазон 1–21/22, «Lifetime Lesson») ⚠ не подтверждены первоисточником.")
    yc_method = "tarot_school" if tarot_method == "tarot_school" else "greer"
    yc = year_card(m, d, year, yc_method, deck)
    yc["mode"] = year_mode
    if year_mode == "birthday":
        yc["valid"] = f"с дня рождения {year} г. до дня рождения {year + 1} г."
    else:
        yc["valid"] = f"календарный {year} г."
    # совпадения карты года с картами рождения (раздатка J. Vernon по Грир: отметить годы, где карта
    # года = Личность, Душа, Скрытый фактор или зодиакальная карта; совпадение со Скрытым фактором
    # Грир называет «Shadow/Teacher Year» — marykgreer.com, ответ от 16.09.2011).
    # Сравнение ведётся с картами рождения выбранного метода (у Tarot School Скрытого фактора нет).
    yn = yc["card"]["number"]
    flags = []
    if tarot_method == "tarot_school":
        if yn == school["first_card"]["number"]:
            flags.append("personality")
        if yn == school["soul_number"]:
            flags.append("soul")
        if yn in [c["number"] for c in school["birth_cards"]] and not flags:
            flags.append("birth_card")
    else:
        if yn == greer["personality"]["number"]:
            flags.append("personality")
        if yn == greer["soul"]["number"]:
            flags.append("soul")
        if yn in [c["number"] for c in greer["birth_cards"]] and not flags:
            flags.append("birth_card")       # средняя карта тройки 19-10-1 (10) — она же Учитель
        if yn in [c["number"] for c in greer["hidden_factor"]]:
            flags.append("hidden_factor (год Учителя/Тени)")
    yc["matches_birth_cards"] = flags

    steps.append(f"Грир: {greer['formula']}; приведение {greer['reduction']} → Личность "
                 f"{greer['personality']['number']}, Душа {greer['soul']['number']} (паттерн {greer['pattern']}).")
    steps.append(f"Tarot School: {school['formula']}; приведение {school['reduction']} → "
                 f"{[c['number'] for c in school['birth_cards']]}.")
    steps.append(f"Карта года ({yc_method}): {yc['formula']} → {yc['reduction']} → {yn}.")

    ru = ru_arcana(y, m, d, ru_over22, deck)
    steps.append(f"Аркан дня: {ru['day_arcana']['reduction']}; сумма цифр даты: "
                 f"{ru['date_digits_minus22']['formula']} → −22: {ru['date_digits_minus22']['reduction']}, "
                 f"сложением цифр: {ru['date_digits_reduce']['reduction']}.")

    # ---------------- C. Ведическая нумерология (нужна для Ло Шу) ----------------
    ved = vedic_numbers(y, m, d, master)
    driver = ved["moolank"]["number"]
    conductor = ved["bhagyank"]["single"]
    steps.append(f"Мулянк: {ved['moolank']['reduction']} → {driver}; Бхагьянк: "
                 f"{ved['bhagyank']['formula']} → {ved['bhagyank']['reduction']}.")

    # ---------------- B. Ло Шу ----------------
    kua = None
    if b.gender in ("male", "female"):
        ky, kw = kua_year(b, kua_boundary)
        warnings.extend(kw)
        kval = kua_number(ky, b.gender)
        kua = {"number": kval, "year_used": ky, "boundary": kua_boundary, "gender": b.gender,
               "group": "East (1,3,4,9)" if kval in (1, 3, 4, 9) else "West (2,6,7,8)"}
        if ky != y:
            warnings.append(f"Рождение до Личунь: для Куа взят {ky} г.")
        steps.append(f"Куа ({b.gender}, год {ky}): {kval}.")
    date_nums = [x for x in date_digits(y, m, d) if x]
    extra: list[int] = []
    if loshu_include != "date":
        extra = [driver, conductor]
        if loshu_include.endswith("+kua"):
            if kua is None:
                warnings.append("Для варианта с Куа нужен пол — Куа не добавлен.")
            else:
                extra.append(kua["number"])
    grid = loshu_grid(date_nums + extra)
    grid["include"] = loshu_include
    grid["numbers_placed"] = date_nums + extra
    grid["driver"] = driver
    grid["conductor"] = conductor
    grid["kua"] = kua
    # альтернативная сетка (вторая распространённая схема) — для сравнения
    alt_inc = "date+driver+conductor" if loshu_include == "date" else "date"
    alt_nums = date_nums + ([driver, conductor] if alt_inc != "date" else [])
    alt = loshu_grid(alt_nums)
    grid["alternative"] = {"include": alt_inc, "numbers_placed": alt_nums, "grid": alt["grid"],
                           "missing": alt["missing"],
                           "arrows_of_strength": [a["cells"] for a in alt["arrows_of_strength"]],
                           "arrows_of_weakness": [a["cells"] for a in alt["arrows_of_weakness"]]}
    steps.append(f"Ло Шу ({loshu_include}): числа {grid['numbers_placed']}; отсутствуют {grid['missing']}.")

    # имя
    name_res = None
    if b.name:
        name_res = chaldean_name_number(b.name)
        if any("А" <= ch <= "я" or ch in "Ёё" for ch in b.name):
            warnings.append("Имя на кириллице транслитерировано по ICAO 9303 (загранпаспорт РФ); "
                            "другая латинская запись даст другое число имени ⚠.")
        if name_res["unmapped"]:
            warnings.append(f"Буквы без значения в халдейской таблице пропущены: {''.join(name_res['unmapped'])} "
                            f"(таблица определена только для латиницы A–Z; запишите имя латиницей).")
        steps.append(f"Имя (халдейская таблица): {name_res['latin']} → {name_res['compound']} → {name_res['number']} "
                     f"(по Хейро — сумма чисел слов: {' + '.join(str(w['single']) for w in name_res['words'])} "
                     f"= {name_res['compound_cheiro']} → {name_res['number']}).")
    ved["name_number"] = name_res
    ved["relations_table"] = relation_table()
    if name_res and name_res["number"]:
        ved["name_relations"] = {
            "to_moolank": natural_relation(name_res["number"], driver) if name_res["number"] != driver else "self",
            "to_bhagyank": natural_relation(name_res["number"], conductor) if name_res["number"] != conductor else "self",
        }

    return {
        "method": "tarot_loshu",
        "variant": {"tarot_method": tarot_method, "deck": deck, "year_card_mode": year_mode,
                    "ru_day_over22": ru_over22, "loshu_include": loshu_include,
                    "kua_boundary": kua_boundary, "vedic_master_numbers": master},
        "inputs_used": {"date": f"{y:04d}-{m:02d}-{d:02d}", "gender": b.gender, "name": b.name,
                        "year_for_year_card": year,
                        "time_used_for_kua": bool(kua is not None and kua_boundary == "lichun"
                                                  and b.has_time and b.tz)},
        "warnings": warnings,
        "tarot": {
            "birth_cards": main_cards,
            "birth_cards_greer": greer,
            "birth_cards_tarot_school": school,
            "year_card": yc,
            "ru_arcana": ru,
        },
        "loshu": grid,
        "vedic": ved,
        "steps": steps,
    }
