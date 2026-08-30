"""Разбор темы на прозу и код с сохранением позиций.

Проверки свода делятся на два вида: одни смотрят прозу и обязаны не видеть
код, другие смотрят код и обязаны не видеть прозу. Оба вида нуждаются в
точных номерах строки и столбца, чтобы вывод указывал на место.

Приём один: вместо вырезания непрозаичных участков они забиваются пробелами.
Длина текста, номера строк и столбцы остаются теми же, что в файле, поэтому
позицию находки не приходится пересчитывать, а регулярные выражения не
склеивают куски, стоявшие по разные стороны листинга.

Пользователи: `glossary_lint.py`, `lint_style.py`, `linkcheck.py`.
"""

from __future__ import annotations

import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from paths import CONTENT_DIR, ROOT

FRONT_RE = re.compile(r"\A---\n(.*?)\n---\n", re.S)
FENCE_RE = re.compile(r"^(?P<indent>[ \t]*)(?P<fence>```+|~~~+)(?P<info>[^\n]*)\n"
                      r"(?P<body>.*?)"
                      r"^[ \t]*(?P=fence)[ \t]*$", re.S | re.M)
CODE_SPAN_RE = re.compile(r"(?<!`)(`+)(?!`)(.+?)(?<!`)\1(?!`)", re.S)
AUTOLINK_RE = re.compile(r"<https?://[^>\s]*>")
BARE_URL_RE = re.compile(r"https?://\S+")


def _blank(s: str) -> str:
    """Заменить всё, кроме переводов строки, пробелами."""
    return "".join("\n" if ch == "\n" else " " for ch in s)


@dataclass
class Fence:
    """Ограждённый блок: где начался, чем помечен, что внутри."""

    info: str
    body: str
    body_start: int
    fence_line: int
    indent: str


@dataclass
class Doc:
    path: Path
    raw: str
    front_text: str = ""
    front_end: int = 0
    prose: str = ""
    code: str = ""
    prose_spans: str = ""
    fences: list[Fence] = field(default_factory=list)
    _starts: list[int] = field(default_factory=list)

    def pos(self, offset: int) -> tuple[int, int]:
        """Смещение в тексте — в пару «строка, столбец», обе с единицы."""
        lo, hi = 0, len(self._starts) - 1
        while lo < hi:
            mid = (lo + hi + 1) // 2
            if self._starts[mid] <= offset:
                lo = mid
            else:
                hi = mid - 1
        return lo + 1, offset - self._starts[lo] + 1

    def line_text(self, line: int) -> str:
        start = self._starts[line - 1]
        end = self.raw.find("\n", start)
        return self.raw[start:end if end >= 0 else len(self.raw)]


def load(path: str | Path) -> Doc:
    path = Path(path)
    # Относительный путь — от корня репозитория, а не от текущего каталога:
    # скрипт обязан работать при запуске из любого места. В `doc.path` путь
    # сохраняется как передан — таким его печатают проверки.
    raw = (path if path.is_absolute() else ROOT / path).read_text(encoding="utf-8")
    doc = Doc(path=path, raw=raw)
    doc._starts = [0] + [m.end() for m in re.finditer("\n", raw)]

    chars = list(raw)
    code_chars = ["\n" if ch == "\n" else " " for ch in raw]

    front = FRONT_RE.match(raw)
    if front:
        doc.front_text = front.group(1)
        doc.front_end = front.end()
        for i in range(front.start(), front.end()):
            if chars[i] != "\n":
                chars[i] = " "

    for m in FENCE_RE.finditer(raw):
        doc.fences.append(Fence(
            info=m.group("info").strip(),
            body=m.group("body"),
            body_start=m.start("body"),
            fence_line=doc.pos(m.start())[0],
            indent=m.group("indent"),
        ))
        for i in range(m.start(), m.end()):
            if chars[i] != "\n":
                chars[i] = " "
        for i in range(m.start("body"), m.end("body")):
            code_chars[i] = raw[i]

    # `prose_spans` — проза вместе с инлайновым кодом. Нужна проверкам, для
    # которых имя заголовка или атрибута в обратных кавычках считается
    # употреблением термина: `Set-Cookie` и `HttpOnly` в прозе иначе не
    # встречаются вовсе (6.4 требует ставить их в код).
    text = "".join(chars)
    doc.prose_spans = text
    for rx in (CODE_SPAN_RE, AUTOLINK_RE, BARE_URL_RE):
        out = []
        last = 0
        for m in rx.finditer(text):
            out.append(text[last:m.start()])
            out.append(_blank(m.group(0)))
            last = m.end()
        out.append(text[last:])
        text = "".join(out)

    doc.prose = text
    doc.code = "".join(code_chars)
    assert len(doc.prose) == len(raw) and len(doc.code) == len(raw)
    assert len(doc.prose_spans) == len(raw)
    return doc


