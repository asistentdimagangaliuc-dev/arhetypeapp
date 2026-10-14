"""Тесты модуля 14: соционика и эннеаграмма (calculators/typology.py).

Независимые эталонные векторы:
* Таблица интертипных отношений 16×16 — Wikisocion:
  https://wikisocion.github.io/content/intertype.html
* Та же таблица, независимый второй эталон (В. Ляшкявичюс, ученик Аугустинавичюте) — Cyclowiki:
  https://cyclowiki.org/wiki/Шаблон:Таблица_интертипных_отношений
* Список отношений ИЛЭ (благодетель ЛСЭ, ревизор ЭИИ и т.д.) — Wikisocion, страница ILE:
  https://wikisocion.github.io/content/ILE.html
* Отношения внутри клубов и темпераментов — Wikisocion: https://wikisocion.github.io/content/club.html ,
  https://wikisocion.github.io/content/temperament.html
* Модель А всех 16 ТИМов (буквы Гуленко) — Wikipedia «Socionics»:
  https://en.wikipedia.org/wiki/Socionics
* Признаки Рейнина для 16 ТИМов — Wikisocion: https://wikisocion.github.io/content/reinin_dich.html
* Стрелы эннеаграммы «1-4-2-8-5-7-1», «9-6-3-9» (стресс) и обратные (рост) — Enneagram Institute:
  https://www.enneagraminstitute.com/how-the-enneagram-system-works
* Карта Эйнштейна: Солнце 23°30′ Рыб (Astro-Databank, рейтинг AA):
  https://www.astro.com/astro-databank/Einstein,_Albert
"""
from __future__ import annotations

import json
import random

import pytest

from calculators import typology as T
from calculators.common.time import BirthInput

# --- эталон Wikisocion (https://wikisocion.github.io/content/intertype.html), строки/столбцы в этом порядке
WS_ORDER = "ILE SEI ESE LII EIE LSI SLE IEI SEE ILI LIE ESI LSE EII IEE SLI".split()
WS_TABLE = """
ILE Ide. Dual Act. Mirr +Ben +Sup Bus. Mrg. Sego Ext. Qua. Conf Ben+ Sup+ Kin. S-d.
SEI Dual Ide. Mirr Act. +Sup +Ben Mrg. Bus. Ext. Sego Conf Qua. Sup+ Ben+ S-d. Kin.
ESE Act. Mirr Ide. Dual Kin. S-d. Ben+ Sup+ Qua. Conf Sego Ext. Bus. Mrg. +Ben +Sup
LII Mirr Act. Dual Ide. S-d. Kin. Sup+ Ben+ Conf Qua. Ext. Sego Mrg. Bus. +Sup +Ben
EIE Ben+ Sup+ Kin. S-d. Ide. Dual Act. Mirr +Ben +Sup Bus. Mrg. Sego Ext. Qua. Conf
LSI Sup+ Ben+ S-d. Kin. Dual Ide. Mirr Act. +Sup +Ben Mrg. Bus. Ext. Sego Conf Qua.
SLE Bus. Mrg. +Ben +Sup Act. Mirr Ide. Dual Kin. S-d. Ben+ Sup+ Qua. Conf Sego Ext.
IEI Mrg. Bus. +Sup +Ben Mirr Act. Dual Ide. S-d. Kin. Sup+ Ben+ Conf Qua. Ext. Sego
SEE Sego Ext. Qua. Conf Ben+ Sup+ Kin. S-d. Ide. Dual Act. Mirr +Ben +Sup Bus. Mrg.
ILI Ext. Sego Conf Qua. Sup+ Ben+ S-d. Kin. Dual Ide. Mirr Act. +Sup +Ben Mrg. Bus.
LIE Qua. Conf Sego Ext. Bus. Mrg. +Ben +Sup Act. Mirr Ide. Dual Kin. S-d. Ben+ Sup+
ESI Conf Qua. Ext. Sego Mrg. Bus. +Sup +Ben Mirr Act. Dual Ide. S-d. Kin. Sup+ Ben+
LSE +Ben +Sup Bus. Mrg. Sego Ext. Qua. Conf Ben+ Sup+ Kin. S-d. Ide. Dual Act. Mirr
EII +Sup +Ben Mrg. Bus. Ext. Sego Conf Qua. Sup+ Ben+ S-d. Kin. Dual Ide. Mirr Act.
IEE Kin. S-d. Ben+ Sup+ Qua. Conf Sego Ext. Bus. Mrg. +Ben +Sup Act. Mirr Ide. Dual
SLI S-d. Kin. Sup+ Ben+ Conf Qua. Ext. Sego Mrg. Bus. +Sup +Ben Mirr Act. Dual Ide.
"""

