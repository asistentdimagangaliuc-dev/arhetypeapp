"""Тесты калькулятора Дизайна Человека (calculators/human_design.py).

Источники эталонов:
* OFFICIAL — официальный движок Jovian Archive / MyBodyGraph (Maia Mechanics):
  POST https://charts.maiamechanics.com/api/charts/free-chart  (его вызывает
  https://app.mybodygraph.com/free-chart, ссылка со страницы
  https://jovianarchive.com/pages/get-your-human-design-chart); запросы сделаны 2026-10-14
  с полем time в UTC (движок отбрасывает секунды). Сохранены ворота.линия.цвет.тон.база всех
  26 активаций, тип, авторитет, определённость, профиль, крест, переменные.
* TOTALHD — опубликованные карты https://totalhumandesign.com/design/<имя> (независимый сайт).
* Таблицы градусов ворот: https://www.barneyandflow.com/gate-zodiac-degrees ,
  https://bonniesorsby.com/human-design-gates-by-degree/
* Список 192 крестов: словарь приложения https://app.mybodygraph.com (js/app.*.js), совпадает с
  https://thehumandesignsystem.com/crosses и https://humandesign4all.com/incarnation-cross-in-human-design/
"""
from __future__ import annotations

import json
import re
from datetime import datetime, timezone

import pytest

from calculators.common.ephemeris import sun_longitude
from calculators.common.time import BirthInput, julian_day_ut
from calculators.human_design import (
    CENTERS, CHANNELS, GATE_INDEX, GATE_ORDER, GATES, PLANETS, QUARTERS, RAX_FAMILIES,
    VALID_PROFILES, _quarter_index, analyze_gates, calculate, chart_from_jd, design_moment, gate_start_longitude,
    incarnation_cross, longitude_to_activation, profile_angle,
)

# ---------------------------------------------------------------------------
# Эталонные персоны
# ---------------------------------------------------------------------------
T1 = BirthInput(1990, 5, 15, 14, 30, place="Москва")
T2 = BirthInput(1984, 2, 4, 23, 30, place="Москва")
T3 = BirthInput(2004, 2, 29, 8, 15, place="Санкт-Петербург")
T4 = BirthInput(1879, 3, 14, 11, 30, tz="LMT", lat=48.4011, lon=9.9876)
OBAMA = BirthInput(1961, 8, 4, 19, 24, tz="Pacific/Honolulu", lat=21.3069, lon=-157.8583)
JOBS = BirthInput(1955, 2, 24, 19, 15, tz="America/Los_Angeles", lat=37.7749, lon=-122.4194)
TRUMP = BirthInput(1946, 6, 14, 10, 54, tz="America/New_York", lat=40.7028, lon=-73.8152)

