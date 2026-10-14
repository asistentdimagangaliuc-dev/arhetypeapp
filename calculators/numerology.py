"""Нумерология по дате рождения и имени: пифагорейская (западная) школа и халдейская система.

Что считает (подробности, источники и обоснование умолчаний — knowledge-base/11-numerology.md):

* по дате: Число жизненного пути (Life Path, в русских источниках часто «число судьбы»)
  тремя способами, Число дня рождения (Birthday), Число отношения (Attitude),
  периоды (Period Cycles), вершины (Pinnacles) с возрастами, испытания (Challenges),
  личные год/месяц/день (Personal Year/Month/Day) с выбором границы года,
  числа кармического долга 13/14/16/19;
* по имени: Экспрессия (Expression/Destiny), Число души (Soul Urge/Heart's Desire),
  Личность (Personality), Зрелость/Реализация (Maturity), Кармические уроки, Скрытая страсть
  (Hidden Passion), Подсознательное «Я», Баланс (по инициалам Декоза и «по числу букв»
  galactica.ru), Рациональное мышление, Краеугольный камень/Замковый камень
  (Cornerstone/Capstone), первая гласная, мосты (Bridges), планы выражения (только латиница),
  «малые» числа текущего имени;
* алфавиты: русская кириллица (33 буквы, А=1 … Я=6 по кругу 1–9) и латиница;
  системы: пифагорейская и халдейская (таблица Кейро, без 9). Для халдейской системы
  кириллица транслитерируется по ICAO Doc 9303 (как в загранпаспорте РФ).

Ничего, кроме стандартной библиотеки, не требуется.
"""
from __future__ import annotations

import re
import unicodedata
from datetime import date
from typing import Any, Iterable

from .common.time import BirthInput

METHOD = "numerology"

# ---------------------------------------------------------------------------
# Справочные таблицы
# ---------------------------------------------------------------------------

#: Русский алфавит (33 буквы, порядок по ГОСТ/словарям: Ё после Е).
RU_ALPHABET = "АБВГДЕЁЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯ"
#: Пифагорейская таблица для кириллицы: номер буквы в алфавите, сведённый к 1–9.
#: 1: А И С Ъ | 2: Б Й Т Ы | 3: В К У Ь | 4: Г Л Ф Э | 5: Д М Х Ю | 6: Е Н Ц Я |
#: 7: Ё О Ч | 8: Ж П Ш | 9: З Р Щ
RU_PYTHAGOREAN: dict[str, int] = {ch: (i % 9) + 1 for i, ch in enumerate(RU_ALPHABET)}

LATIN_ALPHABET = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
#: Пифагорейская таблица для латиницы: A=1 … I=9, J=1 … R=9, S=1 … Z=8.
LATIN_PYTHAGOREAN: dict[str, int] = {ch: (i % 9) + 1 for i, ch in enumerate(LATIN_ALPHABET)}

#: Халдейская таблица (Cheiro, «Cheiro's Book of Numbers», 1926): цифры 1–8, девятки нет.
LATIN_CHALDEAN: dict[str, int] = {
    "A": 1, "B": 2, "C": 3, "D": 4, "E": 5, "F": 8, "G": 3, "H": 5, "I": 1,
    "J": 1, "K": 2, "L": 3, "M": 4, "N": 5, "O": 7, "P": 8, "Q": 1, "R": 2,
    "S": 3, "T": 4, "U": 6, "V": 6, "W": 6, "X": 5, "Y": 1, "Z": 7,
}

#: Гласные. Для русского — 10 гласных букв; Й, Ъ, Ь гласными не считаются.
RU_VOWELS = frozenset("АЕЁИОУЫЭЮЯ")
LATIN_VOWELS = frozenset("AEIOU")  # Y — по правилу (см. _latin_y_is_vowel), W — всегда согласная

#: Транслитерация ICAO Doc 9303 (загранпаспорт РФ, приказ ФМС № 320, 2013).
ICAO_9303: dict[str, str] = {
    "А": "A", "Б": "B", "В": "V", "Г": "G", "Д": "D", "Е": "E", "Ё": "E", "Ж": "ZH",
    "З": "Z", "И": "I", "Й": "I", "К": "K", "Л": "L", "М": "M", "Н": "N", "О": "O",
    "П": "P", "Р": "R", "С": "S", "Т": "T", "У": "U", "Ф": "F", "Х": "KH", "Ц": "TS",
    "Ч": "CH", "Ш": "SH", "Щ": "SHCH", "Ъ": "IE", "Ы": "Y", "Ь": "", "Э": "E",
    "Ю": "IU", "Я": "IA",
}

#: Планы выражения (Planes of Expression) Декоза — только для латиницы.
PLANES_LATIN: dict[str, frozenset[str]] = {
    "physical": frozenset("DEMW"),
    "mental": frozenset("AGHJLNP"),
    "emotional": frozenset("BIORSTXZ"),
    "intuitive": frozenset("CFKQUVY"),
}

MASTER_NUMBERS = (11, 22, 33)
KARMIC_DEBT = (13, 14, 16, 19)

