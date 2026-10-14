"""Матрица судьбы (метод 22 арканов, школа Натальи Ладини) по дате рождения.

Что считает (все точки, буквенные обозначения — см. knowledge-base/10-destiny-matrix.md):

* личный квадрат (ромб): A — день, B — месяц, C — год, D = A+B+C, центр E = A+B+C+D;
* родовой квадрат: F = A+B, G = B+C, I = C+D, H = D+A и его центр
  R = F+G+H+I («аркан силы рода», рисуется справа от центра; в документации — «Rod»,
  чтобы не путать с функцией свёртки);
* внутренние точки линий: A1, A2, A3; B1, B2, B3; C1, C2; D1, D2
  (для вершины K: K2 = K+E, K1 = K+K2, K3 = K2+E);
* внутренние точки диагоналей рода: F1, F2 … I1, I2 (для угла K: K2 = K+R, K1 = K+K2);
* центр линии талантов TAL = A2+B2;
* денежный канал и канал отношений в двух вариантах школ;
* кармический хвост D2-D1-D;
* предназначения (личное, социальное, духовное, планетарное);
* карту здоровья (7 чакр × физика/энергия/эмоции + итог);
* 64 возрастные точки внешнего кольца (0–80 лет) и аркан текущего периода.

Правило свёртки по умолчанию — сложение цифр, пока число > 22 (22 остаётся 22).
Вариант ``reduction="minus22"`` вычитает 22.

Время и место рождения не нужны.
"""
from __future__ import annotations

from datetime import date
from typing import Any

from .common.time import BirthInput

METHOD = "destiny_matrix"

#: Допустимые значения опций.
REDUCTION_RULES = ("digits", "minus22")
SVADHISTHANA_RULES = ("classic", "matrica_sudby")
ANCESTRAL_INNER_RULES = ("rod_center", "personal_center")
HEALTH_TOTAL_RULES = ("sum_of_totals", "sum_of_rows")
#: Все опции, которые понимает ``calculate``; остальные игнорируются с предупреждением.
KNOWN_OPTIONS = frozenset({"reduction", "svadhisthana", "ancestral_inner", "health_total", "on_date", "age"})

# ---------------------------------------------------------------------------
# Справочные таблицы
# ---------------------------------------------------------------------------

