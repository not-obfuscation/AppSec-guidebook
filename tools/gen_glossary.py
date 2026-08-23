#!/usr/bin/env python3
"""Сборка `GLOSSARY.md` из `glossary.yaml`.

`glossary.yaml` правится руками, как `sources.yaml`; `GLOSSARY.md` собирается из
него и руками не правится — по той же схеме, что `topics.yaml` из `sources.yaml`.
Флаг `--check` сверяет собранное с лежащим на диске и не пишет ничего: этим
`make check` ловит правку сгенерированного файла.

Порядок разделов — порядок списка `groups` в `glossary.yaml`, порядок терминов
внутри раздела — по алфавиту канонического написания, с русской раскладкой перед
латинской, чтобы латинские аббревиатуры не разрывали русский ряд.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
GLOSSARY_YAML = ROOT / "glossary.yaml"
GLOSSARY_MD = ROOT / "GLOSSARY.md"

HEADER = """<!-- Собрано `tools/gen_glossary.py` из `glossary.yaml`. Не правьте этот файл:
     правки вносятся в `glossary.yaml`, затем `make glossary`. -->

# Глоссарий

Термины, которыми пользуются написанные темы. Одно написание на весь сайт:
у термина здесь одна статья, а его синонимы названы в ней же.
"""


def sort_key(term: str) -> tuple[int, str]:
    """Русское слово раньше латинского, внутри — по алфавиту, без учёта регистра."""
    return (0 if re.match(r"[А-Яа-яЁё]", term) else 1, term.lower())


def topic_paths() -> dict[str, str]:
    """id темы → путь к файлу от корня репозитория.

    Нужен ссылкам «вводится в»: в редакторе и на GitHub такой путь открывается,
    а сборка сайта переписывает ссылки под свою раскладку сама.
    """
    out = {}
    for path in sorted((ROOT / "content").rglob("*.md")):
        m = re.match(r"\A---\n(.*?)\n---\n", path.read_text(encoding="utf-8"), re.S)
        if not m:
            continue
        front = yaml.safe_load(m.group(1)) or {}
        if front.get("id"):
            out[front["id"]] = str(path.relative_to(ROOT))
    return out


def render(data: dict, link: dict[str, str] | None = None) -> str:
    link = topic_paths() if link is None else link
    by_group: dict[str, list[dict]] = {g["id"]: [] for g in data["groups"]}
    for t in data["terms"]:
        by_group[t["group"]].append(t)
    names = {t["id"]: t["term"] for t in data["terms"]}

    out = [HEADER]
    for g in data["groups"]:
        items = sorted(by_group[g["id"]], key=lambda t: sort_key(t["term"]))
        if not items:
            continue
        out.append(f"## {g['title']}\n")
        for t in items:
            out.append(entry(t, names, link))
    return "\n".join(out).rstrip() + "\n"


def entry(t: dict, names: dict[str, str], link: dict[str, str]) -> str:
    lines = [f"### {t['term']} {{ #{t['id']} }}\n"]

    # Пометки идут одной строкой курсивом, поэтому внутри неё выделения нет:
    # вложенные звёздочки markdown разбирает не так, как читается в источнике.
    marks = []
    if t.get("en"):
        marks.append(f"англ. {t['en']}")
    if t.get("abbr"):
        marks.append(f"сокр. {t['abbr']}")
    aliases = [a for a in (t.get("aliases") or []) if a != t.get("abbr")]
    if aliases:
        marks.append("то же: " + ", ".join(f"«{a}»" for a in aliases))
    if marks:
        lines.append("*" + " · ".join(marks) + "*\n")

    lines.append(" ".join(t["definition"].split()) + "\n")

    tail = []
    if t.get("defines"):
        tail.append("вводится в " + ", ".join(
            f"[{d}]({link[d]})" if d in link else d for d in t["defines"]))
    see = [x for x in (t.get("see_also") or []) if x in names]
    if see:
        tail.append("рядом: " + ", ".join(f"[{names[x]}](#{x})" for x in see))
    if t.get("source"):
        tail.append(f"источник: {t['source']}")
    if tail:
        lines.append("*" + "; ".join(tail) + ".*\n")
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--check", action="store_true",
                    help="сверить с файлом на диске, ничего не писать")
    args = ap.parse_args()

    data = yaml.safe_load(GLOSSARY_YAML.read_text(encoding="utf-8"))
    text = render(data)

    if args.check:
        have = GLOSSARY_MD.read_text(encoding="utf-8") if GLOSSARY_MD.exists() else ""
        if have != text:
            print(f"{GLOSSARY_MD.name}: расходится с glossary.yaml, "
                  f"нужен `make glossary`", file=sys.stderr)
            return 1
        print(f"{GLOSSARY_MD.name}: совпадает с glossary.yaml "
              f"({len(data['terms'])} терминов)", file=sys.stderr)
        return 0

    GLOSSARY_MD.write_text(text, encoding="utf-8")
    print(f"{GLOSSARY_MD.name}: {len(data['terms'])} терминов, "
          f"{len(data['groups'])} разделов", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
