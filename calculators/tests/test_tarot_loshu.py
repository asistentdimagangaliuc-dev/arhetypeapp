"""Тесты модуля 12: арканы Таро по дате рождения, сетка Ло Шу, ведическая нумерология.

Эталоны T1–T4 посчитаны вручную по алгоритму из knowledge-base/12-tarot-loshu-vedic.md;
внешние векторы — из опубликованных источников (URL в комментариях у каждого теста).
"""
from __future__ import annotations

import json

import pytest

from calculators.common.time import BirthInput
from calculators.tarot_loshu import (
    calculate,
    chaldean_name_number,
    greer_birth_cards,
    kua_number,
    loshu_grid,
    natural_relation,
    relation_table,
    ru_arcana,
    tarot_school_birth_cards,
    vedic_numbers,
    year_card,
)

T1 = BirthInput(1990, 5, 15, 14, 30, place="Москва", gender="female", name="Иванова Анна Сергеевна")
T2 = BirthInput(1984, 2, 4, 23, 30, place="Москва", gender="male", name="Петров Дмитрий Олегович")
T3 = BirthInput(2004, 2, 29, 8, 15, place="Санкт-Петербург", gender="female",
                name="Смирнова Мария Александровна")
T4 = BirthInput(1879, 3, 14, 11, 30, tz="LMT", lat=48.4011, lon=9.9876, gender="male", name="Albert Einstein")


def nums(cards: list[dict]) -> list[int]:
    return [c["number"] for c in cards]


def counts(grid: dict) -> dict[int, int]:
    return {int(k): v for k, v in grid["counts"].items() if v}


# ---------------------------------------------------------------------------
# T1–T4: полный расчёт
# ---------------------------------------------------------------------------

def test_t1_full():
    r = calculate(T1, year=2026)
    bc = r["tarot"]["birth_cards"]
    # 5 + 15 + 1990 = 2010 → 3: «одиночная тройка» 3-3, Скрытый фактор 12 и 21
    assert bc["total"] == 2010 and bc["pattern"] == "3-3"
    assert bc["personality"]["number"] == 3 and bc["soul"]["number"] == 3
    assert nums(bc["hidden_factor"]) == [12, 21]
    # Tarot School: 5 + 15 + 19 + 90 = 129 → 12 + 9 = 21 → 21/3 (расходится с Грир!)
    assert nums(r["tarot"]["birth_cards_tarot_school"]["birth_cards"]) == [21, 3]
    # Год 2026: 5 + 15 + 2026 = 2046 → 12 (совпадает со Скрытым фактором)
    assert r["tarot"]["year_card"]["card"]["number"] == 12
    assert any("hidden_factor" in f for f in r["tarot"]["year_card"]["matches_birth_cards"])
    ru = r["tarot"]["ru_arcana"]
    assert ru["day_arcana"]["card"]["number"] == 15
    assert ru["date_digits_minus22"]["card"]["number"] == 8      # 30 − 22
    assert ru["date_digits_reduce"]["card"]["number"] == 3       # 3 + 0
    assert ru["day_month_year"]["card"]["number"] == 12          # 15 + 5 + 19 = 39 → 12
    # Ло Шу: 1,5,5,1,9,9 → 1×2, 5×2, 9×2; стрела 9-5-1, пустые 4-3-8 и 2-7-6
    lo = r["loshu"]
    assert counts(lo) == {1: 2, 5: 2, 9: 2}
    assert lo["missing"] == [2, 3, 4, 6, 7, 8]
    assert [a["cells"] for a in lo["arrows_of_strength"]] == [[9, 5, 1]]
    assert [a["cells"] for a in lo["arrows_of_weakness"]] == [[4, 3, 8], [2, 7, 6]]
    assert lo["alternative"]["numbers_placed"] == [1, 5, 5, 1, 9, 9, 6, 3]
    # Веда: Мулянк 6 (Венера), Бхагьянк 30 → 3 (Юпитер); Куа ж 1990 → 8
    v = r["vedic"]
    assert v["moolank"]["number"] == 6 and v["moolank"]["planet"] == "venus"
    assert v["bhagyank"]["number"] == 3 and v["bhagyank"]["planet"] == "jupiter"
    assert v["driver_conductor"]["driver_to_conductor"] == "neutral"   # Венера → Юпитер
    assert v["driver_conductor"]["conductor_to_driver"] == "enemy"     # Юпитер → Венера
    assert lo["kua"]["number"] == 8 and lo["kua"]["year_used"] == 1990
    # Имя: IVANOVA (27) + ANNA (12) + SERGEEVNA (35) = 74 → 2
    assert v["name_number"]["latin"] == "IVANOVA ANNA SERGEEVNA"
    assert v["name_number"]["compound"] == 74 and v["name_number"]["number"] == 2
    assert v["name_number"]["compound_cheiro"] == 20                 # 9 + 3 + 8 (правило Хейро)
    json.dumps(r, ensure_ascii=False)  # JSON-сериализуемость


