# Протокол независимой проверки: 04-diagnostics.md и 06-esoteric-links.md

- **Дата проверки:** 2026-10-16 (записи реестров USPTO TSDR сформированы 2026-10-15 22:20–22:40 EDT, то есть 2026-10-16 по UTC).
- **Проверяющий:** независимый агент; в сборе материала и написании файлов не участвовал.
- **Объект:** `archetypes/research/04-diagnostics.md` («Как определяют архетип: методы, надёжность, критика, права») и `archetypes/research/06-esoteric-links.md` («Связи эзотерических систем с архетипами»).
- **Изменены только:** эти два файла и настоящий протокол. Заметки `_notes/r*.md`, папки `knowledge-base/` и `calculators/` не менялись (knowledge-base только читалась для сверки ссылок [47] и [48] файла 06). Git-коммитов не делалось.
- **Раздел о правах в 04 — не юридическая консультация;** эта пометка в файле на месте (шапка, раздел 8, таблица 8.7, вывод 8).

---

## 1. Методика

1. **Чтение.** Оба файла прочитаны целиком, включая списки источников (04 — 166 источников до проверки, 06 — 163).
2. **Сверка с первоисточниками.** Каждое утверждение из списка задания проверялось по самому надёжному доступному источнику:
   - руководство PMAI 2021 г. (PDF из файлового хранилища carolspearson.com; текст извлечён `pdftotext`);
   - полные тексты статей в открытом доступе (Faber & Mayer 2009 — авторская копия; Aaker 1997 — PDF Стэнфорда, страницы 349–352 просмотрены как изображения; Bechter 2016 — PDF MDPI; Xara-Brasil 2018 — PDF журнала; Paekivi & Karjus — arXiv HTML; Srivastava 2021 — ACL Anthology; Zeng & Fraikin 2025 — репозиторий Эссекса; Dean & Kelly 2003 — полный текст на astrology-and-science.com; Sotirova-Kohli 2013 — Europe PMC; Капустина 2016 — PDF журнала);
   - метаданные Crossref, аннотации Semantic Scholar и Europe PMC REST API;
   - реестры: USPTO TSDR (27 записей по серийным номерам и 39 по номерам регистрации, запросы по одному с паузой 3–4 с), WIPO Madrid Monitor (4 международные регистрации), TTABVUE (2 производства);
   - тексты решений судов США (law.resource.org), законов (law.cornell.edu, consultant.ru через WebFetch, wto.org, wipo.int);
   - сайты правообладателей и авторов (StoryWell, carolspearson.com, genekeys.com, jovianarchive.com, myss.com, matrica-sudby.ru, eksmo.ru и др.).
3. **Поиск.** WebSearch использовался точечно (5 запросов): для поиска аннотации McPeek, средней оценки Форера, цитаты Грир о 1977 г. и года метода Ладини. Лимит поиска не обходился, страницы выдачи поисковиков не открывались.
4. **Проверка URL.** Все URL из обоих списков источников (04 — 199 уникальных, 06 — 200) проверены автоматически (`curl`, затем повторно по одному с HTTP/1.1). Не открывшиеся через `curl` адреса по возможности открыты через WebFetch или через API/зеркало издателя. Для 49 URL файла 04 и 55 URL файла 06 проверено содержание: подтверждает ли страница утверждение файла (раздел 4).
5. **Правила.** Автоматически проверены: длина цитат (все цитаты в «» и "" длиной от 18 слов выписаны и пересчитаны), ссылки на возможные неавторизованные копии (archive.org, ebin.pub, libgen, scribd, psytests и др.), воспроизведение пунктов тестов, соответствие номеров [n] спискам источников (скрипт: нет ссылок на несуществующие номера, нет неиспользованных источников, нет дублей и пропусков), отсутствие рекомендаций по проектированию продукта.
6. **Пиратские копии не использовались.** Ссылка на копию оригинала Forer (1949) на университетском сервере курса и PDF-копия обзора Dickson & Kelly (1985) на стороннем сайте найдены в выдаче, но не открывались и не цитируются.
7. **Личные данные** в запросы не включались; даты рождения в калькуляторы не вводились. Имена физических лиц — владельцев знаков из TSDR в файлы и протокол не переносились.

---

## 2. Таблица проверки утверждений

Вердикты: **подтверждено** — источник открыт и подтверждает утверждение; **исправлено** — факт, цифра, формулировка или атрибуция изменены; **помечено ⚠** — пометка добавлена или сохранена, потому что подтвердить нельзя; **удалено** — элемент убран из файла.

