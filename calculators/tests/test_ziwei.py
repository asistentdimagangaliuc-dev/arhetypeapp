"""Тесты calculators/ziwei.py (Цзы Вэй Доу Шу).

Источники эталонов:
* iztro 2.6.2 (npm, MIT, https://github.com/SylarLong/iztro) — независимая реализация на TypeScript.
  Значения ниже «заморожены» из вывода calculators/tools/iztro_crosscheck.mjs (iztro 2.6.2,
  lunar-lite 0.2.8, конфигурация по умолчанию: yearDivide=normal, dayDivide=forward, fixLeap=true,
  язык zh-CN). Пересчёт: IZTRO_DIR=<каталог с npm i iztro@2.6.2> node calculators/tools/iztro_crosscheck.mjs
  Дополнительно (вне тестов) прогнано 3210 случайных карт 1900–2099: совпадение 3197/3210; все 13
  расхождений — поздний Цзы в последний день лунного месяца или в високосном месяце после 15-го
  (особенность iztro, см. test_late_zi_month_end_differs_from_iztro и базу знаний).
* Опубликованные правила/примеры: https://www.ncc.com.tw/fate/paleo/gv/gv_15.htm ,
  https://zh.wikipedia.org/wiki/紫微斗數 , https://iztro.com/learn/setup
* Опубликованная карта Мао Цзэдуна: https://wfate.blogspot.com/2013/06/blog-post_15.html (данные 胡玄微),
  https://ziwei.yi958.com/2020/08/22/zi-wei-ming-pan-mao-ze-dong-zhu-xi-de-zi-wei-dou-shu-ming/
"""
from __future__ import annotations

import pytest

from calculators.common.time import BirthInput
from calculators.ziwei import (
    BRANCHES, PALACES, STEMS, body_branch, bureau_number, bureau_number_mnemonic, calculate,
    hour_branch_index, ming_branch, nayin, palace_stem, sihua_for_stem, tianfu_branch, ziwei_branch,
    aux_star_positions, yin_stem,
)

B = BRANCHES.index


def _stars(lst: list[dict]) -> str:
    return ",".join(sorted(s["star"] + s["brightness"] + s["sihua"] for s in lst)) or "-"


def signature(r: dict) -> dict:
    """Компактная подпись карты в формате снимков iztro."""
    pal = {}
    for p in r["palaces"]:
        d = p["decade_ages"]
        pal[p["branch"]] = (f"{p['name']} {p['stem_branch']} M:{_stars(p['major_stars'])} "
                            f"A:{_stars(p['aux_stars'])} D:{d[0]}-{d[1]}")
    return {"ming": r["ming_palace"]["branch"], "body": r["body_palace"]["branch"], "bureau": r["bureau"]["name"],
            "ming_zhu": r["ming_zhu"], "shen_zhu": r["shen_zhu"], "palaces": pal}


