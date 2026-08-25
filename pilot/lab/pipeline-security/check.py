#!/usr/bin/env python3
"""Проверялка лабы pipeline-security.

Три проверки, и одной первой мало.

  1. линтер молчит на обоих описаниях;
  2. подстановка заголовка атакующего больше не выполняет команду — проверяется
     прогоном, а не чтением;
  3. конвейер по-прежнему делает свою работу: приветствие печатается, сборка
     запускается, выкладка на месте. Иначе задача решается удалением файла.

Запуск из каталога лабы:
    python3 check.py
Код возврата 0 — зачтено, 1 — нет.
"""
import pathlib
import re
import subprocess
import sys

HERE = pathlib.Path(__file__).parent
GH = ".github/workflows/pr-greeter.yml"
GL = ".gitlab-ci.yml"
PAYLOADS = ['Опечатка"; id; echo "', "Опечатка$(id)", "Опечатка`id`"]


def run(argv):
    p = subprocess.run([sys.executable] + argv, cwd=HERE,
                       capture_output=True, text=True)
    return p.returncode, p.stdout + p.stderr


def main():
    ok = True

    rc, out = run(["lint.py"])
    if rc == 0:
        print("1. линтер: замечаний нет")
    else:
        ok = False
        print("1. линтер: замечания остались")
        print("\n".join("   " + s for s in out.splitlines()[:20]))

    executed = []
    for path in (GH, GL):
        for payload in PAYLOADS:
            _, out = run(["expand.py", path, payload])
            if re.search(r"uid=\d+", out):
                executed.append((path, payload))
    if executed:
        ok = False
        print("2. подстановка: команда всё ещё выполняется")
        for path, payload in executed:
            print("   %s  на заголовке %s" % (path, payload))
    else:
        print("2. подстановка: ни один из трёх заголовков команду не выполнил")

    gh = (HERE / GH).read_text(encoding="utf-8")
    gl = (HERE / GL).read_text(encoding="utf-8")
    missing = []
    if "Спасибо за запрос" not in gh:
        missing.append("приветствие в GitHub Actions")
    if "ci/build.sh" not in gh:
        missing.append("сборка в GitHub Actions")
    if "publish-action@" not in gh:
        missing.append("шаг выкладки в GitHub Actions")
    if "Спасибо за запрос" not in gl:
        missing.append("приветствие в GitLab CI")
    if "ci/build.sh" not in gl:
        missing.append("сборка в GitLab CI")
    if missing:
        ok = False
        print("3. работа конвейера: пропало — %s" % ", ".join(missing))
        print("   задача не в том, чтобы убрать шаги, а в том, чтобы их починить")
    else:
        print("3. работа конвейера: приветствие, сборка и выкладка на месте")

    print("зачтено" if ok else "не зачтено")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