# --- Модель А, Wikipedia «Socionics» (буквы Гуленко: P=Te E=Fe F=Se I=Ne L=Ti R=Fi S=Si T=Ni)
WIKI_MODEL_A = {
    "ESTj": "P1 S2 E3 T4 R5 I6 L7 F8", "ENTj": "P1 T2 E3 S4 R5 F6 L7 I8",
    "ESFj": "E1 S2 P3 T4 L5 I6 R7 F8", "ENFj": "E1 T2 P3 S4 L5 F6 R7 I8",
    "ESTp": "F1 L2 I3 R4 T5 E6 S7 P8", "ESFp": "F1 R2 I3 L4 T5 P6 S7 E8",
    "ENTp": "I1 L2 F3 R4 S5 E6 T7 P8", "ENFp": "I1 R2 F3 L4 S5 P6 T7 E8",
    "ISTp": "S1 P2 T3 E4 I5 R6 F7 L8", "INTp": "T1 P2 S3 E4 F5 R6 I7 L8",
    "ISFp": "S1 E2 T3 P4 I5 L6 F7 R8", "INFp": "T1 E2 S3 P4 F5 L6 I7 R8",
    "ISTj": "L1 F2 R3 I4 E5 T6 P7 S8", "ISFj": "R1 F2 L3 I4 P5 T6 E7 S8",
    "INTj": "L1 I2 R3 F4 E5 S6 P7 T8", "INFj": "R1 I2 L3 F4 P5 S6 E7 T8",
}
GULENKO = {"P": "Te", "E": "Fe", "F": "Se", "I": "Ne", "L": "Ti", "R": "Fi", "S": "Si", "T": "Ni"}

# --- Признаки Рейнина, Wikisocion (https://wikisocion.github.io/content/reinin_dich.html), порядок столбцов:
# judicious/decisive, subjectivist/objectivist, democratic/aristocratic, process/result, carefree/farsighted,
# yielding/obstinate, static/dynamic, tactical/strategic, constructivist/emotivist, positivist/negativist, asking/declaring
WS_REININ = {
    "ILE": "judicious subjectivist democratic process carefree yielding static tactical constructivist positivist asking",
    "SEI": "judicious subjectivist democratic process carefree yielding dynamic strategic emotivist negativist declaring",
    "LII": "judicious subjectivist democratic result farsighted obstinate static strategic emotivist negativist asking",
    "ESE": "judicious subjectivist democratic result farsighted obstinate dynamic tactical constructivist positivist declaring",
    "EIE": "decisive subjectivist aristocratic process carefree obstinate dynamic strategic constructivist negativist asking",
    "LSI": "decisive subjectivist aristocratic process carefree obstinate static tactical emotivist positivist declaring",
    "IEI": "decisive subjectivist aristocratic result farsighted yielding dynamic tactical emotivist positivist asking",
    "SLE": "decisive subjectivist aristocratic result farsighted yielding static strategic constructivist negativist declaring",
    "SEE": "decisive objectivist democratic process farsighted obstinate static strategic emotivist positivist asking",
    "ILI": "decisive objectivist democratic process farsighted obstinate dynamic tactical constructivist negativist declaring",
    "ESI": "decisive objectivist democratic result carefree yielding static tactical constructivist negativist asking",
    "LIE": "decisive objectivist democratic result carefree yielding dynamic strategic emotivist positivist declaring",
    "LSE": "judicious objectivist aristocratic process farsighted yielding dynamic tactical emotivist negativist asking",
    "EII": "judicious objectivist aristocratic process farsighted yielding static strategic constructivist positivist declaring",
    "SLI": "judicious objectivist aristocratic result carefree obstinate dynamic strategic constructivist positivist asking",
    "IEE": "judicious objectivist aristocratic result carefree obstinate static tactical emotivist negativist declaring",
}
REININ_KEYS = ["judicious/decisive", "subjectivist/objectivist", "democratic/aristocratic", "process/result",
               "carefree/farsighted", "yielding/obstinate", "static/dynamic", "tactical/strategic",
               "constructivist/emotivist", "positivist/negativist", "asking/declaring"]

WS_ABBR = {v["wikisocion"]: k for k, v in T.RELATIONS.items()}


# ============================ соционика: структура ============================

def test_sixteen_tims_unique():
    assert len(T.TIMS) == 16
    assert len({t["letters"] for t in T.TIMS.values()}) == 16
    assert len({(t["leading"], t["creative"]) for t in T.TIMS.values()}) == 16


@pytest.mark.parametrize("letters,expected", list(WIKI_MODEL_A.items()))
def test_model_a_matches_wikipedia(letters, expected):
    k = T.resolve_tim(letters)
    exp = [GULENKO[tok[0]] for tok in expected.split()]
    assert T.TIMS[k]["model_a"] == exp


def test_relation_table_matches_wikisocion_all_256_cells():
    rows = [r.split() for r in WS_TABLE.strip().splitlines()]
    mine = T.relation_table()
    for row in rows:
        a, cells = row[0], row[1:]
        for b, cell in zip(WS_ORDER, cells):
            assert mine[a][b] == WS_ABBR[cell], (a, b, cell, mine[a][b])


