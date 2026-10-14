"""Дизайн Человека (Human Design System, Ra Uru Hu / Jovian Archive): бодиграф.

Конвейер расчёта:
  местное время → UTC → JD(UT) → долготы 13 «активаций» на момент рождения (Личность)
  → момент Дизайна (Солнце на 88° дуги эклиптики раньше) → 13 активаций Дизайна
  → ворота/линия/цвет/тон/база по колесу Рейв-мандалы → каналы → центры
  → тип, стратегия, авторитет, профиль, определённость, инкарнационный крест, переменные.

Значения по умолчанию (обоснование и сверка — knowledge-base/04-human-design.md):
* зодиак тропический, долготы геоцентрические видимые (Swiss Ephemeris);
* момент Дизайна — когда долгота Солнца была ровно на 88°00′ меньше натальной
  (88° солнечной дуги, НЕ 88 суток);
* лунные узлы — ИСТИННЫЕ (true node): так считает официальный движок Jovian Archive /
  MyBodyGraph (charts.maiamechanics.com) — проверено по долготам для 7 карт; средний узел
  доступен опцией node="mean" (так считают некоторые сторонние программы);
* колесо: ворота 41 начинаются в 302°00′ (2°00′ Водолея), шаг 5,625° на ворота,
  0,9375° на линию, 6 цветов на линию, 6 тонов на цвет, 5 баз на тон.

Пример:
    from calculators.common.time import BirthInput
    from calculators.human_design import calculate
    r = calculate(BirthInput(1879, 3, 14, 11, 30, tz="LMT", lat=48.4011, lon=9.9876))
    r["type"]["name_ru"], r["profile"]["profile"], r["incarnation_cross"]["name_en"]
"""
from __future__ import annotations

from collections import deque

from .common import ephemeris as eph
from .common.time import BirthInput, fmt_offset, jd_to_utc, normalize

# ---------------------------------------------------------------------------
# Геометрия Рейв-мандалы
# ---------------------------------------------------------------------------

WHEEL_START = 302.0           # начало ворот 41 = 2°00′00″ Водолея (тропический зодиак)
GATE_SPAN = 360.0 / 64        # 5.625°  = 5°37′30″
LINE_SPAN = GATE_SPAN / 6     # 0.9375° = 56′15″
COLOR_SPAN = LINE_SPAN / 6    # 0.15625° = 9′22.5″
TONE_SPAN = COLOR_SPAN / 6    # 0.0260417° = 1′33.75″
BASE_SPAN = TONE_SPAN / 5     # 0.0052083° = 18.75″
DESIGN_ARC = 88.0             # градусов солнечной дуги между Дизайном и Личностью

# Порядок ворот по колесу, начиная с ворот 41 (302°) и далее по возрастанию долготы.
GATE_ORDER: list[int] = [
    41, 19, 13, 49, 30, 55, 37, 63, 22, 36, 25, 17, 21, 51, 42, 3,
    27, 24, 2, 23, 8, 20, 16, 35, 45, 12, 15, 52, 39, 53, 62, 56,
    31, 33, 7, 4, 29, 59, 40, 64, 47, 6, 46, 18, 48, 57, 32, 50,
    28, 44, 1, 43, 14, 34, 9, 5, 26, 11, 10, 58, 38, 54, 61, 60,
]
GATE_INDEX: dict[int, int] = {g: i for i, g in enumerate(GATE_ORDER)}

# Четверти мандалы (по 16 ворот). Номер четверти = номер варианта правоуглового креста.
QUARTERS: list[dict] = [
    {"id": "initiation", "name_en": "Quarter of Initiation", "name_ru": "Четверть Инициации",
     "theme_ru": "цель реализуется через разум (Mind)", "first_gate": 13},
    {"id": "civilization", "name_en": "Quarter of Civilization", "name_ru": "Четверть Цивилизации",
     "theme_ru": "цель реализуется через форму (Form)", "first_gate": 2},
    {"id": "duality", "name_en": "Quarter of Duality", "name_ru": "Четверть Дуальности",
     "theme_ru": "цель реализуется через связь (Bonding)", "first_gate": 7},
    {"id": "mutation", "name_en": "Quarter of Mutation", "name_ru": "Четверть Мутации",
     "theme_ru": "цель реализуется через трансформацию (Transformation)", "first_gate": 1},
]


def _quarter_index(gate: int) -> int:
    """Номер четверти 0..3: четверть Инициации начинается с ворот 13 (313°15′)."""
    return ((GATE_INDEX[gate] - GATE_INDEX[13]) % 64) // 16


# ---------------------------------------------------------------------------
# Центры, ворота, каналы
# ---------------------------------------------------------------------------

CENTERS: dict[str, dict] = {
    "head":         {"name_ru": "Теменной (Головной) центр", "name_en": "Head", "kind": "давление, осознанность-вдохновение"},
    "ajna":         {"name_ru": "Аджна", "name_en": "Ajna", "kind": "осознанность (ментальная)"},
    "throat":       {"name_ru": "Горловой центр", "name_en": "Throat", "kind": "проявление (речь/действие)"},
    "g":            {"name_ru": "G-центр (центр Я, Идентичности)", "name_en": "G (Self)", "kind": "идентичность, направление, любовь"},
    "heart":        {"name_ru": "Сердце (Эго, Воля)", "name_en": "Heart (Ego/Will)", "kind": "мотор"},
    "sacral":       {"name_ru": "Сакральный центр", "name_en": "Sacral", "kind": "мотор (жизненная сила)"},
    "solar_plexus": {"name_ru": "Солнечное сплетение (Эмоциональный)", "name_en": "Solar Plexus", "kind": "мотор + осознанность (эмоции)"},
    "spleen":       {"name_ru": "Селезёнка (Селезёночный центр)", "name_en": "Spleen", "kind": "осознанность (телесная, интуиция)"},
    "root":         {"name_ru": "Корневой центр", "name_en": "Root", "kind": "мотор + давление"},
}
MOTORS = ("sacral", "solar_plexus", "heart", "root")