IZTRO = {
    # T1: 1990-5-15 timeIndex=7 female fixLeap=True config={'yearDivide': 'normal', 'dayDivide': 'forward'} -> 一九九〇年四月廿一 庚午 辛巳 庚辰 癸未
    'T1': {
        'ming': '戌', 'body': '子', 'bureau': '土五局', 'ming_zhu': '禄存', 'shen_zhu': '火星',
        'palaces': {
            '子': '福德 戊子 M:七杀旺 A:- D:105-114',
            '丑': '田宅 己丑 M:- A:天魁 D:95-104',
            '寅': '官禄 戊寅 M:廉贞庙 A:- D:85-94',
            '卯': '仆役 己卯 M:- A:文昌利 D:75-84',
            '辰': '迁移 庚辰 M:破军旺 A:地空 D:65-74',
            '巳': '疾厄 辛巳 M:天同庙忌 A:- D:55-64',
            '午': '财帛 壬午 M:天府旺,武曲旺权 A:地劫 D:45-54',
            '未': '子女 癸未 M:太阳得禄,太阴不科 A:右弼,天钺,左辅,陀罗庙 D:35-44',
            '申': '夫妻 甲申 M:贪狼平 A:天马,火星陷,禄存 D:25-34',
            '酉': '兄弟 乙酉 M:天机旺,巨门庙 A:擎羊陷 D:15-24',
            '戌': '命宫 丙戌 M:天相得,紫微得 A:铃星庙 D:5-14',
            '亥': '父母 丁亥 M:天梁陷 A:文曲旺 D:115-124',
        },
    },
    # T2: 1984-2-4 timeIndex=12 male fixLeap=True config={'yearDivide': 'normal', 'dayDivide': 'forward'} -> 一九八四年正月初三 甲子 丙寅 己巳 甲子
    'T2': {
        'ming': '寅', 'body': '寅', 'bureau': '火六局', 'ming_zhu': '禄存', 'shen_zhu': '火星',
        'palaces': {
            '子': '夫妻 丙子 M:天府庙,武曲旺科 A:- D:106-115',
            '丑': '兄弟 丁丑 M:太阳不忌,太阴庙 A:天魁,陀罗庙 D:116-125',
            '寅': '命宫 丙寅 M:贪狼平 A:天马,火星庙,禄存 D:6-15',
            '卯': '父母 丁卯 M:天机旺,巨门庙 A:擎羊陷 D:16-25',
            '辰': '福德 戊辰 M:天相得,紫微得 A:左辅,文曲得 D:26-35',
            '巳': '田宅 己巳 M:天梁陷 A:- D:36-45',
            '午': '官禄 庚午 M:七杀旺 A:- D:46-55',
            '未': '仆役 辛未 M:- A:天钺 D:56-65',
            '申': '迁移 壬申 M:廉贞庙禄 A:- D:66-75',
            '酉': '疾厄 癸酉 M:- A:- D:76-85',
            '戌': '财帛 甲戌 M:破军旺权 A:右弼,文昌陷,铃星庙 D:86-95',
            '亥': '子女 乙亥 M:天同庙 A:地劫,地空 D:96-105',
        },
    },
    # T2_tst: 1984-2-4 timeIndex=11 male fixLeap=True config={'yearDivide': 'normal', 'dayDivide': 'forward'} -> 一九八四年正月初三 甲子 丙寅 戊辰 癸亥
    'T2_tst': {
        'ming': '卯', 'body': '丑', 'bureau': '火六局', 'ming_zhu': '文曲', 'shen_zhu': '火星',
        'palaces': {
            '子': '子女 丙子 M:- A:地空 D:96-105',
            '丑': '夫妻 丁丑 M:- A:天魁,火星得,陀罗庙 D:106-115',
            '寅': '兄弟 丙寅 M:- A:天马,禄存 D:116-125',
            '卯': '命宫 丁卯 M:廉贞平禄,破军陷权 A:擎羊陷,文曲旺 D:6-15',
            '辰': '父母 戊辰 M:- A:左辅 D:16-25',
            '巳': '福德 己巳 M:天府得 A:- D:26-35',
            '午': '田宅 庚午 M:天同陷,太阴不 A:- D:36-45',
            '未': '官禄 辛未 M:武曲庙科,贪狼庙 A:天钺 D:46-55',
            '申': '仆役 壬申 M:太阳得忌,巨门庙 A:- D:56-65',
            '酉': '迁移 癸酉 M:天相陷 A:铃星得 D:66-75',
            '戌': '疾厄 甲戌 M:天机利,天梁庙 A:右弼,地劫 D:76-85',
            '亥': '财帛 乙亥 M:七杀平,紫微旺 A:文昌利 D:86-95',
        },
    },
    # T2_zi_current: 1984-2-4 timeIndex=12 male fixLeap=True config={'yearDivide': 'normal', 'dayDivide': 'current'} -> 一九八四年正月初三 甲子 丙寅 戊辰 壬子
    'T2_zi_current': {
        'ming': '寅', 'body': '寅', 'bureau': '火六局', 'ming_zhu': '禄存', 'shen_zhu': '火星',
        'palaces': {
            '子': '夫妻 丙子 M:- A:- D:106-115',
            '丑': '兄弟 丁丑 M:- A:天魁,陀罗庙 D:116-125',
            '寅': '命宫 丙寅 M:- A:天马,火星庙,禄存 D:6-15',
            '卯': '父母 丁卯 M:廉贞平禄,破军陷权 A:擎羊陷 D:16-25',
            '辰': '福德 戊辰 M:- A:左辅,文曲得 D:26-35',
            '巳': '田宅 己巳 M:天府得 A:- D:36-45',
            '午': '官禄 庚午 M:天同陷,太阴不 A:- D:46-55',
            '未': '仆役 辛未 M:武曲庙科,贪狼庙 A:天钺 D:56-65',
            '申': '迁移 壬申 M:太阳得忌,巨门庙 A:- D:66-75',
            '酉': '疾厄 癸酉 M:天相陷 A:- D:76-85',
            '戌': '财帛 甲戌 M:天机利,天梁庙 A:右弼,文昌陷,铃星庙 D:86-95',
            '亥': '子女 乙亥 M:七杀平,紫微旺 A:地劫,地空 D:96-105',
        },
    },
    # T3: 2004-2-29 timeIndex=4 female fixLeap=True config={'yearDivide': 'normal', 'dayDivide': 'forward'} -> 二〇〇四年二月初十 甲申 丁卯 戊寅 丙辰
    'T3': {
        'ming': '亥', 'body': '未', 'bureau': '火六局', 'ming_zhu': '巨门', 'shen_zhu': '天梁',
        'palaces': {
            '子': '父母 丙子 M:天同旺,太阴庙 A:- D:116-125',
            '丑': '福德 丁丑 M:武曲庙科,贪狼庙 A:天魁,陀罗庙 D:106-115',
            '寅': '田宅 丙寅 M:太阳旺忌,巨门庙 A:天马,禄存,铃星庙 D:96-105',
            '卯': '官禄 丁卯 M:天相陷 A:地劫,擎羊陷 D:86-95',
            '辰': '仆役 戊辰 M:天机利,天梁庙 A:- D:76-85',
            '巳': '迁移 己巳 M:七杀平,紫微旺 A:左辅 D:66-75',
            '午': '疾厄 庚午 M:- A:文昌陷,火星庙 D:56-65',
            '未': '财帛 辛未 M:- A:地空,天钺 D:46-55',
            '申': '子女 壬申 M:- A:文曲得 D:36-45',
            '酉': '夫妻 癸酉 M:廉贞平禄,破军陷权 A:右弼 D:26-35',
            '戌': '兄弟 甲戌 M:- A:- D:16-25',
            '亥': '命宫 乙亥 M:天府得 A:- D:6-15',
        },
    },
    # T4: 1879-3-14 timeIndex=6 male fixLeap=True config={'yearDivide': 'normal', 'dayDivide': 'forward'} -> 一八七九年二月廿二 己卯 丁卯 丙申 甲午
    'T4': {
        'ming': '酉', 'body': '酉', 'bureau': '金四局', 'ming_zhu': '文曲', 'shen_zhu': '天同',
        'palaces': {
            '子': '田宅 丙子 M:天梁庙科 A:天魁 D:94-103',
            '丑': '官禄 丁丑 M:七杀庙,廉贞利 A:- D:84-93',
            '寅': '仆役 丙寅 M:- A:- D:74-83',
            '卯': '迁移 丁卯 M:- A:火星利 D:64-73',
            '辰': '疾厄 戊辰 M:天同平 A:文昌得,铃星陷 D:54-63',
            '巳': '财帛 己巳 M:武曲平禄,破军平 A:地劫,地空,天马,左辅,陀罗陷 D:44-53',
            '午': '子女 庚午 M:太阳旺 A:禄存 D:34-43',
            '未': '夫妻 辛未 M:天府庙 A:擎羊庙 D:24-33',
            '申': '兄弟 壬申 M:天机得,太阴利 A:天钺 D:14-23',
            '酉': '命宫 癸酉 M:紫微旺,贪狼利权 A:右弼 D:4-13',
            '戌': '父母 甲戌 M:巨门陷 A:文曲陷忌 D:114-123',
            '亥': '福德 乙亥 M:天相得 A:- D:104-113',
        },
    },
    # X1_leap: 2004-4-10 timeIndex=2 male fixLeap=True config={'yearDivide': 'normal', 'dayDivide': 'forward'} -> 二〇〇四年闰二月廿一 甲申 戊辰 己未 丙寅
    'X1_leap': {
        'ming': '寅', 'body': '午', 'bureau': '火六局', 'ming_zhu': '禄存', 'shen_zhu': '天梁',
        'palaces': {
            '子': '夫妻 丙子 M:破军庙权 A:铃星陷 D:106-115',
            '丑': '兄弟 丁丑 M:天机陷 A:地劫,天魁,陀罗庙 D:116-125',
            '寅': '命宫 丙寅 M:天府庙,紫微旺 A:天马,禄存 D:6-15',
            '卯': '父母 丁卯 M:太阴陷 A:擎羊陷 D:16-25',
            '辰': '福德 戊辰 M:贪狼庙 A:火星陷 D:26-35',
            '巳': '田宅 己巳 M:巨门旺 A:- D:36-45',
            '午': '官禄 庚午 M:天相庙,廉贞平禄 A:左辅,文曲陷 D:46-55',
            '未': '仆役 辛未 M:天梁旺 A:天钺 D:56-65',
            '申': '迁移 壬申 M:七杀庙 A:右弼,文昌得 D:66-75',
            '酉': '疾厄 癸酉 M:天同平 A:地空 D:76-85',
            '戌': '财帛 甲戌 M:武曲庙科 A:- D:86-95',
            '亥': '子女 乙亥 M:太阳陷忌 A:- D:96-105',
        },
    },
    # X1_leap_nofix: 2004-4-10 timeIndex=2 male fixLeap=False config={'yearDivide': 'normal', 'dayDivide': 'forward'} -> 二〇〇四年闰二月廿一 甲申 戊辰 己未 丙寅
    'X1_leap_nofix': {
        'ming': '丑', 'body': '巳', 'bureau': '水二局', 'ming_zhu': '巨门', 'shen_zhu': '天梁',
        'palaces': {
            '子': '兄弟 丙子 M:- A:铃星陷 D:112-121',
            '丑': '命宫 丁丑 M:- A:地劫,天魁,陀罗庙 D:2-11',
            '寅': '父母 丙寅 M:- A:天马,禄存 D:12-21',
            '卯': '福德 丁卯 M:廉贞平禄,破军陷权 A:擎羊陷 D:22-31',
            '辰': '田宅 戊辰 M:- A:火星陷 D:32-41',
            '巳': '官禄 己巳 M:天府得 A:左辅 D:42-51',
            '午': '仆役 庚午 M:天同陷,太阴不 A:文曲陷 D:52-61',
            '未': '迁移 辛未 M:武曲庙科,贪狼庙 A:天钺 D:62-71',
            '申': '疾厄 壬申 M:太阳得忌,巨门庙 A:文昌得 D:72-81',
            '酉': '财帛 癸酉 M:天相陷 A:右弼,地空 D:82-91',
            '戌': '子女 甲戌 M:天机利,天梁庙 A:- D:92-101',
            '亥': '夫妻 乙亥 M:七杀平,紫微旺 A:- D:102-111',
        },
    },
    # X2_leap: 2020-5-23 timeIndex=9 female fixLeap=True config={'yearDivide': 'normal', 'dayDivide': 'forward'} -> 二〇二〇年闰四月初一 庚子 辛巳 丙寅 丁酉
    'X2_leap': {
        'ming': '申', 'body': '寅', 'bureau': '水二局', 'ming_zhu': '廉贞', 'shen_zhu': '火星',
        'palaces': {
            '子': '官禄 戊子 M:天机庙 A:- D:82-91',
            '丑': '仆役 己丑 M:破军旺,紫微庙 A:天魁,文昌庙,文曲庙 D:72-81',
            '寅': '迁移 戊寅 M:- A:地空,天马 D:62-71',
            '卯': '疾厄 己卯 M:天府得 A:- D:52-61',
            '辰': '财帛 庚辰 M:太阴陷科 A:- D:42-51',
            '巳': '子女 辛巳 M:廉贞陷,贪狼陷 A:- D:32-41',
            '午': '夫妻 壬午 M:巨门旺 A:- D:22-31',
            '未': '兄弟 癸未 M:天相得 A:右弼,天钺,左辅,铃星利,陀罗庙 D:12-21',
            '申': '命宫 甲申 M:天同旺忌,天梁陷 A:地劫,禄存 D:2-11',
            '酉': '父母 乙酉 M:七杀旺,武曲利权 A:擎羊陷 D:112-121',
            '戌': '福德 丙戌 M:太阳不禄 A:- D:102-111',
            '亥': '田宅 丁亥 M:- A:火星利 D:92-101',
        },
    },
    # X3_lichun: 2021-2-8 timeIndex=3 male fixLeap=True config={'yearDivide': 'normal', 'dayDivide': 'forward'} -> 二〇二〇年腊月廿七 庚子 己丑 丁亥 癸卯
    'X3_lichun': {
        'ming': '戌', 'body': '辰', 'bureau': '土五局', 'ming_zhu': '禄存', 'shen_zhu': '火星',
        'palaces': {
            '子': '福德 戊子 M:天府庙,武曲旺权 A:- D:25-34',
            '丑': '田宅 己丑 M:太阳不禄,太阴庙科 A:天魁,铃星得 D:35-44',
            '寅': '官禄 戊寅 M:贪狼平 A:地劫,天马 D:45-54',
            '卯': '仆役 己卯 M:天机旺,巨门庙 A:左辅 D:55-64',
            '辰': '迁移 庚辰 M:天相得,紫微得 A:- D:65-74',
            '巳': '疾厄 辛巳 M:天梁陷 A:火星得 D:75-84',
            '午': '财帛 壬午 M:七杀旺 A:- D:85-94',
            '未': '子女 癸未 M:- A:天钺,文昌利,文曲旺,陀罗庙 D:95-104',
            '申': '夫妻 甲申 M:廉贞庙 A:地空,禄存 D:105-114',
            '酉': '兄弟 乙酉 M:- A:擎羊陷 D:115-124',
            '戌': '命宫 丙戌 M:破军旺 A:- D:5-14',
            '亥': '父母 丁亥 M:天同庙忌 A:右弼 D:15-24',
        },
    },
    # X3_lichun_exact: 2021-2-8 timeIndex=3 male fixLeap=True config={'yearDivide': 'exact', 'dayDivide': 'forward'} -> 二〇二〇年腊月廿七 辛丑 辛丑 丁亥 癸卯
    'X3_lichun_exact': {
        'ming': '戌', 'body': '辰', 'bureau': '木三局', 'ming_zhu': '禄存', 'shen_zhu': '天相',
        'palaces': {
            '子': '福德 庚子 M:七杀旺 A:- D:103-112',
            '丑': '田宅 辛丑 M:- A:铃星得 D:93-102',
            '寅': '官禄 庚寅 M:廉贞庙 A:地劫,天钺 D:83-92',
            '卯': '仆役 辛卯 M:- A:左辅 D:73-82',
            '辰': '迁移 壬辰 M:破军旺 A:- D:63-72',
            '巳': '疾厄 癸巳 M:天同庙 A:- D:53-62',
            '午': '财帛 甲午 M:天府旺,武曲旺 A:天魁,火星庙 D:43-52',
            '未': '子女 乙未 M:太阳得权,太阴不 A:文昌利忌,文曲旺科 D:33-42',
            '申': '夫妻 丙申 M:贪狼平 A:地空,陀罗陷 D:23-32',
            '酉': '兄弟 丁酉 M:天机旺,巨门庙禄 A:禄存 D:13-22',
            '戌': '命宫 戊戌 M:天相得,紫微得 A:擎羊庙 D:3-12',
            '亥': '父母 己亥 M:天梁陷 A:右弼,天马 D:113-122',
        },
    },
    # X4_iztro_readme: 2000-8-16 timeIndex=2 female fixLeap=True config={'yearDivide': 'normal', 'dayDivide': 'forward'} -> 二〇〇〇年七月十七 庚辰 甲申 丙午 庚寅
    'X4_iztro_readme': {
        'ming': '午', 'body': '戌', 'bureau': '木三局', 'ming_zhu': '破军', 'shen_zhu': '文昌',
        'palaces': {
            '子': '迁移 戊子 M:贪狼旺 A:铃星陷 D:63-72',
            '丑': '疾厄 己丑 M:天同不忌,巨门不 A:地劫,天魁 D:53-62',
            '寅': '财帛 戊寅 M:天相庙,武曲得权 A:天马 D:43-52',
            '卯': '子女 己卯 M:天梁庙,太阳庙禄 A:- D:33-42',
            '辰': '夫妻 庚辰 M:七杀庙 A:右弼,火星陷 D:23-32',
            '巳': '兄弟 辛巳 M:天机平 A:- D:13-22',
            '午': '命宫 壬午 M:紫微庙 A:文曲陷 D:3-12',
            '未': '父母 癸未 M:- A:天钺,陀罗庙 D:113-122',
            '申': '福德 甲申 M:破军得 A:文昌得,禄存 D:103-112',
            '酉': '田宅 乙酉 M:- A:地空,擎羊陷 D:93-102',
            '戌': '官禄 丙戌 M:天府庙,廉贞利 A:左辅 D:83-92',
            '亥': '仆役 丁亥 M:太阴庙科 A:- D:73-82',
        },
    },
    # X5: 1980-1-1 timeIndex=0 male fixLeap=True config={'yearDivide': 'normal', 'dayDivide': 'forward'} -> 一九七九年冬月十四 己未 丙子 癸酉 壬子
    'X5': {
        'ming': '子', 'body': '子', 'bureau': '水二局', 'ming_zhu': '贪狼', 'shen_zhu': '天相',
        'palaces': {
            '子': '命宫 丙子 M:天相庙,廉贞平 A:右弼,天魁 D:2-11',
            '丑': '父母 丁丑 M:天梁旺科 A:- D:112-121',
            '寅': '福德 丙寅 M:七杀庙 A:左辅 D:102-111',
            '卯': '田宅 丁卯 M:天同平 A:- D:92-101',
            '辰': '官禄 戊辰 M:武曲庙禄 A:文曲得忌 D:82-91',
            '巳': '仆役 己巳 M:太阳旺 A:天马,陀罗陷 D:72-81',
            '午': '迁移 庚午 M:破军庙 A:禄存 D:62-71',
            '未': '疾厄 辛未 M:天机陷 A:擎羊庙 D:52-61',
            '申': '财帛 壬申 M:天府得,紫微旺 A:天钺 D:42-51',
            '酉': '子女 癸酉 M:太阴旺 A:火星得 D:32-41',
            '戌': '夫妻 甲戌 M:贪狼庙权 A:文昌陷,铃星庙 D:22-31',
            '亥': '兄弟 乙亥 M:巨门旺 A:地劫,地空 D:12-21',
        },
    },
    # X6: 1993-7-24 timeIndex=9 female fixLeap=True config={'yearDivide': 'normal', 'dayDivide': 'forward'} -> 一九九三年六月初六 癸酉 己未 丙午 丁酉
    'X6': {
        'ming': '戌', 'body': '辰', 'bureau': '水二局', 'ming_zhu': '禄存', 'shen_zhu': '天同',
        'palaces': {
            '子': '福德 甲子 M:天府庙,武曲旺 A:火星陷,禄存 D:22-31',
            '丑': '田宅 乙丑 M:太阳不,太阴庙科 A:擎羊庙,文昌庙,文曲庙 D:32-41',
            '寅': '官禄 甲寅 M:贪狼平忌 A:地空 D:42-51',
            '卯': '仆役 乙卯 M:天机旺,巨门庙权 A:天魁 D:52-61',
            '辰': '迁移 丙辰 M:天相得,紫微得 A:- D:62-71',
            '巳': '疾厄 丁巳 M:天梁陷 A:右弼,天钺 D:72-81',
            '午': '财帛 戊午 M:七杀旺 A:- D:82-91',
            '未': '子女 己未 M:- A:铃星利 D:92-101',
            '申': '夫妻 庚申 M:廉贞庙 A:地劫 D:102-111',
            '酉': '兄弟 辛酉 M:- A:左辅 D:112-121',
            '戌': '命宫 壬戌 M:破军旺禄 A:- D:2-11',
            '亥': '父母 癸亥 M:天同庙 A:天马,陀罗陷 D:12-21',
        },
    },
    # MAO: 1893-12-26 timeIndex=4 male fixLeap=True config={'yearDivide': 'normal', 'dayDivide': 'forward'} -> 一八九三年冬月十九 癸巳 甲子 丁酉 甲辰
    'MAO': {
        'ming': '申', 'body': '辰', 'bureau': '木三局', 'ming_zhu': '廉贞', 'shen_zhu': '天机',
        'palaces': {
            '子': '官禄 甲子 M:七杀旺 A:右弼,禄存 D:83-92',
            '丑': '仆役 乙丑 M:- A:擎羊庙 D:73-82',
            '寅': '迁移 甲寅 M:廉贞庙 A:左辅,铃星庙 D:63-72',
            '卯': '疾厄 乙卯 M:- A:地劫,天魁 D:53-62',
            '辰': '财帛 丙辰 M:破军旺禄 A:- D:43-52',
            '巳': '子女 丁巳 M:天同庙 A:天钺 D:33-42',
            '午': '夫妻 戊午 M:天府旺,武曲旺 A:文昌陷 D:23-32',
            '未': '兄弟 己未 M:太阳得,太阴不科 A:地空,火星利 D:13-22',
            '申': '命宫 庚申 M:贪狼平忌 A:文曲得 D:3-12',
            '酉': '父母 辛酉 M:天机旺,巨门庙权 A:- D:113-122',
            '戌': '福德 壬戌 M:天相得,紫微得 A:- D:103-112',
            '亥': '田宅 癸亥 M:天梁陷 A:天马,陀罗陷 D:93-102',
        },
    },
    # X7_latezi_month_end: 2006-11-20 timeIndex=12 male fixLeap=True config={'yearDivide': 'normal', 'dayDivide': 'forward'} -> 二〇〇六年九月三十 丙戌 戊戌 甲寅 甲子
    'X7_latezi_month_end': {
        'ming': '戌', 'body': '戌', 'bureau': '木三局', 'ming_zhu': '禄存', 'shen_zhu': '文昌',
        'palaces': {
            '子': '福德 庚子 M:天府庙,武曲旺 A:左辅 D:23-32',
            '丑': '田宅 辛丑 M:太阳不,太阴庙 A:火星得 D:33-42',
            '寅': '官禄 庚寅 M:贪狼平 A:右弼 D:43-52',
            '卯': '仆役 辛卯 M:天机旺权,巨门庙 A:铃星利 D:53-62',
            '辰': '迁移 壬辰 M:天相得,紫微得 A:文曲得,陀罗庙 D:63-72',
            '巳': '疾厄 癸巳 M:天梁陷 A:禄存 D:73-82',
            '午': '财帛 甲午 M:七杀旺 A:擎羊陷 D:83-92',
            '未': '子女 乙未 M:- A:- D:93-102',
            '申': '夫妻 丙申 M:廉贞庙忌 A:天马 D:103-112',
            '酉': '兄弟 丁酉 M:- A:天钺 D:113-122',
            '戌': '命宫 戊戌 M:破军旺 A:文昌陷科 D:3-12',
            '亥': '父母 己亥 M:天同庙禄 A:地劫,地空,天魁 D:13-22',
        },
    },
}


