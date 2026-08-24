#!/usr/bin/env python3
"""Ссылки в темах: внутренние разрешаются, внешние стоят там, где им можно.

Пункт DoD 17 «Битых ссылок нет» распадается на четыре разных вопроса, и
инструмент отвечает на каждый отдельным правилом:

* `S-EXT-IN-BODY`    (error)   внешний адрес вне блока 14 — `SCOPE.md` § 6;
* `S-LINK-BARE`      (error)   внешний адрес в прозе без `<…>`: python-markdown
                               сам ссылок не делает, и читатель получит текст;
* `S-LINK-TOPIC`     (error)   ссылка на тему, которой нет, — 9.4;
* `S-LINK-MD`        (error)   markdown-ссылка на страницу или анкорь, которых
                               нет, — 9.4;
* `S-LINK-SOURCE-URL`(warning) адрес в сноске расходится с `url` реестровой
                               записи, названной в той же сноске;
* `S-LINK-EXT`       (warning) внешний адрес не открывается — 9.4 относит битую
                               внешнюю ссылку к предупреждениям. Отказ вида 403,
                               429 или 503 перепроверяется `curl`: за ним обычно
                               стоит антибот-щит, а не битая ссылка.

Проверка адресов ходит в сеть и потому включается флагом `--external`. Причина
не в скорости: красный вердикт `make check` должен означать «текст сломан», а не
«сети нет». Свод и сам ставит битую внешнюю ссылку в предупреждения, то есть в
разряд «печатается, сборку не роняет».

Реестр `sources.yaml` этот инструмент не обходит: 307 адресов реестра — забота
`validate.py` и автора, а здесь проверяется то, на что нажмёт читатель, то есть
автоссылки самих тем.

Формат вывода — `путь:строка:столбец:ПРАВИЛО:сообщение`, как у Vale. Выход 1,
если есть ошибка. Содержимое `content/**` скрипт только читает.
"""

from __future__ import annotations

import argparse
import concurrent.futures as cf
import json
import re
import shutil
import subprocess
import sys
import unicodedata
import urllib.error
import urllib.request
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import yaml

import mdtext

ERROR, WARNING = "error", "warning"

SOURCES = Path("sources.yaml")
# Два блока опознаются по заголовку, а не по номеру: скелетов в своде 4.2 два,
# и в скелете инструмента «Источники» — тринадцатый блок, а не четырнадцатый.
# Заголовок у обоих скелетов общий, поэтому он и есть признак.
SOURCES_BLOCK = "Источники"   # единственное место для внешних адресов
NEXT_BLOCK = "Дальше"

H2_RE = re.compile(r"^##\s*(\d+)\.\s*(.+?)\s*$", re.M)
HEAD_RE = re.compile(r"^(#{1,6})[ \t]+(.+?)[ \t]*$", re.M)
ATTR_ID_RE = re.compile(r"\{\s*#([^}\s]+)\s*\}\s*$")
TICK_RE = re.compile(r"`([^`]+)`")
MD_LINK_RE = re.compile(r"!?\[(?P<text>[^\]]*)\]\((?P<target>[^)\s]*)"
                        r"(?:[ \t]+(?P<title>\"[^\"]*\"|'[^']*'))?\)")
# Пункт блока 13, начинающийся с идентификатора темы: «- `cookies` — …».
NEXT_ITEM_RE = re.compile(r"^[ \t]*[-*+][ \t]+`([^`]+)`", re.M)
# Ссылка на тему в прозе: слово «тема» в любом падеже и сразу идентификатор.
# Так написаны и «Возврат к теме `cookies`», и «см. тему `http-basics`».
# Группа 1 — слово перед «темой», по нему отсекается указание на саму страницу.
THEME_REF_RE = re.compile(r"(?:(\w+)\s+)?\bтем[аеиоуыюя]{0,2}\s+`([^`]+)`", re.I)
# «В этой теме `Set-Cookie` разбирается ниже» — не ссылка: «эта тема» и есть
# страница, на которой стоит фраза, а код после неё называет не тему, а поле.
# Список закрытый и растёт по находке.
SELF_REF = {"эта", "эту", "этой", "этом", "эти", "данной", "данная", "нашей",
            "текущей", "своей", "каждой", "любой", "той", "одной"}