#: 22 старших аркана в нумерации Матрицы судьбы (8 — Справедливость, 11 — Сила).
ARCANA: dict[int, dict[str, str]] = {
    1: {"name": "Маг", "plus": "воля, инициатива, умение начинать, слово и коммуникация",
        "minus": "манипуляции, обман, распыление, неумение довести до конца"},
    2: {"name": "Верховная Жрица", "plus": "интуиция, знание, наблюдательность, мягкая сила",
        "minus": "скрытность, пассивность, страхи, сплетни, обида"},
    3: {"name": "Императрица", "plus": "женственность, изобилие, творчество, забота, материнство",
        "minus": "критичность, расточительство, лень, жёсткость, проблемы с зачатием"},
    4: {"name": "Император", "plus": "лидерство, порядок, структура, ответственность, защита",
        "minus": "контроль, тирания, жёсткость, упрямство"},
    5: {"name": "Иерофант (Жрец)", "plus": "наставничество, традиции, мораль, обучение",
        "minus": "догматизм, морализаторство, лицемерие, нежелание учиться"},
    6: {"name": "Влюблённые", "plus": "любовь, выбор сердцем, красота, гармония в отношениях",
        "minus": "нерешительность, зависимость от партнёра, ревность, измены"},
    7: {"name": "Колесница", "plus": "движение, победа, целеустремлённость, путешествия",
        "minus": "агрессия, спешка, конфликты, трудоголизм, неумение остановиться"},
    8: {"name": "Справедливость", "plus": "честность, объективность, закон, баланс, умение предвидеть последствия",
        "minus": "осуждение, категоричность, жестокость, злопамятность, судебные тяжбы"},
    9: {"name": "Отшельник", "plus": "мудрость, глубина, самопознание, экспертность",
        "minus": "изоляция, замкнутость, депрессия, отказ делиться знаниями"},
    10: {"name": "Колесо Фортуны", "plus": "удача, поток, перемены, доверие жизни",
         "minus": "фатализм, азарт, нестабильность, «колесо» повторяющихся ситуаций"},
    11: {"name": "Сила", "plus": "сила воли, выносливость, активность, целеустремлённость, работоспособность",
         "minus": "грубость, вспыльчивость, тирания, упрямство; или апатия и лень"},
    12: {"name": "Повешенный", "plus": "служение, творчество, иной взгляд, способность отпускать",
         "minus": "жертвенность, застой, зависимости, ощущение безысходности"},
    13: {"name": "Смерть (Трансформация)", "plus": "обновление, умение завершать, трансформация",
         "minus": "страх перемен, разрушение, застревание в прошлом, экстрим"},
    14: {"name": "Умеренность", "plus": "гармония, мера, спокойствие, исцеление, творчество",
         "minus": "крайности, нетерпение, отсутствие меры, зависимости"},
    15: {"name": "Дьявол", "plus": "харизма, страсть, деньги, влияние, магнетизм",
         "minus": "зависимости, манипуляции, алчность, искушения"},
    16: {"name": "Башня", "plus": "освобождение, прорыв, строительство нового, духовный рост",
         "minus": "гордыня, разрушения, кризисы, потеря опоры"},
    17: {"name": "Звезда", "plus": "вдохновение, талант, надежда, известность, творчество",
         "minus": "звёздная болезнь, разочарование, оторванность от реальности"},
    18: {"name": "Луна", "plus": "интуиция, воображение, глубина, мистика",
         "minus": "страхи, иллюзии, тревожность, обман и самообман"},
    19: {"name": "Солнце", "plus": "радость, успех, щедрость, жизненная сила, дети",
         "minus": "эгоцентризм, тщеславие, выгорание, самолюбование"},
    20: {"name": "Суд", "plus": "род, призвание, возрождение, семейные ценности",
         "minus": "осуждение, вина, конфликты с родом, непринятие"},
    21: {"name": "Мир", "plus": "целостность, свобода, мир без границ, завершение циклов",
         "minus": "ограничения, незавершённость, страх перемен и масштаба"},
    22: {"name": "Шут", "plus": "свобода, лёгкость, новое начало, спонтанность",
         "minus": "безответственность, хаос, инфантильность, безрассудство"},
}

#: Описание точек: ключ -> (название, формула, где на схеме).
POINT_INFO: dict[str, tuple[str, str, str]] = {
    "A": ("Левая вершина личного квадрата (портрет, «визитная карточка»)", "день рождения", "слева, 0 лет"),
    "B": ("Верхняя вершина (таланты от Бога)", "месяц рождения", "сверху, 20 лет"),
    "C": ("Правая вершина (материальная сфера)", "сумма цифр года", "справа, 40 лет"),
    "D": ("Нижняя вершина (карма прошлого воплощения, кармический хвост)", "A+B+C", "снизу, 60 лет"),
    "E": ("Центр — зона комфорта", "A+B+C+D", "центр"),
    "F": ("Левый верхний угол родового квадрата — род отца (мужской род), верх", "A+B", "10 лет"),
    "G": ("Правый верхний угол — род матери (женский род), верх", "B+C", "30 лет"),
    "I": ("Правый нижний угол — род отца (мужской род), низ", "C+D", "50 лет"),
    "H": ("Левый нижний угол — род матери (женский род), низ", "D+A", "70 лет"),
    "R": ("Центр родового квадрата — аркан силы рода", "F+G+H+I", "справа от центра"),
    "A1": ("Линия A, 2-я точка (Аджна, физика; детско-родительский канал)", "A+A2", "рядом с A"),
    "A2": ("Линия A, 3-я точка (Вишудха, физика; детско-родительский канал)", "A+E", "на стороне родового квадрата"),
    "A3": ("Линия A, 4-я точка (Анахата, физика)", "A2+E", "ближе к центру"),
    "B1": ("Линия B, 2-я точка (Аджна, энергия; таланты)", "B+B2", "рядом с B"),
    "B2": ("Линия B, 3-я точка (Вишудха, энергия; таланты)", "B+E", "на стороне родового квадрата"),
    "B3": ("Линия B, 4-я точка (Анахата, энергия)", "B2+E", "ближе к центру"),
    "C1": ("Линия C, внешняя внутренняя точка", "C+C2", "рядом с C"),
    "C2": ("Линия C, точка у центра (Свадхистана, физика — классика; «за что платят»)", "C+E",
           "на стороне родового квадрата"),
    "D1": ("Кармический хвост, средняя точка", "D+D2", "рядом с D"),
    "D2": ("Кармический хвост, точка у центра (Свадхистана, энергия — классика; вход в каналы)", "D+E",
           "на стороне родового квадрата"),
    "F1": ("Мужской род, верх, 2-я точка", "F+F2", "рядом с F"),
    "F2": ("Мужской род, верх, 3-я точка", "F+R", "по диагонали к центру"),
    "G1": ("Женский род, верх, 2-я точка", "G+G2", "рядом с G"),
    "G2": ("Женский род, верх, 3-я точка", "G+R", "по диагонали к центру"),
    "I1": ("Мужской род, низ, 2-я точка", "I+I2", "рядом с I"),
    "I2": ("Мужской род, низ, 3-я точка", "I+R", "по диагонали к центру"),
    "H1": ("Женский род, низ, 2-я точка", "H+H2", "рядом с H"),
    "H2": ("Женский род, низ, 3-я точка", "H+R", "по диагонали к центру"),
    "TAL": ("Центр линии талантов (между A2 и B2)", "A2+B2", "на мужской диагонали, слева сверху"),
    "X": ("Центр денежного канала / канала отношений", "C2+D2", "на диагонали к I, $"),
    "X_money": ("Аркан «под долларом» (классическая схема)", "X+C2", "между X и C2"),
    "X_love": ("Аркан «под сердцем» (классическая схема)", "X+D2", "между X и D2"),
    "Y": ("Третья энергия канала отношений (схема matrica-sudby.ru)", "C1+D1", "на диагонали к I, за X"),
}

