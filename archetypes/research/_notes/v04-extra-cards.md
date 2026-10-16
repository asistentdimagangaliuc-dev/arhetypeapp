# v04 — независимая проверка карточек вне 12 брендовых и оглавления `02-cards/`

> **Дата проверки:** 2026-10-16. **Объект:** `02-cards/extra-*.md` (12 файлов) и `02-cards/README.md`. Проверяющий не участвовал в сборе и написании материалов.
> **Итог в цифрах:** проверено 140 утверждений, 10 пунктов README и сквозных правил, 94 URL (87 адресов из самих файлов и 7 служебных). Из 140 утверждений подтверждено 104, исправлено 29, помечено ⚠ 6. Одна ссылка удалена: блог дословно воспроизводит текст книги. После подтверждения пометка ⚠ снята в 18 местах. Новая ⚠ поставлена в 20 местах: 15 — недоступные ссылки, 5 — неподтверждаемые формулировки.

## 1. Методика

1. **Чтение.** Прочитаны все 13 файлов целиком. Для сверки происхождения утверждений использованы заметки `r01` (Юнг) и `r03` (Мисс, Воглер). Заметки не менялись.
2. **Юнг.** Цитаты и номера параграфов сверялись тремя способами:
   - по онлайн-версии словаря Шарпа (Jung Lexicon), опубликованной с согласия автора, — по точным ссылкам вида «CW 9i, par. 221»;
   - по полнотекстовому поиску Open Library / Internet Archive (`openlibrary.org/search/inside`). Он возвращает только короткие сниппеты из библиотечных экземпляров CW 9i (1959, 1968, 1980), сборника «Four Archetypes» (1973) и вторичной литературы. Номер параграфа считался подтверждённым, если он виден на полях в сниппете или прямо указан во вторичной работе («CW 9i, par. …»). Поиск внутри конкретных экземпляров закрыт (HTTP 403), сами экземпляры не открывались;
   - копии с archive.org, загруженные пользователями (на них опирается r01), **не использовались**.
3. **Мисс.** Сверка по PDF «Gallery of Archetypes» (myss.com, 2015, 105 с.; текст извлечён полностью), по странице myss.com о Проститутке, по рецензиям Publishers Weekly, по описанию Penguin Random House и по ознакомительному фрагменту «Sacred Contracts» на e-bookshelf.de.
4. **Воглер и StoryBrand.** Использованы:
   - сайт Воглера thewritersjourney.com — живой сайт сбрасывает соединение, поэтому взята архивная копия Wayback Machine от 28.10.2016;
   - страница MIT с цитатами из 1-го издания;
   - сниппеты Open Library из 2-го издания (1998);
   - оглавление русского перевода на Фантлабе;
   - Википедия — через API, в виде викитекста;
   - конспект Г. Манна, storybrand.com, страницы «Альпины» и Литреса.
5. **README.** Проверено существование всех файлов из ссылок (скрипт). Таблица Марк и Пирсон сверена по сниппетам Open Library из самой книги (2001) и из Solomon (11-е изд.), по PDF оглавления «Бомборы», по полному тексту Xara-Brasil и соавт. (CC BY).
6. **Правила.** Скрипт проверил:
   - нет ли цитат в «» и "" длиннее 22 слов — таких нет;
   - соответствие номеров [n] спискам источников — в каждом файле нет пропущенных номеров, неиспользованных источников и разрывов нумерации;
   - работоспособность относительных ссылок;
   - строки со словами «Таро», «аркан» и «Tarot».

   Таро-связки сверены с таблицей §2.1 файла `06-esoteric-links.md`.
7. **URL.** Все 87 адресов из файлов проверены через curl. Адреса с HTTP 403 повторно проверены через WebFetch. Содержание проверялось поиском конкретных фраз в загруженном тексте.
8. **Ограничения.** WebSearch использован 8 раз и только для поиска адресов; выдачу поисковиков как источник не использовали. Пиратские копии не открывались. Флибусту, найденную в выдаче, не использовали: данные о переводчике взяты с Литреса. Личные данные в запросы не включались.

## 2. Проверка утверждений

Сокращения: **Шарп** — https://www.psychceu.com/jung/sharplexicon.html; **OL** — полнотекстовый поиск Open Library (`https://openlibrary.org/search/inside?q=…`, в скобках — искомая фраза); **Галерея** — https://myss.com/wp-content/uploads/2015/07/Gallery-of-Archetypes.pdf; **сайт Воглера** — https://web.archive.org/web/20161028170951/http://www.thewritersjourney.com/hero's_journey.htm.

### 2.1. Юнгианские карточки

