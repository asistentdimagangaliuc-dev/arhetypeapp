"""Тесты модуля 15: Сюцай (цифровая психология Ж. Кожамжарова).

Эталоны T1–T4 посчитаны вручную по алгоритму из knowledge-base/15-syutsay.md
(и сверены с логикой калькулятора findh.org). Внешние векторы — из опубликованных
материалов школы и прессы; URL — в комментарии у каждого теста.
"""
from __future__ import annotations

import json

import pytest

from calculators.common.time import BirthInput
from calculators.syutsay import (
    CONSCIOUSNESS_DAYS,
    PLANETS,
    YEAR_THEMES,
    build_matrix,
    calculate,
    calendar_day,
    compatibility,
    consciousness_number,
    extract_given_name,
    financial_code_findh,
    mission_number,
    name_number,
    personal_month,
    personal_year,
    universal_month,
    universal_year,
)

T1 = BirthInput(1990, 5, 15, 14, 30, place="Москва", gender="female", name="Иванова Анна Сергеевна")
T2 = BirthInput(1984, 2, 4, 23, 30, place="Москва", gender="male", name="Петров Дмитрий Олегович")
T3 = BirthInput(2004, 2, 29, 8, 15, place="Санкт-Петербург", gender="female",
                name="Смирнова Мария Александровна")
T4 = BirthInput(1879, 3, 14, 11, 30, tz="LMT", lat=48.4011, lon=9.9876, gender="male",
                name="Эйнштейн Альберт / Albert Einstein")


def cells(year: int, month: int, day: int) -> dict[int, str]:
    """Непустые клетки матрицы: {цифра: '11'}."""
    mx = build_matrix(year, month, day)
    return {int(k): v for k, v in mx["cells"].items() if v != "–"}


def line(mx: dict, line_id: str) -> dict:
    return next(ln for ln in mx["lines"] if ln["id"] == line_id)


# ---------------------------------------------------------------------------
# T1–T4
# ---------------------------------------------------------------------------

def test_t1():
    r = calculate(T1, target_year=2026, partner="1984-02-04")
    json.dumps(r, ensure_ascii=False)
    assert r["consciousness"]["number"] == 6 and r["consciousness"]["chain"] == [15, 6]
    assert r["consciousness"]["planet"] == "Венера"
    assert r["mission"]["number"] == 3 and r["mission"]["chain"] == [30, 3]
    assert not r["mission"]["equals_consciousness"]
    mx = r["matrix"]
    assert cells(1990, 5, 15) == {1: "11", 5: "55", 9: "99"}
    assert mx["zeros"] == 2 and mx["missing"] == [2, 3, 4, 6, 7, 8] and mx["repeated"] == [1, 5, 9]
    assert mx["grid"] == [["–", "–", "99"], ["–", "55", "–"], ["11", "–", "–"]]
    assert line(mx, "row_147")["status"] == "partial"
    assert line(mx, "diag_159")["status"] == "full"          # 1, 5, 9 все есть
    assert mx["programs"][0]["active"] and mx["programs"][0]["amplified"]
    assert r["years"]["personal_year"]["number"] == 3        # 1+5+0+5+2+0+2+6 = 21 → 3
    assert r["years"]["universal_year"]["number"] == 1       # 2026 → 10 → 1
    assert r["name"]["latin"] == "ANNA" and r["name"]["number"] == 3
    assert r["financial_code_findh"]["code"] == "6513"
    assert r["compatibility"]["consciousness"]["relation"] == "not_described"   # 6 и 4
    assert r["life_stages"]["mission_full"]["year"] == 2023
    assert any("Время рождения" in w for w in r["warnings"])


