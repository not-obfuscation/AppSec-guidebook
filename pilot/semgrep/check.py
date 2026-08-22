"""Сверка правила с разметкой тест-кейсов.

Штатный `semgrep --test` в версии 1.174.0 падает с IndexError на этой
раскладке каталогов, поэтому сверка сделана отдельно: разбирается
JSON-вывод обычного прогона и сравнивается с комментариями
`# ruleid:` и `# ok:` в файле тест-кейсов.

Запуск:
    .venv-tools/bin/python pilot/semgrep/check.py
"""

import json
import pathlib
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
RULE = ROOT / "pilot/semgrep/password-fast-digest.yaml"
CASES = ROOT / "pilot/semgrep/password-fast-digest.py"
SEMGREP = ROOT / ".venv-tools/bin/semgrep"


def expected(path: pathlib.Path) -> tuple[set[int], set[int]]:
    """Строки, где находка ожидается, и где она запрещена."""
    hits, clean = set(), set()
    for number, line in enumerate(path.read_text().splitlines(), start=1):
        text = line.strip()
        if text.startswith("# ruleid:"):
            hits.add(number + 1)
        elif text.startswith("# ok:"):
            clean.add(number + 1)
    return hits, clean


def scan(rule: pathlib.Path, target: pathlib.Path) -> set[int]:
    result = subprocess.run(
        [str(SEMGREP), "--metrics=off", "--disable-version-check",
         "--quiet", "--json", "--config", str(rule), str(target)],
        capture_output=True, text=True, check=True)
    payload = json.loads(result.stdout)
    return {item["start"]["line"] for item in payload["results"]}


def main() -> int:
    hits, clean = expected(CASES)
    found = scan(RULE, CASES)
    missed = sorted(hits - found)
    noise = sorted(found & clean)
    stray = sorted(found - hits - clean)
    print(f"ожидалось находок: {len(hits)}, найдено: {len(found)}")
    print(f"пропущено (ложноотрицательные): {missed or 'нет'}")
    print(f"на строках # ok (ложноположительные): {noise or 'нет'}")
    print(f"вне разметки: {stray or 'нет'}")

    lab = ROOT / "pilot/lab/password-storage"
    vulnerable = sorted(scan(RULE, lab / "code.py"))
    fixed = sorted(scan(RULE, lab / "solution.py"))
    print(f"лаба, code.py — строки находок: {vulnerable}")
    print(f"лаба, solution.py — строки находок: {fixed} "
          f"(одно подавление # nosemgrep стоит на сверке старого формата)")

    ok = not missed and not noise and not stray and vulnerable and not fixed
    print("ПРАВИЛО СВЕРЕНО" if ok else "ПРАВИЛО РАСХОДИТСЯ С РАЗМЕТКОЙ")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
