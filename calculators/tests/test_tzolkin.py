"""Тесты калькулятора «Цолькин» (Dreamspell / 13 Лун + классический счёт майя).

Запуск: .venv/bin/python -m pytest calculators/tests/test_tzolkin.py -q
Внешние векторы взяты из опубликованных источников; URL — в комментариях у каждого блока.
Ручной разбор T1–T4 — в knowledge-base/13-tzolkin.md.
"""
from __future__ import annotations

import json

import pytest

from calculators.common.time import BirthInput
from calculators.tzolkin import (
    GAP_KINS, POLAR_KINS, SEALS, affirmation_en, calculate, classic, classic_from_jdn,
    dreamspell_kin, dreamspell_year_bearer, dreamspell_year_code, earth_family, gregorian_to_jdn,
    jdn_to_gregorian, julian_to_jdn, kin_from_tone_seal, kin_info, long_count_to_days, oracle,
    seal_of, thirteen_moon_date, tone_of, wavespell,
)

SEAL_BY_POWER_EN = {v["power"][1]: k for k, v in SEALS.items()}

# ---------------------------------------------------------------------------
# Эталонные персоны T1–T4
# ---------------------------------------------------------------------------

T1 = BirthInput(1990, 5, 15, 14, 30, place="Москва", gender="female", name="Иванова Анна Сергеевна")
T2 = BirthInput(1984, 2, 4, 23, 30, place="Москва", gender="male", name="Петров Дмитрий Олегович")
T3 = BirthInput(2004, 2, 29, 8, 15, place="Санкт-Петербург", gender="female",
                name="Смирнова Мария Александровна")
T4 = BirthInput(1879, 3, 14, 11, 30, tz="LMT", lat=48.4011, lon=9.9876, gender="male", name="Albert Einstein")


def test_t1_dreamspell_and_classic():
    # Dreamspell: https://13moon.com/decoder.php (POST galactic-signature.php, 15.05.1990):
    # «Kin 17: Red Self-Existing Earth … I am guided by the power of Space».
    # Классика: http://tsolkin.ru/api/api.php?date=15.05.1990 → kin 224, тон 3, печать 4 (= 3 Kʼan, GMT 584283).
    r = calculate(T1)
    ds, cl = r["dreamspell"], r["classic"]
    assert ds["kin"] == 17 and ds["tone"] == 4 and ds["seal"] == 17
    assert ds["name_ru"] == "Красная Самосущная Земля"
    assert ds["name_en"] == "Red Self-Existing Earth"
    assert ds["oracle"]["guide"]["kin"] == 173          # Красный Самосущный Небесный Странник (Space)
    assert ds["oracle"]["analog"]["kin"] == 82          # Белый Самосущный Ветер
    assert ds["oracle"]["antipode"]["kin"] == 147       # Синяя Самосущная Рука
    assert ds["oracle"]["occult"]["kin"] == 244         # Жёлтое Планетарное Семя
    assert ds["wavespell"]["number"] == 2 and ds["wavespell"]["seal"] == 14   # ВМ Волшебника
    assert ds["castle"]["number"] == 1
    assert ds["earth_family"]["key"] == "core"
    assert not ds["is_gap"]
    tm = ds["thirteen_moon"]
    assert (tm["moon"], tm["day"], tm["plasma"]["ru"]) == (11, 14, "Силио")
    assert tm["year_start"] == 1989 and tm["year_bearer"]["kin"] == 244       # год Жёлтого Планетарного Семени
    assert affirmation_en(17) == [
        "I Define in order to Evolve", "Measuring Synchronicity", "I seal the Matrix of Navigation",
        "With the Self-Existing tone of Form", "I am guided by the power of Space",
    ]
    assert cl["calendar_round"] == "3 Kʼan 17 Woʼ" and cl["tzolkin"]["index_260"] == 224
    assert cl["long_count"] == "12.18.17.1.4"
    assert r["comparison"]["same"] is False
    assert r["comparison"]["classic_minus_dreamspell_mod260"] == 207


