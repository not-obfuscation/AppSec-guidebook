#!/usr/bin/env python3
"""Сборка сайта: темы и сгенерированные страницы → MkDocs Material.

Одно правило держит всю сборку: `content/` только читается. Всё, что нужно
дописать к теме — ссылки вместо идентификаторов, картинку вместо схемы,
раскрытия аббревиатур, — дописывается в копии, в staging-дереве `build/site-src`.
Исходник темы остаётся тем, что автор написал и что читают линтеры; сайт —
производная, и его можно снести целиком в любой момент.

Что сборщик делает с темой

  * frontmatter из 24 полей сводится к четырём, которые понимает движок
    (`title`, `description`, `status`, `tags`); остальные на страницу не
    выносятся вовсе — со шапки они убраны решением оператора 2026-08-24
    (свод 4.1);
  * `` `topic-id` `` в обратных кавычках становится ссылкой на страницу темы.
    В исходниках markdown-ссылок между темами нет и не будет: 9.1 п. 6 требует
    ссылаться идентификатором, а не путём, чтобы переименование каталога не
    ломало текст. Превращение делает сборка;
  * ограждённый блок `mermaid` заменяется на нарисованный SVG
    (`tools/render_diagrams.py`), потому что сайт открывается с диска и скрипт
    из сети загрузить не может;
  * в конец страницы вклеиваются определения аббревиатур из `glossary.yaml` —
    те, что на странице действительно встретились. Читатель видит раскрытие по
    наведению, а канон написания остаётся один (6.3);
  * номера блоков пересчитываются подряд с единицы: в исходнике стоит номер
    слота канона, и пропущенный слот оставлял на странице дыру («0, 1, 3»).
    Вместе с заголовками переписываются ссылки на номер блока в прозе.

Что сборщик генерирует сам: страницу входа, карту тем, маппинг-индекс внешних
каталогов (9.6 п. 24), глоссарий (из того же `glossary.yaml`, что и
`GLOSSARY.md`) и индекс тегов. Сроки ревизии и состояние тем со страниц ушли
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
import os
import re
import shutil
import subprocess
import sys
from datetime import date, timedelta
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
import gen_glossary  # noqa: E402
import mdtext  # noqa: E402
import render_diagrams  # noqa: E402
import validate_content as vc  # noqa: E402
import wordcount  # noqa: E402
from paths import BUILD_DIR, GLOSSARY_YAML, ROOT, SITE_DIR  # noqa: E402

SRC = BUILD_DIR / "site-src"
CONFIG_IN = ROOT / "mkdocs.yml"
CONFIG_OUT = BUILD_DIR / "mkdocs.yml"
MKDOCS = ROOT / ".venv-site" / "bin" / "mkdocs"
SHIM_SRC = ROOT / "tools" / "vendor" / "iframe-worker-shim.js"
SHIM_REL = "assets/iframe-worker-shim.js"

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


# ── тема → страница ──────────────────────────────────────────────────────────


def front_block(page: vc.Page) -> str:
    """Мета для движка: четыре поля вместо двадцати четырёх."""
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


def transform(page: vc.Page, page_rel: str, index: dict[str, str],
              abbr: dict[str, str], report: dict) -> str:
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
        edits.append((m.start(), m.end(),
                      f"[{m.group(0)}]({link_to(page_rel, index[target_id])})"))
        report["links"] += 1

    body = apply_edits(raw, edits)

    tail = [body.rstrip("\n"), ""]
    here = used_abbr(page.doc.prose, abbr)
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

    written_by_stage_num: dict[int, int] = {}
    for slug, group in by_stage.items():
        written_by_stage_num[int(ctx.stages[slug]["num"])] = len(group)
    planned: dict[int, int] = {}
    for meta in ctx.plan.values():
        if not meta["excluded"]:
            planned[meta["stage"]] = planned.get(meta["stage"], 0) + 1

    rows = []
    for stage in ctx.tax["stages"]:
        if stage.get("excluded"):
            continue
        num = int(stage["num"])
        group = by_stage.get(stage["slug"], [])
        first = f"[к темам]({link_to('index.md', index[group[0].id])})" if group else "—"
        time = sum(int(p.front.get("time_min") or 0) for p in group)
        rows.append(f"| {num} | {stage['title']} | {len(group)} из "
                    f"{planned.get(num, 0)} | {time or '—'} | {first} |")

    total_time = sum(int(p.front.get("time_min") or 0) for p in pages)
    # Столбец «Написано» убран 2026-08-24: сколько тем каждого уровня успело
    # написаться — счётчик хода работ, а не свойство учебника.
    level_rows = [
        f"| {d} | {ctx.tax['depths'][d]['meaning']} | "
        f"{ctx.tax['depths'][d]['words'][0]}–{ctx.tax['depths'][d]['words'][1]} слов |"
        for d in sorted(ctx.depths)
    ]

    return f"""---