| № | Файл | Утверждение | Чем проверено (URL) | Вердикт | Комментарий |
|---|---|---|---|---|---|
| 1 | 04 | PMAI: 72 пункта, по 6 на шкалу, 5-балльная шкала Ликерта Strongly Disagree – Strongly Agree | PDF руководства 2021: https://cdn.prod.website-files.com/5fc7fbb375805cc285353295/65d8ffa286160b97014347f7_PMAI_Manual_2021-1.pdf | подтверждено | Гл. 3: «72 items—six items», «5-point Likert scale» |
| 2 | 04 | Руководство 2021 г. лежит в хранилище официального сайта carolspearson.com | Страницы https://www.carolspearson.com/about/archetypal-assessments и …-pearson-marr-archetype-indicator-r содержат тот же идентификатор Webflow 5fc7fbb375805cc285353295 | подтверждено | На самих страницах ссылки на PDF нет; есть фраза «The 2020 PMAI Manual® is coming soon» |
| 3 | 04 | База норм «более 13 000 записей»; процентильный ранг относительно среднего и SD | То же руководство, гл. 2, с. 6 | подтверждено | — |
| 4 | 04 | Выборка 5 000; 18–93 года, медиана 29; мужчины 55% (2 733), женщины 46% (2 199); студенты гейм-дизайна в Орландо | Руководство, гл. 4, с. 13 | подтверждено | Сумма ≠ 100% — оговорка самих авторов |
| 5 | 04 | Альфы 0,583–0,816 (опечатка «.0583» у Revolutionary), split-half; Realist и Revolutionary < 0,70, Seeker на грани | Руководство, табл. 4.2, с. 14–15 | подтверждено | Таблица выписана построчно, все 12 альф и 12 split-half совпали |
| 6 | 04 | Тест-ретест не проводился (теоретическая и практическая причины) | Руководство, гл. 4, с. 13 | подтверждено | — |
| 7 | 04 | Раздел «Confirmatory Factor Analysis» описывает PCA с варимаксом, 12 факторов, порог 0,30; пять шкал «чистые»; у Magician и Seeker 1–2 пункта < 0,30; «solid, even exceptional» | Руководство, гл. 5, с. 17–18 | подтверждено | Вывод «по сути не CFA» — помечен в файле как оценка исследования |
| 8 | 04 | Seeker–Magician r = 0,51 (25% общей дисперсии); уровень чтения пунктов — 4-й класс, отчётов — 12-й; отсечка «топ-3» «rather arbitrary» | Руководство, с. 5, 6–7, 19 | подтверждено | — |
| 9 | 04 | Цены StoryWell: Core $25, Expanded $55, переход $35; «Overlooked Ally» в Expanded Report | https://www.storywell.com/purchase-the-pmai.htm | подтверждено | — |
| 10 | 04 | «world's first scientifically validated archetype assessment tool»; «not designed to put you into a predetermined box» | https://www.storywell.com/ ; https://www.storywell.com/the-pearson-marr-assessment.htm | подтверждено | — |
| 11 | 04 | PMAI-2020: анонс в мае 2020 г.; данные «since 2003»; три названия изменены, «equally positive»; StoryWell создан CAPT | https://www.carolspearson.com/wp-imort-2/pmai-re-release | подтверждено | Дата на странице: 2020-05-05 / May 6, 2020 |
| 12 | 04 | PMAI снова доступен 22.09.2025 | https://carolspearson.com/post/breaking-news-the-pmai-is-unavailable | подтверждено | — |
| 13 | 04 | McPeek R. W. (2008), *Journal of Psychological Type* 68(7), 52–67 | Библиография StoryWell: https://www.storywell.com/articles/bringing-archetype-together-with-type.htm | подтверждено (выходные данные) | Аннотация («All of the main…») и цифры ≈0,72 / ≈0,68 не проверены: ResearchGate отдаёт 403, поиск аннотацию не нашёл; пометки ⚠ в файле сохранены |
| 14 | 04 | Blandin (2024): более 1 000 человек, 81% N, 64% I; Caregiver ↔ Feeling, Thinking ↔ низкие Caregiver и Lover | https://www.storywell.com/articles/archetypes-and-personality-type-pmai-mbti.htm | подтверждено | Дата статьи — 17.06.2024 |
| 15 | 04 | Faber & Mayer (2009), *J. Research in Personality* 43(3), 307–322 | Crossref: https://api.crossref.org/works/10.1016/j.jrp.2008.11.003 | подтверждено | — |
| 16 | 04 | Исследование 2: n = 125 (52 м, 73 ж); PMAI 72 + 6 пунктов Тени = 78; RCAS–PMAI r(11) = 0,38 (ns); RCAS–самооценка 0,14 (ns); PMAI–самооценка 0,66 (p = 0,014) | http://mcd.woodbury.edu/wp-content/uploads/2016/02/Faber-Mayer-2009.pdf , с. 315–316 | подтверждено | — |
| 17 | 04 | κ = 0,79 (50 против 50 судей), 156 стимулов, 52,95 против 3,84 номинаций | Там же, с. 311–312, табл. 3 | подтверждено | — |
| 18 | 04 | Альфы RCAS 0,38–0,78 и 0,74–0,88; для «Artful & Cultured» R² = 0,12 (ns), ΔR² = 0,48 | Там же, с. 316, 319 | подтверждено | — |
| 19 | 04 | Шкала Аакер: 309 → 114 черт; 631 респондент; 37 брендов; 5 факторов объясняют 92%; 42 черты, 15 фасет | https://www.gsb.stanford.edu/sites/default/files/publication-pdf/Dimensions_of_Brand_Personality.pdf , с. 349–352 | подтверждено | В табл. 2 источника доли дисперсии по факторам дают в сумме 89,8%, а в тексте — 92%: это расхождение внутри самой статьи; файл верно цитирует текст |
| 20 | 04 | Альфы Аакер 0,93/0,95/0,93/0,91/0,90; тест-ретест через 2 мес. (n = 81) 0,75/0,74/0,76/0,75/0,77; подтверждение на 180 человек | Там же, с. 352 | подтверждено | — |
| 21 | 04 | Bechter и др. (2016): 102 студента EMBA (47 европейцев, 55 азиатов); SL — Hero по индикатору, Magician по Аакер; BT — Lover; индикатор «similar to Characterlab.com», основан на PMAI; альф нет; «still a few years off»; «somewhat too vague»; «rugged»/«charming» | PDF: https://mdpi-res.com/d_attachment/admsci/admsci-06-00005/article_deploy/admsci-06-00005.pdf ; Crossref 10.3390/admsci6020005 | подтверждено | Страница mdpi.com отдаёт 403 роботам; PDF издателя открыт |
| 22 | 04 | Xara-Brasil и др. (2018), *Revista de Gestão* 25(2), 142–159: 537 анкет, март–май 2016, 4 страны, 27 слов, «Innovation» 85–95% | https://revistas.usp.br/rege/article/view/147500 и PDF статьи | подтверждено | — |
| 23 | 04 | Hasani и др. (2025): RoBERTa + Focal Loss, 12 архетипов по X, средний F1 = 0,777, слабость на «Explorer» | Semantic Scholar API (аннотация); Crossref 10.1109/icsintesa68165.2025.11413626 | подтверждено | Полный текст закрыт — в файле так и сказано |
| 24 | 04 | Paekivi & Karjus (2026): у людей α = 0,12, κ = −0,02, согласие 46%; LLM — точность 50%, macro-F1 0,28; Polti 12,5%; в целом 68% и 0,39 | https://arxiv.org/html/2606.16053v1 , табл. 3 | подтверждено; формулировка исправлена | Цифры относятся к блоку Hall / Blumler–Katz / Polti; дуга Propp/Campbell — отдельная переменная. В 04 уточнены разделы 5 («Коротко»), 5.5 (таблица) и вывод 4: «архетипические переменные» заменены на «абстрактные переменные (блок Hall / B&K / Polti)» |
| 25 | 04 | Srivastava и др. (2021): «only one out of five attributes»; «can not be distinguished in any of the LMs» | https://aclanthology.org/2021.deelio-1.12.pdf | подтверждено; уточнено | Пять брендов — качественный разбор; исходная выборка — 697 брендов Lovett и др. Таблица 5.5 уточнена |
| 26 | 04 | Опыт Форера: 39 студентов; средняя 4,30 или 4,2 | https://en.wikipedia.org/wiki/Barnum_effect (4,30); https://en.wikipedia.org/wiki/Astrology_and_science (4,2; >40% «5»); https://www.skepdic.com/forer.html (4,26) | исправлено | Расхождение разрешено: средняя 4,26, а 4,30 и 4,2 — округления. Согласуется с пересказами «никто не ниже 2, ниже 4 — пятеро». Добавлен источник [167]. Оригинал (1949) в легальном открытом доступе не найден — ⚠ |
| 27 | 04 | Стандарт согласия кодировщиков: «должно быть 0,80 или выше»; альфа Кронбаха и корреляции не подходят | https://matthewlombard.com/reliability/ | исправлено, ⚠ снят | У Lombard: 0,80 и выше «acceptable in most situations», 0,90 — почти всегда, 0,70 — иногда в поисковых работах. Формулировка смягчена, пометка «по фрагменту выдачи ⚠» снята |
| 28 | 04 | Капустина (2016): n = 120 (60/60, 20–25 лет); MBTI, 16PF (форма C), Гарбузов; «малоинформативна»; *Вестник КемГУ* № 2, 93–101 | https://www.sibscript.ru/jour/article/download/1932/1906 (через WebFetch) | подтверждено | Через `curl` соединение сбрасывается |
| 29 | 04 | Sotirova-Kohli и др. (2013): N = 402; 67,47% против 59,93%; «outside the domain of inquiry…», «still fairly uncommon» | Europe PMC, PMC4217609 (полный текст XML) | подтверждено | — |
| 30 | 04 | Neher (1996), JHP 36(2): страницы 44–60 или 61–91 | Crossref: https://api.crossref.org/works/10.1177/00221678960362008 | исправлено | По Crossref — 61–91. Расхождение 9.1 п. 11 помечено «разрешено», источник [106] исправлен, добавлен [169] |
| 31 | 04 | Big Five: 4 504 прилагательных (Allport–Odbert), 171 черта (Cattell), Tupes и Christal (1957), наследуемость 42–57% | https://en.wikipedia.org/wiki/Big_Five_personality_traits | подтверждено | — |
| 32 | 04 | Roesler 2012, Goodwyn 2010 и 2022, Pietikainen 1998, Merlo 2023, Kreicbergs 2022, Tsai 2006, Djakeli 2018, Allen 2026, Feng 2026, Багдасарова 2022: выходные данные | Crossref по DOI (10 запросов) | подтверждено | У Kreicbergs Crossref даёт «vol. 16, no. 40», а шапка самой статьи — «2022 40(2): 21–38»; файл следует статье, правка не нужна |
| 33 | 04 | Знаки PMAI: № 4059329 (кл. 44, дисклеймер «ARCHETYPE INDICATOR», продлён 07.01.2022); № 3359380 (кл. 16); № 4041887 (кл. 44); № 4179183 (кл. 41); владелец — M&BF | https://tsdr.uspto.gov/statusview/sn85272145 ; sn77167717 ; sn85272133 ; sn85484640 | подтверждено | В истории sn85272145 есть «AUTOMATIC UPDATE OF ASSIGNMENT OF OWNERSHIP» от 08.03.2023 — это подкрепляет предположение файла об уступке. Пометку ⚠ (документ уступки не читался) правильно сохранить |
| 34 | 04 | PEARSON-MARR ARCHETYPE INDICATOR № 3034746 (кл. 16, 41) аннулирован 10.07.2026: не подана декларация по §8 | https://tsdr.uspto.gov/statusview/sn78443690 | подтверждено | — |
| 35 | 04 | STORYBRAND № 6088487 (кл. 41, «Workshops and seminars in the field of advertising and marketing»), §8/§15 приняты 31.10.2025; № 4676858 аннулирован 27.08.2021; STORY BRAND № 5338910, IR 1376275 (AU, EM, GB, JE) | TSDR sn88444964, sn87402920, rn4676858; Madrid Monitor ROM.1376275 | подтверждено | — |
| 36 | 04 | FASCINATE № 5956353 (кл. 41), §8/§15 приняты 07.05.2025; HOW TO FASCINATE № 4465770; FASCINATION ADVANTAGE № 4474428; № 4470256; № 8196489 | TSDR sn87859463; rn4465770, rn4474428, rn4470256, rn8196489 | подтверждено | — |
| 37 | 04 | HERO'S JOURNEY № 4246622 (кл. 41, IR 1426390 — GB, JE; продлён), № 6646543, № 4867550, № 4867549, № 5973469 — JCF | TSDR sn85252681, sn87507534, rn4867550, rn4867549, rn5973469; Madrid Monitor ROM.1426390 | подтверждено | — |
| 38 | 04 | HERO'S JOURNEY № 4424264 (кл. 41): владелец Hole in the Wall Gang Fund Inc., «сосуществует со знаками JCF» | https://tsdr.uspto.gov/statusview/rn4424264 | исправлено | Текущий владелец по TSDR — Joseph Campbell Foundation (уступка учтена 26.07.2023); зарегистрант — Hole in the Wall Gang Fund; продлён 20.05.2023. Строка таблицы 8.4 исправлена, добавлен источник [168] |
| 39 | 04 | ARCHETYPES № 5481385 (кл. 41; сайт с блогами, в том числе «horoscopes and astrology»): CMED, LLC (Иллинойс); §8/§15 приняты 31.10.2023; уступка учтена 20.03.2024 | https://tsdr.uspto.gov/statusview/sn86687391 | подтверждено | — |
| 40 | 04 | TTAB № 92082428: Spotify AB против № 5481385 (Project Miracle IP Holdings), подано 26.05.2023, «CAN DENIED W/O PREJ» 17.08.2023; TTAB № 91211005: JCF против «BIRTH AS A HERO'S JOURNEY», «SUSTAINED» 06.02.2014 | https://ttabvue.uspto.gov/ttabvue/v?qs=86687391 ; https://ttabvue.uspto.gov/ttabvue/v?qs=85252681 | подтверждено | — |
| 41 | 04 | GENE KEYS № 7499528 (10.09.2024; кл. 9, 16, 41, 42, 45); № 7499529, № 8447509, № 7495417–7495419, № 8304066; GENEKEYS № 6678260 (кл. 5, другой владелец) | TSDR sn98164360; rn7499529, rn8447509, rn7495417, rn7495418, rn7495419, rn8304066, rn6678260 | подтверждено | — |
| 42 | 04 | LADINI: № 8407889 (25.08.2026; кл. 9, 16, 41; дисклеймер «METHOD»; IR 1900910 от 20.10.2025; охрана в EM, TR, KZ); № 8340191 (14.07.2026; IR 1888975; охрана в EM, GE, TR; по KZ отказ); владелец — гражданка Украины; RU не назначена | TSDR sn79443153, sn79438028; Madrid Monitor ROM.1900910, ROM.1888975 | подтверждено | — |
| 43 | 04 | Jovian / Human Design: № 7892431, № 7724676 (дисклеймер «HUMAN DESIGN»), № 5797541 (§8 принята 13.06.2025), № 3264277 (аннулирован в 2018 г.); заявки THE HUMAN DESIGN SYSTEM брошены (2006; 28.09.2023 после решения 19.07.2023; 09.09.2024 после решения 07.06.2024); HUMAN DESIGN, LLC: № 7173499, № 4579387 (аннулирован 21.02.2025) | TSDR sn97639098, sn97606650, sn88009411, sn78500739, sn78500640, sn97642294, sn98217560, sn97524449, sn86134850 | подтверждено | Все даты совпали, включая «Date Abandoned» |
| 44 | 04 | ARCHETYPE ME / ARCHETYPEME.COM: «⚠ номера в заметках не указаны», аннулированы в 2020 г. | https://tsdr.uspto.gov/statusview/sn85979796 ; rn4503286 | исправлено (дополнено) | ARCHETYPE ME — № 4503286, аннулирован 30.10.2020, IR 1158661, владелец Archetypes, LLC. Номер ARCHETYPEME.COM не проверен — ⚠ оставлен |
| 45 | 04 | SACRED MONEY ARCHETYPES № 4431978: «текущий статус не уточнён ⚠»; прочие «… ARCHETYPES»: «владельцы не указаны ⚠» | TSDR rn4431978, rn7275171, rn7057387, rn8077824, rn6840864, rn8120988, rn5877102, rn7682831 | исправлено, ⚠ снят | № 4431978 продлён (19.07.2023). Остальные зарегистрированы за разными лицами, не связанными с M&BF, Пирсон или Мисс. Уточнены классы PROM ARCHETYPES (35, 41) |
| 46 | 04 | BRANDING WITH ARCHETYPES № 3795596 (кл. 41, дисклеймер «BRANDING», продлён 22.05.2020); SB7 № 3339471 аннулирован в 2014 г.; SACRED CONTRACTS № 2579651 аннулирован 14.03.2009; BRAND ARCHETYPE № 2426257 аннулирован 12.11.2021; SAGE № 7617463; EXPLORER № 2064621; HERO WITHIN № 6007408; знаки «… HUMAN DESIGN» третьих лиц | TSDR sn77827298; rn3339471, rn2579651, rn2426257, rn7617463, rn2064621, rn6007408, rn8268803, rn6393653, rn8006748, rn8190126, rn6979074 | подтверждено | — |
| 47 | 04 | Applied Innovations v. Regents, 876 F.2d 626 (8th Cir. 1989): цитаты о пунктах MMPI, «close question», «expressions of facts or processes», $226 598 и $162 161 | https://law.resource.org/pub/us/case/reporter/F2/876/876.F2d.626.88-5052.88-1072.html | подтверждено | — |
| 48 | 04 | ETS v. Katzman, 793 F.2d 533 (3d Cir. 1986): merger отклонён («do not represent the only means of expressing the ideas»); перефраз с заменой чисел; fair use для «teaching» не принят | https://law.resource.org/pub/us/case/reporter/F2/793/793.F2d.533.85-5613.html | подтверждено | — |
| 49 | 04 | ГК РФ ст. 1259 п. 5 (и п. 6 пп. 3 о фольклоре) | https://www.consultant.ru/document/cons_doc_LAW_64629/be05678dc42ddc67aae5be9ba9beebd367fb9a3f/ (WebFetch) | подтверждено | — |
| 50 | 04 | ГК РФ ст. 1274 п. 1 пп. 1–2, п. 4 | https://www.consultant.ru/document/cons_doc_LAW_64629/84bbd636598a59112a4fe972432343dd4f51da1d/ | подтверждено | — |
| 51 | 04 | ГК РФ ст. 1479: цитата «…предусмотренных международным договором» | https://www.consultant.ru/document/cons_doc_LAW_64629/2fd42c23588d0ab2c1941640216b8210901502a6/ | исправлено | Цитата была обрезана перед закрывающей кавычкой. Восстановлено: «…международным договором Российской Федерации» |
| 52 | 04 | ГК РФ ст. 1301: компенсация от 10 тыс. до 10 млн руб. или двукратная стоимость экземпляров либо права | https://www.consultant.ru/document/cons_doc_LAW_64629/c2f79b53ce582e92680379e2ebd23eeb9fb7855a/ | подтверждено | Редакция от 07.07.2025 |
| 53 | 04 | ГК РФ ст. 1515 п. 4: те же три варианта компенсации за знак | https://www.consultant.ru/document/cons_doc_LAW_64629/44bf2477089f6ece7185aaf3e37bae5ace2954cf/ | подтверждено | — |
| 54 | 04 | Пленум ВС РФ № 10, п. 80: «авторским правом не охраняются шахматная партия, методики обучения» | https://www.consultant.ru/document/cons_doc_LAW_323470/ee07ed989eace60044215bd4b9b812f99a2f6919/ | подтверждено | — |
| 55 | 04 | 17 U.S.C. §102(b); 37 C.F.R. §202.1 (a)–(c); Circular 33 (rev. 03/2021); Baker v. Selden; TRIPS ст. 9(2) | law.cornell.edu (3 страницы); https://www.copyright.gov/circs/circ33.pdf ; https://www.wto.org/english/docs_e/legal_e/27-trips_04_e.htm | подтверждено | — |
| 56 | 04 | Флорентийский суд, RG n. 2756/2020, 03.06.2020 | https://en.wikipedia.org/wiki/Human_Design | подтверждено как пересказ; помечено ⚠ (сохранено) | Википедия даёт и номер «n. cronol. 944/2020». Первоисточник решения не открывался |
| 57 | 04 | Buros: издатель — M&BF (Гейнсвилл); рецензия в 16th MMY (Spies, Plake) | https://marketplace.unl.edu/buros/pearson-marr-archetype-indicatorr.html | подтверждено; уточнено | Рецензия продаётся за $15, то есть она «недоступна», а не «не найдена». Пометка уточнена |
| 58 | 04 | StoryWell Legal: PMAI — знаки Pearson и Marr; M&BF — знаки CAPT и Storywell; capt.org → myersbriggs.org | https://storywell.com/legal.htm ; https://www.capt.org/ | подтверждено | — |
| 59 | 04 | Ramotion Archetype Finder как квиз с ⚠ во всех ячейках, «страница не открывалась» | https://www.ramotion.com/tools/archetype-finder/ | исправлено | Страница открылась. Это не опросник, а «колесо» 12 архетипов с каталогом 200 брендов; «combine up to two archetypes» подтверждено. Строка таблицы 3.1 и источник [58] исправлены |
| 60 | 04 | Iconic Fox: правило 70/30 | https://iconicfox.com.au/brand-archetypes/ | подтверждено | Примечание источника [57] обновлено |
| 61 | 04 | Putnam: «psychology-backed», «Taken by 250,000+», 12 вопросов | https://kayeputnam.com/quiz/ | подтверждено | — |
| 62 | 04 | JobCannon (ru): 24 вопроса, около 6 минут, доминирующий, вспомогательные и «теневой» архетип | https://jobcannon.io/ru/tests/jungian-archetype | подтверждено | — |
| 63 | 04 | ToolFox: 20 вопросов, «на выборке их не проверяли», процент соответствия | https://toolfox.ru/tools/archetype-day-test (WebFetch) | подтверждено | — |
| 64 | 04 | Added Value: 100 маркетологов, 10 команд, одинаковые архетипы для Tesco и M&S | https://www.mrweb.com/drno/printable/pn8627.htm | подтверждено | — |
| 65 | 04 | WPP BAV: сила в двух и более зонах, «a degree of tension»; Imperial: «almost obsessively»; Gelisim: 2% одноархетипных брендов | https://wppbav.com/insights/brand-archetypes/ ; https://www.imperial.ac.uk/…/lessons-leaders-successful-brands-have-multiple-personalities/ ; https://myo.gelisim.edu.tr/… | подтверждено | Цифра 2% действительно есть только у Gelisim; пометка ⚠ в файле корректна |
| 66 | 04 | LonerWolf: «designed for fun», «not at all a PMAI assessment»; Адт: «более 30 000» на главной | https://lonerwolf.com/psychological-archetype-test/ ; https://alinaadt.ru/ | подтверждено | — |
| 67 | 04 | Westergaard: счётчик Putnam 55 000 | https://www.nickwestergaard.com/the-psychology-of-branding-with-kaye-putnam/ | помечено ⚠ (сохранено) | Страница открылась, но цифры 55 000 в тексте нет; в файле она уже под ⚠ |
| 68 | 04 | Руководство 2002/2003 и диссертация Марра «не найдены» | Сопоставление с разделом 2.4 файла (каталог AbeBooks, Copyright Office) | исправлено (формулировка) | Источники существуют, но недоступны. Заменено на «недоступны … текстов в открытом доступе не найдено», чтобы различать «не найдено» и «недоступно» |
| 69 | 04 | Пометка «не юридическая консультация» | Чтение файла | подтверждено | Строки шапки, 8, 8.7, вывод 8 |
| 70 | 06 | Письмо Mrs. Eckstein, 16.09.1930: «Yes, I know of the Tarot», «the oldest cards historically known»; поправка Грир о 50–75 годах | https://marykgreer.com/2008/03/31/carl-jung-and-tarot/ | подтверждено | — |
| 71 | 06 | «⚠ Что это то же письмо 1930 г., не сверено» (*Letters* I, с. 77, «Spanish gypsies») | Грир [1] (текст письма 1930 г. содержит ту же фразу); компиляция [2] через WebFetch | исправлено, ⚠ сужен | Фраза входит в письмо Eckstein 1930 г., значит, речь об одном письме. Страница 77 по тому не сверена — ⚠ оставлен только на номер страницы |
| 72 | 06 | Семинар «Видения», 01.03.1933, *Visions* vol. 2, с. 923: «psychological images…», «sort of archetypal ideas…» | Грир [1]; издатель: https://press.princeton.edu/books/hardcover/9780691099712/visions (WebFetch) | подтверждено; дополнено | В той же цитате «архетипическими идеями» названы солнце, повешенный, башня и **колесо фортуны**. Колесо было пропущено в таблице A и в тексте. Ячейки Юнга в таблице A теперь ссылаются на цитату у Грир, а не только на Википедию |
| 73 | 06 | CW 9i §81: «distantly descended from the archetypes of transformation», лекция Бернулли | Грир [1] | подтверждено | Год лекции не установлен — ⚠ сохранён |
| 74 | 06 | «diable» (*Visions*, с. 923); *Children's Dreams*, с. 351; *Letters* II, с. 538 (Cornell 1960) | https://carljungdepthpsychologysite.blog/2021/08/10/tarot-2/ (WebFetch; `curl` получает 429) | подтверждено; атрибуция исправлена | Страница 538 есть только в [2], а в тексте стояла ссылка лишь на [1]. Добавлена [2] и перечень методов из письма |
| 75 | 06 | von Franz (1988); Bair (2003), с. 549; Ханни Биндер, 1950; Grimaud; группа распалась около 1954 г. | Грир [1] | подтверждено | — |
| 76 | 06 | Nichols, исп. изд. Kairós: оглавление (Великая Мать, Творец и трикстер, Отец цивилизации…), пролог Грир, введение ван дер Поста | https://content.e-bookshelf.de/media/reading/L-18717667-86f49bf70f.pdf | подтверждено | Легальный ознакомительный фрагмент |
| 77 | 06 | Aeclectic: книга Nichols «very unevenly written», ошибки в истории Таро | https://www.aeclectic.net/tarot/books/jung-and-tarot/ | подтверждено | — |
| 78 | 06 | Конспект OLLI: цитаты Nichols (Маг → Самость, Дьявол — «SHADOW», «spot of individuation», «repetitive instinctual round»), Император — «Wise Old Man» и «powerful animus figure», «The Charioteer, or our ego» | https://www.uc.edu/content/dam/refresh/cont-ed-62/olli/22-winter/jung%20tarot%201.pdf | подтверждено | Атрибуции внутри конспекта по книгам не сверены — ⚠ в файле сохранён |
| 79 | 06 | Pollack: издатель — «a modern psychological interpretation of the tarot archetypes» | https://redwheelweiser.com/book/seventy-eight-degrees-of-wisdom-9781578636655/ | подтверждено | — |
| 80 | 06 | Banzhaf, *Das Tarotbuch*, с. 15: «kollektiven Unbewussten», «archetypischen Lebensweg», сноска о *Tarot und die Reise des Helden* | https://www.penguinrandomhouse.de/leseprobe/Das-Tarotbuch/leseprobe_9783442336463.pdf | подтверждено | — |
| 81 | 06 | Rosengarten: «need for control is the Emperor», «need for solitude the Hermit»; Колесница — «need to have new adventures» ⚠ | https://www.whitecraneinstitute.org/wcjarchives/wc01104.htm | подтверждено, ⚠ снят | Цитата о Колеснице есть в той же фразе рецензии. Пометка снята в таблице A и в примечании под ней |
| 82 | 06 | Wang: аннотация (Mother / Father / Son / Daughter; Жрица — «Virgin Mary», «Isis»; пять лет с Институтами Юнга); learntarot: книга 1981, колода 2002 | https://www.abebooks.com/9780971559110/…/plp ; https://learntarot.com/judesc.htm | подтверждено | — |
| 83 | 06 | Kerykeion: Императрица и Жрица — Анима; Император и Иерофант — Анимус; Император и Колесница — Персона; Дьявол, Луна, Башня — Тень; Солнце и Мир — Самость; страница о пути героя; обновлено 13.06.2026 | https://kerykeion.net/content/learn-tarots/psychology/jung-and-tarot ; …/heros-journey-in-major-arcana | подтверждено | — |
| 84 | 06 | Venefica: таблица «Jung's 12 Archetypes vs. Tarot's Major Players»; «made popular by Carl Jung»; соответствие «Not exactly» взаимно-однозначное | https://www.tarotteachings.com/?p=2602 | подтверждено | — |
| 85 | 06 | Lau, «Brand Archetypes…»: роли арканов («Innovator/Disruptor», «Authority/Leader», «Nurturer/Creator»…); Nike — «The Hero» во введении | https://mysticryst.com/blogs/the-mystic-journal/brand-archetypes-aligning-your-brand-with-major-arcana | подтверждено | — |
| 86 | 06 | **ГЛАВНОЕ.** Таблица «брендовый архетип → аркан» (§2.2): столбец Lau и «совпадение 3 из 3» для Императора | Сверка ролей Lau [33] с архетипами Марк и Пирсон | исправлено | Lau брендовые архетипы Марк и Пирсон не использует: её роли разнесены по строкам исследователем по сходству названий. Это собственная связка исследования, поданная как найденная. Под таблицей добавлено пояснение «Как читать столбец Lau»; уточнены «Коротко» §2.2 и строка сводной таблицы §3 («Император — Правитель у Venefica и b17; у Lau — сопоставление исследования») |
| 87 | 06 | Mizzi: три прилагательных, выбор карты (Шут) | https://janefriedman.com/how-to-use-tarot-to-build-your-brand-as-a-creative/ | подтверждено | — |
| 88 | 06 | JobCannon: «Twelve archetypes are a cast; 22 trumps are a plot» (⚠ «только в сниппете») | https://jobcannon.io/blog/major-arcana-personality-archetypes | подтверждено, ⚠ снят | Фраза есть на странице |
| 89 | 06 | Пирсон: на странице о корнях модели нет Таро и астрологии; студия: «strongest brands behaved like archetypes», «the archetype on its own does not predict…» | https://www.carolspearson.com/post/new-article-the-roots-of-the-pearson-marr-archetypes ; https://thebrandarchetypes.com/history/ | подтверждено | Поиск по словам tarot, astrolog, zodiac, numerolog — 0 совпадений |
| 90 | 06 | Молоканова: «каждое изображение на картах Таро представляет собой отдельный архетип»; «я использую другую концепцию – архетипы Таро» | https://www.litres.ru/book/kseniya-molokanova/…/chitat-onlayn/ | подтверждено | — |
| 91 | 06 | Грир: «archetypal forms»; «I have, however, run into quite a few privately»; издатель *Archetypal Tarot*: «pattern of personal destiny» | https://marykgreer.com/2011/08/17/who-are-you-in-the-tarot/ ; https://redwheelweiser.com/book/archetypal-tarot-9781578637485/ | подтверждено | Цитата Грир о 1977 г. («I first learned…») есть только через модуль базы [47] (Greer 2021, с. xiii); поиском не подтверждена, но и не опровергнута |
| 92 | 06 | Арриен, *The Tarot Handbook* (1987; изд. 1997; 320 с.; колода Тота; Lifetime и Growth symbols) — «⚠ по сниппетам выдачи» | https://www.aeclectic.net/tarot/books/handbook-arrien/ | исправлено, ⚠ сужен | Страница открылась и подтверждает: 1987, переиздание через 10 лет, 320 с., колода Тота. Раздел о старших арканах — «…Teachings, and Archetypes». Формулировка «portraitures and archetypes» не найдена — ⚠ оставлен только на неё |
| 93 | 06 | Матрица судьбы: метод Ладини; год 2006 «подтверждён только сайтом matrica-sudby.ru» | https://eksmo.ru/book/matritsa-sudby-pervoistochnik-ITD1409842/ ; https://matrica-sudby.ru/ ; https://vikna.tv/ru/dlia-tebe/matrytsa-sudby-chto-eto-y-kak-y-o-chem-mozhno-uznat/ | исправлено (формулировка) | Издатель подтверждает авторство («разработанный Натальей Ладини»). Год 2006 дают и сайт, и vikna.tv [60], поэтому «только сайтом» неверно. По книге год не сверен — ⚠ |
| 94 | 06 | matrica-sudby.ru: «22 кодами судьбы», «уже десятки лет», «Каждая энергия в матрице - это один из 22 архетипов», сервис «Матрица личного бренда», автор — Я. Шмидт | https://matrica-sudby.ru/ | подтверждено | — |
| 95 | 06 | Знаки LADINI (кратко в §2.4) | Те же записи TSDR и Madrid Monitor, что в п. 42 | подтверждено | — |
| 96 | 06 | Decoz: «age-old», «There is a right way…», «Numerology does not remove free will»; Millman — «modern method of insight based on ancient wisdom» | https://www.worldnumerology.com/numerology-life-path/ ; https://peacefulwarrior.com/the-life-you-were-born-to-live/ | подтверждено | Википедия даёт для книги Millman 1994 — так и указано в файле |
| 97 | 06 | JobCannon (нумерология): ярлыки чисел, сравнение с юнговскими архетипами, «Numerology is not a science», «no peer-reviewed empirical backing» | https://jobcannon.io/assessments/numerology/about | подтверждено | — |
| 98 | 06 | Storm, *The Enigma of Numbers* (2008, 552 с.): «number archetype of … Jung», числа 1–10 | https://www.goodreads.com/book/show/5217699-enigma-of-numbers | подтверждено | — |
| 99 | 06 | Dreamspell: календарь начат в 1987 г., игра — 1990 г.; Аргуэльес: *Mandala* (1972), «Galactic Mayas», критика Hess 1993 | https://en.wikipedia.org/wiki/Dreamspell ; https://en.wikipedia.org/wiki/Jos%C3%A9_Arg%C3%BCelles | подтверждено | — |
| 100 | 06 | Сюцай: слов «архетип», «Юнг», «Таро» нет; раджа-йога; более 10 000 учеников; «споры о ее эффективности» | https://zhanatglobal.com/filosofiya-syucai | подтверждено | — |
| 101 | 06 | Письмо Барбо 26.05.1954 (*Letters II*, с. 400–402): «coloquio de los dioses… arquetipos psíquicos»; письма Фрейду 254J и 259J; OC 15, с. 50; *Aion*: «conozco demasiado poco…» | https://www.trotta.es/static/pdf/JUNG_Sobre_astrologia_Avance_de_lectura.pdf | подтверждено | — |
| 102 | 06 | Эксперимент CW 8: §§869, 878; §901 — «merely chance»; §877; второй опыт — 10 из 200 | Zeng & Fraikin (2025): https://repository.essex.ac.uk/41591/1/… ; Crossref 10.1111/1468-5922.70016 (70(5), 808–824) | подтверждено | — |
| 103 | 06 | Партии эксперимента: «180 пар, затем 220, всего 483» | https://jungianalchemist.substack.com/p/carl-jungs-curious-experiment-to | исправлено | 180 + 220 = 400. В источнике три партии («a second batch of 220 couples and a third, bringing the total to 483»). Добавлено «и третья партия». Контроль 32 220 пар подтверждён |
| 104 | 06 | «⚠ Номер тома CW для ссылки Zeng & Fraikin на Jung 1958/1973, §1175, не уточнён» | Список литературы Zeng & Fraikin: «Jung (1958/1973). An astrological experiment. CW 18» | исправлено, ⚠ снят | — |
| 105 | 06 | Грин (1984, с. 276) объясняет, «почему эксперимент работает»; Тарнас итог эксперимента не упоминает | Zeng & Fraikin, с. 7–9 | подтверждено | — |
| 106 | 06 | Тарнас: Сатурн — «principle of limit and finitude…», Нептун — «…dissolve boundaries…», «many hundreds of cases»; сайт — «pantheon of the planetary archetypes» | https://www.archai.org/wp-content/uploads/2016/04/Tarnas-%E2%80%93-The-Ideal-and-the-Real-%E2%80%93-Archai-Issue-1.pdf ; https://cosmosandpsyche.com/ | подтверждено | — |
| 107 | 06 | *Cosmos and Psyche*: Уран — Прометей; WSJ — «unadulterated crack-pottery»; критика Херона | https://en.wikipedia.org/wiki/Cosmos_and_Psyche | подтверждено | — |
| 108 | 06 | Психологическая астрология: Радьяр и Рупрети, «humanistic astrology»; «no methodologically sound» исследований | https://en.wikipedia.org/wiki/Psychological_astrology | подтверждено | — |
| 109 | 06 | Берт, *Archetypes of the Zodiac* (1988), рубрики «Archetype (Psychology)», «Zodiac», «Astrology» | Open Library JSON: https://openlibrary.org/works/OL1670943W.json | подтверждено | — |
| 110 | 06 | kodeam: Овен — Воин, Телец — Опекун … Рыбы — Сирота; «I made a hypothesis» | https://proza.ru/2019/08/17/1375 | подтверждено; описание источника исправлено | Текст на proza.ru англоязычный («What does the Zodiac have in common with archetype»). Исправлены описание [111] и фраза о непрочитанной англоязычной версии |
| 111 | 06 | Dykman (19.11.2024): Warrior, Earth Spirit, Trickster, Caregiver, Sovereign, Maiden, Diplomat, Sorcerer, Explorer, Sage, Visionary, Mystic | https://myastrology.com/article/astrological-signs-and-their-legendary-archetypes/ | подтверждено | Все 12 ярлыков совпали |
| 112 | 06 | Lau, «The 12 Zodiac Signs as Jungian Archetypes»: 12 двойных ярлыков; рамка «building on Jung and Joseph Campbell» | https://mysticryst.com/blogs/the-mystic-journal/the-12-zodiac-signs-as-jungian-archetypes-your-birth-chart-as-psyche-map | подтверждено | Все 12 ярлыков совпали |
| 113 | 06 | Таблица «знак → архетип»: у всех трёх авторов совпадают 2 знака из 12 | Сверка трёх страниц (пп. 110–112) | подтверждено с уточнением | Овен совпадает буквально. Скорпион засчитан по близости Sorcerer к Magician — это оценка исследования; при строгом сравнении названий — 1 из 12. Оговорка добавлена в §2.8.4 |
| 114 | 06 | Sorsby: «bold, confident, high-impact» (Лев на Асценденте), «structured, authoritative, legacy-driven» (Козерог-Солнце) | https://bonniesorsby.com/blog/how-your-birth-chart-shapes-your-brand-identity-and-aesthetic | подтверждено | — |
| 115 | 06 | Колесо Мисс: «twelve houses of the zodiac»; 12 домов; Chart of Origin «similar in nature to a natal chart», «simple intuitive process»; 24 бумажки | https://content.e-bookshelf.de/media/reading/L-535049-ae25abbe32.pdf ; https://myss.com/free-resources/sacred-contracts-and-your-archetypes/the-archetypal-wheel/ ; …/casting-your-chart-of-origin/ | подтверждено | — |
| 116 | 06 | Human Design: 1992; «alleged mystical experience in 1987»; «pseudoscientific»; суд Флоренции | https://en.wikipedia.org/wiki/Human_Design | подтверждено | — |
| 117 | 06 | Jovian: кресты — «overarching theme of your life», «192 basic Incarnation Crosses», слова «archetype» нет; условия — «exclusive worldwide rights…», «derived from, and based upon» | https://jovianarchive.com/pages/incarnation-crosses-in-human-design ; https://jovianarchive.com/pages/terms-and-conditions | подтверждено | — |
| 118 | 06 | JobCannon: типы HD — «The Initiator», «The Builder», «The Multi-Passionate»…; «Human Design archetype» | https://jobcannon.io/types/human-design | подтверждено | — |
| 119 | 06 | Gene Keys: «cycles continuously through 64 archetypes»; «archetypal patterns … (Shadows)»; «Brand» в Pearl Sequence, «true recognition»; «Prohibited Commercial Use…» | https://genekeys.com/how-to-read-your-profile/ ; https://genekeys.com/terms-and-conditions/ | подтверждено | — |
| 120 | 06 | Joey Yap, BaZi Profiling Box Set (JY Books, 2010): «personal, social and work masks»; соответствия профилей божествам; слова «archetype» нет | https://www.abebooks.com/9789675395598/BaZi-Profiling-Box-Set-Yap-9675395591/plp | подтверждено | Девять профилей перечислены в аннотации; десятый (The Pioneer) — по Goodreads [137] |
| 121 | 06 | Соционика: Юнг + Кемпинский; Комиссия РАН по лженауке; модель Биби (8 ролей) | https://en.wikipedia.org/wiki/Socionics ; https://en.wikipedia.org/wiki/John_Beebe | подтверждено | — |
| 122 | 06 | Carlson (1985), *Nature* 318(6045): 419–425; NCGR; CPI; «fair test»; «clearly refutes the astrological hypothesis» | Crossref 10.1038/318419a0; https://en.wikipedia.org/wiki/Shawn_Carlson | подтверждено | — |
| 123 | 06 | Dean & Kelly (2003): 2 101 человек, интервал 4,8 мин, 110 переменных в 11, 16 и 23 года, значимы 5 из 110 при 5,5 ожидаемых; эффект 0,051 (более 40 исследований, около 700 астрологов); согласие 0,101 (25 исследований); норма ≥ 0,8 | https://astrology-and-science.com/D-psia2.htm | подтверждено | — |
| 124 | 06 | Тест на интуицию: 45 астрологов, 160 испытуемых, «по EPQ», хуже догадки по возрасту | Там же | исправлено | В источнике — Eysenck Personality Inventory (EPI), а не EPQ. Исправлено. Эффект 0,01 против 0,14 при догадке по возрасту подтверждён |
| 125 | 06 | Hartmann, Reuter & Nyborg (2006), *PAID* 40(7): 1349–1362 | Crossref 10.1016/j.paid.2005.11.017 | подтверждено (выходные данные); помечено ⚠ (сохранено) | Размеры выборок (более 4 000 и более 11 000) не подтверждены: аннотация скрыта издателем, ссылка на библиографию NLS отдаёт 404 (помечена) |
| 126 | 06 | Wunder (2003), *PAID* 35(8): 1783–1789 | Crossref 10.1016/s0191-8869(03)00002-3 | подтверждено | — |
| 127 | 06 | Wyman & Vyse (2008): 52 студента (38 ж, 14 м), средний возраст 19,3; цитата аннотации; эффект Барнума для обоих видов описаний | Europe PMC REST (PMID 18649494); Crossref 10.3200/GENP.135.3.287-300 | подтверждено | — |
| 128 | 06 | Гоклен 1955; Comité Para 1967 (473 из 535); Зелен — 22% против 17%; CSICOP 1979 — отрицательный результат; CFEPP — 1 066 чемпионов | https://en.wikipedia.org/wiki/Mars_effect | подтверждено | 55 из 408 (13,48%) у CSICOP по-прежнему только по сводке — ⚠ сохранён |
| 129 | 06 | «Дин (2011) показал, что эффект исчезает у родившихся после 1950 г.» | https://en.wikipedia.org/wiki/Mars_effect | исправлено | По источнику эффекта после 1950 г. не нашёл сам Гоклен, а Дин лишь предположил объяснение (запись времени врачами; искажения примерно у 3% выборки). «Показал» заменено на «предположил» |
| 130 | 06 | Forer: «газетная астрологическая книга»; 4,30 против 4,2 | Как в п. 26 | исправлено | «Newsstand astrology book» — книга из газетного киоска, а не «газетная». Расхождение разрешено (4,26). Добавлен источник [164] |
| 131 | 06 | Синхронистичность: Bonds 2002 («neither testable nor falsifiable»), Carroll 2003, van Elk и др. 2016, Kerr 2013 (Паули) | https://en.wikipedia.org/wiki/Synchronicity | подтверждено | — |
| 132 | 06 | Юнговские архетипы: «representations … not inherited, only the forms»; Shelburne, Reed | https://en.wikipedia.org/wiki/Jungian_archetypes | подтверждено | — |
| 133 | 06 | Таро: Семецкая; Pew 2025 — 11%; Рэнди; Даммет; семинар 1933 г. | https://en.wikipedia.org/wiki/Tarot_card_reading | подтверждено | Отчёт Pew не открывался — ⚠ в файле сохранён |
| 134 | 06 | Ссылка на psytests.org (источник [43]) | Правило задания о неавторизованных копиях | удалено | URL страницы с пунктами теста удалён; оставлено библиографическое описание с пометкой, как в 04 [39] |
| 135 | 06 | Честная итоговая оценка (§5) опирается на источники | Сверка ссылок §5 с проверенными источниками: [47][48][31][81][1][8][38][41][32][39][43][118][152][95][155][156][159][158][151][161][92][162][73][116] | подтверждено | Выводы, которые принадлежат исследованию, помечены как выводы r12 и r13. Опорные цифры (0,10; нулевые эффекты; «I made a hypothesis»; «Numerology is not a science»; «астрология относится к области верований») сверены |
| 136 | 06 | Цолькин, Ло Шу, квадраты, Сюцай, восточные системы: «связок не найдено» | Чтение разделов и ограничений; проверка оговорок «не искалось» и «предварительно» | подтверждено (по форме) | Файл различает «не найдено» и «не искалось / недоступно» (шапка, §2.6, §2.13, сводная таблица) |

