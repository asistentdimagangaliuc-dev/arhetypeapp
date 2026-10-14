"""Тесты калькулятора Генных ключей (Gene Keys, Гологенетический профиль).

Запуск: .venv/bin/python -m pytest calculators/tests/test_gene_keys.py -q
"""
from __future__ import annotations

import json
from collections import Counter

import pytest

from calculators.common.time import BirthInput
from calculators.gene_keys import (
    CODON_RINGS, EXTENDED_SPHERES, GATE_ORDER, KEYS, LINE_KEYNOTES, SEQUENCES, SPHERES, calculate,
    key_line_from_longitude, programming_partner,
)

SIDE_SPHERES = ["lifes_work", "evolution", "radiance", "purpose", "attraction", "iq", "eq", "sq",
                "core", "culture", "pearl"]


# ---------------------------------------------------------------------------
# 1. Колесо 64 ключей
# ---------------------------------------------------------------------------

# Таблица ворот по градусам: https://bonniesorsby.com/human-design-gates-by-degree/
# (границы округлены источником до минут). Формат: (ключ, знак 0=Овен…11=Рыбы, градус, минута начала).
PUBLISHED_STARTS = [
    (25, 11, 28, 15), (17, 0, 3, 52), (21, 0, 9, 30), (51, 0, 15, 7), (42, 0, 20, 45), (3, 0, 26, 22),
    (27, 1, 2, 0), (24, 1, 7, 37), (2, 1, 13, 15), (23, 1, 18, 52), (8, 1, 24, 30), (20, 2, 0, 7),
    (16, 2, 5, 45), (35, 2, 11, 22), (45, 2, 17, 0), (12, 2, 22, 37), (15, 2, 28, 15), (52, 3, 3, 52),
    (39, 3, 9, 30), (53, 3, 15, 7), (62, 3, 20, 45), (56, 3, 26, 22), (31, 4, 2, 0), (33, 4, 7, 37),
    (7, 4, 13, 15), (4, 4, 18, 52), (29, 4, 24, 30), (59, 5, 0, 7), (40, 5, 5, 45), (64, 5, 11, 22),
    (47, 5, 17, 0), (6, 5, 22, 37), (46, 5, 28, 15), (18, 6, 3, 52), (48, 6, 9, 30), (57, 6, 15, 7),
    (32, 6, 20, 45), (50, 6, 26, 22), (28, 7, 2, 0), (44, 7, 7, 37), (1, 7, 13, 15), (43, 7, 18, 52),
    (14, 7, 24, 30), (34, 8, 0, 7), (9, 8, 5, 45), (5, 8, 11, 22), (26, 8, 17, 0), (11, 8, 22, 37),
    (10, 8, 28, 15), (58, 9, 3, 52), (38, 9, 9, 30), (54, 9, 15, 7), (61, 9, 20, 45), (60, 9, 26, 22),
    (41, 10, 2, 0), (19, 10, 7, 37), (13, 10, 13, 15), (49, 10, 18, 52), (30, 10, 24, 30), (55, 11, 0, 7),
    (37, 11, 5, 45), (63, 11, 11, 22), (22, 11, 17, 0), (36, 11, 22, 37),
]


def test_gate_order_is_permutation():
    assert sorted(GATE_ORDER) == list(range(1, 65))


@pytest.mark.parametrize("key,sign,deg,minute", PUBLISHED_STARTS)
def test_wheel_matches_published_degree_table(key, sign, deg, minute):
    start = sign * 30 + deg + minute / 60.0
    # середина сектора (+2.8125°) не зависит от округления источника до минут
    assert key_line_from_longitude(start + 2.8125)["key"] == key
    # начало ключа (с запасом 1′ на округление источника) — линия 1
    kl = key_line_from_longitude(start + 1 / 60)
    assert (kl["key"], kl["line"]) == (key, 1)


def test_wheel_edges_and_lines():
    assert key_line_from_longitude(302.0)["key"] == 41            # 2°00′ Водолея
    assert (key_line_from_longitude(301.99)["key"], key_line_from_longitude(301.99)["line"]) == (60, 6)
    assert key_line_from_longitude(0.0)["key"] == 25 and key_line_from_longitude(0.0)["line"] == 2
    assert key_line_from_longitude(358.25 + 0.9375 * 5 + 0.01)["line"] == 6
    assert key_line_from_longitude(359.9999)["key"] == 25
    assert key_line_from_longitude(720.0 + 302.5)["key"] == 41    # нормализация >360°