#: Порядок точек кольца по часовой стрелке и возраст главных точек.
RING_ORDER: tuple[tuple[str, int], ...] = (
    ("A", 0), ("F", 10), ("B", 20), ("G", 30), ("C", 40), ("I", 50), ("D", 60), ("H", 70),
)

#: Подпись и смещение (в годах от начала десятилетия) восьми точек одного десятилетия.
#: «age» — условная позиция точки на кольце, «start» — начало периода её действия.
DECADE_SLOTS: tuple[dict[str, Any], ...] = (
    {"slot": "start", "age": 0.0, "start": 0.0},
    {"slot": "e1", "age": 1.25, "start": 1.0},
    {"slot": "q1", "age": 2.5, "start": 2.5},
    {"slot": "e2", "age": 3.75, "start": 3.5},
    {"slot": "mid", "age": 5.0, "start": 5.0},
    {"slot": "e3", "age": 6.25, "start": 6.0},
    {"slot": "q3", "age": 7.5, "start": 7.5},
    {"slot": "e4", "age": 8.75, "start": 8.5},
)

#: Описание чакр для карты здоровья.
CHAKRAS: tuple[tuple[str, str], ...] = (
    ("Сахасрара", "мозг, волосы, верхняя часть черепа; связь с высшим, миссия"),
    ("Аджна", "глаза, уши, лицо; логика и интуиция"),
    ("Вишудха", "горло, щитовидная железа, плечи, руки; самовыражение"),
    ("Анахата", "сердце, лёгкие, бронхи, грудь; любовь, отношения"),
    ("Манипура", "ЖКТ, печень, желчный пузырь, позвоночник; воля, финансы"),
    ("Свадхистана", "репродуктивная и выделительная системы, почки; радость, безопасность"),
    ("Муладхара", "ноги, крестец, мочеполовая система; тело, выживание"),
)


# ---------------------------------------------------------------------------
# Свёртка
# ---------------------------------------------------------------------------

def digit_sum(n: int) -> int:
    """Сумма цифр натурального числа."""
    return sum(int(c) for c in str(abs(n)))


def reduce_arcana(n: int, rule: str = "digits") -> int:
    """Свернуть натуральное число к аркану 1..22.

    * ``digits`` (по умолчанию, школа Ладини и большинство калькуляторов):
      пока число > 22 — сложить его цифры (23 → 5, 28 → 10, 47 → 11);
    * ``minus22``: пока число > 22 — вычесть 22 (23 → 1, 47 → 3).

    22 и меньше не меняются; 0 в Матрице не встречается, но на всякий случай → 22.
    """
    if rule not in REDUCTION_RULES:
        raise ValueError(f"reduction должен быть одним из {REDUCTION_RULES}")
    if n < 0:
        raise ValueError("Отрицательное число не сворачивается")
    if n == 0:
        return 22
    while n > 22:
        n = digit_sum(n) if rule == "digits" else n - 22
    return n


