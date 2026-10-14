"""Тесты Матрицы судьбы (knowledge-base/10-destiny-matrix.md).

Внешние векторы взяты из опубликованных схем и разборов; URL указан у каждого теста.
Запуск: .venv/bin/python -m pytest calculators/tests/test_destiny_matrix.py -q
"""
from __future__ import annotations

import json

import pytest

from calculators.common.time import BirthInput
from calculators.destiny_matrix import (
    ARCANA,
    age_point,
    calculate,
    compute_points,
    reduce_arcana,
)


def _calc(d: int, m: int, y: int, **opt):
    return calculate(BirthInput(y, m, d), **opt)


def _ring_values(res: dict, start_age: int, end_age: int) -> list[int]:
    """Значения точек кольца на отрезке [start_age; end_age) лет."""
    return [p["value"] for p in res["age_ring"] if start_age <= p["age"] < end_age]


# ---------------------------------------------------------------------------
# Свёртка
# ---------------------------------------------------------------------------

def test_reduce_digits_default():
    assert reduce_arcana(22) == 22          # 22 не сворачивается
    assert reduce_arcana(23) == 5
    assert reduce_arcana(31) == 4
    assert reduce_arcana(25) == 7           # 1987 → 25 → 7
    assert reduce_arcana(47) == 11          # пример rodis.org.ua: 47 → 11
    assert reduce_arcana(28) == 10
    assert reduce_arcana(99) == 18
    assert reduce_arcana(154) == 10         # максимум суммы 7 чакр (7 × 22)
    for n in range(1, 23):
        assert reduce_arcana(n) == n


def test_reduce_minus22():
    assert reduce_arcana(23, "minus22") == 1
    assert reduce_arcana(42, "minus22") == 20
    assert reduce_arcana(62, "minus22") == 18
    assert reduce_arcana(44, "minus22") == 22


def test_day_22_and_23_31():
    """День 22 остаётся 22; дни 23–31 сворачиваются сложением цифр."""
    assert _calc(22, 6, 1990)["points"]["A"] == 22
    expected = {23: 5, 24: 6, 25: 7, 26: 8, 27: 9, 28: 10, 29: 11, 30: 3, 31: 4}
    for day, a in expected.items():
        assert _calc(day, 1, 1990)["points"]["A"] == a


# ---------------------------------------------------------------------------
# Внешние векторы
# ---------------------------------------------------------------------------

def test_dolina_10_09_1955_full_chart():
    """Лариса Долина, 10.09.1955 — полная схема на matrica-sudby.ru:
    https://matrica-sudby.ru/razbor-matric/razbor-matriczy-sudby-larisy-dolinoj-po-date-rozhdeniya.html
    (картинка https://matrica-sudby.ru/storage/wp-uploads/2025/12/razbor-matriczy-sudby-larisy-dolinoj-po-date-rozhdeniya.png)
    """
    r = _calc(10, 9, 1955)
    p = r["points"]
    expected = {
        "A": 10, "B": 9, "C": 20, "D": 12, "E": 6,
        "F": 19, "G": 11, "I": 5, "H": 22, "R": 12,
        "A1": 8, "A2": 16, "A3": 22, "B1": 6, "B2": 15, "B3": 21,
        "C1": 10, "C2": 8, "D1": 3, "D2": 18,
        "F1": 5, "F2": 4, "G1": 16, "G2": 5, "I1": 22, "I2": 17, "H1": 11, "H2": 7,
        "TAL": 4, "X": 8, "Y": 13,
    }
    assert {k: p[k] for k in expected} == expected
    # Внешнее кольцо, прочитано со схемы: 0–30 лет и 50–80 лет
    assert _ring_values(r, 0, 30) == [10, 4, 21, 5, 11, 14, 3, 22,
                                      19, 3, 11, 21, 10, 11, 19, 10,
                                      9, 20, 11, 4, 20, 6, 4, 15]
    assert _ring_values(r, 50, 80) == [5, 9, 22, 12, 17, 10, 11, 5,
                                       12, 4, 19, 8, 7, 18, 11, 6,
                                       22, 4, 9, 14, 5, 20, 15, 7]
    # В статье: в 70 лет (2025 год) у неё «22 аркан на периоде»
    r2 = _calc(10, 9, 1955, on_date="2025-12-01")
    assert r2["current_period"]["label"] == "70 лет"
    assert r2["current_period"]["value"] == 22


