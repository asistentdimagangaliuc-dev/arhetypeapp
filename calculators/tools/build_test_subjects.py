"""Генерирует knowledge-base/test-subjects.md — сводку всех методов для эталонных персон T1–T4.

Запуск из корня репозитория:  .venv/bin/python -m calculators.tools.build_test_subjects
"""
from __future__ import annotations

import os

from calculators.cli import METHODS, run_method
from calculators.common.time import BirthInput, fmt_offset, normalize

SUBJECTS = {
    "T1": dict(b=BirthInput(1990, 5, 15, 14, 30, place="Москва", gender="female", name="Иванова Анна Сергеевна"),
               label="ж, Иванова Анна Сергеевна, 15.05.1990 14:30, Москва"),
    "T2": dict(b=BirthInput(1984, 2, 4, 23, 30, place="Москва", gender="male", name="Петров Дмитрий Олегович"),
               label="м, Петров Дмитрий Олегович, 04.02.1984 23:30, Москва"),
    "T3": dict(b=BirthInput(2004, 2, 29, 8, 15, place="Санкт-Петербург", gender="female",
                            name="Смирнова Мария Александровна"),
               label="ж, Смирнова Мария Александровна, 29.02.2004 08:15, Санкт-Петербург"),
    "T4": dict(b=BirthInput(1879, 3, 14, 11, 30, place="Ульм", tz="LMT", gender="male", name="Albert Einstein"),
               label="м, Albert Einstein, 14.03.1879 11:30 LMT, Ульм"),
}


PLANET_RU = {"sun": "Солнце", "moon": "Луна", "mars": "Марс", "mercury": "Меркурий", "jupiter": "Юпитер",
             "venus": "Венера", "saturn": "Сатурн", "rahu": "Раху", "ketu": "Кету"}


def _g(d, *path, default="—"):
    for p in path:
        if isinstance(d, dict) and p in d:
            d = d[p]
        elif isinstance(d, list) and isinstance(p, int) and p < len(d):
            d = d[p]
        else:
            return default
    return d


def summarize(r: dict) -> dict[str, str]:
    out: dict[str, str] = {}
    bz = r["bazi"]
    out["Ба-цзы (по умолчанию: истинное солнечное время, поздний Цзы)"] = (
        f"{_g(bz, 'chart')}; господин дня {_g(bz, 'day_master', 'cn')} ({_g(bz, 'day_master', 'name_ru')})")
    zw = r["ziwei"]
    ming = next((p for p in _g(zw, "palaces", default=[]) if p.get("name") == "命宫"), {})
    stars = ", ".join(s["star"] for s in ming.get("major_stars", [])) or "пусто"
    out["Цзы Вэй Доу Шу"] = (f"Мин {_g(zw, 'ming_palace', 'stem_branch')} ({stars}); Шэнь {_g(zw, 'body_palace', 'branch')}; "
                            f"{_g(zw, 'bureau', 'name')} ({_g(zw, 'bureau', 'name_ru')})")
    ns = r["ninestar"]
    out["Девятизвёздная Ки"] = (f"{_g(ns, 'nine_star_ki', 'notation')} — год {_g(ns, 'nine_star_ki', 'principal', 'ru')}, "
                               f"месяц {_g(ns, 'nine_star_ki', 'month', 'ru')}")
    out["Число Гуа"] = f"{_g(ns, 'gua', 'number')} ({_g(ns, 'gua', 'group_ru')})"
    out["Китайский зодиак (по лунному НГ / по Личуню)"] = (
        f"{_g(ns, 'zodiac_lunar', 'ganzhi')} {_g(ns, 'zodiac_lunar', 'element')} {_g(ns, 'zodiac_lunar', 'animal')} / "
        f"{_g(ns, 'zodiac_solar', 'ganzhi')} {_g(ns, 'zodiac_solar', 'element')} {_g(ns, 'zodiac_solar', 'animal')}")
    hd = r["human_design"]
    out["Human Design"] = (f"{_g(hd, 'type', 'name_ru')}, авторитет: {_g(hd, 'authority', 'name_ru')}, профиль "
                          f"{_g(hd, 'profile', 'profile')}, {_g(hd, 'definition', 'name_ru')}; "
                          f"{_g(hd, 'incarnation_cross', 'name_ru')}")
    gk = r["gene_keys"]["spheres"]
    out["Gene Keys (Дело жизни / Эволюция / Сияние / Предназначение)"] = " / ".join(
        _g(gk, s, "key_line") for s in ("lifes_work", "evolution", "radiance", "purpose"))
    w = r["western"]
    out["Западная астрология"] = ", ".join(str(v) for v in _g(w, "summary", default={}).values())
    jy = r["jyotish"]
    out["Джйотиш (Лахири)"] = (f"Лагна {_g(jy, 'lagna', 'position')}; Луна в {_g(jy, 'moon_sign', 'sign_ru')}, "
                              f"накшатра {_g(jy, 'janma_nakshatra', 'name_ru')} пада {_g(jy, 'janma_nakshatra', 'pada')}; "
                              f"остаток даши {PLANET_RU.get(_g(jy, 'dasha', 'balance', 'lord'), '—')} {_g(jy, 'dasha', 'balance', 'ymd')}")
    py = r["pythagoras"]["working_numbers"]
    out["Квадрат Пифагора (рабочие числа)"] = f"{py['first']}, {py['second']}, {py['third']}, {py['fourth']}"
    py_grid = r["pythagoras"].get("grid")
    if isinstance(py_grid, list):
        out["Квадрат Пифагора (сетка 1-4-7 / 2-5-8 / 3-6-9)"] = " | ".join(
            " ".join(c or "—" for c in row) for row in py_grid)
    al = r["alexandrov"]
    aw = al["working_numbers"]
    out["Квадрат Александрова"] = (f"{aw['first']}, {aw['second']}, {aw['third']}, {aw['fourth']}; "
                                  f"число жизни {_g(al, 'life_number')}")
    dm = r["destiny_matrix"]["points"]
    out["Матрица судьбы (A, B, C, D, E)"] = f"{dm['A']}, {dm['B']}, {dm['C']}, {dm['D']}, {dm['E']}"
    nn = r["numerology"]
    lp = _g(nn, "date_numbers", "life_path", "notation")
    lpm = _g(nn, "date_numbers", "life_path_by_method", default={})
    alt = ", ".join(f"{k}: {v.get('notation')}" for k, v in lpm.items()) if isinstance(lpm, dict) else ""
    out["Нумерология: число жизненного пути"] = f"{lp} ({alt})"
    out["Нумерология имени (выражение / душа / личность)"] = " / ".join(
        str(_g(nn, "name_numbers", k, "notation")) for k in ("expression", "soul_urge", "personality"))
    tl = r["tarot_loshu"]
    out["Арканы Таро (Грир: личность / душа)"] = (
        f"{_g(tl, 'tarot', 'birth_cards', 'personality', 'number')} {_g(tl, 'tarot', 'birth_cards', 'personality', 'name_ru')} / "
        f"{_g(tl, 'tarot', 'birth_cards', 'soul', 'number')} {_g(tl, 'tarot', 'birth_cards', 'soul', 'name_ru')}")
    out["Ведическая нумерология (мулянк / бхагьянк)"] = (
        f"{_g(tl, 'vedic', 'moolank', 'number')} / {_g(tl, 'vedic', 'bhagyank', 'number')}")
    tz = r["tzolkin"]
    out["Цолькин Dreamspell"] = str(_g(tz, "summary", "dreamspell"))
    out["Цолькин классический (GMT 584283)"] = str(_g(tz, "summary", "classic"))
    sy = r["syutsay"]
    out["Сюцай (сознание / миссия)"] = (f"{_g(sy, 'consciousness', 'number')} ({_g(sy, 'consciousness', 'planet')}) / "
                                       f"{_g(sy, 'mission', 'number')} ({_g(sy, 'mission', 'planet')})")
    out["Соционика / эннеаграмма"] = "по дате не вычисляются — нужен опросник (модуль 14)"
    return out


