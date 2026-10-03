#!/usr/bin/env python3
"""Сборка сайта: темы и сгенерированные страницы → MkDocs Material.

Одно правило держит всю сборку: `content/` только читается. Всё, что нужно
дописать к теме — ссылки вместо идентификаторов, картинку вместо схемы,
раскрытия аббревиатур, — дописывается в копии, в staging-дереве `build/site-src`.
Исходник темы остаётся тем, что автор написал и что читают линтеры; сайт —
производная, и его можно снести целиком в любой момент.

Что сборщик делает с темой

  * frontmatter из 27 полей сводится к трём, которые понимает движок
    (`title`, `description`, `tags`); остальные со шапки убраны решением
    оператора 2026-08-24 (свод 4.1), `status` — решением 2026-10-02.
    Исключение одно — условие `skip_if`, о нём свой пункт ниже;
  * тема подаётся как статья, а не как заполненная форма (решение оператора
    2026-10-02): шапка «Уровень … · время …» и абзац «Что прочитать сначала»
    со страницы сняты, предпосылки стоят в конце строкой «Перед этой темой
    полезно знать: …» со ссылками-названиями; у заголовков блоков нет номеров,
    канонические названия заменены живыми (`BLOCK_TITLES`), «Цели» не
    выводятся, «Предвопросы» и «Чеклист ревью» свёрнуты во врезки; цитаты с
    меткой «**Примечание.**», «**Предупреждение.**» и подобными становятся
    admonition своего типа (`CALLOUTS`); листинг `text` с приглашением `$ `
    подсвечивается как сеанс терминала;
  * всё от заголовка «## N. Источники» до конца файла отрезается: «Каркас
    этапа», «Скоропортящийся слой» и «Маркеры уверенности» пишутся для аудита
    и читателю не показываются (решение оператора 2026-08-31). Сам список
    источников с 2026-10-01 возвращён на страницу в другом виде: раздел
    «Что почитать дальше» (до 2026-10-02 — «Первоисточники») собирается из
    поля `sources` темы и реестра `sources.yaml` — название, издатель,
    версия и адрес каждого документа.
    Определения сносок `[^N]: …` из этого хвоста — исключение:
    метки сносок остаются в прозе, поэтому определения переносятся в конец
    страницы, после блока «Дальше»; теме без явного определения оно
    собирается из пункта списка «Источников» с тем же номером;
  * в конец страницы добавляется блок «Дальше» — одна ссылка на следующую
    тему маршрута (этапы — в порядке `taxonomy.yaml`, темы внутри этапа —
    по полю `order`; у последней темы маршрута блока нет). В исходниках
    блока нет: руками ведённый список был второй записью того же маршрута
    (решение оператора 2026-08-31);
  * `` `topic-id` `` в обратных кавычках становится ссылкой на страницу темы,
    подписанной названием темы, а не идентификатором (решение оператора
    2026-10-01, А1). В исходниках markdown-ссылок между темами нет и не будет:
    9.1 п. 6 требует ссылаться идентификатором, а не путём, чтобы
    переименование каталога не ломало текст. Превращение делает сборка;
  * в конец блока «Лаба» дописывается строка запуска: `cd` в каталог лабы и
    команды прогона из её README, со ссылкой на страницу лабы (А8);
  * ограждённый блок `mermaid` заменяется двумя нарисованными SVG — светлым и
    тёмным (`tools/render_diagrams.py`), потому что сайт открывается с диска и
    скрипт из сети загрузить не может; метки `#only-light`/`#only-dark` в
    адресе картинки дают движку темы показать вариант активной палитры;
  * серии строк «A. …», «B. …» в «Проверь себя» становятся абзацами с
    бейджем-буквой (`quiz_options`): markdown такого списка не знает, и
    варианты были неотличимы от прозы;
  * в конец страницы вклеиваются определения аббревиатур из `glossary.yaml` —
    те, что на странице действительно встретились. Читатель видит раскрытие по
    наведению, а канон написания остаётся один (6.3);
  * ссылки на блок в прозе («из блока 5», «из блока «Механика»»)
    переписываются живым названием блока: номеров на странице больше нет;
  * первое вхождение термина глоссария на странице становится ссылкой на его
    статью в глоссарии (9.5 п. 14). Ищется в прозе вне кода, заголовков и
    цитат — теми же написаниями и тем же стеммингом, что `glossary_lint.py`;
  * тема, чья ревизия просрочена более чем вдвое, получает плашку «может
    быть устаревшим» (9.6 п. 20). Считается в календарных месяцах — так же,
    как линтер `validate_content.py`: единицы у сборки и проверки одни;
  * тема с полем `skip_if` получает под заголовком строку «можно отложить,
    если …» (9.5 п. 10): маркер подсказывает, когда
    тему законно отложить, сам маршрут от него не меняется. Поля нет —
    строки нет.

Что сборщик генерирует сам: главную (баннер и карточки этапов), карту тем, маппинг-индекс внешних
каталогов (9.6 п. 24), глоссарий (из того же `glossary.yaml`, что и
`GLOSSARY.md`), индекс тегов и страницу «Атрибуции и лицензии» (PLAYBOOK 10.1
п. 4). С 2026-10-01 к ним добавлены (решения оператора по реестру
`journal/RESEARCH-NOVICE-2026-10.md`, пункты 5 и 7):

  * на каждый этап — страница «Повторение» (вопросы из «Предвопросов» и
    «Проверь себя» пройденных тем плюс функции из лабораторных без подписей)
    и сводка этапа (блоки «Коротко» всех тем подряд и общий чеклист ревью);
  * страница «На чём проверено» — версии инструментов и каталогов из
    «Маркеров уверенности» тем, без дат;
  * страница «Лабы» из `labs.yaml` и страница на каждую лабораторную из её
    README (тем же решением, пункт А8).

Сроки ревизии и состояние тем со страниц ушли
решением оператора 2026-08-26: это журнал производства, а не материал читателя.
Числа печатаются в отчёт сборки — тому, кто её запустил.

Навигация выводится из `stage` и `order` (9.1 п. 7) и дописывается в
`build/mkdocs.yml`, который наследует корневой `mkdocs.yml` механизмом `INHERIT`.
Руками правится только корневой конфиг.

    make site           # собрать в `site/`
    make serve          # собрать и открыть локальный сервер
    .venv-tools/bin/python tools/build_site.py --no-build   # только дерево
"""

from __future__ import annotations

import argparse
import ast
import hashlib
import html
import os
import re
import shutil
import subprocess
import sys
from datetime import date
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
import gen_glossary  # noqa: E402
import mdtext  # noqa: E402
import render_diagrams  # noqa: E402
import validate_content as vc  # noqa: E402
import wordcount  # noqa: E402
from paths import BUILD_DIR, GLOSSARY_YAML, ROOT, SITE_DIR, TOPICS_YAML  # noqa: E402

SRC = BUILD_DIR / "site-src"
CONFIG_IN = ROOT / "mkdocs.yml"
CONFIG_OUT = BUILD_DIR / "mkdocs.yml"
MKDOCS = ROOT / ".venv-site" / "bin" / "mkdocs"
SHIM_SRC = ROOT / "tools" / "vendor" / "iframe-worker-shim.js"
SHIM_REL = "assets/iframe-worker-shim.js"

# JetBrains Mono (OFL 1.1) для листингов и кода: обычное и жирное начертания —
# других на страницах не встречается. Скачаны с релиза v2.304
# (github.com/JetBrains/JetBrainsMono), текст лицензии лежит рядом.
FONTS_SRC = ROOT / "tools" / "vendor" / "fonts"

# Плагин `offline` вставляет в каждую страницу шим WebWorker с unpkg: браузер не
# создаёт воркер из `file://`, а поиск Material живёт в воркере. Ссылка в сеть
# делает «офлайновый» сайт неофлайновым — проверено chrome-headless-shell без
# сети: поиск висит на «Инициализация поиска». Файл лежит в `tools/vendor/`,
# ссылка после сборки переписывается на относительный путь.
SHIM_URL = "https://unpkg.com/iframe-worker/shim"

# Аббревиатура — прописная латиница; из глоссария берутся такие термины и поле
# `abbr`, если оно заполнено. Аббревиатуры вклеиваются только те, что на
# странице встретились в прозе: определение к неупомянутой аббревиатуре ничего
# не значит.
ABBR_SHAPE = re.compile(r"\A[A-Z][A-Za-z0-9./+-]{1,19}\Z")

GENERATED = "<!-- Собрано `tools/build_site.py`. Правки — в исходники, не сюда. -->"

# ── вспомогательное ──────────────────────────────────────────────────────────


def one_line(text: str) -> str:
    return " ".join(str(text or "").split())


def link_to(page_rel: str, target_rel: str) -> str:
    """Ссылка со страницы `page_rel` на `target_rel`, обе от корня дерева."""
    return os.path.relpath(target_rel, os.path.dirname(page_rel)).replace("\\", "/")


def apply_edits(raw: str, edits: list[tuple[int, int, str]]) -> str:
    """Заменить участки текста по смещениям. Пересечений быть не должно."""
    out, last = [], 0
    for start, end, text in sorted(edits):
        if start < last:
            raise ValueError(f"пересекающиеся правки на смещении {start}")
        out.append(raw[last:start])
        out.append(text)
        last = end
    out.append(raw[last:])
    return "".join(out)


def short_title(title: str) -> str:
    """Заголовок темы для схемы и таблицы: до двоеточия, не длиннее 42 знаков."""
    head = one_line(title).split(":")[0].strip(" —")
    return head if len(head) <= 42 else head[:41].rstrip() + "…"


# ── аббревиатуры глоссария ───────────────────────────────────────────────────


def abbreviations(glossary: dict) -> dict[str, str]:
    """Аббревиатура → раскрытие. Раскрытие короткое: оригинал, если он есть,
    иначе первое предложение определения."""
    out: dict[str, str] = {}
    for term in glossary["terms"]:
        key = term.get("abbr") or (term["term"] if ABBR_SHAPE.match(term["term"])
                                   and term["term"].upper() == term["term"] else None)
        if not key:
            continue
        en = one_line(term.get("en") or "")
        if en and en.lower() != key.lower():
            text = en if key == term.get("abbr") else en
        else:
            text = one_line(term["definition"]).split(". ")[0].rstrip(".")
            if len(text) > 120:
                text = text[:119].rstrip() + "…"
        if key == term.get("abbr"):
            text = f"{term['term']} ({text})" if text else term["term"]
        out[key] = text
    return out


def used_abbr(prose: str, table: dict[str, str]) -> dict[str, str]:
    return {k: v for k, v in table.items()
            if re.search(rf"(?<![A-Za-z0-9]){re.escape(k)}(?![A-Za-z0-9])", prose)}


# ── ссылки на глоссарий ──────────────────────────────────────────────────────
#
# 9.5 п. 14: первое вхождение термина на странице — ссылка на глоссарий.
# Написания и стемминг те же, что у `glossary_lint.py` (термин, английский
# оригинал, аббревиатура, синонимы), поэтому «первое вхождение» здесь и в
# проверке G-FIRST совпадает. Ссылку получает только первое вхождение термина
# на странице, в любом из его написаний.


def glossary_spellings(t: dict) -> list[str]:
    """Все написания записи глоссария: термин, оригинал, аббревиатура, синонимы."""
    out = [t["term"]]
    for f in ("en", "abbr"):
        if t.get(f):
            out.append(t[f])
    out += list(t.get("aliases") or [])
    return out


def glossary_matcher(glossary: dict) -> tuple[re.Pattern, dict[str, str]]:
    """Одно выражение на все написания всех терминов. Имя группы совпадения
    знает id термина — по нему строится якорь `glossary.md#id`.

    Написание, заявленное двумя терминами, из выражения убирается: угадать,
    куда ссылка, нельзя, а молча вести не туда хуже, чем не вести.
    """
    seen: dict[str, str] = {}
    forms: list[tuple[str, str]] = []
    for t in glossary["terms"]:
        for sp in glossary_spellings(t):
            key = sp.lower()
            if key in seen and seen[key] != t["id"]:
                continue
            seen[key] = t["id"]
            forms.append((sp, t["id"]))
    owner: dict[str, str] = {}
    branches = []
    for i, (sp, tid) in enumerate(sorted(forms, key=lambda x: -len(x[0]))):
        name = f"g{i}"
        owner[name] = tid
        branches.append(f"(?P<{name}>{mdtext.stem_pattern(sp)})")
    return re.compile("|".join(branches), re.I), owner


HEADING_LINE_RE = re.compile(r"^#{1,6}[ \t].*$", re.M)
MD_LINK_RE = re.compile(r"!?\[[^\]\n]*\]\([^)\n]*\)")
QUOTED_RE = re.compile(r"«[^»]*»", re.S)
# Перенос строки, за которым строка начинается с разметки: ссылка с таким
# переносом внутри разорвётся, поэтому совпадение пропускается.
WRAP_MARKUP_RE = re.compile(r"\n[ \t]*(?:[>\-*+#|]|\d+[.)])")


def blank_out(text: str) -> str:
    return "".join("\n" if ch == "\n" else " " for ch in text)


def glossary_links(page: vc.Page, page_rel: str, raw: str,
                   gloss: tuple[re.Pattern, dict[str, str]],
                   taken: list[tuple[int, int, str]], report: dict,
                   drops: list[tuple[int, int]] | None = None
                   ) -> list[tuple[int, int, str]]:
    """Правки «термин → ссылка на глоссарий» для первых вхождений на странице.

    Поиск идёт по прозе (`doc.prose` уже без кода и адресов), обрезанной на
    блоке «Источники» — хвост для аудита на страницу не попадает. Гасятся
    заголовки, чужие слова в «ёлочках» и готовые ссылки: ссылку в ссылку
    markdown не завернёт.
    """
    rx, owner = gloss
    zone = page.doc.prose
    cut = SOURCES_HEAD_RE.search(zone)
    if cut:
        zone = zone[:cut.start()]
    for mask_re in (HEADING_LINE_RE, MD_LINK_RE, QUOTED_RE):
        zone = mask_re.sub(lambda m: blank_out(m.group(0)), zone)
    # Участки, которые на страницу не попадают (шапка, предпосылки, «Цели»):
    # первое вхождение термина в них ссылкой не станет, и следующее за ним
    # осталось бы без ссылки вовсе.
    for a, b in drops or []:
        zone = zone[:a] + blank_out(zone[a:b]) + zone[b:]

    first: dict[str, tuple[int, int]] = {}
    for m in rx.finditer(zone):
        first.setdefault(owner[m.lastgroup], (m.start(), m.end()))

    href = link_to(page_rel, "glossary.md")
    out = []
    for tid, (a, b) in first.items():
        if any(a < e and s < b for s, e, _ in taken):
            continue
        text = raw[a:b]
        if "\n" in text:
            if WRAP_MARKUP_RE.search(text):
                continue
            text = text.replace("\n", " ")
        out.append((a, b, f"[{text}]({href}#{tid})"))
    report["gloss"] += len(out)
    return out


# ── тема → страница ──────────────────────────────────────────────────────────


def front_block(page: vc.Page) -> str:
    """Мета для движка: три поля вместо двадцати семи.

    Поля `status` больше нет (решение оператора 2026-10-02): плашка «Готовая
    тема» в меню — след производства, читателю статьи она ничего не говорит.
    """
    meta = {
        "title": one_line(page.front.get("title") or page.id),
        "description": one_line(page.front.get("summary") or ""),
    }
    tags = page.front.get("tags") or []
    if tags:
        meta["tags"] = list(tags)
    dumped = yaml.safe_dump(meta, allow_unicode=True, sort_keys=False,
                            default_flow_style=False, width=10 ** 6)
    return f"---\n{dumped}---\n"


# ── заголовки блоков: живые названия вместо номеров слотов ──────────────────
#
# В исходнике номер блока — номер слота канона (`SCHEMA.md` § 4): «Механика»
# всегда 3, «Как ловится автоматикой» всегда 8, и по этому номеру проверки
# `C-BLOCK-*` сравнивают блоки разных тем между собой. Читателю номер слота не
# сообщает ничего. До 2026-10-02 сборка перенумеровывала блоки подряд; решением
# оператора 2026-10-02 номеров на странице нет вовсе, а канонические названия
# заменены живыми — тема читается как статья, а не как заполненная форма.
#
# Соответствие ниже — единственное место, где оно задано. Ключ — название
# блока в исходнике без номера; значение — что выводится на странице:
#   * строка — новое название заголовка;
#   * None — блок не показывается (цели темы — инструмент автора, а не текст);
#   * ADMON — заголовок со своим блоком сворачивается во врезку (см. ниже).
# Новые названия стоят и ключами: исходник, где живой заголовок уже написан,
# проходит как есть (отображение идемпотентно).
#
# Вместе с заголовками переписываются ссылки на блок в прозе: «из блока 5»
# становится «из блока «Как это выглядит в коде»», «из блока «Механика»» —
# «из блока «Как это работает»». Ссылки ищутся по `prose_spans`, где
# ограждённые блоки забиты пробелами: «блок 1: 2175 обращений к оракулу» в
# листинге `padding-oracle` относится к блоку шифра, и переписывать его нельзя.