def test_male_rod_chart_A2_B10_C2_2000s():
    """Схема со статьи «Родовой квадрат» matrica-sudby.ru (A=2, B=10, C=2; дата на картинке не указана,
    все точки зависят только от A, B, C — берём 02.10.2000, у которой те же A, B, C):
    https://matrica-sudby.ru/matrix/rodovoj-kvadrat-matricy-sudby.html
    (картинка https://matrica-sudby.ru/wp-content/uploads/2025/07/muzhskoj-rod.png)
    """
    r = _calc(2, 10, 2000)
    p = r["points"]
    expected = {
        "A": 2, "B": 10, "C": 2, "D": 14, "E": 10,
        "F": 12, "G": 12, "I": 16, "H": 16, "R": 11,
        "A1": 14, "A2": 12, "A3": 22, "B1": 3, "B2": 20, "B3": 3,
        "C1": 14, "C2": 12, "D1": 20, "D2": 6,
        "F1": 17, "F2": 5, "G1": 17, "G2": 5, "I1": 7, "I2": 9, "H1": 7, "H2": 9,
        "TAL": 5, "Y": 7,
    }
    assert {k: p[k] for k in expected} == expected
    # Всё кольцо 0–80 лет, прочитано со схемы
    assert [x["value"] for x in r["age_ring"]] == [
        2, 18, 16, 3, 14, 22, 8, 20,      # 0–10
        12, 19, 7, 11, 22, 9, 5, 15,      # 10–20
        10, 15, 5, 9, 22, 11, 7, 19,      # 20–30
        12, 20, 8, 22, 14, 3, 16, 18,     # 30–40
        2, 22, 20, 11, 18, 7, 7, 5,       # 40–50
        16, 8, 19, 22, 3, 20, 17, 4,      # 50–60
        14, 4, 17, 20, 3, 22, 19, 8,      # 60–70
        16, 5, 7, 7, 18, 11, 20, 22,      # 70–80
    ]
    assert [x["label"] for x in r["age_ring"][:9]] == [
        "0 лет", "1–2,5", "2,5–3,5", "3,5–4", "5 лет", "6–7,5", "7,5–8,5", "8,5–9", "10 лет"]


def test_sila_roda_chart_A11_B11_C12():
    """Схема «Аркан силы рода» matrica-sudby.ru (A=11, B=11, C=12; эквивалентная дата 11.11.2019):
    https://matrica-sudby.ru/matrix/rodovoj-kvadrat-matricy-sudby.html
    (картинка https://matrica-sudby.ru/wp-content/uploads/2025/07/sila-roda.png)
    «Сила рода … получается путем сложения … углов родового квадрата»: 22+5+18+19 = 64 → 10.
    """
    r = _calc(11, 11, 2019)
    p = r["points"]
    expected = {"A": 11, "B": 11, "C": 12, "E": 5, "F": 22, "G": 5, "R": 10,
                "F1": 9, "F2": 5, "G1": 20, "G2": 15, "A1": 9, "A2": 16, "A3": 21,
                "B1": 9, "B2": 16, "B3": 21, "TAL": 5, "C2": 17, "C1": 11}
    assert {k: p[k] for k in expected} == expected
    assert _ring_values(r, 0, 30) == [11, 10, 17, 5, 6, 16, 10, 5,
                                      22, 5, 10, 16, 6, 5, 17, 10,
                                      11, 20, 9, 7, 16, 10, 21, 8]


