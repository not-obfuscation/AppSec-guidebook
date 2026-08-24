"""Функциональность магазина: должна остаться зелёной после починки.

Проверяет сохранность работы, не безопасность. Запуск:
    python3 tests.py
    LAB_TARGET=solution.py python3 tests.py
"""

import sys
from decimal import Decimal

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

    order = lab.new_order()
    check(lab.add_line(order, {"sku": "desk", "qty": "1"})
          == Decimal("450.00"), "корзина из одной строки считается")

    order = lab.new_order()
    lab.add_line(order, {"sku": "desk", "qty": "1"})
    check(lab.add_line(order, {"sku": "pen", "qty": "2"})
          == Decimal("454.00"), "корзина из двух строк складывается")

    order = lab.new_order()
    lab.add_line(order, {"sku": "desk", "qty": "3"})
    lab.apply_discount(order)
    check(lab.due(order) == Decimal("1215.00"),
          "скидка на пороге начисляется")

    order = lab.new_order()
    lab.add_line(order, {"sku": "desk", "qty": "1"})
    check(lab.pay(order, "450.00") == "оплачено",
          "оплата ровно к оплате принимается")

    order = lab.new_order()
    try:
        lab.add_line(order, {"sku": "нет-такого", "qty": "1"})
        unknown = False
    except ValueError:
        unknown = True
    check(unknown, "неизвестный артикул отвергнут")

    order = lab.new_order()
    lab.add_line(order, {"sku": "desk", "qty": "2"})
    lab.pay(order, lab.due(order))
    lab.confirm(order)
    check(order["status"] == "confirmed",
          "законный заказ доходит до подтверждения")

    print()
    print(f"упало: {failed}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
