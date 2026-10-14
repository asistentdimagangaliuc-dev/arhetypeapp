"""Да Лю Жэнь (大六壬): «урок» (课盘) на заданный момент — рождение (命课) или консультацию.

Калькулятор написан с нуля по 《六壬大全》 (明, 郭载騋 校; Викитека «六壬大全») и
《大六壬指南》 (清, 陈公献). Пакет kinliuren (PyPI) используется ТОЛЬКО в тестах/черновиках
для сверки, рантайм-зависимостью не является.

Порядок расчёта (подробно — knowledge-base/17-da-liu-ren.md):
1. Момент → UT (common.time.normalize). Месячный генерал (月将) — по истинной долготе Солнца:
   смена на 中气 (雨水 330° → 亥, 春分 0° → 戌, …, 大寒 300° → 子).
2. Время карты (solar_time='true' по умолчанию, как в Ба-цзы) → ветвь часа (占时) и столп дня
   (zi_hour='late': 23:00–24:00 не меняет день — как в модуле 01).
3. Небесная пластина (天盘): 月将 ставится на ветвь часа земной пластины (月将加时), дальше по порядку.
4. Четыре урока (四课) от «дворца пребывания» ствола дня (寄宫) и ветви дня.
5. Три передачи (三传) по девяти методам (九宗门): 贼克 → 比用 → 涉害 → 遥克 → 昂星 → 别责 → 八专,
   伏吟 и 返吟 — особые пластины.
6. Двенадцать Небесных генералов (天将) от Благородного (贵人): дневной/ночной по стволу дня,
   направление — по земной ветви под Благородным (亥…辰 — по ходу, 巳…戌 — против).
7. Скрытые стволы (遁干), «шесть родственников» (六亲), пустота (空亡).

Варианты школ (options): noble_table, day_night, shehai, biezhe_yin, fuyin_zimao,
solar_time, zi_hour, on_datetime.
"""
from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timedelta, timezone
from math import asin, cos, degrees, radians, sin
from zoneinfo import ZoneInfo

import swisseph as swe

from calculators.bazi import BRANCHES, day_index, ganzhi, ganzhi_index, hour_branch, zi_first_stem
from calculators.common.ephemeris import find_sun_longitude, sun_longitude
from calculators.common.time import (BirthInput, fmt_offset, fmt_offset_hms, jd_to_utc, local_mean_time, normalize,
                                     true_solar_time)

# ---------------------------------------------------------------------------
# Справочники
# ---------------------------------------------------------------------------

# 0 Дерево, 1 Огонь, 2 Земля, 3 Металл, 4 Вода
EL = ["wood", "fire", "earth", "metal", "water"]
EL_RU = {"wood": "Дерево", "fire": "Огонь", "earth": "Земля", "metal": "Металл", "water": "Вода"}
EL_CN = {"wood": "木", "fire": "火", "earth": "土", "metal": "金", "water": "水"}
STEM_EL = [0, 0, 1, 1, 2, 2, 3, 3, 4, 4]
BRANCH_EL = [4, 2, 0, 0, 2, 1, 1, 2, 3, 3, 2, 4]

S = "甲乙丙丁戊己庚辛壬癸"
Z = "子丑寅卯辰巳午未申酉戌亥"

# 十干寄宫: «甲课寅兮乙课辰，丙戊课巳不须论。丁己课未庚申上，辛戌壬亥是其真。癸课原来丑宫坐»
# (《六壬大全》 卷一 «入手法»). Индекс ствола → индекс ветви.
JI_GONG = {0: 2, 1: 4, 2: 5, 3: 7, 4: 5, 5: 7, 6: 8, 7: 10, 8: 11, 9: 1}
# какие стволы «живут» в каждом дворце земной пластины (для подсчёта 涉害)
LODGED: dict[int, list[int]] = {b: [s for s, g in JI_GONG.items() if g == b] for b in range(12)}

# 月将: (ветвь, имя, пиньинь, рус.), 中气 (долгота Солнца) → ветвь генерала
GENERAL_NAMES = {
    0: ("神后", "shénhòu", "Шэньхоу (Божественная императрица)"),
    1: ("大吉", "dàjí", "Дацзи (Великое счастье)"),
    2: ("功曹", "gōngcáo", "Гунцао (Счётный чиновник)"),
    3: ("太冲", "tàichōng", "Тайчун (Великий напор)"),
    4: ("天罡", "tiāngāng", "Тяньган (Небесный ковш)"),
    5: ("太乙", "tàiyǐ", "Тайи (Великое единое)"),
    6: ("胜光", "shèngguāng", "Шэнгуан (Победный свет)"),
    7: ("小吉", "xiǎojí", "Сяоцзи (Малое счастье)"),
    8: ("传送", "chuánsòng", "Чуаньсун (Передающий)"),
    9: ("从魁", "cóngkuí", "Цункуй (Следующий за Куй)"),
    10: ("河魁", "hékuí", "Хэкуй (Речной Куй)"),
    11: ("登明", "dēngmíng", "Дэнмин (Восходящий свет)"),
}
# (долгота 中气, иероглифы, русское чтение, ветвь генерала)
ZHONGQI = [
    (330, "雨水", "Юйшуй", 11), (0, "春分", "Чуньфэнь", 10), (30, "谷雨", "Гуюй", 9),
    (60, "小满", "Сяомань", 8), (90, "夏至", "Сячжи", 7), (120, "大暑", "Дашу", 6),
    (150, "处暑", "Чушу", 5), (180, "秋分", "Цюфэнь", 4), (210, "霜降", "Шуанцзян", 3),
    (240, "小雪", "Сяосюэ", 2), (270, "冬至", "Дунчжи", 1), (300, "大寒", "Дахань", 0),
]

# 十二天将 в порядке раскладки от Благородного; (иероглиф, кратко, пиньинь, рус., элемент, благо/зло)
TIAN_JIANG = [
    ("贵人", "贵", "guìrén", "Благородный (Гуйжэнь)", "earth", "吉"),
    ("腾蛇", "蛇", "téngshé", "Летучий змей (Тэншэ)", "fire", "凶"),
    ("朱雀", "雀", "zhūquè", "Красная птица (Чжуцюэ)", "fire", "凶"),
    ("六合", "合", "liùhé", "Шесть согласий (Люхэ)", "wood", "吉"),
    ("勾陈", "勾", "gōuchén", "Крюк-строй (Гоучэнь)", "earth", "凶"),
    ("青龙", "龙", "qīnglóng", "Зелёный дракон (Цинлун)", "wood", "吉"),
    ("天空", "空", "tiānkōng", "Небесная пустота (Тянькун)", "earth", "凶"),
    ("白虎", "虎", "báihǔ", "Белый тигр (Байху)", "metal", "凶"),
    ("太常", "常", "tàicháng", "Великое постоянство (Тайчан)", "earth", "吉"),
    ("玄武", "玄", "xuánwǔ", "Тёмный воин (Сюаньу)", "water", "凶"),
    ("太阴", "阴", "tàiyīn", "Великая тьма (Тайинь)", "metal", "吉"),
    ("天后", "后", "tiānhòu", "Небесная императрица (Тяньхоу)", "water", "吉"),
]