---

## 3. Соблюдение правил

| Правило | 04-diagnostics | 06-esoteric-links | Что сделано |
|---|---|---|---|
| Нет цитат длиннее ~25 слов | Самая длинная — 22 слова (условия StoryWell) | Самая длинная — 23 слова (условия Gene Keys); 20 слов — заголовок статьи | Нарушений нет |
| Нет ссылок на неавторизованные копии (psytests с пунктами тестов, ebin.pub, сканы archive.org и т. п.) | psytests без ссылок [39]; онлайн-копия книги Марк и Пирсон упомянута без ссылки [5] | **Нарушение:** [43] вёл на страницу psytests.org с пунктами теста | Ссылка [43] удалена. Фрагменты e-bookshelf.de, Penguin Random House (Leseprobe), Litres, Livelib и Яндекс Книг — легальные ознакомительные фрагменты издателей и магазинов |
| Пункты тестов не воспроизводятся | Не воспроизводятся (примеры пунктов MMPI и Faber & Mayer в файл не перенесены) | — | Нарушений нет |
| Неподтверждённое помечено «⚠» | В целом соблюдено | В целом соблюдено | Восемь пометок сняты после подтверждения: Lombard, Neher, статус SACRED MONEY ARCHETYPES, владельцы прочих «… ARCHETYPES», Ramotion (04); Rosengarten о Колеснице, JobCannon «cast/plot», том CW 18 (06). Три сужены: ARCHETYPE ME (номер найден, ⚠ оставлен только для .COM), Eckstein / *Letters* I, Арриен. Добавлены там, где подтверждения нет: оригинал Forer, год Ладини по книге, номер ARCHETYPEME.COM, пять битых ссылок |
| «Не найдено» и «недоступно» различаются | В шапке определения не было | Определено в шапке | В 04 добавлено определение в шапку; формулировка о руководстве 2002/2003 и о рецензии Buros исправлена на «недоступно» |
| Номера [n] соответствуют спискам | 169 источников, нет висячих ссылок, неиспользованных номеров, дублей и пропусков; 1–166 идут по первому упоминанию, 167–169 добавлены в конец | 164 источника, нет висячих ссылок, неиспользованных номеров, дублей и пропусков; 164 добавлен в конец | Проверено скриптом после правок |
| Нет рекомендаций по проектированию продукта | Нет; раздел 8.7 — правовая сводка с пометкой «не юридическая консультация» | Нет; §5 даёт статус идеи по источникам («символическая интерпретация… не диагностика») | Нарушений нет |
| Нет собственных связок исследования, выданных за найденные (06) | — | **Одно нарушение:** столбец Lau в таблице §2.2 и «3 из 3» в сводной таблице | Добавлено пояснение; формулировки «Коротко» и §3 исправлены. Остальные сопоставления (совпадения в §2.1.4, «2 из 12», «маска ≈ персона», ярлыки чисел) уже были помечены как выводы исследователя или наблюдения |