# Как вызвать ziwei.calculate, чтобы получить ту же постановку, что в кейсе iztro
# (дата — местная гражданская, час задан ветвью, без часового пояса).
IZTRO_CASES = {
    "T1": (BirthInput(1990, 5, 15, gender="female"), dict(hour_branch="未")),
    "T2": (BirthInput(1984, 2, 4, gender="male"), dict(hour_branch="晚子")),
    "T2_tst": (BirthInput(1984, 2, 4, gender="male"), dict(hour_branch="亥")),
    "T2_zi_current": (BirthInput(1984, 2, 4, gender="male"), dict(hour_branch="晚子", zi_hour="same_day")),
    "T3": (BirthInput(2004, 2, 29, gender="female"), dict(hour_branch="辰")),
    "T4": (BirthInput(1879, 3, 14, gender="male"), dict(hour_branch="午")),
    "X1_leap": (BirthInput(2004, 4, 10, gender="male"), dict(hour_branch="寅")),
    "X1_leap_nofix": (BirthInput(2004, 4, 10, gender="male"), dict(hour_branch="寅", leap_month="same")),
    "X2_leap": (BirthInput(2020, 5, 23, gender="female"), dict(hour_branch="酉")),
    "X3_lichun": (BirthInput(2021, 2, 8, gender="male"), dict(hour_branch="卯")),
    "X3_lichun_exact": (BirthInput(2021, 2, 8, gender="male"), dict(hour_branch="卯", year_boundary="lichun")),
    "X4_iztro_readme": (BirthInput(2000, 8, 16, gender="female"), dict(hour_branch="寅")),
    "X5": (BirthInput(1980, 1, 1, gender="male"), dict(hour_branch="子")),
    "X6": (BirthInput(1993, 7, 24, gender="female"), dict(hour_branch="酉")),
    "MAO": (BirthInput(1893, 12, 26, gender="male"), dict(hour_branch="辰")),
}