# ---------------------------------------------------------------------------
# OFFICIAL: момент UTC, отправленный в движок (с точностью до минуты), и его ответ.
# Строки P/D: 13 активаций в порядке PLANETS (Солнце, Земля, Луна, С.узел, Ю.узел, Меркурий,
# Венера, Марс, Юпитер, Сатурн, Уран, Нептун, Плутон), формат ворота.линия.цвет.тон.база.
# e_* — граничные случаи, найденные перебором и подтверждённые официальным движком.
# ---------------------------------------------------------------------------
OFFICIAL_UTC = {
    "einstein": "1879-03-14T10:50", "t1": "1990-05-15T10:30", "t2": "1984-02-04T20:30",
    "t3": "2004-02-29T05:15", "obama": "1961-08-05T05:24", "jobs": "1955-02-25T03:15",
    "trump": "1946-06-14T14:54", "e_reflector": "1909-01-30T20:10", "e_sacral": "1984-08-15T08:17",
    "e_egoman": "1942-02-06T01:34", "e_egoproj": "1966-08-01T04:40", "e_selfproj": "1940-02-08T04:18",
    "e_mental": "2027-06-04T04:07", "e_triple": "2007-06-29T04:17", "e_quad": "1950-02-25T22:57",
    "e_juxt": "1975-01-09T17:07", "e_manroot": "1959-07-25T04:06",
    # верификация (волна 2), запрос 2026-10-14: payload {"time": "...Z", "timeInUtc": true, ...};
    # Сердце→G (25-51) → Горло (1-8, 7-31) без 21-45: Манифестор + Эго-манифестированный
    "e_egoman_g": "1963-07-26T22:42",
}
OFFICIAL = {
    "einstein": {
        "P": "36.1.6.4.5 6.1.6.4.5 5.4.3.1.5 41.1.5.5.1 31.1.5.5.1 25.6.2.2.5 51.2.6.6.3 60.1.4.3.4 30.4.2.1.3 17.1.3.1.1 59.2.2.3.4 24.1.2.4.3 8.1.2.3.4",
        "D": "11.4.1.3.4 12.4.1.3.4 46.3.5.4.3 41.3.6.3.4 31.3.6.3.4 38.3.4.5.2 10.1.1.4.4 14.1.5.6.4 41.6.5.4.1 36.5.1.3.1 59.5.3.1.5 27.6.4.5.3 8.1.3.6.3",
        "type": "generator", "authority": "emotional", "definition": "split",
        "profile": "1/4", "variables": "PRR DLL",
        "cross": "Right Angle Cross of Eden (36/6 | 11/12)",
    },
    "t1": {
        "P": "23.6.5.6.4 43.6.5.6.4 60.1.1.1.3 19.3.5.6.1 33.3.5.6.1 24.1.3.4.1 21.4.3.5.4 22.2.3.2.3 39.1.1.2.1 61.5.5.5.5 58.6.4.6.5 38.6.2.1.2 1.4.1.5.1",
        "D": "30.2.6.5.3 29.2.6.5.3 50.4.1.4.1 13.4.3.2.4 7.4.3.2.4 41.3.4.6.2 61.2.2.1.1 38.3.5.4.5 15.3.6.3.1 61.1.1.1.5 58.5.4.5.5 38.5.3.3.1 1.5.6.1.1",
        "type": "projector", "authority": "emotional", "definition": "split",
        "profile": "6/2", "variables": "PRR DRL",
        "cross": "Left Angle Cross of Dedication (23/43 | 30/29)",
    },
    "t2": {
        "P": "13.3.1.4.4 7.3.1.4.4 63.6.3.1.2 35.3.4.2.1 5.3.4.2.1 61.4.3.3.5 38.4.1.2.2 44.5.4.6.3 10.6.3.4.3 1.3.6.6.3 5.2.3.6.5 10.3.3.4.4 28.1.1.6.2",
        "D": "1.5.2.3.3 2.5.2.3.3 54.6.4.1.2 35.6.1.6.2 5.6.1.6.2 43.5.6.5.1 46.3.5.2.1 6.3.4.6.5 5.4.1.6.2 44.1.6.2.1 9.3.3.4.3 11.6.2.1.5 50.5.1.2.4",
        "type": "projector", "authority": "splenic", "definition": "single",
        "profile": "3/5", "variables": "PRL DLR",
        "cross": "Right Angle Cross of The Sphinx (13/7 | 1/2)",
    },
    "t3": {
        "P": "37.5.3.6.4 40.5.3.6.4 45.5.6.3.5 2.1.2.6.2 1.1.2.6.2 37.1.6.5.1 42.4.2.3.4 2.4.3.4.5 64.4.2.6.3 52.3.4.5.3 55.4.2.4.5 13.1.4.6.3 26.6.3.4.1",
        "D": "5.1.4.5.3 35.1.4.5.3 42.5.6.3.5 23.2.4.6.1 43.2.4.6.1 10.5.1.5.5 58.6.5.5.3 36.1.4.6.2 47.1.3.6.4 39.3.4.1.4 30.5.6.6.5 19.4.3.6.5 26.3.4.5.4",
        "type": "manifestor", "authority": "emotional", "definition": "single",
        "profile": "5/1", "variables": "PRR DRR",
        "cross": "Left Angle Cross of Migration (37/40 | 5/35)",
    },
    "obama": {
        "P": "33.6.2.4.1 19.6.2.4.1 20.4.3.5.1 29.3.6.6.4 30.3.6.6.4 31.1.3.1.4 15.4.5.4.5 47.6.6.5.1 60.5.5.5.1 61.5.6.2.5 29.1.5.6.3 44.2.1.2.4 40.2.2.6.1",
        "D": "2.2.3.2.5 1.2.3.2.5 38.5.1.2.4 59.4.3.3.3 55.4.3.3.3 2.6.4.5.2 21.4.4.6.3 56.4.3.5.2 41.5.5.5.4 60.4.5.2.1 4.3.6.6.2 44.3.3.1.2 59.6.5.6.2",
        "type": "projector", "authority": "emotional", "definition": "single",
        "profile": "6/2", "variables": "PRR DLL",
        "cross": "Left Angle Cross of Refinement (33/19 | 2/1)",
    },
    "jobs": {
        "P": "55.6.6.6.5 59.6.6.6.5 17.5.1.5.4 10.6.4.1.1 15.6.4.1.1 13.2.2.1.4 61.1.3.5.1 3.3.6.3.2 53.6.5.3.4 43.3.3.4.5 62.4.4.4.5 50.2.5.5.2 29.1.6.2.3",
        "D": "9.3.1.5.4 16.3.1.5.4 41.1.6.5.5 58.2.6.5.4 52.2.6.5.4 43.6.4.5.5 1.3.1.6.4 30.3.6.6.1 56.4.3.6.3 1.2.6.5.4 56.2.1.3.4 50.1.6.4.5 29.3.3.5.2",
        "type": "generator", "authority": "emotional", "definition": "split",
        "profile": "6/3", "variables": "PRL DRR",
        "cross": "Left Angle Cross of Spirit (55/59 | 9/16)",
    },
    "trump": {
        "P": "12.1.2.6.4 11.1.2.6.4 26.5.3.6.3 45.5.1.3.1 26.5.1.3.1 52.6.2.6.2 62.6.2.6.3 29.3.3.4.2 57.3.3.6.2 62.4.2.4.4 45.1.6.5.2 18.3.1.4.3 33.3.4.3.5",
        "D": "36.3.3.5.3 6.3.3.5.3 59.6.3.3.1 12.4.2.1.3 11.4.2.1.3 21.1.5.3.4 17.2.4.2.2 53.2.6.1.2 32.6.2.6.3 53.4.1.2.1 35.3.3.4.4 18.4.6.5.5 33.3.2.3.5",
        "type": "manifesting_generator", "authority": "emotional", "definition": "single",
        "profile": "1/3", "variables": "PRL DRL",
        "cross": "Right Angle Cross of Eden (12/11 | 36/6)",
    },
    "e_reflector": {
        "P": "19.3.6.3.1 33.3.6.3.1 16.2.6.2.1 12.3.5.1.1 11.3.5.1.1 30.4.4.4.5 54.4.4.6.1 5.3.4.2.5 64.2.5.3.2 17.3.2.2.5 54.4.3.4.2 39.6.6.4.3 12.2.4.1.4",
        "D": "44.6.1.1.5 24.6.1.1.5 25.2.4.6.4 12.5.4.1.4 11.5.4.1.4 50.2.5.6.3 46.4.6.6.1 57.2.5.1.4 40.5.4.3.2 17.1.3.3.1 38.5.4.1.3 53.3.1.2.5 12.4.1.5.5",
        "type": "reflector", "authority": "lunar", "definition": "none",
        "profile": "3/6", "variables": "PLL DLL",
        "cross": "Right Angle Cross of The Four Ways (19/33 | 44/24)",
    },
    "e_sacral": {
        "P": "4.5.1.2.5 49.5.1.2.5 25.6.3.5.3 20.3.5.6.3 34.3.5.6.3 64.3.1.6.1 40.4.5.3.4 14.5.3.6.3 10.6.4.3.1 44.4.1.6.2 9.5.1.2.2 10.1.4.5.1 50.4.4.2.4",
        "D": "8.1.2.1.4 14.1.2.1.4 14.3.3.1.2 16.1.6.1.5 9.1.6.1.5 3.4.5.3.2 2.4.1.4.3 43.1.4.3.3 38.4.2.5.3 44.5.6.2.1 5.1.6.5.4 10.3.6.3.1 50.4.6.5.2",
        "type": "manifesting_generator", "authority": "sacral", "definition": "single",
        "profile": "5/1", "variables": "PLR DLL",
        "cross": "Left Angle Cross of Revolution (4/49 | 8/14)",
    },
    "e_egoman": {
        "P": "13.4.4.5.1 7.4.4.5.1 48.5.4.1.1 64.3.3.1.4 63.3.3.1.4 30.1.2.4.2 19.4.5.6.5 24.6.6.6.2 35.1.1.1.3 23.4.1.5.4 8.2.6.6.1 46.2.3.2.2 31.3.4.2.1",
        "D": "1.6.5.3.5 2.6.5.3.5 33.3.1.3.4 47.5.1.3.3 22.5.1.3.3 50.4.3.5.1 58.2.4.5.5 21.2.5.1.4 45.3.6.5.2 8.2.1.6.3 8.5.4.1.4 46.1.6.6.1 31.5.1.2.2",
        "type": "manifestor", "authority": "ego_manifested", "definition": "split",
        "profile": "4/6", "variables": "PRL DLL",
        "cross": "Right Angle Cross of The Sphinx (13/7 | 1/2)",
    },
    "e_egoproj": {
        "P": "33.1.6.4.2 19.1.6.4.2 41.5.5.3.1 23.4.4.2.4 43.4.4.2.4 31.1.4.5.2 39.4.2.6.2 39.5.6.2.3 53.5.2.1.2 25.2.1.6.4 47.1.3.6.5 43.1.4.3.2 64.6.6.1.4",
        "D": "24.4.1.3.1 44.4.1.3.1 6.1.3.1.3 8.1.6.4.3 14.1.6.4.3 51.2.4.4.1 36.4.3.1.3 24.3.4.2.2 15.2.1.1.2 36.4.3.2.5 64.5.4.5.2 43.3.3.2.3 64.5.6.3.5",
        "type": "projector", "authority": "ego_projected", "definition": "split",
        "profile": "1/4", "variables": "PRL DLR",
        "cross": "Right Angle Cross of The Four Ways (33/19 | 24/44)",
    },
    "e_selfproj": {
        "P": "13.6.3.1.2 7.6.3.1.2 13.4.4.6.3 32.2.3.4.4 42.2.3.4.4 49.6.2.5.1 36.3.4.6.1 42.4.3.3.5 17.4.5.1.4 42.6.4.4.4 2.6.1.5.1 6.3.4.4.2 56.6.3.2.4",
        "D": "43.2.3.6.1 23.2.3.6.1 26.2.3.2.3 50.4.1.1.3 3.4.1.1.3 5.2.1.1.4 9.3.3.2.5 30.2.5.5.2 25.1.6.3.2 42.6.5.2.2 23.2.1.5.5 6.3.3.6.3 31.1.6.5.3",
        "type": "projector", "authority": "self_projected", "definition": "single",
        "profile": "6/2", "variables": "PLR DRL",
        "cross": "Left Angle Cross of Masks (13/7 | 43/23)",
    },
    "e_mental": {
        "P": "35.3.1.4.5 5.3.1.4.5 20.5.4.6.1 13.1.1.1.4 7.1.1.1.4 52.1.6.2.5 8.1.2.2.3 40.4.1.2.3 4.3.1.4.3 42.4.6.1.3 16.1.4.1.2 17.3.4.4.4 41.6.3.1.4",
        "D": "63.5.2.3.4 64.5.2.3.4 49.2.3.3.4 49.2.5.3.3 4.2.5.3.3 49.3.4.3.3 41.5.1.3.5 29.1.6.3.4 4.1.2.6.2 21.5.3.5.1 20.2.6.5.5 25.6.3.6.1 41.5.4.3.5",
        "type": "projector", "authority": "mental", "definition": "single",
        "profile": "3/5", "variables": "PRL DLL",
        "cross": "Right Angle Cross of Consciousness (35/5 | 63/64)",
    },
    "e_triple": {
        "P": "52.4.3.4.1 58.4.3.4.1 26.4.6.1.2 37.4.4.1.2 40.4.4.1.2 52.3.5.4.2 4.2.6.1.5 27.2.2.1.1 5.1.5.5.4 4.4.3.5.5 22.2.5.5.3 49.4.1.2.1 11.6.1.3.5",
        "D": "17.6.4.2.5 18.6.4.2.5 59.1.2.1.3 63.6.1.2.4 64.6.1.2.4 63.2.3.4.3 2.2.4.3.2 49.6.6.6.2 26.3.6.2.5 7.6.4.6.1 63.5.6.6.5 49.3.3.6.4 10.1.5.4.3",
        "type": "projector", "authority": "emotional", "definition": "triple_split",
        "profile": "4/6", "variables": "PRL DLL",
        "cross": "Right Angle Cross of Service (52/58 | 17/18)",
    },
    "e_quad": {
        "P": "37.2.1.4.4 40.2.1.4.4 35.6.4.1.2 17.5.2.5.1 18.5.2.5.1 13.2.4.2.3 41.2.5.3.3 48.1.3.1.5 49.1.6.1.3 64.6.5.4.4 15.3.6.4.4 57.2.6.5.4 7.4.4.1.3",
        "D": "9.4.2.3.3 16.4.2.3.3 42.1.3.6.2 51.1.3.3.1 57.1.3.3.1 5.3.5.6.2 61.6.1.4.5 47.2.6.5.1 60.4.6.5.4 47.2.5.5.4 52.1.1.4.2 57.2.5.1.4 7.6.2.3.5",
        "type": "generator", "authority": "emotional", "definition": "quadruple_split",
        "profile": "2/4", "variables": "PRR DLL",
        "cross": "Right Angle Cross of Planning (37/40 | 9/16)",
    },
    "e_juxt": {
        "P": "54.4.6.4.4 53.4.6.4.4 26.2.2.3.4 9.5.3.2.5 16.5.3.2.5 60.6.2.4.2 41.3.3.5.4 26.5.4.1.3 63.4.5.2.3 53.1.1.2.1 28.1.1.5.5 9.6.2.5.4 18.6.5.3.4",
        "D": "32.1.1.3.3 42.1.1.3.3 18.5.3.1.3 5.1.1.2.3 35.1.1.2.3 44.4.2.1.1 48.6.5.5.3 32.1.1.3.2 37.4.1.4.3 53.4.5.3.5 50.2.3.2.5 9.3.1.2.5 18.4.4.4.2",
        "type": "manifesting_generator", "authority": "sacral", "definition": "single",
        "profile": "4/1", "variables": "PRL DLL",
        "cross": "Juxtaposition Cross of Ambition (54/53 | 32/42)",
    },
    "e_manroot": {
        "P": "56.6.3.5.2 60.6.3.5.2 17.1.3.4.5 18.3.3.3.1 17.3.3.3.1 4.1.2.5.3 40.6.6.6.2 59.3.6.6.3 43.4.4.1.1 10.4.5.4.3 7.3.4.5.2 28.3.3.1.4 59.3.6.3.4",
        "D": "27.2.4.4.1 28.2.4.4.1 43.2.6.1.3 48.4.5.3.5 21.4.5.3.5 17.3.5.6.2 16.6.6.1.5 52.5.3.1.2 14.6.6.2.5 58.4.3.1.3 33.5.6.3.5 28.4.6.3.2 59.2.5.3.5",
        "type": "manifestor", "authority": "splenic", "definition": "single",
        "profile": "6/2", "variables": "PRL DRL",
        "cross": "Left Angle Cross of Distraction (56/60 | 27/28)",
    },
    # ответ движка: type=2 (MANIFESTOR), authority=3 (EGO → «Ego Manifested»), definition=1 (SINGLE),
    # profile=24 («2/4»), variable=10 (PRL_DRL), cross=185 («…The Unexpected (31/41 | 27/28)»),
    # channels: 1-8, 7-31, 17-62, 25-51 (расшифровка по словарям app.mybodygraph.com/js/app.*.js)
    "e_egoman_g": {
        "P": "31.2.2.5.3 41.2.2.5.3 57.1.3.5.4 53.6.4.3.3 54.6.4.3.3 7.5.1.3.2 62.4.2.6.2 46.2.5.2.5 51.5.2.6.3 49.3.2.5.3 59.4.5.3.2 44.6.4.5.1 40.6.1.6.3",
        "D": "27.4.3.4.2 28.4.3.4.2 16.3.3.1.5 62.4.2.2.4 61.4.2.2.4 8.1.6.6.4 25.5.3.4.5 7.1.2.1.3 17.2.3.1.1 49.4.2.4.4 59.2.2.1.2 1.2.3.3.1 40.5.2.2.4",
        "type": "manifestor", "authority": "ego_manifested", "definition": "single",
        "profile": "2/4", "variables": "PRL DRL",
        "cross": "Right Angle Cross of The Unexpected (31/41 | 27/28)",
    },
}
# Единственное расхождение до уровня базы (18.75″) из 468 активаций (18 карт): Уран Личности Обамы
# лежит в ~0.5″ от границы базы — разница эфемерид Swiss Ephemeris и движка Jovian.
KNOWN_BASE_DIFF = {("obama", "P", "uranus")}