def topics() -> list[Path]:
    """Все темы корпуса, путями от корня репозитория: так их печатают проверки,
    а `load()` сам разрешит их независимо от текущего каталога."""
    return sorted(p.relative_to(ROOT) for p in CONTENT_DIR.rglob("*.md"))


# --- предложения -----------------------------------------------------------

# Точки, которые не заканчивают предложение. Список закрытый и растёт только
# по находке: сокращения свода, номера версий, номера параграфов, составные
# имена вида `Node.js`.
_PROTECT = [
    re.compile(r"\b(?:т|е|д|п|рис|см|гл|др|табл|стр|прим|напр|мин|сек|ч)\."),
    re.compile(r"\d+\.\d+"),
    re.compile(r"v\d+(?:\.\d+)*"),
    re.compile(r"§\s*\d+(?:\.\d+)*"),
    re.compile(r"[A-Za-z]\.[A-Za-z]"),
]
# Разрез: знак конца предложения, за ним закрывающая разметка («**» у выделенного
# фрагмента, кавычка, скобка), пробел и прописная буква или цифра, возможно тоже
# за открывающей разметкой. Без разметки в шаблоне «**Примечание.** **Метод** —»
# оставался бы одним предложением.
_MARKUP_AFTER = r"[*_`)»\]\"']*"
# Внутри абзаца перевод строки — обычный пробел, поэтому разделитель `\s+`, а не
# `[ \t]+`: иначе предложение, начатое с новой строки, слипается с предыдущим.
# В `_MARKUP_BEFORE` есть «>» и «|» — префиксы строки цитаты и ячейки таблицы.
_MARKUP_BEFORE = r"[«„\"'(\[*_`>|\s]*"
# Прописной буквы после точки мало: в этом гайде предложение начинается с
# идентификатора в обратных кавычках, а он строчный — «`upgrade-insecure-requests`
# поднимает адреса…». Регистр здесь не выбор автора, а написание, взятое из
# спецификации, поэтому обратная кавычка допускается как начало предложения
# наравне с прописной буквой. Без этой ветки два предложения слипались в одно, и
# `S-SENT-LONG` мерил их сумму: в csp — 58 слов вместо 30 и 28 (замер 2026-08-23).
_SPLIT = re.compile(rf"[.!?…]{_MARKUP_AFTER}\s+(?={_MARKUP_BEFORE}(?:[А-ЯЁA-Z0-9]|`))")
_SENTINEL = "\x00"


