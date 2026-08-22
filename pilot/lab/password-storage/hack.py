"""Эксплойт лабы: восстановление паролей из утёкшего дампа.

Проверяет ровно одно свойство хранилища — можно ли атаковать всю базу
одним проходом словаря. Запускается локально, к сети не обращается,
против чужих систем неприменим.

Код возврата:
    0 — эксплойт НЕ сработал (лаба починена)
    1 — эксплойт сработал (лаба ещё уязвима)
"""

import hashlib
import sys
import time

from labtarget import load

# Пароли из ежегодных подборок «самых частых». Не дамп учётных данных:
# двенадцать общеизвестных строк, нужных, чтобы словарь был не пустым.
DICTIONARY = [
    "123456", "password", "qwerty", "111111", "iloveyou", "admin",
    "welcome", "monkey", "dragon", "letmein", "football", "abc123",
]

ACCOUNTS = [
    ("anna", "qwerty"),
    ("boris", "letmein"),
    ("carol", "qwerty"),
    ("dmitry", "8f!Tz2rP-vQx91Ld"),
]


def build_store(lab):
    lab.reset()
    for login, password in ACCOUNTS:
        lab.register(login, password)
    return lab.export_dump()


def experiment_1_shared_passwords(dump):
    """Видно ли по дампу, что два пользователя выбрали один пароль."""
    values = [value for _, value in dump]
    collided = len(values) != len(set(values))
    print(f"  опыт 1 — одинаковые пароли дают одинаковую запись: "
          f"{'ДА' if collided else 'нет'}")
    return collided


def experiment_2_one_table_for_all(dump):
    """Словарь считается один раз и прикладывается ко всей базе."""
    table = {hashlib.sha256(c.encode("utf-8")).hexdigest(): c
             for c in DICTIONARY}
    cracked = [(login, table[value]) for login, value in dump
               if value in table]
    print(f"  опыт 2 — одна таблица на всю базу вскрыла записей: "
          f"{len(cracked)} из {len(dump)}")
    for login, password in cracked:
        print(f"           {login} -> {password}")
    return bool(cracked)


def experiment_3_rate(lab):
    """Сколько догадок в секунду проходит один поток по одной записи."""
    lab.reset()
    lab.register("probe", "8f!Tz2rP-vQx91Ld")
    start = time.perf_counter()
    tries = 0
    while time.perf_counter() - start < 0.5:
        lab.verify("probe", DICTIONARY[tries % len(DICTIONARY)])
        tries += 1
    rate = tries / (time.perf_counter() - start)
    pretty = f"{rate:,.0f}".replace(",", "\u202f")
    print(f"  опыт 3 — перебор по одной записи: {pretty} догадок/с "
          f"(справочно, критерием не является)")
    return rate


def main() -> int:
    name, lab = load()
    print(f"Цель: {name}")
    dump = build_store(lab)
    shared = experiment_1_shared_passwords(dump)
    bulk = experiment_2_one_table_for_all(dump)
    experiment_3_rate(lab)
    if shared or bulk:
        print("ЭКСПЛОЙТ СРАБОТАЛ: дамп поддаётся атаке одним проходом.")
        return 1
    print("ЭКСПЛОЙТ НЕ СРАБОТАЛ: одинаковые пароли неразличимы, "
          "общая таблица не подходит ни к одной записи.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