# Программные партнёры по заголовкам глав рус. изд. 2013 г. («Программный партнер: N-й Генный Ключ»)
BOOK_PARTNERS = {1: 2, 3: 50, 4: 49, 5: 35, 6: 36, 7: 13, 8: 14, 9: 16, 10: 15, 11: 12, 17: 18, 19: 33,
                 20: 34, 21: 48, 22: 47, 23: 43, 24: 44, 25: 46, 26: 45, 27: 28, 29: 30, 31: 41, 32: 42,
                 37: 40, 38: 39, 51: 57, 52: 58, 53: 54, 55: 59, 56: 60, 61: 62, 63: 64}


def test_programming_partners():
    assert len(BOOK_PARTNERS) == 32
    for a, b in BOOK_PARTNERS.items():
        assert programming_partner(a) == b
        assert programming_partner(b) == a


def test_codon_rings_cover_all_keys_and_match_genetic_code():
    keys = [k for r in CODON_RINGS for k in r["keys"]]
    assert len(CODON_RINGS) == 21
    assert sorted(keys) == list(range(1, 65))
    # вырожденность генетического кода: 3 аминокислоты по 6 кодонов (Leu, Ser, Arg), 5 по 4,
    # 2 группы по 3 (Ile и стоп-кодоны), 9 по 2, 2 по 1 (Met, Trp)
    assert Counter(len(r["keys"]) for r in CODON_RINGS) == Counter({6: 3, 4: 5, 3: 2, 2: 9, 1: 2})


def test_keys_table_complete():
    assert sorted(KEYS) == list(range(1, 65))
    for k, v in KEYS.items():
        for lvl in ("shadow", "gift", "siddhi"):
            en, ru = v[lvl]
            assert en and ru, (k, lvl)
    assert KEYS[1]["shadow"] == ("Entropy", "Энтропия")
    assert KEYS[64]["siddhi"] == ("Illumination", "Просветление")
    assert KEYS[55]["gift"][0] == KEYS[55]["siddhi"][0] == "Freedom"


def test_line_keynote_tables_have_six_lines():
    for theme, lines in LINE_KEYNOTES.items():
        assert sorted(lines) == [1, 2, 3, 4, 5, 6], theme
        for ln in lines.values():
            assert ln["status"] in ("official", "secondary", "unconfirmed")
            if ln["status"] != "unconfirmed":
                assert ln["en"] and ln["ru"]


# ---------------------------------------------------------------------------
# 2. Внешние векторы — опубликованные профили (11 независимых позиций каждый)
# ---------------------------------------------------------------------------

EXTERNAL = {
    # Официальный профиль Gene Keys (© Gene Keys 2020, генератор genekeys.com):
    # https://waynebuckhanan.com/wb/20200728_WLB_GeneKeys.pdf — 25 Oct 1977 19:00, San Antonio, Texas (CDT)
    # (тот же профиль в формате 2012 г.: https://waynebuckhanan.com/wb/20141130_WLB_GeneKeys.pdf)
    "wayne_buckhanan": (
        BirthInput(1977, 10, 25, 19, 0, tz="America/Chicago", lat=29.4241, lon=-98.4936),
        dict(lifes_work="28.1", evolution="27.1", radiance="31.3", purpose="41.3", attraction="11.4",
             iq="48.2", eq="56.4", sq="12.1", core="16.2", culture="12.4", pearl="52.3"),
    ),
    # Официальный профиль Gene Keys (генератор genekeys.com, 2022):
    # https://www.leben-mit-ohne.de/wp-content/uploads/2022/10/LMO_Profile.pdf — 19 Oct 2021 09:44, Lochau, Vorarlberg
    "lmo_2021": (
        BirthInput(2021, 10, 19, 9, 44, tz="Europe/Vienna", lat=47.5167, lon=9.75),
        dict(lifes_work="32.6", evolution="42.6", radiance="56.2", purpose="60.2", attraction="9.6",
             iq="5.2", eq="32.2", sq="29.5", core="4.6", culture="55.1", pearl="49.4"),
    ),
    # IntegralHumanDesign (Pitzal), Golden Path evaluation, публичная персона:
    # https://www.integralhumandesign.net/examples/SchneiderRomy.GOLDENPATH.pdf — 23.09.1938 21:45 MET, Вена
    "romy_schneider": (
        BirthInput(1938, 9, 23, 21, 45, tz="UTC+01:00", lat=48.2167, lon=16.3667),
        dict(lifes_work="46.3", evolution="25.3", radiance="15.5", purpose="10.5", attraction="24.6",
             iq="1.3", eq="40.5", sq="31.6", core="39.3", culture="55.3", pearl="49.5"),
    ),
    # https://www.integralhumandesign.net/examples/KahloFrida.GOLDENPATH.pdf — 06.07.1907 16:07 LMT (06h37W),
    # Койоакан 99W10 19N20 (время — как в источнике)
    "frida_kahlo": (
        BirthInput(1907, 7, 6, 16, 7, tz="LMT", lat=19.3333, lon=-99.1667),
        dict(lifes_work="39.5", evolution="38.5", radiance="51.1", purpose="57.1", attraction="60.3",
             iq="12.3", eq="38.5", sq="55.6", core="10.5", culture="15.6", pearl="53.6"),
    ),
}


