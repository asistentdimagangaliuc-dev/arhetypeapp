# v13 — независимая проверка раунда 2: карточки вне модели и оглавление

> **Дата:** 2026-10-16. **Объект:** `02-cards/extra-*.md` (12 файлов) и `02-cards/README.md` — всё, что добавлено и изменено в раунде доукомплектования (`git diff 6ca98c6 HEAD`; протоколы доукомплектования — `_notes/c01-extra-jung.md`, `_notes/c02-extra-myss-vogler.md`).
> **Проверяющий** не участвовал ни в сборе, ни в написании, ни в доукомплектовании. Это исследование, без проектирования продукта.
> **Правки:** только в `extra-*.md`, `02-cards/README.md` и в этом протоколе; минимальные; новые источники — в конец списков. Git-коммитов проверяющий не делал. Координатор по ходу работы сделал служебный коммит-«checkpoint» `59c3f12`, в который попала часть правок этого протокола; состояние до проверки — коммит `fbc954c`.

## 1. Методика

1. **Чтение.** Все 12 карточек и README прочитаны целиком, затем просмотрен diff `6ca98c6..HEAD` и оба протокола доукомплектования.
2. **Скрипты** (во временном каталоге сессии, не в репозитории):
   - сплошная нумерация `[n]`: номера источников 1…N без пропусков, нет висячих ссылок, нет неиспользованных источников;
   - длина цитат в «…», "…", “…” (порог проверки — 22 слова, правило — до 25);
   - относительные ссылки README и карточек;
   - grep на пиратские домены (ebin.pub, z-lib, libgen, pdfdrive, pdfcoffee, studylib, psytests.org, archive.org/details|download, dokumen.pub, alexeykrol);
   - grep на связки с Таро без ссылки на `06-esoteric-links.md`;
   - grep добавленных строк на рекомендации по проектированию продукта;
   - подсчёт ⚠ по файлам (базовый коммит `6ca98c6`, состояние после доукомплектования `fbc954c`, после проверки).
3. **Веб.** WebSearch не использовался. Только прямые адреса:
   - WebFetch;
   - curl к страницам издателей, журналов, Википедии (`action=raw`), API Crossref;
   - полнотекстовый поиск Open Library (`openlibrary.org/search/inside`). Через curl он в этот день обрывал соединения (`ws_closed_mid_exchange`), поэтому запросы шли через WebFetch. Это поиск по библиотечным экземплярам с выдачей по записи; открывались только сниппеты, сами экземпляры — нет.
   Страницы выдачи поисковиков не запрашивались. Личные данные в запросы не включались: в запросах были только публичные имена, названия и цитаты.
4. **Легальность.** Пиратские копии не открывались и не цитировались. Загруженные пользователями копии на archive.org не открывались. PDF тезисов «Ломоносов-2025» содержит e-mail автора; в карточки и в этот протокол он не переносился.
5. **Правовые статусы.** Проверены:
   - статьи ру-Википедии (wikitext, поиск по словам «иноагент», «иностранный агент», «санкц», «розыск», «уголовн», «въезд», «дискредит», «штраф», «Миротворец» и т. п.);
   - список «иностранных агентов» ру-Википедии — статья «Список «иностранных агентов» (Россия)», последние записи 08.2026;
   - официальный реестр Минюста. Страница `minjust.gov.ru/ru/pages/reestr-inostryannykh-agentov/` открылась (HTTP 200), но реестр подгружается скриптом с `reestrs.minjust.gov.ru`, а соединение с ним обрывается. Поэтому сверка с официальным реестром не выполнена, и во всех правовых примечаниях оставлена пометка о юридической проверке.

## 2. Проверка правил (скрипты)

| Правило | Результат | Комментарий |
|---|---|---|
| Структура 1–15 + «Источники» | 12/12 карточек | заголовки на месте и в нужном порядке |
| Нумерация `[n]` сплошная, нет висячих и неиспользованных | 13/13 файлов | единственное «висячее» `[246]` в persona [17] — это номер параграфа на полях CW 7 внутри цитаты сниппета, а не ссылка; оставлено как есть |
| Цитаты ≤ 25 слов | нарушений нет | ни одна цитата не длиннее 22 слов |
| Ссылки на неавторизованные копии | нет | alexeykrol.com упомянут без ссылки, как удалённый (guide-mentor [11]) |
| Относительные ссылки | все рабочие | ссылка README → `v13-extra-cards.md` появилась вместе с этим протоколом |
| Таро только со ссылкой на `06-esoteric-links.md` | **исправлено** | в разделах 6 и 10 карточек shadow, self, great-mother, в разделе 6 anima и trickster упоминания Таро были без ссылки; добавлено «подробно — 06-esoteric-links.md» (8 мест) |
| Нет рекомендаций по проектированию продукта | нарушений нет | найдены только описательные оговорки («нельзя переносить без оговорки») и прямая формулировка «Это анализ медийных образов, а не рекомендации» |
| README описывает структуру из 15 разделов | да, **исправлено устаревшее** | фраза «юнговские карточки доводятся параллельно… может оставаться прежний шаблон (разделы 1–7)» заменена: все 12 карточек доведены (c01 и c02); у блока Юнга добавлено «— разделы 1–15»; в шапку добавлена ссылка на этот протокол |

## 3. Утверждения: что проверено

Вердикты: **подтверждено**; **исправлено** — утверждение было неточным или неверным, в карточке исправлено; **частично** — суть верна, но формулировка или деталь уточнены; **не проверено** — источник в этот день недоступен.