# Ворота: центр, имя гексаграммы И-цзин (как в MyBodyGraph), ключевое имя ворот HD (англ.) и перевод.
GATES: dict[int, dict] = {
    1:  {"center": "g", "iching": "The Creative", "en": "Self-Expression", "ru": "Самовыражение"},
    2:  {"center": "g", "iching": "The Receptive", "en": "Direction of the Self", "ru": "Направление Я"},
    3:  {"center": "sacral", "iching": "Difficulty at the Beginning", "en": "Ordering", "ru": "Упорядочивание"},
    4:  {"center": "ajna", "iching": "Youthful Folly", "en": "Formulization", "ru": "Формулирование"},
    5:  {"center": "sacral", "iching": "Waiting", "en": "Fixed Patterns (Fixed Rhythms)", "ru": "Фиксированные ритмы"},
    6:  {"center": "solar_plexus", "iching": "Conflict", "en": "Friction", "ru": "Трение"},
    7:  {"center": "g", "iching": "The Army", "en": "The Role of the Self in Interaction", "ru": "Роль Я во взаимодействии"},
    8:  {"center": "throat", "iching": "Holding Together", "en": "Contribution", "ru": "Вклад"},
    9:  {"center": "sacral", "iching": "The Taming Power of the Small", "en": "Focus", "ru": "Фокус"},
    10: {"center": "g", "iching": "Treading", "en": "Behaviour of the Self", "ru": "Поведение Я"},
    11: {"center": "ajna", "iching": "Peace", "en": "Ideas", "ru": "Идеи"},
    12: {"center": "throat", "iching": "Standstill", "en": "Caution", "ru": "Осторожность"},
    13: {"center": "g", "iching": "The Fellowship of Man", "en": "The Listener", "ru": "Слушатель"},
    14: {"center": "sacral", "iching": "Possession in Great Measure", "en": "Power Skills", "ru": "Мастерство силы"},
    15: {"center": "g", "iching": "Modesty", "en": "Extremes", "ru": "Крайности"},
    16: {"center": "throat", "iching": "Enthusiasm", "en": "Skills", "ru": "Навыки"},
    17: {"center": "ajna", "iching": "Following", "en": "Opinion", "ru": "Мнения"},
    18: {"center": "spleen", "iching": "Work on What Has Been Spoilt", "en": "Correction", "ru": "Коррекция"},
    19: {"center": "root", "iching": "Approach", "en": "Wanting", "ru": "Стремление (потребность)"},
    20: {"center": "throat", "iching": "Contemplation", "en": "Direction of the Now (The Now)", "ru": "Сейчас"},
    21: {"center": "heart", "iching": "Biting Through", "en": "The Hunter/Huntress", "ru": "Охотник/Охотница"},
    22: {"center": "solar_plexus", "iching": "Grace", "en": "Openness", "ru": "Открытость"},
    23: {"center": "throat", "iching": "Splitting Apart", "en": "Assimilation", "ru": "Ассимиляция"},
    24: {"center": "ajna", "iching": "The Return", "en": "Rationalization", "ru": "Рационализация"},
    25: {"center": "g", "iching": "Innocence", "en": "The Spirit of the Self", "ru": "Дух Я (невинность)"},
    26: {"center": "heart", "iching": "The Taming Power of the Great", "en": "The Egoist", "ru": "Эгоист"},
    27: {"center": "sacral", "iching": "Nourishment", "en": "Caring", "ru": "Забота"},
    28: {"center": "spleen", "iching": "Preponderance of the Great", "en": "The Game Player", "ru": "Игрок"},
    29: {"center": "sacral", "iching": "The Abysmal", "en": "Perseverance (Saying Yes)", "ru": "Настойчивость («сказать да»)"},
    30: {"center": "solar_plexus", "iching": "The Clinging Fire", "en": "Feelings (Recognition of Feelings)", "ru": "Чувства (признание чувств)"},
    31: {"center": "throat", "iching": "Influence", "en": "Influence (Leading)", "ru": "Влияние (лидерство)"},
    32: {"center": "spleen", "iching": "Duration", "en": "Continuity", "ru": "Непрерывность"},
    33: {"center": "throat", "iching": "Retreat", "en": "Privacy", "ru": "Уединение"},
    34: {"center": "sacral", "iching": "The Power of the Great", "en": "Power", "ru": "Сила"},
    35: {"center": "throat", "iching": "Progress", "en": "Change", "ru": "Перемены"},
    36: {"center": "solar_plexus", "iching": "The Darkening of the Light", "en": "Crisis", "ru": "Кризис"},
    37: {"center": "solar_plexus", "iching": "The Family", "en": "Friendship", "ru": "Дружба"},
    38: {"center": "root", "iching": "Opposition", "en": "The Fighter", "ru": "Боец"},
    39: {"center": "root", "iching": "Obstruction", "en": "Provocation", "ru": "Провокация"},
    40: {"center": "heart", "iching": "Deliverance", "en": "Aloneness", "ru": "Одиночество (уединённость)"},
    41: {"center": "root", "iching": "Decrease", "en": "Contraction", "ru": "Сжатие"},
    42: {"center": "sacral", "iching": "Increase", "en": "Growth", "ru": "Рост"},
    43: {"center": "ajna", "iching": "Breakthrough", "en": "Insight", "ru": "Прозрение (инсайт)"},
    44: {"center": "spleen", "iching": "Coming to Meet", "en": "Alertness", "ru": "Бдительность"},
    45: {"center": "throat", "iching": "Gathering Together", "en": "The Gatherer", "ru": "Собиратель"},
    46: {"center": "g", "iching": "Pushing Upward", "en": "Determination of the Self", "ru": "Решимость Я"},
    47: {"center": "ajna", "iching": "Oppression", "en": "Realization", "ru": "Осознание"},
    48: {"center": "spleen", "iching": "The Well", "en": "Depth", "ru": "Глубина"},
    49: {"center": "solar_plexus", "iching": "Revolution", "en": "Principles", "ru": "Принципы"},
    50: {"center": "spleen", "iching": "The Cauldron", "en": "Values", "ru": "Ценности"},
    51: {"center": "heart", "iching": "The Arousing", "en": "Shock", "ru": "Шок"},
    52: {"center": "root", "iching": "Keeping Still (Mountain)", "en": "Stillness", "ru": "Неподвижность"},
    53: {"center": "root", "iching": "Development", "en": "Beginnings", "ru": "Начала"},
    54: {"center": "root", "iching": "The Marrying Maiden", "en": "Drive (Ambition)", "ru": "Амбиции (драйв)"},
    55: {"center": "solar_plexus", "iching": "Abundance", "en": "Spirit", "ru": "Дух (изобилие)"},
    56: {"center": "throat", "iching": "The Wanderer", "en": "Stimulation", "ru": "Стимуляция"},
    57: {"center": "spleen", "iching": "The Gentle", "en": "Intuitive Clarity", "ru": "Интуитивная ясность"},
    58: {"center": "root", "iching": "The Joyous", "en": "Vitality", "ru": "Жизненность"},
    59: {"center": "sacral", "iching": "After Dispersion", "en": "Sexuality", "ru": "Сексуальность"},
    60: {"center": "root", "iching": "Limitation", "en": "Acceptance", "ru": "Принятие"},
    61: {"center": "head", "iching": "Inner Truth", "en": "Mystery", "ru": "Тайна"},
    62: {"center": "throat", "iching": "Preponderance of the Small", "en": "Details", "ru": "Детали"},
    63: {"center": "head", "iching": "After Completion", "en": "Doubt", "ru": "Сомнение"},
    64: {"center": "head", "iching": "Before Completion", "en": "Confusion", "ru": "Замешательство"},
}

CIRCUITS: dict[str, dict] = {
    "knowing":     {"name_ru": "Контур Знания", "name_en": "Knowing Circuit", "group": "individual"},
    "centering":   {"name_ru": "Контур Центрирования", "name_en": "Centering Circuit", "group": "individual"},
    "integration": {"name_ru": "Каналы Интеграции", "name_en": "Integration Channels", "group": "integration"},
    "logic":       {"name_ru": "Контур Логики (Понимания)", "name_en": "Logic (Understanding) Circuit", "group": "collective"},
    "abstract":    {"name_ru": "Абстрактный контур (Ощущения)", "name_en": "Abstract (Sensing) Circuit", "group": "collective"},
    "ego":         {"name_ru": "Контур Эго", "name_en": "Ego Circuit", "group": "tribal"},
    "defense":     {"name_ru": "Контур Защиты", "name_en": "Defense Circuit", "group": "tribal"},
}
CIRCUIT_GROUPS_RU = {"individual": "Индивидуальная группа", "collective": "Коллективная группа",
                     "tribal": "Племенная группа", "integration": "Интеграция (особая группа)"}

