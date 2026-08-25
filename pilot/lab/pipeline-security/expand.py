#!/usr/bin/env python3
"""Как значение из чужого запроса попадает в команду шага. Две системы, два пути.

**GitHub Actions.** Выражение `${{ … }}` подставляется в текст скрипта до того,
как скрипт увидит оболочка. В оболочку едет уже склеенная строка, и всё, что в
подставленном значении похоже на синтаксис оболочки, оболочка разберёт как
синтаксис. Это подстановка в текст.

**GitLab CI.** Предопределённые переменные раннер кладёт в окружение job.
`echo "$CI_MERGE_REQUEST_TITLE"` подставляет значение уже внутри оболочки, и
`$(…)` в значении не выполняется. Пока строку не разбирают второй раз — `eval`,
`sh -c`, кавычки, снятые руками, — инъекции нет. Это разница в устройстве, а не
в аккуратности вендора.

Скрипт воспроизводит обе подстановки. Форж при этом не запускается:
воспроизведён механизм, описанный документацией обеих систем.

    python3 expand.py .github/workflows/pr-greeter.yml 'заголовок'
    python3 expand.py .gitlab-ci.yml 'заголовок'
"""
import os
import pathlib
import re
import subprocess
import sys

GH = r"\$\{\{\s*github\.event\.pull_request\.title\s*\}\}"
GL = "CI_MERGE_REQUEST_TITLE"


def unquote(s):
    if len(s) > 1 and s[0] == s[-1] and s[0] in "'\"":
        return s[1:-1]
    return s


def script_lines(path):
    """Строки скрипта из описания конвейера. Разбор нарочно грубый: предмет
    лабы — подстановка, а не разбор YAML."""
    out, in_block, block_indent = [], False, 0
    for raw in pathlib.Path(path).read_text(encoding="utf-8").splitlines():
        s = raw.strip()
        if not s or s.startswith("#"):
            continue
        indent = len(raw) - len(raw.lstrip())
        if in_block:
            if indent > block_indent:
                out.append(unquote(s[2:].strip()) if s.startswith("- ") else s)
                continue
            in_block = False
        if s in ("run: |", "script:"):
            in_block, block_indent = True, indent
        elif s.startswith("- run:"):
            out.append(unquote(s[6:].strip()))
        elif s.startswith("run:") and not s.endswith("|"):
            out.append(unquote(s[4:].strip()))
    return out


def main(argv):
    path = argv[1]
    title = argv[2] if len(argv) > 2 else "обычный заголовок"
    github = ".github" in path
    hit = False
    for line in script_lines(path):
        uses_title = bool(re.search(GH, line)) if github else (GL in line)
        if not uses_title:
            continue
        hit = True
        print("описано:    %s" % line)
        if github:
            cooked = re.sub(GH, title, line)
            env = dict(os.environ)
            print("в оболочку: %s" % cooked)
        else:
            cooked = line
            env = dict(os.environ, CI_MERGE_REQUEST_TITLE=title)
            print("в оболочку: %s   (переменная в окружении)" % cooked)
        p = subprocess.run(["bash", "-c", cooked], capture_output=True,
                           text=True, env=env)
        for out in (p.stdout + p.stderr).strip().splitlines():
            print("вывод:      %s" % out)
        print()
    if not hit:
        print("значения из запроса в командах шагов нет — подставлять нечего")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
