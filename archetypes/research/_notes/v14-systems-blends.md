# v14 — независимая проверка раунда 2: `01-systems.md` и `03-blends.md`

- **Дата:** 2026-10-16.
- **Проверяющий:** v14. В сборе, написании и доукомплектовании (c07) не участвовал.
- **Предмет:** всё, что добавлено и изменено в раунде доукомплектования c07 (`git diff 6ca98c6 HEAD -- archetypes/research/01-systems.md archetypes/research/03-blends.md`; протокол `_notes/c07-systems-blends.md`), и межфайловая сверка этих двух файлов с `02-cards/`, `04-diagnostics.md`, `05-personal-brand.md`, `06-esoteric-links.md` и заметками c03, c04.
- **Рамка:** только исследование; продукт не проектировался.
- **Изменены только:** `01-systems.md`, `03-blends.md` и этот протокол. Git-коммитов нет. Правки помечены в файлах «v14».
- **Новые источники:** `01-systems.md` — [175]; `03-blends.md` — [117]. Добавлены в конец списков, прежние номера не менялись.

## 1. Методика

1. **Книги — только легальный поиск по тексту.** Полнотекстовый поиск Open Library (`openlibrary.org/search/inside.json`) по экземплярам Internet Archive с ограниченным доступом. Полные тексты, PDF и djvu не скачивались. Статус каждого из 25 экземпляров IA, на которые ссылаются оба файла, проверен через `archive.org/metadata/<id>`: у всех `access-restricted-item: true`. Часть экземпляров доступна только читателям с нарушениями зрения (коллекция `printdisabled` без `inlibrary`); формулировки «с выдачей по записи» в 01 [27] и во вводной к [158–161] уточнены. Поиск возвращает только фрагменты без номеров страниц, поэтому страницы так не подтверждаются. Служебный эндпоинт поиска BookReader (`fulltext/inside.php`) требует входа; после отказа он не использовался.
2. **Сайты — WebFetch и curl по прямым адресам.** Для Википедии — сырой текст статьи (`index.php?action=raw`) с описательным User-Agent. Для копий Wayback Machine — curl (WebFetch к web.archive.org не допускается).
3. **КиберЛенинка — поисковый API сайта** (`cyberleninka.ru/api/search`): он возвращает OCR-фрагменты, страницы статей закрыты капчей.
4. **Метаданные файлов:** `pdfinfo` (PDF «Лабиринта»), `file` и заголовки HTTP (документ psy.su).
5. **WebSearch не использовался.** Квота исчерпана другими агентами. Страницы выдачи поисковиков не открывались.
6. **Сбои сети.** С 13:15 `openlibrary.org` и `web.archive.org` сбрасывали соединение через прокси (`ws_closed_mid_exchange`). Open Library с перерывами отвечала с 14:08 до 15:05; web.archive.org не ответил ни разу до конца сеанса. Запросы повторялись фоновыми скриптами с паузами (раздел 2.4); что так и не удалось проверить, указано в таблицах.
7. **Пиратские копии** не использовались. Grep по обоим файлам на ebin.pub, z-lib, libgen, pdfdrive, pdfcoffee, studylib, psytests.org/, dokumen.pub, scribd, flibusta, `archive.org/download` и `archive.org/stream` ничего не нашёл. Есть только описательные упоминания pdfdrive в оговорке r01 и psytests в [44] и [45], где ссылки удалены ещё раньше.
8. **Личные данные.** В запросах их не было. Адрес электронной почты из тезисов «Ломоносов-2025» в файлы не переносился. Сведения о частной жизни персон из статей Википедии в 6.6 не включались.
9. **Скрипты:** проверка сплошной нумерации [n], висячих и неиспользованных ссылок (`refcheck.py`); проверка числа ячеек в таблицах (`tblcheck.py`); поиск цитат длиннее 18 слов в добавленных строках; поиск формулировок проектирования продукта в добавленных строках.

## 2. Проверка утверждений

Вердикты: **подтверждено**; **исправлено** — утверждение было неверным и заменено; **уточнено** — в основном верно, формулировка или атрибуция поправлены; **устарело** — опровергнуто данными из другого файла базы; **не проверено** — источник был недоступен, причина указана.

### 2.1. Новые утверждения из источников (п. 1 задания)