def test_upper_arcana_chart_A13_B1_C6():
    """Схема «верхние арканы» со статьи «Родовой квадрат» matrica-sudby.ru (A=13, B=1, C=6; дата на картинке
    не указана — берём эквивалентную 13.01.2004, у неё те же A, B, C):
    https://matrica-sudby.ru/matrix/rodovoj-kvadrat-matricy-sudby.html
    (картинка https://matrica-sudby.ru/wp-content/uploads/2025/07/verhnie-arkany-1.png)
    Видна верхняя половина: Rod = 8 = 14+7+8+6 = 35 → 8 (сумма ВСЕХ четырёх углов; F+G = 21 дало бы 21).
    Значение «3,5–4» частично закрыто стрелкой, видна верхняя часть цифры 4.
    """
    r = _calc(13, 1, 2004)
    p = r["points"]
    expected = {"A": 13, "B": 1, "C": 6, "E": 4, "F": 14, "G": 7, "R": 8,
                "F1": 9, "F2": 22, "G1": 22, "G2": 15, "A1": 3, "A2": 17, "A3": 21,
                "B1": 6, "B2": 5, "B3": 9, "TAL": 22, "C2": 10, "C1": 16}
    assert {k: p[k] for k in expected} == expected
    assert _ring_values(r, 0, 40) == [13, 8, 22, 4, 9, 14, 5, 19,
                                      14, 7, 11, 8, 15, 4, 16, 17,
                                      1, 10, 9, 17, 8, 5, 15, 22,
                                      7, 9, 20, 6, 13, 5, 19, 7]


def test_calkin_26_08_1980_health_map_matrica_sudby_variant():
    """Маколей Калкин, 26.08.1980 (день 26 → 8) — схема и карта здоровья matrica-sudby.ru:
    https://matrica-sudby.ru/razbor-matric/razbor-detskoj-matricy-sudby-makoleya-kalkina.html
    (картинка https://matrica-sudby.ru/wp-content/uploads/2025/06/makolej-kalkin-matricza-sudby.png)
    Сайт сейчас берёт для Свадхистаны точки C1/D1 (энергия 19 = D1), поэтому опция svadhisthana="matrica_sudby".
    """
    r = _calc(26, 8, 1980, svadhisthana="matrica_sudby")
    p = r["points"]
    expected = {"A": 8, "B": 8, "C": 18, "D": 7, "E": 5, "F": 16, "G": 8, "I": 7, "H": 15,
                "A1": 21, "A2": 13, "B2": 13, "C2": 5, "D1": 19, "D2": 12, "X": 17, "TAL": 8}
    assert {k: p[k] for k in expected} == expected
    rows = [(x["chakra"], x["physics"], x["energy"], x["emotions"]) for x in r["health_map"]["rows"]]
    assert rows == [
        ("Сахасрара", 8, 8, 16),
        ("Аджна", 21, 21, 6),
        ("Вишудха", 13, 13, 8),
        ("Анахата", 18, 18, 9),
        ("Манипура", 5, 5, 10),
        ("Свадхистана", 5, 19, 6),
        ("Муладхара", 18, 7, 7),
    ]
    assert r["health_map"]["total"] == {"physics": 16, "energy": 10, "emotions": 8}
    # Классический вариант (по умолчанию) отличается только Свадхистаной
    rc = _calc(26, 8, 1980)
    assert [x["energy"] for x in rc["health_map"]["rows"]][5] == 12


def test_15_09_1944_health_and_purposes_classic():
    """Женщина 15.09.1944 — разбор карты здоровья и предназначений:
    http://iggdrasil-runes.name/matritsa-sudby-o-zdorove-primer-rascheta/
    Свадхистана: «18 энергия и на физическом уровне (3)…», эмоции 21 → классика (C+E, D+E).
    Небо 15, Земля 6, (личное 21), М 12, Ж 3, (социальное 15), Духовное 9, Планетарное 6.
    """
    r = _calc(15, 9, 1944)
    rows = {x["chakra"]: (x["physics"], x["energy"], x["emotions"]) for x in r["health_map"]["rows"]}
    assert rows == {
        "Сахасрара": (15, 9, 6),
        "Аджна": (6, 3, 9),
        "Вишудха": (9, 21, 3),
        "Анахата": (21, 6, 9),
        "Манипура": (12, 12, 6),
        "Свадхистана": (3, 18, 21),
        "Муладхара": (18, 6, 6),
    }
    assert r["purposes"] == {"sky": 15, "earth": 6, "personal": 21, "male": 12, "female": 3,
                             "social": 15, "spiritual": 9, "planetary": 6}


