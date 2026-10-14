"""Тесты нормализации времени рождения (calculators/common/time.py).

Проверяется, что normalize() даёт исторически верное смещение от UTC для
советских, постсоветских и европейских дат. Источник каждого ожидаемого
значения указан комментарием рядом с тестом.

Основные источники (подробно: knowledge-base/00-input-normalization.md, §9):
* [TZDB-EU]  https://raw.githubusercontent.com/eggert/tz/main/europe — данные и комментарии
  IANA tzdb со ссылками на постановления СНК, Совмина СССР и правительства РФ.
* [TZDB-AS]  https://raw.githubusercontent.com/eggert/tz/main/asia
* [RUWIKI-DEKRET]  https://ru.wikipedia.org/wiki/Декретное_время
* [ASTRO21]  https://astro21.ru/tablitsa-chasovyh-popravok/ — таблица переходов на
  летнее время СССР/РФ 1981–2011 для астрологов (независимая сверка дат и часов).
* [ENWIKI-MSK]  https://en.wikipedia.org/wiki/Moscow_Time
* [PTB]  https://www.ptb.de/cms/en/ptb/fachabteilungen/abt4/fb-44/ag-441/realisation-of-legal-time-in-germany/dst-and-midsummer-dst-in-germany-until-1979.html
* [MEEUS]  J. Meeus, Astronomical Algorithms, 2nd ed., гл. 7 (юлианский день).

Тесты регрессии для ошибок, найденных при исследовании (разбор UTC+0530, DST-эвристика zoneinfo,
двойное летнее время, LMT места до 1919–1924, старый стиль) — исправления внесены в common/time.py.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest
import swisseph as swe

from calculators.common.time import (
    BirthInput,
    jd_to_utc,
    julian_day_ut,
    local_mean_time,
    normalize,
    true_solar_time,
)
from calculators.common.time import equation_of_time_minutes

# --------------------------------------------------------------------------- утилиты


def off(year, month, day, hour, minute=0, tz=None, place=None, fold=0, **kw) -> float:
    """Смещение от UTC (в часах), которое normalize() выдаёт для локального времени."""
    b = BirthInput(year, month, day, hour, minute, tz=tz, place=place, fold=fold, **kw)
    return normalize(b).utc_offset_hours


def utc_of(b: BirthInput) -> datetime:
    return normalize(b).utc


# --------------------------------------------------------------------------- T1–T4


class TestReferencePersons:
    """Эталонные персоны из CONVENTIONS.md."""

    def test_t1_moscow_1990_summer_time_utc_plus_4(self):
        # Летнее время 1990 в СССР: 25.03.1990 02:00 → 30.09.1990 03:00, Москва UTC+4.
        # [ASTRO21] строка «1990 | 25.03, 02:00 | 30.09, 03:00»; [TZDB-EU] Rule Russia 1985–2010.
        n = normalize(BirthInput(1990, 5, 15, 14, 30, place="Москва"))
        assert n.utc_offset_hours == 4.0
        assert n.utc == datetime(1990, 5, 15, 10, 30, tzinfo=timezone.utc)
        assert n.jd_ut == pytest.approx(2448026.9375, abs=1e-9)
        assert n.offset_source == "tzdb"
        assert any("летнее время" in w for w in n.warnings)

    def test_t2_moscow_1984_winter_utc_plus_3(self):
        # Февраль 1984: декретное время без летнего, MSK = UTC+3. [TZDB-EU], [ENWIKI-MSK]
        n = normalize(BirthInput(1984, 2, 4, 23, 30, place="Москва"))
        assert n.utc_offset_hours == 3.0
        assert n.utc == datetime(1984, 2, 4, 20, 30, tzinfo=timezone.utc)
        assert n.jd_ut == pytest.approx(2445735.3541667, abs=1e-6)
        assert n.warnings == []

    def test_t3_spb_2004_leap_day(self):
        # 29.02.2004 — зима, MSK = UTC+3 (летнее время 2004 началось 28.03). [ASTRO21], [TZDB-EU]
        n = normalize(BirthInput(2004, 2, 29, 8, 15, place="Санкт-Петербург"))
        assert n.utc_offset_hours == 3.0
        assert n.utc == datetime(2004, 2, 29, 5, 15, tzinfo=timezone.utc)
        assert n.jd_ut == pytest.approx(2453064.71875, abs=1e-9)

    def test_t4_einstein_lmt_astro_databank(self):
        # Astro-Databank / astro-seek: 14.03.1879 11:30 LMT, Ульм 48n24 10e00 → 10:50 UT
        # (поправка −0:40). https://www.astro.com/astro-databank/Einstein,_Albert
        # https://www.astro-seek.com/birth-chart/albert-einstein-horoscope
        # С долготой ровно 10°00′E получаем ровно 10:50:00 UT.
        n = normalize(BirthInput(1879, 3, 14, 11, 30, tz="LMT", lat=48.4, lon=10.0))
        assert n.utc == datetime(1879, 3, 14, 10, 50, tzinfo=timezone.utc)
        assert n.offset_source == "LMT(longitude)"

    def test_t4_einstein_lmt_exact_longitude(self):
        # С точной долготой Ульма 9.9876°E: 9.9876/15 ч = 0:39:57.0 → UT 10:50:03.0.
        n = normalize(BirthInput(1879, 3, 14, 11, 30, tz="LMT", lat=48.4011, lon=9.9876))
        assert n.utc_offset_hours * 3600 == pytest.approx(39 * 60 + 57.024, abs=0.01)
        assert abs((n.utc - datetime(1879, 3, 14, 10, 50, 2, 976000, tzinfo=timezone.utc)).total_seconds()) < 0.01

    def test_t4_tzdb_lmt_is_replaced_by_birthplace_longitude(self):
        # Europe/Berlin до 1893-04-01 — LMT Берлина +0:53:28 [TZDB-EU]. Для Ульма это
        # даёт ошибку ~13.5 мин; normalize() обязана подставить LMT по долготе места.
        n = normalize(BirthInput(1879, 3, 14, 11, 30, place="Ульм"))
        assert n.offset_source == "LMT(longitude)"
        assert n.utc_offset_hours == pytest.approx(9.9876 / 15.0, abs=1e-9)
        assert any("местное среднее время" in w for w in n.warnings)

    def test_t4_without_longitude_falls_back_to_zone_capital_with_warning(self):
        # Без долготы остаётся только LMT Берлина (+0:53:28): UTC 10:36:32. Такую ошибку
        # делают онлайн-калькуляторы; normalize() обязана предупредить.
        b = BirthInput(1879, 3, 14, 11, 30, tz="Europe/Berlin")
        n = normalize(b)
        assert n.utc_offset_hours * 3600 == pytest.approx(53 * 60 + 28, abs=1)
        assert any("LMT столицы зоны" in w for w in n.warnings)


# --------------------------------------------------------------------------- СССР / Россия


class TestMoscowHistory:
    def test_1922_1930_moscow_eet(self):
        # С 01.10.1922 по 21.06.1930 Москва жила по UTC+2 (поясное время II пояса).
        # [TZDB-EU] «3:00 Russia MSK/MSD 1922 Oct; 2:00 - EET 1930 Jun 21»; [ENWIKI-MSK]
        assert off(1925, 1, 1, 12, place="Москва") == 2.0

    def test_decree_time_21_06_1930(self):
        # Декретное время: часы переведены на 1 ч вперёд в 00:00 21.06.1930.
        # [RUWIKI-DEKRET]: «часы на всей территории СССР в 00:00 21 июня 1930 года были
        # переведены на 1 час вперёд»; [TZDB-EU].
        assert off(1930, 6, 20, 12, place="Москва") == 2.0
        assert off(1930, 6, 22, 12, place="Москва") == 3.0

    def test_1918_moscow_double_summer_time(self):
        # Декрет СНК № 497 (30.05.1918): с 31.05.1918 22:00 время +2 ч к московскому
        # среднему (MDST = +4:31:19). http://istmat.info/node/30001, цитируется в [TZDB-EU].
        assert off(1918, 7, 1, 12, place="Москва") * 3600 == pytest.approx(4 * 3600 + 31 * 60 + 19, abs=1)

    @pytest.mark.parametrize(
        "date_, expected",
        [
            # Первое советское летнее время: 01.04.1981 00:00 → 01.10.1981 00:00.
            # Постановление СМ СССР № 925 от 24.10.1980; [ASTRO21]; [TZDB-EU] Rule Russia 1981.
            ((1981, 3, 31, 12), 3.0),
            ((1981, 4, 1, 12), 4.0),
            ((1981, 9, 30, 12), 4.0),
            ((1981, 10, 1, 12), 3.0),
            # 1984: начало 01.04 00:00, конец — уже по новому правилу 30.09 03:00.
            ((1984, 9, 29, 12), 4.0),
            ((1984, 9, 30, 12), 3.0),
            # 1985: последнее воскресенье марта (31.03) 02:00. [ASTRO21]
            ((1985, 3, 30, 12), 3.0),
            ((1985, 3, 31, 12), 4.0),
            # 1996: окончание перенесено на последнее воскресенье октября (27.10). [ASTRO21]
            ((1996, 10, 26, 12), 4.0),
            ((1996, 10, 27, 12), 3.0),
        ],
    )
    def test_soviet_summer_time_switch_dates(self, date_, expected):
        assert off(*date_, place="Москва") == expected

    # Полная таблица переходов СССР/РФ 1981–2011 (Москва, местное время перевода):
    # [ASTRO21] — таблица «Переходы на летнее и зимнее время» (проверено 2026-10-14, совпадает
    # по всем датам и часам) и [TZDB-EU] Rule Russia 1981–2010. Формат: (весна, осень),
    # каждая — (Y, M, D, час перевода по часам ДО перевода).
    SOVIET_DST = {
        1981: ((1981, 4, 1, 0), (1981, 10, 1, 0)), 1982: ((1982, 4, 1, 0), (1982, 10, 1, 0)),
        1983: ((1983, 4, 1, 0), (1983, 10, 1, 0)), 1984: ((1984, 4, 1, 0), (1984, 9, 30, 3)),
        1985: ((1985, 3, 31, 2), (1985, 9, 29, 3)), 1986: ((1986, 3, 30, 2), (1986, 9, 28, 3)),
        1987: ((1987, 3, 29, 2), (1987, 9, 27, 3)), 1988: ((1988, 3, 27, 2), (1988, 9, 25, 3)),
        1989: ((1989, 3, 26, 2), (1989, 9, 24, 3)), 1990: ((1990, 3, 25, 2), (1990, 9, 30, 3)),
        1992: ((1992, 3, 29, 2), (1992, 9, 27, 3)), 1993: ((1993, 3, 28, 2), (1993, 9, 26, 3)),
        1994: ((1994, 3, 27, 2), (1994, 9, 25, 3)), 1995: ((1995, 3, 26, 2), (1995, 9, 24, 3)),
        1996: ((1996, 3, 31, 2), (1996, 10, 27, 3)), 1997: ((1997, 3, 30, 2), (1997, 10, 26, 3)),
        1998: ((1998, 3, 29, 2), (1998, 10, 25, 3)), 1999: ((1999, 3, 28, 2), (1999, 10, 31, 3)),
        2000: ((2000, 3, 26, 2), (2000, 10, 29, 3)), 2001: ((2001, 3, 25, 2), (2001, 10, 28, 3)),
        2002: ((2002, 3, 31, 2), (2002, 10, 27, 3)), 2003: ((2003, 3, 30, 2), (2003, 10, 26, 3)),
        2004: ((2004, 3, 28, 2), (2004, 10, 31, 3)), 2005: ((2005, 3, 27, 2), (2005, 10, 30, 3)),
        2006: ((2006, 3, 26, 2), (2006, 10, 29, 3)), 2007: ((2007, 3, 25, 2), (2007, 10, 28, 3)),
        2008: ((2008, 3, 30, 2), (2008, 10, 26, 3)), 2009: ((2009, 3, 29, 2), (2009, 10, 25, 3)),
        2010: ((2010, 3, 28, 2), (2010, 10, 31, 3)),
    }

    @pytest.mark.parametrize("year", sorted(SOVIET_DST))
    def test_full_dst_table_1981_2010(self, year):
        (sy, sm, sd, sh), (ay, am, ad, ah) = self.SOVIET_DST[year]
        spring = datetime(sy, sm, sd, sh)
        autumn = datetime(ay, am, ad, ah)
        moscow = lambda t: off(t.year, t.month, t.day, t.hour, t.minute, place="Москва")
        # весна: за полчаса до перевода ещё UTC+3, через полтора часа уже UTC+4
        assert moscow(spring - timedelta(minutes=30)) == 3.0
        assert moscow(spring + timedelta(minutes=90)) == 4.0
        # осень: за полтора часа до перевода ещё UTC+4 (вне повторяющегося часа), через полчаса — UTC+3
        assert moscow(autumn - timedelta(minutes=90)) == 4.0
        assert moscow(autumn + timedelta(minutes=30)) == 3.0

    @pytest.mark.parametrize(
        "date_, expected",
        [
            # 31.03.1991: декретный час отменён в момент перехода на летнее время —
            # стрелки в Москве НЕ переводились (UTC+3 до и после). [ASTRO21], [TZDB-EU]
            ((1991, 3, 30, 12), 3.0),
            ((1991, 7, 1, 12), 3.0),
            # 29.09.1991 03:00 → 02:00: зима 1991/92 в Москве = UTC+2. [ENWIKI-MSK], [TZDB-EU]
            ((1991, 12, 1, 12), 2.0),
            ((1992, 1, 18, 12), 2.0),
            # 19.01.1992 02:00: декретное время восстановлено (Пост. Правительства РФ
            # № 23 от 08.01.1992). [RUWIKI-DEKRET]: «Возврат декретного времени был
            # осуществлён 19 января 1992 года».
            ((1992, 1, 19, 12), 3.0),
            ((1992, 7, 1, 12), 4.0),
        ],
    )
    def test_1991_abolition_and_1992_restoration(self, date_, expected):
        assert off(*date_, place="Москва") == expected

    @pytest.mark.parametrize(
        "date_, expected",
        [
            # 27.03.2011 последний переход на летнее время, далее «вечное летнее» UTC+4;
            # 26.10.2014 02:00 возврат на UTC+3. ФЗ «Об исчислении времени» (2011) и поправки
            # 2014 г. (законопроект 431985-6); [ENWIKI-MSK]; [RUWIKI-DEKRET]; [TZDB-EU].
            ((2011, 3, 26, 12), 3.0),
            ((2011, 6, 15, 12), 4.0),
            ((2012, 1, 15, 12), 4.0),  # зимой 2011/12 стрелки не переводили
            ((2014, 10, 25, 12), 4.0),
            ((2014, 10, 26, 12), 3.0),
            ((2015, 6, 15, 12), 3.0),
            ((2024, 7, 1, 12), 3.0),
        ],
    )
    def test_2011_permanent_summer_and_2014_return(self, date_, expected):
        assert off(*date_, place="Москва") == expected


class TestRussianRegions:
    @pytest.mark.parametrize(
        "date_, expected",
        [
            # Самара: с 26.03.1989 на московском времени (Постановление СМ СССР № 227
            # от 14.03.1989, [TZDB-EU]); осенью 1991 стрелки назад не переводила и
            # 20.10.1991 вернулась в «свой» пояс UTC+4 ([RUWIKI-DEKRET]: Совмин РСФСР
            # «вернул региону прежний часовой пояс»); 2010–2011 — на МСК, с 27.03.2011 UTC+4,
            # в 2014 время не меняла ([RUWIKI-DEKRET]).
            ((1988, 7, 1, 12), 5.0),
            ((1990, 1, 15, 12), 3.0),
            ((1990, 7, 1, 12), 4.0),
            ((1991, 10, 5, 12), 3.0),
            ((1991, 12, 1, 12), 4.0),
            ((2010, 12, 1, 12), 3.0),
            ((2015, 1, 15, 12), 4.0),
        ],
    )
    def test_samara(self, date_, expected):
        assert off(*date_, place="Самара") == expected

    @pytest.mark.parametrize(
        "date_, expected",
        [
            # Новосибирск: декретное UTC+7; 23.05.1993 переход в UTC+6 (Shanks & Pottenger,
            # [TZDB-EU]); 2011–2014 UTC+7; 2014–2016 UTC+6; с 24.07.2016 UTC+7 (ФЗ,
            # http://publication.pravo.gov.ru/Document/View/0001201607040064).
            ((1990, 1, 15, 12), 7.0),
            ((1992, 7, 1, 12), 8.0),
            ((1994, 1, 15, 12), 6.0),
            ((2012, 1, 15, 12), 7.0),
            ((2015, 1, 15, 12), 6.0),
            ((2017, 1, 15, 12), 7.0),
        ],
    )
    def test_novosibirsk(self, date_, expected):
        assert off(*date_, place="Новосибирск") == expected

    def test_volgograd_2018_2020(self):
        # Волгоград: UTC+4 с 28.10.2018 (http://publication.pravo.gov.ru/Document/View/0001201810110037),
        # возврат на МСК 27.12.2020 (http://publication.pravo.gov.ru/Document/View/0001202012220002).
        assert off(2018, 7, 1, 12, place="Волгоград") == 3.0
        assert off(2019, 7, 1, 12, place="Волгоград") == 4.0
        assert off(2021, 7, 1, 12, place="Волгоград") == 3.0

    def test_kaliningrad_2011_2014(self):
        # Калининград: 2011–2014 UTC+3 без перевода, с 26.10.2014 UTC+2. [TZDB-EU]
        assert off(2012, 1, 15, 12, tz="Europe/Kaliningrad") == 3.0
        assert off(2015, 1, 15, 12, tz="Europe/Kaliningrad") == 2.0

    def test_yekaterinburg_decree(self):
        # Свердловск: V пояс + декретный час = UTC+5 зимой, UTC+6 летом 1990. [TZDB-EU]
        assert off(1990, 1, 15, 12, place="Свердловск") == 5.0
        assert off(1990, 7, 15, 12, place="Свердловск") == 6.0


class TestPostSovietStates:
    @pytest.mark.parametrize(
        "date_, expected",
        [
            # Киев: летом 1990 — московское летнее UTC+4; 01.07.1990 02:00 переход на
            # «II пояс + летнее» UTC+3 (Пост. СМ УССР № 134 от 18.06.1990); осенью 1990 и
            # весной 1991 стрелки не переводили (Пост. № 272 от 21.09.1990); 29.09.1991
            # 03:00 → UTC+2. Ссылки на постановления — [TZDB-EU], раздел Ukraine.
            ((1990, 5, 15, 12), 4.0),
            ((1990, 7, 2, 12), 3.0),
            ((1990, 12, 15, 12), 3.0),
            ((1991, 7, 1, 12), 3.0),
            ((1991, 12, 15, 12), 2.0),
            ((1992, 7, 1, 12), 3.0),
        ],
    )
    def test_kyiv_1990_1992(self, date_, expected):
        assert off(*date_, place="Киев") == expected

    def test_minsk_2011_permanent_utc3(self):
        # Беларусь с 27.03.2011 — UTC+3 круглый год (решение правительства 2011,
        # в 2014 за Россией не последовала). [TZDB-EU], раздел Belarus.
        assert off(2012, 1, 15, 12, place="Минск") == 3.0
        assert off(2015, 1, 15, 12, place="Минск") == 3.0

    def test_minsk_1990_no_summer_time(self):
        # В 1990 Минск без летнего времени (UTC+3): tzdb (Shanks & Pottenger) и вторичный
        # [RUWIKI-DEKRET]: «несколько регионов, в том числе Белоруссия, отказались от
        # сезонного перевода часов» (1990). Постановления не найдено.
        assert off(1990, 5, 15, 12, place="Минск") == 3.0

    def test_ashgabat_1991_tzdb_vs_wikipedia(self):
        # ⚠ Расхождение источников. tzdb (Shanks & Pottenger): Туркмения отменила декрет
        # 31.03.1991 вместе со всеми → зима 1991/92 UTC+4, с 19.01.1992 UTC+5.
        # [RUWIKI-DEKRET]: декрет отменён «кроме Туркменской ССР и западной части территории
        # Узбекской ССР» → зима 1991/92 была бы UTC+5. Тест фиксирует tzdb; KB §4.5 велит
        # считать обе версии.
        assert off(1991, 12, 1, 12, tz="Asia/Ashgabat") == 4.0
        assert off(1992, 2, 1, 12, tz="Asia/Ashgabat") == 5.0
        # Самарканд (запад Узбекистана) в tzdb декрет в 1991 не отменял — совпадает с вики.
        assert off(1991, 12, 1, 12, tz="Asia/Samarkand") == 5.0

    def test_almaty_2024_unification(self):
        # Казахстан перешёл на единый UTC+5 с 01.03.2024
        # (https://primeminister.kz/ru/decisions/19012024-20, цит. в [TZDB-AS]).
        assert off(2023, 6, 1, 12, place="Алматы") == 6.0
        assert off(2025, 6, 1, 12, place="Алматы") == 5.0

    def test_tashkent_1990_soviet_summer_time(self):
        # Ташкент: V пояс + декрет = UTC+6, летом 1990 UTC+7. [TZDB-AS]
        assert off(1990, 1, 15, 12, place="Ташкент") == 6.0
        assert off(1990, 7, 15, 12, place="Ташкент") == 7.0


# --------------------------------------------------------------------------- война


class TestWartime:
    def test_germany_summer_time_all_year_1940_1942(self):
        # Германия: летнее время непрерывно с 01.04.1940 02:00 до 02.11.1942 03:00. [PTB]
        assert off(1941, 1, 15, 12, place="Берлин") == 2.0

    def test_berlin_1945_midsummer_time(self):
        # Берлин и советская зона: 24.05.1945 — «двойное летнее» CEMT = UTC+3
        # (приказ Берзарина о московском времени). [PTB] (GHEP), [TZDB-EU].
        assert off(1945, 6, 15, 12, place="Берлин") == 3.0

    def test_kyiv_under_occupation_cet(self):
        # Оккупированный Киев: 20.09.1941 — 06.11.1943 по среднеевропейскому времени
        # (CEST летом, CET зимой). [TZDB-EU] Zone Europe/Kyiv.
        assert off(1942, 7, 1, 12, place="Киев") == 2.0
        assert off(1943, 1, 15, 12, place="Киев") == 1.0
        assert off(1944, 1, 15, 12, place="Киев") == 3.0  # после освобождения — MSK

    def test_minsk_under_occupation_cet(self):
        # Минск: 28.06.1941 — 03.07.1944 CET/CEST. [TZDB-EU] Zone Europe/Minsk.
        assert off(1943, 1, 15, 12, place="Минск") == 1.0
        assert off(1944, 8, 1, 12, place="Минск") == 3.0


# --------------------------------------------------------------------------- переводы часов


class TestDstEdges:
    def test_spring_forward_nonexistent_time_warns(self):
        # 25.03.1990 в 02:00 часы переведены на 03:00 — 02:30 не существовало. [ASTRO21]
        n = normalize(BirthInput(1990, 3, 25, 2, 30, place="Москва"))
        assert any("не существовало" in w for w in n.warnings)
        # По умолчанию (fold=0) берётся смещение ДО перехода (UTC+3).
        assert n.utc == datetime(1990, 3, 24, 23, 30, tzinfo=timezone.utc)

    def test_spring_forward_1981_midnight(self):
        # 01.04.1981 00:00 → 01:00: 00:30 не существовало. [TZDB-EU], [ASTRO21]
        n = normalize(BirthInput(1981, 4, 1, 0, 30, place="Москва"))
        assert any("не существовало" in w for w in n.warnings)

    def test_fall_back_ambiguous_time_warns_and_fold_selects(self):
        # 30.09.1990 в 03:00 часы переведены на 02:00 — 02:30 было дважды. [ASTRO21]
        n0 = normalize(BirthInput(1990, 9, 30, 2, 30, place="Москва", fold=0))
        n1 = normalize(BirthInput(1990, 9, 30, 2, 30, place="Москва", fold=1))
        assert any("неоднозначно" in w for w in n0.warnings)
        assert any("неоднозначно" in w for w in n1.warnings)
        assert n0.utc_offset_hours == 4.0  # первое прохождение (ещё летнее)
        assert n1.utc_offset_hours == 3.0  # второе прохождение (уже зимнее)
        assert (n1.utc - n0.utc) == timedelta(hours=1)

    def test_fall_back_1981_ambiguous_before_midnight(self):
        # 01.10.1981 00:00 → 30.09.1981 23:00: 23:30 30 сентября было дважды. [TZDB-EU]
        n = normalize(BirthInput(1981, 9, 30, 23, 30, place="Москва"))
        assert any("неоднозначно" in w for w in n.warnings)

    def test_kyiv_1990_07_01_ambiguous(self):
        # Киев 01.07.1990 02:00 MSD → 01:00 EEST: 01:30 было дважды. [TZDB-EU]
        n = normalize(BirthInput(1990, 7, 1, 1, 30, place="Киев"))
        assert any("неоднозначно" in w for w in n.warnings)

    def test_samara_1991_10_20_gap(self):
        # Самара 20.10.1991 03:00 → 04:00 (UTC+3 → UTC+4): 03:30 не существовало. [TZDB-EU]
        n = normalize(BirthInput(1991, 10, 20, 3, 30, place="Самара"))
        assert any("не существовало" in w for w in n.warnings)

    def test_moscow_1991_03_31_no_gap(self):
        # 31.03.1991: отмена декрета совпала с летним временем — разрыва нет. [ASTRO21]
        n = normalize(BirthInput(1991, 3, 31, 2, 30, place="Москва"))
        assert not any("не существовало" in w or "неоднозначно" in w for w in n.warnings)
        assert n.utc_offset_hours == 3.0

    def test_ordinary_time_has_no_transition_warning(self):
        n = normalize(BirthInput(1990, 9, 30, 12, 0, place="Москва"))
        assert not any("не существовало" in w or "неоднозначно" in w for w in n.warnings)


# --------------------------------------------------------------------------- LMT, ИСВ, JD


class TestSolarTimeAndJulianDay:
    def test_local_mean_time_is_utc_plus_longitude(self):
        # LMT = UTC + λ/15 ч; Москва 37.6173°E → +2:30:28.15.
        utc = datetime(1990, 5, 15, 10, 30, tzinfo=timezone.utc)
        assert local_mean_time(utc, 37.6173) == datetime(1990, 5, 15, 13, 0, 28, 152000)

    def test_local_mean_time_west_longitude_negative(self):
        # Западная долгота отрицательна: Нью-Йорк −74.0060° → −4:56:01.44.
        utc = datetime(2000, 1, 1, 12, 0, tzinfo=timezone.utc)
        assert local_mean_time(utc, -74.0060) == datetime(2000, 1, 1, 7, 3, 58, 560000)

    @pytest.mark.parametrize(
        "date_, lo, hi",
        [
            # Экстремумы уравнения времени (истинное − среднее): около 11–12 февраля
            # ≈ −14.2 мин, около 3 ноября ≈ +16.4 мин (Meeus, гл. 28; NOAA).
            ((2000, 2, 11, 12), -14.5, -14.0),
            ((2000, 11, 3, 12), 16.2, 16.6),
            # Нули около 15 апреля, 13 июня, 1 сентября, 25 декабря.
            ((2000, 4, 15, 12), -0.6, 0.6),
            ((2000, 12, 25, 12), -0.6, 0.6),
        ],
    )
    def test_equation_of_time_sign_and_extremes(self, date_, lo, hi):
        jd = swe.julday(*date_[:3], date_[3], swe.GREG_CAL)
        assert lo <= equation_of_time_minutes(jd) <= hi

    def test_true_solar_time_t2(self):
        # T2: UTC 20:30, λ=37.6173 → LMT 23:00:28; EoT(04.02.1984) ≈ −13.95 мин → ИСВ ≈ 22:46:31.
        # Важно для бацзы: по гражданскому времени 23:30 (час Цзы), по ИСВ — ещё час Хай.
        tst = true_solar_time(datetime(1984, 2, 4, 20, 30, tzinfo=timezone.utc), 37.6173)
        assert abs((tst - datetime(1984, 2, 4, 22, 46, 31)).total_seconds()) < 3

    def test_true_solar_time_t4(self):
        # T4: UTC 10:50:03, λ=9.9876 → LMT 11:30:00; EoT(14.03.1879) ≈ −9.4 мин → ИСВ ≈ 11:20:35.
        utc = datetime(1879, 3, 14, 10, 50, 2, 976000, tzinfo=timezone.utc)
        tst = true_solar_time(utc, 9.9876)
        assert abs((tst - datetime(1879, 3, 14, 11, 20, 35)).total_seconds()) < 3

    @pytest.mark.parametrize(
        "dt, jd",
        [
            # [MEEUS] пример 7.a: 1957 Oct 4.81 = JD 2436116.31
            (datetime(1957, 10, 4, 19, 26, 24, tzinfo=timezone.utc), 2436116.31),
            # Эпоха J2000.0: 2000-01-01 12:00 → 2451545.0 [MEEUS], гл. 7
            (datetime(2000, 1, 1, 12, 0, tzinfo=timezone.utc), 2451545.0),
            # [MEEUS] таблица 7: 1987 Jun 19.5 = 2446966.0; 1600 Jan 1.0 = 2305447.5
            (datetime(1987, 6, 19, 12, 0, tzinfo=timezone.utc), 2446966.0),
            (datetime(1600, 1, 1, 0, 0, tzinfo=timezone.utc), 2305447.5),
        ],
    )
    def test_julian_day_reference_values(self, dt, jd):
        assert julian_day_ut(dt) == pytest.approx(jd, abs=1e-6)

    def test_jd_roundtrip(self):
        dt = datetime(1990, 5, 15, 10, 30, tzinfo=timezone.utc)
        back = jd_to_utc(julian_day_ut(dt))
        assert abs((back - dt).total_seconds()) < 0.01

    def test_delta_t_magnitude_1990(self):
        # ΔT(1990.4) ≈ 57 с (полином Espenak–Meeus: 57.1 с,
        # https://eclipse.gsfc.nasa.gov/SEhelp/deltatpoly2004.html).
        dt_sec = swe.deltat(2448026.9375) * 86400
        assert 56.0 < dt_sec < 58.5

    def test_julian_to_gregorian_rule_1918(self):
        # Декрет СНК от 24.01.1918: после 31.01.1918 (ст. ст.) следует 14.02.1918 (н. ст.),
        # т.е. 31.01 ст. ст. = 13.02 н. ст. (разница 13 дней).
        # https://en.wikipedia.org/wiki/Adoption_of_the_Gregorian_calendar
        jd = swe.julday(1918, 1, 31, 12.0, swe.JUL_CAL)
        assert swe.revjul(jd, swe.GREG_CAL)[:3] == (1918, 2, 13)
        # Граница 12/13 дней: 28.02.1900 ст. ст. = 12.03 н. ст.; 01.03.1900 ст. ст. = 14.03 н. ст.
        assert swe.revjul(swe.julday(1900, 2, 28, 12.0, swe.JUL_CAL), swe.GREG_CAL)[:3] == (1900, 3, 12)
        assert swe.revjul(swe.julday(1900, 3, 1, 12.0, swe.JUL_CAL), swe.GREG_CAL)[:3] == (1900, 3, 14)


# --------------------------------------------------------------------------- ввод


class TestInputValidation:
    def test_missing_time_raises(self):
        with pytest.raises(ValueError):
            normalize(BirthInput(1990, 5, 15, place="Москва"))

    def test_missing_tz_raises(self):
        with pytest.raises(ValueError):
            normalize(BirthInput(1990, 5, 15, 12, 0))

    def test_fixed_offset_with_colon(self):
        n = normalize(BirthInput(2000, 1, 1, 12, 0, tz="UTC+05:30"))
        assert n.utc_offset_hours == 5.5
        assert n.offset_source == "fixed"

    def test_fixed_offset_negative(self):
        assert normalize(BirthInput(2000, 1, 1, 12, 0, tz="UTC-03:30")).utc_offset_hours == -3.5


# --------------------------------------------------------------------------- найденные ошибки


class TestFixedBugs:
    """Регрессия для ошибок, найденных при исследовании и исправленных в common/time.py
    (KB 00, §6.4 и приложение А)."""

    def test_fixed_offset_hhmm_without_colon(self):
        assert normalize(BirthInput(2000, 1, 1, 12, 0, tz="UTC+0530")).utc_offset_hours == 5.5

    def test_dst_warning_never_negative(self):
        n = normalize(BirthInput(1942, 7, 1, 12, 0, place="Киев"))
        assert not any("-1 day" in w for w in n.warnings)

    def test_double_summer_time_warning_shows_two_hours(self):
        # [PTB]: 24.05–24.09.1945 Берлин/советская зона — CEMT (UT+3 = CET+2).
        n = normalize(BirthInput(1945, 6, 15, 12, 0, place="Берлин"))
        assert any("2:00:00" in w or "2 ч" in w for w in n.warnings)

    def test_spb_1900_uses_birthplace_mean_time(self):
        # Петербург жил по своему среднему (пулковскому) времени 2:01:18.7
        # (Karpinsky / Бялокоз 1919, цит. в [TZDB-EU]); λ=30.3351° → 2:01:20.4.
        n = normalize(BirthInput(1900, 1, 1, 12, 0, place="Санкт-Петербург"))
        assert n.utc_offset_hours * 3600 == pytest.approx(30.3351 / 15 * 3600, abs=60)

    def test_julian_calendar_input(self):
        # 2 марта 1879 ст. ст. = 14 марта 1879 н. ст.
        b = BirthInput(1879, 3, 2, 11, 30, tz="LMT", lat=48.4011, lon=9.9876, calendar="julian")  # type: ignore[call-arg]
        assert (b.year, b.month, b.day) == (1879, 3, 14)

    def test_invalid_julian_date_raises(self):
        # swe.julday() молча перекатывает «30.02» в март — BirthInput обязан отвергнуть такую дату.
        # 29.02.1900 по ст. ст. существует (1900 — високосный по юлианскому календарю).
        for bad in [(1900, 2, 30), (1900, 4, 31), (1899, 2, 29), (1900, 13, 1)]:
            with pytest.raises(ValueError):
                BirthInput(*bad, calendar="julian")
        assert BirthInput(1900, 2, 29, calendar="julian").date.isoformat() == "1900-03-13"

    def test_invalid_gregorian_date_raises_early(self):
        # Методы «по дате» (нумерология) не вызывают normalize(): «30.02» должно падать сразу.
        with pytest.raises(ValueError):
            BirthInput(1990, 2, 30)

    def test_calendar_name_case_insensitive(self):
        assert BirthInput(1799, 5, 26, calendar="Julian").date.isoformat() == "1799-06-06"

    def test_latvia_1922_national_mean_time_warning(self):
        # Независимая Латвия 1918–1926: RMT (+1:36:34) могло быть законным временем всей страны
        # (tzdb europe: «Byalokoz 1919 says Latvia was 1:36:34»). Для Даугавпилса (26.53°E)
        # normalize() берёт LMT места, но обязан предложить вариант по RMT.
        n = normalize(BirthInput(1922, 6, 1, 12, 0, tz="Europe/Riga", lat=55.87, lon=26.53))
        assert n.offset_source == "LMT(longitude)"
        assert any("UTC+01:36:34" in w for w in n.warnings)
        # до независимости (Российская империя) такого предупреждения нет
        n = normalize(BirthInput(1910, 6, 1, 12, 0, tz="Europe/Riga", lat=55.87, lon=26.53))
        assert not any("UTC+01:36:34" in w for w in n.warnings)


# --------------------------------------------------------------------------- старый стиль


class TestJulianCalendar:
    @pytest.mark.parametrize(
        "julian, gregorian",
        [
            # Пушкин: «26 мая [6 июня] 1799» — https://ru.wikipedia.org/wiki/Пушкин,_Александр_Сергеевич
            ((1799, 5, 26), (1799, 6, 6)),
            # Толстой: «28 августа [9 сентября] 1828» — https://ru.wikipedia.org/wiki/Толстой,_Лев_Николаевич
            ((1828, 8, 28), (1828, 9, 9)),
            # Ленин: «10 (22) апреля 1870» — https://ru.wikipedia.org/wiki/Ленин,_Владимир_Ильич
            ((1870, 4, 10), (1870, 4, 22)),
            # Шостакович: «12 (25) сентября 1906» — https://ru.wikipedia.org/wiki/Шостакович,_Дмитрий_Дмитриевич
            ((1906, 9, 12), (1906, 9, 25)),
            # Королёв: «30 декабря 1906 [12 января 1907]» — смена года при пересчёте.
            # https://ru.wikipedia.org/wiki/Королёв,_Сергей_Павлович
            ((1906, 12, 30), (1907, 1, 12)),
            # Последний день ст. ст. в РСФСР: 31.01.1918 → следующий день 14.02.1918.
            # Декрет СНК: «Первый день после 31 января сего года считать не 1 февраля, а 14 февраля»
            # https://ru.wikipedia.org/wiki/Декрет_о_введении_в_Российской_республике_западноевропейского_календаря
            ((1918, 1, 31), (1918, 2, 13)),
        ],
    )
    def test_famous_old_style_dates(self, julian, gregorian):
        b = BirthInput(*julian, calendar="julian")
        assert (b.year, b.month, b.day) == gregorian
        assert b.julian_date == julian

    @pytest.mark.parametrize(
        "julian, gregorian",
        [
            # Границы Δ (KB §3.1): Δ меняется на юлианском 29 февраля вековых лет,
            # невисокосных по григорианскому календарю. Проверено swe.julday/revjul.
            ((1700, 2, 28), (1700, 3, 10)), ((1700, 2, 29), (1700, 3, 11)),   # 10 → 11
            ((1800, 2, 28), (1800, 3, 11)), ((1800, 2, 29), (1800, 3, 12)),   # 11 → 12
            ((1900, 2, 28), (1900, 3, 12)), ((1900, 2, 29), (1900, 3, 13)),   # 12 → 13
            ((2100, 2, 28), (2100, 3, 13)), ((2100, 2, 29), (2100, 3, 14)),   # 13 → 14
            ((1582, 10, 4), (1582, 10, 14)), ((1582, 10, 5), (1582, 10, 15)),  # 1582: Δ = 10
        ],
    )
    def test_delta_boundaries(self, julian, gregorian):
        b = BirthInput(*julian, calendar="julian")
        assert (b.year, b.month, b.day) == gregorian

    def test_julian_input_survives_dataclass_replace(self):
        # После пересчёта calendar = "gregorian", поэтому replace() не сдвигает дату повторно.
        import dataclasses

        b = BirthInput(1870, 4, 10, 12, 0, calendar="julian")
        b2 = dataclasses.replace(b, hour=13)
        assert (b2.year, b2.month, b2.day) == (1870, 4, 22)
        assert b2.julian_date == (1870, 4, 10)
