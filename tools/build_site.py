#!/usr/bin/env python3
"""Сборка сайта: темы и сгенерированные страницы → MkDocs Material.

Одно правило держит всю сборку: `content/` только читается. Всё, что нужно
дописать к теме — ссылки вместо идентификаторов, картинку вместо схемы,
раскрытия аббревиатур, — дописывается в копии, в staging-дереве `build/site-src`.
Исходник темы остаётся тем, что автор написал и что читают линтеры; сайт —
производная, и его можно снести целиком в любой момент.

Что сборщик делает с темой

  * frontmatter из 27 полей сводится к четырём, которые понимает движок
    (`title`, `description`, `status`, `tags`); остальные со шапки убраны
    решением оператора 2026-08-24 (свод 4.1) и на страницу не попадают.
    Исключение одно — условие `skip_if`, о нём свой пункт ниже;
  * всё от заголовка «## N. Источники» до конца файла отрезается: «Каркас
    этапа», «Скоропортящийся слой» и «Маркеры уверенности» пишутся для аудита
    и читателю не показываются (решение оператора 2026-08-31). Сам список
    источников с 2026-10-01 возвращён на страницу в другом виде: блок
    «Первоисточники» собирается из поля `sources` темы и реестра
    `sources.yaml` — название, издатель, версия и адрес каждого документа.
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
  * ограждённый блок `mermaid` заменяется на нарисованный SVG
    (`tools/render_diagrams.py`), потому что сайт открывается с диска и скрипт
    из сети загрузить не может;
  * в конец страницы вклеиваются определения аббревиатур из `glossary.yaml` —
    те, что на странице действительно встретились. Читатель видит раскрытие по
    наведению, а канон написания остаётся один (6.3);
  * номера блоков пересчитываются подряд с единицы: в исходнике стоит номер
    слота канона, и пропущенный слот оставлял на странице дыру («0, 1, 3»).
    Вместе с заголовками переписываются ссылки на номер блока в прозе;
  * первое вхождение термина глоссария на странице становится ссылкой на его
    статью в глоссарии (9.5 п. 14). Ищется в прозе вне кода, заголовков и
    цитат — теми же написаниями и тем же стеммингом, что `glossary_lint.py`;
  * тема, чья ревизия просрочена более чем вдвое, получает плашку «может
    быть устаревшим» (9.6 п. 20). Считается в календарных месяцах — так же,
    как линтер `validate_content.py`: единицы у сборки и проверки одни;
  * тема с полем `skip_if` получает под шапкой, после абзаца «Уровень …»,
    строку «можно отложить, если …» (9.5 п. 10): маркер подсказывает, когда
    тему законно отложить, сам маршрут от него не меняется. Поля нет —
    строки нет.

Что сборщик генерирует сам: страницу входа, карту тем, маппинг-индекс внешних
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

# Статус темы читателю: словарь `statuses` из `taxonomy.yaml` — машинные
# значения, и на странице они стоят словами. Подписи те же, что у плашки
# статуса в оглавлении (`mkdocs.yml`, `extra.status`).
STATUS_WORD = {"stub": "заглушка", "draft": "черновик", "published": "готова"}


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
                   taken: list[tuple[int, int, str]], report: dict
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
    """Мета для движка: четыре поля вместо двадцати семи."""
    meta = {
        "title": one_line(page.front.get("title") or page.id),
        "description": one_line(page.front.get("summary") or ""),
        "status": str(page.front.get("status") or "stub"),
    }
    tags = page.front.get("tags") or []
    if tags:
        meta["tags"] = list(tags)
    dumped = yaml.safe_dump(meta, allow_unicode=True, sort_keys=False,
                            default_flow_style=False, width=10 ** 6)
    return f"---\n{dumped}---\n"


# ── сплошная нумерация блоков ────────────────────────────────────────────────
#
# В исходнике номер блока — номер слота канона (`SCHEMA.md` § 4): «Механика»
# всегда 3, «Как ловится автоматикой» всегда 8, и по этому номеру проверки
# `C-BLOCK-*` сравнивают блоки разных тем между собой. Тема, которой слот не
# нужен, слот пропускает, и в исходнике темы L2 номера идут 0, 1, 3, 5, 6, 9.
# Читателю такой номер не сообщает ничего, кроме дыры: куда делась двойка.
# Решение оператора 2026-08-26: на странице номер считается из порядка блоков,
# с единицы и подряд. Исходник при этом не меняется — как и всё остальное в
# этой сборке, номер переписывается в копии.
#
# Вместе с заголовками переписываются ссылки на номер блока в прозе («правило
# SAST из блока 8»): без этого перенумерация уводила бы их на соседний блок.
# Ссылки ищутся по `prose_spans`, где ограждённые блоки забиты пробелами, —
# «блок 1: 2175 обращений к оракулу» в листинге `padding-oracle` относится к
# блоку шифра, а не к блоку скелета, и переписывать его нельзя.

BLOCK_HEAD_RE = re.compile(r"^##[ \t]+(\d+)\.[ \t]", re.M)
BLOCK_REF_RE = re.compile(r"блок\w*[ \t]+(\d+(?:[ \t]*(?:,|и|—)[ \t]*\d+)*)")
REF_NUM_RE = re.compile(r"\d+")

# Хвост темы для аудита: «Источники» и всё за ними («Каркас этапа»,
# «Скоропортящийся слой», «Маркеры уверенности») на страницу не выносятся —
# решение оператора 2026-08-31. Признак — заголовок, а не номер: у двух
# скелетов он разный, а после перенумерации на странице — третий.
SOURCES_HEAD_RE = re.compile(r"^##[ \t]+\d+\.[ \t]+Источники[ \t]*$", re.M)

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


def renumber_blocks(page: vc.Page) -> list[tuple[int, int, str]]:
    """Правки, от которых номера блоков идут подряд: заголовки и ссылки на них."""
    spans = page.doc.prose_spans
    order: dict[int, int] = {}
    for m in BLOCK_HEAD_RE.finditer(spans):
        order.setdefault(int(m.group(1)), len(order) + 1)

    out: list[tuple[int, int, str]] = []
    for m in BLOCK_HEAD_RE.finditer(spans):
        was = int(m.group(1))
        if order[was] != was:
            out.append((m.start(1), m.end(1), str(order[was])))
    for m in BLOCK_REF_RE.finditer(spans):
        for num in REF_NUM_RE.finditer(m.group(1)):
            was = int(num.group(0))
            if order.get(was, was) == was:
                continue
            at = m.start(1) + num.start()
            out.append((at, at + len(num.group(0)), str(order[was])))
    return out


# Шапка темы — абзац «Уровень **L2** · время…» сразу под заголовком. Класс
# ставит сборка: CSS приглушает шапку темы и только её (раньше селектор
# `h1 + p` гасил первый абзац любой страницы, включая главную и глоссарий).
LEAD_START_RE = re.compile(r"^Уровень \*\*", re.M)


def mark_lead(body: str) -> str:
    m = LEAD_START_RE.search(body)
    if not m:
        return body
    end = body.find("\n\n", m.start())
    if end < 0:
        end = len(body)
    return body[:end] + "\n{ .topic-lead }" + body[end:]


def insert_stale_note(body: str) -> str:
    """Плашка 9.6 п. 20 — сразу под заголовком, до шапки."""
    m = re.search(r"^# [^\n]*$", body, re.M)
    at = m.end() if m else 0
    return body[:at] + "\n\n" + STALE_NOTE + body[at:]


def insert_skip_note(body: str, condition: str) -> str:
    """Строка «можно отложить» (9.5 п. 10) — под шапкой, после lead-абзаца.

    Поле `skip_if` держит условие одной фразой, которое читатель проверяет на
    себе (SCHEMA § 3.1); маршрут от маркера не ветвится. Печатается той же
    приглушённой строкой, что шапка, — со своим классом и засечкой слева,
    иначе две строки подряд сливаются. Темы без lead-абзаца в корпусе нет
    (C-HEAD-TIME), но если он не нашёлся, страницу ломать незачем.
    """
    m = LEAD_START_RE.search(body)
    if not m:
        return body
    end = body.find("\n\n", m.start())
    if end < 0:
        end = len(body)
    note = f"**Можно отложить, если** {condition}.\n{{ .topic-skip }}"
    return body[:end] + "\n\n" + note + body[end:]


# ── блок «Лаба»: строка запуска ──────────────────────────────────────────────
#
# Решение оператора 2026-10-01 (А8): строка `cd pilot/lab/…` была на одной
# странице из 37 с лабой, и читатель должен был сам догадаться, что каталог —
# это путь в репозитории рядом с `site/`. Сборка дописывает в конец блока
# «Лаба» команду перехода и команды прогона (из README лабы) со ссылкой на
# страницу лабы, где инструкция лежит целиком.

LAB_BLOCK_HEAD_RE = re.compile(r"^##[ \t]+\d+\.[ \t]+Лаба[ \t]*$", re.M)
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
    edits += renumber_blocks(page)

    for m in mdtext.FENCE_RE.finditer(raw):
        if m.group("info").strip().lower() != "mermaid":
            continue
        try:
            svg = render_diagrams.render(m.group("body"))
        except render_diagrams.Unavailable as exc:
            report["diagrams_failed"].append(f"{page.id}: {exc}")
            continue
        target = link_to(page_rel, f"assets/diagrams/{svg.name}")
        # Текстовая замена схемы — абзац «Описание схемы» под ней, он предписан
        # 7.2; в `alt` идёт короткая подпись, чтобы читалка не пересказывала
        # картинку дважды.
        edits.append((m.start(), m.end(),
                      f"![Схема (описание — в абзаце под ней)]({target}){{ .diagram }}"))
        report["diagrams"] += 1
        report["diagram_files"].add(svg.name)

    for m in mdtext.CODE_SPAN_RE.finditer(page.doc.prose_spans):
        target_id = m.group(2).strip()
        if target_id == page.id or target_id not in index:
            continue
        # Подпись ссылки — название темы, а не её идентификатор (WCAG 2.4.4,
        # решение оператора 2026-10-01, А1): из «`idor`» назначение ссылки не
        # читается, из «Горизонтальная эскалация, IDOR» — читается.
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
        edits += glossary_links(page, page_rel, raw, gloss, edits, report)

    body = apply_edits(raw, edits)
    body = mark_lead(body)
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

    # «Первоисточники» — решение оператора 2026-10-01 (реестр RN-13): список
    # документов с адресами, по которым сверена тема. Срезанный хвост аудита
    # он не возвращает: блок собирается из поля `sources` и реестра, а не из
    # текста «Источников».
    if sources_reg:
        block, n_sources = primary_sources(page, sources_reg)
        if block:
            body = body.rstrip("\n") + "\n\n" + block + "\n"
            report["primary_sources"] += 1
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


def page_index(ctx: vc.Ctx, pages: list[vc.Page], index: dict[str, str],
               today: date) -> str:
    by_stage: dict[str, list[vc.Page]] = {}
    for p in pages:
        by_stage.setdefault(str(p.front.get("stage")), []).append(p)

    rows = []
    for stage in ctx.tax["stages"]:
        if stage.get("excluded"):
            continue
        num = int(stage["num"])
        group = by_stage.get(stage["slug"], [])
        first = f"[к темам]({link_to('index.md', index[group[0].id])})" if group else "—"
        time = sum(int(p.front.get("time_min") or 0) for p in group)
        rows.append(f"| {num} | {stage['title']} | {len(group)} | "
                    f"{time or '—'} | {first} |")

    total_time = sum(int(p.front.get("time_min") or 0) for p in pages)
    # Столбец «Написано» убран 2026-08-24: сколько тем каждого уровня успело
    # написаться — счётчик хода работ, а не свойство учебника.
    level_rows = [
        f"| {d} | {ctx.tax['depths'][d]['meaning']} | "
        f"{ctx.tax['depths'][d]['words'][0]}–{ctx.tax['depths'][d]['words'][1]} слов |"
        for d in sorted(ctx.depths)
    ]

    # Этап 6 исключён из скоупа, но номер в плане занят, и без пояснения скачок
    # 5 → 7 в таблице выглядит потерянным этапом (находка X-NAV-01).
    skip_notes = "; ".join(
        f"этап {s['num']} «{s['title']}» исключён из скоупа, поэтому после "
        f"этапа {int(s['num']) - 1} идёт этап {int(s['num']) + 1}"
        for s in ctx.tax["stages"] if s.get("excluded"))
    skip_note = (f"Нумерация этапов сохранена из плана: {skip_notes}.\n\n"
                 if skip_notes else "")

    return f"""---