| Файл | Утверждение | Чем проверено | Вердикт | Комментарий |
|---|---|---|---|---|
| shadow | Марк и Пирсон: подраздел «Destruction, Metamorphosis, and the Shadow», «Outlaw brands love to be identified with things that are bad for you» | OL search inside, экземпляр herooutlawbuildi0000mark | подтверждено | сниппет: «Destruction, Metamorphosis, and the Shadow Outlaw brands love to be identified…» |
| shadow | Hard Candy, «vampish makeup», с. 131 | OL: «Hard Candy Lipstick ads, picturing a very young girl with vampish…» и указатель «Hard Candy Lipstick ads, 131» | подтверждено | |
| shadow | §469 по Генеральному указателю CW | OL: «carnival(s)… customs, 9i 469» (generalindextoco00forr) | подтверждено | |
| shadow | Хартвелл, Cadillac «Poolside», Олимпиада 2014, Rogue, пародия Ford «Upside»; «the shadow triggers universal fears»; «valuable tools for endogenous growth and learning»; тени Explorer / Visionary / Guardian | WebFetch archetypesinbranding.com (22.09.2016, обн. 30.12.2020) | подтверждено | |
| shadow | Хартвелл, Carl's Jr. (2015, 72 and Sunny), «an appeal to power, a manipulation for selfish reasons», «demographic bait» | WebFetch + curl поста от 15.09.2016 | подтверждено | |
| shadow | «CEO Carl's Jr. связывал с кампанией рост продаж» | тот же пост | **исправлено** | CEO говорит только о росте продаж в 2014 г.; связь с кампанией делает Хартвелл («it is working») |
| shadow | Базикян 2013: Domestos «Millions of germs will die», «green, ugly, wild»; Garnier; Avon Anew; реклама «прячет» тень за «sweet image of a miraculous substance» | WebFetch cyberleninka (статья на англ.) | подтверждено | |
| shadow | Базикян: двойник, слуга, оборотень, колдун | то же | подтверждено | «in the form of a twin… a servant, a "lower" man, a werewolf, a sorcerer» |
| shadow | «агрессивные рекламные слоганы как теневую образность в политике» | то же | **исправлено** | в статье «militant political appeals, aggressive advertising slogans» стоят рядом; переписано как «в один ряд с воинственными политическими призывами» |
| shadow | Thompson, Rindfleisch, Arsel 2006: определение doppelgänger brand image, Starbucks, подрыв аутентичности | experts.illinois.edu (аннотация); Crossref DOI 10.1509/jmkg.70.1.050.qxd | подтверждено | страница Illinois показывает чужой DOI (10.1016/j.jneb…) — ошибка самой страницы; DOI в карточке верный (Crossref) |
| shadow | NYT / Boston.com: >1 млн экз., ~700 тыс. через TikTok Shop, «shadow self» Юнга, «не заменяет терапию», сомнения экспертов | WebFetch boston.com (A. Alter, 31.05.2024) | подтверждено | переиздание — импринт Simon & Schuster (Primero Sueño Press / Atria); по-русски «Simon & Schuster» допустимо |
| shadow | Цвейг — «retired Jungian therapist», три книги о тени, Substack | WebFetch soundstrue.com | подтверждено | страна не указана — как и в карточке |
| shadow | Academy of Ideas: статья 17.12.2015, «relegated to the darkness…», Джекил и Хайд; 3,79 млн подписчиков | curl и WebFetch — HTTP 403 / пусто; YouTube без JS числа не отдаёт | не проверено | оставлено как есть (оценка исследования) |
| shadow | Singer: «Nigredo; Shadow» рядом с «Black holes; Chaos; Moon; Night» | OL, Singer, *Androgyny* (1976) | подтверждено | |
| shadow | «Durand G., Spring 1981»: «nigredo, shadow as only black» | OL: фраза есть в *Spring… 1980* (ред. Hillman, Severson) и в выпуске «Spring» 1983; автор эссе в сниппетах не назван; продолжение «the shadows in whiteness (the blues we dwelled on in the companion…» | **исправлено** | атрибуция Дюрану не подтверждается. Текст карточки и [34] переписаны: «автор статьи в «Spring» 1980» ⚠; вероятный автор — Хиллман (оценка исследования) |
| shadow | Хартвелл: Visionary → Творец, Guardian → Заботливый, Provocateur → Шут | WebFetch SlideShare, слайды 22.08.2014 | подтверждено | в c01 ссылались на заметку r17; добавлен источник [35] |
| shadow | Friebe 2026: «public masks», Nike / Apple / Dove, persona и shadow | WebFetch articlegateway.com; Crossref | подтверждено | |
| persona | CW 7 §245 и §246 (Waddell) | OL: «(CW 7, para. 245)», «(CW 7, para. 246)» в *Mis/takes* | подтверждено | |
| persona | CW 7 §307 (Forsyth) | OL: «…artificial personality without punishment" (CW, 7:307)» | подтверждено | |
| persona | CW 6 §801 (Stein) | OL: «Jung. Coll. Wks., Vol. 6, par. 801» | подтверждено | также Шарп: «functional complex… [Ibid., par. 801]» |
| persona | CW 7 §305 («demands of propriety…»), §318, §269; CW 6 §804; цитаты Шарпа («Money, respect and power…», «trap and a source of neurosis», «assume and drop», «protective covering and an asset») | curl словаря Шарпа (psychceu.com) | подтверждено | номера параграфов у Шарпа совпадают с карточкой |
| persona | Barbour и соавт.: «persona is a mask and derived from performance and acting»; «Goffman's dramaturgical analogy allows us to consider persona as an everyday performance» | curl M/C Journal 17(3) | подтверждено | вторая цитата — подстрока («The resurgence in interest in Goffman's…») |
| persona | «persona studies прямо выводят понятие из Юнга и Гофмана» | то же | **исправлено** | у авторов «levels of deference to writers such as Jung, Goffman, Butler, and Foucault» → «опираются в том числе на Юнга и Гофмана (наряду с Батлер и Фуко)» |
| persona | Marwick, boyd: imagined audience, context collapse, «strategic self-commodification» | аннотация Crossref | подтверждено | |
| persona | Abidin: «calibrated amateurism» — сконструированная «сырость» | аннотация Crossref | подтверждено | |
| persona | Hogan: «выставки», которыми «человек управляет как куратор» | аннотация Crossref | **исправлено** | у Хогана «virtual "curator"» — механизм платформы, а не человек; уточнена и фраза о Гофмане: Хоган дополняет модель «выставочным» подходом |
| persona | Fortune 2023: Херман стоит за «Black Mamba»; Бейонсе — «thing that takes over»; альбом «I Am… Sasha Fierce» | WebFetch fortune.com (C. Taylor, 30.09.2023) | подтверждено | |
| persona | Afford Anything эп. 184 открывается через curl (HTTP 200) | curl и WebFetch | **не подтвердилось** | 2026-10-16 — 403 и для curl; в [4] добавлено примечание; факт о Хермане и Бейонсе дублируется по [20] |
| persona | HubSpot: «sassy owl Duo», «aims to entertain more than it aims to sell», «big green mascot», TikTok с начала 2021, ~7 млн подписчиков, обн. 20.07.2023, L. Alfred | curl blog.hubspot.com | подтверждено | |
| persona | Wendy's: «sassy» персона, «roast»-ответы с 2017 г. | LibreTexts (curl), HubSpot | **исправлено** | 2017 г. нет ни в одном из двух источников; «sassy» в HubSpot относится к Duo и к твитам других компаний. Заменено на «witty, humorous, and often sarcastic» (LibreTexts) и «год в источниках не указан» |
| persona | vc.ru 10.10.2017: «Алиса» — около 320 сценариев, «не терпит унизительного обращения» | WebFetch vc.ru/26878 | частично | В. Гуриев в статье не «редактор характера»: он участвовал в описании характера и подборе реплик. Формулировка уточнена |
| persona | Sostav 05.11.2020: «Салют», Leo Burnett Moscow, характеры Сбера, Афины, Джой | WebFetch sostav.ru | подтверждено | |
| persona | Audrezet и соавт. 2025: Lil Miquela — 7,6 млн, Brud, Calvin Klein / Samsung / BMW, «digital personas» | curl PDF ueaeprints | подтверждено | |
| persona | Колберт: «fictionalized persona», «well-intentioned, poorly informed high-status idiot», отказ от персонажа в 2015 | wikitext en-wiki | подтверждено | |
| persona, trickster | Конвалюк 2018: Верка Сердючка — трикстер; превращения, смена облика и языка; черты трикстера по Липовецкому | WebFetch rspublisher.org; Crossref | подтверждено | точное название — «Вєрка Сердючка – трікстер…»; в [35] / [27] и в цитате таблицы исправлена русифицированная орфография |
| persona | «Конвалюк отделяет персонажа от исполнителя» | аннотация | частично | в аннотации исполнитель назван в скобках, анализ — о персонаже; формулировка смягчена |
| persona | BadComedian: 6,03 млн (23.06.2026), «главный кинокритик российского YouTube» (прозвище в СМИ), EvgenComedian до 2016 | wikitext ru-wiki | подтверждено | |
| persona | Пучков: псевдоним «старший оперуполномоченный Goblin», «Тупичок Гоблина», >3 млн (27.07.2022), санкции ЕС 16.12.2022 | wikitext ru-wiki | подтверждено | добавлены санкции Швейцарии (21.12.2022) и Украины (15.01.2023) по той же статье |
| anima | CW 7 §§296–340 (Steinberg) | OL: «C. G. Jung, cw 7, pars. 296—340» | подтверждено | то же у Хардинг и в самом CW 7 («See below, pars. 296–340») |
| anima | Hillman: «there is no anima in women» | OL, *Anima* (1985) | подтверждено | |
| anima | McLeod 1981: «celebrities representing animus projection, those godlike creatures…» | OL по фразе «godlike creatures in whom» | подтверждено | |
| anima | Эмма Юнг: «animus appears either as a plurality of men» | OL, *Animus and Anima* (изд. 1957) | подтверждено | в [20] указано изд. 1985; фраза есть и в изд. 1957 |
| anima, great-mother | Рандаццо 1993: «The Virgin or Harlot», «eternal nurturer and provider», «John Wayne myth is based on the Warrior archetype» | OL, *Mythmaking on Madison Avenue* / *The Mythmakers* | подтверждено | |
| self | Aion §9 | OL: «(CW9-II, par. 9)» в *Jungian psychology in perspective* (1985) | подтверждено | сниппет из «The Quotable Jung» в первых 20 результатах не показался; номер подтверждён по другой работе |
| self | CW 12 §44 | OL: «(CW 12, para. 44)» у Waddell, в *Living with Paradox* и др. | подтверждено | |
| self | Пирсон: «aggregate Self score» = Ruler + Magician + Sage + Fool | OL, *Awakening the Heroes Within* | подтверждено | |
| self | Hall & Nordby: «the self is our life's goal…» | OL | подтверждено | |
| self | цитаты Шарпа: CW 8 §430, CW 12 §563, CW 9ii §44, CW 6 §790, CW 6 §758, CW 8 §432, CW 7 §377, §389 | словарь Шарпа (curl) | подтверждено | |
| trickster | Мур и Жиллетт: «The Know-It-All Trickster — The bipolar Shadow of the Precocious Child», «The Dummy», «has no heroes» | OL, kingwarriormagic0000moor | подтверждено | |
| trickster | Nichols 1980: «The Magician: Creator and Trickster», с. 45 | OL, jungtarotarchety00nichrich | подтверждено | |
| trickster | Хайд: «consummate boundary-crossers», «satisfy their inordinate appetites, lying, cheating, and stealing», «indispensable heroes of culture», Койот | WebFetch lewishyde.com/?p=20 | подтверждено | |
| trickster | Томас 2024 (Transform, 06.08.2024): Tango, Loaded, Andrex, Weetabix, McDonald's, «provocative levity», «archetypal rebel warrior», Гермес / Локи / Пак / Феррис Бьюлер / «Маска» / Дэдпул, исключение провокаторов, «rarely set out to cause harm» | WebFetch transformmagazine.net | подтверждено | |
| trickster | Липовецкий, НЛО 2009: список советских трикстеров, «Амбивалентность и функция медиатора составляют ядро…», девять памятников Бендеру, расхождение с Юнгом | curl PDF nlobooks.ru, pdftotext | подтверждено | |
| trickster | Lipovetsky 2024 (SEEJ 68(4): 481–500): «gallery of trickster characters», «cynical consensus», «articulate and subvert…», 2014–2022 | curl seej.org | подтверждено | |
| trickster | «после 2022 г. трикстерные персонажи уходят» | аннотация SEEJ | частично | в оригинале «symptomatic waning» → «сходят на нет («waning»)» |
| trickster | Kononenko, Kukharenko 2008: «traditional and archetypical trickster figure», «master of contradictions», раскол аудитории, «feel exploited», «cannot reassume trickster (dis)guise» | curl cambridge.org (аннотация); Crossref | подтверждено | |
| trickster | семейство Шута у Хартвелл: Clown, Entertainer, Provocateur, Shapeshifter | WebFetch SlideShare | подтверждено | ⚠ из раунда c01 снят |
| trickster | The Yes Men: «identity correction», «lies can expose truth», фильмы 2003 / 2009 / 2014, Сервен и Вамос | wikitext en-wiki | подтверждено | |
| trickster | ВТБ 24: «1 января 2018 г. присоединён… (указана и дата 9 января)» | wikitext ru-wiki | частично | в статье «существовавший до января 2018 года», новость ВТБ в сносках датирована 09.01.2018; формулировка уточнена |
| great-mother | Нойманн: «elementary character of the Feminine», «The dynamic element of the transformative character», «woman = body = vessel = world», «Schema II: vessel symbolism» | OL (изд. 1955–2015) | подтверждено | |
| great-mother | Базикян: Сбербанк, «Росгосстрах», J&J, «Семья»; «philosophy of public concern»; компенсация нехватки заботы покупками; «Mother is the opposite of Self» | WebFetch cyberleninka | подтверждено | |
| great-mother | Putnam: Mother or Father, Monk or Nun / Mother Earth, Newman's Own | curl kayeputnam.com/caregiver | подтверждено | |
| great-mother | Тутта Ларсен: TUTTA.TV (05.2015), «Семья на ура!» (05.2021), «Мать и дитя» | wikitext ru-wiki | подтверждено | в Википедии часть фактов без источников — карточка это оговаривает |
| great-mother | Петрановская: книги 2014 / 2014 / 2017, Институт развития семейного устройства (2012), дело о «дискредитации армии» (24.10.2023) | wikitext ru-wiki | подтверждено | |
| great-mother | «Росгосстрах» на 2026 г. в группе ВТБ | wikitext ru-wiki | частично | дополнено: ВТБ с 2024 г. ищет покупателя, на конец 2025 г. сделка не завершена |
| myss-child | 12 домов колеса: подтверждены 9, дома 4, 5, 12 под ⚠ | OL: «FOURTH HOUSE: HOME (First and fourth chakras)», «FIFTH HOUSE: CREATIVITY AND GOOD FORTUNE (Sixth chakra)» (с. 216), «TWELFTH HOUSE: THE UNCONSCIOUS (Sixth and seventh chakras)» | **исправлено** | названы все 12 домов; ⚠ снят; [22] дополнен |
| myss-child | Мур и Жиллетт: «High Chair Tyrant and the Weakling Prince» | OL | подтверждено | |
| myss-child | колода: Penguin NZ 72 + 6; АСТ 80 = 74 + 6 (две колоды, пер. Кобляковой) | curl penguin.co.nz; ast.ru (обе страницы) | подтверждено | |
| myss-child | видеосеминар «The Wounded Child» (19.04.2023): «woundology», «has authority» | curl myss.com | подтверждено | |
| myss-child | Галерея: Анна Франк, Тайни Тим, роли Деппа, Франциск Ассизский, Пражский младенец, Гарпократ, «weekly allowance», «shadow families», «genius is childhood recaptured» и др. | pdftotext Gallery-of-Archetypes.pdf | подтверждено | проверено около 40 фраз из четырёх карточек Мисс |
| myss-child | Стив Ирвин: «первого крокодила поймал в девять лет» | wikitext en-wiki | **исправлено** | в статье «began handling crocodiles at the age of nine» |
| myss-child | Дроздов: «профессор МГУ (1967–2023)» | wikitext ru-wiki | **исправлено** | работал в МГУ в 1967–2023 гг., профессор с 2000 г. |
| victim | «Guardian of Self-esteem» есть только у Одена (2016), в книге Мисс 2001 г. не находится | OL: «The Victim: Guardian of Self-Esteem Being a Victim is a common fear» — *Sacred Contracts* 2001, экземпляр sacredcontractsa0000myss | **исправлено (существенно)** | подзаголовок есть в самой книге Мисс; нет только в онлайн-Галерее 2015 г. Исправлены разделы 1, 15 и источники [11], [12] |
| victim | видеосеминар «The Victim» (01.02.2023): «negative reaction», «go into neutral», «all about self-esteem», «forces on the outside world» | curl myss.com | подтверждено | |
| victim | «Freddie's Victim fell into the sixth house…» | OL | подтверждено | |
| victim | Галерея: «primary objective… self-esteem and personal power», «intuitive voice of your inner Victim», «castle», «perverse advantage», роли Суонк / Фостер / Стрип | pdftotext Галереи | подтверждено | |
| saboteur | «Saboteur archetype in her third house» | OL | подтверждено | |
| saboteur | подзаголовок «Guardian of Choice» только у вторичных пересказов | OL: «The Saboteur: Guardian of Choice Like the Prostitute and the Victim» — *Sacred Contracts* 2001 | частично | подзаголовок есть и в книге; дополнены раздел 3 и [14] |
| saboteur | видеосеминар «The Saboteur» (07.02.2023), Publishers Weekly («thief to catch a thief») | curl myss.com, publishersweekly.com | подтверждено | |
| prostitute | «Prostitute in my tenth house (highest potential)…» | OL | подтверждено | ⚠ «кто говорит» оставлен обоснованно: в сниппете не видно |
| prostitute | Витолс 2011 («make a living», «not a light one»), Маккафри 2014 («downward spiral», «conduit…») | curl goodreads | подтверждено | |
| prostitute | Галерея: «guardian of faith», «Not for sale», «impervious to selling out», Наёмник, Трикстер «can be a great ally» | pdftotext | подтверждено | |
| guide-mentor | StoryBrand: «Principle Three…», «positioned himself as the guide…», «more like Q in the James Bond movies», «Empathetic statements start with words like…», «Nobody likes a know-it-all and nobody wants to be preached at» | OL, *Building a StoryBrand* (2017) | подтверждено | |
| guide-mentor | русский перевод: «Apple играет роль, больше похожую на роль Q…» | curl books.yandex.ru | подтверждено | |
| guide-mentor | storybrand.com: отзывы (60% у Портерфилд), логотипы Chick-fil-A, Nextiva, TOMS, Keller Williams, Tempur Sealy, Microsoft; TREK / TOMS / The Economist на странице книги | curl; логотипы — по именам файлов (cfa, next-bw, kw, toms, tempur, microsoft) | подтверждено | |
| guide-mentor | дата «Building a StoryBrand 2.0» — 07.01.2025 | Business Wire — HTTP 403; метаданные страницы книги на storybrand.com — «datePublished 2025-01-07» | частично | ⚠ снят обоснованно лишь косвенно; в [27] добавлено примечание |
| guide-mentor | Мисс: Mentor («implicit trust», тень — «overbearing attitude», «inability to allow the student…»), Guide («guru, spiritual master», тень — гуру ради «financial gain»), Оби-Ван (Гиннесс → Хэмилл), Кришна для Арджуны, Хирон | pdftotext Галереи | подтверждено | |
| guide-mentor | Sanders & van Krieken 2018: 20 историй, 8 брендов, Helper 16 (80%), Hero 4 (Innocent, WNF), Trickster 2 (Heineken); Pickwick «fulfills the archetypal role of the Helper»; Coca-Cola «The Gardener» | WebFetch PMC | подтверждено | Nike как Helper — только по сводной таблице; в карточке это оговорено |
| guide-mentor | Сассун (ESOMAR, 20.11.2008): «very important archetypes whose aid is crucial for all Heroes» | curl ana.esomar.org | подтверждено | |
| guide-mentor | подкаст Marketing Made Simple, эп. 5, 21.07.2021, «when you help your customers win, you win» | curl libsyn | подтверждено | |
| guide-mentor | Putnam: Teacher (Student, Mentor), «Who can you teach?»; Inner Guide (Priest, Mystic), «greater power»; Apple «Think Different» — Маг | curl kayeputnam.com | подтверждено | |
| guide-mentor | Портерфилд: «I get it, I've been there too», «$130 million», «over 100,000 students», «Six-figure female founders» | curl amyporterfield.com | подтверждено | |
| guide-mentor | Plenum: Kaspersky — Мудрец, «с долей менторства, но не назидающе»; Craftum: «Нетология» — Мудрец; Степанян: Т—Ж — Мудрец + Заботливый, «дружелюбным, ненавязчивым, исключает академическую сухость» | curl dsgners.ru, craftum.com, PDF confhub | подтверждено | |
| guide-mentor | Спиридонов «воспринимается как наставник» (SberBusiness.live) | curl sberbusiness.live | **исправлено** | цитаты в таком виде нет. В статье Мудреца «воспринимают как наставника и учителя», а Спиридонов назван представителем архетипа. Исправлены раздел 5 и строка таблицы |
| guide-mentor | Кожухов: «двадцать лет тревел-шоу (с 2002 г.)»; клуб с 2013 г.; книга АСТ 2017; «сталкерами в мир знаний», «с утра до вечера» | wikitext ru-wiki; curl mktravelclub.ru | частично | «двадцать лет» в статье нет → «ведущий тревел-программ с 2002 г.» с перечнем; остальное подтверждено |
| guide-mentor | Ильяхов: ректор Школы редакторов Бюро Горбунова, «Пиши, сокращай» (2016), «Текст по полочкам» (2022), «Главред» | wikitext ru-wiki | подтверждено | |
| vogler | MIT: p. 34 — «flexible character functions…», «masks, worn by the characters temporarily»; p. 36 — список из семи архетипов без Ally | curl stuff.mit.edu (текст рассылки) | подтверждено | номер страницы стоит перед цитатой |
| vogler | 2-е изд. 1998: «express the energy of the animus and anima», «usually not the main villains», «absorbed him into my adventure» | OL, *The Writer's Journey* (1998) | подтверждено | |
| vogler | Barker: «Caveat Scriptor!… a guideline. It's not a cookbook recipe», с. 265 | curl stuff.mit.edu | подтверждено | |
| vogler | подкаст Business of Story: «threshold guardians», «menacing, threatening», «as in martial arts», «worst enemy can be a kind of an ally», «wish fulfillment business», «unique identity», «hope and death of hope…», Swarovski, LEGO, издание к 25-летию | WebFetch businessofstory.com | подтверждено | дата эпизода на странице не указана — как и в карточке |
| vogler | Чанча 2023: Страж — «the one who stands in the way at important turning points» | curl convergencias.ipcb.pt | подтверждено | у Чанчи «Vogler identified seven archetypes» |
| vogler | Мисс: «Madonna is a master Shapeshifter», «Advertisers are Shapeshifters», «distorts the shape of truth», Карсон и Макмэн, «loyalty, tenacity, and unselfishness», «hanger-on», «smoking mirror»; видео «The Shapeshifter» (14.02.2023) — «survival assets» | pdftotext Галереи; curl myss.com | подтверждено | |
| vogler | Woolford: «Audrey (the Shapeshifter love interest)»; Voytilla: «Marion becomes a SHAPESHIFTER / THRESHOLD GUARDIAN» | OL | подтверждено | |
| vogler | Грей: «applicable for salespeople and copywriters», «Originally printed in 1998» | curl profitadvisors.com | подтверждено | |
| vogler | «1984»: «On January 24th, Apple Computer will introduce Macintosh», единственный общенациональный показ — 22.01.1984 | wikitext en-wiki | подтверждено | |
| vogler | Siri — «most helpful and trusted AI assistant»; «Алиса» — «Поддержу и развлеку», «Помогу понять, а не списать»; «Салют» — «Один ассистент — три характера» | curl apple.com, alice.yandex.ru, salute.sber.ru | подтверждено | |
| vogler | MKBHD: 20,9 млн (данные 03.05.2026), тест дисплея iPhone 6 (07.07.2014); Коуэлл — «blunt, critical»; Роджерс — 1968–2001, темы | wikitext en-wiki | подтверждено | |
| vogler | Левитан: «читал сообщения о начале войны 22.06.1941; объявлял о Победе 9.05.1945»; Гагарин 12.04.1961 | wikitext ru-wiki | **исправлено** | в статье нет, что он читал сообщение 22.06.1941 (там же сказано, что известные записи — послевоенные повторы), и нет даты 9.05. Заменено на «читал сводки Совинформбюро и приказы ВГК; ему было доверено объявить о взятии Берлина и о Победе»; Гагарин подтверждён |
| vogler | Wylsacom: платформы «YouTube, Rutube, Дзен, Telegram»; 11,5 млн (июнь 2026); распаковка MacBook Pro M4 до анонса | wikitext ru-wiki | частично | Rutube и Дзен в статье не упомянуты, Telegram — в другом контексте; оставлено «YouTube» |
| vogler | Леонтьева: «Спокойной ночи, малыши!», «Будильник», «От всей души» (1972–1987), «тётя Валя» | wikitext ru-wiki | подтверждено | |
| README | структура из 15 разделов и состав блоков | сверка с карточками | **исправлено** | см. раздел 2 |

