"""Функциональность прав и ограничителя: должна остаться зелёной после починки.

Проверяется поведение, которое обязано работать при живых зависимостях.
Запуск против решения:
    LAB_TARGET=solution.py python tests.py
"""

import sys

import labtarget
import sandbox

USER = {"name": "alice", "role": "user"}
ADMIN = {"name": "root", "role": "admin"}

CASES = [
    (ADMIN, "grant_admin", "200"),
    (ADMIN, "read", "200"),
    (USER, "read", "200"),
    (USER, "delete_user", "403"),
    (USER, "export_all", "403"),
]


def main() -> int:
    name, mod = labtarget.load()
    print(f"цель: {name}")
    failed = 0

    for user, action, expect in CASES:
        got = mod.authorize(sandbox.PolicyService(), user, action)
        ok = got.startswith(expect)
        failed += 0 if ok else 1
        print(f"  {'ок  ' if ok else 'ПАДЕНИЕ'} {user['role']:>5} {action:<12}"
              f" ждали {expect}, получили {got}")

    store = sandbox.CounterStore()
    allowed = sum(1 for _ in range(10) if mod.login_attempt(store, "carol", "x"))
    ok = allowed == sandbox.RATE_LIMIT
    failed += 0 if ok else 1
    print(f"  {'ок  ' if ok else 'ПАДЕНИЕ'} ограничитель: пропущено {allowed} "
          f"из 10, ждали {sandbox.RATE_LIMIT}")

    print(f"упало проверок: {failed} из {len(CASES) + 1}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