def test_t2_dreamspell_and_classic():
    # Dreamspell: https://13moon.com/decoder.php (04.02.1984): «Kin 67: Blue Lunar Hand … guided by the power of
    # Self-generation». Классика: http://tsolkin.ru/api/api.php?date=04.02.1984 → kin 12, тон 12, печать 12.
    r = calculate(T2)
    ds, cl = r["dreamspell"], r["classic"]
    assert ds["kin"] == 67 and ds["name_ru"] == "Синяя Лунная Рука"
    assert ds["oracle"]["guide"]["seal"] == SEAL_BY_POWER_EN["Self-generation"] == 19
    assert ds["oracle"]["guide"]["kin"] == 119            # Синяя Лунная Буря
    assert ds["thirteen_moon"]["year_start"] == 1983      # дата раньше 26 июля
    assert cl["calendar_round"] == "12 Ebʼ 0 Pax" and cl["tzolkin"]["index_260"] == 12
    assert cl["long_count"] == "12.18.10.12.12"


def test_t3_feb29_hunab_ku():
    # Dreamspell: https://13moon.com/decoder.php: 28.02.2004 и 29.02.2004 → оба «Kin 111: Blue Resonant Monkey»,
    # 01.03.2004 → «Kin 112: Yellow Galactic Human». Официальный виджет https://lawoftime.org/decode/ :
    # функция o(): «2==p&&29==m&&(m=28)» — 29 февраля считается как 28-е.
    # Классика: http://tsolkin.ru/api/api.php?date=29.02.2004 → kin 62, тон 10, печать 2 (10 Ikʼ).
    r = calculate(T3)
    ds = r["dreamspell"]
    assert ds["kin"] == 111 == dreamspell_kin(2004, 2, 28)
    assert dreamspell_kin(2004, 3, 1) == 112
    assert ds["thirteen_moon"]["is_hunab_ku"] is True and ds["thirteen_moon"]["moon"] is None
    assert ds["is_gap"] is True
    assert ds["oracle"]["guide"]["seal"] == SEAL_BY_POWER_EN["Abundance"]
    assert any("Хунаб Ку" in w for w in r["warnings"])
    cl = r["classic"]
    assert cl["tzolkin"]["label"] == "10 Ikʼ" and cl["tzolkin"]["index_260"] == 62
    # классический счёт 29.02 не пропускает: 28.02 и 01.03 различаются на 2 дня
    assert classic(2004, 2, 28)["tzolkin"]["index_260"] == 61
    assert classic(2004, 3, 1)["tzolkin"]["index_260"] == 63


def test_t4_einstein():
    # Dreamspell: Фонд Закона Времени, «Find Who Shares Your Galactic Signature», Kin 260 Yellow Cosmic Sun —
    # Albert Einstein: http://www.lawoftime.org/thirteenmoon/kin/kin260.html
    # Классика: http://tsolkin.ru/api/api.php?date=14.03.1879 → kin 180, тон 11, печать 20 (11 Ajaw).
    r = calculate(T4)
    ds, cl = r["dreamspell"], r["classic"]
    assert ds["kin"] == 260 and ds["name_ru"] == "Жёлтое Космическое Солнце"
    assert ds["is_gap"] is True
    assert ds["oracle"]["guide"]["kin"] == 104            # Жёлтое Космическое Семя (Flowering)
    assert ds["oracle"]["occult"]["kin"] == 1
    assert ds["thirteen_moon"]["year_bearer"]["kin"] == 29  # 26.07.1878 = Красная Электрическая Луна
    assert cl["calendar_round"] == "11 Ajaw 13 Pax" and cl["tzolkin"]["index_260"] == 180
    assert cl["long_count"] == "12.13.4.5.0"


# ---------------------------------------------------------------------------
# Dreamspell: внешние векторы
# ---------------------------------------------------------------------------