| № | Файл | Утверждение | Чем проверено | Вердикт | Комментарий |
|---|---|---|---|---|---|
| 1 | 01 | «Питер» 2005: 12 названий и 4 группы по тезисам «Ломоносов-2025», ссылка «…2005. – 336 с.» | PDF тезисов confhub.ru, текст | подтверждено | В тезисах «Тоска по Раю», «Оставить в мире свой след», «Ни один человек не является островом», «Структурирование мира»; «Славный малый» со строчной буквы; осей в тезисах нет. Место издания в тезисах — «М.», хотя «Питер» — СПб. |
| 2 | 01 | Четыре оси «Питера» в таблице Подкар (2007) | API КиберЛенинки, OCR таблицы | подтверждено | «Стабильность и контроль» — Заботливый, Творец, Правитель; «Риск и мастерство» — Герой, Бунтарь, Маг; «Принадлежность и обладание» — Славный малый, Любовник, Шут; «Независимость и самореализация» — Простодушный, Искатель, Мудрец. Колонки таблицы у Подкар — «Архетипы подготовки / пути / возвращения», то есть стадии Пирсон 1991; в файл не вносилось. Выходные данные «2007, № 3 (8), с. 113–» подтверждены |
| 3 | 01 | Переводчики и выходные данные «Питера» [169] | API КиберЛенинки | подтверждено | Титова и Ковалева (2022): «пер. с англ.: И. Малкова, Д. Раевская, А. Сухенко… 335 с.». ISBN 5-94723-616-8 — у Суворовой (2024). «Под ред. В. Домнина, А. Сухенко… 336 с.», серия «Маркетинг для профессионалов» — у Родиной (2016). Статьи Выпряжкина, Дворниковой и Инешиной существуют, но их библиографические фрагменты в выдаче API v14 не попались |
| 4 | 01 | «Славный Малый [167, 168]» в столбце «Питер» | те же источники | уточнено | В обоих источниках «Славный малый». Исправлено в 3.6, 7.3 и 9.2; вариант r04 «Славный Малый» указан в скобках |
| 5 | 01 | Оглавление «Бомборы» 2023 совпадает с переизданием; различаются объём (432 и 512 с.) и порядок предисловий | PDF «Лабиринта» (pdfinfo: создан 11.04.2023); карточка labirint.ru/books/950126 (ISBN 978-5-04-172815-1, 2023, 432 с., пер. Сайфуллина А. Д.); PDF оглавления Эксмо для 978-5-04-246600-7 | подтверждено | В самом PDF ISBN нет, связь с изданием — по карточке товара 950126. В 2023 году «Предисловие» стоит перед «Предисловием от российского издателя», в переиздании — наоборот |
| 6 | 01 | Пост Хартвелл 27.04.2016: «I changed the Outlaw to the Rebel», «…the Ruler to the Sovereign», «…the Regular Guy/Gal to the Citizen», «expanding on Mark & Pearson's twelve», Everyman, Generalist, «in hindsight» — четыре перемещения, пять планируемых архетипов, «greater nuance, sophistication and layering» | curl страницы, текст | подтверждено дословно | Все фразы на месте |
| 7 | 01 | Замена (О) на (А) в 12 ячейках таблицы 9.1 | пост Хартвелл | подтверждено | Три переименования автор описывает прямо. Для девяти совпадающих имён (А) опирается на «shifting the fundamental heads of the families» и «expanding on Mark & Pearson's twelve». Это чтение источника, а не дословное утверждение, но допустимое |
| 8 | 01 | Shaman, Engineer, Ambassador и Guardian в книге стоят не там, куда автор перенесла бы их «in hindsight»; это совпадает со слайдами 2014 года | пост Хартвелл; [76] по 01 | подтверждено (вывод) | Логика корректна |
| 9 | 01 | 12 домов колеса Мисс, «corresponding to the twelve houses of the zodiac», «Chart of Origin» по интуитивной процедуре | WebFetch myss.com «The Archetypal Wheel» | подтверждено | Названия и пояснения домов совпадают; у 12-го дома пояснения нет |
| 10 | 01 | «Процедура выбора восьми архетипов по книге в c07 не проверялась (на myss.com — только правило отбора из Галереи)» | myss.com «Determining Your Archetypes» и «Casting Your Chart of Origin»; `06-esoteric-links.md`, раздел 2.9 | устарело → обновлено | На сайте описаны обе процедуры: отбор восьми по критерию «trace its life-long influence on you» и расстановка по домам (24 листка, «best serve me»). Добавлен [175]; по тексту книги ⚠ оставлено |
| 11 | 01 | «The Masochist» в «The Warrior Within» (1992) | поиск Open Library (два экземпляра 1992 года) | подтверждено | «neither the Sadist nor the Masochist (the two poles of the Warrior's Shadow)»; схема полюсов «(Active Pole) … (Passive Pole) The Sadist The Masochist»; гл. 7 «The Masochist: A Dishonest Warrior» (с. 121) |
| 12 | 01 | PMAI: «the PMAI assessment published in 2002»; «Pearson, C. S. & Marr, H. K. (2002). The PMAI® Manual»; CAPT — с 2001 года | PDF руководства 2021 года (pdftotext) | подтверждено | Дословно: «CAPT became the publisher in 2001», «the previous PMAI Manual (2002)», «with our publisher, since 2002» |
| 13 | 01 | PMAI Manual в каталоге LoC — 01.08.2003, 101 с., LCCN 2003059616; буклет 2002 года, 57 с., LCCN 2002073536 | JSON записей OL11503426M и OL20009488M (source_records: `marc_loc_2016`) | подтверждено | Совпадают название, подзаголовок, дата, объём, LCCN и ISBN |
| 14 | 01 | «Почему руководство 2021 года пишет 2002 — возможно, дата авторского права» (c07) | `04-diagnostics.md`, разделы 2.4 и 8.2: Copyright Office | уточнено | У руководства в реестре — публикация 15.10.2003 (TX0006085421), у «Introduction to archetypes» — регистрации 2002 и 2005 годов. Гипотеза c07 не подтверждается; добавлена более вероятная версия с пометкой «оценка исследования» |
| 15 | 01 | МАК «12 Архетипов плюс» (Кадыров, Скоробач): опора на «Систему 12 архетипов» К. Пирсон и М. Марк и на Юнга; имена набора Пирсон 1991; два типа карт; ведущий и отвергаемый архетип; файл создан 15.01.2015 | документ psy.su (82 944 байт; Last-Modified 15.01.2015; Create Time 15.01.2015) | подтверждено | «24 карты» — подсчёт 12 × 2 (по две карты на архетип, «1.1 и 1.2» … «12.1 и 12.2»), прямо числа в документе нет; допустимо. Страна в документе не указана — ⚠ в файле стоит верно |
| 16 | 01 | Martyr → Altruist в 3-м издании (1998); ряд таблицы 6 ↔ 12 | поиск Open Library | подтверждено; уточнено | «GETTING ACQUAINTED WITH THE ALTRUIST ARCHETYPE»; «Internal Archetype Orphan Wanderer Warrior Altruist Innocent Magician». Ряд таблицы продолжается: «…Wanderer Seeker Warrior Warrior Altruist Caregiver Altruist Destroyer Lover Creator Ruler Magician Magician Sage…» — Altruist стоит рядом и с Caregiver, и с Destroyer. Добавлено в 01, раздел 4.1, с пометкой «оценка исследования» |
| 17 | 01 | Пирсон 1991: главы 6–17 со страницами и Part V «Honoring Diversity—Transforming Your World» (с. 233) | поиск Open Library | подтверждено | Фрагмент оглавления: «…Fool 220 Part V: Honoring Diversity— Transforming Your World 233 18. From Duality to Wholeness…». В Part V есть ещё гл. 18; в файл не вносилось (второстепенно) |
| 18 | 01 | Марк и Пирсон: названия Part I, Part VI, гл. 20 и 21 | поиск Open Library | подтверждено | «Part I Primal Assets: A System for the Management of Meaning»; «Part VI Finding True North: Positioning an Archetypal Brand»; «Chapter 20 The Real McCoy: Branding and Organizational Congruence Chapter 21 Leaving a Legacy: The Ethics of Archetypal Marketing». По указателю гл. 20 — с. 344–355; колонтитулы «263 264 FINDING TRUE NORTH» согласуются с «Part VI — около с. 263». Слова «Maslow» и «hierarchy of needs» в книге среди первых 50 совпадений нет: вывод c07 «результата не дал» корректен, но отсутствие этим не доказано |
| 19 | 01, 03 | «primary archetypal identity, secondary identity, and so on» | поиск Open Library | подтверждено | Фрагмент: «its primary ar- chetypal identity, secondary identity, and so on. Scoring of Archetypes…» |
| 20 | 01, 03 | «some 48 descriptive attributes included in BAV» | поиск Open Library | подтверждено | «Weights are assigned to some 48 descriptive attributes included in BAV: obliging, rugged, carefree…» |
| 21 | 01, 03 | RADNB: «over 2,000 brands», «the lens of 60 archetypes», «primary and supporting archetypes», «Developed with Imperial College London», эпизод № 357 | WebFetch businessofstory.com | подтверждено | Даты эпизода на странице нет, это указано в файле |
| 22 | 01, 03 | Профиль Gillingwater на CIM (копия Wayback 14.05.2025): «60 archetypal feeling tones» и др. | Wayback; живая страница CIM | не проверено | Wayback недоступен весь сеанс; живая страница — 404 (см. 2.4) |
| 23 | 03 | «66 per cent» в описании подкаста с Хартвелл (копия Wayback 11.06.2026) | Wayback; живая страница | не проверено | Wayback недоступен; живая страница — 403 (см. 2.4) |
| 24 | 03 | «influencer archetype» и 70/30 в гиде Iconic Fox (копия Wayback 07.06.2018) | Wayback | не проверено | Wayback недоступен (см. 2.4) |
| 25 | 01 | Shelburne (1988): «the unconscious images of the instincts themselves» со ссылкой «Vol. 9-A, p. 44» | поиск Open Library | подтверждено | |
| 26 | 01 | Юнг и Кереньи (1951): разделы «The Abandonment of the Child», «The Invincibility of the Child» | поиск Open Library | подтверждено | Фрагмент оглавления: «1. The Abandonment of the Child 2. The Invincibility of the Child 3…» |
| 27 | 01 | «Forms of Rebirth» с §199 | поиск Open Library (*Jung on Death and Immortality*) | подтверждено | «1. FORMS OF REBIRTH 199 The concept of rebirth is not…» |
| 28 | 01 | Триада «maiden, mother, and Hecate» (Princeton 1969); тексты §3 и §90 во вторичных книгах | поиск Open Library | подтверждено | «the Kore in its three- fold aspect as maiden, mother, and Hecate» (1963 и 1969); Thurston: «identical in all men and thus constitutes a common psychic substrate»; Spencer: «the archetypes, which can only become conscious secondarily». «Wicked aspect» в «Four Archetypes» среди первых 50 совпадений нет — ⚠ оставлен верно |
| 29 | 01 | B&N (копия 31.03.2023): 80 карт, шесть пустых; АСТ (копия 24.10.2025): 74 карты-архетипа | Копии Wayback недоступны (сбой соединения); проверены **живые** страницы через WebFetch | подтверждено по живым страницам | B&N (www.barnesandnoble.com/w/…/1005803894): «a unique set of 80 Archetype Cards», «six blank cards». АСТ: «80 карт (74 карты-архетипа + 6 пустых)», переводчик Г. А. Коблякова, ISBN 978-5-17-165096-4, 96 с. Живая страница АСТ, отвечавшая 500 при c07, открылась; в 01 [153], [171] и 6.1 это отмечено. Сами копии Wayback v14 не открыл |
| 30 | 03 | Heaven's Door: «Archetypes in play: The Storyteller, The Creator, and The Wizard»; The Wizard «shares characteristics with The Alchemist/Magician, The Warrior and The Provocateur»; 05.11.2018 | WebFetch блога Хартвелл | подтверждено | Повод — комментарий для Packaging Strategies, как и указано |
| 31 | 03 | Том Хэнкс у Putnam в двух списках | WebFetch kayeputnam.com (Innocent, Girl/Guy Next Door) | подтверждено | «Real-life Innocents: Tom Hanks, Taylor Swift, Reese Witherspoon, Martha Stewart»; «Real-life Girl/Guy Next Doors: Tom Hanks, Drew Barrymore…» |
| 32 | 03 | Яценко, vc.ru, 28.07.2025: «„Заботливый“ в основе + „Мудрец“ в кейсах и разборах» | curl статьи | подтверждено | В 03 цитата дословная. В протоколе c07 (не в 03) парафраз «один основной архетип и один акцентный» подан как цитата; в статье — «выбрать один архетип как основной, второй как акцентный» |
| 33 | 03 | Интервью Пирсон 2024: Lover и Seeker, Caregiver и Warrior, Ruler и «gesture», Мудрец и Маг — «two forms of wisdom» | WebFetch Psychology Today | подтверждено | «gesture» в расшифровке подтверждено |
| 34 | 03 | Матриц 12×12 нет в открытых описаниях курсов (Адт, АрхетипиУМ, Stilouette, Бетева, Щеняева, Ю. Лос, Brand Master Academy) | curl семи страниц, подсчёт слов «совместим», «матриц», «сочетани» | подтверждено | У Адт: «ПРАКТИКА синтезА архетипов… разработки концепций бренда/персонажа на основе синтеза нескольких архетипов», «Иерархия архетипов в бренде» |
| 35 | 03 | Пример с CEO: «…appeals to his own fun-loving Jester»; вариант r08 «подарок из Любовника» не виден (⚠) | поиск Open Library | исправлено | В OCR: «…his own fun-loving Jester or his desire to nurture a child (Caregiver)». Вторая мотивация — Заботливый, вариант r08 неверен |
| 36 | 03 | «easy to recognize» («слово „simple“ во фрагменте не видно», c07) | поиск Open Library | исправлено | Фраза есть целиком: «it needs to be simple and easy to recognize». Исправлено в 1.1, 4.1 и шапке |
| 37 | 03 | «living icon» не найдено (⚠, c07) | поиск Open Library | исправлено (⚠ снят) | «…best accomplished when the owner is a living icon him- or herself». Снято в 1.1, 5.x, 6.1 и открытых вопросах; страница осталась под ⚠ |
| 38 | 03 | «a patchwork quilt of archetypal identities all at once» | поиск Open Library | подтверждено | |
| 39 | 03 | «conceptual unity across offerings» | поиск Open Library | подтверждено | |
| 40 | 03 | «at least some access to all archetypes» | поиск Open Library | подтверждено | |
| 41 | 03 | «some other secondary or perhaps altogether new category archetype» | поиск Open Library | подтверждено | |
| 42 | 03 | «good-naturedly poking fun at sometimes sanctimonious Innocent Coke» | поиск Open Library | подтверждено | |
| 43 | 03 | «gratified (though not surprised)», «being believers» не найдены (⚠ оставлен) | поиск Open Library | подтверждено (⚠ оставлен верно) | По фразе «were gratified (though not surprised)» 7 совпадений, книги Марк и Пирсон среди них нет |
| 44 | 03 | «Five Pocket», «Wide Leg» не найдены (⚠ оставлен) | поиск Open Library | ⚠ оставлен верно | 1131 совпадение по «Five Pocket»; поиск возвращает только первые 50, книга в них не попала. Отсутствие фразы этим не доказано |
| 45 | 03 | «Life requires constant negotiation along these poles»; «its brand identity must remain clear»; «…serves as a beacon» | поиск Open Library | подтверждено | «Life requires constant negotiation along these poles»; «its brand identity must remain clear—not only to keep faith with customers»; «The archetype within the brand serves as a beacon for the corresponding motivation» |

### 2.2. Раздел 6.6 в `03-blends.md`: разборы десяти персон (п. 2 задания)

| № | Персона | Что проверено | Чем | Вердикт | Комментарий |
|---|---|---|---|---|---|
| 46 | Tim Ferriss | «focused on deconstructing world-class performers»; первый подкаст с 100 млн загрузок, затем более миллиарда; «the world's best guinea pig» (Newsweek), «считает комплиментом»; «50+ others» в портфеле; статья NYT 2019 о финансировании психоделической медицины; серия «4-Hour», «Tools of Titans», «Tribe of Mentors» | WebFetch tim.blog/about | подтверждено | Порядок «Мудрец — Искатель» расходится с карточкой Искателя («Искатель + Мудрец»); в 03 это оговорено |
| 47 | Brené Brown | **Основной из источника:** «Real-life Sages: Brene Brown, Simon Sinek, Albert Einstein, Marie Curie» у Putnam. Endowed Chair Хьюстонского университета; McCombs; темы — мужество, уязвимость, стыд, эмпатия, лидерство; годы книг; Netflix 2019; «Atlas of the Heart» 2021; подкасты 2020 года | WebFetch kayeputnam.com/…/sage; сырой текст en.wikipedia | подтверждено | brenebrown.com на автоматические запросы отвечает 403, это указано в [105] |
| 48 | Mark Manson | «Positive thinking is overrated»; «I write self-help for people who hate self-help»; «three-time #1 New York Times bestselling author»; «Your Next Breakthrough»; «This shit is not a weekend retreat» | WebFetch markmanson.net/about | подтверждено | На странице «the three-time…» со строчной; несущественно |
| 49 | Marie Kondo | «spark joy»; уборка по категориям в порядке одежда → книги → бумаги → мелочи → памятные вещи; магазин KonMari (2019); Konmari-Media, LLC; Washington Post 2023; «Joy at Work» (2020) | сырой текст en.wikipedia; curl konmari.com | подтверждено, кроме цитаты | **Исправлено:** цитаты «assign a place for everything» нет ни в статье, ни на konmari.com. В Википедии — «choosing a place for everything from then on» |
| 50 | Bear Grylls | 21 SAS 1994–1997; Эверест 16.05.1998, через 18 месяцев после травмы; парашютный случай в Замбии 1996 года прервал службу; Chief Scout 07.2009–09.2024, самый молодой; посол King's Trust и Care for Children; RNLI, SSAFA; «Man vs. Wild» 2006–2011, «Running Wild» 2014–2023; книги 2011 и 2021 годов | сырой текст en.wikipedia | подтверждено | |
| 51 | Дмитрий Куплинов | **Основной из источника:** Дяченко, Sostav, 25.12.2023 — «Очень часто в архетипе Славного Малого выступают представители блогосферы… (например, ютубер летсплейщик Дмитрий Куплинов)». Жанры канала; исследование 2022 года («Ойкумена», «приятную атмосферу для взаимодействия»); благотворительность 2017 и 2020 годов; описание канала | WebFetch Sostav; сырой текст ru.wikipedia; og:description YouTube | подтверждено; одна атрибуция уточнена | «Мотивацию и поддержку» — это заголовок статьи Medialeaks (2021), на которую ссылается Википедия, а не текст статьи Википедии; уточнено. Адрес [108] — перенаправление на «Куплинов, Дмитрий Алексеевич», работает |
| 52 | Юлия Высоцкая | «Едим дома!» на НТВ с 2003 года; «Ёрник» и студия (2011); турфирма с маршрутами по ресторанам Западной Европы; Food Embassy (2014); «ХлебСоль» (2009–2017); тираж более 2 млн; актриса | сырой текст ru.wikipedia | подтверждено, кроме числа книг | **Исправлено:** «около 38 книг» — это число позиций в библиографии статьи. В статье: «По состоянию на 6 июля 2024 года издано 75 книг, включая переиздания» |
| 53 | Татьяна Черниговская | Директор Института когнитивных исследований СПбГУ (с 2020), академик РАО (2023), и. о. заведующей кафедрой; «Прямая речь»; циклы на «Культуре»; Царскосельская премия 2022; книги о коте Шрёдингера; Telegram — 111K подписчиков, пост «Сегодня международный день мозга! Интересно, мозг об этом знает?)», «Агора», «Пусть не говорят, пусть читают» | сырой текст ru.wikipedia; curl t.me/s/tvchernigovskya | подтверждено | |
| 54 | Фёдор Овчинников | **Основной из источника:** Сбер Бизнес Live, 24.06.2024, Е. Карпова — «Яркий представитель архетипа — Федор Овчинников» (Славный малый). Блог с 2006 года; meta сайта «Избранные заметки блога «Сила ума» и публикации в соцсетях за 2006–2023»; тундра Ямала (2025), фильм в 2026 году; YallaMarket (04.2022); «Додо ИС» (2018); «Дринкит» (2020) | WebFetch sberbusiness.live; curl sila-uma.ru; сырой текст ru.wikipedia | подтверждено; одна атрибуция уточнена | Интервью «Бизнес должен быть открытым — как пицца» — это пресс-центр Microsoft, 18.11.2020 (ссылка в Википедии), а не сайт «Сила ума»; уточнено |
| 55 | Андрей Курпатов | Более 30 книг, тираж более 5 млн; «Красная таблетка» в рейтинге РКС (2020 — 4-е место, 2021 — 15-е); лаборатория Сбербанка (02.2019); «Нет проблем» (2005), «Доктор Курпатов» (2006 — весна 2007); «Красный квадрат» (2007); «Высшая школа методологии» (2014); посты канала проектов (последний — 07.07.2022, 1,68K подписчиков); YouTube-канал | сырой текст ru.wikipedia; curl t.me/s/kurpatov_official; og:title YouTube | подтверждено | Добавлена справка о критике (антипремия «Почётный академик ВРАЛ», 2021) как о доводе против роли Мудреца. Добавлена сноска о расхождении с карточкой Мудреца («Мудрец + Правитель») |
| 56 | Все десять | Пометки «оценка исследования, не из источника» | чтение 6.6 | подтверждено | Шапка раздела, итоговый абзац и ссылки на r07 и карточки оформлены как оценка. «Из источника» стоит только у основного архетипа Brown, Куплинова и Овчинникова, и это подтверждено (№ 47, 51, 54) |
| 57 | Все десять | Итоговый подсчёт «7 из 10 — разные группы, 3 — одна» | пересчёт по группам Марк и Пирсон | подтверждено | Одна группа: Ferriss (Мудрец + Искатель), Куплинов (Славный малый + Шут), Высоцкая (Заботливый + Творец) |
| 58 | Русскоязычные пять | Правовые статусы | grep сырого текста статей ru.wikipedia по словам «иноагент», «иностранн», «санкц», «Миротвор», «уголовн», «розыск» | уточнено | У Куплинова, Высоцкой и Черниговской таких сведений нет. У Овчинникова: дело 2018 года о наркотиках в пиццерии сети, он — свидетель. У Курпатова: уголовное дело 2021–2024 годов возбуждено по его заявлению против другого лица. Формулировка критерия отбора в шапке 6.6 («уголовные дела») с этим расходилась; уточнено до «уголовное преследование самой персоны», к обоим разборам добавлены нейтральные справки. Сведения о частной жизни из статьи о Курпатове не переносились. Сверка с официальными реестрами не проводилась: в 03 стоит пометка о юридической проверке |
| 59 | Все десять | Ссылки на каналы и сайты | curl и og-теги YouTube; t.me | подтверждено | @TimFerriss, @IAmMarkManson, @BearGrylls, @KuplinovPlay и UCX_isCsPV3HOg95qodqIdLQ открываются на нужных каналах. t.me/tvchernigovskya и t.me/kurpatov_official открываются. brenebrown.com — 403 (оговорено) |