PREQ_TITLE = "Подумай, прежде чем читать"
CHECK_TITLE = "Чеклист для ревью"
READ_MORE = "Что почитать дальше"

BLOCK_TITLES: dict[str, str | None] = {
    "Коротко": "Если коротко",
    "Цели": None,
    "Предвопросы": PREQ_TITLE,
    "Механика": "Как это работает",
    "Эксплуатация": "Как это атакуют",
    "Как выглядит в коде": "Как это выглядит в коде",
    "Как чинится": "Как защититься",
    "Как проверить фикс": "Как убедиться, что защита работает",
    "Как ловится автоматикой": "Как это находят инструменты",
    "Ловушка": "Частая ошибка",
    "Чеклист ревью": CHECK_TITLE,
    "Лаба": "Попробуй сам",
    "Задача": "Попробуй сам",
    "Проверь себя": "Проверь себя",
    "Источники": READ_MORE,
}
for _new in [v for v in BLOCK_TITLES.values() if v]:
    BLOCK_TITLES.setdefault(_new, _new)

# Заголовки, которые на странице становятся свёрнутой врезкой: тип и подпись.
ADMON_HEADS = {PREQ_TITLE: ("question", PREQ_TITLE),
               CHECK_TITLE: ("success", CHECK_TITLE)}

# Ссылки на блок по имени в прозе: «Механика» → «Как это работает». Падежные
# формы — только те, что встречаются в корпусе («подглядывая в «Ловушку»»).
NAME_REFS = {old: new for old, new in BLOCK_TITLES.items()
             if new and old != new and new not in ADMON_HEADS}
NAME_REFS.update({"Ловушку": "Частую ошибку", "Ловушке": "Частой ошибке",
                  "Чеклист ревью": CHECK_TITLE, "Предвопросы": PREQ_TITLE})
NAME_REF_RE = re.compile(
    "«(" + "|".join(sorted((re.escape(k).replace(r"\ ", r"\s+")
                            for k in NAME_REFS), key=len, reverse=True))
    + ")»", re.I)

BLOCK_REF_RE = re.compile(
    r"(?<![\w-])(?:[Бб]лок(?:а|е|у|ом|и|ов|ах|ам|ами)?)[ \t]+"
    r"(\d+(?:[ \t]*(?:,|и|—)[ \t]*\d+)*)(?![\d.,]\d)")
REF_NUM_RE = re.compile(r"\d+")
H2_NUM_PREFIX_RE = re.compile(r"\A(\d+)\.[ \t]+")

# Хвост темы для аудита: «Источники» и всё за ними («Каркас этапа»,
# «Скоропортящийся слой», «Маркеры уверенности») на страницу не выносятся —
# решение оператора 2026-08-31. Признак — заголовок; номер у него необязателен,
# а живое название «Что почитать дальше» — тот же блок (идемпотентность).
SOURCES_HEAD_RE = re.compile(
    rf"^##[ \t]+(?:\d+\.[ \t]+)?(?:Источники|{READ_MORE})[ \t]*$", re.M)

# Сноска — два куска: метка `[^N]` в прозе и определение `[^N]: …` в самом
# конце файла, за аппаратом аудита. Метки остаются на странице, а определения
# срез с «Источников» уносил вместе с хвостом: движок не находил определения и
# оставлял висячий литерал `[^1]` (находка X-STYLE-06). Поэтому определения
# собираются из хвоста до среза и переносятся в конец страницы. Темам без
# явных определений (16 штук) определение собирается из пункта списка
# «Источников» с тем же номером — тем же коротким видом, каким автор пишет
# явные определения: кто и что, без перечня разделов и адреса.
FN_DEF_RE = re.compile(r"^\[\^([0-9A-Za-z_-]+)\]:[ \t]*(.*)$")
FN_REF_RE = re.compile(r"\[\^([0-9A-Za-z_-]+)\]")
SRC_ITEM_RE = re.compile(r"^(\d+)\.[ \t]+(.*)$")
SRC_DETAIL_RE = re.compile(r"\.\s+Раздел[ыи]?(?::|\s)")


def footnote_defs(tail: str) -> dict[str, str]:
    """Явные определения сносок в хвосте: строка `[^N]: …` и её продолжения
    с отступом — в корпусе встречаются оба вида (bscp)."""
    defs: dict[str, str] = {}
    cur = None
    for line in tail.split("\n"):
        m = FN_DEF_RE.match(line)
        if m:
            cur = m.group(1)
            defs[cur] = m.group(2).strip()
        elif cur and re.match(r"^[ \t]+\S", line):
            defs[cur] += " " + line.strip()
        elif line.strip():
            cur = None
    return defs


def source_items(tail: str) -> dict[str, str]:
    """Нумерованный список «Источников»: номер → текст пункта одной строкой.
    Пункты идут подряд с единицы, продолжения — с отступом; список кончается
    на первой строке без отступа («Каркас этапа: …»), поэтому «65.» из
    «Маркеров уверенности» пунктом не считается."""
    items: dict[str, str] = {}
    expect, cur = 1, None
    for line in tail.split("\n")[1:]:  # первой строкой стоит сам заголовок
        m = SRC_ITEM_RE.match(line)
        if m and int(m.group(1)) == expect:
            cur = str(expect)
            items[cur] = m.group(2).strip()
            expect += 1
        elif cur and re.match(r"^[ \t]+\S", line):
            items[cur] += " " + line.strip()
        elif line.strip():
            break
    return items


def synth_def(item: str) -> str:
    """Определение сноски из пункта «Источников»: первое предложение без
    перечня разделов и адреса — так выглядят явные определения автора."""
    text = SRC_DETAIL_RE.split(item, maxsplit=1)[0]
    m = re.search(r"\.\s", text)
    if m:
        text = text[:m.start() + 1]
    text = mdtext.AUTOLINK_RE.sub("", text).strip()
    return text if text.endswith(".") else text + "."


def prose_only(text: str) -> str:
    """Текст с забитыми пробелами ограждёнными блоками и инлайн-кодом: метка
    сноски внутри листинга — не метка, а символы примера."""
    spans = [(m.start(), m.end()) for m in mdtext.FENCE_RE.finditer(text)]
    chars = list(text)
    for start, end in spans:
        for i in range(start, end):
            if chars[i] != "\n":
                chars[i] = " "
    return mdtext.CODE_SPAN_RE.sub(lambda m: " " * len(m.group(0)),
                                   "".join(chars))


def line_offsets(lines: list[str]) -> list[int]:
    """Смещение начала каждой строки в тексте; последний элемент — длина."""
    out = [0]
    for ln in lines:
        out.append(out[-1] + len(ln) + 1)
    return out


def para_span(raw: str, start: int, text: str) -> tuple[int, int]:
    """Участок абзаца вместе с пустыми строками за ним: снятый абзац не
    оставляет двойного пробела между соседями."""
    end = start + len(text)
    while raw[end:end + 1] == "\n":
        end += 1
    return start, end


# Шапка темы — абзац «Уровень **L2** · время…» сразу под заголовком. С
# 2026-10-02 на страницу не выводится (решение оператора): уровень, время и
# его раскладка — счётчики производства, а не текст статьи.
LEAD_START_RE = re.compile(r"\AУровень \*\*")


def block_display(title: str) -> str | None:
    """Что выводится вместо заголовка блока `title` (уже без номера)."""
    return BLOCK_TITLES.get(title.strip(), title.strip())


def heading_edits(page: vc.Page) -> tuple[list[tuple[int, int, str]],
                                          list[tuple[int, int]],
                                          dict[int, str]]:
    """Правки заголовков блоков, участки, которые уходят со страницы целиком,
    и номер слота → новое название (для ссылок «из блока 5» в прозе).

    Участки: шапка «Уровень …», абзац «Что прочитать сначала: …» (предпосылки
    переезжают в конец страницы ссылками с названиями тем) и блок «Цели».
    Заголовок «Источники» не трогается: по нему режется хвост аудита.
    """
    raw, lines = page.doc.raw, page.lines
    offs = line_offsets(lines)
    edits: list[tuple[int, int, str]] = []
    drops: list[tuple[int, int]] = []
    if page.head_line and LEAD_START_RE.match(page.head):
        drops.append(para_span(raw, offs[page.head_line - 1], page.head))
    elif page.head_line and vc.PREREQ_HEAD_RE.match(page.head):
        # Шапки нет (исходник уже без «Уровень …»): тогда предпосылки стоят
        # первым абзацем, и разбор считает шапкой их.
        drops.append(para_span(raw, offs[page.head_line - 1], page.head))
    if page.prereq_line:
        drops.append(para_span(raw, offs[page.prereq_line - 1], page.prereq))
    by_num: dict[int, str] = {}
    for b in page.blocks:
        new = block_display(b.title)
        if b.num >= 0 and new:
            by_num[b.num] = new
        if SOURCES_HEAD_RE.match(lines[b.line - 1]):
            continue
        start = offs[b.line - 1]
        if new is None:
            drops.append((start, offs[b.end] if b.end < len(lines) else len(raw)))
            continue
        line = lines[b.line - 1]
        if line != f"## {new}":
            edits.append((start, start + len(line), f"## {new}"))
    return edits, drops, by_num


def block_ref_edits(page: vc.Page, by_num: dict[int, str]
                    ) -> tuple[list[tuple[int, int, str]], list[str]]:
    """«из блока 5» → «из блока «Как это выглядит в коде»»; «блока
    «Механика»» → «блока «Как это работает»». Номер, которому блока нет,
    остаётся как есть и попадает в отчёт сборки."""
    spans = page.doc.prose_spans
    out: list[tuple[int, int, str]] = []
    lost: list[str] = []
    for m in BLOCK_REF_RE.finditer(spans):
        for num in REF_NUM_RE.finditer(m.group(1)):
            was = int(num.group(0))
            at = m.start(1) + num.start()
            if was in by_num:
                out.append((at, at + len(num.group(0)), f"«{by_num[was]}»"))
            else:
                lost.append(f"{page.id}: «{m.group(0)}»")
    lower = {k.lower(): v for k, v in NAME_REFS.items()}
    for m in NAME_REF_RE.finditer(spans):
        key = " ".join(m.group(1).split()).lower()
        new = lower.get(key)
        if new:
            out.append((m.start(), m.end(), f"«{new}»"))
    return out, lost


def overlaps(span: tuple[int, int], spans: list[tuple[int, int]]) -> bool:
    a, b = span
    return any(a < e and s < b for s, e in spans)


# ── разметка по строкам вне ограждённых блоков ───────────────────────────────

FENCE_OPEN_RE = re.compile(r"^[ \t]*(`{3,}|~{3,})")


def fence_flags(lines: list[str]) -> list[bool]:
    """Для каждой строки — внутри ли она ограждённого блока (вместе с самими
    строками ограды). Закрывает блок та же ограда не короче открывшей."""
    flags, cur = [], None
    for ln in lines:
        m = FENCE_OPEN_RE.match(ln)
        if cur is None:
            if m:
                cur = m.group(1)
                flags.append(True)
                continue
            flags.append(False)
        else:
            flags.append(True)
            if m and m.group(1)[0] == cur[0] and len(m.group(1)) >= len(cur) \
                    and not ln.strip()[len(m.group(1)):].strip():
                cur = None
    return flags


def indent(lines: list[str]) -> list[str]:
    return [("    " + ln) if ln.strip() else "" for ln in lines]


def fold_admon_heads(body: str) -> str:
    """Блок «Подумай, прежде чем читать» и «Чеклист для ревью» — свёрнутой
    врезкой вместо раздела: оба полезны, но не обязательны к чтению подряд."""
    lines = body.split("\n")
    flags = fence_flags(lines)
    out, i = [], 0
    while i < len(lines):
        ln = lines[i]
        title = ln[3:].strip() if ln.startswith("## ") and not flags[i] else ""
        if title not in ADMON_HEADS:
            out.append(ln)
            i += 1
            continue
        j = i + 1
        while j < len(lines) and not (lines[j].startswith("## ") and not flags[j]):
            j += 1
        inner = lines[i + 1:j]
        while inner and not inner[0].strip():
            inner.pop(0)
        while inner and not inner[-1].strip():
            inner.pop()
        kind, label = ADMON_HEADS[title]
        out += [f'??? {kind} "{label}"', ""] + indent(inner) + [""]
        i = j
    return "\n".join(out)


# Врезки: цитата, открытая меткой «**Примечание.**» и подобными, — на деле
# врезка (PLAYBOOK 7.6), и на странице она становится admonition своего типа.
# Метки — те, что встречаются в корпусе (2026-10-02: «Примечание» ×26, с
# уточнением через двоеточие ×6, «Предупреждение» ×6, «Глубже» ×2, «На
# собеседовании» ×1), плюс «Важно», «Внимание», «Совет» на вырост. Обычная
# цитата без метки остаётся цитатой.
CALLOUTS = {
    "примечание": ("!!!", "note"),
    "предупреждение": ("!!!", "warning"),
    "важно": ("!!!", "warning"),
    "внимание": ("!!!", "danger"),
    "совет": ("!!!", "tip"),
    "на собеседовании": ("!!!", "tip"),
    "глубже": ("???", "info"),
}
CALLOUT_RE = re.compile(
    r"^>[ \t]*\*\*(?P<label>" + "|".join(k.replace(" ", r"\s") for k in CALLOUTS)
    + r")(?::[ \t]*(?P<sub>[^*]+?))?[.:]\*\*[ \t]*(?P<rest>.*)$", re.I)


def callouts(body: str, report: dict | None = None) -> str:
    lines = body.split("\n")
    flags = fence_flags(lines)
    out, i = [], 0
    while i < len(lines):
        m = None if flags[i] else CALLOUT_RE.match(lines[i])
        if not m:
            out.append(lines[i])
            i += 1
            continue
        j = i + 1
        while j < len(lines) and lines[j].startswith(">") and not flags[j]:
            j += 1
        label = m.group("label")
        mark, kind = CALLOUTS[label.lower()]
        sub = (m.group("sub") or "").strip()
        title = (sub[0].upper() + sub[1:]) if sub else label[0].upper() + label[1:]
        inner = [m.group("rest")] + [re.sub(r"^>[ \t]?", "", ln)
                                     for ln in lines[i + 1:j]]
        out += [f'{mark} {kind} "{title}"', ""] + indent(inner)
        if report is not None:
            report["callouts"] += 1
        i = j
    return "\n".join(out)


# ── варианты ответов в «Проверь себя» ────────────────────────────────────────
#
# Вопрос с вариантами записан в исходниках строками «A. …», «B. …» — буква,
# точка, пробел. Markdown такого списка не знает: варианты либо слипались с
# вопросом в один абзац через жёсткий перевод строки, либо выпадали из
# нумерованного списка в простые абзацы — от прозы неотличимые. Сборка находит
# серию таких строк (два варианта и больше) и размечает каждый абзацем с
# бейджем-буквой: буква уезжает в <span class="quiz-letter">, абзац получает
# класс quiz-opt (attr_list), дальше работает CSS — висячий отступ и рамка.

QUIZ_OPT_RE = re.compile(r"^(?P<ind> {0,3})(?P<letter>[A-Z])\.[ \t]+(?P<text>\S.*)$")


