"""Ци Мэнь Дунь Цзя (奇门遁甲): карта часа рождения (时家奇门, «вращающийся диск» 转盘).

Калькулятор написан с нуля. Солнечные термины ищутся через Swiss Ephemeris
(`common.ephemeris.find_sun_longitude`) в UT; шестидесятеричная арифметика (столп дня,
пять крыс, ветвь часа) берётся из `calculators.bazi`, чтобы столпы совпадали с модулем 01.
Сторонние библиотеки (kinqimen, qimen-dunjia) используются ТОЛЬКО для сверки — их выводы
зафиксированы в тестах как константы.

Умолчания (подробно — knowledge-base/16-qimen-dunjia.md):
* ju_method='chaibu' (拆补法): термин — тот, что действует в момент рождения (точный момент
  прохождения Солнцем 15°-ной отметки, UT); юань (上/中/下元) — по «голове знака» (符头) дня:
  последний день 甲 или 己; его ветвь 子午卯酉 → 上元, 寅申巳亥 → 中元, 辰戌丑未 → 下元.
  Альтернативы: 'zhirun' (置闰法: 超神/接气/置闰 по 《奇门遁甲统宗》, 《遁甲演义》,
  黄宗羲 《易学象数论》) и 'maoshan' (茅山法: 5 суток от момента термина = один юань).
* Земной диск: 戊己庚辛壬癸丁丙乙 по дворцам Ло Шу, 阳遁 — вперёд от дворца № 局, 阴遁 — назад.
* 值符 (звезда-командир) — звезда дворца, где на земном диске стоит «ствол-укрытие» 甲 часа
  (旬首仪); она переносится во дворец ствола часа, остальные 7 звёзд — по кругу (всегда
  по часовой стрелке: 1→8→3→4→9→2→7→6). 值使 (дверь-посланник) — дверь того же дворца;
  она сдвигается на столько дворцов (по числам Ло Шу, вперёд в 阳遁 / назад в 阴遁),
  сколько часов прошло от начала декады (旬) часа.
* 天禽 (звезда центра) «гостит» в 坤-2 и движется вместе с 天芮 (tianqin='kun', 《统宗》:
  «天禽阳遁阴遁俱寄坤宫»); вариант 'kun_gen': в 阴遁 гостит в 艮-8 («一本…阴遁寄艮宫»).
* Восемь духов (八神): deities='baihu' — 值符 腾蛇 太阴 六合 白虎 玄武 九地 九天
  (《遁甲演义》, пример 《御定奇门宝鉴》), 'gouchen' — 勾陈/朱雀 вместо 白虎/玄武
  (《奇门遁甲统宗》, 黄宗羲), 'split' — 阳遁 勾陈/朱雀, 阴遁 白虎/玄武 (kinqimen 0.0.6.6,
  qimen-dunjia). 阳遁 — по часовой стрелке, 阴遁 — против.
* Время карты (день, час) — как в модуле 01: solar_time='true' | 'mean' | 'clock'.
  zi_hour='early' (по умолчанию ЗДЕСЬ, в отличие от Ба-цзы): с 23:00 начинается следующий
  день — так считают kinqimen, qimen-dunjia, bigfishmarquis-qimen; при этом 60 часов
  юаня (甲子…癸亥) непрерывны. 'late' — как в модуле 01 (день меняется в полночь).

Опции (не меняют умолчаний; подробно — §1.3 базы знаний):
* qi='ding' (定气, по умолчанию) | 'ping' (平气 по константам 授时历/大统历: 岁实 365,2425 сут,
  气应 55,06 от 冬至 1280 г., без 消长 — так считал 大统历 1368–1644; совпадает с датами
  терминов 《遁甲演义》, 黄宗羲 и 《明史》 до 时辰).
* ju_method='hybrid' — 置闰 + 拆补 в фазе 接气 (殘局/補局: 《遁甲演义》 1596 г., 李氏 в 《宝鉴》);
  'yinpan' — 局 школы 阴盘 王凤麟: (ветвь года + лунный месяц + лунный день + ветвь часа) mod 9.
* term_boundary='moment' (по умолчанию) | 'hour' — весь 时辰, в котором наступил термин,
  относится к новому термину («丙子日…自丑時…借立春下局», 《遁甲演义》; 李氏 в 《宝鉴》).
* hidden_stems='luoshu' (暗干 как kinqimen 0.3.1) | 'ring' (隐干 王凤麟: ствол часа в дворец 值使,
  далее по кругу — порядок небесного диска); по умолчанию 'ring' только при ju_method='yinpan'.
"""
from __future__ import annotations

from dataclasses import replace
from datetime import date, datetime, timedelta, timezone
from zoneinfo import ZoneInfo

import swisseph as swe

from calculators.bazi import (
    BRANCHES,
    STEMS,
    day_index,
    ganzhi,
    ganzhi_index,
    hour_branch,
    li_chun_jd,
    month_first_stem,
    month_slot,
    year_index,
    zi_first_stem,
)
from calculators.common.ephemeris import find_sun_longitude, sun_longitude
from calculators.common.time import (
    BirthInput,
    fmt_offset,
    jd_to_utc,
    local_mean_time,
    normalize,
    true_solar_time,
)

# ---------------------------------------------------------------------------
# Справочники
# ---------------------------------------------------------------------------

ELEMENT_RU = {"wood": "Дерево", "fire": "Огонь", "earth": "Земля", "metal": "Металл", "water": "Вода"}
ELEMENT_CN = {"wood": "木", "fire": "火", "earth": "土", "metal": "金", "water": "水"}
ELEMENTS = ["wood", "fire", "earth", "metal", "water"]

# 24 солнечных термина, начиная с 冬至 (долгота Солнца 270°); термин k начинается на (270 + 15k) mod 360.
TERMS = [
    ("冬至", "Дунчжи", "Зимнее солнцестояние"), ("小寒", "Сяохань", "Малые холода"),
    ("大寒", "Дахань", "Большие холода"), ("立春", "Личунь", "Начало весны"),
    ("雨水", "Юйшуй", "Дождевая вода"), ("惊蛰", "Цзинчжэ", "Пробуждение насекомых"),
    ("春分", "Чуньфэнь", "Весеннее равноденствие"), ("清明", "Цинмин", "Чистый свет"),
    ("谷雨", "Гуюй", "Хлебные дожди"), ("立夏", "Лися", "Начало лета"),
    ("小满", "Сяомань", "Малое изобилие"), ("芒种", "Манчжун", "Колошение хлебов"),
    ("夏至", "Сячжи", "Летнее солнцестояние"), ("小暑", "Сяошу", "Малая жара"),
    ("大暑", "Дашу", "Большая жара"), ("立秋", "Лицю", "Начало осени"),
    ("处暑", "Чушу", "Конец жары"), ("白露", "Байлу", "Белые росы"),
    ("秋分", "Цюфэнь", "Осеннее равноденствие"), ("寒露", "Ханьлу", "Холодные росы"),
    ("霜降", "Шуанцзян", "Выпадение инея"), ("立冬", "Лидун", "Начало зимы"),
    ("小雪", "Сяосюэ", "Малые снега"), ("大雪", "Дасюэ", "Большие снега"),
]

# Номера 局 (上元, 中元, 下元) для каждого термина — стихи «冬至惊蛰一七四…» / «夏至白露九三六…»
# (сверено: kinqimen config.jieqicode, qimen-dunjia README «節氣局數表», bigfishmarquis-qimen).
JU_TABLE: list[tuple[int, int, int]] = [
    (1, 7, 4), (2, 8, 5), (3, 9, 6), (8, 5, 2), (9, 6, 3), (1, 7, 4),   # 冬至 小寒 大寒 立春 雨水 惊蛰
    (3, 9, 6), (4, 1, 7), (5, 2, 8), (4, 1, 7), (5, 2, 8), (6, 3, 9),   # 春分 清明 谷雨 立夏 小满 芒种
    (9, 3, 6), (8, 2, 5), (7, 1, 4), (2, 5, 8), (1, 4, 7), (9, 3, 6),   # 夏至 小暑 大暑 立秋 处暑 白露
    (7, 1, 4), (6, 9, 3), (5, 8, 2), (6, 9, 3), (5, 8, 2), (4, 7, 1),   # 秋分 寒露 霜降 立冬 小雪 大雪
]
YUAN = [("upper", "上元", "верхний"), ("middle", "中元", "средний"), ("lower", "下元", "нижний")]


def term_deg(k: int) -> float:
    return float((270 + 15 * k) % 360)


def term_is_yang(k: int) -> bool:
    """冬至 … 芒种 (k = 0…11) — 阳遁, 夏至 … 大雪 (k = 12…23) — 阴遁."""
    return (k % 24) < 12


# Девять дворцов Ло Шу: номер → (триграмма, чтение, сторона света, элемент).
PALACES: dict[int, tuple[str, str, str, str]] = {
    1: ("坎", "Кань", "север", "water"),
    2: ("坤", "Кунь", "юго-запад", "earth"),
    3: ("震", "Чжэнь", "восток", "wood"),
    4: ("巽", "Сюнь", "юго-восток", "wood"),
    5: ("中", "Центр", "центр", "earth"),
    6: ("乾", "Цянь", "северо-запад", "metal"),
    7: ("兑", "Дуй", "запад", "metal"),
    8: ("艮", "Гэнь", "северо-восток", "earth"),
    9: ("离", "Ли", "юг", "fire"),
}
# Круг восьми внешних дворцов по часовой стрелке (юг сверху): 坎1 艮8 震3 巽4 离9 坤2 兑7 乾6.
RING = [1, 8, 3, 4, 9, 2, 7, 6]
# Сетка для показа (юг сверху, как в китайских картах): 巽4 离9 坤2 / 震3 中5 兑7 / 艮8 坎1 乾6.
GRID = [[4, 9, 2], [3, 5, 7], [8, 1, 6]]
# Ветви по дворцам (для 空亡 и 驿马).
BRANCH_PALACE = {0: 1, 1: 8, 2: 8, 3: 3, 4: 4, 5: 4, 6: 9, 7: 2, 8: 2, 9: 7, 10: 6, 11: 6}