---

## 4. Таблица проверки URL

Сначала проверены все URL из обоих списков источников: `curl -L`, затем повторно по одному через HTTP/1.1.

- **04:** 199 уникальных URL. Открылись 172. Ещё 11 прочитаны другим путём: consultant.ru (5) и ToolFox — через WebFetch; диссертация Spangenberg — через WebFetch; Bechter — PDF издателя на mdpi-res.com; DOI Wiley, Sage, MDPI — через Crossref. Остальные 16 не открылись. Это антибот-защита (ResearchGate, Emerald, ScienceDirect, Convince & Convert, Spirituality & Practice, journals.sagepub.com; 403) или адреса, которые уже помечены в файле: ФИПС, Роспатент, akademikarsiv.cbu.edu.tr, jibm.ut.ac.ir, brandme.academy (402), а также TTABVUE (2 запроса, «пустой ответ»; две другие страницы TTABVUE открылись). **Новых битых ссылок в 04 нет.**
- **06:** 200 уникальных URL. Открылись 178. Ещё 5 прочитаны другим путём: carljungdepthpsychologysite.blog (429), Princeton UP, ToolFox — через WebFetch; Europe PMC — через REST API. Ссылка psytests.org удалена. **Битые на 2026-10-16 и помеченные «⚠ ссылка недоступна на 2026-10-16»:** Paragon House [18] (тайм-аут), b17.ru [30] (503), Women of Grace [70] (сброс соединения), Urania Trust [104] (502), NLS [155] (404). Gumroad [35] и jung.org [108] (404) уже были помечены в файле. Остальные 403 — антибот-защита: tandfonline, PhilPapers, Medium, LibraryThing, Knox County Library, MIT Press Bookstore, Blinkist, Ingenta, Simon & Schuster. Почти все они уже помечены в файле как «по выдаче» или «403».