**Итого по разделу 3:** 111 строк. Часть строк объединяет несколько фраз одного источника; всего сверено более 200 отдельных цитат и фактов. Вердикты по строкам:
- подтверждено — 87;
- исправлено — 13, из них существенно — 3: подзаголовок Жертвы, атрибуция «Durand», цитата о Спиридонове;
- частично (уточнена формулировка) — 9;
- не проверено или не подтвердилось — 2: Academy of Ideas; страница Afford Anything.

## 4. Обоснованные отказы от атрибуции

| Карточка | Отказ | Вердикт | Комментарий |
|---|---|---|---|
| Самость | бренды и блогеры | корректен | три довода: Самость «cannot be fully known»; нельзя проверить индивидуацию по контенту; ярлык «инфлированный» оценочный. Формулировка нейтральна |
| Анима / Анимус | блогеры; бренды — только Coca-Cola с пометкой «оценка исследования» | корректен | у McLeod — знаменитости как носители проекций, без имён; эксперты (Хиллман, Янг-Айзендрат, Вер) даны как авторы, а не как носители архетипа |
| Жертва | бренды и люди | корректен | ярлык оценочный, по Мисс архетип есть у каждого; вместо людей — роли и клиентские случаи из книги («Freddie») |
| Проститутка | бренды и люди | корректен | то же; разборы колеса из книги приведены без имён |
| Оборотень (Воглер) | людям и брендам | корректен | у Воглера роль связана с двуличием («two-faced»). Мадонна приведена как атрибуция самой Мисс, с оговоркой «это её трактовка»; формулировка нейтральна |
| Дитя (теневые варианты) | людям | корректен | реальные люди — только светлые варианты из Галереи и одна собственная «слабая» оценка (Дроздов) с оговоркой |
| Саботажник | людям, кроме самоописания Мисс | корректен | подтверждено по Publishers Weekly |