# Калькулятор https://13moon.com/decoder.php (Galactic Calendar / SkyTime; POST на galactic-signature.php),
# ответы сняты 14.10.2026. Формат: дата -> (кин, сила Ведущего или None для «собственной удвоенной силы», ПГА).
DECODER_13MOON = {
    (1910, 1, 1): (63, None, False),
    (1926, 5, 26): (68, "Free Will", False),
    (1944, 9, 25): (260, "Flowering", True),
    (1953, 7, 26): (104, "Elegance", False),
    (1963, 6, 9): (67, "Self-generation", False),
    (1965, 2, 7): (155, "Accomplishment", True),
    (1965, 9, 11): (111, "Abundance", True),
    (1969, 7, 24): (222, None, True),
    (1987, 7, 25): (33, "Life Force", False),      # День вне времени — свой кин есть
    (1987, 7, 26): (34, "Endlessness", False),     # якорь: Белый Галактический Волшебник
    (1990, 7, 25): (88, "Intelligence", True),     # до 26 июля
    (1990, 7, 26): (89, None, False),              # после 26 июля (+1 день)
    (2000, 2, 29): (211, "Vision", True),
    (2004, 2, 28): (111, "Abundance", True),
    (2004, 3, 1): (112, "Intelligence", True),
    (2012, 12, 21): (207, "Self-generation", False),
    (2021, 12, 21): (112, "Intelligence", True),
    (2024, 2, 29): (131, None, False),
}


@pytest.mark.parametrize("ymd,expected", list(DECODER_13MOON.items()))
def test_dreamspell_13moon_decoder(ymd, expected):
    kin, guide_power, gap = expected
    assert dreamspell_kin(*ymd) == kin
    o = oracle(kin)
    if guide_power is None:
        assert o["guide"]["self_guided"] and o["guide"]["kin"] == kin
    else:
        assert o["guide"]["seal"] == SEAL_BY_POWER_EN[guide_power]
    assert (kin in GAP_KINS) is gap


# Фонд Закона Времени (lawoftime.org) и его русский сайт (news.law-of-time.ru).
OFFICIAL_LOT = [
    # Planetary Kin Report 2021–2022: https://lawoftime.org/wp-content/uploads/Planetary-Kin-Report.pdf
    ((1987, 8, 16), 55),     # «Harmonic Convergence … August 16, 1987 (Kin 55)»
    ((2001, 9, 11), 11),     # «9-11 … lands on Kin 11: Blue Spectral Monkey»
    ((2021, 12, 21), 112),   # «This December 21 solstice, Kin 112»
    # «Find Who Shares Your Galactic Signature»: http://www.lawoftime.org/thirteenmoon/kin/kin017.html,
    # kin067.html, kin111.html (даты рождения — общеизвестные)
    ((1775, 12, 16), 17),    # Jane Austen
    ((1694, 11, 21), 67),    # Voltaire
    ((1963, 6, 9), 67),      # Johnny Depp
    ((1898, 9, 26), 111),    # George Gershwin
    ((1965, 9, 11), 111),    # Moby
    # https://news.law-of-time.ru/ (блог Стефани Саут, русский перевод)
    ((2023, 7, 25), 173),    # «25 июля 2023 года — Кин 173, Красный Самосущный Небесный Странник»
    ((1953, 6, 2), 50),      # «коронованной … 2 июня 1953 года — 4 день Кристаллической Луны … Кин 50»
    ((2024, 12, 25), 171),   # «Рождество, Кин 171 Синяя Лунная Обезьяна»
    ((2025, 1, 1), 178),     # «вступим в 2025 год … Кин 178, Белое Солнечное Зеркало»
    ((2025, 7, 25), 123),    # «День Вне Времени 2025 года также приходится на Кин 123»
    ((2025, 3, 13), 249),    # «Полного Лунного Затмения в Кин 249, Красную Лунную Луну (13 марта»
    ((2020, 12, 10), 256),   # «Жёлтого Солнечного Воина (10 декабря 2020 г.)»
    ((2023, 6, 15), 133),    # «17-й день Кристаллической Луны … Кин 133» (71 год от 15.06.1952)
    ((2026, 7, 25), 228),    # «Скоро День Вне Времени: Кин 228 … (25 июля»
]


