"""Функциональность кабинета: должна остаться зелёной после починки.

Запуск:
    python3 tests.py
    LAB_TARGET=solution.py python3 tests.py
"""

import sys

from labtarget import load


def main() -> int:
    name, lab = load()
    print(f"Цель: {name}")
    lab.reset()
    failed = 0

    def check(cond, label):
        nonlocal failed
        if not cond:
            failed += 1
        print(f"  {'OK  ' if cond else 'УПАЛ'} {label}")

    check(lab.authorize(lab.issue("wiener", "user")) == "user",
          "пользователь входит по честному RS256")
    check(lab.authorize(lab.issue("administrator", "admin")) == "admin",
          "администратор входит по честному RS256")
    check(lab.authorize("не.токен") is None, "мусор вместо токена отвергнут")
    check(lab.authorize("a.b.c") is None, "битые части отвергнуты")
    check(isinstance(lab.public_key_pem(), (bytes, bytearray)),
          "открытый ключ доступен для проверки")

    print()
    print(f"упало: {failed}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
