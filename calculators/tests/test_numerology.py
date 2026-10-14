"""Тесты калькулятора нумерологии (пифагорейская и халдейская системы, кириллица и латиница).

Запуск: .venv/bin/python -m pytest calculators/tests/test_numerology.py -q
Внешние векторы взяты из опубликованных источников (URL — в комментариях у каждого теста).
Эталонные персоны T1–T4 — из calculators/CONVENTIONS.md; их значения посчитаны вручную
в knowledge-base/11-numerology.md (раздел 7) и совпадают с кодом.
"""
from __future__ import annotations

import json
from datetime import date

import pytest

from calculators.common.time import BirthInput
from calculators.numerology import (
    LATIN_CHALDEAN, LATIN_PYTHAGOREAN, RU_PYTHAGOREAN, analyze_name, calculate, life_path,
    personal_cycles, pinnacles_and_challenges, reduce_chain, transliterate_icao,
)

ON = "2026-10-14"


def calc(name: str | None, y: int, m: int, d: int, **opt) -> dict:
    opt.setdefault("on_date", ON)
    return calculate(BirthInput(y, m, d, name=name), **opt)


def core(r: dict) -> dict:
    """Короткая сводка для сравнения."""
    dn, nn = r["date_numbers"], r["name_numbers"]
    out = {
        "lp": dn["life_path"]["value"], "lp_compound": dn["life_path"]["compound"],
        "birthday": dn["birthday"]["value"],
        "pinnacles": [p["value"] for p in dn["pinnacles"]],
        "challenges": [c["value"] for c in dn["challenges"]],
        "periods": [p["value"] for p in dn["period_cycles"]],
    }
    if nn:
        out.update({
            "exp": nn["expression"]["value"], "exp_compound": nn["expression"]["compound"],
            "soul": nn["soul_urge"]["value"], "soul_compound": nn["soul_urge"]["compound"],
            "pers": nn["personality"]["value"], "pers_compound": nn["personality"]["compound"],
            "maturity": nn["maturity"]["value"],
        })
    return out


# ---------------------------------------------------------------------------
# Таблицы и базовая арифметика
# ---------------------------------------------------------------------------

def test_russian_table_groups():
    # Таблица 33 букв: https://galactica.ru/numero/lessons/2 (и /4), https://kudago.com/all/news/numerologi-rasskazali-kak/
    groups = {1: "АИСЪ", 2: "БЙТЫ", 3: "ВКУЬ", 4: "ГЛФЭ", 5: "ДМХЮ", 6: "ЕНЦЯ", 7: "ЁОЧ", 8: "ЖПШ", 9: "ЗРЩ"}
    for v, letters in groups.items():
        for ch in letters:
            assert RU_PYTHAGOREAN[ch] == v, ch
    assert len(RU_PYTHAGOREAN) == 33


def test_latin_tables():
    assert [LATIN_PYTHAGOREAN[c] for c in "AIJRSZ"] == [1, 9, 1, 9, 1, 8]
    # Кейро (Cheiro's Book of Numbers, 1926), https://archive.org/details/numerology-cheiro : нет девятки
    assert set(LATIN_CHALDEAN.values()) == set(range(1, 9))
    assert [LATIN_CHALDEAN[c] for c in "AFOPZ"] == [1, 8, 7, 8, 7]


def test_reduce_chain():
    assert reduce_chain(1990) == [1990, 19, 10, 1]
    assert reduce_chain(29) == [29, 11]
    assert reduce_chain(29, ()) == [29, 11, 2]
    assert reduce_chain(1984) == [1984, 22]
    assert reduce_chain(33, (11, 22)) == [33, 6]


def test_icao_transliteration():
    # ICAO Doc 9303 (приказ ФМС № 320): https://en.wikipedia.org/wiki/Romanization_of_Russian
    assert transliterate_icao("Щукина Юлия") == "SHCHUKINA IULIIA"
    assert transliterate_icao("Хрущёв") == "KHRUSHCHEV"


# ---------------------------------------------------------------------------
# Число жизненного пути: внешние векторы
# ---------------------------------------------------------------------------

