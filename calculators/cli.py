"""Единая точка входа: python -m calculators <метод|all> [параметры].

Примеры:
  python -m calculators all --date 1990-05-15 --time 14:30 --place Москва --gender female \
      --name "Иванова Анна Сергеевна"
  python -m calculators bazi --date 1984-02-04 --time 23:30 --place Москва --gender male
  python -m calculators destiny_matrix --date 2004-02-29
  python -m calculators western --date 1879-03-14 --time 11:30 --tz LMT --lat 48.4011 --lon 9.9876
"""
from __future__ import annotations

import argparse
import importlib
import json
import sys
import traceback

from .common.time import BirthInput, fmt_offset, normalize

# метод -> (модуль, нужно ли время/место)
METHODS: dict[str, tuple[str, str]] = {
    "bazi":           ("calculators.bazi",           "time+place"),
    "ziwei":          ("calculators.ziwei",          "time+gender"),
    "ninestar":       ("calculators.ninestar",       "date"),
    "human_design":   ("calculators.human_design",   "time+place"),
    "gene_keys":      ("calculators.gene_keys",      "time+place"),
    "western":        ("calculators.western",        "time+place"),
    "jyotish":        ("calculators.jyotish",        "time+place"),
    "pythagoras":     ("calculators.pythagoras",     "date"),
    "alexandrov":     ("calculators.alexandrov",     "date"),
    "destiny_matrix": ("calculators.destiny_matrix", "date"),
    "numerology":     ("calculators.numerology",     "date(+name)"),
    "tarot_loshu":    ("calculators.tarot_loshu",    "date"),
    "tzolkin":        ("calculators.tzolkin",        "date"),
    "syutsay":        ("calculators.syutsay",        "date"),
    "typology":       ("calculators.typology",       "questionnaire (по дате не вычисляется)"),
    "qimen":          ("calculators.qimen",          "time+place"),
    "liuren":         ("calculators.liuren",         "time+place"),
    "forecast_western": ("calculators.forecast_western", "time+place (+--opt on_date=YYYY-MM-DD)"),
    "forecast_eastern": ("calculators.forecast_eastern", "date+time+place+gender (+--opt on_date=YYYY-MM-DD)"),
}


def _parse_args(argv: list[str]) -> argparse.Namespace:
    p = argparse.ArgumentParser(prog="python -m calculators", description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("method", help="метод из списка или 'all' / 'list' / 'time'")
    p.add_argument("--date", help="YYYY-MM-DD (григорианский календарь!)")
    p.add_argument("--time", help="HH:MM или HH:MM:SS местного гражданского времени")
    p.add_argument("--calendar", choices=["gregorian", "julian"], default="gregorian",
                   help="julian — дата по старому стилю (Россия до 14.02.1918), будет переведена")
    p.add_argument("--place", help="город из справочника common/places.py")
    p.add_argument("--tz", help="IANA-зона (Europe/Moscow), UTC+03:00 или LMT")
    p.add_argument("--region", help="регион на дату рождения (напр. «Татарская АССР») — для региональных "
                                    "исключений, которых нет в tzdb (KB 00, табл. 4.11)")
    p.add_argument("--lat", type=float)
    p.add_argument("--lon", type=float, help="восточная долгота положительная")
    p.add_argument("--gender", choices=["male", "female"])
    p.add_argument("--name", help="ФИО для нумерологии")
    p.add_argument("--opt", action="append", default=[],
                   help="опция метода key=value (можно несколько), напр. --opt zi_hour=early; "
                        "для 'all' — с префиксом метода: --opt bazi.solar_time=clock")
    return p.parse_args(argv)


def _options(pairs: list[str]) -> dict:
    out: dict = {}
    for pair in pairs:
        k, _, v = pair.partition("=")
        if v.lower() in ("true", "false"):
            out[k] = v.lower() == "true"
        else:
            try:
                out[k] = int(v)
            except ValueError:
                try:
                    out[k] = float(v)
                except ValueError:
                    out[k] = v
    return out


def build_input(a: argparse.Namespace) -> BirthInput:
    if not a.date:
        raise SystemExit("--date обязателен")
    y, m, d = (int(x) for x in a.date.split("-"))
    hh = mm = None
    ss = 0
    if a.time:
        parts = [int(x) for x in a.time.split(":")]
        hh, mm = parts[0], parts[1]
        ss = parts[2] if len(parts) > 2 else 0
    b = BirthInput(y, m, d, hh, mm, tz=a.tz, lat=a.lat, lon=a.lon, place=a.place,
                   gender=a.gender, name=a.name, second=ss, calendar=a.calendar, region=a.region)
    if a.place and b.lat is None:
        raise SystemExit(f"Место «{a.place}» нет в справочнике common/places.py — передайте --lat --lon [--tz].")
    if b.has_time and b.tz is None:
        raise SystemExit("Время задано, но нет часового пояса: укажите --place, или --lat/--lon, или --tz.")
    return b


def run_method(name: str, b: BirthInput, options: dict | None = None) -> dict:
    module_name, _ = METHODS[name]
    mod = importlib.import_module(module_name)
    return mod.calculate(b, **(options or {}))


def main(argv: list[str] | None = None) -> int:
    a = _parse_args(sys.argv[1:] if argv is None else argv)
    if a.method == "list":
        for k, (_, req) in METHODS.items():
            print(f"{k:15s} {req}")
        return 0
    b = build_input(a)
    opts = _options(a.opt)
    result: dict = {}
    if a.method == "time":
        n = normalize(b)
        result = {"utc": n.utc.isoformat(), "offset": fmt_offset(n.utc_offset_hours),
                  "offset_source": n.offset_source, "jd_ut": n.jd_ut, "warnings": n.warnings,
                  "alternatives": n.alternatives}
    elif a.method == "all":
        per_method: dict[str, dict] = {}
        for k, v in opts.items():
            meth, dot, key = k.partition(".")
            if dot and meth in METHODS:
                per_method.setdefault(meth, {})[key] = v
        for name in METHODS:
            try:
                result[name] = run_method(name, b, per_method.get(name, {}))
            except Exception as e:  # метод не применим к этим входным данным
                result[name] = {"error": f"{type(e).__name__}: {e}"}
    elif a.method in METHODS:
        try:
            result = run_method(a.method, b, opts)
        except Exception:
            traceback.print_exc()
            return 1
    else:
        raise SystemExit(f"Неизвестный метод {a.method}. См. python -m calculators list")
    print(json.dumps(result, ensure_ascii=False, indent=2, default=str))
    return 0