#: Короткие ключи интерпретации (подробная таблица — в базе знаний, раздел 8).
KEYWORDS: dict[int, str] = {
    0: "ноль (только в испытаниях): выбор из всех уроков, «испытание 9»",
    1: "лидерство, независимость, инициатива; тень — эгоизм, упрямство",
    2: "партнёрство, дипломатия, чуткость; тень — зависимость, нерешительность",
    3: "самовыражение, общение, творчество; тень — разбросанность, поверхностность",
    4: "труд, порядок, надёжность; тень — косность, ограниченность",
    5: "свобода, перемены, разнообразие; тень — непостоянство, излишества",
    6: "ответственность, забота, семья, гармония; тень — контроль, жертвенность",
    7: "анализ, поиск истины, уединение, духовность; тень — замкнутость, недоверие",
    8: "власть, деньги, управление, достижения; тень — материализм, жёсткость",
    9: "гуманизм, завершение, сострадание; тень — отстранённость, разочарование",
    11: "мастер-число: интуиция, вдохновение, «посланник»; проявляется и как 2",
    22: "мастер-число: «мастер-строитель», большие проекты; проявляется и как 4",
    33: "мастер-число: «мастер-учитель», служение и забота; проявляется и как 6",
    13: "кармический долг 13 (→4): лень в прошлом — урок труда и сосредоточенности",
    14: "кармический долг 14 (→5): злоупотребление свободой — урок меры и обязательности",
    16: "кармический долг 16 (→7): падение эго — разрушение старого ради роста",
    19: "кармический долг 19 (→1): злоупотребление властью — урок взаимозависимости",
}

LIFE_PATH_METHODS = ("reduce_components", "all_digits", "add_whole_numbers")
SYSTEMS = ("pythagorean", "chaldean")
ALPHABETS = ("auto", "ru", "latin")
NAME_METHODS = ("parts", "all_letters")
Y_RULES = ("decoz", "vowel", "consonant")
RU_SIGNS = ("consonant", "ignore")
NAME_ORDERS = ("auto", "surname_first", "given_first")
PY_BOUNDARIES = ("calendar", "birthday")

_PATRONYMIC_RE = re.compile(r"(ОВИЧ|ЕВИЧ|ЬИЧ|ИЧ|ОВНА|ЕВНА|ИЧНА|ИНИЧНА|ОГЛЫ|КЫЗЫ|УЛЫ)$")
_RU_SURNAME_RE = re.compile(
    r"(ОВ|ЕВ|ЁВ|ИН|ЫН|ОВА|ЕВА|ЁВА|ИНА|ЫНА|СКИЙ|ЦКИЙ|СКАЯ|ЦКАЯ|ОЙ|ИХ|ЫХ|ЕНКО|УК|ЮК|ЧУК|ЕЦ)$"
)
#: Частые личные имена, которые по окончанию похожи на фамилию (Ирина, Екатерина, Лев…).
#: Без этого списка «Ирина Петрова» распознавалась как «Фамилия Имя».
_RU_GIVEN_LOOKALIKES = frozenset((
    "ЛЕВ", "ЯКОВ", "КОНСТАНТИН", "ВАЛЕНТИН", "ВЕНИАМИН", "ЕВА",
    "ИРИНА", "МАРИНА", "АЛИНА", "ПОЛИНА", "КРИСТИНА", "КАРИНА", "АРИНА", "ГАЛИНА", "НИНА",
    "ДИНА", "ВАЛЕНТИНА", "РЕГИНА", "АНГЕЛИНА", "КАРОЛИНА", "ЕКАТЕРИНА", "ЯНИНА", "ЭВЕЛИНА",
    "ЗАРИНА", "ДАРИНА", "АЛЕВТИНА", "ЛИНА", "ИНА", "МАЛЬВИНА", "ЗИНА",
))
#: Латинские буквы, которые Unicode-разложение (NFKD) не сводит к базовой: Ł, Đ, Ħ, ı.
_LATIN_EXTRA = {"Ł": "L", "ł": "L", "Đ": "D", "đ": "D", "Ħ": "H", "ħ": "H", "ı": "I", "Ŧ": "T", "ŧ": "T"}


# ---------------------------------------------------------------------------
# Базовая арифметика
# ---------------------------------------------------------------------------

def digit_sum(n: int) -> int:
    """Сумма цифр неотрицательного целого числа."""
    return sum(int(c) for c in str(abs(int(n))))


def reduce_chain(n: int, masters: Iterable[int] = MASTER_NUMBERS) -> list[int]:
    """Нумерологическое сведение с цепочкой: [n, …, итог].

    Сводим, пока число > 9 и не является мастер-числом из ``masters``.
    Пример: reduce_chain(1990) == [1990, 19, 10, 1]; reduce_chain(29) == [29, 11].
    """
    masters = tuple(masters)
    chain = [int(n)]
    while chain[-1] > 9 and chain[-1] not in masters:
        chain.append(digit_sum(chain[-1]))
    return chain


def reduce_number(n: int, masters: Iterable[int] = MASTER_NUMBERS) -> int:
    """Итог нумерологического сведения (см. reduce_chain)."""
    return reduce_chain(n, masters)[-1]


def to_single(n: int) -> int:
    """Свести до одной цифры без мастер-чисел (11→2, 22→4, 33→6); 0 остаётся 0."""
    return reduce_number(n, ())


def notation(chain: list[int]) -> str:
    """Запись цепочки через «/»: «19/10/1», «16/7», «22».

    Однозначное число записывается одной цифрой («8»). Программа Декоза пишет день
    рождения как «8/8» и пропускает промежуточное мастер-число в сведённых числах
    («29/2» для Зрелости). Значения от этого не меняются.
    """
    if len(chain) == 1:
        return str(chain[0])
    return "/".join(str(x) for x in chain)


def karmic_in_chain(chain: list[int]) -> int | None:
    """Кармический долг: 13/14/16/19 среди промежуточных значений цепочки (кроме итога)."""
    for v in chain[:-1]:
        if v in KARMIC_DEBT:
            return v
    return None


def _num(chain: list[int], **extra: Any) -> dict[str, Any]:
    """Стандартная запись числа в результате."""
    out: dict[str, Any] = {
        "value": chain[-1],
        "compound": chain[0],
        "chain": chain,
        "notation": notation(chain),
        "is_master": chain[-1] in MASTER_NUMBERS,
        "single": to_single(chain[-1]),
        "karmic_debt": karmic_in_chain(chain),
    }
    out.update(extra)
    return out


