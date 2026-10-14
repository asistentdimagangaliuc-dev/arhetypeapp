"""Сюцай — «цифровая психология» Жаната Кожамжарова (числа по дате рождения).

Это НЕ школа Ба-цзы: в русскоязычной среде «Сюцай» — нумерологическая система по дате рождения
(сайт основателя zhanatglobal.com, практики syutsay.ru и др.). Классический Ба-цзы — модуль 01.
Подробности, источники, расхождения и разборы — knowledge-base/15-syutsay.md.

Что считает калькулятор:

* Число сознания (ЧС, «вектор эго», оно же «число реализации») — сумма цифр ДНЯ рождения,
  сводимая до 1–9 без мастер-чисел (29 → 11 → 2, 22 → 4).
* Число миссии — сумма ВСЕХ цифр даты ДД.ММ.ГГГГ, сводимая до 1–9 (27.10.1990: 29 → 11 → 2).
* Матрица — все ненулевые цифры даты, разложенные по сетке 3-6-9 / 2-5-8 / 1-4-7 (нули не
  ставятся, ЧС и миссия в матрицу не добавляются); присутствующие / отсутствующие / повторяющиеся
  энергии, 8 геометрических линий сетки («линия денег» 1-4-7) и «программа доминирующего эго» (1 и 9).
* Общий год (сумма цифр календарного года) и личный год (день + месяц + текущий год), 9-летний цикл.
* Возрастные вехи (сознание раскрывается к 21 году, миссия — с 22 до 33 лет).
* Совместимость чисел сознания двух людей по описаниям школы (если передан партнёр).
* Число имени (халдейская таблица по латинской записи имени) — если известно имя.
* «Финансовый код» калькулятора findh.org — только как справка калькулятора (⚠ не подтверждён школой).

Только стандартная библиотека.
"""
from __future__ import annotations

import re
from datetime import date
from typing import Any

from .common.time import BirthInput

METHOD = "syutsay"
VARIANT = ("Сюцай (цифровая психология Ж. Кожамжарова): ЧС по дню рождения, миссия по всем цифрам "
           "даты, матрица 3-6-9/2-5-8/1-4-7 без нулей; без мастер-чисел")

# ---------------------------------------------------------------------------
# Справочные таблицы (источники — в базе знаний, раздел 9)
# ---------------------------------------------------------------------------

#: Планеты-покровители чисел (syutsay.ru/syutsay-chislo-1…9, findh.org, nur.kz, таблица А. Ройтблата).
PLANETS: dict[int, str] = {
    1: "Солнце", 2: "Луна", 3: "Юпитер", 4: "Раху", 5: "Меркурий",
    6: "Венера", 7: "Кету", 8: "Сатурн", 9: "Марс",
}

#: Дни месяца, дающие каждое число сознания.
CONSCIOUSNESS_DAYS: dict[int, list[int]] = {
    n: [d for d in range(1, 32) if (d - 1) % 9 + 1 == n] for n in range(1, 10)
}

