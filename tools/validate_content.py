#!/usr/bin/env python3
"""Проверки семейства `C-*`: контентная модель против корпуса тем.

Схема, состав по уровням и цена каждого правила — `SCHEMA.md`. Коротко:

* `C-FM-*`    frontmatter: набор полей, типы, словари, форматы идентификаторов;
* `C-REF-*`   ссылки между записями: темы, источники, лабы, план, циклы, сироты;
* `C-BLOCK-*` канонический скелет части 4: форма, порядок, состав по уровню;
* `C-HEAD-*`  шапка темы против frontmatter;
* `C-BODY-*`  служебный аппарат и наполнение блоков 1, 10, 12, 13, 14.

Часть 9.1 плейбука: «Нарушение схемы **ломает сборку**, а не деградирует тихо».
Поэтому почти всё здесь — error. Warning остаётся там, где нарушено не правило,
а ожидание: расхождение формулировок, просроченная ревизия, тема без входящих
ссылок.

    python tools/validate_content.py             # весь корпус
    python tools/validate_content.py --json      # формат для tools/check.py
    python tools/validate_content.py --summary   # по правилам

Проверке нельзя дать подмножество тем: цикл в графе предпосылок, уникальность
`order` и сироты — свойства всего корпуса. Скрипт всегда читает `content/**`
целиком; отбор путей делает `tools/check.py`.

Содержимое `content/**` скрипт только читает.
"""

from __future__ import annotations

import argparse
import datetime as dt
import difflib
import json
import re
import sys
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import yaml

import mdtext

ROOT = Path(__file__).resolve().parent.parent
TAXONOMY = ROOT / "taxonomy.yaml"
TOPICS = ROOT / "topics.yaml"
SOURCES = ROOT / "sources.yaml"
LABS = ROOT / "labs.yaml"

ERROR, WARNING = "error", "warning"

TODAY = dt.date.today()


@dataclass
class Finding:
    path: str
    line: int
    col: int
    rule: str
    level: str
    message: str

    def __str__(self) -> str:
        return f"{self.path}:{self.line}:{self.col}:{self.rule}:{self.message}"

    def sort_key(self):
        return (self.path, self.line, self.col, self.rule)


# ── схема frontmatter ─────────────────────────────────────────────────────────
#
# Порядок здесь — канонический порядок полей в теме (C-FM-SEQ). Он одинаков во
# всех двенадцати темах, написанных до появления схемы, и закрепляется, чтобы
# тринадцатая не начала свой: diff двух тем должен показывать разницу смысла, а
# не разницу раскладки.

SCHEMA: list[tuple[str, str, bool]] = [
    ("id", "str", True),
    ("plan_id", "str", True),
    ("title", "str", True),
    ("summary", "str", True),
    ("stage", "str", True),
    ("order", "int", True),
    ("status", "str", True),
    ("depth", "str", True),
    ("mode", "str", True),
    ("time_min", "int", True),
    ("teaches", "list", True),
    ("prerequisites", "list", True),
    ("related", "list", True),
    ("tags", "list", True),
    ("cwe", "list", True),
    ("asvs", "list", True),
    ("wstg", "list", True),
    ("owasp", "list", True),
    ("labs", "list", True),
    ("sources", "list", True),
    # Два условных поля 9.3 и 9.6 п. 19. В двенадцати темах их нет: адаптаций
    # лицензированного материала пока не было, а правок после первой ревизии —
    # тоже. Схема их знает, чтобы первая же тема с ними не упала на
    # `C-FM-UNKNOWN`, и держит им место в каноническом порядке.
    ("derived_from", "list", False),
    ("updated", "date", False),
    ("reviewed", "date", True),
    ("review_interval", "int", True),
]
FIELDS = [name for name, _, _ in SCHEMA]
KINDS = {name: kind for name, kind, _ in SCHEMA}
REQUIRED = [name for name, _, req in SCHEMA if req]

KEBAB = re.compile(r"\A[a-z][a-z0-9]*(?:-[a-z0-9]+)*\Z")
PLAN_ID = re.compile(r"\At-(\d+)-(\d+)-(\d+)\Z")
IDENT = {
    "cwe": re.compile(r"\ACWE-\d+\Z"),
    "asvs": re.compile(r"\Av\d+\.\d+-\d+(?:\.\d+)+\Z"),
    "wstg": re.compile(r"\AWSTG-v\d+-[A-Z]+-\d+\Z"),
    "owasp": re.compile(r"\AA\d{2}:\d{4}\Z"),
    "labs": re.compile(r"\Alab-[a-z0-9-]+(?:-[a-z0-9]+)*\Z"),
}
# Те же четыре системы, но найденные в тексте, а не в шапке YAML. Формы шире
# `IDENT`: там выражение проверяет значение поля целиком, здесь — вырезает
# идентификатор из фразы, поэтому без якорей и с границей слова.
PRINTED = {
    "cwe": re.compile(r"\bCWE-\d+"),
    "asvs": re.compile(r"\bv\d+\.\d+-\d+(?:\.\d+)+"),
    "wstg": re.compile(r"\bWSTG-v\d+-[A-Z]+-\d+"),
    "owasp": re.compile(r"\bA\d{2}:\d{4}"),
}
INTERVALS = {6, 12, 24}          # 9.6 п. 20
MAX_PREREQ = 4                   # 9.4
MAX_RELATED = 5                  # 9.5 п. 8
TEACHES = (2, 5)                 # 9.3, часть 4 блок 1
TITLE_MAX = 60                   # 9.3
ORDER_STEP = 10                  # 9.1 п. 6