# Идентификатор темы — строчная латиница, цифры и дефис: так заведены все
# двенадцать. Отрицательная проверка, а не догадка: `Set-Cookie`, `HttpOnly` и
# `SameSite` этой форме не отвечают и ссылкой на тему быть не могут.
ID_SHAPE_RE = re.compile(r"^[a-z][a-z0-9]*(?:-[a-z0-9]+)*$")
# Нумерованная сноска блока 14 начинается с «N. » в начале строки.
FOOTNOTE_RE = re.compile(r"^(\d+)\.[ \t]", re.M)

# Версия в строке — не украшение: антибот-щиты отбивают устаревшие браузеры.
# Замер 2026-08-23: `https://www.w3.org/TR/CSP3/` отвечает 403 на `Chrome/126.0`
# и 200 на `Chrome/152.0.0.0` — тем же запросом, с той же машины, в ту же минуту.
# Отсюда правило: подновлять версию, когда проверка начнёт получать 403 от
# хостов, открывающихся в браузере.
UA = ("Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/152.0.0.0 Safari/537.36")


class Finding:
    __slots__ = ("path", "line", "col", "rule", "level", "message")

    def __init__(self, path, line, col, rule, level, message):
        self.path, self.line, self.col = str(path), line, col
        self.rule, self.level, self.message = rule, level, message

    def __str__(self):
        return f"{self.path}:{self.line}:{self.col}:{self.rule}:{self.message}"

    def sort_key(self):
        return (self.path, self.line, self.col, self.rule)


def _blank(s: str) -> str:
    return re.sub(r"[^\n]", " ", s)


def linkable(doc) -> str:
    """Проза без инлайнового кода, но с адресами и ссылками на месте.

    `mdtext.load` отдаёт три маски, и ни одна не годится: `prose` затирает
    адреса вместе с кодом (правилам о языке они мешают), `prose_spans` оставляет
    инлайновый код, в котором адрес — пример, а не ссылка (`https://evil.com` в
    теме про `CORS`). Здесь снимается ровно инлайновый код: frontmatter и
    листинги уже сняты, смещения сохранены.
    """
    return mdtext.CODE_SPAN_RE.sub(lambda m: _blank(m.group(0)), doc.prose_spans)


def blocks_of(doc) -> list[tuple[int, str]]:
    """Начала блоков канона: (смещение, заголовок), по возрастанию смещения."""
    return [(m.start(), m.group(2)) for m in H2_RE.finditer(doc.raw)]


def block_at(marks: list[tuple[int, str]], offset: int) -> str | None:
    """Заголовок блока, внутри которого стоит смещение; None — до первого."""
    cur = None
    for start, title in marks:
        if start <= offset:
            cur = title
        else:
            break
    return cur


def slug(text: str) -> str:
    """Анкорь заголовка так, как его сделает сборка.

    Совпадает с `pymdownx.slugs.slugify(case="lower")`, который включён в
    `mkdocs.yml`. Умолчание python-markdown не годится: оно выбрасывает всё вне
    ASCII, и от «## 3. Механика» остаётся анкорь «3». Если в `mkdocs.yml`
    поменяют slugify, поменять надо и здесь — иначе правило `S-LINK-MD` начнёт
    ругаться на живые анкоря.
    """
    text = ATTR_ID_RE.sub("", text)
    text = re.sub(r"`([^`]*)`", r"\1", text)
    text = re.sub(r"[*_]{1,2}([^*_]+)[*_]{1,2}", r"\1", text)
    text = unicodedata.normalize("NFC", text)
    text = re.sub(r"[^\w\s-]", "", text, flags=re.U).strip().lower()
    return re.sub(r"\s+", "-", text)


def anchors_of(doc) -> set[str]:
    out = set()
    for m in HEAD_RE.finditer(doc.prose_spans):
        title = doc.raw[m.start(2):m.end(2)]
        explicit = ATTR_ID_RE.search(title)
        out.add(explicit.group(1) if explicit else slug(title))
    return out


def load_ids(paths: list[Path]) -> dict[str, Path]:
    """`id` → файл. Берутся и весь корпус, и переданные пути.

    Переданные пути добавляются ради селф-теста: его фикстуры лежат вне
    `content/`, ссылаются на настоящие темы и должны разрешаться. Обратное тоже
    верно: фикстура, ссылающаяся на другую фикстуру, разрешается.
    """
    out: dict[str, Path] = {}
    for path in list(mdtext.topics()) + list(paths):
        doc = mdtext.load(path)
        if not doc.front_text:
            continue
        front = yaml.safe_load(doc.front_text) or {}
        ident = front.get("id")
        if isinstance(ident, str):
            out.setdefault(ident, path)
    return out


