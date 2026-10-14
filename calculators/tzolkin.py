"""Майянский календарь: Цолькин (260 дней) в двух системах.

A) **Dreamspell / «13 Лун»** (Хосе Аргуэльес, Foundation for the Law of Time) — система,
   принятая в русскоязычной эзотерической среде, поэтому она — система по умолчанию.
   * Якорь: 26.07.1987 = Кин 34 (Белый Галактический Волшебник); каждый год 26 июля
     («Галактический Новый год», 1-й день Магнитной Луны) кин сдвигается на +105.
   * 25 июля — «День вне времени» (у него ЕСТЬ свой кин).
   * 29 февраля — «0.0 Хунаб Ку»: вне лун и недель, собственного кина нет. Официальное правило
     Фонда (текст страницы lawoftime.org/decode): родившимся 29.02 ДО полудня местного времени
     брать 28 февраля, ПОСЛЕ полудня — 1 марта. Сам JS-виджет (``2==p&&29==m&&(m=28)``) и
     13moon.com времени не спрашивают и всегда дают кин 28.02. Опция ``feb29_rule``.
   * Оракул судьбы: Ведущий (по группе тона), Аналог (сумма печатей 19),
     Антипод (печать ±10), Оккультный (сумма печатей 21, сумма тонов 14, сумма кинов 261).
   * Волновой модуль, замок, земная семья, цветовая семья, ПГА, дата «13 Лун».

B) **Классический счёт майя** (непрерывный счёт, который сохраняется у кʼиче до сих пор):
   * Корреляция GMT 584283 (по умолчанию) или любая другая (584285 — «Лаунсбери / GMT+2»).
   * JDN → Длинный счёт, Цолькин (число + имя дня Imix…Ajaw), Хааб.
   * Проверка: 21.12.2012 = 13.0.0.0.0, 4 Ajaw 3 Kʼankʼin (GMT 584283).

Две системы дают РАЗНЫЕ результаты для одной даты: Dreamspell не считает 29 февраля и
привязан к собственному якорю. Разница между ними растёт на 1 после каждого 29 февраля.

Подробности, таблицы, разобранные примеры и источники: knowledge-base/13-tzolkin.md.
"""
from __future__ import annotations

from typing import Any

from .common.time import BirthInput

METHOD = "tzolkin"

#: Корреляционные константы (JDN дня 13.0.0.0.0 = 4 Ajaw 8 Kumkʼu).
GMT_CORRELATION = 584283          #: Goodman–Martinez–Thompson (Modified Thompson 2) — общепринятая
LOUNSBURY_CORRELATION = 584285    #: Thompson (Lounsbury), «GMT+2»
NAMED_CORRELATIONS: dict[str, int] = {
    "gmt": GMT_CORRELATION, "584283": GMT_CORRELATION,
    "lounsbury": LOUNSBURY_CORRELATION, "gmt+2": LOUNSBURY_CORRELATION, "584285": LOUNSBURY_CORRELATION,
    "goodman": 584280, "martinez": 584281, "thompson1": 584284,
}

# ---------------------------------------------------------------------------
# Якорь Dreamspell
# ---------------------------------------------------------------------------

#: 26 июля 1987 г. = Кин 34 (Белый Галактический Волшебник) — начало 13-лунного счёта.
DS_ANCHOR_YEAR = 1987
DS_ANCHOR_KIN = 34
#: Сдвиг кина за 365-дневный год: 365 mod 260 = 105.
DS_YEAR_STEP = 105
#: Номер дня 26 июля в невисокосном году (1 января = 0).
DS_NEW_YEAR_DOY = 206

#: Накопленные дни до начала месяца в невисокосном году.
_CUM_DAYS = (0, 31, 59, 90, 120, 151, 181, 212, 243, 273, 304, 334)
#: Коды месяцев для ручного расчёта «код года + код месяца + число» (накопленные дни mod 260).
DS_MONTH_CODES: dict[int, int] = {m: _CUM_DAYS[m - 1] % 260 for m in range(1, 13)}

# ---------------------------------------------------------------------------
# Справочные таблицы Dreamspell
# ---------------------------------------------------------------------------

COLORS: dict[str, dict[str, Any]] = {
    "red":    {"ru": ("Красный", "Красная", "Красное"), "en": "Red",
               "direction_ru": "Восток", "action_ru": "инициирует", "action_en": "initiates"},
    "white":  {"ru": ("Белый", "Белая", "Белое"), "en": "White",
               "direction_ru": "Север", "action_ru": "очищает", "action_en": "refines"},
    "blue":   {"ru": ("Синий", "Синяя", "Синее"), "en": "Blue",
               "direction_ru": "Запад", "action_ru": "преобразует", "action_en": "transforms"},
    "yellow": {"ru": ("Жёлтый", "Жёлтая", "Жёлтое"), "en": "Yellow",
               "direction_ru": "Юг", "action_ru": "созревает", "action_en": "ripens"},
}
_COLOR_BY_MOD4 = {1: "red", 2: "white", 3: "blue", 0: "yellow"}
_GENDER_IDX = {"m": 0, "f": 1, "n": 2}

