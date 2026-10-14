"""Тесты психоматрицы по А. Ф. Александрову (knowledge-base/09-alexandrov-square.md).

Внешние векторы взяты из книг самого автора (первоисточник):
  [K1]  «Цифровой анализ дат рождения и событий. Книга 1. Психоматрица и её свойства» (2011)
        https://thelib.ru/books/aleksandr_fedorovich_aleksandrov/cifrovoy_analiz_dat_rozhdeniya_i_sobytiy_kniga_1_psihomatrica_i_ee_svoystva-read.html
        (стр. -read-2 … -read-5 того же адреса)
  [DR]  «Дата рождения — ключ к пониманию человека» (раннее издание)
        https://litresp.ru/chitat/ru/%D0%90/aleksandrov-aleksandr-fedorovich/data-rozhdeniya--klyuch-k-ponimaniyu-cheloveka/4
  [TMC] «Тайны магических цифр», гл. 1–5
        https://litresp.ru/chitat/ru/%D0%90/aleksandrov-aleksandr-fedorovich/tajni-magicheskih-cifr/2  (…/3, /4, /5)
  [PK]  «Нумерология. Полный курс. Самоучитель цифрового анализа» (повтор примера 1 1 2000)
        https://flibusta.su/book/128075-numerologiya-polnyiy-kurs-samouchitel-tsifrovogo-analiza/read/
"""
from __future__ import annotations

import json
from datetime import date, timedelta

import pytest

from calculators.alexandrov import (
    calculate,
    compatibility,
    gregorian_to_julian,
    psychomatrix_from_groups,
    stability_years,
    time_period,
    working_numbers,
)
from calculators.common.time import BirthInput


def _counts(r: dict) -> dict[int, int]:
    return {int(k): v for k, v in r["counts"].items()}


def _lines(r: dict) -> dict[str, int]:
    return {k: v["count"] for k, v in r["lines"].items()}


def _grid_counts(s: str) -> dict[int, int]:
    """'1111 4 77 / 222 5 - / - - 999' → {1:4, 4:1, 7:2, ...} (строки 1-4-7 / 2-5-8 / 3-6-9)."""
    cells = [(1, 4, 7), (2, 5, 8), (3, 6, 9)]
    out = {d: 0 for d in range(1, 10)}
    for row, digits in zip(s.split("/"), cells):
        for tok, d in zip(row.split(), digits):
            out[d] = 0 if tok == "-" else len(tok)
    return out


# ---------------------------------------------------------------------------
# Эталонные персоны T1–T4 (ручной расчёт в документе 09, раздел 7)
# ---------------------------------------------------------------------------

T_CASES = [
    # id, (y, m, d), запись, числа, матрица, нули, линии (147,258,369,123,456,789,159,357), номер жизни,
    # период, сильные линии, БС, ДС
    ("T1", (1990, 5, 15), "15 5 1990", [30, 3, 28, 10], "111 - - / 2 55 8 / 33 - 99", 3,
     (3, 4, 4, 6, 2, 3, 7, 4), 11, 5, ["col_123", "diag_159"], 64, 126),
    ("T2", (1984, 2, 4), "4 2 1984", [28, 10, 20, 2], "11 44 - / 2222 - 88 / - - 9", 2,
     (4, 6, 1, 6, 2, 3, 3, 0), 11, 5, ["row_258", "col_123"], 0, 72),
    ("T3", (2004, 2, 29), "29 2 2004", [19, 10, 15, 6], "111 4 - / 222 5 - / - 6 99", 3,
     (4, 4, 3, 6, 3, 2, 6, 1), 11, 1,
     ["row_147", "row_258", "row_369", "col_123", "col_456", "col_789", "diag_159", "diag_357"], 12, 144),
    ("T4", (1879, 3, 14), "14 3 1879", [33, 6, 31, 4], "111 44 7 / - - 8 / 3333 6 9", 0,
     (6, 1, 6, 7, 3, 3, 4, 5), 13, 5, ["row_147", "row_369", "col_123", "diag_357"], 30, 168),
]
LINE_KEYS = ["row_147", "row_258", "row_369", "col_123", "col_456", "col_789", "diag_159", "diag_357"]