def test_t2():
    r = calculate(T2, target_year=2026)
    assert r["consciousness"]["number"] == 4 and r["consciousness"]["planet"] == "Раху"
    assert r["mission"]["number"] == 1 and r["mission"]["chain"] == [28, 10, 1]
    assert cells(1984, 2, 4) == {1: "1", 2: "2", 4: "44", 8: "8", 9: "9"}
    mx = r["matrix"]
    assert mx["missing"] == [3, 5, 6, 7]
    assert line(mx, "row_147")["missing_cells"] == [7]
    assert mx["programs"][0]["active"] and not mx["programs"][0]["amplified"]
    assert r["years"]["personal_year"]["number"] == 7        # 0+4+0+2+2+0+2+6 = 16 → 7
    # Личунь и поздний час Цзы на Сюцай не влияют: берётся гражданская дата 04.02.1984
    assert r["inputs_used"]["date"] == "04.02.1984"
    assert r["name"]["latin"] == "DMITRII" and r["name"]["number"] == 8
    assert calculate(T2, target_year=2026, name_latin="DMITRY")["name"]["number"] == 7
    assert r["financial_code_findh"]["code"] == "4241"


def test_t3_29_february():
    r = calculate(T3, target_year=2026, partner="04.02.1984")
    assert r["consciousness"]["chain"] == [29, 11, 2]        # 11 мастер-числом НЕ остаётся
    assert r["consciousness"]["day_note"] and "гипнотиз" in r["consciousness"]["day_note"]
    assert r["mission"]["chain"] == [19, 10, 1]
    assert cells(2004, 2, 29) == {2: "222", 4: "4", 9: "9"}
    assert r["matrix"]["zeros"] == 3
    assert not r["matrix"]["programs"][0]["active"]         # нет 1
    assert r["years"]["personal_year"]["number"] == 5        # 23 → 5; 29.02 на личный год не влияет
    comp = r["compatibility"]["consciousness"]               # ЧС 2 и ЧС 4
    assert comp["relation"] == "difficult" and comp["suffers"] == 2
    assert r["name"]["latin"] == "MARIIA" and r["name"]["number"] == 1
    assert r["financial_code_findh"]["code"] == "2261"


def test_t4():
    r = calculate(T4, target_year=2026)
    assert r["consciousness"]["number"] == 5 and r["consciousness"]["planet"] == "Меркурий"
    assert r["mission"]["chain"] == [33, 6]                  # 33 мастер-числом НЕ остаётся
    assert cells(1879, 3, 14) == {1: "11", 3: "3", 4: "4", 7: "7", 8: "8", 9: "9"}
    mx = r["matrix"]
    assert mx["missing"] == [2, 5, 6]
    assert line(mx, "row_147")["status"] == "full"            # линия денег заполнена
    assert line(mx, "col_987")["status"] == "full"
    assert r["years"]["personal_year"]["number"] == 9        # 18 → 9
    assert r["name"]["latin"] == "ALBERT" and r["name"]["number"] == 8
    assert r["financial_code_findh"]["code"] == "5376"


# ---------------------------------------------------------------------------
# Векторы школы (syutsay.ru, zhanatglobal.com)
# ---------------------------------------------------------------------------

def test_matrix_16_07_1984_syutsay_ru():
    # https://syutsay.ru/matritsa-syutsay — картинка «Как составить свою матрицу»:
    # 16.07.1984 → 3 6 9 / 2 5 8 / 1 4 7 заполняется: «6 9 / 8 / 11 4 7»; нули не ставятся,
    # ЧС (7) и миссия (9) в матрицу НЕ добавляются (в клетках 7 и 9 по одной цифре).
    assert cells(1984, 7, 16) == {1: "11", 4: "4", 6: "6", 7: "7", 8: "8", 9: "9"}
    mx = build_matrix(1984, 7, 16)
    assert mx["grid"] == [["–", "6", "9"], ["–", "–", "8"], ["11", "4", "7"]]


def test_mission_15_07_1985_syutsay_ru():
    # https://syutsay.ru/missiya-syutsay: «1 + 5 + 0 + 7 + 1 + 9 + 8 + 5 = 36 3 + 6 = 9»
    assert mission_number(1985, 7, 15)["chain"] == [36, 9]