def _parse_masters(v: Any, default: tuple[int, ...]) -> tuple[int, ...]:
    """Опция-список мастер-чисел: кортеж, список или строка «11,22»; пустая строка/«none» — нет."""
    if v is None:
        return default
    if isinstance(v, str):
        s = v.strip().lower()
        if s in ("", "none", "no", "false", "0"):
            return ()
        return tuple(int(x) for x in re.split(r"[,\s;]+", s) if x)
    if isinstance(v, int):
        return (v,)
    return tuple(int(x) for x in v)


def _parse_date(v: Any) -> date:
    if v is None:
        return date.today()
    if isinstance(v, date):
        return v
    y, m, d = (int(x) for x in str(v).strip()[:10].split("-"))
    return date(y, m, d)


# ---------------------------------------------------------------------------
# Числа по дате рождения
# ---------------------------------------------------------------------------

def life_path(day: int, month: int, year: int, method: str = "reduce_components",
              masters: Iterable[int] = MASTER_NUMBERS,
              component_masters: Iterable[int] = MASTER_NUMBERS) -> dict[str, Any]:
    """Число жизненного пути тремя способами.

    * ``reduce_components`` — месяц, день и год сводятся отдельно (мастер-числа в
      компонентах сохраняются), затем сумма сводится (Декоз, galactica.ru);
    * ``all_digits`` — сумма всех цифр даты ДД.ММ.ГГГГ, затем сведение
      (популярно на русских сайтах, «горизонтальное» сложение слева направо);
    * ``add_whole_numbers`` — день + месяц + год как целые числа (15 + 10 + 1998 = 2023),
      затем сведение («вертикальное» сложение столбиком).
    """
    masters = tuple(masters)
    cm = tuple(component_masters)
    if method == "reduce_components":
        mc, dc, yc = reduce_chain(month, cm), reduce_chain(day, cm), reduce_chain(year, cm)
        total = mc[-1] + dc[-1] + yc[-1]
        chain = reduce_chain(total, masters)
        step = (f"месяц {notation(mc)}; день {notation(dc)}; год {notation(yc)}; "
                f"{mc[-1]} + {dc[-1]} + {yc[-1]} = {notation(chain)}")
        return _num(chain, method=method,
                    components={"month": mc, "day": dc, "year": yc}, step=step)
    if method == "all_digits":
        digits = [int(c) for c in f"{day:02d}{month:02d}{year:04d}"]
        total = sum(digits)
        chain = reduce_chain(total, masters)
        step = " + ".join(str(x) for x in digits) + f" = {notation(chain)}"
        return _num(chain, method=method, digits=digits, step=step)
    if method == "add_whole_numbers":
        total = day + month + year
        chain = reduce_chain(total, masters)
        step = f"{day} + {month} + {year} = {notation(chain)}"
        return _num(chain, method=method, step=step)
    raise ValueError(f"life_path_method должен быть одним из {LIFE_PATH_METHODS}")


def pinnacles_and_challenges(day: int, month: int, year: int, lp_value: int,
                             component_masters: Iterable[int] = MASTER_NUMBERS,
                             pinnacle_masters: Iterable[int] = MASTER_NUMBERS) -> dict[str, Any]:
    """Вершины (Pinnacles), испытания (Challenges) и периоды (Period Cycles).

    Возрасты — соглашение Декоза (сайт и программа 2020-х): первая вершина длится от
    рождения до возраста T = 36 − ЧЖП (мастер-ЧЖП сначала сводится: 11→2, 22→4, 33→6),
    вторая [T, T+9), третья [T+9, T+18), четвёртая [T+18, ∞).
    Календарные годы — соглашение galactica.ru: вершина заканчивается 31 декабря года,
    в котором исполняется T лет, следующая начинается 1 января.
    """
    cm, pm = tuple(component_masters), tuple(pinnacle_masters)
    m, d, y = reduce_number(month, cm), reduce_number(day, cm), reduce_number(year, cm)
    lp1 = to_single(lp_value)
    t = 36 - lp1

    p1 = reduce_chain(m + d, pm)
    p2 = reduce_chain(d + y, pm)
    p3 = reduce_chain(p1[-1] + p2[-1], pm)
    p4 = reduce_chain(m + y, pm)
    spans = [(0, t), (t, t + 9), (t + 9, t + 18), (t + 18, None)]
    pinnacles = []
    for i, (ch, (a, b), formula) in enumerate(zip(
            (p1, p2, p3, p4), spans,
            (f"месяц {m} + день {d}", f"день {d} + год {y}",
             f"I {p1[-1]} + II {p2[-1]}", f"месяц {m} + год {y}")), start=1):
        # календарные годы galactica: I — с года рождения по год (рождение + T) включительно,
        # каждая следующая — с 1 января следующего года
        pinnacles.append(_num(
            ch, index=i, formula=formula, age_from=a, age_to=b,
            years_from=year if i == 1 else year + a + 1,
            years_to=(year + b) if b is not None else None,
        ))

    ms, ds, ys = to_single(month), to_single(day), to_single(year)
    c1, c2 = abs(ms - ds), abs(ds - ys)
    c3, c4 = abs(c1 - c2), abs(ms - ys)
    challenges = [
        {"index": 1, "value": c1, "formula": f"|месяц {ms} − день {ds}|", "period": "≈ от рождения до 30–35 лет"},
        {"index": 2, "value": c2, "formula": f"|день {ds} − год {ys}|", "period": "≈ от 30–35 до 55–60 лет"},
        {"index": 3, "value": c3, "formula": f"|I {c1} − II {c2}|", "period": "главное, всю жизнь"},
        {"index": 4, "value": c4, "formula": f"|месяц {ms} − год {ys}|", "period": "≈ с 55–60 лет"},
    ]

    periods = [
        _num(reduce_chain(month, cm), index=1, source="месяц", age_from=0, age_to=t),
        _num(reduce_chain(day, cm), index=2, source="день", age_from=t, age_to=t + 27),
        _num(reduce_chain(year, cm), index=3, source="год", age_from=t + 27, age_to=None),
    ]
    return {"first_pinnacle_end_age": t, "lp_single_for_ages": lp1,
            "components": {"month": m, "day": d, "year": y},
            "pinnacles": pinnacles, "challenges": challenges, "period_cycles": periods}