def test_life_path_decoz_examples():
    # https://www.worldnumerology.com/numerology-life-path/ и https://www.worldnumerology.com/do-your-own-reading/
    assert life_path(12, 8, 1990)["value"] == 3                     # 8 + 3 + 1 = 12 → 3
    r = life_path(22, 11, 1983)                                      # 11 + 22 + 3 = 36 → 9
    assert r["components"]["month"][-1] == 11 and r["components"]["day"][-1] == 22
    assert r["chain"] == [36, 9]
    r = life_path(15, 10, 1998)                                      # 1 + 6 + 9 = 16 → 7, долг 16
    assert r["chain"] == [16, 7] and r["karmic_debt"] == 16
    # «неправильные» по Декозу способы: 34 → 7 и 2023 → 7 — долг 16 теряется
    assert life_path(15, 10, 1998, "all_digits")["chain"] == [34, 7]
    assert life_path(15, 10, 1998, "add_whole_numbers")["chain"] == [2023, 7]
    assert life_path(15, 10, 1998, "all_digits")["karmic_debt"] is None


def test_life_path_galactica_examples():
    # https://galactica.ru/numero/lessons/2 и https://galactica.ru/numero/lessons/3
    assert life_path(19, 12, 1906)["value"] == 11      # Брежнев: 1 + 3 + 7 = 11
    assert life_path(19, 8, 1946)["value"] == 11       # Клинтон: 1 + 8 + 2 = 11
    r = life_path(11, 5, 1953)                         # Подводный: 11 + 5 + 9 = 25 → 7
    assert r["chain"] == [25, 7] and r["components"]["day"] == [11]
    assert life_path(12, 4, 1949)["value"] == 3        # Куклачёв
    # 01.04.1961: правильно 1 + 4 + 8 = 13 → 4 (долг 13), «все цифры сразу» — ложное 22
    r = life_path(1, 4, 1961)
    assert r["chain"] == [13, 4] and r["karmic_debt"] == 13
    assert life_path(1, 4, 1961, "all_digits")["value"] == 22


def test_life_path_all_digits_calculator():
    # https://calcforlife.com/?p=2372 : 24.07.1990 → 1+9+9+0+0+7+2+4 = 32 → 5
    assert life_path(24, 7, 1990, "all_digits")["chain"] == [32, 5]


# ---------------------------------------------------------------------------
# Вершины, испытания, личный год: внешние векторы
# ---------------------------------------------------------------------------

def test_pinnacles_decoz_and_galactica():
    # https://www.worldnumerology.com/numerology-pinnacles/ : 15.05.1949 → 11, 11, 22, 1
    lp = life_path(15, 5, 1949)["value"]
    pc = pinnacles_and_challenges(15, 5, 1949, lp)
    assert [p["value"] for p in pc["pinnacles"]] == [11, 11, 22, 1]
    # 5 ноября: 11 + 5 = 16 → 7
    assert pinnacles_and_challenges(5, 11, 2000, 1)["pinnacles"][0]["value"] == 7
    # Пётр I, 30.05.1672, ЧЖП 6: https://galactica.ru/numero/lessons/12
    pc = pinnacles_and_challenges(30, 5, 1672, life_path(30, 5, 1672)["value"])
    assert [p["value"] for p in pc["pinnacles"]] == [8, 1, 9, 3]
    assert pc["first_pinnacle_end_age"] == 30
    assert [(p["years_from"], p["years_to"]) for p in pc["pinnacles"]] == [
        (1672, 1702), (1703, 1711), (1712, 1720), (1721, None)]


def test_challenges_external():
    # Том Круз 3.07.1962: https://www.worldnumerology.com/numerology-challenges/ → 4, 6, 2, 2
    ch = pinnacles_and_challenges(3, 7, 1962, 1)["challenges"]
    assert [c["value"] for c in ch] == [4, 6, 2, 2]
    # 01.04.1961: https://galactica.ru/numero/lessons/16 → 3, 7, 4, 4
    ch = pinnacles_and_challenges(1, 4, 1961, 4)["challenges"]
    assert [c["value"] for c in ch] == [3, 7, 4, 4]


