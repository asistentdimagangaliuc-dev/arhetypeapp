"""Тесты калькулятора «Квадрат Пифагора (психоматрица)».

Запуск: .venv/bin/python -m pytest calculators/tests/test_pythagoras.py -q
Внешние векторы взяты из опубликованных источников (URL — в комментариях у каждого теста).
"""
from __future__ import annotations

import json
from datetime import date, timedelta

import pytest

from calculators.common.time import BirthInput
from calculators.pythagoras import (
    CELL_KEYS, LINE_KEYS, LINES, calculate, date_digits, digits_of, working_numbers,
)


def wn(d: int, m: int, y: int, **opt) -> tuple[int, int, int, int]:
    r = calculate(BirthInput(y, m, d), **opt)["working_numbers"]
    return r["first"], r["second"], r["third"], r["fourth"]


def grid(d: int, m: int, y: int, **opt) -> list[list[str]]:
    return calculate(BirthInput(y, m, d), **opt)["grid"]


def counts(d: int, m: int, y: int, **opt) -> dict[int, int]:
    c = calculate(BirthInput(y, m, d), **opt)["counts"]
    return {int(k): v for k, v in c.items()}


def lines(d: int, m: int, y: int, **opt) -> dict[str, int]:
    r = calculate(BirthInput(y, m, d), **opt)["lines"]
    return {k: v["count"] for k, v in r.items()}


# ---------------------------------------------------------------------------
# Эталонные персоны T1–T4 (ручной расчёт, разобран в knowledge-base/08-pythagoras-square.md)
# ---------------------------------------------------------------------------

def test_t1_15_05_1990():
    # 1+5+5+1+9+9 = 30; 3+0 = 3; 30 − 2×1 = 28; 2+8 = 10
    assert wn(15, 5, 1990) == (30, 3, 28, 10)
    assert grid(15, 5, 1990) == [["111", "", ""], ["2", "55", "8"], ["33", "", "99"]]
    assert lines(15, 5, 1990) == {"goal": 3, "family": 4, "habits": 4, "self_esteem": 6,
                                  "household": 2, "talent": 3, "spirituality": 7, "temperament": 4}


def test_t2_04_02_1984_leading_zero_day():
    # день 04: удваивается первая НЕНУЛЕВАЯ цифра 4 → 28 − 8 = 20
    assert wn(4, 2, 1984) == (28, 10, 20, 2)
    assert grid(4, 2, 1984) == [["11", "44", ""], ["2222", "", "88"], ["", "", "9"]]
    # вариант «буквально»: удваивается 0 → 3-е = 1-е
    assert wn(4, 2, 1984, day_digit="literal") == (28, 10, 28, 10)


def test_t3_29_02_2004_post2000_and_leap_day():
    assert wn(29, 2, 2004) == (19, 10, 15, 6)
    assert grid(29, 2, 2004) == [["111", "4", ""], ["222", "5", ""], ["", "6", "99"]]
    # вариант «+19»: 3-е = 19 + 19 = 38, 4-е = 3 + 8 = 11
    assert wn(29, 2, 2004, post2000_rule="plus19") == (19, 10, 38, 11)
    assert grid(29, 2, 2004, post2000_rule="plus19") == [["1111", "4", ""], ["222", "", "8"],
                                                         ["3", "", "99"]]


def test_t4_14_03_1879_einstein():
    # 1+4+3+1+8+7+9 = 33; 6; 33 − 2 = 31; 4
    assert wn(14, 3, 1879) == (33, 6, 31, 4)
    assert grid(14, 3, 1879) == [["111", "44", "7"], ["", "", "8"], ["3333", "6", "9"]]
    r = calculate(BirthInput(1879, 3, 14))
    assert r["digits_total"] == 13
    assert any("1918" in w for w in r["warnings"])  # предупреждение о стиле даты