@pytest.mark.parametrize("case_id", sorted(IZTRO_CASES))
def test_full_chart_matches_iztro(case_id):
    b, opts = IZTRO_CASES[case_id]
    assert signature(calculate(b, **opts)) == IZTRO[case_id]


def test_late_zi_month_end_differs_from_iztro():
    """2006-11-20 = 九月三十 (последний день месяца), поздний Цзы.
    ziwei.py (隔夜晚子): вся дата переходит на 十月初一 -> месяц 10, день 1.
    iztro 2.6.2: день +1 (=1), но месяц остаётся 9 — известное расхождение, задокументировано."""
    r = calculate(BirthInput(2006, 11, 20, gender="male"), hour_branch="晚子")
    assert (r["lunar_date"]["month"], r["lunar_date"]["day"]) == (10, 1)
    assert r["ming_palace"]["branch"] == "亥"
    assert signature(r)["ming"] != IZTRO["X7_latezi_month_end"]["ming"] == "戌"


# ---------------------------------------------------------------------------
# Эталонные персоны T1–T4 с реальным временем и местом
# ---------------------------------------------------------------------------

T1 = BirthInput(1990, 5, 15, 14, 30, place="Москва", gender="female")
T2 = BirthInput(1984, 2, 4, 23, 30, place="Москва", gender="male")
T3 = BirthInput(2004, 2, 29, 8, 15, place="Санкт-Петербург", gender="female")
T4 = BirthInput(1879, 3, 14, 11, 30, tz="LMT", lat=48.4011, lon=9.9876, gender="male")


