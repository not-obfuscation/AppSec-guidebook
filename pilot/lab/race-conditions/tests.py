"""Функциональность кошелька: должна остаться зелёной после починки.

Проверяет сохранность работы, не безопасность. Запуск:
    python3 tests.py
    LAB_TARGET=solution.py python3 tests.py
"""

import sys

import sandbox
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

    sandbox.reset(lab.SCHEMA_UNIQUE_REDEEM)
    check(lab.withdraw(30) == "выдано", "снятие в пределах остатка проходит")
    check(sandbox.balance() == 70, "остаток уменьшился ровно на снятое")
    check(lab.withdraw(1000) == "недостаточно средств",
          "снятие сверх остатка отвергнуто")
    check(sandbox.balance() == 70, "отклонённое снятие остаток не тронуло")

    sandbox.reset(lab.SCHEMA_UNIQUE_REDEEM)
    check(lab.redeem(sandbox.PROMO_CODE, "u1") == "скидка начислена",
          "первое применение кода проходит")
    check(lab.redeem(sandbox.PROMO_CODE, "u1") == "код уже использован",
          "второе применение кода отвергнуто")
    check(lab.redeem("НЕТ-ТАКОГО", "u1") == "код не найден",
          "неизвестный код отвергнут")

    print()
    print(f"упало: {failed}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