# Ссылки на план: тема «1.6.04», подраздел «1.5». Форма «тема N.N.NN» пишется в
# теле темы там, где страницы ещё нет, — по ней сборка ставит текст без ссылки,
# а проверка убеждается, что номер существует в плане.
PLAN_TOPIC_RE = re.compile(r"\bтем[аеуы]?\s+(\d+)\.(\d+)\.(\d+)", re.I)
PLAN_SUB_RE = re.compile(r"\bподраздел[аеу]?\s+(\d+)\.(\d+)\b", re.I)

# Шапка после чистки 2026-08-24: уровень и время, больше ничего. Код темы,
# `reviewed:`, «проверено на:» и маппинг со страницы убраны решением оператора —
# это данные о том, как тема писалась и проверялась, и живут они во frontmatter,
# `topics.yaml` и `audit.yaml`. Правило `C-HEAD-CLEAN` следит, чтобы они не
# вернулись на страницу.
HEAD_DEPTH_RE = re.compile(r"[Уу]ровень\s+\*\*(L[123])\*\*")
HEAD_TIME_RE = re.compile(r"время\s+(\d+)\s+мин")
HEAD_PARTS_RE = re.compile(r"\((?:теория|чтение)\s+(\d+)\s*/\s*(?:лаба|задача)\s+(\d+)"
                           r"\s*/\s*самопроверка\s+(\d+)")
TICK_RE = re.compile(r"`([^`]+)`")

# Предпосылки: человеческая фраза со ссылками на темы. Абзаца нет вовсе, когда
# предпосылок нет, — строка «пререквизитов нет» была служебной отметкой.
PREREQ_HEAD_RE = re.compile(r"\AЧто прочитать сначала:\s*(.+)\Z", re.S)

# Следы процесса, которым на странице темы больше не место (`C-HEAD-CLEAN`).
BANNED_HEAD = (
    (re.compile(r"\*\*AG-[A-Z]+-\d+\*\*"), "код темы `**AG-…**`"),
    (re.compile(r"reviewed:"), "дата ревизии `reviewed:`"),
    (re.compile(r"проверено на:"), "список «проверено на:»"),
    (re.compile(r"маппинг:"), "маппинг на CWE/ASVS/WSTG/Top 10"),
    (re.compile(r"пререквизит"), "служебное слово «пререквизиты»"),
    (re.compile(r"Состав блоков"), "декларация состава блоков"),
)

H2_RE = re.compile(r"\A##\s+(.+?)\s*\Z")
H2_NUM_RE = re.compile(r"\A(\d+)\.\s+(.+)\Z")
LIST_NUM_RE = re.compile(r"\A(\d+)\.\s+(.+)\Z")
LIST_DASH_RE = re.compile(r"\A-\s+(.+)\Z")

WHY = "**Зачем это в работе AppSec-инженера.**"
TRUST = "**Маркеры уверенности.**"
# 6.6 требует «Откуда это взялось» от каждой темы про механизм защиты или
# ограничение. Ищется подстрока, а не выделенный абзац: свод не назначает
# этому куску одного из шести типов врезок (7.6), и в наборе законны обе
# формы — абзац основного потока и врезка «Глубже» (оговорка 2026-08-23).
ORIGIN = "Откуда это взялось"


# ── загрузка ──────────────────────────────────────────────────────────────────


@dataclass
class Block:
    num: int
    title: str
    line: int
    start: int          # индекс строки после заголовка
    end: int            # индекс строки перед следующим заголовком


@dataclass
class Page:
    path: str
    doc: mdtext.Doc
    front: dict
    keys: list[str]
    lines: list[str]          # исходные строки — из них берётся текст
    plines: list[str]         # те же строки с забитыми фенсами — по ним структура
    h1: str = ""
    h1_line: int = 0
    head: str = ""              # шапка: первый абзац после h1
    head_line: int = 0
    prereq: str = ""            # абзац «Что прочитать сначала: …», если он есть
    prereq_line: int = 0
    intro: str = ""             # всё между h1 и первым `## `: там жили следы
    intro_line: int = 0
    blocks: list[Block] = None

    @property
    def id(self) -> str:
        return str(self.front.get("id") or Path(self.path).stem)

    @property
    def depth(self) -> str:
        return str(self.front.get("depth") or "")

    def at(self, key: str) -> int:
        """Строка поля frontmatter — чтобы замечание попадало в нужное место."""
        for i, line in enumerate(self.lines, 1):
            if line.startswith(f"{key}:"):
                return i
        return 1

    def block(self, num: int) -> Block | None:
        return next((b for b in self.blocks if b.num == num), None)

    def text_of(self, block: Block) -> list[str]:
        return self.lines[block.start:block.end]


def load_yaml(path: Path):
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def read_page(path) -> Page:
    """Одна страница в разобранном виде. Вынесено отдельно ради `lint_selftest`:
    правила уровня страницы — функции от `(Page, Ctx)`, и селф-тест зовёт их на
    фикстуре, не подкладывая ничего в `content/`."""
    doc = mdtext.load(path)
    front = yaml.safe_load(doc.front_text) if doc.front_text else {}
    if not isinstance(front, dict):
        front = {}
    keys = [m.group(1) for m in
            re.finditer(r"^([a-z_]+):", doc.front_text or "", re.M)]
    page = Page(
        path=str(path).replace("\\", "/"),
        doc=doc,
        front=front,
        keys=keys,
        lines=doc.raw.split("\n"),
        plines=doc.prose.split("\n"),
    )
    parse_body(page)
    return page


def load_pages() -> list[Page]:
    pages = [read_page(path) for path in mdtext.topics()]
    pages.sort(key=lambda p: (p.front.get("order", 10 ** 9), p.id))
    return pages