### 4.1. URL файла 04, проверенные по содержанию (49)

| № | Ист. | URL | Доступ | Подтверждает утверждение? | Комментарий |
|---|---|---|---|---|---|
| 1 | [1] | https://cdn.prod.website-files.com/5fc7fbb375805cc285353295/65d8ffa286160b97014347f7_PMAI_Manual_2021-1.pdf | 200, PDF | да | Все цифры разделов 2.1–2.3 |
| 2 | [2] | https://kayeputnam.com/quiz/ | 200 | да | «psychology-backed», «250,000+» |
| 3 | [6] | https://journals.lib.vutbr.cz/index.php/trends/article/download/544/524/1885 | 200, PDF | да | Около 300 роликов, 92, 50, 2 400 комментариев, NVivo |
| 4 | [7] | https://api.crossref.org/works/10.1109/icsintesa68165.2025.11413626 | 200 | да | Выходные данные, с. 525–530 |
| 5 | [8] | http://mcd.woodbury.edu/wp-content/uploads/2016/02/Faber-Mayer-2009.pdf | 200, PDF | да | Пп. 16–18 раздела 2 |
| 6 | [10] | https://jobcannon.io/ru/tests/jungian-archetype | 200 | да | — |
| 7 | [12] | https://toolfox.ru/tools/archetype-day-test | `curl` 000; WebFetch — да | да | — |
| 8 | [18] | https://www.mrweb.com/drno/printable/pn8627.htm | 200 | да | — |
| 9 | [19] | https://revistas.usp.br/rege/article/view/147500 | 200 | да | Плюс PDF статьи |
| 10 | [20] | https://digital.lib.washington.edu/researchworks/items/c15713ba-a19c-4da6-9ca8-2758d42560e1 | `curl` 403; WebFetch — да | частично | Страница записи: заглавие, автор, 2021, аннотация о модели Марк и Пирсон. Страницы 17–25 не сверялись |
| 11 | [21] | https://ideas.repec.org/a/eee/bushor/v66y2023i5p615-629.html | 200 | да | «may have lost its relevance» |
| 12 | [24] | https://aclanthology.org/2021.deelio-1.12 (и .pdf) | 200 | да | — |
| 13 | [25] | https://arxiv.org/html/2606.16053v1 | 200 | да, с уточнением | См. п. 24 раздела 2 |
| 14 | [28] | https://www.storywell.com/purchase-the-pmai.htm | 200 | да | — |
| 15 | [29] | https://www.storywell.com/the-pearson-marr-assessment.htm | 200 | да | — |
| 16 | [31] | https://www.storywell.com/articles/bringing-archetype-together-with-type.htm | 200 | да (выходные данные McPeek) | — |
| 17 | [31] | https://www.researchgate.net/publication/216101940_The_Pearson-Marr_Archetype_Indicator_and_psychological_type | 403 (и WebFetch) | недоступно | ⚠ в файле сохранены |
| 18 | [32] | https://www.storywell.com/articles/archetypes-and-personality-type-pmai-mbti.htm | 200 | да | — |
| 19 | [33] | https://storywell.com/legal.htm | 200 | да | — |
| 20 | [34] | https://marketplace.unl.edu/buros/pearson-marr-archetype-indicatorr.html | 200 | да | Рецензия платная |
| 21 | [35] | https://www.storywell.com/ | 200 | да | — |
| 22 | [36] | https://www.carolspearson.com/about/archetypal-assessments | 200 | да | Идентификатор Webflow совпал |
| 23 | [37] | https://www.sibscript.ru/jour/article/download/1932/1906 | `curl` 000; WebFetch — PDF | да | — |
| 24 | [43] | https://www.carolspearson.com/wp-imort-2/pmai-re-release | 200 | да | — |
| 25 | [45] | https://carolspearson.com/post/breaking-news-the-pmai-is-unavailable | 200 | да | — |
| 26 | [46] | https://tsdr.uspto.gov/statusview/sn85272145 (и sn78443690, sn77167717, sn85272133, sn85484640) | 200 (по одному) | да | При параллельных запросах TSDR отдаёт 403 |
| 27 | [49] | https://lonerwolf.com/psychological-archetype-test/ | 200 | да | — |
| 28 | [50] | https://www.mdpi.com/2076-3387/6/2/5 | 403 (антибот); PDF на mdpi-res.com — 200 | да | — |
| 29 | [55] | https://tsdr.uspto.gov/statusview/sn85979796 | 200 | да | Номер 4503286 дополнен |
| 30 | [57] | https://iconicfox.com.au/brand-archetypes/ | 200 | да | — |
| 31 | [58] | https://www.ramotion.com/tools/archetype-finder/ | 200 | да; описание в файле исправлено | — |
| 32 | [67] | https://www.nickwestergaard.com/the-psychology-of-branding-with-kaye-putnam/ | 200 | нет (цифры 55 000 нет) | ⚠ сохранён |
| 33 | [78] | https://wppbav.com/insights/brand-archetypes/ | 200 | да | — |
| 34 | [86] | https://www.imperial.ac.uk/business-school/ib-knowledge/marketing/lessons-leaders-successful-brands-have-multiple-personalities/ | 200 | да | — |
| 35 | [88] | https://matthewlombard.com/reliability/ | 200 | да, формулировка уточнена | — |
| 36 | [89] | https://myo.gelisim.edu.tr/en/akademik-department-public-relations-and-advertisement-news-how-to-use-archetypes-in-brand-positioning | 200 | да | — |
| 37 | [96] | https://www.gsb.stanford.edu/sites/default/files/publication-pdf/Dimensions_of_Brand_Personality.pdf | 200, скан | да | — |
| 38 | [97] | https://en.wikipedia.org/wiki/Big_Five_personality_traits | 200 | да | — |
| 39 | [108] | https://en.wikipedia.org/wiki/Barnum_effect | 200 | да (4,30) | Расхождение разрешено через [167] |
| 40 | [110] | https://pmc.ncbi.nlm.nih.gov/articles/doi/10.3390/bs3040541 (через Europe PMC PMC4217609) | 200 (API) | да | — |
| 41 | [113] | https://en.wikipedia.org/wiki/Astrology_and_science | 200 | да (4,2; более 40%) | — |
| 42 | [119] | https://www.law.cornell.edu/uscode/text/17/102 | 200 | да | — |
| 43 | [120] | https://www.consultant.ru/document/cons_doc_LAW_64629/be05678dc42ddc67aae5be9ba9beebd367fb9a3f/ | `curl` — сброс; WebFetch — да | да | — |
| 44 | [123] | https://law.resource.org/pub/us/case/reporter/F2/876/876.F2d.626.88-5052.88-1072.html | 200 | да | — |
| 45 | [124] | https://law.resource.org/pub/us/case/reporter/F2/793/793.F2d.533.85-5613.html | 200 | да | — |
| 46 | [126] | https://www3.wipo.int/madrid/monitor/en/showData.jsp?ID=ROM.1376275 | 200 | да | — |
| 47 | [128] | https://www3.wipo.int/madrid/monitor/en/showData.jsp?ID=ROM.1900910 | 200 | да | — |
| 48 | [152] | https://ttabvue.uspto.gov/ttabvue/v?qs=86687391 | 200 (повторно) | да | — |
| 49 | [160] | https://www.consultant.ru/document/cons_doc_LAW_64629/2fd42c23588d0ab2c1941640216b8210901502a6/ | WebFetch — да | да, цитата исправлена | — |