Оценочных или порочащих формулировок о реальных людях не найдено. Отнесения к архетипам помечены «оценка исследования, не из источника» и подкреплены тремя доводами. Правовые сведения изложены нейтрально, со ссылкой на источник. Упоминание «Миротворца» у Кожухова дано с оговоркой, что это негосударственный ресурс и правовым статусом он не является.

## 5. Правовые статусы русскоязычных персон

Сверка 2026-10-16:
- статьи ру-Википедии (wikitext);
- список «иностранных агентов» ру-Википедии (последние записи 08.2026);
- реестр Минюста — **не открылся** (см. раздел 1).

Во всех строках карточек оставлено «перед использованием нужна юридическая проверка».

| Персона | Карточка | Ру-Википедия: правовые сведения | Список «иноагентов» (Википедия) | Что изменено в карточке |
|---|---|---|---|---|
| Ирина Куликова | shadow | статьи нет (частный автор) | не значится | добавлено «не значится [36]» |
| Юлия Соловьева | shadow | статьи нет | не значится (в списке есть только однофамилица с другим именем) | добавлено |
| Алина Адт | shadow | статьи нет | не значится | добавлено |
| Андрей Данилко (Верка Сердючка) | persona, trickster | «В апреле 2022 года… запрещён въезд в Россию на 50 лет» (ссылка на woman.ru); ОАЭ — пожизненный запрет въезда (2024) | не значится | примечание дополнено Википедией и датой статьи «ВМ» (25.09.2025); в «ВМ» — оговорка «якобы» и слова РИА Новости «имеются основания для неразрешения въезда» |
| Дмитрий Пучков («Гоблин») | persona | санкции ЕС (16.12.2022), Швейцарии (21.12.2022), Украины (15.01.2023) | не значится | добавлены Швейцария и Украина |
| Евгений Баженов (BadComedian) | persona | правовых статусов нет | не значится | добавлено |
| Сергей Шнуров | trickster | правовых статусов нет; гражданский иск А. Вокс отклонён судом в 2021 г. (не статус; в карточку не вносилось) | не значится | добавлено |
| Тутта Ларсен | great-mother | правовых статусов нет | не значится | добавлено |
| Людмила Петрановская | great-mother | дело об административном правонарушении о «дискредитации армии» (24.10.2023) — уже было в карточке | не значится | добавлено |
| Максим Спиридонов | guide-mentor | статьи нет (одноимённая — о хоккеисте) | не значится | ⚠ оставлен: реестр не открылся |
| Михаил Кожухов | guide-mentor | российских статусов нет; «с января 2020 года внесён в базу украинского сайта «Миротворец»» | не значится | добавлено с оговоркой |
| Максим Ильяхов | guide-mentor | правовых статусов нет | не значится | добавлено |
| Валентин Петухов (Wylsacom) | vogler | правовых статусов нет | не значится | добавлено; ⚠ оставлен (реестр) |
| Юрий Левитан (1914–1983) | vogler | исторический пример | — | без правового примечания (как и было) |
| Валентина Леонтьева (1923–2007) | vogler | исторический пример | — | то же |
| Николай Дроздов | myss-child | статусов нет; одобрил присоединение Крыма (2014) — уже отражено как «политические высказывания 2014 г.» | не значится | добавлено |