# Девять звёзд по «домашнему» дворцу: (иероглиф, чтение, элемент, полярность, оценка по 《烟波钓叟歌》).
# Элементы: «坎蓬水星離英火，中宮坤艮土為營。乾兌為金震巽木»; полярность: «蓬任衝輔禽陽星，英芮柱心陰宿名»;
# оценка: «輔禽心星為上吉，冲任小吉未全亨。大凶蓬芮不堪使，小凶英柱不精明».
STARS: dict[int, tuple[str, str, str, str, str]] = {
    1: ("天蓬", "Тяньпэн", "water", "yang", "大凶"),
    2: ("天芮", "Тяньжуй", "earth", "yin", "大凶"),
    3: ("天冲", "Тяньчун", "wood", "yang", "小吉"),
    4: ("天辅", "Тяньфу", "wood", "yang", "上吉"),
    5: ("天禽", "Тяньцинь", "earth", "yang", "上吉"),
    6: ("天心", "Тяньсинь", "metal", "yin", "上吉"),
    7: ("天柱", "Тяньчжу", "metal", "yin", "小凶"),
    8: ("天任", "Тяньжэнь", "earth", "yang", "小吉"),
    9: ("天英", "Тяньин", "fire", "yin", "小凶"),
}
VERDICT_RU = {"上吉": "высший благоприятный", "小吉": "малый благоприятный", "大凶": "большой неблагоприятный",
              "小凶": "малый неблагоприятный", "吉": "благоприятная", "凶": "неблагоприятная", "平": "средняя"}

# Восемь дверей (八门) по «домашнему» дворцу: (иероглиф, чтение, перевод, элемент, оценка).
# Элементы — 《奇门遁甲统宗》 卷十二 («休門屬水…生門屬土…傷門屬木…杜門屬木…景門屬火…死門屬土…
# 驚門屬金…開門屬金»); оценка — zh.wikipedia «奇门遁甲»: «开、休、生为三吉门。死、惊、伤为三凶门。
# 杜门、景门为二中平门».
DOORS: dict[int, tuple[str, str, str, str, str]] = {
    1: ("休门", "Сю", "Отдых", "water", "吉"),
    8: ("生门", "Шэн", "Жизнь (Рождение)", "earth", "吉"),
    3: ("伤门", "Шан", "Ранение", "wood", "凶"),
    4: ("杜门", "Ду", "Преграда (Затвор)", "wood", "平"),
    9: ("景门", "Цзин (jǐng)", "Вид (Пейзаж, Свет)", "fire", "平"),
    2: ("死门", "Сы", "Смерть", "earth", "凶"),
    7: ("惊门", "Цзин (jīng)", "Испуг", "metal", "凶"),
    6: ("开门", "Кай", "Открытие", "metal", "吉"),
}

DEITY_RU = {
    "值符": ("Чжифу", "Глава (Командир)"), "腾蛇": ("Тэншэ", "Летучий змей"),
    "太阴": ("Тайинь", "Великая Инь"), "六合": ("Люхэ", "Шесть союзов"),
    "白虎": ("Байху", "Белый тигр"), "玄武": ("Сюаньу", "Сокровенный воин (Чёрная черепаха)"),
    "勾陈": ("Гоучэнь", "Изогнутый строй"), "朱雀": ("Чжуцюэ", "Красная птица"),
    "九地": ("Цзюди", "Девять земель"), "九天": ("Цзютянь", "Девять небес"),
}
DEITIES_BAIHU = ["值符", "腾蛇", "太阴", "六合", "白虎", "玄武", "九地", "九天"]
DEITIES_GOUCHEN = ["值符", "腾蛇", "太阴", "六合", "勾陈", "朱雀", "九地", "九天"]

# Порядок «шести церемониалов и трёх чудес» (六仪三奇) на земном диске: 戊己庚辛壬癸丁丙乙.
STEM_ORDER = [4, 5, 6, 7, 8, 9, 3, 2, 1]
# 甲 «прячется» под церемониалом своей декады: 甲子→戊, 甲戌→己, 甲申→庚, 甲午→辛, 甲辰→壬, 甲寅→癸.
XUN_YI = [4, 5, 6, 7, 8, 9]
# 六仪击刑 (《烟波钓叟歌》: «甲子值符愁向東。戌刑未上申刑虎，寅巳辰辰午刑午»): церемониал в дворце.
JI_XING = {4: 3, 5: 2, 6: 8, 7: 9, 8: 4, 9: 4}
# 驿马 по тройке ветви часа (《三命通会》 «论驿马»: 申子辰→寅, 寅午戌→申, 巳酉丑→亥, 亥卯未→巳).
HORSE = {8: 2, 0: 2, 4: 2, 2: 8, 6: 8, 10: 8, 5: 11, 9: 11, 1: 11, 11: 5, 3: 5, 7: 5}

# 三奇入墓 (небесный диск): основное правило — 乙→坤2, 丙→乾6, 丁→艮8 (《统宗》 «奇门四十格»: «三奇入墓
# 乙奇坤宫 丙奇乾宫 丁奇艮宫»; 《统宗》: «乙未到坤，丙奇到乾，丁奇到艮»; 《遁甲演义》 (王璋): «六乙日奇下临二宫，
# 六丙月奇到六宫，六丁星奇下临八宫»). Варианты: 乙→乾6 (《烟波钓叟歌》 «更兼乙奇來臨六», 《统宗》 «乙丙到乾为墓»),
# 丁→乾6 (《统宗》 «乙木到坤、丙丁火到乾，皆为入墓»).
SAN_QI_MU = {1: 2, 2: 6, 3: 8}
SAN_QI_MU_VARIANT = {1: 6, 3: 6}

JU_METHODS = ("chaibu", "zhirun", "maoshan")               # три классических счёта (alternatives.ju_methods)
JU_METHODS_EXTRA = ("hybrid", "yinpan")                    # опции (alternatives.ju_methods_extra)
JU_METHOD_RU = {
    "chaibu": "拆补法 (термин — по моменту, юань — по 符头 дня)",
    "zhirun": "置闰法 (超神/接气/置闰, юань — по 符头, ju меняется только на 符头)",
    "maoshan": "茅山法 (юань — 5 суток от момента термина)",
    "hybrid": "置闰 + 拆补 в фазе 接气 (《遁甲演义》, 李氏: 殘局/補局 — новый термин с момента, 下元 до 符头)",
    "yinpan": "阴盘 王凤麟 (局 = (ветвь года + лунный месяц + лунный день + ветвь часа) mod 9; 冬至→夏至 阳)",
}

# 平气 (恒气) по 授时历/大统历. 《元史·历志·授时历经》: «至元十八年岁次辛巳为元…岁实，三百六十五万二千四百二十五分…
# 气应，五十五万六百分…其日命甲子算外，即所求天正冬至日辰及分» (日周 = 10000 分): 冬至 1280 г. — день 己未
# (JDN 2188926) + 0,06 сут. 《明史·历志一》: 元统 «取《授时历》，去其岁实消长之说» (大统历), «平节气者，以一岁之实，
# 二十四平分之». Время — местное среднее 大都/北京 (116,4° в. д.). Проверка: 《明史》 «推壬申冬至，《大统》得己亥寅正
# 一刻» → модель: 己亥 04:16; даты терминов 《遁甲演义》 1596–1601 и 黄宗羲 1589 — до 时辰 (тест).
SHOUSHI_EPOCH_LOCAL_JD = 2188926 - 0.5 + 0.06
SHOUSHI_YEAR = 365.2425
SHOUSHI_LON = 116.4
QI_LEN = SHOUSHI_YEAR / 24.0


# ---------------------------------------------------------------------------
# Вспомогательные функции
# ---------------------------------------------------------------------------