def parse_body(page: Page) -> None:
    """Разбор тела: h1, шапка, абзац предпосылок, блоки скелета.

    Структура ищется по `plines` — строкам с забитыми ограждёнными блоками.
    Иначе комментарий `# Псевдокод` внутри листинга сойдёт за заголовок.
    """
    lines = page.plines
    for i, line in enumerate(lines):
        if line.startswith("# ") and not line.startswith("##"):
            page.h1, page.h1_line = page.lines[i][2:].strip(), i + 1
            break

    # Шапка — первый абзац между h1 и первым `## `; следом может стоять абзац
    # предпосылок, а за ним — необязательный абзац о границах темы.
    paras: list[tuple[int, list[str]]] = []
    cur: list[str] = []
    start = 0
    for i in range(page.h1_line, len(lines)):
        line = lines[i]
        if line.startswith("## "):
            break
        if line.strip():
            if not cur:
                start = i + 1
            cur.append(line)
        elif cur:
            paras.append((start, cur))
            cur = []
    if cur:
        paras.append((start, cur))
    if paras:
        page.head_line = paras[0][0]
        page.head = "\n".join(page.lines[paras[0][0] - 1:paras[0][0] - 1 + len(paras[0][1])])
        page.intro_line = paras[0][0]
        page.intro = "\n".join(
            page.lines[paras[0][0] - 1:paras[-1][0] - 1 + len(paras[-1][1])])
    for line_no, body in paras[1:]:
        text = "\n".join(page.lines[line_no - 1:line_no - 1 + len(body)])
        if PREREQ_HEAD_RE.match(text):
            page.prereq_line, page.prereq = line_no, text
            break

    blocks: list[Block] = []
    heads = [(i, H2_RE.match(page.lines[i]).group(1))
             for i, line in enumerate(lines) if H2_RE.match(line)]
    for pos, (i, title) in enumerate(heads):
        end = heads[pos + 1][0] if pos + 1 < len(heads) else len(lines)
        m = H2_NUM_RE.match(title)
        num = int(m.group(1)) if m else -1
        name = m.group(2).strip() if m else title
        blocks.append(Block(num=num, title=name, line=i + 1, start=i + 1, end=end))
    page.blocks = blocks


def flat(text: str) -> str:
    """Текст в одну строку: ссылка в прозе законно переносится, сообщение — нет."""
    return re.sub(r"\s+", " ", text).strip()


def load_plan():
    """Индекс плана: темы и подразделы по номерам, как их пишет тело темы."""
    data = load_yaml(TOPICS)
    topics, subsections = {}, set()
    for stage in data.get("stages") or []:
        snum = int(stage["num"])
        for sub in stage.get("subsections") or []:
            subsections.add((snum, str(sub["num"])))
            for topic in sub.get("topics") or []:
                topics[topic["id"]] = {
                    "stage": snum,
                    "sub": str(sub["num"]),
                    "title": topic["title"],
                    "excluded": bool(stage.get("excluded")),
                }
    return topics, subsections


def load_sources() -> set[str]:
    data = load_yaml(SOURCES)
    return {s["id"] for s in (data.get("sources") or []) if isinstance(s, dict)}


def load_labs():
    data = load_yaml(LABS)
    return {lab["id"]: lab for lab in (data.get("labs") or [])}


class Ctx:
    def __init__(self):
        self.tax = load_yaml(TAXONOMY)
        self.stages = {s["slug"]: s for s in self.tax["stages"]}
        self.tags = set(self.tax["tags"])
        self.modes = set(self.tax["modes"])
        self.statuses = set(self.tax["statuses"])
        self.depths = set(self.tax["depths"])
        self.categories = set(self.tax["code_categories"])
        self.blocks = {b["num"]: b for b in self.tax["blocks"]}
        self.plan, self.subsections = load_plan()
        self.sources = load_sources()
        self.labs = load_labs()

    def required(self, depth: str) -> list[int]:
        return [n for n, b in self.blocks.items() if depth in (b.get("required") or [])]

    def allowed(self, depth: str) -> list[int]:
        return [n for n, b in self.blocks.items()
                if depth in (b.get("required") or []) + (b.get("allowed") or [])]

    def titles(self, num: int, depth: str) -> list[str]:
        b = self.blocks[num]
        out = [b["title"]]
        for alt, levels in (b.get("alt") or {}).items():
            if depth in levels:
                out.append(alt)
        return out


# ── C-FM-*: frontmatter ───────────────────────────────────────────────────────