Авторы источников проверены по тому же списку и в нём не значатся: И. Яппарова, О. Пилиповец, И. Булыгина, Е. Соколова, К. Гас, А. Шарлай, М. Леонова, Е. Исупова, Т. Рожкова, М. Степанян, Е. Карпова, А. Крячко, А. Богданов, Е. Спирица, В. Гуриев (в списке есть только однофамилец с другим именем). Они не примеры, а авторы источников, поэтому правовые примечания к ним в карточках не даются.

## 6. Снятые ⚠: выборочная проверка (32 случая)

| Файл | Было под ⚠ | Чем снято в c01/c02 | Проверка v13 | Вердикт |
|---|---|---|---|---|
| shadow | §469/470 неразличим (раздел 3) | Генеральный указатель CW | OL: «customs, 9i 469» | снятие корректно |
| shadow | то же, раздел 6 | то же | то же | корректно |
| shadow | то же, «Расхождения» | то же | то же | корректно |
| shadow | книга «Питера» не установлена | piter.com | curl обеих страниц piter.com: Спирица Е. В., ISBN 978-5-4461-1928-8 (2026, 224 с.) и 978-5-4461-1477-1 (2024, 192 с.); PDF оглавления — гл. 4 «Архетип Тени» | корректно |
| shadow | [19] название и автор | то же | то же | корректно |
| persona | CW 7 / CW 6 только по Шарпу (шапка) | Waddell, Forsyth, Stein, поля CW 7 | OL: 245, 246, 7:307, Vol. 6 par. 801 | корректно |
| persona | детали Хермана по вторичным (раздел 3) | Afford Anything + Fortune | Fortune подтверждён; Afford Anything — 403 | корректно по Fortune |
| persona | Бейонсе / Брайант в пересказах (раздел 6) | то же | Fortune | корректно |
| persona | [4] Afford Anything 403 | «curl — HTTP 200» | curl — 403 | **снятие не подтвердилось**; оставлено без ⚠, т. к. факт дублирован [20]; в [4] — примечание |
| anima | CW 7 §§296–340 | Steinberg, The Essential Jung | OL: Steinberg, Harding, CW 7 | корректно |
| anima | книга «Питера» | piter.com | PDF оглавления: гл. 5 «Архетип «Анима-Анимус»» | корректно |
| anima | критика Хиллмана и феминисток не изучена | сниппеты OL | OL: Hillman «no anima in women» | корректно (по сниппетам, как и оговорено) |
| self | ≈§9 (шапка) | The Quotable Jung | OL: «(CW9-II, par. 9)» в другой работе | корректно |
| self | ≈§9 (раздел 1) | то же | то же | корректно |
| self | ≈§9 ([1]) | то же | то же | корректно |
| self | «Возвращение = Self» — вывод r14 | AHW 1991 | OL: «aggregate Self score» | корректно |
| self | CW 12 только по Шарпу | Samuels | OL: «CW 12, para. 44» в нескольких работах | корректно |
| trickster | §469/470 | указатель CW | OL | корректно |
| trickster | Мур и Жиллетт по отзывам | сниппеты книги | OL: Know-It-All Trickster, Dummy | корректно |
| trickster | книга «Питера» | piter.com | PDF оглавления: гл. 10 «Архетип Трикстера» | корректно |
| trickster | [8] английский оригинал Nichols не сверен | OL | OL: «The Magician: Creator and Trickster… 45» | корректно |
| great-mother | elementary / transformative у Нойманна | оглавление OL | OL: «elementary character of the Feminine», «dynamic element of the transformative character» | корректно |
| great-mother | книга «Питера» | piter.com | PDF оглавления: гл. 22, 23 | корректно |
| myss-child | колода (80 / 72 + 6) | Penguin NZ, АСТ | curl penguin.co.nz, ast.ru | корректно |
| myss-child | Мур и Жиллетт «Tyrant / Weakling» | OL | OL: High Chair Tyrant, Weakling Prince | корректно |
| myss-child | АСТ HTTP 500 | страница открылась | curl — 200, 80 карт = 74 + 6, ISBN 978-5-17-165096-4 | корректно |
| victim | «хранитель самоуважения» не найден у Мисс | «найден у Одена; в книге 2001 г. нет» | OL: подзаголовок есть в книге 2001 г. | **снятие верно, обоснование неверно** — исправлено |
| victim | источник популярной формулировки не установлен | Оден | первоисточник — сама Мисс (2001) | исправлено |
| guide-mentor | год «2.0» | Business Wire по поисковой сводке | Business Wire — 403; метаданные storybrand.com — 2025-01-07 | снятие допустимо по косвенному подтверждению; примечание добавлено |
| vogler | гибкость ролей по сводкам | MIT p. 34 | curl MIT: p. 34 | корректно |
| vogler | применений в маркетинге нет | подкаст, Сандерс, Сассун, Чанча, Мисс, Грей | все шесть открыты и сверены | корректно |
| vogler | Оборотень ≈ Любовник/Маг (шапка и таблица) | сниппет 2-го изд. об animus и anima | OL: «express the energy of the animus and anima» | корректно (соотнесение помечено как оценка) |