class _Builder:
    """Считает точки с записью каждого шага (для поля ``steps``)."""

    def __init__(self, rule: str) -> None:
        self.rule = rule
        self.v: dict[str, int] = {}
        self.formula: dict[str, str] = {}
        self.steps: list[str] = []

    def _reduce_text(self, total: int) -> tuple[int, str]:
        value = reduce_arcana(total, self.rule)
        if total <= 22:
            return value, f"{total}"
        chain = [str(total)]
        n = total
        while n > 22:
            if self.rule == "digits":
                digits = "+".join(str(n))
                n = digit_sum(n)
                chain.append(f"({digits}) {n}")
            else:
                n -= 22
                chain.append(f"(−22) {n}")
        return value, " → ".join(chain)

    def set(self, key: str, value: int, note: str) -> int:
        self.v[key] = value
        self.formula[key] = note
        self.steps.append(f"{key} = {note}")
        return value

    def add(self, key: str, *terms: str) -> int:
        """key = свёртка(сумма точек terms)."""
        nums = [self.v[t] for t in terms]
        total = sum(nums)
        value, red = self._reduce_text(total)
        expr = "+".join(terms)
        nums_txt = " + ".join(str(x) for x in nums)
        self.v[key] = value
        self.formula[key] = expr
        self.steps.append(f"{key} = {expr} = {nums_txt} = {red}")
        return value

    def add_values(self, label: str, nums: list[int], expr: str) -> int:
        """Свёртка суммы произвольных значений (для карты здоровья и кольца)."""
        total = sum(nums)
        value, red = self._reduce_text(total)
        self.steps.append(f"{label} = {expr} = {' + '.join(str(x) for x in nums)} = {red}")
        return value


# ---------------------------------------------------------------------------
# Основной расчёт
# ---------------------------------------------------------------------------

def _decade_label(base: int, slot: str) -> str:
    """Подпись точки кольца, как на схемах matrica-sudby.ru («11–12,5», «15 лет»)."""
    labels = {
        "start": f"{base} лет",
        "e1": f"{base + 1}–{base + 2},5",
        "q1": f"{base + 2},5–{base + 3},5",
        "e2": f"{base + 3},5–{base + 4}",
        "mid": f"{base + 5} лет",
        "e3": f"{base + 6}–{base + 7},5",
        "q3": f"{base + 7},5–{base + 8},5",
        "e4": f"{base + 8},5–{base + 9}",
    }
    return labels[slot]


def compute_age_ring(points: dict[str, int], rule: str = "digits",
                     steps: list[str] | None = None) -> list[dict[str, Any]]:
    """64 точки внешнего кольца (возрастные точки 0–80 лет).

    Между двумя соседними главными точками P0 (возраст a) и P10 (a+10):
    mid(5) = P0+P10; q1(2,5) = P0+mid; q3(7,5) = mid+P10;
    e1(1–2,5) = P0+q1; e2(3,5–4) = q1+mid; e3(6–7,5) = mid+q3; e4(8,5–9) = q3+P10.
    """
    ring: list[dict[str, Any]] = []
    for idx, (key0, base) in enumerate(RING_ORDER):
        key10 = RING_ORDER[(idx + 1) % len(RING_ORDER)][0]
        p0, p10 = points[key0], points[key10]

        def r(*xs: int) -> int:
            return reduce_arcana(sum(xs), rule)

        mid = r(p0, p10)
        q1 = r(p0, mid)
        q3 = r(mid, p10)
        vals = {
            "start": (p0, key0),
            "e1": (r(p0, q1), f"{key0}+q({base + 2.5:g})"),
            "q1": (q1, f"{key0}+mid({base + 5})"),
            "e2": (r(q1, mid), f"q({base + 2.5:g})+mid({base + 5})"),
            "mid": (mid, f"{key0}+{key10}"),
            "e3": (r(mid, q3), f"mid({base + 5})+q({base + 7.5:g})"),
            "q3": (q3, f"mid({base + 5})+{key10}"),
            "e4": (r(q3, p10), f"q({base + 7.5:g})+{key10}"),
        }
        if steps is not None:
            lb = {s["slot"]: _decade_label(base, s["slot"]) for s in DECADE_SLOTS}
            steps.append(
                f"Кольцо {base}–{base + 10} лет ({key0}={p0} → {key10}={p10}): "
                f"[{lb['mid']}] {p0}+{p10}→{mid}; [{lb['q1']}] {p0}+{mid}→{q1}; "
                f"[{lb['q3']}] {mid}+{p10}→{q3}; [{lb['e1']}] {p0}+{q1}→{vals['e1'][0]}; "
                f"[{lb['e2']}] {q1}+{mid}→{vals['e2'][0]}; [{lb['e3']}] {mid}+{q3}→{vals['e3'][0]}; "
                f"[{lb['e4']}] {q3}+{p10}→{vals['e4'][0]}"
            )
        for slot in DECADE_SLOTS:
            value, formula = vals[slot["slot"]]
            ring.append({
                "age": base + slot["age"],
                "period_start": base + slot["start"],
                "label": _decade_label(base, slot["slot"]),
                "value": value,
                "formula": formula,
                "segment": f"{key0}→{key10}",
            })
    return ring