@pytest.mark.parametrize("ymd,kin", OFFICIAL_LOT)
def test_dreamspell_official_law_of_time(ymd, kin):
    assert dreamspell_kin(*ymd) == kin


def test_dreamspell_year_bearers_and_anchors():
    # Виджет https://lawoftime.org/decode/ : «year=10,seal=9,number=49» для 2002 → 26.07.2002 = Кин 49
    assert dreamspell_year_bearer(2002) == 49 == kin_from_tone_seal(10, 9)
    assert dreamspell_year_bearer(1987) == 34                 # Белый Галактический Волшебник
    # Planetary Kin Report: «Yellow Electric Seed Year NS1.34 / 2021-2022»
    assert kin_info(dreamspell_year_bearer(2021))["name_en"] == "Yellow Electric Seed"
    assert thirteen_moon_date(2021, 8, 1)["ns"] == "NS1.34"
    # news.law-of-time.ru: «год Белого Обертонного Волшебника (26.07.2023- 25.07.2024гг.)»
    assert kin_info(dreamspell_year_bearer(2023))["name_ru"] == "Белый Обертонный Волшебник"
    # 13moon.com: «July 26, 2026 - July 25, 2027 Red Galactic Moon Year»
    assert kin_info(dreamspell_year_bearer(2026))["name_en"] == "Red Galactic Moon"
    # news.law-of-time.ru: «4 день (Кали) Магнитной Луны, года Самосущной Луны, Кин 72 Жёлтый Резонансный Человек,
    # Портал Галактической активации» → 29.07.2022
    tm = thirteen_moon_date(2022, 7, 29)
    assert (tm["moon"], tm["day"], tm["plasma"]["ru"]) == (1, 4, "Кали")
    assert kin_info(tm["year_bearer"]["kin"])["name_ru"] == "Красная Самосущная Луна"
    assert dreamspell_kin(2022, 7, 29) == 72 and 72 in GAP_KINS
    # Ritмическая Луна 9 = 21 декабря (news.law-of-time.ru: «9-й день Ритмической Луны (21 декабря), Кин 217»;
    # год выведен: 21 декабря получает Кин 217 раз в 52 года, в 1987–2038 — только в 2022)
    assert thirteen_moon_date(2022, 12, 21)["moon"] == 6 and thirteen_moon_date(2022, 12, 21)["day"] == 9
    assert dreamspell_kin(2022, 12, 21) == 217
    # Галактический компас: 12 апреля = 10.09 (Планетарная Луна, 9 день)
    # https://lawoftime.org/infobooth/thegalacticcompass.html
    tm = thirteen_moon_date(2024, 4, 12)
    assert (tm["moon"], tm["day"]) == (10, 9)


def test_day_out_of_time_and_boundaries():
    tm = thirteen_moon_date(1990, 7, 25)
    assert tm["is_day_out_of_time"] and tm["year_start"] == 1989
    tm = thirteen_moon_date(1990, 7, 26)
    assert (tm["moon"], tm["day"], tm["plasma"]["ru"]) == (1, 1, "Дали") and tm["year_start"] == 1990
    # Кин продвигается и в День вне времени (25.07 → 26.07 = +1)
    assert dreamspell_kin(1990, 7, 26) - dreamspell_kin(1990, 7, 25) == 1


def test_52_year_cycle_and_year_codes():
    # Галактический компас (lawoftime.org/infobooth/thegalacticcompass.html): кин возвращается на ту же дату
    # через 52 года (18 980 дней). Проверяем на всех датах года.
    for m, d in [(1, 1), (2, 28), (2, 29), (3, 1), (7, 25), (7, 26), (12, 31)]:
        y = 2000 if (m, d) == (2, 29) else 1990
        assert dreamspell_kin(y, m, d) == dreamspell_kin(y + 52, m, d)
    # Ручной метод «код года + код месяца + число»
    assert dreamspell_year_code(1990) == 142
    assert dreamspell_year_code(1991) == (142 + 105) % 260
    assert (dreamspell_year_code(1990) + 120 + 15) % 260 == 17


# ---------------------------------------------------------------------------
# Оракул: официальные правила
# ---------------------------------------------------------------------------

