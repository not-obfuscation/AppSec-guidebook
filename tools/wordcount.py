#!/usr/bin/env python3
"""Объём темы: вердикт по норме 3.1 и две справочные метрики.

    python tools/wordcount.py content/stage-0/*.md
    python tools/wordcount.py --json content/stage-0/*.md

Свод (`PLAYBOOK.md` 3.1) задаёт норму объёма по уровню глубины, но требует
в каждой теме и служебный аппарат — состав блоков, описание схемы, каркас
этапа, скоропортящийся слой, маркеры уверенности, блок идентификации под
заголовком (9.6 п. 21, 11.2 п. 12, часть 4). В норму этот аппарат не заложен:
на темах этапа 0 он стоит 200–260 слов. Решение оператора от 2026-08-23:
**норма относится к тексту без служебного аппарата**, готовые тексты не
режутся. Метод подсчёта назван в своде рядом с нормой (3.1), здесь он
исполняется.

Три метрики, из них решает одна.

`текст`  — вердиктная: проза без служебного аппарата. Из подсчёта исключены
           frontmatter; заголовок h1 и шапка под ним («Уровень **L2** ·
           время …») — она повторяет данные frontmatter; абзац «Что прочитать
           сначала: …» — это навигация; абзацы «Описание схемы.»; блок 14
           «Источники» и всё, что стоит за ним (каркас этапа,
           скоропортящийся слой, маркеры уверенности); ограждённые листинги;
           ответы под `<details>`; два обязательных абзаца — «Зачем это в
           работе AppSec-инженера.» и «Откуда это взялось» (решение оператора
           от 2026-08-23, свод 3.1 п. 8: свод требует их от каждой темы
           независимо от уровня, в норму не заложил, а на L3 они съедали до
           двух пятых бюджета).
`проза`  — справочная: тело без листингов, без ответов под `<details>` и без
           блока 14. Метрика первой приёмки — по ней считаны находки Ф-09
           и Ф-42, поэтому она остаётся в выводе.
`тело`   — справочная: весь текст после frontmatter, вместе с листингами.

Правила: `C-VOL-OVER` — выше нормы уровня, `C-VOL-UNDER` — ниже,
`C-VOL-DEPTH` — уровень в шапке не распознан, объём не с чем сверять.
Уровни правил — `STYLE.md` § 1.1, состав метрики — `SCHEMA.md` § 3.2.
"""

import argparse
import json
import re
import sys
from pathlib import Path

# Норма 3.1 свода. Одно место на весь инструмент: расхождение таблицы свода и
# кода — дефект обвязки, а не повод держать два числа.
NORM = {"L1": (2500, 3500), "L2": (800, 1700), "L3": (300, 500)}

FRONT = re.compile(r"\A---\n(.*?\n)---\n", re.S)
DEPTH = re.compile(r"^depth:\s*(\S+)", re.M)
FENCE = re.compile(r"^```.*?^```", re.M | re.S)
DETAILS = re.compile(r"<details>.*?</details>", re.S)
SOURCES = re.compile(r"^## 14\..*\Z", re.M | re.S)
# Заголовок и шапка: h1, за ним абзац «Уровень **L2** · время …» до пустой
# строки. По `SCHEMA.md` § 2 это данные frontmatter, набранные для человека, а
# не текст темы. Абзац о границах темы, если он есть, считается: после чистки
# 2026-08-24 он говорит о предмете, а не о составе блоков.
IDENT = re.compile(r"\A\s*^#\s.*?\n\n[Уу]ровень\s+\*\*L[123]\*\*.*?(?:\n\n|\Z)",
                   re.M | re.S)
SERVICE = re.compile(
    r"^(?:Что прочитать сначала:|\*\*Описание схемы\.\*\*|\*\*Скоропортящийся слой\.\*\*"
    r"|\*\*Маркеры уверенности\.\*\*|Каркас этапа:).*?(?:\n\n|\Z)",
    re.M | re.S,
)
# Два обязательных абзаца свода (3.1 п. 8). Признак — абзац целиком: маркер
# «Зачем это в работе AppSec-инженера.» открывает свой абзац всегда, а «Откуда
# это взялось» законно и абзацем основного потока, и внутри врезки «Глубже»
# (оговорка `validate_content.py`), поэтому здесь выбрасывается абзац, в
# котором эта строка стоит, вместе с врезкой-обёрткой.
WHY_PARA = re.compile(r"^\*\*Зачем это в работе AppSec-инженера\.\*\*.*?(?:\n\n|\Z)",
                      re.M | re.S)