def test_t1_default_true_solar_and_clock():
    r = calculate(T1)
    assert r["variant"]["time_basis"] == "true_solar"
    assert r["inputs_used"]["basis_time"] == "1990-05-15 13:04"   # 10:30 UTC + 2:30.5 LMT + ~3.7 мин EoT
    assert r["hour"]["branch"] == "未"
    assert any("10 минут" in w for w in r["warnings"])              # 13:04 — у границы 午/未
    assert signature(r) == IZTRO["T1"]
    assert signature(calculate(T1, time_basis="clock")) == IZTRO["T1"]
    assert r["year"]["stem_branch"] == "庚午"
    assert r["ming_palace"]["stem_branch"] == "丙戌" and r["bureau"]["nayin"] == "屋上土"
    assert r["sihua"]["禄"]["star"] == "太阳" and r["sihua"]["忌"]["branch"] == "巳"
    assert r["decade_direction"] == "backward"                      # ян-год (庚), женщина


def test_t2_true_solar_gives_hai_hour():
    r = calculate(T2)
    assert r["inputs_used"]["basis_time"] == "1984-02-04 22:46"
    assert r["hour"]["branch"] == "亥" and not r["hour"]["late_zi"]
    assert signature(r) == IZTRO["T2_tst"]
    assert any("clock" in w and "子" in w for w in r["warnings"])


