"""Эксплойт лабы: инъекция через список IN, собранный склейкой.

Проверяет одно свойство — попадает ли присланная строка в текст запроса.
Запускается локально, к сети не обращается, против чужих систем неприменим.

Код возврата:
    0 — эксплойт НЕ сработал (лаба починена)
    1 — эксплойт сработал (лаба ещё уязвима)
"""

import sys

from labtarget import load


def experiment_1_break_in(lab):
    """Разрыв списка IN: в выдачу попадают невыпущенные товары."""
    payload = ["1", "2) OR released = 0 OR (1=1"]
    try:
        rows = lab.by_ids(payload)
    except Exception as exc:
        print(f"  опыт 1 — разрыв IN: запрос упал ({type(exc).__name__})")
        return False
    names = [r[1] for r in rows]
    leaked = "Секретный прототип" in names
    print(f"  опыт 1 — разрыв списка IN: "
          f"{'НЕВЫПУЩЕННОЕ В ВЫДАЧЕ, ' + str(len(rows)) + ' строк' if leaked else 'нет'}")
    return leaked


def experiment_2_control_ids(lab):
    """Контроль: обычная выборка по списку id работает."""
    rows = lab.by_ids(["1", "4"])
    ids = sorted(r[0] for r in rows)
    ok = ids == [1, 4]
    print(f"  опыт 2 — контроль, выборка id 1 и 4: "
          f"{'работает' if ok else 'ПОЧИНКА СЛОМАЛА ВЫБОРКУ'}")
    return ok


def experiment_3_control_category(lab):
    """Контроль: выборка по категории (уже на параметре) работает."""
    rows = lab.by_category("Gifts")
    names = [r[1] for r in rows]
    ok = "Открытка" in names and "Подарок к запуску" not in names
    print(f"  опыт 3 — контроль, категория Gifts: "
          f"{'работает' if ok else 'СЛОМАНО'}")
    return ok


def main() -> int:
    name, lab = load()
    print(f"Цель: {name}")
    lab.reset()
    hit = experiment_1_break_in(lab)
    lab.reset()
    controls = [experiment_2_control_ids(lab),
                experiment_3_control_category(lab)]
    print()
    if hit:
        print("ЭКСПЛОЙТ СРАБОТАЛ: строка из списка id стала частью команды")
        return 1
    if not all(controls):
        print("ЭКСПЛОЙТ НЕ СРАБОТАЛ, но контроль упал: выборка перестала "
              "работать — это не починка")
        return 1
    print("эксплойт не сработал: список id отвергнут как данные, "
          "выборка работает")
    return 0


if __name__ == "__main__":
    sys.exit(main())