@pytest.mark.parametrize("name", list(EXTERNAL))
def test_external_published_profiles(name):
    b, expected = EXTERNAL[name]
    r = calculate(b)
    got = {k: r["profile"][k] for k in expected}
    assert got == expected
    assert r["profile"]["brand"] == r["profile"]["lifes_work"]
    assert r["profile"]["vocation"] == r["profile"]["core"]
    assert r["checks"]["all_ok"]


def test_official_line_keynotes_wayne():
    # Line Themes из официального профиля 2012 г. (waynebuckhanan.com/wb/20141130_WLB_GeneKeys.pdf)
    r = calculate(EXTERNAL["wayne_buckhanan"][0])
    s = r["spheres"]
    exp = {
        "lifes_work": "Creator", "evolution": "Self-Empowerment", "radiance": "Interaction",
        "purpose": "Movement (blood)", "attraction": "Frigidity / Romance", "iq": "The Brilliant mind",
        "eq": "Kindness / Meanness", "sq": "Certainty (rhythm and routine)", "core": "Denial / Ease",
        "vocation": "Marketing (value)", "culture": "Network", "brand": "Boldness (security)",
        "pearl": "Celebration",
    }
    for sid, text in exp.items():
        assert s[sid]["line_keynote"]["en"].lower().startswith(text.lower()), sid
        assert s[sid]["line_keynote"]["status"] == "official", sid
    assert s["purpose"]["line_keynote_venus"]["en"] == "The Adventurer / Escape Artist"


# ---------------------------------------------------------------------------
# 3. Эталонные персоны T1–T4 (собственный расчёт; внешняя сверка Солнца/Земли и всех
#    планет — с calculators/human_design.py, который строится независимо)
# ---------------------------------------------------------------------------

T = {
    "T1": (BirthInput(1990, 5, 15, 14, 30, place="Москва"),
           dict(lifes_work="23.6", evolution="43.6", radiance="30.2", purpose="29.2", attraction="50.4",
                iq="21.4", eq="22.2", sq="61.2", core="38.3", vocation="38.3", culture="15.3",
                brand="23.6", pearl="39.1"),
           "1990-02-15T07:06"),
    "T2": (BirthInput(1984, 2, 4, 23, 30, place="Москва"),
           dict(lifes_work="13.3", evolution="7.3", radiance="1.5", purpose="2.5", attraction="54.6",
                iq="38.4", eq="44.5", sq="46.3", core="6.3", vocation="6.3", culture="5.4",
                brand="13.3", pearl="10.6"),
           "1983-11-10T04:53"),
    "T3": (BirthInput(2004, 2, 29, 8, 15, place="Санкт-Петербург"),
           dict(lifes_work="37.5", evolution="40.5", radiance="5.1", purpose="35.1", attraction="42.5",
                iq="42.4", eq="2.4", sq="58.6", core="36.1", vocation="36.1", culture="47.1",
                brand="37.5", pearl="64.4"),
           "2003-12-04T13:08"),
    "T4": (BirthInput(1879, 3, 14, 11, 30, tz="LMT", lat=48.4011, lon=9.9876),
           dict(lifes_work="36.1", evolution="6.1", radiance="11.4", purpose="12.4", attraction="46.3",
                iq="51.2", eq="60.1", sq="10.1", core="14.1", vocation="14.1", culture="41.6",
                brand="36.1", pearl="30.4"),
           "1878-12-17T12:51"),
}