# --- второй, независимый эталон: таблица В. Ляшкявичюса (ученика А. Аугустинавичюте), Cyclowiki
# https://cyclowiki.org/wiki/Шаблон:Таблица_интертипных_отношений
# Т тождество, Д дуал, А активация, З зеркало, ро родственные, дел деловые, пД полудуал, м миражные,
# СЭ суперэго, пп полная противоположность (погашение), квт квазитождество, К конфликт,
# П/п — заказ (в строке заказчик / подзаказный), Р/р — ревизия (в строке ревизор / подревизный).
CW_ORDER = "ИЛЭ СЭИ ЭСЭ ЛИИ ЭИЭ ЛСИ СЛЭ ИЭИ СЭЭ ИЛИ ЛИЭ ЭСИ ЛСЭ ЭИИ ИЭЭ СЛИ".split()
CW_TABLE = """
ИЛЭ Т Д А З П Р дел м СЭ пп квт К п р ро пД
СЭИ Д Т З А Р П м дел пп СЭ К квт р п пД ро
ЭСЭ А З Т Д ро пД п р квт К СЭ пп дел м П Р
ЛИИ З А Д Т пД ро р п К квт пп СЭ м дел Р П
ЭИЭ п р ро пД Т Д А З П Р дел м СЭ пп квт К
ЛСИ р п пД ро Д Т З А Р П м дел пп СЭ К квт
СЛЭ дел м П Р А З Т Д ро пД п р квт К СЭ пп
ИЭИ м дел Р П З А Д Т пД ро р п К квт пп СЭ
СЭЭ СЭ пп квт К п р ро пД Т Д А З П Р дел м
ИЛИ пп СЭ К квт р п пД ро Д Т З А Р П м дел
ЛИЭ квт К СЭ пп дел м П Р А З Т Д ро пД п р
ЭСИ К квт пп СЭ м дел Р П З А Д Т пД ро р п
ЛСЭ П Р дел м СЭ пп квт К п р ро пД Т Д А З
ЭИИ Р П м дел пп СЭ К квт р п пД ро Д Т З А
ИЭЭ ро пД п р квт К СЭ пп дел м П Р А З Т Д
СЛИ пД ро р п К квт пп СЭ м дел Р П З А Д Т
"""
CW_ABBR = {"Т": "identity", "Д": "duality", "А": "activation", "З": "mirror", "ро": "kindred", "дел": "business",
           "пД": "semi_duality", "м": "mirage", "СЭ": "super_ego", "пп": "extinguishment", "квт": "quasi_identity",
           "К": "conflict", "П": "benefactor_of", "п": "beneficiary_of", "Р": "supervisor_of", "р": "supervisee_of"}


def test_relation_table_matches_cyclowiki_lyashkyavichus_all_256_cells():
    for row in CW_TABLE.strip().splitlines():
        a, *cells = row.split()
        for b, cell in zip(CW_ORDER, cells):
            assert T.intertype_relation(a, b)["relation"] == CW_ABBR[cell], (a, b, cell)


def test_club_and_temperament_internal_relations():
    # Wikisocion «Club»: внутри клуба — тождество, зеркало, погашение, квазитождество;
    # Wikisocion «Temperament»: внутри темперамента — тождество, деловые, суперэго, родственные.
    for field, allowed in (("club", {"identity", "mirror", "extinguishment", "quasi_identity"}),
                           ("temperament", {"identity", "business", "super_ego", "kindred"})):
        groups: dict[str, list[str]] = {}
        for k, t in T.TIMS.items():
            groups.setdefault(t[field], []).append(k)
        assert len(groups) == 4 and all(len(v) == 4 for v in groups.values())
        for members in groups.values():
            assert {T.intertype_relation(a, b)["relation"] for a in members for b in members} == allowed
    assert {k for k, t in T.TIMS.items() if t["club"].startswith("Исследователи")} == {"ILE", "ILI", "LIE", "LII"}
    assert T.TIMS["ILE"]["temperament"].startswith("гибко-маневренный")   # Wikisocion ILE: «EP temperament»


def test_ile_relations_from_wikisocion_type_page():
    # https://wikisocion.github.io/content/ILE.html — «ILE Intertype relations»
    p = T.partners("ИЛЭ")
    assert p["duality"] == "СЭИ"
    assert p["activation"] == "ЭСЭ"
    assert p["mirror"] == "ЛИИ"
    assert p["kindred"] == "ИЭЭ"
    assert p["semi_duality"] == "СЛИ"
    assert p["beneficiary_of"] == "ЛСЭ"      # Benefactor: LSE
    assert p["supervisee_of"] == "ЭИИ"       # Supervisor: EII
    assert p["super_ego"] == "СЭЭ"
    assert p["extinguishment"] == "ИЛИ"
    assert p["quasi_identity"] == "ЛИЭ"
    assert p["conflict"] == "ЭСИ"
    assert p["business"] == "СЛЭ"
    assert p["mirage"] == "ИЭИ"
    assert p["benefactor_of"] == "ЭИЭ"       # Beneficiary: EIE
    assert p["supervisor_of"] == "ЛСИ"       # Supervisee: LSI


