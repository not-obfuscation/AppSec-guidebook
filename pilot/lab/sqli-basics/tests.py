"""Функциональность витрины: должна остаться зелёной после починки.

Проверяет не безопасность, а сохранность работы. Запуск:
    python3 tests.py                     # против code.py
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
        mark = "OK  " if cond else "УПАЛ"
        if not cond:
            failed += 1
        print(f"  {mark} {label}")

    lab.reset()

    rows = lab.search_products("Gifts")
    names = [r[0] for r in rows]
    check("Открытка" in names and "Букет" in names,
          "поиск Gifts возвращает выпущенные товары")
    check("Подарок к запуску" not in names,
          "поиск Gifts скрывает невыпущенное")

    tech = [r[0] for r in lab.search_products("Tech")]
    check(tech == ["Наушники"], "поиск Tech возвращает свою категорию")

    check(lab.search_products("Нет такой") == [],
          "неизвестная категория возвращает пусто")

    admin = lab.login("administrator", "s3cr3t-9f2a")
    check(admin is not None and admin["role"] == "admin",
          "администратор входит по паролю")

    user = lab.login("wiener", "peter")
    check(user is not None and user["role"] == "user",
          "пользователь входит по паролю")

    check(lab.login("wiener", "wrong") is None,
          "неверный пароль не пускает")

    print()
    print(f"упало: {failed}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
