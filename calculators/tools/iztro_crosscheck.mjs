// Сверка calculators/ziwei.py с независимой реализацией iztro (npm, MIT, https://github.com/SylarLong/iztro).
//
// iztro НЕ является зависимостью проекта. Скрипт нужен только для того, чтобы
// пересчитать эталонные значения, «замороженные» в calculators/tests/test_ziwei.py.
//
// Установка (в любой временный каталог):
//   mkdir /tmp/iztro && cd /tmp/iztro && npm i iztro@2.6.2
// Запуск:
//   IZTRO_DIR=/tmp/iztro node calculators/tools/iztro_crosscheck.mjs            # встроенные кейсы
//   IZTRO_DIR=/tmp/iztro node calculators/tools/iztro_crosscheck.mjs cases.json # свои кейсы
//
// Формат кейса: {"id": "T1", "date": "1990-5-15", "timeIndex": 7, "gender": "female",
//                "fixLeap": true, "config": {"yearDivide": "normal", "dayDivide": "forward"}}
// timeIndex: 0 = ранний Цзы 00:00–01:00, 1 = Чоу 01–03, …, 11 = Хай 21–23, 12 = поздний Цзы 23–24.
// Дата — григорианская дата по МЕСТНОМУ времени (iztro не знает часовых поясов).
//
// Вывод: JSON-массив с компактным описанием карты (названия — на китайском, zh-CN).

import { createRequire } from 'node:module';
import { readFileSync } from 'node:fs';
import path from 'node:path';

const dir = process.env.IZTRO_DIR || process.cwd();
const require = createRequire(path.join(dir, 'package.json'));
const iztro = require('iztro');
const iztroVersion = require('iztro/package.json').version;

const DEFAULT_CASES = [
  // T1: 15.05.1990 14:30 MSD (UTC+4) — час Вэй (13–15), женщина
  { id: 'T1', date: '1990-5-15', timeIndex: 7, gender: 'female' },
  // T2: 04.02.1984 23:30 MSK — поздний Цзы (23–24), мужчина
  { id: 'T2', date: '1984-2-4', timeIndex: 12, gender: 'male' },
  // T2 при «истинном солнечном времени» (22:46) — час Хай
  { id: 'T2_tst', date: '1984-2-4', timeIndex: 11, gender: 'male' },
  // T2, вариант «поздний Цзы = текущий день»
  { id: 'T2_zi_current', date: '1984-2-4', timeIndex: 12, gender: 'male', config: { dayDivide: 'current' } },
  // T3: 29.02.2004 08:15 — час Чэнь (07–09), женщина
  { id: 'T3', date: '2004-2-29', timeIndex: 4, gender: 'female' },
  // T4: Эйнштейн 14.03.1879 11:30 LMT — час У (11–13), мужчина
  { id: 'T4', date: '1879-3-14', timeIndex: 6, gender: 'male' },
  // X1: рождение в високосном месяце (闰二月 2004 г.), день > 15: 2004-04-10 = 闰二月廿一
  { id: 'X1_leap', date: '2004-4-10', timeIndex: 2, gender: 'male' },
  { id: 'X1_leap_nofix', date: '2004-4-10', timeIndex: 2, gender: 'male', fixLeap: false },
  // X2: високосный месяц, день ≤ 15: 2020-05-23 = 闰四月初一
  { id: 'X2_leap', date: '2020-5-23', timeIndex: 9, gender: 'female' },
  // X3: граница года: между Личунем (04.02.2021) и Новым годом (12.02.2021)
  { id: 'X3_lichun', date: '2021-2-8', timeIndex: 3, gender: 'male' },
  { id: 'X3_lichun_exact', date: '2021-2-8', timeIndex: 3, gender: 'male', config: { yearDivide: 'exact' } },
  // X4: опубликованный пример iztro (README): 2000-08-16, timeIndex 2, женщина
  { id: 'X4_iztro_readme', date: '2000-8-16', timeIndex: 2, gender: 'female' },
  // X5: 1980-01-01 Цзы-час — проверка разных бюро
  { id: 'X5', date: '1980-1-1', timeIndex: 0, gender: 'male' },
  // X6: 1993-07-24 18:00 (Ю), женщина
  { id: 'X6', date: '1993-7-24', timeIndex: 9, gender: 'female' },
  // MAO: Мао Цзэдун, 26.12.1893 (光绪十九年十一月十九) час Чэнь, мужчина — опубликованная карта
  // https://wfate.blogspot.com/2013/06/blog-post_15.html , https://ziwei.yi958.com/2020/08/22/zi-wei-ming-pan-mao-ze-dong-zhu-xi-de-zi-wei-dou-shu-ming/
  { id: 'MAO', date: '1893-12-26', timeIndex: 4, gender: 'male' },
  // X7: поздний Цзы в последний день лунного месяца — здесь iztro и ziwei.py РАСХОДЯТСЯ (см. базу знаний)
  { id: 'X7_latezi_month_end', date: '2006-11-20', timeIndex: 12, gender: 'male' },
  // X8: поздний Цзы 15-го дня високосного месяца (2004-04-04 = 闰二月十五) — тоже РАСХОДЯТСЯ:
  // iztro при timeIndex=12 не применяет правило 闰月 (fixLunarMonthIndex), ziwei.py берёт 闰二月十六 -> месяц 3
  { id: 'X8_latezi_leap15', date: '2004-4-4', timeIndex: 12, gender: 'male' },
];

function summarize(c) {
  const conf = { yearDivide: 'normal', horoscopeDivide: 'normal', dayDivide: 'forward', ...(c.config || {}) };
  const a = iztro.astro.withOptions({
    type: 'solar',
    dateStr: c.date,
    timeIndex: c.timeIndex,
    gender: c.gender === 'male' ? '男' : '女',
    fixLeap: c.fixLeap ?? true,
    language: 'zh-CN',
    config: conf,
  });
  const palaces = a.palaces.map((p) => ({
    name: p.name,
    stem: p.heavenlyStem,
    branch: p.earthlyBranch,
    body: p.isBodyPalace,
    major: p.majorStars.map((s) => [s.name, s.brightness || '', s.mutagen || '']),
    minor: p.minorStars.map((s) => [s.name, s.brightness || '', s.mutagen || '']),
    decadal: p.decadal.range,
    ages: p.ages,
  }));
  return {
    id: c.id,
    input: { ...c, config: conf },
    iztroVersion,
    lunarDate: a.lunarDate,
    chineseDate: a.chineseDate,
    time: a.time,
    soulBranch: a.earthlyBranchOfSoulPalace,
    bodyBranch: a.earthlyBranchOfBodyPalace,
    soul: a.soul,
    body: a.body,
    fiveElementsClass: a.fiveElementsClass,
    palaces,
  };
}

const cases = process.argv[2] ? JSON.parse(readFileSync(process.argv[2], 'utf8')) : DEFAULT_CASES;
console.log(JSON.stringify(cases.map(summarize), null, 1));