# 36 каналов: (ворота a, ворота b, имя англ. (Jovian), перевод, контур)
CHANNELS: list[tuple[int, int, str, str, str]] = [
    (10, 20, "Awakening", "Пробуждение", "integration"),
    (20, 34, "Charisma", "Харизма", "integration"),
    (34, 57, "Power", "Сила (архетип)", "integration"),
    (10, 57, "Perfected Form", "Совершенная форма", "integration"),
    (24, 61, "Awareness", "Осознанность", "knowing"),
    (23, 43, "Structuring", "Структурирование", "knowing"),
    (28, 38, "Struggle", "Борьба", "knowing"),
    (20, 57, "The Brain Wave", "Мозговая волна", "knowing"),
    (39, 55, "Emoting", "Эмоциональность (переменчивость настроения)", "knowing"),
    (12, 22, "Openness", "Открытость", "knowing"),
    (3, 60, "Mutation", "Мутация", "knowing"),
    (2, 14, "The Beat", "Пульс (Бит)", "knowing"),
    (1, 8, "Inspiration", "Вдохновение", "knowing"),
    (10, 34, "Exploration", "Исследование", "centering"),
    (25, 51, "Initiation", "Инициация", "centering"),
    (4, 63, "Logic", "Логика", "logic"),
    (17, 62, "Acceptance", "Принятие", "logic"),
    (18, 58, "Judgment", "Суждение", "logic"),
    (16, 48, "The Wavelength", "Длина волны (талант)", "logic"),
    (9, 52, "Concentration", "Концентрация", "logic"),
    (5, 15, "Rhythm", "Ритм", "logic"),
    (7, 31, "The Alpha", "Альфа", "logic"),
    (30, 41, "Recognition", "Признание", "abstract"),
    (35, 36, "Transitoriness", "Быстротечность", "abstract"),
    (47, 64, "Abstraction", "Абстрагирование", "abstract"),
    (11, 56, "Curiosity", "Любопытство", "abstract"),
    (42, 53, "Maturation", "Созревание", "abstract"),
    (29, 46, "Discovery", "Открытие", "abstract"),
    (13, 33, "The Prodigal", "Блудный сын", "abstract"),
    (32, 54, "Transformation", "Трансформация", "ego"),
    (26, 44, "Surrender", "Передача (сдача)", "ego"),
    (19, 49, "Synthesis", "Синтез", "ego"),
    (37, 40, "Community", "Сообщество", "ego"),
    (21, 45, "Money", "Деньги (материалист)", "ego"),
    (6, 59, "Mating (Intimacy)", "Спаривание (близость)", "defense"),
    (27, 50, "Preservation", "Сохранение", "defense"),
]

# ---------------------------------------------------------------------------
# Тип, авторитет, профиль, определённость
# ---------------------------------------------------------------------------

TYPES: dict[str, dict] = {
    "generator": {"name_en": "Generator", "name_ru": "Генератор", "strategy_en": "To Respond",
                  "strategy_ru": "Откликаться (ждать, чтобы откликнуться)", "signature_en": "Satisfaction",
                  "signature_ru": "Удовлетворение", "not_self_en": "Frustration", "not_self_ru": "Фрустрация"},
    "manifesting_generator": {"name_en": "Manifesting Generator", "name_ru": "Манифестирующий Генератор",
                              "strategy_en": "To Respond", "strategy_ru": "Откликаться (затем информировать)",
                              "signature_en": "Satisfaction", "signature_ru": "Удовлетворение",
                              "not_self_en": "Frustration", "not_self_ru": "Фрустрация (и гнев)"},
    "manifestor": {"name_en": "Manifestor", "name_ru": "Манифестор", "strategy_en": "To Inform",
                   "strategy_ru": "Информировать перед действием", "signature_en": "Peace", "signature_ru": "Покой (мир)",
                   "not_self_en": "Anger", "not_self_ru": "Гнев"},
    "projector": {"name_en": "Projector", "name_ru": "Проектор", "strategy_en": "Wait for the Invitation",
                  "strategy_ru": "Ждать приглашения (признания)", "signature_en": "Success", "signature_ru": "Успех",
                  "not_self_en": "Bitterness", "not_self_ru": "Горечь"},
    "reflector": {"name_en": "Reflector", "name_ru": "Рефлектор", "strategy_en": "Wait a Lunar Cycle",
                  "strategy_ru": "Ждать лунный цикл (~29,5 дня) перед важным решением", "signature_en": "Surprise",
                  "signature_ru": "Удивление", "not_self_en": "Disappointment", "not_self_ru": "Разочарование"},
}

AUTHORITIES: dict[str, dict] = {
    "emotional":      {"name_en": "Emotional (Solar Plexus)", "name_ru": "Эмоциональный (Солнечное сплетение)",
                       "hint_ru": "решать не сразу: дождаться ясности после эмоциональной волны"},
    "sacral":         {"name_en": "Sacral", "name_ru": "Сакральный",
                       "hint_ru": "доверять телесному отклику «угу/ага» здесь и сейчас"},
    "splenic":        {"name_en": "Splenic", "name_ru": "Селезёночный",
                       "hint_ru": "мгновенное тихое интуитивное знание в моменте"},
    "ego_manifested": {"name_en": "Ego Manifested", "name_ru": "Эго-манифестированный (Сердце→Горло)",
                       "hint_ru": "что я хочу/чего желает сердце — сказанное вслух"},
    "ego_projected":  {"name_en": "Ego Projected", "name_ru": "Эго-проецированный (Сердце→G)",
                       "hint_ru": "что я хочу для себя — в ответ на приглашение"},
    "self_projected": {"name_en": "Self Projected", "name_ru": "Самопроецируемый (G→Горло)",
                       "hint_ru": "слушать, что говорю я сам, проговаривая с другими"},
    "mental":         {"name_en": "None / Sounding Board (Mental, Environmental)",
                       "name_ru": "Внешний / ментальный («звукоотражатель», среда)",
                       "hint_ru": "нет внутреннего авторитета: проговаривать с доверенными людьми и оценивать среду"},
    "lunar":          {"name_en": "Lunar (Wait a Lunar Cycle)", "name_ru": "Лунный",
                       "hint_ru": "решение созревает за полный лунный цикл"},
}

LINE_NAMES = {1: ("Investigator", "Исследователь"), 2: ("Hermit", "Отшельник"), 3: ("Martyr", "Мученик"),
              4: ("Opportunist", "Оппортунист"), 5: ("Heretic", "Еретик"), 6: ("Role Model", "Ролевая модель")}
VALID_PROFILES = ["1/3", "1/4", "2/4", "2/5", "3/5", "3/6", "4/6", "4/1", "5/1", "5/2", "6/2", "6/3"]

