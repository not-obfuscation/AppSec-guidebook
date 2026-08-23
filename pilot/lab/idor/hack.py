"""Эксплойт лабы: чтение и правка чужого счёта по идентификатору.

Проверяет одно свойство — проверяются ли права на объект, а не только
на функцию. Запускается локально, к сети не обращается, против чужих
систем неприменим.

Код возврата:
    0 — эксплойт НЕ сработал (лаба починена)
    1 — эксплойт сработал (лаба ещё уязвима)
"""

import sys

from labtarget import load

ATTACKER = "anna"
VICTIM_SEQUENTIAL = "1002"
VICTIM_UNGUESSABLE = "b9f1c0d6-7a41-4a2e-9d3b-6c5e0f2a1d84"


def denied(lab, call, *args):
    """Вызвать и сказать, отвергнут ли вызов."""
    try:
        return None, call(*args)
    except (lab.Denied, lab.NotFound) as exc:
        return type(exc).__name__, None


def experiment_1_sequential(lab):
    """Соседний номер: счёт другого пользователя читается целиком."""
    error, data = denied(lab, lab.read_invoice, ATTACKER, VICTIM_SEQUENTIAL)
    got = data is not None
    print(f"  опыт 1 — чтение чужого счёта {VICTIM_SEQUENTIAL}: "
          f"{'ПОЛУЧЕН, сумма ' + str(data['sum']) if got else error}")
    return got


def experiment_2_write(lab):
    """То же на изменяющей операции: подмена адреса доставки счёта."""
    error, data = denied(lab, lab.set_invoice_email,
                         ATTACKER, VICTIM_SEQUENTIAL, "anna@acme.test")
    changed = data is not None
    print(f"  опыт 2 — подмена адреса в чужом счёте: "
          f"{'АДРЕС ЗАМЕНЁН на ' + data['email'] if changed else error}")
    return changed


def experiment_3_unguessable(lab):
    """Непредсказуемый идентификатор не помогает: он приходит из ленты."""
    feed = lab.company_feed(ATTACKER)
    refs = [item["invoice_ref"] for item in feed
            if item["actor"] != ATTACKER]
    target = VICTIM_UNGUESSABLE if VICTIM_UNGUESSABLE in refs else None
    if target is None:
        print("  опыт 3 — идентификатор в ленте не найден")
        return False
    error, data = denied(lab, lab.read_invoice, ATTACKER, target)
    got = data is not None
    print(f"  опыт 3 — счёт с UUID из ленты: "
          f"{'ПОЛУЧЕН, сумма ' + str(data['sum']) if got else error}")
    return got


def experiment_4_control(lab):
    """Контроль: свой счёт по-прежнему читается."""
    error, data = denied(lab, lab.read_invoice, ATTACKER, "1001")
    ok = data is not None
    print(f"  опыт 4 — контроль, свой счёт: "
          f"{'доступен' if ok else 'ПОЧИНКА СЛОМАЛА ШТАТНЫЙ ДОСТУП: ' + error}")
    return ok


def main() -> int:
    name, lab = load()
    print(f"Цель: {name}")
    lab.reset()
    hits = [experiment_1_sequential(lab),
            experiment_2_write(lab),
            experiment_3_unguessable(lab)]
    lab.reset()
    control = experiment_4_control(lab)
    print()
    if any(hits):
        print("ЭКСПЛОЙТ СРАБОТАЛ: чужой объект достался по идентификатору "
              f"({sum(hits)} из 3 опытов)")
        return 1
    if not control:
        print("ЭКСПЛОЙТ НЕ СРАБОТАЛ, но контроль упал: свой счёт закрылся "
              "вместе с чужими — это не починка")
        return 1
    print("эксплойт не сработал: все три опыта отвергнуты, "
          "свой счёт остался доступен")
    return 0


if __name__ == "__main__":
    sys.exit(main())
