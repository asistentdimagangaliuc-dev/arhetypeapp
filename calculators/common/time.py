"""Нормализация входных данных рождения: локальное время -> UTC -> юлианский день.

Ключевые правила (подробно — knowledge-base/00-input-normalization.md):
* Историческое смещение берётся из базы IANA tzdb (zoneinfo), а не «текущее»:
  СССР знал декретное время (с 1930), летнее время 1981–1991, отмену декрета 1991,
  «вечное летнее» 2011–2014 и возврат 2014 — tzdb всё это хранит.
* Если на дату рождения в зоне действовало LMT (до введения поясного времени),
  считаем местное среднее время по долготе места (lon/15 ч), а не LMT столицы зоны.
* Неоднозначное (осенний перевод часов) и несуществующее (весенний) время
  помечаются предупреждением; по умолчанию берётся fold=0 (первое вхождение).
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import date, datetime, time, timedelta, timezone
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
    offset_source: str              # "tzdb", "fixed", "LMT(longitude)"
    jd_ut: float                    # юлианский день UT
    warnings: list[str] = field(default_factory=list)


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
        # проверка на несуществующее/неоднозначное время
        other = local.replace(tzinfo=z, fold=1 - b.fold)
        if other.utcoffset() != aware.utcoffset():
            roundtrip = aware.astimezone(timezone.utc).astimezone(z).replace(tzinfo=None)
            if roundtrip != local:
                warnings.append("Указанное время не существовало (весенний перевод часов) — уточните.")
            else:
                warnings.append("Указанное время неоднозначно (осенний перевод часов): взят fold=%d." % b.fold)
        if dst > timedelta(0):
            # zoneinfo.dst() выводится эвристически: для двойного летнего времени берём 2 ч по аббревиатуре
            hours = 2 if abbr in _DOUBLE_SUMMER else dst.total_seconds() / 3600
            kind = "двойное летнее" if abbr in _DOUBLE_SUMMER else "летнее"
            warnings.append(
                f"Действовало {kind} время ({abbr}, {fmt_offset(aware.utcoffset().total_seconds() / 3600)}): "
                f"+{hours:g} ч к поясному."
            )

    utc = (local - offset).replace(tzinfo=timezone.utc)
    jd = julian_day_ut(utc)
    return NormalizedTime(local, utc, offset.total_seconds() / 3600.0, source, jd, warnings)


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