def test_t2_full_19_triple_and_lichun_day():
    r = calculate(T2, year=2026)
    bc = r["tarot"]["birth_cards"]
    # 2 + 4 + 1984 = 1990 → 19: тройка 19-10-1, Учитель = 10 (таблица Грир, с. 32)
    assert bc["total"] == 1990 and bc["pattern"] == "19-10-1"
    assert nums(bc["birth_cards"]) == [19, 10, 1]
    assert bc["personality"]["number"] == 19 and bc["soul"]["number"] == 1
    assert nums(bc["hidden_factor"]) == [10]
    # Tarot School: 2 + 4 + 19 + 84 = 109 → 10 + 9 = 19 → тоже тройка
    assert nums(r["tarot"]["birth_cards_tarot_school"]["birth_cards"]) == [19, 10, 1]
    assert r["tarot"]["year_card"]["card"]["number"] == 7          # 2032 → 7
    ru = r["tarot"]["ru_arcana"]
    assert ru["day_arcana"]["card"]["number"] == 4
    assert ru["date_digits_minus22"]["card"]["number"] == 6       # 28 − 22
    assert ru["date_digits_reduce"]["card"]["number"] == 10       # 2 + 8
    lo = r["loshu"]
    assert counts(lo) == {1: 1, 2: 1, 4: 2, 8: 1, 9: 1}
    assert [a["cells"] for a in lo["arrows_of_strength"]] == [[4, 9, 2]]
    assert [a["cells"] for a in lo["arrows_of_weakness"]] == [[3, 5, 7]]
    v = r["vedic"]
    assert v["moolank"]["number"] == 4 and v["moolank"]["planet"] == "rahu"
    assert v["bhagyank"]["reduction"] == [28, 10, 1] and v["bhagyank"]["number"] == 1
    # Рождение в 23:30 MSK — после Личунь (≈18:19 MSK) → год 1984, мужской Куа 7
    assert lo["kua"]["year_used"] == 1984 and lo["kua"]["number"] == 7
    assert v["name_number"]["latin"] == "PETROV DMITRII OLEGOVICH"
    assert v["name_number"]["compound"] == 89 and v["name_number"]["number"] == 8
    assert v["name_number"]["compound_cheiro"] == 17                 # 5 + 8 + 4


def test_t2_before_lichun_changes_kua_only():
    """Тот же день, но 10:00 MSK — до Личунь: для Куа берётся 1983 г. (м: 8)."""
    b = BirthInput(1984, 2, 4, 10, 0, place="Москва", gender="male")
    r = calculate(b, year=2026)
    assert r["loshu"]["kua"]["year_used"] == 1983 and r["loshu"]["kua"]["number"] == 8
    # граница 1 января (как в большинстве индийских калькуляторов) — 1984 → 7
    r2 = calculate(b, year=2026, kua_boundary="jan1")
    assert r2["loshu"]["kua"]["number"] == 7
    # без времени — сравнение по ДАТЕ, день Личуня относится к новому году (как в модуле 03,
    # calculators/ninestar.py, boundary_precision='auto'): 1984 → 7, плюс предупреждение
    r3 = calculate(BirthInput(1984, 2, 4, gender="male"), year=2026)
    assert any("Личунь" in w for w in r3["warnings"])
    assert r3["loshu"]["kua"]["year_used"] == 1984 and r3["loshu"]["kua"]["number"] == 7
    r4 = calculate(BirthInput(1984, 2, 4, place="Москва", gender="male"), year=2026)
    assert r4["loshu"]["kua"]["year_used"] == 1984
    # накануне Личуня без времени — ещё 1983 г.
    r5 = calculate(BirthInput(1984, 2, 3, gender="male"), year=2026)
    assert r5["loshu"]["kua"]["year_used"] == 1983 and r5["loshu"]["kua"]["number"] == 8


def test_kua_agrees_with_ninestar_module():
    """Куа (модуль 12) = Гуа (модуль 03) при одинаковой границе Личунь — с временем и без."""
    from calculators import ninestar
    cases = [T1, T2, T3, T4,
             BirthInput(1984, 2, 4, 10, 0, place="Москва", gender="male"),
             BirthInput(1984, 2, 4, gender="female"),
             BirthInput(1984, 2, 4, place="Москва", gender="male"),
             BirthInput(2004, 2, 4, 20, 0, place="Москва", gender="female"),
             BirthInput(1990, 2, 3, gender="male")]
    for b in cases:
        g = ninestar.calculate(b)["gua"]
        k = calculate(b, year=2026)["loshu"]["kua"]
        assert (k["year_used"], k["number"]) == (g["year_used"], g["number"]), (b, k, g)