@pytest.mark.parametrize("case", T_CASES, ids=[c[0] for c in T_CASES])
def test_reference_subjects(case):
    _id, (y, m, d), record, nums, grid, zeros, lines, life, period, strong, bs, ds = case
    r = calculate(BirthInput(y, m, d))
    assert r["date_record"] == record
    assert r["working_numbers_list"] == nums
    assert _counts(r) == _grid_counts(grid)
    assert r["zeros"] == zeros
    assert _lines(r) == dict(zip(LINE_KEYS, lines))
    assert r["life_number"] == life
    assert r["time_intervals"]["period"] == period
    assert r["time_intervals"]["strong_lines"] == strong
    assert r["stability"]["bytovaya"] == bs
    assert r["stability"]["dukhovnaya"] == ds


def test_t2_day_with_leading_zero_differs_from_generic():
    """04.02.1984: у Александрова «4 2 1984» → третье = 28 − 2×4 = 20;
    генерический вариант с ведущим нулём даёт 28 − 2×0 = 28."""
    r = calculate(BirthInput(1984, 2, 4))
    assert r["third_number_raw"] == 20
    assert r["vs_generic"]["generic_numbers"] == [28, 10, 28, 10]
    assert r["vs_generic"]["same_numbers"] is False


def test_t1_t3_t4_same_numbers_as_generic():
    for y, m, d in [(1990, 5, 15), (2004, 2, 29), (1879, 3, 14)]:
        assert calculate(BirthInput(y, m, d))["vs_generic"]["same_numbers"] is True


def test_numbers_and_cells_equal_doc08_default():
    """Проверка 2-й волны: числа и ячейки 1–9 Александрова совпадают с вариантом документа 08
    по умолчанию (first_nonzero + модуль) для любых дат 1000–2999; расходятся только с вариантом
    «буквальный 0» (day_digit='literal')."""
    from calculators.pythagoras import calculate as pyth

    d = date(1000, 1, 1)
    while d <= date(2999, 12, 31):
        a = psychomatrix_from_groups([d.day, d.month, d.year])
        p = pyth(BirthInput(d.year, d.month, d.day), interpret=False)
        w = p["working_numbers"]
        assert a["working_numbers_list"] == [w["first"], w["second"], w["third"], w["fourth"]], d
        assert a["counts"] == p["counts"], d
        d += timedelta(days=37)
    for y, m, d_ in [(1984, 2, 4), (2000, 1, 7), (1973, 9, 6)]:
        vs = calculate(BirthInput(y, m, d_))["vs_generic"]
        assert vs["same_as_doc08_default"] is True
        assert vs["doc08_default_numbers"] == calculate(BirthInput(y, m, d_))["working_numbers_list"]
    assert calculate(BirthInput(2000, 1, 7))["vs_generic"]["generic_numbers"] == [10, 1, 10, 1]


def test_full_date_before_year_1000():
    # Ручной расчёт: 15 6 988 → 1+5+6+9+8+8 = 37; 10; 37 − 2 = 35; 8; 5-й период (800–999).
    r = calculate(BirthInput(988, 6, 15))
    assert r["date_record"] == "15 6 988"
    assert r["working_numbers_list"] == [37, 10, 35, 8]
    assert r["zeros"] == 1
    assert r["time_intervals"]["period"] == 5


def test_t3_post_2000_period_one_potential():
    """29.02.2004: 1-й период → все 8 линий сильные; потенциал ячеек = числу проходящих линий."""
    ti = calculate(BirthInput(2004, 2, 29))["time_intervals"]
    assert ti["threshold"] == 1
    assert ti["max_extra_total"] == 8
    assert ti["max_extra_per_cell"] == {"1": 3, "2": 2, "3": 3, "4": 2, "5": 4, "6": 2, "7": 3, "8": 2, "9": 3}


def test_t4_inputs_ignore_time_and_place():
    r1 = calculate(BirthInput(1879, 3, 14, 11, 30, tz="LMT", lat=48.4011, lon=9.9876))
    r2 = calculate(BirthInput(1879, 3, 14))
    assert r1["working_numbers_list"] == r2["working_numbers_list"]
    assert r1["inputs_used"]["time_used"] is False


# ---------------------------------------------------------------------------
# Внешние векторы из книг автора
# ---------------------------------------------------------------------------