#: Число сознания: группа (findh.org), «+» и «−» (таблица А. Ройтблата / syutsay.ru),
#: через что реализуется душа и как «служить людям» (findh.org), сферы (syutsay.ru).
CONSCIOUSNESS: dict[int, dict[str, str]] = {
    1: {"group": "Царь",
        "plus": "лидерство, инициативность, идеализм, покровительство",
        "minus": "агрессия, деспотизм, консерватизм, эгоизм",
        "soul": "руководство, лидерство или автономный труд",
        "serve": "через идею",
        "spheres": "руководитель, глава коллектива, предприниматель; работать не под чьим-то началом"},
    2: {"group": "Министр иностранных дел",
        "plus": "исполнительность, дипломатичность, желание понять",
        "minus": "двойственность, сомнения, депрессивность",
        "soul": "отношения (хорошие и плохие)",
        "serve": "через принятие решений и стратегию",
        "spheres": "дипломатия, психология, эзотерика, парламент/посольство"},
    3: {"group": "Премьер-министр",
        "plus": "целеустремлённость, знания, «гуру: я знаю»",
        "minus": "принципиальность, лень, «я знаю», категоричность, пустословие, азарт",
        "soul": "наставничество («гуру знаний»)",
        "serve": "через отношения",
        "spheres": "педагогика, кураторство, коучинг, тренерство, медицина, управление (премьер-министр)"},
    4: {"group": "Революционер",
        "plus": "борьба за справедливость, креативность, трансформатор, новатор",
        "minus": "неудовлетворённость, разрушение, отчуждённость, апатия, мошенник",
        "soul": "креатив (везде)",
        "serve": "через наставничество",
        "spheres": "новаторские проекты, издательство, публицистика, реклама"},
    5: {"group": "Бизнес",
        "plus": "высокая коммуникация, удачливость, фортуна, торговля, бизнес",
        "minus": "непостоянство, беспечность, безумие, жестокость, экстремизм",
        "soul": "технический интеллект, рационализаторство, логика",
        "serve": "через креатив",
        "spheres": "предпринимательство, торговля, масштабируемые проекты, создание объектов искусства"},
    6: {"group": "Комфорт",
        "plus": "успех, мудрость, советник, любовь",
        "minus": "противозаконность, неразборчивость, месть, преступность",
        "soul": "творчество",
        "serve": "через интеллект и логику",
        "spheres": "творчество, советник/наставник, инвестиции"},
    7: {"group": "Йога",
        "plus": "быстрая реализация идей, кундалини-йога, кризис-менеджер",
        "minus": "хаос, рассеянность, непонимание ситуации, суицидальность",
        "soul": "йога (везде)",
        "serve": "через творчество (любовь)",
        "spheres": "руководство, антикризисное управление; обязательны физкультура/йога"},
    8: {"group": "Контроль, работа",
        "plus": "контроль, реализм, скрупулёзность, материализм",
        "minus": "сомнение, недоверие, тотальный контроль, ранний инсульт",
        "soul": "тяжёлый труд («чем тяжелее труд, тем яснее ум»)",
        "serve": "через понимание людей",
        "spheres": "контроль результатов, соблюдение законов, укрепление структур (частных и государственных)"},
    9: {"group": "Министр обороны",
        "plus": "стремительность, спортивность, динамичность, воин",
        "minus": "ярость, паранойя, наивность",
        "soul": "идея («дух воина»)",
        "serve": "через труд (самодостаточность) и контроль себя",
        "spheres": "армия, спорт, полиция, хирургия, ветеринария"},
}

#: Число миссии: краткое предназначение (t-j.ru, msk1.ru, таблица Ройтблата), развёрнутое название
#: и «+»/«−» действий (findh.org), группа миссии по Ройтблату (msk1.ru).
MISSION: dict[int, dict[str, str]] = {
    1: {"short": "власть", "title": "миссия власти, одиночества и сверхэгоизма",
        "plus": "лидерство, покровительство", "minus": "агрессия, деспотизм", "group": "мужская"},
    2: {"short": "творчество и психология", "title": "миссия творческой психологии",
        "plus": "желание понять, дипломатичность", "minus": "депрессия, дуальность, двуличие",
        "group": "женская"},
    3: {"short": "анализ", "title": "миссия анализа, справедливого управления и наставничества",
        "plus": "справедливая выгода", "minus": "корыстный расчёт", "group": "женская"},
    4: {"short": "передача тайных знаний", "title": "миссия управления из тени и передачи знаний",
        "plus": "креатив, новшества, трансформация, честность",
        "minus": "мошеннические действия, негативная трансформация", "group": "мужская"},
    5: {"short": "борьба", "title": "миссия борьбы",
        "plus": "высокая коммуникация", "minus": "агрессия", "group": "мужская"},
    6: {"short": "творчество", "title": "миссия творчества",
        "plus": "творчество", "minus": "страдание в поиске любви", "group": "женская"},
    7: {"short": "йога", "title": "миссия йоги и кризиса",
        "plus": "согласованная трансформация", "minus": "кризис себе и окружающим, хаос",
        "group": "женская"},
    8: {"short": "упорный труд", "title": "миссия упорного труда и безбрачия",
        "plus": "упорный труд", "minus": "отшельничество, сомнения, тунеядство", "group": "мужская"},
    9: {"short": "служение людям", "title": "миссия служения обществу",
        "plus": "служение обществу", "minus": "эмоциональное выгорание", "group": "женская"},
}

#: Значение клеток матрицы. Подписи клеток калькулятора findh.org (совпадают с названиями миссий)
#: и компетенции из прессы/официального сайта (4 — постановка целей: zhanatglobal.com, wday.ru;
#: 1 — «солнечная энергия», 4 — «энергия целей»: syutsay.ru; 1/2/5/7/8 — horo.mail.ru).
MATRIX_ENERGY: dict[int, dict[str, str]] = {
    1: {"label": "Власть", "competence": "лидерство, «солнечная энергия»"},
    2: {"label": "Творческая психология", "competence": "сотрудничество, понимание людей"},
    3: {"label": "Анализ", "competence": "анализ, знания"},
    4: {"label": "Передача знаний", "competence": "постановка целей, понимание истинных стремлений"},
    5: {"label": "Борьба", "competence": "коммуникация, взаимодействие с людьми"},
    6: {"label": "Творчество", "competence": "творчество, комфорт"},
    7: {"label": "Йога", "competence": "успех, признание (работает при активных 4, 5 и 8)"},
    8: {"label": "Упорный труд", "competence": "труд, действие, структура, дисциплина"},
    9: {"label": "Служение людям", "competence": "служение, идея"},
}