#: 20 солнечных печатей (племён). Номер 1–20 (Солнце = 20, в кодах Dreamspell — 0).
#: power/action/essence — официальные ключевые слова (lawoftime.org, 13 Moon Calendar Tutorial);
#: русский перевод — по смыслу, в русских изданиях встречаются синонимы.
#: block — «Я опечатываю … (ввод/хранение/процесс/вывод/матрицу)» из официального аффирмационного шаблона.
SEALS: dict[int, dict[str, Any]] = {
    1:  {"ru": "Дракон", "gen": "Дракона", "g": "m", "en": "Dragon", "yucatec": "Imix",
         "power": ("Рождение", "Birth"), "action": ("Питает", "Nurtures"), "essence": ("Бытие", "Being"),
         "block": ("ввод", "Input")},
    2:  {"ru": "Ветер", "gen": "Ветра", "g": "m", "en": "Wind", "yucatec": "Ik",
         "power": ("Дух", "Spirit"), "action": ("Общается", "Communicates"), "essence": ("Дыхание", "Breath"),
         "block": ("ввод", "Input")},
    3:  {"ru": "Ночь", "gen": "Ночи", "g": "f", "en": "Night", "yucatec": "Akbal",
         "power": ("Изобилие", "Abundance"), "action": ("Видит сны", "Dreams"), "essence": ("Интуиция", "Intuition"),
         "block": ("ввод", "Input")},
    4:  {"ru": "Семя", "gen": "Семени", "g": "n", "en": "Seed", "yucatec": "Kan",
         "power": ("Расцвет", "Flowering"), "action": ("Нацеливает", "Targets"), "essence": ("Осознанность", "Awareness"),
         "block": ("ввод", "Input")},
    5:  {"ru": "Змей", "gen": "Змея", "g": "m", "en": "Serpent", "yucatec": "Chicchan",
         "power": ("Жизненная сила", "Life Force"), "action": ("Выживает", "Survives"), "essence": ("Инстинкт", "Instinct"),
         "block": ("хранение", "Store")},
    6:  {"ru": "Соединитель Миров", "gen": "Соединителя Миров", "g": "m", "en": "Worldbridger", "yucatec": "Cimi",
         "power": ("Смерть", "Death"), "action": ("Уравнивает", "Equalizes"), "essence": ("Возможность", "Opportunity"),
         "block": ("хранение", "Store")},
    7:  {"ru": "Рука", "gen": "Руки", "g": "f", "en": "Hand", "yucatec": "Manik",
         "power": ("Свершение", "Accomplishment"), "action": ("Знает", "Knows"), "essence": ("Исцеление", "Healing"),
         "block": ("хранение", "Store")},
    8:  {"ru": "Звезда", "gen": "Звезды", "g": "f", "en": "Star", "yucatec": "Lamat",
         "power": ("Элегантность", "Elegance"), "action": ("Украшает", "Beautifies"), "essence": ("Искусство", "Art"),
         "block": ("хранение", "Store")},
    9:  {"ru": "Луна", "gen": "Луны", "g": "f", "en": "Moon", "yucatec": "Muluc",
         "power": ("Вселенская вода", "Universal Water"), "action": ("Очищает", "Purifies"), "essence": ("Поток", "Flow"),
         "block": ("процесс", "Process")},
    10: {"ru": "Собака", "gen": "Собаки", "g": "f", "en": "Dog", "yucatec": "Oc",
         "power": ("Сердце", "Heart"), "action": ("Любит", "Loves"), "essence": ("Верность", "Loyalty"),
         "block": ("процесс", "Process")},
    11: {"ru": "Обезьяна", "gen": "Обезьяны", "g": "f", "en": "Monkey", "yucatec": "Chuen",
         "power": ("Магия", "Magic"), "action": ("Играет", "Plays"), "essence": ("Иллюзия", "Illusion"),
         "block": ("процесс", "Process")},
    12: {"ru": "Человек", "gen": "Человека", "g": "m", "en": "Human", "yucatec": "Eb",
         "power": ("Свободная воля", "Free Will"), "action": ("Влияет", "Influences"), "essence": ("Мудрость", "Wisdom"),
         "block": ("процесс", "Process")},
    13: {"ru": "Небесный Странник", "gen": "Небесного Странника", "g": "m", "en": "Skywalker", "yucatec": "Ben",
         "power": ("Пространство", "Space"), "action": ("Исследует", "Explores"), "essence": ("Бодрствование", "Wakefulness"),
         "block": ("вывод", "Output")},
    14: {"ru": "Волшебник", "gen": "Волшебника", "g": "m", "en": "Wizard", "yucatec": "Ix",
         "power": ("Безвременье", "Timelessness"), "action": ("Совершает волшебство (очаровывает)", "Enchants"),
         "essence": ("Восприимчивость", "Receptivity"), "block": ("вывод", "Output")},
    15: {"ru": "Орёл", "gen": "Орла", "g": "m", "en": "Eagle", "yucatec": "Men",
         "power": ("Видение", "Vision"), "action": ("Создаёт", "Creates"), "essence": ("Разум", "Mind"),
         "block": ("вывод", "Output")},
    16: {"ru": "Воин", "gen": "Воина", "g": "m", "en": "Warrior", "yucatec": "Cib",
         "power": ("Интеллект", "Intelligence"), "action": ("Вопрошает", "Questions"), "essence": ("Бесстрашие", "Fearlessness"),
         "block": ("вывод", "Output")},
    17: {"ru": "Земля", "gen": "Земли", "g": "f", "en": "Earth", "yucatec": "Caban",
         "power": ("Навигация", "Navigation"), "action": ("Развивается (эволюционирует)", "Evolves"),
         "essence": ("Синхронность", "Synchronicity"), "block": ("матрицу", "Matrix")},
    18: {"ru": "Зеркало", "gen": "Зеркала", "g": "n", "en": "Mirror", "yucatec": "Etznab",
         "power": ("Бесконечность", "Endlessness"), "action": ("Отражает", "Reflects"), "essence": ("Порядок", "Order"),
         "block": ("матрицу", "Matrix")},
    19: {"ru": "Буря", "gen": "Бури", "g": "f", "en": "Storm", "yucatec": "Cauac",
         "power": ("Самопорождение", "Self-generation"), "action": ("Катализирует", "Catalyzes"), "essence": ("Энергия", "Energy"),
         "block": ("матрицу", "Matrix")},
    20: {"ru": "Солнце", "gen": "Солнца", "g": "n", "en": "Sun", "yucatec": "Ahau",
         "power": ("Вселенский огонь", "Universal Fire"), "action": ("Просветляет", "Enlightens"), "essence": ("Жизнь", "Life"),
         "block": ("матрицу", "Matrix")},
}

#: 13 галактических тонов. ru — формы прилагательного (м, ж, ср). Сила/действие/суть —
#: официальные Power/Action/Essence (lawoftime.org), русские — по hunab.ru («13 галактических тонов»).
TONES: dict[int, dict[str, Any]] = {
    1:  {"ru": ("Магнитный", "Магнитная", "Магнитное"), "en": "Magnetic", "maya": "Хун",
         "power": ("Объединять", "Unify"), "action": ("Привлечение", "Attract"), "essence": ("Цель", "Purpose")},
    2:  {"ru": ("Лунный", "Лунная", "Лунное"), "en": "Lunar", "maya": "Ка",
         "power": ("Поляризовать", "Polarize"), "action": ("Стабилизация", "Stabilize"), "essence": ("Вызов", "Challenge")},
    3:  {"ru": ("Электрический", "Электрическая", "Электрическое"), "en": "Electric", "maya": "Ош",
         "power": ("Активировать", "Activate"), "action": ("Связывание", "Bond"), "essence": ("Служение", "Service")},
    4:  {"ru": ("Самосущный", "Самосущная", "Самосущное"), "en": "Self-Existing", "maya": "Кан",
         "power": ("Определять", "Define"), "action": ("Измерение", "Measure"), "essence": ("Форма", "Form")},
    5:  {"ru": ("Обертонный", "Обертонная", "Обертонное"), "en": "Overtone", "maya": "Хо",
         "power": ("Наделять силой", "Empower"), "action": ("Управление", "Command"), "essence": ("Сияние", "Radiance")},
    6:  {"ru": ("Ритмический", "Ритмическая", "Ритмическое"), "en": "Rhythmic", "maya": "Уак",
         "power": ("Организовывать", "Organize"), "action": ("Балансировка", "Balance"), "essence": ("Равенство", "Equality")},
    7:  {"ru": ("Резонансный", "Резонансная", "Резонансное"), "en": "Resonant", "maya": "Ук",
         "power": ("Проводить через себя", "Channel"), "action": ("Вдохновение", "Inspire"), "essence": ("Сонастройка", "Attunement")},
    8:  {"ru": ("Галактический", "Галактическая", "Галактическое"), "en": "Galactic", "maya": "Уашак",
         "power": ("Гармонизировать", "Harmonize"), "action": ("Служить эталоном (моделировать)", "Model"),
         "essence": ("Целостность", "Integrity")},
    9:  {"ru": ("Солнечный", "Солнечная", "Солнечное"), "en": "Solar", "maya": "Болон",
         "power": ("Пульсировать", "Pulse"), "action": ("Реализовывать", "Realize"), "essence": ("Намерение", "Intention")},
    10: {"ru": ("Планетарный", "Планетарная", "Планетарное"), "en": "Planetary", "maya": "Лахун",
         "power": ("Совершенствовать", "Perfect"), "action": ("Производить", "Produce"), "essence": ("Проявление", "Manifestation")},
    11: {"ru": ("Спектральный", "Спектральная", "Спектральное"), "en": "Spectral", "maya": "Хунлахун",
         "power": ("Растворять", "Dissolve"), "action": ("Отпускать", "Release"), "essence": ("Освобождение", "Liberation")},
    12: {"ru": ("Кристаллический", "Кристаллическая", "Кристаллическое"), "en": "Crystal", "maya": "Калахун",
         "power": ("Посвящать", "Dedicate"), "action": ("Универсализировать", "Universalize"),
         "essence": ("Сотрудничество", "Cooperation")},
    13: {"ru": ("Космический", "Космическая", "Космическое"), "en": "Cosmic", "maya": "Ошлахун",
         "power": ("Выдерживать (переносить)", "Endure"), "action": ("Трансцендировать", "Transcend"),
         "essence": ("Присутствие", "Presence")},
}

