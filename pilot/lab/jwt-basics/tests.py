"""Функциональность кабинета: должна остаться зелёной после починки.

Проверяет сохранность работы, не безопасность. Запуск:
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

    u = lab.issue("wiener")
    a = lab.issue("administrator")

    check(lab.authorize(u) == "user", "пользователь входит и получает роль user")
    check(lab.authorize(a) == "admin", "администратор входит и получает роль admin")
    check(lab.authorize("не.токен.вовсе") is None, "мусор вместо токена отвергнут")
    check(lab.get_discount(u) == "PROMO-8842-INTERNAL",
          "скидочный код пользователя доступен через сервер")
    check(lab.get_email(a) == "admin@shop.example",
          "адрес почты администратора доступен через сервер")

    print()
    print(f"упало: {failed}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
