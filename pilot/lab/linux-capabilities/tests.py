"""Функциональные тесты агента. Должны проходить и до правки, и после.

Проверяют не безопасность, а то, что починка ничего не сломала.

Код возврата: 0 — все проверки прошли, 1 — есть упавшие.
"""

import sys

from labtarget import load

FAILED: list[str] = []

TARGETS = {"db": True, "cache": False}


def check(name: str, condition: bool) -> None:
    print(f"  {'OK  ' if condition else 'ПАДАЕТ'} {name}")
    if not condition:
        FAILED.append(name)


def main() -> int:
    name, lab = load()
    print(f"Цель: {name}")

    agent = lab.start_agent(TARGETS)
    check("живой узел отвечает «доступен»", agent.probe("db") == "db: доступен")
    check("мёртвый узел отвечает «недоступен»",
          agent.probe("cache") == "cache: недоступен")
    check("повторная проверка работает", agent.probe("db") == "db: доступен")
    check("отчёт перечисляет проверенные узлы",
          agent.report() == "db, cache, db")

    try:
        agent.probe("unknown")
        check("узел вне списка отклоняется", False)
    except KeyError:
        check("узел вне списка отклоняется", True)

    empty = lab.start_agent({})
    check("агент без целей стартует и отчитывается",
          empty.report() == "проверок не было")

    # У агента должен оставаться рабочий вызов: сырой сокет.
    check("агенту доступен сырой сокет", lab.raw_socket(agent.proc))

    print(f"Упало проверок: {len(FAILED)}")
    for item in FAILED:
        print(f"  - {item}")
    return 1 if FAILED else 0


if __name__ == "__main__":
    sys.exit(main())
