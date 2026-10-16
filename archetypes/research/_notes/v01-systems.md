# v01 — Протокол независимой проверки файла `01-systems.md`

**Проверяемый файл:** `archetypes/research/01-systems.md` («Системы архетипов: сравнение и таблица соответствия названий»).
**Дата проверки:** 2026-10-16. **Проверяющий:** независимый проверяющий, в сборе материала и написании файла не участвовал.
**Рамка:** только исследование для базы знаний; продукт не проектируется. Заметки `_notes/r01–r17` прочитаны выборочно и не изменялись. Правки внесены только в `01-systems.md` и в этот протокол.

---

## 1. Методика

1. **Механические проверки всего файла** (скрипт по тексту):
   - номера `[n]` в тексте сверены со списком источников: все 150 номеров есть в списке, неиспользованных номеров нет — как до правок, так и после;
   - все цитаты в «ёлочках» длиной от 15 слов выписаны и пересчитаны: самая длинная — 17 слов (Хартвелл, [78]); цитат длиннее ~25 слов нет;
   - поиск доменов неавторизованных копий (ebin, z-lib, libgen, pdfdrive, pdfcoffee и т. п.): прямых ссылок нет; упоминания ebin.pub и pdfdrive — только в оговорках о том, что такие копии не приводятся;
   - **все ссылки на archive.org проверены через метаданные Internet Archive** (`archive.org/metadata/<id>`): ограничен ли доступ (`access-restricted-item`), из какой коллекции скан, открыт ли PDF для скачивания;
   - поиск рекомендаций по проектированию продукта («рекомендуем», «приложение», «пользователь», «MVP» и т. п.): не найдено.
2. **Проверка текстов книг по легальным экземплярам.** Полнотекстовый поиск Open Library (`openlibrary.org/search/inside.json?q="…"`) по библиотечным экземплярам Internet Archive с выдачей по записи (controlled lending, `access-restricted-item: true`). Поиск возвращает OCR-фрагменты длиной 100–200 знаков. Полные тексты, PDF и djvu не скачивались. Пагинация (`page=N`) позволяла найти нужную книгу в выдаче. Проверенные экземпляры:
   - CW 9i (Princeton UP, 1968) — `archetypescollec0000jung`; для §6 — также издания 1959 и 1980 года (`archetypescollec0009_part1`, `archetypescollec0009jung`);
   - CW 9ii Aion (Princeton UP, 1968) — `aionresearchesin0009_part2`;
   - CW 5 (Pantheon, 1956) — `symbolsoftransfo0005jung`;
   - Mark & Pearson 2001 — `herooutlawbuildi0000mark`;
   - Pearson 1989 (Harper & Row, ISBN 006254862X) — `herowithinsixarc00pear`;
   - Pearson 1991 — `awakeningheroesw0000pear`;
   - Moore & Gillette (HarperSanFrancisco, 1991) — `kingwarriormagic0000moor`;
   - Bolen 1984/1985 и 1989 — `goddessesinevery0000bole`, `goddessesinevery00bolerich`, `godsineverymanne00bolerich`.
3. **Веб-источники.** Каждый URL открывался через WebFetch или curl (через прокси сессии). Для страниц, которые отдают 403 из-за защиты от ботов, использовалась копия Wayback Machine. Метаданные статей по DOI сверены через Crossref API. PDF (руководство PMAI 2021, оглавление «Бомборы», Галерея Мисс, матрица Хогсхед) извлечены `pdftotext` и проверены поиском по тексту.
4. **WebSearch** использовался трижды: триггеры Хогсхед 2010 года, переводчик «Метода StoryBrand», число карт колоды Мисс. Страницы выдачи поисковиков не открывались. Личные данные в запросах не использовались.
5. **Что не проверялось.** Русскоязычные практики из раздела 7 проверены выборочно: 10 из 36 источников группы Ж. Карточки `02-cards/` проверены только на наличие файлов, на которые ссылается таблица 9.3. Эзотерические источники [134, 135, 148–150] не проверялись.

---

## 2. Проверка утверждений

Вердикты: **подтверждено** / **исправлено** (факт или формулировка изменены в файле) / **помечено ⚠** (добавлена или оставлена пометка) / **удалено** (удалена ссылка или утверждение).