def test_book1_main_example_15_4_1972():
    # [K1] гл. 1–2, 5, 7, 13: 15 4 1972 → 29 11 27 9; строки 1111 4 77 / 222 5 нет / нет нет 999;
    # «в расчёте 14 цифр»; БСм = 3×3×4 = 36; ДСм = 8×7×7 = 392.
    r = calculate(BirthInput(1972, 4, 15))
    assert r["date_record"] == "15 4 1972"
    assert r["working_numbers_list"] == [29, 11, 27, 9]
    assert _counts(r) == _grid_counts("1111 4 77 / 222 5 - / - - 999")
    assert r["zeros"] == 0
    assert r["life_number"] == 14
    ln = _lines(r)
    assert (ln["row_147"], ln["row_258"], ln["row_369"]) == (7, 4, 3)
    assert (ln["col_123"], ln["col_456"], ln["col_789"]) == (7, 2, 5)
    assert (ln["diag_159"], ln["diag_357"]) == (8, 3)
    assert r["stability"] == {"bytovaya": 36, "dukhovnaya": 392,
                              "factors": {"A_357": 3, "B_369": 3, "V_258": 4, "G_159": 8, "D_123": 7, "E_147": 7}}


def test_book1_wife_6_9_1973_day_without_zero():
    # [K1] гл. 6: 6 9 1973 → 35 8 23 5 («35 − 6×2 = 23»); строки жены: 1 нет 7 / 2 55 8 / 333 6 99;
    # гл. 13: А=6, Б=6, В=4 → 144; Г=5, Д=5, Е=2 → 50.
    r = calculate(BirthInput(1973, 9, 6))
    assert r["date_record"] == "6 9 1973"
    assert r["working_numbers_list"] == [35, 8, 23, 5]
    assert _counts(r) == _grid_counts("1 - 7 / 2 55 8 / 333 6 99")
    assert r["stability"]["bytovaya"] == 144
    assert r["stability"]["dukhovnaya"] == 50
    # Генерический вариант с ведущим нулём («06.09.1973») дал бы 35 − 0 = 35:
    assert r["vs_generic"]["generic_numbers"] == [35, 8, 35, 8]


def test_book1_marriage_stability_example1():
    # [K1] гл. 13, пример 1: БСС = 36×144 = 5184 → 14 лет; ДСС = 392×50 = 19600 → 54 года; ОСС = 68.
    c = compatibility(BirthInput(1972, 4, 15), BirthInput(1973, 9, 6))
    s = c["marriage_stability"]
    assert (s["BSS"], s["DSS"]) == (5184, 19600)
    assert (s["bss_years"], s["dss_years"], s["OSS_years"]) == (14, 54, 68)


def test_book1_marriage_stability_example2_from_counts():
    # [K1] гл. 13, пример 2 (даты в тексте не приведены, только линии):
    # БСм = 5×5×7 = 125, БСж = 5×2×5 = 50 → 6250 → 17 лет; ДСм = 70, ДСж = 294 → 20580 → 56; ОСС = 73.
    s = stability_years(125, 50, 70, 294)
    assert (s["BSS"], s["DSS"]) == (6250, 20580)
    assert (s["bss_years"], s["dss_years"], s["OSS_years"]) == (17, 56, 73)


def test_book1_example_1_1_2000_time_intervals():
    # [K1] гл. 12 и [PK]: 1 1 2000 → 4 4 2 2; психоматрица 11 / 222 / 44 и 000;
    # 1-й период; строка1 = 4, строка2 = 3, строка3 = 0, столбцы 5, 2, 0; духовная 2, плотская 0.
    r = calculate(BirthInput(2000, 1, 1))
    assert r["working_numbers_list"] == [4, 4, 2, 2]
    assert _counts(r) == _grid_counts("11 44 - / 222 - - / - - -")
    assert r["zeros"] == 3
    assert _lines(r) == {"row_147": 4, "row_258": 3, "row_369": 0, "col_123": 5, "col_456": 2,
                         "col_789": 0, "diag_159": 2, "diag_357": 0}
    ti = r["time_intervals"]
    assert ti["period"] == 1
    assert ti["strong_lines"] == ["row_147", "row_258", "col_123", "col_456", "diag_159"]
    pc = {int(k): v for k, v in ti["max_extra_per_cell"].items()}
    # Книга: «1 – до трёх, 2 – до двух, 3, 6, 7, 8, 9 – одна, 5 – до трёх» — совпадает.
    assert (pc[1], pc[2], pc[3], pc[5], pc[6], pc[7], pc[8], pc[9]) == (3, 2, 1, 3, 1, 1, 1, 1)
    # ⚠ Книга пишет «Цифра 4 – одна цифра», но через 4 проходят ДВЕ сильные линии (строка 1-4-7 и
    # столбец 4-5-6), а правило автора «каждая сильная линия порождает одну цифру» даёт до двух.
    assert pc[4] == 2
    assert any("Нет цифры 9" in w for w in r["warnings"])


