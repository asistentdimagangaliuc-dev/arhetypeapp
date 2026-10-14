"""Генные ключи (Gene Keys, Ричард Радд) — Гологенетический профиль (Hologenetic Profile).

Профиль строится на той же астрономии, что и Дизайн Человека (Human Design):

* «Личность» (Personality, натальный, сознательный) — момент рождения;
* «Дизайн» (Design, пренатальный, бессознательный) — момент, когда тропическая
  долгота Солнца была на 88° дуги меньше, чем в момент рождения (≈ 88–92 дня до рождения);
* эклиптика делится на 64 сектора по 5°37′30″ (= 5.625°) — колесо гексаграмм / Генных
  ключей; ключ 41 начинается в 302°00′ тропической долготы (2°00′ Водолея), далее
  порядок «колеса Равы» (GATE_ORDER); каждый ключ делится на 6 линий по 0.9375°.

Соответствие сфер и планет взято со страницы официальной документации
https://genekeys.com/docs/what-planets-does-each-sphere-of-the-golden-path-profile-correlate-to/
(обновлено 15.12.2024) и проверено вычислением на четырёх опубликованных профилях
(см. calculators/tests/test_gene_keys.py и knowledge-base/05-gene-keys.md).

Этот модуль намеренно НЕ импортирует calculators.human_design: поиск ключа/линии
реализован независимо, чтобы два модуля можно было сверять друг с другом.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

from .common import ephemeris as eph
from .common.time import BirthInput, fmt_offset, jd_to_utc, julian_day_ut, normalize

# ---------------------------------------------------------------------------
# Колесо 64 ключей
# ---------------------------------------------------------------------------

#: Тропическая долгота начала ключа 41 (2°00′ Водолея) — начало колеса.
WHEEL_START_DEG: float = 302.0
#: Дуга одного ключа (360/64) и одной линии (ключ/6), градусы.
KEY_ARC: float = 360.0 / 64.0          # 5.625°  = 5°37′30″
LINE_ARC: float = KEY_ARC / 6.0        # 0.9375° = 0°56′15″
#: Солнечная дуга между Дизайном и рождением (как в Human Design).
DESIGN_ARC_DEG: float = 88.0

#: Порядок ключей по эклиптике, начиная с 302° (ключ 41) по возрастанию долготы.
GATE_ORDER: list[int] = [
    41, 19, 13, 49, 30, 55, 37, 63, 22, 36, 25, 17, 21, 51, 42, 3,
    27, 24, 2, 23, 8, 20, 16, 35, 45, 12, 15, 52, 39, 53, 62, 56,
    31, 33, 7, 4, 29, 59, 40, 64, 47, 6, 46, 18, 48, 57, 32, 50,
    28, 44, 1, 43, 14, 34, 9, 5, 26, 11, 10, 58, 38, 54, 61, 60,
]
_INDEX_OF_KEY: dict[int, int] = {k: i for i, k in enumerate(GATE_ORDER)}

# ---------------------------------------------------------------------------
# Справочник 64 ключей: Тень / Дар / Сиддхи (EN — оригинал Р. Радда;
# RU — официальный перевод: Р. Радд «Генные ключи», пер. М. Хандий, Д. Буркацкий,
# СПб.: Биверсум, 2013, ISBN 978-5-9904337-2-4 — оглавление и заголовки глав).
# ---------------------------------------------------------------------------

KEYS: dict[int, dict[str, tuple[str, str]]] = {
    1: {"shadow": ("Entropy", "Энтропия"), "gift": ("Freshness", "Свежесть"), "siddhi": ("Beauty", "Красота")},
    2: {"shadow": ("Dislocation", "Потерянность"), "gift": ("Orientation", "Ориентация"), "siddhi": ("Unity", "Единство")},
    3: {"shadow": ("Chaos", "Хаос"), "gift": ("Innovation", "Новаторство"), "siddhi": ("Innocence", "Невинность")},
    4: {"shadow": ("Intolerance", "Нетерпимость"), "gift": ("Understanding", "Понимание"), "siddhi": ("Forgiveness", "Прощение")},
    5: {"shadow": ("Impatience", "Нетерпение"), "gift": ("Patience", "Терпение"), "siddhi": ("Timelessness", "Безвременье")},
    6: {"shadow": ("Conflict", "Конфликт"), "gift": ("Diplomacy", "Дипломатия"), "siddhi": ("Peace", "Мир")},
    7: {"shadow": ("Division", "Разделение"), "gift": ("Guidance", "Руководство"), "siddhi": ("Virtue", "Добродетель")},
    8: {"shadow": ("Mediocrity", "Посредственность"), "gift": ("Style", "Стиль"), "siddhi": ("Exquisiteness", "Изысканность")},
    9: {"shadow": ("Inertia", "Инертность"), "gift": ("Determination", "Целеустремлённость"), "siddhi": ("Invincibility", "Непобедимость")},
    10: {"shadow": ("Self-Obsession", "Самоодержимость"), "gift": ("Naturalness", "Естественность"), "siddhi": ("Being", "Бытие")},
    11: {"shadow": ("Obscurity", "Затемнение"), "gift": ("Idealism", "Идеализм"), "siddhi": ("Light", "Свет")},
    12: {"shadow": ("Vanity", "Тщеславие"), "gift": ("Discrimination", "Проницательность"), "siddhi": ("Purity", "Чистота")},
    13: {"shadow": ("Discord", "Диссонанс"), "gift": ("Discernment", "Распознавание"), "siddhi": ("Empathy", "Эмпатия")},
    14: {"shadow": ("Compromise", "Компромисс"), "gift": ("Competence", "Компетентность"), "siddhi": ("Bounteousness", "Щедрость")},
    15: {"shadow": ("Dullness", "Серость"), "gift": ("Magnetism", "Магнетизм"), "siddhi": ("Florescence", "Цветение")},
    16: {"shadow": ("Indifference", "Безразличие"), "gift": ("Versatility", "Многогранность"), "siddhi": ("Mastery", "Мастерство")},
    17: {"shadow": ("Opinion", "Мнительность"), "gift": ("Far-Sightedness", "Дальновидность"), "siddhi": ("Omniscience", "Всеведение")},
    18: {"shadow": ("Judgement", "Суждение"), "gift": ("Integrity", "Целостность"), "siddhi": ("Perfection", "Совершенство")},
    19: {"shadow": ("Co-Dependence", "Созависимость"), "gift": ("Sensitivity", "Чувствительность"), "siddhi": ("Sacrifice", "Жертвенность")},
    20: {"shadow": ("Superficiality", "Поверхностность"), "gift": ("Self-Assurance", "Уверенность в себе"), "siddhi": ("Presence", "Присутствие")},
    21: {"shadow": ("Control", "Контроль"), "gift": ("Authority", "Авторитетность"), "siddhi": ("Valour", "Доблесть")},
    22: {"shadow": ("Dishonour", "Бесчестие"), "gift": ("Graciousness", "Благосклонность"), "siddhi": ("Grace", "Благодать")},
    23: {"shadow": ("Complexity", "Сложность"), "gift": ("Simplicity", "Простота"), "siddhi": ("Quintessence", "Квинтэссенция")},
    24: {"shadow": ("Addiction", "Зависимость"), "gift": ("Invention", "Изобретательность"), "siddhi": ("Silence", "Тишина")},
    25: {"shadow": ("Constriction", "Ограниченность"), "gift": ("Acceptance", "Принятие"), "siddhi": ("Universal Love", "Универсальная любовь")},
    26: {"shadow": ("Pride", "Гордыня"), "gift": ("Artfulness", "Ловкость"), "siddhi": ("Invisibility", "Невидимость")},
    27: {"shadow": ("Selfishness", "Эгоизм"), "gift": ("Altruism", "Альтруизм"), "siddhi": ("Selflessness", "Самоотверженность")},
    28: {"shadow": ("Purposelessness", "Бесцельность"), "gift": ("Totality", "Тотальность"), "siddhi": ("Immortality", "Бессмертие")},
    29: {"shadow": ("Half-Heartedness", "Нерешительность"), "gift": ("Commitment", "Обязательство"), "siddhi": ("Devotion", "Преданность")},
    30: {"shadow": ("Desire", "Желание"), "gift": ("Lightness", "Лёгкость"), "siddhi": ("Rapture", "Восторг")},
    31: {"shadow": ("Arrogance", "Высокомерие"), "gift": ("Leadership", "Лидерство"), "siddhi": ("Humility", "Смирение")},
    32: {"shadow": ("Failure", "Неудача"), "gift": ("Preservation", "Сохранение"), "siddhi": ("Veneration", "Благоговение")},
    33: {"shadow": ("Forgetting", "Забвение"), "gift": ("Mindfulness", "Осознавание"), "siddhi": ("Revelation", "Откровение")},
    34: {"shadow": ("Force", "Форсирование"), "gift": ("Strength", "Сила"), "siddhi": ("Majesty", "Величие")},
    35: {"shadow": ("Hunger", "Голод"), "gift": ("Adventure", "Приключение"), "siddhi": ("Boundlessness", "Безграничность")},
    36: {"shadow": ("Turbulence", "Турбулентность"), "gift": ("Humanity", "Гуманность"), "siddhi": ("Compassion", "Сострадание")},
    37: {"shadow": ("Weakness", "Слабость"), "gift": ("Equality", "Равенство"), "siddhi": ("Tenderness", "Чуткость")},
    38: {"shadow": ("Struggle", "Борьба"), "gift": ("Perseverance", "Стойкость"), "siddhi": ("Honour", "Честь")},
    39: {"shadow": ("Provocation", "Провокация"), "gift": ("Dynamism", "Динамизм"), "siddhi": ("Liberation", "Освобождение")},
    40: {"shadow": ("Exhaustion", "Истощение"), "gift": ("Resolve", "Решимость"), "siddhi": ("Divine Will", "Божественная воля")},
    41: {"shadow": ("Fantasy", "Фантазия"), "gift": ("Anticipation", "Предчувствие"), "siddhi": ("Emanation", "Эманация")},
    42: {"shadow": ("Expectation", "Ожидание"), "gift": ("Detachment", "Отстранённость"), "siddhi": ("Celebration", "Празднование")},
    43: {"shadow": ("Deafness", "Глухота"), "gift": ("Insight", "Озарение"), "siddhi": ("Epiphany", "Прозрение")},
    44: {"shadow": ("Interference", "Помеха"), "gift": ("Teamwork", "Взаимодействие"), "siddhi": ("Synarchy", "Синархия")},
    45: {"shadow": ("Dominance", "Доминирование"), "gift": ("Synergy", "Синергия"), "siddhi": ("Communion", "Причастие")},
    46: {"shadow": ("Seriousness", "Серьёзность"), "gift": ("Delight", "Удовольствие"), "siddhi": ("Ecstasy", "Экстаз")},
    47: {"shadow": ("Oppression", "Подавление"), "gift": ("Transmutation", "Трансмутация"), "siddhi": ("Transfiguration", "Преображение")},
    48: {"shadow": ("Inadequacy", "Неадекватность"), "gift": ("Resourcefulness", "Находчивость"), "siddhi": ("Wisdom", "Мудрость")},
    49: {"shadow": ("Reaction", "Реакция"), "gift": ("Revolution", "Революция"), "siddhi": ("Rebirth", "Возрождение")},
    50: {"shadow": ("Corruption", "Коррупция"), "gift": ("Equilibrium", "Равновесие"), "siddhi": ("Harmony", "Гармония")},
    51: {"shadow": ("Agitation", "Возбуждение"), "gift": ("Initiative", "Инициатива"), "siddhi": ("Awakening", "Пробуждение")},
    52: {"shadow": ("Stress", "Стресс"), "gift": ("Restraint", "Сдержанность"), "siddhi": ("Stillness", "Неподвижность")},
    53: {"shadow": ("Immaturity", "Незрелость"), "gift": ("Expansion", "Расширение"), "siddhi": ("Superabundance", "Сверхизобилие")},
    54: {"shadow": ("Greed", "Жадность"), "gift": ("Aspiration", "Стремление"), "siddhi": ("Ascension", "Восхождение")},
    55: {"shadow": ("Victimisation", "Преследование"), "gift": ("Freedom", "Свобода"), "siddhi": ("Freedom", "Свобода")},
    56: {"shadow": ("Distraction", "Отвлечение"), "gift": ("Enrichment", "Обогащение"), "siddhi": ("Intoxication", "Интоксикация")},
    57: {"shadow": ("Unease", "Тревожность"), "gift": ("Intuition", "Интуиция"), "siddhi": ("Clarity", "Ясность")},
    58: {"shadow": ("Dissatisfaction", "Неудовлетворённость"), "gift": ("Vitality", "Жизненность"), "siddhi": ("Bliss", "Блаженство")},
    59: {"shadow": ("Dishonesty", "Нечестность"), "gift": ("Intimacy", "Близость"), "siddhi": ("Transparency", "Прозрачность")},
    60: {"shadow": ("Limitation", "Ограничение"), "gift": ("Realism", "Реализм"), "siddhi": ("Justice", "Справедливость")},
    61: {"shadow": ("Psychosis", "Психоз"), "gift": ("Inspiration", "Вдохновение"), "siddhi": ("Sanctity", "Святость")},
    62: {"shadow": ("Intellect", "Интеллект"), "gift": ("Precision", "Точность"), "siddhi": ("Impeccability", "Безупречность")},
    63: {"shadow": ("Doubt", "Сомнение"), "gift": ("Inquiry", "Расследование"), "siddhi": ("Truth", "Истина")},
    64: {"shadow": ("Confusion", "Замешательство"), "gift": ("Imagination", "Воображение"), "siddhi": ("Illumination", "Просветление")},
}

# ---------------------------------------------------------------------------
# Кодоновые кольца (21) и аминокислоты — по заголовкам глав русского издания 2013 г.
# Состав колец согласуется со стандартным генетическим кодом (6/4/3/2/1 кодонов).
# ---------------------------------------------------------------------------

CODON_RINGS: list[dict] = [
    {"en": "Ring of Fire", "ru": "Кольцо Огня", "amino_en": "Lysine", "amino_ru": "Лизин", "keys": [1, 14]},
    {"en": "Ring of Water", "ru": "Кольцо Воды", "amino_en": "Phenylalanine", "amino_ru": "Фенилаланин", "keys": [2, 8]},
    {"en": "Ring of Life and Death", "ru": "Кольцо Жизни и Смерти", "amino_en": "Leucine", "amino_ru": "Лейцин",
     "keys": [3, 20, 23, 24, 27, 42]},
    {"en": "Ring of Union", "ru": "Кольцо Союза (в изд. 2013 также «Кольцо Единства»)", "amino_en": "Valine",
     "amino_ru": "Валин", "keys": [4, 7, 29, 59]},
    {"en": "Ring of Light", "ru": "Кольцо Света", "amino_en": "Threonine", "amino_ru": "Треонин", "keys": [5, 9, 11, 26]},
    {"en": "Ring of Alchemy", "ru": "Кольцо Алхимии", "amino_en": "Glycine", "amino_ru": "Глицин", "keys": [6, 40, 47, 64]},
    {"en": "Ring of Humanity", "ru": "Кольцо Человечества", "amino_en": "Arginine", "amino_ru": "Аргинин",
     "keys": [10, 17, 21, 25, 38, 51]},
    {"en": "Ring of Trials", "ru": "Кольцо Испытаний", "amino_en": "none (stop codons)",
     "amino_ru": "нет (стоп-кодоны)", "keys": [12, 33, 56]},
    {"en": "Ring of Purification", "ru": "Кольцо Очищения", "amino_en": "Glutamine", "amino_ru": "Глутамин", "keys": [13, 30]},
    {"en": "Ring of Seeking", "ru": "Кольцо Поиска", "amino_en": "Serine", "amino_ru": "Серин",
     "keys": [15, 39, 52, 53, 54, 58]},
    {"en": "Ring of Prosperity", "ru": "Кольцо Преуспевания", "amino_en": "Cysteine", "amino_ru": "Цистеин", "keys": [16, 45]},
    {"en": "Ring of Matter", "ru": "Кольцо Материи", "amino_en": "Alanine", "amino_ru": "Аланин", "keys": [18, 46, 48, 57]},
    {"en": "Ring of Gaia", "ru": "Кольцо Геи", "amino_en": "Isoleucine", "amino_ru": "Изолейцин", "keys": [19, 60, 61]},
    {"en": "Ring of Divinity", "ru": "Кольцо Божественности", "amino_en": "Proline", "amino_ru": "Пролин",
     "keys": [22, 36, 37, 63]},
    {"en": "Ring of Destiny", "ru": "Кольцо Судьбы", "amino_en": "Asparagine", "amino_ru": "Аспарагин", "keys": [34, 43]},
    {"en": "Ring of Miracles", "ru": "Кольцо Чудес", "amino_en": "Tryptophan", "amino_ru": "Триптофан", "keys": [35]},
    {"en": "Ring of Illusion", "ru": "Кольцо Иллюзии", "amino_en": "Aspartic acid", "amino_ru": "Аспарагиновая кислота",
     "keys": [28, 32]},
    {"en": "Ring of No Return", "ru": "Кольцо Невозврата", "amino_en": "Tyrosine", "amino_ru": "Тирозин", "keys": [31, 62]},
    {"en": "Ring of Origin", "ru": "Кольцо Источника", "amino_en": "Methionine (start codon)",
     "amino_ru": "Метионин (старт-кодон)", "keys": [41]},
    {"en": "Ring of the Whirlwind", "ru": "Кольцо Вихря", "amino_en": "Histidine", "amino_ru": "Гистидин", "keys": [49, 55]},
    {"en": "Ring of the Illuminati", "ru": "Кольцо Иллюминатов", "amino_en": "Glutamic acid",
     "amino_ru": "Глутаминовая кислота", "keys": [44, 50]},
]
_RING_OF_KEY: dict[int, dict] = {k: r for r in CODON_RINGS for k in r["keys"]}

# ---------------------------------------------------------------------------
# Сферы профиля: (id, RU, EN, последовательность, сторона, тело)
# side: "personality" = натал/сознательное (момент рождения),
#       "design" = пренатал/бессознательное (Солнце на 88° раньше).
# ---------------------------------------------------------------------------

SPHERES: list[dict] = [
    {"id": "lifes_work", "ru": "Дело жизни", "en": "Life's Work", "sequence": "activation",
     "side": "personality", "body": "sun", "lines": "lifes_work"},
    {"id": "evolution", "ru": "Эволюция", "en": "Evolution", "sequence": "activation",
     "side": "personality", "body": "earth", "lines": "evolution"},
    {"id": "radiance", "ru": "Сияние", "en": "Radiance", "sequence": "activation",
     "side": "design", "body": "sun", "lines": "radiance"},
    {"id": "purpose", "ru": "Предназначение", "en": "Purpose", "sequence": "activation",
     "side": "design", "body": "earth", "lines": "purpose_activation", "lines_venus": "purpose_venus"},
    {"id": "attraction", "ru": "Притяжение", "en": "Attraction", "sequence": "venus",
     "side": "design", "body": "moon", "lines": "attraction"},
    {"id": "iq", "ru": "IQ (интеллект)", "en": "IQ", "sequence": "venus",
     "side": "personality", "body": "venus", "lines": "iq"},
    {"id": "eq", "ru": "EQ (эмоциональный интеллект)", "en": "EQ", "sequence": "venus",
     "side": "personality", "body": "mars", "lines": "eq"},
    {"id": "sq", "ru": "SQ (духовный интеллект)", "en": "SQ", "sequence": "venus",
     "side": "design", "body": "venus", "lines": "sq"},
    {"id": "core", "ru": "Ядро (Сердцевина)", "en": "Core", "sequence": "venus",
     "side": "design", "body": "mars", "lines": "core"},
    {"id": "vocation", "ru": "Призвание", "en": "Vocation", "sequence": "pearl",
     "side": "design", "body": "mars", "lines": "vocation"},
    {"id": "culture", "ru": "Культура", "en": "Culture", "sequence": "pearl",
     "side": "design", "body": "jupiter", "lines": "culture"},
    {"id": "brand", "ru": "Бренд", "en": "Brand", "sequence": "pearl",
     "side": "personality", "body": "sun", "lines": "brand"},
    {"id": "pearl", "ru": "Жемчужина", "en": "Pearl", "sequence": "pearl",
     "side": "personality", "body": "jupiter", "lines": "pearl"},
]

#: Дополнительные сферы, перечисленные в той же официальной таблице (12.2024) для
#: «последовательностей в разработке»; принадлежность к последовательности не опубликована.
EXTENDED_SPHERES: list[dict] = [
    {"id": "relating", "ru": "Взаимодействие (Relating)", "en": "Relating", "sequence": "extended",
     "side": "personality", "body": "mercury", "lines": None},
    {"id": "stability", "ru": "Стабильность (Stability)", "en": "Stability", "sequence": "extended",
     "side": "design", "body": "saturn", "lines": None},
    {"id": "creativity", "ru": "Творчество (Creativity)", "en": "Creativity", "sequence": "extended",
     "side": "design", "body": "uranus", "lines": None},
]

SEQUENCES: dict[str, dict] = {
    "activation": {"ru": "Последовательность Активации", "en": "Activation Sequence",
                   "spheres": ["lifes_work", "evolution", "radiance", "purpose"]},
    "venus": {"ru": "Последовательность Венеры", "en": "Venus Sequence",
              "spheres": ["purpose", "attraction", "iq", "eq", "sq", "core"]},
    "pearl": {"ru": "Последовательность Жемчужины", "en": "Pearl Sequence",
              "spheres": ["vocation", "culture", "brand", "pearl"]},
}

BODY_RU = {"sun": "Солнце", "earth": "Земля", "moon": "Луна", "mercury": "Меркурий", "venus": "Венера",
           "mars": "Марс", "jupiter": "Юпитер", "saturn": "Сатурн", "uranus": "Уран"}
SIDE_RU = {"personality": "Личность (натал, момент рождения)",
           "design": "Дизайн (пренатал, Солнце на 88° раньше)"}

# ---------------------------------------------------------------------------
# Ключевые слова линий по сферам.
# status: "official"   — подтверждено официальным материалом/профилем Gene Keys
#         "secondary"  — только вторичный источник (практикующие), ⚠ не подтверждено официально
#         "unconfirmed"— не найдено
# Русские формулировки — перевод составителя базы (официального русского перевода нет).
# ---------------------------------------------------------------------------

_O, _S, _U = "official", "secondary", "unconfirmed"

LINE_KEYNOTES: dict[str, dict[int, dict]] = {
    "generic": {
        1: {"en": "Inner essence & self-empowerment (wound: repression)", "ru": "Внутренняя суть и опора на себя (рана: подавление)", "status": _O},
        2: {"en": "Expression & relationships (wound: denial)", "ru": "Самовыражение и отношения (рана: отрицание)", "status": _O},
        3: {"en": "Experimentation & experience (wound: shame)", "ru": "Эксперимент и опыт (рана: стыд)", "status": _O},
        4: {"en": "Friendship & community (wound: rejection)", "ru": "Дружба и сообщество (рана: отвержение)", "status": _O},
        5: {"en": "Leadership & organisation (wound: guilt)", "ru": "Лидерство и организация (рана: вина)", "status": _O},
        6: {"en": "Vision & role-modelling (wound: isolation)", "ru": "Видение и личный пример (рана: изоляция)", "status": _O},
    },
    "lifes_work": {
        1: {"en": "Creator", "ru": "Творец", "status": _O},
        2: {"en": "Natural", "ru": "Самородок", "status": _S},
        3: {"en": "Changer", "ru": "Преобразователь", "status": _S},
        4: {"en": "Server", "ru": "Служитель", "status": _S},
        5: {"en": "Fixer", "ru": "Решатель проблем", "status": _O},
        6: {"en": "Teacher", "ru": "Учитель", "status": _O},
    },
    "evolution": {
        1: {"en": "Self-Empowerment (shadow keynote: Self-Esteem)", "ru": "Опора на себя (теневая нота: самооценка)", "status": _O},
        2: {"en": "Passion and Relationships (shadow keynote: Projection)", "ru": "Страсть и отношения (теневая нота: проекция)", "status": _O},
        3: {"en": "Energy and Experience (shadow keynote: Avoidance)", "ru": "Энергия и опыт (теневая нота: избегание)", "status": _O},
        4: {"en": "Love and Community (shadow keynote: Comparison)", "ru": "Любовь и сообщество (теневая нота: сравнение)", "status": _O},
        5: {"en": "Power and Projections (shadow keynote: Pressure)", "ru": "Сила и проекции (теневая нота: давление)", "status": _O},
        6: {"en": "Education and Surrender (shadow keynote: Seeking Resolution)", "ru": "Обучение и сдача (теневая нота: поиск разрешения)", "status": _O},
    },
    "radiance": {
        1: {"en": "Solitude", "ru": "Уединение", "status": _S},
        2: {"en": "Marriage", "ru": "Союз (брак)", "status": _O},
        3: {"en": "Interaction", "ru": "Взаимодействие", "status": _O},
        4: {"en": "Friendship", "ru": "Дружба", "status": _S},
        5: {"en": "Impact", "ru": "Влияние", "status": _S},
        6: {"en": "Nurture", "ru": "Забота", "status": _S},
    },
    "purpose_activation": {
        1: {"en": "Physicality (bones)", "ru": "Телесность (кости)", "status": _O},
        2: {"en": "Posture (fluids)", "ru": "Осанка (жидкости)", "status": _O},
        3: {"en": "Movement (blood)", "ru": "Движение (кровь)", "status": _O},
        4: {"en": "Breath", "ru": "Дыхание", "status": _S},
        5: {"en": "Voice", "ru": "Голос", "status": _S},
        6: {"en": "Presence", "ru": "Присутствие", "status": _S},
    },
    "purpose_venus": {
        1: {"en": "The Loner / Anchor", "ru": "Одиночка / Якорь", "status": _O},
        2: {"en": "The Natural / Accuser", "ru": "Естественный / Обвинитель", "status": _O},
        3: {"en": "The Adventurer / Escape Artist", "ru": "Искатель приключений / Беглец", "status": _O},
        4: {"en": "The Nurturer / Politician", "ru": "Опекун / Политик", "status": _S},
        5: {"en": "The Leader / Victim", "ru": "Лидер / Жертва", "status": _S},
        6: {"en": "The Visionary / Judge", "ru": "Визионер / Судья", "status": _S},
    },
    "attraction": {
        1: {"en": "Sterility / Fertility", "ru": "Бесплодность / Плодородие", "status": _S},
        2: {"en": "Lust / Passion", "ru": "Похоть / Страсть", "status": _S},
        3: {"en": "Promiscuity / Playfulness", "ru": "Неразборчивость / Игривость", "status": _S},
        4: {"en": "Frigidity / Romance (distant / intimate)", "ru": "Холодность / Романтика (отстранённый / близкий)", "status": _O},
        5: {"en": "Entrapment / Sensuality", "ru": "Ловушка / Чувственность", "status": _S},
        6: {"en": "Disappointment / Innocence", "ru": "Разочарование / Невинность", "status": _O},
    },
    "iq": {
        1: {"en": "The Contemplative mind (hidden)", "ru": "Созерцательный ум (скрытый)", "status": _S},
        2: {"en": "The Brilliant mind (provocative)", "ru": "Блестящий ум (провокационный)", "status": _O},
        3: {"en": "The Flexible mind (evasive)", "ru": "Гибкий ум (уклончивый)", "status": _O},
        4: {"en": "The Influential mind (inflexible)", "ru": "Влиятельный ум (негибкий)", "status": _S},
        5: {"en": "The Practical mind (defensive)", "ru": "Практичный ум (обороняющийся)", "status": _S},
        6: {"en": "The Objective mind (absent)", "ru": "Объективный ум (отсутствующий)", "status": _S},
    },
    "eq": {
        1: {"en": "Self-esteem / Self-sabotage", "ru": "Самоуважение / Самосаботаж", "status": _O},
        2: {"en": "Courtesy / Aggression", "ru": "Учтивость / Агрессия", "status": _O},
        3: {"en": "Sympathy / Apathy", "ru": "Сочувствие / Апатия", "status": _S},
        4: {"en": "Kindness / Meanness", "ru": "Доброта / Злонравие", "status": _O},
        5: {"en": "Respect / Disrespect", "ru": "Уважение / Неуважение", "status": _S},
        6: {"en": "Reverence / Alienation", "ru": "Благоговение / Отчуждение", "status": _S},
    },
    "sq": {
        1: {"en": "Certainty (rhythm and routine)", "ru": "Уверенность (ритм и распорядок)", "status": _O},
        2: {"en": "Freedom (wildness and boundaries)", "ru": "Свобода (дикость и границы)", "status": _S},
        3: {"en": "Pleasure (adventure and understanding)", "ru": "Удовольствие (приключение и понимание)", "status": _S},
        4: {"en": "Belonging (kinship and community)", "ru": "Принадлежность (родство и общность)", "status": _S},
        5: {"en": "Mentoring (role models with integrity)", "ru": "Наставничество (честные ролевые модели)", "status": _O},
        6: {"en": "Patience (time and space)", "ru": "Терпение (время и пространство)", "status": _S},
    },
    "core": {
        1: {"en": "Repression / Self-honesty", "ru": "Подавление / Честность с собой", "status": _S},
        2: {"en": "Denial / Ease", "ru": "Отрицание / Лёгкость", "status": _O},
        3: {"en": "Shame / Humour", "ru": "Стыд / Юмор", "status": _S},
        4: {"en": "Rejection / Gentleness", "ru": "Отвержение / Мягкость", "status": _S},
        5: {"en": "Guilt / Forgiveness", "ru": "Вина / Прощение", "status": _O},
        6: {"en": "Separation / Self-care", "ru": "Отделённость / Забота о себе", "status": _S},
    },
    "vocation": {
        1: {"en": "Production", "ru": "Производство", "status": _S},
        2: {"en": "Marketing (value)", "ru": "Маркетинг (ценность)", "status": _O},
        3: {"en": "Strategy", "ru": "Стратегия", "status": _S},
        4: {"en": "Sales", "ru": "Продажи", "status": _S},
        5: {"en": "Management (responsibility)", "ru": "Управление (ответственность)", "status": _O},
        6: {"en": "Philanthropy (ethics)", "ru": "Филантропия (этика)", "status": _O},
    },
    "culture": {
        1: {"en": "Individual", "ru": "Индивидуальный формат", "status": _O},
        2: {"en": None, "ru": None, "status": _U},
        3: {"en": None, "ru": None, "status": _U},
        4: {"en": "Network", "ru": "Сеть", "status": _O},
        5: {"en": None, "ru": None, "status": _U},
        6: {"en": "System", "ru": "Система", "status": _O},
    },
    "brand": {
        1: {"en": "Boldness (security)", "ru": "Смелость (безопасность)", "status": _O},
        2: {"en": "Passion (image)", "ru": "Страсть (образ)", "status": _S},
        3: {"en": "Humour (pleasure)", "ru": "Юмор (удовольствие)", "status": _S},
        4: {"en": "Heart (feelings)", "ru": "Сердце (чувства)", "status": _S},
        5: {"en": "Wisdom (solutions)", "ru": "Мудрость (решения)", "status": _O},
        6: {"en": "Vision (education)", "ru": "Видение (просвещение)", "status": _S},
    },
    "pearl": {
        1: {"en": "Simplicity", "ru": "Простота", "status": _S},
        2: {"en": "Recognition", "ru": "Признание", "status": _S},
        3: {"en": "Celebration", "ru": "Празднование", "status": _O},
        4: {"en": "Charity", "ru": "Благотворительность", "status": _O},
        5: {"en": "Power", "ru": "Сила (влияние)", "status": _S},
        6: {"en": "Nature", "ru": "Природа", "status": _O},
    },
}


# ---------------------------------------------------------------------------
# Базовые функции колеса
# ---------------------------------------------------------------------------

def key_line_from_longitude(lon: float) -> dict:
    """Тропическая долгота -> ключ (1..64), линия (1..6) и положение внутри.

    Алгоритм:
      offset = (lon − 302°) mod 360°
      i      = ⌊offset / 5.625°⌋               (номер сектора 0..63 от ключа 41)
      key    = GATE_ORDER[i]
      line   = ⌊(offset − i·5.625°) / 0.9375°⌋ + 1
    """
    lon = lon % 360.0
    offset = (lon - WHEEL_START_DEG) % 360.0
    idx = int(offset // KEY_ARC)
    if idx > 63:  # защита от погрешности на самом краю круга
        idx = 63
    in_key = offset - idx * KEY_ARC
    line = int(in_key // LINE_ARC) + 1
    if line > 6:
        line = 6
    in_line = in_key - (line - 1) * LINE_ARC
    key_start = (WHEEL_START_DEG + idx * KEY_ARC) % 360.0
    line_start = (key_start + (line - 1) * LINE_ARC) % 360.0
    return {
        "key": GATE_ORDER[idx],
        "line": line,
        "wheel_index": idx,
        "offset_from_wheel_start": offset,
        "deg_in_key": in_key,
        "deg_in_line": in_line,
        "key_start_lon": key_start,
        "line_start_lon": line_start,
        # расстояние до ближайшей границы линии (чувствительность к времени рождения)
        "margin_deg": min(in_line, LINE_ARC - in_line),
    }


def programming_partner(key: int) -> int:
    """Программный партнёр — ключ, противоположный на колесе (+180° = +32 сектора)."""
    return GATE_ORDER[(_INDEX_OF_KEY[key] + 32) % 64]


def key_info(key: int) -> dict:
    """Тень/Дар/Сиддхи, программный партнёр и кодоновое кольцо ключа."""
    k = KEYS[key]
    ring = _RING_OF_KEY[key]
    return {
        "shadow": {"en": k["shadow"][0], "ru": k["shadow"][1]},
        "gift": {"en": k["gift"][0], "ru": k["gift"][1]},
        "siddhi": {"en": k["siddhi"][0], "ru": k["siddhi"][1]},
        "programming_partner": programming_partner(key),
        "codon_ring": {"en": ring["en"], "ru": ring["ru"], "keys": list(ring["keys"]),
                       "amino_acid_en": ring["amino_en"], "amino_acid_ru": ring["amino_ru"]},
    }


def line_keynote(theme: str | None, line: int) -> dict | None:
    if theme is None:
        return None
    return dict(LINE_KEYNOTES[theme][line])


# ---------------------------------------------------------------------------
# Астрономия: два момента
# ---------------------------------------------------------------------------

_BODIES = ["sun", "earth", "moon", "mercury", "venus", "mars", "jupiter", "saturn", "uranus"]


def _bodies_at(jd_ut: float) -> dict[str, dict]:
    pp = eph.planet_positions(jd_ut)
    out: dict[str, dict] = {}
    for name in _BODIES:
        if name == "earth":
            src = pp["sun"]
            out[name] = {"lon": (src["lon"] + 180.0) % 360.0, "speed": src["speed"]}
        else:
            out[name] = {"lon": pp[name]["lon"], "speed": pp[name]["speed"]}
    return out


def design_jd(jd_birth_ut: float) -> float:
    """Момент Дизайна: последнее до рождения прохождение Солнцем долготы (Солнце_рожд − 88°)."""
    target = (eph.sun_longitude(jd_birth_ut) - DESIGN_ARC_DEG) % 360.0
    return eph.find_sun_longitude(target, jd_birth_ut, search_back=True)


def profile_for_jd(jd_ut: float, include_extended: bool = True) -> dict:
    """Ядро расчёта для момента рождения jd_ut (UT): ключ.линия всех сфер.

    Возвращает {"jd_design", "personality", "design", "spheres": {id: "K.L"}} —
    удобно для перекрёстной сверки с модулем Human Design.
    """
    jd_d = design_jd(jd_ut)
    pers = _bodies_at(jd_ut)
    des = _bodies_at(jd_d)
    spheres = {}
    for s in SPHERES + (EXTENDED_SPHERES if include_extended else []):
        src = pers if s["side"] == "personality" else des
        kl = key_line_from_longitude(src[s["body"]]["lon"])
        spheres[s["id"]] = f"{kl['key']}.{kl['line']}"
    return {"jd_design": jd_d, "personality": pers, "design": des, "spheres": spheres}


# ---------------------------------------------------------------------------
# Основной расчёт
# ---------------------------------------------------------------------------

def _iso(jd: float) -> str:
    return jd_to_utc(jd).replace(microsecond=0).isoformat()


def _line_change_minutes(s: dict, pers: dict, des: dict, margin_deg: float) -> float | None:
    """Оценка: на сколько минут нужно сдвинуть время рождения, чтобы линия сменилась.

    Для стороны «Личность» скорость тела берётся в момент рождения. Для стороны «Дизайн»
    момент Дизайна сдвигается вслед за рождением с коэффициентом
    v☉(рожд) / v☉(дизайн) (≈1), поэтому скорость = v_тела(дизайн) · этот коэффициент.
    """
    if s["side"] == "personality":
        v = abs(pers[s["body"]]["speed"])
    else:
        ratio = pers["sun"]["speed"] / des["sun"]["speed"]
        v = abs(des[s["body"]]["speed"] * ratio)
    if v < 1e-9:
        return None
    return margin_deg / v * 1440.0


def _build_sphere(s: dict, pers: dict, des: dict) -> dict:
    src = pers if s["side"] == "personality" else des
    lon = src[s["body"]]["lon"]
    kl = key_line_from_longitude(lon)
    key, line = kl["key"], kl["line"]
    out = {
        "id": s["id"],
        "name_ru": s["ru"],
        "name_en": s["en"],
        "sequence": s["sequence"],
        "source": {"side": s["side"], "side_ru": SIDE_RU[s["side"]], "body": s["body"],
                   "body_ru": BODY_RU[s["body"]]},
        "lon": round(lon, 6),
        "lon_str": eph.format_lon(lon),
        "key": key,
        "line": line,
        "key_line": f"{key}.{line}",
        "deg_in_key": round(kl["deg_in_key"], 6),
        "margin_deg": round(kl["margin_deg"], 6),
        "line_change_minutes_approx": None,
        **key_info(key),
        "line_keynote": line_keynote(s["lines"], line),
        "line_generic": line_keynote("generic", line),
    }
    m = _line_change_minutes(s, pers, des, kl["margin_deg"])
    out["line_change_minutes_approx"] = None if m is None else round(m, 1)
    if s.get("lines_venus"):
        out["line_keynote_venus"] = line_keynote(s["lines_venus"], line)
    return out


def _local_day_scan(b: BirthInput, step_min: int = 10) -> tuple[list[float], list[str]]:
    """Моменты (JD UT) для перебора суток рождения, если время неизвестно."""
    warnings: list[str] = []
    if b.tz:
        tzname = b.tz
        moments = []
        for i in range(0, 24 * 60, step_min):
            bb = BirthInput(b.year, b.month, b.day, i // 60, i % 60, tz=tzname, lat=b.lat, lon=b.lon)
            moments.append(normalize(bb).jd_ut)
        last = BirthInput(b.year, b.month, b.day, 23, 59, tz=tzname, lat=b.lat, lon=b.lon)
        moments.append(normalize(last).jd_ut)
    else:
        warnings.append("Не задан часовой пояс/место: перебраны все моменты, когда в каком-либо поясе "
                        "(UTC−12…UTC+14) шла указанная дата.")
        start = datetime(b.year, b.month, b.day, tzinfo=timezone.utc) - timedelta(hours=14)
        moments = [julian_day_ut(start + timedelta(minutes=i)) for i in range(0, (24 + 26) * 60 + 1, step_min)]
    return moments, warnings


def calculate(b: BirthInput, **options) -> dict:
    """Гологенетический профиль Генных ключей.

    Опции:
      include_extended (bool, True) — добавить сферы Relating / Stability / Creativity
                                      (официальная таблица 12.2024, последовательность не опубликована);
      time_uncertainty_min (int, 15) — допуск времени рождения для проверки устойчивости сфер;
      scan_step_min (int, 10) — шаг перебора суток, если время рождения неизвестно.
    """
    include_extended = bool(options.get("include_extended", True))
    tol_min = float(options.get("time_uncertainty_min", 15))
    scan_step = int(options.get("scan_step_min", 10))
    warnings: list[str] = []
    steps: list[dict] = []

    time_known = b.has_time
    scan: dict | None = None
    if time_known:
        if b.tz is None:
            raise ValueError("Генные ключи: задано время, но не задан часовой пояс/место (tz/place).")
        n = normalize(b)
        warnings += n.warnings
        jd = n.jd_ut
        inputs_used = {
            "local": n.local.isoformat(), "tz": b.tz, "utc_offset": fmt_offset(n.utc_offset_hours),
            "offset_source": n.offset_source, "utc": n.utc.replace(microsecond=0).isoformat(),
            "jd_ut": round(jd, 6), "lat": b.lat, "lon": b.lon, "place": b.place, "time_known": True,
        }
        steps.append({"step": 1, "title": "Время рождения → UTC → юлианский день",
                      "detail": f"{n.local:%d.%m.%Y %H:%M} ({b.tz}, смещение {fmt_offset(n.utc_offset_hours)}, "
                                f"источник: {n.offset_source}) = {n.utc:%d.%m.%Y %H:%M:%S} UTC; JD(UT) = {jd:.6f}"})
    else:
        # Время неизвестно: перебираем сутки, основной профиль — на 12:00 местного времени.
        moments, w = _local_day_scan(b, scan_step)
        warnings += w
        warnings.append("Время рождения неизвестно: профиль показан на 12:00 местного времени; "
                        "надёжны только сферы из списка time_scan.stable.")
        if b.tz:
            n = normalize(BirthInput(b.year, b.month, b.day, 12, 0, tz=b.tz, lat=b.lat, lon=b.lon))
            jd = n.jd_ut
            utc_str = n.utc.replace(microsecond=0).isoformat()
        else:
            jd = julian_day_ut(datetime(b.year, b.month, b.day, 12, 0, tzinfo=timezone.utc))
            utc_str = _iso(jd)
        values: dict[str, list[str]] = {}
        for mjd in moments:
            for sid, v in profile_for_jd(mjd, include_extended)["spheres"].items():
                lst = values.setdefault(sid, [])
                if not lst or lst[-1] != v:
                    lst.append(v)
        scan = {"samples": len(moments), "step_min": scan_step,
                "stable": sorted(k for k, v in values.items() if len(v) == 1),
                "variable": {k: v for k, v in values.items() if len(v) > 1}}
        inputs_used = {"local": f"{b.year:04d}-{b.month:02d}-{b.day:02d}T12:00 (условно)", "tz": b.tz,
                       "utc": utc_str, "jd_ut": round(jd, 6), "lat": b.lat, "lon": b.lon,
                       "place": b.place, "time_known": False}
        steps.append({"step": 1, "title": "Время неизвестно",
                      "detail": f"Перебор суток с шагом {scan_step} мин ({len(moments)} моментов); "
                                f"основной профиль — на полдень: JD(UT) = {jd:.6f}"})

    # 2. Личность
    pers = _bodies_at(jd)
    sun_p = pers["sun"]["lon"]
    steps.append({"step": 2, "title": "Личность (Personality): положения планет в момент рождения",
                  "detail": "Тропический зодиак, геоцентрически, Swiss Ephemeris. " + "; ".join(
                      f"{BODY_RU[k]} {pers[k]['lon']:.4f}° ({eph.format_lon(pers[k]['lon'])})"
                      for k in ["sun", "earth", "venus", "mars", "jupiter"])})

    # 3. Дизайн
    jd_d = design_jd(jd)
    des = _bodies_at(jd_d)
    target = (sun_p - DESIGN_ARC_DEG) % 360.0
    days_before = jd - jd_d
    steps.append({"step": 3, "title": "Дизайн (Design): момент, когда Солнце было на 88° раньше",
                  "detail": f"Цель: {sun_p:.4f}° − 88° = {target:.4f}° ({eph.format_lon(target)}). "
                            f"Солнце прошло эту точку {_iso(jd_d)} UTC (JD {jd_d:.6f}), "
                            f"за {days_before:.2f} сут до рождения. Положения в этот момент: " + "; ".join(
                                f"{BODY_RU[k]} {des[k]['lon']:.4f}° ({eph.format_lon(des[k]['lon'])})"
                                for k in ["sun", "earth", "moon", "venus", "mars", "jupiter"])})

    # 4. Перевод долгот в ключ.линия
    sphere_defs = SPHERES + (EXTENDED_SPHERES if include_extended else [])
    spheres = {s["id"]: _build_sphere(s, pers, des) for s in sphere_defs}
    lw = spheres["lifes_work"]
    off = (lw["lon"] - WHEEL_START_DEG) % 360.0
    idx = int(off // KEY_ARC)
    steps.append({"step": 4, "title": "Долгота → Генный ключ и линия (пример — Дело жизни)",
                  "detail": f"offset = ({lw['lon']:.4f}° − 302°) mod 360 = {off:.4f}°; "
                            f"индекс = ⌊{off:.4f}/5.625⌋ = {idx} → GATE_ORDER[{idx}] = ключ {lw['key']}; "
                            f"внутри ключа {lw['deg_in_key']:.4f}° → линия ⌊{lw['deg_in_key']:.4f}/0.9375⌋+1 = {lw['line']}"})
    steps.append({"step": 5, "title": "Сферы профиля (сторона · тело → долгота → ключ.линия)",
                  "detail": "; ".join(f"{sp['name_ru']}: {sp['source']['side']}·{sp['source']['body_ru']} "
                                      f"{sp['lon']:.4f}° → {sp['key_line']}" for sp in spheres.values())})

    # 5. Самопроверки
    checks = {
        "evolution_is_partner_of_lifes_work":
            spheres["evolution"]["key"] == programming_partner(spheres["lifes_work"]["key"])
            and spheres["evolution"]["line"] == spheres["lifes_work"]["line"],
        "purpose_is_partner_of_radiance":
            spheres["purpose"]["key"] == programming_partner(spheres["radiance"]["key"])
            and spheres["purpose"]["line"] == spheres["radiance"]["line"],
        "brand_equals_lifes_work": spheres["brand"]["key_line"] == spheres["lifes_work"]["key_line"],
        "vocation_equals_core": spheres["vocation"]["key_line"] == spheres["core"]["key_line"],
        "design_sun_arc_deg": round((sun_p - des["sun"]["lon"]) % 360.0, 6),
        "design_days_before_birth": round(days_before, 3),
    }
    checks["all_ok"] = (checks["evolution_is_partner_of_lifes_work"] and checks["purpose_is_partner_of_radiance"]
                        and checks["brand_equals_lifes_work"] and checks["vocation_equals_core"]
                        and abs(checks["design_sun_arc_deg"] - 88.0) < 1e-4)
    steps.append({"step": 6, "title": "Самопроверка",
                  "detail": f"Эволюция = партнёр Дела жизни: {checks['evolution_is_partner_of_lifes_work']}; "
                            f"Предназначение = партнёр Сияния: {checks['purpose_is_partner_of_radiance']}; "
                            f"Бренд = Дело жизни: {checks['brand_equals_lifes_work']}; "
                            f"Призвание = Ядро: {checks['vocation_equals_core']}; "
                            f"дуга Солнца = {checks['design_sun_arc_deg']}°"})

    # 6. Чувствительность к времени рождения
    sensitivity: dict = {"tolerance_min": tol_min, "changes_within_tolerance": {}}
    if time_known and tol_min > 0:
        lo = profile_for_jd(jd - tol_min / 1440.0, include_extended)["spheres"]
        hi = profile_for_jd(jd + tol_min / 1440.0, include_extended)["spheres"]
        for sid, sp in spheres.items():
            vals = {lo[sid], sp["key_line"], hi[sid]}
            if len(vals) > 1:
                sensitivity["changes_within_tolerance"][sid] = [lo[sid], sp["key_line"], hi[sid]]
        if sensitivity["changes_within_tolerance"]:
            names = ", ".join(spheres[s]["name_ru"] for s in sensitivity["changes_within_tolerance"])
            warnings.append(f"При сдвиге времени рождения на ±{tol_min:g} мин меняется линия/ключ в сферах: {names}.")

    sequences = {k: {"ru": v["ru"], "en": v["en"], "spheres": list(v["spheres"])} for k, v in SEQUENCES.items()}

    result = {
        "method": "gene_keys",
        "variant": ("Гологенетический профиль Gene Keys (genekeys.com, таблица сфер от 15.12.2024): "
                    "тропический зодиак, Swiss Ephemeris, Дизайн = Солнце −88° дуги, колесо 64 ключей "
                    "от 302° (ключ 41), 6 линий по 0.9375°"),
        "inputs_used": {**inputs_used, "design_utc": _iso(jd_d), "design_jd_ut": round(jd_d, 6)},
        "warnings": warnings,
        "personality": {"jd_ut": round(jd, 6),
                        "bodies": {k: {"lon": round(v["lon"], 6), "lon_str": eph.format_lon(v["lon"]),
                                       **{x: key_line_from_longitude(v["lon"])[x] for x in ("key", "line")}}
                                   for k, v in pers.items()}},
        "design": {"jd_ut": round(jd_d, 6), "utc": _iso(jd_d),
                   "bodies": {k: {"lon": round(v["lon"], 6), "lon_str": eph.format_lon(v["lon"]),
                                  **{x: key_line_from_longitude(v["lon"])[x] for x in ("key", "line")}}
                              for k, v in des.items()}},
        "spheres": spheres,
        "sequences": sequences,
        "profile": {sid: sp["key_line"] for sid, sp in spheres.items()},
        "checks": checks,
        "time_sensitivity": sensitivity,
        "steps": steps,
    }
    if scan is not None:
        result["time_scan"] = scan
    return result


__all__ = [
    "calculate", "key_line_from_longitude", "programming_partner", "key_info", "profile_for_jd",
    "design_jd", "GATE_ORDER", "KEYS", "CODON_RINGS", "SPHERES", "EXTENDED_SPHERES", "LINE_KEYNOTES",
]