def load_source_urls() -> dict[str, str]:
    if not SOURCES.exists():
        return {}
    data = yaml.safe_load(SOURCES.read_text(encoding="utf-8")) or {}
    out = {}
    for rec in data.get("sources", []):
        if isinstance(rec, dict) and rec.get("id"):
            out[rec["id"]] = (rec.get("url") or "").strip()
    return out


# --- внешние адреса ---------------------------------------------------------

def external_links(doc) -> list[tuple[int, str, bool]]:
    """Все внешние адреса прозы: (смещение, адрес, автоссылка ли)."""
    text = linkable(doc)
    out = []
    for m in mdtext.AUTOLINK_RE.finditer(text):
        out.append((m.start(), m.group(0)[1:-1], True))
    masked = mdtext.AUTOLINK_RE.sub(lambda m: _blank(m.group(0)), text)
    # Адрес внутри markdown-ссылки — не «голый»: ссылкой он станет.
    masked = MD_LINK_RE.sub(lambda m: _blank(m.group(0)), masked)
    for m in mdtext.BARE_URL_RE.finditer(masked):
        out.append((m.start(), m.group(0).rstrip(".,;:)»"), False))
    out.sort()
    return out


def check_external_placement(path, doc, marks) -> list[Finding]:
    out = []
    for off, url in ((o, u) for o, u, _a in external_links(doc)):
        block = block_at(marks, off)
        if block != SOURCES_BLOCK:
            where = f"блоке «{block}»" if block is not None else "шапке темы"
            line, col = doc.pos(off)
            out.append(Finding(
                path, line, col, "S-EXT-IN-BODY", ERROR,
                f"внешний адрес в {where}: {url}. Границу самодостаточности "
                f"задаёт SCOPE.md § 6 — вне блока «{SOURCES_BLOCK}» внешний "
                "адрес может стоять только носителем содержания"))
    for off, url, auto in external_links(doc):
        if not auto:
            line, col = doc.pos(off)
            out.append(Finding(
                path, line, col, "S-LINK-BARE", ERROR,
                f"адрес {url} записан без угловых скобок: ссылкой он не станет, "
                "python-markdown голые адреса не размечает. Нужно <…> либо "
                "обратные кавычки, если это пример, а не ссылка"))
    return out


def check_source_urls(path, doc, marks, source_urls) -> list[Finding]:
    """Адрес сноски против `url` реестровой записи, названной в той же сноске."""
    start = next((s for s, title in marks if title == SOURCES_BLOCK), None)
    if start is None:
        return []
    end = next((s for s, n in marks if s > start), len(doc.raw))
    text = linkable(doc)
    cuts = [start + m.start() for m in FOOTNOTE_RE.finditer(doc.raw[start:end])]
    out = []
    for i, cut in enumerate(cuts):
        stop = cuts[i + 1] if i + 1 < len(cuts) else end
        chunk = doc.raw[cut:stop]
        ids = [s for s in TICK_RE.findall(chunk) if s in source_urls]
        if not ids:
            continue
        for m in mdtext.AUTOLINK_RE.finditer(text[cut:stop]):
            url = m.group(0)[1:-1]
            registry = source_urls[ids[0]]
            if registry and url != registry:
                line, col = doc.pos(cut + m.start())
                out.append(Finding(
                    path, line, col, "S-LINK-SOURCE-URL", WARNING,
                    f"адрес сноски {url} не совпадает с `url` записи "
                    f"`{ids[0]}` ({registry}): читатель и реестр смотрят в "
                    "разные места. Законно, когда сноска ведёт на сам файл, а "
                    "реестр — на страницу документа"))
    return out


# --- внутренние ссылки ------------------------------------------------------