def _jd(utc_minute: str) -> float:
    return julian_day_ut(datetime.fromisoformat(utc_minute).replace(tzinfo=timezone.utc))


def _fmt5(a: dict) -> str:
    return f"{a['gate']}.{a['line']}.{a['color']}.{a['tone']}.{a['base']}"


# ---------------------------------------------------------------------------
# 1. Колесо, центры, каналы — самосогласованность справочников
# ---------------------------------------------------------------------------

def test_wheel_order_is_permutation_and_offsets():
    assert sorted(GATE_ORDER) == list(range(1, 65))
    # barneyandflow / bonniesorsby: ворота 41 = 2°00′ Водолея, 25 = 28°15′ Рыб, 17 = 3°52′30″ Овна,
    # 15 = 28°15′ Близнецов, 10 = 28°15′ Стрельца, 60 = 26°22′30″ Козерога, 31 = 2°00′ Льва
    assert gate_start_longitude(41) == pytest.approx(302.0)
    assert gate_start_longitude(25) == pytest.approx(330 + 28.25)
    assert gate_start_longitude(17) == pytest.approx(3.875)
    assert gate_start_longitude(15) == pytest.approx(60 + 28.25)
    assert gate_start_longitude(10) == pytest.approx(240 + 28.25)
    assert gate_start_longitude(60) == pytest.approx(270 + 26.375)
    assert gate_start_longitude(31) == pytest.approx(122.0)