def age_point(ring: list[dict[str, Any]], age: float) -> dict[str, Any]:
    """Точка кольца, действующая в возрасте ``age`` (лет, дробное).

    Используются границы периодов по подписям matrica-sudby.ru: [0;1), [1;2,5), [2,5;3,5),
    [3,5;5), [5;6), [6;7,5), [7,5;8,5), [8,5;10) — и так каждое десятилетие.
    После 80 лет круг начинается заново (возраст берётся по модулю 80).
    """
    if age < 0:
        raise ValueError("Возраст не может быть отрицательным")
    a = age % 80
    current = ring[0]
    for p in ring:
        if p["period_start"] <= a + 1e-9:
            current = p
        else:
            break
    return current


def _age_on(birth: date, on: date) -> float:
    """Полный возраст в годах с дробной частью (по дням от последнего дня рождения)."""
    years = on.year - birth.year - ((on.month, on.day) < (birth.month, birth.day))

    def anniversary(y: int) -> date:
        try:
            return date(y, birth.month, birth.day)
        except ValueError:  # 29 февраля в невисокосный год → 1 марта
            return date(y, 3, 1)

    last = anniversary(birth.year + years)
    nxt = anniversary(birth.year + years + 1)
    return years + (on - last).days / max((nxt - last).days, 1)


def compute_points(day: int, month: int, year: int, *, reduction: str = "digits",
                   ancestral_inner: str = "rod_center") -> tuple[dict[str, int], dict[str, str], list[str]]:
    """Все точки октаграммы. Возвращает (значения, формулы, шаги)."""
    if ancestral_inner not in ANCESTRAL_INNER_RULES:
        raise ValueError(f"ancestral_inner должен быть одним из {ANCESTRAL_INNER_RULES}")
    date(year, month, day)  # проверка корректности даты
    bld = _Builder(reduction)

    # 1. Личный квадрат (ромб)
    a_val, a_txt = bld._reduce_text(day)
    bld.set("A", a_val, f"день {day} = {a_txt}")
    bld.set("B", month, f"месяц {month}")
    ys = digit_sum(year)
    c_val, c_txt = bld._reduce_text(ys)
    bld.set("C", c_val, f"год {year}: {'+'.join(str(year))} = {c_txt}")
    bld.add("D", "A", "B", "C")
    bld.add("E", "A", "B", "C", "D")

    # 2. Родовой квадрат и его центр
    bld.add("F", "A", "B")
    bld.add("G", "B", "C")
    bld.add("I", "C", "D")
    bld.add("H", "D", "A")
    bld.add("R", "F", "G", "H", "I")

    # 3. Внутренние точки осей (к центру E)
    for k in ("A", "B", "C", "D"):
        bld.add(f"{k}2", k, "E")
        bld.add(f"{k}1", k, f"{k}2")
    bld.add("A3", "A2", "E")
    bld.add("B3", "B2", "E")

    # 4. Внутренние точки диагоналей рода
    center = "R" if ancestral_inner == "rod_center" else "E"
    for k in ("F", "G", "I", "H"):
        bld.add(f"{k}2", k, center)
        bld.add(f"{k}1", k, f"{k}2")

    # 5. Линия талантов, каналы денег и отношений
    bld.add("TAL", "A2", "B2")
    bld.add("X", "C2", "D2")
    bld.add("X_money", "X", "C2")
    bld.add("X_love", "X", "D2")
    bld.add("Y", "C1", "D1")
    return bld.v, bld.formula, bld.steps


