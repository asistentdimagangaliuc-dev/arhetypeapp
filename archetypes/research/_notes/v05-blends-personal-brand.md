# Протокол независимой проверки: 03-blends.md и 05-personal-brand.md

> **Дата проверки:** 2026-10-16. **Проверяющий:** независимый проверяющий, в сборе и написании не участвовал.
> **Объект:** `research/03-blends.md` («Смешанные профили и пропорции») и `research/05-personal-brand.md` («Архетипы в блогах и личном бренде»).
> **Рамка.** Только исследование. Рекомендаций по продукту в протоколе нет. Заметки `_notes/r*.md` прочитаны выборочно и не менялись.

---

## 1. Методика

1. **Первоисточники и надёжные базы.**
   - Научные работы: Crossref API (`api.crossref.org/works/<DOI>`), PubMed E-utilities (аннотации), PMC, OpenAlex, полные тексты в открытом доступе (диссертация Spangenberg, PDF CHI 2022 и USENIX 2023, PMAI Manual).
   - Книга Марк и Пирсон: публичный поиск по тексту библиотечного экземпляра Internet Archive через `openlibrary.org/search/inside.json`. Это короткие OCR-фрагменты, страниц он почти не даёт.
   - Сайты авторов и школ: страницы скачивались `curl`, текст извлекался скриптом и искался по ключевым фразам. Страницы, закрытые для `curl`, открывались через WebFetch.
   - Википедия: WebFetch, потому что API отвечал 429.
2. **Поиск контрпримеров** к утверждению «схемы 50/30/20, 60/30/10, 70/20/10 не найдены»: пять запросов WebSearch (три на английском, два на русском) и чтение уже процитированных страниц Iconic Fox.
3. **Массовая проверка ссылок.** Из обоих файлов извлечены все уникальные URL (115 и 165). Каждый запрошен `curl -L` с обычным User-Agent; записан HTTP-код. Для ответов 403/000 сделана повторная попытка через WebFetch или найден альтернативный легальный адрес (PubMed, PMC, Crossref).
4. **Правила.**
   - Длина цитат: скрипт искал фрагменты в «…» и “…” длиннее 18 слов; вручную разобраны найденные.
   - Нумерация: скрипт сверял все [n] в тексте со списками источников.
   - Отдельно просмотрены неавторизованные копии, пометки «⚠», «оценка исследования, не из источника», рекламные метки и следы проектирования продукта.
5. **Правки** — минимальные, прямо в файлах. Структура и нумерация источников сохранены. Новые источники добавлены в конец: в 03 — [96], [97], в 05 — [127]. Личные данные в запросы не включались, тесты не проходились, регистраций не было.

---

## 2. Проверка утверждений

Вердикты: **подтверждено** / **исправлено** / **помечено ⚠** / **удалено**. «03» и «05» — файлы.

