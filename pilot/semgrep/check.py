"""Сверка правила с разметкой тест-кейсов.

Штатный `semgrep --test` в версии 1.174.0 падает с IndexError на этой
раскладке каталогов, поэтому сверка сделана отдельно: разбирается
JSON-вывод обычного прогона и сравнивается с комментариями
`ruleid:` и `ok:` в файлах тест-кейсов. Маркер стоит строкой выше
ожидаемой находки и называет правило, которое должно сработать.

Запуск:
    .venv-tools/bin/python pilot/semgrep/check.py            # все правила
    .venv-tools/bin/python pilot/semgrep/check.py postmessage
"""

import json
import pathlib
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
SEMGREP = ROOT / ".venv-tools/bin/semgrep"

# Правило, его тест-кейсы и лаба, на которой оно должно ловить уязвимый файл
# и молчать на исправленном. Ключ — короткое имя для аргумента запуска.
SUITES = {
    "password": {
        "rule": "pilot/semgrep/password-fast-digest.yaml",
        "cases": ["pilot/semgrep/password-fast-digest.py"],
        "vulnerable": "pilot/lab/password-storage/code.py",
        "fixed": "pilot/lab/password-storage/solution.py",
        "note": "одно подавление # nosemgrep стоит на сверке старого формата",
    },
    "admin-route": {
        "rule": "pilot/semgrep/admin-route-no-authz.yaml",
        "cases": ["pilot/semgrep/admin-route-no-authz.py"],
        "vulnerable": "pilot/lab/privilege-escalation-vertical/code.py",
        "fixed": "pilot/lab/privilege-escalation-vertical/solution.py",
        "note": "право объявлено у маршрута аргументом role=",
    },
    "object-lookup": {
        "rule": "pilot/semgrep/object-lookup-unscoped.yaml",
        "cases": ["pilot/semgrep/object-lookup-unscoped.py"],
        "vulnerable": "pilot/lab/idor/code.py",
        "fixed": "pilot/lab/idor/solution.py",
        "note": "выборка ограничена владельцем, получатель вызова — не таблица",
    },
    "outbound-url": {
        "rule": "pilot/semgrep/outbound-url-unvalidated.yaml",
        "cases": ["pilot/semgrep/outbound-url-unvalidated.py"],
        "vulnerable": "pilot/lab/ssrf-basics/code.py",
        "fixed": "pilot/lab/ssrf-basics/solution.py",
        "note": "адрес собран приложением после сверки со списком",
    },
    "sql-query": {
        "rule": "pilot/semgrep/sql-query-string-built.yaml",
        "cases": ["pilot/semgrep/sql-query-string-built.py"],
        "vulnerable": "pilot/lab/sqli-basics/code.py",
        "fixed": "pilot/lab/sqli-basics/solution.py",
        "note": "текст запроса постоянный, данные — связанными параметрами",
    },
    "postmessage": {
        "rule": "pilot/semgrep/postmessage-no-origin-check.yaml",
        "cases": ["pilot/semgrep/postmessage-no-origin-check.js",
                  "pilot/semgrep/postmessage-no-origin-check.ts"],
        "vulnerable": "pilot/lab/same-origin-policy/code.js",
        "fixed": "pilot/lab/same-origin-policy/solution.js",
        "note": "второй стек — TypeScript, идиома React",
    },
}

MARKS = ("ruleid:", "ok:")


def expected(path: pathlib.Path) -> tuple[set, set]:
    """Пары (строка, правило): где находка ожидается и где запрещена."""
    hits, clean = set(), set()
    for number, line in enumerate(path.read_text().splitlines(), start=1):
        text = line.strip().lstrip("/#").strip()
        for mark, target in ((MARKS[0], hits), (MARKS[1], clean)):
            if text.startswith(mark):
                rule = text[len(mark):].strip()
                if rule:
                    target.add((number + 1, rule))
    return hits, clean


def scan(rule: pathlib.Path, target: pathlib.Path) -> set:
    result = subprocess.run(
        [str(SEMGREP), "--metrics=off", "--disable-version-check",
         "--quiet", "--json", "--config", str(rule), str(target)],
        capture_output=True, text=True, check=True)
    payload = json.loads(result.stdout)
    if payload.get("errors"):
        for item in payload["errors"]:
            print(f"  ОШИБКА semgrep: {item.get('message', item)}")
    return {(item["start"]["line"], item["check_id"].split(".")[-1])
            for item in payload["results"]}


def run(name: str, suite: dict) -> bool:
    rule = ROOT / suite["rule"]
    print(f"=== {name}: {suite['rule']}")
    ok = True
    for case in suite["cases"]:
        path = ROOT / case
        hits, clean = expected(path)
        found = scan(rule, path)
        missed = sorted(hits - found)
        noise = sorted(found & clean)
        stray = sorted(found - hits - clean)
        print(f"  {path.name}: ожидалось {len(hits)}, найдено {len(found)}")
        print(f"    пропущено (ложноотрицательные): {missed or 'нет'}")
        print(f"    на строках ok (ложноположительные): {noise or 'нет'}")
        print(f"    вне разметки: {stray or 'нет'}")
        ok = ok and not missed and not noise and not stray

    vulnerable = sorted(scan(rule, ROOT / suite["vulnerable"]))
    fixed = sorted(scan(rule, ROOT / suite["fixed"]))
    print(f"  лаба, {pathlib.Path(suite['vulnerable']).name} — находки: {vulnerable}")
    print(f"  лаба, {pathlib.Path(suite['fixed']).name} — находки: {fixed}"
          f"  ({suite['note']})")
    ok = ok and bool(vulnerable) and not fixed
    print("  ПРАВИЛО СВЕРЕНО" if ok else "  ПРАВИЛО РАСХОДИТСЯ С РАЗМЕТКОЙ")
    return ok


def main(argv: list[str]) -> int:
    names = argv or list(SUITES)
    unknown = [n for n in names if n not in SUITES]
    if unknown:
        print(f"неизвестное правило: {unknown}; есть {list(SUITES)}")
        return 2
    return 0 if all(run(n, SUITES[n]) for n in names) else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