def test_degree_table_barneyandflow_all_signs():
    # начало каждого знака лежит в воротах (по таблице barneyandflow): 0° Овна — 25, 0° Тельца — 3, ...
    expected = {0: 25, 30: 3, 60: 8, 90: 15, 120: 56, 150: 29, 180: 46, 210: 50, 240: 14, 270: 10, 300: 60, 330: 30}
    for lon, gate in expected.items():
        assert longitude_to_activation(lon)["gate"] == gate, lon


def test_line_color_tone_base_boundaries():
    a = longitude_to_activation(302.0)
    assert (a["gate"], a["line"], a["color"], a["tone"], a["base"]) == (41, 1, 1, 1, 1)
    a = longitude_to_activation(302.0 - 1e-9)
    assert (a["gate"], a["line"], a["color"], a["tone"], a["base"]) == (60, 6, 6, 6, 5)
    assert longitude_to_activation(0.0)["gate_line"] == "25.2"
    assert longitude_to_activation(302.0 + 0.9375)["gate_line"] == "41.2"
    assert longitude_to_activation(302.0 + 5.625)["gate_line"] == "19.1"


def test_centers_and_channels_tables():
    counts = {c: sum(1 for g in GATES.values() if g["center"] == c) for c in CENTERS}
    assert counts == {"head": 3, "ajna": 6, "throat": 11, "g": 8, "heart": 4, "sacral": 9,
                      "solar_plexus": 7, "spleen": 7, "root": 9}
    assert len(CHANNELS) == 36
    assert len({frozenset((a, b)) for a, b, *_ in CHANNELS}) == 36
    for a, b, *_ in CHANNELS:
        assert GATES[a]["center"] != GATES[b]["center"]
    # каждые ворота участвуют хотя бы в одном канале
    assert {g for a, b, *_ in CHANNELS for g in (a, b)} == set(range(1, 65))