# ---------------------------------------------------------------------------
# Первоисточник: А. Ф. Александров, «Дата рождения — ключ к пониманию человека»
# https://litresp.ru/chitat/ru/%D0%90/aleksandrov-aleksandr-fedorovich/data-rozhdeniya--klyuch-k-ponimaniyu-cheloveka/4
# (копия на royallib.com содержит только предисловие; тот же пример 15 4 1972:
#  https://thelib.ru/books/aleksandr_fedorovich_aleksandrov/cifrovoy_analiz_dat_rozhdeniya_i_sobytiy_kniga_1_psihomatrica_i_ee_svoystva-read-2.html)
# ---------------------------------------------------------------------------

def test_alexandrov_15_04_1972():
    # «1541972 / 29 11 27 9 … в расчете — 14 цифр»; строки «1111 4 77», «222 5 нет», «нет нет 999»
    assert wn(15, 4, 1972) == (29, 11, 27, 9)
    assert grid(15, 4, 1972) == [["1111", "4", "77"], ["222", "5", ""], ["", "", "999"]]
    r = calculate(BirthInput(1972, 4, 15))
    assert r["digits_total"] == 14
    ln = lines(15, 4, 1972)
    # «в первой строке (1111, 4, 77) — семь цифр»; «во второй строке 4 цифры»; «в третьей строке 3 цифры»
    # «1-й столбец — 7 цифр, 2-й столбец — 2 цифры, 3-й столбец — 5 цифр»
    assert (ln["goal"], ln["family"], ln["habits"]) == (7, 4, 3)
    assert (ln["self_esteem"], ln["household"], ln["talent"]) == (7, 2, 5)


def test_alexandrov_06_09_1973_day_with_zero():
    # «691973 … 6+9+1+9+7+3=35 … 3+5=8 … 35−6×2=35−12=23 … 2+3=5»
    assert wn(6, 9, 1973) == (35, 8, 23, 5)


def test_alexandrov_01_01_2000():
    # «1 1 2000 4422» — раздел «Применение системы Пифагора после 2000 года»
    assert wn(1, 1, 2000) == (4, 4, 2, 2)
    assert counts(1, 1, 2000) == {1: 2, 2: 3, 3: 0, 4: 2, 5: 0, 6: 0, 7: 0, 8: 0, 9: 0}


# ---------------------------------------------------------------------------
# numerolog.ru — https://numerolog.ru/pifagor/kak-rasschitat-kvadrat-pifagora.html
# ---------------------------------------------------------------------------

def test_numerolog_27_10_1986_grid_and_lines():
    assert wn(27, 10, 1986) == (34, 7, 30, 3)
    assert grid(27, 10, 1986) == [["11", "4", "77"], ["2", "", "8"], ["333", "6", "9"]]
    # «Темперамент – 5, Цель – 5, Семья – 2, Привычки – 5, Самооценка – 6, Быт – 2, Талант – 4, Дух – 3»
    assert lines(27, 10, 1986) == {"goal": 5, "family": 2, "habits": 5, "self_esteem": 6,
                                   "household": 2, "talent": 4, "spirituality": 3, "temperament": 5}


def test_numerolog_01_01_2015_post2000():
    # Опубликована только матрица: «11111 пусто пусто / 2 5 88 / пусто пусто пусто»
    # (рабочие числа на странице не приведены; 10 1 8 8 выведены из матрицы).
    assert wn(1, 1, 2015) == (10, 1, 8, 8)
    assert grid(1, 1, 2015) == [["11111", "", ""], ["2", "5", "88"], ["", "", ""]]
    # Вектор различает варианты: при удвоении «буквального» 0 (день 01) вышло бы 10 1 10 1 и
    # матрица 1111111 / 2 5 — / —, что НЕ совпадает с публикацией. Хотя numerolog.ru велит
    # писать «01, 02 … 09» и удваивать «первую цифру в дате рождения», его пример подтверждает
    # вариант first_nonzero (по умолчанию).
    assert wn(1, 1, 2015, day_digit="literal") == (10, 1, 10, 1)
    assert grid(1, 1, 2015, day_digit="literal") == [["1111111", "", ""], ["2", "5", ""], ["", "", ""]]