def test_trump_syutsay_ru():
    # https://syutsay.ru/articles/pobeda-na-vyborakh-tramp: 14.06.1946 — ЧС 5 (1+4), миссия 4,
    # «2024 год для Трампа находится под энергией Солнца (1)» → личный год 2024 = 1
    r = calculate(BirthInput(1946, 6, 14), target_year=2024)
    assert r["consciousness"]["number"] == 5
    assert r["mission"]["number"] == 4
    assert r["years"]["personal_year"]["number"] == 1 and r["years"]["personal_year"]["planet"] == "Солнце"


def test_consciousness_day_groups_syutsay_ru():
    # https://syutsay.ru/syutsay-chislo-1 … -9: «1, 10, 19, 28», «2, 11, 20, 29», «3, 12, 21, 30»,
    # «4, 13, 22, 31», «5, 14, 23», «6, 15, 24», «7, 16, 25», «8, 17, 26», «9, 18, 27»
    assert CONSCIOUSNESS_DAYS == {1: [1, 10, 19, 28], 2: [2, 11, 20, 29], 3: [3, 12, 21, 30],
                                  4: [4, 13, 22, 31], 5: [5, 14, 23], 6: [6, 15, 24],
                                  7: [7, 16, 25], 8: [8, 17, 26], 9: [9, 18, 27]}
    # «рожден 19-го … 1+9. Итого – 10. Далее … 1 и 0 … 1»; «3+1 = 4»; 22 (Ленин) → 4
    assert consciousness_number(19)["chain"] == [19, 10, 1]
    assert consciousness_number(31)["number"] == 4
    assert consciousness_number(22)["chain"] == [22, 4]


def test_planets_syutsay_ru():
    # https://syutsay.ru/syutsay-chislo-N: Солнце, Луна, Юпитер, Раху, Меркурий, Венера, Кету, Сатурн, Марс
    # (то же — findh.org, nur.kz, таблица А. Ройтблата на wday.ru)
    assert [PLANETS[n] for n in range(1, 10)] == [
        "Солнце", "Луна", "Юпитер", "Раху", "Меркурий", "Венера", "Кету", "Сатурн", "Марс"]


def test_zhanatglobal_official():
    # https://zhanatglobal.com/filosofiya-syucai/: «10.01.2000 года число миссии равно 4 (1+1+2)»;
    # «21 числа, число сознания будет равно 3 (2 + 1)»; «для 2024 года – это число восемь»
    assert mission_number(2000, 1, 10)["number"] == 4
    assert consciousness_number(21)["number"] == 3
    assert universal_year(2024)["number"] == 8


# ---------------------------------------------------------------------------
# Векторы прессы
# ---------------------------------------------------------------------------

def test_tj_ru_vectors():
    # https://t-j.ru/cifrovaya-psihologiya/ : «29-го … 2 и 9. Но 11 не может быть числом сознания … 2»
    assert consciousness_number(29)["chain"] == [29, 11, 2]
    # «рожденному 2 февраля 1977 года … полученным числом 33 — сложить две тройки … 6».
    # ⚠ Опечатка источника: у 02.02.1977 сумма 28 → 10 → 1; сумму 33 даёт 02.07.1977
    # (2 ИЮЛЯ — как в их же инфографике матрицы 02.07.1976). Правило сведения 33 → 6 подтверждено.
    assert mission_number(1977, 2, 2)["chain"] == [28, 10, 1]
    assert mission_number(1977, 7, 2)["chain"] == [33, 6]
    # Инфографика «Пример заполненной матрицы … 2 июля 1976 года»: 1, 2, 6, 77, 9 есть;
    # 3, 4, 5, 8 нет; «линия денег не заполнена»
    mx = build_matrix(1976, 7, 2)
    assert cells(1976, 7, 2) == {1: "1", 2: "2", 6: "6", 7: "77", 9: "9"}
    assert mx["missing"] == [3, 4, 5, 8]
    assert line(mx, "row_147")["status"] == "partial" and line(mx, "row_147")["missing_cells"] == [4]