def test_relation_properties():
    tab = T.relation_table()
    for a in T.TIM_ORDER:
        # каждая строка — перестановка 16 направленных отношений
        assert sorted(tab[a].values()) == sorted(T.RELATIONS)
        assert tab[a][a] == "identity"
        for b in T.TIM_ORDER:
            r, back = tab[a][b], tab[b][a]
            if T.RELATIONS[r]["symmetric"]:
                assert back == r
            else:
                assert back == T.RELATIONS[r]["inverse"]


def test_duality_is_involution_and_within_quadra():
    for a in T.TIM_ORDER:
        d = T.resolve_tim(T.partners(a)["duality"])
        assert T.resolve_tim(T.partners(d)["duality"]) == a
        assert T.TIMS[a]["quadra"] == T.TIMS[d]["quadra"]
        # дуалы различаются по E/I, N/S, T/F и совпадают по рациональности
        la, ld = T.TIMS[a]["letters"], T.TIMS[d]["letters"]
        assert [x != y for x, y in zip(la, ld)] == [True, True, True, False]


def test_quadra_members_and_values():
    # Wikisocion «Quadra»: Alpha ILE SEI LII ESE; Beta SLE IEI EIE LSI; Gamma SEE ILI LIE ESI; Delta IEE SLI LSE EII
    groups = {"alpha": {"ILE", "SEI", "LII", "ESE"}, "beta": {"SLE", "IEI", "EIE", "LSI"},
              "gamma": {"SEE", "ILI", "LIE", "ESI"}, "delta": {"IEE", "SLI", "LSE", "EII"}}
    for q, members in groups.items():
        assert {k for k, t in T.TIMS.items() if t["quadra"] == q} == members
        for a in members:
            for b in members:
                assert T.intertype_relation(a, b)["relation"] in {"identity", "duality", "activation", "mirror"}


def test_supervision_and_benefit_rings_have_length_4():
    for rel in ("supervisor_of", "benefactor_of"):
        for start in T.TIM_ORDER:
            ring, cur = [start], start
            for _ in range(4):
                cur = T.resolve_tim(T.partners(cur)[rel])
                ring.append(cur)
            assert ring[4] == start and len(set(ring[:4])) == 4
            assert len({T.TIMS[x]["quadra"] for x in ring[:4]}) == 4   # по одному ТИМу из каждой квадры
    # кольцо ревизии ИЛЭ → ЛСИ → СЭЭ → ЭИИ → ИЛЭ
    ring, cur = [], "ILE"
    for _ in range(4):
        ring.append(T.TIMS[cur]["code_ru"])
        cur = T.resolve_tim(T.partners(cur)["supervisor_of"])
    assert ring == ["ИЛЭ", "ЛСИ", "СЭЭ", "ЭИИ"]


@pytest.mark.parametrize("tim", list(WS_REININ))
def test_reinin_matches_wikisocion(tim):
    mine = T.reinin_traits(tim)
    expected = WS_REININ[tim].split()
    for key, exp in zip(REININ_KEYS, expected):
        assert mine[key].endswith(f"({exp})"), (tim, key, mine[key], exp)


def test_resolve_tim_forms_and_mbti_caveat():
    assert T.resolve_tim("ИЛЭ") == T.resolve_tim("ENTp") == T.resolve_tim("Дон Кихот") == "ILE"
    with pytest.raises(ValueError):
        T.resolve_tim("INTJ")          # неоднозначно: MBTI или соционика?
    lii = T.TIMS["LII"]
    assert lii["letters"] == "INTj" and lii["mbti_by_letters"] == "INTJ" and lii["mbti_by_functions"] == "INTP"
    ile = T.TIMS["ILE"]
    assert ile["mbti_by_letters"] == ile["mbti_by_functions"] == "ENTP"


def test_model_a_rejects_invalid_ego():
    with pytest.raises(ValueError):
        T.model_a("Ne", "Ni")
    with pytest.raises(ValueError):
        T.model_a("Ne", "Se")


# ============================ эннеаграмма: структура ============================

def _cycle(mapping, start):
    seq, cur = [start], mapping[start]
    while cur != start:
        seq.append(cur)
        cur = mapping[cur]
    return seq + [start]


