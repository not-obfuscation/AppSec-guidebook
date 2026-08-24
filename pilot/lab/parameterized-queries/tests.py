"""Функциональность выборки: должна остаться зелёной после починки.

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

    lab.reset()

    rows = lab.by_ids(["1", "2"])
    check(sorted(r[0] for r in rows) == [1, 2],
          "выборка по списку id возвращает эти товары")

    rows = lab.by_ids(["4"])
    check([r[0] for r in rows] == [4], "выборка одного id работает")

    rows = lab.by_ids(["3"])
    check(rows == [], "невыпущенный товар не возвращается по id")

    cat = [r[1] for r in lab.by_category("Gifts")]
    check("Открытка" in cat and "Букет" in cat,
          "выборка по категории возвращает выпущенное")
    check("Подарок к запуску" not in cat,
          "выборка по категории скрывает невыпущенное")

    print()
    print(f"упало: {failed}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