def compute_purposes(p: dict[str, int], rule: str = "digits",
                     steps: list[str] | None = None) -> dict[str, int]:
    """Небо/Земля, мужская/женская линии и четыре предназначения."""
    r = lambda *xs: reduce_arcana(sum(xs), rule)  # noqa: E731
    out: dict[str, int] = {}
    out["sky"] = r(p["B"], p["D"])
    out["earth"] = r(p["A"], p["C"])
    out["personal"] = r(out["sky"], out["earth"])
    out["male"] = r(p["F"], p["I"])
    out["female"] = r(p["G"], p["H"])
    out["social"] = r(out["male"], out["female"])
    out["spiritual"] = r(out["personal"], out["social"])
    out["planetary"] = r(out["social"], out["spiritual"])
    if steps is not None:
        steps.append(f"Небо = B+D = {p['B']}+{p['D']} → {out['sky']}; Земля = A+C = {p['A']}+{p['C']} → {out['earth']}; "
                     f"Личное = Небо+Земля = {out['sky']}+{out['earth']} → {out['personal']}")
        steps.append(f"М (мужская линия) = F+I = {p['F']}+{p['I']} → {out['male']}; "
                     f"Ж (женская линия) = G+H = {p['G']}+{p['H']} → {out['female']}; "
                     f"Социальное = М+Ж = {out['male']}+{out['female']} → {out['social']}")
        steps.append(f"Духовное = Личное+Социальное = {out['personal']}+{out['social']} → {out['spiritual']}; "
                     f"Планетарное = Социальное+Духовное = {out['social']}+{out['spiritual']} → {out['planetary']}")
    return out


def compute_health(p: dict[str, int], rule: str = "digits", svadhisthana: str = "classic",
                   total_rule: str = "sum_of_totals",
                   steps: list[str] | None = None) -> dict[str, Any]:
    """Карта здоровья: 7 чакр × (физика, энергия, эмоции) + строка «Итого»."""
    if svadhisthana not in SVADHISTHANA_RULES:
        raise ValueError(f"svadhisthana должен быть одним из {SVADHISTHANA_RULES}")
    if total_rule not in HEALTH_TOTAL_RULES:
        raise ValueError(f"health_total должен быть одним из {HEALTH_TOTAL_RULES}")
    sv = ("C2", "D2") if svadhisthana == "classic" else ("C1", "D1")
    pairs = (("A", "B"), ("A1", "B1"), ("A2", "B2"), ("A3", "B3"), ("E", "E"), sv, ("C", "D"))
    rows = []
    for (name, organs), (kp, ke) in zip(CHAKRAS, pairs):
        phys, energy = p[kp], p[ke]
        emo = reduce_arcana(phys + energy, rule)
        rows.append({"chakra": name, "physics": phys, "energy": energy, "emotions": emo,
                     "physics_point": kp, "energy_point": ke, "body": organs})
        if steps is not None:
            steps.append(f"{name}: физика {kp}={phys}, энергия {ke}={energy}, эмоции {phys}+{energy} → {emo}")
    t_phys = reduce_arcana(sum(r["physics"] for r in rows), rule)
    t_energy = reduce_arcana(sum(r["energy"] for r in rows), rule)
    emo_totals = reduce_arcana(t_phys + t_energy, rule)
    emo_rows = reduce_arcana(sum(r["emotions"] for r in rows), rule)
    t_emo = emo_totals if total_rule == "sum_of_totals" else emo_rows
    if steps is not None:
        steps.append("Итого: физика = " + "+".join(str(r["physics"]) for r in rows)
                     + f" = {sum(r['physics'] for r in rows)} → {t_phys}; энергия = "
                     + "+".join(str(r["energy"]) for r in rows)
                     + f" = {sum(r['energy'] for r in rows)} → {t_energy}; эмоции = "
                     + (f"{t_phys}+{t_energy} → {emo_totals}" if total_rule == "sum_of_totals"
                        else f"сумма эмоций {sum(r['emotions'] for r in rows)} → {emo_rows}"))
    return {
        "rows": rows,
        "total": {"physics": t_phys, "energy": t_energy, "emotions": t_emo},
        "total_emotions_alt": emo_rows if total_rule == "sum_of_totals" else emo_totals,
        "svadhisthana_rule": svadhisthana,
        "total_rule": total_rule,
    }