| № | Утверждение | Место в файле | Чем проверено (URL) | Вердикт | Комментарий |
|---|---|---|---|---|---|
| 1 | Юнг: «There are as many archetypes as there are typical situations in life» — CW 9i §99 | 2.3; 1.2; 10.1 п. 1 | OCR библиотечного экземпляра CW 9i: https://archive.org/details/archetypescollec0000jung (фрагмент «people, 99 There are as many archetypes…») | подтверждено; ⚠ снята | Номер параграфа виден на полях. Ключевой тезис «12 архетипов — не у Юнга» опирается теперь на легальный экземпляр |
| 2 | §99: «like an instinctual drive», «against all reason and will» | 1.2; 2.6 | тот же экземпляр | подтверждено; ⚠ снята | — |
| 3 | CW 9i §310 «far from exhausting all the statistical regularities»; §309 «according to my suggestion» | 2.2; 2.3; 2.6 | тот же экземпляр | подтверждено; ⚠ снята с цитат | Сравнение с ботаникой (§309, сн. 1) и тезис о биполярности (§§310, 413) в OCR не найдены — ⚠ оставлена |
| 4 | CW 9i §6 «a hypothetical and irrepresentable model… pattern of behaviour» | 2.1 | OCR изданий 1959 и 1980 года: https://archive.org/details/archetypescollec0009_part1 ; https://archive.org/details/archetypescollec0009jung | подтверждено; ⚠ снята | — |
| 5 | CW 9i §155 «empty and purely formal, nothing but a facultas praeformandi» | 1.2; 2.1 | https://archive.org/details/archetypescollec0000jung | подтверждено; ⚠ снята | — |
| 6 | CW 9i §136 «inherited possibilities of ideas» | 1.2; 2.1 | тот же экземпляр + Sharp: https://www.psychceu.com/jung/sharplexicon.html | подтверждено | Шарп даёт «CW 9i, par. 136» |
| 7 | CW 9i §80 «They are not personalities, but are typical situations…» | 2.1; 2.6 | https://archive.org/details/archetypescollec0000jung | подтверждено; ⚠ снята | — |
| 8 | CW 9i §221 «usually rewarded in cash», «that which in reality one is not»; §222 «practically identical with the dark side…» | 2.2; 2.4; 2.6 | тот же экземпляр (после «cash» стоит номер «222»); Sharp (§221, §222) | подтверждено; ⚠ снята | Граница §§221/222 подтверждена по полям |
| 9 | CW 9i §158 «the loving and the terrible mother»; §278 «The child is potential future»; §398 «magician, doctor, priest…»; §472 «forerunner of the saviour»; §88 «never been in consciousness» | 2.2; 2.4 | тот же экземпляр | подтверждено; ⚠ снята с этих цитат | Номера §§ — по r01, по полям не видны. «wicked aspect» (§414), «secondarily» (§90), «покинутость и непобедимость» не найдены — ⚠ оставлена с уточнением |
| 10 | CW 9i §3 «identical in all men»; §91 «unconscious images of the instincts themselves»; §81 (Таро); §100; триада Коры | 2.1; 2.2; 6.11; 8 | поиск Open Library | помечено ⚠ (оставлено) | Фразы слишком частотные или не найдены в экземпляре CW 9i; §91 найден только в другой книге |
| 11 | Aion §13 «the shadow, the anima, and the animus»; §14 «a moral problem that challenges the whole ego-personality»; §29 анима ↔ Эрос, анимус ↔ Логос | 2.2 | OCR библиотечного экземпляра Aion: https://archive.org/details/aionresearchesin0009_part2 | подтверждено | — |
| 12 | Aion §33, §§44–46 (посредничество анимы, инфляция эго) | 2.2; 2.6 | поиск не дал результата | помечено ⚠ | Раньше эти пункты считались проверенными по скану [2], который оказался открытым сканом неустановленного статуса (п. 13) |
| 13 | Ссылка [2] на Aion — «библиотечный скан того же типа, что экземпляры Пирсон» | шапка раздела 2; источник [2] | метаданные IA: коллекция `collectedworkscgjung`/`americana`, доступ не ограничен, PDF открыт для скачивания | исправлено; ссылка удалена и заменена | Скан книги под копирайтом (Princeton UP, 1968) с открытым PDF — нарушение правила об источниках. Заменена на экземпляр с выдачей по записи |
| 14 | CW 5 «never exceeds certain natural limits» (§450) | 2.3 | OCR библиотечного экземпляра CW 5 (Pantheon, 1956): https://archive.org/details/symbolsoftransfo0005jung | подтверждено (цитата); номер § — ⚠ | Ссылка добавлена в [3] |
| 15 | Персона — «функциональный комплекс» (CW 6 §801), «определяет Шарп» | 2.2 | https://www.psychceu.com/jung/sharplexicon.html | исправлено (формулировка) | Это определение самого Юнга (CW 6 §801), которое цитирует Шарп; в тексте уточнено |
| 16 | Sharp: CW 8 §342, CW 7 §245 «a mask that feigns individuality», CW 7 §377 «the well-known archetype of the mighty man», CW 8 §414 (спектр), CW 6 «function-types» | 2.1; 2.2; 2.4 | https://www.psychceu.com/jung/sharplexicon.html | подтверждено | — |
| 17 | Юнг 1919, «Instinct and the Unconscious», BJP 10(1):15–23 | 2.1; [5] | https://api.crossref.org/works/10.1111/j.2044-8295.1919.tb00003.x | подтверждено | — |
| 18 | Sotirova-Kohli и др. 2013: «outside the domain of… mainstream academic psychology», «still fairly uncommon», N = 402, 67,47% против 59,93% | 2.5 | https://pmc.ncbi.nlm.nih.gov/articles/doi/10.3390/bs3040541 | подтверждено | — |
| 19 | Выходные данные статей JAP, Neher, Aaker, Azoulay & Kapferer, Woodside и др., Bechter и др., Xara-Brasil и др., Merlo и др. (16 DOI) | 2.5; 6.9; источники | Crossref API (`api.crossref.org/works/<doi>`) | подтверждено | Авторы, журналы, тома, страницы, годы совпадают |
| 20 | 12 бренд-архетипов Марк–Пирсон и группировка по частям II–V | 3.2; 9.1 | OCR оглавления: https://archive.org/details/herooutlawbuildi0000mark ; оглавление «Бомборы»: https://cdn.eksmo.ru/v2/ITD000000001500651/PDF/ITD000000001500651_TOC.pdf | подтверждено | — |
| 21 | Точные названия частей: The Yearning for Paradise (с. 49), Leaving a Thumbprint on the World (с. 101), No Man (or Woman) Is an Island (≈ с. 161–164), Providing Structure to the World; гл. 3 Postmodern Marketing (с. 33), гл. 6 (с. 88) | 3.2 | OCR [22] | подтверждено | Part V по колонтитулам ≈ с. 205–207 (в файл не вносилось) |
| 22 | Книга — 7 частей и 21 глава; части II–V по 3 главы | 3.2 | оглавление «Бомборы» (PDF издателя) | подтверждено | — |
| 23 | Оси: «…Independence/Self-Actualization, and Stability/Control versus Risk/Mastery»; левый полюс первой оси — «вероятно, Belonging (⚠)» | 3.3 | OCR [22]: «two axes: Belonging/People versus Independence/Self-Actualization…» | исправлено | Левый полюс — **Belonging/People**; ⚠ снята; открытый вопрос 10.2 п. 2 обновлён |
| 24 | Девиз Шута «в OCR книги не найден» | 3.2 | OCR [22]: «Motto: "If I can't dance, I don't want to be part of your revolution"», Emma Goldman | исправлено | Девиз найден в самой книге; в Solomon — «a part of» |
| 25 | Explorer «also ma[y be] known as the seeker»; «adjective soup»; «Meaning management is relevant not only…»; «the first systematic approach to meaning management» | 3.2; 3.4 | OCR [22] | подтверждено | — |
| 26 | «one—and only one—archetype» и «at least one active archetype in each quadrant» — только по копии r08 [23] ⚠ | 3.3; 3.4; 4.4 | OCR [22] | исправлено (источник [23] ⚠ → [22]) | Фразы есть в легальном экземпляре; номер страницы (42) остаётся под ⚠ |
| 27 | Мадонна «always the outrageous Rebel», Николсон — Outlaw; Мег Райан и Том Хэнкс — Innocent | 3.4 | OCR [22] («2 PRIMAL ASSETS … always the outrageous Rebel. Offscreen and on, Jack Nicholson…») | исправлено частично | Мадонна и Николсон подтверждены (с. 2); Райан и Хэнкс в OCR не найдены — ⚠ оставлена |
| 28 | BAV: MVA «rose by 97% more» | 3.5 | OCR [22] | подтверждено | — |
| 29 | ISBN 0071364153 и 007138118X / 9780071381185 | 3.1 | метаданные IA `herooutlawbuildi0000mark`, `herooutlaw0000unse` | подтверждено | — |
| 30 | «Бомбора»: Дитя, Искатель, Мудрец, Герой, Бунтарь, Маг, Славный малый, Любовник, Шут, Служитель, Творец, Правитель; части «В поисках рая», «Оставить след в этом мире», «Один в поле не воин», «Упорядочить мир»; ч. I, VI, VII | 3.2; 3.3; 3.6; 7.3; 9.2 | PDF оглавления издателя [100] | подтверждено | — |
| 31 | «Бомбора», 2023: ISBN 978-5-04-172815-1, 432 с., серия «Маркетинг для немаркетологов», пер. А. Д. Сайфуллина | 7.3 | https://www.labirint.ru/books/950126/ | подтверждено | — |
| 32 | Переиздание «Бомборы»: ISBN 978-5-04-246600-7, 512 с., серия «Бомбора Foundation. Self-help», ред. М. А. Бердник | 7.3; [100] | https://eksmo.ru/book/geroy-i-buntar-kak-ispolzovat-arkhetipy-na-polzu-biznesu-i-tvorchestvu-ITD1500651/ | подтверждено | Переводчик на карточке не указан; Сайфуллина подтверждается Литресом и Лабиринтом |
| 33 | Эл. издание: ISBN 978-5-04-253913-8, 531 с., на Литресе с 23.09.2026, пер. Азалия Сайфуллина | 7.3 | https://www.litres.ru/book/carol-s-pearson-2/geroy-i-buntar-kak-ispolzovat-arhetipy-na-polzu-biznesu-74458861/ | подтверждено | — |
| 34 | «Питер», 2005: «Герой и бунтарь. Создание бренда с помощью архетипов», 336 с., ISBN 5-94723-616-8 | 7.3 | https://www.advertology.ru/index.php?name=Book&bid=2149171 (ISBN, 336 с., 2005); https://urss.ru/cgi-bin/db.pl?lang=Ru&blang=ru&page=Book&id=154748 (название, 2005, 336 с.); https://psytests.org/typo/heropm.html («СПб.: Питер, 2005») | подтверждено | Названия архетипов «Питера» легально не подтверждены — ⚠ оставлена, как в файле |
| 35 | КнигиКратко: Простодушный, Искатель, Мудрец | 3.6 | https://www.litres.ru/book/nataliya-grebenuk/kratkoe-soderzhanie-geroy-i-buntar-sozdanie-brendov-s-po-69484276/chitat-onlayn/ | подтверждено | Остальные имена в бесплатном фрагменте отсутствуют, что соответствует пометке «косвенно» |
| 36 | Пирсон 1986/1989: Innocent, Orphan, Wanderer, Warrior, Martyr, Magician; таблица Goal / Task / Fear | 4.1 | OCR библиотечного экземпляра 1989 года: https://archive.org/details/herowithinsixarc00pear | подтверждено | ISBN 006254862X, «Copyright © 1986, 1989», Expanded ed. — подтверждены |
| 37 | «the cyclical nature of the journey and the essential equality of the archetypes»; «in our conscious lives» | 2.3; 4.1 | тот же экземпляр | подтверждено | — |
| 38 | Самотест: 36 утверждений, пороги 9/15 | 4.1 | тот же экземпляр: виден бланк подсчёта по шести архетипам перед Appendix B | помечено ⚠ | Число пунктов и пороги r02 брал из скана неустановленного статуса |
| 39 | Ссылка [26] на скан The Hero Within | источник [26] | метаданные IA: коллекция `universallibrary`, доступ не ограничен, PDF открыт | удалено (ссылка); заменено | Открытый скан книги под копирайтом (© 1986, 1989); заменён на экземпляр с выдачей по записи того же издания |
| 40 | Пирсон 1991: 12 архетипов; Part I «The Dance of Ego, Self, and Soul» (с. 25), Part II «Preparation for the Journey» (с. 69), Part III «The Journey—Becoming Real» (с. 121; гл. 10 Seeker, 11 Destroyer) | 4.2 | OCR: https://archive.org/details/awakeningheroesw0000pear | подтверждено | Part IV «The Return—Becoming Free» в OCR не найден — оставлено по r14 |
| 41 | HMI (Form E) опубликован в книге | 4.2 | OCR [28]: «Appendix: The Heroic Myth Index (Form E) 299» | подтверждено; добавлена ссылка [28] | — |
| 42 | Fool: реакция на дракона «Play tricks on it» | 9.3 | OCR [28] | подтверждено | — |
| 43 | Сайт Пирсон: «The 12-Archetype System began with this book» | 4.2 | https://www.carolspearson.com/ | подтверждено | Фраза есть и на [32] |
| 44 | Пирсон: Realist «was once called Orphan» (цитата в кавычках) | 4.4; 9.1 | https://www.carolspearson.com/about/the-pearson-12-archetype-system-human-development-and-evolution | **исправлено** | Такой фразы на странице нет. Есть «can rightly be called Orphan» → Realist → «Everyperson»; «this same archetype is called Regular Guy/Gal». Цитата заменена точным пересказом |
| 45 | Пирсон: «do not actually have names»; Destroyer «would really not work»; «In the PMAI… it becomes the Revolutionary, but the name that marketers liked was Outlaw»; Outlaw в личной работе — «immoral and illegal»; «wild sides» | 4.4; 9.1 | тот же URL | подтверждено | — |
| 46 | 9.1, Jester: «сайт Пирсон говорит, что AHW использует «оригинальные» имена» | 9.1 | тот же URL (слов «original» и «Fool» на странице нет) | **исправлено** | Точнее: книги Адсон используют имена AHW, а «What Stories Are You Living?» — имена текущего PMAI; добавлено [42] |
| 47 | PMAI-2020: Orphan → Realist, Innocent → Idealist, Destroyer → Revolutionary; причина — Orphan и Destroyer внизу у большинства | 4.3 | руководство 2021 года (PDF): https://cdn.prod.website-files.com/5fc7fbb375805cc285353295/65d8ffa286160b97014347f7_PMAI_Manual_2021-1.pdf | подтверждено | Там же: на Destroyer рассматривались имена Outlaw, Initiate, Revolutionary |
| 48 | PMAI: 72 пункта, 6 на шкалу, 5-балльная шкала Лайкерта; база более 13 000; Inner Allies (3) / Inner Treasure Chest (8) / Blind Spot (1); «may, and should, change over time»; авторы и ISBN руководства 2021 года | 4.3; 4.4 | тот же PDF | подтверждено | — |
| 49 | Jester до 2020 года — «вывод исследования» | 4.3; 4.4; 9.1; 10.2 п. 5 | табл. 3.1 руководства 2021 года: у Jester нет пометки о смене имени | исправлено (вывод → источник) | То, что Fool 1991 года = Jester PMAI, остаётся выводом |
| 50 | Год PMAI: «2001 (psytests) / Manual 2003; официального подтверждения нет» | 4.3; 8 | руководство 2021 года: диссертация Марра (1995), CAPT приобрёл PMAI в 2001 году, предыдущее руководство — «PMAI Manual (2002)»; AbeBooks: 2003 | исправлено; расхождение 2002/2003 — ⚠ | — |
| 51 | Анонс 5–6 мая 2020 года, StoryWell, «equally positive», данные «since 2003» | 4.3; 8 | https://www.carolspearson.com/wp-imort-2/pmai-re-release | подтверждено | — |
| 52 | Цены $25 / $55 / $35; «Overlooked Ally» на странице покупки | 4.3 | https://www.storywell.com/purchase-the-pmai.htm | подтверждено | — |
| 53 | «the world's first scientifically validated archetype assessment tool» без коэффициентов; 12 шкал PMAI-2020 | 4.3; 8 | https://www.storywell.com/ | подтверждено | — |
| 54 | Buros: «1989–2020», Myers & Briggs Foundation, Гейнсвилл | 4.3 | https://marketplace.unl.edu/buros/pearson-marr-archetype-indicatorr.html | подтверждено | — |
| 55 | Кэмпбелл 1949: Pantheon / Bollingen Series XVII; 2-е изд. 1968, 3-е 2008; влияние Юнга, Фрейда, ван Геннепа, Ранка, Фрэзера | 5.1 | https://en.wikipedia.org/wiki/The_Hero_with_a_Thousand_Faces | подтверждено | — |
| 56 | 17 стадий, три части, p. 38; мономиф — из «Поминок по Финнегану» (p. 30, n. 35); Дандес; Мердок 1990; в «Hero's journey» Воглер датирован 1998 годом | 5.1; 5.2 | https://en.wikipedia.org/wiki/Hero%27s_journey | подтверждено | — |
| 57 | Русские издания Кэмпбелла 1997 года (София, пер. К. Семёнов, ISBN 5-220-00066-7; Ваклер / Рефл-бук / АСТ, пер. А. П. Хомик) | 5.1; 7.3 | https://ru.wikipedia.org/wiki/Тысячеликий_герой | подтверждено | «София» — СПб. |
| 58 | Воглер: 8 архетипов, 12 стадий, издания 1992 / 1998 / 2007 / 2020 | 5.2; 8 | https://en.wikipedia.org/wiki/The_Writer%27s_Journey:_Mythic_Structure_for_Writers | подтверждено | — |
| 59 | Меморандум — семь страниц; Disney; «went viral… by fax machines»; 1985 | 5.2 | https://en.wikipedia.org/wiki/Christopher_Vogler | подтверждено частично | «Seven pages» есть; Disney, факсы и год в статье не упомянуты (год уже под ⚠; [65] не перепроверен) |
| 60 | Список 12 стадий через запятые читался как 14 пунктов | 5.2 | — | исправлено (пунктуация) | Разделители заменены на «;» |
| 61 | Воглер: «flexible character functions rather than… rigid character types», «masks… worn by the characters temporarily», p. 34, ISBN 0-941188-13-2 | 1.2; 5.2 | https://stuff.mit.edu/afs/athena.mit.edu/user/m/b/mbarker/www/exercises/exer981026.txt | подтверждено | — |
| 62 | Русский Воглер: Альпина нон-фикшн, 2015, 480 с., тираж 3000, ISBN 978-5-91671-353-4, пер. М. Николенко; «русские названия остальных ролей не приведены (⚠)» | 5.2; 7.3; 10.2 п. 6 | https://fantlab.ru/edition158653 | подтверждено; **дополнено** | По оглавлению: Герой, Наставник, Привратники, Вестник, Оборотень, Тень, Союзник, Плут; перевод с 3-го издания. «Страж порога», «Глашатай», «Трикстер» — не термины перевода; это теперь оговорено |
| 63 | SB7: семь элементов; «The customer is the hero, not your brand»; Йода / Гэндальф; эмпатия и авторитет; три уровня проблемы | 5.3 | https://grahammann.net/book-notes/building-a-storybrand-donald-miller | подтверждено | — |
| 64 | «Метод StoryBrand»: Альпина Паблишер, 2020, 232 с.; бренд — «проводник»; пер. Е. Виноградова | 5.3; 7.2; 7.3 | https://alpinabook.ru/catalog/book-metod-storybrand/ ; WebSearch → карточка аудиокниги на Литресе (перевод Е. Виноградовой) | подтверждено | ISBN 978-5-9614-2738-7 не сверен (на странице издателя нет) |
| 65 | «Метод StoryBrand 2.0», пер. Любовь Макарина | 5.3; 7.3 | https://books.yandex.ru/books/PiCWF7Yo | подтверждено | Год на странице не указан — ⚠ оставлена |
| 66 | Конспект 2022: «клиенты ищут не другого героя, а проводника», «проводник или наставник» | 5.3; 7.2 | https://alexeykrol.com/blog/2022/01/20/87687612321/ | подтверждено | — |
| 67 | Мисс: четыре архетипа выживания (Child, Victim, Prostitute, Saboteur), «are up to us», 12 архетипов | 6.1 | https://publishersweekly.com/9780517703922 | подтверждено | — |
| 68 | Галерея Мисс: «their other eight personal archetypes», «circle of twelve», 9 семейств, 105 с., 2015, светлая и теневая сторона | 6.1 | https://myss.com/wp-content/uploads/2015/07/Gallery-of-Archetypes.pdf | подтверждено | — |
| 69 | Мисс 2013: 10 архетипов; тест на ArchetypeMe.com [74] | 6.1 | https://www.penguinrandomhouse.com/books/601468/archetypes-by-caroline-myss/9781401941109 | подтверждено; ArchetypeMe — помечено ⚠ | На странице [74] ArchetypeMe не упомянут; современное название издания — «Archetypes: A Beginner's Guide to Your Inner-net», «Who Are You?» — название твёрдой обложки 2013 года |
| 70 | Колода «Archetype Cards» — 80 карт | 6.1 | Barnes & Noble (домен не разрешается); https://www.penguin.co.nz/books/archetype-cards-9781401901844 | помечено ⚠ | Penguin NZ: 72 карты и 6 пустых; расхождение с 80 не разрешено |
| 71 | Хартвелл и Чен: HOW Books, 2012, ISBN 9781440308185; колода «sixty original archetype cards»; предисловие Jay Ogilvy; мотивы «belonging, stability, mastery and self-actualization» | 6.2 | https://www.archetypesinbranding.com/ ; https://openlibrary.org/isbn/9781440308185.json (HOW Books, 13.09.2012, 158 с.); https://www.bookshare.org/browse/book/652185 (F+W Media, 2012) | подтверждено | — |
| 72 | Структура 60 = 12 семейств × 5 и состав подархетипов | 6.2; 9.1 | https://www.slideshare.net/slideshow/archetypes-in-branding/49975573 — страница-проверка «Client Challenge» | не перепроверено; ⚠ оставлена | В файле уже есть оговорка, что структура взята со слайдов, а не из книги |
| 73 | Putnam: 12 имён и синонимы «also known as» (Maverick — Outlaw, Revolutionary, Rebel; Girl/Guy Next Door — Everyman, Realist, Friend; Entertainer — Jester…; Royal — Ruler…; Innocent — Purist, Idealist, Traditionalist и др.) | 6.3; 9.1 | 12 страниц https://kayeputnam.com/brand-archetypes/<архетип>/ | подтверждено | У Royal точнее: «Royalty, the Ruler, the King or Queen» |
| 74 | Putnam: «ровно три подтипа, всего 36» | 6.3; 8; 10.1 п. 5 | страницы Sage и Caregiver | **исправлено** | На 2026-10-16 у Sage четыре подтипа (+ The Analyst: Detective, Decoder, Translator), у Caregiver тоже четыре (+ The Advocate: Peacemaker, Social Worker); всего 38. Обновлялся ли сайт после 2026-10-15, не установлено |
| 75 | Квиз Putnam: 12 вопросов, около 3 минут, без e-mail, «250,000+», primary + secondary; «deliberately (and commit to it)»; «Rooted in Jungian psychology and applied to branding by Carol Pearson» | 6.3 | https://kayeputnam.com/quiz/ ; https://kayeputnam.com/brand-archetypes/ ; https://www.kayeputnam.com/ | подтверждено | — |
| 76 | Iconic Fox: 03.05.2018 / 01.12.2025, «12 Jungian Archetypes», правило 70%, «inspire them and make them feel empowered…», смесь 2–3, «95%» без источника | 3.x; 6.4 | копии Wayback: https://web.archive.org/web/20261001054329/https://iconicfox.com.au/brand-archetypes/ ; https://web.archive.org/web/20260327201752/https://iconicfox.com.au/can-you-mix-brand-archetypes/ | подтверждено | Живой сайт отдаёт проверяющему 403; в [69, 70] добавлены адреса копий |
| 77 | Хогсхед: 7 преимуществ, 49 архетипов, матрица © 2014 | 6.5 | https://www.howtofascinate.com/wp-content/uploads/2024/07/HTF-Matrix.pdf | подтверждено | — |
| 78 | Хогсхед: Kelton 2007, тест из 28 вопросов, «failed verification», «over 100,000» | 6.5 | https://en.wikipedia.org/wiki/Sally_Hogshead | подтверждено | Цифры 250 000 в статье нет — расхождение уже под ⚠ |
| 79 | «Триггеры 2010 года — passion, mystique, prestige, alarm, rebellion, trust, power» | 6.5 | https://www.richardpachter.com/2010/06/learn-how-seven-triggers-pique-our.html ; WebSearch (описания издателя Fascinate, 2010) | **исправлено** | В книге 2010 года: Lust, Mystique, Alarm, Prestige, Power, Vice, Trust. Источник NAIFA (404) заменён в [88] |
| 80 | Мур и Жиллетт: 1990, 159 с., «within a Jungian framework», четыре архетипа; «Only men's movement enthusiasts…» — о продолжении | 6.6; 8 | https://www.publishersweekly.com/9780062505972 | подтверждено | Фраза относится к «King Within» |
| 81 | Тени Мура и Жиллетта и мальчишеские архетипы — «точные названия ⚠» | 6.6 | OCR: https://archive.org/details/kingwarriormagic0000moor | исправлено (⚠ снята частично) | Tyrant / Weakling, Detached Manipulator / Denying "Innocent" One, Addicted / Impotent Lover, Sadist; Divine, Precocious, Oedipal Child — подтверждены; «Masochist» не найден — ⚠ |
| 82 | Русское издание Мура и Жиллетта: Литературная учеба, 2014, ISBN 978-5-88915-079-4, ред. Л. И. Карханина | 6.6; 7.3 | https://www.labirint.ru/reviews/goods/464858/ | подтверждено | — |
| 83 | Болен: юнгианский аналитик; 1984 и 1989; «The major Greek gods as male archetypal patterns» | 6.7 | https://en.wikipedia.org/wiki/Jean_Shinoda_Bolen ; https://www.jeanbolen.com/books | подтверждено | — |
| 84 | Три категории богинь (девственные, уязвимые, алхимическая) | 6.7 | OCR: https://archive.org/details/goddessesinevery0000bole ; https://archive.org/details/goddessesinevery00bolerich | подтверждено | В Википедии [93] категорий нет; опора — [95] с добавленными ссылками на библиотечные экземпляры |
| 85 | «Список 8 богов ⚠ не подтверждён» | 6.7; 8; 10.2 п. 10 | OCR оглавления: https://archive.org/details/godsineverymanne00bolerich | исправлено (⚠ снята) | Зевс, Посейдон, Аид («The Father Archetype»); Аполлон, Гермес, Арес, Гефест, Дионис («The Generation of the Sons») |
| 86 | Говард-Спинк, Admap, 30.09.2002: «universal and eternal truth», «champion brands», «just some of many archetypes available» | 6.8 | https://www.warc.com/content/article/admap/using-archetypes-to-build-stronger-brands/en-gb/76945 | подтверждено | — |
| 87 | Added Value «Archetype Game», 18.07.2008, опора на Юнга, Говард-Спинк не упомянут | 6.8 | https://www.mrweb.com/drno/printable/pn8627.htm | подтверждено | — |
| 88 | Merlo и др. 2023: «strong brands tend to leverage multiple archetypes at a time» | 3.5 | https://ideas.repec.org/a/eee/bushor/v66y2023i5p615-629.html | подтверждено | — |
| 89 | WPP BAV: бренды с силой в нескольких зонах «more interesting, engaging and successful» | 3.5 | https://wppbav.com/insights/brand-archetypes/ | подтверждено | — |
| 90 | Spangenberg 2021: четыре новых кластера; 242 взрослых; 18 из 30 брендов «flexible» | 3.3; 3.5 | https://digital.lib.washington.edu/researchworks/items/c15713ba-a19c-4da6-9ca8-2758d42560e1 | подтверждено частично | На странице записи есть только аннотация (четыре кластера); цифры — из полного текста, его проверяющий не открывал |
| 91 | МИФ 2024: ISBN 978-5-00214-422-8, 480 с., пер. А. Багрянцева, серия «МИФ. Психология архетипов» | 7.3 | https://www.labirint.ru/books/1002571/ | подтверждено | — |
| 92 | Имена в переводе МИФ, стадии «Подготовка», «Путешествие», «Возвращение», «качества сильного Эго», слова «Разрушитель» нет | 4.2; 4.4; 9.2 | https://www.litres.ru/book/carol-s-pearson-2/probuzhdenie-vnutrennego-geroya-12-arhetipov-kotorye-pom-70498927/chitat-onlayn/ | подтверждено | Destroyer = «Бунтарь» выводится по позиции в списке, как и сказано в файле |
| 93 | I-am-Brand: 12 имён по четырём группам, опора на Юнга, Пирсон 1986 и Марк–Пирсон 2001, тест; 04.08.2023 | 7.1; 7.2; 9.2 | https://i-am-brand.ru/knowledge-base/arhetipy-v-lichnom-brende/ | подтверждено | — |
| 94 | Адт: 12 имён (Балагур, Влюблённый, Друг, Хранитель, Идеалист…), «по модели Кэрол Пирсон», ≈2 минуты, Telegram-бот, «свыше 250 000»; «на главной — более 30 000» | 7.1 | https://alinaadt.ru/archetypes ; https://alinaadt.ru/ | подтверждено; уточнено | «Более 30 000» на главной — люди, которых она «вывела на лучшее понимание себя», а не число прохождений теста; формулировка уточнена |
| 95 | Гас: синонимы «Заботливый (родитель, наставник)», «Простодушный (ребенок, дитя)» и др.; опора на Марк–Пирсон и Дули | 7.1; 7.2; 9.2 | https://teletype.in/@katyagas/czNfmod6BTZ ; https://yogajournal.ru/conscious/psychology/kak-s-pomoshchyu-arkhetipov-upakovat-lichnyy-brend-chtoby-vlyublyat-tselevuyu-auditoriyu-s-pervogo-v_518/ | подтверждено | Дули упомянут только в статье Yoga Journal [121] |
| 96 | Skillbox: «Невинный или Идеалист», «Путешественник», «Воин или Герой», «Мученик, Альтруист или Родитель», «Разрушитель, Революционер», «Сирота… Гражданин или Реалист», «Глупец», «Создатель или Креатор» | 7.2; 9.2 | https://skillbox.ru/media/design/archetypes-in-simple-words/ | подтверждено | — |
| 97 | Левшин: Невинный, Обыватель, Разбойник, Исследователь, Волшебник, Опекун и др.; «профессиональная помощь» | 7.1; 9.2 | https://nokc.org.ru/nokc-style/ | подтверждено | — |
| 98 | Леонова: 12 тюркских архетипов в 4 группах; ISBN 978-5-0062-9568-1; прямых соответствий во фрагменте нет | 7.1; 9.3 | https://books.yandex.ru/books/PKGjPsYP/read-online | подтверждено | — |
| 99 | Лытов и Орский (2001, «Соционика, ментология и психология личности», № 6): 8 «архетипов»; Рожков и Краско; Ульяновский | 7.1; 7.2 | https://cyberleninka.ru/article/n/mifodizayn-kak-sotsiokulturnyy-fenomen | подтверждено | Первоисточник 2001 года по-прежнему не открыт (⚠ в файле есть) |
| 100 | psytests: PMAI «Carol Pearson, Hugh Marr (2001)», перевод 2023 года; HMI Form E | 4.3 | https://psytests.org/typo/heropm.html | подтверждено | — |
| 101 | Пирсон — PhD Rice, «applied the 12-archetype theory to branding» | 3.1 | https://www.carolspearson.com/about/about-carol-s-pearson-and-her-archetypal-journey ; https://en.wikipedia.org/wiki/Carol_S._Pearson | подтверждено | В Википедии «What Story Are You Living?» — 2006 (расхождение 2006/2007 в файле оставлено) |
| 102 | Таблица 9.3: «Карточка «Дитя» запланирована для Мисс» | 9.3 | папка `02-cards/` | исправлено | Карточка `extra-myss-child.md` уже есть; остальные отметки «Да» в столбце соответствуют файлам `extra-*.md` |
| 103 | Таблица 9.1–9.2: пометки (А) / (П) / (О) | 9 | URL из строк 44–46, 49, 73–74; см. также п. 104 | подтверждено с двумя исправлениями (пп. 44, 46) | Выдуманных соответствий под меткой (А) не найдено. Все связки Хартвелл, Воглера, Мура и Жиллетта, Болен и Мисс помечены (О). (А) у Putnam подтверждено синонимами «also known as» на её страницах; (А) у Пирсон — страницей [32] и руководством [42] |
| 104 | Происхождение русских названий: «Проводник» ← перевод StoryBrand (2020); «Наставник» ← Воглер (2015); «Хранитель» — у Лытова и Орского (2001) | 7.2 | [110] alpinabook, [112] alexeykrol, [108] fantlab, [131] cyberleninka | подтверждено | Формулировки о происхождении в файле — оценка исследования, они помечены как вывод r04 |

