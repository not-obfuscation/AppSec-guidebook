"""Эксплойт лабы: setuid-обёртка запускает программу атакующего.

Проверяет ровно одно свойство обёртки — доверяет ли она переменной
PATH из окружения вызывающего. Если доверяет, пользователь кладёт свой
`collect-backup` в свой каталог, ставит его первым в PATH, и обёртка
исполняет чужую программу с эффективным uid 0.

Запускается локально, к сети не обращается, против чужих систем
неприменим. Это модель: привилегии изображены полями структур.

Код возврата:
    0 — эксплойт НЕ сработал (лаба починена)
    1 — эксплойт сработал (обёртка исполнила программу атакующего)
"""

import sys

from labtarget import load

ATTACKER_UID = 1000


def attacker_program(host, proc, argv):
    """«Сборщик» атакующего: пишет в файл, принадлежащий root."""
    host.write_file(proc, "/etc/attacker-was-here", f"euid={proc.euid}")
    return "программа атакующего отработала"


def experiment_1_path_hijack(lab) -> bool:
    """Подмена сборщика через PATH вызывающего."""
    host = lab.make_host()
    host.install("/tmp/attacker/collect-backup", attacker_program,
                 owner=ATTACKER_UID)
    env = {"PATH": "/tmp/attacker:/usr/bin", "LANG": "ru_RU.UTF-8"}
    lab.run_backup(host, ATTACKER_UID, env)
    ran_path, ran_euid, _ = host.exec_log[-1]
    planted = ran_path.startswith("/tmp/attacker/")
    print(f"  опыт 1 — обёртка запустила {ran_path} с euid={ran_euid}")
    print(f"           это программа атакующего: "
          f"{'ДА' if planted else 'нет'}")
    marker = host.files.get("/etc/attacker-was-here")
    if marker:
        print(f"           она записала /etc/attacker-was-here: {marker[1]!r}")
    return planted and ran_euid == 0 and marker is not None


def experiment_2_env_aside(lab) -> None:
    """Справочно: что из окружения доехало до программы."""
    host = lab.make_host()
    env = {"PATH": "/usr/bin", "LANG": "ru_RU.UTF-8",
           "LD_PRELOAD": "/tmp/attacker/evil.so"}
    seen = {}

    def spy(host_, proc, argv):
        seen.update(proc.env)
        return lab.collect_backup(host_, proc, argv)

    host.install("/usr/bin/collect-backup", spy)
    lab.run_backup(host, ATTACKER_UID, env)
    leaked = "LD_PRELOAD" in seen
    print(f"  опыт 2 — LD_PRELOAD доехал до программы: "
          f"{'ДА' if leaked else 'нет'} (справочно)")


def experiment_3_control(lab) -> bool:
    """Контроль: честный вызов обязан работать и до починки, и после."""
    host = lab.make_host()
    out = lab.run_backup(host, ATTACKER_UID,
                         {"PATH": "/usr/bin", "LANG": "ru_RU.UTF-8"})
    ok = "копия собрана" in out
    print(f"  опыт 3 — контроль, честный запуск: "
          f"{'работает' if ok else 'СЛОМАН'}")
    return ok


def main() -> int:
    name, lab = load()
    print(f"Цель: {name}")
    hijacked = experiment_1_path_hijack(lab)
    experiment_2_env_aside(lab)
    control = experiment_3_control(lab)
    if not control:
        print("КОНТРОЛЬ СЛОМАН: честный запуск обёртки не работает.")
        return 1
    if hijacked:
        print("ЭКСПЛОЙТ СРАБОТАЛ: обёртка исполнила программу "
              "атакующего с правами root.")
        return 1
    print("ЭКСПЛОЙТ НЕ СРАБОТАЛ: обёртка нашла настоящий сборщик,")
    print("окружение вызывающего проигнорировано.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