#: Сетка матрицы сверху вниз (syutsay.ru/matritsa-syutsay; t-j.ru; findh.org).
GRID_ROWS: tuple[tuple[int, int, int], ...] = ((3, 6, 9), (2, 5, 8), (1, 4, 7))

#: Восемь геометрических линий сетки. Школа говорит о «12 радиальных линиях», но их состав не
#: опубликован; достоверно названа только «линия денег» 1-4-7 (t-j.ru, gems-brokers.ru).
LINES: list[dict[str, Any]] = [
    {"id": "row_369", "cells": [3, 6, 9], "kind": "строка (верх)", "name": None},
    {"id": "row_258", "cells": [2, 5, 8], "kind": "строка (середина)", "name": None},
    {"id": "row_147", "cells": [1, 4, 7], "kind": "строка (низ)", "name": "линия денег"},
    {"id": "col_321", "cells": [3, 2, 1], "kind": "столбец (левый)", "name": None},
    {"id": "col_654", "cells": [6, 5, 4], "kind": "столбец (средний)", "name": None},
    {"id": "col_987", "cells": [9, 8, 7], "kind": "столбец (правый)", "name": None},
    {"id": "diag_357", "cells": [3, 5, 7], "kind": "диагональ", "name": None},
    {"id": "diag_159", "cells": [1, 5, 9], "kind": "диагональ", "name": None},
]

#: Особенности «составных» дней (syutsay.ru, snob.ru).
DAY_NOTES: dict[int, str] = {
    2: "явный эзотерик (syutsay.ru/syutsay-chislo-2)",
    10: "ноль в дне: от природы негативное мышление, «обнуляются каждый день» (syutsay.ru, snob.ru)",
    11: "нетипичная двойка: «раздвоенное сознание», свойства 2 и 1; тайный эзотерик (syutsay.ru)",
    19: "самая энергетическая единица, «знак огня», целительские способности (syutsay.ru)",
    20: "ноль в дне: особый риск депрессии, негативное мышление; явный эзотерик (syutsay.ru, snob.ru)",
    29: "тайный эзотерик, гипнотизёр (syutsay.ru)",
    30: "ноль в дне: негативное мышление, надменность; женщинам — риск в отношениях с детьми (syutsay.ru)",
}

#: Значения числа имени по Сюцай (nur.kz).
NAME_MEANING: dict[int, str] = {
    1: "популярность", 2: "личное благополучие", 3: "солидность", 4: "отчуждённость",
    5: "артистизм", 6: "успех", 7: "вызов природе", 8: "постоянный упорный труд",
    9: "эмоциональная глубина",
}

#: Халдейская таблица для латиницы (её даёт nur.kz для Сюцай; = таблица Хейро, модуль 12 §4.9).
LATIN_CHALDEAN: dict[str, int] = {
    "A": 1, "I": 1, "J": 1, "Q": 1, "Y": 1, "B": 2, "K": 2, "R": 2, "C": 3, "G": 3, "L": 3, "S": 3,
    "D": 4, "M": 4, "T": 4, "E": 5, "H": 5, "N": 5, "X": 5, "U": 6, "V": 6, "W": 6, "O": 7, "Z": 7,
    "F": 8, "P": 8,
}

#: Транслитерация ICAO Doc 9303 (загранпаспорт РФ) — ⚠ выбор транслитерации школой не описан.
ICAO_9303: dict[str, str] = {
    "А": "A", "Б": "B", "В": "V", "Г": "G", "Д": "D", "Е": "E", "Ё": "E", "Ж": "ZH", "З": "Z",
    "И": "I", "Й": "I", "К": "K", "Л": "L", "М": "M", "Н": "N", "О": "O", "П": "P", "Р": "R",
    "С": "S", "Т": "T", "У": "U", "Ф": "F", "Х": "KH", "Ц": "TS", "Ч": "CH", "Ш": "SH", "Щ": "SHCH",
    "Ъ": "IE", "Ы": "Y", "Ь": "", "Э": "E", "Ю": "IU", "Я": "IA",
}

