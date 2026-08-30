#!/usr/bin/env python3
"""Одна команда, один вердикт: обёртка над всеми проверками гайдбука.

    python tools/check.py                        # всё, по всему content/**
    python tools/check.py content/stage-1/*.md   # только эти темы
    python tools/check.py --only vale --warnings
    python tools/check.py --list

Внутри три вида проверок, и они дают разное.

  реестр  — команда либо зелёная, либо нет: `validate.py` (реестр источников и
            покрытие тем), `gen_topics.py --check` и `gen_glossary.py --check`
            (сгенерированное не разошлось с рукописным источником);
  линтеры — Vale, markdownlint, `glossary_lint.py`, `lint_style.py`: замечание
            с адресом, правилом и уровнем;
  отчёты  — `wordcount.py` и `stoplist.py`: цифры без вердикта. Стоп-лист
            связок смотрится глазами, а таблица объёма нужна целиком —
            вердиктная метрика рядом со справочными. Такие проверки
            печатаются и ничего не роняют.

`wordcount.py` стоит в двух местах: линтером `volume` он даёт вердикт по норме
3.1 (`--json`, правила `C-VOL-*`), отчётом `wordcount` — ту же таблицу со
справочными метриками `проза` и `тело`. Норма и метод подсчёта заданы сводом
(3.1, решение оператора от 2026-08-23), поэтому порог здесь не выдуман.

Уровни — STYLE.md § 1.1: error роняет проверку, warning печатается. Правила
из § 9 не проверяются машиной вовсе и здесь не появляются.

Исключения из `tools/exceptions.yaml` применяются ко всем линтерам
единообразно (STYLE.md § 1.4): снятое печатается отдельным разделом и
считается — молча спрятанное исключение через полгода неотличимо от
отсутствующей проверки.

Выход 1, если есть ошибка, не снятая исключением; если упала проверка реестра;
если инструмент не найден. Пропущенная проверка снаружи неотличима от
пройденной, поэтому отсутствие инструмента — тоже красный вердикт, а не
молчаливый пропуск.
"""

import argparse
import json
import re
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path

from paths import EXCEPTIONS_YAML, ROOT, TOOLS_DIR

PY = sys.executable
VALE = TOOLS_DIR / "bin" / "vale"
VALE_INI = str(TOOLS_DIR / "vale" / ".vale.ini")
MDL = TOOLS_DIR / "node" / "node_modules" / ".bin" / "markdownlint-cli2"
MDL_CFG = str(TOOLS_DIR / "markdownlint.jsonc")
EXCEPTIONS = EXCEPTIONS_YAML

# Совпадает с `tools/plan_parse.py`. Проверка, которой нечего было
# проверять, помечает свой вывод этим словом, и тогда её «ok» видно
# отдельно — и в списке реестра, и в итоговой строке.
SKIP_MARK = "ПРОПУЩЕНО"

SETUP_HINT = "нет инструмента — `make setup` (tools/setup.sh)"


@dataclass
class Finding:
    """Замечание одного линтера, приведённое к общему виду."""

    path: str
    line: int
    col: int
    rule: str  # канонический идентификатор STYLE.md: L-*, MD*, S-*, G-*
    native: str  # как правило называет себя сам: AppSec.Banned, MD009/no-...
    level: str  # error | warning
    message: str
    fragment: str  # то, на что правило показало: против него сверяется match
    tool: str
    excused: str = ""  # причина из exceptions.yaml, если срабатывание снято

    @property
    def where(self) -> str:
        return f"{self.line}:{self.col}" if self.col else str(self.line)


@dataclass
class Result:
    """Итог одной проверки."""

    name: str
    kind: str  # registry | lint | report
    ok: bool
    findings: list = field(default_factory=list)
    output: str = ""
    note: str = ""


# ── запуск ────────────────────────────────────────────────────────────────────