def stem_element(s: int) -> str:
    return ELEMENTS[s // 2]


def _palace_brief(p: int) -> str:
    return f"{PALACES[p][0]}{p}"


def _iso(dt: datetime) -> str:
    return dt.replace(microsecond=0).isoformat()


def _jd_iso_utc(jd: float) -> str:
    return _iso(jd_to_utc(jd).astimezone(timezone.utc)).replace("+00:00", "Z")


def earth_plate(yang: bool, ju: int) -> dict[int, int]:
    """Земной диск: дворец → ствол. 戊 стоит в дворце № ju, далее 己庚辛壬癸丁丙乙 вперёд (阳) / назад (阴)."""
    out: dict[int, int] = {}
    for i, s in enumerate(STEM_ORDER):
        p = ((ju - 1 + i) % 9) + 1 if yang else ((ju - 1 - i) % 9) + 1
        out[p] = s
    return out


def yuan_by_futou(day_idx: int) -> int:
    """Юань по «голове знака» (符头) дня: 0 上, 1 中, 2 下. Блоки по 5 дней от 甲子: (i // 5) mod 3."""
    return (day_idx // 5) % 3


def futou_index(day_idx: int) -> int:
    """Индекс дня-符头 (последний 甲 или 己 день, включая сам день)."""
    return day_idx - (day_idx % 10) % 5


def term_index_at(jd: float) -> int:
    """Номер термина (0 = 冬至 … 23 = 大雪), действующего в момент jd (UT)."""
    lam = sun_longitude(jd)
    return int(((lam - 270.0) % 360.0) // 15.0) % 24


def _jd_noon(d: date) -> float:
    return swe.julday(d.year, d.month, d.day, 12.0, swe.GREG_CAL)


class _Terms:
    """Моменты начала терминов (JD UT): qi='ding' — истинные (定气, долгота Солнца 15k°, эфемерида);
    qi='ping' — средние (平气) по константам 授时历/大统历 (равные доли 365,2425/24 сут от 冬至 1280 г.)."""

    def __init__(self, qi: str = "ding"):
        self.qi = qi

    def _x(self, jd: float) -> float:
        """Номер «平气-термина» от эпохи (дробный): 0 = 冬至 1280 г."""
        return (jd + SHOUSHI_LON / 360.0 - SHOUSHI_EPOCH_LOCAL_JD) / QI_LEN

    @staticmethod
    def _jd_of(i: int) -> float:
        return SHOUSHI_EPOCH_LOCAL_JD + i * QI_LEN - SHOUSHI_LON / 360.0

    def index_at(self, jd: float) -> int:
        """Номер термина (0 = 冬至 … 23 = 大雪), действующего в момент jd."""
        if self.qi == "ping":
            return int(self._x(jd) // 1) % 24
        return term_index_at(jd)

    def start_before(self, k: int, jd: float) -> float:
        """Последнее начало термина k не позже jd."""
        if self.qi == "ping":
            i = int(self._x(jd) // 1)
            i -= (i - k) % 24
            return self._jd_of(i)
        return find_sun_longitude(term_deg(k), jd, search_back=True)

    def start_after(self, k: int, jd: float) -> float:
        """Первое начало термина k позже jd."""
        if self.qi == "ping":
            i = int(self._x(jd) // 1) + 1
            i += (k - i) % 24
            return self._jd_of(i)
        return find_sun_longitude(term_deg(k), jd, search_back=False)


_TERMS_DING = _Terms("ding")


def term_start(k: int, jd: float, qi: str = "ding") -> float:
    """Начало термина k (JD UT), последнее не позже jd; qi='ding' | 'ping'."""
    return _Terms(qi).start_before(k, jd)


def _jd_for_term(jd: float, chart_t: datetime | None, term_boundary: str) -> float:
    """Момент, по которому решается «наступил ли термин»: сам момент или конец его 时辰 (term_boundary='hour')."""
    if term_boundary != "hour" or chart_t is None:
        return jd
    mins = chart_t.hour * 60 + chart_t.minute + chart_t.second / 60.0
    end = ((mins + 60) // 120) * 120 + 60                    # конец двухчасовки: 01:00, 03:00, …, 25:00
    return jd + (end - mins) / 1440.0 - 1e-7


# ---------------------------------------------------------------------------
# Время карты
# ---------------------------------------------------------------------------


class _Clock:
    """Пересчёт момента UT в «время карты» выбранной шкалы (для дат терминов и рождения)."""

    def __init__(self, tz: str, offset_source: str, offset_h: float, lon: float | None, mode: str):
        self.mode = mode
        self.lon = lon
        self.offset_h = offset_h
        self.zone = ZoneInfo(tz) if offset_source == "tzdb" else None

    def civil(self, utc: datetime) -> datetime:
        if self.zone is not None:
            return utc.astimezone(self.zone).replace(tzinfo=None)
        return (utc + timedelta(hours=self.offset_h)).replace(tzinfo=None)

    def chart(self, utc: datetime) -> datetime:
        if self.mode == "clock" or self.lon is None:
            return self.civil(utc)
        if self.mode == "mean":
            return local_mean_time(utc, self.lon)
        return true_solar_time(utc, self.lon)

    def chart_jd(self, jd: float) -> datetime:
        return self.chart(jd_to_utc(jd).astimezone(timezone.utc))


def chart_day(chart_t: datetime, zi_hour: str) -> date:
    """Дата, по которой берётся столп дня: с 23:00 — следующая при zi_hour='early'."""
    d = chart_t.date()
    if zi_hour == "early" and chart_t.hour == 23:
        d += timedelta(days=1)
    return d


def hour_pillar(chart_t: datetime) -> int:
    """Столп часа (индекс 0…59). После 23:00 ствол — по следующему дню (в обеих школах, как в модуле 01)."""
    minutes = chart_t.hour * 60 + chart_t.minute + chart_t.second / 60.0
    hb = hour_branch(minutes)
    stem_day = day_index(chart_t.date() + timedelta(days=1 if chart_t.hour == 23 else 0)) % 10
    hs = (zi_first_stem(stem_day) + hb) % 10
    return ganzhi_index(hs, hb)


# ---------------------------------------------------------------------------
# Определение 局
# ---------------------------------------------------------------------------


def ju_chaibu(jd: float, day_idx: int, terms: _Terms | None = None) -> dict:
    k = (terms or _TERMS_DING).index_at(jd)
    y = yuan_by_futou(day_idx)
    return {"term": k, "yuan": y, "leap": False}


def ju_maoshan(jd: float, terms: _Terms | None = None, jd_term: float | None = None) -> dict:
    """茅山法. jd_term — момент для выбора термина (при term_boundary='hour' — конец 时辰)."""
    T = terms or _TERMS_DING
    jt = jd if jd_term is None else jd_term
    k = T.index_at(jt)
    t0 = T.start_before(k, jt + 1e-6)
    elapsed = max(0.0, jd - t0)
    y = min(2, int(elapsed // 5.0))
    return {"term": k, "yuan": y, "leap": False, "elapsed_days": elapsed, "term_jd": t0}


def _zhirun_upper_futou(z_day: date, leap_days: int) -> date:
    """Верхний 符头 (甲子/己卯/甲午/己酉) для солнцестояния: z_day − F ∈ [leap_days − 15, leap_days)."""
    start = z_day - timedelta(days=leap_days - 1)
    for k in range(15):
        d = start + timedelta(days=k)
        if day_index(d) % 15 == 0:
            return d
    raise RuntimeError("Не найден верхний 符头 в пределах 15 дней")  # pragma: no cover


def ju_zhirun(d_chart: date, jd_ref: float, clock: _Clock, leap_days: int = 8,
              terms: _Terms | None = None) -> dict:
    """置闰法: 15-дневные блоки от верхних 符头; каждый блок — следующий термин; если 符头 блока,
    который должен открыть 夏至/冬至, отстоит от солнцестояния на ≥ leap_days дней раньше
    (超神), блок повторяет 芒种/大雪 (闰奇), и солнцестояние начинается на 15 дней позже.

    d_chart — дата столпа дня рождения; даты терминов — по той же шкале времени карты
    (календарная дата момента термина, без правила zi_hour: так датирует 《统宗》 夏至 1717 г.
    «五月十三日丙寅夜子初二刻» и считает от него «已超三日»).
    """
    T = terms or _TERMS_DING

    def term_day(jd: float) -> date:
        return clock.chart_jd(jd).date()

    probe = _jd_noon(d_chart) + 20.0
    z0, z12 = T.start_before(0, probe), T.start_before(12, probe)
    z_jd, base_k = (z0, 0) if z0 > z12 else (z12, 12)
    for _ in range(4):
        f = _zhirun_upper_futou(term_day(z_jd), leap_days)
        if f <= d_chart:
            break
        base_k = 12 - base_k
        z_jd = T.start_before(base_k, z_jd - 1.0)
    else:  # pragma: no cover
        raise RuntimeError("置闰法: не удалось найти блок")
    delta = (d_chart - f).days
    n, within = divmod(delta, 15)
    yuan = within // 5
    leap = n >= 12
    k = base_k + (11 if leap else n)
    block_start = f + timedelta(days=15 * n)
    # Состояние: разность дат термина и верхнего 符头 его блока (>0 超神, <0 接气, 0 正授).
    if leap:
        nxt = T.start_before((base_k + 12) % 24, _jd_noon(block_start) + 20.0)
        chao = (term_day(nxt) - block_start).days
        state = "leap"
    else:
        t_jd = T.start_before(k % 24, _jd_noon(block_start) + 20.0)
        chao = (term_day(t_jd) - block_start).days
        state = "chaoshen" if chao > 0 else ("jieqi" if chao < 0 else "zhengshou")
    return {"term": k % 24, "yuan": yuan, "leap": leap, "block_start": block_start.isoformat(),
            "solstice_futou": f.isoformat(), "solstice": TERMS[base_k][0], "state": state,
            "chao_days": chao, "leap_days": leap_days}


def ju_hybrid(jd_t: float, d_chart: date, clock: _Clock, leap_days: int = 8, terms: _Terms | None = None) -> dict:
    """«Гибрид» 《遁甲演义》 / 李氏 (《御定奇门宝鉴》 «辨三氏奇门»): цепочка 置闰法 (超神, 正授, 闰奇 — как в
    ju_zhirun), но в фазе 接气 термин вступает с момента своего наступления: от момента термина до верхнего
    符头 его блока — 下元 нового термина (殘局: «拆補之局，永為下之殘局，必待符頭先到日，方為某節某氣上局»);
    недостающие часы 下元 добираются в конце блока (補局 — совпадает с 置闰). Внутри блока 闰奇 солнцестояние
    殘局 не открывает («借夏至七日», 《演义》 1346 г.).

    jd_t — момент, по которому решается наступление термина (при term_boundary='hour' — конец 时辰).
    """
    T = terms or _TERMS_DING
    zr = ju_zhirun(d_chart, jd_t, clock, leap_days, T)
    out = dict(zr)
    out["canju"] = False
    if zr["leap"]:
        return out
    b = date.fromisoformat(zr["block_start"])
    nb = b + timedelta(days=15)
    nxt = ju_zhirun(nb, jd_t, clock, leap_days, T)
    if nxt["leap"]:
        return out
    k_next = nxt["term"]
    t = T.start_before(k_next, jd_t)
    t_day = clock.chart_jd(t).date()
    if jd_t >= t and t_day >= b:
        out.update({"term": k_next, "yuan": 2, "state": "canju", "canju": True,
                    "chao_days": (t_day - nb).days, "canju_term_utc": _jd_iso_utc(t),
                    "canju_block_start": nb.isoformat()})
    return out


def ju_yinpan(jd_t: float, d_chart: date, hour_idx: int, terms: _Terms | None = None,
              year_branch_lichun: int | None = None) -> dict:
    """局 школы 阴盘 (王凤麟, «2009年第二套阴盘奇门遁甲移星换斗实战实例精解», гл. 2 «定局»):
    «阳遁: 冬至后夏至前…阴遁: 夏至后冬至前. 局数取(年支序数+月数+日数+时支序数)除9之余数» (子 = 1 … 亥 = 12;
    остаток 0 → 9). Лунная дата — китайский календарь (UTC+8) для даты столпа дня; ветвь года — лунного
    года (⚠ в книге не уточнено: лунный год или год по Личуню; второй вариант — в ju_lichun_year).
    """
    from lunar_python import Solar

    T = terms or _TERMS_DING
    k = T.index_at(jd_t)
    yang = term_is_yang(k)
    lun = Solar.fromYmd(d_chart.year, d_chart.month, d_chart.day).getLunar()
    zhi = [BRANCHES[i][0] for i in range(12)]
    yb = zhi.index(lun.getYearZhi()) + 1
    m = abs(lun.getMonth())
    dd = lun.getDay()
    hb = hour_idx % 12 + 1
    n = (yb + m + dd + hb) % 9 or 9
    out = {"term": k, "yuan": None, "leap": False, "yinpan": True, "yang": yang, "ju": n,
           "lunar": {"year_branch": zhi[yb - 1], "month": m, "leap_month": lun.getMonth() < 0, "day": dd,
                     "hour_branch": zhi[hb - 1], "sum": yb + m + dd + hb}}
    if year_branch_lichun is not None and year_branch_lichun + 1 != yb:
        out["ju_lichun_year"] = (year_branch_lichun + 1 + m + dd + hb) % 9 or 9
    return out


STATE_RU = {"chaoshen": "超神 (符头 пришёл раньше термина — «опережение»)",
            "jieqi": "接气 (термин пришёл раньше 符头 — «подхват»)",
            "zhengshou": "正授 (符头 и термин в один день)",
            "leap": "闰奇 (вставной повтор 芒种/大雪)",
            "canju": "殘局 (拆补 в фазе 接气: термин уже наступил, его 符头 ещё нет — 下元 нового термина)"}


# ---------------------------------------------------------------------------
# Построение карты
# ---------------------------------------------------------------------------


def build_chart(yang: bool, ju: int, hour_idx: int, tianqin: str = "kun", deities: str = "baihu",
                hidden_rule: str = "luoshu") -> dict:
    """Расставить земной и небесный диски, звёзды, двери, духов для 局 и столпа часа."""
    earth = earth_plate(yang, ju)
    stem_palace = {s: p for p, s in earth.items()}
    jg = 2 if (tianqin == "kun" or yang) else 8           # дворец, где «гостит» 天禽
    xun_n = hour_idx // 10
    xun_head = xun_n * 10
    yi = XUN_YI[xun_n]
    pos = hour_idx % 10                                    # номер часа в декаде (0 = час 甲)
    hs = hour_idx % 10
    eff = yi if hs == 0 else hs                            # ствол часа (甲 → его церемониал)
    p0 = stem_palace[yi]                                   # дворец 旬首 на земном диске
    t_raw = stem_palace[eff]
    t = jg if t_raw == 5 else t_raw                        # дворец, куда идёт 值符
    s = jg if p0 == 5 else p0
    off = (RING.index(t) - RING.index(s)) % 8
    star_at: dict[int, list[int]] = {}
    for h in RING:
        star_at.setdefault(RING[(RING.index(h) + off) % 8], []).append(h)
    jg_star_palace = RING[(RING.index(jg) + off) % 8]
    star_at[jg_star_palace].append(5)
    # двери
    d_raw = ((p0 - 1 + pos) % 9) + 1 if yang else ((p0 - 1 - pos) % 9) + 1
    d = jg if d_raw == 5 else d_raw
    door_src = jg if p0 == 5 else p0
    offd = (RING.index(d) - RING.index(door_src)) % 8
    door_at = {RING[(RING.index(h) + offd) % 8]: h for h in RING}
    # духи
    if deities == "gouchen" or (deities == "split" and yang):
        names = DEITIES_GOUCHEN
    else:
        names = DEITIES_BAIHU
    ring_from = RING.index(t)
    deity_at = {}
    for i, nm in enumerate(names):
        p = RING[(ring_from + i) % 8] if yang else RING[(ring_from - i) % 8]
        deity_at[p] = nm
    heaven = {p: [earth[h] for h in homes] for p, homes in star_at.items()}
    # скрытые стволы (暗干/隐干) — современные правила, в классике (《统宗》, 《宝鉴》, 《演义》) не найдены:
    # 'luoshu' — kinqimen TS 0.3.1: ствол часа во дворец 值使 (до «гостевой» поправки; если он совпал с дворцом
    #   ствола часа — в центр), далее 戊己庚辛壬癸丁丙乙 по числам Ло Шу вперёд (阳) / назад (阴);
    # 'ring' — 王凤麟 (阴盘): «时干加在值使门上，然后按照天盘的顺序…排列一圈» — небесный диск, повёрнутый по
    #   кругу так, чтобы ствол часа оказался во дворце 值使 (центр без скрытого ствола).
    start_p = 5 if d_raw == t_raw else d_raw
    hidden: dict[int, list[int]] = {}
    if hidden_rule == "ring":
        hs_heaven = next(p for p, ss in heaven.items() if eff in ss)
        offh = (RING.index(d) - RING.index(hs_heaven)) % 8
        for p in RING:
            hidden[RING[(RING.index(p) + offh) % 8]] = list(heaven[p])
        hidden[5] = []
    else:
        k0 = STEM_ORDER.index(eff)
        for i in range(9):
            p = ((start_p - 1 + i) % 9) + 1 if yang else ((start_p - 1 - i) % 9) + 1
            hidden[p] = [STEM_ORDER[(k0 + i) % 9]]
    return {
        "earth": earth, "heaven": heaven, "star_at": star_at, "door_at": door_at, "deity_at": deity_at,
        "hidden": hidden, "ji_gong": jg, "xun_head": xun_head, "xun_yi": yi, "pos": pos, "eff_stem": eff,
        "p0": p0, "t_raw": t_raw, "t": t, "star_offset": off, "door_raw": d_raw, "door": d,
        "door_offset": offd, "door_src": door_src, "deity_names": names, "hidden_start": start_p,
        "hidden_rule": hidden_rule,
    }


def _stem_brief(s: int) -> dict:
    return {"cn": STEMS[s][0], "ru": STEMS[s][2], "element": stem_element(s)}


def _relation(year_stem: int, other: int) -> tuple[str, str]:
    """Шесть родственных связей ствола относительно ствола года (《统宗》 卷十二)."""
    a = ELEMENTS.index(stem_element(year_stem))
    b = ELEMENTS.index(stem_element(other))
    d = (b - a) % 5
    return {0: ("兄弟", "братья/сёстры (比肩)"), 1: ("子孙", "дети (我生)"), 2: ("妻财", "жена/богатство (我克)"),
            3: ("官禄疾厄", "служба/болезни (克我)"), 4: ("父母", "родители (生我)")}[d]


def _patterns(ch: dict) -> dict:
    out: dict = {}
    out["star_fuyin"] = ch["star_offset"] == 0
    out["star_fanyin"] = ch["star_offset"] == 4
    out["door_fuyin"] = ch["door_offset"] == 0
    out["door_fanyin"] = ch["door_offset"] == 4
    ji = []
    for p, stems in ch["heaven"].items():
        for s in stems:
            if JI_XING.get(s) == p:
                ji.append({"stem": STEMS[s][0], "palace": p, "trigram": PALACES[p][0]})
    out["ji_xing"] = ji
    mp = []
    for p, h in ch["door_at"].items():
        de = ELEMENTS.index(DOORS[h][3])
        pe = ELEMENTS.index(PALACES[p][3])
        if (pe - de) % 5 == 2:          # дверь контролирует (克) дворец
            mp.append({"door": DOORS[h][0], "palace": p, "trigram": PALACES[p][0]})
    out["men_po"] = mp
    # 三奇入墓 — по небесному диску («三奇墓者．謂六乙日奇下臨二宮…», 《遁甲演義》)
    mu, mu_var = [], []
    for p, stems in ch["heaven"].items():
        for s in stems:
            if SAN_QI_MU.get(s) == p:
                mu.append({"stem": STEMS[s][0], "palace": p, "trigram": PALACES[p][0]})
            if SAN_QI_MU_VARIANT.get(s) == p:
                mu_var.append({"stem": STEMS[s][0], "palace": p, "trigram": PALACES[p][0]})
    out["san_qi_ru_mu"] = mu
    out["san_qi_ru_mu_variant"] = mu_var
    return out


def _palaces_out(ch: dict, empty_palaces: set[int], horse_palace: int | None) -> list[dict]:
    res = []
    for p in range(1, 10):
        tri, tri_ru, side, el = PALACES[p]
        item: dict = {"palace": p, "trigram": tri, "trigram_ru": tri_ru, "direction": side,
                      "element": el, "earth_stem": STEMS[ch["earth"][p]][0]}
        if p == 5:
            item.update({"heaven_stems": [], "star": None, "door": None, "deity": None,
                         "note": f"центр: 天禽 и ствол {STEMS[ch['earth'][5]][0]} «гостят» в "
                                 f"{_palace_brief(ch['ji_gong'])} и движутся с его звездой"})
        else:
            homes = ch["star_at"][p]
            item["heaven_stems"] = [STEMS[s][0] for s in ch["heaven"][p]]
            item["star"] = STARS[homes[0]][0]
            item["star_home"] = homes[0]
            if 5 in homes:
                item["star_guest"] = "天禽"
            dh = ch["door_at"][p]
            item["door"] = DOORS[dh][0]
            item["door_home"] = dh
            item["deity"] = ch["deity_at"][p]
        hs = ch["hidden"].get(p) or []
        item["hidden_stem"] = "".join(STEMS[x][0] for x in hs) or None
        flags = []
        if p in empty_palaces:
            flags.append("空亡")
        if p == horse_palace:
            flags.append("驿马")
        if p == ch["t"]:
            flags.append("值符")
        if p == ch["door"]:
            flags.append("值使")
        item["flags"] = flags
        res.append(item)
    return res


def _grid_text(ch: dict) -> list[str]:
    rows = []
    for row in GRID:
        cells = []
        for p in row:
            if p == 5:
                cells.append(f"中5 地{STEMS[ch['earth'][5]][0]}")
            else:
                homes = ch["star_at"][p]
                st = "".join(STARS[h][0][1] for h in homes)
                hv = "".join(STEMS[s][0] for s in ch["heaven"][p])
                cells.append(f"{PALACES[p][0]}{p} {ch['deity_at'][p]} {st} {DOORS[ch['door_at'][p]][0]} "
                             f"天{hv}/地{STEMS[ch['earth'][p]][0]}")
        rows.append(" | ".join(cells))
    return rows


# ---------------------------------------------------------------------------
# Основной расчёт
# ---------------------------------------------------------------------------


def _opt_solar(v) -> str:
    if v is True:
        return "true"
    if v is False:
        return "clock"
    return str(v).strip().lower()


def _determine(method: str, jd: float, d_chart: date, clock: _Clock, leap_days: int,
               terms: _Terms | None = None, chart_t: datetime | None = None, term_boundary: str = "moment",
               hour_idx: int | None = None, year_branch_lichun: int | None = None) -> dict:
    """局 выбранным методом. chart_t нужен для term_boundary='hour', hour_idx — для 'yinpan'."""
    T = terms or _TERMS_DING
    jt = _jd_for_term(jd, chart_t, term_boundary)
    if method == "chaibu":
        return ju_chaibu(jt, day_index(d_chart), T)
    if method == "maoshan":
        return ju_maoshan(jd, T, jt)
    if method == "hybrid":
        return ju_hybrid(jt, d_chart, clock, leap_days, T)
    if method == "yinpan":
        if hour_idx is None:
            hour_idx = hour_pillar(chart_t)
        return ju_yinpan(jt, d_chart, hour_idx, T, year_branch_lichun)
    return ju_zhirun(d_chart, jd, clock, leap_days, T)


def _ju_yang(r: dict) -> bool:
    return r["yang"] if "yang" in r else term_is_yang(r["term"])


def _ju_number(r: dict) -> int:
    return r["ju"] if "ju" in r else JU_TABLE[r["term"]][r["yuan"]]


def _ju_label(r: dict) -> str:
    if r.get("yinpan"):
        return f"{'阳' if r['yang'] else '阴'}遁{r['ju']}局 阴盘"
    k = r["term"]
    yang = term_is_yang(k)
    ju = JU_TABLE[k][r["yuan"]]
    return f"{'阳' if yang else '阴'}遁{ju}局 {TERMS[k][0]}{'闰' if r.get('leap') else ''}{YUAN[r['yuan']][1]}"


def calculate(b: BirthInput, **options) -> dict:
    """Карта Ци Мэнь Дунь Цзя на момент рождения.

    options:
      ju_method: 'chaibu' (по умолч.) | 'zhirun' | 'maoshan';
      solar_time: 'true' (по умолч.) | 'mean' | 'clock';
      zi_hour: 'early' (по умолч.) | 'late';
      tianqin: 'kun' (по умолч.) | 'kun_gen';
      deities: 'baihu' (по умолч.) | 'gouchen' | 'split';
      zhirun_leap_days: порог 超神 для 置闰 в днях-разности (по умолч. 8 = «九日» при счёте включительно);
      qi: 'ding' (по умолч., 定气) | 'ping' (平气 授时历/大统历 — для дат до 1645 г.);
      term_boundary: 'moment' (по умолч.) | 'hour' (时辰 с моментом термина — уже новый термин);
      hidden_stems: 'luoshu' | 'ring' (по умолч. 'luoshu', при ju_method='yinpan' — 'ring').
      ju_method также 'hybrid' (置闰 + 拆补 в 接气) и 'yinpan' (阴盘 王凤麟).
    """
    method = str(options.get("ju_method", "chaibu")).strip().lower()
    solar_time = _opt_solar(options.get("solar_time", "true"))
    zi_hour = str(options.get("zi_hour", "early")).strip().lower()
    tianqin = str(options.get("tianqin", "kun")).strip().lower()
    deities = str(options.get("deities", "baihu")).strip().lower()
    leap_days = int(options.get("zhirun_leap_days", 8))
    qi = str(options.get("qi", "ding")).strip().lower()
    term_boundary = str(options.get("term_boundary", "moment")).strip().lower()
    hidden_rule = str(options.get("hidden_stems", "ring" if method == "yinpan" else "luoshu")).strip().lower()
    if method not in JU_METHODS + JU_METHODS_EXTRA:
        raise ValueError("ju_method: 'chaibu' | 'zhirun' | 'maoshan' | 'hybrid' | 'yinpan'")
    if qi not in ("ding", "ping"):
        raise ValueError("qi: 'ding' | 'ping'")
    if term_boundary not in ("moment", "hour"):
        raise ValueError("term_boundary: 'moment' | 'hour'")
    if hidden_rule not in ("luoshu", "ring"):
        raise ValueError("hidden_stems: 'luoshu' | 'ring'")
    terms = _Terms(qi)
    xopt = {"qi": qi, "term_boundary": term_boundary, "hidden_rule": hidden_rule, "terms": terms}
    if solar_time not in ("true", "mean", "clock"):
        raise ValueError("solar_time: 'true' | 'mean' | 'clock'")
    if zi_hour not in ("early", "late"):
        raise ValueError("zi_hour: 'early' | 'late'")
    if tianqin not in ("kun", "kun_gen"):
        raise ValueError("tianqin: 'kun' | 'kun_gen'")
    if deities not in ("baihu", "gouchen", "split"):
        raise ValueError("deities: 'baihu' | 'gouchen' | 'split'")
    if not 1 <= leap_days <= 14:
        raise ValueError("zhirun_leap_days: 1…14")

    warnings: list[str] = []
    steps: list[str] = []

    def add(msg: str) -> None:
        steps.append(f"Шаг {len(steps) + 1}. {msg}")

    has_time = b.has_time
    if b.tz is None and b.lat is not None and b.lon is not None:
        from calculators.common.places import tz_for_coords
        tzname = tz_for_coords(b.lat, b.lon)
        if tzname:
            b = replace(b, tz=tzname)
            warnings.append(f"Часовой пояс определён по координатам: {tzname}.")
    if b.tz is None:
        if has_time:
            raise ValueError("Не задан часовой пояс (tz) или место — без них нельзя найти момент в UT.")
        b = replace(b, tz="UTC")
        warnings.append("Нет ни времени, ни пояса: термин определён по UTC.")

    if not has_time:
        return _day_level(b, method, solar_time, zi_hour, tianqin, deities, leap_days, warnings, steps, add, **xopt)

    n = normalize(b)
    warnings.extend(n.warnings)
    jd = n.jd_ut
    used_mode = solar_time
    if solar_time != "clock" and b.lon is None:
        warnings.append("Долгота неизвестна — солнечное время не вычислить, использовано время часов.")
        used_mode = "clock"
    clock = _Clock(b.tz, n.offset_source, n.utc_offset_hours, b.lon, used_mode)
    add(f"Местное время {n.local:%d.%m.%Y %H:%M} ({b.tz}, {fmt_offset(n.utc_offset_hours)}, источник: "
        f"{n.offset_source}) → UTC {n.utc:%d.%m.%Y %H:%M:%S}; JD(UT) = {jd:.5f}.")
    chart_t = clock.chart(n.utc)
    mode_ru = {"clock": "время часов", "mean": "местное среднее солнечное (LMT)",
               "true": "истинное солнечное (LMT + уравнение времени)"}[used_mode]
    add(f"Время карты ({mode_ru}): {chart_t:%d.%m.%Y %H:%M:%S}.")

    # --- столпы ---
    y_utc = n.utc.year
    lc = li_chun_jd(y_utc)
    bazi_year = y_utc if jd >= lc else y_utc - 1
    yi_idx = year_index(bazi_year)
    slot = month_slot(sun_longitude(jd))
    mi = ganzhi_index((month_first_stem(yi_idx % 10) + slot) % 10, (slot + 2) % 12)
    d_chart = chart_day(chart_t, zi_hour)
    di = day_index(d_chart)
    hi = hour_pillar(chart_t)
    is23 = chart_t.hour == 23
    add(f"Столпы (как в модуле 01): год {ganzhi(yi_idx)} (Личунь), месяц {ganzhi(mi)}, день {ganzhi(di)} "
        f"(дата {d_chart:%d.%m.%Y}{', 23-й час → следующий день (zi_hour=early)' if is23 and zi_hour == 'early' else ''}), "
        f"час {ganzhi(hi)} (ветвь {BRANCHES[hi % 12][0]}, «пять крыс» от ствола "
        f"{'следующего ' if is23 else ''}дня).")

    # --- термин и 局 ---
    k_now = terms.index_at(jd)
    t_prev = terms.start_before(k_now, jd + 1e-6)
    t_next = terms.start_after((k_now + 1) % 24, jd)
    if qi == "ping":
        add(f"Термины — 平气 (授时历/大统历: 冬至 1280 г. 己未 + 0,06 сут, доля 365,2425/24 сут, местное время "
            f"北京 116,4° в. д.) → действующий термин {TERMS[k_now][0]} ({TERMS[k_now][1]}) с {_jd_iso_utc(t_prev)} UT "
            f"(время карты {clock.chart_jd(t_prev):%d.%m.%Y %H:%M}); следующий {TERMS[(k_now + 1) % 24][0]} — "
            f"{_jd_iso_utc(t_next)} UT. (Истинная долгота Солнца λ = {sun_longitude(jd):.4f}°.)")
    else:
        add(f"Долгота Солнца λ = {sun_longitude(jd):.4f}° → действующий термин {TERMS[k_now][0]} "
            f"({TERMS[k_now][1]}, {term_deg(k_now):.0f}°) с {_jd_iso_utc(t_prev)} UT "
            f"(время карты {clock.chart_jd(t_prev):%d.%m.%Y %H:%M}); следующий {TERMS[(k_now + 1) % 24][0]} — "
            f"{_jd_iso_utc(t_next)} UT.")
    for tj, nm in ((t_prev, TERMS[k_now][0]), (t_next, TERMS[(k_now + 1) % 24][0])):
        if abs(jd - tj) < 1.0:
            warnings.append(f"Рождение в {abs(jd - tj) * 24:.1f} ч от термина {nm}: при ошибке во времени "
                            f"рождения термин (а с ним 局) может смениться.")

    if term_boundary == "hour":
        jt = _jd_for_term(jd, chart_t, term_boundary)
        if terms.index_at(jt) != k_now:
            add(f"term_boundary='hour': термин {TERMS[terms.index_at(jt)][0]} наступает внутри часа рождения "
                f"({_jd_iso_utc(t_next)} UT) — весь 时辰 относится к нему («自丑時…借立春下局», 《遁甲演義》).")
    dctx = {"terms": terms, "chart_t": chart_t, "term_boundary": term_boundary, "hour_idx": hi,
            "year_branch_lichun": yi_idx % 12}
    r = _determine(method, jd, d_chart, clock, leap_days, **dctx)
    k = r["term"]
    yang = _ju_yang(r)
    ju = _ju_number(r)
    fu = futou_index(di)
    if method == "yinpan":
        lu = r["lunar"]
        add(f"阴盘 (王凤麟): {'阳遁 (冬至→夏至)' if yang else '阴遁 (夏至→冬至)'}; лунная дата столпа дня "
            f"{d_chart:%d.%m.%Y} — {lu['year_branch']}年 {'闰' if lu['leap_month'] else ''}{lu['month']}月 {lu['day']}日, "
            f"час {lu['hour_branch']}: ({lu['year_branch']}={[BRANCHES[i][0] for i in range(12)].index(lu['year_branch']) + 1} "
            f"+ {lu['month']} + {lu['day']} + {lu['hour_branch']}={hi % 12 + 1}) = {lu['sum']} → mod 9 = {ju} → "
            f"{'阳' if yang else '阴'}遁{ju}局. Раскладка дисков, звёзд, дверей и духов — как в 转盘 (пример книги "
            f"2006-05-23 19:45 совпадает клетка в клетку).")
        if lu["leap_month"]:
            warnings.append("阴盘: лунный месяц високосный (闰) — взят его номер; правило для 闰月 в источнике не дано ⚠.")
        if "ju_lichun_year" in r:
            warnings.append(f"阴盘: ветвь лунного года и года по Личуню различаются; по году Личуня — "
                            f"{'阳' if yang else '阴'}遁{r['ju_lichun_year']}局 (в источнике не уточнено ⚠).")
        if chart_t.hour == 23:
            warnings.append("阴盘: час 23:00–24:00 — лунный день взят по дате столпа дня (zi_hour); источник этот "
                            "случай не разбирает ⚠.")
        if abs(n.utc_offset_hours - 8.0) > 1e-6:
            try:
                from lunar_python import Solar as _S
                from calculators.ziwei import _check_new_moon_timezone
                wmsg = _check_new_moon_timezone(_S.fromYmd(d_chart.year, d_chart.month, d_chart.day).getLunar(),
                                                d_chart, n.utc_offset_hours)
                if wmsg:
                    warnings.append("阴盘: " + wmsg)
            except Exception:  # pragma: no cover
                pass
    elif method == "chaibu":
        add(f"拆补法: термин {TERMS[k][0]}. 符头 дня {ganzhi(di)} = последний день 甲/己 = {ganzhi(fu)}; "
            f"ветвь {BRANCHES[fu % 12][0]} → {YUAN[r['yuan']][1]} (子午卯酉 — 上, 寅申巳亥 — 中, 辰戌丑未 — 下).")
    elif method == "maoshan":
        add(f"茅山法: от начала термина {TERMS[k][0]} прошло {r['elapsed_days']:.3f} сут → "
            f"{YUAN[r['yuan']][1]} (0–5 сут — 上, 5–10 — 中, далее — 下).")
        for edge in (5.0, 10.0):
            if abs(r["elapsed_days"] - edge) < 2.0 / 24:
                warnings.append(f"茅山法: рождение в {abs(r['elapsed_days'] - edge) * 24:.1f} ч от границы юаня "
                                f"({edge:.0f} сут после термина).")
    else:
        add(f"置闰法 (порог {leap_days} дн.): верхний 符头 солнцестояния {r['solstice']} — {r['solstice_futou']}; "
            f"блок рождения начат {r['block_start']} → термин {TERMS[k][0]}{' (闰奇 — повтор)' if r['leap'] else ''}, "
            f"{YUAN[r['yuan']][1]}; состояние: {STATE_RU[r['state']]}, разность дат {r['chao_days']:+d} дн.")
        if method == "hybrid":
            add("hybrid (《遁甲演義》/李氏): " + (
                f"термин {TERMS[k][0]} уже наступил ({r['canju_term_utc']}), а его блок начнётся с 符头 "
                f"{r['canju_block_start']} → 殘局: {TERMS[k][0]} 下元 («拆補之局，永為下之殘局»)."
                if r.get("canju") else "вне окна 殘局 — как 置闰法."))
    label = _ju_label(r)
    if method != "yinpan":
        add(f"Таблица 局: {TERMS[k][0]} → {JU_TABLE[k][0]}/{JU_TABLE[k][1]}/{JU_TABLE[k][2]} (上/中/下) → "
            f"{'阳遁' if yang else '阴遁'} {ju} 局 ({label}).")

    ch = build_chart(yang, ju, hi, tianqin, deities, hidden_rule)
    earth = ch["earth"]
    add("Земной диск (地盘): " + ", ".join(f"{STEMS[earth[p]][0]}→{_palace_brief(p)}" for p in
                                          sorted(earth, key=lambda q: STEM_ORDER.index(earth[q])))
        + f" ({'вперёд' if yang else 'назад'} по числам Ло Шу от {_palace_brief(ju)}).")
    xh = ch["xun_head"]
    zf_home = ch["p0"]
    zf_star = STARS[zf_home][0]
    zs_door = DOORS[ch["door_src"]][0]
    add(f"Час {ganzhi(hi)} принадлежит декаде {ganzhi(xh)} → 甲 прячется под {STEMS[ch['xun_yi']][0]} "
        f"(旬首仪), он стоит в {_palace_brief(zf_home)} → 值符 = {zf_star}, 值使 = {zs_door}"
        + (f" (центр «гостит» в {_palace_brief(ch['ji_gong'])})" if zf_home == 5 else "") + ".")
    add(f"值符 {zf_star} идёт к стволу часа {STEMS[ch['eff_stem']][0]}"
        + (f" (час 甲 → его церемониал {STEMS[ch['xun_yi']][0]})" if hi % 10 == 0 else "")
        + f": он на земном диске в {_palace_brief(ch['t_raw'])}"
        + (f" → центр «гостит» в {_palace_brief(ch['t'])}" if ch['t_raw'] == 5 else "")
        + f". Сдвиг звёзд по кругу 1→8→3→4→9→2→7→6: {ch['star_offset']} позиц.; каждая звезда несёт "
          f"ствол своего домашнего дворца (天盘), 天禽 — вместе с {STARS[ch['ji_gong']][0]}.")
    add(f"值使 {zs_door}: час {ganzhi(hi)} — {ch['pos']}-й от начала декады; {_palace_brief(zf_home)} "
        f"{'+' if yang else '−'} {ch['pos']} по числам Ло Шу → {_palace_brief(ch['door_raw'])}"
        + (f" → центр «гостит» в {_palace_brief(ch['door'])}" if ch['door_raw'] == 5 else "")
        + f". Остальные двери — по кругу по часовой стрелке (сдвиг {ch['door_offset']}).")
    add(f"Восемь духов ({'/'.join(ch['deity_names'][4:6])}): 值符 в {_palace_brief(ch['t'])}, далее "
        f"{'по часовой стрелке' if yang else 'против часовой стрелки'}.")

    # 空亡, 驿马
    xun_branch = xh % 12
    kong = [(xun_branch + 10) % 12, (xun_branch + 11) % 12]
    kong_palaces = sorted({BRANCH_PALACE[x] for x in kong})
    dx = di - di % 10
    dkong = [(dx % 12 + 10) % 12, (dx % 12 + 11) % 12]
    horse_b = HORSE[hi % 12]
    horse_p = BRANCH_PALACE[horse_b]
    add(f"Пустота (空亡) декады часа {ganzhi(xh)}: {BRANCHES[kong[0]][0]}{BRANCHES[kong[1]][0]} → дворцы "
        f"{', '.join(_palace_brief(p) for p in kong_palaces)}. Почтовая лошадь (驿马) часа {BRANCHES[hi % 12][0]}: "
        f"{BRANCHES[horse_b][0]} → {_palace_brief(horse_p)}.")

    patterns = _patterns(ch)
    palaces = _palaces_out(ch, set(kong_palaces), horse_p)

    # --- натальный блок (《奇门遁甲统宗》 卷十二: «人取年干为命，主时之局为定») ---
    ys = yi_idx % 10
    ys_eff = XUN_YI[yi_idx // 10] if ys == 0 else ys
    heaven_palace_of = {s: p for p, ss in ch["heaven"].items() for s in ss}
    ming_p = heaven_palace_of.get(ys_eff)
    relations = []
    for p in RING:
        for s in ch["heaven"][p]:
            rel = _relation(ys_eff, s)
            relations.append({"stem": STEMS[s][0], "palace": p, "trigram": PALACES[p][0], "relation": rel[0],
                              "relation_ru": rel[1], "door": DOORS[ch["door_at"][p]][0]})
    natal = {
        "year_stem": STEMS[ys][0],
        "year_stem_used": STEMS[ys_eff][0],
        "ming_palace_heaven": ming_p,
        "ming_palace_earth": {s: p for p, s in earth.items()}[ys_eff],
        "ming": None if ming_p is None else {
            "trigram": PALACES[ming_p][0], "star": STARS[ch["star_at"][ming_p][0]][0],
            "door": DOORS[ch["door_at"][ming_p]][0], "deity": ch["deity_at"][ming_p]},
        "self_palace_zhifu": ch["t"],
        "career_palace_zhishi": ch["door"],
        "six_relations": relations,
        "note": "《统宗》: судьба человека — по карте часа рождения; «本命» — ствол года рождения в карте "
                "(здесь — на небесном диске; ⚠ в тексте диск не указан); без года — 值符 = «я», "
                "值使 = дело/супруга/служба. Родственные связи — по 生克 ствола относительно ствола года.",
    }
    if ming_p is not None:
        add(f"本命: ствол года {STEMS[ys][0]}{' (甲 → ' + STEMS[ys_eff][0] + ')' if ys == 0 else ''} на небесном "
            f"диске в {_palace_brief(ming_p)}: {natal['ming']['star']}, {natal['ming']['door']}, {natal['ming']['deity']}.")

    # --- альтернативы ---
    alt_methods = {}
    for m in JU_METHODS:
        try:
            alt_methods[m] = _ju_label(_determine(m, jd, d_chart, clock, leap_days, **dctx))
        except RuntimeError as e:  # pragma: no cover
            alt_methods[m] = f"ошибка: {e}"
    if len(set(alt_methods.values())) > 1:
        warnings.append("局 зависит от метода определения (拆补/置闰/茅山) — см. alternatives.ju_methods.")
    alt_extra = {m: _ju_label(_determine(m, jd, d_chart, clock, leap_days, **dctx)) for m in JU_METHODS_EXTRA}
    # Порог 置闰 — школьный: 8 (《统宗》 1718, 《演義》 1346 — «超九日» включительно) или 9 (黄宗羲 считает разностью).
    other_leap = 9 if leap_days == 8 else 8
    zr_other = _ju_label(_determine("zhirun", jd, d_chart, clock, other_leap, **dctx))
    zhirun_other = None
    if zr_other != alt_methods["zhirun"]:
        zhirun_other = {"zhirun_leap_days": other_leap, "label": zr_other}
        if method == "zhirun":
            warnings.append(f"置闰法: 局 зависит от порога 置闰 (zhirun_leap_days={leap_days} → {alt_methods['zhirun']}, "
                            f"{other_leap} → {zr_other}); см. alternatives.zhirun_other_threshold.")
    alt_time = []
    seen = set()
    for mode in ("clock", "mean", "true"):
        if mode != "clock" and b.lon is None:
            continue
        ck = _Clock(b.tz, n.offset_source, n.utc_offset_hours, b.lon, mode)
        ct = ck.chart(n.utc)
        for zh in ("early", "late"):
            dd = chart_day(ct, zh)
            hh = hour_pillar(ct)
            rr = _determine(method, jd, dd, ck, leap_days, terms=terms, chart_t=ct, term_boundary=term_boundary,
                            hour_idx=hh, year_branch_lichun=yi_idx % 12)
            key = (dd, hh, _ju_label(rr))
            seen.add(key)
            alt_time.append({"solar_time": mode, "zi_hour": zh, "chart_time": _iso(ct), "day": ganzhi(day_index(dd)),
                             "hour": ganzhi(hh), "ju": _ju_label(rr)})
    if len(seen) > 1:
        warnings.append("Столп часа/дня или 局 зависят от шкалы времени (solar_time) или границы дня (zi_hour) — "
                        "см. alternatives.time_bases.")
    mins = chart_t.hour * 60 + chart_t.minute + chart_t.second / 60.0
    to_b = (mins + 60) % 120
    near = min(to_b, 120 - to_b)
    if near < 15:
        warnings.append(f"Время карты в {near:.0f} мин от границы двухчасовки: час (и вся карта) чувствителен к "
                        f"точности времени и выбору solar_time.")
    qi_other = None
    if method != "yinpan" and (b.year < 1645 or qi == "ping"):
        other = "ping" if qi == "ding" else "ding"
        qi_other = {"qi": other, "label": _ju_label(_determine(method, jd, d_chart, clock, leap_days,
                                                               **{**dctx, "terms": _Terms(other)}))}
    if b.year < 1645 and qi == "ding":
        warnings.append("Дата до 1645 г.: календари Мин (大统历) и Юань (授时历) считали термины «средними» (平气); "
                        f"здесь — истинные (定气). С qi='ping' (константы 授时历/大统历): {qi_other['label'] if qi_other else '—'}"
                        " — см. alternatives.qi_other.")
    if qi == "ping" and b.year >= 1645:
        warnings.append("qi='ping' для даты после 1645 г.: с календаря 时宪历 (1645) в Китае термины — истинные (定气); "
                        "平气 здесь неисторичен.")
    if qi == "ping" and b.year < 1368:
        warnings.append("qi='ping' до 1368 г.: модель — 大统历 (授时历 без 消长); календари Юань (с 消长) и Сун "
                        "давали моменты терминов, отличные на часы — дата термина может сдвинуться на сутки ⚠.")

    steps.append("Итог: " + " / ".join(_grid_text(ch)))
    hidden_rule_ru = (
        "隐干 (王凤麟, 阴盘): ствол часа — во дворец 值使, далее по кругу по часовой стрелке стволы небесного диска в их "
        "порядке («时干加在值使门上，然后按照天盘的顺序…排列一圈»); у центра скрытого ствола нет; ⚠ в классике не найдено"
        if hidden_rule == "ring" else
        "暗干: ствол часа ставится во дворец 值使 (если 值使 и 值符 в одном дворце — в центр), "
        "далее 戊己庚辛壬癸丁丙乙 вперёд (阳) / назад (阴) по числам Ло Шу; правило kinqimen "
        "TS 0.3.1, ⚠ в классических текстах не найдено")

    return {
        "method": "qimen",
        "variant": (f"时家奇门 转盘; ju_method='{method}' ({JU_METHOD_RU[method]}); solar_time='{used_mode}'; "
                    f"zi_hour='{zi_hour}'; tianqin='{tianqin}'; deities='{deities}'"
                    + (f"; zhirun_leap_days={leap_days}" if method in ("zhirun", "hybrid") else "")
                    + (f"; qi='{qi}'" if qi != "ding" else "")
                    + (f"; term_boundary='{term_boundary}'" if term_boundary != "moment" else "")
                    + (f"; hidden_stems='{hidden_rule}'" if hidden_rule != "luoshu" else "")),
        "inputs_used": {
            "local": _iso(n.local), "tz": b.tz, "utc_offset": fmt_offset(n.utc_offset_hours),
            "offset_source": n.offset_source, "utc": _iso(n.utc).replace("+00:00", "Z"), "jd_ut": round(jd, 6),
            "lat": b.lat, "lon": b.lon, "has_time": True, "chart_time": _iso(chart_t),
            "options": {"ju_method": method, "solar_time": used_mode, "zi_hour": zi_hour, "tianqin": tianqin,
                        "deities": deities, "zhirun_leap_days": leap_days, "qi": qi,
                        "term_boundary": term_boundary, "hidden_stems": hidden_rule},
        },
        "warnings": warnings,
        "pillars": {"year": ganzhi(yi_idx), "month": ganzhi(mi), "day": ganzhi(di), "hour": ganzhi(hi),
                    "day_date": d_chart.isoformat()},
        "solar_term": {
            "current": {"index": k_now, "cn": TERMS[k_now][0], "ru": TERMS[k_now][1], "meaning": TERMS[k_now][2],
                        "deg": term_deg(k_now), "utc": _jd_iso_utc(t_prev),
                        "chart_time": _iso(clock.chart_jd(t_prev))},
            "next": {"cn": TERMS[(k_now + 1) % 24][0], "ru": TERMS[(k_now + 1) % 24][1],
                     "deg": term_deg(k_now + 1), "utc": _jd_iso_utc(t_next)},
            "elapsed_days": round(jd - t_prev, 4),
            "qi": qi,
        },
        "ju": {
            "method": method, "label": label, "dun": "yang" if yang else "yin", "dun_cn": "阳遁" if yang else "阴遁",
            "number": ju, "yuan": YUAN[r["yuan"]][0] if r["yuan"] is not None else None,
            "yuan_cn": YUAN[r["yuan"]][1] if r["yuan"] is not None else None,
            "term_used": {"index": k, "cn": TERMS[k][0], "ru": TERMS[k][1]},
            "leap": bool(r.get("leap")),
            "fu_tou": {"day": ganzhi(di), "fu_tou": ganzhi(fu)},
            "zhirun": ({kk: r[kk] for kk in ("state", "chao_days", "block_start", "solstice", "solstice_futou",
                                              "leap_days")} if method in ("zhirun", "hybrid") else None),
            "maoshan_elapsed_days": round(r["elapsed_days"], 4) if method == "maoshan" else None,
            "hybrid_canju": ({kk: r.get(kk) for kk in ("canju", "canju_term_utc", "canju_block_start")}
                             if method == "hybrid" else None),
            "yinpan": ({"lunar": r["lunar"], "ju_lichun_year": r.get("ju_lichun_year")} if method == "yinpan" else None),
        },
        "xun": {"head": ganzhi(xh), "yi": STEMS[ch["xun_yi"]][0], "hour_position": ch["pos"],
                "kong_hour": [BRANCHES[x][0] for x in kong], "kong_hour_palaces": kong_palaces,
                "kong_day": [BRANCHES[x][0] for x in dkong],
                "kong_day_palaces": sorted({BRANCH_PALACE[x] for x in dkong})},
        "zhi_fu": {"star": zf_star, "star_ru": STARS[zf_home][1], "home_palace": zf_home,
                   "palace": ch["t"], "hour_stem_palace_earth": ch["t_raw"],
                   "carried_by": STARS[ch["ji_gong"]][0] if zf_home == 5 else None},
        "zhi_shi": {"door": zs_door, "door_ru": DOORS[ch["door_src"]][1], "home_palace": zf_home,
                    "palace": ch["door"], "palace_raw": ch["door_raw"], "steps": ch["pos"]},
        "horse": {"branch": BRANCHES[horse_b][0], "palace": horse_p},
        "tianqin": {"ji_gong": ch["ji_gong"], "with_star": STARS[ch["ji_gong"]][0],
                    "palace": RING[(RING.index(ch["ji_gong"]) + ch["star_offset"]) % 8],
                    "stem": STEMS[earth[5]][0]},
        "palaces": palaces,
        "grid": [[p for p in row] for row in GRID],
        "grid_text": _grid_text(ch),
        "patterns": patterns,
        "hidden_stems_rule": hidden_rule_ru,
        "natal": natal,
        "alternatives": {"ju_methods": alt_methods, "ju_methods_extra": alt_extra,
                         "zhirun_other_threshold": zhirun_other, "qi_other": qi_other, "time_bases": alt_time},
        "steps": steps,
    }


def _year_branch_at(jd: float) -> int:
    """Ветвь года (по Личуню, как в модуле 01) в момент jd."""
    y = jd_to_utc(jd).year
    return year_index(y if jd >= li_chun_jd(y) else y - 1) % 12


def _day_level(b: BirthInput, method: str, solar_time: str, zi_hour: str, tianqin: str, deities: str,
               leap_days: int, warnings: list[str], steps: list[str], add, qi: str = "ding",
               term_boundary: str = "moment", hidden_rule: str = "luoshu", terms: _Terms | None = None) -> dict:
    """Без времени рождения: данные дня и все варианты часа в пределах местных суток.

    Местные сутки (00:00–24:00 по часам) просматриваются поминутно: для каждой минуты — время карты
    (solar_time; без долготы — часы), дата столпа дня (zi_hour), столп часа и 局. Подряд идущие минуты
    с одинаковыми (день, час, 局) образуют вариант. Обычно вариантов 13, а не 12: сутки по часам не
    совпадают с сутками карты (солнечное время, час 23:00–24:00 при early — уже следующий день).
    """
    warnings.append("Время рождения неизвестно: карта Ци Мэнь строится на ЧАС (值符, 值使, звёзды, двери, духи "
                    "меняются каждые 2 часа). Ниже — только данные дня и варианты по часам; для карты нужен час.")
    used_mode = solar_time
    if solar_time != "clock" and b.lon is None:
        warnings.append("Долгота неизвестна — солнечное время не вычислить, использовано время часов.")
        used_mode = "clock"
    d_next = b.date + timedelta(days=1)
    n0 = normalize(replace(b, hour=0, minute=0, second=0))
    n1 = normalize(replace(b, year=d_next.year, month=d_next.month, day=d_next.day, hour=0, minute=0, second=0))
    warnings.extend(w for w in n0.warnings if w not in warnings)
    clock = _Clock(b.tz, n0.offset_source, n0.utc_offset_hours, b.lon, used_mode)
    total = int(round((n1.jd_ut - n0.jd_ut) * 1440))          # 1440 (1380/1500 в дни перевода часов)

    def moment(i: int) -> tuple[float, datetime, datetime]:
        utc = n0.utc + timedelta(minutes=i)                    # точно, без округления JD → datetime
        return n0.jd_ut + i / 1440.0, clock.civil(utc), clock.chart(utc)

    # 1) поминутно: (дата столпа дня, столп часа)
    runs: list[list] = []                                     # [day_date, hour_idx, i_start, i_end]
    for i in range(total):
        _, _, ct = moment(i)
        key = (chart_day(ct, zi_hour), hour_pillar(ct))
        if runs and (runs[-1][0], runs[-1][1]) == key:
            runs[-1][3] = i
        else:
            runs.append([key[0], key[1], i, i])

    # 2) 局 на границах каждого отрезка; если внутри сменился термин / юань — делим (бисекция по минутам)
    cache: dict[int, dict] = {}

    def ju_at(i: int, dd: date) -> dict:
        if i not in cache:
            jd_i, _, ct_i = moment(i)
            cache[i] = _determine(method, jd_i, dd, clock, leap_days, terms=terms, chart_t=ct_i,
                                  term_boundary=term_boundary, hour_idx=hour_pillar(ct_i),
                                  year_branch_lichun=_year_branch_at(jd_i))
        return cache[i]

    segs: list[tuple] = []                                    # (day_date, hour_idx, i_s, i_e, r)

    def split(dd: date, hh: int, i_s: int, i_e: int) -> None:
        rs, re_ = ju_at(i_s, dd), ju_at(i_e, dd)
        if _ju_label(rs) == _ju_label(re_):
            segs.append((dd, hh, i_s, i_e, rs))
            return
        lo, hi = i_s, i_e                                     # label(lo) = начальный, label(hi) ≠
        while hi - lo > 1:
            mid = (lo + hi) // 2
            if _ju_label(ju_at(mid, dd)) == _ju_label(rs):
                lo = mid
            else:
                hi = mid
        segs.append((dd, hh, i_s, lo, rs))
        split(dd, hh, hi, i_e)

    for dd, hh, i_s, i_e in runs:
        split(dd, hh, i_s, i_e)

    def hm(t: datetime) -> str:
        return f"{t:%H:%M}"

    candidates = []
    for dd, hh, i_s, i_e, r in segs:
        k = r["term"]
        ch = build_chart(_ju_yang(r), _ju_number(r), hh, tianqin, deities, hidden_rule)
        _, civ_s, ct_s = moment(i_s)
        _, civ_e, ct_e = moment(i_e + 1)
        candidates.append({
            "hour_branch": BRANCHES[hh % 12][0], "hours": f"{hm(ct_s)}–{hm(ct_e)}",
            "clock_hours": f"{hm(civ_s)}–{'24:00' if i_e + 1 == total else hm(civ_e)}",
            "day_pillar": ganzhi(day_index(dd)), "hour_pillar": ganzhi(hh), "ju": _ju_label(r),
            "xun_head": ganzhi(ch["xun_head"]), "zhi_fu_star": STARS[ch["p0"]][0], "zhi_fu_palace": ch["t"],
            "zhi_shi_door": DOORS[ch["door_src"]][0], "zhi_shi_palace": ch["door"],
        })

    # 3) 局 по отрезкам суток и «局 дня» — на последнюю минуту суток со столпом дня этой даты
    variants = []
    for c in candidates:
        if variants and variants[-1]["ju"] == c["ju"]:
            variants[-1]["local_to"] = c["clock_hours"].split("–")[1]
        else:
            variants.append({"local_from": c["clock_hours"].split("–")[0], "local_to": c["clock_hours"].split("–")[1],
                             "ju": c["ju"]})
    di = day_index(b.date)
    own = [s for s in segs if s[0] == b.date] or segs
    r = own[-1][4]
    if len(variants) > 1:
        warnings.append("В эти сутки 局 меняется: " + "; ".join(f"{v['local_from']}–{v['local_to']} — {v['ju']}"
                                                              for v in variants) + ". Без времени нельзя выбрать.")
    if b.year < 1645 and qi == "ding":
        warnings.append("Дата до 1645 г.: календари Мин (大统历) и Юань (授时历) считали термины «средними» (平气); "
                        "здесь — истинные (定气), поэтому 局 может не совпасть с историческими книгами "
                        "(вариант — qi='ping').")
    if qi == "ping" and b.year >= 1645:
        warnings.append("qi='ping' для даты после 1645 г.: с календаря 时宪历 (1645) термины — истинные (定气).")

    lc = li_chun_jd(n1.utc.year)
    jd_end = n1.jd_ut - 1e-6
    bazi_year = n1.utc.year if jd_end >= lc else n1.utc.year - 1
    yi_idx = year_index(bazi_year)
    slot = month_slot(sun_longitude(jd_end))
    mi = ganzhi_index((month_first_stem(yi_idx % 10) + slot) % 10, (slot + 2) % 12)
    mode_ru = {"clock": "время часов", "mean": "местное среднее солнечное (LMT)",
               "true": "истинное солнечное"}[used_mode]
    add(f"Дата {b.date:%d.%m.%Y} (без времени): столп дня {ganzhi(di)}; год {ganzhi(yi_idx)}, месяц {ganzhi(mi)} "
        f"— на конец местной даты (как в модуле 01).")
    add(f"Сутки 00:00–24:00 по часам ({b.tz}) просмотрены поминутно; время карты — {mode_ru}, граница дня "
        f"zi_hour='{zi_hour}'. Вариантов (день, час, 局): {len(candidates)}; поле clock_hours — по часам, "
        f"hours — по времени карты.")
    k = r["term"]
    yang = _ju_yang(r)
    ju = _ju_number(r)
    add(f"局 дня {ganzhi(di)} (последняя минута суток с этим столпом дня; {JU_METHOD_RU[method]}): {_ju_label(r)}"
        + ("" if len(variants) == 1 else "; в течение суток: " + ", ".join(v["ju"] for v in variants)) + ".")
    earth = earth_plate(yang, ju)
    add("Земной диск: " + ", ".join(f"{STEMS[earth[p]][0]}→{_palace_brief(p)}" for p in
                                   sorted(earth, key=lambda q: STEM_ORDER.index(earth[q]))) + ".")
    dx = di - di % 10
    return {
        "method": "qimen",
        "variant": (f"时家奇门 转盘; ju_method='{method}'; solar_time='{used_mode}'; zi_hour='{zi_hour}'; "
                    + (f"qi='{qi}'; " if qi != "ding" else "")
                    + (f"term_boundary='{term_boundary}'; " if term_boundary != "moment" else "")
                    + "без времени — только данные дня"),
        "inputs_used": {"local": b.date.isoformat(), "tz": b.tz, "lat": b.lat, "lon": b.lon, "has_time": False,
                        "options": {"ju_method": method, "solar_time": used_mode, "zi_hour": zi_hour,
                                    "tianqin": tianqin, "deities": deities, "zhirun_leap_days": leap_days,
                                    "qi": qi, "term_boundary": term_boundary, "hidden_stems": hidden_rule}},
        "warnings": warnings,
        "pillars": {"year": ganzhi(yi_idx), "month": ganzhi(mi), "day": ganzhi(di), "hour": None,
                    "day_date": b.date.isoformat()},
        "ju": {"method": method, "label": _ju_label(r), "dun": "yang" if yang else "yin", "number": ju,
               "yuan": YUAN[r["yuan"]][0] if r["yuan"] is not None else None,
               "yuan_cn": YUAN[r["yuan"]][1] if r["yuan"] is not None else None,
               "term_used": {"index": k, "cn": TERMS[k][0], "ru": TERMS[k][1]}, "leap": bool(r.get("leap")),
               "variants_in_day": variants},
        "earth_plate": {str(p): STEMS[s][0] for p, s in sorted(earth.items())},
        "xun_day": {"head": ganzhi(dx), "kong": [BRANCHES[(dx % 12 + 10) % 12][0], BRANCHES[(dx % 12 + 11) % 12][0]]},
        "hour_candidates": candidates,
        "chart": None,
        "steps": steps,
    }


if __name__ == "__main__":  # pragma: no cover
    import json

    out = calculate(BirthInput(1990, 5, 15, 14, 30, place="Москва"))
    print(json.dumps(out, ensure_ascii=False, indent=1)[:6000])