def test_t2_clock_late_zi_variants():
    r = calculate(T2, time_basis="clock")
    assert r["hour"] == {"branch": "子", "index": 0, "range": "23:00–01:00", "late_zi": True}
    assert r["inputs_used"]["chart_date"] == "1984-02-05"
    assert (r["lunar_date"]["month"], r["lunar_date"]["day"]) == (1, 4)
    assert r["year"]["stem_branch"] == "甲子"   # Новый год 02.02.1984; Личунь 04.02 18:19 MSK — тоже 甲子
    assert signature(r) == IZTRO["T2"]
    r2 = calculate(T2, time_basis="clock", zi_hour="same_day")
    assert r2["lunar_date"]["day"] == 3
    assert signature(r2) == IZTRO["T2_zi_current"]
    # Личунь-граница не меняет год у T2 (рождение после Личуня)
    assert calculate(T2, time_basis="clock", year_boundary="lichun")["year"]["stem_branch"] == "甲子"


def test_t3_feb29():
    r = calculate(T3)
    assert r["inputs_used"]["basis_time"] == "2004-02-29 07:03"
    assert r["hour"]["branch"] == "辰"
    assert signature(r) == IZTRO["T3"]
    assert signature(calculate(T3, time_basis="clock")) == IZTRO["T3"]
    assert r["lunar_date"]["text"] == "二〇〇四年二月初十"


def test_t4_einstein_lmt():
    r = calculate(T4)
    assert r["hour"]["branch"] == "午"
    assert signature(r) == IZTRO["T4"]
    assert r["year"]["stem_branch"] == "己卯"
    assert r["ming_palace"]["branch"] == r["body_palace"]["branch"] == "酉"   # час 午 -> 身宫 = 命宫
    assert r["bureau"]["name"] == "金四局"


# ---------------------------------------------------------------------------
# Опубликованная внешняя карта: Мао Цзэдун (не из iztro)
# ---------------------------------------------------------------------------

