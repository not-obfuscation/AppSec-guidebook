"""УЯЗВИМЫЙ образец: магазин из четырёх шагов.

Заказ проходит корзину, скидку, оплату и подтверждение. Сервер не помнит, на
каком шаге заказ, и берёт цену из тела запроса.

Демонстрация для лабы, не для продакшена.
"""

from decimal import Decimal

CATALOG = {"desk": Decimal("450.00"), "pen": Decimal("2.00")}
THRESHOLD = Decimal("1000.00")
DISCOUNT_RATE = Decimal("0.10")
MAX_QTY = 20


def new_order():
    return {"lines": [], "total": Decimal("0.00"),
            "discount": Decimal("0.00"), "paid": Decimal("0.00"),
            "status": "new"}


def add_line(order, req):
    """Строка заказа: цена берётся из запроса, если она там есть."""
    if req["sku"] not in CATALOG:
        raise ValueError("неизвестный артикул")
    price = Decimal(req["price"]) if "price" in req else CATALOG[req["sku"]]
    order["lines"].append((req["sku"], int(req["qty"]), price))
    order["total"] = sum(q * p for _, q, p in order["lines"])
    return order["total"]


def apply_discount(order):
    """Скидка начисляется, если сумма дошла до порога."""
    if order["total"] >= THRESHOLD:
        order["discount"] = order["total"] * DISCOUNT_RATE
        return "скидка начислена"
    return "порог не достигнут"


def due(order):
    return order["total"] - order["discount"]


def pay(order, amount):
    """Платёж: принимается любая сумма."""
    order["paid"] += Decimal(str(amount))
    order["status"] = "paid"
    return "оплачено"


def confirm(order):
    """Подтверждение: состояние заказа не спрашивается."""
    order["status"] = "confirmed"
    return "заказ подтверждён"