def test_tmc_negative_third_number_7_1_2000():
    # [TMC] гл. 1, пример 2: 7 1 2000: 10, 1, «10 − 2×7 = 10 − 14 = 14 − 10 = 4», 4.
    r = calculate(BirthInput(2000, 1, 7))
    assert r["date_record"] == "7 1 2000"
    assert r["third_number_raw"] == -4
    assert r["working_numbers_list"] == [10, 1, 4, 4]
    assert any("отрицательным" in w for w in r["warnings"])


def test_zero_third_number_3_1_2000():
    # Граничный случай: 3 1 2000 → 6, 6, 6 − 2×3 = 0, 0; нули считаются отдельно.
    r = calculate(BirthInput(2000, 1, 3))
    assert r["working_numbers_list"] == [6, 6, 0, 0]
    assert r["zeros"] == 5  # 2000 (три нуля) + 0 + 0
    assert r["life_number"] == 5  # 3, 1, 2, 6, 6


def test_tmc_30_7_1998():
    # [TMC] гл. 1: 30 7 1998 → 37 10 31 4; психоматрица «111 4 7 / нет нет 8 / 333 нет 99 и 00».
    r = calculate(BirthInput(1998, 7, 30))
    assert r["working_numbers_list"] == [37, 10, 31, 4]
    c = _counts(r)
    assert (c[1], c[2], c[3], c[4], c[5], c[6], c[8], c[9]) == (3, 0, 3, 1, 0, 0, 1, 2)
    assert r["zeros"] == 2
    # ⚠ В книге в ячейке 7 напечатано «7», но семёрок две: месяц 7 и число 37 → «77» (опечатка книги).
    assert c[7] == 2


@pytest.mark.parametrize("dmy,grid", [
    # Матрицы, напечатанные автором в [TMC] гл. 2–4 (litresp.ru …/tajni-magicheskih-cifr/3, /4, /5);
    # сверено при проверке 2-й волны.
    ((4, 4, 1964), "11 444 - / 222 - 8 / - 6 9"),
    ((30, 4, 1969), "1 4 - / 22 5 8 / 33 66 99"),
    ((17, 8, 1982), "11 4 77 / 2 - 88 / 33 6 99"),
    ((3, 9, 1937), "1 - 7 / 22 5 8 / 333 6 99"),
    ((9, 8, 1965), "111 - - / 22 5 88 / 3 6 99"),
])
def test_tmc_published_matrices(dmy, grid):
    d, m, y = dmy
    assert _counts(calculate(BirthInput(y, m, d))) == _grid_counts(grid)


def test_tmc_2_11_1943_book_typo():
    # [TMC] гл. 4: «2 11 1943 / 21 3 17 8 / 11111 4 7 / 22 нет 8 / 333 нет 9».
    # ⚠ Троек в расчёте две (год 1943 и второе число 3), а не три — опечатка книги, как и у 30 7 1998.
    r = calculate(BirthInput(1943, 11, 2))
    c = _counts(r)
    assert r["working_numbers_list"] == [21, 3, 17, 8]
    assert {d: c[d] for d in (1, 2, 4, 5, 6, 7, 8, 9)} == {1: 5, 2: 2, 4: 1, 5: 0, 6: 0, 7: 1, 8: 1, 9: 1}
    assert c[3] == 2


def test_tmc_15_8_1957_strong_lines():
    # [TMC] гл. 1: 15 8 1957 → 36 9 34 7; психоматрица 11 4 77 / нет 55 8 / 33 6 99; 5-й период.
    r = calculate(BirthInput(1957, 8, 15))
    assert r["working_numbers_list"] == [36, 9, 34, 7]
    assert _counts(r) == _grid_counts("11 4 77 / - 55 8 / 33 6 99")
    strong = set(r["time_intervals"]["strong_lines"])
    # Книга перечисляет: 3-я строка (5), 3-й столбец (5), плотская (6), духовная (6).
    assert {"row_369", "col_789", "diag_357", "diag_159"} <= strong
    # ⚠ Первая строка «11 4 77» тоже содержит 5 цифр, и по правилу автора («5 и более») она сильная;
    # в книге она пропущена.
    assert "row_147" in strong and len(strong) == 5