**Итого:** 32 случая:
- снятие корректно — 28;
- в двух снятие верно, но обоснование было неверным (Жертва: подзаголовок и источник формулировки) — исправлено;
- в одном снятие не подтвердилось (Afford Anything): пометка не возвращена, так как факт дублирован, но добавлено примечание;
- одно снятие допустимо по косвенному подтверждению (дата «2.0»).

**⚠ этой проверки:**
- **снято 2** — дома 4, 5, 12 у Дитя (подтверждены); семейство Шута у Хартвелл (Трикстер; слайды открылись);
- **добавлено 2** — Тень, раздел 10 и [34]: автор фразы «shadow as only black» не установлен, атрибуция Дюрану не подтвердилась.

Итог по extra-карточкам: 63 → 63; README — 6 (без изменений).

## 7. URL

95 адресов, добавленных в раунде доукомплектования, проверены curl (HTTP-код).

| Код | Сколько | Комментарий |
|---|---|---|
| 200 | 82 | |
| 202 | 1 | e-space.mmu.ac.uk — заглушка; в карточке уже отмечено «⚠ по поисковой сводке, репозиторий отвечает HTTP 403» |
| 403 | 4 | academyofideas.com, affordanything.com, blinkist.com, businesswire.com |
| 429 | 1 | ru.wikipedia «Леонтьева» — позже открыта через `action=raw` |
| 000 | 7 | 5 ссылок на поиск Open Library (curl обрывался; через WebFetch открываются), filmcourage.com (Cloudflare, 403), web.archive.org (ArchetypeMe 2012) — обрыв соединения |

