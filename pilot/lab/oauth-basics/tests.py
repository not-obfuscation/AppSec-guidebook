"""Функциональность входа через OAuth: должна остаться зелёной после починки.

Запуск:
    python3 tests.py
    LAB_TARGET=solution.py python3 tests.py
"""

import sys

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

    lab.reset()
    req = lab.build_authorization_request()
    check("client_id=shop-client" in req, "запрос несёт client_id клиента")
    check("state=" in req, "запрос несёт параметр state")

    redirect_w = lab.authorize(req, "wiener")
    check(lab.complete_login(redirect_w) == "AT-wiener-7a1c",
          "вход wiener выдаёт клиенту его токен доступа")

    lab.reset()
    redirect_a = lab.authorize(lab.build_authorization_request(), "administrator")
    check(lab.complete_login(redirect_a) == "AT-admin-0001",
          "вход administrator выдаёт клиенту его токен доступа")

    print()
    print(f"упало: {failed}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