def test_personal_cycles_external():
    # Декоз: 15 мая, 2026 → 3; февраль → 5; 3 февраля → 8 (https://www.worldnumerology.com/do-your-own-reading/)
    pc = personal_cycles(15, 5, date(2026, 2, 3))
    assert (pc["personal_year"]["value"], pc["personal_month"]["value"], pc["personal_day"]["value"]) == (3, 5, 8)
    # Декоз: 12 апреля, 2021 → 3; январь → 4 (https://www.worldnumerology.com/personal-numerology-forecast/)
    pc = personal_cycles(12, 4, date(2021, 1, 10))
    assert (pc["personal_year"]["value"], pc["personal_month"]["value"]) == (3, 4)
    # galactica: 16 ноября, 2003 → 7 + 11 + 5 = 23 → 5 (https://galactica.ru/numero/lessons/11)
    pc = personal_cycles(16, 11, date(2003, 6, 1))
    assert pc["personal_year"]["chain"] == [23, 5]
    # roxyapi: 15 июня, 2026 → 4 (https://roxyapi.com/tools/numerology/personal-year)
    assert personal_cycles(15, 6, date(2026, 7, 1))["personal_year"]["value"] == 4


def test_personal_year_birthday_boundary_and_feb29():
    # До дня рождения при границе «birthday» действует прошлый год
    cal = personal_cycles(15, 5, date(2026, 3, 1), "calendar")
    bd = personal_cycles(15, 5, date(2026, 3, 1), "birthday")
    assert cal["cycle_year"] == 2026 and bd["cycle_year"] == 2025
    assert bd["personal_year"]["value"] == (cal["personal_year"]["value"] - 2) % 9 + 1
    # 29 февраля в невисокосный год: 28.02 — ещё старый год, 01.03 — новый
    assert personal_cycles(29, 2, date(2025, 2, 28), "birthday")["cycle_year"] == 2024
    assert personal_cycles(29, 2, date(2025, 3, 1), "birthday")["cycle_year"] == 2025


# ---------------------------------------------------------------------------
# Числа имени: внешние векторы (латиница)
# ---------------------------------------------------------------------------

def test_expression_tom_cruise_decoz():
    # https://www.worldnumerology.com/numerology-expression-number.htm : Thomas 22 (мастер), Cruise 30/3, Mapother 42/6 → 31/4
    nn = analyze_name("Thomas Cruise Mapother")
    assert [p["sum"] for p in nn["parts"]] == [22, 30, 42]
    assert nn["expression"]["chain"] == [31, 4]
    # «все буквы сразу»: 94 → 13 → 4 — тот же итог, но появляется кармический долг 13
    alt = analyze_name("Thomas Cruise Mapother", name_method="all_letters")
    assert alt["expression"]["chain"] == [94, 13, 4] and alt["expression"]["karmic_debt"] == 13


def test_soul_urge_hancock_decoz():
    # https://www.worldnumerology.com/numerology-soul-urge/ : 7 + 6 + 7 = 20 → 2
    nn = analyze_name("Thomas John Hancock")
    assert [p["vowel_sum"] for p in nn["parts"]] == [7, 6, 7]
    assert nn["soul_urge"]["chain"] == [20, 2]