# ---------------------------------------------------------------------------
# С. Трошин (VK) — https://vk.ru/@sergei_troshin-kak-rasschitat-psihomatricu-ikvadrat-pifagora-po-date-rozhde
# правило: искусственные нули не учитываются; отрицательное 3-е — «используем модуль числа»
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("d,m,y,expected", [
    (22, 9, 1988, (39, 12, 35, 8)),
    (8, 7, 1986, (39, 12, 23, 5)),    # день 08 → удваиваем 8
    (15, 12, 2005, (16, 7, 14, 5)),
    (2, 12, 1977, (29, 11, 25, 7)),
    (17, 3, 1962, (29, 11, 27, 9)),
    (20, 2, 1962, (22, 4, 18, 9)),
    (30, 4, 1989, (34, 7, 28, 10)),   # 4-е = 2+8 = 10, дальше не сворачиваем
    (5, 11, 2000, (9, 9, 1, 1)),      # 9 − 10 = −1 → 1
    (5, 1, 2020, (10, 1, 0, 0)),      # 10 − 10 = 0
])
def test_troshin_vectors(d, m, y, expected):
    assert wn(d, m, y) == expected


# ---------------------------------------------------------------------------
# istashenko.com — https://www.istashenko.com/2014/11/deti-21-veka-psihomatritsa/
# (ответы автора в комментариях; «минус не учитывается»)
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("d,m,y,expected", [
    (27, 3, 2019, (24, 6, 20, 2)),
    (9, 1, 2002, (14, 5, 4, 4)),      # 14 − 18 = −4 → 4
    (7, 1, 2011, (12, 3, 2, 2)),      # 12 − 14 = −2 → 2
])
def test_istashenko_vectors(d, m, y, expected):
    assert wn(d, m, y) == expected


def test_negative_third_is_flagged():
    r = calculate(BirthInput(2002, 1, 9))
    assert r["working_numbers"]["third_raw"] == -4
    assert any("отрицательным" in w for w in r["warnings"])


def test_years_before_1000_and_negative_third_outside_2000s():
    # Ручной расчёт (проверка 2-й волны): год < 1000 пишется как есть, ведущий 0 года в квадрат не идёт.
    # 15.06.988: 1+5+6+9+8+8 = 37; 3+7 = 10; 37 − 2 = 35; 3+5 = 8.
    assert wn(15, 6, 988) == (37, 10, 35, 8)
    assert calculate(BirthInput(988, 6, 15))["date_digits"] == "15060988"
    # Отрицательное 3-е бывает не только после 2000 г., а у любых лет с малой суммой цифр:
    # 30.01.1000: 3+1+1 = 5; 5; 5 − 6 = −1 → 1; 1.
    r = calculate(BirthInput(1000, 1, 30))
    assert wn(30, 1, 1000) == (5, 5, 1, 1)
    assert r["working_numbers"]["third_raw"] == -1
    assert r["counts"] == {"1": 4, "2": 0, "3": 1, "4": 0, "5": 2, "6": 0, "7": 0, "8": 0, "9": 0}


# ---------------------------------------------------------------------------
# Прочие независимые разборы
# ---------------------------------------------------------------------------

def test_kp_12_09_1997():
    # https://www.kp.ru/woman/goroskop/kvadrat-pifagora/ — «12091997, 38, 11, 36, 9»; сетка 1111/-/7; 2/-/8; 33/6/9999
    assert wn(12, 9, 1997) == (38, 11, 36, 9)
    assert grid(12, 9, 1997) == [["1111", "", "7"], ["2", "", "8"], ["33", "6", "9999"]]