def test_tj_ru_name_numbers():
    # t-j.ru: «число Елены, Оксаны и Сергея — единица»; таблица букв для Сюцай — латиница,
    # халдейская (https://www.nur.kz/esoterics/interesting/2055342-...): ELENA 19, OKSANA 19, SERGEI 19 → 1
    for name in ("Елена", "Оксана", "Сергей", "SERGEY"):
        assert name_number(name)["number"] == 1, name


def test_letu_ru_vectors():
    # https://www.letu.ru/blog/chto-takoe-praktika-syuczaj-kak-rasschitat-prednaznachenie-i-harakter-po-date-rozhdeniya
    # «15-го числа. 1+5=6», «23-го? 2+3=5», «29-го? 2+9=11, 1+1=2»
    assert [consciousness_number(d)["number"] for d in (15, 23, 29)] == [6, 5, 2]
    # «29.01.2001: 2+9+0+1+2+0+0+1=15, 1+5=6»; «08.07.1995: …=39, 3+9=12, 1+2=3»
    assert mission_number(2001, 1, 29)["chain"] == [15, 6]
    assert mission_number(1995, 7, 8)["chain"] == [39, 12, 3]
    # «11.01.2015 … 1,1,0,1,2,0,1,5»
    assert build_matrix(2015, 1, 11)["digits"] == [1, 1, 0, 1, 2, 0, 1, 5]


def test_horo_mail_vectors():
    # https://horo.mail.ru/article/9040-chto-takoe-syutsaj/ : 29.01.2001 → миссия 6;
    # 11.01.2015: ЧС 2, миссия 2, «в матрице этой даты есть цифры 1, 2 и 5»
    assert mission_number(2001, 1, 29)["number"] == 6
    r = calculate(BirthInput(2015, 1, 11), target_year=2026)
    assert r["consciousness"]["number"] == 2 and r["mission"]["number"] == 2
    assert r["matrix"]["present"] == [1, 2, 5]


def test_other_press_mission_vectors():
    # https://www.nur.kz/esoterics/interesting/2051360-... : 03.09.1978 «=37 … 3+7=10, 1+0=1»; 12 → 3
    assert mission_number(1978, 9, 3)["chain"] == [37, 10, 1]
    assert consciousness_number(12)["number"] == 3
    # https://msk1.ru/text/family/2024/04/29/72183623/ : 27.10.1990 «=29=2+9=11=1+1=2»
    assert mission_number(1990, 10, 27)["chain"] == [29, 11, 2]
    # https://www.wday.ru/stil-zhizny/motivatsiya/nauka-syucai-kak-uznat-vse-o-svoem-soznanii-i-missii-po-date-rozhdeniya/
    # 10.10.2000 → миссия 4; «28 = 2+8 = 10, ноль не считается» → 1
    assert mission_number(2000, 10, 10)["number"] == 4
    assert consciousness_number(28)["number"] == 1
    # https://www.marieclaire.ru/psychology/nauka-syutsay-chto-takoe-psihologiya-tsifr-i-kak-ona-mojet-izmenit-vashu-jizn/
    # 10 → 1+0 = 1; 10.01.2000 → 4
    assert consciousness_number(10)["number"] == 1 and mission_number(2000, 1, 10)["number"] == 4
    # https://diapazon.kz/news/113421-magiya-chisel-syucai-chto-taitsya-v-date-rozhdeniya : 12 → 3;
    # 12.10.1990 «=23=2+3=5»; 2020 год — «цифра 4, планета Раху»; «2022 год – это число 6»
    assert mission_number(1990, 10, 12)["chain"] == [23, 5]
    assert universal_year(2020)["number"] == 4 and universal_year(2020)["planet"] == "Раху"
    assert universal_year(2022)["number"] == 6
    # https://thegirl.ru/articles/nauka-syucai-cifry-podskazhut-kak-stat-eshe-schastlivee-i-uspeshnee/ :
    # 1 октября 1992 «1+1+1+9+9+2 … 23 … 5»
    assert mission_number(1992, 10, 1)["chain"] == [23, 5]
    # https://yakutia-daily.ru/praktika-syuczaj-kak-rasschitat-prednaznachenie-po-date-rozhdeniya/ :
    # «10.10.2010 = 1+1+3 = 5»
    assert mission_number(2010, 10, 10)["number"] == 5
    # https://gems-brokers.ru/numerologiya-i-kamni/czifrovaya-psixologiya-syuczaj/ :
    # 25.06.1990 — ЧС 7, миссия 32 → 5; 11.03.1985 — ЧС 2
    assert consciousness_number(25)["number"] == 7
    assert mission_number(1990, 6, 25)["chain"] == [32, 5]
    assert consciousness_number(11)["number"] == 2