def test_t3_full_feb29():
    r = calculate(T3, year=2026)
    bc = r["tarot"]["birth_cards"]
    # 2 + 29 + 2004 = 2035 → 10 → 10/1, Скрытый фактор 19
    assert bc["total"] == 2035 and bc["pattern"] == "10-1"
    assert nums(bc["hidden_factor"]) == [19]
    # Tarot School: 2 + 29 + 20 + 04 = 55 → 10 → 10/1
    assert nums(r["tarot"]["birth_cards_tarot_school"]["birth_cards"]) == [10, 1]
    ru = r["tarot"]["ru_arcana"]
    assert ru["day_arcana"]["card"]["number"] == 7               # 29 − 22
    assert ru["date_digits_minus22"]["card"]["number"] == 19
    lo = r["loshu"]
    assert counts(lo) == {2: 3, 4: 1, 9: 1}
    assert [a["cells"] for a in lo["arrows_of_weakness"]] == [[3, 5, 7], [8, 1, 6]]
    v = r["vedic"]
    assert v["moolank"]["reduction"] == [29, 11, 2] and v["moolank"]["number"] == 2
    assert v["bhagyank"]["number"] == 1
    assert v["driver_conductor"]["driver_to_conductor"] == "friend"   # Луна ↔ Солнце
    assert lo["kua"]["number"] == 1                                   # ж, 2004: 6 + 4 = 10 → 1
    assert v["name_number"]["compound"] == 84 and v["name_number"]["number"] == 3
    assert v["name_number"]["compound_cheiro"] == 12                 # 2 + 1 + 9
    # Карта года в режиме «от дня рождения»: 28.02.2026 — день рождения ещё не наступил → 2025
    r2 = calculate(T3, year_card_mode="birthday", on_date="2026-02-28")
    assert r2["tarot"]["year_card"]["year"] == 2025
    r3 = calculate(T3, year_card_mode="birthday", on_date="2026-03-01")
    assert r3["tarot"]["year_card"]["year"] == 2026


def test_t4_full_einstein():
    r = calculate(T4, year=2026)
    bc = r["tarot"]["birth_cards"]
    # 3 + 14 + 1879 = 1896 → 24 → 6: одиночная 6-6 (Влюблённые), Скрытый фактор 15 (Дьявол)
    assert bc["reduction"] == [1896, 24, 6] and bc["pattern"] == "6-6"
    assert nums(bc["hidden_factor"]) == [15]
    # Tarot School: 3 + 14 + 18 + 79 = 114 → 11 + 4 = 15 → 15/6
    assert nums(r["tarot"]["birth_cards_tarot_school"]["birth_cards"]) == [15, 6]
    ru = r["tarot"]["ru_arcana"]
    assert ru["date_digits_minus22"]["card"]["number"] == 11      # 33 − 22
    assert ru["date_digits_reduce"]["card"]["number"] == 6
    lo = r["loshu"]
    assert counts(lo) == {1: 2, 3: 1, 4: 1, 7: 1, 8: 1, 9: 1}
    assert lo["missing"] == [2, 5, 6]
    assert [a["cells"] for a in lo["arrows_of_strength"]] == [[4, 3, 8]]
    v = r["vedic"]
    assert v["moolank"]["number"] == 5 and v["bhagyank"]["number"] == 6
    assert lo["kua"]["number"] == 4 and lo["kua"]["year_used"] == 1879
    # ALBERT (17) + EINSTEIN (29) = 46 → 1 (халдейская таблица); по Хейро 8 + 2 = 10 → 1
    assert v["name_number"]["compound"] == 46 and v["name_number"]["number"] == 1
    assert v["name_number"]["compound_cheiro"] == 10
    assert any("1900" in w for w in r["warnings"])


# ---------------------------------------------------------------------------
# A. Таро — внешние векторы
# ---------------------------------------------------------------------------

def test_greer_primary_table_hidden_factors():
    """Таблица «Patterns of Personal Destiny», Greer, Tarot for Your Self, с. 32
    (скан в раздатке Joy Vernon: https://joyvernon.com/images/Tarot%20Birth%20Cards.pdf)."""
    from calculators.tarot_loshu import greer_from_total
    expected = {  # сумма ММ+ДД+ГГГГ (подобрана) → (паттерн, скрытый фактор)
        1000: ("1-1", [10, 19]), 2017: ("10-1", [19]), 1990: ("19-10-1", [10]),
        2000: ("2-2", [11, 20]), 2009: ("11-2", [20]), 1991: ("20-2", [11]),
        2010: ("3-3", [12, 21]), 2019: ("12-3", [21]), 1992: ("21-3", [12]),
        2011: ("4-4", [13, 22]), 2029: ("13-4", [22]), 1984: ("22-4", [13]),
        2003: ("5-5", [14]), 1904: ("14-5", []), 2004: ("6-6", [15]), 1905: ("15-6", []),
        2005: ("7-7", [16]), 1906: ("16-7", []), 2006: ("8-8", [17]), 1907: ("17-8", []),
        2007: ("9-9", [18]), 1980: ("18-9", []),
        # суммы цифр > 22 сводятся повторно: 1994 → 23 → 5, 1997 → 26 → 8
        1994: ("5-5", [14]), 1997: ("8-8", [17]),
    }
    for total, (pattern, hidden) in expected.items():
        r = greer_from_total(total)
        assert r["pattern"] == pattern, total
        assert nums(r["hidden_factor"]) == hidden, total


