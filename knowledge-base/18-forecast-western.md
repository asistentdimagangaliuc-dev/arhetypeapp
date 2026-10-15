# 18. Западная прогностика: транзиты, прогрессии, дирекции, соляр, профекции

> Модуль: `calculators/forecast_western.py` (`calculate(b, **options)`), тесты: `calculators/tests/test_forecast_western.py`.
> Python: `calculate(BirthInput(1990, 5, 15, 14, 30, place="Москва"), on_date="2026-10-14")`.
> CLI (пока метод не внесён в общий `calculators/cli.py`): `.venv/bin/python -m calculators.forecast_western --date 1990-05-15 --time 14:30 --place Москва --opt on_date=2026-10-14 [--opt sr_place=Новосибирск --opt progression_angles=solar_arc --opt progression_direction=converse --opt profection_month=calendar --opt primary_directions=true --opt exact_window_years=30]`.
> Натальная карта берётся из модуля 06 (`calculators/western.py`): те же время, дома, узел, аспекты и таблицы.

**Коротко для агента.** Прогноз всегда считается **на конкретную дату** `on_date` — назовите её пользователю. Пять техник отвечают на разные вопросы: **транзиты** — какие реальные планеты сейчас (и в периоде) касаются натальных точек; **вторичные прогрессии** («день = год») — медленное внутреннее развитие, прежде всего прогрессивная Луна и фаза прогрессивной лунации; **дирекции солнечной дуги** — все точки радикса сдвинуты на дугу Солнца; **соляр** — карта на момент возврата Солнца к натальной долготе (на год вперёд); **годовые профекции** — знак года и управитель года (эллинистическая техника). Числа берите из калькулятора; формулы ниже нужны для проверки и объяснения. Точные моменты транзитов ищутся с учётом ретроградных петель: один аспект медленной планеты может стать точным **трижды** — называйте все проходы. По запросу (опции, умолчания не меняют): конверсные вторичные прогрессии, первичные дирекции планет к углам, варианты месяцев профекции, расширенное окно поиска точных дат прогрессий и дирекций.

---

## 1. Суть и школы

### 1.1. Техники

| Техника | Что это | Единица времени | По умолчанию |
|---|---|---|---|
| **Транзиты (transits)** | Реальные положения планет на дату и их аспекты к натальным точкам. «Транзит действует», пока аспект в орбисе; важнее всего момент, когда он **точный** | реальное время | орбис 1° для всех транзитов (astro.com, Р. Хэнд); мажорные аспекты; точные моменты в периоде — для Марса…Плутона |
| **Вторичные прогрессии (secondary progressions)** | Карта на момент «через N суток после рождения», где N — возраст в годах: 1 сут после рождения ≈ 1 год жизни (astro.com: «At 30 years of age, a chart is calculated for the 30th day after birth») | 1 сут эфемерид = 1 год | год = 365,24219 сут; углы — `mean_sun` (ключ Наибода в ARMC, как astro.com); орбис 1° |
| **Дирекции солнечной дуги (solar arc directions)** | Все точки радикса сдвигаются на одну и ту же дугу — путь прогрессивного Солнца от рождения (AstroWiki: «All the planets and axes are moved by the same amount as the sun moves in one day») | ≈1° в год | истинная дуга; орбис 1°; ASC + дуга |
| **Соляр (solar return, солнечная революция)** | Карта на момент, когда Солнце возвращается к своей натальной долготе; действует до следующего соляра | 1 год | тропический; место рождения; Плацидус |
| **Лунар (lunar return)** | То же для Луны: возврат к натальной долготе Луны раз в ~27,3 сут | 1 мес. | на место соляра |
| **Годовые профекции (annual profections)** | От знака ASC отсчитывается по знаку на каждый прожитый год; управитель полученного знака — «управитель года» (time-lord) | 1 знак = 1 год | от ASC, целые знаки, традиционные управители, смена года в момент соляра; месяц — 1/12 года (`profection_month`) |
| **Первичные дирекции к углам (primary directions)** — по запросу | Планета (промиссор) переносится суточным вращением неба до MC, IC, ASC или DSC радикса; дуга в прямом восхождении переводится в годы «ключом» | 1° RA ≈ 1 год | выключены (`primary_directions=True`); со своей широтой (in mundo); ключ Наибода; до 100 лет |

### 1.2. Расхождения школ и вариантов

**Транзиты — орбис.** Единого орбиса нет (AstroWiki «Transit»: «It is not possible to give a definite answer…»).
- astro.com: отчёты Роберта Хэнда (Extended Daily Horoscope, Transits of the Year, Astrotext Forecast) — «an orb of 1° for all transits to all natal planets» (FAQ «Forecast Horoscopes»). Лиз Грин — «a more complex system which considers different factors, such as pre-orb / post-orb, aspect type, and the planets involved. It would be too complex to list all the orbs individually… her orbs are generally wider»; там же: «We do not publish the logic behind our calculations and interpretations». ⚠ Таблица орбисов Грин не опубликована — воспроизвести её нельзя (повторный поиск 15.10.2026 ничего не дал); для «широких» орбисов задавайте `transit_orbs` числом или словарём и называйте это вариантом.
- Р. Хэнд, «Planets in Transit» (1976), Transit Rule 2: «Strictly speaking, there is no such thing as an "orb" of influence concerning a transit… Space can be converted into time, because the transiting planet is moving, so an orb of so many degrees and minutes indicates the length of time in which a transit is likely…»; его компьютерный отчёт в той же книге даёт для каждого транзита «the date it enters one degree of orb, the date it becomes exact» — это и есть умолчание 1°.
- AstroWiki «Transit»: «The initial recommendation is to use a small orb of around one degree… The orb can then be increased to three or five degrees».
- Kerykeion (вторичный): для внешних планет «1 to 3 degrees is usually sufficient», для внутренних — «within 1 degree or less».
- **Период действия**: astro.com «Transits of the Year» считает транзит активным «from the first entry into orb up to the last exit» (с учётом ретроградной петли), а «Astrotext Forecast» — только пока планета в орбисе 1° (транзит прерывается и возобновляется). FAQ: «What is really reliable is the date when a transit is exact». Поэтому калькулятор выдаёт **все точные моменты** с номером прохода, а длительность оставляет на выбор школы.

**Прогрессии — длина года и момент.** Возраст в годах переводится в сутки эфемерид. В Astrolog год = `rDayInYear` = 365,24219 сут (тропический год; `astrolog.h`); вариант `year_length="julian"` (365,25) сдвигает прогрессивный момент на ~1,5 мин к 50 годам — пренебрежимо. astro.com считает прогрессии **на полночь UT** целевой даты (FAQ «Calculations»: «The progressed charts are calculated for midnight Universal Time»); калькулятор так же трактует `on_date` без времени.

**Прогрессии — углы (ASC, MC, куспиды).** Это главное расхождение программ:

