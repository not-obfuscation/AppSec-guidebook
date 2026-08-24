"""Тест-кейсы правила money-value-from-request.

Разметка: строка ruleid над ожидаемой находкой, строка ok над чистым местом.
"""

from decimal import Decimal

CATALOG = {"desk": Decimal("450.00"), "pen": Decimal("2.00")}


def line_price_from_body(req):
    """Цена приходит вместе с артикулом."""
    # ruleid: money-value-from-request
    return Decimal(req["price"])


def total_from_body(payload):
    """Итог заказа берётся готовым из запроса."""
    # ruleid: money-value-from-request
    return float(payload["total"])


def discount_via_str(form):
    """Обёртка str() не меняет происхождения значения."""
    # ruleid: money-value-from-request
    return Decimal(str(form["discount"]))


def line_price_from_catalog(req):
    """Цена берётся по артикулу из каталога на сервере."""
    # ok: money-value-from-request
    return CATALOG[req["sku"]]


def quantity_from_body(req):
    """Количество клиент называть вправе: это не денежная величина."""
    # ok: money-value-from-request
    qty = int(req["qty"])
    if not 1 <= qty <= 20:
        raise ValueError("количество вне допустимого")
    return qty