def test_findh_calculator_vector():
    # https://findh.org/5155-suitsai.html (пример на странице): 31.05.2001 —
    # «31 = 3 + 1 = 4», Раху, «Революционер»; миссия «= 12 = 1 + 2 = 3»; «Финансовый код = 4533»
    r = calculate(BirthInput(2001, 5, 31), target_year=2026)
    assert r["consciousness"]["number"] == 4 and r["consciousness"]["group"] == "Революционер"
    assert r["mission"]["chain"] == [12, 3]
    assert financial_code_findh(2001, 5, 31)["code"] == "4533"


def test_personal_year_formula_vc_ru():
    # https://vc.ru/life/1656201-kak-chisla-vliyayut-na-nashu-sudbu :
    # «нужно сложить цифры дня рождения, месяца и сумму текущего года … к однозначному числу»
    assert personal_year(14, 6, 2024)["sum"] == 19 and personal_year(14, 6, 2024)["number"] == 1
    # цикл: личный год растёт на 1 каждый календарный год (по модулю 9)
    seq = [personal_year(15, 5, y)["number"] for y in range(2026, 2035)]
    assert seq == [3, 4, 5, 6, 7, 8, 9, 1, 2]


# ---------------------------------------------------------------------------
# Совместимость (syutsay.ru/syutsay-chislo-N)
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("a,b,rel,suffers", [
    (1, 2, "good", None),        # chislo-2: «Для них отлично подходят люди-единицы»
    (3, 9, "good", None),        # chislo-3 + chislo-9: «прекрасного партнера и друга»
    (4, 7, "good", None),        # chislo-4 + chislo-7
    (6, 8, "good", None),        # chislo-6 + chislo-8
    (9, 9, "good", None),        # chislo-9: «непременно нужно быть вместе»
    (2, 4, "difficult", 2),      # chislo-4: «Нежелательно жениться на … 2, пострадает 2-ка»
    (4, 9, "difficult", 4),      # chislo-4: «с … 9, будет ущемлена сама четверка»
    (3, 5, "difficult", 3),      # chislo-5: «Не очень удачным выбором будет … 3, пострадает тройка»
    (3, 6, "difficult", 6),      # chislo-6: «Тройки могут уничтожить шестерок энергетически»
    (1, 9, "difficult", None),   # chislo-9
    (6, 9, "mixed", None),       # chislo-6: страсть, но ссоры
    (4, 5, "not_described", None),
])
def test_compatibility(a, b, rel, suffers):
    c = compatibility(a, b)
    assert c["relation"] == rel and c["suffers"] == suffers
    assert compatibility(b, a)["relation"] == rel          # таблица симметрична по отношению


# ---------------------------------------------------------------------------
# Инварианты и граничные случаи
# ---------------------------------------------------------------------------