#: Совместимость чисел сознания по описаниям школы (syutsay.ru/syutsay-chislo-N).
#: relation: good / difficult / mixed; suffers — чьё число «страдает» в паре, если указано.
COMPATIBILITY: dict[frozenset[int], dict[str, Any]] = {
    frozenset({1}): {"relation": "good", "note": "женщине-1 хороший муж — 1 или 2", "src": [1]},
    frozenset({1, 2}): {"relation": "good", "note": "двойкам «отлично подходят» единицы", "src": [1, 2]},
    frozenset({1, 3}): {"relation": "good", "note": "тройки хорошо дружат с 1 и 9", "src": [3]},
    frozenset({1, 5}): {"relation": "good", "note": "«неплохое сотрудничество»", "src": [5]},
    frozenset({1, 7}): {"relation": "difficult", "suffers": 1,
                        "note": "семёрка может «морально раздавить» единицу", "src": [7]},
    frozenset({1, 8}): {"relation": "difficult", "note": "восьмёркам не советуют отношения с 1", "src": [8]},
    frozenset({1, 9}): {"relation": "difficult", "note": "сложно найти взаимопонимание", "src": [9]},
    frozenset({2, 4}): {"relation": "difficult", "suffers": 2,
                        "note": "нежелательный брак, «пострадает 2-ка»", "src": [2, 4]},
    frozenset({2, 7}): {"relation": "difficult", "suffers": 2,
                        "note": "7 решает стремительно, 2 сомневается; 7 может «раздавить» 2", "src": [2, 7]},
    frozenset({2, 9}): {"relation": "mixed",
                        "note": "легче, чем 9 с 1, но разногласия: 9 стремительна, 2 нерешительна",
                        "src": [2, 9]},
    frozenset({3, 5}): {"relation": "difficult", "suffers": 3,
                        "note": "«не очень удачный выбор, пострадает тройка»", "src": [3, 5]},
    frozenset({3, 6}): {"relation": "difficult", "suffers": 6,
                        "note": "тройки могут «уничтожить шестёрок энергетически»", "src": [3, 6]},
    frozenset({3, 9}): {"relation": "good", "note": "«прекрасный партнёр и друг»", "src": [3, 9]},
    frozenset({4, 7}): {"relation": "good",
                        "note": "«как один организм», но сексуальные желания не всегда совпадают",
                        "src": [4, 7]},
    frozenset({4, 8}): {"relation": "good", "note": "«чувствуют друг друга даже на расстоянии»", "src": [8]},
    frozenset({4, 9}): {"relation": "difficult", "suffers": 4,
                        "note": "девятка «жёстко подавляет» четвёрку", "src": [4, 9]},
    frozenset({5, 8}): {"relation": "good", "note": "«хороший, понимающий партнёр»", "src": [5]},
    frozenset({6, 8}): {"relation": "good", "note": "«неплохо понимают друг друга»", "src": [6, 8]},
    frozenset({6, 9}): {"relation": "mixed", "note": "страсть, но бурные ссоры и скандалы", "src": [6, 9]},
    frozenset({9}): {"relation": "good", "note": "двум девяткам «непременно нужно быть вместе»", "src": [9]},
}

RELATION_RU = {"good": "благоприятно", "difficult": "сложно", "mixed": "неоднозначно",
               "not_described": "школа не описывает"}

_PATRONYMIC_RE = re.compile(r"(ОВИЧ|ЕВИЧ|ЬИЧ|ИЧ|ОВНА|ЕВНА|ИЧНА|ИНИЧНА|ОГЛЫ|КЫЗЫ|УЛЫ)$")
_RU_SURNAME_RE = re.compile(
    r"(ОВ|ЕВ|ЁВ|ИН|ЫН|ОВА|ЕВА|ЁВА|ИНА|ЫНА|СКИЙ|ЦКИЙ|СКАЯ|ЦКАЯ|ОЙ|ИХ|ЫХ|ЕНКО|УК|ЮК|ЧУК|ЕЦ|ЕЙН|ШТЕЙН)$"
)

# ---------------------------------------------------------------------------
# Арифметика
# ---------------------------------------------------------------------------


def digit_sum(n: int) -> int:
    """Сумма цифр неотрицательного целого."""
    return sum(int(c) for c in str(abs(n)))


def reduce_chain(n: int) -> list[int]:
    """Цепочка сведения суммированием цифр до 1–9 (мастер-числа НЕ сохраняются): 29 → [29, 11, 2]."""
    if n <= 0:
        raise ValueError("Сводить можно только положительное число")
    chain = [n]
    while chain[-1] > 9:
        chain.append(digit_sum(chain[-1]))
    return chain