def self_checks(p: dict[str, int], purposes: dict[str, int], health: dict[str, Any],
                ring: list[dict[str, Any]], rule: str = "digits") -> dict[str, Any]:
    """Самопроверки результата (те же, что в разделе 6 документации, для ручного счёта).

    Свёртка сохраняет остаток: сложение цифр — по модулю 9, вычитание 22 — по модулю 22.
    Поэтому, например, Rod = F+G+H+I = 2·(A+B+C+D) ≡ 2·E, а Социальное ≡ 2·E.
    """
    m = 9 if rule == "digits" else 22

    def eq(x: int, y: int) -> bool:
        return (x - y) % m == 0

    e = p["E"]
    main_ring = [x["value"] for x in ring if float(x["age"]).is_integer() and int(x["age"]) % 10 == 0]
    items = [
        ("все точки в диапазоне 1..22", all(1 <= v <= 22 for v in p.values())),
        (f"D ≡ A+B+C (mod {m})", eq(p["D"], p["A"] + p["B"] + p["C"])),
        (f"E ≡ A+B+C+D (mod {m})", eq(e, p["A"] + p["B"] + p["C"] + p["D"])),
        (f"Rod ≡ 2·E (mod {m})", eq(p["R"], 2 * e)),
        (f"Личное ≡ E, Социальное ≡ 2·E, Духовное ≡ 3·E, Планетарное ≡ 5·E (mod {m})",
         eq(purposes["personal"], e) and eq(purposes["social"], 2 * e)
         and eq(purposes["spiritual"], 3 * e) and eq(purposes["planetary"], 5 * e)),
        ("Манипура = (E, E, R(2·E))", health["rows"][4]["physics"] == e == health["rows"][4]["energy"]
         and health["rows"][4]["emotions"] == reduce_arcana(2 * e, rule)),
        ("кольцо: 64 точки; в 0, 10, …, 70 лет стоят A, F, B, G, C, I, D, H",
         len(ring) == 64 and main_ring == [p[k] for k, _ in RING_ORDER]),
    ]
    return {"modulus": m, "items": [{"check": t, "ok": ok} for t, ok in items],
            "all_ok": all(ok for _, ok in items)}