def quiz_options(body: str, report: dict | None = None) -> str:
    """Серии строк «A. …», «B. …» → абзацы с бейджем-буквой (см. EXTRA_CSS).

    Серия — два и больше вариантов подряд: между ними могут стоять пустые
    строки и строки-продолжения (перенесённый текст варианта, он с отступом).
    Одиночная строка «A. …» в прозе — не серия и не трогается. Ограждённые
    блоки пропускаются: в коде «A.» — не вариант.
    """
    lines = body.split("\n")
    flags = fence_flags(lines)

    def option_at(i: int) -> re.Match | None:
        return None if flags[i] else QUIZ_OPT_RE.match(lines[i])

    # Серии: индексы строк-вариантов; между соседними — только пустые строки
    # или строки с отступом (продолжения предыдущего варианта).
    runs: list[list[int]] = []
    for i in range(len(lines)):
        if not option_at(i):
            continue
        if runs and all(not lines[k].strip() or lines[k][:1] in (" ", "\t")
                        for k in range(runs[-1][-1] + 1, i)):
            runs[-1].append(i)
        else:
            runs.append([i])
    runs = [run for run in runs if len(run) >= 2]
    if not runs:
        return body

    at = {i for run in runs for i in run}
    out: list[str] = []
    i = 0
    while i < len(lines):
        if i not in at:
            out.append(lines[i])
            i += 1
            continue
        m = option_at(i)
        ind, letter = m.group("ind"), m.group("letter")
        # Продолжения варианта: строки с отступом до первой пустой, до
        # следующего варианта или до конца абзаца.
        j = i + 1
        cont: list[str] = []
        while j < len(lines) and j not in at and lines[j].strip() \
                and lines[j][:1] in (" ", "\t"):
            cont.append(lines[j].rstrip())
            j += 1
        # Вариант — отдельный абзац: если перед ним текст (вопрос с жёстким
        # переводом строки), абзац надо оборвать пустой строкой.
        if out and out[-1].strip():
            out.append("")
        out.append(f'{ind}<span class="quiz-letter">{letter}</span> '
                   + m.group("text").rstrip())
        out += cont
        out.append(f"{ind}{{ .quiz-opt }}")
        out.append("")
        if report is not None:
            report["quiz_opts"] += 1
        i = j
        while i < len(lines) and not lines[i].strip():
            i += 1              # пустые строки между вариантами уже выданы
    return "\n".join(out)


def insert_stale_note(body: str) -> str:
    """Плашка 9.6 п. 20 — сразу под заголовком."""
    m = re.search(r"^# [^\n]*$", body, re.M)
    at = m.end() if m else 0
    return body[:at] + "\n\n" + STALE_NOTE + body[at:]


def insert_skip_note(body: str, condition: str) -> str:
    """Строка «можно отложить» (9.5 п. 10) — сразу под заголовком темы.

    Поле `skip_if` держит условие одной фразой, которое читатель проверяет на
    себе (SCHEMA § 3.1); маршрут от маркера не ветвится. Это совет читателю, а
    не след производства, поэтому со снятием шапки он остаётся: приглушённой
    строкой с засечкой слева.
    """
    m = re.search(r"^# [^\n]*$", body, re.M)
    at = m.end() if m else 0
    note = f"**Можно отложить, если** {condition}.\n{{ .topic-skip }}"
    return body[:at] + "\n\n" + note + body[at:]


# ── блок «Лаба»: строка запуска ──────────────────────────────────────────────
#
# Решение оператора 2026-10-01 (А8): строка `cd pilot/lab/…` была на одной
# странице из 37 с лабой, и читатель должен был сам догадаться, что каталог —
# это путь в репозитории рядом с `site/`. Сборка дописывает в конец блока
# «Лаба» команду перехода и команды прогона (из README лабы) со ссылкой на
# страницу лабы, где инструкция лежит целиком.

LAB_BLOCK_HEAD_RE = re.compile(
    r"^##[ \t]+(?:\d+\.[ \t]+)?(?:Лаба|Попробуй сам)[ \t]*$", re.M)
NEXT_HEAD_RE = re.compile(r"^## ", re.M)


def lab_run_edit(page_rel: str, raw: str,
                 labs: list[dict]) -> tuple[int, int, str] | None:
    """Точечная вставка в конец блока «Лаба»: как лабу запустить."""
    m = LAB_BLOCK_HEAD_RE.search(raw)
    if not m:
        return None
    nxt = NEXT_HEAD_RE.search(raw, m.end())
    at = nxt.start() if nxt else len(raw)
    parts = []
    for lab in labs:
        text = f"`cd {lab['path']}`"
        run = lab["run"]
        if run:
            text += ", затем `" + "`, `".join(run[:2]) + "`"
            if len(run) > 2:
                text += " и дальше по инструкции"
        text += (". Полная инструкция — на странице лабы "
                 f"[{lab['name']}]({link_to(page_rel, 'labs/' + lab['slug'] + '.md')}).")
        parts.append(text)
    para = "**Запуск — из корня репозитория.** " + "\n".join(parts)
    pad = "" if raw[:at].endswith("\n\n") else "\n"
    end = "\n\n" if nxt else "\n"
    return (at, at, pad + para + end)


def transform(page: vc.Page, page_rel: str, index: dict[str, str],
              abbr: dict[str, str], report: dict,
              nxt: vc.Page | None = None, today: date | None = None,
              gloss: tuple[re.Pattern, dict[str, str]] | None = None,
              sources_reg: dict[str, dict] | None = None,
              titles: dict[str, str] | None = None,
              labs: list[dict] | None = None) -> str:
    """Тема как страница сайта. Исходник не меняется — меняется копия."""
    raw = page.doc.raw
    edits: list[tuple[int, int, str]] = [(0, page.doc.front_end, front_block(page))]
    heads, drops, by_num = heading_edits(page)
    edits += heads
    refs, lost = block_ref_edits(page, by_num)
    edits += [e for e in refs if not overlaps(e[:2], drops)]
    report["block_refs"] += len(refs)
    report["block_refs_lost"] += lost

    for m in mdtext.FENCE_RE.finditer(raw):
        info = m.group("info").strip().lower()
        report["langs"].add(info.split()[0] if info else "text")
        # Листинг `text`, где строки команд начинаются с «$ », — сеанс
        # терминала: лексер `console` красит приглашение, а вывод оставляет
        # выводом. Текст листинга не меняется, меняется только подсветка.
        if info == "text" and re.search(r"^[ \t]*\$ ", m.group("body"), re.M):
            edits.append((m.start("info"), m.end("info"), "console"))
            report["langs"].add("console")
            report["console"] += 1
            continue
        if info != "mermaid":
            continue
        try:
            light, dark = render_diagrams.render(m.group("body"))
        except render_diagrams.Unavailable as exc:
            report["diagrams_failed"].append(f"{page.id}: {exc}")
            continue
        # Два варианта одной схемы — светлый и тёмный; метки `#only-light` и
        # `#only-dark` в адресе понимает движок темы: показывает вариант
        # активной палитры, и переключатель темы меняет схему без перезагрузки.
        target_light = link_to(page_rel, f"assets/diagrams/{light.name}")
        target_dark = link_to(page_rel, f"assets/diagrams/{dark.name}")
        # Текстовая замена схемы — абзац «Описание схемы» под ней, он предписан
        # 7.2; в `alt` идёт короткая подпись, чтобы читалка не пересказывала
        # картинку дважды.
        # Ширина из нарисованного SVG (`max-width` в его style): у `<img>` с
        # SVG `width="100%"` своей ширины нет, и узкую схему растягивало на
        # всю колонку, а шрифт в ней — вдвое. Шире колонки не станет:
        # `max-width: 100%` у картинок задаёт тема.
        natural = re.search(r"max-width:\s*([\d.]+)px", light.read_text()[:4000])
        width = f' width="{round(float(natural.group(1)))}"' if natural else ""
        alt = "Схема (описание — в абзаце под ней)"
        edits.append((m.start(), m.end(),
                      f"![{alt}]({target_light}#only-light){{ .diagram{width} }}"
                      f"![{alt}]({target_dark}#only-dark){{ .diagram{width} }}"))
        report["diagrams"] += 1
        report["diagram_files"].update((light.name, dark.name))

    for m in mdtext.CODE_SPAN_RE.finditer(page.doc.prose_spans):
        target_id = m.group(2).strip()
        if target_id == page.id or target_id not in index:
            continue
        # Подпись ссылки — название темы, а не её идентификатор (WCAG 2.4.4,
        # решение оператора 2026-10-01, А1): из «`idor`» назначение ссылки не
        # читается, из «Горизонтальная эскалация, IDOR» — читается.
        if overlaps((m.start(), m.end()), drops):
            continue
        label = (titles or {}).get(target_id) or m.group(2).strip()
        edits.append((m.start(), m.end(),
                      f"[{label}]({link_to(page_rel, index[target_id])})"))
        report["links"] += 1

    if labs:
        run_edit = lab_run_edit(page_rel, raw, labs)
        if run_edit:
            edits.append(run_edit)
            report["lab_run"] += 1

    if gloss is not None:
        edits += glossary_links(page, page_rel, raw, gloss, edits, report,
                                drops=drops)

    # Снятые участки — пустой заменой; правки внутри них уже отброшены.
    edits += [(a, b, "") for a, b in drops]
    body = apply_edits(raw, edits)
    body = fold_admon_heads(body)
    body = callouts(body, report)
    body = quiz_options(body, report)
    skip_if = one_line(str(page.front.get("skip_if") or "")).removesuffix(".")
    if skip_if:
        body = insert_skip_note(body, skip_if)
        report["skip"] += 1
    if today is not None:
        state = review_elapsed(page.front, today)
        if state and state[0] > 2 * state[1]:
            body = insert_stale_note(body)
            report["stale"] += 1

    # Хвост с «Источников» и до конца — аппарат аудита, а не текст страницы.
    # Прежде чем резать, из хвоста забираются определения сносок: метки `[^N]`
    # остаются в прозе, и без определения движок оставляет литерал как есть.
    cut = SOURCES_HEAD_RE.search(body)
    footnotes: list[str] = []
    if cut:
        tail_text = body[cut.start():]
        body = body[:cut.start()]
        defs, items = footnote_defs(tail_text), source_items(tail_text)
        seen: set[str] = set()
        for m in FN_REF_RE.finditer(prose_only(body)):
            ref = m.group(1)
            if ref in seen:
                continue
            seen.add(ref)
            if ref in defs:
                footnotes.append(f"[^{ref}]: {defs[ref]}")
            elif ref in items:
                footnotes.append(f"[^{ref}]: {synth_def(items[ref])}")
                report["footnotes_synth"] += 1
            else:
                report["footnotes_missing"].append(f"{page.id}: [^{ref}]")

    # «Что почитать дальше» — решение оператора 2026-10-02: предпосылки темы
    # (раньше — строка «Что прочитать сначала» под заголовком) и первоисточники
    # (решение 2026-10-01, реестр RN-13) одним разделом в конце статьи.
    # Срезанный хвост аудита он не возвращает: блок собирается из полей
    # `prerequisites` и `sources` темы и реестра, а не из текста «Источников».
    block, n_sources = read_more(page, page_rel, index, titles or {},
                                 sources_reg or {})
    if block:
        body = body.rstrip("\n") + "\n\n" + block + "\n"
        report["primary_sources"] += 1 if n_sources else 0
        report["primary_links"] += n_sources

    # «Дальше» — ссылка на следующую тему маршрута; генерируется здесь, а не
    # пишется автором (решение оператора 2026-08-31). У последней темы нет.
    if nxt is not None:
        body = (body.rstrip("\n")
                + "\n\n## Дальше\n\n"
                + f"[{one_line(nxt.front.get('title') or nxt.id)}]"
                  f"({link_to(page_rel, index[nxt.id])})\n")

    tail = [body.rstrip("\n"), ""]
    if footnotes:
        report["footnotes"] += len(footnotes)
        tail += footnotes + [""]
    # Аббревиатуры считаются по всей странице, включая перенесённые сноски:
    # раскрытие по наведению должно работать и в тексте сноски.
    here = used_abbr("\n".join(tail), abbr)
    if here:
        report["abbr"] += len(here)
        tail.append("")
        for key in sorted(here):
            tail.append(f"*[{key}]: {here[key]}")
    tail += [""]
    return "\n".join(tail)


# ── сгенерированные страницы ─────────────────────────────────────────────────


# ASCII-баннер главной (figlet, шрифт standard). Рисуется моноширинным и
# зелёным; для читалки он скрыт — заголовок страницы стоит обычным `h1` под ним.
BANNER = r"""    _                 ____
   / \   _ __  _ __  / ___|  ___  ___
  / _ \ | '_ \| '_ \ \___ \ / _ \/ __|
 / ___ \| |_) | |_) | ___) |  __/ (__
/_/   \_\ .__/| .__/ |____/ \___|\___|
        |_|   |_|"""


def html_href(page_rel: str, target_md: str) -> str:
    """Ссылка для сырого HTML: движок переписывает `.md` → `.html` только в
    markdown-ссылках, в разметке карточек адрес нужен готовым."""
    return link_to(page_rel, target_md).removesuffix(".md") + ".html"


def page_index(ctx: vc.Ctx, pages: list[vc.Page], index: dict[str, str],
               today: date) -> str:
    """Главная: баннер, одна фраза о гайдбуке и карточки этапов.

    Решение оператора 2026-10-02: главная — вход в книгу, а не её паспорт.
    Таблица уровней, сумма минут, дата сборки и пояснения о скоупе с неё
    убраны: это следы производства. `today` остаётся в подписи ради
    совместимости вызова и на страницу не печатается.
    """
    del today
    by_stage: dict[str, list[vc.Page]] = {}
    for p in pages:
        by_stage.setdefault(str(p.front.get("stage")), []).append(p)

    cards = []
    for stage in ctx.tax["stages"]:
        group = by_stage.get(stage["slug"], [])
        if stage.get("excluded") or not group:
            continue
        first = group[0]
        n = len(group)
        first_title = html.escape(short_title(one_line(first.front.get("title"))))
        cards.append(
            f'<a class="stage-card" href="{html_href("index.md", index[first.id])}">\n'
            f'<span class="stage-card__num">этап {int(stage["num"])}</span>\n'
            f'<span class="stage-card__title">{html.escape(stage["title"])}</span>\n'
            f'<span class="stage-card__meta">{n} '
            f'{plural(n, ("тема", "темы", "тем"))}</span>\n'
            f'<span class="stage-card__go">начать с «{first_title}»</span>\n'
            f'</a>')

    total = len(pages)
    return f"""---
title: Начало
description: Учебник по прикладной безопасности — как устроены уязвимости веб-приложений, как их находят и как от них защищаются.
hide:
  - navigation
  - toc
---

{GENERATED}

<div class="hero" markdown="0">
<pre class="hero__banner" aria-hidden="true">{html.escape(BANNER)}</pre>
<p class="hero__prompt"><span class="hero__ps">$</span> cat README<span class="hero__cursor" aria-hidden="true"></span></p>
</div>

# AppSec-гайдбук

Как ломаются веб-приложения и как это увидеть в чужом коде: {total} статей —
от того, как браузер говорит с сервером, до SAST в конвейере. Каждая статья
объясняет механизм своими словами, показывает дефект в коде, его починку и
способ убедиться, что починка работает.

<div class="stage-grid" markdown="0">
{chr(10).join(cards)}
</div>

## Как читать

Этапы идут по порядку: каждый следующий опирается на предыдущие. Внутри статьи
сначала идёт короткий ответ («Если коротко»), потом механизм, атака, код и
защита; в конце — «Проверь себя» и ссылка на следующую статью. Под рукой —
[карта тем]({link_to('index.md', 'map.md')}),
[лабы]({link_to('index.md', 'labs.md')}) ({len(ctx.labs)} практических работ,
запускаются локально) и [глоссарий]({link_to('index.md', 'glossary.md')}).

!!! warning "Только свои системы"
    Гайд учит защите. Приёмы из статей применяйте к собственным системам и
    учебным стендам; разборы уязвимостей ведутся на локальных лабах.

"""


def page_map(ctx: vc.Ctx, pages: list[vc.Page], index: dict[str, str],
             report: dict, titles: dict[str, str],
             topic_labs: dict[str, list[dict]]) -> str:
    out = [f"""---
title: Карта тем
description: Все темы гайдбука с уровнем, временем, предпосылками и лабами.
---

{GENERATED}

# Карта тем

Порядок внутри этапа тот же, что в оглавлении: тема стоит после тех, на которых
держится. Уровень задаёт подробность, а не самодостаточность: на любом уровне
механизм объяснён своими словами и со своим примером.

Столбец «Требует» и есть карта связей: он называет темы, без которых эта не
читается. Столбец «Лаба» ведёт на практическую работу темы — цель, файлы и
запуск разобраны на странице лабы.
"""]

    by_stage: dict[str, list[vc.Page]] = {}
    for p in pages:
        by_stage.setdefault(str(p.front.get("stage")), []).append(p)

    for stage in ctx.tax["stages"]:
        if stage.get("excluded"):
            continue
        group = by_stage.get(stage["slug"], [])
        num = int(stage["num"])
        pending = [(tid, meta) for tid, meta in sorted(ctx.plan.items())
                   if meta["stage"] == num and not meta["excluded"]
                   and tid not in {p.front.get("plan_id") for p in group}]
        if not group and not pending:
            continue
        out.append(f"## Этап {num}. {stage['title']}\n")
        if group:
            out.append("| Тема | Уровень | Мин | Требует | Лаба |")
            out.append("|---|---|---|---|---|")
            for p in group:
                # Подпись предпосылки — название темы, а не идентификатор (А1);
                # тема вне корпуса остаётся кодом: сослаться не на что.
                prereqs = ", ".join(
                    f"[{titles[q]}]({link_to('map.md', index[q])})" if q in index
                    else f"`{q}`"
                    for q in (p.front.get("prerequisites") or [])) or "—"
                lab_cell = ", ".join(
                    f"[{short_title(lab['name'])}]"
                    f"({link_to('map.md', 'labs/' + lab['slug'] + '.md')})"
                    for lab in topic_labs.get(p.id, [])) or "—"
                out.append(
                    f"| [{one_line(p.front.get('title'))}]"
                    f"({link_to('map.md', index[p.id])}) "
                    f"| {p.depth} | {p.front.get('time_min')} "
                    f"| {prereqs} | {lab_cell} |")
            out.append("")
        if pending:
            out.append("Ещё не написаны:\n")
            for _, meta in pending:
                out.append(f"- {one_line(meta['title'])}")
            out.append("")
    return "\n".join(out)