def test_arrows_match_enneagram_institute():
    assert _cycle(T.DISINTEGRATION, 1) == [1, 4, 2, 8, 5, 7, 1]
    assert _cycle(T.DISINTEGRATION, 9) == [9, 6, 3, 9]
    assert _cycle(T.INTEGRATION, 1) == [1, 7, 5, 8, 2, 4, 1]
    assert _cycle(T.INTEGRATION, 9) == [9, 3, 6, 9]
    assert _cycle(T.INTEGRATION, 3) == [3, 6, 9, 3]
    for t in range(1, 10):
        assert T.DISINTEGRATION[T.INTEGRATION[t]] == t      # линии одни и те же, направления обратны
        assert T.INTEGRATION[t] != t


@pytest.mark.parametrize("t,growth,stress", [(1, 7, 4), (2, 4, 8), (3, 6, 9), (4, 1, 2), (5, 8, 7),
                                             (6, 9, 3), (7, 5, 1), (8, 2, 5), (9, 3, 6)])
def test_arrows_per_type_pages(t, growth, stress):
    # https://www.enneagraminstitute.com/type-1 … type-9
    info = T.enneagram_type_info(t)
    assert info["integration"] == growth and info["disintegration"] == stress


def test_wings_centers_groups():
    assert T.wings(1) == (9, 2) and T.wings(9) == (8, 1) and T.wings(5) == (4, 6)
    for groups in (T.CENTERS, T.HORNEVIAN, T.HARMONIC):
        assert sorted(x for g in groups.values() for x in g) == list(range(1, 10))
    assert T.enneagram_type_info(8)["center"] == "gut"
    assert T.enneagram_type_info(3)["hornevian"] == "assertive"
    assert T.enneagram_type_info(9)["harmonic"] == "positive_outlook"
    with pytest.raises(ValueError):
        T.wings(0)


# ============================ опросник ============================

def test_question_bank_integrity():
    ids = list(T.SOCIONICS_ITEMS) + list(T.ENNEAGRAM_ITEMS) + list(T.INSTINCT_ITEMS) \
        + list(T.INSTINCT_FC_ITEMS) + list(T.ENNEAGRAM_FOLLOWUP_ITEMS)
    assert len(ids) == len(set(ids))
    base = [i for i in T.SOCIONICS_ITEMS.values() if not i.extra]
    assert len(base) == 24 and len(T.ENNEAGRAM_ITEMS) == 36 and len(T.INSTINCT_ITEMS) == 12
    for scale, (pos, _neg) in T.SOC_POLES.items():
        items = [i for i in base if i.scale == scale]
        assert len(items) == 6
        assert sum(i.pole_a == pos for i in items) == 3      # полюса сбалансированы между A и B
    q = T.get_questionnaire("all")
    assert len(q["socionics"]) == 24 and len(q["enneagram"]) == 36 and len(q["instincts"]) == 15
    q2 = T.get_questionnaire("all", include_extra=True)
    assert len(q2["socionics"]) == 32 and len(q2["enneagram_followup"]) == 10
    # соседние вопросы эннеаграммы не относятся к одному типу
    keys = [x["id"].split("-")[1] for x in q["enneagram"]]
    assert all(a != b for a, b in zip(keys, keys[1:]))


def _soc_answers(letters: str, strong: bool = True) -> dict:
    target = {"EI": letters[0], "NS": letters[1], "TF": letters[2], "JP": letters[3].upper()}
    out = {}
    for iid, it in T.SOCIONICS_ITEMS.items():
        if it.extra:
            continue
        a = "A" if it.pole_a == target[it.scale] else "B"
        out[iid] = a if strong else a.lower()
    return out


def _ennea_answers(core: int, wing: int) -> dict:
    out = {}
    for iid, it in T.ENNEAGRAM_ITEMS.items():
        t = int(it.key)
        out[iid] = 4 if t == core else (2 if t == wing else 1)
    return out


@pytest.mark.parametrize("tim", T.TIM_ORDER)
def test_pure_socionics_profiles(tim):
    let = T.TIMS[tim]["letters"]
    r = T.score_socionics(_soc_answers(let))
    assert r["tim_en"] == tim and r["confidence"]["level"] == "high"
    assert r["consistency_flags"] == []
    r2 = T.score_socionics(_soc_answers(let, strong=False))
    assert r2["tim_en"] == tim and r2["confidence"]["level"] == "high"


@pytest.mark.parametrize("core", range(1, 10))
def test_pure_enneagram_profiles(core):
    w = T.wings(core)[1]
    r = T.score_enneagram(_ennea_answers(core, w))
    assert r["type"] == core and r["wing"] == w and r["label"] == f"{core}w{w}"
    assert r["confidence"]["level"] == "high"


def test_scoring_is_deterministic_and_order_independent():
    ans = {**_soc_answers("ENFp"), **_ennea_answers(7, 8)}
    keys = list(ans)
    random.Random(42).shuffle(keys)
    shuffled = {k: ans[k] for k in keys}
    r1, r2 = T.score_all(ans), T.score_all(shuffled)
    assert json.dumps(r1, sort_keys=True, ensure_ascii=False, default=str) == \
        json.dumps(r2, sort_keys=True, ensure_ascii=False, default=str)
    assert r1["socionics"]["tim"] == "ИЭЭ" and r1["enneagram"]["type"] == 7
    assert r1 == T.score_all(ans)