### 2.3. Снятые и суженные пометки ⚠ (выборка, п. 4 задания)

| № | Файл, раздел | Пометка c07 | Проверка v14 | Вердикт |
|---|---|---|---|---|
| 1 | 01, 2.2 | Дитя: «покинутость и непобедимость» — снято | № 26 | снято верно |
| 2 | 01, 2.2 | Перерождение: раздел «Forms of Rebirth» — сужено | № 27 | верно |
| 3 | 01, 2.1 | §91 — сужено до номера § | № 25 | верно |
| 4 | 01, 3.3 | Части и оси «Питера» — сняты | № 1, 2 | верно (вторично; ⚠ на порядке слов оставлен честно) |
| 5 | 01, 3.6 | Столбец «Питер» — снято | № 1–4 | верно; регистр «Славный малый» уточнён |
| 6 | 01, 7.2 | «Заботливый» («Питер») — снято | № 1, 2 | верно |
| 7 | 01, 7.3 | Переводчики «Питера» — снято | № 3 | верно |
| 8 | 01, 7.3 | Оглавление «Бомборы» 2023 — снято | № 5 | верно |
| 9 | 01, 9.2 | Заголовок столбца «Питер» — сужено | № 1, 2 | верно |
| 10 | 01, 10.1 п. 3 | Названия «Питера» — сужено | № 1, 2 | верно |
| 11 | 01, 6.1 | Зодиак и названия домов Мисс — снято | № 9 | верно |
| 12 | 01, 6.1 | Процедура выбора восьми — новое ⚠ «не проверялась» | № 10 | устарело → сужено до «по тексту книги» |
| 13 | 01, 6.2 | Структура Хартвелл по книге — сужено | № 6, 8 | верно |
| 14 | 01, 6.2, 8, 9.1 | Соответствие Хартвелл с Марк–Пирсон: (О) → (А) | № 6, 7 | верно |
| 15 | 01, 4.2 | Номера глав 15–17 — снято | № 17 | верно |
| 16 | 01, 4.3 | PMAI 2002/2003 — сужено | № 12, 14 | верно; гипотеза о дате авторского права заменена |
| 17 | 01, 3.4 | «primary archetypal identity…» — снято | № 19 | верно |
| 18 | 03, шапка | «primary… secondary identity» — снято | № 19 | верно |
| 19 | 03, 1.1 | «access to all archetypes», CEO — снято; новое ⚠ «подарок из Любовника» | № 35, 40 | снято верно; новое ⚠ заменено исправлением |
| 20 | 03, 1.1 | «simple and easy to recognize» — сужено до «easy to recognize» | № 36 | c07 ошибся; исправлено |
| 21 | 03, 1.1 | Продолжение дрейфа Levi's — сужено, ⚠ на Regular Guy/Gal | № 60 (раздел 4) | ⚠ снят: Regular Guy or Gal подтверждён цитатой в [117] |
| 22 | 03, 1.1 | «living icon» — ⚠ оставлен | № 37 | ⚠ снят v14 |
| 23 | 03, 1.1 | «conceptual unity» — сужено | № 39 | верно |
| 24 | 03, 1.1 | Леттерман — «оставлено (имя в OCR не найдено)» | раздел 4, п. е | устарело: имя найдено c04, перепроверено v14; ⚠ снят |
| 25 | 03, 1.1 | Dove как «secondary» — сужено, ⚠ «Dove не виден» | раздел 4, п. е | устарело: «Dove is more of a Caregiver brand» в OCR; ⚠ снят |
| 26 | 03, 2 | RADNB «primary and supporting» (2 строки) — снято | № 21 | верно |
| 27 | 03, 2 | Хартвелл: «The four primary archetypes» — ⚠ оставлен | — | оставлен верно (расшифровки нет) |
| 28 | 03, 5.5 | Совет психологам (vc.ru) — снято | № 32 | верно |
| 29 | 03, [83] | vc.ru «только фрагмент выдачи» — снято | № 32 | верно |
| 30 | 03, 5.7 | Матрицы в курсах — сужено | № 34 | верно |
| 31 | 03, 6.1 | Pepsi / Joe Camel — сужено, ⚠ на Joe Camel | раздел 4, п. е | устарело: «Joe Camel was the Jester to Marlboro's serious Hero», рядом «275»; ⚠ снят |
| 32 | 03, 3.2 | 48 против 55 атрибутов — снято | № 20; Researchscape [38] в 03 | снято допустимо: объяснение помечено как оценка |
| 33 | 03, 3.4 | «gratified (though not surprised)» — оставлено | № 43 | оставлено верно |
| 34 | 03, 1.2 | «gesture» вместо «jester» — оставлено | № 33 | оставлено верно |
| 35 | 03, 2 | «influencer» в 2018 году — снято | № 24 | не проверено v14 (Wayback недоступен) |
| 36 | 03, 3.4 | «66 per cent» — снято | № 23 | не проверено v14 (Wayback недоступен) |
| 37 | 03, [33] | Профиль CIM — снято | № 22 | не проверено v14 (Wayback недоступен) |
| 38 | 01, [75], [153] | B&N и АСТ — сняты по копиям | № 29 | снято верно (по живым страницам) |
| 39 | 01, 6.6 | «Masochist» — снято | № 11 | снято верно |
| 40 | 01, 4.1 | Martyr → Altruist — исправлено | № 16 | исправлено верно; добавлено уточнение о таблице |
| 41 | 01, 3.2 | Название Part I — снято | № 18 | снято верно |
| 42 | 01, 9.3 | Кора: триада — снято | № 28 | снято верно |