def page_glossary(glossary: dict, index: dict[str, str],
                  titles: dict[str, str]) -> str:
    """Тот же глоссарий, что `GLOSSARY.md`, только ссылки ведут на страницы.

    `gen_glossary` подписывает ссылки «вводится в …» идентификатором темы;
    здесь подпись заменяется названием темы (решение оператора 2026-10-01,
    А1) — из текста ссылки должно читаться, куда она ведёт.
    """
    link = {tid: link_to("glossary.md", rel) for tid, rel in index.items()}
    text = gen_glossary.render(glossary, link=link)
    for tid, href in link.items():
        if tid in titles:
            text = text.replace(f"[{tid}]({href})", f"[{titles[tid]}]({href})")
    # У страницы своя мета: заголовок для оглавления и описание для поиска.
    return ("---\ntitle: Глоссарий\ndescription: Термины гайдбука; "
            "одно написание термина на весь сайт.\n---\n\n" + text)


def page_tags(ctx: vc.Ctx) -> str:
    rows = "\n\n".join(f"`{tag}`\n:   {meaning}"
                       for tag, meaning in sorted(ctx.tax["tags"].items()))
    return f"""---
title: Теги
description: Фасеты каталога: тема попадает в несколько тегов, этап у неё один.
---

{GENERATED}

# Теги

Тег — фасет, а не рубрика: этап у темы один и он же её дом в оглавлении, а тегов
у темы несколько. Словарь тегов закрытый: новых тегов на страницах не заводится,
и одно и то же всегда названо одним словом.

<!-- material/tags -->

## Что значит каждый тег

{rows}
"""


def page_attributions() -> str:
    """Правовой слой сайта: лицензия гайдбука и условия чужих материалов.

    Страница предписана PLAYBOOK 10.1 п. 4: формулировка про OWASP со ссылкой
    на лицензию и указанием факта изменений, копирайт-нотис MITRE и отметка
    про NIST. Те же две лицензии записаны в `LICENSE` в корне репозитория.
    """
    return f"""---
title: Атрибуции и лицензии
description: Лицензии гайдбука и условия использованных в нём чужих материалов.
---

{GENERATED}

# Атрибуции и лицензии

## Лицензия гайдбука

Текст гайдбука опубликован по лицензии [CC BY-SA
4.0](https://creativecommons.org/licenses/by-sa/4.0/): его можно копировать и
адаптировать с указанием авторства и на тех же условиях. Код примеров и
инструменты сборки — по лицензии [MIT](https://opensource.org/license/mit):
их можно использовать без ограничений, сохраняя уведомление об авторских
правах.

## Использованные материалы

- **OWASP.** Материалы OWASP опубликованы под [CC BY-SA
  4.0](https://creativecommons.org/licenses/by-sa/4.0/); переводы и адаптации
  помечаются полем `derived_from` во frontmatter темы. Оригиналы — © OWASP
  Foundation, перевод и изменения сделаны автором гайдбука.
- **MITRE CWE.** CWE™ — товарный знак The MITRE Corporation; условия
  использования — на [cwe.mitre.org](https://cwe.mitre.org/about/termsofuse.html).
  Упоминание каталога не означает одобрения со стороны MITRE.
- **NIST.** Публикации NIST (SP 800-61r3 и другие) — общественное достояние
  в США и используются свободно.
- **PortSwigger.** Все права защищены; в гайде — только ссылки на материалы
  Web Security Academy, без пересказа лабораторных заданий.
- **JetBrains Mono.** Шрифт листингов и кода; файлы лежат в самой сборке,
  в сеть сайт за ними не ходит. © 2020 The JetBrains Mono Project Authors;
  лицензия [SIL Open Font License 1.1](https://openfontlicense.org), её текст —
  в репозитории рядом со шрифтами (`tools/vendor/fonts/OFL.txt`).
- **Press Start 2P.** Пиксельный шрифт заголовков; файл лежит в той же
  папке сборки. © 2012 CodeMan38; лицензия та же — [SIL Open Font License
  1.1](https://openfontlicense.org), текст общий с JetBrains Mono
  (`tools/vendor/fonts/OFL.txt`).
"""


def cwe_release() -> str:
    """Выпуск каталога CWE из записи `cwe-taxonomy` реестра источников."""
    for src in (vc.load_yaml(vc.SOURCES_YAML).get("sources") or []):
        if isinstance(src, dict) and src.get("id") == "cwe-taxonomy":
            return str(src.get("version_or_date") or "").replace("Version ", "")
    return ""


def natural_key(text: str) -> list:
    """Ключ сортировки, в котором `CWE-90` идёт перед `CWE-1004`.

    Идентификаторы каталогов — смесь букв и чисел (`CWE-1004`, `v5.0-3.3.1`,
    `A04:2025`), и по строке они сортируются не так, как их читают: `1004`
    оказывается раньше `295`. Числовые куски сравниваются числами.
    """
    return [int(part) if part.isdigit() else part
            for part in re.split(r"(\d+)", text)]


def page_mapping(ctx: vc.Ctx, pages: list[vc.Page], index: dict[str, str]) -> str:
    """Соответствие внешним каталогам — отдельной страницей, а не рубрикой.

    Свод 9.6 п. 24 запрещает строить оглавление по номерам OWASP Top 10: за год
    номер переезжает, а тема — нет, и рубрикатор пришлось бы перекладывать
    вслед за чужой нумерацией. Соответствие держится здесь, и держится машинно:
    страница собрана из полей `cwe`, `asvs`, `wstg` и `owasp` во frontmatter,
    поэтому разойтись с темами не может. До этой страницы требование висело
    неисполненным (`journal/WRITE-REVIEW-2.md` § 8 п. 12, находка Ф-32).
    """
    order = {p.id: (str(p.front.get("stage")), int(p.front.get("order") or 0))
             for p in pages}

    def section(field: str, title: str, label, empty: str) -> list[str]:
        groups: dict[str, list[vc.Page]] = {}
        for p in pages:
            for value in (p.front.get(field) or []):
                groups.setdefault(str(value), []).append(p)
        out = [f"## {title}\n"]
        if not groups:
            return out + [empty, ""]
        out += ["| Идентификатор | Темы |", "|---|---|"]
        for ident in sorted(groups, key=natural_key):
            links = ", ".join(
                f"[{short_title(q.front.get('title'))}]"
                f"({link_to('mapping.md', index[q.id])})"
                for q in sorted(groups[ident], key=lambda q: order[q.id]))
            out.append(f"| {label(ident)} | {links} |")
        return out + [""]

    # Выпуск каталога берётся из реестра источников: со страниц тем он убран
    # вместе с остальным «проверено на:» (решение оператора 2026-08-24), а
    # запись `cwe-taxonomy` — то место, где это сведение и должно жить.
    cwe_note = (f"Номера сверены по выпуску каталога **{cwe_release()}**."
                if cwe_release() else
                "Выпуск каталога — запись `cwe-taxonomy` реестра источников.")

    out = [f"""---
title: Маппинг-индекс
description: Номер внешнего каталога — темы, которые его разбирают.
---

{GENERATED}

# Маппинг-индекс

Оглавление гайдбука построено по этапам, а не по номерам внешних каталогов:
номер переезжает между выпусками, а тема остаётся на месте.
Обратный ход — от номера к теме — держит эта страница. Она собирается из самих
тем, поэтому расходиться с ними ей нечем.

Номер в таблице означает, что тема разбирает названную им слабость или
требование, а не что тема исчерпывает его целиком.
"""]
    out += section("cwe", "CWE", lambda v: f"`{v}`",
                   f"Ни одна тема не называет номера CWE. {cwe_note}")
    out.append(f"{cwe_note}\n")
    out += section("asvs", "ASVS", lambda v: f"`ASVS {v}`",
                   "Ни одна тема не называет требований ASVS.")
    out += section("wstg", "WSTG", lambda v: f"`{v}`",
                   "Ни одна тема не называет разделов WSTG.")
    out += section("owasp", "OWASP Top 10", lambda v: f"`{v}`",
                   "Ни одна тема не отнесена к категории Top 10: категория "
                   "проставляется там, где разбор ведётся от неё.")

    silent = [p for p in sorted(pages, key=lambda q: order[q.id])
              if not any(p.front.get(f) for f in ("cwe", "asvs", "wstg", "owasp"))]
    if silent:
        names = ", ".join(f"[{short_title(p.front.get('title'))}]"
                          f"({link_to('mapping.md', index[p.id])})" for p in silent)
        out += ["## Темы без внешних идентификаторов\n", names, ""]
    return "\n".join(out)


def review_months(seen: date, today: date) -> int:
    """Календарные месяцы между датами. Формула та же, что у линтера
    (`tools/validate_content.py`, C-FM-REVIEW): `review_interval` задан в
    месяцах (`SCHEMA.md`, 9.6 п. 20), и единицы у сборки с проверкой одни."""
    return (today.year - seen.year) * 12 + today.month - seen.month


def review_elapsed(front: dict, today: date) -> tuple[int, int] | None:
    """(Месяцев с ревизии, интервал) по frontmatter; None, если ревизии нет."""
    reviewed = front.get("reviewed")
    interval = int(front.get("review_interval") or 0)
    if not reviewed or not interval:
        return None
    seen = reviewed if isinstance(reviewed, date) else date.fromisoformat(str(reviewed))
    return review_months(seen, today), interval


STALE_NOTE = """!!! warning "Может быть устаревшим"
    Материал этой темы давно не пересматривался и может быть устаревшим:
    версии инструментов и номера стандартов сверяйте с первоисточниками,
    прежде чем применять описанное.
"""


def author_notes(ctx: vc.Ctx, pages: list[vc.Page], today: date) -> list[str]:
    """Авторская бухгалтерия: просрочка ревизии и перекос объёма.

    До 2026-08-26 это была страница сайта «Обслуживание». Решением оператора она
    убрана: сроки ревизии и состояние тем — журнал производства, а читателю на
    них смотреть незачем (тем же решением 4.1 убрало статус из шапки темы).
    Данные не потеряны — они лежат во frontmatter, и сборка печатает их тому,
    кто её запустил. Читатель видит только плашку 9.6 п. 20, когда просрочка
    больше интервала вдвое.
    """
    overdue, on_time = [], 0
    for p in pages:
        state = review_elapsed(p.front, today)
        if state is None:
            continue
        months, interval = state
        if months > interval:
            overdue.append((months - interval, p.id))
        else:
            on_time += 1

    notes = []
    if overdue:
        overdue.sort(reverse=True)
        notes.append(f"ревизия просрочена у {len(overdue)} тем из "
                     f"{len(overdue) + on_time} с датой: " + head_tail(
                         f"{tid} на {late} мес." for late, tid in overdue))
    else:
        notes.append(f"ревизия в срок у всех {on_time} тем с датой")

    skew = []
    for p in pages:
        _, _, core = wordcount.counts(p.doc.raw)
        lo, hi = ctx.tax["depths"][p.depth]["words"]
        if not lo <= core <= hi:
            skew.append(f"{p.id} {core} против {lo}\u2013{hi}")
    notes.append(f"объём вне нормы уровня у {len(skew)} тем из {len(pages)}"
                 + (": " + head_tail(skew) if skew else ""))
    return notes


def head_tail(items, keep: int = 5) -> str:
    """Первые `keep` штук через запятую; остальные — числом, чтобы влезло в строку."""
    items = list(items)
    shown = ", ".join(items[:keep])
    return shown if len(items) <= keep else f"{shown} и ещё {len(items) - keep}"


