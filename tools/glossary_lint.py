#!/usr/bin/env python3
"""Проверки семейства `G-*`: глоссарий против корпуса тем.

Правила и цена каждого — `STYLE.md` § 5. Коротко:

* `G-CANON`  (error)   одно написание термина на весь сайт — 6.3;
* `G-FIRST`  (warning) первое употребление раскрыто — 6.3;
* `G-SYNSET` (error)   синонимы двух терминов не пересекаются — 9.4;
* `G-UNUSED` (warning) термин глоссария кем-то употреблён — 9.4;
* `G-GLOSS`  (error)   целостность самого `glossary.yaml`: группы, `see_also`,
                       `defines` называют существующие темы;
* `G-NEW-PAGE`         не правило, а метрика 6.7. Печатается по `--report`.

Формат вывода — `путь:строка:столбец:ПРАВИЛО:сообщение`, тот же, что у
`vale --output=line`, поэтому `tools/check.py` разбирает всё одним выражением.
Замечания к самому глоссарию адресуются строкой записи в `glossary.yaml`.

Выход 1, если есть хотя бы одна ошибка. Предупреждения на код выхода не влияют:
двенадцать тем написаны до появления глоссария, и warning здесь — материал для
авторской ревизии, а не поломка сборки.

Содержимое `content/**` скрипт только читает.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import yaml

import mdtext
from paths import GLOSSARY_YAML

ERROR, WARNING = "error", "warning"

# Русские окончания и латиница с цифрами: слово прозы для G-CANON. Дефис и точка
# внутри слова сохраняются, иначе `Set-Cookie` распадётся на `Set` и `Cookie`, а
# `Node.js` — на `Node` и `js`.
WORD_RE = re.compile(r"[^\W_]+(?:[-.][^\W_]+)*", re.UNICODE)

# Похожее на домен или путь пропускаем: `graphql.org` каноническим `GraphQL` не
# правится. Автоссылки и код `mdtext` вырезал раньше, это добор для прозы.
DOMAINISH_RE = re.compile(r"^[a-z0-9-]+(?:\.[a-z0-9-]+)*\.[a-z]{2,}$", re.I)

# Блок «Источники» (14 у уязвимостей, 13 у инструментов) — сплошь чужие
# заглавия: «Cross-Origin Resource Sharing (CORS)», «Session ID Properties»,
# «Introspection». Заглавие цитируется буквально (7.4), поэтому канон
# написаний на него не распространяется.
SOURCES_RE = re.compile(r"^##\s*1[34]\.\s*Источники", re.M)

# Текст в «ёлочках» — цитата или заглавие, то есть чужие слова: «Authentication
# Failures» в названии раздела учебного плана, «ЭКСПЛОЙТ НЕ СРАБОТАЛ» в выводе
# программы. Своего написания в них нет и править их нельзя.
QUOTED_RE = re.compile(r"«[^»]*»", re.S)

# Пробег из двух и более латинских слов с прописной буквы — английское имя
# собственное: `OWASP Session Management Cheat Sheet`, `Key Exchange, Server
# Parameters, Authentication`. Внутри такого пробега `Session` — часть имени, а
# не термин `session`, написанный не так.
PROPER_RUN_RE = re.compile(
    r"[A-Z][A-Za-z0-9]*(?:-[A-Za-z0-9]+)*"
    r"(?:,?\s+[A-Z][A-Za-z0-9]*(?:-[A-Za-z0-9]+)*)+")


class Finding:
    __slots__ = ("path", "line", "col", "rule", "level", "message")

    def __init__(self, path, line, col, rule, level, message):
        self.path, self.line, self.col = str(path), line, col
        self.rule, self.level, self.message = rule, level, message

    def __str__(self):
        return f"{self.path}:{self.line}:{self.col}:{self.rule}:{self.message}"

    def sort_key(self):
        return (self.path, self.line, self.col, self.rule)


def norm(s: str) -> str:
    """Написание с точностью до регистра. Дефис и пробел значимы.

    `STYLE.md` § 5 требует сверять написания «с точностью до регистра»: в этой
    предметной области дефис несёт смысл. `SameSite` — атрибут cookie,
    `same-site` — отношение двух сайтов в rfc6265bis, и оба написания законны в
    одном предложении. То же у `__Secure-` (префикс имени) и `Secure` (атрибут).
    Правило, слепое к дефису, объявило бы половину этих пар ошибкой.
    """
    return s.lower()


# --- загрузка ---------------------------------------------------------------

def load_glossary():
    data = yaml.safe_load(GLOSSARY_YAML.read_text(encoding="utf-8"))
    terms = data["terms"]
    # Группы объявлены списком записей: порядок списка — порядок разделов в
    # собранном `GLOSSARY.md`, поэтому это не словарь.
    groups = {g["id"]: g["title"] for g in data["groups"]}
    lines = {}
    for i, raw in enumerate(GLOSSARY_YAML.read_text(encoding="utf-8").splitlines(), 1):
        m = re.match(r"\s*-\s+id:\s*(\S+)", raw)
        if m:
            lines.setdefault(m.group(1), i)
    return data, terms, groups, lines


def spellings(t: dict) -> list[str]:
    """Все написания записи: термин, английский эквивалент, аббревиатура, синонимы."""
    out = [t["term"]]
    for f in ("en", "abbr"):
        if t.get(f):
            out.append(t[f])
    out += list(t.get("aliases") or [])
    return out


def load_pages():
    pages = []
    for path in mdtext.topics():
        doc = mdtext.load(path)
        front = yaml.safe_load(doc.front_text) if doc.front_text else {}
        pages.append((path, doc, front))
    pages.sort(key=lambda p: (p[2].get("order", 10**9), p[2].get("id", "")))
    return pages


# --- G-GLOSS, G-SYNSET ------------------------------------------------------

def check_glossary(terms, groups, lines, page_ids) -> list[Finding]:
    out = []

    def at(term_id, rule, level, msg):
        out.append(Finding("glossary.yaml", lines.get(term_id, 1), 1, rule, level, msg))

    seen_ids = set()
    for t in terms:
        tid = t["id"]
        if tid in seen_ids:
            at(tid, "G-GLOSS", ERROR, f"идентификатор «{tid}» встречается второй раз")
        seen_ids.add(tid)
        if t["group"] not in groups:
            at(tid, "G-GLOSS", ERROR,
               f"группа «{t['group']}» не объявлена в разделе groups")
        if not t.get("definition", "").strip():
            at(tid, "G-GLOSS", ERROR, "определение пустое")

    for t in terms:
        for ref in t.get("see_also") or []:
            if ref not in seen_ids:
                at(t["id"], "G-GLOSS", ERROR,
                   f"see_also ссылается на «{ref}» — такого термина в глоссарии нет")
        for ref in t.get("defines") or []:
            if ref not in page_ids:
                at(t["id"], "G-GLOSS", ERROR,
                   f"defines называет тему «{ref}» — такой страницы в content нет")

    # G-SYNSET: пересечение множеств написаний двух записей. Одно написание,
    # ведущее к двум терминам, делает G-CANON неоднозначным, а ссылку из темы —
    # неразрешимой (9.4, блокирующая проверка).
    owner: dict[str, str] = {}
    for t in terms:
        for sp in spellings(t):
            key = norm(sp)
            if key in owner and owner[key] != t["id"]:
                at(t["id"], "G-SYNSET", ERROR,
                   f"написание «{sp}» уже принадлежит термину «{owner[key]}»")
            owner[key] = t["id"]
    return out


# --- G-CANON ----------------------------------------------------------------

def build_canon(terms):
    """Ключ нормализованного написания → (каноническое написание, id термина).

    В карту попадают только однословные написания: слово прозы сравнивается со
    словом словаря. Многословные термины ловятся правилом `G-FIRST` и метрикой
    `G-NEW-PAGE`, где поиск идёт выражением, а не по одному слову.
    """
    canon = {}
    for t in terms:
        for sp in spellings(t):
            if " " in sp:
                continue
            canon[norm(sp)] = (sp, t["id"])
    return canon


def canon_scope(doc) -> str:
    """Проза без чужих слов: блока источников, цитат в «ёлочках», имён собственных.

    Смещения сохраняются — вырезанное заменяется пробелами той же длины, — иначе
    номера строк пришлось бы пересчитывать (см. `mdtext`).
    """
    text = doc.prose
    m = SOURCES_RE.search(text)
    if m:
        text = text[:m.start()] + blank(text[m.start():])
    for rx in (QUOTED_RE, PROPER_RUN_RE):
        text = rx.sub(lambda mm: blank(mm.group(0)), text)
    return text


def blank(s: str) -> str:
    return "".join("\n" if ch == "\n" else " " for ch in s)


def check_canon(pages, canon) -> list[Finding]:
    out = []
    for path, doc, _front in pages:
        text = canon_scope(doc)
        starts = mdtext.word_starts(doc.prose, mdtext.sentences(doc.prose))
        for m in WORD_RE.finditer(text):
            word = m.group(0)
            if DOMAINISH_RE.match(word):
                continue
            hit = canon.get(norm(word))
            if hit is None:
                continue
            good, tid = hit
            if word == good:
                continue
            # Начало предложения: прописная первая буква законна всегда.
            if m.start() in starts and word == good[:1].upper() + good[1:]:
                continue
            line, col = doc.pos(m.start())
            out.append(Finding(path, line, col, "G-CANON", ERROR,
                               f"«{word}» — не каноническое написание, в глоссарии "
                               f"«{good}» (термин {tid})"))
    return out


# --- G-FIRST, G-UNUSED, G-NEW-PAGE -----------------------------------------

def term_regexes(terms):
    out = {}
    for t in terms:
        pats = []
        for sp in spellings(t):
            pats.append(mdtext.stem_pattern(sp))
        out[t["id"]] = re.compile("|".join(pats), re.I)
    return out


# Блоки «Дальше» и «Источники» (13/14 у уязвимостей, 12/13 у инструментов)
# говорят не о материале страницы, а о других страницах и о чужих документах. Аббревиатура в указателе
# «`tls-and-proxy` — почему `upgrade-insecure-requests` не заменяет HSTS» — не
# первое употребление термина, а ссылка вперёд, и раскрывать её незачем.
MATERIAL_END_RE = re.compile(r"^##\s*1[23]\.\s*Дальше", re.M)


def material_end(doc) -> int:
    m = MATERIAL_END_RE.search(doc.prose)
    return m.start() if m else len(doc.prose)


def first_hits(pages, regexes, field="prose", material_only=False):
    """id темы → id термина → смещение первого вхождения.

    При `material_only` берётся материал страницы своими словами: блоки 0–12 без
    цитат и заглавий в «ёлочках». Причина та же, что у `canon_scope`, и записана
    у `QUOTED_RE`: в чужих словах своего написания нет и править их нельзя. Тема
    `app-architecture` ссылается на MDN «CORS errors» и приводит текст ошибки
    браузера «Multiple CORS header … not allowed», а сама аббревиатуру `CORS`
    нигде не употребляет — раскрывать в заглавии источника нечего, и до этой
    оговорки правило требовало невозможного (находка Ф-33, 2026-08-23).
    """
    hits = {}
    for path, doc, front in pages:
        text = getattr(doc, field)
        if material_only:
            text = QUOTED_RE.sub(lambda m: blank(m.group(0)),
                                 text[:material_end(doc)])
        page = {}
        for tid, rx in regexes.items():
            m = rx.search(text)
            if m:
                page[tid] = m.start()
        hits[front.get("id", path.stem)] = page
    return hits


# Аббревиатура: латиница прописными, две буквы и больше, с цифрами и дефисами
# внутри — `HTTP`, `TLS`, `CSPRNG`, `SHA-256`. Именно про этот класс говорит 6.3
# своим примером «межсайтовый скриптинг (cross-site scripting, XSS)».
ABBR_RE = re.compile(r"\A[A-Z][A-Z0-9]+(?:-[A-Z0-9]+)*\Z")


def needs_disclosure(t: dict) -> bool:
    """Требует ли термин раскрытия при первом употреблении.

    Требуют аббревиатуры: читатель, встретивший `HSTS` без расшифровки, не
    может даже поискать её. Не требуют русские слова, у которых в глоссарии
    есть только поле `en`: «метод (method)» в скобках — не раскрытие, а шум.
    Поле `en` заведено, чтобы читатель нашёл англоязычную литературу, и
    обязательства на предложение оно не накладывает.
    """
    if t.get("abbr"):
        return True
    return bool(t.get("en")) and ABBR_RE.match(t["term"]) is not None


def prereq_closure(pages) -> dict[str, set[str]]:
    """id темы → все темы, прочитанные до неё по полю `prerequisites`.

    Транзитивно: если тема требует `cookies`, а `cookies` требует `http-basics`,
    то к моменту чтения прочитаны обе. Замыкание нужно правилу `G-FIRST`:
    аббревиатура, раскрытая в теме-предпосылке, читателю уже знакома, и
    требовать раскрытия второй раз — значит требовать шума.
    """
    direct = {f.get("id", p.stem): list(f.get("prerequisites") or [])
              for p, _d, f in pages}
    out: dict[str, set[str]] = {}

    def walk(pid, seen):
        if pid in out:
            return out[pid]
        if pid in seen:            # цикл в предпосылках — забота валидатора модели
            return set()
        seen = seen | {pid}
        acc = set()
        for dep in direct.get(pid, []):
            acc.add(dep)
            acc |= walk(dep, seen)
        out[pid] = acc
        return acc

    for pid in direct:
        walk(pid, set())
    return out


def check_first(pages, terms, regexes, hits) -> list[Finding]:
    by_id = {t["id"]: t for t in terms}
    closure = prereq_closure(pages)
    out = []
    for path, doc, front in pages:
        page_id = front.get("id", path.stem)
        read_before = closure.get(page_id, set())
        sents = mdtext.sentences(doc.prose)
        for tid, off in sorted(hits[page_id].items(), key=lambda kv: kv[1]):
            t = by_id[tid]
            defines = t.get("defines") or []
            if page_id in defines:
                continue          # условие 3: тема вводит термин своим содержанием
            if read_before & set(defines):
                continue          # условие 4: раскрыто в теме-предпосылке
            if not needs_disclosure(t):
                continue
            sent = next((s for s in sents if s[0] <= off < s[1]), None)
            text = doc.prose[sent[0]:sent[1]] if sent else ""
            if disclosed(t, text):
                continue
            line, col = doc.pos(off)
            want = ", ".join(x for x in (t.get("en"), t.get("abbr")) if x)
            out.append(Finding(path, line, col, "G-FIRST", WARNING,
                               f"первое употребление «{t['term']}» не раскрыто: "
                               f"ожидается ({want}) в том же предложении "
                               f"(термин {tid})"))
    return out


def disclosed(t: dict, sentence: str) -> bool:
    """Раскрыто ли первое употребление — любое из трёх условий `STYLE.md` § 5."""
    low = sentence.lower()
    if t.get("en") and t["en"].lower() in low:
        return True                       # условие 1: английское раскрытие рядом
    if t.get("abbr") and re.search(mdtext.stem_pattern(t["term"]), sentence, re.I):
        return True                       # условие 2: полная форма и аббревиатура
    for alias in t.get("aliases") or []:  # русский синоним в роли полной формы
        if re.search("[А-Яа-яЁё]", alias) and \
                re.search(mdtext.stem_pattern(alias), sentence, re.I):
            return True
    return False


def check_unused(terms, hits, lines) -> list[Finding]:
    """`hits` здесь считаются по прозе вместе с инлайновым кодом (см. mdtext)."""
    used = set()
    for page in hits.values():
        used |= set(page)
    out = []
    for t in terms:
        if t["id"] not in used:
            out.append(Finding("glossary.yaml", lines.get(t["id"], 1), 1,
                               "G-UNUSED", WARNING,
                               f"термин «{t['term']}» не встречается ни в одной теме"))
    return out


def report_new_terms(pages, terms, hits) -> str:
    by_id = {t["id"]: t for t in terms}
    lines = ["", "G-NEW-PAGE: новые термины по страницам "
                 "(метрика 6.7, порога нет)", ""]
    lines.append(f"{'страница':<24} {'новых':>6} {'всего':>6}  термины")
    seen: set[str] = set()
    for _path, _doc, front in pages:
        page_id = front.get("id")
        page = hits.get(page_id, {})
        fresh = [tid for tid in sorted(page, key=lambda k: page[k]) if tid not in seen]
        seen |= set(page)
        names = ", ".join(by_id[t]["term"] for t in fresh[:6])
        if len(fresh) > 6:
            names += f", … (+{len(fresh) - 6})"
        lines.append(f"{page_id:<24} {len(fresh):>6} {len(page):>6}  {names}")
    lines.append("")
    lines.append(f"терминов глоссария: {len(terms)}, употреблённых: {len(seen)}")
    return "\n".join(lines)


# --- главная ---------------------------------------------------------------

def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--report", action="store_true",
                    help="печатать метрику G-NEW-PAGE таблицей")
    ap.add_argument("--summary", action="store_true",
                    help="печатать сводку по правилам вместо списка замечаний")
    ap.add_argument("--json", action="store_true",
                    help="по одному объекту JSON на замечание, с уровнем: "
                         "этим форматом замечания читает tools/check.py")
    args = ap.parse_args()

    data, terms, groups, lines = load_glossary()
    pages = load_pages()
    page_ids = {f.get("id", p.stem) for p, _d, f in pages}
    regexes = term_regexes(terms)
    hits = first_hits(pages, regexes, material_only=True)

    findings = []
    findings += check_glossary(terms, groups, lines, page_ids)
    findings += check_canon(pages, build_canon(terms))
    findings += check_first(pages, terms, regexes, hits)
    findings += check_unused(terms, first_hits(pages, regexes, "prose_spans"), lines)
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
            print(f"{rule:<12} {level:<8} {n}")
    else:
        for f in findings:
            print(f)

    if args.report:
        print(report_new_terms(pages, terms, hits))

    errors = sum(1 for f in findings if f.level == ERROR)
    warnings = len(findings) - errors
    if not args.json:
        print(f"\nglossary_lint: {errors} error, {warnings} warning "
              f"({len(terms)} терминов, {len(pages)} тем)", file=sys.stderr)
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