def personal_cycles(b_day: int, b_month: int, on: date, boundary: str = "calendar") -> dict[str, Any]:
    """Личный год/месяц/день (Personal Year/Month/Day).

    ЛГ = свести(свести(месяц) + свести(день) + свести(год)) до одной цифры; мастер-11/22,
    встретившиеся в цепочке, отмечаются флагом ``master_in_chain``.
    ЛМ = свести(ЛГ + номер календарного месяца); ЛД = свести(ЛМ + число месяца).
    ``boundary='calendar'`` — год меняется 1 января (Декоз, galactica.ru, большинство);
    ``boundary='birthday'`` — меняется в день рождения (меньшинство школ).
    Для 29 февраля в невисокосный год день рождения считается наступившим 1 марта.
    """
    if boundary not in PY_BOUNDARIES:
        raise ValueError(f"personal_year_boundary должен быть одним из {PY_BOUNDARIES}")
    year = on.year
    if boundary == "birthday" and (on.month, on.day) < (b_month, b_day):
        year -= 1
    mm, dd, yy = reduce_number(b_month, (11, 22)), reduce_number(b_day, (11, 22)), reduce_number(year, (11, 22))
    chain = reduce_chain(mm + dd + yy, ())
    py = chain[-1]
    pm_chain = reduce_chain(py + on.month, ())
    pd_chain = reduce_chain(pm_chain[-1] + on.day, ())
    uy = reduce_chain(year, ())
    return {
        "on_date": on.isoformat(),
        "boundary": boundary,
        "cycle_year": year,
        "universal_year": {"value": uy[-1], "chain": uy},
        "personal_year": {"value": py, "chain": chain, "notation": notation(chain),
                          "master_in_chain": next((v for v in chain if v in (11, 22)), None),
                          "step": f"месяц {mm} + день {dd} + год {year}→{yy} = {notation(chain)}"},
        "personal_month": {"value": pm_chain[-1], "chain": pm_chain,
                           "step": f"ЛГ {py} + месяц {on.month} = {notation(pm_chain)}"},
        "personal_day": {"value": pd_chain[-1], "chain": pd_chain,
                         "step": f"ЛМ {pm_chain[-1]} + число {on.day} = {notation(pd_chain)}"},
    }


# ---------------------------------------------------------------------------
# Имя: нормализация, разбор, таблицы
# ---------------------------------------------------------------------------

def _is_cyrillic(ch: str) -> bool:
    return "А" <= ch <= "я" or ch in "Ёё"


def detect_alphabet(name: str) -> str:
    """'ru' если в имени есть кириллица, иначе 'latin'."""
    return "ru" if any(_is_cyrillic(c) for c in name) else "latin"


def pick_name_variant(name: str, alphabet: str) -> tuple[str, list[str]]:
    """Имя может содержать варианты через «/» («Эйнштейн Альберт / Albert Einstein»).

    Возвращает (выбранный вариант, все варианты). Для alphabet='auto' берётся первый.
    """
    variants = [v.strip() for v in name.split("/") if v.strip()]
    if not variants:
        return "", []
    if alphabet in ("ru", "latin"):
        for v in variants:
            if detect_alphabet(v) == alphabet:
                return v, variants
    return variants[0], variants


def _strip_latin_diacritics(s: str) -> str:
    s = s.replace("ß", "SS").replace("ẞ", "SS").replace("Æ", "AE").replace("æ", "AE")
    s = s.replace("Ø", "O").replace("ø", "O").replace("Œ", "OE").replace("œ", "OE")
    s = "".join(_LATIN_EXTRA.get(ch, ch) for ch in s)
    out = []
    for ch in s:
        if _is_cyrillic(ch):
            out.append(ch)  # Й/Ё не разлагаем
            continue
        dec = unicodedata.normalize("NFKD", ch)
        out.append("".join(c for c in dec if not unicodedata.combining(c)))
    return "".join(out)


def transliterate_icao(text: str) -> str:
    """Кириллица → латиница по ICAO Doc 9303 (загранпаспорт РФ с 2013 г.)."""
    return "".join(ICAO_9303.get(ch, ch) for ch in text.upper())


def split_name(name: str, alphabet: str, yo_as_e: bool = False,
               ru_signs: str = "consonant", dropped: list[str] | None = None) -> list[str]:
    """Разбить имя на части (слова) в верхнем регистре, оставив только буквы алфавита.

    Дефис и апостроф склеивают части («Анна-Мария» → «АННАМАРИЯ»).
    Если передан список ``dropped``, в него складываются отброшенные буквы, которых нет
    в таблице алфавита (украинские І/Ї/Є/Ґ, латиница внутри кириллического имени и т. п.).
    """
    name = name.replace("-", "").replace("‐", "").replace("'", "").replace("’", "")
    parts: list[str] = []
    for raw in name.split():
        w = raw.upper()
        if alphabet == "ru":
            if yo_as_e:
                w = w.replace("Ё", "Е")
            if ru_signs == "ignore":
                w = w.replace("Ъ", "").replace("Ь", "")
            table = RU_PYTHAGOREAN
        else:
            w = _strip_latin_diacritics(w)
            table = LATIN_PYTHAGOREAN
        if dropped is not None:
            dropped += [c for c in w if c.isalpha() and c not in table]
        w = "".join(c for c in w if c in table)
        if w:
            parts.append(w)
    return parts