def test_mao_published_chart():
    # https://wfate.blogspot.com/2013/06/blog-post_15.html — 癸巳年十一月十九日辰時, 木三局, 命 庚申, 身 辰;
    # https://ziwei.yi958.com/2020/08/22/zi-wei-ming-pan-mao-ze-dong-zhu-xi-de-zi-wei-dou-shu-ming/ —
    # «命宫贪狼文曲化忌在申», «身宫破军化禄坐辰宫», «子女宫天同天钺», «事业宫七杀右弼», «福宫紫微天相在戌»,
    # «命主为廉贞星».
    r = calculate(BirthInput(1893, 12, 26, gender="male"), hour_branch="辰")
    assert r["lunar_date"]["text"] == "一八九三年冬月十九"
    assert r["bureau"]["name"] == "木三局"
    assert r["ming_palace"]["stem_branch"] == "庚申" and r["body_palace"]["branch"] == "辰"
    assert r["ming_zhu"] == "廉贞"
    published = {  # дворец: (ствол-ветвь, главные, вспомогательные из 14) — по тексту wfate.blogspot
        "命宫": ("庚申", {"贪狼"}, {"文曲"}),
        "兄弟": ("己未", {"太阳", "太阴"}, {"火星", "地空"}),
        "夫妻": ("戊午", {"天府", "武曲"}, {"文昌"}),
        "子女": ("丁巳", {"天同"}, {"天钺"}),
        "财帛": ("丙辰", {"破军"}, set()),
        "疾厄": ("乙卯", set(), {"地劫", "天魁"}),
        "迁移": ("甲寅", {"廉贞"}, {"左辅", "铃星"}),
        "仆役": ("乙丑", set(), {"擎羊"}),
        "官禄": ("甲子", {"七杀"}, {"右弼", "禄存"}),
        "田宅": ("癸亥", {"天梁"}, {"陀罗", "天马"}),
        "福德": ("壬戌", {"紫微", "天相"}, set()),
        "父母": ("辛酉", {"巨门", "天机"}, set()),
    }
    got = {p["name"]: (p["stem_branch"], {s["star"] for s in p["major_stars"]}, {s["star"] for s in p["aux_stars"]})
           for p in r["palaces"]}
    assert got == published
    assert r["sihua"]["忌"]["star"] == "贪狼" and r["sihua"]["禄"]["star"] == "破军"
    decades = {p["name"]: p["decade_ages"] for p in r["palaces"]}
    assert decades["命宫"] == [3, 12] and decades["兄弟"] == [13, 22] and decades["官禄"] == [83, 92]


# ---------------------------------------------------------------------------
# Правила по отдельности (опубликованные примеры)
# ---------------------------------------------------------------------------

def test_ziwei_examples_ncc():
    # https://www.ncc.com.tw/fate/paleo/gv/gv_15.htm «起紫微星訣», примеры 1–3
    assert BRANCHES[ziwei_branch(27, 3)[0]] == "戌"
    assert BRANCHES[ziwei_branch(13, 6)[0]] == "亥"
    assert BRANCHES[ziwei_branch(6, 5)[0]] == "未"
    # «水二局: 初一 丑, 初二 寅»
    assert BRANCHES[ziwei_branch(1, 2)[0]] == "丑" and BRANCHES[ziwei_branch(2, 2)[0]] == "寅"


def test_ziwei_start_verse():
    # «六五四三二，酉午亥辰丑»: день 1 при бюро 6,5,4,3,2 -> 酉,午,亥,辰,丑
    assert [BRANCHES[ziwei_branch(1, n)[0]] for n in (6, 5, 4, 3, 2)] == list("酉午亥辰丑")


def test_ziwei_full_table_shape():
    # 紫微 не может стоять дважды одинаково для соседних дней «слишком далеко»: проверим
    # периодичность — при бюро n дни d и d+n дают сдвиг ровно на 1 ветвь вперёд.
    for n in (2, 3, 4, 5, 6):
        for d in range(1, 31 - n + 1):
            assert (ziwei_branch(d + n, n)[0] - ziwei_branch(d, n)[0]) % 12 == 1


def test_tianfu_mirror_ncc():
    # «丑卯相更迭, 未酉互為根, 往來午與戌, 蹀躞子和辰, 巳亥交馳騁, 同位在寅申»
    pairs = {"丑": "卯", "卯": "丑", "未": "酉", "酉": "未", "午": "戌", "戌": "午",
             "子": "辰", "辰": "子", "巳": "亥", "亥": "巳", "寅": "寅", "申": "申"}
    for z, f in pairs.items():
        assert BRANCHES[tianfu_branch(B(z))] == f


@pytest.mark.parametrize("gzs,expected", [
    ("丙子", 2), ("辛未", 5), ("庚申", 3),   # https://iztro.com/learn/setup
    ("戊寅", 5), ("甲戌", 6),                # https://www.ncc.com.tw/fate/paleo/gv/gv_15.htm
    ("丙戌", 5),                             # https://zh.wikipedia.org/wiki/紫微斗數 «命宮坐丙戌，為土五局»
])
def test_bureau_examples(gzs, expected):
    s, b = STEMS.index(gzs[0]), B(gzs[1])
    assert bureau_number(s, b) == expected == bureau_number_mnemonic(s, b)


def test_bureau_formula_equals_nayin_all_60():
    for i in range(60):
        assert bureau_number(i % 10, i % 12) == bureau_number_mnemonic(i % 10, i % 12)
    assert nayin(0, 0) == "海中金" and nayin(9, 11) == "大海水"


def test_five_tigers():
    # 甲己→丙寅, 乙庚→戊寅, 丙辛→庚寅, 丁壬→壬寅, 戊癸→甲寅
    assert [STEMS[yin_stem(s)] for s in range(10)] == list("丙戊庚壬甲丙戊庚壬甲")
    # 子 и 丑 получают стволы 寅 и 卯 (продолжение счёта после 亥)
    for s in range(10):
        assert palace_stem(s, B("子")) == palace_stem(s, B("寅"))
        assert palace_stem(s, B("丑")) == palace_stem(s, B("卯"))


