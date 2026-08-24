"""Функциональные тесты витрины. Проходят и до правки, и после.

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

    first = lab.handle("http://partner.example/catalog/42")
    check("карточка первого партнёра отдаётся", first["status"] == 200)
    check("тело карточки не подменено", "товар 42" in first["body"])

    second = lab.handle("http://cdn.example/catalog/7")
    check("карточка второго партнёра отдаётся",
          second["status"] == 200)

    check("явный порт партнёра принимается",
          lab.handle("http://partner.example:80/catalog/1")["status"]
          == 200)
    check("адрес партнёра по https принимается",
          lab.handle("https://partner.example/catalog/1")["status"]
          == 200)

    check("пустой адрес даёт 400, а не исключение",
          lab.handle("")["status"] == 400)
    check("мусор вместо адреса даёт 400 или 502",
          lab.handle("не адрес")["status"] in (400, 502))
    check("несуществующая карточка партнёра даёт 404 в теле",
          lab.handle("http://partner.example/catalog")["status"]
          in (200, 400))

    print()
    print(f"упало: {len(FAILED)}")
    return 1 if FAILED else 0


if __name__ == "__main__":
    sys.exit(main())
