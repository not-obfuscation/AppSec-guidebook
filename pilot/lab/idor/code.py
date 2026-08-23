"""Кабинет счетов: чтение, правка и выгрузка счёта по идентификатору.

Фрагмент биллинга, сведённый к одному вопросу: проверяются ли права на
объект, который достали по идентификатору из запроса. Хранилище в
памяти, сети не требуется, HTTP не поднимается.

Лаборатория гайдбука. Всё исполняется локально и применимо только к
этой лабе.

Задача: починить доступ к объектам так, чтобы hack.py перестал
срабатывать, а tests.py продолжил проходить.
"""

USERS = {"anna": {"company": "acme"}, "boris": {"company": "globex"}}


class Invoice:
    """Таблица счетов. Ключ — номер, у каждого счёта есть владелец."""

    ROWS = {}

    @classmethod
    def get(cls, invoice_id):
        """Глобальная выборка: ищет по всей таблице."""
        return cls.ROWS.get(invoice_id)

    @classmethod
    def by_owner(cls, owner):
        return {k: v for k, v in cls.ROWS.items() if v["owner"] == owner}


class Denied(Exception):
    """Отказ в доступе."""


class NotFound(Exception):
    """Объекта нет."""


# УЯЗВИМО — демонстрация, не для продакшена.
def read_invoice(user, invoice_id):
    """Показать счёт."""
    invoice = Invoice.get(invoice_id)
    if invoice is None:
        raise NotFound
    return dict(invoice)


# УЯЗВИМО — демонстрация, не для продакшена.
def set_invoice_email(user, invoice_id, email):
    """Сменить адрес, на который уходит счёт."""
    invoice = Invoice.get(invoice_id)
    if invoice is None:
        raise NotFound
    invoice["email"] = email
    return dict(invoice)


def list_invoices(user):
    """Свои счета. Показывает только свои — и это работает."""
    return Invoice.by_owner(user)


def company_feed(user):
    """Лента компании: кто выставил счёт и когда.

    Отдаёт события всех участников рынка — так задумано продуктом.
    Идентификаторы счетов в событиях остались от отладки.
    """
    return [{"actor": row["owner"], "invoice_ref": ref, "at": row["at"]}
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