def test_greer_external_vectors():
    # https://angelorum.co/topics/divination/how-to-calculate-your-personality-sou/
    # 13 апреля 1975: 13 + 4 + 1975 = 1992 → 21 (Мир) / 3 (Императрица); Скрытый фактор 12
    # (то же — musingmystical.com/tag/birth-card: 21, 3, Hidden Factor 12)
    r = greer_birth_cards(1975, 4, 13)
    assert r["total"] == 1992 and r["personality"]["number"] == 21 and r["soul"]["number"] == 3
    assert nums(r["hidden_factor"]) == [12]
    assert r["personality"]["name_en"] == "The World" and r["soul"]["name_en"] == "The Empress"
    # там же, комментарий: 19 января 2000 → 1 + 19 + 2000 = 2020 → 4 (Император)
    r = greer_birth_cards(2000, 1, 19)
    assert r["total"] == 2020 and r["pattern"] == "4-4"
    # https://marykgreer.com/2011/08/17/who-are-you-in-the-tarot/ (ответ Грир читательнице):
    # 24 октября 1966 → «Single 2 (2000)», в 2011 г. — «11 Year»
    r = greer_birth_cards(1966, 10, 24)
    assert r["total"] == 2000 and r["pattern"] == "2-2"
    assert year_card(10, 24, 2011)["card"]["number"] == 11
    # https://www.findyourfate.com/tarot/birth-personality-card.php
    # 14 июня 1977: 14 + 6 + 1977 = 1997 → 26 → 8 (Strength)
    r = greer_birth_cards(1977, 6, 14)
    assert r["reduction"] == [1997, 26, 8] and r["personality"]["name_en"] == "Strength"


def test_tarot_school_external_vectors():
    # https://biddytarot.com/podcast/btp86-birth-cards-part-1/
    r = tarot_school_birth_cards(1969, 4, 7)       # 4 + 7 + 19 + 69 = 99 → 18 / 9
    assert r["reduction"] == [99, 18] and nums(r["birth_cards"]) == [18, 9]
    r = tarot_school_birth_cards(1979, 4, 27)      # 4 + 27 + 19 + 79 = 129 → 12 + 9 = 21 / 3
    assert r["reduction"] == [129, 21] and nums(r["birth_cards"]) == [21, 3]
    # https://labyrinthos.co/blogs/learn-tarot-with-labyrinthos-academy/how-to-calculate-your-tarot-birth-card-plus-short-birth-card-meanings-infographic
    r = tarot_school_birth_cards(1989, 7, 20)      # 07 + 20 + 19 + 89 = 135 → 13 + 5 = 18 / 9
    assert r["reduction"] == [135, 18] and nums(r["birth_cards"]) == [18, 9]
    r = tarot_school_birth_cards(2000, 11, 22)     # 11 + 22 + 20 + 00 = 53 → 8, вторая 17
    assert r["reduction"] == [53, 8] and nums(r["birth_cards"]) == [8, 17]
    # https://www.aeclectic.net/tarot/blog/numerology-tarot-birth-cards.shtml
    r = tarot_school_birth_cards(1948, 12, 9)      # 12 + 09 + 19 + 48 = 88 → 16 / 7
    assert nums(r["birth_cards"]) == [16, 7]
    r = tarot_school_birth_cards(1948, 12, 29)     # 108 → 9 «с подразумеваемой 18»
    assert sorted(nums(r["birth_cards"])) == [9, 18]
    # https://tools.devcomma.com/en/calculators/arcana — 06 + 11 + 19 + 92 = 128 → 12 + 8 = 20 / 2
    r = tarot_school_birth_cards(1992, 6, 11)
    assert r["reduction"] == [128, 20] and nums(r["birth_cards"]) == [20, 2]


def test_tarot_school_primary_tarot_tips():
    # Первоисточник: R. A. & W. Amberstone, «Tarot Tips» (Llewellyn, 2003), Tip #69, с. 128–130, и Tip #60
    # (ответ Georgia), https://archive.org/details/tarot_202304 (файл «… - Tarot Tips_djvu.txt»).
    r = tarot_school_birth_cards(1941, 12, 2)      # «12 + 02 + 19 + 41 = 74 … 7 + 4 = 11 … Justice … 2»
    assert r["reduction"] == [74, 11] and nums(r["birth_cards"]) == [11, 2]
    r = tarot_school_birth_cards(1969, 8, 20)      # «08 + 20 + 19 + 69 = 116 … 11 + 6 = 17 … Star … 8»
    assert r["reduction"] == [116, 17] and nums(r["birth_cards"]) == [17, 8]
    r = tarot_school_birth_cards(1931, 1, 19)      # «1+19+19+31=70=7 … 7 is a direct reduction of 16»
    assert r["reduction"] == [70, 7] and nums(r["birth_cards"]) == [7, 16]
    # Однозначная сумма → только вторая карта n + 9 («the higher octave is implied»); для 2 и 3 — 11 и 12
    # («the first of these numbers is the one that works»); третьей карты n + 18 нет.
    r = tarot_school_birth_cards(1912, 1, 8)       # 1 + 8 + 19 + 12 = 40 → 4 → Император / Смерть
    assert r["reduction"] == [40, 4] and nums(r["birth_cards"]) == [4, 13]
    r = tarot_school_birth_cards(1910, 1, 19)      # 1 + 19 + 19 + 10 = 49 → 13 → 13 / 4 (двузначная)
    assert nums(r["birth_cards"]) == [13, 4]
    assert not any("⚠" in n for n in tarot_school_birth_cards(1912, 1, 8)["notes"])