def digital_root(n: int) -> int:
    """Цифровой корень 1–9 (то же, что последнее звено reduce_chain)."""
    return (n - 1) % 9 + 1


def date_digits(year: int, month: int, day: int) -> list[int]:
    """Цифры даты в записи ДД.ММ.ГГГГ (с ведущими нулями)."""
    return [int(c) for c in f"{day:02d}{month:02d}{year:04d}"]


def _chain_str(chain: list[int]) -> str:
    return " → ".join(str(x) for x in chain)


def _sum_str(digits: list[int], chain: list[int]) -> str:
    """«1+5+0+5 = 11 → 2»: цифры, их сумма и дальнейшее сведение (chain[0] — сумма цифр)."""
    return "+".join(str(x) for x in digits) + " = " + _chain_str(chain)


# ---------------------------------------------------------------------------
# Основные числа
# ---------------------------------------------------------------------------


def consciousness_number(day: int) -> dict:
    """Число сознания: сумма цифр дня рождения, сведённая до 1–9 (29 → 11 → 2; 22 → 4)."""
    if not 1 <= day <= 31:
        raise ValueError("День месяца должен быть 1–31")
    chain = reduce_chain(day)  # 29 → [29, 11, 2]; 22 → [22, 4]; 7 → [7]
    n = chain[-1]
    return {"number": n, "day": day, "chain": chain, "planet": PLANETS[n],
            "days_with_same_number": CONSCIOUSNESS_DAYS[n]}


def mission_number(year: int, month: int, day: int) -> dict:
    """Число миссии: сумма всех цифр ДД.ММ.ГГГГ, сведённая до 1–9 (27.10.1990: 29 → 11 → 2)."""
    digits = date_digits(year, month, day)
    total = sum(digits)
    chain = reduce_chain(total)
    n = chain[-1]
    return {"number": n, "digits": digits, "sum": total, "chain": chain, "planet": PLANETS[n]}


def build_matrix(year: int, month: int, day: int) -> dict:
    """Матрица Сюцай: счёт цифр 1–9 даты, сетка 3-6-9/2-5-8/1-4-7, линии и «программы»."""
    digits = date_digits(year, month, day)
    counts = {n: digits.count(n) for n in range(1, 10)}
    zeros = digits.count(0)
    cells = {str(n): (str(n) * counts[n] if counts[n] else "–") for n in range(1, 10)}
    grid = [[cells[str(n)] for n in row] for row in GRID_ROWS]
    present = [n for n in range(1, 10) if counts[n]]
    missing = [n for n in range(1, 10) if not counts[n]]
    repeated = [n for n in range(1, 10) if counts[n] >= 2]

    lines = []
    for ln in LINES:
        filled = [c for c in ln["cells"] if counts[c]]
        status = "full" if len(filled) == 3 else ("empty" if not filled else "partial")
        lines.append({
            "id": ln["id"], "cells": ln["cells"], "kind": ln["kind"], "name": ln["name"],
            "status": status, "filled_cells": filled,
            "missing_cells": [c for c in ln["cells"] if not counts[c]],
            "digits_total": sum(counts[c] for c in ln["cells"]),
        })

    ego_active = counts[1] > 0 and counts[9] > 0
    programs = [{
        "id": "dominant_ego", "name": "программа доминирующего эго", "cells": [1, 9],
        "active": ego_active, "counts": {"1": counts[1], "9": counts[9]},
        "amplified": ego_active and (counts[1] >= 2 or counts[9] >= 2),
        "source": "t-j.ru: заполнены ячейки 1 и 9, «особенно если там оказалось сразу несколько цифр»",
    }]
    business = {
        "order": [4, 5, 8, 7],
        "present": [n for n in (4, 5, 8, 7) if counts[n]],
        "seven_supported": bool(counts[7] and counts[4] and counts[5] and counts[8]),
        "source": "horo.mail.ru (Е. Ларина): 7 эффективна только при активных 4, 5 и 8",
    }
    return {
        "digits": digits,
        "counts": {str(n): counts[n] for n in range(1, 10)},
        "zeros": zeros,
        "cells": cells,
        "grid_rows": [list(r) for r in GRID_ROWS],
        "grid": grid,
        "present": present,
        "missing": missing,
        "repeated": repeated,
        "energies": {str(n): {**MATRIX_ENERGY[n], "planet": PLANETS[n], "count": counts[n]}
                     for n in range(1, 10)},
        "lines": lines,
        "programs": programs,
        "business_energies": business,
    }