| № | файл | утверждение | чем проверено (URL) | вердикт | комментарий |
|---|---|---|---|---|---|
| 1 | persona | CW 9i §221: определение Персоны, «that which in reality one is not…» | Шарп («Concerning Rebirth», CW 9i, par. 221); OL («which oneself as well as others think one is» — у Stevens 1994 и Lopker 2000 «CW 9i, par. 221») | подтверждено | — |
| 2 | persona, prostitute | §221: профессор и тенор, «the persona is usually rewarded in cash» | OL («usually rewarded in cash»: Humbert 1988 — «C.W. 9/1, par. 221»; в «Jung on Death and Immortality» сразу за фразой номер 222) | подтверждено | главная цитата карточки и README |
| 3 | persona | §43: «the mask of the actor» | OL (фраза в контексте «we cover it with the persona, the mask of the actor») | подтверждено | формулировка; номер — по r01 |
| 4 | persona | CW 7 §245 «mask that feigns individuality»; §246 «compromise between individual and society» | Шарп: обе фразы в одной выдержке с пометкой «pars. 245f.» | исправлено | §246 → «§§245 сл.» (2 места) |
| 5 | persona | CW 7 §244 «arbitrary segment of the collective psyche» | Шарп (статья «Collective», CW 7, par. 244) | подтверждено | — |
| 6 | persona | CW 6 §801 «functional complex…»; «Шарп называет её…» | Шарп («Persona»: «[Ibid., par. 801]», где Ibid. — CW 6 «Definitions») | исправлено | это слова Юнга, Шарп их только цитирует |
| 7 | persona | CW 7 §307 «…without punishment» | Шарп («Anima and Animus», par. 307) | подтверждено | — |
| 8 | persona, self | CW 7 §§377, 380, 389 (мана-личность, «adulterated with an archetype») | Шарп («Mana-personality») | подтверждено | — |
| 9 | persona, anima | Вики-сводка: Персона, Анима, Тень, Самость — «personality systems» (Pennington 2018) | https://en.wikipedia.org/wiki/Jungian_archetypes (викитекст: «four of the archetypes that fall under the separate systems of the personality») | исправлено | кавычки стояли не на точной формулировке; Википедия называет их архетипами (3 места) |
| 10 | persona | Пирсон: назвав архетипы, человек выходит за пределы внешней персоны | https://www.psychologytoday.com/us/blog/the-seekers-forum/202408/which-archetypes-are-you-living («move beyond the persona of how we're showing up») | подтверждено | — |
| 11 | persona | Куликова: «одна только персона делает человека неполным» | https://snob.ru/profile/406294/blog/3095455/ («поняв односторонность персоны, приняв всю силу своей тени») | исправлено | пересказ уточнён |
| 12 | persona | Пилиповец: «создаёт недоверие»; «Архетип не нужно «играть»…» | https://mybusiness.by/2026/tpost/archetypes-founder-business | исправлено | точная цитата — «возникает недоверие»; вторая цитата подтверждена |
| 13 | persona | Яппарова: «Первичен не образ, первичен человек» | https://vc.ru/1129215-chto-ne-tak-s-arhetipami | подтверждено | — |
| 14 | persona | Соколова: ошибка — искусственная «маска» | https://www.sostav.ru/blogs/288649/93766 («Только не делайте из архетипа искусственную маску») | подтверждено | — |
| 15 | persona | Булыгина: «ощущение фальши и манипуляции» | https://tenchat.ru/media/3750005-… (со второй попытки) | подтверждено | — |
| 16 | persona | Bailey et al. 2020: 10 560 пользователей Facebook; предрегистрированный эксперимент; 11:4889 | https://api.crossref.org/works/10.1038/s41467-020-18539-w ; Europe PMC | подтверждено | ссылка UCL — HTTP 403 → помечено ⚠, добавлен DOI |
| 17 | persona | Duffy & Hund: «too real» / «not real enough»; «многие заранее цензурируют себя» | https://ijoc.org/index.php/ijoc/article/view/11729 | исправлено | первое подтверждено; в аннотации не «цензура», а «stave off potential critique in patterned ways» |
| 18 | persona | Kross et al. 2014: самодистанцирование — меньше дистресса, лучше оценка наблюдателей | https://rascl.studentorg.berkeley.edu/…/self-talk_….pdf («performed better according to objective raters»); Crossref 10.1037/a0035173 (JPSP 106(2):304–324) | подтверждено | — |
| 19 | persona | Херман / Бейонсе — Sasha Fierce | https://affordanything.com/episode184 — HTTP 403 (curl и WebFetch) | помечено ⚠ | ссылка недоступна; утверждение и раньше было под ⚠ |
| 20 | shadow | Aion §13: самая доступная — Тень | OL («The most accessible of these, and the easiest to experience, is the shadow») | подтверждено | формулировка; номер — по r01 |
| 21 | shadow | Aion §14: «moral problem that challenges the whole ego-personality» | Шарп («The Shadow», CW 9ii, par. 14) | подтверждено | — |
| 22 | shadow | Aion §15 (автономия), §17 («replica of one's own unknown face») | Шарп (par. 15, par. 17) | подтверждено | — |
| 23 | shadow | Aion §19: «a rare and shattering experience» | Шарп («The Shadow», ibid., par. 19) | подтверждено | — |
| 24 | shadow | CW 9i §45: «a tight passage, a narrow door» | OL (фраза) | подтверждено | формулировка; номер — по r01 |
| 25 | shadow, anima | CW 9i §61: «apprentice-piece» / «master-piece» | Шарп («Archetypes of the CU», CW 9i, par. 61) | подтверждено | — |
| 26 | shadow | CW 9i §222: подчинённая функция ≈ тёмная сторона | Шарп («Inferior function», par. 222) | подтверждено | — |
| 27 | shadow, README | CW 9i §309: перечень главных фигур, «suggestion» | Шарп (Kore, par. 309); OL («according to my suggestion, the shadow, the wise old man, the child…») | подтверждено | — |
| 28 | shadow, trickster | CW 9i §485: тень «although by definition a negative figure»; трикстер — «parallel of the individual shadow» | OL: в CW 9i (1968) и «Four Archetypes» номер «485» стоит на полях перед «If we take the trickster as a parallel…» | подтверждено | подтверждён и номер параграфа |
| 29 | shadow, trickster | §469/470: «remnants of a collective shadow figure» | OL (фраза; номер в сниппетах не виден) | помечено ⚠ | ⚠ сохранён |
| 30 | shadow | CW 11 §134: «not wholly bad» (по Шарпу) | Шарп («Psychology and Religion», CW 11, par. 134) | подтверждено | — |
| 31 | shadow | Воглер: Тень — функция антагониста, «а не внутренняя часть героя» | сайт Воглера («Villains and enemies, perhaps the enemy within… the repressed possibilities of the hero») | исправлено | Воглер прямо допускает внутреннее прочтение (разделы 3, 4, 6, 7; источник [21]) |
| 32 | shadow | Пирсон: тень — то, что отвергнуто как «not OK»; в ней «treasure» | Psychology Today (см. п. 10) | подтверждено | — |
| 33 | shadow, saboteur, victim | МИФ: «с почтением», «недостаточно хороши», «Позиция жертвы», «курсы саморазвития» | https://blog.mann-ivanov-ferber.ru/2024/07/23/… | подтверждено | — |
| 34 | shadow, saboteur | Sorsby: «fear of being seen», «shrinking your message to avoid judgment», «fear of being misunderstood»; архетипов в тексте нет | https://bonniesorsby.com/how-to-use-shadow-work-to-strengthen-your-brand/ | подтверждено | — |
| 35 | shadow, self | АрхетипиУМ: «страх проявляться», «что подумают», «хейт», «паралич анализа»; у Мага — «гуру» | arhetipium.ru (/idealist, /slavniy-malyi, /mudrec, /mag, /workshop-…) | подтверждено | — |
| 36 | shadow | Адт: модули «Идентификация теней и комплексов…», «Теневые стратегии» | https://alinaadt.ru/masterarchetype | подтверждено | — |
| 37 | shadow | JobCannon: цитата «доминирующий архетип, два-три вторичных и теневой архетип» | https://jobcannon.io/ru/tests/jungian-archetype | исправлено | цитата была составной; заменена пересказом с точными словами страницы |
| 38 | shadow | Куликова: непризнанная тень «управляет», энергия уходит на подавление или на реализацию | snob.ru (см. п. 11) | подтверждено | — |
| 39 | shadow, anima, great-mother, trickster | «Питер» (ISBN 978-5-4461-1928): главы «Тень», «Анима-Анимус», «Трикстер», «Мать», «Грозная Мать» | https://storage.piter.com/upload/contents/978544611928/978544611928_X.pdf (гл. 4, 5, 10, 22, 23) | подтверждено | автор и название книги по-прежнему ⚠ |
| 40 | shadow | Лукас опирался на Кэмпбелла | https://en.wikipedia.org/wiki/The_Hero_with_a_Thousand_Faces | подтверждено | — |
| 41 | anima | Aion §26: анима — «the projection-making factor» | OL («The projection-making factor is the anima, or rather the unconscious…») | подтверждено | формулировка; номер — по r01 |
| 42 | anima | Aion §29: Логос и Эрос; «I do not wish or intend to give these two intuitive concepts too specific a definition» | Шарп («The Syzygy», CW 9ii, «pars. 28f.» и par. 29) | подтверждено | — |
| 43 | anima | Aion §33: анимус — «psychopomp», «capacity for reflection, deliberation, and self-knowledge» | Шарп (par. 33); OL (Matthews 2005: «CW-9-II, par. 33») | подтверждено | — |
| 44 | anima | CW 7 §336: «the deposit… of all woman's ancestral experiences of man» | Шарп («Anima and Animus», CW 7, par. 336) | подтверждено | — |
| 45 | anima | CW 9i §66: «the archetype of life itself» | Шарп (par. 66) | подтверждено | — |
| 46 | anima | CW 9i §60: «angel of light, a psychopomp…» | OL: в CW 9i фраза стоит непосредственно перед «If the encounter with the shadow is the apprentice-piece…» (это §61 по Шарпу) | подтверждено | номер §60 согласуется с текстом |
| 47 | anima | §310: у мужчины Кора — тип анимы | OL (вторичное: «in a man the kore belongs to the anima type»); r01 | подтверждено | добавлено: у женщины — тип «supraordinate personality» |
| 48 | anima | §311: формы Коры («unknown young girl», танцовщица, менада, нимфа, никса) поданы как формы **анимы** | Шарп («Kore», CW 9i, par. 311: «the Kore often appears **in woman** as an unknown young girl…»); OL («maiden appears as the corybant, maenad, or nymph») | исправлено | это формы Коры в женской психологии (разделы 3 и 6) |
| 49 | anima, README | Ось Марк и Пирсон: полюс «Belonging» ⚠ | OL — сниппет книги 2001 г.: «along two axes: Belonging/People versus Independence/Self-Actualization, and Stability/Control versus Risk/Mastery»; Solomon 11e | исправлено | ⚠ снят в карточке и в README |
| 50 | anima | Solomon: Lover — «Attain intimacy and experience sensual pleasure» | OL (Solomon, изд. 2018) | подтверждено | в 11-м изд. (2014) сниппет не найден — вероятно, из-за OCR |
| 51 | anima, persona, self, shadow | Kerykeion: Анима — Жрица и Императрица; Анимус — Император и Иерофант; Тень — Дьявол, Луна, Башня; Самость — Мир, Солнце; Персона — Колесница (и Император) | https://kerykeion.net/content/learn-tarots/psychology/jung-and-tarot | подтверждено | совпадает с 06 |
| 52 | self | Aion гл. I, с. 5: «I have suggested calling the total personality…» (≈§9 ⚠) | OL (Fordham et al. 1980: «(p. 5)») | подтверждено | с. 5 подтверждена; номер §9 по-прежнему ⚠ |
| 53 | self | CW 9i §315: «I usually describe the supraordinate personality as the "self"» | Шарп («Supraordinate personality», «pars. 314f.») | подтверждено | — |
| 54 | self | CW 9i §306: Кора ↔ «the self or supraordinate personality… and the anima» | OL («The "Kore" has her psychological counterpart in those archetypes…») | подтверждено | формулировка |
| 55 | self | CW 12 §44: «not only the centre, but also the whole circumference» | Шарп («Introduction», CW 12, par. 44) | подтверждено | — |
| 56 | self | Aion §§59–60: символы целостности ≈ imago Dei | OL («can no longer be distinguished from the imago Dei») | подтверждено | формулировка; номера — по r01 |
| 57 | self | Aion §44: инфляция | Шарп («The Self», CW 9ii, par. 44) | подтверждено | — |
| 58 | self | «В перечне форм перерождения Юнг называет «естественную трансформацию (индивидуацию)» [§§199–219]» | OL: CW 9i (1968) и «Four Archetypes» — «234 h. Natural transformation (individuation)»; в оглавлении это подпункт h раздела «Subjective Transformation», а не одна из «форм перерождения» | исправлено | §234; формулировка исправлена в тексте и в источнике [2] |
| 59 | self, child | CW 9i §278: «symbol which unites the opposites» | OL (фраза) | подтверждено | формулировка |
| 60 | self | Хиллман: Юнг «too prescriptive», против «life-maps» | https://en.wikipedia.org/wiki/Archetypal_psychology | подтверждено | — |
| 61 | self | Нолл и Шамдасани («Cult Fictions», 1998) | https://en.wikipedia.org/wiki/The_Jung_Cult | подтверждено | — |
| 62 | self, shadow, guide | Avia Venefica: Солнце — «The Radiant Self», Мир — «The Whole Self», Дьявол — «The Shadow / The Tempter», Иерофант — «The Mentor / The Spiritual Teacher» | https://www.tarotteachings.com/?p=2602 | подтверждено | — |
| 63 | self, anima, gm, trickster | OLLI: Шут — «archetype of the unrealized Self»; Маг — «towards the Self», «trickster»; Император — «powerful animus figure»; мачехи — тень Матери | https://www.uc.edu/…/jung%20tarot%201.pdf | подтверждено | — |
| 64 | trickster | §456: черты Меркурия, «approximation to the figure of a saviour»; карнавал — «reversal of the hierarchic order» | OL (фразы; Rowland 2005: «(ibid.: para. 456)» — к фрагменту о карнавале) | подтверждено | — |
| 65 | trickster | §465: «psychologem»; плутовские романы, карнавалы | OL: в «Four Archetypes» на полях «465» перед «In picaresque tales, in carnivals and revels…» | подтверждено | подтверждён и номер |
| 66 | trickster | §469: «hoodoos», «jinxes», «mischievousness of the object» | OL (фраза) | подтверждено | формулировка; номер — по r01 |
| 67 | trickster | §472: «chief and most alarming characteristic is his unconsciousness», «forerunner of the saviour» | Шарп («Trickster», par. 472); OL (Bassil-Morozow: «CW9/I: para. 472») | подтверждено | — |
| 68 | trickster | §487: спаситель в конце мифа | OL («If, at the end of the trickster myth, the saviour is hinted at…») | подтверждено | формулировка |
| 69 | trickster | PMAI: Jester — «Entertainer, Trickster, Court Fool» | https://www.storywell.com/archetypes/archetype-descriptions.htm (alt-текст изображения) | подтверждено | — |
| 70 | trickster | Ebaq: Jester также «trickster» | https://www.ebaqdesign.com/blog/brand-archetypes | подтверждено | — |
| 71 | trickster | Solomon / Franzen & Moriarty: Jester — «To live in the moment with full enjoyment» | OL (Solomon 11e; Franzen & Moriarty 2009) | подтверждено | — |
| 72 | trickster, child | Мур и Жиллетт: Trickster — тень Precocious Child; тени Divine Child — Tyrant и Weakling | https://www.goodreads.com/book/show/91781 (заметки читателей) | подтверждено (по отзывам) | ⚠ «по тексту книги не подтверждено» сохранён |
| 73 | trickster, gm, self | Nichols (исп. изд.): гл. 4 «El Mago: Creador y tramposo»; гл. 6 «La Emperatriz: Señora, Gran Madre…»; гл. 22 «El Sol: Centro radiante» | https://content.e-bookshelf.de/media/reading/L-18717667-86f49bf70f.pdf | подтверждено | — |
| 74 | trickster | Davidson: Маг — Трикстер и Прометей | https://jessicadavidson.co.uk/2014/07/09/tarot-heros-journey-the-magician/ | подтверждено | — |
| 75 | trickster, gm | Леонова: Алдар-Косе в группе «Принадлежность» (с Махаббат и Джигитом); Әже — в группе «Стабильность» | https://books.yandex.ru/books/PKGjPsYP/read-online | подтверждено | — |
| 76 | trickster, guide | Т—Ж (2025): «Трикстер», «Наставник» среди названий | https://t-j.ru/mif-kak-metod/ | подтверждено | — |
| 77 | trickster | Воглер: Трикстер — одна из 8 функций | Wikipedia (3-е изд.); MIT (1-е изд.: 7); сайт Воглера; Фантлаб | исправлено | добавлено «в 1-м изд. — из 7», описание Воглера и русское «Плут» (новые [16], [17]) |
| 78 | great-mother | §155: «empty and purely formal, nothing but a facultas praeformandi» | OL (фраза) | подтверждено | формулировка |
| 79 | great-mother | §157: тёмные символы (ведьма, дракон, могила… «deep water, death, nightmares») | OL (Mis/takes 2006 — ссылка на CW 9i; «Four Archetypes») | подтверждено | — |
| 80 | great-mother | §158: «the loving and the terrible mother», Дева Мария и Кали; «maternal solicitude and sympathy» | OL (CW 9i 1968: «In India, "the loving and terrible mother" is the paradoxical Kali»; «maternal solicitude and sympathy») | подтверждено | — |
| 81 | great-mother | Материнский комплекс: §§162, 167, 168, 170 — по Шарпу | Шарп («Mother complex»: par. 162; Ibid., par. 167, 168, 170) | подтверждено | — |
| 82 | great-mother | CW 5 §395 (дракон — «negative mother-imago»), §459 («never anything but temporary») | OL (Kimball 1997; Bloom 1985) | подтверждено | формулировка; номера — по r01 |
| 83 | great-mother | Нойманн: «primordial image of the human psyche», образы, «both nurturing and fearsome», дитя ↔ Великая Мать | https://press.princeton.edu/books/paperback/9780691166070/the-great-mother (через curl — 403, через WebFetch открывается; изд. 2015) | подтверждено | — |
| 84 | great-mother | Нойманн, «Origins»: Великая Мать, разделение Мировых Родителей, рождение героя, убийство дракона | https://press.princeton.edu/books/paperback/9780691163598/the-origins-and-history-of-consciousness (WebFetch; изд. 2014) | подтверждено | — |
| 85 | great-mother | «Год немецкого издания — 1956, в тексте статьи — 1955 ⚠» | https://en.wikipedia.org/wiki/Erich_Neumann_(psychologist) — англ. «The Great Mother» (1955), нем. «Die große Mutter» (1956) | исправлено | это не противоречие (английский перевод вышел раньше оригинала); ⚠ снят |
| 86 | great-mother | VisionOne: Caregiver «also goes by… the Mother» | https://visionone.co.uk/brand-archetype-quiz/the-caregiver-brand-archetype/ | подтверждено | — |
| 87 | great-mother | Kaye Putnam: подтипы «The Mother or Father», «Mother Earth» (внутри «Monk or Nun») | https://kayeputnam.com/brand-archetypes/caregiver | подтверждено | — |
| 88 | great-mother | Wang: «архетип Матери» | https://www.abebooks.com/9780971559110/… | подтверждено | — |
| 89 | great-mother | Шарлай: Мать, Старец, Дитя, Возлюбленный | https://www.litres.ru/book/anna-sharlay/arhetipy-i-obrazy-64468643/chitat-onlayn/ | подтверждено | — |
| 90 | great-mother, guide, child | Гас: «Заботливый (родитель, наставник)», «Простодушный (ребенок, дитя)» | https://teletype.in/@katyagas/czNfmod6BTZ («11. Заботливый, родитель, наставник»; «1. Простодушный, ребенок, дитя») | исправлено | кавычки приведены к тексту (3 файла) |
| 91 | great-mother | Skillbox: «Родитель» | https://skillbox.ru/media/design/archetypes-in-simple-words/ | подтверждено | — |

### 2.2. Карточки Мисс

| № | файл | утверждение | чем проверено (URL) | вердикт | комментарий |
|---|---|---|---|---|---|
| 92 | child, victim, prostitute, saboteur | PW (2001): «controlled in different ways», «are up to us»; Harmony, 464 с. | https://publishersweekly.com/9780517703922 (рецензия от 03.12.2001) | подтверждено | — |
| 93 | child | Галерея: 4 архетипа выживания «common to all of humanity», «four legs of a table», «other eight personal archetypes», «circle of twelve» | Галерея | подтверждено | — |
| 94 | child | Дитя — «guardian of innocence»; 7 вариантов; один обычно доминирует; урок — «hone responsibility»; ядро — напряжение между зависимостью и ответственностью | Галерея | подтверждено | — |
| 95 | child | Тени вариантов: Раненое — жалость к себе, обвинение родителей, поиск родительских фигур; Сирота — «суррогатная семья»; Зависимое — нуждаемость | Галерея | подтверждено | — |
| 96 | child | Нельзя «привить» архетип только потому, что он нравится | Галерея (введение: «You cannot graft on an archetype simply because you find it attractive to own») | подтверждено | — |
| 97 | child | Колесо из 12 домов; названия домов ⚠ | https://content.e-bookshelf.de/media/reading/L-535049-ae25abbe32.pdf (фрагмент «Sacred Contracts»: «twelve archetypal patterns, corresponding to the twelve houses of the zodiac»; в оглавлении — «Template for the Twelve Houses of the Archetypal Wheel») | исправлено (уточнено) | связь с 12 домами зодиака подтверждена (новый [16]); названия домов — ⚠ сохранён |
| 98 | child | Объём Галереи: «около 90 статей в 9 семействах»; «более 70» в книге ⚠ | Галерея (алфавитный список — ровно 90 позиций, 7 из них — варианты Дитя; 9 обзоров семейств); OL (Heaven 2006: «Sacred Contracts (New York: Bantam, 2002), lists more than seventy archetypes») | исправлено | 90 — точно; «более 70» — по вторичному источнику [19], по самой книге ⚠ |
| 99 | child | Колода «Archetype Cards»: 80 карт, в т. ч. 6 пустых | https://www.books2door.com/products/9781401901844 (80); https://avidreader.com.au/p/archetype-cards (72 + 6 пустых); АСТ (по поисковой сводке: 74 + 6); B&N — 502 | помечено ⚠ | описания расходятся; добавлены [17]–[20] |
| 100 | child | Мисс 2013: «from careers to relationships»; «10 других семейств» | https://www.penguinrandomhouse.com/books/601468/… (фраза есть в данных страницы); https://publishersweekly.com/9781401941086 («ten emerging archetypal patterns») | исправлено | цитата подтверждена; «семейства» заменены на «10 основных архетипов с подархетипами» |
| 101 | child | Примеров персонажей в Галерее нет; Питер Пэн — оценка исследования | Галерея: у каждого варианта есть разделы FILMS, FICTION, RELIGION/MYTH; Питер Пэн — в «Eternal Child» | исправлено | добавлены примеры; Питер Пэн — из источника |
| 102 | child, victim | Пирсон: опыт потери «rightly called Orphan»; в M&P — Regular Guy/Gal, «evoked an image customers would recognize» | https://carolspearson.com/about/the-pearson-12-archetype-system-human-development-and-evolution | подтверждено | — |
| 103 | victim | Ядро (отказ от силы, чтобы не отвечать за независимость), свет, тень («never your fault»), урок (границы, самоуважение) | Галерея | подтверждено | — |
| 104 | victim | ⚠ подзаголовка «guardian of…» у Жертвы нет | Галерея (в списке — просто «victim», в заголовке статьи тоже) | подтверждено | ⚠ об отсутствии подзаголовка снят; ⚠ на популярное «хранитель самоуважения» сохранён |
| 105 | victim | Раздел 6: «в источниках не найдено» | Галерея (Хилари Суонк, Джоди Фостер, Мерил Стрип; «Джекил и Хайд», «Мизери»; Исаак, Геракл) | исправлено | — |
| 106 | victim | Solomon: цель Славного малого — «To belong» | OL (Solomon 11e: «Goal: To belong and fit in») | исправлено | цитата дополнена |
| 107 | prostitute | «guardian of faith»; продажа целостности, талантов и самовыражения; «Not for sale»; «take up your bed and walk»; «money, energy, dignity, or time» | Галерея | подтверждено | — |
| 108 | prostitute | Ключевой вопрос «through what means will I survive?» ⚠ (по поисковой сводке) | https://myss.com/the-prostitute-the-power-of-archetypes/ (запись от 15.03.2023) | подтверждено | ⚠ снят в трёх местах |
| 109 | prostitute | «Несчастливые отношения / нелюбимая работа» [3][4] | myss.com (п. 108) — в тексте этого нет | исправлено | оставлен только [3] (Галерея) |
| 110 | prostitute | Раздел 6: «в источниках не найдено» | Галерея (Джек Леммон, Фред Макмюррей, Марлон Брандо; «Доктор Фауст»; Ошун) | исправлено | — |
| 111 | saboteur | «guardian of choice»; «fear of inviting change»; нейтральная энергия; «gut instinct»; мужество и малые выборы; «opt to be ordinary» | Галерея | подтверждено | — |
| 112 | saboteur | Связь страхов с низкой самооценкой ⚠ (r11) | Галерея («The Saboteur's fears are all related to low self-esteem») | подтверждено | пометка r11 снята |
| 113 | saboteur | Саботажник как «Guardian of Choice» «защищает от неудобной правды» [4][5] | https://liveencounters.net/?p=10396 (есть «Guardian of Choice», «неудобной правды» нет); https://mavericksandmalbec.substack.com/p/… (платный доступ) | помечено ⚠ | 2 места |
| 114 | saboteur | Раздел 6: «в источниках не найдено» | Галерея (Гарбо, Лэнсбери; Сальери; Локи — «a Shape-shifter and Trickster», Эрида, Змей) | исправлено | — |
| 115 | saboteur | Перевод МИФ: «Бунтарь разрушает многое…», пер. А. Багрянцевой | https://www.litres.ru/book/carol-s-pearson-2/probuzhdenie-vnutrennego-geroya-…/chitat-onlayn/ | подтверждено | — |
| 116 | victim, prostitute, saboteur, child | Оглавление «Sacred Contracts» по каталогу ICPL | https://search.icpl.org/Record/1206155 — HTTP 403 (curl и WebFetch); фрагмент издателя на e-bookshelf | помечено ⚠ | ссылка недоступна; оглавление подтверждено фрагментом (новые [6], [9], [11], [16]) |

### 2.3. Воглер и StoryBrand

| № | файл | утверждение | чем проверено (URL) | вердикт | комментарий |
|---|---|---|---|---|---|
| 117 | guide, vogler, trickster | «flexible character functions…», «masks… temporarily»; p. 34 ⚠ (в другой сводке p. 36) | https://stuff.mit.edu/afs/athena.mit.edu/user/m/b/mbarker/www/exercises/exer981026.txt («(P. 34)» — цитата; «(P. 36)» — список архетипов) | исправлено | ⚠ снят: p. 36 — страница списка, а не цитаты |
| 118 | guide, vogler | 8 архетипов; «некоторые пересказы дают 7, без Союзника» | Wikipedia (8 — по 3-му изд. 2007); MIT (1-е изд., с. 36: семь, без Ally); OL (2-е изд. 1998: «HERO / MENTOR… / SHAPESHIFTER / SHADOW / TRICKSTER»); https://fantlab.ru/edition158653 (рус. пер. с 3-го изд.: восемь, есть «Союзник») | исправлено | семь — это 1-е и 2-е издания самой книги, а не «пересказы» |
| 119 | vogler | «Содержательных описаний самого Воглера в источниках нет — только названия» | сайт Воглера (Heralds, Threshold Guardians, Shapeshifters, Allies…); https://en.wikipedia.org/wiki/The_Writer%27s_Journey:_Mythic_Structure_for_Writers (однострочные описания по 3-му изд.) | исправлено | добавлены определения |
| 120 | vogler | Связь Вестника с зовом — «оценка исследования» | сайт Воглера: «One who brings the Call to Adventure» | исправлено | это слова Воглера; привязка Стража к первому порогу осталась оценкой |
| 121 | vogler | Связь Оборотня с романтическим интересом ⚠ | сайт Воглера: «The opposite sex, the way people can be two-faced» | помечено ⚠ (уточнено) | связь с противоположным полом подтверждена; ⚠ — только на «любовную линию» |
| 122 | vogler, guide | Меморандум: 7 страниц, «середина 1980-х», дата 1985 ⚠ | сайт Воглера («written in the mid-1980s»; шапка «© 1985»); https://en.wikipedia.org/wiki/Christopher_Vogler | подтверждено | ⚠ снят |
| 123 | vogler | «По словам самого Воглера», меморандум «went viral… by fax machines» и привёл его к «Королю Льву» | https://networkisa.org/creative-screenwriting/view/know-the-paradigm-break-the-paradigm-christopher-vogler (WebFetch) | исправлено | факс — цитата Воглера; «Король Лев» — изложение интервьюера |
| 124 | vogler | Меморандум повлиял на «Красавицу и чудовище», «Аладдина», «Короля Льва» | https://en.wikipedia.org/wiki/The_Hero_with_a_Thousand_Faces | подтверждено | — |
| 125 | vogler, guide | В статье «Hero's journey» 1998 год «ошибочно» указан как год первого издания | викитекст https://en.wikipedia.org/wiki/Hero%27s_journey: «date=2007, orig-year=1998» у книги «…Mythic Structure For Writers» | исправлено | формулировка смягчена: 1998 — год 2-го изд., когда появилось это название |
| 126 | vogler | Как в переводе названы Herald, Threshold Guardian, Shapeshifter, Ally ⚠ | https://fantlab.ru/edition158653 (оглавление: «Привратники», «Вестник», «Оборотень», «Союзник», «Плут») | подтверждено | ⚠ снят; «Страж порога» и «Глашатай» обозначены как варианты исследования |
| 127 | vogler, guide | 12 стадий; 4-я — встреча с наставником; 6-я — «Tests, Allies, Enemies» | Wikipedia; Фантлаб («Стадия четвертая. Встреча с наставником») | подтверждено | — |
| 128 | guide | Кэмпбелл: Supernatural Aid — 3-я из 17 стадий (1949, p. 38) | викитекст «Hero's journey» (таблица; «sfn Campbell 1949 p=38») | подтверждено | — |
| 129 | guide | Рус. Википедия: «при помощи наставника» | https://ru.wikipedia.org/wiki/Тысячеликий_герой | подтверждено | — |
| 130 | guide | Юнг о Мудром старце: §398 (образы), §414 («wicked aspect too»), §415 | OL («the old man has a wicked aspect too» — «Four Archetypes» и др.) | подтверждено | формулировка §414; §§398, 406, 415 — по r01 |
| 131 | guide | SB7; «The customer is the hero, not your brand»; Йода и Гэндальф; эмпатия и авторитет | https://grahammann.net/book-notes/building-a-storybrand-donald-miller | подтверждено | — |
| 132 | guide | Сертификация «StoryBrand Certified Guide» | https://storybrand.com/ | подтверждено | — |
| 133 | guide | Русский перевод: «Метод StoryBrand», Альпина Паблишер, 2020, пер. Е. Виноградовой; guide = «проводник» | https://alpinabook.ru/catalog/book-metod-storybrand/ (аннотация: клиент — «героем», компания — «проводником»; год выпуска 2020); https://www.litres.ru/book/donald-miller/metod-storybrand-…-51373655/ (переводчик Е. Виноградова, ISBN 978-5-9614-3369-2) | подтверждено | Литрес добавлен как [24] |
| 134 | guide | Цитаты перевода «клиенты ищут не другого героя, а проводника», «проводник или наставник» — по «конспекту» alexeykrol.com | https://alexeykrol.com/blog/2022/01/20/87687612321/ — около 8 400 слов, по сути дословный текст перевода | удалено (ссылка) | ссылка удалена по правилу о неавторизованных копиях; цитаты оставлены с ⚠ и пояснением |
| 135 | guide | «Метод StoryBrand 2.0», пер. Л. Макариной | https://books.yandex.ru/books/PiCWF7Yo | подтверждено | — |
| 136 | guide | Воглер по-русски: Альпина нон-фикшн, 2015, пер. М. Николенко; «Наставник: умудренный жизнью человек» | https://fantlab.ru/edition158653 | подтверждено | перевод сделан с 3-го изд. |
| 137 | guide | Iconic Fox: Мудрец «more likely to pass on their wisdom…»; Герой — «inspire them and make them feel empowered to succeed and achieve» | https://iconicfox.com.au/brand-archetypes/ | подтверждено | — |
| 138 | guide | Пилиповец: «Наставник» — подархетип Мудреца | mybusiness.by («Мудрец… Аналитик… Наставник — ведёт и обучает») | подтверждено | — |
| 139 | guide | Uprock: Мудрец как «компетентный проводник» ⚠ (по сниппету) | https://www.uprock.ru/articles/arhetipy-sozdaem-zapominayushchiysya-brend (со второй попытки) | подтверждено | ⚠ снят, цитата уточнена |
| 140 | guide | Аркан 9: дар наставничества, «наставником особого рода»; слова «проводник» нет | https://astroguru.ru/matrica-sudby/arkan-9 ; https://matrica-sudby.ru/matrix/9-arkan-v-matrice-sudby.html | подтверждено | — |

### 2.4. README и решения по пограничным случаям

Пункты README пронумерованы отдельно (R1–R8), чтобы не смешивать их с карточками.

| № | файл | утверждение | чем проверено (URL) | вердикт | комментарий |
|---|---|---|---|---|---|
| R1 | README | Все 12 брендовых карточек (`01-innocent.md` … `12-ruler.md`) и 12 файлов `extra-…` существуют под указанными именами; ссылки на `../01-systems.md`, `../06-esoteric-links.md`, `../_notes/` работают | `ls` и скрипт проверки относительных ссылок | подтверждено | новая ссылка — на этот протокол |
| R2 | README | Части II–V и их состав; Part II — с. 49, Part III — с. 101; Sage — гл. 6, с. 88 | OL (оглавление M&P 2001: «Part II The Yearning for Paradise: Innocent, Explorer, Sage 49…», «Part III Leaving a Thumbprint on the World: Hero, Outlaw, Magician 101», «Chapter 6 The Sage 88») | подтверждено | — |
| R3 | README | Названия частей и архетипов у «Бомборы»: «В поисках рая», «Оставить след в этом мире», «Один в поле не воин», «Упорядочить мир»; Дитя, Служитель | https://cdn.eksmo.ru/v2/ITD000000001500651/PDF/ITD000000001500651_TOC.pdf | подтверждено | — |
| R4 | README | Таблица «полюс мотивации → часть → архетипы» | п. 49 и R2 | исправлено | полюс «Belonging/People» без ⚠; соотнесение частей с полюсами по-прежнему помечено ⚠ как вывод по названиям |
| R5 | README | Xara-Brasil и соавт. (2018): группа «risk and mastery», четыре «human drivers» | https://revistas.usp.br/rege/article/download/147500/141030/297554 (CC BY 4.0: «four human main drivers: "belonging and enjoyment," "independence and fulfillment"…», «Risk and Mastery»); Crossref | подтверждено | цитата уточнена; DOI → 403, добавлена ссылка открытого доступа |
| R6 | README | Hartwell & Chen: «belonging, stability, mastery and self-actualization» | https://www.archetypesinbranding.com/ (со второй попытки; с первой — 429) | подтверждено | — |
| R7 | README | I-am-Brand: четыре группы | https://i-am-brand.ru/knowledge-base/arhetipy-v-lichnom-brende/ | подтверждено | — |
| R8 | README | Легенда пометок | сверка с пометками в 12 файлах | подтверждено | все использованные пометки описаны в легенде |
| R9 | trickster, great-mother, child, guide | Решения по пограничным случаям: Трикстер ≠ Шут, Великая Мать ≠ Заботливый, Дитя у Мисс ≠ Простодушный, Проводник ≠ Мудрец | опоры проверены выше: §472 (бессознательность), §485 (связь с тенью), PMAI и Ebaq (смешение с Шутом); §158 (биполярность), VisionOne и Putnam; Галерея (7 вариантов, «Magical (innocent…)»), сайт Пирсон (Orphan → Regular Guy) | подтверждено | везде, кроме Проводника, решение помечено «Это решение исследования»; в карточке Проводника пометка добавлена |
| R10 | 7 файлов | Таро-связки даны только со ссылкой на `06-esoteric-links.md`, новых нет | сверка с таблицей §2.1 в 06 (Nichols, OLLI, Sargent, Wang, Kerykeion, Avia Venefica, Davidson, Illumina, b17, матрица) | подтверждено | в разделах 7 карточек Анимы, Самости, Великой Матери и Трикстера, где связки упомянуты повторно, добавлены ссылки на 06 |

## 3. Проверка URL

Доступ проверен 2026-10-16: curl через прокси, при отказе — WebFetch. «Подтверждает» означает, что на странице найдено то, ради чего на неё ссылается карточка. Файлы указаны без префикса `extra-`.

| № | URL | где | доступ | подтверждает | действие |
|---|---|---|---|---|---|
| 1 | https://affordanything.com/episode184 | persona | 403 (curl и WebFetch) | не проверено | ⚠ «ссылка недоступна на 2026-10-16» |
| 2 | https://alinaadt.ru/masterarchetype | shadow | 200 | да | — |
| 3 | https://alpinabook.ru/catalog/book-metod-storybrand/ | guide-mentor | 200 | да (2020, «проводник») | описание уточнено |
| 4 | https://arhetipium.ru/idealist | shadow | 200 | да | — |
| 5 | https://arhetipium.ru/mag | self | 200 | да | — |
| 6 | https://arhetipium.ru/mudrec | shadow | 200 | да | — |
| 7 | https://arhetipium.ru/slavniy-malyi | shadow | 200 | да | — |
| 8 | https://arhetipium.ru/workshop-bit-soboi-v-bloge | shadow | 200 | да | — |
| 9 | https://ast.ru/book/glubinnye-arkhetipy-…-876582/ | myss-child | 500 (curl и WebFetch) | только по поисковой сводке | добавлен [20] с ⚠ |
| 10 | https://astroguru.ru/matrica-sudby/arkan-9 | guide-mentor | 200 | да | — |
| 11 | https://avidreader.com.au/p/archetype-cards | myss-child | 200 (WebFetch) | да (72 + 6) | добавлен [18] |
| 12 | https://bigredjelly.com/blog/what-is-storybrand-… | guide-mentor | 200 | да (SB7) | метка «по поисковой сводке» снята |
| 13 | https://blog.mann-ivanov-ferber.ru/2024/07/23/temnye-storony-… | shadow, saboteur, victim | 200 | да | — |
| 14 | https://bonniesorsby.com/how-to-use-shadow-work-to-strengthen-your-brand/ | shadow, saboteur | 200 | да | — |
| 15 | https://books.yandex.ru/books/PKGjPsYP/read-online | great-mother, trickster | 200 | да | — |
| 16 | https://books.yandex.ru/books/PiCWF7Yo | guide-mentor | 200 | да | — |
| 17 | https://carolspearson.com/about/the-pearson-12-archetype-system-… | myss-child, victim | 200 | да | — |
| 18 | https://cdn.eksmo.ru/v2/ITD000000001500651/PDF/ITD000000001500651_TOC.pdf | great-mother, myss-child, README | 200 (одна попытка — сброс соединения) | да | — |
| 19 | https://content.e-bookshelf.de/media/reading/L-18717667-86f49bf70f.pdf | great-mother, trickster | 200 | да | — |
| 20 | https://content.e-bookshelf.de/media/reading/L-535049-ae25abbe32.pdf | myss-child, prostitute, saboteur, victim | 200 | да (оглавление, 12 домов) | добавлен в 4 файла |
| 21 | https://cyberleninka.ru/article/n/mifodizayn-kak-sotsiokulturnyy-fenomen | anima, great-mother, myss-child, shadow | 200, но страница-капча «Вы точно человек?» | содержимое не проверено | без изменений: защита от ботов, а не битая ссылка |
| 22 | https://discovery-pp.ucl.ac.uk/10134044/1/Wu_s41467-020-18539-w.pdf | persona | 403 (curl и WebFetch) | — | ⚠ + DOI |
| 23 | https://doi.org/10.1002/mar.20203 | guide-mentor | DOI работает, сайт издателя — 403 | библиография — да (Crossref) | без изменений |
| 24 | https://doi.org/10.1038/s41467-020-18539-w | persona | DOI работает (Nature требует вход) | да (Crossref, Europe PMC) | добавлен |
| 25 | https://doi.org/10.1108/REGE-02-2018-0029 | README | DOI работает, сайт Emerald — 403 | да (Crossref) | ⚠ + ссылка открытого доступа |
| 26 | https://en.wikipedia.org/wiki/Archetypal_psychology | self | 200 | да | — |
| 27 | https://en.wikipedia.org/wiki/Christopher_Vogler | guide-mentor, vogler-roles | 200 | да | — |
| 28 | https://en.wikipedia.org/wiki/Erich_Neumann_(psychologist) | great-mother | 200 | да (1955/1956) | ⚠ снят |
| 29 | https://en.wikipedia.org/wiki/Hero%27s_journey | guide-mentor, vogler-roles | 200 | да; «ошибка 1998» не подтвердилась | формулировка смягчена |
| 30 | https://en.wikipedia.org/wiki/Jungian_archetypes | anima, persona | 200 | частично (другая формулировка) | цитата исправлена |
| 31 | https://en.wikipedia.org/wiki/The_Hero_with_a_Thousand_Faces | shadow, vogler-roles | 200 | да | — |
| 32 | https://en.wikipedia.org/wiki/The_Jung_Cult | self | 200 | да | — |
| 33 | https://en.wikipedia.org/wiki/The_Writer%27s_Journey:_Mythic_Structure_for_Writers | guide, shadow, trickster, vogler | 200 | да (8 архетипов по 3-му изд., 12 стадий, издания) | — |
| 34 | https://fantlab.ru/edition158653 | guide, trickster, vogler | 200 | да (+ русские названия) | добавлен в trickster |
| 35 | https://grahammann.net/book-notes/building-a-storybrand-donald-miller | guide-mentor | 200 | да | — |
| 36 | https://i-am-brand.ru/knowledge-base/arhetipy-v-lichnom-brende/ | README | 200 | да | — |
| 37 | https://iconicfox.com.au/brand-archetypes/ | guide-mentor | 200 | да | — |
| 38 | https://ijoc.org/index.php/ijoc/article/view/11729 | persona | 200 | частично (о «самоцензуре» в аннотации нет) | исправлено |
| 39 | https://jessicadavidson.co.uk/2014/07/09/tarot-heros-journey-the-magician/ | trickster | 200 | да | — |
| 40 | https://jobcannon.io/ru/tests/jungian-archetype | shadow | 200 | да (цитата была составной) | исправлено |
| 41 | https://kayeputnam.com/brand-archetypes/caregiver | great-mother | 200 | да | — |
| 42 | https://kerykeion.net/content/learn-tarots/psychology/jung-and-tarot | anima, persona, self, shadow | 200 | да | — |
| 43 | https://liveencounters.net/?p=10396 | saboteur | 200 | частично | ⚠ на «неудобную правду» |
| 44 | https://matrica-sudby.ru/matrix/9-arkan-v-matrice-sudby.html | guide-mentor | 200 | да | — |
| 45 | https://mavericksandmalbec.substack.com/p/the-saboteur-self-sabotage-and-a | saboteur | 200, платный доступ (запись от 24.04.2026) | нет | ⚠ |
| 46 | https://mybusiness.by/2026/tpost/archetypes-founder-business | guide, persona | 200 | да | цитата уточнена |
| 47 | https://myss.com/the-prostitute-the-power-of-archetypes/ | prostitute | 200 | да | ⚠ снят |
| 48 | https://myss.com/wp-content/uploads/2015/07/Gallery-of-Archetypes.pdf | 4 файла Мисс | 200 | да | исправлены разделы 6 |
| 49 | https://networkisa.org/creative-screenwriting/view/know-the-paradigm-… | vogler-roles | curl — 403, WebFetch — 200 | да (fax); «Король Лев» — изложение интервьюера | исправлено |
| 50 | https://press.princeton.edu/books/paperback/9780691163598/… | great-mother | curl — 403, WebFetch — 200 | да | — |
| 51 | https://press.princeton.edu/books/paperback/9780691166070/the-great-mother | great-mother | curl — 403, WebFetch — 200 | да | — |
| 52 | https://publishersweekly.com/9780517703922 | 4 файла Мисс | 200 | да | — |
| 53 | https://publishersweekly.com/9781401941086 | myss-child | 200 | частично (10 архетипов) | — |
| 54 | https://rascl.studentorg.berkeley.edu/assets/files/self-talk_….pdf | persona | 200 | да | — |
| 55 | https://revistas.usp.br/rege/article/view/147500 | README | 200 (PDF) | да | добавлен |
| 56 | https://ru.wikipedia.org/wiki/Тысячеликий_герой | guide-mentor | 200 | да | — |
| 57 | https://search.icpl.org/Record/1206155 | 4 файла Мисс | 403 (curl и WebFetch) | — | ⚠ + фрагмент издателя |
| 58 | https://skillbox.ru/media/design/archetypes-in-simple-words/ | great-mother | 200 | да | — |
| 59 | https://snob.ru/profile/406294/blog/3095455/ | persona, shadow | 200 | да | пересказ в Персоне уточнён |
| 60 | https://storage.piter.com/upload/contents/978544611928/978544611928_X.pdf | anima, great-mother, shadow, trickster | 200 | да | — |
| 61 | https://storybrand.com/ | guide-mentor | 200 | да | — |
| 62 | https://stuff.mit.edu/afs/athena.mit.edu/user/m/b/mbarker/www/exercises/exer981026.txt | guide, trickster, vogler | 200 | да (+ 7 архетипов, p. 36) | исправлено |
| 63 | https://t-j.ru/mif-kak-metod/ | guide, trickster | 200 | да | — |
| 64 | https://teletype.in/@katyagas/czNfmod6BTZ | great-mother, guide, child | 200 | да (пунктуация цитат была иной) | исправлено |
| 65 | https://tenchat.ru/media/3750005-… | persona | 200 (с первой попытки — сброс соединения) | да | — |
| 66 | https://valsec.barnesandnoble.com/w/archetype-cards/caroline-myss/1005803894 | myss-child | ошибка шлюза 502 | — | ⚠ + [17][18] |
| 67 | https://vc.ru/1129215-chto-ne-tak-s-arhetipami | persona | 200 | да | — |
| 68 | https://visionone.co.uk/brand-archetype-quiz/the-caregiver-brand-archetype/ | great-mother | 200 | да | — |
| 69 | https://web.archive.org/web/20161028170951/http://www.thewritersjourney.com/hero's_journey.htm | guide, shadow, trickster, vogler | 200 | да | добавлен (живой сайт сбрасывает соединение) |
| 70 | https://www.abebooks.com/9780971559110/… | great-mother | 200 | да | — |
| 71 | https://www.archetypesinbranding.com/ | README | 429, после повтора 200 | да | — |
| 72 | https://www.b17.ru/article/739217/ | great-mother, trickster | 503 (дважды) | — | ⚠ «ссылка недоступна» (trickster) |
| 73 | https://www.books2door.com/products/9781401901844 | myss-child | 200 (WebFetch) | да (80) | добавлен [17] |
| 74 | https://www.ebaqdesign.com/blog/brand-archetypes | trickster | 200 | да | — |
| 75 | https://www.goodreads.com/author_blog_posts/23489082-… | shadow, vogler | 200 | да | — |
| 76 | https://www.goodreads.com/book/show/91781 | myss-child, trickster | 200 | да (заметки читателей) | ⚠ сохранён |
| 77 | https://www.litres.ru/book/anna-sharlay/arhetipy-i-obrazy-64468643/chitat-onlayn/ | great-mother | 200 | да | — |
| 78 | https://www.litres.ru/book/carol-s-pearson-2/probuzhdenie-vnutrennego-geroya-…/chitat-onlayn/ | saboteur | 200 | да | — |
| 79 | https://www.litres.ru/book/donald-miller/metod-storybrand-…-51373655/ | guide-mentor | 200 | да | добавлен [24] |
| 80 | https://www.penguinrandomhouse.com/books/601468/archetypes-by-caroline-myss/9781401941109 | myss-child | 200 | да | — |
| 81 | https://www.psychceu.com/jung/sharplexicon.html | anima, great-mother, myss-child, persona, self, shadow | 200 | да | основной инструмент сверки |
| 82 | https://www.psychologytoday.com/us/blog/the-seekers-forum/202408/which-archetypes-are-you-living | myss-child, persona, shadow | 200 | да | — |
| 83 | https://www.sostav.ru/blogs/288649/93766 | persona | 200 | да | — |
| 84 | https://www.storywell.com/archetypes/archetype-descriptions.htm | trickster | 200 | да (alt-текст) | — |
| 85 | https://www.tarotteachings.com/?p=2602 | guide, self, shadow | 200 | да | — |
| 86 | https://www.uc.edu/content/dam/refresh/cont-ed-62/olli/22-winter/jung%20tarot%201.pdf | 6 файлов | 200 | да | — |
| 87 | https://www.uprock.ru/articles/arhetipy-sozdaem-zapominayushchiysya-brend | guide-mentor | сброс соединения, после повтора 200 | да | ⚠ снят |
| 88 | https://alexeykrol.com/blog/2022/01/20/87687612321/ | guide-mentor (была) | 200 | дословный текст перевода (~8 400 слов) | **ссылка удалена** |
| 89 | https://openlibrary.org/search/inside.json?q=… | — | 200 | инструмент (сниппеты) | — |
| 90 | https://api.crossref.org/works/… (4 DOI) | persona, guide, README | 200 | да | — |
| 91 | https://www.ebi.ac.uk/europepmc/webservices/rest/search?query=DOI:10.1038/s41467-020-18539-w | persona | 200 | да | — |
| 92 | https://www.thewritersjourney.com/ | — | сброс соединения (3 попытки) | — | заменён архивной копией (п. 69) |
| 93 | https://www.goodreads.com/author_blog_posts/15285072-how-to-casting-your-sacred-contracts-chart-of-origin | — | 200 | названий домов нет | не использован |
| 94 | https://www.nature.com/articles/s41467-020-18539-w | — | перенаправление на вход | — | не использован; взят DOI |

## 4. Соблюдение правил

| Правило | Результат |
|---|---|
| Цитаты не длиннее ~25 слов | Скрипт по «» и "" во всех 13 файлах: ни одной цитаты длиннее 22 слов. Новые цитаты проверки — не длиннее 15 слов |
| Нет ссылок на неавторизованные копии | Найдено одно нарушение: «конспект» alexeykrol.com с дословным текстом перевода StoryBrand — ссылка удалена. Ссылки на копии CW с archive.org из r01 в карточки не попали. Книги указаны по изданиям |
| Неподтверждённое помечено ⚠ | Новая ⚠ — в 20 местах: 15 недоступных ссылок и 5 формулировок (состав колоды Мисс, «неудобная правда» Саботажника — 2 места, цитаты перевода StoryBrand, «хранитель самоуважения» у Жертвы). Снято 18 ⚠ после подтверждения: Belonging/People (3), ключевой вопрос Проститутки (3), низкая самооценка Саботажника (1), год Нойманна (1), p. 34/36 (4), дата меморандума (2), русские названия Воглера (1), Uprock (2), отсутствие подзаголовка у Жертвы (1) |
| Собственные выводы помечены «оценка исследования, не из источника» | Соблюдено. Добавлена пометка к решению в карточке Проводника. Два утверждения, ошибочно поданные как оценка, оказались из источника и переведены в «из источников»: Питер Пэн у Мисс, связь Вестника с зовом у Воглера |
| Номера [n] соответствуют спискам | После правок скрипт не нашёл ни пропущенных номеров, ни неиспользованных источников, ни разрывов нумерации. Новые источники добавлены в конец: shadow [21]; trickster [16]–[17]; myss-child [16]–[20]; victim [9]; prostitute [6]; saboteur [11]; guide-mentor [22]–[24]; vogler-roles [11]–[12]; README [7] |
| Таро — только со ссылкой на 06, без новых связок | Все упоминания совпадают с таблицей §2.1 файла 06. Новых связок нет. Добавлены ссылки на 06 в разделах 7, где связки повторялись без ссылки |

## 5. Сводка

**Объём.** Проверено 140 утверждений (91 — юнгианские карточки, 25 — Мисс, 24 — Воглер и StoryBrand) и 10 пунктов README и сквозных правил. Проверено 94 URL: 87 из файлов и 7 служебных.

**Вердикты по 140 утверждениям:**

| Вердикт | Число |
|---|---|
| подтверждено | 104 |
| исправлено | 29 |
| помечено ⚠ | 6 |
| удалено | 1 |

Ещё 10 пунктов (R1–R10, README и сквозные правила): 9 подтверждено, 1 исправлено (R4 — таблица). В R9 и R10 добавлены недостающие пометка и ссылки.

**Главные исправления:**
1. **Анима — формы Коры.** «Unknown young girl», танцовщица, менада, нимфа, никса — у Юнга это формы Коры **в женской психологии** (CW 9i §311: «the Kore often appears in woman as…»). В карточке они были поданы как формы анимы у мужчины.
2. **Самость — индивидуация.** «Естественная трансформация (индивидуация)» — это §234, подпункт h раздела «Subjective Transformation». В карточке было «перечень форм перерождения, §§199–219».
3. **Мисс — примеры.** В Галерее у Дитя (по вариантам), Жертвы, Проститутки и Саботажника есть списки примеров из кино, литературы и мифов, а карточки утверждали «в источниках не найдено». Питер Пэн — пример самой Мисс, а не оценка исследования.
4. **Воглер — семь архетипов.** В 1-м (1992) и 2-м (1998) изданиях главных архетипов семь, без Союзника; восемь — с 3-го изд. (2007). «Семь» — это не ошибка пересказов.
5. **Воглер — описания функций.** Собственные описания Воглера (сайт, архив 2016) существуют, вопреки «только названия». Вестник у него прямо связан с зовом, Оборотень — с противоположным полом, Тень — и с «enemy within».
6. **Официальные русские названия Воглера** (перевод с 3-го изд.): Привратники, Вестник, Оборотень, Союзник, Плут.
7. **README и Анима — ось Марк и Пирсон.** Полюс «Belonging/People» подтверждён по тексту книги, ⚠ снят.
8. **Удалена ссылка на «конспект»** StoryBrand, дословно воспроизводящий перевод. Перевод и слово «проводник» подтверждены по страницам «Альпины» и Литреса.
9. **Точечные уточнения:**
   - CW 7 §246 → §§245 сл.;
   - CW 6 §801 — слова Юнга, а не Шарпа;
   - «personality systems» → «separate systems of the personality»;
   - цитаты Пилиповец, Гас, JobCannon, Duffy & Hund, Solomon («To belong and fit in»);
   - год Нойманна — не противоречие;
   - «ошибка 1998» в Википедии — смягчено.

**Осталось под ⚠ (или не перепроверено):**
- **Юнг.**
  - CW 7, CW 6, CW 12 и CW 11 сверены только по Шарпу.
  - Номер ≈§9 в Aion и §469/470 в CW 9i.
  - Формулировки подтверждены, но номера взяты из r01 и независимо не сверены: Aion §§13, 26, 35, 59–60; CW 9i §§43, 45, 60, 155–157, 306, 398, 406, 415, 469, 487; CW 5 §§395, 459. Отдельной пометки ⚠ в карточках у них нет, это остаточный риск.
- **Карточки Юнга, прочее.** Автор и название книги «Питера»; тени у Мура и Жиллетта (только по отзывам); Херман и Бейонсе (ссылка 403); постъюнгианская критика пола (Хиллман и др.) не изучена.
- **Мисс.** Названия и смысл 12 домов колеса; число архетипов в приложении к книге 2001 г. («более 70» — по вторичному источнику); состав колоды (80 / 72 + 6 / 74 + 6); русское издание и русские названия; «хранитель самоуважения»; «защищает от неудобной правды».
- **Воглер и StoryBrand.** Связь Оборотня с любовной линией; происхождение SB7; академическая критика Воглера; формулировки русского перевода StoryBrand сверены только по выдержке в блоге; год оригинала «StoryBrand 2.0».
- **Недоступные ссылки на 2026-10-16:** ICPL (403), affordanything (403), UCL (403), B&N (502), b17 (503), AST (500); Substack за платным доступом. Содержимое cyberleninka не проверено: страница-капча.

**Рекомендации (вне объёма правок).**
- Сверить по печатному CW 9i номера, подтверждённые только через r01, и CW 7 / CW 12 — помимо Шарпа.
- Проверить, не повторяют ли брендовые карточки и `01-systems.md` утверждения «у Воглера 8 архетипов», «у Воглера Тень — не внутренняя часть героя» и «примеров у Мисс нет».
