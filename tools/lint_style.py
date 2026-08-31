#!/usr/bin/env python3
"""Проверки семейства `S-*`: то, чего не умеют ни Vale, ни markdownlint.

Правила и цена каждого — `STYLE.md` § 3 и § 6:

* `S-CODE-WIDTH` (error)   строка листинга ≤ 76 символов — 7.1 п. 3;
* `S-CODE-LEN`   (warn/err) блок ≤ 25 строк, 40 — предел — 7.1 п. 4;
* `S-CODE-PUNCT` (warning) знак препинания вне кода, падеж не приклеен — 6.4;
* `S-LIST-ORDER` (error)   номера пунктов идут по возрастанию с шагом 1;
* `S-LIST-MIX`   (warning) пунктуация внутри одного списка однородна — 6.4;
* `S-SENT-LONG`  (warning) предложение свыше 25 слов — 6.1;
* `S-PARA-LONG`  (warning) абзац свыше 100 слов — 6.1;
* `S-HEAD-DEPTH` (error)   заголовков не глубже трёх уровней — 6.4;
* `S-PLACEHOLDER` (error)  заполнитель шаблона `⟨…⟩` не заменён.

Формат вывода — `путь:строка:столбец:ПРАВИЛО:сообщение`, как у Vale. Выход 1,
если есть ошибка. Содержимое `content/**` скрипт только читает.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import mdtext

ERROR, WARNING = "error", "warning"

CODE_WIDTH = 76          # 7.1 п. 3
CODE_LINES_WARN = 25     # 7.1 п. 4, норма разбираемого примера
CODE_LINES_MAX = 40      # 7.1 п. 4, абсолютный максимум
SENT_WORDS = 25          # 6.1, «свыше 25 переписывается»
PARA_WORDS = 100         # 6.1, пересчёт нормы «3–7 строк» в слова

MARKER_RE = re.compile(r"\A(?P<indent>[ \t]*)"
                       r"(?:(?P<num>\d+)[.)]|(?P<bullet>[-*+]))[ \t]+(?P<text>.*)\Z")
HEAD_RE = re.compile(r"^(#{4,})\s", re.M)
# Схема URI строчными с двоеточием: `data:`, `javascript:`, `mailto:`. Имя поля
# заголовка пишется с прописной (`Cache-Control`), поэтому под это не попадает.
SCHEME_RE = re.compile(r"[a-z][a-z0-9+.\-]*:")
# Многоточие в конце моноширинного фрагмента — знак усечения самого кода
# («`%2553...` переживает один проход»), а не пунктуация фразы: точки стоят
# внутри показываемой записи и вынести их наружу нельзя, не соврав.
ELLIPSIS_RE = re.compile(r"(?:\.\.\.|…)\Z")
# Ссылка на сущность XML или HTML: `&xxe;`, `&amp;`, `&#38;`, `&#x26;`. Точка с
# запятой входит в неё по грамматике формата ровно так же, как двоеточие — в
# схему URI: `&xxe` без неё сущностью не является.
ENTITY_RE = re.compile(r"&(?:#[0-9]+|#[xX][0-9a-fA-F]+|[A-Za-z][A-Za-z0-9]*);\Z")
# Блок «Источники» и хвост за ним: чужие заглавия и аппарат аудита. Мерить их
# длиной предложения бессмысленно — заглавие длинное по своей природе.
# Опознаются по заголовку, а не по номеру: номер у двух скелетов свода 4.2
# разный, заголовок — общий. (До решения оператора 2026-08-31 материал
# заканчивался блоком «Дальше»; блок убран, ссылку вперёд генерирует сборка.)
MATERIAL_END_RE = re.compile(r"^##\s*\d+\.\s+Источники\s*$", re.M)
# Заполнители шаблонов из `templates/*.md`: всё, что автор обязан заменить,
# размечено угловыми скобками ⟨…⟩. Ни в одной теме и ни в одном файле свода
# этих скобок нет, поэтому любое их появление в тексте — недоделка, а не стиль.
PLACEHOLDER_RE = re.compile(r"⟨[^⟨⟩]{0,120}⟩|[⟨⟩]")


class Finding:
    __slots__ = ("path", "line", "col", "rule", "level", "message")

    def __init__(self, path, line, col, rule, level, message):
        self.path, self.line, self.col = str(path), line, col
        self.rule, self.level, self.message = rule, level, message

    def __str__(self):
        return f"{self.path}:{self.line}:{self.col}:{self.rule}:{self.message}"

    def sort_key(self):
        return (self.path, self.line, self.col, self.rule)


def fence_line_set(doc) -> set[int]:
    """Номера строк, занятых ограждёнными блоками, вместе с ограждениями."""
    out = set()
    for f in doc.fences:
        n_body = f.body.count("\n")
        for i in range(f.fence_line, f.fence_line + n_body + 2):
            out.add(i)
    return out


# --- листинги ---------------------------------------------------------------

def check_code(path, doc) -> list[Finding]:
    out = []
    for f in doc.fences:
        body = f.body
        lines = body.split("\n")
        if lines and lines[-1] == "":
            lines.pop()
        for i, raw in enumerate(lines):
            text = raw[len(f.indent):] if raw.startswith(f.indent) else raw
            if len(text) > CODE_WIDTH:
                out.append(Finding(path, f.fence_line + 1 + i, CODE_WIDTH + 1,
                                   "S-CODE-WIDTH", ERROR,
                                   f"строка листинга {len(text)} символов, "
                                   f"предел {CODE_WIDTH} (7.1 п. 3)"))
        n = len(lines)
        if n > CODE_LINES_MAX:
            out.append(Finding(path, f.fence_line, 1, "S-CODE-LEN", ERROR,
                               f"листинг {n} строк, абсолютный максимум "
                               f"{CODE_LINES_MAX} (7.1 п. 4)"))
        elif n > CODE_LINES_WARN:
            out.append(Finding(path, f.fence_line, 1, "S-CODE-LEN", WARNING,
                               f"листинг {n} строк, норма разбираемого примера "
                               f"{CODE_LINES_WARN} (7.1 п. 4)"))
    return out


def check_code_punct(path, doc) -> list[Finding]:
    """Знак препинания перед закрывающей кавычкой и русская буква сразу после неё."""
    out = []
    text = doc.prose_spans
    for m in mdtext.CODE_SPAN_RE.finditer(text):
        inner = m.group(2)
        if (SCHEME_RE.fullmatch(inner) or not inner.strip(",.;: ")
                or ELLIPSIS_RE.search(inner) or ENTITY_RE.search(inner)):
            # `data:` и `javascript:` — схемы URI, двоеточие входит в них по
            # грамматике URL. `.` целиком в кавычках — сам разбираемый знак
            # («файловая система получает `.`»), а не пунктуация фразы. То же с
            # многоточием усечения и с точкой с запятой сущности `&xxe;`: знак
            # принадлежит записи внутри кавычек, а не предложению вокруг них.
            pass
        elif inner and inner[-1] in ",.;:":
            line, col = doc.pos(m.end() - 1 - len(m.group(1)))
            out.append(Finding(path, line, col, "S-CODE-PUNCT", WARNING,
                               f"«{inner[-1]}» стоит внутри моноширинного "
                               f"фрагмента, знак препинания ставится вне (6.4)"))
        after = text[m.end():m.end() + 1]
        if re.match(r"[А-Яа-яЁё]", after):
            line, col = doc.pos(m.end())
            out.append(Finding(path, line, col, "S-CODE-PUNCT", WARNING,
                               "окончание приклеено к моноширинному фрагменту, "
                               "падеж решается дескриптором (6.4)"))
    return out


# --- списки -----------------------------------------------------------------

class Group:
    def __init__(self, indent, ordered, first_line):
        self.indent, self.ordered = indent, ordered
        self.items: list[tuple[int, int | None, list[str]]] = []
        self.first_line = first_line


def parse_lists(doc) -> list[Group]:
    """Списки документа, каждый — как последовательность пунктов одного отступа.

    Пункт держит свои строки-продолжения: они нужны `S-LIST-MIX`, который судит
    по последнему знаку пункта, а не по последнему знаку его первой строки.
    """
    inside = fence_line_set(doc)
    lines = doc.raw.split("\n")
    front_line = doc.pos(doc.front_end)[0] if doc.front_end else 1

    stack: list[Group] = []
    done: list[Group] = []

    def close_to(indent):
        while stack and stack[-1].indent >= indent:
            done.append(stack.pop())

    for n, raw in enumerate(lines, 1):
        if n < front_line or n in inside:
            continue
        if not raw.strip():
            continue
        m = MARKER_RE.match(raw)
        if m:
            indent = len(m.group("indent").expandtabs(4))
            ordered = m.group("num") is not None
            close_to(indent + 1)
            if not stack or stack[-1].indent < indent:
                stack.append(Group(indent, ordered, n))
            elif stack[-1].ordered != ordered:
                done.append(stack.pop())
                stack.append(Group(indent, ordered, n))
            num = int(m.group("num")) if ordered else None
            stack[-1].items.append((n, num, [m.group("text")]))
            continue
        indent = len(raw) - len(raw.lstrip())
        if stack and indent > stack[-1].indent and stack[-1].items:
            stack[-1].items[-1][2].append(raw.strip())
        else:
            close_to(0)
    close_to(0)
    done += stack
    return [g for g in done if g.items]


def check_lists(path, doc) -> list[Finding]:
    out = []
    for g in parse_lists(doc):
        if g.ordered:
            prev = None
            for line, num, _text in g.items:
                if prev is not None and num != prev + 1:
                    out.append(Finding(path, line, 1, "S-LIST-ORDER", ERROR,
                                       f"пункт «{num}.» после «{prev}.»: номера "
                                       f"идут по возрастанию с шагом 1, начало "
                                       f"любое"))
                prev = num
        out += check_list_mix(path, g)
    return out


def endings(g: Group) -> list[str]:
    out = []
    for _line, _num, text in g.items:
        joined = " ".join(t for t in text if t).rstrip()
        last = joined[-1] if joined else ""
        # Вопрос кончается вопросительным знаком, и от точки он в этом счёте не
        # отличается: блок 12 «Проверь себя» законно смешивает вопросы с
        # указаниями («Назовите два механизма.»).
        out.append({".": ".", "?": ".", "!": ".", "…": "."}.get(last, last)
                   if last in ".?!…;,:" else "")
    return out


def check_list_mix(path, g: Group) -> list[Finding]:
    """Однородность пунктуации. Три законных вида списка — 6.4.

    Шаги: каждый пункт с точкой. Продолжение фразы после двоеточия: точка с
    запятой, у последнего точка. Значения без пояснений: без знаков вовсе.
    Четвёртого вида свод не знает, и всё остальное — смешение.
    """
    ends = endings(g)
    if len(ends) < 2:
        return []
    if all(e == "." for e in ends):
        return []
    if all(e == ";" for e in ends[:-1]) and ends[-1] == ".":
        return []
    if all(e == "" for e in ends):
        return []
    shown = ", ".join(f"«{e or '—'}»" for e in ends)
    return [Finding(path, g.first_line, 1, "S-LIST-MIX", WARNING,
                    f"пунктуация списка смешана: {shown}. Законны три вида: "
                    f"все с точкой; «;» и точка у последнего; без знаков (6.4)")]


# --- проза ------------------------------------------------------------------

def material(doc) -> int:
    m = MATERIAL_END_RE.search(doc.prose)
    return m.start() if m else len(doc.prose)


BLOCK_START_RE = re.compile(r"^##\s", re.M)
# Абзацы метаданных вводной зоны: шапка «Уровень **L2** · время 30 мин …» и
# навигация «Что прочитать сначала: …». Они разделены точками-посередине,
# предложения там нет, а слов набирается на пятьдесят — правило ловило бы
# каждую тему за паспорт. Вся остальная вводная зона (введение темы, свод 4.3) —
# проза для читателя и мерится наравне с телом.
INTRO_META_RE = re.compile(r"(?:[Уу]ровень\s+\*\*L[123]\*\*|Что прочитать сначала:)")


def skipped_lines(doc) -> set[int]:
    """Строки, которые из счёта слов выпадают: таблицы, заголовки, блоки кода.

    Таблица — не абзац: разбор предложений склеил бы её в одно длинное. Заголовок
    точкой не заканчивается, и предложением его считать нельзя тоже.

    Из вводной зоны (всё до первого `## `) выпадают только абзацы метаданных —
    шапка и «Что прочитать сначала». До 2026-08-30 выпадала вся зона целиком:
    исторически там стояла одна строка метаданных, а когда туда переехало
    введение темы (свод 4.3), правила `S-SENT-LONG` и `S-PARA-LONG` его перестали
    видеть. Дыра закрыта вместе с правкой пяти отложенных находок в
    `jwt-attacks`, `jwt-basics`, `password-storage` и `path-traversal`
    (`docs/reports/PILOT.md` § 4.3).
    """
    out = fence_line_set(doc)
    for n, raw in enumerate(doc.raw.split("\n"), 1):
        stripped = raw.strip()
        if stripped.startswith(("|", "#")):
            out.add(n)
    if doc.front_end:
        for n in range(1, doc.pos(doc.front_end)[0]):
            out.add(n)
    first_block = BLOCK_START_RE.search(doc.raw)
    intro_end = doc.pos(first_block.start())[0] if first_block else None
    meta = False  # текущий абзац вводной зоны — метаданные, мерить нечего
    fresh = True  # предыдущая строка пустая: эта открывает абзац
    for n, raw in enumerate(doc.raw.split("\n"), 1):
        if intro_end is not None and n >= intro_end:
            break
        if not raw.strip():
            fresh = True
            continue
        if fresh:
            meta = bool(INTRO_META_RE.match(raw.strip()))
            fresh = False
        if meta:
            out.add(n)
    return out


# Слово — то, в чём есть буква, цифра или обратная кавычка. Последнее намеренно:
# моноширинный фрагмент считается словом, он занимает место и требует чтения.
# А вот тире, знак параграфа и маркер цитаты `>` словами не являются: свод
# требует тире как знак (`L-DASH`), и на длинных перечислениях через тире счёт
# завышался на два-три слова — предложение объявлялось длинным за пунктуацию.
WORD_RE = re.compile(r"[\w`]", re.UNICODE)


def words(doc, a: int, b: int) -> int:
    """Слова в куске текста, считая моноширинные фрагменты словами."""
    return sum(1 for t in doc.prose_spans[a:b].split() if WORD_RE.search(t))


def check_prose(path, doc) -> list[Finding]:
    out = []
    end = material(doc)
    skip = skipped_lines(doc)

    # Границы предложений ищутся по `prose_spans`, где инлайновый код виден: в
    # `prose` он заглушён пробелами, и предложение, начатое идентификатором
    # («`upgrade-insecure-requests` поднимает адреса…»), сливалось с предыдущим —
    # правило мерило сумму двух. Длина считается по тому же тексту, где
    # моноширинный фрагмент — слово, так что источник у разреза и у счёта один.
    for a, b in mdtext.sentences(doc.prose_spans[:end]):
        if doc.pos(a)[0] in skip:
            continue
        n = words(doc, a, b)
        if n > SENT_WORDS:
            line, col = doc.pos(a)
            out.append(Finding(path, line, col, "S-SENT-LONG", WARNING,
                               f"предложение {n} слов, свыше {SENT_WORDS} "
                               f"переписывается (6.1)"))

    for a, para in mdtext.paragraphs(doc.prose[:end]):
        if doc.pos(a)[0] in skip:
            continue
        n = words(doc, a, a + len(para))
        if n > PARA_WORDS:
            line, col = doc.pos(a)
            out.append(Finding(path, line, col, "S-PARA-LONG", WARNING,
                               f"абзац {n} слов, норма 3–7 строк — это примерно "
                               f"40–90 (6.1)"))

    for m in HEAD_RE.finditer(doc.prose):
        line, col = doc.pos(m.start())
        out.append(Finding(path, line, col, "S-HEAD-DEPTH", ERROR,
                           f"заголовок уровня {len(m.group(1))}: свод разрешает "
                           f"три (6.4)"))
    return out


# --- заполнители шаблона ----------------------------------------------------

def check_placeholder(path, doc) -> list[Finding]:
    """Незаменённый заполнитель шаблона.

    Смотрит на `raw`, а не на `prose`: заполнитель во frontmatter (`⟨механизм⟩`
    в `teaches`) и заполнитель внутри листинга — та же недоделка, что в прозе, и
    прячется он там лучше. Врезки шаблона, адресованные автору, начинаются с
    `⟨Автору⟩` и попадают под то же правило: одна разметка на всё, что подлежит
    удалению.
    """
    out = []
    for m in PLACEHOLDER_RE.finditer(doc.raw):
        line, col = doc.pos(m.start())
        out.append(Finding(path, line, col, "S-PLACEHOLDER", ERROR,
                           "заполнитель шаблона не заменён: "
                           + m.group(0).replace("\n", " ")[:60]))
    return out


# --- главная ---------------------------------------------------------------

def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--summary", action="store_true",
                    help="печатать сводку по правилам вместо списка замечаний")
    ap.add_argument("--json", action="store_true",
                    help="по одному объекту JSON на замечание, с уровнем: "
                         "этим форматом замечания читает tools/check.py")
    ap.add_argument("paths", nargs="*", help="файлы; по умолчанию content/**/*.md")
    args = ap.parse_args()

    paths = [Path(p) for p in args.paths] or mdtext.topics()
    findings: list[Finding] = []
    for path in paths:
        doc = mdtext.load(path)
        findings += check_code(path, doc)
        findings += check_code_punct(path, doc)
        findings += check_lists(path, doc)
        findings += check_prose(path, doc)
        findings += check_placeholder(path, doc)
    findings.sort(key=Finding.sort_key)

    if args.json:
        for f in findings:
            print(json.dumps({"path": f.path, "line": f.line, "col": f.col,
                              "rule": f.rule, "level": f.level,
                              "message": f.message}, ensure_ascii=False))
    elif args.summary:
        per = defaultdict(int)
        for f in findings:
            per[(f.rule, f.level)] += 1
        for (rule, level), n in sorted(per.items()):
            print(f"{rule:<14} {level:<8} {n}")
    else:
        for f in findings:
            print(f)

    errors = sum(1 for f in findings if f.level == ERROR)
    if not args.json:
        print(f"\nlint_style: {errors} error, {len(findings) - errors} warning "
              f"({len(paths)} файлов)", file=sys.stderr)
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
