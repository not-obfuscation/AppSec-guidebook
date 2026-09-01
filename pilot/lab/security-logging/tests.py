"""Функциональные тесты сервиса. Должны проходить и до правки, и после.

Проверяют не безопасность, а то, что починка ничего не сломала:
вход работает, события журналируются, у записи есть обязательные
атрибуты.

Код возврата: 0 — все проверки прошли, 1 — есть упавшие.
"""

import sys

from labtarget import load

FAILED: list[str] = []


def check(name: str, condition: bool) -> None:
    print(f"  {'OK  ' if condition else 'ПАДАЕТ'} {name}")
    if not condition:
        FAILED.append(name)


def main() -> int:
    name, lab = load()
    print(f"Цель: {name}")

    lab.reset()
    token = lab.login("anna", "qwerty2026")
    check("верный пароль пускает", token is not None)
    check("отчёт по токену открывается",
          token is not None and lab.read_report(token) is not None)

    lab.reset()
    check("неверный пароль не пускает",
          lab.login("anna", "qwerty2027") is None)
    check("неизвестный логин не пускает",
          lab.login("nobody", "qwerty2026") is None)
    check("чужой токен не открывает отчёт",
          lab.read_report("0" * 16) is None)

    lab.reset()
    lab.login("anna", "qwerty2027")
    log = lab.dump_log()
    check("отказ входа пишется в журнал", len(log) == 1)
    if log:
        line = log[0]
        check("у записи есть отметка времени", line[:4].isdigit())
        check("у записи есть тип события", "event=login" in line)
        check("у записи есть логин", "user=anna" in line)
        check("у записи есть исход", "result=fail" in line)

    lab.reset()
    check("после сброса журнал пуст", lab.dump_log() == [])

    print(f"Упало проверок: {len(FAILED)}")
    for item in FAILED:
        print(f"  - {item}")
    return 1 if FAILED else 0


if __name__ == "__main__":
    sys.exit(main())