def test_invariants_all_dates_1900_2030():
    from datetime import date, timedelta
    d = date(1900, 1, 1)
    while d <= date(2030, 12, 31):
        mx = build_matrix(d.year, d.month, d.day)
        counts = {int(k): v for k, v in mx["counts"].items()}
        # сумма клеток + нули = 8 цифр
        assert sum(counts.values()) + mx["zeros"] == 8
        # миссия = цифровой корень суммы клеток матрицы
        s = sum(n * c for n, c in counts.items())
        assert mission_number(d.year, d.month, d.day)["number"] == (s - 1) % 9 + 1
        d += timedelta(days=37)


def test_matches_vedic_module_12():
    # Формулы ЧС и миссии совпадают с Мулянком и Бхагьянком модуля 12 (без мастер-чисел),
    # число имени — с халдейским Намянком для одного слова. Проверка на выборке дат.
    tl = pytest.importorskip("calculators.tarot_loshu")
    from datetime import date, timedelta
    d = date(1930, 1, 1)
    while d <= date(2030, 12, 31):
        v = tl.vedic_numbers(d.year, d.month, d.day)
        assert consciousness_number(d.day)["number"] == v["moolank"]["number"]
        assert mission_number(d.year, d.month, d.day)["number"] == v["bhagyank"]["number"]
        d += timedelta(days=101)
    for nm in ("ANNA", "DMITRII", "MARIIA", "ALBERT", "ELENA"):
        assert name_number(nm)["sum"] == tl.chaldean_name_number(nm)["compound"]


def test_given_name_parsing():
    assert extract_given_name("Иванова Анна Сергеевна")[0] == "Анна"
    assert extract_given_name("Анна Сергеевна Иванова")[0] == "Анна"
    assert extract_given_name("Эйнштейн Альберт / Albert Einstein")[0] == "Albert"
    assert extract_given_name("Петров Дмитрий")[0] == "Дмитрий"
    assert extract_given_name("Мария")[0] == "Мария"
    # Два слова «Имя Фамилия»: имя на -ина/-ин или короткое не принимается за фамилию
    # (ошибка, найденная проверкой: «Марина Иванова» → «Иванова», «Лев Толстой» → «Толстой»).
    for full, given in [("Марина Иванова", "Марина"), ("Иванова Марина", "Марина"),
                        ("Екатерина Смирнова", "Екатерина"), ("Константин Петров", "Константин"),
                        ("Лев Толстой", "Лев"), ("Толстой Лев", "Лев"),
                        ("Сергей Есенин", "Сергей"), ("Есенин Сергей", "Сергей")]:
        assert extract_given_name(full)[0] == given, full


def test_heuristic_name_parse_warns():
    r = calculate(BirthInput(1990, 5, 15, name="Марина Иванова"), target_year=2026)
    assert r["name"]["name"] == "Марина"
    assert any("эвристик" in w for w in r["warnings"])
    r = calculate(T1, target_year=2026)                     # ФИО с отчеством — без предупреждения
    assert not any("эвристик" in w for w in r["warnings"])


def test_invalid_date():
    with pytest.raises(ValueError):
        calculate(BirthInput(2003, 2, 29))


def test_no_name_no_partner():
    r = calculate(BirthInput(2000, 1, 10), target_year=2026, financial_code=False)
    assert "name" not in r and "compatibility" not in r and "financial_code_findh" not in r
    assert r["consciousness"]["zero_in_day"] and r["consciousness"]["day_note"]
    assert len(r["years"]["cycle"]) == 9


# ---------------------------------------------------------------------------
# Официальный календарь школы: месяцы, дни, граница года, сведение 11/22/33
# (повторная проверка, приоритет 1)
# ---------------------------------------------------------------------------