def test_tmc_event_year_only_1242():
    # [TMC] «Исход Ледового побоища 1242 года»: 1 2 4 2 → 9 9 7 7; 2-й период; сильные все линии,
    # кроме второго столбца.
    p = psychomatrix_from_groups([1242], year=1242)
    assert p["working_numbers_list"] == [9, 9, 7, 7]
    assert p["time_intervals"]["period"] == 2
    assert set(p["time_intervals"]["strong_lines"]) == {
        "row_147", "row_258", "row_369", "col_123", "col_789", "diag_159", "diag_357"}


def test_dr_event_year_only_988():
    # [DR] «Психоматрица Крещения Руси: ? ? 988 → 25 7 7 7» (первая цифра ряда — 9).
    assert working_numbers([988])["first"] == 25
    p = psychomatrix_from_groups([988])
    assert p["working_numbers_list"] == [25, 7, 7, 7]


AUTHOR_VECTORS = [
    # (день, месяц, год) в записи автора (для дореволюционных — старый стиль), ожидаемые 4 числа, источник
    ((30, 5, 1672), [24, 6, 18, 9], "DR: Пётр I, «24 − 2×3 = 18»"),
    ((8, 11, 1711), [20, 2, 4, 4], "DR: М. В. Ломоносов («20 2 44»)"),
    ((13, 11, 1730), [17, 8, 15, 6], "DR: А. В. Суворов"),
    ((27, 10, 1492), [26, 8, 22, 4], "DR"),
    ((25, 10, 1917), [26, 8, 22, 4], "DR: 25 октября 1917"),
    ((7, 11, 1917), [27, 9, 13, 4], "DR: «711 1917 / 279 134»"),
    ((10, 4, 1870), [21, 3, 19, 10], "DR: В. И. Ленин (ст. ст.), четвёртое число 10 не сокращается"),
    ((2, 3, 1931), [19, 10, 15, 6], "DR: М. С. Горбачёв, второе число 10 не сокращается"),
    ((1, 2, 1931), [17, 8, 15, 6], "DR: Б. Н. Ельцин"),
    ((12, 6, 1990), [28, 10, 26, 8], "DR"),
    ((12, 6, 1991), [29, 11, 27, 9], "DR"),
    ((2, 10, 1974), [24, 6, 20, 2], "DR"),
    ((21, 6, 1962), [27, 9, 23, 5], "DR"),
    ((24, 6, 1990), [31, 4, 27, 9], "DR"),
    ((15, 8, 1990), [33, 6, 31, 4], "DR"),
    ((15, 10, 1956), [28, 10, 26, 8], "DR"),
    ((16, 10, 1991), [28, 10, 26, 8], "DR"),
    ((1, 2, 1970), [20, 2, 18, 9], "TMC гл. 2"),
    ((4, 4, 1964), [28, 10, 20, 2], "TMC гл. 2"),
    ((30, 6, 1908), [27, 9, 21, 3], "TMC гл. 2: Тунгусский феномен"),
    ((30, 4, 1969), [32, 5, 26, 8], "TMC гл. 3"),
    ((17, 8, 1982), [36, 9, 34, 7], "TMC гл. 3"),
    ((3, 9, 1937), [32, 5, 26, 8], "TMC гл. 4"),
    ((2, 11, 1943), [21, 3, 17, 8], "TMC гл. 4"),
    ((9, 8, 1965), [38, 11, 20, 2], "TMC гл. 4"),
    ((1, 1, 2000), [4, 4, 2, 2], "K1 гл. 12"),
    ((7, 1, 2000), [10, 1, 4, 4], "TMC гл. 1"),
]


@pytest.mark.parametrize("dmy,expected,src", AUTHOR_VECTORS, ids=[s for _, _, s in AUTHOR_VECTORS])
def test_author_published_working_numbers(dmy, expected, src):
    d, m, y = dmy
    assert psychomatrix_from_groups([d, m, y])["working_numbers_list"] == expected


@pytest.mark.parametrize("greg,expected_record,expected", [
    ((1870, 4, 22), "10 4 1870", [21, 3, 19, 10]),   # Ленин: 22.04.1870 н. ст. = 10.04 ст. ст.
    ((1672, 6, 9), "30 5 1672", [24, 6, 18, 9]),     # Пётр I: 9.06.1672 н. ст. = 30.05 ст. ст.
    ((1711, 11, 19), "8 11 1711", [20, 2, 4, 4]),    # Ломоносов: 19.11.1711 н. ст. = 8.11 ст. ст.
    ((1730, 11, 24), "13 11 1730", [17, 8, 15, 6]),  # Суворов: 24.11.1730 н. ст. = 13.11 ст. ст.
])
def test_julian_option_reproduces_author_old_style(greg, expected_record, expected):
    r = calculate(BirthInput(*greg), calendar="julian")
    assert r["date_record"] == expected_record
    assert r["working_numbers_list"] == expected


