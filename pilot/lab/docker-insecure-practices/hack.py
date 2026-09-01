"""Эксплойт лабы: выход из контейнера через доступный ему канал.

Сценарий: код атакующего исполняется внутри контейнера мониторинга
(как он туда попал — вопрос другой темы). Вопрос лабы один: может ли
контейнер через свой канал к демону создать новый контейнер с bind
хоста. Если да — атакующий получил хост.

Запускается локально, к сети не обращается, против чужих систем
неприменим. Это модель: демон изображён структурой данных.

Код возврата:
    0 — эксплойт НЕ сработал (лаба починена)
    1 — эксплойт сработал (контейнер создал контейнер)
"""

import sys

from labtarget import load


def experiment_1_control(lab) -> bool:
    """Контроль: рабочая функция мониторинга обязана отвечать."""
    daemon = lab.Daemon()
    daemon.containers.append({"name": "web", "image": "nginx"})
    _, report = lab.monitoring_container(daemon)
    out = report()
    ok = out == "контейнеров на хосте: 1"
    print(f"  опыт 1 — контроль, отчёт мониторинга: "
          f"{'работает' if ok else 'СЛОМАН'}")
    return ok


def experiment_2_create_through_channel(lab) -> bool:
    """Создание контейнера с bind хоста через канал мониторинга."""
    daemon = lab.Daemon()
    channel, _ = lab.monitoring_container(daemon)
    spec = {"name": "escape", "image": "alpine",
            "binds": ["/host:/m"], "privileged": True}
    code, name = channel("POST", "/containers/create", spec)
    print(f"  опыт 2 — POST /containers/create через канал контейнера: "
          f"{code}" + (f", создан «{name}»" if code == 201 else ""))
    return code == 201


def main() -> int:
    name, lab = load()
    print(f"Цель: {name}")
    control = experiment_1_control(lab)
    escaped = experiment_2_create_through_channel(lab)
    if not control:
        print("КОНТРОЛЬ СЛОМАН: мониторинг не отвечает.")
        return 1
    if escaped:
        print("ЭКСПЛОЙТ СРАБОТАЛ: контейнер создал контейнер с bind "
              "хоста — это выход на хост.")
        return 1
    print("ЭКСПЛОЙТ НЕ СРАБОТАЛ: канал контейнера умеет только читать "
          "список.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
