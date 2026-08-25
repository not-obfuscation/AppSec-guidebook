#!/usr/bin/env python3
"""Проверялка лабы pipeline-anatomy.

Задача «почини»: сделать так, чтобы стадия test действительно проверяла то,
что собрала стадия build. Проверяется не текст описания, а поведение —
двумя прогонами одного и того же конвейера:

  прогон 1  сборка исправна  -> конвейер зелёный, тест сказал, что проверил
  прогон 2  сборка испорчена -> конвейер красный

Второй прогон и есть смысл лабы: конвейер, который не краснеет на сломанной
сборке, ничего не проверяет, сколько бы job в нём ни было.

Запуск из каталога лабы:
    python3 check.py
Код возврата 0 — зачтено, 1 — нет.
"""
import pathlib
import shutil
import subprocess
import sys

HERE = pathlib.Path(__file__).parent
SRC = HERE / "src" / "app.py"
BROKEN = 'VERSION = "1.0.0"\n\n\ndef render():\n    return ""\n'


def run():
    p = subprocess.run([sys.executable, "runner.py", "pipeline.yml"],
                       cwd=HERE, capture_output=True, text=True)
    return p.returncode, p.stdout + p.stderr


def main():
    ok = True

    rc1, out1 = run()
    if rc1 != 0:
        print("прогон 1: конвейер красный на исправной сборке — так быть не должно")
        print(out1)
        return 1
    if "артефакт проверен" not in out1:
        print("прогон 1: конвейер зелёный, но тест не сказал, что проверил артефакт.")
        print("          стадия test по-прежнему работает вхолостую.")
        ok = False
    else:
        print("прогон 1: сборка исправна, конвейер зелёный, тест проверил артефакт")

    keep = SRC.read_text(encoding="utf-8")
    try:
        SRC.write_text(BROKEN, encoding="utf-8")
        rc2, out2 = run()
    finally:
        SRC.write_text(keep, encoding="utf-8")

    if rc2 == 0:
        print("прогон 2: сборка испорчена, а конвейер зелёный — дефект уехал дальше")
        ok = False
    else:
        print("прогон 2: сборка испорчена, конвейер красный — тест поймал")

    for junk in ("run.json",):
        (HERE / junk).unlink(missing_ok=True)

    print("зачтено" if ok else "не зачтено")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