---

## 3. Проверка URL

«Открывается?» — ответ сервера на 2026-10-16. «Подтверждает?» — подтверждает ли страница утверждение, к которому привязана в файле.

| URL | Открывается? | Подтверждает? | Действие |
|---|---|---|---|
| прежняя ссылка [2] на скан Aion в коллекции IA `collectedworkscgjung` (адрес не приводится) | да; **открытый скан, PDF скачивается** | — | ссылка удалена (скан книги под копирайтом, авторизованность не установлена); заменена на библиотечный экземпляр |
| https://archive.org/details/aionresearchesin0009_part2 (новая, [2]) | да; выдача по записи | да (Aion §§13–14, 29) | добавлена |
| https://archive.org/details/archetypescollec0000jung (новая, [1]) | да; выдача по записи | да (CW 9i §99 и ещё 13 цитат) | добавлена |
| https://archive.org/details/symbolsoftransfo0005jung (новая, [3]) | да; выдача по записи | да (CW 5, «never exceeds certain natural limits») | добавлена |
| https://archive.org/details/dli.ernet.7919 [4] | да; открытый скан DLI | не проверялось | оставлено с ⚠: перевод 1923 года в США в общественном достоянии, но авторизованность скана не установлена |
| https://doi.org/10.1111/j.2044-8295.1919.tb00003.x [5] | метаданные Crossref | да | — |
| https://www.psychceu.com/jung/sharplexicon.html [6] | да | да | — |
| https://link.springer.com/referenceworkentry/10.1007/978-3-642-27771-9_45-4 [7] | 303 → страница входа | нет (недоступно) | пометка в [7] уточнена |
| https://pmc.ncbi.nlm.nih.gov/articles/doi/10.3390/bs3040541 [12] | да | да | — |
| DOI [13]–[20], [48]–[50], [52], [56], [57] (16 шт.) | метаданные Crossref | да (библиографические данные) | — |
| https://archive.org/details/herooutlawbuildi0000mark [22] | да; выдача по записи | да | — |
| https://archive.org/details/herooutlaw0000unse [22] | да; выдача по записи | да (ISBN) | — |
| https://archive.org/details/consumerbehavior0000mich_edi11 ; https://archive.org/details/consumerbehavior0000solo_n4t7 [24] | да; выдача по записи | метаданные | — |
| прежняя ссылка [26] на скан The Hero Within в коллекции IA `universallibrary` (адрес не приводится) | да; **открытый скан Universal Library, PDF скачивается** | — | ссылка удалена; заменена |
| https://archive.org/details/herowithinsixarc00pear (новая, [26]) | да; выдача по записи | да | добавлена |
| https://archive.org/details/herowithinsixarc0000pear [27] | да; выдача по записи | да (1998, HarperSanFrancisco) | — |
| https://archive.org/details/awakeningheroesw0000pear [28] | да; выдача по записи | да | — |
| https://archive.org/details/writersguidetofi0000lyon [29]; https://archive.org/details/transpersonalper0000unse [30] | да; выдача по записи | метаданные | — |
| https://www.carolspearson.com/ [31] | да | да | — |
| https://www.carolspearson.com/about/the-pearson-12-archetype-system-human-development-and-evolution [32] | да | частично | неточная цитата («was once called Orphan») и формулировка про «оригинальные» имена исправлены |
| https://www.carolspearson.com/about/about-carol-s-pearson-and-her-archetypal-journey [34] | да | да | — |
| https://www.carolspearson.com/wp-imort-2/pmai-re-release [35] | да | да | — |
| https://www.storywell.com/ [36] | да | да | — |
| https://www.storywell.com/purchase-the-pmai.htm [37] | да | да | — |
| https://marketplace.unl.edu/buros/pearson-marr-archetype-indicatorr.html [40] | да | да | — |
| https://www.abebooks.com/9780935652741/PMAI-Manual-Guide-Interpreting-Pearson-Marr-0935652744/plp [41] | да | да (2003) | добавлена ⚠: руководство 2021 года называет 2002 |
| PMAI Manual 2021 (PDF) [42] | да | да | — |
| https://psytests.org/typo/heropm.html [44] | да | да | — |
| https://en.wikipedia.org/wiki/Carol_S._Pearson [46] | да | да | — |
| https://digital.lib.washington.edu/researchworks/items/c15713ba-a19c-4da6-9ca8-2758d42560e1 [51] | да | частично (аннотация) | — |
| https://ideas.repec.org/a/eee/bushor/v66y2023i5p615-629.html [52] | да | да | — |
| https://wppbav.com/insights/brand-archetypes/ [55] | да | да | — |
| https://en.wikipedia.org/wiki/The_Hero_with_a_Thousand_Faces [60] | да | да | — |
| https://en.wikipedia.org/wiki/Hero%27s_journey [61] | да | да | — |
| https://en.wikipedia.org/wiki/The_Writer%27s_Journey:_Mythic_Structure_for_Writers [62] | да | да | — |
| https://en.wikipedia.org/wiki/Christopher_Vogler [63] | да | частично (семь страниц — да; Disney и год — нет) | — |
| https://stuff.mit.edu/afs/athena.mit.edu/user/m/b/mbarker/www/exercises/exer981026.txt [64] | да | да | — |
| https://grahammann.net/book-notes/building-a-storybrand-donald-miller [66] | да | да | — |
| https://iconicfox.com.au/brand-archetypes/ [69] | 403 (защита от ботов) | да — по Wayback от 01.10.2026 | в [69] добавлен адрес копии |
| https://iconicfox.com.au/can-you-mix-brand-archetypes/ [70] | 403 | да — по Wayback от 27.03.2026 | в [70] добавлены адрес копии и дата публикации |
| https://myss.com/wp-content/uploads/2015/07/Gallery-of-Archetypes.pdf [71] | да | да | — |
| https://publishersweekly.com/9780517703922 [72] | да | да | — |
| https://www.penguinrandomhouse.com/books/601468/archetypes-by-caroline-myss/9781401941109 [74] | да | частично (10 архетипов — да; ArchetypeMe — нет) | в тексте ⚠ |
| https://valsec.barnesandnoble.com/w/archetype-cards/caroline-myss/1005803894 [75] | **нет** (домен не разрешается) | — | помечено «⚠ ссылка недоступна на 2026-10-16»; добавлена Penguin NZ |
| https://www.penguin.co.nz/books/archetype-cards-9781401901844 (новая, [75]) | да | 72 карты + 6 пустых | добавлена |
| https://www.slideshare.net/slideshow/archetypes-in-branding/49975573 [76] | страница-проверка «Client Challenge» | не проверено | структура 12 × 5 остаётся под ⚠ (как в файле) |
| https://www.archetypesinbranding.com/ [77] | да | да | — |
| https://www.bookshare.org/browse/book/652185 [80] | да | да | — |
| https://www.kayeputnam.com/ [82] | да | да | — |
| https://kayeputnam.com/brand-archetypes/ и 12 страниц архетипов [83] | да | частично | число подтипов исправлено (38) |
| https://kayeputnam.com/quiz/ [84] | да | да | — |
| https://www.howtofascinate.com/wp-content/uploads/2024/07/HTF-Matrix.pdf [85] | да | да | — |
| https://en.wikipedia.org/wiki/Sally_Hogshead [87] | да | да | — |
| https://at.naifa.org/2012/09/09/you-can-fascinate [88] | **нет** (404) | — | помечено «⚠ ссылка недоступна на 2026-10-16»; основной источник [88] заменён |
| https://www.richardpachter.com/2010/06/learn-how-seven-triggers-pique-our.html (новая, [88]) | да | да (триггеры 2010 года) | добавлена |
| https://www.publishersweekly.com/9780062505972 [89] | да | да | — |
| https://archive.org/details/kingwarriormagic0000moor (новая, [92]) | да; выдача по записи | да (тени) | добавлена |
| https://en.wikipedia.org/wiki/Jean_Shinoda_Bolen [93] | да | частично (категорий богинь нет) | ссылка для категорий перенесена на [95] |
| https://www.jeanbolen.com/books [94] | да | да | — |
| https://archive.org/details/godsineverymanne00bolerich (новая, [94]) | да; выдача по записи | да (8 богов) | добавлена |
| https://archive.org/details/goddessesinevery0000bole ; https://archive.org/details/goddessesinevery00bolerich (новые, [95]) | да; выдача по записи | да (категории) | добавлены |
| https://www.warc.com/content/article/admap/using-archetypes-to-build-stronger-brands/en-gb/76945 [96] | да | да | — |
| https://www.mrweb.com/drno/printable/pn8627.htm [98] | да | да | — |
| https://insideag.wpp.com/wppedcream/2008/research_1a.html [99] | **нет** (домен не разрешается) | — | помечено «⚠ ссылка недоступна на 2026-10-16» |
| https://cdn.eksmo.ru/v2/ITD000000001500651/PDF/ITD000000001500651_TOC.pdf [100] | да | да | — |
| https://eksmo.ru/book/geroy-i-buntar-kak-ispolzovat-arkhetipy-na-polzu-biznesu-i-tvorchestvu-ITD1500651/ [100] | да | да (переводчика на карточке нет) | — |
| https://www.litres.ru/book/carol-s-pearson-2/geroy-i-buntar-kak-ispolzovat-arhetipy-na-polzu-biznesu-74458861/ [101] | да | да | — |
| https://www.labirint.ru/books/950126/ [102] | да | да | — |
| https://urss.ru/cgi-bin/db.pl?lang=Ru&blang=ru&page=Book&id=154748 [103] | да | частично (без ISBN и издательства) | — |
| https://www.advertology.ru/index.php?name=Book&bid=2149171 [103] | да (кодировка частично битая) | да (ISBN, 336 с., 2005) | — |
| https://www.litres.ru/book/nataliya-grebenuk/kratkoe-soderzhanie-geroy-i-buntar-sozdanie-brendov-s-po-69484276/chitat-onlayn/ [104] | да | да (три имени) | — |
| https://www.litres.ru/book/carol-s-pearson-2/probuzhdenie-vnutrennego-geroya-12-arhetipov-kotorye-pom-70498927/chitat-onlayn/ [105] | да | да | — |
| https://www.labirint.ru/books/1002571/ [106] | да | да | — |
| https://fantlab.ru/edition158653 [108] | да | да | в 5.2 и 7.3 добавлены названия ролей из перевода |
| https://ru.wikipedia.org/wiki/Тысячеликий_герой [109] | да | да | — |
| https://alpinabook.ru/catalog/book-metod-storybrand/ [110] | да | да (2020, 232 с., «проводник») | — |
| https://www.chitai-gorod.ru/product/metod-storybrand-rasskazhite-o-svoem-brende-tak-chtoby-v-nego-vlyubilis-2784853 [110] | **нет** (403) | — | не менялось: основная ссылка [110] (издатель) рабочая |
| https://books.yandex.ru/books/PiCWF7Yo [111] | да | да | — |
| https://alexeykrol.com/blog/2022/01/20/87687612321/ [112] | да | да | — |
| https://www.labirint.ru/reviews/goods/464858/ [113] | да | да | — |
| https://alinaadt.ru/ ; https://alinaadt.ru/archetypes [115] | да | да | формулировка о «30 000» уточнена |
| https://i-am-brand.ru/knowledge-base/arhetipy-v-lichnom-brende/ [119] | да | да | — |
| https://teletype.in/@katyagas/czNfmod6BTZ [120] | да | да | — |
| https://yogajournal.ru/conscious/psychology/kak-s-pomoshchyu-arkhetipov-upakovat-lichnyy-brend-chtoby-vlyublyat-tselevuyu-auditoriyu-s-pervogo-v_518/ [121] | да | да | — |
| https://nokc.org.ru/nokc-style/ [123] | да | да | — |
| https://books.yandex.ru/books/PKGjPsYP/read-online [125] | да | да | — |
| https://cyberleninka.ru/article/n/mifodizayn-kak-sotsiokulturnyy-fenomen [131] | да | да | — |
| https://skillbox.ru/media/design/archetypes-in-simple-words/ [137] | да | да | — |