Также по содержанию открыты [130] Baker v. Selden, [131] Circular 33, [132] 37 CFR 202.1, [122] TRIPS, [121] Бернская и [161] Парижская конвенции (200), [133] Пленум п. 80, [139] ст. 1274, [163] ст. 1301, [164] ст. 1515 (WebFetch), [135], [136], [141], [142], [144], [145], [148], [149], [151] (TSDR — 200), [127], [129] (Madrid Monitor — 200), [156] (TTABVUE — 200), [14] alinaadt.ru (200).

### 4.2. URL файла 06, проверенные по содержанию (55)

| № | Ист. | URL | Доступ | Подтверждает утверждение? | Комментарий |
|---|---|---|---|---|---|
| 1 | [1] | https://marykgreer.com/2008/03/31/carl-jung-and-tarot/ | 200 | да | Плюс два дополнения (колесо фортуны, письмо 1930 г.) |
| 2 | [2] | https://carljungdepthpsychologysite.blog/2021/08/10/tarot-2/ | `curl` 429; WebFetch — да | да | Страницы 77, 538, 351, 923 |
| 3 | [3] | https://press.princeton.edu/books/hardcover/9780691099712/visions | `curl` 403; WebFetch — да | да | ред. C. Douglas, 1997, два тома |
| 4 | [7] | https://redwheelweiser.com/book/tarot-and-the-archetypal-journey-9781578636594/ | 200 | да | На странице сейчас ISBN другого издания (9781633411180) |
| 5 | [8] | https://content.e-bookshelf.de/media/reading/L-18717667-86f49bf70f.pdf | 200, PDF | да | — |
| 6 | [9] | https://www.aeclectic.net/tarot/books/jung-and-tarot/ | 200 | да | — |
| 7 | [12] | https://www.uc.edu/content/dam/refresh/cont-ed-62/olli/22-winter/jung%20tarot%201.pdf | 200, PDF | да | — |
| 8 | [13] | https://redwheelweiser.com/book/seventy-eight-degrees-of-wisdom-9781578636655/ | 200 | да | — |
| 9 | [16] | https://www.penguinrandomhouse.de/leseprobe/Das-Tarotbuch/leseprobe_9783442336463.pdf | 200, PDF | да | — |
| 10 | [18] | https://paragonhouse.com/product/tarot-and-psychology-spectrums-of-possibility/ | тайм-аут (`curl` и WebFetch) | недоступно | Помечено «⚠ ссылка недоступна на 2026-10-16» |
| 11 | [20] | https://www.whitecraneinstitute.org/wcjarchives/wc01104.htm | 200 | да | ⚠ о Колеснице снят |
| 12 | [21] | https://www.abebooks.com/9780971559110/Jungian-Tarot-Archetypal-Imagery-Trilogy-0971559112/plp | 200 | да | — |
| 13 | [22] | https://learntarot.com/judesc.htm | 200 | да | — |
| 14 | [25] | https://kerykeion.net/content/learn-tarots/psychology/jung-and-tarot | 200 | да | — |
| 15 | [26] | https://kerykeion.net/content/learn-tarots/psychology/heros-journey-in-major-arcana | 200 | да | — |
| 16 | [30] | https://www.b17.ru/article/739217/ | 503 | недоступно | Помечено |
| 17 | [31] | https://www.litres.ru/book/kseniya-molokanova/arhetipy-taro-kak-cherez-datu-rozhdeniya-poznakomitsya-72830167/chitat-onlayn/ | 200 | да | — |
| 18 | [32] | https://www.tarotteachings.com/?p=2602 | 200 | да | — |
| 19 | [33] | https://mysticryst.com/blogs/the-mystic-journal/brand-archetypes-aligning-your-brand-with-major-arcana | 200 | да | Сопоставление с Марк и Пирсон делает исследование — исправлено |
| 20 | [34] | https://janefriedman.com/how-to-use-tarot-to-build-your-brand-as-a-creative/ | 200 | да | — |
| 21 | [36] | https://jobcannon.io/blog/major-arcana-personality-archetypes | 200 | да | ⚠ снят |
| 22 | [38] | https://www.carolspearson.com/post/new-article-the-roots-of-the-pearson-marr-archetypes | 200 | да (Таро нет) | — |
| 23 | [41] | https://thebrandarchetypes.com/history/ | 200 | да | — |
| 24 | [43] | https://psytests.org/typo/heropm.html | не открывалась | — | Удалена по правилу |
| 25 | [44] | https://redwheelweiser.com/book/archetypal-tarot-9781578637485/ | 200 | да | — |
| 26 | [45] | https://marykgreer.com/2011/08/17/who-are-you-in-the-tarot/ | 200 | да | — |
| 27 | [46] | https://www.aeclectic.net/tarot/books/handbook-arrien/ | 200 | да (кроме «portraitures») | ⚠ сужен |
| 28 | [49] | https://eksmo.ru/book/matritsa-sudby-pervoistochnik-ITD1409842/ | 200 | да | — |
| 29 | [50] | https://matrica-sudby.ru/ | 200 | да | — |
| 30 | [60] | https://vikna.tv/ru/dlia-tebe/matrytsa-sudby-chto-eto-y-kak-y-o-chem-mozhno-uznat/ | 200 | да | «с 2006 года», Ладини |
| 31 | [61] | https://tsdr.uspto.gov/statusview/sn79443153 (и sn79438028, ROM.1900910, ROM.1888975) | 200 | да | — |
| 32 | [65] | https://www.worldnumerology.com/numerology-life-path/ | 200 | да | — |
| 33 | [66] | https://peacefulwarrior.com/the-life-you-were-born-to-live/ | 200 | да | — |
| 34 | [70] | https://www.womenofgrace.com:8443/blog/?p=707 | сброс соединения | недоступно | Помечено |
| 35 | [73] | https://jobcannon.io/assessments/numerology/about | 200 | да | — |
| 36 | [76] | https://www.goodreads.com/book/show/5217699-enigma-of-numbers | 200 | да | — |
| 37 | [82] | https://en.wikipedia.org/wiki/Dreamspell | 200 | да | — |
| 38 | [86] | https://zhanatglobal.com/filosofiya-syucai | 200 | да | — |
| 39 | [87] | https://www.trotta.es/static/pdf/JUNG_Sobre_astrologia_Avance_de_lectura.pdf | 200, PDF | да | — |
| 40 | [92] | https://repository.essex.ac.uk/41591/1/J%20Analytical%20Psychology%20-%202025%20-%20Zeng%20-%20Synchronicity%20in%20Post%E2%80%90Jungian%20Astrology%20A%20Cosmological%20Quest.pdf | 200, PDF | да | Том CW 18 для §1175 уточнён |
| 41 | [93] | https://jungianalchemist.substack.com/p/carl-jungs-curious-experiment-to | 200 | да; текст исправлен (три партии) | — |
| 42 | [95] | https://astrology-and-science.com/D-psia2.htm | 200 | да; EPQ → EPI | — |
| 43 | [100] | https://www.archai.org/wp-content/uploads/2016/04/Tarnas-%E2%80%93-The-Ideal-and-the-Real-%E2%80%93-Archai-Issue-1.pdf | 200, PDF | да | — |
| 44 | [101] | https://cosmosandpsyche.com/ | 200 | да | — |
| 45 | [104] | https://uraniatrust.org/celebrated-astrologers/liz-greene | 502 | недоступно | Помечено |
| 46 | [109] | https://openlibrary.org/works/OL1670943W | 200 (JSON) | да | — |
| 47 | [111] | https://proza.ru/2019/08/17/1375 | 200 | да | Описание источника исправлено |
| 48 | [112] | https://myastrology.com/article/astrological-signs-and-their-legendary-archetypes/ | 200 | да | — |
| 49 | [113] | https://mysticryst.com/blogs/the-mystic-journal/the-12-zodiac-signs-as-jungian-archetypes-your-birth-chart-as-psyche-map | 200 | да | — |
| 50 | [118] | https://myss.com/free-resources/sacred-contracts-and-your-archetypes/the-archetypal-wheel/ (и …/casting-your-chart-of-origin/) | 200 | да | — |
| 51 | [122] | https://jovianarchive.com/pages/incarnation-crosses-in-human-design | 200 | да | — |
| 52 | [131] | https://genekeys.com/how-to-read-your-profile/ | 200 | да | — |
| 53 | [136] | https://www.abebooks.com/9789675395598/BaZi-Profiling-Box-Set-Yap-9675395591/plp | 200 | да | — |
| 54 | [155] | https://nlsinfo.org/bibliography/search/author=Hartmann%2C+Peter | 404 | недоступно | Помечено; данные Crossref о статье подтверждены |
| 55 | [156] | https://europepmc.org/article/MED/18649494 | `curl` 403; REST API — да | да | — |