EXTRA_CSS = """/* Собрано `tools/build_site.py`; правки — в сборщик, не сюда. */

/* ── палитра ─────────────────────────────────────────────────────────────────
   Решение оператора 2026-10-02: тёмная «хакерская» тема по умолчанию, светлая
   — переключателем. Фон почти чёрный, а не #000, и основной текст светло-серый,
   а не насыщенный зелёный: светлое на чистом чёрном и #00ff00 сплошным текстом
   дают ореолы (halation) у читателей с астигматизмом. Зелёный — только акцент:
   заголовки, ссылки, активный пункт меню, маркеры списков, приглашение `$`,
   полоса у листингов. Контраст текста, ссылок и токенов подсветки — не ниже
   4,5:1 в обеих темах; его меряет `tools/check_site.mjs` по getComputedStyle. */
[data-md-color-scheme="slate"] {
  --gb-bg: #0d1117;
  --gb-surface: #161b22;
  --gb-surface-2: #1c2128;
  --gb-border: #30363d;
  --gb-text: #c9d1d9;
  --gb-muted: #8b949e;
  --gb-green: #3fb950;
  --gb-green-hi: #7ee787;
  --gb-green-soft: rgba(63, 185, 80, 0.14);
  --gb-head: #7ee787;

  --md-hue: 215;
  --md-default-bg-color: var(--gb-bg);
  --md-default-bg-color--light: rgba(13, 17, 23, 0.7);
  --md-default-bg-color--lighter: rgba(13, 17, 23, 0.3);
  --md-default-bg-color--lightest: rgba(13, 17, 23, 0.12);
  --md-default-fg-color: var(--gb-text);
  --md-default-fg-color--light: var(--gb-muted);
  --md-default-fg-color--lighter: rgba(139, 148, 158, 0.55);
  --md-default-fg-color--lightest: rgba(139, 148, 158, 0.18);
  --md-primary-fg-color: var(--gb-surface);
  --md-primary-fg-color--light: var(--gb-surface-2);
  --md-primary-fg-color--dark: var(--gb-bg);
  --md-primary-bg-color: var(--gb-text);
  --md-primary-bg-color--light: var(--gb-muted);
  --md-accent-fg-color: var(--gb-green-hi);
  --md-accent-fg-color--transparent: var(--gb-green-soft);
  --md-accent-bg-color: var(--gb-bg);
  --md-typeset-color: var(--gb-text);
  --md-typeset-a-color: var(--gb-green);
  --md-typeset-mark-color: rgba(187, 128, 9, 0.4);
  --md-typeset-table-color: var(--gb-border);
  --md-typeset-table-color--light: rgba(48, 54, 61, 0.35);
  --md-code-bg-color: var(--gb-surface);
  --md-code-fg-color: var(--gb-text);
  --md-code-hl-color: #2f81f7;
  --md-code-hl-color--light: rgba(47, 129, 247, 0.15);
  --md-code-hl-keyword-color: #ff7b72;
  --md-code-hl-string-color: #a5d6ff;
  --md-code-hl-number-color: #79c0ff;
  --md-code-hl-special-color: #ffa198;
  --md-code-hl-function-color: #d2a8ff;
  --md-code-hl-constant-color: #79c0ff;
  --md-code-hl-name-color: var(--gb-text);
  --md-code-hl-operator-color: #ff7b72;
  --md-code-hl-punctuation-color: var(--gb-text);
  --md-code-hl-comment-color: var(--gb-muted);
  --md-code-hl-generic-color: var(--gb-muted);
  --md-code-hl-variable-color: #ffa657;
  --md-admonition-bg-color: var(--gb-bg);
  --md-admonition-fg-color: var(--gb-text);
  --md-footer-bg-color: var(--gb-surface);
  --md-footer-bg-color--dark: var(--gb-bg);
  --md-footer-fg-color: var(--gb-text);
  --md-footer-fg-color--light: var(--gb-muted);
  --md-footer-fg-color--lighter: var(--gb-muted);
  --md-shadow-z1: 0 0 0 1px var(--gb-border);
  --md-shadow-z2: 0 0 0 1px var(--gb-border), 0 0.2rem 0.6rem rgba(0, 0, 0, 0.4);
}
[data-md-color-scheme="default"] {
  --gb-bg: #ffffff;
  --gb-surface: #f6f8fa;
  --gb-surface-2: #eef1f4;
  --gb-border: #d0d7de;
  --gb-text: #1f2328;
  --gb-muted: #59636e;
  --gb-green: #1a7f37;
  --gb-green-hi: #116329;
  --gb-green-soft: rgba(26, 127, 55, 0.1);
  --gb-head: #116329;

  --md-default-bg-color: var(--gb-bg);
  --md-default-fg-color: var(--gb-text);
  --md-default-fg-color--light: var(--gb-muted);
  --md-default-fg-color--lighter: rgba(89, 99, 110, 0.55);
  --md-default-fg-color--lightest: rgba(89, 99, 110, 0.15);
  --md-primary-fg-color: var(--gb-surface);
  --md-primary-fg-color--light: var(--gb-surface-2);
  --md-primary-fg-color--dark: var(--gb-border);
  --md-primary-bg-color: var(--gb-text);
  --md-primary-bg-color--light: var(--gb-muted);
  --md-accent-fg-color: var(--gb-green-hi);
  --md-accent-fg-color--transparent: var(--gb-green-soft);
  --md-accent-bg-color: var(--gb-bg);
  --md-typeset-color: var(--gb-text);
  --md-typeset-a-color: var(--gb-green);
  --md-typeset-table-color: var(--gb-border);
  --md-code-bg-color: var(--gb-surface);
  --md-code-fg-color: var(--gb-text);
  --md-code-hl-keyword-color: #cf222e;
  --md-code-hl-string-color: #0a3069;
  --md-code-hl-number-color: #0550ae;
  --md-code-hl-special-color: #a40e26;
  --md-code-hl-function-color: #6639ba;
  --md-code-hl-constant-color: #0550ae;
  --md-code-hl-name-color: var(--gb-text);
  --md-code-hl-operator-color: #cf222e;
  --md-code-hl-punctuation-color: var(--gb-text);
  --md-code-hl-comment-color: var(--gb-muted);
  --md-code-hl-generic-color: var(--gb-muted);
  --md-code-hl-variable-color: #953800;
  --md-admonition-bg-color: var(--gb-bg);
  --md-admonition-fg-color: var(--gb-text);
  --md-footer-bg-color: var(--gb-surface);
  --md-footer-bg-color--dark: var(--gb-surface-2);
  --md-footer-fg-color: var(--gb-text);
  --md-footer-fg-color--light: var(--gb-muted);
  --md-footer-fg-color--lighter: var(--gb-muted);
  --md-shadow-z1: 0 0 0 1px var(--gb-border);
  --md-shadow-z2: 0 0 0 1px var(--gb-border), 0 0.2rem 0.6rem rgba(31, 35, 40, 0.12);
}

/* ── шрифты ──────────────────────────────────────────────────────────────────
   Три роли, три шрифта. Заголовки — Press Start 2P: пиксельный, по решению
   оператора 2026-10-02 (© 2012 CodeMan38, OFL 1.1 — текст лицензии общий с
   JetBrains Mono: `tools/vendor/fonts/OFL.txt`). Код и «хром» — JetBrains Mono
   (OFL 1.1). Файлы обоих — в `assets/fonts/`, в сеть сайт не ходит. Тело
   статьи — пропорциональный системный шрифт: моноширинный текст абзацами
   читается медленнее. Переменная `--md-code-font` — первое звено цепочки
   `--md-code-font-family` темы. */
@font-face {
  font-family: "JetBrains Mono";
  src: url("fonts/JetBrainsMono-Regular.woff2") format("woff2");
  font-weight: 400;
  font-style: normal;
  font-display: swap;
}
@font-face {
  font-family: "JetBrains Mono";
  src: url("fonts/JetBrainsMono-Bold.woff2") format("woff2");
  font-weight: 700;
  font-style: normal;
  font-display: swap;
}
@font-face {
  font-family: "Press Start 2P";
  src: url("fonts/PressStart2P-Regular.woff2") format("woff2");
  font-weight: 400;
  font-style: normal;
  font-display: swap;
}
:root {
  --md-code-font: "JetBrains Mono";
  /* Цепочка задана явно: `--md-code-font-family` тема объявляет на `body`, и
     на `:root` ссылка на неё пуста. */
  --gb-mono: "JetBrains Mono", ui-monospace, SFMono-Regular, Menlo, Consolas,
    "Liberation Mono", monospace;
  /* Заголовочный шрифт с откатом на моноширинный: если woff2 не доехал,
     страница остаётся в прежнем виде, а не в системном sans. */
  --gb-display: "Press Start 2P", var(--gb-mono);
}
.md-typeset h4,
.md-header__title, .md-nav__title, .md-footer__title, .md-path,
.md-typeset .admonition-title, .md-typeset summary {
  font-family: var(--gb-mono);
  font-feature-settings: "liga" 0, "calt" 0;
}
/* У Press Start 2P один градус: жирного нет, и синтетический жирный размыл
   бы пиксели — поэтому `font-weight: 400` в обеих темах. Шрифт очень широкий
   и высокий: кегль урезан против умолчания темы, интерлиньяж увеличен —
   длинные русские заголовки переносятся, и строки не должны налезать друг
   на друга. Кегль в rem, а не в em: размер текста статьи меняется ступенями
   медиазапросов, а пропорции заголовков держатся от корня. */
.md-typeset h1, .md-typeset h2, .md-typeset h3 {
  font-family: var(--gb-display);
  font-weight: 400;
  letter-spacing: normal;
  line-height: 1.6;
  overflow-wrap: break-word;
}
.md-typeset h1 { font-size: 1rem; }
.md-typeset h2 { font-size: 0.75rem; }
.md-typeset h3 { font-size: 0.65rem; }

/* Лигатур в коде быть не должно: стрелка вместо `->` — это уже другой текст. */
.md-typeset code,
.md-typeset kbd,
.md-typeset pre {
  font-variant-ligatures: none;
  font-feature-settings: "liga" 0, "calt" 0;
}

/* ── каркас ──────────────────────────────────────────────────────────────── */
.md-header {
  border-bottom: 1px solid var(--gb-border);
  box-shadow: none;
}
.md-header__title { color: var(--gb-head); }
.md-header__button.md-logo { color: var(--gb-green); }
.md-footer { border-top: 1px solid var(--gb-border); }
.md-footer__link:hover .md-footer__title,
.md-footer__link:focus .md-footer__title { color: var(--gb-green-hi); }
.md-search__form { background-color: var(--gb-bg);
                   box-shadow: 0 0 0 1px var(--gb-border); }
.md-search__input, .md-search__input::placeholder,
.md-search__icon { color: var(--gb-muted); }
.md-search__input { color: var(--gb-text); }

/* Меню: активный пункт — зелёный с засечкой слева. */
.md-nav__link--active,
.md-nav__item .md-nav__link--active {
  color: var(--gb-green);
  font-weight: 700;
}
.md-nav--primary .md-nav__link--active {
  box-shadow: inset 2px 0 0 var(--gb-green);
  padding-left: 0.4rem;
  margin-left: -0.4rem;
}
.md-nav__link:hover, .md-nav__link:focus { color: var(--gb-green-hi); }
/* Прилипший заголовок меню («AppSec-гайдбук», «Содержание»): пункты меню
   прокручиваются под ним. Правила адресованы с контекстом `--primary`/
   `--secondary`, иначе проигрывают таким же по специфичности правилам движка.
   Тень движка (0 0 .4rem .4rem) растекалась ниже текста заголовка
   полупрозрачной кромкой, и припаркованный под заголовком пункт («Этап 0. …»)
   просвечивал сквозь неё срезанным пополам. Без тени: фон заголовка сплошной,
   что ушло под него — скрыто целиком, что ниже — видно целиком. */
.md-nav--primary .md-nav__title, .md-nav--secondary .md-nav__title {
  color: var(--gb-muted);
  background: var(--gb-bg);
  box-shadow: none;
}

/* Хлебные крошки (А6): где я, на узком экране тоже. */
.md-path { font-size: 0.62rem; color: var(--gb-muted); }
.md-path__link:hover { color: var(--gb-green-hi); }

/* ── статья ─────────────────────────────────────────────────────────────── */
.md-typeset { color: var(--gb-text); }
.md-typeset h1, .md-typeset h2, .md-typeset h3, .md-typeset h4 {
  color: var(--gb-head);
}
/* Кегль, градус и интерлиньяж заголовков — в блоке «шрифты» выше: они
   свойства выбранного шрифта, а не статьи. */
.md-typeset h2 {
  border-bottom: 1px solid var(--gb-border);
  padding-bottom: 0.25em;
}
/* Решётки перед заголовками — разметка markdown как украшение, а не номер:
   псевдоэлемент в текст заголовка и в оглавление не попадает. */
.md-typeset h2::before { content: "## "; color: var(--gb-muted); }
.md-typeset h3::before { content: "### "; color: var(--gb-muted); }
.md-typeset a { color: var(--gb-green); text-underline-offset: 0.15em; }
.md-typeset a:hover, .md-typeset a:focus { color: var(--gb-green-hi);
                                           text-decoration: underline; }
.md-typeset .headerlink { color: var(--gb-muted); }
.md-typeset ul li::marker, .md-typeset ol li::marker { color: var(--gb-green); }
.md-typeset ol li::marker { font-family: var(--gb-mono); }
.md-typeset hr { border-bottom-color: var(--gb-border); }
.md-typeset blockquote {
  border-left: 0.2rem solid var(--gb-border);
  color: var(--gb-muted);
}
.md-typeset abbr { text-decoration-color: var(--gb-muted); }
/* Аббревиатура внутри заголовка — не ссылка и не выносная сноска: пунктирная
   черта под ней (движок рисует её border-bottom) читалась как подчёркивание
   заголовка. Раскрытие по наведению (cursor: help) остаётся. */
.md-typeset h1 abbr, .md-typeset h2 abbr, .md-typeset h3 abbr,
.md-typeset h4 abbr { border-bottom: none; }
.md-typeset table:not([class]) {
  border: 1px solid var(--gb-border);
  box-shadow: none;
}
.md-typeset table:not([class]) th {
  background: var(--gb-surface);
  color: var(--gb-head);
  font-family: var(--gb-mono);
  font-size: 0.85em;
  /* Таблицы карты тем длинные: заголовок остаётся видимым. */
  position: sticky;
  top: 0;
}
.md-typeset table:not([class]) td { border-top: 1px solid var(--gb-border); }

/* Теги темы — чипами с решёткой, как в терминальном выводе. */
.md-typeset .md-tag {
  font-family: var(--gb-mono);
  background: var(--gb-surface);
  color: var(--gb-muted);
  border: 1px solid var(--gb-border);
}
.md-typeset .md-tag::before { content: "#"; color: var(--gb-green); }

/* Инлайн-код: рамка вместо заливки — в абзаце он не должен звенеть. */
.md-typeset :not(pre) > code {
  border: 1px solid var(--gb-border);
  border-radius: 0.2rem;
  color: var(--gb-text);
}
.md-typeset a code { color: var(--gb-green); }

/* ── листинги: окно терминала ────────────────────────────────────────────────
   Рамка, полоса слева и шапка-полоска с тремя точками и меткой языка. Метку
   даёт класс `language-*` (`pygments_lang_class`); правила под языки корпуса
   сборщик дописывает в конец этого файла. */
.md-typeset .highlight {
  position: relative;
  margin: 1.2em 0;
  border: 1px solid var(--gb-border);
  border-left: 3px solid var(--gb-green);
  border-radius: 0.35rem;
  background: var(--gb-surface);
  overflow: hidden;
}
.md-typeset .highlight::before {
  content: "code";
  display: block;
  /* Высота полосы = высоте кнопки копирования (1,75rem): кнопка живёт в этой
     полосе (правило `.md-code__nav` ниже) и не наезжает на строки листинга. */
  height: 1.75rem;
  line-height: 1.75rem;
  padding: 0 0.8rem 0 3.6rem;
  font-family: var(--gb-mono);
  font-size: 0.6rem;
  letter-spacing: 0.04em;
  color: var(--gb-muted);
  background:
    radial-gradient(circle at 0.85rem 50%, #ff5f56 0.22rem, transparent 0.24rem),
    radial-gradient(circle at 1.65rem 50%, #ffbd2e 0.22rem, transparent 0.24rem),
    radial-gradient(circle at 2.45rem 50%, #27c93f 0.22rem, transparent 0.24rem),
    var(--gb-surface-2);
  border-bottom: 1px solid var(--gb-border);
}
.md-typeset .highlight pre { margin: 0; }
.md-typeset .highlight pre > code {
  background: var(--gb-surface);
  border-radius: 0;
  box-shadow: none;
  /* Интерлиньяж листинга 1,45 (тема даёт 1,4). */
  line-height: 1.45;
}
/* Кнопка копирования — в шапке-полоске окна листинга, как кнопка окна.
   Движок ставит её в правый верхний угол `pre` (position: relative у него
   из темы), и конец длинной первой строки уезжал под неё; в шапке кода нет.
   Класс у кнопки в material 9.7 — `.md-code__nav`/`.md-code__button`;
   прежнее правило писалось под `.md-clipboard` и давно ни во что не попадало. */
.md-typeset .highlight .md-code__nav { top: -1.75rem; right: 0.5rem; }
/* Сеанс терминала: приглашение зелёное, вывод приглушён. */
.md-typeset .highlight .gp { color: var(--gb-green); font-weight: 700;
                             user-select: none; }
.md-typeset .highlight .go { color: var(--gb-muted); }
.md-typeset .highlight .err { color: var(--md-code-hl-special-color);
                              background: none; }

/* ── врезки ──────────────────────────────────────────────────────────────
   Рамка вместо тяжёлой заливки; подпись врезки — моноширинным. */
.md-typeset .admonition, .md-typeset details {
  background: var(--gb-bg);
  border-width: 1px;
  border-left-width: 3px;
  box-shadow: none;
  font-size: 0.9em;
}
.md-typeset .admonition-title, .md-typeset summary {
  color: var(--gb-text);
  font-weight: 700;
}
.md-typeset details > summary { cursor: pointer; }
/* Свёрнутые ответы «Проверь себя» (`<details>` без типа) — нейтральной
   рамкой с зелёным значком, а не синей «заметкой» темы. */
.md-typeset details:not([class]) { border-color: var(--gb-border);
                                   border-left-color: var(--gb-green); }
.md-typeset details:not([class]) > summary { background: var(--gb-surface); }
.md-typeset details:not([class]) > summary::before,
.md-typeset details:not([class]) > summary::after {
  background-color: var(--gb-green);
}

/* Схемы рисуются в двух вариантах (светлый и тёмный, `tools/render_diagrams.py`);
   движок показывает один из них по метке `#only-light`/`#only-dark` в адресе.
   Фон под картинкой повторяет испечённый фон варианта — виден в кайме padding. */
.md-typeset img.diagram {
  display: block;
  height: auto;
  margin-inline: auto;
  background: #fff;
  padding: 0.7rem;
  border-radius: 0.35rem;
  border: 1px solid var(--gb-border);
}
[data-md-color-scheme="slate"] .md-typeset img.diagram { background: #161b22; }
/* Движок прячет вариант не той темы правилом из своего каскадного слоя, но
   слой проигрывает нашему неслоеному `display: block` выше — поэтому показ
   варианта задаём здесь, тем же механизмом по метке в адресе. */
[data-md-color-scheme="slate"] .md-typeset img.diagram[src$="#only-light"],
[data-md-color-scheme="default"] .md-typeset img.diagram[src$="#only-dark"] {
  display: none;
}

/* Варианты ответов в «Проверь себя» («A. …», «B. …»): абзац с висячим
   отступом и бейджем-буквой; разметку ставит сборка (`quiz_options`). */
.md-typeset p.quiz-opt { padding-left: 2.1em; margin: 0.35em 0; }
.md-typeset .quiz-letter {
  display: inline-block;
  box-sizing: border-box;
  width: 1.45em;
  height: 1.45em;
  margin-left: -2.1em;
  margin-right: 0.65em;
  line-height: 1.4;
  text-align: center;
  font-family: var(--gb-mono);
  font-size: 0.8em;
  font-weight: 700;
  color: var(--gb-green);
  border: 1px solid var(--gb-green);
  border-radius: 0.2rem;
}

/* Маркер «можно отложить» (9.5 п. 10) — строка сразу под заголовком темы,
   приглушённая, с засечкой слева. */
.md-typeset p.topic-skip {
  font-size: 0.85em;
  line-height: 1.5;
  color: var(--gb-muted);
  border-left: 0.15rem solid var(--gb-green);
  padding-left: 0.6rem;
}

/* ── главная ─────────────────────────────────────────────────────────────── */
.md-typeset .hero { margin: 0.4rem 0 1.4rem; }
.md-typeset .hero__banner {
  margin: 0;
  font-family: var(--gb-mono);
  font-size: clamp(0.5rem, 2.4vw, 0.95rem);
  line-height: 1.3;
  color: var(--gb-green);
  background: none;
  white-space: pre;
  overflow: hidden;
}
.md-typeset .hero__prompt {
  margin: 0.6rem 0 0;
  font-family: var(--gb-mono);
  color: var(--gb-muted);
}
.md-typeset .hero__ps { color: var(--gb-green); font-weight: 700; }
.md-typeset .hero__cursor {
  display: inline-block;
  width: 0.55em;
  height: 1.1em;
  margin-left: 0.2em;
  vertical-align: text-bottom;
  background: var(--gb-green);
  animation: gb-blink 1.1s steps(1) infinite;
}
@keyframes gb-blink { 50% { opacity: 0; } }
@media (prefers-reduced-motion: reduce) {
  .md-typeset .hero__cursor { animation: none; }
}
.md-typeset .stage-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(13rem, 1fr));
  gap: 0.8rem;
  margin: 1.4rem 0 2rem;
}
.md-typeset a.stage-card {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
  padding: 0.9rem 1rem;
  border: 1px solid var(--gb-border);
  border-radius: 0.4rem;
  background: var(--gb-surface);
  color: var(--gb-text);
  text-decoration: none;
  transition: border-color 0.15s, transform 0.15s;
}
.md-typeset a.stage-card:hover, .md-typeset a.stage-card:focus-visible {
  border-color: var(--gb-green);
  transform: translateY(-1px);
  text-decoration: none;
}
.md-typeset a.stage-card:focus-visible { outline: 2px solid var(--gb-green);
                                         outline-offset: 2px; }
.stage-card__num {
  font-family: var(--gb-mono);
  font-size: 0.75em;
  color: var(--gb-green);
}
.stage-card__num::before { content: "~/"; color: var(--gb-muted); }
.stage-card__title { font-weight: 700; color: var(--gb-text); line-height: 1.3; }
.stage-card__meta { font-family: var(--gb-mono); font-size: 0.75em;
                    color: var(--gb-muted); }
.stage-card__go { margin-top: auto; padding-top: 0.4rem; font-size: 0.8em;
                  color: var(--gb-green); }
.stage-card__go::before { content: "$ "; font-family: var(--gb-mono); }

/* ── кегль ───────────────────────────────────────────────────────────────────
   Кегль текста 18 px (PLAYBOOK 7.7, норма 17–19 px). Тема задаёт корень в
   процентах ступенями — 125 % (20 px), от 100 em 137,5 % (22 px), от 125 em
   150 % (24 px) — поэтому кегль перезадаётся на каждой ступени. Кегль кода
   тема считает сама как 0,85em от текста: выходит 15,3 px, норма «не меньше
   15 px» держится без отдельного правила. Печатная ступень повторяет тему. */
.md-typeset { font-size: 0.9rem; }
@media screen and (min-width: 100em) {
  .md-typeset { font-size: 0.82rem; }
}
@media screen and (min-width: 125em) {
  .md-typeset { font-size: 0.75rem; }
}
@media print {
  .md-typeset { font-size: 0.68rem; }
  .md-typeset .highlight::before { display: none; }
}
"""

