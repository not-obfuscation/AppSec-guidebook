"""Функциональные тесты сервиса. Должны проходить и до правки, и после.

Проверяют не безопасность, а то, что починка ничего не сломала.

Код возврата: 0 — все проверки прошли, 1 — есть упавшие.
"""

import os
import sys
import tempfile

from labtarget import load

FAILED: list[str] = []


def check(name: str, condition: bool) -> None:
    print(f"  {'OK  ' if condition else 'ПАДАЕТ'} {name}")
    if not condition:
        FAILED.append(name)


def main() -> int:
    name, lab = load()
    print(f"Цель: {name}")

    with tempfile.TemporaryDirectory() as workdir:
        path = os.path.join(workdir, "service.conf")

        lab.write_config(path, "tok-first")
        check("конфиг пишется и читается обратно",
              lab.read_config(path) == "tok-first")

        lab.write_config(path, "tok-second")
        check("повторная запись обновляет токен",
              lab.read_config(path) == "tok-second")

        lab.ensure_config(path, "tok-third")
        check("ensure_config не затирает существующий файл",
              lab.read_config(path) == "tok-second")

        other = os.path.join(workdir, "other.conf")
        lab.ensure_config(other, "tok-third")
        check("ensure_config создаёт отсутствующий файл",
              lab.read_config(other) == "tok-third")

        try:
            lab.write_config(os.path.join(workdir, "empty.conf"), "")
            check("пустой токен отклоняется", False)
        except ValueError:
            check("пустой токен отклоняется", True)

        # Конфиг обязан оставаться рабочим под любой из типовых масок
        for mask in (0o022, 0o027, 0o077):
            target = os.path.join(workdir, f"m{mask:03o}.conf")
            old_umask = os.umask(mask)
            try:
                lab.write_config(target, "tok-mask")
            finally:
                os.umask(old_umask)
            mode = os.stat(target).st_mode & 0o777
            check(f"при umask {mask:03o} владелец читает и пишет",
                  mode & 0o600 == 0o600)
            check(f"при umask {mask:03o} чтение работает",
                  lab.read_config(target) == "tok-mask")

    print(f"Упало проверок: {len(FAILED)}")
    for item in FAILED:
        print(f"  - {item}")
    return 1 if FAILED else 0


if __name__ == "__main__":
    sys.exit(main())