def test_cyrillic_letters_accepted_and_invalid_rejected():
    ans = {k: v.replace("A", "А").replace("B", "Б") for k, v in _soc_answers("ISTj").items()}
    assert T.score_socionics(ans)["tim"] == "ЛСИ"
    with pytest.raises(ValueError):
        T.score_socionics({"SO-EI-1": "C"})
    with pytest.raises(ValueError):
        T.score_enneagram({"EN-1-1": 5})
    with pytest.raises(ValueError):
        T.score_enneagram({"EN-1-1": True})
    assert T.score_all({"XX-1": 1, "EN-1-1": 2})["unknown_keys"] == ["XX-1"]


def test_socionics_unresolved_tie_gives_candidates():
    ans = _soc_answers("ISTj")
    # T/F: равные баллы и нейтральный ключевой пункт → не определено
    for iid in ("SO-TF-1", "SO-TF-2", "SO-TF-3", "SO-TF-4", "SO-TF-5", "SO-TF-6"):
        ans[iid] = "?"
    r = T.score_socionics(ans)
    assert r["tim"] is None and sorted(r["candidates"]) == ["ЛСИ", "ЭСИ"]
    assert r["confidence"]["level"] == "undetermined"
    assert set(r["followup"]["items"]) == {"SO-TF-X1", "SO-TF-X2"}


def test_enneagram_wing_tie_and_instinct_tie():
    ans = _ennea_answers(5, 4)
    for i in range(1, 5):
        ans[f"EN-6-{i}"] = 2          # крылья 4 и 6 равны
    r = T.score_enneagram(ans)
    assert r["type"] == 5 and r["wing"] is None and r["label"] == "5"
    ans.update({f"IN-{k}-{i}": 2 for k in ("SP", "SO", "SX") for i in range(1, 5)})
    r = T.score_enneagram(ans)
    assert r["instincts"]["dominant"] is None and r["instincts"]["stacking"] is None
    assert r["instincts"]["confidence"] == "undetermined"


# ============================ разобранные примеры из базы знаний ============================

EX1 = {
    "SO-EI-1": "B", "SO-EI-2": "A", "SO-EI-3": "b", "SO-EI-4": "A", "SO-EI-5": "B", "SO-EI-6": "a",
    "SO-NS-1": "A", "SO-NS-2": "B", "SO-NS-3": "a", "SO-NS-4": "B", "SO-NS-5": "A", "SO-NS-6": "?",
    "SO-TF-1": "A", "SO-TF-2": "B", "SO-TF-3": "A", "SO-TF-4": "b", "SO-TF-5": "a", "SO-TF-6": "B",
    "SO-JP-1": "A", "SO-JP-2": "B", "SO-JP-3": "a", "SO-JP-4": "B", "SO-JP-5": "A", "SO-JP-6": "b",
    "IN-FC-1": "a", "IN-FC-2": "B", "IN-FC-3": "A",
}
_E1 = {1: [4, 3, 4, 3], 2: [1, 1, 2, 1], 3: [2, 1, 2, 1], 4: [1, 1, 1, 0], 5: [2, 2, 2, 1],
       6: [3, 2, 2, 1], 7: [0, 1, 1, 1], 8: [1, 2, 1, 1], 9: [3, 2, 2, 2]}
_I1 = {"SP": [4, 3, 4, 3], "SO": [2, 3, 2, 3], "SX": [1, 1, 0, 1]}

EX2 = {
    "SO-EI-1": "b", "SO-EI-2": "A", "SO-EI-3": "B", "SO-EI-4": "a", "SO-EI-5": "b", "SO-EI-6": "A",
    "SO-NS-1": "A", "SO-NS-2": "b", "SO-NS-3": "A", "SO-NS-4": "b", "SO-NS-5": "a", "SO-NS-6": "a",
    "SO-TF-1": "a", "SO-TF-2": "a", "SO-TF-3": "B", "SO-TF-4": "b", "SO-TF-5": "A", "SO-TF-6": "a",
    "SO-JP-1": "A", "SO-JP-2": "b", "SO-JP-3": "a", "SO-JP-4": "B", "SO-JP-5": "a", "SO-JP-6": "b",
    "IN-FC-1": "b", "IN-FC-2": "b", "IN-FC-3": "a",
}
_E2 = {1: [2, 2, 1, 2], 2: [2, 2, 1, 2], 3: [1, 1, 1, 1], 4: [1, 2, 1, 1], 5: [2, 2, 1, 2],
       6: [3, 3, 3, 2], 7: [1, 1, 1, 1], 8: [1, 0, 1, 0], 9: [4, 3, 3, 1]}