title: Начало
description: Учебник по прикладной безопасности приложений — с чего начать чтение.
---

{GENERATED}

# AppSec-гайдбук

Учебник, который пишется, чтобы уметь: читать чужой код и видеть в нём дефект,
объяснять механизм словами и проверять утверждения по первоисточнику. Каждая
тема самодостаточна — механизм объяснён здесь, а не по ссылке на чужую статью.

Гайд учит защите и предназначен для обучения: применяйте описанные приёмы
только к собственным системам и учебным стендам. Разборы уязвимостей ведутся
на запатченных версиях и локальных лабораторных.

## Как читать тему

Тема идёт по одному и тому же скелету: «Коротко» → механизм → код → как чинится
→ как проверить → чеклист ревью → «Проверь себя», а в конце страницы — ссылка
«Дальше» на следующую тему маршрута. Порядок блоков не меняется; на коротких
уровнях часть из них не пишется. Читать сплошь не нужно: «Коротко» и «Чеклист
ревью» работают отдельно.

Сразу после «Коротко» тема задаёт два-три предвопроса по главному из того, что
впереди. Ответьте на них до чтения, даже если не уверены: нужна собственная
догадка, с которой текст дальше сравнится, а неверный ответ ничего не портит.
Ответ на каждый предвопрос прямо сказан в тексте темы, и вопрос ещё вернётся —
в «Проверь себя» и на странице «Повторение» этапа.