DEFINITIONS = {0: ("none", "No Definition", "Нет определённости"), 1: ("single", "Single Definition", "Одинарная"),
               2: ("split", "Split Definition", "Расщеплённая (split)"),
               3: ("triple_split", "Triple Split", "Тройное расщепление"),
               4: ("quadruple_split", "Quadruple Split", "Четверное расщепление")}

# ---------------------------------------------------------------------------
# Инкарнационные кресты (192 = 64 правоугловых + 64 джакстапозиций + 64 левоугловых).
# Имена — как в официальном приложении MyBodyGraph (Jovian Archive), ключ — ворота Солнца Личности.
# ---------------------------------------------------------------------------

RAX_FAMILIES: dict[str, tuple[str, list[int]]] = {
    # имя (англ.): (перевод, [ворота P-Солнца в четвертях 1..4])
    "Consciousness": ("Сознания", [63, 35, 64, 5]),
    "Contagion": ("Заразительности", [30, 8, 29, 14]),
    "Eden": ("Эдема", [36, 12, 6, 11]),
    "Explanation": ("Объяснения", [49, 23, 4, 43]),
    "The Four Ways": ("Четырёх путей", [24, 33, 44, 19]),
    "Laws": ("Законов", [3, 56, 50, 60]),
    "Maya": ("Майи", [42, 62, 32, 61]),
    "Penetration": ("Проникновения", [51, 53, 57, 54]),
    "Planning": ("Планирования", [37, 16, 40, 9]),
    "Rulership": ("Правления", [22, 45, 47, 26]),
    "Service": ("Служения", [17, 52, 18, 58]),
    "The Sleeping Phoenix": ("Спящего Феникса", [55, 20, 59, 34]),
    "The Sphinx": ("Сфинкса", [13, 2, 7, 1]),
    "Tension": ("Напряжения", [21, 39, 48, 38]),
    "The Unexpected": ("Неожиданного", [27, 31, 28, 41]),
    "The Vessel of Love": ("Сосуда Любви", [25, 15, 46, 10]),
}

JXP_NAMES: dict[int, tuple[str, str]] = {
    1: ("Self-expression", "Самовыражения"), 2: ("The Driver", "Водителя"), 3: ("Mutation", "Мутации"),
    4: ("Formulization", "Формулирования"), 5: ("Habits", "Привычек"), 6: ("Conflict", "Конфликта"),
    7: ("Interaction", "Взаимодействия"), 8: ("Contribution", "Вклада"), 9: ("Focus", "Фокуса"),
    10: ("Behavior", "Поведения"), 11: ("Ideas", "Идей"), 12: ("Articulation", "Артикуляции"),
    13: ("Listening", "Слушания"), 14: ("Empowering", "Наделения силой"), 15: ("Extremes", "Крайностей"),
    16: ("Experimentation", "Экспериментирования"), 17: ("Opinions", "Мнений"), 18: ("Correction", "Коррекции"),
    19: ("Need", "Нужды"), 20: ("The Now", "Настоящего момента"), 21: ("Control", "Контроля"),
    22: ("Grace", "Грации"), 23: ("Assimilation", "Ассимиляции"), 24: ("Rationalization", "Рационализации"),
    25: ("Innocence", "Невинности"), 26: ("The Trickster", "Трикстера"), 27: ("Caring", "Заботы"),
    28: ("Risks", "Рисков"), 29: ("Commitment", "Обязательства"), 30: ("Fates", "Судеб"),
    31: ("Influence", "Влияния"), 32: ("Conservation", "Сохранения"), 33: ("Retreat", "Отступления"),
    34: ("Power", "Силы"), 35: ("Experience", "Опыта"), 36: ("Crisis", "Кризиса"),
    37: ("Bargains", "Сделок"), 38: ("Opposition", "Оппозиции"), 39: ("Provocation", "Провокации"),
    40: ("Denial", "Отрицания"), 41: ("Fantasy", "Фантазии"), 42: ("Completion", "Завершения"),
    43: ("Insight", "Прозрения"), 44: ("Alertness", "Бдительности"), 45: ("Possession", "Обладания"),
    46: ("Serendipity", "Счастливой случайности"), 47: ("Oppression", "Угнетения"), 48: ("Depth", "Глубины"),
    49: ("Principles", "Принципов"), 50: ("Values", "Ценностей"), 51: ("Shock", "Шока"),
    52: ("Stillness", "Неподвижности"), 53: ("Beginnings", "Начал"), 54: ("Ambition", "Амбиций"),
    55: ("Moods", "Настроений"), 56: ("Stimulation", "Стимуляции"), 57: ("Intuition", "Интуиции"),
    58: ("Vitality", "Жизненности"), 59: ("Strategy", "Стратегии"), 60: ("Limitation", "Ограничения"),
    61: ("Thinking", "Мышления"), 62: ("Detail", "Детали"), 63: ("Doubts", "Сомнений"),
    64: ("Confusion", "Замешательства"),
}

LAX_NAMES: dict[str, tuple[str, tuple[int, int]]] = {
    # имя (англ.): (перевод, (ворота P-Солнца варианта 1, варианта 2)) — пары противоположных ворот
    "Alignment": ("Выравнивания", (27, 28)), "The Alpha": ("Альфы", (31, 41)),
    "The Clarion": ("Горна", (51, 57)), "Confrontation": ("Конфронтации", (45, 26)),
    "Cycles": ("Циклов", (53, 54)), "Dedication": ("Посвящения", (23, 43)),
    "Defiance": ("Неповиновения", (2, 1)), "Demands": ("Требований", (52, 58)),
    "Distraction": ("Отвлечения", (56, 60)), "Dominion": ("Господства", (63, 64)),
    "Duality": ("Двойственности", (20, 34)), "Education": ("Образования", (12, 11)),
    "Endeavor": ("Усилия", (21, 48)), "Healing": ("Исцеления", (25, 46)),
    "Identification": ("Идентификации", (16, 9)), "Incarnation": ("Воплощения", (24, 44)),
    "Individualism": ("Индивидуализма", (39, 38)), "Industry": ("Трудолюбия", (30, 29)),
    "Informing": ("Информирования", (22, 47)), "Limitation": ("Ограничения", (42, 32)),
    "Masks": ("Масок", (13, 7)), "Migration": ("Миграции", (37, 40)),
    "Obscuration": ("Затемнения", (62, 61)), "The Plane": ("Плоскости", (36, 6)),
    "Prevention": ("Предотвращения", (15, 10)), "Refinement": ("Утончённости", (33, 19)),
    "Revolution": ("Революции", (49, 4)), "Separation": ("Разделения", (35, 5)),
    "Spirit": ("Духа", (55, 59)), "Uncertainty": ("Неопределённости", (8, 14)),
    "Upheaval": ("Переворота", (17, 18)), "Wishes": ("Желаний", (3, 50)),
}

ANGLES = {"right": ("Right Angle Cross", "Правоугловой крест"),
          "juxtaposition": ("Juxtaposition Cross", "Крест джакстапозиции (джакстапозиционный)"),
          "left": ("Left Angle Cross", "Левоугловой крест")}