ORIGIN_PARA = re.compile(r"(?:\A|(?<=\n\n))(?:(?!\n\n).)*?Откуда это взялось.*?(?:\n\n|\Z)",
                         re.S)
WORD = re.compile(r"[0-9A-Za-zА-Яа-яЁё][0-9A-Za-zА-Яа-яЁё'’-]*")


def depth_of(text: str) -> tuple[str | None, int]:
    """Уровень темы и номер строки, где он объявлен."""
    front = FRONT.match(text)
    if not front:
        return None, 1
    m = DEPTH.search(front.group(1))
    if not m:
        return None, 1
    line = text[: front.start(1) + m.start()].count("\n") + 1
    return m.group(1).strip().strip("'\""), line


def counts(text: str) -> tuple[int, int, int]:
    body = FRONT.sub("", text)
    prose = SOURCES.sub("", DETAILS.sub("", FENCE.sub("", body)))
    core = ORIGIN_PARA.sub("", WHY_PARA.sub("", SERVICE.sub("", IDENT.sub("", prose))))
    return (
        len(WORD.findall(body)),
        len(WORD.findall(prose)),
        len(WORD.findall(core)),
    )


def check(path: Path) -> tuple[tuple[int, int, int], str | None, list[dict]]:
    text = path.read_text(encoding="utf-8")
    body, prose, core = counts(text)
    depth, line = depth_of(text)
    out: list[dict] = []
    if depth not in NORM:
        out.append(
            {
                "path": str(path),
                "line": line,
                "col": 0,
                "rule": "C-VOL-DEPTH",
                "level": "warning",
                "message": (
                    f"уровень {depth!r} не из L1/L2/L3 — объём {core} слов "
                    "не с чем сверять (свод 3.1)"
                ),
            }
        )
    else:
        lo, hi = NORM[depth]
        if core < lo:
            out.append(
                {
                    "path": str(path),
                    "line": line,
                    "col": 0,
                    "rule": "C-VOL-UNDER",
                    "level": "error",
                    "message": (
                        f"{core} слов без служебного аппарата — ниже нормы "
                        f"{depth} {lo}–{hi} на {lo - core} (свод 3.1)"
                    ),
                }
            )
        elif core > hi:
            out.append(
                {
                    "path": str(path),
                    "line": line,
                    "col": 0,
                    "rule": "C-VOL-OVER",
                    "level": "error",
                    "message": (
                        f"{core} слов без служебного аппарата — выше нормы "
                        f"{depth} {lo}–{hi} на {core - hi} (свод 3.1)"
                    ),
                }
            )
    return (body, prose, core), depth, out


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description="объём темы против нормы 3.1")
    ap.add_argument("paths", nargs="*", help="темы; без аргументов — ничего")
    ap.add_argument("--json", action="store_true",
                    help="замечания машинным форматом, по объекту на строку")
    args = ap.parse_args(argv)

    findings: list[dict] = []
    rows: list[tuple[str, str, tuple[int, int, int]]] = []
    for name in args.paths:
        path = Path(name)
        nums, depth, out = check(path)
        findings.extend(out)
        rows.append((path.name, depth or "?", nums))

    if args.json:
        for f in findings:
            print(json.dumps(f, ensure_ascii=False))
        return 1 if any(f["level"] == "error" for f in findings) else 0

    print(f"{'файл':<34}{'ур.':>5}{'текст':>8}{'норма':>12}{'проза':>8}{'тело':>8}")
    for name, depth, (body, prose, core) in rows:
        lo, hi = NORM.get(depth, (0, 0))
        norm = f"{lo}–{hi}" if depth in NORM else "—"
        mark = "" if depth not in NORM or lo <= core <= hi else "  ←"
        print(f"{name:<34}{depth:>5}{core:>8}{norm:>12}{prose:>8}{body:>8}{mark}")
    errors = [f for f in findings if f["level"] == "error"]
    if errors:
        print()
        for f in errors:
            print(f"  {f['rule']}  {Path(f['path']).name}  {f['message']}")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
