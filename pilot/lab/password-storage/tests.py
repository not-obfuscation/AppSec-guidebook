"""Функциональные тесты сервиса. Должны проходить и до правки, и после.

Проверяют не безопасность, а то, что починка ничего не сломала.

Код возврата: 0 — все проверки прошли, 1 — есть упавшие.
"""

import hashlib
import sys
import time

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
    lab.register("anna", "correct horse battery staple")
    check("верный пароль пускает",
          lab.verify("anna", "correct horse battery staple"))
    check("неверный пароль не пускает",
          not lab.verify("anna", "correct horse battery stapl"))
    check("неизвестный логин не пускает",
          not lab.verify("nobody", "correct horse battery staple"))

    # ASVS v5.0-6.2.8: пароль проверяется ровно в том виде, в каком пришёл
    lab.reset()
    lab.register("boris", " пароль с пробелами ")
    check("пробелы по краям не срезаются",
          lab.verify("boris", " пароль с пробелами "))
    check("пароль без пробелов не подходит",
          not lab.verify("boris", "пароль с пробелами"))

    lab.reset()
    lab.register("carol", "Пароль-Ёжик-🦔-2026")
    check("не-ASCII и эмодзи работают",
          lab.verify("carol", "Пароль-Ёжик-🦔-2026"))
    check("регистр значим",
          not lab.verify("carol", "пароль-ёжик-🦔-2026"))

    # ASVS v5.0-6.2.9: пароли не короче 64 символов должны приниматься
    lab.reset()
    long_password = "ф" * 64
    lab.register("dmitry", long_password)
    check("пароль в 64 символа принимается",
          lab.verify("dmitry", long_password))
    check("усечённый пароль не подходит",
          not lab.verify("dmitry", "ф" * 63))

    # Записи предыдущей версии сервиса уже лежат в проде
    lab.reset()
    legacy = hashlib.sha256("stariy-parol-2019".encode("utf-8")).hexdigest()
    lab.load_legacy("elena", legacy)
    check("пользователь из старой базы входит",
          lab.verify("elena", "stariy-parol-2019"))
    check("чужой пароль старую запись не открывает",
          not lab.verify("elena", "123456"))

    lab.reset()
    lab.register("fedor", "8f!Tz2rP-vQx91Ld")
    start = time.perf_counter()
    lab.verify("fedor", "8f!Tz2rP-vQx91Ld")
    spent = time.perf_counter() - start
    # Password Storage Cheat Sheet: проверка должна укладываться в секунду
    check(f"проверка укладывается в 1 с (заняла {spent * 1000:.0f} мс)",
          spent < 1.0)

    lab.reset()
    lab.register("galina", "parol")
    dump = lab.export_dump()
    check("export_dump отдаёт пары (логин, строка)",
          isinstance(dump, list) and len(dump) == 1
          and isinstance(dump[0][0], str) and isinstance(dump[0][1], str))
    check("пароль в открытом виде в дампе не лежит",
          "parol" not in dump[0][1])

    print(f"Упало проверок: {len(FAILED)}")
    for item in FAILED:
        print(f"  - {item}")
    return 1 if FAILED else 0


if __name__ == "__main__":
    sys.exit(main())