# Переменные (Variables): значения по цвету и подтипы по тону (тон 1–3 = левый, 4–6 = правый),
# названия — как в приложении MyBodyGraph.
VAR_DETERMINATION = {1: ("Appetite", "Аппетит", "Consecutive", "Alternating"),
                     2: ("Taste", "Вкус", "Open", "Closed"), 3: ("Thirst", "Жажда", "Hot", "Cold"),
                     4: ("Touch", "Прикосновение", "Calm", "Nervous"), 5: ("Sound", "Звук", "High", "Low"),
                     6: ("Light", "Свет", "Direct", "Indirect")}
VAR_COGNITION = {1: ("Smell", "Обоняние"), 2: ("Taste", "Вкус"), 3: ("Outer Vision", "Внешнее зрение"),
                 4: ("Inner Vision", "Внутреннее зрение"), 5: ("Feeling", "Чувствование"), 6: ("Touch", "Осязание")}
VAR_ENVIRONMENT = {1: ("Caves", "Пещеры", "Selective", "Blending"), 2: ("Markets", "Рынки", "Internal", "External"),
                   3: ("Kitchens", "Кухни", "Wet", "Dry"), 4: ("Mountains", "Горы", "Active", "Passive"),
                   5: ("Valleys", "Долины", "Narrow", "Wide"), 6: ("Shores", "Берега", "Natural", "Artificial")}
VAR_MOTIVATION = {1: ("Fear", "Страх"), 2: ("Hope", "Надежда"), 3: ("Desire", "Желание"),
                  4: ("Need", "Потребность"), 5: ("Guilt", "Вина"), 6: ("Innocence", "Невинность")}
VAR_SENSE = {1: ("Security", "Безопасность"), 2: ("Uncertainty", "Неопределённость"), 3: ("Action", "Действие"),
             4: ("Meditation", "Медитация"), 5: ("Judgment", "Суждение"), 6: ("Acceptance", "Принятие")}
VAR_VIEW = {1: ("Survival", "Выживание"), 2: ("Possibility", "Возможность"), 3: ("Power", "Сила"),
            4: ("Wanting", "Желание"), 5: ("Probability", "Вероятность"), 6: ("Personal", "Личное")}

PLANETS: list[str] = ["sun", "earth", "moon", "north_node", "south_node", "mercury", "venus", "mars",
                      "jupiter", "saturn", "uranus", "neptune", "pluto"]
PLANET_RU = {"sun": "Солнце", "earth": "Земля", "moon": "Луна", "north_node": "Северный узел",
             "south_node": "Южный узел", "mercury": "Меркурий", "venus": "Венера", "mars": "Марс",
             "jupiter": "Юпитер", "saturn": "Сатурн", "uranus": "Уран", "neptune": "Нептун", "pluto": "Плутон"}


# ---------------------------------------------------------------------------
# Базовые функции
# ---------------------------------------------------------------------------

def gate_start_longitude(gate: int) -> float:
    """Тропическая долгота начала ворот (°)."""
    return (WHEEL_START + GATE_INDEX[gate] * GATE_SPAN) % 360.0


