"""Функциональные тесты портала. Должны проходить и до правки, и после.

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

    check("свой профиль открыт обычному пользователю",
          lab.handle("anna", "/profile")["status"] == 200)
    check("свои заявки открыты обычному пользователю",
          lab.handle("anna", "/tickets")["status"] == 200)
    check("в своих заявках только свои",
          list(lab.handle("anna", "/tickets")["body"]) == [1])
    check("администратор видит список учётных записей",
          lab.handle("sysadmin", "/admin/users")["status"] == 200)
    check("администратор выгружает заявки",
          lab.handle("sysadmin", "/admin/export")["status"] == 200)

    lab.reset()
    resp = lab.handle("sysadmin", "/admin/tickets/delete",
                      method="POST", query={"id": "1"})
    check("администратор удаляет заявку", resp["status"] == 200)
    check("заявка действительно удалена", 1 not in lab.TICKETS)
    lab.reset()

    check("неизвестный маршрут даёт 404",
          lab.handle("anna", "/nothing/here")["status"] == 404)
    check("административная функция закрыта обычному пользователю",
          lab.handle("anna", "/admin/users")["status"] == 403)

    print()
    print(f"упало: {len(FAILED)}")
    return 1 if FAILED else 0


if __name__ == "__main__":
    sys.exit(main())
