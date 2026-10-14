"""Перекрёстная сверка Дизайна Человека (calculators/human_design.py) и Генных ключей
(calculators/gene_keys.py).

Оба модуля строятся на одной астрономии (тропический зодиак, Дизайн = Солнце −88° дуги,
колесо 64 ворот/ключей от 302°), но таблицу колеса и функцию «долгота → ворота.линия»
реализуют независимо (gene_keys.py намеренно не импортирует human_design.py).
Поэтому для каждого общего тела (Солнце, Земля, Луна, Меркурий…Уран; узлы в Gene Keys
не используются) ворота.линия должны совпасть, а каждая сфера Gene Keys должна равняться
активации HD той же стороны (Личность/Дизайн) и того же тела.

Карта «сфера → сторона/тело» взята с официальной страницы
https://genekeys.com/docs/what-planets-does-each-sphere-of-the-golden-path-profile-correlate-to/
(обновлено 15.12.2024; проверено WebFetch 2026-10-14).

Запуск: .venv/bin/python -m pytest calculators/tests/test_cross_hd_gk.py -q
"""
from __future__ import annotations

import random

import pytest

from calculators import gene_keys as gk
from calculators import human_design as hd
from calculators.common.time import BirthInput

# Тела, общие для обоих модулей (у Gene Keys нет узлов, Нептуна и Плутона).
SHARED_BODIES = ["sun", "earth", "moon", "mercury", "venus", "mars", "jupiter", "saturn", "uranus"]

# Официальная таблица genekeys.com (12.2024): сфера → (сторона, тело).
OFFICIAL_SPHERE_SOURCE = {
    "lifes_work": ("personality", "sun"), "brand": ("personality", "sun"),
    "evolution": ("personality", "earth"),
    "radiance": ("design", "sun"), "purpose": ("design", "earth"),
    "attraction": ("design", "moon"),
    "iq": ("personality", "venus"), "eq": ("personality", "mars"),
    "sq": ("design", "venus"),
    "core": ("design", "mars"), "vocation": ("design", "mars"),
    "culture": ("design", "jupiter"), "pearl": ("personality", "jupiter"),
    # «последовательности в разработке» той же таблицы
    "relating": ("personality", "mercury"), "stability": ("design", "saturn"),
    "creativity": ("design", "uranus"),
}

T_PERSONS = {
    "T1": BirthInput(1990, 5, 15, 14, 30, place="Москва"),
    "T2": BirthInput(1984, 2, 4, 23, 30, place="Москва"),
    "T3": BirthInput(2004, 2, 29, 8, 15, place="Санкт-Петербург"),
    "T4": BirthInput(1879, 3, 14, 11, 30, tz="LMT", lat=48.4011, lon=9.9876),
}

_ZONES = ["Europe/Moscow", "America/New_York", "Asia/Tokyo", "Australia/Sydney", "Europe/Berlin",
          "America/Los_Angeles", "Asia/Kolkata", "UTC+00:00"]


def _random_persons(n: int = 20, seed: int = 20261014) -> dict[str, BirthInput]:
    """20 случайных дат 1900–2030 (фиксированное зерно — тест воспроизводим)."""
    rnd = random.Random(seed)
    out = {}
    for k in range(n):
        y, m = rnd.randint(1900, 2030), rnd.randint(1, 12)
        d = rnd.randint(1, 28)
        hh, mm = rnd.randint(0, 23), rnd.randint(0, 59)
        tz = _ZONES[k % len(_ZONES)]
        out[f"R{k:02d}_{y}-{m:02d}-{d:02d}T{hh:02d}:{mm:02d}_{tz}"] = BirthInput(y, m, d, hh, mm, tz=tz)
    return out


ALL_PERSONS = {**T_PERSONS, **_random_persons()}


def test_sphere_table_matches_official_genekeys_docs():
    table = {s["id"]: (s["side"], s["body"]) for s in gk.SPHERES + gk.EXTENDED_SPHERES}
    assert table == OFFICIAL_SPHERE_SOURCE


