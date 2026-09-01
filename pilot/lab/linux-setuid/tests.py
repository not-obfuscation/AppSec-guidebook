"""Функциональные тесты обёртки. Должны проходить и до правки, и после.

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

    host = lab.make_host()
    env = {"PATH": "/usr/bin", "LANG": "ru_RU.UTF-8"}
    out = lab.run_backup(host, 1000, env)
    check("обычный запуск собирает копию", "копия собрана" in out)
    check("LANG доезжает до сборщика", "ru_RU.UTF-8" in out)
    check("копия лежит в /var/backups",
          "/var/backups/latest.tar" in host.files)

    path, euid, argv = host.exec_log[-1]
    check("журнал зафиксировал настоящий сборщик",
          path == "/usr/bin/collect-backup")
    check("сборщик работал с euid 0", euid == 0)

    out2 = lab.run_backup(host, 1001, env)
    check("запуск от другого пользователя тоже работает",
          "копия собрана" in out2)
    check("журнал ведётся по каждому запуску", len(host.exec_log) == 2)

    try:
        lab.run_backup(host, "1000", env)
        check("нечисловой uid отклоняется", False)
    except TypeError:
        check("нечисловой uid отклоняется", True)

    print(f"Упало проверок: {len(FAILED)}")
    for item in FAILED:
        print(f"  - {item}")
    return 1 if FAILED else 0


if __name__ == "__main__":
    sys.exit(main())