#: Правило Ведущего: тон -> (сдвиг печати, описание). Источник: lawoftime.org 13 Moon Calendar Tutorial
#: и официальный виджет lawoftime.org/decode (guide=seal+4 / +12 / +8 / −4).
GUIDE_SHIFT: dict[int, int] = {1: 0, 6: 0, 11: 0, 2: 12, 7: 12, 12: 12, 3: 4, 8: 4, 13: 4, 4: 16, 9: 16, 5: 8, 10: 8}
GUIDE_RULE_TEXT: dict[int, str] = {
    0: "тоны 1, 6, 11: Ведущий = та же печать («ведом собственной удвоенной силой»)",
    12: "тоны 2, 7, 12: Ведущий = печать +12 (или −8)",
    4: "тоны 3, 8, 13: Ведущий = печать +4 (или −16)",
    16: "тоны 4, 9: Ведущий = печать −4 (или +16)",
    8: "тоны 5, 10: Ведущий = печать +8 (или −12)",
}

#: 5 замков по 52 кина. Источник русских названий и «дворов»: news.law-of-time.ru («Ноосферное письмо»
#: № 22–27, 2024: «Красный Восточный Замок Поворота: Двор Рождения (Кины 1-52)» и т.д.).
#: Для Зелёного замка в одном выпуске встречается и «Двор Матрицы».
CASTLES: dict[int, dict[str, Any]] = {
    1: {"ru": "Красный Восточный Замок Поворота", "en": "Red Eastern Castle of Turning",
        "court_ru": "Двор Рождения", "kins": (1, 52)},
    2: {"ru": "Белый Северный Замок Перехода", "en": "White Northern Castle of Crossing",
        "court_ru": "Двор Смерти", "kins": (53, 104)},
    3: {"ru": "Синий Западный Замок Горения", "en": "Blue Western Castle of Burning",
        "court_ru": "Двор Магии", "kins": (105, 156)},
    4: {"ru": "Жёлтый Южный Замок Даяния", "en": "Yellow Southern Castle of Giving",
        "court_ru": "Двор Интеллекта", "kins": (157, 208)},
    5: {"ru": "Зелёный Центральный Замок Чарования", "en": "Green Central Castle of Enchantment",
        "court_ru": "Двор Синхронизации", "kins": (209, 260)},
}

#: 5 земных семей = печати с одинаковым остатком по модулю 5 (Аргуэльес, «28 Meditations on the Law of Time»,
#: Meditation 5: Polar = Dog, Eagle, Sun, Serpent; Cardinal = Monkey, Warrior, Dragon, World-Bridger;
#: Core = Hand, Human, Earth, Wind; Signal = Star, Skywalker, Mirror, Night; Gateway = Seed, Moon, Wizard, Storm).
EARTH_FAMILIES: dict[int, dict[str, Any]] = {
    0: {"key": "polar", "ru": "Полярная", "en": "Polar", "seals": (5, 10, 15, 20),
        "center_ru": "корона (макушка)", "zone_ru": "северный полюс"},
    1: {"key": "cardinal", "ru": "Кардинальная", "en": "Cardinal", "seals": (1, 6, 11, 16),
        "center_ru": "горло", "zone_ru": "северная умеренная зона"},
    2: {"key": "core", "ru": "Центральная", "en": "Core", "seals": (2, 7, 12, 17),
        "center_ru": "сердце", "zone_ru": "экваториальный пояс"},
    3: {"key": "signal", "ru": "Сигнальная", "en": "Signal", "seals": (3, 8, 13, 18),
        "center_ru": "солнечное сплетение", "zone_ru": "южная умеренная зона"},
    4: {"key": "gateway", "ru": "Портальная", "en": "Gateway", "seals": (4, 9, 14, 19),
        "center_ru": "корень (основание)", "zone_ru": "южный полюс"},
}

#: 52 Портала Галактической Активации (ПГА). Источник: официальный виджет lawoftime.org/decode (массив gaps).
GAP_KINS: frozenset[int] = frozenset((
    1, 20, 22, 39, 43, 50, 51, 58, 64, 69, 72, 77, 85, 88, 93, 96,
    106, 107, 108, 109, 110, 111, 112, 113, 114, 115,
    146, 147, 148, 149, 150, 151, 152, 153, 154, 155,
    165, 168, 173, 176, 184, 189, 192, 197, 203, 210, 211, 218, 222, 239, 241, 260,
))

#: 16 «полярных кинов» (тоны 3, 4, 10, 11 печатей Полярной семьи). Источник: тот же виджет (массив season).
POLAR_KINS: frozenset[int] = frozenset((10, 30, 50, 55, 75, 95, 115, 120, 140, 160, 180, 185, 205, 225, 245, 250))

#: 13 Лун по 28 дней (Магнитная Луна начинается 26 июля). Русские названия — news.law-of-time.ru.
MOONS: dict[int, dict[str, str]] = {
    1:  {"ru": "Магнитная Луна Летучей Мыши", "en": "Magnetic Moon of the Bat"},
    2:  {"ru": "Лунная Луна Скорпиона", "en": "Lunar Moon of the Scorpion"},
    3:  {"ru": "Электрическая Луна Оленя", "en": "Electric Moon of the Deer"},
    4:  {"ru": "Самосущная Луна Совы", "en": "Self-Existing Moon of the Owl"},
    5:  {"ru": "Обертонная Луна Павлина", "en": "Overtone Moon of the Peacock"},
    6:  {"ru": "Ритмическая Луна Ящерицы", "en": "Rhythmic Moon of the Lizard"},
    7:  {"ru": "Резонансная Луна Обезьяны", "en": "Resonant Moon of the Monkey"},
    8:  {"ru": "Галактическая Луна Сокола (Ястреба)", "en": "Galactic Moon of the Hawk"},
    9:  {"ru": "Солнечная Луна Ягуара", "en": "Solar Moon of the Jaguar"},
    10: {"ru": "Планетарная Луна Собаки", "en": "Planetary Moon of the Dog"},
    11: {"ru": "Спектральная Луна Змеи", "en": "Spectral Moon of the Serpent"},
    12: {"ru": "Кристаллическая Луна Кролика", "en": "Crystal Moon of the Rabbit"},
    13: {"ru": "Космическая Луна Черепахи", "en": "Cosmic Moon of the Turtle"},
}

#: 7 радиальных плазм (дни недели 13-лунного календаря): 1, 8, 15, 22 дни луны — всегда Дали и т.д.
PLASMAS: tuple[tuple[str, str], ...] = (
    ("Дали", "Dali"), ("Сэли", "Seli"), ("Гамма", "Gamma"), ("Кали", "Kali"),
    ("Альфа", "Alpha"), ("Лими", "Limi"), ("Силио", "Silio"),
)

