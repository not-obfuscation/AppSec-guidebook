#!/usr/bin/env python3
"""Проверялка лабы quality-gates.

Восемь прогонов одного гейта на четырёх сохранённых отчётах. Проверяется договор
о коде возврата, а не текст сообщений.

Запуск из каталога лабы:
    python3 check.py
Код возврата 0 — зачтено, 1 — нет.
"""
import pathlib
import subprocess
import sys

HERE = pathlib.Path(__file__).parent

CASES = [
    # env, аргументы, ожидаемый код, за что отвечает
    ({}, ["reports/clean.json"], 0,
     "чистый отчёт при пороге 0 — зелёный"),
    ({}, ["reports/base.json"], 1,
     "один ERROR при пороге 0 — сборка остановлена"),
    ({"MODE": "warn"}, ["reports/base.json"], 0,
     "тот же отчёт в информационном режиме — сборка идёт дальше"),
    ({"THRESHOLD": "5"}, ["reports/head.json"], 0,
     "порог 5 при двух ERROR — зелёный"),
    ({"SEVERITY": "WARNING"}, ["reports/base.json"], 1,
     "порог по WARNING считает и предупреждения"),
    ({}, ["reports/head.json", "--baseline", "reports/base.json"], 1,
     "новый ERROR относительно базы — сборка остановлена"),
    ({}, ["reports/base.json", "--baseline", "reports/base.json"], 0,
     "нового относительно самой себя нет — зелёный"),
    ({}, ["reports/failed.json"], 2,
     "сканер не отработал — вердикта нет, код 2"),
]


def main():
    import os
    ok = True
    for env, args, want, what in CASES:
        e = dict(os.environ)
        e.update(env)
        p = subprocess.run([sys.executable, "gate.py"] + args, cwd=HERE,
                           capture_output=True, text=True, env=e)
        mark = "ок  " if p.returncode == want else "мимо"
        if p.returncode != want:
            ok = False
        print("%s  ждали %d, получили %d — %s" % (mark, want, p.returncode, what))
    print("зачтено" if ok else "не зачтено")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