### 2.4. Результаты повторных запросов к Open Library и Wayback

Запросы, которые не прошли в 13:15–14:10 из-за сбоев соединения, повторялись двумя фоновыми пакетами (27 запросов к Open Library). Результаты внесены в таблицы 2.1 и 2.3.

- **Open Library — всё получено.** Подтверждены: Altruist и ряд таблицы 6 ↔ 12 (1998); «The Masochist» (1992); Part I, Part VI, гл. 20–21 у Марк и Пирсон; Part V у Пирсон 1991; «48 descriptive attributes»; «constant negotiation along these poles»; «brand identity must remain clear»; «serves as a beacon»; триада Коры; тексты §3 и §90; второй раздел эссе о Дитя. Записи каталога PMAI (OL11503426M, OL20009488M) получены в JSON.
- **По слишком частым словам поиск не решает.** «Maslow», «hierarchy of needs», «wicked aspect», «Five Pocket», «The Real McCoy» и «Leaving a Legacy» дают десятки тысяч совпадений, а поиск возвращает только первые 50. Названия гл. 20 и 21 подтверждены более узкими запросами. Для остальных отсутствие фразы не доказано, и пометки ⚠ в файлах оставлены верно.
- **Wayback Machine — не получено.** Копии [99], [102], [116] в 03 и [174] в 01 v14 не открыл: соединение с web.archive.org сбрасывалось весь сеанс, фоновый скрипт повторял попытки больше часа. Живые страницы не помогают: CIM — 404, Convince & Convert — 403, у текущей версии гида Iconic Fox WebFetch получил пустую страницу. Поэтому №№ 22–24 («60 archetypal feeling tones», «66 per cent», «influencer» в 2018 году) остаются **не проверенными v14**. Пометки c07 в файлах не возвращались: утверждения опираются на конкретные копии с датой, и признаков ошибки нет. Копии [171] и [172] в 01 тоже не открыты, но их содержание подтверждено живыми страницами (№ 29).