def test_web_calculator_15_08_1986():
    # https://web-calculator.ru/ezoterika/kvadrat-pifagora — 38, 11, 36, 9;
    # «единиц — четыре, троек — две, пятёрка — одна, шестёрок — две, восьмёрок — три, девяток — две; ячейки 2, 4 и 7 пустые»
    assert wn(15, 8, 1986) == (38, 11, 36, 9)
    assert counts(15, 8, 1986) == {1: 4, 2: 0, 3: 2, 4: 0, 5: 1, 6: 2, 7: 0, 8: 3, 9: 2}


def test_gadalkindom_15_10_1988():
    # https://gadalkindom.ru/kvadrat-pifagora — ряды «15101988» и «33063104»
    assert wn(15, 10, 1988) == (33, 6, 31, 4)
    assert counts(15, 10, 1988) == {1: 4, 2: 0, 3: 3, 4: 1, 5: 1, 6: 1, 7: 0, 8: 2, 9: 1}


def test_7days_17_10_1991():
    # https://7days.ru/astro/horoscope/psikhomatritsa-po-date-rozhdeniya-ili-kvadrat-pifagora.htm — «1711991, 29, 11, 27, 9»
    assert wn(17, 10, 1991) == (29, 11, 27, 9)


def test_afisha_12_07_1992_fourth_not_reduced():
    # https://daily.afisha.ru/poleznye-stati/30489-kvadrat-matrica-pifagora-chto-eto-kak-rasschitat-po-date-rozhdeniya-i-kak-rasshifrovat/
    # «2 + 9 = 11 — четвертое дополнительное число»; ряд 1,2,0,7,1,9,9,2,3,1,4,2,9,1,1
    assert wn(12, 7, 1992) == (31, 4, 29, 11)
    r = calculate(BirthInput(1992, 7, 12))
    assert sorted(r["all_digits"]) == sorted([1, 2, 7, 1, 9, 9, 2, 3, 1, 4, 2, 9, 1, 1])


def test_heaclub_12_05_2002_digit_code():
    # https://heaclub.ru/primenenie-sistemy-pifagora-v-numerologii-dlya-lic-rozhdennyh-posle-2000-goda
    # «Цифровой код для заполнения матрицы … 1111222235»
    r = calculate(BirthInput(2002, 5, 12))
    assert "".join(str(x) for x in sorted(r["all_digits"])) == "1111222235"


def test_zet_15_06_1988():
    # https://zet.in.ua/ru/kvadrat-pifahora-povnyi-hid-z-rozrakhunku-ta-rozshyfrovky-psykhomatrytsi/ — «38, 11, 36, 9»
    assert wn(15, 6, 1988) == (38, 11, 36, 9)


# ---------------------------------------------------------------------------
# Варианты для рождённых после 2000 года
# ---------------------------------------------------------------------------

def test_tayasheva_year_1999_variant():
    # https://proza.ru/2019/05/15/639 — «5 10 1999 11 … 5+1+1+9+9+9+1+1=36. 3+6=9. 36-5*2=36-10=26. 2+6=8»;
    # «В квадратики записываем год и цифры 1999 и 11 и 2010 тоже»
    r = calculate(BirthInput(2010, 10, 5), post2000_rule="year_1999")
    w = r["working_numbers"]
    assert (w["first"], w["second"], w["third"], w["fourth"]) == (36, 9, 26, 8)
    assert r["extra_digits"] == [1, 9, 9, 9, 1, 1]
    assert r["counts"] == {"1": 5, "2": 2, "3": 1, "4": 0, "5": 1, "6": 2, "7": 0, "8": 1, "9": 4}
    # классика для той же даты: 5+1+2+1 = 9; 9; 9 − 10 = −1 → 1; 1
    assert wn(5, 10, 2010) == (9, 9, 1, 1)


def test_plus19_rule_mechanics():
    # Правило «если позже [2000], прибавляем 19» — https://tayniymir.com/numerology/prognoz.html
    # (там же для дат до 2000: «отнимаем 2», пример 01.01.1984: 24 − 2 = 22, 2 + 2 = 4 — совпадает с классикой,
    #  т. к. первая цифра дня = 1). Опубликованного разбора даты после 2000 по «+19» не найдено ⚠.
    assert wn(1, 1, 1984) == (24, 6, 22, 4)
    assert wn(1, 1, 2000, post2000_rule="plus19") == (4, 4, 23, 5)
    assert wn(5, 11, 2000, post2000_rule="plus19") == (9, 9, 28, 10)