DECOZ_SAMPLES = [
    # Образцы отчётов программы Декоза (вымышленные лица, расчёт — программой автора метода):
    # https://www.worldnumerology.com/numerology-readings/sample-numerology-readings-members/personality-profile-numerology-reading.pdf
    ("Vincent Michael Tarriano", (1988, 1, 8), "Vince Tarriano",
     dict(exp="72/9", soul="19/10/1", pers="17/8", lp="17/8", mat=8, rt=5, bal=1, hp=[5, 9], kl=[7], ss=8,
          ch=[7, 0, 7, 7], pin=[9, 7, 7, 9], ages=[0, 28, 37, 46], per=[1, 8, 8],
          br=(0, 1, 7), minor=("14/5", "13/4", "10/1"))),
    # https://www.worldnumerology.com/numerology-app/sample-readings-new/personality-profile-sample-wn-app.pdf
    ("Jonathan Livingston Seagull", (1991, 7, 25), "Jonathan Seagull",
     dict(exp="22", soul="23/5", pers="17/8", lp="16/7", mat=2, rt=9, bal=5, hp=[1], kl=[], ss=9,
          ch=[0, 5, 5, 5], pin=[5, 9, 5, 9], ages=[0, 29, 38, 47], per=[7, 7, 2],
          br=(0, 3, 3), minor=("16/7", "17/8", "8"))),
    # https://www.worldnumerology.com/pdf-readings-wn-collection/ultimate-numerology-reading.pdf
    ("Kathleen Karen Johnson", (1990, 6, 3), "Kathy Johnson",
     dict(exp="31/4", soul="20/2", pers="11", lp="10/1", mat=5, rt=7, bal=5, hp=[5], kl=[4, 7], ss=7,
          ch=[3, 2, 1, 5], pin=[9, 4, 4, 7], ages=[0, 35, 44, 53], per=[6, 3, 1],
          br=(2, 3, 0), minor=("7", "11", "5"))),
    # https://www.worldnumerology.com/pdf-sample-reports/numerology-personality-profile-forecast-report.pdf
    ("Markus Angel Dunvale", (1977, 3, 3), None,
     dict(exp="12/3", soul="19/10/1", pers="20/2", lp="12/3", mat=6, rt=5, bal=9, hp=[1, 3, 5], kl=[6, 8], ss=7,
          ch=[0, 3, 3, 3], pin=[6, 9, 6, 9], ages=[0, 33, 42, 51], per=[3, 3, 6], br=(0, 0, 1), minor=None)),
    # https://www.worldnumerology.com/member-report-samples/ultimate-numerology-report.pdf
    ("Anthony Joseph Mercier", (1989, 5, 18), "Anthony Mercier",
     dict(exp="16/7", soul="17/8", pers="17/8", lp="23/5", mat=3, rt=7, bal=6, hp=[5], kl=[], ss=9,
          ch=[4, 0, 4, 4], pin=[5, 9, 5, 5], ages=[0, 31, 40, 49], per=[5, 9, 9],
          br=(4, 2, 0), minor=("15/6", "6", None))),
]


@pytest.mark.parametrize("name,ymd,short,exp", DECOZ_SAMPLES, ids=[s[0] for s in DECOZ_SAMPLES])
def test_decoz_software_samples(name, ymd, short, exp):
    r = calc(name, *ymd, current_name=short) if short else calc(name, *ymd)
    dn, nn = r["date_numbers"], r["name_numbers"]
    assert nn["expression"]["notation"] == exp["exp"]
    assert nn["soul_urge"]["notation"] == exp["soul"]
    assert nn["personality"]["notation"] == exp["pers"]
    assert dn["life_path"]["notation"] == exp["lp"]
    assert nn["maturity"]["value"] == exp["mat"]
    assert nn["rational_thought"]["value"] == exp["rt"]
    assert nn["balance"]["value"] == exp["bal"]
    assert nn["hidden_passion"]["values"] == exp["hp"]
    assert nn["karmic_lessons"] == exp["kl"]
    assert nn["subconscious_self"] == exp["ss"]
    assert [c["value"] for c in dn["challenges"]] == exp["ch"]
    assert [p["value"] for p in dn["pinnacles"]] == exp["pin"]
    assert [p["age_from"] for p in dn["pinnacles"]] == exp["ages"]
    assert [p["value"] for p in dn["period_cycles"]] == exp["per"]
    br = r["bridges"]
    assert (br["life_path_birthday"], br["life_path_expression"], br["soul_personality"]) == exp["br"]
    if exp["minor"]:
        mn = nn["minor"]
        for key, want in zip(("expression", "soul_urge", "personality"), exp["minor"]):
            if want is not None:
                assert mn[key]["notation"] == want


def test_decoz_planes_of_expression():
    # Anthony Joseph Mercier: Physical 19/10/1, Mental 35/8, Emotional 42/6, Intuitive 10/1
    # https://www.worldnumerology.com/member-report-samples/ultimate-numerology-report.pdf
    planes = analyze_name("Anthony Joseph Mercier")["planes_of_expression"]
    assert {k: v["notation"] for k, v in planes.items()} == {
        "physical": "19/10/1", "mental": "35/8", "emotional": "42/6", "intuitive": "10/1"}