def sentences(text: str) -> list[tuple[int, int]]:
    """Границы предложений в тексте, парами смещений.

    Разрез идёт по точке, восклицательному и вопросительному знаку, за которыми
    стоит пробел и прописная буква или цифра. Точки из `_PROTECT` на время
    разреза подменяются, поэтому «т. е.» и `§ 6.1.3` предложение не разрывают.

    Надёжного способа резать русский текст регулярным выражением нет, поэтому
    все правила, которые этим пользуются, живут на уровне warning — см.
    `STYLE.md` § 3, `S-SENT-LONG`.
    """
    masked = list(text)
    for rx in _PROTECT:
        for m in rx.finditer(text):
            for i in range(m.start(), m.end()):
                if masked[i] == ".":
                    masked[i] = _SENTINEL
    masked_text = "".join(masked)

    out: list[tuple[int, int]] = []
    for para_start, para in _paragraphs(masked_text):
        cuts = [0] + [m.end() - para_start
                      for m in _SPLIT.finditer(masked_text, para_start,
                                               para_start + len(para))]
        cuts.append(len(para))
        for a, b in zip(cuts, cuts[1:]):
            frag = para[a:b]
            if frag.strip():
                lead = len(frag) - len(frag.lstrip())
                out.append((para_start + a + lead, para_start + a + len(frag.rstrip())))
    return out


_LEADING_MARKUP = re.compile(r"[#>*_`|\-\s]*(?:\d+[.)][ \t]*)?[*_`«„\"'(\[]*")


def word_starts(text: str, bounds: list[tuple[int, int]]) -> set[int]:
    """Смещения, с которых начинается предложение, — и до разметки, и после неё.

    Прописная буква законна в начале предложения, а началом предложения бывает
    заголовок, пункт нумерованного списка и выделенный фрагмент. Разметку перед
    первым словом правило `G-CANON` обязано пропустить, иначе «### Отпечаток»
    выглядит как слово посреди фразы.
    """
    out = set()
    for a, _b in bounds:
        out.add(a)
        out.add(a + _LEADING_MARKUP.match(text, a).end() - a)
    return out


_LIST_MARKER_RE = re.compile(r"\A[ \t]*(?:[-*+]|\d+[.)])[ \t]+")


def _paragraphs(text: str) -> list[tuple[int, str]]:
    """Абзацы: куски, разделённые пустой строкой или началом пункта списка.

    Пункт списка — отдельная единица текста, и склеивать его с соседними
    пунктами нельзя: пункты часто идут без завершающего знака, и склеенный
    список выглядел бы одним предложением на сотню слов. Строка цитаты («>»)
    абзац не разрывает — цитата бывает многострочной.
    """
    out: list[tuple[int, str]] = []
    start: int | None = None
    end = 0
    pos = 0
    for line in text.split("\n"):
        if not line.strip():
            if start is not None:
                out.append((start, text[start:end]))
                start = None
        else:
            if start is not None and _LIST_MARKER_RE.match(line):
                out.append((start, text[start:end]))
                start = None
            if start is None:
                start = pos + len(line) - len(line.lstrip())
            end = pos + len(line.rstrip())
        pos += len(line) + 1
    if start is not None:
        out.append((start, text[start:end]))
    return out


def paragraphs(text: str) -> list[tuple[int, str]]:
    return _paragraphs(text)


# --- термины ----------------------------------------------------------------

def stem_pattern(term: str) -> str:
    """Выражение, которым термин ищется в тексте с учётом словоформ.

    Русское слово усекается до основы (длина минус два, но не короче четырёх
    символов) и продолжается любыми буквами: «граница доверия» найдётся в
    «за границей доверия». Латиница не склоняется (6.3) и берётся целиком.
    Это грубая замена морфологическому разбору, поэтому она годится для
    вопроса «термин вообще употреблён» и не годится для вопроса «в какой форме».
    """
    parts = re.split(r"(\s+|-)", term)
    out = []
    for part in parts:
        if not part:
            continue
        if part.isspace():
            out.append(r"\s+")
        elif part == "-":
            out.append("-")
        elif re.search(r"[А-Яа-яЁё]", part):
            n = max(4, len(part) - 2)
            out.append(re.escape(part[:n]) + r"[А-Яа-яЁё]*")
        else:
            out.append(re.escape(part))
    return r"(?<!\w)" + "".join(out) + r"(?!\w)"