def check_front(page: Page, ctx: Ctx) -> list[Finding]:
    out: list[Finding] = []
    f = page.front

    def add(rule, level, msg, key=None):
        out.append(Finding(page.path, page.at(key) if key else 1, 1, rule, level, msg))

    if not page.doc.front_text:
        add("C-FM-REQUIRED", ERROR, "нет frontmatter: тема — запись коллекции, "
                                    "а не свободный markdown")
        return out

    for name in REQUIRED:
        if name not in f:
            add("C-FM-REQUIRED", ERROR, f"нет обязательного поля `{name}`")
    for name in page.keys:
        if name not in KINDS:
            add("C-FM-UNKNOWN", ERROR,
                f"поле `{name}` не описано схемой (`SCHEMA.md` § 3)", name)

    known = [k for k in page.keys if k in KINDS]
    if known != sorted(known, key=FIELDS.index):
        first = next(k for k, nxt in zip(known, known[1:])
                     if FIELDS.index(nxt) < FIELDS.index(k))
        add("C-FM-SEQ", ERROR,
            f"поля идут не в порядке схемы: `{first}` стоит не на своём месте", first)

    for name, kind, _req in SCHEMA:
        if name not in f:
            continue
        val = f[name]
        ok = {"str": lambda v: isinstance(v, str),
              "int": lambda v: isinstance(v, int) and not isinstance(v, bool),
              "list": lambda v: isinstance(v, list),
              "date": lambda v: isinstance(v, dt.date)}[kind](val)
        if not ok:
            add("C-FM-TYPE", ERROR,
                f"поле `{name}`: ожидается {kind}, а стоит "
                f"{type(val).__name__} ({val!r:.40})", name)

    def lst(name) -> list:
        v = f.get(name)
        return v if isinstance(v, list) else []

    def text(name) -> str:
        v = f.get(name)
        return v if isinstance(v, str) else ""

    # id и связь с файлом
    stem = Path(page.path).stem
    if text("id") and text("id") != stem:
        add("C-FM-ID", ERROR,
            f"`id: {f['id']}` не совпадает с именем файла `{stem}.md`: "
            "адрес страницы выводится из id", "id")
    if text("id") and not KEBAB.match(text("id")):
        add("C-FM-ID", ERROR, f"`id: {f['id']}` не kebab-case", "id")

    # план
    pid = text("plan_id")
    if pid and not PLAN_ID.match(pid):
        add("C-FM-PLAN", ERROR, f"`plan_id: {pid}` не по форме `t-<этап>-<подраздел>-<NN>`",
            "plan_id")
    elif pid and pid not in ctx.plan:
        add("C-FM-PLAN", ERROR,
            f"`plan_id: {pid}` не разрешается в `topics.yaml`: такой темы в плане нет",
            "plan_id")

    # заголовок
    title = text("title")
    if title and page.h1 and title != page.h1:
        add("C-FM-TITLE", ERROR,
            f"`title` не совпадает с h1:\n    frontmatter: {title}\n    h1:          {page.h1}",
            "title")
    if len(title) > TITLE_MAX:
        add("C-FM-TITLE-LEN", ERROR,
            f"длина `title` — {len(title)} при норме ≤{TITLE_MAX} (9.3): "
            "заголовок такой длины не помещается в навигацию и карточку поиска",
            "title")

    summary = text("summary").strip()
    if summary:
        n = len(mdtext.sentences(summary))
        if not 1 <= n <= 2:
            add("C-FM-SUMMARY", WARNING,
                f"`summary` — {n} предложения при норме 1–2 (9.3): "
                "текст идёт в карточку поиска целиком", "summary")

    # словари
    stage = text("stage")
    if stage and stage not in ctx.stages:
        add("C-FM-VOCAB", ERROR,
            f"этап `{stage}` вне словаря `taxonomy.yaml`", "stage")
    elif stage:
        want = ctx.stages[stage]["dir"]
        have = Path(page.path).parent.name
        if have != want:
            add("C-FM-STAGE-DIR", ERROR,
                f"тема этапа `{stage}` лежит в `{have}/`, а этап живёт в `{want}/`: "
                "у темы ровно один этап-дом (9.1 п. 4)", "stage")
        if ctx.stages[stage].get("excluded"):
            add("C-FM-VOCAB", ERROR,
                f"этап `{stage}` исключён из гайдбука решением оператора", "stage")
    if text("status") and text("status") not in ctx.statuses:
        add("C-FM-VOCAB", ERROR, f"статус `{f['status']}` вне словаря", "status")
    if text("depth") and text("depth") not in ctx.depths:
        add("C-FM-VOCAB", ERROR, f"уровень `{f['depth']}` вне словаря", "depth")
    if text("mode") and text("mode") not in ctx.modes:
        add("C-FM-VOCAB", ERROR, f"режим `{f['mode']}` вне словаря", "mode")

    tags = lst("tags")
    if not tags:
        add("C-FM-VOCAB", ERROR, "нет ни одного тега: тема не попадёт ни в один фасет",
            "tags")
    for tag in tags:
        if tag not in ctx.tags:
            add("C-FM-VOCAB", ERROR,
                f"тег `{tag}` вне контролируемого словаря (9.2): "
                "добавьте его в `taxonomy.yaml` с одной строкой смысла", "tags")
    if len(tags) != len(set(tags)):
        add("C-FM-VOCAB", ERROR, "тег повторяется", "tags")

    # порядок
    order = f.get("order")
    if isinstance(order, int) and order % ORDER_STEP:
        add("C-FM-ORDER", ERROR,
            f"`order: {order}` не кратен {ORDER_STEP}: шаг нужен, чтобы вставка "
            "темы не требовала перенумерации (9.1 п. 6)", "order")

    if isinstance(f.get("time_min"), int) and f["time_min"] <= 0:
        add("C-FM-TYPE", ERROR, "`time_min` должен быть положительным", "time_min")

    # цели
    teaches = lst("teaches")
    if not TEACHES[0] <= len(teaches) <= TEACHES[1]:
        add("C-FM-TEACHES", ERROR,
            f"целей {len(teaches)} при норме {TEACHES[0]}–{TEACHES[1]} (9.3)", "teaches")
    for goal in teaches:
        if isinstance(goal, str) and goal[:1].islower():
            add("C-FM-TEACHES", ERROR,
                f"цель начинается со строчной: «{goal[:40]}»", "teaches")

    # связи
    prereq = lst("prerequisites")
    if len(prereq) > MAX_PREREQ:
        add("C-FM-PREREQ", ERROR,
            f"прямых предпосылок {len(prereq)} при пределе {MAX_PREREQ} (9.4): "
            "лишние — это связи через одну, они выводятся из графа", "prerequisites")
    if page.id in prereq:
        add("C-FM-PREREQ", ERROR, "тема стоит в своих же предпосылках", "prerequisites")
    related = lst("related")
    if len(related) > MAX_RELATED:
        add("C-FM-RELATED", ERROR,
            f"смежных тем {len(related)} при пределе {MAX_RELATED} (9.5 п. 8)", "related")
    if page.id in related:
        add("C-FM-RELATED", ERROR, "тема стоит в своих же смежных", "related")

    # внешние идентификаторы: всегда с версией (9.6 п. 25)
    for name, rx in IDENT.items():
        for val in lst(name):
            if not isinstance(val, str) or not rx.match(val):
                add("C-FM-IDENT", ERROR,
                    f"`{name}: {val}` не по форме `{rx.pattern[2:-2]}`: "
                    "внешний идентификатор печатается с версией", name)

    if len(lst("sources")) < 2:
        add("C-FM-SOURCES", ERROR,
            f"источников {len(lst('sources'))}: тема опирается минимум на два "
            "первоисточника (DoD 8; верхней границы нет)", "sources")
    for field in ("sources", "derived_from"):
        for sid in lst(field):
            if sid not in ctx.sources:
                add("C-REF-SOURCE", ERROR,
                    f"источник `{sid}` не найден в `sources.yaml`", field)
    for lid in lst("labs"):
        if lid not in ctx.labs:
            add("C-REF-LAB", ERROR, f"лаба `{lid}` не найдена в `labs.yaml`", "labs")
        elif ctx.labs[lid].get("topic") != page.id:
            add("C-REF-LAB", ERROR,
                f"лаба `{lid}` в `labs.yaml` числится за темой "
                f"`{ctx.labs[lid].get('topic')}`", "labs")

    # ревизия
    reviewed = f.get("reviewed")
    interval = f.get("review_interval")
    if isinstance(reviewed, dt.date) and reviewed > TODAY:
        add("C-FM-DATE", ERROR, f"`reviewed: {reviewed}` в будущем", "reviewed")
    if isinstance(interval, int) and interval not in INTERVALS:
        add("C-FM-VOCAB", ERROR,
            f"`review_interval: {interval}` не из набора {sorted(INTERVALS)} (9.6 п. 20)",
            "review_interval")
    if isinstance(reviewed, dt.date) and isinstance(interval, int):
        months = (TODAY.year - reviewed.year) * 12 + TODAY.month - reviewed.month
        if months > interval:
            add("C-FM-REVIEW", WARNING,
                f"ревизия просрочена: прошло {months} мес. при интервале {interval}",
                "reviewed")
    return out