def test_15_10_1990_channels_classic():
    """15.10.1990 — пример thematrixofdestiny.com: Karmic Tail 15-5-8, Love Line 15-20-5, Money Line 8-13-5.
    https://www.thematrixofdestiny.com/destiny-matrix-chart
    """
    r = _calc(15, 10, 1990)
    assert r["personal_square"] == {"A": 15, "B": 10, "C": 19, "D": 8, "E": 7}
    assert r["zones"]["karmic_tail_code"] == "15-5-8"
    assert r["channels"]["classic"]["love_line"] == [15, 20, 5]
    assert r["channels"]["classic"]["money_line"] == [8, 13, 5]


def test_28_11_1987_year_sum_over_22():
    """28.11.1987 (день 28, сумма цифр года 25 > 22) — пример matrixdestiny.io:
    https://matrixdestiny.io/en/methodology  (на .../matrix-destiny-guide этой даты нет, там только 08.08.2020)
    A=10, B=11, C=7, D=10, E=11; углы рода 21, 18, 17, 20 (F, G, I, H по часовой).
    Формулы канала той же страницы: D+E, C+E, K = их сумма, сердце = (D+E)+K, деньги = (C+E)+K.
    """
    r = _calc(28, 11, 1987)
    p = r["points"]
    assert r["personal_square"] == {"A": 10, "B": 11, "C": 7, "D": 10, "E": 11}
    assert (p["F"], p["G"], p["I"], p["H"]) == (21, 18, 17, 20)
    assert (p["D2"], p["C2"], p["X"], p["X_love"], p["X_money"]) == (21, 18, 12, 6, 3)


def test_31_03_1967_matrica_sudby_howto():
    """31.03.1967 (день 31, год 23 → 5) — пошаговый пример matrica-sudby.ru:
    https://matrica-sudby.ru/matrix/chto-takoe-matrica-sudby-i-kak-rasschitat.html
    «3+1=4 … 1+9+6+7=23, 2+3=5 … 4+3+5=12 … 4+3+5+12=24; 2+4=6 … 4+3=7, 3+5=8 …
    4+6=10; 4+10=14 … 4, 14, 10, 6 … 16+3=19 … 11+18=29; 2+9=11».
    """
    r = _calc(31, 3, 1967)
    p = r["points"]
    assert r["personal_square"] == {"A": 4, "B": 3, "C": 5, "D": 12, "E": 6}
    assert (p["F"], p["G"]) == (7, 8)
    assert (p["A"], p["A1"], p["A2"], p["E"]) == (4, 14, 10, 6)
    assert (p["C1"], p["D1"], p["Y"]) == (16, 3, 19)
    assert (p["C2"], p["D2"], p["X"]) == (11, 18, 11)


def test_17_08_1992_karmic_tail():
    """17.08.1992 — destiny-matrix.cc: Future 10, Helper 11, Past 21, Present 4 (хвост 21-4-10).
    https://destiny-matrix.cc/en/blog/how-to-calculate-karmic-tail/
    """
    r = _calc(17, 8, 1992)
    assert r["points"]["E"] == 11
    assert r["zones"]["karmic_tail"] == [21, 4, 10]


def test_08_08_2020_post2000():
    """08.08.2020 — matrixdestiny.io: A=8, B=8, C=4, D=20, E=40→4.
    https://matrixdestiny.io/en/matrix-destiny-guide
    """
    r = _calc(8, 8, 2020)
    assert r["personal_square"] == {"A": 8, "B": 8, "C": 4, "D": 20, "E": 4}