@pytest.mark.parametrize("tid", list(T))
def test_reference_subjects(tid):
    b, expected, design_utc = T[tid]
    r = calculate(b)
    assert {k: r["profile"][k] for k in expected} == expected
    assert r["inputs_used"]["design_utc"].startswith(design_utc)
    assert r["checks"]["all_ok"]
    assert abs(r["checks"]["design_sun_arc_deg"] - 88.0) < 1e-4
    assert 85.0 < r["checks"]["design_days_before_birth"] < 93.0


def test_t1_soviet_dst_offset():
    r = calculate(T["T1"][0])
    assert r["inputs_used"]["utc_offset"] == "UTC+04:00"
    assert r["inputs_used"]["utc"].startswith("1990-05-15T10:30")
    # Луна Дизайна близко к границе линии — должно быть предупреждение
    assert "attraction" in r["time_sensitivity"]["changes_within_tolerance"]


def test_t4_lmt():
    r = calculate(T["T4"][0])
    assert r["inputs_used"]["offset_source"] == "LMT(longitude)"
    assert r["inputs_used"]["utc"].startswith("1879-03-14T10:50")
    assert r["spheres"]["lifes_work"]["lon_str"] == "23°30′ Рыбы"


# ---------------------------------------------------------------------------
# Повторная проверка (приоритет 2), 14.10.2026: текстовые таблицы против официальных источников
# ---------------------------------------------------------------------------

# Таблица lineTeaching.full из JS официального профайлера Gene Keys
# (genekeys.com/free-profile/ → wp-content/themes/buddyboss-theme-child/assets/js/profilerreact.js?ver=1.2.2).
# Эволюция сверяется отдельно (в модуле — формулировки PDF «Deep-Dive Keynotes» 2020).
OFFICIAL_PROFILER_LINES = {
    "lifes_work": ["Creator", "Dancer", "Changer", "Server", "Fixer", "Teacher"],
    "radiance": ["Solitude", "Marriage", "Interaction", "Friendship", "Impact", "Nurture"],
    "purpose_activation": ["Physicality (bones)", "Posture (fluids)", "Movement (blood)", "Breath (rhythm)",
                           "Voice (frequency)", "Intent (cells)"],
    "purpose_venus": ["The Anchor/Loner", "The Natural/Accuser", "The Adventurer/Escape Artist",
                      "The Nurturer/Politician", "The Leader/Victim", "The Visionary/Judge"],
    "attraction": ["Sterility/Fertility", "Lust/Passion", "Promiscuity/Playfulness", "Frigidity/Romance",
                   "Entrapment/Sensuality", "Disappointment/Innocence"],
    "iq": ["The Contemplative mind (hidden)", "The Brilliant mind (provocative)", "The Flexible mind (evasive)",
           "The Influential mind (inflexible)", "The Practical mind (defensive)", "The Objective mind (absent)"],
    "eq": ["Self-esteem/Self-sabotage", "Courtesy/Aggression", "Sympathy/Apathy", "Kindness/Meanness",
           "Respect/Disrespect", "Reverence/Alienation"],
    "sq": ["Certainty (rhythm and routine)", "Freedom (wildness and boundaries)",
           "Pleasure (adventure and understanding)", "Belonging (kinship and community)",
           "Mentoring (role models with integrity)", "Patience (time and space)"],
    "core": ["Repression/Honesty", "Denial/Ease", "Shame/Humour", "Rejection/Gentleness", "Guilt/Forgiveness",
             "Isolation/Care"],
    "vocation": ["Production (originality)", "Marketing (value)", "Strategy (implementation)", "Sales (connection)",
                 "Management (responsibility)", "Philanthropy (ethics)"],
    "culture": ["Individual", "Partnership", "Unit", "Network", "Society", "System"],
    "brand": ["Boldness (security)", "Passion (image)", "Humour (pleasure)", "Heart (feelings)",
              "Wisdom (solutions)", "Vision (education)"],
    "pearl": ["Simplicity", "Recognition", "Celebration", "Charity", "Power", "Nature"],
    "relating": ["Dissonance", "Feedback", "Assimilation", "Sharing", "Distillation", "Gratitude"],
    "stability": ["Self Discipline", "Fearlessness", "Surrender", "Service", "Coherence", "Grounding"],
    "creativity": ["Timing", "Cultivation", "Alchemy", "Authenticity", "Crystallisation", "Synchronicity"],
}