title: Начало
description: Учебник по прикладной безопасности приложений — с чего начать чтение.
---

{GENERATED}

# AppSec-гайдбук

Учебник, который пишется, чтобы уметь: читать чужой код и видеть в нём дефект,
объяснять механизм словами и проверять утверждения по первоисточнику. Каждая
тема самодостаточна — механизм объяснён здесь, а не по ссылке на чужую статью;
внешние адреса законны только в блоке «Источники».

## Как читать

Тема идёт по одному и тому же скелету: «Коротко» → механизм → код → как чинится
→ как проверить → чеклист ревью → «Проверь себя» → «Дальше» → «Источники».
Порядок блоков не меняется; на коротких уровнях часть из них не пишется. Читать
сплошь не нужно: «Коротко» и «Чеклист ревью» работают отдельно.

Уровень темы стоит в её шапке и говорит, до чего доводит чтение.

| Уровень | Что даёт | Норма объёма |
|---|---|---|
{chr(10).join(level_rows)}

Времени на прочтение и разбор — {total_time} мин на {len(pages)} тем; оценка
стоит в шапке каждой темы и там же разложена на теорию, практику и самопроверку.

## Этапы

| № | Этап | Тем | Минут | |
|---|---|---|---|---|
{chr(10).join(rows)}

Столбец «Тем» читается как «готово из запланированного»: число справа — все
темы этапа, и оно не меняется от того, сколько из них уже написано.

## Что где лежит

- [Карта тем]({link_to('index.md', 'map.md')}) — все темы с уровнем, временем и
  предпосылками; там же видно, каких тем ещё нет.
- [Маппинг-индекс]({link_to('index.md', 'mapping.md')}) — обратный ход: номер
  CWE, ASVS, WSTG или Top 10 — темы, которые его разбирают.
- [Глоссарий]({link_to('index.md', 'glossary.md')}) — термины и одно написание
  на весь сайт.
- [Теги]({link_to('index.md', 'tags.md')}) — фасеты: тема попадает в несколько.

Сайт собран {today.isoformat()} и открывается с диска: ни одна страница не ходит
в сеть, поиск тоже работает офлайн.
"""


def page_map(ctx: vc.Ctx, pages: list[vc.Page], index: dict[str, str],
             report: dict) -> str:
    out = [f"""---
title: Карта тем
description: Все темы гайдбука с уровнем, временем и предпосылками.
---

{GENERATED}

# Карта тем

Порядок внутри этапа тот же, что в оглавлении: тема стоит после тех, на которых
держится. Уровень задаёт подробность, а не самодостаточность: на любом уровне
механизм объяснён своими словами и со своим примером.

Столбец «Требует» и есть карта связей: он называет темы, без которых эта не
читается. Схема тех же связей со страницы убрана решением оператора
2026-08-26 — на 139 темах она давала клубок, по которому ничего не найти, а
7.4 разрешает схему только там, где она объясняет то, чего не объясняет текст.
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
            out.append("| Тема | Уровень | Мин | Статус | Требует |")
            out.append("|---|---|---|---|---|")
            for p in group:
                prereqs = ", ".join(
                    f"[`{q}`]({link_to('map.md', index[q])})" if q in index else f"`{q}`"
                    for q in (p.front.get("prerequisites") or [])) or "—"
                out.append(
                    f"| [{one_line(p.front.get('title'))}]"
                    f"({link_to('map.md', index[p.id])}) "
                    f"| {p.depth} | {p.front.get('time_min')} "
                    f"| {STATUS_WORD.get(str(p.front.get('status')), '—')} "
                    f"| {prereqs} |")
            out.append("")
        if pending:
            out.append("Ещё не написаны:\n")
            for _, meta in pending:
                out.append(f"- {one_line(meta['title'])}")
            out.append("")
    return "\n".join(out)


def page_glossary(glossary: dict, index: dict[str, str]) -> str:
    """Тот же глоссарий, что `GLOSSARY.md`, только ссылки ведут на страницы."""
    link = {tid: link_to("glossary.md", rel) for tid, rel in index.items()}
    text = gen_glossary.render(glossary, link=link)
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