## 3. Проверенные URL (п. 5 задания)

Из 57 адресов, добавленных в c07, здесь проверены все 50, кроме копий Wayback и записей Open Library (о них — примечание под таблицей). Кроме того, проверены 3 адреса, добавленные v14, и 10 опорных адресов. Коды — ответ curl с `-L` 2026-10-16. Код 429 — ограничение частоты; эти страницы до этого открылись через WebFetch или curl.

| № | URL | Код | Что подтверждено |
|---|---|---|---|
| 1 | https://myss.com/free-resources/sacred-contracts-and-your-archetypes/the-archetypal-wheel/ | 200 | 12 домов, зодиак, Chart of Origin |
| 2 | https://myss.com/free-resources/sacred-contracts-and-your-archetypes/casting-your-chart-of-origin/ | 200 | процедура расстановки (новый [175] в 01) |
| 3 | https://myss.com/free-resources/sacred-contracts-and-your-archetypes/determining-your-archetypes/ | 200 | отбор восьми (новый [175] в 01) |
| 4 | https://www.archetypesinbranding.com/post/pulling-back-the-curtain | 200 → 429 при повторе | пост 2016 года, все цитаты |
| 5 | https://www.archetypesinbranding.com/post/bob-dylan-writing-welding-and-whiskey | 200 (WebFetch) → 429 | Heaven's Door, 05.11.2018 |
| 6 | https://businessofstory.com/podcast/brand-archetype-tells-brand-story/ | 200 | RADNB, № 357 |
| 7 | https://static10.labirint.ru/books/950126/demo.pdf | 200 | оглавление 2023 года |
| 8 | https://www.labirint.ru/books/950126/ | 200 | ISBN 978-5-04-172815-1, 2023, 432 с. |
| 9 | https://cdn.eksmo.ru/v2/ITD000000001500651/PDF/ITD000000001500651_TOC.pdf | 200 | порядок предисловий в переиздании |
| 10 | https://confhub.ru/archive/Lomonosov_2025/data/36727/183406_uid271377_report.pdf | 200 | 12 названий, 4 группы |
| 11 | https://cyberleninka.ru/article/n/nekommercheskiy-brending-opyt-ispolzovaniya-arhetipov | 200 (капча; текст — через API) | таблица осей |
| 12 | https://cyberleninka.ru/article/n/arhetipy-v-reklame-kak-formula-uspeha | 200 (через API) | Малкова, Раевская, Сухенко, 335 с.; соавтор Ковалева |
| 13 | https://cyberleninka.ru/article/n/psihologiya-reklamy-arhetipy | 200 (через API) | статья существует (2018) |
| 14 | https://cyberleninka.ru/article/n/marshrutnaya-karta-put-geroya-kak-instrument-psihologo-pedagogicheskogo-soprovozhdeniya-razvitiya-kompetentnosti-buduschego | 200 (через API) | статья существует (2020) |
| 15 | https://cyberleninka.ru/article/n/evolyutsiya-arhetipov-v-reklamnoy-kampanii-sotovyh-operatorov | 200 (через API) | статья существует (2018) |
| 16 | https://www.psy.su/mod_files/additions_1/fle_file_additions_1_3656.doc | 200 | 82 944 байт, Last-Modified 15.01.2015 |
| 17 | https://archive.org/details/mythoslogosintho0000shel | metadata | restricted; фраза и «Vol. 9-A, p. 44» |
| 18 | https://archive.org/details/introductiontosc0000jung | metadata | restricted; разделы о Дитя |
| 19 | https://archive.org/details/essaysonscienceo00jung | metadata | restricted (printdisabled) |
| 20 | https://archive.org/details/fourarchetypesmo00jung | metadata | restricted (printdisabled) |
| 21 | https://archive.org/details/jungondeathimmor00carl | metadata | restricted (printdisabled); «Forms of Rebirth» §199 |
| 22 | https://archive.org/details/innerpowerofsile0000thur | metadata | restricted |
| 23 | https://archive.org/details/mothersarepeople0000spen | metadata | restricted |
| 24 | https://archive.org/details/warriorwithinacc00moor | metadata | restricted; Morrow, 1992 |
| 25 | https://archive.org/details/herowithinsixarc0000pear | metadata | restricted (printdisabled); 1998 |
| 26 | https://archive.org/details/isbn_9780739173268 | metadata | restricted; Lexington, 2012 (новый [117] в 03) |
| 27 | https://tim.blog/about/ | 200 | факты Ferriss |
| 28 | https://tim.blog/podcast/ | 200 | подкаст |
| 29 | https://www.youtube.com/@TimFerriss | 200 | og:title «Tim Ferriss» |
| 30 | https://en.wikipedia.org/wiki/Bren%C3%A9_Brown | 200 | должность, книги, Netflix |
| 31 | https://brenebrown.com/ | 403 | автоматические запросы блокируются (оговорено в [105]) |
| 32 | https://markmanson.net/about | 200 | пять цитат |
| 33 | https://markmanson.net/ | 200 | — |
| 34 | https://www.youtube.com/@IAmMarkManson | 200 | og:title «Mark Manson» |
| 35 | https://en.wikipedia.org/wiki/Marie_Kondo | 200 | факты; цитата исправлена |
| 36 | https://konmari.com/ | 200 | «spark joy»; «assign a place» нет |
| 37 | https://en.wikipedia.org/wiki/Bear_Grylls | 200 | факты |
| 38 | https://www.youtube.com/@BearGrylls | 200 | og:title «Bear Grylls» |
| 39 | https://www.beargrylls.com/ | 200 | — |
| 40 | https://ru.wikipedia.org/wiki/Дмитрий_Куплинов | 200 (перенаправление) | факты |
| 41 | https://www.youtube.com/@KuplinovPlay | 200 | описание канала |
| 42 | https://www.sostav.ru/blogs/261743/42960 | 200 | Куплинов у Дяченко |
| 43 | https://ru.wikipedia.org/wiki/Высоцкая,_Юлия_Александровна | 200 → 429 при повторе | факты; число книг исправлено |
| 44 | https://www.edimdoma.ru/ | 200 | числа книг на странице нет |
| 45 | https://ru.wikipedia.org/wiki/Черниговская,_Татьяна_Владимировна | 200 | факты |
| 46 | https://t.me/s/tvchernigovskya | 200 | 111K, посты |
| 47 | https://t.me/tvchernigovskya | 200 | — |
| 48 | https://ru.wikipedia.org/wiki/Овчинников,_Фёдор_Владимирович | 200 | факты; ссылка на интервью Microsoft |
| 49 | https://sila-uma.ru/ | 200 | блог с 2006 года; meta «…за 2006–2023» |
| 50 | https://ru.wikipedia.org/wiki/Курпатов,_Андрей_Владимирович | 200 | факты; критика |
| 51 | https://t.me/s/kurpatov_official | 200 | посты, последний — 07.07.2022 |
| 52 | https://t.me/kurpatov_official | 200 | — |
| 53 | https://www.youtube.com/channel/UCX_isCsPV3HOg95qodqIdLQ | 200 | og:title «Андрей Курпатов» |
| 54 | https://brandmasteracademy.com/ | 200 | слова «archetype» на главной нет |
| 55 | https://cityclass.ru/los_personal_branding_on_archetypes/ | 200 | слов о совместимости нет |
| 56 | https://arhetipium.ru/kurs-arhetipy | 200 | слов о совместимости нет |
| 57 | https://kayeputnam.com/brand-archetypes/sage/ | 200 | Brené Brown среди «Real-life Sages» |
| 58 | https://kayeputnam.com/brand-archetypes/innocent/ ; …/girl-guy-next-door/ | 200 (WebFetch) | Том Хэнкс в двух списках |
| 59 | https://sberbusiness.live/publications/archetype | 200 | Овчинников — Славный малый |
| 60 | https://vc.ru/marketing/2124860-arkhetipy-brenda-dlya-psikhologov | 200 | Яценко, 28.07.2025 |
| 61 | https://jovianarchive.com/pages/understanding-profile-in-human-design | 200 | «six fundamental Personality Archetypes» |
| 62 | https://www.psychologytoday.com/us/blog/the-seekers-forum/202408/which-archetypes-are-you-living | 200 | пары и «two forms of wisdom» |
| 63 | https://alinaadt.ru/masterarchetype | 200 | «синтез архетипов», «Иерархия архетипов» |