# ---------------------------------------------------------------------------
# Справочные таблицы классического счёта
# ---------------------------------------------------------------------------

#: 20 имён дней (индекс 1–20). name — орфография Академии майяских языков Гватемалы (ALMG),
#: landa — орфография XVI в. (Ланда), kiche — кʼиче (Wikipedia «Maya calendar», по Kaufman 1989),
#: ru — традиционная русская передача (⚠ написание в русской литературе варьирует).
DAY_NAMES: dict[int, dict[str, str]] = {
    1:  {"name": "Imix", "landa": "Imix", "kiche": "Imox", "ru": "Имиш"},
    2:  {"name": "Ikʼ", "landa": "Ik", "kiche": "Iqʼ", "ru": "Ик"},
    3:  {"name": "Akʼbʼal", "landa": "Akbal", "kiche": "Aqʼabʼal", "ru": "Акбаль"},
    4:  {"name": "Kʼan", "landa": "Kan", "kiche": "Kʼat", "ru": "Кан"},
    5:  {"name": "Chikchan", "landa": "Chicchan", "kiche": "Kan", "ru": "Чикчан"},
    6:  {"name": "Kimi", "landa": "Cimi", "kiche": "Kame", "ru": "Кими"},
    7:  {"name": "Manikʼ", "landa": "Manik", "kiche": "Kej", "ru": "Маник"},
    8:  {"name": "Lamat", "landa": "Lamat", "kiche": "Qʼanil", "ru": "Ламат"},
    9:  {"name": "Muluk", "landa": "Muluc", "kiche": "Toj", "ru": "Мулук"},
    10: {"name": "Ok", "landa": "Oc", "kiche": "Tzʼiʼ", "ru": "Ок"},
    11: {"name": "Chuwen", "landa": "Chuen", "kiche": "Bʼatzʼ", "ru": "Чуэн"},
    12: {"name": "Ebʼ", "landa": "Eb", "kiche": "Eʼ", "ru": "Эб"},
    13: {"name": "Bʼen", "landa": "Ben", "kiche": "Aj", "ru": "Бен"},
    14: {"name": "Ix", "landa": "Ix", "kiche": "Iʼx", "ru": "Иш"},
    15: {"name": "Men", "landa": "Men", "kiche": "Tzʼikin", "ru": "Мен"},
    16: {"name": "Kʼibʼ", "landa": "Cib", "kiche": "Ajmaq", "ru": "Киб"},
    17: {"name": "Kabʼan", "landa": "Caban", "kiche": "Noʼj", "ru": "Кабан"},
    18: {"name": "Etzʼnabʼ", "landa": "Etznab", "kiche": "Tijax", "ru": "Эцнаб"},
    19: {"name": "Kawak", "landa": "Cauac", "kiche": "Kawoq", "ru": "Кавак"},
    20: {"name": "Ajaw", "landa": "Ahau", "kiche": "Ajpu", "ru": "Ахав"},
}

#: 18 месяцев по 20 дней + Wayebʼ (5 дней). Индекс 0–18.
HAAB_MONTHS: tuple[dict[str, str], ...] = (
    {"name": "Pop", "ru": "Поп"}, {"name": "Woʼ", "ru": "Во"}, {"name": "Sip", "ru": "Сип"},
    {"name": "Sotzʼ", "ru": "Соц"}, {"name": "Sek", "ru": "Сек"}, {"name": "Xul", "ru": "Шуль"},
    {"name": "Yaxkʼin", "ru": "Яшкин"}, {"name": "Mol", "ru": "Моль"}, {"name": "Chʼen", "ru": "Чен"},
    {"name": "Yax", "ru": "Яш"}, {"name": "Sak", "ru": "Сак"}, {"name": "Keh", "ru": "Кех"},
    {"name": "Mak", "ru": "Мак"}, {"name": "Kʼankʼin", "ru": "Канкин"}, {"name": "Muwan", "ru": "Муван"},
    {"name": "Pax", "ru": "Паш"}, {"name": "Kʼayab", "ru": "Кайаб"}, {"name": "Kumkʼu", "ru": "Кумку"},
    {"name": "Wayebʼ", "ru": "Ваеб"},
)

#: Позиция эры 13.0.0.0.0 в Хаабе: 8 Kumkʼu = 17·20 + 8 = 348-й день года Хааб (0 = 0 Pop).
_HAAB_EPOCH_POS = 348

# ---------------------------------------------------------------------------
# Календарная арифметика (общая)
# ---------------------------------------------------------------------------


def gregorian_to_jdn(y: int, m: int, d: int) -> int:
    """Юлианский день (целый, полдень) для даты пролептического григорианского календаря.

    Годы астрономические: 1 г. до н.э. = 0, 3114 г. до н.э. = −3113.
    """
    a = (14 - m) // 12
    yy = y + 4800 - a
    mm = m + 12 * a - 3
    return d + (153 * mm + 2) // 5 + 365 * yy + yy // 4 - yy // 100 + yy // 400 - 32045


def julian_to_jdn(y: int, m: int, d: int) -> int:
    """Юлианский день для даты юлианского календаря (астрономические годы)."""
    a = (14 - m) // 12
    yy = y + 4800 - a
    mm = m + 12 * a - 3
    return d + (153 * mm + 2) // 5 + 365 * yy + yy // 4 - 32083