def test_arrien_primary_tarot_handbook():
    # A. Arrien, «The Tarot Handbook» (1987), полнотекстовый поиск archive.org по
    # https://archive.org/details/tarothandbookpra00arri :
    # «month 12 day +24 36 year 1940 1976 = 23» → однозначная (5) — Personality и Soul;
    # «September 9, 1956 … 18 … 1956 1974 = 21» → 21 / 3; «If your final total equals 28, it will reduce
    # to 10»; «If your final total equals 22, it reduces to 4 and also become 0»;
    # Growth Symbol: «month 12 day +24 36 year 1982 2018 = 11 Number 11, Strength/Lust»;
    # «The growth year is from birthday to birthday, not the calendar year»;
    # «Emperor years (where your birthday and the current year add up to the number 22 or 4)».
    r = calculate(BirthInput(1940, 12, 24), tarot_method="arrien", year=1982)
    bc = r["tarot"]["birth_cards"]
    assert bc["method"] == "arrien" and bc["reduction"] == [1976, 23, 5] and bc["pattern"] == "5-5"
    yc = r["tarot"]["year_card"]
    assert yc["reduction"] == [2018, 11] and yc["card"]["name_en"] == "Lust" and yc["mode"] == "birthday"
    r = calculate(BirthInput(1956, 9, 9), tarot_method="arrien", year=2026)
    assert nums(r["tarot"]["birth_cards"]["birth_cards"]) == [21, 3]
    assert r["tarot"]["birth_cards"]["personality"]["name_en"] == "The Universe"
    # Сумма карты года 22: у Арриен — Император (4), у Грир — Шут (22)
    r = calculate(BirthInput(1940, 12, 24), tarot_method="arrien", year=1957)     # 36 + 1957 = 1993 → 22
    assert r["tarot"]["year_card"]["reduction"] == [1993, 22, 4] and r["tarot"]["year_card"]["card"]["number"] == 4
    r = calculate(BirthInput(1940, 12, 24), tarot_method="arrien", year=1957, year_card_22="fool")
    assert r["tarot"]["year_card"]["card"]["number"] == 22                         # старое поведение
    assert year_card(12, 24, 1957)["card"]["name_en"] == "The Fool"                # Грир: «between 1 and 22»
    with pytest.raises(ValueError):
        year_card(12, 24, 1957, sum22="zero")


def test_year_card_external_vectors():
    # https://xtarot.com/tarot-reading/tarot-yearly-card.php — 7.09.1979, год 2014: 2030 → 5 (Иерофант)
    yc = year_card(9, 7, 2014)
    assert yc["reduction"] == [2030, 5] and yc["card"]["number"] == 5
    # https://www.aeclectic.net/tarot/blog/numerology-tarot-birth-cards.shtml — личный год Tarot School:
    # 12 + 29 + 2 + 0 + 0 + 6 = 49 → 13 (Смерть)
    yc = year_card(12, 29, 2006, method="tarot_school")
    assert yc["reduction"] == [49, 13] and yc["card"]["number"] == 13
    assert year_card(12, 29, 2006)["card"]["number"] == 13       # по Грир: 2047 → 13
    # Грир (marykgreer.com, ответ от 16.09.2011, т.е. ДО дня рождения 24.10 → календарный год):
    # 24.10, 2011 → 2045 → 11; «год от дня рождения» дал бы 2010 → 2044 → 10
    assert year_card(10, 24, 2011)["card"]["number"] == 11
    r = calculate(BirthInput(1966, 10, 24), year=2011)
    assert r["tarot"]["year_card"]["matches_birth_cards"] == ["hidden_factor (год Учителя/Тени)"]  # «Shadow/Teacher Year»
    # Tarot School: совпадения ищутся с картами Tarot School (T1: 21/3), а не Грир
    r = calculate(T1, tarot_method="tarot_school", year=2026)   # 5 + 15 + (2+0+2+6) = 30 → 3
    assert r["tarot"]["year_card"]["card"]["number"] == 3
    assert r["tarot"]["year_card"]["matches_birth_cards"] == ["soul"]