# ── C-REF-*: связи между записями ─────────────────────────────────────────────


def check_refs(pages: list[Page], ctx: Ctx) -> list[Finding]:
    out: list[Finding] = []
    ids = {}
    for page in pages:
        if page.id in ids:
            out.append(Finding(page.path, page.at("id"), 1, "C-FM-ID", ERROR,
                               f"id `{page.id}` уже занят темой `{ids[page.id]}`"))
        ids[page.id] = page.path

    # plan_id: один к одному, этап совпадает
    plan_used = {}
    for page in pages:
        pid = page.front.get("plan_id")
        if not isinstance(pid, str) or pid not in ctx.plan:
            continue
        if pid in plan_used:
            out.append(Finding(page.path, page.at("plan_id"), 1, "C-FM-PLAN", ERROR,
                               f"`plan_id: {pid}` уже занят темой `{plan_used[pid]}`"))
        plan_used[pid] = page.id
        stage = ctx.stages.get(str(page.front.get("stage")))
        if stage and ctx.plan[pid]["stage"] != stage["num"]:
            out.append(Finding(
                page.path, page.at("plan_id"), 1, "C-FM-PLAN", ERROR,
                f"`plan_id: {pid}` относится к этапу {ctx.plan[pid]['stage']} плана, "
                f"а `stage: {stage['slug']}` — это этап {stage['num']}"))

    # order уникален внутри этапа
    seen = defaultdict(dict)
    for page in pages:
        stage, order = page.front.get("stage"), page.front.get("order")
        if not isinstance(order, int):
            continue
        if order in seen[stage]:
            out.append(Finding(page.path, page.at("order"), 1, "C-FM-ORDER", ERROR,
                               f"`order: {order}` внутри этапа уже занят темой "
                               f"`{seen[stage][order]}`"))
        seen[stage][order] = page.id

    # ссылки по id
    for page in pages:
        for field in ("prerequisites", "related"):
            for ref in page.front.get(field) or []:
                if ref not in ids:
                    out.append(Finding(
                        page.path, page.at(field), 1, "C-REF-TOPIC", ERROR,
                        f"`{field}: {ref}` — темы с таким id нет. Ссылка на ещё "
                        "не написанную тему пишется в прозе номером плана "
                        "(«тема 1.1.09»), а не идентификатором"))

    # цикл в графе предпосылок
    graph = {p.id: [r for r in (p.front.get("prerequisites") or []) if r in ids]
             for p in pages}
    by_id = {p.id: p for p in pages}
    color: dict[str, int] = {}
    stack: list[str] = []

    def walk(node: str) -> list[str] | None:
        color[node] = 1
        stack.append(node)
        for nxt in graph.get(node, []):
            if color.get(nxt) == 1:
                return stack[stack.index(nxt):] + [nxt]
            if color.get(nxt, 0) == 0:
                cycle = walk(nxt)
                if cycle:
                    return cycle
        stack.pop()
        color[node] = 2
        return None

    for node in graph:
        if color.get(node, 0) == 0:
            cycle = walk(node)
            if cycle:
                page = by_id[cycle[0]]
                out.append(Finding(page.path, page.at("prerequisites"), 1,
                                   "C-REF-CYCLE", ERROR,
                                   "цикл в графе предпосылок: " + " → ".join(cycle)))
                break

    # сироты: 9.4, предупреждение
    incoming = defaultdict(set)
    for page in pages:
        for ref in (page.front.get("prerequisites") or []) + (page.front.get("related") or []):
            if ref in ids and ref != page.id:
                incoming[ref].add(page.id)
        nxt = page.block(13)
        if nxt:
            for span in TICK_RE.findall("\n".join(page.text_of(nxt))):
                if span in ids and span != page.id:
                    incoming[span].add(page.id)
    for page in pages:
        if not incoming[page.id]:
            out.append(Finding(page.path, page.at("id"), 1, "C-REF-ORPHAN", WARNING,
                               "на тему не ссылается ни одна другая тема: в каталоге "
                               "она есть, в маршруте читателя её нет"))

    # ссылки на план в прозе
    for page in pages:
        prose = page.doc.prose
        for m in PLAN_TOPIC_RE.finditer(prose):
            pid = f"t-{int(m.group(1))}-{int(m.group(2))}-{m.group(3)}"
            if pid in ctx.plan:
                continue
            line, col = page.doc.pos(m.start())
            out.append(Finding(page.path, line, col, "C-REF-PLAN", ERROR,
                               f"«{flat(m.group(0))}» — такой темы в плане нет "
                               f"(искали `{pid}` в `topics.yaml`)"))
        for m in PLAN_SUB_RE.finditer(prose):
            key = (int(m.group(1)), f"{int(m.group(1))}.{int(m.group(2))}")
            if key in ctx.subsections:
                continue
            line, col = page.doc.pos(m.start())
            out.append(Finding(page.path, line, col, "C-REF-PLAN", ERROR,
                               f"«{flat(m.group(0))}» — такого подраздела в плане нет"))
    return out


