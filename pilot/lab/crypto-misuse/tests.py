"""Функциональность профиля и сеанса: должна остаться зелёной после починки.

Проверяется поведение, которое обязано работать: выданное значение читается
обратно и все три поля сохраняются. Запуск против решения:
    LAB_TARGET=solution.py python tests.py
"""

import sys

import labtarget

CASES = [
    ("alice", "user0", 50),
    ("bob", "admin", 0),
    ("charlie", "user0", 1000000),
]


def main() -> int:
    name, mod = labtarget.load()
    print(f"цель: {name}")
    failed = 0

    for user, role, credit in CASES:
        got = mod.load_profile(mod.issue_profile(user, role, credit))
        ok = got.get("user") == user and got.get("role") == role \
            and got.get("credit") == str(credit)
        print(f"  профиль {user}/{role}/{credit}: {'ok' if ok else 'СБОЙ'}")
        failed += not ok

    for user, role, credit in CASES:
        got = mod.load_session(mod.issue_session(user, role, credit))
        ok = got.get("user") == user and got.get("role") == role \
            and got.get("credit") == str(credit)
        print(f"  сеанс {user}/{role}/{credit}: {'ok' if ok else 'СБОЙ'}")
        failed += not ok

    print(f"\nупало: {failed}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