# Благородный (天乙贵人) по стволу дня: (дневной 昼, ночной 夜).
# 'daquan' (по умолчанию) — «甲戊庚牛羊，乙己鼠猴乡，丙丁猪鸡位，壬癸蛇兔藏，六辛逢马虎»
#   (《六壬大全》 卷四; первым назван дневной). Подтверждено статьями 卷十二 «旬内空亡» и примерами 卷十.
# 'xieji' — 《协纪辨方书》 卷七 / 《星历考原》: 阳贵 «起于先天之坤» (от 子 по ходу), 阴贵 от 申 против
#   хода; 阳贵 = дневной (так считает 考原: «当以起未而顺者为阳，起丑而逆者为阴»).
# 'cao' — таблица 曹震圭 в изложении 《协纪辨方书》 卷七: 阳贵 «以甲加丑逆行», 阴贵 «以甲加未顺行».
NOBLE_TABLES: dict[str, dict[int, tuple[int, int]]] = {
    "daquan": {0: (1, 7), 4: (1, 7), 6: (1, 7), 1: (0, 8), 5: (0, 8), 2: (11, 9), 3: (11, 9),
               8: (5, 3), 9: (5, 3), 7: (6, 2)},
    "xieji": {0: (7, 1), 1: (8, 0), 2: (9, 11), 3: (11, 9), 4: (1, 7), 5: (0, 8), 6: (1, 7),
              7: (2, 6), 8: (3, 5), 9: (5, 3)},
    "cao": {0: (1, 7), 1: (0, 8), 2: (11, 9), 3: (9, 11), 4: (1, 7), 5: (8, 0), 6: (7, 1),
            7: (6, 2), 8: (5, 3), 9: (3, 5)},
}

# 三刑: что «наказывает» ветвь (для 伏吟). 辰午酉亥 — самонаказание (自刑).
XING = {0: 3, 3: 0, 2: 5, 5: 8, 8: 2, 1: 10, 10: 7, 7: 1, 4: 4, 6: 6, 9: 9, 11: 11}
SELF_XING = {4, 6, 9, 11}
MENG, ZHONG, JI = {2, 5, 8, 11}, {0, 3, 6, 9}, {1, 4, 7, 10}

LIUQIN = {0: ("兄弟", "Братья"), 1: ("子孙", "Дети-внуки"), 2: ("妻财", "Жена-богатство"),
          3: ("官鬼", "Чиновник-демон"), 4: ("父母", "Родители")}

METHODS = {
    "zeike": ("贼克法", "Метод «грабежа и подавления»"),
    "biyong": ("比用法", "Метод «сходства» (知一)"),
    "shehai": ("涉害法", "Метод «переправы через вред»"),
    "yaoke": ("遥克法", "Метод «дальнего подавления»"),
    "maoxing": ("昴星法", "Метод «звезды Мао» (昂星)"),
    "biezhe": ("别责法", "Метод «иного взыскания»"),
    "bazhuan": ("八专法", "Метод «восьми сосредоточений»"),
    "fuyin": ("伏吟法", "Метод «затаённого стона»"),
    "fanyin": ("返吟法", "Метод «обратного стона»"),
}


def controls(a: int, b: int) -> bool:
    """Элемент a подавляет (克) элемент b: Дерево→Земля→Вода→Огонь→Металл→Дерево."""
    return (b - a) % 5 == 2


def generates(a: int, b: int) -> bool:
    """Элемент a порождает элемент b."""
    return (b - a) % 5 == 1


def b_yang(b: int) -> bool:
    return b % 2 == 0


def zname(b: int) -> str:
    return Z[b % 12]


# ---------------------------------------------------------------------------
# Пластины, уроки, передачи (чистые функции без дат — их удобно тестировать)
# ---------------------------------------------------------------------------