| `progression_angles` | Формула | Кто использует |
|---|---|---|
| `mean_sun` (**по умолчанию**) | ARMC_p = ARMC_рожд + 0,98564733° × возраст; ASC, MC и куспиды пересчитываются из ARMC_p | astro.com: «the number of years is multiplied by the mean daily motion of the Sun… added to the sidereal time of birth, and axes and houses are recalculated… ('Naibod key') 0.98564733°»; AstroWiki: «The most common method…» (3 мин 56,55 с звёздного времени в год) |
| `solar_arc` | MC_p = MC_рожд + (Солнце_прогр − Солнце_рожд) в долготе; ASC и куспиды — из MC_p на широте рождения | Solar Fire (по описанию astro.com FAQ: «Solar Fire calculates them as follows: The solar arc… is added to the midheaven»); Astrolog 8 — ключи `-p1 -pc` («Solar arc house cusps recomputed based on progressed MC», `charts0.cpp`); на astro.com — опция «MC from solar arc». ⚠ Что это **умолчание** Solar Fire, известно только из FAQ astro.com: руководство Solar Fire не найдено (повторный поиск 15.10.2026) |
| `naibod` | MC_p = MC_рожд + 0,98564733° × возраст в **долготе** | «Naibod in Longitude» — один из пяти способов в руководстве Astracadabra v1 (© 2004–2008 Esoteric Technologies, производитель Solar Fire): «S.A. in Long., S.A. in R.A., Naibod in Longitude, Naibod in Right Ascension and Mean Quotidian»; есть и в Solar Fire («Solar Fire currently has Naibod in longitude and r.a., and solar arc in long. and r.a.» — Astrolog32 Wish List); К. Б. Риске (Llewellyn's Complete Book of Predictive Astrology, 2011): «I have found that angles progressed by Naibod in longitude are the most accurate» |
| `solar_arc_ra` | ARMC_p = ARMC_рожд + (α_Солнца_прогр − α_Солнца_рожд) | «Solar Arc in R.A.» — те же источники (Astracadabra, Solar Fire) |
| `quotidian` | карта на сам прогрессивный момент: ARMC растёт на ~361° за прогрессивные сутки (= за год жизни) | astro.com: опция «ARMC 361° / prog. Day»; **умолчание Astrolog 8** (`-p`: куспиды строятся на момент `is.Tp = T + (JDp − T)/(rProgDay·rProgCusp)`, `-pC` по умолчанию 1,0 — `calc.cpp`, `charts0.cpp`) |

astro.com подчёркивает: способы через ключ Наибода и солнечную дугу «strictly speaking… are not real secondary progressions, but primary directions» углов. На вопрос «Can I set a progressed chart to use SA (solar arcs) in Longitude method?» FAQ «Other methods» отвечает «No»: на astro.com прогрессивные углы — только ARMC + 3m56s в год. «The original Astrolog only progressed the MC in a secondary using Naibod right ascension» (Astrolog32 Wish List) — это наш `mean_sun`; в Astrolog 8 по умолчанию уже `quotidian`.

**Прогрессивные углы — наклон эклиптики ε** (`progression_obliquity`). По умолчанию истинный ε на прогрессивный момент JD_p (`"progressed"`); вариант `"natal"` — ε рождения, как в Astrolog 8 для куспидов от направленного MC (`-p1 -pc`: `SwissHouse(is.Tp, …)` с `is.Tp` = время рождения; `calc.cpp`). Для `quotidian` всегда ε прогрессивного момента (это настоящая карта на этот момент). Разница — секунды дуги (T4: ASC 0,2″), на даты срабатывания не влияет. ⚠ Какой ε берёт astro.com, не опубликовано.

**Конверсные вторичные прогрессии** (`progression_direction="converse"`). astro.com FAQ «Other methods»: «For 'converse' secondary progressions, use negative age with offset from your birth date… born in 1950 and want converse progressions for 2002, the age is 52. Using negative age, you ought to enter the year 1898». Калькулятор: JD_p = JD₀ − A; углы теми же способами с отрицательным возрастом (`mean_sun`: ARMC₀ − 0,98564733° × A; `solar_arc`: дуга отрицательна); в реальном времени прогрессивная Луна и элонгация движутся **назад** (Луна переходит в предыдущий знак, фаза лунации сменяется на предыдущую). Дирекции солнечной дуги остаются прямыми (конверсная дуга не реализована).

**Дирекции — истинная дуга или ключ Наибода.** AstroWiki «Solar Arc»: «It is possible to use either the actual distance travelled by the Sun… (the true solar arc) or… the mean solar arc… Naibod key… 59 minutes and 8.33 seconds of arc». Разница за год жизни зависит от сезона рождения: Солнце проходит 0,953–1,019°/сут, у T1 (рождение в мае) к 36 годам истинная дуга на 0,99° **меньше** Наибодовой — это почти год во времени срабатывания. По умолчанию — истинная (`arc="true"`: дуга = прогрессивное Солнце − натальное, как в определении AstroWiki и в Solar Fire по описанию astro.com).
**astro.com в картах «Solar arc directions» / «Natal and solar arc direction» берёт среднюю дугу (Наибод)**: «The age of the native is calculated in years, and then multiplied by the mean daily motion of the Sun. The result is added to all planets, axes and houses» (FAQ «Overview chart types»). Для сверки с картами дуги astro.com задавайте `arc="naibod"`.
ASC в дирекциях: «All the planets and axes are moved by the same amount» (ASC + дуга, `sa_asc="arc"`, по умолчанию) или «the other house cusps… based on the movement of the Medium Coeli» (ASC из направленного MC, `sa_asc="from_mc"`).

**Соляр — место и зодиак.**
- Место (AstroWiki «Solar Return Chart»): «Three possible locations… present place of residence, their place of birth or the place at which they happen to be». astro.com по умолчанию берёт место рождения (флажок «use birth place»), а для релокации советует указать город, где человек «have spent or will spend your birthday» (FAQ «Return charts»). Калькулятор: место рождения по умолчанию, релокация — `sr_place` или `sr_lat`/`sr_lon`/`sr_tz`. **Момент соляра от места не зависит**, меняются только местное время, углы и дома.
- Зодиак: тропический соляр — Солнце возвращается к натальной тропической долготе. «Соляр с поправкой на прецессию» (precession-corrected) — к натальной **сидерической** долготе: он наступает позже на ≈ 50,29″ × возраст / 0,9856°/сут ≈ 0,0142 сут × возраст (у Эйнштейна в 26 лет — на 8,6 ч). astro.com такой расчёт не предлагает: «we do not consider the method logical and consistent» (FAQ «Other methods»). Опция `sr_zodiac="sidereal"` (аянамша `sr_ayanamsa`, по умолчанию Fagan/Bradley) — с предупреждением.

**Профекции.**
- Brennan (TMA, astro.com): «you begin from the sign that contains the Ascendant; the ruler of that sign becomes the "time-lord of the year" for the first year»; «When a person is born, start from zero at the sign that contains the Ascendant, which is the 1st Whole Sign house… Every twelve years, the profection returns to the rising sign… 12… 24, then 36, 48, 60». Управители — **традиционные** («I'm going to be using the traditional rulership scheme»), высшие планеты как управители не берутся, но учитываются, если стоят в знаке года.
- Граница года: «In the second year of the native's life, starting on their first solar return» (TMA) и «it jumps suddenly on the day of your birthday» (подкаст, эп. 153). Разница — не больше суток. По умолчанию `profection_boundary="solar_return"`, вариант `"birthday"` (местная полночь дня рождения).
- Месячные профекции: «profections can actually be done at a yearly rate, at a monthly rate, or even daily» (Brennan, эп. 153); в книге Brennan «Hellenistic Astrology» (2017, гл. 17): «Profections can also be advanced on a monthly, daily, or even hourly level», механика месяца не дана. Источники с механикой (опция `profection_month`):

  | `profection_month` | Правило | Источник |
  |---|---|---|
  | `equal` (**по умолчанию**) | год профекции (соляр → соляр) делится на 12 равных частей; знак месяца = знак года + номер месяца | ⚠ условность калькулятора: прямого источника нет; от `calendar` отличается на ±1–2 сут в границах |
  | `calendar` | месяцы от дня рождения: границы — местная полночь того же числа каждого следующего месяца (если такого числа нет — последний день месяца) | D. George, «Astrology and the Authentic Self» (2008): «the seventh house governs the first month following the birthday—in Bill's case, November 17 to December 17. The eighth house governs the following month—December 17 to January 17»; AstroWiki «Profection» (по Knappich): возраст «27 years, 6 months, and 5 days» → 6 месяцев = 6 знаков |
  | `thirteen` | 13 равных частей года профекции (≈ 28,1 сут), знак = знак года + номер; 13-й месяц снова в знаке года | Птолемей, Tetrabiblos IV.10 (пер. Ashmand, 1822): «the number of the month… is to be projected from such places as possess the dominion of the year, in the proportion of twenty-eight days per sign»; R. Hand (предисловие к Project Hindsight, т. IX, 1995): «the monthly profections have to go at the rate of thirteen signs per year… a little over 28 days» |
  | `valens` | дуга светила секты от натального положения до текущего, по 30° на знак от знака года (днём Солнце, ночью Луна; без времени рождения — Солнце с предупреждением) | Валент, Anthology IV.28 (пер. M. Riley): «determine the distance from the Sun at the moment in question to the Sun at the nativity, then count that distance from the sign which has been allotted the year. For night births… from the Moon» |

  Ещё у Валента (V.6 по Riley; у Brennan — 5, 4: 1, «Nechepso»): «distance from the Sun's current position to the Moon's position at birth, then count that distance from the Ascendant»; сам Валент считал действенными месяцы, когда Солнце проходит знаки распределения года, — **не реализованы**.
- Другие «профекционные» системы (AstroWiki «Profection»): Мюнхенская ритмика (7 лет на дом), школа Глана (8⅓ года), Возрастная точка Хуберов (6 лет на дом Коха), ключ Франкленда (7 лет на знак) — **не реализованы**.

**Первичные дирекции** (`primary_directions=True`, только к углам). astro.com предлагает их отдельной картой («Primary Directions are a complex subject…»; FAQ «Other methods») с опциями `mb=0` «promissors without latitude», `mc=1/2` только прямые/только конверсные, ключи `ms=n` «Naibod/Kühr», `ms=L`/`ms=a` движение Солнца в день рождения по эклиптике/экватору, `ms=k` «Kündig: 1 degree in AR»; какой ключ у astro.com по умолчанию, в FAQ не сказано ⚠. Калькулятор считает только **соединения планет и северного узла с MC, IC, ASC, DSC**: для углов формулы одинаковы в системах Плацидуса и Региомонтана (Makransky, «Primary Directions. A Primer of Calculation», гл. II: «The simplest directions to calculate are those in which the MC or IC is the significator»; гл. IV и VII: если значимая точка — MC или ASC, общие формулы Региомонтана и Плацидуса сводятся к «Arc = RAp − RAMC» и «Arc = OAp − OAasc»). Дуга > 0 — прямая (direct), < 0 — конверсная (converse); во времени берётся |дуга| (Makransky, гл. III: «Converse arcs are here treated as direct arcs»). Ключи (`pd_key`): `naibod` (по умолчанию; 0,98564733° = 1 год), `ptolemy` (1° = 1 год), `birthday_ra` (Симмонайт: ход Солнца по RA за дату рождения 0h–24h UT), `true_solar_ra` (Плацидус: «the arc of direction is added to the sun's natal RA… timed by the motion in RA of the secondary progressed sun»; по Makransky — «overwhelmingly the most popular method… by modern practitioners»). Широта промиссора (`pd_latitude`): `with` — in mundo (по умолчанию, как astro.com без `mb=0`), `without` — in zodiaco. Дирекции к планетам, мунданные аспекты и полюса значимых точек (Плацидус/Региомонтан) **не реализованы** ⚠ (у Makransky — гл. IV–VII).

### 1.3. Значения по умолчанию и почему

| Параметр | По умолчанию | Варианты | Обоснование |
|---|---|---|---|
| `on_date` | сегодня (UTC) + предупреждение | дата `YYYY-MM-DD` или `YYYY-MM-DDTHH:MM`, зона `on_tz` | без даты прогноз не воспроизводим; дата без времени = 00:00 `on_tz` (как прогрессии astro.com на 0h UT) |
| `period_start`, `period_end` | `[on_date, on_date + 1 год)` | любые даты (≤ 10 лет); дата конца включительно | окно для точных транзитов, стоянок, ингрессий, событий прогрессивной Луны |
| `transit_orbs` | `"hand"` = 1° | число; словарь `{тело: орбис, "default": …}` | astro.com/Р. Хэнд, AstroWiki «initial recommendation» |
| `transit_aspects`, `direction_aspects` | `"major"` (☌ ⚹ □ △ ☍) | `"all"` (+ 6 минорных из модуля 06) | AstroWiki «Transit»: «It is common practice to concentrate on the main aspects» |
| `hit_bodies` | `"slow"` (Марс…Плутон) | `"all"` (Солнце…Плутон), `"all_with_moon"`, список `"jupiter,saturn"` | Луна даёт ~200 точных аспектов в месяц; AstroWiki: медленные транзиты важнее |
| `natal_points` | `"planets_angles"` (10 планет + ASC + MC) | `"all"` (+ северный узел) | — |
| `progression_angles` | `"mean_sun"` | `naibod`, `solar_arc`, `solar_arc_ra`, `quotidian` | умолчание astro.com, «most common» по AstroWiki |
| `year_length` | `"tropical"` (365,24219) | `"julian"` (365,25) | Astrolog `rDayInYear` |
| `progression_orb` | 1° | число | Wikipedia: «usually limited to an orb of one degree»; AstroWiki: ~0,5° для планет, ~1° для Луны |
| `arc` | `"true"` | `"naibod"` | определение солнечной дуги (AstroWiki); **astro.com рисует дуги по Наибоду** — для сверки с ним `"naibod"` |
| `sa_asc` | `"arc"` | `"from_mc"` | AstroWiki «Solar Arc» |
| `direction_orb` | 1° | число | AstroWiki: «A tight orb… generally under one degree» |
| место соляра | место рождения | `sr_place` / `sr_lat`, `sr_lon` [, `sr_tz`] | умолчание astro.com |
| `sr_year` | соляр, действующий на `on_date` | год | — |
| `sr_zodiac` | `"tropical"` | `"sidereal"` + `sr_ayanamsa` | astro.com (см. §1.2) |
| `include_lunar_return` | `True` | `False` | — |
| `profection_from` | `"asc"` | `"sun"`, `"moon"`, `"mc"` | классика — от ASC; от других точек — «advanced» вариант (слайды Brennan) |
| `profection_boundary` | `"solar_return"` | `"birthday"` | Brennan (TMA) |
| `profection_month` | `"equal"` | `"calendar"`, `"thirteen"`, `"valens"` | §1.2 (умолчание — условность ⚠) |
| `progression_direction` | `"direct"` | `"converse"` | astro.com: конверсные — «negative age» |
| `progression_obliquity` | `"progressed"` | `"natal"` | Astrolog 8 `-p1 -pc` — ε рождения; влияние ≤ 4″ |
| `exact_window_years` | 3 | (0, 120] лет | окно поиска точной даты аспектов прогрессий (кроме Луны: ±120 сут) и дирекций; `null` — точность вне окна |
| `primary_directions` | `False` | `True` + `pd_key` (`"naibod"` \| `"ptolemy"` \| `"birthday_ra"` \| `"true_solar_ra"`), `pd_latitude` (`"with"` \| `"without"`), `pd_max_age` (100) | Makransky; astro.com (опции `ms`, `mb`) |
| `hsys`, `node` | `"P"`, `"true"` | как в модуле 06 | единообразие с натальной картой |

---

## 2. Входные данные

| Поле | Обязательно | Что будет без него |
|---|---|---|
| Дата рождения | да | — |
| Время рождения | для углов, домов, профекций от ASC, Луны | Натал считается на 12:00 местного (как в 06). **Нет**: натальных домов и углов, прогрессивных углов, дирекций ASC/MC, углов соляра и лунара, профекций от ASC (можно `profection_from="sun"`), первичных дирекций. Ненадёжны: натальная Луна (±6–7°) и транзиты к ней, прогрессивная Луна (±6 мес.), фаза лунации (±6 мес.), момент соляра (±12 ч, т. к. натальное Солнце известно лишь ±0,5°) |
| Место рождения (или `tz`) | для UTC; координаты — для домов | без координат — как без времени для домов; без пояса расчёт невозможен |
| `on_date` | желательно | сегодня с предупреждением |
| Место соляра | нет | место рождения |
| Пол, имя | не нужны | — |

**Чувствительность ко времени рождения.** Прогрессивные и дирекционные **углы** сдвигаются на 1° (≈ 1 год срабатывания) при ошибке времени рождения ≈ 4 мин (AstroWiki «Direction»: «a time of birth which is incorrect by as little as 4 minutes would lead to prognoses which are inaccurate by up to one year»). Прогрессивная Луна: 1 ч ошибки ≈ 0,5° натальной Луны ≈ 2 недели в датах. Первичные дирекции к углам: 4 мин времени = 1° RAMC ≈ 1 год во всех ключах. Транзиты к планетам от времени рождения почти не зависят (кроме Луны).

---

## 3. Алгоритм

### 3.1. Общий шаг: моменты и возраст

1. Натальная карта — как в модуле 06 (`western.calculate`): местное → UTC → JD₀ (UT), планеты, ASC/MC, куспиды (Плацидус), **ARMC** рождения (звёздное время в градусах).
2. Целевой момент `on_date` → UTC → JD. Возраст в годах: **A = (JD − JD₀) / 365,24219**.
3. Период поиска `[P₀, P₁)` — по умолчанию год от `on_date`.

### 3.2. Транзиты

1. **Положения на дату**: λ, скорость (°/сут), R (скорость < 0), натальный дом (по натальным куспидам).
2. **Аспект транзита к натальной точке**: d = λ_тр − λ_нат, приведённое к (−180°, 180°]; разделение s = |d|; для каждого аспекта с углом α отклонение δ = s − α. Аспект есть, если |δ| ≤ орбис (1°). Если подходят несколько — берётся с меньшим |δ|.
3. **Сходящийся / расходящийся** (натальная точка неподвижна): ds/dt = sign(d) × v_тр. Если δ × ds/dt < 0 — сходящийся (applying), иначе расходящийся (separating). Особый случай: «сходящийся», но планета встанет в стоянку раньше точного аспекта — точного момента не будет (пример T2, §7.4).
4. **Точный момент** — корень функции f(t) = λ_тр(t) − τ, где τ = λ_нат + α или λ_нат − α (для ☌ и ☍ — одна цель). Корень ищется так:
   - сначала находятся **стоянки** (корни скорости v(t)) на сетке с шагом меньше длительности петли (Меркурий 1 сут, Марс 2 сут, Юпитер–Сатурн 4 сут, Уран–Плутон 5 сут, Луна 0,25 сут) и уточняются бисекцией;
   - сетка дополняется моментами стоянок: между соседними узлами движение **монотонно**, поэтому смена знака f = ровно одно прохождение, а скачок f через ±180° (противоположная сторона круга) корнем не считается (|Δf| < 90°);
   - бисекция до 10⁻⁶ сут (0,09 с).
   Так ретроградная петля даёт **три** прохода (прямой → попятный → прямой), а у Нептуна и Плутона бывает и пять (AstroWiki «Transit»: «Neptune and Pluto can even pass over some degrees of the zodiac up to five times»). Расчёт SE (1850–2150): у Урана — не больше трёх; у Нептуна — до пяти (336°30′ = 6°30′ Рыб: 25.04.1850 – 27.11.1851); у Плутона около афелия (дуга попятного хода ≈ 3° при годовом смещении ≈ 1°) — **до семи** (0°48′ Тельца: 17.07.1851 – 24.01.1854). Калькулятор ограничений на число проходов не имеет. Проходы нумеруются `pass_index / passes_in_period`.
5. **Ингрессии**: те же корни для целей 0°, 30°, …, 330° (знаки) и натальных куспидов (дома). При прямом движении через куспид k планета входит в дом k, при попятном — в дом k − 1.
6. **Стоянки** Меркурия…Плутона в периоде и натальные точки, которые стоянка задевает в орбисе (AstroWiki: «An aspect formed during this stationary phase is thought to be very powerful»).

**Вручную по эфемериде.** Найдите две соседние даты, между которыми разность λ_тр − τ меняет знак, и интерполируйте линейно: t = t₁ + (t₂ − t₁) × f₁ / (f₁ − f₂). Около стоянки линейная интерполяция неточна — используйте суточные значения и проверяйте, не меняет ли планета направление внутри интервала.

### 3.3. Вторичные прогрессии

1. **Прогрессивный момент**: JD_p = JD₀ + A (1 год жизни = 1 сутки эфемерид). Проверка: Wikipedia — родившийся 02.04.1982 в 2007 г. имеет прогрессии на 27.04.1982 («25 days for 25 years»). **Конверсные** (`progression_direction="converse"`): JD_p = JD₀ − A; перевод в реальное время JD = JD₀ − (JD_p − JD₀) × 365,24219; «скорость в год» = −(суточная скорость эфемерид).
2. **Прогрессивные планеты** — положения на JD_p; «скорость в год» = суточная скорость эфемерид. Прогрессивные планеты дополнительно размещаются в натальных домах и в домах прогрессивной карты.
3. **Прогрессивные углы** (§1.2), с истинным наклоном ε на JD_p (`progression_obliquity="natal"` — ε на JD₀, кроме `quotidian`); у конверсных возраст A берётся со знаком минус:
   - `mean_sun`: ARMC_p = ARMC₀ + 0,98564733° × A;
   - `naibod`: MC_p = MC₀ + 0,98564733° × A, затем ARMC_p = α(MC_p) = atan2(sin λ · cos ε, cos λ);
   - `solar_arc`: MC_p = MC₀ + (☉_p − ☉₀), ARMC_p = α(MC_p);
   - `solar_arc_ra`: ARMC_p = ARMC₀ + (α☉_p − α☉₀);
   - `quotidian`: ARMC_p — звёздное время самого момента JD_p на месте рождения.
   Затем по ARMC_p (как в 06 §3.2): **MC = atan2(sin ARMC, cos ARMC · cos ε)**, **ASC = atan2(cos ARMC, −(sin ARMC · cos ε + tg φ · sin ε))** (+ правило восточной половины), куспиды — `swe.houses_armc(ARMC, φ, ε, hsys)`; за полярным кругом — Порфирий.
4. **Аспекты прогрессивных точек к натальным** — как §3.2 п. 2–3, орбис 1°, скорость — «в год». Соединение прогрессивной точки со своей же натальной точкой не выводится (медленные планеты остаются в орбисе десятилетиями), **кроме Луны** (прогрессивный «лунный возврат» в ~27 лет). Точная дата — корень в реальном времени (окно ±120 сут для Луны, ±`exact_window_years` = 3 года для остальных; ближайший к `on_date` корень); `null` — точность вне окна. У медленных планет аспект в орбисе 1° может быть точным за десятилетия (T2: прогр. Сатурн △ Луны — точно 25.10.2005, найдено при `exact_window_years=30`).
5. **Прогрессивная Луна**: знак, натальный дом, дом прогрессивной карты; когда вошла в знак, ближайшие смены знака и натального дома; все такие события в периоде. Перевод из прогрессивного времени в реальное: **JD = JD₀ + (JD_p − JD₀) × 365,24219**. Средняя скорость прогрессивной Луны 11,8–15,4°/год: знак за 1,95–2,5 года (AstroWiki: «on average 2 1/2 years in one house or sign»).
6. **Фаза прогрессивной лунации**: элонгация E = (☽_p − ☉_p) mod 360°, фаза = ⌊E / 45°⌋ (8 фаз Радьяра, границы — табл. 4.4). Начало фазы, следующая фаза, последнее и следующее прогрессивное новолуние, следующее полнолуние — корни E(JD_p) = 45°·k в прогрессивном времени, переведённые в реальные даты. Прогрессивный синодический цикл ≈ 29,5 года (astro.com: «progressed New Moons occur only about every 29.5 years»).

### 3.4. Дирекции солнечной дуги

1. **Дуга**: истинная D = (☉_p − ☉₀) mod 360° (прогрессивное Солнце из §3.3); Наибода D_N = 0,98564733° × A.
2. **Направленные точки**: λ_дир = λ₀ + D для 10 планет, узла, MC; ASC = ASC₀ + D (`sa_asc="arc"`) или ASC из ARMC = α(MC₀ + D) на широте рождения (`"from_mc"`).
3. **Аспекты направленных точек к натальным**, орбис 1°; пара «точка — она же» исключается (у всех точек одна дуга, это не событие). Направленные точки движутся только вперёд (~1°/год), поэтому «сходящийся» = точный аспект впереди.
4. **Точная дата**: нужная дуга D* = (τ − λ₀) (τ = натал ± угол); для истинной дуги — момент, когда прогрессивное Солнце = ☉₀ + D*, переведённый в реальную дату; для Наибода A* = D* / 0,98564733. Вручную: 1° ≈ 1 год, точнее — 1° / (суточная скорость Солнца после рождения).

### 3.5. Соляр и лунар

1. **Момент соляра** — корень λ☉(t) = λ☉₀ (видимая тропическая долгота) на интервале вокруг дня рождения нужного года: ищется ближайшее прохождение **до** `on_date` (действующий соляр) или вокруг дня рождения года `sr_year` (`common.ephemeris.find_sun_longitude`, бисекция). Контрольная точка: момент отличается от годовщины момента рождения (UT) меньше чем на сутки (AstroWiki: «This occurs either on the same date as the day of birth or the day before or after»), **кроме лет у невисокосных 1900 и 2100**: между 29.02.1896 и 29.02.1904 (и 2096–2104) нет ни одного 29 февраля, и отклонение доходит до **+1,70 сут** (рождение 01.03.1896 12:00 UT → соляр 03.03.1903 04:46 UT; тест `test_solar_return_more_than_a_day_near_1900`). Быстрая прикидка отклонения — §3.8.
2. **Местное время** соляра — в поясе **места соляра** на дату соляра (историческое смещение tzdb). Если рождение задано `tz="LMT"` или фиксированным смещением (`"UTC+04:00"` — летнее время), для соляра на месте рождения берётся IANA-зона по координатам (с предупреждением): у Эйнштейна соляр 2026 г. в Ульме — 03:17:28 CET, а не «02:57:25 LMT»; если tzdb на дату соляра ещё не знает поясного времени (`LMT` столицы зоны), — LMT по долготе места.
3. **Карта соляра**: планеты на момент, ASC/MC и куспиды на месте соляра (Плацидус, за полярным кругом — Порфирий), дома соляра для планет, натальный дом ASC и MC соляра, аспекты внутри карты соляра (орбисы Astrotheme, мажорные — как в 06).
4. **Сидерический соляр** (`sr_zodiac="sidereal"`): цель λ☉₀ + (аянамша(t) − аянамша(рождения)); 3–4 итерации.
5. **Лунар**: последнее прохождение Луны через натальную долготу Луны до `on_date` (окно 28 сут), следующее, ASC/MC и дом Луны на месте соляра.

### 3.6. Годовые профекции

1. Полных лет N = round((начало текущего года профекции − JD₀) / 365,24219), где начало — последний соляр ≤ `on_date` (или местная полночь последнего дня рождения).
2. Знак года S = (знак ASC + N) mod 12; номер дома в целых знаках = N mod 12 + 1 (возраст 0 → 1-й дом).
3. Управитель года — **традиционный** управитель S (табл. 4.6); современный — для справки. Выводятся: положение управителя в радиксе (знак, дом в целых знаках и по Плацидусу), его транзит на `on_date`, натальные планеты в знаке S.
4. Месяц профекции (`profection_month`, §1.2): `equal` — m = ⌊12 × (t − начало) / (конец − начало)⌋ ⚠ (условность); `calendar` — m = число прошедших границ «то же число, что день рождения, местная полночь»; `thirteen` — m = ⌊13 × (t − начало) / (конец − начало)⌋ (0…12); `valens` — m = ⌊((λ_светила(t) − λ_светила натал) mod 360°) / 30°⌋, светило секты. Знак месяца = S + m (mod 12), управитель — традиционный.

### 3.7. Псевдокод

```text
natal = western.calculate(b)                     # JD0, планеты, ASC, MC, куспиды, ARMC0
JD = utc(on_date); A = (JD − JD0)/365.24219
# транзиты
for p in bodies: pos[p] = ephem(p, JD)
aspects = [(p, n, asp) | | |λp − λn| − angle(asp) | ≤ orb]
for p in hit_bodies:
    st = roots(speed_p, P0, P1, step_p)                       # стоянки
    grid = uniform(P0, P1, step_p) ∪ st                       # монотонные отрезки
    for τ in {λn ± angle}: hits += sign_changes(λp − τ, grid) → bisect
    ingresses += sign_changes(λp − 30k, grid), sign_changes(λp − cusp_k, grid)
# прогрессии
JDp = JD0 + A; prog[p] = ephem(p, JDp)
ARMCp = ARMC0 + 0.98564733·A      (mean_sun) | α(MC0 + arc) (solar_arc) | …
cusps_p = houses_armc(ARMCp, φ, ε(JDp))
E = (☽p − ☉p) mod 360 → phase = floor(E/45)
# дирекции
D = (☉p − ☉0) mod 360 (true) | 0.98564733·A (naibod); dir[p] = λ0[p] + D
# соляр
JDsr = last root of λ☉(t) = ☉0 before JD; chart(JDsr, место соляра)
# профекции
N = round((JDsr − JD0)/365.24219); S = (sign(ASC) + N) mod 12; lord = ruler_trad[S]
month = S + m (equal: ⌊12·frac⌋ | calendar: прошедшие «дни рождения» месяцев | thirteen: ⌊13·frac⌋ | valens: ⌊(λ☉/☽ − λ₀)/30⌋)
# конверсные прогрессии (опция): JDp = JD0 − A; ARMCp = ARMC0 − 0.98564733·A
# первичные дирекции к углам (опция): AD = asin(tg δ·tg φ)
arc_MC = α − RAMC; arc_IC = α − RAMC − 180; arc_ASC = (α − AD) − (RAMC + 90); arc_DSC = (α + AD) − (RAMC − 90)
years = |arc| / 0.98564733 (naibod) | |arc| (ptolemy) | … ; date = JD0 + years·365.24219
```

### 3.8. Ручная прикидка (без программы) и самопроверка

Без эфемерид точные положения **не придумывать**; таблица ниже — для оценки и для проверки чисел калькулятора (все строки сверены с калькулятором, T1 на 14.10.2026: N = 36, A = 36,4157; тесты `test_solar_return_manual_formula`, `test_profections_t1_t4`).

| Что | Прикидка | Проверка на T1 |
|---|---|---|
| Прогрессивная дата | момент рождения (UT) + A суток; 1 месяц жизни ≈ 2 ч эфемерид | 15.05.1990 10:30 UT + 36,4157 сут = 20.06.1990 20:29 UT ✓ |
| Солнечная дуга (= прогрессивное Солнце − натальное) | A × средняя суточная скорость Солнца за первые A суток после рождения (0,953°/сут в начале июля … 1,019°/сут в начале января); «1° в год» — только грубо | 36,4157 × 0,9585 = 34,90° (точно 34,906°); «1° в год» дало бы 36,4° — ошибка 1,5° ≈ 1,5 года |
| Прогрессивная Луна | Луна в эфемериде на прогрессивную дату; дальше ≈ 1°/мес. (11,8–15,4°/год), знак за 2–2,5 года | 2°01′ Близнецов, 15,04°/год → до 0° Рака (30° − 2,03°)/15,04 = 1,86 года → ≈ 23.08.2028 (точно 23.08.2028 23:08 UT) |
| Прогрессивный MC (`mean_sun`) | ARMC₀ + 0,98564733° × A → MC по формуле §3.3; грубо MC₀ + (0,9856° × A) × k, k ≈ 0,92 у 0° Рака/Козерога … 1,09 у 0° Овна/Весов | 68,0119° + 35,8931° = 103,905° → MC 12°48′ Рака ✓; грубо 9°40′ Близнецов + 35,89° × 0,92 ≈ 12°42′ Рака |
| Момент соляра | Δ = соляр − годовщина момента рождения (UT) ≈ **0,24219·N − L** сут, L — число 29 февраля строго между датой рождения и годовщиной (у рождённых 29.02 — отклонение от 28.02 невисокосного года); точность ±1,5 ч (400 случайных рождений 1900–2010, возраст 1–90). Каждый год соляр сдвигается на +5 ч 49 мин по времени суток и на −1 сут после 29 февраля; около 1900 и 2100 гг. Δ доходит до +1,7 сут | L = 9 (1992 … 2024): Δ ≈ 8,719 − 9 = −0,281 сут = −6 ч 45 мин → 03:45 UT 15.05.2026 (точно 03:34:26 UT, Δ = −0,289); T2: −0,828 (точно −0,803); T4 1905: +0,297 (точно +0,308) |
| Местное время соляра | UT + смещение **места соляра на дату соляра** (не пояс рождения!) | 03:34 UT + 3 ч = 06:34 MSK; в Новосибирске +7 ч = 10:34 |
| Профекция | N = полных лет на момент последнего соляра; знак года = знак ASC + (N mod 12); дом = N mod 12 + 1; управитель — традиционный (табл. 4.6) | 36 mod 12 = 0 → Дева, 1-й дом, Меркурий ✓ |
| Сколько проходов у транзита | натальная точка (± угол аспекта) внутри дуги попятного хода (от стоянки D до стоянки R, табл. 4.7) → три прохода за цикл | Юпитер: R 13.12.2026 на 27°01′ Льва, D 13.04.2027 на 16°59′ Льва; □ Солнца = 24°20′ Льва внутри → 3 прохода ✓ |
| Лунар | раз в 27,3 сут; 1° натальной Луны ≈ 2 ч | 21.09.2026 → 18.10.2026 (27,35 сут) ✓ |

### 3.9. Первичные дирекции к углам (`primary_directions=True`)

По Makransky («Primary Directions. A Primer of Calculation», гл. I–III; формулы проверены на его спекулуме принца Чарльза, §7.7):
1. Для каждого промиссора (10 планет + северный узел) — прямое восхождение α и склонение δ на момент рождения: со своей широтой (`pd_latitude="with"`, in mundo; видимые α, δ истинного экватора даты) или точки эклиптики λ с β = 0 (`"without"`, in zodiaco; ε истинный).
2. Восходящая разность **AD = arcsin(tg δ · tg φ)** (Formula I-1; φ — географическая широта рождения). Если |tg δ · tg φ| ≥ 1 (незаходящее/невосходящее тело) — дирекций к ASC/DSC нет (предупреждение).
3. Дуги (приводятся к (−180°, 180°]):
   - → MC: **α − RAMC**; → IC: **α − (RAMC + 180°)**;
   - → ASC: **(α − AD) − (RAMC + 90°)** (косое восхождение OA = α − AD; OA ASC = RAMC + 90°; Formula II-1);
   - → DSC: **(α + AD) − (RAMC − 90°)** (косое нисхождение OD = α + AD; Formula II-2).
   Дуга > 0 — прямая дирекция (d), < 0 — конверсная (c).
4. Время по |дуге| (`pd_key`): Наибод — |дуга| / 0,98564733 лет; Птолемей — |дуга| лет; Симмонайт — |дуга| / (α☉(0h UT следующего дня) − α☉(0h UT даты рождения)); Плацидус (`true_solar_ra`) — t: α☉(JD₀ + t) = α☉₀ + |дуга|, возраст = t лет (1 сут = 1 год). Дата = JD₀ + возраст × 365,24219.
5. Выводятся все дирекции до `pd_max_age` лет (по умолчанию 100) и отдельно — с датой в пределах ±1 года от `on_date`.

---

## 4. Справочные таблицы

### 4.1. Константы

| Величина | Значение | Источник |
|---|---|---|
| Ключ Наибода (среднее суточное движение Солнца) | 0,98564733° = 59′08,33″ | astro.com FAQ «Overview chart types»; AstroWiki «Naibodic Arc» |
| Прирост звёздного времени за год прогрессий | 3 мин 56,555 с (= 0,98564733° / 15 × 3600 с) | AstroWiki «Naibodic Arc», «Secondary Progression» |
| Год для «день = год» | 365,24219 сут (тропический); вариант 365,25 | Astrolog (`astrolog.h`: `#define rDayInYear 365.24219`) |
| Суточная скорость Солнца | 0,953°/сут (начало июля) … 1,019°/сут (начало января) | вычислено SE; см. также 06 §4.5 |
| Сдвиг сидерического соляра | ≈ 0,0142 сут на год возраста (50,29″/год прецессии : 0,9856°/сут) | расчёт |
| Прогрессивный синодический цикл (новолуние → новолуние) | ≈ 29,5 года | astro.com FAQ («progressed New Moons occur only about every 29.5 years») |

### 4.2. Орбисы по техникам

| Техника | По умолчанию | Другие школы |
|---|---|---|
| Транзиты | 1° ко всем натальным точкам | Лиз Грин — шире, зависит от фазы и планет (⚠ не опубликовано); AstroWiki — начать с 1°, расширять до 3–5°; Kerykeion — внешние 1–3°, внутренние ≤ 1° |
| Прогрессии к радиксу | 1° | AstroWiki: «around half a degree» для планет, «around one degree» для прогрессивной Луны; Wikipedia: «usually limited to an orb of one degree» |
| Дирекции солнечной дуги | 1° | AstroWiki «Solar Arc»: «generally under one degree»; «Profection»: «about one degree» |
| Аспекты внутри карты соляра | натальные орбисы Astrotheme (модуль 06) | — |

### 4.3. Аспекты

По умолчанию — пять птолемеевых: соединение 0°, секстиль 60°, квадрат 90°, тригон 120°, оппозиция 180°. С `*_aspects="all"` — ещё полусекстиль 30°, полуквадрат 45°, квинтиль 72°, полутораквадрат 135°, биквинтиль 144°, квинконс 150° (определения — модуль 06 §4.3). Для аспектов, кроме 0° и 180°, у каждой натальной точки **две** цели: λ + α и λ − α.

### 4.4. Фазы лунации (Д. Радьяр; границы по F. Boele, astro.com)

| № | Элонгация ☽ − ☉ | Фаза (`phase`) | Название |
|---|---|---|---|
| 1 | 0°–44° | `new` | Новолуние (New Moon) |
| 2 | 45°–89° | `crescent` | Растущий серп (Crescent) |
| 3 | 90°–134° | `first_quarter` | Первая четверть (First Quarter) |
| 4 | 135°–179° | `gibbous` | Выпуклая растущая Луна (Gibbous) |
| 5 | 180°–224° | `full` | Полнолуние (Full Moon) |
| 6 | 225°–269° | `disseminating` | Распространяющая, убывающая выпуклая (Disseminating) |
| 7 | 270°–314° | `last_quarter` | Последняя четверть (Last Quarter) |
| 8 | 315°–359° | `balsamic` | Бальзамическая (Balsamic) |

### 4.5. Годовые профекции: возраст → дом (целые знаки, от ASC)

| Дом | Возраст (полных лет) |
|---|---|
| 1 | 0, 12, 24, 36, 48, 60, 72, 84, 96 |
| 2 | 1, 13, 25, 37, 49, 61, 73, 85, 97 |
| 3 | 2, 14, 26, 38, 50, 62, 74, 86, 98 |
| 4 | 3, 15, 27, 39, 51, 63, 75, 87, 99 |
| 5 | 4, 16, 28, 40, 52, 64, 76, 88, 100 |
| 6 | 5, 17, 29, 41, 53, 65, 77, 89, 101 |
| 7 | 6, 18, 30, 42, 54, 66, 78, 90, 102 |
| 8 | 7, 19, 31, 43, 55, 67, 79, 91, 103 |
| 9 | 8, 20, 32, 44, 56, 68, 80, 92, 104 |
| 10 | 9, 21, 33, 45, 57, 69, 81, 93, 105 |
| 11 | 10, 22, 34, 46, 58, 70, 82, 94, 106 |
| 12 | 11, 23, 35, 47, 59, 71, 83, 95, 107 |

### 4.6. Управитель года: традиционный (и современный) управитель знака

| Знак | Традиционный (управитель года) | Современный (справочно) |
|---|---|---|
| Овен | Марс | Марс |
| Телец | Венера | Венера |
| Близнецы | Меркурий | Меркурий |
| Рак | Луна | Луна |
| Лев | Солнце | Солнце |
| Дева | Меркурий | Меркурий |
| Весы | Венера | Венера |
| Скорпион | Марс | Плутон |
| Стрелец | Юпитер | Юпитер |
| Козерог | Сатурн | Сатурн |
| Водолей | Сатурн | Уран |
| Рыбы | Юпитер | Нептун |

### 4.7. Ретроградность (вычислено SE, 2000–2050) — для оценки числа проходов

| Планета | Попятных периодов | Длительность R, сут (мин–сред–макс) | Синодический период, сут | Дуга попятного хода | Доля времени R |
|---|---|---|---|---|---|
| Меркурий | 158 | 19,8–22,2–24,2 | 115,9 | 8,6°–16,3° | 19,1 % |
| Венера | 31 | 40,9–42,1–43,1 | 583,9 | 15,4°–16,5° | 7,1 % |
| Марс | 23 | 60,0–73,7–81,1 | 779,8 | 10,0°–19,5° | 9,3 % |
| Юпитер | 46 | 117,5–120,6–123,6 | 398,9 | 9,8°–10,1° | 29,7 % |
| Сатурн | 48 | 133,7–137,6–141,4 | 378,0 | 6,6°–7,0° | 36,2 % |
| Уран | 50 | 149,0–151,3–154,3 | 369,6 | 3,9°–4,2° | 40,6 % |
| Нептун | 50 | 156,9–158,6–160,1 | 367,5 | 2,8° | 42,5 % |
| Плутон | 50 | 158,5–162,0–164,6 | 367,0 | 2,2°–2,8° | 44,4 % |

Натальная точка внутри дуги попятного хода получает от этой планеты три прохода за один цикл. Солнце и Луна ретроградными не бывают — их транзиты всегда однократны.

### 4.8. Сравнение способов прогрессивных углов (T4, 30.06.1905, возраст 26,2936 г.)

| Способ | Прирост ARMC | MC | ASC |
|---|---|---|---|
| `mean_sun` | 25,9163° | 10°59′20″ Овна | 1°45′00″ Льва |
| `naibod` | 23,8584° | 8°45′22″ Овна | 0°13′03″ Льва |
| `solar_arc` | 23,9304° | 8°50′03″ Овна | 0°16′17″ Льва |
| `solar_arc_ra` | 23,9585° | 8°51′53″ Овна | 0°17′32″ Льва |
| `quotidian` | 131,6283° | 23°55′39″ Рака | 18°52′00″ Весов |

Натальный MC Эйнштейна (12°50′ Рыб) у точки равноденствия: там 1° прямого восхождения ≈ 1,09° долготы, поэтому прибавка 25,9° к ARMC (`mean_sun`) даёт MC на 2,15° дальше, чем прибавка 26,0° к MC в долготе (`solar_arc`). 2° — это ≈ 2 года во времени срабатывания аспектов к MC. С `progression_obliquity="natal"` (ε рождения 23,45647° вместо 23,45638°) ASC `mean_sun` и `solar_arc` сдвигаются на 0,2″, MC `mean_sun` — на 0,03″ (MC `solar_arc` от ε не зависит).

### 4.9. Месяц профекции T1 на 14.10.2026 00:00 UTC по вариантам (год: Дева, 1-й дом, с 15.05.2026 06:34 MSK)

| `profection_month` | Месяц | Знак / управитель | Границы (UTC) |
|---|---|---|---|
| `equal` | 5 из 12 | Козерог / Сатурн | 13.09.2026 21:26 – 14.10.2026 07:54 |
| `calendar` | 5 из 12 | Козерог / Сатурн | 14.09.2026 21:00 – 14.10.2026 21:00 (15-е число, 00:00 MSK) |
| `thirteen` | 6 из 13 | Водолей / Сатурн | 02.10.2026 14:57 – 30.10.2026 17:14 |
| `valens` (дневное рождение → Солнце, дуга 146,33°) | 5 | Козерог / Сатурн | 17.09.2026 04:55 – 17.10.2026 16:50 (Солнце на 24°20′ Девы … Весов) |

На 15.10.2026: `equal` и `calendar` — уже Водолей (6-й месяц), `valens` — ещё Козерог. Варианты расходятся у границ месяцев, а `thirteen` — систематически (13 месяцев в году).

### 4.10. Ключи первичных дирекций (Makransky, гл. III; пример — принц Чарльз, §7.7)

| `pd_key` | Годы на 1° дуги | MO ☌ MC mund d (дуга 16,10°) | JU ☌ DSC zod c (дуга −45,54°) |
|---|---|---|---|
| `ptolemy` | 1 | 16,10 г. → 21.12.1964 | 45,54 г. → 30.05.1994 |
| `naibod` (по умолчанию) | 1 / 0,98564733 = 1,01456 | 16,335 г. → 17.03.1965 | 46,205 г. → 28.01.1995 |
| `birthday_ra` | 1 / (ход α☉ за дату рождения = 1,025°) | 15,707 г. → 30.07.1964 | 44,429 г. → 20.04.1993 |
| `true_solar_ra` | по прогрессивному Солнцу в α | 15,318 сут → 10.03.1964 | 42,043 сут → 30.11.1990 |

(Даты — по Makransky; калькулятор: 23.12.1964, 19.03.1965, 03.08.1964, 06.03.1964; 29.05.1994, 27.01.1995, 22.04.1993, 04.12.1990 — дуги отличаются на ≤ 0,02°, т. е. ≤ 1 нед.)

---

## 5. Выход (JSON)

```jsonc
{
  "method": "western_forecast",
  "variant": "тропический зодиак; транзитные орбисы 'hand'; прогрессии 1 сут = 1 год (365.24219 сут); углы mean_sun; дуга true; соляр tropical, место рождения; дома Плацидус (Placidus); профекции от asc, целые знаки, трад. управители",
  "inputs_used": {"birth_utc": "...", "birth_jd": 2448026.9375, "tz": "Europe/Moscow", "lat": 55.7558, "lon": 37.6173,
                  "time_known": true, "on_date_utc": "2026-10-14T00:00:00+00:00", "on_jd": 2461327.5,
                  "period": {"start_utc": "...", "end_utc": "..."}, "options": {"transit_orbs": "hand", "...": "..."}},
  "warnings": ["..."],
  "natal": {"bodies": {"sun": {"lon": 54.3358, "pos": "24°20′09″ Телец", "house": 9}, "...": {}},
            "asc": 165.3778, "mc": 69.6723, "armc": 68.011884, "cusps": [165.3778, "..."], "house_system": "P"},
  "age_years": 36.415734,
  "transits": {
    "jd": 2461327.5, "utc": "...",
    "positions": {"saturn": {"lon": 10.5620, "pos": "10°33′43″ Овен", "speed": -0.0768, "retrograde": true, "natal_house": 8}},
    "aspects": [{"transit": "saturn", "natal": "mc", "aspect": "sextile", "angle": 60, "orb": 0.8895, "orb_dm": "0°53′",
                 "orb_allowed": 1.0, "phase": "applying", "phase_ru": "сходящийся", "transit_retrograde": true,
                 "exact_prev_utc": "2026-05-05T17:35:38+00:00", "exact_next_utc": "2026-10-26T03:26:52+00:00",
                 "exact_search_window_days": 400}],
    "orbs": "hand", "period": {"start_utc": "...", "end_utc": "...", "bodies": ["mars", "...", "pluto"]},
    "exact_hits": [{"transit": "jupiter", "natal": "sun", "aspect": "square", "side": 1, "jd": 2461345.604, "utc": "...",
                    "transit_lon": 144.3358, "transit_pos": "24°20′09″ Лев", "retrograde": false,
                    "pass_index": 1, "passes_in_period": 3}],
    "stations": [{"body": "mercury", "type": "retrograde", "type_ru": "...", "utc": "...", "pos": "...",
                  "aspects_to_natal": [{"natal": "...", "aspect": "...", "orb": 0.4}]}],
    "sign_ingresses": [{"body": "jupiter", "utc": "...", "to_sign_ru": "Дева", "retrograde": false}],
    "house_ingresses": [{"body": "jupiter", "utc": "...", "cusp": 1, "enters_house": 1, "retrograde": false}]
  },
  "progressions": {
    "direction": "direct", "progressed_jd": 2448063.353234, "progressed_utc": "1990-06-20T20:28:39+00:00", "age_years": 36.415734,
    "year_length_days": 365.24219, "exact_search_window_years": 3.0,
    "positions": {"moon": {"pos": "2°01′38″ Близнецы", "speed_per_year": 15.04, "natal_house": 9, "progressed_house": 8},
                  "asc": {"...": "..."}, "mc": {"...": "..."}},
    "angles": {"method": "mean_sun", "method_ru": "...", "armc": 103.904955, "armc_natal": 68.011884,
               "armc_advance": 35.893071, "system": "P", "obliquity": 23.44197, "obliquity_source": "progressed",
               "cusps": [{"house": 1, "lon": 189.25, "pos": "..."}]},
    "aspects_to_natal": [{"progressed": "mc", "natal": "venus", "aspect": "square", "orb": 0.0497, "phase": "separating",
                          "exact_utc": "2026-09-24T03:05:09+00:00"}],
    "moon": {"pos": "...", "entered_sign_utc": "...", "next_sign_change": {"utc": "...", "to_sign_ru": "Рак"},
             "next_natal_house_change": {"utc": "...", "to_house": 10}, "events_in_period": ["..."]},
    "lunation": {"elongation": 332.79, "phase": "balsamic", "phase_ru": "...", "phase_index": 8, "phase_range": "315°–359°",
                 "phase_started": {"utc": "...", "age_years": 35.145, "before_birth": false}, "next_phase": {"...": "..."},
                 "next_phase_name": "new", "last_new_moon": {"...": "..."}, "next_new_moon": {"...": "..."}, "next_full_moon": {"...": "..."}}
  },
  "solar_arc": {"arc_method": "true", "arc": 34.90559, "arc_dms": "34°54′", "arc_true": 34.90559, "arc_naibod": 35.893071,
                "asc_method": "arc", "exact_search_window_years": 3.0, "directed": {"mc": {"pos": "14°34′41″ Рак", "natal_house": 10}},
                "aspects_to_natal": [{"directed": "mc", "natal": "neptune", "aspect": "opposition", "orb": 0.2243,
                                      "phase": "separating", "exact_utc": "...", "exact_age_years": 36.181}]},
  "solar_return": {"moment_jd": 2461175.649, "moment_utc": "2026-05-15T03:34:26+00:00", "local": "2026-05-15T06:34:26",
                   "tz": "Europe/Moscow", "utc_offset": "UTC+03:00", "zodiac": "tropical", "natal_sun": 54.3358, "sr_sun": 54.3358,
                   "sun_check_arcsec": 0.0, "days_from_birth_anniversary_utc": -0.2886, "next_moment_utc": "...",
                   "place": "Москва", "lat": 55.7558, "lon": 37.6173, "where": "birthplace",
                   "angles": {"asc": {"pos": "3°17′10″ Рак", "natal_house": 10}, "mc": {"...": "..."}},
                   "houses": {"system": "P", "cusps": ["..."]}, "bodies": {"sun": {"sr_house": 12, "natal_house": 9}},
                   "aspects": [{"p1": "sun", "p2": "mercury", "aspect": "conjunction", "orb": 0.67}]},
  "lunar_return": {"moment_utc": "...", "local": "...", "next_moment_utc": "...", "asc": {"...": "..."}, "mc": {"...": "..."}, "moon_house": 2},
  "profections": {"from": "asc", "age_completed": 36, "house_whole_sign": 1, "sign": "Virgo", "sign_ru": "Дева",
                  "lord": "mercury", "lord_ru": "Меркурий", "lord_modern": "mercury", "year_start_utc": "...", "year_end_utc": "...",
                  "boundary": "solar_return", "natal_planets_in_sign": [],
                  "lord_natal": {"pos": "8°01′12″ Телец", "house_whole_sign": 9, "house": 9},
                  "lord_transit": {"pos": "15°35′50″ Скорпион", "retrograde": false, "natal_house": 3, "house_whole_sign": 3},
                  "month": {"method": "equal", "variant": "...", "months_in_year": 12, "index": 5, "sign_ru": "Козерог",
                            "lord": "saturn", "start_utc": "...", "end_utc": "..."}},   // valens: + "luminary", "luminary_arc"
  "primary_directions": null,   // при primary_directions=True:
  // {"key": "naibod", "key_ru": "...", "latitude": "with", "armc": 68.011884, "oa_asc": 158.011884, "od_dsc": 338.011884,
  //  "obliquity": 23.44..., "birthday_ra_motion": null, "max_age": 100.0,
  //  "speculum": {"sun": {"ra": 51.968036, "dec": 18.857191, "ad": 30.114574}, "...": {}},
  //  "directions": [{"promissor": "neptune", "significator": "ic", "aspect": "conjunction", "type": "direct",
  //                  "arc": 37.4725, "arc_dms": "37°28′", "age_years": 38.0181, "jd": ..., "utc": "2028-05-21T..."}],
  //  "near_on_date": []}
  "steps": [{"step": "1. Натальная карта", "detail": "..."}, "... 7 шагов (8-й — первичные дирекции, если включены) ..."]
}
```

Без времени рождения: `progressions.angles`, `solar_return.angles/houses`, `profections` (от ASC), `primary_directions` = `null`, ключей `asc`/`mc` нет в `directed`, `natal.asc` = `null`.

---

## 6. Контрольные точки

**Инварианты (проверяются тестами)**
- В момент `exact_hits[i].jd` долгота транзита = натал ± угол (< 0,0002°); `retrograde` = знак скорости в этот момент.
- У тройного прохода порядок `retrograde` = прямой → попятный → прямой (1/3, 2/3, 3/3).
- Вокруг стоянки скорость меняет знак (+ → − у `retrograde`, − → + у `direct`).
- JD_p = JD₀ + (JD − JD₀)/365,24219; прогрессивное Солнце движется 0,95–1,02° в год, т. е. **дуга ≈ возраст в градусах**.
- `mean_sun`: прирост ARMC = 0,98564733 × A; `naibod`: MC − MC₀ = 0,98564733 × A; `solar_arc`: MC − MC₀ = истинной дуге; в момент рождения все способы дают натальные углы; куспид 1 = ASC, куспид 10 = MC.
- Солнечная дуга: каждая направленная точка = натал + дуга; в `exact_utc` аспект точный.
- Соляр: долгота Солнца в момент соляра = натальной (< 0,01″); отклонение от годовщины момента рождения < 1 сут (исключение — годы у 1900 и 2100: до +1,7 сут, §3.5) и ≈ 0,24219·N − L сут с точностью ±1,5 ч (§3.8); момент не зависит от места.
- Лунар: следующий через 27,0–27,7 сут.
- Профекции: возраст 0, 12, 24, 36 … → 1-й дом; знак года = знак ASC + N mod 12.
- Фаза лунации = ⌊элонгация/45°⌋ + 1; `phase_started` ≤ `on_date` ≤ `next_phase`.
- Конверсные прогрессии: JD_p = JD₀ − A; `mean_sun`: прирост ARMC = −0,98564733 × A; «скорость в год» = −скорость эфемерид; в момент события прогрессивной Луны она на границе знака/куспида и уходит в **предыдущий** знак/дом; фаза началась на верхней границе (45°·(k+1)) и кончится на нижней (45°·k); дирекции дуги те же, что у прямых.
- Месяцы профекции: `equal` — 12 равных частей; `calendar` — границы в 00:00 местного времени того же числа; `thirteen` — 13 равных частей, 13-й месяц в знаке года; `valens` — в начале месяца светило секты стоит на натальной долготе + 30°·m.
- Первичные дирекции: дуга = формула §3.9 из спекулума (α, δ, AD) и RAMC; `age_years` = |дуга| / ключ; ни одной дирекции старше `pd_max_age`; без времени рождения — `null`.

**Типичные ошибки**
1. **Часовой пояс места соляра.** Момент соляра один и тот же везде; меняется местное время. T1: 15.05.2026 03:34:26 UTC = 06:34:26 в Москве и 10:34:26 в Новосибирске. Если ввести московское время как новосибирское, ASC соляра «уедет» на целый знак. Пояс **рождения** на соляр не переносится: летнее время 1990 г. (UTC+4) или LMT 1879 г. действовали только тогда — в 2026 г. Москва живёт по UTC+3, Ульм по CET/CEST (калькулятор сам берёт IANA-зону места, §3.5 п. 2).
2. **Сидерический соляр вместо тропического** (или наоборот). Для 26 лет разница 8,6 ч, для 50 лет — ~17 ч: углы и дома соляра совершенно другие. Спрашивайте, какой нужен; по умолчанию — тропический.
3. **Наибод вместо истинной дуги** (и наоборот). T1 (рождение в мае, Солнце медленное): к 36 годам истинная дуга 34,906°, Наибодова 35,893° — **разница 0,99°, почти год** во времени срабатывания дирекций. Называйте, какая дуга использована. Сверяя с картой дуг astro.com, помните: там дуга **Наибодова** (`arc="naibod"`), а не истинная.
4. **Прогрессивные углы разными способами.** `mean_sun` (astro.com) и `solar_arc` (Solar Fire) расходятся, особенно если натальный MC около 0° Овна/Весов (T4: 2,15° за 26 лет, табл. 4.8). Сверяя с чужой программой, сначала выясните способ.
5. **Натальные орбисы для транзитов.** Транзиты считают с орбисом ~1°, а не 8–10°: иначе «действует» почти всё.
6. **Забытые проходы ретроградной петли.** Одна дата «точного аспекта» для Юпитера…Плутона почти всегда неполна: проверьте `passes_in_period` и расширьте период.
7. **«Сходящийся» ≠ «будет точным».** Планета может встать в стоянку раньше точного аспекта (T2, Плутон □ Плутон, §7.4): `exact_next_utc = null`.
8. **Счёт профекций с 1 вместо 0.** Год рождения (возраст 0) — 1-й дом; в 36 лет — снова 1-й дом, а не 12-й.
9. **Современные управители в профекциях.** Управитель года — традиционный (Водолей → Сатурн, Рыбы → Юпитер, Скорпион → Марс).
10. **Возраст «по календарю» вместо точного.** Профекция и соляр меняются в момент соляра (±1 сут от дня рождения; у 1900 и 2100 гг. — до +1,7 сут); 14.05 и 15.05 могут давать разные годы. Для дат у самой границы указывайте обе версии (`profection_boundary`).
11. **29 февраля.** В невисокосный год соляр приходится на 28.02 или 01.03 (у T3 — 28.02), «день рождения» для `profection_boundary="birthday"` — 01.03.
12. **Прогрессии без точного времени.** Прогрессивные углы и дирекции ASC/MC при времени «около 8 утра» бессмысленны (4 мин ≈ 1 год); прогрессивная Луна — ±2 недели на каждый час ошибки.
13. **Соляр по «таблице дат».** Момент считается только по эфемериде; «соляр в день рождения в то же время, что рождение» ошибочен на часы (T2: −0,8 сут).

14. **Профекция месяца без указания варианта.** Четыре варианта (§1.2, табл. 4.9) дают разные знаки у границ месяцев, `thirteen` — почти всегда другой; называйте вариант.
15. **Знак конверсной дуги первичной дирекции.** Конверсная дирекция (дуга < 0) — не «до рождения»: во времени берётся |дуга| (Makransky); тип `converse` указывайте отдельно.

**Граничные случаи:** соляр за полярным кругом (Плацидус не определён → Порфирий, предупреждение; §7.5); 29 февраля (§7.5); неизвестное время (§7.5); `on_date` раньше рождения — ошибка (конверсные прогрессии — опцией `progression_direction="converse"` на дату после рождения, §7.8); стоянка до точного аспекта (§7.4); прогрессивное новолуние до рождения (`before_birth: true`, реальная «дата» раньше рождения; у конверсных — фазы после рождения в прогрессивном времени); рождение 29–31 числа в `profection_month="calendar"` — граница в последний день короткого месяца (рождение 31.01 → 28.02, затем 31.03); незаходящий промиссор на широте рождения — нет дирекций к ASC/DSC (предупреждение).

---

## 7. Примеры

### 7.0. Сверка с внешними источниками

| Что | Источник | Результат |
|---|---|---|
| Момент соляра T4 (1905) и T1 (2026) | JPL Horizons (DE441), ObsEcLon Солнца в момент рождения и в наш момент соляра | T4: 353,5076977° и 353,5077229° (Δ 0,09″ ≈ 2 с); T1: 54,3358312° и 54,3358333° (Δ 0,01″) |
| Прогрессивные Солнце и Луна T4 на JD_p 2407449,245069 | JPL Horizons | Δ 0,30″ и 0,27″ |
| Точные транзиты (тройные проходы) T1 2026–27 и T4 1905 | JPL Horizons: поправка Ньютона по ObsEcLon вокруг нашего момента | 11 моментов; Δ ≤ 15 с (2026–27), ≤ 2,5 мин (1905; Уран 0,04°/сут — это 0,15″) |
| Стоянки (7 для 2026–27, 7 для 1905) | JPL Horizons: экстремум долготы (часовая сетка, парабола) | Δ ≤ 0,11 ч; Плутон 0,7–1,1 ч (экстремум очень плоский) |
| Фазы прогрессивной лунации | F. Boele, «The Progressed Lunation Cycle» (astro.com; данные рождения из статьи) | 28 из 28 утверждений совпадают (§7.6); ещё 2 события Леннона (ноябрь 1961, 08.11.1968) у границы фазы: по расчёту фаза наступает на 33 и 25 дней позже (≈1° элонгации ≈ 1 ч времени рождения рейтинга A) |
| Годовые профекции Ф. Ф. Копполы (AA, 07.04.1939 1:38 EST, Детройт; ASC 7°24′ Козерога по Astrotheme) | C. Brennan, TMA (astro.com) | 4 из 4: Дева/Меркурий в 32 года (1971), Весы/Венера 10-й дом (1972), Водолей/Сатурн (1976), Телец/Венера (1979) |
| Прогрессивная дата 02.04.1982 → 2007 г. | Wikipedia «Astrological progression» | 27.04.1982 ✓ |
| Первичные дирекции к углам: спекулум и дуги принца Чарльза (14.11.1948 21:14:39 GMT, 51N30, 0W10) | B. Makransky, «Primary Directions. A Primer of Calculation» (archive.org) | RAMC 12,37 ✓; α, AD 6 тел — Δ ≤ 0,02°; 7 дуг (MO ☌ MC, SU ☌ IC, SA ☌ IC, PL ☌ ASC, UR ☌ ASC, JU ☌ DSC mund и zod) — Δ ≤ 0,015°; 8 сроков в 4 ключах — Δ ≤ 0,02 г. (§7.7) |
| Календарные месяцы профекции | D. George, «Astrology and the Authentic Self» (пример «Bill»: 7-й дом года, 17.11; 17.05–16.06 — 1-й дом) | воспроизведено на синтетическом рождении 17.11.1996 ✓ (тест `test_profection_calendar_months_george`) |
| Конверсные прогрессии | astro.com FAQ «Other methods» («negative age») | JD_p = JD₀ − A, положения = эфемерида на JD₀ − A ✓ |
| Ключ Наибода и «3 мин 56,55 с» | astro.com FAQ, AstroWiki | 0,98564733° × 240 с/° = 236,555 с ✓ |

### 7.1. T4 — Альберт Эйнштейн, прогноз на 30.06.1905 (annus mirabilis; соляр на Берн)

**Вход:** натал 14.03.1879 11:30 LMT, Ульм (48,4011N, 9,9876E) — как в модуле 06 §7.1. `on_date = 1905-06-30` (статья «Zur Elektrodynamik bewegter Körper» «was received on 30 June and published 26 September» — Wikipedia «Annus mirabilis papers», вторичный). Соляр на Берн (46,9480N, 7,4474E, `Europe/Zurich`; Эйнштейн работал в Швейцарском патентном бюро в Берне, в 1903–1905 гг. жил на Kramgasse 49, в 1909 г. перешёл в Цюрихский университет — Wikipedia «Albert Einstein», «Einsteinhaus», вторичный). Период поиска транзитов — весь 1905 год.

1. **Натал:** UTC 1879-03-14 10:50:03, JD₀ = 2407422,951423; Солнце 23°30′28″ Рыб, ASC 11°38′50″ Рака, MC 12°50′23″ Рыб, ARMC₀ = 344,1841°.
2. **Целевой момент:** 1905-06-30 00:00 UTC = JD 2417026,5; A = (2417026,5 − 2407422,951423)/365,24219 = 26,293645 года.
3. **Транзиты на 30.06.1905** (орбис 1°): Нептун ⚹ натального Нептуна 0°00′ сх. (точно 30.06 00:47 UTC); Солнце ⚹ Нептуна 0°21′ сх.; Луна ⚹ Сатурна 0°41′ расх.; Уран △ Урана 0°44′ сх. (Уран R, точно 19.07.1905); Юпитер △ Марса 0°56′ сх. (точно 04.07.1905).
   **Тройные проходы 1905 г.:** Уран △ натального Урана (1°17′ Девы) — 11.01 (прямо), 19.07 (R), 29.10 (прямо); Сатурн ☌ натального Юпитера (27°29′ Водолея) — 19.03, 21.09 (R), 09.12; Уран □ натального Сатурна (4°11′ Овна) — 29.03, 19.04 (R), 23.12; Уран □ натального Меркурия — 16.02, 01.06 (R), 06.12. Стоянки: Уран D 09.09.1905 15:17 UTC (0°14′ Козерога), Сатурн D 31.10.1905, Меркурий R 16.08.1905 (14°03′ Девы, □ натальной Луны 0,47°).
4. **Прогрессии:** JD_p = 2407422,951423 + 26,293645 = 2407449,245069 = **1879-04-09 17:52:53 UTC**. Прогрессивное Солнце 19°30′08″ Овна, Луна 29°27′03″ Скорпиона (5-й натальный дом), Меркурий 1°13′51″ Тельца R.
   Углы (`mean_sun`): ARMC_p = 344,1841° + 0,98564733 × 26,293645 = 344,1841° + 25,9163° = 10,1004°; ε(JD_p) = 23,45638°; MC = atan2(sin 10,1004°, cos 10,1004° · cos ε) = **10°59′20″ Овна**; ASC = **1°45′00″ Льва** (другие способы — табл. 4.8).
   Аспекты к радиксу (орбис 1°): прогр. Меркурий △ натального Урана 0°03′ (точно 07.04.1905), прогр. MC □ натального ASC 0°40′ сх. (10.02.1906), прогр. Марс ⚹ Венеры 0°50′ сх. (15.08.1906).
   Прогрессивная Луна вошла в Скорпион 20.07.1903, входит в **Стрелец 13.07.1905** и в 6-й натальный дом 28.09.1905.
   **Лунация:** элонгация (239,4509° − 19,5022°) = 219,95° → **Полнолуние (180°–224°)**, фаза началась 07.09.1902, Распространяющая — с 10.11.1905; последнее прогрессивное новолуние 17.08.1887 (8,4 года), следующее 30.04.1917 (38,1 года).
5. **Солнечная дуга:** истинная D = 19,5022° − 353,5078° (mod 360) = **25,9945°** (25°59′40″; `arc_dms` = 26°00′ после округления до минуты); Наибода = 0,98564733 × 26,293645 = 25,9163°. Направленные: Юпитер 27°29′02″ Водолея + 25°59′40″ = 23°28′42″ Рыб ☌ натального Солнца 0°02′ сх. (точно 10.07.1905, 26,32 года); Венера ⚹ MC 0°08′ (09.05.1905); ASC □ Нептуна 0°14′ (23.09.1905); Нептун ⚹ Сатурна 0°19′ (28.10.1905); Уран △ Марса 0°22′ (12.02.1905); Нептун ⚹ Меркурия 0°43′ (04.10.1904).
6. **Соляр 1905 (Берн):** Солнце возвращается на 23°30′28″ Рыб **1905-03-14 18:13:01 UTC = 19:13:01 CET (UTC+1)**; отклонение от годовщины момента рождения +0,308 сут (контрольная точка: < 1 сут). Следующий соляр 1906-03-15 00:11 UTC. ASC соляра 1°46′52″ Весов (4-й натальный дом), MC 2°11′44″ Рака (12-й натальный); Солнце соляра в 6-м доме соляра (10-м натальном), Нептун R на MC соляра (☌ 3°11′), Луна соляра 28°04′ Близнецов в 9-м доме. Сверка JPL Horizons: Δ 0,09″ (≈ 2 с).
   **Лунар** (на Берн): 1905-06-16 11:37:35 UTC = 12:37:35 CET; ASC лунара 26°57′ Девы, натальная Луна в 3-м доме лунара; следующий 13.07.1905.
7. **Профекции:** год с 14.03.1905 (соляр) по 15.03.1906; N = 26; знак ASC Рак + 26 mod 12 = Рак + 2 = **Дева, 3-й дом** (целые знаки); управитель года — **Меркурий** (в радиксе 3°08′ Овна, 10-й дом), в знаке Девы натальный Уран; транзитный Меркурий 30.06.1905 — 14°13′ Рака, в 1-м натальном доме. Месяц 4 (`equal`: 14.06–14.07.1905): Стрелец, Юпитер; тот же знак во всех вариантах (`calendar` 14.06–14.07 CET, `thirteen` 07.06–05.07, `valens` 15.06–16.07).

### 7.2. T1 — Иванова А. С., 15.05.1990 14:30 MSD, Москва; прогноз на 14.10.2026

1. **Натал** (модуль 06 §7.2): UTC 10:30, JD₀ = 2448026,9375; Солнце 24°20′09″ Тельца, Луна 26°23′25″ Козерога, ASC 15°22′40″ Девы, MC 9°40′20″ Близнецов, ARMC₀ = 68,0119°.
2. **Момент:** 2026-10-14 00:00 UTC = JD 2461327,5; A = 13300,5625 / 365,24219 = **36,415734**.
3. **Транзиты на дату** (позиции: Солнце 20°40′ Весов, Сатурн 10°34′ Овна R (8-й дом), Уран 5°15′ Близнецов R (9-й), Нептун 2°31′ Овна R (7-й), Плутон 3°04′ Водолея R (5-й)); аспекты в орбисе 1°:

   | Транзит | Аспект | Натал | Орбис | Фаза | Точно (пред. / след.) |
   |---|---|---|---|---|---|
   | Меркурий | ⚹ | ASC | 0°13′ | расх. | 13.10.2026 18:13 / 02.11.2026 02:29 (попятный проход 2/3; 3/3 — 26.11.2026 05:14, после стоянки D) |
   | Меркурий | ☌ | Плутон | 0°34′ | сх. | — / 14.10.2026 15:27 |
   | Марс | ⚹ | MC | 0°35′ | сх. | — / 15.10.2026 01:33 |
   | Сатурн R | ⚹ | MC | 0°53′ | сх. | 05.05.2026 17:36 / 26.10.2026 03:27 |

   **Тройной проход:** Юпитер □ натального Солнца (24°20′ Льва) — 1/3 **01.11.2026 02:29:51** (прямо), 2/3 **24.01.2027 00:11:19** (R), 3/3 **26.06.2027 12:27:58** (прямо); Horizons: 02:29:56, 00:11:21, 12:28:04. Сатурн □ Урана — 02.11.2026 (R) и 17.01.2027; Сатурн ☌ Венеры 26.02.2027; Уран ☌ MC 20.08.2027 и 11.10.2027 (R); Юпитер ☌ ASC 06.10.2027 (Юпитер входит в 1-й дом в тот же день). Стоянки: Плутон D 16.10.2026, Меркурий R 24.10.2026 (20°59′ Скорпиона) и D 13.11.2026, Венера D 14.11.2026, Сатурн D 10.12.2026, Юпитер R 13.12.2026, Марс R 10.01.2027 (□ MC, ⚹ Юпитера).
4. **Прогрессии:** JD_p = 2448026,9375 + 36,415734 = 2448063,353234 = **1990-06-20 20:28:39 UTC**. Солнце 29°14′29″ Близнецов, Луна **2°01′38″ Близнецов** (9-й натальный дом, 8-й прогрессивный), Меркурий 15°31′ Близнецов, Венера 25°05′ Тельца.
   Углы `mean_sun`: ARMC_p = 68,0119° + 35,8931° = 103,9050°; ε = 23,44197°; MC = **12°47′48″ Рака**, ASC = **9°15′13″ Весов** (вручную по формулам §3.3 — то же до секунды).
   Аспекты к радиксу: прогр. MC □ Венеры 0°03′ (точно 24.09.2026), прогр. ASC □ Урана 0°04′ (05.09.2026), прогр. Меркурий □ ASC 0°08′ (18.09.2026), прогр. Венера △ Сатурна 0°10′ сх. (03.12.2026), прогр. ASC □ Юпитера 0°17′ сх. (17.03.2027), прогр. Венера ☌ Солнца 0°45′ расх. (23.02.2026) и др.
   Прогрессивная Луна вошла в Близнецы 25.08.2026, войдёт в 10-й натальный дом 17.04.2027, в Рак — 23.08.2028.
   **Лунация:** элонгация 332,79° → **Бальзамическая** (с 06.07.2025); следующее прогрессивное новолуние **19.09.2028** (38,35 года).
5. **Солнечная дуга:** истинная 34,9056° (34°54′), Наибода 35,8931° (разница 0,99° ≈ 1 год, типичная ошибка № 3). Направленный MC 14°34′41″ Рака ☍ натального Нептуна 0°13′ расх. (точно 20.07.2026), Меркурий ⚹ Венеры 0°11′ (06.08.2026), Венера ⚹ Марса 0°38′ сх. (13.06.2027), MC ⚹ ASC 0°48′ сх. (16.08.2027).
6. **Соляр 2026 (Москва):** **2026-05-15 03:34:26 UTC = 06:34:26 MSK**; отклонение −0,289 сут; ASC соляра 3°17′10″ Рака (10-й натальный дом), MC 21°44′34″ Водолея; Солнце в 12-м доме соляра; Нептун □ ASC соляра 0°23′. Следующий соляр 15.05.2027 09:09 UTC. Horizons: Δ 0,01″.
   С `sr_place="Новосибирск"`: тот же момент, местное 10:34:26 (UTC+7), ASC в другом знаке (тест `test_relocated_vs_birthplace_same_moment`).
   **Лунар:** 21.09.2026 10:03:34 UTC (13:03 MSK), ASC 5°49′ Стрельца; следующий 18.10.2026.
7. **Профекции:** N = 36 → Дева + 36 mod 12 = **Дева, 1-й дом**; управитель года **Меркурий** (радикс: 8°01′ Тельца, 9-й дом); транзитный Меркурий 14.10.2026 — 15°36′ Скорпиона (3-й дом) и в ретроградной петле 24.10–13.11.2026. Месяц 5 (`equal`: 13.09–14.10.2026): Козерог/Сатурн; другие варианты — табл. 4.9.

### 7.3. T2 — Петров Д. О., 04.02.1984 23:30 MSK, Москва; на 14.10.2026

1. **Натал:** UTC 20:30, JD₀ = 2445735,354167; Солнце 15°13′09″ Водолея, Луна 16°22′51″ Рыб, ASC 19°28′30″ Весов, MC 27°15′12″ Рака, ARMC₀ = 119,3121°.
2. A = (2461327,5 − 2445735,354167)/365,24219 = **42,689882**.
3. **Транзиты на дату:** Меркурий □ Солнца 0°23′ расх.; Меркурий ☌ Сатурна 0°27′ сх. (14.10 12:09); Меркурий △ Луны 0°47′ сх.; Нептун R □ Юпитера 0°50′ (точно 13.09.2026 и 05.03.2027); **Плутон R □ натального Плутона 0°56′ «сх.», точно было 11.12.2025, следующего нет** (§7.4). Тройные проходы — Марс в петле 10.01–01.04.2027: △ Нептуна 27.11.2026 / 20.02.2027 (R) / 16.05.2027; ⚹ Плутона 01.12 / 16.02 / 20.05; △ Юпитера 04.12 / 13.02 / 23.05. Сатурн ☍ ASC 22.04.2027 (Сатурн входит в 7-й дом), Сатурн □ MC 13.07.2027 и 05.09.2027 (R).
4. **Прогрессии:** JD_p = 2445778,044048 = 1984-03-18 13:03:25 UTC; Солнце 28°07′22″ Рыб, Луна 14°02′33″ Весов (12-й натальный дом; в 1-й — 23.02.2027); углы `mean_sun`: ARMC 161,3892° (+42,0772°), MC 9°50′41″ Девы, ASC 17°12′44″ Скорпиона. Аспекты: прогр. ASC △ Луны 0°50′ (05.07.2025), прогр. Солнце △ MC 0°52′ (28.11.2025), прогр. Марс △ MC 0°44′ сх. **Лунация:** 195,92° — **Полнолуние** (с 30.08.2025), последнее прогрессивное новолуние 05.01.2011.
5. **Дуга:** истинная 42,9037°, Наибода 42,0772° (Солнце в феврале быстрое: истинная **больше** Наибодовой на 0,83°). Направленный Плутон ⚹ Солнца 0°11′ сх. (18.12.2026), Юпитер □ Сатурна 0°12′ (03.08.2026).
6. **Соляр 2026 (Москва):** 2026-02-04 01:13:34 UTC = **04:13:34 MSK** (отклонение −0,803 сут: соляр приходится на **4 февраля в 04:13**, а не на «23:30 4 февраля»); ASC 6°49′ Стрельца (2-й натальный дом), MC 11°08′ Весов.
7. **Профекции:** N = 42 → Весы + 42 mod 12 = Весы + 6 = **Овен, 7-й дом**; управитель года **Марс** (радикс 11°59′ Скорпиона: 1-й дом по Плацидусу, 2-й в целых знаках); транзитный Марс 9°05′ Льва (10-й дом) и войдёт в попятную петлю 10.01.2027.

### 7.4. Граничный случай: стоянка до точного аспекта (T2, Плутон □ Плутон)

Квадрат натальному Плутону (2°08′10″ Скорпиона) — это 2°08′10″ Водолея. Цикл Плутона (расчёт модуля): точные проходы **03.02.2025 14:49** (прямо), **13.08.2025 23:27** (R), **11.12.2025 01:03 UTC** (прямо) — тройной проход завершён; стоянки: R 04.05.2025 (3°49′ Водолея), D 14.10.2025 (1°22′), R **06.05.2026 (5°30′34″)**, D **16.10.2026 02:40 UTC на 3°04′07″ Водолея** — в 0,93° от точного квадрата. 14.10.2026 Плутон попятный и приближается к квадрату (фаза «сходящийся»), но поворачивает раньше, поэтому `exact_next_utc = null`, а в `stations` эта стоянка помечена `aspects_to_natal: □ Плутона, орбис 0,93°`. Агенту: «аспект в орбисе и усиливается, но точным в этом цикле больше не станет; стоянка в орбисе натальной точки — сильный момент (AstroWiki)».

### 7.5. T3 и граничные случаи: 29 февраля, полярный соляр, неизвестное время

**T3 — Смирнова М. А., 29.02.2004 08:15 MSK, Санкт-Петербург; на 14.10.2026.**
1. Натал: UTC 05:15, JD₀ = 2453064,71875; Солнце 9°57′30″ Рыб, ASC 19°01′17″ Рыб, MC 27°39′35″ Стрельца, ARMC₀ = 267,4497°. A = **22,622746**.
2. Транзиты на дату: Венера R △ Сатурна 0°06′, Юпитер ⚹ Луны 0°11′ (точно 12.10.2026, затем 14.02.2027 R и 09.06.2027), Юпитер △ Плутона 0°17′ сх. (15.10.2026; тройной: 10.02.2027 R, 12.06.2027), Меркурий ☍ Марса 0°53′, Солнце △ Луны 0°56′. Уран □ Урана 07.12.2026 (R) и 10.04.2027.
3. Прогрессии: JD_p = 2453087,341496 = 2004-03-22 20:11:45 UTC; Солнце 2°32′ Овна, Луна 24°50′ Овна (12-й прогрессивный, 1-й натальный дом; Телец — с 14.03.2027); углы `mean_sun` MC 18°13′48″ Козерога, ASC 2°26′31″ Близнецов; **лунация: Новолуние** (элонгация 22,30°, прогрессивное новолуние было 20.11.2024 в 20,7 года).
4. Дуга: истинная 22,5817°, Наибода 22,2980°; направленная Венера ☌ Марса 0°06′ сх. (21.11.2026), Нептун ☌ Меркурия 0°12′ сх. (24.12.2026).
5. **Соляр 29 февраля в невисокосный год:** 2026-02-28 13:17:55 UTC = **28.02.2026 16:17:55 MSK** (отклонение −0,665 сут от 01.03 — годовщины в невисокосный год); ASC соляра 21°49′ Льва, MC 0°18′ Тельца. Соседние годы (местное время MSK, UTC+3): 2027 — 28.02 22:03:16; 2028 (високосный) — **29.02 03:47:54**; 2100 (невисокосный по григорианскому правилу) — 28.02 15:02:13.
6. Профекции: N = 22 → Рыбы + 22 mod 12 = Рыбы + 10 = **Козерог, 11-й дом**, управитель **Сатурн** (радикс 6°20′ Рака, 4-й дом по Плацидусу, 5-й в целых знаках; транзит 10°34′ Овна R в 1-м доме). Месяц 8 (`equal`: 29.09–30.10.2026): Лев/Солнце; `calendar` (29-е число) и `valens` — тоже Лев, `thirteen` — 9-й из 13, Дева/Меркурий.

**Соляр за полярным кругом:** T1, соляр 2026 на Мурманск (68,9585N, 33,0827E): Плацидус не определён → Порфирий (`houses.system = "O"`), ASC 29°58′ Рака, предупреждение «Соляр: Система домов Плацидус… не определена».

**Неизвестное время:** T1 без времени (натал на 12:00 MSD): нет домов, углов, прогрессивных углов, профекций от ASC (`profections = null`; с `profection_from="sun"` — Телец + 36 ≡ **Телец**, Венера); момент соляра 15.05.2026 01:04:34 UTC вместо 03:34:26 (±12 ч — без углов); предупреждение о Луне.

**Сидерический соляр** T4 1905: 15.03.1905 02:49:27 UTC — на 8,6 ч позже тропического (26 лет × 0,0142 сут = 0,37 сут ✓).

### 7.6. Внешние примеры: фазы прогрессивной лунации (F. Boele, astro.com)

Данные рождения из статьи (время, пояс, координаты как опубликованы); фаза на дату события по нашему расчёту. Где в статье дан только месяц или год, взятая дата помечена «взято» (тест `test_progressed_lunation_boele`):

| Персона | Событие (дата) | Фаза по статье | Расчёт: элонгация → фаза |
|---|---|---|---|
| М. Тэтчер (13.10.1925 9:00 GMT, Грантем) | отставка 22.11.1990 | New | 23,25° New ✓ |
| П. Маккартни (18.06.1942 14:00 GDWT, Ливерпуль) | уход из Beatles 09.04.1970 | New | 31,33° ✓ |
| Р. Старр (07.07.1940 0:05 GDT) | распад Beatles (взято 10.04.1970) | New | 25,76° ✓ |
| Б. Олдрин (20.01.1930 14:17 EST) | Луна 20.07.1969; депрессия «Oct. 1971» (взято 15.10.1971) | New | 8,22° / 33,76° ✓ |
| Иоанн Павел II (18.05.1920 17:30 EET) | избрание 16.10.1978 | New | 2,94° ✓ |
| Н. Армстронг (05.08.1930 0:31 EST) | лётчик ВМС «from 1949 to 1952», вылеты в Корее (взято 01.01.1951) | New | ✓; фаза New по расчёту 06.07.1949–01.10.1952 (на 01.01.1949 — 352,7°, Balsamic) |
| Дж. Леннон (09.10.1940 18:30 GDT) | «signed them two months later» (контракт с Эпштейном, взято 24.01.1962) | New | 1,43° ✓ (знакомство «Nov. 1961», взято 15.11.1961 — 358,7°, за 33 дня до прогрессивного новолуния 18.12.1961) |
| У. Черчилль (30.11.1874 1:30 GMT) | «Five years later… victory over Hitler» (взято 08.05.1945) | New | 27,93° ✓ |
| Дж. Р. Р. Толкин (03.01.1892, «20–24 ч» LMT; взято 22:00) | канун публикации, 29.07.1954 | First Quarter | 97,56° ✓ |
| Принцесса Диана (01.07.1961 19:45 GDT) | свадьба 29.07.1981 | First Quarter | 100,54° ✓ |
| Дж. Леннон | брак с Йоко Оно 20.03.1969 | First Quarter | 93,32° ✓ (развод 08.11.1968 — 89,19°, за 25 дней до начала Первой четверти 03.12.1968) |
| С. Рушди (19.06.1947 2:30 IST) | фетва 14.02.1989 | Gibbous | 152,27° ✓ |
| Н. Армстронг | полёт «six year old» (взято 05.08.1936); Gemini 8 16.03.1966 | Full | 199,34° / 199,05° ✓ |
| П. Маккартни | первое выступление с Ленноном 18.10.1957 | Disseminating | 251,58° ✓ |
| Н. Армстронг | Луна 20.07.1969 | Disseminating | 237,19° ✓ |
| Н. Мандела (18.07.1918 14:54 EET, DD) | освобождение 11.02.1990 | Last Quarter | 281,06° ✓ |
| М. Али (17.01.1942 18:35 CST) | смена имени «shortly after» 25.02.1964 (взято 06.03.1964) | Last Quarter | 277,04° ✓ |
| В. ван Гог (30.03.1853 11:00 LMT) | выстрел 27.07.1890 | Balsamic | 344,72° ✓ |
| М. Али | «title was revoked in 1967» (взято 28.04.1967) | Balsamic | 318,96° ✓ |
| Маккартни, Старр | «Beatles Anthology» 1995 (взято 01.06.1995) | Balsamic | 341,42° / 328,16° ✓ |
| У. Черчилль | премьер 10.05.1940, речи 04.06 и 20.08.1940 | Balsamic | 325,45° / 326,25° / 328,75° ✓ |
| Э. Рузвельт (11.10.1884 11:00 EST) | Декларация прав человека 10.12.1948 | Balsamic | 330,38° ✓ |
| Н. Мандела | президент 10.05.1994 | Balsamic | 329,54° ✓ |

### 7.7. Внешний пример: первичные дирекции к углам (принц Чарльз, Makransky)

**Вход:** 14.11.1948 21:14:39 GMT, 51°30′N, 0°10′W (как в спекулуме Makransky), `primary_directions=True`.
1. Спекулум: RAMC 12,3689° (Makransky 12,37 = ST 0h49m28s); ε истинный 23,4480° (у Makransky 23,4459 — средний). α/AD: Солнце 230,01/−24,69 (230,01/−24,70), Луна 28,48/14,47 (28,47/14,46), Сатурн 157,63/14,04 (157,63/14,03), Плутон 141,48/32,38 (141,49/32,37), Уран 89,92/33,40 (89,93/33,40), Юпитер 269,88/−32,92 (269,87/−32,93).
2. Дуги (in mundo): MO ☌ MC = 28,48 − 12,37 = **+16,11** d (16,10); SU ☌ IC = 230,01 − 192,37 = **+37,64** d (37,64); SA ☌ IC = **−34,74** c (−34,74); PL ☌ ASC = (141,48 − 32,38) − 102,37 = **+6,74** d (6,75); UR ☌ ASC = (89,92 − 33,40) − 102,37 = **−45,85** c (−45,84); JU ☌ DSC = (269,88 − 32,92) − 282,37 = **−45,41** c (−45,43). In zodiaco: JU ☌ DSC **−45,54** c (−45,54).
3. Сроки — табл. 4.10 (Makransky в скобках): расхождение дат ≤ 4 сут, т. е. ≤ 0,02° дуги — разница эфемерид 1980-х и Swiss Ephemeris.
Тесты: `test_primary_directions_makransky_arcs`, `test_primary_directions_makransky_speculum_and_keys`.

### 7.8. T1 с опциями: конверсные прогрессии, первичные дирекции, окно точных дат

**Конверсные прогрессии на 14.10.2026** (`progression_direction="converse"`): JD_p = 2448026,9375 − 36,415734 = **1990-04-09 00:31:20 UTC**; Солнце 18°54′18″ Овна, Луна 6°29′40″ Весов (−12,16°/год, 2-й натальный дом); `mean_sun`: ARMC 68,0119° − 35,8931° = 32,1188°, MC 4°22′52″ Тельца, ASC 21°41′40″ Льва. Луна «вошла» в Весы (из Скорпиона) 01.11.2024, перейдёт в 1-й натальный дом 25.10.2026 (назад через куспид 2-го дома 6°08′ Весов) и в Деву 26.04.2027. Лунация: 167,59° — **Выпуклая** (с 01.09.2025, когда элонгация убывала через 180°), следующая фаза — **Первая четверть** 25.08.2029; последнее конверсное новолуние 15.08.2010.

**Первичные дирекции** (`primary_directions=True`, Наибод, in mundo): до 100 лет — 21 дирекция; в пределах ±1 года от 14.10.2026 (`near_on_date`) — ни одной; недавние — ☿ ☌ MC c (дуга −31,53°, 11.05.2022), ♅ ☌ IC d (+32,01°, 04.11.2022), ♃ ☌ MC d (+32,37°, 17.03.2023); следующая — ♆ ☌ IC d (+37,47°, **21.05.2028**), затем ♀ ☌ DSC d (+39,39°, 03.05.2030).

**Окно точных дат** (T2, `exact_window_years=30`): прогр. Сатурн △ Луны — точно 25.10.2005, прогр. Сатурн □ Солнца — 19.10.2041, прогр. Марс △ MC — 09.01.2031 (при окне 3 года — `null`).

---

## 8. Ключи интерпретации

### 8.1. Транзитные планеты (AstroWiki «Transit»)

| Транзит | Ключ |
|---|---|
| Солнце | усиливает осознание темы натальной точки; действует часы — 1–2 дня |
| Луна | эмоциональный фон, настроения; часы |
| Меркурий | понимание, общение, короткие поездки |
| Венера | чувственное восприятие, отношения, искусство |
| Марс | активизирует сферу, но время остерегаться ссор и несчастных случаев; частый «спусковой крючок» для медленных транзитов |
| Юпитер | рост, поиск смысла в затронутой сфере; с ретроградной петлёй — недели–месяцы |
| Сатурн | созревание, концентрация на главном; ограничения, разочарования, ответственность; до года |
| Уран | освобождение и перемены; неожиданные повороты, тревога у тех, кто боится перемен; 2–3 года |
| Нептун | повышенная чувствительность; разочарование, утрата иллюзий, растворение; с петлёй — до 2–3 лет |
| Плутон | разрушение изживших себя структур, исцеление и трансформация («greater sense of personal wholeness»); до 2–3 лет |
| Меркурий, Венера, Марс в ретроградной петле (тройной проход) | «considered to be more significant» |
| Стоянка в орбисе натальной точки | «very powerful» (AstroWiki) |
| Ингрессия в натальный дом | тема дома; важнейшие моменты — пересечение куспидов |

Аспекты: соединение важнее всего, затем квадрат и оппозиция, затем секстиль и тригон; у Сатурна…Плутона разница «гармоничный/напряжённый» менее значима (AstroWiki «Transit»). Фон транзита — роль транзитной планеты в радиксе (дом, знак, аспекты); «спусковые крючки» длительных транзитов — новолуние/полнолуние или затмение на том же градусе, быстрая планета (особенно Марс), транзит через натальное место самой медленной планеты (AstroWiki «Transit», раздел «Trigger»). Медленные транзиты (Сатурн…Плутон) — «life-changing events or processes» (AstroWiki «Transit»); быстрые — «opportunities, health, moods and states of mind», медленные — «cycles of development… learning phases, crises, as well as periods of stability and happiness» (astro.com FAQ «Transits»).

### 8.2. Прогрессии и дирекции (AstroWiki «Secondary Progression», «Solar Arc», «Direction»)

| Событие | Ключ |
|---|---|
| Аспект прогрессивной/направленной точки к натальной | «спусковой крючок»: натальная тема активируется; главное — какие планеты, а не тип аспекта |
| Прогрессивная/направленная планета входит в новый знак или дом | смена жизненной ориентации, начало новой фазы |
| Прогрессивная Луна в натальном доме | активирует тему этого дома ~2½ года |
| Прогрессивная планета меняет направление (R ↔ D) | смена направленности темы планеты (пример AstroWiki: натальный R Меркурий становится прямым — меньше интроверсии) |
| Прогрессивное Солнце в новом знаке | к натальным качествам добавляются качества нового знака (Овен → Телец: + стабильность, материальность) |
| Взаимный аспект двух прогрессивных планет | «mutual exchange of energy» (калькулятор такие аспекты не выводит) |
| Какие прогрессии главные | обычно личные планеты (Солнце, Луна, Меркурий, Венера, Марс); медленные — у пожилых, особенно у конца знака или дома (AstroWiki) |
| Прогрессивные углы | только при времени рождения с точностью до минуты («accurate to within a minute»), иначе ошибка ≥ 1 года |
| Направленная точка (дуга) к натальной | «trigger», орбис до 1° — действует несколько месяцев; вход в знак/дом — новая фаза (AstroWiki «Solar Arc») |
| Конверсные прогрессии, первичные дирекции | ⚠ отдельных ключей толкования в источниках модуля нет (Makransky: «no interpretations are given») — толковать как аспект/соединение соответствующих планет и углов |

### 8.3. Фазы прогрессивной лунации (F. Boele, «The Progressed Lunation Cycle»)

| Фаза | Ключ (Boele, прогрессивная фаза) |
|---|---|
| Новолуние | «both the beginning and the end of the cycle»: потери и завершения, траур и переориентация, «movement towards home», переезд/новые корни; начинания малы и почти незаметны |
| Растущий серп | рискнуть, чтобы начать свою историю: выйти из дома, учёба, свидания, ребёнок; нужна поддержка, человек ещё действует внутри прежней группы |
| Первая четверть | «a clean break from the past»: независимость, конфронтация с «другим», свадьбы и разводы, выход в мир |
| Выпуклая | мир расширяется (путешествия, учёба, новые горизонты); «everything grows big» — возможности, проблемы и эмоции; легко переусердствовать |
| Полнолуние | кульминация: успех или поражение, «a release of energy», ясность и видение, иногда призвание |
| Распространяющая | вернуться и поделиться результатом, найти свою нишу и единомышленников; порой тихое время «в изгнании» |
| Последняя четверть | кризис личности: «who we are, what we want», бунт против коллектива/общества, новая идентичность, страх «не успеть» |
| Бальзамическая | мир сужается: уходят опоры, планы срываются, нужно беречь здоровье; «it's now or never» — отпустить страхи и иллюзии, высказать несказанное, мемуары; образ «ripe and rotten fruit which releases the seed» |

AstroWiki «Lunation Cycle» (по Д. Радьяру) даёт ключи **натальной** фазы (типы личности: 1 — «subjective, impulsive», 6 — «need to teach and communicate» и т. д.) — для прогрессивной фазы их не подставлять.

### 8.4. Соляр и лунар (AstroWiki «Solar Return Chart», «Lunar Return Chart»)

| Фактор соляра | Ключ |
|---|---|
| ASC соляра | общий подход к жизни в этот год |
| MC соляра | цель года |
| Натальные дома, где стоят ASC и MC соляра | активированы |
| Управитель ASC соляра | активированы натальный дом и дом соляра, где он стоит |
| Дом соляра с Солнцем; дом с 3+ планетами | акценты года |
| Планеты в аспекте к углам соляра (особенно ☌ ASC) | особенно значимы |
| Аспект, повторяющий натальный | натальная тема получает новый импульс |
| Натальные планеты с множеством аспектов от планет соляра | активированы |
| Лунар | эмоциональный фон и повседневность на месяц: углы лунара (особенно соединения с ними), аспекты к Луне, дом лунара с Луной, натальные дома ASC и MC лунара; из аспектов — прежде всего соединения и оппозиции |

Соляр «only makes sense against the backdrop of the natal chart»; его темы ощущаются за 1–2 месяца до дня рождения; он «more concerned with current events», но это не «prediction of events» (AstroWiki).

### 8.5. Профекции (C. Brennan)

| Фактор | Ключ |
|---|---|
| Знак/дом года | тема года — тема этого дома радикса (целые знаки) |
| Управитель года | активирован «и в натальном положении, и в транзитах»: его натальное состояние (секта, достоинства, дома, аспекты) окрашивает год |
| Транзиты к управителю года и от него, транзиты через знак года | особенно значимы в этот год (Brennan, «Hellenistic Astrology», гл. 17, по Гефестиону 2.27: «Transits to the lord of the year in the natal chart; Transits by the lord of the year to natal planets; Transits through the profected sign that year») |
| Состояние управителя года | «can dictate the quality of the year»: что планета «обещает» в радиксе, то и проявится (там же) |
| Натальные планеты в знаке года | тоже активированы (в т. ч. высшие планеты, которые управителями не считаются) |
| 12-летний цикл | годы 12, 24, 36… — снова тема 1-го дома |
| Месяц, когда месячная профекция приходит в знак с натальным управителем года | «the most important month in the native's life in that particular year» (правило Р. Цоллера, у Brennan, гл. 18, прим. 24); D. George: «it is during that month that the effects of how the time lord is functioning… become fully apparent» |

---

## 9. Источники

| Источник | Что взято | Надёжность |
|---|---|---|
| astro.com FAQ «Overview chart types»: https://www.astro.com/cgi/xa.cgi/faq/fq_fh_owtype_e.htm | определение вторичных прогрессий, ключ Наибода 0,98564733°, способ углов astro.com (ARMC + Наибод), описание Solar Fire (MC + дуга), опции «MC from solar arc», «ARMC 361° / prog. Day», прогрессивное новолуние ~29,5 лет; дирекции солнечной дуги astro.com — средняя дуга (возраст × 0,98564733°) | первоисточник (сайт-калькулятор, Swiss Ephemeris) |
| astro.com FAQ «Other methods»: https://www.astro.com/cgi/xa.cgi/faq/fq_fh_methods_e.htm | «1 day = 1 year», ARMC +3 м 56 с в сутки, нет «SA in Longitude» для прогрессивной карты, отказ от поправки на прецессию, конверсные прогрессии отрицательным возрастом, опции первичных дирекций (`mb`, `mc`, `ms`) | первоисточник |
| astro.com FAQ «Calculations»: https://www.astro.com/cgi/xa.cgi/faq/fq_fh_calc_e.htm | прогрессии на полночь UT | первоисточник |
| astro.com FAQ «Forecast Horoscopes»: https://www.astro.com/cgi/xa.cgi/faq/fq_sh_fore_e.htm | орбис 1° у Р. Хэнда, орбисы Лиз Грин шире | первоисточник |
| astro.com FAQ «Duration», «Transits»: https://www.astro.com/cgi/xa.cgi/faq/fq_fh_dura_e.htm , …/fq_fh_transits_e.htm | период действия транзита (первый вход — последний выход vs только в орбисе); надёжна дата точного аспекта | первоисточник |
| astro.com FAQ «Return charts»: https://www.astro.com/cgi/xa.cgi/faq/fq_fh_return_e.htm | место соляра (где проведён день рождения), возвраты других планет через транзитный календарь | первоисточник |
| AstroWiki (astro.com), вики-исходники `https://www.astro.com/wiki/astrowiki-en/index.php?title=<Статья>&action=raw`: Secondary_Progression, Solar_Arc, Naibodic_Arc, Solar_Return_Chart, Lunar_Return_Chart, Transit, Direction, Profection, Lunation_Cycle | определения, орбисы, места соляра, ключи интерпретации, системы профекций | школа/энциклопедия (вторичный, редакция Astrodienst) |
| C. Brennan, «Introduction to Hellenistic Astrology (2) — Annual Profections, Lots, and Zodiacal Releasing», TMA 2018 / astro.com 2019: https://www.astro.com/cgi/xa.cgi/astrology/tma_article190314_e.htm | правило профекций, счёт с 0, 12-летний цикл, смена на соляре, пример Копполы | школа (эллинистическая, современный исследователь) |
| The Astrology Podcast, эп. 153 (транскрипт): https://theastrologypodcast.com/transcripts/ep-153-annual-profections-an-ancient-time-lord-technique/ | традиционные управители, только домицил, смена «в день рождения», месячные профекции упомянуты | школа (транскрипт; авторы предупреждают о возможных ошибках расшифровки) |
| F. Boele, «The Progressed Lunation Cycle», TMA 2006 / astro.com: https://www.astro.com/cgi/xa.cgi/astrology/in_progmoon_e.htm | границы фаз, 30 датированных примеров с данными рождения | школа (практик) |
| Astrotheme, Ф. Ф. Коппола: https://www.astrotheme.com/astrology/Francis_Ford_Coppola | данные рождения AA (07.04.1939 1:38, Детройт), ASC 7°24′ Козерога | калькулятор (SE) + данные Rodden |
| Wikipedia, «Astrological progression»: https://en.wikipedia.org/wiki/Astrological_progression | пример 1982 → 2007; орбис прогрессий 1° | вторичный |
| Astrolog 8.00, исходники: https://github.com/CruiserOne/Astrolog (`astrolog.h`: `rDayInYear 365.24219`; `calc.cpp`: прогрессии `is.T += (is.JDp − is.T)/us.rProgDay`) | длина года прогрессий | калькулятор (открытый код) |
| Kerykeion, «Guide: orbs — which to use»: https://kerykeion.net/content/learn-astrology/guide-orbs-which-to-use | транзитные орбисы 1–3° / ≤ 1° | вторичный |
| B. Makransky, «Primary Directions. A Primer of Calculation» (archive.org): https://archive.org/details/bob-makransky-primary-directions-a-primer-of-calculations-i | формулы дирекций к углам (AD, OA/OD, гл. I–II), ключи Птолемея, Наибода, Симмонайта, Плацидуса (гл. III), спекулум и примеры принца Чарльза | школа (учебник расчёта) |
| R. Hand, «Planets in Transit» (1976), полнотекстовый поиск archive.org: https://archive.org/details/planetsintransit00hand | Transit Rule 2 (орбис как время), отчёт «enters one degree of orb» | школа (автор отчётов astro.com) |
| C. Brennan, «Hellenistic Astrology: The Study of Fate and Fortune» (2017), archive.org: https://archive.org/details/chris-brennan-hellenistic-astrology-the-study-of-fate-and-fortune-1 | профекции «monthly, daily, or even hourly», управитель года и транзиты (Гефестион 2.27), правило Цоллера о месяце | школа |
| Vettius Valens, «Anthologies», пер. M. T. Riley (изд. 2019, archive.org): https://archive.org/details/vettius-valens-anthologies | месяц по Валенту IV.28 (Солнце→Солнце / Луна→Луна от знака года), V.6 («the King») | первоисточник (перевод) |
| Ptolemy, «Tetrabiblos», пер. J. M. Ashmand (1822), archive.org: https://archive.org/details/ptolemystetrabib00ptol | IV.10: «twenty-eight days per sign» для месяцев, «two days and a third» для дней | первоисточник (перевод) |
| R. Schmidt (пер.), R. Hand (ред.), «Dorotheus, Orpheus, Anubio & Pseudo-Valens: Teachings on Transits», Project Hindsight IX (1995), предисловие Хэнда: https://archive.org/details/dorotheus-orpheus-anubio-and-valens-transits | 13 знаков месячной профекции в год (≈ 28 сут) | школа (комментарий переводчика) |
| D. George, «Astrology and the Authentic Self» (2008), archive.org: https://archive.org/details/demetra-george-astrology-and-the-authentic-self-integrating-traditional-and-modern-astrology | календарные месяцы профекции от дня рождения, месяц управителя года | школа |
| AstroWiki «Profection» (raw): https://www.astro.com/wiki/astrowiki-en/index.php?title=Profection&action=raw | пример Knappich «27 years, 6 months, and 5 days» (месяцы возраста) | школа/энциклопедия |
| Astracadabra v1, руководство (© 2004–2008 Esoteric Technologies — производитель Solar Fire), archive.org: https://archive.org/details/manualzilla-id-5647155 | пять способов прогрессии MC: S.A. in Long., S.A. in R.A., Naibod in Longitude, Naibod in R.A., Mean Quotidian | калькулятор (документация) |
| «Astrolog32 Wish List» (Philipeau), archive.org: https://archive.org/details/manualzilla-id-5834499 | «Solar Fire currently has Naibod in longitude and r.a., and solar arc in long. and r.a.»; старый Astrolog — «Naibod right ascension» | вторичный (пользовательский документ) |
| K. B. Riske, «Llewellyn's Complete Book of Predictive Astrology» (2011), поиск archive.org: https://archive.org/details/llewellynscomple0000risk | предпочтение «Naibod in longitude» | вторичный |
| Astrolog 8.00, `calc.cpp` (`CastChart`, `SwissHouse`), `charts0.cpp` (справка `-p`, `-p1`, `-pc`, `-pC`): https://github.com/CruiserOne/Astrolog | прогрессивные куспиды по умолчанию — на прогрессивный момент (quotidian); `-p1 -pc` — MC + солнечная дуга, ε рождения | калькулятор (открытый код) |
| Wikipedia «Annus mirabilis papers», «Albert Einstein», «Einsteinhaus» | 30.06.1905 — поступление статьи о СТО; Берн 1902–1909 | вторичный |
| JPL Horizons API: https://ssd.jpl.nasa.gov/api/horizons.api (DE441, ObsEcLon) | независимая сверка моментов соляров, прогрессивных положений, точных транзитов и стоянок | первоисточник (астрономическая эфемерида) |
| Swiss Ephemeris (pyswisseph) — через `common/ephemeris.py` | все положения, `houses_armc`, наклон эклиптики | первоисточник |

---

## Протокол проверки

**14.10.2026, автор модуля.** Тесты: `.venv/bin/python -m pytest calculators/tests/test_forecast_western.py -q` — 133 теста, все зелёные, пропусков нет (прежние 6 пропусков — соляры «до рождения» в параметризации по фиксированным годам — заменены годами от рождения: +1, +4, +26, +50, +96).

1. **Независимая эфемерида (JPL Horizons, DE441, 40+ запросов к API).** Солнце в момент соляра = натальному: T4 1905 Δ 0,09″, T1 2026 Δ 0,01″. Прогрессивные Солнце и Луна T4: 0,30″ и 0,27″. 11 точных транзитов (тройные проходы Юпитер □ Солнце T1, Сатурн □ Уран T1, Уран △ Уран и Сатурн ☌ Юпитер T4): Δ ≤ 15 с (2026–27), ≤ 2,5 мин (1905). 14 стоянок: ≤ 0,11 ч, Плутон 0,7–1,1 ч (плоский экстремум). Моменты Horizons зашиты в тесты `test_exact_hits_vs_horizons`, `test_stations_vs_horizons`.
2. **Независимый пересчёт pyswisseph в тестах** (не через код модуля): корни точных транзитов, ингрессий, стоянок, прогрессивные положения, события прогрессивной Луны, моменты точных дирекций, соляр/лунар.
3. **Опубликованные примеры.** Boele: 28 утверждений — 28 совпадений (где в статье только месяц/год, дата помечена «взято»); 2 события Леннона у границы фазы (на 25 и 33 дня раньше нашей границы ≈ 1 ч времени рождения) вынесены в отдельный тест с допуском. Brennan: профекции Копполы 4/4. Wikipedia: 1982 → 27.04.1982. astro.com/AstroWiki: формула `mean_sun` (ARMC + 0,98564733° × A) и «3 мин 56,555 с».
4. **Ручные формулы.** Прогрессивные MC/ASC T1 и T4 по формулам §3.3 (`mc_from_ramc`, `asc_from_ramc` из модуля 06) совпали с `swe.houses_armc` до секунды дуги (§7.1, §7.2).
5. **Граничные случаи:** 29.02 (соляры 2005, 2026–2028, 2100), полярный соляр (Порфирий), неизвестное время, сидерический соляр (+0,37 сут при 26 годах), стоянка до точного аспекта (T2), `on_date` до рождения (ошибка).

**⚠ Не подтверждено / ограничения** (состояние на 14.10.2026; что закрыто 15.10.2026 — в «Повторной проверке» ниже).
- Умолчание Solar Fire для прогрессивных углов (MC + солнечная дуга) известно только из описания astro.com; первоисточник Solar Fire не открыт.
- Варианты `naibod` (в долготе) и `solar_arc_ra` реализованы по определению ключа Наибода и солнечной дуги; программ, где они умолчание, в источниках модуля нет.
- Орбисы Лиз Грин для транзитов не опубликованы.
- Механика месячных профекций (равные 1/12 года) — одна из версий; 28-дневные и календарные месяцы, а также профекции Хуберов/Мюнхенской школы не реализованы.
- Значимость даты 30.06.1905 и проживание Эйнштейна в Берне — общеизвестные факты, в модуле не проверялись.
- Конверсные прогрессии и первичные дирекции не реализованы (astro.com предлагает их отдельно).
- Сверка с готовыми карточками соляров/прогрессий astro.com и astro-seek не выполнена: astro-seek отвечает 403 (защита от ботов), карты astro.com строятся только в сессии пользователя; вместо них — JPL Horizons и опубликованные датированные примеры.

**Бюджет.** WebSearch: 6 запросов. WebFetch: 4 (Wikipedia, Kerykeion, транскрипт подкаста, документация Ketu — без численных примеров). curl: astro.com FAQ (12 страниц), AstroWiki (вики-исходники, 15), статьи TMA (2), Astrotheme (1), GitHub Astrolog (1), JPL Horizons (~45 запросов, ответы закэшированы в рабочей папке сессии). web.archive.org не использовался.

### Протокол независимой проверки

**14.10.2026, независимый верификатор (adversarial).** Тесты после правок: `.venv/bin/python -m pytest calculators/tests/test_forecast_western.py calculators/tests/test_western.py -q` — 216 тестов (140 + 76), все зелёные.

1. **Пересчёт pyswisseph напрямую, без кода модуля** (T1 и T4 на 14.10.2026, T4 на 30.06.1905): натал (JD₀, планеты, ASC, MC, ARMC), транзитные положения и аспекты в орбисе 1° с фазой (T1: Меркурий ⚹ ASC 0,2195°, ☌ Плутона 0,5717°, Марс ⚹ MC 0,5881°, Сатурн ⚹ MC 0,8895°; T4-2026: Плутон ⚹ Меркурия 0,0743°, Нептун ☌ Меркурия 0,6327°; T4-1905 — 5 аспектов §7.1), прогрессивная дата и Солнце/Луна, прогрессивные MC/ASC способами `mean_sun`, `naibod`, `solar_arc` (+ `solar_arc_ra`, `quotidian` для табл. 4.8), истинная и Наибодова дуги, все направленные точки и их аспекты, момент соляра 2026 (UT) и его ASC/MC на месте рождения, профекция (T4-2026: N = 147 → Весы, Венера, 4-й дом). **Все значения совпали с `calculate` до 1″** (расхождение ≤ 1″ в MC соляра — от округления натальной долготы Солнца до 10⁻⁶° в модуле 06, ≈ 0,09 с).
2. **Точные моменты — перебором (brute force)**, часовая сетка + линейная интерполяция по всем целям «натал ± угол», без кода поиска модуля: T1 2026–27 (Марс…Плутон: 66 попаданий; Меркурий и Венера: 207), T4 1905 (77), T2 2025–26 (Сатурн, Нептун, Плутон, включая стоянку Плутона до точного □ Плутона), T3 — Луна и Солнце за 6 недель (183). Число попаданий, ингрессий в знаки и дома и стоянок совпало полностью, расхождение моментов ≤ 2·10⁻⁵ сут (стоянки — в пределах шага сетки). Отдельно перебором подтверждены точные даты прогрессий и дирекций (прогр. MC □ Венеры 24.09.2026 03:05, ASC □ Урана 05.09.2026 23:26, вход прогр. Луны в Близнецы 25.08.2026 и в Рак 23.08.2028, прогр. новолуние 19.09.2028, начало Бальзамической фазы 06.07.2025, направленный Юпитер ☌ Солнца T4 10.07.1905 21:09).
3. **Числа разобранных примеров §7.1–§7.5, JSON §5 и табл. 4.8** сверены с выводом калькулятора построчно — расхождений нет (минуты в тексте — округление). Табл. 4.7 пересчитана (SE, 2000–2050) — совпадает в пределах краевого счёта периодов. Ручные формулы: ε(JD_p) T4 23,45638°, T1 23,44197° ✓; 4 значения Boele (Тэтчер, Диана, Рушди, Мандела) пересчитаны напрямую ✓.
4. **Источники перечитаны** (curl/WebFetch): astro.com FAQ «Overview chart types» (ARMC + 0,98564733° × возраст ✓; Solar Fire: MC + дуга ✓; «ARMC 361° / prog. Day» ✓; **дирекции солнечной дуги astro.com — по Наибоду**), «Other methods» (3m56s в сутки, отказ от precession correction ✓), «Calculations» (полночь UT ✓), «Forecast Horoscopes» (1° у Хэнда ✓), «Duration» ✓, «Return charts» ✓; AstroWiki Solar_Arc, Naibodic_Arc (59′08,33″ = 0,98564733°, 3 мин 56,555 с ✓), Secondary_Progression, Profection, Solar_Return_Chart, Transit ✓; Brennan TMA (правило от ASC, счёт с 0, 12-летний цикл, смена на соляре, Коппола 4/4 ✓); подкаст эп. 153 (три цитаты ✓); Boele ✓; Wikipedia (1982 → 27.04.1982, орбис 1° ✓); Astrolog `rDayInYear 365.24219` и `rProgDay` по умолчанию = `rDayInYear` (`data.cpp`) ✓.

**Найдено и исправлено.**
- **Код:** местное время соляра/лунара на месте рождения и граница «день рождения» в профекциях брались в поясе **рождения**. При `tz="LMT"` или фиксированном смещении это неверно для последующих лет (T4: соляр 2026 «02:57:25 LMT» вместо 03:17:28 CET; соляр 1905 — 18:52:58 вместо гражданских 19:13:01 CET; T1 с `tz="UTC+04:00"` — летнее время 1990 г. переносилось на 2026 г.). Теперь берётся IANA-зона по координатам (tzdb на дату события) с предупреждением, а до введения поясного времени — LMT места. Момент и углы не менялись. Тест `test_birthplace_return_local_time_uses_civil_zone`.
- **Документ:** (а) не было сказано, что astro.com строит дирекции солнечной дуги по **средней** дуге (Наибод), — добавлено в §1.2, §1.3, типичную ошибку 3 и §9; (б) инвариант «соляр < 1 сут от годовщины» неверен около 1900/2100 гг. (до +1,70 сут) — уточнено в §3.5, §6, ошибке 10, тест `test_solar_return_more_than_a_day_near_1900`; (в) «пять проходов у Урана» — по AstroWiki только Нептун и Плутон; расчёт SE 1850–2150: Уран ≤ 3, Нептун до 5, Плутон около афелия до 7 (§3.2); (г) цитата «life-changing events or processes» — из AstroWiki «Transit», а не из FAQ astro.com (§8.1); (д) §7.2: точный момент Меркурий ⚹ ASC 02.11.2026 — попятный проход внутри петли, а не «после петли» (добавлен 3-й проход 26.11.2026); (е) годы соседних соляров T3 — местное время MSK. Добавлен §3.8 «Ручная прикидка» с формулой Δ_соляра ≈ 0,24219·N − L (±1,5 ч на 400 случайных рождениях; тест `test_solar_return_manual_formula`).
- **Ссылки в тестах:** `https://www.astro.com/astrology/…` (Boele, Brennan) отдают curl-у страницу защиты от ботов («One moment…»); заменены на рабочие `https://www.astro.com/cgi/xa.cgi/astrology/…` (как в §9).

**Остаточные риски.** Сверка с готовыми картами прогрессий/дуг astro.com и Solar Fire по-прежнему не выполнена (только описания способов); выбор ε (истинный наклон на JD_p) для прогрессивных углов не подтверждён ни одной программой (влияние ≤ 4″: у T4 ASC сдвигается на 3,6″ при среднем ε вместо истинного, при ε рождения — на 0,2″); окно поиска точной даты прогрессий ±3 года — у медленных прогрессивных планет `exact_utc = null` для аспектов, которые фактически натальные; местное время соляра на месте рождения зависит от timezonefinder и tzdb (для СССР до 1970 г. — см. модуль 00). Бюджет: WebSearch 0, WebFetch 3 (astro.com FAQ, Wikipedia, транскрипт подкаста), curl: astro.com FAQ (7), AstroWiki raw (6), TMA (2), GitHub Astrolog (4 файла). web.archive.org не использовался.

### Повторная проверка (приоритет 1)

**15.10.2026, агент повторного исследования.** Цель — открытые пункты, меняющие числа. Источники: astro.com FAQ через `/cgi/xa.cgi/` (curl, generic User-Agent), полнотекстовый поиск и тексты archive.org, исходники Astrolog 8 (GitHub raw). web.archive.org недоступен, astro-seek — 403, руководство Solar Fire не найдено.

| # | Пункт | Итог | Основание |
|---|---|---|---|
| 1 | Орбисы Лиз Грин для транзитов | **не решаемо**, ⚠ оставлен с причиной | astro.com FAQ «Forecast Horoscopes»: «It would be too complex to list all the orbs individually»; «We do not publish the logic behind our calculations»; других публикаций нет |
| 2 | Орбис 1° Хэнда | **подтверждено** дополнительно | Hand, «Planets in Transit», Transit Rule 2 и отчёт «enters one degree of orb» |
| 3 | Умолчание Solar Fire для прогрессивных углов (MC + дуга) | **не решаемо**, ⚠ оставлен | руководство Solar Fire не найдено (archive.org — только дистрибутивы программы, их не открывали); подтверждено лишь, что такие способы в Solar Fire есть |
| 4 | `naibod` (Наибод в долготе) | **подтверждено**, ⚠ снят | Astracadabra v1 (Esoteric Technologies): «Naibod in Longitude»; Astrolog32 Wish List о Solar Fire; Riske 2011 |
| 5 | `solar_arc_ra` | **подтверждено**, ⚠ снят | Astracadabra v1: «Solar Arc in Right Ascension (S.A. in R.A.)»; Astrolog32 Wish List |
| 6 | `quotidian` | **подтверждено** дополнительно | Astrolog 8 `calc.cpp`: куспиды `-p` на момент `is.Tp` = прогрессивный момент (`-pC` = 1,0) — это умолчание Astrolog |
| 7 | ε для прогрессивных углов | **частично**: опция `progression_obliquity` (`natal` — как Astrolog `-p1 -pc`); умолчание не менялось; ⚠ для astro.com остаётся (влияние ≤ 4″) | Astrolog 8 `calc.cpp` (`SwissHouse(is.Tp…)`, `EclToEqu` с ε рождения) |
| 8 | Месячные профекции | **реализованы 3 источниковых варианта** (`calendar`, `thirteen`, `valens`); умолчание `equal` не менялось, ⚠ «условность» оставлен (прямого источника нет) | D. George 2008; AstroWiki/Knappich; Ptolemy IV.10 (Ashmand); R. Hand (Project Hindsight IX); Valens IV.28 (Riley). Ранее упомянутые «28-дневные» месяцы = Птолемей; «календарные» = George |
| 9 | Окно поиска точной даты прогрессий/дирекций (±3 г.) | **опция** `exact_window_years` (до 120 лет); умолчание 3 | — (технический параметр); T2: прогр. ♄ △ ☽ найдено на 25.10.2005 |
| 10 | Конверсные вторичные прогрессии | **реализованы** опцией `progression_direction="converse"` | astro.com FAQ «Other methods»: «use negative age» |
| 11 | Первичные дирекции | **реализованы только к углам** (`primary_directions=True`; ключи Наибода, Птолемея, Симмонайта, Плацидуса; in mundo / in zodiaco); дирекции к планетам и мунданные аспекты — ⚠ не реализованы | Makransky, гл. I–III; сверка со спекулумом принца Чарльза: 7 дуг Δ ≤ 0,015°, 8 сроков Δ ≤ 0,02 г. |
| 12 | Сверка с готовыми картами astro.com / astro-seek | **не решаемо**, ⚠ оставлен | astro-seek 403; карты astro.com — только в сессии пользователя |

Итого: 12 пунктов — подтверждено 4 (из них 2 ⚠ сняты), реализовано опциями 5 (умолчания не менялись), не решаемо 3 (⚠ с причиной). Опровергнутых нет.

**Код** (`calculators/forecast_western.py`, умолчания и числа по умолчанию не изменились — сравнение JSON старой и новой версии на T1–T4 и T1 без времени: совпадение, кроме нового текста `method_ru`/`variant` месяца и шага 7): опции `profection_month`, `progression_direction`, `progression_obliquity`, `exact_window_years`, `primary_directions` (+ `pd_key`, `pd_latitude`, `pd_max_age`); функция `primary_directions_to_angles`; новые поля JSON (`progressions.direction`, `exact_search_window_years`, `angles.obliquity`/`obliquity_source`, `profections.month.method`/`months_in_year`, `primary_directions`).

**Тесты:** +21 (`test_primary_directions_makransky_arcs` ×7, `…_speculum_and_keys`, `…_invariants`, `test_converse_progressions_t1`, `test_converse_angles_mirror` ×5, `test_profection_month_variants_t1`, `test_profection_calendar_months_george`, `test_profection_month_valens_night_and_feb29`, `test_exact_window_years_option`, `test_progression_obliquity_option`, `test_new_option_errors`). `.venv/bin/python -m pytest calculators/tests/test_forecast_western.py calculators/tests/test_western.py -q` — 237 тестов, все зелёные.

### Повторная проверка (приоритет 2)

**15.10.2026, тот же агент.** Ключи интерпретации и атрибуции перечитаны по источникам (AstroWiki raw: Transit, Secondary_Progression, Solar_Arc, Direction, Lunation_Cycle, Solar_Return_Chart, Lunar_Return_Chart; astro.com FAQ «Transits»; Boele; Brennan 2017; Wikipedia).

- §8.1 (AstroWiki «Transit»): 12 строк — все подтверждены; добавлены строка о Меркурии/Венере/Марсе в петле («more significant») и абзац о фоне и «спусковых крючках» (раздел «Trigger»); цитаты «life-changing events or processes» (AstroWiki) и «opportunities, health, moods…» (astro.com FAQ «Transits») — атрибуция верна.
- §8.2 (AstroWiki «Secondary Progression», «Solar Arc»): 6 строк подтверждены; добавлены 4 строки (взаимные аспекты прогрессий, приоритет личных планет, дирекции дуги, отсутствие ключей у конверсных и первичных дирекций — Makransky: «no interpretations are given»).
- §8.3: **исправлена атрибуция** — AstroWiki «Lunation Cycle» описывает фазы **натальной** Луны (типы личности по Радьяру), а не прогрессивные; ключи таблицы теперь только по Boele. Исправлены 3 строки, не совпадавшие с Boele: Растущий серп («рост в защищённой среде, эксперименты»), Выпуклая («анализ и совершенствование» — у Boele нет), Бальзамическая («пожинать посеянное» — у Boele образ «ripe and rotten fruit which releases the seed»); остальные 5 переформулированы с цитатами.
- §8.4 (AstroWiki «Solar/Lunar Return Chart»): 7 строк подтверждены; добавлена пропущенная строка «управитель ASC соляра», расширена строка лунара (дом с Луной, приоритет ☌ и ☍), добавлено «more concerned with current events».
- §8.5 (Brennan): 5 строк подтверждены по книге 2017 г. (гл. 17); строка о транзитах дополнена третьим пунктом Brennan/Гефестиона («Transits through the profected sign»); добавлены строки о состоянии управителя года и о месяце, когда месячная профекция приходит в знак управителя года (Цоллер у Brennan; D. George).
- §7.1: факты о 30.06.1905 и Берне подтверждены (Wikipedia «Annus mirabilis papers»: «received on 30 June»; «Albert Einstein», «Einsteinhaus»), ⚠ сняты.

Итого: проверено 40 утверждений (38 строк §8 + 2 факта §7.1), подтверждено 37, исправлено 3 строки и 1 атрибуция, добавлено 8 строк и 1 абзац; ничего не выдумано (каждая добавка — с цитатой).

**Бюджет.** WebSearch: 2. WebFetch: 0. curl: astro.com FAQ (5), AstroWiki raw (8), Boele (1), archive.org (метаданные, полнотекстовый поиск ~35 запросов, 9 текстов + архив Considerations 78 файлов), GitHub raw Astrolog (8 файлов), Wikipedia raw (4). web.archive.org не использовался.