def test_add_1_9_variant():
    # web-calculator.ru: переключатель «Расширенный метод для рождённых после 2000 года
    # (добавляет 1 и 9; спорный, не канон)»
    base = counts(1, 1, 2000)
    var = counts(1, 1, 2000, post2000_rule="add_1_9")
    assert var[1] == base[1] + 1 and var[9] == base[9] + 1
    assert sum(var.values()) == sum(base.values()) + 2


def _web_calculator_js_counts(day: int, month: int, year: int, extended: bool) -> dict[int, int]:
    """Перенос логики https://web-calculator.ru/js/ezoterika/kvadrat-pifagora.js (скачан 14.10.2026):
    r(e,n,t): a = s(e)+s(n)+s(t), i = s(a), r = первая цифра String(день), o = a − 2·r,
    w4 = s(|o|); o(e,n,t,a): l = [].concat(i(e), i(n), i(t), i(w1), i(w2), i(|w3|), i(w4));
    «a&&t>=2e3&&(l=l.concat([1,9]),o=!0)» — расширенный режим и год >= 2000 добавляют ровно 1 и 9;
    в ячейки идут цифры 1..9."""
    def s(n: int) -> int:
        return sum(int(c) for c in str(abs(n)))

    def i(n: int) -> list[int]:
        return [int(c) for c in str(abs(n))]

    w1 = s(day) + s(month) + s(year)
    w2 = s(w1)
    w3 = w1 - 2 * int(str(day)[0])
    w4 = s(abs(w3))
    digits = i(day) + i(month) + i(year) + i(w1) + i(w2) + i(abs(w3)) + i(w4)
    if extended and year >= 2000:
        digits += [1, 9]
    return {d: digits.count(d) for d in range(1, 10)}


@pytest.mark.parametrize("d,m,y", [(1, 1, 2000), (29, 2, 2004), (5, 10, 2010), (31, 12, 1999),
                                   (15, 5, 1990), (9, 1, 2002), (27, 3, 2019), (7, 1, 2000)])
def test_add_1_9_matches_web_calculator_js(d, m, y):
    """Вариант «1 и 9» подтверждён кодом web-calculator.ru: ровно одна 1 и одна 9, рабочие числа
    классические, порог — год >= 2000 (для 31.12.1999 опция не применяется ни там, ни здесь)."""
    assert counts(d, m, y, post2000_rule="add_1_9") == _web_calculator_js_counts(d, m, y, True)
    assert counts(d, m, y) == _web_calculator_js_counts(d, m, y, False)


def test_sidorova_ideal_row_01_01_1984():
    # https://tayniymir.com/numerology/prognoz.html (метод Н. Сидоровой «Идеал»): «Сложите цифры:
    # 1+1+1+9+8+4=24. Если дата рождения до 2000 года, отнимаем 2, если позже, прибавляем 19. Это постоянное
    # значение. 24-2=22. Складываем: 2+2=4. Выписываем все цифры: 1.1.1984.24.2.22.4».
    # Пифагорейский ряд той же даты на той же странице: «1.1.1984.24.6.22.4» — константа стоит в ряду
    # на месте 2-го числа.
    r = calculate(BirthInput(1984, 1, 1), post2000_rule="sidorova")
    assert r["working_row"] == "24 2 22 4"
    assert r["steps"][-4] == "Ряд: 1.1.1984.24.2.22.4"
    assert r["all_digits"] == [1, 1, 1, 9, 8, 4, 2, 4, 2, 2, 2, 4]
    assert counts(1, 1, 1984, post2000_rule="sidorova") == {1: 3, 2: 4, 3: 0, 4: 3, 5: 0, 6: 0, 7: 0,
                                                            8: 1, 9: 1}
    assert calculate(BirthInput(1984, 1, 1))["working_row"] == "24 6 22 4"
    assert r["leading_number"] is None and r["warnings"]