---

## 4. Сводка

- **Проверено утверждений:** 104 строки таблицы раздела 2. Это более 120 отдельных фактов: цитаты, номера параграфов, выходные данные, списки и соответствия названий.
- **Проверено URL:** около 96 адресов из списка источников (из них 16 DOI через Crossref) плюс 12 страниц архетипов Putnam и 10 новых адресов, добавленных при проверке. Не открылись: Springer [7] (перенаправление на вход), Barnes & Noble [75] и WPP [99] (домен не разрешается), NAIFA [88] (404), SlideShare [76] (проверка от ботов), Читай-город [110] (403). Iconic Fox [69, 70] отдаёт 403, но проверен по Wayback.
- **Исправлено ошибок по существу — 9:**
  1. Хогсхед: триггеры издания 2010 года указаны неверно — правильно Lust, Mystique, Alarm, Prestige, Power, Vice, Trust.
  2. Putnam: «ровно три подтипа, 36» — на 2026-10-16 у Sage и Caregiver по четыре, всего 38.
  3. Пирсон: неточная «цитата» «was once called Orphan» (4.4, 9.1) заменена точным пересказом со словами страницы.
  4. Таблица 9.1, Jester: несуществующее на странице слово «оригинальные» заменено точной формулировкой; добавлено [42].
  5. Источник [2] (Aion) ошибочно назван библиотечным сканом: это открытый для скачивания скан книги под копирайтом. Ссылка удалена и заменена; непроверенные параграфы Aion (§33, §§44–46) получили ⚠.
  6. Источник [26] (The Hero Within, 1989) вёл на открытый скан Universal Library. Ссылка удалена и заменена на библиотечный экземпляр; детали самотеста получили ⚠.
  7. Марк–Пирсон: левый полюс оси — Belonging/People (было «вероятно, Belonging ⚠»).
  8. Марк–Пирсон: девиз Шута есть в OCR книги (было «не найден»).
  9. PMAI: история уточнена по руководству 2021 года — диссертация 1995 года, CAPT с 2001 года, предыдущее руководство 2002 или 2003 года; то, что Jester не переименовывался в 2020 году, теперь опирается на табл. 3.1, а не на вывод.