**Примечание.** Записи Open Library ([165] в 01) проверены через JSON (№ 13 в 2.1). Копии Wayback ([171], [172], [174] в 01; [99], [102], [116] в 03) не открылись; о них — раздел 2.4.

## 4. Межфайловая сверка (п. 3 задания)

| Пункт | Что искалось | Результат в 01 | Результат в 03 | Что сделано |
|---|---|---|---|---|
| а) Голден | Формулировки списка К. Голдена (jaced.com, 2014), приписанные Марк и Пирсон: поля Weakness / Talent, «boring for all their naive innocence», «becoming a misfit», «study details forever», «being a chicken», «another battle to fight», «competence and courage», «becoming manipulative», «win-win», «to get to paradise», «using intelligence and analysis», «true to one's soul», «wisdom, intelligence», длинные строки «also known as»; девизы Голдена («I make things happen», «You're the only one», «You only live once», «If you can imagine it, it can be done») | Нет. Девизы в 3.2 — по OCR книги. «Also known as» — только OCR врезки Explorer и синонимы Putnam. Слово «Weakness» есть только в таблице Пирсон 1986 (страх Warrior) | Нет | Исправлений не требуется |
| б) Levi's | Дрейф у Марк и Пирсон начинается с Explorer, с. 9 (c04; `02-cards/02-explorer.md`, `07-regular-guy.md`) | Levi's не упоминается | Устарело: «[1, гл. 5]» для фразы о дрейфе и «гл. 1, с. 10 ⚠ стр.» для продолжения; Regular Guy/Gal под ⚠ | Исправлено в 1.1 и 6.1: с. 9–10. Ряд «…back to Explorer, then to Regular Guy or Gal, then to Jester» подтверждён цитатой «(Mark and Pearson 2001, 9)» в книге Lexington 2012 (поиск Open Library) — новый [117]. «Seemed a bit lost» оставлено с «гл. 5 — по r08» как отдельное место |
| в) Девиз Бунтаря | «Rules are meant to be broken» | Верно в 3.2; вариант «made» описан как ошибка r02 | Девиза нет | Исправлений не требуется |
| г) Российские знаки и суды (04) | Утверждения «не проверено» о российских знаках | Таких утверждений нет. «Бренд-Личность™» и «Архетон™» Адт в 7.1 — знак ™ из самоописания автора; в 04 сведений о регистрации нет | Таких утверждений нет | В 01, раздел 6.11, добавлена отсылка к `04-diagnostics.md`, разделы 8.2 и 8.4–8.6 («Дизайн человека», «Метод Ладини Матрица судьбы», № А40-170352/2019) |
| д) Jovian (06) | Линии профиля как «архетипы» | В 6.11 Human Design упомянут без этого факта | Нет упоминаний | Добавлено в 01, раздел 6.11: «six fundamental Personality Archetypes» (проверено на jovianarchive.com) |
| е) Другие устаревшие факты, найденные при сверке | Леттерман, Dove, Joe Camel / Pepsi, страницы 274–275 (c04, v03; `02-cards/07`, `09`, `10`) | — | Устарело: «имя Леттермана в OCR не видно ⚠», «Dove не виден ⚠», «Joe Camel не подтверждён ⚠», «с. 274 ⚠», «с. 275 ⚠ стр.» | Исправлено в 1.1, 4.x, 6.1, 6.4 и открытых вопросах. Фразы перепроверены поиском Open Library: «The "lesser Jester," David Letterman», «Dove is more of a Caregiver brand», «Joe Camel was the Jester to Marlboro's serious Hero» (рядом «275») |
| ж) PMAI в Copyright Office (04) | Даты публикации | Гипотеза c07 «2002 — дата авторского права» | — | Уточнено в 4.3: руководство опубликовано 15.10.2003 (TX0006085421) |
| з) Мисс (06, раздел 2.9) | Процедуры колеса и отбора восьми | «не проверялась» | — | Обновлено в 6.1 и 10.2 п. 10, добавлен [175] |
| и) «Матрица судьбы» (06, раздел 2.4) | Дата метода | «2006 (⚠)» в таблице 8 | — | Уточнено: 2006 год по matrica-sudby.ru и книге Н. Ладини 2025 года |
| к) Пары PMAI (c03) | c03 считает примечание к табл. 3.1 прямым подтверждением всех шести пар | — | В 1.2 и 5.2 пары выведены из порядка таблицы, который руководство само называет порядком пар; ⚠ «прямого перечня нет» | Согласуется по сути; оставлено |
| л) Персоны 6.6 и карточки | Атрибуции тех же персон в `02-cards/` | — | Ferriss оговорён; Курпатов в карточке Мудреца — «Мудрец + Правитель» | Добавлена оговорка к Курпатову. Grylls, Manson, Куплинов, Черниговская, Овчинников с карточками согласуются; Высоцкая оговорена через r07 |