def test_ru_arcana_external_vectors():
    # https://lenta.ru/articles/2025/04/08/kak-uznat-svoy-arkan-taro-po-date-rozhdeniya/ — 23.05.1992: 31 − 22 = 9
    r = ru_arcana(1992, 5, 23)
    assert r["date_digits_minus22"]["reduction"] == [31, 9]
    assert r["date_digits_minus22"]["card"]["name_ru"] == "Отшельник"
    # https://www.nur.kz/esoterics/interesting/2009995-arkany-taro-kak-rasschitat-svoy-za-2-minuty-i-uznat-ego-znachenie/
    # 08.08.1974: 37 − 22 = 15 (Дьявол); по дню: 3 сентября 1978 → 3 (Императрица)
    assert ru_arcana(1974, 8, 8)["date_digits_minus22"]["card"]["number"] == 15
    assert ru_arcana(1978, 9, 3)["day_arcana"]["card"]["number"] == 3
    # https://vikna.tv/ru/dozvillia/goroskop/arkan-po-date-rozhdeniya-kak-rasschitat-i-uznat-svoj/ —
    # способ 1: 15.03.1990 → 28 − 22 = 6 (Влюблённые); способ 2: 27.07.1990 → 9 + 7 + 19 = 35 → 8 (Сила)
    assert ru_arcana(1990, 3, 15)["date_digits_minus22"]["card"]["number"] == 6
    r = ru_arcana(1990, 7, 27)
    assert r["day_month_year"]["reduction"] == [35, 8] and r["day_month_year"]["card"]["name_ru"] == "Сила"
    # https://www.svitstyle.com.ua/ru/?p=113 — 23.12.2001: 2+3+1+2+2+0+0+1 = 11 (Справедливость)
    r = ru_arcana(2001, 12, 23)
    assert r["date_digits_reduce"]["card"]["number"] == 11
    assert r["date_digits_reduce"]["card"]["name_ru"] == "Справедливость"
    # день > 22: −22 (по умолчанию) или сумма цифр
    assert ru_arcana(1990, 1, 27)["day_arcana"]["card"]["number"] == 5
    assert ru_arcana(1990, 1, 27, over22="digits")["day_arcana"]["card"]["number"] == 9


def test_decks_numbering():
    from calculators.tarot_loshu import card
    assert card(8)["name_ru"] == "Сила" and card(11)["name_ru"] == "Справедливость"
    assert card(8, "marseille")["name_ru"] == "Справедливость" and card(8, "marseille")["name_en"] == "La Justice"
    assert card(11, "marseille")["name_ru"] == "Сила"
    assert card(8, "thoth")["name_en"] == "Adjustment" and card(11, "thoth")["name_en"] == "Lust"
    assert card(22)["name_en"] == "The Fool" and card(0)["name_en"] == "The Fool"
    r = calculate(T1, tarot_method="arrien", year=2026)
    assert r["variant"]["deck"] == "thoth" and r["tarot"]["birth_cards"]["terms"]["year"] == "Growth Symbol"


def test_greer_22_fool():
    from calculators.tarot_loshu import greer_from_total
    r = greer_from_total(1984)     # 1+9+8+4 = 22 → Шут / Император, Учитель 13
    assert r["personality"]["name_en"] == "The Fool" and r["soul"]["number"] == 4
    assert nums(r["hidden_factor"]) == [13]
    r = greer_from_total(1999)     # 28 → 10 → 10/1
    assert r["reduction"] == [1999, 28, 10] and r["pattern"] == "10-1"


# ---------------------------------------------------------------------------
# B. Ло Шу — внешние векторы
# ---------------------------------------------------------------------------

def _date_only(y: int, m: int, d: int) -> dict:
    return calculate(BirthInput(y, m, d), year=2026)["loshu"]


def test_loshu_date_only_external():
    # https://astromedha.in/insights/lo-shu/grid — 15.08.1982: 1×2, 2, 5, 8×2, 9; нет 3, 4, 6, 7
    lo = _date_only(1982, 8, 15)
    assert counts(lo) == {1: 2, 2: 1, 5: 1, 8: 2, 9: 1} and lo["missing"] == [3, 4, 6, 7]
    # https://numerologynamcalc.com/lo-shu-grid-guide/ — 14.02.1990: 1×2, 2, 4, 9×2; Driver 5, Conductor 8
    lo = _date_only(1990, 2, 14)
    assert counts(lo) == {1: 2, 2: 1, 4: 1, 9: 2} and lo["missing"] == [3, 5, 6, 7, 8]
    assert lo["driver"] == 5 and lo["conductor"] == 8
    # https://ganak.app/calculators/lo-shu-grid-calculator/ — 15.03.1990: 1×2, 3, 5, 9×2; Driver 6, Conductor 1
    lo = _date_only(1990, 3, 15)
    assert counts(lo) == {1: 2, 3: 1, 5: 1, 9: 2} and lo["missing"] == [2, 4, 6, 7, 8]
    assert lo["driver"] == 6 and lo["conductor"] == 1
    # https://www.vastucart.in/tools/lo-shu-grid — 15.08.1987: 1×2, 5, 7, 8×2, 9; пусто 2, 3, 4, 6
    lo = _date_only(1987, 8, 15)
    assert counts(lo) == {1: 2, 5: 1, 7: 1, 8: 2, 9: 1} and lo["missing"] == [2, 3, 4, 6]


