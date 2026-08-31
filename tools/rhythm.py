#!/usr/bin/env python3
"""Ритм прозы: длины предложений по темам и по корпусу.

    python tools/rhythm.py                      # весь корпус
    python tools/rhythm.py content/stage-2/*.md # подмножество

Отчёт без вердикта — радар для фазы 3 плана `PLAN-VOICE.md`: монотонный ритм
лечится точечной переписью, и метрика нужна, чтобы видеть сдвиг до/после.
Порогов нет, код возврата всегда 0.

Три числа на тему и одной строкой по корпусу: доля предложений ≤5 слов,
средняя длина, коэффициент вариации длин (CV = среднеквадратичное отклонение /
среднее; 0 — все предложения одинаковы).

Меряется бегущая проза материала (без блока «Источники» и хвоста за ним).
Не меряется мебель, которую предписывает скелет, а не выбирает автор:
списки и цитаты, заголовки и таблицы, шапка с навигацией (тот же набор, что
в `lint_style.skipped_lines`), ответы под `<details>`, жирные метки-затравки
(«**Цена.**», «**Шаг 1.**» — решением оператора от 2026-08-30 они убираются,
и метрика не должна прыгнуть от одной этой правки) и вводные строки с
двоеточием («После этого раздела вы сможете:»).

Предложение и слово понимаются ровно так, как их понимает гейт `S-SENT-LONG`:
тот же разрез `mdtext.sentences`, тот же счёт `lint_style.words`
(моноширинный фрагмент — слово, тире — нет).

Оговорка о сличении с аудитом: замер из `PLAN-VOICE.md` (≤5 слов — 4 %,
CV 0,49, коридор 10–20 слов — 59 %) сделан своим резаком до этого инструмента.
Здесь на том же корпусе: коридор 10–20 совпадает (60 %), CV и доля коротких
другие — у аудита, судя по числам, мебель не вычиталась целиком. Абсолютные
значения двух замеров несопоставимы; метрика годится для дельт до/после,
что и требуется фазе 3.
"""

import re
import statistics
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import mdtext
from lint_style import material, skipped_lines, words

SHORT = 5  # предложение-удар: не длиннее пяти слов

LIST_RE = re.compile(r"[ \t]*(?:[-*+]|\d+[.)])[ \t]+")
DETAILS_RE = re.compile(r"<details[^>]*>.*?</details>", re.S)
# Затравка абзаца целиком из жирного: «**Цена.**», «**Шаг 1.**». Содержание
# абзаца за ней меряется как обычно — вычитается только сама метка.
BOLD_LABEL_RE = re.compile(r"\A[*_`«„\"'(\[\s]*\*\*[^*\n]+\*\*[.:]?\**\s*\Z")


def lengths(doc) -> list[int]:
    """Длины предложений бегущей прозы темы, в словах."""
    end = material(doc)
    skip = skipped_lines(doc)
    # Ответы под <details> заглушены пробелами: позиции строк не съезжают.
    spans = DETAILS_RE.sub(lambda m: re.sub(r"[^\n]", " ", m.group(0)),
                           doc.prose_spans[:end])
    out = []
    for a, b in mdtext.sentences(spans):
        line = doc.pos(a)[0]
        if line in skip:
            continue
        raw = doc.line_text(line)
        if LIST_RE.match(raw) or raw.lstrip().startswith(">"):
            continue  # пункт списка и цитата — не бегущая проза
        frag = spans[a:b].strip()
        if BOLD_LABEL_RE.match(frag) or frag.endswith(":"):
            continue  # метка скелета и вводная строка с двоеточием
        out.append(words(doc, a, b))
    return out


def stats(lens: list[int]) -> tuple[int, float, float, float]:
    """Число предложений, доля коротких, средняя длина, CV."""
    n = len(lens)
    if not n:
        return 0, 0.0, 0.0, 0.0
    mean = statistics.fmean(lens)
    short = sum(1 for x in lens if x <= SHORT) / n
    cv = statistics.pstdev(lens) / mean if mean else 0.0
    return n, short, mean, cv


def main(argv: list[str]) -> int:
    paths = [Path(p) for p in argv] or mdtext.topics()
    print(f"{'файл':<34}{'предл.':>8}{'≤5 слов':>9}{'средняя':>9}{'CV':>7}")
    corpus: list[int] = []
    for path in paths:
        lens = lengths(mdtext.load(path))
        corpus += lens
        n, short, mean, cv = stats(lens)
        print(f"{Path(path).name:<34}{n:>8}{short:>9.0%}{mean:>9.1f}{cv:>7.2f}")
    n, short, mean, cv = stats(corpus)
    print(f"{'КОРПУС':<34}{n:>8}{short:>9.0%}{mean:>9.1f}{cv:>7.2f}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