def test_oracle_rules_official():
    # lawoftime.org 13 Moon Calendar Tutorial (http://www.lawoftime.org/thirteenmoon/tutorial.html):
    # «Kin 2, White Lunar Wind … guided by White Lunar Wizard»; «Wind and the Storm are occult/hidden powers of each
    # other; Warrior … and Worldbridger … are antipode/challenge partners»; «Kin 1 … guided by its own power doubled».
    assert oracle(2)["guide"]["name_en"] == "White Lunar Wizard" and oracle(2)["guide"]["kin"] == 54
    assert oracle(1)["guide"]["kin"] == 1
    assert seal_of(oracle(kin_from_tone_seal(5, 2))["occult"]["kin"]) == 19
    assert seal_of(oracle(kin_from_tone_seal(5, 16))["antipode"]["kin"]) == 6
    # Oracle Board (http://www.lawoftime.org/images/oracle-board.png), красный лист:
    # Дракон: антипод Обезьяна, аналог Зеркало, оккульт Солнце; Ветер: Человек, Земля, Буря;
    # Ночь: Небесный Странник, Воин, Зеркало; Семя: Волшебник, Орёл, Земля.
    board = {1: (11, 18, 20), 2: (12, 17, 19), 3: (13, 16, 18), 4: (14, 15, 17)}
    for s, (anti, ana, occ) in board.items():
        o = oracle(kin_from_tone_seal(1, s))
        assert (o["antipode"]["seal"], o["analog"]["seal"], o["occult"]["seal"]) == (anti, ana, occ)
    # Destiny Oracle graphic (http://www.lawoftime.org/images/destinyoracle-guide.png): Ведущий того же цвета
    # и тона; аналог и антипод того же тона; тоны оккульта в сумме 14.
    for kin in range(1, 261):
        o = oracle(kin)
        t = tone_of(kin)
        assert o["guide"]["tone"] == o["analog"]["tone"] == o["antipode"]["tone"] == t
        assert o["guide"]["color"] == kin_info(kin)["color"]
        assert o["occult"]["tone"] + t == 14
        assert o["occult"]["kin"] + kin == 261
        assert (o["analog"]["seal"] + seal_of(kin)) % 20 == 19
        assert (o["antipode"]["seal"] - seal_of(kin)) % 20 == 10
    # news.law-of-time.ru: «Ведущий Кин Космической Собаки (кина 130) — Белый Космический Волшебник: Кин 234»
    assert oracle(130)["guide"]["kin"] == 234


def test_tables_consistency():
    assert len(GAP_KINS) == 52 and all(261 - k in GAP_KINS for k in GAP_KINS)   # симметрия ткацкого станка
    assert len(POLAR_KINS) == 16
    assert all(earth_family(seal_of(k))["key"] == "polar" for k in POLAR_KINS)
    assert all(tone_of(k) in (3, 4, 10, 11) for k in POLAR_KINS)
    for t in range(1, 14):
        for s in range(1, 21):
            k = kin_from_tone_seal(t, s)
            assert tone_of(k) == t and seal_of(k) == s
    assert wavespell(1)["name_ru"] == "Красный Волновой Модуль Дракона"
    assert wavespell(118)["name_ru"] == "Синий Волновой Модуль Обезьяны"
    assert wavespell(260)["first_kin"] == 248 and wavespell(260)["seal"] == 6       # Соединитель Миров
    # 28 Meditations on the Law of Time (Meditation 5): Gateway = Seed, Moon, Wizard, Storm
    assert earth_family(4)["seals"] == (4, 9, 14, 19)
    assert all(earth_family(seal_of(dreamspell_year_bearer(y)))["key"] == "gateway" for y in range(1900, 2100))


# ---------------------------------------------------------------------------
# Классический счёт: академические и современные (кʼиче) векторы
# ---------------------------------------------------------------------------