def test_mccartney_decoz_2003():
    # Программа Декоза 2003 г.: James Paul McCartney, 18.06.1942
    # https://www.worldnumerology.com/numerology-software/software-sample-readings/profile-reading.pdf
    r = calc("James Paul McCartney", 1942, 6, 18, current_name="Paul McCartney", part_masters="11,22")
    dn, nn = r["date_numbers"], r["name_numbers"]
    assert dn["life_path"]["chain"] == [22] and dn["life_path"]["single"] == 4     # 22/4
    assert nn["expression"]["value"] == 11                                           # 11/2
    assert nn["soul_urge"]["notation"] == "16/7"
    assert nn["personality"]["notation"] == "13/4"      # 33 в части имени сведено (версия 2003 г.)
    assert nn["maturity"]["value"] == 6                 # 22 + 11 = 33 → 6
    assert nn["rational_thought"]["notation"] == "30/3"
    assert nn["balance"]["value"] == 3
    assert nn["karmic_lessons"] == [6, 8] and nn["hidden_passion"]["values"] == [1]
    assert [c["value"] for c in dn["challenges"]] == [3, 2, 1, 1]
    assert [p["value"] for p in dn["pinnacles"]] == [6, 7, 4, 4]
    assert [p["value"] for p in dn["period_cycles"]] == [6, 9, 7]
    assert nn["minor"]["expression"]["value"] == 8 and nn["minor"]["soul_urge"]["notation"] == "10/1"
    assert {k: v["value"] for k, v in nn["planes_of_expression"].items()} == {
        "physical": 9, "mental": 1, "emotional": 3, "intuitive": 7}
    # с умолчаниями (33 — мастер и в частях, как в программе 2020-х) итог тот же, меняется запись
    r2 = calc("James Paul McCartney", 1942, 6, 18)
    assert r2["name_numbers"]["personality"]["notation"] == "40/4"


def test_y_rule_decoz():
    # https://www.worldnumerology.com/numerology-articles/numerology-Y-vowel-consonant.html
    def y_flags(word):
        nn = analyze_name(word)
        return [l[2] for l in nn["parts"][0]["letters"] if l[0] == "Y"]
    assert y_flags("Yvonne") == ["V"]       # первая, перед согласной
    assert y_flags("Yolanda") == ["C"]      # первая, перед гласной
    assert y_flags("Barry") == ["V"]        # последняя после согласной
    assert y_flags("Mickey") == ["C"]       # последняя после гласной
    assert y_flags("Kyle") == ["V"]         # между согласными
    assert y_flags("Sydney") == ["V", "C"]
    assert y_flags("Kay") == ["C"]


# ---------------------------------------------------------------------------
# Числа имени: внешние векторы (кириллица)
# ---------------------------------------------------------------------------

def test_pugacheva_galactica():
    # https://galactica.ru/numero/lessons/4 : Экспрессия 1 + 1 + 7 = 9; Душа 2 + 7 + 3 = 12 → 3
    nn = analyze_name("Алла Борисовна Пугачёва")
    assert [p["sum"] for p in nn["parts"]] == [10, 37, 34]
    assert nn["expression"]["chain"] == [9]
    assert [p["vowel_sum"] for p in nn["parts"]] == [2, 16, 12]
    assert nn["soul_urge"]["chain"] == [12, 3]
    assert nn["given_name"] == "АЛЛА"
    # если в документе «Пугачева» (Е=6): фамилия 33, Экспрессия меняется на 8
    assert analyze_name("Алла Борисовна Пугачёва", yo_as_e=True)["expression"]["value"] == 8


def test_tikhomirov_karmic_debt_galactica():
    # https://galactica.ru/numero/lessons/8 : Экспрессия 9 + 4 = 13 → 4 (долг 13); Душа 8 + 7 = 15 → 6
    nn = analyze_name("Александр Тихомиров")
    assert nn["expression"]["chain"] == [13, 4] and nn["expression"]["karmic_debt"] == 13
    assert nn["soul_urge"]["chain"] == [15, 6] and nn["soul_urge"]["karmic_debt"] is None
    assert nn["given_name"] == "АЛЕКСАНДР"


