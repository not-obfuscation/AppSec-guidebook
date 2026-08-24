"""Функциональность выдачи: должна остаться зелёной после починки.

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

    def refused(name_):
        try:
            lab.read_document(name_)
            return False
        except (OSError, PermissionError, ValueError):
            return True

    check("январь" in lab.read_document("invoice-2026-01.txt"),
          "документ из базового каталога отдаётся")
    check("декабрь" in lab.read_document("archive/invoice-2025-12.txt"),
          "документ из подкаталога отдаётся")
    check("февраль" in lab.read_document("archive/../invoice-2026-02.txt"),
          "путь с .. внутри базового каталога остаётся рабочим")
    check(refused("нет-такого.txt"),
          "несуществующий документ отвергнут")
    check("invoice-2026-01.txt" in lab.list_documents(),
          "перечень документов собирается")

    print()
    print(f"упало: {failed}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
