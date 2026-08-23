"""Образцовое решение лабы: выборка ограничена владельцем.

Отличий от code.py три.

1. Объект ищется не по всей таблице, а в выборке текущего
   пользователя: `Invoice.owned_by(user).get(id)`. Опыты 1 и 3.
2. То же правило стоит на изменяющей операции, а не только на
   читающей. Опыт 2.
3. Чужой и несуществующий объект отвечают одинаково: `NotFound`. Иначе
   разница ответов подтверждает, что счёт существует.

Идентификаторы в ленте компании заменены на непрозрачные ссылки,
привязанные к получателю ленты: показывать чужой ключ незачем.
"""

import hashlib

USERS = {"anna": {"company": "acme"}, "boris": {"company": "globex"}}


class Invoice:
    """Таблица счетов. Ключ — номер, у каждого счёта есть владелец."""

    ROWS = {}

    @classmethod
    def owned_by(cls, owner):
        """Выборка пользователя: дальше ищут только в ней."""
        return {k: v for k, v in cls.ROWS.items() if v["owner"] == owner}

    @classmethod
    def by_owner(cls, owner):
        return cls.owned_by(owner)


class Denied(Exception):
    """Отказ в доступе."""


class NotFound(Exception):
    """Объекта нет либо он не ваш: ответ одинаковый."""


def _own_invoice(user, invoice_id):
    invoice = Invoice.owned_by(user).get(invoice_id)
    if invoice is None:
        raise NotFound
    return invoice


def read_invoice(user, invoice_id):
    """Показать счёт."""
    return dict(_own_invoice(user, invoice_id))


def set_invoice_email(user, invoice_id, email):
    """Сменить адрес, на который уходит счёт."""
    invoice = _own_invoice(user, invoice_id)
    invoice["email"] = email
    return dict(invoice)


def list_invoices(user):
    """Свои счета."""
    return Invoice.by_owner(user)


def opaque_ref(viewer, invoice_id):
    """Ссылка на счёт для ленты: своя у каждого получателя."""
    raw = f"{viewer}:{invoice_id}".encode("utf-8")
    return hashlib.sha256(raw).hexdigest()[:16]


def company_feed(user):
    """Лента компании без чужих ключей."""
    return [{"actor": row["owner"], "invoice_ref": opaque_ref(user, ref),
             "at": row["at"]}
            for ref, row in sorted(Invoice.ROWS.items())]


def reset():
    Invoice.ROWS.clear()
    Invoice.ROWS.update({
        "1001": {"owner": "anna", "email": "anna@acme.test",
                 "sum": 120, "at": "2026-08-01"},
        "1002": {"owner": "boris", "email": "boris@globex.test",
                 "sum": 90_000, "at": "2026-08-02"},
        "b9f1c0d6-7a41-4a2e-9d3b-6c5e0f2a1d84": {
            "owner": "boris", "email": "cfo@globex.test",
            "sum": 4_500_000, "at": "2026-08-03"},
    })