def calculate(b: BirthInput, **options: Any) -> dict[str, Any]:
    """Полный расчёт Матрицы судьбы.

    Опции:
      * ``reduction``: ``digits`` (по умолчанию) | ``minus22``;
      * ``svadhisthana``: ``classic`` (C2, D2 — по умолчанию) | ``matrica_sudby`` (C1, D1);
      * ``ancestral_inner``: ``rod_center`` (F2 = F+R — по умолчанию) | ``personal_center`` (F2 = F+E);
      * ``health_total``: ``sum_of_totals`` (эмоции итога = итог физики + итог энергии) | ``sum_of_rows``;
      * ``on_date`` (``YYYY-MM-DD`` или ``date``) или ``age`` (лет) — для аркана текущего периода.
    """
    reduction = options.get("reduction", "digits")
    svadhisthana = options.get("svadhisthana", "classic")
    ancestral_inner = options.get("ancestral_inner", "rod_center")
    health_total = options.get("health_total", "sum_of_totals")
    if reduction not in REDUCTION_RULES:
        raise ValueError(f"reduction должен быть одним из {REDUCTION_RULES}")

    warnings: list[str] = []
    unknown = sorted(set(options) - KNOWN_OPTIONS)
    if unknown:
        warnings.append(f"Неизвестные опции проигнорированы: {', '.join(unknown)}. "
                        f"Допустимые: {', '.join(sorted(KNOWN_OPTIONS))}.")
    if reduction != "digits":
        warnings.append("Свёртка «минус 22» — не вариант Ладини; результаты не совпадут с популярными калькуляторами.")
    if ancestral_inner != "rod_center":
        warnings.append("Внутренние точки рода считаются от центра E — вариант не подтверждён опубликованными схемами.")
    if b.year < 1800 or b.year > 2399:
        warnings.append("Год вне диапазона, проверенного тестами (1800–2399); расчёт формален.")

    pts, formulas, steps = compute_points(b.day, b.month, b.year, reduction=reduction,
                                          ancestral_inner=ancestral_inner)
    purposes = compute_purposes(pts, reduction, steps)
    health = compute_health(pts, reduction, svadhisthana, health_total, steps)
    ring = compute_age_ring(pts, reduction, steps)

    current = None
    birth = date(b.year, b.month, b.day)
    age = options.get("age")
    on_date = options.get("on_date")
    if age is None and on_date is not None:
        on = on_date if isinstance(on_date, date) else date.fromisoformat(str(on_date))
        age = _age_on(birth, on)
    if age is not None:
        age = float(age)
        if age >= 80:
            warnings.append("Возраст ≥ 80: кольцо пройдено полностью, берётся второй круг (возраст − 80).")
        cp = age_point(ring, age)
        current = {"age": round(age, 3), "label": cp["label"], "value": cp["value"],
                   "arcanum": ARCANA[cp["value"]]["name"]}

    karmic_tail = [pts["D2"], pts["D1"], pts["D"]]
    result: dict[str, Any] = {
        "method": METHOD,
        "variant": {
            "school": "Наталья Ладини (22 аркана), схема точек как на matrica-sudby.ru",
            "reduction": reduction,
            "svadhisthana": svadhisthana,
            "ancestral_inner": ancestral_inner,
            "health_total": health_total,
        },
        "inputs_used": {"day": b.day, "month": b.month, "year": b.year, "gender": b.gender},
        "warnings": warnings,
        "points": pts,
        "formulas": formulas,
        "personal_square": {k: pts[k] for k in ("A", "B", "C", "D", "E")},
        "ancestral_square": {k: pts[k] for k in ("F", "G", "I", "H", "R")},
        "zones": {
            "comfort_zone": pts["E"],
            "portrait_child_parent": [pts["A"], pts["A1"], pts["A2"]],
            "talents_top_line": [pts["B"], pts["B1"], pts["B2"]],
            "talent_line": [pts["A2"], pts["TAL"], pts["B2"]],
            "material_line": [pts["C"], pts["C1"], pts["C2"]],
            "karmic_tail": karmic_tail,
            "karmic_tail_code": "-".join(str(x) for x in karmic_tail),
        },
        "channels": {
            "classic": {
                "center_X": pts["X"],
                "money_line": [pts["C2"], pts["X_money"], pts["X"]],
                "love_line": [pts["D2"], pts["X_love"], pts["X"]],
                "note": "Деньги: C2 → «под долларом» (X+C2) → X; отношения: D2 → «под сердцем» (X+D2) → X",
            },
            "matrica_sudby_ru": {
                "money_line": [pts["D2"], pts["C2"], pts["X"]],
                "relationship_line": [pts["D1"], pts["C1"], pts["Y"]],
                "note": "Деньги: вход D2, «за что платят» C2, выход/блок X=C2+D2; "
                        "отношения: вход D1, C1, Y=C1+D1",
            },
        },
        "ancestral_lines": {
            "male_father": {"top": [pts["F"], pts["F1"], pts["F2"]],
                            "bottom": [pts["I"], pts["I1"], pts["I2"]]},
            "female_mother": {"top": [pts["G"], pts["G1"], pts["G2"]],
                              "bottom": [pts["H"], pts["H1"], pts["H2"]]},
            "rod_strength": pts["R"],
        },
        "purposes": purposes,
        "health_map": health,
        "age_ring": ring,
        "current_period": current,
        "arcana": {str(v): ARCANA[v]["name"] for v in sorted(set(pts.values()))},
        "checks": self_checks(pts, purposes, health, ring, reduction),
        "steps": steps,
    }
    return result


__all__ = [
    "ARCANA", "POINT_INFO", "calculate", "compute_points", "compute_purposes", "compute_health",
    "compute_age_ring", "age_point", "reduce_arcana", "digit_sum", "self_checks",
]