# Образец «Персонального бизнес календаря 2026» на zhanatglobal.com (общие картинки всех товаров «2026 — год N»,
# напр. https://zhanatglobal.com/product/kalendar-2025-1/):
#   https://zhanatglobal.com/wp-content/uploads/2024/12/webpconverter-3-1-scaled.webp — «ЯНВАРЬ», круг «2»,
#   «Покровитель месяца — Луна»; https://zhanatglobal.com/wp-content/uploads/2024/12/webpconverter-4-1-scaled.webp —
#   «ФЕВРАЛЬ», круг «3», «Планета месяца — Юпитер»; https://zhanatglobal.com/wp-content/uploads/2024/12/
#   webpconverter-2-1-scaled.webp — «Глобальный год 2026 - 1». В каждой клетке «общий день» и «личный день»
#   (в образце они совпадают). Числа переписаны с картинок:
OFFICIAL_JAN_2026 = [3, 4, 5, 6, 7, 8, 9, 1, 2, 3, 4, 5, 6, 7, 8, 9, 1, 2, 3, 4, 5, 6, 7, 8, 9, 1, 2, 3, 4, 5, 6]
OFFICIAL_FEB_2026 = [4, 5, 6, 7, 8, 9, 1, 2, 3, 4, 5, 6, 7, 8, 9, 1, 2, 3, 4, 5, 6, 7, 8, 9, 1, 2, 3, 4]
# Цвета клеток (легенда «Обозначения»): зелёный «успех через анализ», бирюзовый «успех через любовь и комфорт»,
# красный «обнуление».
OFFICIAL_COLORS_2026 = {
    1: {"успех через анализ": [1, 19, 28], "успех через любовь и комфорт": [4, 13, 22, 31], "обнуление": [10, 20, 30]},
    2: {"успех через анализ": [9, 18, 27], "успех через любовь и комфорт": [3, 12, 21], "обнуление": [10, 20]},
}


def test_official_calendar_universal_months_and_days_2026():
    from datetime import date
    assert universal_year(2026)["number"] == 1                       # «Глобальный год 2026 - 1»
    assert universal_month(2026, 1)["number"] == 2 and PLANETS[2] == "Луна"
    assert universal_month(2026, 2)["number"] == 3 and PLANETS[3] == "Юпитер"
    for month, expected in ((1, OFFICIAL_JAN_2026), (2, OFFICIAL_FEB_2026)):
        got = [calendar_day(15, 5, date(2026, month, dd))["universal_day"]["number"] for dd in range(1, len(expected) + 1)]
        assert got == expected
        for label, days in OFFICIAL_COLORS_2026[month].items():
            for dd in days:
                assert calendar_day(15, 5, date(2026, month, dd))["universal_day"]["highlight"] == label
        coloured = {dd for days in OFFICIAL_COLORS_2026[month].values() for dd in days}
        for dd in set(range(1, len(expected) + 1)) - coloured:
            assert calendar_day(15, 5, date(2026, month, dd))["universal_day"]["highlight"] is None


def test_official_calendar_master_numbers_reduced():
    # В том же образце суммы 11, 22 и 33 сведены к 2, 4 и 6 (мастер-чисел нет):
    # 09.01: 2 + 9 = 11 → «2»; 20.01: 2 + 20 = 22 → «4»; 31.01: 2 + 31 = 33 → «6»; 08.02: 3 + 8 = 11 → «2»;
    # 19.02: 3 + 19 = 22 → «4».
    from datetime import date
    for (mm, dd), (chain, n) in {(1, 9): ([11, 2], 2), (1, 20): ([22, 4], 4), (1, 31): ([33, 6], 6),
                                 (2, 8): ([11, 2], 2), (2, 19): ([22, 4], 4)}.items():
        u = calendar_day(15, 5, date(2026, mm, dd))["universal_day"]
        official = (OFFICIAL_JAN_2026 if mm == 1 else OFFICIAL_FEB_2026)[dd - 1]
        assert u["chain"] == chain and u["number"] == n == official