# Метка языка в шапке листинга: подписи для языков корпуса. Язык, которого
# здесь нет, подписывается своим именем из класса.
LANG_LABELS = {"console": "terminal", "text": "text", "javascript": "js",
               "typescript": "ts", "dockerfile": "Dockerfile", "ql": "codeql"}


def lang_css(langs: set[str]) -> str:
    """Правила `::before` с меткой языка для каждого языка, что встретился."""
    rules = []
    for lang in sorted(langs):
        if not re.fullmatch(r"[a-z0-9+#-]+", lang):
            continue
        label = LANG_LABELS.get(lang, lang)
        rules.append(f'.md-typeset .language-{lang}.highlight::before '
                     f'{{ content: "{label}"; }}')
    return "\n/* Метки языков листингов: собраны из корпуса. */\n" + "\n".join(rules) + "\n"


# ── «Первоисточники», «Повторение», сводки этапов, «На чём проверено» ────────
#
# Решения оператора 2026-10-01 (реестр `journal/RESEARCH-NOVICE-2026-10.md`,
# пункты 5 и 7). Всё ниже собирается из данных, которые уже есть: вопросы — из
# блоков «Предвопросы» и «Проверь себя» тем, функции — из файлов `code.*`
# лабораторных, сводки — из блоков «Коротко» и «Чеклист ревью», версии — из
# «Маркеров уверенности». Исходники тем при этом не меняются.


def load_sources_registry() -> dict[str, dict]:
    """Реестр источников по `id`: адрес, название, издатель, версия."""
    data = vc.load_yaml(vc.SOURCES_YAML)
    return {str(s["id"]): s for s in (data.get("sources") or [])
            if isinstance(s, dict)}


def primary_sources(page: vc.Page, registry: dict[str, dict]) -> list[str]:
    """Пункты списка первоисточников темы: название, издатель, версия."""
    items = []
    for sid in (page.front.get("sources") or []):
        src = registry.get(str(sid)) or {}
        url, title = src.get("url"), one_line(src.get("title") or "")
        if not url or not title:
            continue
        extra = ", ".join(x for x in (one_line(src.get("publisher") or ""),
                                      one_line(src.get("version_or_date") or ""))
                          if x)
        items.append(f"- [{title}]({url})" + (f" — {extra}." if extra else "."))
    return items


def read_more(page: vc.Page, page_rel: str, index: dict[str, str],
              titles: dict[str, str], registry: dict[str, dict]
              ) -> tuple[str, int]:
    """Раздел «Что почитать дальше» и число первоисточников в нём.

    Первая строка — предпосылки ссылками с названиями тем («Перед этой темой
    полезно знать: …»); тема вне корпуса остаётся без ссылки — сослаться не на
    что. За ней — первоисточники, по которым сверена тема.
    """
    parts = []
    prereqs = [q for q in (page.front.get("prerequisites") or []) if q != page.id]
    if prereqs:
        links = ", ".join(
            f"[{titles.get(q, q)}]({link_to(page_rel, index[q])})" if q in index
            else f"«{q}»" for q in prereqs)
        parts.append(f"Перед этой темой полезно знать: {links}.")
    items = primary_sources(page, registry)
    if items:
        parts.append("Первоисточники, по которым сверена статья, — с них стоит "
                     "начать, если хочется глубже. Если текст и документ "
                     "расходятся, верен документ.")
        parts.append("\n".join(items))
    if not parts:
        return "", 0
    return f"## {READ_MORE}\n\n" + "\n\n".join(parts), len(items)


# ── заимствование текста тем ─────────────────────────────────────────────────

NUM_ITEM_RE = re.compile(r"^(\d+)\.[ \t]+")


def block_titled(page: vc.Page, word: str) -> vc.Block | None:
    """Блок по каноническому названию — или по живому, если в исходнике уже
    стоит оно (`BLOCK_TITLES`): собранные страницы этапа не должны терять
    блок оттого, что автор переименовал заголовок."""
    names = {word, BLOCK_TITLES.get(word) or word}
    return next((b for b in page.blocks if any(n in b.title for n in names)),
                None)


def numbered_items(lines: list[str]) -> list[str]:
    """Пункты нумерованного списка без номеров, с продолжениями.

    Продолжение пункта — строка с отступом или пустая; первая строка без
    отступа и не «N.» список заканчивает (так список вопросов отрезается от
    следующего за ним `<details>`, а список ответов — от `</details>`).
    """
    items, cur = [], []
    for ln in lines:
        if NUM_ITEM_RE.match(ln):
            if cur:
                items.append("\n".join(cur).rstrip())
            cur = [NUM_ITEM_RE.sub("", ln, count=1)]
        elif cur and (not ln.strip() or ln[:1] in (" ", "\t")):
            cur.append(ln)
        elif cur:
            items.append("\n".join(cur).rstrip())
            cur = []
            break
    if cur:
        items.append("\n".join(cur).rstrip())
    return [it for it in items if it.strip()]


def selfcheck_qa(page: vc.Page) -> list[tuple[str, str | None]]:
    """Пары «вопрос, ответ» из блока «Проверь себя». Нумерация в корпусе
    сплошная и совпадающая у вопросов и ответов (проверено по 160 блокам),
    поэтому пары ставятся по позиции."""
    block = block_titled(page, "Проверь себя")
    if not block:
        return []
    q_lines, a_lines, inside = [], [], False
    for ln in page.text_of(block):
        tag = ln.strip()
        if tag.startswith("<details"):
            inside = True
            continue
        if tag.startswith("</details"):
            inside = False
            continue
        if tag.startswith("<summary"):
            continue
        (a_lines if inside else q_lines).append(ln)
    questions, answers = numbered_items(q_lines), numbered_items(a_lines)
    return [(q, answers[i] if i < len(answers) else None)
            for i, q in enumerate(questions)]


def prequestions(page: vc.Page) -> list[str]:
    """Предвопросы темы без вводной фразы о методе."""
    block = block_titled(page, "Предвопросы")
    return numbered_items(page.text_of(block)) if block else []


def topic_footnotes(page: vc.Page) -> dict[str, str]:
    """Определения сносок темы: явные из хвоста, а где их нет — собранные из
    пунктов «Источников» (тем же способом, что на странице самой темы)."""
    cut = SOURCES_HEAD_RE.search(page.doc.raw)
    if not cut:
        return {}
    tail = page.doc.raw[cut.start():]
    defs, items = footnote_defs(tail), source_items(tail)
    for ref, item in items.items():
        defs.setdefault(ref, synth_def(item))
    return defs


def carry_footnotes(text: str, page: vc.Page, defs: dict[str, str],
                    needed: dict[str, str]) -> str:
    """Метки сносок в заимствованном тексте получают приставку темы, а
    определения переезжают на собранную страницу: чужой `[^1]` иначе
    столкнулся бы с нашим или остался бы висеть литералом."""
    def repl(m: re.Match) -> str:
        ref = m.group(1)
        if ref not in defs:
            return m.group(0)
        label = f"{page.id}-{ref}"
        needed.setdefault(label, defs[ref])
        return f"[^{label}]"
    return FN_REF_RE.sub(repl, text)


def embed_links(text: str, page_rel: str, index: dict[str, str],
                report: dict, titles: dict[str, str] | None = None) -> str:
    """`` `topic-id` `` → ссылка на тему: то же превращение, что на страницах
    тем (подпись — название темы, А1), но для текста, заимствованного
    собранными страницами. Ограждённые блоки пропускаются — в коде ссылка не
    работает."""
    def repl(m: re.Match) -> str:
        tid = m.group(2).strip()
        if "\n" not in tid and tid in index:
            report["links"] += 1
            label = (titles or {}).get(tid) or tid
            return f"[{label}]({link_to(page_rel, index[tid])})"
        return m.group(0)
    out, last = [], 0
    for fence in mdtext.FENCE_RE.finditer(text):
        out.append(mdtext.CODE_SPAN_RE.sub(repl, text[last:fence.start()]))
        out.append(fence.group(0))
        last = fence.end()
    out.append(mdtext.CODE_SPAN_RE.sub(repl, text[last:]))
    return "".join(out)


def stable_key(*parts: str) -> str:
    """Порядок выборки, одинаковый от сборки к сборке: меняется только вместе
    с самими данными, а не от запуска к запуску."""
    return hashlib.sha1("\x00".join(parts).encode("utf-8")).hexdigest()


# ── «Повторение»: вопросы пройденного и смешанные задачи ─────────────────────


def review_pool(pages: list[vc.Page], stage_order: dict[str, int],
                upto: int) -> list[tuple[vc.Page, str, str | None]]:
    """Вопросы тем до конца этапа `upto` включительно. Сначала самопроверка
    (у неё есть ответы), предвопросом заполненный дубликат не вытесняет."""
    pool = []
    for p in pages:
        if stage_order[str(p.front.get("stage"))] > upto:
            continue
        seen: set[str] = set()
        for q, a in selfcheck_qa(p) + [(q, None) for q in prequestions(p)]:
            key = re.sub(r"\s+", " ", q.lower())[:100]
            if key in seen:
                continue
            seen.add(key)
            pool.append((p, q, a))
    return pool


def pick_review(pool: list[tuple[vc.Page, str, str | None]],
                stage_order: dict[str, int], limit: int = 10
                ) -> list[tuple[vc.Page, str, str | None]]:
    """Выборка с разносом по этапам: по кругу от самого раннего, не больше
    одного вопроса на тему, пока хватает кандидатов."""
    buckets: dict[str, list] = {}
    for cand in pool:
        buckets.setdefault(str(cand[0].front.get("stage")), []).append(cand)
    for bucket in buckets.values():
        bucket.sort(key=lambda c: stable_key(c[0].id, c[1]))
    picked, taken, per_topic = [], set(), {}
    cap = 1
    while len(picked) < limit and cap <= 2:
        progressed = False
        for slug in sorted(buckets, key=lambda s: stage_order[s]):
            for cand in buckets[slug]:
                key = stable_key(cand[0].id, cand[1])
                if key in taken or per_topic.get(cand[0].id, 0) >= cap:
                    continue
                picked.append(cand)
                taken.add(key)
                per_topic[cand[0].id] = per_topic.get(cand[0].id, 0) + 1
                progressed = True
                break
            if len(picked) >= limit:
                break
        if not progressed:
            cap += 1
    picked.sort(key=lambda c: (stage_order[str(c[0].front.get("stage"))],
                               int(c[0].front.get("order") or 0)))
    return picked


VULN_MARK = "УЯЗВИМО"
JS_FN_RE = re.compile(r"^(?:export[ \t]+)?(?:async[ \t]+)?function[ \t]+\w+")


def py_units(text: str) -> list[str]:
    """Функции верхнего уровня с пометкой «УЯЗВИМО» в строках над `def`."""
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return []
    lines = text.split("\n")
    out = []
    for node in tree.body:
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        start = min([node.lineno] + [d.lineno for d in node.decorator_list])
        above = "\n".join(lines[max(0, start - 4):start - 1])
        if VULN_MARK not in above:
            continue
        out.append("\n".join(lines[start - 1:node.end_lineno]))
    return out


def js_units(text: str) -> list[str]:
    """Обработчики верхнего уровня по балансу скобок; если функций нет —
    файл целиком (так устроен `same-origin-policy/code.js`)."""
    lines = text.split("\n")
    units, i = [], 0
    while i < len(lines):
        if JS_FN_RE.match(lines[i]):
            depth, j, opened = 0, i, False
            while j < len(lines):
                depth += lines[j].count("{") - lines[j].count("}")
                opened = opened or "{" in lines[j]
                j += 1
                if opened and depth <= 0:
                    break
            units.append("\n".join(lines[i:j]))
            i = max(j, i + 1)
        else:
            i += 1
    handlers = [u for u in units if re.search(r"function[ \t]+(handle|dispatch)", u)]
    return handlers or units or [text]


def clean_unit(code: str) -> str:
    """Пометка «УЯЗВИМО» и шапка комментариев срезаются: подпись «откуда и
    что здесь не так» — это ответ на задачу, а не часть условия."""
    lines = [ln for ln in code.split("\n") if VULN_MARK not in ln]
    while lines and (not lines[0].strip()
                     or lines[0].lstrip().startswith(("#", "//", "/*", "*"))):
        lines.pop(0)
    return "\n".join(lines).strip("\n")


def lab_units(lab: dict) -> list[tuple[str, str]]:
    """(язык, код) уязвимых фрагментов лабораторной — без имён файлов."""
    out, seen = [], set()
    for code_file in sorted((ROOT / lab["path"]).glob("code.*")):
        text = code_file.read_text(encoding="utf-8")
        if code_file.suffix == ".py":
            units = [("python", u) for u in py_units(text)]
        elif code_file.suffix in (".js", ".mjs"):
            units = [("javascript", u) for u in js_units(text)]
        else:
            continue
        for lang, unit in units:
            cleaned = clean_unit(unit)
            if not (4 <= len(cleaned.split("\n")) <= 30) or cleaned in seen:
                continue
            seen.add(cleaned)
            out.append((lang, cleaned))
    return out