def main() -> None:
    results = {}
    times = {}
    for tid, s in SUBJECTS.items():
        b = s["b"]
        n = normalize(b)
        times[tid] = f"UTC {n.utc:%Y-%m-%d %H:%M:%S} ({fmt_offset(n.utc_offset_hours)}, {n.offset_source}); JD {n.jd_ut:.5f}"
        r = {}
        for m in METHODS:
            r[m] = run_method(m, b, {})
        results[tid] = summarize(r)
    rows = list(next(iter(results.values())).keys())
    lines = [
        "# Эталонные персоны: сводка результатов всех методов",
        "",
        "Файл сгенерирован скриптом `calculators/tools/build_test_subjects.py` из эталонных калькуляторов "
        "(варианты школ — по умолчанию; альтернативы и все промежуточные шаги — в документах методов и в JSON "
        "`python -m calculators all …`). Используйте эту таблицу как контрольную: если ваш ручной расчёт для T1–T4 "
        "не совпадает с ней, ищите ошибку по разделу «Контрольные точки» соответствующего документа.",
        "",
    ]
    for tid, s in SUBJECTS.items():
        lines.append(f"- **{tid}** — {s['label']}. {times[tid]}")
    lines += ["", "| Метод | " + " | ".join(SUBJECTS) + " |", "|---|" + "---|" * len(SUBJECTS)]
    for row in rows:
        cells = [results[t][row].replace("|", "\\|") for t in SUBJECTS]
        lines.append(f"| {row} | " + " | ".join(cells) + " |")
    lines += [
        "",
        "Примечания:",
        "- T2: по часам 23:30 — поздний час Цзы, по истинному солнечному времени 22:46 — час 亥 (Хай); Ба-цзы и Цзы Вэй "
        "по умолчанию используют истинное солнечное время, варианты — в документах 01 и 02.",
        "- T3: рождение 29.02 — Dreamspell использует правило полудня (до 12:00 → кин 28.02).",
        "- T4: время — местное среднее (LMT) Ульма; AstroSage и ряд сайтов ошибочно считают его по CET (UTC+1).",
        "- T4: число жизненного пути 6 (по компонентам) vs 33 (сумма всех цифр) — обе версии встречаются в литературе.",
        "",
    ]
    path = os.path.join(os.path.dirname(__file__), "..", "..", "knowledge-base", "test-subjects.md")
    with open(os.path.abspath(path), "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print("written", os.path.abspath(path))


if __name__ == "__main__":
    main()