def test_quarters_match_official_rax_order():
    # в словаре MyBodyGraph варианты правоуглового креста идут по четвертям 1..4
    for fam, (_ru, gates) in RAX_FAMILIES.items():
        assert [_quarter_index(g) for g in gates] == [0, 1, 2, 3], fam
    # четверти по 16 ворот: 13 (313°15′), 2 (43°15′), 7 (133°15′), 1 (223°15′)
    assert [GATE_INDEX[q["first_gate"]] for q in QUARTERS] == [2, 18, 34, 50]
    assert [gate_start_longitude(q["first_gate"]) for q in QUARTERS] == pytest.approx([313.25, 43.25, 133.25, 223.25])


# ---------------------------------------------------------------------------
# 2. Момент Дизайна
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("b", [T1, T2, T3, T4])
def test_design_is_88_degrees_of_sun(b):
    r = calculate(b)
    jd, jdd = r["inputs_used"]["jd_ut"], r["inputs_used"]["jd_design"]
    diff = (sun_longitude(jd) - sun_longitude(jdd)) % 360
    assert diff == pytest.approx(88.0, abs=1e-5)
    assert 85 < jd - jdd < 93          # 88° солнечной дуги ≈ 86–92 суток, не ровно 88 суток


# ---------------------------------------------------------------------------
# 3. Сверка с официальным движком Jovian Archive / MyBodyGraph (18 карт × 26 активаций)
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("key", list(OFFICIAL))
def test_official_engine_vectors(key):
    ref = OFFICIAL[key]
    ch = chart_from_jd(_jd(OFFICIAL_UTC[key]))
    for side, acts in (("P", ch["personality"]), ("D", ch["design"])):
        expected = ref[side].split()
        for pl, exp in zip(PLANETS, expected):
            got = _fmt5(acts[pl])
            if (key, side, pl) in KNOWN_BASE_DIFF:
                assert got.rsplit(".", 1)[0] == exp.rsplit(".", 1)[0], (key, side, pl, got, exp)
            else:
                assert got == exp, (key, side, pl, got, exp)
    assert ch["type"]["id"] == ref["type"]
    assert ch["authority"]["id"] == ref["authority"]
    assert ch["definition"]["id"] == ref["definition"]
    assert ch["profile"]["profile"] == ref["profile"]
    assert ch["variables"]["notation"] == ref["variables"]
    assert ch["incarnation_cross"]["name_en"] == ref["cross"]
    assert ch["incarnation_cross"]["nominal_design_gates_match"]


# ---------------------------------------------------------------------------
# 4. T1–T4 через calculate() (местное время → UTC), сверка с OFFICIAL до цвета
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("key,b,utc", [
    ("t1", T1, "1990-05-15T10:30:00+00:00"),       # летнее время СССР UTC+4
    ("t2", T2, "1984-02-04T20:30:00+00:00"),
    ("t3", T3, "2004-02-29T05:15:00+00:00"),
    ("einstein", T4, "1879-03-14T10:50:02"),         # LMT Ульма = UTC+0:39:57
    ("obama", OBAMA, "1961-08-05T05:24:00+00:00"),
    ("jobs", JOBS, "1955-02-25T03:15:00+00:00"),
    ("trump", TRUMP, "1946-06-14T14:54:00+00:00"),   # EDT 1946 (tzdb)
])
def test_calculate_matches_official_to_color(key, b, utc):
    r = calculate(b)
    assert r["inputs_used"]["utc"].startswith(utc)
    ref = OFFICIAL[key]
    for side, short in (("P", "personality"), ("D", "design")):
        for pl, exp in zip(PLANETS, ref[side].split()):
            got = r[short][pl]
            assert f"{got['gate']}.{got['line']}.{got['color']}" == ".".join(exp.split(".")[:3]), (key, side, pl)
    assert r["type"]["id"] == ref["type"]
    assert r["authority"]["id"] == ref["authority"]
    assert r["profile"]["profile"] == ref["profile"]
    assert r["incarnation_cross"]["name_en"] == ref["cross"]
    json.dumps(r, ensure_ascii=False)