Также по содержанию открыты [6] Tarot card reading, [83] José Argüelles, [96] Synchronicity, [97] Psychological astrology, [98] Cosmos and Psyche, [121] Human Design, [126] JobCannon HD, [145] Socionics, [147] John Beebe, [151] Astrology and science, [152] Shawn Carlson, [158] Barnum effect, [159] Mars effect и Skeptic UK, [161] Jungian archetypes, [114] Sorsby, [117] Myss (фрагмент e-bookshelf), [123] Jovian Terms, [135] Gene Keys Terms (все — 200).

---

## 5. Сводка

- **Проверено утверждений:** 136 строк таблицы раздела 2 (04 — 69, 06 — 67). Многие строки объединяют несколько фактов (например, 39 записей TSDR по номерам регистрации сведены в пп. 36–46). Всего сверено около 250 отдельных фактов: цифр, дат, номеров, цитат.
  - Подтверждено — 105 строк; в некоторых из них по итогам проверки снят ⚠.
  - Подтверждено, но ⚠ на непроверяемую часть сохранён — 4.
  - Исправлено или уточнено — 25: 18 исправлений и 7 уточнений формулировки или атрибуции.
  - Помечено ⚠ — 1 строка; ещё 5 пометок «ссылка недоступна» поставлены на битые URL в 06.
  - Удалено — 1 (ссылка psytests.org в 06 [43]).
  - Всего ⚠ снят в 8 местах, сужен в 3.