def test_personal_month_day_and_year_boundary():
    from datetime import date
    # Родившийся 04.05 имеет личный 2026 = 0+4+0+5+2+0+2+6 = 19 → 1 = общему году. Для него личные числа
    # совпадают с общими — ровно как в образце календаря (строки «общий день» и «личный день» одинаковы).
    assert personal_year(4, 5, 2026)["number"] == 1
    for mm, expected in ((1, OFFICIAL_JAN_2026), (2, OFFICIAL_FEB_2026)):
        assert personal_month(4, 5, 2026, mm)["number"] == universal_month(2026, mm)["number"]
        assert [calendar_day(4, 5, date(2026, mm, dd))["personal_day"]["number"]
                for dd in range(1, len(expected) + 1)] == expected
    # T1 (15.05): личный 2026 = 3 → личный январь = 3 + 1 = 4, июнь = 3 + 6 = 9, декабрь = 3 + 12 = 15 → 6.
    r = calculate(T1, target_date="2026-01-09")
    assert r["years"]["target_year"] == 2026 and r["years"]["personal_year"]["number"] == 3
    assert [x["personal_month"] for x in r["years"]["months"]] == [4, 5, 6, 7, 8, 9, 1, 2, 3, 4, 5, 6]
    assert [x["universal_month"] for x in r["years"]["months"]] == [2, 3, 4, 5, 6, 7, 8, 9, 1, 2, 3, 4]
    assert r["day"]["universal_day"]["number"] == 2 and r["day"]["personal_day"]["number"] == 4   # 4 + 9 = 13 → 4
    # Граница личного года — 1 января (календарь «2026 — год N» начинается с января): для T1 (день рождения
    # 15 мая) январь 2026 считается уже от личного года 2026, а не 2025.
    assert r["day"]["personal_month"] == personal_month(15, 5, 2026, 1)["number"] == 4
    assert personal_year(15, 5, 2025)["number"] == 2
    assert r["years"]["boundary"].startswith("1 января")
    assert "личные месяц и день" not in " ".join(r["not_computed"])
    assert r["years"]["personal_year"]["theme"] == YEAR_THEMES[3] == "систематизация и управление"
    # 10/20/30 — «дни обнуления» (zhanatglobal.com, «Бизнес календарь — одностраничник успешных дней»:
    # «10, 20 и 30 число каждого месяца — дни обнуления»)
    z = calculate(T1, target_date="20.02.2026")["day"]
    assert z["zeroing_day"] is True and z["personal_day"]["highlight"] == "обнуление"
    assert "day" not in calculate(T1, target_year=2026)


def test_year_themes_official_covers():
    # Обложки «Персональный бизнес календарь 2026 — год N» (zhanatglobal.com/product/…, картинки webpconverter-god-N):
    # «в ваш личный год построения стратегии / построения отношений / систематизации и управления / целеполагания /
    # масштабирования / комфорта и творчества / дисциплины и внедрения целей / упорного труда и контроля процессов /
    # генерации идей и здоровья»
    assert [YEAR_THEMES[n] for n in range(1, 10)] == [
        "построение стратегии", "построение отношений", "систематизация и управление", "целеполагание",
        "масштабирование", "комфорт и творчество", "дисциплина и внедрение целей",
        "упорный труд и контроль процессов", "генерация идей и здоровье"]


def test_row_369_note_official_blog():
    # https://zhanatglobal.com/kak-czifrovaya-nauka-syuczaj-menyaet-zhizn/ (А. Шаталин, 03.11.1961):
    # «Моя линия цифр 3-6-9 помогала мне анализировать ситуацию и видеть окончание любого процесса.
    # Четыре единицы давали способность самостоятельно действовать.»
    mx = build_matrix(1961, 11, 3)
    assert mx["counts"]["1"] == 4
    row = line(mx, "row_369")
    assert row["status"] == "full" and "анализировать ситуацию" in row["note"] and row["name"] is None
    assert line(mx, "row_147")["name"] == "линия денег"