## 5. Правила (п. 6 задания)

| Правило | Проверка | Итог |
|---|---|---|
| Цитаты до 25 слов | Скрипт по добавленным строкам обоих файлов (цитаты в «»), порог 18 слов | Одна цитата — 22 слова (пример с CEO, расширен v14); остальные короче. Нарушений нет |
| Нет ссылок на неавторизованные копии | Grep по пиратским доменам; статус 25 экземпляров IA через metadata | Нарушений нет; все экземпляры IA с ограниченным доступом |
| Сплошная нумерация [n] | `refcheck.py` | 01: 1–175, без пропусков, дублей, висячих и неиспользованных. 03: 1–117, то же. Совпадения «124, 127, 274» — это ссылки на номера в `01-systems.md` и номера страниц, а не висячие ссылки |
| Таблицы корректны | `tblcheck.py`: число ячеек в каждой строке равно числу ячеек заголовка | 01: 16 таблиц, 03: 13 таблиц, ошибок нет |
| Нет рекомендаций по проектированию продукта | Grep добавленных строк по словам «рекоменд», «приложени», «анкет», «калькулятор», «MVP», «UX» и др. | Совпадения только в описании источников («в приложении к книге», «не рекомендуют» у Марк и Пирсон). Нарушений нет |

## 6. Сводка