def _latin_y_is_vowel(word: str, i: int) -> tuple[bool, str]:
    """Правило «Y — гласная или согласная» по Декозу (worldnumerology.com).

    Возвращает (гласная?, номер правила). Правила 7–8 — «по умолчанию согласная,
    бывают исключения» (Bryan, Wyatt — гласная).
    """
    prev = word[i - 1] if i > 0 else None
    nxt = word[i + 1] if i + 1 < len(word) else None

    def v(c: str | None) -> bool:
        return c is not None and c in LATIN_VOWELS

    if prev is None and nxt is None:
        return True, "single"
    if prev is None:
        return (False, "3") if v(nxt) else (True, "1")
    if nxt is None:
        return (False, "4") if v(prev) else (True, "2")
    if not v(prev) and not v(nxt):
        return True, "5"
    if v(prev) and v(nxt):
        return False, "6"
    if not v(prev) and v(nxt):
        return False, "7"
    return False, "8"


def classify_letters(word: str, alphabet: str, y_rule: str = "decoz") -> tuple[list[bool], list[str]]:
    """Для каждой буквы слова: гласная ли она. Плюс заметки о спорных Y."""
    notes: list[str] = []
    flags: list[bool] = []
    for i, ch in enumerate(word):
        if alphabet == "ru":
            flags.append(ch in RU_VOWELS)
            continue
        if ch == "Y":
            if y_rule == "vowel":
                flags.append(True)
            elif y_rule == "consonant":
                flags.append(False)
            else:
                is_v, rule = _latin_y_is_vowel(word, i)
                flags.append(is_v)
                if rule in ("7", "8"):
                    notes.append(f"Y в «{word}» (позиция {i + 1}) по умолчанию согласная (правило {rule} Декоза), "
                                 f"но если Y — единственный гласный звук слога (Bryan, Wyatt), считайте её гласной: "
                                 f"опция y_rule='vowel'.")
        else:
            flags.append(ch in LATIN_VOWELS)
    return flags, notes


def letter_table(alphabet: str, system: str) -> dict[str, int]:
    if system == "chaldean":
        return LATIN_CHALDEAN
    return RU_PYTHAGOREAN if alphabet == "ru" else LATIN_PYTHAGOREAN


def _detect_given_index(parts: list[str], alphabet: str, order: str) -> tuple[int, str, list[str]]:
    """Индекс личного имени среди частей и принятый порядок; плюс предупреждения."""
    warns: list[str] = []
    n = len(parts)
    if n == 0:
        return 0, order, warns
    if order == "given_first":
        return 0, order, warns
    if order == "surname_first":
        return (1 if n >= 2 else 0), order, warns
    # auto
    if alphabet != "ru":
        return 0, "given_first", warns
    if n >= 3:
        if _PATRONYMIC_RE.search(parts[1]):
            return 0, "given_first", warns          # Имя Отчество Фамилия
        if _PATRONYMIC_RE.search(parts[-1]):
            return 1, "surname_first", warns        # Фамилия Имя Отчество
        warns.append("Не удалось распознать отчество: принят порядок «Фамилия Имя Отчество». "
                     "Укажите name_order или first_name.")
        return 1, "surname_first", warns
    if n == 2:
        def surname_like(p: str) -> bool:
            return bool(_RU_SURNAME_RE.search(p)) and p not in _RU_GIVEN_LOOKALIKES
        s0, s1 = surname_like(parts[0]), surname_like(parts[1])
        if s1 and not s0:
            return 0, "given_first", warns
        if not (s0 and not s1):
            warns.append("Порядок двух частей имени неочевиден: принято «Фамилия Имя». "
                         "Укажите name_order или first_name.")
        return 1, "surname_first", warns
    return 0, "given_first", warns


# ---------------------------------------------------------------------------
# Числа по имени
# ---------------------------------------------------------------------------

def _name_number(part_sums: list[int], method: str, part_masters: tuple[int, ...],
                 masters: tuple[int, ...]) -> dict[str, Any]:
    """Сведение числа имени: по частям (Декоз, galactica) или всех букв сразу."""
    if method == "parts":
        reduced = [reduce_chain(s, part_masters) for s in part_sums]
        total = sum(r[-1] for r in reduced)
        chain = reduce_chain(total, masters)
        step = " + ".join(notation(r) for r in reduced) + f" → {' + '.join(str(r[-1]) for r in reduced)} = {notation(chain)}"
        return _num(chain, method=method, parts=[r for r in reduced], step=step)
    total = sum(part_sums)
    chain = reduce_chain(total, masters)
    step = " + ".join(str(s) for s in part_sums) + f" = {notation(chain)}"
    return _num(chain, method=method, step=step)