def check_topic_refs(path, doc, marks, ids) -> list[Finding]:
    """Ссылка на тему в прозе и в блоке 13 разрешается в написанную тему.

    Шапка темы («пререквизиты: `a`, `b`») здесь не проверяется: её сверяют
    `C-HEAD-PREREQ` (совпадение с frontmatter) и `C-REF-TOPIC` (разрешение
    самого frontmatter). Два правила на одно и то же место дали бы два
    сообщения об одном дефекте.
    """
    # Идентификатор темы стоит в обратных кавычках (6.4 требует ставить в код
    # всё машинное), поэтому здесь нужна маска, инлайновый код сохраняющая:
    # `linkable` затёрла бы ровно то, что проверяется.
    text = doc.prose_spans
    spots: list[tuple[int, str, str]] = []

    start = next((s for s, title in marks if title == NEXT_BLOCK), None)
    if start is not None:
        end = next((s for s, _t in marks if s > start), len(doc.raw))
        for m in NEXT_ITEM_RE.finditer(text[start:end]):
            spots.append((start + m.start(1), m.group(1),
                          f"пункт блока «{NEXT_BLOCK}»"))

    for m in THEME_REF_RE.finditer(text):
        before = (m.group(1) or "").lower()
        ident = m.group(2)
        if before in SELF_REF or not ID_SHAPE_RE.match(ident):
            continue
        spots.append((m.start(2), ident, "ссылка на тему в прозе"))

    out = []
    seen = set()
    for off, ident, where in sorted(spots):
        if (off, ident) in seen:
            continue
        seen.add((off, ident))
        if ident in ids:
            continue
        line, col = doc.pos(off)
        out.append(Finding(
            path, line, col, "S-LINK-TOPIC", ERROR,
            f"{where} указывает на `{ident}`, а темы с таким `id` нет. "
            "Ненаписанная тема называется номером плана («Тема 1.6.04»), а не "
            "идентификатором: иначе ссылка ведёт в пустоту"))
    return out


def check_md_links(path, doc, ids) -> list[Finding]:
    """markdown-ссылки: внутренняя цель — существующий файл и существующий анкорь.

    В сегодняшнем корпусе markdown-ссылок нет ни одной: перекрёстные ссылки
    стоят идентификатором в обратных кавычках, внешние — автоссылкой в блоке 14.
    Правило заведено потому, что 9.4 относит битую внутреннюю ссылку и битый
    анкорь к блокирующим, а молчащее правило проверяется фикстурой, а не
    надеждой.
    """
    text = linkable(doc)
    out = []
    for m in MD_LINK_RE.finditer(text):
        target = m.group("target")
        line, col = doc.pos(m.start())
        if not target:
            out.append(Finding(path, line, col, "S-LINK-MD", ERROR,
                               "markdown-ссылка с пустой целью"))
            continue
        if re.match(r"^[a-z][a-z0-9+.\-]*:", target) or target.startswith("//"):
            continue  # внешний адрес: им занимается S-EXT-IN-BODY
        file_part, _, anchor = target.partition("#")
        target_doc = doc
        if file_part:
            resolved = (Path(path).parent / file_part).resolve()
            if not resolved.exists():
                as_id = file_part.removesuffix(".md")
                hint = (f". Тема `{as_id}` существует — ссылка на неё ставится "
                        "идентификатором в обратных кавычках, ссылку делает "
                        "сборка") if as_id in ids else ""
                out.append(Finding(path, line, col, "S-LINK-MD", ERROR,
                                   f"ссылка на {file_part}: файла нет{hint}"))
                continue
            target_doc = mdtext.load(resolved)
        if anchor and anchor not in anchors_of(target_doc):
            out.append(Finding(
                path, line, col, "S-LINK-MD", ERROR,
                f"анкоря #{anchor} нет на странице "
                f"{file_part or Path(path).name}: заголовка, который дал бы "
                "такой анкорь, там не стоит"))
    return out


# --- сеть -------------------------------------------------------------------

def probe(url: str, timeout: float, tries: int = 2) -> str:
    """Пустая строка — адрес открылся; иначе короткое описание отказа.

    Запрос только `GET`, и он читает первые байты ответа. `HEAD` был бы дешевле,
    но врёт: `portswigger.net` отвечает на `HEAD` кодом 404 на страницы, которые
    по `GET` отдаёт с кодом 200, — три ссылки в `tls-and-proxy` были объявлены
    битыми на пустом месте. Читатель ходит по ссылке методом `GET`, значит и
    проверка ходит им же.

    Одна повторная попытка: первое соединение с медленным хостом успевает
    упереться в таймаут, когда рядом идут ещё пять запросов, и «сеть медленная»
    выглядело бы как «ссылка битая».
    """
    last = "неизвестно"
    for attempt in range(tries):
        req = urllib.request.Request(url, method="GET", headers={
            "User-Agent": UA,
            "Accept": "text/html,application/xhtml+xml,application/pdf;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
        })
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                resp.read(2048)
                if 200 <= resp.status < 400:
                    return ""
                return f"код {resp.status}"
        except urllib.error.HTTPError as e:
            return f"код {e.code}"
        except urllib.error.URLError as e:
            last = f"нет соединения: {e.reason}"
        except Exception as e:                       # noqa: BLE001 — печатаем как есть
            last = f"{type(e).__name__}: {e}"
    return last


