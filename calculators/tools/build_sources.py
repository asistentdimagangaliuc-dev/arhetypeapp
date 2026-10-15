"""Собирает knowledge-base/sources.md — индекс всех URL, процитированных в документах методов.

Запуск: .venv/bin/python -m calculators.tools.build_sources
"""
from __future__ import annotations

import glob
import os
import re

KB = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "knowledge-base"))
URL_RE = re.compile(r"https?://[^\s)\]>\"'`|]+")


def main() -> None:
    lines = [
        "# Источники базы знаний",
        "",
        "Каждый документ метода содержит раздел «Источники» с оценкой надёжности каждого источника и раздел "
        "«Протокол проверки» (что именно было независимо перепроверено). Здесь — сводный индекс всех процитированных "
        "URL по модулям (сгенерирован `calculators/tools/build_sources.py`).",
        "",
        "**Шкала надёжности, используемая в документах:**",
        "",
        "| Уровень | Что это | Как использовать |",
        "|---|---|---|",
        "| первоисточник | книга/сайт основателя системы, официальный калькулятор школы, астрономические службы (USNO, HKO), tzdb | правило считается установленным |",
        "| школа | сайты и курсы признанных практиков школы | правило школы; при расхождениях — указывать вариант |",
        "| калькулятор | выдача известных калькуляторов (сверка чисел) | годится для тестовых векторов, не для правил |",
        "| вторичный | статьи, блоги, форумы, журналистика | только как подсказка; помечено ⚠, если не подтверждено |",
        "",
        "Ограничения проверки: часть сайтов (astro.com / Astro-Databank, ladini.ru, некоторые китайские ресурсы) "
        "была недоступна из среды исследования (защита от ботов, HTTP 503); соответствующие утверждения в документах "
        "подтверждены через копии/другие источники или помечены ⚠.",
        "",
    ]
    total = 0
    for path in sorted(glob.glob(os.path.join(KB, "[0-9][0-9]-*.md"))):
        name = os.path.basename(path)
        with open(path, encoding="utf-8") as f:
            text = f.read()
        title = next((ln[2:].strip() for ln in text.splitlines() if ln.startswith("# ")), name)
        urls = []
        for u in URL_RE.findall(text):
            u = u.rstrip(".,;:")
            if u not in urls:
                urls.append(u)
        total += len(urls)
        lines += [f"## [{name}]({name}) — {title}", "", f"Уникальных URL: {len(urls)}", ""]
        lines += [f"- <{u}>" for u in urls]
        lines.append("")
    lines.insert(4, f"Всего уникальных ссылок по модулям: **{total}**.")
    lines.insert(5, "")
    with open(os.path.join(KB, "sources.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print("sources:", total)


if __name__ == "__main__":
    main()
