#!/usr/bin/env python3
"""Шесть правил по описаниям конвейера. Ни сети, ни установки.

Правила написаны под эту лабу и повторяют то, что в работе делят между собой
`actionlint` и свои правила Semgrep. Каждое правило — одна проверка одного
признака; регулярное выражение здесь ровно потому, что предмет проверки —
текст описания, а не программа.

    python3 lint.py                 # обе системы
    python3 lint.py .gitlab-ci.yml  # один файл

Код возврата: 0 — замечаний нет, 1 — есть.
"""
import pathlib
import re
import sys

HERE = pathlib.Path(__file__).parent
FILES = [".github/workflows/pr-greeter.yml", ".gitlab-ci.yml"]

RULES = [
    ("CI-3 права токена сборки шире необходимого",
     r"permissions:\s*write-all",
     "`write-all` отдаёт токену запись во всё. Поставьте `contents: read` "
     "на весь workflow и повышайте права точечно."),

    ("CI-4 сборка чужого кода с правами основной ветки",
     r"(?s)pull_request_target.{0,800}?github\.event\.pull_request\.head\.sha",
     "`pull_request_target` идёт с секретами и правами основной ветки, "
     "а checkout по head.sha берёт код чужого запроса."),

    ("CI-5 сторонний шаг по подвижной ссылке",
     r"uses:\s*(?!actions/)[\w.-]+/[\w.-]+@(?!\b[0-9a-f]{40}\b)\S+",
     "Ветку и тег владелец действия переписывает в любой момент. "
     "Прикрепляйте сторонний шаг к сумме коммита."),

    ("CI-6 секрет записан в описание конвейера",
     r"^\s*[A-Z_]*(TOKEN|SECRET|KEY|PASSWORD)[A-Z_]*:\s*[\"']?\S{8,}",
     "Значение секрета лежит в файле, который читает каждый, у кого есть "
     "доступ к репозиторию. Секрет приходит из хранилища форжа."),
]


SCRIPT_RULES = [
    ("CI-1 подстановка чужого значения в команду шага",
     r"\$\{\{\s*github\.event\.[^}]*(title|body|head_ref|label|name)[^}]*\}\}",
     "Значение из запроса подставляется в текст скрипта до оболочки. "
     "Вынесите его в переменную окружения шага и обращайтесь как к переменной."),

    ("CI-2 повторный разбор строки с чужим значением",
     r"\beval\b[^\n]*\$\{?CI_[A-Z_]*(TITLE|DESCRIPTION|SOURCE_BRANCH)",
     "`eval` разбирает строку второй раз, и подстановка из окружения "
     "становится кодом. Уберите второй разбор."),
]


def script_body(text):
    """Строки, попадающие в команду шага. Правила CI-1 и CI-2 спрашиваются
    только с них: то же выражение в блоке `env:` — законная запись значения в
    переменную, а не подстановка в текст скрипта."""
    out, inside, level = [], False, 0
    for num, raw in enumerate(text.splitlines(), 1):
        st = raw.strip()
        if not st:
            continue
        indent = len(raw) - len(raw.lstrip())
        if inside and indent <= level:
            inside = False
        if st in ("run: |", "script:") or st.startswith("run: |"):
            inside, level = True, indent
            continue
        if st.startswith("- run:") or (st.startswith("run:") and not st.endswith("|")):
            out.append((num, st))
            continue
        if inside:
            out.append((num, st))
    return out


def check(path):
    text = (HERE / path).read_text(encoding="utf-8")
    hits = []
    body = script_body(text)
    for name, pattern, advice in SCRIPT_RULES:
        for num, line in body:
            m = re.search(pattern, line)
            if m:
                hits.append((name, num, m.group(0)[:60], advice))
                break
    for name, pattern, advice in RULES:
        m = re.search(pattern, text, re.M)
        if m:
            line = text[:m.start()].count("\n") + 1
            hits.append((name, line, m.group(0).splitlines()[0][:60], advice))
    return hits


def main(argv):
    files = argv[1:] or FILES
    total = 0
    for path in files:
        hits = check(path)
        print("== %s: замечаний %d" % (path, len(hits)))
        for name, line, frag, advice in hits:
            print("   строка %-3d %s" % (line, name))
            print("             %s" % frag)
            print("             %s" % advice)
        total += len(hits)
    print("\nвсего замечаний: %d" % total)
    return 1 if total else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