В конце каждого этапа стоят две страницы, которые сборка собирает из самих
тем: «Повторение» — вопросы на пройденное и задачи без подписей, «Этап
коротко» — все «Коротко» подряд и общий чеклист ревью.

Уровень темы стоит в её шапке и говорит, до чего доводит чтение.

| Уровень | Что даёт | Норма объёма |
|---|---|---|
{chr(10).join(level_rows)}

Времени на прочтение и разбор — {total_time} мин на {len(pages)} тем; оценка
стоит в шапке каждой темы и там же разложена на теорию, практику и самопроверку.

## Чем этот гайд не является

- Не справочник по эксплуатации и не сборник пейлоадов.
- Не курс с проверкой заданий и наставником.
- Не юридическая консультация по нормативке РФ.
- Не покрывает реверс-инжиниринг, AppSec встраиваемых систем и защиту сетевого
  периметра.
- Не гарантирует трудоустройство.

## Этапы

| № | Этап | Тем | Минут | |
|---|---|---|---|---|
{chr(10).join(rows)}

{skip_note}## Что где лежит

- [Карта тем]({link_to('index.md', 'map.md')}) — все темы с уровнем, временем и
  предпосылками; там же видно, каких тем ещё нет.
- [Лабы]({link_to('index.md', 'labs.md')}) — {len(ctx.labs)} практических работ:
  каждая привязана к своей теме и запускается локально, из каталога `pilot/lab/`
  репозитория.