def test_sidorova_after_2000_constant_19_in_row():
    # Та же система после 2000 г.: константа 19 вписывается в ряд (по аналогии с «2» в примере 1984 г.;
    # опубликованного разбора даты после 2000 г. нет ⚠). 29.02.2004: 19, 19, 19+19 = 38, 3+8 = 11.
    assert wn(29, 2, 2004, post2000_rule="sidorova") == (19, 19, 38, 11)
    assert wn(29, 2, 2004, post2000_rule="plus19") == (19, 10, 38, 11)   # реконструкция без константы
    assert grid(29, 2, 2004, post2000_rule="sidorova") == [["1111", "4", ""], ["222", "", "8"],
                                                           ["3", "", "999"]]


def test_post2000_rule_ignored_before_2000():
    r = calculate(BirthInput(1990, 5, 15), post2000_rule="plus19")
    assert r["inputs_used"]["post2000_applied"] is False
    assert (r["working_numbers"]["third"]) == 28
    assert any("не применена" in w for w in r["warnings"])


def test_bad_options_and_dates():
    with pytest.raises(ValueError):
        calculate(BirthInput(1990, 5, 15), post2000_rule="foo")
    with pytest.raises(ValueError):
        calculate(BirthInput(1990, 5, 15), day_digit="foo")
    with pytest.raises(ValueError):
        calculate(BirthInput(1990, 2, 30))


# ---------------------------------------------------------------------------
# Инварианты
# ---------------------------------------------------------------------------

def test_result_contract_and_json():
    r = calculate(BirthInput(1990, 5, 15, 14, 30, place="Москва"))
    for key in ("method", "variant", "inputs_used", "warnings", "steps", "working_numbers", "cells",
                "lines", "grid"):
        assert key in r
    json.dumps(r, ensure_ascii=False)
    assert all("key" in c for c in r["cells"].values())
    assert all("key" in v for v in r["lines"].values())
    assert r["inputs_used"]["time_used"] is False


def test_interpretation_tables_cover_all_counts():
    for d, table in CELL_KEYS.items():
        covered = set()
        for lo, hi, _ in table:
            covered.update(range(lo, (hi if hi is not None else 20) + 1))
        assert covered >= set(range(0, 21)), d
    for k, table in LINE_KEYS.items():
        covered = set()
        for lo, hi, _ in table:
            covered.update(range(lo, (hi if hi is not None else 30) + 1))
        assert covered >= set(range(0, 31)), k
    assert set(LINE_KEYS) == set(LINES)


def test_invariants_over_many_dates():
    d = date(1900, 1, 1)
    while d <= date(2030, 12, 31):
        r = calculate(BirthInput(d.year, d.month, d.day), interpret=False)
        c = {int(k): v for k, v in r["counts"].items()}
        total = r["digits_total"]
        ln = {k: v["count"] for k, v in r["lines"].items()}
        assert ln["goal"] + ln["family"] + ln["habits"] == total
        assert ln["self_esteem"] + ln["household"] + ln["talent"] == total
        w = r["working_numbers"]
        assert w["second"] == sum(digits_of(w["first"]))
        assert w["fourth"] == sum(digits_of(w["third"]))
        nz = [x for x in date_digits(d.day, d.month, d.year) if x]
        assert total == len(nz) + sum(1 for n in (w["first"], w["second"], w["third"], w["fourth"])
                                      for x in digits_of(n) if x)
        assert total <= 15  # Александров: «больше 15 цифр не будет»
        if d.year < 2000:
            assert w["third_raw"] >= 0 and c[1] >= 1 and c[9] >= 1  # для 1900–1999 всегда есть 1 и 9
        d += timedelta(days=7)