def universal_year(year: int) -> dict:
    """Число общего года: сумма цифр года до 1–9 (2024 → 8, zhanatglobal.com)."""
    chain = reduce_chain(year)  # 2024 → [2024, 8]
    return {"year": year, "number": chain[-1], "chain": chain, "planet": PLANETS[chain[-1]]}


def personal_year(day: int, month: int, year: int) -> dict:
    """Личный год: цифры дня и месяца рождения + цифры текущего года, до 1–9.

    Трамп 14.06.1946, 2024: 1+4+0+6+2+0+2+4 = 19 → 10 → 1 (syutsay.ru: «2024 год … энергия Солнца (1)»).
    Граница года — 1 января (⚠ вывод из того, что календари продаются на календарный год).
    """
    digits = [int(c) for c in f"{day:02d}{month:02d}{year:04d}"]
    total = sum(digits)
    chain = reduce_chain(total)
    n = chain[-1]
    return {"year": year, "number": n, "digits": digits, "sum": total, "chain": chain,
            "planet": PLANETS[n]}


def financial_code_findh(year: int, month: int, day: int) -> dict:
    """«Финансовый код» калькулятора findh.org (⚠ формула калькулятора, школой не опубликована).

    ЧС + сумма цифр месяца + корень года + корень их суммы, записанные подряд: 31.05.2001 → 4533.
    """
    cs = digital_root(day)
    ms = digit_sum(month)
    ys = digital_root(digit_sum(year))
    fs = digital_root(cs + ms + ys)
    return {"code": f"{cs}{ms}{ys}{fs}", "parts": [cs, ms, ys, fs],
            "status": "calculator_only",
            "source": "https://findh.org/5155-suitsai.html (распакованный JS калькулятора)"}


# ---------------------------------------------------------------------------
# Имя
# ---------------------------------------------------------------------------


def transliterate_icao(text: str) -> str:
    """Кириллица → латиница по ICAO 9303; латиница остаётся как есть (в верхнем регистре)."""
    out = []
    for ch in text.upper():
        out.append(ICAO_9303.get(ch, ch))
    return "".join(out)


def extract_given_name(full_name: str) -> tuple[str, str]:
    """Выделить личное имя из ФИО. Возвращает (имя, как определено)."""
    s = full_name.strip()
    if "/" in s:
        parts = [p.strip() for p in s.split("/") if p.strip()]
        latin = [p for p in parts if re.search(r"[A-Za-z]", p)]
        s = latin[0] if latin else parts[0]
    tokens = [t for t in re.split(r"\s+", s) if t]
    if not tokens:
        raise ValueError("Пустое имя")
    if len(tokens) == 1:
        return tokens[0], "одно слово"
    is_cyr = bool(re.search(r"[А-Яа-яЁё]", s))
    if is_cyr:
        up = [t.upper() for t in tokens]
        if len(tokens) >= 3 and _PATRONYMIC_RE.search(up[-1]):
            return tokens[1], "Фамилия Имя Отчество"
        if len(tokens) >= 3 and _PATRONYMIC_RE.search(up[1]):
            return tokens[0], "Имя Отчество Фамилия"
        if _RU_SURNAME_RE.search(up[0]):
            return tokens[1], "Фамилия Имя"
        return tokens[0], "Имя Фамилия (по умолчанию)"
    return tokens[0], "латиница: Имя Фамилия"


def name_number(name: str) -> dict:
    """Число имени по Сюцай: халдейская таблица для латинской записи имени, сумма до 1–9."""
    latin = transliterate_icao(name)
    letters = [(ch, LATIN_CHALDEAN[ch]) for ch in latin if ch in LATIN_CHALDEAN]
    if not letters:
        raise ValueError("В имени нет латинских букв после транслитерации")
    total = sum(v for _, v in letters)
    chain = reduce_chain(total)
    n = chain[-1]
    return {"name": name, "latin": latin, "letters": [[c, v] for c, v in letters], "sum": total,
            "chain": chain, "number": n, "meaning": NAME_MEANING[n]}


# ---------------------------------------------------------------------------
# Совместимость
# ---------------------------------------------------------------------------