# ── C-HEAD-*: шапка против frontmatter ────────────────────────────────────────
#
# Шапка темы — то немногое из frontmatter, что нужно читателю перед чтением:
# уровень и время с разбивкой. Остальное — дата ревизии, версии документов, код
# темы, маппинг на каталоги — данные о производстве темы; они остаются во
# frontmatter, `topics.yaml` и `audit.yaml`, а на страницу не выносятся
# (решение оператора 2026-08-24). Предпосылки печатаются отдельным абзацем
# человеческой фразой и только тогда, когда они есть.


def check_head(page: Page, ctx: Ctx) -> list[Finding]:
    out: list[Finding] = []
    head, line = page.head, page.head_line or 1

    def add(rule, level, msg, at=None):
        out.append(Finding(page.path, at or line, 1, rule, level, msg))

    if not head:
        add("C-HEAD-DEPTH", ERROR, "нет шапки темы: часть 4 требует её до блока 0")
        return out

    # Ищется по всей вводной части — от h1 до первого `## `. Иначе след,
    # вернувшийся не в первый абзац, а в соседний, правило не увидит.
    for rx, what in BANNED_HEAD:
        if rx.search(page.intro):
            add("C-HEAD-CLEAN", ERROR,
                f"во вводной части темы снова {what}: со страницы это убрано "
                "решением оператора 2026-08-24, данные живут во frontmatter, "
                "`topics.yaml` и `audit.yaml`", page.intro_line or line)

    m = HEAD_DEPTH_RE.search(head)
    if not m:
        add("C-HEAD-DEPTH", ERROR, "в шапке нет уровня вида `Уровень **L2**`")
    elif m.group(1) != page.depth:
        add("C-HEAD-DEPTH", ERROR,
            f"в шапке уровень {m.group(1)}, во frontmatter `depth: {page.depth}`")

    m = HEAD_TIME_RE.search(head)
    time_min = page.front.get("time_min")
    if not m:
        add("C-HEAD-TIME", ERROR, "в шапке нет времени вида `время 30 мин`")
    else:
        total = int(m.group(1))
        if isinstance(time_min, int) and total != time_min:
            add("C-HEAD-TIME", ERROR,
                f"в шапке {total} мин, во frontmatter `time_min: {time_min}`")
        parts = HEAD_PARTS_RE.search(head)
        if parts:
            summed = sum(int(x) for x in parts.groups())
            if summed != total:
                add("C-HEAD-TIME", ERROR,
                    f"слагаемые времени дают {summed} мин, а объявлено {total}")
        elif page.depth != "L3":
            add("C-HEAD-TIME", ERROR,
                "нет разбивки времени вида `(теория 15 / задача 10 / самопроверка 5)`")

    prereq = [str(x) for x in (page.front.get("prerequisites") or [])]
    if not page.prereq:
        got = []
    else:
        m = PREREQ_HEAD_RE.match(page.prereq)
        got = TICK_RE.findall(m.group(1)) if m else None
    if got is None:
        add("C-HEAD-PREREQ", ERROR,
            "абзац предпосылок не по форме «Что прочитать сначала: `id`, `id`.»",
            page.prereq_line or line)
    elif got != prereq:
        add("C-HEAD-PREREQ", ERROR,
            f"предпосылки на странице {got or '—'} не совпадают с frontmatter "
            f"{prereq or '—'}; при пустом списке абзаца быть не должно",
            page.prereq_line or line)
    return out


# ── C-BLOCK-*: скелет части 4 ───────────────────────────────────────