Содержимое открыто и сверено с утверждением у 64 адресов (новые и затронутые правками):

| URL | Код / способ | Подтверждает утверждение? |
|---|---|---|
| https://cyberleninka.ru/article/n/sociocultural-models-for-interpretation-of-c-g-jung-archetypes-in-advertising-industry | WebFetch | да; уточнена «политика» |
| https://experts.illinois.edu/en/publications/emotional-branding-and-the-strategic-value-of-the-doppelg%C3%A4nger-br/ | WebFetch | да |
| https://journal.media-culture.org.au/index.php/mcjournal/article/view/841 | 200 | цитаты да; «прямо выводят» — исправлено |
| https://www.archetypesinbranding.com/post/archetypal-shadows-of-the-american-dream | WebFetch | да |
| https://www.archetypesinbranding.com/post/stereotypes-and-the-shadow-of-the-provocateur | 200 | да; CEO — исправлено |
| https://www.slideshare.net/slideshow/archetypes-in-branding/49975573 | WebFetch | да (семейства) |
| https://lewishyde.com/?p=20 | 200 | да |
| https://transformmagazine.net/articles/2024/the-return-of-the-trickster | WebFetch | да |
| https://www.nlobooks.ru/upload/iblock/259/224-245.pdf | 200, pdftotext | да |
| https://seej.org/issues/68.4.html | 200 | да; «уходят» → «сходят на нет» |
| https://rspublisher.org/index.php/ws/article/view/1553 | WebFetch | да; название — исправлено |
| https://www.cambridge.org/core/journals/slavic-review/article/abs/borat-the-trickster-folklore-and-the-media-folklore-in-the-media/3D1D757648FF45E14510199F415EDF9D | 200 | да |
| https://vm.ru/accidents/1264276-mogut-ne-pustit-v-rossiyu-kak-verka-serdyuchka-perecherknula-otnosheniya-s-rf | WebFetch | да; дата 25.09.2025 добавлена |
| https://pmc.ncbi.nlm.nih.gov/articles/PMC6156458/ | WebFetch | да |
| https://businessofstory.com/podcast/brand-storytelling-christopher-vogler/ | WebFetch | да |
| https://myss.com/wp-content/uploads/2015/07/Gallery-of-Archetypes.pdf | 200, pdftotext | да (около 70 фраз) |
| https://myss.com/the-shapeshifter-the-power-of-archetypes/ | 200 | да (14.02.2023) |
| https://myss.com/the-victim-the-power-of-archetypes/ | 200 | да (01.02.2023) |
| https://myss.com/the-saboteur-the-power-of-archetypes/ | 200 | да (07.02.2023) |
| https://myss.com/the-wounded-child/ | 200 | да (19.04.2023) |
| https://myss.com/the-power-of-archetypes/ | 200 | да |
| https://www.piter.com/product/arhetipy-kak-ponyat-sebya-i-okruzhayuschih-ekopoket | 200 | да |
| https://www.piter.com/product/arhetipy-kak-ponyat-sebya-i-okruzhayuschih | 200 | да |
| https://www.boston.com/news/books/2024/05/31/how-a-self-published-book-broke-all-the-rules-and-became-a-bestseller/ | WebFetch | да |
| https://www.soundstrue.com/a/resources/contributor/connie-zweig | WebFetch | да |
| https://fortune.com/2023/09/30/kobe-bryant-beyonce-alter-ego-black-mamba-sasha-fierce-career-advice-performance-promotion-introvert-paul-mccartney-todd-herman-clinton-senkow-career-coach/ | WebFetch | да |
| https://blog.hubspot.com/marketing/duolingo-unhinged-content | 200 | да |
| https://socialsci.libretexts.org/…/4.03%3A_Case_study_Wendys_social_media_success_with_the_Roast_campaign | 200 | цитаты да; «с 2017 г.» — нет, исправлено |
| https://vc.ru/26878 | WebFetch | да; «редактор характера» — уточнено |
| https://www.sostav.ru/publication/sber-45972.html | WebFetch | да |
| https://articlegateway.com/journals/index.php/JHETP/article/view/8162 | WebFetch | да |
| https://ueaeprints.uea.ac.uk/100464/1/Audrezet_etal_2025_JBusinessResearch.pdf | 200, pdftotext | да |
| https://kayeputnam.com/brand-archetypes/sage | 200 | да |
| https://kayeputnam.com/brand-archetypes/magician | 200 | да |
| https://storybrand.com/ | 200 | да (отзывы; логотипы по именам файлов) |
| https://storybrand.com/building-a-storybrand-book/ | 200 | да; datePublished 2025-01-07 |
| https://marketingmadesimple.libsyn.com/5-are-you-the-hero-or-the-guide-to-your-customers | 200 | да (21.07.2021) |
| https://ana.esomar.org/documents/the-role-of-helpers-in-advertising | 200 | да |
| https://convergencias.ipcb.pt/index.php/convergences/article/view/13 | 200 | да |
| https://www.profitadvisors.com/journey.shtml | 200 | да |
| https://www.amyporterfield.com/ | 200 | да |
| https://mktravelclub.ru/about/ | 200 | да |
| https://sberbusiness.live/publications/archetype | 200 | цитата о Спиридонове — нет; исправлено |
| https://dsgners.ru/Plenum/5317-arhetipyi-v-marketinge-na-primere-didjitalnyih-brendov | 200 | да |
| https://craftum.com/blog/arhetipy-brenda/ | 200 | да |
| https://confhub.ru/archive/Lomonosov_2025/data/36727/183406_uid271377_report.pdf | 200, pdftotext | да |
| https://books.yandex.ru/books/Sa41TOTa/read-online | 200 | да |
| https://www.apple.com/siri/ | 200 | да |
| https://alice.yandex.ru/ | 200 | да |
| https://salute.sber.ru/ | 200 | да |
| https://stuff.mit.edu/afs/athena.mit.edu/user/m/b/mbarker/www/books/tech970523.txt | 200 | да |
| https://www.penguin.co.nz/books/archetype-cards-9781401901844 | 200 | да |
| https://ast.ru/book/arkhetipy-soyuzniki-i-razrushiteli-istochnik-vashey-sily-879844/ | 200 | да |
| https://nlb.overdrive.com/media/91216 | 200 | да |
| https://www.goodreads.com/author_blog_posts/1364557-sacred-contracts-by-caroline-myss | 200 | да |
| https://www.goodreads.com/author_blog_posts/7397244-creativity-part-vi-the-virgin-and-the-sacred-prostitute | 200 | да |
| https://carolspearson.com/books-page/the-hero-and-the-outlaw-building-extraordinary-brands-through-the-power-of-archetypes | 200 | да |
| https://openlibrary.org/search/inside?q=%22guardian+of+self-esteem%22 | WebFetch | **опровергает** прежнее примечание victim [11]; исправлено |
| https://openlibrary.org/search/inside?q=%22Weakling+Prince%22 (и запрос «High Chair Tyrant…») | WebFetch | да |
| https://openlibrary.org/search/inside?q=%22energy+of+the+animus%22 | WebFetch | да |
| https://openlibrary.org/search/inside?q=%22Saboteur+archetype+in+her+third+house%22 | WebFetch | да |
| https://openlibrary.org/search/inside?q=%22tenth+house+(highest+potential%22 (запрос «Prostitute in my tenth house») | WebFetch | да |
| https://en.wikipedia.org/wiki/… (Stephen_Colbert_(character), The_Yes_Men, 1984_(advertisement), Donald_Miller_(author), Fred_Rogers, Marques_Brownlee, Simon_Cowell, Steve_Irwin) | wikitext | да; Ирвин — уточнено |
| https://ru.wikipedia.org/wiki/… (BadComedian, Wylsacom, ВТБ_24, Уралсиб, Росгосстрах, Пучков, Кожухов, Ильяхов, Левитан, Леонтьева, Тутта_Ларсен, Петрановская, Дроздов) | wikitext | да; Левитан, Дроздов, ВТБ 24, Wylsacom, Кожухов — уточнено |