# ---------------------------------------------------------------------------
# Граничные случаи и инварианты
# ---------------------------------------------------------------------------

def test_gregorian_to_julian_reference_points():
    assert gregorian_to_julian(1918, 2, 14) == (1918, 2, 1)
    assert gregorian_to_julian(1582, 10, 15) == (1582, 10, 5)
    assert gregorian_to_julian(2000, 3, 14) == (2000, 3, 1)


def test_time_period_table():
    # [TMC]: 1-й — 2000–2199, 2-й — 2200–2399, …, 5-й — 1800–1999.
    assert [time_period(y) for y in (2000, 2199, 2200, 2399, 1600, 1799, 1800, 1999, 1242, 988)] == \
        [1, 1, 2, 2, 4, 4, 5, 5, 2, 5]


def test_boundary_year_warning():
    assert any("границе периода" in w for w in calculate(BirthInput(2000, 5, 5))["warnings"])
    assert not any("границе периода" in w for w in calculate(BirthInput(1990, 5, 15))["warnings"])


def test_julian_after_1918_warns_and_bad_option_raises():
    assert calculate(BirthInput(1990, 5, 15), calendar="julian")["warnings"]
    with pytest.raises(ValueError):
        calculate(BirthInput(1990, 5, 15), calendar="mayan")
    with pytest.raises(ValueError):
        calculate(BirthInput(2001, 2, 29))


def test_transition_5_9_is_two_way():
    # [DR], «Цифра 5…»: «55 дают 9 и 99 дают 5»; «Переходы цифр»: «55 — дополнительно 9»,
    # «если 99, то можно дополнить одной цифрой 5».
    # T1 15.05.1990: 55 и 99 → оба перехода; 15.04.1972: 5, 999 → только 99 → +5.
    t1 = {x["transition"] for x in calculate(BirthInput(1990, 5, 15))["possible_transitions"]}
    assert {"55 → +9", "99 → +5"} <= t1
    ex = {x["transition"] for x in calculate(BirthInput(1972, 4, 15))["possible_transitions"]}
    assert "99 → +5" in ex and "55 → +9" not in ex


def test_calm_character_examples():
    # «111 и 8 → 1 и 88»; «11111 → 1 и 88»; «1111 в покое ≈ 11 и 8».
    assert calculate(BirthInput(1990, 5, 15))["calm_character"] == "1 и 88"   # T1: 111 и 8
    assert calculate(BirthInput(1972, 4, 15))["calm_character"] == "11 и 8"   # 1111, 8 нет


def test_json_serializable_and_steps():
    r = calculate(BirthInput(1984, 2, 4))
    json.dumps(r, ensure_ascii=False)
    assert r["method"] == "alexandrov_psychomatrix"
    assert any("4 2 1984" in s for s in r["steps"])
    json.dumps(compatibility(BirthInput(1972, 4, 15), BirthInput(1973, 9, 6)), ensure_ascii=False)


def test_invariants_over_range():
    """Для всех дат 1900–2100 (шаг 7 дней): сумма ячеек = номер жизни ≤ 15 (утверждение автора),
    линии = суммы ячеек, число сильных линий = максимум дополнительных цифр, третье ≥ 0."""
    d = date(1900, 1, 1)
    while d <= date(2100, 12, 31):
        p = psychomatrix_from_groups([d.day, d.month, d.year], year=d.year)
        c = {int(k): v for k, v in p["counts"].items()}
        digits = "".join(map(str, [d.day, d.month, d.year] + p["working_numbers_list"]))
        assert sum(c.values()) + p["zeros"] == len(digits)
        assert p["life_number"] <= 15
        assert p["lines"]["row_147"] == c[1] + c[4] + c[7]
        assert p["lines"]["diag_357"] == c[3] + c[5] + c[7]
        assert p["working_numbers"]["third"] >= 0
        ti = p["time_intervals"]
        assert ti["max_extra_total"] == len(ti["strong_lines"])
        d += timedelta(days=7)
