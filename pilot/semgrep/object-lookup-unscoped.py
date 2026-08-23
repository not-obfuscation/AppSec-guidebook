"""Тест-кейсы правила object-lookup-unscoped.

Маркер стоит строкой выше ожидаемой находки: `ruleid:` — правило
обязано сработать, `ok:` — обязано промолчать. Сверка:

    .venv-tools/bin/python pilot/semgrep/check.py object-lookup
"""


class Invoice:
    ROWS = {}


class Report:
    ROWS = {}


require_owner = None


# --- ловит -----------------------------------------------------------

def read_invoice(user, invoice_id):
    # ruleid: object-lookup-unscoped
    return Invoice.get(invoice_id)


def read_report(user, report_ref, fmt="pdf"):
    # ruleid: object-lookup-unscoped
    row = Report.find(report_ref)
    return render(row, fmt)


def delete_invoice(user, invoice_uuid):
    # ruleid: object-lookup-unscoped
    Invoice.get_or_404(invoice_uuid).delete()


# --- молчит ----------------------------------------------------------

def read_invoice_scoped(user, invoice_id):
    # Выборка ограничена владельцем: получатель вызова — не таблица.
    # ok: object-lookup-unscoped
    return Invoice.owned_by(user).get(invoice_id)


def read_invoice_relation(user, invoice_id):
    # Связь пользователя, а не глобальная таблица.
    # ok: object-lookup-unscoped
    return user.invoices.get(invoice_id)


def settings_of(user, name):
    # Параметр не похож на идентификатор объекта.
    # ok: object-lookup-unscoped
    return Invoice.get(name)


def background_job(invoice_id):
    # Пользователя в функции нет: это фоновая задача, а не запрос.
    # ok: object-lookup-unscoped
    return Invoice.get(invoice_id)


def render(row, fmt):
    return f"{row}:{fmt}"
