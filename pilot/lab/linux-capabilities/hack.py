"""Эксплойт лабы: у агента оказались полномочия всего root.

Сценарий: атакующий получил исполнение своего кода внутри процесса
агента (через любой дефект самого агента — он здесь не разбирается).
Вопрос лабы один: что ему доступно дальше. Ответ задаёт набор
capabilities процесса.

Запускается локально, к сети не обращается, против чужих систем
неприменим. Это модель: системные вызовы изображены функциями.

Код возврата:
    0 — эксплойт НЕ сработал (агенту хватает одной capability)
    1 — эксплойт сработал (агенту доступны вызовы, не нужные ему)
"""

import sys

from labtarget import load

TARGETS = {"db": True, "cache": True}


def attempt(lab, proc, action, note):
    """Один вызов от имени процесса агента: сработал или нет."""
    try:
        action(proc)
    except PermissionError:
        print(f"           {note}: ОТКАЗАНО")
        return False
    print(f"           {note}: СРАБОТАЛО")
    return True


def main() -> int:
    name, lab = load()
    print(f"Цель: {name}")
    agent = lab.start_agent(TARGETS)

    # Контроль: рабочий вызов агента обязан проходить всегда.
    control = agent.probe("db") == "db: доступен"
    print(f"  опыт 0 — контроль, рабочий probe: "
          f"{'работает' if control else 'СЛОМАН'}")

    print("  опыт 1 — вызовы, не нужные агенту:")
    extra = [
        attempt(lab, agent.proc, lab.mount_fs,
                "смонтировать файловую систему"),
        attempt(lab, agent.proc, lab.set_system_time,
                "перевести системные часы"),
        attempt(lab, agent.proc, lab.read_any_file,
                "прочитать /etc/shadow в обход прав"),
        attempt(lab, agent.proc, lab.kill_any,
                "послать сигнал чужому процессу"),
        attempt(lab, agent.proc, lab.bind_low_port,
                "слушать порт 443"),
    ]
    gained = sum(extra)
    print(f"           сверх cap_net_raw доступно вызовов: "
          f"{gained} из {len(extra)}")

    if not control:
        print("КОНТРОЛЬ СЛОМАН: рабочий вызов агента не проходит.")
        return 1
    if gained:
        print("ЭКСПЛОЙТ СРАБОТАЛ: код внутри процесса агента получил")
        print("полномочия, которые агенту не нужны.")
        return 1
    print("ЭКСПЛОЙТ НЕ СРАБОТАЛ: у процесса только cap_net_raw, "
          "ничего сверх неё.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