def test_kolesnikov_variants_galactica():
    # https://galactica.ru/numero/lessons/4 : полное имя 8/7; «Александр Колесников» 5/11;
    # «Alexander Kolesnikov» 1/11; «Шурик» 6/4; «Alex» 6/6. Ь в «Геннадьевич» учитывается (=3).
    def es(name, **o):
        nn = analyze_name(name, **o)
        return nn["expression"]["value"], nn["soul_urge"]["value"]
    assert es("Александр Геннадьевич Колесников") == (8, 7)
    assert es("Александр Колесников") == (5, 11)
    assert es("Alexander Kolesnikov") == (1, 11)
    assert es("Шурик") == (6, 4)
    assert es("Alex") == (6, 6)
    # без Ь (вариант ru_signs='ignore') полное имя дало бы 5, а не 8 — источник подтверждает учёт Ь
    assert es("Александр Геннадьевич Колесников", ru_signs="ignore")[0] == 5


def test_putin_galactica():
    # https://galactica.ru/numero/lessons/15 : ЖП 7, ДР 7, Экспрессия 6, Душа 9, Личность 6
    r = calc("Путин Владимир Владимирович", 1952, 10, 7)
    c = core(r)
    assert (c["lp"], c["birthday"], c["exp"], c["soul"], c["pers"]) == (7, 7, 6, 9, 6)
    assert r["date_numbers"]["life_path"]["karmic_debt"] == 16


def test_pushkin_soul_numeroscop():
    # https://numeroscop.ru/numerologija_imeni/chislo_dushi/ : гласные 3+1+1+6+1+6+6+6+1 = 31 → 4
    nn = analyze_name("Пушкин Александр Сергеевич", name_method="all_letters")
    assert nn["soul_urge"]["chain"] == [31, 4]
    # по частям (Декоз/galactica): 4 + 8 + 1 = 13 → 4 — итог тот же, но виден долг 13
    assert analyze_name("Пушкин Александр Сергеевич")["soul_urge"]["chain"] == [13, 4]


def test_balance_letter_count_galactica():
    # https://galactica.ru/numero/lessons/23 : «Андрей Вадимович Макаревич» 6 + 9 + 9 = 24 → 6
    nn = analyze_name("Андрей Вадимович Макаревич")
    assert nn["balance_letter_count"]["counts"] == [6, 9, 9]
    assert nn["balance_letter_count"]["chain"] == [24, 6]
    assert analyze_name("Андрей Макаревич")["balance_letter_count"]["value"] == 6
    assert analyze_name("Макар")["balance_letter_count"]["value"] == 5


# ---------------------------------------------------------------------------
# Халдейская система: внешние векторы (Кейро)
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("name,words,total", [
    # Cheiro's Book of Numbers (1926), гл. XII–XIV: https://archive.org/details/numerology-cheiro
    ("John Smith", [(18, 9), (17, 8)], [17, 8]),
    ("Lloyd George", [(18, 9), (25, 7)], [16, 7]),
    ("Baldwin", [(22, 4)], [4]),
    ("David Lloyd George", [(16, 7), (18, 9), (25, 7)], [23, 5]),
])
def test_chaldean_cheiro(name, words, total):
    cn = analyze_name(name, system="chaldean")["chaldean_name_number"]
    assert [(w["compound"], w["single"]) for w in cn["words"]] == words
    assert cn["chain"] == total


def test_chaldean_cyrillic_is_transliterated():
    r = calc("Иванова Анна Сергеевна", 1990, 5, 15, system="chaldean")
    nn = r["name_numbers"]
    assert nn["name_used"] == "IVANOVA ANNA SERGEEVNA"
    assert any("ICAO" in w for w in r["warnings"])
    assert r["date_numbers"]["chaldean_birth_number"]["value"] == 6


# ---------------------------------------------------------------------------
# Эталонные персоны T1–T4 (ручной расчёт — knowledge-base/11-numerology.md, раздел 7)
# ---------------------------------------------------------------------------

