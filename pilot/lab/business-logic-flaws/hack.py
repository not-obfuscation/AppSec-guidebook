"""Эксплойт лабы business-logic-flaws: три нарушенных правила магазина.

Механизмы магазина исправны: артикул сверяется с каталогом, количество
целое, суммы складываются верно. Нарушены правила предметной области —
отгрузка после оплаты, цена из прайс-листа, скидка при выполненном условии.

Локально, к сети не обращается, против чужих систем неприменимо.

Код возврата:
    0 — эксплойт НЕ сработал (все три правила удержаны)
    1 — эксплойт сработал (хотя бы одно правило нарушено)
"""

import sys
from decimal import Decimal

from labtarget import load


def experiment_1_confirm_without_pay(lab):
    """Подтверждение заказа, за который не заплачено."""
    order = lab.new_order()
    try:
        lab.add_line(order, {"sku": "desk", "qty": "2"})
        lab.confirm(order)
    except (PermissionError, ValueError) as e:
        print(f"  опыт 1 — confirm без pay: отказ ({e})")
        return False
    got = order["status"] == "confirmed" and order["paid"] == Decimal("0.00")
    print(f"  опыт 1 — confirm без pay: "
          f"{'ЗАКАЗ ПОДТВЕРЖДЁН, внесено 0.00' if got else 'не прошло'}")
    return got


def experiment_2_price_from_request(lab):
    """Цена товара приходит вместе с товаром."""
    order = lab.new_order()
    try:
        lab.add_line(order, {"sku": "desk", "qty": "1", "price": "0.01"})
        lab.pay(order, "0.01")
        lab.confirm(order)
    except (PermissionError, ValueError) as e:
        print(f"  опыт 2 — цена 0.01 вместо 450.00: отказ ({e})")
        return False
    got = order["status"] == "confirmed" and order["total"] < Decimal("1.00")
    tail = (f"ЗАКАЗ ПОДТВЕРЖДЁН, итог {order['total']}"
            if got else "не прошло")
    print(f"  опыт 2 — цена 0.01 вместо 450.00: {tail}")
    return got


def experiment_3_discount_survives(lab):
    """Скидка взята на пороге и удержана после уменьшения корзины."""
    order = lab.new_order()
    try:
        lab.add_line(order, {"sku": "desk", "qty": "3"})
        lab.apply_discount(order)
        lab.add_line(order, {"sku": "desk", "qty": "-1"})
        lab.pay(order, lab.due(order))
        lab.confirm(order)
    except (PermissionError, ValueError) as e:
        print(f"  опыт 3 — скидка пережила уменьшение корзины: отказ ({e})")
        return False
    got = order["discount"] > 0 and order["total"] < lab.THRESHOLD
    tail = (f"итог {order['total']}, скидка {order['discount']}"
            if got else "не прошло")
    print(f"  опыт 3 — скидка пережила уменьшение корзины: {tail}")
    return got


def experiment_4_control(lab):
    """Контроль на живучесть: законный заказ обязан проходить."""
    order = lab.new_order()
    try:
        lab.add_line(order, {"sku": "desk", "qty": "1"})
        lab.pay(order, "450.00")
        lab.confirm(order)
        ok = order["status"] == "confirmed"
    except Exception:
        ok = False
    print(f"  опыт 4 — контроль, законный заказ на 450.00: "
          f"{'проведён' if ok else 'ПОЧИНКА СЛОМАЛА МАГАЗИН'}")
    return ok


def main() -> int:
    name, lab = load()
    print(f"Цель: {name}")
    print(f"каталог: {dict((k, str(v)) for k, v in lab.CATALOG.items())}, "
          f"порог скидки {lab.THRESHOLD}")
    print()
    broken = [
        experiment_1_confirm_without_pay(lab),
        experiment_2_price_from_request(lab),
        experiment_3_discount_survives(lab),
    ]
    control = experiment_4_control(lab)
    print()
    if any(broken):
        print(f"ЭКСПЛОЙТ СРАБОТАЛ: правило предметной области нарушено "
              f"({sum(broken)} из 3 опытов)")
        return 1
    if not control:
        print("ЭКСПЛОЙТ НЕ СРАБОТАЛ, но контроль упал: законный заказ "
              "перестал проходить")
        return 1
    print("эксплойт не сработал: три правила удержаны, законный заказ "
          "проходит")
    return 0


if __name__ == "__main__":
    sys.exit(main())
