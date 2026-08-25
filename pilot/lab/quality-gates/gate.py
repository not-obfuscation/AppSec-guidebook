#!/usr/bin/env python3
"""Quality gate: заготовка в сломанном состоянии.

Читает отчёт сканера в формате Semgrep JSON и решает, останавливать ли сборку.
Договор о коде возврата, который надо выполнить:

    0  проверка прошла: порог не превышен
    1  порог превышен: сборка останавливается
    2  проверка не отработала: вердикта нет — это не «чисто»

Запуск:
    python3 gate.py reports/head.json
    python3 gate.py reports/head.json --baseline reports/base.json
    SEVERITY=ERROR THRESHOLD=0 python3 gate.py reports/head.json

Переменные среды:
    SEVERITY   уровень, начиная с которого находка считается (по умолчанию ERROR)
    THRESHOLD  сколько находок пропускается (по умолчанию 0)
    MODE       block — порог останавливает сборку; warn — только сообщает

Сейчас гейт отдаёт ноль всегда. Это и есть задача.
"""
import json
import os
import sys


def load(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def key(finding):
    """Опознание находки: одна и та же находка в двух отчётах — одна находка.

    Поля `extra.lines` и `extra.fingerprint` бесплатная сборка сканера отдаёт
    строкой «requires login», то есть отпечатка в отчёте нет. Остаётся номер
    строки — ключ хрупкий, и это не изъян лабы, а свойство отчёта.
    """
    return (finding.get("check_id"),
            finding.get("path"),
            (finding.get("start") or {}).get("line"))


def main(argv):
    path = argv[1]
    baseline = None
    if "--baseline" in argv:
        baseline = argv[argv.index("--baseline") + 1]

    severity = os.environ.get("SEVERITY", "ERROR")
    threshold = int(os.environ.get("THRESHOLD", "0"))
    mode = os.environ.get("MODE", "block")

    report = load(path)
    findings = report.get("results", [])

    # TODO 1: отчёт со списком ошибок сканера — это не «чисто».
    # TODO 2: отфильтровать находки по уровню severity.
    # TODO 3: при заданном baseline считать только те находки, которых
    #         в базовом отчёте не было.
    # TODO 4: сравнить с порогом и вернуть код по договору, а в режиме warn
    #         сообщить и не останавливать.

    print("gate: находок %d, порог %d, режим %s" % (len(findings), threshold, mode))
    print("gate: зелёный")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