- **Уточнения и дополнения (без ошибки по существу):**
  - с 17 цитат CW 9i / CW 9ii / CW 5 снята пометка ⚠ — они сверены по легальным библиотечным экземплярам, в том числе CW 9i §99 вместе с номером параграфа;
  - три фразы Марк–Пирсон, которые держались только на копии r08, теперь опираются на [22];
  - подтверждены список 8 богов Болен и английские названия теней у Мура и Жиллетта;
  - в 5.2 и 7.3 внесены названия ролей и стадий Воглера из русского перевода;
  - уточнены: пунктуация списка стадий Воглера, атрибуция определения Персоны, цифра «30 000» у Адт, наличие карточки «Дитя» Мисс;
  - к пяти битым или недоступным ссылкам добавлены пометки или замены.
- **Что осталось под ⚠ (не подтверждено):**
  - CW 9i: §3, §91, §§310/413 (биполярность), §81, §100, §414, триада Коры, «secondarily» (§90); номера параграфов, кроме §99 и §§221–222; CW 5 — всё, кроме цитаты §450; Aion §33, §§44–46;
  - Марк–Пирсон: страницы 42 и 1–2 по r08; Мег Райан и Том Хэнкс; «primary archetypal identity, secondary identity»; название Part I; теория мотивации под осями; английские страницы глав 10–15;
  - названия архетипов в «Питере» 2005 года (легального экземпляра нет);
  - Хартвелл и Чен: структура 12 × 5 (SlideShare недоступен, книга не проверена);
  - Мисс: число карт колоды (72 или 80), ArchetypeMe.com, дома колеса;
  - «Masochist» у Мура и Жиллетта;
  - PMAI: год предыдущего руководства (2002 или 2003);
  - «What Story Are You Living?» (2006 или 2007);
  - год «Метода StoryBrand 2.0» и ISBN «Метода StoryBrand»;
  - Воглер: дата меморандума и Disney;
  - Spangenberg: цифры 242 и «18 из 30» по полному тексту;
  - Iconic Fox: живая версия сайта (проверено только по Wayback);
  - Putnam: обновлялся ли набор подтипов между 15 и 16 октября 2026 года;
  - Психологические типы [4]: статус скана DLI.
- **Соблюдение правил:** цитат длиннее ~25 слов нет; ссылок на неавторизованные копии после правок нет (две найденные заменены); рекомендаций по проектированию продукта нет; номера [n] соответствуют списку (1–150, без пропусков и лишних); собственные выводы помечены «оценка исследования» или (О).
