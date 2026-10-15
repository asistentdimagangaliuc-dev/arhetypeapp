"""Модуль 19. Восточная прогностика на заданный год/дату.

Три блока (подробно — knowledge-base/19-forecast-eastern.md):

* ``bazi_year`` — Ба-цзы: годовой столп (流年, граница — Личунь), 12 месячных столпов (流月) с моментами
  цзе, столп дня, текущий Столп удачи (大运) и место в нём; взаимодействия годового/месячного столпа и
  Столпа удачи с натальной картой (合/冲/刑/害/破, 三合/三会, 伏吟/反吟), божество ствола года, отношения
  с Тай Суй (值/冲/刑/害/破太岁), «征»/«晦» по 《渊海子平》, «戰/沖/和/好» удачи и года по 《滴天髓》.
* ``ninestar_year`` — Девятизвёздная Ки / летящие звёзды: звезда года и месяцев, полные карты 年盤/月盤
  (9 дворцов, прямой полёт), палата звезды рождения (回座), японские 凶方/吉方 (五黄殺, 暗剣殺, 歳破/月破,
  本命殺, 本命的殺, 月命殺, 定位対冲, 吉方, 最大吉方 в двух трактовках) и китайские годовые «ша» (太岁, 岁破,
  三煞, 五黄, 二黑).
* ``jyotish`` — Джйотиш: Вимшоттари (махадаша/антардаша/пратьянтардаша на дату и периоды года), гочара
  9 грах от натальной Луны (Чандра-лагна) и Лагны по таблицам «Пхаладипики» (гл. XXVI) с ведхой, ингрессии
  Сатурна/Юпитера/Раху/Кету за год, Саде-сати, Аштама- и Ардхаштама-Шани с датами.

Натальные карты не пересчитываются заново: используются ``calculators.bazi``, ``calculators.ninestar``,
``calculators.jyotish`` (их умолчания и опции).
"""
from __future__ import annotations

from datetime import date, datetime, timedelta, timezone

import swisseph as swe

from calculators import bazi as bz
from calculators import jyotish as jy
from calculators import ninestar as ns
from calculators.common import ephemeris as eph
from calculators.common.ephemeris import find_sun_longitude, sun_longitude
from calculators.common.time import BirthInput, jd_to_utc, julian_day_ut

UTC = timezone.utc
YEAR_DAYS = 365.2425

# ---------------------------------------------------------------------------
# Общие справочники
# ---------------------------------------------------------------------------

DIR_RU = {"N": "Север", "NE": "Северо-восток", "E": "Восток", "SE": "Юго-восток", "S": "Юг",
          "SW": "Юго-запад", "W": "Запад", "NW": "Северо-запад", "C": "Центр"}
DIR_JA = {"N": "北", "NE": "北東", "E": "東", "SE": "南東", "S": "南", "SW": "南西", "W": "西", "NW": "北西",
          "C": "中央"}
OPPOSITE = {"N": "S", "S": "N", "E": "W", "W": "E", "NE": "SW", "SW": "NE", "SE": "NW", "NW": "SE"}

#: Ветвь → сторона света (дворец Ло Шу): 子 N; 丑寅 NE; 卯 E; 辰巳 SE; 午 S; 未申 SW; 酉 W; 戌亥 NW.
BRANCH_PALACE = {0: "N", 1: "NE", 2: "NE", 3: "E", 4: "SE", 5: "SE", 6: "S", 7: "SW", 8: "SW", 9: "W",
                 10: "NW", 11: "NW"}

# ---------------------------------------------------------------------------
# Время прогноза
# ---------------------------------------------------------------------------


def _iso_min(dt: datetime) -> str:
    """Дата-время с округлением до минуты."""
    return (dt + timedelta(seconds=30)).replace(second=0, microsecond=0).strftime("%Y-%m-%d %H:%M")


def _forecast_zone(b: BirthInput, tz_opt: str | None) -> tuple["ns.Zone", str, list[str]]:
    """Пояс, в котором показываются даты прогноза (по умолчанию — пояс места рождения)."""
    warns: list[str] = []
    tz = tz_opt or b.tz
    if tz and str(tz).upper() == "LMT":
        tz = None
        if b.lat is not None and b.lon is not None:
            from calculators.common.places import tz_for_coords
            tz = tz_for_coords(b.lat, b.lon)
        warns.append(f"Рождение по LMT: даты прогноза показаны в поясе {tz or 'UTC'} (современный пояс места "
                     f"рождения). Другой пояс — опция tz.")
    if not tz:
        tz = "UTC"
        if not tz_opt:
            warns.append("Пояс прогноза неизвестен: даты показаны по UTC (опция tz).")
    return ns.Zone(tz), tz, warns


def _when(jd: float, zone: "ns.Zone") -> dict:
    """Момент JD(UT) → UTC, местное время пояса прогноза и IST (для сверки с индийскими таблицами)."""
    u = jd_to_utc(jd)
    return {"utc": _iso_min(u), "local": _iso_min(zone.to_local(u)),
            "ist": _iso_min((u + timedelta(hours=5.5)).replace(tzinfo=None))}


def _solar_year_of(jd: float) -> int:
    """Год по Личуню (立春, Солнце 315°) для момента jd."""
    y = jd_to_utc(jd).year
    return y if jd >= bz.li_chun_jd(y) else y - 1


def _jie_on_date_warning(ref_jd: float, on_date: date, zone: "ns.Zone", warnings: list[str]) -> None:
    """Предупреждение, если на дату прогноза приходится цзе (смена месяца Ба-цзы и звезды месяца Ки).

    Добавляется один раз, даже если его запрашивают оба блока (bazi и ninestar)."""
    slot = bz.month_slot(sun_longitude(ref_jd))
    mstart = find_sun_longitude(bz.JIE[slot][0], ref_jd, search_back=True)
    mend = find_sun_longitude(bz.JIE[(slot + 1) % 12][0], ref_jd, search_back=False)
    for jd_j in (mstart, mend):
        if zone.to_local(jd_to_utc(jd_j)).date() == on_date:
            w = (f"На {on_date.isoformat()} приходится цзе ({_when(jd_j, zone)['local']}): месячный столп Ба-цзы и "
                 f"звезда месяца Ки в этот день зависят от времени (расчёт — на момент {_when(ref_jd, zone)['local']}, "
                 f"опция on_time).")
            if w not in warnings:
                warnings.append(w)


# ---------------------------------------------------------------------------
# A. Ба-цзы: 流年, 流月, 大运 и взаимодействия
# ---------------------------------------------------------------------------

REL_NAMES = {
    "stem_combination": ("天干五合", "слияние стволов"),
    "stem_clash": ("天干相冲", "столкновение стволов"),
    "six_combination": ("六合", "слияние ветвей"),
    "clash": ("六冲", "столкновение ветвей"),
    "harm": ("六害", "вред"),
    "destruction": ("六破", "разрушение"),
    "punishment": ("刑", "наказание"),
    "self_punishment": ("自刑", "самонаказание"),
    "half_harmony": ("半合", "полугармония"),
    "same_branch": ("同支", "одинаковые ветви"),
    "fu_yin": ("伏吟", "Фу-инь: столп повторяет натальный (ствол и ветвь)"),
    "fan_yin": ("反吟 (天克地冲)", "Фань-инь: ствол подавляет ствол и ветви сталкиваются"),
}

TAI_SUI_RU = {
    "zhi": ("值太岁", "встреча с Тай Суй (本命年 — год своей ветви)"),
    "chong": ("冲太岁", "столкновение с Тай Суй"),
    "xing": ("刑太岁", "наказание Тай Суй"),
    "hai": ("害太岁", "вред Тай Суй"),
    "po": ("破太岁", "разрушение Тай Суй"),
}

#: «三煞» — стороны света по тройке ветви года (申子辰 → юг 巳午未, 寅午戌 → север 亥子丑,
#: 巳酉丑 → восток 寅卯辰, 亥卯未 → запад 申酉戌). Индекс тройки — bz.TRINE_OF.
SAN_SHA = {0: ("S", "巳午未"), 1: ("N", "亥子丑"), 2: ("E", "寅卯辰"), 3: ("W", "申酉戌")}


def _el_index(stem: int) -> int:
    return stem // 2


def _branch_el_index(branch: int) -> int:
    return bz.ELEMENTS.index(bz.branch_element(branch))


def _controls(a_el: int, b_el: int) -> bool:
    """Элемент a подавляет (克) элемент b: Дерево → Земля → Вода → Огонь → Металл → Дерево."""
    return (b_el - a_el) % 5 == 2


#: Правила 反吟: 'tian_ke_di_chong' — «天克地冲» (ветви 六冲 + стволы в 克; умолчание модуля, современное
#: употребление); 'clash' — 《三命通会》: «岁运与日相对，谓之返吟» (卷二 «总论岁运»), любое 六冲 столпов, включая
#: «天比地冲»; исключение — 戊辰/戊戌: «戊辰、戊戌之土为魁罡相会…不得以为反吟» (卷一).
FAN_YIN_RULES = ("tian_ke_di_chong", "clash")
_KUI_GANG_PAIR = frozenset({4, 34})        # 戊辰, 戊戌


def _pair_relations(e: int, n: int, fan_yin_rule: str = "tian_ke_di_chong") -> list[dict]:
    """Отношения внешнего столпа e (流年/流月/大运, индекс 0…59) с натальным столпом n.

    fan_yin_rule — см. FAN_YIN_RULES (по умолчанию «天克地冲»)."""
    se, be, sn, bn = e % 10, e % 12, n % 10, n % 12
    out: list[dict] = []

    def add(kind: str, detail: str, **extra) -> None:
        cn, ru = REL_NAMES[kind]
        out.append({"type": kind, "cn": cn, "ru": ru, "detail": detail, **extra})

    ps = frozenset({se, sn})
    stems = bz.STEMS[se][0] + bz.STEMS[sn][0]
    brs = bz.BRANCHES[be][0] + bz.BRANCHES[bn][0]
    if ps in bz.STEM_COMBOS:
        add("stem_combination", stems, element=bz.STEM_COMBOS[ps])
    if ps in bz.STEM_CLASHES:
        add("stem_clash", stems)
    pb = frozenset({be, bn})
    if pb in bz.SIX_COMBOS:
        add("six_combination", brs, element=bz.SIX_COMBOS[pb])
    clash = (be - bn) % 12 == 6
    if clash:
        add("clash", brs)
    if pb in bz.HARMS:
        add("harm", brs)
    if pb in bz.DESTRUCTIONS:
        add("destruction", brs)
    if pb == bz.PUNISHMENT_PAIR[0]:
        add("punishment", brs, subtype=bz.PUNISHMENT_PAIR[1])
    for grp, name in bz.PUNISHMENT_GROUPS:
        if be in grp and bn in grp and be != bn:
            add("punishment", brs, subtype=name)
    if be == bn:
        if be in bz.SELF_PUNISH:
            add("self_punishment", brs)
        if e != n:
            add("same_branch", brs)
    for (x, mid, z), el in bz.THREE_HARMONIES:
        if pb in (frozenset({x, mid}), frozenset({mid, z})):
            add("half_harmony", brs, element=el)
    if e == n:
        add("fu_yin", bz.ganzhi(e))
    elif clash:
        ee, en = _el_index(se), _el_index(sn)
        ctrl = _controls(ee, en) or _controls(en, ee)
        if fan_yin_rule == "clash":
            if frozenset({e, n}) != _KUI_GANG_PAIR:
                extra = {"cn": "反吟 (相对)", "ru": "Фань-инь: ветви столпов сталкиваются («岁运与日相对»)",
                         "rule": "clash", "rule_ru": "《三命通会》: любое столкновение столпов («相对»)",
                         "tian_ke_di_chong": ctrl}
                if ctrl:
                    extra["controller"] = "external" if _controls(ee, en) else "natal"
                add("fan_yin", f"{bz.ganzhi(e)}–{bz.ganzhi(n)}", **extra)
        elif ctrl:
            add("fan_yin", f"{bz.ganzhi(e)}–{bz.ganzhi(n)}", rule="tian_ke_di_chong",
                controller="external" if _controls(ee, en) else "natal",
                controller_ru=("внешний столп подавляет натальный" if _controls(ee, en)
                               else "натальный столп подавляет внешний"))
    return out