def test_loshu_with_driver_conductor_external():
    opt = {"loshu_include": "date+driver+conductor", "year": 2026}
    # https://bivs.com/tools/lo-shu-grid-calculator/ — 16.05.1990 (+7, +4): 1×2, 4, 5, 6, 7, 9×2; нет 2, 3, 8
    lo = calculate(BirthInput(1990, 5, 16), **opt)["loshu"]
    assert lo["driver"] == 7 and lo["conductor"] == 4
    assert counts(lo) == {1: 2, 4: 1, 5: 1, 6: 1, 7: 1, 9: 2} and lo["missing"] == [2, 3, 8]
    # https://pathnumbers.com/chinese-numerology-calculator/ — 15.03.1987: 1,5,3,1,9,8,7 + 6 + 7; нет 2, 4
    lo = calculate(BirthInput(1987, 3, 15), **opt)["loshu"]
    assert sorted(lo["numbers_placed"]) == sorted([1, 5, 3, 1, 9, 8, 7, 6, 7])
    assert lo["missing"] == [2, 4] and lo["repeated"] == {"1": 2, "7": 2}
    # https://sheelaa.com/blog/what-is-lo-shu-grid-the-ancient-magic-square-that-reveals-your-lifes-blueprint/
    # 17.09.1988 (+8, +7): 1×2, 7×2, 8×3, 9×2; нет 2, 3, 4, 5, 6
    lo = calculate(BirthInput(1988, 9, 17), **opt)["loshu"]
    assert counts(lo) == {1: 2, 7: 2, 8: 3, 9: 2} and lo["missing"] == [2, 3, 4, 5, 6]


def test_loshu_lines_invariants():
    g = loshu_grid([1, 2, 3, 4, 5, 6, 7, 8, 9])
    assert len(g["arrows_of_strength"]) == 8 and not g["arrows_of_weakness"]
    g = loshu_grid([])
    assert len(g["arrows_of_weakness"]) == 8 and g["missing"] == list(range(1, 10))
    # каждая линия магического квадрата даёт 15
    for p in g["planes"]:
        assert sum(p["cells"]) == 15
    # ноль не размещается
    g = loshu_grid([0, 0, 5])
    assert counts(g) == {5: 1}
    # Куа добавляется в сетку только при наличии пола
    lo = calculate(BirthInput(1990, 5, 15, gender="female"), loshu_include="date+driver+conductor+kua",
                   year=2026)["loshu"]
    assert lo["numbers_placed"][-3:] == [6, 3, 8]


def test_kua_formula():
    # Формула: https://ganak.app/calculators/lo-shu-grid-calculator/ (м: 10 − r / 9 − r; ж: r + 5 / r + 6;
    # 5 → 2 у мужчин, 8 у женщин).
    assert kua_number(1990, "male") == 1 and kua_number(1990, "female") == 8
    assert kua_number(2000, "male") == 9 and kua_number(2000, "female") == 6
    assert kua_number(1986, "male") == 2          # 10 − 5 = 5 → 2
    assert kua_number(1987, "female") == 2        # 5 + 6 = 11 → 2
    assert kua_number(2009, "male") == 9          # 9 − 9 = 0 → 9
    # https://namenumerologycalculator.com/lo-shu-grid-calculator/ — пример «мужчина 1985»:
    # «10 − 8 − 5 = −3 → +9»: арифметика страницы даёт 6 (на странице опечатка «3»)
    assert kua_number(1985, "male") == 6
    # начало верхней эпохи Сань Юань (1864): мужчины 1, женщины 5 → 8
    assert kua_number(1864, "male") == 1 and kua_number(1864, "female") == 8
    with pytest.raises(ValueError):
        kua_number(1990, "x")


# ---------------------------------------------------------------------------
# C. Ведическая нумерология — внешние векторы
# ---------------------------------------------------------------------------

def test_vedic_external_vectors():
    # https://panchangbodh.com/vedic-numerology — 23-08-1990: Мулянк 5, Бхагьянк 32 → 5
    v = vedic_numbers(1990, 8, 23)
    assert v["moolank"]["number"] == 5 and v["bhagyank"]["reduction"] == [32, 5]
    # https://anktriveni.onrender.com/ — 29-06-1990: Мулянк 11 → 2, Бхагьянк 36 → 9
    v = vedic_numbers(1990, 6, 29)
    assert v["moolank"]["reduction"] == [29, 11, 2] and v["bhagyank"]["reduction"] == [36, 9]
    # https://astrosight.ai/kundli/psychic-and-destiny-number-compatibility — 15.03.1990: Psychic 6, Destiny 28→10→1
    v = vedic_numbers(1990, 3, 15)
    assert v["moolank"]["number"] == 6 and v["bhagyank"]["reduction"] == [28, 10, 1]
    # https://ganak.app/calculators/lo-shu-grid-calculator/ — 25.12.1990: Driver 7, Conductor 29 → 11 → 2
    v = vedic_numbers(1990, 12, 25)
    assert v["moolank"]["number"] == 7 and v["bhagyank"]["reduction"] == [29, 11, 2]
    # https://instaastro.com/numerology/lo-shu-grid/ — 15.10.1997: Driver 6, Conductor 33 → 6
    v = vedic_numbers(1997, 10, 15)
    assert v["moolank"]["number"] == 6 and v["bhagyank"]["reduction"] == [33, 6]
    # вариант с мастер-числами (не ведический по умолчанию)
    assert vedic_numbers(1997, 10, 15, master=True)["bhagyank"]["number"] == 33