def test_15_03_1990_rodis():
    """15.03.1990 — rodis.org.ua: A=15, B=3, C=19, D=37→10, E=47→11.
    https://www.rodis.org.ua/ru/rozrakhuvaty-matrytsiu-doli-povnyi-pokrokovyi-haid/
    """
    r = _calc(15, 3, 1990)
    assert r["personal_square"] == {"A": 15, "B": 3, "C": 19, "D": 10, "E": 11}


def test_14_07_1992_minus22_variant():
    """Вариант «вычитать 22» — ask-sibylla.com, 14.07.1992: A=14, B=7, C=21, D=42→20, E=62→40→18,
    F=21, G=28→6, H(C+D)=41→19, K(D+A)=34→12 (у них H/K — наши I/H).
    https://ask-sibylla.com/ru/statti/matrytsia-doli-samostiino-pokrokovo
    """
    r = _calc(14, 7, 1992, reduction="minus22")
    p = r["points"]
    assert r["personal_square"] == {"A": 14, "B": 7, "C": 21, "D": 20, "E": 18}
    assert (p["F"], p["G"], p["I"], p["H"]) == (21, 6, 19, 12)
    assert r["warnings"]
    # по умолчанию (сложение цифр) D и E другие
    assert _calc(14, 7, 1992)["personal_square"] == {"A": 14, "B": 7, "C": 21, "D": 6, "E": 12}


# ---------------------------------------------------------------------------
# Эталонные персоны T1–T4 (сверены вручную, см. раздел «Примеры» документа)
# ---------------------------------------------------------------------------

def test_T1_15_05_1990():
    r = _calc(15, 5, 1990)
    p = r["points"]
    assert r["personal_square"] == {"A": 15, "B": 5, "C": 19, "D": 12, "E": 6}
    assert (p["F"], p["G"], p["I"], p["H"], p["R"]) == (20, 6, 4, 9, 12)
    assert r["zones"]["karmic_tail_code"] == "18-3-12"
    assert r["purposes"] == {"sky": 17, "earth": 7, "personal": 6, "male": 6, "female": 15,
                             "social": 21, "spiritual": 9, "planetary": 3}
    assert r["health_map"]["total"] == {"physics": 14, "energy": 13, "emotions": 9}


def test_T2_04_02_1984_year_sum_exactly_22():
    r = _calc(4, 2, 1984)
    p = r["points"]
    assert p["C"] == 22                      # 1+9+8+4 = 22 → не сворачивается
    assert r["personal_square"] == {"A": 4, "B": 2, "C": 22, "D": 10, "E": 11}
    assert r["zones"]["karmic_tail_code"] == "21-4-10"
    assert r["channels"]["classic"]["money_line"] == [6, 15, 9]
    assert r["channels"]["classic"]["love_line"] == [21, 3, 9]


def test_T3_29_02_2004():
    r = _calc(29, 2, 2004)
    p = r["points"]
    assert r["personal_square"] == {"A": 11, "B": 2, "C": 6, "D": 19, "E": 11}
    # Хвост 3-22-19 — известная программа (matrica-sudby.ru/programmy/karmicheskij-hvost-3-22-19-programma.html)
    assert r["zones"]["karmic_tail_code"] == "3-22-19"
    assert (p["F"], p["G"], p["I"], p["H"], p["R"]) == (13, 8, 7, 3, 4)


def test_T4_14_03_1879():
    r = _calc(14, 3, 1879)
    p = r["points"]
    assert p["C"] == 7                       # 1+8+7+9 = 25 → 7
    assert r["personal_square"] == {"A": 14, "B": 3, "C": 7, "D": 6, "E": 3}
    assert r["zones"]["karmic_tail_code"] == "9-15-6"
    assert r["purposes"]["personal"] == 3