def analyze_name(name: str, *, alphabet: str = "auto", system: str = "pythagorean",
                 name_method: str = "parts", masters: Iterable[int] = MASTER_NUMBERS,
                 part_masters: Iterable[int] = MASTER_NUMBERS, y_rule: str = "decoz",
                 ru_signs: str = "consonant", yo_as_e: bool = False,
                 name_order: str = "auto", first_name: str | None = None) -> dict[str, Any]:
    """Числа имени: Экспрессия, Душа, Личность, уроки, страсть, баланс и т. д.

    Для системы 'chaldean' кириллица транслитерируется (ICAO 9303), мастер-числа не
    сохраняются (у Кейро их нет), а составное число имени считается как у Кейро:
    сумма однозначных чисел слов.
    """
    warnings: list[str] = []
    masters, part_masters = tuple(masters), tuple(part_masters)
    if system not in SYSTEMS:
        raise ValueError(f"system должен быть одним из {SYSTEMS}")
    if name_method not in NAME_METHODS:
        raise ValueError(f"name_method должен быть одним из {NAME_METHODS}")
    if y_rule not in Y_RULES:
        raise ValueError(f"y_rule должен быть одним из {Y_RULES}")
    if ru_signs not in RU_SIGNS:
        raise ValueError(f"ru_signs должен быть одним из {RU_SIGNS}")

    chosen, variants = pick_name_variant(name, alphabet)
    alpha = detect_alphabet(chosen) if alphabet == "auto" else alphabet
    src_alpha = detect_alphabet(chosen)
    original = chosen
    if alpha == "latin" and src_alpha == "ru":
        chosen = transliterate_icao(chosen)
        warnings.append(f"Кириллица транслитерирована по ICAO 9303: «{original}» → «{chosen}». "
                        "Это вариант «имя из загранпаспорта», а не имя при рождении.")
    if alpha == "ru" and src_alpha == "latin":
        raise ValueError("Выбран алфавит 'ru', но имя записано латиницей.")
    if system == "chaldean" and alpha == "ru":
        chosen = transliterate_icao(chosen)
        alpha = "latin"
        warnings.append("Халдейская таблица определена только для латиницы (Кейро). Кириллица "
                        f"транслитерирована по ICAO 9303: «{original}» → «{chosen}». "
                        "⚠ Кириллических халдейских таблиц нет единых — не подтверждено.")
        masters = part_masters = ()
    elif system == "chaldean":
        masters = part_masters = ()

    if alpha == "ru" and "Ё" in original.upper() and not yo_as_e:
        warnings.append("В имени есть Ё (=7). Если в документе написано Е (=6), результат другой: "
                        "опция yo_as_e=True.")

    dropped: list[str] = []
    parts = split_name(chosen, alpha, yo_as_e=yo_as_e, ru_signs=ru_signs, dropped=dropped)
    if not parts:
        raise ValueError("В имени нет букв выбранного алфавита.")
    if dropped:
        warnings.append(
            f"Буквы {sorted(set(dropped))} не входят в таблицу алфавита «{alpha}» и НЕ учтены. "
            "Для украинских/белорусских букв (І, Ї, Є, Ґ, Ў) единой таблицы нет (⚠): передайте имя "
            "так, как оно записано в русском документе, или латиницей, как в загранпаспорте.")
    table = letter_table(alpha, system)

    given_idx, order_used, w = _detect_given_index(parts, alpha, name_order)
    warnings += w
    if first_name:
        fn = split_name(first_name, alpha, yo_as_e=yo_as_e, ru_signs=ru_signs)
        if fn and fn[0] in parts:
            given_idx = parts.index(fn[0])
        else:
            warnings.append(f"first_name «{first_name}» не найдено среди частей имени — проигнорировано.")

    part_info: list[dict[str, Any]] = []
    all_values: list[int] = []
    y_notes: list[str] = []
    for idx, word in enumerate(parts):
        flags, notes = classify_letters(word, alpha, y_rule)
        y_notes += notes
        vals = [table[c] for c in word]
        all_values += vals
        vs = sum(v for v, f in zip(vals, flags) if f)
        cs = sum(v for v, f in zip(vals, flags) if not f)
        part_info.append({
            "part": word,
            "role": "given" if idx == given_idx else "other",
            "letters": [[c, v, "V" if f else "C"] for c, v, f in zip(word, vals, flags)],
            "sum": sum(vals), "vowel_sum": vs, "consonant_sum": cs,
            "letter_count": len(word),
            "reduced": reduce_number(sum(vals), part_masters),
            "vowel_reduced": reduce_number(vs, part_masters),
            "consonant_reduced": reduce_number(cs, part_masters),
        })
    warnings += y_notes

    expression = _name_number([p["sum"] for p in part_info], name_method, part_masters, masters)
    soul = _name_number([p["vowel_sum"] for p in part_info], name_method, part_masters, masters)
    personality = _name_number([p["consonant_sum"] for p in part_info], name_method, part_masters, masters)

    given = parts[given_idx]
    gflags, _ = classify_letters(given, alpha, y_rule)
    first_vowel = next(((c, table[c]) for c, f in zip(given, gflags) if f), None)

    res: dict[str, Any] = {
        "name_used": " ".join(parts),
        "name_input": original,
        "name_variants": variants,
        "alphabet": alpha,
        "system": system,
        "name_order": order_used,
        "given_name": given,
        "parts": part_info,
        "letters_total": sum(all_values),
        "expression": expression,
        "soul_urge": soul,
        "personality": personality,
        "cornerstone": {"letter": given[0], "value": table[given[0]]},
        "capstone": {"letter": given[-1], "value": table[given[-1]]},
        "first_vowel": ({"letter": first_vowel[0], "value": first_vowel[1]} if first_vowel else None),
        "balance": _num(reduce_chain(sum(table[p[0]] for p in parts), ()),
                        initials=[p[0] for p in parts],
                        step=" + ".join(f"{p[0]}{table[p[0]]}" for p in parts)),
        "balance_letter_count": _num(reduce_chain(sum(len(p) for p in parts), ()),
                                     counts=[len(p) for p in parts]),
        "warnings": warnings,
    }

    if system == "pythagorean":
        counts = {k: all_values.count(k) for k in range(1, 10)}
        mx = max(counts.values())
        lessons = [k for k in range(1, 10) if counts[k] == 0]
        res.update({
            "inclusion_table": counts,
            "hidden_passion": {"values": [k for k in range(1, 10) if counts[k] == mx], "count": mx},
            "karmic_lessons": lessons,
            "subconscious_self": 9 - len(lessons),
        })
        if alpha == "latin":
            # Сумма всех букв плана, сведённая с мастер-числами: программа Декоза 2020-х
            # оставляет 11 (Tarriano: Mental 29/11). У Декоза 2003 мастер-сумм в планах нет.
            planes = {}
            for plane, letters in PLANES_LATIN.items():
                s = sum(table[c] for p in parts for c in p if c in letters)
                planes[plane] = _num(reduce_chain(s, masters))
            res["planes_of_expression"] = planes
    else:
        # Кейро: число имени = сумма однозначных чисел слов («Lloyd George» → 9 + 7 = 16/7)
        word_chains = [reduce_chain(p["sum"], ()) for p in part_info]
        total = sum(c[-1] for c in word_chains)
        chain = reduce_chain(total, ())
        res["chaldean_name_number"] = _num(
            chain, words=[{"word": p["part"], "compound": p["sum"], "single": c[-1]}
                          for p, c in zip(part_info, word_chains)],
            letters_total_chain=reduce_chain(sum(all_values), ()))
    return res