# ---------------------------------------------------------------------------
# 5. TOTALHD — опубликованные карты (gate.line всех 26 активаций)
# ---------------------------------------------------------------------------
TOTALHD = {
    # https://totalhumandesign.com/design/albert-einstein  (14.03.1879 11:30, Ulm)
    "einstein": (T4, "36.1 6.1 5.4 41.1 31.1 25.6 51.2 60.1 30.4 17.1 59.2 24.1 8.1",
                 "11.4 12.4 46.3 41.3 31.3 38.3 10.1 14.1 41.6 36.5 59.5 27.6 8.1",
                 "generator", "1/4", "emotional", "split", {"25-51", "6-59", "30-41"}),
    # https://totalhumandesign.com/design/barack-obama  (04.08.1961 19:24, Honolulu)
    "obama": (OBAMA, "33.6 19.6 20.4 29.3 30.3 31.1 15.4 47.6 60.5 61.5 29.1 44.2 40.2",
              "2.2 1.2 38.5 59.4 55.4 2.6 21.4 56.4 41.5 60.4 4.3 44.3 59.6",
              "projector", "6/2", "emotional", "single", {"30-41"}),
    # https://totalhumandesign.com/design/steve-jobs  (24.02.1955 19:15, San Francisco)
    "jobs": (JOBS, "55.6 59.6 17.5 10.6 15.6 13.2 61.1 3.3 53.6 43.3 62.4 50.2 29.1",
             "9.3 16.3 41.1 58.2 52.2 43.6 1.3 30.3 56.4 1.2 56.2 50.1 29.3",
             "generator", "6/3", "emotional", "split", {"17-62", "30-41", "9-52"}),
    # https://totalhumandesign.com/design/donald-trump  (14.06.1946 10:54, Queens NY)
    "trump": (TRUMP, "12.1 11.1 26.5 45.5 26.5 52.6 62.6 29.3 57.3 62.4 45.1 18.3 33.3",
              "36.3 6.3 59.6 12.4 11.4 21.1 17.2 53.2 32.6 53.4 35.3 18.4 33.3",
              "manifesting_generator", "1/3", "emotional", "single", {"17-62", "35-36", "21-45", "6-59"}),
}


@pytest.mark.parametrize("key", list(TOTALHD))
def test_totalhumandesign_published_charts(key):
    b, p, d, t, prof, auth, dfn, chans = TOTALHD[key]
    r = calculate(b)
    assert " ".join(r["personality_short"][pl] for pl in PLANETS) == p
    assert " ".join(r["design_short"][pl] for pl in PLANETS) == d
    assert r["type"]["id"] == t
    assert r["profile"]["profile"] == prof
    assert r["authority"]["id"] == auth
    assert r["definition"]["id"] == dfn
    assert {c["channel"] for c in r["channels"]} == chans


# ---------------------------------------------------------------------------
# 6. Кресты: все 192 имени = словарь MyBodyGraph
# ---------------------------------------------------------------------------
# формат: ворота P-Солнца:имя|ворота D-Солнца (номинальные)
OFFICIAL_CROSSES = {
    "right": "1:The Sphinx|7 2:The Sphinx|13 3:Laws|60 4:Explanation|23 5:Consciousness|64 6:Eden|12 7:The Sphinx|2 8:Contagion|30 9:Planning|40 10:The Vessel of Love|46 11:Eden|6 12:Eden|36 13:The Sphinx|1 14:Contagion|29 15:The Vessel of Love|25 16:Planning|37 17:Service|58 18:Service|52 19:The Four Ways|44 20:The Sleeping Phoenix|55 21:Tension|38 22:Rulership|26 23:Explanation|49 24:The Four Ways|19 25:The Vessel of Love|10 26:Rulership|47 27:The Unexpected|41 28:The Unexpected|31 29:Contagion|8 30:Contagion|14 31:The Unexpected|27 32:Maya|62 33:The Four Ways|24 34:The Sleeping Phoenix|59 35:Consciousness|63 36:Eden|11 37:Planning|9 38:Tension|48 39:Tension|21 40:Planning|16 41:The Unexpected|28 42:Maya|61 43:Explanation|4 44:The Four Ways|33 45:Rulership|22 46:The Vessel of Love|15 47:Rulership|45 48:Tension|39 49:Explanation|43 50:Laws|56 51:Penetration|54 52:Service|17 53:Penetration|51 54:Penetration|57 55:The Sleeping Phoenix|34 56:Laws|3 57:Penetration|53 58:Service|18 59:The Sleeping Phoenix|20 60:Laws|50 61:Maya|32 62:Maya|42 63:Consciousness|5 64:Consciousness|35",
    "juxtaposition": "1:Self-expression|4 2:The Driver|49 3:Mutation|41 4:Formulization|8 5:Habits|47 6:Conflict|15 7:Interaction|23 8:Contribution|55 9:Focus|64 10:Behavior|18 11:Ideas|46 12:Articulation|25 13:Listening|43 14:Empowering|59 15:Extremes|17 16:Experimentation|63 17:Opinions|38 18:Correction|39 19:Need|1 20:The Now|37 21:Control|54 22:Grace|11 23:Assimilation|30 24:Rationalization|13 25:Innocence|58 26:The Trickster|6 27:Caring|19 28:Risks|33 29:Commitment|20 30:Fates|34 31:Influence|24 32:Conservation|56 33:Retreat|2 34:Power|40 35:Experience|22 36:Crisis|10 37:Bargains|5 38:Opposition|57 39:Provocation|51 40:Denial|35 41:Fantasy|44 42:Completion|60 43:Insight|29 44:Alertness|7 45:Possession|36 46:Serendipity|52 47:Oppression|12 48:Depth|53 49:Principles|14 50:Values|31 51:Shock|61 52:Stillness|21 53:Beginnings|42 54:Ambition|32 55:Moods|9 56:Stimulation|27 57:Intuition|62 58:Vitality|48 59:Strategy|16 60:Limitation|28 61:Thinking|50 62:Detail|3 63:Doubts|26 64:Confusion|45",
    "left": "1:Defiance|4 2:Defiance|49 3:Wishes|41 4:Revolution|8 5:Separation|47 6:The Plane|15 7:Masks|23 8:Uncertainty|55 9:Identification|64 10:Prevention|18 11:Education|46 12:Education|25 13:Masks|43 14:Uncertainty|59 15:Prevention|17 16:Identification|63 17:Upheaval|38 18:Upheaval|39 19:Refinement|1 20:Duality|37 21:Endeavor|54 22:Informing|11 23:Dedication|30 24:Incarnation|13 25:Healing|58 26:Confrontation|6 27:Alignment|19 28:Alignment|33 29:Industry|20 30:Industry|34 31:The Alpha|24 32:Limitation|56 33:Refinement|2 34:Duality|40 35:Separation|22 36:The Plane|10 37:Migration|5 38:Individualism|57 39:Individualism|51 40:Migration|35 41:The Alpha|44 42:Limitation|60 43:Dedication|29 44:Incarnation|7 45:Confrontation|36 46:Healing|52 47:Informing|12 48:Endeavor|53 49:Revolution|14 50:Wishes|31 51:The Clarion|61 52:Demands|21 53:Cycles|42 54:Cycles|32 55:Spirit|9 56:Distraction|27 57:The Clarion|62 58:Demands|48 59:Spirit|16 60:Distraction|28 61:Obscuration|50 62:Obscuration|3 63:Dominion|26 64:Dominion|45",
}


