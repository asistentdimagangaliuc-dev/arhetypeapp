"""Межмодульная проверка: год по Личуню одинаков в Ба-цзы (01), Ки/зодиаке (03) и Гуа (03 = 12).

Особенно важен случай «время неизвестно, дата — день Личуня»: все модули считают такой день
уже новым годом (соглашение задокументировано в 01, 03 и 12).
"""
import pytest

from calculators import bazi, ninestar, tarot_loshu
from calculators.common.time import BirthInput

CASES = [(y, 2, d, place) for y in range(1980, 2031, 3) for d in (3, 4, 5) for place in ("Москва", "Пекин", "Нью-Йорк")]


@pytest.mark.parametrize("y,m,d,place", CASES)
def test_year_pillar_matches_ninestar_without_time(y, m, d, place):
    b = BirthInput(y, m, d, place=place, gender="male")
    assert bazi.calculate(b)["pillars"]["year"]["ganzhi"] == ninestar.calculate(b)["zodiac_solar"]["ganzhi"]


@pytest.mark.parametrize("hh", [10, 20])
def test_year_and_gua_on_li_chun_day_with_time(hh):
    # 04.02.1984: Личунь около 18:19 MSK — до него 1983 (癸亥), после — 1984 (甲子)
    b = BirthInput(1984, 2, 4, hh, 0, place="Москва", gender="male")
    expected = "癸亥" if hh == 10 else "甲子"
    assert bazi.calculate(b)["pillars"]["year"]["ganzhi"] == expected
    assert ninestar.calculate(b)["zodiac_solar"]["ganzhi"] == expected
    assert ninestar.calculate(b)["gua"]["number"] == tarot_loshu.calculate(b)["loshu"]["kua"]["number"]