def test_classic_long_count_table_wikipedia():
    # https://en.wikipedia.org/wiki/Mesoamerican_Long_Count_calendar — таблица (GMT 584,283, пролептический
    # григорианский): 0.0.0.0.0 = 11.08.3114 до н.э. JDN 584283; 9.0.0.0.0 = 9.12.435 JDN 1880283;
    # 12.0.0.0.0 = 18.09.1618 JDN 2312283; 13.0.0.0.0 = 21.12.2012 JDN 2456283.
    assert gregorian_to_jdn(-3113, 8, 11) == 584283
    assert classic(-3113, 8, 11)["calendar_round"] == "4 Ajaw 8 Kumkʼu"
    assert classic(435, 12, 9)["long_count"] == "9.0.0.0.0" and gregorian_to_jdn(435, 12, 9) == 1880283
    assert classic(1618, 9, 18)["long_count"] == "12.0.0.0.0"
    assert jdn_to_gregorian(2600283) == (2407, 3, 26)                 # 14.0.0.0.0
    r = classic(2012, 12, 21)
    assert r["jdn"] == 2456283 and r["long_count"] == "13.0.0.0.0"
    # https://en.wikipedia.org/wiki/2012_phenomenon : «13.0.0.0.0 4 Ahau 3 Kʼankʼin … 21 or 23 December 2012»
    assert r["calendar_round"] == "4 Ajaw 3 Kʼankʼin"
    alt = classic(2012, 12, 23, correlation=584285)
    assert alt["long_count"] == "13.0.0.0.0" and alt["calendar_round"] == "4 Ajaw 3 Kʼankʼin"


def test_classic_inscriptions_wikipedia():
    # https://en.wikipedia.org/wiki/Mesoamerican_Long_Count_calendar
    # Пакаль: «9.8.9.13.0 8 Ajaw 13 Pop (24 March 603 CE Gregorian)»; восшествие «5 Lamat 1 Mol, 9.9.2.4.8 …
    # 27 July 615 CE»; Чичен-Ица «10.2.9.1.9 9 Muluk 7 Sak, equivalent to July 28, 878 (GMT Gregorian)»;
    # «9.12.2.0.16 5 Kibʼ 14 Yaxkʼin»; «9.10.11.17.0 … 1,372,300 + 584,283 = 1,956,583 … Julian … October 31, 644».
    for (y, m, d), lc, cr in [((603, 3, 24), "9.8.9.13.0", "8 Ajaw 13 Pop"),
                              ((615, 7, 27), "9.9.2.4.8", "5 Lamat 1 Mol"),
                              ((878, 7, 28), "10.2.9.1.9", "9 Muluk 7 Sak")]:
        r = classic(y, m, d)
        assert r["long_count"] == lc and r["calendar_round"] == cr
    assert classic_from_jdn(long_count_to_days(9, 12, 2, 0, 16) + 584283)["calendar_round"] == "5 Kʼibʼ 14 Yaxkʼin"
    assert long_count_to_days(9, 10, 11, 17, 0) + 584283 == 1956583 == julian_to_jdn(644, 10, 31)


def test_classic_colonial_highland_records():
    # Wikipedia (Long Count, раздел о корреляции): Weeks, Sachse, Prager «Maya Daykeeping» (2013):
    # «December 9, 1722 = 8 Kej 20 Ukabʼ Siʼj (8 Manikʼ 0 Yax) and December 9, 1723 = 9 E … (9 Ebʼ 0 Yax)»;
    # Анналы какчикелей: «2 Tihax (Etzʼnabʼ) is September 10, 1541 (Julian)»;
    # падение Теночтитлана 13.08.1521 (юлиан.) = «1 Snake» (Chikchan).
    r = classic(1722, 12, 9)
    assert r["calendar_round"] == "8 Manikʼ 0 Yax" and r["tzolkin"]["label_kiche"] == "8 Kej"
    r = classic(1723, 12, 9)
    assert r["calendar_round"] == "9 Ebʼ 0 Yax" and r["tzolkin"]["label_kiche"] == "9 Eʼ"
    assert classic(1541, 9, 10, calendar="julian")["tzolkin"]["label"] == "2 Etzʼnabʼ"
    assert classic(1521, 8, 13, calendar="julian")["tzolkin"]["label"] == "1 Chikchan"