- [Маппинг-индекс]({link_to('index.md', 'mapping.md')}) — обратный ход: номер
  CWE, ASVS, WSTG или Top 10 — темы, которые его разбирают.
- [Глоссарий]({link_to('index.md', 'glossary.md')}) — термины и одно написание
  на весь сайт.
- [Теги]({link_to('index.md', 'tags.md')}) — фасеты: тема попадает в несколько.
- [На чём проверено]({link_to('index.md', 'verified.md')}) — версии инструментов,
  на которых темы проверялись прогоном: по списку видно, что перечитать при
  выходе новой версии.

Сайт собран {today.isoformat()} и открывается с диска: ни одна страница не ходит
в сеть, поиск тоже работает офлайн.
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
            out.append("| Тема | Уровень | Мин | Статус | Требует | Лаба |")
            out.append("|---|---|---|---|---|---|")
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
                    f"| {STATUS_WORD.get(str(p.front.get('status')), '—')} "
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

/* Схемы нарисованы тёмным по белому: на тёмной теме сайта картинке нужен свой
   фон, иначе текст схемы сливается с полем страницы. */
.md-typeset img.diagram {
  background: #fff;
  padding: 0.7rem;
  border-radius: 0.2rem;
  box-shadow: 0 0 0 1px rgba(0, 0, 0, 0.07);
}

/* Шапка темы — вторая копия frontmatter для человека. Она стоит сразу под
   заголовком и не должна спорить с ним весом. Класс ставит сборка: селектор
   вида `h1 + p` гасил первый абзац любой страницы, включая главную. */
.md-typeset p.topic-lead {
  font-size: 0.8rem;
  line-height: 1.5;
  color: var(--md-default-fg-color--light);
}

/* Маркер «можно отложить» (9.5 п. 10) — строка сразу под шапкой темы. Та же
   приглушённость, что у шапки, плюс засечка слева: без неё строка сливается
   со строкой уровня в один абзац. */
