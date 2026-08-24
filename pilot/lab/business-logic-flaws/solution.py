"""Образец починки: состояние на сервере, цена из каталога, пересчёт скидки.

Три решения. Каждый шаг объявляет, из каких состояний он допустим. Цена
берётся по артикулу и присланная не участвует. Скидка вычисляется заново на
каждом изменении корзины, а подтверждение сверяет деньги.
"""

from decimal import Decimal

CATALOG = {"desk": Decimal("450.00"), "pen": Decimal("2.00")}
THRESHOLD = Decimal("1000.00")
DISCOUNT_RATE = Decimal("0.10")
MAX_QTY = 20

ALLOWED = {"new": {"cart", "discount", "pay"},
           "priced": {"cart", "discount", "pay"},
           "paid": {"confirm"},
           "confirmed": set()}


def new_order():
    return {"lines": [], "total": Decimal("0.00"),
            "discount": Decimal("0.00"), "paid": Decimal("0.00"),
            "status": "new"}


def _step(order, name):
    if name not in ALLOWED[order["status"]]:
        raise PermissionError(
            f"шаг {name} закрыт из состояния {order['status']}")


def _discount_for(order):
    if order["total"] >= THRESHOLD:
        return (order["total"] * DISCOUNT_RATE).quantize(Decimal("0.01"))
    return Decimal("0.00")


def add_line(order, req):
    _step(order, "cart")
    if req["sku"] not in CATALOG:
        raise ValueError("неизвестный артикул")
    qty = int(req["qty"])
    if not 1 <= qty <= MAX_QTY:
        raise ValueError("количество вне границ")
    order["lines"].append((req["sku"], qty, CATALOG[req["sku"]]))
    order["total"] = sum(q * p for _, q, p in order["lines"])
    order["discount"] = _discount_for(order)
    order["status"] = "priced"
    return order["total"]


def apply_discount(order):
    _step(order, "discount")
    order["discount"] = _discount_for(order)
    return ("скидка начислена" if order["discount"]
            else "порог не достигнут")


def due(order):
    return order["total"] - order["discount"]


def pay(order, amount):
    _step(order, "pay")
    amount = Decimal(str(amount))
    if amount != due(order):
        raise ValueError(f"к оплате {due(order)}, прислано {amount}")
    order["paid"] += amount
    order["status"] = "paid"
    return "оплачено"


def confirm(order):
    _step(order, "confirm")
    if order["paid"] != due(order):
        raise PermissionError("оплата не сходится")
    order["status"] = "confirmed"
    return "заказ подтверждён"
