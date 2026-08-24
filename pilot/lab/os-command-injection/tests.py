"""Функциональность подписи: должна остаться зелёной после починки.

Запуск:
    python3 tests.py
    LAB_TARGET=solution.py python3 tests.py
"""

import sys

from labtarget import load


def main() -> int:
    name, lab = load()
    print(f"Цель: {name}")
    failed = 0

    def check(cond, label):
        nonlocal failed
        if not cond:
            failed += 1
        print(f"  {'OK  ' if cond else 'УПАЛ'} {label}")

    out = lab.make_label("Q3")
    check("Отчёт:" in out and "Q3" in out, "обычная подпись строится")

    out = lab.make_label("годовой")
    check("годовой" in out, "подпись с кириллицей работает")

    print()
    print(f"упало: {failed}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
