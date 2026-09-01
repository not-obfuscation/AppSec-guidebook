"""Функциональные тесты мониторинга. Должны проходить и до, и после.

Проверяют не безопасность, а то, что починка ничего не сломала.

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

    daemon = lab.Daemon()
    _, report = lab.monitoring_container(daemon)
    check("пустой хост: контейнеров 0", report() == "контейнеров на хосте: 0")

    daemon.containers.append({"name": "web", "image": "nginx"})
    check("отчёт видит новый контейнер",
          report() == "контейнеров на хосте: 1")

    daemon.containers.append({"name": "db", "image": "postgres"})
    check("отчёт видит оба", report() == "контейнеров на хосте: 2")
    check("повторный вызов не падает", report() == "контейнеров на хосте: 2")

    # Демон хоста работает напрямую — канал мониторинга ему не мешает
    code, created = daemon.handle("POST", "/containers/create",
                                  {"name": "job", "image": "alpine"})
    check("демон напрямую создаёт контейнеры", code == 201 and
          created == "job")
    check("отчёт видит созданное напрямую",
          report() == "контейнеров на хосте: 3")

    code, _ = daemon.handle("GET", "/unknown")
    check("неизвестная точка API отвечает 404", code == 404)

    print(f"Упало проверок: {len(FAILED)}")
    for item in FAILED:
        print(f"  - {item}")
    return 1 if FAILED else 0


if __name__ == "__main__":
    sys.exit(main())
