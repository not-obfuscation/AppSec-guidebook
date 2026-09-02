#!/usr/bin/env python3
"""Сверка внешних идентификаторов тем с официальными каталогами.

    python tools/verify_idents.py                      # весь корпус
    python tools/verify_idents.py content/stage-1/*.md # подмножество
    APPSEC_IDENT_CACHE=/tmp/idents python tools/verify_idents.py

Проверяет поля frontmatter `cwe`, `asvs`, `wstg`, `owasp`: каждый
идентификатор обязан существовать в эталонном каталоге — полном XML CWE,
ASVS v5.0.0, WSTG v4.2, OWASP Top 10 изданий 2021 и 2025. Смысл
соответствия («тот ли это CWE») скрипт не оценивает: только существование
и формат.

Сеть не используется: эталоны читаются из локального кэша, который заранее
наполняет `tools/fetch_idents.py`. Каталог кэша — опция `--cache`, переменная
`APPSEC_IDENT_CACHE`, по умолчанию `~/.cache/appsec-idents`. Если кэша нет,
печатается ПРОПУЩЕНО с подсказкой, как его загрузить.

Отчётный скрипт уровня `clones.py`: в `make check` не входит, код возврата
всегда 0, вердикт — в тексте отчёта.
"""

from __future__ import annotations

import argparse
import os
import re
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import yaml  # noqa: E402 — путь до tools/ настраивается выше

import mdtext  # noqa: E402
from paths import ROOT  # noqa: E402

DEFAULT_CACHE = "~/.cache/appsec-idents"

# Поле frontmatter → (файл кэша, формат идентификатора, название каталога).
FIELDS = {
    "cwe": ("cwe.tsv", re.compile(r"^CWE-\d+$"),
            "каталог CWE (cwe.mitre.org, cwec_latest)"),
    "asvs": ("asvs-5.0.0.tsv", re.compile(r"^v5\.0-\d+\.\d+\.\d+$"),
             "ASVS v5.0.0 (OWASP/ASVS, тег v5.0.0)"),
    "wstg": ("wstg-4.2.tsv", re.compile(r"^WSTG-v42-[A-Z]{4,5}-\d{2}$"),
             "WSTG v4.2 (OWASP/wstg, тег v4.2)"),
    "owasp": ("owasp-top10.tsv", re.compile(r"^A(0[1-9]|10):20(21|25)$"),
              "OWASP Top 10 2021/2025 (owasp.org/Top10)"),
}


def load_reference(path: Path) -> dict[str, tuple[str, str]]:
    """TSV кэша → {идентификатор: (название, вид)}."""
    out = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        ident, name, kind = line.split("\t")
        out[ident] = (name, kind)
    return out


def front_values(doc, field: str) -> list[str]:
    """Значения поля frontmatter: список строк, пустое поле — пустой список."""
    if not doc.front_text:
        return []
    data = yaml.safe_load(doc.front_text) or {}
    value = data.get(field) or []
    if isinstance(value, str):
        value = [value]
    return [str(v) for v in value]


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("paths", nargs="*", help="темы; по умолчанию весь корпус")
    parser.add_argument("--cache", help="каталог кэша эталонов")
    args = parser.parse_args(argv)

    cache = Path(args.cache
                 or os.environ.get("APPSEC_IDENT_CACHE", DEFAULT_CACHE)
                 ).expanduser()
    references = {}
    missing = []
    for field, (fname, _fmt, _label) in FIELDS.items():
        path = cache / fname
        if path.is_file():
            references[field] = load_reference(path)
        else:
            missing.append(path)
    if missing:
        print("ПРОПУЩЕНО: нет локального кэша эталонов:")
        for path in missing:
            print(f"  {path}")
        print("Загрузка (единственный скрипт, который ходит в сеть):")
        print("  python tools/fetch_idents.py")
        print(f"  # или в другой каталог: python tools/fetch_idents.py КАТАЛОГ")
        print("  # и тогда проверка: python tools/verify_idents.py --cache КАТАЛОГ")
        return 0

    paths = [Path(p) for p in args.paths] or mdtext.topics()
    stats: Counter = Counter()          # поле → упоминаний
    uniq: dict[str, set] = {f: set() for f in FIELDS}
    bad_format: list[tuple[str, str, str]] = []   # тема, поле, идентификатор
    unknown: list[tuple[str, str, str]] = []      # тема, поле, идентификатор
    for path in paths:
        doc = mdtext.load(path)
        rel = path if not path.is_absolute() else path.relative_to(ROOT)
        for field, (_fname, fmt, _label) in FIELDS.items():
            for ident in front_values(doc, field):
                stats[field] += 1
                uniq[field].add(ident)
                if not fmt.match(ident):
                    bad_format.append((str(rel), field, ident))
                elif ident not in references[field]:
                    unknown.append((str(rel), field, ident))

    print(f"тем проверено: {len(paths)}")
    for field, (_fname, _fmt, label) in FIELDS.items():
        print(f"{field:5} упоминаний: {stats[field]:4}  "
              f"уникальных: {len(uniq[field]):4}  эталон: {label} "
              f"({len(references[field])} записей)")

    if not bad_format and not unknown:
        print("\nрасхождений нет: все идентификаторы существуют в эталонах")
        return 0

    if bad_format:
        print(f"\nнарушен формат ({len(bad_format)}):")
        for rel, field, ident in bad_format:
            print(f"  {rel}: {field}: {ident!r} — не соответствует шаблону "
                  f"поля")
    if unknown:
        print(f"\nнет в эталонном каталоге ({len(unknown)}):")
        for rel, field, ident in unknown:
            print(f"  {rel}: {field}: {ident} — отсутствует в "
                  f"{FIELDS[field][2]}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