# ---------------------------------------------------------------------------
# Инварианты
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("d,m,y", [(1, 1, 1900), (22, 12, 1999), (31, 12, 2099), (29, 2, 2004),
                                   (15, 5, 1990), (4, 2, 1984), (14, 3, 1879), (9, 9, 1999)])
def test_invariants(d, m, y):
    r = _calc(d, m, y)
    p = r["points"]
    assert all(1 <= v <= 22 for v in p.values())
    assert p["D"] == reduce_arcana(p["A"] + p["B"] + p["C"])
    assert p["E"] == reduce_arcana(p["A"] + p["B"] + p["C"] + p["D"])
    assert p["R"] == reduce_arcana(p["F"] + p["G"] + p["H"] + p["I"])
    assert len(r["age_ring"]) == 64
    # главные точки кольца
    ring = {x["age"]: x["value"] for x in r["age_ring"]}
    assert [ring[a] for a in (0, 10, 20, 30, 40, 50, 60, 70)] == [
        p["A"], p["F"], p["B"], p["G"], p["C"], p["I"], p["D"], p["H"]]
    # каждая точка кольца — сумма соседей уровнем выше
    vals = [x["value"] for x in r["age_ring"]] + [p["A"]]
    for s in range(0, 64, 8):
        p0, p10 = vals[s], vals[s + 8]
        mid = reduce_arcana(p0 + p10)
        assert vals[s + 4] == mid
        assert vals[s + 2] == reduce_arcana(p0 + mid)
        assert vals[s + 6] == reduce_arcana(mid + p10)
    # строки карты здоровья: эмоции = физика + энергия
    for row in r["health_map"]["rows"]:
        assert row["emotions"] == reduce_arcana(row["physics"] + row["energy"])
    json.dumps(r, ensure_ascii=False)       # результат сериализуем
    assert r["steps"] and r["method"] == "destiny_matrix"


def test_age_point_boundaries():
    r = _calc(2, 10, 2000)
    ring = r["age_ring"]
    assert age_point(ring, 0.5)["label"] == "0 лет"
    assert age_point(ring, 1.0)["label"] == "1–2,5"
    assert age_point(ring, 2.49)["label"] == "1–2,5"
    assert age_point(ring, 2.5)["label"] == "2,5–3,5"
    assert age_point(ring, 4.9)["label"] == "3,5–4"
    assert age_point(ring, 5.0)["label"] == "5 лет"
    assert age_point(ring, 9.99)["label"] == "8,5–9"
    assert age_point(ring, 44.0)["label"] == "43,5–44"
    assert age_point(ring, 79.9)["label"] == "78,5–79"
    assert age_point(ring, 80.0)["label"] == "0 лет"     # второй круг


def test_options_validation_and_variants():
    with pytest.raises(ValueError):
        _calc(1, 1, 2000, reduction="bad")
    with pytest.raises(ValueError):
        _calc(1, 1, 2000, svadhisthana="bad")
    with pytest.raises(ValueError):
        _calc(31, 2, 2000)
    # вариант внутренних точек рода от центра E
    p = _calc(10, 9, 1955, ancestral_inner="personal_center")["points"]
    assert p["F2"] == reduce_arcana(19 + 6) and p["F1"] == reduce_arcana(19 + p["F2"])
    # сумма эмоций по строкам vs итог физики+энергии могут различаться (28.11.1987)
    r1 = _calc(28, 11, 1987)
    r2 = _calc(28, 11, 1987, health_total="sum_of_rows")
    assert r1["health_map"]["total"]["emotions"] == 10
    assert r2["health_map"]["total"]["emotions"] == 1


def test_arcana_table_complete():
    assert sorted(ARCANA) == list(range(1, 23))
    assert ARCANA[8]["name"] == "Справедливость" and ARCANA[11]["name"] == "Сила"
    for v in ARCANA.values():
        assert v["plus"] and v["minus"]


def test_compute_points_direct():
    vals, formulas, steps = compute_points(15, 5, 1990)
    assert formulas["D"] == "A+B+C"
    assert any(s.startswith("C = год 1990") for s in steps)