def _parts(text):
    parts = (x.strip().lower() for x in text.replace(" / ", "/").split("/"))
    return frozenset(x[4:] if x.startswith("the ") else x for x in parts)


def test_line_keynotes_match_official_profiler():
    for theme, lines in OFFICIAL_PROFILER_LINES.items():
        for i, official in enumerate(lines, start=1):
            ours = LINE_KEYNOTES[theme][i]
            # порядок частей у «The Loner / Anchor» в справке genekeys.com обратный — сравниваем множества
            en = ours["en"]
            if "(" not in official:  # у Attraction 4 в модуле добавлено пояснение из профиля 2012 г.
                en = en.split(" (")[0]
            assert _parts(en) == _parts(official), (theme, i, ours["en"], official)
            assert ours["status"] == "official", (theme, i)
    # после сверки во всех таблицах нет вторичных / ненайденных ключевых слов
    assert all(ln["status"] == "official" for lines in LINE_KEYNOTES.values() for ln in lines.values())


def test_corrected_keynotes_regression():
    # было по вторичным источникам → стало по официальному профайлеру
    assert LINE_KEYNOTES["lifes_work"][2]["en"] == "Dancer"            # было «Natural»
    assert LINE_KEYNOTES["purpose_activation"][6]["en"] == "Intent (cells)"  # было «Presence»
    assert LINE_KEYNOTES["core"][6]["en"] == "Isolation / Care"         # было «Separation / Self-care»
    assert LINE_KEYNOTES["core"][1]["en"] == "Repression / Honesty"     # было «… / Self-honesty»
    assert [LINE_KEYNOTES["culture"][i]["en"] for i in (2, 3, 5)] == ["Partnership", "Unit", "Society"]


def test_star_pearl_spheres_have_official_lines():
    assert {s["id"]: (s["sequence"], s["lines"]) for s in EXTENDED_SPHERES} == {
        "relating": ("star_pearl", "relating"), "stability": ("star_pearl", "stability"),
        "creativity": ("star_pearl", "creativity")}
    r = calculate(T["T1"][0])
    for sid in ("relating", "stability", "creativity"):
        kn = r["spheres"][sid]["line_keynote"]
        assert kn["status"] == "official" and kn["en"] == OFFICIAL_PROFILER_LINES[sid][r["spheres"][sid]["line"] - 1]


def test_pathways_official_sphere_pairs():
    # pathwayMappings официального профайлера + описания уроков («The Pathway of … connects …»)
    pairs = {p["en"]: (tuple(p["from"]), p["to"]) for seq in SEQUENCES.values() for p in seq["pathways"]}
    assert pairs == {
        "Challenge": (("lifes_work",), "evolution"), "Breakthrough": (("evolution",), "radiance"),
        "Core Stability": (("radiance",), "purpose"),
        "Dharma": (("purpose",), "attraction"), "Karma": (("attraction",), "iq"), "Intelligence": (("iq",), "eq"),
        "Love": (("eq",), "sq"), "Realisation": (("sq",), "core"),
        "Initiative": (("vocation",), "culture"), "Growth": (("culture",), "brand"),
        "Service": (("brand",), "vocation"), "Quantum": (("brand", "vocation", "culture"), "pearl"),
    }
    assert len(pairs) == 12  # «12 Pathways that link together the 11 Spheres» (официальный профиль 2012)
    for seq in SEQUENCES.values():
        for p in seq["pathways"]:
            assert set(p["from"]) | {p["to"]} <= set(seq["spheres"])
    r = calculate(T["T1"][0])
    assert [p["en"] for p in r["sequences"]["venus"]["pathways"]] == ["Dharma", "Karma", "Intelligence", "Love",
                                                                       "Realisation"]