- **Проверено URL:** все 399 URL обоих списков — на доступность; 104 — по содержанию (04 — 49, 06 — 55), с поправкой на дубли; ещё около 45 открыты как дополнительные.

### Самые важные исправления
1. **06, главное требование — собственные связки.** В таблице «брендовый архетип → аркан» (§2.2) роли Nicole Lau были разнесены по архетипам Марк и Пирсон исследователем, а «Император — Правитель у 3 из 3» подавалось как совпадение авторов. Добавлено пояснение, исправлены «Коротко» и сводная таблица. Других собственных связок, выданных за найденные, не обнаружено.
2. **06, удалена ссылка на psytests.org** со страницей с пунктами теста ([43]).
3. **04, товарные знаки.** HERO'S JOURNEY № 4424264 сейчас принадлежит Joseph Campbell Foundation (уступка учтена 26.07.2023), а не Hole in the Wall Gang Fund. Утверждение о «сосуществовании» неверно. Дополнены номер ARCHETYPE ME (№ 4503286) и статус SACRED MONEY ARCHETYPES (продлён 19.07.2023). Остальные 60+ номеров и статусов USPTO и Madrid Monitor подтвердились.
4. **Эффект Форера (оба файла).** Расхождение 4,30 и 4,2 разрешено: средняя 4,26, остальное — округления. В 06 также исправлена «газетная» книга: на самом деле книга из газетного киоска.
5. **06, эмпирика.** Тест на интуицию у Dean & Kelly проводился по EPI, а не по EPQ. «Дин показал» исправлено на «Дин предположил»: исчезновение эффекта Марса после 1950 г. нашёл сам Гоклен. Партии эксперимента Юнга: 180 + 220 + третья = 483 (в файле стояло «180, затем 220, всего 483»).
6. **06, Юнг о Таро.** В цитате *Visions* (с. 923) архетипическими идеями названо и колесо фортуны — добавлено в таблицу A. Письмо 1930 г. и *Letters* I, с. 77 — по-видимому, одно письмо. Страница 538 письма Cornell теперь атрибутирована источнику [2]. Ссылка Zeng & Fraikin на §1175 ведёт в CW 18.
7. **04, ИИ и контент-анализ.** α = 0,12 у Paekivi & Karjus относится к блоку Hall / Blumler–Katz / Polti, а не к «архетипическим переменным» вообще; формулировки в трёх местах уточнены. Стандарт Lombard смягчён до «0,80 и выше приемлемо в большинстве ситуаций».
8. **04, прочее.** Цитата ст. 1479 ГК РФ восстановлена до конца («…Российской Федерации»). Страницы Neher (1996) — 61–91 по Crossref. Ramotion Archetype Finder — не квиз, а «колесо» с каталогом брендов.

### Что осталось под ⚠
- **04:**
  - McPeek (2008): аннотация и цифры ≈0,72 / ≈0,68 — ResearchGate недоступен;
  - рецензия Buros — платная, не получена;
  - оригинал Forer (1949) — легальной открытой копии нет;
  - номер ARCHETYPEME.COM;
  - российский реестр (ФИПС, Роспатент — недоступны);
  - флорентийское решение — только пересказ Википедии;
  - документ об уступке знаков PMAI (запись об обновлении от 08.03.2023 в TSDR есть, сам документ не читался);
  - Westergaard: цифра 55 000 на странице не найдена;
  - Duarte и др. (2026) и Haddad и др. (2015) — репозиторий за антибот-защитой;
  - карточки ResearchGate и ScienceDirect, где ⚠ уже стоял.
- **06:**
  - страница *Letters* I для письма 1930 г.;
  - год и тема лекции Бернулли;
  - номер параграфа CW 15;
  - атрибуции конспекта OLLI по книгам;
  - формулировка Арриен «portraitures and archetypes»;
  - год 2006 по книге Ладини;
  - размеры выборок у Hartmann и др. (2006) — аннотация скрыта;
  - CSICOP: 55 из 408;
  - отчёт Pew 2025;
  - b17.ru (страница недоступна);
  - Wang: Анима, Тень, Самость;
  - пять ссылок, помеченных «⚠ ссылка недоступна на 2026-10-16»: [18], [30], [70], [104], [155].
- **Замечание о первоисточнике Aaker (1997):** в тексте статьи — 92% объяснённой дисперсии, а сумма по табл. 2 — 89,8%. Это расхождение внутри самой статьи; файл верно цитирует текст.