def _formations(natal_br: dict[str, int], ext_br: dict[str, int]) -> list[dict]:
    """Тройки (三合, 三会, полные 三刑), которые складываются ТОЛЬКО с участием внешних ветвей."""
    base = set(natal_br.values())
    allb = base | set(ext_br.values())
    out = []
    groups = ([(t, el, "three_harmony", "三合局", "три гармонии") for t, el in bz.THREE_HARMONIES]
              + [(t, el, "directional", "三会方", "сезонный союз") for t, el in bz.DIRECTIONAL]
              + [(t, None, "full_punishment", "三刑", nm) for t, nm in bz.PUNISHMENT_GROUPS])
    for trio, el, kind, cn, ru in groups:
        if set(trio) <= allb and not set(trio) <= base:
            out.append({"type": kind, "cn": cn, "ru": ru, "branches": "".join(bz.BRANCHES[x][0] for x in trio),
                        "element": el,
                        "external": [k for k, v in ext_br.items() if v in trio],
                        "natal": [k for k, v in natal_br.items() if v in trio]})
    return out


def _relations_with_natal(e: int, natal: dict[str, int],
                          fan_yin_rule: str = "tian_ke_di_chong") -> dict[str, list[dict]]:
    return {k: rels for k, v in natal.items() if v is not None and (rels := _pair_relations(e, v, fan_yin_rule))}


def xiao_yun(nominal_age: int, hour_idx: int | None, forward: bool | None, gender: str | None) -> dict:
    """小运 (малая удача, «行年») на номинальный возраст (虚岁) по 《三命通会》 卷二 «论小运».

    * hour_based — «醉醒子以为男女小运皆由时生而行之，逆顺亦以年定。如阳命阳年甲子时生堕地，即行乙丑，二岁丙寅，
      一位一年»: от столпа часа на 1 шаг за год, направление — как у Столпов удачи (forward). «童限未交大运，
      专用此法» — до первого Столпа удачи только этот способ. Так же считает lunar-python (XiaoYun).
    * xing_nian — «古人以男起丙寅顺行，女起壬申逆行»: в 1 суй мужчина — 丙寅 и дальше вперёд, женщина — 壬申 и назад.
    """
    out: dict = {"nominal_age": nominal_age}
    if hour_idx is not None and forward is not None:
        out["hour_based"] = {"index": (hour_idx + (nominal_age if forward else -nominal_age)) % 60,
                             "rule": "醉醒子: от столпа часа, 1 суй = следующий столп; направление как у 大运"}
        out["hour_based"]["ganzhi"] = bz.ganzhi(out["hour_based"]["index"])
    if gender in ("male", "female"):
        idx = (2 + (nominal_age - 1)) % 60 if gender == "male" else (8 - (nominal_age - 1)) % 60
        out["xing_nian"] = {"index": idx, "ganzhi": bz.ganzhi(idx),
                            "rule": "古法: мужчина — 丙寅 в 1 суй, вперёд; женщина — 壬申 в 1 суй, назад"}
    return out


def _ten_gods_of(idx: int, dm: int) -> dict:
    s, b = idx % 10, idx % 12
    return {
        "stem": {"cn": bz.STEMS[s][0], **bz.ten_god(dm, s)},
        "branch_hidden": [{"cn": bz.STEMS[hs][0], "role": role, "weight": w, "ten_god": bz.ten_god(dm, hs)["cn"],
                           "ten_god_ru": bz.ten_god(dm, hs)["ru"]} for hs, role, w in bz.HIDDEN_STEMS[b]],
        "life_stage_dm": bz.life_stage(dm, b),
        "nayin": bz.nayin(idx),
    }


def _short(rels: dict[str, list[dict]]) -> list[str]:
    """Краткая запись отношений: «год: 冲 子午»."""
    return [f"{bz.PILLAR_RU[k]}: {r['cn']} {r['detail']}" for k, lst in rels.items() for r in lst]


def _tai_sui(natal_branch: int, year_branch: int) -> list[dict]:
    """Отношения ветви (обычно ветви года рождения) с ветвью года (太岁)."""
    out = []
    x, y = natal_branch, year_branch
    pb = frozenset({x, y})
    if x == y:
        out.append("zhi")
    if (x - y) % 12 == 6:
        out.append("chong")
    if (pb == bz.PUNISHMENT_PAIR[0] or (x == y and x in bz.SELF_PUNISH)
            or any(x in g and y in g and x != y for g, _ in bz.PUNISHMENT_GROUPS)):
        out.append("xing")
    if pb in bz.HARMS:
        out.append("hai")
    if pb in bz.DESTRUCTIONS:
        out.append("po")
    return [{"type": k, "cn": TAI_SUI_RU[k][0], "ru": TAI_SUI_RU[k][1],
             "branches": bz.BRANCHES[x][0] + bz.BRANCHES[y][0]} for k in out]


def tai_sui_table(year: int) -> dict[str, list[str]]:
    """Какие ветви (животные) «задевают» Тай Суй года year — для сверки с опубликованными списками."""
    yb = bz.year_index(year) % 12
    table: dict[str, list[str]] = {k: [] for k in TAI_SUI_RU}
    for x in range(12):
        for r in _tai_sui(x, yb):
            table[r["type"]].append(bz.BRANCHES[x][0])
    return table


def _zheng_hui(day_idx: int, year_idx: int, luck_idx: int | None, hour_idx: int | None = None) -> list[dict]:
    """«征» и «晦» по 《渊海子平》 «论征太岁»: «日干支冲剋太岁曰征，运支干伤冲太岁亦曰征»;
    «日干支合太岁干支曰晦，岁运合岁干亦然». Дополнения 《三命通会》 (卷二 «论太岁», «总论岁运», поле source):
    «太岁干支冲日干支亦曰征» — ствол года, сталкиваясь (天干相冲), подавляет ствол дня («岁伤日干，有祸必轻»);
    «日干与时干不宜与太岁元天元合，合则名为晦气» — слияние ствола часа со стволом года."""
    out = []
    yz = "渊海子平"
    ds, db, ys, yb = day_idx % 10, day_idx % 12, year_idx % 10, year_idx % 12
    if _controls(_el_index(ds), _el_index(ys)):
        out.append({"type": "zheng", "cn": "征 (日犯岁君)", "detail": f"ствол дня {bz.STEMS[ds][0]} подавляет "
                    f"ствол года {bz.STEMS[ys][0]}", "source": yz})
    if (db - yb) % 12 == 6:
        out.append({"type": "zheng", "cn": "征", "detail": f"ветвь дня {bz.BRANCHES[db][0]} сталкивается с ветвью "
                    f"года {bz.BRANCHES[yb][0]}", "source": yz})
    if frozenset({ds, ys}) in bz.STEM_CLASHES and _controls(_el_index(ys), _el_index(ds)):
        out.append({"type": "zheng", "cn": "征 (岁伤日干)", "detail": f"ствол года {bz.STEMS[ys][0]} сталкивается со "
                    f"стволом дня {bz.STEMS[ds][0]} и подавляет его («岁伤日干，有祸必轻» — легче, чем 日犯岁君)",
                    "source": "三命通会"})
    if frozenset({ds, ys}) in bz.STEM_COMBOS:
        heavy = ds % 2 == 0          # «甲合己灾重，己合甲灾轻»: ствол дня — Ян-партнёр слияния → тяжелее
        out.append({"type": "hui", "cn": "晦", "detail": f"ствол дня {bz.STEMS[ds][0]} сливается со стволом года "
                    f"{bz.STEMS[ys][0]}", "source": yz,
                    "severity_sanming": "heavier" if heavy else "lighter"})
    if frozenset({db, yb}) in bz.SIX_COMBOS:
        out.append({"type": "hui", "cn": "晦", "detail": f"ветвь дня {bz.BRANCHES[db][0]} сливается с ветвью года "
                    f"{bz.BRANCHES[yb][0]}", "source": yz})
    if hour_idx is not None and frozenset({hour_idx % 10, ys}) in bz.STEM_COMBOS:
        out.append({"type": "hui", "cn": "晦", "detail": f"ствол часа {bz.STEMS[hour_idx % 10][0]} сливается со "
                    f"стволом года {bz.STEMS[ys][0]}", "source": "三命通会"})
    if luck_idx is not None:
        ls, lb = luck_idx % 10, luck_idx % 12
        if _controls(_el_index(ls), _el_index(ys)):
            out.append({"type": "zheng", "cn": "征", "detail": f"ствол удачи {bz.STEMS[ls][0]} подавляет ствол года "
                        f"{bz.STEMS[ys][0]}", "source": yz})
        if (lb - yb) % 12 == 6:
            out.append({"type": "zheng", "cn": "征", "detail": f"ветвь удачи {bz.BRANCHES[lb][0]} сталкивается с "
                        f"ветвью года {bz.BRANCHES[yb][0]}", "source": yz})
        if frozenset({ls, ys}) in bz.STEM_COMBOS:
            out.append({"type": "hui", "cn": "晦", "detail": f"ствол удачи {bz.STEMS[ls][0]} сливается со стволом "
                        f"года {bz.STEMS[ys][0]}", "source": yz})
    return out


def _luck_vs_year(luck_idx: int, year_idx: int, fan_yin_rule: str = "tian_ke_di_chong") -> list[dict]:
    """Удача против года по 《滴天髓》 «歲運»: 戰 (подавление стволов), 沖 (столкновение ветвей),
    和 (слияние), 好 (один элемент, разная полярность). Направление — по подавляющему элементу."""
    out = []
    ls, lb, ys, yb = luck_idx % 10, luck_idx % 12, year_idx % 10, year_idx % 12
    if luck_idx == year_idx:
        out.append({"type": "sui_yun_bing_lin", "cn": "岁运併临", "ru": "столп удачи совпадает со столпом года",
                    "detail": bz.ganzhi(year_idx)})
    el_l, el_y = _el_index(ls), _el_index(ys)
    if _controls(el_l, el_y):
        out.append({"type": "zhan", "cn": "戰 (運伐歲)", "ru": "ствол удачи подавляет ствол года",
                    "detail": bz.STEMS[ls][0] + bz.STEMS[ys][0]})
    elif _controls(el_y, el_l):
        out.append({"type": "zhan", "cn": "戰 (歲伐運)", "ru": "ствол года подавляет ствол удачи",
                    "detail": bz.STEMS[ys][0] + bz.STEMS[ls][0]})
    if (lb - yb) % 12 == 6:
        bl, by = _branch_el_index(lb), _branch_el_index(yb)
        cn = "沖 (運沖歲)" if _controls(bl, by) else ("沖 (歲沖運)" if _controls(by, bl) else "沖")
        out.append({"type": "chong", "cn": cn, "ru": "ветви удачи и года сталкиваются",
                    "detail": bz.BRANCHES[lb][0] + bz.BRANCHES[yb][0]})
    if frozenset({ls, ys}) in bz.STEM_COMBOS:
        out.append({"type": "he", "cn": "和", "ru": "стволы удачи и года сливаются",
                    "detail": bz.STEMS[ls][0] + bz.STEMS[ys][0], "element": bz.STEM_COMBOS[frozenset({ls, ys})]})
    if frozenset({lb, yb}) in bz.SIX_COMBOS:
        out.append({"type": "he", "cn": "和", "ru": "ветви удачи и года сливаются",
                    "detail": bz.BRANCHES[lb][0] + bz.BRANCHES[yb][0],
                    "element": bz.SIX_COMBOS[frozenset({lb, yb})]})
    if el_l == el_y and ls != ys:
        out.append({"type": "hao", "cn": "好", "ru": "стволы одного элемента разной полярности",
                    "detail": bz.STEMS[ls][0] + bz.STEMS[ys][0]})
    if lb != yb and lb not in (1, 4, 7, 10) and yb not in (1, 4, 7, 10) and _branch_el_index(lb) == _branch_el_index(yb):
        out.append({"type": "hao", "cn": "好", "ru": "ветви одного элемента разной полярности",
                    "detail": bz.BRANCHES[lb][0] + bz.BRANCHES[yb][0]})
    # прочие отношения ветвей (刑/害/破) — как с натальным столпом
    for r in _pair_relations(year_idx, luck_idx, fan_yin_rule):
        if r["type"] in ("harm", "destruction", "punishment", "self_punishment", "fan_yin", "half_harmony"):
            out.append({"type": r["type"], "cn": r["cn"], "ru": r["ru"], "detail": r["detail"]})
    return out