.md-typeset p.topic-skip {
  font-size: 0.8rem;
  line-height: 1.5;
  color: var(--md-default-fg-color--light);
  border-left: 0.15rem solid var(--md-accent-fg-color);
  padding-left: 0.6rem;
}

/* Код внутри ссылки в тёмной теме: штатный #5e8bde на фоне кода даёт 4,2:1
   при норме 4,5:1 (WCAG 1.4.3). Светлее, из той же ссылочной гаммы: на фоне
   кода slate выходит около 5,4:1. */
[data-md-color-scheme="slate"] .md-typeset a code {
  color: #7ba0e8;
}

/* Таблицы карты тем длинные: заголовок остаётся видимым. */
.md-typeset table:not([class]) th {
  position: sticky;
  top: 0;
}

/* Кегль текста 18 px (PLAYBOOK 7.7, норма 17–19 px). Тема задаёт корень в
   процентах ступенями — 125 % (20 px), от 100 em 137,5 % (22 px), от 125 em
   150 % (24 px) — поэтому кегль перезадаётся на каждой ступени. Кегль кода
   тема считает сама как 0,85em от текста: выходит 15,3 px, норма «не меньше
   15 px» держится без отдельного правила. Печатная ступень повторяет тему:
   без неё базовое правило ниже (оно позже в каскаде при той же специфичности)
   затирало бы печатный кегль. */
.md-typeset { font-size: 0.9rem; }
@media screen and (min-width: 100em) {
  .md-typeset { font-size: 0.82rem; }
}
@media screen and (min-width: 125em) {
  .md-typeset { font-size: 0.75rem; }
}
@media print {
  .md-typeset { font-size: 0.68rem; }
}

/* Интерлиньяж листинга 1,45 (тема даёт 1,4). */
.md-typeset pre > code { line-height: 1.45; }

/* Код и листинги — JetBrains Mono: ноль с точкой не спутаешь с «O», кириллица
   в комплекте. Файлы лежат в `assets/fonts/`, в сеть сайт не ходит (OFL 1.1,
   см. страницу «Атрибуции и лицензии»). Переменная `--md-code-font` — первое
   звено цепочки `--md-code-font-family`: за ним остаются системные запасные
   гарнитуры темы. */
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
:root { --md-code-font: "JetBrains Mono"; }

/* Лигатур в коде быть не должно: стрелка вместо `->` — это уже другой текст.
   У темы правило есть; здесь оно продублировано, потому что гарнитура сменилась
   на ту, где лигатуры реально нарисованы. */
.md-typeset code,
.md-typeset kbd,
.md-typeset pre {
  font-variant-ligatures: none;
  font-feature-settings: "liga" 0, "calt" 0;
}
"""


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


def primary_sources(page: vc.Page, registry: dict[str, dict]) -> tuple[str, int]:
    """Блок «Первоисточники» для страницы темы и число документов в нём."""
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
    if not items:
        return "", 0
    return ("## Первоисточники\n\n"
            "Тема сверена по этим документам; если текст и документ расходятся, "
            "верен документ.\n\n" + "\n".join(items)), len(items)


# ── заимствование текста тем ─────────────────────────────────────────────────

NUM_ITEM_RE = re.compile(r"^(\d+)\.[ \t]+")


def block_titled(page: vc.Page, word: str) -> vc.Block | None:
    return next((b for b in page.blocks if word in b.title), None)


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

Страница собрана из того, что уже написано: вопросы — из блоков «Предвопросы»
и «Проверь себя» пройденных тем, функции — из лабораторных. Набор меняется,
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
                      f"блоках «Как выглядит в коде» и «Как чинится».")
            parts.append(f"```{lang}\n{code}\n```\n\n"
                         f"<details markdown=\"1\">\n<summary>Ответ</summary>\n\n"
                         f"{answer}\n\n</details>\n")

    if needed:
        parts.append("")
        parts += [f"[^{label}]: {text}" for label, text in needed.items()]
    return "\n".join(parts)


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

Конденсат этапа: блоки «Коротко» всех тем подряд и за ними общий чеклист
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
              "labs": len(labs), "lab_run": 0}

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
    (assets / "extra.css").write_text(EXTRA_CSS, encoding="utf-8")
    shutil.copy2(SHIM_SRC, assets / "iframe-worker-shim.js")
    # Шрифт листингов (А5): локальные woff2, сайт за ними в сеть не ходит.
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