def test_wheel_tables_identical():
    assert gk.GATE_ORDER == hd.GATE_ORDER
    assert gk.WHEEL_START_DEG == hd.WHEEL_START
    assert gk.KEY_ARC == hd.GATE_SPAN and gk.LINE_ARC == hd.LINE_SPAN
    # программный партнёр Gene Keys = ворота напротив (Земля к Солнцу) в HD
    for g in range(1, 65):
        assert gk.programming_partner(g) == hd.GATE_ORDER[(hd.GATE_INDEX[g] + 32) % 64]


def test_longitude_mapping_identical_random_and_boundaries():
    rnd = random.Random(64)
    lons = [rnd.uniform(0.0, 360.0) for _ in range(20000)]
    # все границы линий (384 шт.) и точки в 1e-7° по обе стороны от них
    for i in range(64 * 6):
        b = (302.0 + i * hd.LINE_SPAN) % 360.0
        lons += [b, (b + 1e-7) % 360.0, (b - 1e-7) % 360.0]
    for lon in lons:
        a = hd.longitude_to_activation(lon)
        k = gk.key_line_from_longitude(lon)
        assert (a["gate"], a["line"]) == (k["key"], k["line"]), lon


@pytest.mark.parametrize("pid", list(ALL_PERSONS))
def test_same_gate_line_for_shared_bodies(pid):
    b = ALL_PERSONS[pid]
    rh = hd.calculate(b)
    rg = gk.calculate(b)
    # один и тот же момент рождения и момент Дизайна
    assert rh["inputs_used"]["jd_ut"] == pytest.approx(rg["inputs_used"]["jd_ut"], abs=1e-6)
    assert rh["inputs_used"]["jd_design"] == pytest.approx(rg["inputs_used"]["design_jd_ut"], abs=1e-6)
    for side in ("personality", "design"):
        for body in SHARED_BODIES:
            h = rh[side][body]
            g = rg[side]["bodies"][body]
            assert g["lon"] == pytest.approx(h["lon"], abs=1e-6), (pid, side, body)
            assert (g["key"], g["line"]) == (h["gate"], h["line"]), (pid, side, body)


@pytest.mark.parametrize("pid", list(ALL_PERSONS))
def test_spheres_equal_hd_activations(pid):
    b = ALL_PERSONS[pid]
    rh = hd.calculate(b)
    rg = gk.calculate(b)
    short = {"personality": rh["personality_short"], "design": rh["design_short"]}
    for sid, (side, body) in OFFICIAL_SPHERE_SOURCE.items():
        assert rg["profile"][sid] == short[side][body], (pid, sid)
    # Дело жизни/Эволюция = крест HD (Солнце/Земля Личности), Сияние/Предназначение — Дизайна
    cr = rh["incarnation_cross"]["gates"]
    assert int(rg["profile"]["lifes_work"].split(".")[0]) == cr["personality_sun"]
    assert int(rg["profile"]["evolution"].split(".")[0]) == cr["personality_earth"]
    assert int(rg["profile"]["radiance"].split(".")[0]) == cr["design_sun"]
    assert int(rg["profile"]["purpose"].split(".")[0]) == cr["design_earth"]
    # линии Дела жизни и Сияния = профиль HD (линия Солнца Личности / Дизайна)
    p_line, d_line = (int(x) for x in rh["profile"]["profile"].split("/"))
    assert rg["spheres"]["lifes_work"]["line"] == p_line
    assert rg["spheres"]["radiance"]["line"] == d_line


def test_core_functions_agree_on_random_jd():
    """Ядро без нормализации времени: chart_from_jd (HD) против profile_for_jd (GK)."""
    rnd = random.Random(88)
    for _ in range(60):
        jd = rnd.uniform(2415020.5, 2462502.5)          # 1900–2030
        ch = hd.chart_from_jd(jd)
        pr = gk.profile_for_jd(jd)
        assert pr["jd_design"] == pytest.approx(ch["jd_design"], abs=1e-9)
        sides = {"personality": ch["personality"], "design": ch["design"]}
        for sid, (side, body) in OFFICIAL_SPHERE_SOURCE.items():
            assert pr["spheres"][sid] == sides[side][body]["gate_line"], (jd, sid)