- **Проверено:**
  - 59 утверждений (45 из источников и 14 по разделу 6.6);
  - 42 снятые или суженные пометки ⚠;
  - 63 URL в таблице раздела 3: все 50 адресов c07, кроме Wayback и Open Library, плюс 13 опорных и новых; ещё 2 записи Open Library ([165]) проверены через JSON; 5 копий Wayback не открылись, содержание двух из них подтверждено живыми страницами;
  - 25 экземпляров Internet Archive по metadata;
  - 11 пунктов межфайловой сверки;
  - 5 правил оформления.
- **Вердикты по 59 утверждениям:**
  - подтверждено — 45;
  - исправлено — 5 (пример с CEO, «simple and easy to recognize», «living icon», цитата у Кондо, число книг Высоцкой);
  - уточнено — 5 («Славный малый», гипотеза о дате PMAI, две атрибуции в 6.6, правовой критерий 6.6);
  - устарело — 1 (процедуры Мисс);
  - не проверено — 3 (копии Wayback).
- **Пометки ⚠:**
  - выборка из 42: снято верно или оставлено верно — 31; оставлено c07, но снято v14 — 5 (Levi's / Regular Guy, «living icon», Леттерман, Dove, Joe Camel); c07 ошибся в сужении — 2 («simple…», «подарок из Любовника»); устарело — 1 (процедура Мисс); не проверено — 3;
  - в `01-systems.md` — 178 → 177; в `03-blends.md` — 64 → 52.
- **Главные исправления:**
  1. **03, Levi's:** дрейф идёт с Explorer на с. 9–10, а не «гл. 5» и «с. 10»; Regular Guy or Gal подтверждён цитатой «Mark and Pearson 2001, 9» (новый [117]).
  2. **03, устаревшие ⚠:** Леттерман, Dove (с. 274–275), Joe Camel и Pepsi (с. 275) — их уже подтвердили c04 и v03 в карточках; сняты.
  3. **03, ошибки c07 и r08 в тексте Марк и Пирсон:** «simple and easy to recognize» есть целиком; «living icon» найден; вторая мотивация в примере с CEO — Caregiver, а не Любовник.
  4. **03, раздел 6.6:** цитата Кондо «assign a place for everything» не найдена → «choosing a place for everything» (Википедия); у Высоцкой «около 38 книг» → 75 книг с переизданиями; две атрибуции уточнены (Medialeaks, Microsoft). Добавлены нейтральные справки об уголовных делах, где Овчинников — свидетель, а Курпатов — заявитель, и о критике Курпатова; критерий отбора персон уточнён.
  5. **01, межфайловая сверка:** PMAI в Copyright Office (04) — гипотеза «2002 — дата авторского права» не подтверждается; процедуры Мисс (06, новый [175]); Jovian и линии профиля как «архетипы» (06); отсылка к российским знакам и делам (04); дата «Матрицы судьбы» (06).
  6. **01, мелкие правки:** «Славный малый» по [167, 168]; живые страницы АСТ и B&N; продолжение ряда 6 ↔ 12 (Altruist рядом с Destroyer); описание [27] и вводной к [158–161].
- **Что осталось:**
  - три утверждения по копиям Wayback ([99], [102], [116] в 03; [174] в 01): повторить, когда web.archive.org станет доступен;
  - страницы Марк и Пирсон (с. 1–2, 26–27, 30, 42, 162, 284–285, гл. 20): поиск Open Library страниц не даёт;
  - «gratified (though not surprised)», 501 / Five Pocket / Wide Leg, «wicked aspect», Маслоу — не найдены; при частых словах поиск не доказывает отсутствие;
  - «Питер» 2005 по самому изданию, полный список 60 Хартвелл и Чена, полный текст Merlo и др. (как в c07);
  - правовые статусы пяти русскоязычных персон — только по Википедии, без официальных реестров; перед использованием нужна юридическая проверка.