_I2 = {"SP": [3, 2, 3, 2], "SO": [3, 3, 2, 3], "SX": [1, 2, 1, 1]}

for _ex, _e, _i in ((EX1, _E1, _I1), (EX2, _E2, _I2)):
    _ex.update({f"EN-{t}-{n + 1}": v for t, vals in _e.items() for n, v in enumerate(vals)})
    _ex.update({f"IN-{k}-{n + 1}": v for k, vals in _i.items() for n, v in enumerate(vals)})


def test_example_1_clear_profile():
    s = T.score_socionics(EX1)
    assert s["tim"] == "ЛСИ" and s["letters"] == "ISTj"
    assert {k: d["score"] for k, d in s["dichotomies"].items()} == {"EI": -10, "NS": -9, "TF": 10, "JP": 10}
    assert s["confidence"] == {"level": "high", "min_clarity": 0.75}
    assert s["dual"] == "ЭИЭ"
    e = T.score_enneagram(EX1)
    assert e["scores"] == {1: 14, 2: 5, 3: 6, 4: 3, 5: 7, 6: 8, 7: 3, 8: 5, 9: 9}
    assert e["label"] == "1w9" and e["confidence"]["level"] == "high" and e["confidence"]["margin"] == 5
    assert e["tritype"] == "163"
    # Архетип Фовр: https://www.katherinefauvre.com/tritype — «136 - The Taskmaster»
    assert e["tritype_archetype"] == {"key": "136", "name_en": "The Taskmaster",
                                      "source": "https://www.katherinefauvre.com/tritype"}
    assert e["instincts"]["scores"] == {"sp": 17, "so": 12, "sx": 3}
    assert e["instincts"]["full_stacking"] == "sp/so/sx" and e["instincts"]["confidence"] == "high"


def test_example_2_tie_breaks_and_followups():
    s = T.score_socionics(EX2)
    assert s["dichotomies"]["TF"]["score"] == 0 and s["dichotomies"]["TF"]["resolved_by"] == "anchor"
    assert s["tim"] == "ЛСИ" and s["confidence"]["level"] == "low"
    assert s["alternatives"][0]["tim"] == "ЭСИ" and s["alternatives"][0]["relation_to_main"] == "Деловые"
    assert s["followup"]["items"] == ["SO-TF-X1", "SO-TF-X2"]
    e = T.score_enneagram(EX2)
    assert e["type"] == 9 and e["confidence"]["resolved_by"] == "anchor" and e["confidence"]["level"] == "low"
    assert e["followup"]["items"] == ["FU-6v9"]
    r2 = dict(EX2, **{"SO-TF-X1": "B", "SO-TF-X2": "a", "FU-6v9": "B"})
    s2 = T.score_socionics(r2)
    assert s2["tim"] == "ЭСИ" and s2["dichotomies"]["TF"]["score"] == -3 and s2["dichotomies"]["TF"]["max"] == 16
    assert s2["confidence"]["level"] == "low"
    e2 = T.score_enneagram(r2)
    assert e2["adjusted"][9] == 13 and e2["adjusted"][6] == 11
    assert e2["label"] == "9w1" and e2["confidence"]["level"] == "medium" and e2["tritype"] == "962"
    assert e2["tritype_archetype"]["name_en"] == "The Good Samaritan"   # «269 - The Good Samaritan»
    assert e2["instincts"]["full_stacking"] == "so/sp/sx" and e2["instincts"]["confidence"] == "medium"


def test_example_3_invalid_protocol():
    ex3 = {i: "A" for i, it in T.SOCIONICS_ITEMS.items() if not it.extra}
    ex3.update({i: 4 for i in T.ENNEAGRAM_ITEMS})
    ex3.update({i: 4 for i in T.INSTINCT_ITEMS})
    ex3.update({i: "A" for i in T.INSTINCT_FC_ITEMS})
    s = T.score_socionics(ex3)
    assert s["tim"] is None and s.get("invalid_protocol") and s["confidence"]["level"] == "undetermined"
    assert s["protocol_ok"] is False and s["followup"]["items"] == []
    e = T.score_enneagram(ex3)
    assert e["type"] is None and e["confidence"]["level"] == "undetermined"
    assert e["candidates"] == list(range(1, 10))          # ничья всех девяти, а не «1 или 2»
    assert "recommendation" in e and e["followup"]["items"] == [] and e["protocol_ok"] is False
    assert e["instincts"]["dominant"] is None