@pytest.mark.parametrize("ymd,label_kiche", [
    # Waqxaqibʼ Bʼatzʼ (8 Bʼatzʼ = 8 Chuwen), https://livinginguatemala.com/es/eventos/waqxaqi-batz-ano-nuevo-maya/ :
    # 18.01.2025 (AGN), 22.06.2026 (календарь ALMG), 09.03.2027 (календарь ALMG)
    ((2025, 1, 18), "8 Bʼatzʼ"), ((2026, 6, 22), "8 Bʼatzʼ"), ((2027, 3, 9), "8 Bʼatzʼ"),
    # https://www.prensalibre.com/opinion/8-batz-y-20-de-octubre/ (21.10.2015): «Este 18 de octubre» 8 Bʼatzʼ
    ((2015, 10, 18), "8 Bʼatzʼ"),
    # https://sacredroad.org/ — заголовки дневных постов Cholqʼij: «1 Bʼatzʼ · 2.VI.2026», «12 Qʼanil · 9.VII.2026»,
    # «1 Toj · 19.VIII.2026»
    ((2026, 6, 2), "1 Bʼatzʼ"), ((2026, 7, 9), "12 Qʼanil"), ((2026, 8, 19), "1 Toj"),
])
def test_classic_living_kiche_count(ymd, label_kiche):
    assert classic(*ymd)["tzolkin"]["label_kiche"] == label_kiche


@pytest.mark.parametrize("ddmmyyyy,index_260", [
    # Калькулятор http://tsolkin.ru/api/api.php?date=… (классический счёт GMT, названия по Dreamspell):
    ("15.05.1990", 224), ("04.02.1984", 12), ("29.02.2004", 62), ("14.03.1879", 180),
    ("08.07.1990", 18), ("21.12.2012", 160), ("14.10.2026", 5),
])
def test_classic_tsolkin_ru(ddmmyyyy, index_260):
    d, m, y = (int(x) for x in ddmmyyyy.split("."))
    assert classic(y, m, d)["tzolkin"]["index_260"] == index_260


# ---------------------------------------------------------------------------
# Общие проверки API
# ---------------------------------------------------------------------------

def test_dreamspell_and_classic_drift():
    # Сдвиг «классика − Dreamspell» растёт на 1 после каждого 29 февраля.
    assert calculate(T2)["comparison"]["classic_minus_dreamspell_mod260"] == 205
    assert calculate(T1)["comparison"]["classic_minus_dreamspell_mod260"] == 207   # +2: 1984, 1988
    assert calculate(T3)["comparison"]["classic_minus_dreamspell_mod260"] == 211   # +3 (92, 96, 00) +1 (29.02.04)
    assert calculate(T4)["comparison"]["classic_minus_dreamspell_mod260"] == 180   # 25 високосных дней до 1984


def test_result_schema_and_options():
    r = calculate(T1)
    json.dumps(r, ensure_ascii=False)
    for key in ("method", "variant", "inputs_used", "warnings", "steps", "dreamspell", "classic", "comparison"):
        assert key in r
    assert r["method"] == "tzolkin" and r["default_system"] == "dreamspell"
    assert r["summary"]["primary"].startswith("Кин 17")
    r2 = calculate(BirthInput(2012, 12, 21), correlation="lounsbury", primary="classic")
    assert r2["classic"]["correlation"] == 584285 and r2["default_system"] == "classic"
    assert r2["classic"]["long_count"] == "12.19.19.17.18"
    assert "variant_584285" not in r2["classic"]
    # юлианский ввод (историческая дата) пересчитывается в григорианскую для Dreamspell
    r3 = calculate(BirthInput(1541, 9, 10), input_calendar="julian")
    assert r3["inputs_used"]["gregorian_date"] == "1541-09-20"
    assert r3["classic"]["tzolkin"]["label"] == "2 Etzʼnabʼ"
    assert any("1582" in w for w in r3["warnings"])
    with pytest.raises(ValueError):
        calculate(BirthInput(2001, 2, 29))
