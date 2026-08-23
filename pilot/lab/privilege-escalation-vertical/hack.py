"""Эксплойт лабы: три способа попасть в административную функцию.

Проверяет одно свойство контроля доступа — закрыта ли административная
функция от обычного пользователя. Запускается локально, к сети не
обращается, против чужих систем неприменим.

Код возврата:
    0 — эксплойт НЕ сработал (лаба починена)
    1 — эксплойт сработал (лаба ещё уязвима)
"""

import sys

from labtarget import load

ATTACKER = "anna"          # обычный пользователь, роль user


def experiment_1_unlisted(lab):
    """Функция, которой нет в списке закрытых: прямой запрос."""
    resp = lab.handle(ATTACKER, "/admin/export")
    ok = resp["status"] == 200
    print(f"  опыт 1 — /admin/export без роли: код {resp['status']}"
          f"{' — ВЫГРУЗКА ПОЛУЧЕНА' if ok else ''}")
    return ok


def experiment_2_case(lab):
    """Тот же путь другим регистром: маршрут находится, охрана — нет."""
    resp = lab.handle(ATTACKER, "/ADMIN/USERS")
    ok = resp["status"] == 200
    print(f"  опыт 2 — /ADMIN/USERS без роли: код {resp['status']}"
          f"{' — СПИСОК УЧЁТНЫХ ЗАПИСЕЙ ПОЛУЧЕН' if ok else ''}")
    return ok


def experiment_3_delete(lab):
    """Изменяющее действие тем же приёмом: удаление чужой заявки."""
    lab.reset()
    resp = lab.handle(ATTACKER, "/Admin/Tickets/Delete",
                      method="POST", query={"id": "2"})
    gone = 2 not in lab.TICKETS
    print(f"  опыт 3 — удаление чужой заявки: код {resp['status']}"
          f"{' — ЗАЯВКА УДАЛЕНА' if gone else ''}")
    lab.reset()
    return gone


def experiment_4_control(lab):
    """Контроль: администратор в свои функции попадает по-прежнему."""
    resp = lab.handle("sysadmin", "/admin/users")
    ok = resp["status"] == 200
    print(f"  опыт 4 — контроль, администратор: код {resp['status']}"
          f"{'' if ok else ' — ПОЧИНКА СЛОМАЛА ШТАТНЫЙ ДОСТУП'}")
    return ok


def main() -> int:
    name, lab = load()
    print(f"Цель: {name}")
    lab.reset()
    hits = [experiment_1_unlisted(lab),
            experiment_2_case(lab),
            experiment_3_delete(lab)]
    control = experiment_4_control(lab)
    print()
    if any(hits):
        print("ЭКСПЛОЙТ СРАБОТАЛ: обычный пользователь дошёл до "
              f"административной функции ({sum(hits)} из 3 опытов)")
        return 1
    if not control:
        print("ЭКСПЛОЙТ НЕ СРАБОТАЛ, но контроль упал: администратор "
              "потерял доступ — это не починка")
        return 1
    print("эксплойт не сработал: все три опыта отвергнуты, "
          "администратор доступ сохранил")
    return 0


if __name__ == "__main__":
    sys.exit(main())