def test_T1_ivanova():
    r = calc("Иванова Анна Сергеевна", 1990, 5, 15)
    c = core(r)
    assert (c["lp"], c["lp_compound"], c["birthday"]) == (3, 12, 6)
    assert {m: v["value"] for m, v in r["date_numbers"]["life_path_by_method"].items()} == {
        "reduce_components": 3, "all_digits": 3, "add_whole_numbers": 3}
    assert c["pinnacles"] == [11, 7, 9, 6] and c["challenges"] == [1, 5, 4, 4]
    assert [p["age_from"] for p in r["date_numbers"]["pinnacles"]] == [0, 33, 42, 51]
    # Иванова 22 (мастер) + Анна 14/5 + Сергеевна 42/6 = 33 — мастер-33
    assert [p["sum"] for p in r["name_numbers"]["parts"]] == [22, 14, 42]
    assert (c["exp"], c["soul"], c["pers"]) == (33, 4, 11)
    assert c["maturity"] == 9
    nn = r["name_numbers"]
    assert nn["given_name"] == "АННА" and nn["karmic_lessons"] == [2, 5, 8]
    assert nn["hidden_passion"]["values"] == [1, 6]
    # школа galactica (мастер-числа только 11 и 22): 33 → 6
    r2 = calc("Иванова Анна Сергеевна", 1990, 5, 15, masters="11,22", part_masters="11,22")
    assert r2["name_numbers"]["expression"]["value"] == 6
    # «все буквы сразу»: 78 → 15 → 6
    r3 = calc("Иванова Анна Сергеевна", 1990, 5, 15, name_method="all_letters")
    assert r3["name_numbers"]["expression"]["chain"] == [78, 15, 6]
    pc = r["personal_cycles"]                      # 14.10.2026: 5 + 6 + 1 = 12 → 3; 3+10 → 4; 4+14 → 9
    assert (pc["personal_year"]["value"], pc["personal_month"]["value"], pc["personal_day"]["value"]) == (3, 4, 9)


def test_T2_petrov():
    r = calc("Петров Дмитрий Олегович", 1984, 2, 4)
    c = core(r)
    dn = r["date_numbers"]
    assert dn["life_path"]["components"]["year"] == [1984, 22]
    assert dn["life_path"]["chain"] == [28, 10, 1]
    assert dn["life_path_by_method"]["add_whole_numbers"]["chain"] == [1990, 19, 10, 1]
    assert dn["life_path_by_method"]["add_whole_numbers"]["karmic_debt"] == 19
    assert c["pinnacles"] == [6, 8, 5, 6] and c["challenges"] == [2, 0, 2, 2]
    assert (c["exp"], c["soul"], c["pers"], c["maturity"]) == (9, 9, 9, 1)
    assert r["name_numbers"]["parts"][0]["consonant_sum"] == 22     # П8 Т2 Р9 В3
    assert r["name_numbers"]["given_name"] == "ДМИТРИЙ"
    # Й — согласная: в «Дмитрий» гласные только И, И
    assert r["name_numbers"]["parts"][1]["vowel_sum"] == 2


def test_T3_smirnova_feb29():
    r = calc("Смирнова Мария Александровна", 2004, 2, 29)
    c = core(r)
    dn = r["date_numbers"]
    assert dn["life_path"]["components"]["day"] == [29, 11]
    assert dn["life_path"]["chain"] == [19, 10, 1] and dn["life_path"]["karmic_debt"] == 19
    assert dn["birthday"]["chain"] == [29, 11]
    # если мастер-11 дня свести (только итоговые мастер-числа), долг 19 исчезает: 2 + 2 + 6 = 10 → 1
    r2 = calc("Смирнова Мария Александровна", 2004, 2, 29, part_masters="none")
    assert r2["date_numbers"]["life_path"]["chain"] == [10, 1]
    assert c["pinnacles"] == [4, 8, 3, 8] and c["challenges"] == [0, 4, 4, 4]
    assert [p["sum"] for p in r["name_numbers"]["parts"]] == [33, 22, 53]
    assert (c["exp"], c["exp_compound"], c["soul"], c["pers"]) == (9, 63, 6, 3)
    # граница «birthday»: 28.02.2025 — ещё год 2024
    pc = calc("Смирнова Мария Александровна", 2004, 2, 29, on_date="2025-02-28",
              personal_year_boundary="birthday")
    assert pc["personal_cycles"]["cycle_year"] == 2024
    assert any("29 февраля" in w for w in pc["warnings"])


