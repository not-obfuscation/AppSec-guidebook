"""Эксплойт лабы: четыре приёма SQL-инъекции против витрины.

Проверяет одно свойство — различает ли база код и данные. Запускается
локально, к сети не обращается, против чужих систем неприменим.

Код возврата:
    0 — эксплойт НЕ сработал (лаба починена)
    1 — эксплойт сработал (лаба ещё уязвима)
"""

import sys

from labtarget import load


def experiment_1_auth_bypass(lab):
    """Вход администратором без пароля: комментарий срезает проверку."""
    role = lab.login("administrator'--", "")
    got = role is not None and role["role"] == "admin"
    print(f"  опыт 1 — вход как administrator'-- : "
          f"{'РОЛЬ ADMIN БЕЗ ПАРОЛЯ' if got else 'отвергнут'}")
    return got


def experiment_2_hidden_data(lab):
    """Скрытые данные: невыпущенный товар в выдаче поиска."""
    rows = lab.search_products("Gifts'--")
    names = [r[0] for r in rows]
    got = "Подарок к запуску" in names
    print(f"  опыт 2 — Gifts'-- показывает невыпущенное: "
          f"{'ДА, ' + str(len(rows)) + ' строк' if got else 'нет'}")
    return got


def experiment_3_or_true(lab):
    """OR '1'='1: условие всегда истинно, каталог отдаётся весь."""
    rows = lab.search_products("no-such' OR '1'='1")
    got = len(rows) >= 3
    print(f"  опыт 3 — OR '1'='1 отдаёт весь каталог: "
          f"{'ДА, ' + str(len(rows)) + ' строк' if got else 'нет'}")
    return got


def experiment_4_union(lab):
    """UNION: имя и пароль из чужой таблицы в выдаче поиска."""
    rows = lab.search_products(
        "no-such' UNION SELECT username, password FROM users--")
    leaked = [r for r in rows if r[0] == "administrator"]
    got = bool(leaked)
    secret = leaked[0][1] if leaked else ""
    print(f"  опыт 4 — UNION вытягивает пароль admin: "
          f"{'ДА, пароль ' + secret if got else 'нет'}")
    return got


def experiment_5_control_search(lab):
    """Контроль: обычный поиск возвращает только выпущенное."""
    rows = lab.search_products("Gifts")
    names = [r[0] for r in rows]
    ok = "Открытка" in names and "Подарок к запуску" not in names
    print(f"  опыт 5 — контроль, поиск Gifts: "
          f"{'работает' if ok else 'ПОЧИНКА СЛОМАЛА ПОИСК'}")
    return ok


def experiment_6_control_login(lab):
    """Контроль: честный вход по паролю по-прежнему проходит."""
    role = lab.login("wiener", "peter")
    ok = role is not None and role["role"] == "user"
    print(f"  опыт 6 — контроль, вход wiener: "
          f"{'работает' if ok else 'ПОЧИНКА СЛОМАЛА ВХОД'}")
    return ok


def main() -> int:
    name, lab = load()
    print(f"Цель: {name}")
    lab.reset()
    hits = [experiment_1_auth_bypass(lab),
            experiment_2_hidden_data(lab),
            experiment_3_or_true(lab),
            experiment_4_union(lab)]
    lab.reset()
    controls = [experiment_5_control_search(lab),
                experiment_6_control_login(lab)]
    print()
    if any(hits):
        print("ЭКСПЛОЙТ СРАБОТАЛ: присланная строка исполнилась как код "
              f"({sum(hits)} из 4 опытов)")
        return 1
    if not all(controls):
        print("ЭКСПЛОЙТ НЕ СРАБОТАЛ, но контроль упал: витрина перестала "
              "работать — это не починка")
        return 1
    print("эксплойт не сработал: все четыре приёма отвергнуты, "
          "поиск и вход работают")
    return 0


if __name__ == "__main__":
    sys.exit(main())
