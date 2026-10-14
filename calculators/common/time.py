"""Нормализация входных данных рождения: локальное время -> UTC -> юлианский день.

Ключевые правила (подробно — knowledge-base/00-input-normalization.md):
* Историческое смещение берётся из базы IANA tzdb (zoneinfo), а не «текущее»:
  СССР знал декретное время (с 1930), летнее время 1981–1991, отмену декрета 1991,
  «вечное летнее» 2011–2014 и возврат 2014 — tzdb всё это хранит.
* Если на дату рождения в зоне действовало LMT (до введения поясного времени),
  считаем местное среднее время по долготе места (lon/15 ч), а не LMT столицы зоны.
* Неоднозначное (осенний перевод часов) и несуществующее (весенний) время
  помечаются предупреждением; по умолчанию берётся fold=0 (первое вхождение).
* Известные отклонения фактического времени от tzdb (регионы-«нарушители» 1981/82,
  Туркмения 1991/92, Поволжье и Средняя Азия 1990–1992, Крым 1990–1997, ДНР/ЛНР,
  Абхазия и Южная Осетия после 2014 и др.) собраны в таблице _REGIONAL_RULES с источниками:
  либо исправляют смещение (offset_source = "regional_exception"), либо дают
  предупреждение и альтернативу в NormalizedTime.alternatives (KB 00, §3.3 и табл. 4.11).
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import date, datetime, time, timedelta, timezone
from typing import Callable
from zoneinfo import ZoneInfo

import swisseph as swe

from .places import resolve_place


@dataclass
class BirthInput:
    """Входные данные. Время и место необязательны (для методов «только по дате»)."""

    year: int
    month: int
    day: int
    hour: int | None = None
    minute: int | None = None
    tz: str | None = None          # IANA, напр. "Europe/Moscow"; или "UTC+03:00"; или "LMT"
    lat: float | None = None
    lon: float | None = None       # восточная долгота положительна
    place: str | None = None       # название из справочника places.py
    gender: str | None = None      # "male" / "female"
    name: str | None = None        # ФИО (для нумерологии)
    fold: int = 0                  # для неоднозначного времени при переводе часов
    second: int = 0                # секунды (важно для точного Асцендента: 4 с ≈ 1′)
    calendar: str = "gregorian"    # "gregorian" | "julian" (старый стиль: Россия до 14.02.1918)
    julian_date: tuple[int, int, int] | None = None  # исходная дата по ст. ст., если была
    region: str | None = None      # регион/область на дату рождения («Татарская АССР», «Тюменская область»,
                                   # «Абхазия», «ДНР»…) — для региональных исключений tzdb (KB 00, табл. 4.11)

    def __post_init__(self) -> None:
        cal = str(self.calendar).strip().lower()
        if cal not in ("gregorian", "julian"):
            raise ValueError("calendar должен быть 'gregorian' или 'julian'")
        self.calendar = cal
        if self.calendar == "julian":
            # Перевод даты старого стиля в григорианскую (+10…+13 дней в зависимости от века).
            # swe.julday() не проверяет дату: «30.02» или «31.04» молча перекатились бы
            # в следующий месяц, поэтому сверяем обратным переводом.
            jd = swe.julday(self.year, self.month, self.day, 12.0, swe.JUL_CAL)
            if tuple(swe.revjul(jd, swe.JUL_CAL)[:3]) != (self.year, self.month, self.day):
                raise ValueError(
                    f"Несуществующая дата юлианского календаря: {self.day:02d}.{self.month:02d}.{self.year}"
                )
            self.julian_date = (self.year, self.month, self.day)
            self.year, self.month, self.day, _ = swe.revjul(jd, swe.GREG_CAL)
            self.calendar = "gregorian"   # чтобы dataclasses.replace() не перевёл дату повторно
        else:
            try:
                date(self.year, self.month, self.day)
            except ValueError:
                raise ValueError(
                    f"Несуществующая дата: {self.day:02d}.{self.month:02d}.{self.year}"
                ) from None
        if self.place and (self.lat is None or self.lon is None or self.tz is None):
            p = resolve_place(self.place)
            if p:
                self.lat = p["lat"] if self.lat is None else self.lat
                self.lon = p["lon"] if self.lon is None else self.lon
                self.tz = p["tz"] if self.tz is None else self.tz
        if self.tz is None and self.lat is not None and self.lon is not None:
            # зона по координатам (timezonefinder); историческое смещение потом даст tzdb
            from .places import tz_for_coords
            self.tz = tz_for_coords(self.lat, self.lon)

    @property
    def date(self) -> date:
        return date(self.year, self.month, self.day)

    @property
    def has_time(self) -> bool:
        return self.hour is not None

    @property
    def has_place(self) -> bool:
        return self.lat is not None and self.lon is not None


@dataclass
class NormalizedTime:
    local: datetime                 # наивное локальное (как ввёл пользователь)
    utc: datetime                   # aware UTC
    utc_offset_hours: float
    offset_source: str              # "tzdb", "fixed", "LMT(longitude)", "regional_exception"
    jd_ut: float                    # юлианский день UT
    warnings: list[str] = field(default_factory=list)
    # Другие версии момента рождения: {"utc_offset_hours", "tz", "utc", "jd_ut", "reason"}.
    # Заполняется при переводе часов (вторая версия fold) и для региональных исключений.
    alternatives: list[dict] = field(default_factory=list)


_FIXED_RE = re.compile(r"^(?:UTC|GMT)?([+-])(\d{1,2})(?::?(\d{2}))?(?::?(\d{2}))?$")


def _parse_fixed_offset(tz: str) -> timedelta | None:
    """'UTC', 'UTC+3', 'UTC+03:00', 'UTC+0300', 'GMT-3:30', '+05:45' -> timedelta; иначе None.

    Строки, похожие на смещение, но некорректные (например 'UTC+5:3' или 'UTC+99'), вызывают ValueError,
    а не молча превращаются в сотни часов.
    """
    s = tz.strip().upper().replace(" ", "")
    if s in ("UTC", "GMT", "Z", "UT"):
        return timedelta(0)
    if not (s.startswith(("UTC", "GMT")) or s[:1] in "+-"):
        return None
    m = _FIXED_RE.match(s)
    if not m:
        raise ValueError(f"Не удалось разобрать смещение {tz!r}: ожидается вид UTC+03:00, UTC+0300 или UTC+3")
    sign = -1 if m.group(1) == "-" else 1
    h, mi, se = int(m.group(2)), int(m.group(3) or 0), int(m.group(4) or 0)
    if mi >= 60 or se >= 60 or h * 3600 + mi * 60 + se > 14 * 3600:
        raise ValueError(f"Смещение {tz!r} вне диапазона UTC−14…UTC+14")
    return sign * timedelta(hours=h, minutes=mi, seconds=se)


# Зоны бывшей Российской империи. До перехода на поясное время (1919–1924) tzdb хранит для
# всей зоны среднее время ГОРОДА-эталона (MMT Москвы, KMT Киева, TBMT Тифлиса …), хотя
# единого законного времени не было и в других городах шло своё местное время. Поэтому
# для этих аббревиатур подставляем LMT по долготе места рождения (+ летний сдвиг 1917–1919).
_RU_EMPIRE_MEAN_TIME: dict[str, set[str]] = {
    "Europe/Moscow": {"MMT", "MST", "MDST"},
    "Europe/Kyiv": {"KMT"}, "Europe/Kiev": {"KMT"},
    "Europe/Minsk": {"MMT"},
    "Europe/Simferopol": {"SMT"},
    "Europe/Chisinau": {"CMT"},
    "Europe/Riga": {"RMT", "LST"},
    "Europe/Tallinn": {"TMT"},
    "Asia/Tbilisi": {"TBMT"},
    "Asia/Irkutsk": {"IMT"},
}

# С этих дат (местное время) «среднее время столицы» в tzdb относится уже к независимому
# государству и могло быть законным для всей страны (⚠ не подтверждено): LMT места
# по-прежнему подставляется, но с предупреждением и альтернативой.
_NATIONAL_MEAN_TIME_FROM: dict[str, datetime] = {
    "Europe/Riga": datetime(1918, 11, 18),     # Латвийская Республика; RMT до 11.05.1926
    "Europe/Tallinn": datetime(1919, 7, 1),    # Эстонская Республика; TMT до 01.05.1921
}

_DOUBLE_SUMMER = {"CEMT", "BDST", "MDST", "WEMT"}


# --------------------------------------------------------------------------- регионы
# Опознание региона по BirthInput.region или BirthInput.place. Шаблон — слова через пробел;
# «*» в конце слова — совпадение по началу слова («ивановск* обл*» = «Ивановская область»).
# Строки нормализуются: нижний регистр, «ё» → «е», знаки препинания и дефисы → пробел.
# Списки взяты из источников правил ниже (перечень «Труда» 1982, таблица административных
# центров ru.wikipedia «Время в России» и т. п.) и заведомо не полны: если регион не опознан,
# правило выдаёт предупреждение с альтернативой, а не молчит.
_REGION_ALIASES: dict[str, tuple[str, ...]] = {
    # Регионы-«нарушители» европейской части РСФСР, 1981/82 («Труд», 20.02.1982; «Наука и жизнь», 1981, № 3).
    # Адыгея и Карачаево-Черкесия входили в Краснодарский и Ставропольский края.
    "violator_1981": (
        "дагестан*", "махачкала", "кабардино балкар*", "нальчик", "калмык*", "калмыц*", "элиста",
        "коми", "сыктывкар", "марий эл", "марийск*", "йошкар ола", "мордов*", "саранск",
        "северн* осет*", "северо осетин*", "владикавказ", "орджоникидзе", "татарстан", "татарск*",
        "татария", "казань", "чечено ингуш*", "чечн*", "чеченск*", "ингуш*", "грозный", "назрань",
        "чуваш*", "чебоксары", "краснодар", "краснодарск*", "адыге*", "майкоп", "ставрополь",
        "ставропольск*", "карачаево черкес*", "черкесск", "архангельск*", "владимир",
        "владимирск* обл*", "вологд*", "вологодск*", "воронеж*", "нижн* новгород", "нижегородск*",
        "горький", "горьковск*", "иваново", "ивановск* обл*", "кострома", "костромск*", "липецк*",
        "пенз*", "ростов", "ростов на дону", "ростовск* обл*", "рязан*", "тамбов", "тамбовск* обл*",
        "ярославл*", "ярославск* обл*", "ненецк*", "нарьян мар",
    ),
    "tyumen_1981": ("тюмен*", "салехард", "ханты мансийск*", "ямало ненецк*"),
    "evenkia_1981": ("эвенки*", "эвенкийск*", "тура", "хатанг*"),
    # Заведомо не «нарушители» (эталонные города зон) — чтобы не выдавать лишних предупреждений.
    "moscow": ("москва", "московск* обл*", "зеленоград"),
    "spb": ("санкт петербург", "петербург", "ленинград", "спб", "ленинградск* обл*", "st petersburg"),
    "sverdlovsk": ("екатеринбург", "свердловск*"),
    "krasnoyarsk_city": ("красноярск",),
    # Europe/Samara объединяет Удмуртию и Самарскую обл. (tzdb europe), их история 1989–1992 разная.
    "udmurtia": ("удмурт*", "ижевск", "устинов", "сарапул", "воткинск", "глазов"),
    "samara_obl": ("самар*", "куйбышев", "тольятти", "сызрань", "новокуйбышевск"),
    "kerch": ("керчь",),
    "dpr_lpr": ("днр", "лнр", "донецк", "луганск", "ворошиловград", "донецк* народн*", "луганск* народн*"),
    "abkhazia_so": ("абхаз*", "сухум*", "гагра", "пицунда", "гудаут*", "южн* осет*", "цхинвал*"),
    "transcarpathia": ("закарпат*", "ужгород", "мукачев*", "берегово", "хуст"),
    "berlin": ("берлин", "berlin"),
    "wurttemberg": ("ульм", "ulm", "штутгарт", "stuttgart", "вюртемберг*", "württemberg*", "wurttemberg*",
                    "wuerttemberg*", "фридрихсхафен"),
}

_NORM_RE = re.compile(r"[^0-9a-zа-яäöüß]+")


def _norm_text(s: str) -> list[str]:
    return _NORM_RE.sub(" ", s.lower().replace("ё", "е")).split()


def _alias_matches(alias: str, words: list[str]) -> bool:
    pat = alias.split()
    for i in range(len(words) - len(pat) + 1):
        if all(w.startswith(p[:-1]) if p.endswith("*") else w == p for p, w in zip(pat, words[i:])):
            return True
    return False


def identify_region(b: "BirthInput") -> str | None:
    """Ключ региона из _REGION_ALIASES по b.region, затем по b.place; для Europe/Samara — по широте.

    None — регион не опознан (тогда правила, привязанные к регионам, только предупреждают).
    """
    for text in (b.region, b.place):
        if not text:
            continue
        words = _norm_text(text)
        for key, aliases in _REGION_ALIASES.items():
            if any(_alias_matches(a, words) for a in aliases):
                return key
    if b.tz == "Europe/Samara" and b.lat is not None:
        # Удмуртия лежит севернее 55.8° с. ш., Самарская область — южнее 54.7° с. ш.;
        # между ними — Татарстан (Europe/Moscow), поэтому граница 55° однозначна.
        return "udmurtia" if b.lat >= 55.0 else "samara_obl"
    return None


@dataclass(frozen=True)
class _RegionalRule:
    """Известное расхождение фактического гражданского времени с tzdb.

    action="correct": если регион опознан (или правило на всю зону), смещение tzdb ЗАМЕНЯЕТСЯ
    на вариант правила (offset_source="regional_exception"), версия tzdb уходит в alternatives.
    action="alt": смещение tzdb сохраняется, вариант правила — предупреждение и alternatives.
    Для correct-правил с неопознанным регионом — тоже только предупреждение.
    """

    key: str
    zones: tuple[str, ...]
    start: datetime                 # местное время, включительно
    end: datetime                   # местное время, не включительно
    action: str                     # "correct" | "alt"
    note: str                       # что случилось и источник (кратко, по-русски)
    regions: tuple[str, ...] = ()   # ключи _REGION_ALIASES; пусто — вся зона
    offset_h: float | None = None   # смещение варианта, ч
    delta_h: float | None = None    # или: вариант = tzdb + delta
    alt: Callable[[datetime], timedelta] | None = None  # или: функция местного времени
    warn_unidentified: bool = True  # предупреждать, если регион не опознан
    exclude: tuple[str, ...] = ()   # опознанные регионы, к которым правило не относится

    def alternative(self, local: datetime, tzdb_offset: timedelta) -> timedelta:
        if self.alt is not None:
            return self.alt(local)
        if self.offset_h is not None:
            return timedelta(hours=self.offset_h)
        return tzdb_offset + timedelta(hours=self.delta_h or 0)


def _abkhazia_before_2011(local: datetime) -> timedelta:
    # ru.wikipedia «Время в Грузии»: московское время; перевод на летнее в Абхазии — с 2005 г.
    if local < datetime(2005, 3, 27, 2):
        return timedelta(hours=3)
    return datetime(local.year, local.month, local.day, local.hour, local.minute,
                    tzinfo=ZoneInfo("Europe/Moscow")).utcoffset()


def _germany_west_1945(local: datetime) -> timedelta:
    # PTB и правило C-Eur tzdb: летнее время 02.04.1945 – 16.09.1945 02:00s (03:00 CEST), затем CET.
    return timedelta(hours=2 if local < datetime(1945, 9, 16, 3) else 1)


def _uzhgorod_tzdb2022c(local: datetime) -> timedelta:
    # tzdb 2022c, Zone Europe/Uzhgorod (до слияния с Киевом в 2022d): CET до 1940; C-Eur (как Берлин)
    # до 10.1944; CEST до 26.10.1944; CET до 29.06.1945.
    if local < datetime(1940, 1, 1):
        return timedelta(hours=1)
    if local < datetime(1944, 10, 1):
        return datetime(local.year, local.month, local.day, local.hour, local.minute,
                        tzinfo=ZoneInfo("Europe/Berlin")).utcoffset()
    return timedelta(hours=2 if local < datetime(1944, 10, 26) else 1)


_D = datetime
_SRC_1981 = ("«Наука и жизнь», 1981, № 3 (В. Бойцов, Госстандарт): «нарушители времени» 1.10.1981 стрелки "
             "назад не переводят; «Труд», 20.02.1982: с 1.04.1982 летнее время там не вводится и регионы "
             "возвращаются к прежнему счёту времени (http://besp.narod.ru/nauka_1981_3.htm; tzdb europe, "
             "комм. S. Golosunov 2016)")
_SRC_1991_ASIA = ("постановление Кабмина СССР № 20 от 04.02.1991 (pravo.gov.ru, nd=102010545) и планы "
                  "Госкомиссии единого времени в «Известиях» № 68 от 20.03.1991 и «Советской России» "
                  "29.03.1991 (tzdb asia, комм. S. Golosunov; ru.wikipedia «Декретное время»)")

_REGIONAL_RULES: tuple[_RegionalRule, ...] = (
    # --- 1981/82: регионы-«нарушители» не перевели часы ни 1.10.1981, ни 1.04.1982 ---------------
    _RegionalRule(
        "violators_1981_europe", ("Europe/Moscow",), _D(1981, 9, 30, 23), _D(1982, 4, 1, 1), "correct",
        "регион-«нарушитель» 1981/82 (АССР Дагестанская, Кабардино-Балкарская, Калмыцкая, Коми, Марийская, "
        "Мордовская, Северо-Осетинская, Татарская, Чечено-Ингушская, Чувашская; Краснодарский и Ставропольский "
        "края; области Архангельская, Владимирская, Вологодская, Воронежская, Горьковская, Ивановская, "
        "Костромская, Липецкая, Пензенская, Ростовская, Рязанская, Тамбовская, Ярославская; Ненецкий АО): "
        "с 01.10.1981 до 01.04.1982 часы не переводили — UTC+4 (МСК+1). Для Коми и НАО после 01.04.1982 "
        "источники расходятся (Атлас СССР 1983: МСК+1 до 1984–1987). Источник: " + _SRC_1981,
        regions=("violator_1981",), offset_h=4.0),
    _RegionalRule(
        "violators_1981_tyumen", ("Asia/Yekaterinburg",), _D(1981, 9, 30, 23), _D(1982, 4, 1, 1), "correct",
        "Тюменская область (вкл. Ханты-Мансийский и Ямало-Ненецкий АО) 1981/82: с 01.10.1981 до 01.04.1982 "
        "часы не переводили — UTC+6 (МСК+3), с 01.04.1982 снова МСК+2. Источник: " + _SRC_1981,
        regions=("tyumen_1981",), offset_h=6.0),
    _RegionalRule(
        "violators_1981_evenkia", ("Asia/Krasnoyarsk",), _D(1981, 9, 30, 23), _D(1982, 4, 1, 1), "correct",
        "Эвенкийский АО и Хатангский район Таймырского АО 1981/82: с 01.10.1981 до 01.04.1982 часы не "
        "переводили — UTC+8 (МСК+5), с 01.04.1982 снова МСК+4. Источник: " + _SRC_1981,
        regions=("evenkia_1981",), offset_h=8.0),
    # --- 1989–1992: Поволжье и Удмуртия ------------------------------------------------------------
    _RegionalRule(
        "udmurtia_1989_1991", ("Europe/Samara",), _D(1989, 3, 26, 2), _D(1991, 10, 20, 3), "alt",
        "Удмуртия 1989–1991: Europe/Samara отражает Куйбышев (Самару), перешедший на МСК 26.03.1989 "
        "(пост. СМ СССР № 227); Удмуртии в этом перечне нет, по ru.wikipedia («Время в России», Ижевск) "
        "она осталась на МСК+1 до 1991 г. (tzdb europe, комм. S. Golosunov: «Udmurtia is not mentioned in "
        "the 1989 act»). Вариант на 1 ч больше tzdb",
        regions=("udmurtia",), delta_h=+1.0),
    _RegionalRule(
        "samara_1991", ("Europe/Samara",), _D(1991, 10, 20, 3), _D(1992, 1, 19, 2), "alt",
        "Самарская обл. 20.10.1991–19.01.1992: tzdb переводит часы на +1 ч 20.10.1991 (источник в tzdb не "
        "указан); по ru.wikipedia («Время в России»: Самара 3 с 29.09.1991, 4 с 1992; «Аргументы и факты в "
        "Самаре») — UTC+3 до 19.01.1992",
        regions=("samara_obl",), delta_h=-1.0),
    _RegionalRule(
        "volga_1991_1992", ("Europe/Astrakhan", "Europe/Volgograd", "Europe/Saratov", "Europe/Kirov"),
        _D(1991, 3, 31, 2), _D(1992, 3, 29, 2), "alt",
        "Астраханская, Волгоградская, Саратовская, Кировская обл. 31.03.1991–29.03.1992: в tzdb UTC+4 "
        "(источник не указан); по плану Госкомиссии (весной 1991 г. часы «на большей части СССР» не "
        "переводят) и ru.wikipedia «Декретное время» (вероятнее всего не переводили часы осенью 1991 и "
        "19.01.1992, «действовало время UTC+3») — UTC+3",
        delta_h=-1.0),
    # --- 1990–1992: Средняя Азия и Закавказье --------------------------------------------------------
    _RegionalRule(
        "no_dst_1990", ("Asia/Tashkent", "Asia/Samarkand", "Asia/Dushanbe", "Asia/Baku"),
        _D(1990, 3, 25, 2), _D(1990, 9, 30, 3), "alt",
        "лето 1990: tzdb (Shanks & Pottenger) переводит часы на летнее время; по сообщению ТАСС («Звезда», "
        "Пермь, 27.02.1991; цит. ru.wikipedia «Декретное время», «Время в Узбекистане», «Время в "
        "Таджикистане») «Белоруссия, Узбекистан, Таджикистан, Азербайджан летнее время не вводили»",
        delta_h=-1.0),
    _RegionalRule(
        "uzbekistan_1991", ("Asia/Tashkent", "Asia/Samarkand"), _D(1991, 3, 31, 2), _D(1991, 9, 29, 3), "alt",
        "Узбекистан, лето 1991: tzdb даёт UTC+6; по пост. № 20 вся Узбекская ССР получает время 5-го пояса "
        "(UTC+5), летнее время необязательно, а по плану Госкомиссии восточные области 31.03.1991 переводят "
        "часы на 1 ч назад, западные не переводят. Источник: " + _SRC_1991_ASIA,
        delta_h=-1.0),
    _RegionalRule(
        "kyrgyzstan_1991", ("Asia/Bishkek",), _D(1991, 3, 31, 2), _D(1991, 8, 31, 2), "alt",
        "Киргизия, 31.03–31.08.1991: tzdb (Shanks & Pottenger) переводит часы назад только 31.08.1991; по плану "
        "Госкомиссии — 31.03.1991 (UTC+5). Источник: " + _SRC_1991_ASIA,
        delta_h=-1.0),
    _RegionalRule(
        "tajikistan_1991", ("Asia/Dushanbe",), _D(1991, 3, 31, 2), _D(1991, 9, 9, 2), "alt",
        "Таджикистан, 31.03–09.09.1991: tzdb (Shanks & Pottenger) переводит часы назад только 09.09.1991; по "
        "плану Госкомиссии — 31.03.1991 (UTC+5). Источник: " + _SRC_1991_ASIA,
        delta_h=-1.0),
    _RegionalRule(
        "turkmenistan_1991", ("Asia/Ashgabat",), _D(1991, 9, 29, 2), _D(1992, 1, 19, 3), "correct",
        "Туркмения 29.09.1991–19.01.1992: пост. Кабмина СССР № 20 от 04.02.1991 устанавливает в Туркменской "
        "ССР время 5-го пояса (UTC+5), и по обоим опубликованным планам Госкомиссии 29.09.1991 часы в "
        "Туркмении назад не переводят — UTC+5; tzdb (Shanks & Pottenger, без ссылки на документ) даёт UTC+4. "
        "Источник: " + _SRC_1991_ASIA,
        offset_h=5.0),
    # --- Крым ------------------------------------------------------------------------------------------
    _RegionalRule(
        "crimea_1990_1991", ("Europe/Simferopol",), _D(1990, 3, 25, 2), _D(1991, 9, 29, 3), "alt",
        "Крым 1990–1991: tzdb (без источника) — МСК без летнего, затем UTC+2 с 01.07.1990; постановления СМ "
        "УССР № 134 и № 272 от 1990 г. (действовали на всей территории УССР; tzdb europe, Europe/Kyiv) и "
        "ru.wikipedia «Время в России» (Симферополь) дают время Киева — на 1 ч больше",
        delta_h=+1.0),
    _RegionalRule(
        "crimea_1994_spring", ("Europe/Simferopol",), _D(1994, 3, 27, 2), _D(1994, 5, 1), "alt",
        "Крым, весна 1994: tzdb переводит Крым на московское время «в мае» (догадка: «For now, guess it changed "
        "in May»); по указу Президента Республики Крым № 01/94 от 01.03.1994 (цит. ru.wikipedia «Время в "
        "России», «Время на Украине») — с 27.03.1994 московское летнее UTC+4",
        offset_h=4.0),
    _RegionalRule(
        "kerch_1994_1996", ("Europe/Simferopol",), _D(1994, 5, 1), _D(1996, 3, 31, 2), "alt",
        "Керчь 1994–1996: по IATA SSIM (tzdb europe) Керчь оставалась на киевском времени, хотя центральный "
        "Крым перешёл на московское (ru.wikipedia: вся АР Крым)",
        regions=("kerch",), delta_h=-1.0, warn_unidentified=False),
    _RegionalRule(
        "crimea_1996_1997", ("Europe/Simferopol",), _D(1996, 3, 31, 2), _D(1997, 3, 30, 3), "alt",
        "Крым 31.03.1996–30.03.1997: tzdb (IATA SSIM) — ещё московское время до 30.03.1997; ru.wikipedia «Время "
        "на Украине»: «весной 1996 года республика … перешла на киевское время» — на 1 ч меньше",
        delta_h=-1.0),
    # --- после 2014 ------------------------------------------------------------------------------------
    _RegionalRule(
        "dpr_lpr_2014", ("Europe/Kyiv", "Europe/Kiev"), _D(2014, 10, 26, 3), _D(2100, 1, 1), "correct",
        "ДНР/ЛНР: с 26.10.2014 часы на зимнее время не переводили — UTC+3 круглый год («донецкое»/московское "
        "время; ru.wikipedia «Время на Украине», «Московское время»: segodnya.ua, RT 24.10.2014, Росбалт "
        "26.10.2014); tzdb Europe/Kyiv — время Украины",
        regions=("dpr_lpr",), offset_h=3.0, warn_unidentified=False),
    _RegionalRule(
        "abkhazia_so_2014", ("Asia/Tbilisi",), _D(2014, 10, 26, 2), _D(2100, 1, 1), "correct",
        "Абхазия и Южная Осетия: с 26.10.2014 московское время UTC+3 (ru.wikipedia «Декретное время», «Время в "
        "Грузии»); tzdb Asia/Tbilisi — время Грузии UTC+4",
        regions=("abkhazia_so",), offset_h=3.0, warn_unidentified=False),
    _RegionalRule(
        "abkhazia_so_before_2011", ("Asia/Tbilisi",), _D(1992, 1, 1), _D(2011, 3, 27, 2), "alt",
        "Абхазия и Южная Осетия до 2011: «после провозглашения независимости … переход с тбилисского времени "
        "на московское», летнее время в Абхазии с 2005 г. (ru.wikipedia «Время в Грузии»; дата перехода не "
        "установлена)",
        regions=("abkhazia_so",), alt=_abkhazia_before_2011, warn_unidentified=False),
    # --- до 1946 -------------------------------------------------------------------------------------
    _RegionalRule(
        "transcarpathia_pre1945", ("Europe/Kyiv", "Europe/Kiev"), _D(1890, 10, 1), _D(1945, 6, 29), "alt",
        "Закарпатье до 29.06.1945 не входило в Российскую империю/СССР (Австро-Венгрия, ЧСР, Венгрия): "
        "Europe/Kyiv к нему неприменима; данные tzdb до 2022d (Zone Europe/Uzhgorod, Shanks & Pottenger) — "
        "CET/CEST",
        regions=("transcarpathia",), alt=_uzhgorod_tzdb2022c, warn_unidentified=False),
    _RegionalRule(
        "germany_west_1945", ("Europe/Berlin",), _D(1945, 5, 24, 2), _D(1945, 11, 18, 3), "alt",
        "Германия 1945: tzdb применяет к Europe/Berlin правило «SovietZone» (московское время по приказу "
        "Берзарина, CEMT +3 до 24.09, CEST до 18.11.1945); для западных зон оккупации PTB даёт обычное летнее "
        "время до 16.09.1945, затем CET",
        alt=_germany_west_1945, exclude=("berlin",)),
    _RegionalRule(
        "wurttemberg_pre1893", ("Europe/Berlin",), _D(1850, 1, 1), _D(1893, 4, 1), "alt",
        "Вюртемберг до 01.04.1893: «In Württemberg galt die Stuttgarter Zeit» (Gleber, Badische Heimat 2/2003; "
        "пример: когда в Брегенце был полдень, во Фридрихсхафене было 11.39 — это время Штутгарта, а не "
        "LMT Фридрихсхафена 11.40). Был ли по нему записан час рождения, не установлено; Astro-Databank "
        "считает по LMT. Вариант — время Штутгарта",
        regions=("wurttemberg",), offset_h=(36 * 60 + 42) / 3600, warn_unidentified=False),
)


def regional_rules_for(b: "BirthInput") -> list[dict]:
    """Справка: какие региональные правила относятся к зоне b.tz (для агента и документации)."""
    return [
        {"key": r.key, "start": r.start.isoformat(), "end": r.end.isoformat(), "action": r.action,
         "regions": list(r.regions), "note": r.note}
        for r in _REGIONAL_RULES if b.tz in r.zones
    ]


def normalize(b: BirthInput) -> NormalizedTime:
    """Перевести локальное время рождения в UTC и юлианский день (UT)."""
    if not b.has_time:
        raise ValueError("Время рождения не задано — метод требует время.")
    local = datetime(b.year, b.month, b.day, b.hour, b.minute or 0, b.second or 0)
    warnings: list[str] = []
    if b.tz is None:
        raise ValueError("Не задан часовой пояс (tz) или место (place).")

    fixed = _parse_fixed_offset(b.tz)
    if b.tz.upper() == "LMT":
        if b.lon is None:
            raise ValueError("Для LMT нужна долгота.")
        offset = timedelta(hours=b.lon / 15.0)
        source = "LMT(longitude)"
    elif fixed is not None:
        offset = fixed
        source = "fixed"
    else:
        z = ZoneInfo(b.tz)
        aware = local.replace(tzinfo=z, fold=b.fold)
        offset = aware.utcoffset()
        source = "tzdb"
        abbr = aware.tzname() or ""
        dst = aware.dst() or timedelta(0)
        mean_time_city = False
        if abbr in _RU_EMPIRE_MEAN_TIME.get(b.tz, set()):
            # подставляем, только если база tzdb (без летнего сдвига) = LMT города-эталона (±60 с);
            # Москва 1916-07-03…1919-07-01 (2:31:19 = Петроград+30 мин) остаётся как в tzdb
            zone_lmt = datetime(1800, 1, 1, tzinfo=z).utcoffset()
            base = aware.utcoffset() - (dst if dst > timedelta(0) else timedelta(0))
            mean_time_city = abs((base - zone_lmt).total_seconds()) <= 60
            if not mean_time_city:
                warnings.append(
                    f"Дореформенное время {abbr} по tzdb относится к городу-эталону зоны; "
                    "для другого населённого пункта смещение ⚠ не подтверждено."
                )
        if abbr == "LMT" or mean_time_city:
            if b.lon is not None:
                # летний сдвиг 1917–1919 (MST/MDST/LST) сохраняем, базу заменяем на LMT места
                offset = timedelta(hours=b.lon / 15.0) + (dst if dst > timedelta(0) else timedelta(0))
                source = "LMT(longitude)"
                warnings.append(
                    "На дату рождения поясное время ещё не введено: использовано местное "
                    "среднее время по долготе места рождения"
                    + (f" (tzdb: {abbr} {fmt_offset(aware.utcoffset().total_seconds() / 3600)})." if mean_time_city else ".")
                )
                if mean_time_city and local >= _NATIONAL_MEAN_TIME_FROM.get(b.tz, datetime.max):
                    # Независимые Латвия (1918–1926) и Эстония (1919–1921): время столицы могло быть
                    # законным для всей страны (Byalokoz 1919: «Latvia was 1:36:34», tzdb europe).
                    warnings.append(
                        f"⚠ В {local.year} г. {abbr} могло быть законным временем всей страны, а не "
                        "только столицы: для другого населённого пункта посчитайте также вариант "
                        f"tz='{fmt_offset_hms(aware.utcoffset())}'."
                    )
            else:
                warnings.append(f"Дата до введения поясного времени, долгота неизвестна: LMT столицы зоны ({abbr}).")
        # региональные исключения tzdb (KB 00, §3.3, табл. 4.11)
        corrected, rule_warnings, alternatives = _apply_regional_rules(b, local, offset)
        if corrected is not None:
            offset, source = corrected, "regional_exception"
        else:
            # проверка на несуществующее/неоднозначное время (при исправлении региональным правилом
            # перевода часов в этом регионе не было — проверка не нужна)
            other = local.replace(tzinfo=z, fold=1 - b.fold)
            if other.utcoffset() != aware.utcoffset():
                roundtrip = aware.astimezone(timezone.utc).astimezone(z).replace(tzinfo=None)
                if roundtrip != local:
                    warnings.append("Указанное время не существовало (весенний перевод часов) — уточните.")
                else:
                    warnings.append("Указанное время неоднозначно (осенний перевод часов): взят fold=%d." % b.fold)
                alternatives.append(_alternative(local, other.utcoffset(), f"fold={1 - b.fold}: другая сторона перевода часов"))
            if dst > timedelta(0):
                # zoneinfo.dst() выводится эвристически: для двойного летнего времени берём 2 ч по аббревиатуре
                hours = 2 if abbr in _DOUBLE_SUMMER else dst.total_seconds() / 3600
                kind = "двойное летнее" if abbr in _DOUBLE_SUMMER else "летнее"
                warnings.append(
                    f"Действовало {kind} время ({abbr}, {fmt_offset(aware.utcoffset().total_seconds() / 3600)}): "
                    f"+{hours:g} ч к поясному."
                )
        warnings.extend(rule_warnings)
        utc = (local - offset).replace(tzinfo=timezone.utc)
        return NormalizedTime(local, utc, offset.total_seconds() / 3600.0, source, julian_day_ut(utc),
                              warnings, alternatives)

    utc = (local - offset).replace(tzinfo=timezone.utc)
    jd = julian_day_ut(utc)
    return NormalizedTime(local, utc, offset.total_seconds() / 3600.0, source, jd, warnings)


def _alternative(local: datetime, offset: timedelta, reason: str) -> dict:
    utc = (local - offset).replace(tzinfo=timezone.utc)
    return {"utc_offset_hours": offset.total_seconds() / 3600.0, "tz": fmt_offset_hms(offset),
            "utc": utc.isoformat(), "jd_ut": julian_day_ut(utc), "reason": reason}


def _apply_regional_rules(b: BirthInput, local: datetime, tzdb_offset: timedelta
                          ) -> tuple[timedelta | None, list[str], list[dict]]:
    """Применить _REGIONAL_RULES: (исправленное смещение или None, предупреждения, альтернативы)."""
    region = identify_region(b)
    corrected: timedelta | None = None
    warnings: list[str] = []
    alternatives: list[dict] = []
    for r in _REGIONAL_RULES:
        if b.tz not in r.zones or not (r.start <= local < r.end):
            continue
        if region is not None and region in r.exclude:
            continue
        if r.regions:
            known = region in r.regions
            if region is not None and not known:
                continue                    # регион опознан, правило не о нём
            if not known and not r.warn_unidentified:
                continue
        else:
            known = True                    # правило на всю зону
        alt = r.alternative(local, tzdb_offset)
        if alt == tzdb_offset:
            continue
        if r.action == "correct" and known and corrected is None:
            corrected = alt
            warnings.append(
                f"⚠ Региональное исключение tzdb: {r.note}. Использовано {fmt_offset_hms(alt)}; "
                f"по tzdb было бы {fmt_offset_hms(tzdb_offset)} (вариант tz='{fmt_offset_hms(tzdb_offset)}')."
            )
            alternatives.append(_alternative(local, tzdb_offset, f"tzdb без регионального исключения ({r.key})"))
        else:
            prefix = "" if known else "Если место рождения относится к перечисленным территориям: "
            warnings.append(
                f"⚠ {prefix}{r.note}. Посчитайте также вариант tz='{fmt_offset_hms(alt)}' "
                f"(сейчас {fmt_offset_hms(tzdb_offset)} по tzdb)."
            )
            alternatives.append(_alternative(local, alt, f"{r.key}: " + ("вариант источника" if known
                                                                         else "если регион из перечня")))
    return corrected, warnings, alternatives


def julian_day_ut(dt_utc: datetime) -> float:
    """Юлианский день (UT) по григорианскому календарю."""
    h = dt_utc.hour + dt_utc.minute / 60 + dt_utc.second / 3600 + dt_utc.microsecond / 3.6e9
    return swe.julday(dt_utc.year, dt_utc.month, dt_utc.day, h, swe.GREG_CAL)


def jd_to_utc(jd_ut: float) -> datetime:
    y, m, d, h = swe.revjul(jd_ut, swe.GREG_CAL)
    base = datetime(y, m, d, tzinfo=timezone.utc)
    return base + timedelta(hours=h)


def local_mean_time(utc: datetime, lon: float) -> datetime:
    """Местное среднее время (LMT) = UTC + долгота/15 ч."""
    return (utc + timedelta(hours=lon / 15.0)).replace(tzinfo=None)


def equation_of_time_minutes(jd_ut: float) -> float:
    """Уравнение времени (истинное − среднее солнечное), минуты."""
    return swe.time_equ(jd_ut) * 24 * 60


def true_solar_time(utc: datetime, lon: float) -> datetime:
    """Истинное солнечное время = LMT + уравнение времени."""
    jd = julian_day_ut(utc)
    return local_mean_time(utc, lon) + timedelta(minutes=equation_of_time_minutes(jd))


def fmt_offset(hours: float) -> str:
    sign = "+" if hours >= 0 else "-"
    total = round(abs(hours) * 60)
    return f"UTC{sign}{total // 60:02d}:{total % 60:02d}"


def fmt_offset_hms(offset: timedelta) -> str:
    """Смещение с секундами в виде, который принимает BirthInput.tz: 'UTC+01:36:34'."""
    sec = round(offset.total_seconds())
    sign = "+" if sec >= 0 else "-"
    sec = abs(sec)
    return f"UTC{sign}{sec // 3600:02d}:{sec % 3600 // 60:02d}:{sec % 60:02d}"