def compatibility(c1: int, c2: int) -> dict:
    """Совместимость двух чисел сознания по описаниям syutsay.ru (пары, о которых школа молчит, —
    not_described). Оговорка школы: при развитом сознании союз возможен с любым числом."""
    for n in (c1, c2):
        if not 1 <= n <= 9:
            raise ValueError("Число сознания должно быть 1–9")
    rec = COMPATIBILITY.get(frozenset({c1, c2}))
    if rec is None:
        out: dict[str, Any] = {"pair": [c1, c2], "relation": "not_described",
                               "relation_ru": RELATION_RU["not_described"], "note": None,
                               "suffers": None, "sources": []}
    else:
        out = {"pair": [c1, c2], "relation": rec["relation"], "relation_ru": RELATION_RU[rec["relation"]],
               "note": rec["note"], "suffers": rec.get("suffers"),
               "sources": [f"https://syutsay.ru/syutsay-chislo-{k}" for k in rec["src"]]}
    extra = []
    if 8 in (c1, c2):
        extra.append("бизнес с восьмёркой эффективен, если партнёры разного пола (syutsay.ru/syutsay-chislo-8)")
    out["extra_notes"] = extra
    out["caveat"] = ("школа: «при работе над своим сознанием … можно вступить в брак или начать дружбу "
                     "с любой цифрой» (syutsay.ru/syutsay-chislo-4)")
    return out


# ---------------------------------------------------------------------------
# Разбор опций
# ---------------------------------------------------------------------------


def _parse_partner(p: Any) -> tuple[int, int, int] | None:
    if p is None or p == "":
        return None
    if isinstance(p, BirthInput):
        return p.year, p.month, p.day
    if isinstance(p, date):
        return p.year, p.month, p.day
    if isinstance(p, dict):
        return int(p["year"]), int(p["month"]), int(p["day"])
    s = str(p).strip()
    m = re.fullmatch(r"(\d{4})-(\d{1,2})-(\d{1,2})", s)
    if m:
        y, mo, d = (int(x) for x in m.groups())
    else:
        m = re.fullmatch(r"(\d{1,2})\.(\d{1,2})\.(\d{4})", s)
        if not m:
            raise ValueError(f"Не понимаю дату партнёра: {p!r} (нужно YYYY-MM-DD или ДД.ММ.ГГГГ)")
        d, mo, y = (int(x) for x in m.groups())
    date(y, mo, d)  # валидация
    return y, mo, d


# ---------------------------------------------------------------------------
# Главная функция
# ---------------------------------------------------------------------------