def test_T4_einstein_latin_and_cyrillic():
    name = "Эйнштейн Альберт / Albert Einstein"
    r = calc(name, 1879, 3, 14, alphabet="latin")
    c = core(r)
    dn, nn = r["date_numbers"], r["name_numbers"]
    # Методы ЧЖП расходятся: по компонентам 3 + 5 + 7 = 15 → 6; все цифры 1+4+0+3+1+8+7+9 = 33
    assert dn["life_path"]["chain"] == [15, 6]
    assert dn["life_path_by_method"]["all_digits"]["chain"] == [33]
    assert dn["life_path_by_method"]["add_whole_numbers"]["chain"] == [1896, 24, 6]
    assert any("разные результаты" in w for w in r["warnings"])
    assert dn["birthday"]["karmic_debt"] == 14
    assert c["pinnacles"] == [8, 3, 11, 1] and c["challenges"] == [2, 2, 0, 4]
    assert nn["name_used"] == "ALBERT EINSTEIN"
    assert [p["sum"] for p in nn["parts"]] == [22, 41]
    assert (c["exp"], c["soul"], c["pers"], c["maturity"]) == (9, 7, 11, 6)
    assert nn["karmic_lessons"] == [4, 6, 7, 8] and nn["hidden_passion"]["values"] == [5]
    assert nn["rational_thought"]["chain"] == [36, 9] and nn["balance"]["value"] == 6
    # кириллица (первый вариант имени): Эйнштейн 36/9 + Альберт 27/9 = 18/9
    rc = calc(name, 1879, 3, 14)
    ncy = rc["name_numbers"]
    assert ncy["name_used"] == "ЭЙНШТЕЙН АЛЬБЕРТ" and ncy["given_name"] == "АЛЬБЕРТ"
    assert (ncy["expression"]["value"], ncy["soul_urge"]["value"], ncy["personality"]["value"]) == (9, 8, 1)
    # халдейская: Albert 17/8 + Einstein 29/2 → 10/1
    ch = calc(name, 1879, 3, 14, alphabet="latin", system="chaldean")["name_numbers"]["chaldean_name_number"]
    assert ch["notation"] == "10/1"


# ---------------------------------------------------------------------------
# Инварианты и контракт
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("name,ymd", [
    ("Иванова Анна Сергеевна", (1990, 5, 15)), ("Петров Дмитрий Олегович", (1984, 2, 4)),
    ("Смирнова Мария Александровна", (2004, 2, 29)), ("Albert Einstein", (1879, 3, 14)),
    ("Kathleen Karen Johnson", (1990, 6, 3)),
])
def test_invariants(name, ymd):
    r = calc(name, *ymd)
    nn, dn = r["name_numbers"], r["date_numbers"]
    # Экспрессия ≡ Душа + Личность (mod 9) — для способа «по частям» и «все буквы»
    for meth in ("parts", "all_letters"):
        n2 = analyze_name(name, name_method=meth)
        e, s, p = (n2[k]["single"] for k in ("expression", "soul_urge", "personality"))
        assert (s + p - e) % 9 == 0
    # все три способа ЧЖП совпадают по модулю 9
    vals = {v["single"] for v in dn["life_path_by_method"].values()}
    assert len(vals) == 1
    # сумма гласных + согласных = сумма букв в каждой части
    for p in nn["parts"]:
        assert p["vowel_sum"] + p["consonant_sum"] == p["sum"]
    # испытания 0–8, вершины 1–9 или мастер
    assert all(0 <= c["value"] <= 8 for c in dn["challenges"])
    assert all(1 <= p["value"] <= 9 or p["value"] in (11, 22, 33) for p in dn["pinnacles"])
    assert sum(nn["inclusion_table"].values()) == sum(p["letter_count"] for p in nn["parts"])
    json.dumps(r, ensure_ascii=False)
    for key in ("method", "variant", "inputs_used", "warnings", "steps"):
        assert key in r


def test_without_name_and_validation():
    r = calculate(BirthInput(1990, 5, 15), on_date=ON)
    assert r["name_numbers"] is None and any("Имя не задано" in w for w in r["warnings"])
    with pytest.raises(ValueError):
        calculate(BirthInput(1990, 5, 15), life_path_method="nope")
    with pytest.raises(ValueError):
        analyze_name("Ivanova", alphabet="ru")


def test_cli_string_options():
    # CLI передаёт опции строками: masters=11,22, on_date=YYYY-MM-DD
    r = calculate(BirthInput(1990, 5, 15, name="Иванова Анна Сергеевна"),
                  masters="11,22", part_masters="11,22", on_date="2026-01-01")
    assert r["name_numbers"]["expression"]["value"] == 6
    assert r["inputs_used"]["options"]["masters"] == [11, 22]