def probe_curl(url: str, timeout: float) -> str:
    """То же, но чужими руками: пустая строка — открылся, иначе описание отказа.

    Нужно из-за хостов за антибот-щитом. `www.w3.org` отдаёт `urllib` код 403 и
    страницу «Just a moment…», а `curl` с тем же `User-Agent` — 200: различает
    их не адрес и не заголовок, а отпечаток клиента, то есть набор шифров TLS и
    порядок полей HTTP/2. Читатель ходит браузером, чей отпечаток похож на
    curl'овский, поэтому ссылка живая, и объявлять её битой — врать про текст.
    """
    curl = shutil.which("curl")
    if not curl:
        return "curl не найден"
    try:
        done = subprocess.run(
            [curl, "-sS", "-L", "--compressed", "-A", UA,
             "--max-time", str(int(timeout)), "-o", "/dev/null",
             "-w", "%{http_code}", url],
            capture_output=True, text=True, timeout=timeout + 5)
    except subprocess.TimeoutExpired:
        return "curl: таймаут"
    code = (done.stdout or "").strip()
    if code.isdigit() and 200 <= int(code) < 400:
        return ""
    return f"curl: код {code}" if code.isdigit() else "curl: нет ответа"


def check_external(occurrences, timeout: float, workers: int) -> list[Finding]:
    """Один запрос на адрес, сколько бы тем на него ни ссылалось.

    Отказ, похожий на работу антибот-щита (403, 429, 503), перепроверяется
    `curl`: см. `probe_curl`. Второй запрос уходит только на такие адреса, и
    их единицы, так что прогон от этого не удлиняется.
    """
    SHIELD = ("код 403", "код 429", "код 503")
    urls = sorted({url for _p, _l, _c, url in occurrences})
    verdicts: dict[str, str] = {}
    with cf.ThreadPoolExecutor(max_workers=workers) as pool:
        for url, why in zip(urls, pool.map(lambda u: probe(u, timeout), urls)):
            verdicts[url] = why
    shielded = sorted(u for u, why in verdicts.items() if why in SHIELD)
    if shielded:
        with cf.ThreadPoolExecutor(max_workers=workers) as pool:
            for url, why in zip(shielded,
                                pool.map(lambda u: probe_curl(u, timeout), shielded)):
                verdicts[url] = why if why else ""
    out = []
    for path, line, col, url in occurrences:
        why = verdicts.get(url, "")
        if why:
            out.append(Finding(path, line, col, "S-LINK-EXT", WARNING,
                               f"{url} не открылся — {why}"))
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--external", action="store_true",
                    help="проверять внешние адреса: один запрос на адрес, сеть")
    ap.add_argument("--timeout", type=float, default=25.0,
                    help="таймаут одного запроса, секунды (по умолчанию 25)")
    ap.add_argument("--workers", type=int, default=6,
                    help="сколько адресов проверять одновременно")
    ap.add_argument("--summary", action="store_true",
                    help="печатать сводку по правилам вместо списка замечаний")
    ap.add_argument("--json", action="store_true",
                    help="по одному объекту JSON на замечание, с уровнем: "
                         "этим форматом замечания читает tools/check.py")
    ap.add_argument("paths", nargs="*", help="файлы; по умолчанию content/**/*.md")
    args = ap.parse_args()

    paths = [Path(p) for p in args.paths] or mdtext.topics()
    ids = load_ids(paths)
    source_urls = load_source_urls()

    findings: list[Finding] = []
    occurrences: list[tuple[str, int, int, str]] = []
    for path in paths:
        doc = mdtext.load(path)
        marks = blocks_of(doc)
        findings += check_external_placement(path, doc, marks)
        findings += check_source_urls(path, doc, marks, source_urls)
        findings += check_topic_refs(path, doc, marks, ids)
        findings += check_md_links(path, doc, ids)
        for off, url, _auto in external_links(doc):
            line, col = doc.pos(off)
            occurrences.append((str(path), line, col, url))
    if args.external:
        findings += check_external(occurrences, args.timeout, args.workers)
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
            print(f"{rule:<18} {level:<8} {n}")
    else:
        for f in findings:
            print(f)

    errors = sum(1 for f in findings if f.level == ERROR)
    if not args.json:
        checked = len({u for _p, _l, _c, u in occurrences})
        tail = f", внешних адресов {checked}" if args.external else ""
        print(f"\nlinkcheck: {errors} error, {len(findings) - errors} warning "
              f"({len(paths)} файлов{tail})", file=sys.stderr)
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