Не открылись или не подтверждены:
- academyofideas.com, affordanything.com, blinkist.com, businesswire.com, networkisa.org — 403;
- filmcourage.com — Cloudflare;
- slideshare.net/purifiedgenius — заглушка: «mentor brand» (Опра / Чопра / Стюарт) и «hero's trusted companion» не перепроверены; в карточках источник уже помечен «низкая надёжность»;
- YouTube (@msrachel, @academyofideas) — без JS число подписчиков не отдаётся;
- web.archive.org (сайт Воглера 2016, ArchetypeMe 2012) — обрыв соединения; живой thewritersjourney.com — 503, как и указано в карточках;
- reestrs.minjust.gov.ru — обрыв.

Новые источники, добавленные в конец списков:
- shadow [35], [36];
- persona [37], [38];
- trickster [34], [35];
- great-mother [30];
- guide-mentor [47];
- vogler-roles [36];
- myss-child [32].

## 8. Сводка

- **Проверено:**
  - 111 строк-утверждений (более 200 отдельных цитат и фактов) из нового и изменённого текста;
  - 32 снятые ⚠;
  - 95 новых URL по HTTP-коду, из них у 64 сверено содержимое;
  - 16 русскоязычных персон из таблиц разделов 13 и 15 авторов источников;
  - правила: нумерация, цитаты, ссылки, пиратские домены, Таро, отсутствие продуктовых рекомендаций, README.
- **Главные исправления:**
  1. **Жертва:** подзаголовок «The Victim: Guardian of Self-Esteem» есть в самой книге Мисс 2001 г. Раньше утверждалось обратное, со ссылкой на якобы пустой поиск. Попутно для Саботажника: «Guardian of Choice» тоже есть в книге.
  2. **Тень:** фраза «nigredo, shadow as only black» приписана Дюрану (1981) без опоры на источник. Сниппет — из ежегодника «Spring» 1980, автор не назван. Атрибуция снята, поставлена ⚠.
  3. **Проводник:** цитата «воспринимается как наставник» о Спиридонове в источнике отсутствует. Статья говорит это о Мудреце вообще, а Спиридонова называет его представителем.
  4. **Дитя:** найдены названия домов 4, 5, 12 (Home; Creativity and Good Fortune; The Unconscious), ⚠ снят.
  5. **Неточности источников исправлены:**
     - Carl's Jr.: связь продаж с кампанией делает Хартвелл, а не CEO;
     - Wendy's: «с 2017 г.» в источниках нет;
     - Hogan: «куратор» — механизм платформы;
     - persona studies: опираются в том числе на Юнга и Гофмана, а не «прямо выводят»;
     - Базикян: слоганы в одном ряду с политическими призывами;
     - Левитан: нет ни 22.06.1941, ни 9.05;
     - Ирвин, Дроздов, Кожухов («двадцать лет»), Wylsacom (платформы), ВТБ 24, «Росгосстрах»;
     - название статьи Конвалюк — украинская орфография.
  6. **Правовые примечания** дополнены:
     - сверкой со списком «иноагентов» ру-Википедии у всех живых русскоязычных персон;
     - запретом въезда для Данилко по Википедии и датой статьи «ВМ»;
     - санкциями Швейцарии и Украины для Пучкова;
     - пометкой о «Миротворце» для Кожухова, с оговоркой.
  7. **Таро:** добавлены ссылки на `06-esoteric-links.md` в 8 местах.
  8. **README:** снято устаревшее «юнговские карточки доводятся параллельно», добавлены ссылки на c01 и v13.
- **Что осталось:**
  - **Реестр Минюста** не открылся (скрипт с reestrs.minjust.gov.ru). Все правовые примечания требуют юридической проверки по официальному реестру; у Спиридонова и Wylsacom оставлена ⚠.
  - **Автор эссе в «Spring» 1980** («shadow as only black») не установлен; нужен экземпляр или оглавление выпуска.
  - **Не перепроверены** (страницы недоступны): Afford Anything (эпизод 184), Academy of Ideas, слайды purifiedgenius («mentor brand»), Business Wire (дата «2.0» — только косвенно), YouTube-счётчики (Ms Rachel 21,6 млн, Academy of Ideas 3,79 млн), архив сайта Воглера («© 1985», определения ролей), ArchetypeMe 2012.
  - **Остаются ⚠ из c01/c02 с причинами:** русское издание «Sacred Contracts», платный Substack (Саботажник), ICPL / B&N, сайт Воглера (503), сводки по Нилану и Film Courage, русская формулировка цитат StoryBrand, «Мудрец-наставник», SB7.
  - **Сводные файлы** (`sources.md`, `verification.md`, корневой README) этой проверкой не обновлялись: это шаг 8 плана.