def run(argv: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(
        argv, cwd=ROOT, capture_output=True, text=True, encoding="utf-8"
    )


def content_files() -> list[str]:
    return sorted(
        str(p.relative_to(ROOT)) for p in ROOT.glob("content/*/*.md")
    )


def rel(path: str) -> str:
    """Путь от корня репозитория, каким его печатает вся остальная обвязка."""
    p = Path(path)
    if not p.is_absolute():
        p = (ROOT / p).resolve()
    try:
        return str(p.relative_to(ROOT))
    except ValueError:
        return str(p)


# ── линтеры ───────────────────────────────────────────────────────────────────


def vale(paths: list[str]) -> Result:
    if not VALE.exists():
        return Result("vale", "lint", False, note=f"{VALE} — {SETUP_HINT}")
    proc = run([str(VALE), "--config", VALE_INI, "--output=JSON", *paths])
    if not proc.stdout.strip():
        return Result("vale", "lint", False, note=proc.stderr.strip() or "пустой вывод")
    try:
        data = json.loads(proc.stdout)
    except json.JSONDecodeError as exc:
        return Result("vale", "lint", False, note=f"вывод не JSON: {exc}")
    out = []
    for path, items in data.items():
        for i in items:
            link = i.get("Link") or ""
            canon = link.rsplit("#", 1)[-1] if "#" in link else i["Check"]
            level = "warning" if i["Severity"] == "suggestion" else i["Severity"]
            out.append(
                Finding(
                    path=rel(path),
                    line=i["Line"],
                    col=(i.get("Span") or [0])[0],
                    rule=canon,
                    native=i["Check"],
                    level=level,
                    message=i["Message"],
                    fragment=i.get("Match", ""),
                    tool="vale",
                )
            )
    return Result("vale", "lint", True, out)


MDL_RE = re.compile(
    r"\A(?P<path>.+?):(?P<line>\d+)(?::(?P<col>\d+))?\s+"
    r"(?P<level>\w+)\s+(?P<rule>MD\d+)(?P<alias>\S*)\s+(?P<msg>.*)\Z"
)
MDL_CTX_RE = re.compile(r"\[Context: \"(?P<ctx>.*)\"\]\s*\Z")


def markdownlint(paths: list[str]) -> Result:
    """markdownlint-cli2 берёт список файлов из своего конфига.

    Пути в командной строке он к этому списку добавляет, а не заменяет им.
    Поэтому пути передаются (иначе фикстуры селф-теста, лежащие вне `content`,
    остались бы непроверенными), а лишнее отбирается по путям уже из результата.
    """
    if not MDL.exists():
        return Result("markdownlint", "lint", False, note=f"{MDL} — {SETUP_HINT}")
    proc = run([str(MDL), "--config", MDL_CFG, *paths])
    lines = (proc.stdout + proc.stderr).splitlines()
    out, unparsed = [], []
    for line in lines:
        line = line.rstrip()
        if not line or line.startswith(("markdownlint-cli2 ", "Finding: ", "Linting: ", "Summary: ")):
            continue
        m = MDL_RE.match(line)
        if not m:
            unparsed.append(line)
            continue
        msg = m["msg"]
        ctx = MDL_CTX_RE.search(msg)
        out.append(
            Finding(
                path=rel(m["path"]),
                line=int(m["line"]),
                col=int(m["col"] or 0),
                rule=m["rule"],
                native=m["rule"] + m["alias"],
                level="error" if m["level"] == "error" else "warning",
                message=msg,
                fragment=ctx["ctx"] if ctx else msg,
                tool="markdownlint",
            )
        )
    keep = set(paths)
    out = [f for f in out if f.path in keep]
    note = ""
    if unparsed:
        note = "нераспознанные строки вывода: " + " / ".join(unparsed[:3])
    return Result("markdownlint", "lint", not unparsed, out, note=note)


def own(name: str, script: str, paths: list[str], whole: bool = False,
        extra: list[str] | None = None) -> Result:
    """Свой линтер: формат `--json`, по объекту на замечание.

    `whole` — линтеру нельзя дать подмножество тем: `glossary_lint.py` отвечает
    на вопросы «термин не употреблён нигде» и «первое употребление на сайте», и
    от одной темы ответ будет неверным. Такой линтер всегда работает по всему
    набору, а обёртка отбирает из результата нужные пути — но оставляет
    замечания к `glossary.yaml`: они не про тему, а про сам глоссарий.
    """
    proc = run([PY, f"tools/{script}", "--json", *(extra or []),
                *([] if whole else paths)])
    out = []
    for line in proc.stdout.splitlines():
        if not line.strip():
            continue
        try:
            d = json.loads(line)
        except json.JSONDecodeError:
            return Result(name, "lint", False, note=f"вывод не JSON: {line[:80]}")
        out.append(
            Finding(
                path=rel(d["path"]),
                line=d["line"],
                col=d.get("col", 0),
                rule=d["rule"],
                native=d["rule"],
                level=d["level"],
                message=d["message"],
                fragment=d["message"],
                tool=name,
            )
        )
    if whole:
        keep = set(paths)
        out = [f for f in out if f.path in keep or not f.path.startswith("content/")]
    ok = proc.returncode in (0, 1) and not proc.stderr.strip()
    return Result(name, "lint", ok, out, note=proc.stderr.strip()[:400])


# ── реестр и отчёты ───────────────────────────────────────────────────────────


def command(name: str, kind: str, argv: list[str]) -> Result:
    proc = run(argv)
    text = (proc.stdout + proc.stderr).rstrip()
    if kind == "report":
        return Result(name, kind, True, output=text)
    return Result(name, kind, proc.returncode == 0, output=text)


# ── исключения ────────────────────────────────────────────────────────────────


def load_exceptions() -> list[dict]:
    if not EXCEPTIONS.exists():
        return []
    import yaml

    data = yaml.safe_load(EXCEPTIONS.read_text(encoding="utf-8")) or []
    for i, e in enumerate(data, 1):
        missing = [k for k in ("rule", "file", "match", "reason", "added") if not e.get(k)]
        if missing:
            sys.stderr.write(
                f"{EXCEPTIONS.name}: запись {i} без полей {', '.join(missing)} "
                "— STYLE.md § 1.4 требует все четыре условия\n"
            )
            sys.exit(2)
        e["hits"] = 0
    return data


def apply_exceptions(findings: list[Finding], excs: list[dict]) -> None:
    for f in findings:
        for e in excs:
            if e["file"] != f.path:
                continue
            if e["rule"] not in (f.rule, f.native):
                continue
            if e["match"] not in f.fragment:
                continue
            f.excused = " ".join(str(e["reason"]).split())
            e["hits"] += 1
            break


# ── печать ────────────────────────────────────────────────────────────────────


def plural(n: int, one: str, few: str, many: str) -> str:
    """Согласование числа: «1 тема», «2 темы», «12 тем»."""
    if n % 10 == 1 and n % 100 != 11:
        return f"{n} {one}"
    if n % 10 in (2, 3, 4) and n % 100 not in (12, 13, 14):
        return f"{n} {few}"
    return f"{n} {many}"


def wrap(text: str, width: int, indent: str) -> list[str]:
    words, lines, cur = text.split(), [], ""
    for w in words:
        if cur and len(cur) + 1 + len(w) > width:
            lines.append(cur)
            cur = w
        else:
            cur = f"{cur} {w}".strip()
    if cur:
        lines.append(cur)
    return [indent + l for l in lines]


def print_findings(findings: list[Finding], limit: int | None) -> None:
    by_path: dict[str, list[Finding]] = {}
    for f in findings:
        by_path.setdefault(f.path, []).append(f)
    for path in sorted(by_path):
        group = sorted(by_path[path], key=lambda f: (f.line, f.col, f.rule))
        shown = group if limit is None else group[:limit]
        print(f"  {path}")
        for f in shown:
            print(f"    {f.where:>7}  {f.rule:<14} {f.message}")
        if len(group) > len(shown):
            print(f"    … ещё {len(group) - len(shown)} — `--full`")


def print_by_rule(findings: list[Finding], examples: int) -> None:
    by_rule: dict[str, list[Finding]] = {}
    for f in findings:
        by_rule.setdefault(f.rule, []).append(f)
    for rule in sorted(by_rule, key=lambda r: (-len(by_rule[r]), r)):
        group = sorted(by_rule[rule], key=lambda f: (f.path, f.line))
        print(f"  {rule}  ×{len(group)}")
        for f in group[:examples]:
            print(f"    {f.path}:{f.where}  {f.message}")
        if len(group) > examples:
            print(f"    … ещё {len(group) - examples} — `--full`")


# ── сборка ────────────────────────────────────────────────────────────────────

REGISTRY = [
    ("validate", ["tools/validate.py", "--quiet"]),
    ("topics", ["tools/gen_topics.py", "--check"]),
    ("glossary-gen", ["tools/gen_glossary.py", "--check"]),
]
REPORTS = [
    ("wordcount", ["tools/wordcount.py"]),
    ("stoplist", ["tools/stoplist.py"]),
]
LINTERS = ["vale", "markdownlint", "glossary", "style", "model", "links", "volume"]
# Кто чьи правила печатает. Нужно ровно для одного: не объявлять исключение
# мёртвым, когда его линтер в этом прогоне не запускался. Префикса тут не
# хватает: `S-` делят между собой `lint_style.py` и `linkcheck.py`, поэтому
# правила ссылок перечислены поимённо, а остальное разбирается по началу имени.
LINK_RULES = {"S-EXT-IN-BODY", "S-LINK-BARE", "S-LINK-TOPIC", "S-LINK-MD",
              "S-LINK-SOURCE-URL", "S-LINK-EXT"}
RULE_PREFIX = [("C-VOL-", "volume"), ("C-", "model"), ("G-", "glossary"),
               ("L-", "vale"), ("AppSec.", "vale"), ("MD", "markdownlint"),
               ("S-", "style")]


def owner(rule: str) -> str | None:
    """Линтер, печатающий это правило, или None, если правило незнакомое."""
    if rule in LINK_RULES:
        return "links"
    for prefix, name in RULE_PREFIX:
        if rule.startswith(prefix):
            return name
    return None
ALL = [n for n, _ in REGISTRY] + LINTERS + [n for n, _ in REPORTS]


def main() -> int:
    ap = argparse.ArgumentParser(
        description="все проверки гайдбука одной командой",
        epilog="имена проверок: " + ", ".join(ALL),
    )
    ap.add_argument("paths", nargs="*", help="темы; по умолчанию весь content/**")
    ap.add_argument("--only", action="append", default=[],
                    help="запустить только эти проверки (можно через запятую и повторять)")
    ap.add_argument("--full", action="store_true",
                    help="печатать предупреждения целиком, а не по три примера на правило")
    ap.add_argument("--quiet", action="store_true",
                    help="только сводка, ошибки и вердикт: без отчётов и предупреждений")
    ap.add_argument("--external", action="store_true",
                    help="в линтере links проверять и внешние адреса: это сеть, "
                         "и по умолчанию проверка её не касается — красный "
                         "вердикт должен означать «текст сломан», а не «сети нет»")
    ap.add_argument("--no-exceptions", action="store_true",
                    help="не применять tools/exceptions.yaml — видно, что именно оно снимает")
    ap.add_argument("--json", action="store_true",
                    help="все замечания машинным форматом, с полем excused")
    ap.add_argument("--list", action="store_true", help="перечислить проверки и выйти")
    args = ap.parse_args()

    if args.list:
        for name, argv in REGISTRY:
            print(f"  реестр   {name:<14} {' '.join(argv)}")
        for name in LINTERS:
            print(f"  линтер   {name}")
        for name, argv in REPORTS:
            print(f"  отчёт    {name:<14} {' '.join(argv)}")
        return 0

    wanted = {n.strip() for spec in args.only for n in spec.split(",") if n.strip()}
    unknown = wanted - set(ALL)
    if unknown:
        sys.stderr.write(f"неизвестная проверка: {', '.join(sorted(unknown))}\n")
        return 2
    picked = (lambda n: not wanted or n in wanted)

    paths = [rel(p) for p in args.paths] or content_files()
    missing = [p for p in paths if not (ROOT / p).exists()]
    if missing:
        sys.stderr.write("нет файла: " + ", ".join(missing) + "\n")
        return 2

    results: list[Result] = []
    for name, argv in REGISTRY:
        if picked(name):
            results.append(command(name, "registry", [PY, *argv]))
    if picked("vale"):
        results.append(vale(paths))
    if picked("markdownlint"):
        results.append(markdownlint(paths))
    if picked("glossary"):
        results.append(own("glossary", "glossary_lint.py", paths, whole=True))
    if picked("style"):
        results.append(own("style", "lint_style.py", paths))
    # Контентная модель смотрит на корпус целиком: цикл в графе предпосылок и
    # занятый `order` — свойства набора тем, а не одной страницы. Поэтому
    # whole=True, и отбор по путям делает уже сам `own`.
    if picked("model"):
        results.append(own("model", "validate_content.py", paths, whole=True))
    # Ссылки: `id` разрешается по всему корпусу, поэтому whole=True — иначе на
    # одной теме законная ссылка на соседнюю окажется битой.
    if picked("links"):
        results.append(own("links", "linkcheck.py", paths, whole=True,
                           extra=["--external"] if args.external else None))
    # Объём: вердикт по норме 3.1 отдельно от таблицы. Таблица нужна целиком и
    # печатается отчётом `wordcount`; здесь из того же скрипта берутся только
    # замечания `C-VOL-*`, чтобы они попали под исключения и в общий счёт.
    if picked("volume"):
        results.append(own("volume", "wordcount.py", paths))
    for name, argv in REPORTS:
        if picked(name):
            results.append(command(name, "report", [PY, *argv, *paths]))

    findings = [f for r in results for f in r.findings]
    excs = [] if args.no_exceptions else load_exceptions()
    apply_exceptions(findings, excs)

    if args.json:
        for f in sorted(findings, key=lambda f: (f.path, f.line, f.col, f.rule)):
            print(json.dumps(f.__dict__, ensure_ascii=False))

    errors = [f for f in findings if f.level == "error" and not f.excused]
    warnings = [f for f in findings if f.level == "warning" and not f.excused]
    excused = [f for f in findings if f.excused]
    broken = [r for r in results if not r.ok and r.kind == "lint"]
    red_registry = [r for r in results if not r.ok and r.kind == "registry"]

    if args.json:
        return 1 if errors or broken or red_registry else 0

    print("проверки гайдбука — "
          f"{plural(len(paths), 'тема', 'темы', 'тем')}, "
          f"{plural(len(results), 'проверка', 'проверки', 'проверок')}\n")

    reg = [r for r in results if r.kind == "registry"]
    if reg:
        print("реестр")
        for r in reg:
            # Проверка может пройти, потому что ей нечего было проверять.
            # Такое «ok» обязано выглядеть иначе, чем полноценное: иначе
            # выключенная проверка неотличима от выполненной.
            skipped = [ln for ln in r.output.splitlines() if SKIP_MARK in ln]
            mark = ("ok" if not skipped else "ok, но не вся") if r.ok else "НЕ ПРОШЛА"
            print(f"  {r.name:<14} {mark}")
            for line in skipped:
                print(f"      {line.strip()}")
            if not r.ok and r.output:
                for line in r.output.splitlines()[:20]:
                    print(f"      {line}")
        print()

    lints = [r for r in results if r.kind == "lint"]
    if lints:
        print(f"  {'линтер':<14}{'ошибок':>8}{'предупр.':>10}{'снято':>8}")
        for r in lints:
            if not r.ok:
                print(f"  {r.name:<14}{'—':>8}{'—':>10}{'—':>8}   {r.note}")
                continue
            e = sum(1 for f in r.findings if f.level == "error" and not f.excused)
            w = sum(1 for f in r.findings if f.level == "warning" and not f.excused)
            x = sum(1 for f in r.findings if f.excused)
            print(f"  {r.name:<14}{e:>8}{w:>10}{x:>8}")
        print()

    if errors:
        print(f"ошибки ({len(errors)}) — роняют проверку")
        print_findings(errors, None)
        print()

    if warnings and not args.quiet:
        print(f"предупреждения ({len(warnings)}) — печатаются, проверку не роняют")
        if args.full:
            print_findings(warnings, None)
        else:
            print_by_rule(warnings, 3)
        print()

    if excused:
        print(f"снято исключениями ({len(excused)}) — tools/exceptions.yaml")
        groups: dict[str, list[Finding]] = {}
        for f in excused:
            groups.setdefault(f.excused, []).append(f)
        for reason, group in groups.items():
            for f in sorted(group, key=lambda f: (f.path, f.line)):
                frag = " ".join(f.fragment.split())
                print(f"  {f.path}:{f.where}  {f.rule}  «{frag}»")
            print("\n".join(wrap(reason, 72, "      ")))
        print()
    # Когда линтер не отработал, про его исключения ничего не известно:
    # молчание правила и отсутствие правила снаружи выглядят одинаково. То же
    # с линтером, который не запускали: `make links` ничего не знает про
    # исключения Vale, а `make check` — про `S-LINK-EXT`, потому что внешние
    # адреса проверяются только с `--external`. Молча пропустить такую запись
    # правильнее, чем звать её мёртвой: обвинение на пустом месте учит автора
    # не верить выводу.
    ran = {r.name for r in results if r.kind == "lint" and r.ok}
    def alive_here(e: dict) -> bool:
        who = owner(e["rule"])
        if who is None:                 # незнакомое правило — сказать всё равно
            return True
        if who not in ran:
            return False
        return args.external if e["rule"] == "S-LINK-EXT" else True
    stale = [] if broken else [e for e in excs
                               if not e["hits"] and alive_here(e)]
    if stale:
        print(f"исключения без срабатываний ({len(stale)}) — правило или текст изменились")
        for e in stale:
            print(f"  {e['file']}  {e['rule']}  «{e['match']}»  от {e['added']}")
        print()

    reports = [r for r in results if r.kind == "report"]
    if reports and not args.quiet:
        for r in reports:
            print(f"отчёт {r.name} — без вердикта")
            for line in r.output.splitlines():
                print(f"  {line}")
            print()

    for r in broken:
        print(f"линтер {r.name} не отработал: {r.note}")

    skipped_reg = [r for r in results
                   if r.kind == "registry" and r.ok and SKIP_MARK in r.output]

    bad = bool(errors or broken or red_registry)
    parts = [plural(len(errors), "ошибка", "ошибки", "ошибок"),
             plural(len(warnings), "предупреждение", "предупреждения", "предупреждений")]
    if excused:
        parts.append(f"{len(excused)} снято исключениями")
    if red_registry:
        parts.append("реестр не сошёлся")
    if broken:
        parts.append(plural(len(broken), "линтер не отработал",
                            "линтера не отработали", "линтеров не отработали"))
    if skipped_reg:
        parts.append(plural(len(skipped_reg), "проверка пропущена",
                            "проверки пропущены", "проверок пропущено"))
    print("ИТОГ: " + ", ".join(parts) + (" — не пройдено" if bad else " — пройдено"))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