def longitude_to_activation(lon: float) -> dict:
    """Долгота (тропическая, °) → ворота, линия, цвет, тон, база.

    x = (λ − 302°) mod 360; ворота = GATE_ORDER[⌊x/5.625⌋]; линия = ⌊(x mod 5.625)/0.9375⌋+1;
    цвет = ⌊(x mod 0.9375)/0.15625⌋+1; тон = ⌊(x mod 0.15625)/(0.15625/6)⌋+1;
    база = ⌊(x mod тон)/(тон/5)⌋+1.
    """
    x = (lon - WHEEL_START) % 360.0
    gi = int(x // GATE_SPAN)
    in_gate = x - gi * GATE_SPAN
    line = int(in_gate // LINE_SPAN)
    in_line = in_gate - line * LINE_SPAN
    color = int(in_line // COLOR_SPAN)
    in_color = in_line - color * COLOR_SPAN
    tone = int(in_color // TONE_SPAN)
    in_tone = in_color - tone * TONE_SPAN
    base = int(in_tone // BASE_SPAN)
    gate = GATE_ORDER[gi]
    line, color, tone, base = min(line, 5) + 1, min(color, 5) + 1, min(tone, 5) + 1, min(base, 4) + 1
    return {"gate": gate, "line": line, "color": color, "tone": tone, "base": base,
            "gate_line": f"{gate}.{line}", "deg_in_gate": round(in_gate, 6)}


def design_moment(jd_ut: float, arc: float = DESIGN_ARC) -> float:
    """JD(UT) момента Дизайна: Солнце на `arc` градусов дуги раньше натальной долготы."""
    target = (eph.sun_longitude(jd_ut) - arc) % 360.0
    return eph.find_sun_longitude(target, jd_ut, search_back=True)


def activations_at(jd_ut: float, node: str = "true") -> dict[str, dict]:
    """13 активаций (Солнце, Земля, Луна, узлы, Меркурий…Плутон) на момент jd_ut."""
    pp = eph.planet_positions(jd_ut, node=node)
    out: dict[str, dict] = {}
    for p in PLANETS:
        if p == "earth":
            lon, retro = (pp["sun"]["lon"] + 180.0) % 360.0, False
        else:
            lon, retro = pp[p]["lon"], pp[p]["retro"]
        a = longitude_to_activation(lon)
        g = GATES[a["gate"]]
        out[p] = {"planet": p, "planet_ru": PLANET_RU[p], "lon": round(lon, 6),
                  "lon_str": eph.format_lon(lon), **a, "center": g["center"],
                  "gate_name_en": g["en"], "gate_name_ru": g["ru"],
                  "retro": bool(retro) if p not in ("earth", "north_node", "south_node") else None}
    return out


# ---------------------------------------------------------------------------
# Анализ бодиграфа
# ---------------------------------------------------------------------------

def _components(nodes: set[str], edges: list[tuple[str, str]]) -> list[set[str]]:
    adj: dict[str, set[str]] = {n: set() for n in nodes}
    for a, b in edges:
        adj[a].add(b)
        adj[b].add(a)
    seen: set[str] = set()
    comps: list[set[str]] = []
    # обход в фиксированном порядке центров (а не в порядке хэшей множества), чтобы порядок
    # групп в definition.groups не зависел от PYTHONHASHSEED
    order = [c for c in CENTERS if c in nodes] + sorted(n for n in nodes if n not in CENTERS)
    for n in order:
        if n in seen:
            continue
        comp, q = set(), deque([n])
        seen.add(n)
        while q:
            x = q.popleft()
            comp.add(x)
            for y in adj[x]:
                if y not in seen:
                    seen.add(y)
                    q.append(y)
        comps.append(comp)
    return comps


def analyze_gates(personality_gates: set[int], design_gates: set[int]) -> dict:
    """Каналы, центры, тип, авторитет, определённость по множествам ворот."""
    all_gates = personality_gates | design_gates
    channels = []
    edges: list[tuple[str, str]] = []
    for a, b, en, ru, circ in CHANNELS:
        if a in all_gates and b in all_gates:
            ca, cb = GATES[a]["center"], GATES[b]["center"]
            edges.append((ca, cb))
            channels.append({"channel": f"{a}-{b}", "gates": [a, b], "name_en": en, "name_ru": ru,
                             "centers": [ca, cb], "circuit": circ, "circuit_ru": CIRCUITS[circ]["name_ru"],
                             "circuit_group": CIRCUITS[circ]["group"]})
    defined = {c for e in edges for c in e}
    comps = _components(defined, edges)
    comp_of = {c: i for i, comp in enumerate(comps) for c in comp}

    def connected(a: str, b: str) -> bool:
        return a in comp_of and b in comp_of and comp_of[a] == comp_of[b]

    motor_to_throat = [m for m in MOTORS if connected(m, "throat")]
    if not defined:
        t = "reflector"
    elif "sacral" in defined:
        t = "manifesting_generator" if motor_to_throat else "generator"
    else:
        t = "manifestor" if motor_to_throat else "projector"

    if t == "reflector":
        auth = "lunar"
    elif "solar_plexus" in defined:
        auth = "emotional"
    elif "sacral" in defined:
        auth = "sacral"
    elif "spleen" in defined:
        auth = "splenic"
    elif "heart" in defined:
        auth = "ego_manifested" if connected("heart", "throat") else "ego_projected"
    elif connected("g", "throat"):
        auth = "self_projected"
    else:
        auth = "mental"

    centers = {}
    for c, info in CENTERS.items():
        gates_here = sorted(g for g in all_gates if GATES[g]["center"] == c)
        centers[c] = {"name_ru": info["name_ru"], "name_en": info["name_en"], "defined": c in defined,
                      "gates": gates_here,
                      "state": "defined" if c in defined else ("undefined" if gates_here else "open")}
    n = len(comps)
    d_id, d_en, d_ru = DEFINITIONS[min(n, 4)]
    return {
        "channels": channels,
        "centers": centers,
        "defined_centers": [c for c in CENTERS if c in defined],
        "undefined_centers": [c for c in CENTERS if c not in defined],
        "open_centers": [c for c in CENTERS if centers[c]["state"] == "open"],
        "type_id": t,
        "motors_to_throat": motor_to_throat,
        "authority_id": auth,
        "definition": {"id": d_id, "name_en": d_en, "name_ru": d_ru, "components": len(comps),
                       "groups": [[c for c in CENTERS if c in comp] for comp in comps]},
    }


def _n_components(gates: set[int]) -> int:
    """Число связных групп определённых центров для множества активных ворот."""
    edges = [(GATES[a]["center"], GATES[b]["center"]) for a, b, *_ in CHANNELS if a in gates and b in gates]
    return len(_components({c for e in edges for c in e}, edges))


def split_bridges(all_gates: set[int]) -> dict | None:
    """«Мосты» расщеплённой (split) определённости — как поле chart.bridges официального движка
    Jovian Archive / MyBodyGraph (charts.maiamechanics.com/api/charts/free-chart; проверено 14.10.2026).

    * bridging_gates — ворота, каждые из которых по отдельности соединяют обе группы (простое расщепление,
      simple split). Пример движка: Эйнштейн → {"bridgingGates": [2, 34, 15, 29]}.
    * Если таких ворот нет — широкое расщепление (wide split); движок тогда отдаёт
      bridging_channels — каналы без активных ворот, напрямую соединяющие группы, и
      bridging_far_gates — ворота из пар, которые соединяют группы через неопределённый центр
      (каждые ворота пары замыкают канал с уже активными воротами). Пример движка: Джобс →
      bridgingChannels ["34/20", "12/22", "35/36"], bridgingFarGates [20, 34, 5, 46, 8, 33, 18, 48, 27].
    * Признак wide в приложении MyBodyGraph (app.mybodygraph.com/js/app.*.js):
      isWideSplit = bridgingChannels || bridgingFarGates.
    Для одинарной, тройной и четверной определённости возвращает None (вкладка «Bridges» у движка
    показывается только при definition = SPLIT).
    """
    if _n_components(all_gates) != 2:
        return None
    # кандидаты: ворота, замыкающие канал с уже активными воротами
    candidates = sorted({b if a in all_gates else a for a, b, *_ in CHANNELS
                         if (a in all_gates) != (b in all_gates)})
    single = [g for g in candidates if _n_components(all_gates | {g}) == 1]
    if single:
        return {"kind": "simple", "name_en": "Simple Split", "name_ru": "простое расщепление",
                "bridging_gates": single, "bridging_channels": [], "bridging_far_gates": []}
    channels = [f"{a}-{b}" for a, b, *_ in CHANNELS if a not in all_gates and b not in all_gates
                and _n_components(all_gates | {a, b}) == 1]
    pairs_as_channel = {frozenset((a, b)) for a, b, *_ in CHANNELS}
    far: set[int] = set()
    for i, g in enumerate(candidates):
        for h in candidates[i + 1:]:
            # пара, которая сама образует канал, — это «канал-мост», а не «дальние ворота» (вывод по ответу
            # движка для Джобса: 12, 22, 35, 36 из каналов-мостов в bridgingFarGates не входят)
            if (g in far and h in far) or frozenset((g, h)) in pairs_as_channel:
                continue
            if _n_components(all_gates | {g, h}) == 1:
                far.update((g, h))
    return {"kind": "wide", "name_en": "Wide Split", "name_ru": "широкое расщепление",
            "bridging_gates": [], "bridging_channels": channels, "bridging_far_gates": sorted(far)}


def profile_angle(p_line: int, d_line: int) -> str:
    """Угол креста по профилю: 4/1 — джакстапозиция; линия Личности 5–6 — левый; иначе правый."""
    if p_line == 4 and d_line == 1:
        return "juxtaposition"
    return "left" if p_line >= 5 else "right"


def incarnation_cross(p_sun: int, p_earth: int, d_sun: int, d_earth: int, angle: str) -> dict:
    """Имя инкарнационного креста по углу и воротам Солнца Личности."""
    q = _quarter_index(p_sun)
    gates_str = f"{p_sun}/{p_earth} | {d_sun}/{d_earth}"
    if angle == "right":
        fam = next(f for f, (_, gl) in RAX_FAMILIES.items() if p_sun in gl)
        name, name_ru = fam, RAX_FAMILIES[fam][0]
        variant = RAX_FAMILIES[fam][1].index(p_sun) + 1
    elif angle == "juxtaposition":
        name, name_ru = JXP_NAMES[p_sun]
        variant = None
    else:
        name = next(f for f, (_, pair) in LAX_NAMES.items() if p_sun in pair)
        name_ru = LAX_NAMES[name][0]
        variant = None
    # номинальные ворота дизайна: −16 ворот по колесу (правый угол) или −15 (джакстапозиция, левый)
    shift = 16 if angle == "right" else 15
    nd_sun = GATE_ORDER[(GATE_INDEX[p_sun] - shift) % 64]
    nd_earth = GATE_ORDER[(GATE_INDEX[nd_sun] + 32) % 64]
    en_angle, ru_angle = ANGLES[angle]
    return {
        "angle": angle, "angle_en": en_angle, "angle_ru": ru_angle,
        "name": name,
        "name_en": f"{en_angle} of {name} ({gates_str})",
        "name_ru": f"{ru_angle} {name_ru} ({gates_str})",
        "gates": {"personality_sun": p_sun, "personality_earth": p_earth,
                  "design_sun": d_sun, "design_earth": d_earth},
        "notation": gates_str,
        "nominal_design_gates_match": (nd_sun, nd_earth) == (d_sun, d_earth),
        "quarter": QUARTERS[q]["id"], "quarter_ru": QUARTERS[q]["name_ru"],
        "quarter_theme_ru": QUARTERS[q]["theme_ru"],
        "rax_number": variant,
    }


def variables(p: dict[str, dict], d: dict[str, dict]) -> dict:
    """Переменные (4 стрелки) по цвету/тону Солнца и Северного узла Дизайна и Личности."""
    def lr(tone: int) -> str:
        return "L" if tone <= 3 else "R"

    ds, dn, ps, pn = d["sun"], d["north_node"], p["sun"], p["north_node"]
    det = VAR_DETERMINATION[ds["color"]]
    env = VAR_ENVIRONMENT[dn["color"]]
    motivation = VAR_MOTIVATION[ps["color"]]
    transference = VAR_MOTIVATION[(ps["color"] + 2) % 6 + 1]
    view = VAR_VIEW[pn["color"]]
    return {
        "notation": f"P{lr(ps['tone'])}{lr(pn['tone'])} D{lr(ds['tone'])}{lr(dn['tone'])}",
        "arrows": {"design_sun": lr(ds["tone"]), "design_node": lr(dn["tone"]),
                   "personality_sun": lr(ps["tone"]), "personality_node": lr(pn["tone"])},
        "determination": {"color": ds["color"], "tone": ds["tone"], "name_en": det[0], "name_ru": det[1],
                          "subtype": det[2] if ds["tone"] <= 3 else det[3]},
        "cognition": {"tone": ds["tone"], "name_en": VAR_COGNITION[ds["tone"]][0],
                      "name_ru": VAR_COGNITION[ds["tone"]][1]},
        "environment": {"color": dn["color"], "tone": dn["tone"], "name_en": env[0], "name_ru": env[1],
                        "subtype": env[2] if dn["tone"] <= 3 else env[3]},
        "motivation": {"color": ps["color"], "tone": ps["tone"], "name_en": motivation[0], "name_ru": motivation[1],
                       "subtype": "Strategic" if ps["tone"] <= 3 else "Receptive",
                       "transference_en": transference[0], "transference_ru": transference[1]},
        "sense": {"tone": ps["tone"], "name_en": VAR_SENSE[ps["tone"]][0], "name_ru": VAR_SENSE[ps["tone"]][1]},
        "view": {"color": pn["color"], "tone": pn["tone"], "name_en": view[0], "name_ru": view[1],
                 "subtype": "Focused" if pn["tone"] <= 3 else "Peripheral"},
    }


def chart_from_jd(jd_ut: float, node: str = "true", design_arc: float = DESIGN_ARC) -> dict:
    """Полный бодиграф по JD(UT) рождения (без нормализации времени)."""
    jd_d = design_moment(jd_ut, design_arc)
    p = activations_at(jd_ut, node)
    d = activations_at(jd_d, node)
    an = analyze_gates({a["gate"] for a in p.values()}, {a["gate"] for a in d.values()})
    p_line, d_line = p["sun"]["line"], d["sun"]["line"]
    angle = profile_angle(p_line, d_line)
    cross = incarnation_cross(p["sun"]["gate"], p["earth"]["gate"], d["sun"]["gate"], d["earth"]["gate"], angle)
    t = TYPES[an["type_id"]]
    a = AUTHORITIES[an["authority_id"]]
    gates_map: dict[int, dict] = {}
    for side, acts in (("personality", p), ("design", d)):
        for pl, act in acts.items():
            gates_map.setdefault(act["gate"], {"personality": [], "design": []})[side].append(pl)
    return {
        "jd_design": jd_d,
        "personality": p,
        "design": d,
        "gates": {str(g): {**v, "center": GATES[g]["center"], "name_ru": GATES[g]["ru"]}
                  for g, v in sorted(gates_map.items())},
        **{k: v for k, v in an.items() if k not in ("type_id", "authority_id")},
        "type": {"id": an["type_id"], **t},
        "authority": {"id": an["authority_id"], **a},
        "profile": {"profile": f"{p_line}/{d_line}", "personality_line": p_line, "design_line": d_line,
                    "name_en": f"{LINE_NAMES[p_line][0]} / {LINE_NAMES[d_line][0]}",
                    "name_ru": f"{LINE_NAMES[p_line][1]} / {LINE_NAMES[d_line][1]}",
                    "valid": f"{p_line}/{d_line}" in VALID_PROFILES},
        "incarnation_cross": cross,
        "variables": variables(p, d),
    }


# ---------------------------------------------------------------------------
# Публичный API
# ---------------------------------------------------------------------------

def _short(acts: dict[str, dict]) -> dict[str, str]:
    return {pl: a["gate_line"] for pl, a in acts.items()}


def calculate(b: BirthInput, node: str = "true", design_arc: float = DESIGN_ARC,
              unknown_time: str = "noon", **_ignored) -> dict:
    """Бодиграф Дизайна Человека.

    Параметры:
      node: 'true' (истинный узел, по умолчанию — как Jovian Archive/MyBodyGraph) | 'mean'
      design_arc: дуга Солнца между Дизайном и Личностью, по умолчанию 88.0°
      unknown_time: при отсутствии времени — 'noon' (карта на 12:00 + анализ изменчивости за сутки)
    """
    if node not in ("true", "mean"):
        raise ValueError("node: 'true' или 'mean'")
    warnings: list[str] = []
    steps: list[dict] = []
    time_known = b.has_time
    if not time_known:
        if unknown_time != "noon":
            raise ValueError("Время рождения неизвестно; поддерживается только unknown_time='noon'.")
        b_calc = BirthInput(b.year, b.month, b.day, 12, 0, tz=b.tz, lat=b.lat, lon=b.lon, place=b.place)
        warnings.append("Время рождения неизвестно: карта построена на 12:00 местного времени. Луна за сутки "
                        "проходит ~2–3 ворот, поэтому её ворота (и иногда линии других тел, профиль, каналы, тип) "
                        "ненадёжны — см. блок time_sensitivity.")
    else:
        b_calc = b
    if b_calc.tz is None:
        raise ValueError("Нужен часовой пояс (tz) или место (place): Дизайн Человека требует точный момент UTC.")
    nt = normalize(b_calc)
    warnings.extend(nt.warnings)
    if node == "mean":
        warnings.append("Выбран средний узел: Jovian Archive/MyBodyGraph используют истинный узел; ворота/линии "
                        "узлов могут отличаться от официальной карты.")
    if abs(design_arc - DESIGN_ARC) > 1e-9:
        warnings.append(f"Нестандартная дуга Дизайна {design_arc}° (стандарт — 88°).")

    ch = chart_from_jd(nt.jd_ut, node, design_arc)
    jd_d = ch.pop("jd_design")
    ch["definition"]["bridges"] = split_bridges({int(g) for g in ch["gates"]})
    design_utc = jd_to_utc(jd_d)
    p, d = ch["personality"], ch["design"]

    # --- шаги ---
    steps.append({"step": "1. Местное время → UTC → JD",
                  "detail": f"{nt.local:%Y-%m-%d %H:%M} ({b_calc.tz}, {fmt_offset(nt.utc_offset_hours)}, "
                            f"источник: {nt.offset_source}) → {nt.utc:%Y-%m-%d %H:%M:%S} UTC; JD(UT) = {nt.jd_ut:.6f}"})
    ps_lon = p["sun"]["lon"]
    steps.append({"step": "2. Момент Дизайна (Солнце на 88° раньше)",
                  "detail": f"λ☉(рождение) = {ps_lon:.4f}° ({p['sun']['lon_str']}); цель = {ps_lon:.4f} − {design_arc} = "
                            f"{(ps_lon - design_arc) % 360:.4f}°; найдено {design_utc:%Y-%m-%d %H:%M:%S} UTC "
                            f"(JD {jd_d:.6f}), за {nt.jd_ut - jd_d:.2f} сут до рождения"})
    steps.append({"step": "3. Долгота → ворота.линия",
                  "detail": "x = (λ − 302°) mod 360; ворота = порядок_колеса[⌊x/5.625⌋]; линия = ⌊(x mod 5.625)/0.9375⌋+1. "
                            f"Пример: Солнце Личности λ = {ps_lon:.4f}°, x = {(ps_lon - WHEEL_START) % 360:.4f}, "
                            f"индекс {int(((ps_lon - WHEEL_START) % 360) // GATE_SPAN)} → ворота {p['sun']['gate']}, "
                            f"в воротах {p['sun']['deg_in_gate']:.4f}° → линия {p['sun']['line']}"})
    steps.append({"step": "4. Активации Личности (рождение)", "detail": ", ".join(
        f"{PLANET_RU[k]} {v['gate_line']}" for k, v in p.items())})
    steps.append({"step": "5. Активации Дизайна (−88°)", "detail": ", ".join(
        f"{PLANET_RU[k]} {v['gate_line']}" for k, v in d.items())})
    steps.append({"step": "6. Каналы (обе ворота канала активированы)",
                  "detail": "; ".join(f"{c['channel']} {c['name_ru']}" for c in ch["channels"]) or "нет каналов"})
    steps.append({"step": "7. Центры", "detail": "определены: " + (", ".join(
        CENTERS[c]["name_ru"] for c in ch["defined_centers"]) or "нет")})
    steps.append({"step": "8. Тип", "detail": f"{ch['type']['name_ru']}: сакрал {'определён' if 'sacral' in ch['defined_centers'] else 'не определён'}; "
                  f"моторы, связанные с Горлом: {', '.join(CENTERS[m]['name_ru'] for m in ch['motors_to_throat']) or 'нет'}"})
    steps.append({"step": "9. Авторитет (иерархия: Солн. сплетение > Сакрал > Селезёнка > Сердце > G→Горло > внешний; "
                          "Рефлектор — лунный)", "detail": ch["authority"]["name_ru"]})
    steps.append({"step": "10. Профиль = линия Солнца Личности / линия Солнца Дизайна",
                  "detail": f"{p['sun']['gate_line']} / {d['sun']['gate_line']} → {ch['profile']['profile']} "
                            f"({ch['profile']['name_ru']})"})
    br = ch["definition"]["bridges"]
    br_txt = ""
    if br and br["kind"] == "simple":
        br_txt = f"; простое расщепление (simple split), мосты-ворота: {', '.join(map(str, br['bridging_gates']))}"
    elif br:
        br_txt = (f"; широкое расщепление (wide split): одних ворот мало; каналы-мосты: "
                  f"{', '.join(br['bridging_channels']) or 'нет'}; дальние ворота (пары через неопределённый центр): "
                  f"{', '.join(map(str, br['bridging_far_gates'])) or 'нет'}")
    steps.append({"step": "11. Определённость (число связных групп определённых центров)",
                  "detail": f"{ch['definition']['components']} → {ch['definition']['name_ru']}{br_txt}"})
    cr = ch["incarnation_cross"]
    steps.append({"step": "12. Инкарнационный крест (Солнце/Земля Личности | Солнце/Земля Дизайна; угол по профилю)",
                  "detail": f"{cr['name_ru']} — {cr['name_en']}; {cr['quarter_ru']}"})
    steps.append({"step": "13. Переменные (тон 1–3 = L, 4–6 = R)", "detail": ch["variables"]["notation"]})

    if not ch["profile"]["valid"]:
        warnings.append("Невозможный профиль — проверьте расчёт момента Дизайна.")
    if not cr["nominal_design_gates_match"]:
        warnings.append("Ворота Дизайна креста не совпали с номинальными — проверьте расчёт.")

    result = {
        "method": "human_design",
        "variant": f"Jovian Archive (Ra Uru Hu): тропический зодиак, Дизайн = Солнце −{design_arc:g}°, "
                   f"узел {'истинный' if node == 'true' else 'средний'}, колесо от 302° (ворота 41)",
        "inputs_used": {
            "date": f"{b.year:04d}-{b.month:02d}-{b.day:02d}",
            "time": f"{b_calc.hour:02d}:{(b_calc.minute or 0):02d}"
                    + (f":{getattr(b_calc, 'second', 0):02d}" if getattr(b_calc, "second", 0) else "")
                    + ("" if time_known else " (подставлено)"),
            "julian_date_input": getattr(b, "julian_date", None),
            "time_known": time_known, "tz": b_calc.tz, "utc_offset": fmt_offset(nt.utc_offset_hours),
            "offset_source": nt.offset_source, "utc": nt.utc.isoformat(), "jd_ut": round(nt.jd_ut, 6),
            "lat": b.lat, "lon": b.lon, "place": b.place, "node": node, "design_arc": design_arc,
            "design_utc": design_utc.isoformat(), "jd_design": round(jd_d, 6),
        },
        "warnings": warnings,
        "personality_short": _short(p),
        "design_short": _short(d),
        **ch,
        "steps": steps,
    }
    if not time_known:
        result["time_sensitivity"] = _day_sensitivity(b, node, design_arc)
    return result


def _day_sensitivity(b: BirthInput, node: str, design_arc: float) -> dict:
    """Что меняется за сутки, если время неизвестно: перебор с шагом 1 ч (00:00…23:59 местного)."""
    seen: dict[str, set] = {k: set() for k in ("type", "authority", "profile", "definition", "cross")}
    acts: dict[str, set] = {}
    for h in list(range(0, 24)) + [23.99]:
        hh, mm = int(h), int(round((h - int(h)) * 60))
        nt = normalize(BirthInput(b.year, b.month, b.day, hh, mm, tz=b.tz, lat=b.lat, lon=b.lon, place=b.place))
        ch = chart_from_jd(nt.jd_ut, node, design_arc)
        seen["type"].add(ch["type"]["id"])
        seen["authority"].add(ch["authority"]["id"])
        seen["profile"].add(ch["profile"]["profile"])
        seen["definition"].add(ch["definition"]["id"])
        seen["cross"].add(ch["incarnation_cross"]["name_en"].split(" (")[0])
        for side in ("personality", "design"):
            for pl, a in ch[side].items():
                acts.setdefault(f"{side}.{pl}", set()).add(a["gate_line"])
    return {
        "possible": {k: sorted(v) for k, v in seen.items()},
        "stable": {k: len(v) == 1 for k, v in seen.items()},
        "variable_activations": {k: sorted(v) for k, v in acts.items() if len(v) > 1},
    }