@pytest.mark.parametrize("angle", ["right", "juxtaposition", "left"])
def test_all_192_cross_names(angle):
    shift = 16 if angle == "right" else 15
    entries = {}
    # разбор: «ворота:имя|ворота» (в именах есть пробелы, поэтому режем по шаблону)
    for m in re.finditer(r"(\d+):([^|]+)\|(\d+)", OFFICIAL_CROSSES[angle]):
        entries[int(m.group(1))] = (m.group(2).strip(), int(m.group(3)))
    assert len(entries) == 64
    for ps, (name, ds) in entries.items():
        pe = GATE_ORDER[(GATE_INDEX[ps] + 32) % 64]
        d_sun = GATE_ORDER[(GATE_INDEX[ps] - shift) % 64]
        assert d_sun == ds, (angle, ps)
        de = GATE_ORDER[(GATE_INDEX[d_sun] + 32) % 64]
        c = incarnation_cross(ps, pe, d_sun, de, angle)
        assert c["name"] == name, (angle, ps)
        assert c["nominal_design_gates_match"]


# ---------------------------------------------------------------------------
# 7. Опции и граничные случаи
# ---------------------------------------------------------------------------

def test_true_vs_mean_node_einstein():
    # Узел Эйнштейна лежит у границы ворот 60/41: истинный 302.73° → 41.1 (так у Jovian),
    # средний ≈ 301.4° → 60.6. Это показывает, почему узел по умолчанию — истинный.
    rt = calculate(T4)
    rm = calculate(T4, node="mean")
    assert rt["personality_short"]["north_node"] == "41.1"
    assert rm["personality_short"]["north_node"] == "60.6"
    assert any("средний узел" in w for w in rm["warnings"])


def test_unknown_time_noon_and_sensitivity():
    r = calculate(BirthInput(1990, 5, 15, place="Москва"))
    assert not r["inputs_used"]["time_known"]
    assert r["warnings"]
    ts = r["time_sensitivity"]
    assert "personality.moon" in ts["variable_activations"]
    assert "personality.sun" not in ts["variable_activations"] or len(ts["variable_activations"]["personality.sun"]) <= 2


def test_requires_timezone():
    with pytest.raises(ValueError):
        calculate(BirthInput(1990, 5, 15, 14, 30))


def test_output_contract_and_steps():
    r = calculate(T1)
    for k in ("method", "variant", "inputs_used", "warnings", "steps", "personality", "design", "type",
              "authority", "profile", "definition", "channels", "centers", "incarnation_cross", "variables"):
        assert k in r
    assert r["method"] == "human_design"
    assert len(r["personality"]) == 13 and len(r["design"]) == 13
    assert all(isinstance(s, dict) and "step" in s for s in r["steps"])
    # Земля ровно напротив Солнца, Южный узел напротив Северного — ворота через 32 позиции колеса
    for side in ("personality", "design"):
        acts = r[side]
        assert (GATE_INDEX[acts["earth"]["gate"]] - GATE_INDEX[acts["sun"]["gate"]]) % 64 == 32
        assert acts["earth"]["line"] == acts["sun"]["line"]
        assert (GATE_INDEX[acts["south_node"]["gate"]] - GATE_INDEX[acts["north_node"]["gate"]]) % 64 == 32
    assert r["profile"]["valid"]
    json.dumps(r, ensure_ascii=False)


def test_design_moment_function_direct():
    jd = _jd("1990-05-15T10:30")
    jdd = design_moment(jd)
    assert (sun_longitude(jd) - sun_longitude(jdd)) % 360 == pytest.approx(88.0, abs=1e-6)


# ---------------------------------------------------------------------------
# 8. Верификация (волна 2): логика типа/авторитета/определённости на синтетических наборах ворот
#    (правила сверены с официальным движком — примеры e_* выше — и с открытым кодом
#    SharpAstrology.HumanDesign, HumanDesignChart.cs: Type/_Authority)
# ---------------------------------------------------------------------------

def _gates_of(*channels: str) -> set[int]:
    return {int(g) for ch in channels for g in ch.split("-")}


