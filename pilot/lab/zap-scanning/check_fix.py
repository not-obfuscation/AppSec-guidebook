#!/usr/bin/env python3
"""Проверялка задачи «почини»: hack.py и tests.py должны быть зелёными разом.

    ./stand.sh reset
    python3 check_fix.py

Критерий: ни одна проба hack.py не проходит и ни одна проверка tests.py не
падает. Одно без другого не считается: выключить поиск целиком — не починка.
"""
import pathlib
import subprocess
import sys

HERE = pathlib.Path(__file__).parent


def run(name):
    proc = subprocess.run([sys.executable, str(HERE / name)], capture_output=True, text=True)
    print(proc.stdout.rstrip())
    if proc.stderr.strip():
        print(proc.stderr.rstrip())
    return proc.returncode


def main():
    print("== пробы эксплуатации ==")
    hack = run("hack.py")
    print("\n== функциональные проверки ==")
    tests = run("tests.py")
    if hack == 2 or tests == 2:
        return 2
    print()
    if hack == 0 and tests == 0:
        print("зачтено: дефекты закрыты, лавка работает")
        return 0
    if hack != 0:
        print("не зачтено: часть проб всё ещё проходит")
    if tests != 0:
        print("не зачтено: сломана работа приложения")
    return 1


if __name__ == "__main__":
    sys.exit(main())
