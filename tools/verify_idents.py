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

Те же ключи проверяются в `metadata` каждого правила `pilot/semgrep/*.yaml`:
там значение поля — не голый идентификатор, а строка вида «CWE-862: Missing
Authorization», идентификатор стоит в ней первым словом.

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

SEMGREP_DIR = ROOT / "pilot" / "semgrep"

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


def semgrep_file(path: Path) -> tuple[int, list[tuple[str, str, str]]]:
    """Файл правил → (число правил, [(поле, идентификатор, id правила)]).

    В metadata semgrep-правила значение ключа — строка вида «CWE-862: Missing
    Authorization»: идентификатор стоит первым словом, название за ним не
    сверяется. Одно значение или список — как в frontmatter тем.
    """
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    rules = data.get("rules") or []
    out = []
    for rule in rules:
        if not isinstance(rule, dict):
            continue
        meta = rule.get("metadata") or {}
        if not isinstance(meta, dict):
            continue
        for field in FIELDS:
            value = meta.get(field)
            if value is None:
                continue
            if not isinstance(value, list):
                value = [value]
            for item in value:
                parts = str(item).split(None, 1)
                ident = parts[0].rstrip(":") if parts else ""
                out.append((field, ident, str(rule.get("id", "?"))))
    return len(rules), out


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
    bad_format: list[tuple[str, str, str]] = []   # файл, поле, идентификатор
    unknown: list[tuple[str, str, str]] = []      # файл, поле, идентификатор

    def check_ident(where: str, field: str, ident: str) -> None:
        stats[field] += 1
        uniq[field].add(ident)
        fmt = FIELDS[field][1]
        if not fmt.match(ident):
            bad_format.append((where, field, ident))
        elif ident not in references[field]:
            unknown.append((where, field, ident))

    for path in paths:
        doc = mdtext.load(path)
        rel = path if not path.is_absolute() else path.relative_to(ROOT)
        for field in FIELDS:
            for ident in front_values(doc, field):
                check_ident(str(rel), field, ident)

    # metadata правил semgrep — тот же набор ключей и тот же эталон; проверяется
    # всегда целиком, подмножество тем на него не влияет.
    semgrep_files = sorted(SEMGREP_DIR.glob("*.yaml"))
    semgrep_rules = 0
    for path in semgrep_files:
        n_rules, rows = semgrep_file(path)
        semgrep_rules += n_rules
        rel = path.relative_to(ROOT)
        for field, ident, rid in rows:
            check_ident(f"{rel}#{rid}", field, ident)

    print(f"тем проверено: {len(paths)}")
    if SEMGREP_DIR.is_dir():
        print(f"файлов semgrep проверено: {len(semgrep_files)} "
              f"(правил: {semgrep_rules})")
    else:
        print(f"ПРОПУЩЕНО: каталог {SEMGREP_DIR.relative_to(ROOT)} не найден")
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