def cwe_release() -> str:
    """Выпуск каталога CWE из записи `cwe-taxonomy` реестра источников."""
    for src in (vc.load_yaml(vc.SOURCES).get("sources") or []):
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


def author_notes(ctx: vc.Ctx, pages: list[vc.Page], today: date) -> list[str]:
    """Авторская бухгалтерия: просрочка ревизии и перекос объёма.

    До 2026-08-26 это была страница сайта «Обслуживание». Решением оператора она
    убрана: сроки ревизии и состояние тем — журнал производства, а читателю на
    них смотреть незачем (тем же решением 4.1 убрало статус из шапки темы).
    Данные не потеряны — они лежат во frontmatter, и сборка печатает их тому,
    кто её запустил.
    """
    overdue, on_time = [], 0
    for p in pages:
        reviewed = p.front.get("reviewed")
        interval = int(p.front.get("review_interval") or 0)
        if not reviewed or not interval:
            continue
        seen = reviewed if isinstance(reviewed, date) else date.fromisoformat(str(reviewed))
        late = (today - (seen + timedelta(weeks=interval))).days
        if late > 0:
            overdue.append((late, p.id))
        else:
            on_time += 1

    notes = []
    if overdue:
        overdue.sort(reverse=True)
        notes.append(f"ревизия просрочена у {len(overdue)} тем из "
                     f"{len(overdue) + on_time} с датой: " + head_tail(
                         f"{tid} на {late} дн." for late, tid in overdue))
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
   заголовком и не должна спорить с ним весом. */
.md-typeset h1 + p {
  font-size: 0.8rem;
  line-height: 1.5;
  color: var(--md-default-fg-color--light);
}

/* Таблицы карты тем длинные: заголовок остаётся видимым. */
.md-typeset table:not([class]) th {
  position: sticky;
  top: 0;
}
"""


# ── сборка ───────────────────────────────────────────────────────────────────


def nav_for(ctx: vc.Ctx, pages: list[vc.Page], index: dict[str, str]) -> list:
    by_stage: dict[str, list[vc.Page]] = {}
    for p in pages:
        by_stage.setdefault(str(p.front.get("stage")), []).append(p)
    nav: list = [{"Начало": "index.md"}]
    for stage in ctx.tax["stages"]:
        group = by_stage.get(stage["slug"], [])
        if not group:
            continue
        nav.append({f"Этап {stage['num']}. {stage['title']}":
                    [index[p.id] for p in group]})
    nav.append({"Справочное": ["map.md", "mapping.md", "tags.md",
                               "glossary.md"]})
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
    abbr = abbreviations(glossary)
    report = {"pages": 0, "links": 0, "abbr": 0, "diagrams": 0,
              "diagrams_failed": [], "generated": 0, "diagram_files": set(),
              "notes": author_notes(ctx, pages, today)}

    if SRC.exists():
        shutil.rmtree(SRC)
    SRC.mkdir(parents=True)

    for p in pages:
        rel = index[p.id]
        target = SRC / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(transform(p, rel, index, abbr, report), encoding="utf-8")
        report["pages"] += 1

    generated = {
        "index.md": page_index(ctx, pages, index, today),
        "map.md": page_map(ctx, pages, index, report),
        "glossary.md": page_glossary(glossary, index),
        "tags.md": page_tags(ctx),
        "mapping.md": page_mapping(ctx, pages, index),
    }
    for name, text in generated.items():
        (SRC / name).write_text(text.rstrip("\n") + "\n", encoding="utf-8")
        report["generated"] += 1

    assets = SRC / "assets"
    (assets / "diagrams").mkdir(parents=True, exist_ok=True)
    # Кэш схем помнит и прежние версии рисунка: имя — хэш от исходника, и
    # правка схемы оставляет старый файл лежать. В сайт идут только те схемы,
    # что стоят на страницах этой сборки, иначе он тащит мёртвые картинки.
    for name in sorted(report["diagram_files"]):
        shutil.copy2(render_diagrams.OUT / name, assets / "diagrams" / name)
    (assets / "extra.css").write_text(EXTRA_CSS, encoding="utf-8")
    shutil.copy2(SHIM_SRC, assets / "iframe-worker-shim.js")

    write_config(nav_for(ctx, pages, index))
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
          f"{report['links']} ссылок на темы, {report['abbr']} раскрытий "
          f"аббревиатур, {report['diagrams']} схем", file=sys.stderr)
    for line in report["diagrams_failed"]:
        print(f"  схема не нарисована — {line}", file=sys.stderr)
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
