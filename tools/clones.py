#!/usr/bin/env python3
"""Клоны между темами: предложения прозы, дословно повторённые в 2+ файлах.

    python tools/clones.py                      # весь корпус
    python tools/clones.py content/stage-2/*.md # подмножество

Отчёт без вердикта — радар для волн фазы 3 плана `PLAN-VOICE.md` (машинная
версия DoD 20 «не повторять вводные абзацы соседних»). Порогов нет, код
возврата всегда 0.

Смотрится только проза: frontmatter, листинги, инлайновый код-разметка и ссылки
заглушает `mdtext`; блоки «Дальше» и «Источники» отрезаются тем же признаком,
что в `lint_style.py`, — заглавия длинны по своей природе; заголовки, таблицы,
шапка и навигация («Что прочитать сначала») вычитаются через
`lint_style.skipped_lines` — метаданные у всех тем одинаковые, и без этого они
забивают список. Границы предложений и понятие «материала» общие с линтером,
чтобы радар и гейт мерили один текст.

Предложение нормализуется: нижний регистр, схлопнутые пробелы, остаются только
кириллица, латиница и цифры. В список попадают предложения от восьми слов,
встреченные в двух и более файлах. Предложение, живущее более чем в десяти
файлах, — каркас («Наследуются всеми темами…», служебные строки скелета): его
повтор предписан сводом, поэтому оно идёт отдельным счётчиком и в список не
попадает.

Ритуал практики из счёта вычитается: клон-счётчик меряет прозу мышления, а не
обвязку лабораторной. Вычитаются два ритуала по признакам разметки. Первый —
зоны: разделы «Лаба» и «Задача» целиком, там унифицированная инструкция
(«Решение лежит в `solution.py`…», «Всё локально…», «Цель одной фразой…») —
одинаковая подача здесь полезна читателю. Второй — формулы-рамки вне этих
зон: вводная строка раздела «Предвопросы» («Попробуйте ответить до чтения…»)
и первая фраза раздела «Как проверить фикс» («Ретест повторяет…»). Сами
разделы несут прозу темы и потому не вычитаются — убирается только формула.
"""

import re
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import mdtext
from lint_style import material, skipped_lines

MIN_WORDS = 8       # короче — совпадение оборота, а не клон
FRAMEWORK_FILES = 10  # больше — осознанный шаблон скелета, а не заимствование

KEEP_RE = re.compile(r"[^0-9A-Za-zА-Яа-яЁё]+")

# Ритуальные зоны: разделы «Лаба» и «Задача» — инструкция практики, одинаковая
# во всех темах сознательно. Признак разметки — заголовок раздела.
RITUAL_SECTION_RE = re.compile(r"^##\s+\d+\.\s+(?:Лаба|Задача)\s*$")
BLOCK_RE = re.compile(r"^##\s")
# Формулы-рамки вне зон: вводная «Предвопросов» и первая фраза ретеста.
RITUAL_RE = re.compile(r"^(?:попробуйте ответить до чтения|ретест повторяет)")


def normalize(text: str) -> str:
    """Ключ сравнения: регистр вниз, пунктуация и разметка в пробелы."""
    return " ".join(KEEP_RE.sub(" ", text.lower()).split())


def ritual_lines(doc) -> set[int]:
    """Строки разделов «Лаба»/«Задача»: от заголовка до следующего раздела."""
    out = set()
    inside = False
    for n, raw in enumerate(doc.raw.split("\n"), 1):
        if BLOCK_RE.match(raw):
            inside = bool(RITUAL_SECTION_RE.match(raw))
        if inside:
            out.add(n)
    return out


def prose_sentences(doc) -> list[tuple[str, int]]:
    """Предложения материала темы: нормализованный текст и строка начала."""
    end = material(doc)
    skip = skipped_lines(doc)
    ritual = ritual_lines(doc)
    out = []
    for a, b in mdtext.sentences(doc.prose_spans[:end]):
        line = doc.pos(a)[0]
        if line in skip or line in ritual:
            continue  # заголовок, таблица, шапка, навигация — не проза автора;
            # разделы «Лаба»/«Задача» — ритуал практики, а не проза мышления
        key = normalize(doc.prose_spans[a:b])
        if RITUAL_RE.match(key):
            continue  # формула-рамка «Предвопросов» или ретеста
        if len(key.split()) >= MIN_WORDS:
            out.append((key, line))
    return out


def main(argv: list[str]) -> int:
    paths = [Path(p) for p in argv] or mdtext.topics()
    hits: dict[str, list[tuple[str, int]]] = defaultdict(list)
    for path in paths:
        doc = mdtext.load(path)
        for key, line in prose_sentences(doc):
            hits[key].append((str(path), line))

    clones, framework = [], 0
    for key, places in hits.items():
        files = {p for p, _ in places}
        if len(files) < 2:
            continue
        if len(files) > FRAMEWORK_FILES:
            framework += 1
            continue
        clones.append((key, places))
    clones.sort(key=lambda item: (-len({p for p, _ in item[1]}), item[0]))

    print(f"предложений-клонов (≥{MIN_WORDS} слов, в 2+ темах): {len(clones)}")
    print(f"каркас (более чем в {FRAMEWORK_FILES} темах, в список не входит): "
          f"{framework}")
    for key, places in clones:
        print(f"\n«{key}»")
        for path, line in places:
            print(f"  {path}:{line}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