def calculate(b: BirthInput, **options) -> dict:
    """Рассчитать числа Сюцай по дате рождения.

    Опции:
      target_year (или year): год для личного года (по умолчанию — текущий календарный)
      cycle_years: сколько лет показать в таблице личных лет, начиная с target_year (по умолчанию 9)
      partner: дата партнёра ('YYYY-MM-DD', 'ДД.ММ.ГГГГ', BirthInput) — совместимость чисел сознания
      given_name: личное имя для числа имени (иначе берётся из b.name); name_latin — готовая латиница
      financial_code: True (по умолчанию) | False — справочный «финансовый код» findh.org
    """
    y, m, d = b.year, b.month, b.day
    date(y, m, d)  # валидация даты (29.02 в невисокосный год — ошибка)
    warnings: list[str] = []
    steps: list[str] = []

    target_year = options.get("target_year", options.get("year"))
    target_year = int(target_year) if target_year is not None else date.today().year
    cycle_years = int(options.get("cycle_years", 9))
    with_fin = options.get("financial_code", True)

    if b.has_time:
        warnings.append("Время рождения в Сюцай не используется: берётся гражданская дата рождения.")

    # 1. Число сознания
    cs = consciousness_number(d)
    cn = cs["number"]
    steps.append(f"Число сознания: день {_chain_str(cs['chain'])} ({PLANETS[cn]}); "
                 f"мастер-числа не сохраняются")

    # 2. Число миссии
    ms = mission_number(y, m, d)
    mn = ms["number"]
    steps.append(f"Число миссии: {_sum_str(ms['digits'], ms['chain'])} ({PLANETS[mn]})")

    # 3. Матрица
    mx = build_matrix(y, m, d)
    steps.append("Матрица: цифры " + "".join(str(x) for x in mx["digits"])
                 + f", нулей {mx['zeros']} (в сетку не ставятся); сетка "
                 + " / ".join(" ".join(row) for row in mx["grid"])
                 + f"; нет цифр: {mx['missing'] or '—'}")
    money = next(ln for ln in mx["lines"] if ln["id"] == "row_147")
    steps.append(f"Линия денег 1-4-7: {money['status']}"
                 + (f" (нет {money['missing_cells']})" if money["missing_cells"] else ""))

    # 4. Годы
    uy = universal_year(target_year)
    py = personal_year(d, m, target_year)
    steps.append(f"Общий год {target_year}: "
                 f"{_sum_str([int(c) for c in str(target_year)], reduce_chain(digit_sum(target_year)))}")
    steps.append(f"Личный год {target_year}: {_sum_str(py['digits'], py['chain'])} "
                 f"({PLANETS[py['number']]})")
    cycle = [{"year": yy, "personal_year": personal_year(d, m, yy)["number"],
              "universal_year": universal_year(yy)["number"]}
             for yy in range(target_year, target_year + max(cycle_years, 0))]

    consciousness = {
        **cs,
        **CONSCIOUSNESS[cn],
        "day_note": DAY_NOTES.get(d),
        "zero_in_day": d in (10, 20, 30),
    }
    mission = {**ms, **MISSION[mn],
               "equals_consciousness": mn == cn}
    if mn != cn:
        steps.append("Миссия ≠ сознанию: по школе в 33 года возможна резкая смена поведения/жизни")

    stages = {
        "consciousness_forms": {"ages": [14, 21], "years": [y + 14, y + 21],
                                "source": "t-j.ru: личность формируется с 14 до 21 года"},
        "mission_reveals": {"ages": [22, 33], "years": [y + 22, y + 33],
                            "source": "t-j.ru: миссия раскрывается с 22 до 33 лет"},
        "mission_full": {"age": 33, "year": y + 33,
                         "source": "zhanatglobal.com, syutsay.ru: миссия полностью проявляется к 33 годам"},
    }

    result: dict[str, Any] = {
        "method": METHOD,
        "variant": VARIANT,
        "inputs_used": {"date": f"{d:02d}.{m:02d}.{y:04d}", "target_year": target_year,
                        "time_used": False, "place_used": False},
        "warnings": warnings,
        "consciousness": consciousness,
        "mission": mission,
        "matrix": mx,
        "years": {"target_year": target_year, "universal_year": uy, "personal_year": py,
                  "cycle": cycle,
                  "boundary": "1 января (⚠ граница личного года школой явно не названа)"},
        "life_stages": stages,
        "steps": steps,
    }

    # 5. Партнёр
    partner = _parse_partner(options.get("partner"))
    if partner is not None:
        py_, pm_, pd_ = partner
        pcs = consciousness_number(pd_)["number"]
        pms = mission_number(py_, pm_, pd_)["number"]
        comp = compatibility(cn, pcs)
        result["compatibility"] = {
            "partner_date": f"{pd_:02d}.{pm_:02d}.{py_:04d}",
            "partner_consciousness": pcs, "partner_mission": pms,
            "consciousness": comp,
            "mission_groups": {"self": MISSION[mn]["group"], "partner": MISSION[pms]["group"],
                               "source": "msk1.ru/wday.ru (А. Ройтблат): миссии 2,3,6,7,9 «женские», "
                                         "1,4,5,8 «мужские»"},
        }
        steps.append(f"Совместимость ЧС {cn} и {pcs}: {comp['relation_ru']}"
                     + (f" — {comp['note']}" if comp["note"] else ""))

    # 6. Имя
    given = options.get("name_latin") or options.get("given_name")
    how = "опция"
    if not given and b.name:
        try:
            given, how = extract_given_name(b.name)
        except ValueError:
            given = None
    if given:
        nn = name_number(str(given))
        nn["parsed_as"] = how
        result["name"] = nn
        steps.append(f"Число имени: {nn['latin']} → "
                     f"{_sum_str([v for _, v in nn['letters']], nn['chain'])} ({nn['meaning']})")
        if re.search(r"[А-Яа-яЁё]", str(given)):
            warnings.append("Число имени посчитано по транслитерации ICAO; при другом привычном написании "
                            "(напр. DMITRY вместо DMITRII) число может измениться — передайте name_latin.")

    # 7. Справочный «финансовый код»
    if with_fin:
        fc = financial_code_findh(y, m, d)
        result["financial_code_findh"] = fc
        steps.append(f"Финансовый код (калькулятор findh.org, ⚠): {fc['code']}")

    result["not_computed"] = [
        "12 радиальных линий матрицы (состав не опубликован; посчитаны 8 линий сетки)",
        "«Задача от Творца», «сфера/предназначение», «число финансового взлёта», «число денег» — "
        "формулы не опубликованы",
        "личные месяц и день (школа их считает, формула не опубликована)",
        "цвета и дни недели по числам (опубликовано только для 1: красный и белый, кошелёк серебристый)",
    ]
    return result