def pick_tasks(labs: list[dict], by_id: dict[str, vc.Page],
               stage_order: dict[str, int], stage_slug: str, upto: int,
               limit: int = 8) -> list[tuple[dict, str, str]]:
    """Функции лабораторных без подписей: свои этапы вперёд, не больше двух
    фрагментов из одной лабораторной."""
    pools = []
    for lab in labs:
        topic = by_id.get(lab["topic"])
        if topic is None:
            continue
        tstage = str(topic.front.get("stage"))
        if stage_order[tstage] > upto:
            continue
        units = lab_units(lab)
        if units:
            pools.append((tstage != stage_slug, lab, units))
    pools.sort(key=lambda x: (x[0], stable_key(x[1]["id"])))
    picked, taken, per_lab = [], set(), {}
    cap = 1
    while len(picked) < limit and cap <= 2:
        progressed = False
        for _, lab, units in pools:
            for unit in sorted(units, key=lambda u: stable_key(lab["id"], u[1])):
                key = stable_key(lab["id"], unit[1])
                if key in taken or per_lab.get(lab["id"], 0) >= cap:
                    continue
                picked.append((lab, *unit))
                taken.add(key)
                per_lab[lab["id"]] = per_lab.get(lab["id"], 0) + 1
                progressed = True
                break
            if len(picked) >= limit:
                break
        if not progressed:
            cap += 1
    return picked


def page_stage_review(stage: dict, upto: int, ctx: vc.Ctx,
                      pages: list[vc.Page], labs: list[dict],
                      fn_of, index: dict[str, str], rel: str,
                      report: dict, titles: dict[str, str] | None = None) -> str:
    """Страница «Повторение» этапа: вопросы на пройденное и смешанные задачи."""
    num, title = int(stage["num"]), stage["title"]
    stage_order = {s["slug"]: i for i, s in enumerate(ctx.tax["stages"])}
    by_id = {p.id: p for p in pages}
    needed: dict[str, str] = {}

    def adopt(text: str, owner: vc.Page) -> str:
        return embed_links(carry_footnotes(text, owner, fn_of(owner), needed),
                           rel, index, report, titles)

    parts = [f"""---
title: Этап {num}. Повторение
description: Вопросы на пройденные темы и задачи без подписей — повторение этапа «{title}».
---

{GENERATED}

# Этап {num}. Повторение

Страница собрана из того, что уже написано: вопросы — из врезок «Подумай,
прежде чем читать» и разделов «Проверь себя» пройденных тем, функции — из
лабораторных. Набор меняется,
только когда меняются сами темы.

## Повтор пройденного

Ответьте на каждый вопрос вслух или черновиком, не открывая ответа: вспомнить
своими словами и есть упражнение.
"""]

    picked = pick_review(review_pool(pages, stage_order, upto), stage_order)
    groups: dict[str, list] = {}
    for topic, q, a in picked:
        groups.setdefault(topic.id, []).append((topic, q, a))
    report["review_q"] += len(picked)
    for tid, items in groups.items():
        topic = items[0][0]
        parts.append(f"### [{one_line(topic.front.get('title'))}]"
                     f"({link_to(rel, index[tid])})\n")
        for i, (_, q, _) in enumerate(items, 1):
            parts.append(f"{i}. {adopt(q, topic)}")
        parts.append("\n<details markdown=\"1\">\n<summary>Ответы</summary>\n")
        for i, (_, _, a) in enumerate(items, 1):
            parts.append(f"{i}. {adopt(a, topic) if a else 'Это предвопрос: '
                         'ответ на него даёт текст самой темы.'}")
        parts.append("\n</details>\n")

    tasks = pick_tasks(labs, by_id, stage_order, stage["slug"], upto)
    if tasks:
        parts.append("""## Смешанные задачи

Функции из лабораторных — без подписей и вперемешку. На каждую ответьте двумя
фразами: какой здесь класс дефекта и какая строка его держит.
""")
        report["mixed"] += len(tasks)
        for lab, lang, code in tasks:
            topic = by_id[lab["topic"]]
            answer = (f"Из лабораторной к теме "
                      f"[{one_line(topic.front.get('title'))}]"
                      f"({link_to(rel, index[topic.id])}): дефект того класса, "
                      f"которому посвящена тема; точное место и починка — в её "
                      f"разделах «Как это выглядит в коде» и «Как защититься».")
            parts.append(f"```{lang}\n{code}\n```\n\n"
                         f"<details markdown=\"1\">\n<summary>Ответ</summary>\n\n"
                         f"{answer}\n\n</details>\n")

    if needed:
        parts.append("")
        parts += [f"[^{label}]: {text}" for label, text in needed.items()]
    # Вопросы и ответы заимствованы из тем целиком — с вариантами «A. …»;
    # разметка бейджей та же, что на страницах тем.
    return quiz_options("\n".join(parts), report)


# ── сводка этапа ─────────────────────────────────────────────────────────────


def page_stage_summary(stage: dict, group: list[vc.Page], ctx: vc.Ctx,
                       sub_titles: dict[tuple[int, str], str], fn_of,
                       index: dict[str, str], rel: str, report: dict,
                       titles: dict[str, str] | None = None) -> str:
    """Сводка этапа: блоки «Коротко» всех тем подряд и общий чеклист ревью."""
    num, title = int(stage["num"]), stage["title"]
    needed: dict[str, str] = {}

    def adopt(text: str, owner: vc.Page) -> str:
        return embed_links(carry_footnotes(text, owner, fn_of(owner), needed),
                           rel, index, report, titles)

    # Подразделы есть не у всех этапов: где план их задаёт, сводка резана по
    # ним; где этап единым списком — темы идут подряд.
    subs: dict[str, list[vc.Page]] = {}
    for p in group:
        meta = ctx.plan.get(str(p.front.get("plan_id") or "")) or {}
        subs.setdefault(str(meta.get("sub") or ""), []).append(p)
    use_subs = len(subs) > 1

    def topics_lines(part: str) -> list[str]:
        out = []
        for sub, topics in subs.items():
            if use_subs:
                out.append(f"### {sub_titles.get((num, sub), sub)}\n")
            for p in topics:
                block = block_titled(p, "Коротко" if part == "korotko"
                                     else "Чеклист ревью")
                if not block:
                    continue
                text = "\n".join(p.text_of(block)).strip("\n")
                if not text.strip():
                    continue
                link = f"[{one_line(p.front.get('title'))}]({link_to(rel, index[p.id])})"
                if use_subs:
                    if part == "korotko":
                        text = f"**{link}.** " + text
                    else:
                        text = f"**{link}:**\n\n" + text
                else:
                    out.append(f"### {link}\n")
                out.append(adopt(text, p) + "\n")
        return out

    parts = [f"""---
title: Этап {num} коротко
description: Все темы этапа «{title}» одним абзацем каждая и общий чеклист ревью.
---

{GENERATED}

# Этап {num} коротко

Конденсат этапа: «Если коротко» всех тем подряд и за ними общий чеклист для
ревью. Примеры, разборы и ответы — в самих темах.

## Коротко о каждой теме
"""]
    parts += topics_lines("korotko")
    parts.append("## Чеклист этапа\n")
    parts += topics_lines("checklist")
    if needed:
        parts.append("")
        parts += [f"[^{label}]: {text}" for label, text in needed.items()]
    return "\n".join(parts)


# ── «На чём проверено» ───────────────────────────────────────────────────────
#
# Версии извлекаются из «Маркеров уверенности» тем. Даты по решению оператора
# не выносятся: страница отвечает «на чём», а не «когда».

MARKERS_RE = re.compile(r"\*\*Маркеры уверенности\.\*\*(.*?)(?:\n[ \t]*\n|\Z)",
                        re.S)
VERSION_RE = re.compile(
    r"(?<![\w./:+@-])v?(\d+(?:\.\d+)+(?:[-+.][0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*)?)")
# Слова, после которых число — не версия инструмента: балл CVSS («NVD 10.0,
# RedHat 9.8»), версия протокола в тексте («TLS 1.3»), префикс «v».
NAME_STOP = {"tls", "cvss", "nvd", "redhat", "http", "https", "v"}
# Одно и то же под разными именами в маркерах: «Node 26.7.0» и «Node.js 26.7.0».
NAME_ALIAS = {"node": "node.js"}


def tool_mentions(text: str) -> list[tuple[str, str]]:
    """Пары «название, версия» из абзаца маркеров. Название собирается
    обратным ходом от версии по латинским словам через один пробел:
    «на Python 3.14.7» → Python, «по OpenID Connect Core 1.0» → все три
    слова. Кириллица, конец предыдущего предложения и стоп-слова ход
    останавливают."""
    flat = re.sub(r"\s+", " ", text)
    out = []
    for m in VERSION_RE.finditer(flat):
        ver = m.group(1).rstrip(".")
        tokens = flat[:m.start()].rstrip().split(" ")
        words, tainted = [], False
        for pos in range(len(tokens) - 1, -1, -1):
            tok = tokens[pos]
            if not tok or not tok[0].isascii() or not tok[0].isalpha():
                break
            if tok.lower() in NAME_STOP:
                tainted = True
                break
            # Элемент перечня («Arch Linux, Docker 29.7.2») — не часть названия.
            if tok.endswith((",", ";", ":")):
                break
            words.append(tok)
            if pos > 0 and tokens[pos - 1].endswith((".", "!", "?", ":", ";", ",")):
                break
            if len(words) >= 4:
                break
        if words and not tainted:
            out.append((" ".join(reversed(words)), ver))
    return out


def plural(n: int, forms: tuple[str, str, str]) -> str:
    """Русское согласование числительных: 1 тема, 3 темы, 5 тем."""
    n100, n10 = n % 100, n % 10
    if 11 <= n100 <= 14 or n10 == 0 or n10 >= 5:
        return forms[2]
    return forms[0] if n10 == 1 else forms[1]


def page_verified(pages: list[vc.Page], index: dict[str, str]) -> tuple[str, int]:
    """«На чём проверено»: инструмент, версия, темы — по маркерам уверенности."""
    by_id = {p.id: p for p in pages}
    route_pos = {p.id: i for i, p in enumerate(pages)}
    rows: dict[tuple[str, str], dict] = {}
    for p in pages:
        m = MARKERS_RE.search(p.doc.raw)
        if not m:
            continue
        for name, ver in tool_mentions(m.group(1)):
            key = name.lower().removeprefix("owasp ")
            key = NAME_ALIAS.get(key, key)
            row = rows.setdefault((key, ver), {"casings": {}, "topics": set()})
            row["casings"][name] = row["casings"].get(name, 0) + 1
            row["topics"].add(p.id)
    entries = []
    for (name_key, ver), row in rows.items():
        name = max(row["casings"], key=row["casings"].get)
        entries.append((name, ver, sorted(row["topics"], key=route_pos.get)))
    entries.sort(key=lambda e: (-len(e[2]), e[0].lower(), e[1]))

    parts = [f"""---
title: На чём проверено
description: Версии инструментов, каталогов и образцов, на которых темы проверялись прогоном.
---

{GENERATED}

# На чём проверено

Приёмы и листинги тем проверяются прогоном на конкретных версиях. Здесь
собрано, на каких именно: когда выходит новая версия инструмента, по этому
списку видно, какие темы стоит перечитать и перепроверить. Дат здесь нет:
страница отвечает на вопрос «на чём», а не «когда».

Записи собраны машиной из пометок проверки в исходниках тем; если чего-то
здесь нет, значит, версия просто не записана, а не что тема не проверялась.
"""]
    for name, ver, tids in entries:
        links = ", ".join(f"[{short_title(by_id[t].front.get('title'))}]"
                          f"({link_to('verified.md', index[t])})" for t in tids)
        parts.append(f"### {name} {ver}\n")
        parts.append(f"{len(tids)} {plural(len(tids), ('тема', 'темы', 'тем'))}.\n\n"
                     f"<details markdown=\"1\">\n"
                     f"<summary>Какие именно</summary>\n\n{links}\n\n</details>\n")
    return "\n".join(parts), len(entries)


# ── лабораторные: страница «Лабы» и страницы лаб ─────────────────────────────
#
# Решение оператора 2026-10-01 (А8). До него лабы существовали только в
# репозитории: `pilot/` в сайт не попадал, страницы лаб в сборке не было, на
# карте — колонки, в блоке «Лаба» — команды запуска. Всё ниже собирается из
# `labs.yaml` и `pilot/lab/*/README.md`; исходники лаб не меняются.

LAB_H1_RE = re.compile(r"^#[ \t]+(.+)$", re.M)
LAB_RUN_HEAD_RE = re.compile(r"^##[ \t]+(?:Запуск|Как запускать)[ \t]*$", re.M)
FENCE_BODY_RE = re.compile(r"```\w*[ \t]*\n(.*?)```", re.S)
# Заголовки README двух видов: «Лаба: горизонтальная эскалация и IDOR» и
# «Лаба zap-scanning: разверни, …» — служебное слово и id срезаются в обоих.
LAB_NAME_PREFIX_RE = re.compile(r"^Лаба(?:[ \t]+[a-z0-9-]+)?:[ \t]*")


def lab_human_name(h1: str, fallback: str) -> str:
    """Название лабы для читателя — из заголовка её README, без служебного id."""
    name = LAB_NAME_PREFIX_RE.sub("", h1).strip()
    if not name:
        return fallback
    return name[0].upper() + name[1:]


def lab_commands(text: str) -> list[str]:
    """Команды прогона из раздела «Запуск»/«Как запускать» README. Строка `cd`
    пропускается — её страница строит из реестра; пояснения-комментарии
    срезаются; переносы строки по `\\` склеиваются."""
    m = LAB_RUN_HEAD_RE.search(text)
    fence = FENCE_BODY_RE.search(text, m.end()) if m else None
    if not fence:
        return []
    cmds, cur = [], ""
    for ln in fence.group(1).split("\n"):
        cur = (cur + " " + ln.strip()) if cur else ln.strip()
        if cur.endswith("\\"):
            cur = cur[:-1].rstrip()
            continue
        if cur and not cur.startswith("#"):
            cmds.append(re.sub(r"[ \t]+#.*$", "", cur).strip())
        cur = ""
    if cur and not cur.startswith("#"):
        cmds.append(re.sub(r"[ \t]+#.*$", "", cur).strip())
    return [c for c in cmds if not c.startswith("cd ")]


def lab_docs(ctx: vc.Ctx, route_pos: dict[str, int]) -> list[dict]:
    """Лабы с названием, командами и slug страницы. Порядок — порядок маршрута
    тем-владельцев: лаба идёт вслед за своей темой, а не по алфавиту id."""
    out = []
    for lab in ctx.labs.values():
        text = (ROOT / lab["path"] / "README.md").read_text(encoding="utf-8")
        m = LAB_H1_RE.search(text)
        h1 = m.group(1).strip() if m else lab["id"]
        out.append({**lab,
                    "slug": Path(lab["path"]).name,
                    "name": lab_human_name(h1, lab["id"]),
                    "readme": text,
                    "run": lab_commands(text)})
    out.sort(key=lambda lab: (route_pos.get(str(lab["topic"]), 10 ** 6),
                              lab["slug"]))
    return out


def page_labs(labs: list[dict], by_id: dict[str, vc.Page],
              index: dict[str, str]) -> str:
    """Страница «Лабы»: все лабораторные одной таблицей."""
    rows = []
    for lab in labs:
        topic = by_id.get(lab["topic"])
        topic_cell = "—"
        if topic:
            topic_cell = (f"[{short_title(one_line(topic.front.get('title')))}]"
                          f"({link_to('labs.md', index[topic.id])})")
        run = f"`cd {lab['path']}`"
        if lab["run"]:
            run += ", затем `" + "`, `".join(lab["run"][:2]) + "`"
            if len(lab["run"]) > 2:
                run += " и дальше по инструкции"
        cells = [f"[{lab['name']}](labs/{lab['slug']}.md)", topic_cell,
                 f"«{lab['kind']}»", run]
        rows.append("| " + " | ".join(c.replace("|", "\\|") for c in cells) + " |")

    return f"""---
title: Лабы
description: Все лабораторные гайдбука — к какой теме привязана, что задано, как запустить.
---

{GENERATED}

# Лабы

Темы читаются, лабы делаются: {len(labs)} практических работ, каждая привязана
к своей теме. Всё запускается локально, без сети: из корня репозитория — `cd`
в каталог лабы, затем команды из таблицы. Цель, состав файлов, подсказка и
сброс — на странице самой лабы.

Колонка «Формат» — что задано: «почини» — убрать дефект, не сломав
функциональность; «найди-дефект» — дефект не подписан, его надо найти и
объяснить; «напиши-правило» — довести заготовку SAST-правила до схождения с
разметкой; «разверни-и-проверь» — поднять стенд и проверить его инструментом.

| Лаба | Тема | Формат | Запуск |
|---|---|---|---|
{chr(10).join(rows)}
"""