def test_mechanical_answers_with_neutral_and_side_bias():
    base = {i: "A" for i, it in T.SOCIONICS_ITEMS.items() if not it.extra}
    # один «?» не спасает механический протокол
    r = T.score_socionics(dict(base, **{"SO-EI-2": "?"}))
    assert r["tim"] is None and r.get("invalid_protocol") and r["protocol_ok"] is False
    # 23 «A» + 1 «b»: протокол формально действителен, но перекос сторон → protocol_ok = False
    r = T.score_socionics(dict(base, **{"SO-EI-2": "b"}))
    assert r["protocol_ok"] is False and any(f.startswith("Перекос") for f in r["consistency_flags"])
    assert r["confidence"]["level"] in ("low", "undetermined")
    # у чистых профилей сторон A и B поровну — флага нет
    assert T.score_socionics(_soc_answers("ISTj"))["protocol_ok"] is True


def test_low_core_anchor_downgrades_confidence():
    ans = _ennea_answers(4, 5)
    assert T.score_enneagram(ans)["confidence"]["level"] == "high"
    ans["EN-4-1"] = 1           # ключевое утверждение ядра почти отвергнуто
    r = T.score_enneagram(ans)
    assert r["type"] == 4 and r["confidence"]["level"] == "medium"
    assert any("EN-4-1" in f for f in r["consistency_flags"])


# ============================ дата рождения: не вычисляется ============================

PERSONAS = {
    "T1": BirthInput(1990, 5, 15, 14, 30, place="Москва"),
    "T2": BirthInput(1984, 2, 4, 23, 30, place="Москва"),
    "T3": BirthInput(2004, 2, 29, 8, 15, place="Санкт-Петербург"),
    "T4": BirthInput(1879, 3, 14, 11, 30, tz="LMT", lat=48.4011, lon=9.9876),
}


@pytest.mark.parametrize("pid", list(PERSONAS))
def test_calculate_refuses_type_from_birth_date(pid):
    r = T.calculate(PERSONAS[pid])
    assert r["computable_from_birth_date"] is False
    assert r["socionics_type"] is None and r["enneagram_type"] is None
    assert "noncanonical_date_variant" not in r
    assert r["next_step"]["action"] == "run_questionnaire"
    json.dumps(r, ensure_ascii=False)


def test_noncanonical_variant_requires_explicit_request():
    with pytest.raises(PermissionError):
        T.noncanonical_date_variant(PERSONAS["T1"])


@pytest.mark.parametrize("pid,life_path,sun,mercury,soc", [
    ("T1", 3, "Телец", "Телец", None),
    ("T2", 1, "Водолей", "Козерог", None),
    ("T3", 1, "Рыбы", "Рыбы", ["ЭИИ"]),
    ("T4", 6, "Рыбы", "Овен", ["ЭИЭ"]),     # Эйнштейн: Солнце 23°30′ Рыб (ADB), сумма цифр 33 → 6
])
def test_noncanonical_variant_values_and_label(pid, life_path, sun, mercury, soc):
    r = T.calculate(PERSONAS[pid], user_explicitly_requested_date_variant=True)
    nc = r["noncanonical_date_variant"]
    assert nc["status"] == "noncanonical" and nc["label"].startswith("НЕКАНОНИЧНО")
    assert r["socionics_type"] is None and r["enneagram_type"] is None   # канонического типа нет и тут
    v = nc["variants"]
    assert v[0]["result"]["enneagram_type_claimed"] == life_path
    assert v[1]["calc"].startswith(f"Солнце: {sun}")
    assert v[2]["calc"].startswith(f"Меркурий: {mercury}")
    assert v[2]["result"]["socionics_types_claimed"] == soc


def test_einstein_sun_longitude_matches_adb():
    lon = T._sign_range(PERSONAS["T4"], "sun")["lon"]
    assert abs(lon - (330 + 23.5)) < 0.05   # ADB: 23°30′ Pisces


def test_noncanonical_without_time_flags_cusp():
    # 20.03.2004 — день равноденствия (Солнце входит в Овен 20.03.2004 ок. 06:49 UT): без времени знак неоднозначен
    r = T.noncanonical_date_variant(BirthInput(2004, 3, 20), user_explicitly_asked=True)
    assert "на границе знаков" in r["variants"][1]["calc"]


def test_tritype_archetypes_fauvre_complete():
    # https://www.katherinefauvre.com/tritype : 27 архетипов, по одному типу из каждого центра
    # («head (5, 6, 7), heart (2, 3, 4), and gut (8, 9, 1)»); «The Mentor Tritype®: 125, 152, 215, 251, 512, 521».
    from itertools import product
    from calculators.typology import TRITYPE_ARCHETYPES_EN
    keys = {"".join(sorted(f"{a}{b}{c}")) for a, b, c in product((8, 9, 1), (2, 3, 4), (5, 6, 7))}
    assert keys == set(TRITYPE_ARCHETYPES_EN) and len(keys) == 27
    assert TRITYPE_ARCHETYPES_EN["125"] == "The Mentor" and TRITYPE_ARCHETYPES_EN["479"] == "The Gentle Spirit"
    assert TRITYPE_ARCHETYPES_EN["278"] == "The Free Spirit" and TRITYPE_ARCHETYPES_EN["358"] == "The Solution Master"