def monthly_general(sun_lon: float) -> int:
    """Ветвь месячного генерала по долготе Солнца (смена на 中气): 330°→亥, 0°→戌, … 300°→子."""
    k = int(((sun_lon - 330.0) % 360.0) // 30.0)
    return (11 - k) % 12


def heaven_plate(general: int, hour: int) -> list[int]:
    """天盘: plate[e] — небесная ветвь над земной ветвью e (月将加时)."""
    return [(e + general - hour) % 12 for e in range(12)]


def earth_under(plate: list[int], heaven: int) -> int:
    """Земная ветвь, над которой стоит небесная ветвь heaven."""
    return plate.index(heaven)


def relation(upper_el: int, lower_el: int) -> str:
    """Отношение урока: 'zei' (下贼上 — низ подавляет верх), 'ke' (上克下), 'sheng_up' (низ порождает верх),
    'sheng_down' (верх порождает низ), 'bi' (один элемент)."""
    if controls(lower_el, upper_el):
        return "zei"
    if controls(upper_el, lower_el):
        return "ke"
    if generates(lower_el, upper_el):
        return "sheng_up"
    if generates(upper_el, lower_el):
        return "sheng_down"
    return "bi"


REL_CN = {"zei": "下贼上", "ke": "上克下", "sheng_up": "下生上", "sheng_down": "上生下", "bi": "比和"}
REL_RU = {"zei": "низ подавляет верх («грабёж», 贼)", "ke": "верх подавляет низ (克)",
          "sheng_up": "низ порождает верх", "sheng_down": "верх порождает низ", "bi": "один элемент"}


def four_lessons(ds: int, db: int, plate: list[int]) -> list[dict]:
    """Четыре урока: 1 — верх над 寄宫 ствола дня; 2 — над верхом 1-го; 3 — над ветвью дня; 4 — над верхом 3-го.

    lower_pos — земная ветвь, на которой стоит верх урока; lower_el — элемент низа
    (у 1-го урока низ — сам ствол дня, у остальных — ветвь).
    """
    jg = JI_GONG[ds]
    u1 = plate[jg]
    u2 = plate[u1]
    u3 = plate[db]
    u4 = plate[u3]
    raw = [
        (1, u1, jg, STEM_EL[ds], S[ds]),
        (2, u2, u1, BRANCH_EL[u1], Z[u1]),
        (3, u3, db, BRANCH_EL[db], Z[db]),
        (4, u4, u3, BRANCH_EL[u3], Z[u3]),
    ]
    out = []
    for n, u, pos, lel, lname in raw:
        r = relation(BRANCH_EL[u], lel)
        out.append({"n": n, "upper": u, "lower_pos": pos, "lower_el": lel, "lower": lname,
                    "rel": r, "text": f"{Z[u]}/{lname}"})
    return out


def distinct_lessons(lessons: list[dict]) -> int:
    """Число различных уроков: совпадают, если одинаковы верх и земная позиция низа («首尾相同»)."""
    return len({(l["upper"], l["lower_pos"]) for l in lessons})


def _unique_uppers(lessons: list[dict]) -> list[dict]:
    seen: set[int] = set()
    out = []
    for l in lessons:
        if l["upper"] not in seen:
            seen.add(l["upper"])
            out.append(l)
    return out


def shehai_depth(upper: int, lower_pos: int, kind: str) -> tuple[int, list[str]]:
    """Глубина 涉害 по 《六壬大全》: идти по земной пластине по ходу от позиции (не считая её)
    до «родного дома» ветви (не считая его) и считать ветви и «живущие» там стволы, которые
    подавляют кандидата (kind='zei') или которых кандидат подавляет (kind='ke')."""
    ue = BRANCH_EL[upper]
    n = 0
    hits: list[str] = []
    p = (lower_pos + 1) % 12
    while p != upper:
        items = [(Z[p], BRANCH_EL[p])] + [(S[s], STEM_EL[s]) for s in LODGED[p]]
        for name, el in items:
            if (kind == "zei" and controls(el, ue)) or (kind == "ke" and controls(ue, el)):
                n += 1
                hits.append(name)
        p = (p + 1) % 12
    return n, hits


def _zhuixia(cands: list[dict], ds: int) -> dict:
    """缀瑕 (复等): Ян-день — первый кандидат среди уроков 1,2,3,4 (干上先见),
    Инь-день — среди уроков 3,4,1,2 (支上先见)."""
    order = [1, 2, 3, 4] if ds % 2 == 0 else [3, 4, 1, 2]
    for n in order:
        for c in cands:
            if c["n"] == n:
                return c
    return cands[0]


def _meng_zhong_ji(cands: list[dict], ds: int, log: list[str]) -> tuple[dict, str]:
    """孟→仲→季 по земной позиции кандидата; при равенстве — 缀瑕."""
    for group, name, label in ((MENG, "孟 (寅申巳亥)", "见机"), (ZHONG, "仲 (子午卯酉)", "察微"),
                               (JI, "季 (辰戌丑未)", "察微")):
        g = [c for c in cands if c["lower_pos"] in group]
        if len(g) == 1:
            log.append(f"На {name} стоит один кандидат {Z[g[0]['upper']]} (над {Z[g[0]['lower_pos']]}) → {label}.")
            return g[0], label
        if len(g) > 1:
            c = _zhuixia(g, ds)
            log.append(f"На {name} стоят несколько кандидатов ({', '.join(Z[x['upper']] for x in g)}) → "
                       f"缀瑕 (复等): {'Ян-день — верх, первым встречающийся в уроках 1–4' if ds % 2 == 0 else 'Инь-день — верх, первым встречающийся в уроках 3,4,1,2'} → {Z[c['upper']]}.")
            return c, "缀瑕"
    raise AssertionError("кандидаты без позиции")


def _shehai(cands: list[dict], ds: int, kind: str, variant: str, log: list[str]) -> tuple[dict, str]:
    """Выбор по 涉害 среди нескольких кандидатов (все одного рода: 'zei' или 'ke')."""
    if variant == "mengzhongji":
        log.append("涉害 по 《大六壬指南》: «只以孟仲季为准，不以涉害深浅为义».")
        return _meng_zhong_ji(cands, ds, log)
    depths = []
    for c in cands:
        d, hits = shehai_depth(c["upper"], c["lower_pos"], kind)
        depths.append(d)
        log.append(f"涉害: {Z[c['upper']]} над {Z[c['lower_pos']]} → до дома {Z[c['upper']]} "
                   f"{'подавляющих' if kind == 'zei' else 'подавляемых'}: {d}"
                   + (f" ({' '.join(hits)})" if hits else ""))
    m = max(depths)
    top = [c for c, d in zip(cands, depths) if d == m]
    if len(top) == 1:
        log.append(f"Глубже всех {Z[top[0]['upper']]} ({m}) → 涉害.")
        return top[0], "涉害"
    log.append(f"Глубина равна ({m}) у {', '.join(Z[c['upper']] for c in top)} → 孟仲季.")
    c, lab = _meng_zhong_ji(top, ds, log)
    return c, lab


def three_transmissions(ds: int, db: int, general: int, hour: int, *, shehai: str = "depth",
                        biezhe_yin: str = "branch", fuyin_zimao: str = "chong") -> dict:
    """Три передачи (三传) по девяти методам. Возвращает dict: method, kind (课体), chuan, lessons, log.

    shehai: 'depth' — 《六壬大全》 (глубина 涉害, при равенстве 孟→仲→季, затем 缀瑕);
            'mengzhongji' — 《大六壬指南》 (сразу 孟→仲→季, затем 缀瑕).
    biezhe_yin: 'branch' — Инь-день 别责 берёт саму ветвь «支前三合»; 'heaven' — небесную над ней.
    fuyin_zimao: 'chong' — 伏吟 卯→子: третья передача 午 (冲, 《六壬大全》 卷七 «杜传»);
                 'xing' — третья передача 卯 (刑 子→卯, пример 《大六壬指南》 卷三, день 辛卯).
    """
    plate = heaven_plate(general, hour)
    lessons = four_lessons(ds, db, plate)
    log: list[str] = []
    yang_day = ds % 2 == 0
    jg = JI_GONG[ds]
    gan_shang, zhi_shang = plate[jg], plate[db]
    names: list[str] = []
    method = ""
    sel = None  # метод выбора первой передачи внутри 返吟

    def nxt(b: int) -> int:
        return plate[b]

    # --- 伏吟 ---
    if general == hour:
        method = "fuyin"
        names.append("伏吟")
        l1 = lessons[0]
        from_gan = True
        if l1["rel"] in ("zei", "ke"):
            chu = jg
            log.append(f"伏吟 (月将 = час): небесная пластина совпадает с земной. Есть 克 в 1-м уроке "
                       f"({l1['text']}, {REL_CN[l1['rel']]}) → «伏吟有克还为用»: первая передача {Z[chu]}.")
        elif yang_day:
            chu = jg
            names.append("自任")
            log.append(f"伏吟 без 克, Ян-день → первая передача — верх над стволом (干上) {Z[chu]} (自任).")
        else:
            chu = db
            from_gan = False
            names.append("自信")
            log.append(f"伏吟 без 克, Инь-день → первая передача — верх над ветвью дня (支上) {Z[chu]} (自信).")
        if chu in SELF_XING:
            zhong = db if from_gan else jg
            names.append("杜传")
            log.append(f"{Z[chu]} — самонаказание (自刑) → вторая передача «次传颠倒日辰»: "
                       f"{'支 (ветвь дня)' if from_gan else '干上 (дворец ствола)'} {Z[zhong]} (杜传).")
        else:
            zhong = XING[chu]
            log.append(f"Вторая передача — то, что «наказывает» {Z[chu]} (三刑): {Z[zhong]}.")
        if zhong in SELF_XING:
            mo = (zhong + 6) % 12
            log.append(f"{Z[zhong]} — 自刑 → третья передача — противостояние (冲) {Z[mo]}.")
        elif XING[zhong] == chu and fuyin_zimao == "chong":
            mo = (zhong + 6) % 12
            log.append(f"{Z[zhong]} наказывает {Z[chu]} (子卯 взаимно) — «子卯两刑，不复再传» (《六壬大全》) → "
                       f"третья передача — 冲 {Z[mo]}.")
        else:
            mo = XING[zhong]
            log.append(f"Третья передача — то, что «наказывает» {Z[zhong]}: {Z[mo]}.")
        return _pack(method, sel, names, [chu, zhong, mo], lessons, plate, log)

    fan = (general - hour) % 12 == 6
    if fan:
        method = "fanyin"
        names.append("返吟")
    zei = [l for l in lessons if l["rel"] == "zei"]
    ke = [l for l in lessons if l["rel"] == "ke"]

    # --- 贼克 / 比用 / 涉害 ---
    if zei or ke:
        kind = "zei" if zei else "ke"
        pool = _unique_uppers(zei if zei else ke)
        log.append("Отношения уроков: " + "; ".join(f"{l['n']}) {l['text']} {REL_CN[l['rel']]}" for l in lessons) + ".")
        if zei and ke:
            log.append("Есть и 下贼上, и 上克下 → «先贼后克»: берутся только 贼.")
        if len(pool) == 1:
            chu = pool[0]["upper"]
            sub = "重审" if kind == "zei" else "元首"
            names.append(sub)
            sel = "zeike"
            log.append(f"Один {'贼' if kind == 'zei' else '克'} ({pool[0]['text']}) → {sub}: первая передача {Z[chu]}.")
        else:
            bi = [c for c in pool if b_yang(c["upper"]) == yang_day]
            log.append(f"Несколько кандидатов: {', '.join(Z[c['upper']] for c in pool)}. День "
                       f"{'Ян' if yang_day else 'Инь'} ({S[ds]}); «сходны» по полярности (比): "
                       f"{', '.join(Z[c['upper']] for c in bi) or 'нет'}.")
            if len(bi) == 1:
                chu = bi[0]["upper"]
                names.append("知一")
                sel = "biyong"
                log.append(f"Один сходный → 比用 (知一): первая передача {Z[chu]}.")
            else:
                cands = bi if bi else pool
                log.append("«俱比俱不比» → 涉害" + (" среди сходных." if bi else " среди всех."))
                c, lab = _shehai(cands, ds, kind, shehai, log)
                chu = c["upper"]
                names.append("涉害")
                if lab != "涉害":
                    names.append(lab)
                sel = "shehai"
        if not fan:
            method = sel
        zhong = nxt(chu)
        mo = nxt(zhong)
        log.append(f"Передачи «相因»: вторая — небесная ветвь над {Z[chu]} = {Z[zhong]}, "
                   f"третья — над {Z[zhong]} = {Z[mo]}.")
        return _pack(method, sel, names, [chu, zhong, mo], lessons, plate, log)

    log.append("В четырёх уроках нет ни 贼, ни 克: " + "; ".join(f"{l['n']}) {l['text']} {REL_CN[l['rel']]}" for l in lessons) + ".")

    # --- 返吟 без克: 井栏射 ---
    if fan:
        if db not in (1, 7):  # pragma: no cover - без 克 返吟 бывает только в дни 丑/未
            raise AssertionError("返吟 без 克 вне дней 丑/未")
        chu = plate[5] if db == 1 else plate[11]
        zhong, mo = zhi_shang, gan_shang
        names.append("井栏射")
        sel = "jinglan"
        log.append(f"返吟 без 克 (井栏射, «无依»): ветвь дня {Z[db]} «стреляет» в {'巳' if db == 1 else '亥'}; "
                   f"над ней стоит {Z[chu]} → первая передача; вторая — 支上 {Z[zhong]}, третья — 干上 {Z[mo]}.")
        if jg == db:
            log.append("День ещё и 八专 (干支同位): правило 八专 дало бы те же три передачи.")
        return _pack(method, sel, names, [chu, zhong, mo], lessons, plate, log)

    # --- 八专 (干支同位, без 克; «论克不论遥») ---
    if jg == db:
        method = "bazhuan"
        names.append("八专")
        if yang_day:
            chu = (gan_shang + 2) % 12
            log.append(f"八专 (干支同位 {S[ds]}{Z[db]}), Ян-день: от верха 1-го урока {Z[gan_shang]} по ходу "
                       f"«连本位» три знака → {Z[chu]}.")
        else:
            u4 = lessons[3]["upper"]
            chu = (u4 - 2) % 12
            log.append(f"八专 (干支同位 {S[ds]}{Z[db]}), Инь-день: от верха 4-го урока {Z[u4]} против хода "
                       f"три знака → {Z[chu]}.")
        zhong = mo = gan_shang
        log.append(f"Вторая и третья передачи — верх над стволом (干上) {Z[gan_shang]}.")
        if chu == gan_shang:
            names.append("独足")
        else:
            names.append("帷薄不修")
        return _pack(method, sel, names, [chu, zhong, mo], lessons, plate, log)

    # --- 遥克 ---
    ups = _unique_uppers(lessons[1:])
    de = STEM_EL[ds]
    shen_ke_ri = [l for l in ups if controls(BRANCH_EL[l["upper"]], de)]
    ri_ke_shen = [l for l in ups if controls(de, BRANCH_EL[l["upper"]])]
    yao, yname = (shen_ke_ri, "蒿矢") if shen_ke_ri else (ri_ke_shen, "弹射")
    if yao:
        method = "yaoke"
        names.append(yname)
        log.append(f"遥克: верхи уроков 2–4 {', '.join(Z[l['upper']] for l in ups)}; "
                   + ("подавляют ствол дня (神遥克日, 蒿矢): " if yname == "蒿矢" else
                      "никто не подавляет ствол дня; ствол подавляет (日遥克神, 弹射): ")
                   + ", ".join(Z[l["upper"]] for l in yao) + ".")
        if len(yao) == 1:
            chu = yao[0]["upper"]
        else:
            bi = [c for c in yao if b_yang(c["upper"]) == yang_day]
            log.append(f"Несколько → 比: сходных по полярности {', '.join(Z[c['upper']] for c in bi) or 'нет'}.")
            if len(bi) == 1:
                chu = bi[0]["upper"]
            else:
                # Во всех 720 уроках 比 разрешает выбор однозначно (проверено перебором, тест
                # test_yaoke_always_resolved_by_bi); ветка ниже — страховка: «先举» (《观月经》).
                cands = bi if bi else yao  # pragma: no cover
                chu = cands[0]["upper"]  # pragma: no cover
                log.append(f"«俱比俱不比，先举用为真»: первый по порядку уроков → {Z[chu]}.")  # pragma: no cover
        zhong = nxt(chu)
        mo = nxt(zhong)
        log.append(f"Первая передача {Z[chu]}; вторая — над ней {Z[zhong]}; третья — {Z[mo]}.")
        return _pack(method, sel, names, [chu, zhong, mo], lessons, plate, log)
    log.append("遥克 нет: ни один из верхов уроков 2–4 не подавляет ствол дня и не подавляется им.")

    # --- 昴星 (4 урока) / 别责 (3 урока) ---
    nd = distinct_lessons(lessons)
    if nd == 4:
        method = "maoxing"
        if yang_day:
            chu = plate[9]
            zhong, mo = zhi_shang, gan_shang
            names.append("虎视")
            log.append(f"昴星, Ян-день («阳仰»): над земным 酉 стоит {Z[chu]} → первая передача; "
                       f"вторая — 支上 {Z[zhong]}, третья — 干上 {Z[mo]} (虎视转蓬).")
        else:
            chu = earth_under(plate, 9)
            zhong, mo = gan_shang, zhi_shang
            names.append("冬蛇掩目")
            log.append(f"昴星, Инь-день («阴俯»): небесный 酉 стоит над земным {Z[chu]} → первая передача; "
                       f"вторая — 干上 {Z[zhong]}, третья — 支上 {Z[mo]} (冬蛇掩目).")
        return _pack(method, sel, names, [chu, zhong, mo], lessons, plate, log)

    method = "biezhe"
    names.append("别责")
    if yang_day:
        hs = (ds + 5) % 10
        chu = plate[JI_GONG[hs]]
        log.append(f"别责 (уроков только {nd}), Ян-день: ствол-партнёр (干合) {S[ds]}→{S[hs]}, его дворец "
                   f"{Z[JI_GONG[hs]]}, над ним {Z[chu]} → первая передача.")
    else:
        sh = (db + 4) % 12
        if biezhe_yin == "heaven":
            chu = plate[sh]
            log.append(f"别责 (уроков только {nd}), Инь-день: «支前三合» {Z[db]}→{Z[sh]}; вариант 'heaven' — "
                       f"небесная ветвь над ним {Z[chu]}.")
        else:
            chu = sh
            log.append(f"别责 (уроков только {nd}), Инь-день: «支前三合» — следующая ветвь тройки {Z[db]} → {Z[chu]} "
                       f"(сама ветвь, «而不用乘神» — 《指南》).")
    zhong = mo = gan_shang
    log.append(f"Вторая и третья передачи — 干上 {Z[gan_shang]}.")
    return _pack(method, sel, names, [chu, zhong, mo], lessons, plate, log)


def _pack(method, sel, names, chuan, lessons, plate, log) -> dict:
    return {"method": method, "selection": sel, "kind": names, "chuan": chuan, "lessons": lessons,
            "plate": plate, "log": log}


# ---------------------------------------------------------------------------
# Генералы, 遁干, 六亲, 空亡
# ---------------------------------------------------------------------------


def noble_branch(ds: int, is_day: bool, table: str = "daquan") -> int:
    d, n = NOBLE_TABLES[table][ds]
    return d if is_day else n


def generals_on_plate(noble: int, plate: list[int]) -> tuple[dict[int, int], bool, int]:
    """Раскладка 12 генералов: {небесная ветвь: индекс генерала}, по ходу ли, земная ветвь под 贵人.

    По ходу (顺), если 贵人 стоит над 亥子丑寅卯辰, против хода (逆) — над 巳午未申酉戌
    («在天门之前、地户之后则顺行；若居地户之前、天门之后则逆行» — 《大六壬指南》).
    """
    e = earth_under(plate, noble)
    fwd = e in (11, 0, 1, 2, 3, 4)
    m = {}
    for k in range(12):
        x = (noble + k) % 12 if fwd else (noble - k) % 12
        m[x] = k
    return m, fwd, e


def xun_kong(day_idx: int) -> tuple[int, int, int]:
    """(ветвь 旬首, пустота1, пустота2) для столпа дня."""
    xs = (day_idx - day_idx % 10) % 12
    return xs, (xs + 10) % 12, (xs + 11) % 12


def dun_gan(day_idx: int, b: int, void: str = "none") -> int | None:
    """遁干: ствол, который ветвь b получает в 旬 дня (旬首 甲 на ветви 旬首, далее по порядку).

    Пустые ветви (空亡) ствола в своём 旬 не имеют: void='none' → None; void='next' → 甲/乙
    (продолжение счёта, как в примерах 《大六壬指南》 卷三: в 甲子旬 戌 = 甲, 亥 = 乙).
    """
    xs = (day_idx - day_idx % 10) % 12
    k = (b - xs) % 12
    if k < 10:
        return k
    return k - 10 if void == "next" else None


def liuqin(ds: int, b: int) -> tuple[str, str]:
    d = (BRANCH_EL[b] - STEM_EL[ds]) % 5
    return LIUQIN[d]


# «家» генералов по 《六壬大全》 卷二 («贵人…己丑土», «螣蛇…丁巳火», «六合…家乙卯木» … «天后…家壬子»)
TIAN_JIANG_HOME = ["己丑", "丁巳", "丙午", "乙卯", "戊辰", "甲寅", "戊戌", "庚申", "己未", "癸亥", "辛酉", "壬子"]


def _gen_info(k: int) -> dict:
    cn, short, py, ru, el, gj = TIAN_JIANG[k]
    return {"index": k, "cn": cn, "short": short, "pinyin": py, "ru": ru, "element": el, "nature": gj,
            "home": TIAN_JIANG_HOME[k]}


def build_chart(day_idx: int, hour: int, general: int, is_day: bool, *, noble_table: str = "daquan",
                shehai: str = "depth", biezhe_yin: str = "branch", fuyin_zimao: str = "chong") -> dict:
    """Полный 课盘 по 干支 дня, ветви часа и месячному генералу (без дат и астрономии)."""
    ds, db = day_idx % 10, day_idx % 12
    tt = three_transmissions(ds, db, general, hour, shehai=shehai, biezhe_yin=biezhe_yin, fuyin_zimao=fuyin_zimao)
    plate = tt["plate"]
    noble = noble_branch(ds, is_day, noble_table)
    gmap, fwd, noble_earth = generals_on_plate(noble, plate)
    _, k1, k2 = xun_kong(day_idx)

    def binfo(b: int) -> dict:
        dg = dun_gan(day_idx, b)
        lq = liuqin(ds, b)
        return {"branch": Z[b], "index": b, "element": EL[BRANCH_EL[b]],
                "general": _gen_info(gmap[b]), "dun_gan": S[dg] if dg is not None else None,
                "dun_gan_void_next": None if dg is not None else S[dun_gan(day_idx, b, "next")],
                "liuqin": {"cn": lq[0], "ru": lq[1]}, "kong": b in (k1, k2),
                "earth": Z[earth_under(plate, b)]}

    lessons = []
    for l in tt["lessons"]:
        lessons.append({"n": l["n"], "upper": Z[l["upper"]], "lower": l["lower"],
                        "lower_position": Z[l["lower_pos"]], "relation": l["rel"],
                        "relation_cn": REL_CN[l["rel"]], "general": TIAN_JIANG[gmap[l["upper"]]][0],
                        "text": l["text"]})
    chuan = []
    for i, b in enumerate(tt["chuan"]):
        chuan.append({"stage": ["初传", "中传", "末传"][i], "stage_ru": ["первая", "вторая", "третья"][i],
                      **binfo(b)})
    plates = []
    for e in range(12):
        h = plate[e]
        plates.append({"earth": Z[e], "heaven": Z[h], "general": TIAN_JIANG[gmap[h]][0]})
    m = tt["method"]
    return {
        "day": ganzhi(day_idx), "hour_branch": Z[hour], "general": {"branch": Z[general],
                                                                  "name": GENERAL_NAMES[general][0],
                                                                  "ru": GENERAL_NAMES[general][2]},
        "plates": plates,
        "lessons": lessons,
        "transmissions": {
            "method": {"key": m, "cn": METHODS[m][0] if m in METHODS else m,
                       "ru": METHODS[m][1] if m in METHODS else m},
            "selection": tt["selection"],
            "kind": tt["kind"],
            "chuan": chuan,
            "sanchuan": "".join(Z[b] for b in tt["chuan"]),
        },
        "noble": {"branch": Z[noble], "is_day": is_day, "table": noble_table,
                  "earth": Z[noble_earth], "direction": "forward" if fwd else "backward",
                  "direction_cn": "顺" if fwd else "逆"},
        "kong_wang": [Z[k1], Z[k2]],
        "log": tt["log"],
    }


# ---------------------------------------------------------------------------
# Время
# ---------------------------------------------------------------------------


def _iso(dt: datetime) -> str:
    return dt.replace(microsecond=0).isoformat()


def _jd_iso(jd: float) -> str:
    return _iso(jd_to_utc(jd).astimezone(timezone.utc)).replace("+00:00", "Z")


def sun_altitude(jd_ut: float, lat: float, lon: float) -> float:
    """Геометрическая высота центра Солнца, градусы."""
    ra, dec = swe.calc_ut(jd_ut, swe.SUN, swe.FLG_SWIEPH | swe.FLG_EQUATORIAL)[0][:2]
    lst = swe.sidtime(jd_ut) * 15.0 + lon
    h = radians((lst - ra) % 360.0)
    phi, d = radians(lat), radians(dec)
    return degrees(asin(sin(phi) * sin(d) + cos(phi) * cos(d) * cos(h)))


def _gender(g: str | None) -> str | None:
    if g is None:
        return None
    g = g.strip().lower()
    if g in ("male", "m", "м", "муж", "мужской", "man"):
        return "male"
    if g in ("female", "f", "ж", "жен", "женский", "woman"):
        return "female"
    return None


def _parse_on_datetime(v) -> datetime:
    if isinstance(v, datetime):
        return v
    s = str(v).strip()
    if s.lower() == "now":
        return datetime.now(timezone.utc)
    return datetime.fromisoformat(s.replace("Z", "+00:00"))


def _bazi_year(jd: float, year: int) -> int:
    lc = find_sun_longitude(315.0, swe.julday(year, 2, 20, 0.0), search_back=True)
    return year if jd >= lc else year - 1


def calculate(b: BirthInput, **options) -> dict:
    """Построить 课盘 Да Лю Жэнь на момент рождения (по умолчанию) или на момент консультации.

    options:
      on_datetime: ISO-строка ('2026-10-14T15:30', можно со смещением) / datetime / 'now' —
          момент консультации; наивное время считается местным в поясе on_tz (по умолч. b.tz)
          в месте рождения (или on_lat/on_lon/on_place);
      solar_time: 'true' (по умолч.) | 'mean' | 'clock' — шкала для ветви часа и даты;
      zi_hour: 'late' (по умолч.; 23:00–24:00 не меняет день) | 'early' (день меняется в 23:00);
      noble_table: 'daquan' (по умолч.) | 'xieji' | 'cao';
      day_night: 'branch' (по умолч.; 卯…申 — день) | 'sun' (Солнце над горизонтом) | 'day' | 'night';
      shehai: 'depth' (по умолч., 《六壬大全》) | 'mengzhongji' (《大六壬指南》);
      biezhe_yin: 'branch' (по умолч.) | 'heaven';
      fuyin_zimao: 'chong' (по умолч., 《六壬大全》: 卯子午) | 'xing' (《大六壬指南》: 卯子卯).
    """
    def opt(name: str, default: str, allowed: tuple[str, ...]) -> str:
        v = options.get(name, default)
        if v is True:
            v = "true"
        elif v is False:
            v = "clock"
        v = str(v).strip().lower()
        if v not in allowed:
            raise ValueError(f"{name}: допустимо {' | '.join(allowed)}")
        return v

    solar_time = opt("solar_time", "true", ("true", "mean", "clock"))
    zi_hour = opt("zi_hour", "late", ("late", "early"))
    noble_table = opt("noble_table", "daquan", tuple(NOBLE_TABLES))
    day_night = opt("day_night", "branch", ("branch", "sun", "day", "night"))
    shehai = opt("shehai", "depth", ("depth", "mengzhongji"))
    biezhe_yin = opt("biezhe_yin", "branch", ("branch", "heaven"))
    fuyin_zimao = opt("fuyin_zimao", "chong", ("chong", "xing"))
    kw = {"noble_table": noble_table, "biezhe_yin": biezhe_yin, "fuyin_zimao": fuyin_zimao}

    warnings: list[str] = []
    steps: list[str] = []

    def add(msg: str) -> None:
        steps.append(f"Шаг {len(steps) + 1}. {msg}")

    birth = b
    on = options.get("on_datetime")
    purpose = "birth"
    if on is not None:
        purpose = "consultation"
        dt = _parse_on_datetime(on)
        tz = options.get("on_tz") or b.tz
        lat = options.get("on_lat", b.lat)
        lon = options.get("on_lon", b.lon)
        if options.get("on_place"):
            from calculators.common.places import resolve_place
            p = resolve_place(options["on_place"])
            if not p:
                raise ValueError(f"Место консультации не найдено: {options['on_place']}")
            lat, lon, tz = p["lat"], p["lon"], options.get("on_tz") or p["tz"]
        if dt.tzinfo is not None:
            if tz is None:
                # пояс не задан ни у рождения, ни у консультации: берём смещение из самой строки
                # (иначе час считался бы по часам UTC, а не по местным часам консультации)
                tz = fmt_offset_hms(dt.utcoffset())
            if tz.upper() not in ("LMT",) and not tz.upper().startswith(("UTC", "GMT", "+", "-")):
                dt = dt.astimezone(ZoneInfo(tz)).replace(tzinfo=None)
            else:
                # фиксированный пояс: переводим через normalize-совместимую строку
                off = BirthInput(2000, 1, 1, 0, 0, tz=tz, lon=lon)
                n0 = normalize(off)
                dt = (dt.astimezone(timezone.utc) + timedelta(hours=n0.utc_offset_hours)).replace(tzinfo=None)
        b = BirthInput(dt.year, dt.month, dt.day, dt.hour, dt.minute, tz=tz, lat=lat, lon=lon,
                       gender=birth.gender, second=dt.second)

    if not b.has_time:
        return {
            "method": "da_liu_ren", "variant": "не рассчитано", "inputs_used": {"has_time": False},
            "warnings": ["Время неизвестно: 课盘 Да Лю Жэнь без часа не строится (月将 ставится на ветвь часа). "
                         "Укажите время рождения или задайте on_datetime (момент консультации)."],
            "chart": None, "steps": [],
        }
    if b.tz is None:
        raise ValueError("Не задан часовой пояс (tz) или место — без них нельзя найти момент в UT.")

    n = normalize(b)
    warnings.extend(n.warnings)
    jd = n.jd_ut
    add(f"{'Момент консультации' if purpose == 'consultation' else 'Момент рождения'}: {n.local:%d.%m.%Y %H:%M} "
        f"({b.tz}, {fmt_offset(n.utc_offset_hours)}, источник смещения: {n.offset_source}) → "
        f"UTC {n.utc:%d.%m.%Y %H:%M:%S}; JD(UT) = {jd:.5f}.")

    # --- 月将 ---
    lam = sun_longitude(jd)
    general = monthly_general(lam)
    k = int(((lam - 330.0) % 360.0) // 30.0)
    zq_prev = ZHONGQI[k]
    zq_next = ZHONGQI[(k + 1) % 12]
    jd_prev = find_sun_longitude(zq_prev[0], jd, search_back=True)
    jd_next = find_sun_longitude(zq_next[0], jd, search_back=False)
    add(f"Долгота Солнца λ = {lam:.4f}°. Последний 中气: {zq_prev[1]} ({zq_prev[0]}°) {_jd_iso(jd_prev)} UT; "
        f"следующий: {zq_next[1]} ({zq_next[0]}°) {_jd_iso(jd_next)} UT. Месячный генерал (月将) = "
        f"{Z[general]} {GENERAL_NAMES[general][0]}.")
    for jdx, nm in ((jd_prev, zq_prev[1]), (jd_next, zq_next[1])):
        if abs(jd - jdx) < 1.0:
            warnings.append(f"Момент в пределах {abs(jd - jdx) * 24:.1f} ч от 中气 {nm}: при ошибке времени "
                            f"месячный генерал (月将) может смениться — сравните с соседним.")

    # --- время карты, день, час ---
    used_mode = solar_time
    if solar_time != "clock" and b.lon is None:
        warnings.append("Долгота неизвестна — солнечное время не вычислить, использовано время часов.")
        used_mode = "clock"
    if used_mode == "clock":
        chart_t = n.local
    elif used_mode == "mean":
        chart_t = local_mean_time(n.utc, b.lon)
    else:
        chart_t = true_solar_time(n.utc, b.lon)
    mode_ru = {"clock": "время часов", "mean": "местное среднее солнечное (LMT)",
               "true": "истинное солнечное"}[used_mode]
    d = chart_t.date()
    is23 = chart_t.hour == 23
    di = day_index(d + timedelta(days=1)) if (is23 and zi_hour == "early") else day_index(d)
    minutes = chart_t.hour * 60 + chart_t.minute + chart_t.second / 60.0
    hb = hour_branch(minutes)
    stem_day = day_index(d + timedelta(days=1)) % 10 if is23 else di % 10
    hs = (zi_first_stem(stem_day) + hb) % 10
    hi = ganzhi_index(hs, hb)
    add(f"Время карты ({mode_ru}): {chart_t:%d.%m.%Y %H:%M:%S} → час {Z[hb]} ({BRANCHES[hb][5]}), "
        f"столп часа {ganzhi(hi)}; столп дня {ganzhi(di)}"
        + (f" (23-й час, zi_hour='{zi_hour}')" if is23 else "") + ".")
    to_b = (minutes + 60) % 120
    near = min(to_b, 120 - to_b)
    if near < 15:
        warnings.append(f"Время карты в {near:.0f} мин от границы двухчасовки: ветвь часа (占时) и вся пластина "
                        f"чувствительны к точности времени и к solar_time.")

    # --- день/ночь для 贵人 ---
    alt = None
    if day_night == "day":
        is_day = True
        dn_note = "задано вручную: дневной"
    elif day_night == "night":
        is_day = False
        dn_note = "задано вручную: ночной"
    elif day_night == "sun":
        if b.lat is None or b.lon is None:
            warnings.append("day_night='sun' требует координаты — использовано правило ветвей (卯…申 — день).")
            is_day = 3 <= hb <= 8
            dn_note = "по ветви часа (卯…申 — день)"
        else:
            alt = sun_altitude(jd, b.lat, b.lon)
            is_day = alt > -0.8333
            dn_note = f"по Солнцу: высота {alt:.2f}° ({'над' if is_day else 'под'} горизонтом)"
    else:
        is_day = 3 <= hb <= 8
        dn_note = "по ветви часа (卯辰巳午未申 — день, 酉戌亥子丑寅 — ночь)"

    ch = build_chart(di, hb, general, is_day, shehai=shehai, **kw)
    plate = heaven_plate(general, hb)
    add(f"Небесная пластина: {Z[general]} (月将) ставится на земной {Z[hb]} (час), далее по порядку: "
        + " ".join(f"{Z[e]}←{Z[plate[e]]}" for e in range(12)) + " (земная←небесная).")
    ds = di % 10
    add(f"Ствол дня {S[ds]} «живёт» (寄宫) в {Z[JI_GONG[ds]]}. Четыре урока: "
        + "; ".join(f"{l['n']}) {l['upper']}/{l['lower']} ({l['relation_cn']})" for l in ch["lessons"]) + ".")
    for line in ch["log"]:
        add(line)
    nb = ch["noble"]
    add(f"Благородный (贵人): таблица '{noble_table}', {'дневной' if is_day else 'ночной'} ({dn_note}) → "
        f"{nb['branch']}; стоит над земным {nb['earth']} → {'по ходу (顺)' if nb['direction'] == 'forward' else 'против хода (逆)'}.")
    add("Три передачи: " + " → ".join(
        f"{c['branch']} ({c['general']['cn']}, {c['liuqin']['cn']}, 遁干 {c['dun_gan'] or '—'}"
        f"{', 空' if c['kong'] else ''})" for c in ch["transmissions"]["chuan"]) + ".")

    # альтернативы: школы и пограничные случаи
    alternatives = []
    opts_now = {"shehai": shehai, "biezhe_yin": biezhe_yin, "fuyin_zimao": fuyin_zimao}

    def day_hour(ct: datetime, zh: str) -> tuple[int, int]:
        """(индекс столпа дня, ветвь часа) для времени карты ct при правиле zi_hour = zh."""
        mm = ct.hour * 60 + ct.minute + ct.second / 60.0
        dd = ct.date()
        return (day_index(dd + timedelta(days=1)) if (ct.hour == 23 and zh == "early") else day_index(dd),
                hour_branch(mm))

    def dn_for(hb_: int) -> bool:
        return (3 <= hb_ <= 8) if day_night == "branch" else is_day

    def brief(o: dict) -> dict:
        return {"day": o["day"], "hour_branch": o["hour_branch"], "general": o["general"]["branch"],
                "sanchuan": o["transmissions"]["sanchuan"], "kind": o["transmissions"]["kind"],
                "chuan_generals": [c["general"]["cn"] for c in o["transmissions"]["chuan"]]}

    other = build_chart(di, hb, general, not is_day, shehai=shehai, **kw)
    if day_night in ("branch", "sun"):
        alternatives.append({"what": "другой Благородный (день↔ночь)", "noble": other["noble"]["branch"],
                             "direction": other["noble"]["direction"],
                             "chuan_generals": [c["general"]["cn"] for c in other["transmissions"]["chuan"]]})
    if day_night == "branch" and hb in (2, 9):
        warnings.append(f"Час {Z[hb]} — пограничный для дневного/ночного Благородного: правило «卯…申 — день» "
                        f"(по умолчанию) не единственное. В 《六壬大全》 卷七 при часе 酉 во всех трёх примерах взят "
                        f"дневной 贵人, при часе 寅 — в двух из четырёх; 卷十一 советует считать по восходу и закату "
                        f"(day_night='sun'). Другой Благородный — в alternatives.")
    # школы, меняющие три передачи: 涉害, 伏吟 子卯, 别责 Инь-дня
    for name, values, label in (("shehai", ("depth", "mengzhongji"), "Школы 涉害 расходятся"),
                                ("fuyin_zimao", ("chong", "xing"), "伏吟 子卯: школы расходятся"),
                                ("biezhe_yin", ("branch", "heaven"), "别责 Инь-дня: школы расходятся")):
        for t in values:
            if t == opts_now[name]:
                continue
            o = build_chart(di, hb, general, is_day, noble_table=noble_table, **{**opts_now, name: t})
            if o["transmissions"]["sanchuan"] != ch["transmissions"]["sanchuan"]:
                alternatives.append({"what": f"{name}='{t}'", "sanchuan": o["transmissions"]["sanchuan"],
                                     "kind": o["transmissions"]["kind"]})
                warnings.append(f"{label}: {name}='{t}' даёт три передачи "
                                f"{o['transmissions']['sanchuan']} — см. alternatives.")
    # другие таблицы Благородного (передачи те же, меняются генералы) — без предупреждения
    for tbl in NOBLE_TABLES:
        if tbl == noble_table:
            continue
        o = build_chart(di, hb, general, is_day, shehai=shehai, biezhe_yin=biezhe_yin, fuyin_zimao=fuyin_zimao,
                        noble_table=tbl)
        if (o["noble"]["branch"], o["noble"]["direction"]) != (ch["noble"]["branch"], ch["noble"]["direction"]):
            alternatives.append({"what": f"noble_table='{tbl}'", "noble": o["noble"]["branch"],
                                 "direction": o["noble"]["direction"],
                                 "chuan_generals": [c["general"]["cn"] for c in o["transmissions"]["chuan"]]})
    for mode in ("clock", "mean", "true"):
        if mode == used_mode or (mode != "clock" and b.lon is None):
            continue
        ct = n.local if mode == "clock" else (local_mean_time(n.utc, b.lon) if mode == "mean"
                                               else true_solar_time(n.utc, b.lon))
        di2, hb2 = day_hour(ct, zi_hour)
        if (hb2, di2) != (hb, di):
            o = build_chart(di2, hb2, general, dn_for(hb2), shehai=shehai, **kw)
            alternatives.append({"what": f"solar_time='{mode}'", "chart_time": _iso(ct), "day": o["day"],
                                 "hour_branch": o["hour_branch"], "sanchuan": o["transmissions"]["sanchuan"],
                                 "kind": o["transmissions"]["kind"]})
            warnings.append(f"При solar_time='{mode}' час/день другие ({o['day']}, {o['hour_branch']}) → "
                            f"три передачи {o['transmissions']['sanchuan']} — см. alternatives.")
    # 23:00–24:00: день зависит от правила zi_hour (для 六壬 классикой не определено)
    if chart_t.hour == 23:
        zh2 = "early" if zi_hour == "late" else "late"
        di2, _ = day_hour(chart_t, zh2)
        o = build_chart(di2, hb, general, is_day, shehai=shehai, **kw)
        alternatives.append({"what": f"zi_hour='{zh2}'", **brief(o)})
        warnings.append(f"Время карты 23:00–24:00: при zi_hour='{zh2}' столп дня {o['day']} → три передачи "
                        f"{o['transmissions']['sanchuan']} — см. alternatives.")
    # соседняя ветвь часа (если до границы двухчасовки < 15 мин)
    if near < 15:
        shift = -(to_b + 1.0) if to_b < 60 else (120.0 - to_b + 1.0)
        ct = chart_t + timedelta(minutes=shift)
        di2, hb2 = day_hour(ct, zi_hour)
        o = build_chart(di2, hb2, general, dn_for(hb2), shehai=shehai, **kw)
        alternatives.append({"what": f"соседняя ветвь часа ({Z[hb2]}, время карты {_iso(ct)})", **brief(o)})
    # соседний месячный генерал (если до 中气 < 1 суток)
    for jdx, nm, g2 in ((jd_prev, zq_prev[1], (general + 1) % 12), (jd_next, zq_next[1], (general - 1) % 12)):
        if abs(jd - jdx) < 1.0:
            o = build_chart(di, hb, g2, is_day, shehai=shehai, **kw)
            alternatives.append({"what": f"соседний 月将 {Z[g2]} (по другую сторону 中气 {nm})", **brief(o)})

    # 本命 / 行年
    gender = _gender(birth.gender)
    nian = None
    if birth.has_time or birth.tz:
        try:
            nb_ = birth if birth.has_time else replace(birth, hour=12, minute=0)
            nbirth = normalize(nb_) if nb_.tz else None
        except Exception:  # pragma: no cover
            nbirth = None
        if nbirth is not None:
            by = _bazi_year(nbirth.jd_ut, nbirth.utc.year)
            cy = _bazi_year(jd, n.utc.year)
            age = cy - by + 1
            ben = (by - 4) % 12
            xing = None
            if gender == "male":
                xing = ganzhi((2 + age - 1) % 60)
            elif gender == "female":
                xing = ganzhi((8 - (age - 1)) % 60)
            nian = {"ben_ming": Z[ben], "ben_ming_heaven_over": None,
                    "age_xusui_by_lichun": age, "xing_nian": xing, "xing_nian_heaven_over": None,
                    "note": "本命 — ветвь года рождения (по Личуню); 行年 — мужчина: 1 год = 丙寅 по ходу, "
                            "женщина: 1 год = 壬申 против хода (《六壬大全》 卷八); возраст — по годам Личуня (⚠ "
                            "традиционно — по лунному Новому году)."}
            nian["ben_ming_heaven_over"] = Z[plate[ben]]
            if xing:
                nian["xing_nian_heaven_over"] = Z[plate[Z.index(xing[1])]]

    variant = (f"《六壬大全》: 月将 по 中气, 贵人 '{noble_table}', день/ночь '{day_night}', 涉害 '{shehai}', "
               f"solar_time='{used_mode}', zi_hour='{zi_hour}'")
    return {
        "method": "da_liu_ren",
        "variant": variant,
        "inputs_used": {
            "purpose": purpose,
            "local": _iso(n.local), "tz": b.tz, "utc_offset": fmt_offset(n.utc_offset_hours),
            "offset_source": n.offset_source, "utc": _iso(n.utc).replace("+00:00", "Z"),
            "jd_ut": round(jd, 6), "lat": b.lat, "lon": b.lon, "has_time": True,
            "chart_time": _iso(chart_t), "gender": gender,
            "options": {"solar_time": used_mode, "zi_hour": zi_hour, "noble_table": noble_table,
                        "day_night": day_night, "shehai": shehai, "biezhe_yin": biezhe_yin,
                        "fuyin_zimao": fuyin_zimao},
        },
        "warnings": warnings,
        "solar": {"sun_longitude": round(lam, 5),
                  "zhongqi_prev": {"cn": zq_prev[1], "ru": zq_prev[2], "deg": zq_prev[0], "utc": _jd_iso(jd_prev)},
                  "zhongqi_next": {"cn": zq_next[1], "ru": zq_next[2], "deg": zq_next[0], "utc": _jd_iso(jd_next)},
                  "sun_altitude": round(alt, 3) if alt is not None else None},
        "pillars": {"day": ganzhi(di), "hour": ganzhi(hi)},
        "general": {"branch": Z[general], "name": GENERAL_NAMES[general][0], "pinyin": GENERAL_NAMES[general][1],
                    "ru": GENERAL_NAMES[general][2]},
        "hour_branch": Z[hb],
        "chart": ch,
        "nian_ming": nian,
        "alternatives": alternatives,
        "steps": steps,
    }


if __name__ == "__main__":  # pragma: no cover
    import json

    r = calculate(BirthInput(1990, 5, 15, 14, 30, place="Москва", gender="female"))
    print(json.dumps(r, ensure_ascii=False, indent=1)[:5000])