def check_blocks(page: Page, ctx: Ctx) -> list[Finding]:
    out: list[Finding] = []
    depth = page.depth
    if depth not in ctx.depths:
        return out

    def add(rule, level, msg, line=1):
        out.append(Finding(page.path, line, 1, rule, level, msg))

    nums: list[int] = []
    for b in page.blocks:
        if b.num < 0:
            add("C-BLOCK-SHAPE", ERROR,
                f"заголовок «{b.title}» не по форме `## N. Название`: блоки скелета "
                "нумерованы, и по номеру их сравнивают между темами", b.line)
            continue
        if b.num not in ctx.blocks:
            add("C-BLOCK-NUM", ERROR,
                f"блока {b.num} в скелете части 4 нет (номера 0–14)", b.line)
            continue
        titles = ctx.titles(b.num, depth)
        if b.title not in titles:
            add("C-BLOCK-TITLE", ERROR,
                f"блок {b.num} назван «{b.title}», канон — "
                + " / ".join(f"«{t}»" for t in titles), b.line)
        nums.append(b.num)

    if nums != sorted(nums):
        numbered = [b for b in page.blocks if b.num >= 0 and b.num in ctx.blocks]
        first = next((b.line for a, b in zip(numbered, numbered[1:])
                      if b.num < a.num), page.h1_line or 1)
        add("C-BLOCK-ORDER", ERROR,
            "блоки переставлены: " + ", ".join(str(n) for n in nums)
            + ". Отклонение от канона части 4 допускается только удалением",
            first)
    dup = sorted({n for n in nums if nums.count(n) > 1})
    if dup:
        add("C-BLOCK-ORDER", ERROR,
            "блок встречается второй раз: " + ", ".join(str(n) for n in dup))

    have = set(nums)
    for num in sorted(set(ctx.required(depth)) - have):
        add("C-BLOCK-REQ", ERROR,
            f"нет блока {num} «{ctx.blocks[num]['title']}», обязательного на {depth}")
    for num in sorted(have - set(ctx.allowed(depth))):
        add("C-BLOCK-EXTRA", ERROR,
            f"блок {num} «{ctx.blocks[num]['title']}» на уровне {depth} не предусмотрен "
            f"(`SCHEMA.md` § 4)", page.block(num).line)

    return out


# ── C-BODY-*: служебный аппарат и наполнение блоков ───────────────────────────


def norm(text: str) -> str:
    text = text.replace("ё", "е").replace("`", "").lower()
    text = re.sub(r"[\s ]+", " ", text)
    return text.strip(" .;:")


def items(page: Page, block: Block, dash: bool = False) -> list[tuple[int, str]]:
    """Пункты списка блока: (строка, текст с подклеенными продолжениями)."""
    out: list[tuple[int, str]] = []
    rx = LIST_DASH_RE if dash else LIST_NUM_RE
    for i in range(block.start, block.end):
        line = page.plines[i] if i < len(page.plines) else ""
        raw = page.lines[i]
        m = rx.match(line)
        if m:
            out.append((i + 1, raw.split(". ", 1)[-1] if not dash else raw[2:]))
        elif out and raw.startswith("   ") and raw.strip():
            out[-1] = (out[-1][0], out[-1][1] + " " + raw.strip())
    return out