def test_codon_rings_match_official_table():
    # https://genekeys.com/codon-ring/ (официальная таблица: название, ключи, аминокислота), 14.10.2026
    official = {
        "Ring of Alchemy": [6, 40, 47, 64], "Ring of Destiny": [34, 43], "Ring of Divinity": [22, 36, 37, 63],
        "Ring of Fire": [1, 14], "Ring of Gaia": [19, 60, 61], "Ring of Humanity": [10, 17, 21, 25, 38, 51],
        "Ring of the Illuminati": [44, 50], "Ring of Illusion": [28, 32],
        "Ring of Life and Death": [3, 20, 23, 24, 27, 42], "Ring of Light": [5, 9, 11, 26],
        "Ring of Matter": [18, 46, 48, 57], "Ring of Miracles": [35], "Ring of No Return": [31, 62],
        "Ring of Origin": [41], "Ring of Prosperity": [16, 45], "Ring of Purification": [13, 30],
        "Ring of Seeking": [15, 39, 52, 53, 54, 58], "Ring of Trials": [12, 33, 56],
        "Ring of Union": [4, 7, 29, 59], "Ring of Water": [2, 8], "Ring of the Whirlwind": [49, 55],
    }
    assert {r["en"]: sorted(r["keys"]) for r in CODON_RINGS} == official


def test_extended_spheres_sources():
    r = calculate(T["T1"][0])
    assert {"relating", "stability", "creativity"} <= set(r["spheres"])
    assert r["spheres"]["relating"]["source"] == {"side": "personality", "side_ru": r["spheres"]["iq"]["source"]["side_ru"],
                                                  "body": "mercury", "body_ru": "Меркурий"}
    r2 = calculate(T["T1"][0], include_extended=False)
    assert "relating" not in r2["spheres"]


def test_sphere_mapping_matches_official_table():
    # https://genekeys.com/docs/what-planets-does-each-sphere-of-the-golden-path-profile-correlate-to/
    official = {"lifes_work": ("personality", "sun"), "brand": ("personality", "sun"),
                "evolution": ("personality", "earth"), "radiance": ("design", "sun"),
                "purpose": ("design", "earth"), "attraction": ("design", "moon"),
                "iq": ("personality", "venus"), "eq": ("personality", "mars"), "sq": ("design", "venus"),
                "core": ("design", "mars"), "vocation": ("design", "mars"), "culture": ("design", "jupiter"),
                "pearl": ("personality", "jupiter")}
    assert {s["id"]: (s["side"], s["body"]) for s in SPHERES} == official


# ---------------------------------------------------------------------------
# 4. Граничные случаи и формат
# ---------------------------------------------------------------------------

def test_unknown_time_day_scan():
    r = calculate(BirthInput(1990, 5, 15, place="Москва"))
    scan = r["time_scan"]
    assert "culture" in scan["stable"]
    # 15.05.1990 Солнце переходит из ключа 23 в ключ 8 (24°30′ Тельца) — Дело жизни неустойчиво
    assert scan["variable"]["lifes_work"] == ["23.6", "8.1"]
    assert "attraction" in scan["variable"]
    assert any("неизвестно" in w for w in r["warnings"])


def test_unknown_time_and_place():
    r = calculate(BirthInput(2004, 2, 29))
    assert r["time_scan"]["samples"] > 280
    assert "culture" in r["time_scan"]["stable"]


def test_time_without_tz_raises():
    with pytest.raises(ValueError):
        calculate(BirthInput(1990, 5, 15, 14, 30))


def test_output_contract_and_json():
    r = calculate(T["T3"][0])
    for k in ("method", "variant", "inputs_used", "warnings", "spheres", "sequences", "profile", "checks", "steps"):
        assert k in r
    assert r["method"] == "gene_keys"
    assert len(r["steps"]) >= 5
    sp = r["spheres"]["lifes_work"]
    assert sp["shadow"]["ru"] == "Слабость" and sp["gift"]["en"] == "Equality"
    assert sp["programming_partner"] == 40 and r["spheres"]["evolution"]["key"] == 40
    assert sp["codon_ring"]["en"] == "Ring of Divinity"
    json.dumps(r, ensure_ascii=False)