# ---------------------------------------------------------------------------
# Главная функция
# ---------------------------------------------------------------------------

def calculate(b: BirthInput, **options: Any) -> dict[str, Any]:
    """Полный нумерологический расчёт.

    Опции (по умолчанию — первая):
      name: str — переопределить b.name (ФИО при рождении);
      current_name: str — нынешнее/короткое имя → «малые» числа (Minor);
      alphabet: 'auto'|'ru'|'latin'; system: 'pythagorean'|'chaldean';
      life_path_method: 'reduce_components'|'all_digits'|'add_whole_numbers';
      masters: мастер-числа итоговых чисел, по умолчанию (11, 22, 33);
      part_masters: мастер-числа в компонентах даты и частях имени, по умолчанию (11, 22, 33);
      pinnacle_masters: по умолчанию (11, 22, 33); maturity_masters: по умолчанию () — как
        в программе Декоза (22+11=33→6, 7+22=29→2);
      name_method: 'parts'|'all_letters'; y_rule: 'decoz'|'vowel'|'consonant';
      ru_signs: 'consonant'|'ignore' (Ъ и Ь); yo_as_e: False;
      name_order: 'auto'|'surname_first'|'given_first'; first_name: str;
      on_date: 'YYYY-MM-DD' (для личного года; по умолчанию сегодня);
      personal_year_boundary: 'calendar'|'birthday'.
    """
    o = dict(options)
    system = o.get("system", "pythagorean")
    alphabet = o.get("alphabet", "auto")
    lp_method = o.get("life_path_method", "reduce_components")
    if system not in SYSTEMS:
        raise ValueError(f"system должен быть одним из {SYSTEMS}")
    if alphabet not in ALPHABETS:
        raise ValueError(f"alphabet должен быть одним из {ALPHABETS}")
    if lp_method not in LIFE_PATH_METHODS:
        raise ValueError(f"life_path_method должен быть одним из {LIFE_PATH_METHODS}")
    if o.get("name_order", "auto") not in NAME_ORDERS:
        raise ValueError(f"name_order должен быть одним из {NAME_ORDERS}")
    masters = _parse_masters(o.get("masters"), MASTER_NUMBERS)
    part_masters = _parse_masters(o.get("part_masters"), MASTER_NUMBERS)
    pinnacle_masters = _parse_masters(o.get("pinnacle_masters"), MASTER_NUMBERS)
    maturity_masters = _parse_masters(o.get("maturity_masters"), ())
    on = _parse_date(o.get("on_date"))
    boundary = o.get("personal_year_boundary", "calendar")
    yo_as_e = o.get("yo_as_e", False)
    if isinstance(yo_as_e, str):
        yo_as_e = yo_as_e.lower() == "true"

    warnings: list[str] = []
    steps: list[str] = []
    d, m, y = b.day, b.month, b.year
    date(y, m, d)  # валидация даты

    # --- дата ---
    lp_all = {meth: life_path(d, m, y, meth, masters, part_masters) for meth in LIFE_PATH_METHODS}
    lp = lp_all[lp_method]
    distinct = {meth: r["value"] for meth, r in lp_all.items()}
    if len(set(distinct.values())) > 1:
        warnings.append(f"Способы расчёта ЧЖП дают разные результаты: {distinct}. Принят «{lp_method}».")
    steps.append(f"ЧЖП ({lp_method}): {lp['step']}")
    for meth, r in lp_all.items():
        if meth != lp_method:
            steps.append(f"  для сравнения ЧЖП ({meth}): {r['step']}")

    bday_chain = reduce_chain(d, part_masters)
    birthday = _num(bday_chain, day=d)
    birthday["karmic_debt"] = d if d in KARMIC_DEBT else None
    steps.append(f"Число дня рождения: {notation(bday_chain)}")

    att_chain = reduce_chain(reduce_number(m, part_masters) + reduce_number(d, part_masters), part_masters)
    attitude = _num(att_chain, step=f"{reduce_number(m, part_masters)} + {reduce_number(d, part_masters)} "
                                    f"= {notation(att_chain)}")
    steps.append(f"Число отношения (месяц + день): {attitude['step']}")

    pc = pinnacles_and_challenges(d, m, y, lp["value"], part_masters, pinnacle_masters)
    steps.append(f"Вершины: T = 36 − {pc['lp_single_for_ages']} = {pc['first_pinnacle_end_age']}; "
                 + "; ".join(f"{p['index']}: {p['formula']} = {p['notation']} (возраст {p['age_from']}–"
                             f"{p['age_to'] if p['age_to'] is not None else '…'})" for p in pc["pinnacles"]))
    steps.append("Испытания: " + "; ".join(f"{c['index']}: {c['formula']} = {c['value']}" for c in pc["challenges"]))

    cycles = personal_cycles(d, m, on, boundary)
    steps.append(f"Личный год на {on.isoformat()} ({boundary}): {cycles['personal_year']['step']}; "
                 f"{cycles['personal_month']['step']}; {cycles['personal_day']['step']}")
    if boundary == "birthday" and (m, d) == (2, 29):
        warnings.append("Рождение 29 февраля: в невисокосный год смена личного года — 1 марта (⚠ соглашение модуля).")

    karmic: list[dict[str, Any]] = []
    if lp["karmic_debt"]:
        karmic.append({"number": lp["karmic_debt"], "where": "life_path"})
    if birthday["karmic_debt"]:
        karmic.append({"number": birthday["karmic_debt"], "where": "birthday"})

    result: dict[str, Any] = {
        "method": METHOD,
        "variant": f"{system}/{lp_method}",
        "inputs_used": {
            "date": date(y, m, d).isoformat(),
            "name": None,
            "options": {
                "system": system, "alphabet": alphabet, "life_path_method": lp_method,
                "masters": list(masters), "part_masters": list(part_masters),
                "pinnacle_masters": list(pinnacle_masters), "maturity_masters": list(maturity_masters),
                "name_method": o.get("name_method", "parts"), "y_rule": o.get("y_rule", "decoz"),
                "ru_signs": o.get("ru_signs", "consonant"), "yo_as_e": bool(yo_as_e),
                "name_order": o.get("name_order", "auto"),
                "on_date": on.isoformat(), "personal_year_boundary": boundary,
            },
        },
        "warnings": warnings,
        "date_numbers": {
            "life_path": lp,
            "life_path_by_method": lp_all,
            "birthday": birthday,
            "attitude": attitude,
            "period_cycles": pc["period_cycles"],
            "pinnacles": pc["pinnacles"],
            "first_pinnacle_end_age": pc["first_pinnacle_end_age"],
            "challenges": pc["challenges"],
        },
        "personal_cycles": cycles,
        "name_numbers": None,
        "bridges": {"life_path_birthday": abs(to_single(lp["value"]) - to_single(birthday["value"]))},
        "karmic_debts": karmic,
        "keywords": {},
        "steps": steps,
    }
    if system == "chaldean":
        bn = reduce_chain(d, ())
        result["date_numbers"]["chaldean_birth_number"] = _num(bn, step=f"день {d} → {notation(bn)}")

    # --- имя ---
    name = o.get("name") or b.name
    if not name:
        warnings.append("Имя не задано — числа имени не рассчитаны (нужно ФИО при рождении).")
    else:
        common = dict(alphabet=alphabet, system=system, name_method=o.get("name_method", "parts"),
                      masters=masters, part_masters=part_masters, y_rule=o.get("y_rule", "decoz"),
                      ru_signs=o.get("ru_signs", "consonant"), yo_as_e=bool(yo_as_e),
                      name_order=o.get("name_order", "auto"))
        nn = analyze_name(name, first_name=o.get("first_name"), **common)
        warnings += nn.pop("warnings")
        result["inputs_used"]["name"] = nn["name_used"]
        exp, soul, pers = nn["expression"], nn["soul_urge"], nn["personality"]

        mat_chain = reduce_chain(lp["value"] + exp["value"], maturity_masters)
        nn["maturity"] = _num(mat_chain, step=f"ЧЖП {lp['value']} + Экспрессия {exp['value']} = {notation(mat_chain)}")
        given_part = next(p for p in nn["parts"] if p["role"] == "given")
        rt_chain = reduce_chain(given_part["sum"] + d, ())
        nn["rational_thought"] = _num(rt_chain, step=f"имя {given_part['part']} {given_part['sum']} + день {d} "
                                                     f"= {notation(rt_chain)}")
        result["name_numbers"] = nn
        result["bridges"].update({
            "life_path_expression": abs(to_single(lp["value"]) - to_single(exp["value"])),
            "soul_personality": abs(to_single(soul["value"]) - to_single(pers["value"])),
        })
        for key, num in (("expression", exp), ("soul_urge", soul), ("personality", pers)):
            if num["karmic_debt"]:
                karmic.append({"number": num["karmic_debt"], "where": key})
        steps.append(f"Имя: {nn['name_used']} ({nn['alphabet']}, {system}); "
                     + "; ".join(f"{p['part']}: " + "+".join(str(l[1]) for l in p["letters"]) + f"={p['sum']}"
                                 for p in nn["parts"]))
        steps.append(f"Экспрессия: {exp['step']}")
        steps.append(f"Душа (гласные): {soul['step']}")
        steps.append(f"Личность (согласные): {pers['step']}")
        steps.append(f"Зрелость: {nn['maturity']['step']}")
        if system == "pythagorean":
            steps.append(f"Кармические уроки (нет цифр): {nn['karmic_lessons'] or 'нет'}; "
                         f"скрытая страсть: {nn['hidden_passion']['values']} ({nn['hidden_passion']['count']} раз)")
        else:
            cn = nn["chaldean_name_number"]
            steps.append("Число имени по Кейро: " + " + ".join(f"{w['word']} {w['compound']}/{w['single']}"
                                                              for w in cn["words"]) + f" = {cn['notation']}")

        cur = o.get("current_name")
        if cur:
            mn = analyze_name(cur, **common)
            warnings += [f"(текущее имя) {w}" for w in mn.pop("warnings")]
            result["name_numbers"]["minor"] = {
                "name_used": mn["name_used"],
                "expression": mn["expression"], "soul_urge": mn["soul_urge"],
                "personality": mn["personality"],
            }

    # ключи интерпретации для чисел, встретившихся в ядре
    core_vals = {lp["value"], birthday["value"]}
    if result["name_numbers"]:
        nn = result["name_numbers"]
        core_vals |= {nn["expression"]["value"], nn["soul_urge"]["value"], nn["personality"]["value"],
                      nn["maturity"]["value"]}
    core_vals |= {k["number"] for k in karmic}
    result["keywords"] = {str(v): KEYWORDS[v] for v in sorted(core_vals) if v in KEYWORDS}
    return result


__all__ = [
    "calculate", "life_path", "pinnacles_and_challenges", "personal_cycles", "analyze_name",
    "reduce_chain", "reduce_number", "to_single", "digit_sum", "transliterate_icao",
    "RU_PYTHAGOREAN", "LATIN_PYTHAGOREAN", "LATIN_CHALDEAN", "RU_VOWELS", "KEYWORDS",
]