def check_body(page: Page, ctx: Ctx) -> list[Finding]:
    out: list[Finding] = []
    depth = page.depth

    def add(rule, level, msg, line=1):
        out.append(Finding(page.path, line, 1, rule, level, msg))

    body = "\n".join(page.lines[page.h1_line:]) if page.h1_line else page.doc.raw
    for marker, rule, why in ((WHY, "C-BODY-WHY", "DoD 6"),
                              (TRUST, "C-BODY-TRUST", "DoD 12")):
        n = body.count(marker)
        if n == 0:
            add(rule, ERROR, f"нет абзаца «{marker.strip('*')}» ({why})")
        elif n > 1:
            add(rule, ERROR, f"абзац «{marker.strip('*')}» встречается {n} раза")

    # Повтор здесь не считается ошибкой, в отличие от двух правил выше: тема
    # вправе рассказать, откуда взялись два механизма, а вот отсутствие
    # рассказа — то самое место, на котором приёмка остановилась (Ф-36).
    if ORIGIN not in body:
        add("C-BODY-ORIGIN", ERROR,
            f"нет врезки «{ORIGIN}»: что было до, что сломалось, что придумали "
            f"(6.6)")

    # блок 1 отражает teaches
    teaches = [str(t) for t in (page.front.get("teaches") or [])]
    goals = page.block(1)
    if goals and teaches:
        listed = items(page, goals)
        if len(listed) != len(teaches):
            add("C-BODY-GOALS", ERROR,
                f"в блоке 1 целей {len(listed)}, во frontmatter `teaches` — "
                f"{len(teaches)}: читатель и сборка должны видеть один список",
                goals.line)
        # Формулировка не сверяется дословно: `teaches` — короткая форма для
        # карточек и поиска, блок 1 — фраза для читателя, и 11.1 стадия 2
        # требует от автоматики только наличия блока с 2–5 целями. Правило
        # ловит другое: цель, которая не про то же самое (список скопирован из
        # соседней темы). Порог 0.55 при минимуме 0.73 на корпусе — запас,
        # чтобы пересказ не шумел.
        for (line_no, text), goal in zip(listed, teaches):
            a, b = norm(text), norm(goal)
            if a == b or difflib.SequenceMatcher(None, a, b).ratio() >= 0.55:
                continue
            add("C-BODY-GOALS", ERROR,
                f"цель из frontmatter не отражена в блоке 1:\n"
                f"    блок 1:      {text}\n    frontmatter: {goal}", line_no)

    # блок 10: чеклист
    check = page.block(10)
    if check:
        listed = items(page, check)
        if not 5 <= len(listed) <= 8:
            add("C-BODY-CHECKLIST", ERROR,
                f"в чеклисте {len(listed)} пунктов при норме 5–8 (часть 4)", check.line)
        elif depth == "L2" and len(listed) > 7:
            add("C-BODY-CHECKLIST", WARNING,
                f"в чеклисте {len(listed)} пунктов: DoD 8 просит для L2 5–7", check.line)
        for line_no, text in listed:
            if not text.startswith("Verify that"):
                add("C-BODY-CHECKLIST", ERROR,
                    f"пункт чеклиста не в залоге «Verify that…»: {text[:50]}", line_no)

    # блок 12: самопроверка
    self_check = page.block(12)
    if self_check:
        raw = page.lines[self_check.start:self_check.end]
        split = next((i for i, line in enumerate(raw) if line.startswith("<details>")), None)
        if split is None:
            add("C-BODY-SELFCHECK", ERROR,
                "в блоке 12 нет `<details>` с ответами: ответы под спойлером, "
                "но обязательно есть (часть 4)", self_check.line)
        else:
            qs = [line for line in raw[:split] if LIST_NUM_RE.match(line)]
            ans = [line for line in raw[split:] if LIST_NUM_RE.match(line)]
            back = [line for line in qs if "озврат к теме" in line]
            if len(qs) != len(ans):
                add("C-BODY-SELFCHECK", ERROR,
                    f"вопросов {len(qs)}, ответов {len(ans)}", self_check.line)
            repro = len(qs) - len(back)
            if not 4 <= repro <= 6:
                add("C-BODY-SELFCHECK", ERROR,
                    f"вопросов на воспроизведение {repro} при норме 4–6 (часть 4)",
                    self_check.line)
            if page.front.get("prerequisites") and not 1 <= len(back) <= 2:
                add("C-BODY-SELFCHECK", ERROR,
                    f"вопросов на возврат к прошлым темам {len(back)} при норме 1–2 "
                    "(часть 4). Возврат опускается только у темы без предпосылок",
                    self_check.line)

    # блок 13: навигация вперёд
    nxt = page.block(13)
    if nxt:
        listed = items(page, nxt, dash=True)
        if not 1 <= len(listed) <= 5:
            add("C-BODY-NEXT", ERROR,
                f"в блоке 13 пунктов {len(listed)} при норме 1–5 (9.5 п. 8)", nxt.line)
        for line_no, text in listed:
            has_id = any(span for span in TICK_RE.findall(text))
            has_plan = PLAN_TOPIC_RE.search(text) or PLAN_SUB_RE.search(text)
            if not has_id and not has_plan:
                add("C-BODY-NEXT", ERROR,
                    "пункт блока 13 не называет ни темы (`id`), ни номера плана: "
                    f"{flat(text)[:60]}", line_no)

    # блок 14: источники
    src = page.block(14)
    declared = {str(s) for s in (page.front.get("sources") or [])}
    if src:
        listed = items(page, src)
        if len(listed) < 2:
            add("C-BODY-SOURCES", ERROR,
                f"сносок в блоке 14 — {len(listed)}: первоисточников минимум два "
                "(DoD 8; верхней границы нет)", src.line)
        # Реестровые идентификаторы берутся только из сносок. Абзац после них
        # («Каркас этапа: `owasp-asvs-5-document`, …») называет источники,
        # унаследованные всем этапом: они законно не повторяются в `sources`
        # каждой темы, и ловить их — учить автора пролистывать вывод.
        named = {span for _, text in listed
                 for span in TICK_RE.findall(text) if span in ctx.sources}
        for sid in sorted(declared - named):
            add("C-BODY-SOURCES", ERROR,
                f"источник `{sid}` объявлен во frontmatter, но в блоке 14 не назван: "
                "читатель не увидит, откуда взято", src.line)
        for sid in sorted(named - declared):
            add("C-BODY-SOURCES", ERROR,
                f"в блоке 14 назван источник `{sid}`, которого нет во frontmatter",
                src.line)

    # Внешние идентификаторы: напечатанное входит в объявленное.
    #
    # Frontmatter — указатель: по нему тему находят, спрашивая «где про 7.4.2».
    # Требование, названное в тексте, но не объявленное, из указателя выпадает —
    # ошибка.
    #
    # Обратная сверка (объявлено, но нигде не напечатано) снята 2026-08-24
    # вместе с маппингом: до чистки маппинг печатался в шапке, поэтому «не
    # напечатан» значило «тема заявлена в указателе, а разбора нет». Теперь
    # идентификаторы на странице стоят только там, где о них идёт речь, и
    # ненапечатанный номер — норма, а не дефект. Указатель по-прежнему сверяется
    # с каталогами: это делает `audit.yaml` и маппинг-индекс сборки.
    #
    # Считается вся страница после h1, вместе с листингами: читателю видно и то
    # и другое, а «напечатано» здесь значит именно «читатель это видит».
    for field, pat in PRINTED.items():
        listed_ids = {str(x) for x in (page.front.get(field) or [])}
        for ident in sorted(set(pat.findall(body)) - listed_ids):
            add("C-BODY-IDENT", ERROR,
                f"в тексте напечатан {ident}, а во frontmatter `{field}` его нет: "
                "по указателю тему не найти", page.at(field))
    return out


# ── сборка ────────────────────────────────────────────────────────────────────


def collect() -> list[Finding]:
    ctx = Ctx()
    pages = load_pages()
    findings: list[Finding] = []
    for page in pages:
        findings += check_front(page, ctx)
        findings += check_head(page, ctx)
        findings += check_blocks(page, ctx)
        findings += check_body(page, ctx)
    findings += check_refs(pages, ctx)
    findings.sort(key=Finding.sort_key)
    return findings


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--json", action="store_true",
                    help="по одному объекту JSON на замечание, с уровнем: "
                         "этим форматом замечания читает tools/check.py")
    ap.add_argument("--summary", action="store_true",
                    help="печатать сводку по правилам вместо списка замечаний")
    args = ap.parse_args()

    findings = collect()
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
            print(f"{rule:<20} {level:<8} {n}")
    else:
        for f in findings:
            print(f)

    errors = sum(1 for f in findings if f.level == ERROR)
    if not args.json:
        print(f"\nvalidate_content: {errors} error, {len(findings) - errors} warning",
              file=sys.stderr)
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