@pytest.mark.parametrize("channels,type_id,auth_id,definition", [
    # МГ: мотор (Сакрал) → Горло только через G (2-14 + 1-8)
    (("2-14", "1-8"), "manifesting_generator", "sacral", "single"),
    # МГ: Сакрал → Селезёнка → Горло (27-50 + 48-16)
    (("27-50", "16-48"), "manifesting_generator", "sacral", "single"),
    # Генератор: Сакрал определён, Горло определено, но не связано с мотором
    (("5-15", "17-62"), "generator", "sacral", "split"),
    # МГ через Сердце→Горло (21-45) при определённом Сакрале в другой группе
    (("21-45", "3-60"), "manifesting_generator", "sacral", "split"),
    # Манифестор: Корень → Селезёнка → Горло (54-32 + 48-16), авторитет селезёночный
    (("32-54", "16-48"), "manifestor", "splenic", "single"),
    # Манифестор: Корень → Сол. сплетение → Горло (39-55 + 35-36), эмоциональный
    (("39-55", "35-36"), "manifestor", "emotional", "single"),
    # Эго-манифестированный: Сердце → Горло напрямую (21-45)
    (("21-45",), "manifestor", "ego_manifested", "single"),
    # Эго-манифестированный: Сердце → G (25-51) → Горло (10-20) — подтверждено движком (e_egoman_g)
    (("25-51", "10-20"), "manifestor", "ego_manifested", "single"),
    # Эго-проецированный: Сердце–G без связи с Горлом; Голова–Аджна отдельно → split
    (("25-51",), "projector", "ego_projected", "single"),
    (("25-51", "24-61"), "projector", "ego_projected", "split"),
    # Селезёнка выше Сердца: 26-44 (Сердце–Селезёнка) + 16-48 → Манифестор, но авторитет селезёночный
    (("26-44", "16-48"), "manifestor", "splenic", "single"),
    # Самопроецируемый: G → Горло без моторов
    (("1-8",), "projector", "self_projected", "single"),
    (("13-33", "47-64"), "projector", "self_projected", "split"),
    # Ментальный (Sounding Board): только Голова/Аджна/Горло
    (("24-61", "23-43"), "projector", "mental", "single"),
    (("4-63",), "projector", "mental", "single"),
    # Рефлектор
    ((), "reflector", "lunar", "none"),
    # тройное и четверное расщепление
    (("24-61", "9-52", "25-51"), "generator", "sacral", "triple_split"),
    (("47-64", "12-22", "18-58", "25-51"), "manifestor", "emotional", "quadruple_split"),
])
def test_type_authority_definition_synthetic(channels, type_id, auth_id, definition):
    gates = _gates_of(*channels)
    an = analyze_gates(gates, set())
    assert {c["channel"] for c in an["channels"]} == set(channels)
    assert an["type_id"] == type_id
    assert an["authority_id"] == auth_id
    assert an["definition"]["id"] == definition
    # сторона активации (Личность/Дизайн) не влияет на механику
    an2 = analyze_gates(set(), gates)
    assert (an2["type_id"], an2["authority_id"]) == (type_id, auth_id)


def test_hanging_gates_do_not_define_centers():
    an = analyze_gates({1, 2, 3, 4, 5, 6, 7, 9}, {10, 11, 12})   # ни одной пары канала
    assert an["channels"] == [] and an["type_id"] == "reflector"
    assert an["centers"]["g"]["state"] == "undefined" and an["centers"]["heart"]["state"] == "open"


@pytest.mark.parametrize("p_line,d_line,angle", [
    (1, 3, "right"), (1, 4, "right"), (2, 4, "right"), (2, 5, "right"), (3, 5, "right"), (3, 6, "right"),
    (4, 6, "right"), (4, 1, "juxtaposition"), (5, 1, "left"), (5, 2, "left"), (6, 2, "left"), (6, 3, "left"),
])
def test_profile_angle_rule(p_line, d_line, angle):
    assert profile_angle(p_line, d_line) == angle
    assert f"{p_line}/{d_line}" in VALID_PROFILES


def test_only_12_profiles_occur():
    # 88° = 15,64 ворот → линия Дизайна жёстко связана с линией Личности
    seen = set()
    jd = _jd("1990-01-01T00:00")
    for k in range(0, 366 * 4, 3):
        ch = chart_from_jd(jd + k * 0.25 + 0.013 * k)
        seen.add(ch["profile"]["profile"])
    assert seen <= set(VALID_PROFILES) and len(seen) == 12


def test_manual_design_iteration_from_knowledge_base():
    """Ручная итерация из 04-human-design.md (шаг 3): t₀ = JD − 89,3;
    t_{k+1} = t_k − Δ/0,9856, где Δ = (λ☉(t_k) − цель), приведённая к −180…+180.
    За 4 итерации сходится к точному моменту (≤1 с) для T1–T4."""
    for b in (T1, T2, T3, T4):
        r = calculate(b)
        jd, exact = r["inputs_used"]["jd_ut"], r["inputs_used"]["jd_design"]
        target = (sun_longitude(jd) - 88.0) % 360.0
        t = jd - 89.3
        for _ in range(4):
            delta = (sun_longitude(t) - target + 180.0) % 360.0 - 180.0
            t -= delta / 0.9856
        assert abs(t - exact) * 86400 < 1.0


def test_t1_moon_gate_boundary_documented():
    # 04-human-design.md, §6: Луна Личности T1 в 0,0153° от начала ворот 60; на 2 мин раньше — 61.6
    r = calculate(T1)
    assert r["personality"]["moon"]["gate_line"] == "60.1"
    assert r["personality"]["moon"]["deg_in_gate"] == pytest.approx(0.0153, abs=5e-5)
    earlier = chart_from_jd(r["inputs_used"]["jd_ut"] - 2 / 1440)
    assert earlier["personality"]["moon"]["gate_line"] == "61.6"


def test_definition_groups_order_is_deterministic():
    # группы перечисляются в порядке центров CENTERS (не зависят от PYTHONHASHSEED)
    r = calculate(T4)
    assert r["definition"]["groups"] == [["g", "heart"], ["sacral", "solar_plexus", "root"]]
    order = list(CENTERS)
    firsts = [order.index(g[0]) for g in r["definition"]["groups"]]
    assert firsts == sorted(firsts)