def jdn_to_gregorian(jdn: int) -> tuple[int, int, int]:
    """Обратное преобразование JDN -> (год, месяц, день) пролептического григорианского календаря."""
    a = jdn + 32044
    b = (4 * a + 3) // 146097
    c = a - 146097 * b // 4
    dd = (4 * c + 3) // 1461
    e = c - 1461 * dd // 4
    m = (5 * e + 2) // 153
    day = e - (153 * m + 2) // 5 + 1
    month = m + 3 - 12 * (m // 10)
    year = 100 * b + dd - 4800 + m // 10
    return year, month, day


def _is_leap(y: int) -> bool:
    return y % 4 == 0 and (y % 100 != 0 or y % 400 == 0)


def _validate_gregorian(y: int, m: int, d: int) -> None:
    if not 1 <= m <= 12:
        raise ValueError(f"Неверный месяц: {m}")
    mdays = (31, 29 if _is_leap(y) else 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31)[m - 1]
    if not 1 <= d <= mdays:
        raise ValueError(f"Неверная дата: {d:02d}.{m:02d}.{y}")


def kin_from_tone_seal(tone: int, seal: int) -> int:
    """Кин 1–260 по тону (1–13) и печати (1–20; Солнце = 20 или 0).

    Китайская теорема об остатках: 40 ≡ 1 (mod 13), 40 ≡ 0 (mod 20); −39 ≡ 0 (mod 13), −39 ≡ 1 (mod 20),
    поэтому кин ≡ 40·тон − 39·печать (mod 260), 0 → 260.
    """
    k = (40 * tone - 39 * seal) % 260
    return 260 if k == 0 else k


def tone_of(kin: int) -> int:
    """Тон кина: остаток от деления на 13 (0 → 13)."""
    t = kin % 13
    return 13 if t == 0 else t


def seal_of(kin: int) -> int:
    """Печать кина: остаток от деления на 20 (0 → 20, Солнце)."""
    s = kin % 20
    return 20 if s == 0 else s


def _wrap20(s: int) -> int:
    s %= 20
    return 20 if s == 0 else s


# ---------------------------------------------------------------------------
# Dreamspell
# ---------------------------------------------------------------------------


def _noleap_doy(m: int, d: int) -> int:
    """Номер дня в 365-дневном году (1 января = 0); 29 февраля приравнивается к 28 февраля."""
    if m == 2 and d == 29:
        d = 28
    return _CUM_DAYS[m - 1] + d - 1


def dreamspell_year_start(y: int, m: int, d: int) -> int:
    """Григорианский год, в котором начался 13-лунный год (26 июля) для данной даты."""
    return y if (m, d) >= (7, 26) else y - 1


def dreamspell_year_bearer(year_start: int) -> int:
    """Кин 26 июля года ``year_start`` (Носитель года): 34 + 105·(год − 1987) по модулю 260."""
    k = (DS_ANCHOR_KIN - 1 + DS_YEAR_STEP * (year_start - DS_ANCHOR_YEAR)) % 260
    return k + 1


def dreamspell_day_offset(m: int, d: int) -> int:
    """Номер дня внутри 13-лунного года: 0 = 26 июля … 364 = 25 июля (29.02 = 28.02)."""
    return (_noleap_doy(m, d) - DS_NEW_YEAR_DOY) % 365


def dreamspell_kin(y: int, m: int, d: int) -> int:
    """Кин Dreamspell для григорианской даты (алгоритм официального виджета lawoftime.org/decode)."""
    _validate_gregorian(y, m, d)
    y0 = dreamspell_year_start(y, m, d)
    bearer = dreamspell_year_bearer(y0)
    off = dreamspell_day_offset(m, d)
    return (bearer - 1 + off) % 260 + 1


def dreamspell_year_code(y: int) -> int:
    """Код календарного года для ручного расчёта: кин = (код года + код месяца + число) mod 260, 0 → 260.

    Код года = кин 1 января − 1. Каждый следующий год +105, цикл 52 года.
    """
    return (dreamspell_kin(y, 1, 1) - 1) % 260


def _ru_signature(tone: int, seal: int) -> str:
    s = SEALS[seal]
    gi = _GENDER_IDX[s["g"]]
    color = COLORS[_COLOR_BY_MOD4[seal % 4]]["ru"][gi]
    return f"{color} {TONES[tone]['ru'][gi]} {s['ru']}"


def _en_signature(tone: int, seal: int) -> str:
    return f"{COLORS[_COLOR_BY_MOD4[seal % 4]]['en']} {TONES[tone]['en']} {SEALS[seal]['en']}"


def kin_info(kin: int) -> dict[str, Any]:
    """Краткое описание кина: номер, тон, печать, цвет, названия."""
    if not 1 <= kin <= 260:
        raise ValueError(f"Кин вне диапазона 1–260: {kin}")
    t, s = tone_of(kin), seal_of(kin)
    return {
        "kin": kin, "tone": t, "seal": s, "seal_code": s % 20,
        "color": _COLOR_BY_MOD4[s % 4],
        "name_ru": _ru_signature(t, s), "name_en": _en_signature(t, s),
    }


def oracle(kin: int) -> dict[str, Any]:
    """Оракул судьбы (Destiny / Fifth Force Oracle) для кина.

    * Ведущий (Guide): тот же тон и цвет, печать сдвинута по правилу тона (GUIDE_SHIFT).
    * Аналог (Analog): тот же тон, печать: сумма номеров = 19 (Солнце = 20 ↔ Буря 19 через mod 20).
    * Антипод (Antipode): тот же тон, печать ±10.
    * Оккультный (Occult, скрытый учитель): тон 14 − тон, печать 21 − печать; кин = 261 − кин.
    """
    t, s = tone_of(kin), seal_of(kin)
    shift = GUIDE_SHIFT[t]
    guide = kin_from_tone_seal(t, _wrap20(s + shift))
    analog = kin_from_tone_seal(t, _wrap20(19 - s))
    antipode = kin_from_tone_seal(t, _wrap20(s + 10))
    occult = kin_from_tone_seal(14 - t, _wrap20(21 - s))
    assert occult == 261 - kin
    return {
        "guide": {**kin_info(guide), "role_ru": "Ведущий (ведущая сила, высшее «я»)", "role_en": "Guide",
                  "rule": GUIDE_RULE_TEXT[shift], "self_guided": shift == 0},
        "analog": {**kin_info(analog), "role_ru": "Аналог (поддерживающая сила, партнёр)", "role_en": "Analog",
                   "rule": "тот же тон; печать = 19 − печать (mod 20, 0 → 20): Дракон 1 ↔ Зеркало 18, Буря 19 ↔ Солнце 20"},
        "antipode": {**kin_info(antipode), "role_ru": "Антипод (сила вызова, испытания и укрепления)",
                     "role_en": "Antipode", "rule": "тот же тон; печать ±10"},
        "occult": {**kin_info(occult), "role_ru": "Оккультный (скрытый учитель, скрытая сила)", "role_en": "Occult",
                   "rule": "тон = 14 − тон, печать = 21 − печать; кин = 261 − кин"},
    }


def wavespell(kin: int) -> dict[str, Any]:
    """Волновой модуль (13 кинов). Назван по печати первого кина модуля."""
    w = (kin - 1) // 13 + 1
    first = 13 * (w - 1) + 1
    s = seal_of(first)
    color = _COLOR_BY_MOD4[s % 4]
    return {
        "number": w, "first_kin": first, "last_kin": first + 12, "position": tone_of(kin),
        "seal": s, "color": color,
        "name_ru": f"{COLORS[color]['ru'][0]} Волновой Модуль {SEALS[s]['gen']}",
        "name_en": f"{COLORS[color]['en']} {SEALS[s]['en']} Wavespell",
    }


def castle(kin: int) -> dict[str, Any]:
    """Замок (52 кина = 4 волновых модуля)."""
    c = (kin - 1) // 52 + 1
    return {"number": c, **CASTLES[c]}


def earth_family(seal: int) -> dict[str, Any]:
    """Земная семья: печати с одинаковым остатком по модулю 5."""
    fam = EARTH_FAMILIES[seal % 5]
    return {**fam, "seals_ru": [SEALS[x]["ru"] for x in fam["seals"]]}


def thirteen_moon_date(y: int, m: int, d: int) -> dict[str, Any]:
    """Дата календаря 13 Лун: луна 1–13 и день 1–28, День вне времени (25.07) или 0.0 Хунаб Ку (29.02)."""
    _validate_gregorian(y, m, d)
    y0 = dreamspell_year_start(y, m, d)
    bearer = dreamspell_year_bearer(y0)
    # Нумерация «Нового Сириуса»: NS1.0 = 1987–1988 (Planetary Kin Report: «NS1.34 / 2021-2022»).
    # Для лет до 1987 принятая запись не подтверждена — не выдаём.
    ns = None
    if y0 >= DS_ANCHOR_YEAR:
        ns = f"NS{1 + (y0 - DS_ANCHOR_YEAR) // 52}.{(y0 - DS_ANCHOR_YEAR) % 52}"
    out: dict[str, Any] = {
        "year_start": y0, "year_span": f"26.07.{y0} — 25.07.{y0 + 1}",
        "year_bearer": kin_info(bearer), "ns": ns,
        "is_day_out_of_time": False, "is_hunab_ku": False,
    }
    if m == 2 and d == 29:
        out.update(is_hunab_ku=True, moon=None, day=None, plasma=None,
                   label_ru="0.0 Хунаб Ку (вне лун и недель; между 22 и 23 днём Галактической Луны)")
        return out
    off = dreamspell_day_offset(m, d)
    if off == 364:
        out.update(is_day_out_of_time=True, moon=None, day=None, plasma=None,
                   label_ru="День вне времени (25 июля)")
        return out
    moon, day = off // 28 + 1, off % 28 + 1
    pl = PLASMAS[(day - 1) % 7]
    out.update(moon=moon, day=day, moon_name_ru=MOONS[moon]["ru"], moon_name_en=MOONS[moon]["en"],
               plasma={"ru": pl[0], "en": pl[1], "index": (day - 1) % 7 + 1},
               label_ru=f"{MOONS[moon]['ru']}, день {day} ({moon}.{day}), плазма {pl[0]}")
    return out


#: Инфинитивы действий печатей для аффирмации (массив poemseal официального виджета).
_SEAL_VERB_EN: dict[int, str] = {
    1: "Nurture", 2: "Communicate", 3: "Dream", 4: "Target", 5: "Survive", 6: "Equalize", 7: "Know",
    8: "Beautify", 9: "Purify", 10: "Love", 11: "Play", 12: "Influence", 13: "Explore", 14: "Enchant",
    15: "Create", 16: "Question", 17: "Evolve", 18: "Reflect", 19: "Catalyze", 20: "Enlighten",
}


def affirmation_en(kin: int) -> list[str]:
    """Официальная английская «галактическая аффирмация» (шаблон виджета lawoftime.org/decode)."""
    t, s = tone_of(kin), seal_of(kin)
    tone, seal = TONES[t], SEALS[s]
    action_ing = {"Unify": "Attracting", "Polarize": "Stabilizing", "Activate": "Bonding", "Define": "Measuring",
                  "Empower": "Commanding", "Organize": "Balancing", "Channel": "Inspiring", "Harmonize": "Modeling",
                  "Pulse": "Realizing", "Perfect": "Producing", "Dissolve": "Releasing",
                  "Dedicate": "Universalizing", "Endure": "Transcending"}[tone["power"][1]]
    shift = GUIDE_SHIFT[t]
    lines = [
        f"I {tone['power'][1]} in order to {_SEAL_VERB_EN[s]}",
        f"{action_ing} {seal['essence'][1]}",
        f"I seal the {seal['block'][1]} of {seal['power'][1]}",
        f"With the {tone['en']} tone of {tone['essence'][1]}",
        "I am guided by my own power doubled" if shift == 0
        else f"I am guided by the power of {SEALS[_wrap20(s + shift)]['power'][1]}",
    ]
    if kin in GAP_KINS:
        lines.append("I am a galactic activation portal, enter me")
    return lines


#: Правила для 29 февраля в Dreamspell (опция ``feb29_rule``).
FEB29_RULES = ("noon", "feb28", "mar1")


def feb29_kin_date(rule: str = "noon", hour: int | None = None, minute: int | None = None) -> dict[str, Any]:
    """По какой дате брать кин для рождения 29 февраля.

    * ``noon`` (по умолчанию) — официальное указание Фонда Закона Времени (lawoftime.org/decode):
      «If you were born on February 29 before noon local time, use February 28. If you were born after
      noon local time, use March 1». Время неизвестно → 28.02 (как сам виджет и 13moon.com) + предупреждение.
      Ровно 12:00 считается «после полудня» (граница, тоже с предупреждением).
    * ``feb28`` — всегда 28.02 (поведение JS-виджета lawoftime.org/decode и калькулятора 13moon.com).
    * ``mar1`` — всегда 1 марта.

    Возвращает ``{"use": "feb28"|"mar1", "kin_date": (м, д), "time_known": bool, "after_noon": bool|None}``.
    """
    if rule not in FEB29_RULES:
        raise ValueError(f"feb29_rule: одно из {FEB29_RULES}")
    time_known = hour is not None
    after_noon = (hour * 60 + (minute or 0)) >= 720 if time_known else None
    if rule == "feb28":
        use = "feb28"
    elif rule == "mar1":
        use = "mar1"
    else:
        use = "mar1" if after_noon else "feb28"
    return {"use": use, "kin_date": (3, 1) if use == "mar1" else (2, 28),
            "time_known": time_known, "after_noon": after_noon}


def dreamspell(y: int, m: int, d: int, kin_date: tuple[int, int] | None = None) -> dict[str, Any]:
    """Полный расчёт Dreamspell для григорианской даты.

    ``kin_date`` — (месяц, день), по которым считать кин, если он отличается от самой даты
    (только для 29.02: (2, 28) или (3, 1), см. ``feb29_kin_date``). Дата «13 Лун» всегда по самой дате.
    """
    km, kd = kin_date if kin_date else (m, d)
    kin = dreamspell_kin(y, km, kd)
    t, s = tone_of(kin), seal_of(kin)
    color = _COLOR_BY_MOD4[s % 4]
    seal, tone = SEALS[s], TONES[t]
    return {
        **kin_info(kin),
        "tone_info": {"number": t, "name_ru": tone["ru"][0], "name_en": tone["en"], "maya": tone["maya"],
                      "power": tone["power"], "action": tone["action"], "essence": tone["essence"]},
        "seal_info": {"number": s, "code": s % 20, "name_ru": seal["ru"], "name_en": seal["en"],
                      "yucatec": seal["yucatec"], "power": seal["power"], "action": seal["action"],
                      "essence": seal["essence"]},
        "color_info": {"key": color, "name_ru": COLORS[color]["ru"][0], "name_en": COLORS[color]["en"],
                       "direction_ru": COLORS[color]["direction_ru"], "action_ru": COLORS[color]["action_ru"]},
        "oracle": oracle(kin),
        "wavespell": wavespell(kin),
        "castle": castle(kin),
        "earth_family": earth_family(s),
        "is_gap": kin in GAP_KINS,
        "is_polar_kin": kin in POLAR_KINS,
        "thirteen_moon": thirteen_moon_date(y, m, d),
        "affirmation_en": affirmation_en(kin),
        "year_code": dreamspell_year_code(y),
        "month_code": DS_MONTH_CODES[km],
    }


# ---------------------------------------------------------------------------
# Классический счёт
# ---------------------------------------------------------------------------


def long_count_to_days(baktun: int, katun: int, tun: int, winal: int, kin: int) -> int:
    """Число дней от 13.0.0.0.0 (0.0.0.0.0) для записи Длинного счёта."""
    return baktun * 144000 + katun * 7200 + tun * 360 + winal * 20 + kin


def days_to_long_count(x: int) -> tuple[int, int, int, int, int]:
    """Дни от начала эры -> (бактун, катун, тун, виналь, кин). Для x ≥ 0."""
    b, r = divmod(x, 144000)
    k, r = divmod(r, 7200)
    t, r = divmod(r, 360)
    w, q = divmod(r, 20)
    return b, k, t, w, q


def classic_from_jdn(jdn: int, correlation: int = GMT_CORRELATION) -> dict[str, Any]:
    """Классический календарный круг и Длинный счёт по юлианскому дню."""
    x = jdn - correlation
    number = (x + 3) % 13 + 1                 # 0-й день эры = 4 Ajaw
    name_idx = (x + 19) % 20 + 1              # 0-й день эры = Ajaw (20)
    h = (x + _HAAB_EPOCH_POS) % 365           # 0-й день эры = 8 Kumkʼu
    hm, hd = divmod(h, 20)
    dn = DAY_NAMES[name_idx]
    month = HAAB_MONTHS[hm]
    out: dict[str, Any] = {
        "correlation": correlation, "jdn": jdn, "days_since_era": x,
        "tzolkin": {
            "number": number, "day_index": name_idx, "day_name": dn["name"], "day_name_landa": dn["landa"],
            "day_name_kiche": dn["kiche"], "day_name_ru": dn["ru"],
            "index_260": kin_from_tone_seal(number, name_idx),
            "label": f"{number} {dn['name']}", "label_kiche": f"{number} {dn['kiche']}",
        },
        "haab": {"day": hd, "month_index": hm, "month": month["name"], "month_ru": month["ru"],
                 "label": f"{hd} {month['name']}"},
    }
    out["calendar_round"] = f"{out['tzolkin']['label']} {out['haab']['label']}"
    if x >= 0:
        lc = days_to_long_count(x)
        out["long_count"] = ".".join(str(v) for v in lc)
        out["long_count_digits"] = list(lc)
    else:
        out["long_count"] = None
        out["long_count_digits"] = None
    return out


def classic(y: int, m: int, d: int, correlation: int = GMT_CORRELATION, calendar: str = "gregorian") -> dict[str, Any]:
    """Классический счёт для даты (по умолчанию григорианской)."""
    jdn = julian_to_jdn(y, m, d) if calendar == "julian" else gregorian_to_jdn(y, m, d)
    return classic_from_jdn(jdn, correlation)


def _resolve_correlation(value: Any) -> int:
    if value is None:
        return GMT_CORRELATION
    if isinstance(value, int):
        return value
    key = str(value).strip().lower()
    if key in NAMED_CORRELATIONS:
        return NAMED_CORRELATIONS[key]
    try:
        return int(key)
    except ValueError as e:
        raise ValueError(f"Неизвестная корреляция: {value!r}") from e


# ---------------------------------------------------------------------------
# Публичный API
# ---------------------------------------------------------------------------


def calculate(b: BirthInput, **options: Any) -> dict[str, Any]:
    """Цолькин по дате рождения: Dreamspell (по умолчанию) + классический счёт майя.

    Опции:
      * ``correlation`` — корреляция для классического счёта: 584283 (по умолчанию, GMT),
        584285 / "lounsbury" (GMT+2) или любое целое.
      * ``input_calendar`` — "gregorian" (по умолчанию) или "julian" (для исторических дат;
        Dreamspell тогда считается по пересчитанной григорианской дате).
      * ``primary`` — "dreamspell" (по умолчанию) или "classic": какая система идёт в сводку первой.
      * ``feb29_rule`` — только для рождения 29 февраля в Dreamspell: "noon" (по умолчанию, официальное
        правило Фонда: до полудня → кин 28.02, после полудня → кин 01.03), "feb28" (всегда 28.02, как
        виджет lawoftime.org/decode и 13moon.com) или "mar1".
    """
    correlation = _resolve_correlation(options.get("correlation"))
    input_calendar = str(options.get("input_calendar", "gregorian")).lower()
    if input_calendar not in ("gregorian", "julian"):
        raise ValueError("input_calendar: 'gregorian' или 'julian'")
    primary = str(options.get("primary", "dreamspell")).lower()
    if primary not in ("dreamspell", "classic"):
        raise ValueError("primary: 'dreamspell' или 'classic'")
    feb29_rule = str(options.get("feb29_rule", "noon")).lower()
    if feb29_rule not in FEB29_RULES:
        raise ValueError(f"feb29_rule: одно из {FEB29_RULES}")

    warnings: list[str] = []
    steps: list[str] = []

    if input_calendar == "julian":
        jdn = julian_to_jdn(b.year, b.month, b.day)
        gy, gm, gd = jdn_to_gregorian(jdn)
        steps.append(f"Юлианская дата {b.day:02d}.{b.month:02d}.{b.year} → JDN {jdn} → "
                     f"григорианская {gd:02d}.{gm:02d}.{gy}.")
    else:
        _validate_gregorian(b.year, b.month, b.day)
        gy, gm, gd = b.year, b.month, b.day
        jdn = gregorian_to_jdn(gy, gm, gd)

    is_feb29 = (gm, gd) == (2, 29)
    if b.has_time and not is_feb29:
        warnings.append("Время рождения не используется: день цолькина определяется гражданской датой "
                        "(местная полночь — граница дня). При рождении около полуночи проверьте дату.")
    if gy < 1582 or (gy == 1582 and (gm, gd) < (10, 15)):
        warnings.append("Дата раньше введения григорианского календаря (15.10.1582): Dreamspell посчитан по "
                        "пролептическому григорианскому календарю — это экстраполяция, а не практика системы.")

    # --- Dreamspell ---
    feb29: dict[str, Any] | None = None
    kin_m, kin_d = gm, gd
    if is_feb29:
        f = feb29_kin_date(feb29_rule, b.hour, b.minute)
        kin_m, kin_d = f["kin_date"]
        k28, k01 = dreamspell_kin(gy, 2, 28), dreamspell_kin(gy, 3, 1)
        feb29 = {"rule": feb29_rule, "used": f["use"], "time_known": f["time_known"],
                 "after_noon": f["after_noon"], "kin_if_before_noon": k28, "kin_if_after_noon": k01,
                 "source": "lawoftime.org/decode: до полудня местного времени — 28.02, после полудня — 01.03"}
    ds = dreamspell(gy, gm, gd, kin_date=(kin_m, kin_d))
    if feb29 is not None:
        ds["feb29"] = feb29
    tm = ds["thirteen_moon"]
    y0 = tm["year_start"]
    off = dreamspell_day_offset(kin_m, kin_d)
    if is_feb29:
        used_txt = "28 февраля" if feb29["used"] == "feb28" else "1 марта"
        if feb29_rule == "noon" and not feb29["time_known"]:
            why = ("время рождения неизвестно, поэтому взят кин 28.02 (так считают виджет lawoftime.org/decode "
                   f"и 13moon.com); если рождение было после полудня — Кин {feb29['kin_if_after_noon']} (01.03)")
        elif feb29_rule == "noon":
            why = (f"рождение {'после' if feb29['after_noon'] else 'до'} полудня местного времени → кин {used_txt}"
                   + (" (ровно 12:00 — граница, считаем «после полудня»; проверьте время)"
                      if (b.hour, b.minute or 0) == (12, 0) else ""))
        else:
            why = f"по опции feb29_rule='{feb29_rule}' взят кин {used_txt}"
        warnings.append("29 февраля = «0.0 Хунаб Ку»: в 13-лунном календаре этот день вне лун и недель и своего "
                        "кина не имеет. Официальное правило Фонда Закона Времени: до полудня местного времени — "
                        f"кин 28.02 (Кин {feb29['kin_if_before_noon']}), после полудня — кин 01.03 "
                        f"(Кин {feb29['kin_if_after_noon']}). Здесь: {why}. "
                        "Классический счёт майя 29 февраля считает обычным днём.")
    if tm["is_day_out_of_time"]:
        warnings.append("25 июля — «День вне времени»: вне лун и недель, но собственный кин у дня есть.")

    steps.append("Dreamspell (13 Лун): якорь 26.07.1987 = Кин 34; каждый год 26 июля кин сдвигается на "
                 "+105 (365 mod 260); 29 февраля не считается.")
    steps.append(f"13-лунный год для {gd:02d}.{gm:02d}.{gy} начался 26.07.{y0} "
                 f"({'дата не раньше 26 июля' if (gm, gd) >= (7, 26) else 'дата раньше 26 июля → предыдущий год'}).")
    bearer = tm["year_bearer"]["kin"]
    raw = DS_ANCHOR_KIN - 1 + DS_YEAR_STEP * (y0 - DS_ANCHOR_YEAR)
    steps.append(f"Кин 26.07.{y0} (Носитель года) = (34 − 1 + 105·({y0} − 1987)) mod 260 + 1 = "
                 f"({raw}) mod 260 + 1 = {bearer} — {tm['year_bearer']['name_ru']}.")
    steps.append(f"Дней от 26.07.{y0} до даты (без 29 февраля) = {off}"
                 + ((" (29.02 приравнено к 28.02)" if kin_m == 2 else " (29.02 приравнено к 01.03)")
                    if is_feb29 else "") + ".")
    steps.append(f"Кин = ({bearer} − 1 + {off}) mod 260 + 1 = {ds['kin']}.")
    yc, mc = ds["year_code"], ds["month_code"]
    dd = kin_d
    s = (yc + mc + dd) % 260
    steps.append(f"Проверка по таблице кодов: код года {gy} = {yc}, код месяца = {mc}, число = {dd}; "
                 f"{yc} + {mc} + {dd} = {yc + mc + dd} → mod 260 = {s if s else 260}.")
    steps.append(f"Тон = {ds['kin']} mod 13 → {ds['tone']} ({TONES[ds['tone']]['ru'][0]}); "
                 f"печать = {ds['kin']} mod 20 → {ds['seal']} ({SEALS[ds['seal']]['ru']}); "
                 f"цвет по печати (mod 4) — {ds['color_info']['name_ru']}. Итог: Кин {ds['kin']}, {ds['name_ru']}.")
    o = ds["oracle"]
    steps.append(f"Оракул: Ведущий — {o['guide']['rule']} → Кин {o['guide']['kin']} {o['guide']['name_ru']}; "
                 f"Аналог (19 − печать) → Кин {o['analog']['kin']} {o['analog']['name_ru']}; "
                 f"Антипод (печать ± 10) → Кин {o['antipode']['kin']} {o['antipode']['name_ru']}; "
                 f"Оккультный (261 − кин) → Кин {o['occult']['kin']} {o['occult']['name_ru']}.")
    w = ds["wavespell"]
    steps.append(f"Волновой модуль № {w['number']} (кины {w['first_kin']}–{w['last_kin']}): {w['name_ru']}, "
                 f"позиция {w['position']}; замок № {ds['castle']['number']}: {ds['castle']['ru']} "
                 f"({ds['castle']['court_ru']}); "
                 f"земная семья: {ds['earth_family']['ru']}; ПГА: {'да' if ds['is_gap'] else 'нет'}.")
    steps.append(f"Дата 13 Лун: {tm['label_ru']}; год {tm['year_span']}"
                 + (f" ({tm['ns']})." if tm["ns"] else "."))

    # --- Классический счёт ---
    cl = classic_from_jdn(jdn, correlation)
    x = cl["days_since_era"]
    steps.append(f"Классический счёт: JDN({gd:02d}.{gm:02d}.{gy}) = {jdn}; дней от 13.0.0.0.0 = "
                 f"{jdn} − {correlation} = {x}.")
    if cl["long_count"]:
        steps.append(f"Длинный счёт: {x} = {cl['long_count_digits'][0]}·144000 + {cl['long_count_digits'][1]}·7200 + "
                     f"{cl['long_count_digits'][2]}·360 + {cl['long_count_digits'][3]}·20 + {cl['long_count_digits'][4]} "
                     f"→ {cl['long_count']}.")
    tz = cl["tzolkin"]
    hb = cl["haab"]
    steps.append(f"Цолькин: число = ({x} + 3) mod 13 + 1 = {tz['number']}; имя = ({x} + 19) mod 20 + 1 = "
                 f"{tz['day_index']} ({tz['day_name']}, кʼиче {tz['day_name_kiche']}) → {tz['label']}.")
    steps.append(f"Хааб: ({x} + 348) mod 365 = {hb['month_index'] * 20 + hb['day']} → месяц {hb['month_index']} "
                 f"({hb['month']}), день {hb['day']} → {hb['label']}.")
    if correlation == GMT_CORRELATION:
        alt = classic_from_jdn(jdn, LOUNSBURY_CORRELATION)
        cl["variant_584285"] = {"calendar_round": alt["calendar_round"], "long_count": alt["long_count"],
                                "index_260": alt["tzolkin"]["index_260"]}
        steps.append(f"Вариант корреляции 584285 (GMT+2): {alt['calendar_round']} — на 2 дня «раньше» по счёту майя.")

    shift = (tz["index_260"] - ds["kin"]) % 260
    comparison = {
        "dreamspell_kin": ds["kin"], "classic_index_260": tz["index_260"],
        "same": ds["kin"] == tz["index_260"], "classic_minus_dreamspell_mod260": shift,
        "note_ru": ("Dreamspell и классический счёт — разные отсчёты: Dreamspell пропускает 29 февраля и "
                    "привязан к якорю Аргуэльеса, классический счёт непрерывен со времён майя. Сдвиг между "
                    "ними растёт на 1 после каждого 29 февраля."),
    }
    steps.append(f"Сравнение: Dreamspell Кин {ds['kin']} ↔ классический индекс {tz['index_260']} "
                 f"({tz['label']}); разность {shift} (mod 260).")

    ds_summary = f"Кин {ds['kin']} — {ds['name_ru']} ({ds['name_en']})"
    cl_summary = (f"{tz['label']} (кʼиче: {tz['label_kiche']}; рус. {tz['number']} {tz['day_name_ru']}), "
                  f"Хааб {hb['label']}" + (f", Длинный счёт {cl['long_count']}" if cl["long_count"] else "")
                  + f" — корреляция {correlation}")

    return {
        "method": METHOD,
        "variant": f"{primary}: Dreamspell (Foundation for the Law of Time) + классический счёт (корреляция {correlation})",
        "default_system": primary,
        "inputs_used": {
            "date": f"{b.year:04d}-{b.month:02d}-{b.day:02d}", "input_calendar": input_calendar,
            "gregorian_date": f"{gy:04d}-{gm:02d}-{gd:02d}", "jdn": jdn,
            "time_used": bool(is_feb29 and feb29_rule == "noon" and b.has_time),
            "place_used": False, "correlation": correlation,
            "feb29_rule": feb29_rule if is_feb29 else None,
        },
        "warnings": warnings,
        "summary": {"primary": ds_summary if primary == "dreamspell" else cl_summary,
                    "dreamspell": ds_summary, "classic": cl_summary},
        "dreamspell": ds,
        "classic": cl,
        "comparison": comparison,
        "steps": steps,
    }


def dreamspell_year_code_table(first_year: int = 1910, last_year: int = 2065) -> dict[int, int]:
    """Таблица кодов календарных лет для ручного расчёта (цикл 52 года)."""
    return {y: dreamspell_year_code(y) for y in range(first_year, last_year + 1)}