def test_huo_ling_example():
    # https://iztro.com/learn/setup: «壬辰年卯时生人 … 火星在巳，铃星在丑»
    pos = aux_star_positions(STEMS.index("壬"), B("辰"), 1, B("卯"))
    assert BRANCHES[pos["火星"]] == "巳" and BRANCHES[pos["铃星"]] == "丑"


def test_body_palace_invariant():
    # 身宫 всегда в одном из 6 дворцов: 子午 -> 命, 丑未 -> 福德, 寅申 -> 官禄, 卯酉 -> 迁移, 辰戌 -> 财帛, 巳亥 -> 夫妻
    expect = {0: "命宫", 1: "福德", 2: "官禄", 3: "迁移", 4: "财帛", 5: "夫妻"}
    for m in range(1, 13):
        for h in range(12):
            mb, sb = ming_branch(m, h), body_branch(m, h)
            assert PALACES[(mb - sb) % 12][0] == expect[h % 6]


def test_hour_branch_index():
    assert [hour_branch_index(h) for h in (0, 1, 2, 3, 11, 12, 13, 21, 22, 23)] == [0, 1, 1, 2, 6, 6, 7, 11, 11, 0]
    assert hour_branch_index(0, 59) == 0 and hour_branch_index(1, 0) == 1


def test_sihua_variants():
    assert sihua_for_stem(STEMS.index("庚")) == {"禄": "太阳", "权": "武曲", "科": "太阴", "忌": "天同"}
    assert sihua_for_stem(STEMS.index("庚"), "quanshu") == {"禄": "太阳", "权": "武曲", "科": "天同", "忌": "太阴"}
    assert sihua_for_stem(STEMS.index("庚"), "zhongzhou")["科"] == "天府"
    assert sihua_for_stem(STEMS.index("庚"), "beipai")["忌"] == "天相"
    assert sihua_for_stem(STEMS.index("壬"), "quanshu")["科"] == "天府"
    assert sihua_for_stem(STEMS.index("戊"), "zhongzhou")["科"] == "太阳"
    # T1 (庚午): при 全书 忌 у 太阴 (дворец 未)
    r = calculate(T1, sihua="quanshu")
    assert r["sihua"]["忌"] == {"star": "太阴", "star_ru": "Тай Инь (Луна)", "branch": "未",
                                "meaning_ru": "Хуа Цзи (препятствие)"}


def test_kui_yue_variant_for_geng():
    r = calculate(T1, kui_yue="geng_wu_yin")
    assert r["star_positions"]["天魁"] == "午" and r["star_positions"]["天钺"] == "寅"
    r0 = calculate(T1)
    assert r0["star_positions"]["天魁"] == "丑" and r0["star_positions"]["天钺"] == "未"


def test_ming_zhu_by_year_branch():
    assert calculate(T1, ming_zhu="year_branch")["ming_zhu"] == "破军"  # год 午
    assert calculate(T1)["ming_zhu"] == "禄存"                          # 命宫 戌


def test_leap_month_rules():
    b = BirthInput(2004, 4, 10, gender="male")  # 闰二月廿一
    assert calculate(b, hour_branch="寅")["lunar_date"]["month_used"] == 3
    assert calculate(b, hour_branch="寅", leap_month="same")["lunar_date"]["month_used"] == 2
    assert calculate(b, hour_branch="寅", leap_month="next")["lunar_date"]["month_used"] == 3
    b2 = BirthInput(2020, 5, 23, gender="female")  # 闰四月初一
    assert calculate(b2, hour_branch="酉")["lunar_date"]["month_used"] == 4
    assert calculate(b2, hour_branch="酉", leap_month="next")["lunar_date"]["month_used"] == 5


def test_lichun_with_real_time():
    # 2021-02-03 22:59 Пекин: Личунь 2021 наступил 03.02 22:58:39 по Пекину -> уже 辛丑 по Личуню
    b = BirthInput(2021, 2, 3, 23, 30, place="Пекин", gender="male")
    r = calculate(b, year_boundary="lichun", time_basis="clock")
    assert r["year"]["stem_branch"] == "辛丑"
    assert calculate(b, time_basis="clock")["year"]["stem_branch"] == "庚子"


def test_partial_without_time():
    r = calculate(BirthInput(1990, 5, 15, gender="female"))
    assert r["status"] == "partial"
    assert len(r["candidates_by_hour"]) == 12
    wei = next(c for c in r["candidates_by_hour"] if c["hour_branch"] == "未")
    assert wei["ming"] == "丙戌" and wei["ziwei"] == "戌" and wei["bureau"] == "土五局"
    assert r["year_month_stars"]["禄存"] == "申"


def test_flow_year_t1_2026():
    r = calculate(T1, flow_year=2026)
    fy = r["flow_year"]
    assert fy["stem_branch"] == "丙午" and fy["nominal_age"] == 37
    assert fy["flow_ming_natal_palace"] == "财帛"
    assert fy["decade"]["ages"] == [35, 44] and fy["decade"]["palace"] == "子女"
    assert fy["flow_sihua"]["忌"]["star"] == "廉贞"


def test_output_is_json_serializable():
    import json
    json.dumps(calculate(T2, flow_year=2025), ensure_ascii=False)
    json.dumps(calculate(BirthInput(1990, 5, 15)), ensure_ascii=False)


def test_unknown_option_rejected():
    with pytest.raises(ValueError):
        calculate(T1, foo=1)


def test_option_aliases_compatible_with_bazi():
    a = calculate(T2, solar_time="clock", zi_hour="late")
    b = calculate(T2, time_basis="clock", zi_hour="same_day")
    assert signature(a) == signature(b) == IZTRO["T2_zi_current"]
    assert signature(calculate(T2, solar_time="clock", zi_hour="early")) == IZTRO["T2"]
