"""Функциональные тесты кабинета. Должны проходить и до правки, и после.

Проверяют не безопасность, а то, что починка ничего не сломала.

Код возврата: 0 — все проверки прошли, 1 — есть упавшие.
"""

import sys

from labtarget import load

FAILED = []


def check(name, condition):
    print(f"  {'OK  ' if condition else 'ПАДАЕТ'} {name}")
    if not condition:
        FAILED.append(name)


def main() -> int:
    name, lab = load()
    print(f"Цель: {name}")
    lab.reset()

    check("свой счёт читается",
          lab.read_invoice("anna", "1001")["sum"] == 120)
    check("в своём счёте видна сумма и адрес",
          set(lab.read_invoice("anna", "1001")) >= {"sum", "email"})
    check("список своих счетов содержит только свои",
          list(lab.list_invoices("anna")) == ["1001"])
    check("у второго пользователя свой список",
          set(lab.list_invoices("boris")) ==
          {"1002", "b9f1c0d6-7a41-4a2e-9d3b-6c5e0f2a1d84"})

    lab.reset()
    lab.set_invoice_email("anna", "1001", "billing@acme.test")
    check("свой адрес доставки меняется",
          lab.read_invoice("anna", "1001")["email"] == "billing@acme.test")

    lab.reset()
    missing = False
    try:
        lab.read_invoice("anna", "9999")
    except lab.NotFound:
        missing = True
    except lab.Denied:
        missing = True
    check("несуществующий счёт не отдаётся", missing)

    check("лента компании отдаёт события всех участников",
          len(lab.company_feed("anna")) == 3)

    print()
    print(f"упало: {len(FAILED)}")
    return 1 if FAILED else 0


if __name__ == "__main__":
    sys.exit(main())