| № | Файл | Утверждение | Чем проверено (URL) | Вердикт | Комментарий |
|---|---|---|---|---|---|
| 1 | 03, 05 | Марк и Пирсон: «identifying solidly with one—and only one—archetype» | https://openlibrary.org/search/inside.json?q=%22identifying%20solidly%22 (экземпляр `herooutlawbuildi0000mark`) | подтверждено | Текст подтверждён; с. 42 известна только из r08, в 05 добавлено «⚠ стр.» |
| 2 | 03, 05 | BAV: 50 брендов, 1993–1999, две равные группы, порог 10 %, MVA «rose by 97% more», EVA «66% greater» | https://www.goodreads.com/work/quotes/347790 ; https://researchscape.com/blog/are-brands-people-or-religions | подтверждено | Все числа совпадают. Researchscape добавляет «over 120,000 consumers» и «over 55 attributes per brand»; расхождение с «около 48 атрибутов» внесено в 03 с ⚠ |
| 3 | 03 | «cumulative distribution score for each archetype (the percentile…» | openlibrary search inside, запрос «cumulative distribution score» | подтверждено | — |
| 4 | 03 | «single coherent archetype», «pick some characteristics from column A…» (раньше «легально не сверено ⚠») | openlibrary search inside | исправлено | Оба фрагмента найдены; ⚠ о тексте снята, «⚠ стр.» оставлена |
| 5 | 03, 05 | Мадонна «always the outrageous Rebel» (раньше только по r08) | openlibrary search inside | подтверждено | Рядом колонтитул «2 PRIMAL ASSETS», это согласуется с с. 1–2; в 05 добавлено «⚠ стр.» |
| 6 | 03 | Ivory как владелец «category archetype» | openlibrary search inside | подтверждено частично | Фрагмент об Ivory найден; часть о Dove как «secondary» не найдена, оставлено ⚠ |
| 7 | 03 | Levi's «once a strong and clear Explorer», «seemed a bit lost» | openlibrary search inside | подтверждено | — |
| 8 | 03 | Леттерман: «Jester with Everyman/Regular Joe vulnerability» | openlibrary search inside | подтверждено | с. 162 только по r08 (⚠ стр.) |
| 9 | 03 | Harley-Davidson: «An Outlaw Masterpiece» | openlibrary search inside | подтверждено | — |
| 10 | 03 | PMAI: 3 «Inner Allies», 8 «Inner Treasure Chest», 1 «Blind Spot»; часто работают с двумя нижними | https://cdn.prod.website-files.com/5fc7fbb375805cc285353295/65d8ffa286160b97014347f7_PMAI_Manual_2021-1.pdf (гл. 2, с. 6–8) | подтверждено | — |
| 11 | 03, 05 | PMAI: процентили против среднего и SD базы «over 13,000 records»; в отчёте числами не показываются; «rather arbitrary», «Like Goldilocks» | PMAI Manual, гл. 2 | подтверждено | — |
| 12 | 03, 05 | PMAI: 72 пункта по 6, шкала Ликерта 5; альфы ≈0,58–0,82; тест-ретеста нет; Seeker–Magician r = 0,51; база 5 000 | PMAI Manual, гл. 3–5 | подтверждено | Минимальная альфа Revolutionary в таблице напечатана как «.0583» (опечатка издателя, по смыслу 0,583) |
| 13 | 03 | Переименования Orphan→Realist, Innocent→Idealist, Destroyer→Revolutionary; дополнительные пары Realist–Idealist, Revolutionary–Creator | PMAI Manual, гл. 3, с. 10–11 | подтверждено | Порядок таблицы даёт и пары Seeker–Lover, Magician–Sage, Ruler–Jester, как и сказано в файле (с ⚠) |
| 14 | 03 | Сайт Пирсон: «three reported in your PMAI results as most active», «in the shadows, awaiting expression, idealized» | https://carolspearson.com/about/archetypal-assessment-pearson-marr-archetype-indicator-r | подтверждено | — |
| 15 | 03 | Переименования «to make all of them equally positive» (май 2020) | https://www.carolspearson.com/wp-imort-2/pmai-re-release | подтверждено | — |
| 16 | 03 | StoryWell: нижний архетип — «Overlooked Ally» | https://www.storywell.com/purchase-the-pmai.htm | подтверждено | Страница продажи — добавлена метка «рекламный» |
| 17 | 05 | Отдельный инструмент «IBM Kenexa» для «карьерного и лидерского применения» | https://www.carolspearson.com/about/archetypal-assessments | исправлено | На странице — IBM Kenexa Organizational Cultural Insight Survey для организационной культуры |
| 18 | 05 | Сайт называет PMAI «the world's first scientifically validated archetype assessment tool»; страница исследований без статистики | carolspearson.com/about/archetypal-assessments ; https://www.storywell.com/research-with-the-pearson-marr-assessment.htm | подтверждено | — |
| 19 | 03, 05 | Iconic Fox: «a core archetype that will represent a minimum of 70%…», «The other 30% is your influencer archetype», «spend it wisely» | https://iconicfox.com.au/brand-archetypes/ (curl, 2026-10-16) | подтверждено | Страница открылась; в разметке datePublished 2018-05-03, dateModified 2025-12-01 |
| 20 | 03 | Чек-лист Brand Master Academy (70/30, «70% Everyman, 30% Outlaw», «diluted or confused») «только по сводке сторонней копии» | https://brandmasteracademy.com/wp-content/uploads/2020/07/Brand-Archetype-Checklist.pdf | исправлено | Найден PDF на сайте самой академии (контакт stephen@iconicfox.com.au; создан 2018-05-14). ⚠ снята, URL добавлен в [26] |
| 21 | 03 | «Схемы 50/30/20, 60/30/10, 70/20/10 ни в одном проверенном источнике не найдены» | https://iconicfox.com.au/can-you-mix-brand-archetypes/ ; 5 запросов WebSearch | исправлено | **Контрпример:** Iconic Fox (2025-11-14) — основной «60-70% of brand expression», второй «20-30%», «tertiary influences (5-10%)». Добавлен источник [96]; правки в «Коротко», 2, 3.1, 3.4, 3.5, 5.3, 8, вопрос 7. Схема 50/30/20 не найдена |
| 22 | 05 | Iconic Fox: только core ≥70 % + influencer 30 % | iconicfox.com.au/can-you-mix-brand-archetypes/ | исправлено | Добавлена версия 2025 года (60–70 / 20–30 / 5–10) в 1.1, 5.3 и [37] |
| 23 | 03, 05 | «Нет обоснования числа «2–3»» | https://alinaadt.ru/archetypes ; iconicfox.com.au/can-you-mix-brand-archetypes/ | исправлено | Обоснование данными нет, но утверждения есть: Адт — «очень редко выражен 1, а больше 3х для брендинга - ошибка»; Iconic Fox — «Most successful brands use 2-3 archetypes». Формулировка уточнена |
| 24 | 03 | Iconic Fox: Apple «broke through» как Outlaw, затем Creator | iconicfox.com.au/brand-archetypes/ ; https://en.wikipedia.org/wiki/Get_a_Mac | исправлено | Цитата исправлена на «breaking through with one and developing with another». Добавлено как оценка исследования: «Get a Mac» (2006–2009) шла позже «Think Different» (1997). Источник [97] |
| 25 | 03 | Происхождение «influencer»: «датировать не удалось» | разметка iconicfox.com.au ; PDF-метаданные чек-листа | исправлено | Указаны даты 2018-05-03 и 2018-05-14; в чек-листе слова «influencer» нет (⚠ для термина оставлена) |
| 26 | 03 | Spangenberg 2021: 242 / 200 / 157 участников MTurk; шкала 1–6; 18 «flexible» из 30, 12 «tightly defined»; «very little overlap»; «many brands are actually associated with multiple archetypes» | https://digital.lib.washington.edu/researchworks/bitstreams/4d33b25a-2369-446b-9147-3957e3ff0eb3/download (с. 17–25, табл. 4) | подтверждено | Добавлены данные табл. 4 по Harley-Davidson, Apple, Disney (6.1, 6.5) и то, что порог 10 % у Spangenberg — относительная разница |
| 27 | 03 | Dove Lover 4,63 / Innocent 4,60; Victoria's Secret Lover 4,88 / Creator 3,69 | Spangenberg, с. 23–24 | подтверждено | — |
| 28 | 03, 05 | Merlo, Eisingerich, Gillingwater, Cao (2023), *Business Horizons* 66(5): 615–629; более 2 400 брендов; «strong brands tend to leverage multiple archetypes at a time» | https://api.crossref.org/works/10.1016/j.bushor.2022.11.001 ; https://ideas.repec.org/a/eee/bushor/v66y2023i5p615-629.html | подтверждено | Crossref — 27 цитирований, OpenAlex — 28; OA-статус hybrid |
| 29 | 03 | «only 2 percent» — только во вторичном пересказе | https://myo.gelisim.edu.tr/en/akademik-department-public-relations-and-advertisement-news-how-to-use-archetypes-in-brand-positioning ; RePEc | подтверждено | В пересказе есть, в аннотации нет; ⚠ оставлена |
| 30 | 03 | Imperial (Merlo): «layering multiple archetypes…», «drive brand stories, create tension, develop intrigue», Harley «more of the Patriarch», Companion, Barbour «dominated by the Rebel», Dove «two opposing sides», «almost obsessively… brand schizophrenia», Engineer–Shaman / Engineer–Visionary, Land Rover, Jeep, Jaguar, Alfa Romeo | https://www.imperial.ac.uk/business-school/ib-knowledge/marketing/lessons-leaders-successful-brands-have-multiple-personalities/ | подтверждено | — |
| 31 | 03 | Feng и др., *JRIM* 2026, 20(4): 473–490; одна работа со вторичными данными + три эксперимента; Study 3 — «archetype consistency» как медиатор; Study 4 — «brand control» | https://api.crossref.org/works/10.1108/JRIM-02-2025-0084 | подтверждено | Онлайн с 2025-08-19 — добавлено в [88]. Страница Emerald отдаёт 403 автоматическому доступу |
| 32 | 03 | Allen & Brouer 2026, *JSBS* 36(2), концептуальная модель: синергия Sage–Creator, напряжение Sage–Innocent, «multi-archetype signaling», «schema incongruity» | https://api.crossref.org/works/10.53703/001c.157807 | подтверждено | — |
| 33 | 03 | Djakeli & True 2018, *Journal of Business* 6(1): 27–32; пилот на студентах Kennesaw State | https://api.crossref.org/works/10.31578/.v6i1.119 | подтверждено | — |
| 34 | 03 | Xara-Brasil и др. 2018, *Revista de Gestão* 25(2): 142–159 | https://api.crossref.org/works/10.1108/REGE-02-2018-0029 | подтверждено (выходные данные) | Содержание не перепроверялось |
| 35 | 03 | Faber & Mayer 2009: 100 судей, 156 стимулов, κ = 0,79 | http://mcd.woodbury.edu/wp-content/uploads/2016/02/Faber-Mayer-2009.pdf ; Crossref 10.1016/j.jrp.2008.11.003 | подтверждено | PDF лежит на сайте университета; статус размещения не установлен (это статья, не книга) |
| 36 | 03 | Paekivi & Karjus 2026: 57 видео с людьми-кодировщиками, архетипы ненадёжны «for both humans and machines» | https://arxiv.org/html/2606.16053v1 | подтверждено | — |
| 37 | 03 | Bechter и др. 2016, *Administrative Sciences* 6(2): 5 | Crossref 10.3390/admsci6020005 | подтверждено (выходные данные) | MDPI отдаёт 403; содержание (Hero и Magician) не перепроверено |
| 38 | 03 | Researchscape «отмечает, что детали метода не опубликованы» | https://researchscape.com/blog/are-brands-people-or-religions | исправлено | Автор метод не критикует: называет анализ количественным и оговаривается «the devil is in the details» |
| 39 | 03 | Kaye Putnam советует командам основателей «работать с тремя подтипами на архетип» | https://ebaqdesign.com/podcast/archetypes-branding (WebFetch) | исправлено | В расшифровке подтипов нет; есть «what your top two archetypes should be». Формулировка заменена |
| 40 | 03, 05 | Putnam: «My two archetypes are the magician and the sage»; «it's not a scientific framework. It's a useful framework»; «jumping off point» | https://logogeek.uk/podcast/branding-archetypes | подтверждено | — |
| 41 | 03, 05 | Квиз Putnam: «The strongest brands pair a primary and secondary archetype…»; обзор: «choose one deliberately (and commit to it)»; «psychology-backed personality» | https://kayeputnam.com/quiz/ ; https://kayeputnam.com/brand-archetypes/ | подтверждено | Квизу добавлена метка «рекламный» |
| 42 | 03 | Putnam: Patagonia «Maverick with an Explorer secondary» | https://kayeputnam.com/brand-archetypes/maverick | подтверждено | — |
| 43 | 03 | Марта Стюарт — Творец с «чертой Правителя» | https://kayeputnam.com/brand-archetypes/creator ; …/innocent | исправлено | В источнике — «makes order out of chaos»; «черта Правителя» помечена как оценка исследования. Добавлено, что Putnam называет Стюарт и среди «Real-life Innocents» |
| 44 | 03 | Digital Surgeons: «Everyman makes the Rebel feel attainable»; «Visionary, Rebel, Creator, Sage, and Caretaker» как цитаты | https://legacy.digitalsurgeons.com/thoughts/marketing/brand-archetypes/ | исправлено | Дословно: Everyman нужен, чтобы «bring the Rebel to reality, making it feel relatable and achievable». Вторая «цитата» — пересказ, кавычки сняты |
| 45 | 03 | Digital Surgeons: Apple Rebel / Sage / Caretaker по точкам контакта; «Warrior Monk», «Rebel Royal», «push and pull», «form and structure» | тот же URL | подтверждено | — |
| 46 | 03 | WPP BAV: «more interesting, engaging and successful», «a degree of tension» | https://wppbav.com/insights/brand-archetypes/ | подтверждено | Методики на странице нет |
| 47 | 03 | Umbrex: «Too many archetypes create incoherence», Caregiver + Sage «empathy and expertise» и др. | https://umbrex.com/resources/frameworks/marketing-frameworks/brand-archetypes-framework-jungian-archetypes/ | подтверждено | — |
| 48 | 03 | HubSpot: соседние архетипы смешиваются, пример Caregiver + Innocent | https://blog.hubspot.com/marketing/brand-archetypes | подтверждено | — |
| 49 | 03 | Moonb: Apple — Творец «с бунтарской жилкой»; второй архетип «в малых дозах» | https://www.moonb.io/blog/brand-archetypes | подтверждено | В оригинале «Creator with an Outlaw streak» |
| 50 | 03 | Myss: «unique combination of twelve archetypal patterns…»; главы «Reinventing the Wheel», «Creating Your Chart of Origin» | https://content.e-bookshelf.de/media/reading/L-535049-ae25abbe32.pdf | подтверждено | — |
| 51 | 03 | Название гл. 4 Мисс расходится (⚠) | там же, оглавление | исправлено | Глава 4 — «Speaking Archetypes: Your Four Principal Energy Companions»; ⚠ снята |
| 52 | 03, 05 | Галерея Мисс: «their other eight personal archetypes», «circle of twelve», Saboteur — «guardian of choice», «fear of inviting change», страхи «related to low self-esteem» | https://myss.com/wp-content/uploads/2015/07/Gallery-of-Archetypes.pdf | подтверждено | — |
| 53 | 03 | Колесо Мисс: дома «Personality, Ego», «Life Values»; «instead of the positions of the constellations» | https://myss.com/free-resources/sacred-contracts-and-your-archetypes/the-archetypal-wheel/ | подтверждено | — |
| 54 | 03 | Хартвелл: «both-and» not «either-or»; «I don't subscribe to there being a "best" or "right" set…» | https://www.archetypesinbranding.com/post/3questions | подтверждено | — |
| 55 | 03, 05 | Русская адаптация Пирсон–Марр: выборка 120 студентов, «малоинформативной» | https://www.sibscript.ru/jour/article/jats/1932 | подтверждено | — |
| 56 | 03 | Благодарности «Бомборы»: Пол Фокс и Эд Лебар из группы BAV Y&R | https://www.litres.ru/book/carol-s-pearson-2/geroy-i-buntar-kak-ispolzovat-arhetipy-na-polzu-biznesu-74458861/chitat-onlayn/ | подтверждено | — |
| 57 | 03 | Маргарет Марк — бывший EVP Young & Rubicam | https://www.getabstract.com/en/summary/the-hero-and-the-outlaw/1499 | подтверждено | — |
| 58 | 03 | Сбер — Заботливый у Plenum и Craftum («типичный хранитель»), Герой у Gromov («амбициозный лидер»); Правителем не назван | https://dsgners.ru/Plenum/5317-arhetipyi-v-marketinge-na-primere-didjitalnyih-brendov ; https://craftum.com/blog/arhetipy-brenda/ ; https://gromovbranding.ru/branding-blog/arhetipy-brenda-polnyy-gayd-primerami-rossiyskih-mirovyh | подтверждено | Правителем Craftum называет ВТБ, не Сбер |
| 59 | 03 | МТС — Маг-Визионер (ролик «Как изменится будущее» с Д. Нагиевым) и Заботливый-Дворецкий у одного автора | https://www.sostav.ru/blogs/261743/84422 ; https://www.sostav.ru/blogs/261743/101795 | подтверждено | — |
| 60 | 03 | Точка банк — Заботливый с примесью Героя; Яндекс Карты и «Забота» — Заботливый | https://www.sostav.ru/blogs/261743/101795 | подтверждено | — |
| 61 | 03 | Т-Банк: «после ребрендинга эксперты ADPASS видят сдвиг к нейтральному экосистемному образу» | https://adpass.ru/tinkoff-opyat-pereshel-t-eksperty-adpass-razbirayut-podhodit-li-gruppe-novyj-brend/ | исправлено | Слова «архетип» в материале нет. Оставлено то, что есть в тексте; вывод о сдвиге от Бунтаря помечен как оценка исследования |
| 62 | 03 | Билайн, Aviasales, Додо, Яндекс Лавка в Plenum / Craftum / Gromov | те же три URL | подтверждено | — |
| 63 | 03 | Тезисы «Ломоносов-2025»: ключевой Мудрец + дополнительный Заботливый, «гибрид», голос без «академической сухости» | https://confhub.ru/archive/Lomonosov_2025/data/36727/183406_uid271377_report.pdf | подтверждено | — |
| 64 | 03 | Соколова: «В 90% тестов» 2–4 архетипа; Apple «маг и творец»; агентство — «мудрец и творец»; «быть всем для всех» | https://www.sostav.ru/blogs/288649/93766 | подтверждено | — |
| 65 | 03, 05 | Катя Гас: «смешение — «каша», лучше один основной архетип плюс нетипичная черта» | https://teletype.in/@katyagas/czNfmod6BTZ ; https://yogajournal.ru/…_518/ | исправлено | «Каша - мала» в посте — о стиле общения без архетипов, «нетипичное» — выбор нетипичного архетипа. Тезиса «смешение — каша» нет. В статье 2023 года — «1-3 архетипа». Правки в 03 (2, 5.3, 8) и 05 (1.2, 5.3) |
| 66 | 03, 05 | Deza: сочетание архетипов — «абсурд» | https://www.sostav.ru/blogs/283812/65584 | исправлено | В тексте: архетипы «парами или даже тройками» — «оксюморон». «Абсурд» там о риске применения вообще |
| 67 | 05 | Deza: «прикрепить стереотипные атрибуты (цвета, шрифты, тон, историю)» как цитата | тот же URL | исправлено | Дословно: архетипу «присваивается набор стереотипных характеристик» (цвета, формы, типографика, тон голоса) |
| 68 | 05 | Deza: «ярлык вместо уникальности», Censydiam, Nielsen, Аакер; «Таротипы» — «почти шутка» | тот же URL ; https://tarotipy.ru/ | подтверждено | — |
| 69 | 03, 05 | Яппарова: Герой + Мудрец + Ребёнок — «обо всем и ни о чем»; «Первичен не образ, первичен человек»; «98%»; IKEA и Apple подогнаны задним числом; «Классификации нас путают сильнее, чем помогают»; соцсети — часть картинки; «касдев» | https://vc.ru/1129215-chto-ne-tak-s-arhetipami | подтверждено | — |
| 70 | 03, 05 | Адт: «иерархия архетипов в бренде», «2–3 ключевых» как цитаты | https://alinaadt.ru/masterarchetype ; https://xn--80acjd0bccjogl6j.xn--p1ai/archetype | исправлено | Дословно: «строить бренд на 2-3х архетипах», «иерархию смыслов», «основной архетип» + «вторичный архетип или несколько» |
| 71 | 05 | Адт: курс от 82 000 ₽, 6,5–7 месяцев, старт «ноябрь 2026 или январь 2027»; с 2011 года; термин 2023 года; тест — 3 ведущих, 2 минуты, «свыше 250 000» | https://alinaadt.ru/masterarchetype ; https://alinaadt.ru/archetypes | подтверждено | — |
| 72 | 05 | Адт: «более 30 000 прошедших» тест | https://alinaadt.ru/ | исправлено | На главной: «вывела более 30 000 человек на лучшее понимание себя» — это не число прохождений теста |
| 73 | 05 | АрхетипиУМ: 4 990 / 45 000 / 60 000 / 90 000 / 150 000 / 250 000 ₽; первые обучения в 2020; Петербург; «20000 подписчиков за месяц»; «2 млн»; «синдром самозванца»; «избавишься от страхов»; «х2» | https://arhetipium.ru/workshop-bit-soboi-v-bloge ; …/kurs-arhetipy ; …/opredeli-svoi-arhetipy ; …/tvoi-arhetipy ; …/about-me | подтверждено | — |
| 74 | 05 | Связки «тень ↔ страх» у АрхетипиУМ (Герой, Мудрец, Идеалист, Славный малый, Эстет, Маг, Правитель, Творец, Шут) | https://arhetipium.ru/hero , /mudrec , /idealist , /slavniy-malyi , /estet , /mag , /pravitel , /tvorec , /shut | подтверждено | Все цитаты найдены дословно |
| 75 | 05 | Тень у Putnam: «как описаны страхи новичков, не зафиксировано ⚠»; Coulbourn «приписывание не подтверждено её материалами» | https://kayeputnam.com/brand-archetypes/creator , /royal , /sage , /entertainer и ещё 8 страниц | исправлено | Блоки «The Shadow Side» прочитаны: у Творца — «self-doubt», «own worst critic», «Procrastination and perfectionism»; у Royal — перфекционизм и «feelings of unworthiness»; у Sage и Entertainer — прокрастинация. С блогом и новичками не связаны. Добавлены строки в 4.1 и уточнения в 4.2, 4.3, 7.1, 7.2 |
| 76 | 05 | Связки у Пирсон / МИФ: тень Мудреца — «Бесчувственный судья», «недостаточно хороши»; тень Искателя — «Перфекционист…» | https://blog.mann-ivanov-ferber.ru/2024/07/23/temnye-storony-arxetipov-kak-v-vas-proyavlyayutsya-teni-prostodushnogo-voina-shuta/ | подтверждено | Пост называет модель «Кэрол Пирсон и Хью Марр» |
| 77 | 05 | Славный малый: страх «выделиться, казаться высокомерным, потерять связь с «народом»», стать «белой вороной» (⚠ по сниппетам) | https://hr-mar.ru/blog/articles/arkhetipy-v-marketinge-slavnyy-malyy/ ; https://welovebrands.com.ua/blog/slavnyj/ | исправлено / помечено ⚠ | Первая часть подтверждена на hr-mar.ru; «белой вороной» нет ни на одной из страниц — ⚠ оставлена только на этом |
| 78 | 05 | Pickles: Любовник «боится быть отвергнутым» (⚠ по сниппету) | https://pickles.team/lover | подтверждено | ⚠ снята. Таблица «Magnum, Chanel» — у Л. Токарева (Pickles team) на workspace.ru, как и указано |
| 79 | 05 | Sorsby: «fear of being seen», «shrinking your message to avoid judgment», перфекционизм, прокрастинация | https://bonniesorsby.com/how-to-use-shadow-work-to-strengthen-your-brand/ | подтверждено | — |
| 80 | 05 | Булыгина: вебинар 04.09.2025 («дата восстановлена ⚠»); «ощущение фальши и манипуляции» | https://tenchat.ru/media/3750005-… (WebFetch) | исправлено | Дата подтверждена комментарием автора, ⚠ снята |
| 81 | 05 | Булыгина: «Вещать, но не стараться быть понятыми» как цитата; платные «Путеводитель» и «Ценностный компас» | тот же URL | исправлено / помечено ⚠ | Дословно: «не высказаться, а быть понятым». «Путеводитель» на странице не найден (⚠); цена «Ценностного компаса» не указана |
| 82 | 03, 05 | Разбор поста В. Деминой: ведущий Шут, вкрапление Бунтаря, акценты Славный малый и Мудрец; Славный малый «добавлял близости и доверия» (⚠ по выдаче); Тиньков по ссылке как Бунтарь; «архетипическая воронка» | https://tenchat.ru/media/3757216-… (WebFetch) | подтверждено | ⚠ в 03 (4.2) снята |
| 83 | 05 | Brandme: мастер-класс 15.10.2026 | https://cityclass.ru/los_personal_branding_on_archetypes/ | исправлено / помечено ⚠ | Страница показывает дату просмотра («Ждем вас 16.10.2026», время 02:22–05:22) и место «уточняется». Это подстановка, а не дата события |
| 84 | 05 | Brandme: страна «⚠ прямо не указана» | тот же URL | исправлено | В анонсе: «C 2012 года развивает тему персонального брендинга в России» |
| 85 | 05 | Stilouette: 490–790 €, поток 14.09–05.10.2026, «более 2000 клиентов» | https://stilouette.com/professional/ | подтверждено | — |
| 86 | 05 | Шевченко: 200 € (18 000 ₽), «микс архетипов», «финансово успешным» | https://teletype.in/@anatomia_brenda/Mk3pBEc1vos | подтверждено | — |
| 87 | 05 | Щеняева: 15 000 ₽, 6 часов, «по дате рождения», сертификат | https://shchenyaeva.art/mc/7 | подтверждено | — |
| 88 | 05 | МИПИП: 94 000 / 250 000 ₽; «подняла цену в 2,5 раза»; «цены выросли на 30–40%»; блок «Личная легенда» | https://mipip.ru/expert-academy | подтверждено | — |
| 89 | 05 | «Тайны Netflix»: 2 990 ₽; рост с 4 500 до 160 000 ₽/мес; «Кластер» 2–3 архетипа, «80% твоей жизни» | https://teletype.in/@eugene_drm/unicalnost3 | подтверждено | — |
| 90 | 05 | ToolFox: 20 вопросов, «на выборке их не проверяли», автор Р. Авдеев | https://toolfox.ru/tools/archetype-day-test (WebFetch) | подтверждено | — |
| 91 | 05 | JobCannon: 24 вопроса, «теневой», повторное прохождение даёт другой тип, футер «валидированных психологических моделях» | https://jobcannon.io/ru/tests/jungian-archetype | подтверждено | — |
| 92 | 05 | Сураева: доминирующие 3–4 (допускает 3–5), для бренда 1–2 | https://vc.ru/marketing/988741-lichnyi-brend-s-pomoshyu-arhetipov-baza (WebFetch) | подтверждено | «связка из 2 архетипов или вообще 1» |
| 93 | 05 | Левшин: «чистых архетипов нет», два доминирующих и два менее выраженных | https://nokc.org.ru/nokc-style/ | подтверждено | В тексте «не бывает чистых архетипов» — близкий пересказ |
| 94 | 05 | Пилиповец: профиль через «ИИ-анализ»; «Архетип не нужно «играть»…»; Любовник «Хорош как акцент»; Шут «усилитель, не основа» | https://mybusiness.by/2026/tpost/archetypes-founder-business | подтверждено | — |
| 95 | 05 | Бетева: «один или два… И придерживайтесь их во всем»; Птушкин, «Орел и Решка», «Гудков», «Кац»; не зацикливаться на отраслевом архетипе | https://mariabeteva.com/archetypes | подтверждено | — |
| 96 | 05 | Багдасарова и Силенко: Лиззка 2,13 млн «[51]» | https://www.tsutmb.ru/…/Bagdasarova_Silenko.pdf ; https://humanities.fa.ru/jour/article/download/629/616 | исправлено | 2,13 млн — в тезисах 2021 года [50], ссылка поправлена |
| 97 | 05 | Власов, Кузьма, Юлик — «2021–2022» [50, 51] | те же URL | исправлено | Они есть только в статье 2022 года [51] |
| 98 | 05 | Шейдлина: Instagram 4,5 млн, YouTube 2,16 млн; «критическое стремление к совершенству»; авторы считают проверку соответствия контента перспективным направлением | humanities.fa.ru | подтверждено | — |
| 99 | 05 | Куликова: «быстрого создания доверия» как цитата; тень Шута «хаос и жестокость» | https://snob.ru/profile/406294/blog/3095455/ | исправлено | Дословно: «чтобы быстро создать доверие»; про Шута — подтверждено |
| 100 | 05 | Куплинов — «типичное лицо» архетипа | https://www.sostav.ru/blogs/261743/42960 | исправлено | В тексте Куплинов — пример того, что в архетипе Славного малого «очень часто» выступают блогеры; кавычки сняты |
| 101 | 05 | Фадеев: «Я не знаю, что такое бренд-архетип», «У меня нет цели бунтовать» | https://www.sostav.ru/blogs/261743/37806 | подтверждено | — |
| 102 | 05 | Дяченко: «90-100% личного времени», «натянуть», «кто вы такой, чтобы отнимать чьё-то время?» | https://www.sostav.ru/blogs/261743/41286 | подтверждено | — |
| 103 | 05 | Сбер Бизнес Live: Лебедев — Творец с Бунтарём; Спиридонов — Мудрец; Овчинников — Славный малый; «один основной и несколько второстепенных» | https://sberbusiness.live/publications/archetype | подтверждено | — |
| 104 | 05 | Хогсхед: Fascinate 2010, How the World Sees You 2014, 28 вопросов, 49 архетипов, «treats the individual as though he or she were a brand» | https://en.wikipedia.org/wiki/Sally_Hogshead (WebFetch) | подтверждено | США, Орландо |
| 105 | 05 | Хогсхед: «become more of who you already are» | https://www.nbcnews.com/news/amp/wbna55191259 | подтверждено | — |
| 106 | 05 | Хогсхед: 49 = 42 + 7 «Double Trouble» | https://www.shortform.com/summary/how-the-world-sees-you-summary-sally-hogshead | подтверждено | — |
| 107 | 05 | Putnam: «250K+», «100+ Brands», «20+ Years», «fastest path to clarity», «Rooted in Jungian psychology… by Carol Pearson», ориентация на STR и гостеприимство | https://kayeputnam.com/ | подтверждено | — |
| 108 | 05 | Putnam: квиз с 2013 года, «over 200,000»; «over 100,000»; «on truth, not trends»; Brandfluency — 12 курсов; школа offline | https://logogeek.uk/podcast/branding-archetypes ; https://ebaqdesign.com/podcast/archetypes-branding ; https://kayeputnam.teachable.com/p/complete-set | подтверждено | — |
| 109 | 05 | Putnam: «55,000» прохождений (⚠ по выдаче) | https://www.nickwestergaard.com/the-psychology-of-branding-with-kaye-putnam/ | помечено ⚠ | В тексте страницы числа нет; «clarity and confidence to scale your impact and income» подтверждено |
| 110 | 05 | Pearson & Marr, «What Stories Are You Living?» — 2007, 213 с.; переработка 2021 | https://www.goodreads.com/book/show/55446407 ; PMAI Manual | подтверждено | — |
| 111 | 05 | Мисс: «Sacred Contracts» (Harmony, 2001); «Archetypes: Who Are You?» (Hay House, 2013) — 10 архетипов | https://publishersweekly.com/9780517703922 ; https://publishersweekly.com/9781401941086 ; https://www.penguinrandomhouse.com/books/601468/archetypes-by-caroline-myss/9781401941109 | подтверждено | Фразу «from careers to relationships» на странице PRH не нашли |
| 112 | 05 | Русские издания: Питер 2005; Бомбора 2023 (ISBN 978-5-04-246600-7); МИФ 2024, пер. А. Багрянцевой, ISBN 978-5-00214-422-8 | https://urss.ru/cgi-bin/db.pl?lang=Ru&blang=ru&page=Book&id=154748 ; https://www.labirint.ru/books/950126/ ; https://eksmo.ru/book/…ITD1500651/ ; https://www.labirint.ru/books/1002571/ | подтверждено | — |
| 113 | 05 | Матрикс — Litres, 06.05.2023, 156 с.; Путинцева — Ridero, 2025, ISBN 978-5-0065-4019-4 | https://litres.com/book/albina-matriks/matrica-sudby-lichnyy-brend-69212533/read/ ; https://books.yandex.ru/books/tfkNDXua/read-online | подтверждено | — |
| 114 | 05 | Овчинникова, «Архетипы руководителей» — выходные данные ⚠ | https://www.chitai-gorod.ru/… (403) ; WebSearch | помечено ⚠ | Подтвердить не удалось; ⚠ оставлена |
| 115 | 05 | NCS-R (Ruscio и др., 2008): публичные выступления 21,2 %; хотя бы один страх 24,1 %; 19,5 / 16,8 / 14,7 %; СТР 12,1 % и 7,1 % | https://pmc.ncbi.nlm.nih.gov/articles/PMC2262178/ ; Crossref 10.1017/S0033291707001699 | подтверждено | Добавлены 38(1): 15–28 и DOI |
| 116 | 05 | NCS (Kessler и др., 1998): N = 8 098; 30,2 % (⚠) | https://pubmed.ncbi.nlm.nih.gov/9585711/ | подтверждено частично / ⚠ | N подтверждено, страницы 613–619 добавлены; 30,2 % в аннотации нет, ⚠ оставлена |
| 117 | 05 | Bravata 2020: 62 исследования, 14 161 участник, 9–82 %, лечение не оценивалось, финансирование Crossover Health | https://pmc.ncbi.nlm.nih.gov/articles/PMC7174434/ | подтверждено | Добавлены 35(4): 1252–1275 и DOI |
| 118 | 05 | Clance & Imes 1978, 15(3): 241–247 (⚠ не сверено) | Crossref 10.1037/h0086006 | исправлено | Выходные данные подтверждены, ⚠ снята, DOI добавлен |
| 119 | 05 | Эффект прожектора (Gilovich и др., 2000): переоценка ≈ в 2 раза; ⚠ цифры по вторичным | https://pubmed.ncbi.nlm.nih.gov/10707330/ ; https://atticusli.com/replication-crisis/spotlight-effect/ | подтверждено / ⚠ | Аннотация подтверждает эффект и дизайн (футболка, исследования 1–5); 46 % против 23 % — только во вторичном источнике, ⚠ оставлена |
| 120 | 05 | Bailey и др. 2020: N = 10 560, предрегистрированный эксперимент, внутриличностный эффект | https://pubmed.ncbi.nlm.nih.gov/33024115/ | подтверждено | Добавлены DOI и PMC7538578 (UCL и Columbia отдают 403) |
| 121 | 05 | Kross и др. 2014: 7 исследований, N = 585, мини-метаанализ (Study 6) | https://pubmed.ncbi.nlm.nih.gov/24467424/ ; PDF на rascl.studentorg.berkeley.edu | подтверждено | — |
| 122 | 05 | White и др. 2017: N = 180, 4 и 6 лет, 10 минут, Бэтмен > третье лицо > первое лицо | https://pubmed.ncbi.nlm.nih.gov/27982409/ ; https://experts.umn.edu/… | подтверждено | — |
| 123 | 05 | BPS: 55 % и 32 %; альтернативные объяснения — «идентификация с силой персонажа, привычность ролевой игры» | https://www.bps.org.uk/research-digest/pretending-be-batman-helps-kids-stay-task | исправлено | Цифры совпадают. Объяснения уточнены: условие было интереснее; идентификация с персонажем |
| 124 | 05 | Thomas и др., CHI 2022: 135 создателей; 44 % < 10 тыс.; 18 % стаж 1–2 года; 95 %; ≈70 %; 36 %; 22 %; 44 % временно и 19 % навсегда ушли; 82 % и 55 % | https://elie.net/static/files/…/it-s-common-….pdf ; Crossref 10.1145/3491102.3501879 | подтверждено | DOI добавлен |
| 125 | 05 | Samermit и др., USENIX 2023: «по выдаче, хейт испытывали 95 % ⚠» | https://www.usenix.org/system/files/usenixsecurity23-samermit.pdf | исправлено | Полный текст открыт: 95 % — пересказ опроса из CHI 2022, новой выборки нет |
| 126 | 05 | Abidin 2016: «visibility labour», цитата-определение | https://wishcrys.com/2016/09/28/procrastiprogress-updates-from-the-cave-vi/ ; Crossref 10.1177/1329878X16665177 | подтверждено | Добавлено «Сингапур» (из аннотации) |
| 127 | 05 | Duffy & Hund 2019: 25 интервью, женщины, мода / красота / лайфстайл, «too real» / «not real enough», «can't win» | https://ijoc.org/index.php/ijoc/article/view/11729 ; https://cals.cornell.edu/news/2019/10/women-instagram-derided-too-real-or-not-real-enough | подтверждено | — |
| 128 | 05 | Awin 22.08.2022: 78 / 66 / 72 / 53 % | https://www.awin.com/us/news-and-events/industrynews/creator-burnout-survey | подтверждено | — |
| 129 | 05 | Billion Dollar Boy: 52 % и 37 %; «год не установлен ⚠» | https://www.netinfluencer.com/creator-burnout-crisis-… | исправлено | Публикация 10.07.2025, выборка 1 000 создателей и 1 000 маркетологов; ⚠ снята |
| 130 | 05 | Creators 4 Mental Health «совместно с Гарвардом» (⚠ по выдаче) | https://www.entrepreneur.com/living/i-cant-afford-to-take-breaks-content-creators-are/499525 | исправлено | Партнёр — Lupiani Insights & Strategies; Гарвард не упоминается. Публикация 12.11.2025, более 500 создателей, Северная Америка |
| 131 | 05 | Watson & Friend 1969 (⚠ страница не загрузилась) | https://pubmed.ncbi.nlm.nih.gov/5810590/ | исправлено | Выходные данные 33(4): 448–457 подтверждены; данные FNE по-прежнему не собраны (⚠) |
| 132 | 05 | McAdams & McLean 2013: редемптивные смыслы и агентность связаны с благополучием (корреляции) | https://www.psychologicalscience.org/journals/current-directions/0963721413475622/ ; Crossref | подтверждено | Добавлены 22(3): 233–238 и DOI |
| 133 | 05 | Форер: 39 студентов, 13 утверждений, 4,30 по шкале 0–5 | https://en.wikipedia.org/wiki/Barnum_effect (WebFetch) | подтверждено | — |
| 134 | 05 | Моргенштерн: реестр иноагентов с 06.05.2022 | https://ru.wikipedia.org/wiki/Моргенштерн_(музыкант) (WebFetch) | подтверждено, дополнено | Добавлено: 08.09.2024 возбуждено уголовное дело об уклонении от обязанностей иноагента (по Википедии, результата нет) |
| 135 | 05 | Тиньков: реестр иноагентов 16.02.2024; выход из гражданства в 10.2022 | https://ru.wikipedia.org/wiki/Тиньков,_Олег_Юрьевич (WebFetch) | подтверждено | — |
| 136 | 05 | BadComedian: «статья прочитана наполовину ⚠» | https://ru.wikipedia.org/wiki/BadComedian (WebFetch, два прохода) | исправлено | Прочитано почти всё: сведений о реестрах и делах нет; закрытие группы VK — 22.12.2024 |
| 137 | 05 | Лебедев: правовых примечаний нет | https://ru.wikipedia.org/wiki/Лебедев,_Артемий_Андреевич (WebFetch) | исправлено | Добавлено нейтрально: на Украине запрет въезда (2017), санкционный список (22.01.2023), подозрение СБУ (21.03.2023). Блокировка YouTube 22.02.2023 и VK с 10.2023 подтверждены |
| 138 | 05 | Птушкин: «правовой статус не проверялся» | https://ru.wikipedia.org/wiki/Антон_Птушкин (WebFetch) | исправлено / помечено ⚠ | По Википедии со ссылкой на Baza: запрет въезда в РФ на 50 лет с 16.04.2022 (официального документа нет, ⚠); YouTube 5,45 млн на 17.01.2026 подтверждён |
| 139 | 05 | Нагиев: «правовой статус не проверялся» | https://ru.wikipedia.org/wiki/Нагиев,_Дмитрий_Владимирович (WebFetch, ≈60 %) | исправлено / помечено ⚠ | В прочитанной части реестров и дел нет; обращение депутата (12.2025) о признании иноагентом без решения. Источник [127] |
| 140 | 05 | РУДН: Бузова и Канделаки без архетипов | http://repository.rudn.ru/en/records/article/record/95008/ | подтверждено | — |

**Итого: 140 утверждений.**
- подтверждено — 97, из них 3 частично или только по выходным данным;
- исправлено — 34;
- исправлено и помечено ⚠ — 5;
- подтверждено частично или не подтверждено, ⚠ оставлена — 4;
- удалено — 0.

---

## 3. Проверка URL

Коды — результат `curl -L` 2026-10-16 (повторы через WebFetch отмечены). «Подтверждает» — есть ли на странице то, на что ссылается файл.

### 3.1. 03-blends.md (проверено содержательно 52 URL)

| № | URL | Источник в файле | Открывается | Подтверждает | Комментарий |
|---|---|---|---|---|---|
| 1 | https://openlibrary.org/search/inside.json (экземпляр herooutlawbuildi0000mark) | [1] | да | да | 12 фраз; страницы не даёт |
| 2 | https://www.goodreads.com/work/quotes/347790 | [3] | да | да | Числа BAV |
| 3 | https://cdn.prod.website-files.com/…/PMAI_Manual_2021-1.pdf | [5] | да | да | — |
| 4 | https://carolspearson.com/about/archetypal-assessment-pearson-marr-archetype-indicator-r | [6] | да | да | — |
| 5 | https://www.carolspearson.com/wp-imort-2/pmai-re-release | [7] | да | да | — |
| 6 | https://www.carolspearson.com/about/the-pearson-12-archetype-system-human-development-and-evolution | [8] | да | да | — |
| 7 | https://www.storywell.com/purchase-the-pmai.htm | [9] | да | да | Добавлена метка «рекламный» |
| 8 | https://www.storywell.com/the-pearson-marr-assessment.htm | [10] | да | да | — |
| 9 | https://www.psychologytoday.com/us/blog/the-seekers-forum/202408/which-archetypes-are-you-living | [11] | да | да | «gesture» в расшифровке есть |
| 10 | https://www.sibscript.ru/jour/article/jats/1932 | [12] | да | да | — |
| 11 | https://content.e-bookshelf.de/media/reading/L-535049-ae25abbe32.pdf | [13] | да | да | Ознакомительный фрагмент издателя; глава 4 уточнена |
| 12 | https://myss.com/free-resources/sacred-contracts-and-your-archetypes/the-archetypal-wheel/ | [14] | да | да | — |
| 13 | https://myss.com/wp-content/uploads/2015/07/Gallery-of-Archetypes.pdf | [15] | да | да | — |
| 14 | https://publishersweekly.com/9780517703922 | [16] | да | да | — |
| 15 | https://www.archetypesinbranding.com/post/3questions | [17] | да | да | — |
| 16 | https://www.slideshare.net/slideshow/archetypes-in-branding/49975573 | [18] | нет (страница не грузится без JS) | не проверено | Ссылку не менял: ответ 200, ошибка только в рендере |
| 17 | https://kayeputnam.com/brand-archetypes/ и 12 страниц архетипов | [19] | да | да | Patagonia, Стюарт, Royal, Shadow Side |
| 18 | https://kayeputnam.com/quiz/ | [20] | да | да | Добавлена метка «рекламный» |
| 19 | https://logogeek.uk/podcast/branding-archetypes | [21] | да | да | — |
| 20 | https://ebaqdesign.com/podcast/archetypes-branding | [22] | curl — тайм-аут; WebFetch — да | частично | Трёх подтипов нет → исправлено |
| 21 | https://www.howtofascinate.com/wp-content/uploads/2024/07/HTF-Matrix.pdf | [23] (добавлен) | да | да (© 2014) | Названия ячеек — графика |
| 22 | https://www.shortform.com/summary/how-the-world-sees-you-summary-sally-hogshead | [24] | да | да | — |
| 23 | https://iconicfox.com.au/brand-archetypes/ | [25] | да (curl); WebFetch — пусто | да | — |
| 24 | https://brandmasteracademy.com/wp-content/uploads/2020/07/Brand-Archetype-Checklist.pdf | [26] (добавлен) | да | да | Заменяет «стороннюю копию» |
| 25 | https://smithery.ai/skills/mike-coulbourn/brand-archetype-selection | [27] | да | да (70/30) | — |
| 26 | https://spellbrand.com/brand-archetypes | [28] | да | да | — |
| 27 | https://umbrex.com/resources/frameworks/marketing-frameworks/brand-archetypes-framework-jungian-archetypes/ | [29] | да | да | — |
| 28 | https://legacy.digitalsurgeons.com/thoughts/marketing/brand-archetypes/ | [30] | да | частично | Две «цитаты» не дословны → исправлено |
| 29 | https://wppbav.com/insights/brand-archetypes/ | [31] | да | да | — |
| 30 | https://www.imperial.ac.uk/business-school/ib-knowledge/marketing/lessons-leaders-successful-brands-have-multiple-personalities/ | [32] | curl — сброс; WebFetch — да | да | — |
| 31 | https://cim.co.uk/content-hub/authors/richard-gillingwater | [33] | **нет (404)** | — | Помечено «⚠ ссылка недоступна на 2026-10-16» |
| 32 | https://blog.hubspot.com/marketing/brand-archetypes | [34] | да | да | — |
| 33 | https://www.moonb.io/blog/brand-archetypes | [35] | да | да | — |
| 34 | https://postmypost.io/glossary/brand-archetype | [36] | да | да | — |
| 35 | https://researchscape.com/blog/are-brands-people-or-religions | [38] | да | **нет** (для тезиса о «неопубликованном методе») | Исправлено |
| 36 | https://www.convinceandconvert.com/podcasts/episodes/create-magnetic-demand-with-character-archetypes/ | [39] | **нет (403)** | не проверено | В тексте добавлено «⚠ не перепроверено» |
| 37 | https://www.mrweb.com/drno/printable/pn8627.htm | [40] | да | да | — |
| 38 | https://desantisbreindel.com/?p=674 | [41] | да | да | — |
| 39 | https://toolfox.ru/tools/archetype-day-test | [43] | curl — ошибка HTTP/2; WebFetch — да | да | — |
| 40 | https://myo.gelisim.edu.tr/en/akademik-department-public-relations-and-advertisement-news-how-to-use-archetypes-in-brand-positioning | [44] | да | да («2 percent») | — |
| 41 | https://www.warc.com/content/article/admap/using-archetypes-to-build-stronger-brands/en-gb/76945 | [45] | да | да | — |
| 42 | https://www.sostav.ru/blogs/288649/93766 | [47] | да | да | — |
| 43 | https://confhub.ru/archive/Lomonosov_2025/data/36727/183406_uid271377_report.pdf | [48] | да (зеркало lomonosov.msu.ru перенаправляет сюда) | да | — |
| 44 | https://dsgners.ru/Plenum/5317-arhetipyi-v-marketinge-na-primere-didjitalnyih-brendov | [73] | да | да | — |
| 45 | https://craftum.com/blog/arhetipy-brenda/ | [74] | да | да | — |
| 46 | https://gromovbranding.ru/branding-blog/arhetipy-brenda-polnyy-gayd-primerami-rossiyskih-mirovyh | [75] | да | да | — |
| 47 | https://adpass.ru/tinkoff-opyat-pereshel-t-eksperty-adpass-razbirayut-podhodit-li-gruppe-novyj-brend/ | [77] | да | **нет** (об архетипах ни слова) | Исправлено |
| 48 | https://secrets.tbank.ru/razvitie/arhetip-brenda/ | [78] | нет (ошибка TLS-сертификата) | — | В файле уже ⚠ |
| 49 | https://api.crossref.org/works/10.1016/j.bushor.2022.11.001 | [86] | да (при повторе 429) | да | — |
| 50 | https://digital.lib.washington.edu/researchworks/bitstreams/4d33b25a-2369-446b-9147-3957e3ff0eb3/download | [87] | да при первом запросе; 403 при массовой проверке | да | Защита от ботов, ссылка рабочая |
| 51 | https://www.emerald.com/jrim/article/20/4/473/1275812/… | [88] | **нет (403)** | — | Метаданные подтверждены через Crossref |
| 52 | https://www.mdpi.com/2076-3387/6/2/5 | [91] | **нет (403)** | — | Метаданные — через Crossref |
| 53 | http://mcd.woodbury.edu/wp-content/uploads/2016/02/Faber-Mayer-2009.pdf | [93] | да | да | — |
| 54 | https://arxiv.org/html/2606.16053v1 | [94] | да | да | — |
| 55 | https://www.getabstract.com/en/summary/the-hero-and-the-outlaw/1499 | [95] | да | да | — |
| 56 | https://iconicfox.com.au/can-you-mix-brand-archetypes/ | [96] (новый) | да | да | Контрпример 60–70 / 20–30 / 5–10 |
| 57 | https://en.wikipedia.org/wiki/Get_a_Mac | [97] (новый) | WebFetch — да | да | — |

Прочие URL 03-blends без содержательной сверки (только HTTP-код): из 115 уникальных адресов 96 ответили 200. Не открылись: cdn.eksmo.ru (TOC-PDF, сброс соединения), insideag.wpp.com (502, в файле уже ⚠), doaj.org ×2 (403, рядом есть рабочие ссылки на журналы).

### 3.2. 05-personal-brand.md (проверено содержательно 70 URL)

| № | URL | Источник в файле | Открывается | Подтверждает | Комментарий |
|---|---|---|---|---|---|
| 1 | https://kayeputnam.com/ | [1] | да | да | — |
| 2 | https://kayeputnam.com/brand-archetypes/ (+ /creator, /royal, /sage, /entertainer, /maverick, /innocent и др.) | [2] | да | да | Shadow Side прочитан |
| 3 | https://kayeputnam.com/quiz/ | [3] | да | да | — |
| 4 | https://logogeek.uk/podcast/branding-archetypes | [4] | да | да | — |
| 5 | https://ebaqdesign.com/podcast/archetypes-branding | [5] | WebFetch — да | да | — |
| 6 | https://www.nickwestergaard.com/the-psychology-of-branding-with-kaye-putnam/ | [6] | да | частично | «55,000» нет |
| 7 | https://kayeputnam.teachable.com/p/complete-set | [7] | да | да («offline») | — |
| 8 | https://en.wikipedia.org/wiki/Sally_Hogshead | [8] | WebFetch — да | да | — |
| 9 | https://www.shortform.com/summary/how-the-world-sees-you-summary-sally-hogshead | [9] | да | да | — |
| 10 | https://www.howtofascinate.com/wp-content/uploads/2024/07/HTF-Matrix.pdf | [10] | да | да | — |
| 11 | https://www.nbcnews.com/news/amp/wbna55191259 | [13] | да | да | — |
| 12 | https://www.aol.com/2015/06/03/want-to-get-paid-more-try-this/ | [15] | **нет (404)** | — | Помечено «⚠ ссылка недоступна на 2026-10-16» |
| 13 | https://www.goodreads.com/book/show/55446407 | [16] | да | да | — |
| 14 | https://www.carolspearson.com/post/new-article-the-roots-of-the-pearson-marr-archetypes | [17] | да | да | — |
| 15 | https://www.carolspearson.com/about/archetypal-assessments | [18] | да | да | IBM-KCIS → исправлено |
| 16 | PMAI Manual (cdn.prod.website-files.com) | [19] | да | да | — |
| 17 | https://www.storywell.com/research-with-the-pearson-marr-assessment.htm | [20] | да | да | — |
| 18 | https://www.psychologytoday.com/us/blog/the-seekers-forum/202408/which-archetypes-are-you-living | [21] | да | да | — |
| 19 | https://urss.ru/cgi-bin/db.pl?lang=Ru&blang=ru&page=Book&id=154748 | [23] | да | да (2005) | — |
| 20 | https://www.labirint.ru/books/950126/ | [23] | да | да | — |
| 21 | https://eksmo.ru/book/geroy-i-buntar-…-ITD1500651/ | [23] | да | да (ISBN) | — |
| 22 | https://publishersweekly.com/9781401941086 | [25] | да | да | — |
| 23 | https://www.penguinrandomhouse.com/books/601468/archetypes-by-caroline-myss/9781401941109 | [25] | да | частично | — |
| 24 | https://www.spiritualityandpractice.com/book-reviews/view/24685/archetypes | [25] | **нет (403)** | — | Не менял: на тезис есть другие ссылки |
| 25 | https://myss.com/wp-content/uploads/2015/07/Gallery-of-Archetypes.pdf | [26] | да | да | — |
| 26 | https://affordanything.com/episode184 | [27] | **нет (403)** | — | Тезис помечен ⚠ в файле |
| 27 | https://booksthatslay.com/the-alter-ego-effect-summary/ | [28] | да | да | — |
| 28 | https://www.perlego.com/book/1213231/little-brand-book-pdf | [29] | да | да | Каталог Perlego (легальная подписочная библиотека) |
| 29 | https://payhip.com/b/uths | [32] | **нет (403)** | — | В файле уже ⚠ |
| 30 | https://bonniesorsby.com/how-to-use-shadow-work-to-strengthen-your-brand/ | [34] | да | да | — |
| 31 | https://justynarossy.substack.com/p/welcome-to-the-confidently-visible | [35] | **нет (404)** | — | Помечено «⚠ ссылка недоступна» |
| 32 | https://iconicfox.com.au/brand-archetypes/ ; https://iconicfox.com.au/can-you-mix-brand-archetypes/ | [37] | да | да | Описание [37] дополнено |
| 33 | https://grahammann.net/book-notes/building-a-storybrand-donald-miller | [38] | да | да | — |
| 34 | https://ideas.repec.org/a/eee/bushor/v66y2023i5p615-629.html | [39] | да | да | — |
| 35 | https://www.chitai-gorod.ru/product/arhetipy-rukovoditelej-potomu-cto-v-biznese-licnoe-vse-3173346 | [40] | **нет (403)** | — | В файле уже ⚠ |
| 36 | https://vc.ru/1129215-chto-ne-tak-s-arhetipami | [41] | да | да | — |
| 37 | https://www.sostav.ru/blogs/283812/65584 | [42] | да | частично | Две формулировки исправлены |
| 38 | https://tarotipy.ru/ | [43] | да | да | — |
| 39 | https://snob.ru/profile/406294/blog/3095455/ | [44] | да | частично | Цитата уточнена |
| 40 | https://tenchat.ru/media/3750005-… | [45] | curl — сброс; WebFetch — да | частично | Исправлено |
| 41 | https://tenchat.ru/media/3757216-… | [46] | да | да | — |
| 42 | https://tenchat.ru/media/3819574-… | [47] | нет (сброс соединения) | не проверено | — |
| 43 | https://www.tsutmb.ru/…/Bagdasarova_Silenko.pdf | [50] | да | да | — |
| 44 | https://humanities.fa.ru/jour/article/download/629/616 | [51] | да | да | — |
| 45 | https://career.habr.com/courses/marketing/self-branding | [52] | да | да (архетипов нет) | — |
| 46 | https://arhetipium.ru/ и 15 подстраниц | [53]–[57] | да | да | — |
| 47 | https://t.me/s/vse_pro_arhetipy | [58] | да | да (853 подписчика) | — |
| 48 | https://stilouette.com/professional/ | [59] | да | да | — |
| 49 | https://teletype.in/@anatomia_brenda/Mk3pBEc1vos | [60] | да | да | — |
| 50 | https://shchenyaeva.art/mc/7 | [61] | да | да | — |
| 51 | https://mipip.ru/expert-academy | [62] | да | да | — |
| 52 | https://teletype.in/@eugene_drm/unicalnost3 | [63] | да | да | — |
| 53 | https://alinaadt.ru/masterarchetype ; https://alinaadt.ru/archetypes ; https://alinaadt.ru/ ; станьбрендом.рф/archetype | [64], [65] | да | частично | «30 000» и «иерархия» исправлены |
| 54 | https://brandme.academy/club-kinomarafon ; …/page1517576.html | [66] | **нет (402)** | — | В файле уже ⚠ |
| 55 | https://cityclass.ru/los_personal_branding_on_archetypes/ | [66] | да | частично | Дата подставляется динамически → исправлено |
| 56 | https://rsv.ru/blog/arhetipy-v-soczsetyah-kak-sdelat-blog-uznavaemym/ | [69] | да | да | — |
| 57 | https://mariabeteva.com/archetypes | [70] | да | да | — |
| 58 | https://jobcannon.io/ru/tests/jungian-archetype | [72] | да | да | — |
| 59 | https://www.sostav.ru/blogs/261743/41286 ; …/42960 ; …/84422 ; …/37806 ; …/101795 | [74]–[78] | да | да / частично | 42960 — «типичное лицо» исправлено |
| 60 | https://mybusiness.by/2026/tpost/archetypes-founder-business | [79] | да | да | — |
| 61 | https://blog.mann-ivanov-ferber.ru/2024/07/23/temnye-storony-arxetipov-… | [80] | да | да | — |
| 62 | https://www.labirint.ru/books/1002571/ | [80] | да | да | — |
| 63 | https://sberbusiness.live/publications/archetype | [81] | да | да | — |
| 64 | https://teletype.in/@katyagas/czNfmod6BTZ ; yogajournal.ru/…_518/ | [82] | да | частично | Исправлено |
| 65 | https://vc.ru/marketing/988741-lichnyi-brend-s-pomoshyu-arhetipov-baza | [83] | да (WebFetch) | да | — |
| 66 | https://nokc.org.ru/nokc-style/ | [84] | да | да | — |
| 67 | https://i-am-brand.ru/knowledge-base/arhetipy-v-lichnom-brende/ | [85] | да | да | — |
| 68 | https://adwai.digital/blog/j4rlrpry31-12-arhetipov-lichnogo-brenda-postroenie | [86] | да | да | — |
| 69 | https://litres.com/book/albina-matriks/matrica-sudby-lichnyy-brend-69212533/read/ | [87] | да | да | — |
| 70 | https://books.yandex.ru/books/tfkNDXua/read-online | [88] | да | да | — |
| 71 | https://pickles.team/lover ; https://workspace.ru/blog/arhetip-yunga-… | [89] | да | да | ⚠ снята |
| 72 | https://hr-mar.ru/blog/articles/arkhetipy-v-marketinge-slavnyy-malyy/ ; https://welovebrands.com.ua/blog/slavnyj/ | [90] | да | частично | «белой вороной» нет |
| 73 | https://nv.ua/blogs/kak-nauchitsya-proyavlyat-sebya-psihologicheskie-sovety-50521934.html | [91] | **нет (403)** | — | — |
| 74 | https://www.spbranding.ru/nmarafon | [92] | **нет (404)** | — | В файле уже ⚠ |
| 75 | https://ekapromo.ru/ | [93] | да («на переработке, откроется в октябре») | — | В файле уже ⚠ |
| 76 | https://ru.wikipedia.org/wiki/Моргенштерн_(музыкант) | [95] | WebFetch — да | да | Дополнено |
| 77 | https://ru.wikipedia.org/wiki/Тиньков,_Олег_Юрьевич | [96] | WebFetch — да | да | — |
| 78 | https://ru.wikipedia.org/wiki/BadComedian | [97] | WebFetch — да | да | — |
| 79 | https://ru.wikipedia.org/wiki/Лебедев,_Артемий_Андреевич | [100] | WebFetch — да | да | Дополнено |
| 80 | https://ru.wikipedia.org/wiki/Антон_Птушкин | [101] | WebFetch — да | да | Дополнено |
| 81 | http://repository.rudn.ru/en/records/article/record/95008/ | [102] | да | да | — |
| 82 | https://companies.rbc.ru/news/UU5sbGkmxP/… | [103] | нет (сброс) | — | В файле уже ⚠ |
| 83 | https://pmc.ncbi.nlm.nih.gov/articles/PMC2262178/ | [104] | да | да | — |
| 84 | https://psychiatryonline.org/doi/10.1176/ajp.155.5.613 | [105] | **нет (403)** | — | Добавлена ссылка PubMed |
| 85 | https://pmc.ncbi.nlm.nih.gov/articles/PMC7174434/ | [106] | да | да | — |
| 86 | https://atticusli.com/replication-crisis/spotlight-effect/ | [108] | да | да | Вторичный |
| 87 | https://web.colby.edu/cogblog/?p=2577 | [108] | **нет (403)** | — | — |
| 88 | https://rascl.studentorg.berkeley.edu/assets/files/self-talk_as_a_regulatory_mechanism_how_you_do_it_matters.pdf | [109] | да | да | — |
| 89 | https://experts.umn.edu/en/publications/the-batman-effect-improving-perseverance-in-young-children/ | [110] | да | да | — |
| 90 | https://www.bps.org.uk/research-digest/pretending-be-batman-helps-kids-stay-task | [111] | WebFetch — да | да | — |
| 91 | https://discovery-pp.ucl.ac.uk/10134044/1/Wu_s41467-020-18539-w.pdf ; columbia press release | [112] | **нет (403)** | — | Добавлена PMC7538578 |
| 92 | https://www.psychologicalscience.org/journals/current-directions/0963721413475622/ | [113] | да | да | — |
| 93 | https://sites.utexas.edu/psyhonors18/files/2023/12/NeerulGupta_HonorsThesis2023.pdf | [114] | да | частично | Adler 2015 упомянут, пересказ лонгитюда отдельно не сверен |
| 94 | https://dlab.sauder.ubc.ca/sjdm/dmidi/Self-Concept%20Clarity.html | [115] | да | да | — |
| 95 | https://instruct.uwo.ca/psychology/294g-570/overheads/5-3.html | [115] | **нет** (сервис закрыт 03.07.2025, перенаправление) | — | Помечено «⚠ ссылка недоступна» |
| 96 | https://wishcrys.com/2016/09/28/procrastiprogress-updates-from-the-cave-vi/ | [116] | да | да | — |
| 97 | https://ijoc.org/index.php/ijoc/article/view/11729 | [117] | да | да | — |
| 98 | https://cals.cornell.edu/news/2019/10/women-instagram-derided-too-real-or-not-real-enough | [117] | да | да | — |
| 99 | https://elie.net/static/files/…/it-s-common-….pdf | [118] | да | да | — |
| 100 | https://www.usenix.org/system/files/usenixsecurity23-samermit.pdf | [119] | да | да | Смысл цифры уточнён |
| 101 | https://www.awin.com/us/news-and-events/industrynews/creator-burnout-survey | [120] | да | да | — |
| 102 | https://www.netinfluencer.com/creator-burnout-crisis-… | [121] | да | да | Дата добавлена |
| 103 | https://www.entrepreneur.com/living/i-cant-afford-to-take-breaks-content-creators-are/499525 | [122] | да | частично | Партнёр исправлен |
| 104 | https://psycnet.apa.org/doi/10.1037/h0027806 | [123] | да (200) | не проверено | Добавлена ссылка PubMed |
| 105 | https://en.wikipedia.org/wiki/Barnum_effect | [124] | WebFetch — да | да | — |
| 106 | https://ru.wikipedia.org/wiki/Нагиев,_Дмитрий_Владимирович | [127] (новый) | WebFetch — да | частично | Прочитано ≈60 % |

Прочие URL 05-personal-brand без содержательной сверки (только HTTP-код): из 165 уникальных адресов 134 ответили 200.

**Итого по URL.**
- 03: в таблице 57 строк. 49 адресов подтверждают утверждение полностью или частично, 2 открываются, но тезиса не подтверждают (Researchscape, ADPASS; исправлено), 6 недоступны или не отрисовываются.
- 05: в таблице 106 строк (часть строк объединяет подстраницы). 89 подтверждают полностью или частично, 17 недоступны или содержательно не проверены.
- Массовая проверка HTTP-кодов охватила все 280 адресов (115 + 165, уникальных в пределах файла). Недоступны на 2026-10-16 и помечены в файлах: CIM-профиль Gillingwater (404), AOL (404), Substack Rossy (404), слайд UWO (сервис закрыт). Закрыты для автоматического доступа (403/402/сброс), но не битые: Emerald, MDPI, DOAJ, Convince & Convert, psychiatryonline, UCL, Columbia, Spirituality & Practice, affordanything, payhip, nv.ua, chitai-gorod, brandme.academy, tenchat (часть), companies.rbc.ru.

---

## 4. Соблюдение правил

| Правило | Результат | Что сделано |
|---|---|---|
| Нет цитат длиннее ~25 слов | Соблюдено | Самая длинная цитата — 20 слов (Юнг, CW 9i §221; «The brands that choose one deliberately…»). Длиннее только названия статей в списках источников |
| Нет ссылок на неавторизованные копии книг | Соблюдено | Книги Марк и Пирсон, Юнга и Хогсхед даны без ссылок на копии. В 03 [23] вместо «PDF-копии без URL» указан официальный PDF матрицы на сайте автора, в [26] — официальный PDF чек-листа вместо сторонней копии. Статья Faber & Mayer (2009) лежит на сайте Woodbury University; это статья, не книга, статус размещения не установлен — оставлено как есть |
| Неподтверждённое помечено «⚠» | В целом соблюдено | Снято 13 устаревших ⚠ (подтверждено при проверке); добавлены новые ⚠: «белой вороной», «Путеводитель», дата Brandme, запрет въезда Птушкину, Нагиев, 48 / 55 атрибутов BAV, «66 per cent» у Хартвелл, четыре недоступные ссылки |
| Собственные разборы помечены «оценка исследования, не из источника» | Нарушения исправлены | Без пометки были: «черта Правителя» у Марты Стюарт (03, три места) и вывод о сдвиге Т-Банка от Бунтаря (03). Пометки добавлены; новая собственная оценка о хронологии «Get a Mac» помечена сразу |
| Рекламные материалы помечены | Нарушения исправлены | Добавлена метка «рекламный»: 03 [9] (страница продажи PMAI), 03 [20] (квиз Putnam), 03 [96]; 05 [37] (гид о смешении), 05 [58] (канал школы), 05 [66] (анонс City Class) |
| Номера [n] соответствуют спискам | Соблюдено | Скрипт: в 03 все ссылки 1–97 определены и используются; в 05 — 1–127. Новые источники добавлены в конец. Точечные исправления адресации: 05 — Лиззка 2,13 млн → [50]; Власов, Кузьма, Юлик → [51] |
| Нет рекомендаций по проектированию продукта | Соблюдено | Поиск по ключевым словам (приложение, интерфейс, UX, MVP, «рекомендуем» и др.) ничего не нашёл |

---

## 5. Сводка

**Проверено.** 140 утверждений: 97 подтверждено (3 из них частично), 39 исправлено (5 — с новой пометкой ⚠), 4 оставлены под ⚠, удалений нет. По URL: в таблицах 163 строки (57 для 03, 106 для 05). Утверждение подтверждают 138 адресов: 49 в 03 и 89 в 05. HTTP-код проверен у всех 280 адресов.

**Самые важные исправления**
1. **Контрпример к «50/30/20, 60/30/10, 70/20/10 не найдены».** Iconic Fox (S. Houraghan, гид от 2025-11-14) даёт трёхступенчатую схему 60–70 / 20–30 / 5–10 [03: 96; 05: 37]. Утверждение исправлено в обоих файлах; не найденной осталась только 50/30/20. Там же найден и источник утверждения «2–3 архетипа» (без данных). У того же автора две версии правила расходятся.
2. **Чек-лист Brand Master Academy** найден на сайте самой академии (PDF создан 2018-05-14). ⚠ «сторонняя копия» снята, появилась датировка правила 70/30.
3. **Тени у Putnam прочитаны.** Перфекционизм и прокрастинация есть у самой Putnam (Творец, Royal, Sage, Entertainer). Неверное «приписывание Coulbourn не подтверждено её материалами» исправлено; разделы 4.1–4.3 и 7.1 дополнены.
4. **Искажённые позиции практиков.** Катя Гас («смешение — каша» в посте нет), Deza («оксюморон», а не «абсурд»), ADPASS (об архетипах ничего), Researchscape (метод не критикует), Putnam в On Branding («три подтипа» нет). Исправлены неточные «цитаты» Digital Surgeons, Deza, Булыгиной, Куликовой, Дяченко (Куплинов), Адт.
5. **Смежные исследования.** Creators 4 Mental Health работали не с Гарвардом, а с Lupiani Insights & Strategies. Цифра 95 % в USENIX 2023 — пересказ CHI 2022, а не новые данные. Опрос Billion Dollar Boy датирован 10.07.2025. Clance & Imes и Watson & Friend сверены по Crossref и PubMed. В научные ссылки добавлены тома, страницы и DOI.
6. **Даты и числа в 05.** Мастер-класс Brandme «15.10.2026» оказался подставленной датой просмотра. «Более 30 000» у Адт — не число прохождений теста.
7. **Правовые статусы** дополнены нейтрально, со ссылкой на Википедию и оговоркой о юридической проверке: Моргенштерн (уголовное дело 2024), Лебедев (украинские ограничения), Птушкин (запрет въезда со ссылкой на Baza, ⚠), Нагиев (обращение депутата без решения, ⚠). У BadComedian статья прочитана почти полностью.
8. **Данные Spangenberg (табл. 4)** добавлены к разборам Harley-Davidson, Apple и Disney: в оценках потребителей Harley и Disney — «flexible», Apple — «tightly defined». У Spangenberg порог 10 % — относительная разница.

**Что осталось под ⚠**
- Номера страниц «The Hero and the Outlaw» (с. 1–2, 10, 26–27, 30, 42, 162, 274–275, 284–285, гл. 20). Тексты в основном подтверждены, страницы нет. Не найдены «primary archetypal identity, secondary identity», «gratified (though not surprised)», часть про Dove и левый полюс «Belonging/People».
- Число атрибутов BAV: около 48 (r08, Spangenberg) или «over 55» (Researchscape).
- Merlo и др. (2023): полный текст не прочитан — таксономия, кодирование, «2 %».
- Feng и др. (2026): определение «archetype consistency», выборки, размеры эффектов.
- Gilovich (46 % / 23 %) и «эффект Бэтмена» (55 % / 32 %) — только по вторичным источникам. 30,2 % из NCS 1998 — по выдержке поиска. Корреляции SCC — слайд UWO теперь недоступен. Данные FNE не собраны.
- «66 per cent» в описании подкаста Хартвелл (страница отдаёт 403). Bechter и др. — содержание (403). Слайды Хартвелл (SlideShare не рендерится).
- 05: выходные данные книги Ю. Овчинниковой; «Путеводитель» Булыгиной; дата мастер-класса Brandme; «белой вороной»; Кудейкина (сайт «на переработке»); содержание платных модулей о тенях у Адт и Соловьевой.
- Правовые статусы по Википедии — вторичный источник. Нагиев прочитан на ≈60 %. Запрет въезда Птушкину известен со ссылкой на СМИ. Личности «Кац», «Гудков», И. Гиберман не установлены. Перед любым использованием нужна сверка с официальными реестрами.