def bazi_months(year: int) -> list[dict]:
    """12 месячных столпов (流月) года Ба-цзы `year` (с Личуня year до Личуня year+1), моменты цзе в JD(UT)."""
    lc = bz.li_chun_jd(year)
    nxt = bz.li_chun_jd(year + 1)
    starts = [find_sun_longitude(bz.JIE[k][0], lc + 30.44 * k + 10.0, search_back=True) for k in range(12)]
    ys = bz.year_index(year) % 10
    out = []
    for k in range(12):
        stem = (bz.month_first_stem(ys) + k) % 10
        branch = (k + 2) % 12
        out.append({"n": k + 1, "index": bz.ganzhi_index(stem, branch), "branch_index": branch,
                    "jie": {"deg": bz.JIE[k][0], "cn": bz.JIE[k][1], "ru": bz.JIE[k][2]},
                    "start_jd": starts[k], "end_jd": starts[k + 1] if k < 11 else nxt})
    return out


def _bazi_section(b: BirthInput, ref_jd: float, on_date: date, year: int, zone: "ns.Zone",
                  options: dict, warnings: list[str], steps: list[str]) -> dict:
    luck_count = max(10, (year + 1 - b.year) // 10 + 2)
    nat_opts = {k: options[k] for k in ("solar_time", "zi_hour", "nobleman_variant") if k in options}
    natal = bz.calculate(b, luck_count=luck_count, **nat_opts)
    warnings.extend(f"Ба-цзы (натал): {w}" for w in natal["warnings"])
    pidx = {k: (natal["pillars"][k]["index"] if natal["pillars"][k] else None) for k in bz.PILLAR_KEYS}
    natal_br = {k: v % 12 for k, v in pidx.items() if v is not None}
    dm = pidx["day"] % 10
    fy_rule = options.get("fan_yin_rule", "tian_ke_di_chong")
    if fy_rule not in FAN_YIN_RULES:
        raise ValueError("fan_yin_rule: " + " | ".join(repr(x) for x in FAN_YIN_RULES))

    # --- годовой столп и Личунь
    yi = bz.year_index(year)
    lc0, lc1 = bz.li_chun_jd(year), bz.li_chun_jd(year + 1)
    steps.append(f"Ба-цзы. Год {year}: Личунь {_when(lc0, zone)['local']} – {_when(lc1, zone)['local']} "
                 f"({zone.label}); столп года = ({year} − 4) mod 60 = {yi} → {bz.ganzhi(yi)}.")
    annual = {"year": year, **bz.pillar_brief(yi), "li_chun_start": _when(lc0, zone), "li_chun_end": _when(lc1, zone),
              "ten_gods": _ten_gods_of(yi, dm)}
    steps.append(f"Ствол года {bz.STEMS[yi % 10][0]} для Дневного Мастера {bz.STEMS[dm][0]}: "
                 f"{annual['ten_gods']['stem']['cn']} ({annual['ten_gods']['stem']['ru']}).")

    # --- Столп удачи на дату
    luck = natal.get("luck_pillars")
    luck_now = None
    luck_idx = None
    if luck is None:
        warnings.append("Пол не указан: Столпы удачи (大运) и их взаимодействия с годом не рассчитаны.")
    else:
        items = luck["pillars"]
        cur = [p for p in items if p["start_date"][:10] <= on_date.isoformat()]
        if not cur:
            first = items[0]
            luck_now = {"status": "before_first", "first_start": first["start_date"][:10],
                        "note": "Дата раньше начала первого Столпа удачи (童限): по 《三命通会》 «论小运» до 交运 "
                                "действует 小运 — см. поле xiao_yun (hour_based — «童限未交大运，专用此法»)."}
        else:
            p = cur[-1]
            nxt = items[p["n"]] if p["n"] < len(items) else None
            start = date.fromisoformat(p["start_date"][:10])
            elapsed = (on_date - start).days / YEAR_DAYS
            luck_idx = p["index"]
            luck_now = {"status": "active", "n": p["n"], "ganzhi": p["ganzhi"], "ru": p["ru"], "index": p["index"],
                        "start_date": p["start_date"][:10], "end_date": nxt["start_date"][:10] if nxt else None,
                        "years_elapsed": round(elapsed, 2), "years_left": round(10 - elapsed, 2),
                        "half": "stem" if elapsed < 5 else "branch",
                        "half_ru": ("первые 5 лет — ствол (вместе с ветвью)" if elapsed < 5
                                    else "вторые 5 лет — ветвь (ствол уже не учитывается)"),
                        "half_source": "《渊海子平》 «运行十数载，上下五年分»; 《三命通会》 «论大运»: "
                                       "«在干兼用地支之神，在支则弃天干之物»",
                        "ten_gods": _ten_gods_of(p["index"], dm),
                        "relations_with_natal": _relations_with_natal(p["index"], pidx, fy_rule),
                        "direction": luck["direction"]}
            steps.append(f"Столп удачи на {on_date.isoformat()}: №{p['n']} {p['ganzhi']} с {p['start_date'][:10]} "
                         f"(прошло {elapsed:.2f} г.; {luck_now['half_ru']} — «上下五年分», 《渊海子平》).")

    # --- взаимодействия года
    rel_year = _relations_with_natal(yi, pidx, fy_rule)
    ext = {"annual": yi % 12}
    if luck_idx is not None:
        ext["luck"] = luck_idx % 12
    formations = _formations(natal_br, ext)
    tai = {"by_year_branch": _tai_sui(pidx["year"] % 12, yi % 12),
           "by_day_branch": _tai_sui(pidx["day"] % 12, yi % 12),
           "by_day_branch_note": ("по ветви дня классики говорят только о 冲 (= 征, 《渊海子平》/《三命通会》) и "
                                  "о полном совпадении столпа дня со столпом года (日年相并); 值/刑/害/破 太岁 по "
                                  "ветви дня — ⚠ без первоисточника"),
           "zhen_tai_sui": yi == pidx["year"],
           "ri_nian_xiang_bing": yi == pidx["day"],
           "natal_year_branch": bz.BRANCHES[pidx["year"] % 12][0],
           "year_branch": bz.BRANCHES[yi % 12][0]}
    # популярный «знак» по китайскому Новому году может отличаться от ветви года Ба-цзы (Личунь)
    cny = ns.lunar_new_year(b.year)
    if cny is not None:
        lunar_y = b.year if b.date >= cny else b.year - 1
        lb = bz.year_index(lunar_y) % 12
        if lb != pidx["year"] % 12:
            tai["by_lunar_new_year_branch"] = {"branch": bz.BRANCHES[lb][0], "relations": _tai_sui(lb, yi % 12)}
            warnings.append(f"Знак года рождения по китайскому Новому году ({bz.BRANCHES[lb][0]}) отличается от "
                            f"ветви года Ба-цзы по Личуню ({bz.BRANCHES[pidx['year'] % 12][0]}): популярные списки "
                            f"«犯太岁» считают по Новому году — см. tai_sui.by_lunar_new_year_branch.")
    zheng_hui = _zheng_hui(pidx["day"], yi, luck_idx, pidx["hour"])
    luck_year = _luck_vs_year(luck_idx, yi, fy_rule) if luck_idx is not None else []
    if tai["zhen_tai_sui"]:
        steps.append(f"Столп года {bz.ganzhi(yi)} = столп года рождения: 真太岁 (《三命通会》 «论太岁»).")
    if tai["ri_nian_xiang_bing"]:
        steps.append(f"Столп года {bz.ganzhi(yi)} = столп дня: 日年相并 (《三命通会》 «论太岁»).")

    # --- 小运 на год прогноза (номинальный возраст 虚岁 по годам Ба-цзы: год рождения = 1)
    birth_bz_year = b.year if bz.year_index(b.year) == pidx["year"] else b.year - 1
    age = year - birth_bz_year + 1
    small = None
    if age >= 1:
        small = xiao_yun(age, pidx["hour"], (luck["direction"] == "forward") if luck else None,
                         bz._gender(b.gender))
        for key in ("hour_based", "xing_nian"):
            if key in small:
                ix = small[key]["index"]
                small[key].update({**bz.pillar_brief(ix), "ten_gods": _ten_gods_of(ix, dm),
                                   "relations_with_natal": _relations_with_natal(ix, pidx, fy_rule),
                                   "relation_with_annual": [f"{r['cn']} {r['detail']}"
                                                            for r in _pair_relations(ix, yi, fy_rule)]})
        small["birth_bazi_year"] = birth_bz_year
        small["source"] = "《三命通会》 卷二 «论小运»"
        if "hour_based" in small:
            steps.append(f"小运 {year} (虚岁 {age}): от столпа часа {bz.ganzhi(pidx['hour'])} "
                         f"{'вперёд' if luck and luck['direction'] == 'forward' else 'назад'} на {age} → "
                         f"{small['hour_based']['ganzhi']}.")
    if rel_year:
        steps.append("Год ↔ натал: " + "; ".join(_short(rel_year)) + ".")
    if tai["by_year_branch"]:
        steps.append("Тай Суй (по ветви года рождения): " + ", ".join(r["cn"] for r in tai["by_year_branch"]) + ".")

    # --- месяцы
    months = []
    for m in bazi_months(year):
        rels = _relations_with_natal(m["index"], pidx, fy_rule)
        months.append({
            "n": m["n"], **bz.pillar_brief(m["index"]), "jie": m["jie"],
            "start": _when(m["start_jd"], zone), "end": _when(m["end_jd"], zone),
            "stem_ten_god": bz.ten_god(dm, m["index"] % 10)["cn"],
            "branch_main_ten_god": bz.ten_god(dm, bz.HIDDEN_STEMS[m["index"] % 12][0][0])["cn"],
            "relations_with_natal": _short(rels),
            "relation_with_annual": [f"{r['cn']} {r['detail']}" for r in _pair_relations(m["index"], yi, fy_rule)],
        })

    # --- месяц и день на дату
    y_ref = _solar_year_of(ref_jd)
    slot = bz.month_slot(sun_longitude(ref_jd))
    mi = bz.ganzhi_index((bz.month_first_stem(bz.year_index(y_ref) % 10) + slot) % 10, (slot + 2) % 12)
    mstart = find_sun_longitude(bz.JIE[slot][0], ref_jd, search_back=True)
    mend = find_sun_longitude(bz.JIE[(slot + 1) % 12][0], ref_jd, search_back=False)
    _jie_on_date_warning(ref_jd, on_date, zone, warnings)
    ext_m = dict(ext, month=mi % 12)
    month_now = {"solar_year": y_ref, **bz.pillar_brief(mi), "start": _when(mstart, zone), "end": _when(mend, zone),
                 "ten_gods": _ten_gods_of(mi, dm), "relations_with_natal": _relations_with_natal(mi, pidx, fy_rule),
                 "relations_with_annual": _pair_relations(mi, bz.year_index(y_ref), fy_rule),
                 "formations_with_annual_luck": _formations(natal_br, ext_m)}
    di = bz.day_index(on_date)
    day_now = {"date": on_date.isoformat(), **bz.pillar_brief(di), "stem_ten_god": bz.ten_god(dm, di % 10)["cn"],
               "relations_with_natal": _short(_relations_with_natal(di, pidx, fy_rule)),
               "note": "Столп дня — по гражданской дате в поясе прогноза; день меняется в полночь (zi_hour='late')."}
    steps.append(f"Месяц на дату: {bz.ganzhi(mi)} (с {month_now['start']['local']}); день {on_date.isoformat()} — "
                 f"{bz.ganzhi(di)} ((JDN + 49) mod 60).")
    if y_ref != year:
        warnings.append(f"Дата {on_date.isoformat()} лежит вне года Ба-цзы {year} (год даты — {y_ref}): блоки "
                        f"«месяц/день/удача» относятся к дате, «год/месяцы года» — к {year}.")

    return {
        "variant": natal["variant"],
        "natal": {"chart": natal["chart"], "day_master": {k: natal["day_master"][k] for k in ("cn", "ru", "name_ru")},
                  "pillars": {k: (bz.ganzhi(v) if v is not None else None) for k, v in pidx.items()},
                  "luck_direction": luck["direction"] if luck else None,
                  "luck_start": luck["start_date"] if luck else None},
        "annual_pillar": annual,
        "annual_relations_with_natal": rel_year,
        "formations": formations,
        "tai_sui": tai,
        "zheng_hui": zheng_hui,
        "luck_pillar": luck_now,
        "luck_vs_year": luck_year,
        "xiao_yun": small,
        "fan_yin_rule": fy_rule,
        "months": months,
        "month_on_date": month_now,
        "day_on_date": day_now,
    }


# ---------------------------------------------------------------------------
# B. Девятизвёздная Ки: 年盤/月盤, 吉方/凶方
# ---------------------------------------------------------------------------

#: Путь полёта звёзд (飛泊): центр → СЗ → З → СВ → Ю → С → ЮЗ → В → ЮВ (по базовым числам 5→6→…→4).
PALACE_PATH = ["C", "NW", "W", "NE", "S", "N", "SW", "E", "SE"]
PALACE_HOME = {"C": 5, "NW": 6, "W": 7, "NE": 8, "S": 9, "N": 1, "SW": 2, "E": 3, "SE": 4}
PALACE_JA = {"C": "中宮", "NW": "乾宮", "W": "兌宮", "NE": "艮宮", "S": "離宮", "N": "坎宮", "SW": "坤宮",
             "E": "震宮", "SE": "巽宮"}
STAR_EL = {n: ns.STARS[n]["element_en"] for n in range(1, 10)}
#: Фаза 9-летнего цикла по дворцу звезды рождения в 年盤 (回座): 江庭俊之 «九星気学入門» (bccks.jp) — «中宮にある
#: 本命星は、次の年、西北の乾宮に移動します。ここからが一般的に衰運期の始まりです…» (сам автор: «一般論でしかありません»).
KAIZA_PHASE = {
    "C": {"ja": "男性は吉、女性は衰運 (+ 八方塞がり)", "ru": "центр: для мужчин благоприятно, для женщин — спад"},
    "NW": {"ja": "衰運期の始まり", "ru": "начало периода спада"},
    "W": {"ja": "(衰運期)", "ru": "период спада (отдельной характеристики нет)"},
    "NE": {"ja": "衰変・人生の変化の時", "ru": "перелом, время перемен"},
    "S": {"ja": "衰運の中の一休み", "ru": "передышка внутри спада"},
    "N": {"ja": "衰極・一番悪い時期", "ru": "дно цикла, самое трудное время"},
    "SW": {"ja": "盛運期の始まり", "ru": "начало подъёма"},
    "E": {"ja": "盛運期の頂点", "ru": "вершина подъёма"},
    "SE": {"ja": "盛運期の頂点", "ru": "вершина подъёма"},
}
GENERATES = {"wood": "fire", "fire": "earth", "earth": "metal", "metal": "water", "water": "wood"}


def _to9(n: int) -> int:
    r = n % 9
    return 9 if r == 0 else r


def flying_chart(center: int, forward: bool = True) -> dict[str, int]:
    """Карта летящих звёзд: звезда каждого дворца при звезде center в центре.

    forward=True — прямой полёт (順飛, номера растут по пути PALACE_PATH): так строятся 年盤 и 月盤.
    forward=False — обратный полёт (逆飛, номера убывают по тому же пути).
    """
    return {p: _to9(center + i if forward else center - i) for i, p in enumerate(PALACE_PATH)}


def palace_of(chart: dict[str, int], star: int) -> str:
    return next(p for p, s in chart.items() if s == star)


def star_relation(person: int, other: int) -> str | None:
    """Отношение звезды other к звезде person по пяти стихиям: 'same' (та же звезда), 'hiwa' (比和),
    'feeds_you' (other порождает вас), 'you_feed' (вы порождаете other), иначе None (相剋)."""
    if person == other:
        return "same"
    a, o = STAR_EL[person], STAR_EL[other]
    if a == o:
        return "hiwa"
    if GENERATES[o] == a:
        return "feeds_you"
    if GENERATES[a] == o:
        return "you_feed"
    return None


REL_RU = {"hiwa": "比和 (та же стихия)", "feeds_you": "相生 (звезда порождает вашу)",
          "you_feed": "相生 (ваша звезда порождает её)"}


def lucky_stars(person: int) -> dict[int, str]:
    """Звёзды в 相生/比和 с person, без самой звезды (本命殺) и без 5 (五黄殺) — ja.wikipedia «九星»."""
    out = {}
    for s in range(1, 10):
        r = star_relation(person, s)
        if s != person and s != 5 and r is not None:
            out[s] = r
    return out


def _cell(p: str, s: int) -> dict:
    return {"palace": p, "palace_ja": PALACE_JA[p], "direction": p, "direction_ru": DIR_RU[p],
            "direction_ja": DIR_JA[p], "star": s, "star_ja": ns.STARS[s]["ja"]}


def chart_directions(chart: dict[str, int], branch: int, kind: str, honmei: int | None = None,
                     getsumei: int | None = None) -> dict:
    """Японские 凶方/吉方 для одной карты (kind = 'year' | 'month' | 'day').

    Правила (ja.wikipedia «九星気学»): 五黄殺 — дворец звезды 5; 暗剣殺 — противоположный (нет, если 5 в центре);
    歳破/月破/日破 — сторона, противоположная ветви периода; 本命殺 — дворец звезды рождения (нет, если она
    в центре), 本命的殺 — противоположный; 月命殺/月命的殺 — то же для звезды месяца рождения (только 月盤);
    定位対冲 — звезда стоит напротив своего «родного» дворца.
    В 年盤 getsumei влияет только на also_good_for_month_star / max_lucky_honmei_getsumei («最大吉方» (а)).
    """
    ha_name = {"year": "歳破", "month": "月破", "day": "日破"}[kind]
    c = chart["C"]
    five = palace_of(chart, 5)
    goo = None if five == "C" else five
    out: dict = {"center": c, "center_ja": ns.STARS[c]["ja"],
                 "layout": [_cell(p, chart[p]) for p in PALACE_PATH],
                 "go_o_satsu": goo, "anken_satsu": OPPOSITE[goo] if goo else None,
                 # 5 в центре: по ja.wikipedia 五黄殺/暗剣殺 нет; у части авторов (江庭俊之, «九星気学入門») — «全方位が
                 # 五黄殺» (ослабленный). Флаг для агента, в списки unlucky/lucky не влияет.
                 "go_o_in_center": five == "C"}
    opp_b = (branch + 6) % 12
    out["ha"] = {"name": ha_name, "branch": bz.BRANCHES[opp_b][0], "palace": BRANCH_PALACE[opp_b],
                 "period_branch": bz.BRANCHES[branch][0]}
    out["teii_taichu"] = [p for p in PALACE_PATH[1:] if chart[p] != 5 and PALACE_HOME[p] != 5
                          and OPPOSITE[p] == next(q for q, h in PALACE_HOME.items() if h == chart[p])]
    bad: dict[str, list[str]] = {}

    def mark(p: str | None, name: str) -> None:
        if p and p != "C":
            bad.setdefault(p, []).append(name)

    mark(out["go_o_satsu"], "五黄殺")
    mark(out["anken_satsu"], "暗剣殺")
    mark(out["ha"]["palace"], ha_name)
    if honmei is not None:
        hp = palace_of(chart, honmei)
        out["honmei"] = {"star": honmei, "palace": hp, "palace_ja": PALACE_JA[hp], "direction_ru": DIR_RU[hp],
                         "honmei_satsu": None if hp == "C" else hp,
                         "honmei_teki_satsu": None if hp == "C" else OPPOSITE[hp],
                         "in_center": hp == "C"}
        mark(out["honmei"]["honmei_satsu"], "本命殺")
        mark(out["honmei"]["honmei_teki_satsu"], "本命的殺")
    if getsumei is not None and kind == "month":
        gp = palace_of(chart, getsumei)
        out["getsumei"] = {"star": getsumei, "palace": gp, "getsumei_satsu": None if gp == "C" else gp,
                           "getsumei_teki_satsu": None if gp == "C" else OPPOSITE[gp]}
        mark(out["getsumei"]["getsumei_satsu"], "月命殺")
        mark(out["getsumei"]["getsumei_teki_satsu"], "月命的殺")
    out["unlucky"] = [{"direction": p, "direction_ru": DIR_RU[p], "direction_ja": DIR_JA[p], "star": chart[p],
                       "reasons": v} for p, v in sorted(bad.items(), key=lambda kv: PALACE_PATH.index(kv[0]))]
    if honmei is not None:
        good_h = lucky_stars(honmei)
        good_g = lucky_stars(getsumei) if getsumei is not None else {}
        lucky = []
        for p in PALACE_PATH[1:]:
            s = chart[p]
            if s in good_h and p not in bad:
                lucky.append({"direction": p, "direction_ru": DIR_RU[p], "direction_ja": DIR_JA[p], "star": s,
                              "relation": good_h[s], "relation_ru": REL_RU[good_h[s]],
                              "also_good_for_month_star": s in good_g,
                              "teii_taichu": p in out["teii_taichu"]})
        out["lucky"] = lucky
        out["max_lucky_honmei_getsumei"] = [x["direction"] for x in lucky if x["also_good_for_month_star"]]
    return out


#: Ширина секторов направлений (азимут от дома, градусы по часовой от севера; границы [from, to)).
#: 'cn_45' — 8 × 45° (китайская практика: ne.jp/asahi/tokoro «奇門遁甲は各方位45度»);
#: 'ja_30_60' — «東西南北各３０度、東北、東南、西南、西北各６０度» (江庭俊之 «九星気学入門», bccks.jp; 柴山和枝,
#: event.rakuten.co.jp; ne.jp/asahi/tokoro «九星気学は30度、60度»). Стороны: 東北 = 丑寅 и т. д. (по 2 ветви).
DIRECTION_SECTORS: dict[str, dict[str, tuple[float, float]]] = {
    "cn_45": {"N": (337.5, 22.5), "NE": (22.5, 67.5), "E": (67.5, 112.5), "SE": (112.5, 157.5),
              "S": (157.5, 202.5), "SW": (202.5, 247.5), "W": (247.5, 292.5), "NW": (292.5, 337.5)},
    "ja_30_60": {"N": (345.0, 15.0), "NE": (15.0, 75.0), "E": (75.0, 105.0), "SE": (105.0, 165.0),
                 "S": (165.0, 195.0), "SW": (195.0, 255.0), "W": (255.0, 285.0), "NW": (285.0, 345.0)},
}


def direction_of_azimuth(azimuth: float, scheme: str = "ja_30_60") -> str:
    """Сторона света (дворец) для азимута azimuth (0° — север, по часовой) в схеме секторов scheme."""
    if scheme not in DIRECTION_SECTORS:
        raise ValueError("scheme: " + " | ".join(repr(x) for x in DIRECTION_SECTORS))
    a = azimuth % 360.0
    for d, (lo, hi) in DIRECTION_SECTORS[scheme].items():
        if (lo <= a < hi) if lo < hi else (a >= lo or a < hi):
            return d
    raise AssertionError(a)  # pragma: no cover


def ninestar_months(year: int) -> list[dict]:
    """12 месяцев года Ки year: звезда месяца, моменты цзе (JD UT)."""
    ys = ns.year_star(year)
    return [{"n": m["n"], "index": m["index"], "branch_index": m["branch_index"], "jie": m["jie"],
             "start_jd": m["start_jd"], "end_jd": m["end_jd"], "star": ns.month_star(ys, m["n"] - 1)}
            for m in bazi_months(year)]


def _ninestar_section(b: BirthInput, ref_jd: float, on_date: date, year: int, zone: "ns.Zone",
                      options: dict, warnings: list[str], steps: list[str]) -> dict:
    nat_opts = {k: options[k] for k in ("tendency_method",) if k in options}
    natal = ns.calculate(b, day_star_method=None, hour_star_method=None, **nat_opts)
    # предупреждения натала (Личунь/цзе в день рождения без времени и т. п.) важны: от них зависят 本命星/月命星;
    # предупреждения о числе Гуа здесь не нужны
    warnings.extend(f"Ки (натал): {w}" for w in natal["warnings"] if "Гуа" not in w)
    honmei = natal["nine_star_ki"]["principal"]["number"]
    getsumei = natal["nine_star_ki"]["month"]["number"]
    ys = ns.year_star(year)
    ychart = flying_chart(ys)
    # getsumei передаётся, чтобы в 年盤 был посчитан «最大吉方» (а): 月命殺 в 年盤 не ставится (только в 月盤)
    ydir = chart_directions(ychart, bz.year_index(year) % 12, "year", honmei, getsumei)
    hp = ydir["honmei"]["palace"]
    steps.append(f"Ки. Звезда года {year}: 11 − ({year} mod 9) → {ys} {ns.STARS[ys]['ja']}; 年盤 прямым полётом "
                 f"(центр → СЗ → З → СВ → Ю → С → ЮЗ → В → ЮВ). Звезда рождения {honmei} стоит в "
                 f"{PALACE_JA[hp]} ({DIR_RU[hp]}).")
    if hp == "C":
        warnings.append(f"Звезда рождения {honmei} в центре 年盤 {year}: «八方塞がり» (раз в 9 лет; «何をしても思うに"
                        f"成らず», miyajidake.or.jp). 本命殺/本命的殺 в такой год нет; список lucky построен по общему "
                        f"правилу 相生/比和 (⚠ часть авторов в год 八方塞がり 吉方 по 年盤 не даёт).")
    yb = bz.year_index(year) % 12
    cn = {"tai_sui": {"branch": bz.BRANCHES[yb][0], "palace": BRANCH_PALACE[yb]},
          "sui_po": {"branch": bz.BRANCHES[(yb + 6) % 12][0], "palace": BRANCH_PALACE[(yb + 6) % 12]},
          "san_sha": {"palace": SAN_SHA[bz.TRINE_OF[yb]][0], "branches": SAN_SHA[bz.TRINE_OF[yb]][1]},
          "wu_huang": palace_of(ychart, 5), "er_hei": palace_of(ychart, 2)}

    months = []
    for m in ninestar_months(year):
        ch = flying_chart(m["star"])
        d = chart_directions(ch, m["branch_index"], "month", honmei, getsumei)
        year_good = {x["direction"] for x in ydir.get("lucky", [])}
        months.append({
            "n": m["n"], "branch": bz.BRANCHES[m["branch_index"]][0], "jie": m["jie"],
            "start": _when(m["start_jd"], zone), "end": _when(m["end_jd"], zone),
            "center": m["star"], "center_ja": ns.STARS[m["star"]]["ja"],
            "layout_compact": "-".join(str(ch[p]) for p in ("SE", "S", "SW", "E", "C", "W", "NE", "N", "NW")),
            "go_o_satsu": d["go_o_satsu"], "anken_satsu": d["anken_satsu"], "geppa": d["ha"]["palace"],
            "honmei_palace": d["honmei"]["palace"], "getsumei_palace": d["getsumei"]["palace"],
            "lucky": [x["direction"] for x in d["lucky"]],
            "lucky_year_and_month": [x["direction"] for x in d["lucky"] if x["direction"] in year_good],
        })

    # месяц и день на дату
    y_ref = _solar_year_of(ref_jd)
    slot = bz.month_slot(sun_longitude(ref_jd))
    ms = ns.month_star(ns.year_star(y_ref), slot)
    mbranch = (slot + 2) % 12
    mchart = flying_chart(ms)
    mdir = chart_directions(mchart, mbranch, "month", honmei, getsumei)
    ychart_ref = flying_chart(ns.year_star(y_ref))
    ydir_ref = ydir if y_ref == year else chart_directions(ychart_ref, bz.year_index(y_ref) % 12, "year", honmei,
                                                          getsumei)
    _jie_on_date_warning(ref_jd, on_date, zone, warnings)
    y_good = {x["direction"] for x in ydir_ref.get("lucky", [])}
    mdir["lucky_year_and_month"] = [x["direction"] for x in mdir["lucky"] if x["direction"] in y_good]
    steps.append(f"Месяц на дату ({bz.BRANCHES[mbranch][0]}, год Ки {y_ref}): звезда {ms}; 五黄殺 "
                 f"{mdir['go_o_satsu'] or '—'}, 暗剣殺 {mdir['anken_satsu'] or '—'}, 月破 {mdir['ha']['palace']}.")
    az_check = None
    if options.get("azimuth") is not None:
        az = float(options["azimuth"])
        az_check = {"azimuth": az % 360.0,
                    **{k: direction_of_azimuth(az, k) for k in DIRECTION_SECTORS},
                    "note": "азимут от дома на цель, 0° — север; 気学 по ne.jp/asahi/tokoro — по магнитному "
                            "северу (偏差), 奇門 — по истинному; школы расходятся"}
        if az_check["ja_30_60"] != az_check["cn_45"]:
            warnings.append(f"Азимут {az % 360.0:.1f}° попадает в разные стороны при делении 30°/60° "
                            f"({az_check['ja_30_60']}) и 8 × 45° ({az_check['cn_45']}).")
    day_method = options.get("day_star_method", "ja_leap")
    day = None
    if day_method:
        dsr = ns.day_star(on_date, day_method)
        db = bz.day_index(on_date) % 12
        day = {"date": on_date.isoformat(), "star": dsr["number"], "star_ja": ns.STARS[dsr["number"]]["ja"],
               "method": day_method, "dun": dsr["dun"], "day_ganzhi": dsr["day_ganzhi"],
               "nippa": {"branch": bz.BRANCHES[(db + 6) % 12][0], "palace": BRANCH_PALACE[(db + 6) % 12]}}
        if options.get("day_chart", True):
            # 日盤: звезда дня в центре, прямой полёт по тому же пути, что 年盤/月盤, и в Ян-, и в Инь-дунь
            # (skillon.com, ежедневные карты; 江庭俊之 «九星気学入門»: путь 飛泊 один для всех盤). 月命殺 — только в 月盤.
            dchart = flying_chart(dsr["number"])
            dd = chart_directions(dchart, db, "day", honmei)
            day["chart"] = {"flight": "順飛 (прямой) и в 陰遁", **dd,
                            "layout_compact": "-".join(str(dchart[p]) for p in
                                                       ("SE", "S", "SW", "E", "C", "W", "NE", "N", "NW"))}
            steps.append(f"日盤 {on_date.isoformat()}: звезда дня {dsr['number']} в центре (прямой полёт); 五黄殺 "
                         f"{dd['go_o_satsu'] or '—'}, 暗剣殺 {dd['anken_satsu'] or '—'}, 日破 {dd['ha']['palace']}.")

    return {
        "variant": {"year_boundary": "li_chun", "flight": "順飛 (прямой) для 年盤, 月盤 и 日盤",
                    "direction_sectors": "калькулятор называет дворец; ширина секторов — direction_sectors "
                                         "(ja_30_60 — японский 気学, cn_45 — китайская практика)",
                    "day_star_method": day_method, "honmei_from": "ninestar.calculate (граница Личунь)"},
        "natal": {"honmei": honmei, "honmei_ja": ns.STARS[honmei]["ja"], "getsumei": getsumei,
                  "getsumei_ja": ns.STARS[getsumei]["ja"], "notation": natal["nine_star_ki"]["notation"],
                  "lucky_stars_for_honmei": {str(k): v for k, v in lucky_stars(honmei).items()}},
        "year": {"year": year, "star": ys, "star_ja": ns.STARS[ys]["ja"], **ydir,
                 "honmei_palace_meaning": ("八方塞がり (звезда рождения в центре)" if hp == "C"
                                           else f"{PALACE_JA[hp]}: тема дворца — звезда {PALACE_HOME[hp]} "
                                                f"{ns.STARS[PALACE_HOME[hp]]['ja']} (⚠ см. KB 19 §8)"),
                 "honmei_palace_phase": KAIZA_PHASE[hp]},
        "chinese_annual_afflictions": cn,
        "months": months,
        "month_on_date": {"solar_year": y_ref, "branch": bz.BRANCHES[mbranch][0], "star": ms,
                          "star_ja": ns.STARS[ms]["ja"], **mdir},
        "day_on_date": day,
        "direction_sectors": {k: {d: list(v) for d, v in t.items()} for k, t in DIRECTION_SECTORS.items()},
        **({"azimuth_check": az_check} if az_check else {}),
    }


# ---------------------------------------------------------------------------
# C. Джйотиш: даши, гочара, Саде-сати
# ---------------------------------------------------------------------------

#: Гочара от знака Луны, «Пхаладипика» XXVI.2–8 (пер. V. Subrahmanya Sastri, 1950): благоприятный дом → дом ведхи.
GOCHARA_GOOD: dict[str, dict[int, int | None]] = {
    "sun": {3: 9, 6: 12, 10: 4, 11: 5},
    "moon": {1: 5, 3: 9, 6: 12, 7: 2, 10: 4, 11: 8},
    "mars": {3: 12, 6: 9, 11: 5},
    "mercury": {2: 5, 4: 3, 6: 9, 8: 1, 10: 8, 11: 12},
    "jupiter": {2: 12, 5: 4, 7: 3, 9: 10, 11: 8},
    # XXVI.8: «1st, 2nd, 3rd, 4th, 5th, 8th, 9th, 12th and 11th … 8th, 7th, 1st, 10th, 9th, 5th, 11th, 6th and 3rd
    # respectively» → 12-й ↔ 6-й, 11-й ↔ 3-й (не наоборот).
    "venus": {1: 8, 2: 7, 3: 1, 4: 10, 5: 9, 8: 5, 9: 11, 11: 3, 12: 6},
    "saturn": {3: 12, 6: 9, 11: 5},
    # XXVI.2: «Rahu and Ketu are similar to the Sun»; точки ведхи для узлов в тексте не даны.
    "rahu": {3: None, 6: None, 10: None, 11: None},
    "ketu": {3: None, 6: None, 10: None, 11: None},
}
#: Вариант «Прашна-марги» (пер. B. V. Raman, ч. 2, гл. о гочаре, ст. 51): «The Vedhya positions for Rahu and Ketu are
#: 3, 6, and 11 as for Saturn and the Vedha positions are 12, 9, 5» — опция node_gochara='prasna_marga'.
NODE_GOCHARA = {
    "phaladeepika": {3: None, 6: None, 10: None, 11: None},
    "prasna_marga": {3: 12, 6: 9, 11: 5},
}
#: Пары без ведхи: «no Vedha between the father and son» (Солнце–Сатурн, XXVI.3, 5), Луна–Меркурий (XXVI.4, 6).
VEDHA_EXEMPT = {"sun": "saturn", "saturn": "sun", "moon": "mercury", "mercury": "moon"}
#: XXVI.25: в какой части знака транзит «даёт плоды» (градусы внутри знака).
EFFECT_PORTION = {"sun": (0, 10), "mars": (0, 10), "jupiter": (10, 20), "venus": (10, 20),
                  "moon": (20, 30), "saturn": (20, 30), "mercury": (0, 30), "rahu": (0, 30)}
SLOW = {"saturn": swe.SATURN, "jupiter": swe.JUPITER}

#: Аштакаварга (अष्टकवर्ग): благоприятные места (bindu/rekha) в карте планеты, считая от знака каждого из 8
#: «источников» (7 планет и Лагна). «Пхаладипика» XXIII.3–9 (пер. V. Subrahmanya Sastri, 1950).
AV_CONTRIBUTORS = ("sun", "moon", "mars", "mercury", "jupiter", "venus", "saturn", "lagna")
AV_PLANETS = AV_CONTRIBUTORS[:7]
ASHTAKAVARGA_PHALADEEPIKA: dict[str, dict[str, tuple[int, ...]]] = {
    "sun": {"sun": (1, 2, 4, 7, 8, 9, 10, 11), "moon": (3, 6, 10, 11), "mars": (1, 2, 4, 7, 8, 9, 10, 11),
            "mercury": (3, 5, 6, 9, 10, 11, 12), "jupiter": (5, 6, 9, 11), "venus": (6, 7, 12),
            "saturn": (1, 2, 4, 7, 8, 9, 10, 11), "lagna": (3, 4, 6, 10, 11, 12)},
    "moon": {"sun": (3, 6, 7, 8, 10, 11), "moon": (1, 3, 6, 7, 10, 11), "mars": (2, 3, 5, 6, 9, 10, 11),
             "mercury": (1, 3, 4, 5, 7, 8, 10, 11), "jupiter": (1, 2, 4, 7, 8, 10, 11),
             "venus": (3, 4, 5, 7, 9, 10, 11), "saturn": (3, 5, 6, 11), "lagna": (3, 6, 10, 11)},
    "mars": {"sun": (3, 5, 6, 10, 11), "moon": (3, 6, 11), "mars": (1, 2, 4, 7, 8, 10, 11), "mercury": (3, 5, 6, 11),
             "jupiter": (6, 10, 11, 12), "venus": (6, 8, 11, 12), "saturn": (1, 4, 7, 8, 9, 10, 11),
             "lagna": (1, 3, 6, 10, 11)},
    "mercury": {"sun": (5, 6, 9, 11, 12), "moon": (2, 4, 6, 8, 10, 11), "mars": (1, 2, 4, 7, 8, 9, 10, 11),
                "mercury": (1, 3, 5, 6, 9, 10, 11, 12), "jupiter": (6, 8, 11, 12),
                "venus": (1, 2, 3, 4, 5, 8, 9, 11), "saturn": (1, 2, 4, 7, 8, 9, 10, 11),
                "lagna": (1, 2, 4, 6, 8, 10, 11)},
    "jupiter": {"sun": (1, 2, 3, 4, 7, 8, 9, 10, 11), "moon": (2, 5, 7, 9, 11), "mars": (1, 2, 4, 7, 8, 10, 11),
                "mercury": (1, 2, 4, 5, 6, 9, 10, 11), "jupiter": (1, 2, 3, 4, 7, 8, 10, 11),
                "venus": (2, 5, 6, 9, 10, 11), "saturn": (3, 5, 6, 12), "lagna": (1, 2, 4, 5, 6, 7, 9, 10, 11)},
    "venus": {"sun": (8, 11, 12), "moon": (1, 2, 3, 4, 5, 8, 9, 11, 12), "mars": (3, 5, 6, 9, 11, 12),
              "mercury": (3, 5, 6, 9, 11), "jupiter": (5, 8, 9, 10, 11), "venus": (1, 2, 3, 4, 5, 8, 9, 10, 11),
              "saturn": (3, 4, 5, 8, 9, 10, 11), "lagna": (1, 2, 3, 4, 5, 8, 9, 11)},
    "saturn": {"sun": (1, 2, 4, 7, 8, 10, 11), "moon": (3, 6, 11), "mars": (3, 5, 6, 10, 11, 12),
               "mercury": (6, 8, 9, 10, 11, 12), "jupiter": (5, 6, 11, 12), "venus": (6, 11, 12),
               "saturn": (3, 5, 6, 11), "lagna": (1, 3, 4, 6, 10, 11)},
}
#: Вариант «Брихат Парашара Хора Шастры» (пер. R. Santhanam, гл. 66, ст. 46–48 и 56–58): в карте Луны — 9-й от
#: самой Луны есть, 9-го от Марса нет; в карте Венеры от Марса — 3, 4, 6, 9, 11, 12 (так и сноска «Пхаладипики»
#: к XXIII.8: «According to Parasara, the 3rd, 4th, 6th, 9th, 11th and 12th places from Mars»). Итоги те же (49, 52).
ASHTAKAVARGA_BPHS = {**ASHTAKAVARGA_PHALADEEPIKA,
                     "moon": {**ASHTAKAVARGA_PHALADEEPIKA["moon"], "moon": (1, 3, 6, 7, 9, 10, 11),
                              "mars": (2, 3, 5, 6, 10, 11)},
                     "venus": {**ASHTAKAVARGA_PHALADEEPIKA["venus"], "mars": (3, 4, 6, 9, 11, 12)}}
ASHTAKAVARGA = {"phaladeepika": ASHTAKAVARGA_PHALADEEPIKA, "bphs": ASHTAKAVARGA_BPHS}
#: «Пхаладипика» XXIII.11: транзит планеты по знаку с 0…8 точками в её собственной аштакаварге.
AV_TRANSIT_RESULT = {
    0: "loss of life (угроза жизни)", 1: "destruction or loss (разрушение, потеря)", 2: "expenditure (расходы)",
    3: "fear (страх)", 4: "fear (страх; так в переводе 1950 г.)", 5: "accomplishment of the desired object (исполнение "
    "желаемого)", 6: "acquisition of a damsel (обретение спутницы)", 7: "gain of wealth or property (богатство, "
    "имущество)", 8: "gaining a Kingdom or high Government position (власть, высокий пост)",
}


def ashtakavarga(signs: dict[str, int], school: str = "phaladeepika") -> dict:
    """Бхинна-аштакаварга 7 планет и сарва-аштакаварга по знакам (0 = Овен … 11 = Рыбы).

    signs — сидерические знаки (0…11) натальных sun…saturn и 'lagna'. Возвращает {'bav': {planet: [12]},
    'sav': [12], 'totals': {planet: n}}. Без шодханы (трикона/экадхипатья) — как в «Пхаладипике» XXIII.11, 20.
    """
    table = ASHTAKAVARGA[school]
    bav = {}
    for p in AV_PLANETS:
        row = [0] * 12
        for c in AV_CONTRIBUTORS:
            for h in table[p][c]:
                row[(signs[c] + h - 1) % 12] += 1
        bav[p] = row
    sav = [sum(bav[p][i] for p in AV_PLANETS) for i in range(12)]
    return {"bav": bav, "sav": sav, "totals": {p: sum(r) for p, r in bav.items()}, "sav_total": sum(sav)}


def gochara_house(sign: int, ref_sign: int) -> int:
    """Номер дома знака sign от опорного знака ref_sign (1…12, по целым знакам)."""
    return (sign - ref_sign) % 12 + 1


def _sid_lon(jd: float, body: int, ayan: str) -> float:
    return eph.body_position(jd, body, ayan)["lon"]


def _body_lon(name: str, jd: float, ayan: str, node: str) -> float:
    if name in SLOW:
        return _sid_lon(jd, SLOW[name], ayan)
    nl = _sid_lon(jd, swe.MEAN_NODE if node == "mean" else swe.TRUE_NODE, ayan)
    return nl if name == "rahu" else (nl + 180.0) % 360.0


def sign_segments(name: str, jd_from: float, jd_to: float, ayan: str = "lahiri", node: str = "mean",
                  step: float = 1.0) -> list[dict]:
    """Пребывание граха name (saturn/jupiter/rahu/ketu) в сидерических знаках на отрезке [jd_from, jd_to].

    Ингрессии ищутся шагом step суток и бисекцией (точность ~0.01 с). У первого и последнего отрезка
    start/end = None, если граница лежит за пределами окна.
    """
    def sign(jd: float) -> int:
        return int(_body_lon(name, jd, ayan, node) // 30)

    segs = []
    jd = jd_from
    s0 = sign(jd)
    start = None
    while jd < jd_to:
        jd2 = min(jd + step, jd_to)
        s1 = sign(jd2)
        if s1 != s0:
            lo, hi = jd, jd2
            for _ in range(45):
                mid = (lo + hi) / 2
                if sign(mid) == s0:
                    lo = mid
                else:
                    hi = mid
            segs.append({"sign": s0, "start_jd": start, "end_jd": hi})
            start, s0 = hi, sign(hi)
        jd = jd2
    segs.append({"sign": s0, "start_jd": start, "end_jd": None})
    return segs


def _runs(segs: list[dict], houses: set[int], moon_sign: int, merge_gap_days: float = 400.0) -> list[list[dict]]:
    """Группы подряд идущих отрезков в домах houses от Луны; короткие ретро-выходы (< merge_gap_days) не рвут
    период — они попадают в него как «interruptions»."""
    runs: list[list[dict]] = []
    cur: list[dict] = []
    for s in segs:
        if gochara_house(s["sign"], moon_sign) in houses:
            cur.append(s)
        elif cur:
            runs.append(cur)
            cur = []
    if cur:
        runs.append(cur)
    merged: list[list[dict]] = []
    for r in runs:
        if merged and merged[-1][-1]["end_jd"] is not None and r[0]["start_jd"] is not None \
                and r[0]["start_jd"] - merged[-1][-1]["end_jd"] < merge_gap_days:
            merged[-1] = merged[-1] + r
        else:
            merged.append(r)
    return merged


SADE_PHASE = {12: ("rising", "восходящая (12-й от Луны)"), 1: ("peak", "пиковая (над Луной)"),
              2: ("setting", "заходящая (2-й от Луны)")}


def saturn_periods(moon_sign: int, jd_center: float, zone: "ns.Zone", ayan: str = "lahiri",
                   span_years: float = 31.0) -> dict:
    """Саде-сати (12/1/2 от Луны), Аштама-Шани (8) и Ардхаштама/Кантака-Шани (4) в окне ±span_years."""
    a, z = jd_center - span_years * YEAR_DAYS, jd_center + span_years * YEAR_DAYS
    segs = sign_segments("saturn", a, z, ayan)

    def describe(run: list[dict], kind: str) -> dict:
        out = {"start": _when(run[0]["start_jd"], zone) if run[0]["start_jd"] else None,
               "end": _when(run[-1]["end_jd"], zone) if run[-1]["end_jd"] else None,
               "segments": [], "interruptions": []}
        for s in run:
            h = gochara_house(s["sign"], moon_sign)
            seg = {"sign": s["sign"] + 1, "sign_ru": eph.SIGNS_RU[s["sign"]], "house_from_moon": h,
                   "start": _when(s["start_jd"], zone) if s["start_jd"] else None,
                   "end": _when(s["end_jd"], zone) if s["end_jd"] else None}
            if kind == "sade_sati":
                seg["phase"], seg["phase_ru"] = SADE_PHASE[h]
            out["segments"].append(seg)
        for s1, s2 in zip(run, run[1:]):
            if s2["start_jd"] - s1["end_jd"] > 1e-6:
                out["interruptions"].append({"from": _when(s1["end_jd"], zone), "to": _when(s2["start_jd"], zone)})
        return out

    def covers(run: list[dict], jd: float) -> bool:
        """jd внутри одного из отрезков группы (не в ретро-перерыве)."""
        return any((s["start_jd"] if s["start_jd"] is not None else -1e18) <= jd
                   < (s["end_jd"] if s["end_jd"] is not None else 1e18) for s in run)

    res: dict = {}
    # «kantaka_shani» в широком смысле: Сатурн в кендре от Луны (1, 4, 7, 10) — «The 1st, the 10th, the 7th and the
    # 4th houses are known by the terms Kendra, Kantaka and Chatushtaya» («Пхаладипика» I.17); узкий смысл (4-й) —
    # ardhashtama_shani.
    for kind, houses in (("sade_sati", {12, 1, 2}), ("ashtama_shani", {8}), ("ardhashtama_shani", {4}),
                         ("kantaka_shani", {1, 4, 7, 10})):
        raw = _runs(segs, houses, moon_sign)
        bounds = [((r[0]["start_jd"] if r[0]["start_jd"] is not None else -1e18),
                   (r[-1]["end_jd"] if r[-1]["end_jd"] is not None else 1e18)) for r in raw]
        cur_i = next((i for i, (s0, e0) in enumerate(bounds) if s0 <= jd_center < e0), None)
        prev_i = [i for i, (_s, e0) in enumerate(bounds) if e0 <= jd_center]
        next_i = [i for i, (s0, _e) in enumerate(bounds) if s0 > jd_center]
        res[kind] = {"active": cur_i is not None and covers(raw[cur_i], jd_center),
                     "current": describe(raw[cur_i], kind) if cur_i is not None else None,
                     "previous": describe(raw[prev_i[-1]], kind) if prev_i else None,
                     "next": describe(raw[next_i[0]], kind) if next_i else None,
                     "all_in_window": [describe(r, kind) for r in raw]}
    sat_now = next(s for s in segs if (s["start_jd"] if s["start_jd"] is not None else -1e18) <= jd_center
                   < (s["end_jd"] if s["end_jd"] is not None else 1e18))
    h = gochara_house(sat_now["sign"], moon_sign)
    res["saturn_house_from_moon_now"] = h
    res["saturn_sign_now"] = sat_now["sign"] + 1
    if h in SADE_PHASE:
        res["sade_sati_phase_now"] = SADE_PHASE[h][0]
    return res


def _dasha_walk(moon_lon: float, jd_birth: float, dasha_year: str, ayan: str, jd_a: float, jd_b: float,
                jd_ref: float) -> dict:
    """Периоды Вимшоттари (как jyotish.vimshottari): текущие на jd_ref и пересекающие [jd_a, jd_b)."""
    clock = jy.DashaClock(jd_birth, dasha_year, ayan)
    nak = jy.nakshatra_of(moon_lon)
    lord = nak["lord"]
    frac = nak["degrees_in_nakshatra"] / jy.NAK_SPAN
    t = -frac * jy.DASHA_YEARS[lord]
    i0 = jy.DASHA_ORDER.index(lord)
    current: dict = {}
    ads_in_year: list[dict] = []
    pds_in_year: list[dict] = []
    for k in range(27):
        md = jy.DASHA_ORDER[(i0 + k) % 9]
        length = jy.DASHA_YEARS[md]
        m0, m1 = clock.jd(t), clock.jd(t + length)
        hit_ref = m0 <= jd_ref < m1
        hit_year = m0 < jd_b and m1 > jd_a
        if hit_ref:
            current["mahadasha"] = {"lord": md, "lord_ru": jy.GRAHA_RU[md], "start_jd": m0, "end_jd": m1}
        if hit_ref or hit_year:
            for ad, a0, a1 in jy.sub_periods(md, t, length):
                j0, j1 = clock.jd(a0), clock.jd(a1)
                in_ref = j0 <= jd_ref < j1
                in_year = j0 < jd_b and j1 > jd_a
                if in_ref:
                    current["antardasha"] = {"lord": ad, "lord_ru": jy.GRAHA_RU[ad], "start_jd": j0, "end_jd": j1}
                if in_year:
                    ads_in_year.append({"mahadasha": md, "antardasha": ad, "start_jd": j0, "end_jd": j1})
                if in_ref or in_year:
                    for pd, p0, p1 in jy.sub_periods(ad, a0, a1 - a0):
                        q0, q1 = clock.jd(p0), clock.jd(p1)
                        if q0 <= jd_ref < q1:
                            current["pratyantardasha"] = {"lord": pd, "lord_ru": jy.GRAHA_RU[pd],
                                                          "start_jd": q0, "end_jd": q1}
                        if q0 < jd_b and q1 > jd_a:
                            pds_in_year.append({"mahadasha": md, "antardasha": ad, "pratyantardasha": pd,
                                                "start_jd": q0, "end_jd": q1})
        if m0 > jd_b and m0 > jd_ref:
            break
        t += length
    return {"current": current, "antardashas_in_year": ads_in_year, "pratyantardashas_in_year": pds_in_year}


def _jd_fmt(d: dict, zone: "ns.Zone") -> dict:
    out = {k: v for k, v in d.items() if k not in ("start_jd", "end_jd")}
    out["start"] = _when(d["start_jd"], zone)["local"]
    out["end"] = _when(d["end_jd"], zone)["local"]
    return out


def _jyotish_section(b: BirthInput, ref_jd: float, on_date: date, year: int, zone: "ns.Zone",
                     options: dict, warnings: list[str], steps: list[str]) -> dict:
    ayan = options.get("ayanamsa", "lahiri")
    node = options.get("node", "mean")
    if isinstance(node, bool):
        node = "true" if node else "mean"
    dasha_year = options.get("dasha_year", "gregorian")
    vedha_by_nodes = bool(options.get("vedha_by_nodes", False))
    node_gochara = options.get("node_gochara", "phaladeepika")
    if node_gochara not in NODE_GOCHARA:
        raise ValueError("node_gochara: " + " | ".join(repr(x) for x in NODE_GOCHARA))
    viparita = bool(options.get("viparita_vedha", False))
    av_school = options.get("ashtakavarga_school", "phaladeepika")
    if av_school not in ASHTAKAVARGA:
        raise ValueError("ashtakavarga_school: " + " | ".join(repr(x) for x in ASHTAKAVARGA))
    gtable = {**GOCHARA_GOOD, "rahu": NODE_GOCHARA[node_gochara], "ketu": NODE_GOCHARA[node_gochara]}
    natal = jy.calculate(b, ayanamsa=ayan, node=node, dasha_year=dasha_year, dasha_levels=1,
                         on_date=on_date.isoformat())
    warnings.extend(f"Джйотиш (натал): {w}" for w in natal["warnings"])
    moon_lon = natal["grahas"]["moon"]["lon"]
    moon_sign = int(moon_lon // 30)
    lagna_sign = natal["lagna"]["sign"] - 1 if natal["lagna"] else None
    jd_birth = natal["inputs_used"]["jd_ut"]

    # --- даши
    y0 = julian_day_ut(zone.to_utc(datetime(year, 1, 1)))
    y1 = julian_day_ut(zone.to_utc(datetime(year + 1, 1, 1)))
    dw = _dasha_walk(moon_lon, jd_birth, dasha_year, ayan, y0, y1, ref_jd)
    cur = {k: _jd_fmt(v, zone) for k, v in dw["current"].items()}
    dasha = {"year_length": dasha_year, "moon_nakshatra": natal["janma_nakshatra"]["name"],
             "on_date": cur,
             "antardashas_in_year": [_jd_fmt(x, zone) for x in dw["antardashas_in_year"]],
             "pratyantardashas_in_year": [_jd_fmt(x, zone) for x in dw["pratyantardashas_in_year"]],
             "jyotish_module_current": natal["dasha"].get("current"),
             "note": "on_date — на момент прогноза (по умолчанию 12:00 пояса прогноза); "
                     "jyotish_module_current — расчёт модуля 07 на 12:00 UT той же даты."}
    if cur:
        steps.append("Даша на дату: " + " / ".join(f"{v['lord_ru']} ({v['start']} – {v['end']})" for v in cur.values())
                     + ".")

    # --- гочара на момент прогноза
    pos = eph.planet_positions(ref_jd, sidereal=ayan, node=node)
    lons = {g: pos[g]["lon"] for g in ("sun", "moon", "mars", "mercury", "jupiter", "venus", "saturn")}
    lons["rahu"] = pos["north_node"]["lon"]
    lons["ketu"] = (pos["north_node"]["lon"] + 180.0) % 360.0
    signs = {g: int(v // 30) for g, v in lons.items()}
    hm = {g: gochara_house(s, moon_sign) for g, s in signs.items()}
    vedha_sources = [g for g in jy.GRAHAS if g not in ("rahu", "ketu") or vedha_by_nodes]

    def counter(g: str, house: int) -> list[str]:
        """Грахи (кроме g, пары-исключения и пары узлов), стоящие в доме house от Луны."""
        return [o for o in vedha_sources if o != g and o != VEDHA_EXEMPT.get(g)
                and not ({g, o} <= {"rahu", "ketu"}) and hm[o] == house]

    # --- аштакаварга натала (нужна Лагна): «Пхаладипика» XXIII
    av = None
    if options.get("ashtakavarga", True) and lagna_sign is not None:
        nat_signs = {g: int(natal["grahas"][g]["lon"] // 30) for g in AV_PLANETS}
        nat_signs["lagna"] = lagna_sign
        av = ashtakavarga(nat_signs, av_school)
    transits = {}
    for g in jy.GRAHAS:
        good = gtable[g]
        h = hm[g]
        rec = {"lon": round(lons[g], 4), "position": jy.sign_dms(lons[g]), "sign": signs[g] + 1,
               "sign_ru": eph.SIGNS_RU[signs[g]], "house_from_moon": h,
               "house_from_lagna": gochara_house(signs[g], lagna_sign) if lagna_sign is not None else None,
               "favorable_house": h in good,
               "retrograde": bool(pos["north_node"]["retro"] if g in ("rahu", "ketu") else pos[g]["retro"])}
        if h in good and good[h] is not None:
            v = good[h]
            blockers = counter(g, v)
            rec["vedha_house"] = v
            rec["vedha_by"] = blockers
            rec["result"] = "favorable_obstructed" if blockers else "favorable"
        elif h in good:
            rec["vedha_house"] = None
            rec["result"] = "favorable"
        else:
            rec["result"] = "unfavorable"
            # випарита-ведха («Прашна-марга», ст. 35, 43, 53): граха в неблагоприятном доме h, который служит домом
            # ведхи для её благоприятного дома f; граха в f «встречно» снимает зло
            f = next((k for k, v in good.items() if v == h), None)
            if f is not None:
                rec["viparita_vedha_house"] = f
                rec["viparita_vedha_by"] = counter(g, f)
                if viparita and rec["viparita_vedha_by"]:
                    rec["result"] = "unfavorable_cancelled"
        if av is not None:
            sav = av["sav"][signs[g]]
            rec["ashtakavarga"] = {"sav_bindus": sav,
                                   "sav_verdict": "good" if sav > 28 else ("bad" if sav < 28 else "neutral")}
            if g in AV_PLANETS:
                bb = av["bav"][g][signs[g]]
                rec["ashtakavarga"].update({"bav_bindus": bb, "bav_result": AV_TRANSIT_RESULT[bb]})
        portion = EFFECT_PORTION.get(g)
        if portion:
            deg = lons[g] % 30
            rec["in_effective_portion"] = portion[0] <= deg < portion[1]
        transits[g] = rec
    steps.append(f"Гочара от Луны ({eph.SIGNS_RU[moon_sign]}): " + "; ".join(
        f"{jy.GRAHA_RU[g]} {eph.SIGNS_RU[signs[g]]} — {hm[g]}-й ({transits[g]['result']})" for g in jy.GRAHAS) + ".")

    # --- медленные планеты за гражданский год
    year_transits = {}
    for g in ("saturn", "jupiter", "rahu", "ketu"):
        segs = sign_segments(g if g in SLOW else "rahu", y0 - 400, y1 + 1, ayan, node, 1.0 if g in SLOW else 0.5)
        if g == "ketu":
            segs = [dict(s, sign=(s["sign"] + 6) % 12) for s in segs]
        lst = []
        for s in segs:
            s0 = s["start_jd"] if s["start_jd"] is not None else -1e18
            e0 = s["end_jd"] if s["end_jd"] is not None else 1e18
            if s0 < y1 and e0 > y0:
                h = gochara_house(s["sign"], moon_sign)
                lst.append({"sign": s["sign"] + 1, "sign_ru": eph.SIGNS_RU[s["sign"]],
                            "start": _when(s["start_jd"], zone) if s["start_jd"] else None,
                            "end": _when(s["end_jd"], zone) if s["end_jd"] else None,
                            "house_from_moon": h, "favorable_house": h in gtable[g],
                            "house_from_lagna": gochara_house(s["sign"], lagna_sign) if lagna_sign is not None
                            else None})
                if av is not None:
                    lst[-1]["sav_bindus"] = av["sav"][s["sign"]]
                    if g in AV_PLANETS:
                        lst[-1]["bav_bindus"] = av["bav"][g][s["sign"]]
        year_transits[g] = lst

    sat = saturn_periods(moon_sign, ref_jd, zone, ayan)
    ss = sat["sade_sati"]
    if ss["active"]:
        steps.append(f"Саде-сати активна: Сатурн в {sat['saturn_house_from_moon_now']}-м от Луны "
                     f"({sat.get('sade_sati_phase_now')}); период {ss['current']['start']['local']} – "
                     f"{ss['current']['end']['local'] if ss['current']['end'] else '…'}.")
    else:
        steps.append(f"Саде-сати не активна; Сатурн в {sat['saturn_house_from_moon_now']}-м от Луны; следующая — с "
                     f"{ss['next']['start']['local'] if ss['next'] else '—'}.")
    if not b.has_time:
        warnings.append("Время рождения неизвестно: знак Луны мог смениться в течение суток — проверьте "
                        "moon_range_for_day модуля 07 (от знака Луны зависят гочара и Саде-сати).")
    if av is not None:
        steps.append("Аштакаварга (" + av_school + "): транзит по точкам своей карты — " + "; ".join(
            f"{jy.GRAHA_RU[g]} {transits[g]['ashtakavarga']['bav_bindus']}" for g in AV_PLANETS)
            + f"; сумма знаков 337 = {av['sav_total']}.")
    elif options.get("ashtakavarga", True):
        warnings.append("Аштакаварга не рассчитана: нужна Лагна (время и место рождения).")

    return {
        "variant": natal["variant"],
        "natal": {"moon_sign": moon_sign + 1, "moon_sign_ru": eph.SIGNS_RU[moon_sign],
                  "moon_lon": round(moon_lon, 4), "janma_nakshatra": natal["janma_nakshatra"]["name"],
                  "lagna_sign": lagna_sign + 1 if lagna_sign is not None else None,
                  "lagna_sign_ru": eph.SIGNS_RU[lagna_sign] if lagna_sign is not None else None},
        "dasha": dasha,
        "transits_on_date": transits,
        "transit_moment": _when(ref_jd, zone),
        "slow_transits_in_year": year_transits,
        "saturn": sat,
        "ashtakavarga": ({"school": av_school,
                          "source": ("«Пхаладипика» XXIII.3–9, 11, 20" if av_school == "phaladeepika"
                                     else "БПХШ гл. 66 (пер. R. Santhanam); правила транзита — «Пхаладипика» XXIII"),
                          "bav": {p: {eph.SIGNS_RU[i]: n for i, n in enumerate(row)} for p, row in av["bav"].items()},
                          "sav": {eph.SIGNS_RU[i]: n for i, n in enumerate(av["sav"])},
                          "totals": av["totals"], "sav_total": av["sav_total"],
                          "note": "точки (bindu) в знаках натальной аштакаварги без шодханы; транзит граха по знаку "
                                  "с 0…8 точками в её карте — XXIII.11; знак с суммой > 28 — благоприятен для "
                                  "транзитов (XXIII.20); у Раху/Кету своей аштакаварги нет"}
                         if av is not None else None),
        "variant_options": {"node_gochara": node_gochara, "vedha_by_nodes": vedha_by_nodes,
                            "viparita_vedha": viparita, "ashtakavarga_school": av_school},
        "year_window": {"from": _when(y0, zone)["local"], "to": _when(y1, zone)["local"],
                        "note": "гражданский год в поясе прогноза"},
    }


# ---------------------------------------------------------------------------
# Точка входа
# ---------------------------------------------------------------------------

SECTIONS = ("bazi", "ninestar", "jyotish")


def calculate(b: BirthInput, **options) -> dict:
    """Восточный прогноз на дату/год.

    options:
      on_date: 'YYYY-MM-DD' (или date) — дата прогноза; по умолчанию сегодня в поясе прогноза;
      on_time: 'HH:MM' — момент внутри даты (по умолчанию '12:00'): от него зависят месяц у цзе, гочара, даша;
      year: год прогноза (год Ба-цзы/Ки с Личуня; для Джйотиш — гражданский год); по умолчанию — год даты;
            если задан только year (без on_date) и сегодня вне этого года, дата = Личунь + 1 ч;
      tz: пояс прогноза (IANA или 'UTC+03:00'); по умолчанию пояс места рождения;
      sections: список блоков из ('bazi', 'ninestar', 'jyotish');
      Ба-цзы: solar_time, zi_hour, nobleman_variant (передаются в bazi.calculate);
      Ки: day_star_method (как в ninestar; None — не считать звезду дня), tendency_method;
      Джйотиш: ayanamsa ('lahiri'), node ('mean'), dasha_year ('gregorian'), vedha_by_nodes (False).
    """
    warnings: list[str] = []
    steps: list[str] = []
    zone, tz_label, zw = _forecast_zone(b, options.get("tz"))
    warnings.extend(zw)

    on_time = str(options.get("on_time", "12:00"))
    hh, mm = (int(x) for x in on_time.split(":")[:2])
    year_opt = options.get("year")
    od = options.get("on_date")
    if od is not None:
        on_date = od if isinstance(od, date) else date.fromisoformat(str(od))
        ref_jd = julian_day_ut(zone.to_utc(datetime(on_date.year, on_date.month, on_date.day, hh, mm)))
    else:
        today = zone.to_local(datetime.now(UTC)).date()
        on_date = today
        ref_jd = julian_day_ut(zone.to_utc(datetime(today.year, today.month, today.day, hh, mm)))
        if year_opt is not None and _solar_year_of(ref_jd) != int(year_opt):
            ref_jd = bz.li_chun_jd(int(year_opt)) + 1.0 / 24.0
            loc = zone.to_local(jd_to_utc(ref_jd))
            on_date = loc.date()
            on_time = loc.strftime("%H:%M")
            warnings.append(f"Задан только year={year_opt}: блоки «на дату» посчитаны на начало года "
                            f"(Личунь + 1 ч = {_iso_min(loc)}).")
        else:
            warnings.append(f"Дата прогноза не задана — взята сегодняшняя ({on_date.isoformat()}).")
    year = int(year_opt) if year_opt is not None else _solar_year_of(ref_jd)
    steps.append(f"Момент прогноза: {on_date.isoformat()} {on_time} ({zone.label}) = "
                 f"{_when(ref_jd, zone)['utc']} UT; год прогноза {year}.")

    sections = options.get("sections", SECTIONS)
    if isinstance(sections, str):
        sections = [s.strip() for s in sections.split(",") if s.strip()]
    out: dict = {"method": "forecast_eastern"}
    builders = {"bazi": ("bazi_year", _bazi_section), "ninestar": ("ninestar_year", _ninestar_section),
                "jyotish": ("jyotish", _jyotish_section)}
    for key in SECTIONS:
        name, fn = builders[key]
        if key not in sections:
            out[name] = None
            continue
        try:
            out[name] = fn(b, ref_jd, on_date, year, zone, options, warnings, steps)
        except ValueError as exc:
            out[name] = None
            warnings.append(f"Блок {name} не рассчитан: {exc}")

    variant = {
        "bazi": "流年 по Личуню, 流月 по 12 цзе, Столп удачи — из модуля 01; взаимодействия по таблицам 01 §4.10",
        "ninestar": "年盤/月盤 прямым полётом, японские 凶方/吉方 (ja.wikipedia), китайские 太岁/岁破/三煞",
        "jyotish": "Вимшоттари (модуль 07), гочара от Луны по «Пхаладипике» XXVI, Саде-сати по ингрессиям Сатурна",
    }
    return {
        **out,
        "variant": variant,
        "inputs_used": {
            "birth_date": b.date.isoformat(),
            "birth_time": f"{b.hour:02d}:{(b.minute or 0):02d}" if b.has_time else None,
            "birth_tz": b.tz, "lat": b.lat, "lon": b.lon, "gender": b.gender,
            "on_date": on_date.isoformat(), "on_time": on_time, "forecast_tz": tz_label,
            "ref_utc": _when(ref_jd, zone)["utc"], "year": year, "sections": list(sections),
        },
        "warnings": warnings,
        "steps": steps,
    }


if __name__ == "__main__":  # pragma: no cover
    import json

    r = calculate(BirthInput(1990, 5, 15, 14, 30, place="Москва", gender="female"), on_date="2026-10-14")
    print(json.dumps(r, ensure_ascii=False, indent=1)[:6000])