def page_lab(lab: dict, topic: vc.Page | None, index: dict[str, str]) -> str:
    """Страница лабы: её README целиком плюс обратная ссылка на тему."""
    rel = f"labs/{lab['slug']}.md"
    topic_title = one_line(topic.front.get("title")) if topic else ""
    meta = yaml.safe_dump(
        {"title": lab["name"],
         "description": (f"Лабораторная к теме «{topic_title}»: цель, файлы, "
                         f"запуск." if topic else
                         "Лабораторная гайдбука: цель, файлы, запуск.")},
        allow_unicode=True, sort_keys=False, width=10 ** 6)
    lead = f"Формат: «{lab['kind']}». Каталог в репозитории: `{lab['path']}`."
    if topic:
        lead = (f"Тема: [{topic_title}]({link_to(rel, index[topic.id])}). "
                + lead)
    # README начинается с h1 «Лаба …»: на странице заголовок уже стоит,
    # второй не нужен.
    body = LAB_H1_RE.sub("", lab["readme"], count=1).strip("\n")
    return (f"---\n{meta}---\n\n{GENERATED}\n\n# {lab['name']}\n\n{lead}\n\n"
            f"{body}\n")


# ── сборка ───────────────────────────────────────────────────────────────────


def subsections_of(topics_cfg: dict, stage: dict) -> list[dict]:
    """Подразделы этапа из `topics.yaml` (план обучения), в порядке плана."""
    for s in (topics_cfg or {}).get("stages") or []:
        if int(s["num"]) == int(stage["num"]):
            return list(s.get("subsections") or [])
    return []


def nav_sub_label(sub: dict) -> str:
    """Подпись подраздела в меню: «1.1 Broken Access Control» — номер и
    название без скобочного хвоста: каталожные номера и пометки плана в меню
    не нужны, полное название стоит заголовком в сводке этапа."""
    title = re.sub(r"[ \t]*\([^()]*\)[ \t]*$", "", str(sub.get("title") or ""))
    title = title.strip()
    return f"{sub['num']} {title}".strip()


def stage_nav(stage: dict, group: list[vc.Page], ctx: vc.Ctx,
              topics_cfg: dict, index: dict[str, str]) -> list:
    """Пункты меню этапа. Этап с подразделами в плане (этапы 1, 2, 4, 7)
    строится деревом по подразделам — решение оператора 2026-10-01 (А7):
    плоский список из 83 тем первого этапа не читается. Этап без подразделов
    в плане остаётся плоским списком."""
    subs = subsections_of(topics_cfg, stage)
    if len(subs) < 2:
        return [index[p.id] for p in group]
    known = {str(sub["num"]) for sub in subs}
    by_sub: dict[str, list[vc.Page]] = {}
    loose: list[vc.Page] = []
    for p in group:
        meta = ctx.plan.get(str(p.front.get("plan_id") or "")) or {}
        sub = str(meta.get("sub") or "")
        if sub in known:
            by_sub.setdefault(sub, []).append(p)
        else:
            loose.append(p)
    items: list = [index[p.id] for p in loose]
    for sub in subs:
        bucket = by_sub.get(str(sub["num"]))
        if bucket:
            items.append({nav_sub_label(sub): [index[p.id] for p in bucket]})
    return items


def nav_for(ctx: vc.Ctx, pages: list[vc.Page], index: dict[str, str],
            stage_extras: dict[str, list[str]] | None = None,
            topics_cfg: dict | None = None,
            labs: list[dict] | None = None) -> list:
    by_stage: dict[str, list[vc.Page]] = {}
    for p in pages:
        by_stage.setdefault(str(p.front.get("stage")), []).append(p)
    nav: list = [{"Начало": "index.md"}]
    for stage in ctx.tax["stages"]:
        group = by_stage.get(stage["slug"], [])
        if not group:
            continue
        items = stage_nav(stage, group, ctx, topics_cfg or {}, index)
        items += list((stage_extras or {}).get(stage["slug"], []))
        nav.append({f"Этап {stage['num']}. {stage['title']}": items})
    if labs:
        nav.append({"Лабы": ["labs.md"]
                    + [{lab["name"]: f"labs/{lab['slug']}.md"} for lab in labs]})
    nav.append({"Справочное": ["map.md", "mapping.md", "tags.md",
                               "glossary.md", "verified.md", "attributions.md"]})
    return nav


def write_config(nav: list) -> None:
    body = yaml.safe_dump({"docs_dir": "site-src", "site_dir": "../site",
                           "nav": nav},
                          allow_unicode=True, sort_keys=False, width=10 ** 6)
    CONFIG_OUT.write_text(
        "# Собрано `tools/build_site.py`: навигация выведена из `stage` и `order`\n"
        "# тем (9.1 п. 7). Правки вносятся в корневой `mkdocs.yml`, этот файл\n"
        "# перезаписывается каждой сборкой.\n"
        f"INHERIT: ../{CONFIG_IN.name}\n" + body, encoding="utf-8")


def stage_tree(today: date) -> dict:
    ctx = vc.Ctx()
    pages = vc.load_pages()
    if not pages:
        raise SystemExit("в `content/` нет ни одной темы: собирать нечего")
    glossary = yaml.safe_load(GLOSSARY_YAML.read_text(encoding="utf-8"))

    index = {p.id: f"{ctx.stages[str(p.front.get('stage'))]['dir']}/{p.id}.md"
             for p in pages}
    # Маршрут читателя: этапы — в порядке словаря `taxonomy.yaml`, темы внутри
    # этапа — по полю `order`. Ссылка «Дальше» на странице ведёт на следующую
    # тему маршрута; у последней темы маршрута её нет (решение 2026-08-31).
    stage_order = {s["slug"]: i for i, s in enumerate(ctx.tax["stages"])}
    route = sorted(pages, key=lambda p: (stage_order[str(p.front.get("stage"))],
                                         int(p.front.get("order") or 0)))
    next_of = {p.id: q for p, q in zip(route, route[1:])}
    abbr = abbreviations(glossary)
    gloss = glossary_matcher(glossary)
    sources_reg = load_sources_registry()
    # Подписи межтемных ссылок (А1): id темы → её название для ссылки.
    titles = {p.id: short_title(one_line(p.front.get("title") or p.id))
              for p in pages}
    # Лабораторные (А8): README прочитаны один раз, порядок — по маршруту тем.
    by_id = {p.id: p for p in pages}
    route_pos = {p.id: i for i, p in enumerate(route)}
    labs = lab_docs(ctx, route_pos)
    topic_labs: dict[str, list[dict]] = {}
    for lab in labs:
        topic_labs.setdefault(str(lab["topic"]), []).append(lab)
    report = {"pages": 0, "links": 0, "gloss": 0, "stale": 0, "skip": 0,
              "abbr": 0,
              "diagrams": 0, "diagrams_failed": [], "generated": 0,
              "diagram_files": set(), "footnotes": 0, "footnotes_synth": 0,
              "footnotes_missing": [], "notes": author_notes(ctx, pages, today),
              "primary_sources": 0, "primary_links": 0, "review_pages": 0,
              "review_q": 0, "mixed": 0, "verified": 0,
              "labs": len(labs), "lab_run": 0, "block_refs": 0,
              "block_refs_lost": [], "console": 0, "callouts": 0,
              "quiz_opts": 0,
              "langs": set()}

    if SRC.exists():
        shutil.rmtree(SRC)
    SRC.mkdir(parents=True)

    for p in pages:
        rel = index[p.id]
        target = SRC / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(transform(p, rel, index, abbr, report,
                                    next_of.get(p.id), today=today,
                                    gloss=gloss, sources_reg=sources_reg,
                                    titles=titles,
                                    labs=topic_labs.get(p.id)),
                          encoding="utf-8")
        report["pages"] += 1

    verified_text, report["verified"] = page_verified(route, index)
    generated = {
        "index.md": page_index(ctx, pages, index, today),
        "map.md": page_map(ctx, pages, index, report, titles, topic_labs),
        "labs.md": page_labs(labs, by_id, index),
        "glossary.md": page_glossary(glossary, index, titles),
        "tags.md": page_tags(ctx),
        "mapping.md": page_mapping(ctx, pages, index),
        "verified.md": verified_text,
        "attributions.md": page_attributions(),
    }
    for name, text in generated.items():
        (SRC / name).write_text(text.rstrip("\n") + "\n", encoding="utf-8")
        report["generated"] += 1

    # Страницы лаб (А8): README каждой лабораторной с обратной ссылкой на тему.
    (SRC / "labs").mkdir(exist_ok=True)
    for lab in labs:
        rel = f"labs/{lab['slug']}.md"
        (SRC / rel).write_text(page_lab(lab, by_id.get(lab["topic"]), index)
                               .rstrip("\n") + "\n", encoding="utf-8")
        report["generated"] += 1

    # Страницы этапов — решения оператора 2026-10-01: «Повторение» (вопросы
    # пройденного и смешанные задачи) и сводка этапа. Собираются из самих тем
    # и лабораторных, поэтому разойтись с корпусом им нечем.
    topics_cfg = vc.load_yaml(TOPICS_YAML)
    sub_titles = {(int(s["num"]), str(sub["num"])): str(sub.get("title") or sub["num"])
                  for s in (topics_cfg.get("stages") or [])
                  for sub in (s.get("subsections") or [])}
    fn_cache: dict[str, dict[str, str]] = {}

    def footnotes_of(p: vc.Page) -> dict[str, str]:
        if p.id not in fn_cache:
            fn_cache[p.id] = topic_footnotes(p)
        return fn_cache[p.id]

    by_stage: dict[str, list[vc.Page]] = {}
    for p in pages:
        by_stage.setdefault(str(p.front.get("stage")), []).append(p)

    stage_extras: dict[str, list[str]] = {}
    for stage in ctx.tax["stages"]:
        group = by_stage.get(stage["slug"], [])
        if stage.get("excluded") or not group:
            continue
        upto = stage_order[stage["slug"]]
        stage_dir = ctx.stages[stage["slug"]]["dir"]
        rel_r = f"{stage_dir}/povtor.md"
        rel_s = f"{stage_dir}/svodka.md"
        (SRC / rel_r).write_text(
            page_stage_review(stage, upto, ctx, pages, labs, footnotes_of,
                              index, rel_r, report, titles).rstrip("\n") + "\n",
            encoding="utf-8")
        (SRC / rel_s).write_text(
            page_stage_summary(stage, group, ctx, sub_titles, footnotes_of,
                               index, rel_s, report, titles).rstrip("\n") + "\n",
            encoding="utf-8")
        stage_extras[stage["slug"]] = [rel_r, rel_s]
        report["review_pages"] += 2

    assets = SRC / "assets"
    (assets / "diagrams").mkdir(parents=True, exist_ok=True)
    # Кэш схем помнит и прежние версии рисунка: имя — хэш от исходника, и
    # правка схемы оставляет старый файл лежать. В сайт идут только те схемы,
    # что стоят на страницах этой сборки, иначе он тащит мёртвые картинки.
    for name in sorted(report["diagram_files"]):
        shutil.copy2(render_diagrams.OUT / name, assets / "diagrams" / name)
    (assets / "extra.css").write_text(EXTRA_CSS + lang_css(report["langs"]),
                                      encoding="utf-8")
    shutil.copy2(SHIM_SRC, assets / "iframe-worker-shim.js")
    # Шрифты сайта (А5): локальные woff2, сайт за ними в сеть не ходит.
    (assets / "fonts").mkdir(exist_ok=True)
    for font in sorted(FONTS_SRC.glob("*.woff2")):
        shutil.copy2(font, assets / "fonts" / font.name)

    write_config(nav_for(ctx, pages, index, stage_extras, topics_cfg, labs))
    return report


def localize_shim() -> int:
    """Переписать ссылку на unpkg в относительный путь к своей копии шима.

    Плагин `offline` вставляет адрес жёстко и настройки для него не имеет,
    поэтому правка идёт по готовому HTML. Считается число переписанных
    страниц: ноль на непустом сайте означает, что плагин сменил разметку и
    проверку офлайновости надо повторить руками.
    """
    changed = 0
    for html in sorted(SITE_DIR.rglob("*.html")):
        text = html.read_text(encoding="utf-8")
        if SHIM_URL not in text:
            continue
        rel = os.path.relpath(SITE_DIR / SHIM_REL, html.parent).replace(os.sep, "/")
        html.write_text(text.replace(SHIM_URL, rel), encoding="utf-8")
        changed += 1
    return changed


def drop_sitemap() -> list[str]:
    """Снести карту сайта, которую движок собирает пустой.

    Карта сайта по схеме sitemaps.org состоит из абсолютных адресов, и взять
    их движку неоткуда: `site_url` не задан. Задавать его нечем — гайдбук
    нигде не опубликован, и выдуманный домен был бы неправдой прямо в
    артефакте. Относительных адресов схема не допускает, так что третьего
    варианта нет.

    Пустой `<urlset>` хуже отсутствия файла: он выглядит как карта сайта, у
    которой ноль страниц. Поэтому файл убирается, а его возвращение ловит
    `tools/check_site.mjs`.
    """
    gone = []
    for name in ("sitemap.xml", "sitemap.xml.gz"):
        path = SITE_DIR / name
        if path.exists():
            path.unlink()
            gone.append(name)
    return gone


def run_mkdocs(args: list[str]) -> int:
    if not MKDOCS.exists():
        print(f"нет {MKDOCS.relative_to(ROOT)}: `make setup`", file=sys.stderr)
        return 1
    return subprocess.call([str(MKDOCS), *args, "--config-file", str(CONFIG_OUT)],
                           cwd=str(ROOT))


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--no-build", action="store_true",
                    help="только staging-дерево, движок не звать")
    ap.add_argument("--serve", action="store_true",
                    help="собрать и открыть локальный сервер")
    ap.add_argument("--addr", default="127.0.0.1:8000", help="адрес для --serve")
    args = ap.parse_args()

    report = stage_tree(date.today())
    print(f"дерево: {report['pages']} тем, {report['generated']} страниц собрано, "
          f"{report['links']} ссылок на темы, {report['gloss']} ссылок на "
          f"глоссарий, {report['stale']} плашек просрочки, "
          f"{report['skip']} маркеров «можно отложить», "
          f"{report['abbr']} раскрытий "
          f"аббревиатур, {report['diagrams']} схем, "
          f"{report['footnotes']} сносок ({report['footnotes_synth']} "
          f"собрано из списка источников)", file=sys.stderr)
    print(f"решения 2026-10-01: первоисточники на {report['primary_sources']} "
          f"страницах ({report['primary_links']} ссылок), "
          f"{report['review_pages']} страниц этапов ({report['review_q']} "
          f"вопросов повторения, {report['mixed']} смешанных задач), "
          f"«на чём проверено»: {report['verified']} записей, "
          f"{report['labs']} лаб (строка запуска дописана в "
          f"{report['lab_run']} тем)", file=sys.stderr)
    for line in report["diagrams_failed"]:
        print(f"  схема не нарисована — {line}", file=sys.stderr)
    print(f"решения 2026-10-02: {report['block_refs']} ссылок на блоки "
          f"переписано названиями, {report['callouts']} врезок, "
          f"{report['console']} листингов-сеансов терминала", file=sys.stderr)
    for line in report["block_refs_lost"]:
        print(f"  ссылка на блок без блока — {line}", file=sys.stderr)
    for line in report["footnotes_missing"]:
        print(f"  сноска без определения — {line}", file=sys.stderr)
    for line in report["notes"]:
        print(f"  автору: {line}", file=sys.stderr)
    print(f"конфиг: {CONFIG_OUT.relative_to(ROOT)} (наследует "
          f"{CONFIG_IN.name})", file=sys.stderr)

    if args.no_build:
        return 0
    if args.serve:
        return run_mkdocs(["serve", "--dev-addr", args.addr])
    code = run_mkdocs(["build", "--clean"])
    if code == 0:
        n = localize_shim()
        print(f"шим поиска локализован на {n} страницах", file=sys.stderr)
        gone = drop_sitemap()
        print(f"карта сайта не собирается: {', '.join(gone) or 'нечего сносить'} "
              f"(адрес публикации не задан, пустой urlset — не карта)",
              file=sys.stderr)
        print(f"сайт: {SITE_DIR.relative_to(ROOT)}/index.html", file=sys.stderr)
    return code


if __name__ == "__main__":
    sys.exit(main())