def test_planets_and_relations():
    from calculators.tarot_loshu import PLANETS
    # https://panchangbodh.com/vedic-numerology, https://astrosight.ai/... — 1 Солнце … 9 Марс
    assert [PLANETS[i] for i in range(1, 10)] == ["sun", "moon", "jupiter", "rahu", "mercury",
                                                  "venus", "ketu", "saturn", "mars"]
    # BPHS 3.55 (та же таблица в calculators/jyotish.py)
    assert natural_relation(1, 8) == "enemy"      # Солнце → Сатурн
    assert natural_relation(8, 1) == "enemy"
    assert natural_relation(2, 5) == "friend"     # Луна → Меркурий
    assert natural_relation(5, 2) == "enemy"      # Меркурий → Луна (асимметрия)
    assert natural_relation(1, 9) == "friend" and natural_relation(3, 9) == "friend"
    assert natural_relation(4, 1) == "neutral" and natural_relation(7, 2) == "neutral"   # Раху/Кету
    t = relation_table()
    assert t["1"] == {"friend": [2, 3, 9], "neutral": [4, 5, 7], "enemy": [6, 8]}
    assert t["2"]["enemy"] == []


def test_chaldean():
    # Таблица Хейро: https://anktriveni.onrender.com/ (A,I,J,Q,Y=1; B,K,R=2; C,G,L,S=3; D,M,T=4;
    # E,H,N,X=5; U,V,W=6; O,Z=7; F,P=8)
    r = chaldean_name_number("Albert Einstein")
    assert [w["compound"] for w in r["words"]] == [17, 29] and r["number"] == 1
    r = chaldean_name_number("Щука Юля")
    assert r["latin"] == "SHCHUKA IULIA"


def test_chaldean_cheiro_primary_examples():
    """Первоисточник: Cheiro's Book of Numbers (Herbert Jenkins, London), гл. XIII–XIV, с. 70–72, 86–87.
    Скан: https://archive.org/details/in.ernet.dli.2015.70770 ;
    https://archive.org/details/cheirosbookofnumbers (OCR-текст _djvu.txt)."""
    # «JOHN … 18 = 1 plus 8 = 9; SMITH … 17 = 1 plus 7 = 8 … the 8 and 9 added together make 17,
    #  and 1 plus 7 makes 8»
    r = chaldean_name_number("John Smith")
    assert [(w["compound"], w["single"]) for w in r["words"]] == [(18, 9), (17, 8)]
    assert r["compound_cheiro"] == 17 and r["number"] == 8
    # LLOYD = 18 → 9, GEORGE → 7: «7 plus 9 and you get the compound number of 16»
    r = chaldean_name_number("Lloyd George")
    assert [w["single"] for w in r["words"]] == [9, 7] and r["compound_cheiro"] == 16 and r["number"] == 7
    # «David Lloyd George … would make the total of the three names the number 23»
    assert chaldean_name_number("David Lloyd George")["compound_cheiro"] == 23
    # BALDWIN: B2 A1 L3 D4 W6 I1 N5 = 22 → 4
    r = chaldean_name_number("Baldwin")
    assert r["compound"] == 22 and r["number"] == 4
    # с. 75–76: «RAMSAY … 12 = 3», «MACDONALD … 32 = 5», «5 plus 3, produces an 8»
    r = chaldean_name_number("Ramsay MacDonald")
    assert [(w["compound"], w["single"]) for w in r["words"]] == [(12, 3), (32, 5)]
    assert r["compound_cheiro"] == 8 and r["number"] == 8
    # F = 8 и K = 2 читаются в OCR второго скана, с. 70 («F = 8», «K = 2»):
    # https://archive.org/details/cheirosbookofnum00chei (полнотекстовый поиск archive.org)
    from calculators.tarot_loshu import CHALDEAN
    assert CHALDEAN["F"] == 8 and CHALDEAN["K"] == 2
    # Буквы вне A–Z (укр. І, Ґ) не имеют значения — помечаются и дают предупреждение
    assert chaldean_name_number("Ґудзь")["unmapped"] == ["Ґ"]
    r = calculate(BirthInput(1990, 5, 15, name="Олексій"), year=2026)
    assert any("без значения" in w for w in r["warnings"])
