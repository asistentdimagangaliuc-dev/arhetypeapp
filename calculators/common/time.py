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

    def __post_init__(self) -> None:
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


def _parse_fixed_offset(tz: str) -> timedelta | None:
    s = tz.strip().upper().replace("GMT", "UTC")
    if not s.startswith("UTC"):
        return None
    rest = s[3:]
    if not rest:
        return timedelta(0)
    sign = -1 if rest[0] == "-" else 1
    rest = rest.lstrip("+-")
    if ":" in rest:
        h, m = rest.split(":")
    else:
        h, m = rest, "0"
    return sign * timedelta(hours=int(h), minutes=int(m))


def normalize(b: BirthInput) -> NormalizedTime:
    """Перевести локальное время рождения в UTC и юлианский день (UT)."""
    if not b.has_time:
        raise ValueError("Время рождения не задано — метод требует время.")
    local = datetime(b.year, b.month, b.day, b.hour, b.minute or 0)
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
        if aware.tzname() == "LMT":
            if b.lon is not None:
                offset = timedelta(hours=b.lon / 15.0)
                source = "LMT(longitude)"
                warnings.append(
                    "На дату рождения поясное время ещё не введено: использовано местное "
                    "среднее время по долготе места рождения."
                )
            else:
                warnings.append("Дата до введения поясного времени, долгота неизвестна: LMT столицы зоны.")
        # проверка на несуществующее/неоднозначное время
        other = local.replace(tzinfo=z, fold=1 - b.fold)
        if other.utcoffset() != aware.utcoffset():
            roundtrip = aware.astimezone(timezone.utc).astimezone(z).replace(tzinfo=None)
            if roundtrip != local:
                warnings.append("Указанное время не существовало (весенний перевод часов) — уточните.")
            else:
                warnings.append("Указанное время неоднозначно (осенний перевод часов): взят fold=%d." % b.fold)
        if aware.dst() and aware.dst() != timedelta(0):
            warnings.append(f"Действовало летнее время (DST {aware.dst()}).")

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
